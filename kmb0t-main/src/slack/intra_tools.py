import os, sys, re, yaml
import pandas as pd
from datetime import datetime
import pytz

with open('data/config.yml', 'r') as f: config = yaml.safe_load(f)

from src.tools import json_intra_api
from src.slack.tools import remove_emoji

def del_title(client, event, ts):
    remove_emoji(client, event['item']['channel'], ts, 'white_check_mark')
    with open(f"logs/{ts}.title") as f: intra_id = f.readlines()[0]
    json_intra_api('DEL', f'titles_users/{intra_id}')
    user = client[0].users_profile_get(user=event['user'])
    login = user['profile']['display_name']
    if len(login) == 0: login = user['profile']['real_name']
    msg = f"🚫 Title canceled by {login}."
    client[0].chat_postMessage(channel=event['item']['channel'], thread_ts=ts, text=msg)
    os.remove(f'logs/{ts}.title')

def del_coalition(client, event, ts):
    remove_emoji(client, event['item']['channel'], ts, 'white_check_mark')
    with open(f"logs/{ts}.coa") as f: data = f.readlines()
    json_intra_api('DEL', f'coalitions/{data[0]}/scores/{data[1]}')
    user = client[0].users_profile_get(user=event['user'])
    login = user['profile']['display_name']
    if len(login) == 0: login = user['profile']['real_name']
    msg = f"🚫 Transaction canceled by {login}."
    client[0].chat_postMessage(channel=event['item']['channel'], thread_ts=ts, text=msg)
    os.remove(f'logs/{ts}.coa')

def del_transaction(client, event, ts):
    remove_emoji(client, event['item']['channel'], ts, 'white_check_mark')
    with open(f"logs/{ts}.wallet") as f: intra_id = f.readlines()[0]
    json_intra_api('DEL', f'transactions/{intra_id}')
    user = client[0].users_profile_get(user=event['user'])
    login = user['profile']['display_name']
    if len(login) == 0: login = user['profile']['real_name']
    msg = f"🚫 Transaction canceled by {login}."
    client[0].chat_postMessage(channel=event['item']['channel'], thread_ts=ts, text=msg)
    os.remove(f'logs/{ts}.wallet')

def del_create_event(client, event, ts):
    remove_emoji(client, event['item']['channel'], ts, 'white_check_mark')
    remove_emoji(client, event['item']['channel'], ts, 'eyes')
    with open(f"logs/{ts}.create-event") as f: intra_id = f.readlines()[0]
    json_intra_api('DEL', f'events/{intra_id}')
    user = client[0].users_profile_get(user=event['user'])
    login = user['profile']['display_name']
    if len(login) == 0: login = user['profile']['real_name']
    msg = f"🚫 Event deleted by {login}."
    client[0].chat_postMessage(channel=event['item']['channel'], thread_ts=ts, text=msg)
    os.remove(f'logs/{ts}.create-event')

def del_create_exam(client, event, ts):
    remove_emoji(client, event['item']['channel'], ts, 'white_check_mark')
    remove_emoji(client, event['item']['channel'], ts, 'eyes')
    with open(f"logs/{ts}.create-exam") as f: intra_id = f.readlines()[0]
    json_intra_api('DEL', f'exams/{intra_id}')
    user = client[0].users_profile_get(user=event['user'])
    login = user['profile']['display_name']
    if len(login) == 0: login = user['profile']['real_name']
    msg = f"🚫 Exam deleted by {login}."
    client[0].chat_postMessage(channel=event['item']['channel'], thread_ts=ts, text=msg)
    os.remove(f'logs/{ts}.create-exam')

def del_tig(client, event, ts):
    remove_emoji(client, event['item']['channel'], ts, 'white_check_mark')
    with open(f"logs/{ts}.tig") as f: ids = f.readlines()[0].split(',')
    json_intra_api('DEL', f'community_services/{ids[1]}')
    json_intra_api('DEL', f'closes/{ids[0]}')
    user = client[0].users_profile_get(user=event['user'])
    login = user['profile']['display_name']
    if len(login) == 0: login = user['profile']['real_name']
    msg = f"🚫 T.I.G. deleted by {login}."
    client[0].chat_postMessage(channel=event['item']['channel'], thread_ts=ts, text=msg)
    os.remove(f'logs/{ts}.tig')

def get_logins():
    if os.path.isfile('logs/tmp/studs.pkl'): 
        return pd.read_pickle('logs/tmp/studs.pkl')
    stud_data = []
    studs = json_intra_api('GET', 'campus/48/users')
    for stud in studs:
        stud_data.append([stud['login'], stud['id'], stud['staff?'], stud['active?']])
        data = json_intra_api('GET', f"users/{stud['id']}")
    df = pd.DataFrame(stud_data, columns=['login', 'id', 'staff', 'active'])
    df.to_pickle('logs/tmp/studs.pkl')
    return df

def parse_wallet(client, data):
    login = data['text'].split(' ')[2]
    reason = re.search(r'"(.*?)"', data['text']).group(1)
    amount = data['text'].split(' ')[1]
    if not login in get_logins()['login'].values:
        msg = f"🤔 {login} not found in 42 Mulhouse studs"
    elif not re.match(r'^[0-9a-zA-ZÀ-ÿ-_.,()/\'’*+=\" ]{1,100}$', reason):
        msg = f"❌ Reason is incorrect. Max 100 chars. Do not use special characters.\nUsage: `!wallet 42 yoyostud \"He's a really nice guy\"`"
    else:
        return amount, login, reason
    client[0].chat_postMessage(channel=data['channel'], thread_ts=data['ts'], text=msg)
    client[0].reactions_add(channel=data['channel'], name='x', timestamp=data['ts'])
    remove_emoji(client, data['channel'], data['ts'], 'eyes')
    sys.exit()

def parse_tig(client, data):
    login = data['text'].split(' ')[2]
    args = re.findall(r'"(.*?)"', data['text'])
    reason = args[0]
    occupation = "Boite à TIG" if len(args) == 1 or len(args[1]) > 168 else args[1]
    amount = data['text'].split(' ')[1]
    if not login in get_logins()['login'].values:
        msg = f"🤔 {login} not found in 42 Mulhouse studs"
    elif not re.match(r'^[0-9a-zA-ZÀ-ÿ-_.,()/\'’*+= \"]{1,100}$', reason):
        msg = f"❌ Reason is incorrect. Max 100 chars. Do not use special characters.\nUsage: `!tig 4h yoyostud \"He's a really bad guy\"`"
    elif int(amount[0]) not in [2,4,8]:
        msg = f"📒 Incorrect value : 2h or 4h or 8h. <https://meta.intra.42.fr/articles/code-of-conduct-and-community-services-tig-ab7047e2-7edd-4472-92d3-ea91e3acb1a7|Check rules>."
    else:
        amount = str(int(amount[0]) * 3600)
        return amount, login, reason, occupation
    client[0].chat_postMessage(channel=data['channel'], thread_ts=data['ts'], text=msg)
    client[0].reactions_add(channel=data['channel'], name='x', timestamp=data['ts'])
    remove_emoji(client, data['channel'], data['ts'], 'eyes')
    sys.exit()

def parse_coalition(client, data):
    coa_slug = data['text'].split(' ')[2]
    reason = re.search(r'"(.*?)"', data['text']).group(1)
    amount = data['text'].split(' ')[1]
    if coa_slug not in config['intra']['coalitions']:
        msg = f"🤔 {coa_slug} not found in coalitions : `{list(config['intra']['coalitions'].keys())}`"
    elif not re.match(r'^[0-9a-zA-ZÀ-ÿ-_.,()/\'’*+= \"]{1,100}$', reason):
        msg = f"❌ Reason is incorrect. Max 100 chars. Do not use special characters.\nUsage: `!coa gear-managers 42 \"Bingogogo\"`"
    else:
        return amount, config['intra']['coalitions'][coa_slug], reason
    client[0].chat_postMessage(channel=data['channel'], thread_ts=data['ts'], text=msg)
    client[0].reactions_add(channel=data['channel'], name='x', timestamp=data['ts'])
    remove_emoji(client, data['channel'], data['ts'], 'eyes')
    sys.exit()

def parse_titre(client, data):
    title_id = data['text'].split(' ')[1]
    login = data['text'].split(' ')[2]
    studs = get_logins()
    if not login in studs['login'].values:
        msg = f"🤔 {login} not found in 42 Mulhouse studs"
    elif not bool(re.fullmatch(r"[+-]?\d+", title_id)) or int(title_id) > 4242:
        msg = f"Usage: `!titre 653 yoyostud`"
    else:
        return title_id, studs.loc[studs['login'] == login, 'id'].values[0]
    client[0].chat_postMessage(channel=data['channel'], thread_ts=data['ts'], text=msg)
    client[0].reactions_add(channel=data['channel'], name='x', timestamp=data['ts'])
    remove_emoji(client, data['channel'], data['ts'], 'eyes')
    sys.exit()

def parse_create_event(client, data):
    args = re.findall(r'"(.*?)"', data['text'])
    if len(args) != 5:
        msg = f"❌ Incorrect usage.\nUsage: `!create-event \"event name\" \"dd/mm/yyyy hh:mm\" \"dd/mm/yyyy hh:mm\" \"location\" \"description\" login`"
        client[0].chat_postMessage(channel=data['channel'], thread_ts=data['ts'], text=msg)
        client[0].reactions_add(channel=data['channel'], name='x', timestamp=data['ts'])
        remove_emoji(client, data['channel'], data['ts'], 'eyes')
        sys.exit()
    
    name = args[0]
    begin_at_raw = args[1]
    end_at_raw = args[2]
    location = args[3]
    description = args[4]
    login = data['text'].split('"')[-1].strip().split(' ')[-1]
    studs = get_logins()
    
    # Verifications
    if not login in studs['login'].values:
        msg = f"🤔 {login} not found in 42 Mulhouse studs"
    elif not re.match(r'^[0-9a-zA-ZÀ-ÿ\-_.,()/\'*+= \"]{1,100}$', name):
        msg = f"❌ Name is incorrect. Max 100 chars. Do not use special characters."
    elif not re.match(r'^[0-9a-zA-ZÀ-ÿ\-_.,()/\'*+= \"]{1,168}$', location):
        msg = f"❌ Location is incorrect. Max 168 chars. Do not use special characters."
    elif not re.match(r'^[0-9a-zA-ZÀ-ÿ\-_.,()/\'*+=\n\r \"]{1,500}$', description):
        msg = f"❌ Description is incorrect. Max 500 chars. Do not use special characters."
    else:
        try:
            tz = pytz.timezone('Europe/Paris')
            begin_at = pd.to_datetime(begin_at_raw, format='%d/%m/%Y %H:%M', errors='raise').replace(tzinfo=tz).astimezone(pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')
            end_at = pd.to_datetime(end_at_raw, format='%d/%m/%Y %H:%M', errors='raise').replace(tzinfo=tz).astimezone(pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')
            
            if begin_at >= end_at:
                msg = f"❌ Begin date must be before end date."
            else:
                # Toutes les validations sont OK - retourner les valeurs
                return name, begin_at, end_at, location, description, login
        except Exception as e:
            msg = f"❌ Invalid date format. Use dd/mm/yyyy hh:mm format (ex: 22/03/2025 10:00)"
    
    # En cas d'erreur, envoyer le message et arrêter
    client[0].chat_postMessage(channel=data['channel'], thread_ts=data['ts'], text=msg)
    client[0].reactions_add(channel=data['channel'], name='x', timestamp=data['ts'])
    remove_emoji(client, data['channel'], data['ts'], 'eyes')
    sys.exit()

def parse_create_exam(client, data):
    args = re.findall(r'"(.*?)"', data['text'])
    if len(args) != 3:
        msg = f"❌ Incorrect usage.\nUsage: `!create-exam \"dd/mm/yyyy hh:mm\" \"dd/mm/yyyy hh:mm\" \"location\"`"
        client[0].chat_postMessage(channel=data['channel'], thread_ts=data['ts'], text=msg)
        client[0].reactions_add(channel=data['channel'], name='x', timestamp=data['ts'])
        remove_emoji(client, data['channel'], data['ts'], 'eyes')
        sys.exit()
    
    begin_at_raw = args[0]
    end_at_raw = args[1]
    location = args[2]
    studs = get_logins()
    
    # Verifications
    if not re.match(r'^[0-9a-zA-ZÀ-ÿ\-_.,()/\'*+= \"]{1,168}$', location):
        msg = f"❌ Location is incorrect. Max 168 chars. Do not use special characters."
    else:
        try:
            tz = pytz.timezone('Europe/Paris')
            begin_at = pd.to_datetime(begin_at_raw, format='%d/%m/%Y %H:%M', errors='raise').replace(tzinfo=tz).astimezone(pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')
            end_at = pd.to_datetime(end_at_raw, format='%d/%m/%Y %H:%M', errors='raise').replace(tzinfo=tz).astimezone(pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')
            begin_at_france = pd.to_datetime(begin_at_raw, format='%d/%m/%Y %H:%M', errors='raise').replace(tzinfo=tz)
            if begin_at >= end_at:
                msg = f"❌ Begin date must be before end date."
            else:
                # Toutes les validations sont OK - retourner les valeurs
                return begin_at_france, begin_at, end_at, location
        except Exception as e:
            msg = f"❌ Invalid date format. Use dd/mm/yyyy hh:mm format (ex: 22/03/2025 10:00)"
    
    # En cas d'erreur, envoyer le message et arrêter
    client[0].chat_postMessage(channel=data['channel'], thread_ts=data['ts'], text=msg)
    client[0].reactions_add(channel=data['channel'], name='x', timestamp=data['ts'])
    remove_emoji(client, data['channel'], data['ts'], 'eyes')
    sys.exit()