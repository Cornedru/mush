import os
from datetime import datetime
from typing import Any, Dict

SYNC_DIR = "/toad/sync"
LAST_SYNC_FILE = f"{SYNC_DIR}/last_sync"

def load_dates() -> Dict[str, datetime]:
	"""Load the sync dates from the last sync file"""
	if not os.path.exists(LAST_SYNC_FILE):
		return {}

	dates: Dict[str, datetime] = {}
	with open(LAST_SYNC_FILE, "r", encoding="utf-8") as f:
		for line in f:
			line = line.strip()
			if not line or "=" not in line:
				continue
			split = line.split("=", 1)
			if len(split) == 2:
				try:
					dates[split[0]] = datetime.fromisoformat(split[1].replace("Z", "+00:00"))
				except ValueError:
					print(f"Warning: Could not parse date for {split[0]}: {split[1]}")

	return dates

def save_module_date(module_name: str, sync_date: datetime) -> None:
	"""Save the sync date for a single module immediately after it completes."""
	os.makedirs(SYNC_DIR, exist_ok=True)
	
	existing_dates = load_dates()
	
	existing_dates[module_name] = sync_date

	to_write = ""
	for key, date in existing_dates.items():
		to_write += f"{key}={date.isoformat()}\n"
	
	with open(LAST_SYNC_FILE, "w", encoding="utf-8") as f:
		f.write(to_write)
	
	print(f"Saved sync date for {module_name}: {sync_date.isoformat()}")

def save_dates(data: Dict[str, Any], begin_date: datetime) -> None:
	"""Save the sync dates for all modules"""
	os.makedirs(SYNC_DIR, exist_ok=True)
	to_write = ""
	for key in data:
		to_write += f"{key}={begin_date.isoformat()}\n"
	with open(LAST_SYNC_FILE, "w", encoding="utf-8") as f:
		f.write(to_write)
