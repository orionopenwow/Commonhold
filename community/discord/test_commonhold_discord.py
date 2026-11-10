"""Tests for commonhold_discord.py with a fake Discord: the plan, names, read-only channels, idempotent posts."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import commonhold_discord as cd  # noqa: E402


class Fake:
    def __init__(self, channels=None):
        self.channels = channels or []
        self.roles = [{"id": "g1", "name": "@everyone"}]
        self.msgs = {}
        self.log = []
        self.n = 100

    def call(self, method, path, body=None):
        self.log.append((method, path, body))
        if path == "/users/@me":
            return {"id": "bot"}
        if path == "/guilds/g1/channels" and method == "GET":
            return [dict(c) for c in self.channels]
        if path == "/guilds/g1/roles" and method == "GET":
            return self.roles
        if path == "/guilds/g1/roles":
            self.roles.append({"id": str(self.n), "name": body["name"]}); self.n += 1; return self.roles[-1]
        if path == "/guilds/g1/channels":
            self.n += 1
            c = dict(body, id=str(self.n)); self.channels.append(c); return c
        if method == "PATCH" and path.startswith("/channels/"):
            cid = path.split("/")[2]
            for c in self.channels:
                if c["id"] == cid:
                    c.update({k: v for k, v in body.items()})
            return {}
        if path.endswith("/messages?limit=50"):
            return self.msgs.get(path.split("/")[2], [])
        if path.endswith("/messages"):
            cid = path.split("/")[2]
            m = {"id": "m" + cid, "author": {"id": "bot"}, "content": body["content"]}
            self.msgs.setdefault(cid, []).append(m); return m
        if "/pins/" in path:
            return None
        raise AssertionError(path)


def run(fake, repo=""):
    d = cd.Discord("x"); d.call = fake.call
    cd.ensure(d, "g1", repo, True)


def test_names_and_bare():
    assert cd.chan_name("💬", "general", cd.TEXT) == "💬︱general"
    assert cd.chan_name("🎙️", "dev call", cd.VOICE) == "🎙️︱dev call"
    assert cd.bare("💬︱general") == "general" and cd.bare("#general") == "general" and cd.bare("◆┃General") == "general"


def test_fresh_server_gets_everything_once():
    f = Fake()
    run(f, repo="https://github.com/commonhold/commonhold")
    names = [c["name"] for c in f.channels]
    assert names == ["🧭︱start here", "👋︱welcome", "📢︱announcements", "🛠️︱build", "💬︱general", "📜︱spec",
                     "⚙️︱dev", "🐞︱help", "🚀︱ships", "🎙️︱dev call"]
    ro = {c["name"] for c in f.channels if c.get("permission_overwrites")}
    assert ro == {"👋︱welcome", "📢︱announcements", "🚀︱ships"}
    assert {r["name"] for r in f.roles} >= {"Builder", "Steward"}
    posts = sum(len(v) for v in f.msgs.values())
    assert posts == 7                           # every text channel, not the voice channel
    welcome = next(c for c in f.channels if c["name"] == "👋︱welcome")
    assert "https://github.com/commonhold/commonhold" in f.msgs[welcome["id"]][0]["content"]
    # twice: nothing new made or posted
    before = len(f.channels)
    run(f)
    assert len(f.channels) == before and sum(len(v) for v in f.msgs.values()) == 7


def test_existing_channel_kept_and_renamed():
    f = Fake([{"id": "5", "name": "general", "type": cd.TEXT}])
    run(f)
    assert sum(1 for c in f.channels if cd.bare(c["name"]) == "general") == 1
    assert next(c for c in f.channels if c["id"] == "5")["name"] == "💬︱general"


def test_no_repo_line_when_not_given():
    f = Fake()
    run(f)
    welcome = next(c for c in f.channels if c["name"] == "👋︱welcome")
    assert "Repo:" not in f.msgs[welcome["id"]][0]["content"] and "{repo}" not in f.msgs[welcome["id"]][0]["content"]
