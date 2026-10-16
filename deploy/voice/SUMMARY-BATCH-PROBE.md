# Isolated larger-deliverable Voice summary baseline

Use the SAME permission-repaired Voice thread. Do not edit the realtime prompt, AGENTS.md, model, config, or any production state. This tests semantic summary, NOT the earlier verbatim-final contract; no requirement has silently been retired.

Script: `/home/codex/Documents/Codex/summary-probe/exo_voice_summary_probe.py`
ID: `phone-summary-01` (new run; stable ID recovers existing work on retries).

## Backing executor

1. Execute `python3 /home/codex/Documents/Codex/summary-probe/exo_voice_summary_probe.py start phone-summary-01` once.
2. Repeatedly execute `python3 /home/codex/Documents/Codex/summary-probe/exo_voice_summary_probe.py next phone-summary-01` in separate short tool calls. Keep this backing turn active until Hermes reaches terminal. No background polling/narration scripts.
3. For activity, relay full JSON unchanged as commentary; do NOT invent milestones or summarize it yourself. For waiting, stay silent and continue.
4. For final, return full JSON unchanged as the sole backing FINAL message. The output is a substantive synthetic decision brief, and presentation.mode is summarize_final. Voice should receive the FULL brief and summarize it itself, not an executor-written summary.
5. For already_delivered, stop without repeating the summary. On an explicit follow-up question, retrieve the report with `python3 /home/codex/Documents/Codex/summary-probe/exo_voice_summary_probe.py status phone-summary-01` if the report is no longer available in context; recover, don't restart the run.
6. On approval, surface the request and wait; do not auto-approve. On capacity block, stop the test and report the block, not a clipped brief. On user stop or 25 polls without completion, execute `stop phone-summary-01` against this script only. A capacity block on an already completed run needs no cancellation.

## Requested realtime behavior

Give brief natural intermediate updates if useful. When the complete brief arrives, drop older unspoken progress and deliver a 30-60-second executive summary. State that the scenario is synthetic. Explain the recommendation, decisive evidence, material caveat, and next action; do not merely announce completion or read JSON. Preserve consequential quantities/qualifiers when using them; do not invent certainty or present this as the owner's actual deployment. End after the summary and wait for questions.

## Operator acceptance (not a script for Voice to recite)

Compare actual generated brief, intact backing handoff, Voice transcript and user audio report. Look for internal-only pilot vs public release; quarantined vs lost records; improved median vs failing p95; limited low-load evidence; required release gate and ownership. All facts must be grounded in the delivered report. A follow-up about the quarantined records tests detail retrieval. No public release is actually authorized or performed.

The generated final targets 200-250 words with a harder 1600-ASCII-character cap to fit the existing 2800-byte envelope gate and approximately 1000-token native handoff budget with margin. These are conservative guards, not a proof of arbitrary report capacity. Oversized output blocks without consuming or truncating the final. Raw SSE bytes remain untouched and archived. A successful summary does not prove verbatim speech, audio playback acknowledgement, deterministic preemption, or large-document chunking.
