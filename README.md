# Commonhold

**Open network for player-run worlds.** Run your own world, play with everyone else, and keep your character
forever, even if a server shuts down. No owner, no money, no game files: just signed records that anyone can check.

<!-- ch:pulse:start -->
<!-- ch:pulse:end -->

[Console](https://commonhold.github.io/commonhold/) · [Wiki](wiki/Home.md) · [Spec](spec/README.md) · [Credits](CREDITS.md) · [How to join](wiki/How-to-join.md)
<!-- TODO(owner): fix the console link once the org name is final -->

## Who's building it

Each member keeps their own project and name. Commonhold is the shared road between them.

<!-- ch:members:start -->
<!-- ch:members:end -->

## The spec

<!-- ch:spec:start -->
<!-- ch:spec:end -->

## Roadmap

<!-- ch:roadmap:start -->
<!-- ch:roadmap:end -->

## Open decisions

<!-- ch:decisions:start -->
<!-- ch:decisions:end -->

## Recently shipped

<!-- ch:recent:start -->
<!-- ch:recent:end -->

## The story so far

<!-- ch:chronicle:start -->
<!-- ch:chronicle:end -->

## How this repository works

- **`members/<you>/` is yours.** Ship with `python tools/ch.py ship -m "..."` (or `Ship my folder.bat`); it merges by
  itself once the guard check passes. Nobody else can change it without your approval.
- **`joint/` and `wiki/`** need 2 other members to approve. **`spec/`** needs 3, including the section's steward.
- **The guard** blocks game files, executables, secrets and large binaries in every pull request.
- **This README rewrites its own sections** every day and after every merge, from member files, the spec status,
  the roadmap, decisions and history. Edit the text outside the marked sections by pull request like anything else.

Read [CHARTER.md](CHARTER.md) and [GOVERNANCE.md](GOVERNANCE.md) before your first pull request.

---
Spec and shared code: Apache-2.0. Each member folder keeps its owner's licence (see that folder's `member.yml`).
Not affiliated with or endorsed by any game publisher. Players use their own clients and game files.
