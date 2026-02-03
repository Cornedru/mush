import sys, re, os
from slack_sdk import WebClient
import yaml

with open('data/config.yml', 'r') as f: config = yaml.safe_load(f)

c_42born2code = WebClient(token=config['slack']['42born2code']['bot_token'])
channel = config['slack']['42born2code']['campus_channel']

def generate_ip(hostname):
	#hostname: kKrRpP.42mulhouse.fr
	if not re.match(r"^k[0-2]r[1-4]p[0-9]{1,2}\.42mulhouse\.fr$", hostname):
		return f"invalid hostname ({hostname})"

	kluster = hostname[hostname.index('k') + 1:hostname.index('r')]
	rank = hostname[hostname.index('r') + 1:hostname.index('p')]
	post = hostname[hostname.index('p') + 1:hostname.index('.')]

	return f"10.{int(kluster) + 11}.{rank}.{post}"

def generate_hostname(ip):
	scope = int(ip.split('.')[0])
	kluster = int(ip.split('.')[1]) - 11
	rank = int(ip.split('.')[2])
	post = int(ip.split('.')[3])

	if scope != 10 or kluster < 0 or kluster > 2 or rank < 1 or rank > 4 or post < 0 or post > 99:
		return 0, f"invalid ip ({ip})"

	return 1, f"k{kluster}r{rank}p{post}.42mulhouse.fr"

def format_hostname(hostname):
	if not re.match(r"^k[0-2]r[1-4]p[0-9]{1,2}\.42mulhouse\.fr$", hostname):
		return f"invalid hostname `{hostname}`"
	return hostname.split('.')[0]


def generate_hash(data):
	if 'where' in data and 'what' in data and 'who' in data and 'details' in data and 'when' in data:
		hash = os.popen(f"echo -n \"{data['where']}{data['what']}{data['who']}{data['details']}{data['when']}{config['infra']['usb_key']}\" | sha256sum | awk '{{print $1}}'").read().strip()
		return hash
	else:
		return 'wrong request'

def usb_monitoring(data):
	if (not 'remote_addr' in data or
	 	not 'where' in data or
		not 'what' in data or
		not 'who' in data or
		not 'details' in data
		or not generate_ip(data['where']) == data['remote_addr']):
		who = 'inconnu'
		if 'who' in data: who = f"<https://profile.intra.42.fr/users/{data['who']}|{data['who']}>"
		where = 'inconnu'
		if 'where' in data: where = format_hostname(data['where'])
		what = 'Fraudulous request:'
		details = ''
		if ('where' in data and
	  		not generate_ip(data['where']) == data['remote_addr']):
			details = f"The declared post ({format_hostname(data['where'])}) doesn't match the remote address implied post (`{generate_hostname(data['remote_addr'])[1]}`). By attempting to fetch manually the bot, someone is abusing the ressources of the school!"
			hostname = generate_hostname(data['remote_addr']) 
			where = ""
			if hostname[0] == 1:
				where = hostname[1].split('.')[0]
			else:
				where = hostname[1]

		message = f"‼️ *USB MONITOR* ‼️\n\t{who} on {where}\n\t{what}\n\t\t{details}"
		print(message, file=sys.stderr, flush=True)
		return
	elif data['type'] == 'power_btn':
		link_stud = f"https://profile.intra.42.fr/users/{data['who']}"
		message = f"🔌 *POWER BUTTON* by <{link_stud}|{data['who']}> on {data['where'].split('.')[0]}"
	elif data['type'] == 'exam_login' or data['type'] == 'exam_plug':
		message = f"📛 *EXAM* {data['where'].split('.')[0]} | {data['details']}"

	c_42born2code.chat_postMessage(channel=channel, text=message, unfurl_links=True)
