#!/usr/bin/env python3
"""Hängt Eintrag an CHANGELOG.md an."""
import os
import sys
from datetime import datetime

def add_changelog(project_path, text):
    changelog_path = os.path.join(project_path, "CHANGELOG.md")
    
    if not os.path.exists(changelog_path):
        print("Fehler: CHANGELOG.md nicht gefunden. Erstelle mit 'init'.")
        sys.exit(1)
    
    date = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"## [{date}] {text}\n"
    
    with open(changelog_path, "a", encoding="utf-8") as f:
        f.write(entry)
    
    print(f"✓ Eintrag hinzugefügt: {text}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python add.py <projekt-pfad> \"<text>\"")
        sys.exit(1)
    add_changelog(sys.argv[1], sys.argv[2])