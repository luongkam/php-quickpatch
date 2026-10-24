"""Online data layer of php-quickpatch (DOC-SRS-QP-FEED-001..003).

sources  - catalog of SRC-001..017 and their settings
http     - HTTPS client (retry, rate limit, conditional GET)
store    - feeds/ directory (raw, parts, state)
collect  - one adapter per source: response -> facts
sync     - one `feeds update` run (FR-FEED-SYNC-001)
normalize- facts -> normalized model, min_patched (DOC-SRS-QP-FEED-002)
risk     - lifecycle_status, priority, risk score R (DOC-SRS-QP-FEED-002 §8)
bundle   - bundle files, atomic swap, readers (DOC-SRS-QP-FEED-003 §2.5, §3)
snapshot - offline snapshot export/import/packaged (DOC-SRS-QP-FEED-003 §4)
schedule - systemd timer / cron (DOC-SRS-QP-FEED-003 §5.2)
osv      - OSV lookups for libraries and distro backports (SRC-007, SRC-014..016)
"""
