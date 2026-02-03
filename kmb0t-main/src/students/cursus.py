import os, sys, yaml
from slack_sdk import WebClient

with open('data/config.yml', 'r') as f: config = yaml.safe_load(f)
c_42born2code = WebClient(token=config['slack']['42born2code']['bot_token'])
if not os.path.exists('logs/cursus'): os.mkdir('logs/cursus')

from src.tools import jprint, json_slack_api, json_intra_api
from src.google.tools import send_email
from src.students.cursus_vars import fin_CC_email

def ft_transcendence_locked():
    payload = {
      "filter[campus]": "48",
      "filter[locked]": "true",
      "filter[status]": "in_progress"
    }
    groups = json_intra_api('GET', 'projects/ft_transcendence/teams', payload=payload)

    for gr in groups:
        members, emails, slack_links = [], [], []
        for m in gr['users']:
            members.append(m['login'])
            emails.append(f"{m['login']}@student.42mulhouse.fr")
            slack_links.append(f"<https://profile.intra.42.fr/users/{m['login']}|{m['login']}>")
        gr_name = f"transcendence-locked_{'_'.join(members)}_{gr['id']}"
        if not os.path.isfile(f'logs/cursus/{gr_name}'):
            with open(f'logs/cursus/{gr_name}', 'w') as f: pass
            send_email('pedago@42mulhouse.fr', '42 Advanced', fin_CC_email, cc=emails)
            msg = f"🔒 ft_transcendence team `{gr['name']}` with {', '.join(slack_links)} has been locked"
            c_42born2code.chat_postMessage(channel=config['slack']['42born2code']['support_channel'], text=msg)

def ft_transcendence_validate(client, data):
    if data["project_id"] == 1337 and data["status"] == "finished" and data["validated?"] == "true":
        teams = json_intra_api('GET', f"/teams/{data['team_id']}")
        members, slack_links = [], []
        for m in teams['users']:
            members.append(m['login'])
            slack_links.append(f"<https://profile.intra.42.fr/users/{m['login']}|{m['login']}>")
        team_name = f"transcendence-validate_{'_'.join(members)}_{teams['id']}"
        if not os.path.isfile(f'logs/cursus/{team_name}'):
            with open(f'logs/cursus/{team_name}', 'w') as f: pass
            msg = f"🎉 ft_transcendence team `{teams['name']}` with {', '.join(slack_links)} has been validated"
            c_42born2code.chat_postMessage(channel=config['slack']['42born2code']['support_channel'], text=msg)

def minishell():
    payload = {
      "filter[campus]": "48",
      "filter[locked]": "true",
      "filter[status]": "in_progress"
    }
    groups = json_intra_api('GET', 'projects/42cursus-minishell/teams', payload=payload)

    for gr in groups:
        members, emails, slack_links = [], [], []
        for m in gr['users']:
            members.append(m['login'])
            emails.append(f"{m['login']}@student.42mulhouse.fr")
            slack_links.append(f"<https://profile.intra.42.fr/users/{m['login']}|{m['login']}>")
        gr_name = f"minishell-locked_{'_'.join(members)}_{gr['id']}"
        if not os.path.isfile(f'logs/cursus/{gr_name}'):
            with open(f'logs/cursus/{gr_name}', 'w') as f: pass
            msg = f"🔒 minishell team `{gr['name']}` with {', '.join(slack_links)} has been locked"
            c_42born2code.chat_postMessage(channel=config['slack']['42born2code']['support_channel'], text=msg)
