"""Module catalogue from Odoo __manifest__.py files (parsed with ast.literal_eval, never executed).

Usage: python -I odoo_catalogue.py <odoo repo dir> <output dir>
Writes modules.json, modules.csv and apps.md to the output dir.
"""
import ast, csv, json, os, sys
from collections import defaultdict

repo, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
mods = {}
for base in ('addons', os.path.join('odoo', 'addons')):
    root = os.path.join(repo, base)
    if not os.path.isdir(root):
        continue
    for name in sorted(os.listdir(root)):
        mf = os.path.join(root, name, '__manifest__.py')
        if not os.path.isfile(mf):
            continue
        try:
            d = ast.literal_eval(open(mf, encoding='utf-8').read())
        except Exception as e:  # noqa: BLE001 - report and continue
            print('unreadable manifest', name, e)
            continue
        mods[name] = {
            'module': name, 'name': d.get('name', name), 'category': d.get('category', ''),
            'summary': (d.get('summary') or '').strip(), 'depends': list(d.get('depends') or []),
            'application': bool(d.get('application')), 'auto_install': d.get('auto_install', False),
            'installable': d.get('installable', True), 'license': d.get('license', ''),
            'where': base.replace(os.sep, '/'),
        }

# Foundation: everything that is not a business app (no app of its own in its dependency closure
# other than these). 'mail' (Discuss) and 'contacts' are apps that almost everything leans on.
FOUNDATION_APPS = {'mail', 'contacts', 'calendar', 'web', 'base'}

closure_cache = {}


def closure(m, seen=None):
    if m in closure_cache:
        return closure_cache[m]
    seen = seen or set()
    if m in seen or m not in mods:
        return set()
    seen.add(m)
    res = set()
    for dep in mods[m]['depends']:
        res.add(dep)
        res |= closure(dep, seen)
    closure_cache[m] = res
    return res


apps = sorted(m for m, v in mods.items() if v['application'] and v['installable'])
business_apps = [a for a in apps if a not in FOUNDATION_APPS]


# Base modules that are the real core of an app whose app module is a thin wrapper.
APP_CORE = {'sale': 'sale_management', 'event': 'website_event'}
fam_cache = {}


def families(m, stack=()):
    """App families a module touches: an app is its own family, an app core counts as its app,
    anything else inherits the families of its direct dependencies."""
    if m in fam_cache:
        return fam_cache[m]
    if m not in mods or m in stack:
        return set()
    if m in business_apps:
        res = {m}
    elif m in APP_CORE:
        res = {APP_CORE[m]}
    else:
        res = set()
        for dep in mods[m]['depends']:
            res |= families(dep, stack + (m,))
    fam_cache[m] = res
    return res


fc_cache = {}


def family_closure(a, stack=()):
    """Families an app itself needs (so they can be dropped from a bridge's list)."""
    if a in fc_cache:
        return fc_cache[a]
    if a in stack or a not in mods:
        return set()
    out = set()
    deps = list(mods[a]['depends'])
    for core, app in APP_CORE.items():  # an app also needs whatever its core module needs
        if app == a and core in mods:
            deps += mods[core]['depends']
    for d in deps:
        for f in families(d):
            if f == a:
                continue
            out.add(f)
            out |= family_closure(f, stack + (a,))
    fc_cache[a] = out
    return out


def apps_in(m):
    s = families(m)
    return sorted(a for a in s if not any(a in family_closure(b) for b in s if b != a))


for m, v in mods.items():
    v['l10n'] = m.startswith('l10n_')
    hi = apps_in(m)
    v['apps'] = hi
    allapps = sorted(families(m) | {x for f in families(m) for x in family_closure(f)})
    v['apps_all'] = allapps
    if v['application']:
        v['kind'] = 'foundation app' if m in FOUNDATION_APPS else 'app'
    elif v['l10n']:
        v['kind'] = 'localisation'
    elif m in APP_CORE:
        v['kind'] = 'app core'
    elif not allapps:
        v['kind'] = 'foundation'
    elif len(hi) == 1:
        v['kind'] = 'extension'
    else:
        v['kind'] = 'bridge'
    auto = v['auto_install']
    v['auto'] = 'yes' if auto is True else (('if ' + '+'.join(auto)) if isinstance(auto, list) and auto else 'no')

json.dump(mods, open(os.path.join(out, 'modules.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
with open(os.path.join(out, 'modules.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f)
    w.writerow(['module', 'name', 'kind', 'apps (top)', 'apps (all in closure)', 'depends', 'auto_install',
                'application', 'category', 'installable', 'license', 'summary'])
    for m in sorted(mods):
        v = mods[m]
        w.writerow([m, v['name'], v['kind'], ' + '.join(v['apps']), ' + '.join(v['apps_all']), ' '.join(v['depends']),
                    v['auto'], 'yes' if v['application'] else '', v['category'], 'yes' if v['installable'] else 'no',
                    v['license'], v['summary']])

# per-app summary
ext = defaultdict(list); bridges = defaultdict(list)
for m, v in mods.items():
    if not v['installable'] or v['l10n']:
        continue
    if v['kind'] == 'extension':
        ext[v['apps'][0]].append(m)
    elif v['kind'] == 'bridge':
        for a in v['apps']:
            bridges[a].append(m)

kinds = defaultdict(int)
for v in mods.values():
    kinds[v['kind'] + ('' if v['installable'] else ' (not installable)')] += 1

lines = ['# Odoo module catalogue (generated)', '',
         f'Source: `{repo}`. {len(mods)} manifests. Generated by `odoo_catalogue.py`; do not edit by hand.', '',
         '## Module kinds', '']
for k in sorted(kinds):
    lines.append(f'- {k}: {kinds[k]}')
lines += ['', '## Apps', '',
          '"Needs apps" lists the other business apps in its dependency closure. "Bridges" are modules that need '
          'this app and at least one other app at the same level.', '',
          '| App module | Name | Category | Needs apps | Own extensions | Bridges | License |', '|---|---|---|---|---:|---:|---|']
for a in apps:
    v = mods[a]
    need = sorted(set(v['apps_all']) - {a})
    lines.append(f"| `{a}` | {v['name']} | {v['category']} | {', '.join(need) or '-'} | {len(ext.get(a, []))} | "
                 f"{len(bridges.get(a, []))} | {v['license']} |")
lines += ['', '## Bridges by app pair', '']
pairs = defaultdict(list)
for m, v in mods.items():
    if v['kind'] == 'bridge' and v['installable'] and not v['l10n']:
        pairs[' + '.join(v['apps'])].append(m)
for p in sorted(pairs, key=lambda p: (-len(pairs[p]), p)):
    lines.append(f"- **{p}** ({len(pairs[p])}): " + ', '.join(f'`{x}`' for x in sorted(pairs[p])))
open(os.path.join(out, 'apps.md'), 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
print('modules', len(mods), 'apps', len(apps), dict(kinds))
