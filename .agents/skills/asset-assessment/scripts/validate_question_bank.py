#!/usr/bin/env python3
"""Validate asset-assessment bank v2, manifest, assemblies, and migration lineage."""
from __future__ import annotations
import argparse, csv, json, re, sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from banklib import REFS, bank_rows, legal_assemblies, load_manifest, load_review_config, selected_files, suppression_map

REQUIRED = {"question_id","asset_class","tier","factor","dimension","construct_id","parent_question_id","relation_to_parent","question","default_gate","gate_stage","default_scored","applicability","evidence_standard","failure_example","status","version_added","version_retired","supersedes"}
CLASSES={"common","crypto","stock"}; TIERS={"core","deep"}; STATUSES={"active","experimental","retired"}
RELATIONS={"","strict_refinement"}; BOOL={"YES","NO"}
PREFIXES=("COM-","CRY-","STK-","EXP-")

def tokens(text:str)->set[str]:
    stop={"the","a","an","is","are","does","do","can","and","or","of","to","for","with","under","this","that","its","be"}
    return {x for x in re.findall(r"[a-z0-9]+",text.lower()) if x not in stop}

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("--manifest",type=Path,default=REFS/"bank-manifest.json"); ap.add_argument("--json",dest="json_path",type=Path); args=ap.parse_args()
    errors=[]; warnings=[]
    try:
        manifest=load_manifest(args.manifest,verify=True);load_review_config();rows,specificity=bank_rows(manifest,args.manifest.parent)
    except (OSError,ValueError,json.JSONDecodeError) as e:
        print(f"error: {e}",file=sys.stderr); return 2
    ids=Counter(r.get("question_id","") for r in rows); by_id={r.get("question_id",""):r for r in rows}
    for qid,n in ids.items():
        if not qid: errors.append("blank question_id")
        if n>1: errors.append(f"duplicate question_id {qid}")
    factors=set(manifest.get("factors",[])); dimmap=manifest.get("dimension_layer_map",{}); stages=manifest.get("gate_stages",[])
    if {'bank_version':manifest.get('bank_version'),'bank_hash':manifest.get('bank_hash')} not in manifest.get('comparable_with',[]):errors.append('current bank tuple absent from comparable_with')
    if {'runtime_version':manifest.get('runtime_version'),'runtime_hash':manifest.get('runtime_hash')} not in manifest.get('compatible_runtimes',[]):errors.append('current runtime tuple absent from compatible_runtimes')
    exact={}; tokenized={}
    for r in rows:
        qid=r.get("question_id") or "<blank>"; label=f"{r.get('_source')}:{qid}"
        miss=REQUIRED-set(r)
        if miss: errors.append(f"{label}: missing columns {sorted(miss)}"); continue
        if r["asset_class"] not in CLASSES: errors.append(f"{label}: invalid asset_class")
        if not qid.startswith(PREFIXES): errors.append(f"{label}: invalid ID prefix")
        if r["tier"] not in TIERS: errors.append(f"{label}: invalid tier")
        if r["factor"] not in factors: errors.append(f"{label}: invalid factor {r['factor']}")
        if r["dimension"] not in dimmap: errors.append(f"{label}: invalid dimension {r['dimension']}")
        if r["status"] not in STATUSES: errors.append(f"{label}: invalid status")
        for f in ("default_gate","default_scored"):
            if r[f] not in BOOL: errors.append(f"{label}: {f} must be YES/NO")
        if r["default_gate"]=="YES":
            if r["default_scored"]!="NO": errors.append(f"{label}: gate rows must be unscored")
            if r["gate_stage"] not in stages or r["gate_stage"]=="evidence": errors.append(f"{label}: invalid bank gate_stage")
        elif r["gate_stage"]: errors.append(f"{label}: non-gate must not have gate_stage")
        if r["relation_to_parent"] not in RELATIONS: errors.append(f"{label}: invalid relation_to_parent")
        if bool(r["parent_question_id"]) != bool(r["relation_to_parent"]): errors.append(f"{label}: parent and relation must both be present or blank")
        if not r["construct_id"]: errors.append(f"{label}: blank construct_id")
        if not r["question"].endswith("?"): errors.append(f"{label}: question must end with ?")
        for f in ("question","applicability","evidence_standard","failure_example","version_added"):
            if not r[f]: errors.append(f"{label}: {f} required")
        if not re.fullmatch(r"\d+\.\d+\.\d+",r["version_added"]): errors.append(f"{label}: invalid version_added")
        if r["status"]=="retired" and not r["version_retired"]: errors.append(f"{label}: retired row needs version_retired")
        n=re.sub(r"\W+"," ",r["question"].lower()).strip()
        if n in exact: errors.append(f"{label}: exact duplicate wording with {exact[n]}")
        exact[n]=label; tokenized[qid]=tokens(r["question"])
        if re.search(r"\bnot\b|rather than",r["question"].lower()): warnings.append(f"{label}: inspect negative polarity")
        if len(re.findall(r"\b(?:and|or)\b",r["question"].lower()))>=3: warnings.append(f"{label}: inspect atomicity")
    for r in rows:
        p=r.get("parent_question_id","")
        if not p: continue
        qid=r["question_id"]
        if p not in by_id: errors.append(f"{qid}: missing parent {p}"); continue
        pr=by_id[p]
        if pr["construct_id"]!=r["construct_id"]: errors.append(f"{qid}: parent construct mismatch")
        if pr["dimension"]!=r["dimension"]: errors.append(f"{qid}: parent dimension mismatch")
        if pr["tier"]=="deep" and r["tier"]=="core": errors.append(f"{qid}: core child cannot depend on deep parent {p}")
        if specificity[p]>=specificity[qid]: errors.append(f"{qid}: parent must be less specific")
        seen={qid}; cur=p
        while cur:
            if cur in seen: errors.append(f"{qid}: parent cycle"); break
            seen.add(cur); cur=by_id.get(cur,{}).get("parent_question_id","")
    # Gate constructs must be single-member globally.
    by_construct=defaultdict(list)
    for r in rows:
        if r["status"]=="active": by_construct[r["construct_id"]].append(r)
    for cid,members in by_construct.items():
        if any(r["default_gate"]=="YES" for r in members) and len(members)>1: errors.append(f"construct {cid}: gate construct has multiple members")
    # Similar wording is a review warning, not an automatic error.
    qids=sorted(tokenized)
    for i,q1 in enumerate(qids):
        for q2 in qids[i+1:]:
            a,b=tokenized[q1],tokenized[q2]
            score=len(a&b)/len(a|b) if a|b else 0
            if score>=0.72 and by_id[q1]["construct_id"]!=by_id[q2]["construct_id"]:
                warnings.append(f"{q1}/{q2}: near-duplicate wording ({score:.2f}) across constructs")
    assembly_reports={}
    legal=legal_assemblies(manifest)
    for cls,sub,exp in sorted(legal):
        names=selected_files(manifest,cls,sub,exp); selected=[r for r in rows if r["_source"] in names and r["status"]=="active"]
        key=f"{cls}/{sub}/{exp}"
        missing=factors-{r["factor"] for r in selected}
        if missing: errors.append(f"{key}: missing factors {sorted(missing)}")
        children=defaultdict(list); roots=defaultdict(list)
        for r in selected:
            if r["parent_question_id"]: children[r["parent_question_id"]].append(r["question_id"])
            else: roots[r["construct_id"]].append(r["question_id"])
        for cid,root_ids in roots.items():
            if len(root_ids)>1: errors.append(f"{key}: construct {cid} has multiple roots {root_ids}")
        for parent,ch in children.items():
            if len(ch)>1: errors.append(f"{key}: construct branches at {parent}: {ch}")
        # No two rows at the same specificity within one construct.
        levels=Counter((r["construct_id"],specificity[r["question_id"]]) for r in selected)
        for (cid,rank),count in levels.items():
            if count>1: errors.append(f"{key}: construct {cid} has {count} rows at specificity {rank}")
        suppressed=set(suppression_map(manifest,cls,sub,exp));gate_only=manifest.get('gate_only_dimensions_by_tier',{})
        for tier in ('core','full'):
            tier_rows=[r for r in selected if r['question_id'] not in suppressed and (tier=='full' or r['tier']=='core')]
            for dim in {r['dimension'] for r in tier_rows}:
                if not any(r['dimension']==dim and r['default_scored']=='YES' for r in tier_rows) and dim not in gate_only.get(tier,[]):errors.append(f"{key}/{tier}: dimension {dim} has no scored construct and is not declared gate-only")
        assembly_reports[key]={"full_rows":len(selected),"core_rows":sum(r["tier"]=="core" for r in selected),"constructs":len({r["construct_id"] for r in selected}),"gates":sum(r["default_gate"]=="YES" for r in selected)}
    # Every declared suppression must identify an active row in the selected class family.
    for class_data in manifest.get("subtypes",{}).values():
        for data in class_data.values():
            for qid in data.get("suppress",[]):
                if qid not in by_id: errors.append(f"manifest suppression references unknown {qid}")
    for data in manifest.get("exposures",{}).values():
        for qid in data.get("suppress",[]):
            if qid not in by_id: errors.append(f"manifest suppression references unknown {qid}")
    # Migration coverage and exact hash verification for frozen v1.
    old_manifest_path=args.manifest.parent/"versions/1.0.0/bank-manifest.json"
    try:
        old_manifest=json.loads(old_manifest_path.read_text(encoding='utf-8'))
        import hashlib
        for name,meta in old_manifest['files'].items():
            actual=hashlib.sha256((old_manifest_path.parent/name).read_bytes()).hexdigest()
            if actual!=meta['sha256']:errors.append(f"v1 freeze hash mismatch for {name}")
        payload={k:v for k,v in old_manifest.items() if k!='bank_hash'}
        actual=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
        if actual!=old_manifest['bank_hash']:errors.append('v1 freeze bank_hash mismatch')
    except (OSError,KeyError,json.JSONDecodeError) as e:errors.append(f'cannot verify v1 freeze: {e}')
    migration=args.manifest.parent/"migration-1.0.0-to-2.0.0.csv"; migration_count=0
    if migration.exists():
        with migration.open(newline="",encoding="utf-8") as f: mrows=list(csv.DictReader(f))
        migration_count=len(mrows); mapped={r["old_id"] for r in mrows}
        old_ids=set()
        for name in ("question-bank-common.csv","question-bank-crypto.csv","question-bank-stocks.csv"):
            with (args.manifest.parent/"versions/1.0.0"/name).open(newline="",encoding="utf-8") as f: old_ids|={r["question_id"] for r in csv.DictReader(f)}
        if old_ids-mapped: errors.append(f"migration missing old IDs {sorted(old_ids-mapped)}")
        for r in mrows:
            if r["new_id"] and r["new_id"] not in by_id: errors.append(f"migration maps to unknown {r['new_id']}")
            elif r["new_id"] and r["construct_id"]!=by_id[r["new_id"]]["construct_id"]:errors.append(f"migration construct mismatch for {r['new_id']}: {r['construct_id']} != {by_id[r['new_id']]['construct_id']}")
    else: errors.append("missing migration-1.0.0-to-2.0.0.csv")
    report:dict[str,Any]={"valid":not errors,"bank_version":manifest.get("bank_version"),"bank_hash":manifest.get("bank_hash"),"rows":len(rows),"active_rows":sum(r["status"]=="active" for r in rows),"unique_ids":len(ids),"assemblies":assembly_reports,"migration_rows":migration_count,"warnings":warnings,"errors":errors}
    rendered=json.dumps(report,indent=2)
    if args.json_path: args.json_path.write_text(rendered+"\n",encoding="utf-8")
    print(rendered); return 0 if not errors else 1
if __name__=="__main__": raise SystemExit(main())
