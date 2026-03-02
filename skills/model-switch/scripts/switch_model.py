#!/usr/bin/env python3
import sys
import os
import subprocess
import shutil
from datetime import datetime

CONFIG_PATH = os.path.expanduser("~/.openclaw/openclaw.json")
BACKUP_PATH = os.path.expanduser("~/.openclaw/openclaw.json.backup")
FREE_MODEL = "openrouter/openrouter/free"
PREMIUM_MODEL = "openrouter/minimax/minimax-m2.5"

def count_occurrences(content, model):
    return content.count(model)

def main():
    if len(sys.argv) < 2:
        print("Usage: switch_model.py free|premium|status")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    try:
        shutil.copy(CONFIG_PATH, BACKUP_PATH)
    except Exception as e:
        print(f"Backup nicht erstellt: {e}")
        sys.exit(1)
    
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if command == "free":
        old_count = count_occurrences(content, PREMIUM_MODEL)
        content = content.replace(PREMIUM_MODEL, FREE_MODEL)
        new_count = count_occurrences(content, FREE_MODEL)
        new_model = FREE_MODEL
        old_model = PREMIUM_MODEL
        
    elif command == "premium":
        old_count = count_occurrences(content, FREE_MODEL)
        content = content.replace(FREE_MODEL, PREMIUM_MODEL)
        new_count = count_occurrences(content, PREMIUM_MODEL)
        new_model = PREMIUM_MODEL
        old_model = FREE_MODEL
        
    elif command == "status":
        premium_count = count_occurrences(content, PREMIUM_MODEL)
        free_count = count_occurrences(content, FREE_MODEL)
        
        if premium_count > 0:
            aktuell = "premium"
        elif free_count > 0:
            aktuell = "free"
        else:
            aktuell = "unbekannt"
        
        print(f"=== MODEL STATUS ===")
        print(f"Aktuelles Modell: {aktuell}")
        print(f"premium-Eintraege: {premium_count}")
        print(f"free-Eintraege: {free_count}")
        sys.exit(0)
        
    else:
        print(f"Unbekannter Befehl: {command}")
        sys.exit(1)
    
    changed = old_count > 0
    
    if changed:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Gateway restart
        try:
            result = subprocess.run(
                ["C:\\Program Files\\nodejs\\openclaw.cmd", "gateway", "restart"],
                capture_output=True,
                text=True,
                timeout=15
            )
            if result.returncode == 0:
                gateway_status = "OK"
            else:
                gateway_status = "FEHLER"
        except Exception as e:
            gateway_status = f"FEHLER: {e}"
        
        print(f"=== MODELL GEWECHSELT ===")
        print(f"Von: {old_model}")
        print(f"Nach: {new_model}")
        print(f"Eintraege geaendert: {old_count}")
        print(f"Gateway restart: {gateway_status}")
        print(f"Zeit: {datetime.now().strftime('%H:%M:%S')}")
    else:
        print(f"Bereits auf {new_model}")

if __name__ == "__main__":
    main()