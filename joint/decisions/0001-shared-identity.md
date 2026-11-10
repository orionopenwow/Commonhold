---
title: One identity shared with mod-p2p
status: proposed
proposed_by: orion
date: 2026-11-10
---
# One identity shared with mod-p2p

## What we decide
Commonhold uses mod-p2p's Ed25519 account key and character-ID derivation, so one player key works for live play
and for visits and passports. Per-world visit keys are derived from it, so a player can't be tracked across worlds
by one public key.

## Why
Two identity formats would split the community into two keys, two modules and two sets of tools.

## Open questions for the identity steward (IS4)
- Can a per-world key be derived without changing mod-p2p's character IDs?
- Shared test vectors: where do they live, and who signs them?
