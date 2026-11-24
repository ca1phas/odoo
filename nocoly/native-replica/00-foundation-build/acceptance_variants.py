"""Acceptance tests 6-8 (plan v1 §9): 3 x 3 variants, removing one value archives 3, a "Never" attribute adds none.
Everything is TEST data and is deleted at the end without triggering workflows.
Run: python acceptance_variants.py        (build and test)
     python acceptance_variants.py cleanup
"""
import json, sys, time
from lib import hap, APP
from wflib import S, option_key

P, L, A, AV, T, V, Q = ('product_template', 'product_template_attribute_line', 'product_attribute', 'product_attribute_value',
                        'product_template_attribute_value', 'product_product', 'x_product__variant_queue')
IDS = 'backups/test-variants9.json'
VALUES = {'colour': ['Red', 'Green', 'Blue'], 'size': ['S', 'M', 'L'], 'engraving': ['Yes', 'No']}


def create(sheet, fields):
    r = hap('worksheet', 'record', 'create', S[sheet], '-a', APP, '--ignore-rules', '--fields-json', json.dumps(fields))
    r = r.get('data', r)
    return r.get('rowid') or r.get('rowId')


def rows(sheet):
    out, page = [], 1
    while True:
        d = hap('worksheet', 'record', 'list', S[sheet], '-a', APP, '--page-size', '200', '--page', str(page))
        d = d.get('data', d)
        got = d.get('rows') or []
        out += got
        if len(got) < 200:
            return out
        page += 1


def sid(v):
    v = json.loads(v) if isinstance(v, str) and v.startswith('[') else v
    return v[0].get('sid') if isinstance(v, list) and v else None


def of_product(sheet, field, pid):
    return [r for r in rows(sheet) if sid(r.get(field)) == pid]


def status(r):
    return json.dumps(r.get('x_product__status'), ensure_ascii=False)


def active(r):
    return str(r.get('active')).lower() in ('1', 'true')


def wait_queue(pid, label, timeout=300):
    t0 = time.time()
    req = []
    while time.time() - t0 < timeout:
        time.sleep(10)
        req = of_product(Q, 'x_product__product_id', pid)
        if req and all('Done' in status(r) or 'Skipped' in status(r) for r in req):
            break
    variants = of_product(V, 'product_tmpl_id', pid)
    act = sorted(v.get('display_name') or '' for v in variants if active(v))
    arc = sorted(v.get('display_name') or '' for v in variants if not active(v))
    print(f'{label}: {len(req)} requests ({sum("Done" in status(r) for r in req)} Done, '
          f'{sum("Skipped" in status(r) for r in req)} Skipped), {len(act)} active, {len(arc)} archived')
    print('   active:', act)
    print('   archived:', arc)
    return act, arc


def main():
    ids = {}
    inst, never = option_key(A, 'create_variant', 'Instantly'), option_key(A, 'create_variant', 'Never')
    radio = option_key(A, 'display_type', 'Radio')
    for key, name, mode in (('colour', 'TEST Colour', inst), ('size', 'TEST Size', inst), ('engraving', 'TEST Engraving', never)):
        ids[key] = create(A, [{'id': 'name', 'value': name}, {'id': 'create_variant', 'value': mode},
                              {'id': 'display_type', 'value': radio}, {'id': 'active', 'value': '1'}])
    for key, names in VALUES.items():
        for i, n in enumerate(names):
            ids[f'{key}_{n}'] = create(AV, [{'id': 'name', 'value': n}, {'id': 'attribute_id', 'value': [ids[key]]},
                                            {'id': 'sequence', 'value': str(i + 1)}, {'id': 'active', 'value': '1'}])
    json.dump(ids, open(IDS, 'w'), indent=1)
    ids['product'] = create(P, [{'id': 'name', 'value': 'TEST Tee'}, {'id': 'list_price', 'value': '20'}, {'id': 'active', 'value': '1'}])
    json.dump(ids, open(IDS, 'w'), indent=1)
    wait_queue(ids['product'], 'New product')

    def line(key, values):
        return create(L, [{'id': 'product_tmpl_id', 'value': [ids['product']]}, {'id': 'attribute_id', 'value': [ids[key]]},
                          {'id': 'value_ids', 'value': [ids[f'{key}_{n}'] for n in values]}, {'id': 'active', 'value': '1'}])
    ids['line_colour'] = line('colour', VALUES['colour'])
    ids['line_size'] = line('size', VALUES['size'])
    json.dump(ids, open(IDS, 'w'), indent=1)
    wait_queue(ids['product'], 'TEST 6: Colour x Size')
    hap('worksheet', 'record', 'update', S[L], ids['line_size'], '-a', APP, '--ignore-rules', '--fields-json',
        json.dumps([{'id': 'value_ids', 'value': [ids['size_S'], ids['size_M']]}]))
    wait_queue(ids['product'], 'TEST 7: Size L removed')
    ids['line_engraving'] = line('engraving', VALUES['engraving'])
    json.dump(ids, open(IDS, 'w'), indent=1)
    wait_queue(ids['product'], 'TEST 8: Never attribute added')


def cleanup():
    ids = json.load(open(IDS))
    pid = ids.get('product')
    gone = {}
    if pid:
        for sheet, field in ((Q, 'x_product__product_id'), (V, 'product_tmpl_id'), (T, 'product_tmpl_id'), (L, 'product_tmpl_id'),
                             ('x_product__combination', 'x_product__product_id')):
            rs = [r['rowId'] for r in of_product(sheet, field, pid)]
            if rs:
                hap('worksheet', 'record', 'delete', S[sheet], '-a', APP, '-y', '--no-trigger-workflow', '--row-ids', ','.join(rs))
            gone[sheet] = len(rs)
        hap('worksheet', 'record', 'delete', S[P], '-a', APP, '-y', '--no-trigger-workflow', '--row-ids', pid)
    av = [ids[f'{k}_{n}'] for k, names in VALUES.items() for n in names if f'{k}_{n}' in ids]
    hap('worksheet', 'record', 'delete', S[AV], '-a', APP, '-y', '--no-trigger-workflow', '--row-ids', ','.join(av))
    hap('worksheet', 'record', 'delete', S[A], '-a', APP, '-y', '--no-trigger-workflow', '--row-ids',
        ','.join(ids[k] for k in VALUES if k in ids))
    print('deleted', gone, '| values', len(av), '| attributes', len([k for k in VALUES if k in ids]), '| product 1')


if __name__ == '__main__':
    cleanup() if 'cleanup' in sys.argv else main()
