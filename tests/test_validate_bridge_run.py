from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "messenger-bridge"
    / "scripts"
    / "validate_bridge_run.py"
)
SPEC = importlib.util.spec_from_file_location("validate_bridge_run", SCRIPT_PATH)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def valid_record() -> dict:
    payload = {"body": "synthetic message [MB-E2E-TEST-01]", "attachments": []}
    return {
        "sender": {
            "adapter_id": "synthetic-source",
            "endpoint_id": "source-endpoint",
            "endpoint_confirmed": True,
            "endpoint_confirmation_evidence": "user confirmed displayed source session and endpoint",
            "capabilities": ["read", "detect-completion"],
            "healthy": True,
            "authenticated": True,
            "snapshot": {
                "completed": True,
                "content": payload,
                "source_evidence": "synthetic-source-event",
                "completion_evidence": "persisted-snapshot",
            },
        },
        "receiver": {
            "adapter_id": "synthetic-receiver",
            "endpoint_id": "receiver-endpoint",
            "endpoint_confirmed": True,
            "endpoint_confirmation_evidence": "user confirmed displayed destination session and endpoint",
            "capabilities": ["send", "delivery-receipt", "history-readback"],
            "healthy": True,
            "authenticated": True,
            "payload_compatible": True,
        },
        "bridge": {
            "bridge_spec_id": "synthetic-bridge",
            "correlation_id": "MB-E2E-TEST-01",
            "correlation_evidence": "marker in source and receiver read-back",
            "sender_endpoint_id": "source-endpoint",
            "receiver_endpoint_id": "receiver-endpoint",
            "mapping_policy": "lossless",
            "effective_payload": copy.deepcopy(payload),
            "authorization": {
                "approved": True,
                "matches_spec": True,
                "incremental_cost": False,
                "cost_approved": False,
            },
            "send_attempts": 1,
            "required_assurance": "verified",
            "receiver_result": {
                "accepted": True,
                "receipt_id": "synthetic-receipt",
                "readback_match": True,
                "matching_messages": 1,
            },
        },
    }


def issue_codes(result: dict, role: str) -> set[str]:
    return {issue["code"] for issue in result["issues"] if issue["role"] == role}


class ValidateBridgeRunTests(unittest.TestCase):
    def test_complete_verified_run_passes_all_roles(self) -> None:
        result = VALIDATOR.validate_bridge_run(valid_record())

        self.assertTrue(result["valid"])
        self.assertEqual(result["achieved_assurance"], "verified")
        self.assertTrue(all(role["valid"] for role in result["roles"].values()))

    def test_sender_requires_completion_capability_and_evidence(self) -> None:
        record = valid_record()
        record["sender"]["capabilities"].remove("detect-completion")
        record["sender"]["snapshot"]["completion_evidence"] = ""

        result = VALIDATOR.validate_bridge_run(record)

        self.assertFalse(result["roles"]["sender"]["valid"])
        self.assertIn("sender.capability.detect-completion", issue_codes(result, "sender"))
        self.assertIn("sender.completion_evidence.required", issue_codes(result, "sender"))

    def test_sender_requires_user_endpoint_confirmation(self) -> None:
        record = valid_record()
        record["sender"]["endpoint_confirmed"] = False
        record["sender"]["endpoint_confirmation_evidence"] = ""

        result = VALIDATOR.validate_bridge_run(record)

        self.assertFalse(result["roles"]["sender"]["valid"])
        self.assertIn("sender.endpoint_confirmed.required", issue_codes(result, "sender"))
        self.assertIn(
            "sender.endpoint_confirmation_evidence.required", issue_codes(result, "sender")
        )

    def test_receiver_requires_send_and_readback_capabilities(self) -> None:
        record = valid_record()
        record["receiver"]["capabilities"] = ["delivery-receipt"]

        result = VALIDATOR.validate_bridge_run(record)

        self.assertFalse(result["roles"]["receiver"]["valid"])
        self.assertIn("receiver.capability.send", issue_codes(result, "receiver"))
        self.assertIn("receiver.capability.history-readback", issue_codes(result, "receiver"))

    def test_receiver_requires_user_endpoint_confirmation(self) -> None:
        record = valid_record()
        record["receiver"]["endpoint_confirmed"] = False
        record["receiver"]["endpoint_confirmation_evidence"] = ""

        result = VALIDATOR.validate_bridge_run(record)

        self.assertFalse(result["roles"]["receiver"]["valid"])
        self.assertIn("receiver.endpoint_confirmed.required", issue_codes(result, "receiver"))
        self.assertIn(
            "receiver.endpoint_confirmation_evidence.required", issue_codes(result, "receiver")
        )

    def test_bridge_rejects_lossless_mutation_and_duplicate_send(self) -> None:
        record = valid_record()
        record["bridge"]["effective_payload"]["body"] = "mutated"
        record["bridge"]["send_attempts"] = 2
        record["bridge"]["receiver_result"]["matching_messages"] = 2

        result = VALIDATOR.validate_bridge_run(record)

        self.assertFalse(result["roles"]["bridge"]["valid"])
        self.assertIn("bridge.lossless.mismatch", issue_codes(result, "bridge"))
        self.assertIn("bridge.send_attempts.single", issue_codes(result, "bridge"))
        self.assertIn("bridge.duplicate.detected", issue_codes(result, "bridge"))

    def test_authorized_transform_passes(self) -> None:
        record = valid_record()
        record["bridge"]["mapping_policy"] = "transform"
        record["bridge"]["effective_payload"]["body"] = "authorized summary [MB-E2E-TEST-01]"
        record["bridge"]["transform_authorized"] = True
        record["bridge"]["transform_notes"] = ["Summarized the source body"]

        result = VALIDATOR.validate_bridge_run(record)

        self.assertTrue(result["valid"])

    def test_verified_requirement_rejects_receipt_only(self) -> None:
        record = valid_record()
        record["bridge"]["receiver_result"]["readback_match"] = False
        record["bridge"]["receiver_result"]["matching_messages"] = 0

        result = VALIDATOR.validate_bridge_run(record)

        self.assertFalse(result["roles"]["bridge"]["valid"])
        self.assertEqual(result["achieved_assurance"], "delivered")
        self.assertIn("bridge.assurance.insufficient", issue_codes(result, "bridge"))

    def test_billable_run_requires_cost_approval(self) -> None:
        record = valid_record()
        record["bridge"]["authorization"]["incremental_cost"] = True

        result = VALIDATOR.validate_bridge_run(record)

        self.assertFalse(result["roles"]["bridge"]["valid"])
        self.assertIn("bridge.cost_approval.required", issue_codes(result, "bridge"))


if __name__ == "__main__":
    unittest.main()
