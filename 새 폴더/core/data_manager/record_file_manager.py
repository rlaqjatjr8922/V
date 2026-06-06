import shutil
import time
from pathlib import Path

from config import (
    SHORT_RECORD_DIR,
    LONG_RECORD_DIR,
    TEMP_RECORD_DIR
)


VIDEO_EXTENSIONS = [
    ".mp4",
    ".mkv",
    ".mov",
    ".flv"
]


MAX_SHORT_FILES = 30


def safe_name(name):
    return (
        str(name)
        .replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
        .replace("*", "_")
        .replace("?", "_")
        .replace('"', "_")
        .replace("<", "_")
        .replace(">", "_")
        .replace("|", "_")
    )


def ensure_record_dirs():
    Path(TEMP_RECORD_DIR).mkdir(parents=True, exist_ok=True)
    Path(SHORT_RECORD_DIR).mkdir(parents=True, exist_ok=True)
    Path(LONG_RECORD_DIR).mkdir(parents=True, exist_ok=True)


def get_latest_temp_video():
    ensure_record_dirs()

    temp_dir = Path(TEMP_RECORD_DIR)
    videos = []

    for file in temp_dir.iterdir():
        if file.is_file() and file.suffix.lower() in VIDEO_EXTENSIONS:
            videos.append(file)

    if not videos:
        return None

    videos.sort(
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )

    return videos[0]


def has_long_json(match_id):
    ensure_record_dirs()

    match_name = safe_name(match_id)
    json_path = Path(LONG_RECORD_DIR) / f"{match_name}.json"

    return json_path.exists()


def cleanup_temp_folder():
    temp_dir = Path(TEMP_RECORD_DIR)

    for file in temp_dir.iterdir():
        if file.is_file() and file.suffix.lower() in VIDEO_EXTENSIONS:
            try:
                file.unlink()
                print("[TEMP DELETE]", file.name)
            except PermissionError:
                print("[TEMP DELETE SKIP] 사용 중:", file.name)
            except Exception as e:
                print("[TEMP DELETE ERROR]", e)


def cleanup_short_folder():
    short_dir = Path(SHORT_RECORD_DIR)
    videos = []

    for file in short_dir.iterdir():
        if file.is_file() and file.suffix.lower() in VIDEO_EXTENSIONS:
            videos.append(file)

    videos.sort(
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )

    while len(videos) > MAX_SHORT_FILES:
        old_file = videos.pop()

        try:
            old_file.unlink()
            print("[SHORT DELETE]", old_file.name)
        except PermissionError:
            print("[SHORT DELETE SKIP] 사용 중:", old_file.name)
        except Exception as e:
            print("[SHORT DELETE ERROR]", e)


def move_file_with_retry(src, dst, retry_count=15, delay=1):
    for i in range(retry_count):
        try:
            shutil.move(
                str(src),
                str(dst)
            )

            return True

        except PermissionError:
            print(
                "[RECORD MOVE WAIT]",
                i + 1,
                "/",
                retry_count,
                "파일 사용 중:",
                src.name
            )

            time.sleep(delay)

    return False


def move_latest_record(match_id):
    ensure_record_dirs()

    video = get_latest_temp_video()

    if video is None:
        print("[RECORD FILE] temp 영상 없음")
        return {
            "ok": False,
            "error": "temp 영상 없음"
        }

    match_name = safe_name(match_id)
    target_ext = video.suffix.lower()

    if has_long_json(match_id):
        target_dir = Path(LONG_RECORD_DIR)
        target_type = "long"
    else:
        target_dir = Path(SHORT_RECORD_DIR)
        target_type = "short"

    target_path = target_dir / f"{match_name}{target_ext}"

    if target_path.exists():
        try:
            target_path.unlink()
        except PermissionError:
            print("[TARGET DELETE WAIT] 기존 파일 사용 중:", target_path.name)

            for i in range(10):
                try:
                    target_path.unlink()
                    break
                except PermissionError:
                    time.sleep(1)

    moved = move_file_with_retry(
        video,
        target_path
    )

    if not moved:
        return {
            "ok": False,
            "error": "파일 사용 중이라 이동 실패",
            "from": str(video),
            "to": str(target_path)
        }

    if target_type == "short":
        cleanup_short_folder()

    cleanup_temp_folder()

    return {
        "ok": True,
        "type": target_type,
        "from": str(video),
        "to": str(target_path),
        "file": target_path.name
    }


def get_record_files(folder_path):
    folder = Path(folder_path)
    folder.mkdir(parents=True, exist_ok=True)

    files = []

    for file in folder.iterdir():
        if file.is_file() and file.suffix.lower() in VIDEO_EXTENSIONS:
            files.append({
                "name": file.name,
                "path": str(file),
                "size_mb": round(file.stat().st_size / 1024 / 1024, 1),
                "mtime": file.stat().st_mtime
            })

    files.sort(
        key=lambda x: x["mtime"],
        reverse=True
    )

    return files


def get_short_files():
    return get_record_files(SHORT_RECORD_DIR)


def get_long_files():
    return get_record_files(LONG_RECORD_DIR)


def get_temp_files():
    return get_record_files(TEMP_RECORD_DIR)