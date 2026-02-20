# Codex Task Seed

Task:

OpenClaw Full Power Optimization: Erstelle folgende Dateien im Ordner openclaw_optimization/: 1) ANALYSIS.md - Detaillierte Analyse einer OpenClaw-Installation mit 6 Agents (main, testbot, sysadmin, financeplanner, planli, phonedealer). Aktuelle Config: model=openrouter/auto, thinking=off(main)/medium(subagents), maxConcurrent=4, streamMode=partial. Analysiere Performance-Bottlenecks und empfehle Optimierungen. 2) optimized_config_patch.json - Ein JSON-Patch fuer die OpenClaw gateway config.patch API mit: thinking=high ueberall, maxConcurrent=8, optimierte Hook-Einstellungen. 3) apply_optimization.py - Ein Python-Script das die Optimierungen dokumentiert und als Checkliste dient. Fokus: Maximale Performance, kein unnötiges Logging, schnelle Antwortzeiten.

## Goal
- Nice CLI calculator
- Add tests
- Improve error handling
