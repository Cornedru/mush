from datetime import datetime
from typing import Literal

class Colors:
	RED = "\x1b[31m"
	YELLOW = "\x1b[33m"
	RESET = "\x1b[0m"

INFO = "INFO"
WARN = "WARN"
ERROR = "ERROR"
DEBUG = "DEBUG"
LogLevel = Literal[INFO, WARN, ERROR, DEBUG]

def get_timestamp() -> str:
	now = datetime.now()
	return now.strftime("%Y-%m-%d-%H-%M-%S")

def log(
	level: LogLevel,
	context: str,
	message: str
) -> None:
	timestamp = get_timestamp()
	prefix = f"[{timestamp}] [Mario] [{context}]"

	if level == "ERROR":
		print(f"{Colors.RED}{prefix} - {message}{Colors.RESET}")
	elif level == "WARN":
		print(f"{Colors.YELLOW}{prefix} - {message}{Colors.RESET}")
	else:
		print(f"{prefix} - {message}")
