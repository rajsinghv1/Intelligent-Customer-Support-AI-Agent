
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]

load_dotenv(BASE_DIR / ".env")

APP_NAME = os.getenv(
    "APP_NAME",
    "Intelligent Customer Support AI Agent"
)

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY", ""
).strip()

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.5-flash-lite"
).strip()

_db_value = os.getenv(
    "DB_PATH",
    "data/customer_support.db"
)

_db_path = Path(_db_value)

DB_PATH = (
    _db_path
    if _db_path.is_absolute()
    else BASE_DIR / _db_path
)


def validate_config():
    if not GEMINI_API_KEY or GEMINI_API_KEY.startswith(
        "your_"
    ):
        raise ValueError(
            "GEMINI_API_KEY is missing. "
            "Add your API key to the .env file."
        )

    if not GEMINI_MODEL:
        raise ValueError(
            "GEMINI_MODEL cannot be empty."
        )
