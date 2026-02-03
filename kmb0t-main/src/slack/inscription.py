import sys, os, re, json, yaml
from datetime import datetime, timedelta
import pytz

def create_inscription(client, data, msg):
    with open('data/config.yml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    channel = config['slack']['42born2code']['tuteurs_channel']
    resp = client[0].chat_postMessage(channel=channel, text=msg)
    main_ts = resp['ts']
    with open(f'logs/{main_ts}.inscription', 'w') as f:
        f.write('inscription message sent')
    client[0].reactions_add(channel=channel, name='one', timestamp=main_ts)
    client[0].reactions_add(channel=channel, name='two', timestamp=main_ts)

def tutor_inscription(client, event, slack_user):
    ts = event['item']['ts']
    reaction = event['reaction']

    if os.path.isfile(f'logs/{ts}.inscription'):
        with open(f'logs/{ts}.inscription') as f:
            lines = f.readlines()

        last_msg_ts = lines[0].strip()
        tutors_data = [line.strip() for line in lines[1:] if line.strip()]

        tutor_login = slack_user['profile']['display_name_normalized']
        slot = '1' if reaction == 'one' else '2'
        tutor_entry = f"{tutor_login}:{slot}"
        existing_entries = [entry for entry in tutors_data if entry.startswith(f"{tutor_login}:")]

        if existing_entries:
            if tutor_entry in tutors_data:
                tutors_data.remove(tutor_entry)
            else:
                for old_entry in existing_entries:
                    tutors_data.remove(old_entry)
                tutors_data.append(tutor_entry)
        else:
            tutors_data.append(tutor_entry)

        if last_msg_ts != 'inscription message sent':
            try:
                client[0].chat_delete(channel=event['item']['channel'], ts=last_msg_ts)
            except Exception as e:
                print(f"Failed to delete previous inscription message: {e}", file=sys.stderr, flush=True)

        with open('data/config.yml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        channel = config['slack']['42born2code']['tuteurs_channel']

        slot1_tutors = [entry.split(':')[0] for entry in tutors_data if entry.endswith(':1')]
        slot2_tutors = [entry.split(':')[0] for entry in tutors_data if entry.endswith(':2')]

        msg = "Inscription des tuteurs pour l'exam:\n\n"
        msg += f"**Créneau 1️⃣** ({len(slot1_tutors)} tuteur(s)):\n"
        if slot1_tutors:
            for tutor in slot1_tutors:
                msg += f"  • {tutor}\n"
        else:
            msg += "  _Aucun tuteur inscrit_\n"

        msg += f"\n**Créneau 2️⃣** ({len(slot2_tutors)} tuteur(s)):\n"
        if slot2_tutors:
            for tutor in slot2_tutors:
                msg += f"  • {tutor}\n"
        else:
            msg += "  _Aucun tuteur inscrit_\n"

        resp = client[0].chat_postMessage(channel=channel, thread_ts=ts, text=msg)
        new_msg_ts = resp['ts']

        with open(f'logs/{ts}.inscription', 'w') as f:
            f.write(f"{new_msg_ts}\n")
            for entry in tutors_data:
                f.write(f"{entry}\n")