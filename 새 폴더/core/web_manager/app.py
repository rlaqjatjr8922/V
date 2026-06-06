import json
import os
import shutil
from pathlib import Path

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    jsonify,
    send_from_directory
)

from config import (
    SHORT_RECORD_DIR,
    LONG_RECORD_DIR
)

from core import storage
from core import record_marks

from core.obs_controller import get_record_status

from core.player_manager import (
    get_current_match,
    build_all_info_rows,
    build_realtime_info_rows
)

from core.valorant_manager import ValorantManager


app = Flask(__name__)

valorant = ValorantManager()

VIDEO_EXTENSIONS = [".mp4", ".mkv", ".mov", ".flv"]


def to_bool(value):
    if isinstance(value, bool):
        return value

    return str(value).lower() in [
        "true",
        "1",
        "on",
        "yes"
    ]


def clean_map_name(map_name):
    if not map_name:
        return "알 수 없음"

    return str(map_name).split("/")[-1]


def get_video_size_mb(path):
    return round(os.path.getsize(path) / 1024 / 1024, 1)


def load_record_mark_json(match_id):
    path = Path(LONG_RECORD_DIR) / f"{match_id}.json"

    if not path.exists():
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            return data

        return []

    except:
        return []


def save_record_mark_json(match_id, marks):
    Path(LONG_RECORD_DIR).mkdir(parents=True, exist_ok=True)

    path = Path(LONG_RECORD_DIR) / f"{match_id}.json"

    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            marks,
            f,
            ensure_ascii=False,
            indent=4
        )

    return marks


def ensure_long_record(match_id, filename):
    short_video = Path(SHORT_RECORD_DIR) / filename
    long_video = Path(LONG_RECORD_DIR) / filename
    long_json = Path(LONG_RECORD_DIR) / f"{match_id}.json"

    Path(LONG_RECORD_DIR).mkdir(parents=True, exist_ok=True)

    if short_video.exists():
        if long_video.exists():
            long_video.unlink()

        shutil.move(
            str(short_video),
            str(long_video)
        )

    if not long_json.exists():
        with open(long_json, "w", encoding="utf-8") as f:
            json.dump(
                [],
                f,
                ensure_ascii=False,
                indent=4
            )


def build_record_rows(folder_path, record_type):
    matches = storage.load_matches()
    rows = []
    errors = []

    folder = Path(folder_path)
    folder.mkdir(parents=True, exist_ok=True)

    for file in folder.iterdir():
        if not file.is_file():
            continue

        if file.suffix.lower() not in VIDEO_EXTENSIONS:
            continue

        match_id = file.stem
        match = matches.get(match_id)

        if not match:
            errors.append(f"매치 정보 없음: {file.name}")
            continue

        mark_count = 0

        if record_type == "long":
            marks = load_record_mark_json(match_id)
            mark_count = len(marks)

        rows.append({
            "match_id": match_id,
            "filename": file.name,
            "record_type": record_type,
            "map": clean_map_name(match.get("map", "")),
            "date": match.get("date", ""),
            "game_duration": match.get("game_duration", ""),
            "score": f'{match.get("blue_score", 0)} : {match.get("red_score", 0)}',
            "win": match.get("win", ""),
            "size_mb": get_video_size_mb(file),
            "mark_count": mark_count
        })

    rows.sort(
        key=lambda x: x["date"],
        reverse=True
    )

    return rows, errors


def total_size_gb(rows):
    total = 0

    for row in rows:
        total += row.get("size_mb", 0)

    return round(total / 1024, 1)


@app.route("/")
def home():
    return redirect("/live")


@app.route("/live")
def live():
    match = get_current_match(
        valorant.valorant_players,
        valorant.valorant_match_id
    )

    players = storage.load_players()

    return render_template(
        "live.html",
        match_id=valorant.valorant_match_id,
        match=match,
        players=players,
        valorant_state=valorant.valorant_state
    )


@app.route("/valorant_state")
def valorant_state_api():
    return jsonify(
        valorant.get_api_state()
    )


@app.route("/all_info")
def all_info():
    rows = build_all_info_rows()

    return render_template(
        "all_info.html",
        rows=rows,
        valorant_state=valorant.valorant_state
    )


@app.route("/history")
def history():
    matches = storage.load_matches()

    rows = []

    for match_id, match in matches.items():
        rows.append({
            "match_id": match_id,
            "map": clean_map_name(match.get("map", "")),
            "game_mode": match.get("game_mode", ""),
            "date": match.get("date", ""),
            "game_duration": match.get("game_duration", ""),
            "blue_score": match.get("blue_score", 0),
            "red_score": match.get("red_score", 0)
        })

    rows.sort(
        key=lambda x: x["date"],
        reverse=True
    )

    return render_template(
        "history.html",
        rows=rows,
        valorant_state=valorant.valorant_state
    )

@app.route("/realtime_info")
def realtime_info():
    rows = build_realtime_info_rows(
        valorant.valorant_players,
        valorant.valorant_match_id
    )

    return render_template(
        "realtime_info.html",
        rows=rows,
        valorant_state=valorant.valorant_state
    )


@app.route("/click", methods=["POST"])
def click_event():
    match_id = request.form.get("match_id")
    subject = request.form.get("subject")
    riot_id = request.form.get("riot_id")

    if not match_id or not subject or not riot_id:
        return jsonify({
            "ok": False,
            "error": "값 부족"
        }), 400

    players = storage.load_players()
    matches = storage.load_matches()

    record = storage.get_player_match(
        players,
        subject,
        riot_id,
        match_id
    )

    record["throw_count"] = int(to_bool(request.form.get("throw_count")))
    record["block_count"] = int(to_bool(request.form.get("block_count")))
    record["flame_count"] = int(to_bool(request.form.get("flame_count")))
    record["like_count"] = int(to_bool(request.form.get("like_count")))
    record["dislike_count"] = int(to_bool(request.form.get("dislike_count")))

    storage.commit(
        players,
        matches
    )

    return jsonify({
        "ok": True
    })


@app.route("/memo", methods=["POST"])
def memo():
    subject = request.form.get("subject")
    riot_id = request.form.get("riot_id")
    match_id = request.form.get("match_id")
    memo_text = request.form.get("memo", "")

    if not subject or not riot_id or not match_id:
        return jsonify({
            "ok": False,
            "error": "값 부족"
        }), 400

    result = storage.update_player_memo(
        subject=subject,
        riot_id=riot_id,
        match_id=match_id,
        memo=memo_text
    )

    return jsonify({
        "ok": True,
        "data": result
    })


@app.route("/delete_player")
def delete_player():
    subject = request.args.get("subject")
    players = storage.load_players()

    if subject in players:
        del players[subject]
        storage.save_players(players)

    return redirect("/all_info")


@app.route("/record_file")
def record_file():
    obs_status = get_record_status()

    short_files, short_errors = build_record_rows(
        SHORT_RECORD_DIR,
        "short"
    )

    long_files, long_errors = build_record_rows(
        LONG_RECORD_DIR,
        "long"
    )

    errors = short_errors + long_errors

    short_total_gb = total_size_gb(short_files)
    long_total_gb = total_size_gb(long_files)

    return render_template(
        "record_file.html",
        valorant_state=valorant.valorant_state,
        obs_status=obs_status,
        short_files=short_files,
        long_files=long_files,
        errors=errors,
        total_count=len(short_files) + len(long_files),
        total_size_gb=round(short_total_gb + long_total_gb, 1),
        short_total_gb=short_total_gb,
        long_total_gb=long_total_gb
    )


@app.route("/record_file/play/<record_type>/<filename>")
def record_file_play(record_type, filename):
    if record_type == "long":
        folder = LONG_RECORD_DIR
    else:
        folder = SHORT_RECORD_DIR

    return send_from_directory(
        folder,
        filename
    )


@app.route("/record_file/delete", methods=["POST"])
def record_file_delete():
    match_id = request.form.get("match_id")
    record_type = request.form.get("record_type")
    filename = request.form.get("filename")

    if record_type == "long":
        folder = Path(LONG_RECORD_DIR)
    else:
        folder = Path(SHORT_RECORD_DIR)

    video_path = folder / filename
    json_path = folder / f"{match_id}.json"

    if video_path.exists():
        video_path.unlink()

    if json_path.exists():
        json_path.unlink()

    return redirect("/record_file")


@app.route("/record_file/edit/<record_type>/<filename>")
def record_file_edit(record_type, filename):
    match_id = Path(filename).stem

    if record_type == "short":
        ensure_long_record(
            match_id,
            filename
        )

    return redirect(f"/record_edit/{match_id}")


@app.route("/record_edit/<match_id>")
def record_edit_page(match_id):
    match = storage.get_match(match_id)

    if not match:
        return redirect("/record_file")

    video_name = f"{match_id}.mp4"
    video_path = Path(LONG_RECORD_DIR) / video_name

    if not video_path.exists():
        return redirect("/record_file")

    marks = load_record_mark_json(match_id)

    return render_template(
        "record_edit.html",
        match_id=match_id,
        match=match,
        map_name=clean_map_name(match.get("map", "")),
        marks=marks,
        video_name=video_name,
        valorant_state=valorant.valorant_state
    )


@app.route("/record_edit/add_mark", methods=["POST"])
def record_edit_add_mark():
    match_id = request.form.get("match_id")
    time_text = request.form.get("time")

    if not match_id or not time_text:
        return jsonify({
            "ok": False,
            "error": "값 부족"
        }), 400

    marks = load_record_mark_json(match_id)

    marks.append({
        "time": time_text
    })

    save_record_mark_json(
        match_id,
        marks
    )

    return jsonify({
        "ok": True,
        "marks": marks
    })


@app.route("/record_edit/delete_mark", methods=["POST"])
def record_edit_delete_mark():
    match_id = request.form.get("match_id")
    index = request.form.get("index")

    if not match_id or index is None:
        return jsonify({
            "ok": False,
            "error": "값 부족"
        }), 400

    marks = load_record_mark_json(match_id)

    try:
        index = int(index)
    except:
        return jsonify({
            "ok": False,
            "error": "index 오류"
        }), 400

    if 0 <= index < len(marks):
        marks.pop(index)

    save_record_mark_json(
        match_id,
        marks
    )

    return jsonify({
        "ok": True,
        "marks": marks
    })


@app.route("/record_edit/video/<filename>")
def record_edit_video(filename):
    return send_from_directory(
        LONG_RECORD_DIR,
        filename
    )


@app.route("/record_marks")
def record_marks_page():
    marks = record_marks.load_marks_for_view(
        valorant.valorant_match_id
    )

    return render_template(
        "record_marks.html",
        match_id=valorant.valorant_match_id,
        marks=marks,
        valorant_state=valorant.valorant_state
    )


@app.route("/add_record_mark", methods=["POST"])
def add_record_mark():
    match_id = request.form.get("match_id")

    if not match_id:
        return jsonify({
            "ok": False,
            "error": "값 부족"
        }), 400

    status = get_record_status()

    if not status.get("ok"):
        return jsonify({
            "ok": False,
            "error": "OBS 연결 실패"
        }), 400

    if not status.get("active"):
        return jsonify({
            "ok": False,
            "error": "녹화중 아님"
        }), 400

    timecode = status.get(
        "timecode",
        "00:00:00.000"
    )

    result = record_marks.add_mark(
        match_id,
        timecode
    )

    return jsonify({
        "ok": True,
        "data": result
    })


@app.route("/delete_record_mark", methods=["POST"])
def delete_record_mark():
    match_id = request.form.get("match_id")
    index = request.form.get("index")

    if not match_id or index is None:
        return jsonify({
            "ok": False,
            "error": "값 부족"
        }), 400

    deleted = record_marks.delete_mark(
        match_id,
        int(index)
    )

    return jsonify({
        "ok": True,
        "data": deleted
    })

@app.route("/match_detail/<match_id>")
def match_detail(match_id):
    matches = storage.load_matches()
    players = storage.load_players()

    match = matches.get(match_id)

    if not match:
        return redirect("/history")

    blue_players = []
    red_players = []

    for subject in match.get("players", []):
        player = players.get(subject, {})

        record = (
            player
            .get("records", {})
            .get(match_id, {})
        )

        row = {
            "riot_id": player.get("riot_id", subject),
            "agent": record.get("agent", ""),
            "kills": record.get("kills", 0),
            "deaths": record.get("deaths", 0),
            "assists": record.get("assists", 0)
        }

        team = record.get("team", "")

        if team == "Blue":
            blue_players.append(row)
        else:
            red_players.append(row)

    return render_template(
        "match_detail.html",
        match_id=match_id,
        match={
            "map": clean_map_name(match.get("map", "")),
            "game_mode": match.get("game_mode", ""),
            "date": match.get("date", ""),
            "game_duration": match.get("game_duration", ""),
            "blue_score": match.get("blue_score", 0),
            "red_score": match.get("red_score", 0),
            "win": match.get("win", "")
        },
        blue_players=blue_players,
        red_players=red_players,
        valorant_state=valorant.valorant_state
    )


@app.route("/player_detail/<subject>")
def player_detail(subject):
    players = storage.load_players()
    matches = storage.load_matches()

    player = players.get(subject)

    if not player:
        return redirect("/all_info")

    records = player.get("records", {})

    total_throw = 0
    total_block = 0
    total_flame = 0
    total_like = 0
    total_dislike = 0

    rows = []

    for match_id, record in records.items():
        match = matches.get(match_id, {})

        team = record.get("team", "")
        win_team = match.get("win", "")

        total_throw += int(record.get("throw_count", 0))
        total_block += int(record.get("block_count", 0))
        total_flame += int(record.get("flame_count", 0))
        total_like += int(record.get("like_count", 0))
        total_dislike += int(record.get("dislike_count", 0))

        rows.append({
            "match_id": match_id,

            # 여기부터 matches.json에서 가져옴
            "meet_date": match.get("date", ""),
            "map": match.get("map", ""),
            "game_mode": match.get("game_mode", ""),
            "blue_score": match.get("blue_score", 0),
            "red_score": match.get("red_score", 0),

            # 여기부터 players.json record에서 가져옴
            "agent": record.get("agent", ""),
            "team": team,
            "kills": record.get("kills", 0),
            "deaths": record.get("deaths", 0),
            "assists": record.get("assists", 0),
            "win": "승리" if team == win_team else "패배",
            "memo": record.get("memo", "")
        })

    rows.sort(
        key=lambda x: x["meet_date"],
        reverse=True
    )

    return render_template(
        "player_detail.html",
        subject=subject,
        player=player,
        rows=rows,
        total_throw=total_throw,
        total_block=total_block,
        total_flame=total_flame,
        total_like=total_like,
        total_dislike=total_dislike,
        valorant_state=valorant.valorant_state
    )


if __name__ == "__main__":
    storage.ensure_data_files()

    valorant.start()    

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
        use_reloader=False
    )