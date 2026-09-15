#!/usr/bin/env python3
"""Decide whether a model is structurally core, from the Odoo source.

A worksheet is core only if Odoo enforces it with required=True from a model
that is itself core, or the concept is unrepresentable without it. This script
answers the first half: it finds every required=True Many2one pointing at the
given models, and says which module declares it.

    python3 nocoly/tools/verify_core.py
    python3 nocoly/tools/verify_core.py account.tax product.category

Beware two false positives the plan had to correct for by hand:
  * self-references — account.payment.term.line.payment_id requires its own parent
  * references from optional features — account.fiscal.position.account requires
    account.account, but fiscal positions are themselves an optional bundle
"""
import collections, glob, os, re, sys

DEFAULT = [
    'res.partner', 'uom.uom', 'product.template', 'product.product',
    'account.journal', 'account.move', 'account.move.line',
    'account.tax', 'account.account', 'product.category',
    'account.payment.term', 'account.payment.method', 'account.payment',
    'mail.activity.type', 'res.country', 'res.currency',
]
FIELD = re.compile(r'(\w+)\s*=\s*fields\.Many2one\((.{0,600}?)\)\s*\n', re.S)

def scan(targets, repo='.'):
    hits = collections.defaultdict(set)
    files = (glob.glob(os.path.join(repo, 'addons/*/models/**/*.py'), recursive=True)
             + glob.glob(os.path.join(repo, 'odoo/addons/base/models/*.py')))
    for f in files:
        parts = f.split(os.sep)
        mod = parts[parts.index('addons') + 1] if 'addons' in parts else 'base'
        if mod.startswith('l10n_') or mod.startswith('test_'):
            continue
        try:
            src = open(f, encoding='utf-8', errors='ignore').read()
        except OSError:
            continue
        for block in re.split(r'\nclass ', src):
            own = re.search(r"_(?:name|inherit)\s*=\s*['\"]([a-z0-9_.]+)['\"]", block)
            own = own.group(1) if own else '?'
            for m in FIELD.finditer(block):
                body = m.group(2)
                tgt = re.search(r"['\"]([a-z0-9_.]+)['\"]", body)
                if tgt and tgt.group(1) in targets and 'required=True' in body:
                    hits[tgt.group(1)].add(f'{own}.{m.group(1)}  [{mod}]')
    return hits

def main():
    targets = sys.argv[1:] or DEFAULT
    hits = scan(set(targets))
    width = max(len(t) for t in targets)
    for t in targets:
        rows = sorted(hits.get(t, ()))
        verdict = 'CORE ' if rows else 'check'
        print(f'[{verdict}] {t:<{width}}  ' + ('; '.join(rows[:3]) if rows else '— no required=True reference —'))
    print('\nA "check" result means nothing in the source forces it to exist.')
    print('That makes it a feature bundle, however much you want it on day one.')

if __name__ == '__main__':
    main()
