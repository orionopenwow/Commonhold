---
title: Clean provenance for everything shared
status: proposed
proposed_by: orion
date: 2026-11-10
---
# Clean provenance for everything shared

## What we decide
Shared code, listings and links never include decompiled, recompiled or leaked clients or server sources. Shared code
targets stock AzerothCore, TrinityCore and CMaNGOS. A member's own folder may hold reference notes about other cores,
but nothing from those sources moves into `spec/`, `tools/` or any shared release.

## Why
Recent legal action against large servers makes provenance the network's best protection, and every host relies on it.

## Consequences
- The network never requires a modified client binary.
- Browser clients made by recompiling the original executable are not listed or linked.
