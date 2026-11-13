"""The reference record check against the shared test vector, plus tampering and a fresh signature."""
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import records  # noqa: E402

VECTOR = Path(__file__).resolve().parent.parent / "spec" / "vectors" / "records" / "mesh-vector.json"


def test_vector_checks_out():
    recs = json.loads(VECTOR.read_text(encoding="utf-8"))["records"]
    assert recs and all(records.check_record(r) == [] for r in recs)


def test_tampering_is_caught():
    rec = next(r for r in json.loads(VECTOR.read_text(encoding="utf-8"))["records"] if r["kind"] == "realm")
    t = copy.deepcopy(rec); t["beat"]["status"]["players"] += 1
    assert "realm: bad signature" in records.check_record(t)
    t = copy.deepcopy(rec); t["beat"]["realm_id"] = "aaaaaaaaaaaaaaaa"
    assert records.check_record(t)


def test_context_separates_record_types():
    seed = bytes(range(32))
    doc = {"v": 1, "name": "Hëro", "seq": 3}
    sig = records.sign(seed, doc, records.CONTEXTS["profile"])
    pub = records.public_of(seed).hex()
    assert records.verify(pub, doc, records.CONTEXTS["profile"], sig)
    assert not records.verify(pub, doc, records.CONTEXTS["friendship"], sig)   # same bytes, other purpose: refused
    assert records.canonical(doc) == '{"name":"Hëro","seq":3,"v":1}'.encode("utf-8")
