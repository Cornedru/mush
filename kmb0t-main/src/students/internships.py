import os, sys, yaml
import pandas as pd
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from slack_sdk import WebClient

with open('data/config.yml', 'r') as f: config = yaml.safe_load(f)
c_42born2code = WebClient(token=config['slack']['42born2code']['bot_token'])

from src.tools import jprint, json_slack_api, json_intra_api
from src.google.data import save_stage_gsheet, save_stage_stud_gsheet
from src.students.internships_coorporate import email_end_internship
from src.students.internships_vars import get_msg_internship


def get_corrections(user, project):
    if project == 'internship-I-mid': project_id = 1641
    if project == 'internship-I-end': project_id = 1642
    if project == 'internship-II-mid': project_id = 1647
    if project == 'internship-II-end': project_id = 1648
    if project == 'startup-mid': project_id = 1665
    if project == 'startup-end': project_id = 1666

    corrections = json_intra_api('GET', f'users/{user}/scale_teams/as_corrected')
    for corr in corrections:
        if corr['team']['project_id'] == project_id and corr['final_mark']:
            return corr['final_mark'], corr['comment'], corr['team']['users'][0]['projects_user_id']
        if corr['team']['project_id'] == project_id and corr['final_mark']:
            return corr['final_mark'], corr['comment'], corr['team']['users'][0]['projects_user_id']
    return 'no', 'review', 'yet'

def get_corrs_stage(login, administration_id):
    if administration_id in [122, 218, 219, 230]: #122=SFP 218=stud 219=stud-no-xp, 230=SFP-no-xp
        s_mid_mark, s_mid_com, project_user = get_corrections(login, 'internship-I-mid')
        s_mid_link = f"projects.intra.42.fr/projects/work-experience-i-work-experience-i-company-mid-evaluation/projects_users/{project_user}"
        s_end_mark, s_end_com, project_user = get_corrections(login, 'internship-I-end')
        s_end_link = f"projects.intra.42.fr/projects/work-experience-i-work-experience-i-company-final-evaluation/projects_users/{project_user}"
    elif administration_id in [198, 228]: #Internship II - 198=stud 228=SFP
        s_mid_mark, s_mid_com, project_user = get_corrections(login, 'internship-II-mid')
        s_mid_link = f"projects.intra.42.fr/projects/work-experience-ii-work-experience-ii-company-mid-evaluation/projects_users/{project_user}"
        s_end_mark, s_end_com, project_user = get_corrections(login, 'internship-II-end')
        s_end_link = f"projects.intra.42.fr/projects/work-experience-ii-work-experience-ii-company-final-evaluation/projects_users/{project_user}"
    elif administration_id == 204: #Startup Intership 
        s_mid_mark, s_mid_com, project_user = get_corrections(login, 'startup-mid')
        s_mid_link = f"projects.intra.42.fr/projects/startup-experience-startup-experience-tutor-mid-evaluation/projects_users/{project_user}"
        s_end_mark, s_end_com, project_user = get_corrections(login, 'startup-end')
        s_end_link = f"projects.intra.42.fr/projects/startup-experience-startup-experience-tutor-final-evaluation/projects_users/{project_user}"
    else:
        print(f"Sync internship Gsheet error : {login} has an unknown work experience administration_id={administration_id}", file=sys.stderr, flush=True)
        return ('skip'), ('convention')
    return (s_mid_mark, s_mid_com, s_mid_link), (s_end_mark, s_end_com, s_end_link)

def share_internship(start_at, end_at, login, s):
    s_id = json_slack_api(c_42born2code, 'slack_id_from_login', s['user']['login'])
    if start_at.date() + timedelta(days=1) == datetime.today().date():
        msg = f"💼 Le stage de <@{s_id}|cal> chez *{s['company_name']}* à {s['company_city']} commence aujourd'hui, bon courage pour ton sujet: `{s['subject']}`"
        c_42born2code.chat_postMessage(channel=config['slack']['42born2code']['jobs_channel'], text=msg.replace('\r\n', ', '))
    if end_at.date() + timedelta(days=1) == datetime.today().date():
        msg = f"👔 <@{s_id}|cal> termine son stage chez *{s['company_name']}* à {s['company_city']}. Bientôt la Peer Video pour détailler le travail accompli sur: `{s['subject']}`"
        c_42born2code.chat_postMessage(channel=config['slack']['42born2code']['jobs_channel'], text=msg.replace('\r\n', ', '))
        email_end_internship(s)

# Set intra badge about internship
def set_work_experience_liste(today, start_at, end_at, login):
    with open('data/studs/stage.yml') as f: studs_stage = yaml.safe_load(f) or []
    if today > start_at.date() and today < end_at.date() and login not in studs_stage:
        studs_stage.append(login)
        with open('data/studs/stage.yml', 'w') as f: yaml.dump(studs_stage, f)
    elif (today < start_at.date() or today > end_at.date()) and login in studs_stage:
        studs_stage.remove(login)
        with open('data/studs/stage.yml', 'w') as f: yaml.dump(studs_stage, f)

def get_stage_type(administration_id):
    if administration_id == 122: return 'SFP - WE 1'
    elif administration_id == 218: return 'Etudiant - WE 1'
    elif administration_id == 228: return 'Etudiant - WE 2'
    elif administration_id == 198: return 'SFP - WE 2'
    elif administration_id == 204: return 'Startup'
    return 'WE 0 (sans XP)'

def sync_internships():
    all_stages = pd.DataFrame(columns=['NOM', 'PRÉNOM', 'LOGIN', 'CONTRAT', 'ENTREPRISE', 'SUPERVISEUR', 'LIEU', 'ENTRÉE', 'FIN', 'DURÉE', 'RÉMUNÉRATION', 'MID', 'EVALUATION', 'END', 'EVALUATION'])
    all_stages_stud = pd.DataFrame(columns=['LOGIN', 'SUBJECT', 'ENTREPRISE', 'LIEU', 'ENTRÉE', 'DURÉE'])
    stages = json_intra_api('GET', f"internships")
    for s in reversed(stages): #From oldest internship to newest
        login = s['user']['login']
        intra_link = f"https://profile.intra.42.fr/users/{login}"
        s_id = json_slack_api(c_42born2code, 'slack_id_from_login', login)
        link_stage = f"https://companies.intra.42.fr/en/users/{login}/internships/{s['id']}"
        if login in ['yoyotest', 'aalves']: continue
        stage_type = get_stage_type(s['administration_id'])
        if s['state'] == 'need_validation' and s['convention']['convention']['url'] == None and date.today().weekday() < 5:
            company_link = 'https://' + s['company_boss_user_email'].split('@')[-1]
            msg = f"*<@{s_id}|cal> souhaite faire un <{link_stage}|({stage_type.replace(' -', ')')}> chez <{company_link}|{s['company_name']}> :*"
            a_msg_internship = get_msg_internship(s)
            c_42born2code.chat_postMessage(channel=config['slack']['42born2code']['bocal_channel'], text=msg, attachments=a_msg_internship["attachments"])
            continue
        elif s['state'] == 'need_validation' and date.today().weekday() < 5: #Only weekday
            msg = f"💼 <@{s_id}|cal> sent contract signed by *{s['company_name']}* and <{link_stage}|need validation>, please verify and validate."
            c_42born2code.chat_postMessage(channel=config['slack']['42born2code']['bocal_channel'], text=msg)
            continue

        login_link = f'=LIEN_HYPERTEXTE("profile.intra.42.fr/users/{login}";"{login}")'
        contrat_link = f'=LIEN_HYPERTEXTE("companies.intra.42.fr/en/users/{login}";"{stage_type}")'
        if s['company_country'] == 'France': lieu = s['company_postal']
        else: lieu = f"{s['company_city']}, {s['company_country']}"
        start_at = datetime.strptime(s['start_at'], "%Y-%m-%dT%H:%M:%S.%fZ")
        end_at = datetime.strptime(s['end_at'], "%Y-%m-%dT%H:%M:%S.%fZ")
        duree = relativedelta(end_at, start_at)
        total_months = duree.years * 12 + duree.months + (duree.days / 30)

        stage_mid, stage_end = get_corrs_stage(login, s['administration_id'])
        if stage_mid[0] == 'skip': continue
        elif stage_mid[0] != 'no':
            stage_mid_mark = f'=LIEN_HYPERTEXTE("{stage_mid[2]}";"{stage_mid[0]}")'
            stage_mid_comm = stage_mid[1].replace('\n', ' ').replace('\r', ' ')
        else: stage_mid_mark, stage_mid_comm = ' ', ' '
        if stage_end[0] != 'no':
            stage_end_mark = f'=LIEN_HYPERTEXTE("{stage_end[2]}";"{stage_end[0]}")'
            stage_end_comm = stage_end[1].replace('\n', ' ').replace('\r', ' ')
        else: stage_end_mark, stage_end_comm = ' ', ' '

        company_name = s['company_name']
        today = datetime.today().date()
        if s['state'] == 'generated':
            company_name = f"{s['company_name']} ⚠️ SIGNATURE NEEDED"
            if today > start_at.date():
                msg = f"📑 <@{s_id}|cal> havn't <{link_stage}|upload> signed contrat for internship with *{s['company_name']}*, please verify or change dates."
                c_42born2code.chat_postMessage(channel=config['slack']['42born2code']['bocal_channel'], text=msg)
        elif start_at.date() + timedelta(days=1) == today or end_at.date() + timedelta(days=1) == today:
            share_internship(start_at, end_at, login, s)
        set_work_experience_liste(today, start_at, end_at, login)
        
        row = [s['user']['last_name'].upper(), \
               s['user']['first_name'], \
               login_link, \
               contrat_link, \
               company_name, \
               s['company_user_email'].lower(), \
               lieu, \
               start_at, \
               end_at.strftime("%-d %b %Y"), \
               f"{total_months:.1f} mois",
               f"{int(s['salary'])} {s['currency']}",
               stage_mid_mark,
               stage_mid_comm.replace('\n', ' ').replace('\r', ' '),
               stage_end_mark,
               stage_end_comm.replace('\n', ' ').replace('\r', ' ')]

        all_stages.loc[len(all_stages)] = row

        row = [login_link, \
               s['subject'].replace('\n', '– '), \
               company_name, \
               f"{s['company_city'].lower().title()} {lieu}", \
               start_at, \
               f"{total_months:.1f} mois"]
        if stage_type != 'Startup': all_stages_stud.loc[len(all_stages)] = row

    all_stages = all_stages.sort_values(by='ENTRÉE', ascending=False)
    all_stages['ENTRÉE'] = all_stages['ENTRÉE'].dt.strftime('%-d %b %Y')
    save_stage_gsheet(all_stages)
    all_stages_stud = all_stages_stud.sort_values(by='ENTRÉE', ascending=False)
    all_stages_stud['ENTRÉE'] = all_stages_stud['ENTRÉE'].dt.strftime('%-d %b %Y')
    save_stage_stud_gsheet(all_stages_stud)
