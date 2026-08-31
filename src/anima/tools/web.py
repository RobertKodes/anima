"""Web fetch, crawl, and explore — gated by capability grants."""

from __future__ import annotations

import ipaddress
import re
import socket
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx

MAX_FETCH_BYTES = 512_000
MAX_CRAWL_PAGES = 8
MAX_CRAWL_DEPTH = 2
MAX_EXPLORE_LINKS = 24
USER_AGENT = "Anima/0.1 (+https://github.com/RobertKodes/anima)"


class _LinkParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__()
        self.base_url = base_url
        self.links: list[str] = []
        self.title = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self.links.append(urljoin(self.base_url, href))

    def handle_data(self, data: str) -> None:
        if not self.title and data.strip():
            self.title = data.strip()[:200]


def extract_url(text: str) -> str | None:
    match = re.search(r"https?://[^\s<>\"']+", text.strip())
    return match.group(0).rstrip(".,)") if match else None


def is_safe_url(url: str) -> tuple[bool, str]:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        return False, "only http and https URLs are allowed"
    host = parsed.hostname
    if not host:
        return False, "missing hostname"
    lowered = host.lower()
    if lowered in {"localhost", "127.0.0.1", "0.0.0.0", "::1"}:
        return False, "local addresses are blocked"
    if lowered.endswith(".local") or lowered.endswith(".internal"):
        return False, "local network hosts are blocked"
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False, "could not resolve hostname"
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            return False, "private or reserved addresses are blocked"
    return True, "ok"


def _html_to_text(html: str) -> str:
    text = re.sub(r"(?is)<script.*?>.*?</script>", " ", html)
    text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def fetch_url(url: str, *, max_bytes: int = MAX_FETCH_BYTES) -> dict[str, Any]:
    ok, reason = is_safe_url(url)
    if not ok:
        return {"ok": False, "url": url, "error": reason}
    try:
        with httpx.Client(timeout=20.0, follow_redirects=True, headers={"User-Agent": USER_AGENT}) as client:
            response = client.get(url)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            raw = response.content[:max_bytes]
            if "html" in content_type.lower():
                html = raw.decode(response.encoding or "utf-8", errors="replace")
                parser = _LinkParser(str(response.url))
                parser.feed(html)
                text = _html_to_text(html)[:8000]
                return {
                    "ok": True,
                    "url": str(response.url),
                    "status": response.status_code,
                    "content_type": content_type,
                    "title": parser.title,
                    "text": text,
                    "links": parser.links[:MAX_EXPLORE_LINKS],
                }
            text = raw.decode(response.encoding or "utf-8", errors="replace")[:8000]
            return {
                "ok": True,
                "url": str(response.url),
                "status": response.status_code,
                "content_type": content_type,
                "title": "",
                "text": text,
                "links": [],
            }
    except Exception as exc:
        return {"ok": False, "url": url, "error": str(exc)}


def crawl_site(url: str, *, max_pages: int = MAX_CRAWL_PAGES, max_depth: int = MAX_CRAWL_DEPTH) -> dict[str, Any]:
    seed_ok, reason = is_safe_url(url)
    if not seed_ok:
        return {"ok": False, "url": url, "error": reason}
    parsed_seed = urlparse(url)
    origin = f"{parsed_seed.scheme}://{parsed_seed.netloc}"
    seen: set[str] = set()
    queue: list[tuple[str, int]] = [(url, 0)]
    pages: list[dict[str, Any]] = []

    while queue and len(pages) < max_pages:
        current, depth = queue.pop(0)
        if current in seen:
            continue
        seen.add(current)
        page = fetch_url(current)
        if not page.get("ok"):
            continue
        pages.append(
            {
                "url": page["url"],
                "title": page.get("title") or "",
                "excerpt": (page.get("text") or "")[:400],
            }
        )
        if depth >= max_depth:
            continue
        for link in page.get("links") or []:
            parsed = urlparse(link)
            if parsed.scheme not in {"http", "https"}:
                continue
            if f"{parsed.scheme}://{parsed.netloc}" != origin:
                continue
            safe, _ = is_safe_url(link)
            if safe and link not in seen:
                queue.append((link, depth + 1))

    if not pages:
        return {"ok": False, "url": url, "error": "no pages could be fetched"}
    return {"ok": True, "seed": url, "pages": pages, "count": len(pages)}


def explore_site(url: str, *, max_links: int = MAX_EXPLORE_LINKS) -> dict[str, Any]:
    page = fetch_url(url)
    if not page.get("ok"):
        return page
    links: list[dict[str, str]] = []
    for link in (page.get("links") or [])[: max_links * 2]:
        safe, _ = is_safe_url(link)
        if not safe:
            continue
        label = urlparse(link).path.rstrip("/").split("/")[-1] or link
        links.append({"url": link, "label": label})
        if len(links) >= max_links:
            break
    return {
        "ok": True,
        "url": page["url"],
        "title": page.get("title") or "",
        "summary": (page.get("text") or "")[:1200],
        "links": links,
        "link_count": len(links),
    }


def format_fetch(result: dict[str, Any]) -> str:
    if not result.get("ok"):
        return f"Fetch failed for {result.get('url')}: {result.get('error')}"
    title = result.get("title") or "(no title)"
    text = result.get("text") or ""
    excerpt = text[:2000] + ("…" if len(text) > 2000 else "")
    return f"Fetched {result.get('url')}\nTitle: {title}\n\n{excerpt}"


def format_crawl(result: dict[str, Any]) -> str:
    if not result.get("ok"):
        return f"Crawl failed for {result.get('url')}: {result.get('error')}"
    lines = [f"Crawled {result.get('count')} page(s) from {result.get('seed')}:"]
    for page in result.get("pages") or []:
        lines.append(f"- {page.get('title') or page.get('url')}: {page.get('url')}")
        if page.get("excerpt"):
            lines.append(f"  {page['excerpt'][:180]}…")
    return "\n".join(lines)


def format_explore(result: dict[str, Any]) -> str:
    if not result.get("ok"):
        return f"Explore failed for {result.get('url')}: {result.get('error')}"
    lines = [
        f"Explored {result.get('url')}",
        f"Title: {result.get('title') or '(no title)'}",
        "",
        (result.get("summary") or "")[:1200],
        "",
        f"Links found ({result.get('link_count', 0)}):",
    ]
    for link in result.get("links") or []:
        lines.append(f"- {link.get('label')}: {link.get('url')}")
    return "\n".join(lines)
