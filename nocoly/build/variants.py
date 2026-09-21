#!/usr/bin/env python3
"""Build the Product Variants worksheet (Odoo product.product, as on casimir.odoo.com saas~19.4) in ERP Master.

    ~/.hap-venv/bin/python nocoly/build/variants.py create       # 0. worksheet in menu group Products, after Products
    ~/.hap-venv/bin/python nocoly/build/variants.py fields       # 1. the variant's own controls and tabs (fresh worksheet only)
    ~/.hap-venv/bin/python nocoly/build/variants.py relations    # 2. Product and Extra Packagings, one-way
    ~/.hap-venv/bin/python nocoly/build/variants.py lookups      # 3. Name, Product Type, Unit, Sales, Purchase, Sales Price
    ~/.hap-venv/bin/python nocoly/build/variants.py display      # 4. Display Name "[Internal Reference] Name" as the title
    ~/.hap-venv/bin/python nocoly/build/variants.py layout       # 5. positions, tabs, permissions, descriptions, pickers
    ~/.hap-venv/bin/python nocoly/build/variants.py rules        # 6. Sales / Inventory tab visibility, as on Products
    ~/.hap-venv/bin/python nocoly/build/variants.py views        # 7. Product Variants and Archived tables
    ~/.hap-venv/bin/python nocoly/build/variants.py buttons      # 8. Archive / Unarchive, with the product cascade
    ~/.hap-venv/bin/python nocoly/build/variants.py automations  # 9. product -> variant workflows A, B, C
    ~/.hap-venv/bin/python nocoly/build/variants.py switches     # 10. no Create, Duplicate or Re-create (Odoo create/duplicate False)
    ~/.hap-venv/bin/python nocoly/build/variants.py seed         # 11. one variant per product (upsert), then verify
    ~/.hap-venv/bin/python nocoly/build/variants.py verify       # compare every variant with its product and the extract
    ~/.hap-venv/bin/python nocoly/build/variants.py order        # each view's records, in the order the view sorts them
    ~/.hap-venv/bin/python nocoly/build/variants.py variant "[CONS-0002] Whiteboard Marker Set"   # live values by Display Name
    ~/.hap-venv/bin/python nocoly/build/variants.py raw <rowid>  # one variant as `record get` returns it
    ~/.hap-venv/bin/python nocoly/build/variants.py show         # print the live control list

Requirements: nocoly/worksheets/04-product-variants.md. Generic helpers: common.py.
"""
import json, os, re, sys, time
from decimal import Decimal

import common as C
import hap

APP = hap.ids()['app']
SECTION, WORKSHEET, PRODUCTS, UNITS = 'Products', 'Product Variants', 'Products', 'Units & Packagings'
KEY = WORKSHEET + ': '                         # ids.json key prefix for everything this worksheet owns


def ws():
    return hap.ids()['worksheets'][WORKSHEET]


def products_ws():
    return hap.ids()['worksheets'][PRODUCTS]


def units_ws():
    return hap.ids()['worksheets'][UNITS]


# Odoo saas~19.4 product.product form (the template form, product_normal_form_view) on HAP's 12-column grid.
# Header: the name (here the Product relation), Favorite with Sales and Purchase, the image, then the notebook.
# HAP draws fields outside tabs above the tab bar, so Display Name, Active and Name sit there too.
GENERAL, SALES, INVENTORY = 'General Information', 'Sales', 'Inventory'
TAB_ROWS = {GENERAL: 4, SALES: 8, INVENTORY: 10}
PLACE = {  # field name -> (row, col, size, tab)
    'Product': (0, 0, 12, None),
    'Favorite': (1, 0, 4, None), 'Sales': (1, 1, 4, None), 'Purchase': (1, 2, 4, None),
    'Variant Image': (2, 0, 12, None),
    'Display Name': (3, 0, 12, None),
    'Product Type': (5, 0, 6, GENERAL), 'Sales Price': (5, 1, 6, GENERAL),
    'Unit': (6, 0, 6, GENERAL), 'Cost': (6, 1, 6, GENERAL),
    'Internal Reference': (7, 0, 6, GENERAL), 'Barcode': (7, 1, 6, GENERAL),
    'Extra Packagings': (9, 0, 12, SALES),
    'Weight': (11, 0, 6, INVENTORY), 'Volume': (11, 1, 6, INVENTORY),
    'Active': (12, 0, 6, None), 'Name': (12, 1, 6, None),
}
FROM_PRODUCT = 'Copied from the product — edit it there. Read-only on the variant while each product has one variant.'
DESC = {  # Odoo field help (product_product.py, 19.4 fields_get), and where a value comes from
    'Product': 'The product this is a variant of. Set when the variant is created with its product; read-only, '
               'as on the Odoo variant form. Odoo product_tmpl_id.',
    'Internal Reference': FROM_PRODUCT,
    'Barcode': 'International Article Number used for product identification.',
    'Cost': 'Value of the product (automatically computed in AVCO).\n'
            'Used to value the product when the purchase cost is not known (e.g. inventory adjustment).\n'
            'Used to compute margins on sale orders.\n' + FROM_PRODUCT,
    'Weight': FROM_PRODUCT, 'Volume': FROM_PRODUCT,
    'Extra Packagings': 'Variant-specific additional packagings for this product which can be used for sales',
    'Active': 'If unchecked, it will allow you to hide the product without removing it.',
    'Name': "The product's Name, a stored lookup read by Display Name and the views' sort.",
    'Product Type': "The product's Product Type — edit it on the product.",
    'Unit': "The product's Unit — edit it on the product.",
    'Sales': "The product's Sales flag — edit it on the product.",
    'Purchase': "The product's Purchase flag — edit it on the product.",
    'Sales Price': "The product's Sales Price — edit it on the product. Price extras per attribute value come with "
                   'the Product Variants bundle.',
    'Display Name': 'How this variant appears in lists and pickers: [Internal Reference] Name, or the Name alone '
                    'when there is no Internal Reference. Odoo display_name.',
    'Favorite': "The product's Favorite — edit it on the product. Odoo relates the two "
                "(is_favorite = product_tmpl_id.is_favorite).",
}
READONLY = ['Product', 'Internal Reference', 'Cost', 'Weight', 'Volume', 'Favorite']   # the product is their master
HIDDEN = ['Active', 'Name']
MYR = json.dumps({'currencycode': 'MYR', 'symbol': 'RM'})


def ctl(kind, name, alias='', **kw):
    row, col, size, _ = PLACE[name]
    return C.control(kind, name, (row, col, size), alias=alias, hint='', desc=DESC.get(name),   # '' = no placeholder
                     hidden=name in HIDDEN, readonly=name in READONLY, **kw)


def tabs(ctrls):
    return {c['controlName']: c for c in ctrls if c['type'] == C.TAB}


SIGNATURE = ('controlName', 'type', 'alias', 'row', 'col', 'size', 'sectionId', 'required', 'attribute', 'unique',
             'fieldPermission', 'dataSource', 'sourceControlId', 'showControls', 'advancedSetting', 'desc', 'hint')


def signatures():
    """Products' and Units & Packagings' controls, by id (a full save elsewhere can reorder their listing)."""
    return {name: sorted(json.dumps([c['controlId']] + [c.get(k) for k in SIGNATURE], sort_keys=True,
                                    ensure_ascii=False) for c in hap.controls(wid))
            for name, wid in ((PRODUCTS, products_ws()), (UNITS, units_ws()))}


def check_untouched(before):
    after = signatures()
    for name in before:
        if after[name] != before[name]:
            sys.exit(f'{name} controls changed: {sorted(set(after[name]) ^ set(before[name]))}')
        print(f'  {name}: controls unchanged ({len(after[name])})')


def save_all(ctrls):
    """A full update-fields save of this worksheet, proving Products and Units & Packagings unchanged."""
    before = signatures()
    hap.run('worksheet', 'update-fields', ws(), '--controls', json.dumps(ctrls, ensure_ascii=False))
    check_untouched(before)


# ── 0 · worksheet ───────────────────────────────────────────────────────────

def step_create():
    section = hap.ids()['sections'][SECTION]
    wid = C.ensure_worksheet(APP, section, WORKSHEET, alias='product_product', icon='sys_15_10_barcode',
                             remark='Odoo product.product: the sellable variants of each product — one per product '
                                    'until the Product Variants bundle')
    C.remember('worksheets', WORKSHEET, wid)
    items = next(s for s in C.app_info(APP)['sections'] if s['id'] == section)['items']
    ids = [i['id'] for i in items]
    order = [products_ws(), wid] + [i for i in ids if i not in (products_ws(), wid)]   # Products, Variants, Units
    if order != ids:
        hap.run('app', 'sort-worksheets', APP, section, *order)
    for s in C.app_info(APP)['sections']:
        print(f"  {s['name']:<10} {s['id']}  {[(i['name'], i['id'], i.get('alias')) for i in s['items']]}")


# ── 1 · the variant's own controls ──────────────────────────────────────────

def switch(name, alias, default):
    return ctl('SWITCH', name, alias=alias, advanced_setting={'defsource': C.static_default(default)})


def number(name, alias, suffix):
    """2 decimals (Odoo 'Stock Weight' / 'Volume'), default 0, the unit as a suffix, as on Products."""
    return ctl('NUMBER', name, alias=alias, advanced_setting={'suffix': suffix, 'defsource': C.static_default(0)},
               extra={'dot': 2})


def step_fields():
    """One save on the fresh worksheet. The three stock controls are reused, none dropped: Name becomes
    Internal Reference (the title until Display Name exists), Description becomes Barcode, Attachment
    becomes Variant Image."""
    existing = hap.controls(ws())
    if len(existing) > 3:
        sys.exit(f'{WORKSHEET} already has {len(existing)} controls — refusing to replace them.')
    hap.backup('variants_controls_pre_fields', existing)
    stock = hap.by_name(existing)
    code = ctl('TEXT', 'Internal Reference', alias='default_code', is_title=True)
    code['controlId'] = stock['Name']['controlId']
    # Odoo _check_barcode_uniqueness: HAP's field-level No duplicates (an empty Barcode is not checked)
    barcode = ctl('TEXT', 'Barcode', alias='barcode', unique=True, extra={'enumDefault': 2})   # 2 = single line
    barcode['controlId'] = stock['Description']['controlId']
    image = ctl('ATTACHMENT', 'Variant Image', alias='image_variant_1920')
    image['controlId'] = stock['Attachment']['controlId']
    controls = [
        code, barcode, image,
        switch('Favorite', 'is_favorite', 0),
        C.control('SECTION', GENERAL, (TAB_ROWS[GENERAL], 0, 12)),
        ctl('MONEY', 'Cost', alias='standard_price', extra={'dot': 2},
            advanced_setting={'currency': MYR, 'defsource': C.static_default(0)}),
        C.control('SECTION', SALES, (TAB_ROWS[SALES], 0, 12)),
        C.control('SECTION', INVENTORY, (TAB_ROWS[INVENTORY], 0, 12)),
        number('Weight', 'weight', 'kg'), number('Volume', 'volume', 'm³'),
        switch('Active', 'active', 1),
    ]
    save_all(controls)
    C.show(ws())


# ── 2 · relations ───────────────────────────────────────────────────────────

def step_relations():
    """Product (product_tmpl_id) and Extra Packagings (extra_uom_ids): one-way, so neither Products nor
    Units & Packagings gets a reverse field."""
    f = C.fields(ws())
    new = [ctl('RELATE_SHEET', name, alias=alias, data_source=target, multi=multi, required=required,
               advanced_setting={'bidirectional': '0', 'showtype': '3'})                 # 3 = dropdown
           for name, alias, target, multi, required in [
               ('Product', 'product_tmpl_id', products_ws(), False, True),
               ('Extra Packagings', 'extra_uom_ids', units_ws(), True, False)]
           if name not in f]
    if new:
        before = signatures()
        C.append_controls(ws(), new)
        check_untouched(before)
    C.show(ws())


# ── 3 · lookups from the product ────────────────────────────────────────────

# Odoo's _inherits makes every template field readable on the variant. These six are the ones the form, the
# views and the display name need: (name, alias = Odoo field on product.product, the Products field, extra)
LOOKUPS = [
    ('Name', 'name', 'Name', {}),
    ('Product Type', 'type', 'Product Type', {}),
    ('Unit', 'uom_id', 'Unit', {}),
    ('Sales', 'sale_ok', 'Sales', {}),
    ('Purchase', 'purchase_ok', 'Purchase', {}),
    ('Sales Price', 'lst_price', 'Sales Price', {'dot': 2}),
]


def step_lookups():
    """Stored lookups ('00') through Product, so views can sort and filter on them and Display Name recomputes
    when the product changes. Added in one full save of the (still empty) worksheet, which mints their ids."""
    ctrls = hap.controls(ws())
    have = {c['controlName'] for c in ctrls if c['type'] != C.TAB}          # the Sales tab shares a lookup's name
    product, source = hap.by_name(ctrls)['Product'], C.fields(products_ws())
    new = []
    for name, alias, field, extra in LOOKUPS:
        if name in have:
            continue
        adv = {'currency': MYR} if name == 'Sales Price' else {}
        new.append(ctl('SHEET_FIELD', name, alias=alias, data_source=product['controlId'],
                       source_control_id=source[field]['controlId'], advanced_setting=adv,
                       extra={'strDefault': '00', **extra}))
    if new:
        hap.backup('variants_controls_pre_lookups', ctrls)
        save_all(ctrls + new)
    C.show(ws())


# ── 4 · Display Name ────────────────────────────────────────────────────────

def display_name_expression(f):
    """Odoo product.product _compute_display_name (product_product.py:816) without partner or seller context:
    "[default_code] name", or the name alone when there is no Internal Reference. The " (attribute values)"
    suffix waits for the Product Variants bundle. A number formula has no IF, so this is a function formula;
    TRIM as on Contacts (Odoo's web client strips what is typed)."""
    code, name = (f"${f[n]['controlId']}$" for n in ('Internal Reference', 'Name'))
    return f'IF(ISBLANK({code}),TRIM({name}),CONCAT("[",TRIM({code}),"] ",TRIM({name})))'


def function_source(expression):
    """dataSource of a function formula (type 53), as contacts.function_source."""
    return json.dumps({'type': 'mdfunction', 'expression': expression, 'status': 1}, ensure_ascii=False)


def step_display():
    """Display Name as the title field: a text function formula, read-only and hidden on create (not hidden: a
    hidden field never shows as a table column). Safe to re-run."""
    f = C.fields(ws())
    if 'Display Name' not in f:
        formula = ctl('FORMULA_FUNC', 'Display Name', alias='display_name',
                      advanced_setting={'analysislink': '1', 'sorttype': 'en'},
                      extra={'enumDefault2': 2, 'dataSource': function_source(display_name_expression(f))})
        # add-fields keeps the client-side id, under which a formula computes nothing; a full save re-mints it
        hap.run('worksheet', 'add-fields', ws(), '--controls', json.dumps([formula], ensure_ascii=False))
        save_all(hap.controls(ws()))
    ctrls = hap.controls(ws())
    hap.backup('variants_controls_pre_display', ctrls)
    f = hap.by_name(c for c in ctrls if c['type'] != C.TAB)
    display = f['Display Name']
    stale = []
    expression = display_name_expression(f)
    if json.loads(display.get('dataSource') or '{}').get('expression') != expression:
        display['dataSource'] = function_source(expression)
        stale.append('expression')
    permission = C.field_permission_str(readonly=True, hidden_on_create=True)          # "100"
    if (display.get('desc'), display.get('fieldPermission')) != (DESC['Display Name'], permission):
        display.update(desc=DESC['Display Name'], fieldPermission=permission)
        stale.append('description / permission')
    for c in ctrls:
        want = 1 if c['controlId'] == display['controlId'] else 0     # one title: Display Name
        if (c.get('attribute') or 0) != want:
            c['attribute'] = want
            stale.append(f"title {c['controlName']}")
    if stale:
        save_all(ctrls)
        print(f'  updated: {stale}')
    C.show(ws())


# ── 5 · layout ──────────────────────────────────────────────────────────────

def active_only(active):
    """Picker condition: the candidate's Active is checked (Odoo active_test)."""
    return {'controlId': active['controlId'], 'dataType': 36, 'spliceType': 1, 'filterType': C.EQ, 'values': ['1'],
            'value': '1', 'isDynamicsource': False, 'dynamicSource': []}


def not_the_unit(units, f):
    """Extra Packagings leave out the product's own Unit, as Products' Packagings do (Odoo domain
    [('id', '!=', uom_id)]). The variant has no Unit relation, only the Unit lookup, which stores the unit's
    name as text; so the candidate's Unit Name is compared with it. Unit names are distinct in the catalogue."""
    return {'controlId': units['Unit Name']['controlId'], 'dataType': 2, 'spliceType': 1, 'filterType': C.NE,
            'values': [], 'value': '', 'isDynamicsource': True,
            'dynamicSource': [{'rcid': '', 'cid': f['Unit']['controlId'], 'staticValue': '', 'isAsync': False}]}


def step_layout():
    ctrls = hap.controls(ws())
    hap.backup('variants_controls_pre_layout', ctrls)
    tab = {n: c['controlId'] for n, c in tabs(ctrls).items()}
    f = hap.by_name(c for c in ctrls if c['type'] != C.TAB)
    for c in ctrls:
        name = c['controlName']
        if c['type'] == C.TAB:
            c.update(row=TAB_ROWS[name], col=0, size=12, sectionId='')
            continue
        row, col, size, in_tab = PLACE[name]
        c.update(row=row, col=col, size=size, sectionId=tab[in_tab] if in_tab else '', hint='')
        if name in DESC:
            c['desc'] = DESC[name]
        c['fieldPermission'] = ('100' if name == 'Display Name' else '011' if name in HIDDEN
                                else '101' if name in READONLY else '111')
    units, products = C.fields(units_ws()), C.fields(products_ws())
    # Odoo's product dropdown shows "[Internal Reference] Name"; HAP's dropdown lists titles (the Name), and its
    # search also matches the picker's fields, so typing a reference finds the product.
    f['Product']['showControls'] = [products['Internal Reference']['controlId']]
    f['Product']['advancedSetting']['filters'] = json.dumps([active_only(products['Active'])])
    f['Extra Packagings']['showControls'] = [units['Contains']['controlId'], units['Reference Unit']['controlId']]
    f['Extra Packagings']['advancedSetting']['filters'] = json.dumps([active_only(units['Active']),
                                                                      not_the_unit(units, f)])
    save_all(ctrls)
    C.show(ws())


# ── 6 · rules ───────────────────────────────────────────────────────────────

def step_rules():
    """The variant form is the template form in Odoo, with its page attributes. Nothing is validated: Cost is
    read-only here (the negative-Cost onchange is moot) and Odoo only warns about a repeated Internal Reference."""
    ctrls = hap.controls(ws())
    f, tab = hap.by_name(c for c in ctrls if c['type'] != C.TAB), tabs(ctrls)
    service = next(o['key'] for o in C.fields(products_ws())['Product Type']['options'] if o['value'] == 'Service')
    rules = [  # (name, type, filters, items, options) — conditions on the stored lookups, evaluated in the form
        ('Sales tab only for products that can be sold', C.INTERACTION,        # page sales invisible="not sale_ok"
         C.any_of([C.cond(f['Sales'], C.NE, 1)]), [C.item(C.HIDE, tab[SALES])], {}),
        ('Inventory tab only for goods', C.INTERACTION,                         # page inventory invisible="type in ['service', 'combo']"
         C.any_of([C.cond(f['Product Type'], C.EQ, service)]), [C.item(C.HIDE, tab[INVENTORY])], {}),
    ]
    C.upsert_rules(ws(), rules, 'variants_rules_pre_rules')


# ── 7 · views ───────────────────────────────────────────────────────────────

def step_views():
    f = C.fields(ws())
    i = lambda *names: [f[n]['controlId'] for n in names]
    # Odoo's variant list: default_order "is_favorite desc, default_code, name, id" (product_views.xml:426); it shows
    # (image,) Name, Sales Price, Cost, Barcode, (On Hand, Free To Use: Inventory,) Unit. Display Name stands for
    # Name, as Odoo's list shows the display name. HAP sorts an empty Internal Reference first, Odoo last.
    sort = C.sort_by([(f['Favorite'], False), (f['Internal Reference'], True), (f['Name'], True)])
    columns = i('Display Name', 'Sales Price', 'Cost', 'Barcode', 'Unit')
    views = {
        # search filters Goods · Services | Favorites | Sales · Purchase
        WORKSHEET: (dict(viewType='table', filter=C.switch_filter(f['Active'], 'eq'), tableFields=columns,
                         quickFilters=[{'fieldId': f['Product Type']['controlId'], 'selectionType': 'single',
                                        'displayType': 'dropdown'}, *i('Sales', 'Purchase', 'Favorite')]),
                    sort, columns),
        'Archived': (dict(viewType='table', filter=C.switch_filter(f['Active'], 'ne'), tableFields=columns),
                     sort, columns),                                   # search filter Archived
    }
    for name, vid in C.upsert_views(ws(), APP, views, 'variants_views_pre_views', default_view=WORKSHEET).items():
        C.remember('views', KEY + name, vid)
    print('  order:', C.sort_views(ws(), APP, list(views)))
    C.print_views(ws(), APP)
    for v in hap.listing('worksheet', 'view', 'list', ws(), '-a', APP):
        info = C.view_info(ws(), APP, v['viewId'])
        names = {c['controlId']: c['controlName'] for c in hap.controls(ws())}
        print(f"  {info['name']} quick filters: "
              f"{[(names.get(x['controlId']), x.get('dataType'), x.get('advancedSetting')) for x in info.get('fastFilters') or []]}")


def step_order():
    """Each view's records in the order the view returns them (its own filter and sort); ★ marks favourites."""
    display, fav = (C.fields(ws())[n]['controlId'] for n in ('Display Name', 'Favorite'))
    favorites = {r['rowid'] for r in C.records(ws(), APP) if str(r.get(fav)) == '1'}
    for v in hap.listing('worksheet', 'view', 'list', ws(), '-a', APP):
        res = hap.run('worksheet', 'record', 'list', ws(), '-a', APP, '-n', '100', '--view-id', v['viewId'],
                      '--use-field-id-as-key')
        data = res.get('data', res) if isinstance(res, dict) else res
        rows = (data.get('rows') if isinstance(data, dict) else data) or []
        print(f"  {v['name']} ({len(rows)}): "
              f"{[(r.get(display) or '') + (' ★' if r['rowid'] in favorites else '') for r in rows]}")


# ── workflow helpers ────────────────────────────────────────────────────────

FIND, GET_MANY = ('7', '406'), ('13', '400')     # (flowNodeType, actionId) of the two search nodes


def relation_is(node_id, field, value_node, value_field='rowid', kind=GET_MANY):
    """Condition: the searched record's Relation `field` points at `value_node`'s record (or at the record in
    that node's own Relation field `value_field`). conditionId 33 is the workflow's "is" for a relation."""
    return {'nodeId': node_id, 'nodeType': int(kind[0]), 'actionId': kind[1], 'filedId': field['controlId'],
            'filedValue': field['controlName'], 'filedTypeId': 29, 'enumDefault': field.get('enumDefault', 1),
            'conditionId': '33', 'sourceType': 0, 'conditionValues': [
                {'nodeId': value_node, 'controlId': value_field, 'value': '', 'sureNodeId': value_node}]}


def switch_is(node_id, field, checked, kind=GET_MANY):
    """Condition: checkbox `field` is checked (29) or unchecked (30)."""
    return {'nodeId': node_id, 'nodeType': int(kind[0]), 'actionId': kind[1], 'filedId': field['controlId'],
            'filedValue': field['controlName'], 'filedTypeId': 36, 'enumDefault': 0,
            'conditionId': '29' if checked else '30', 'sourceType': 0, 'conditionValues': []}


def not_this_record(node_id, value_node, kind=FIND):
    """Condition: the searched record is not `value_node`'s own record."""
    return {'nodeId': node_id, 'nodeType': int(kind[0]), 'actionId': kind[1], 'filedId': 'rowid',
            'filedValue': 'Record ID', 'filedTypeId': 2, 'enumDefault': 0, 'conditionId': '10', 'sourceType': 0,
            'conditionValues': [{'nodeId': value_node, 'controlId': 'rowid', 'value': '', 'sureNodeId': value_node}]}


def save_search(pid, node, worksheet, conditions, kind=GET_MANY, sorts=None, execute_type=None):
    """Save a search node's filter the way the UI stores it: `filters`, not `operateCondition` (which
    `node batch-add --nodes` sends and the UI never reads)."""
    config = {'actionId': kind[1], 'appId': worksheet, 'selectNodeId': '',
              'filters': [{'spliceType': 2, 'conditions': [conditions]}],
              'sorts': sorts or [{'controlId': 'ctime', 'controlType': 16, 'isAsc': True}]}
    if execute_type is not None:
        config['executeType'] = execute_type
    hap.run('workflow', 'node', 'save', pid, node['id'], '--type', kind[0], '-c', json.dumps(config, ensure_ascii=False),
            '-n', node['name'])


def nodes_by_name(pid):
    proc = hap.run('workflow', 'node', 'list', pid)
    return proc, {n['name']: n for n in proc['flowNodeMap'].values()}


def last_in_chain(proc):
    node = proc['startEventId']
    while proc['flowNodeMap'][node].get('nextId') not in (None, '', '99'):
        node = proc['flowNodeMap'][node]['nextId']
    return node


def product_fields(names):
    """[(variant control, product control)] for the fields a workflow copies from the product."""
    v, p = C.fields(ws()), C.fields(products_ws())
    return [(v[n], p[n]) for n in names]


def copy_fields(names, source={'nodeAlias': 'trigger'}):
    """update_record field patches copying the product's values onto the variant."""
    return [{'fieldId': v['controlId'], 'type': v['type'],
             'valueRef': {'kind': 'field', 'node': source, 'fieldId': p['controlId'], 'nodeAppId': products_ws()}}
            for v, p in product_fields(names)]


# ── 8 · buttons ─────────────────────────────────────────────────────────────

MASTERED = ['Internal Reference', 'Cost', 'Weight', 'Volume']     # Products is the master of these four


def step_buttons():
    """Archive / Unarchive as on Products, plus Odoo's cascade to the product (product.product action_archive /
    action_unarchive): archiving the last active variant archives its product, and unarchiving a variant
    unarchives its product."""
    f = C.fields(ws())
    active = f['Active']['controlId']
    when = lambda op: {'type': 'group', 'logic': 'AND', 'children': [
        {'type': 'condition', 'field': active, 'operator': op, 'value': ['1']}]}
    buttons = [  # Odoo ⚙ Actions › Archive / Unarchive, word for word as on Products
        ({'name': 'Archive', 'type': 'triggerWorkflow', 'enableWhen': when('eq'), 'isBatch': True,
          'confirm': True, 'confirmMsg': 'Are you sure that you want to archive this record?',
          'sureName': 'Archive', 'cancelName': 'Cancel'}, [{'fieldId': active, 'value': '0'}], 'Archive the variant'),
        ({'name': 'Unarchive', 'type': 'triggerWorkflow', 'enableWhen': when('ne'), 'isBatch': True},
         [{'fieldId': active, 'value': '1'}], 'Unarchive the variant'),
    ]
    C.upsert_buttons(ws(), APP, buttons, KEY, 'variants_buttons_pre_buttons')
    cascade_archive()
    cascade_unarchive()
    for key in (KEY + 'Archive', KEY + 'Unarchive'):
        print(C.structure(hap.ids()['workflows'][key]))


GET_PRODUCT = 'Get the product'
OTHER_ACTIVE = 'Does the product still have an active variant?'
LAST_ACTIVE = 'Was it the last active variant?'


def get_product_node(alias='product'):
    """The variant's product, as a search on Products; its filter (record ID = the trigger's Product) is saved
    afterwards with save_search. A "get related record" step cannot start from a button's trigger record: the
    server leaves that trigger out of the step's sources and drops the relation field."""
    return {'nodeAlias': alias, 'nodeType': 'get_single', 'name': GET_PRODUCT,
            'config': {'worksheet': products_ws(), 'execute_type': 2}}


def product_of(node_id, trigger):
    """Condition for GET_PRODUCT: the product's record ID equals the trigger variant's Product."""
    return {'nodeId': node_id, 'nodeType': 7, 'actionId': '406', 'filedId': 'rowid', 'filedValue': 'Record ID',
            'filedTypeId': 2, 'enumDefault': 0, 'conditionId': '9', 'sourceType': 0, 'conditionValues': [
                {'nodeId': trigger, 'controlId': C.fields(ws())['Product']['controlId'], 'value': '',
                 'sureNodeId': trigger}]}


def name_result_paths(pid, gateway, names):
    """batch-add drops path names; a result branch's paths are told apart by resultTypeId (3 found, 4 not)."""
    proc, byname = nodes_by_name(pid)
    for n in proc['flowNodeMap'].values():
        if n.get('typeId') == 2 and n.get('prveId') == byname[gateway]['id'] and n.get('name') != names[n.get('resultTypeId')]:
            hap.run('workflow', 'node', 'rename', pid, n['id'], '-n', names[n.get('resultTypeId')])


def check_nodes(pid, expected, rollback=False):
    """Read back create / update nodes: {node name: (worksheet, [field ids that must carry a value])}. A node
    added with the wrong worksheet keeps it (saveNode cannot rebind it) and silently loses its fields. On a
    mismatch the step stops; with rollback (a workflow that has a published version) the unpublished draft is
    first rolled back to that version, so no node is deleted."""
    proc, byname = nodes_by_name(pid)
    bad = {}
    for name, (worksheet, fields) in expected.items():
        d = hap.run('workflow', 'node', 'get', pid, byname[name]['id'])
        d = d.get('data', d)
        valued = {f.get('fieldId') for f in d.get('fields') or [] if f.get('fieldValue') not in ('', None) or f.get('nodeId')}
        if d.get('appId') != worksheet or not set(fields) <= valued:
            bad[name] = {'worksheet': (d.get('appId'), worksheet), 'unset': sorted(set(fields) - valued)}
    if bad:
        if rollback:
            hap.run('workflow', 'rollback', pid, '-y')
        sys.exit(f'{pid}: read back {bad}' + ('; the draft was rolled back to the published version' if rollback else ''))
    print(f'  {len(expected)} data nodes read back as built')


def name_paths_by_step(pid, names):
    """Name condition-branch paths after their first step: {first step name: path name}."""
    proc, byname = nodes_by_name(pid)
    nodes = proc['flowNodeMap']
    for n in nodes.values():
        first = nodes.get(n.get('nextId') or '', {}).get('name')
        if n.get('typeId') == 2 and first in names and n.get('name') != names[first]:
            hap.run('workflow', 'node', 'rename', pid, n['id'], '-n', names[first])


def set_product_active(alias, name, value, source='product'):
    return {'nodeAlias': alias, 'nodeType': 'update_record', 'name': name,
            'config': {'target': {'node': {'nodeAlias': source}}, 'worksheet': products_ws(),
                       'fields': [{'fieldId': C.fields(products_ws())['Active']['controlId'], 'type': 36,
                                   'value': value}]}}


def cascade_archive():
    """product.product.action_archive: the product is archived when its last active variant is."""
    pid = hap.ids()['workflows'][KEY + 'Archive']
    proc, byname = nodes_by_name(pid)
    if OTHER_ACTIVE not in byname:
        nodes = [
            {'nodeAlias': 'others', 'nodeType': 'get_single', 'name': OTHER_ACTIVE,
             'config': {'worksheet': ws(), 'execute_type': 2}},          # 2 = carry on when nothing is found
            {'nodeAlias': 'last', 'nodeType': 'branch', 'name': LAST_ACTIVE,
             'config': {'result_branch': True, 'paths': [
                 {'alias': 'more', 'name': 'Another variant is active', 'result_type': 'has_data'},
                 {'alias': 'none_left', 'name': 'It was the last', 'result_type': 'no_data', 'nodes': [
                     get_product_node(), set_product_active('archive_product', 'Archive the product', '0')]}]}},
        ]
        hap.run('workflow', 'node', 'batch-add', pid, '--nodes', json.dumps(nodes, ensure_ascii=False),
                '--trigger-node-id', last_in_chain(proc), '--trigger-alias', 'last_step')
        proc, byname = nodes_by_name(pid)
        check_nodes(pid, {'Archive the product': (products_ws(), [C.fields(products_ws())['Active']['controlId']])},
                    rollback=True)
    trigger, f = proc['startEventId'], C.fields(ws())
    node = byname[OTHER_ACTIVE]
    save_search(pid, node, ws(), [relation_is(node['id'], f['Product'], trigger, f['Product']['controlId'], FIND),
                                  switch_is(node['id'], f['Active'], True, FIND),
                                  not_this_record(node['id'], trigger)], kind=FIND, execute_type=2)
    save_search(pid, byname[GET_PRODUCT], products_ws(), [product_of(byname[GET_PRODUCT]['id'], trigger)],
                kind=FIND, execute_type=2)
    name_result_paths(pid, LAST_ACTIVE, {3: 'Another variant is active', 4: 'It was the last'})
    print('  Archive:', C.publish(pid))


def cascade_unarchive():
    """product.product.action_unarchive: a product with an active variant is active."""
    pid = hap.ids()['workflows'][KEY + 'Unarchive']
    proc, byname = nodes_by_name(pid)
    if GET_PRODUCT not in byname:
        nodes = [get_product_node(), set_product_active('unarchive_product', 'Unarchive the product', '1')]
        hap.run('workflow', 'node', 'batch-add', pid, '--nodes', json.dumps(nodes, ensure_ascii=False),
                '--trigger-node-id', last_in_chain(proc), '--trigger-alias', 'last_step')
        proc, byname = nodes_by_name(pid)
        check_nodes(pid, {'Unarchive the product': (products_ws(), [C.fields(products_ws())['Active']['controlId']])},
                    rollback=True)
    save_search(pid, byname[GET_PRODUCT], products_ws(), [product_of(byname[GET_PRODUCT]['id'], proc['startEventId'])],
                kind=FIND, execute_type=2)
    print('  Unarchive:', C.publish(pid))


# ── 9 · automations ─────────────────────────────────────────────────────────

FOLLOWED = MASTERED + ['Favorite']              # what a variant takes from its product (Odoo: Favorite is related)

CREATE_VARIANT = KEY + "create a new product's variant"
# ids.json keeps a workflow's first name as its key: B was renamed when Favorite joined the copied fields
COPY_TO_VARIANT = KEY + "copy a product's Internal Reference, Cost, Weight and Volume to its active variant"
ARCHIVE_WITH_PRODUCT = KEY + "archive and unarchive a product's variant with it"

FIND_EXISTING = 'Does the product already have a variant?'
CREATE_STEP = "Create the product's variant"
ACTIVE_VARIANTS = "Get the product's active variants"
COPY_STEP = 'Copy the five fields to them'
ARCHIVE_ACTIVE = "Get the product's active variants to archive"
ARCHIVE_STEP = 'Archive them'
OLDEST_VARIANT = "Get the product's own variant (its oldest)"
REACTIVATE_STEP = "Unarchive it with the product's current values"
RENAMED_STEPS = {'Copy the four fields to them': COPY_STEP}
TRIGGER_EVENTS = {'create': '1', 'update': '4'}     # a worksheet trigger's triggerId: 1 created, 4 updated


def entry_source(entry, trigger):
    """Where a create / update step's field entry takes its value: ('trigger', field id) or ('value', literal).
    A text field copied from a node reads back as the template "$node-field$", the other types as nodeId and
    fieldValueId."""
    if entry.get('nodeId') == trigger and entry.get('fieldValueId'):
        return ('trigger', entry['fieldValueId'])
    template = re.fullmatch(r'\$([^$-]+)-([^$]+)\$', entry.get('fieldValue') or '')
    if template and template.group(1) == trigger:
        return ('trigger', template.group(2))
    return ('value', entry.get('fieldValue'))


def sync_step(pid, trigger, name, worksheet, wanted):
    """Make an existing create / update step write `wanted` — {variant control id: ('trigger', field id on the
    trigger record) | ('value', literal)} — keeping its other entries; save, then read back."""
    node = nodes_by_name(pid)[1][name]
    read = lambda: (lambda d: d.get('data', d))(hap.run('workflow', 'node', 'get', pid, node['id']))
    d = read()
    if d.get('appId') != worksheet:
        sys.exit(f'{pid} {name}: bound to {d.get("appId")}, not {worksheet} — left for a person to look at')
    fields = d.get('fields') or []
    by_id = {e.get('fieldId'): e for e in fields}
    stale = [cid for cid, want in wanted.items() if cid not in by_id or entry_source(by_id[cid], trigger) != want]
    if stale:
        hap.backup(f"variants_workflow_{pid}_step_{node['id']}", d)
        controls = {c['controlId']: c for c in hap.controls(worksheet)}
        for cid in stale:
            kind, value = wanted[cid]
            entry = {'fieldId': cid, 'type': controls[cid]['type'], 'alias': controls[cid].get('alias'), 'addType': 0,
                     'fieldValue': '', 'fieldValueId': '', 'nodeId': '', 'sureNodeId': '', 'nodeAppType': 0,
                     'nodeAppId': '', 'sourceType': 0, 'isClear': False}
            if kind == 'trigger':
                entry.update(fieldValueId=value, nodeId=trigger, sureNodeId=trigger, nodeAppType=1,
                             nodeAppId=products_ws())
            else:
                entry['fieldValue'] = value
            if cid in by_id:
                by_id[cid].update(entry)
            else:
                fields.append(entry)
        config = {'actionId': d['actionId'], 'appId': worksheet, 'appType': d.get('appType') or 1,
                  'selectNodeId': d.get('selectNodeId') or '', 'fields': fields}
        hap.run('workflow', 'node', 'save', pid, node['id'], '--type', '6', '-n', name,
                '-c', json.dumps(config, ensure_ascii=False))
        by_id = {e.get('fieldId'): e for e in read().get('fields') or []}
    wrong = {cid: entry_source(by_id[cid], trigger) if cid in by_id else None
             for cid, want in wanted.items() if cid not in by_id or entry_source(by_id[cid], trigger) != want}
    if wrong:
        hap.run('workflow', 'rollback', pid, '-y')           # back to the published version; no step deleted
        sys.exit(f'{pid} {name}: read back {wrong}, wanted {wanted}; the draft was rolled back')
    print(f"  {name}: {len(wanted)} fields read back as built" + (f' ({len(stale)} rewritten)' if stale else ''))


def sync_trigger(pid, start, wf):
    """Worksheet, event, trigger fields and condition of an existing worksheet-event trigger, rewritten when they
    differ, then read back."""
    from hap_cli.core.workflow_node_dsl import translate_condition_group
    want = translate_condition_group(wf['filter'], {'trigger': start}) if wf['filter'] else []
    shape = lambda groups: [[(c.get('filedId'), str(c.get('conditionId'))) for c in g] for g in groups or []]
    live = lambda: (lambda t: (t.get('appId'), str(t.get('triggerId')), sorted(t.get('assignFieldIds') or []),
                               shape(t.get('operateCondition'))))(
        (lambda d: d.get('data', d))(hap.run('workflow', 'node', 'get', pid, start)))
    target = (products_ws(), TRIGGER_EVENTS[wf['event']], sorted(wf['fields']), shape(want))
    if live() != target:
        hap.backup(f'variants_workflow_{pid}_trigger', hap.run('workflow', 'node', 'get', pid, start))
        hap.run('workflow', 'node', 'save', pid, start, '--type', '0', '-n', wf['trigger_name'], '-c', json.dumps(
            {'appId': products_ws(), 'appType': 1, 'triggerId': TRIGGER_EVENTS[wf['event']],
             'assignFieldIds': wf['fields'], 'operateCondition': want, 'returns': []}, ensure_ascii=False))
        if live() != target:
            hap.run('workflow', 'rollback', pid, '-y')       # back to the published version
            sys.exit(f'{pid}: trigger read back {live()}, wanted {target}; the draft was rolled back')
        print(f"  {wf['name']}: trigger rewritten")


def step_automations():
    """Products is the master of Internal Reference, Cost, Weight, Volume and Favorite while each product has one
    variant.

    A  a new product gets its variant                  Odoo product.template create -> _create_variant_ids
    B  its active variants follow those five fields    Odoo _set_product_variant_field (single active variant);
                                                       is_favorite is related to the product's
    C  archiving a product archives all its variants;  Odoo product.template.write
       unarchiving it reactivates its own (oldest)     Odoo write -> _create_variant_ids
       variant, brought up to date

    Creates a missing workflow; brings an existing one up to date in place (name, description, trigger, the fields
    its steps write, search filters, step and path names), then republishes. No step is ever deleted.

    None of them can loop: they trigger on Products and write only Product Variants, where no worksheet event
    starts a workflow. The variant's Archive / Unarchive buttons write its product, which starts C once; C then
    finds nothing left to change."""
    v, p = C.fields(ws()), C.fields(products_ws())
    trigger = {'nodeAlias': 'trigger'}
    when = lambda name, op: {'left': {'node': trigger, 'fieldId': p[name]['controlId'],
                                      '_filedTypeId': p[name]['type'], '_filedValue': name}, 'op': op}
    copies = lambda names: {v[n]['controlId']: ('trigger', p[n]['controlId']) for n in names}
    workflows = [
        dict(key=CREATE_VARIANT, name=CREATE_VARIANT,
             desc="Odoo product.template create -> _create_variant_ids: a new product gets its variant, with the "
                  "product's Internal Reference, Cost, Weight, Volume, Favorite and Active. Skipped if it already "
                  'has one.',
             trigger_name='When a product is created', event='create', fields=[],
             filter={'logic': 'and', 'items': [when('Name', 'not_empty')]},       # Odoo: a product has a name
             nodes=[
                 {'nodeAlias': 'existing', 'nodeType': 'get_single', 'name': FIND_EXISTING,
                  'config': {'worksheet': ws(), 'execute_type': 2}},
                 {'nodeAlias': 'found', 'nodeType': 'branch', 'name': 'Variant found?', 'config': {
                     'result_branch': True, 'paths': [
                         {'alias': 'has_one', 'name': 'It has one', 'result_type': 'has_data'},
                         {'alias': 'has_none', 'name': 'No variant yet', 'result_type': 'no_data', 'nodes': [
                             {'nodeAlias': 'make', 'nodeType': 'create_record', 'name': CREATE_STEP,
                              'config': {'worksheet': ws(), 'fields': [
                                  {'fieldId': v['Product']['controlId'], 'type': 29,
                                   'valueRef': {'kind': 'field', 'node': trigger, 'fieldId': 'rowid'}},
                                  *copy_fields(FOLLOWED + ['Active'])]}}]}]}}],
             searches={FIND_EXISTING: (FIND, lambda node, t: [relation_is(node, v['Product'], t, 'rowid', FIND)], 2)},
             paths={'Variant found?': {3: 'It has one', 4: 'No variant yet'}},
             data={CREATE_STEP: {v['Product']['controlId']: ('trigger', 'rowid'), **copies(FOLLOWED + ['Active'])}}),
        dict(key=COPY_TO_VARIANT,
             name=KEY + "copy a product's Internal Reference, Cost, Weight, Volume and Favorite to its active variant",
             desc="Odoo product.template _set_default_code / _set_standard_price / _set_weight / _set_volume, and "
                  "product.product is_favorite (related): while a product has one active variant, its Internal "
                  "Reference, Cost, Weight, Volume and Favorite are the variant's. Archived variants keep their own "
                  'values.',
             trigger_name="When a product's Internal Reference, Cost, Weight, Volume or Favorite changes",
             event='update', fields=[p[n]['controlId'] for n in FOLLOWED], filter=None,   # the trigger fields are the condition
             nodes=[
                 {'nodeAlias': 'active_variants', 'nodeType': 'get_multiple', 'name': ACTIVE_VARIANTS,
                  'config': {'worksheet': ws()}},
                 {'nodeAlias': 'copy', 'nodeType': 'update_record', 'name': COPY_STEP,
                  'config': {'target': {'node': {'nodeAlias': 'active_variants'}}, 'fields': copy_fields(FOLLOWED)}}],
             searches={ACTIVE_VARIANTS: (GET_MANY, lambda node, t: [relation_is(node, v['Product'], t),
                                                                    switch_is(node, v['Active'], True)], None)},
             paths={},
             data={COPY_STEP: copies(FOLLOWED)}),
        dict(key=ARCHIVE_WITH_PRODUCT, name=ARCHIVE_WITH_PRODUCT,
             desc='Odoo product.template.write: archiving a product archives its variants; unarchiving it '
                  "reactivates its own variant (the oldest, as _create_variant_ids does) with the product's current "
                  'Internal Reference, Cost, Weight, Volume and Favorite. Extra archived variants stay archived.',
             trigger_name='When a product is archived or unarchived', event='update',
             fields=[p['Active']['controlId']], filter=None,              # the Active trigger field is the condition
             nodes=[
                 {'nodeAlias': 'which', 'nodeType': 'branch', 'name': 'Archived or unarchived?', 'config': {
                     'mode': 'exclusive', 'paths': [
                         {'alias': 'archived', 'name': 'Archived',
                          'condition': {'logic': 'and', 'items': [when('Active', 'unchecked')]},
                          'nodes': [
                              {'nodeAlias': 'to_archive', 'nodeType': 'get_multiple', 'name': ARCHIVE_ACTIVE,
                               'config': {'worksheet': ws()}},
                              {'nodeAlias': 'archive', 'nodeType': 'update_record', 'name': ARCHIVE_STEP,
                               'config': {'target': {'node': {'nodeAlias': 'to_archive'}},
                                          'fields': [{'fieldId': v['Active']['controlId'], 'type': 36,
                                                      'value': '0'}]}}]},
                         {'alias': 'unarchived', 'name': 'Unarchived',
                          'condition': {'logic': 'and', 'items': [when('Active', 'checked')]},
                          'nodes': [
                              {'nodeAlias': 'own', 'nodeType': 'get_single', 'name': OLDEST_VARIANT,
                               'config': {'worksheet': ws(), 'execute_type': 2}},
                              {'nodeAlias': 'reactivate', 'nodeType': 'update_record', 'name': REACTIVATE_STEP,
                               'config': {'target': {'node': {'nodeAlias': 'own'}},
                                          'fields': copy_fields(FOLLOWED + ['Active'])}}]}]}}],
             searches={ARCHIVE_ACTIVE: (GET_MANY, lambda node, t: [relation_is(node, v['Product'], t),
                                                                   switch_is(node, v['Active'], True)], None),
                       OLDEST_VARIANT: (FIND, lambda node, t: [relation_is(node, v['Product'], t, 'rowid', FIND)], 2)},
             paths={}, steps={ARCHIVE_ACTIVE: 'Archived', OLDEST_VARIANT: 'Unarchived'},
             data={ARCHIVE_STEP: {v['Active']['controlId']: ('value', '0')},
                   REACTIVATE_STEP: copies(FOLLOWED + ['Active'])}),
    ]
    ids = hap.ids()
    for wf in workflows:
        pid = ids.get('workflows', {}).get(wf['key'])
        if not pid:
            out = hap.run('workflow', 'create', '-c', ids['org'], '-n', wf['name'], '-a', APP, '--type', 'worksheet',
                          '-d', wf['desc'])
            data = out.get('data', out) if isinstance(out, dict) else out
            pid = data if isinstance(data, str) else (data.get('id') or data.get('processId'))
            C.remember('workflows', wf['key'], pid)
            args = ['workflow', 'node', 'batch-add', pid, '--nodes', json.dumps(wf['nodes'], ensure_ascii=False),
                    '--trigger-worksheet', products_ws(), '--trigger-event', wf['event'], '--trigger-alias', 'trigger']
            if wf['fields']:
                args += ['--trigger-fields', ','.join(wf['fields'])]
            if wf['filter']:
                args += ['--trigger-filter', json.dumps(wf['filter'], ensure_ascii=False)]
            hap.run(*args)
            print(f"  {wf['name']}: created {pid}")
        info = hap.run('workflow', 'get', pid)
        info = info.get('data', info)
        if (info.get('name'), info.get('explain') or '') != (wf['name'], wf['desc']):
            hap.run('workflow', 'update', pid, '-n', wf['name'], '-d', wf['desc'])
            print(f"  {pid}: name / description updated" +
                  (f" (was {info.get('name')!r})" if info.get('name') != wf['name'] else ''))
        proc, byname = nodes_by_name(pid)
        for old, new in RENAMED_STEPS.items():
            if old in byname and new not in byname:
                hap.run('workflow', 'node', 'rename', pid, byname[old]['id'], '-n', new)
                proc, byname = nodes_by_name(pid)
        missing = [n for n in list(wf['searches']) + list(wf['data']) if n not in byname]
        if missing:
            sys.exit(f"{wf['name']}: steps {missing} are missing — left for a person to look at")
        start = proc['startEventId']
        sync_trigger(pid, start, wf)
        for name, (kind, conditions, execute_type) in wf['searches'].items():
            node = byname[name]
            sorts = [{'controlId': 'ctime', 'controlType': 16, 'isAsc': True}]          # oldest first
            save_search(pid, node, ws(), conditions(node['id'], start), kind=kind, sorts=sorts,
                        execute_type=execute_type)
        for name, wanted in wf['data'].items():
            sync_step(pid, start, name, ws(), wanted)
        hap.run('workflow', 'node', 'rename', pid, start, '-n', wf['trigger_name'])
        for gateway, names in wf['paths'].items():
            name_result_paths(pid, gateway, names)
        name_paths_by_step(pid, wf.get('steps', {}))
        print(f"  {wf['name']}:", C.publish(pid))
    for wf in workflows:
        print(C.structure(hap.ids()['workflows'][wf['key']]))


# ── 10 · switches ───────────────────────────────────────────────────────────

# Odoo's Product Variants action is opened from a product with create False, and the variant list and form say
# duplicate="false": a variant comes with its product (automation A). HAP's matching worksheet switches:
SWITCHES_OFF = {10: 'Show create button', 26: 'View › Batch › Duplicate', 36: 'Record › Duplicate',
                37: 'Record › Re-create'}


def step_switches():
    """Only the UI's creation paths are switched off; workflows and API writes still create records."""
    live = {s['type']: s['state'] for s in hap.listing('worksheet', 'switches', ws())}
    todo = [t for t in SWITCHES_OFF if live.get(t) is not False]
    if todo:
        hap.run('worksheet', 'batch-edit-switch', ws(), *[x for t in todo for x in ('--set', f'{t}=false')])
    live = {s['type']: s['state'] for s in hap.listing('worksheet', 'switches', ws())}
    for t, name in SWITCHES_OFF.items():
        print(f'  {t:>3} {name:<26} {"off" if live.get(t) is False else "ON — not switched off"}')
    if any(live.get(t) is not False for t in SWITCHES_OFF):
        sys.exit('switches did not read back off')


# ── 11 · seed and verify ────────────────────────────────────────────────────

REFERENCE = os.path.join(hap.HERE, '..', 'reference', 'odoo-19.4', 'product.product.md')
COPIED = ('code', 'standard_price', 'weight', 'volume', 'is_favorite')    # the product's values (automations A, B, C)


def number_value(v):
    return Decimal(str(v)) if v not in (None, '') else None


def listed(v):
    """A record-get option or relation value (a list, or a JSON string of one) as a list."""
    if isinstance(v, str):
        v = json.loads(v) if v.startswith('[') else []
    return v if isinstance(v, list) else []


def flag(v):
    return str(v) in ('1', 'True', 'true')


def text(v):
    """A lookup's value as text: options and relations come back as lists of {value} / {name}."""
    items = listed(v) if isinstance(v, (list, str)) and str(v).startswith('[') else None
    if items is None:
        return '' if v in (None, '') else str(v)
    return ', '.join(str(x.get('value') or x.get('name') or '') if isinstance(x, dict) else str(x) for x in items)


def read_variant(rowid):
    """One variant through `record get` (by alias): `record list` blanks hidden fields."""
    d = hap.run('worksheet', 'record', 'get', ws(), rowid, '-a', APP)['data']
    product = listed(d.get('product_tmpl_id'))
    return dict(rowid=rowid, created=d.get('_createdAt') or '', display_name=d.get('display_name') or '',
                product=product[0].get('name') if product else None,
                product_rowid=product[0].get('sid') if product else None, code=d.get('default_code') or '',
                barcode=d.get('barcode') or '', standard_price=number_value(d.get('standard_price')),
                weight=number_value(d.get('weight')), volume=number_value(d.get('volume')), active=flag(d.get('active')),
                is_favorite=flag(d.get('is_favorite')), extra_uom_ids=d.get('extra_uom_ids'),
                name=text(d.get('name')), type=text(d.get('type')), uom=text(d.get('uom_id')),
                sale_ok=flag(text(d.get('sale_ok'))), purchase_ok=flag(text(d.get('purchase_ok'))),
                lst_price=number_value(text(d.get('lst_price'))), raw=d)


def read_variants():
    """Every variant, archived included: {rowid: read_variant}."""
    return {r['rowid']: read_variant(r['rowid']) for r in C.records(ws(), APP)}


def read_products():
    import products
    return products.read_products()


def by_product(variants):
    """{product rowid: [variants, oldest first]}. The oldest is the product's own variant — the one automation A
    or the seed created with it, and the one Odoo's _create_variant_ids reactivates. Any later one is an extra
    (07 Invoice Lines may add the tenant's archived originals as extras); the seed never touches extras."""
    out = {}
    for v in sorted(variants.values(), key=lambda v: (v['created'], v['rowid'])):
        out.setdefault(v['product_rowid'], []).append(v)
    return out


def expected_display_name(code, name):
    return f'[{code.strip()}] {name.strip()}' if code else name.strip()


def product_differences(v, p):
    """{field: (variant, product)} for what a variant copies or looks up from its product."""
    pairs = {'code': (v['code'], p['code']), 'standard_price': (v['standard_price'], p['standard_price']),
             'weight': (v['weight'], p['weight']), 'volume': (v['volume'], p['volume']),
             'is_favorite': (v['is_favorite'], p['is_favorite']),
             'active': (v['active'], p['active']), 'name': (v['name'], p['name']), 'type': (v['type'], p['type']),
             'uom': (v['uom'], p['uom']), 'sale_ok': (v['sale_ok'], p['sale_ok']),
             'purchase_ok': (v['purchase_ok'], p['purchase_ok']), 'lst_price': (v['lst_price'], p['list_price']),
             'display_name': (v['display_name'], expected_display_name(p['code'], p['name']))}
    return {k: (str(a), str(b)) for k, (a, b) in pairs.items() if a != b}


# ── the reverse on Products, and Odoo's Variants count ──────────────────────
#
# 04 §1 first said the Product relation was one-way and that Products carried no reverse. That was wrong twice
# over: Odoo's `product.template.product_variant_ids` is a real one2many, surfaced on the product form as the
# **Variants** smart button with `product_variant_count` — and 03 had already deferred that button *to this
# worksheet*, so the field fell between the two documents and nobody built it.
#
# It was never one-way in HAP's eyes either. `add-fields` had **reserved** the reverse's id in the Product
# control's `sourceControlId` and left it dangling, which is the second case prodcat.ensure_reverses describes:
# the server reserves the id and makes no control. Units & Packagings shows the finished shape — Reference Unit
# and Related UoMs each carry the other's id in `sourceControlId`. This step completes the same handshake.
#
# Both new controls are placed where **no existing row moves**: the count beside Active on row 3 (Odoo puts its
# stat button at the top of the form too), and the list at row 19 under everything, where `showtype` "2" draws
# it as a tab at the foot of the record rather than in the grid.

REVERSE, VARIANT_COUNT = 'Variants', '# Variants'
REVERSE_PLACE, COUNT_PLACE = (19, 0, 12), (3, 1, 6)
REVERSE_DESC = ('The variants of this product. Odoo product_variant_ids — read-only here, as it is there: a '
                'variant says which product it belongs to.')
COUNT_DESC = "The number on Odoo's Variants smart button (product_variant_count)."

# The columns the Variants list shows. A `showtype` "2" Relation draws as a **tab at the foot of the record**, and
# a list with no `showControls` shows its row count over the words *No visible fields* (BUILDING.md) — which is
# what this tab did until 21 Sep 2026. The columns are named by controlId **from the target worksheet**, the way
# Product Categories' own Products list names Products' Name and Internal Reference (prodcat.LIST_COLUMNS).
#
# These five are Odoo's, not a choice: the Variants smart button opens the product.product list
# (`product.product.md` › Menu), whose default-visible columns are image · Name · Attributes · Sales Price · Cost ·
# Barcode · On Hand · Free To Use · Unit (› List). Attributes waits for the Product Variants bundle and On Hand /
# Free To Use for Inventory, which leaves exactly the five this worksheet's own Product Variants view already shows
# (`04-product-variants.md` › Views), Display Name standing for Odoo's Name as it does there. **Internal Reference
# is deliberately not among them**: Odoo's list carries it `optional="hide"`, and Display Name already reads
# "[Internal Reference] Name".
REVERSE_COLUMNS = ('Display Name', 'Sales Price', 'Cost', 'Barcode', 'Unit')


def products_ws():
    return hap.ids()['worksheets'][PRODUCTS]


def reverse_columns():
    """REVERSE_COLUMNS as controlIds on Product Variants — the target worksheet, whose ids the list names."""
    f = C.fields(ws())
    missing = [n for n in REVERSE_COLUMNS if n not in f]
    if missing:
        sys.exit(f'{REVERSE}: {missing} are not on {WORKSHEET} — run the earlier steps first')
    return [f[n]['controlId'] for n in REVERSE_COLUMNS]


def products_signature(ctrls=None):
    """Products' controls by id, for proving a save of that worksheet changed only what it meant to."""
    return {c['controlId']: json.dumps([c.get(k) for k in SIGNATURE], sort_keys=True, ensure_ascii=False)
            for c in (hap.controls(products_ws()) if ctrls is None else ctrls)}


def set_reverse_columns(reserved):
    """Give the Variants list its columns, in one version-pinned save of Products. Idempotent: when they already
    read back as REVERSE_COLUMNS nothing is written. Only that one control may change."""
    columns = reverse_columns()
    pw = products_ws()
    live = next((c for c in hap.controls(pw) if c['controlId'] == reserved), None)
    if (live or {}).get('showControls') == columns:
        print(f'  {REVERSE}: columns already {" · ".join(REVERSE_COLUMNS)}; nothing saved')
        return False
    ctrls, version = C.controls_with_version(pw)
    hap.backup('products_controls_pre_variant_columns', ctrls)
    before = products_signature(ctrls)
    target = next((c for c in ctrls if c['controlId'] == reserved), None)
    if not target:
        sys.exit(f'the reverse {reserved} is not in the control set just read from {PRODUCTS}')
    was = target.get('showControls') or []
    target['showControls'] = columns
    # The `version` pins HAP's optimistic lock: a control save anyone made between the read above and this one is
    # refused (code 10, 数据过时) rather than overwritten. Through the CLI's session, as products.py layout does:
    # the Relations' snapshots of their targets put the control list past the kernel's argument limit.
    C.save_controls(pw, ctrls, version=version)
    after = products_signature()
    changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    if changed != [reserved]:
        sys.exit(f'{PRODUCTS}: the save changed {changed}, wanted only {reserved}')
    back = next((c for c in hap.controls(pw) if c['controlId'] == reserved), None)
    if (back or {}).get('showControls') != columns:
        sys.exit(f'{REVERSE}: showControls read back {(back or {}).get("showControls")}, wanted {columns}')
    print(f'  {REVERSE}: columns {was} -> {columns} ({" · ".join(REVERSE_COLUMNS)})')
    return True


def step_reverse():
    """Give Products the reverse of Product Variants' Product relation, plus Odoo's variant count."""
    forward = C.fields(ws()).get('Product')
    if not forward:
        sys.exit('the Product relation is not on Product Variants')
    reserved = forward.get('sourceControlId')
    if not reserved:
        sys.exit('Product carries no sourceControlId — it was saved one-way and needs re-creating')
    pw = products_ws()
    ctrls = hap.controls(pw)
    have = {c['controlId'] for c in ctrls}
    pf = hap.by_name(c for c in ctrls if c['type'] != C.TAB)

    if reserved in have:
        print(f'  the reverse {reserved} is already on {PRODUCTS}; not re-created')
    else:
        control = C.control('RELATE_SHEET', REVERSE, REVERSE_PLACE, alias='product_variant_ids', hint='',
                            desc=REVERSE_DESC, data_source=ws(), multi=True,
                            advanced_setting={'showtype': '2'})          # 2 = the related records as a list
        control.update(controlId=reserved, sourceControlId=forward['controlId'], sourceControlType=6,
                       fieldPermission='101')                            # read-only, as prodcat's reverses are
        C.save_controls(pw, ctrls + [control])
        print(f"  {REVERSE}: reverse {reserved} saved on {PRODUCTS}, pairing with Product "
              f"({forward['controlId']})")
        ctrls = hap.controls(pw)
        pf = hap.by_name(c for c in ctrls if c['type'] != C.TAB)

    back = next((c for c in ctrls if c['controlId'] == reserved), None)
    if not back or back.get('sourceControlId') != forward['controlId'] or back.get('enumDefault') != 2:
        sys.exit(f'the reverse read back wrong: {json.dumps(back, ensure_ascii=False)[:300]}')

    if VARIANT_COUNT in pf:
        print(f'  {VARIANT_COUNT} is already there; not re-created')
    else:
        from hap_cli.core.app_creator.fields import rollup_control
        count = rollup_control(VARIANT_COUNT, via_control_id=reserved,
                               source_control_id=pf['Name']['controlId'], aggregate='count')
        row, col, size = COUNT_PLACE
        count.update(controlName=VARIANT_COUNT, alias='product_variant_count', row=row, col=col, size=size,
                     dot=0, desc=COUNT_DESC, hint='', fieldPermission='101')
        C.add_fields(pw, [count])
        print(f'  {VARIANT_COUNT} added (count over {REVERSE})')

    set_reverse_columns(reserved)

    names = {c['controlId']: c['controlName'] for c in hap.controls(ws())}
    for c in hap.controls(pw):
        if c['controlName'] in (REVERSE, VARIANT_COUNT):
            C.remember('controls', KEY + c['controlName'], c['controlId'])
            print(f"  {c['controlName']:14} {c['controlId']} r{c.get('row')} c{c.get('col')} "
                  f"type={c['type']} perm={c.get('fieldPermission')}")
            if c['controlName'] == REVERSE:
                print(f"  {'':14} columns {[names.get(x, x) for x in (c.get('showControls') or [])]}")
    return 0


def step_seed(*only):
    """Give every product exactly its one variant: create the missing ones, correct what a variant copies from
    its product (Internal Reference, Cost, Weight, Volume, Favorite, Active). Barcode, Extra Packagings and Variant
    Image are the variant's own: set empty on creation, never overwritten. `only` limits it to product names."""
    f = C.fields(ws())
    cid = lambda n: f[n]['controlId']
    products, variants = read_products(), read_variants()
    hap.backup('variants_records_pre_seed', {k: {a: str(b) for a, b in v.items() if a != 'raw'}
                                             for k, v in variants.items()})
    grouped = by_product(variants)
    for name, p in sorted(products.items()):
        if only and name not in only:
            continue
        mine = grouped.get(p['rowid'], [])
        values = [{'id': cid('Internal Reference'), 'value': p['code']},
                  {'id': cid('Cost'), 'value': str(p['standard_price'] or 0)},
                  {'id': cid('Weight'), 'value': str(p['weight'] or 0)},
                  {'id': cid('Volume'), 'value': str(p['volume'] or 0)},
                  {'id': cid('Favorite'), 'value': 1 if p['is_favorite'] else 0},
                  {'id': cid('Active'), 'value': 1 if p['active'] else 0}]            # always explicit on API writes
        if mine:
            v = mine[0]
            if not {k: d for k, d in product_differences(v, p).items() if k in COPIED + ('active',)}:
                continue
            hap.run('worksheet', 'record', 'update', ws(), v['rowid'], '-a', APP,
                    '--fields-json', json.dumps(values, ensure_ascii=False))
            rowid = v['rowid']
            print(f'  updated the variant of {name}')
        else:
            values += [{'id': cid('Product'), 'value': [p['rowid']]}, {'id': cid('Barcode'), 'value': ''}]
            rowid = C.row_id(hap.run('worksheet', 'record', 'create', ws(), '-a', APP,
                                     '--fields-json', json.dumps(values, ensure_ascii=False)))
            print(f'  created the variant of {name}: {rowid}')
        got = read_variant(rowid)
        copied = {k: d for k, d in product_differences(got, p).items() if k in COPIED + ('active',)}
        if got['product_rowid'] != p['rowid'] or copied:
            sys.exit(f'{name}: read back product={got["product"]} {copied}')
    time.sleep(5)                                    # stored lookups and the formula settle asynchronously
    return step_verify(*only)


def reference_variants():
    """The 21 variants of the 19.4 extract: [dict(display_name, template, code, lst_price, cost, attributes, active)]."""
    out, section = [], None
    for line in open(REFERENCE, encoding='utf-8'):
        if line.startswith('#'):
            section = line.strip('# \n')
            continue
        cells = [x.strip() for x in line.strip().strip('|').split('|')] if line.startswith('|') else []
        if section and section.startswith('Records') and len(cells) == 7 and cells[6] in ('yes', '**archived**'):
            out.append(dict(display_name=cells[0], template=cells[1], code=cells[2], lst_price=Decimal(cells[3]),
                            cost=Decimal(cells[4]), attributes=cells[5], active=cells[6] == 'yes'))
    return out


def step_verify(*only):
    """Every product has exactly one variant whose copies, lookups and Display Name match it; the variants of the
    extract's single-variant products match the extract."""
    products, variants = read_products(), read_variants()
    grouped = by_product(variants)
    bad = 0
    for name, p in sorted(products.items()):
        if only and name not in only:
            continue
        mine = grouped.get(p['rowid'], [])
        diffs = product_differences(mine[0], p) if mine else {'variants': ('0', '1')}
        active_extras = [x['display_name'] for x in mine[1:] if x['active']]
        if active_extras:                                   # Phase 1: one active variant per product
            diffs['active extra variants'] = (str(active_extras), '[]')
        bad += bool(diffs)
        v = mine[0] if mine else {}
        print(f"  {'OK  ' if not diffs else 'DIFF'}  {v.get('display_name', '-')!s:<44} cost={v.get('standard_price')} "
              f"weight={v.get('weight')} volume={v.get('volume')} price={v.get('lst_price')} unit={v.get('uom')} "
              f"type={v.get('type')} sales={int(bool(v.get('sale_ok')))} purchase={int(bool(v.get('purchase_ok')))} "
              f"active={int(bool(v.get('active')))} favorite={int(bool(v.get('is_favorite')))} "
              f"barcode={v.get('barcode') or '-'}" + (f'  <- {diffs}' if diffs else ''))
    orphans = [v['display_name'] for k, vs in grouped.items() if k not in {p['rowid'] for p in products.values()}
               for v in vs]
    extras = [v['display_name'] for vs in grouped.values() for v in vs[1:]]
    print(f'  {len(products)} products; {bad} whose own variant differs or is missing; {len(extras)} extra '
          f'variants {extras}; {len(orphans)} variants without a product {orphans}')
    # the extract: products with one variant must match exactly; the attribute variants wait for the bundle
    reference = reference_variants()
    count = {}
    for e in reference:
        count[e['template']] = count.get(e['template'], 0) + 1
    live = {v['display_name']: v for v in variants.values()}
    matched, waiting, extract_bad = 0, [], 0
    for e in reference:
        if count[e['template']] > 1:
            waiting.append(e['display_name'] + ('' if e['active'] else ' (archived)'))
            continue
        v = live.get(e['display_name'])
        diffs = ({'missing': (None, e['display_name'])} if not v else
                 {k: (str(a), str(b)) for k, (a, b) in {
                     'code': (v['code'], e['code']), 'lst_price': (v['lst_price'], e['lst_price']),
                     'standard_price': (v['standard_price'], e['cost']), 'active': (v['active'], e['active']),
                     'product': (v['product'], e['template']), 'barcode': (v['barcode'], '')}.items() if a != b})
        extract_bad += bool(diffs)
        matched += not diffs
        if diffs:
            print(f"  EXTRACT DIFF  {e['display_name']}  <- {diffs}")
    print(f'  extract: {matched} of {matched + extract_bad} single-variant products match; '
          f'{len(waiting)} variants wait for the Product Variants bundle {waiting}')
    return bad + extract_bad


def step_variant(*names):
    """Print the live values of variants by Display Name (all when none given), hidden fields included."""
    variants = sorted(read_variants().values(), key=lambda v: v['display_name'])
    for v in variants:
        if names and v['display_name'] not in names:
            continue
        print(f"  {v['display_name']}: " + json.dumps({k: str(x) for k, x in v.items() if k != 'raw'}, ensure_ascii=False))
    missing = set(names) - {v['display_name'] for v in variants}
    for name in sorted(missing):
        print(f'  {name}: no such variant')


def step_raw(rowid):
    """One variant's `record get` output, as stored (aliases, lookups, the creation time)."""
    print(json.dumps(hap.run('worksheet', 'record', 'get', ws(), rowid, '-a', APP)['data'], ensure_ascii=False, indent=1))


def show():
    C.show(ws())


if __name__ == '__main__':
    steps = {'create': step_create, 'fields': step_fields, 'relations': step_relations, 'lookups': step_lookups,
             'reverse': step_reverse,
             'display': step_display, 'layout': step_layout, 'rules': step_rules, 'views': step_views,
             'buttons': step_buttons, 'automations': step_automations, 'switches': step_switches,
             'seed': step_seed, 'verify': step_verify, 'order': step_order, 'variant': step_variant, 'raw': step_raw,
             'show': show}
    steps[sys.argv[1] if len(sys.argv) > 1 else 'show'](*sys.argv[2:])
