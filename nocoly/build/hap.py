"""Thin wrapper over the hap CLI for the build scripts.

Run the scripts with the CLI's own interpreter so its builders import:

    ~/.hap-venv/bin/python nocoly/build/<worksheet>.py <step>
"""
import datetime, json, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
IDS_PATH = os.path.join(HERE, 'ids.json')
BACKUPS = os.path.join(HERE, 'backups')


def ids():
    return json.load(open(IDS_PATH))


def run(*args):
    """Run `hap --json <args>` and return the parsed output; raise on failure."""
    p = subprocess.run(['hap', '--json', *args], capture_output=True, text=True, timeout=180)
    out = p.stdout.strip()
    if p.returncode != 0:
        raise RuntimeError(f"hap {' '.join(args[:3])} failed ({p.returncode}): {p.stderr.strip() or out}")
    try:
        return json.loads(out) if out else None
    except json.JSONDecodeError:
        return out


def controls(worksheet_id):
    return run('worksheet', 'fields', worksheet_id, '--raw')


def listing(*args):
    """Run a read command whose JSON is either a bare list or {'data': [...]}."""
    out = run(*args)
    return out if isinstance(out, list) else (out or {}).get('data') or []


def by_name(ctrls):
    return {c['controlName']: c for c in ctrls}


def backup(name, data):
    """Write data to backups/<name>_<yyyymmdd-hhmmss>.json before a change."""
    os.makedirs(BACKUPS, exist_ok=True)
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    path = os.path.join(BACKUPS, f'{name}_{stamp}.json')
    json.dump(data, open(path, 'w'), ensure_ascii=False, indent=1)
    return path
