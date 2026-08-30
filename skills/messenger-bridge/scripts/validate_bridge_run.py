#!/usr/bin/env python3
"""Validate a sanitized, completed messenger BridgeRun without external I/O."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any


ASSURANCE_RANK = {"none": 0, "accepted": 1, "delivered": 2, "verified": 3}


def validate_bridge_run(record: Any) -> dict[str, Any]:
    """Return deterministic sender, receiver, and bridge validation results."""
    issues: list[dict[str, str]] = []

    def fail(role: str, code: str, message: str) -> None:
        issues.append({"role": role, "code": code, "message": message})

    def object_field(parent: Mapping[str, Any], field: str, role: str) -> Mapping[str, Any]:
        value = parent.get(field)
        if not isinstance(value, Mapping):
            fail(role, f"{role}.{field}.type", f"{field} must be an object")
            return {}
        return value

    def require_text(parent: Mapping[str, Any], field: str, role: str) -> str:
        value = parent.get(field)
        if not isinstance(value, str) or not value.strip():
            fail(role, f"{role}.{field}.required", f"{field} must be non-empty text")
            return ""
        return value

    def capabilities(parent: Mapping[str, Any], role: str) -> set[str]:
        value = parent.get("capabilities")
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            fail(role, f"{role}.capabilities.type", "capabilities must be a list of strings")
            return set()
        return set(value)

    def require_true(parent: Mapping[str, Any], field: str, role: str) -> None:
        if parent.get(field) is not True:
            fail(role, f"{role}.{field}.required", f"{field} must be true")

    def validate_payload(payload: Any, role: str, field: str) -> bool:
        if not isinstance(payload, Mapping):
            fail(role, f"{role}.{field}.type", f"{field} must be an object")
            return False
        body = payload.get("body")
        attachments = payload.get("attachments", [])
        if body is not None and not isinstance(body, str):
            fail(role, f"{role}.{field}.body_type", "payload body must be text when present")
            return False
        if not isinstance(attachments, list):
            fail(role, f"{role}.{field}.attachments_type", "payload attachments must be a list")
            return False
        if not body and not attachments:
            fail(role, f"{role}.{field}.empty", "payload must contain a body or attachment")
            return False
        return True

    if not isinstance(record, Mapping):
        fail("bridge", "bridge.record.type", "BridgeRun must be an object")
        return _build_result(issues, "none")

    sender = object_field(record, "sender", "sender")
    receiver = object_field(record, "receiver", "receiver")
    bridge = object_field(record, "bridge", "bridge")

    sender_endpoint = require_text(sender, "endpoint_id", "sender")
    require_text(sender, "adapter_id", "sender")
    require_true(sender, "endpoint_confirmed", "sender")
    require_text(sender, "endpoint_confirmation_evidence", "sender")
    sender_caps = capabilities(sender, "sender")
    for capability in ("read", "detect-completion"):
        if capability not in sender_caps:
            fail("sender", f"sender.capability.{capability}", f"sender requires {capability}")
    require_true(sender, "healthy", "sender")
    require_true(sender, "authenticated", "sender")

    snapshot = object_field(sender, "snapshot", "sender")
    require_true(snapshot, "completed", "sender")
    require_text(snapshot, "source_evidence", "sender")
    require_text(snapshot, "completion_evidence", "sender")
    source_payload = snapshot.get("content")
    validate_payload(source_payload, "sender", "snapshot.content")

    receiver_endpoint = require_text(receiver, "endpoint_id", "receiver")
    require_text(receiver, "adapter_id", "receiver")
    require_true(receiver, "endpoint_confirmed", "receiver")
    require_text(receiver, "endpoint_confirmation_evidence", "receiver")
    receiver_caps = capabilities(receiver, "receiver")
    if "send" not in receiver_caps:
        fail("receiver", "receiver.capability.send", "receiver requires send")
    require_true(receiver, "healthy", "receiver")
    require_true(receiver, "authenticated", "receiver")
    require_true(receiver, "payload_compatible", "receiver")

    require_text(bridge, "bridge_spec_id", "bridge")
    require_text(bridge, "correlation_id", "bridge")
    require_text(bridge, "correlation_evidence", "bridge")
    bridge_sender_endpoint = require_text(bridge, "sender_endpoint_id", "bridge")
    bridge_receiver_endpoint = require_text(bridge, "receiver_endpoint_id", "bridge")
    if sender_endpoint and bridge_sender_endpoint != sender_endpoint:
        fail("bridge", "bridge.sender_endpoint.mismatch", "bridge sender endpoint does not match sender")
    if receiver_endpoint and bridge_receiver_endpoint != receiver_endpoint:
        fail("bridge", "bridge.receiver_endpoint.mismatch", "bridge receiver endpoint does not match receiver")

    required_assurance = bridge.get("required_assurance")
    if required_assurance not in {"accepted", "delivered", "verified"}:
        fail("bridge", "bridge.required_assurance.invalid", "required_assurance is invalid")
        required_assurance = "none"
    if required_assurance == "delivered" and "delivery-receipt" not in receiver_caps:
        fail("receiver", "receiver.capability.delivery-receipt", "delivered requires delivery-receipt")
    if required_assurance == "verified" and "history-readback" not in receiver_caps:
        fail("receiver", "receiver.capability.history-readback", "verified requires history-readback")

    mapping_policy = bridge.get("mapping_policy")
    if mapping_policy not in {"lossless", "transform"}:
        fail("bridge", "bridge.mapping_policy.invalid", "mapping_policy must be lossless or transform")
    effective_payload = bridge.get("effective_payload")
    validate_payload(effective_payload, "bridge", "effective_payload")
    if mapping_policy == "lossless" and effective_payload != source_payload:
        fail("bridge", "bridge.lossless.mismatch", "lossless payload differs from the sender snapshot")
    if mapping_policy == "transform":
        require_true(bridge, "transform_authorized", "bridge")
        notes = bridge.get("transform_notes")
        if not isinstance(notes, list) or not notes or any(
            not isinstance(note, str) or not note.strip() for note in notes
        ):
            fail("bridge", "bridge.transform_notes.required", "authorized transforms require change notes")

    authorization = object_field(bridge, "authorization", "bridge")
    require_true(authorization, "approved", "bridge")
    require_true(authorization, "matches_spec", "bridge")
    incremental_cost = authorization.get("incremental_cost")
    if not isinstance(incremental_cost, bool):
        fail("bridge", "bridge.incremental_cost.type", "incremental_cost must be boolean")
    elif incremental_cost and authorization.get("cost_approved") is not True:
        fail("bridge", "bridge.cost_approval.required", "incremental cost requires explicit approval")

    send_attempts = bridge.get("send_attempts")
    if not isinstance(send_attempts, int) or isinstance(send_attempts, bool):
        fail("bridge", "bridge.send_attempts.type", "send_attempts must be an integer")
    elif send_attempts != 1:
        fail("bridge", "bridge.send_attempts.single", "a completed BridgeRun must contain exactly one send attempt")

    receiver_result = object_field(bridge, "receiver_result", "bridge")
    accepted = receiver_result.get("accepted") is True
    if not accepted:
        fail("bridge", "bridge.receiver_result.accepted", "receiver did not return explicit acceptance")
    receipt_id = receiver_result.get("receipt_id")
    has_receipt = isinstance(receipt_id, str) and bool(receipt_id.strip())
    if has_receipt and "delivery-receipt" not in receiver_caps:
        fail("receiver", "receiver.receipt.capability", "receipt evidence requires delivery-receipt")

    readback_match = receiver_result.get("readback_match") is True
    matching_messages = receiver_result.get("matching_messages")
    if not isinstance(matching_messages, int) or isinstance(matching_messages, bool) or matching_messages < 0:
        fail("bridge", "bridge.matching_messages.type", "matching_messages must be a non-negative integer")
        matching_messages = 0
    if matching_messages > 1:
        fail("bridge", "bridge.duplicate.detected", "read-back found duplicate matching messages")
    if readback_match and matching_messages != 1:
        fail("bridge", "bridge.readback.count", "a read-back match requires exactly one matching message")
    if readback_match and "history-readback" not in receiver_caps:
        fail("receiver", "receiver.readback.capability", "read-back evidence requires history-readback")

    achieved_assurance = "none"
    if accepted:
        achieved_assurance = "accepted"
    if accepted and has_receipt:
        achieved_assurance = "delivered"
    if accepted and readback_match and matching_messages == 1:
        achieved_assurance = "verified"
    if ASSURANCE_RANK[achieved_assurance] < ASSURANCE_RANK[required_assurance]:
        fail(
            "bridge",
            "bridge.assurance.insufficient",
            f"required {required_assurance}, achieved {achieved_assurance}",
        )

    return _build_result(issues, achieved_assurance)


def _build_result(issues: list[dict[str, str]], achieved_assurance: str) -> dict[str, Any]:
    roles = {
        role: {"valid": not any(issue["role"] == role for issue in issues)}
        for role in ("sender", "receiver", "bridge")
    }
    return {
        "valid": all(result["valid"] for result in roles.values()),
        "roles": roles,
        "achieved_assurance": achieved_assurance,
        "issues": issues,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", help="BridgeRun JSON file, or - for stdin")
    args = parser.parse_args(argv)

    try:
        if args.record == "-":
            record = json.load(sys.stdin)
        else:
            with Path(args.record).open(encoding="utf-8") as stream:
                record = json.load(stream)
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, ensure_ascii=False))
        return 2

    result = validate_bridge_run(record)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
