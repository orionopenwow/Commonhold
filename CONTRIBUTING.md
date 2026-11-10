# Contributing

Thanks for helping. The short version is in [wiki/How-to-join.md](wiki/How-to-join.md).

- **Sign off every commit** (`git commit -s`), certifying the [Developer Certificate of Origin](https://developercertificate.org/).
  `tools/ch.py ship` does this for you.
- **Licence:** contributions to shared folders are Apache-2.0 (inbound = outbound). Your own folder uses the licence
  in your `member.yml`.
- **AI help:** fine, but say so with a trailer such as `Assisted-by: <tool>`, and review what you ship. People approve
  every shared change.
- **Never commit:** game files (archives, databases, models, maps, textures), executables, private keys, tokens, or
  anything you don't have the right to share. The guard blocks the common cases; you're responsible for the rest.
- **Check before you push:** `python tools/ch.py check`.
