import os, re, json, time, sys
import subprocess

from src.slack.tools import wait_validation, remove_emoji
from src.slack.help import help_event_msg, help_exam_msg, help_lan_msg


def parse_target(trgt):
    if not (re.match(r"^k[0-2]$", trgt) or \
            re.match(r"^k[0-2]r[0-4]$", trgt) or \
            re.match(r"^k[0-2]r[0-4]p[0-9]{1,2}$", trgt) or \
            trgt == 'all'):
        return 'Wrong target'
    if re.match(r"^k[0-2]r[0-4]p[0-9]{1,2}$", trgt):
        return trgt+'.42mulhouse.fr'
    elif trgt == 'all':
        return 'k0,k1,k2'
    else:
        return trgt

def parse_argument(client, data, command):
    cmds = command.split(' ')

    if len(cmds) == 1 or parse_target(cmds[1]) == 'Wrong target':
        client[0].reactions_add(channel=data['channel'], name='x', timestamp=data['ts'])
        msg = f"❌ Please indicate which target ({cmds[0]} k0 or k0r1 or k0r1p2)"
        client[0].chat_postMessage(channel=data['channel'], thread_ts=data['ts'], text=msg)
        remove_emoji(client, data['channel'], data['ts'], 'eyes')
        sys.exit()
    target = parse_target(cmds[1])
    if len(cmds) == 2: #no option
        return cmds[0], target, ''

    if cmds[0] in ['!exam', '!event', '!lan'] and cmds[2] in ['on', 'off', 'lock']:
        return cmds[0], target, cmds[2]
    if cmds[0] == '!wake' and re.search(r'([1-8])h', cmds[2]):
        return cmds[0], target, re.search(r'([1-8])h', cmds[2]).group(1)
    if cmds[0] == '!wallpaper' and cmds[2] in ['default', 'work-in-progress']:
        return cmds[0], target, cmds[2]

    client[0].reactions_add(channel=data['channel'], name='x', timestamp=data['ts'])
    msg = f"❌ Options are incorrect."
    client[0].chat_postMessage(channel=data['channel'], thread_ts=data['ts'], text=msg)
    remove_emoji(client, data['channel'], data['ts'], 'eyes')
    #TODO: send details about cmds[0] and informations in help.py
    sys.exit()


def ansible(client, data):
    s_cmd, trgt, opt = parse_argument(client, data, data['text'])

    val = 'No validation needed'
    if len(trgt) == 2: val = wait_validation(client, data, 2)
    if len(trgt) == 4: val = wait_validation(client, data, 1)
    if val == 'Invalidated': return 'Invalidated'

    help_msg = False
    if s_cmd == '!wake':
        if opt == '': opt = 0
        cmd = f"ansible-playbook -l {trgt} site.yml --tags wallpaper_wake -e 'ansible_strategy=free duree_wake={opt}'"
    elif s_cmd == '!wallpaper':
        img = opt if len(opt) > 1 else 'slack'
        cmd = f"ansible-playbook -l {trgt} site.yml --tags wallpaper_update -e 'ansible_strategy=free img_wallpaper={img}'"
    elif s_cmd == '!exam' and opt == 'off':
        cmd = f"ansible-playbook -l {trgt} site.yml --tags exam-off -e ansible_strategy=free"
    elif s_cmd == '!exam':
        cmd = f"ansible-playbook -l {trgt} site.yml --tags exam-on -e ansible_strategy=free"
        help_msg = help_exam_msg
    elif s_cmd == '!lan' and opt == 'off':
        cmd = f"ansible-playbook -l {trgt} gaming.yml --tags lan-out -e ansible_strategy=free"
    elif s_cmd == '!lan':
        cmd = f"ansible-playbook -l {trgt} gaming.yml --tags lan-on -e ansible_strategy=free"
        help_msg = help_lan_msg
    elif s_cmd == '!event' and opt == 'off':
        cmd = f"ansible-playbook -l {trgt} site.yml --tags event-off -e ansible_strategy=free"
    elif s_cmd == '!event' and opt == 'lock':
        cmd = f"ansible {trgt} -a 'sudo runuser -l event -c \"XDG_SEAT_PATH=/org/freedesktop/DisplayManager/Seat0 ft_lock\"'"
    elif s_cmd == '!event':
        cmd = f"ansible-playbook -l {trgt} site.yml --tags event-on -e ansible_strategy=free"
        help_msg = help_event_msg
    elif s_cmd == '!reboot':
        cmd = f"ansible {trgt} -a 'sudo reboot'"

    cmd = 'cd ansiblecluster-linux && source venv/bin/activate && ' + cmd

    with open(f"logs/{data['ts']}.out", 'w+') as f_out, open(f"logs/{data['ts']}.err", 'w+') as f_err:
        proc = subprocess.Popen(['ssh', 'ansiblecluster-linux', cmd], shell=False, stdout=f_out, stderr=f_err)
        with open(f"logs/{data['ts']}.pid", 'w+') as f:
            f.write(str(proc.pid)) #save PID si demande de cancel par slack
        proc.wait()
    client[0].reactions_add(channel=data['channel'], name='white_check_mark', timestamp=data['ts'])
    remove_emoji(client, data['channel'], data['ts'], 'eyes')
    if help_msg: client[0].chat_postMessage(channel=data['channel'], thread_ts=data['ts'], text=help_msg)

    return True
