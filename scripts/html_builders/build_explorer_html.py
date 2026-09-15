#!/usr/bin/env python3
"""
Build results_html/results_explorer.html.

Reported analysis first (whole-tract model with a subregion term, then quartiles and the metric
comparison), then an interactive browser over every node-wise permutation test that was run, then
the hippocampal gray-matter and HVLT tables. Data: results_data.json + models_data.json
(scripts/html_builders/build_results_data.py).
"""
import json
OUT = '/Users/dannyzweben/Desktop/SDN/DTI/SDN-IMPACT-DTI/results_html'
DATA = json.load(open(f'{OUT}/results_data.json'))
MODELS = json.load(open(f'{OUT}/models_data.json'))
ORDER = ['Social FABias', 'Social d′', 'Social misattribution', 'Monetary FABias', 'Monetary d′', 'Monetary misattribution']
NICE = {'Social FABias': 'Social positive FA bias', 'Monetary FABias': 'Monetary positive FA bias'}


def pcell(p, star=True):
    if p is None: return '<td>—</td>'
    s = f'{p:.3f}'.replace('0.', '.', 1) if p >= .001 else '&lt;.001'
    return f'<td class="sig">{s}{" *" if star else ""}</td>' if p < .05 else f'<td>{s}</td>'


def bcell(b): return f'<td>{b:+.3f}</td>'


def rows(analysis, metric=None, segment=None):
    return [r for r in MODELS if r['analysis'] == analysis and (metric is None or r['metric'] == metric)
            and (segment is None or r['segment'] == segment)]


def whole_table():
    h = '<table class="dtable"><thead><tr><th>Outcome</th><th>Interaction p</th><th>Main effect b</th><th>Main effect p</th></tr></thead><tbody>'
    for o in ORDER:
        r = next(x for x in rows('whole_tract') if x['outcome'] == o)
        h += f'<tr><td>{NICE.get(o,o)}</td>{pcell(r["interaction_p"], False)}{bcell(r["main_b"])}{pcell(r["main_p"])}</tr>'
    return h + '</tbody></table>'


def quart_table(key):
    segs = ['Q1', 'Q2', 'Q3', 'Q4']
    h = f'<table class="dtable"><thead><tr><th>Outcome</th>' + ''.join(f'<th>{s}</th>' for s in segs) + '<th>Whole</th></tr></thead><tbody>'
    for o in ORDER:
        cells = ''
        for s in segs:
            r = next(x for x in rows('quartile', 'NDI', s) if x['outcome'] == o); cells += pcell(r[key], key == 'main_p')
        w = next(x for x in rows('whole_tract') if x['outcome'] == o); cells += pcell(w[key], key == 'main_p')
        h += f'<tr><td>{NICE.get(o,o)}</td>{cells}</tr>'
    return h + '</tbody></table>'


def metric_table():
    mets = ['NDI', 'ODI', 'FWF', 'FA']
    h = '<table class="dtable"><thead><tr><th>Main-effect p</th>' + ''.join(f'<th>{m}</th>' for m in mets) + '</tr></thead><tbody>'
    for o in ORDER:
        cells = ''
        for m in mets:
            r = next((x for x in rows('metric', m) if x['outcome'] == o), None); cells += pcell(r['main_p']) if r else '<td>—</td>'
        h += f'<tr><td>{NICE.get(o,o)}</td>{cells}</tr>'
    return h + '</tbody></table>'


def hpc_table():
    h = '<table class="dtable"><thead><tr><th>Outcome</th><th>β</th><th>p</th><th>n</th></tr></thead><tbody>'
    for o in ORDER:
        r = next(x for x in rows('hpc_gm_ndi') if x['outcome'] == o)
        h += f'<tr><td>{NICE.get(o,o)}</td>{bcell(r["main_b"])}{pcell(r["main_p"])}<td>{r["n"]}</td></tr>'
    return h + '</tbody></table>'


def hvlt_table():
    h = '<table class="dtable"><thead><tr><th>HVLT</th><th>b</th><th>p</th><th>n</th></tr></thead><tbody>'
    for r in rows('hvlt'):
        h += f'<tr><td>{r["outcome"]}</td>{bcell(r["main_b"])}{pcell(r["main_p"])}<td>{r["n"]}</td></tr>'
    return h + '</tbody></table>'


n_all = len(DATA); n_rep = sum(r['reported'] for r in DATA); n_sig = sum(r['passed'] for r in DATA)

HTML = f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>IMPACT · Results</title>
<link rel="stylesheet" href="_pres.css">
<style>
.wrap{{max-width:1040px}}
.controls{{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:10px 0 6px}}
.controls label{{font-size:12px;color:var(--mut);margin-right:3px}}
.controls select,.controls input{{background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:6px;padding:6px 9px;font-size:13px}}
.count{{margin-left:auto;font-size:13px;color:var(--mut)}}
#tbl th{{cursor:pointer;user-select:none;white-space:nowrap}} #tbl th:hover{{color:var(--ink)}}
tr.row{{cursor:pointer}} tr.row:hover td{{background:var(--shade)}}
tr.rep td:first-child{{font-weight:600}}
.badge{{display:inline-block;border-radius:5px;padding:1px 7px;font-size:11.5px;font-weight:600}}
.b-sig{{background:var(--accent-soft);color:var(--accent)}} .b-ns{{background:var(--shade);color:var(--mut)}}
.b-pos{{background:#eef3f1;color:#3a6a5f}} .b-neg{{background:#f6ece8;color:#a8553f}}
tr.detail-row td{{padding:0;background:var(--shade)}}
.dbox{{padding:16px 18px}} .dgrid{{display:grid;grid-template-columns:1fr 1.2fr;gap:18px}} @media (max-width:760px){{.dgrid{{grid-template-columns:1fr}}}}
.dbox h4{{margin:0 0 6px;font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--mut)}}
.kv2{{display:grid;grid-template-columns:auto 1fr;gap:3px 14px;font-size:13.5px}} .kv2 .k{{color:var(--mut)}}
.viz{{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:8px;margin-top:6px}}
.tag{{font-size:12.5px;color:var(--mut)}}
</style></head><body>
<nav class="topnav">
  <span class="brand">IMPACT · <span>VTA→HPC</span> &amp; Motivated Memory</span>
  <a href="intro.html">Overview</a>
  <a href="background.html">Background</a>
  <a href="pipeline.html">Pipeline</a>
  <a href="analyses.html">Analyses</a>
  <a href="results_explorer.html" class="active results">Results</a>
</nav>
<div class="wrap">
  <h1>Results</h1>
  <p class="lead">One bilateral VTA→hippocampus pathway, neurite density. Three social memory effects, every monetary counterpart null. The reported model comes first; everything that was run follows.</p>
  <p class="small">n = 52 social, 53 monetary. Covariates throughout: ICV, tract length, streamline count, absolute motion, maternal age. * p &lt; .05.</p>

  <h2>Whole tract, both subregions in one model</h2>
  <p>NDI averaged over all 100 nodes, one value per subject per subregion, two rows per subject (anterior, posterior). NDI regressed on memory, subregion and the covariates with a random intercept for subject; each row carries its own tract length and streamline count. Maximum likelihood. The interaction (memory × subregion) is tested by likelihood ratio and dropped when it does not improve fit.</p>
  {whole_table()}
  <p>The interaction is droppable for every outcome, so there is no evidence the two hippocampal subregions relate to memory differently. All three social effects hold with it dropped; the monetary counterparts are null and monetary misattribution runs in the opposite direction.</p>

  <h2>Quartiles</h2>
  <p>The same model with NDI averaged within each quarter of the tract. Q1 is nodes 0 to 24 at the VTA end, Q4 is 75 to 99 at the hippocampus. Whole repeats the model above.</p>
  <h3>Interaction p</h3>{quart_table('interaction_p')}
  <h3>Main-effect p, interaction dropped</h3>{quart_table('main_p')}
  <p>Positive false-alarm bias is significant in all four segments and the interaction is droppable in all four, so that effect is uniform along the tract. d′ and misattribution hold on the whole-tract average but not segment by segment. Contrasting Q1 against Q4 is null for all three social outcomes (difference p = .44, .45, .95) while the mean carries the effect: the signal is diffuse rather than focal.</p>

  <h2>Metric comparison</h2>
  <p>Same whole-tract model, each microstructure metric in turn.</p>
  {metric_table()}
  <p>NDI is the only metric carrying all three social effects with every monetary outcome null. FA tracks it and is the supplement for traditional-DTI readers. FWF adds only the bias effect plus a control-domain hit, and is dropped. ODI's bias effect runs in the same direction as NDI rather than opposite, which is atypical for the pair.</p>

  <h2>Node-wise</h2>
  <p>Every node-wise permutation test that was run: {n_all} analyses over the two bilateral tracts ({n_sig} FWE-significant). Each row is one outcome × tract × metric. At each of the 100 nodes the outcome is regressed on that node's metric plus the covariates; contiguous nodes with p &lt; .05 form a cluster; a cluster survives if its extent exceeds the 95th percentile of the maximum cluster under 5000 Freedman–Lane permutations. Click a row for the profile along the tract. Because the effect is diffuse, this view is descriptive; the whole-tract model above is the inferential unit.</p>
  <div class="controls">
    <span><label>Show</label><select id="f_show"><option value="rep">Reported outcomes</option><option value="sig">FWE-significant</option><option value="all">All measures</option></select></span>
    <span><label>Condition</label><select id="f_cond"></select></span>
    <span><label>Tract</label><select id="f_tract"></select></span>
    <span><label>Metric</label><select id="f_metric"></select></span>
    <span><label>Family</label><select id="f_family"></select></span>
    <input id="f_search" placeholder="search" style="min-width:120px">
    <span class="count" id="count"></span>
  </div>
  <table id="tbl" class="dtable"><thead><tr>
    <th data-k="outcome_label">Outcome</th><th data-k="condition">Condition</th><th data-k="tract_label">Tract</th><th data-k="metric">Metric</th>
    <th data-k="N">n</th><th data-k="n_sig_nodes">Sig nodes</th><th data-k="obs_max_cluster">Max cluster</th><th data-k="extent_threshold">Threshold</th>
    <th data-k="best_p">Cluster p</th><th data-k="passed">FWE</th>
  </tr></thead><tbody id="tbody"></tbody></table>

  <h2>Hippocampal gray-matter NDI</h2>
  <p>Bilateral hippocampal NDI from a NODDI refit at the gray-matter parallel diffusivity (1.1e-3 mm²/s), regressed on each outcome with ICV, hippocampal volume, motion and maternal age. Standardized β. Hippocampal volume on its own predicts none of them. <a href="hpc_region_vs_connection.html">Detail</a>.</p>
  {hpc_table()}

  <h2>HVLT</h2>
  <p>Collapsed whole-tract NDI with each subregion's streamline count entered separately. HVLT trial 1 and RAFT social d′ correlate at −.05, so this is a separate finding, not convergent validation of the RAFT. <a href="hvlt_explorer.html">Detail</a>.</p>
  {hvlt_table()}
</div>

<script>
const DATA=__DATA__;
function uniq(k){{return [...new Set(DATA.map(r=>r[k]))].sort()}}
function fill(id,vals,label){{const s=document.getElementById(id);s.innerHTML=`<option value="">${{label}}</option>`+vals.map(v=>`<option>${{v}}</option>`).join('')}}
fill('f_cond',uniq('condition'),'Both');fill('f_tract',uniq('tract_label'),'Both tracts');fill('f_metric',uniq('metric'),'All');fill('f_family',uniq('family'),'All families');
let sortK='best_p',sortDir=1;
document.querySelectorAll('#tbl th').forEach(th=>th.onclick=()=>{{const k=th.dataset.k;if(sortK===k)sortDir*=-1;else{{sortK=k;sortDir=1}}render()}});
function pass(r){{
 const sh=f_show.value,c=f_cond.value,t=f_tract.value,m=f_metric.value,f=f_family.value,q=f_search.value.toLowerCase();
 if(sh==='rep'&&!r.reported)return false; if(sh==='sig'&&!r.passed)return false;
 if(c&&r.condition!==c)return false; if(t&&r.tract_label!==t)return false; if(m&&r.metric!==m)return false; if(f&&r.family!==f)return false;
 if(q&&!(r.outcome_label+' '+r.tract_label+' '+r.metric+' '+r.family+' '+r.outcome).toLowerCase().includes(q))return false;
 return true;}}
['f_show','f_cond','f_tract','f_metric','f_family','f_search'].forEach(id=>document.getElementById(id).oninput=render);
function fmtP(p){{return p==null?'—':(p===0?'&lt;.0002':String(p).replace(/^0\\./,'.'))}}
function dirBadge(d){{return d==='Positive'?'<span class="badge b-pos">positive</span>':'<span class="badge b-neg">negative</span>'}}
function viz(r){{
 const W=600,H=96,pad=18,n=100,ts=r.tvals.map(x=>x==null?0:x),mx=Math.max(3,...ts.map(Math.abs)),bw=(W-2*pad)/n;
 let shade='';r.clusters.forEach(c=>{{if(c.passes)shade+=`<rect x="${{pad+c.start*bw}}" y="4" width="${{(c.end-c.start+1)*bw}}" height="${{H-8}}" fill="rgba(58,106,95,.13)" stroke="rgba(58,106,95,.45)"/>`}});
 let bars='';for(let i=0;i<n;i++){{const t=ts[i],sig=r.pvals[i]!=null&&r.pvals[i]<0.05,h=Math.abs(t)/mx*(H/2-8),y=t>=0?(H/2-h):(H/2);
  const col=sig?(t>=0?'#3a6a5f':'#a8553f'):'#d9d4c9';bars+=`<rect x="${{pad+i*bw}}" y="${{y}}" width="${{Math.max(bw-0.4,0.6)}}" height="${{h}}" fill="${{col}}"><title>node ${{i}}: t = ${{t}}</title></rect>`}}
 return `<svg viewBox="0 0 ${{W}} ${{H}}" width="100%" style="max-width:${{W}}px">${{shade}}<line x1="${{pad}}" y1="${{H/2}}" x2="${{W-pad}}" y2="${{H/2}}" stroke="#b8b2a6"/>${{bars}}
  <text x="${{pad}}" y="${{H-2}}" fill="#767066" font-size="9">VTA (node 0)</text><text x="${{W-pad}}" y="${{H-2}}" fill="#767066" font-size="9" text-anchor="end">hippocampus (node 99)</text></svg>`}}
function detail(r){{
 const cl=r.clusters.length?'<table class="dtable" style="width:auto"><thead><tr><th>Nodes</th><th>Size</th><th>Direction</th><th>Mean t</th><th>Cluster p</th><th>FWE</th></tr></thead><tbody>'+
  r.clusters.map(c=>`<tr><td>${{c.start}}–${{c.end}}</td><td>${{c.size}}</td><td>${{dirBadge(c.dir)}}</td><td>${{c.mean_t}}</td><td>${{fmtP(c.p)}}</td><td>${{c.passes?'<span class="badge b-sig">yes</span>':'<span class="badge b-ns">no</span>'}}</td></tr>`).join('')+'</tbody></table>':'<span class="tag">No contiguous clusters formed.</span>';
 return `<td colspan="10"><div class="dbox"><div class="dgrid"><div>
  <h4>${{r.outcome_label}} · ${{r.tract_label}} · ${{r.metric}}</h4>
  <div class="kv2"><div class="k">Family</div><div>${{r.family}}</div><div class="k">Condition</div><div>${{r.condition}}</div>
  <div class="k">n</div><div>${{r.N}} <span class="tag">(${{r.dropped}} dropped)</span></div><div class="k">Permutations</div><div>${{r.n_perms}}, Freedman–Lane</div>
  <div class="k">Nodes with p &lt; .05</div><div>${{r.n_sig_nodes}} / 100</div><div class="k">Largest cluster</div><div>${{r.obs_max_cluster}} nodes</div>
  <div class="k">Extent threshold</div><div>${{r.extent_threshold}} nodes (95th percentile of null max)</div>
  <div class="k">Verdict</div><div>${{r.passed?'<span class="badge b-sig">FWE-significant</span> cluster p = '+fmtP(r.best_p):'<span class="badge b-ns">not significant</span>'}}</div>
  <div class="k">Covariates</div><div class="tag">${{r.covariates}}</div></div>
  <h4 style="margin-top:14px">Clusters</h4>${{cl}}
  <h4 style="margin-top:12px">Command</h4><div class="tag mono">Rscript permutation_one.R &lt;csv&gt; ${{r.outcome}} ${{r.metric}}_ &lt;out&gt; ${{r.id}}</div>
  </div><div><h4>t along the tract <span class="tag">(one regression per node; green positive, brown negative, shaded = FWE cluster)</span></h4><div class="viz">${{viz(r)}}</div>
  <h4 style="margin-top:12px">Nodes with p &lt; .05</h4><div class="tag" style="line-height:1.6">${{r.sig_node_list.length?r.sig_node_list.join(', '):'none'}}</div></div></div></div></td>`}}
function render(){{
 let rows=DATA.filter(pass);
 rows.sort((a,b)=>{{let x=a[sortK],y=b[sortK];if(sortK==='best_p'){{x=x==null?9:x;y=y==null?9:y}}if(typeof x==='string')return sortDir*x.localeCompare(y);return sortDir*((x>y)-(x<y))}});
 const tb=document.getElementById('tbody');tb.innerHTML='';
 rows.forEach(r=>{{const tr=document.createElement('tr');tr.className='row'+(r.reported?' rep':'');const d=r.clusters.find(c=>c.passes);
  tr.innerHTML=`<td>${{r.outcome_label}}</td><td>${{r.condition==='SOCIAL'?'Social':'Monetary'}}</td><td>${{r.tract_label}}</td><td>${{r.metric}}</td><td>${{r.N}}</td><td>${{r.n_sig_nodes}}</td><td>${{r.obs_max_cluster}}</td><td>${{r.extent_threshold}}</td>
   <td>${{r.best_p!=null?'<span class="sig">'+fmtP(r.best_p)+'</span> '+dirBadge(d.dir):'<span class="tag">—</span>'}}</td><td>${{r.passed?'<span class="badge b-sig">yes</span>':'<span class="badge b-ns">no</span>'}}</td>`;
  tr.onclick=()=>{{const nx=tr.nextSibling;if(nx&&nx.classList&&nx.classList.contains('detail-row')){{nx.remove();return}}document.querySelectorAll('.detail-row').forEach(e=>e.remove());const dr=document.createElement('tr');dr.className='detail-row';dr.innerHTML=detail(r);tr.after(dr)}};
  tb.appendChild(tr)}});
 document.getElementById('count').textContent=`${{rows.length}} of ${{DATA.length}} · ${{rows.filter(r=>r.passed).length}} FWE-significant`}}
render();
</script></body></html>'''
HTML = HTML.replace('__DATA__', json.dumps(DATA))
open(f'{OUT}/results_explorer.html', 'w').write(HTML)
print(f'wrote results_explorer.html ({len(HTML)//1024} KB): {n_all} analyses, {n_rep} reported, {n_sig} significant')
