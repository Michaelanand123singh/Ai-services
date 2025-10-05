"""
Minimal AI service smoke test

Checks:
- /health
- /ai/providers/test (gemini with model from env)

Env used: AI_SERVICE_URL, AI_SERVICE_API_KEY, GEMINI_MODEL

Usage:
  python scripts/smoke_ai.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv


def get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    val = os.getenv(name)
    return val if val is not None else default


def main() -> int:
    # Load .env from AI-services directory if present
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(dotenv_path=str(env_path), override=False)

    base_url = get_env("AI_SERVICE_URL", "http://localhost:8001")
    api_key = get_env("AI_SERVICE_API_KEY", "")
    gemini_model = get_env("GEMINI_MODEL", "gemini-pro")

    headers = {"x-api-key": api_key} if api_key else {}

    ok_all = True

    # Health
    try:
        r = requests.get(f"{base_url}/health/", timeout=15)
        print(f"/health -> {r.status_code} {r.text[:200]}")
        ok_all &= r.ok
    except Exception as e:
        print(f"/health -> ERROR {e}")
        ok_all = False

    # Providers status
    try:
        r = requests.get(f"{base_url}/ai/providers/status", headers=headers, timeout=20)
        print(f"/ai/providers/status -> {r.status_code} {r.text[:200]}")
        ok_all &= r.ok
    except Exception as e:
        print(f"/ai/providers/status -> ERROR {e}")
        ok_all = False

    # Providers models (should include live_gemini_models)
    try:
        r = requests.get(f"{base_url}/ai/providers/models", headers=headers, timeout=20)
        print(f"/ai/providers/models -> {r.status_code} {r.text[:200]}")
        ok_all &= r.ok
    except Exception as e:
        print(f"/ai/providers/models -> ERROR {e}")
        ok_all = False

    # Provider test (gemini)
    try:
        payload = {"provider": "gemini", "model": gemini_model, "test_prompt": "Say hello"}
        r = requests.post(f"{base_url}/ai/providers/test", json=payload, headers=headers, timeout=30)
        print(f"/ai/providers/test (model={gemini_model}) -> {r.status_code} {r.text[:200]}")
        ok_all &= r.ok
    except Exception as e:
        print(f"/ai/providers/test -> ERROR {e}")
        ok_all = False

    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())


