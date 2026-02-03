import os, sys, yaml

with open('data/config.yml', 'r') as f: config = yaml.safe_load(f)

from src.infra.usb import generate_hash

def check_campus_webhook(data):
    if 'hash' in data and (
            data['hash'] == config['infra']['badgeuse_key'] or
            data['hash'] == config['infra']['monitoring'] or
            data['hash'] == f"Bearer {config['infra']['grafana']}" or
            data['hash'] == config['infra']['shop'] or
            data['hash'] == config['infra']['mario_key']
        ):
        return True

    hash = generate_hash(data)
    if not 'hash' in data or hash == 'wrong request' or hash != data['hash']:
        return False
    
    return True
