"""build_index.py —— 从 knowledge.json 重建 index.html（让可视化随引擎同步）。"""
import json, os

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>海马体知识库 · Hippocampus Knowledge Base</title>
<style>
  :root {{
    --bg:#f4f7fb; --panel:#fff; --ink:#1f2733; --muted:#5b6573; --line:#e2e8f0;
    --ec:#2E7D32; --dg:#1565C0; --ca3:#6A1B9A; --ca1:#E65100; --sub:#00838F; --accent:#1565C0;
    --shadow:0 6px 24px rgba(20,40,80,.10);
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font-family:"Segoe UI","PingFang SC","Microsoft YaHei",system-ui,sans-serif; background:var(--bg); color:var(--ink); line-height:1.6; }}
  header {{ background:linear-gradient(120deg,#0d2b54,#1565C0); color:#fff; padding:22px 28px; box-shadow:var(--shadow); }}
  header h1 {{ margin:0; font-size:24px; letter-spacing:1px; }}
  header p {{ margin:6px 0 0; opacity:.85; font-size:13px; }}
  .wrap {{ display:grid; grid-template-columns:1.05fr 1fr; gap:18px; padding:18px; max-width:1320px; margin:0 auto; }}
  @media (max-width:920px){{ .wrap {{ grid-template-columns:1fr; }} }}
  .card {{ background:var(--panel); border:1px solid var(--line); border-radius:14px; box-shadow:var(--shadow); }}
  .viz {{ padding:10px; position:relative; }}
  .viz svg {{ width:100%; height:auto; display:block; }}
  .region {{ cursor:pointer; transition:transform .15s; }}
  .region:hover {{ transform:scale(1.06); }}
  .region circle.halo {{ opacity:.25; }}
  .region.active circle.core {{ stroke:#fff; stroke-width:3; }}
  .region text {{ font-size:13px; font-weight:700; fill:var(--ink); pointer-events:none; }}
  .legend {{ position:absolute; left:18px; bottom:14px; font-size:11px; color:var(--muted); background:rgba(255,255,255,.82); padding:6px 10px; border-radius:8px; }}
  .side {{ padding:18px 20px; display:flex; flex-direction:column; min-height:460px; }}
  .side h2 {{ margin:0 0 4px; font-size:18px; }}
  .side .role {{ color:var(--muted); font-size:12px; margin-bottom:12px; }}
  .item {{ border-left:4px solid var(--accent); background:#f8fafc; padding:10px 12px; border-radius:8px; margin-bottom:10px; }}
  .item h3 {{ margin:0 0 4px; font-size:14px; }}
  .item p {{ margin:0; font-size:13px; color:#33404f; }}
  .item a {{ font-size:11px; color:var(--accent); text-decoration:none; }}
  .item a:hover {{ text-decoration:underline; }}
  .hint {{ color:var(--muted); font-size:13px; }}
  .toolbar {{ display:flex; gap:10px; align-items:center; padding:0 18px 14px; max-width:1320px; margin:0 auto; }}
  .toolbar input {{ flex:1; padding:9px 12px; border:1px solid var(--line); border-radius:10px; font-size:14px; }}
  .chips {{ display:flex; flex-wrap:wrap; gap:8px; padding:0 18px 6px; max-width:1320px; margin:0 auto; }}
  .chip {{ border:1px solid var(--line); background:#fff; padding:5px 12px; border-radius:20px; font-size:12px; cursor:pointer; color:var(--muted); }}
  .chip:hover, .chip.active {{ color:#fff; border-color:transparent; }}
  .counts {{ font-size:12px; color:var(--muted); padding:0 18px 18px; max-width:1320px; margin:0 auto; }}
  footer {{ text-align:center; color:var(--muted); font-size:12px; padding:16px; }}
</style>
</head>
<body>
<header>
  <h1>🧠 海马体知识库 · Hippocampus Knowledge Base</h1>
  <p>以海马体神经环路为隐喻，组织全部记忆 / 文件 / 知识点 — 内嗅皮层(EC)→齿状回(DG)→CA3→CA1→下托(Subiculum)。本机中枢 + 线上乐享知识库互为备份。由记忆流引擎自动同步更新。</p>
</header>
<div class="chips" id="chips"></div>
<div class="toolbar"><input id="search" placeholder="🔍 全局搜索知识点（如：130988、Bartik、backdrop-filter、Warhammer…）" /></div>
<div class="wrap">
  <div class="card viz">
    <svg viewBox="0 0 680 560" id="hippo" aria-label="海马体神经环路">
      <defs>
        <linearGradient id="bodyGrad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stop-color="#1565C0" stop-opacity=".30"/>
          <stop offset="1" stop-color="#6A1B9A" stop-opacity=".30"/>
        </linearGradient>
        <filter id="glow"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
      </defs>
      <path d="M 190 130 C 360 95, 470 175, 425 285 C 392 362, 255 360, 268 448 C 280 518, 430 528, 495 472" fill="none" stroke="url(#bodyGrad)" stroke-width="46" stroke-linecap="round"/>
      <path d="M 190 130 C 360 95, 470 175, 425 285 C 392 362, 255 360, 268 448 C 280 518, 430 528, 495 472" fill="none" stroke="#fff" stroke-width="2" stroke-dasharray="2 8" opacity=".5"/>
      <g stroke="#9aa7b5" stroke-width="1.6" fill="none" stroke-dasharray="5 5" opacity=".7">
        <path d="M 214 150 C 320 130, 380 150, 430 196"/>
        <path d="M 412 240 C 360 320, 330 330, 300 360"/>
        <path d="M 282 392 C 276 410, 274 428, 270 446"/>
        <path d="M 300 470 C 380 500, 440 500, 478 482"/>
        <path d="M 470 452 C 360 430, 260 360, 214 150" opacity=".35"/>
      </g>
      <g id="nodes"></g>
    </svg>
    <div class="legend">点击任意脑区查看该层记忆 · 流向表示记忆的编码→巩固→导出通路</div>
  </div>
  <div class="card side" id="side">
    <h2 id="sideTitle">🧭 全部知识点</h2>
    <div class="role" id="sideRole"></div>
    <div id="sideBody"><p class="hint">从左侧海马体选择一个脑区，或使用顶部搜索框检索全部记忆与知识点。</p></div>
  </div>
</div>
<div class="counts" id="counts"></div>
<footer>海马体知识库 · 由记忆流引擎自动同步 · 数据源：<a href="knowledge.json">knowledge.json</a> + 本地 memory.db（L3）</footer>
<script>
const DATA = __DATA__;
const POS = {{
  ec:{{x:190,y:130,label:"EC 内嗅皮层"}}, dg:{{x:448,y:205,label:"DG 齿状回"}},
  ca3:{{x:300,y:372,label:"CA3"}}, ca1:{{x:270,y:452,label:"CA1"}},
  sub:{{x:492,y:478,label:"下托 Subiculum"}}, auto:{{x:430,y:300,label:"自动沉淀"}} }};
const COLORVAR = {{ ec:"var(--ec)",dg:"var(--dg)",ca3:"var(--ca3)",ca1:"var(--ca1)",sub:"var(--sub)",auto:"#37474F" }};
const ORDER = Object.keys(POS).filter(id=>DATA[id]);
const nodesG = document.getElementById("nodes");
function getColor(v){{ return v.startsWith("var(") ? getComputedStyle(document.documentElement).getPropertyValue(v.slice(4,-1)).trim() : v; }}
ORDER.forEach(id=>{{
  const p=POS[id], c=getColor(DATA[id]?DATA[id].color:COLORVAR[id]);
  const g=document.createElementNS("http://www.w3.org/2000/svg","g");
  g.setAttribute("class","region"); g.dataset.region=id;
  g.innerHTML=`<circle class="halo" cx="${{p.x}}" cy="${{p.y}}" r="30" fill="${{c}}"/><circle class="core" cx="${{p.x}}" cy="${{p.y}}" r="20" fill="${{c}}" filter="url(#glow)"/><text x="${{p.x}}" y="${{p.y-38}}" text-anchor="middle">${{p.label}}</text>`;
  g.addEventListener("click",()=>selectRegion(id));
  nodesG.appendChild(g);
}});
const sideTitle=document.getElementById("sideTitle"), sideRole=document.getElementById("sideRole"), sideBody=document.getElementById("sideBody"), chipsEl=document.getElementById("chips"), countsEl=document.getElementById("counts");
const allChip=mkChip("全部",null); chipsEl.appendChild(allChip);
ORDER.forEach(id=>{{ const c=mkChip(DATA[id].name.split(" ")[0],id); c.style.setProperty("--c",getColor(DATA[id].color)); chipsEl.appendChild(c); }});
function mkChip(text,region){{ const b=document.createElement("button"); b.className="chip"+(region===null?" active":""); b.textContent=text; b.onclick=()=>{{ setActiveChip(b); if(region===null) showAll(); else selectRegion(region,true); }}; return b; }}
function setActiveChip(el){{ document.querySelectorAll(".chip").forEach(c=>c.classList.remove("active")); el.classList.add("active"); const col=el.style.getPropertyValue("--c"); if(col) el.style.background=col; else el.style.background="var(--accent)"; }}
let current=null;
function selectRegion(id,fromChip){{ current=id; document.querySelectorAll(".region").forEach(r=>r.classList.toggle("active",r.dataset.region===id)); if(!fromChip) document.querySelectorAll(".chip").forEach(c=>c.classList.remove("active")); const d=DATA[id]; sideTitle.textContent=d.name; sideTitle.style.color=getColor(d.color); sideRole.textContent=d.role+" — "+d.summary; renderItems(d.items); countsEl.textContent=`当前脑区：${{d.name}} · 知识点 ${{d.items.length}} 条`; }}
function renderItems(items){{ sideBody.innerHTML=items.map(it=>`<div class="item" style="border-left-color:${{current?getColor(DATA[current].color):'var(--accent)'}}"><h3>${{it.t||it.title}}</h3><p>${{it.d||it.detail}}</p>{{it.s?`<a href="${{it.s}}" target="_blank" rel="noopener">📂 来源</a>`:''}}</div>`).join(""); }}
function showAll(){{ current=null; document.querySelectorAll(".region").forEach(r=>r.classList.remove("active")); sideTitle.textContent="🧭 全部知识点"; sideTitle.style.color="var(--ink)"; const total=ORDER.reduce((n,id)=>n+DATA[id].items.length,0); sideRole.textContent=`共 ${{ORDER.length}} 个脑区 · ${{total}} 个知识点 — 点击左侧脑区或上方筛选/搜索`; const all=ORDER.flatMap(id=>DATA[id].items.map(it=>({{...it,_r:id}}))); renderItems(all); countsEl.textContent=`全部脑区 · 共 ${{total}} 条知识点`; }}
document.getElementById("search").addEventListener("input",e=>{{ const q=e.target.value.trim().toLowerCase(); if(!q){{ showAll(); return; }} const hit=ORDER.flatMap(id=>DATA[id].items).filter(it=>(it.t||it.title||""+it.d||it.detail||"").toLowerCase().includes(q)); sideTitle.textContent=`🔍 搜索：“${{e.target.value}}”`; sideTitle.style.color="var(--accent)"; sideRole.textContent=`命中 ${{hit.length}} 条`; current="__search__"; renderItems(hit); countsEl.textContent=`搜索命中 ${{hit.length}} 条知识点`; }});
showAll();
</script>
</body>
</html>
"""

def build(knowledge_path, out_html):
    with open(knowledge_path, encoding="utf-8") as f:
        kb = json.load(f)
    # 转成前端 DATA 结构：每个 region 的 items 统一为 {title,detail,source}
    data = {}
    for reg in kb.get("regions", []):
        items = []
        for it in reg.get("items", []):
            items.append({
                "title": it.get("title") or it.get("t") or "",
                "detail": it.get("detail") or it.get("d") or "",
                "source": it.get("source") or it.get("s") or ""
            })
        data[reg["id"]] = {
            "name": reg.get("name", reg["id"]),
            "role": reg.get("role", ""),
            "color": reg.get("color", "#37474F"),
            "summary": reg.get("summary", ""),
            "items": items
        }
    html = HTML_TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False))
    os.makedirs(os.path.dirname(out_html) or ".", exist_ok=True)
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html)
    return len(data)
