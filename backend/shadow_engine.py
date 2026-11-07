"""
Phase 8.4C: Shadow Staging Engine for Candidate Policy D
Project: Visual Heritage Recognition Platform (SIH 2025 - SIH25052)

Provides bounded, asynchronous, non-blocking shadow execution of Candidate Policy D
in parallel with authoritative production Policy A recognition.

CRITICAL INVARIANTS:
1. Policy A is 100% authoritative for all user-facing responses.
2. Policy D executes in shadow mode only and NEVER modifies user-facing responses.
3. Hard 500ms timeout budget, bounded worker pool (2 threads), and bounded queue (10 tasks).
4. Telemetry written asynchronously to backend/telemetry/shadow_staging_audit.jsonl.
5. If shadow mode is disabled, zero background tasks are dispatched.
6. Fail-safe: Any timeout, exception, or telemetry error is isolated and logged.
"""

import atexit
import json
import logging
import os
import queue
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger("shadow_engine")

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_TELEMETRY_DIR = BASE_DIR / "telemetry"
DEFAULT_TELEMETRY_FILE = DEFAULT_TELEMETRY_DIR / "shadow_staging_audit.jsonl"
CONFIG_FILE = BASE_DIR / "phase_8_4c_shadow_config.json"

MODEL_IDENTIFIER = "openai/clip-vit-base-patch32"
INDEX_HASH = "519620C2B6C9EDAF3A91D5C67D05F8FBDD5DE344E629065CA8BBC46E5E55C603"
CONFIG_HASH = "214FBB0366AB076F5150DCEB45BEA9234C869DD5BC0E61E3410587DD7CB4957F"


class ShadowConfig:
    """Manages shadow staging configuration with dynamic runtime kill-switch support."""

    def __init__(
        self,
        config_path: Optional[Path] = None,
        enabled: Optional[bool] = None,
        max_workers: Optional[int] = None,
        max_queue_size: Optional[int] = None,
        timeout_seconds: Optional[float] = None,
        timeout_ms: Optional[float] = None,
    ):
        self.config_path = config_path or CONFIG_FILE
        self.default_enabled: bool = False
        self.max_workers: int = 2
        self.max_queue_size: int = 10
        self.timeout_seconds: float = 0.500  # 500 ms hard deadline
        self.telemetry_path: Path = DEFAULT_TELEMETRY_FILE
        self._runtime_override: Optional[bool] = None
        self._lock = threading.Lock()
        self.load_config()

        if enabled is not None:
            self._runtime_override = enabled
        if max_workers is not None:
            self.max_workers = max_workers
        if max_queue_size is not None:
            self.max_queue_size = max_queue_size
        if timeout_ms is not None:
            self.timeout_seconds = timeout_ms / 1000.0
        elif timeout_seconds is not None:
            self.timeout_seconds = timeout_seconds

    def load_config(self) -> None:
        """Loads static config from JSON file if present, falling back to safe defaults."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.default_enabled = bool(data.get("enabled_by_default", False))
                    self.max_workers = int(data.get("max_workers", 2))
                    self.max_queue_size = int(data.get("max_queue_size", 10))
                    self.timeout_seconds = float(data.get("timeout_seconds", 0.500))
                    t_path = data.get("telemetry_path")
                    if t_path:
                        self.telemetry_path = Path(t_path) if Path(t_path).is_absolute() else (BASE_DIR / t_path)
            except Exception as e:
                logger.warning(f"Could not load shadow config file ({e}). Using safe disabled defaults.")
                self.default_enabled = False

    def is_enabled(self) -> bool:
        """
        Evaluates whether shadow mode is enabled with runtime kill-switch support.
        Priority:
        1. Explicit in-memory runtime override (set_runtime_enabled).
        2. Environment variable ENABLE_SHADOW_CANDIDATE_POLICY_D.
        3. Static JSON configuration file.
        4. Safe default: False.
        """
        with self._lock:
            if self._runtime_override is not None:
                return self._runtime_override

        env_val = os.getenv("ENABLE_SHADOW_CANDIDATE_POLICY_D")
        if env_val is not None:
            clean_env = env_val.strip().lower()
            if clean_env in ("1", "true", "yes", "on"):
                return True
            if clean_env in ("0", "false", "no", "off"):
                return False
            # Malformed environment value -> fail safely disabled
            logger.warning(f"Malformed ENABLE_SHADOW_CANDIDATE_POLICY_D='{env_val}'. Failing safely: DISABLED.")
            return False

        return self.default_enabled

    def set_runtime_enabled(self, enabled: Optional[bool]) -> None:
        """Dynamically enables, disables, or resets the shadow staging kill-switch at runtime."""
        with self._lock:
            self._runtime_override = enabled
            logger.info(f"Shadow staging runtime kill-switch updated: override={self._runtime_override}")


class ShadowTelemetryLogger:
    """Thread-safe, non-blocking JSONL telemetry recorder for shadow comparisons."""

    def __init__(self, log_path: Path):
        self.log_path = log_path
        self._lock = threading.Lock()
        self.write_failure_count: int = 0
        self.total_write_count: int = 0
        self.duplicate_event_count: int = 0
        self.last_write_success_utc: Optional[str] = None
        self._recorded_requests: Dict[str, str] = {}
        self._ensure_dir()

    def _ensure_dir(self) -> None:
        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(f"Could not create telemetry directory ({e}).")

    def record_event(self, event: Dict[str, Any]) -> bool:
        """
        Appends a structured JSONL event record to disk.
        Protected by mutex to prevent line interleaving from concurrent worker threads.
        Tracks write failures, timestamps, duplicate events, and late completions.
        Never raises exceptions to the caller.
        """
        req_id = event.get("request_id")
        event_type = event.get("event_type", "UNKNOWN")

        with self._lock:
            if req_id:
                if req_id in self._recorded_requests:
                    prior_type = self._recorded_requests[req_id]
                    if prior_type == "SHADOW_TIMEOUT" and event_type in ("SHADOW_EVALUATION_COMPLETED", "SHADOW_TIMEOUT"):
                        # Late completion after recorded timeout
                        event["event_type"] = "SHADOW_LATE_COMPLETION"
                        event["prior_event_type"] = prior_type
                        event["late_completion"] = True
                    elif prior_type == event_type:
                        # Suppress duplicate identical primary event
                        self.duplicate_event_count += 1
                        logger.debug(f"Duplicate telemetry event suppressed for {req_id} ({event_type})")
                        return True
                else:
                    self._recorded_requests[req_id] = event_type
                    if len(self._recorded_requests) > 5000:
                        oldest_keys = list(self._recorded_requests.keys())[:1000]
                        for k in oldest_keys:
                            self._recorded_requests.pop(k, None)

            try:
                line = json.dumps(event, ensure_ascii=False) + "\n"
                with open(self.log_path, "a", encoding="utf-8") as f:
                    f.write(line)
                    f.flush()
                self.total_write_count += 1
                self.last_write_success_utc = datetime.now(timezone.utc).isoformat()
                return True
            except Exception as e:
                self.write_failure_count += 1
                logger.error(
                    f"CRITICAL: Shadow telemetry write failure (total_failures={self.write_failure_count}): {e}. "
                    f"Destination: {self.log_path}"
                )
                return False

    def log_event(self, event: Dict[str, Any]) -> bool:
        """Convenience alias for record_event."""
        return self.record_event(event)

    def get_health(self) -> Dict[str, Any]:
        """Provides operational health metrics for the telemetry subsystem."""
        with self._lock:
            is_writable = False
            try:
                self._ensure_dir()
                test_file = self.log_path.parent / ".telemetry_health_probe"
                with open(test_file, "a") as f:
                    f.write("")
                if test_file.exists():
                    test_file.unlink(missing_ok=True)
                is_writable = True
            except Exception:
                is_writable = False

            healthy = is_writable and (self.write_failure_count == 0)
            return {
                "healthy": healthy,
                "log_destination": str(self.log_path),
                "is_writable": is_writable,
                "total_writes": self.total_write_count,
                "write_failures": self.write_failure_count,
                "duplicate_events_suppressed": self.duplicate_event_count,
                "last_write_success_utc": self.last_write_success_utc,
            }


class ShadowEngine:
    """
    Production-grade bounded background executor for Candidate Policy D.
    Enforces strict admission control, bounded concurrency, hard deadlines,
    and safe lifecycle shutdown.
    """

    def __init__(self, config: Optional[ShadowConfig] = None):
        self.config = config or ShadowConfig()
        self.telemetry = ShadowTelemetryLogger(self.config.telemetry_path)
        self._executor: Optional[ThreadPoolExecutor] = None
        self._queue: queue.Queue = queue.Queue(maxsize=self.config.max_queue_size)
        self._recent_requests: set = set()
        self._recent_lock = threading.Lock()
        self._shutdown = False
        self._dropped_count = 0
        self._total_submissions = 0
        self._ref_sift_cache: Dict[str, Tuple[Any, Any]] = {}
        self._cache_lock = threading.Lock()
        self._init_executor()
        atexit.register(self.shutdown)

    def _init_executor(self) -> None:
        """Initializes the bounded worker thread pool."""
        self._executor = ThreadPoolExecutor(
            max_workers=self.config.max_workers,
            thread_name_prefix="policy_d_shadow_worker",
        )
        logger.info(
            f"ShadowEngine initialized [max_workers={self.config.max_workers}, "
            f"max_queue_size={self.config.max_queue_size}, "
            f"timeout={self.config.timeout_seconds*1000:.0f}ms, "
            f"enabled={self.config.is_enabled()}]"
        )

    def is_enabled(self) -> bool:
        return self.config.is_enabled() and not self._shutdown

    def set_runtime_enabled(self, enabled: bool) -> None:
        """Dynamically enables or disables shadow mode without restart."""
        self.config.set_runtime_enabled(enabled)

    def get_metrics(self) -> Dict[str, Any]:
        """Returns live engine execution metrics."""
        return {
            "enabled": self.is_enabled(),
            "queue_length": self._queue.qsize(),
            "active_threads": getattr(self._executor, "_work_queue", queue.Queue()).qsize() if self._executor else 0,
            "dropped_submissions": self._dropped_count,
            "total_submissions": self._total_submissions,
            "telemetry": self.telemetry.get_health(),
        }

    def submit_shadow_evaluation(
        self,
        request_id: str,
        image: Image.Image,
        top1_key: str,
        top1_sim: float,
        margin: float,
        gatekeeper_score: float,
        policy_a_decision: str,
        policy_a_monument: str,
        reference_items: Optional[List[Dict[str, Any]]] = None,
        clip_model: Optional[Any] = None,
        clip_processor: Optional[Any] = None,
    ) -> str:
        """
        Asynchronously submits a query to Candidate Policy D in shadow mode.
        Returns immediately (non-blocking) without waiting for shadow computation.
        If shadow mode is disabled, returns 'SHADOW_DISABLED' immediately without dispatch.
        """
        if not self.is_enabled():
            return "SHADOW_DISABLED"

        if self._shutdown:
            logger.warning(f"ShadowEngine is shutting down. Task {request_id} rejected.")
            return "SHADOW_SHUTDOWN"

        # Request deduplication check
        with self._recent_lock:
            if request_id in self._recent_requests:
                logger.info(f"Duplicate shadow task {request_id} ignored.")
                return "SHADOW_DUPLICATE"
            self._recent_requests.add(request_id)
            if len(self._recent_requests) > 1000:
                self._recent_requests.pop()

        # Admission control: Bounded queue capacity check
        # queue.Queue.qsize() approximates active backlog; reject if saturated
        try:
            self._queue.put_nowait(request_id)
        except queue.Full:
            self._dropped_count += 1
            logger.warning(
                f"Shadow staging queue saturated ({self.config.max_queue_size} pending). "
                f"Skipping shadow task for {request_id} (SHADOW_SKIPPED_CAPACITY)."
            )
            self._record_telemetry(
                request_id=request_id,
                policy_a_decision=policy_a_decision,
                policy_a_monument=policy_a_monument,
                policy_d_decision="UNKNOWN",
                policy_d_monument=top1_key,
                duration_ms=0.0,
                status="SHADOW_SKIPPED_CAPACITY",
            )
            return "SHADOW_SKIPPED_CAPACITY"

        # Prepare lightweight image copy for thread-safe detached processing.
        # Optimization: Downscale queries exceeding 800px immediately to prevent
        # massive raster duplication (e.g. 36 MB per 4K image) in queue buffer.
        try:
            if image is not None:
                w, h = image.size
                max_dim = 800
                if max(w, h) > max_dim:
                    scale = max_dim / max(w, h)
                    image_copy = image.resize((int(w * scale), int(h * scale)), Image.Resampling.BILINEAR)
                else:
                    image_copy = image.copy()
            else:
                image_copy = None
        except Exception:
            image_copy = image

        # Dispatch task to bounded background thread pool
        try:
            self._total_submissions += 1
            self._executor.submit(
                self._run_task_wrapper,
                request_id,
                image_copy,
                top1_key,
                top1_sim,
                margin,
                gatekeeper_score,
                policy_a_decision,
                policy_a_monument,
                reference_items,
                clip_model,
                clip_processor,
            )
            return "SUBMITTED"
        except Exception as e:
            logger.warning(f"Could not submit shadow task {request_id}: {e}")
            try:
                self._queue.get_nowait()
            except Exception:
                pass
            return "SHADOW_SUBMISSION_FAILED"

    def _run_task_wrapper(
        self,
        request_id: str,
        image: Image.Image,
        top1_key: str,
        top1_sim: float,
        margin: float,
        gatekeeper_score: float,
        policy_a_decision: str,
        policy_a_monument: str,
        reference_items: Optional[List[Dict[str, Any]]],
        clip_model: Optional[Any],
        clip_processor: Optional[Any],
    ) -> None:
        """Executes Policy D evaluation with deadline enforcement and exception isolation."""
        # Optimization: Enforce single-threaded OpenCV scoping in worker thread
        # to prevent background SIFT/RANSAC from starving CPU cores needed by Policy A.
        try:
            cv2.setNumThreads(1)
        except Exception:
            pass

        t_start = time.perf_counter()
        status = "COMPLETED"
        policy_d_decision = "UNCERTAIN_MATCH"
        policy_d_monument = top1_key
        error_msg = ""

        try:
            # Policy D evaluation
            state_d, mon_d = self.evaluate_policy_d(
                image=image,
                top1_key=top1_key,
                top1_sim=top1_sim,
                margin=margin,
                gatekeeper_score=gatekeeper_score,
                reference_items=reference_items,
                clip_model=clip_model,
                clip_processor=clip_processor,
                deadline_seconds=self.config.timeout_seconds,
            )
            policy_d_decision = state_d
            policy_d_monument = mon_d

            duration_ms = (time.perf_counter() - t_start) * 1000.0
            if duration_ms > (self.config.timeout_seconds * 1000.0):
                status = "SHADOW_TIMEOUT"
        except TimeoutError as te:
            duration_ms = (time.perf_counter() - t_start) * 1000.0
            status = "SHADOW_TIMEOUT"
            error_msg = str(te) or "Execution exceeded deadline budget"
            logger.warning(f"Shadow task {request_id} exceeded deadline ({duration_ms:.1f}ms). Recorded SHADOW_TIMEOUT.")
        except Exception as e:
            duration_ms = (time.perf_counter() - t_start) * 1000.0
            status = "SHADOW_ERROR"
            error_msg = str(e)
            logger.warning(f"Shadow task {request_id} encountered error ({e}). Recorded SHADOW_ERROR.")
        finally:
            # Remove from admission queue
            try:
                self._queue.get_nowait()
            except Exception:
                pass

            # Record telemetry
            self._record_telemetry(
                request_id=request_id,
                policy_a_decision=policy_a_decision,
                policy_a_monument=policy_a_monument,
                policy_d_decision=policy_d_decision,
                policy_d_monument=policy_d_monument,
                duration_ms=duration_ms,
                status=status,
                error_message=error_msg,
            )

    def evaluate_policy_d(
        self,
        image: Image.Image,
        top1_key: str,
        top1_sim: float,
        margin: float,
        gatekeeper_score: float,
        reference_items: Optional[List[Dict[str, Any]]] = None,
        clip_model: Optional[Any] = None,
        clip_processor: Optional[Any] = None,
        deadline_seconds: float = 0.500,
    ) -> Tuple[str, str]:
        """
        Executes frozen Candidate Policy D decision logic:
        1. Severe non-monument check: gatekeeper < 0.45 -> NON_MONUMENT_REJECTED.
        2. Marginal gatekeeper (0.45 <= gk < 0.50) or borderline sim (0.70 <= sim < 0.75) -> REVIEW_REQUIRED.
        3. Low similarity sim < 0.70 -> UNKNOWN_HERITAGE_SPECIMEN.
        4. Decisive global margin >= 0.08 -> VERIFIED_MATCH.
        5. Relaxed margin corridor [0.05, 0.08):
           Promoted to VERIFIED_MATCH if:
             (best SIFT/RANSAC inliers >= 10) OR (local CLIP mean >= 0.80 AND gatekeeper >= 0.65).
           Otherwise -> UNCERTAIN_MATCH.
        """
        t0 = time.perf_counter()

        # Gate 1: Non-monument rejection
        if gatekeeper_score < 0.45:
            return "NON_MONUMENT_REJECTED", top1_key

        # Gate 2: Borderline / Review Required
        if (0.45 <= gatekeeper_score < 0.50) or (0.70 <= top1_sim < 0.75):
            return "REVIEW_REQUIRED", top1_key

        # Gate 3: Unknown heritage
        if top1_sim < 0.70:
            return "UNKNOWN_HERITAGE_SPECIMEN", top1_key

        # Gate 4: Decisive global match
        if margin >= 0.08:
            return "VERIFIED_MATCH", top1_key

        # Gate 5: Relaxed margin corridor [0.05, 0.08) requiring geometric or local semantic corroboration
        if margin >= 0.05:
            # Check deadline budget
            if (time.perf_counter() - t0) >= deadline_seconds:
                raise TimeoutError("Deadline exceeded before local feature extraction.")

            corroborated = False

            # Check 5A: SIFT geometric correspondence against reference images of top1 candidate
            sift_inliers = 0
            if reference_items and top1_key:
                try:
                    sift_inliers = self._compute_sift_inliers(image, top1_key, reference_items, deadline_seconds - (time.perf_counter() - t0))
                    if sift_inliers >= 10:
                        corroborated = True
                except TimeoutError:
                    raise
                except Exception as e:
                    logger.debug(f"SIFTS corroboration check error: {e}")

            # Check 5B: Local CLIP multi-crop semantic agreement fallback
            if not corroborated and clip_model is not None and clip_processor is not None:
                if (time.perf_counter() - t0) >= deadline_seconds:
                    raise TimeoutError("Deadline exceeded before local CLIP extraction.")
                try:
                    local_clip_mean = self._compute_local_clip_mean(image, clip_model, clip_processor)
                    if local_clip_mean >= 0.80 and gatekeeper_score >= 0.65:
                        corroborated = True
                except Exception as e:
                    logger.debug(f"Local CLIP corroboration check error: {e}")

            if corroborated:
                return "VERIFIED_MATCH", top1_key
            else:
                return "UNCERTAIN_MATCH", top1_key

        return "UNCERTAIN_MATCH", top1_key

    def _compute_sift_inliers(
        self,
        image: Image.Image,
        monument_key: str,
        reference_items: List[Dict[str, Any]],
        remaining_seconds: float,
    ) -> int:
        """Extracts SIFT keypoints and estimates RANSAC inliers against up to 3 candidate references."""
        t_sub = time.perf_counter()
        w, h = image.size
        # Downscale for bounded processing
        max_dim = 800
        if max(w, h) > max_dim:
            scale = max_dim / max(w, h)
            image_small = image.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
        else:
            image_small = image

        query_cv = cv2.cvtColor(np.array(image_small), cv2.COLOR_RGB2GRAY)
        sift = cv2.SIFT_create(nfeatures=400)
        kp1, des1 = sift.detectAndCompute(query_cv, None)
        if des1 is None or len(kp1) < 8:
            return 0

        # Filter candidate references for matching monument key
        cand_refs = [r for r in reference_items if r.get("monument_key") == monument_key][:3]
        if not cand_refs:
            return 0

        flann = cv2.FlannBasedMatcher(dict(algorithm=1, trees=5), dict(checks=30))
        max_inliers = 0

        for r_item in cand_refs:
            if (time.perf_counter() - t_sub) >= remaining_seconds:
                raise TimeoutError("Deadline exceeded during SIFT matching loop.")

            ref_path = r_item.get("file_path")
            if not ref_path or not Path(ref_path).exists():
                continue

            # Optimization: Immutable reference SIFT descriptor cache.
            # Avoids re-reading identical static reference images from disk
            # and recomputing SIFT keypoints on CPU for repeated queries.
            kp2 = None
            des2 = None
            with self._cache_lock:
                if ref_path in self._ref_sift_cache:
                    kp2, des2 = self._ref_sift_cache[ref_path]

            if des2 is None:
                ref_gray = cv2.imread(str(ref_path), cv2.IMREAD_GRAYSCALE)
                if ref_gray is None:
                    continue
                if max(ref_gray.shape[:2]) > 800:
                    s = 800 / max(ref_gray.shape[:2])
                    ref_gray = cv2.resize(ref_gray, (int(ref_gray.shape[1] * s), int(ref_gray.shape[0] * s)))

                kp2, des2 = sift.detectAndCompute(ref_gray, None)
                if des2 is not None and len(kp2) >= 8:
                    with self._cache_lock:
                        self._ref_sift_cache[ref_path] = (kp2, des2)

            if des2 is None or len(kp2) < 8:
                continue

            try:
                matches = flann.knnMatch(des1, des2, k=2)
                good = [m for m, n in matches if len(matches[0]) == 2 and m.distance < 0.75 * n.distance] if matches and len(matches[0]) >= 2 else []
                if len(good) >= 8:
                    src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
                    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
                    _, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
                    inliers = int(np.sum(mask)) if mask is not None else 0
                    if inliers > max_inliers:
                        max_inliers = inliers
                        if max_inliers >= 10:
                            break  # Early exit on confirmed corroboration
            except Exception:
                continue

        return max_inliers

    def _compute_local_clip_mean(self, image: Image.Image, model: Any, processor: Any) -> float:
        """Extracts multi-crop local patches (3x3 grid) and computes mean cosine similarity."""
        import torch
        w, h = image.size
        patches = []
        for i in range(3):
            for j in range(3):
                box = (int(j * w / 3), int(i * h / 3), int((j + 1) * w / 3), int((i + 1) * h / 3))
                p = image.crop(box).resize((224, 224), Image.Resampling.LANCZOS)
                patches.append(p)

        inputs = processor(images=patches, return_tensors="pt")
        with torch.no_grad():
            out = model.get_image_features(**inputs)
            tensor = out.pooler_output if hasattr(out, "pooler_output") and out.pooler_output is not None else out
            tensor = tensor / tensor.norm(dim=-1, keepdim=True)
            # Embedding pairwise dot products
            embs = tensor.cpu().numpy()
            mean_emb = np.mean(embs, axis=0, keepdims=True)
            mean_emb = mean_emb / (np.linalg.norm(mean_emb) + 1e-9)
            sims = (embs @ mean_emb.T).flatten()
            return float(np.mean(sims))

    @staticmethod
    def classify_divergence(policy_a_decision: str, policy_d_decision: str) -> str:
        """Classifies divergence taxonomy according to Phase 8.4C specification."""
        if policy_a_decision == "VERIFIED_MATCH" and policy_d_decision == "VERIFIED_MATCH":
            return "AGREEMENT"
        if policy_a_decision in ["UNCERTAIN_MATCH", "REVIEW_REQUIRED"] and policy_d_decision == "VERIFIED_MATCH":
            return "POLICY_D_UPGRADE"
        if policy_a_decision == "VERIFIED_MATCH" and policy_d_decision != "VERIFIED_MATCH":
            return "POLICY_D_DOWNGRADE"
        if policy_a_decision in ["UNCERTAIN_MATCH", "REVIEW_REQUIRED"] and policy_d_decision in ["UNCERTAIN_MATCH", "REVIEW_REQUIRED"]:
            return "UNVERIFIED_AGREEMENT"
        if policy_a_decision in ["NON_MONUMENT_REJECTED", "UNKNOWN_HERITAGE_SPECIMEN"] and policy_d_decision in ["NON_MONUMENT_REJECTED", "UNKNOWN_HERITAGE_SPECIMEN"]:
            return "OUT_OF_CATALOG_NEGATIVE_REJECTION"
        return "DISAGREEMENT_OTHER"

    _classify_divergence = classify_divergence

    def _record_telemetry(
        self,
        request_id: str,
        policy_a_decision: str,
        policy_a_monument: str,
        policy_d_decision: str,
        policy_d_monument: str,
        duration_ms: float,
        status: str,
        error_message: str = "",
    ) -> None:
        """Formats and writes a structured telemetry event."""
        if status == "SHADOW_TIMEOUT":
            timeout_event = {
                "event_type": "SHADOW_TIMEOUT",
                "request_id": request_id,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "elapsed_ms": round(duration_ms, 2),
                "timeout_threshold_ms": int(self.config.timeout_seconds * 1000),
                "policy_a_decision": policy_a_decision,
                "policy_a_monument": policy_a_monument,
            }
            self.telemetry.record_event(timeout_event)
            return

        if status == "SHADOW_ERROR":
            err_event = {
                "event_type": "SHADOW_ERROR",
                "request_id": request_id,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "elapsed_ms": round(duration_ms, 2),
                "error_message": error_message,
                "policy_a_decision": policy_a_decision,
                "policy_a_monument": policy_a_monument,
            }
            self.telemetry.record_event(err_event)
            return

        monument_agreed = (policy_a_monument == policy_d_monument) if policy_a_monument and policy_d_monument else False
        decision_agreed = (policy_a_decision == policy_d_decision)
        d_recovered = (policy_d_decision == "VERIFIED_MATCH" and policy_a_decision != "VERIFIED_MATCH")
        a_verified_d_rejected = (policy_a_decision == "VERIFIED_MATCH" and policy_d_decision != "VERIFIED_MATCH")
        div_cat = self.classify_divergence(policy_a_decision, policy_d_decision)

        event = {
            "event_type": "SHADOW_EVALUATION_COMPLETED",
            "request_id": request_id,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "policy_a_decision": policy_a_decision,
            "policy_a_monument": policy_a_monument,
            "policy_d_decision": policy_d_decision,
            "policy_d_monument": policy_d_monument,
            "divergence_category": div_cat,
            "latency_ms": round(duration_ms, 2),
            "policy_a": {
                "authoritative": True,
                "decision_state": policy_a_decision,
                "predicted_monument": policy_a_monument,
            },
            "policy_d": {
                "authoritative": False,
                "decision_state": policy_d_decision,
                "predicted_monument": policy_d_monument,
                "execution_duration_ms": round(duration_ms, 2),
            },
            "comparison": {
                "divergence_category": div_cat,
                "monument_agreement": monument_agreed,
                "decision_state_agreement": decision_agreed,
                "policy_d_recovered_uncertain": d_recovered,
                "policy_a_verified_d_rejected": a_verified_d_rejected,
            },
            "shadow_execution": {
                "status": status,
                "hard_timeout_ms": int(self.config.timeout_seconds * 1000),
                "model_identifier": MODEL_IDENTIFIER,
                "index_hash": INDEX_HASH,
                "config_hash": CONFIG_HASH,
            },
        }
        self.telemetry.record_event(event)

    def shutdown(self, wait: bool = False) -> None:
        """Safely terminates the executor without blocking application shutdown."""
        self._shutdown = True
        if self._executor:
            try:
                self._executor.shutdown(wait=wait, cancel_futures=True)
                logger.info("ShadowEngine executor safely shut down.")
            except Exception as e:
                logger.warning(f"Error shutting down ShadowEngine ({e}).")


# Singleton instance for platform-wide import
shadow_engine = ShadowEngine()


def evaluate_policy_d(*args, **kwargs):
    """Module-level convenience wrapper around the active shadow engine's evaluate_policy_d."""
    return shadow_engine.evaluate_policy_d(*args, **kwargs)
