from datetime import datetime
from typing import Any, Dict, List
from api_client import IntraApi, YoshiApi
from sync_students import STUDENTS
from sync_projects import PROJECTS

PUSHES = "push"

def sync_pushes(data: Dict[str, Any]) -> List[Any]:
	last_sync = data["dates"].get(PUSHES, data["default_date"])
	if isinstance(last_sync, str):
		last_sync = datetime.fromisoformat(last_sync.replace("Z", "+00:00"))
	
	pushes = IntraApi.get_all_pages(
		"teams",
		data["token"],
		f"filter[primary_campus]=48"
		f"&filter[cursus]=21"
		f"&range[updated_at]={last_sync.isoformat()},{datetime.now().isoformat()}",
		token_refresh_callback=data.get("token_refresh_callback")
	)

	studs = data["already_fetched"].get(STUDENTS, [])
	projects = data["already_fetched"].get(PROJECTS, [])

	valid_pushes = []
	for push in pushes:
		users = push.get("users", [])
		
		if (
			any(
				user["login"].startswith("3b3") or
				not any(stud.get("login") == user["login"] for stud in studs)
				for user in users
			) or
			not any(project["id"] == push["project_id"] for project in projects)
		):
			continue
		
		valid_pushes.append(push)

	for push in valid_pushes:
		users = push.get("users", [])
		YoshiApi.put(f"/pushes/{push['id']}", {
			"id": push["id"],
			"project_id": push["project_id"],
			"correcteds_logins": [user["login"] for user in users],
			"status": "finished" if push.get("final_mark") is not None else "waiting_for_correction",
		})

	print(f"Synced {len(valid_pushes)} push(es)")
	return valid_pushes