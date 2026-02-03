import sys, os, re, json, yaml, glob
from slack_sdk import WebClient

with open('data/config.yml', 'r') as f: config = yaml.safe_load(f)

from src.tools import jprint, json_slack_api, json_intra_api, inform_stud
from src.intra.logtime import set_intra_host, sync_intra_host
from src.intra.logtime_vars import b_OK, b_sending
from src.students.internships_coorporate import inform_convention_corpo
from src.students.internships_vars import get_msg_internship
from src.tools_webdriver import get_intra_convention
from src.google.files import Gdrive_upload_file

max_Cantina = max_2424 = 12
max_k0,max_k1,max_k2 = 56,64,40
c_42born2code = WebClient(token=config['slack']['42born2code']['bot_token'])


def get_available_host(client, host):
    logged_studs = glob.glob("logs/badge/*.process_interaction")

    py_host = host.split(' ')[-1].replace('/','')
    max_place = globals()['max_' + py_host]

    intra_host = 'not available'
    for p in range(1, max_place + 1):
        intra_host = f"{host.replace(' ', '_').replace('/','-')}_p{p}"
        loc_free = True
        for loc in logged_studs:
            with open(loc) as f: data = yaml.safe_load(f)
            if 'location' in data and data['location'] == intra_host: loc_free = False
        if loc_free == True: return intra_host

    return 'All location have been took'

def logtime(client, data):
    login = json_slack_api(client[0], 'login_from_slack_id', data['user']['id'])
    if os.path.isfile(f'logs/badge/{login}.wait_interaction'):
        os.rename(f'logs/badge/{login}.wait_interaction', f'logs/badge/{login}.process_interaction')
    elif os.path.isfile(f'logs/badge/{login}.process_interaction'):
        return 'Request already sent, ignoring multiples clicks'
    else:
        client[0].chat_update(channel=data['channel']['id'], ts=data['message']['ts'], text="❌ Error, veuillez rebadger ou avertir le staff.")
        return 'Files have been deleted ?' #from sync_intra_host() if intra down

    delay_answer = float(data['actions'][0]['action_ts']) - float(data['message']['ts'])
    if delay_answer / 60 > 10:
        client[0].chat_update(channel=data['channel']['id'], ts=data['message']['ts'], text="❌ Choix de l'emplacement trop long, veuillez re-badger.")
        os.remove(f"logs/badge/{login}.process_interaction")
        return 'Request answer is more than 10min, ignoring'

    client[0].chat_update(channel=data['channel']['id'], ts=data['message']['ts'], blocks=b_sending, text='Sending data...')

    host, slack_user = data['actions'][0]['text']['text'], data['user']['id']
    intra_host = get_available_host(client, host)
    if intra_host == "All location have been took":
        client[0].chat_update(channel=data['channel']['id'], ts=data['message']['ts'], text=f"🙅 Il n'y a plus de place en {host}!")
        os.remove(f"logs/badge/{login}.process_interaction")
        return "All location have been took"

    try:
        ret = set_intra_host(login, intra_host)
    except:
        print('Unknow error in src/slack/interactions.py `def logtime`. Failed to set_intra_host', file=sys.stderr, flush=True)
        sync_intra_host()
        sys.exit()
    if hasattr(ret, 'reason') and ret.reason == 'Created':
        link_stud = f"https://profile.intra.42.fr/users/{login}"
        msg = f'📍 <{link_stud}|{login}> start location in {host}.'# React with 🚫 to stop or ❌ to delete logtime.'
        s = client[0].chat_postMessage(channel=config['slack']['42born2code']['badgeuse_channel'], text=msg)
        client[0].reactions_add(channel=s['channel'], name='no_entry_sign', timestamp=s['ts'])
        client[0].reactions_add(channel=s['channel'], name='wastebasket', timestamp=s['ts'])
        logtime_id = json.loads(ret.text)['id']
        with open(f'logs/badge/{login}.process_interaction', 'a') as f:
            f.write(f"slack_DM_msg_ts: '{data['message']['ts']}'\nslack_campus_msg_ts: '{s['ts']}'\nlocation: '{intra_host}'\nintra_loc_id: {logtime_id}\n")
        os.system(f"cp logs/badge/{login}.process_interaction logs/{s['ts']}.logtime") #pour réaction ❌
        client[0].chat_update(channel=data['channel']['id'], ts=data['message']['ts'], blocks=b_OK, text='Badgeuse OK. Happy coding !')
    elif hasattr(ret, 'reason') and 'déjà connecté' in ret.reason:
        client[0].chat_update(channel=data['channel']['id'], ts=data['message']['ts'], text=ret)
        os.remove(f'logs/badge/{login}.process_interaction')
    elif 'intra error' in ret:
        os.remove(f'logs/badge/{login}.process_interaction')
        client[0].chat_postMessage(channel=data['channel']['id'], ts=data['message']['ts'], text='❌  api.intra.42.fr non disponible, veuillez rebadger plus tard.')    

def internship(client, data):
    val_interaction = data['actions'][0]['value'].split('=')
    stage_id, login = val_interaction[0], val_interaction[1]
    s_id = json_slack_api(c_42born2code, 'slack_id_from_login', login)
    stage = json_intra_api('GET', f'internships/{stage_id}')
    msg_convention_no_buttons = get_msg_internship(stage)
    msg_convention_no_buttons["attachments"][0]["blocks"] = [
        block for block in msg_convention_no_buttons["attachments"][0]["blocks"]
        if block.get("type") != "actions"
    ]
    client[0].chat_update(channel=data['channel']['id'], ts=data['message']['ts'], text="Downloading contract...", attachments=msg_convention_no_buttons["attachments"])
    link_stage = f"https://companies.intra.42.fr/en/users/{login}/internships/{stage['id']}"
    company_link = 'https://' + stage['company_boss_user_email'].split('@')[-1]
    if "Informer l'entreprise" in data['actions'][0]['text']['text']:
        stage_id = data['actions'][0]['value'].split('=')[0]
        json_intra_api('PUT', f"internships/{stage_id}", payload={'internship[state]': 'generated'})
        stage = json_intra_api('GET', f'internships/{stage_id}', refresh=True)
        link_convention = f"https://companies.intra.42.fr/users/{login}/internships/{stage['id']}.pdf"
        conv_path = get_intra_convention(link_convention)
        if os.path.isfile(conv_path):
            url_Gdrive_convention = 'https://drive.google.com/drive/u/1/folders/16tQuN_2t2lIkj65PSLlymTPAX19_vz5e'
            uploaded_file = Gdrive_upload_file(conv_path, url_Gdrive_convention.split('/')[-1])
            os.remove(conv_path)
            inform_convention_corpo(stage)
            msg = f"*La convention de <@{s_id}|cal> pour <{link_stage}|son stage> chez <{company_link}|{stage['company_name']}> a été téléversée dans <{url_Gdrive_convention}|Gdrive>.*\n \
👉 Ajouter les demandes de <{uploaded_file['webViewLink']}|signatures électronique>"
            client[0].chat_update(channel=data['channel']['id'], ts=data['message']['ts'], text=msg, attachments=msg_convention_no_buttons["attachments"])
    elif "Convoquer l'étudiant" in data['actions'][0]['text']['text']:
        msg = "Le staff a des questions à propos de ton stage, merci de venir au bocal."
        inform_stud(data['actions'][0]['value'], msg)
        msg = f"💬 *<@{s_id}|cal> a été prévenu de venir au bocal pour clarifier sa demande <{link_stage}|de stage> chez chez <{company_link}|{stage['company_name']}>*"
        client[0].chat_update(channel=data['channel']['id'], ts=data['message']['ts'], text=msg, attachments=msg_convention_no_buttons["attachments"])

def interactions(client, data):
    print(data['message']['text'])
    if 'Badgeuse' in data['message']['text']:
        logtime(client, data)
    elif 'companies.intra.42.fr' in data['message']['text']:
        internship(client, data)
