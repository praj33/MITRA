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

    @staticmethod
    def _format_event_times(start_str: str, end_str: str, tz_name: str) -> Tuple[str, str, str]:
        """
        Produces valid RFC3339 timestamps preserving the intended local time and IANA timezone.
        """
        from zoneinfo import ZoneInfo
        resolved_tz = tz_name or "UTC"
        try:
            tz = ZoneInfo(resolved_tz)
        except Exception:
            resolved_tz = "UTC"
            tz = ZoneInfo("UTC")

        def _to_rfc3339(dt_s: str) -> str:
            clean = dt_s.strip()
            if clean.endswith("Z"):
                dt = datetime.fromisoformat(clean.replace("Z", "+00:00"))
                return dt.isoformat()
            dt = datetime.fromisoformat(clean)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=tz)
            return dt.isoformat()

        try:
            start_rfc = _to_rfc3339(start_str)
            end_rfc = _to_rfc3339(end_str)
            return start_rfc, end_rfc, resolved_tz
        except Exception:
            return start_str, end_str, resolved_tz

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

            # Scope pre-check for Google: verify write permissions exist before making external call
            if provider == "google" and user_id:
                try:
                    from app.services.connected_account_service import connected_account_service
                    conn = connected_account_service.get_user_connection(user_id, "google")
                    if conn:
                        scopes = conn.get("scopes") or []
                        if scopes and not any("calendar" in s.lower() for s in scopes):
                            logger.info(f"[{trace_id}] User {user_id} Google account has identity scopes only; calendar write scope missing.")
                            return {
                                "status": "error",
                                "error_code": "scope_missing",
                                "error": "Google Calendar permission required. Connect Google Calendar in Integrations.",
                                "provider": "google",
                                "sync_status": "Saved in Mitra — Google Calendar permission required. Connect Google Calendar in Integrations.",
                                "synchronized": False,
                                "provider_event_id": None,
                                "trace_id": trace_id,
                                "timestamp": datetime.utcnow().isoformat()
                            }
                except Exception as scope_check_err:
                    logger.debug(f"Scope pre-check warning: {scope_check_err}")

            # Format RFC3339 timestamps preserving the intended local time and IANA timezone
            start_rfc, end_rfc, resolved_tz = self._format_event_times(start_time, end_time, tz_str)

            if provider == "microsoft":
                url = "https://graph.microsoft.com/v1.0/me/events"
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "subject": title,
                    "body": {"contentType": "Text", "content": description},
                    "start": {"dateTime": start_rfc, "timeZone": resolved_tz},
                    "end": {"dateTime": end_rfc, "timeZone": resolved_tz},
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
                    safe_msg = "Microsoft Calendar authentication expired. Please reconnect in Integrations." if response.status_code == 401 else f"Microsoft Graph API error (HTTP {response.status_code})."
                    return {
                        "status": "error",
                        "error": safe_msg,
                        "provider": "microsoft",
                        "sync_status": f"Saved in Mitra — Microsoft Calendar sync failed: {safe_msg}",
                        "synchronized": False,
                        "provider_event_id": None,
                        "trace_id": trace_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }

            else:
                # Google Calendar API
                event_data = {
                    "summary": title,
                    "description": description,
                    "location": location,
                    "start": {"dateTime": start_rfc, "timeZone": resolved_tz},
                    "end": {"dateTime": end_rfc, "timeZone": resolved_tz},
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
                    status_code = response.status_code
                    res_text = response.text or ""
                    safe_error = "Google Calendar sync failed."
                    error_code = "provider_error"

                    # 401 Unauthorized
                    if status_code == 401:
                        error_code = "auth_expired"
                        safe_error = "Google authentication expired or invalid. Please reconnect Google Calendar in Integrations."
                        if user_id:
                            try:
                                from app.services.connected_account_service import connected_account_service
                                connected_account_service.mark_status(user_id, "google", "needs_reauthorization")
                            except Exception:
                                pass

                    # 403 Forbidden
                    elif status_code == 403:
                        if "insufficientPermissions" in res_text or "insufficient authentication scopes" in res_text.lower():
                            error_code = "scope_missing"
                            safe_error = "Google Calendar permission required. Connect Google Calendar in Integrations."
                        elif "SERVICE_DISABLED" in res_text or "has not been used in project" in res_text.lower() or "disabled" in res_text.lower():
                            error_code = "api_disabled"
                            safe_error = "Google Calendar API is disabled in your Google Cloud Project."
                        else:
                            error_code = "permission_denied"
                            safe_error = "Google Calendar permission denied. Please verify your Google account permissions."

                    # 400 Bad Request
                    elif status_code == 400:
                        error_code = "invalid_payload"
                        try:
                            res_json = response.json()
                            msg = res_json.get("error", {}).get("message", "Invalid calendar event data.")
                            safe_msg = msg.split("See ")[0].strip() if "See " in msg else msg
                            safe_error = f"Invalid event data: {safe_msg}"
                        except Exception:
                            safe_error = "Invalid calendar event data provided."

                    else:
                        safe_error = f"Google Calendar service error (HTTP {status_code})."

                    logger.warning(f"[{trace_id}] Google Calendar API error | status: {status_code} | code: {error_code} | error: {safe_error}")

                    return {
                        "status": "error",
                        "error": safe_error,
                        "error_code": error_code,
                        "provider": "google",
                        "sync_status": f"Saved in Mitra — Google Calendar sync failed: {safe_error}",
                        "synchronized": False,
                        "provider_event_id": None,
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
