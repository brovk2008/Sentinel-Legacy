import sys
from pathlib import Path
import pytest

root_dir = Path(__file__).parent.parent.parent.resolve()
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sentinel.ledger.writer import AuditLedger


def verify_entries_mock(entries: list[dict]) -> tuple[bool, int | None]:
    expected_prev = AuditLedger.GENESIS_HASH
    for entry in entries:
        content = {
            "agent_id": entry["agent_id"],
            "action": entry["action"],
            "resource_id": entry["resource_id"],
            "policy_id": entry["policy_id"],
            "decision": entry["decision"],
            "tier": entry["tier"],
            "context_snapshot": entry["context_snapshot"],
            "cedar_detail": entry["cedar_detail"],
        }
        computed = AuditLedger._compute_hash(content, expected_prev)
        if computed != entry["entry_hash"] or entry["prev_entry_hash"] != expected_prev:
            return False, entry["sequence_num"]
        expected_prev = entry["entry_hash"]
    return True, None


def test_chain_tamper_detection():
    """Simulates a row modification and verifies detection per §20 blueprint."""
    entries = []
    prev_hash = AuditLedger.GENESIS_HASH

    for i in range(5):
        content = {
            "agent_id": f"agt_{i}",
            "action": "order.read",
            "resource_id": "CUST-001",
            "decision": "ALLOW",
            "policy_id": "DATA-012",
            "tier": 1,
            "context_snapshot": {},
            "cedar_detail": {},
        }
        entry_hash = AuditLedger._compute_hash(content, prev_hash)
        entries.append({
            **content,
            "entry_hash": entry_hash,
            "prev_entry_hash": prev_hash,
            "sequence_num": i + 1,
        })
        prev_hash = entry_hash

    # Initial chain is valid
    is_valid, _ = verify_entries_mock(entries)
    assert is_valid

    # Tamper with entry #2 (index 1)
    entries[1]["decision"] = "ALLOW_TAMPERED"

    # Verify must detect tamper at sequence 2
    valid, bad_seq = verify_entries_mock(entries)
    assert not valid
    assert bad_seq == 2
