import sys, os, json, yaml
import pygsheets
import pandas as pd
import numpy as np

with open('data/config.yml', 'r') as f: config = yaml.safe_load(f)

from src.google.tools import get_google_token


def save_stage_gsheet(df):
    gc = pygsheets.authorize(custom_credentials=get_google_token())
    sht1 = gc.open_by_key(config['gsheet']['stages'])
    wks = sht1.worksheet_by_title("Stages")
    wks.set_dataframe(df, (0,0))

def save_stage_stud_gsheet(df):
    gc = pygsheets.authorize(custom_credentials=get_google_token())
    sht1 = gc.open_by_key(config['gsheet']['stages_stud'])
    wks = sht1.worksheet_by_title("Stages")
    wks.set_dataframe(df, (2,1))

def get_studs_gsheet(gsheet_id, fields):
  try:
    gc = pygsheets.authorize(custom_credentials=get_google_token())
    spreadsheet = gc.open_by_key(gsheet_id)

    if 'Liste à jour' not in [s.title for s in spreadsheet.worksheets()]:
      return f'Error in gheet {spreadsheet.title}: sheet "Liste à jour" not present'
    worksheet = spreadsheet.worksheet_by_title('Liste à jour')
    data = worksheet.get_all_values()
    df = pd.DataFrame.from_records(data[1:], columns=data[0])
    df.replace('', np.nan, inplace=True)
    df.dropna(how='all', inplace=True)
  except Exception as e:
    return f'Error: {e}'

  for f in fields:
    if f not in df.columns: return f'Error in gheet {spreadsheet.title}: {f} colomn not in gsheet'
  return df[fields]
