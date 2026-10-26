"""Data age and freshness (BR-FEED-005, FR-FEED-AGE-001) and `feeds status` (FR-FEED-CMD-002)."""
import time

from . import sources
from .store import parse_iso

LEVELS = ('FRESH', 'AGING', 'STALE', 'EXPIRED')
AGING_MAX_H = 168
STALE_MAX_H = 2160


def counted(src):
    """Sources whose age counts: scheduled ones, not the optional key-only SRC-013."""
    return src in sources.SCHEDULED and sources.SOURCES[src]['role'] != 'optional'


def source_level(age_h, ttl_h):
    if age_h is None:
        return None
    if age_h <= ttl_h:
        return 'FRESH'
    if age_h <= AGING_MAX_H:
        return 'AGING'
    if age_h <= STALE_MAX_H:
        return 'STALE'
    return 'EXPIRED'


def freshness(rows, now=None):
    """rows: manifest/sync-status source rows. -> (freshness, data_age_h, stale_sources, per_src_age)."""
    now = time.time() if now is None else now
    worst, oldest, stale, ages = None, None, [], {}
    for r in rows:
        src = r['src_id']
        if not counted(src) or r.get('status') == 'DISABLED' or not r.get('last_ok_at'):
            continue
        age_h = max(0, int((now - parse_iso(r['last_ok_at'])) // 3600))
        ages[src] = age_h
        ttl = int(r.get('ttl_h') or sources.SOURCES[src]['ttl_hours'])
        lvl = source_level(age_h, ttl)
        if worst is None or LEVELS.index(lvl) > LEVELS.index(worst):
            worst = lvl
        if oldest is None or age_h > oldest:
            oldest = age_h
        if age_h > ttl:
            stale.append({'src_id': src, 'age_h': age_h, 'last_error': r.get('last_error')})
    stale.sort(key=lambda s: -s['age_h'])
    return worst, oldest, stale, ages
