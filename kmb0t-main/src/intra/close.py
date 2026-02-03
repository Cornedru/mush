import sys, os, yaml, locale
from datetime import datetime

with open('data/config.yml', 'r') as f: config = yaml.safe_load(f)

from src.students.blackhole import report_blackholed

def intra_freeze(client, data):
    if 'user' in data and 'login' in data['user']:
        login = data['user']['login']
        link_stud = f"https://profile.intra.42.fr/users/{login}"

    if data['state'] == 'close':
        msg = f"🥶 <{link_stud}|{login}>: {data['reason']}"
    elif data['state'] == 'unclose':
        msg = f"🚀 <{link_stud}|{login}> revient de son A.G.U."
    else:
        msg = f"Another state of AGU webhook have been receive : \n{data}"
        client[0].chat_postMessage(channel=config['slack'][client[1]]['admin_DM'], text=msg)
        sys.exit()

    client[0].chat_postMessage(channel=config['slack'][client[1]]['KMb0t_channel'], text=msg)
    sys.exit()


def intra_tig(client, data, tig):
    if 'user' in data and 'login' in data['user']:
        link_stud = f"https://profile.intra.42.fr/users/{data['user']['login']}"

    if 'reason' in data and data['reason'] == "Shop TIG":
        return #already warned in src/intra/shop
    elif 'schedule_at' in tig and tig['schedule_at'] == None:
         t = int(tig['duration'] / 60 / 60)
         msg = f"""
👮 <{link_stud}|{data['user']['login']}> a reçu une TIG de {t}h par {data['closer']['login']}.\r
Raison: {data['reason']}. Occupation: {data['community_services'][0]['occupation']}.
               """
    elif 'schedule_at' in tig and tig['schedule_at'] != None:
        t = int(tig['duration'] / 60 / 60)
        locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
        dt = datetime.strptime(tig['schedule_at'], '%Y-%m-%d %H:%M:%S UTC').strftime("%A %-d %B %Y")
        msg = f"📅  <{link_stud}|{data['user']['login']}> à défini sa TIG de {t}h le {dt} à 10h."

    client[0].chat_postMessage(channel=config['slack'][client[1]]['KMb0t_channel'], text=msg)

def intra_close(client, data):
    if 'community_services' in data and len(data['community_services']) == 1:
        intra_tig(client, data, data['community_services'][0])
    elif 'kind' in data and data['kind'] == 'agu':
        intra_freeze(client, data)
    elif 'reason' in data and data['reason'] in ['Black Hole ended.', 'Blackholed for missing a milestone at pace 24'] and data['state'] == 'close':
        report_blackholed(data['user']['login'])
