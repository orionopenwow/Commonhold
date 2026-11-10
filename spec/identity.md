# Identity and keys

Steward: IS4 · Status: draft

## Goals
- One person, one root key (Ed25519), kept on the player's own PC and unlocked by a Hero Key or passphrase.
- **Compatible with mod-p2p:** the account key and character ID follow mod-p2p's identity format, so one key works
  for live play and for visits. See [mod-p2p: Identity and cryptography](https://github.com/Project-Eternal/mod-p2p/wiki/Identity-and-Cryptography).
- **Unlinkable by default:** a per-world visit key is derived from the root key for each world visited, so hosts
  can't track a player across worlds by one public key. A public profile is opt-in.
- **Recoverable:** an encrypted backup file, an optional encrypted copy on the home world, a printed recovery code,
  and re-binding signed by the home world. Guardian co-signing comes later.

## To write
- [ ] Key derivation for visit keys (domain-separated HKDF), with test vectors
- [ ] Binding a character to a key (mod-p2p's character-ID derivation)
- [ ] Device linking with a one-time code
- [ ] Recovery and re-binding records
