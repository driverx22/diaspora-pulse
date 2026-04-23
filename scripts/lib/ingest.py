"""Ingest search results.

Five backends are supported, dispatched per scoped query:

  1. Reddit JSON (no key, always-on) — used for community-category sources
     whose domain starts with reddit.com/r/. Calls /search.json for topic
     mode, /hot.json for trending mode. Captures `ups` + `num_comments`
     for engagement-based virality scoring.
  2. X API v2 recent search (X_API_BEARER_TOKEN) — for x_diaspora handles.
     Captures public_metrics (likes, retweets, replies, quotes).
  3. YouTube Data API v3 (YOUTUBE_API_KEY) — for youtube_diaspora handles.
     Two-pass: search.list then videos.list?part=statistics for view counts.
  4. GDELT DOC API (no key, always-on) — fired once per run as a
     supplementary broad query. Surfaces fresh Ghana/diaspora news from
     outlets NOT in the registry, ranked by GDELT's hybridrel sort. Fills
     the "unknown unknowns" gap for breaking stories.
  5. Generic web search (BRAVE_API_KEY or SERPAPI_API_KEY) — every other
     scoped query and the broad_queries section.

If none is available, run_live_search returns [] and the CLI falls back to
emitting the plan. Reddit JSON and GDELT are always-on because they don't
require credentials — the only reason to skip them is if you've got no
internet.

Trending mode:
    When the plan's `trending` flag is set, all keyword-driven backends
    (Reddit, X, YouTube) drop the topic filter and pull most-recent /
    most-engaged items from the source within the lookback window.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sources  # noqa: E402


def load_ingest_file(path: Path) -> list:
    data = json.loads(path.read_text(encoding="utf-8"))
    items = []
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        if "results" in data and isinstance(data["results"], list):
            items = data["results"]
        else:
            for q, lst in data.items():
                if isinstance(lst, list):
                    for r in lst:
                        if isinstance(r, dict):
                            r.setdefault("query", q)
                            items.append(r)
    return _normalize(items)


def run_live_search(search_plan: dict) -> list:
    web_backend = _pick_web_backend()
    x_enabled = bool(os.getenv("X_API_BEARER_TOKEN"))
    yt_enabled = bool(os.getenv("YOUTUBE_API_KEY"))
    # Reddit JSON + GDELT are always-on (no credentials required)
    reddit_enabled = os.getenv("DIASPORA_PULSE_DISABLE_REDDIT") != "1"
    gdelt_enabled = os.getenv("DIASPORA_PULSE_DISABLE_GDELT") != "1"

    if not any([web_backend, x_enabled, yt_enabled, reddit_enabled, gdelt_enabled]):
        return []

    topic = search_plan.get("topic", "") or ""
    after = search_plan.get("after")
    trending = bool(search_plan.get("trending"))
    days = search_plan.get("days") or 30
    out = []

    for q in search_plan.get("scoped_queries", []):
        query = q["query"]
        n = q.get("max_results", 15)
        category = q.get("category")
        handle = q.get("handle")
        domain = q.get("domain", "") or ""
        # Source attribution for pre-stamping specialized-backend results.
        src_attr = {
            "source_id": q.get("source_id"),
            "source_name": q.get("source_name"),
            "category": category,
            "weight": q.get("weight"),
        }

        try:
            # Reddit JSON — dispatch any community source on reddit.com/r/*
            if (reddit_enabled
                    and category == "community"
                    and domain.lower().startswith("reddit.com/r/")):
                sub = domain.split("/r/", 1)[1].split("/", 1)[0]
                out.extend(_reddit_json_search(sub, topic, days, n, query, trending, src_attr))
                continue
            if category == "x_diaspora" and x_enabled and handle:
                out.extend(_x_api_search(handle, topic, after, n, query, trending, src_attr))
                continue
            if category == "youtube_diaspora" and yt_enabled and handle:
                out.extend(_youtube_api_search(handle, topic, after, n, query, trending, src_attr))
                continue
            if web_backend:
                out.extend(web_backend(query, n))
        except Exception as e:
            sys.stderr.write(f"diaspora-pulse: query failed ({query!r}): {e}\n")

    if web_backend:
        for q in search_plan.get("broad_queries", []):
            try:
                out.extend(web_backend(q["query"], q.get("max_results", 15)))
            except Exception as e:
                sys.stderr.write(f"diaspora-pulse: query failed ({q['query']!r}): {e}\n")

    # GDELT — one supplementary pass, broad news coverage.
    if gdelt_enabled:
        try:
            out.extend(_gdelt_search(topic, days, trending, max_results=25))
        except Exception as e:
            sys.stderr.write(f"diaspora-pulse: GDELT query failed: {e}\n")

    return _normalize(out)


# ---------------------------------------------------------------------------
# WEB BACKENDS (Brave / SerpAPI)
# ---------------------------------------------------------------------------
def _pick_web_backend():
    if os.getenv("BRAVE_API_KEY"):
        return _brave_search
    if os.getenv("SERPAPI_API_KEY"):
        return _serpapi_search
    return None


def _brave_search(query: str, n: int) -> list:
    import urllib.parse, urllib.request
    url = "https://api.search.brave.com/res/v1/web/search?" + urllib.parse.urlencode(
        {"q": query, "count": min(n, 20)})
    req = urllib.request.Request(url, headers={
        "Accept": "application/json",
        "X-Subscription-Token": os.environ["BRAVE_API_KEY"],
    })
    with urllib.request.urlopen(req, timeout=20) as resp:
        payload = json.loads(resp.read())
    results = (payload.get("web") or {}).get("results") or []
    return [{
        "title": r.get("title"),
        "url": r.get("url"),
        "snippet": r.get("description"),
        "published": (r.get("page_age") or "").split("T")[0] or None,
        "query": query,
    } for r in results]


def _serpapi_search(query: str, n: int) -> list:
    import urllib.parse, urllib.request
    url = "https://serpapi.com/search.json?" + urllib.parse.urlencode(
        {"q": query, "num": min(n, 20), "api_key": os.environ["SERPAPI_API_KEY"]})
    with urllib.request.urlopen(url, timeout=20) as resp:
        payload = json.loads(resp.read())
    return [{
        "title": r.get("title"),
        "url": r.get("link"),
        "snippet": r.get("snippet"),
        "published": r.get("date"),
        "query": query,
    } for r in (payload.get("organic_results") or [])]


# ---------------------------------------------------------------------------
# X API v2 (recent search) — captures public_metrics for virality scoring
# ---------------------------------------------------------------------------
def _x_api_search(handle: str, topic: str, after, n: int, query: str, trending: bool, src_attr: dict | None = None) -> list:
    import urllib.parse, urllib.request

    user = handle.lstrip("@")
    q_parts = [f"from:{user}"]
    if topic and not trending:
        q_parts.append(f'"{topic}"')
    elif topic and trending:
        q_parts.append(topic)  # unquoted soft boost
    x_query = " ".join(q_parts)

    params = {
        "query": x_query,
        "max_results": max(10, min(n, 100)),
        "tweet.fields": "created_at,text,author_id,public_metrics",
    }
    if after:
        params["start_time"] = f"{after}T00:00:00Z"

    url = "https://api.twitter.com/2/tweets/search/recent?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {os.environ['X_API_BEARER_TOKEN']}",
    })
    with urllib.request.urlopen(req, timeout=20) as resp:
        payload = json.loads(resp.read())

    out = []
    for t in (payload.get("data") or []):
        tid = t.get("id")
        text = (t.get("text") or "").strip()
        created = (t.get("created_at") or "").split("T")[0] or None
        tweet_url = f"https://x.com/{user}/status/{tid}" if tid else f"https://x.com/{user}"
        title = text[:120].replace("\n", " ").strip() or f"@{user} tweet"
        m = t.get("public_metrics") or {}
        engagement = (
            (m.get("like_count") or 0)
            + (m.get("retweet_count") or 0) * 2
            + (m.get("reply_count") or 0)
            + (m.get("quote_count") or 0) * 2
        )
        item = {
            "title": title,
            "url": tweet_url,
            "snippet": text,
            "published": created,
            "query": query,
            "metrics": {
                "likes": m.get("like_count", 0),
                "retweets": m.get("retweet_count", 0),
                "replies": m.get("reply_count", 0),
                "quotes": m.get("quote_count", 0),
            },
            "engagement": engagement,
        }
        if src_attr:
            item["_source_attr"] = src_attr
        out.append(item)
    return out


# ---------------------------------------------------------------------------
# YouTube Data API v3 — two-pass: search.list -> videos.list(statistics)
# ---------------------------------------------------------------------------
_YT_CHANNEL_CACHE: dict = {}


def _youtube_api_search(handle: str, topic: str, after, n: int, query: str, trending: bool, src_attr: dict | None = None) -> list:
    import urllib.parse, urllib.request

    channel_id = _yt_resolve_channel(handle)
    if not channel_id:
        return []

    params = {
        "part": "snippet",
        "channelId": channel_id,
        "type": "video",
        "order": "date",
        "maxResults": max(1, min(n, 50)),
        "key": os.environ["YOUTUBE_API_KEY"],
    }
    if topic and not trending:
        params["q"] = topic
    elif topic and trending:
        params["q"] = topic  # soft filter; YT API won't force quote semantics anyway
    if after:
        params["publishedAfter"] = f"{after}T00:00:00Z"

    url = "https://www.googleapis.com/youtube/v3/search?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=20) as resp:
        payload = json.loads(resp.read())

    items_raw = payload.get("items") or []
    video_ids = [(it.get("id") or {}).get("videoId") for it in items_raw]
    video_ids = [v for v in video_ids if v]

    stats_by_id = _yt_fetch_stats(video_ids) if video_ids else {}

    out = []
    for item in items_raw:
        vid = (item.get("id") or {}).get("videoId")
        if not vid:
            continue
        snip = item.get("snippet") or {}
        title = (snip.get("title") or "").strip()
        desc = (snip.get("description") or "").strip()
        published = (snip.get("publishedAt") or "").split("T")[0] or None
        s = stats_by_id.get(vid, {})
        views = int(s.get("viewCount", 0) or 0)
        likes = int(s.get("likeCount", 0) or 0)
        comments = int(s.get("commentCount", 0) or 0)
        # Views dominate; likes/comments are secondary signals
        engagement = views + likes * 10 + comments * 5
        item = {
            "title": title,
            "url": f"https://www.youtube.com/watch?v={vid}",
            "snippet": desc,
            "published": published,
            "query": query,
            "metrics": {"views": views, "likes": likes, "comments": comments},
            "engagement": engagement,
        }
        if src_attr:
            item["_source_attr"] = src_attr
        out.append(item)
    return out


def _yt_fetch_stats(video_ids: list) -> dict:
    """Second-pass videos.list call to get statistics for virality scoring."""
    import urllib.parse, urllib.request

    if not video_ids:
        return {}
    out = {}
    # videos.list accepts up to 50 IDs per call
    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i:i + 50]
        url = "https://www.googleapis.com/youtube/v3/videos?" + urllib.parse.urlencode({
            "part": "statistics",
            "id": ",".join(chunk),
            "key": os.environ["YOUTUBE_API_KEY"],
        })
        try:
            with urllib.request.urlopen(url, timeout=15) as resp:
                payload = json.loads(resp.read())
            for it in (payload.get("items") or []):
                vid = it.get("id")
                stats = it.get("statistics") or {}
                if vid:
                    out[vid] = stats
        except Exception as e:
            sys.stderr.write(f"diaspora-pulse: YouTube stats fetch failed: {e}\n")
    return out


def _yt_resolve_channel(handle: str):
    import urllib.parse, urllib.request

    if handle in _YT_CHANNEL_CACHE:
        return _YT_CHANNEL_CACHE[handle]

    clean = handle.lstrip("@")

    try:
        url = "https://www.googleapis.com/youtube/v3/channels?" + urllib.parse.urlencode({
            "part": "id",
            "forHandle": clean,
            "key": os.environ["YOUTUBE_API_KEY"],
        })
        with urllib.request.urlopen(url, timeout=15) as resp:
            payload = json.loads(resp.read())
        items = payload.get("items") or []
        if items:
            cid = items[0].get("id")
            if cid:
                _YT_CHANNEL_CACHE[handle] = cid
                return cid
    except Exception:
        pass

    try:
        url = "https://www.googleapis.com/youtube/v3/search?" + urllib.parse.urlencode({
            "part": "snippet",
            "q": clean,
            "type": "channel",
            "maxResults": 1,
            "key": os.environ["YOUTUBE_API_KEY"],
        })
        with urllib.request.urlopen(url, timeout=15) as resp:
            payload = json.loads(resp.read())
        items = payload.get("items") or []
        if items:
            cid = ((items[0].get("id") or {}).get("channelId")
                   or (items[0].get("snippet") or {}).get("channelId"))
            if cid:
                _YT_CHANNEL_CACHE[handle] = cid
                return cid
    except Exception:
        pass

    return None


# ---------------------------------------------------------------------------
# Reddit JSON (always-on, no auth required — just needs a UA header)
# ---------------------------------------------------------------------------
_REDDIT_UA = "diaspora-pulse/0.1 (by /u/diaspora-pulse)"


def _reddit_json_search(subreddit: str, topic: str, days: int, n: int,
                       query: str, trending: bool, src_attr: dict | None = None) -> list:
    """Pull posts from a subreddit via Reddit's free JSON endpoint.

    Topic mode     -> /search.json?q=TOPIC&restrict_sr=on&sort=new&t=week|month
    Trending mode  -> /hot.json?limit=N  (what's currently trending, no filter)

    Engagement = ups + num_comments*3 (comments weigh more than upvotes because
    they indicate deeper engagement, which better predicts virality).
    Posts older than the lookback window are dropped client-side.
    """
    import urllib.parse, urllib.request, time

    sub = subreddit.strip().strip("/")
    if not sub:
        return []
    base = f"https://www.reddit.com/r/{sub}"

    if trending and not topic:
        # Pure trending pull
        url = f"{base}/hot.json?limit={max(10, min(n * 2, 100))}"
    elif trending and topic:
        # Trending with soft topic boost — still use /search but with sort=hot
        t = "week" if days <= 7 else ("month" if days <= 31 else "year")
        qs = urllib.parse.urlencode({
            "q": topic, "restrict_sr": "on", "sort": "hot", "t": t, "limit": n,
        })
        url = f"{base}/search.json?{qs}"
    else:
        # Topic mode — keyword filter, sort by new
        t = "week" if days <= 7 else ("month" if days <= 31 else "year")
        qs = urllib.parse.urlencode({
            "q": topic, "restrict_sr": "on", "sort": "new", "t": t, "limit": n,
        })
        url = f"{base}/search.json?{qs}"

    req = urllib.request.Request(url, headers={
        "User-Agent": _REDDIT_UA,
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=20) as resp:
        payload = json.loads(resp.read())

    cutoff_ts = time.time() - (days * 86400) if days else None
    children = ((payload.get("data") or {}).get("children") or [])

    out = []
    for ch in children:
        d = (ch or {}).get("data") or {}
        created = d.get("created_utc")
        if cutoff_ts and created and created < cutoff_ts:
            continue
        title = (d.get("title") or "").strip()
        if not title:
            continue
        permalink = d.get("permalink") or ""
        post_url = f"https://www.reddit.com{permalink}" if permalink else d.get("url") or ""
        body = (d.get("selftext") or "").strip()
        snippet = body[:400] if body else (d.get("url") or "")
        ups = int(d.get("ups") or d.get("score") or 0)
        comments = int(d.get("num_comments") or 0)
        engagement = ups + comments * 3
        published = None
        if created:
            try:
                import datetime as dt
                published = dt.datetime.utcfromtimestamp(int(created)).date().isoformat()
            except Exception:
                pass

        item = {
            "title": title,
            "url": post_url,
            "snippet": snippet,
            "published": published,
            "query": query,
            "metrics": {"ups": ups, "comments": comments, "ratio": d.get("upvote_ratio")},
            "engagement": engagement,
        }
        if src_attr:
            item["_source_attr"] = src_attr
        out.append(item)

    # Sort by engagement so the caller sees the most viral first
    out.sort(key=lambda x: -x.get("engagement", 0))
    return out[:n]


# ---------------------------------------------------------------------------
# GDELT DOC API (always-on, no auth required)
# ---------------------------------------------------------------------------
def _gdelt_search(topic: str, days: int, trending: bool, max_results: int = 25) -> list:
    """Fire GDELT DOC API once as a supplementary broad news pass.

    GDELT indexes ~100k news sources in near-real-time. This catches breaking
    Ghana/diaspora stories from outlets NOT in the registry. Free, no key.

    Query construction:
      topic mode      -> "TOPIC" AND (ghana OR ghanaian OR "ghanaian diaspora")
      trending mode   -> (ghana OR ghanaian OR "ghanaian diaspora")
                         + optional soft topic boost
    """
    import urllib.parse, urllib.request

    # Clamp GDELT timespan — their API caps at ~14d per call for free tier
    timespan = f"{min(max(1, days), 14)}d"
    ghana_clause = '(ghana OR ghanaian OR "ghanaian diaspora")'
    if topic and not trending:
        gdelt_query = f'"{topic}" AND {ghana_clause}'
    elif topic and trending:
        gdelt_query = f'{topic} AND {ghana_clause}'
    else:
        gdelt_query = ghana_clause

    params = {
        "query": gdelt_query,
        "mode": "artlist",
        "format": "json",
        "sort": "hybridrel",   # relevance + recency
        "maxrecords": str(min(max_results, 75)),
        "timespan": timespan,
        "sourcelang": "eng",
    }
    url = "https://api.gdeltproject.org/api/v2/doc/doc?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "User-Agent": _REDDIT_UA,  # generic UA is fine
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=25) as resp:
        raw = resp.read()

    # GDELT sometimes returns non-JSON error pages; guard parse
    try:
        payload = json.loads(raw)
    except Exception as e:
        sys.stderr.write(f"diaspora-pulse: GDELT non-JSON response ({e}); first 200 bytes: {raw[:200]!r}\n")
        return []

    out = []
    for a in (payload.get("articles") or []):
        title = (a.get("title") or "").strip()
        url_ = (a.get("url") or "").strip()
        if not title or not url_:
            continue
        seen = a.get("seendate") or ""
        # seendate is like "20260422T143000Z" — split to YYYY-MM-DD
        published = None
        if len(seen) >= 8:
            try:
                published = f"{seen[0:4]}-{seen[4:6]}-{seen[6:8]}"
            except Exception:
                pass
        snippet = (a.get("domain") or "")
        if a.get("sourcecountry"):
            snippet = f"{snippet} · {a.get('sourcecountry')}"
        if a.get("language"):
            snippet = f"{snippet} · {a.get('language')}"

        out.append({
            "title": title,
            "url": url_,
            "snippet": snippet,
            "published": published,
            "query": f"gdelt:{gdelt_query}",
            # No engagement signal from GDELT; recency + weight will carry
            "engagement": 0,
        })
    return out


# ---------------------------------------------------------------------------
# NORMALIZATION + URL MATCHING (load-bearing)
# ---------------------------------------------------------------------------
def _normalize(items: list) -> list:
    seen = set()
    out = []
    for it in items:
        if not isinstance(it, dict):
            continue
        url = (it.get("url") or "").strip()
        title = (it.get("title") or "").strip()
        if not url or not title:
            continue
        key = url.split("#")[0]
        if key in seen:
            continue
        seen.add(key)
        matched = _match_source(url)
        pre = it.get("_source_attr") or {}
        # Prefer URL match; fall back to pre-stamped attribution from the
        # backend (used by YouTube where /watch?v=... URLs don't encode the channel).
        if matched:
            src_id = matched["id"]
            src_name = matched["name"]
            src_cat = matched["category"]
            src_weight = float(matched.get("weight", 1.0))
        elif pre.get("source_id"):
            src_id = pre.get("source_id")
            src_name = pre.get("source_name") or _host_only(url)
            src_cat = pre.get("category") or "web"
            src_weight = float(pre.get("weight") or 1.0)
        else:
            src_id = None
            src_name = _host_only(url)
            src_cat = "web"
            src_weight = 0.8
        item = {
            "title": title,
            "url": url,
            "snippet": (it.get("snippet") or "").strip(),
            "published": it.get("published"),
            "source_id": src_id,
            "source_name": src_name,
            "category": src_cat,
            "weight": src_weight,
            "query": it.get("query"),
            "metrics": it.get("metrics") or {},
            "engagement": int(it.get("engagement") or 0),
        }
        out.append(item)
    out.sort(key=lambda x: (-x["weight"], 0 if x.get("published") else 1, len(x["title"])))
    return out


def _match_source(url: str):
    host, path = _host_and_path(url)
    if not host:
        return None
    path_sources, host_sources = [], []
    for s in sources.ALL_SOURCES:
        d = (s.get("domain") or "").lower()
        if not d:
            continue
        (path_sources if "/" in d else host_sources).append(s)
    for s in path_sources:
        d = s["domain"].lower()
        d_host, _, d_path = d.partition("/")
        if host == d_host or host.endswith("." + d_host):
            if path.lstrip("/").lower().startswith(d_path.lower()):
                return s
    for s in host_sources:
        d = s["domain"].lower()
        if host == d or host.endswith("." + d):
            return s
    return None


def _host_and_path(url: str):
    try:
        p = urlparse(url)
        return (p.hostname or "").lower(), (p.path or "")
    except Exception:
        return "", ""


def _host_only(url: str) -> str:
    return _host_and_path(url)[0]
