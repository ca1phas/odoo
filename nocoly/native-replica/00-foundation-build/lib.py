"""Shared helpers for the wave 0 build scripts: hap-cli calls, the ledger (ids.json) and the build log.

Every step script reads live state first, writes, then reads back. Return values of write commands are never trusted
on their own: the script re-reads the object and the step is only marked done after a check in the HAP UI.
"""
import datetime, json, os, subprocess, time

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.environ.get('ODOO_REPLICA_APP_ID', '')  # set it locally; ids stay out of the repo
PROFILE = os.environ.get('HAP_PROFILE', '')
LEDGER = os.path.join(HERE, 'ids.json')
ENV = dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONUTF8='1')


class HapError(RuntimeError):
    pass


def hap(*args, ok_fail=False, retries=1):
    cmd = ['hap', '--profile', PROFILE, '--json', *[str(a) for a in args]]
    for attempt in range(retries + 1):
        r = subprocess.run(cmd, capture_output=True, env=ENV)
        out = r.stdout.decode('utf-8', 'replace').strip()
        err = r.stderr.decode('utf-8', 'replace').strip()
        try:
            data = json.loads(out) if out else None
        except ValueError:
            data = None
        if r.returncode == 0 and data is not None:
            return data
        if attempt < retries and 'timed out' not in (out + err).lower():
            time.sleep(2)
            continue
        if ok_fail:
            return {'_error': (out or err)[:500], '_exit': r.returncode}
        raise HapError(f"hap {' '.join(map(str, args))[:200]}: exit {r.returncode}: {(out or err)[:500]}")


def unwrap(d):
    return d.get('data', d) if isinstance(d, dict) and 'success' in d and 'data' in d else d


def app_info():
    return unwrap(hap('app', 'info', '-a', APP))


def sections_flat(info=None):
    info = info or app_info()
    out = []

    def walk(ss, parent):
        for s in ss:
            out.append({'id': s['id'], 'name': s.get('name', ''), 'parent': parent, 'items': s.get('items', [])})
            walk(s.get('childSections') or [], s['id'])
    walk(info.get('sections', []), None)
    return out


def roles():
    return unwrap(hap('app', 'role', 'list', '-a', APP)).get('roles', [])


def ledger():
    if os.path.exists(LEDGER):
        return json.load(open(LEDGER, encoding='utf-8'))
    return {'app': APP, 'objects': {}}


def record(oid, type_, name, module, note):
    led = ledger()
    led['objects'][oid] = {'type': type_, 'name': name, 'module': module, 'note': note,
                           'recorded': datetime.datetime.now().isoformat(timespec='seconds')}
    json.dump(led, open(LEDGER, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def backup(name, data):
    d = os.path.join(HERE, 'backups')
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, f"{datetime.datetime.now():%Y%m%d-%H%M%S}-{name}.json")
    json.dump(data, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return p
