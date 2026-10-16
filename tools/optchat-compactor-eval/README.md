# OptChat compactor comparison — 2026-10-15 (America/Denver evening)

Tom asked to compare compressor quality of Haiku 5.5 (high, xhigh) against the current Sonnet 5.5 (medium).

**Run:** from a pi-optchat checkout, `OPTCHAT_DIR=<checkout> OPTCHAT_PROFILE=<optchat profile dir> npx tsx <this dir>/eval.mts <outDir> --leaves=40 --merges=27 --configs=all` (outputs contain memory excerpts: keep them out of git).

**Method:** `eval.mts` copies an OptChat profile's memory to a temp dir (the real profile is never opened for writing), samples real native-history compaction tasks, and runs each through upstream OptChat's own `createCompressor` (same prompts, 512-byte rule, 640-byte tolerance, retries) via Pi 1.1.0's model registry and the existing CLIProxy route. Opus 5.5 (high) grades blind: per task it sees the source and the three lines in random order and reports factual errors, coverage (1–5), usefulness (1–5) and a rank. Runs: `run-40` (40 single-message compressions, seed 7; the merge sampler had a key bug, so it held no merges) and `run-merges` (27 merges across tree levels 1–9, seed 7). `dry-run` was the 3-task harness check.

| 67 tasks (40 leaves + 27 merges) | Sonnet 5.5 medium (current) | Haiku 5.5 high | Haiku 5.5 xhigh |
|---|---|---|---|
| Mean rank (1 best) | 2.12 | 1.94 | 1.94 |
| First place | 19 | 24 | 24 |
| Coverage / usefulness (1–5) | 3.69 / 3.64 | 3.88 / 3.72 | 3.80 / 3.64 |
| Judge-flagged errors (summaries with any) | 52 (23) | 59 (32) | 63 (33) |
| Leaves: rank / coverage | 2.10 / 3.73 | 2.15 / 3.75 | **1.75 / 3.95** |
| Merges: rank / coverage / flagged errors | 2.15 / 3.63 / 6 | **1.63 / 4.07** / 12 | 2.22 / 3.56 / 20 |
| Within 512 bytes | 50/67 | 61/67 | 66/66 |
| Failures | 0 | 0 | 1 (merge) |
| Median latency leaf / merge | 3.2 s / 3.9 s | 11 s / 30 s | 21 s / 119 s |
| Catalog cost per summary leaf / merge | $0.019 / $0.014 | $0.002 / $0.005 | $0.004 / $0.015 |

Grading cost $2.48; compaction $1.90 (catalog estimates, subscription route, not billing).

**Read:** quality is close. Haiku high ties or slightly beats Sonnet on rank and coverage (clearest on merges), with somewhat more flagged errors on merges; Haiku xhigh helps single messages but is worse and very slow on merges and had a failure. Haiku is several times cheaper but 3–8× slower, which matters when a turn waits for summaries.

**Limits:** one judge, one sample per configuration, 67 tasks; differences are small relative to noise. The judge sees only the source (for merges, the two lines), while compactors may correctly pull details from the surrounding view, so some merge "errors" may be false positives; flagged errors are high for every model, so read them comparatively. Not a human evaluation.

**Bigger lever found:** main's OptChat 0.7.0 lacks upstream #97 (compactions get their own view, a quarter of the budget). Clone usage: on 0.7.0, median compactor prompt 61,469 tokens, 29% cache hit, $0.097/call; on upstream 0.8.5, 9,954 tokens, 60% hit, $0.012/call (catalog).

## Seven-way run (`run-7way`, same 67 tasks and seed) — 2026-10-16

Added Haiku 5.5 medium and GPT-6 Luna medium/high/xhigh (Tom asked for "gpt-6.1-luna": no such model exists; OpenAI's current Luna is GPT-6 Luna, `openai-codex/gpt-6-luna` via the ChatGPT subscription route). One Opus 5.5 judge ranked all seven blind per task (rank 1–7). Four failures were CLIProxy connection resets under 14-way parallel load, not model failures; a failure is graded as "no summary" and drags that config's rank.

| | Sonnet med | Haiku med | Haiku high | Haiku xhigh | Luna med | Luna high | Luna xhigh |
|---|---|---|---|---|---|---|---|
| Mean rank (1–7) | 4.04 | 3.73 | 3.88 | **3.10** | 4.99 | 4.43 | 3.82 |
| Beats Sonnet on | — | 35/67 | 36/67 | **48/67** | 24/67 | 29/67 | 32/67 |
| Coverage leaf / merge | 3.83 / 3.30 | 3.77 / 3.74 | 3.83 / 3.63 | **4.30** / 3.74 | 2.80 / 3.48 | 3.10 / 3.70 | 3.40 / **4.00** |
| Flagged errors | 40 | 59 | 50 | 43 | 40 | **33** | 38 |
| Median latency leaf / merge | 4.4 / 5.4 s | 8.4 / 18 s | 11 / 34 s | 22 / 150 s | 3.4 / 4.7 s | 4.7 / 5.6 s | 7.0 / 21 s |
| Cost per summary (catalog) | $0.017 | $0.002 | $0.003 | $0.010 | $0.0005 | $0.0006 | $0.0014 |

Read: Haiku xhigh is the strongest on quality (as in run 1 for leaves; run 1's weak merges did not repeat, so treat merge differences as noisy). Haiku medium ≈ high ≈ Sonnet. Luna medium/high write noticeably thinner single-message summaries; Luna xhigh is competitive, best on merges, cheapest by far, and on a separate (OpenAI) quota pool. Grading $4.03 plus compaction (catalog estimates).

## When does a turn wait? (OptChat source, upstream 0.8.5)

`context_with_system` on the first model call of a turn runs `memory.settle(signal)` (until `'turn'`): it waits until every line of the current view has a summary, or until all pending summaries have failed. Summaries start eagerly in the background as soon as messages are logged (up to 8 at once); messages of 512 bytes or less need none. So a turn waits only for summaries still unfinished when the next turn starts, typically the previous reply and its tool calls when the person answers quickly. Mid-turn refresh (30% of the context window) also waits. On failure OptChat already proceeds with "(not summarized yet: zoom it)" placeholders. Actual wait times are not logged; unmeasured.
