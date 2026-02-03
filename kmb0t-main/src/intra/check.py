import os, yaml
with open('data/config.yml', 'r') as f: config = yaml.safe_load(f)

def check_intra_webhook(token):
   for key, value in config['intra']['webhook'].items():
      if token == value: return key
   return 'KO'
