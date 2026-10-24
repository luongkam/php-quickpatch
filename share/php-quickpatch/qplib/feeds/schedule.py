"""`feeds schedule install|remove|show` (FR-FEED-SCHD-001, DOC-SRS-QP-FEED-003 §5.2, BR-FEED-057).

systemd (root, /run/systemd/system present): php-quickpatch-feeds.service + .timer
cron (root, no systemd): /etc/cron.d/php-quickpatch-feeds
user (not root): one line in the user's crontab marked '# php-quickpatch-feeds'
At most one schedule exists; install updates it in place. The minute is
fixed per machine (hash of /etc/machine-id) so servers do not all call the
sources at :00.
"""
import hashlib
import os
import re
import shutil
import subprocess
import time

MARK = '# php-quickpatch-feeds'
UNIT = 'php-quickpatch-feeds'
SYSTEMD_DIR = '/etc/systemd/system'
CRON_FILE = '/etc/cron.d/php-quickpatch-feeds'
INTERVALS = (1, 2, 3, 4, 6, 8, 12, 24)


def kind():
    if os.geteuid() != 0:
        return 'crontab_user'
    if os.path.isdir('/run/systemd/system') and shutil.which('systemctl'):
        return 'systemd'
    return 'cron'


def machine_minute():
    for p in ('/etc/machine-id', '/var/lib/dbus/machine-id'):
        try:
            with open(p) as f:
                mid = f.read().strip()
            if mid:
                return int(hashlib.sha256(mid.encode()).hexdigest(), 16) % 60
        except OSError:
            pass
    return int(hashlib.sha256(os.uname().nodename.encode()).hexdigest(), 16) % 60


def _cron_hours(n):
    return '0' if n == 24 else '*/%d' % n


def render(k, script, n, minute):
    cmd = '%s feeds update --quiet' % script
    if k == 'systemd':
        hours = '00' if n == 24 else '00/%d' % n
        service = ('[Unit]\nDescription=php-quickpatch feeds update\nAfter=network-online.target\n'
                   'Wants=network-online.target\n\n[Service]\nType=oneshot\nExecStart=%s\n' % cmd)
        timer = ('[Unit]\nDescription=php-quickpatch feeds update every %d h %s\n\n[Timer]\n'
                 'OnCalendar=*-*-* %s:%02d:00\nRandomizedDelaySec=900\nPersistent=true\n\n'
                 '[Install]\nWantedBy=timers.target\n' % (n, MARK, hours, minute))
        return {os.path.join(SYSTEMD_DIR, UNIT + '.service'): service,
                os.path.join(SYSTEMD_DIR, UNIT + '.timer'): timer}
    if k == 'cron':
        return {CRON_FILE: '%d %s * * * root %s %s\n' % (minute, _cron_hours(n), cmd, MARK)}
    return {'crontab': '%d %s * * * %s %s' % (minute, _cron_hours(n), cmd, MARK)}


def _crontab_lines():
    try:
        p = subprocess.run(['crontab', '-l'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return []
    return p.stdout.decode('utf-8', 'replace').splitlines() if p.returncode == 0 else []


def _parse_cron(line):
    m = re.match(r'^\s*(\d+)\s+(\S+)\s+', line)
    if not m:
        return None, None
    minute, hours = int(m.group(1)), m.group(2)
    n = 24 if hours == '0' else (int(hours[2:]) if hours.startswith('*/') and hours[2:].isdigit() else None)
    return minute, n


def show(state_dir=None, now=None):
    """Current schedule or None: {type, interval_h, minute, next_run, files}."""
    k = kind()
    minute = n = None
    files = []
    if k == 'systemd':
        timer = os.path.join(SYSTEMD_DIR, UNIT + '.timer')
        if os.path.isfile(timer):
            text = open(timer).read()
            m = re.search(r'OnCalendar=\*-\*-\* (\d+)(?:/(\d+))?:(\d+):00', text)
            if m:
                n = int(m.group(2)) if m.group(2) else 24
                minute = int(m.group(3))
            files = [timer, os.path.join(SYSTEMD_DIR, UNIT + '.service')]
    elif k == 'cron':
        if os.path.isfile(CRON_FILE):
            for line in open(CRON_FILE):
                if MARK in line:
                    minute, n = _parse_cron(line)
            files = [CRON_FILE]
    else:
        for line in _crontab_lines():
            if MARK in line:
                minute, n = _parse_cron(line)
    if n is None:
        # A root cron line also counts when systemd is present (and the reverse), so install never duplicates.
        if k == 'systemd' and os.path.isfile(CRON_FILE):
            return dict(show_cron_file(), type='cron')
        return None
    return {'type': k, 'interval_h': n, 'minute': minute, 'next_run': next_run(n, minute, now), 'files': files}


def show_cron_file():
    minute = n = None
    for line in open(CRON_FILE):
        if MARK in line:
            minute, n = _parse_cron(line)
    return {'interval_h': n, 'minute': minute, 'next_run': next_run(n, minute) if n else None, 'files': [CRON_FILE]}


def next_run(n, minute, now=None):
    now = time.time() if now is None else now
    t = int(now) - int(now) % 3600 + minute * 60
    for _ in range(49):
        h = time.gmtime(t).tm_hour
        if t > now and h % n == 0:
            return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(t))
        t += 3600
    return None


def plan_install(script, n):
    k = kind()
    cur = show()
    minute = cur['minute'] if cur and cur.get('minute') is not None else machine_minute()
    content = render(k, script, n, minute)
    if k == 'systemd':
        cmds = [['systemctl', 'daemon-reload'], ['systemctl', 'enable', '--now', UNIT + '.timer']]
    elif k == 'cron':
        cmds = []
    else:
        cmds = [['crontab', '-']]
    return {'type': k, 'interval_h': n, 'minute': minute, 'content': content, 'commands': cmds,
            'replaces': cur}


def install(plan):
    k = plan['type']
    if k == 'crontab_user':
        lines = [ln for ln in _crontab_lines() if MARK not in ln] + [plan['content']['crontab']]
        p = subprocess.run(['crontab', '-'], input=('\n'.join(lines) + '\n').encode(), timeout=30)
        if p.returncode != 0:
            raise OSError('crontab - exited %d' % p.returncode)
        return
    for path, text in plan['content'].items():
        tmp = path + '.tmp-%d' % os.getpid()
        with open(tmp, 'w') as f:
            f.write(text)
        os.chmod(tmp, 0o644)
        os.replace(tmp, path)
    for cmd in plan['commands']:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)


def plan_remove():
    k = kind()
    cur = show()
    files, cmds = [], []
    if k == 'systemd':
        files = [p for p in (os.path.join(SYSTEMD_DIR, UNIT + '.timer'), os.path.join(SYSTEMD_DIR, UNIT + '.service'))
                 if os.path.exists(p)]
        if files:
            cmds = [['systemctl', 'disable', '--now', UNIT + '.timer'], ['systemctl', 'daemon-reload']]
        if os.path.isfile(CRON_FILE):
            files.append(CRON_FILE)
    elif k == 'cron':
        files = [CRON_FILE] if os.path.isfile(CRON_FILE) else []
    elif cur:
        cmds = [['crontab', '-']]
    return {'type': k, 'files': files, 'commands': cmds, 'current': cur}


def remove(plan):
    if plan['type'] == 'crontab_user':
        if plan['current']:
            lines = [ln for ln in _crontab_lines() if MARK not in ln]
            subprocess.run(['crontab', '-'], input=('\n'.join(lines) + '\n').encode() if lines else b'', timeout=30)
        return
    for cmd in plan['commands'][:1]:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
    for p in plan['files']:
        os.unlink(p)
    for cmd in plan['commands'][1:]:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
