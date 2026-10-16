# Isolated terminal-priority and verbatim-final test

Explicitly requested experiment; production unchanged. Use the existing permission-repaired Voice thread. This trial retains the continuously active backing turn, but carries terminal presentation instructions all the way to realtime instead of stripping the final envelope to a bare sentence.

Script: `/home/codex/Documents/Codex/native-batch-probe/terminal-probe.py`
New ID: `phone-final-01`. Do not reuse another test's ID/cursor or follow the old one-batch-then-final protocol.

## Backing executor

1. Call `python3 /home/codex/Documents/Codex/native-batch-probe/terminal-probe.py start phone-final-01` once.
2. Repeatedly call `python3 /home/codex/Documents/Codex/native-batch-probe/terminal-probe.py next phone-final-01` using separate short tool invocations. Do not generate background loops, timers or narration.
3. For `activity`, relay the complete JSON UNCHANGED in commentary and continue. It contains exact event payloads plus separately labeled presentation metadata. Do not summarize, infer phases, or add 'still running' commentary yourself.
4. For `waiting`, stay silent and continue.
5. For `final`, stop polling and return the complete JSON UNCHANGED as your sole FINAL message. **Do not strip the presentation metadata or extract output in the backing executor for this test.** Realtime must receive both the final text and the instruction that it supersedes older activity.
6. For `already_delivered`, stop without repeating the final. Explicit user requests for a lost answer may use `status phone-final-01`.
7. For `approval`, surface the exact request and wait; no bypass. For capacity-blocked or after 25 next calls without completion, call `stop phone-final-01` on this script only and report the test as blocked/incomplete. User stop requests cancel only this probe immediately.

## Realtime presentation contract being tested

The user's request must explicitly ask for this contract; a document read only by the backing executor is not proof Voice received it.

- Summarize activity semantically in the past tense: e.g. a recorded tool finished or another tool was started. Do not upgrade an earlier snapshot into a claim that a phase is STILL underway now. Do not read JSON or timestamps aloud.
- A terminal envelope supersedes every earlier activity batch for the same run. Discard any earlier progress you have not spoken; do not finish a stale progress recap as a preface to the final.
- For `status: completed` and `presentation.mode: verbatim_final`, speak exactly the JSON `output` value ONCE. No 'and now', 'the test has', acknowledgement, paraphrase, suffix, or explanation. Treat the presentation object as delivery control, not content to summarize. Then stop.
- For failed/cancelled/interrupted status, report that status truthfully; do not claim successful completion.

For this fixture the exact final must be: Native batch probe complete.

## Honest acceptance gate

The added metadata contains no scripted semantic summary and does not mutate raw.sse. It is a model-facing instruction, NOT an enforced speech scheduler, audio buffer clear, or playback acknowledgement. Already-generated/playing audio may remain outside this interface's control.

Pass requires actual phone evidence of intermediate semantic updates, the exact final wording once, and no stale progress spoken after terminal information reaches Voice. Compare terminal status, tool result, backing final, realtime transcript and the owner's audio observations. If Voice paraphrases again or stale audio survives, mark those gates failed rather than adding repeated prompts and claiming deterministic guarantees. No production promotion until reviewed.
