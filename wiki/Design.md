# Design overview

The full design is being turned into the spec section by section. This page is the plain summary.

## Everything is a signed record
Small canonical-JSON objects signed with Ed25519 by the key they're about, with a sequence number and an expiry.
Relays pass them around without changing them. See [spec/records](../spec/records.md).

## A visit, step by step (copy, never move)
1. **Check:** compare the home charter with the destination charter; show a fit score with plain reasons.
2. **Depart:** home signs passport v(n) and locks the character with an `away` record. Customs splits what may go in
   from what stays in the home vault.
3. **Arrive:** the host rebuilds the character with fresh local IDs. Items it doesn't know become appearance-only
   stand-ins or stay in the vault; temporary rows are wiped when the visitor leaves.
4. **Play:** the host signs checkpoints, at least on logout.
5. **Return:** the host signs a visit record against v(n). Home compares the departure snapshot, its current state
   and the visit record, applies its caps, and the player approves. The result is v(n+1).
6. **No replays:** a visit record applies only to v(n), once.

## Shutdown resilience
The player always holds the latest passport. Waystations keep append-only fingerprints of each version. If a world
goes dark (missed heartbeats) or closes gracefully (a signed `closing` record), players can re-home anywhere that
accepts newcomers, and the new home checks the signature and the fingerprint.

## Rules across many worlds
Leagues, visit tiers (Story, Adventure, Full), gold that never travels, raid clears stamped on the passport, trust
that each world opts into, and listing tiers by criteria: Always-on, Community, Unlisted.

## Lessons from older networks
Virtual worlds that let avatars travel between independently run grids learned that items stop working when they
cross between different software, that fixes don't help until every host installs them, and that protecting
travellers from rogue hosts adds friction. Commonhold answers with namespaced item references and translation tables,
adapters that update themselves through launchers, and hosts that can only propose changes, never edit the home copy.
