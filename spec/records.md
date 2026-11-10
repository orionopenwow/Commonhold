# Signed records

Steward: Orion · Status: draft

Every record is canonical JSON, signed with Ed25519 by the key it is about, and carries `type`, `v` (spec version),
`key`, `seq` (grows with each update), `issued`, `expires` and `sig`. Relays store and forward records but never
change them. Newer `seq` replaces older; expired records are dropped. This is the model Leyline's mesh already runs
for realm, relay and block records.

## Record types
| type | signed by | purpose |
|---|---|---|
| `realm` | world key | realm card: name, versions, modules, rates, rules, tier, policy agreement |
| `relay` | relay key | a relay's address and capacity |
| `charter` | world key | visit rules: league, tiers, caps, what visitors may bring and take home |
| `away` | world key | a character is visiting elsewhere (locks the home copy) |
| `visit` | host key | signed account of a visit: gains, losses, clears, against passport v(n) |
| `witness` | waystation key | append-only entry: hash of passport v(n) |
| `closing` | world key | the world is shutting down gracefully; final passports issued |
| `block` | 2 of 3 council keys | a world or relay is delisted, with reason and expiry |

## To write
- [ ] Canonical JSON rules and signing contexts, with vectors
- [ ] Merge and expiry rules
- [ ] Size limits per type
