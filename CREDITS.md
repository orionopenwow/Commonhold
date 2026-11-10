# Credits

Generated from `members/*/member.yml` and the project history. Edit your own `member.yml`
to change how you're credited. Every piece of Commonhold carries its author's name.

## Orion ([@orionopenwow](https://github.com/orionopenwow))

- **Brings:** Directory and realm cards, relays, one-click hosting and joining, the community workspace
- **Project:** [Leyline](https://leylinelauncher.com)
- **Steward of:** directory, relays
- **Worked on:** root (20), spec (11), .github (8), site (8), joint (8), community (7)
- **Commits:** 5
- **Contributed:**
  - Started Commonhold and this workspace; the Leyline launcher, host kit, relays and signed realm listings it builds on
  - The "unified network, nobody owns it" direction, the seeded big world, free and signed hosting for the record

## IS4

- **Brings:** Shared identity, live play across player-run servers (mod-p2p), spec quality
- **Project:** [Project Eternal mod-p2p](https://github.com/Project-Eternal/mod-p2p)
- **Steward of:** identity
- **Commits:** 0
- **Contributed:**
  - mod-p2p (Project Eternal): live play across player-run servers, with a byte-exact public spec
  - The identity Commonhold adopts: Ed25519 account keys, derived character IDs, signed certificates
  - Escrowed transfers between servers, the pattern behind the Customs Vault's design

## Maweu

- **Brings:** Shutdown resilience and backups, local tamper-proof passports, anti-selling, safety policy, fair listing
- **Steward of:** resilience, policy
- **Commits:** 0
- **Contributed:**
  - Shutdown resilience: characters that survive a server closing, migration and backups
  - Local, tamper-proof passports and selling characters made hard without invasive checks
  - The hosting safety policy, and fair listing ("Official looks like an ad")
  - Session worlds on a laptop with opt-in write-back; resilience as the reason people join

## Leon (Wrekczar)

- **Brings:** Character Passport, Customs Vault, three-way reconciliation, visit rules
- **Project:** Worlds of CoreCraft
- **Steward of:** passport, customs
- **Commits:** 0
- **Contributed:**
  - Worlds of CoreCraft, the project the visits idea comes from ("go over to a friend's house" with your own character)
  - The Character Passport, with the first working round trip between two servers
  - The Customs Vault, three-way reconciliation on return, temporary rows for visitors, federation lockouts
  - The hub-and-spoke design and "Keeping Things Practical" (auction house, gold, dupes)

## Thanks

People whose ideas and reports shaped Commonhold. Want a folder of your own? Open a dev request.

- **Akuma** (Discord): First host to hit and report the host kit's 'invalid reference format' error, which got it fixed for everyone
- **Squishy** (Discord): Reported that single player couldn't be picked in the server list, which led to both local worlds becoming proper rows
- **z… [BFLD]** (Discord): Asked whether this could be a fork of an existing core, which shaped the 'stock cores, open protocol' answer

## Built on and learned from

- [AzerothCore](https://github.com/azerothcore/azerothcore-wotlk): The open-source server core most worlds here run; the first passport adapter targets it
- [TrinityCore](https://github.com/TrinityCore/TrinityCore): Open-source server core; adapter planned
- [CMaNGOS](https://github.com/cmangos): Open-source server cores for the earlier eras; adapter planned
- [Project Eternal mod-p2p](https://github.com/Project-Eternal/mod-p2p): Live play between player-run servers; the shared identity format (by IS4)
- [Sigstore Rekor and Sigsum](https://docs.sigstore.dev/logging/overview/): Append-only transparency logs: the model for waystation witness logs
- [Nostr](https://nostrcg.github.io/devguide/protocol/overview): Signed events on simple relays: the closest model to the network's records
- [atproto (Bluesky)](https://atproto.com/blog/rpg-actor): Player-held character records checked by issuers: the same idea as passports and witnesses
- [iroh](https://pinggy.io/blog/iroh_1_0_dial_keys_not_ips/): Dial keys, not IPs: a candidate for direct links between nodes
- [OpenSimulator Hypergrid](https://hypergridbusiness.com/?p=51141): Years of avatars travelling between independent grids, and the lessons about items, patches and rogue hosts
- [All Contributors](https://allcontributors.org/docs/en/specification): Credit for every kind of contribution, not just code
