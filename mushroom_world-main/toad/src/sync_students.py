from datetime import datetime
from typing import Any, Dict, List
from api_client import IntraApi, YoshiApi

STUDENTS = "students"
BOCAL_GROUP_ID = 36
TEST_ACCOUNT_GROUP_ID = 119
STUDENTS_SEED_ID = 2147483647

def sync_students(data: Dict[str, Any]) -> List[Any]:
	start_range = data["dates"].get(STUDENTS, data["default_date"])
	if isinstance(start_range, str):
		start_range = datetime.fromisoformat(start_range.replace("Z", "+00:00"))
	
	studs = IntraApi.get_all_pages(
		"cursus/21/users",
		data["token"],
		f"sort=login"
		f"&filter[primary_campus_id]=48"
		f"&range[updated_at]={start_range.isoformat()},{datetime.now().isoformat()}",
		token_refresh_callback=data.get("token_refresh_callback")
	)

	i = 0
	synced_count = 0
	to_anonymize = []
	while i < len(studs):
		studs[i] = IntraApi.get_one(f"users/{studs[i]['id']}", data["token"], token_refresh_callback=data.get("token_refresh_callback"))

		if (
			studs[i].get("staff?", False) or
			any(group["id"] in [TEST_ACCOUNT_GROUP_ID, BOCAL_GROUP_ID] for group in studs[i].get("groups", []))
		):
			studs.pop(i)
			continue
		
		YoshiApi.put(f"/students/{studs[i]['id']}", {
			"login": studs[i]["login"],
			"id": studs[i]["id"],
		})

		if (studs[i].get("first_name") == "3b3"):
			to_anonymize.append(studs[i]['id'])
		i += 1
		synced_count += 1

	print(f"Synced {synced_count} student(s)")

	mulhouse_studs = YoshiApi.get("/students")
	mulhouse_studs = [stud for stud in mulhouse_studs if stud["id"] != STUDENTS_SEED_ID]

	anon_count = 0
	for anon in to_anonymize:
		YoshiApi.patch(f"/students/anonymize/{anon}")
		anon_count += 1

	print(f"Anonymized {anon_count} student(s)")

	return mulhouse_studs
