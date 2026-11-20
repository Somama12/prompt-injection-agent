"""Time one synthetic summary request and report the provider's token usage."""
import json
import os
from pathlib import Path
import time

import requests
from dotenv import load_dotenv


def main():
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    key = os.getenv("MOONSHOT_API_KEY") or os.getenv("KIMI_API_KEY")
    if not key:
        raise SystemExit("Set MOONSHOT_API_KEY in the project's .env to run the timing check.")
    model = os.getenv("KIMI_MODEL") or "kimi-k3.1-pro"
    started = time.monotonic()
    response = requests.post(
        "https://api.moonshot.ai/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={
            "model": model,
            "messages": [{"role": "user", "content": "Summarize in one sentence: The campus library will open an hour earlier during final exams."}],
            "max_tokens": 512,
        },
        timeout=90,
        allow_redirects=False,
    )
    if response.status_code != 200:
        raise SystemExit(f"Kimi returned HTTP {response.status_code}.")
    data = response.json()
    choice = data["choices"][0]
    if not (choice["message"].get("content") or "").strip():
        raise SystemExit(f"No summary returned. Finish reason: {choice.get('finish_reason')}")
    print(json.dumps({"model": data.get("model", model),
                      "elapsed_seconds": round(time.monotonic() - started, 2),
                      "usage": data.get("usage")}, indent=2))


if __name__ == "__main__":
    main()
