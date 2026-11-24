"""Wave 0 (plan v2), step 3 of §9: load the remaining reference data (units, product categories, activity types).

Re-runnable: rows whose key already exists are skipped; relations and computed helper fields (factor, path, level,
ancestor keys) are then written for every row, from HAP record ids, so they match what workflows #7 and #10 will
maintain. The data is loaded before the workflows exist and matches Odoo's computed values.
Run: python step5_load_data.py [units categories activity_types]
"""
import json, sys
from lib import hap, APP
from sheetlib import sheets_by_alias
from step4a_load_reference import data, rows_of, create

WS = {k: v['id'] for k, v in sheets_by_alias().items()}


def update(ws, rid, vals):
    # record update refuses --no-workflow ("workflows cannot be suppressed for this write"); none exist yet.
    # --ignore-rules: hidden helper fields are refused otherwise ("not shown on the form, so it cannot be written").
    return hap('worksheet', 'record', 'update', ws, rid, '-a', APP, '--ignore-rules',
               '--fields-json', json.dumps([{'id': k, 'value': v} for k, v in vals.items()], ensure_ascii=False))


def chain(name, parent_of):
    """Names from the top of the chain down to `name`."""
    out = [name]
    while parent_of.get(out[0]):
        out.insert(0, parent_of[out[0]])
    return out


def load_units():
    ws = WS['uom_uom']
    src = data('units')
    have = {r.get('name') for r in rows_of(ws, 'name')}
    rows = [{'name': u['name'], 'relative_factor': float(u['relative_factor']), 'factor': float(u['factor']),
             'active': u['active'] == 't', 'sequence': int(u['sequence'])} for u in src if u['name'] not in have]
    written = create(ws, rows)
    ids = {r['name']: r['rowId'] for r in rows_of(ws, 'name')}
    parent_of = {u['name']: u['relative_uom'] for u in src}
    for u in src:
        names = chain(u['name'], parent_of)
        p = u['relative_uom']
        update(ws, ids[u['name']], {
            'relative_uom_id': [ids[p]] if p else [], 'x_uom__last_valid_uom_id': [ids[p]] if p else [],
            'parent_path': '/' + '/'.join(ids[n] for n in names) + '/', 'x_uom__level': len(names)})
    return written, len(ids)


def load_categories():
    ws = WS['product_category']
    src = [c for c in data('product_categories') if c['xmlid'].startswith('product.')]   # rows owned by `product`
    have = {r.get('name') for r in rows_of(ws, 'name')}
    written = create(ws, [{'name': c['name'], 'complete_name': c['complete_name']} for c in src if c['name'] not in have])
    ids = {r['name']: r['rowId'] for r in rows_of(ws, 'name')}
    parent_of = {c['name']: c['parent'] for c in src}
    for c in src:
        names = chain(c['name'], parent_of)
        anc = [ids[n] for n in reversed(names)]                      # itself first, then its parents
        vals = {'parent_id': [ids[c['parent']]] if c['parent'] else [],
                'x_product__last_valid_parent_id': [ids[c['parent']]] if c['parent'] else [],
                'complete_name': c['complete_name'], 'parent_path': '/' + '/'.join(ids[n] for n in names) + '/'}
        for i in range(1, 6):
            vals[f'x_product__ancestor_{i}'] = anc[i - 1] if i <= len(anc) else ''
        update(ws, ids[c['name']], vals)
    return written, len(ids)


if __name__ == '__main__':
    todo = sys.argv[1:] or ['units', 'categories']
    if 'units' in todo:
        print('units written %s, now %s' % load_units())
    if 'categories' in todo:
        print('categories written %s, now %s' % load_categories())
