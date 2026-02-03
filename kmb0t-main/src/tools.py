import sys, os, json, yaml, time, re
from slack_sdk import WebClient

with open('data/config.yml', 'r') as f: config = yaml.safe_load(f)
c_42born2code = WebClient(token=config['slack']['42born2code']['bot_token'])
if not os.path.exists('logs'): os.mkdir('logs')
if not os.path.exists('logs/tmp'): os.mkdir('logs/tmp')


from src.api42.intra import ic

def jprint(data, f=False):
  if type(data) is list:
    for item in data:
      jprint(item)
  else:
    data = dict(data) if type(data) is not dict else data
    formatted_json = json.dumps(data, sort_keys=True, indent=4)
    #print(formatted_json) #windows sinon :
    from pygments import highlight, lexers, formatters
    colorful_json = highlight(formatted_json, lexers.JsonLexer(), formatters.TerminalFormatter())
    print(colorful_json)
    if f:
      with open('log.txt', 'a+') as flog:
        flog.write(colorful_json)

def slack_json():
    jsondata = ""
    with open('data/slack.json', 'r') as jsonfile:
        for line in jsonfile:
            jsondata += line.split("//")[0]
    json_slack = json.loads(jsondata)
    return json_slack

def split_list(list_string):
  list_of_list=[[]]
  for i in list_string:
      if len(i)>0:
          list_of_list[-1].append(i)
      else:
          list_of_list.append([])
  return list_of_list

#42_cursus_id=21
#c-piscine_id=9
#42mulhouse_campus_id=48

def json_intra_api(typ, route, payload={}, refresh=False) -> dict:
    f_name = route.replace('/', '.')
    if typ == 'GET' and not refresh and os.path.isdir('logs/tmp') and os.path.exists('logs/tmp/'+f_name+'.json'):
        with open('logs/tmp/'+f_name+'.json') as data_file:    
            data = json.load(data_file)
    else:
        if not os.path.isdir('logs/tmp'): os.mkdir('logs/tmp')
        attempt = 1
        while attempt < 5:
            try: 
                if typ == 'GET':
                    data = ic.pages_threaded(route, params=payload)
                    with open('logs/tmp/'+f_name+'.json', 'w+') as f: json.dump(data, f, indent=4)
                elif typ == 'POST': data = ic.post(route, params=payload)
                elif typ == 'PUT': data = ic.put(route, params=payload)
                elif typ == 'DEL': data = ic.delete(route)
                break
            except ValueError as e:
                if attempt == 4: return f"intra error:{err}"
                if re.search(r"b'{(.*?)}'", e.args[0]):
                    err = re.search(r"b'{(.*?)}'", e.args[0]).group(1)
                else: err = e.args[0]
                print(f'Intra request failed for {typ} {route} {err} params={payload}.\nNext retry in {4 ** attempt}s, {attempt}/3', file=sys.stderr, flush=True)
                time.sleep(4 ** attempt)
            attempt += 1
            if attempt == 5: return f"intra error not catched:{err}"
    return data

def json_slack_api(slack, route, args):
    if route == 'slack_id_from_login':
        login = args
        with open('data/studs/slack.yml', 'r+') as f:
            slack_user_id = yaml.safe_load(f)['42born2code'].get(login)
        if slack_user_id == None:
            try: 
                slack_user = slack.users_lookupByEmail(email=f"{login}@student.42mulhouse.fr")
                slack_user_id = slack_user['user']['id']
                time.sleep(1) #slack rate limit = 100/min
            except Exception as e:
                #print(f'c_42born2code.users_lookupByEmail failed with `{login}`.\nInvite this user and delete data/studs/slack.yml entry to update his slack id.', file=sys.stderr, flush=True)
                slack_user_id = 'login not in slack'
            with open('data/studs/slack.yml', 'a') as f:
                f.write(f'    {login}: "{slack_user_id}"\n')
        return slack_user_id
    elif route == 'login_from_slack_id':
        slack_id = args
        email = slack.users_profile_get(user=slack_id).data['profile']['email']
        login = email.split('@')[0]
        if login == 'yohan': login = 'yoyostud'
        return login

def send_error(slack):
    sys.stderr = open(os.devnull, 'w')
    while True:
        if os.path.isfile('logs/kmb0t.err') and os.path.getsize('logs/kmb0t.err') > 0:
            with open('logs/kmb0t.err', 'r') as f: msg = f.read()
            with open('logs/kmb0t.err', 'w') as f: f.write('')
            slack.chat_postMessage(channel=config['slack']['42born2code']['error_channel'], text='```'+msg+'```')
        time.sleep(2) #rate limite


def inform_stud(login, msg):
    slack_id = json_slack_api(c_42born2code, 'slack_id_from_login', login)
    if slack_id != 'login not in slack':
        DM_stud = c_42born2code.conversations_open(users=slack_id)
        c_42born2code.chat_postMessage(channel=DM_stud['channel']['id'], text=msg)

#Pour trouver le short_name de l'emoji pour client[0].reactions_add :
#https://raw.githubusercontent.com/iamcal/emoji-data/master/emoji.json
#Recherche le code uni de l'emoji ✅ = 2705 = white_check_mark
