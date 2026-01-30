from typing import Any, Dict, List
from api_client import IntraApi, YoshiApi

SLOTS = "slots"
CAMPUS_ID = 48

def sync_slots(data: Dict[str, Any]) -> List[Any]:
	# Fetch all future slots for campus 48
	slots = IntraApi.get_all_pages(
		"slots",
		data["token"],
		f"filter[campus_id]={CAMPUS_ID}&filter[future]=true",
		token_refresh_callback=data.get("token_refresh_callback"),
		page_size=100
	)

	synced_count = 0
	fetched_slot_ids = []

	for slot in slots:
		# Extract required fields for all slots (booked and unbooked)
		slot_data = {
			"id": slot["id"],
			"student_id": slot["user"]["id"],
			"begin_at": slot["begin_at"],
			"end_at": slot["end_at"],
		}

		# Upsert the slot
		YoshiApi.put(f"/slots/{slot['id']}", slot_data)
		fetched_slot_ids.append(slot["id"])
		synced_count += 1

	print(f"Synced {synced_count} slot(s)")

	# Delete old slots not in the fetched list
	if fetched_slot_ids:
		YoshiApi.post("/slots/cleanup", {"slotIds": fetched_slot_ids})
		print(f"Cleaned up old slots (kept {len(fetched_slot_ids)} slots)")
	else:
		# If no slots fetched, delete all
		YoshiApi.post("/slots/cleanup", {"slotIds": []})
		print("No future slots found, cleaned up all slots")

	return slots
