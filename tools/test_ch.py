"""Tests for tools/ch.py: folder rules, file and secret checks, the living README, credits and the chronicle."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import ch  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CFG = ch.load_config(ROOT)
MEMBERS = ch.load_members(ROOT)


def kinds(paths, author):
    return sorted((n.kind, n.approvers_needed, tuple(sorted(n.must_include)))
                  for n in ch.needs_for(paths, author, MEMBERS, CFG))


def test_own_folder_needs_nothing_and_merges_itself():
    needs = ch.needs_for(["members/orion/notes.md", "members/orion/x/y.py"], "orion", MEMBERS, CFG)
    assert [n.kind for n in needs] == ["own"]
    assert all(ok for _, ok, _ in ch.check_needs(needs, set()))


def test_someone_elses_folder_needs_their_approval():
    needs = ch.needs_for(["members/is4/notes.md"], "orion", MEMBERS, CFG)
    assert not ch.check_needs(needs, {"maweu", "wrekczar"})[0][1]
    assert ch.check_needs(needs, {"is4"})[0][1]


def test_joint_needs_two_and_spec_needs_three_with_steward():
    assert kinds(["joint/roadmap.yml"], "orion") == [("joint", 2, ())]
    needs = ch.needs_for(["spec/identity.md"], "orion", MEMBERS, CFG)
    assert needs[0].must_include == {"is4"} and needs[0].approvers_needed == 3
    assert not ch.check_needs(needs, {"maweu", "wrekczar", "orion"})[0][1]   # steward missing
    assert ch.check_needs(needs, {"maweu", "wrekczar", "is4"})[0][1]


def test_steward_editing_own_section_still_needs_three_others():
    needs = ch.needs_for(["spec/identity.md"], "is4", MEMBERS, CFG)
    assert needs[0].must_include == set()
    assert not ch.check_needs(needs, {"orion", "maweu"})[0][1]


def test_core_and_generated_and_new_member():
    assert kinds([".github/workflows/guard.yml"], "orion") == [("core", 2, ())]
    assert kinds(["CREDITS.md"], "orion") == [("blocked", 0, ())]
    assert kinds(["members/newperson/member.yml"], None) == [("joint", 2, ())]


def test_mixed_pr_is_not_own_only():
    needs = ch.needs_for(["members/orion/a.md", "wiki/FAQ.md"], "orion", MEMBERS, CFG)
    assert {n.kind for n in needs} == {"own", "joint"}


def test_game_files_and_binaries_blocked():
    assert ch.scan_file("members/orion/patch-A.MPQ", None, 10, "added", CFG)
    assert ch.scan_file("members/orion/Spell.dbc", None, 10, "added", CFG)
    assert ch.scan_file("members/orion/tool.exe", None, 10, "added", CFG)
    assert ch.scan_file("members/orion/blob.xyz", None, 10, "added", CFG)
    assert not ch.scan_file("members/orion/shot.png", None, 1000, "added", CFG)
    assert ch.scan_file("members/orion/huge.png", None, 5_000_000, "added", CFG)
    assert not ch.scan_file("members/orion/old.mpq", None, 10, "removed", CFG)


def test_secrets_found_only_in_added_lines():
    tok = "ghp_" + "a" * 36
    assert ch.scan_file("x.md", f"+token = {tok}\n", None, "modified", CFG)
    assert not ch.scan_file("x.md", f"-token = {tok}\n", None, "modified", CFG)
    key = "-----BEGIN OPENSSH " + "PRIVATE KEY-----"
    assert ch.scan_file("k.txt", "+" + key, None, "added", CFG)


def test_dco():
    assert ch.dco_problems([{"sha": "abc1234", "commit": {"message": "x\n\nSigned-off-by: A <a@b>"}}]) == []
    assert ch.dco_problems([{"sha": "abc1234", "commit": {"message": "no sign"}}])


def test_latest_review_wins_and_author_ignored():
    members = {"a": {"github": "A"}, "b": {"github": "B"}}
    reviews = [{"user": {"login": "B"}, "state": "APPROVED"}, {"user": {"login": "B"}, "state": "CHANGES_REQUESTED"},
               {"user": {"login": "A"}, "state": "APPROVED"}, {"user": {"login": "stranger"}, "state": "APPROVED"}]
    assert ch.latest_approvals(reviews, "A", members) == set()


def test_replace_section():
    t = "x\n<!-- ch:a:start -->\nold\n<!-- ch:a:end -->\ny"
    assert ch.replace_section(t, "a", "new") == "x\n<!-- ch:a:start -->\nnew\n<!-- ch:a:end -->\ny"
    assert ch.replace_section("nothing", "a", "new") == "nothing"


def test_render_end_to_end(tmp_path):
    work = tmp_path / "repo"
    shutil.copytree(ROOT, work, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
    g = lambda *a: subprocess.run(["git", "-C", str(work), *a], check=True, capture_output=True)
    g("init", "-q", "-b", "main")
    g("add", "-A")
    g("-c", "user.name=Orion", "-c", "user.email=1+orionopenwow@users.noreply.github.com", "commit", "-q", "-m", "start")
    # finish a milestone and accept a decision: the chronicle must pick both up, once
    rm = (work / "joint" / "roadmap.yml")
    rm.write_text(rm.read_text().replace("status: doing", "status: done, done_on: 2026-11-11"))
    dec = work / "joint" / "decisions" / "0003-folders-and-shipping.md"
    dec.write_text(dec.read_text().replace("status: proposed", "status: accepted"))
    assert ch.main(["render", "--root", str(work)]) == 0
    assert ch.main(["render", "--root", str(work)]) == 0
    readme = (work / "README.md").read_text()
    assert "**Orion**" in readme and "Day **" in readme and "Identity and keys" in readme
    chron = (work / "joint" / "chronicle.md").read_text()
    assert chron.count("milestone:found") == 1 and chron.count("decision:0003") == 1
    st = json.loads((work / "site" / "status.json").read_text())
    orion = next(m for m in st["members"] if m["handle"] == "orion")
    assert orion["credit"]["commits"] == 1
    assert "@orionopenwow" in (work / "CODEOWNERS").read_text()
    assert "# Credits" in (work / "CREDITS.md").read_text()
