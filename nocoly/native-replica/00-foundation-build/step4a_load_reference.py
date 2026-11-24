"""Wave 0, step 4a: load the reference data into Currencies, Currency Rates, Countries and Country Groups.

Re-runnable: rows whose key already exists are skipped. Large sets go with --single-request, which only answers a
count, so every sheet is read back afterwards (count, relations, options, region values).
Countries get the native Region value (country-level id = ISO code) only when Nocoly's region list has that code.
Run: python step4a_load_reference.py [currencies rates countries groups]
"""
import csv, json, os, sys
from concurrent.futures import ThreadPoolExecutor
from lib import hap, APP

HERE = os.path.dirname(os.path.abspath(__file__))
WS = {'currencies': '<id>', 'rates': '<id>',
      'countries': '<id>', 'groups': '<id>', 'industries': '<id>'}
POS = {'after': 'After Amount', 'before': 'Before Amount'}
ZIP = {'required': 'Required', 'optional': 'Optional', 'not_applicable': 'Not Applicable'}
NAMEPOS = {'before': 'Before Address', 'after': 'After Address'}


def data(name):
    return list(csv.DictReader(open(os.path.join(HERE, 'data', name + '.csv'), encoding='utf-8')))


def rows_of(ws, *fields):
    out, page = [], 1
    while True:
        args = ['worksheet', 'record', 'list', ws, '-a', APP, '-n', '1000', '-p', str(page)]
        for f in fields:
            args += ['--fields', f]
        batch = hap(*args)['data']['rows']
        out += batch
        if len(batch) < 1000:
            return out
        page += 1


def create(ws, rows):
    """Chunks under ~20k characters of JSON (Windows command-line limit), one request per chunk."""
    chunk, size, written = [], 0, 0
    for r in rows + [None]:
        s = len(json.dumps(r, ensure_ascii=False)) if r else 0
        if r is None or (chunk and size + s > 20000):
            if chunk:
                res = hap('worksheet', 'record', 'batch-create', ws, '-a', APP, '--rows',
                          json.dumps(chunk, ensure_ascii=False), '--single-request')
                written += res.get('written', 0)
            chunk, size = [], 0
        if r:
            chunk.append(r)
            size += s
    return written


def rel_id(v):
    """Row id held by a relation cell in a record list."""
    if isinstance(v, str):
        try:
            v = json.loads(v)
        except ValueError:
            return v
    if isinstance(v, list) and v:
        v = v[0]
    return v.get('sid') or v.get('rowid') or v.get('rowId') if isinstance(v, dict) else v


def load_currencies():
    have = {r.get('name') for r in rows_of(WS['currencies'], 'name')}
    rows = [{'name': c['name'], 'full_name': c['full_name'], 'symbol': c['symbol'], 'active': c['active'] == 't',
             'decimal_places': int(c['decimal_places'] or 0), 'rounding': float(c['rounding'] or 0),
             'position': POS.get(c['position'], ''), 'currency_unit_label': c['currency_unit_label'],
             'currency_subunit_label': c['currency_subunit_label'],
             **({'iso_numeric': int(c['iso_numeric'])} if c['iso_numeric'] else {})}
            for c in data('currencies') if c['name'] not in have]
    return create(WS['currencies'], rows)


def currency_ids():
    return {r['name']: r['rowId'] for r in rows_of(WS['currencies'], 'name')}


def load_rates():
    cur = currency_ids()
    have = {(rel_id(r.get('currency_id')), (r.get('name') or '')[:10]) for r in rows_of(WS['rates'], 'name', 'currency_id')}
    rows = [{'name': r['date'], 'currency_id': cur[r['currency']], 'rate': float(r['rate'])}
            for r in data('currency_rates') if r['currency'] in cur and (cur[r['currency']], r['date']) not in have]
    return create(WS['rates'], rows)


def region_ok(code):
    d = hap('region', 'get', '--id', code, '-a', APP, ok_fail=True)
    regs = ((d or {}).get('data') or {}).get('regions') or []
    return code if any(x.get('id') == code for x in regs) else None


def load_countries():
    cur = currency_ids()
    have = {r.get('code') for r in rows_of(WS['countries'], 'code')}
    todo = [c for c in data('countries') if c['code'] not in have]
    # All 251 codes were looked up one by one on 23 Nov 2026: only XI and XK are missing from Nocoly's region list.
    # No parallel lookups (Module Owner: no parallel work); use region_ok(code) again only for codes not seen before.
    NOT_IN_REGION_LIST = {'XI', 'XK'}
    valid = {c['code']: (None if c['code'] in NOT_IN_REGION_LIST else c['code']) for c in todo}
    missing = sorted(k for k, v in valid.items() if not v)
    rows = []
    for c in todo:
        r = {'name': c['name'], 'code': c['code'], 'vat_label': c['vat_label'], 'state_required': c['state_required'] == 't',
             'zip_applicability': ZIP.get(c['zip_applicability'], ''), 'name_position': NAMEPOS.get(c['name_position'], ''),
             'address_format': c['address_format']}
        if c['phone_code']:
            r['phone_code'] = int(c['phone_code'])
        if c['currency'] in cur:
            r['currency_id'] = cur[c['currency']]
        if valid.get(c['code']):
            r['x_base__region'] = c['code']
        rows.append(r)
    return create(WS['countries'], rows), missing


def load_groups():
    ids = {r['code']: r['rowId'] for r in rows_of(WS['countries'], 'code')}
    have = {r.get('name') for r in rows_of(WS['groups'], 'name')}
    rows = [{'name': g['name'], 'code': g['code'], 'country_ids': [ids[c] for c in g['countries'].split() if c in ids]}
            for g in data('country_groups') if g['name'] not in have]
    return create(WS['groups'], rows)


if __name__ == '__main__':
    todo = sys.argv[1:] or ['currencies', 'rates', 'countries', 'groups']
    if 'currencies' in todo:
        print('currencies written', load_currencies(), '-> now', len(rows_of(WS['currencies'], 'name')))
    if 'rates' in todo:
        print('rates written', load_rates(), '-> now', len(rows_of(WS['rates'], 'name')))
    if 'countries' in todo:
        n, missing = load_countries()
        print('countries written', n, '-> now', len(rows_of(WS['countries'], 'code')), '; codes not in the native region list:', missing)
    if 'groups' in todo:
        print('groups written', load_groups(), '-> now', len(rows_of(WS['groups'], 'name')))


def load_industries():
    have = {r.get('name') for r in rows_of(WS['industries'], 'name')}
    rows = [{'name': r['name'], 'full_name': r['full_name'], 'active': r['active'] == 't'}
            for r in data('industries') if r['name'] not in have]
    return create(WS['industries'], rows)


if __name__ == '__main__' and 'industries' in sys.argv[1:]:
    print('industries written', load_industries(), '-> now', len(rows_of(WS['industries'], 'name')))
