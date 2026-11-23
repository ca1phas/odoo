"""Read-only scan of a HAP app for the module register (HAP side).

Only read commands of hap-cli run: app info, worksheet info / fields / view list / rules / custom-actions / chart list,
workflow list / structure, custom-page info, app role list, app optionset list.

Output: <out>/<YYYY-MM-DD-HHMM>/hap-scan.json (normalised, plus each object's raw JSON for references).

Usage:
  python -I register_scan.py [--app APP_ID] [--profile <profile>] [--out DIR] [--limit-sheets N]
Defaults: app and profile from the environment (ODOO_REPLICA_APP_ID, HAP_PROFILE); out = this folder's scans/.
"""
import argparse, datetime, json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_APP = os.environ.get('ODOO_REPLICA_APP_ID', '')  # set it locally; ids stay out of the repo
ENV = dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONUTF8='1')
SYSTEM_CONTROLS = {'rowid', 'ownerid', 'caid', 'ctime', 'utime', 'uaid', 'wfname', 'wfcuaids', 'wfcaid', 'wfctime',
                   'wfrtime', 'wfcotime', 'wfdtime', 'wfftime', 'wfstatus'}
ERRORS = []


def hap(profile, *args, allow_fail=False):
    cmd = ['hap', '--profile', profile, '--json', *args]
    for attempt in (1, 2):
        r = subprocess.run(cmd, capture_output=True, env=ENV)
        out = r.stdout.decode('utf-8', 'replace').strip()
        try:
            return json.loads(out)
        except ValueError:
            if attempt == 2:
                msg = f"{' '.join(args)}: exit {r.returncode}: {out[:200]} {r.stderr.decode('utf-8', 'replace')[:200]}"
                ERRORS.append(msg)
                if allow_fail:
                    return None
                raise RuntimeError(msg)


def unwrap(d):
    return d.get('data', d) if isinstance(d, dict) and 'data' in d and 'success' in d else d


def walk_sections(sections, parent=None, out=None):
    out = [] if out is None else out
    for s in sections:
        out.append({'id': s['id'], 'name': s.get('name', ''), 'parent': parent,
                    'items': [{'type': i.get('type'), 'id': i.get('id'), 'name': i.get('name'), 'alias': i.get('alias', '')}
                              for i in s.get('items', [])]})
        walk_sections(s.get('childSections', []) or [], s['id'], out)
    return out


def scan_sheet(profile, app, ws, parent=None):
    extra = ['--parent', parent] if parent else []
    info = hap(profile, 'worksheet', 'info', ws, '-a', app, allow_fail=True) or {}
    fields = hap(profile, 'worksheet', 'fields', ws, '-a', app, '--raw', *extra, allow_fail=True) or []
    views = hap(profile, 'worksheet', 'view', 'list', ws, '-a', app, allow_fail=True) or []
    rules = hap(profile, 'worksheet', 'rules', ws, allow_fail=True) or []
    actions = hap(profile, 'worksheet', 'custom-actions', ws, '-a', app, allow_fail=True) or []
    charts = hap(profile, 'worksheet', 'chart', 'list', ws, allow_fail=True) or {}
    charts = charts.get('reports', []) if isinstance(charts, dict) else charts
    return {
        'id': ws, 'name': info.get('name', ''), 'alias': info.get('alias', ''), 'desc': info.get('desc', ''),
        'parent_sheet': parent,
        'system_fields': [c['controlId'] for c in (info.get('template') or {}).get('controls', []) if c['controlId'] in SYSTEM_CONTROLS],
        'fields': [{'id': c['controlId'], 'name': c.get('controlName', ''), 'alias': c.get('alias', ''), 'type': c.get('type'),
                    'dataSource': c.get('dataSource', ''), 'sourceControlId': c.get('sourceControlId', ''),
                    'required': c.get('required'), 'unique': c.get('unique'), 'raw': c} for c in fields],
        'views': [{'id': v['viewId'], 'name': v.get('name', ''), 'type': v.get('viewType'), 'raw': v} for v in views],
        'rules': [{'id': r['ruleId'], 'name': r.get('name', ''), 'disabled': r.get('disabled'), 'raw': r} for r in rules],
        'buttons': [{'id': b['btnId'], 'name': b.get('name', ''), 'workflowId': b.get('workflowId', ''), 'raw': b} for b in actions],
        'charts': [{'id': c['id'], 'name': c.get('name', ''), 'reportType': c.get('reportType'), 'raw': c} for c in charts],
    }


def scan_workflows(profile, app):
    flows, page = [], 1
    while True:
        d = hap(profile, 'workflow', 'list', '-a', app, '-n', '100', '-p', str(page), allow_fail=True) or {}
        batch = d.get('data', []) if isinstance(d, dict) else d
        flows += batch
        if not (isinstance(d, dict) and d.get('has_more')) or not batch:
            break
        page += 1
    out = []
    for f in flows:
        st = hap(profile, 'workflow', 'structure', f['id'], allow_fail=True) or {}
        nodes = list((st.get('flowNodeMap') or {}).values())
        out.append({'id': f['id'], 'name': f.get('name', ''), 'enabled': f.get('enabled'), 'explain': f.get('explain', ''),
                    'trigger_sheet': f.get('appId', ''), 'trigger_type': f.get('triggerId'), 'list_type': f.get('processListType'),
                    'start_app_type': f.get('startAppType'), 'child': f.get('child'),
                    'nodes': [{'id': n.get('id'), 'type': n.get('typeId'), 'name': n.get('name', ''), 'sheet': n.get('appId', ''),
                               'app_type': n.get('appType'), 'action': n.get('actionId')} for n in nodes],
                    'raw': {'list': f, 'structure': st}})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--app', default=DEFAULT_APP)
    ap.add_argument('--profile', default=os.environ.get('HAP_PROFILE', ''))
    ap.add_argument('--out', default=os.path.join(HERE, 'scans'))
    ap.add_argument('--limit-sheets', type=int, default=0, help='scan only the first N sheets (tool tests)')
    ap.add_argument('--no-workflows', action='store_true')
    a = ap.parse_args()

    started = datetime.datetime.now()
    info = unwrap(hap(a.profile, 'app', 'info', '-a', a.app))
    sections = walk_sections(info.get('sections', []))
    sheet_ids = [i['id'] for s in sections for i in s['items'] if i['type'] == 0]
    page_ids = [i['id'] for s in sections for i in s['items'] if i['type'] == 1]
    if a.limit_sheets:
        sheet_ids = sheet_ids[:a.limit_sheets]

    with ThreadPoolExecutor(4) as ex:
        sheets = list(ex.map(lambda w: scan_sheet(a.profile, a.app, w), sheet_ids))
    # sub-table sheets that are not in the navigation: scan them through their parent sheet
    known = set(sheet_ids)
    queue = [(f['dataSource'], s['id']) for s in sheets for f in s['fields'] if f['type'] == 34 and f['dataSource'] and f['dataSource'] not in known]
    while queue and not a.limit_sheets:
        ws, parent = queue.pop()
        if ws in known:
            continue
        known.add(ws)
        s = scan_sheet(a.profile, a.app, ws, parent)
        sheets.append(s)
        queue += [(f['dataSource'], s['id']) for f in s['fields'] if f['type'] == 34 and f['dataSource'] and f['dataSource'] not in known]

    pages = []
    for p in page_ids:
        d = hap(a.profile, 'custom-page', 'info', p, allow_fail=True) or {}
        pages.append({'id': p, 'name': d.get('name', ''), 'components': [{'id': c.get('id'), 'type': c.get('type')} for c in d.get('components', [])], 'raw': d})

    roles = (unwrap(hap(a.profile, 'app', 'role', 'list', '-a', a.app, allow_fail=True)) or {}).get('roles', [])
    opts = (unwrap(hap(a.profile, 'app', 'optionset', 'list', '-a', a.app, allow_fail=True)) or {}).get('optionsets', [])
    flows = [] if a.no_workflows else scan_workflows(a.profile, a.app)

    scan = {
        'app': {'id': a.app, 'name': info.get('name'), 'profile': a.profile},
        'scanned_at': started.isoformat(timespec='seconds'),
        'complete': not a.limit_sheets and not a.no_workflows,
        'sections': sections,
        'worksheets': sheets,
        'workflows': flows,
        'pages': pages,
        'roles': [{'id': r['id'], 'name': r.get('name', ''), 'roleType': r.get('roleType'),
                   'members': len(r.get('accounts', [])) + len(r.get('departments', [])) + len(r.get('jobs', []))} for r in roles],
        'optionsets': [{'id': o['id'], 'name': o.get('name', ''), 'options': len(o.get('options', [])), 'raw': o} for o in opts],
        'errors': ERRORS,
    }
    folder = os.path.join(a.out, started.strftime('%Y-%m-%d-%H%M'))
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, 'hap-scan.json')
    json.dump(scan, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    n = lambda k: sum(len(s[k]) for s in sheets)
    print(f"{info.get('name')}: {len(sections)} groups, {len(sheets)} sheets, {n('fields')} fields, {n('views')} views, "
          f"{n('rules')} rules, {n('buttons')} buttons, {n('charts')} charts, {len(flows)} workflows, {len(pages)} pages, "
          f"{len(scan['roles'])} roles, {len(opts)} option sets; {len(ERRORS)} read errors -> {path}")
    for e in ERRORS[:10]:
        print('  error:', e)


if __name__ == '__main__':
    main()
