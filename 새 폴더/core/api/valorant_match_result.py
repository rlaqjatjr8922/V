import sys
import os

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from core.valorant_local_api import (
    get_tokens,
    get_region_shard,
    riot_get,
    riot_put,
    load_agents
)

from core.kr import (
    MAP_NAMES,
    GAME_MODES,
    update_kr_data
)


update_kr_data()


def ko_map(value):
    if not value:
        print("[KR 없음 - MAP] 빈값")
        return ""

    value = str(value)
    result = MAP_NAMES.get(value)

    if result is None:
        print("[KR 없음 - MAP]", value)
        return value

    return result


def ko_mode(value):
    if not value:
        print("[KR 없음 - MODE] 빈값")
        return ""

    value = str(value)

    result = (
        GAME_MODES.get(value)
        or GAME_MODES.get(value.lower())
    )

    if result is None:
        print("[KR 없음 - MODE]", value)
        return value

    return result


def get_player_names(subjects, access_token, ent_token, shard):
    if not subjects:
        return {}

    url = f"https://pd.{shard}.a.pvp.net/name-service/v2/players"

    data = riot_put(
        url,
        access_token,
        ent_token,
        subjects
    )

    names = {}

    if not isinstance(data, list):
        print("[NAME SERVICE ERROR]", data)
        return names

    for p in data:
        subject = p.get("Subject")
        game_name = p.get("GameName")
        tag_line = p.get("TagLine")

        if subject and game_name and tag_line:
            names[subject] = f"{game_name}#{tag_line}"
        else:
            print("[NAME SERVICE 이름 없음]", p)

    return names


def get_match_result(match_id):
    access_token, ent_token, my_subject = get_tokens()

    if not access_token or not ent_token or not my_subject:
        return {
            "ok": False,
            "error": "토큰 없음",
            "players": [],
            "teams": []
        }

    _, shard, _ = get_region_shard()
    agents = load_agents()

    url = (
        f"https://pd.{shard}.a.pvp.net/"
        f"match-details/v1/matches/{match_id}"
    )

    data = riot_get(
        url,
        access_token,
        ent_token
    )

    if not data or "players" not in data:
        return {
            "ok": False,
            "error": "매치 결과 없음",
            "raw": data,
            "players": [],
            "teams": []
        }

    raw_players = data.get("players", [])

    subjects = [
        p.get("subject")
        for p in raw_players
        if p.get("subject")
    ]

    name_map = get_player_names(
        subjects,
        access_token,
        ent_token,
        shard
    )

    players = []

    for p in raw_players:
        subject = p.get("subject", "")
        game_name = p.get("gameName", "")
        tag_line = p.get("tagLine", "")
        team_id = p.get("teamId", "")
        character_id = p.get("characterId", "").lower()
        stats = p.get("stats", {})

        if game_name and tag_line:
            riot_id = f"{game_name}#{tag_line}"
        elif subject in name_map:
            riot_id = name_map[subject]
        else:
            riot_id = ""
            print(
                "[RIOT ID 없음]",
                "subject=", subject,
                "gameName=", game_name,
                "tagLine=", tag_line
            )

        agent_name = agents.get(character_id)

        if agent_name is None:
            if character_id:
                print("[KR 없음 - AGENT]", character_id)
            agent_name = "미선택"

        players.append({
            "subject": subject,
            "riot_id": riot_id,
            "team": team_id,
            "agent": agent_name,
            "kills": stats.get("kills", 0),
            "deaths": stats.get("deaths", 0),
            "assists": stats.get("assists", 0)
        })

    match_info = data.get("matchInfo", {})

    teams = []

    for team in data.get("teams", []):
        teams.append({
            "team": team.get("teamId", ""),
            "rounds_won": team.get("roundsWon", 0)
        })

    return {
        "ok": True,
        "match_id": match_id,
        "map_id": match_info.get("mapId", ""),
        "game_mode_id": match_info.get("queueID", ""),
        "players": players,
        "teams": teams
    }


def make_readable_result(result):
    if not result.get("ok"):
        return result

    blue_score = 0
    red_score = 0

    for team in result.get("teams", []):
        if team.get("team") == "Blue":
            blue_score = team.get("rounds_won", 0)
        elif team.get("team") == "Red":
            red_score = team.get("rounds_won", 0)

    win = ""

    if blue_score > red_score:
        win = "Blue"
    elif red_score > blue_score:
        win = "Red"

    map_id = result.get("map_id", "")
    game_mode_id = result.get("game_mode_id", "")

    map_name = ko_map(map_id)
    game_mode = ko_mode(game_mode_id)

    print("[MAP ID]", map_id)
    print("[MAP KR]", map_name)
    print("[MODE ID]", game_mode_id)
    print("[MODE KR]", game_mode)

    return {
        "ok": True,
        "match_id": result.get("match_id", ""),
        "map": map_name,
        "game_mode": game_mode,
        "blue_score": blue_score,
        "red_score": red_score,
        "win": win,
        "players": result.get("players", [])
    }


if __name__ == "__main__":
    test_match_id = "f8e159f9-b43c-4950-9f68-84ec7921c36f"

    raw_result = get_match_result(test_match_id)
    readable_result = make_readable_result(raw_result)

    print(readable_result)