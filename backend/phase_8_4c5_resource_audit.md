# Phase 8.4C.5 — Resource Bottleneck Audit Report

**Project**: Visual Heritage Recognition & Grounded Cultural Discovery Platform (SIH 2025 – SIH25052)  
**Workspace**: `C:\Users\humai\Heritage PJ`  
**Date**: November 7, 2026  
**Auditor**: Principal ML Systems Performance Engineer & ML Reliability Lead  
**Phase**: 8.4C.5 (Fast-Track Resource Optimization & Pilot Validation)  
**Status**: COMPLETE — AUDIT EXECUTED & EVIDENCE DOCUMENTED

---

## 1. Executive Summary

Phase 8.4C.4 established that while Candidate Policy D operates safely with $0.00\%$ production errors and $100.0\%$ functional response invariance, tail latency equivalence at p95 was rejected ($\Delta_{\text{p95}} = +139.29\text{ ms}$, exceeding the $\pm 100.0\text{ ms}$ margin) and peak native working set memory breached the $\pm 100\text{ MB}$ margin by $+2.51\text{ MB}$.

This audit forensically inspects `backend/shadow_engine.py`, `backend/main.py`, `backend/local_feature_engine.py`, telemetry I/O, and CPU/memory profiles to pinpoint the exact operations responsible for resource competition between Policy A (authoritative) and Policy D (shadow).

---

## 2. Resource Bottleneck Identification & Severity Matrix

The following table summarizes all identified resource bottlenecks across CPU time, native memory, thread scheduling, image preprocessing, and I/O overhead:

| Bottleneck ID | Subsystem / Operation | Severity | Empirical Evidence | Mechanism of Resource Contention | Recommended Engineering Action |
| :--- | :--- | :---: | :--- | :--- | :--- |
| **BN-01** | `_compute_sift_inliers` (Repeated Reference SIFT & Disk I/O) | **HIGH** | Phase 8.4C.3 Slow condition tail latency: $\Delta_{\text{p95}} = +159.32\text{ ms}$. Gate 5 calls `cv2.imread()` & `sift.detectAndCompute()` up to 3 times per query. | Uncached disk reads and redundant SIFT feature extraction on static reference gallery images consume 40–80 ms of CPU time and allocate temporary OpenCV C++ matrices on the heap. | Implement an immutable, thread-safe SIFT descriptor cache for reference gallery views in `ShadowEngine`. |
| **BN-02** | OpenCV Multi-Core Thread Spawning (Unbounded OpenMP/TBB) | **HIGH** | Phase 8.4C.4 p95 normal CI: `[+33.19 ms, +245.39 ms]`. OpenCV `cv2.findHomography` and `sift.detectAndCompute` default to all available cores. | Background worker threads spawn multi-core threads across all CPU cores during RANSAC, directly starving Policy A's main request pipeline during complex image processing. | Enforce single-threaded OpenCV execution (`cv2.setNumThreads(1)`) within shadow worker threads. |
| **BN-03** | Synchronous Full-Resolution Image Copy in Request Path | **MEDIUM** | Baseline vs Normal shadow peak RSS jumped from 990.35 MB to 1092.86 MB ($\Delta_{\text{peak}} = +102.51\text{ MB}$). | `submit_shadow_evaluation` performs `image.copy()` on the synchronous FastAPI request thread, duplicating high-res PIL rasters (up to 36 MB per 4K image) even when Gates 1–4 discard the image. | Implement selective/lazy downscaling in `submit_shadow_evaluation`, downscaling to $\le 800\text{px}$ prior to queue buffering and bypassing copy when scalar gates apply. |
| **BN-04** | Synchronous Telemetry File Flush Under Lock | **LOW-MEDIUM** | In `ShadowTelemetryLogger`, every event opens file, writes, and calls `f.flush()` while holding `self._lock`. | Concurrent worker completion and queue saturation drops contend on `self._lock` and disk write I/O, causing micro-stalls in worker loop turnaround. | Buffer file handle or isolate telemetry logging to prevent lock contention with worker threads. |
| **BN-05** | Redundant Image Preprocessing (Double Downscaling) | **LOW** | Image is copied on submission, then downscaled with `LANCZOS` in `_compute_sift_inliers`, then cropped into 9 patches for local CLIP. | Repeated image allocations and resizing steps increase transient memory fragmentation in LibTorch/OpenCV. | Pre-scale input once upon shadow admission if geometric verification corridor is reachable. |

---

## 3. Detailed Root-Cause Analysis

### 3.1 CPU Contention vs. Memory Pressure vs. Model Initialization
- **Model Initialization**: Verified that CLIP weights, FAISS indices (210 vectors), and Grounded Knowledge bases are pre-loaded at FastAPI application lifespan startup (`backend/main.py:518-525`). Model loading does NOT occur per request.
- **CPU Contention**: The primary driver of the p95 tail expansion is CPU core starvation. Because OpenCV does not restrict internal multi-threading (`cv2.getNumThreads()` returns host core count), when a shadow thread invokes SIFT or RANSAC, it consumes 100% of available CPU cores. When Policy A concurrently handles an exception ticket, geo-boost calculation, or image decode, it experiences thread preemption.
- **Memory Pressure**: The native RSS Working Set expansion ($\Delta = +102.51\text{ MB}$) is driven by:
  1. Multiple uncompressed PIL image objects buffered in the 10-task admission queue.
  2. Temporary `cv::Mat` allocation buffers created and freed by LibTorch and OpenCV C++ extensions. Because the native C runtime allocator does not immediately return free memory pages to the Windows kernel, the working set expands during bursty traffic blocks.

---

## 4. Optimization Candidates for Task 2 Selection

To ensure strict production invariants (Policy A unaffected, zero changes to recognition logic or thresholds), we select three targeted, low-risk optimizations:

1. **Optimization A: Reference SIFT Descriptor Pre-Caching**:
   - Cache pre-extracted `(keypoints, descriptors)` for candidate reference images in an immutable thread-safe dictionary within `ShadowEngine`.
   - Re-use cached descriptors during SIFT matching; eliminate `cv2.imread()` disk access and reference feature extraction on every query.
2. **Optimization B: OpenCV Single-Thread Scoping for Shadow Execution**:
   - Explicitly bound OpenCV worker thread concurrency to 1 (`cv2.setNumThreads(1)`).
   - Prevents shadow workers from monopolizing all CPU cores, preserving CPU cache and scheduler availability for Policy A.
3. **Optimization C: Scaled Image Buffering for Shadow Admission**:
   - In `submit_shadow_evaluation`, downscale images exceeding $800\text{px}$ immediately before buffering in the admission queue, and skip image copying when scalar gating criteria determine `image` will not be accessed.
   - Reduces queue memory footprint from ~36 MB per image to $<1.5\text{ MB}$, directly eliminating transient RSS spikes.

