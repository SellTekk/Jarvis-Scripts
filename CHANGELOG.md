# Changelog

## 2026-03-03

- Added `codex_tasks/crawler_fix/crawler_handy_wrapper.py` to auto-restart `crawler_handy.py` after crashes and continue until all products are processed.
- Added checkpoint persistence via `crawler_handy.checkpoint.json` with restart count, progress, and completion status.
- Updated `codex_tasks/crawler_fix/README.md` with analysis and usage instructions for the watchdog wrapper.
