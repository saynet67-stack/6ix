import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import aiohttp
import asyncio
import wavelink
from config import YOUTUBE_API_KEY

YT_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"


async def yt_api_search(query, max_results=7):
    if not YOUTUBE_API_KEY:
        return []
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "videoEmbeddable": "true",
        "videoSyndicated": "true",
        "maxResults": max_results,
        "key": YOUTUBE_API_KEY,
    }
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as s:
            async with s.get(YT_SEARCH_URL, params=params) as r:
                if r.status != 200:
                    return []
                data = await r.json()
    except Exception as e:
        print(f"[YTAPI] search err: {e}")
        return []

    out = []
    for it in data.get("items", []):
        vid = it.get("id", {}).get("videoId")
        if not vid:
            continue
        sn = it.get("snippet", {}) or {}
        th = sn.get("thumbnails", {}) or {}
        thumb = (th.get("high") or th.get("medium") or th.get("default") or {}).get("url")
        out.append({
            "id": vid,
            "title": sn.get("title", "Unknown"),
            "author": sn.get("channelTitle", "Unknown"),
            "url": f"https://www.youtube.com/watch?v={vid}",
            "thumbnail": thumb,
        })
    return out


async def _resolve(url):
    try:
        tracks = await wavelink.Playable.search(url)
        return _first(tracks)
    except Exception as e:
        print(f"[YTAPI] resolve err: {e}")
    return None


def _first(tracks):
    if not tracks:
        return None
    try:
        if hasattr(tracks, 'tracks') and tracks.tracks:
            return tracks.tracks[0]
        return tracks[0]
    except Exception:
        return None


def _to_list(tracks, limit=None):
    try:
        if hasattr(tracks, 'tracks') and tracks.tracks:
            items = tracks.tracks
        else:
            items = list(tracks)
    except Exception:
        items = []
    if limit:
        items = items[:limit]
    return items


async def search_one(query):
    for source in ("ytsearch", "ytmsearch"):
        try:
            tracks = await asyncio.wait_for(
                wavelink.Playable.search(query, source=source), timeout=10
            )
            t = _first(tracks)
            if t:
                print(f"[SEARCH] OK '{query}' -> {t.title}")
                return t
        except asyncio.TimeoutError:
            print(f"[SEARCH] timeout '{query}' source={source}")
        except Exception as e:
            print(f"[SEARCH] err '{query}' source={source}: {e}")
    try:
        results = await yt_api_search(query, 5)
        for r in results:
            t = await _resolve(r["url"])
            if t:
                return t
    except Exception as e:
        print(f"[YTAPI] fallback err: {e}")
    return None


async def search_many(query, limit=7):
    try:
        tracks = await asyncio.wait_for(
            wavelink.Playable.search(query, source="ytsearch"), timeout=10
        )
        out = _to_list(tracks, limit)
        if out:
            return out
    except asyncio.TimeoutError:
        print(f"[SEARCH] timeout '{query}'")
    except Exception as e:
        print(f"[SEARCH] err '{query}': {e}")
    try:
        results = await yt_api_search(query, limit)
        out = []
        for r in results:
            t = await _resolve(r["url"])
            if t:
                out.append(t)
        return out
    except Exception as e:
        print(f"[YTAPI] fallback err: {e}")
    return []