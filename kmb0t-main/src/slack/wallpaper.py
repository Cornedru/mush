import os, re, sys, json, yaml
import requests
from src.slack.tools import wait_validation, remove_emoji
from src.tools import json_slack_api

with open('data/config.yml', 'r') as f: config = yaml.safe_load(f)
with open('data/studs/bde.yml') as f: bde_list = yaml.safe_load(f) or []

def wallpaper_shop(client, data):
    if os.path.isfile(f"logs/{data['user']}.checking_wallpaper"):
        msg = ":x: Ta dernière image est en cours de validation.\rTu pourras renvoyer une image si elle est refusée par le staff/tuteurs."
        client[0].chat_postMessage(channel=data['channel'], text=msg)
        remove_emoji(client, data['channel'], data['ts'], 'eyes')
        sys.exit()

    login = json_slack_api(client[0], 'login_from_slack_id', data['user'])
    link_stud = f"https://profile.intra.42.fr/users/{login}"
    file_permalink = data['files'][0]['permalink']
    msg = f"""
<{link_stud}|{login}> souhaite diffuser en clusters l'<{file_permalink}|image ci-dessous>.\r
Veuillez vérifier qu'elle n'offense personne et qu'elle respecte le règlement.
    """
    slack_msg = client[0].chat_postMessage(channel=config['slack']['42born2code']['KMb0t_channel'], text=msg)
    if data['user'] in config['slack']['42born2code']['admin_users'] or login in bde_list:
        if login in bde_list: client[0].chat_postMessage(channel=config['slack']['42born2code']['KMb0t_channel'], text=f'!wallet 21 {login} "You are a BDE member, refund shop wallpaper"')
        with open(f"logs/{data['user']}.wallpaper_OK", 'w') as f: pass
        return 'Send by staff or bde'
    with open(f"logs/{data['user']}.checking_wallpaper", 'w') as f: pass
    if wait_validation(client, slack_msg, 2) == 'Invalidated':
        os.remove(f"logs/{data['user']}.checking_wallpaper")
        return 'Invalidated'
    os.rename(f"logs/{data['user']}.checking_wallpaper", f"logs/{data['user']}.wallpaper_OK")

def wallpaper(client, data):
    file_url = data['files'][0]['url_private_download']
    ext = file_url.split('.')[-1].lower()

    if not ext.lower() in ['png', 'jpg', 'jpeg', 'webp']:
        return client[0].chat_postMessage(channel=data['channel'], text=":x: Wrong file format.")

    client[0].reactions_add(channel=data['channel'], name='eyes', timestamp=data['ts'])

    if os.path.isfile('logs/shop_wallpaper.user_infos'):
        if wallpaper_shop(client, data) == 'Invalidated':
            remove_emoji(client, data['channel'], data['ts'], 'eyes')
            client[0].chat_postMessage(channel=data['channel'], text='Ton image a été refusé, veuillez en envoyer une autre.')
            sys.exit()

    rsa_key = '~/.ssh/ansiblecluster_rsa'
    hostname = 'root@ansiblecluster-linux.42mulhouse.fr'
    bot_token = config['slack'][client[1]]['bot_token']

    cmd = f'''curl {file_url} --header 'Authorization: Bearer {bot_token}' --output /tmp/slack.{ext}'''
    os.system(f'ssh -q -i {rsa_key} -p 4222 -tt {hostname} "{cmd}" 2>/dev/null')
    os.system(f'ssh -q -i {rsa_key} -p 4222 -tt {hostname} "convert /tmp/slack.{ext} /root/ansiblecluster-linux/campus_files/usr/share/42/wallpaper/login-screen-slack.jpg" 2>/dev/null')

    remove_emoji(client, data['channel'], data['ts'], 'eyes')
    client[0].reactions_add(channel=data['channel'], name='white_check_mark', timestamp=data['ts'])
    msg = """
📥 Slack image received and confirmed. Use `!wallpaper [target]` to apply on iMacs :\r
`!wallpaper k0r1p2` to apply to the iMac cluster 0, row 1, post 2.\r
`!wallpaper k0r1` to apply on 14 iMacs located on cluster 1 and row 1.\r
`!wallpaper k0` to apply to all iMacs on cluster 0.\r
`!wallpaper all` to apply to all iMacs.\r\r
⚠️  It will not display if a student is connected or locked.
"""
    client[0].chat_postMessage(channel=data['channel'], text=msg)
    sys.exit()
