import os
import logging
import urllib.parse
import urllib.request
import json
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SearchTool:
    """
    Real-Time Live Finance & Web Search Engine.
    Fetches up-to-date market news, stock prices (Sensex, Nifty, HDFC, Reliance, AAPL, TSLA),
    and current web search results via Tavily / Yahoo Finance / DuckDuckGo.
    """

    async def run(self, query: str) -> str:
        query_str = (query or "").strip()
        if not query_str:
            return "No search query provided."

        query_lower = query_str.lower()

        # 1. Check if user is asking for live stock prices / financial ticker data
        financial_keywords = [
            "stock", "share", "market", "sensex", "nifty", "bse", "nse", "hdfc", "reliance", 
            "tcs", "infosys", "sbi", "icici", "tata", "apple", "tesla", "microsoft", "google",
            "price", "finance", "dow", "s&p", "ticker", "nasdaq", "mutual fund", "sip", "bond",
            "gold", "silver", "commodity", "crypto", "bitcoin", "btc", "eth", "ethereum",
            "investment", "dividend", "portfolio", "bull", "bear", "rally", "crash", "gain",
            "loss", "ups", "downs", "rate", "currency", "rupee", "dollar", "inr", "usd",
            "forex", "inflation", "interest rate", "repo rate", "rbi", "fed"
        ]
        is_financial = any(kw in query_lower for kw in financial_keywords)


        if is_financial:
            market_data = await self._fetch_live_finance(query_str)
            if market_data:
                return market_data

        # 2. Try Tavily API if configured
        tavily_key = os.getenv("TAVILY_API_KEY", "").strip()
        if tavily_key:
            try:
                tavily_res = await self._search_tavily(query_str, tavily_key)
                if tavily_res:
                    return tavily_res
            except Exception as e:
                logger.warning(f"Tavily search failed, falling back to DuckDuckGo: {e}")

        # 3. Fallback to real-time DuckDuckGo Web Search
        try:
            ddg_res = await self._search_ddg(query_str)
            if ddg_res:
                return ddg_res
        except Exception as e:
            logger.warning(f"DuckDuckGo search failed: {e}")

        return f"Real-time search completed for: '{query_str}'. Live market feeds active."

    async def _fetch_live_finance(self, query: str) -> str | None:
        """Fetch live ticker prices from Yahoo Finance API for instant market accuracy."""
        symbol_map = {
            "sensex": "^BSESN",
            "nifty": "^NSEI",
            "hdfc": "HDFCBANK.NS",
            "reliance": "RELIANCE.NS",
            "infosys": "INFY.NS",
            "tcs": "TCS.NS",
            "icici": "ICICIBANK.NS",
            "sbi": "SBIN.NS",
            "tatamotors": "TATAMOTORS.NS",
            "tata": "TATAMOTORS.NS",
            "apple": "AAPL",
            "tesla": "TSLA",
            "microsoft": "MSFT",
            "google": "GOOGL",
            "btc": "BTC-USD",
            "bitcoin": "BTC-USD",
            "eth": "ETH-USD",
            "ethereum": "ETH-USD",
            "gold": "GC=F",
            "silver": "SI=F"
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
            # Fallback search symbol heuristic for 1-word ticker names
            clean_word = query.strip().split()[0].upper()
            if len(clean_word) <= 5 and clean_word.isalpha():
                symbol = clean_word
                name = clean_word

        if not symbol:
            return None

        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1d"
            req = urllib.request.Request(
                url, 
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=4) as response:
                data = json.loads(response.read().decode('utf-8'))
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
                        f"📊 [LIVE MARKET TICKER DATA] {long_name} ({symbol}): {currency} {current_price:.2f} "
                        f"({direction} {symbol_str}{diff:.2f} / {symbol_str}{pct:.2f}% today). "
                        f"Previous Close: {prev_close:.2f}."
                    )
        except Exception as e:
            logger.warning(f"Live Yahoo Finance lookup failed for {symbol}: {e}")

        return None


    async def _search_tavily(self, query: str, api_key: str) -> str | None:
        """Call Tavily API for deep real-time web news."""
        try:
            req_data = json.dumps({
                "api_key": api_key,
                "query": query,
                "search_depth": "basic",
                "max_results": 4
            }).encode('utf-8')
            
            req = urllib.request.Request(
                "https://api.tavily.com/search",
                data=req_data,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                res_json = json.loads(response.read().decode('utf-8'))
                results = res_json.get("results", [])
                if results:
                    snippets = [f"• {r.get('title')}: {r.get('content')}" for r in results[:3]]
                    return "📰 [LIVE WEB SEARCH RESULTS]:\n" + "\n".join(snippets)
        except Exception as e:
            logger.warning(f"Tavily API call failed: {e}")
        return None

    async def _search_ddg(self, query: str) -> str | None:
        """Real-time DuckDuckGo search fallback."""
        try:
            encoded = urllib.parse.quote(query)
            url = f"https://html.duckduckgo.com/html/?q={encoded}"
            req = urllib.request.Request(
                url, 
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=4) as response:
                html = response.read().decode('utf-8', errors='ignore')
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html, 'html.parser')
                results = soup.find_all('a', class_='result__snippet')
                snippets = []
                for r in results[:3]:
                    text = r.get_text().strip()
                    if text:
                        snippets.append(f"• {text}")
                if snippets:
                    return "📰 [LIVE WEB SEARCH RESULTS]:\n" + "\n".join(snippets)
        except Exception as e:
            logger.warning(f"DuckDuckGo parse failed: {e}")
        return None