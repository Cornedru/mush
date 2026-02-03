import sys, os, yaml
from slack_sdk import WebClient
from io import BytesIO
from PIL import Image
import requests

with open('data/config.yml', 'r') as f: config = yaml.safe_load(f)
c_42born2code = WebClient(token=config['slack']['42born2code']['bot_token'])
with open('data/studs/tuteurs.yml') as f: tuteurs = yaml.safe_load(f) or []
with open('data/studs/mentors.yml') as f: mentors = yaml.safe_load(f) or []
with open('data/studs/phoenix.yml') as f: phoenix = yaml.safe_load(f) or []
with open('data/studs/bde.yml') as f: bde = yaml.safe_load(f) or []
with open('data/studs/lifeguards.yml') as f: lifeguards = yaml.safe_load(f) or []
with open('data/studs/stage.yml') as f: stage = yaml.safe_load(f) or []

from src.tools import json_intra_api, jprint
from src.api42.intra import ic

def get_group_or_delete(login, intra_id):
    gr_mentor, gr_tutor, gr_bde, gr_phoenix, gr_lifeguards, gr_stage = False, False, False, False, False, False
    groups_users = json_intra_api('GET', f"users/{intra_id}/groups_users")

    for gr in groups_users:
        if gr['group']['name'] == 'mentor':
            if login not in mentors:
                json_intra_api('DEL', f"groups_users/{gr['id']}")
                remove_from_tutor(login)
            gr_mentor = True
        elif gr['group']['name'] == 'Tutor':
            if login not in tuteurs:
                json_intra_api('DEL', f"groups_users/{gr['id']}")
                remove_from_tutor(login)
            gr_tutor = True
        elif gr['group']['name'] == 'BDE':
            if login not in bde: json_intra_api('DEL', f"groups_users/{gr['id']}")
            gr_bde = True
        elif gr['group']['name'] == 'PHOENIX':
            if login not in phoenix: json_intra_api('DEL', f"groups_users/{gr['id']}")
            gr_phoenix = True
        elif gr['group']['name'] == 'lifeguard':
            if login not in lifeguards:
                json_intra_api('DEL', f"groups_users/{gr['id']}")
                remove_from_tutor(login)
            gr_lifeguards = True
        elif gr['group']['name'] == 'Stage':
            if login not in stage: json_intra_api('DEL', f"groups_users/{gr['id']}")
            gr_stage = True
    return gr_mentor, gr_tutor, gr_bde, gr_phoenix, gr_lifeguards, gr_stage


def set_stud_group(user_id, group):
    if group == 'Mentor': gr_id = '91'
    if group == 'Tutor': gr_id = '19'
    if group == 'BDE': gr_id = '73'
    if group == 'PHOENIX': gr_id = '47'
    if group == 'lifeguard': gr_id = '294'
    if group == 'stage': gr_id = '373'
    payload = {
      "groups_user[group_id]": gr_id,
      "groups_user[user_id]":  user_id
    }
    json_intra_api('POST', 'groups_users', payload=payload)

def set_intra_group(login, intra_id):
    gr_mentor, gr_tutor, gr_bde, gr_phoenix, gr_lifeguards, gr_stage = get_group_or_delete(login, intra_id)

    if login in mentors and gr_mentor == False:
        set_stud_group(intra_id, 'Mentor')
        update_to_tutor(login, "mentor")
    if login in tuteurs and gr_tutor == False:
        set_stud_group(intra_id, 'Tutor')
        update_to_tutor(login, "tutor")
    if login in bde and gr_bde == False:
        set_stud_group(intra_id, 'BDE')
    if login in phoenix and gr_phoenix == False:
        set_stud_group(intra_id, 'PHOENIX')
    if login in lifeguards and gr_lifeguards == False:
        set_stud_group(intra_id, 'lifeguard')
        update_to_tutor(login, "lifeguard")
    if login in stage and gr_stage == False:
        set_stud_group(intra_id, 'stage')



# Update the user's profile picture to the tutor/mentor/lifeguard badge (main function)
def update_to_tutor(login, type):
    photo = get_user_photo(login)
    if photo:
        with open(f'./data/studs/intra-photo/photos/{login}.jpeg', 'wb') as file:
            file.write(photo)
        if type == "mentor":
            badge_path = "./data/studs/intra-photo/mentor_full.png"
        elif type == "tutor":
            badge_path = "./data/studs/intra-photo/tutor_full.png"
        else:
            badge_path = "./data/studs/intra-photo/lifeguard_full.png"
        # Get image bytes of badge_status
        badge_status = Image.open(badge_path).convert("RGBA")
        if export_final_image([photo, badge_status], login) == 1:
            return
        update_profile_picture(login)
    else:
        print(f"User '{login}' not found in 42 API", file=sys.stderr, flush=True)


# Remove the tutor/mentor/lifeguard badge from the user's profile picture by reuploading the original photo
def remove_from_tutor(login):
    photo = open(f'./data/studs/intra-photo/photos/{login}.jpeg', 'rb')
    file_picture = {"user[image]": photo}

    try:
        response = ic.patch(f"https://api.intra.42.fr/v2/users/{login}", files=file_picture)
        sleep(1000 / 8)
        response.raise_for_status()
        os.remove(f'./data/studs/intra-photo/photos/{login}.jpeg')
    except requests.exceptions.RequestException as e:
        print(f"Error removing profile picture for {login}: {e}", file=sys.stderr, flush=True)


# Update the user's profile picture with mentor/tutor/lifeguard badge
def update_profile_picture(login):
    
    photo = open("tmp.jpeg", 'rb')
    file_picture = {"user[image]": photo}

    try:
        response = ic.patch(f"https://api.intra.42.fr/v2/users/{login}", files=file_picture)
        sleep(1000 / 8)
        response.raise_for_status()
        os.remove("tmp.jpeg")

    except requests.exceptions.RequestException as e:
        print(f"Error updating profile picture for {login}: {e}", file=sys.stderr, flush=True)
        os.remove("tmp.jpeg")


# Get the user's photo from the 42 API
def get_user_photo(login):
    response = ic.get(f"https://api.intra.42.fr/v2/users/{login}")
    sleep(1000 / 8)

    if not response.ok:
        return None
    
    photo_link = response.json().get("image", {}).get("link")
    if not photo_link:
        return None

    photo_response = ic.get(photo_link)
    sleep(1000 / 8)
    if photo_response.status_code != 200:
        return None
    
    return photo_response.content


# Sleep for a given amount of milliseconds to avoid API rate limits
def sleep(ms):
    import time
    time.sleep(ms / 1000)


# Generate and return the final image with the tutor/mentor badge
def export_final_image(layers, login):

    image = Image.open(BytesIO(layers[0]))

    if image.size[0] != image.size[1]:
        print(f"Error: Photo must be square for {login}", file=sys.stderr, flush=True)
        return 1
    
    image = image.resize((2000, 2000), Image.ANTIALIAS)

    final_image = image
    tutor_layer = layers[1]
    final_image.paste(tutor_layer, (0, 0), tutor_layer)
    final_image.save("tmp.jpeg", format="JPEG")

    return 0
