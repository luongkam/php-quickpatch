# Changelog

## 0.1.1 — 2026-10-24

Security fix release for `php-quickpatch.sh` v0.1.0. Two bugs were fixed;
both change behaviour on purpose.

### Fixed

- **`rollback --dry-run` changed real files.** `do_rollback` ran `cp -a`,
  `rm -f`, `tar -xzf`, `composer install` and `npm ci` without looking at
  `--dry-run`. Now every manifest step is only printed as
  `[dry-run] <action> <args>`; no file is changed and no service is restarted
  (service restarts are printed the same way). Basis: `FR-PTCH-RBK-002`,
  `CR-FR-02`.
- **Predictable, unchecked state directory.** v0.1.0 used `mkdir -p` and fell
  back to `${TMPDIR:-/tmp}/php-quickpatch-$EUID` for every user, root included,
  without checking symlinks, owner or mode. Another local user could create
  that directory first and plant a `manifest`; `rollback` then ran its lines
  with the privileges of whoever ran the tool. `STATE_DIR` is now chosen and
  checked as in spec §2.1 (`CR-SRS-13`, `NFR-SEC-010`, error
  `ERR-CLI-412-01`). Basis: `FR-CLI-ENV-001`, `FR-PTCH-RBK-002`.

### Behaviour changes compared with 0.1.0

| Situation | 0.1.0 | 0.1.1 |
| :--- | :--- | :--- |
| `rollback [ID] --dry-run` | Restored files, removed created files, unpacked Node.js tarballs, ran `composer install`/`npm ci`; only restarts were printed | Prints each step as `[dry-run] …`, ends with `Dry-run: nothing was changed.`; exit 0 |
| Root cannot create `/var/lib/php-quickpatch` (e.g. read-only FS) | Fell back to `/tmp/php-quickpatch-0` | Exits 2: `State directory … is unsafe (create_failed) [ERR-CLI-412-01]` |
| Primary state dir (`/var/lib/php-quickpatch` or `~/.php-quickpatch`) is a symlink, not a directory, owned by another user, or group/other-writable | Used as is | Exits 2 with `ERR-CLI-412-01` (`reason=symlink\|not_dir\|owner\|mode`); nothing is read or written there and there is no fallback |
| Primary state dir is safe but readable by others (e.g. `0755` made by 0.1.0) | Left as is | `chmod 0750` (root) / `0700` (other users), one warning line in the log |
| New state dir | `mkdir -p` with the umask (usually `0755`) | `mkdir -m 0750` (root) / `-m 0700` (other users), last component only |
| Non-root user with empty `HOME` | `/tmp/.php-quickpatch` | Fallback below |
| Non-root fallback | Fixed name `${TMPDIR:-/tmp}/php-quickpatch-$EUID`, created with `mkdir -p` | Newest safe directory among `${TMPDIR:-/tmp}/php-quickpatch-$EUID` (old name, so old runs can still be rolled back) and `…-$EUID.*`; unsafe candidates are skipped with a `[WARN]` line and left in place; otherwise `mktemp -d …-$EUID.XXXXXX` (mode `0700`) |
| `rollback [ID]` | Read any `backups/<ID>/manifest` that existed | `backups/<ID>/` must be a real directory and `manifest` a regular file, both owned by the current user and not group/other-writable; otherwise exit 2 with `ERR-CLI-412-01` before a single line is replayed |
| `rollback <ID>` with an ID that is not `YYYYmmdd-HHMMSS` | Joined into a path as is | Exits 2 (`Invalid rollback ID`) |
| `php-quickpatch.log` | Created with the umask | Created with mode `0600` |

`scan`, `fix`, their options, output format and exit codes are otherwise
unchanged.

### Tests

- `tests/bash/test_v011_rollback_dry_run.sh`: SHA-256 and mtime of every file
  named in a manifest (`copy`, `created`, `untar`, `composer-install`,
  `npm-ci`, `note`) are unchanged after `rollback --dry-run`, and no changing
  command runs; the same manifest without `--dry-run` still restores in the
  right order.
- `tests/bash/test_v011_state_dir.sh`: objects planted by another user (symlink,
  foreign owner, mode `0777`/`0666`, wrong type) at the primary path (root and
  non-root), at both fallback names, at `backups/<ID>/` and at `manifest`,
  for `scan`, `fix --dry-run` and `rollback`; root on a read-only filesystem.
- Run them with `sudo tests/run.sh` (they need root for `unshare -m`,
  `runuser` and `chown`).

## 0.1.0 — 2026-10-22

First release: `scan`, `fix`, `rollback` for PHP, Node.js, Composer, npm,
WordPress, Dockerfiles/compose files, running containers and webshell
indicators.
