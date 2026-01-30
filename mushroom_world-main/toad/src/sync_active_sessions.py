from typing import Any, Dict, List
from api_client import IntraApi, YoshiApi

ACTIVE_SESSIONS = "active_sessions"
CAMPUS_ID = 48

def sync_active_sessions(data: Dict[str, Any]) -> List[Any]:
	# Fetch all currently active locations (end_at is null means they're still connected)
	active_locations = IntraApi.get_all_pages(
		"locations",
		data["token"],
		f"filter[campus_id]={CAMPUS_ID}&filter[active]=true",
		token_refresh_callback=data.get("token_refresh_callback")
	)

	# Delete all stored sessions from Yoshi
	stored_sessions = YoshiApi.get("/active-sessions")
	for session in stored_sessions:
		YoshiApi.delete(f"/active-sessions/{session['student_id']}")

	# Send each active location to Yoshi one by one
	sessions = []
	for location in active_locations:
		user = location.get("user", {})
		if not user or not user.get("id") or not user.get("login"):
			continue

		session = {
			"login": user["login"],
			"host": location.get("host", "unknown"),
			"begin_at": location.get("begin_at", ""),
		}
		YoshiApi.put(f"/active-sessions/{user['id']}", session)
		sessions.append(session)

	print(f"Synced {len(sessions)} active session(s)")

	return sessions
