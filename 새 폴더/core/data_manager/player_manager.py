from core import storage


def clean_riot_id(value):
    if value is None:
        return ""

    value = str(value).strip()

    if value == "":
        return ""

    if value.lower() == "none":
        return ""

    if value.lower() == "null":
        return ""

    return value


def get_display_name(riot_id):
    riot_id = clean_riot_id(riot_id)

    if riot_id:
        return riot_id

    return "플레이어"


def get_current_match(valorant_players, valorant_match_id):
    if not valorant_players:
        return storage.get_match(valorant_match_id) or {
            "players": []
        }

    live_players = []

    for p in valorant_players:
        subject = p.get("subject") or p.get("puuid", "")
        riot_id = clean_riot_id(p.get("riot_id"))
        agent = p.get("agent", "Unknown")
        team = p.get("team", "")

        display_name = get_display_name(riot_id)

        live_players.append({
            "subject": subject,
            "riot_id": riot_id,
            "display_name": display_name,
            "agent": agent,
            "team": team
        })

        storage.save_player_match(
            subject=subject,
            riot_id=riot_id,
            match_id=valorant_match_id,
            agent=agent,
            team=team
        )

    return storage.save_match(
        match_id=valorant_match_id,
        players=live_players
    )


def build_all_info_rows():
    players = storage.load_players()
    rows = []

    for subject, player in players.items():
        riot_id = clean_riot_id(player.get("riot_id"))
        records = player.get("records", {})

        throw_total = 0
        block_total = 0
        flame_total = 0
        like_total = 0
        dislike_total = 0
        latest_memo = ""
        latest_date = ""
        latest_agent = ""

        for match_id, data in records.items():
            throw_total += data.get("throw_count", 0)
            block_total += data.get("block_count", 0)
            flame_total += data.get("flame_count", 0)
            like_total += data.get("like_count", 0)
            dislike_total += data.get("dislike_count", 0)

            meet_date = data.get("meet_date", "")
            memo = data.get("memo", "")
            agent = data.get("agent", "")

            if meet_date > latest_date:
                latest_date = meet_date
                latest_memo = memo
                latest_agent = agent

        rows.append({
            "subject": subject,
            "riot_id": riot_id,
            "display_name": get_display_name(riot_id),
            "meet_count": len(records),
            "throw_count": throw_total,
            "block_count": block_total,
            "flame_count": flame_total,
            "like_count": like_total,
            "dislike_count": dislike_total,
            "memo": latest_memo,
            "date": latest_date,
            "latest_agent": latest_agent
        })

    rows.sort(
        key=lambda x: x["date"],
        reverse=True
    )

    return rows


def build_realtime_info_rows(valorant_players, valorant_match_id):
    match = get_current_match(
        valorant_players,
        valorant_match_id
    )

    players_data = storage.load_players()
    rows = []

    match_players = match.get("players", [])

    # 예전 데이터가 dict여도 안 터지게 호환
    if isinstance(match_players, dict):
        iterable_players = []

        for subject, info in match_players.items():
            if isinstance(info, dict):
                info["subject"] = subject
                iterable_players.append(info)
            else:
                iterable_players.append({
                    "subject": subject
                })
    else:
        iterable_players = match_players

    for info in iterable_players:
        if isinstance(info, dict):
            subject = info.get("subject") or info.get("puuid", "")
            riot_id = clean_riot_id(info.get("riot_id"))
            agent_now = info.get("agent", "Unknown")
            team_now = info.get("team", "")
        else:
            subject = str(info)
            riot_id = ""
            agent_now = "Unknown"
            team_now = ""

        player_saved = players_data.get(subject, {})
        records = player_saved.get("records", {})

        throw_total = 0
        block_total = 0
        flame_total = 0
        like_total = 0
        dislike_total = 0

        latest_old_date = ""
        latest_old_agent = ""

        memos = []
        game_count = 0

        for record_match_id, data in records.items():
            game_count += 1

            throw_total += data.get("throw_count", 0)
            block_total += data.get("block_count", 0)
            flame_total += data.get("flame_count", 0)
            like_total += data.get("like_count", 0)
            dislike_total += data.get("dislike_count", 0)

            meet_date = data.get("meet_date", "")
            agent = data.get("agent", "")

            if record_match_id != valorant_match_id:
                if meet_date > latest_old_date:
                    latest_old_date = meet_date
                    latest_old_agent = agent

            memo = data.get("memo", "")

            if memo:
                memos.append(memo)

        rows.append({
            "subject": subject,
            "riot_id": riot_id,
            "display_name": get_display_name(riot_id),
            "current_agent": agent_now,
            "last_agent": latest_old_agent,
            "team": team_now,
            "throw_total": throw_total,
            "block_total": block_total,
            "flame_total": flame_total,
            "like_total": like_total,
            "dislike_total": dislike_total,
            "meet_count": game_count,
            "meet_dates": [latest_old_date] if latest_old_date else [],
            "memos": memos
        })

    return rows