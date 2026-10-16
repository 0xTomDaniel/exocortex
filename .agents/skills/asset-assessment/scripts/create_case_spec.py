#!/usr/bin/env python3
"""Create a draft frozen-input case specification for asset-assessment v2."""
from __future__ import annotations
import argparse,json,sys
from datetime import datetime,timezone
from pathlib import Path
from banklib import legal_assemblies,load_manifest

def candidate(text):
 left,*parts=text.split('|')
 if len(parts)!=3:raise ValueError('candidate must be ID[=NAME]|CLASS|SUBTYPE|EXPOSURE')
 aid,sep,name=left.partition('=')
 return {'asset':aid,'asset_name':name if sep else aid,'asset_class':parts[0],'subtype':parts[1],'exposure_type':parts[2]}
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--case-id',required=True);ap.add_argument('--decision',required=True);ap.add_argument('--purpose',choices=['screen','diligence','action'],required=True);ap.add_argument('--tier',choices=['core','full'],default='core');ap.add_argument('--candidate',action='append',required=True,metavar='ID[=NAME]|CLASS|SUBTYPE|EXPOSURE');ap.add_argument('--horizon',required=True);ap.add_argument('--planned-horizon-end',required=True);ap.add_argument('--evidence-cutoff',required=True,help='ISO timestamp with timezone');ap.add_argument('--case-spec-author',required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
 try:
  m=load_manifest();universe=[candidate(x) for x in args.candidate];legal=legal_assemblies(m)
  for x in universe:
   if (x['asset_class'],x['subtype'],x['exposure_type']) not in legal:raise ValueError(f"unsupported assembly {(x['asset_class'],x['subtype'],x['exposure_type'])}")
  cutoff=datetime.fromisoformat(args.evidence_cutoff.replace('Z','+00:00'))
  if cutoff.tzinfo is None:raise ValueError('evidence-cutoff must include a timezone')
  spec={'schema_version':'2.0.0','case_id':args.case_id,'decision':args.decision,'purpose':args.purpose,'tier':args.tier,'horizon':args.horizon,'planned_horizon_end':args.planned_horizon_end,'candidate_universe':universe,'reference_size':{'value':None,'unit':'USD'},'proposed_position':None,'evidence_cutoff':args.evidence_cutoff,'thresholds':{},'overrides':{},'extensions':[],'weights':{'dimensions_by_layer':{},'layer_weights':{}},'outcome_definition':'','constraints':[],'case_spec_author':args.case_spec_author,'created_at':datetime.now(timezone.utc).isoformat(),'bank_version':m['bank_version'],'bank_hash':m['bank_hash'],'runtime_version':m['runtime_version'],'runtime_hash':m['runtime_hash']}
  args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(spec,indent=2)+'\n',encoding='utf-8');print(str(args.output));return 0
 except (OSError,ValueError,json.JSONDecodeError) as e:print(f'error: {e}',file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
