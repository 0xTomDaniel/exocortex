#!/usr/bin/env python3
"""Synthetic multi-section deliverable; shared raw capture, separate test state.

No realtime prompt override. This selects semantic final presentation instead
of the earlier verbatim gate; it doesn't relax that separate acceptance lane.
"""
import exo_native_batch_probe as probe

PROMPT = '''This is an isolated Voice-summary experiment with SYNTHETIC data, not a real deployment assessment. Do not inspect files, memory, credentials, remote hosts, other agents, or real customer data. Do not delegate or change any files. Run the following three harmless terminal commands as separate tool calls, waiting for each to complete:
1. sleep 8; printf 'SYNTHETIC integrity fixture: 120 records submitted; 114 imported; 6 quarantined safely for missing account IDs; zero records lost.\\n'
2. sleep 8; printf 'SYNTHETIC performance fixture: median latency 1.2 seconds versus baseline 2.0; p95 latency 4.8 seconds versus target 3.0. Measurement covers one low-load hour only; peak load is untested.\\n'
3. sleep 8; printf 'SYNTHETIC release fixture: an internal pilot is reversible; public release requires resolving quarantine and a 1000-record peak-profile test that meets the p95 target. Test lead owns these checks; no real person or deadline assigned.\\n'

Then synthesize a useful executive decision brief, not a completion sentence. Use four short sections: Findings; Recommendation and rationale; Risk and uncertainty; Next action and owner. Recommend an internal-only pilot, NOT public release. Distinguish quarantined records from lost records. Preserve the median-versus-p95 distinction and the limited evidence window. Name the public-release gate and owner; do not invent evidence, dates or confidence scores. Label the brief Synthetic test. Target 200-250 words but HARD LIMIT 1600 ASCII characters for the entire final brief, including headings and whitespace; shorten if needed. Return only the brief, with no reasoning or preface. This report will be summarized by Voice, not read verbatim.'''


def main():
    probe.PROMPT = PROMPT
    probe.FINAL_PRESENTATION_MODE = 'summarize_final'
    probe.main()


if __name__ == '__main__':
    main()
