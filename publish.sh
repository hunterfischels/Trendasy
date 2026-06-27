#!/usr/bin/env bash
# Publish this project to a target git repository, preserving local history.
#
# Usage:
#   ./publish.sh <remote-url> [branch]
#
# Example:
#   ./publish.sh https://github.com/hunterfischels/Trendasy.git main
#
# This pushes the *current* repository's HEAD to <branch> on <remote-url>.
# It is intended to be run from the root of the Trendasy project.
set -euo pipefail

REMOTE_URL="${1:-}"
BRANCH="${2:-main}"

if [[ -z "${REMOTE_URL}" ]]; then
  echo "usage: $0 <remote-url> [branch]" >&2
  exit 64
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: not inside a git work tree" >&2
  exit 1
fi

echo "Publishing $(git rev-parse --short HEAD) to ${REMOTE_URL} (${BRANCH})"

# Use a throwaway remote name so we don't clobber an existing 'origin'.
TMP_REMOTE="_publish_target"
git remote remove "${TMP_REMOTE}" 2>/dev/null || true
git remote add "${TMP_REMOTE}" "${REMOTE_URL}"

# Push current HEAD to the target branch. Add --force if the target already
# has unrelated history you intend to replace.
git push "${TMP_REMOTE}" "HEAD:${BRANCH}"

git remote remove "${TMP_REMOTE}"
echo "Done. Enable Pages: Settings → Pages → Source = GitHub Actions."
