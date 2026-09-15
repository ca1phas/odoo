#!/usr/bin/env python3
"""Parse every __manifest__.py in this checkout into a dependency graph.

    python3 nocoly/tools/manifest_graph.py            # summary
    python3 nocoly/tools/manifest_graph.py --json out.json

A "bridge" is a non-localisation module flagged auto_install with two or more
dependencies: it exists only to join two apps. Roughly half of Odoo's business
modules are bridges, which is why apps can be copied one at a time.
"""
import argparse, ast, collections, json, os, sys

ROOTS = ('addons', os.path.join('odoo', 'addons'))

def load(repo='.'):
    mods = {}
    for root in ROOTS:
        d = os.path.join(repo, root)
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            p = os.path.join(d, name, '__manifest__.py')
            if not os.path.isfile(p):
                continue
            try:
                m = ast.literal_eval(open(p, encoding='utf-8').read())
            except Exception as e:
                print(f'skip {name}: {e}', file=sys.stderr)
                continue
            mods[name] = {
                'depends': m.get('depends', []),
                'category': m.get('category', ''),
                'application': bool(m.get('application')),
                'auto_install': m.get('auto_install', False),
                'installable': m.get('installable', True),
            }
    return mods

def closure(mods, name, seen=None):
    if seen is None:
        seen = set()
    for d in mods.get(name, {}).get('depends', []):
        if d not in seen:
            seen.add(d)
            closure(mods, d, seen)
    return seen

def is_noise(name):
    return name.startswith('l10n_') or name.startswith('test_')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', default='.')
    ap.add_argument('--json')
    a = ap.parse_args()
    mods = load(a.repo)
    business = {m for m in mods if not is_noise(m)}
    bridges = {m for m in business
               if mods[m]['auto_install'] and len(mods[m]['depends']) >= 2}
    rev = collections.Counter()
    for m, v in mods.items():
        for d in v['depends']:
            rev[d] += 1

    print(f'modules           {len(mods)}')
    print(f'  localisations   {sum(1 for m in mods if m.startswith("l10n_"))}')
    print(f'  test harnesses  {sum(1 for m in mods if m.startswith("test_"))}')
    print(f'  business        {len(business)}')
    print(f'  bridges         {len(bridges)}  ({len(bridges)/len(business):.0%} of business modules)')
    print('\nmost depended upon:')
    for m, c in rev.most_common(8):
        print(f'  {c:4d}  {m}')
    print('\napp dependency closures (smaller is cheaper to copy):')
    apps = sorted((len(closure(mods, m)), m) for m, v in mods.items() if v['application'])
    for n, m in apps[:10]:
        print(f'  {n:4d}  {m}')

    if a.json:
        json.dump({'modules': mods, 'bridges': sorted(bridges)},
                  open(a.json, 'w'), indent=1)
        print(f'\nwrote {a.json}')

if __name__ == '__main__':
    main()
