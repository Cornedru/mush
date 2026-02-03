import sys, os, yaml, json, time, re
from slack_sdk import WebClient
import subprocess
import requests

from src.tools import json_slack_api, inform_stud, json_intra_api
from src.slack.intra_tools import get_logins

with open('data/config.yml', 'r') as f: config = yaml.safe_load(f)
url_storage = 'https://student-storage-linux.42mulhouse.fr/api/v1'
token = config['infra']['homemaker_token']
c_42born2code = WebClient(token=config['slack']['42born2code']['bot_token'])


def shop_home(data, action, link_stud):
    while os.path.exists('logs/homemakerctl.busy'): time.sleep(1)
    with open('logs/homemakerctl.busy', 'w') as f: pass
    login = data['user']['login']

    cmd = ['homemakerctl', '--url', url_storage, '-t', token, 'homes', 'list', '-i', login]
    ret = subprocess.run(cmd, stdout=subprocess.PIPE).stdout.decode('utf-8')
    size = int(re.search(' ([0-9]+)\.?[0-9]? GiB', ret).group(1))
    if size >= 20: size += 1
    if size >= 34: size += 1
    if 'iqn.fr.42' in ret: #HOME in used
        poste = re.search(r'\:(.*?)\.42mulhouse', ret).group(1)
        ssh_cmd = f"'cd ansiblecluster-linux && source venv/bin/activate && ansible {poste}.42mulhouse.fr -a \"sudo pkill -9 -u {login}\"'"
        os.system(f"ssh ansiblecluster-linux.42mulhouse.fr -p 4222 -i ~/.ssh/ansiblecluster_rsa {ssh_cmd}")
        time.sleep(5)

    ret = subprocess.run(cmd, stdout=subprocess.PIPE).stdout.decode('utf-8')
    if 'iqn.fr.42' in ret: #HOME still in used
        inform_stud(login, '❌ Error during disconnect your HOME from server. Please contact bocal.')
        print(f"❌ Error during disconnect {login}'s HOME with homemaker for {action} from intra shop.")
        os.remove('logs/homemakerctl.busy')
        sys.exit()
    full_size = re.search(' ([0-9]+\.?[0-9]?) GiB', ret).group(1)
    if action == 'upgrade':
        os.system(f"homemakerctl --url {url_storage} -t {token} homes update -s {size + 2} -i {login}")
        msg = f"💽 Ton HOME de {full_size} GiB a été augmenté de +1 GiB."
        public_msg = f"💽 <{link_stud}|{login}> HOME de {full_size} GiB a été augmenté de +1 GiB."
    elif action == 'reset':
        os.system(f"homemakerctl --url {url_storage} -t {token} homes delete -i {login}")
        os.system(f"homemakerctl --url {url_storage} -t {token} homes create -i {login} -s {size + 1}")
        msg = f"💽 Ton HOME de {full_size} GiB a été réinitialisé."
        public_msg = f"💽 <{link_stud}|{login}> a réinitialisé son HOME de {full_size} GiB."
    inform_stud(login, msg)
    os.remove('logs/homemakerctl.busy')
    return public_msg


def shop_wallpaper(client, data):
    slack_id = json_slack_api(c_42born2code, 'slack_id_from_login', data['user']['login'])

    if slack_id not in config['slack']['42born2code']['admin_users'] and os.path.exists('logs/shop_wallpaper.user_infos'):
        with open('logs/shop_wallpaper.user_infos') as f: stud = f.read().split('\n')[2]
        inform_stud(data['user']['login'], f'{stud} a déjà acheté пропаганда, veuillez patienter.')
        while os.path.exists('logs/shop_wallpaper.user_infos'): time.sleep(1) 

    msg = """
Merci pour ta commande. Tu as maintenant 24h pour envoyer ton image ici.\r
Après validation des tuteurs ou staff tu recevras un message pour choisir la zone d'iMacs à diffuser.\r
⚠️ Tu peux diffuser qu'une seule version, si le rendu ne te convient pas il faudra racheter l'item.
    """

    if slack_id == 'login not in slack':
        return print(f"{data['user']['login']} bought shop_wallpaper but is not on slack", file=sys.stderr, flush=True)
    DM_stud = c_42born2code.conversations_open(users=slack_id)
    c_42born2code.chat_postMessage(channel=DM_stud['channel']['id'], text=msg)        

    with open('logs/shop_wallpaper.user_infos', 'w') as f:
        f.write(f"{DM_stud['channel']['id']}\n{slack_id}\n{data['user']['login']}")
    time.sleep(24 * 60 * 60)
    if os.path.exists('logs/shop_wallpaper.user_infos'):
        c_42born2code.chat_postMessage(channel=DM_stud['channel']['id'], text='Aucune image diffusée, veuillez racheter пропаганда.')
        os.remove('logs/shop_wallpaper.user_infos')

def shop_tig(login):
    studs = get_logins()
    stud_id = str(studs.loc[studs['login'] == login]['id'].values[0])
    payload = {
      "close[user_id] ": stud_id,
      "close[closer_id]": stud_id,
      "close[kind]" : "other",
      "close[reason]" : "Shop TIG",
      "close[community_services_attributes]" : [{"[duration]" : str(2 * 3600)}]
    }
    ret = json_intra_api('POST', f'users/{stud_id}/closes', payload=payload)
    close_id = json.loads(ret.text)['id']
    payload = {
      "community_service[close_id]": close_id,
      "community_service[duration]" : str(2 * 3600),
      "community_service[occupation]" : "Boite à TIG",
      "community_service[tiger_id]" : stud_id
    }
    json_intra_api('POST', f'community_services', payload=payload)
    inform_stud(login, f"🤦‍♂️ Merci pour ton achat... de TIG ?! Tu vas recevoir un mail pour décider le jour de ta TIG et débloquer ton compte.")


def shop_sgoinfre(login):
    time.sleep(10) #To let shop.42mulhouse.fr acknowledge his webhook
    sgoinfre_status = requests.get(f'https://shop.42mulhouse.fr/api/v1/sub/info/{login}')
    if sgoinfre_status.status_code == 200:
        return f"💾 Le sgoinfre de 1TO sera monté à ta session lors du login. Les infos de ton abonnement est visibe depuis https://shop.42mulhouse.fr"
    else:
        print(f"Error lors de l'achat de l'item sgoinfre. Le service https://shop.42mulhouse.fr ne répond pas pour {login}", file=sys.stderr, flush=True)
        return "Error", "Une erreur est survenue. Le bocal est informé. Veuillez réclamer vos wallets."

def intra_shop(client, data):
    if 'user' in data and 'login' in data['user']:
        login = data['user']['login']
        link_stud = f"https://profile.intra.42.fr/users/{login}"
    if data['transactable_id'] == 573:
        msg = f"🤦‍♂️ <{link_stud}|{login}> a acheté une TIG dans le shop..."
        shop_tig(login)
    elif data['transactable_id'] == 34:
        msg = shop_home(data, 'upgrade', link_stud)
    elif data['transactable_id'] == 783:
        msg = f"🍻 <{link_stud}|{login}> souhaite se faire inviter par le bocal au Nomad/Pantographe."
    elif data['transactable_id'] in [784, 782, 781, 780, 779, 778, 777, 847]:
        msg = f"💰 <{link_stud}|{login}> a acheté : {data['reason']}."
        inform_stud(login, f"🛍️ Ton article {data['reason']} t'attend au bocal.")
    elif data['transactable_id'] == 831:
        msg = f"☕️ <{link_stud}|{login}> réclame sa boisson Maxicoffee."
    elif data['transactable_id'] == 829:
        msg = f"😋 <{link_stud}|{login}> souhaite se faire inviter au Pantographe/Nomad."
    elif data['transactable_id'] == 820:
        msg = f"🎞️ <{link_stud}|{login}> souhaite diffuser ses oeuvres dans les clusters."
    elif data['transactable_id'] == 1376:
        msg = shop_home(data, 'reset', link_stud)
    elif data['transactable_id'] == 706:
        stud_msg = shop_sgoinfre(login)
        msg = f"💽 <{link_stud}|{login}> s'est abonné au sgoinfre."
        inform_stud(login, stud_msg)
    elif 'value' in data:
        if int(data['value']) > 0:
            msg = f"🤑 <{link_stud}|{login}> received {data['value']} ₳ : `{data['reason']}`" # type: ignore
            inform_stud(login, f"🤑 Tu as gagné {data['value']} ₳ pour `{data['reason']}`")
        else:
            msg = f"💸 <{link_stud}|{login}> a été crédité de {data['value']} ₳ : `{data['reason']}`" # type: ignore
            inform_stud(login, f"💸 Tu as été crédité de {data['value']} ₳ pour `{data['reason']}`")
        if int(data['value']) <= 10: return "No need to spam 42mulhouse_campus channel"
    else: #pas un article connu ?
        return print(f'Bought unknown article from intra shop :\n{data}', file=sys.stderr, flush=True)
    c_42born2code.chat_postMessage(channel=config['slack']['42born2code']['campus_channel'], text=msg)

    #Inform in campus_channel before run shop_wallpaper that takes time
    if data['transactable_id'] == 820: shop_wallpaper(client, data)

def sgoinfre_access(data):
    login = data['login']
    s_id = json_slack_api(c_42born2code, 'slack_id_from_login', login)
    link_stud = f"https://profile.intra.42.fr/users/{login}"
    link_dashboard = "https://shop.42mulhouse.fr/admin/dashboard"
    message = f"🙏  <{link_stud}|{login}> demande un accès au sgoinfre : <{link_dashboard}|traiter la demande> et informer <@{s_id}|cal>"
    c_42born2code.chat_postMessage(channel=config['slack']['42born2code']['support_channel'], text=message)
