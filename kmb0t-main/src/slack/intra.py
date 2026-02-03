import sys, os, re, json, yaml
from datetime import datetime, timedelta
import pytz


from src.tools import jprint, json_slack_api, json_intra_api
from src.slack.intra_tools import parse_wallet, get_logins, parse_tig, parse_coalition, parse_titre, parse_create_event, parse_create_exam
from src.slack.tools import wait_validation, remove_emoji
from src.intra.logtime import get_active_stud_badge, stop_intra_logtime, get_last_logtime, close_intra_logtime
from src.slack.inscription import create_inscription

from src.api42.intra import ic

def titre(client, data):
    try:
        title_id, login = parse_titre(client, data)
    except Exception as e:
        print(e, file=sys.stderr, flush=True)
        client[0].reactions_add(channel=data['channel'], name='x', timestamp=data['ts'])
        msg = f"Usage: `!titre 653 yoyostud`"
        client[0].chat_postMessage(channel=data['channel'], thread_ts=data['ts'], text=msg)
        remove_emoji(client, data['channel'], data['ts'], 'eyes')
        return "Wrong args"

    ret = wait_validation(client, data, 42)
    if ret == 'Invalidated': return 'Invalidated'

    payload = {
      "titles_user[title_id]": title_id,
      "titles_user[user_id]": login
    }
    ret = json_intra_api('POST', f'titles_users', payload=payload)
    if hasattr(ret, 'status_code') and ret.status_code == 201:
        client[0].reactions_add(channel=data['channel'], name='white_check_mark', timestamp=data['ts'])
        with open(f"logs/{data['ts']}.title", 'w+') as f:
            f.write(f"{json.loads(ret.text)['id']}") #save ID si demande de cancel par slack
    else:
        client[0].reactions_add(channel=data['channel'], name='x', timestamp=data['ts'])
        client[0].chat_postMessage(channel=data['channel'], thread_ts=data['ts'], text=f"Intra error: {ret}")
    remove_emoji(client, data['channel'], data['ts'], 'eyes')

def create_exam(client, data):
    try:
        dict_cluster_api = {'k0': "10.11.0.0/16", "k1": "10.12.0.0/16", "k2": "10.13.0.0/16"}
        dict_cluster_nb_stud = {'k0': 53, "k1": 62, "k2": 38} # Marge pc HS
        args = re.findall(r'"(.*?)"', data['text'])
        if len(args) == 0: #si commande egale a !create-exam sans args -> commande par defaut, prochain jeudi de 15h a 18h au k0
            # Utiliser le fuseau horaire français
            france_tz = pytz.timezone('Europe/Paris')
            now_france = datetime.now(france_tz)
            days_ahead = 3 - now_france.weekday()
            if days_ahead < 0 or (days_ahead == 0 and now_france.hour >= 15):
                days_ahead += 7

            next_thursday_france = now_france + timedelta(days=days_ahead)
            # Créer les heures en heure française (15h et 18h)
            begin_at_france = next_thursday_france.replace(hour=15, minute=0, second=0, microsecond=0)
            end_at_france = next_thursday_france.replace(hour=18, minute=0, second=0, microsecond=0)

            # Convertir en UTC pour l'API
            begin_at = begin_at_france.astimezone(pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')
            end_at = end_at_france.astimezone(pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')
            location = "k0" # cluster par defaut
        else:
            begin_at_france, begin_at, end_at, location = parse_create_exam(client, data)
    except Exception as e:
        print(e, file=sys.stderr, flush=True)
        client[0].reactions_add(channel=data['channel'], name='x', timestamp=data['ts'])
        msg = f"❌ Incorrect usage.\nUsage: `!create-exam \"dd/mm/yyyy hh:mm\" \"dd/mm/yyyy hh:mm\" \"location\"`"
        client[0].chat_postMessage(channel=data['channel'], thread_ts=data['ts'], text=msg)
        remove_emoji(client, data['channel'], data['ts'], 'eyes')
        return "Wrong args"

    ret = wait_validation(client, data, 42)
    if ret == 'Invalidated': return 'Invalidated'
    location = location.lower()
    if location not in dict_cluster_api:
        return "Wrong location"
    payload = {
        "exam": {
            "name": "exam stud",
            "begin_at": begin_at,
            "end_at": end_at,
            "ip_range": dict_cluster_api[location],
            "location": location,
            "max_people": dict_cluster_nb_stud[location],
            "visible": True,
            "campus_id": 48,
            "project_ids": [1320, 1321, 1322, 1323, 1324, 2708, 2709, 2710, 2711, 2712]
        }
    }
    ret = ic.post("/exams", json=payload)
    if hasattr(ret, 'status_code') and ret.status_code == 201:
        client[0].reactions_add(channel=data['channel'], name='white_check_mark', timestamp=data['ts'])
        client[0].reactions_add(channel=data['channel'], name='chair', timestamp=data['ts'])
        # ajoute une confimation avec la date et l'heure de l'exam
        msg = f"✅ Exam studs created successfully!\nExam Date and Time: {begin_at_france.strftime('%d/%m/%Y %H:%M')}."
        client[0].chat_postMessage(channel=data['channel'], thread_ts=data['ts'], text=msg)
        with open(f"logs/{data['ts']}.create-exam", 'w+') as f:
            f.write(f"{json.loads(ret.text)['id']}") #save ID si demande de cancel par slack
        
        msg = f"Surveillance de l'exam de {begin_at_france.strftime('%d/%m/%Y %H:%M')} au {end_at_france.strftime('%d/%m/%Y %H:%M')} en {location}.\nBesoin de minimum 2 surveillants par créneau :\n1️⃣ {begin_at_france.strftime('%H:%M')} - {(begin_at_france + timedelta(hours=1, minutes=30)).strftime('%H:%M')}, 2️⃣ {(begin_at_france + timedelta(hours=1, minutes=30)).strftime('%H:%M')} - {end_at_france.strftime('%H:%M')}.\n"
        create_inscription(client, data, msg)
    else:
        client[0].reactions_add(channel=data['channel'], name='x', timestamp=data['ts'])
        client[0].chat_postMessage(channel=data['channel'], thread_ts=data['ts'], text=f"Intra error: {ret}")
    remove_emoji(client, data['channel'], data['ts'], 'eyes')


def create_event(client, data):
    try:
        name, begin_at, end_at, location, description, login = parse_create_event(client, data)
    except Exception as e:
        print(e, file=sys.stderr, flush=True)
        client[0].reactions_add(channel=data['channel'], name='x', timestamp=data['ts'])
        msg = f"❌ Incorrect usage.\nUsage: `!create-event \"event name\" \"dd/mm/yyyy hh:mm\" \"dd/mm/yyyy hh:mm\" \"location\" \"description\" login`"
        client[0].chat_postMessage(channel=data['channel'], thread_ts=data['ts'], text=msg)
        remove_emoji(client, data['channel'], data['ts'], 'eyes')
        return "Wrong args"

    ret = wait_validation(client, data, 42)
    if ret == 'Invalidated': return 'Invalidated'

    payload = {
        "event[name]": name,
        "event[begin_at]": begin_at,
        "event[end_at]": end_at,
        "event[location]": location,
        "event[description]": description,
        "event[creator_login]": login,
        "event[kind]": "association",
        "event[campus_ids][]": 48,
        "event[cursus_ids][]": 21,
        "event[events_themes_attributes][0][theme_id]": 123,
        "event[events_themes_attributes][0][theme_attributes][name]": login
    }
    ret = json_intra_api('POST', 'events', payload=payload)
    if hasattr(ret, 'status_code') and ret.status_code == 201:
        client[0].reactions_add(channel=data['channel'], name='white_check_mark', timestamp=data['ts'])
        with open(f"logs/{data['ts']}.create-event", 'w+') as f:
            f.write(f"{json.loads(ret.text)['id']}") #save ID si demande de cancel par slack

        msg = f"✅ Événement '{name}' créé avec succès!\nAjoutez l'emoji  👀  pour voir la liste des participants."
        client[0].chat_postMessage(channel=data['channel'], thread_ts=data['ts'], text=msg)
    else:
        client[0].reactions_add(channel=data['channel'], name='x', timestamp=data['ts'])
        client[0].chat_postMessage(channel=data['channel'], thread_ts=data['ts'], text=f"Intra error: {ret}")
    remove_emoji(client, data['channel'], data['ts'], 'eyes')

def coalition(client, data):

    try:
        amount, coa_id, reason = parse_coalition(client, data)
    except Exception as e:
        print(e, file=sys.stderr, flush=True)
        client[0].reactions_add(channel=data['channel'], name='x', timestamp=data['ts'])
        msg = f"Usage: `!coa gear-managers 420 \"Bingogogo\"`"
        client[0].chat_postMessage(channel=data['channel'], thread_ts=data['ts'], text=msg)
        remove_emoji(client, data['channel'], data['ts'], 'eyes')
        return "Wrong args"

    if int(amount) > 500:
        ret = wait_validation(client, data, 42)
    else:
        ret = wait_validation(client, data, 2)
    if ret == 'Invalidated': return 'Invalidated'

    payload = {
      "score[value]": amount,
      "score[reason]": reason
    }
    ret = json_intra_api('POST', f'coalitions/{coa_id}/scores', payload=payload)
    if hasattr(ret, 'status_code') and ret.status_code == 201:
        client[0].reactions_add(channel=data['channel'], name='white_check_mark', timestamp=data['ts'])
        with open(f"logs/{data['ts']}.coa", 'w+') as f:
            f.write(f"{coa_id}\n{json.loads(ret.text)['id']}") #save ID si demande de cancel par slack
    else:
        client[0].reactions_add(channel=data['channel'], name='x', timestamp=data['ts'])
        client[0].chat_postMessage(channel=data['channel'], thread_ts=data['ts'], text=f"Intra error: {ret}")
    remove_emoji(client, data['channel'], data['ts'], 'eyes')


def wallet(client, data):
    try:
        amount, login, reason = parse_wallet(client, data)
    except Exception as e:
        print(e, file=sys.stderr, flush=True)
        client[0].reactions_add(channel=data['channel'], name='x', timestamp=data['ts'])
        msg = f"Usage: `!wallet 42 yoyostud \"He's a nice guy\"`"
        client[0].chat_postMessage(channel=data['channel'], thread_ts=data['ts'], text=msg)
        remove_emoji(client, data['channel'], data['ts'], 'eyes')
        return "Wrong args"

    if int(amount) > 42:
        ret = wait_validation(client, data, 42)
    else:
        ret = wait_validation(client, data, 2)
    if ret == 'Invalidated': return 'Invalidated'

    studs = get_logins()
    stud_id = studs.loc[studs['login'] == login]
    payload = {
      "transaction[value]": amount,
      "transaction[user_id]": str(stud_id['id'].values[0]),
      "transaction[transactable_type]": "42Mulhouse KMb0t tuteur",
      "transaction[reason]": reason
    }
    ret = json_intra_api('POST', 'transactions', payload=payload)
    if hasattr(ret, 'status_code') and ret.status_code == 201:
        client[0].reactions_add(channel=data['channel'], name='white_check_mark', timestamp=data['ts'])
        with open(f"logs/{data['ts']}.wallet", 'w+') as f:
            f.write(str(json.loads(ret.text)['id'])) #save ID si demande de cancel par slack
    else:
        client[0].reactions_add(channel=data['channel'], name='x', timestamp=data['ts'])
        client[0].chat_postMessage(channel=data['channel'], thread_ts=data['ts'], text=f"Intra error: {ret}")
    remove_emoji(client, data['channel'], data['ts'], 'eyes')


def tig(client, data):
    try:
        duration, login, reason, occupation = parse_tig(client, data)
    except Exception as e:
        print(e, file=sys.stderr, flush=True)
        client[0].reactions_add(channel=data['channel'], name='x', timestamp=data['ts'])
        msg = f"Usage: `!tig 2h yoyostud \"He's a bad guy\"`"
        client[0].chat_postMessage(channel=data['channel'], thread_ts=data['ts'], text=msg)
        remove_emoji(client, data['channel'], data['ts'], 'eyes')
        return "Wrong args"

    if wait_validation(client, data, 5) == 'Invalidated': return 'Invalidated'

    studs = get_logins()
    stud_id = str(studs.loc[studs['login'] == login]['id'].values[0])

    closed_id = "141151" #42mulhouse_tech intra account
    payload = {
      "close[user_id] ": stud_id,
      "close[closer_id]": closed_id,
      "close[kind]" : "other",
      "close[reason]" : reason,
      "close[community_services_attributes]" : [{"[duration]" : duration}]
    }
    ret = json_intra_api('POST', f'users/{stud_id}/closes', payload=payload)
    close_id = json.loads(ret.text)['id']
    payload = {
      "community_service[close_id]": close_id,
      "community_service[duration]" : duration,
      "community_service[occupation]" : occupation,
      "community_service[tiger_id]" : closed_id
    }
    ret = json_intra_api('POST', f'community_services', payload=payload)

    if hasattr(ret, 'status_code') and ret.status_code == 201:
        client[0].reactions_add(channel=data['channel'], name='white_check_mark', timestamp=data['ts'])
        with open(f"logs/{data['ts']}.tig", 'w+') as f:
            f.write(f"{close_id},{json.loads(ret.text)['id']}")
    else:
        client[0].reactions_add(channel=data['channel'], name='x', timestamp=data['ts'])
        client[0].chat_postMessage(channel=data['channel'], thread_ts=data['ts'], text=f"Intra error: {ret}")
    remove_emoji(client, data['channel'], data['ts'], 'eyes')

def stop_location(client, data):
    if len(data['text'].split(' ')) != 2:
        remove_emoji(client, data['channel'], data['ts'], 'eyes')
        client[0].reactions_add(channel=data['channel'], name='x', timestamp=data['ts'])
        client[0].chat_postMessage(channel=data['channel'], thread_ts=data['ts'], text=f'Usage: `!stop yoyostud`')
    else:
        login = data['text'].split(' ')[1]
        if not login in get_logins()['login'].values:
            remove_emoji(client, data['channel'], data['ts'], 'eyes')
            client[0].reactions_add(channel=data['channel'], name='x', timestamp=data['ts'])
            client[0].chat_postMessage(channel=data['channel'], thread_ts=data['ts'], text=f'{login} not found in 42 Mulhouse studs')
            return
        stud_badge = get_active_stud_badge('login', login)
        stud_loc = get_last_logtime(login)
        if stud_loc == 'intra error':
            remove_emoji(client, data['channel'], data['ts'], 'eyes')
            client[0].reactions_add(channel=data['channel'], name='x', timestamp=data['ts'])
            client[0].chat_postMessage(channel=data['channel'], thread_ts=data['ts'], text=f'Intra is not available, try again later')
            return
        if stud_loc['end_at'] != None:
            remove_emoji(client, data['channel'], data['ts'], 'eyes')
            client[0].reactions_add(channel=data['channel'], name='x', timestamp=data['ts'])
            client[0].chat_postMessage(channel=data['channel'], thread_ts=data['ts'], text=f'Intra returns: {login} is not connected')
            return
        if stud_badge != 'stud is not connected to badgeuse':
            ret = stop_intra_logtime(client, data['user'], stud_badge['slack_campus_msg_ts'])
        else:
            ret = close_intra_logtime(stud_loc['id'])
        try:
            if 'intra error' in ret:
                client[0].reactions_add(channel=data['channel'], name='x', timestamp=data['ts'])
                msg = 'Error intra, veuillez réessayer plus tard'
            else:
                client[0].reactions_add(channel=data['channel'], name='white_check_mark', timestamp=data['ts'])
                msg = f"{login} a été déconnecté de {stud_loc['host']}"
        except Exception as e: #TODO: delete if not triggered after intra down
            print('Error in stop_location', file=sys.stderr, flush=True)
            msg = 'Error intra, veuillez réessayer plus tard'
        client[0].chat_postMessage(channel=data['channel'], thread_ts=data['ts'], text=msg)
        remove_emoji(client, data['channel'], data['ts'], 'eyes')

def intra(client, data):
    if data['text'].split(' ')[0] == '!wallet':
        wallet(client, data)
    if data['text'].split(' ')[0] == '!tig':
        tig(client, data)
    if data['text'].split(' ')[0] == '!stop':
        stop_location(client, data)
    if data['text'].split(' ')[0] == '!coa':
        coalition(client, data)
    if data['text'].split(' ')[0] == '!titre':
        titre(client, data)
    if data['text'].split(' ')[0] == '!create-event':
        create_event(client, data)
    if data['text'].split(' ')[0] == '!create-exam':
        create_exam(client, data)
