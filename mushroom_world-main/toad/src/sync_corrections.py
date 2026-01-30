from datetime import datetime
from typing import Any, Dict, List, Optional
from api_client import IntraApi, YoshiApi
from sync_pushes import PUSHES
from sync_students import STUDENTS

CORRECTIONS = "correction"

def parse_date(date_string: Optional[str]) -> Optional[str]:
	if not date_string:
		return None
	try:
		parsed = datetime.fromisoformat(date_string.replace("Z", "+00:00"))
		return parsed.isoformat()
	except ValueError:
		print(f"Warning: Invalid date string: {date_string}")
		return None

def get_correction_status(filled_at: Optional[str]) -> str:
	if filled_at is None or filled_at == "":
		return "scheduled"
	return "done"

def sync_corrections(data: Dict[str, Any]) -> List[Any]:
	last_sync = data["dates"].get(CORRECTIONS, data["default_date"])
	if isinstance(last_sync, str):
		last_sync = datetime.fromisoformat(last_sync.replace("Z", "+00:00"))
	
	corrections = IntraApi.get_all_pages(
		"scale_teams",
		data["token"],
		f"filter[campus_id]=48"
		f"&filter[cursus_id]=21"
		f"&range[updated_at]={last_sync.isoformat()},{datetime.now().isoformat()}",
		token_refresh_callback=data.get("token_refresh_callback")
	)

	pushes = data["already_fetched"].get(PUSHES, [])
	studs = data["already_fetched"].get(STUDENTS, [])

	valid_corrections = []
	for correction in corrections:
		# Check if push exists
		if not any(push["id"] == correction["team"]["id"] for push in pushes):
			continue
		
		# Check if corrector exists (only if corrector is provided)
		if (
			correction.get("corrector") and
			not any(stud["id"] == correction["corrector"]["id"] for stud in studs)
		):
			continue
		
		valid_corrections.append(correction)

	for correction in valid_corrections:
		if correction["scale"]["correction_number"] != 3:
			YoshiApi.patch(f"/pushes/{correction['team']['id']}", {
				"nb_correction_needed": correction["scale"]["correction_number"],
			})

		status = get_correction_status(correction.get("filled_at"))

		YoshiApi.put(f"/corrections/{correction['id']}", {
			"id": correction["id"],
			"comment": correction.get("comment", ""),
			"feedback": correction.get("feedback", ""),
			"mark": correction.get("final_mark"),
			"flag": correction.get("flag", {}).get("name") if correction.get("flag") else None,
			"begin_at": parse_date(correction.get("begin_at")),
			"filled_at": parse_date(correction.get("filled_at")),
			"corrector_id": correction.get("corrector", {}).get("id") if correction.get("corrector") else None,
			"push_id": correction["team"]["id"],
			"status": status,
		})

	print(f"Synced {len(valid_corrections)} correction(s)")
	return valid_corrections
