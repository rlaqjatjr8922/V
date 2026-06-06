import os
import base64
import requests
import urllib3

from core.kr import AGENT_NAMES_KR, update_kr_data

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

LOCKFILE = os.path.expandvars(
    r"%LocalAppData%\Riot Games\Riot Client\Config\lockfile"
)

CLIENT_PLATFORM = (
    "ew0KCSJwbGF0Zm9ybVR5cGUiOiAiUEMiLA0K"
    "CSJwbGF0Zm9ybU9TIjogIldpbmRvd3MiLA0K"
    "CSJwbGF0Zm9ybU9TVmVyc2lvbiI6ICIxMC4wLjE5MDQ1LjEiLA0K"
    "CSJwbGF0Zm9ybUNoaXBzZXQiOiAiVW5rbm93biINCn0="
)

AGENT_CACHE = None


def read_lockfile():
    with open(LOCKFILE, "r", encoding="utf-8") as f:
        name, pid, port, password, protocol = f.read().strip().split(":")
    return port, password, protocol


def local_get(path):
    port, password, protocol = read_lockfile()

    auth = base64.b64encode(
        f"riot:{password}".encode()
    ).decode()

    r = requests.get(
        f"{protocol}://127.0.0.1:{port}{path}",
        headers={"Authorization": f"Basic {auth}"},
        verify=False
    )

    try:
        return r.json()
    except Exception:
        return {}


def get_client_version():
    data = local_get("/product-session/v1/external-sessions")

    for _, session in data.items():
        if isinstance(session, dict):
            if session.get("productId") == "valorant":
                return session.get("version", "")

    return ""


def get_tokens():
    data = local_get("/entitlements/v1/token")

    return (
        data.get("accessToken"),
        data.get("token"),
        data.get("subject")
    )


def get_region_shard():
    session = local_get("/chat/v1/session")
    region = session.get("region", "kr1").lower()

    if region in ["kr", "kr1"]:
        return region, "kr", "kr-1"

    if region in ["ap", "ap1", "asia"]:
        return region, "ap", "ap-1"

    if region in ["na", "na1"]:
        return region, "na", "na-1"

    if region in ["eu", "eu1"]:
        return region, "eu", "eu-1"

    return region, "kr", "kr-1"


def riot_headers(access_token, ent_token):
    return {
        "Authorization": f"Bearer {access_token}",
        "X-Riot-Entitlements-JWT": ent_token,
        "X-Riot-ClientVersion": get_client_version(),
        "X-Riot-ClientPlatform": CLIENT_PLATFORM,
        "Content-Type": "application/json"
    }


def riot_get(url, access_token, ent_token):
    r = requests.get(
        url,
        headers=riot_headers(access_token, ent_token),
        verify=False
    )

    try:
        return r.json()
    except Exception:
        return {}


def riot_put(url, access_token, ent_token, body=None):
    r = requests.put(
        url,
        headers=riot_headers(access_token, ent_token),
        json=body,
        verify=False
    )

    try:
        return r.json()
    except Exception:
        return {}


def load_agents():
    global AGENT_CACHE

    if AGENT_CACHE is not None:
        return AGENT_CACHE

    try:
        update_kr_data()
    except Exception:
        pass

    try:
        data = requests.get(
            "https://valorant-api.com/v1/agents?isPlayableCharacter=true",
            timeout=10
        ).json()

        agents = {}

        for agent in data.get("data", []):
            uuid = agent.get("uuid", "").lower()
            name_en = agent.get("displayName", "")

            if not uuid:
                continue

            name_kr = AGENT_NAMES_KR.get(name_en)

            if not name_kr:
                print("[KR 없음 - AGENT]", name_en, uuid)
                name_kr = name_en

            agents[uuid] = name_kr

        AGENT_CACHE = agents
        return AGENT_CACHE

    except Exception as e:
        print("[AGENT LOAD ERROR]", e)
        return {}


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
        return names

    for p in data:
        subject = p.get("Subject")
        game_name = p.get("GameName")
        tag_line = p.get("TagLine")

        if subject and game_name and tag_line:
            names[subject] = f"{game_name}#{tag_line}"

    return names


def make_player_row(p, team, agents, name_map, state):
    subject = p.get("Subject")
    char_id = p.get("CharacterID", "").lower()
    riot_id = name_map.get(subject)

    agent_name = agents.get(char_id)

    if not agent_name:
        if char_id:
            print("[KR 없음 - CHARACTER ID]", char_id)
        agent_name = "미선택"

    if riot_id is None:
        riot_id = ""

    return {
        "team": team,
        "subject": subject,
        "riot_id": riot_id,
        "agent": agent_name,
        "state": state
    }


def get_game_state():
    access_token, ent_token, my_subject = get_tokens()

    if not access_token or not ent_token or not my_subject:
        return "메인 메뉴"

    _, shard, glz = get_region_shard()

    pregame = riot_get(
        f"https://glz-{glz}.{shard}.a.pvp.net/"
        f"pregame/v1/players/{my_subject}",
        access_token,
        ent_token
    )

    if "MatchID" in pregame:
        return "요원 선택중"

    core = riot_get(
        f"https://glz-{glz}.{shard}.a.pvp.net/"
        f"core-game/v1/players/{my_subject}",
        access_token,
        ent_token
    )

    if "MatchID" in core:
        return "게임 진행중"

    return "메인 메뉴"


def get_players():
    access_token, ent_token, my_subject = get_tokens()

    if not access_token or not ent_token or not my_subject:
        return {}

    _, shard, glz = get_region_shard()
    agents = load_agents()

    pregame = riot_get(
        f"https://glz-{glz}.{shard}.a.pvp.net/"
        f"pregame/v1/players/{my_subject}",
        access_token,
        ent_token
    )

    if "MatchID" in pregame:
        match_id = pregame["MatchID"]

        match = riot_get(
            f"https://glz-{glz}.{shard}.a.pvp.net/"
            f"pregame/v1/matches/{match_id}",
            access_token,
            ent_token
        )

        ally_team = match.get("AllyTeam", {})
        raw_players = ally_team.get("Players", [])

        subjects = [
            p.get("Subject")
            for p in raw_players
            if p.get("Subject")
        ]

        name_map = get_player_names(
            subjects,
            access_token,
            ent_token,
            shard
        )

        players = []

        for p in raw_players:
            players.append(
                make_player_row(
                    p=p,
                    team=ally_team.get("TeamID", "Blue"),
                    agents=agents,
                    name_map=name_map,
                    state=p.get("CharacterSelectionState", "unknown")
                )
            )

        return {
            match_id: players
        }

    core = riot_get(
        f"https://glz-{glz}.{shard}.a.pvp.net/"
        f"core-game/v1/players/{my_subject}",
        access_token,
        ent_token
    )

    if "MatchID" not in core:
        return {}

    match_id = core["MatchID"]

    match = riot_get(
        f"https://glz-{glz}.{shard}.a.pvp.net/"
        f"core-game/v1/matches/{match_id}",
        access_token,
        ent_token
    )

    raw_players = match.get("Players", [])

    subjects = [
        p.get("Subject")
        for p in raw_players
        if p.get("Subject")
    ]

    name_map = get_player_names(
        subjects,
        access_token,
        ent_token,
        shard
    )

    players = []

    for p in raw_players:
        players.append(
            make_player_row(
                p=p,
                team=p.get("TeamID", "Unknown"),
                agents=agents,
                name_map=name_map,
                state="in_game"
            )
        )

    return {
        match_id: players
    }


def get_match_id():
    data = get_players()

    if not data:
        return None

    return next(iter(data))


if __name__ == "__main__":
    print("상태:", get_game_state())
    print(get_players())