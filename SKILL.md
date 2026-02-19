# OpenClaw Codex Bridge Skill

## Ziel
- Standardisiere die Arbeit mit der OpenClaw Codex Bridge für alle OpenClaw Agents.
- Nutze ein einheitliches Vokabular für Trigger-Erkennung und Follow-up auf Pull Requests.

## Workflow
1. Prüfe den Triggertext zuerst und leite die konkrete Absicht ab (Fix, Update, Review, Follow-up).
2. Konsultiere PR-Metadaten und Kommentare nur für entscheidungsrelevante Informationen.
3. Leite Änderungen minimal-invasiv aus der Triggerabsicht ab.
4. Führe lokale Validierungen aus (Lint, Tests, Format).
5. Committ Änderungen mit klarer Nachricht und erstelle anschließend einen PR mit präziser Zusammenfassung.

## Trigger-Mapping
- **OpenClaw / Codex Bridge**: Agentenübergreifende Bridge-Änderungen, Orchestrierung, Integrationen.
- **SKILL.md / skill-meta.json**: Skill-Pflege, Trigger-Optimierung, Verfügbarkeit für alle Agents.
- **PR Follow-up / Kommentar**: Nacharbeiten auf Basis von Reviewer- oder User-Feedback.
- **Trigger-Wörter**: Erweiterung oder Präzisierung der aktivierenden Schlüsselwörter.

## Qualitätskriterien
- Halte Trigger in description präzise und breit genug für reale Formulierungen.
- Vermeide redundante Prozessbeschreibungen; priorisiere klare, ausführbare Schritte.
- Stelle sicher, dass Metadaten globale Verfügbarkeit für OpenClaw Agents signalisieren.

## Befehle (für Agenten)
- `codex test` - GitHub-Verbindung testen
- `codex send <repo> "<task>"` - Task an Codex senden
- `codex workflow <repo> "<task>"` - Vollständiger Workflow
- `codex status <repo> <branch>` - Status prüfen
- `codex result <repo> <branch>` - Ergebnisse holen

## Trigger-Wörter
- openclaw, codex bridge, codex pr, skill, skill.md, skill-meta.json
- trigger-wörter, trigger words, agent routing, bridge automation
- github pr kommentar, follow-up actions