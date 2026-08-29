# Role Validation

Use this reference when designing or executing validation for a BridgeSpec or BridgeRun. Validate the three roles separately, then validate their relationship. Never infer whole-bridge correctness from one successful tool call.

## Validation layers

Run the least invasive layer that supplies the required evidence:

1. **Offline contract validation** checks a sanitized BridgeRun record without network access, credentials, messages, or charges. Run it for every adapter, policy, and validator change.
2. **Operational preflight** uses read-only identity, health, capability, endpoint, and schema probes. It proves current readiness but does not prove message delivery.
3. **Live end-to-end validation** captures one completed sender snapshot, performs exactly one authorized send, and verifies the receiver. Use it only when the user requests live or end-to-end proof and has approved the exact destination and payload. Obtain separate approval for any potential charge.

A higher layer does not erase a lower-layer failure. Stop before a live send when sender, receiver, or bridge preflight is invalid.

## Sender gates

The sender passes only when:

- the adapter identity and exact source endpoint are resolved;
- authentication and read-only health checks pass;
- `read` and `detect-completion` are available;
- one immutable source snapshot contains usable content and source evidence; and
- completion is supported by an explicit final signal or persisted snapshot, not timeout alone.

Record the completion policy and whether later edits require another BridgeRun. A visible partial response or unsupported inference is not sender evidence.

## Receiver gates

The receiver passes only when:

- the adapter identity and exact destination endpoint are resolved;
- authentication, health, and `send` capability pass;
- the effective payload is compatible without an unauthorized loss; and
- the adapter exposes the evidence capability required by the BridgeSpec: `delivery-receipt` for a receipt-dependent `delivered` claim and `history-readback` for `verified`.

After a live send, distinguish an explicit accepted result, a stable receipt, and independent read-back. Assistant prose is not receiver evidence.

## Bridge gates

The bridge passes only when:

- its recorded sender and receiver endpoint IDs match the validated roles;
- mapping is `lossless`, or every transformation is explicitly authorized and recorded;
- authorization matches the exact direction, endpoints, effective payload, and lifetime;
- any incremental cost has separate approval;
- one correlation identifier links source, send result, and read-back evidence;
- exactly one send attempt occurred and read-back found no duplicate; and
- the evidence supports the required assurance level.

An accepted but unverified send may be a valid result only when the BridgeSpec requires no more than `accepted`. Never retry merely to raise assurance after an accepted result.

## Deterministic record validation

Use `scripts/validate_bridge_run.py` for a completed, sanitized BridgeRun record:

```text
python skills/messenger-bridge/scripts/validate_bridge_run.py <bridge-run.json>
```

The JSON object contains `sender`, `receiver`, and `bridge` objects. The sender records adapter and endpoint IDs, capabilities, health, authentication, and a completed `snapshot` with `content`, `source_evidence`, and `completion_evidence`. The receiver records adapter and endpoint IDs, capabilities, health, authentication, and `payload_compatible`. The bridge records endpoint links, mapping and authorization, cost approval state, correlation evidence, effective payload, send count, required assurance, and the structured receiver result.

The validator emits JSON containing independent role verdicts, computed assurance, and stable issue codes. Exit code `0` means all roles pass; `1` means one or more role gates fail; `2` means the input could not be read or parsed. The validator performs no network or messaging operation and must never receive secrets or private runtime logs.

## Test matrix

Routine tests must include:

- a complete `verified` run that passes all roles;
- missing sender completion capability or evidence;
- missing receiver send or assurance capability;
- unauthorized transformation or lossless payload mutation;
- duplicate or repeated send evidence;
- a `verified` requirement with only accepted or delivered evidence; and
- a billable run without explicit cost approval.

Keep fixtures synthetic. A live test must use a fresh marker, sanitize retained evidence, and stop after the first accepted result even when final read-back fails.
