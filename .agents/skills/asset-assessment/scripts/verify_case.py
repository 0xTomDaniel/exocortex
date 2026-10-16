#!/usr/bin/env python3
"""Verify bank, runtime, case-spec, checklist, and finalized assessment hashes."""
from __future__ import annotations
import argparse,csv,json,sys
from datetime import datetime,timezone
from pathlib import Path
from banklib import assessment_hash_for_rows,case_spec_hash,checklist_hash_for_rows,file_hash,load_json,load_manifest,row_bool

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--case-spec',type=Path,required=True);ap.add_argument('--checklist',type=Path,required=True);ap.add_argument('--record',type=Path);args=ap.parse_args();checks=[]
 try:
  m=load_manifest();spec=load_json(args.case_spec)
  with args.checklist.open(newline='',encoding='utf-8-sig') as f:rows=[{k:(v or '').strip() for k,v in r.items()} for r in csv.DictReader(f)]
  sh=case_spec_hash(spec);ch=checklist_hash_for_rows(rows,m['bank_hash'],sh)
  checks += [{'check':'bank_hash','valid':all(r['bank_hash']==m['bank_hash'] for r in rows)},{'check':'runtime_hash','valid':all(r.get('runtime_version')==m['runtime_version'] and r.get('runtime_hash')==m['runtime_hash'] for r in rows)},{'check':'case_spec_hash','valid':all(r['case_spec_hash']==sh for r in rows)},{'check':'checklist_hash','valid':all(r['checklist_hash']==ch for r in rows)}]
  result={'bank_hash':m['bank_hash'],'runtime_hash':m['runtime_hash'],'case_spec_hash':sh,'checklist_hash':ch}
  if args.record:
   rec=load_json(args.record);ah=assessment_hash_for_rows(rows,sh,ch,finalized_at=rec['finalized_at'],evaluator=rec['evaluator'],model_id=rec['model_id'],record_role=rec['record_role'],supersedes_assessment_hash=rec.get('supersedes_assessment_hash',''),review_config_hash=rec.get('review_config_hash',''))
   cutoff=datetime.fromisoformat(spec['evidence_cutoff'].replace('Z','+00:00')).astimezone(timezone.utc);observed=[]
   for r in rows:
    if row_bool(r.get('evidence_sufficient',''),allow_blank=True) is True:observed.append(datetime.fromisoformat(r['observed_at'].replace('Z','+00:00')).astimezone(timezone.utc))
   mode='prospective' if all(x<=cutoff for x in observed) else 'retrospective'
   checks += [{'check':'assessment_hash','valid':rec.get('assessment_hash')==ah},{'check':'temporal_mode','valid':rec.get('temporal_mode')==mode},{'check':'checklist_file_sha256','valid':rec.get('checklist_file_sha256')==file_hash(args.checklist)},{'check':'case_spec_file_sha256','valid':rec.get('case_spec_file_sha256')==file_hash(args.case_spec)}];result['assessment_hash']=ah
  result.update(valid=all(x['valid'] for x in checks),checks=checks);print(json.dumps(result,indent=2));return 0 if result['valid'] else 1
 except (OSError,ValueError,json.JSONDecodeError,KeyError) as e:print(f'error: {e}',file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
