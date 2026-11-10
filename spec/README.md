# The Commonhold specification

Game-neutral by design: it talks about characters, item entries, maps and quests, never about any brand. Every
section has a steward who must approve changes to it. Status lives in `status.yml`; the README and console show it.

Conventions for every section:
- **MUST / SHOULD / MAY** as in RFC 2119.
- Byte-exact tables for anything on the wire (mod-p2p's wiki is the bar).
- Every record type has test vectors in `spec/vectors/`, including tampered and replayed cases.
- Versions follow semver; two versions are supported at once, with deprecation one release ahead.
