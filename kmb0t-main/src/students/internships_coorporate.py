import os ,time
from babel.dates import format_date
from datetime import datetime, timedelta

from src.google.tools import send_email
from src.tools import json_slack_api, inform_stud

url_catalogue_campus = 'https://drive.google.com/file/d/1C34hciTDbfw4MyH2qxpTliUNS5_aobq2/view'
url_catalogue_Pro = 'https://drive.google.com/file/d/1KIs5Lysz6J0ceIksMFjnxicuL1QOroSQ/view'

def inform_convention_corpo(s):
    start_at = datetime.strptime(s['start_at'], "%Y-%m-%dT%H:%M:%S.%fZ") + timedelta(days=1)
    start_formatted = format_date(start_at, "EEEE d MMMM yyyy", locale="fr")
    end_at = datetime.strptime(s['end_at'], "%Y-%m-%dT%H:%M:%S.%fZ") + timedelta(days=1)
    end_formatted = format_date(end_at, "EEEE d MMMM yyyy", locale="fr")
    if s['administration_id'] in [122, 198]:
        extra_sfp = """
Nous attirons votre attention sur le statut de <em>stagiaire de la formation professionnelle</em> de notre étudiant. De ce fait, sa convention de stage diffère légèrement de celle des conventions étudiantes classiques :<br>
<ul><li>La rémunération est facultative, mais nous incitons toujours les entreprises à prévoir une gratification, même symbolique. Elle varie, en règle générale, de 400 à 1 400 €.</li>
<li>Lorsqu'il y en a une, elle est soumise à charges dès le premier euro (pas d'exonération de charges sociales), comme stipulé dans l'article 5 de la convention.</li></ul>
"""
    else:
        extra_sfp = ''
    email_send_conv = f"""
Mme, M. {s['company_boss_user_last_name']},<br>
<br>
Notre étudiant, {s['user']['displayname']}, nous a transmis votre demande de stage, qui se déroulera du <b>{start_formatted} au {end_formatted}</b>.<br>
Les signataires recevront un second courriel afin de procéder à la signature électronique de la convention de stage.<br>
{extra_sfp}<br>
Nous en profitons pour vous transmettre notre <a href="{url_catalogue_campus}">plaquette Entreprise</a>, apportant des informations sur les possiblités d'alternance après-stage, ainsi que notre <a href="{url_catalogue_Pro}">catalogue de formations destiné aux entreprises</a>.<br>
Nous vous remercions par avance pour votre confiance et restons à votre disposition.<br>
"""
    email_cc = [s['user']['email'], s['company_user_email'], 'entreprise@42mulhouse.fr']
    send_email(s['company_boss_user_email'], 'Convention stage 42Mulhouse', email_send_conv, cc=email_cc, signature=True)
    # send_email('yohan@42mulhouse.fr', 'Convention stage 42Mulhouse', email_send_conv)#, cc=email_cc, signature=True)
    url_slide = "https://docs.google.com/presentation/d/e/2PACX-1vQ3VWQPgQ1BUICJfF8Logm1h4zJR88Ui7fF6n5MsXOGBznoIbW_Ni3ex0jzbJAeGmMtNOmqj4lXoOxc/pub#slide=id.g3462217da2f_0_0"
    inform_stud(s['user']['login'], f"📑 Nous avons validé ta demande de stage du *{start_formatted} au {end_formatted}* et une demande de eSignature de la convention te sera envoyé. Si tu as besoin d'éditer la convention merci de prendre contact avec le bocal.\nPour les prochaines étapes tu peux te référer <{url_slide}|aux slides de l'intra>.")

def email_end_internship(s):
    email_fin_stage = f"""
Mme, M. {s['company_user_last_name']},<br>
<br>
Le stage de notre étudiant, {s['user']['displayname']}, prend fin aujourd'hui et nous vous remercions de lui avoir accordé votre confiance.<br>
<br>
Nous espérons qu'il a répondu à vos attentes et serions ravis de recueillir vos impressions sur les points suivants :<br>
<br>
  1. Êtes-vous satisfait du travail fourni par {s['user']['displayname'].split(' ')[0]} ? Les résultats ont-ils été conformes, dépassé ou en deçà de vos attentes ?<br>
  2. Quels sont, selon vous, les points forts et les axes d'amélioration que vous avez observés ?<br>
  3. Envisagez-vous de renouveler cette expérience en proposant une nouvelle offre de stage ?<br>
<br>
Vos réponses resteront confidentielles et ne seront pas partagées avec l'étudiant. Elles nous aideront à affiner notre formation afin de mieux répondre aux besoins des entreprises.<br>
<br>
Nous vous remercions pour votre temps et nous restons à votre disposition.<br>
<br>
Cordialement,
"""
    send_email(s['company_user_email'].lower(), f"Feedback stage {s['user']['first_name']} 42Mulhouse", email_fin_stage, cc=['entreprise@42mulhouse.fr'], signature=True)

# email_relance_3mois = f"""
# Madame/Monsieur {s['company_user_last_name']},

# Il y a trois mois, vous avez accueilli notre étudiant {s['user']['displayname']}, dans le cadre d'un stage d'une durée de {s['duration']} mois.
# Nous espérons que le fruit de son travail fut productif pour vos équipes et serions ravis de continuer à vous accompagner dans vos besoins.

# Si vous le souhaitez, nous serions heureux de recevoir vos offres de stage, que nous transmettrons à nos étudiants.
# Nous pouvons également organiser un rendez-vous dans nos locaux ou en visioconférence, voire planifier une rencontre avec nos étudiants.

# Nous vous remercions par avance pour votre temps et vous souhaitons une excellente journée.

# Cordialement,

# L'équipe 42 Mulhouse
# """