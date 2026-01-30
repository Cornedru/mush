import os
import requests
from logger import log, INFO, ERROR
from api_client import _get_session_42

AUTH_URL = "https://api.intra.42.fr/oauth/token"

def get_token():
	try:
		# Use connection pooling: reuse 42 API session
		session = _get_session_42()
		response = session.post(
			AUTH_URL,
			data={
				"grant_type": "client_credentials",
				"client_id": os.getenv("INTRA_UID"),
				"client_secret": os.getenv("INTRA_SECRET"),
				"scope": "public projects",
			},
			headers={
				"Content-Type": "application/x-www-form-urlencoded",
			},
			timeout=30
		)
		log(INFO, "42 API", "POST", AUTH_URL, f"Status: {response.status_code}")
		response.raise_for_status()
		return response.json()
	except Exception as err:
		log(ERROR, "42 API", "POST", AUTH_URL, str(err))
		raise Exception(f"Failed to get token: {err}")
