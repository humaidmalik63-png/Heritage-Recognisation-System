"""
Heritage & Monument Recognition System - Persistence & Audit Trail Test
Project No. 30 (SIH 2025): Phase 6.2 Persistence Audit

Verifies:
  1. Exception tickets remain persistent across backend process restarts.
  2. Resolving a ticket records audit history that survives restart.
  3. Duplicate suppression correctly reuses ticket for identical scans without merging unrelated scans.
"""

import json
import logging
import sys
from pathlib import Path

from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from main import app, load_exceptions_log, record_exception_entry, save_exceptions_log

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("audit_persistence")


def run_persistence_audit():
    logger.info("=" * 75)
    logger.info("PHASE 6.2 PERSISTENCE & AUDIT TRAIL VERIFICATION")
    logger.info("=" * 75)

    with TestClient(app) as client:
        # 1. Check existing exceptions loaded from exceptions_log.json
        initial_log = load_exceptions_log()
        initial_count = len(initial_log)
        logger.info(f"Initial tickets loaded from disk: {initial_count}")
        assert initial_count > 0, "Expected existing tickets in exceptions_log.json"

        # Pick the most recent pending ticket
        pending_item = next((item for item in initial_log if item["status"] == "PENDING_REVIEW"), None)
        if not pending_item:
            # Create a new test ticket
            ticket_id = record_exception_entry(
                filename="persistence_test.jpg",
                gatekeeper_score=0.85,
                top_candidate=None,
                reason="Persistence test ticket creation",
                specimen_hash="persist_hash_123",
            )
        else:
            ticket_id = pending_item["id"]

        logger.info(f"Testing resolution on ticket: {ticket_id}")

        # 2. Resolve ticket via POST /api/exceptions/{id}/resolve
        curator_notes = "Field survey confirmed Chola period architectural mandapa; indexed under regional annex."
        res = client.post(
            f"/api/exceptions/{ticket_id}/resolve",
            json={"status": "APPROVED", "curator_notes": curator_notes},
        )
        assert res.status_code == 200, f"Resolution failed: {res.text}"
        resolved_data = res.json()["exception"]
        assert resolved_data["status"] == "APPROVED"
        assert resolved_data["curator_notes"] == curator_notes
        assert len(resolved_data["history"]) >= 2
        logger.info(f"[PASSED] Ticket #{ticket_id} resolved as APPROVED with curator notes.")

        # 3. Simulate Backend Restart (Force fresh re-read from disk)
        logger.info("\n--- Simulating Backend Process Restart ---")
        reloaded_log = load_exceptions_log()
        reloaded_ticket = next((item for item in reloaded_log if item["id"] == ticket_id), None)
        assert reloaded_ticket is not None, f"Ticket {ticket_id} vanished after restart!"
        assert reloaded_ticket["status"] == "APPROVED", f"Expected APPROVED, got {reloaded_ticket['status']}"
        assert reloaded_ticket["curator_notes"] == curator_notes
        assert len(reloaded_ticket["history"]) >= 2
        actions = [h["action"] for h in reloaded_ticket["history"]]
        assert "CREATED" in actions and "RESOLVED" in actions
        logger.info(f"[PASSED] Ticket #{ticket_id} and full audit history survived restart: {actions}")

        # 4. Verify Duplicate Suppression vs. Unrelated Scan Isolation
        logger.info("\n--- Testing Duplicate Suppression vs. Unrelated Scan Isolation ---")
        hash_a = "unique_scan_hash_AAA"
        hash_b = "unique_scan_hash_BBB"

        ticket_a1 = record_exception_entry(
            filename="scan_a.jpg",
            gatekeeper_score=0.78,
            top_candidate=None,
            reason="Scan A initial",
            specimen_hash=hash_a,
        )
        # Identical scan A
        ticket_a2 = record_exception_entry(
            filename="scan_a.jpg",
            gatekeeper_score=0.78,
            top_candidate=None,
            reason="Scan A repeated attempt",
            specimen_hash=hash_a,
        )
        # Distinct scan B
        ticket_b = record_exception_entry(
            filename="scan_b.jpg",
            gatekeeper_score=0.62,
            top_candidate=None,
            reason="Scan B distinct specimen",
            specimen_hash=hash_b,
        )

        assert ticket_a1 == ticket_a2, f"Duplicate scan must reuse ticket! Got {ticket_a1} vs {ticket_a2}"
        assert ticket_b != ticket_a1, f"Unrelated scan B must NOT merge with scan A! Got {ticket_b} == {ticket_a1}"
        logger.info(f"[PASSED] Duplicate suppression verified: Scan A reused {ticket_a1}; Unrelated Scan B created distinct {ticket_b}.")

    logger.info("\n" + "=" * 75)
    logger.info("PERSISTENCE & AUDIT TRAIL AUDIT PASSED 100%!")
    logger.info("=" * 75)


if __name__ == "__main__":
    run_persistence_audit()
