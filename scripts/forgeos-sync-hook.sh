#!/usr/bin/env bash
# ForgeOS graph-refresh hook (sample).
#
# Keeps the ForgeOS knowledge + code-intelligence graphs current after the working tree
# changes. Install as a git hook in your project, e.g.:
#
#   chmod +x scripts/forgeos-sync-hook.sh
#   ln -sf ../../scripts/forgeos-sync-hook.sh .git/hooks/post-merge
#   ln -sf ../../scripts/forgeos-sync-hook.sh .git/hooks/post-checkout
#
# Safe by design: no-ops if forgeos isn't installed or the project isn't initialized, and
# never fails the git operation. Note: avoid running while a forgeos MCP session holds the
# project's sqlite (prevents "database is locked").
set -u
command -v forgeos >/dev/null 2>&1 || exit 0
[ -d .forgeos ] || exit 0
forgeos sync >/dev/null 2>&1 || true
exit 0
