import os, sys, traceback, yaml

os.chdir(os.path.dirname(os.path.realpath(__file__))) #execute by crontab from /
with open('data/config.yml', 'r') as f: config = yaml.safe_load(f)

from src.tools import jprint, json_intra_api
from src.slack.intra_tools import get_logins
from src.students.tools import get_studs_data
from src.students.intra import set_intra_group
from src.students.slack import set_slack_channel
from src.students.internships import sync_internships
from src.google.data import get_studs_gsheet
from src.students.cursus import ft_transcendence_locked, minishell
import pandas as pd
##
# This script is executed everyday
##

def sync_gsheet(df_studs):
    for gsheet_id in config['gsheet']['promos']:
        gsheet = get_studs_gsheet(gsheet_id, ['Login', 'Prénom', 'Nom', 'Email'])
        if 'Error' in gsheet:
            print(gsheet, file=sys.stderr, flush=True)
            return 'Gsheet broken'
        dict_gsheet = gsheet.to_dict(orient='records')
        for stud in dict_gsheet:
            if stud['Login'] not in df_studs['login'].values:
                print(stud['Login'])
                print(gsheet_id)
            # print(stud)
        # print(type(dict_gsheet))


sys.stdout, sys.stderr = open('logs/kmb0t.out', 'a'), open('logs/kmb0t.err', 'a')
os.system('rm -rf logs/tmp') #Comment for testing
os.system(f'find ./logs/* -type f -mtime +7 -delete')

try: sync_internships()
except: print(traceback.format_exc(), file=sys.stderr, flush=True)

try:
    studs = get_logins()
    df_studs = get_studs_data(studs)
    for index, row in df_studs.iterrows():
        set_intra_group(row['login'], row['id'])
    set_slack_channel()
except: print(traceback.format_exc(), file=sys.stderr, flush=True)

try: 
    ft_transcendence_locked()
    minishell()
except: print(traceback.format_exc(), file=sys.stderr, flush=True)


# sync_gsheet(df_studs) #work with abel Gsheet to sync badge

