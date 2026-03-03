# Codex Task

Task:

Der bestehende Python Wrapper (F:/crawlerv5/crawler_wrapper.py) startet nach SIGKILL nicht automatisch neu. AUFGABE: 1) Analysiere das Problem 2) Erstelle einen verbesserten Wrapper der: a) Bei ANY Exit-Code (auch SIGKILL) automatisch neustartet b) Die Checkpoint-Datei ausliest und dort weitermacht wo der Crawler aufgehört c) Dies in einer Endlos-Schleife macht bis alle Produkte verarbeitet sind

File:
crawler_wrapper.py
