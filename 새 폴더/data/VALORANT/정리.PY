import json
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MATCHES_PATH = os.path.join(BASE_DIR, "matches.json")
PLAYERS_PATH = os.path.join(BASE_DIR, "players.json")


REQUIRED_MATCH_FIELDS = [
    "map",
    "game_mode",
    "date",
    "game_duration",
    "win",
]


def load_json(path):
    if not os.path.exists(path):
        print("[파일 없음]", path)
        return {}

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def clean_matches():
    matches = load_json(MATCHES_PATH)

    cleaned = {}
    deleted = 0

    for match_id, match in matches.items():
        if match_id == "VALORANT_LIVE":
            deleted += 1
            print("[MATCH 삭제 - LIVE]", match_id)
            continue

        remove = False

        for field in REQUIRED_MATCH_FIELDS:
            if not match.get(field):
                remove = True
                break

        if remove:
            deleted += 1
            print("[MATCH 삭제]", match_id)
            continue

        cleaned[match_id] = match

    save_json(MATCHES_PATH, cleaned)

    print()
    print("matches.json")
    print("남음 :", len(cleaned))
    print("삭제 :", deleted)

    return cleaned


def clean_players(valid_matches):
    players = load_json(PLAYERS_PATH)

    cleaned = {}
    deleted_players = 0
    deleted_records = 0

    valid_match_ids = set(valid_matches.keys())

    for subject, player in players.items():
        riot_id = player.get("riot_id", "")
        records = player.get("records", {})

        if riot_id == "":
            deleted_players += 1
            print("[PLAYER 삭제 - riot_id 없음]", subject)
            continue

        if not records:
            deleted_players += 1
            print("[PLAYER 삭제 - records 없음]", subject)
            continue

        cleaned_records = {}

        for match_id, record in records.items():
            if match_id not in valid_match_ids:
                deleted_records += 1
                print("[RECORD 삭제 - matches에 없음]", subject, match_id)
                continue

            cleaned_records[match_id] = record

        if not cleaned_records:
            deleted_players += 1
            print("[PLAYER 삭제 - 남은 records 없음]", subject)
            continue

        player["records"] = cleaned_records
        cleaned[subject] = player

    save_json(PLAYERS_PATH, cleaned)

    print()
    print("players.json")
    print("남음 :", len(cleaned))
    print("PLAYER 삭제 :", deleted_players)
    print("RECORD 삭제 :", deleted_records)


def main():
    print("데이터 정리 시작")
    print("기준 폴더:", BASE_DIR)
    print("matches:", MATCHES_PATH)
    print("players:", PLAYERS_PATH)
    print()

    valid_matches = clean_matches()
    print()
    clean_players(valid_matches)

    print()
    print("정리 완료")


if __name__ == "__main__":
    main()