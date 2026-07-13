import json
OUT='/Users/dannyzweben/Desktop/SDN/DTI/SDN-IMPACT-DTI/results_html'
results=json.load(open(f'{OUT}/results_data.json'))
meta=json.load(open(f'{OUT}/meta_data.json'))
demo=meta['demographics']

# scripts registry (shown in detail panel)
SCRIPTS={
 'extraction':'scripts/run_step27_fa_extraction.py (FA) / run_step30_noddi_extraction.py (NDI/ODI/FWF) — AFQ-style tract profiling, 100 nodes, Gaussian-weighted.',
 'covariates':'scripts/extract_imaging_covariates.py — head motion (eddy QUAD qc_mot_abs), ICV (fslstats), streamline count + mean length (tckstats).',
 'merge':'scripts/build_analysis_csvs.py — merges tract profiles + covariates + REDCap outcomes into wide analysis CSVs.',
 'permute':'scripts/permutation_one.R — Freedman–Lane 5000-perm cluster-extent test, one outcome×tract×metric.',
 'runner':'scripts/run_perm_cr2.sh — parallel runner on cr2 (128 cores).',
}

data_js=json.dumps(results)
meta_js=json.dumps(meta)

html='''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>IMPACT VTA→HPC — Results Explorer</title>
<style>
:root{--bg:#0f1117;--card:#1a1d27;--card2:#232733;--ink:#e6e9ef;--mut:#9aa3b2;--line:#2c3140;
--pos:#f4664a;--neg:#3b82f6;--sig:#22c55e;--accent:#a78bfa;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
header{padding:22px 26px;border-bottom:1px solid var(--line);background:linear-gradient(180deg,#171a24,#0f1117)}
h1{margin:0 0 4px;font-size:22px}
.sub{color:var(--mut);font-size:13px}
.wrap{padding:20px 26px;max-width:1400px;margin:0 auto}
.pill{display:inline-block;background:var(--card2);border:1px solid var(--line);border-radius:999px;padding:3px 11px;margin:2px;font-size:12px;color:var(--mut)}
.section{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px 20px;margin:16px 0}
.section h2{margin:0 0 12px;font-size:16px;color:var(--accent)}
.grid{display:grid;gap:10px}
.demo-grid{grid-template-columns:repeat(auto-fit,minmax(190px,1fr))}
.stat{background:var(--card2);border:1px solid var(--line);border-radius:9px;padding:11px 13px}
.stat .k{color:var(--mut);font-size:11px;text-transform:uppercase;letter-spacing:.04em}
.stat .v{font-size:19px;font-weight:600;margin-top:3px}
.stat .d{color:var(--mut);font-size:12px;margin-top:2px}
.controls{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:12px}
.controls select,.controls input{background:var(--card2);color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:7px 10px;font-size:13px}
.controls label{color:var(--mut);font-size:12px;margin-right:3px}
.count{color:var(--mut);font-size:13px;margin-left:auto}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;color:var(--mut);font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.04em;padding:8px 10px;border-bottom:1px solid var(--line);cursor:pointer;user-select:none;white-space:nowrap}
th:hover{color:var(--ink)}
td{padding:8px 10px;border-bottom:1px solid #20242f}
tr.row{cursor:pointer}
tr.row:hover{background:var(--card2)}
tr.sig td{background:rgba(34,197,94,.06)}
.badge{display:inline-block;border-radius:6px;padding:2px 7px;font-size:11px;font-weight:600}
.b-sig{background:rgba(34,197,94,.16);color:#4ade80}
.b-ns{background:#242835;color:var(--mut)}
.b-pos{background:rgba(244,102,74,.16);color:#fb7a5e}
.b-neg{background:rgba(59,130,246,.16);color:#60a5fa}
.hemi{font-weight:600}
.detail{background:var(--card2);border-top:2px solid var(--accent)}
.detail td{padding:0}
.dbox{padding:18px 22px}
.dgrid{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.dcol h4{margin:0 0 8px;font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--accent)}
.kv{display:grid;grid-template-columns:auto 1fr;gap:4px 14px;font-size:13px}
.kv .k{color:var(--mut)}
.nodeviz{margin-top:10px;background:#12141c;border:1px solid var(--line);border-radius:8px;padding:10px}
.script{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11.5px;color:#c9d1e0;background:#12141c;border:1px solid var(--line);border-radius:8px;padding:10px;margin-top:4px;white-space:pre-wrap;line-height:1.45}
.latbar{display:flex;height:26px;border-radius:6px;overflow:hidden;border:1px solid var(--line);margin-top:6px}
.latbar .L{background:#3b82f6;display:flex;align-items:center;justify-content:center;font-size:11px;color:#fff}
.latbar .R{background:#f4664a;display:flex;align-items:center;justify-center;justify-content:center;font-size:11px;color:#fff}
a.back{color:var(--accent);text-decoration:none;font-size:13px}
.legend{font-size:12px;color:var(--mut);margin-top:8px}
.tag{font-size:11px;color:var(--mut)}
.clbl{font-size:11px;color:var(--mut)}
</style></head><body>
<header>
<h1>IMPACT · VTA→HPC Tract Microstructure — Results Explorer</h1>
<div class="sub">All 96 node-wise permutation analyses — 6 outcomes (social &amp; monetary × d′, positivity bias in false memories, positivity bias in correct memories) × 4 tracts × 4 metrics (FA + NODDI: NDI, ODI, FWF). Freedman–Lane, 5000 permutations, cluster-extent FWE at α=0.05. Click any row for the tract, significant nodes, laterality, stats, and scripts. &nbsp;·&nbsp; <a class="back" href="data_quality.html">→ Memory data &amp; d′</a></div>
</header>
<div class="wrap">

<div class="section"><h2>Sample — mothers (DTI analysis cohort)</h2>
<div class="note" style="background:#232733;border-left:3px solid #a78bfa;border-radius:6px;padding:11px 14px;margin:2px 0 14px;font-size:12.5px;color:#c9d1e0">
<b>One consistent roster.</b> 55 mothers with complete VTA→HPC tractography (2 pilot scans removed; maternal age recovered for all 55 from current demographics). Memory outcomes were recomputed directly from the raw trial files with the standard signal-detection d′ formula, and <b>2 sessions with corrupted or heavily-missed recall were excluded on data-quality grounds</b>. Resulting per-outcome N: <b>social d′ = 53, monetary d′ = 54</b>; bias metrics <b>51–53</b> (a few mothers also lack the valence-broken-down counts a bias score needs). The exact N is shown on every result row.</div>
<div id="demo"></div></div>

<div class="section"><h2>Outcomes analysed — definitions</h2>
<div class="grid" style="grid-template-columns:1fr;gap:12px">
 <div class="stat"><div class="k">Memory accuracy — d′</div>
  <div style="font-size:13.5px;margin-top:5px">Signal-detection sensitivity: how well a mother tells apart items she actually saw (with feedback) from lures. <span class="tag">d′ = z(hit rate) − z(false-alarm rate). Higher = sharper memory. Run separately for the <b>social</b> (faces/feedback) and <b>monetary</b> (doors) tasks.</span></div></div>
 <div class="stat"><div class="k">Positivity bias — false memories &nbsp;(<code>FABias</code>)</div>
  <div style="font-size:13.5px;margin-top:5px">Among items she <b>falsely</b> "remembered" (never actually shown), was she more likely to false-alarm to <b>positive</b> than <b>negative</b> items?
  <div class="script" style="margin-top:6px">FABias = P(false alarm | positive item) − P(false alarm | negative item)
       = (FalseMem_positive / N_positive) − (FalseMem_negative / N_negative)</div>
  <span class="tag">Positive value → she conjures up more <i>positive</i> false memories (rose-tinted misremembering). Negative value → more negative false memories.</span></div></div>
 <div class="stat"><div class="k">Positivity bias — correct memories &nbsp;(<code>HitRateBias</code>)</div>
  <div style="font-size:13.5px;margin-top:5px">Among items she actually saw, was she more likely to <b>correctly</b> remember <b>positive</b> than <b>negative</b> ones?
  <div class="script" style="margin-top:6px">HitRateBias = P(hit | positive item) − P(hit | negative item)
          = (TrueMem_positive / N_positive) − (TrueMem_negative / N_negative)</div>
  <span class="tag">Positive value → better memory for positive material. This is the "accuracy" side of valence bias, vs. FABias which is the "error" side.</span></div></div>
</div></div>

<div class="section"><h2>All results</h2>
<div class="controls">
<span><label>Outcome family</label><select id="f_family"></select></span>
<span><label>Condition</label><select id="f_cond"></select></span>
<span><label>Tract</label><select id="f_tract"></select></span>
<span><label>Hemisphere</label><select id="f_hemi"></select></span>
<span><label>Metric</label><select id="f_metric"></select></span>
<span><label>Show</label><select id="f_sig"><option value="all">All</option><option value="sig">FWE-significant only</option><option value="trend">≥5 sig nodes</option></select></span>
<input id="f_search" placeholder="search…" style="min-width:130px">
<span class="count" id="count"></span>
</div>
<table id="tbl"><thead><tr>
<th data-k="outcome_label">Outcome</th><th data-k="family">Family</th><th data-k="condition">Cond</th>
<th data-k="tract_label">Tract</th><th data-k="hemisphere">Hemi</th><th data-k="tract_type">Type</th>
<th data-k="metric">Metric</th><th data-k="N">N</th><th data-k="n_sig_nodes">Sig nodes</th>
<th data-k="obs_max_cluster">Max cluster</th><th data-k="extent_threshold">Thresh</th>
<th data-k="best_p">Cluster p</th><th data-k="passed">FWE</th>
</tr></thead><tbody id="tbody"></tbody></table>
<div class="legend">FWE = cluster passes permutation extent threshold. Direction: <span class="badge b-pos">Positive</span> higher metric → higher outcome · <span class="badge b-neg">Negative</span> higher metric → lower outcome.<br><b>Node values are partial-regression t-statistics</b> (each node = outcome regressed on that node’s metric + covariates), not zero-order correlations. In the detail view, the <b>Hemispheric node overlap</b> panel stacks the L and R tracts aligned by node so you can see whether the significant nodes fall in the same place; nodes significant on <span style="color:#4ade80">both</span> sides are shown in green.</div>
</div>
</div>

<script>
const DATA=__DATA__;
const META=__META__;
const SCRIPTS=__SCRIPTS__;

// ---- demographics ----
(function(){
 const d=META.demographics; const el=document.getElementById('demo');
 function dist(o){return Object.entries(o).map(([k,v])=>`<span class="pill">${k}: ${v}</span>`).join('')}
 let h='<div class="grid demo-grid">';
 h+=`<div class="stat"><div class="k">N (DTI roster)</div><div class="v">${d.n_dti}</div><div class="d">mothers w/ tractography (2 pilots excluded)</div></div>`;
 h+=`<div class="stat"><div class="k">Maternal age</div><div class="v">${d.age.mean} ± ${d.age.sd}</div><div class="d">range ${d.age.min}–${d.age.max} (n=${d.age.n})</div></div>`;
 if(d.income&&d.income.median)h+=`<div class="stat"><div class="k">Household income</div><div class="v">$${(d.income.median/1000).toFixed(0)}k</div><div class="d">median · range $${(d.income.min/1000).toFixed(0)}k–$${(d.income.max/1000).toFixed(0)}k</div></div>`;
 h+='</div>';
 h+='<div style="margin-top:12px"><div class="clbl">Race</div>'+dist(d.race)+'</div>';
 h+='<div style="margin-top:8px"><div class="clbl">Ethnicity</div>'+dist(d.ethnicity)+'</div>';
 h+='<div style="margin-top:8px"><div class="clbl">Education</div>'+dist(d.education)+'</div>';
 h+='<div style="margin-top:8px"><div class="clbl">Marital status</div>'+dist(d.marital)+'</div>';
 el.innerHTML=h;
})();

// ---- filters ----
function uniq(k){return [...new Set(DATA.map(r=>r[k]))].sort()}
function fillSel(id,vals,label){const s=document.getElementById(id);s.innerHTML=`<option value="">${label}</option>`+vals.map(v=>`<option>${v}</option>`).join('')}
fillSel('f_family',uniq('family'),'All families');
fillSel('f_cond',uniq('condition'),'All');
fillSel('f_tract',uniq('tract_label'),'All tracts');
fillSel('f_hemi',uniq('hemisphere'),'All');
fillSel('f_metric',uniq('metric'),'All');

let sortK='best_p',sortDir=1;
document.querySelectorAll('th').forEach(th=>th.onclick=()=>{const k=th.dataset.k;if(sortK===k)sortDir*=-1;else{sortK=k;sortDir=1}render()});

function passFilters(r){
 const fam=f_family.value,cond=f_cond.value,tr=f_tract.value,he=f_hemi.value,me=f_metric.value,sg=f_sig.value,q=f_search.value.toLowerCase();
 if(fam&&r.family!==fam)return false;
 if(cond&&r.condition!==cond)return false;
 if(tr&&r.tract_label!==tr)return false;
 if(he&&r.hemisphere!==he)return false;
 if(me&&r.metric!==me)return false;
 if(sg==='sig'&&!r.passed)return false;
 if(sg==='trend'&&r.n_sig_nodes<5)return false;
 if(q&&!(r.outcome_label+' '+r.tract_label+' '+r.metric+' '+r.family).toLowerCase().includes(q))return false;
 return true;
}
['f_family','f_cond','f_tract','f_hemi','f_metric','f_sig','f_search'].forEach(id=>document.getElementById(id).oninput=render);

function dirBadge(d){return d==='Positive'?'<span class="badge b-pos">Positive</span>':'<span class="badge b-neg">Negative</span>'}
function fmtP(p){return (p===0||p===0.0)?'<0.0002':p}  // permutation p of 0 = 0/5000 → floor to <1/nperm

function nodeViz(r){
 // inline SVG bar of t-values, sig nodes highlighted
 const W=560,H=90,pad=18,n=100;
 const ts=r.tvals.map(x=>x==null?0:x);
 const mx=Math.max(3,...ts.map(Math.abs));
 const bw=(W-2*pad)/n;
 let bars='';
 for(let i=0;i<n;i++){
  const t=ts[i];const sig=r.pvals[i]!=null&&r.pvals[i]<0.05;
  const h=Math.abs(t)/mx*(H/2-8);
  const y=t>=0?(H/2-h):(H/2);
  const col=sig?(t>=0?'#f4664a':'#3b82f6'):'#39404f';
  bars+=`<rect x="${pad+i*bw}" y="${y}" width="${Math.max(bw-0.4,0.6)}" height="${h}" fill="${col}"><title>node ${i}: t=${t}</title></rect>`;
 }
 // cluster shading
 let shade='';
 r.clusters.forEach(c=>{if(c.passes)shade+=`<rect x="${pad+c.start*bw}" y="4" width="${(c.end-c.start+1)*bw}" height="${H-8}" fill="rgba(34,197,94,.10)" stroke="rgba(34,197,94,.4)"/>`;});
 return `<svg viewBox="0 0 ${W} ${H}" width="100%" style="max-width:${W}px">
  ${shade}<line x1="${pad}" y1="${H/2}" x2="${W-pad}" y2="${H/2}" stroke="#4a5163" stroke-width="1"/>${bars}
  <text x="${pad}" y="${H-2}" fill="#6b7280" font-size="9">VTA (node 0)</text>
  <text x="${W-pad}" y="${H-2}" fill="#6b7280" font-size="9" text-anchor="end">HPC (node 99)</text>
 </svg>`;
}

function detail(r){
 const lat=r.laterality;
 const Lp=lat.pct_left!=null?lat.pct_left:0, Rp=lat.pct_right!=null?lat.pct_right:0;
 let clusters=r.clusters.length?('<table style="width:auto"><thead><tr><th>Nodes</th><th>Size</th><th>Dir</th><th>mean t</th><th>max|t|</th><th>@node</th><th>cluster p</th><th>FWE</th></tr></thead><tbody>'+
   r.clusters.map(c=>`<tr><td>${c.start}–${c.end}</td><td>${c.size}</td><td>${dirBadge(c.dir)}</td><td>${c.mean_t}</td><td>${c.max_abs_t}</td><td>${c.max_abs_t_node}</td><td>${fmtP(c.p)}</td><td>${c.passes?'<span class="badge b-sig">PASS</span>':'<span class="badge b-ns">no</span>'}</td></tr>`).join('')+'</tbody></table>')
   :'<span class="tag">No contiguous clusters formed.</span>';
 const signodes=r.sig_node_list.length?r.sig_node_list.join(', '):'none';
 return `<td colspan="13" class="detail"><div class="dbox">
  <div class="dgrid">
   <div class="dcol">
    <h4>${r.outcome_label} &nbsp;·&nbsp; ${r.tract_label} &nbsp;·&nbsp; ${r.metric}</h4>
    <div class="kv">
     <div class="k">Outcome family</div><div>${r.family}</div>
     <div class="k">Condition</div><div>${r.condition}</div>
     <div class="k">Tract</div><div>${r.tract_label} <span class="tag">(${r.tract_type}, ${r.hemisphere} hemisphere)</span></div>
     <div class="k">Microstructure metric</div><div>${r.metric}</div>
     <div class="k">N (after listwise deletion)</div><div>${r.N} <span class="tag">(${r.dropped} dropped)</span></div>
     <div class="k">Permutations</div><div>${r.n_perms} (Freedman–Lane)</div>
     <div class="k">Nodewise-significant nodes</div><div>${r.n_sig_nodes} / 100</div>
     <div class="k">Observed max cluster</div><div>${r.obs_max_cluster} nodes</div>
     <div class="k">Extent threshold (95th %ile null)</div><div>${r.extent_threshold} nodes</div>
     <div class="k">FWE verdict</div><div>${r.passed?'<span class="badge b-sig">SIGNIFICANT</span> (cluster p='+fmtP(r.best_p)+')':'<span class="badge b-ns">n.s.</span>'}</div>
    </div>
    <h4 style="margin-top:16px">Controlled for (covariates)</h4>
    <div class="tag">${r.covariates}</div>
    <h4 style="margin-top:16px">Laterality <span class="tag">(nodewise-sig nodes, ${r.tract_type} L vs R, ${r.metric})</span></h4>
    <div class="latbar"><div class="L" style="width:${Lp}%">L ${lat.L_sig} (${Lp}%)</div><div class="R" style="width:${Rp}%">R ${lat.R_sig} (${Rp}%)</div></div>
    <h4 style="margin-top:14px">Hemispheric node overlap <span class="tag">(same outcome+metric, both ${r.tract_type} tracts aligned by node)</span></h4>
    <div class="nodeviz">${dualLatViz(r)}</div>
    <div class="tag" style="margin-top:6px">Overlapping significant nodes (sig on <b>both</b> L &amp; R): ${(lat.overlap_nodes&&lat.overlap_nodes.length)?'<span style="color:#4ade80">'+lat.overlap_nodes.join(', ')+'</span>':'none'}</div>
   </div>
   <div class="dcol">
    <h4>Node-wise t-values <span class="tag">(partial-regression t, covariate-adjusted — not a raw correlation; green = FWE cluster; colored bars = p&lt;0.05)</span></h4>
    <div class="nodeviz">${nodeViz(r)}</div>
    <h4 style="margin-top:14px">Clusters</h4>${clusters}
    <h4 style="margin-top:14px">Significant nodes (p&lt;0.05, uncorrected)</h4>
    <div class="tag" style="line-height:1.6">${signodes}</div>
   </div>
  </div>
  <h4 style="margin-top:18px">Scripts used to produce this result</h4>
  <div class="script">1. Tract profiling → ${r.metric==='FA'?SCRIPTS.extraction.split(' / ')[0]:SCRIPTS.extraction.split(' / ')[1]}
2. Covariates → ${SCRIPTS.covariates}
3. Merge → ${SCRIPTS.merge}
4. Permutation test → ${SCRIPTS.permute}
5. Parallel runner → ${SCRIPTS.runner}
Command: Rscript permutation_one.R &lt;csv&gt; ${r.outcome} ${r.metric}_ &lt;out&gt; ${r.id}</div>
 </div></td>`;
}


function siblingOf(r){return DATA.find(x=>x.outcome===r.outcome&&x.metric===r.metric&&x.tract_type===r.tract_type&&x.hemisphere!==r.hemisphere)}
function miniProfile(r,label,overlap){
 const W=560,H=64,pad=18,n=100;const ts=r?r.tvals.map(x=>x==null?0:x):new Array(100).fill(0);
 const mx=Math.max(3,...ts.map(Math.abs));const bw=(W-2*pad)/n;let bars='';
 for(let i=0;i<n;i++){const t=ts[i];const sig=r&&r.pvals[i]!=null&&r.pvals[i]<0.05;const ov=overlap.includes(i);
  const h=Math.abs(t)/mx*(H/2-6);const y=t>=0?(H/2-h):(H/2);
  const col=ov&&sig?'#22c55e':(sig?(t>=0?'#f4664a':'#3b82f6'):'#39404f');
  bars+=`<rect x="${pad+i*bw}" y="${y}" width="${Math.max(bw-0.4,0.6)}" height="${h}" fill="${col}"><title>node ${i}: t=${t}</title></rect>`;}
 let shade='';if(r)r.clusters.forEach(c=>{if(c.passes)shade+=`<rect x="${pad+c.start*bw}" y="3" width="${(c.end-c.start+1)*bw}" height="${H-6}" fill="rgba(34,197,94,.08)" stroke="rgba(34,197,94,.35)"/>`;});
 return `<div style="display:flex;align-items:center;gap:8px"><div style="width:34px;font-size:11px;color:var(--mut);text-align:right">${label}</div>
  <svg viewBox="0 0 ${W} ${H}" width="100%" style="max-width:${W}px">${shade}<line x1="${pad}" y1="${H/2}" x2="${W-pad}" y2="${H/2}" stroke="#4a5163"/>${bars}</svg></div>`;
}
function dualLatViz(r){
 const sib=siblingOf(r);const ov=r.laterality.overlap_nodes||[];
 const Lr=r.hemisphere==='L'?r:sib, Rr=r.hemisphere==='R'?r:sib;
 return miniProfile(Lr,'L',ov)+miniProfile(Rr,'R',ov)+
  `<div style="font-size:10px;color:var(--mut);text-align:right;padding-right:2px">node 0 (VTA) ————— node 99 (HPC)</div>`;
}

let openId=null;
function render(){
 let rows=DATA.filter(passFilters);
 rows.sort((a,b)=>{let x=a[sortK],y=b[sortK];
  if(sortK==='best_p'){x=x==null?9:x;y=y==null?9:y}
  if(typeof x==='string')return sortDir*x.localeCompare(y);
  return sortDir*((x>y)-(x<y));});
 const tb=document.getElementById('tbody');tb.innerHTML='';
 rows.forEach(r=>{
  const tr=document.createElement('tr');tr.className='row'+(r.passed?' sig':'');
  const dir=r.clusters.find(c=>c.passes);
  tr.innerHTML=`<td><b>${r.outcome_label}</b></td><td>${r.family}</td><td>${r.condition}</td>
   <td>${r.tract_label}</td><td class="hemi ${r.hemisphere==='L'?'':''}">${r.hemisphere}</td><td>${r.tract_type}</td>
   <td>${r.metric}</td><td>${r.N}</td><td>${r.n_sig_nodes}</td><td>${r.obs_max_cluster}</td><td>${r.extent_threshold}</td>
   <td>${r.best_p!=null?fmtP(r.best_p)+' '+(dir?dirBadge(dir.dir):''):'<span class="tag">—</span>'}</td>
   <td>${r.passed?'<span class="badge b-sig">✓</span>':'<span class="badge b-ns">·</span>'}</td>`;
  tr.onclick=()=>{
   const nx=tr.nextSibling;
   if(nx&&nx.classList&&nx.classList.contains('detail-row')){nx.remove();openId=null;return}
   document.querySelectorAll('.detail-row').forEach(e=>e.remove());
   const dr=document.createElement('tr');dr.className='detail-row';dr.innerHTML=detail(r);
   tr.after(dr);openId=r.id;
  };
  tb.appendChild(tr);
 });
 document.getElementById('count').textContent=`${rows.length} of ${DATA.length} analyses · ${rows.filter(r=>r.passed).length} FWE-significant`;
}
render();
</script></body></html>'''

html=html.replace('__DATA__',data_js).replace('__META__',meta_js).replace('__SCRIPTS__',json.dumps(SCRIPTS))
open(f'{OUT}/results_explorer.html','w').write(html)
print("wrote results_explorer.html",len(html),"bytes")
