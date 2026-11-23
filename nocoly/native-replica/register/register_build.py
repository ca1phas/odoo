"""Build the module register from a HAP scan and the Odoo export: who owns every object of the app.

Inputs
- a scan from register_scan.py (default: the newest scans/<stamp>/hap-scan.json)
- ../catalogue/odoo-20.0/odoo-models.csv, odoo-fields.csv, modules.json (from odoo_export.py / odoo_catalogue.py)
- the build ledgers ../*-build/ids.json: {"objects": {"<id>": {"type", "name", "module", "note"}}}
- conventions.json (next to this file): workflow name prefixes -> module

Owner of each object, first match wins
- worksheet: ledger; alias x_<module>__<name>; alias = Odoo model with "_" for "." -> module that defines the model
- field: ledger; HAP system field -> system; alias x_<module>__<name>; alias = field of the sheet's model -> module that declares it
- view / rule / button / chart: ledger; else the sheet's owner (source "inherit")
- workflow: ledger; name prefix "<App> - " (conventions.json); trigger sheet's owner (inherit)
- page / option set: ledger.  role: built-in roles -> system; else ledger.  group: ledger, else derived from its items
Anything left is "unresolved". Acceptance test 19 needs zero unresolved objects.

Outputs (in the scan's folder): register.json, register.md, diff.md (against the previous scan with a register),
and on request prune-<module>.md (--prune) and coverage.md (--coverage).

Usage: python -I register_build.py [--scan PATH] [--prune MODULE ...] [--coverage base,contacts,uom,product,mail]
"""
import argparse, csv, glob, json, os, re, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
PLANS = os.path.dirname(HERE)
CAT = os.path.join(PLANS, 'catalogue', 'odoo-20.0')
TYPES = ['group', 'worksheet', 'field', 'view', 'rule', 'button', 'chart', 'workflow', 'page', 'role', 'optionset']
SYSTEM = 'system'
TECH_FIELDS = {'id', 'display_name', 'create_uid', 'create_date', 'write_uid', 'write_date', '__last_update'}
MIXIN_PREFIX = ('message_', 'activity_', 'website_message', 'rating_', 'access_', 'has_message')
ID_RE = re.compile(r'[0-9a-f]{24}|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')


def load_csv(name):
    return list(csv.DictReader(open(os.path.join(CAT, name), encoding='utf-8')))


class Odoo:
    def __init__(self):
        self.modules = json.load(open(os.path.join(CAT, 'modules.json'), encoding='utf-8'))
        self.model_owner, self.alias_model = {}, {}
        for r in load_csv('odoo-models.csv'):
            self.model_owner[r['model']] = (r['modules'].split(' ') or [''])[0]
            self.alias_model.setdefault(r['model'].replace('.', '_'), []).append(r['model'])
        self.fields = {}
        for r in load_csv('odoo-fields.csv'):
            r['owner'] = (r['modules'].split(' ') or [''])[0]
            self.fields[(r['model'], r['name'])] = r
        self.rdeps = defaultdict(set)
        for m, v in self.modules.items():
            for d in v.get('depends', []):
                self.rdeps[d].add(m)

    def info(self, module):
        if module == SYSTEM:
            return {'family': SYSTEM, 'kind': SYSTEM}
        v = self.modules.get(module)
        if not v:
            return {'family': '?', 'kind': 'unknown module'}
        if v['kind'] in ('foundation', 'foundation app'):
            fam = 'foundation'
        else:
            fam = ' + '.join(self.modules[a]['name'] if a in self.modules else a for a in v.get('apps') or []) or module
        return {'family': fam, 'kind': v['kind']}

    def x_module(self, alias):
        """x_<module>__<name> -> module (or None)."""
        if alias and alias.startswith('x_') and '__' in alias[2:]:
            m = alias[2:].split('__', 1)[0]
            if m in self.modules or m == SYSTEM:
                return m
        return None

    def closure(self, module):
        seen, todo = {module}, [module]
        while todo:
            for d in self.rdeps.get(todo.pop(), ()):
                if d not in seen:
                    seen.add(d)
                    todo.append(d)
        return seen


def load_ledger():
    led = {}
    for p in sorted(glob.glob(os.path.join(PLANS, '*-build', 'ids.json'))):
        for oid, v in (json.load(open(p, encoding='utf-8')).get('objects') or {}).items():
            led[oid] = dict(v, ledger=os.path.relpath(p, PLANS))
    return led


def strings(x):
    if isinstance(x, dict):
        for v in x.values():
            yield from strings(v)
    elif isinstance(x, list):
        for v in x:
            yield from strings(v)
    elif isinstance(x, str):
        yield x


def latest_scan():
    scans = sorted(glob.glob(os.path.join(HERE, 'scans', '*', 'hap-scan.json')))
    if not scans:
        sys.exit('no scan found; run register_scan.py first')
    return scans[-1]


def build(scan, odoo, led, conv):
    objs = []

    def add(o):
        if o['module'] not in (None, 'derived'):
            o.update(odoo.info(o['module']))
        objs.append(o)
        return o

    def from_ledger(oid):
        v = led.get(oid)
        return (v['module'], 'ledger') if v and v.get('module') else (None, None)

    sheet_owner = {}
    for s in scan['worksheets']:
        mod, src = from_ledger(s['id'])
        models = odoo.alias_model.get(s['alias'], [])
        model = models[0] if len(models) == 1 else ''
        if not mod and odoo.x_module(s['alias']):
            mod, src = odoo.x_module(s['alias']), 'alias x_'
        if not mod and model:
            mod, src = odoo.model_owner.get(model), 'odoo model'
        why = '' if mod else ('alias matches several Odoo models: ' + ', '.join(models) if len(models) > 1 else
                              'no alias' if not s['alias'] else f"alias '{s['alias']}' is not an Odoo model and has no x_<module>__ prefix")
        sheet_owner[s['id']] = mod
        add({'type': 'worksheet', 'id': s['id'], 'name': s['name'], 'alias': s['alias'], 'odoo_model': model,
             'module': mod, 'source': src, 'why': why, 'parent_sheet': s.get('parent_sheet'), 'raw': {'desc': s['desc']}})
        for f in s['fields']:
            mod, src = from_ledger(f['id'])
            ofield = odoo.fields.get((model, f['alias'])) if model and f['alias'] else None
            if not mod and odoo.x_module(f['alias']):
                mod, src = odoo.x_module(f['alias']), 'alias x_'
            if not mod and ofield:
                mod, src = ofield['owner'], 'odoo field'
            why = '' if mod else ('no alias' if not f['alias'] else
                                  f"alias '{f['alias']}' is not a field of {model or 'an Odoo model'} and has no x_<module>__ prefix")
            add({'type': 'field', 'id': f['id'], 'name': f['name'], 'alias': f['alias'], 'sheet': s['id'], 'sheet_name': s['name'],
                 'field_type': f['type'], 'odoo_field': f['alias'] if ofield else '', 'module': mod, 'source': src, 'why': why,
                 'raw': f['raw']})
        for kind, key in (('view', 'views'), ('rule', 'rules'), ('button', 'buttons'), ('chart', 'charts')):
            for c in s[key]:
                mod, src = from_ledger(c['id'])
                if not mod and sheet_owner[s['id']]:
                    mod, src = sheet_owner[s['id']], 'inherit'
                add({'type': kind, 'id': c['id'], 'name': c['name'], 'sheet': s['id'], 'sheet_name': s['name'],
                     'module': mod, 'source': src, 'why': '' if mod else 'sheet has no owner', 'raw': c['raw']})

    prefixes = conv.get('workflow_prefixes', {})
    for w in scan['workflows']:
        mod, src = from_ledger(w['id'])
        if not mod:
            p = w['name'].split(' - ', 1)[0] if ' - ' in w['name'] else ''
            if p in prefixes:
                mod, src = prefixes[p], 'name prefix'
        if not mod and sheet_owner.get(w['trigger_sheet']):
            mod, src = sheet_owner[w['trigger_sheet']], 'inherit'
        add({'type': 'workflow', 'id': w['id'], 'name': w['name'], 'sheet': w['trigger_sheet'], 'enabled': w['enabled'],
             'module': mod, 'source': src, 'why': '' if mod else 'not in a ledger, no known name prefix, no owned trigger sheet',
             'raw': w['raw']})
    for p in scan['pages']:
        mod, src = from_ledger(p['id'])
        add({'type': 'page', 'id': p['id'], 'name': p['name'], 'module': mod, 'source': src,
             'why': '' if mod else 'not in a ledger', 'raw': p['raw']})
    for r in scan['roles']:
        mod, src = from_ledger(r['id'])
        if not mod and r['roleType'] in (1, 2, 100):
            mod, src = SYSTEM, 'built-in role'
        add({'type': 'role', 'id': r['id'], 'name': r['name'], 'members': r['members'], 'module': mod, 'source': src,
             'why': '' if mod else 'not in a ledger', 'raw': {}})
    for o in scan['optionsets']:
        mod, src = from_ledger(o['id'])
        add({'type': 'optionset', 'id': o['id'], 'name': o['name'], 'module': mod, 'source': src,
             'why': '' if mod else 'not in a ledger', 'raw': o['raw']})
    for g in scan['sections']:
        mod, src = from_ledger(g['id'])
        add({'type': 'group', 'id': g['id'], 'name': g['name'], 'parent': g['parent'], 'items': [i['id'] for i in g['items']],
             'module': mod or 'derived', 'source': src or 'items', 'why': '', 'raw': {}})

    known = {o['id'] for o in objs}
    for o in objs:
        refs = set()
        for t in strings(o['raw']):
            refs.update(i for i in ID_RE.findall(t) if i in known)
        refs.discard(o['id'])
        if o.get('sheet'):
            refs.add(o['sheet'])
        o['refs'] = sorted(refs)
    return objs


def strip(o):
    return {k: v for k, v in o.items() if k != 'raw'}


def write_md(path, scan, objs, odoo, led):
    by = defaultdict(Counter)
    for o in objs:
        by[o['module'] or 'UNRESOLVED'][o['type']] += 1
    unresolved = [o for o in objs if not o['module']]
    inherit = Counter(o['type'] for o in objs if o['source'] == 'inherit')
    L = [f"# Module register: {scan['app']['name']}", '',
         f"Scan {scan['scanned_at']} ({'complete' if scan['complete'] else 'PARTIAL scan'}), app `{scan['app']['id']}`, profile `{scan['app']['profile']}`. "
         f"Generated by `register_build.py`; do not edit. Ledger entries: {len(led)}.", '',
         f"**{len(objs)} objects, {len(unresolved)} unresolved.**" + (f" Read errors during the scan: {len(scan['errors'])}." if scan['errors'] else ''), '',
         '| Module | Family | Kind | ' + ' | '.join(t.capitalize() + 's' for t in TYPES) + ' |',
         '|---|---|---|' + '---:|' * len(TYPES)]
    for m in sorted(by, key=lambda k: (k in ('UNRESOLVED', SYSTEM, 'derived'), k)):
        i = odoo.info(m) if m not in ('UNRESOLVED', 'derived') else {'family': '', 'kind': ''}
        L.append(f"| {m} | {i['family']} | {i['kind']} | " + ' | '.join(str(by[m][t] or '') for t in TYPES) + ' |')
    L += ['', '"derived" groups have no owner of their own: a group goes when all its items go.', '']
    if inherit:
        L += ['Owner taken from the sheet (not in a ledger): ' + ', '.join(f'{v} {k}s' for k, v in inherit.items()) +
              '. A later module that adds such an object to a shared sheet must record it in its ledger.', '']
    L += ['## Sheets', '', '| Sheet | Alias | Odoo model | Owner | Fields by owner |', '|---|---|---|---|---|']
    for s in (o for o in objs if o['type'] == 'worksheet'):
        fc = Counter(f['module'] or 'UNRESOLVED' for f in objs if f['type'] == 'field' and f['sheet'] == s['id'])
        L.append(f"| {s['name']} | `{s['alias']}` | {s['odoo_model'] or '—'} | {s['module'] or '**UNRESOLVED**'} | " +
                 ', '.join(f'{k} {v}' for k, v in fc.most_common()) + ' |')
    if unresolved:
        L += ['', '## Unresolved', '', '| Type | Name | Sheet | Alias | Why |', '|---|---|---|---|---|']
        for o in unresolved:
            L.append(f"| {o['type']} | {o['name']} | {o.get('sheet_name', '')} | `{o.get('alias', '')}` | {o['why']} |")
    if scan['errors']:
        L += ['', '## Read errors', ''] + [f'- {e}' for e in scan['errors']]
    open(path, 'w', encoding='utf-8').write('\n'.join(L) + '\n')


def write_diff(path, cur, prev_path):
    if not prev_path:
        open(path, 'w', encoding='utf-8').write('# Diff\n\nNo earlier register to compare with.\n')
        return
    prev = {o['id']: o for o in json.load(open(prev_path, encoding='utf-8'))['objects']}
    now = {o['id']: o for o in cur}
    L = [f'# Diff against {os.path.basename(os.path.dirname(prev_path))}', '']
    added = [now[i] for i in now if i not in prev]
    removed = [prev[i] for i in prev if i not in now]
    changed = [(prev[i], now[i]) for i in now if i in prev and any(prev[i].get(k) != now[i].get(k) for k in ('name', 'alias', 'module'))]
    L.append(f'{len(added)} added, {len(removed)} removed, {len(changed)} changed (name, alias or owner).')
    for title, rows in (('Added', added), ('Removed', removed)):
        if rows:
            L += ['', f'## {title}', '', '| Type | Name | Sheet | Owner |', '|---|---|---|---|']
            L += [f"| {o['type']} | {o['name']} | {o.get('sheet_name', '')} | {o['module'] or 'UNRESOLVED'} |" for o in rows]
    if changed:
        L += ['', '## Changed', '', '| Type | Before | After |', '|---|---|---|']
        for a, b in changed:
            L.append(f"| {b['type']} | {a['name']} `{a.get('alias', '')}` ({a['module']}) | {b['name']} `{b.get('alias', '')}` ({b['module']}) |")
    open(path, 'w', encoding='utf-8').write('\n'.join(L) + '\n')


def write_prune(path, module, objs, odoo):
    gone_mods = odoo.closure(module)
    gone = {o['id'] for o in objs if o['module'] in gone_mods}
    for g in (o for o in objs if o['type'] == 'group' and o['module'] == 'derived'):
        if g['items'] and all(i in gone for i in g['items']):
            gone.add(g['id'])
    keep = [o for o in objs if o['id'] not in gone]
    bridges = [(o, [r for r in o['refs'] if r in gone]) for o in keep]
    bridges = [(o, r) for o, r in bridges if r]
    name = {o['id']: f"{o['type']} {o['name']}" for o in objs}
    L = [f'# Prune prediction: remove `{module}`', '',
         f"Modules that go with it (they depend on it): {', '.join(sorted(m for m in gone_mods if any(o['module'] == m for o in objs))) or module}.", '',
         f'**Remove {len(gone)} objects, retain {len(keep)}, {len(bridges)} retained objects point at removed ones, '
         f"{sum(1 for o in objs if not o['module'])} unresolved.**", '', '## Remove', '']
    c = Counter(o['type'] for o in objs if o['id'] in gone)
    L += [f'- {v} {k}s' for k, v in c.items()] or ['- nothing']
    L += ['', '## Retain', ''] + [f'- {m}: {v}' for m, v in Counter(o['module'] or 'UNRESOLVED' for o in keep).most_common()]
    L += ['', '## Bridges to fix (retained, but they point at removed objects)', '']
    L += [f"- {o['type']} **{o['name']}** ({o['module']}) → " + '; '.join(name[r] for r in r_) for o, r_ in bridges] or ['- none']
    open(path, 'w', encoding='utf-8').write('\n'.join(L) + '\n')


def write_coverage(path, modules, objs, odoo):
    decisions = {}
    for p in glob.glob(os.path.join(PLANS, '*-build', 'field-decisions.csv')):
        for r in csv.DictReader(open(p, encoding='utf-8')):
            decisions[(r['model'], r['field'])] = (r['decision'], r['reason'])
    built = defaultdict(set)
    sheets = {o['id']: o for o in objs if o['type'] == 'worksheet'}
    for f in (o for o in objs if o['type'] == 'field' and o['odoo_field']):
        built[sheets[f['sheet']]['odoo_model']].add(f['odoo_field'])
    models = sorted({s['odoo_model'] for s in sheets.values() if s['odoo_model']})
    L = ['# No-feature-cut checklist', '', f"Odoo fields declared by {', '.join(modules)} on the models that have a HAP sheet. "
         'Technical fields and the message / activity / rating / portal mixins are left out (HAP has its own). '
         'Decisions come from `*-build/field-decisions.csv`.', '']
    total = Counter()
    for m in models:
        rows = [r for (mm, n), r in odoo.fields.items() if mm == m and r['owner'] in modules
                and n not in TECH_FIELDS and not n.startswith(MIXIN_PREFIX)]
        st = []
        for r in sorted(rows, key=lambda r: r['name']):
            if r['name'] in built[m]:
                s = 'built'
            elif (m, r['name']) in decisions:
                s = decisions[(m, r['name'])][0]
            else:
                s = 'OPEN'
            total[s.split(':')[0]] += 1
            st.append((r, s))
        c = Counter(s.split(':')[0] for _, s in st)
        L += [f'## `{m}`', '', ', '.join(f'{k} {v}' for k, v in c.most_common()), '', '| Field | Label | Type | Stored | Owner | Status |', '|---|---|---|---|---|---|']
        L += [f"| `{r['name']}` | {r['label']} | {r['ttype']} | {r['store']} | {r['owner']} | {s}"
              + (f" — {decisions[(m, r['name'])][1]}" if (m, r['name']) in decisions and s != 'built' else '') + ' |' for r, s in st]
        L.append('')
    L.insert(4, '**Total:** ' + ', '.join(f'{k} {v}' for k, v in total.most_common()) + '\n')
    open(path, 'w', encoding='utf-8').write('\n'.join(L) + '\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--scan')
    ap.add_argument('--prune', nargs='*', default=[])
    ap.add_argument('--coverage', help='comma-separated Odoo modules, e.g. base,contacts,uom,product,mail')
    a = ap.parse_args()
    scan_path = a.scan or latest_scan()
    folder = os.path.dirname(scan_path)
    scan = json.load(open(scan_path, encoding='utf-8'))
    odoo, led = Odoo(), load_ledger()
    conv_path = os.path.join(HERE, 'conventions.json')
    conv = json.load(open(conv_path, encoding='utf-8')) if os.path.exists(conv_path) else {}
    objs = build(scan, odoo, led, conv)
    out = [strip(o) for o in objs]
    json.dump({'scan': os.path.relpath(scan_path, HERE), 'app': scan['app'], 'scanned_at': scan['scanned_at'],
               'complete': scan['complete'], 'objects': out}, open(os.path.join(folder, 'register.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    write_md(os.path.join(folder, 'register.md'), scan, out, odoo, led)
    prevs = sorted(p for p in glob.glob(os.path.join(HERE, 'scans', '*', 'register.json')) if os.path.dirname(p) < folder)
    write_diff(os.path.join(folder, 'diff.md'), out, prevs[-1] if prevs else None)
    for m in a.prune:
        write_prune(os.path.join(folder, f'prune-{m}.md'), m, out, odoo)
    if a.coverage:
        write_coverage(os.path.join(folder, 'coverage.md'), [m.strip() for m in a.coverage.split(',')], out, odoo)
    un = sum(1 for o in out if not o['module'])
    print(f"{len(out)} objects, {un} unresolved -> {folder}")
    print(' '.join(f'{t}:{n}' for t, n in Counter(o['type'] for o in out).items()))


if __name__ == '__main__':
    main()
