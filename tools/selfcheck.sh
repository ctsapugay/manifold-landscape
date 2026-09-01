#!/usr/bin/env bash
# External tripwire for the checker itself.
#
# validate.py hashes its own source into the baseline, so editing it shows as drift --
# but only to a validate.py that has not itself been replaced. A self-hashing checker
# cannot detect its own subversion. This script closes that gap from outside: it uses
# git ONLY (no repo Python) to compare the tools and governed files against the most
# recent APPROVED commit. It is deliberately short so you can audit it at a glance.
#
#     bash tools/selfcheck.sh
#
# Exit 0 = unchanged since the last approval. Exit 1 = something changed; read the diff
# before you trust validate.py's output.
set -euo pipefail
cd "$(dirname "$0")/.."

ref=$(git log --grep='APPROVED:' -n1 --format=%H 2>/dev/null || true)
if [ -z "$ref" ]; then
  echo "No APPROVED commit yet — governance has not engaged, nothing to compare."
  exit 0
fi

paths=(tools/ constraints/ goals/ governance/)
echo "Comparing working tree to last approved commit ${ref:0:12} ..."
if git diff --quiet "$ref" -- "${paths[@]}"; then
  echo "OK — tools and governed files are unchanged since the last approval."
  exit 0
fi

echo
echo "CHANGED since the last approval:"
git diff --stat "$ref" -- "${paths[@]}"
echo
echo "If you did not just approve a change, inspect it before trusting validate.py:"
echo "    git diff $ref -- tools/"
exit 1
