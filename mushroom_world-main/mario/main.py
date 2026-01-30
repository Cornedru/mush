#!python3
import logging
import atexit
import time
from multiprocessing import Process
from process_correction import process_correction

from flask import Flask, jsonify
from tools.logger import log, INFO, WARN, ERROR
from tools.conf import validate_environment_variables

# Constants
PROCESS_SHUTDOWN_TIMEOUT_SECONDS = 30
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 3002

app = Flask(__name__)
werkzeug_log = logging.getLogger('werkzeug')
werkzeug_log.setLevel(logging.ERROR)

# Process management
active_processes = []

def cleanup_finished_processes():
	"""Remove finished processes from the active list."""
	global active_processes
	active_processes = [p for p in active_processes if p.is_alive()]

def cleanup_all_processes():
	"""Wait for all active processes to finish (with timeout) and clean up."""
	global active_processes
	cleanup_finished_processes()
	if active_processes:
		log(INFO, "Shutdown", f"Waiting for {len(active_processes)} active processes to finish...")
		start_time = time.time()
		for p in active_processes[:]:
			remaining_time = PROCESS_SHUTDOWN_TIMEOUT_SECONDS - (time.time() - start_time)
			if remaining_time <= 0:
				log(WARN, "Shutdown", f"Timeout waiting for processes, {len(active_processes)} processes still running")
				break
			try:
				p.join(timeout=remaining_time)
				if not p.is_alive():
					active_processes.remove(p)
			except Exception as e:
				log(ERROR, "Shutdown", f"Error waiting for process: {e}")
				if not p.is_alive():
					active_processes.remove(p)
		if active_processes:
			log(WARN, "Shutdown", f"{len(active_processes)} processes did not finish in time")

# Register cleanup on exit
atexit.register(cleanup_all_processes)

@app.route('/health', methods=['GET'])
def health():
	return jsonify({'status': 'ok'}), 200

@app.route('/trigger/<correction_id>', methods=['GET'])
def luigi_hook(correction_id):
	log(INFO, "API", f"Received trigger request for correction {correction_id}")
	cleanup_finished_processes()
	try:
		p = Process(target=process_correction, args=(correction_id,))
		p.daemon = True  # Process will be terminated when parent exits
		active_processes.append(p)
		p.start()
		if not p.is_alive():
			log(ERROR, "API", f"Process for correction {correction_id} failed to start")
			return jsonify({'success': False, 'error': 'Process failed to start'}), 500
		return jsonify({'success': True}), 200
	except Exception as e:
		log(ERROR, "API", f"Error starting process for correction {correction_id}: {e}")
		return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
	try:
		validate_environment_variables()
		log(INFO, "Startup", f"Starting Mario service on {SERVER_HOST}:{SERVER_PORT}")
		app.run(host=SERVER_HOST, port=SERVER_PORT)
	except Exception as e:
		log(ERROR, "Startup", f"Failed to start service: {e}")
		exit(1)
