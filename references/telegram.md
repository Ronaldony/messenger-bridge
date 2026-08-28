# Telegram Adapter

Read this reference only when the selected messenger platform is Telegram.

## Required capabilities

Use the Telegram MCP app selected in the ChatGPT message for the actual send. Use its read-only `search_messages` or `list_messages` operation from Codex for receipt verification. Resolve the exact account and chat or channel ID before sending.

Do not use `wait_for_new_message` or `wait_for_settled_message` for outgoing channel or self-authored posts. Those event operations can miss channel and self-originated messages.

## Local tunnel recovery

Installation does not prove connectivity. If Telegram tools return tunnel `404`, `429`, or unavailable errors, verify the local MCP endpoint and Secure MCP Tunnel readiness. When the installation paths are known, run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File "<skill-directory>\scripts\start-telegram-relay-stack.ps1" `
  -TelegramMcpRoot "<telegram-mcp-root>" `
  -TunnelClientPath "<tunnel-client.exe>" `
  -TunnelProfile "<profile>"
```

Continue only when the local MCP port is reachable and the tunnel `/readyz` response is `ready`. Retry one read-only Telegram probe after recovery.

## Receipt

Read the exact destination during the same Codex turn and locate the unique marker. Require the returned Telegram text to match the ChatGPT response, then record the Telegram message ID and timestamp.
