# Changelog

## 2.0.0-alpha.3 — 2026-10-24 (Phase 1, milestone M3)

Development build of v2 (not a release).

### Added
- Scenario catalog `share/php-quickpatch/catalog/` (`scenarios.json`,
  `checklists.json`, `playbooks.json`, `bc_rules.json`, `mitigations.json`,
  `framework_php.tsv`, `catalog.json`, `SHA256SUMS`): 28 scenarios and 623
  checklist items (399 PHP, 224 Node.js), generated from the scenario
  documents by `tools/build-catalog.py`. A newer valid catalog imported with
  a snapshot (`feeds/catalog`) replaces the packaged one; a catalog with a
  wrong SHA-256 (`ERR-FEED-422-02`) or missing keys (`ERR-FEED-502-02`) is
  never used. `catalog_version` is in every `--json` envelope (FR-SCN-CAT-001).
- `scan`: each runtime gets `scenario_ids` (one VERSION + OVERLAYs, BR-SCN-040
  for PHP from the raw `PHP_VERSION`, BR-SCN-020 for Node.js), `locked` and
  `lock_reason` for pre-release/abnormal versions (`ERR-SCN-422-01`; `fix`
  skips every change on them), `pb_id`, Node.js `apps[]` (systemd).
- `scan`: environment detection and playbooks (`environment.playbooks[]`,
  `pb_provider`, `pb_bindings`, `pb_node`, `evidence[]`, `restrictions[]`,
  PB-000 with `ERR-ENV-422-01`), site inventory `sites[]` for Nginx and Apache
  with PHP-FPM and Apache `mod_php` (`--only sites`; sites in files that no
  running server loads get `ERR-ENV-422-02`), `site_key`, `site_ids` of each
  runtime, `scan_fingerprint` over site bindings and runtime versions,
  `plan_deadlines[]` (EOL − 30 days), ranking reason codes of the CLI
  contract. The result is also saved to `state/last-scan.json`.
- `assess [--runtime-id ID | --bin PATH] [--candidates]` (`qp.assess/1`):
  current version (CVE counts, KEV, lifecycle, EOL, latest/min patch, R),
  advisories, candidates `SAME_BRANCH_LATEST`/`NEXT_SUPPORTED`/`RECOMMENDED`/
  `LATEST_STABLE` with `selectable` (BR-ASMT-002, BR-SCN-005/006/007) and
  `installable` (PB-001 via `apt-cache policy`), comparison rows (R, delta_R)
  on one bundle and one day.
- `plan create|list|show|approve|item|run|cancel|complete|close|canary|waive`
  (`qp.plan/1`): target checks (BR-UPG-004, BR-PLAN-001), effective checklist
  per site (OVERLAY first, `applies_when`, "(khi nâng)" sub-items, variables
  replaced), plan and item state machines (T-PLN-*, T-CHK-*), dependencies
  (`ERR-SCN-424-01`), stale plans (BR-PLAN-006), approval deadline, audit
  records and `events.jsonl` under `STATE_DIR/plans/<plan_id>/`.
- PHP pre-release builds of php.net collected with SRC-002 (`prerelease_url`).

### Changed
- Interim PHP mitigation follows `mitigations.json`: the file starts with
  `; qp-rules=<ids>; sha256=<body>`; a file written by the tool (or a v0.1
  file) is backed up and rewritten when the rules change, a file edited by
  hand is kept and reported (`high`) (FR-PTCH-MIT-001, CR-FR-07).
- `risk.components` uses `S_cvss`, `S_cnt`, `S_kev`, `S_life`, `S_eol` as
  numbers (plus `floor`, `R_raw`); `risk.score` added next to `risk.R`.
- Ranking reason codes: `KEV`, `CVSS_GE_9`, `EOL`, `CVSS_7_TO_8_9`,
  `EOL_LE_90D`, `OTHER`; same `R` sorts by `object_ref`.

## 2.0.0-alpha.2 — 2026-10-24 (Phase 1, milestone M2)

Development build of v2 (not a release).

### Added
- Online data layer `qp-feeds.py` (Python 3.6+, standard library only):
  collectors for SRC-001..016 (endoflife.date, php.net releases/ChangeLog/
  NEWS/eol.php, NVD 2.0 with paging and incremental `lastMod` windows,
  CVE.org, CISA KEV, OSV, GitHub advisories, nodejs.org index/schedule,
  Node.js Security WG, WordPress.org, optional Wordfence key), HTTPS only,
  TLS >= 1.2, retries 3x, `Retry-After`, rate limits, conditional GET,
  time budget, fallback chain with `data_origin` (FR-FEED-*).
- Normalized bundle `STATE_DIR/feeds/bundles/<bundle_id>/` (9 TSV files +
  `sources.tsv`, `feeds.db`, `manifest.json`, `SHA256SUMS`); `current` and
  `previous` symlinks switched with one `rename(2)`; readers hold a shared
  lock so a bundle in use is never removed (BR-FEED-051).
- Merge rules, `min_patched` per branch, temporary advisories for security
  releases without CVE details, distro backport chain (OSV distro, Ubuntu/
  Red Hat trackers, local changelog), risk score R 0-100 computed in integer
  tenths in both Bash and Python (BR-FEED-020..031, 040..044).
- Commands `feeds update|status|verify|export|import|schedule` (aliases
  `sync`, `snapshot export|import`), each with `--json` (`qp.feeds.<sub>/1`).
  `import` and `schedule install|remove` are write commands: `--yes` or a
  TTY, `--dry-run`, audit records.
- Packaged snapshot support: `share/php-quickpatch/feeds-snapshot.tar.gz`
  pinned by `QP_SNAPSHOT_SHA256` is installed by Bash on first use, without
  Python (FR-FEED-SNAP-001). The snapshot itself ships with the release (M7).
- `scan --json`: `data` (bundle id, freshness, data age, stale sources),
  per-runtime `lifecycle_status`, `priority`, `eol_date`, `days_to_eol`,
  `min_patched`, `latest_patch`, `driver_ids`, `backport`, `risk`;
  `ranking[]`; dependency findings with severity, KEV flag and fixed
  versions; WordPress findings with advisories and risk.

### Changed (compared with 2.0.0-alpha.1)
- The hard-coded `PHP_FIXED`, `PHP_CVES`, `NODE_FIXED`, `WP_FIXED` are gone:
  patched versions, CVE lists and EOL come from the bundle
  (FR-CLI-COMP-002). Text lines that named the 2026-10 data ("PHP2Shell",
  "wp2shell", "October 2026 security release") now name the CVEs, and issue
  severities follow the risk level (e.g. PHP 8.2.34 is HIGH, R=60).
- WordPress: 7.0.2 is no longer reported patched (CVE-2026-87902, in KEV);
  the patched versions are 6.9.10, 7.0.7 and 7.1.3 (BR-FEED-025).
- `scan`/`fix` refresh the data first (at most 120 s) when a source is older
  than its TTL, unless `--offline` (BR-FEED-001). With no bundle, no
  snapshot and no network, runtimes are `unknown` and the exit code is 2
  (ERR-FEED-503-01).
- With Python available, Composer/npm lookups go through `qp-feeds.py`
  (cache per lockfile SHA-256, stale cache up to 7 days when OSV fails);
  without Python the v0.1 `curl` lookup is kept.

## 2.0.0-alpha.1 — 2026-10-24 (Phase 1, milestone M1)

Development build of v2 (not a release). Base: 0.1.1.

### Added
- `--json` on `scan`, `fix`, `rollback`: one JSON document on stdout
  (envelope `qp.<command>/1` with `schema_version`), human text on stderr
  and in the log (FR-CLI-JSON-001). JSON is built in pure Bash: no `jq`,
  no Python needed for `scan`/`fix`/`rollback`.
- `schema <command>` and JSON Schema 2020-12 files in
  `share/php-quickpatch/schemas/` (FR-CLI-JSON-002).
- Inventory in `scan --json`: runtimes (`runtime_id`, SAPIs, extensions,
  owning package, install source, ABI, npm version), projects, running
  containers (with compose labels), dependency, WordPress and webshell
  findings (SHA-256, mtime, size) (FR-SCAN-RT/PRJ/WSH).
- Append-only audit log `STATE_DIR/audit/audit-YYYYMM.jsonl` with a SHA-256
  hash chain shared by Bash and Python; `audit list|verify` (Python 3.6+),
  anchors in `--json` of write commands (FR-JOB-AUD-001..003).
- Error codes `ERR-*` with English and Vietnamese messages
  (`QP_LANG=vi`), catalog generated from the SRS error matrix.
- `feeds`, `assess`, `plan`, `report`, `audit`, `serve` are dispatched to
  Python; without Python 3.6+ they stop with `ERR-CLI-424-01`.

### Changed (compared with 0.1.1)
- `scan` and every `--dry-run` take a shared lock: two scans can run at the
  same time; a `fix` still excludes them (BR-JOB-002, CR-SRS-06).
- Each fix run gets its own `backups/<run_id>/` created atomically; a
  second run in the same second waits for the next second, at most 10 tries
  (`ERR-PTCH-409-01`). A run needs 50 MiB free in `STATE_DIR`
  (`ERR-ENV-507-01`); `backups/` over 1 GiB prints a warning.
- After a restart, each service is checked for up to 15 s; a service that
  is not active makes `fix` exit 2 with `ERR-PTCH-500-01` (no automatic
  rollback). Remi `phpNN-php-fpm` units are now restarted; `ea-php`
  packages on dpkg (cPanel on Ubuntu) are now upgraded (CR-SRS-07).
- WordPress: core and the plugins about to be updated are backed up as
  tarballs (`untar` lines); rollback restores them. The `copy` of
  `version.php` alone is gone (it used to leave a mismatched core).
- Container mitigation: an existing file is never overwritten, and a
  `docker-created` manifest line lets rollback remove it.
- Rollback restarts Node.js only for `untar` lines whose target has
  `bin/node`; a failing manifest step is reported per line in `--json`.
- Runtime probes stop after 10 s; a binary or container that does not
  answer is reported (`ERR-SCN-422-01`) instead of hanging the scan.
- `QP_PHP_BINS`/`QP_NODE_BINS` paths are resolved through symlinks and
  `php-configX.Y` is ignored, so one runtime is listed once.
- The webshell scan reads PHP files below 2 MiB (0.1.x effectively stopped
  at 1 MiB because of `find -size` rounding).
- Unreadable PHP/Node versions are now printed as a `[WARN]` line.

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
