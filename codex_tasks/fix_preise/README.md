# Codex Task

Task:

Fix the Python script crawler_handy_preise.py - it has an IndentationError at line 190. The error is: 'Variation': r['Variation'] has wrong indentation. Also add these features: 1) Remove the code that loads existing results and skips products with price>0 - we want to ALWAYS crawl fresh prices 2) Add the robustness features: orphan chrome kill, lean chrome options, save every 20 products, browser restart every 30 products

File:
crawler_handy_preise.py
