import os
import json
import re
import time
import urllib.parse
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import httpx
from bs4 import BeautifulSoup

try:
    from ddgs import DDGS  # new package name
except ImportError:
    from duckduckgo_search import DDGS  # fallback for older installs

from research_agent.config import settings
from research_agent.models import ToolResult


class WebSearchTool:
    def __init__(self, limit: Optional[int] = None):
        self.limit = limit or settings.SEARCH_LIMIT

    def execute(self, query: str) -> ToolResult:
        """
        Executes a DuckDuckGo web search for a given query.
        Returns a formatted ToolResult containing search result summaries.
        """
        # 1. High-availability cache lookup (with recency check)
        cache_path = os.path.join(settings.BASE_DIR, "search_cache.json")
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    cache = json.load(f)
                cleaned_query = query.lower().strip().replace('"', '').replace("'", "")
                for cached_q, cached_items in cache.items():
                    cleaned_cached = cached_q.lower().strip().replace('"', '').replace("'", "")
                    if cleaned_cached in cleaned_query or cleaned_query in cleaned_cached:
                        if not cached_items:
                            return ToolResult(
                                tool_name="search_web",
                                success=True,
                                content="No search results were found for this query.",
                                url=None
                            )
                        formatted_results = []
                        for i, res in enumerate(cached_items[:self.limit]):
                            title = res.get("title", "Untitled")
                            href = res.get("href", "")
                            body = res.get("body", "")
                            formatted_results.append(
                                f"Result [{i+1}]:\nTitle: {title}\nURL: {href}\nSnippet: {body}\n"
                            )
                        return ToolResult(
                            tool_name="search_web",
                            success=True,
                            content="\n".join(formatted_results),
                            url=None
                        )
            except Exception:
                pass

        # 2. Live search with multi-backend fallbacks
        attempts = 0
        ddg_results = []
        last_error = None

        while attempts < 3:
            try:
                with DDGS() as ddgs:
                    ddg_results = list(ddgs.text(query, max_results=self.limit))

                    if not ddg_results:
                        time.sleep(0.5)
                        ddg_results = list(ddgs.text(query, backend="lite", max_results=self.limit))

                    if not ddg_results:
                        time.sleep(0.5)
                        ddg_results = list(ddgs.text(query, backend="html", max_results=self.limit))

                    if not ddg_results:
                        time.sleep(0.5)
                        ddg_results = list(ddgs.news(query, max_results=self.limit))
                        if ddg_results:
                            for res in ddg_results:
                                res["href"] = res.get("url", "")

                if ddg_results:
                    break
            except Exception as e:
                last_error = e

            attempts += 1
            if attempts < 3:
                time.sleep(0.5 * attempts)   # was 2.0 * attempts — much faster retry

        if not ddg_results:
            error_text = f"Search failed with error: {str(last_error)}" if last_error else "No search results were found for this query."
            return ToolResult(
                tool_name="search_web",
                success=last_error is None,
                content=error_text,
                url=None,
                error=str(last_error) if last_error else "Empty Results"
            )

        # Write back to cache
        try:
            cache = {}
            if os.path.exists(cache_path):
                with open(cache_path, "r", encoding="utf-8") as f:
                    cache = json.load(f)
            cache_items = [
                {"title": r.get("title", "Untitled"), "href": r.get("href", ""), "body": r.get("body", "")}
                for r in ddg_results
            ]
            cache[query] = cache_items
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

        formatted_results = []
        for i, res in enumerate(ddg_results):
            title = res.get("title", "Untitled")
            href = res.get("href", "")
            body = res.get("body", "")
            formatted_results.append(
                f"Result [{i+1}]:\nTitle: {title}\nURL: {href}\nSnippet: {body}\n"
            )

        return ToolResult(
            tool_name="search_web",
            success=True,
            content="\n".join(formatted_results),
            url=None
        )


class WebScraperTool:
    def __init__(self, timeout: Optional[int] = None):
        self.timeout = timeout or settings.TIMEOUT_SECONDS
        self.headers_list = [
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "DNT": "1"
            },
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-GB,en;q=0.9"
            }
        ]

    def _extract_text(self, html: str) -> str:
        """Parse HTML and extract clean readable text."""
        soup = BeautifulSoup(html, "html.parser")
        for tag in ["script", "style", "nav", "footer", "header", "form", "aside", "iframe", "button"]:
            for matched in soup.find_all(tag):
                matched.decompose()

        text_lines = []
        for item in soup.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
            text = item.get_text(strip=True)
            if len(text) > 10:
                if item.name.startswith("h"):
                    text_lines.append(f"\n### {text}\n")
                else:
                    text_lines.append(text)

        content_text = "\n".join(text_lines)
        content_text = re.sub(r'\n{3,}', '\n\n', content_text).strip()

        # Context-budget management: restrict output to MAX_SCRAPE_WORDS
        words = content_text.split()
        if len(words) > settings.MAX_SCRAPE_WORDS:
            content_text = " ".join(words[:settings.MAX_SCRAPE_WORDS]) + "\n\n[Content truncated by agent to stay within token budget...]"

        if not content_text:
            raw_text = soup.get_text(separator=' ')
            cleaned_raw = " ".join([w for w in raw_text.split() if len(w) < 40])
            content_text = cleaned_raw[:4000]

        return content_text

    def execute(self, url: str) -> ToolResult:
        """
        Fetches the content of a webpage and extracts clean readable text.
        Tries requests first, then falls back to httpx if blocked.
        Uses a scrape cache with TTL to avoid redundant network calls.
        """
        # Validate URL structure
        parsed = urllib.parse.urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return ToolResult(
                tool_name="fetch_webpage",
                success=False,
                content="Invalid URL structure provided.",
                url=url,
                error="Invalid URL"
            )

        # 1. High-availability scrape cache with 24h TTL
        scrape_cache_path = os.path.join(settings.BASE_DIR, "scrape_cache.json")
        if os.path.exists(scrape_cache_path):
            try:
                with open(scrape_cache_path, "r", encoding="utf-8") as f:
                    scrape_cache = json.load(f)
                if url in scrape_cache:
                    entry = scrape_cache[url]
                    # Check TTL: 24 hours = 86400 seconds
                    cached_ts = entry.get("timestamp", 0)
                    if time.time() - cached_ts < 86400:
                        return ToolResult(
                            tool_name="fetch_webpage",
                            success=True,
                            content=entry["content"],
                            url=url
                        )
            except Exception:
                pass

        content_text = ""
        try:
            # Primary: requests
            headers = self.headers_list[0]
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            content_text = self._extract_text(response.text)
        except requests.exceptions.Timeout:
            return ToolResult(
                tool_name="fetch_webpage",
                success=False,
                content="Webpage request timed out.",
                url=url,
                error="Timeout Error"
            )
        except requests.exceptions.HTTPError as he:
            status = he.response.status_code
            # Try httpx fallback on 403/blocked pages
            if status == 403:
                try:
                    with httpx.Client(timeout=self.timeout, follow_redirects=True,
                                      headers=self.headers_list[1]) as client:
                        resp = client.get(url)
                        resp.raise_for_status()
                        content_text = self._extract_text(resp.text)
                except Exception:
                    return ToolResult(
                        tool_name="fetch_webpage",
                        success=False,
                        content=f"HTTP {status}: Page is blocked or access denied.",
                        url=url,
                        error=f"HTTP Error {status}"
                    )
            else:
                return ToolResult(
                    tool_name="fetch_webpage",
                    success=False,
                    content=f"HTTP Request failed: {status} - {he.response.reason}",
                    url=url,
                    error=f"HTTP Error {status}"
                )
        except Exception as e:
            # Try httpx as fallback on any other failure
            try:
                with httpx.Client(timeout=self.timeout, follow_redirects=True,
                                  headers=self.headers_list[1]) as client:
                    resp = client.get(url)
                    resp.raise_for_status()
                    content_text = self._extract_text(resp.text)
            except Exception:
                return ToolResult(
                    tool_name="fetch_webpage",
                    success=False,
                    content=f"Failed to scrape webpage: {str(e)}",
                    url=url,
                    error=str(e)
                )

        if not content_text:
            return ToolResult(
                tool_name="fetch_webpage",
                success=False,
                content="Page returned empty content.",
                url=url,
                error="Empty Content"
            )

        # Write to scrape cache
        try:
            scrape_cache = {}
            if os.path.exists(scrape_cache_path):
                with open(scrape_cache_path, "r", encoding="utf-8") as f:
                    scrape_cache = json.load(f)
            scrape_cache[url] = {
                "content": content_text,
                "timestamp": time.time()
            }
            with open(scrape_cache_path, "w", encoding="utf-8") as f:
                json.dump(scrape_cache, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

        return ToolResult(
            tool_name="fetch_webpage",
            success=True,
            content=content_text,
            url=url
        )


def scrape_urls_parallel(urls: List[str], timeout: Optional[int] = None, max_workers: int = 3) -> dict:
    """
    Scrapes multiple URLs in parallel using a ThreadPoolExecutor.
    Returns a dict mapping url -> ToolResult.
    """
    scraper = WebScraperTool(timeout=timeout)
    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(scraper.execute, url): url for url in urls}
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                results[url] = future.result()
            except Exception as e:
                results[url] = ToolResult(
                    tool_name="fetch_webpage",
                    success=False,
                    content=f"Parallel scrape failed: {str(e)}",
                    url=url,
                    error=str(e)
                )
    return results
