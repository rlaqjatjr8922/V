import os
import time
import subprocess
from pathlib import Path

from obsws_python import ReqClient

from config import (
    OBS_HOST,
    OBS_PORT,
    OBS_PASSWORD,
    OBS_EXE,
    SHORT_RECORD_DIR,
    LONG_RECORD_DIR
)


def is_obs_running():
    try:
        import psutil

        for proc in psutil.process_iter(["name"]):
            name = proc.info.get("name", "")

            if name and "obs64" in name.lower():
                return True

    except Exception as e:
        print("[OBS CHECK ERROR]", e)

    return False


def start_obs():
    try:
        if not os.path.exists(OBS_EXE):
            print("[OBS OPEN ERROR] OBS 실행 파일 없음:", OBS_EXE)
            return False

        obs_dir = os.path.dirname(OBS_EXE)

        subprocess.Popen(
            [OBS_EXE, "--minimize-to-tray"],
            cwd=obs_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        time.sleep(6)
        return True

    except Exception as e:
        print("[OBS OPEN ERROR]", e)
        return False


def get_obs():
    return ReqClient(
        host=OBS_HOST,
        port=OBS_PORT,
        password=OBS_PASSWORD
    )


def connect_obs():
    try:
        return get_obs()

    except Exception as e:
        if is_obs_running():
            raise Exception(
                f"OBS는 실행중인데 WebSocket 연결 실패: {e}"
            )

        print("[OBS] 꺼져있음 → 자동 실행")

        if not start_obs():
            raise Exception("OBS 실행 실패")

        return get_obs()


def start_record():
    try:
        obs = connect_obs()
        status = obs.get_record_status()

        if not status.output_active:
            obs.start_record()

        return True

    except Exception as e:
        print("[OBS START ERROR]", e)
        return False


def stop_record():
    try:
        obs = connect_obs()
        status = obs.get_record_status()

        if status.output_active:
            obs.stop_record()

        return True

    except Exception as e:
        print("[OBS STOP ERROR]", e)
        return False


def get_record_status():
    try:
        obs = connect_obs()
        status = obs.get_record_status()

        return {
            "ok": True,
            "active": status.output_active,
            "paused": status.output_paused,
            "timecode": status.output_timecode
        }

    except Exception as e:
        print("[OBS STATUS ERROR]", e)

        return {
            "ok": False,
            "active": False,
            "paused": False,
            "timecode": ""
        }


def get_short_record_files():
    return get_record_files(SHORT_RECORD_DIR)


def get_long_record_files():
    return get_record_files(LONG_RECORD_DIR)


def get_record_files(folder_path):
    folder = Path(folder_path)
    folder.mkdir(parents=True, exist_ok=True)

    files = []

    for f in folder.iterdir():
        if f.is_file():
            files.append({
                "name": f.name,
                "path": str(f),
                "size_mb": round(f.stat().st_size / 1024 / 1024, 1),
                "mtime": f.stat().st_mtime
            })

    files.sort(
        key=lambda x: x["mtime"],
        reverse=True
    )

    return files