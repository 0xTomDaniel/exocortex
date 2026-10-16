#!/usr/bin/env python3
"""Resolve constructs, staged gates, layered scores, and authorization for bank v2."""
from __future__ import annotations
import argparse,csv,json,math,sys
from collections import defaultdict
from pathlib import Path
from typing import Any
from banklib import REFS,load_manifest,load_json,row_bool

REQUIRED={"case_id","bank_version","bank_hash","runtime_version","runtime_hash","case_spec_hash","checklist_hash","purpose","asset","asset_class","origin","question_id","construct_id","parent_question_id","relation_to_parent","specificity_rank","factor","dimension","layer","question","manifest_suppressed","applicable","applicability_reason","applicability_source","evidence_sufficient","verdict","gate","gate_stage","scored","gate_override_reason","scored_override_reason","adjudication","adjudication_reason"}

def pct(x):return None if x is None else round(100*x,2)
def read_rows(path):
    with path.open(newline='',encoding='utf-8-sig') as f:
        rd=csv.DictReader(f);missing=REQUIRED-set(rd.fieldnames or [])
        if missing:raise ValueError(f"missing columns: {sorted(missing)}")
        out=[];seen=set()
        for n,r in enumerate(rd,2):
            r={k:(v or '').strip() for k,v in r.items()}; key=(r['asset'],r['question_id'])
            if key in seen:raise ValueError(f"row {n}: duplicate asset/question {key}")
            seen.add(key)
            for f in ('case_id','asset','question_id','construct_id','dimension','layer'):
                if not r[f]:raise ValueError(f"row {n}: {f} required")
            try:
                r['_app']=row_bool(r['applicable']);r['_evid']=row_bool(r['evidence_sufficient'],allow_blank=True);r['_verdict']=row_bool(r['verdict'],allow_blank=True);r['_gate']=bool(row_bool(r['gate']));r['_scored']=bool(row_bool(r['scored']));r['_suppressed']=bool(row_bool(r['manifest_suppressed']));r['_rank']=int(r['specificity_rank'])
            except ValueError as e:raise ValueError(f"row {n}: {e}")
            if r['_suppressed'] and (r['_app'] or r['applicability_source']!='manifest'):raise ValueError(f"row {n}: manifest-suppressed row must remain manifest N/A")
            if not r['_suppressed'] and r['applicability_source']=='manifest':raise ValueError(f"row {n}: manifest source is invalid for an unsuppressed row")
            if not r['_app']:
                if not r['applicability_reason'] or r['applicability_source'] not in {'bank','manifest','evaluator'}:raise ValueError(f"row {n}: N/A requires applicability_reason and valid source")
                if r['_evid'] is True or r['_verdict'] is not None:raise ValueError(f"row {n}: N/A cannot have evidence/verdict")
            else:
                if r['_evid'] is True and r['_verdict'] is None:raise ValueError(f"row {n}: verdict required when evidence is YES")
                if r['_evid'] is not True and r['_verdict'] is not None:raise ValueError(f"row {n}: verdict requires evidence YES")
            if r['_gate'] and r['_scored']:raise ValueError(f"row {n}: gate rows must be unscored")
            if r['_gate'] and not r['gate_stage']:raise ValueError(f"row {n}: gate_stage required")
            if r['_gate'] and r['gate_stage']=='identity' and not r['_app'] and r['applicability_source']!='manifest':raise ValueError(f"row {n}: identity gates may be N/A only by manifest rule")
            if not r['_gate'] and r['gate_stage']:raise ValueError(f"row {n}: non-gate cannot have gate_stage")
            if r['adjudication'] not in {'','primary_upheld','supporting_upheld'}:raise ValueError(f"row {n}: invalid adjudication")
            if r['adjudication'] and not r['adjudication_reason']:raise ValueError(f"row {n}: adjudication reason required")
            out.append(r)
    if not out:raise ValueError('empty checklist')
    return out

def weight_config(spec,manifest):
    raw=spec.get('weights') or {}; dims=raw.get('dimensions_by_layer',{}) if isinstance(raw,dict) else {}; layer_weights=raw.get('layer_weights',{}) if isinstance(raw,dict) else {}
    for layer,mapping in dims.items():
        if layer not in set(manifest['dimension_layer_map'].values()) or not isinstance(mapping,dict):raise ValueError(f"invalid layer weights {layer}")
        for dim,val in mapping.items():
            if manifest['dimension_layer_map'].get(dim)!=layer or isinstance(val,bool) or not isinstance(val,(int,float)) or not math.isfinite(val) or val<=0:raise ValueError(f"invalid weight {layer}/{dim}")
    for layer,val in layer_weights.items():
        if layer not in dims or isinstance(val,bool) or not isinstance(val,(int,float)) or val<=0:raise ValueError(f"invalid layer weight {layer}")
    return dims,layer_weights

def resolve(rows):
    applicable=[r for r in rows if r['_app']]
    if not applicable:return {'state':'NA','effective_primary':None,'resolved_by':'none','support_coverage_pct':None,'row':None}
    top=max(r['_rank'] for r in applicable); primary=[r for r in applicable if r['_rank']==top]
    if len(primary)!=1:raise ValueError(f"construct {rows[0]['construct_id']} has {len(primary)} effective primaries")
    p=primary[0]; parents=[r for r in applicable if r is not p]
    parent_no=any(r['_evid'] is True and r['_verdict'] is False for r in parents)
    if p['_evid'] is True and p['_verdict'] is False:state,res='NO','primary'
    elif p['_evid'] is True and p['_verdict'] is True:
        if parent_no:
            if p['adjudication']=='primary_upheld':state,res='YES','adjudication'
            elif p['adjudication']=='supporting_upheld':state,res='NO','adjudication'
            else:state,res='CONFLICT','contradiction'
        else:state,res='YES','primary'
    elif parent_no:state,res='NO','parent_entailment'
    else:state,res='UNKNOWN','insufficient_evidence'
    answered=sum(r['_evid'] is True for r in parents)
    return {'state':state,'effective_primary':p['question_id'],'resolved_by':res,'support_coverage_pct':pct(answered/len(parents)) if parents else None,'row':p}

def dimension_stat(items):
    applicable=[x for x in items if x['state']!='NA'];yes=sum(x['state']=='YES' for x in applicable);no=sum(x['state']=='NO' for x in applicable);conf=sum(x['state']=='CONFLICT' for x in applicable);unknown=sum(x['state']=='UNKNOWN' for x in applicable);answered=yes+no
    return {'applicable':len(applicable),'yes':yes,'no':no,'unknown':unknown,'conflict':conf,'pass_rate_pct':pct(yes/answered) if answered else None,'evidence_coverage_pct':pct(answered/len(applicable)) if applicable else None,'conservative_evidence_adjusted_pct':pct(yes/len(applicable)) if applicable else None}

def stage_states(asset_rows,manifest,evidence_state):
    result={}
    for stage in manifest['gate_stages']:
        if stage=='evidence':result[stage]=evidence_state;continue
        all_gates=[r for r in asset_rows if r['_gate'] and r['gate_stage']==stage]
        if not all_gates:result[stage]='NOT_APPLICABLE';continue
        gates=[r for r in all_gates if r['_app']]
        if any(not r['_app'] and r['applicability_source']=='evaluator' for r in all_gates):result[stage]='UNRESOLVED'
        elif not gates:result[stage]='N/A'
        elif any(r['_evid'] is True and r['_verdict'] is False for r in gates):result[stage]='FAILED'
        elif any(r['_evid'] is not True for r in gates):result[stage]='UNRESOLVED'
        else:result[stage]='PASSED'
    return result

def evidence_for(purpose,dimstats,manifest):
    cfg=manifest['purposes'][purpose]
    if cfg['min_coverage'] is None:return 'N/A'
    relevant=[s for d,s in dimstats.items() if manifest['dimension_layer_map'][d] in {'merit','entry','integrity'} and s['applicable']]
    total=sum(s['applicable'] for s in relevant);answered=sum(s['yes']+s['no'] for s in relevant);conf=sum(s['conflict'] for s in relevant)
    coverage=answered/total if total else 0
    floors=[(s['yes']+s['no'])/s['applicable'] for s in relevant]
    return 'PASSED' if coverage>=cfg['min_coverage'] and all(x>=cfg['per_dimension_floor'] for x in floors) and conf<=cfg['max_conflicts'] else 'UNRESOLVED'

def purpose_status(purpose,stages,manifest):
    values=[stages[s] for s in manifest['purposes'][purpose]['enforced_stages']]
    if 'FAILED' in values:return 'FAILED'
    if 'UNRESOLVED' in values or 'N/A' in values:return 'UNRESOLVED'
    return 'PASSED'

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('input_csv',type=Path);ap.add_argument('--case-spec',type=Path,required=True);ap.add_argument('--manifest',type=Path,default=REFS/'bank-manifest.json');ap.add_argument('--rank-by',choices=['merit','entry','integrity','implementation','fit','composite']);ap.add_argument('--output',type=Path);ap.add_argument('--summary-csv',type=Path);args=ap.parse_args()
    try:
        manifest=load_manifest(args.manifest);spec=load_json(args.case_spec);rows=read_rows(args.input_csv);dims_weights,layer_weights=weight_config(spec,manifest)
        constants={f:{r[f] for r in rows} for f in ('case_id','bank_version','bank_hash','runtime_version','runtime_hash','case_spec_hash','checklist_hash','purpose')}
        bad={f:v for f,v in constants.items() if len(v)!=1}
        if bad:raise ValueError(f"inconsistent case fields: {bad}")
        if next(iter(constants['bank_hash']))!=manifest['bank_hash']:raise ValueError('checklist bank_hash mismatch')
        if next(iter(constants['runtime_version']))!=manifest['runtime_version'] or next(iter(constants['runtime_hash']))!=manifest['runtime_hash']:raise ValueError('checklist runtime version/hash mismatch')
        from banklib import case_spec_hash,checklist_hash_for_rows
        spec_hash=case_spec_hash(spec)
        if next(iter(constants['case_spec_hash']))!=spec_hash:raise ValueError('case_spec_hash mismatch')
        expected_checklist=checklist_hash_for_rows(rows,manifest['bank_hash'],spec_hash)
        if next(iter(constants['checklist_hash']))!=expected_checklist:raise ValueError('checklist_hash mismatch; gate/scoring/question configuration changed after build')
        by_asset=defaultdict(list)
        for r in rows:by_asset[r['asset']].append(r)
        assets=[]
        for asset,arows in sorted(by_asset.items()):
            groups=defaultdict(list)
            for r in arows:groups[r['construct_id']].append(r)
            constructs=[]
            for cid,members in groups.items():
                x=resolve(members);x['construct_id']=cid
                if x['row'] is not None:
                    x['dimension']=x['row']['dimension'];x['layer']=x['row']['layer'];x['scored']=x['row']['_scored'];x['gate']=x['row']['_gate']
                else:x.update({'dimension':members[0]['dimension'],'layer':members[0]['layer'],'scored':False,'gate':False})
                constructs.append(x)
            dimitems=defaultdict(list)
            for x in constructs:
                if x['scored'] and not x['gate']:dimitems[x['dimension']].append(x)
            dimstats={d:dimension_stat(v) for d,v in sorted(dimitems.items())}
            layerstats={}
            for layer in sorted(set(manifest['dimension_layer_map'].values())):
                ds={d:s for d,s in dimstats.items() if manifest['dimension_layer_map'][d]==layer}
                entry={'dimensions':ds,'weighted':None}
                weights=dims_weights.get(layer,{})
                if len(ds)==1 and not weights:weights={next(iter(ds)):1}
                if ds and weights:
                    missing=set(ds)-set(weights)
                    if missing:raise ValueError(f"weights for {layer} missing {sorted(missing)}")
                    active=[(d,s,weights[d]) for d,s in ds.items() if s['applicable']]
                    denom=sum(w for _,_,w in active)
                    if denom:
                        def avg(field):return sum(w*(s[field]/100) for _,s,w in active if s[field] is not None)/sum(w for _,s,w in active if s[field] is not None) if any(s[field] is not None for _,s,w in active) else None
                        raw_pass=avg('pass_rate_pct');raw_coverage=avg('evidence_coverage_pct');raw_conservative=avg('conservative_evidence_adjusted_pct')
                        entry['weighted']={'pass_rate_pct':pct(raw_pass),'evidence_coverage_pct':pct(raw_coverage),'conservative_evidence_adjusted_pct':pct(raw_conservative),'decision_value':raw_conservative,'counts':{k:sum(s[k] for s in ds.values()) for k in ('applicable','yes','no','unknown','conflict')},'weights':weights}
                layerstats[layer]=entry
            composite=None
            if layer_weights:
                chosen=[]
                for layer,weight in layer_weights.items():
                    weighted=layerstats.get(layer,{}).get('weighted')
                    if not weighted:raise ValueError(f"composite layer {layer} lacks a weighted result")
                    chosen.append((weighted,weight))
                composite={}
                for field in ('pass_rate_pct','evidence_coverage_pct','conservative_evidence_adjusted_pct'):
                    available=[(result[field],weight) for result,weight in chosen if result[field] is not None]
                    composite[field]=pct(sum(weight*(value/100) for value,weight in available)/sum(weight for _,weight in available)) if available else None
                available=[(result.get('decision_value'),weight) for result,weight in chosen if result.get('decision_value') is not None]
                composite['decision_value']=sum(weight*value for value,weight in available)/sum(weight for _,weight in available) if available else None
                composite['layer_weights']=layer_weights
            evidence={p:evidence_for(p,dimstats,manifest) for p in manifest['purposes']}
            stages_by_purpose={p:stage_states(arows,manifest,evidence[p]) for p in manifest['purposes']}
            statuses={p:purpose_status(p,stages_by_purpose[p],manifest) for p in manifest['purposes']}
            authorization='none'
            purpose_order=('screen','diligence','action')
            for p in purpose_order[:purpose_order.index(spec['purpose'])+1]:
                if statuses[p]=='PASSED':authorization=p
            failed=[r['question_id'] for r in arows if r['_gate'] and r['_app'] and r['_evid'] is True and r['_verdict'] is False]
            unresolved=[r['question_id'] for r in arows if r['_gate'] and r['_app'] and r['_evid'] is not True]
            identity_state=stages_by_purpose[spec['purpose']]['identity'];integrity_state=stages_by_purpose[spec['purpose']]['integrity']
            labels=[]
            if identity_state!='PASSED':labels.append('identity_unresolved_scoring_blocked')
            if integrity_state=='FAILED':labels.append('avoid_failed_integrity')
            elif integrity_state in {'UNRESOLVED','N/A'}:labels.append('unresolved_integrity')
            assets.append({'asset':asset,'purpose_status':statuses[spec['purpose']],'authorization_ceiling':authorization,'stage_states':stages_by_purpose[spec['purpose']],'labels':labels,'failed_gates':failed,'unresolved_gates':unresolved,'dimensions':dimstats if identity_state=='PASSED' else {},'layers':layerstats if identity_state=='PASSED' else {},'composite':composite if identity_state=='PASSED' else None,'constructs':[{k:v for k,v in x.items() if k!='row'} for x in sorted(constructs,key=lambda x:x['construct_id'])]})
        if args.rank_by:
            for a in assets:
                if 'identity_unresolved_scoring_blocked' in a['labels']:continue
                w=a['composite'] if args.rank_by=='composite' else a['layers'].get(args.rank_by,{}).get('weighted')
                if not w:raise ValueError(f"--rank-by {args.rank_by} requires predeclared weights and applicable dimensions")
            order={'PASSED':0,'NOT_APPLICABLE':0,'UNRESOLVED':1,'N/A':2,'FAILED':3}
            def sort_key(a):
                identity=order[a['stage_states']['identity']]; integrity=0 if a['stage_states']['integrity']=='PASSED' else 1 if a['stage_states']['integrity'] in {'UNRESOLVED','N/A'} else 2
                w=a['composite'] if args.rank_by=='composite' else a['layers'].get(args.rank_by,{}).get('weighted')
                value=w.get('decision_value') if w else None
                return (identity,integrity,order[a['purpose_status']],-(value if value is not None else -1),a['asset'])
            assets.sort(key=sort_key)
            previous=None;shared_rank=0
            for position,a in enumerate(assets,1):
                if 'identity_unresolved_scoring_blocked' in a['labels']:a['rank']=None;continue
                w=a['composite'] if args.rank_by=='composite' else a['layers'][args.rank_by]['weighted'];key=sort_key(a)[:-1]
                if key!=previous:shared_rank=position;previous=key
                a['rank']=shared_rank
        result={'meta':{'bank_version':manifest['bank_version'],'bank_hash':manifest['bank_hash'],'case_id':spec['case_id'],'purpose':spec['purpose'],'rank_by':args.rank_by,'warning':'Mechanical layer statistics are not trade authorization. Unknown and conflict receive zero pending credit only in the conservative statistic.'},'assets':assets}
        rendered=json.dumps(result,indent=2)
        if args.output:args.output.write_text(rendered+'\n',encoding='utf-8')
        else:print(rendered)
        if args.summary_csv:
            fields=['rank','asset','purpose_status','authorization_ceiling','labels','rank_layer_pass_rate_pct','rank_layer_evidence_coverage_pct','rank_layer_conservative_pct','applicable','yes','no','unknown','conflict','failed_gates','unresolved_gates']
            with args.summary_csv.open('w',newline='',encoding='utf-8') as f:
                w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
                for a in assets:
                    metric=(a['composite'] if args.rank_by=='composite' else a['layers'].get(args.rank_by or '',{}).get('weighted')) if args.rank_by else None;metric=metric or {};counts=metric.get('counts',{})
                    w.writerow({'rank':a.get('rank',''),'asset':a['asset'],'purpose_status':a['purpose_status'],'authorization_ceiling':a['authorization_ceiling'],'labels':';'.join(a['labels']),'rank_layer_pass_rate_pct':metric.get('pass_rate_pct',''),'rank_layer_evidence_coverage_pct':metric.get('evidence_coverage_pct',''),'rank_layer_conservative_pct':metric.get('conservative_evidence_adjusted_pct',''),'applicable':counts.get('applicable',''),'yes':counts.get('yes',''),'no':counts.get('no',''),'unknown':counts.get('unknown',''),'conflict':counts.get('conflict',''),'failed_gates':';'.join(a['failed_gates']),'unresolved_gates':';'.join(a['unresolved_gates'])})
        return 0
    except (OSError,ValueError,json.JSONDecodeError,ZeroDivisionError) as e:print(f"error: {e}",file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
