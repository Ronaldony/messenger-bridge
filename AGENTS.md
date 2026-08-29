# Repository Guidelines

## Purpose and Structure

This repository publishes the platform-neutral `messenger-bridge` Agent Skill. Telegram and ChatGPT are supported examples, not fixed endpoints.

- `skills/messenger-bridge/SKILL.md`: shared model, routing, safety boundaries, and core workflow.
- `agents/openai.yaml`: UI metadata and invocation policy; recheck it when scope or triggers change.
- `references/environment-setup.md`: discovery and setup when no compatible adapter is ready.
- `references/adapters/<service>.md`: service capabilities, authentication, endpoint rules, and authoritative sources.
- `scripts/adapters/<service>/`: deterministic setup or recovery helpers.

Use progressive disclosure. Keep conditional details in references and link them from `SKILL.md`; do not duplicate them. Add an adapter reference only for a concrete bridge use case.

## Domain Invariants

Model each directed connection as `sender -> bridge -> receiver`. Roles are contextual; represent bidirectional exchange as two BridgeSpecs. Judge adapters by actual capabilities (`read`, `detect-completion`, `send`, `delivery-receipt`, and `history-readback`), not product or package names.

Preserve exact endpoint resolution, explicit payload transformations, assurance levels, and the single-send boundary. Do not silently add scheduled jobs, persistent monitoring, or background runtimes. Installation, authentication, permission changes, and live sends require applicable authorization.

## Cost Control and Approval

Design bridges for zero incremental cost whenever the required capabilities, assurance, security, and reliability can still be met. Prefer healthy existing connections, already-paid entitlements, local adapters, and free official interfaces before paid APIs, hosted tunnels, premium plugins, cloud runtimes, or metered AI and messaging operations. Compare total operational cost, including recurring hosting, storage, network egress, verification reads, and retries; do not describe an option as free when it only shifts cost elsewhere.

Before any action that can create, increase, or commit a charge, explain the provider, billable action, pricing unit, expected amount or range, recurrence, uncertainty, and no-cost alternative. Obtain the user's explicit approval immediately before execution. General approval to build, install, authenticate, test, or send does not authorize a charge. Approval is limited to the named action, provider, cost ceiling, and lifetime; obtain new approval when any of them changes. If cost cannot be determined or free-tier eligibility cannot be verified, treat the action as potentially billable and stop for approval. Read-only pricing research may proceed without purchase authorization.

## Content and Script Conventions

Write concise, imperative Markdown and use descriptive kebab-case filenames. Prefer official service documentation and primary repositories; distinguish verified capabilities from assumptions.

PowerShell scripts should use `Set-StrictMode`, stop on errors, validate resolved paths, and use bounded readiness timeouts. Emit machine-readable JSON on stdout and diagnostics on stderr. Never embed credentials, account identifiers, tunnel URLs, or machine-specific paths.

## Validation

There is no application build or package manifest. Do not invent `npm run build` or `npm test` commands. Validate the skill structure with:

```text
python <skill-creator>/scripts/quick_validate.py skills/messenger-bridge
npx skills add . --list
```

Syntax-check changed scripts and exercise only non-destructive, non-billable health paths. Routine tests must not send messages, create credentials, change permissions, expose tunnels, or consume paid quotas. A live end-to-end test requires explicit approval, an exact destination, one marker-bearing send, sanitized evidence, and separate cost approval when any step may be billable.

Evaluate behavior changes against realistic cases: minimal-intent routing, missing adapters, ambiguous endpoints, unsupported payload fields, accepted-but-unverified delivery, and duplicate-send prevention. Claim success only from fresh command output or observable delivery evidence.

## Security and Contributions

Never commit tokens, passwords, login codes, session strings, private endpoint identifiers, runtime logs, or personal messages. Recheck third-party adapter provenance, license, maintenance, and current documentation.

Use focused Conventional Commits such as `feat: add discord adapter guidance` or `fix: prevent retry after accepted send`. Pull requests should name the affected contract or adapter, list validation, cite new integration sources, and state whether a live send occurred. Include only sanitized evidence.
