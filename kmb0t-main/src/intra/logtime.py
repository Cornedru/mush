import sys, os, json, glob, yaml, statistics
from datetime import datetime

with open('data/config.yml', 'r') as f: config = yaml.safe_load(f)
custom_loc = ['k0_', 'k1_', 'k2_', 'Cantina', '24-24']

from src.tools import json_slack_api, json_intra_api, jprint
from src.slack.tools import remove_emoji

def sync_intra_host():
    os.system('rm -f logs/badge/*.wait_interaction')
    logged_studs = glob.glob("logs/badge/*.process_interaction")
    for loc in logged_studs:
        with open(loc) as f: data = yaml.safe_load(f)
        login = loc.split('.')[0].split('/')[-1]
        ret = get_last_logtime(login)
        if 'intra error' in ret : return ret
        if ret['end_at'] != None or ('location' in data and ret['host'] != data['location']):
            print(f"clean_active_host: file logs/badge/{login}.process_interaction not true, deleting.", file=sys.stderr, flush=True)
            os.remove(loc)
            if os.path.isfile(f'logs/{login}.badgage'): os.remove(f'logs/{login}.badgage')
    stopping_studs = glob.glob("logs/badge/*.closing")
    for stop in stopping_studs:
        with open(stop) as f: data = yaml.safe_load(f)
        login = stop.split('.')[0].split('/')[-1]
        ret = get_last_logtime(login)
        if 'intra error' in ret: return ret
        if ret['end_at'] != None or ('location' in data and ret['host'] != data['location']):
            print(f"clean_active_host: file logs/badge/{login}.stopping not true, deleting.", file=sys.stderr, flush=True)
            os.remove(stop)
            if os.path.isfile(f'logs/{login}.badgage'): os.remove(f'logs/{login}.badgage')
    return "Sync done"

def close_intra_logtime(intra_id):
    end_date = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    payload = {'location[end_at]': end_date}
    return json_intra_api('PUT', f'locations/{intra_id}', payload=payload)

def get_active_stud_badge(field, value):
    logged_studs = glob.glob("logs/badge/*.process_interaction")
    for s in logged_studs:
        with open(s) as f: data = yaml.safe_load(f)
        if field in data and data[field] == value: return data
    return 'stud is not connected to badgeuse'

def delete_intra_logtime(client, event, ts):
    if not os.path.isfile(f'logs/{ts}.logtime'):
        msg = '🤔 Delete requested but no logtime attached to this slack msg.'
        return client[0].chat_postMessage(channel=event['item']['channel'], thread_ts=ts, text=msg)
    with open(f'logs/{ts}.logtime') as f: stud_badge = yaml.safe_load(f)
    location = json_intra_api('GET', f"locations/{stud_badge['intra_loc_id']}")
    if 'begin_at' in location:
        begin_time = datetime.strptime(location["begin_at"], '%Y-%m-%dT%H:%M:%S.%fZ')
        if location["end_at"] == None:
            end_time = datetime.utcnow()
        else:
            end_time = datetime.strptime(location["end_at"], '%Y-%m-%dT%H:%M:%S.%fZ')
        diff_time = (end_time - begin_time).total_seconds()
        hours = int(diff_time / 3600)
        minutes = int(diff_time / 60) % 60
    else:
        hours, minutes = '?', 0
    ret = json_intra_api('DEL', f"locations/{stud_badge['intra_loc_id']}")
    if hasattr(ret, 'status_code') and ret.status_code == 204:            
        #msg = f"💥 Ton logtime du {stud_badge['date']} en {stud_badge['location']} a été supprimé par <@{event['user']}|cal>. Prend contact avec lui pour clarifier cet oubli."
        msg = f"💥 Ton logtime du {stud_badge['date']} en {stud_badge['location']} d'une durée de *{hours}h{minutes:02d}* a été supprimé.\nLa bageuse t'es suspendu pendant 21 jours. Si c'est une erreur, merci d'en notifier le bocal."
        client[0].chat_postMessage(channel=stud_badge['slack_DM'], text=msg)
        if os.path.isfile(f"logs/badge/{stud_badge['login']}.process_interaction"): 
            os.remove(f"logs/badge/{stud_badge['login']}.process_interaction")
        os.rename(f"logs/{ts}.logtime", f"logs/badge/{stud_badge['login']}.deleted") #will block stud for 21 days
        deleted_login = json_slack_api(client[0], 'login_from_slack_id', event['user'])
        with open(f"logs/badge/{stud_badge['login']}.deleted", 'a') as f: f.write(f"deleted_by: {deleted_login}\n")
        msg = f"💥 Logtime deleted by <@{event['user']}|cal>. Inform <@{stud_badge['slack_id']}|cal> about your action."
    else:
        msg = f"Error: {ret}. Intra down ? Try again later or contact bocal."
    client[0].chat_postMessage(channel=event['item']['channel'], thread_ts=ts, text=msg, reply_broadcast=True)
    client[0].chat_postMessage(channel=event['item']['channel'], thread_ts=ts, text='<@U02H15353EC|cal> logtime deleted')

def stop_intra_logtime(client, slack_user, ts):
    stopped_login = json_slack_api(client[0], 'login_from_slack_id', slack_user)
    stud_badge = get_active_stud_badge('slack_campus_msg_ts', ts)
    slack_campus_id = config['slack']['42born2code']['badgeuse_channel']
    ret = close_intra_logtime(stud_badge['intra_loc_id'])
    if hasattr(ret, 'status_code') and ret.status_code == 204:
        #msg = f"🚫 Ta position a été cloturé par <@{slack_user}|cal>. Prend contact avec lui pour clarifier cet oubli."
        msg = f"🔍 Il semblerait que tu es absent du campus.\nTa position a été cloturé par <@{slack_user}|cal>. Si c'est une erreur, merci d'en notifier le bocal."
        client[0].chat_postMessage(channel=stud_badge['slack_DM'], text=msg)
        os.system(f"cp logs/{ts}.logtime logs/badge/{stud_badge['login']}.stopped")
        with open(f"logs/badge/{stud_badge['login']}.stopped", 'a') as f: f.write(f"stopped_by: {stopped_login}\n")
        location_close(stud_badge['login'], client[0])
        msg = f"🚫 Logtime stopped by <@{slack_user}|cal>. Inform <@{stud_badge['slack_id']}|cal> about your action."
    else:
        msg = f"intra error: {ret}. Try again later or contact bocal."
    client[0].chat_postMessage(channel=slack_campus_id, thread_ts=ts, text=msg, reply_broadcast=True)
    client[0].chat_postMessage(channel=slack_campus_id, thread_ts=ts, text='<@U02H15353EC|cal> logtime stopped')
    return msg

def get_last_logtime(user, n=0):
    last_logtime = json_intra_api('GET', f'users/{user}/locations', refresh=True)
    if 'intra error' in last_logtime:
        return f'intra error: {last_logtime}'
    else:
        return last_logtime[n]

def set_intra_host(user, host):
    last_logtime = get_last_logtime(user)
    if 'intra error' in last_logtime:
        return f"intra error: {last_logtime}"
    elif last_logtime['end_at'] == None:
        return f"❌ Tu es déjà connecté en {last_logtime['host']}."

    payload = {
        "location[user_id]": user,
        "location[host]": host,
        "location[campus_id]": 48
    }
    return json_intra_api('POST', f'users/{user}/locations', payload=payload)

def location_close(login, slack, webhook=False):
    if not webhook and os.path.isfile(f'logs/badge/{login}.closing'):
        with open(f'logs/badge/{login}.closing') as f: stud = yaml.safe_load(f)
    elif os.path.isfile(f'logs/badge/{login}.process_interaction'): #Used 🚫
        with open(f'logs/badge/{login}.process_interaction') as f: stud = yaml.safe_load(f)
        os.remove(f'logs/badge/{login}.process_interaction')
    else:
        return "Already closed"
    msg = f"🧮 Calcul du temps passé à *travailler* sur le campus..."
    ret = slack.chat_postMessage(channel=stud['slack_DM'], text=msg)
    
    if not webhook:
        data = get_last_logtime(login)
        if data == 'intra error':
            msg = f"🕓 Après ?h??, ta position en {stud['location']} a été cloturé. À bientôt !"
            slack.chat_update(channel=stud['slack_DM'], ts=ret['ts'], text=msg)
            return print(f'Bdage location_close: Failed to "🧮 Calcul du temps" for {login}', file=sys.stderr, flush=True)
        begin_time = datetime.strptime(data["begin_at"], '%Y-%m-%dT%H:%M:%S.%fZ')
        end_time = datetime.strptime(data["end_at"], '%Y-%m-%dT%H:%M:%S.%fZ')
    else:
        begin_time = datetime.strptime(webhook["begin_at"], '%Y-%m-%d %H:%M:%S %Z')
        end_time = datetime.strptime(webhook["end_at"], '%Y-%m-%d %H:%M:%S %Z')
    
    diff_time = (end_time - begin_time).total_seconds()
    hours = int(diff_time / 3600)
    minutes = int(diff_time / 60) % 60
    if hours >= 8:
        msg = f"👀 <@U02H15353EC|cal> Location ended after {hours}h{minutes:02d} which is > 8h"
        msg_stud = f"⏰ Ta position en {stud['location']} a été cloturé après {hours}h{minutes:02d}.\nTu as utilisé la badgeuse pour une durée > 8h sans pause obligatoire. L'utilisation de la bageuse t'es suspendu pendant 8 jours."
        with open(f'logs/badge/{login}.banned', 'w'): pass #will block stud for 8 days
    else:
        msg = f'Location ended after {hours}h{minutes:02d}.'
        msg_stud = f"🕓 Après {hours}h{minutes:02d}, ta position en {stud['location']} a été cloturé. À bientôt !"

    slack_ts = stud['slack_campus_msg_ts']
    slack_campus_id = config['slack']['42born2code']['badgeuse_channel']
    slack.chat_postMessage(channel=slack_campus_id, thread_ts=slack_ts, text=msg, reply_broadcast=False)
    remove_emoji((slack,None), slack_campus_id, slack_ts, 'no_entry_sign')

    slack.chat_update(channel=stud['slack_DM'], ts=ret['ts'], text=msg_stud)

def location(data, event_type, slack):
    if event_type == 'location_close' and any(loc in data['host'] for loc in custom_loc):
        location_close(data['user']['login'], slack, webhook=data)
