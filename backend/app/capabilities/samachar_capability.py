"""
samachar_capability.py — Registered Samachar News & Retrieval Capability
Provides structured media & news intelligence retrieval for MITRA.
"""
from __future__ import annotations
import os
import logging
import re
import httpx
from datetime import datetime
from typing import Any, Dict, List, Optional
from app.capabilities.base_capability import BaseCapability, CapabilityResult

logger = logging.getLogger(__name__)

class SamacharCapability(BaseCapability):
    """
    Samachar capability participant contract.
    Retrieves current news, headlines, and structured media context by calling
    the external Samachar News-AI Service API.
    """
    def __init__(self) -> None:
        super().__init__()
        # Retrieve the Samachar API base URL from the environment or default to localhost:8001
        self.api_url = os.getenv("SAMACHAR_API_URL", "http://localhost:8001/api/unified-news-workflow")

    @property
    def name(self) -> str:
        return "samachar"

    @property
    def description(self) -> str:
        return "Retrieves structured news, headlines, articles, and media intelligence."

    @property
    def supported_intents(self) -> List[str]:
        return ["news", "samachar", "headlines", "articles", "press", "media"]

    async def execute(self, intent: str, params: Dict[str, Any], trace_id: Optional[str] = None) -> CapabilityResult:
        query = params.get("message") or params.get("query") or "latest news"
        user_id = params.get("user_id", "anonymous")

        logger.info("Executing Samachar capability query='%s' user_id=%s trace_id=%s", query, user_id, trace_id)

        # 1. Identify or search for a URL
        url = self._extract_url(query)
        if not url:
            url = await self._search_first_url(query)

        if not url:
            logger.warning("[SAMACHAR RESOLUTION] No relevant individual article URL found for query='%s'", query)
            return CapabilityResult(
                capability=self.name,
                intent=intent,
                status="failed",
                summary=f"No relevant live news article URL could be resolved for query: '{query}'. Please paste a direct article link.",
                data={
                    "capability": "samachar",
                    "query": query,
                    "result": f"📰 SAMACHAR NEWS SEARCH UNAVAILABLE\n\nUnable to resolve a live article URL for query: '{query}'. Please paste a direct news article link or try again."
                },
                trace_id=trace_id
            )

        logger.info("[SAMACHAR DEBUG] query='%s' -> resolved_url='%s'", query, url)

        try:
            # 2. Consume the canonical Samachar capability contract via HTTP POST
            async with httpx.AsyncClient(timeout=25.0) as client:
                response = await client.post(
                    self.api_url,
                    json={"url": url},
                    headers={"Content-Type": "application/json"}
                )
                
                logger.info("[SAMACHAR DEBUG] Samachar API status_code=%d for url='%s'", response.status_code, url)

                if response.status_code != 200:
                    raise Exception(f"HTTP {response.status_code}: {response.text}")
                
                res_body = response.json()
                if not res_body.get("success"):
                    raise Exception(res_body.get("message") or "Workflow failed on Samachar service")
                
                workflow_data = res_body.get("data", {})
                scraped = workflow_data.get("scraped_data", {})
                vetting = workflow_data.get("vetting_results", {})
                summary = workflow_data.get("summary", {})
                brief_desc = workflow_data.get("brief_description", "")
                
                # 3. Format structured response to fulfill MITRA's rendering expectations
                title = scraped.get("title") or "News Article"
                author = scraped.get("author") or "Unknown"
                if isinstance(author, dict):
                    author = author.get("name") or "Unknown"
                date_published = scraped.get("date") or "N/A"
                category = scraped.get("category") or "general"
                summary_text = summary.get("text") or brief_desc or "No summary extracted."
                authenticity_score = vetting.get("authenticity_score") or 0
                credibility_rating = vetting.get("credibility_rating") or "Unknown"
                
                report = (
                    f"📰 TITLE: {title}\n"
                    f"🏷️ CATEGORY: {category.upper()}\n"
                    f"✍️ AUTHOR: {author}\n"
                    f"📅 DATE: {date_published}\n"
                    f"🛡️ CREDIBILITY: {credibility_rating} (Score: {authenticity_score}/100)\n\n"
                    f"📝 SUMMARY:\n{summary_text}"
                )
                
                logger.info("[SAMACHAR DEBUG] Transformed MITRA Response:\n%s", report[:300])

                data = {
                    "capability": "samachar",
                    "version": "2.0.0",
                    "query": query,
                    "url": url,
                    "result": report,
                    "retrieved_at": datetime.now().isoformat(),
                    "scraped_data": scraped,
                    "vetting_results": vetting,
                    "summary": summary
                }
                
                return CapabilityResult(
                    capability=self.name,
                    intent=intent,
                    status="success",
                    summary=f"Retrieved news intelligence for '{query}' from Samachar.",
                    data=data,
                    trace_id=trace_id
                )
                
        except Exception as exc:
            logger.error("Samachar capability HTTP request failed: %s", exc)
            return CapabilityResult.error_result(
                capability=self.name,
                intent=intent,
                error=f"Samachar retrieval failed: {str(exc)}",
                trace_id=trace_id
            )

    def _extract_url(self, text: str) -> str | None:
        url_match = re.search(r'(https?://[^\s]+)', text)
        return url_match.group(1) if url_match else None

    @staticmethod
    def _is_individual_article_url(url: str) -> bool:
        """Validate whether a candidate URL points to a specific individual article rather than a portal homepage."""
        import urllib.parse
        parsed = urllib.parse.urlparse(url)
        path = parsed.path.rstrip('/')
        if not path or path in ('/news', '/sport', '/home', '/about', '/section', '/mumbai', '/world', '/india'):
            return False
        segments = [s for s in path.split('/') if s]
        if len(segments) >= 2 or re.search(r'\d{4,}', path) or re.search(r'\.(html|ece|cms|story|article)$', path) or path.count('-') >= 2:
            return True
        return False

    async def _search_first_url(self, query: str) -> str | None:
        """
        Dynamically resolve natural-language news query to a semantically relevant individual article URL.
        Logs: original query, generated search query, provider status, candidates, selected URL, and selection reason.
        """
        import urllib.parse
        import xml.etree.ElementTree as ET
        from bs4 import BeautifulSoup

        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"}
        
        # 1. Primary Provider: Bing News RSS
        encoded_query = urllib.parse.quote(query)
        bing_rss_url = f"https://www.bing.com/news/search?q={encoded_query}&format=rss"
        logger.info("[SAMACHAR RESOLUTION] Original Query: '%s' | Generated Search Query: '%s' | Provider: Bing News RSS (%s)", query, query, bing_rss_url)
        
        candidates = []
        try:
            async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
                res = await client.get(bing_rss_url, headers=headers)
                logger.info("[SAMACHAR RESOLUTION] Bing News RSS HTTP Status: %d", res.status_code)
                if res.status_code == 200:
                    root = ET.fromstring(res.text)
                    items = root.findall('.//item')
                    for item in items:
                        link_node = item.find('link')
                        title_node = item.find('title')
                        if link_node is not None and link_node.text:
                            raw_link = link_node.text.strip()
                            title = title_node.text.strip() if title_node is not None else ""
                            parsed_link = urllib.parse.urlparse(raw_link)
                            qs = urllib.parse.parse_qs(parsed_link.query)
                            real_url = qs['url'][0] if 'url' in qs else raw_link
                            candidates.append((title, real_url))
        except Exception as exc:
            logger.warning("[SAMACHAR RESOLUTION] Bing News RSS error: %s", exc)

        logger.info("[SAMACHAR RESOLUTION] Candidate URLs Found (%d): %s", len(candidates), [c[1] for c in candidates[:5]])

        # Evaluate candidate URLs against individual article criteria
        for title, cand_url in candidates:
            if self._is_individual_article_url(cand_url):
                logger.info("[SAMACHAR RESOLUTION] Selected URL: '%s' | Reason: Matches individual article criteria for title '%s'", cand_url, title)
                return cand_url

        # 2. Secondary Provider: DuckDuckGo HTML Search
        ddg_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        logger.info("[SAMACHAR RESOLUTION] Falling back to Secondary Provider: DuckDuckGo HTML (%s)", ddg_url)
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.get(ddg_url, headers=headers)
                logger.info("[SAMACHAR RESOLUTION] DuckDuckGo HTTP Status: %d", res.status_code)
                if res.status_code == 200:
                    soup = BeautifulSoup(res.text, 'html.parser')
                    links = soup.find_all('a', class_='result__url')
                    for link in links:
                        href = link.get('href', '')
                        if href:
                            parsed = urllib.parse.urlparse(href)
                            qs = urllib.parse.parse_qs(parsed.query)
                            candidate = qs['uddg'][0] if 'uddg' in qs else href
                            if self._is_individual_article_url(candidate):
                                logger.info("[SAMACHAR RESOLUTION] Selected URL: '%s' | Reason: DuckDuckGo individual article result", candidate)
                                return candidate
        except Exception as exc:
            logger.warning("[SAMACHAR RESOLUTION] DuckDuckGo error: %s", exc)

        # Provider failed or no valid article found -> Return None for controlled failure response
        logger.warning("[SAMACHAR RESOLUTION] Selection Reason: Search providers returned no valid individual article URLs for query '%s'", query)
        return None
