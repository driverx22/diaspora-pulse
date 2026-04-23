# diaspora-pulse

A Ghanaian-diaspora research skill. Point it at any topic and get the last N
days of coverage from where US-based Ghanaians actually read, post, and gather
— diaspora media, community forums, YouTube creators, X handles, Ghanaian
association sites, diaspora church networks, podcasts, and remittance/business
content hubs.

Modeled on the `ghana-pulse` skill architecture but scoped to the Ghanaian
diaspora in the United States. Topic-agnostic by design.

## Install

This is a Claude Code / Cowork skill. Install it as a plugin straight from
GitHub:

```
/plugin marketplace add driverx22/diaspora-pulse
/plugin install diaspora-pulse@driverx22
```

Or, if you've cloned the repo locally and want to point at the folder
directly (useful for development):

```
/plugin marketplace add /path/to/diaspora-pulse
/plugin install diaspora-pulse@diaspora-pulse
```

## Layout

```
diaspora-pulse/
  SKILL.md                 # skill definition + usage contract
  scripts/
    diaspora_pulse.py      # CLI entrypoint
    sources.py             # Diaspora source registry (edit freely)
    lib/
      __init__.py
      plan.py              # builds a scoped-search plan
      ingest.py            # runs live search OR ingests a results file
      render.py            # markdown + HTML dashboard renderers
  commands/
    diaspora-pulse.md      # slash-command entrypoint
  .claude-plugin/
    plugin.json
    marketplace.json
  README.md
```

## Use it three ways

### 1. Inside Claude Code / Cowork (no API keys needed)

```
/diaspora-pulse year of return
```

The skill emits a search plan; the harness runs each scoped `site:` query
via its built-in `WebSearch` tool and pipes results back in.

Manually:

```bash
python3 scripts/diaspora_pulse.py "year of return" --emit=plan > plan.json
# ...agent harness runs plan.json queries, saves combined results as results.json...
python3 scripts/diaspora_pulse.py "year of return" --ingest=results.json --emit=both
```

### 2. Standalone with a search API

Set `BRAVE_API_KEY` (preferred) or `SERPAPI_API_KEY` and the engine runs the
plan itself:

```bash
export BRAVE_API_KEY=...
python3 scripts/diaspora_pulse.py "remittance corridors" --days=30 --emit=both
```

### 3. Just the plan

```bash
python3 scripts/diaspora_pulse.py "ghana elections diaspora" --emit=plan
```

Useful when you want to hand the scoped queries to any other system.

## Flags

| Flag | Default | Notes |
|------|---------|-------|
| `--days N` | 30 | lookback window |
| `--emit` | markdown | markdown \| html \| both \| json \| plan |
| `--sources` | community,diaspora_media,youtube_diaspora,x_diaspora,associations,church,podcasts,business | restrict to categories |
| `--max-items N` | 15 | cap per-source items |
| `--out-dir PATH` | ./output | where to write outputs |
| `--ingest PATH` | - | JSON file of pre-collected results |
| `--no-exec` | off | always emit the plan, never run live search |

## Output

- `output/diaspora-pulse-<slug>.md` — ranked brief grouped by source category
- `output/diaspora-pulse-<slug>.html` — single-file dashboard with filters + search
- `output/diaspora-pulse-<slug>.json` — raw merged feed (when `--emit=json`)

## Editing the source registry

Everything lives in `scripts/sources.py`. Each source is a plain dict:

```python
{"id": "okayafrica", "name": "OkayAfrica", "category": "diaspora_media",
 "domain": "okayafrica.com", "weight": 1.1,
 "notes": "Pan-African diaspora publication with significant Ghana coverage."}
```

For subreddits and Facebook groups, use path-prefixed domains — the URL matcher
in `lib/ingest.py` supports this and will match correctly without colliding
with other reddit/facebook URLs:

```python
{"id": "r_ghanaians", "name": "r/ghanaians", "category": "community",
 "domain": "reddit.com/r/ghanaians", "weight": 1.2,
 "notes": "Ghanaian subreddit — strong diaspora presence."}
```

Add a source — it appears in the plan on next run. No other code changes
needed.

Categories: `community`, `diaspora_media`, `youtube_diaspora`, `x_diaspora`,
`associations`, `church`, `podcasts`, `business`.
