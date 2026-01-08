import time
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import feedparser
from feedgen.feed import FeedGenerator

ROOT = Path(__file__).parent
FEEDS_TXT = ROOT / "feeds.txt"
OUTPUT = ROOT / "combined.xml"

MAX_ITEMS = 100

def entry_datetime(e):
    for key in ("published_parsed", "updated_parsed", "created_parsed"):
        t = e.get(key)
        if t:
            return datetime.fromtimestamp(time.mktime(t), tz=timezone.utc)
    return datetime.now(timezone.utc)

def stable_id(entry):
    base = entry.get("id") or (entry.get("link", "") + entry.get("title", ""))
    return hashlib.sha1(base.encode("utf-8")).hexdigest()

def load_feeds():
    return [
        line.strip()
        for line in FEEDS_TXT.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

def main():
    feed_urls = load_feeds()
    items = []

    for url in feed_urls:
        d = feedparser.parse(url)
        for e in getattr(d, "entries", []):
            items.append((entry_datetime(e), url, e))

    items.sort(key=lambda x: x[0], reverse=True)
    items = items[:MAX_ITEMS]

    fg = FeedGenerator()
    fg.title("Combined Feed")
    fg.description("Merged RSS feed generated via GitHub Actions + GitHub Pages")
    fg.language("en")

    # Set "self" link to where combined.xml will live on GitHub Pages
    # This is a best-effort default; you can customize later.
    fg.link(href="combined.xml", rel="self")

    seen = set()
    for dt, source_url, e in items:
        sid = stable_id(e)
        if sid in seen:
            continue
        seen.add(sid)

        fe = fg.add_entry()
        fe.id(sid)
        fe.title(e.get("title", "(no title)"))
        if e.get("link"):
            fe.link(href=e.link)
        fe.published(dt)

        summary = e.get("summary") or e.get("description") or ""
        if summary:
            fe.summary(summary)

        fe.category(term=source_url)

    fg.rss_file(str(OUTPUT))
    print(f"Wrote {OUTPUT}")

if __name__ == "__main__":
    main()
