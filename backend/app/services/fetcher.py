"""Content fetchers for each supported source type. Currently only RSS/Atom is implemented."""
from dataclasses import dataclass
from datetime import datetime, timezone

import feedparser


@dataclass
class FetchedItem:
    """Normalised representation of a single piece of content from any source type."""
    external_id: str
    url: str
    title: str
    content: str
    published_at: datetime | None


def fetch_rss(url: str) -> list[FetchedItem]:
    """Parse an RSS/Atom feed at `url` and return all entries as FetchedItems."""
    feed = feedparser.parse(url)
    items: list[FetchedItem] = []
    for entry in feed.entries:
        content = ""
        if hasattr(entry, "content"):
            content = entry.content[0].value
        elif hasattr(entry, "summary"):
            content = entry.summary

        published_at = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)

        items.append(FetchedItem(
            external_id=entry.get("id", entry.get("link", "")),
            url=entry.get("link", ""),
            title=entry.get("title", ""),
            content=content,
            published_at=published_at,
        ))
    return items


def fetch_source(source_type: str, url: str) -> list[FetchedItem]:
    """Dispatch to the correct fetcher based on `source_type`. Raises NotImplementedError for unsupported types."""
    if source_type == "rss":
        return fetch_rss(url)
    raise NotImplementedError(f"Source type '{source_type}' not yet implemented")
