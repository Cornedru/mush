import os, sys, yaml
from slack_sdk import WebClient

with open('data/config.yml', 'r') as f: config = yaml.safe_load(f)
c_42world = WebClient(token=config['slack']['42world']['bot_token'])
c_42born2code = WebClient(token=config['slack']['42born2code']['bot_token'])
link_std_mgmt = "https://student-mgmt.42.fr/?query=blackholed%3Astill_running&columns=ph-l-fn-ln-bhd-ckind-creason-lvl&order=blackholed_day-asc&size=100"

from src.google.tools import send_email


def report_blackholed(stud_bh):
    link_stud = f"https://profile.intra.42.fr/users/{stud_bh}"
    msg = f"☠️  <{link_stud}|{stud_bh}> est <{link_std_mgmt}|*blackhole*>. Régulariser sa situation administrative et supprimer son badge d'accès."

    c_42world.chat_postMessage(channel=config['slack']['42world']['KMb0t_channel'], text=msg, unfurl_links=True)
    c_42born2code.chat_postMessage(channel=config['slack']['42born2code']['support_channel'], text=msg.split('. Régulariser')[0], unfurl_links=True)

    msg = msg.replace('<', '<a href="').replace('|', '">').replace('>', '</a>').replace('*', '')
    if send_email('pedago@42mulhouse.fr', 'KMbØt blackhole report', msg, True, cc=['adm@42mulhouse.fr']) == False:
        c_42world.chat_postMessage(channel=config['slack']['42world']['admin_DM'], text='Gmail failed', unfurl_links=True)
