"""
Auto-Restart Wrapper für Crawler
Startet den Crawler bei Crash automatisch neu
"""

import subprocess
import time
import os
import sys

CRAWLER_SCRIPT = "F:/crawlerv5/crawler_handy.py"
CHECKPOINT_FILE = "F:/crawlerv5/crawler_checkpoint.txt"
MAX_RESTARTS = 100  # Max Neustarts
WAIT_SECONDS = 5   # Wartezeit zwischen Neustarts

def get_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, 'r') as f:
                return int(f.read().strip())
        except:
            return 0
    return 0

def main():
    restarts = 0
    
    print("🔄 Auto-Restart Wrapper gestartet")
    print(f"   Script: {CRAWLER_SCRIPT}")
    print(f"   Checkpoint: {CHECKPOINT_FILE}")
    print("-" * 40)
    
    while restarts < MAX_RESTARTS:
        checkpoint = get_checkpoint()
        print(f"\n[{restarts+1}] Starter Crawler... (Checkpoint: {checkpoint})")
        
        try:
            # Crawler starten
            result = subprocess.run(
                [sys.executable, CRAWLER_SCRIPT],
                cwd=os.path.dirname(CRAWLER_SCRIPT),
                timeout=3600  # 1 Stunde max pro Durchgang
            )
            
            # Erfolgreich beendet (Exit Code 0)
            print("✅ Crawler erfolgreich beendet!")
            break
            
        except subprocess.TimeoutExpired:
            print("⏱️ Timeout - Crawler läuft zu lange, restarte...")
            restarts += 1
            time.sleep(WAIT_SECONDS)
            
        except Exception as e:
            print(f"❌ Fehler: {e}")
            restarts += 1
            time.sleep(WAIT_SECONDS)
    
    if restarts >= MAX_RESTARTS:
        print(f"⚠️ Max Neustarts ({MAX_RESTARTS}) erreicht - beende")
    else:
        print("🏁 Fertig!")

if __name__ == "__main__":
    main()
