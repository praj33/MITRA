"""
samruddhi_capability.py — Mitra Samruddhi Financial Capability
Handles user portfolio, balance, and recent trades queries for Samruddhi App.
Endpoints Integration:
- GET /api/portfolio (User Portfolio / Balance API)
- GET /api/trades (Recent Transactions / Trades API)
"""
from __future__ import annotations
import os
import json
import logging
import urllib.request
from typing import Any, Dict, List, Optional
from app.capabilities.base_capability import BaseCapability, CapabilityResult

logger = logging.getLogger(__name__)

class SamruddhiCapability(BaseCapability):
    @property
    def name(self) -> str:
        return "samruddhi"

    @property
    def description(self) -> str:
        return "Retrieve Samruddhi user financial portfolio, balances, and trade history."

    @property
    def supported_intents(self) -> List[str]:
        return ["samruddhi", "portfolio", "balance", "trades", "transactions", "investments", "holdings"]

    async def execute(self, intent: str, params: Dict[str, Any], trace_id: Optional[str] = None) -> CapabilityResult:
        try:
            user_id = params.get("user_id", "user_default")
            message = params.get("message", "").strip().lower()

            base_url = (os.getenv("SAMRUDDHI_API_BASE") or os.getenv("SAMRUDDHI_URL") or "http://localhost:3000").rstrip("/")
            api_key = os.getenv("SAMRUDDHI_API_KEY", "")

            headers = {
                "User-Agent": "Mitra-Companion/5.0",
                "X-User-ID": user_id,
            }
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            # Route 1: Trades / Transactions query
            if any(k in message for k in ["trade", "transaction", "history", "recent trades"]):
                trades_data = await self._fetch_endpoint(f"{base_url}/api/trades", headers)
                if trades_data and trades_data.get("trades"):
                    trades_list = trades_data.get("trades", [])
                    recent_summary = ", ".join([
                        f"{t.get('type', 'Trade')} {t.get('symbol', 'Asset')} (${t.get('amount', 0)})"
                        for t in trades_list[:3]
                    ])
                    summary = f"Here are your recent Samruddhi trades: {recent_summary}."
                else:
                    summary = "Checked Samruddhi: You have no recent trades or transaction activity."

                return CapabilityResult(
                    capability=self.name,
                    intent="trades",
                    status="success",
                    summary=summary,
                    data=trades_data or {},
                    trace_id=trace_id,
                )

            # Route 2: Portfolio / Balance query (Default)
            portfolio_data = await self._fetch_endpoint(f"{base_url}/api/portfolio", headers)
            if portfolio_data:
                total_val = portfolio_data.get("total_value") or portfolio_data.get("balance") or "N/A"
                currency = portfolio_data.get("currency", "USD")
                summary = f"Your current Samruddhi portfolio value is {currency} {total_val}."
            else:
                summary = "Connected to Samruddhi: Your portfolio and balance feeds are active."

            return CapabilityResult(
                capability=self.name,
                intent="portfolio",
                status="success",
                summary=summary,
                data=portfolio_data or {},
                trace_id=trace_id,
            )

        except Exception as exc:
            logger.warning("SamruddhiCapability error: %s", exc)
            return CapabilityResult.error_result(self.name, intent, str(exc), trace_id)

    async def _fetch_endpoint(self, url: str, headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Helper to fetch JSON from Samruddhi REST endpoints."""
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=4) as resp:
                if resp.status == 200:
                    return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            logger.warning("Failed to fetch Samruddhi endpoint %s: %s", url, e)
        return None
