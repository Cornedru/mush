import os, sys, yaml, traceback

with open('data/config.yml', 'r') as f: config = yaml.safe_load(f)

from src.slack.tools import get_slack_id

def is_request_ok(data):
    is_token_valid = False
    if data['token'] == config['slack']['42world']['verif_token'] or \
       data['token'] == config['slack']['42born2code']['verif_token']:
        is_token_valid = True
                
    is_team_id_valid = False
    if 'team_id' in data and data['team_id'] == config['slack']['42world']['team_id'] or \
       'team_id' in data and data['team_id'] == config['slack']['42born2code']['team_id'] or \
       'team' in data and data['team']['id'] == config['slack']['42born2code']['team_id']:
        is_team_id_valid = True

    return is_token_valid and is_team_id_valid

def is_channel_ok(data):
    if 'actions' in data: return True

    if 'channel_id' in data:
        channel_id = data['channel_id']
    elif 'channel' in data:
        channel_id = data['channel']['id']
    elif 'event' in data and 'channel' in data['event']:
        channel_id = data['event']['channel']
    elif 'event' in data and 'item' in data['event']:
        channel_id = data['event']['item']['channel']
    else:
        return False

    intra_shop_chan = ''
    if os.path.isfile('logs/shop_wallpaper.user_infos'):
        with open('logs/shop_wallpaper.user_infos') as f:
            intra_shop_chan = f.read().split('\n')[0]
        
    if channel_id in config['slack']['42world']['valid_channels'] or \
       channel_id in config['slack']['42born2code']['valid_channels'] or \
       channel_id == intra_shop_chan:
        return True
    else:
        return False

def is_user_ok(data, slack_client):
    if 'actions' in data: return True

    if 'event' in data and 'user' in data['event']:
        user_id = data['event']['user']
    elif 'event' in data and 'user_id' in data['event']:
        user_id = data['event']['user_id']
    elif 'user' in data and 'id' in data['user']:
        user_id = data['user']['id']
    else:
        return False

    with open('data/studs/tuteurs.yml') as f: tuteurs = get_slack_id(yaml.safe_load(f))
    with open('data/studs/mentors.yml') as f: mentors = get_slack_id(yaml.safe_load(f))

    if os.path.isfile('logs/shop_wallpaper.user_infos'):
        with open('logs/shop_wallpaper.user_infos') as f:
            tuteurs.append(f.read().split('\n')[1])

    if user_id in config['slack']['42world']['admin_users'] or \
       user_id in config['slack']['42born2code']['admin_users'] or \
       user_id in tuteurs or \
       user_id in mentors:
        return True
    return False


def check_slack_webhook(data, c_42born2code, c_42world):
    try:
        if not is_request_ok(data) or \
           not is_channel_ok(data) or \
           not is_user_ok(data, c_42born2code):
            return False
        else:
            return True
    except:
        c_42world.chat_postMessage(channel=config['slack']['42world']['admin_DM'], text=traceback.format_exc())
        return False
