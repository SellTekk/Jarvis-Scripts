"""Robuster Wrapper für ``crawler_handy.py``.

Ziel:
- Startet den Crawler als Subprozess.
- Bei Crash/unerwartetem Exit automatischer Neustart.
- Liest/schreibt eine Checkpoint-Datei, damit Fortschritt sichtbar bleibt.
- Stoppt erst, wenn alle Produkte verarbeitet wurden.

Hinweis:
Der eigentliche Resume-Mechanismus liegt bereits in ``crawler_handy.py``:
Das Script liest ``OUTPUT_FILE`` und überspringt SKUs mit vorhandenem Preis.
Dieser Wrapper überwacht nur den Lauf und startet neu, bis alle SKUs im Output stehen.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

# Dateien relativ zu diesem Script
BASE_DIR = Path(__file__).resolve().parent
CRAWLER_SCRIPT = BASE_DIR / "crawler_handy.py"
CHECKPOINT_FILE = BASE_DIR / "crawler_handy.checkpoint.json"

# Muss zu crawler_handy.py passen
INPUT_FILE = Path("F:/crawlerv5/RELEASE_handy_TB.xlsx")
OUTPUT_FILE = Path("F:/crawlerv5/RELEASE_handy_ergebnis.xlsx")

RESTART_DELAY_SECONDS = 8
MAX_RESTARTS = 200  # Sicherheitsgrenze


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def safe_load_checkpoint() -> dict[str, Any]:
    if not CHECKPOINT_FILE.exists():
        return {
            "created_at": now_iso(),
            "restart_count": 0,
            "last_processed": 0,
            "total_products": 0,
            "completed": False,
        }

    try:
        return json.loads(CHECKPOINT_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {
            "created_at": now_iso(),
            "restart_count": 0,
            "last_processed": 0,
            "total_products": 0,
            "completed": False,
            "warning": "Checkpoint war defekt und wurde zurückgesetzt",
        }


def save_checkpoint(data: dict[str, Any]) -> None:
    data["updated_at"] = now_iso()
    CHECKPOINT_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def get_total_products() -> int:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input-Datei fehlt: {INPUT_FILE}")
    return len(pd.read_excel(INPUT_FILE))


def get_processed_products() -> int:
    if not OUTPUT_FILE.exists():
        return 0

    try:
        result_df = pd.read_excel(OUTPUT_FILE)
    except Exception:
        return 0

    if "SKU" not in result_df.columns:
        return 0

    return int(result_df["SKU"].dropna().nunique())


def run_crawler_once() -> int:
    print(f"\n[{now_iso()}] Starte Crawler: {CRAWLER_SCRIPT}")
    process = subprocess.run([sys.executable, str(CRAWLER_SCRIPT)], check=False)
    print(f"[{now_iso()}] Crawler beendet mit Exit-Code: {process.returncode}")
    return process.returncode


def main() -> int:
    checkpoint = safe_load_checkpoint()
    total = get_total_products()
    checkpoint["total_products"] = total

    processed = get_processed_products()
    checkpoint["last_processed"] = processed
    checkpoint["remaining"] = max(total - processed, 0)

    print("=== crawler_handy Wrapper ===")
    print(f"Input:      {INPUT_FILE}")
    print(f"Output:     {OUTPUT_FILE}")
    print(f"Checkpoint: {CHECKPOINT_FILE}")
    print(f"Fortschritt: {processed}/{total}")

    if processed >= total > 0:
        checkpoint["completed"] = True
        checkpoint["last_exit_code"] = 0
        save_checkpoint(checkpoint)
        print("Alle Produkte bereits verarbeitet. Nichts zu tun.")
        return 0

    save_checkpoint(checkpoint)

    while checkpoint.get("restart_count", 0) < MAX_RESTARTS:
        exit_code = run_crawler_once()

        processed = get_processed_products()
        remaining = max(total - processed, 0)

        checkpoint["last_exit_code"] = exit_code
        checkpoint["last_processed"] = processed
        checkpoint["remaining"] = remaining

        if processed >= total > 0:
            checkpoint["completed"] = True
            save_checkpoint(checkpoint)
            print(f"Fertig: {processed}/{total} verarbeitet.")
            return 0

        checkpoint["restart_count"] = int(checkpoint.get("restart_count", 0)) + 1
        checkpoint["completed"] = False
        save_checkpoint(checkpoint)

        print(
            f"Noch nicht fertig ({processed}/{total}). "
            f"Neustart #{checkpoint['restart_count']} in {RESTART_DELAY_SECONDS}s..."
        )
        time.sleep(RESTART_DELAY_SECONDS)

    checkpoint["completed"] = False
    checkpoint["error"] = f"Maximale Neustarts erreicht ({MAX_RESTARTS})"
    save_checkpoint(checkpoint)
    print(checkpoint["error"])
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
