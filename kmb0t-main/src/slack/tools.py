import os, sys, time, yaml
from slack_sdk import WebClient

with open('data/config.yml', 'r') as f: config = yaml.safe_load(f)
c_42born2code = WebClient(token=config['slack']['42born2code']['bot_token'])

from src.tools import json_slack_api

def get_slack_id(logins):
    if logins == None: return []
    studs_slack_id = []
    for s in logins:
        studs_slack_id.append(json_slack_api(c_42born2code, 'slack_id_from_login', s))
    return studs_slack_id

def check_if_needed(client, data, nb_tuteur, staff, mentors):
    if client[1] == '42world' or data['user'] in staff or data['user'] in mentors:
        return False
    if nb_tuteur == 42:
        msg = f"Command needs staff validation."
        client[0].reactions_add(channel=data['channel'], name='cop', timestamp=data['ts'])
        time.sleep(1) #pour garder 👮‍♀️ à gauche de 🆗
        client[0].reactions_add(channel=data['channel'], name='ok', timestamp=data['ts'])
    else:
        msg = f"Command needs staff or {nb_tuteur} tuteurs validation.\nPress 🆗 to engage your approvement.\n"
        client[0].reactions_add(channel=data['channel'], name='ok', timestamp=data['ts'])
    with open(f"logs/{data['ts']}.info", 'w') as f: f.write(msg)

def remove_emoji(client, channel, msg_ts, emoji):
    ret = client[0].reactions_get(channel=channel, timestamp=msg_ts)
    if not 'reactions' in ret['message']: return 'no reaction to remove'
    for reaction in ret['message']['reactions']:
        if reaction['name'] == emoji and client[0].auth_test()['user_id'] in reaction['users']:
            client[0].reactions_remove(channel=channel, name=emoji, timestamp=msg_ts)

def add_emoji(client, channel, msg_ts, emoji):
    ret = client[0].reactions_get(channel=channel, timestamp=msg_ts)
    if not 'reactions' in ret['message']:
        client[0].reactions_add(channel=channel, name=emoji, timestamp=msg_ts)
    else:
        already_added = False
        for reaction in ret['message']['reactions']:
            if reaction['name'] == emoji: already_added = True
        if not already_added:
            client[0].reactions_add(channel=channel, name=emoji, timestamp=msg_ts)

def wait_validation(client, data, nb_tuteur):
    staff = config['slack']['42born2code']['admin_users']
    with open('data/studs/tuteurs.yml') as f: tuteurs = get_slack_id(yaml.safe_load(f))
    with open('data/studs/mentors.yml') as f: mentors = get_slack_id(yaml.safe_load(f))

    if check_if_needed(client, data, nb_tuteur, staff, mentors) == False:
        return "No validation needed"

    with open(f"logs/{data['ts']}.OK", 'w') as f: pass
    nb_ok = []
    start_time = time.time()
    while len(nb_ok) < nb_tuteur:
        with open(f"logs/{data['ts']}.OK") as f: nb_ok = f.read().split(' ')
        if 'x' in nb_ok:
            remove_emoji(client, data['channel'], data['ts'], 'ok')
            remove_emoji(client, data['channel'], data['ts'], 'eyes')
            os.remove(f"logs/{data['ts']}.OK")
            return 'Invalidated'
        nb_ok = [nb for nb in nb_ok if nb not in  ['', data['user']]]
        for slack_id in nb_ok:
            if slack_id in staff or slack_id in mentors:
                login = json_slack_api(client[0], 'login_from_slack_id', slack_id)
                msg = f"✅ validated by {login}."
                with open(f"logs/{data['ts']}.info", 'a+') as f: f.write(msg)
                remove_emoji(client, data['channel'], data['ts'], 'ok')
                return "Validated by staff"
        time.sleep(1)
        if (time.time() - start_time) > 60 * 60 * 24:
            msg = f"❌ It's been 24h without confirmation. Request is cancelled."
            with open(f"logs/{data['ts']}.info", 'a+') as f: f.write(msg)
            client[0].chat_postMessage(channel=data['channel'], thread_ts=data['ts'], text=msg)
            client[0].reactions_add(channel=data['channel'], name='x', timestamp=data['ts'])
            remove_emoji(client, data['channel'], data['ts'], 'ok')
            remove_emoji(client, data['channel'], data['ts'], 'eyes')
            return 'Invalidated'

    msg = f"✅ validated by "
    for slack_id in nb_ok:
        login = json_slack_api(client[0], 'login_from_slack_id', slack_id)
        msg = msg + f"{login} "
    with open(f"logs/{data['ts']}.info", 'a+') as f: f.write(msg + '.')
    remove_emoji(client, data['channel'], data['ts'], 'ok')
    return "Validated by tutor"
