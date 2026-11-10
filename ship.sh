#!/usr/bin/env sh
# Sends the changes in your own members/<you>/ folder. They merge by themselves once the guard check passes.
cd "$(dirname "$0")" && python3 tools/ch.py ship -m "${*:-update my folder}"
