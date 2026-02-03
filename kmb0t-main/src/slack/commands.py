import os, sys, time, yaml

with open('data/config.yml', 'r') as f: config = yaml.safe_load(f)

from src.slack.help import print_help
from src.slack.ansible import ansible, parse_argument
from src.slack.intra import intra
from src.slack.tools import remove_emoji, add_emoji
from src.intra.logtime import sync_intra_host
import re

def shop_command(client, data):
    cmd = data['text'].split(' ')
    if cmd[0] != '!wallpaper':
        client[0].reactions_add(channel=data['channel'], name='x', timestamp=data['ts'])
        remove_emoji(client, data['channel'], data['ts'], 'eyes')
    elif cmd[0] == '!wallpaper' and os.path.isfile(f"logs/{data['user']}.wallpaper_OK"):
        parse_argument(client, data, data['text'])
        os.remove('logs/shop_wallpaper.user_infos')
        os.remove(f'logs/{data["user"]}.wallpaper_OK')
        client[0].chat_postMessage(channel=config['slack']['42born2code']['KMb0t_channel'], text=f'!wallpaper {cmd[1]}')
        client[0].chat_postMessage(channel=config['slack']['42born2code']['KMb0t_channel'], text=f'!wake {cmd[1]} 4h')
        remove_emoji(client, data['channel'], data['ts'], 'eyes')
        client[0].reactions_add(channel=data['channel'], name='white_check_mark', timestamp=data['ts'])
        time.sleep((4 * 60 * 60)) #4h
        client[0].chat_postMessage(channel=config['slack']['42born2code']['KMb0t_channel'], text=f'!wallpaper {cmd[1]} default')



def command(client, data):
    add_emoji(client, data['channel'], data['ts'], 'eyes')
    
    shop_user = ''
    if os.path.isfile('logs/shop_wallpaper.user_infos'):
        with open('logs/shop_wallpaper.user_infos') as f: shop_user = f.read().split('\n')[1]
        if data['user'] == shop_user: return shop_command(client, data)
    data["text"] = re.sub(r'[«»“”]', '"', data["text"]) #remplacer les doubles quotes non prise en compte
    data["text"] = re.sub(r'[‘’]', "'", data["text"]) #pareil pour les simples
    cmd = data['text'].split(' ')
    if cmd[0] == '!help':
        print_help(client, data)
    elif cmd[0] == '!wake' or cmd[0] == '!event' or cmd[0] == '!lan':
        ansible(client, data)
    elif cmd[0] == '!exam' or cmd[0] == '!update' or cmd[0] == '!wallpaper' or cmd[0] == '!reboot':
        ansible(client, data)
    elif cmd[0] == '!wallet' or cmd[0] == '!tig' or cmd[0] == '!stop' or cmd[0] == '!coa' or cmd[0] == '!titre' or cmd[0] == '!create-event' or cmd[0] == '!create-exam':
        intra(client, data)
    elif cmd[0] == '!unban':
        remove_emoji(client, data['channel'], data['ts'], 'eyes')
        if os.path.isfile(f"logs/badge/{cmd[1]}.banned"):
            os.remove(f"logs/badge/{cmd[1]}.banned")
            add_emoji(client, data['channel'], data['ts'], 'white_check_mark')
        elif os.path.isfile(f"logs/badge/{cmd[1]}.deleted"):
            os.remove(f"logs/badge/{cmd[1]}.deleted")
            add_emoji(client, data['channel'], data['ts'], 'white_check_mark')
        else:
            add_emoji(client, data['channel'], data['ts'], 'x')
    elif cmd[0] == '!stop-KMb0t':
        remove_emoji(client, data['channel'], data['ts'], 'eyes')
        add_emoji(client, data['channel'], data['ts'], 'dead')
        os.system('systemctl stop KMb0t.service')
    else:
        client[0].reactions_add(channel=data['channel'], name='thinking_face', timestamp=data['ts'])
        print_help(client, data)
