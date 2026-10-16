#!/usr/bin/env python3
"""Shared deterministic helpers for asset-assessment bank/runtime v2."""
from __future__ import annotations
import csv,hashlib,json,tomllib
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parent.parent
REFS=ROOT/'references'
MANIFEST_PATH=REFS/'bank-manifest.json'
REVIEW_CONFIG_PATH=ROOT/'assets'/'independent-review.toml'

def canonical_json(value:Any)->bytes:return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')
def sha256_bytes(value:bytes)->str:return hashlib.sha256(value).hexdigest()
def file_hash(path:Path)->str:return sha256_bytes(path.read_bytes())
def load_json(path:Path)->Any:return json.loads(path.read_text(encoding='utf-8'))
def load_csv(path:Path)->list[dict[str,str]]:
 with path.open(newline='',encoding='utf-8-sig') as f:return [{k:(v or '').strip() for k,v in r.items()} for r in csv.DictReader(f)]

def bank_hash_for_manifest(manifest:dict[str,Any])->str:
 excluded={'bank_hash','bank_commit','runtime_version','runtime_hash','runtime_files','audit_files','comparable_with','compatible_runtimes','superseded_runtimes'}
 return sha256_bytes(canonical_json({k:v for k,v in manifest.items() if k not in excluded}))

def load_manifest(path:Path=MANIFEST_PATH,verify:bool=True)->dict[str,Any]:
 m=load_json(path)
 if verify:
  roots={'files':path.parent,'audit_files':path.parent,'runtime_files':ROOT}
  for group,root in roots.items():
   for name,meta in m.get(group,{}).items():
    actual=file_hash(root/name)
    if actual!=meta.get('sha256'):raise ValueError(f"{group} hash mismatch for {name}: {actual} != {meta.get('sha256')}")
  rh=sha256_bytes(canonical_json(m.get('runtime_files',{})))
  if rh!=m.get('runtime_hash'):raise ValueError(f"runtime_hash mismatch: {rh} != {m.get('runtime_hash')}")
  bh=bank_hash_for_manifest(m)
  if bh!=m.get('bank_hash'):raise ValueError(f"bank_hash mismatch: {bh} != {m.get('bank_hash')}")
 return m

def load_review_config(path:Path=REVIEW_CONFIG_PATH)->dict[str,Any]:
 cfg=tomllib.loads(path.read_text(encoding='utf-8'))
 reviewers=cfg.get('default_reviewers',[]);ids=[r.get('model_id','') for r in reviewers]
 if cfg.get('minimum_distinct_models',0)<2:raise ValueError('independent-review config requires at least two distinct models')
 if len(ids)<2 or len(ids)!=len(set(ids)) or any(not x for x in ids):raise ValueError('default independent-review model IDs must be nonblank and distinct')
 for r in reviewers:
  if not all(r.get(k) for k in ('slot','model_id','display_name','provider','model','reasoning_level','agent_kind')):raise ValueError('incomplete default reviewer config')
 adjudicators=cfg.get('adjudication',{}).get('permitted_producer_ids',[])
 if not isinstance(adjudicators,list) or any(not isinstance(x,str) or not x.strip() or x in ids for x in adjudicators):raise ValueError('adjudication producer IDs must be distinct, non-empty strings')
 return cfg

def specificity_for_file(m:dict[str,Any],name:str)->int:
 if name=='question-bank-common.csv':return 0
 if name in {'question-bank-crypto.csv','question-bank-stocks.csv'}:return 1
 subtype={d.get('overlay_file') for cs in m.get('subtypes',{}).values() for d in cs.values()}
 exposure={d.get('overlay_file') for d in m.get('exposures',{}).values()}
 return 2 if name in subtype else 3 if name in exposure else 1

def bank_rows(m:dict[str,Any],refs:Path=REFS)->tuple[list[dict[str,str]],dict[str,int]]:
 rows=[];specificity={}
 for name in m.get('files',{}):
  rank=specificity_for_file(m,name)
  for r in load_csv(refs/name):r['_source']=name;r['_specificity']=str(rank);rows.append(r);specificity[r['question_id']]=rank
 return rows,specificity

def assembly_key(asset_class:str,subtype:str,exposure:str)->tuple[str,str,str]:return asset_class,subtype,exposure
def legal_assemblies(m:dict[str,Any])->set[tuple[str,str,str]]:return {assembly_key(a['class'],a['subtype'],a['exposure']) for a in m['assemblies']}
def selected_files(m:dict[str,Any],asset_class:str,subtype:str,exposure:str)->list[str]:
 out=['question-bank-common.csv','question-bank-crypto.csv' if asset_class=='crypto' else 'question-bank-stocks.csv'];sd=m['subtypes'][asset_class][subtype];ed=m['exposures'][exposure]
 if sd.get('overlay_file'):out.append(sd['overlay_file'])
 if ed.get('overlay_file'):out.append(ed['overlay_file'])
 return out
def suppression_map(m:dict[str,Any],asset_class:str,subtype:str,exposure:str)->dict[str,str]:
 out={}
 for d in (m['subtypes'][asset_class][subtype],m['exposures'][exposure]):
  for qid in d.get('suppress',[]):out[qid]=d.get('reason') or 'Suppressed by the selected canonical assembly.'
 return out

def case_spec_hash(spec:dict[str,Any])->str:return sha256_bytes(canonical_json(spec))

CHECKLIST_HASH_FIELDS=['case_id','bank_version','bank_hash','bank_commit','runtime_version','runtime_hash','case_spec_hash','purpose','bank_tier','asset','asset_name','asset_class','subtype','exposure_type','origin','question_id','construct_id','parent_question_id','relation_to_parent','construct_role','specificity_rank','factor','dimension','layer','question','manifest_suppressed','gate','gate_stage','scored','gate_override_reason','scored_override_reason']
ASSESSMENT_HASH_FIELDS=['asset','question_id','applicable','applicability_reason','applicability_source','evidence_sufficient','verdict','adjudication','adjudication_reason','explanation','source_ref','source_digest','data_as_of','evidence_available_at','observed_at','confidence','reviewer']
ASSESSMENT_META_FIELDS=['finalized_at','evaluator','model_id','record_role','supersedes_assessment_hash','review_config_hash']

def checklist_hash_for_rows(rows:list[dict[str,str]],bank_hash:str,spec_hash:str)->str:
 return sha256_bytes(canonical_json({'bank_hash':bank_hash,'case_spec_hash':spec_hash,'rows':[[r.get(f,'') for f in CHECKLIST_HASH_FIELDS] for r in rows]}))
def assessment_hash_for_rows(rows:list[dict[str,str]],spec_hash:str,checklist_hash:str,*,finalized_at:str,evaluator:str,model_id:str,record_role:str,supersedes_assessment_hash:str='',review_config_hash:str='')->str:
 meta={'finalized_at':finalized_at,'evaluator':evaluator,'model_id':model_id,'record_role':record_role,'supersedes_assessment_hash':supersedes_assessment_hash,'review_config_hash':review_config_hash}
 return sha256_bytes(canonical_json({'case_spec_hash':spec_hash,'checklist_hash':checklist_hash,'rows':[[r.get(f,'') for f in ASSESSMENT_HASH_FIELDS] for r in rows],'assessment_meta':meta}))
def row_bool(value:str,*,allow_blank:bool=False)->bool|None:
 x=(value or '').strip().lower()
 if x in {'yes','y','true','1'}:return True
 if x in {'no','n','false','0'}:return False
 if allow_blank and x in {'','unknown','na','n/a','null','none'}:return None
 raise ValueError(f"expected YES/NO{'/blank' if allow_blank else ''}; got {value!r}")
