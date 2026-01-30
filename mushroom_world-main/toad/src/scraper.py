from datetime import datetime
from typing import Any, Dict
from auth import get_token
from dates import load_dates, save_module_date
from sync_functions import sync_functions, slot_sync_functions
from api_client import api_call_counter, API_42, API_YOSHI, close_sessions

def scrap(date_to_sync_with: datetime, mode: str = "full") -> None:
	print(f"start scraping (mode: {mode})")
	
	api_call_counter[API_42] = 0
	api_call_counter[API_YOSHI] = 0
	
	token_data = get_token()
	if not token_data:
		raise Exception("Failed to get token")
	
	token = token_data["access_token"]
	dates = load_dates()
	default_date = datetime.fromtimestamp(0)

	data: Dict[str, Any] = {
		"token": token,
		"dates": dates,
		"default_date": default_date,
		"already_fetched": {},
	}

	# Token refresh callback that updates the token in data dict
	def refresh_token() -> str:
		print("Refreshing access token...")
		new_token_data = get_token()
		if not new_token_data:
			raise Exception("Failed to refresh token")
		new_token = new_token_data["access_token"]
		data["token"] = new_token
		return new_token
	
	data["token_refresh_callback"] = refresh_token

	# Select sync functions based on mode
	selected_sync_functions = slot_sync_functions if mode == "slots" else sync_functions

	for sf in selected_sync_functions:
		try:
			print(f"Starting sync for: {sf['name']}")
			data["already_fetched"][sf["name"]] = sf["f"](data)
			print(f"Completed sync for: {sf['name']}")
			save_module_date(sf["name"], datetime.now())
		except Exception as error:
			print(f"Error syncing {sf['name']}: {error}")
			raise
	
	print(f"\n42 API calls: {api_call_counter[API_42]}")
	print(f"Yoshi API calls: {api_call_counter[API_YOSHI]}")
	
	# Close connection pools when done
	close_sessions()