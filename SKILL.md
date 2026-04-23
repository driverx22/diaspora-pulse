---
name: diaspora-pulse
version: "0.1.0"
description: "Research any topic through Ghanaian-diaspora sources in the United States. Pulls signals from diaspora media, community forums, diaspora YouTube creators, X handles, Ghanaian association and church-network sites, podcasts, and remittance/business hubs."
argument-hint: 'diaspora-pulse year of return | diaspora-pulse remittance corridors | diaspora-pulse ghana presidential elections'
allowed-tools: Bash, Read, Write, WebSearch, WebFetch
author: Daniel Gyimah
license: MIT
user-invocable: true
---

# diaspora-pulse

A Ghanaian-diaspora research skill. Point it at any topic and it will surface the last N days of coverage, commentary, and discussion from where US-based Ghanaians actually read, post, and gather — diaspora and pan-African media, Reddit/forum communities, diaspora YouTube creators, X handles, Ghanaian association sites, diaspora church networks, podcasts, and remittance/business hubs.

## When to use

- Research how a topic is landing inside the Ghanaian-American diaspora rather than in Ghana's domestic press
- Track a story through diaspora voices — creators, associations, churches, forums
- Pull diaspora perspectives and commentary for content, analysis, or podcast prep
- Audit a topic's coverage across the diaspora ecosystem (media vs. community vs. creators vs. institutional outlets)

For Ghana-domestic coverage, use `/ghana-pulse` instead. For global / non-Ghana research, use `/last30days`.

## How to invoke

```bash
# Topic mode — "what are diaspora sources saying about X?"
python3 scripts/diaspora_pulse.py "year of return"             --days=30 --emit=both
python3 scripts/diaspora_pulse.py "remittance corridors"       --days=14 --emit=markdown
python3 scripts/diaspora_pulse.py "ghana elections"            --sources=community,diaspora_media --emit=html
python3 scripts/diaspora_pulse.py "ghanaian churches in texas" --emit=json

# Trending mode — "what's moving in diaspora-land right now?" (topic optional)
python3 scripts/diaspora_pulse.py --trending --days=7 --emit=both
python3 scripts/diaspora_pulse.py "afrobeats" --trending --days=3 --emit=html
```

Flags:

- `--days=N` — lookback window (default 30)
- `--emit=markdown|html|both|json|plan` — output format (default markdown). `plan` emits the search plan without executing.
- `--sources=community,diaspora_media,youtube_diaspora,x_diaspora,associations,church,podcasts,business` — restrict to source categories
- `--max-items=N` — cap items per source (default 15)
- `--out-dir=PATH` — where to write outputs (default `./output`)
- `--trending` — trending mode. Topic becomes optional. Pulls most recent / most-engaged items from every source in the lookback window without forcing a keyword match. Output gets a "Trending now" top-N (ranked by virality score) and a "Rising themes" section highlighting keywords crossing 3+ categories in the last 48 hours. If you also pass a topic, it's applied as a soft boost (unquoted) instead of a hard filter.
- `--ingest=PATH` — render from a pre-collected JSON feed instead of running live search

## Trending mode — what it adds

When `--trending` is set the engine stops forcing `"topic"` quoting in scoped queries and instead asks each source for its most-recent content in the window. The renderer then:

1. **Scores every item** with `score = ln(1 + engagement) × recency_decay × source_weight`. Engagement comes from X `public_metrics` (likes/retweets/replies/quotes) and YouTube `statistics` (views/likes/comments) when those backends are live — web results fall back to recency × weight so they still rank.
2. **Surfaces "Trending now"** — top 15 items by score at the top of the brief/dashboard.
3. **Detects "Rising themes"** — tokenizes the last 48h of titles + snippets, finds tokens appearing in ≥3 distinct categories, and lists them as cross-over signals. This is the early-warning channel for stories breaking across diaspora press, community, and social simultaneously.

Optional API keys for richer trending signal: `X_API_BEARER_TOKEN` (tweet engagement metrics), `YOUTUBE_API_KEY` (channel recent-uploads + view counts), `BRAVE_API_KEY` or `SERPAPI_API_KEY` (generic web search).

## Backends (auto-dispatched per source)

| Backend | Scope | Auth | Engagement signal |
|---|---|---|---|
| Reddit JSON | any `community` source on `reddit.com/r/*` | none | `ups + 3×num_comments` |
| X API v2 | `x_diaspora` handles | `X_API_BEARER_TOKEN` | likes + 2×retweets + replies + 2×quotes |
| YouTube Data v3 | `youtube_diaspora` handles | `YOUTUBE_API_KEY` | views + 10×likes + 5×comments |
| GDELT DOC API | supplementary broad news pass (once per run) | none | — (ranked by recency × weight) |
| Brave / SerpAPI | every other scoped query + broad_queries | `BRAVE_API_KEY` or `SERPAPI_API_KEY` | — (ranked by recency × weight) |

Reddit and GDELT are always-on since they need no credentials — skip them with `DIASPORA_PULSE_DISABLE_REDDIT=1` or `DIASPORA_PULSE_DISABLE_GDELT=1`.

## Source categories

`scripts/sources.py` ships with a curated registry. Edit freely.

1. **community** — r/ghanaians, r/Ghana, GhanaWeb forum diaspora threads, Nairaland Ghana, indexed Facebook group pages for big chapters
2. **diaspora_media** — OkayAfrica, The Africa Report, African Arguments, Quartz Africa, Semafor Africa, Rest of World, TechCabal, African Business, Face2Face Africa
3. **youtube_diaspora** — Wode Maya, SVTV Africa, Ameyaw TV, ZionFelix, Delay Show, Kwaku Manu, Afia Schwarzenegger and other creators covering or living the US-diaspora life
4. **x_diaspora** — @GhanaEmbassyUSA, chapter handles, Ghanaian-American Chamber of Commerce, African Diaspora Network, prominent diaspora commentators
5. **associations** — NCOGA, COGA DC, COGA DFW, Ghana Council of Georgia, GUAOM (Maryland), AGO USA, GPSF (ghanaphysicians.org), US-Ghana Chamber of Commerce, African Diaspora Network
6. **church** — Church of Pentecost USA (copusa.org), ICGC North America, Presbyterian Church of Ghana USA congregations, Methodist/Wesley Methodist USA, Action Chapel International, Lighthouse / Dag Heward-Mills network
7. **podcasts** — Afropop Worldwide, Afrobility, African Tech Roundup and other diaspora-relevant shows with crawlable show-note pages
8. **business** — Remitly, Sendwave, WorldRemit and Wise blog corridor content, GIPC diaspora pages, Year of Return / Beyond the Return archive pages

## Output

- **Markdown brief** — ranked items grouped by category, each with source, date, one-line summary, and link. Includes a top-of-doc "Key patterns" section.
- **HTML dashboard** — self-contained single-file dashboard with KPI tiles, source/category filters, and a searchable table. Openable directly in a browser.
- **JSON** — raw merged feed for piping into downstream tools.

## Notes

- The skill uses the built-in `WebSearch` tool for discovery (scoped with `site:` filters) and `WebFetch` for enrichment. No third-party API keys required for baseline usage.
- If you have a Brave or SerpAPI key, drop it into `.env` and the engine will use it automatically for higher-fidelity results.
- Rendering is topic-agnostic — the skill does not inject business-specific framing. It renders what the sources say.
