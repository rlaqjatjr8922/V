import json
from pathlib import Path

from config import LONG_RECORD_DIR


def get_mark_file(match_id):
    folder = Path(LONG_RECORD_DIR)
    folder.mkdir(parents=True, exist_ok=True)

    safe_match_id = str(match_id).replace("/", "_").replace("\\", "_")

    return folder / f"{safe_match_id}.json"


def load_marks(match_id):
    path = get_mark_file(match_id)

    if not path.exists():
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            return data

        return []

    except json.JSONDecodeError:
        return []


def save_marks(match_id, marks):
    path = get_mark_file(match_id)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            marks,
            f,
            ensure_ascii=False,
            indent=4
        )

    return marks


def add_mark(match_id, timecode):
    marks = load_marks(match_id)

    mark = {
        "time": str(timecode)
    }

    marks.append(mark)

    save_marks(match_id, marks)

    return mark


def delete_mark(match_id, index):
    marks = load_marks(match_id)

    index = int(index)

    if 0 <= index < len(marks):
        deleted = marks.pop(index)
        save_marks(match_id, marks)
        return deleted

    return None


def clear_marks(match_id):
    save_marks(match_id, [])
    return []


def load_marks_for_view(match_id):
    marks = load_marks(match_id)

    rows = []

    for idx, mark in enumerate(marks):
        rows.append({
            "index": idx,
            "time": str(mark.get("time", "00:00:00.000"))
        })

    rows.reverse()

    return rows