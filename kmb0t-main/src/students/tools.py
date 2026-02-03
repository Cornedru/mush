import os, sys, json, re, time, yaml
from datetime import datetime
import pandas as pd
from slack_sdk import WebClient

with open('data/config.yml', 'r') as f: config = yaml.safe_load(f)

from src.tools import json_intra_api, json_slack_api, jprint

#42cursus studs, not blackhole, not AGU, not staff
def get_studs_data(studs):
    stud_data = []
    for index, stud in studs.iterrows():
        if stud['staff'] == True or stud['login'] == 'tlamart': continue
        data = json_intra_api('GET', f"users/{stud['id']}")
        if any(g['name'] == 'Test account' for g in data['groups']): continue
        for cur in data['cursus_users']:
            if cur['cursus_id'] == 21 and cur['end_at'] == None:
                login = cur['user']['login']
                if cur['user']['usual_first_name']:
                    fist_name = cur['user']['usual_first_name'].encode('UTF-8').decode()
                else:
                    fist_name = cur['user']['first_name'].encode('UTF-8').decode()
                last_name = cur['user']['last_name'].encode('UTF-8').decode()
                stud_data.append([login, fist_name, last_name, cur['level'], cur['user']['wallet'], cur['user']['id']])
    df = pd.DataFrame(stud_data, columns=['login', 'fist_name', 'last_name', 'lvl', 'wallet', 'id'])
    return df
