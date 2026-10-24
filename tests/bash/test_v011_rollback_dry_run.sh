#!/usr/bin/env bash
# Regression (v0.1.1, FR-PTCH-RBK-002, CR-FR-02): `rollback --dry-run` must not
# change any file named in the manifest and must not run any command.
# shellcheck source=tests/bash/lib.sh
. "$(dirname "$0")/lib.sh"
need_root
reexec_in_mount_ns "$@"

T=$(new_tmp); trap 'rm -rf "$T"' EXIT
[ -n "${QP_KEEP:-}" ] && trap - EXIT
F=$T/fx                        # fixture "server"
STUB=$T/stub; CALLS=$T/calls; : >"$CALLS"
mkdir -p "$F/proj" "$F/conf.d" "$F/node/bin" "$F/node/lib/node_modules/npm" "$STUB"

# Recording stubs: any call is logged; cp/rm/tar/mv also run for real.
for c in composer npm systemctl pm2 docker apachectl httpd pkill runuser; do
  printf '#!/bin/sh\necho "%s $*" >>"%s"\n' "$c" "$CALLS" >"$STUB/$c"
done
for c in cp rm tar mv; do
  printf '#!/bin/sh\necho "%s $*" >>"%s"\nexec %s "$@"\n' "$c" "$CALLS" "$(command -v $c)" >"$STUB/$c"
done
chmod +x "$STUB"/*

# State of the server after a "fix" run ...
echo '{"require":{"a/b":"^2.0"}}' >"$F/proj/composer.json"
echo '{"dependencies":{"x":"2.0.0"}}' >"$F/proj/package.json"
echo 'session.upload_progress.enabled = 0' >"$F/conf.d/zz-php-quickpatch-mitigation.ini"
printf '#!/bin/sh\necho v22.23.4\n' >"$F/node/bin/node"; chmod +x "$F/node/bin/node"

# ... and the backup it left behind (same layout as ensure_backup_dir).
SD=/var/lib/php-quickpatch; RUN=20261021-120000; B=$SD/backups/$RUN
mkdir -m 0750 "$SD"; mkdir -p "$B/files$F/proj"
echo '{"require":{"a/b":"^1.0"}}' >"$B/files$F/proj/composer.json"
echo '{"dependencies":{"x":"1.0.0"}}' >"$B/files$F/proj/package.json"
mkdir -p "$T/oldnode/bin"; printf '#!/bin/sh\necho v22.1.0\n' >"$T/oldnode/bin/node"; chmod +x "$T/oldnode/bin/node"
tar -czf "$B/node-old.tar.gz" -C "$T/oldnode" bin
{
  printf 'composer-install\t%s\n' "$F/proj"
  printf 'copy\t%s\t%s\n' "$F/proj/composer.json" "$B/files$F/proj/composer.json"
  printf 'npm-ci\t%s\n' "$F/proj"
  printf 'copy\t%s\t%s\n' "$F/proj/package.json" "$B/files$F/proj/package.json"
  printf 'created\t%s\n' "$F/conf.d/zz-php-quickpatch-mitigation.ini"
  printf 'note\t%s\n' "apt upgraded: php8.3 (packages are not downgraded by rollback)"
  printf 'untar\t%s\t%s\n' "$B/node-old.tar.gz" "$F/node"
} >"$B/manifest"
chmod 0600 "$B/manifest"

run_qp() { PATH="$STUB:$PATH" TMPDIR=$T bash "$QP" "$@" 2>&1; }

before=$(fingerprint "$F" "$B")
out=$(run_qp rollback "$RUN" --dry-run); rc=$?
after=$(fingerprint "$F" "$B")

assert_eq "dry-run exits 0" "$rc" 0
assert_eq "dry-run: SHA-256/mtime of every fixture and backup file unchanged" "$after" "$before"
check "dry-run: mitigation file named by 'created' still exists" test -f "$F/conf.d/zz-php-quickpatch-mitigation.ini"
# Read-only probes (docker info, pm2 pid) are allowed; anything else is not.
assert_eq "dry-run: no changing command run (composer/npm/systemctl/pm2/docker/cp/tar/mv)" \
  "$(grep -E '^(composer|npm|systemctl|pm2|docker|apachectl|httpd|pkill|runuser|cp|tar|mv) ' "$CALLS" | grep -vE '^(docker info|pm2 pid)$' | wc -l)" 0
assert_eq "dry-run: rm never touches the fixture" "$(grep -c "^rm .*$F" "$CALLS")" 0
assert_eq "dry-run: one [dry-run] line per replayable manifest line" \
  "$(grep -cE '^ +\[dry-run\] (copy|created|untar|composer-install|npm-ci) ' <<<"$out")" 6
assert_contains "dry-run: prints the copy it would do" "$out" "[dry-run] copy $F/proj/composer.json $B/files$F/proj/composer.json"
assert_contains "dry-run: notes are still shown" "$out" "apt upgraded: php8.3"
assert_contains "dry-run: says nothing changed" "$out" "Dry-run: nothing was changed."

# The same manifest without --dry-run still restores everything.
: >"$CALLS"
out=$(run_qp rollback "$RUN"); rc=$?
assert_eq "real rollback exits 0" "$rc" 0
assert_eq "real rollback restores composer.json" "$(cat "$F/proj/composer.json")" '{"require":{"a/b":"^1.0"}}'
assert_eq "real rollback restores package.json" "$(cat "$F/proj/package.json")" '{"dependencies":{"x":"1.0.0"}}'
check "real rollback removes the created mitigation file" test ! -e "$F/conf.d/zz-php-quickpatch-mitigation.ini"
assert_eq "real rollback restores the Node.js tarball" "$("$F/node/bin/node")" "v22.1.0"
check "real rollback runs composer install" grep -q '^composer install' "$CALLS"
check "real rollback runs npm ci" grep -q '^npm ci' "$CALLS"
# Manifest is replayed in reverse: restores happen before the reinstall steps.
order=$(grep -nE '^(cp|composer|npm) ' "$CALLS" | cut -d: -f2 | awk '{print $1}' | tr '\n' ' ')
assert_eq "real rollback order: cp package.json, npm ci, cp composer.json, composer install" "$order" "cp npm cp composer "

# Malformed IDs never reach the filesystem.
out=$(run_qp rollback ../../etc --dry-run); rc=$?
assert_eq "rollback with a path-like ID exits 2" "$rc" 2

t_done
