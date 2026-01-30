from datetime import datetime
from typing import Literal

class Colors:
	RED = "\x1b[31m"
	YELLOW = "\x1b[33m"
	RESET = "\x1b[0m"

INFO = "INFO"
WARN = "WARN"
ERROR = "ERROR"
LogLevel = Literal[INFO, WARN, ERROR]
ApiName = Literal["42 API", "Yoshi API"]

def get_timestamp() -> str:
	now = datetime.now()
	return now.strftime("%Y-%m-%d-%H-%M-%S")

def log(
	level: LogLevel,
	api: ApiName,
	method: str,
	url: str,
	message: str,
	retry_count: int | None = None
) -> None:
	timestamp = get_timestamp()
	retry_info = f" [Retry {retry_count}]" if retry_count is not None else ""
	prefix = f"[{timestamp}] [{api}] {method.upper()} {url}"

	if level == "ERROR":
		print(f"{Colors.RED}{prefix}{retry_info} - {message}{Colors.RESET}")
	elif level == "WARN":
		print(f"{Colors.YELLOW}{prefix}{retry_info} - {message}{Colors.RESET}")
	else:
		print(f"{prefix} - {message}")
