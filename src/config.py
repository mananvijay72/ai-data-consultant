"""
Loads config.yaml once and exposes it as a simple dict-like object.
Also loads .env for GEMINI_API_KEY.
"""
import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent.parent


def load_config() -> dict:
    config_path = ROOT_DIR / "config.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


CONFIG = load_config()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

if not GEMINI_API_KEY:
    # Not raising here — some modules (pure KPI engine, chunker tests) don't
    # need a key. Anything that calls Gemini will raise a clear error later.
    pass
