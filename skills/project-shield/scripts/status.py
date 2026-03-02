#!/usr/bin/env python3
"""Zeigt letzte Einträge aus CHANGELOG.md."""
import os
import sys

def show_status(project_path, limit=5):
    changelog_path = os.path.join(project_path, "CHANGELOG.md")
    
    if not os.path.exists(changelog_path):
        print("Fehler: CHANGELOG.md nicht gefunden.")
        sys.exit(1)
    
    with open(changelog_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    # Finde alle Einträge (## [...])
    entries = [line.strip() for line in lines if line.strip().startswith("## [")]
    
    if not entries:
        print("Keine Einträge gefunden.")
        return
    
    print("Letzte Änderungen:")
    print("-" * 40)
    for entry in reversed(entries[-limit:]):
        print(entry)

if __name__ == "__main__":
    project_path = sys.argv[1] if len(sys.argv) > 1 else "."
    show_status(project_path)