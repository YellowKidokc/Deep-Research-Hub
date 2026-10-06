"""API_DEEP.html: one self-contained page per paper, in the house visual language of the approved Paper Information
Matrix (IBM Plex, diverging blue = toward the fruit / red = away / grey = neutral, circles, dark mode).
The page carries its own data as JSON and draws every chart as inline SVG; nothing is fetched except fonts."""
from __future__ import annotations
import html, json

FRUITS = ["love", "joy", "peace", "patience", "kindness", "goodness", "faithfulness", "gentleness", "self_control"]


def build(ctx: dict, R: dict, rows: list[dict]) -> str:
    sentences = [{"id": r["id"], "p": r["para"], "t": r["text"], "v": r["v"], "w": r["why"] or {},
                  "x": {k: v for k, v in (r.get("lexicon") or {}).items() if v}} for r in rows]
    calls = [{"name": c["name"], "tokens": c["tokens"], "error": c["error"], "reused": bool(c.get("reused"))} for c in ctx["calls"]]
    data = {"title": ctx["title"], "source": ctx["path"].name, "sha": ctx["source_sha"][:16], "model": f"{ctx['provider']}/{ctx['model']}",
            "finished": ctx["finished"][:19].replace("T", " "), "sentences": sentences, "calls": calls, **{k: R.get(k) for k in
            ("fruits", "fruits_sentences_summary", "axiom_nodes", "atoms", "lean4", "stories", "master_equation", "master_equation_b", "coherence", "love_truth")}}
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return PAGE.replace("__TITLE__", html.escape(ctx["title"][:80])).replace("__DATA__", payload)


PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__ · API Deep</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Sans+Condensed:wght@500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{--plane:#f5f5f2;--surface:#fcfcfb;--ink:#0b0b0b;--muted:#6f6d67;--grid:#e1e0d9;--axis:#c3c2b7;--border:rgba(11,11,11,.10);--mid:#e4e3de;
--g1:#86b6ef;--g2:#2a78d6;--g3:#104281;--b1:#f0a39d;--b2:#e34948;--b3:#a8292a;--good:#0ca30c;--warn:#c98500;--crit:#d03b3b;
--sans:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;--cond:"IBM Plex Sans Condensed","IBM Plex Sans",system-ui,sans-serif;--mono:"IBM Plex Mono",ui-monospace,Consolas,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--plane:#0f0f0e;--surface:#1a1a19;--ink:#fff;--muted:#9a988f;--grid:#2c2c2a;--axis:#383835;--border:rgba(255,255,255,.10);--mid:#383835;
--g1:#1c5cab;--g2:#3987e5;--g3:#9ec5f4;--b1:#7d2a28;--b2:#e66767;--b3:#f4aaa6}}
:root[data-theme="dark"]{--plane:#0f0f0e;--surface:#1a1a19;--ink:#fff;--muted:#9a988f;--grid:#2c2c2a;--axis:#383835;--border:rgba(255,255,255,.10);--mid:#383835;
--g1:#1c5cab;--g2:#3987e5;--g3:#9ec5f4;--b1:#7d2a28;--b2:#e66767;--b3:#f4aaa6}
*{box-sizing:border-box}body{margin:0;background:var(--plane);color:var(--ink);font:14px/1.5 var(--sans)}
.wrap{max-width:1180px;margin:0 auto;padding:24px 16px 64px}
header h1{font:600 26px/1.2 var(--sans);margin:0 0 4px}.meta{color:var(--muted);font:12px var(--mono);word-break:break-all}
.note{color:var(--muted);font-size:12px;margin:6px 0 0}
.strip{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:8px;margin:18px 0}
.kpi{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:10px 12px}
.kpi b{display:block;font:600 20px/1.2 var(--cond)}.kpi span{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.04em}
section{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:18px;margin:16px 0}
h2{font:600 18px/1.3 var(--sans);margin:0 0 4px}h2 small{color:var(--muted);font-weight:400;font-size:13px;margin-left:6px}
h3{font:600 14px var(--sans);margin:16px 0 6px}.sub{color:var(--muted);font-size:12.5px;margin:0 0 12px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}@media (max-width:760px){.grid2{grid-template-columns:1fr}}
svg{display:block;width:100%;height:auto;overflow:visible}svg text{fill:var(--ink);font-family:var(--sans)}.mut{fill:var(--muted)}
.tbl{width:100%;border-collapse:collapse;font-size:12.5px}.tbl th{text-align:left;color:var(--muted);font-weight:500;border-bottom:1px solid var(--axis);padding:6px 8px;white-space:nowrap}
.tbl td{border-bottom:1px solid var(--grid);padding:6px 8px;vertical-align:top}.scroll{overflow-x:auto}
.pill{display:inline-block;border-radius:99px;padding:1px 8px;font-size:11.5px;border:1px solid var(--border);white-space:nowrap}
.pos{background:color-mix(in srgb,var(--g2) 16%,transparent)}.neg{background:color-mix(in srgb,var(--b2) 16%,transparent)}.neu{background:var(--mid)}
ul.q{margin:0;padding-left:18px}ul.q li{margin:4px 0}.id{font:12px var(--mono);color:var(--muted)}
#tip{position:fixed;pointer-events:none;background:var(--surface);border:1px solid var(--border);box-shadow:0 6px 20px rgba(0,0,0,.18);border-radius:8px;padding:8px 10px;font-size:12px;max-width:360px;display:none;z-index:9}
#tip .t1{font-weight:600}input.search{width:100%;max-width:360px;padding:7px 10px;border:1px solid var(--axis);border-radius:6px;background:var(--plane);color:var(--ink);font:13px var(--sans);margin:0 0 10px}
.cell{display:inline-block;width:16px;height:16px;border-radius:3px;text-align:center;font:10px/16px var(--mono)}
.theme{float:right;background:none;border:1px solid var(--axis);color:var(--ink);border-radius:6px;padding:3px 9px;cursor:pointer;font:12px var(--sans)}
nav.toc{display:flex;flex-wrap:wrap;gap:6px;margin:4px 0 0}nav.toc a{color:var(--ink);text-decoration:none;font-size:12.5px;border:1px solid var(--border);border-radius:99px;padding:2px 10px}
.bar{height:8px;border-radius:4px;background:var(--mid);position:relative}.bar i{position:absolute;left:0;top:0;bottom:0;border-radius:4px;background:var(--g2)}
</style></head><body><div class="wrap" id="app"></div><div id="tip"></div>
<script>
var D=__DATA__;
var FR=["love","joy","peace","patience","kindness","goodness","faithfulness","gentleness","self_control"];
function css(v){return getComputedStyle(document.documentElement).getPropertyValue(v).trim();}
function esc(s){return String(s==null?"":s).replace(/[&<>"]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c];});}
function nm(f){return f.replace("_"," ");}
function div(v){return v<=-2?css("--b3"):v===-1?css("--b1"):v===0||v==null?css("--mid"):v===1?css("--g1"):css("--g3");}
function el(t,a,p){var e=document.createElementNS("http://www.w3.org/2000/svg",t);for(var k in a)e.setAttribute(k,a[k]);if(p)p.appendChild(e);return e;}
function tx(s,x,y,t,a){var e=el("text",Object.assign({x:x,y:y,"font-size":11},a||{}),s);e.textContent=t;return e;}
var tip=document.getElementById("tip");
function showTip(e,h){tip.innerHTML=h;tip.style.display="block";var x=e.clientX+14,y=e.clientY+14;if(x+370>innerWidth)x=e.clientX-370;if(y+tip.offsetHeight>innerHeight)y=e.clientY-tip.offsetHeight-10;tip.style.left=Math.max(4,x)+"px";tip.style.top=Math.max(4,y)+"px";}
function hover(n,h){n.addEventListener("mousemove",function(e){showTip(e,typeof h==="function"?h(e):h);});n.addEventListener("mouseleave",function(){tip.style.display="none";});}
function sentTip(s){return '<div class="t1">'+s.id+' · '+s.p+'</div><div>'+esc(s.t.slice(0,260))+'</div>'+(s.v?'<div style="margin-top:4px">'+FR.map(function(f,j){return s.v[j]?nm(f)+' '+(s.v[j]>0?'+':'')+s.v[j]:'';}).filter(Boolean).join(' · ')+'</div>':'')+
 (Object.keys(s.w).length?'<div style="margin-top:4px;color:var(--muted)">'+Object.keys(s.w).map(function(k){return esc(k+': '+s.w[k]);}).join('<br>')+'</div>':'')+
 (Object.keys(s.x).length?'<div style="margin-top:4px;font-family:var(--mono);font-size:11px">'+Object.keys(s.x).map(function(k){return esc(k.replace('_',' ')+': '+s.x[k].join(', '));}).join('<br>')+'</div>':'');}
var app=document.getElementById("app"), LT=D.love_truth||{}, PR=LT.profile||{}, TE=LT.truth_engine||{}, SS=D.fruits_sentences_summary||{};
function sec(id,title,small,sub){var s=document.createElement("section");s.id=id;s.innerHTML='<h2>'+title+(small?'<small>'+small+'</small>':'')+'</h2>'+(sub?'<p class="sub">'+sub+'</p>':'');app.appendChild(s);return s;}
function svgIn(node,w,h){var s=el("svg",{viewBox:"0 0 "+w+" "+h});node.appendChild(s);return s;}
function table(node,head,rows){var d=document.createElement("div");d.className="scroll";d.innerHTML='<table class="tbl"><thead><tr>'+head.map(function(h){return '<th>'+h+'</th>';}).join('')+'</tr></thead><tbody>'+rows.map(function(r){return '<tr>'+r.map(function(c){return '<td>'+c+'</td>';}).join('')+'</tr>';}).join('')+'</tbody></table>';node.appendChild(d);return d;}

/* header + headline strip */
var co=((D.coherence||{}).overall||{}), me=D.master_equation||{}, shape=(PR.shapes_matched||[]).map(function(x){return x.name;}).join(" / ")||"no clear shape";
app.innerHTML='<header><button class="theme" onclick="var r=document.documentElement;r.dataset.theme=(r.dataset.theme===\'dark\'||(!r.dataset.theme&&matchMedia(\'(prefers-color-scheme: dark)\').matches))?\'light\':\'dark\';render()">Theme</button><h1>'+esc(D.title)+'</h1><div class="meta">'+esc(D.source)+' · sha256 '+D.sha+'… · '+esc(D.model)+' · '+D.finished+' UTC</div>'+
 '<p class="note">Every result on this page is an AI proposal pending David\'s review. Word hits are a trace, never character evidence.</p>'+
 '<nav class="toc">'+[["lt","Love and Truth"],["fr","Fruits"],["ax","Axioms"],["at","Atoms"],["le","Lean"],["st","Stories"],["me","Master equation"],["co","Coherence"],["ss","Sentences"],["au","Audit"]].map(function(x){return '<a href="#'+x[0]+'">'+x[1]+'</a>';}).join('')+'</nav></header>';
var strip=document.createElement("div");strip.className="strip";
[[PR.quadrant||"—","Love × Truth"],[shape,"Character shape"],[PR.love_axis!=null?PR.love_axis.toFixed(2):"—","Love axis"],[PR.truth_axis!=null?PR.truth_axis.toFixed(2):"—","Truth axis"],
 [TE.truth_score_raw!=null?TE.truth_score_raw:"—","Truth Engine score"],[co.score!=null?co.score+"/10":"—","Coherence"],[me.analog_strength!=null?me.analog_strength+" ("+me.analog_strength_spread+")":"—","Master eq. analog"],
 [((D.atoms||{}).atoms||[]).length,"Atoms"],[((D.axiom_nodes||{}).axiom_nodes||[]).length,"Axiom nodes"],[D.sentences.length,"Sentences"],[((D.fruits||{}).system_status)||"—","Fruits verdict"],
 [D.calls.reduce(function(a,c){return a+(c.reused?0:c.tokens);},0).toLocaleString(),"New tokens"]].forEach(function(k){var d=document.createElement("div");d.className="kpi";d.innerHTML='<b>'+esc(k[0])+'</b><span>'+k[1]+'</span>';strip.appendChild(d);});
app.appendChild(strip);

var charts=[];
function render(){charts.forEach(function(f){f();});var q=document.getElementById("q");if(q)sentRows(q.value);}

/* 1 LOVE AND TRUTH */
var s1=sec("lt","1 · Fruits of Love and Truth",PR.sentences?"scored from "+PR.sentences+" "+(PR.unit||"sentences")+(PR.unit==="turns"?" (speaker turns)":""):"",(PR.unit==="turns"?"Spoken transcript: each speaker turn is scored as a whole answer (net points per 100 turns). ":"")+"Love axis from the nine fruits; truth axis from the Truth Engine lexicon, coherence and the truth gate. Cut at 0.5.");
var g1=document.createElement("div");g1.className="grid2";s1.appendChild(g1);
var qa=document.createElement("div"),na=document.createElement("div");g1.appendChild(qa);g1.appendChild(na);
charts.push(function(){qa.innerHTML='<h3>Love × Truth</h3>';var s=svgIn(qa,320,300),X=40,Y=10,W=260,H=250;
 [["Grace and Truth",1,0],["Sentimentalist",1,1],["Clanging Cymbal",0,0],["Propagandist",0,1]].forEach(function(q){el("rect",{x:X+q[1]*W/2,y:Y+q[2]*H/2,width:W/2,height:H/2,fill:q[1]&&!q[2]?css("--g1"):!q[1]&&q[2]?css("--b1"):css("--mid"),"fill-opacity":.35,stroke:css("--surface")},s);tx(s,X+q[1]*W/2+8,Y+q[2]*H/2+16,q[0],{"font-size":10.5,"class":"mut"});});
 tx(s,X+W/2,Y+H+30,"love →",{"text-anchor":"middle","class":"mut"});var t=tx(s,14,Y+H/2,"truth →",{"text-anchor":"middle","class":"mut",transform:"rotate(-90 14 "+(Y+H/2)+")"});
 [0,.5,1].forEach(function(v){tx(s,X+v*W,Y+H+14,v,{"text-anchor":"middle","font-size":9,"class":"mut"});tx(s,X-6,Y+H-v*H+3,v,{"text-anchor":"end","font-size":9,"class":"mut"});});
 if(PR.love_axis!=null){var cx=X+PR.love_axis*W,cy=Y+H-PR.truth_axis*H;var c=el("circle",{cx:cx,cy:cy,r:9,fill:css("--g2"),stroke:css("--surface"),"stroke-width":3},s);
  hover(c,'<div class="t1">'+esc(PR.quadrant)+'</div>love '+PR.love_axis+' · truth '+PR.truth_axis+'<br>'+Object.keys(PR.truth_parts||{}).map(function(k){return k+' '+(+PR.truth_parts[k]).toFixed(2);}).join(' · '));}
});
charts.push(function(){na.innerHTML='<h3>Net points per 100 '+(PR.unit||'sentences')+'</h3>';var net=PR.net_per_100||{},act=PR.active_sentences||{};var s=svgIn(na,340,9*26+24),mx=Math.max(10,Math.max.apply(null,FR.map(function(f){return Math.abs(net[f]||0);})));
 var X0=110,W=210,zero=X0+W/2;el("line",{x1:zero,y1:0,x2:zero,y2:9*26,stroke:css("--axis")},s);
 FR.forEach(function(f,i){var v=net[f]||0,y=i*26+13,x=zero+v/mx*W/2;tx(s,X0-8,y+4,nm(f),{"text-anchor":"end"});el("line",{x1:zero,y1:y,x2:x,y2:y,stroke:v>=0?css("--g2"):css("--b2"),"stroke-width":2},s);
  var c=el("circle",{cx:x,cy:y,r:Math.max(4,Math.min(10,3+Math.sqrt(act[f]||0)*1.6)),fill:v>=0?css("--g2"):css("--b2"),stroke:css("--surface"),"stroke-width":2},s);
  hover(c,'<div class="t1">'+nm(f)+'</div>'+(v>0?'+':'')+v+' net per 100 sentences<br>'+(act[f]||0)+' sentences engage it');});
 tx(s,zero,9*26+16,"0",{"text-anchor":"middle","class":"mut","font-size":9});tx(s,X0+W,9*26+16,"+"+Math.round(mx),{"text-anchor":"end","class":"mut","font-size":9});tx(s,X0,9*26+16,"−"+Math.round(mx),{"class":"mut","font-size":9});
});
var lt2=document.createElement("div");s1.appendChild(lt2);
lt2.innerHTML='<h3>Character shape</h3><p>'+((PR.shapes_matched||[]).length?PR.shapes_matched.map(function(x){return '<span class="pill pos">'+esc(x.name)+'</span> gap '+x.gap+' (high: '+x.high.map(nm).join(', ')+(x.low.length?'; low: '+x.low.map(nm).join(', '):'')+')';}).join('<br>'):'No shape reaches the threshold. Closest: '+esc(((PR.shapes_ranked||[])[0]||{}).name)+' (gap '+(((PR.shapes_ranked||[])[0]||{}).gap)+').')+
 (PR.levels&&PR.levels.length?'<br>Level: '+PR.levels.map(function(l){return '<span class="pill neu">'+esc(l)+'</span>';}).join(' '):'')+'</p>'+
 '<p class="sub">Paper verdict (rubric 0–4) as a second opinion: '+esc(((LT.verdict_profile||{}).quadrant)||'—')+'. Workbook characterizations: '+(((LT.characterizations||[]).map(function(c){return esc(c.name);}).join(', '))||'none triggered')+'.</p>'+
 '<h3>Truth Engine v2.0 (lexicon)</h3><p class="sub">TRUTH '+TE.truth_score_raw+' → '+TE.truth_score_0_1+' over '+TE.words+' words. Per 100 words: '+Object.keys(TE.per_100_words||{}).map(function(k){return nm(k)+' '+TE.per_100_words[k];}).join(' · ')+'</p>'+
 '<p class="sub">Top words — '+Object.keys(TE.top_words||{}).filter(function(k){return Object.keys(TE.top_words[k]).length;}).map(function(k){return '<b>'+nm(k)+'</b>: '+esc(Object.keys(TE.top_words[k]).slice(0,6).join(', '));}).join(' · ')+'</p>';

/* 2 FRUITS: heat strip, paragraph love, spikes, verdict */
var s2=sec("fr","2 · Fruits of the Spirit",SS.scored+"/"+SS.total+" sentences scored","Every sentence is a column. Blue moves toward the fruit, red moves away, grey is neutral. Hover for the sentence, the reason and the trigger words.");
var hs=document.createElement("div");s2.appendChild(hs);
charts.push(function(){hs.innerHTML='';var n=D.sentences.length,W=1000,cw=W/n,rh=15;var s=svgIn(hs,W+80,9*rh+24);
 FR.forEach(function(f,j){tx(s,74,j*rh+11,nm(f),{"text-anchor":"end","font-size":10});});
 D.sentences.forEach(function(r,i){for(var j=0;j<9;j++)el("rect",{x:80+i*cw,y:j*rh,width:cw+.1,height:rh-2,fill:r.v?div(r.v[j]):css("--grid")},s);});
 var hit=el("rect",{x:80,y:0,width:W,height:9*rh,fill:"transparent"},s);hover(hit,function(e){var b=hit.getBoundingClientRect();var i=Math.max(0,Math.min(n-1,Math.floor((e.clientX-b.left)/b.width*n)));return sentTip(D.sentences[i]);});
 var step=Math.max(1,Math.round(n/6));for(var i=0;i<n;i+=step)tx(s,80+i*cw,9*rh+14,D.sentences[i].id,{"font-size":9,"class":"mut"});
});
var pl=document.createElement("div");s2.appendChild(pl);
charts.push(function(){var P=SS.paragraph_love||{},T=SS.paragraph_total||{},ks=Object.keys(P);pl.innerHTML='<h3>Love by paragraph <small class="id">bar = mean love, dot = mean of all nine</small></h3>';if(!ks.length)return;
 var W=1000,bw=W/ks.length,H=90,mid=H/2;var s=svgIn(pl,W+40,H+18);el("line",{x1:30,y1:mid,x2:30+W,y2:mid,stroke:css("--axis")},s);
 tx(s,26,8,"+2",{"text-anchor":"end","font-size":9,"class":"mut"});tx(s,26,H,"−2",{"text-anchor":"end","font-size":9,"class":"mut"});
 ks.forEach(function(k,i){var v=P[k],h=v/2*mid,x=30+i*bw;var r=el("rect",{x:x+1,y:v>=0?mid-h:mid,width:Math.max(1,bw-2),height:Math.max(1,Math.abs(h)),fill:v>=0?css("--g2"):css("--b2"),rx:1.5},s);
  el("circle",{cx:x+bw/2,cy:mid-(T[k]||0)/2*mid/4,r:1.8,fill:css("--ink"),"fill-opacity":.5},s);hover(r,'<div class="t1">'+k+'</div>love '+v+' · all nine '+(T[k]||0));});
});
var sp=document.createElement("div");sp.className="grid2";s2.appendChild(sp);
function spikeList(t,a,cls){return '<div><h3>'+t+'</h3>'+((a||[]).length?'<ul class="q">'+a.map(function(x){return '<li><span class="pill '+cls+'">'+(x.sum>0?'+':'')+x.sum+'</span> <span class="id">'+x.id+'</span> “'+esc(x.text)+'”'+(Object.keys(x.why||{}).length?'<br><span class="id">'+esc(Object.keys(x.why).map(function(k){return k+': '+x.why[k];}).join('; '))+'</span>':'')+'</li>';}).join('')+'</ul>':'<p class="sub">None.</p>')+'</div>';}
sp.innerHTML=spikeList("Strongest toward the fruits",SS.top_toward,"pos")+spikeList("Strongest away",SS.top_away,"neg")+spikeList("Counterfeit candidates (fruit words, anti-fruit work)",SS.counterfeit_candidates,"neg")+spikeList("Hidden fruit (fruit work, no fruit words)",SS.hidden_fruit,"pos");
var FV=D.fruits||{};if(FV.fruit_profile){var vd=document.createElement("div");s2.appendChild(vd);
 vd.innerHTML='<h3>Paper verdict, rubric v0.3.0 <small class="id">'+esc(FV.epistemic_status)+' · '+esc(FV.system_status)+' · confidence '+FV.confidence+'</small></h3>';
 table(vd,["Fruit","Score 0–4","Confidence","Counterfeit","Rationale"],FV.fruit_profile.map(function(p){return [nm(p.fruit_id.split(".").pop()),'<b>'+p.score+'</b>',p.confidence,(p.counterfeit||{}).flag?'<span class="pill neg">yes</span>':'no',esc(p.rationale)];}));
 table(vd,["Gate","Status","Hard","Rationale"],(FV.gate_results||[]).map(function(g){return [esc(g.gate_id),'<span class="pill '+(g.status==="PASS"?"pos":g.status==="FAIL"?"neg":"neu")+'">'+g.status+'</span>',g.hard?"hard":"",esc(g.rationale)];}));
 if((FV.repair_path||[]).length)vd.insertAdjacentHTML("beforeend",'<h3>Repair path</h3><ul class="q">'+FV.repair_path.map(function(x){return '<li>'+esc(x)+'</li>';}).join('')+'</ul>');}

/* 3 AXIOMS */
var AX=D.axiom_nodes||{};var s3=sec("ax","3 · Axiom nodes",(AX.axiom_nodes||[]).length+" engaged · primary mode "+esc(AX.primary_mode||"—"),esc(AX.summary||""));
table(s3,["Node","Name","Mode","Alignment","Confidence","Quote"],(AX.axiom_nodes||[]).map(function(n){var a=n.alignment||"";return ['<span class="id">'+esc(n.node_id)+'</span>',esc(n.name),esc(n.mode),'<span class="pill '+(a==="contested"?"neg":a==="directly_asserted"||a==="supported"?"pos":"neu")+'">'+esc(a)+'</span>',esc(n.confidence),esc(n.evidence_quote)];}));
if((AX.unmapped_claims||[]).length)s3.insertAdjacentHTML("beforeend",'<p class="sub">Unmapped atoms: '+AX.unmapped_claims.map(esc).join(', ')+'</p>');

/* 4 ATOMS */
var AT=D.atoms||{};var s4=sec("at","4 · Atoms",(AT.atoms||[]).length+" · domain "+esc(AT.domainType||"—"),esc(AT.summary||""));
table(s4,["Id","Type","Stage","Name","Plain statement","Falsified if","Sentences"],(AT.atoms||[]).map(function(a){return ['<span class="id">'+a.atom_id+'</span>',esc(a.nodeType),esc(a.stage),'<b>'+esc(a.name)+'</b>',esc(a.statementPlain),esc(a.falsificationCondition),'<span class="id">'+esc((a.source_sentences||[]).slice(0,8).join(', '))+((a.source_sentences||[]).length>8?'…':'')+'</span>'];}));

/* 5 LEAN */
var LE=D.lean4||{};var s5=sec("le","5 · Lean 4 formalization candidates",(LE.formal_candidates||[]).length+" targets","The Lean corpus was not searched in this run; these are targets, not results.");
table(s5,["Claim","Disposition","Object","Proposed statement","What remains open"],(LE.formal_candidates||[]).map(function(c){return [esc((c.identity||{}).claim_id),esc((c.source_selection||{}).selection_disposition),esc((c.formal_object||{}).object_type),esc((c.formal_object||{}).exact_proposed_statement),esc((c.result_and_boundary||{}).what_remains_open)];}));

/* 6 STORIES */
var STo=D.stories||{},arc=STo.narrative_arc||{};var s6=sec("st","6 · Stories",(STo.stories||[]).length+" found",arc.opening_device?'Arc: <b>'+esc(arc.opening_device)+'</b> → <b>'+esc(arc.central_tension)+'</b> → <b>'+esc(arc.resolution_or_payoff)+'</b> · returns to opening: '+arc.return_to_opening:"");
table(s6,["Story","Type","Function","Span","Shows","Does not show","Load-bearing"],(STo.stories||[]).map(function(x){var b=x.boundaries||{};return ['<b>'+esc(x.title_or_label)+'</b>',esc(x.story_type),esc(x.intended_function),'<span class="id">'+esc(x.source_span)+'</span>',esc(b.what_it_shows),esc(b.what_it_does_not_show),x.is_separable_from_argument===false?'<span class="pill neg">yes</span>':'no'];}));

/* 7 MASTER EQUATION */
var pt=me.product_test||{},cr=me.core_relation||{};var s7=sec("me","7 · Master equation analog","strength "+(me.analog_strength!=null?me.analog_strength:"—")+" ("+(me.analog_strength_spread||"")+") · two independent runs",
 'χ = G·M·E·S<sub>eff</sub>·T·K·R·Q·F·C. Core relation: '+esc(cr.sentence||cr)+'<br>Product test: <b>'+esc(pt.run1)+'</b> / <b>'+esc(pt.run2)+'</b> ('+esc(pt.status)+') — '+esc(pt.reason));
var mdv=document.createElement("div");s7.appendChild(mdv);
charts.push(function(){mdv.innerHTML='';var sl=me.slots||[];if(!sl.length)return;var s=svgIn(mdv,10*64+10,110),fit={direct:1,analogous:.66,stretched:.33,absent:0};
 sl.forEach(function(r,i){var cx=36+i*64,v1=fit[r.fit_1],v2=fit[r.fit_2],v=((v1||0)+(v2||0))/2;
  var c=el("circle",{cx:cx,cy:44,r:6+v*18,fill:v>=.66?css("--g2"):v>=.33?css("--g1"):css("--mid"),stroke:r.status==="contested"?css("--b2"):"none","stroke-width":2.5,"stroke-dasharray":r.status==="contested"?"4 2":"none"},s);
  tx(s,cx,96,r.slot,{"text-anchor":"middle","font-weight":600});hover(c,'<div class="t1">'+r.slot+' · '+esc(r.fit_1)+' / '+esc(r.fit_2)+' ('+r.status+')</div>'+esc(r.plays_role)+'<br><span style="color:var(--muted)">'+esc(r.quote)+'</span>');});
});
s7.insertAdjacentHTML("beforeend",'<p class="sub">Circle size = fit (direct &gt; analogous &gt; stretched &gt; absent), averaged over both runs. Dashed red ring = the two runs disagree.</p>'+(me.one_line?'<p>“'+esc(me.one_line)+'”</p>':''));

/* 8 COHERENCE */
var s8=sec("co","8 · Coherence",co.score!=null?co.score+"/"+(co.score_ceiling||10):"",esc(co.summary||""));
(D.coherence&&D.coherence.dimensions||[]).forEach(function(d){s8.insertAdjacentHTML("beforeend",'<div style="margin:8px 0"><div style="display:flex;justify-content:space-between"><b>'+esc(nm(d.name||""))+'</b><span class="id">'+d.score+'/10</span></div><div class="bar"><i style="width:'+(d.score||0)*10+'%;background:'+((d.score||0)>=7?css("--g2"):(d.score||0)>=5?css("--g1"):css("--b2"))+'"></i></div><div class="sub" style="margin-top:4px">'+esc((d.reasons||[]).join(' · '))+'</div></div>');});
["contradictions","tensions","missing_definitions"].forEach(function(k){var a=(D.coherence||{})[k]||[];if(a.length)s8.insertAdjacentHTML("beforeend",'<h3>'+nm(k)+'</h3><ul class="q">'+a.map(function(x){return '<li>'+(typeof x==="object"?(x.term?'<b>'+esc(x.term)+'</b>: ':'')+esc(x.description||x.note||JSON.stringify(x))+(x.severity?' <span class="pill neu">'+esc(x.severity)+'</span>':''):esc(x))+'</li>';}).join('')+'</ul>');});

/* 9 ALL SENTENCES */
var s9=sec("ss","9 · Every sentence","searchable","Nine cells per sentence in fruit order (love … self-control). Type to filter by text, id or trigger word.");
s9.insertAdjacentHTML("beforeend",'<input class="search" id="q" placeholder="Filter sentences…">');var tb=document.createElement("div");s9.appendChild(tb);
function sentRows(f){f=(f||"").toLowerCase();var rs=D.sentences.filter(function(s){return !f||(s.id+" "+s.t+" "+JSON.stringify(s.x)+" "+JSON.stringify(s.w)).toLowerCase().indexOf(f)>=0;});
 tb.innerHTML='';table(tb,["Id","Fruits","Sentence","Why / trigger words"],rs.map(function(s){return ['<span class="id">'+s.id+'<br>'+s.p+'</span>','<span style="white-space:nowrap">'+FR.map(function(fr,j){var v=s.v?s.v[j]:null;return '<span class="cell" title="'+nm(fr)+' '+v+'" style="background:'+div(v)+';color:'+(Math.abs(v||0)===2?"#fff":"inherit")+'">'+(v?(v>0?'+':'−'):'')+'</span>';}).join('')+'</span>',esc(s.t),'<span class="id">'+esc(Object.keys(s.w).map(function(k){return k+': '+s.w[k];}).concat(Object.keys(s.x).map(function(k){return k.replace('_',' ')+': '+s.x[k].join(', ');})).join(' · '))+'</span>'];}));}
document.getElementById("q").addEventListener("input",function(e){sentRows(e.target.value);});

/* AUDIT */
var sa=sec("au","Audit","","Each call's tokens; reused = taken from an earlier run because its prompt had not changed.");
table(sa,["Call","Tokens","Status"],D.calls.map(function(c){return [esc(c.name),c.tokens.toLocaleString(),c.error?'<span class="pill neg">'+esc(c.error)+'</span>':c.reused?'<span class="pill neu">reused</span>':'<span class="pill pos">ok</span>'];}));

render();
matchMedia("(prefers-color-scheme: dark)").addEventListener("change",render);
</script></body></html>
"""
