"""Render collected results as Markdown brief and single-file HTML dashboard.

Virality scoring
----------------
Each item gets a `score` computed from:
  score = ln(1 + engagement) * recency_decay * weight
where:
  engagement    = normalized signal from X public_metrics / YouTube
                  statistics / 0 for web results
  recency_decay = max(0.1, 1 - days_since_published / lookback_window)
  weight        = source weight from the registry

Items without a published date get recency_decay = 0.5 (neutral). Items
without engagement signals still get a score from (recency_decay * weight)
so web results don't disappear.

Rising themes
-------------
After scoring, we tokenize titles + snippets (alphanumeric, >= 4 chars,
excluding stopwords) and count how many DISTINCT categories each token
appears in within the last 48 hours. Tokens appearing in 3+ categories
are surfaced as "rising themes" — early-warning signal for stories
crossing over between diaspora press, community, and social.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import math
import re
from collections import Counter, defaultdict


CAT_ORDER = [
    "community",
    "diaspora_media",
    "youtube_diaspora",
    "x_diaspora",
    "associations",
    "church",
    "podcasts",
    "business",
    "web",
]
CAT_LABEL = {
    "community": "Community",
    "diaspora_media": "Diaspora Media",
    "youtube_diaspora": "YouTube (Diaspora)",
    "x_diaspora": "X / Twitter (Diaspora)",
    "associations": "Associations",
    "church": "Church Networks",
    "podcasts": "Podcasts",
    "business": "Business / Remittance",
    "web": "Other web",
}

# Minimal stopword set — we only care about tokens 4+ chars
_STOPWORDS = {
    "this", "that", "with", "from", "have", "been", "were", "they", "their",
    "about", "what", "when", "will", "your", "would", "could", "should",
    "there", "these", "those", "also", "than", "then", "into", "some", "more",
    "just", "like", "over", "such", "only", "most", "much", "very", "here",
    "news", "said", "says", "told", "year", "week", "time", "ghana", "diaspora",
    "ghanaian", "ghanaians", "african", "america", "american",
}


# ---------------------------------------------------------------------------
# SCORING
# ---------------------------------------------------------------------------
def _score_items(results: list, days: int) -> list:
    today = dt.date.today()
    lookback = max(1, days)
    scored = []
    for r in results:
        engagement = int(r.get("engagement") or 0)
        weight = float(r.get("weight") or 1.0)
        pub = r.get("published")
        if pub:
            try:
                pub_date = dt.date.fromisoformat(str(pub)[:10])
                age_days = max(0, (today - pub_date).days)
                recency_decay = max(0.1, 1 - (age_days / lookback))
            except Exception:
                recency_decay = 0.5
        else:
            recency_decay = 0.5
        score = math.log1p(engagement) * recency_decay * weight
        # Floor: even engagement=0 items should rank on recency * weight
        if score == 0:
            score = recency_decay * weight * 0.25
        r2 = dict(r)
        r2["score"] = round(score, 3)
        r2["recency_decay"] = round(recency_decay, 3)
        scored.append(r2)
    return scored


# ---------------------------------------------------------------------------
# RISING THEMES — cross-category keyword overlap in last 48h
# ---------------------------------------------------------------------------
_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9'-]{3,}")


def _rising_themes(results: list, min_categories: int = 3, window_days: int = 2) -> list:
    today = dt.date.today()
    cat_by_token = defaultdict(set)        # token -> set(category)
    count_by_token = Counter()             # token -> total mentions in window
    for r in results:
        pub = r.get("published")
        if pub:
            try:
                pub_date = dt.date.fromisoformat(str(pub)[:10])
                if (today - pub_date).days > window_days:
                    continue
            except Exception:
                continue
        else:
            # undated items: include them (news-style results often lack dates)
            pass
        text = f"{r.get('title', '')} {r.get('snippet', '')}".lower()
        for tok in _WORD_RE.findall(text):
            tok = tok.lower()
            if tok in _STOPWORDS or len(tok) < 4:
                continue
            cat_by_token[tok].add(r.get("category") or "web")
            count_by_token[tok] += 1

    themes = []
    for tok, cats in cat_by_token.items():
        if len(cats) >= min_categories:
            themes.append({
                "token": tok,
                "categories": sorted(cats),
                "mentions": count_by_token[tok],
            })
    themes.sort(key=lambda x: (-len(x["categories"]), -x["mentions"]))
    return themes


# ---------------------------------------------------------------------------
# MARKDOWN
# ---------------------------------------------------------------------------
def render_markdown(
    topic: str, days: int, results: list, categories: list, trending: bool = False
) -> str:
    today = dt.date.today().isoformat()
    scored = _score_items(results, days)
    total = len(scored)

    by_cat = defaultdict(list)
    for r in scored:
        by_cat[r.get("category", "web")].append(r)

    source_counts = Counter(r.get("source_name") or "web" for r in scored)
    top_sources = source_counts.most_common(10)

    # Top N by score for "Trending now" — cap at 15
    trending_top = sorted(scored, key=lambda x: -x.get("score", 0))[:15]
    themes = _rising_themes(scored)

    lines = []
    title = topic if topic else "(no topic — trending pulse)"
    lines.append(f"# diaspora-pulse: {title}")
    lines.append("")
    mode_label = "trending mode" if trending else "topic mode"
    lines.append(
        f"_Pulled {today} - lookback {days} days - {mode_label} - "
        f"categories: {', '.join(categories)}_"
    )
    lines.append("")
    lines.append(f"**{total} items** across {sum(1 for c in by_cat if by_cat[c])} source categories.")
    lines.append("")

    # TRENDING NOW — top by virality score
    lines.append("## Trending now (top by virality score)")
    lines.append("")
    if trending_top:
        for r in trending_top:
            sc = r.get("score", 0)
            eng = r.get("engagement", 0)
            cat = CAT_LABEL.get(r.get("category", "web"), r.get("category", "web"))
            src = r.get("source_name") or ""
            pub = r.get("published") or "—"
            eng_frag = f" · {eng:,} eng" if eng else ""
            lines.append(
                f"- **[{sc:.2f}]** {r['title']} — _{src}_ · {cat} · {pub}{eng_frag}"
            )
            lines.append(f"  - {r['url']}")
    else:
        lines.append("- No items collected.")
    lines.append("")

    # RISING THEMES
    lines.append("## Rising themes (cross-category, last 48h)")
    lines.append("")
    if themes:
        for th in themes[:12]:
            cats = ", ".join(CAT_LABEL.get(c, c) for c in th["categories"])
            lines.append(
                f"- **{th['token']}** — {len(th['categories'])} categories "
                f"({cats}) · {th['mentions']} mentions"
            )
    else:
        lines.append("- No cross-category themes detected in the last 48 hours.")
    lines.append("")

    # Key patterns
    lines.append("## Key patterns")
    lines.append("")
    if top_sources:
        for name, count in top_sources:
            lines.append(f"- {name}: {count} item{'s' if count != 1 else ''}")
    else:
        lines.append("- No items collected.")
    lines.append("")

    # Grouped items
    for cat in CAT_ORDER:
        items = by_cat.get(cat) or []
        if not items:
            continue
        items.sort(key=lambda x: -x.get("score", 0))
        lines.append(f"## {CAT_LABEL.get(cat, cat)}")
        lines.append("")
        for r in items[:40]:
            pub = r.get("published") or ""
            pub_s = f" ({pub})" if pub else ""
            src = r.get("source_name") or ""
            sc = r.get("score", 0)
            eng = r.get("engagement", 0)
            eng_frag = f" · {eng:,} eng" if eng else ""
            lines.append(
                f"- **{r['title']}** — {src}{pub_s} · score {sc:.2f}{eng_frag}"
            )
            snip = (r.get("snippet") or "").strip()
            if snip:
                lines.append(f"  - {snip[:300]}")
            lines.append(f"  - {r['url']}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(
        "_diaspora-pulse is a skill for pulling Ghanaian-diaspora (USA) coverage of any topic. "
        "Edit `scripts/sources.py` to tune the registry. Run with `--trending` for a no-topic pulse._"
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# HTML DASHBOARD
# ---------------------------------------------------------------------------
def render_html(
    topic: str, days: int, results: list, categories: list, trending: bool = False
) -> str:
    today = dt.date.today().isoformat()
    scored = _score_items(results, days)
    total = len(scored)
    by_cat = Counter(r.get("category", "web") for r in scored)
    by_source = Counter(r.get("source_name", "?") for r in scored)
    trending_top = sorted(scored, key=lambda x: -x.get("score", 0))[:15]
    themes = _rising_themes(scored)

    items_payload = [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "snippet": r.get("snippet", ""),
            "published": r.get("published") or "",
            "source": r.get("source_name") or "",
            "category": r.get("category") or "web",
            "weight": r.get("weight", 1.0),
            "score": r.get("score", 0),
            "engagement": r.get("engagement", 0),
            "metrics": r.get("metrics") or {},
        }
        for r in scored
    ]

    topic_h = html.escape(topic) if topic else "(trending pulse)"
    cats_h = html.escape(", ".join(categories))
    mode_label = "trending" if trending else "topic"

    kpi_tiles = "".join(
        f'<div class="kpi"><div class="kpi-val">{n}</div>'
        f'<div class="kpi-lbl">{html.escape(CAT_LABEL.get(cat, str(cat)))}</div></div>'
        for cat, n in by_cat.most_common()
    )

    trending_rows = "".join(
        f'<tr><td><b>{r.get("score", 0):.2f}</b></td>'
        f'<td><a href="{html.escape(r.get("url", ""))}" target="_blank" rel="noopener">'
        f'{html.escape(r.get("title", ""))}</a></td>'
        f'<td>{html.escape(r.get("source_name") or "")}</td>'
        f'<td><span class="cat">{html.escape(CAT_LABEL.get(r.get("category", "web"), "web"))}</span></td>'
        f'<td>{html.escape(r.get("published") or "—")}</td>'
        f'<td>{r.get("engagement", 0):,}</td></tr>'
        for r in trending_top
    ) or '<tr><td colspan="6" style="color:var(--muted); padding:18px;">No items scored.</td></tr>'

    themes_chips = "".join(
        f'<span class="theme" title="{html.escape(", ".join(CAT_LABEL.get(c, c) for c in th["categories"]))}">'
        f'{html.escape(th["token"])} <em>({len(th["categories"])})</em></span>'
        for th in themes[:12]
    ) or '<span class="muted">No cross-category themes detected in last 48h.</span>'

    top_sources_rows = "".join(
        f"<tr><td>{html.escape(str(name))}</td><td>{count}</td></tr>"
        for name, count in by_source.most_common(15)
    )

    cat_options = "".join(
        f'<option value="{html.escape(cat)}">{html.escape(CAT_LABEL.get(cat, cat))}</option>'
        for cat in CAT_ORDER
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>diaspora-pulse - {topic_h}</title>
<style>
  :root {{
    --bg:#0b1020; --panel:#121a33; --text:#e6ecff; --muted:#9fb0d9; --accent:#ffd166;
    --border:#1f2a4a; --hit:#f9f7f2; --heat:#ff6b6b;
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; font-family:-apple-system,Segoe UI,Roboto,sans-serif; background:var(--bg); color:var(--text); }}
  header {{ padding:24px 28px; border-bottom:1px solid var(--border); }}
  h1 {{ margin:0 0 4px; font-size:22px; }}
  h2 {{ font-size:15px; color:var(--muted); text-transform:uppercase; letter-spacing:.08em; margin:26px 0 10px; }}
  .sub {{ color:var(--muted); font-size:13px; }}
  .badge {{ display:inline-block; padding:2px 8px; margin-left:8px; background:var(--heat); color:#fff;
            border-radius:999px; font-size:11px; font-weight:600; letter-spacing:.05em; }}
  .wrap {{ padding:24px 28px; max-width:1280px; margin:0 auto; }}
  .kpis {{ display:flex; gap:12px; flex-wrap:wrap; margin:0 0 20px; }}
  .kpi {{ background:var(--panel); border:1px solid var(--border); border-radius:10px; padding:14px 16px; min-width:120px; }}
  .kpi-val {{ font-size:26px; font-weight:700; color:var(--accent); }}
  .kpi-lbl {{ color:var(--muted); font-size:12px; text-transform:uppercase; letter-spacing:.08em; }}
  .toolbar {{ display:flex; gap:10px; align-items:center; flex-wrap:wrap; margin-bottom:16px; }}
  input[type=text], select {{ background:var(--panel); color:var(--text); border:1px solid var(--border); border-radius:8px; padding:8px 10px; }}
  table {{ width:100%; border-collapse:collapse; background:var(--panel); border:1px solid var(--border); border-radius:10px; overflow:hidden; }}
  th, td {{ text-align:left; padding:10px 12px; border-bottom:1px solid var(--border); vertical-align:top; font-size:14px; }}
  th {{ background:#0f172c; color:var(--muted); font-weight:600; font-size:12px; text-transform:uppercase; letter-spacing:.06em; }}
  tr:last-child td {{ border-bottom:none; }}
  a {{ color:#8cb4ff; text-decoration:none; }}
  a:hover {{ text-decoration:underline; }}
  .cat {{ display:inline-block; padding:2px 8px; border-radius:999px; background:#1b2750; color:var(--muted); font-size:11px; letter-spacing:.04em; }}
  .themes {{ display:flex; flex-wrap:wrap; gap:8px; margin-bottom:20px; }}
  .theme {{ background:var(--panel); border:1px solid var(--border); color:var(--text);
            padding:6px 12px; border-radius:999px; font-size:13px; }}
  .theme em {{ color:var(--accent); font-style:normal; font-weight:600; }}
  .muted {{ color:var(--muted); font-size:13px; }}
  .two-col {{ display:grid; grid-template-columns: 2fr 1fr; gap:20px; margin-top:18px; }}
  @media (max-width: 900px) {{ .two-col {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
<header>
  <h1>diaspora-pulse - {topic_h} <span class="badge">{mode_label}</span></h1>
  <div class="sub">Pulled {today} - lookback {days} days - categories: {cats_h} - {total} items</div>
</header>
<div class="wrap">
  <div class="kpis">
    <div class="kpi"><div class="kpi-val">{total}</div><div class="kpi-lbl">items</div></div>
    {kpi_tiles}
  </div>

  <h2>Rising themes (cross-category, last 48h)</h2>
  <div class="themes">{themes_chips}</div>

  <h2>Trending now (top 15 by virality score)</h2>
  <table>
    <thead>
      <tr><th>Score</th><th>Title</th><th>Source</th><th>Category</th><th>Published</th><th>Eng</th></tr>
    </thead>
    <tbody>{trending_rows}</tbody>
  </table>

  <h2>All items</h2>
  <div class="toolbar">
    <input id="q" type="text" placeholder="Filter items..." size="40" />
    <select id="catFilter">
      <option value="">All categories</option>
      {cat_options}
    </select>
    <select id="sortBy">
      <option value="score">Sort: score</option>
      <option value="published">Sort: published</option>
      <option value="engagement">Sort: engagement</option>
    </select>
  </div>

  <div class="two-col">
    <div>
      <table id="items">
        <thead>
          <tr><th>Score</th><th>Title</th><th>Source</th><th>Category</th><th>Published</th><th>Eng</th></tr>
        </thead>
        <tbody></tbody>
      </table>
    </div>
    <div>
      <table>
        <thead><tr><th>Top sources</th><th>#</th></tr></thead>
        <tbody>
          {top_sources_rows}
        </tbody>
      </table>
    </div>
  </div>
</div>

<script>
const ITEMS = {_js(items_payload)};
const CAT_LABEL = {_js(CAT_LABEL)};
const tbody = document.querySelector("#items tbody");
const q = document.getElementById("q");
const catSel = document.getElementById("catFilter");
const sortSel = document.getElementById("sortBy");

function esc(s) {{
  return String(s || "").replace(/[&<>"]/g, c => ({{"&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;"}}[c]));
}}

function render() {{
  const needle = q.value.toLowerCase().trim();
  const cat = catSel.value;
  const sortKey = sortSel.value;
  const rows = ITEMS.filter(it => {{
    if (cat && it.category !== cat) return false;
    if (!needle) return true;
    return (it.title + " " + it.snippet + " " + it.source).toLowerCase().includes(needle);
  }}).sort((a, b) => {{
    if (sortKey === "published") return (b.published || "").localeCompare(a.published || "");
    if (sortKey === "engagement") return (b.engagement || 0) - (a.engagement || 0);
    return (b.score || 0) - (a.score || 0);
  }}).map(it => `
    <tr>
      <td><b>${{(it.score || 0).toFixed(2)}}</b></td>
      <td><a href="${{esc(it.url)}}" target="_blank" rel="noopener">${{esc(it.title)}}</a>
          <div style="color:var(--muted); font-size:12px; margin-top:3px;">${{esc(it.snippet)}}</div></td>
      <td>${{esc(it.source)}}</td>
      <td><span class="cat">${{esc(CAT_LABEL[it.category] || it.category)}}</span></td>
      <td>${{esc(it.published)}}</td>
      <td>${{(it.engagement || 0).toLocaleString()}}</td>
    </tr>
  `).join("");
  tbody.innerHTML = rows || '<tr><td colspan="6" style="color:var(--muted); padding:18px;">No items match.</td></tr>';
}}

q.addEventListener("input", render);
catSel.addEventListener("change", render);
sortSel.addEventListener("change", render);
render();
</script>
</body>
</html>
"""


def _js(obj) -> str:
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")
