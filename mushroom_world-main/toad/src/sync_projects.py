from datetime import datetime
from typing import Any, Dict, List
from api_client import IntraApi, YoshiApi

PROJECTS = "project"

def sync_projects(data: Dict[str, Any]) -> List[Any]:
	print("[sync_projects] Starting project sync")
	last_sync = data["dates"].get(PROJECTS, data["default_date"])
	if isinstance(last_sync, str):
		last_sync = datetime.fromisoformat(last_sync.replace("Z", "+00:00"))
	print(f"[sync_projects] Last sync date: {last_sync.isoformat()}")

	print("[sync_projects] Fetching projects from 42 API...")
	projects = IntraApi.get_all_pages(
		"cursus/21/projects",
		data["token"],
		f"range[updated_at]={last_sync.isoformat()},{datetime.now().isoformat()}",
		page_size=25,
		token_refresh_callback=data.get("token_refresh_callback")
	)

	for project in projects:
		YoshiApi.put(f"/projects/{project['id']}", {
			"name": project["name"],
			"id": project["id"],
		})

	print(f"Synced {len(projects)} project(s)")

	print("[sync_projects] Fetching all projects from Yoshi API...")
	return YoshiApi.get("/projects")
