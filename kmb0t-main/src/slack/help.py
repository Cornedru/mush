import sys, os
from src.slack.tools import remove_emoji

all_titles = 'https://42born2code.slack.com/files/U02H15353EC/F07TUDULJCQ/titres?origin_team=T039P7U66&origin_channel=C06RCJDLQJU'

def print_help(client, data):
	remove_emoji(client, data['channel'], data['ts'], 'eyes')
	msg = f"""
Usage:\n
	`!coa [amount] [slug] "[reason]"`\n
	`!unban [login]`\n
	`!event [target] (on/off/lock)`\n
	`!exam [target] (on/off)`\n
	`!lan [target] (on/off)`\n
	`!reboot [target]`\n
	`!stop [login]`\n
	`!tig [2/4/8h] [login] "[reason]" "(occupation)"`\n
	`!titre <{all_titles}|[id]> [login]`\n
	`!wake [target] (1-8h)`\n
	`!wallet [amount] [login] "[reason]"`\n
	`!wallpaper [target] (default/work-in-progress)`\n
	`!create-event "[name]" "[begin_at](24/02/2025 10:00)" "[end_at](24/02/2025 15:00)" "[location]" "[description]"`\n
	`!create-exam "[begin_at](24/02/2025 15:00)" "[end_at](24/02/2025 18:00)" "[location]"`\n
	`!create-exam` (without args) creates an exam the next Thursday from 15h to 18h at K2 location.\n
	

To see logs or people registered react with  👀
To cancel command react with  ❌

		  """
	client[0].chat_postMessage(channel=data['channel'], text=msg, thread_ts=data['ts'])


help_event_msg = """
Event mode is activated. Logout is disabled and the screen will remain ON for the next 5 days. To switch OFF screen or lock session `!event [target] lock`, password to unlock is `event`. To save data, you can use 💾 to create 'sgoinfre' folder. Don't forget to use `!event [target] off` at the end of the event.\n
Following games are available :
  • `42zzle`: rocket game similar to <https://game.42mulhouse.fr|admissions>
  • `shell_game`: cli game, can be improve on <https://gitlab.42mulhouse.fr/Yohan/shellgame/-/tree/piscine?ref_type=heads|Gitlab>
  • `compute-it`: next admissions game
  • `Code blocks games`: learn coding with blocks, for kids
To reset game level use on browser CTRL+SHIFT+DEL and refresh page with CTRL+R. Quit game with CTRL+W.

Following discovery piscines are present :
  • <https://cdn.intra.42.fr/pdf/pdf/139492/fr.subject.pdf|Web Programming Essentials>
  • <https://cdn.intra.42.fr/pdf/pdf/149144/en.subject.pdf|Core Python Programming>
  • AI Fundamentals for All [BETA TEST]
"""

help_exam_msg = """
>Check-list de surveillance d'exam :
  • Au minimum deux tuteurs doivent être présents pour préparer et surveiller l'exam.
  • Préparer l'exam 20-30min avant l'horaire de début en demandant aux étudiants présents dans le kluster de partir et de se déconnecter.
  • Indiquer avec la pancarte que kluster est réservé à l'exam.
  • Déconnecter les étudiants encore log avec le bouton power
  • Vérifier un à un les postes en s'assurant que :
    - Rien ne soit plug en USB.
    - Rien ne soit présent sous le clavier ou le tapis de souris.
  • Basculer en mode exam les postes avec !exam target.
  • Faire rentrer les étudiants à partir de 15min avant le début :
	- Un par un en contrôlant les cartes
	- En les plaçant idéalement les plus espacés possibles
    - En ne faisant pas suivre deux étudiants passant le même examen.
  • Chaque étudiant doit avoir sa carte en évidence sur la table.
  • Annoncer le début de l'exam et fermer la porte.
  • Ne pas accepter de retardataires.
  • S'assurer de la connexion à examshell pendant les 21 premières minutes
  • Faire changer l'étudiant de poste cas de problème individuel.
  • Noter le détail du problème (poste, nature, étudiant, etc.) pour les remonter.
  • Contacter le Bocal en cas de problème plus important.
  • Accompagner un par un les étudiants voulant aller aux toilettes.


>Guidelines spécifiques aux exams des piscines :
  • Fouiller les toilettes avant le début de l'exam
  • Demander aux piscineux de garder leurs photos d'examshell ouvertes jusqu'à contrôle par un surveillant
  • Rappeler que pour demander de l'aide il faut se lever silencieusement.
  • Faire particulièrement attention aux piscineux regardant les écrans voisins.
  • Toutes les heures, emmener aux toilettes du km0 les piscineux le souhaitant et uniquement à ce moment tout en prêtant particulièrement attention qu'il n'y ait pas de discussions lorsqu'ils sont ensemble.
  • Pour l'exam final, vérifier que les aliments apportés par les piscineux sont conformes au règlement.


>Guidelines pour les surveillants :
  • Interdiction de rester trop longuement derrière un étudiant.
  • Possibilité de travailler ou de faire autre chose (1 seul surveillant à la fois) mais rester attentif à l'examen.
  • Pas de musique ni d'écouteurs/casques.
  • Faire des rondes régulièrement.
  • En cas d'enfreinte du règlement, faire sortir l'étudiant et invalider l'exam par le bocal.
  • Aucune aide aux étudiants sur le contenu de l'exam et setup de la session.


Un anti cheat visant à empêcher la triche en examen via l’utilisation d’un clé usb ou d’un volume externe pendant ce dernier. En cas de branchement/débranchement d’un périphérique du genre, une alerte sera envoyée sur slack précisant l’heure exacte et la position du poste concerné. Sources et doc complète sur <https://gitlab.42mulhouse.fr/bdehais/usb_monitoring|Gitlab>.
"""

help_lan_msg = """
Lan mode is activated. Logout is disabled and the screen will remain ON for the next 5 days. Don't forget to use `!event [target] off` at the end of the event.\n
Good games
"""