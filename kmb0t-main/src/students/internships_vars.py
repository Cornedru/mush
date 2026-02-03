import json
from datetime import datetime, timedelta
from babel.dates import format_date


def get_msg_internship(s):
    start_at = datetime.strptime(s['start_at'], "%Y-%m-%dT%H:%M:%S.%fZ") + timedelta(days=1)
    start_formatted = format_date(start_at, "EEEE d MMMM yyyy", locale="fr")
    end_at = datetime.strptime(s['end_at'], "%Y-%m-%dT%H:%M:%S.%fZ") + timedelta(days=1)
    end_formatted = format_date(end_at, "EEEE d MMMM yyyy", locale="fr")
    msg_convention = {
        "attachments": [
            {
                "color": "#2eb886",  # Green sidebar (change to any color you want)
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"""
📅 Du {start_formatted} au {end_formatted} 📍{s['internship_city']} {s['internship_postal']}, {s['internship_country']}\n
_{s['subject']}_
✉️ BOSS: `{s['company_boss_user_email']}`  TUTOR: `{s['company_user_email']}`\n
    """
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "emoji": True,
                                    "text": "Informer l'entreprise"
                                },
                                "style": "primary",
                                "value": f"{s['id']}={s['user']['login']}"
                            },
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "emoji": True,
                                    "text": "Convoquer l'étudiant"
                                },
                                "style": "danger",
                                "value": f"{s['id']}={s['user']['login']}"
                            }
                        ]
                    }
                ]
            }
        ]
    }
    return msg_convention
