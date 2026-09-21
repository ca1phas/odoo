#!/usr/bin/env python3
"""Build the Products worksheet (Odoo product.template, as on casimir.odoo.com saas~19.4) in ERP Master.

    ~/.hap-venv/bin/python nocoly/build/products.py create     # 0. worksheet Products in menu group Products, first
    ~/.hap-venv/bin/python nocoly/build/products.py fields     # 1. base controls and tabs, in one save (fresh worksheet only)
    ~/.hap-venv/bin/python nocoly/build/products.py relations  # 2. Unit and Packagings, one-way relations to Units & Packagings
    ~/.hap-venv/bin/python nocoly/build/products.py layout     # 3. positions, tabs, hints, pickers, the Unit default
    ~/.hap-venv/bin/python nocoly/build/products.py rules      # 4. Sales / Inventory tab visibility, negative Cost (upsert by name)
    ~/.hap-venv/bin/python nocoly/build/products.py views      # 5. Products gallery, List and Archived tables
    ~/.hap-venv/bin/python nocoly/build/products.py buttons    # 6. Archive / Unarchive and their one-step workflows
    ~/.hap-venv/bin/python nocoly/build/products.py seed       # 7. the 14 products of the extract (upsert by Name), then verify
    ~/.hap-venv/bin/python nocoly/build/products.py verify     # compare the live products with the 19.4 extract
    ~/.hap-venv/bin/python nocoly/build/products.py order      # each view's records, in the order the view sorts them
    ~/.hap-venv/bin/python nocoly/build/products.py product "Onsite Training (per day)"   # live values by name
    ~/.hap-venv/bin/python nocoly/build/products.py show       # print the live control list

Requirements: nocoly/worksheets/03-products.md. Generic helpers: common.py.
"""
import json, os, sys, uuid
from decimal import Decimal

import common as C
import hap

APP = hap.ids()['app']
SECTION, WORKSHEET, UNITS = 'Products', 'Products', 'Units & Packagings'
KEY = WORKSHEET + ': '                         # ids.json key prefix for everything this worksheet owns


def ws():
    return hap.ids()['worksheets'][WORKSHEET]


def units_ws():
    return hap.ids()['worksheets'][UNITS]


# Odoo saas~19.4 product_template_form_view on HAP's 12-column grid. Header: Name (the favourite star beside
# it), the Sales and Purchase checkboxes under it, the image; then the notebook.
GENERAL, SALES, INVENTORY, ACCOUNTING = 'General Information', 'Sales', 'Inventory', 'Accounting'
TAB_ROWS = {GENERAL: 4, SALES: 11, INVENTORY: 14, ACCOUNTING: 17}
# Re-cut to the live form on 21 Sep 2026 at the owner's ruling "follow whichever used by Odoo". The old rows were
# written before the Taxes bundle inserted Sales Taxes and Purchase Taxes, and everything below them had shifted by
# one, two, three and finally four rows — which is why `prodcat check` and `accounts.py check-b` had been reporting
# Products "out of place" without anything actually being wrong. The order below **is** Odoo's own right-hand group:
# Sales Price · Sales Taxes · Cost · Purchase Taxes · Category · Reference, then Internal Notes as its own group
# (product.template.md › Form). Unit sits beside Cost because Odoo draws the unit inline after both prices.
PLACE = {  # field name -> (row, col, size, tab)
    'Name': (0, 0, 12, None),
    'Favorite': (1, 0, 4, None), 'Sales': (1, 1, 4, None), 'Purchase': (1, 2, 4, None),
    'Image': (2, 0, 12, None),
    'Active': (3, 0, 6, None),                                   # hidden by fieldPermission; Archive/Unarchive set it
    'Product Type': (5, 0, 6, GENERAL), 'Sales Price': (5, 1, 6, GENERAL),      # group_general | group_standard_price
    'Sales Taxes': (6, 0, 12, GENERAL),                          # bundle 6 (13-taxes.md)
    'Unit': (7, 0, 6, GENERAL), 'Cost': (7, 1, 6, GENERAL),
    'Purchase Taxes': (8, 0, 12, GENERAL),                       # bundle 6
    # Category (categ_id) belongs to the Product Categories bundle (nocoly/worksheets/08-product-categories.md,
    # built by prodcat.py), which added it with `add-fields` — that parks a new control at row 9999, and only a
    # full save moves it. This step is that save, so Category lands where Odoo's form has it, after Purchase Taxes.
    'Category': (9, 0, 6, GENERAL), 'Internal Reference': (9, 1, 6, GENERAL),
    'Internal Notes': (10, 0, 12, GENERAL),
    'Packagings': (12, 0, 12, SALES), 'Sales Description': (13, 0, 12, SALES),
    'Weight': (15, 0, 6, INVENTORY), 'Volume': (15, 1, 6, INVENTORY),
    # **Delivery Time is not ours and not Odoo's.** No builder creates it, it is in no ids.json, it carries no alias
    # and no fieldPermission, and 03-products.md lists Delivery Time among the parts of Odoo's Inventory tab that
    # were *not* built. It appeared in the app around 18 Sep 2026. It is placed here so a layout save does not move
    # it, and flagged for the owner: on the "follow Odoo" rule it should go, and deleting needs their approval.
    'Delivery Time': (16, 0, 6, INVENTORY),
    # The tab Accounting and its two accounts belong to the Chart of Accounts bundle (09-chart-of-accounts.md, built
    # by accounts.py `products`), added with `add-fields` and placed by this step, as Category was: after Inventory,
    # where Odoo has the page. Odoo's group title "Cost and Revenue" is left out, as the other group titles are.
    'Income Account': (18, 0, 6, ACCOUNTING), 'Expense Account': (18, 1, 6, ACCOUNTING),
}
HINTS = {'Name': 'e.g. Cheese Burger', 'Internal Notes': 'This note is only for internal purposes.',
         'Sales Description': 'This note is added to sales orders and invoices.',
         'Income Account': 'From Category', 'Expense Account': 'From Category'}   # no other placeholders, as in Odoo
DESC = {  # Odoo field help (product_template.py)
    'Product Type': 'Goods are tangible materials and merchandise you provide.\n'
                    'A service is a non-material product you provide.',
    'Sales Price': 'Price at which the product is sold to customers.',
    'Cost': 'Value of the product (automatically computed in AVCO).\n'
            'Used to value the product when the purchase cost is not known (e.g. inventory adjustment).\n'
            'Used to compute margins on sale orders.',
    'Unit': 'Default unit of measure used for all stock operations.',
    'Packagings': 'Additional packagings for this product which can be used for sales',
    'Sales Description': 'A description of the Product that you want to communicate to your customers. This '
                         'description will be copied to every Sales Order, Delivery Order and Customer '
                         'Invoice/Credit Note',
    'Active': 'If unchecked, it will allow you to hide the product without removing it.',
    # the Chart of Accounts bundle (product.py, property_account_income_id / property_account_expense_id)
    'Income Account': 'Keep this field empty to use the default value from the product category.',
    'Expense Account': 'Keep this field empty to use the default value from the product category. If anglo-saxon '
                       'accounting with automated valuation method is configured, the expense account on the product '
                       'category will be used.',
}
HIDDEN = ['Active']
MYR = json.dumps({'currencycode': 'MYR', 'symbol': 'RM'})
PRODUCT_TYPES = ['Goods', 'Service']           # Combo waits for the Product Combos bundle


def ctl(kind, name, alias='', **kw):
    row, col, size, _ = PLACE[name]
    return C.control(kind, name, (row, col, size), alias=alias, hint=HINTS.get(name, ''), desc=DESC.get(name),
                     hidden=name in HIDDEN, **kw)


def tabs(ctrls):
    return {c['controlName']: c for c in ctrls if c['type'] == C.TAB}


# ── 0 · worksheet ───────────────────────────────────────────────────────────

def step_create():
    section = hap.ids()['sections'][SECTION]
    wid = C.ensure_worksheet(APP, section, WORKSHEET, alias='product_template', icon='sys_13_2_shopping_bag',
                             remark='Odoo product.template: the goods and services a company sells and buys')
    C.remember('worksheets', WORKSHEET, wid)
    items = next(s for s in C.app_info(APP)['sections'] if s['id'] == section)['items']
    order = [wid] + [i['id'] for i in items if i['id'] != wid]       # Odoo: products first, units under them
    if order != [i['id'] for i in items]:
        hap.run('app', 'sort-worksheets', APP, section, *order)
    for s in C.app_info(APP)['sections']:
        print(f"  {s['name']:<10} {s['id']}  {[(i['name'], i['id'], i.get('alias')) for i in s['items']]}")


# ── 1 · base controls ───────────────────────────────────────────────────────

def switch(name, alias, default):
    return ctl('SWITCH', name, alias=alias, advanced_setting={'defsource': C.static_default(default)})


def money(name, alias, default):
    """Currency MYR shown as RM, 2 decimals (Odoo decimal precision 'Product Price')."""
    return ctl('MONEY', name, alias=alias, advanced_setting={'currency': MYR, 'defsource': C.static_default(default)},
               extra={'dot': 2})


def number(name, alias, suffix):
    """2 decimals (Odoo 'Stock Weight' / 'Volume'), default 0, the unit as a suffix (weight_uom_name / volume_uom_name)."""
    return ctl('NUMBER', name, alias=alias, advanced_setting={'suffix': suffix, 'defsource': C.static_default(0)},
               extra={'dot': 2})


def step_fields():
    existing = hap.controls(ws())
    if len(existing) > 3:
        sys.exit(f'{WORKSHEET} already has {len(existing)} controls — refusing to replace them.')
    hap.backup('products_controls_pre_fields', existing)
    stock = hap.by_name(existing)

    name = ctl('TEXT', 'Name', alias='name', required=True, is_title=True)
    name['controlId'] = next(c for c in existing if c.get('attribute') == 1)['controlId']
    image = ctl('ATTACHMENT', 'Image', alias='image_1920')
    if 'Attachment' in stock:
        image['controlId'] = stock['Attachment']['controlId']
    kinds = [{'key': str(uuid.uuid4()), 'value': v, 'index': i + 1, 'checked': v == 'Goods', 'isDeleted': False,
              'color': color} for i, (v, color) in enumerate(zip(PRODUCT_TYPES, ['#C9E6FC', '#C3F2F2']))]
    goods = next(o['key'] for o in kinds if o['checked'])
    kind = ctl('FLAT_MENU', 'Product Type', alias='type', required=True, options=kinds,
               advanced_setting={'defsource': C.static_default(goods), 'showtype': '1', 'direction': '2',
                                 'checktype': '1'})   # Odoo widget="radio" horizontal: showtype 1 flat, direction 2 across
    controls = [
        name, switch('Favorite', 'is_favorite', 0), switch('Sales', 'sale_ok', 1), switch('Purchase', 'purchase_ok', 1),
        image,
        C.control('SECTION', GENERAL, (TAB_ROWS[GENERAL], 0, 12)),
        kind, money('Sales Price', 'list_price', 1), money('Cost', 'standard_price', 0),
        ctl('TEXT', 'Internal Reference', alias='default_code'),
        ctl('RICH_TEXT', 'Internal Notes', alias='description'),
        C.control('SECTION', SALES, (TAB_ROWS[SALES], 0, 12)),
        ctl('TEXT', 'Sales Description', alias='description_sale', extra={'enumDefault': 1}),   # 1 = multi-line
        C.control('SECTION', INVENTORY, (TAB_ROWS[INVENTORY], 0, 12)),
        number('Weight', 'weight', 'kg'), number('Volume', 'volume', 'm³'),
        switch('Active', 'active', 1),
    ]
    C.save_controls(ws(), controls)
    C.show(ws())


# ── 2 · relations ───────────────────────────────────────────────────────────

def step_relations():
    """Unit (uom_id) and Packagings (uom_ids): one-way, so Units & Packagings gets no reverse field."""
    f = C.fields(ws())
    new = [ctl('RELATE_SHEET', name, alias=alias, data_source=units_ws(), multi=multi, required=required,
               advanced_setting={'bidirectional': '0', 'showtype': '3'})             # 3 = dropdown
           for name, alias, multi, required in [('Unit', 'uom_id', False, True), ('Packagings', 'uom_ids', True, False)]
           if name not in f]
    if new:
        before = units_signature()
        C.append_controls(ws(), new)
        check_units_untouched(before)
    C.show(ws())


SIGNATURE = ('controlName', 'type', 'alias', 'row', 'col', 'size', 'sectionId', 'required', 'attribute',
             'fieldPermission', 'dataSource', 'sourceControlId', 'showControls', 'advancedSetting', 'desc', 'hint')


def units_signature():
    """Units & Packagings' controls by id: their listing order changed once after a full save on Products, with
    every attribute unchanged, so position is not compared."""
    return sorted(json.dumps([c['controlId']] + [c.get(k) for k in SIGNATURE], sort_keys=True, ensure_ascii=False)
                  for c in hap.controls(units_ws()))


def check_units_untouched(before):
    after = units_signature()
    if after != before:
        sys.exit(f'{UNITS} controls changed: {sorted(set(after) ^ set(before))}')
    print(f'  {UNITS}: controls unchanged ({len(after)})')


# ── 3 · layout ──────────────────────────────────────────────────────────────

def unit_rows():
    """Units & Packagings records by Unit Name: rowid and Active (record list hides hidden fields, so the
    Active flag comes from the two views' filters)."""
    views = {v['name']: v['viewId'] for v in hap.listing('worksheet', 'view', 'list', units_ws(), '-a', APP)}
    name = C.fields(units_ws())['Unit Name']['controlId']
    out = {}
    for view, active in ((UNITS, True), ('Archived', False)):
        res = hap.run('worksheet', 'record', 'list', units_ws(), '-a', APP, '-n', '200', '--view-id', views[view],
                      '--use-field-id-as-key')
        data = res.get('data', res) if isinstance(res, dict) else res
        for r in (data.get('rows') if isinstance(data, dict) else data) or []:
            out.setdefault(r[name], dict(rowid=r['rowid'], active=active))
    return out


def picker_filters(units, f, exclude_unit=False):
    """Odoo active_test: archived units are not offered. Packagings also leaves out the product's own Unit
    (uom_ids domain [('id', '!=', uom_id)]): the record id is compared with the form's Unit."""
    filters = [{'controlId': units['Active']['controlId'], 'dataType': 36, 'spliceType': 1, 'filterType': C.EQ,
                'values': ['1'], 'value': '1', 'isDynamicsource': False, 'dynamicSource': []}]
    if exclude_unit:
        filters.append({'controlId': 'rowid', 'dataType': 2, 'spliceType': 1, 'filterType': C.NE, 'values': [],
                        'value': '', 'isDynamicsource': True,
                        'dynamicSource': [{'rcid': '', 'cid': f['Unit']['controlId'], 'staticValue': '',
                                           'isAsync': False}]})
    return json.dumps(filters)


def step_layout():
    ctrls = hap.controls(ws())
    hap.backup('products_controls_pre_layout', ctrls)
    tab = {n: c['controlId'] for n, c in tabs(ctrls).items()}
    f = hap.by_name(c for c in ctrls if c['type'] != C.TAB)
    for c in ctrls:
        name = c['controlName']
        if c['type'] == C.TAB:
            c.update(row=TAB_ROWS[name], col=0, size=12, sectionId='')
            continue
        row, col, size, in_tab = PLACE[name]
        c.update(row=row, col=col, size=size, sectionId=tab[in_tab] if in_tab else '', hint=HINTS.get(name, ''))
        if name in DESC:
            c['desc'] = DESC[name]
        c['fieldPermission'] = '011' if name in HIDDEN else '111'
    units = C.fields(units_ws())
    # Odoo's unit dropdown shows "Days --8 Hours--" (uom formatted_display_name): the picker shows each
    # unit's Contains and Reference Unit, as the Reference Unit picker on Units & Packagings does.
    for name in ('Unit', 'Packagings'):
        f[name]['showControls'] = [units['Contains']['controlId'], units['Reference Unit']['controlId']]
        f[name]['advancedSetting']['filters'] = picker_filters(units, f, exclude_unit=name == 'Packagings')
    # Odoo default_get: uom_id = uom.product_uom_unit ("Units"). A static relation default is the record id list.
    rows = unit_rows()
    f['Unit']['advancedSetting']['defsource'] = json.dumps([{'cid': '', 'rcid': '', 'relateSheetName': 'Units',
                                                             'staticValue': json.dumps([rows['Units']['rowid']])}])
    before = units_signature()
    # Through the CLI's session, not the command line: the account Relations' snapshots of Chart of Accounts put
    # the control list past the kernel's argument limit (common.save_controls).
    C.save_controls(ws(), ctrls)
    check_units_untouched(before)
    C.show(ws())


# ── 4 · rules ───────────────────────────────────────────────────────────────

LT = 15                                         # filter operator: less than
MSG_COST = "The cost of a product can't be negative."


def step_rules():
    ctrls = hap.controls(ws())
    f, tab = hap.by_name(c for c in ctrls if c['type'] != C.TAB), tabs(ctrls)
    service = next(o['key'] for o in f['Product Type']['options'] if o['value'] == 'Service')
    rules = [  # (name, type, filters, items, options)
        ('Sales tab only for products that can be sold', C.INTERACTION,        # page sales invisible="not sale_ok"
         C.any_of([C.cond(f['Sales'], C.NE, 1)]), [C.item(C.HIDE, tab[SALES])], {}),
        ('Inventory tab only for goods', C.INTERACTION,                         # page inventory invisible="type in ['service', 'combo']"
         C.any_of([C.cond(f['Product Type'], C.EQ, service)]), [C.item(C.HIDE, tab[INVENTORY])], {}),
        # @onchange _onchange_standard_price raises in the form only; API writes are not checked, as in Odoo.
        ('Cost cannot be negative', C.VALIDATION,
         C.any_of([C.cond(f['Cost'], LT, 0)]), [C.item(C.ERROR, f['Cost'], message=MSG_COST)],
         {'check_type': 0, 'hint_type': 0}),
    ]
    C.upsert_rules(ws(), rules, 'products_rules_pre_rules')


# ── 5 · views ───────────────────────────────────────────────────────────────

def step_views():
    f = C.fields(ws())
    i = lambda *names: [f[n]['controlId'] for n in names]
    # Odoo _order "is_favorite desc, name"; the list shows Favorite, Product Name, Internal Reference, Sales
    # Price, Cost, (On Hand, Forecasted: Inventory,) Unit.
    sort = C.sort_by([(f['Favorite'], False), (f['Name'], True)])
    columns = i('Name', 'Internal Reference', 'Sales Price', 'Cost', 'Unit')
    active = C.switch_filter(f['Active'], 'eq')
    views = {
        # the Products action opens in Kanban: image, name, Internal Reference, Sales Price (and Unit)
        'Products': (dict(viewType='gallery', filter=active,
                          card={'titleField': f['Name']['controlId'],
                                'displayFields': i('Internal Reference', 'Sales Price', 'Unit'),
                                'coverField': f['Image']['controlId'], 'coverDirection': 'left',
                                'coverDisplayMode': 'square'}), sort, None),
        'List': (dict(viewType='table', filter=active, tableFields=columns,
                      quickFilters=[{'fieldId': f['Product Type']['controlId'], 'selectionType': 'single',
                                     'displayType': 'dropdown'}, *i('Sales', 'Purchase', 'Favorite')]),
                 sort, columns),
        'Archived': (dict(viewType='table', filter=C.switch_filter(f['Active'], 'ne'), tableFields=columns),
                     sort, columns),                                  # search filter Archived
    }
    for name, vid in C.upsert_views(ws(), APP, views, 'products_views_pre_views', default_view='List').items():
        C.remember('views', KEY + name, vid)
    print('  order:', C.sort_views(ws(), APP, list(views)))
    C.print_views(ws(), APP)


def step_order():
    """Each view's records in the order the view returns them (the view's own filter and sort)."""
    name, fav = (C.fields(ws())[n]['controlId'] for n in ('Name', 'Favorite'))
    favorites = {r['rowid'] for r in C.records(ws(), APP) if str(r.get(fav)) == '1'}   # a view lists only its columns
    for v in hap.listing('worksheet', 'view', 'list', ws(), '-a', APP):
        res = hap.run('worksheet', 'record', 'list', ws(), '-a', APP, '-n', '100', '--view-id', v['viewId'],
                      '--use-field-id-as-key')
        data = res.get('data', res) if isinstance(res, dict) else res
        rows = (data.get('rows') if isinstance(data, dict) else data) or []
        print(f"  {v['name']} ({len(rows)}): {[r[name] + (' ★' if r['rowid'] in favorites else '') for r in rows]}")


# ── 6 · buttons ─────────────────────────────────────────────────────────────

def step_buttons():
    active = C.fields(ws())['Active']['controlId']
    when = lambda op: {'type': 'group', 'logic': 'AND', 'children': [
        {'type': 'condition', 'field': active, 'operator': op, 'value': ['1']}]}
    buttons = [  # Odoo ⚙ Actions › Archive / Unarchive, as on Contacts and Units & Packagings
        ({'name': 'Archive', 'type': 'triggerWorkflow', 'enableWhen': when('eq'), 'isBatch': True,
          'confirm': True, 'confirmMsg': 'Are you sure that you want to archive this record?',
          'sureName': 'Archive', 'cancelName': 'Cancel'}, [{'fieldId': active, 'value': '0'}], 'Archive the product'),
        ({'name': 'Unarchive', 'type': 'triggerWorkflow', 'enableWhen': when('ne'), 'isBatch': True},
         [{'fieldId': active, 'value': '1'}], 'Unarchive the product'),
    ]
    C.upsert_buttons(ws(), APP, buttons, KEY, 'products_buttons_pre_buttons')
    for key in (KEY + 'Archive', KEY + 'Unarchive'):
        print(C.structure(hap.ids()['workflows'][key]))


# ── 7 · seed and verify ─────────────────────────────────────────────────────

REFERENCE = os.path.join(hap.HERE, '..', 'reference', 'odoo-19.4', 'product.template.md')


def reference_table():
    """The 14 records of the 19.4 extract, by Name: Internal Reference, Product Type, Sales, Purchase, Sales
    Price, Cost, Unit (table "Records") and Sales Description (table "Sales descriptions")."""
    out, section = {}, None
    for line in open(REFERENCE, encoding='utf-8'):
        if line.startswith('#'):
            section = line.strip('# \n')
            continue
        cells = [x.strip() for x in line.strip().strip('|').split('|')] if line.startswith('|') else []
        if section.startswith('Records') and len(cells) == 12 and cells[2] in PRODUCT_TYPES:
            out[cells[0]] = dict(code=cells[1], type=cells[2], sale_ok=cells[3] == '✓', purchase_ok=cells[4] == '✓',
                                 list_price=Decimal(cells[5]), standard_price=Decimal(cells[6]), uom=cells[7])
        elif section == 'Sales descriptions' and len(cells) == 2 and cells[0] in out:
            out[cells[0]]['description_sale'] = cells[1]
    return out


def number_value(v):
    return Decimal(str(v)) if v not in (None, '') else None


def fmt(d):
    return '-' if d is None else format(d.normalize(), 'f')


def listed(v):
    """A record-get option or relation value (a list, or a JSON string of one) as a list."""
    if isinstance(v, str):
        v = json.loads(v) if v.startswith('[') else []
    return v if isinstance(v, list) else []


def read_product(rowid):
    """One product through `record get` (by alias); `record list` returns hidden fields empty."""
    d = hap.run('worksheet', 'record', 'get', ws(), rowid, '-a', APP)['data']
    kind = [x.get('value') if isinstance(x, dict) else x for x in listed(d.get('type'))]
    unit = [x.get('name') for x in listed(d.get('uom_id'))]
    flag = lambda k: str(d.get(k)) in ('1', 'True', 'true')
    return dict(rowid=rowid, name=d.get('name'), code=d.get('default_code') or '', type=kind[0] if kind else None,
                sale_ok=flag('sale_ok'), purchase_ok=flag('purchase_ok'), is_favorite=flag('is_favorite'),
                active=flag('active'), list_price=number_value(d.get('list_price')),
                standard_price=number_value(d.get('standard_price')), uom=unit[0] if unit else None,
                packagings=d.get('uom_ids'), description_sale=d.get('description_sale') or '',
                weight=number_value(d.get('weight')), volume=number_value(d.get('volume')),
                description=d.get('description') or '')


def read_products():
    name = C.fields(ws())['Name']['controlId']
    return {r[name]: read_product(r['rowid']) for r in C.records(ws(), APP)}


def expected(e):
    """The live values a seeded product must have."""
    return dict(code=e['code'], type=e['type'], sale_ok=e['sale_ok'], purchase_ok=e['purchase_ok'],
                list_price=e['list_price'], standard_price=e['standard_price'], uom=e['uom'],
                description_sale=e['description_sale'], active=True, is_favorite=False,
                weight=Decimal(0), volume=Decimal(0))


def differences(live, e):
    """{field: (live, expected)} where they differ; numbers compare by value (1890.00 == 1890)."""
    want = expected(e)
    return {k: (str(live.get(k)), str(v)) for k, v in want.items() if live.get(k) != v}


def step_seed(*only):
    """Create the missing products and correct the ones that differ from the extract. `only` limits it to names."""
    f = C.fields(ws())
    cid = lambda n: f[n]['controlId']
    kinds = {o['value']: o['key'] for o in f['Product Type']['options']}
    units = unit_rows()
    products = read_products()
    hap.backup('products_records_pre_seed', {k: {a: str(b) for a, b in v.items()} for k, v in products.items()})
    for name, e in reference_table().items():
        if only and name not in only:
            continue
        live = products.get(name)
        if live and not differences(live, e):
            continue
        values = [{'id': cid('Name'), 'value': name},
                  {'id': cid('Internal Reference'), 'value': e['code']},
                  {'id': cid('Product Type'), 'value': [kinds[e['type']]]},
                  {'id': cid('Sales'), 'value': 1 if e['sale_ok'] else 0},
                  {'id': cid('Purchase'), 'value': 1 if e['purchase_ok'] else 0},
                  {'id': cid('Favorite'), 'value': 0},
                  {'id': cid('Sales Price'), 'value': str(e['list_price'])},
                  {'id': cid('Cost'), 'value': str(e['standard_price'])},
                  {'id': cid('Unit'), 'value': [units[e['uom']]['rowid']]},
                  {'id': cid('Sales Description'), 'value': e['description_sale']},
                  {'id': cid('Weight'), 'value': '0'}, {'id': cid('Volume'), 'value': '0'},    # 0 on the tenant
                  {'id': cid('Active'), 'value': 1}]                                    # always explicit on API writes
        if live:
            hap.run('worksheet', 'record', 'update', ws(), live['rowid'], '-a', APP,
                    '--fields-json', json.dumps(values, ensure_ascii=False))
            rowid = live['rowid']
            print(f'  updated {name}')
        else:
            rowid = C.row_id(hap.run('worksheet', 'record', 'create', ws(), '-a', APP,
                                     '--fields-json', json.dumps(values, ensure_ascii=False)))
            print(f'  created {name}: {rowid}')
        got = products[name] = read_product(rowid)
        if got['name'] != name or differences(got, e):
            sys.exit(f'{name}: read back {differences(got, e)}')
    step_verify(*only)


def step_verify(*only):
    """Compare the live products with the 19.4 extract, field by field."""
    reference, products = reference_table(), read_products()
    bad = 0
    for name, e in reference.items():
        if only and name not in only:
            continue
        live = products.get(name)
        if not live:
            print(f'  MISSING  {name}')
            bad += 1
            continue
        diffs = differences(live, e)
        bad += bool(diffs)
        print(f"  {'OK  ' if not diffs else 'DIFF'}  {name:<31} {live['code'] or '-':<9} {str(live['type']):<7} "
              f"sales={int(live['sale_ok'])} purchase={int(live['purchase_ok'])} price={fmt(live['list_price'])} "
              f"cost={fmt(live['standard_price'])} unit={live['uom']} active={int(live['active'])} "
              f"favorite={int(live['is_favorite'])}" + (f'  <- {diffs}' if diffs else ''))
    extra = sorted(set(products) - set(reference))
    print(f'  {len(reference)} in the extract; {bad} missing or differing; {len(extra)} not in the extract {extra}')
    return bad


def step_product(*names):
    """Print the live values of products by name, hidden fields included."""
    products = read_products()
    for name in names or sorted(products):
        p = products.get(name)
        print(f'  {name}: ' + (json.dumps({k: str(v) for k, v in p.items()}, ensure_ascii=False) if p else 'no such product'))


def show():
    C.show(ws())


if __name__ == '__main__':
    steps = {'create': step_create, 'fields': step_fields, 'relations': step_relations, 'layout': step_layout,
             'rules': step_rules, 'views': step_views, 'buttons': step_buttons, 'seed': step_seed,
             'verify': step_verify, 'order': step_order, 'product': step_product, 'show': show}
    steps[sys.argv[1] if len(sys.argv) > 1 else 'show'](*sys.argv[2:])
