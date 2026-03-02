#!/usr/bin/env python3
"""Initialisiert project-shield in einem Projekt."""
import os
import sys
from datetime import datetime

README_TEMPLATE = '''# {project_name}

## Projekt-Ziel
> Kurze Beschreibung des Projekts

## Funktionen
- TODO: Funktionen auflisten

## Tech-Stack
- TODO: Technologien

## Getting Started
1. TODO: Setup-Schritte

---
**Letzte Änderung:** {date}
'''

CHANGELOG_HEADER = '''# Changelog
Alle Änderungen werden chronologisch festgehalten. Nichts wird gelöscht.

---

'''

def init_project(project_path):
    project_name = os.path.basename(project_path)
    date = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # README.md
    readme_path = os.path.join(project_path, "README.md")
    if not os.path.exists(readme_path):
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(README_TEMPLATE.format(project_name=project_name, date=date))
        print(f"✓ README.md erstellt")
    
    # CHANGELOG.md
    changelog_path = os.path.join(project_path, "CHANGELOG.md")
    if not os.path.exists(changelog_path):
        with open(changelog_path, "w", encoding="utf-8") as f:
            f.write(CHANGELOG_HEADER)
        print(f"✓ CHANGELOG.md erstellt")
    
    print(f"\n✓ Project-Shield initialisiert in: {project_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python init.py <projekt-pfad>")
        sys.exit(1)
    init_project(sys.argv[1])