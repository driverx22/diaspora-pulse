---
description: Research any topic through Ghanaian-diaspora sources in the United States — diaspora media, forums, YouTube creators, X handles, association and church-network sites, podcasts, and remittance/business hubs.
argument-hint: <topic> — e.g. "year of return" or "remittance corridors" or "ghana elections diaspora"
allowed-tools: [Bash, Read, Write, WebSearch, WebFetch]
---

Invoke the `diaspora-pulse` skill with the user's arguments: $ARGUMENTS

## Execution contract

1. If the user provided no arguments, ask them for a topic before proceeding.

2. Build the search plan by running the engine in plan-only mode:
   ```bash
   python3 "$SKILL_ROOT/scripts/diaspora_pulse.py" "$TOPIC" --emit=plan > /tmp/diaspora-pulse-plan.json
   ```
   where `$SKILL_ROOT` points to this plugin folder (resolve it from the command context) and `$TOPIC` is `$ARGUMENTS`.

3. Read the plan. For each entry in `scoped_queries` and `broad_queries`, run the query via the `WebSearch` tool. Collect results into a JSON file with shape:
   ```json
   {
     "<query string>": [
       {"title": "...", "url": "...", "snippet": "...", "published": "YYYY-MM-DD"},
       ...
     ],
     ...
   }
   ```
   Save to `/tmp/diaspora-pulse-results.json`.

4. Render by piping the collected results back into the engine:
   ```bash
   python3 "$SKILL_ROOT/scripts/diaspora_pulse.py" "$TOPIC" \
       --ingest=/tmp/diaspora-pulse-results.json \
       --emit=both \
       --out-dir="$SKILL_ROOT/output"
   ```

5. Present both artifacts to the user using `computer://` links:
   - `output/diaspora-pulse-<slug>.md` — the markdown brief
   - `output/diaspora-pulse-<slug>.html` — the single-file dashboard

## Flags the user may pass

Parse these from `$ARGUMENTS` if present and forward them verbatim to the engine:

- `--days=N` — lookback window (default 30)
- `--sources=community,diaspora_media,youtube_diaspora,x_diaspora,associations,church,podcasts,business` — restrict source categories
- `--max-items=N` — cap items per source (default 15)
- `--emit=markdown|html|both|json|plan` — override default (both)

## Source registry

The skill ships with a curated Ghanaian-diaspora source registry in `scripts/sources.py`. It covers community (r/ghanaians, r/Ghana, GhanaWeb forum, Nairaland Ghana), diaspora media (OkayAfrica, The Africa Report, African Arguments, Quartz Africa, Semafor Africa, Rest of World, TechCabal, African Business, Face2Face Africa), diaspora YouTube creators (Wode Maya, SVTV Africa, Ameyaw TV, ZionFelix, Delay Show, Kwaku Manu, Afia Schwarzenegger), X handles (@GhanaEmbassyUSA, chapter accounts, African Diaspora Network, prominent commentators), associations (NCOGA, COGA DC, COGA DFW, Ghana Council of Georgia, GUAOM, AGO USA, GPSF, US-Ghana Chamber of Commerce, African Diaspora Network), diaspora church networks (Church of Pentecost USA, ICGC North America, Presbyterian Church of Ghana USA congregations, Methodist/Wesley Methodist USA, Action Chapel, Dag Heward-Mills/Lighthouse), podcasts (Afropop Worldwide, Afrobility, African Tech Roundup), and remittance/business hubs (Remitly, Sendwave, WorldRemit, Wise, GIPC, Year of Return). Edit `scripts/sources.py` directly to add or tune sources.

## Output framing

Render what the sources say. Do not inject Fintaxe, marketing, or client-pitch framing unless the user explicitly asks. The skill is topic-agnostic. Attribute clearly, let the user decide the next step.
