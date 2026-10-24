#!/usr/bin/env bash
# Run every test suite: Bash tests (tests/bash/test_*.sh) and, when present,
# Python unit tests (python3 -m unittest). Exit 1 if any suite fails.
cd "$(dirname "$0")/.." || exit 2
rc=0
for t in tests/bash/test_*.sh; do
  [ -e "$t" ] || continue
  echo "### $t"
  bash "$t" || rc=1
done
if [ -d tests/python ] && command -v python3 >/dev/null; then
  echo "### python3 -m unittest"
  python3 -m unittest discover -s tests/python -t . || rc=1
fi
exit $rc
