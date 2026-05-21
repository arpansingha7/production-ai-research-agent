import os
import json
import re
import urllib.parse
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

from research_agent.config import settings
from research_agent.models import ToolResult

class WebSearchTool:
    def __init__(self, limit: Optional[int] = None):
        self.limit = limit or settings.SEARCH_LIMIT

    def execute(self, query: str) -> ToolResult:
        """
        Executes a Google/DuckDuckGo web search for a given query.
        Returns a formatted ToolResult containing search result summaries.
        """
        import time
        attempts = 0
        ddg_results = []
        last_error = None
        
        # 1. High Availability Cache lookup
        cache_path = os.path.join(settings.BASE_DIR, "search_cache.json")
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    cache = json.load(f)
                cleaned_query = query.lower().strip().replace('"', '').replace("'", "")
                for cached_q, cached_items in cache.items():
                    cleaned_cached = cached_q.lower().strip().replace('"', '').replace("'", "")
                    if cleaned_cached in cleaned_query or cleaned_query in cleaned_cached:
                        if not cached_items:  # Explicit empty cache means no results found (e.g. edge-case mock)
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
            except Exception as e:
                # Silently ignore cache reading errors and fallback to live search
                pass

        # 2. Live search with multi-backend fallbacks
        while attempts < 3:
            try:
                ddgs = DDGS()
                # First try standard text search
                ddg_results = list(ddgs.text(query, max_results=self.limit))
                
                # Fallback to lite backend if empty
                if not ddg_results:
                    time.sleep(1.0)
                    ddg_results = list(ddgs.text(query, backend="lite", max_results=self.limit))
                    
                # Fallback to html backend if empty
                if not ddg_results:
                    time.sleep(1.0)
                    ddg_results = list(ddgs.text(query, backend="html", max_results=self.limit))
                
                # Fallback to news search if still empty
                if not ddg_results:
                    time.sleep(1.0)
                    ddg_results = list(ddgs.news(query, max_results=self.limit))
                    if ddg_results:
                        for res in ddg_results:
                            res["href"] = res.get("url", "")
                            res["body"] = res.get("body", "")
                
                if ddg_results:
                    break
            except Exception as e:
                last_error = e
            
            attempts += 1
            if attempts < 3:
                time.sleep(2.0 * attempts)
                
        if not ddg_results:
            error_text = f"Search failed with error: {str(last_error)}" if last_error else "No search results were found for this query."
            return ToolResult(
                tool_name="search_web",
                success=last_error is None,
                content=error_text,
                url=None,
                error=str(last_error) if last_error else "Empty Results"
            )
            
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

    def execute(self, url: str) -> ToolResult:
        """
        Fetches the content of a webpage and extracts clean readable text.
        Filters out scripts, styles, navigations, footers to reduce token overhead.
        Truncates the output to a safe context budget.
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

        # Rotate headers to reduce risk of cloudflare/scraping blocks
        headers = self.headers_list[0]
        
        try:
            response = requests.get(url, headers=headers, timeout=self.timeout)
            
            # Catch standard HTTP errors (e.g. 403, 404, 500)
            response.raise_for_status()
            
            html = response.text
            soup = BeautifulSoup(html, "html.parser")
            
            # Remove promotional or interactive clutter
            for tag in ["script", "style", "nav", "footer", "header", "form", "aside", "iframe", "button"]:
                for matched in soup.find_all(tag):
                    matched.decompose()
            
            # Extract content cleanly
            text_lines = []
            for item in soup.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
                text = item.get_text(strip=True)
                if len(text) > 10:  # Avoid single character elements
                    if item.name.startswith("h"):
                        text_lines.append(f"\n### {text}\n")
                    else:
                        text_lines.append(text)
            
            content_text = "\n".join(text_lines)
            content_text = re.sub(r'\n{3,}', '\n\n', content_text).strip()
            
            # Context-budget management: restrict output to max 3000 words
            words = content_text.split()
            if len(words) > 3000:
                self.logger_warning_triggered = True # Can trace truncation
                content_text = " ".join(words[:3000]) + "\n\n[Content truncated by agent to stay within token budget...]"
            
            if not content_text:
                # If structured parsing failed, attempt a raw fallback
                raw_text = soup.get_text(separator=' ')
                cleaned_raw = " ".join([w for w in raw_text.split() if len(w) < 40]) # Strip extremely long tokens
                content_text = cleaned_raw[:6000]
                
            return ToolResult(
                tool_name="fetch_webpage",
                success=True,
                content=content_text if content_text else "Empty page content retrieved.",
                url=url
            )
            
        except requests.exceptions.Timeout:
            return ToolResult(
                tool_name="fetch_webpage",
                success=False,
                content="Webpage request timed out.",
                url=url,
                error="Timeout Error"
            )
        except requests.exceptions.HTTPError as he:
            return ToolResult(
                tool_name="fetch_webpage",
                success=False,
                content=f"HTTP Request failed: {he.response.status_code} - {he.response.reason}",
                url=url,
                error=f"HTTP Error {he.response.status_code}"
            )
        except Exception as e:
            return ToolResult(
                tool_name="fetch_webpage",
                success=False,
                content=f"Failed to scrape webpage: {str(e)}",
                url=url,
                error=str(e)
            )
