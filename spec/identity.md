# Identity and keys

Steward: IS4 · Status: draft (v0.1) · Depends on: [records](records.md)

One person is one key. There are no accounts, emails or passwords on the network: a key made on the player's own PC
is the identity, and everything about that player is a record signed by it.

## 1. The player key (live in Leyline)

- **Algorithm:** Ed25519.
- **Storage:** the 32-byte seed is kept as 64 hex characters in a file on the player's PC (Leyline: `peer.key` in
  its app data folder). It is owner-only where the OS allows, and never sent anywhere.
- **Id:** the key id from [records §3](records.md#3-key-ids): `base32(sha256(public_key))[0:16]`.
- **Friend code:** the public key, which is all anyone needs to write to that player.

## 2. Writing to a player (live in Leyline)

Messages are sealed to the recipient's public key:
1. The recipient's Ed25519 key is converted to X25519 with the standard birational map, the same as libsodium's
   `crypto_sign_ed25519_pk_to_curve25519`.
2. Each message uses a fresh ephemeral X25519 key.
3. The shared secret goes through HKDF-SHA256 with the info string `leyline-friends-seal-v1`.
4. The message is encrypted with ChaCha20-Poly1305.

The envelope shows only the recipient's id. A sealed message is signed by the sender before sealing, is good for 10
minutes, and each nonce is accepted once.

## 3. Proving it's you (live in Leyline)

To prove who you are when joining a world, the host sends a fresh challenge (`leyline-join-v1`, good for 120
seconds). The joiner signs it with their player key. The host checks the signature, and that the key's id is one it
accepts, for example a friend's. Leyline uses this for lasting logins on a friend's single player world.

## 4. Characters bound to the key (to write, with the passport steward)

- A character's id is derived from the player key, so a passport can only ever belong to one identity.
- **Proposal:** follow mod-p2p's derivation, `SHA-256("p2p character" || account public key || nonce)[0:16]`, so
  the same character has the same id in live play (mod-p2p) and on passports (Commonhold). **IS4 to confirm.**

## 5. Not trackable across worlds (to write)

One public key shown to every world would let anyone follow a player from world to world.

**Proposal:**
- **A visit key per world,** derived from the player key:
  `visit_seed = HKDF-SHA256(ikm = player seed, salt = world key id, info = "commonhold-visit-key-v1")`.
- **Each world sees a different key.** The home world and the player can prove the link when needed, for example on
  re-homing, with a record signed by both keys.
- **A public profile stays opt-in.**

## 6. Losing a key (to write)

- **Backups:** an encrypted export file made by the launcher, an optional encrypted copy on the home world, and a
  printed recovery code.
- **Re-binding:** a record signed by the home world that moves characters from the lost key to a new one. Guardian
  co-signing (two friends' keys) comes later.
- **More devices:** a second device joins by typing a one-time code shown on the first.

## 7. Compatibility with mod-p2p

| | mod-p2p | Leyline today | Spec proposal |
|---|---|---|---|
| Signing key | Ed25519 account key | Ed25519 peer key | Ed25519: the same key can serve both |
| Encryption | X25519 derived via HKDF, ChaCha20-Poly1305 | X25519 via the birational map, HKDF, ChaCha20-Poly1305 | Write down one derivation, with vectors for both |
| Character id | `SHA-256("p2p character" ‖ key ‖ nonce)[0:16]` | (none yet) | Adopt mod-p2p's |
| Certificates | Signed by the account key | Signed records with contexts | Records with contexts; a mod-p2p certificate maps onto one |

## To write

- [ ] Vectors: seed → public key → id → X25519 key, and a sealed message
- [ ] The character id, confirmed with IS4
- [ ] Visit-key derivation and the link record, with vectors
- [ ] Recovery and re-binding records
