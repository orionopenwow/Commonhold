#!/usr/bin/env python3
"""Commonhold workspace tool: guard pull requests, render the living README and console data, ship your folder.

    python tools/ch.py guard --pr 12            (CI) is this pull request allowed, and may it merge itself?
    python tools/ch.py render                   (CI) rebuild README sections, CREDITS.md, CODEOWNERS, site/status.json
    python tools/ch.py ship -m "what changed"   (you) send your folder's changes; they merge themselves if clean
    python tools/ch.py check                    (you) the same file checks as the guard, on your working tree
    python tools/ch.py sync                     (you) get everyone's newest work, keeping what you haven't shipped

Needs Python 3.9+, PyYAML, git, and the GitHub CLI (gh) for guard and ship. Never runs code from a pull request:
the guard reads only the list of changed files, their text diffs and reviews through the GitHub API.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
MEMBER_RE = re.compile(r"^members/([a-z0-9][a-z0-9-]{0,38})/")

SECRET_PATTERNS = {
    "GitHub token": re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{60,})\b"),
    "Discord bot token": re.compile(r"\b[MNO][A-Za-z\d_-]{23,27}\.[A-Za-z\d_-]{6}\.[A-Za-z\d_-]{27,40}\b"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |ED25519 |PGP )?PRIVATE KEY-----"),
    "AWS key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "Slack token": re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b"),
    "Codeberg/Gitea token": re.compile(r"(?i)\b(?:codeberg|gitea)[_-]?token\s*[:=]\s*['\"]?[0-9a-f]{40}\b"),
}


# ---------------------------------------------------------------------------------------------- config and members
def load_yaml(path: Path, default=None):
    if not path.exists():
        return default
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or default


def load_config(root: Path = ROOT) -> dict:
    return load_yaml(root / "commonhold.yml", {})


def load_members(root: Path = ROOT) -> dict[str, dict]:
    """handle -> member.yml contents, for every members/<handle>/member.yml."""
    out = {}
    for p in sorted((root / "members").glob("*/member.yml")):
        m = load_yaml(p, {}) or {}
        m.setdefault("handle", p.parent.name)
        if m["handle"] != p.parent.name:
            raise SystemExit(f"{p}: handle '{m['handle']}' must match its folder name '{p.parent.name}'")
        out[m["handle"]] = m
    return out


def login_to_handle(members: dict[str, dict]) -> dict[str, str]:
    return {str(m.get("github", "")).lower(): h for h, m in members.items() if m.get("github")}


# ---------------------------------------------------------------------------------------------- guard: rules
@dataclass
class Need:
    """One requirement a pull request must meet."""
    kind: str                 # own | owner | joint | spec | core | blocked
    detail: str
    approvers_needed: int = 0
    must_include: set = field(default_factory=set)   # member handles that must be among the approvers
    files: list = field(default_factory=list)


def classify(path: str, author_handle: str | None, members: dict, cfg: dict) -> tuple[str, str | None]:
    """(kind, owner_or_section) for one changed path."""
    rules = cfg.get("rules", {})
    if any(path == g or path.startswith(g) for g in rules.get("generated_paths", [])):
        return "blocked", "generated"
    m = MEMBER_RE.match(path)
    if m:
        h = m.group(1)
        if h not in members:
            return "joint", f"new member folder members/{h}/"
        return ("own", h) if h == author_handle else ("owner", h)
    if path.startswith("members/"):
        return "joint", "members/ (outside a member folder)"
    if any(path == c or path.startswith(c) for c in rules.get("core_paths", [])):
        return "core", None
    if any(path.startswith(s) for s in rules.get("spec_paths", ["spec/"])):
        rest = path.split("/", 1)[1] if "/" in path else ""
        section = re.split(r"[/.]", rest)[0] if rest else ""
        return "spec", section
    return "joint", None


def needs_for(paths: list[str], author_handle: str | None, members: dict, cfg: dict) -> list[Need]:
    rules = cfg.get("rules", {})
    stewards = cfg.get("spec_sections", {})
    needs: dict[tuple, Need] = {}

    def add(key, need, path):
        n = needs.setdefault(key, need)
        n.files.append(path)

    for p in paths:
        kind, who = classify(p, author_handle, members, cfg)
        if kind == "blocked":
            add(("blocked",), Need("blocked", "generated files are written only by the render job"), p)
        elif kind == "own":
            add(("own",), Need("own", f"your own folder members/{who}/"), p)
        elif kind == "owner":
            add(("owner", who), Need("owner", f"members/{who}/ belongs to {who}", 1, {who}), p)
        elif kind == "spec":
            st = stewards.get(who)
            add(("spec", who), Need("spec", f"spec section '{who or 'general'}'"
                                    + (f" (steward: {st})" if st else ""),
                                    int(rules.get("spec_approvals", 3)),
                                    {st} if st and st != author_handle else set()), p)
        elif kind == "core":
            add(("core",), Need("core", "how the workspace works", int(rules.get("core_approvals", 2))), p)
        else:
            add(("joint", who or ""), Need("joint", who or "joint work", int(rules.get("joint_approvals", 2))), p)
    return list(needs.values())


def check_needs(needs: list[Need], approvals: set[str]) -> list[tuple[Need, bool, str]]:
    out = []
    for n in needs:
        if n.kind == "blocked":
            out.append((n, False, "remove these files from the pull request"))
        elif n.kind == "own":
            out.append((n, True, "ships on its own"))
        else:
            missing = n.must_include - approvals
            enough = len(approvals) >= n.approvers_needed
            ok = enough and not missing
            why = []
            if not enough:
                why.append(f"{len(approvals)}/{n.approvers_needed} member approvals")
            if missing:
                why.append("needs approval from " + ", ".join(sorted(missing)))
            out.append((n, ok, "approved" if ok else "; ".join(why)))
    return out


# ---------------------------------------------------------------------------------------------- guard: content
def scan_text(path: str, text: str) -> list[str]:
    problems = []
    for name, rx in SECRET_PATTERNS.items():
        if rx.search(text or ""):
            problems.append(f"{path}: looks like a {name}. Remove it and rotate it now")
    return problems


def scan_file(path: str, patch: str | None, size: int | None, status: str, cfg: dict) -> list[str]:
    g = cfg.get("guard", {})
    ext = os.path.splitext(path.lower())[1]
    problems = []
    if status == "removed":
        return problems
    if ext in g.get("blocked_extensions", []):
        problems.append(f"{path}: {ext} files can't be added (no game files, executables or binaries in Commonhold)")
    if patch is None:   # binary or too large for a text diff
        if ext not in g.get("allowed_binary_extensions", []):
            problems.append(f"{path}: binary file type {ext or '(none)'} isn't allowed; images and PDFs only")
        elif size is not None and size > int(g.get("max_binary_bytes", 2_000_000)):
            problems.append(f"{path}: {size // 1000} KB is over the {int(g.get('max_binary_bytes')) // 1000} KB limit")
    else:
        added = "\n".join(l[1:] for l in patch.splitlines() if l.startswith("+") and not l.startswith("+++"))
        problems += scan_text(path, added)
    return problems


def dco_problems(commits: list[dict]) -> list[str]:
    bad = []
    for c in commits:
        msg = c.get("commit", {}).get("message", "")
        if "Signed-off-by:" not in msg:
            bad.append(c.get("sha", "")[:7] + " " + msg.splitlines()[0][:60] if msg else c.get("sha", "")[:7])
    return [f"commit {b} has no Signed-off-by line (commit with -s, or use tools/ch.py ship)" for b in bad]


# ---------------------------------------------------------------------------------------------- guard: GitHub glue
def gh_json(*args: str):
    r = subprocess.run(["gh", "api", *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"gh api {args[0]} failed: {r.stderr.strip()[:300]}")
    return json.loads(r.stdout or "null")


def gh_pages(path: str) -> list:
    out, page = [], 1
    while True:
        chunk = gh_json(f"{path}{'&' if '?' in path else '?'}per_page=100&page={page}")
        out += chunk
        if len(chunk) < 100:
            return out
        page += 1


def latest_approvals(reviews: list[dict], author_login: str, members: dict) -> set[str]:
    by_login = login_to_handle(members)
    state = {}
    for r in reviews:   # API returns oldest first; later reviews replace earlier ones
        login = (r.get("user") or {}).get("login", "").lower()
        if login and login != author_login.lower() and r.get("state") in ("APPROVED", "CHANGES_REQUESTED", "DISMISSED"):
            state[login] = r["state"]
    return {by_login[l] for l, s in state.items() if s == "APPROVED" and l in by_login}


def cmd_guard(a) -> int:
    cfg, members = load_config(), load_members()   # read from the base branch checkout, never from the PR
    repo = a.repo or os.environ.get("GITHUB_REPOSITORY") or cfg.get("repo")
    pr = gh_json(f"repos/{repo}/pulls/{a.pr}")
    author = pr["user"]["login"]
    author_handle = login_to_handle(members).get(author.lower())
    files = gh_pages(f"repos/{repo}/pulls/{a.pr}/files")
    reviews = gh_pages(f"repos/{repo}/pulls/{a.pr}/reviews")
    commits = gh_pages(f"repos/{repo}/pulls/{a.pr}/commits")
    head = pr["head"]["sha"]

    problems = []
    for f in files:
        size = None
        if f.get("patch") is None and f.get("status") != "removed":
            try:
                size = gh_json(f"repos/{repo}/contents/{f['filename']}?ref={head}").get("size")
            except SystemExit:
                size = None
        problems += scan_file(f["filename"], f.get("patch"), size, f.get("status", ""), cfg)
    problems += dco_problems(commits)

    paths = [f["filename"] for f in files]
    needs = needs_for(paths, author_handle, members, cfg)
    approvals = latest_approvals(reviews, author, members)
    results = check_needs(needs, approvals)
    ok = not problems and all(r[1] for r in results)
    own_only = ok and author_handle is not None and all(n.kind == "own" for n in needs)
    report = render_guard_report(author, author_handle, results, problems, approvals, own_only, ok)
    print(report)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as s:
            s.write(report + "\n")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as o:
            o.write(f"ok={'true' if ok else 'false'}\nown_only={'true' if own_only else 'false'}\n")
    return 0 if ok else 1


def render_guard_report(author, handle, results, problems, approvals, own_only, ok) -> str:
    lines = [f"## Guard: {'✅ allowed' if ok else '❌ not yet'}", "",
             f"Author: **{author}**" + (f" (member `{handle}`)" if handle else " (not a member yet)"),
             f"Member approvals so far: {', '.join(sorted(approvals)) or 'none'}", "",
             "| Change | Rule | Status |", "|---|---|---|"]
    for n, good, why in results:
        shown = ", ".join(f"`{p}`" for p in n.files[:4]) + (f" +{len(n.files) - 4} more" if len(n.files) > 4 else "")
        lines.append(f"| {shown} | {n.detail} | {'✅' if good else '⏳'} {why} |")
    if problems:
        lines += ["", "### Must fix", *[f"- {p}" for p in problems]]
    if own_only:
        lines += ["", "Only your own folder changed, so this merges itself once checks pass."]
    return "\n".join(lines)


# ---------------------------------------------------------------------------------------------- check (local)
def cmd_check(a) -> int:
    cfg = load_config()
    r = subprocess.run(["git", "-C", str(ROOT), "diff", "--name-status", a.base], capture_output=True, text=True)
    untracked = subprocess.run(["git", "-C", str(ROOT), "ls-files", "--others", "--exclude-standard"],
                               capture_output=True, text=True).stdout.split()
    entries = [l.split("\t") for l in r.stdout.splitlines() if l] + [["A", u] for u in untracked]
    problems = []
    for e in entries:
        status, path = e[0], e[-1]
        p = ROOT / path
        if status.startswith("D") or not p.exists():
            continue
        data = p.read_bytes()
        is_text = b"\0" not in data[:8000]
        patch = ("\n".join("+" + l for l in data.decode("utf-8", "replace").splitlines())) if is_text else None
        problems += scan_file(path, patch, len(data), "added", cfg)
    print("\n".join(problems) if problems else "CHECK OK: no game files, binaries or secrets")
    return 1 if problems else 0


# ---------------------------------------------------------------------------------------------- render
MARK = "<!-- ch:{name}:{edge} -->"


def replace_section(text: str, name: str, body: str) -> str:
    start, end = MARK.format(name=name, edge="start"), MARK.format(name=name, edge="end")
    if start not in text or end not in text:
        return text
    pre, rest = text.split(start, 1)
    _, post = rest.split(end, 1)
    return f"{pre}{start}\n{body.rstrip()}\n{end}{post}"


def git_log(root: Path, n: int = 400) -> list[dict]:
    fmt = "%H%x1f%an%x1f%ae%x1f%cI%x1f%s"
    r = subprocess.run(["git", "-C", str(root), "log", f"-{n}", f"--format={fmt}", "--name-only"],
                       capture_output=True, text=True)
    out, cur = [], None
    for line in r.stdout.splitlines():
        if "\x1f" in line:
            h, an, ae, date, subj = line.split("\x1f")
            cur = {"sha": h, "name": an, "email": ae, "date": date, "subject": subj, "files": []}
            out.append(cur)
        elif line.strip() and cur is not None:
            cur["files"].append(line.strip())
    return out


def commit_handle(c: dict, members: dict) -> str | None:
    email, name = c["email"].lower(), c["name"].lower()
    for h, m in members.items():
        gh = str(m.get("github", "")).lower()
        if gh and (email.endswith(f"+{gh}@users.noreply.github.com") or email == f"{gh}@users.noreply.github.com"):
            return h
        if name in [str(x).lower() for x in m.get("git_names", [])] or name == str(m.get("name", "")).lower():
            return h
    return None


def area_of(path: str) -> str:
    m = MEMBER_RE.match(path)
    if m:
        return f"members/{m.group(1)}"
    return path.split("/", 1)[0] if "/" in path else "root"


def build_status(root: Path = ROOT, today: dt.date | None = None) -> dict:
    cfg, members = load_config(root), load_members(root)
    today = today or dt.date.today()
    log = git_log(root)
    spec = load_yaml(root / "spec" / "status.yml", {}) or {}
    roadmap = load_yaml(root / "joint" / "roadmap.yml", {}) or {}
    decisions = []
    for p in sorted((root / "joint" / "decisions").glob("*.md")):
        if p.stem.startswith("0000"):
            continue
        meta, title = front_matter(p.read_text(encoding="utf-8"))
        decisions.append({"id": p.stem, "title": meta.get("title") or title or p.stem,
                          "status": meta.get("status", "proposed"), "proposed_by": meta.get("proposed_by", ""),
                          "date": str(meta.get("date", ""))})
    credits = {h: {"commits": 0, "areas": {}, "last": None} for h in members}
    recent = []
    for c in log:
        h = commit_handle(c, members)
        if h:
            cr = credits[h]
            cr["commits"] += 1
            cr["last"] = cr["last"] or c["date"]
            for f in c["files"]:
                a = area_of(f)
                cr["areas"][a] = cr["areas"].get(a, 0) + 1
        if len(recent) < 12 and not c["subject"].startswith("render:"):
            recent.append({"date": c["date"][:10], "who": h or c["name"], "subject": c["subject"][:100]})
    started = dt.date.fromisoformat(str(cfg.get("started", today.isoformat())))
    wiki = sorted((p.name for p in (root / "wiki").glob("*.md") if not p.name.startswith("_")),
                  key=lambda n: (n != "Home.md", n))
    secs = spec.get("sections", [])
    return {
        "project": cfg.get("project", "Commonhold"), "descriptor": cfg.get("descriptor", ""),
        "tagline": cfg.get("tagline", ""), "repo": cfg.get("repo", ""),
        "generated": today.isoformat(), "age_days": (today - started).days,
        "members": [{**{k: v for k, v in m.items() if k not in ("git_names",)}, "handle": h,
                     "credit": credits[h]} for h, m in members.items()],
        "spec": {"version": spec.get("version", "0.0"), "sections": secs,
                 "done": sum(1 for s in secs if s.get("status") in ("accepted", "stable"))},
        "roadmap": roadmap.get("phases", []),
        "decisions": decisions, "recent": recent, "wiki": wiki,
        "doors": load_yaml(root / "joint" / "doors.yml", {}).get("doors", []) if (root / "joint" / "doors.yml").exists() else [],
        "thanks": load_yaml(root / "joint" / "thanks.yml", {}) or {},
    }


def front_matter(text: str) -> tuple[dict, str]:
    meta, body = {}, text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            meta = yaml.safe_load(parts[1]) or {}
            body = parts[2]
    title = next((l[2:].strip() for l in body.splitlines() if l.startswith("# ")), "")
    return meta, title


STATUS_CHIP = {"empty": "⬜ empty", "draft": "🟨 draft", "review": "🟧 in review", "accepted": "🟩 accepted",
               "stable": "✅ stable", "todo": "⬜ to do", "doing": "🟨 in progress", "done": "✅ done",
               "proposed": "🟨 proposed", "rejected": "⬛ not adopted", "superseded": "⬛ superseded"}


def chip(s: str) -> str:
    return STATUS_CHIP.get(str(s), str(s))


def render_sections(st: dict) -> dict[str, str]:
    members = st["members"]
    rows = ["| Member | Brings | Project | Licence of their folder | Commits |", "|---|---|---|---|---|"]
    for m in members:
        proj = m.get("project") or {}
        pj = f"[{proj.get('name')}]({proj.get('url')})" if proj.get("url") else proj.get("name", "")
        gh = f"[@{m['github']}](https://github.com/{m['github']})" if m.get("github") else ""
        rows.append(f"| **{m.get('name', m['handle'])}** {gh} | {m.get('role', '')} | {pj} | "
                    f"{m.get('license', 'Apache-2.0')} | {m['credit']['commits']} |")
    spec = [f"Spec **v{st['spec']['version']}**: {st['spec']['done']} of {len(st['spec']['sections'])} sections accepted.",
            "", "| Section | Steward | Status |", "|---|---|---|"]
    spec += [f"| [{s.get('title', s['id'])}](spec/{s['id']}.md) | {s.get('steward', '')} | {chip(s.get('status'))} |"
             for s in st["spec"]["sections"]]
    road = ["| When | Milestone | Status |", "|---|---|---|"]
    road += [f"| {p.get('when', '')} | {p.get('title', p.get('id'))} | {chip(p.get('status'))} |" for p in st["roadmap"]]
    open_d = [d for d in st["decisions"] if d["status"] == "proposed"]
    dec = ([f"- [{d['title']}](joint/decisions/{d['id']}.md), proposed by {d['proposed_by'] or 'someone'}" for d in open_d]
           or ["- None open right now."])
    done_d = [d for d in st["decisions"] if d["status"] == "accepted"]
    if done_d:
        dec += ["", "Accepted: " + ", ".join(f"[{d['title']}](joint/decisions/{d['id']}.md)" for d in done_d)]
    rec = [f"- {r['date']} · **{r['who']}** · {r['subject']}" for r in st["recent"]] or ["- Nothing shipped yet."]
    done = sum(1 for p in st["roadmap"] if p.get("status") == "done")
    pulse = (f"Day **{st['age_days']}** · **{len(members)}** members · spec {st['spec']['done']}/"
             f"{len(st['spec']['sections'])} sections accepted · {done}/{len(st['roadmap'])} milestones done · "
             f"updated {st['generated']}")
    th = st.get("thanks") or {}
    thanks = []
    for p in th.get("people", []):
        gh = f" [@{p['github']}](https://github.com/{p['github']})" if p.get("github") else ""
        thanks.append(f"- **{p['name']}**{gh}: {p.get('for', '')}")
    if th.get("projects"):
        thanks.append("")
        thanks.append("Built on and learned from: " + ", ".join(f"[{x['name']}]({x['url']})" for x in th["projects"]) + ".")
    thanks.append("")
    thanks.append("Everyone's full contribution is in [CREDITS.md](CREDITS.md).")
    return {"pulse": pulse, "thanks": "\n".join(thanks), "members": "\n".join(rows), "spec": "\n".join(spec), "roadmap": "\n".join(road),
            "decisions": "\n".join(dec), "recent": "\n".join(rec)}


def render_credits(st: dict) -> str:
    out = ["# Credits", "", "Generated from `members/*/member.yml` and the project history. Edit your own `member.yml`",
           "to change how you're credited. Every piece of Commonhold carries its author's name.", ""]
    for m in sorted(st["members"], key=lambda m: -m["credit"]["commits"]):
        proj = m.get("project") or {}
        out += [f"## {m.get('name', m['handle'])}" + (f" ([@{m['github']}](https://github.com/{m['github']}))" if m.get("github") else ""),
                "", f"- **Brings:** {m.get('role', '')}"]
        if proj.get("name"):
            out.append(f"- **Project:** [{proj['name']}]({proj['url']})" if proj.get("url") else f"- **Project:** {proj['name']}")
        if m.get("stewards"):
            out.append(f"- **Steward of:** {', '.join(m['stewards'])}")
        areas = sorted(m["credit"]["areas"].items(), key=lambda kv: -kv[1])[:6]
        if areas:
            out.append("- **Worked on:** " + ", ".join(f"{a} ({n})" for a, n in areas))
        out.append(f"- **Commits:** {m['credit']['commits']}")
        if m.get("thanks"):
            out.append(f"- **Thanks:** {m['thanks']}")
        if m.get("contributed"):
            out.append("- **Contributed:**")
            out += [f"  - {c}" for c in m["contributed"]]
        out.append("")
    th = st.get("thanks") or {}
    if th.get("people"):
        out += ["## Thanks", "", "People whose ideas and reports shaped Commonhold. Want a folder of your own? Open a dev request.", ""]
        for p in th["people"]:
            gh = f" ([@{p['github']}](https://github.com/{p['github']}))" if p.get("github") else ""
            via = f" ({p['found_via']})" if p.get("found_via") else ""
            out.append(f"- **{p['name']}**{gh}{via}: {p.get('for', '')}")
        out.append("")
    if th.get("projects"):
        out += ["## Built on and learned from", ""]
        out += [f"- [{x['name']}]({x['url']}): {x.get('for', '')}" for x in th["projects"]]
        out.append("")
    return "\n".join(out)


def render_codeowners(cfg: dict, members: dict) -> str:
    stewards = sorted({f"@{members[h]['github']}" for h in cfg.get("spec_sections", {}).values()
                       if h in members and members[h].get("github")})
    team = " ".join(stewards) or "@TODO-stewards"
    lines = ["# Generated by tools/ch.py render. Member folders are guarded by the guard check, not listed here,",
             "# so you can ship your own folder without waiting for anyone.",
             f".github/ {team}", f"tools/ {team}", f"commonhold.yml {team}", f"CHARTER.md {team}",
             f"GOVERNANCE.md {team}", f"LICENSE {team}"]
    for section, h in cfg.get("spec_sections", {}).items():
        if h in members and members[h].get("github"):
            lines.append(f"spec/{section}.md @{members[h]['github']}")
    return "\n".join(lines) + "\n"


def update_chronicle(root: Path, st: dict) -> bool:
    path = root / "joint" / "chronicle.md"
    text = path.read_text(encoding="utf-8") if path.exists() else "# Chronicle\n\nThe story of Commonhold, one milestone at a time.\n"
    changed = False
    for p in st["roadmap"]:
        tag = f"<!-- milestone:{p.get('id')} -->"
        if p.get("status") == "done" and tag not in text:
            who = ", ".join(p.get("by", [])) or "the group"
            text = text.rstrip() + f"\n\n- **{p.get('done_on') or st['generated']}**: {p.get('title')}. Thanks to {who}. {tag}\n"
            changed = True
    for d in st["decisions"]:
        tag = f"<!-- decision:{d['id']} -->"
        if d["status"] == "accepted" and tag not in text:
            text = text.rstrip() + (f"\n\n- **{d['date'] or st['generated']}**: decided: {d['title']}"
                                    f" (proposed by {d['proposed_by'] or 'the group'}). {tag}\n")
            changed = True
    if changed:
        path.write_text(text, encoding="utf-8")
    return changed


def cmd_render(a) -> int:
    root = Path(a.root).resolve() if a.root else ROOT
    st = build_status(root)
    update_chronicle(root, st)
    chron = (root / "joint" / "chronicle.md")
    lines = [l for l in chron.read_text(encoding="utf-8").splitlines() if l.startswith("- **")] if chron.exists() else []
    readme = (root / "README.md").read_text(encoding="utf-8")
    secs = render_sections(st)
    secs["chronicle"] = "\n".join(re.sub(r"\s*<!--.*?-->", "", l) for l in lines[-5:]) or "- The story starts here."
    for name, body in secs.items():
        readme = replace_section(readme, name, body)
    (root / "README.md").write_text(readme, encoding="utf-8")
    (root / "CREDITS.md").write_text(render_credits(st), encoding="utf-8")
    (root / "CODEOWNERS").write_text(render_codeowners(load_config(root), load_members(root)), encoding="utf-8")
    (root / "site").mkdir(exist_ok=True)
    console = root / "site" / "console.html"
    if console.exists():   # the console is written without a document skeleton; GitHub Pages needs one
        (root / "site" / "index.html").write_text(
            '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n</head>\n<body>\n'
            + console.read_text(encoding="utf-8") + "\n</body>\n</html>\n", encoding="utf-8")
    (root / "site" / "status.json").write_text(json.dumps(st, indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    print(f"RENDER OK: {len(st['members'])} members, spec {st['spec']['done']}/{len(st['spec']['sections'])}, "
          f"{len(st['recent'])} recent ships")
    return 0


# ---------------------------------------------------------------------------------------------- ship (local)
def run(*cmd: str, check=True) -> str:
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    if check and r.returncode != 0:
        raise SystemExit(f"{' '.join(cmd[:3])} failed: {(r.stderr or r.stdout).strip()[:400]}")
    return r.stdout.strip()


def cmd_ship(a) -> int:
    members = load_members()
    login = run("gh", "api", "user", "--jq", ".login").lower()
    me = login_to_handle(members).get(login)
    if not me:
        print(f"Signed in to GitHub as {login}, which isn't a member yet. Add members/<you>/member.yml in a pull request first.")
        return 1
    status = [l[3:].split(" -> ")[-1] for l in run("git", "status", "--porcelain", "-uall").splitlines()]
    mine, other = [p for p in status if p.startswith(f"members/{me}/")], [p for p in status if not p.startswith(f"members/{me}/")]
    if other:
        print("These changes are outside your folder, so ship won't send them (open a normal pull request for them):")
        print("\n".join("  " + p for p in other))
    if not mine:
        print(f"Nothing to ship in members/{me}/.")
        return 0 if not other else 1
    cfg = load_config()
    problems = []
    for p in mine:
        f = ROOT / p
        if f.exists():
            data = f.read_bytes()
            text = b"\0" not in data[:8000]
            problems += scan_file(p, ("+" + data.decode("utf-8", "replace").replace("\n", "\n+")) if text else None,
                                  len(data), "added", cfg)
    if problems:
        print("Not shipped:\n" + "\n".join("  " + p for p in problems))
        return 1
    run("git", "fetch", "origin", "main")
    branch = f"ship/{me}-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    # the ship branch starts from the newest main, so what you send never undoes anyone else's work; your folder's
    # changes come along (only you change your folder, so they never clash with main)
    r = subprocess.run(["git", "switch", "-c", branch, "origin/main"], capture_output=True, text=True, cwd=ROOT)
    if r.returncode != 0:
        print("Couldn't start from the newest version: run Get latest (python tools/ch.py sync) first, then ship again.")
        return 1
    run("git", "add", "--", f"members/{me}/")
    msg = a.message or f"{me}: update my folder"
    run("git", "commit", "-s", "-m", msg)
    run("git", "push", "-u", "origin", branch)
    url = run("gh", "pr", "create", "--base", "main", "--head", branch, "--title", msg,
              "--body", f"Shipped from members/{me}/ with tools/ch.py ship.")
    print(f"Sent: {url}\nThe guard checks it and merges it by itself. Waiting for that (up to 3 minutes)…")
    for _ in range(36):
        time.sleep(5)
        state = run("gh", "pr", "view", url, "--json", "state", "--jq", ".state", check=False)
        if state == "MERGED":
            sync_main()
            print(f"SHIPPED: merged into main, and this folder is up to date with everyone's work.")
            return 0
        if state == "CLOSED":
            print("The pull request was closed without merging. Open it to see why.")
            return 1
    print("Still being checked. Your work is safe on its own branch; run Get latest in a few minutes to come back to main.")
    return 0


def sync_main() -> None:
    """Come back to main with everyone's newest work, keeping anything you haven't shipped yet."""
    run("git", "fetch", "origin", "main")
    here = run("git", "branch", "--show-current", check=False)
    dirty = bool(run("git", "status", "--porcelain", check=False))
    if dirty:
        run("git", "stash", "push", "-u", "-m", "commonhold-sync")
    if here != "main":
        run("git", "switch", "main")
    r = subprocess.run(["git", "merge", "--ff-only", "origin/main"], capture_output=True, text=True, cwd=ROOT)
    if r.returncode != 0:
        # local commits on main that never went anywhere: keep them on a side branch, then take main as it is
        side = f"kept/{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}"
        run("git", "branch", side)
        run("git", "reset", "--hard", "origin/main")
        print(f"Your own unsent commits on main were kept on the branch {side}.")
    if here.startswith("ship/"):
        run("git", "branch", "-D", here, check=False)
    for old in run("git", "branch", "--list", "ship/*", "--merged", "main", check=False).split():
        if old != "*":
            run("git", "branch", "-D", old, check=False)
    if dirty:
        r = subprocess.run(["git", "stash", "pop"], capture_output=True, text=True, cwd=ROOT)
        if r.returncode != 0:
            print("Your unshipped changes are kept in the stash (git stash list): they overlap something new on main.")


def cmd_sync(a) -> int:
    sync_main()
    print("UP TO DATE: you have everyone's newest work. Your unshipped changes are still here.")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("guard"); g.add_argument("--pr", required=True); g.add_argument("--repo")
    r = sub.add_parser("render"); r.add_argument("--root")
    s = sub.add_parser("ship"); s.add_argument("-m", "--message")
    c = sub.add_parser("check"); c.add_argument("--base", default="HEAD")
    sub.add_parser("sync")
    a = ap.parse_args(argv)
    return {"guard": cmd_guard, "render": cmd_render, "ship": cmd_ship, "check": cmd_check, "sync": cmd_sync}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
