"""
    Handle the requests from Mario
"""
from slack_sdk import WebClient
import yaml

with open('data/config.yml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)
channel = config['slack']['42born2code']['error_channel'] #TODO: replace later once ready by support_channel
c_42born2code = WebClient(token=config['slack']['42born2code']['bot_token'])


def add_flags_details(flags, thread_ts):
    '''
        Add the flags details in a given thread.
    '''
    message = ""
    for k in flags:
        flag = flags[k]
        applicable = flag.get("applicable", True)

        if applicable:
            value = round(flag["value"], 5)
            threshold = round(flag["threshold"], 5)
            status = "🔥" if flag["triggered"] else "🆗"
            message += f"{status} {k}: {value}/{threshold}\n{flag['description']}\n"
        else:
            status = "⏸️"
            message += f"{status} {k}: N/A\n{flag['description']}\n"

        if flag.get("details"):
            message += f"_{flag['details']}_\n"
        message += "\n"
    c_42born2code.chat_postMessage(channel=channel, thread_ts=thread_ts, text=message)

def mario_hook(data):
    '''
        Send message to Slack according to the data from Mario.
        We assume that the datetimes are in the correct time zone.

        Refer to https://gitlab.42mulhouse.fr/nlederge/mushroom_world
    '''
    analysis = data["analysis"]
    is_suspicious = analysis["suspicious"]

    corrector_login = data["corrector"]["login"]
    corrector = f"<https://profile.intra.42.fr/users/{corrector_login}|{corrector_login}>"

    project = data["project"]["name"]
    correcteds = [c["login"] for c in data["correcteds"]]

    begin_at_str = data["correction"]["begin_at"]
    date = begin_at_str.split("T")[0]
    hour = begin_at_str.split("T")[1][:5]  # HH:MM only

    flags = analysis["flags"]

    group_string = ", ".join(f"<https://profile.intra.42.fr/users/{c}|{c}>" for c in correcteds)

    applicable_count = analysis.get("applicable_count", analysis["total_flags"])
    emoji = "🔥" if is_suspicious else "📡"
    message = (
        f"{emoji} {corrector} corrige le projet {project} du groupe {group_string} le {date} à {hour}.\n"
        f"Score: {analysis['final_score']:.3f} | Flags: {analysis['triggered_count']}/{applicable_count} (applicable: {applicable_count}/{analysis['total_flags']})"
    )
    resp = c_42born2code.chat_postMessage(channel=channel, text=message, unfurl_links=True)
    thread_ts = resp["ts"]

    add_flags_details(flags, thread_ts)
