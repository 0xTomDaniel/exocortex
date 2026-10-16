// OptChat compactor comparison: Haiku 5.5 high / xhigh vs Sonnet 5.5 medium (current).
// Real compaction tasks from a TEMP COPY of the clone's memory, run through OptChat's own
// createCompressor (same prompts, 512-byte rule, 640-byte tolerance, retries). Blind Opus grading.
// Never writes the real profile. Usage: tsx eval.ts <outDir> [--tasks=30] [--seed=7]
import {cpSync,mkdtempSync,mkdirSync,writeFileSync,readFileSync,existsSync,rmSync} from 'node:fs';
import {join} from 'node:path';import {tmpdir} from 'node:os';
// Locations come from the environment, never from this file:
//   OPTCHAT_DIR      a pi-optchat checkout (upstream)
//   OPTCHAT_PROFILE  the OptChat profile directory whose memory is sampled (copied to a temp dir; never written)
//   PI_PACKAGE       the pi-coding-agent package directory (default: global modules of the running Node)
const need=(k:string)=>{const v=process.env[k];if(!v)throw Error(`Set ${k}`);return v;};
const UP=need('OPTCHAT_DIR'),PROFILE=need('OPTCHAT_PROFILE');
const G=process.env.PI_PACKAGE??join(process.execPath,'..','..','lib','node_modules','@earendil-works','pi-coding-agent');
const {Memory,start,end,flat,bytes,NODE}=await import(UP+'/src/memory.ts') as any;
const {createCompressor}=await import(UP+'/src/compactor.ts') as any;
const {ModelRuntime,ModelRegistry}=await import(G+'/dist/index.js') as any;
const arg=(k:string,d:string)=>process.argv.find(a=>a.startsWith(`--${k}=`))?.slice(k.length+3)??d;
const out=process.argv[2];if(!out)throw Error('outDir required');mkdirSync(out,{recursive:true});
const N=Number(arg('tasks','30')),seed=Number(arg('seed','7'));let s=seed;const rand=()=>((s=(s*1103515245+12345)%2**31)/2**31);
// 1. Temp copy of the clone's memory; a compressor that never answers, so opening it cannot build anything.
const live=join(PROFILE,'memories');const id=JSON.parse(readFileSync(join(PROFILE,'active-memory.json'),'utf8'));
const tmp=mkdtempSync(join(tmpdir(),'optchat-eval-'));const memId=(typeof id==='string'?id:Object.values(id).find(v=>typeof v==='string') as string).split('/').pop()!;if(!existsSync(join(live,memId)))throw Error('active memory not found');
cpSync(join(live,memId),join(tmp,memId),{recursive:true});
const never=()=>new Promise<string>(()=>{});const memory:any=new Memory(join(tmp,memId),never,()=>{});
// 2. Sample real tasks: leaves needing compression (> 512 bytes), and merges at several levels; native history only.
const root=memory.root as any[],tree=memory.tree as Map<number,any>,K=(l:number,i:number)=>l*2**40+i;
const native=(p:any)=>root.slice(start(p),end(p)).every((e:any)=>!e.origin);
const leaves=root.filter((e,i)=>!e.origin&&bytes(`${e.kind}: ${e.text}`)>NODE&&i>root.length-3000).map(e=>({l:0,i:e.i}));
const merges=[...tree.values()].filter(n=>n.l>=1&&n.l<=9&&native(n)&&tree.has(K(n.l-1,2*n.i))&&tree.has(K(n.l-1,2*n.i+1))).map(n=>({l:n.l,i:n.i}));
const pick=(a:any[],k:number)=>{const c=[...a],r:any[]=[];while(r.length<k&&c.length)r.push(c.splice(Math.floor(rand()*c.length),1)[0]);return r;};
const byLevel=new Map<number,any[]>();for(const m of merges)byLevel.set(m.l,[...(byLevel.get(m.l)??[]),m]);
const mergeTasks:any[]=[];const M=Number(arg('merges',String(process.argv.includes('--merges-only')?N:Math.floor(N/2))));for(let k=0;mergeTasks.length<M&&k<200;k++)for(const[,v]of byLevel){if(mergeTasks.length>=M)break;const p=pick(v.filter(x=>!mergeTasks.includes(x)),1)[0];if(p)mergeTasks.push(p);}
const mergesOnly=process.argv.includes('--merges-only');
const tasks=mergesOnly?mergeTasks:[...pick(leaves,Number(arg('leaves',String(N-mergeTasks.length)))),...mergeTasks];
const input=(part:any)=>{const text=(p:any)=>memory.text(p);const source=part.l===0?`${root[part.i].kind}: ${root[part.i].text}`:[0,1].map(o=>text({l:part.l-1,i:2*part.i+o})).join('\n');
 const mergeSource=part.l>0?[0,1].map(o=>flat(text({l:part.l-1,i:2*part.i+o}))).join('\n'):source;const call=part.l===0?memory.callOf(part.i):undefined;
 return {context:memory.compactionView(part),source:mergeSource,part,historical:false,...(call?{call:{i:call.i,text:`tool: ${call.text}`.slice(0,4000)}}:{})};};
const inputs=tasks.map(p=>({part:p,input:input(p),existing:tree.get(K(p.l,p.i))?.text??null}));
// 3. Run each configuration through OptChat's own compressor.
const runtime=await ModelRuntime.create({});const registry=new ModelRegistry(runtime);
const ALL=[{name:'sonnet-5.5-medium',provider:'anthropic',model:'claude-sonnet-5-5',thinking:'medium'},{name:'haiku-5.5-medium',provider:'anthropic',model:'claude-haiku-5-5',thinking:'medium'},{name:'haiku-5.5-high',provider:'anthropic',model:'claude-haiku-5-5',thinking:'high'},{name:'haiku-5.5-xhigh',provider:'anthropic',model:'claude-haiku-5-5',thinking:'xhigh'},{name:'gpt-6-luna-medium',provider:'openai-codex',model:'gpt-6-luna',thinking:'medium'},{name:'gpt-6-luna-high',provider:'openai-codex',model:'gpt-6-luna',thinking:'high'},{name:'gpt-6-luna-xhigh',provider:'openai-codex',model:'gpt-6-luna',thinking:'xhigh'}];
const want=arg('configs','sonnet-5.5-medium,haiku-5.5-high,haiku-5.5-xhigh').split(',');const CONFIGS=want[0]==='all'?ALL:ALL.filter(c=>want.includes(c.name));
const results:any[]=[];
writeFileSync(join(out,'inputs.json'),JSON.stringify(inputs));
await Promise.all(CONFIGS.map(async cfg=>{
 const queue=[...inputs.keys()];const work=async()=>{for(let j=queue.shift();j!==undefined;j=queue.shift()){
  const usage:any[]=[];const compress=createCompressor(registry,()=>cfg,(m:any)=>usage.push(m.usage),()=>640);const t0=Date.now();let line:string|null=null,error:string|null=null;
  try{line=await compress(inputs[j].input,AbortSignal.timeout(300000));}catch(e:any){error=String(e?.message??e);}
  results.push({config:cfg.name,task:j,part:inputs[j].part,line,error,bytes:line?bytes(line):null,calls:usage.length,ms:Date.now()-t0,cost:usage.reduce((a,u)=>a+(u?.cost?.total??0),0),output:usage.reduce((a,u)=>a+(u?.output??0),0),reasoning:usage.reduce((a,u)=>a+(u?.reasoning??0),0)});
  process.stderr.write(`${cfg.name} task ${j} ${error?'ERROR '+error:bytes(line)+'B'} ${usage.length} call(s)\n`);}};
 await Promise.all([work(),work()]);
}));
writeFileSync(join(out,'tasks.json'),JSON.stringify(inputs.map(x=>({part:x.part,source:x.input.source,call:x.input.call??null,existing:x.existing,contextBytes:x.input.context.length})),null,1));
writeFileSync(join(out,'outputs.json'),JSON.stringify(results,null,1));
// 4. Blind grading by Opus 5.5 (high): per task, the source and the three lines in random order.
const judge=registry.find('anthropic','claude-opus-5-5');
const LABELS='ABCDEFG'.split('').slice(0,CONFIGS.length);
const RUBRIC=`You grade summaries written by a memory compactor for a personal AI assistant. Each summary replaces the SOURCE in the assistant's long-term memory and must let it later recall what matters: decisions, commitments, user corrections and preferences, facts with their numbers, names and dates, open loops, and outcomes (distinguishing attempts from successes). Summaries are limited to about 512 bytes, so judge what each keeps within that limit.
For EACH labelled summary give: "errors" (list of statements that are wrong or unsupported by the SOURCE; [] if none), "coverage" 1-5 (how much of what matters it keeps), "usefulness" 1-5 (how well the assistant could act on it later: precise, specific, unambiguous). Then "rank": all labels from best to worst. Reply with JSON only, one key per label plus "rank": {"A":{"errors":[],"coverage":n,"usefulness":n},"B":{...},...,"rank":["A","B",...]}`;
const grades:any[]=[];const gq=[...inputs.keys()];
const grade=async()=>{for(let j=gq.shift();j!==undefined;j=gq.shift()){
 const rows=CONFIGS.map(c=>results.find(r=>r.task===j&&r.config===c.name));const order=CONFIGS.map((_,k)=>k).sort(()=>rand()-.5),labels=LABELS;
 const src=inputs[j].part.l===0?inputs[j].input.source:`Two adjacent memory lines being merged (each already summarizes earlier messages):\n${inputs[j].input.source}`;
 const body=`${RUBRIC}\n\n<SOURCE>\n${src.slice(0,14000)}\n</SOURCE>\n\n`+order.map((k,n)=>`<SUMMARY ${labels[n]}>\n${rows[k]?.line??'(no summary: the compactor failed)'}\n</SUMMARY ${labels[n]}>`).join('\n\n');
 try{const r=await registry.streamSimple(judge,{messages:[{role:'user',content:body,timestamp:Date.now()}]},{reasoning:'high',signal:AbortSignal.timeout(300000)}).result();if(r.stopReason==='error')throw Error(r.errorMessage);
  const text=r.content.filter((c:any)=>c.type==='text').map((c:any)=>c.text).join('');const g=JSON.parse(text.slice(text.indexOf('{'),text.lastIndexOf('}')+1));
  grades.push({task:j,cost:r.usage?.cost?.total??0,scores:Object.fromEntries(order.map((k,n)=>[CONFIGS[k].name,{...g[labels[n]],rank:g.rank.indexOf(labels[n])+1}]))});process.stderr.write(`graded ${j}\n`);}
 catch(e:any){grades.push({task:j,error:String(e?.message??e)});}}};
await Promise.all([grade(),grade(),grade()]);
writeFileSync(join(out,'grades.json'),JSON.stringify(grades,null,1));
// 5. Summary.
const mean=(a:number[])=>a.length?+(a.reduce((x,y)=>x+y,0)/a.length).toFixed(2):null,med=(a:number[])=>{const c=[...a].sort((x,y)=>x-y);return c.length?c[Math.floor((c.length-1)/2)]:null;};
const summary:any={tasks:inputs.length,leaves:inputs.filter(x=>x.part.l===0).length,merges:inputs.filter(x=>x.part.l>0).length,levels:[...new Set(inputs.map(x=>x.part.l))].sort((a,b)=>a-b),configs:{}};
for(const c of CONFIGS){const rs=results.filter(r=>r.config===c.name),gs=grades.filter(g=>g.scores?.[c.name]).map(g=>g.scores[c.name]);
 summary.configs[c.name]={failures:rs.filter(r=>r.error).length,within512:rs.filter(r=>r.bytes!==null&&r.bytes<=512).length,within640:rs.filter(r=>r.bytes!==null&&r.bytes<=640).length,medianBytes:med(rs.filter(r=>r.bytes).map(r=>r.bytes)),extraCalls:rs.reduce((a,r)=>a+Math.max(0,r.calls-1),0),medianMs:med(rs.map(r=>r.ms)),costTotal:+rs.reduce((a,r)=>a+r.cost,0).toFixed(4),costPerSummary:+(rs.reduce((a,r)=>a+r.cost,0)/rs.length).toFixed(5),meanReasoningTokens:mean(rs.map(r=>r.reasoning)),
  errorsTotal:gs.reduce((a,g)=>a+(g.errors?.length??0),0),summariesWithErrors:gs.filter(g=>g.errors?.length).length,coverage:mean(gs.map(g=>g.coverage)),usefulness:mean(gs.map(g=>g.usefulness)),meanRank:mean(gs.map(g=>g.rank)),firstPlace:gs.filter(g=>g.rank===1).length,
  byKind:{leaf:{coverage:mean(grades.filter(g=>g.scores&&inputs[g.task].part.l===0).map(g=>g.scores[c.name].coverage)),rank:mean(grades.filter(g=>g.scores&&inputs[g.task].part.l===0).map(g=>g.scores[c.name].rank))},merge:{coverage:mean(grades.filter(g=>g.scores&&inputs[g.task].part.l>0).map(g=>g.scores[c.name].coverage)),rank:mean(grades.filter(g=>g.scores&&inputs[g.task].part.l>0).map(g=>g.scores[c.name].rank))}}};}
summary.judgeCost=+grades.reduce((a,g)=>a+(g.cost??0),0).toFixed(4);summary.judgeFailures=grades.filter(g=>g.error).length;
writeFileSync(join(out,'summary.json'),JSON.stringify(summary,null,1));console.log(JSON.stringify(summary,null,1));
rmSync(tmp,{recursive:true,force:true});process.exit(0);
