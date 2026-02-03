import os, json, yaml, pickle
import google.oauth2.credentials
from simplegmail import Gmail
import pygsheets

#Use google.py to generate data/google_creds.json from desktop env
#Download data/client_secret.json from google console :
# https://console.cloud.google.com/apis/credentials?authuser=2&project=kmb0t-365507&supportedpurview=project&pli=1
def get_google_token():
    base_dir = os.path.dirname(os.path.realpath(__file__))
    with open(base_dir+'/../../data/google_creds.json', 'r') as f:
      cred = json.load(f)

    credentials = google.oauth2.credentials.Credentials(
          cred.get('token'),
          refresh_token=cred.get('refresh_token'),
          token_uri=cred.get('token_uri'),
          client_id=cred.get('client_id'),
          client_secret=cred.get('client_secret'),
          scopes=cred.get('scopes'),
    )
    return credentials

#Need to modify simplegmail creds managment.
#Remplace src/google/simplegmail.gmail.py to ENV_py3.7/lib/[..]/simplegmail/gmail.py
def send_email(to, subj, msg, signature=False, cc=False, pj=False, token=False):
  params = {
      "to": to,
      "sender": "staff@42mulhouse.fr",
      "subject": subj,
      "msg_html": msg,
      "signature": signature  # use my account signature
    }
  if cc: params.update({"cc": cc})
  if pj: params.update({"attachments": [pj]})

  try:
    gmail = Gmail(_creds=get_google_token())
    message = gmail.send_message(**params)
  except Exception as e:
    print(e)  
    return False
  return True


