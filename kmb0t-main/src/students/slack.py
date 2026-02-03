import os, sys, json, re, time, yaml
from slack_sdk import WebClient

with open('data/config.yml', 'r') as f: config = yaml.safe_load(f)
c_42born2code = WebClient(token=config['slack']['42born2code']['bot_token'])
with open('data/studs/tuteurs.yml') as f: tuteurs = yaml.safe_load(f) or []
with open('data/studs/mentors.yml') as f: mentors = yaml.safe_load(f) or []
with open('data/studs/lifeguards.yml') as f: lifeguards = yaml.safe_load(f) or []
with open('data/studs/bde.yml') as f: bde = yaml.safe_load(f) or []

from src.tools import json_slack_api, jprint

#TODO request Network to accept conversations.kick and put this lines in set_intra_group
def set_slack_channels_specified(channels, studs_login):
    for channel in channels:
        channel_id = config['slack']['42born2code'][channel]

        studs_slack_id = []
        for s in studs_login:
            studs_slack_id.append(json_slack_api(c_42born2code, 'slack_id_from_login', s))

        channel_members = c_42born2code.conversations_members(channel=channel_id)['members']
        for m_id in channel_members:
            if m_id not in studs_slack_id + config['slack']['42born2code']['admin_users']:

                #42Network do not authorized this action. clafoutis: "C’est un peu violent comme droits"
                #c_42born2code.conversations_kick(channel=channel_id, user=m_id)

                login = json_slack_api(c_42born2code, 'login_from_slack_id', m_id)
                c_42born2code.chat_postMessage(channel=channel_id, text=f'<@{m_id}|cal> ({login}) is not in list. Please quit this channel.', unfurl_links=True)

        for s_id in studs_slack_id:
            if s_id not in channel_members and s_id != "login not in slack":
                c_42born2code.conversations_invite(channel=channel_id, users=s_id)

def set_slack_channel():
    tuteurs_mentors_channels = ['tuteurs_channel', 'KMb0t_channel', 'badgeuse_channel', 'campus_channel', 'support_channel']
    lifeguards_channels = ['lifeguards_channel']
    set_slack_channels_specified(tuteurs_mentors_channels, tuteurs + mentors)
    set_slack_channels_specified(lifeguards_channels, tuteurs + mentors + lifeguards)