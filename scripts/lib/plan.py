"""Build a search plan — a set of scoped queries against the diaspora source registry."""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sources  # noqa: E402  (imported from ../sources.py)


def build_search_plan(
    *,
    topic: str,
    days: int,
    categories: list,
    max_items: int,
    trending: bool = False,
) -> dict:
    """Return a JSON-serializable search plan.

    Modes:
      topic mode (default): `site:DOMAIN "topic" after:YYYY-MM-DD` per source,
        plus broad diaspora-qualified queries. Answers "what are diaspora
        sources saying about <topic>?"
      trending mode (trending=True): `site:DOMAIN after:YYYY-MM-DD` per source,
        no topic quoting. Broad queries become generic diaspora-pulse queries.
        Answers "what's moving in diaspora-land right now?" regardless of any
        specific topic. If a topic is ALSO provided, it's appended as a
        soft-boost keyword (no quotes) so relevant items still surface but
        the query isn't forced to match.

    The `after:YYYY-MM-DD` date filter is appended to every query using
    (today - days). Specialized backends (X API, YouTube Data API) read
    the same `after` from the top-level plan.
    """
    cutoff = (dt.date.today() - dt.timedelta(days=days)).isoformat()
    date_suffix = f" after:{cutoff}"

    srcs = sources.get_sources(categories)
    scoped_queries: list = []
    for s in srcs:
        domain = s.get("domain", "")
        if not domain:
            continue
        if trending:
            topic_frag = f" {topic}" if topic else ""  # unquoted = soft boost
            query = f"site:{domain}{topic_frag}" + date_suffix
        else:
            query = f'site:{domain} "{topic}"' + date_suffix

        scoped_queries.append({
            "source_id": s["id"],
            "source_name": s["name"],
            "category": s["category"],
            "weight": s.get("weight", 1.0),
            "domain": domain,
            "handle": s.get("handle"),
            "query": query,
            "max_results": max_items,
        })

    if trending:
        topic_frag = f" {topic}" if topic else ""
        broad_queries = [
            {"query": f"Ghanaian diaspora{topic_frag}" + date_suffix, "max_results": max_items},
            {"query": f"Ghanaians in America{topic_frag}" + date_suffix, "max_results": max_items},
            {"query": f"Ghana USA diaspora{topic_frag}" + date_suffix, "max_results": max_items},
            {"query": f"site:reddit.com Ghanaian{topic_frag}" + date_suffix, "max_results": max_items},
        ]
    else:
        broad_queries = [
            {"query": f'"{topic}" Ghanaian diaspora' + date_suffix, "max_results": max_items},
            {"query": f'"{topic}" Ghanaians in America' + date_suffix, "max_results": max_items},
            {"query": f'"{topic}" Ghana USA' + date_suffix, "max_results": max_items},
            {"query": f'"{topic}" site:reddit.com Ghanaian' + date_suffix, "max_results": max_items},
        ]

    return {
        "topic": topic,
        "days": days,
        "after": cutoff,
        "trending": trending,
        "categories": categories,
        "source_count": len(srcs),
        "scoped_queries": scoped_queries,
        "broad_queries": broad_queries,
    }
