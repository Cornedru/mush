import os
import time
import json
from typing import Any, Dict, Optional, TypeVar, Callable, Literal
from ratelimit import limits, sleep_and_retry
import requests
from logger import log, INFO, WARN, ERROR

# ============================================================================
# Configuration
# ============================================================================

INTRA_BASE_URL = "https://api.intra.42.fr/v2"
YOSHI_BASE_URL = "http://yoshi:3000"
MAX_RETRIES_COUNT = 3
REQUEST_TIMEOUT_SECONDS = 30
API_42 = "42 API"
API_YOSHI = "Yoshi API"

MAX_REQUESTS_PER_SECOND = int(os.getenv("MAX_REQUESTS_PER_SECOND", "2"))
if MAX_REQUESTS_PER_SECOND < 2 or MAX_REQUESTS_PER_SECOND > 64:
	raise ValueError("MAX_REQUESTS_PER_SECOND must be a positive number between 2 and 64, given: " + os.getenv("MAX_REQUESTS_PER_SECOND"))

api_call_counter: Dict[str, int] = {
	API_42: 0,
	API_YOSHI: 0,
}

_session_42: Optional[requests.Session] = None
_session_yoshi: Optional[requests.Session] = None

def _get_session_42() -> requests.Session:
	"""Get or create the 42 API session for connection pooling."""
	global _session_42
	if _session_42 is None:
		_session_42 = requests.Session()
	return _session_42

def _get_session_yoshi() -> requests.Session:
	"""Get or create the Yoshi API session for connection pooling."""
	global _session_yoshi
	if _session_yoshi is None:
		_session_yoshi = requests.Session()
	return _session_yoshi

def close_sessions() -> None:
	"""Close all sessions. Call this when done with all requests."""
	global _session_42, _session_yoshi
	if _session_42 is not None:
		_session_42.close()
		_session_42 = None
	if _session_yoshi is not None:
		_session_yoshi.close()
		_session_yoshi = None

@limits(calls=MAX_REQUESTS_PER_SECOND, period=1)
@sleep_and_retry
def _rate_limited_42_api():
	"""Dummy function for rate limiting 42 API calls"""
	pass

# ============================================================================
# Generic Request Handler
# ============================================================================

def make_request(
	api: Literal[API_42, API_YOSHI],
	method: str,
	url: str,
	data: Optional[Any] = None,
	token: Optional[str] = None,
	token_refresh_callback: Optional[Callable[[], str]] = None
) -> requests.Response:
	"""Generic request handler for 42 API and Yoshi API with retry logic."""
	retry_count = 0

	while retry_count <= MAX_RETRIES_COUNT:
		try:
			if api == API_42:
				_rate_limited_42_api()

			headers = {"Content-Type": "application/json"}
			if token:
				headers["Authorization"] = f"Bearer {token}"

			# Use connection pooling: reuse session for same API
			session = _get_session_42() if api == API_42 else _get_session_yoshi()
			response = session.request(
				method=method,
				url=url,
				json=data if data else None,
				headers=headers,
				timeout=REQUEST_TIMEOUT_SECONDS
			)

			response.raise_for_status()

			api_call_counter[api] += 1

			items_info = ""
			try:
				response_data = response.json()
				if isinstance(response_data, list):
					items_info = f", Items: {len(response_data)}"
			except ValueError:
				pass

			log(INFO, api, method, url, f"Status: {response.status_code}{items_info}")

			return response

		except requests.exceptions.HTTPError as error:
			response = error.response
			if response is None:
				retry_count += 1
				log(ERROR, api, method, url, f"HTTP error without response: {str(error)}", retry_count)
				if retry_count > MAX_RETRIES_COUNT:
					raise Exception(f"[{api}] {method.upper()} {url} - Max retries exhausted: HTTP error without response")
				time.sleep(1)
				continue

			status = response.status_code
			
			# Handle token expiration (401) for 42 API
			if status == 401 and token_refresh_callback and api == API_42:
				try:
					response_data = response.json()
					if isinstance(response_data, dict) and response_data.get("message") == "The access token expired":
						log(WARN, api, method, url, "Token expired, refreshing...", retry_count)
						new_token = token_refresh_callback()
						if new_token:
							token = new_token
							retry_count += 1
							log(INFO, api, method, url, "Token refreshed, retrying...", retry_count)
							if retry_count > MAX_RETRIES_COUNT:
								raise Exception(f"[{api}] {method.upper()} {url} - Max retries exhausted: Token refresh failed")
							time.sleep(1)
							continue
				except (ValueError, KeyError, AttributeError):
					pass
			
			# Handle rate limiting for 42 API
			if api == API_42 and status == 429:
				retry_count += 1
				retry_after = response.headers.get("retry-after", "60")
				log(WARN, api, method, url, f"Rate limited, waiting {retry_after}s...", retry_count)

				if retry_count > MAX_RETRIES_COUNT:
					raise Exception(f"[{api}] {method.upper()} {url} - Max retries exhausted: Rate limit")

				time.sleep(int(retry_after))
				continue

			# Handle other HTTP errors
			retry_count += 1
			try:
				response_data = response.json()
			except ValueError:
				response_data = response.text
			
			log(ERROR, api, method, url, f"Status: {status} - {str(response_data)}", retry_count)

			if retry_count > MAX_RETRIES_COUNT:
				raise Exception(f"[{api}] {method.upper()} {url} - Max retries exhausted: HTTP {status}")

			time.sleep(1)
			continue

		except requests.exceptions.RequestException as error:
			retry_count += 1
			log(ERROR, api, method, url, f"Network error: {str(error)}", retry_count)

			if retry_count > MAX_RETRIES_COUNT:
				raise Exception(f"[{api}] {method.upper()} {url} - Max retries exhausted: Network error")

			time.sleep(1)
			continue

		except Exception as error:
			retry_count += 1
			log(ERROR, api, method, url, f"Unexpected error: {str(error)}", retry_count)
			if retry_count > MAX_RETRIES_COUNT:
				raise
			time.sleep(1)
			continue

	raise Exception(f"[{api}] {method.upper()} {url} - Unexpected exit from retry loop")

# ============================================================================
# 42 API Client
# ============================================================================

class IntraApi:
	@staticmethod
	def get_all_pages(uri: str, token: str, options: str = "", page_size: int = 100, token_refresh_callback: Optional[Callable[[], str]] = None) -> list[Any]:
		page = 1
		total_elements = 0
		data: list[Any] = []
		token_container = [token]

		while True:
			url = f"{INTRA_BASE_URL}/{uri}?{options}{'&' if options else ''}page[number]={page}&page[size]={page_size}"

			def refresh_wrapper():
				if token_refresh_callback:
					new_token = token_refresh_callback()
					if new_token:
						token_container[0] = new_token
					return new_token
				return None

			response = make_request(
				API_42,
				"GET",
				url,
				token=token_container[0],
				token_refresh_callback=refresh_wrapper if token_refresh_callback else None
			)

			total_elements = int(response.headers.get("x-total", "0"))
			page_data = response.json()
			if isinstance(page_data, list):
				data.extend(page_data)
			else:
				data.append(page_data)

			if len(data) >= total_elements:
				break
			page += 1

		return data

	@staticmethod
	def get_one(uri: str, token: str, options: str = "", token_refresh_callback: Optional[Callable] = None) -> Any:
		url = f"{INTRA_BASE_URL}/{uri}{'?' + options if options else ''}"

		response = make_request(
			API_42,
			"GET",
			url,
			token=token,
			token_refresh_callback=token_refresh_callback
		)

		return response.json()

# ============================================================================
# Yoshi API Client
# ============================================================================

class YoshiApi:
	@staticmethod
	def _safe_json_parse(response: requests.Response, url: str) -> Any:
		"""Safely parse JSON response, logging error details if parsing fails."""
		try:
			return response.json()
		except (ValueError, json.JSONDecodeError) as error:
			response_text = response.text[:500]
			content_type = response.headers.get("Content-Type", "unknown")
			log(ERROR, API_YOSHI, "PARSE", url, 
				f"[{API_YOSHI}] Failed to parse JSON response. Status: {response.status_code}, "
				f"Content-Type: {content_type}, "
				f"Response preview: {response_text}, "
				f"Error: {str(error)}")
			raise Exception(
				f"[{API_YOSHI}] Failed to parse JSON response from {url}. "
				f"Status: {response.status_code}, Content-Type: {content_type}, "
				f"Error: {str(error)}"
			)

	@staticmethod
	def get(endpoint: str) -> Any:
		url = f"{YOSHI_BASE_URL}{endpoint}"
		response = make_request(API_YOSHI, "GET", url)
		return YoshiApi._safe_json_parse(response, url)

	@staticmethod
	def post(endpoint: str, data: Any) -> Any:
		url = f"{YOSHI_BASE_URL}{endpoint}"
		response = make_request(API_YOSHI, "POST", url, data=data)
		return YoshiApi._safe_json_parse(response, url)

	@staticmethod
	def put(endpoint: str, data: Any) -> Any:
		url = f"{YOSHI_BASE_URL}{endpoint}"
		response = make_request(API_YOSHI, "PUT", url, data=data)
		return YoshiApi._safe_json_parse(response, url)

	@staticmethod
	def patch(endpoint: str, data: Optional[Any] = None) -> Any:
		url = f"{YOSHI_BASE_URL}{endpoint}"
		response = make_request(API_YOSHI, "PATCH", url, data=data)
		return YoshiApi._safe_json_parse(response, url)

	@staticmethod
	def delete(endpoint: str) -> Any:
		url = f"{YOSHI_BASE_URL}{endpoint}"
		response = make_request(API_YOSHI, "DELETE", url)
		return YoshiApi._safe_json_parse(response, url)
