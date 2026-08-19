"""
search_tool.py — Mitra High-Speed Real-Time Web & Live Data Engine

Provides real-time web search, structured weather data, live stock prices,
and news context for LLM synthesis.
"""
from __future__ import annotations

import logging
import os
import re
import urllib.parse
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class SearchTool:
    """
    Real-time Live Finance, Weather & Web Search Engine.
    Fetches clean data for LLM context synthesis.
    """

    async def run(self, query: str) -> str:
        query_str = (query or "").strip()
        if not query_str:
            return "No search query provided."

        query_lower = query_str.lower()

        # 1. Check for weather queries
        weather_keywords = ["weather", "temperature", "forecast", "climate", "rain", "drizzle", "sun", "aqi"]
        if any(kw in query_lower for kw in weather_keywords):
            weather_data = await self._fetch_live_weather(query_str)
            if weather_data:
                return weather_data

        # 2. Check for financial ticker queries
        financial_keywords = [
            "stock", "share", "market", "sensex", "nifty", "bse", "nse", "hdfc", "reliance",
            "tcs", "infosys", "sbi", "icici", "tata", "apple", "tesla", "microsoft", "google",
            "price", "finance", "dow", "s&p", "ticker", "nasdaq", "gold", "silver", "crypto",
            "bitcoin", "btc", "eth", "inr", "usd", "forex", "rbi", "fed"
        ]
        if any(kw in query_lower for kw in financial_keywords):
            market_data = await self._fetch_live_finance(query_str)
            if market_data:
                return market_data

        # 3. Try Tavily API if configured
        tavily_key = os.getenv("TAVILY_API_KEY", "").strip()
        if tavily_key:
            try:
                tavily_res = await self._search_tavily(query_str, tavily_key)
                if tavily_res:
                    return tavily_res
            except Exception as e:
                logger.warning("Tavily search failed, falling back to DuckDuckGo: %s", e)

        # 4. Fallback to real-time DuckDuckGo Web Search
        try:
            ddg_res = await self._search_ddg(query_str)
            if ddg_res:
                return ddg_res
        except Exception as e:
            logger.warning("DuckDuckGo search failed: %s", e)

        return f"Real-time query completed for: '{query_str}'."

    async def _fetch_live_weather(self, query: str) -> Optional[str]:
        """Fetch clean structured weather data using wttr.in JSON API."""
        try:
            import httpx
            # Extract city name heuristic (default to Mumbai if mentioned or fallback)
            words = query.strip().split()
            city = "Mumbai"
            for w in words:
                clean_w = re.sub(r"[^\w]", "", w)
                if clean_w.lower() not in ("how", "is", "the", "weather", "today", "tomorrow", "forecast", "in", "at", "for"):
                    city = clean_w
                    break

            url = f"https://wttr.in/{urllib.parse.quote(city)}?format=j1"
            async with httpx.AsyncClient(timeout=4.0, follow_redirects=True) as client:
                resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
                if resp.status_code == 200:
                    data = resp.json()
                    curr = data.get("current_condition", [{}])[0]
                    nearest = data.get("nearest_area", [{}])[0]
                    area_name = nearest.get("areaName", [{}])[0].get("value", city)
                    country = nearest.get("country", [{}])[0].get("value", "")

                    temp_c = curr.get("temp_C", "N/A")
                    feels_like_c = curr.get("FeelsLikeC", "N/A")
                    desc = curr.get("weatherDesc", [{}])[0].get("value", "Clear")
                    humidity = curr.get("humidity", "N/A")
                    wind_speed = curr.get("windspeedKmph", "N/A")

                    return (
                        f"Live Weather Data for {area_name}, {country}:\n"
                        f"- Condition: {desc}\n"
                        f"- Temperature: {temp_c}°C (Feels like: {feels_like_c}°C)\n"
                        f"- Humidity: {humidity}%\n"
                        f"- Wind Speed: {wind_speed} km/h"
                    )
        except Exception as exc:
            logger.warning("Live weather API lookup failed: %s", exc)
        return None

    async def _fetch_live_finance(self, query: str) -> Optional[str]:
        """Fetch live ticker prices from Yahoo Finance API."""
        symbol_map = {
            "sensex": "^BSESN", "nifty": "^NSEI", "hdfc": "HDFCBANK.NS",
            "reliance": "RELIANCE.NS", "infosys": "INFY.NS", "tcs": "TCS.NS",
            "icici": "ICICIBANK.NS", "sbi": "SBIN.NS", "tatamotors": "TATAMOTORS.NS",
            "tata": "TATAMOTORS.NS", "apple": "AAPL", "tesla": "TSLA",
            "microsoft": "MSFT", "google": "GOOGL", "btc": "BTC-USD",
            "bitcoin": "BTC-USD", "eth": "ETH-USD", "gold": "GC=F", "silver": "SI=F"
        }
        q_lower = query.lower()
        symbol = None
        name = query

        for key, sym in symbol_map.items():
            if key in q_lower:
                symbol = sym
                name = key.upper()
                break

        if not symbol:
            clean_word = query.strip().split()[0].upper()
            if len(clean_word) <= 5 and clean_word.isalpha():
                symbol = clean_word
                name = clean_word

        if not symbol:
            return None

        try:
            import httpx
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1d"
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
                if resp.status_code == 200:
                    data = resp.json()
                    result = data.get("chart", {}).get("result", [{}])[0]
                    meta = result.get("meta", {})
                    current_price = meta.get("regularMarketPrice")
                    prev_close = meta.get("chartPreviousClose") or meta.get("previousClose")
                    currency = meta.get("currency", "USD")
                    long_name = meta.get("longName") or meta.get("shortName") or name

                    if current_price and prev_close:
                        diff = round(current_price - prev_close, 2)
                        pct = round((diff / prev_close) * 100, 2)
                        direction = "UP" if diff >= 0 else "DOWN"
                        symbol_str = "+" if diff >= 0 else ""
                        return (
                            f"Live Financial Ticker ({long_name} / {symbol}):\n"
                            f"- Current Price: {currency} {current_price:.2f}\n"
                            f"- Change Today: {direction} {symbol_str}{diff:.2f} ({symbol_str}{pct:.2f}%)\n"
                            f"- Previous Close: {currency} {prev_close:.2f}"
                        )
        except Exception as e:
            logger.warning("Live Yahoo Finance lookup failed for %s: %s", symbol, e)
        return None

    async def _search_tavily(self, query: str, api_key: str) -> Optional[str]:
        """Call Tavily API for clean web search context."""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": api_key,
                        "query": query,
                        "search_depth": "basic",
                        "max_results": 4
                    }
                )
                if resp.status_code == 200:
                    results = resp.json().get("results", [])
                    if results:
                        snippets = [
                            f"- {r.get('title')}: {self._clean_text(r.get('content', ''))}"
                            for r in results[:4]
                        ]
                        return "Live Web Search Context:\n" + "\n".join(snippets)
        except Exception as e:
            logger.warning("Tavily API call failed: %s", e)
        return None

    async def _search_ddg(self, query: str) -> Optional[str]:
        """Real-time DuckDuckGo web search fallback."""
        try:
            import httpx
            from bs4 import BeautifulSoup
            encoded = urllib.parse.quote(query)
            url = f"https://html.duckduckgo.com/html/?q={encoded}"
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    results = soup.find_all("a", class_="result__snippet")
                    snippets = []
                    for r in results[:4]:
                        text = self._clean_text(r.get_text())
                        if text:
                            snippets.append(f"- {text}")
                    if snippets:
                        return "Live Web Search Context:\n" + "\n".join(snippets)
        except Exception as e:
            logger.warning("DuckDuckGo search failed: %s", e)
        return None

    @staticmethod
    def _clean_text(text: str) -> str:
        """Strip HTML tags, raw pipe table syntax, timestamp IDs, and extra whitespace."""
        if not text:
            return ""
        # Remove script and style elements
        t = re.sub(r"<script.*?>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
        t = re.sub(r"<style.*?>.*?</style>", "", t, flags=re.DOTALL | re.IGNORECASE)
        t = re.sub(r"<.*?>", " ", t)
        # Remove table pipe dividers like | 58% | 59% |
        t = re.sub(r"\|\s*", " ", t)
        # Remove 8+ digit numeric timestamp IDs like 125735712
        t = re.sub(r"\b\d{8,}\b", "", t)
        # Normalize whitespace
        t = re.sub(r"\s+", " ", t).strip()
        return t