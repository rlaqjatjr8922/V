import json
import os
from datetime import datetime


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(BASE_DIR, "data")
PLAYERS_FILE = os.path.join(DATA_DIR, "players.json")
MATCHES_FILE = os.path.join(DATA_DIR, "matches.json")


def now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ensure_parent(path):
    parent = os.path.dirname(path)

    if parent:
        os.makedirs(parent, exist_ok=True)


def save_json(path, data):
    ensure_parent(path)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=4
        )


def load_json(path):
    ensure_parent(path)

    if not os.path.exists(path):
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            return data

        return {}

    except json.JSONDecodeError:
        return {}


def ensure_data_files():
    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(PLAYERS_FILE):
        save_json(PLAYERS_FILE, {})

    if not os.path.exists(MATCHES_FILE):
        save_json(MATCHES_FILE, {})


def load_players():
    ensure_data_files()
    return load_json(PLAYERS_FILE)


def save_players(players):
    save_json(PLAYERS_FILE, players)


def load_matches():
    ensure_data_files()
    return load_json(MATCHES_FILE)


def save_matches(matches):
    save_json(MATCHES_FILE, matches)


def commit(players, matches):
    save_players(players)
    save_matches(matches)


def is_real_riot_id(riot_id):
    return bool(riot_id)


def get_player_match(players, subject, riot_id, match_id):
    if not subject:
        subject = "unknown"

    if subject not in players:
        players[subject] = {
            "riot_id": riot_id or "",
            "records": {}
        }

    if is_real_riot_id(riot_id):
        players[subject]["riot_id"] = riot_id
    else:
        players[subject].setdefault("riot_id", "")

    players[subject].setdefault("records", {})

    records = players[subject]["records"]

    if match_id not in records:
        records[match_id] = {
            "throw_count": 0,
            "block_count": 0,
            "flame_count": 0,
            "like_count": 0,
            "dislike_count": 0,
            "agent": "",
            "kills": 0,
            "deaths": 0,
            "assists": 0,
            "memo": "",
            "team": ""
        }

    return records[match_id]


def ensure_match(matches, match_id):
    if match_id not in matches:
        matches[match_id] = {
            "map": "",
            "game_mode": "",
            "date": now_text(),
            "game_duration": "",
            "blue_score": 0,
            "red_score": 0,
            "win": "",
            "players": []
        }

    matches[match_id].setdefault("map", "")
    matches[match_id].setdefault("game_mode", "")
    matches[match_id].setdefault("date", now_text())
    matches[match_id].setdefault("game_duration", "")
    matches[match_id].setdefault("blue_score", 0)
    matches[match_id].setdefault("red_score", 0)
    matches[match_id].setdefault("win", "")
    matches[match_id].setdefault("players", [])

    return matches[match_id]


def toggle_player_event(subject, riot_id, match_id, event_name):
    allowed = {
        "throw": "throw_count",
        "block": "block_count",
        "flame": "flame_count",
        "like": "like_count",
        "dislike": "dislike_count"
    }

    if event_name not in allowed:
        raise ValueError(f"알 수 없는 이벤트: {event_name}")

    players = load_players()
    matches = load_matches()

    player_match = get_player_match(
        players,
        subject,
        riot_id,
        match_id
    )

    key = allowed[event_name]

    if player_match.get(key, 0) == 0:
        player_match[key] = 1
    else:
        player_match[key] = 0

    commit(players, matches)

    return player_match


def increment_player_event(subject, riot_id, match_id, event_name):
    return toggle_player_event(
        subject=subject,
        riot_id=riot_id,
        match_id=match_id,
        event_name=event_name
    )


def update_player_memo(subject, riot_id, match_id, memo):
    players = load_players()
    matches = load_matches()

    player_match = get_player_match(
        players,
        subject,
        riot_id,
        match_id
    )

    player_match["memo"] = memo

    commit(players, matches)

    return player_match


def apply_player_match(
    players,
    matches,
    subject,
    riot_id,
    match_id,
    agent="",
    kills=None,
    deaths=None,
    assists=None,
    memo=None,
    team="",
    throw_count=None,
    block_count=None,
    flame_count=None,
    like_count=None,
    dislike_count=None
):
    player_match = get_player_match(
        players,
        subject,
        riot_id,
        match_id
    )

    if agent:
        player_match["agent"] = agent

    if team:
        player_match["team"] = team

    if memo is not None:
        player_match["memo"] = memo

    if kills is not None:
        player_match["kills"] = int(kills)

    if deaths is not None:
        player_match["deaths"] = int(deaths)

    if assists is not None:
        player_match["assists"] = int(assists)

    if throw_count is not None:
        player_match["throw_count"] = int(throw_count)

    if block_count is not None:
        player_match["block_count"] = int(block_count)

    if flame_count is not None:
        player_match["flame_count"] = int(flame_count)

    if like_count is not None:
        player_match["like_count"] = int(like_count)

    if dislike_count is not None:
        player_match["dislike_count"] = int(dislike_count)

    return player_match


def save_player_match(
    subject,
    riot_id,
    match_id,
    agent="",
    kills=None,
    deaths=None,
    assists=None,
    memo=None,
    team="",
    throw_count=None,
    block_count=None,
    flame_count=None,
    like_count=None,
    dislike_count=None
):
    players = load_players()
    matches = load_matches()

    player_match = apply_player_match(
        players=players,
        matches=matches,
        subject=subject,
        riot_id=riot_id,
        match_id=match_id,
        agent=agent,
        kills=kills,
        deaths=deaths,
        assists=assists,
        memo=memo,
        team=team,
        throw_count=throw_count,
        block_count=block_count,
        flame_count=flame_count,
        like_count=like_count,
        dislike_count=dislike_count
    )

    commit(players, matches)

    return player_match


def save_match(
    match_id,
    map="",
    game_mode="",
    date=None,
    game_duration="",
    blue_score=0,
    red_score=0,
    win="",
    players=None
):
    matches = load_matches()

    match = ensure_match(matches, match_id)

    if map is not None:
        match["map"] = map

    if game_mode is not None:
        match["game_mode"] = game_mode

    if date is not None:
        match["date"] = date

    if game_duration is not None:
        match["game_duration"] = game_duration

    if blue_score is not None:
        match["blue_score"] = blue_score

    if red_score is not None:
        match["red_score"] = red_score

    if win is not None:
        match["win"] = win

    if players is not None:
        match["players"] = players

    save_matches(matches)

    return match


def get_match(match_id):
    matches = load_matches()
    return matches.get(match_id)


def get_all_matches():
    return load_matches()


def get_all_player_records(subject):
    players = load_players()
    player = players.get(subject, {})

    return player.get("records", {})


def reset_all_data():
    save_players({})
    save_matches({})


def update_match(match_id, data):
    matches = load_matches()

    if match_id not in matches:
        return None

    matches[match_id].update(data)
    save_matches(matches)

    return matches[match_id]


def delete_match(match_id):
    matches = load_matches()

    if match_id in matches:
        del matches[match_id]
        save_matches(matches)
        return True

    return False