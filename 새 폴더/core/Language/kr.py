import requests


GAME_MODES = {}

MAP_NAMES = {}

AGENT_NAMES_KR = {}


def update_kr_data():
    global MAP_NAMES, GAME_MODES, AGENT_NAMES_KR

    try:
        agents_data = requests.get(
            "https://valorant-api.com/v1/agents?isPlayableCharacter=true&language=ko-KR",
            timeout=10
        ).json()

        for agent in agents_data.get("data", []):
            name_kr = agent.get("displayName", "")
            uuid = agent.get("uuid", "").lower()

            names = agent.get("displayName", "")

            if name_kr:
                AGENT_NAMES_KR[name_kr] = name_kr

            if uuid and name_kr:
                AGENT_NAMES_KR[uuid] = name_kr

    except Exception as e:
        print("[KR LOAD FAIL - AGENTS]", e)

    try:
        agents_en_data = requests.get(
            "https://valorant-api.com/v1/agents?isPlayableCharacter=true",
            timeout=10
        ).json()

        for agent in agents_en_data.get("data", []):
            name_en = agent.get("displayName", "")
            uuid = agent.get("uuid", "").lower()

            name_kr = AGENT_NAMES_KR.get(uuid)

            if name_en and name_kr:
                AGENT_NAMES_KR[name_en] = name_kr
                AGENT_NAMES_KR[name_en.lower()] = name_kr

    except Exception as e:
        print("[KR LOAD FAIL - AGENTS EN]", e)

    try:
        maps_data = requests.get(
            "https://valorant-api.com/v1/maps?language=ko-KR",
            timeout=10
        ).json()

        for m in maps_data.get("data", []):
            map_url = m.get("mapUrl", "")
            name_kr = m.get("displayName", "")

            if map_url and name_kr:
                MAP_NAMES[map_url] = name_kr

    except Exception as e:
        print("[KR LOAD FAIL - MAPS]", e)

    try:
        maps_en_data = requests.get(
            "https://valorant-api.com/v1/maps",
            timeout=10
        ).json()

        for m in maps_en_data.get("data", []):
            name_en = m.get("displayName", "")
            map_url = m.get("mapUrl", "")

            name_kr = MAP_NAMES.get(map_url)

            if name_en and name_kr:
                MAP_NAMES[name_en] = name_kr
                MAP_NAMES[name_en.lower()] = name_kr

    except Exception as e:
        print("[KR LOAD FAIL - MAPS EN]", e)

    try:
        modes_data = requests.get(
            "https://valorant-api.com/v1/gamemodes?language=ko-KR",
            timeout=10
        ).json()

        for mode in modes_data.get("data", []):
            name_kr = mode.get("displayName", "")
            uuid = mode.get("uuid", "").lower()

            if uuid and name_kr:
                GAME_MODES[uuid] = name_kr

    except Exception as e:
        print("[KR LOAD FAIL - MODES]", e)

    try:
        modes_en_data = requests.get(
            "https://valorant-api.com/v1/gamemodes",
            timeout=10
        ).json()

        for mode in modes_en_data.get("data", []):
            name_en = mode.get("displayName", "")
            uuid = mode.get("uuid", "").lower()

            name_kr = GAME_MODES.get(uuid)

            if name_en and name_kr:
                GAME_MODES[name_en] = name_kr
                GAME_MODES[name_en.lower()] = name_kr

    except Exception as e:
        print("[KR LOAD FAIL - MODES EN]", e)

    GAME_MODES.update({
        "competitive": "경쟁전",
        "unrated": "일반전",
        "swiftplay": "신속플레이",
        "deathmatch": "데스매치",
        "spikerush": "스파이크 돌격",
        "replication": "복제",
        "escalation": "에스컬레이션",
        "premier": "프리미어",
        "custom": "사용자 설정",

        "ggteam": "에스컬레이션",
        "onefa": "복제",
        "hurm": "팀 데스매치",
        "snowball": "눈싸움",
        "newmap": "신규 맵",

        "skirmish": "난투",
        "skirmish1v1": "난투 1대1",
        "skirmishascension": "초월 난투",
        "skirmishascension1v1": "초월 난투 1대1",
    })

    print(
        "[KR LOAD]",
        "MAP_NAMES:", len(MAP_NAMES),
        "GAME_MODES:", len(GAME_MODES),
        "AGENT_NAMES_KR:", len(AGENT_NAMES_KR)
    )


def ko_map(value):
    if not value:
        return ""

    value = str(value)

    result = (
        MAP_NAMES.get(value)
        or MAP_NAMES.get(value.lower())
    )

    if result is None:
        print("[KR 없음 - MAP]", value)
        return value

    return result


def ko_mode(value):
    if not value:
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


def ko_agent(value):
    if not value:
        return "미선택"

    value = str(value)

    result = (
        AGENT_NAMES_KR.get(value)
        or AGENT_NAMES_KR.get(value.lower())
    )

    if result is None:
        print("[KR 없음 - AGENT]", value)
        return value

    return result


if __name__ == "__main__":
    update_kr_data()

    print("MAP_NAMES =")
    print(MAP_NAMES)

    print("\nGAME_MODES =")
    print(GAME_MODES)

    print("\nAGENT_NAMES_KR =")
    print(AGENT_NAMES_KR)