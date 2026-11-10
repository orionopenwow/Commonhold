#!/usr/bin/env python3
"""Commonhold Discord: set up the server for developers, in one run, from your own PC.

    py -3 commonhold_discord.py                  preview: shows the whole plan, changes nothing
    py -3 commonhold_discord.py --go             makes what's missing and posts each channel's purpose (pinned)
    py -3 commonhold_discord.py --go --repo https://github.com/<org>/commonhold    the same, with the repo link

What it does:
  1. finds the server the bot is in (or --guild <id> when it's in more than one);
  2. makes the roles that are missing (Builder, Steward);
  3. makes the categories and channels that are missing, named "<emoji>︱<name>" like the Leyline Discord. A channel
     that already exists under the same name (with or without the emoji) is kept and moved into place, so its history
     stays. Topics are set; #welcome, #announcements and #ships are read-only for everyone;
  4. posts one short message in each channel saying what it's for, and pins it. A channel where the bot has already
     posted is skipped, so running it twice changes nothing the second time.
It never deletes or renames anything else, and never changes the server's name, icon or banner.

Discord only lets a program change a server through a bot token: make a throwaway bot, invite it with Administrator,
run this, then kick the bot (README.md). The token is read from token.txt next to this script or asked for with the
input hidden; it is never printed, logged or saved. Python 3 standard library only.
"""
from __future__ import annotations

import argparse
import getpass
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API = "https://discord.com/api/v10"
BAR = "︱"   # the vertical bar the Leyline Discord uses between the emoji and the name

TEXT, VOICE, CATEGORY = 0, 2, 4
SEND = 1 << 11
SEND_IN_THREADS = 1 << 38
CREATE_PUBLIC_THREADS = 1 << 35
CREATE_PRIVATE_THREADS = 1 << 36
READ_ONLY_DENY = SEND | SEND_IN_THREADS | CREATE_PUBLIC_THREADS | CREATE_PRIVATE_THREADS

ROLES = [
    {"name": "Steward", "color": 0xC4892F, "hoist": True, "why": "approves changes to one section of the spec"},
    {"name": "Builder", "color": 0x3D8B7D, "hoist": True, "why": "has a members/ folder in the repo"},
]

# (emoji, name, type, read_only, topic, purpose message). {repo} is replaced by the repo line, or dropped.
PLAN = [
    ("🧭", "start here", [
        ("👋", "welcome", TEXT, True, "What Commonhold is and how to join",
         "**Welcome to Commonhold.** An open network for player-run worlds: run your own world, play with everyone "
         "else, and keep your character even if a server shuts down. No owner, no money, no game files.\n\n"
         "**To join the build:** say hi in #general with your GitHub name and what you'd like to work on. You'll get "
         "a folder in the repo that only you can change, and it ships itself in one click.{repo}"),
        ("📢", "announcements", TEXT, True, "Milestones only; every post links to the repo",
         "**Announcements.** Milestones only: spec versions, the first round trips, new doors into the network. "
         "Every post links to the repo, where the details live."),
    ]),
    ("🛠️", "build", [
        ("💬", "general", TEXT, False, "Talk, introductions, ideas",
         "**General.** Introductions, ideas and anything that doesn't fit elsewhere. New here? Tell us your GitHub "
         "name and what you'd like to build, and a member will add your folder."),
        ("📜", "spec", TEXT, False, "The protocol: identity, passports, visits, resilience, directory",
         "**Spec.** Discussion of the Commonhold protocol, section by section. Each section has a steward who "
         "approves changes. Anything we decide here gets written into `spec/` or `joint/decisions/`, because the "
         "repo is the record, not this chat."),
        ("⚙️", "dev", TEXT, False, "Code, adapters, launchers, tools; share what you're working on",
         "**Dev.** Code, adapters, launchers and tools. Share what you're building, ask for review, paste errors. "
         "Your own folder ships with `Ship my folder.bat` (or `ship.sh`); shared folders need approvals."),
        ("🐞", "help", TEXT, False, "Stuck? Setup, the repo, hosting, the guard check",
         "**Help.** Stuck with setup, the repo, hosting or the guard check? Ask here with what you tried and the "
         "exact message you got."),
        ("🚀", "ships", TEXT, True, "Everything merged into the repo, posted automatically",
         "**Ships.** Every change merged into the repo shows up here automatically. Read-only; talk about a ship "
         "in #dev."),
        ("🎙️", "dev call", VOICE, False, "", ""),
    ]),
]


def chan_name(emoji: str, name: str, kind: int) -> str:
    """'💬︱general' for text channels (Discord lowercases and hyphenates text names); categories keep spaces."""
    if kind == TEXT:
        return f"{emoji}{BAR}{name.replace(' ', '-')}"
    return f"{emoji}{BAR}{name}"


def bare(name: str) -> str:
    """The name without its leading emoji and bar, for matching an existing channel: '💬︱general' -> 'general'."""
    n = name.strip().lower()
    for sep in (BAR, "┃", "|", "│", "・"):
        if sep in n:
            n = n.split(sep, 1)[1]
    n = n.lstrip("#").strip()
    return n.replace(" ", "-")


# ---------------------------------------------------------------------------------------------- Discord REST
class Discord:
    def __init__(self, token: str):
        self.token = token

    def call(self, method: str, path: str, body=None):
        data = json.dumps(body).encode() if body is not None else None
        for _ in range(6):
            req = urllib.request.Request(API + path, data=data, method=method, headers={
                "Authorization": f"Bot {self.token}", "Content-Type": "application/json",
                "User-Agent": "DiscordBot (https://github.com/commonhold, 1.0)"})
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    raw = r.read()
                    return json.loads(raw) if raw else None
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    wait = float(json.loads(e.read() or b"{}").get("retry_after", 1.0))
                    time.sleep(wait + 0.25)
                    continue
                msg = e.read().decode("utf-8", "replace")[:300]
                if e.code == 401:
                    raise SystemExit("Discord said the token isn't valid. Copy the bot's token again (Bot -> Reset Token).")
                if e.code == 403:
                    raise SystemExit(f"Discord refused ({method} {path}): give the bot Administrator and drag its role to the top. {msg}")
                raise SystemExit(f"Discord error {e.code} on {method} {path}: {msg}")
        raise SystemExit("Discord kept asking us to slow down; try again in a minute.")


# ---------------------------------------------------------------------------------------------- the plan
def plan_actions(channels: list[dict], roles: list[dict]) -> list[tuple]:
    """What would change, as (kind, detail) rows, from the server's current channels and roles."""
    out = []
    have_roles = {r["name"].lower() for r in roles}
    for r in ROLES:
        if r["name"].lower() not in have_roles:
            out.append(("role", r["name"]))
    by_bare = {(bare(c["name"]), c["type"]): c for c in channels}
    for cemoji, cname, items in PLAN:
        cat = by_bare.get((bare(cname), CATEGORY))
        out.append(("keep category" if cat else "make category", chan_name(cemoji, cname, CATEGORY)))
        for emoji, name, kind, ro, topic, _msg in items:
            ch = by_bare.get((bare(name), kind))
            full = chan_name(emoji, name, kind)
            if ch is None:
                out.append(("make channel", full + (" (read-only)" if ro else "")))
            else:
                out.append(("keep channel", f"{ch['name']} -> {full}" if ch["name"] != full else full))
    return out


def ensure(d: Discord, gid: str, repo: str, go: bool) -> None:
    me = d.call("GET", "/users/@me")
    channels = d.call("GET", f"/guilds/{gid}/channels")
    roles = d.call("GET", f"/guilds/{gid}/roles")
    rows = plan_actions(channels, roles)
    print("\nThe plan:")
    for kind, detail in rows:
        print(f"  {kind:<14} {detail}")
    if not go:
        print("\nPreview only: nothing changed. Run again with --go to do it.")
        return

    have_roles = {r["name"].lower() for r in roles}
    for r in ROLES:
        if r["name"].lower() not in have_roles:
            d.call("POST", f"/guilds/{gid}/roles", {"name": r["name"], "color": r["color"], "hoist": r["hoist"], "mentionable": True})
            print(f"  made role {r['name']}")

    everyone = gid   # the @everyone role's id is the server's id
    by_bare = {(bare(c["name"]), c["type"]): c for c in channels}
    repo_line = f"\n\nRepo: {repo}" if repo else ""
    position = 0
    for cemoji, cname, items in PLAN:
        cat_name = chan_name(cemoji, cname, CATEGORY)
        cat = by_bare.get((bare(cname), CATEGORY))
        if cat is None:
            cat = d.call("POST", f"/guilds/{gid}/channels", {"name": cat_name, "type": CATEGORY, "position": position})
            print(f"  made category {cat_name}")
        elif cat["name"] != cat_name:
            d.call("PATCH", f"/channels/{cat['id']}", {"name": cat_name})
        position += 1
        for emoji, name, kind, ro, topic, msg in items:
            full = chan_name(emoji, name, kind)
            body = {"name": full, "type": kind, "parent_id": cat["id"], "position": position}
            if kind == TEXT:
                body["topic"] = topic
            if ro:
                body["permission_overwrites"] = [{"id": everyone, "type": 0, "allow": "0", "deny": str(READ_ONLY_DENY)}]
            ch = by_bare.get((bare(name), kind))
            if ch is None:
                ch = d.call("POST", f"/guilds/{gid}/channels", body)
                print(f"  made {full}")
            else:
                patch = {k: v for k, v in body.items() if k != "type"}
                if not ro:
                    patch.pop("permission_overwrites", None)
                d.call("PATCH", f"/channels/{ch['id']}", patch)
                print(f"  kept {full}")
            position += 1
            if kind == TEXT and msg:
                post_purpose(d, ch["id"], me["id"], msg.replace("{repo}", repo_line), full)
    print("\nDONE. You can kick the bot now (Server Settings -> Members -> the bot -> Kick).")


def post_purpose(d: Discord, cid: str, bot_id: str, text: str, label: str) -> None:
    recent = d.call("GET", f"/channels/{cid}/messages?limit=50") or []
    if any((m.get("author") or {}).get("id") == bot_id for m in recent):
        print(f"    {label}: already has its purpose post, skipped")
        return
    m = d.call("POST", f"/channels/{cid}/messages", {"content": text, "allowed_mentions": {"parse": []}})
    try:
        d.call("PUT", f"/channels/{cid}/pins/{m['id']}")
    except SystemExit:
        pass
    print(f"    {label}: posted and pinned its purpose")


def read_token() -> str:
    f = Path(__file__).with_name("token.txt")
    if f.exists():
        t = f.read_text(encoding="utf-8").strip()
        if t:
            return t
    return getpass.getpass("Paste the bot's token (hidden), then Enter: ").strip()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Set up the Commonhold Discord for developers.")
    ap.add_argument("--go", action="store_true", help="make the changes (without it: preview only)")
    ap.add_argument("--guild", help="the server's id, when the bot is in more than one")
    ap.add_argument("--repo", default="", help="the repo link to put in #welcome")
    a = ap.parse_args(argv)
    token = read_token()
    if not token:
        print("No token given.")
        return 1
    d = Discord(token)
    guilds = d.call("GET", "/users/@me/guilds")
    if a.guild:
        g = next((x for x in guilds if x["id"] == a.guild), None)
    elif len(guilds) == 1:
        g = guilds[0]
    else:
        print("The bot is in " + ("no server yet: invite it first (README.md)." if not guilds else
              "more than one server. Run again with --guild <id>:\n" + "\n".join(f"  {x['id']}  {x['name']}" for x in guilds)))
        return 1
    if g is None:
        print("The bot isn't in that server.")
        return 1
    print(f"Server: {g['name']}")
    ensure(d, g["id"], a.repo.strip(), a.go)
    return 0


if __name__ == "__main__":
    sys.exit(main())
