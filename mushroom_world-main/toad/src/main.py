import os
import sys
import argparse
from datetime import datetime
from scraper import scrap

def validate_environment_variables():
	required_env_vars = [
		"INTRA_UID",
		"INTRA_SECRET",
	]

	missing_vars = []
	for env_var in required_env_vars:
		if not os.getenv(env_var) or os.getenv(env_var) == "":
			missing_vars.append(env_var)

	if missing_vars:
		error_message = f"Missing required environment variables: {', '.join(missing_vars)}"
		print(f"Error: {error_message}", file=sys.stderr)
		exit(1)

if __name__ == "__main__":
	try:
		parser = argparse.ArgumentParser(description="Toad scraper service")
		parser.add_argument(
			"--mode",
			choices=["full", "slots"],
			default="full",
			help="Scraping mode: 'full' for all modules, 'slots' for slots only"
		)
		args = parser.parse_args()

		validate_environment_variables()
		scrap(datetime.now(), mode=args.mode)
	except Exception as e:
		print(f"Error: {e}", file=sys.stderr)
		exit(1)
