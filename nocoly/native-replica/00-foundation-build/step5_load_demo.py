"""Wave 0, step 3 of §9 (demo part): load data/demo.json (from step3_export_demo.py) into the app.

Order follows the references: contacts -> company -> attributes + values -> products -> attribute lines -> PTAVs ->
variants -> combos -> pricelists + rules -> activity type links -> activity plans + steps.
Fields that workflows will maintain (display names, commercial fields, keys, variant prices, rule helpers) are
computed here the same way, so the flows start from consistent data. Each part is skipped when its sheet already
holds rows. Prices are loaded as MYR amounts (decision 3); pricelist currencies stay as in Odoo.

Key formats (the #8 variant flow uses the same):
- PTAV Key = "<product row id>|<attribute value row id>";
- variant Combination Key = "|<value row id>" for each value, in line creation order ("" for a product without lines).
Run: python step5_load_demo.py
"""
import json, os, re
from lib import hap, APP
from sheetlib import sheets_by_alias
from step4a_load_reference import rows_of

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, 'data', 'demo.json'), encoding='utf-8'))
S = {k: v['id'] for k, v in sheets_by_alias().items()}
IDS = {}          # (kind, odoo id) -> HAP row id

TYPE = {'contact': 'Contact', 'invoice': 'Invoice Address', 'delivery': 'Delivery Address', 'other': 'Other Address'}
LANG = {'en_US': 'English'}
PTYPE = {'consu': 'Goods', 'service': 'Service', 'combo': 'Combo'}
CREATE = {'always': 'Instantly', 'dynamic': 'Dynamically', 'no_variant': 'Never'}
DISPLAY = {'radio': 'Radio', 'pills': 'Pills', 'select': 'Select', 'color': 'Color', 'multi': 'Multi-checkbox'}
APPLIED = {'3_global': 'All Products', '2_product_category': 'Product Category', '1_product': 'Product', '0_product_variant': 'Product Variant'}
RANK = {'0_product_variant': 0, '1_product': 1, '2_product_category': 2, '3_global': 3}
COMPUTE = {'discount': 'Discount', 'markup': 'Surcharge', 'fixed': 'Fixed Price'}
BASE = {'list_price': 'Sales Price', 'standard_price': 'Cost', 'pricelist': 'Other Pricelist'}
RESP = {'on_demand': 'Ask at launch', 'other': 'Specific User', 'role': 'Role', 'manager': 'Manager', 'employee': 'Employee'}
DFROM = {'before_plan_date': 'Before Plan Date', 'after_plan_date': 'After Plan Date'}
MODEL = {'hr.employee': 'Employees', 'res.partner': 'Contacts', 'product.template': 'Products', 'product.product': 'Variants'}
DIAL = {'US': '1', 'SM': '378', 'BE': '32', 'MY': '60'}


def batch(ws, rows):
    """Create rows (one request each) and return their row ids in order."""
    ids = []
    for i in range(0, len(rows), 20):
        out = hap('worksheet', 'record', 'batch-create', ws, '-a', APP, '--rows', json.dumps(rows[i:i + 20], ensure_ascii=False))
        bad = [r for r in out.get('results', []) if r.get('resultCode') != 1]
        if bad or len(out.get('rowIds', [])) != len(rows[i:i + 20]):
            raise RuntimeError(f'batch-create on {ws}: {json.dumps(bad or out, ensure_ascii=False)[:600]}')
        ids += out['rowIds']
    return ids


def update(ws, rid, vals):
    return hap('worksheet', 'record', 'update', ws, rid, '-a', APP, '--ignore-rules',
               '--fields-json', json.dumps([{'id': k, 'value': v} for k, v in vals.items()], ensure_ascii=False))


def keyed(ws, key='name'):
    return {r.get(key): r['rowId'] for r in rows_of(ws, key)}


def phone(p, country):
    if not p:
        return None
    digits = re.sub(r'[^\d+]', '', p)
    if digits.startswith('+'):
        return digits
    return '+' + DIAL.get(country or 'US', '1') + digits


def region(country, state):
    if not country:
        return None
    return f'{country}|{country}-{state}' if state else country


def load_contacts():
    ws = S['res_partner']
    if rows_of(ws, 'name'):
        print('contacts: already loaded'); return
    countries = keyed(S['res_country'], 'code')
    industries = keyed(S['res_partner_industry'])
    main = D['company'][0]['partner']
    def row(c):
        r = {'name': c['name'], 'complete_name': c['complete_name'], 'company_type': ['Company' if c['is_company'] or c['oid'] == main else 'Person'],
             'type': [TYPE.get(c['type'], 'Contact')], 'function': c['function'], 'email': c['email'],
             'website': c['website'], 'street': c['street'], 'street2': c['street2'], 'zip': c['zip'], 'city': c['city'],
             'vat': c['vat'], 'ref': c['ref'], 'lang': [LANG.get(c['lang'], 'English')], 'comment': c['comment'],
             'employee': bool(c['employee']), 'barcode': c['barcode'], 'active': c['active'] is not False,
             'commercial_company_name': c['commercial_company_name']}
        ph = phone(c['phone'], c['country'])
        if ph:
            r['phone'] = ph
        reg = region(c['country'], c['state'])
        if reg:
            r['x_base__region'] = reg
        if c['country'] in countries:
            r['country_id'] = [countries[c['country']]]
        if c['industry'] in industries:
            r['industry_id'] = [industries[c['industry']]]
        if c['tags']:
            r['category_id'] = c['tags']
        return {k: v for k, v in r.items() if v not in (None, '', [])}
    tops = [c for c in D['contacts'] if not c['parent']]
    for c, rid in zip(tops, batch(ws, [row(c) for c in tops])):
        IDS[('partner', c['oid'])] = rid
    kids = [c for c in D['contacts'] if c['parent']]
    rows = []
    for c in kids:
        r = row(c)
        r['parent_id'] = [IDS[('partner', c['parent'])]]
        rows.append(r)
    for c, rid in zip(kids, batch(ws, rows)):
        IDS[('partner', c['oid'])] = rid
    for c in D['contacts']:                                   # commercial entity (#2), now that all ids exist
        update(ws, IDS[('partner', c['oid'])], {'commercial_partner_id': [IDS[('partner', c['commercial'])]]})
    print('contacts:', len(D['contacts']))


def load_company():
    ws = S['res_company']
    if rows_of(ws, 'name'):
        print('company: already loaded'); return
    co = D['company'][0]
    partner = keyed(S['res_partner']).get(next(c['name'] for c in D['contacts'] if c['oid'] == co['partner']))
    myr = keyed(S['res_currency'])['MYR']
    batch(ws, [{'name': co['name'], 'partner_id': [partner], 'currency_id': [myr]}])
    print('company:', co['name'], '(currency MYR, decision 3)')


def load_attributes():
    aws, vws = S['product_attribute'], S['product_attribute_value']
    if rows_of(aws, 'name'):
        for a, rid in keyed(aws).items():
            pass
        print('attributes: already loaded'); return
    attrs = D['attributes']
    for a, rid in zip(attrs, batch(aws, [{'name': a['name'], 'create_variant': [CREATE[a['create_variant']]],
                                          'display_type': [DISPLAY.get(a['display_type'], 'Radio')],
                                          'sequence': a['sequence'] or 0, 'active': a['active'] is not False} for a in attrs])):
        IDS[('attribute', a['oid'])] = rid
    vals = [(a, v) for a in attrs for v in (a['values'] or [])]
    rows = [{k: x for k, x in {'name': v['name'], 'html_color': v['html_color'], 'is_custom': bool(v['is_custom']),
                               'default_extra_price': v['default_extra_price'] or 0, 'sequence': v['sequence'] or 0,
                               'active': v['active'] is not False, 'attribute_id': [IDS[('attribute', a['oid'])]]}.items()
             if x not in (None, '')} for a, v in vals]
    for (a, v), rid in zip(vals, batch(vws, rows)):
        IDS[('value', v['oid'])] = rid
    print('attributes:', len(attrs), 'values:', len(vals))


def variant_name(code, name, values):
    return (f'[{code}] ' if code else '') + name + (f" ({', '.join(values)})" if values else '')


def load_products():
    pws = S['product_template']
    if rows_of(pws, 'name'):
        print('products: already loaded'); return
    categs = keyed(S['product_category'], 'complete_name')
    units = keyed(S['uom_uom'])
    vname = {v['oid']: v['name'] for a in D['attributes'] for v in (a['values'] or [])}
    aseq = {a['oid']: (a['sequence'] or 0) for a in D['attributes']}
    prods = D['products']
    rows = []
    for p in prods:
        r = {'name': p['name'], 'type': [PTYPE[p['type']]], 'is_storable': bool(p['is_storable']), 'list_price': p['list_price'] or 0,
             'default_code': p['default_code'], 'barcode': p['barcode'], 'sale_ok': bool(p['sale_ok']),
             'purchase_ok': bool(p['purchase_ok']), 'uom_id': [units[p['uom']]], 'description': p['description'],
             'description_sale': p['description_sale'], 'description_purchase': p['description_purchase'],
             'weight': p['weight'] or 0, 'volume': p['volume'] or 0, 'sequence': p['sequence'] or 0, 'active': p['active'] is not False}
        if p['is_favorite']:
            r['is_favorite'] = 1
        if p['categ'] in categs:
            r['categ_id'] = [categs[p['categ']]]
        if p['uoms']:
            r['uom_ids'] = [units[u] for u in p['uoms'] if u in units]
        if len(p['variants'] or []) == 1:                    # Odoo shows a single variant's cost on the product
            r['standard_price'] = p['variants'][0]['standard_price'] or 0
        rows.append({k: v for k, v in r.items() if v not in (None, '', [])})
    for p, rid in zip(prods, batch(pws, rows)):
        IDS[('product', p['oid'])] = rid
    # attribute lines (subform rows: the back relation Product links them)
    lws = S['product_template_attribute_line']
    lines = [(p, l) for p in prods for l in sorted(p['lines'] or [], key=lambda l: (l['sequence'] or 0, l['oid']))]
    attr_name = {a['oid']: a['name'] for a in D['attributes']}
    lrows = [{'x_product__label': f"{attr_name[l['attribute']]}: {', '.join(vname[v] for v in l['values'])}",
              'attribute_id': [IDS[('attribute', l['attribute'])]], 'value_ids': [IDS[('value', v)] for v in l['values']],
              'sequence': l['sequence'] or 0, 'active': l['active'] is not False,
              'product_tmpl_id': [IDS[('product', p['oid'])]]} for p, l in lines]
    for (p, l), rid in zip(lines, batch(lws, lrows)):
        IDS[('line', l['oid'])] = rid
    # PTAVs
    tws = S['product_template_attribute_value']
    line_attr = {l['oid']: l['attribute'] for p in prods for l in (p['lines'] or [])}
    ptavs = [(p, t) for p in prods for t in (p['ptavs'] or [])]
    trows = []
    for p, t in ptavs:
        pid, vid = IDS[('product', p['oid'])], IDS[('value', t['value'])]
        trows.append({'name': vname[t['value']], 'product_tmpl_id': [pid], 'product_attribute_value_id': [vid],
                      'attribute_id': [IDS[('attribute', line_attr[t['line']])]], 'attribute_line_id': [IDS[('line', t['line'])]],
                      'price_extra': t['price_extra'] or 0, 'ptav_active': t['active'] is not False,
                      'x_product__key': f'{pid}|{vid}', 'x_product__run': 'load', 'sequence': t['sequence'] or 0})
    ptav_val = {}
    for (p, t), rid in zip(ptavs, batch(tws, trows)):
        IDS[('ptav', t['oid'])] = rid
        ptav_val[t['oid']] = t
    # variants
    xws = S['product_product']
    line_order = {l['oid']: i for p in prods for i, l in enumerate(sorted(p['lines'] or [], key=lambda l: (l['sequence'] or 0, l['oid'])))}
    vars_ = [(p, v) for p in prods for v in (p['variants'] or [])]
    xrows = []
    for p, v in vars_:
        ts = sorted((ptav_val[t] for t in (v['ptavs'] or [])), key=lambda t: line_order[t['line']])
        extra = sum(t['price_extra'] or 0 for t in ts)
        r = {'display_name': variant_name(v['default_code'], p['name'], [vname[t['value']] for t in ts]),
             'product_tmpl_id': [IDS[('product', p['oid'])]],
             'product_template_attribute_value_ids': [IDS[('ptav', t['oid'])] for t in ts],
             'combination_indices': ''.join('|' + IDS[('value', t['value'])] for t in ts),
             'default_code': v['default_code'], 'barcode': v['barcode'], 'standard_price': v['standard_price'] or 0,
             'lst_price': round((p['list_price'] or 0) + extra, 2), 'weight': v['weight'] or 0, 'volume': v['volume'] or 0,
             'active': v['active'] is not False, 'x_product__run': 'load'}
        if v['is_favorite']:
            r['is_favorite'] = 1
        xrows.append({k: x for k, x in r.items() if x not in (None, '', [])} | {'combination_indices': r['combination_indices']})
    for (p, v), rid in zip(vars_, batch(xws, xrows)):
        IDS[('variant', v['oid'])] = rid
        IDS[('variant_name', v['oid'])] = None
    print('products:', len(prods), 'lines:', len(lines), 'ptavs:', len(ptavs), 'variants:', len(vars_))


def load_combos():
    cws, iws = S['product_combo'], S['product_combo_item']
    if rows_of(cws, 'name'):
        print('combos: already loaded'); return
    vnames = {r['rowId']: r.get('display_name') for r in rows_of(S['product_product'], 'display_name')}
    combos = D['combos']
    for c, rid in zip(combos, batch(cws, [{'name': c['name'], 'sequence': c['sequence'] or 0} for c in combos])):
        IDS[('combo', c['oid'])] = rid
    items = [(c, i) for c in combos for i in (c['items'] or [])]
    batch(iws, [{'product_id': [IDS[('variant', i['product'])]], 'x_product__label': vnames.get(IDS[('variant', i['product'])]),
                 'extra_price': i['extra_price'] or 0, 'combo_id': [IDS[('combo', c['oid'])]]} for c, i in items])
    for p in D['products']:
        if p['combos']:
            update(S['product_template'], IDS[('product', p['oid'])], {'combo_ids': [IDS[('combo', c)] for c in p['combos']]})
    print('combos:', len(combos), 'items:', len(items))


def load_pricelists():
    pws, rws = S['product_pricelist'], S['product_pricelist_item']
    if rows_of(pws, 'name'):
        print('pricelists: already loaded'); return
    cur = keyed(S['res_currency'])
    groups = keyed(S['res_country_group'])
    pls = D['pricelists']
    rows = []
    for p in pls:
        r = {'name': p['name'], 'currency_id': [cur[p['currency']]], 'sequence': p['sequence'] or 0, 'active': p['active'] is not False}
        g = [groups[n] for n in (p['country_groups'] or []) if n in groups]
        if g:
            r['country_group_ids'] = g
        rows.append(r)
    for p, rid in zip(pls, batch(pws, rows)):
        IDS[('pricelist', p['oid'])] = rid
    name = {p['oid']: p['name'] for p in pls}
    items = [(p, i) for p in pls for i in (p['items'] or [])]
    rrows = []
    for p, i in items:
        base = BASE[i['base'] or 'list_price']
        on = base if i['base'] != 'pricelist' else f"Other Pricelist ({name[i['base_pricelist']]})"
        if i['compute_price'] == 'fixed':
            price = f"{i['fixed_price'] or 0:.2f}"
        elif i['compute_price'] == 'markup':
            price = f"{-(i['price_discount'] or 0):g}% surcharge on {on}"
        else:
            price = f"{i['price_discount'] or 0:g}% discount on {on}"
        r = {'name': APPLIED[i['applied_on']], 'applied_on': [APPLIED[i['applied_on']]], 'min_quantity': i['min_quantity'] or 0,
             'compute_price': [COMPUTE[i['compute_price']]], 'base': [base], 'price_discount': i['price_discount'] or 0,
             'fixed_price': i['fixed_price'] or 0, 'price_round': i['price_round'] or 0, 'price_surcharge': i['price_surcharge'] or 0,
             'price_min_margin': i['price_min_margin'] or 0, 'price_max_margin': i['price_max_margin'] or 0, 'price': price,
             'pricelist_id': [IDS[('pricelist', p['oid'])]]}
        if i['compute_price'] == 'markup':
            r['price_markup'] = -(i['price_discount'] or 0)
        if i['base_pricelist']:
            r['base_pricelist_id'] = [IDS[('pricelist', i['base_pricelist'])]]
        if i['applied_on'] != '3_global':
            raise RuntimeError('demo rule targets are all global in Odoo 20 demo; extend the loader for others')
        rrows.append(r)
    rule_ids = batch(rws, rrows)
    for (p, i), rid in zip(items, rule_ids):                      # hidden helpers for the #12 rule search
        update(rws, rid, {'x_product__rank': RANK[i['applied_on']], 'x_product__target_key': 'ALL', 'x_product__categ_sort': 0,
                          'x_product__effective_start': (i['date_start'] or '1900-01-01 00:00:00')[:19],
                          'x_product__effective_end': (i['date_end'] or '2999-12-31 23:59:59')[:19]})
    # Chain (hidden): every pricelist reachable through "Other Pricelist", itself included, as #id#id#
    based = {p['oid']: {i['base_pricelist'] for i in (p['items'] or []) if i['base_pricelist']} for p in pls}
    for p in pls:
        seen, todo = [], [p['oid']]
        while todo:
            x = todo.pop(0)
            if x not in seen:
                seen.append(x)
                todo += sorted(based.get(x, ()))
        update(pws, IDS[('pricelist', p['oid'])], {'x_product__chain': '#' + '#'.join(IDS[('pricelist', x)] for x in seen) + '#'})
    print('pricelists:', len(pls), 'rules:', len(items))


def load_activity_config():
    tws = S['mail_activity_type']
    types = keyed(tws)
    import csv
    for r in csv.DictReader(open(os.path.join(HERE, 'data', 'activity_types.csv'), encoding='utf-8')):
        if r['xmlid'].startswith('mail.') and r['suggested_next'] and r['suggested_next'] in types:
            update(tws, types[r['name']], {'suggested_next_type_id': [types[r['suggested_next']]]})
    pws, sws = S['mail_activity_plan'], S['mail_activity_plan_template']
    if rows_of(pws, 'name'):
        print('plans: already loaded'); return
    plans = D['plans']
    pids = batch(pws, [{'name': p['name'], 'res_model': [MODEL.get(p['res_model'], 'Contacts')], 'active': p['active'] is not False}
                       for p in plans])
    steps = [(pid, s) for p, pid in zip(plans, pids) for s in (p['steps'] or [])]
    batch(sws, [{k: v for k, v in {'summary': s['summary'], 'activity_type_id': [types[s['type']]],
                                   'responsible_type': [RESP[s['responsible_type']]], 'delay_count': s['delay_count'] or 0,
                                   'delay_unit': [s['delay_unit']], 'delay_from': [DFROM[s['delay_from']]], 'note': s['note'],
                                   'sequence': s['sequence'] or 0, 'plan_id': [pid]}.items() if v not in (None, '')}
                for pid, s in steps])
    print('plans:', len(plans), 'steps:', len(steps))


if __name__ == '__main__':
    load_contacts()
    load_company()
    load_attributes()
    load_products()
    load_combos()
    load_pricelists()
    load_activity_config()
    json.dump({f'{k[0]}:{k[1]}': v for k, v in IDS.items() if v}, open(os.path.join(HERE, 'data', 'demo-ids.json'), 'w'), indent=0)
