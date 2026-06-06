import threading
import time
import uuid

from core import storage
from core.valorant_local_api import (
    get_game_state,
    get_players
)
from core.obs_controller import (
    start_record,
    stop_record,
    get_record_status
)
from core.valorant_match_result import (
    get_match_result,
    make_readable_result
)
from core.record_file_manager import move_latest_record


DEFAULT_MATCH_ID = "VALORANT_LIVE"


def is_real_match_id(match_id):
    if not match_id:
        return False

    if match_id == DEFAULT_MATCH_ID:
        return False

    try:
        uuid.UUID(match_id)
        return True
    except ValueError:
        return False


class ValorantManager:
    def __init__(self):
        self.valorant_state = "메인 메뉴"
        self.last_state = "메인 메뉴"

        self.valorant_players = []
        self.valorant_match_id = DEFAULT_MATCH_ID

        self.recording_auto = False
        self.thread = None

        self.alert_message = ""

    def fix_player_riot_ids(self, players):
        players_db = storage.load_players()

        for p in players:
            if not p.get("riot_id"):
                subject = p.get("subject")
                saved = players_db.get(subject, {})
                saved_riot_id = saved.get("riot_id")

                if saved_riot_id:
                    p["riot_id"] = saved_riot_id
                else:
                    p["riot_id"] = ""

        return players

    def sync_players_once(self):
        data = get_players()

        print("[RAW PLAYERS]", data)

        if not data:
            self.valorant_players = []
            print("[SYNC FAIL] 플레이어 데이터 없음")
            return False

        match_id = next(iter(data))
        players = data[match_id]

        players = self.fix_player_riot_ids(players)

        self.valorant_match_id = match_id
        self.valorant_players = players

        print("[PLAYERS SYNC]", self.valorant_match_id, len(players))
        print("[SYNC OK]", self.valorant_match_id, players)

        return True

    def save_match_result(self, match_id, game_duration="00:00:00.00"):
        if not is_real_match_id(match_id):
            self.alert_message = f"저장 안함: 가짜 match_id ({match_id})"
            print("[MATCH RESULT]", self.alert_message)
            return False
    
        for try_count in range(1, 4):
            print("[MATCH RESULT] API 호출", try_count, "/ 3")
    
            raw_result = get_match_result(match_id)
    
            if raw_result and raw_result.get("ok"):
                result = make_readable_result(raw_result)
    
                players_data = storage.load_players()
                matches_data = storage.load_matches()
    
                match = storage.ensure_match(matches_data, match_id)
    
                match_map = result.get("map", "")
                match_game_mode = result.get("game_mode", "")
                match_blue_score = result.get("blue_score", None)
                match_red_score = result.get("red_score", None)
                match_win = result.get("win", "")
    
                missing_fields = []
    
                if not match_map:
                    missing_fields.append("map")
    
                if not match_game_mode:
                    missing_fields.append("game_mode")
    
                if match_blue_score is None:
                    missing_fields.append("blue_score")
    
                if match_red_score is None:
                    missing_fields.append("red_score")
    
                if not match_win:
                    missing_fields.append("win")
    
                if missing_fields:
                    print(
                        "[MATCH RESULT] 매치 값 못 받음:",
                        ", ".join(missing_fields)
                    )
    
                match["map"] = match_map
                match["game_mode"] = match_game_mode
                match["game_duration"] = game_duration
                match["blue_score"] = (
                    match_blue_score
                    if match_blue_score is not None
                    else 0
                )
                match["red_score"] = (
                    match_red_score
                    if match_red_score is not None
                    else 0
                )
                match["win"] = match_win
                match["status"] = "FINISHED"
    
                match["players"] = [
                    p.get("subject", "")
                    for p in result.get("players", [])
                    if p.get("subject")
                ]
    
                for p in result.get("players", []):
                    storage.apply_player_match(
                        players=players_data,
                        matches=matches_data,
                        subject=p.get("subject", ""),
                        riot_id=p.get("riot_id", ""),
                        match_id=match_id,
                        agent=p.get("agent", ""),
                        kills=p.get("kills", 0),
                        deaths=p.get("deaths", 0),
                        assists=p.get("assists", 0),
                        team=p.get("team", "")
                    )
    
                storage.commit(players_data, matches_data)
    
                print(
                    "[MATCH RESULT] 저장 완료:",
                    len(result.get("players", [])),
                    "맵:",
                    match.get("map"),
                    "모드:",
                    match.get("game_mode"),
                    "게임시간:",
                    game_duration,
                    "스코어:",
                    match.get("blue_score"),
                    ":",
                    match.get("red_score"),
                    "승리팀:",
                    match.get("win")
                )
    
                return True
    
            print(
                "[MATCH RESULT] 실패:",
                raw_result.get("error") if raw_result else "결과 없음"
            )
    
            time.sleep(2)
    
        print("[MATCH RESULT] 3번 실패 → 가져온 값 + 더미 데이터 저장")
    
        players_data = storage.load_players()
        matches_data = storage.load_matches()
    
        match = storage.ensure_match(matches_data, match_id)
    
        match["map"] = match.get("map", "")
        match["game_mode"] = match.get("game_mode", "")
        match["game_duration"] = game_duration
        match["blue_score"] = 0
        match["red_score"] = 0
        match["win"] = ""
        match["status"] = "DODGE"
    
        match["players"] = [
            p.get("subject", "")
            for p in self.valorant_players
            if p.get("subject")
        ]
    
        for p in self.valorant_players:
            storage.apply_player_match(
                players=players_data,
                matches=matches_data,
                subject=p.get("subject", ""),
                riot_id=p.get("riot_id", ""),
                match_id=match_id,
                agent=p.get("agent", ""),
                kills=0,
                deaths=0,
                assists=0,
                team=p.get("team", "")
            )
    
        storage.commit(players_data, matches_data)
    
        print(
            "[DODGE SAVE] 저장 완료:",
            match_id,
            "플레이어:",
            len(match["players"]),
            "게임시간:",
            game_duration
        )
    
        return True

    def finish_recording(self, match_id):
        record_status = get_record_status()

        game_duration = record_status.get(
            "timecode",
            "00:00:00.00"
        )

        ok = stop_record()

        if not ok:
            print("[REC] 녹화 종료 실패")
            return False

        print("[REC] 녹화 종료 완료")
        print("[REC] 게임 시간:", game_duration)

        time.sleep(1)

        try:
            self.save_match_result(
                match_id,
                game_duration=game_duration
            )
        except Exception as e:
            print("[MATCH RESULT ERROR]", e)

        try:
            moved = move_latest_record(match_id)
            print("[RECORD MOVE]", moved)
        except Exception as e:
            print("[RECORD MOVE ERROR]", e)

        return True

    def handle_state_change(self, new_state):
        print("[STATE CHANGE]", self.last_state, "->", new_state)

        if new_state in ["요원 선택중", "게임 진행중"]:
            time.sleep(1)

            self.sync_players_once()

            if not self.recording_auto:
                ok = start_record()

                if ok:
                    self.recording_auto = True
                    print("[REC] 게임 시작 감지 → 녹화 시작")

        elif (
            self.last_state in ["게임 진행중", "요원 선택중"]
            and
            new_state == "메인 메뉴"
        ):
            finished_match_id = self.valorant_match_id
            self.valorant_players = []

            print(
                "[MATCH END]",
                self.last_state,
                "->",
                new_state,
                finished_match_id
            )

            if self.recording_auto:
                if self.finish_recording(finished_match_id):
                    self.recording_auto = False
                    print("[REC] 게임 종료 감지 → 후처리 완료")

            self.valorant_match_id = DEFAULT_MATCH_ID

    def loop(self):
        while True:
            try:
                new_state = get_game_state()

                self.valorant_state = new_state

                if new_state != self.last_state:
                    self.handle_state_change(new_state)
                    self.last_state = new_state

            except Exception as e:
                print("[VALORANT ERROR]", e)

                if self.recording_auto:
                    try:
                        self.finish_recording(self.valorant_match_id)
                    except Exception as ee:
                        print("[REC FORCE STOP ERROR]", ee)

                    self.recording_auto = False

                self.valorant_state = "메인 메뉴"
                self.last_state = "메인 메뉴"
                self.valorant_players = []
                self.valorant_match_id = DEFAULT_MATCH_ID

            time.sleep(1)

    def start(self):
        self.thread = threading.Thread(
            target=self.loop,
            daemon=True
        )
        self.thread.start()

    def get_api_state(self):
        return {
            "state": self.valorant_state,
            "match_id": self.valorant_match_id,
            "players": self.valorant_players,
            "recording_auto": self.recording_auto,
            "alert_message": self.alert_message
        }