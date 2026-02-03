import os, sys, yaml, time
from slack_sdk import WebClient
import pandas as pd

if not os.path.exists('logs/badge'): os.mkdir('logs/badge')
with open('data/config.yml', 'r') as f: config = yaml.safe_load(f)
c_42born2code = WebClient(token=config['slack']['42born2code']['bot_token'])
custom_loc = ['k0_', 'k1_', 'k2_', 'Cantina', '24-24']

from src.google.data import get_studs_gsheet
from src.infra.badgeuse_vars import choose_location
from src.intra.logtime import get_last_logtime, close_intra_logtime, location_close, sync_intra_host
from src.tools import json_slack_api, json_intra_api
from src.intra.logtime_vars import b_banned, b_KO

def get_login(badge_id):
    if not badge_id.isdigit(): return 'Badge unknown'

    if os.path.isfile('logs/tmp/badges.yml'):
        with open('logs/tmp/badges.yml') as f: all_badges = yaml.safe_load(f)
    else:
        all_badges = {}
        for gsheet_id in config['gsheet']['promos']:
            gsheet = get_studs_gsheet(gsheet_id, ['Login','Badge', 'Badge clef'])
            if 'Error' in gsheet:
                print(gsheet, file=sys.stderr, flush=True)
                return 'Gsheet broken'
            dict_gsheet = gsheet.to_dict(orient='records')

            badge = {row['Badge']: row['Login'] for row in dict_gsheet if not pd.isna(row['Badge'])}
            badge_clef = {row['Badge clef']: row['Login'] for row in dict_gsheet if not pd.isna(row['Badge clef'])}

            all_badges = {**all_badges, **badge}
            all_badges = {**all_badges, **badge_clef}
        with open('logs/tmp/badges.yml', 'w') as f: yaml.dump(all_badges, f)

    for badge, login in all_badges.items():
        if not badge.isdigit():
            print(f'{login} has incorrect badge in Gsheet: {badge}', file=sys.stderr, flush=True)
            continue
        if int(badge) == int(badge_id): return login

    print(f'Badgeuse: {badge_id} unknown', file=sys.stderr, flush=True)
    return "Badge unknown"

def check_crash_intra(login, DM_stud):
    if os.path.isfile(f'logs/badge/{login}.badgage'):
        current_time = time.time()
        time_creation = os.path.getmtime(f'logs/badge/{login}.badgage')
        file_age_minutes = (current_time - time_creation) / 60
        if file_age_minutes < 10:
            return 'ignoring: Badgage en cours dans la durée des 10min'
        else:
            c_42born2code.chat_postMessage(channel=DM_stud, text="Badgage en cours annulé, veuillez réessayer. Veuillez contacter le bocal si le problème persiste.")
            print(f"Badgage en cours de + de 10min, test de retry", file=sys.stderr, flush=True)
    if os.path.isfile(f'logs/badge/{login}.closing'):
        current_time = time.time()
        time_creation = os.path.getmtime(f'logs/badge/{login}.closing')
        file_age_minutes = (current_time - time_creation) / 60
        if file_age_minutes < 10:
            return 'ignoring: Closing badge en cours'
        else:
            c_42born2code.chat_postMessage(channel=DM_stud, text="Error: sync location with intra, please wait...")
            print(f"Error: {login}.closing exist for too long, sync location with intra", file=sys.stderr, flush=True)
            if sync_intra_host() == 'intra error':
                c_42born2code.chat_postMessage(channel=DM_stud, text="Cannot reach intra, try again later.")
                return 'ignoring: error intra KO'
    return 'OK'


def check_stud_authorization(login, DM_channel):
    ret = json_intra_api('GET', f'users/{login}/projects_users', payload={'filter[project_id]': '1337'})
    if 'intra error' in ret:
        c_42born2code.chat_postMessage(channel=DM_channel, text="❌  api.intra.42.fr indisponible, veuillez réessayer plus tard.")
        return 'KO'
    if len(ret) == 0 or (ret[0]['status'] not in ['in_progress', 'finished'] and not ret[0]['validated?']):
        c_42born2code.chat_postMessage(channel=DM_channel, blocks=b_KO, text='Stud not authorized')
        return 'KO'
    if os.path.isfile(f'logs/badge/{login}.deleted'):
        current_time = time.time()
        time_creation = os.path.getmtime(f'logs/badge/{login}.deleted')
        file_age_minutes = (current_time - time_creation) / 60
        banned_minutes = 60 * 24 * 21
        if file_age_minutes > banned_minutes:
            os.remove(f'logs/badge/{login}.deleted')
        else:
            delay_suspended = (banned_minutes - file_age_minutes) / 60 / 24
            banned = b_banned.replace('DAYS', f'{delay_suspended:.1f} jours')
            c_42born2code.chat_postMessage(channel=DM_channel, text='Stud not authorized', blocks=banned)
            return 'KO'
    if os.path.isfile(f'logs/badge/{login}.banned'):
        current_time = time.time()
        time_creation = os.path.getmtime(f'logs/badge/{login}.banned')
        file_age_minutes = (current_time - time_creation) / 60
        banned_minute = 60 * 24 * 8
        if file_age_minutes > banned_minute:
            os.remove(f'logs/badge/{login}.banned')
        else:
            delay_suspended = (banned_minute - file_age_minutes) / 60 / 24
            banned = b_banned.replace('DAYS', f'{delay_suspended:.1f} jours')
            c_42born2code.chat_postMessage(channel=DM_channel, text='Stud not authorized', blocks=banned)
            return 'KO'

def badgeuse(data):
    login = get_login(data['badge'])
    if login in ['Badge unknown', 'Gsheet broken']: return
    slack_id = json_slack_api(c_42born2code, 'slack_id_from_login', login)
    DM_stud = c_42born2code.conversations_open(users=slack_id)['channel']['id']

    if 'ignoring' in check_crash_intra(login, DM_stud): return

    #check badgage forcing
    if os.path.isfile(f'logs/badge/{login}.wait_interaction'):
        c_42born2code.chat_postMessage(channel=DM_stud, text="Choisi l'emplacement dans la question ci-dessus ⬆️")

    #check stud authorization + intra location and manage if intra down
    last_location = get_last_logtime(login)
    if slack_id == 'login not in slack':
        return print('Stud used badgeuse but not in slack', file=sys.stderr, flush=True)
    elif 'intra error' in last_location and os.path.isfile(f'logs/badge/{login}.process_interaction'):
        return c_42born2code.chat_postMessage(channel=DM_stud, text="❌  api.intra.42.fr indisponible, veuillez rebadger ou demander à un tuteur de cloturer votre connexion plus tard.")    
    elif 'intra error' in last_location:
        return c_42born2code.chat_postMessage(channel=DM_stud, text="❌  api.intra.42.fr indisponible, veuillez rebadger plus tard.")
    elif check_stud_authorization(login, DM_stud) == 'KO': return
    
    #Let stud open or close intra location
    with open(f'logs/badge/{login}.badgage', 'w') as f: pass
    if not os.path.isfile(f'logs/badge/{login}.wait_interaction') and not os.path.isfile(f'logs/badge/{login}.process_interaction') and not os.path.isfile(f'logs/badge/{login}.closing'):
        with open(f'logs/badge/{login}.wait_interaction', 'w') as f:
            f.write(f"date: {data['when']}\nlogin: {login}\nbadge: {data['badge']}\nslack_id: {slack_id}\nslack_DM: {DM_stud}\n")
        c_42born2code.chat_postMessage(channel=DM_stud, text='Badgeuse: choose location', blocks=choose_location)
    elif last_location['end_at'] == None and any(loc in last_location['host'] for loc in custom_loc):
        if os.path.isfile(f'logs/badge/{login}.process_interaction'):
            os.rename(f'logs/badge/{login}.process_interaction', f'logs/badge/{login}.closing')
        ret = close_intra_logtime(last_location['id'])
        if hasattr(ret, 'status_code') and ret.status_code == 204: location_close(login, c_42born2code)
        else:
            print(f'Badge error: intra failed to close location. Stud {login} is adviced to retry later.', file=sys.stderr, flush=True)
            c_42born2code.chat_postMessage(channel=DM_stud, text="Erreur de l'intra, veuillez rebadger plus tard ou contacter le bocal.")
        if os.path.isfile(f'logs/badge/{login}.closing'): os.remove(f'logs/badge/{login}.closing')
    else:
        print(f'Unknow badge error with {login}', file=sys.stderr, flush=True)
        c_42born2code.chat_postMessage(channel=DM_stud, text="Erreur du logtime sur l'intra, veuillez réessayer ou contacter le bocal.")
        if last_location['end_at'] != None and os.path.isfile(f'logs/badge/{login}.process_interaction'): os.remove(f'logs/badge/{login}.process_interaction')
    os.remove(f'logs/badge/{login}.badgage')
