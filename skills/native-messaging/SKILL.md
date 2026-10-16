---
name: native-messaging
description: Send user-authorized messages and attachments through the existing Hermes messaging transports using the official hermes send CLI. Use for Telegram delivery, sending an artifact to an existing configured chat, cross-channel delivery requests, and diagnosing missing send_message tools without creating duplicate integrations.
---
# Native messaging delivery

Use the existing transport; do not configure another bot, copy credentials to a voice client, or claim sending is unavailable merely because no model tool named send_message appears. Some Hermes versions intentionally omit that model tool while retaining the official `hermes send` CLI.

## Resolve and authorize

1. Resolve the user's requested content/artifact from the current conversation and actual source record. For “send that”, inspect the preceding result rather than asking again when the referent is clear. Confirm the file exists in this runtime; an artifact path in another isolated process is not automatically accessible.
2. Check `hermes send --help` and `hermes send --list telegram --json` (or the requested platform). Use the existing home target for a bare “send to Telegram” only when it is configured and consistent with the intended recipient. If missing or ambiguous, ask; do not guess a chat ID. Do not disclose private destination IDs unnecessarily.
3. Send only content and recipients authorized by the user. A general capability test does not authorize contacting unrelated people. Preserve any real runtime approval requirement; do not disable it or quietly widen scopes.

## Send through the native CLI

Some profiles strip messaging credentials from the agent's terminal environment even while the gateway is connected. If the profile provides `$HERMES_HOME/bin/hermes-native-send`, use that launcher in place of `hermes send` below, including for target discovery. It ONLY loads that profile's existing credential-file reference and home destination into the child environment, then execs the official CLI. Do not improvise token-reading shell commands or copy tokens into dotenv/config/chat. Missing launcher/configuration is a specific environment issue, not a disconnected bot. The loader is not an authorization boundary; all recipient and user-approval checks still apply.

Use a properly shell-quoted command in the existing execution environment:

```bash
hermes send --to telegram --json 'Requested message text'
hermes send --to telegram --json 'MEDIA:/absolute/path/to/image.png'
```

`--file` reads a TEXT message body; it is NOT an attachment flag. Use `MEDIA:<path>` inside the message for images/documents. Use the runtime's installed `hermes` executable, checking `command -v hermes` if needed. Never include bot tokens in commands, prompts, or logs. Do not implement direct Bot API calls when the supported CLI can do the job.

## Verify without duplicate sends

Inspect the exit code AND JSON result. Record the platform's delivery/message receipt when returned, and report only what it establishes: accepted/sent, not read by the person. The local artifact or a MEDIA marker alone is not a delivery receipt.

If execution returns a running process/session handle, follow THAT process to completion; do not launch another send. On timeout or lost response, treat delivery as uncertain. Check available receipts or ask the recipient before retrying; an ambiguous result is not permission to send a duplicate. Stop on an actual failure and report the specific missing target/permission/transport problem rather than falsely saying the whole integration is absent.
