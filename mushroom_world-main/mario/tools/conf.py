import os
import sys


YOSHI_URL = os.getenv('YOSHI_URL')
KMB0T_AUTH_TOKEN = os.getenv('KMB0T_AUTH_TOKEN')
KMB0T_URL = os.getenv('KMB0T_URL')

def validate_environment_variables():
	required_env_vars = [
		"KMB0T_AUTH_TOKEN",
		"YOSHI_URL",
		"KMB0T_URL",
	]

	missing_vars = []
	for env_var in required_env_vars:
		if not os.getenv(env_var) or os.getenv(env_var) == "":
			missing_vars.append(env_var)

	if missing_vars:
		error_message = f"Missing required environment variables: {', '.join(missing_vars)}"
		print(f"Error: {error_message}", file=sys.stderr)
		exit(1)
	