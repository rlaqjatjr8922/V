from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


OBS_HOST = "localhost"
OBS_PORT = 4455
OBS_PASSWORD = "nfDjLYInAoyrH6a8"

OBS_EXE = r"C:\Program Files\obs-studio\bin\64bit\obs64.exe"


RECORDINGS_DIR = BASE_DIR / "recordings"

SHORT_RECORD_DIR = str(
    RECORDINGS_DIR / "short"
)

LONG_RECORD_DIR = str(
    RECORDINGS_DIR / "long"
)
TEMP_RECORD_DIR = str(
    RECORDINGS_DIR / "temp"
)