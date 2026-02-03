import os, sys, json, yaml, logging
from multiprocessing import Process
from flask import Flask, request
from slack_sdk import WebClient
from datetime import datetime

os.chdir(os.path.dirname(os.path.realpath(__file__))) #to be executed from any path
with open('data/config.yml', 'r') as f: config = yaml.safe_load(f)
c_42world = WebClient(token=config['slack']['42world']['bot_token'])
c_42born2code = WebClient(token=config['slack']['42born2code']['bot_token'])

from src.tools import *
from src.slack.commands import command
from src.slack.wallpaper import wallpaper
from src.slack.reactions import reaction
from src.slack.check import check_slack_webhook
from src.intra.shop import intra_shop, sgoinfre_access
from src.intra.check import check_intra_webhook
from src.intra.close import intra_close
from src.intra.correction import intra_corr
from src.infra.usb import usb_monitoring
from src.slack.interactions import interactions
from src.infra.check import check_campus_webhook
from src.infra.badgeuse import badgeuse
from src.intra.logtime import location
from src.students.mario_hook import mario_hook
from src.infra.monitoring import monitoring
from src.students.cursus import ft_transcendence_validate


app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

def load_request(request):
    try:
        if len(request.data) > 0: data = json.loads(request.data.decode('utf-8'))
        else: data = json.loads(request.form.get('payload'))
        data['remote_addr'] = request.remote_addr
        jprint(data)
    except Exception as e:
        msg = f'ERROR: cannot load incoming request. `{e}`\n```{request.data}```'
        with open('logs/kmb0t.err', 'w') as f: f.write(msg)
        return 'KO'
    return data


@app.route('/', methods=['GET'])
def status():
    return "OK\n", 200

@app.route('/h/slack', methods=['POST'])
def slack():
    data = load_request(request)

    if 'challenge' in data: return json.dumps(data['challenge']), 200

    if data == 'KO' or not check_slack_webhook(data, c_42born2code, c_42world):
        return json.dumps({'success':True}), 200, {'ContentType':'application/json'}
    with open('logs/slack.webhook', 'a+') as f: f.write(f"{datetime.now()}\n{json.dumps(data, indent=2)}\n")

    if 'team_id' in data and data['team_id'] == config['slack']['42world']['team_id']:
        client = (c_42world, '42world')
    elif ('team_id' in data and data['team_id'] == config['slack']['42born2code']['team_id']) or\
         ('team' in data and data['team']['id'] == config['slack']['42born2code']['team_id']):
        client = (c_42born2code, '42born2code')

    if 'actions' in data:
        p = Process(target=interactions, args=(client, data))
    elif 'files' in data['event'] and data['event']['channel'][0] == 'D':
        p = Process(target=wallpaper, args=(client, data['event']))
    elif 'text' in data['event'] and 'parent_user_id' not in data['event'] and len(data['event']['text']) > 0 and data['event']['text'][0] == '!':
        p = Process(target=command, args=(client, data['event']))
    elif 'reaction' in data['event']:
        p = Process(target=reaction, args=(client, data['event']))
    else:
        return json.dumps({'success':True}), 200, {'ContentType':'application/json'}
    p.start()

    return json.dumps({'success':True}), 200, {'ContentType':'application/json'}

@app.route('/h/intra', methods=['POST'])
def intra():
    data = load_request(request)

    event_type = check_intra_webhook(request.headers['X-Secret'])
    if data == 'KO' or event_type == 'KO' :
        return json.dumps({'success':True}), 200, {'ContentType':'application/json'}
    with open('logs/intra.webhook', 'a+') as f: f.write(f'{datetime.now()} {event_type}\n{json.dumps(data, indent=2)}\n')

    client = (c_42world, '42world')

    if 'transactable_type' in data:
        p = Process(target=intra_shop, args=(client, data))
    elif 'closer' in data:
        p = Process(target=intra_close, args=(client, data))
    elif 'scaleteam' in event_type:
        p = Process(target=intra_corr, args=(data, event_type))
    elif 'location' in event_type:
        p = Process(target=location, args=(data, event_type, c_42born2code))
    elif 'projectsuser' in event_type:
        p = Process(target=ft_transcendence_validate, args=(client, data))
    else:
        return json.dumps({'success':True}), 200, {'ContentType':'application/json'}
    p.start()

    return json.dumps({'success':True}), 200, {'ContentType':'application/json'}

@app.route('/h/campus', methods=['POST'])
def campus():
    data = load_request(request)
    jprint(data)
    if 'alerts' in data: #grafana webhook
        data['type'] = 'monitoring'
        data['hash'] = request.headers.get('Authorization', '')
    if data == 'KO' or 'type' not in data or not check_campus_webhook(data):
        return json.dumps({'success':True}), 200, {'ContentType':'application/json'}
    with open('logs/campus.webhook', 'a+') as f: f.write(f"{datetime.now()}\n{json.dumps(data, indent=2)}\n")

    if data['type'] == 'power_btn' or 'exam_' in data['type']:
        p = Process(target=usb_monitoring, args=(data,))
    elif data['type'] == 'badgeuse':
        p = Process(target=badgeuse, args=(data,))
    elif data['type'] == 'mario':
        p = Process(target=mario_hook, args=(data,))
    elif data['type'] == 'monitoring':
        p = Process(target=monitoring, args=(data,))
    elif data['type'] == 'shop.42mulhouse.fr':
        p = Process(target=sgoinfre_access, args=(data,))
    else:
        return json.dumps({'success':True}), 200, {'ContentType':'application/json'}
    p.start()

    return json.dumps({'success':True}), 200, {'ContentType':'application/json'}


if __name__ == '__main__':
    sys.stdout, sys.stderr = open('logs/kmb0t.out', 'a'), open('logs/kmb0t.err', 'a')
    p = Process(target=send_error, args=(c_42born2code,)); p.start()
    app.run(host="0.0.0.0", port=8080)
