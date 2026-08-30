# Adapter Discovery and Environment Setup

Read this reference only when a required adapter is missing, disconnected, unverified, or explicitly requested for setup. The goal is to turn a service-level request into a safe SetupPlan without requiring the user to understand MCP, plugins, connectors, APIs, or browser automation.

## Interpret before selecting technology

Extract what the user actually needs:

- sender and receiver services;
- direction and candidate source and destination sessions or channels;
- one-shot delivery or ongoing automation;
- message body, formatting, attachments, threads, and reply context;
- required identity, such as a bot, webhook, application, or the user's own account; and
- required assurance: `accepted`, `delivered`, or `verified`.

Default to one-shot delivery, text payload, and the strongest evidence available. Do not infer an exact source, destination, account authority, or persistent operation. Treat endpoints named in the initial request as candidates until the user confirms the resolved identities in a new reply. Do not ask whether the user wants MCP; MCP is one possible implementation.

## Discover the environment first

Inspect in this order and stop when a healthy option satisfies the BridgeSpec:

1. Built-in tools already available to the current host.
2. Connected plugins, connectors, or apps with the needed service operations.
3. Relevant but unconnected plugins or connectors discoverable through the host's integration catalog.
4. Configured MCP servers and their exposed tool schemas.
5. Known local adapters, processes, endpoints, and client configuration.
6. Official service APIs or webhooks.
7. Maintained third-party adapters from a verified source.
8. Browser automation only when no purpose-built interface fits and its lower reliability is acceptable.

Use read-only health, identity, schema, and endpoint-metadata probes where available. Before endpoint confirmation, do not retrieve message bodies or start a message wait; if a discovery result incidentally includes content, do not use it as a source snapshot. Inspect whether credentials are configured without printing or reading their secret values. Map actual operations to `read`, `detect-completion`, `send`, `delivery-receipt`, and `history-readback` rather than trusting an installation name.

Detect the host OS, architecture, shell, available runtimes, and service-management constraints before selecting an installation or recovery path. Treat OS-specific scripts as optional helpers, not as adapter requirements. If a helper does not support the current host, use the adapter's documented platform-neutral interface or select a compatible alternative; do not translate commands mechanically across shells.

When the host catalog returns an unconnected plugin or connector, suggest only an exact service or capability match and explain the required connection action. Do not claim it is installed, connected, or sufficient until its connection and tool schema are verified. Continue any research and planning that does not depend on the connection.

## Research capability gaps

Research current options when discovery finds no compatible adapter. Start with the service's official integration, API, authentication, permissions, rate-limit, and webhook documentation. For each third-party candidate, inspect its primary repository and current release documentation rather than relying on a package name or search snippet.

Compare candidates on:

- required sender and receiver capabilities;
- bot, webhook, app, or personal-account identity;
- destination coverage, including direct messages, channels, groups, topics, and threads;
- achievable assurance and independent read-back;
- credential scope, storage, transport security, and least-privilege controls;
- host and operating-system compatibility;
- one-shot versus persistent runtime requirements;
- installation provenance, pinned version or commit, license, maintenance, and test evidence; and
- operational complexity, rate limits, and recovery behavior.

Do not recommend an unverified package solely because its name matches the service. Cite the authoritative sources used and explain why the recommendation fits the user's goal.

## Adapter reference contract

Create a platform reference under `references/adapters/<service>.md` only after that service has a concrete bridge use case. Each platform reference must record:

- supported identity models and the situations each one fits;
- official interfaces plus any reviewed connector or MCP candidates;
- capability and assurance mapping based on actual operations;
- the smallest service-specific questions that may remain after discovery;
- installation, authentication, permissions, and secret-handling boundaries;
- supported operating systems and runtimes, plus the platform-neutral behavior contract for any OS-specific helper;
- endpoint resolution, payload limits, verification, and retry behavior;
- health checks and recovery steps; and
- authoritative documentation and primary repository links that must be rechecked before setup.

If no platform reference exists, use the generic research process above and propose a SetupPlan. Do not imply that the service is already supported or create a speculative reference without a real requirement.

## Produce one actionable SetupPlan

Present the result at the user's level rather than dumping implementation choices:

1. **Interpreted goal**: what will be sent, from where, to which kind of destination, and for how long.
2. **Environment findings**: working capabilities and the exact missing capability.
3. **Recommendation**: one adapter and topology compatible with the detected host, with the decisive reason.
4. **Fallback**: one materially different option and its tradeoff.
5. **User action**: explicit source-session and destination-session selection, plus any login steps, destination details, or approvals.
6. **Validation**: health, identity, endpoint, capability, receipt, and read-back checks.

Ask at most one compact group of related questions at a time. Discover implementation details and endpoint candidates when safe, but always ask the user to confirm the exact source and destination after presenting their service, acting account or session, visible name, stable identifier when available, direction, and proposed action. A low-risk default or a single exact match may be recommended but never auto-selected for message receipt or delivery.

## Authorization and secret handling

- Research and read-only discovery may proceed without installation approval.
- Obtain approval before installing software, changing host configuration, starting a persistent service, authenticating an account, creating a bot or webhook, changing channel permissions, reading or waiting for messenger content, or sending a live test.
- Treat initial endpoint names as discovery hints. Require a new user reply that confirms the resolved source and destination before any message content read, wait, or send action.
- Treat installation approval, account authorization, and message-send authorization as distinct scopes, but combine them into one clearly itemized approval request when they are all required next.
- Direct the user to an official login page, local interactive prompt, OS credential store, or untracked environment file. Never request secrets in chat or echo them in commands, logs, evidence, or BridgeRun records.
- Use least privilege. Expose only the read operations required for discovery and verification plus the exact write operations required by the BridgeSpec.
- Do not store machine-specific paths, account identifiers, or credentials in the skill repository. Reuse host connection state; propose a sanitized, untracked local profile only when it would materially reduce future setup friction.

## Validate before declaring ready

1. Confirm the adapter process or remote endpoint is reachable.
2. Confirm the authenticated service identity with a read-only operation.
3. Resolve source and destination candidates from metadata without reading message bodies.
4. Present the exact sessions and endpoints and obtain the user's explicit selection for both roles.
5. Confirm the required capabilities and payload limits from actual schemas or probes.
6. Prefer a non-sending dry run when the adapter provides one.
7. After explicit payload and live-send authorization, execute one marker-bearing test and report the achieved assurance level.

If setup cannot be completed, report the failed layer—discovery, installation, authentication, authorization, connectivity, capability, destination, or verification—and give the smallest next user action. Do not end with a generic instruction such as "install an MCP server."
