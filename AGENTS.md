# Instructions for AI assistants working in this repo

- **Start of a session:** run `python tools/ch.py sync` to get everyone's newest work.
- **Where to write:** only inside `members/<your user's handle>/`, unless your user asks for a shared change. Shared
  folders (`joint/`, `wiki/`, `spec/`) go through a normal pull request, and you must tell your user it needs approvals.
- **Shipping:** when your user says "ship", run `python tools/ch.py ship -m "<one line saying what changed>"`. It
  checks the files, branches from the newest main, opens the pull request, waits for the guard to merge it and syncs.
  Report its last line to your user.
- **Never:**
  - push to `main` or force-push;
  - edit other members' folders;
  - commit game files (archives, databases, models, maps, textures), executables, keys or tokens;
  - add anything decompiled, recompiled or leaked;
  - add payments or donation links;
  - put game or publisher brand names in player-facing text.
- **Commits:** sign off (`-s`). Add `Assisted-by: <tool>` to commit messages you wrote.
- **Read before changing shared things:** PHILOSOPHY.md (how we build), CHARTER.md, GOVERNANCE.md.
