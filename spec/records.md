# Signed records

Steward: Orion · Status: draft (v0.1) · Reference check: [`tools/records.py`](../tools/records.py) · Vectors: [`vectors/records/`](vectors/records/)

Everything on the network is a small JSON document signed by the key it's about. Relays store and pass records
along but can't change them: a node can leave records out, but it can't add, change or revive one. This is what the
Leyline launcher and host kit already run for realm listings, relays and blocks. It's written down here so any
implementation can do the same and produce the same bytes.

## 1. Canonical JSON

The bytes a signature covers are the document serialised with:
- keys sorted by Unicode code point, at every level;
- no whitespace: separators are `,` and `:`;
- UTF-8, with non-ASCII characters written as they are, not `\u` escaped;
- numbers as integers. Records MUST NOT carry floats.

In Python that's `json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")`.

## 2. Signatures

```
sig = hex( Ed25519_sign( secret, context + "\n" + canonical(document) ) )
```

- **The context** is a short versioned string naming what the signature is for, for example
  `wu-listing-heartbeat-v1`. The same document signed for one purpose MUST NOT verify for another, so a realm
  listing can never be replayed as a relay login.
- **The signature** is 128 lower-case hex characters, carried next to the document, never inside it.
- **Verifiers** MUST check every record on arrival, whoever sent it, and MUST drop anything forged, expired, or over
  its size limit.

## 3. Key ids

```
id = lower( base32( sha256( public_key ) ) )[0:16]
```

RFC 4648 base32, no padding. A record that names an id MUST carry the public key it comes from, and verifiers
MUST recompute the id, so nobody can claim another key's id.

## 4. Freshness and order

- `seq`: a number that grows with every new version of a record from the same key. The newest `seq` wins. Ties
  are settled by the smaller sha256 of the signature.
- `ts`: Unix seconds when signed. Verifiers allow 300 seconds of clock skew.
- `exp` or a per-type lifetime: expired records are dropped and never revived.

## 5. Record types

| Context | Signed by | Carries | Lifetime | Status |
|---|---|---|---|---|
| `wu-listing-heartbeat-v1` | world key | Realm card: `realm_id`, `pubkey`, `seq`, `ts`, `relay`, `record` (name, tagline, tags, build, region, max players, direct), `status` (online, players, bots, uptime) | 15 min | live in Leyline |
| `leyline-mesh-endpoint-v1` | relay key | Where a realm is reachable through that relay: ports, websocket | with its realm | live |
| `leyline-mesh-node-v1` | relay key | A relay: host, region, volunteer, capacity, load | refreshed | live |
| `leyline-mesh-block-v1` | pinned staff keys | A delisting, with reason and expiry | its expiry | live; becomes 2 of 3 council |
| `leyline-profile-v1` | player key | Profile card: name, status, a few worlds, mailbox relay | ≤ 30 days, ≤ 2 KB | live (Leyline friends) |
| `leyline-friendship-v1` | **both** player keys | `{a, b, ts}`, the two public keys sorted | until revoked | live |
| `leyline-friend-revoke-v1` | either player | Ends a friendship; kept 60 days so it can't be replayed | 60 days | live |
| `commonhold-charter-v1` | world key | Visit rules: league, tiers, caps, what may come and go | refreshed | to write |
| `commonhold-away-v1` | home world key | A character is visiting; the home copy is locked | until return | to write |
| `commonhold-visit-v1` | host world key | What happened on a visit, against passport v(n) | single use | to write |
| `commonhold-witness-v1` | waystation key | sha256 of passport v(n), append-only | permanent | to write |
| `commonhold-closing-v1` | world key | The world is closing; final passports issued | permanent | to write |

Existing Leyline contexts keep their names: renaming would break every listing already out there. New Commonhold
types use the `commonhold-` prefix.

## 6. Size limits

A record MUST stay under 2 KB, except a realm card with endpoints (8 KB) and a sealed message envelope (15 KB, under
the relay's 16 KB body limit).

## 7. Test vectors

`vectors/records/mesh-vector.json` holds a realm card (with a non-ASCII name, quotes and a newline in its fields),
its endpoint and a relay record, all signed. Every implementation MUST verify all of them, and MUST reject them
after any one byte of a document changes. `python tools/records.py verify spec/vectors/records/mesh-vector.json`
runs the reference check.

## To write

- [ ] Vectors for the friendship, profile and block types
- [ ] The `commonhold-*` types, with the passport steward (charter, away, visit) and the resilience steward
      (witness, closing)
- [ ] How a world's key is rotated without losing its history
