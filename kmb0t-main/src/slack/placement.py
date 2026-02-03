import os
import re
import sys

from src.tools import json_intra_api
from collections import defaultdict

def get_next_exam(login):
    participant_quest = json_intra_api('GET', f"/users/{login}/quests_users")
    if participant_quest and isinstance(participant_quest, list):
        first_slug = participant_quest[0]['quest']['slug']
    else :
        first_slug = 'no_quest'

    match = re.search(r'(\d+)$', first_slug)
    if match:
        next_exam = int(match.group(1)) + 1
        return f"{next_exam:02d}"
    else:
        return 'unknown_exam'

def get_cluster(exam_ip):
    dict_cluster_api = {'k0': "10.11.0.0/16", "k1": "10.12.0.0/16", "k2": "10.13.0.0/16"}
    for cluster, ip_range in dict_cluster_api.items():
        if exam_ip == ip_range:
            return cluster
    return 'unknown_cluster'

def calculate_placements(participants_info, sit_per_row):
    from collections import Counter, deque

    rows_count = 4
    total_seats = rows_count * sit_per_row

    exam_counts = Counter(exam for _, exam in participants_info)
    sorted_exams = [exam for exam, _ in exam_counts.most_common()]
    exam_groups = {
        exam: deque([login for login, e in participants_info if e == exam])
        for exam in sorted_exams
    }

    seats = [None] * total_seats

    def count_consecutive_before(idx, exam):
        row_idx = idx // sit_per_row
        seat_idx = idx % sit_per_row
        row_start = row_idx * sit_per_row

        count = 0
        for back in range(1, 3):
            if seat_idx - back < 0:
                break
            prev_idx = row_start + seat_idx - back
            if seats[prev_idx] and seats[prev_idx][1] == exam:
                count += 1
            else:
                break
        return count

    for exam in sorted_exams:
        if not exam_groups[exam]:
            continue

        # Phase 1: Placer 1 sur 2 dans les positions impaires
        for row in range(rows_count):
            row_start = row * sit_per_row
            row_end = row_start + sit_per_row
            for idx in range(row_start, row_end, 2):
                if seats[idx] is None and exam_groups[exam]:
                    seats[idx] = (exam_groups[exam].popleft(), exam)

        # Phase 2: Remplir les trous en respectant max 3 consécutifs
        while exam_groups[exam]:
            placed = False
            for idx in range(total_seats):
                if seats[idx] is None and exam_groups[exam]:
                    if count_consecutive_before(idx, exam) < 2:
                        seats[idx] = (exam_groups[exam].popleft(), exam)
                        placed = True
                    if not exam_groups[exam]:
                        break
            if not placed:
                break

    # Phase 3: Placer tous les étudiants restants sans contrainte
    for exam in sorted_exams:
        while exam_groups[exam]:
            for idx in range(total_seats):
                if seats[idx] is None and exam_groups[exam]:
                    seats[idx] = (exam_groups[exam].popleft(), exam)
                    break

    placements = []
    for idx, val in enumerate(seats):
        if val:
            login, exam = val
            place = f"r{idx // sit_per_row + 1}p{idx % sit_per_row + 1}"
            placements.append((login, place, exam))

    return placements

def get_exam_placements(client, event):
    ts = event['item']['ts']
    if os.path.isfile(f'logs/{ts}.create-exam'):
        with open(f'logs/{ts}.create-exam') as f: exam_id = f.read().strip()
        placements_ts_file = f'logs/{ts}.placements_exam'
        if os.path.isfile(placements_ts_file):
            with open(placements_ts_file) as f: last_msg_ts = f.read().strip()
            if last_msg_ts:
                try:
                    client[0].chat_delete(channel=event['item']['channel'], ts=last_msg_ts)
                except Exception as e:
                    print(f"Failed to delete previous placements message: {e}", file=sys.stderr, flush=True)

        responses = json_intra_api('GET', f"/exams/{exam_id}/exams_users")
        exam_ip = responses[0]['exam']['ip_range']
        participants_info = []

        for response in responses:
            participant = response['user']['login']
            participants_exam = get_next_exam(participant)
            participants_info.append((participant, participants_exam))

        cluster = get_cluster(exam_ip)
        sit_per_row = 14
        if cluster == 'k1':
            sit_per_row = 16
        elif cluster == 'k2':
            sit_per_row = 10


        placements = calculate_placements(participants_info, sit_per_row)

        if placements:
            placements_sorted = sorted(placements, key=lambda x: x[0])
            col1_width = max(len(login) for login, _, _ in placements_sorted) + 2
            col2_width = max(len(place) for _, place, _ in placements_sorted) + 2
            col3_width = 6

            sep = f"+{'-' * col1_width}+{'-' * col2_width}+{'-' * col3_width}+"
            header = f"| Login{' ' * (col1_width - 6)}| Place{' ' * (col2_width - 6)}| Exam |"

            msg = "Placements dans l'exam :\n```\n"
            msg += sep + "\n"
            msg += header + "\n"
            msg += sep + "\n"

            for login, place, exam in placements_sorted:
                msg += f"|{login.ljust(col1_width)}|{place.ljust(col2_width)}|({exam})  |\n"

            msg += sep + "\n```"
        else:
            msg = "Aucun placement à afficher"

        resp = client[0].chat_postMessage(channel=event['item']['channel'], thread_ts=ts, text=msg)
        with open(placements_ts_file, 'w') as f: f.write(resp['ts'])