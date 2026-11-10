# Commonhold

**Open network for player-run worlds.** Run your own world, play with everyone else, and keep your character
forever, even if a server shuts down. No owner, no money, no game files: just signed records that anyone can check.

<!-- ch:pulse:start -->
Day **0** · **4** members · spec 0/8 sections accepted · 0/9 milestones done · updated 2026-11-10
<!-- ch:pulse:end -->

[Console](https://commonhold.github.io/commonhold/) · [Wiki](wiki/Home.md) · [Spec](spec/README.md) · [Credits](CREDITS.md) · [How to join](wiki/How-to-join.md)
<!-- TODO(owner): fix the console link once the org name is final -->

## Who's building it

Each member keeps their own project and name. Commonhold is the shared road between them.

<!-- ch:members:start -->
| Member | Brings | Project | Licence of their folder | Commits |
|---|---|---|---|---|
| **IS4**  | Shared identity, live play across player-run servers (mod-p2p), spec quality | [Project Eternal mod-p2p](https://github.com/Project-Eternal/mod-p2p) | MPL-2.0 | 0 |
| **Maweu**  | Shutdown resilience and backups, local tamper-proof passports, anti-selling, safety policy, fair listing |  | Apache-2.0 | 0 |
| **Orion** [@orionopenwow](https://github.com/orionopenwow) | Directory and realm cards, relays, one-click hosting and joining, the community workspace | [Leyline](https://leylinelauncher.com) | Apache-2.0 | 1 |
| **Leon (Wrekczar)**  | Character Passport, Customs Vault, three-way reconciliation, visit rules | Worlds of CoreCraft | Leon's choice | 0 |
<!-- ch:members:end -->

## The spec

<!-- ch:spec:start -->
Spec **v0.1-draft**: 0 of 8 sections accepted.

| Section | Steward | Status |
|---|---|---|
| [Identity and keys](spec/identity.md) | is4 | 🟨 draft |
| [Signed records](spec/records.md) | orion | 🟨 draft |
| [Realm cards and tiers](spec/directory.md) | orion | ⬜ empty |
| [Relays and transport](spec/relays.md) | orion | ⬜ empty |
| [Character Passport](spec/passport.md) | wrekczar | ⬜ empty |
| [Visits, charters and customs](spec/customs.md) | wrekczar | ⬜ empty |
| [Witness logs and re-homing](spec/resilience.md) | maweu | ⬜ empty |
| [Hosting, safety and privacy](spec/policy.md) | maweu | ⬜ empty |
<!-- ch:spec:end -->

## Roadmap

<!-- ch:roadmap:start -->
| When | Milestone | Status |
|---|---|---|
| Week 0 | Org created, workspace pushed, members invited, Discord opened | 🟨 in progress |
| Weeks 1-3 | Spec v0.1: identity, realm card, charter, passport, visit record, witness entry, test vectors | ⬜ to do |
| Weeks 2-5 | Reference library (Python + Rust) and commonhold-check | ⬜ to do |
| Weeks 3-7 | Stock AzerothCore passport adapter | ⬜ to do |
| Weeks 6-8 | Pilot: one character visits another world and comes home; chaos tests | ⬜ to do |
| Weeks 6-10 | Leyline door: tiers, tags, passport store, backups, Visit and Re-home | ⬜ to do |
| Weeks 8-12 | Live-play bridge with mod-p2p on stock AzerothCore | ⬜ to do |
| Weeks 8-12 | Waystations, witness logs, Close this world, re-homing | ⬜ to do |
| Weeks 10-12 | First league with 3-5 hosts; spec v1.0 public | ⬜ to do |
<!-- ch:roadmap:end -->

## Open decisions

<!-- ch:decisions:start -->
- [One identity shared with mod-p2p](joint/decisions/0001-shared-identity.md), proposed by orion
- [Clean provenance for everything shared](joint/decisions/0002-clean-provenance.md), proposed by orion
- [Your folder is yours; shared work is reviewed](joint/decisions/0003-folders-and-shipping.md), proposed by orion
<!-- ch:decisions:end -->

## Recently shipped

<!-- ch:recent:start -->
- 2026-11-10 · **orion** · Commonhold workspace: folders, guard, living README, console, wiki, spec skeleton
<!-- ch:recent:end -->

## The story so far

<!-- ch:chronicle:start -->
- **2026-11-10**: IS4 (Project Eternal), Leon (Worlds of CoreCraft), Maweu and Orion (Leyline) agree to link their work into one open network.
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
