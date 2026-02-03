import sys, re, os, yaml
from slack_sdk import WebClient
from datetime import datetime, timezone
from dateutil.parser import isoparse

with open('data/config.yml', 'r') as f: config = yaml.safe_load(f)
from src.tools import jprint

c_42born2code = WebClient(token=config['slack']['42born2code']['bot_token'])
channel = config['slack']['42born2code']['campus_channel'] #'U02H15353EC' yohan DM for testing

def count_instances(alerts):
    ret = []
    for elem in alerts:
        instance = elem['labels']['instance'].split(':')[0]
        now = datetime.now(timezone.utc)
        start_at_dt = isoparse(elem["startsAt"])
        delta_hours = int((now - start_at_dt).total_seconds() // 3600)
        ret.append((delta_hours, instance))
    ret.sort(reverse=True)
    return ret

def monitoring(data):
    if 'DatasourceError' in data['groupLabels']['alertname']: return print(data['title'], file=sys.stderr, flush=True)
    instances = count_instances(data['alerts'])
    print(instances)
    if len(instances) == 1:
        msg_thread = False
        if 'TargetDown' in data['title']:
            msg = f"😶‍🌫 {instances[-1][1]} is unreachable."
        elif 'HighMemoryUsage' in data['title']:
            msg = f"😋 {instances[-1][1]} is using 90% of RAM for the last 2 minutes."
        if 'HighCPUUsage' in data['title']:
            msg = f"🥵 {instances[-1][1]} is using all CPU for the last 5 minutes."
    else:
        if 'TargetDown' in data['title']:
            msg = f"😶‍🌫 {instances[-1][1]} and {len(instances) - 1} computers are unreachable."
            msg_thread = "\n".join(f"{instance} down for {hours}h" for hours, instance in instances)
        elif 'HighMemoryUsage' in data['title']:
            msg = f"😋 {instances[-1][1]} and {len(instances) - 1} computers are using 90% of RAM for the last 2 minutes."
            msg_thread = "\n".join(f"{instance} down for {hours}h" for hours, instance in instances)
        if 'HighCPUUsage' in data['title']:
            msg = f"🥵 {instances[-1][1]} and {len(instances) - 1} computers are using all CPU for the last 5 minutes."
            msg_thread = "\n".join(f"{instance} down for {hours}h" for hours, instance in instances)
    
    link_grafana_3h = 'https://monitoring.42mulhouse.fr/grafana/d/1/kluster-node-exporter-full?orgId=2&var-job=KX&var-row=RX&var-node=FULL:9100&refresh=2s&from=now-3h&to=now'
    match = re.search(r'k(\d+)r(\d+)p(\d+)', msg)
    k, r, p = match.groups()
    link_grafana_3h = link_grafana_3h.replace('KX', 'k'+k).replace('RX', 'r'+r).replace('FULL', f'k{k}r{r}p{p}')
    msg = msg.replace(f'k{k}r{r}p{p}', f"<{link_grafana_3h}|k{k}r{r}p{p}>")
    ret = c_42born2code.chat_postMessage(channel=channel, text=msg)
    if msg_thread: c_42born2code.chat_postMessage(channel=channel, text=msg_thread, thread_ts=ret['ts'])
