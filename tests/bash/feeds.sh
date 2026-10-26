# shellcheck shell=bash
# Feeds test helpers: a local HTTPS server with the fixtures of
# tests/fixtures/feeds (tests/fakesrv.py) and sources.conf pointing at it, so
# no test reaches the real sources.
# Usage: feeds_server_start; sources_conf DIR; fixture_bundle; feeds_server_stop

FEEDS_FIX=$QP_ROOT/tests/fixtures/feeds
QPF=$QP_ROOT/share/php-quickpatch/qp-feeds.py

feeds_server_start() {
  FEEDS_SRV=$(mktemp -d); chmod 755 "$FEEDS_SRV"
  python3 "$QP_ROOT/tests/fakesrv.py" "$FEEDS_FIX" "$FEEDS_SRV" >"$FEEDS_SRV/server.log" 2>&1 &
  FEEDS_PID=$!
  local _; for _ in $(seq 150); do [ -f "$FEEDS_SRV/port" ] && break; sleep 0.1; done
  FEEDS_PORT=$(cat "$FEEDS_SRV/port" 2>/dev/null)
  [ -n "$FEEDS_PORT" ] || { echo "# fake feeds server did not start"; cat "$FEEDS_SRV/server.log"; return 1; }
  chmod 644 "$FEEDS_SRV/ca.pem"; touch "$FEEDS_SRV/osv.vulns"; chmod 666 "$FEEDS_SRV/osv.vulns"
  export SSL_CERT_FILE="$FEEDS_SRV/ca.pem" NO_PROXY="127.0.0.1,localhost" no_proxy="127.0.0.1,localhost"
  FEEDS_BASE="https://127.0.0.1:$FEEDS_PORT"
}

feeds_server_stop() { [ -n "${FEEDS_PID:-}" ] && kill "$FEEDS_PID" 2>/dev/null; rm -rf "${FEEDS_SRV:-/nonexistent}"; }

# feeds_control JSON: script failures of the fake server (see tests/fakesrv.py).
feeds_control() { printf '%s\n' "$1" >"$FEEDS_SRV/control.json"; }
feeds_requests() { cat "$FEEDS_SRV/requests.log" 2>/dev/null; }

# sources_conf FEEDS_DIR [EXTRA_INI]: every source -> the fake server, no retry waits.
sources_conf() {
  local d=$1 b=$FEEDS_BASE s url mirror
  mkdir -p "$d"
  {
    for s in 001 002 003 004 005 006 007 008 009 010 011 012 013 014 015; do
      url="$b/SRC-$s"; mirror="$b/SRC-$s-mirror"
      case $s in
        006) url="$b/SRC-006/kev.json"; mirror="$b/SRC-006-mirror/kev.json" ;;
        009) url="$b/SRC-009/index.json" ;;
        010) url="$b/SRC-010/schedule.json" ;;
        011) url="$b/SRC-011/index.json" ;;
      esac
      printf '[SRC-%s]\nurl = %s\nmirror_url = %s\nretry_delays = 0,0,0\nmin_interval_s = 0\ntimeout_s = 10\n' "$s" "$url" "$mirror"
      [ "$s" = 002 ] && printf 'prerelease_url = %s\n' "$b/SRC-002/pre-release-builds.php?format=json"
    done
    [ -n "${2:-}" ] && printf '%s\n' "$2"
  } >"$d/sources.conf"
}

# fixture_bundle: build the fixture bundle in this test's STATE_DIR (root,
# /var/lib in the private mount namespace). Prints the bundle id.
fixture_bundle() {
  local sd=/var/lib/php-quickpatch
  mkdir -p "$sd/feeds"; chmod 0750 "$sd"; chmod 0755 "$sd/feeds"
  sources_conf "$sd/feeds"
  python3 -I "$QPF" --script "$QP" feeds update --quiet >/dev/null 2>"$FEEDS_SRV/fixture-update.err"
  basename "$(readlink "$sd/feeds/current")"
}
