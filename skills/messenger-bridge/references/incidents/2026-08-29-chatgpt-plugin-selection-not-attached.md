# Incident: ChatGPT Adapter Routing Was Not Verified

- **Incident ID:** `INC-2026-08-29-001`
- **Date:** 2026-08-29
- **Stage:** ChatGPT in-sender preflight
- **Impact:** One unnecessary ChatGPT request; no Telegram delivery
- **Cost impact:** No confirmed incremental charge
- **Status:** Open; the corrected delivery succeeded, but the pre-send workflow was not cleanly rehearsed

## Summary

An end-to-end ChatGPT-to-Telegram test was sent after the agent incorrectly concluded that the Telegram plugin had been attached to the ChatGPT composer. The plugin name had only been inserted as plain text. ChatGPT returned prose claiming that an OpenAI safety check blocked the request, but no structured tool call occurred and an independent Telegram search found no matching marker.

A later authorized correction produced a structured Telegram tool result and an exact receiver read-back even though the corrected turn had no visible inline selection pill. Therefore, the missing pill correlated with the first failure but is not proven to be its sole cause. The confirmed defect was proceeding from unverified routing state and then overstating the cause.

## Expected and actual state

The expected composer state contained a platform-recognized inline plugin selection for the exact Telegram adapter. A previously successful message exposed an inline selection pill with the plugin identifier and later displayed a tool-call result.

The failed message ended with the adapter name as ordinary text. It had no inline selection pill, tool-call card, or structured adapter result. Telegram remained unchanged.

## Confirmed process root cause

The browser workflow clicked a generic picker hint and then typed the adapter name with coordinate-based input. Focus returned to the main composer, so the adapter name was appended to the prompt instead of filtering the picker. The picker closing was incorrectly interpreted as successful selection. No pre-send postcondition distinguished explicit per-message selection from connected-tool context retained by the conversation.

The exact service-side reason for the first turn's non-invocation remains unconfirmed. The assistant's safety prose was not a structured tool error, and the successful correction disproved the claim that a visible pill is universally required.

## Faulty agent judgments

1. The agent inferred selection from visible text instead of verifying the platform's semantic attachment state.
2. It did not define or check a postcondition for the selection step before requesting send approval.
3. It treated ChatGPT's prose about a safety block as an authoritative tool error before checking for a tool-call card or structured result.
4. During the correction, it used an Enter keystroke that submitted unexpectedly before the intended attachment check; the successful result does not make that interaction safe.
5. It relied on visual similarity to a prior successful message even though the DOM evidence differed materially.
6. It initially promoted a correlation—the absent pill—into a sole-cause claim without a controlled comparison.

The topology choice itself was not the defect: an already working in-sender adapter was a valid choice. The failure was an unverified UI transition inside that topology.

## Evidence

- The successful message contained an inline plugin-selection element associated with the Telegram plugin ID.
- The failed message contained only ordinary text naming the plugin.
- The failed assistant response contained no tool-call UI or structured receiver result.
- The plugin permission was configured to allow actions, so a permission prompt was not the blocking layer.
- The Telegram adapter was reachable and independently resolved the test destination.
- A marker search returned no result, confirming that no delivery occurred.
- The authorized correction displayed a structured tool result, and independent Telegram read-back returned exactly one matching message.
- The corrected turn had no visible current-turn pill, demonstrating that established conversation context can still expose the tool.

Do not store account names, chat IDs, private endpoint identifiers, payloads, or credentials in this record.

## Prevention gates

Before sending through a ChatGPT in-sender tool:

1. Identify whether routing is explicit per-message selection or connected-tool context retained by the conversation.
2. For explicit selection, open the plugin picker, target its actual search input, select the exact result, and verify the platform-recognized pill or equivalent attachment.
3. For retained context, verify semantic tool availability exposed by the platform; do not infer it from plain text or from pill absence alone.
4. Verify the payload, destination, Chat mode, and send boundary independently of routing state.
5. Use a keystroke that cannot submit while selecting or inspecting tools, and verify the final composer state immediately before the authorized send.
6. Stop before sending if any required postcondition is ambiguous.

After sending, count only a platform tool-call card and structured tool result as invocation evidence. Assistant prose is not tool evidence. For `verified` assurance, independently read the Telegram destination and match the marker and payload.

If the tool is not invoked, do not retry automatically. Confirm absence through receiver read-back, repair the selection step, obtain any newly required approval, and allow at most the BridgeSpec's authorized correction.

## Closure criteria

Close this incident only after a fresh, intentionally controlled test proves all three stages: pre-send routing is semantically verified for the selected routing mode, ChatGPT displays a structured Telegram tool result, and Telegram read-back returns the matching marker without a duplicate. An accidental submission that happens to succeed does not satisfy the first stage.
