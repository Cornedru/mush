import os, sys, glob
import signal
import json

from src.tools import json_slack_api, json_intra_api
from src.slack.intra_tools import del_transaction, del_tig, del_coalition, del_title, del_create_event, del_create_exam
from src.slack.tools import remove_emoji
from src.intra.logtime import delete_intra_logtime, stop_intra_logtime
from src.slack.inscription import tutor_inscription
from src.slack.placement import get_exam_placements

def add_log_subprocess(client, event):
    ts = event['item']['ts']
    if not os.path.isfile(f'logs/{ts}.out') and not os.path.isfile(f'logs/{ts}.info'):
        msg = '🤔 no logs attached to this ts slack message.'
        client[0].chat_postMessage(channel=event['item']['channel'], thread_ts=event['item']['ts'], text=msg)
        return

    if os.path.isfile(f'logs/{ts}.info'):
        with open(f"logs/{ts}.info") as f: data_out = f.read()
        client[0].chat_postMessage(channel=event['item']['channel'], thread_ts=event['item']['ts'], text=str(data_out))
    if os.path.isfile(f'logs/{ts}.out'):
        login = json_slack_api(client[0], 'login_from_slack_id', event['user'])
        if len(login) == 0:
            user = client[0].users_profile_get(user=event['user'])
            login = user['profile']['real_name']

        with open(f"logs/{ts}.out") as f: data_out = f.readlines()
        if len(data_out) > 42:
            msg = f"Last 42 lines of `stdout` requested by {login}:\n>[...]{'>'.join(data_out[-42:])}"
        else:
            msg = f"stdout requested by {login}:\n{'>'.join(data_out)}"
        client[0].chat_postMessage(channel=event['item']['channel'], thread_ts=event['item']['ts'], text=msg)
    if os.path.isfile(f'logs/{ts}.err') and os.stat(f"logs/{ts}.err").st_size != 0:
        with open(f"logs/{ts}.err") as f: data_err = f.readlines()
        if len(data_err) > 42:
            msg = f"Last 42 lines of `stderr`:\n>[...]\n{'>'.join(data_err[-42:])}"
        else:
            msg = f"stderr:\n>{'>'.join(data_err)}"
        client[0].chat_postMessage(channel=event['item']['channel'], thread_ts=event['item']['ts'], text=msg)

def cancel_process(client, event, ts):
    with open(f"logs/{ts}.pid") as f: pid = f.readlines()[0]

    login = json_slack_api(client[0], 'login_from_slack_id', event['user'])
    try:
        os.kill(int(pid), signal.SIGTERM)
    except Exception as e:
        msg = f"🤔 Cancel request by {login} but `{e}`."
    else:
        msg = f"❌ Command canceled by {login}."
        remove_emoji(client, event['item']['channel'], event['item']['ts'], 'eyes')
    client[0].chat_postMessage(channel=event['item']['channel'], thread_ts=event['item']['ts'], text=msg)
    #os.system(f"rm {event['item']['ts']}.*")


def stop_wait_validation(client, event, ts):
    ts = event['item']['ts']
    if os.path.isfile(f'logs/{ts}.OK'):
        with open(f'logs/{ts}.OK') as f: nb_ok = f.read()
        with open(f'logs/{ts}.OK', 'w') as f: f.write(f"{nb_ok}x ")
    if os.path.isfile(f'logs/{ts}.info'):
        cancel_login = json_slack_api(client[0], 'login_from_slack_id', event['user'])
        msg = f'Command canceled by {cancel_login}.'
        with open(f'logs/{ts}.info', 'w') as f: f.write(msg)


def cancel_command(client, event):
    ts = event['item']['ts']
    if os.path.isfile(f'logs/{ts}.pid'):
        cancel_process(client, event, ts)
    elif os.path.isfile(f'logs/{ts}.wallet'):
        del_transaction(client, event, ts)
    elif os.path.isfile(f'logs/{ts}.tig'):
        del_tig(client, event, ts)
    elif os.path.isfile(f'logs/{ts}.coa'):
        del_coalition(client, event, ts)
    elif os.path.isfile(f'logs/{ts}.title'):
        del_title(client, event, ts)
    elif os.path.isfile(f'logs/{ts}.create-event'):
        del_create_event(client, event, ts)
    elif os.path.isfile(f'logs/{ts}.create-exam'):
        del_create_exam(client, event, ts)
    else:
        msg = '🤔 Cancel requested but no process/logs attached to this slack msg.'
        client[0].chat_postMessage(channel=event['item']['channel'], thread_ts=ts, text=msg)
    if os.path.isfile(f'logs/{ts}.OK'): stop_wait_validation(client, event, ts)


def add_approuvement(client, event):
    ts = event['item']['ts']
    if os.path.isfile(f'logs/{ts}.OK'):
        with open(f'logs/{ts}.OK') as f: nb_ok = f.read()
        if event['user'] not in nb_ok:
            with open(f'logs/{ts}.OK', 'w') as f: f.write(f"{nb_ok}{event['user']} ")
# participant dans un code annex =
# ic.get(f"/events/{event_id}/events_users").json()

def get_event_participants(client, event):
    ts = event['item']['ts']
    if os.path.isfile(f'logs/{ts}.create-event'):
        with open(f'logs/{ts}.create-event') as f: event_id = f.read().strip()
        participants_ts_file = f'logs/{ts}.participants_exam'
        if os.path.isfile(participants_ts_file):
            with open(participants_ts_file) as f: last_msg_ts = f.read().strip()
            if last_msg_ts:
                try:
                    client[0].chat_delete(channel=event['item']['channel'], ts=last_msg_ts)
                except Exception as e:
                    print(f"Failed to delete previous participants message: {e}", file=sys.stderr, flush=True)
        participants = json_intra_api('GET', f"/events/{event_id}/events_users")
        msg = "Participants in this event:\n"
        for participant in participants:
            msg += f"- {participant['user']['login']}\n"
        resp = client[0].chat_postMessage(channel=event['item']['channel'], thread_ts=ts, text=msg)
        with open(participants_ts_file, 'w') as f: f.write(resp['ts'])

def is_log_now(login):
    location = json_intra_api('GET', f"/users/{login}/locations")
    if location[0]["end_at"] is None:
        return True
    else:
        return False

def get_exam_participants(client, event):
    ts = event['item']['ts']
    if os.path.isfile(f'logs/{ts}.create-exam'):
        with open(f'logs/{ts}.create-exam') as f: exam_id = f.read().strip()
        participants_ts_file = f'logs/{ts}.participants_exam'
        if os.path.isfile(participants_ts_file):
            with open(participants_ts_file) as f: last_msg_ts = f.read().strip()
            if last_msg_ts:
                try:
                    client[0].chat_delete(channel=event['item']['channel'], ts=last_msg_ts)
                except Exception as e:
                    print(f"Failed to delete previous participants message: {e}", file=sys.stderr, flush=True)
        participants = json_intra_api('GET', f"/exams/{exam_id}/exams_users")
        msg = "Participants in this exam:\n"
        for participant in participants:
            if is_log_now(participant['user']['login']):
                msg += f"- 🟢 {participant['user']['login']}\n"
            else:
                msg += f"- ⚫️ {participant['user']['login']}\n"
        resp = client[0].chat_postMessage(channel=event['item']['channel'], thread_ts=ts, text=msg)
        with open(participants_ts_file, 'w') as f: f.write(resp['ts'])

def reaction(client, event):
    if not ('item' in event and event['item']['type'] == 'message'):
        return 'reaction not managed'
    slack_user = client[0].users_profile_get(user=event['user'])
    if slack_user['profile']['real_name_normalized'] == 'KMbOt' or \
    slack_user['profile']['real_name_normalized'] == 'KMb0t':
        return 'reaction from bot not managed'

    if event['reaction'] == 'eyes':
        ts = event['item']['ts']
        if event['item']["ts"]:
            if os.path.isfile(f'logs/{ts}.create-event'):
                get_event_participants(client, event)
            elif os.path.isfile(f'logs/{ts}.create-exam'):
                get_exam_participants(client, event)
            else:
                add_log_subprocess(client, event)

    elif event['reaction'] == 'chair':
        ts = event['item']['ts']
        if event['item']["ts"]:
            if os.path.isfile(f'logs/{ts}.create-exam'):
                get_exam_placements(client, event)

    elif event['reaction'] == 'one':
        tutor_inscription(client, event, slack_user)
    elif event['reaction'] == 'two':
        tutor_inscription(client, event, slack_user)
    elif event['reaction'] == 'x':
        cancel_command(client, event)
    elif event['reaction'] == 'ok':
        add_approuvement(client, event)
    elif event['reaction'] == 'no_entry_sign':
        stop_intra_logtime(client, event['user'], event['item']['ts'])
    elif event['reaction'] == 'wastebasket':
        delete_intra_logtime(client, event, event['item']['ts'])
