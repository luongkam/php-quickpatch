# shellcheck shell=bash disable=SC2034
# Shared helpers for the Bash test suites (no external test framework).
# Source it from a test file; call t_done at the end.

QP_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
QP=${QP_SCRIPT:-$QP_ROOT/php-quickpatch.sh}
QP_TEST_USER=${QP_TEST_USER:-nobody}   # unprivileged user that runs the tool
QP_OTHER_UID=${QP_OTHER_UID:-4242}     # "another local user" (numeric, need not exist)
T_PASS=0
T_FAIL=0

pass() { T_PASS=$((T_PASS + 1)); printf 'ok   - %s\n' "$*"; }
fail() { T_FAIL=$((T_FAIL + 1)); printf 'FAIL - %s\n' "$*"; }

# check DESC CMD...: pass when CMD succeeds.
check() { local d=$1; shift; if "$@"; then pass "$d"; else fail "$d"; fi; }

# assert_eq DESC ACTUAL EXPECTED
assert_eq() { if [ "$2" = "$3" ]; then pass "$1"; else fail "$1 (expected '$3', got '$2')"; fi; }

# assert_contains DESC HAYSTACK NEEDLE
assert_contains() { if [[ $2 == *"$3"* ]]; then pass "$1"; else fail "$1 (missing '$3')"; fi; }
assert_not_contains() { if [[ $2 != *"$3"* ]]; then pass "$1"; else fail "$1 (unexpected '$3')"; fi; }

# fingerprint PATH...: type, owner, mode, mtime and SHA-256 of every entry.
fingerprint() {
  find "$@" -printf '%p %y %U %m %T@ %l\n' 2>/dev/null | sort
  find "$@" -type f -exec sha256sum {} + 2>/dev/null | sort
}

need_root() { [ "$EUID" -eq 0 ] || { echo "# skip $(basename "$0"): needs root"; exit 0; }; }

# reexec_in_mount_ns: rerun this test file in a private mount namespace with a
# tmpfs over /var/lib, so /var/lib/php-quickpatch is private to the test.
reexec_in_mount_ns() {
  [ -n "${QP_IN_NS:-}" ] && return 0
  command -v unshare >/dev/null || { echo "# skip $(basename "$0"): unshare missing"; exit 0; }
  QP_IN_NS=1 exec unshare -m --propagation private bash -c 'mount -t tmpfs tmpfs /var/lib && exec bash "$0" "$@"' "$0" "$@"
}

# new_tmp: world-traversable scratch dir (sticky like /tmp), removed on exit.
new_tmp() {
  local d; d=$(mktemp -d) && chmod 1777 "$d" && echo "$d"
}

t_done() {
  printf '# %s: %d passed, %d failed\n' "$(basename "$0")" "$T_PASS" "$T_FAIL"
  [ "$T_FAIL" -eq 0 ]
}

# path_without DIR NAME...: fill DIR with symlinks to every command on the
# current PATH except NAME... and print DIR (simulates a host without them).
path_without() {
  local dir=$1 d f n skip; shift
  mkdir -p "$dir"
  local IFS=:
  for d in $PATH; do
    [ -d "$d" ] || continue
    for f in "$d"/*; do
      n=${f##*/}; skip=0
      for s in "$@"; do [ "$n" = "$s" ] && skip=1; done
      (( skip )) || [ -e "$dir/$n" ] || ln -s "$f" "$dir/$n"
    done
  done
  echo "$dir"
}

# json_get FILE EXPR: evaluate a Python expression on the parsed document d.
json_get() { python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print(eval(sys.argv[2]))' "$1" "$2"; }

# schema_ok FILE: validate a --json document against its published schema.
schema_ok() {
  python3 - "$1" "$QP_ROOT/share/php-quickpatch" <<'PY'
import json, sys
sys.path.insert(0, sys.argv[2])
from qplib import jsonschema_lite
doc = json.load(open(sys.argv[1]))
name = doc["schema"].split("/")[0][3:]
schema = json.load(open("%s/schemas/qp.%s.v1.schema.json" % (sys.argv[2], name)))
errs = jsonschema_lite.validate(doc, schema)
for e in errs[:10]: print(e)
sys.exit(1 if errs else 0)
PY
}
