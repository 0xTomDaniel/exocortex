# Voice frontend acceptance — specified, not executed

Run only against an explicitly authorized isolated Voice deployment with synthetic
owner notes and the candidate HOST-AGENTS.md/REALTIME-PROMPT.md actually installed.
Record deployed source hashes, client/server versions, scenario date/timezone and
fresh session identifiers privately. Use the same Mixed/Open fixture meanings and
ordinary spoken prompts from the integration catalog. Do not read grading criteria
into Voice or seed them into the backing thread.

| Case | Frontend observation and backing evidence |
| --- | --- |
| Fresh Voice greeting with paused week | Greeting reaches backing agent before substantive context claims; spoken reply offers verified next step and permits redirection. Inspect actual backing turn and note reads. |
| Text-first Astra/low, then Voice in same thread | Inspect actual backing rollout context for every Voice turn; preserve Astra/low and existing continuity. Selector/server default alone is insufficient evidence. |
| Fresh phone-originated Voice thread | Observe actual backing model and effort independently. A phone override/fallback fails Astra/low acceptance even if the conversation sounds correct. |
| Tangent and explicit commitment, then end call | Spoken commitment reaches backing agent, saves once, preserves paused scope. End-of-call acknowledgement does not imply workflow completion. Inspect saved notes and tail-turn ordering. |
| Return in fresh thread/call | Recover saved scope/next step and commitment without earlier transcript. Do not imply the agent performed background work. |
| No active workflow, hypothetical reflection | Useful natural conversation with no automatic checklist/task; spoken output should not expose unnecessary implementation narration. |
| One-week confirmation and sprint deferral | Voice forwards exact scope/correction; backing records only that agreement, preserves enclosing work and dated re-entry. Spoken completion matches saved scope. |
| Explicit cancellation, then reflection | Cancellation persists; separate obligations remain. Subsequent speech does not restart the cancelled workflow. |

Capture audio/transcript and backing-event correspondence with timestamps, saved
artifacts and actual model contexts. Grade frontend routing/presentation separately
from backing behavior; report missing audio, events or client visibility as
unverified. Check both previous and candidate prompt sets with repeated runs and
wording variations before claiming improvement. Local `codex exec` results cannot
fill any of these frontend cells. Production rollout and phone tests require their
own authorization and environment; this protocol changes neither.
