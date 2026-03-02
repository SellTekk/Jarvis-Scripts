#!/usr/bin/env python3
# Model Switch - Wechsle zwischen free, premium und auto Modellen
# Ersetzt ALLE openrouter/* Eintraege durch das Zielmodell

import json
import sys
import os
import subprocess
import shutil
from datetime import datetime

CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".openclaw", "openclaw.json")
BACKUP_PATH = os.path.join(os.path.expanduser("~"), ".openclaw", "openclaw.json.backup")

# Modell-Kennungen
FREE_MODEL = "openrouter/openrouter/free"
PREMIUM_MODEL = "openrouter/minimax/minimax-m2.5"
AUTO_MODEL = "openrouter/auto"

MODEL_MAP = {
    "free": FREE_MODEL,
    "premium": PREMIUM_MODEL,
    "auto": AUTO_MODEL,
}

LABEL_MAP = {
    FREE_MODEL: "Free",
    PREMIUM_MODEL: "Premium",
    AUTO_MODEL: "Auto",
}


def replace_all_openrouter_models(obj, target_model):
    """Rekursiv ALLE openrouter/* Werte in model/primary Keys ersetzen."""
    count = 0
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in ("model", "primary") and isinstance(value, str) and value.startswith("openrouter/") and value != target_model:
                obj[key] = target_model
                count += 1
            elif isinstance(value, (dict, list)):
                count += replace_all_openrouter_models(value, target_model)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if isinstance(item, (dict, list)):
                count += replace_all_openrouter_models(item, target_model)
    return count


def find_current_models(obj):
    """Zaehle alle openrouter/* Modelle in model/primary Keys."""
    found = {}
    def _scan(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key in ("model", "primary") and isinstance(value, str) and value.startswith("openrouter/"):
                    found[value] = found.get(value, 0) + 1
                elif isinstance(value, (dict, list)):
                    _scan(value)
        elif isinstance(node, list):
            for item in node:
                if isinstance(item, (dict, list)):
                    _scan(item)
    _scan(obj)
    return found


def restart_gateway():
    """Gateway neu starten - Windows-kompatibel."""
    candidates = [
        os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "nodejs", "openclaw.cmd"),
        shutil.which("openclaw") or "",
    ]
    for path in candidates:
        if path and os.path.exists(path):
            try:
                result = subprocess.run(
                    [path, "gateway", "restart"],
                    capture_output=True, text=True, timeout=20
                )
                if result.returncode == 0:
                    return "OK"
                else:
                    return f"FEHLER: {result.stderr.strip()}"
            except Exception as e:
                return f"FEHLER: {e}"
    return "openclaw nicht gefunden - manuell: openclaw gateway restart"


def main():
    if len(sys.argv) < 2:
        print("Usage: switch.py free|premium|auto|status")
        sys.exit(1)

    command = sys.argv[1].lower()

    if not os.path.exists(CONFIG_PATH):
        print(f"FEHLER: Config nicht gefunden: {CONFIG_PATH}")
        sys.exit(1)

    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # --- STATUS ---
    if command == "status":
        found = find_current_models(config)
        if not found:
            print("=== MODEL STATUS ===")
            print("Keine openrouter/* Modelle gefunden.")
            sys.exit(0)

        most_common = max(found, key=found.get)
        label = LABEL_MAP.get(most_common, most_common)
        print(f"=== MODEL STATUS ===")
        print(f"Aktuelles Modell: {label} ({most_common})")
        for m, c in found.items():
            print(f"  {m}: {c}x")
        sys.exit(0)

    # --- SWITCH ---
    if command not in MODEL_MAP:
        print(f"Unbekannter Befehl: {command}")
        print("Verfuegbar: free | premium | auto | status")
        sys.exit(1)

    target_model = MODEL_MAP[command]
    label = LABEL_MAP[target_model]

    # Bereits auf Zielmodell?
    found = find_current_models(config)
    most_common = max(found, key=found.get) if found else None
    if most_common == target_model and len(found) == 1:
        print(f"Bereits auf {label} ({target_model})")
        sys.exit(0)

    # Backup
    try:
        shutil.copy(CONFIG_PATH, BACKUP_PATH)
    except Exception as e:
        print(f"Backup-Warnung: {e}")

    # ALLE openrouter/* durch Zielmodell ersetzen
    total_changed = replace_all_openrouter_models(config, target_model)

    if total_changed == 0:
        print(f"Keine Eintraege zum Aendern gefunden.")
        sys.exit(0)

    # Config schreiben
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"=== MODEL GEWECHSELT ===")
    print(f"Neues Modell: {label} ({target_model})")
    print(f"Eintraege geaendert: {total_changed}")

    # Gateway restart
    gw_status = restart_gateway()
    print(f"Gateway restart: {gw_status}")
    print(f"Zeit: {datetime.now().strftime('%H:%M:%S')}")


if __name__ == "__main__":
    main()
