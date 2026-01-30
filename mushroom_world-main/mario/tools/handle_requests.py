import time
import requests
from typing import Optional, Callable, Any
from tools.logger import log, ERROR

MAX_RETRIES_COUNT = 3
REQUEST_TIMEOUT_SECONDS = 30
RETRY_DELAY_SECONDS = 1

_session: Optional[requests.Session] = None


def _get_session() -> requests.Session:
	"""Get or create the session for connection pooling."""
	global _session
	if _session is None:
		_session = requests.Session()
	return _session


def _make_request(
	url: str,
	request_fn: Callable[[], requests.Response],
	operation_name: str
) -> requests.Response:
	"""
	Generic request handler with retry logic.

	Args:
		url: The URL being requested (for logging)
		request_fn: Function that performs the actual request
		operation_name: Name of the operation for logging (e.g., "Data Fetch", "Data Post")

	Returns:
		The response object

	Raises:
		Exception: If max retries exhausted or unrecoverable error
	"""
	retry_count = 0

	while retry_count <= MAX_RETRIES_COUNT:
		try:
			res = request_fn()

			if res is None:
				raise Exception("Received None response")

			if res.status_code >= 400:
				raise Exception(f"HTTP {res.status_code}")

			return res

		except requests.exceptions.Timeout as e:
			retry_count += 1
			log(ERROR, operation_name,
			    f"Timeout for {url} (attempt {retry_count}/{MAX_RETRIES_COUNT + 1}): {e}")
			if retry_count > MAX_RETRIES_COUNT:
				raise Exception(f"Timeout - Max retries exhausted: {e}")
			time.sleep(RETRY_DELAY_SECONDS)

		except requests.exceptions.RequestException as e:
			retry_count += 1
			log(ERROR, operation_name,
			    f"Network error for {url} (attempt {retry_count}/{MAX_RETRIES_COUNT + 1}): {e}")
			if retry_count > MAX_RETRIES_COUNT:
				raise Exception(f"Network error - Max retries exhausted: {e}")
			time.sleep(RETRY_DELAY_SECONDS)

		except Exception as e:
			retry_count += 1
			log(ERROR, operation_name,
			    f"Error for {url} (attempt {retry_count}/{MAX_RETRIES_COUNT + 1}): {e}")
			if retry_count > MAX_RETRIES_COUNT:
				raise
			time.sleep(RETRY_DELAY_SECONDS)

	raise Exception(f"Unexpected exit from retry loop for {url}")


def get_data(url: str) -> Any:
	"""
	Make a GET request with retry logic and session reuse.

	Args:
		url: The URL to fetch

	Returns:
		Parsed JSON response

	Raises:
		Exception: If request fails after retries or JSON parsing fails
	"""
	session = _get_session()

	res = _make_request(
		url,
		lambda: session.get(url, timeout=REQUEST_TIMEOUT_SECONDS),
		"Data Fetch"
	)

	retry_count = 0
	while retry_count <= MAX_RETRIES_COUNT:
		try:
			return res.json()
		except ValueError as e:
			retry_count += 1
			log(ERROR, "Data Fetch",
			    f"Invalid JSON from {url} (attempt {retry_count}/{MAX_RETRIES_COUNT + 1}): {e}")
			if retry_count > MAX_RETRIES_COUNT:
				raise Exception(f"Invalid JSON - Max retries exhausted: {e}")
			time.sleep(RETRY_DELAY_SECONDS)
			# Re-fetch the data
			res = _make_request(
				url,
				lambda: session.get(url, timeout=REQUEST_TIMEOUT_SECONDS),
				"Data Fetch"
			)


def get_data_or_none(url: str) -> Any:
	"""
	Make a GET request that returns None on 404 (useful for optional lookups).

	This is useful for cases where a 404 is an expected outcome, not an error.
	For example, checking if a user has an active session - 404 means not logged in.

	Args:
		url: The URL to fetch

	Returns:
		Parsed JSON response, or None if 404
	"""
	session = _get_session()

	try:
		res = session.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
		if res.status_code == 404:
			return None
		if res.status_code >= 400:
			raise Exception(f"HTTP {res.status_code}")
		return res.json()
	except requests.exceptions.RequestException as e:
		log(ERROR, "Data Fetch", f"Network error for {url}: {e}")
		raise
	except ValueError as e:
		log(ERROR, "Data Fetch", f"Invalid JSON from {url}: {e}")
		raise


def post_data(
	url: str,
	json_data: Optional[dict] = None,
	headers: Optional[dict] = None
) -> requests.Response:
	"""
	Make a POST request with retry logic and session reuse.

	Args:
		url: The URL to post to
		json_data: Optional JSON data to send in the request body
		headers: Optional headers to include in the request

	Returns:
		Response object

	Raises:
		Exception: If request fails after retries
	"""
	session = _get_session()

	return _make_request(
		url,
		lambda: session.post(url, json=json_data, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS),
		"Data Post"
	)
