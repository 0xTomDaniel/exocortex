#!/usr/bin/env python3
"""Fail unless finalized review sets satisfy the configured multi-model policy."""
from __future__ import annotations
import argparse,json,subprocess,sys,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--ledger',type=Path,required=True);ap.add_argument('--case-spec-hash');ap.add_argument('--review-config',type=Path);ap.add_argument('--require-all-purposes',action='store_true',help='Enforce review policy even for purposes not configured as required');args=ap.parse_args()
 with tempfile.TemporaryDirectory() as td:
  out=Path(td)/'analysis.json';cmd=[sys.executable,str(HERE/'analyze_question_history.py'),'--ledger',str(args.ledger),'--output',str(out)]
  if args.review_config:cmd+=['--review-config',str(args.review_config)]
  p=subprocess.run(cmd,text=True,capture_output=True)
  if p.returncode:print(p.stderr or p.stdout,file=sys.stderr);return p.returncode
  data=json.loads(out.read_text());sets=data['review_sets']
  if args.case_spec_hash:sets=[x for x in sets if x['case_spec_hash']==args.case_spec_hash]
  if not sets:print('error: no matching finalized review set',file=sys.stderr);return 2
  checked=sets if args.require_all_purposes else [x for x in sets if x['required']]
  failures=[x for x in checked if not x['policy_met']]
  print(json.dumps({'valid':not failures,'review_sets':sets,'checked_sets':checked,'failures':failures},indent=2))
  return 0 if not failures else 1
if __name__=='__main__':raise SystemExit(main())
