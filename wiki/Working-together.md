# Working together

Many people work in this repo at once. Three habits keep everyone in sync, and nobody ever overwrites anyone.

## The loop
1. **Get latest** when you sit down: double-click `Get latest.bat` (Windows) or run `./get-latest.sh`. You get
   everyone's newest work, and anything you haven't shipped stays as it is.
2. **Work in your own folder:** `members/<you>/`. Only you can change it, so nobody else's work can clash with it.
3. **Ship:** double-click `Ship my folder.bat` (or `./ship.sh "what changed"`) and type one line about what changed,
   for example `passport: first draft of the return trip`.

Shipping then does everything else:
- it checks your files: no game files, executables, secrets or big binaries;
- it starts from the newest main, so it never undoes someone else's work;
- it sends your change and waits while the guard merges it, usually under a minute;
- it brings you back up to date with everyone's work.

## Shared folders
`joint/`, `wiki/` and `spec/` belong to everyone, so changes there go through a pull request with approvals (the guard
says whose). Before you edit a shared file, say so in #spec or #dev so two people don't rewrite the same lines.
Small, frequent pull requests merge more easily than one big one.

## Never
- Push straight to `main` (it's blocked anyway) or force-push.
- Edit someone else's folder without asking them. The guard will ask them to approve it.
- Commit files you don't have the right to share.

## Using an AI coding assistant
Paste this at the start of a session (Claude, Copilot, Cursor and others):

> You're working in the Commonhold repo. Read AGENTS.md first and follow it. Run `python tools/ch.py sync` before you
> start. Only change files in `members/<my-handle>/` unless I ask for something else. When I say "ship", run
> `python tools/ch.py ship -m "<one line saying what changed>"` and tell me the result. Never push to main, never
> force-push, never commit game files or secrets.

Replace `<my-handle>` with your folder name.
