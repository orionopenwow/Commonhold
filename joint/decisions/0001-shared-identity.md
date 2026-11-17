---
title: One identity for live play and visits
status: proposed
proposed_by: orion
date: 2026-11-10
---
# One identity for live play and visits

## What we decide
Commonhold uses one Ed25519 player key and one character-ID derivation, so one player key works for live play
and for visits and passports. Per-world visit keys are derived from it, so a player can't be tracked across worlds
by one public key.

## Why
Two identity formats would split the community into two keys, two modules and two sets of tools.

## Open questions for the identity steward
- Can a per-world key be derived without changing character IDs?
- Shared test vectors: where do they live, and who signs them?
