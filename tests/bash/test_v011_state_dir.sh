#!/usr/bin/env bash
# Regression (v0.1.1, spec §2.1, CR-SRS-13, NFR-SEC-010): STATE_DIR, its /tmp
# fallback and backups/<run_id>/manifest planted by another local user must
# make the tool exit 2 (ERR-CLI-412-01) or skip the candidate, and nothing may
# be written into them or executed from them.
# shellcheck source=tests/bash/lib.sh
. "$(dirname "$0")/lib.sh"
need_root
reexec_in_mount_ns "$@"

T=$(new_tmp); trap 'rm -rf "$T"' EXIT
OTHER=$QP_OTHER_UID
RUSER=$QP_TEST_USER; RUID=$(id -u "$RUSER")
PROJ=$T/proj; mkdir -p "$PROJ"           # empty project root: scans are no-ops
VICTIM=$T/victim; echo keep >"$VICTIM"   # a planted manifest tries to delete it
RUN=20261021-120000

# A fake manifest whose replay would delete $VICTIM.
plant_manifest() { # plant_manifest STATEDIR
  mkdir -p "$1/backups/$RUN"; printf 'created\t%s\n' "$VICTIM" >"$1/backups/$RUN/manifest"
}

# plant KIND PATH: create the object an attacker would leave at PATH.
#   other   - directory owned by another user (with a fake manifest)
#   symlink - symlink to a directory of another user
#   mode    - directory of the right owner but group/other writable (0777)
#   file    - a regular file where a directory is expected
plant() {
  local kind=$1 p=$2 owner=${3:-0}
  case $kind in
    other)   mkdir -p "$p"; plant_manifest "$p"; chown -R "$OTHER" "$p"; chmod 0755 "$p" ;;
    symlink) local d; d=$(mktemp -d "$T/attacker-XXXXXX")
             plant_manifest "$d"; chown -R "$OTHER" "$d"; ln -s "$d" "$p" ;;
    mode)    mkdir -p "$p"; plant_manifest "$p"; chown -R "$owner" "$p"; chmod 0777 "$p" ;;
    file)    echo x >"$p"; chown "$owner" "$p" ;;
  esac
}

expect_reason() { case $1 in other) echo owner ;; symlink) echo symlink ;; mode) echo mode ;; file) echo not_dir ;; esac; }

as_root() { TMPDIR=$T/tmp bash "$QP" "$@" --only webshell --path "$PROJ" 2>&1; }
as_user() { local home=$1; shift; runuser -u "$RUSER" -- env HOME="$home" TMPDIR=$T/tmp PATH="$PATH" bash "$QP" "$@" 2>&1; }
cmd_args() { case $1 in scan) echo scan ;; fix) echo "fix --dry-run" ;; rollback) echo "rollback $RUN" ;; esac; }

mkdir -m 1777 "$T/tmp"

# --- 1. root, primary path /var/lib/php-quickpatch -------------------------
P=/var/lib/php-quickpatch
for kind in other symlink mode file; do
  for cmd in scan fix rollback; do
    rm -rf "$P" "$T"/attacker-*; plant "$kind" "$P" 0
    before=$(fingerprint "$P" "$P/" "$VICTIM" "$T/tmp")
    # shellcheck disable=SC2046
    if [ "$cmd" = rollback ]; then out=$(TMPDIR=$T/tmp bash "$QP" rollback "$RUN" 2>&1); else out=$(as_root $(cmd_args "$cmd")); fi
    rc=$?
    after=$(fingerprint "$P" "$P/" "$VICTIM" "$T/tmp")
    assert_eq "root $kind@primary $cmd: exit 2" "$rc" 2
    assert_contains "root $kind@primary $cmd: ERR-CLI-412-01 reason=$(expect_reason "$kind")" "$out" "reason=$(expect_reason "$kind")"
    assert_eq "root $kind@primary $cmd: nothing written, manifest not run, no /tmp fallback" "$after" "$before"
  done
done

# --- 2. root on a read-only filesystem: no fallback ------------------------
rm -rf "$P" "$T"/attacker-*
mount -o remount,ro /var/lib
before=$(fingerprint "$T/tmp")
out=$(as_root scan); rc=$?
mount -o remount,rw /var/lib
assert_eq "root read-only /var/lib: exit 2" "$rc" 2
assert_contains "root read-only /var/lib: reason=create_failed" "$out" "reason=create_failed"
assert_eq "root read-only /var/lib: no fallback directory in TMPDIR" "$(fingerprint "$T/tmp")" "$before"

# --- 3. root, legitimate directories ----------------------------------------
rm -rf "$P"
out=$(as_root scan); rc=$?
check "root fresh: state dir created" test -d "$P"
assert_eq "root fresh: mode 0750" "$(stat -c %a "$P")" 750
chmod 0755 "$P"; out=$(as_root scan)
assert_eq "root v0.1-made 0755 dir: tightened to 0750" "$(stat -c %a "$P")" 750
check "root v0.1-made 0755 dir: warning in log" grep -q "tightened to 0750" "$P/php-quickpatch.log"

# --- 4. root, planted backups/<run_id>/ and manifest -------------------------
plant_run() { # plant_run KIND: legit STATE_DIR, unsafe run dir or manifest
  rm -rf "$P" "$T"/attacker-*; mkdir -m 0750 "$P"; mkdir -p "$P/backups"
  local r=$P/backups/$RUN
  case $1 in
    dir-other)    plant_manifest "$P"; chown -R "$OTHER" "$r" ;;
    dir-symlink)  plant symlink "$r" ;;
    dir-mode)     plant_manifest "$P"; chmod 0777 "$r" ;;
    dir-file)     echo x >"$r" ;;
    man-other)    plant_manifest "$P"; chown "$OTHER" "$r/manifest" ;;
    man-symlink)  mkdir -p "$r"; printf 'created\t%s\n' "$VICTIM" >"$T/evil-manifest"; chown "$OTHER" "$T/evil-manifest"; ln -s "$T/evil-manifest" "$r/manifest" ;;
    man-mode)     plant_manifest "$P"; chmod 0666 "$r/manifest" ;;
    man-dir)      mkdir -p "$r/manifest" ;;
  esac
}
for kind in dir-other dir-symlink dir-mode dir-file man-other man-symlink man-mode man-dir; do
  for args in "rollback $RUN" "rollback" "rollback $RUN --dry-run"; do
    plant_run "$kind"
    before=$(fingerprint "$VICTIM" "$P/backups")
    # shellcheck disable=SC2086
    out=$(TMPDIR=$T/tmp bash "$QP" $args 2>&1); rc=$?
    assert_eq "root $kind '$args': exit 2" "$rc" 2
    check "root $kind '$args': victim file untouched" test -f "$VICTIM"
    assert_eq "root $kind '$args': backups unchanged" "$(fingerprint "$VICTIM" "$P/backups")" "$before"
  done
done
plant_run man-mode; chmod 0600 "$P/backups/$RUN/manifest"
out=$(TMPDIR=$T/tmp bash "$QP" rollback "$RUN" --dry-run 2>&1); rc=$?
assert_eq "root safe run dir + manifest: dry-run accepted" "$rc" 0
assert_contains "root safe run dir + manifest: replay listed" "$out" "[dry-run] created $VICTIM"

# --- 5. non-root, primary path $HOME/.php-quickpatch ------------------------
H=$T/home; mkdir -p "$H"; chown "$RUID" "$H"
for kind in other symlink mode file; do
  for cmd in scan fix rollback; do
    rm -rf "$H/.php-quickpatch" "$T"/attacker-* "$T/tmp"/*; plant "$kind" "$H/.php-quickpatch" "$RUID"
    before=$(fingerprint "$H" "$H/.php-quickpatch/" "$VICTIM" "$T/tmp")
    # shellcheck disable=SC2046
    out=$(as_user "$H" $(cmd_args "$cmd") --only webshell --path "$PROJ"); rc=$?
    assert_eq "user $kind@primary $cmd: exit 2" "$rc" 2
    assert_contains "user $kind@primary $cmd: reason=$(expect_reason "$kind")" "$out" "reason=$(expect_reason "$kind")"
    assert_eq "user $kind@primary $cmd: nothing written, no fallback" "$(fingerprint "$H" "$H/.php-quickpatch/" "$VICTIM" "$T/tmp")" "$before"
  done
done
rm -rf "$H/.php-quickpatch"
out=$(as_user "$H" scan --only webshell --path "$PROJ")
assert_eq "user fresh: ~/.php-quickpatch mode 0700" "$(stat -c '%a %u' "$H/.php-quickpatch")" "700 $RUID"

# --- 6. non-root fallback (HOME empty): planted candidates are skipped -------
for name in "php-quickpatch-$RUID" "php-quickpatch-$RUID.AbC123"; do
  for kind in other symlink mode file; do
    for cmd in scan fix rollback; do
      rm -rf "$T/tmp"/* "$T"/attacker-*; plant "$kind" "$T/tmp/$name" "$RUID"
      before=$(fingerprint "$T/tmp/$name" "$T/tmp/$name/" "$VICTIM")
      # shellcheck disable=SC2046
      out=$(as_user "" $(cmd_args "$cmd") --only webshell --path "$PROJ"); rc=$?
      new=$(find "$T/tmp" -maxdepth 1 -name "php-quickpatch-$RUID.*" ! -name "${name##*/}" -user "$RUID" -perm 0700 | wc -l)
      assert_eq "user $kind@fallback $name $cmd: candidate skipped" "$(grep -c 'skipped unsafe state dir candidate' <<<"$out")" 1
      assert_eq "user $kind@fallback $name $cmd: fresh mktemp dir 0700 used" "$new" 1
      assert_eq "user $kind@fallback $name $cmd: planted object untouched, manifest not run" "$(fingerprint "$T/tmp/$name" "$T/tmp/$name/" "$VICTIM")" "$before"
      if [ "$cmd" = rollback ]; then assert_eq "user $kind@fallback $name rollback: exit 2 (no own backup)" "$rc" 2; fi
    done
  done
done

# --- 7. non-root fallback: own safe candidate is reused (newest mtime) -------
rm -rf "$T/tmp"/*
mkdir -m 0700 "$T/tmp/php-quickpatch-$RUID" "$T/tmp/php-quickpatch-$RUID.zzzzzz"
chown "$RUID" "$T/tmp/php-quickpatch-$RUID" "$T/tmp/php-quickpatch-$RUID.zzzzzz"
touch -d '2026-01-01' "$T/tmp/php-quickpatch-$RUID"
out=$(as_user "" scan --only webshell --path "$PROJ")
assert_contains "user fallback: newest own candidate reused" "$out" "log=$T/tmp/php-quickpatch-$RUID.zzzzzz/php-quickpatch.log"
assert_eq "user fallback: no extra directory created" "$(find "$T/tmp" -mindepth 1 -maxdepth 1 | wc -l)" 2

t_done
