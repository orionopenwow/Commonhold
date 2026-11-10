#!/usr/bin/env sh
# Gets everyone's newest work. Anything you haven't shipped yet stays as it is.
cd "$(dirname "$0")" && python3 tools/ch.py sync
