#!/usr/bin/env python3
"""diaspora-pulse CLI.

Research any topic through Ghanaian-diaspora (USA) sources. Pulls from
community forums, diaspora and pan-African media, diaspora YouTube creators,
X handles, Ghanaian association and church-network sites, podcasts, and
remittance/business content hubs, then emits a markdown brief, HTML
dashboard, or JSON feed.

Usage:
    python3 diaspora_pulse.py "year of return" --days=30 --emit=both
    python3 diaspora_pulse.py "remittance corridors" --emit=markdown --sources=community,business
    python3 diaspora_pulse.py --trending --days=7 --emit=both
    python3 diaspora_pulse.py "afrobeats" --trending --days=3 --emit=html

Notes:
    The engine generates a "search plan" and either executes it against the
    available search backends (Brave, SerpAPI, X API, YouTube Data API) OR
    emits the plan as machine-readable JSON so an LLM harness can run the
    searches and pipe results back in via --ingest=<file>.

    --trending mode: skips topic-keyword filtering and pulls each source's
    most recent / most-engaged content in the lookback window. The renderer
    then scores items by engagement + recency and surfaces cross-category
    rising themes (keywords mentioned in 3+ categories within 48h).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR))

from lib import plan, ingest, render  # noqa: E402


def parse_args(argv: list) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="diaspora-pulse",
        description="Research any topic through Ghanaian-diaspora (USA) sources.",
    )
    p.add_argument(
        "topic",
        nargs="?",
        default="",
        help="What to research (e.g. 'year of return'). Optional when --trending is set.",
    )
    p.add_argument("--days", type=int, default=30, help="Lookback window in days (default 30)")
    p.add_argument(
        "--sources",
        default="community,diaspora_media,youtube_diaspora,x_diaspora,associations,church,podcasts,business",
        help=(
            "Comma-separated categories: community, diaspora_media, youtube_diaspora, "
            "x_diaspora, associations, church, podcasts, business"
        ),
    )
    p.add_argument("--max-items", type=int, default=15, help="Max items per source (default 15)")
    p.add_argument(
        "--emit",
        choices=["markdown", "html", "both", "json", "plan"],
        default="markdown",
        help="Output format. 'plan' prints the search plan without executing it.",
    )
    p.add_argument(
        "--out-dir",
        default=str(SCRIPT_DIR.parent / "output"),
        help="Directory to write outputs (default ./output)",
    )
    p.add_argument(
        "--ingest",
        default=None,
        help="Path to a JSON file of search results produced by an external harness. "
             "When set, the engine skips live search and renders from this file.",
    )
    p.add_argument(
        "--no-exec",
        action="store_true",
        help="Do not run live searches even if a backend is available. Emit the plan instead.",
    )
    p.add_argument(
        "--trending",
        action="store_true",
        help="Trending mode. Topic becomes optional. Pulls most recent / most-engaged items "
             "from every source in the lookback window (no keyword filter). Renderer ranks by "
             "virality score and surfaces rising themes across categories.",
    )
    args = p.parse_args(argv)

    if not args.trending and not args.topic:
        p.error("topic is required unless --trending is set")

    return args


def main(argv: list) -> int:
    args = parse_args(argv)
    categories = [c.strip() for c in args.sources.split(",") if c.strip()]
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = _slugify(args.topic) if args.topic else ("trending" if args.trending else "topic")

    search_plan = plan.build_search_plan(
        topic=args.topic,
        days=args.days,
        categories=categories,
        max_items=args.max_items,
        trending=args.trending,
    )

    if args.emit == "plan" or args.no_exec:
        print(json.dumps(search_plan, indent=2, ensure_ascii=False))
        return 0

    if args.ingest:
        results = ingest.load_ingest_file(Path(args.ingest))
    else:
        results = ingest.run_live_search(search_plan)

    if not results:
        sys.stderr.write(
            "diaspora-pulse: no results were collected. Either run with --emit=plan "
            "to get the search plan, execute the queries with your harness, and "
            "re-run with --ingest=<file>, OR configure a search backend "
            "(BRAVE_API_KEY, SERPAPI_API_KEY). See README.md.\n"
        )
        return 2

    artifacts = {}
    if args.emit in ("markdown", "both"):
        md_path = out_dir / f"diaspora-pulse-{slug}.md"
        md_path.write_text(
            render.render_markdown(
                args.topic, args.days, results, categories, trending=args.trending
            ),
            encoding="utf-8",
        )
        artifacts["markdown"] = md_path
    if args.emit in ("html", "both"):
        html_path = out_dir / f"diaspora-pulse-{slug}.html"
        html_path.write_text(
            render.render_html(
                args.topic, args.days, results, categories, trending=args.trending
            ),
            encoding="utf-8",
        )
        artifacts["html"] = html_path
    if args.emit == "json":
        json_path = out_dir / f"diaspora-pulse-{slug}.json"
        json_path.write_text(
            json.dumps(
                {"topic": args.topic, "days": args.days, "trending": args.trending,
                 "results": results},
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        artifacts["json"] = json_path

    for kind, p in artifacts.items():
        print(f"{kind}: {p}")
    return 0


def _slugify(s: str) -> str:
    import re

    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:60] or "topic"


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
