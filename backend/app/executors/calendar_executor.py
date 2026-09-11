"""
Calendar Executor — Unified Google & Microsoft Integration
Manages Google Calendar & Microsoft Calendar events via API.
Supports: create_event, update_event, delete_event, list_events.
Simulation mode when credentials not configured.
"""

import os
import requests
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
import json

from app.core.gateway_auth import GatewayAuthError, require_gateway_invocation

logger = logging.getLogger(__name__)


class CalendarExecutor:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_CALENDAR_API_KEY")
        self.access_token = os.getenv("GOOGLE_CALENDAR_ACCESS_TOKEN")
        self.calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")
        self.base_url = "https://www.googleapis.com/calendar/v3"

    def _get_effective_connection(self, user_id: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
        """
        Resolves (access_token, provider_name) for the target user.
        Checks Google connection first, then Microsoft connection.
        Returns (token, provider) or (None, None) if not connected.
        """
        if user_id:
            try:
                from app.services.token_refresh_service import token_refresh_service
                token = token_refresh_service.get_valid_access_token(user_id, "google")
                if token:
                    return token, "google"
            except Exception:
                pass

            try:
                from app.services.token_refresh_service import token_refresh_service
                token = token_refresh_service.get_valid_access_token(user_id, "microsoft")
                if token:
                    return token, "microsoft"
            except Exception:
                pass

        if self.access_token:
            return self.access_token, "google"
        return None, None

    def _get_effective_access_token(self, user_id: Optional[str] = None) -> Optional[str]:
        token, _ = self._get_effective_connection(user_id)
        return token

    def _is_configured(self, user_id: Optional[str] = None) -> bool:
        token, _ = self._get_effective_connection(user_id)
        return bool(token or self.api_key)

    def create_event(self, title: str, start_time: str, end_time: Optional[str] = None,
                     description: str = "", location: str = "", trace_id: str = "", gateway_auth: str = None,
                     user_id: Optional[str] = None, timezone: str = "UTC", attendees: Optional[list] = None) -> Dict[str, Any]:
        """Create a calendar event across Google or Microsoft Graph with timezone & attendee support."""
        try:
            try:
                require_gateway_invocation(
                    gateway_auth=gateway_auth,
                    trace_id=trace_id,
                    platform="calendar",
                    action="create_event",
                )
            except GatewayAuthError as e:
                return {
                    "status": "error",
                    "error": f"unauthorized: {str(e)}",
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "platform": "calendar",
                }

            # Range validation:
            # If end_time is not provided: default to start_time + 1 hour.
            # If explicit end_time is provided and end_dt <= start_dt: return validation error.
            tz_str = timezone or "UTC"
            if not end_time:
                try:
                    start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                    end_dt = start_dt + timedelta(hours=1)
                    end_time = end_dt.isoformat()
                except Exception as parse_err:
                    return {
                        "status": "error",
                        "error": f"Invalid start_time format: {parse_err}. Expected ISO 8601 string.",
                        "trace_id": trace_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "platform": "calendar",
                    }
            else:
                try:
                    start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                    end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
                except Exception as parse_err:
                    return {
                        "status": "error",
                        "error": f"Invalid date format: {parse_err}. Expected ISO 8601 string.",
                        "trace_id": trace_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "platform": "calendar",
                    }
                if end_dt <= start_dt:
                    return {
                        "status": "error",
                        "error": f"Invalid time range: end_time ({end_time}) must be strictly after start_time ({start_time}).",
                        "trace_id": trace_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "platform": "calendar",
                    }

            token, provider = self._get_effective_connection(user_id)

            if not token and not self.api_key:
                logger.info(f"[{trace_id}] Calendar event saved locally only in Mitra: '{title}' (no external provider connected)")
                return {
                    "status": "success",
                    "sync_status": "Saved only in Mitra",
                    "synchronized": False,
                    "provider": None,
                    "provider_event_id": None,
                    "event_id": f"sim_evt_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    "action": "create_event",
                    "event": {"title": title, "start": start_time, "end": end_time, "timezone": tz_str},
                    "method": "calendar_simulation",
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "platform": "calendar",
                    "note": "Saved only in Mitra. Connect Google or Microsoft Calendar for external synchronization."
                }

            if provider == "microsoft":
                url = "https://graph.microsoft.com/v1.0/me/events"
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "subject": title,
                    "body": {"contentType": "Text", "content": description},
                    "start": {"dateTime": start_time, "timeZone": tz_str},
                    "end": {"dateTime": end_time, "timeZone": tz_str},
                    "location": {"displayName": location}
                }
                if attendees:
                    payload["attendees"] = [{"emailAddress": {"address": a}, "type": "required"} for a in attendees]

                response = requests.post(url, json=payload, headers=headers, timeout=30)
                if response.status_code in [200, 201]:
                    res_data = response.json()
                    evt_id = res_data.get("id")
                    return {
                        "status": "success",
                        "sync_status": "Created in Microsoft Calendar",
                        "synchronized": True,
                        "provider": "microsoft",
                        "provider_event_id": evt_id,
                        "event_id": evt_id,
                        "action": "create_event",
                        "event": payload,
                        "html_link": res_data.get("webLink"),
                        "method": "microsoft_calendar_api",
                        "trace_id": trace_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "platform": "calendar"
                    }
                else:
                    if response.status_code == 401 and user_id:
                        try:
                            from app.services.connected_account_service import connected_account_service
                            connected_account_service.mark_status(user_id, "microsoft", "needs_reauthorization")
                        except Exception:
                            pass
                    return {
                        "status": "error",
                        "error": f"Microsoft Graph API error: {response.status_code} - {response.text}",
                        "trace_id": trace_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }

            else:
                # Google Calendar
                event_data = {
                    "summary": title,
                    "description": description,
                    "location": location,
                    "start": {"dateTime": start_time, "timeZone": tz_str},
                    "end": {"dateTime": end_time, "timeZone": tz_str},
                }
                if attendees:
                    event_data["attendees"] = [{"email": a} for a in attendees]

                url = f"{self.base_url}/calendars/{self.calendar_id}/events"
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                response = requests.post(url, json=event_data, headers=headers, timeout=30)
                if response.status_code in [200, 201]:
                    result = response.json()
                    evt_id = result.get("id")
                    return {
                        "status": "success",
                        "sync_status": "Created in Google Calendar",
                        "synchronized": True,
                        "provider": "google",
                        "provider_event_id": evt_id,
                        "event_id": evt_id,
                        "action": "create_event",
                        "event": event_data,
                        "html_link": result.get("htmlLink"),
                        "method": "google_calendar_api",
                        "trace_id": trace_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "platform": "calendar"
                    }
                else:
                    if response.status_code == 401 and user_id:
                        try:
                            from app.services.connected_account_service import connected_account_service
                            connected_account_service.mark_status(user_id, "google", "needs_reauthorization")
                        except Exception:
                            pass
                    return {
                        "status": "error",
                        "error": f"Calendar API error: {response.status_code} - {response.text}",
                        "trace_id": trace_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }

        except Exception as e:
            logger.error(f"[{trace_id}] Calendar create_event failed: {e}")
            return {"status": "error", "error": str(e), "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat()}

    def update_event(self, event_id: str, updates: Dict[str, Any], trace_id: str = "", gateway_auth: str = None,
                     user_id: Optional[str] = None) -> Dict[str, Any]:
        """Update an existing calendar event across Google or Microsoft Graph."""
        try:
            try:
                require_gateway_invocation(
                    gateway_auth=gateway_auth,
                    trace_id=trace_id,
                    platform="calendar",
                    action="update_event",
                )
            except GatewayAuthError as e:
                return {
                    "status": "error",
                    "error": f"unauthorized: {str(e)}",
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "platform": "calendar",
                }

            token, provider = self._get_effective_connection(user_id)

            if not token and not self.api_key:
                logger.info(f"[{trace_id}] Calendar simulation: updating event {event_id}")
                return {
                    "status": "success",
                    "event_id": event_id,
                    "action": "update_event",
                    "updates": updates,
                    "method": "calendar_simulation",
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "platform": "calendar",
                    "note": "Simulation mode"
                }

            if provider == "microsoft":
                url = f"https://graph.microsoft.com/v1.0/me/events/{event_id}"
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                ms_payload = {}
                if "title" in updates or "summary" in updates:
                    ms_payload["subject"] = updates.get("title") or updates.get("summary")
                if "description" in updates:
                    ms_payload["body"] = {"contentType": "Text", "content": updates["description"]}

                response = requests.patch(url, json=ms_payload or updates, headers=headers, timeout=30)
                if response.status_code == 200:
                    return {
                        "status": "success", "event_id": event_id, "action": "update_event",
                        "updates": updates, "method": "microsoft_calendar_api",
                        "trace_id": trace_id, "timestamp": datetime.utcnow().isoformat(),
                        "platform": "calendar"
                    }
                else:
                    return {"status": "error", "error": f"Microsoft Graph API error: {response.status_code}",
                            "trace_id": trace_id, "timestamp": datetime.utcnow().isoformat()}

            else:
                url = f"{self.base_url}/calendars/{self.calendar_id}/events/{event_id}"
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                response = requests.patch(url, json=updates, headers=headers, timeout=30)
                if response.status_code == 200:
                    return {
                        "status": "success", "event_id": event_id, "action": "update_event",
                        "updates": updates, "method": "google_calendar_api",
                        "trace_id": trace_id, "timestamp": datetime.utcnow().isoformat(),
                        "platform": "calendar"
                    }
                else:
                    return {"status": "error", "error": f"Calendar API error: {response.status_code}",
                            "trace_id": trace_id, "timestamp": datetime.utcnow().isoformat()}

        except Exception as e:
            logger.error(f"[{trace_id}] Calendar update_event failed: {e}")
            return {"status": "error", "error": str(e), "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat()}

    def delete_event(self, event_id: str, trace_id: str = "", gateway_auth: str = None,
                     user_id: Optional[str] = None) -> Dict[str, Any]:
        """Delete a calendar event across Google or Microsoft Graph."""
        try:
            try:
                require_gateway_invocation(
                    gateway_auth=gateway_auth,
                    trace_id=trace_id,
                    platform="calendar",
                    action="delete_event",
                )
            except GatewayAuthError as e:
                return {
                    "status": "error",
                    "error": f"unauthorized: {str(e)}",
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "platform": "calendar",
                }

            token, provider = self._get_effective_connection(user_id)

            if not token and not self.api_key:
                logger.info(f"[{trace_id}] Calendar simulation: deleting event {event_id}")
                return {
                    "status": "success", "event_id": event_id, "action": "delete_event",
                    "method": "calendar_simulation", "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(), "platform": "calendar",
                    "note": "Simulation mode"
                }

            if provider == "microsoft":
                url = f"https://graph.microsoft.com/v1.0/me/events/{event_id}"
                headers = {"Authorization": f"Bearer {token}"}
                response = requests.delete(url, headers=headers, timeout=30)
                if response.status_code in [200, 204]:
                    return {
                        "status": "success", "event_id": event_id, "action": "delete_event",
                        "method": "microsoft_calendar_api", "trace_id": trace_id,
                        "timestamp": datetime.utcnow().isoformat(), "platform": "calendar"
                    }
                else:
                    return {"status": "error", "error": f"Microsoft Graph API error: {response.status_code}",
                            "trace_id": trace_id, "timestamp": datetime.utcnow().isoformat()}

            else:
                url = f"{self.base_url}/calendars/{self.calendar_id}/events/{event_id}"
                headers = {"Authorization": f"Bearer {token}"}
                response = requests.delete(url, headers=headers, timeout=30)
                if response.status_code == 204:
                    return {
                        "status": "success", "event_id": event_id, "action": "delete_event",
                        "method": "google_calendar_api", "trace_id": trace_id,
                        "timestamp": datetime.utcnow().isoformat(), "platform": "calendar"
                    }
                else:
                    return {"status": "error", "error": f"Calendar API error: {response.status_code}",
                            "trace_id": trace_id, "timestamp": datetime.utcnow().isoformat()}

        except Exception as e:
            logger.error(f"[{trace_id}] Calendar delete_event failed: {e}")
            return {"status": "error", "error": str(e), "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat()}

    def list_events(self, max_results: int = 10, trace_id: str = "", gateway_auth: str = None,
                    user_id: Optional[str] = None) -> Dict[str, Any]:
        """List upcoming calendar events across Google or Microsoft Graph."""
        try:
            try:
                require_gateway_invocation(
                    gateway_auth=gateway_auth,
                    trace_id=trace_id,
                    platform="calendar",
                    action="list_events",
                )
            except GatewayAuthError as e:
                return {
                    "status": "error",
                    "error": f"unauthorized: {str(e)}",
                    "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "platform": "calendar",
                }

            token, provider = self._get_effective_connection(user_id)

            if not token and not self.api_key:
                return {
                    "status": "success", "action": "list_events", "events": [],
                    "method": "calendar_simulation", "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat(), "platform": "calendar",
                    "note": "Simulation mode"
                }

            if provider == "microsoft":
                url = "https://graph.microsoft.com/v1.0/me/events"
                headers = {"Authorization": f"Bearer {token}"}
                params = {
                    "$top": max_results,
                    "$select": "id,subject,start,end,location"
                }
                response = requests.get(url, headers=headers, params=params, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    events = [{
                        "id": e.get("id"), "title": e.get("subject"),
                        "start": e.get("start", {}).get("dateTime"),
                        "end": e.get("end", {}).get("dateTime"),
                        "location": e.get("location", {}).get("displayName", "")
                    } for e in data.get("value", [])]
                    return {
                        "status": "success", "action": "list_events", "events": events,
                        "method": "microsoft_calendar_api", "trace_id": trace_id,
                        "timestamp": datetime.utcnow().isoformat(), "platform": "calendar"
                    }
                else:
                    return {"status": "error", "error": f"Microsoft Graph API error: {response.status_code}",
                            "trace_id": trace_id, "timestamp": datetime.utcnow().isoformat()}

            else:
                url = f"{self.base_url}/calendars/{self.calendar_id}/events"
                headers = {"Authorization": f"Bearer {token}"}
                params = {
                    "maxResults": max_results,
                    "timeMin": datetime.utcnow().isoformat() + "Z",
                    "orderBy": "startTime",
                    "singleEvents": True
                }

                response = requests.get(url, headers=headers, params=params, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    events = [{
                        "id": e.get("id"), "title": e.get("summary"),
                        "start": e.get("start", {}).get("dateTime"),
                        "end": e.get("end", {}).get("dateTime"),
                        "location": e.get("location", "")
                    } for e in data.get("items", [])]
                    return {
                        "status": "success", "action": "list_events", "events": events,
                        "method": "google_calendar_api", "trace_id": trace_id,
                        "timestamp": datetime.utcnow().isoformat(), "platform": "calendar"
                    }
                else:
                    return {"status": "error", "error": f"Calendar API error: {response.status_code}",
                            "trace_id": trace_id, "timestamp": datetime.utcnow().isoformat()}

        except Exception as e:
            logger.error(f"[{trace_id}] Calendar list_events failed: {e}")
            return {"status": "error", "error": str(e), "trace_id": trace_id,
                    "timestamp": datetime.utcnow().isoformat()}
