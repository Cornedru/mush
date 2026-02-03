import sys, os, yaml, time
import signal
from datetime import datetime, timedelta
from slack_sdk import WebClient
from src.api42.intra import ic

with open('data/config.yml', 'r') as f: config = yaml.safe_load(f)
c_42born2code = WebClient(token=config['slack']['42born2code']['bot_token'])
c_42world = WebClient(token=config['slack']['42world']['bot_token'])
with open('data/studs/slack.yml', 'r') as f: studs = yaml.safe_load(f)


from src.tools import json_slack_api, jprint, json_intra_api

# def warn_copinage(data, studs):
#     dt_corr = datetime.strptime(data['begin_at'], '%Y-%m-%d %H:%M:%S UTC') + timedelta(hours=2)
#     link_stud = f"https://profile.intra.42.fr/users/{data['user']['login']}"
#     stud_corrector = f"<{link_stud}|{data['user']['login']}>"
#     msg = f"🔎  {stud_corrector} will correct {','.join(studs)} for {data['project']['name']} on *{dt_corr.strftime('%A %-d %B %-Hh%M')}*.\n \
# Students will be warned that 1 tuteur is authorized to supervise this correction 15min before."
#     ret = c_42born2code.chat_postMessage(channel=config['slack']['42born2code']['support_channel'], text=msg)

#     with open(f"logs/{data['id']}.copinage", 'w') as f: f.write(f"{os.getpid()}\n{ret['ts']}")
#     time.sleep((dt_corr - datetime.now() - timedelta(minutes=15)).seconds)

#     msg = f"🕓 The correction will start in *15 minutes*."
#     c_42born2code.chat_postMessage(channel=config['slack']['42born2code']['support_channel'], text=msg, thread_ts=ret['ts'], reply_broadcast=True)

#     if '42cursus' in data['project']['slug']: slack = c_42born2code
#     elif 'cpp-module' in data['project']['slug']: slack = c_42born2code
#     elif 'c-piscine' in data['project']['slug']: slack = c_piscine
#     else:
#         msg = f"Try to warn_copinage but project not in knowed cursus: {data['project']['slug']}"
#         c_42world.chat_postMessage(channel=config['slack']['42world']['admin_DM'], text=msg)
#         return
#     slack_id_correcteur = json_slack_api(slack, 'slack_id_from_login', data['user']['login'])
#     if slack_id_correcteur != 'login not in slack':
#         DM_stud = slack.conversations_open(users=slack_id_correcteur)
#         msg = f"You will correct {''.join(studs)} on {data['project']['name']} in 15min. 1 tuteur/staff may supervise this correction."
#         slack.chat_postMessage(channel=DM_stud['channel']['id'], text=msg)

#     for stud in studs:
#         stud = stud.split('|')[1][:-1]
#         slack_id = json_slack_api(slack, 'slack_id_from_login', stud)
#         if slack_id != 'login not in slack':
#             DM_stud = slack.conversations_open(users=slack_id)
#             msg = f"You will be correct by {stud_corrector} on {data['project']['name']} in 15min. 1 tuteur/staff may supervise this correction."
#             slack.chat_postMessage(channel=DM_stud['channel']['id'], text=msg)


# def check_copinage(data):
#     studs_project, copinage, inform_copinage = [], False, False
#     #with open("data/studs/copinage.yml", "r") as f: studs_copinage = yaml.safe_load(f)
#     users_project = ic.pages_threaded(f"teams/{str(data['team']['id'])}")['users']
#     for user in users_project:
#         # if user['login'] in studs_copinage and \
#         #    data['user']['login'] in get_copinage_studs(user['login'], 4): #4 most correctors
#         #     copinage = True
#         # if user['login'] in studs_copinage: inform_copinage = True
#         link_stud = f"https://profile.intra.42.fr/users/{user['login']}"
#         studs_project.append(f"<{link_stud}|{user['login']}>")

#     if copinage == True:
#         warn_copinage(data, studs_project)
#     elif inform_copinage == True:
#         dt_corr = datetime.strptime(data['begin_at'], '%Y-%m-%d %H:%M:%S UTC') + timedelta(hours=2)
#         link_stud = f"https://profile.intra.42.fr/users/{data['user']['login']}"
#         stud_corrector = f"<{link_stud}|{data['user']['login']}>"
#         link_copinage = "https://docs.google.com/spreadsheets/d/1j8GyNuzXivarUxnnTbzKTlhjYDeabPnMgNrshoZrYFA/edit#gid=1255561861"
#         msg = f"👍 {stud_corrector} will correct {','.join(studs_project)} for {data['project']['name']} on *{dt_corr.strftime('%A %-d %B %-Hh%M')}*.\n \
# Students are on the list of <{link_copinage}|copinage> but this correction seems legit. Nothing to do."
#         ret = c_42born2code.chat_postMessage(channel=config['slack']['42born2code']['support_channel'], text=msg)


# #TODO: faire des stats les corrections destroy and mettre des limites
# def corr_cancel(data):
#     if os.path.exists(f"logs/{data['id']}.copinage"): 
#         with open(f"logs/{data['id']}.copinage") as file:
#             lines = [line.rstrip() for line in file]
#         pid, slack_ts = int(lines[0]), lines[1]

#         os.kill(pid, signal.SIGTERM)
#         msg = f"🧐 Correction has been destroyed."
#         c_42born2code.chat_postMessage(channel=config['slack']['42born2code']['support_channel'], text=msg, thread_ts=slack_ts)

#TODO: diff de la pool piscine et pool cursus
def ecretage_points(data):
    max_points = config['intra']['max_points_corr']
    if data['user'] and data['user']['correction_point'] > max_points:
        stud = data['user']['id']
        extra_points = data['user']['correction_point'] - max_points
        payload = {
            'id':stud ,
            'reason':f'Do not hold more that {max_points} points.',
            'amount':f'-{extra_points}'
        }
        json_intra_api('POST', f'users/{stud}/correction_points/add', payload=payload)
        if data['user']['login'] in studs.get("42born2code", {}):
            json_intra_api('POST', 'pools/78/points/add', payload={'points': str(extra_points)})

def check_flags(data):
    login = data['team']['repo_uuid'].split('-')[-1]
    link_stud = f"https://profile.intra.42.fr/users/{login}"
    if data['user']: link_corr = f"https://profile.intra.42.fr/users/{data['user']['login']}"
    if data['flag']['name'] == 'Cheat':
        msg = f"🤥 Cheat detected for <{link_stud}|{login}>'s group on {data['project']['name']} by <{link_corr}|{data['user']['login']}>"
    elif data['flag']['name'] == 'Concerning situation':
        msg = f"🤨 Concerning situation have been reported by <{link_corr}|{data['user']['login']}> for <{link_stud}|{login}>'s group on {data['project']['name']}"
    elif data['flag']['id'] == 14:
        msg = f"🙄 <{link_corr}|{data['user']['login']}> was not convinced by <{link_stud}|{login}>'s group on {data['project']['name']} : Can't support / explain code."
    else:
        return "No concerning flags detected"
    c_42born2code.chat_postMessage(channel=config['slack']['42born2code']['support_channel'], text=msg)

def intra_corr(data, event_type):
    if event_type == 'scaleteam_create':
        pass
        #check_copinage(data)
    elif event_type == 'scaleteam_delete':
        pass
        #corr_cancel(data)
    elif event_type == 'scaleteam_update':
        ecretage_points(data)
        check_flags(data)
