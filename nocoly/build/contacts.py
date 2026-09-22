#!/usr/bin/env python3
"""Build the Contacts worksheet (Odoo res.partner, as on casimir.odoo.com saas~19.4) in ERP Master.

    ~/.hap-venv/bin/python nocoly/build/contacts.py fields       # 1. controls, in one save (then display, layout)
    ~/.hap-venv/bin/python nocoly/build/contacts.py display      # 1b. Display Name (complete_name) as the title field
    ~/.hap-venv/bin/python nocoly/build/contacts.py layout       # 2. positions, tabs, company filter, reverse columns
    ~/.hap-venv/bin/python nocoly/build/contacts.py rules        # 3. rules (upsert by name, obsolete ones disabled)
    ~/.hap-venv/bin/python nocoly/build/contacts.py views        # 4. Contacts / Kanban / Archived views
    ~/.hap-venv/bin/python nocoly/build/contacts.py buttons      # 5. Archive / Unarchive buttons and their workflows
    ~/.hap-venv/bin/python nocoly/build/contacts.py automations  # 6. company -> contact sync workflows (create or update)
    ~/.hap-venv/bin/python nocoly/build/contacts.py to194        # one-off, already applied: moved the Odoo 19.0 build to 19.4
    ~/.hap-venv/bin/python nocoly/build/contacts.py names        # print every contact's Name and Display Name
    ~/.hap-venv/bin/python nocoly/build/contacts.py show         # print the live control list

Requirements: nocoly/worksheets/01-contacts.md.

`fields` replaces the whole control set, so it only runs on a worksheet that has
no records yet. After that, append with `hap worksheet add-fields`.

**Countries (bundle 4, 18 Sep 2026).** The text control Country (`6aa8a452f363582dd37a50e7`) was replaced by a
one-way relation to the Countries worksheet and **deleted**, with the owner's approval, once every contact's
value had been carried across and read back (`11-countries.md`). `countries.py` creates, aliases and places the
relation; everything here that names Country resolves it **by name**, so `layout` keeps it in its old cell
(row 9, right half), `views` points the Country column, the Country quick filter and the Kanban card field at
it, and `automations` copies it between a company and its contacts as one of the six address fields. What
changed in this file is `ADDRESS_TEXT` — the address fields that are still Text — and `address_nodes`,
which re-points the two address-sync workflows the way `term_nodes` re-points bundle 3's.

**States (bundle 5, 18 Sep 2026).** The same again for State (`6aa8a452f363582dd37a50e5`): a one-way relation
to the States worksheet in the text control's cell — row 8, right half, beside City — and the text control
deleted once the eight contacts that had one had been carried across and read back (`12-states.md`,
`states.py`). `ADDRESS_TEXT` is now the **four** address fields still built here as Text; `HINTS` lost its
`State` entry as it lost `Country`, and `arrange` never writes a hint on a Relation. No view of Contacts ever
named State, so `views` had nothing to re-point. `states.py` also adds workflows **E** and **F**, which keep a
contact's Country and State in step (Odoo's two address onchanges) — they are not built here.
"""
import json, subprocess, sys, uuid

from hap_cli.core import worksheet_templates as wt
from hap_cli.core.app_creator.fields import bidirectional_relation_control, field_permission_str

import common as C
import hap

WS = hap.ids()['worksheets']['Contacts']
MALAYSIA = json.dumps({'name': 'Malaysia', 'iso2': 'my', 'dialCode': '60'})
# Odoo res.partner._address_fields: the six a company shares with its contacts. Both sync automations copy all
# six, and every one of them is looked up by name — so Country here is the **relation to Countries** that
# bundle 4 put in the text control's place (11-countries.md, countries.py).
ADDRESS = ['Street', 'Street 2', 'City', 'State', 'ZIP', 'Country']
# …and these four are the ones still built here as Text. Country and State are not: countries.py and states.py
# add them as Relations, with no hint — HINTS therefore no longer carries one for either, and `arrange` never
# writes a hint on a Relation.
ADDRESS_TEXT = [('Street', 'street'), ('Street 2', 'street2'), ('City', 'city'), ('ZIP', 'zip')]

# Odoo saas~19.4 view_partner_form on HAP's 12-column grid: name -> (row, col, size, tab)
PLACE = {
    'Name': (0, 0, 12, None),
    'Company': (1, 0, 6, None), 'Address Type': (1, 1, 6, None),
    'Email': (2, 0, 6, None), 'Phone': (2, 1, 6, None),
    'Job Position': (3, 0, 6, None), 'Website': (3, 1, 6, None),
    'Tax ID': (4, 0, 6, None), 'Company ID': (4, 1, 6, None),
    'DUNS': (5, 0, 6, None),
    'Address': (6, 0, 12, None),
    'Street': (7, 0, 6, None), 'Street 2': (7, 1, 6, None),
    'City': (8, 0, 6, None), 'State': (8, 1, 6, None),
    # State is a Relation → States since bundle 5 and Country a Relation → Countries since bundle 4; each keeps
    # the cell its text control had (12 §1, 11 §1)
    'ZIP': (9, 0, 6, None), 'Country': (9, 1, 6, None),
    'Image': (10, 0, 12, None),
    'Contacts': (12, 0, 12, 'Contacts'),
    # The Payment Terms bundle (10-payment-terms.md, payterms.py `contacts`) adds Customer and Vendor Payment Terms in
    # Odoo's order — Sales, Purchase, Misc: Salesperson | Customer Payment Terms, then Vendor Payment Terms on its own
    # row, above the Misc divider so it is not read as a Misc field; Reference and everything under it moved down.
    'Sales': (14, 0, 12, 'Sales & Purchase'), 'Salesperson': (15, 0, 6, 'Sales & Purchase'),
    'Customer Payment Terms': (15, 1, 6, 'Sales & Purchase'),
    'Vendor Payment Terms': (16, 0, 6, 'Sales & Purchase'),
    'Misc': (17, 0, 12, 'Sales & Purchase'), 'Reference': (18, 0, 6, 'Sales & Purchase'),
    # The tab Invoicing and its two accounts belong to the Chart of Accounts bundle (09-chart-of-accounts.md,
    # built by accounts.py `contacts`), which adds them with `add-fields` — that parks a new control at row 9999,
    # and only a full save moves it. This step is that save, so they are placed here, between Sales & Purchase and
    # Notes where Odoo has the page; Notes and everything under it moved down two rows to make room.
    'Account Receivable': (20, 0, 6, 'Invoicing'), 'Account Payable': (20, 1, 6, 'Invoicing'),
    'Notes': (22, 0, 12, 'Notes'),
    'Active': (23, 0, 6, None),
    'Display Name': (24, 0, 12, None),
    'Parent name': (25, 0, 6, None),
}
TABS = {'Contacts': 11, 'Sales & Purchase': 13, 'Invoicing': 19, 'Notes': 21}
HINTS = {'Name': 'Name (company or person)', 'Company': 'Company Employer', 'Email': 'Email', 'Phone': 'Phone',
         'Job Position': 'e.g. Sales Director', 'Website': 'e.g. https://www.example.com', 'Tax ID': 'Tax ID',
         'Company ID': 'Company ID', 'DUNS': 'DUNS', 'Street': 'Street...', 'Street 2': 'Street 2...',
         'City': 'City', 'ZIP': 'ZIP', 'Image': 'Upload an image',
         'Salesperson': 'Salesperson', 'Reference': 'Reference', 'Notes': 'Internal notes...'}
OBSOLETE_RULES = ['Company is hidden on companies', 'Job Position only for persons',
                  'Company ID only on stand-alone companies']       # 19.0 rules; 19.4 has no Person/Company switch


def options(labels, default):
    """Option dicts with stable keys, the default marked."""
    return [{'key': str(uuid.uuid4()), 'value': v, 'index': i + 1, 'checked': v == default,
             'isDeleted': False, 'color': c}
            for i, (v, c) in enumerate(zip(labels, ['#C9E6FC', '#C3F2F2', '#C2F1D2', '#FFE7B1']))]


def default_option(opts):
    key = next(o['key'] for o in opts if o['checked'])
    return json.dumps([{'cid': '', 'rcid': '', 'staticValue': key}])


def ctl(kind, name, alias='', **kw):
    row, col, size, _ = PLACE.get(name, (TABS.get(name, 0), 0, 12, None))
    c = wt.build_control(kind, name, row=row, col=col, size=size, hint=HINTS.get(name), **kw)
    c['alias'] = alias
    return c


def step_fields():
    existing = hap.controls(WS)
    if len(existing) > 3:
        sys.exit(f'Contacts already has {len(existing)} controls — refusing to replace them.')
    hap.backup('contacts_controls_pre_fields', existing)
    keep = hap.by_name(existing)                      # reuse the default Name and Attachment ids
    address_type = options(['Contact', 'Invoice', 'Delivery', 'Other'], default='Contact')

    name = ctl('TEXT', 'Name', alias='name', is_title=True)
    name['controlId'] = keep['Name']['controlId']
    company = bidirectional_relation_control(
        'Company', target_worksheet_id=WS, host_worksheet_id=WS,
        forward_id=str(uuid.uuid4()), reverse_id=str(uuid.uuid4()), reverse_name='Contacts',
        multi=False, display='dropdown', reverse_display='table')
    company.update(alias='parent_id', hint=HINTS['Company'])
    image = ctl('ATTACHMENT', 'Image', alias='image_1920')
    image['controlId'] = keep['Attachment']['controlId']
    active = ctl('SWITCH', 'Active', alias='active',
                 advanced_setting={'defsource': json.dumps([{'cid': '', 'rcid': '', 'staticValue': '1'}])})
    active['fieldPermission'] = field_permission_str(hidden=True)

    c = [name, company,
         ctl('DROP_DOWN', 'Address Type', alias='type', required=True, options=address_type,
             advanced_setting={'defsource': default_option(address_type)}),
         ctl('EMAIL', 'Email', alias='email'),
         ctl('MOBILE_PHONE', 'Phone', alias='phone', advanced_setting={'defaultarea': MALAYSIA}),
         ctl('TEXT', 'Job Position', alias='function'), ctl('TEXT', 'Website', alias='website'),
         ctl('TEXT', 'Tax ID', alias='vat'),
         ctl('TEXT', 'Company ID', alias='company_registry'),       # 19.4: additional identifier "Company ID"
         ctl('TEXT', 'DUNS', alias='duns'),                         # 19.4: additional identifier "DUNS"
         ctl('SPLIT_LINE', 'Address'),
         *[ctl('TEXT', n, alias=a) for n, a in ADDRESS_TEXT],      # State and Country are Relations (bundles 5 and 4)
         image,
         ctl('SECTION', 'Contacts'), ctl('SECTION', 'Sales & Purchase'), ctl('SECTION', 'Notes'),
         ctl('SPLIT_LINE', 'Sales'), ctl('USER_PICKER', 'Salesperson', alias='user_id'),
         ctl('SPLIT_LINE', 'Misc'), ctl('TEXT', 'Reference', alias='ref'),
         ctl('RICH_TEXT', 'Notes', alias='comment'),
         active]
    C.save_controls(WS, c)
    step_display()
    step_layout()


def arrange(ctrls):
    """Positions, tabs, hints, the Company picker filter and the reverse Contacts columns, in place."""
    tabs = {c['controlName']: c['controlId'] for c in ctrls if c['type'] == 52}
    field = {c['controlName']: c for c in ctrls if c['type'] != 52}
    for c in ctrls:
        if c['type'] == 52:
            c.update(row=TABS[c['controlName']], col=0, size=12, sectionId='')
            continue
        row, col, size, tab = PLACE[c['controlName']]
        c.update(row=row, col=col, size=size, sectionId=tabs[tab] if tab else '')
        if c['controlName'] in HINTS and c['type'] not in (22, 29):
            c['hint'] = HINTS[c['controlName']]
    company = field['Company']
    company['hint'] = HINTS['Company']
    # Odoo 19.4 parent_id domain [('parent_id', '=', False)]: any contact that has no company itself;
    # Odoo's active_test also leaves archived contacts out of the picker
    company['advancedSetting']['filters'] = json.dumps([
        {'controlId': company['controlId'], 'dataType': 29, 'spliceType': 1, 'filterType': 7,
         'values': [], 'value': '', 'isDynamicsource': False, 'dynamicSource': []},
        {'controlId': field['Active']['controlId'], 'dataType': 36, 'spliceType': 1, 'filterType': 2,
         'values': ['1'], 'value': '1', 'isDynamicsource': False, 'dynamicSource': []}])
    reverse = field['Contacts']
    reverse['alias'] = 'child_ids'            # a new reverse control comes back at row 9999, width 0, no alias
    cols = [field[n]['controlId'] for n in ('Name', 'Address Type', 'Email', 'Phone', 'Job Position')]
    reverse['showControls'] = cols
    reverse['advancedSetting']['controlssorts'] = json.dumps(cols)


def step_layout():
    ctrls = hap.controls(WS)
    hap.backup('contacts_controls_pre_layout', ctrls)
    arrange(ctrls)
    C.save_controls(WS, ctrls)
    show()


DISPLAYED_TYPES = ['Invoice', 'Delivery', 'Other']   # res.partner _complete_name_displayed_types
DESC = {
    'Parent name': "The name of the contact's company.",
    'Display Name': 'How this contact appears in lists and pickers: the Company\'s name, a comma and the Name — '
                    'or the Address Type for a nameless address.',
    # The Chart of Accounts bundle's two accounts (09 §1; Odoo has no help on either field). accounts.py writes
    # and checks them; `display` and `layout` here never rewrite a description.
    'Account Receivable': "The account this contact's customer invoices are recorded on.",
    'Account Payable': "The account this contact's vendor bills are recorded on.",
    # The Payment Terms bundle's two terms (10 §1; Odoo has no help on either). payterms.py writes and checks them.
    'Customer Payment Terms': "A customer invoice for this contact takes these terms. A contact given a company takes "
                              "the company's; a company's change reaches all its contacts.",
    'Vendor Payment Terms': "A vendor bill for this contact takes these terms. A contact given a company takes the "
                            "company's; a company's change reaches all its contacts.",
}
# A hidden field drops out of table columns (cards and pickers still get the title), so Display Name is shown
# read-only, once the record exists; Parent name is hidden.
PERMISSION = {'Parent name': field_permission_str(hidden=True),
              'Display Name': field_permission_str(readonly=True, hidden_on_create=True)}


def complete_name_expression(f):
    """Odoo _get_complete_name (res_partner.py:378) as a HAP function formula — a number formula has no IF.

    Function formulas take plain function names (IF, not cIF), compare option labels as text, and read the
    Company's Name through the stored lookup Parent name. Odoo strips the result; TRIM does the same."""
    ref = lambda n: f"${f[n]['controlId']}$"
    name, company, parent, kind = ref('Name'), ref('Company'), ref('Parent name'), ref('Address Type')
    typed = ','.join(f'{kind}=="{t}"' for t in DISPLAYED_TYPES)
    return (f'IF(ISBLANK({company}),TRIM({name}),'
            f'TRIM(CONCAT({parent},", ",IF(AND(ISBLANK({name}),OR({typed})),{kind},{name}))))')


def function_source(expression):
    """dataSource of a function formula (type 53)."""
    return json.dumps({'type': 'mdfunction', 'expression': expression, 'status': 1}, ensure_ascii=False)


def step_display():
    """Display Name (Odoo complete_name) as the title field: a stored lookup of the Company's Name (Odoo
    parent_name), hidden, and a text function formula, read-only. Name keeps its rules. Safe to re-run."""
    def fields():
        return hap.by_name(c for c in hap.controls(WS) if c['type'] != 52)

    def append(control):
        # add-fields keeps the client-side id, and a formula saved under it computes nothing; a full save of
        # the control set re-mints it
        hap.run('worksheet', 'add-fields', WS, '--controls', json.dumps([control], ensure_ascii=False))
        C.save_controls(WS, hap.controls(WS))

    hap.backup('contacts_controls_pre_display', hap.controls(WS))
    f = fields()
    if 'Parent name' not in f:
        append(ctl('SHEET_FIELD', 'Parent name', alias='parent_name', data_source=f['Company']['controlId'],
                   source_control_id=f['Name']['controlId'], extra={'strDefault': '00'}))   # '00' = stored
        f = fields()
    if 'Display Name' not in f:
        append(ctl('FORMULA_FUNC', 'Display Name', alias='complete_name',
                   advanced_setting={'analysislink': '1', 'sorttype': 'en'},
                   extra={'enumDefault2': 2, 'dataSource': function_source(complete_name_expression(f))}))  # 2 = text
    ctrls = hap.controls(WS)
    f = hap.by_name(c for c in ctrls if c['type'] != 52)
    want = {c['controlId']: 1 if c['controlName'] == 'Display Name' else 0 for c in ctrls}
    stale = [c['controlName'] for c in ctrls if (c.get('attribute') or 0) != want[c['controlId']]]
    display = f['Display Name']
    expression = complete_name_expression(f)
    if json.loads(display.get('dataSource') or '{}').get('expression') != expression:
        print(f"  Display Name: read back {display.get('dataSource')!r}; rewriting")
        display['dataSource'] = function_source(expression)
        stale.append('Display Name expression')
    for name, permission in PERMISSION.items():
        if (f[name].get('desc'), f[name].get('fieldPermission')) != (DESC[name], permission):
            f[name].update(desc=DESC[name], fieldPermission=permission)
            stale.append(f'{name} description / permission')
    for c in ctrls:
        c['attribute'] = want[c['controlId']]           # one title field: Display Name, no longer Name
    if stale:
        C.save_controls(WS, ctrls)
        print(f'  updated: {stale}')
    show()


def step_names():
    """Every contact's Name, Company, Address Type and Display Name, read one by one (lists hide hidden fields)."""
    app = hap.ids()['app']
    rows = hap.run('worksheet', 'record', 'list', WS, '-a', app, '-n', '200', '--use-field-id-as-key')
    rows = rows.get('data', rows) if isinstance(rows, dict) else rows
    rows = rows.get('rows', rows) if isinstance(rows, dict) else rows
    for r in rows:
        d = hap.run('worksheet', 'record', 'get', WS, r['rowid'], '-a', app)['data']
        company = d.get('parent_id') or []
        company = json.loads(company) if isinstance(company, str) and company.startswith('[') else company
        kind = d.get('type') or []
        kind = json.loads(kind) if isinstance(kind, str) and kind.startswith('[') else kind
        print(f"  {d.get('complete_name')!r:<48} name={d.get('name')!r} company={[x.get('name') for x in company]} "
              f"type={[x.get('value', x) if isinstance(x, dict) else x for x in kind]} "
              f"parent_name={d.get('parent_name')!r} active={d.get('active')} rowid={r['rowid']}")


SHOW, HIDE, REQUIRE, ERROR = 1, 2, 5, 6          # rule item types
EQ, NE, EMPTY, NOT_EMPTY = 2, 6, 7, 8             # filter operators


def cond(c, op, key=None):
    return {'controlId': c['controlId'], 'dataType': c['type'], 'spliceType': 1, 'filterType': op,
            'value': '', 'values': [key] if key else [], 'dynamicSource': [], 'isGroup': False}


def any_of(*groups):
    """OR of AND-groups: any_of([a, b], [c]) == (a and b) or c."""
    return [{'controlId': '', 'dataType': 1, 'spliceType': 2, 'filterType': 0, 'value': '', 'values': [],
             'dynamicSource': [], 'isGroup': True, 'groupFilters': list(g)} for g in groups]


def item(kind, *ctrls, message=''):
    return {'type': kind, 'isAll': False, 'message': message,
            'controls': [{'isCustom': False, 'controlId': c['controlId'], 'childControlIds': [],
                          'permission': [], 'type': '', 'value': ''} for c in ctrls]}


RULE_INVOICING = 'Invoicing hidden for a contact under a company'   # bundle 2, Chart of Accounts


def step_rules():
    ctrls = hap.controls(WS)
    f = hap.by_name(c for c in ctrls if c['type'] != 52)
    tab = {c['controlName']: c for c in ctrls if c['type'] == 52}   # "Contacts" and "Notes" are a tab and a field
    contact = next(o['key'] for o in f['Address Type']['options'] if o['value'] == 'Contact')
    rules = [  # (name, type 0=interaction 1=validation, filters, items)
        ('Address Type only under a company', 0,        # Odoo edits `type` only in a sub-contact's form
         any_of([cond(f['Company'], EMPTY)]), [item(HIDE, f['Address Type'])]),
        ('Name is required for contacts', 0,
         any_of([cond(f['Address Type'], EQ, contact)]), [item(REQUIRE, f['Name'])]),
        ('Contacts require a name', 1,                   # Odoo constraint _check_name
         any_of([cond(f['Address Type'], EQ, contact), cond(f['Name'], EMPTY)]),
         [item(ERROR, f['Name'], message='Contacts require a name')]),
    ]
    if 'Invoicing' in tab:
        # <page name="accounting" invisible="not is_company and parent_id">: a contact under a company posts through
        # the company's accounts. Written as a hide while Company is set, so a new contact — no Company yet — shows
        # the tab, as Odoo does. The tab arrives with the Chart of Accounts bundle (accounts.py `contacts`).
        rules.append((RULE_INVOICING, 0, any_of([cond(f['Company'], NOT_EMPTY)]), [item(HIDE, tab['Invoicing'])]))
    live = {r['name']: r for r in hap.listing('worksheet', 'rules', WS)}
    hap.backup('contacts_rules_pre_rules', list(live.values()))
    for name, kind, filters, items in rules:
        args = ['worksheet', 'save-rule', WS, '--name', name, '--type', str(kind),
                '--filters', json.dumps(filters), '--rule-items', json.dumps(items, ensure_ascii=False)]
        if kind == 1:
            args += ['--check-type', '1', '--hint-type', '0']      # enforce on API writes too
        if name in live:
            args += ['--rule-id', live[name]['ruleId']]
        hap.run(*args)
    for name in OBSOLETE_RULES:
        r = live.get(name)
        if r and not r['disabled']:     # the CLI has no rule delete; disable, and delete in the form designer
            hap.run('worksheet', 'save-rule', WS, '--rule-id', r['ruleId'], '--name', name, '--type', str(r['type']),
                    '--filters', json.dumps(r['filters']), '--rule-items', json.dumps(r['ruleItems']), '--disabled')
    for r in hap.listing('worksheet', 'rules', WS):
        acts = [(i['type'], [c['controlId'][-4:] for c in i['controls']], i.get('message', '')) for i in r['ruleItems']]
        print(f"type={r['type']} check={r.get('checkType')} disabled={r['disabled']}  {r['name']:<42} {acts}")


def step_views():
    app = hap.ids()['app']
    f = hap.by_name(c for c in hap.controls(WS) if c['type'] != 52)
    i = lambda *names: [f[n]['controlId'] for n in names]
    active = lambda op: {'type': 'group', 'logic': 'AND', 'children': [
        {'type': 'condition', 'field': f['Active']['controlId'], 'operator': op, 'value': ['1']}]}
    # Odoo _order is complete_name ASC. --view-spec ignores sort keys, so sort is set with --view-json below.
    display = f['Display Name']
    sort = {'sortCid': display['controlId'], 'sortType': 2,
            'moreSort': [{'controlId': display['controlId'], 'dataType': display['type'], 'spliceType': 0,
                          'filterType': 0, 'dateRange': 0, 'dateRangeType': 0, 'value': '', 'values': [],
                          'minValue': '', 'maxValue': '', 'isAsc': True, 'dynamicSource': [], 'advancedSetting': {},
                          'isGroup': False, 'groupFilters': [], 'emptyRule': 0}]}
    # Odoo 19.4 list shows display_name ("Company, Person"), email, phone, country by default. A table leaves out
    # hidden fields, title or not, which is why Display Name is read-only rather than hidden (see PERMISSION).
    columns = i('Display Name', 'Email', 'Phone', 'Country')
    views = {
        'Contacts': dict(viewType='table', filter=active('eq'), tableFields=columns,
                         quickFilters=i('Salesperson', 'Company', 'Country')),
        'Kanban': dict(viewType='gallery', filter=active('eq'),
                       card={'titleField': display['controlId'],
                             'displayFields': i('Email', 'Phone', 'City', 'Country'),
                             'coverField': f['Image']['controlId'], 'coverDirection': 'left',
                             'coverDisplayMode': 'square'}),
        'Archived': dict(viewType='table', filter=active('ne'), tableFields=columns),
    }
    live = hap.listing('worksheet', 'view', 'list', WS, '-a', app)
    hap.backup('contacts_views_pre_views', live)
    live = {v['name']: v['viewId'] for v in live}
    if 'Contacts' not in live and 'All' in live:                            # the default view becomes Contacts
        live['Contacts'] = live.pop('All')
    for name, spec in views.items():
        spec = {'name': name, **spec}
        if name in live:
            hap.run('worksheet', 'view', 'update', WS, live[name], '-a', app, '--view-spec', json.dumps(spec))
        else:
            hap.run('worksheet', 'view', 'create', WS, name, '-a', app, '--view-spec', json.dumps(spec))
    for v in hap.listing('worksheet', 'view', 'list', WS, '-a', app):
        hap.run('worksheet', 'view', 'update', WS, v['viewId'], '-a', app,
                '--view-json', json.dumps(sort), '--edit-attrs', 'sortCid,sortType,moreSort')
        if v['viewType'] == 0:
            # a table's columns are showControls (+ customShowControls); --view-spec's tableFields only
            # sets displayControls, and the table then shows every field
            hap.run('worksheet', 'view', 'update', WS, v['viewId'], '-a', app, '--view-json', json.dumps({
                'showControls': columns,
                'advancedSetting': {'customdisplay': '1', 'customShowControls': json.dumps(columns)}}),
                '--edit-attrs', 'showControls,advancedSetting', '--edit-ad-keys', 'customdisplay,customShowControls')
    names = {c['controlId']: c['controlName'] for c in f.values()}
    for v in hap.listing('worksheet', 'view', 'list', WS, '-a', app):
        print(f"{v['name']:<9} type={v['viewType']} sort={names.get(v.get('sortCid'), v.get('sortCid'))}/{v.get('sortType')} "
              f"customDisplay={v.get('customDisplay')} filters={len(v.get('filters') or [])} "
              f"fast={[names.get(x['controlId']) for x in v.get('fastFilters') or []]} "
              f"columns={[names.get(x, x) for x in v.get('showControls') or []]} "
              f"card={[names.get(x, x) for x in v.get('displayControls') or []]} cover={names.get(v.get('coverCid'), '')}")


def button_workflow(process_id, fields, node_name):
    """Trigger by button -> update the triggering record -> publish (as lib/button_flows.py in the Sales repo)."""
    proc = hap.run('workflow', 'node', 'list', process_id)
    trigger = proc['startEventId']
    first = proc['flowNodeMap'][trigger].get('nextId')
    if first not in (None, '', '99'):                 # '99' is the end marker; virtual nodes hang off-chain
        print(f'  {node_name}: workflow {process_id} already has steps; left as is')
        return
    spec = [{'nodeAlias': 'upd', 'nodeType': 'update_record', 'name': node_name,
             'config': {'target': {'node': {'nodeAlias': 'trigger'}}, 'fields': fields}}]
    hap.run('workflow', 'node', 'batch-add', process_id, '--nodes', json.dumps(spec),
            '--trigger-node-id', trigger, '--trigger-alias', 'trigger')
    hap.run('workflow', 'publish', process_id)


def step_buttons():
    app = hap.ids()['app']
    f = hap.by_name(c for c in hap.controls(WS) if c['type'] != 52)
    active = f['Active']['controlId']
    when = lambda op: {'type': 'group', 'logic': 'AND', 'children': [
        {'type': 'condition', 'field': active, 'operator': op, 'value': ['1']}]}
    buttons = [  # Odoo ⚙ Actions › Archive / Unarchive
        ({'name': 'Archive', 'type': 'triggerWorkflow', 'enableWhen': when('eq'), 'isBatch': True,
          'confirm': True, 'confirmMsg': 'Are you sure that you want to archive this record?',
          'sureName': 'Archive', 'cancelName': 'Cancel'}, '0', 'Archive the contact'),
        ({'name': 'Unarchive', 'type': 'triggerWorkflow', 'enableWhen': when('ne'), 'isBatch': True},
         '1', 'Unarchive the contact'),
    ]
    live = hap.listing('worksheet', 'custom-actions', WS)
    hap.backup('contacts_buttons_pre_buttons', live)
    live = {b['name']: b for b in live}
    ids = hap.ids()
    for spec, value, node_name in buttons:
        if spec['name'] in live:
            # create-custom-action --action-spec ignores --btn-id and always adds a new button (hap-cli 0.8.31)
            print(f"  {spec['name']}: exists ({live[spec['name']]['btnId']}); not re-created")
            continue
        out = hap.run('worksheet', 'create-custom-action', WS, '-a', app, '--action-spec', json.dumps(spec))
        data = out.get('data', out) if isinstance(out, dict) else {}
        pid = data.get('processId') or ids.get('workflows', {}).get(spec['name'])
        if not pid:
            sys.exit(f"{spec['name']}: no processId in create-custom-action output: {out}")
        ids.setdefault('workflows', {})[spec['name']] = pid
        button_workflow(pid, [{'fieldId': active, 'value': value}], node_name)
    for b in hap.listing('worksheet', 'custom-actions', WS):
        ids.setdefault('buttons', {})[b['name']] = b['btnId']
    json.dump(ids, open(hap.IDS_PATH, 'w'), ensure_ascii=False, indent=1)
    for b in hap.listing('worksheet', 'custom-actions', WS):
        print(f"{b['name']:<10} btnId={b['btnId']} clickType={b.get('clickType')} workflowType={b.get('workflowType')} "
              f"isBatch={b.get('isBatch')} filters={len(b.get('filters') or [])} confirm={b.get('confirmMsg', '')!r}")


COPY_DETAILS = 'Contacts: copy company details to its contact'
PUSH_DETAILS = 'Contacts: push company address and Tax ID to its contacts'
IDENTIFIERS = ['Tax ID', 'Company ID', 'DUNS']
# Odoo commercial fields added by the Payment Terms bundle (10-payment-terms.md): copied from a company that has them,
# and pushed to all of a company's contacts, as Tax ID is. Built only once payterms.py has added the two controls.
TERMS = ['Customer Payment Terms', 'Vendor Payment Terms']
TERM_BRANCHES = {'Customer Payment Terms': ('customer_terms', 'The company has Customer Payment Terms?',
                                            'Copy the Customer Payment Terms'),
                 'Vendor Payment Terms': ('vendor_terms', 'The company has Vendor Payment Terms?',
                                          'Copy the Vendor Payment Terms')}
PUSH_TERMS_STEP = 'Copy the Payment Terms to them'
# The two nodes that name all six address fields, and the branch in front of the first of them. Both were
# written once by `batch-add`, which never rewrites a step it already made — so when one of the six changes
# control, as Country did in bundle 4, `address_nodes` below re-points them in place.
COPY_ADDRESS_STEP = 'Copy the company address'
COPY_ADDRESS_BRANCH = 'Contact-type, and the company has an address?'
PUSH_ADDRESS_STEP = 'Copy the address to them'
GET_COMPANY = 'Get the company'
GET_CONTACT_TYPE = 'Get its Contact-type contacts'


def step_automations():
    """Odoo res.partner._fields_sync, company -> contacts. Upstream sync (contact -> company) is left out.

    Creates the two workflows, or brings existing ones up to date: steps missing by name are appended
    after the last step, and the trigger's fields and condition are rewritten when they differ.
    """
    from hap_cli.core.workflow_node_dsl import translate_condition_group

    ids = hap.ids()
    f = hap.by_name(c for c in hap.controls(WS) if c['type'] != 52)
    fid = lambda n: f[n]['controlId']
    terms = [n for n in TERMS if n in f]              # the Payment Terms bundle's, when it has been built
    option = lambda field, label: next({'key': o['key'], 'value': o['value'], 'isDeleted': False}
                                       for o in f[field]['options'] if o['value'] == label)

    def when(node, name, op, label=None):
        left = {'node': node, 'fieldId': fid(name), '_filedTypeId': f[name]['type']}
        if f[name]['type'] == 29:
            left['_enumDefault'] = f[name].get('enumDefault')
        item = {'left': left, 'op': op}
        if label:
            item['right'] = {'kind': 'literal', 'value': option(name, label)}
        return item

    def update(alias, name, target, names, source):
        return {'nodeAlias': alias, 'nodeType': 'update_record', 'name': name,
                'config': {'target': {'node': target}, 'fields': [
                    {'fieldId': fid(n), 'valueRef': {'kind': 'field', 'node': source, 'fieldId': fid(n),
                                                     'nodeAppId': WS}} for n in names]}}

    def branch(alias, name, condition, then):
        return {'nodeAlias': alias, 'nodeType': 'branch', 'name': name, 'config': {'paths': [
            {'alias': alias + '_yes', 'name': 'Yes', 'condition': condition, 'nodes': [then]},
            {'alias': alias + '_no', 'name': 'No'}]}}

    def copy_steps(r):
        """Odoo copies each commercial field only when the company has it (_get_commercial_values)."""
        trigger, company = r['trigger'], r['company']
        only_if_set = lambda alias, field: branch(
            alias, f'The company has a {field}?', {'logic': 'and', 'items': [when(company, field, 'not_empty')]},
            update('copy_' + alias, f'Copy the {field}', trigger, [field], company))
        return [
            {'nodeAlias': 'company', 'nodeType': 'get_relation', 'name': 'Get the company',
             'config': {'target': {'node': trigger}, 'fields': [{'fieldId': fid('Company')}], 'worksheet': WS}},
            branch('address', 'Contact-type, and the company has an address?',
                   {'groups': [{'items': [when(trigger, 'Address Type', 'eq', 'Contact'),
                                          when(company, n, 'not_empty')]} for n in ADDRESS]},
                   update('copy_address', 'Copy the company address', trigger, ADDRESS, company)),
            only_if_set('vat', 'Tax ID'),
            branch('salesperson', 'A contact without a salesperson?',
                   {'logic': 'and', 'items': [when(trigger, 'Salesperson', 'empty'),
                                              when(company, 'Salesperson', 'not_empty')]},
                   update('copy_salesperson', 'Copy the salesperson', trigger, ['Salesperson'], company)),
            only_if_set('registry', 'Company ID'),
            only_if_set('duns', 'DUNS'),
            *[branch(TERM_BRANCHES[n][0], TERM_BRANCHES[n][1],
                     {'logic': 'and', 'items': [when(company, n, 'not_empty')]},
                     update('copy_' + TERM_BRANCHES[n][0], TERM_BRANCHES[n][2], trigger, [n], company))
              for n in terms],
        ]

    def push_steps(r):
        trigger = r['trigger']
        return [
            {'nodeAlias': 'all_contacts', 'nodeType': 'get_relation_records', 'name': 'Get its contacts',
             'config': {'target': {'node': trigger}, 'fields': [{'fieldId': fid('Contacts')}], 'worksheet': WS}},
            update('push_ids', 'Copy Tax ID, Company ID and DUNS to them', {'nodeAlias': 'all_contacts'},
                   IDENTIFIERS, trigger),
            # Odoo _commercial_sync_to_descendants writes every commercial field, an empty one included
            *([update('push_terms', PUSH_TERMS_STEP, r.get('all_contacts', {'nodeAlias': 'all_contacts'}), terms,
                      trigger)] if terms else []),
            {'nodeAlias': 'contact_type', 'nodeType': 'get_relation_records', 'name': 'Get its Contact-type contacts',
             'config': {'target': {'node': trigger}, 'fields': [{'fieldId': fid('Contacts')}], 'worksheet': WS}},
            update('push_address', 'Copy the address to them', {'nodeAlias': 'contact_type'}, ADDRESS, trigger),
        ]

    workflows = [
        dict(name=COPY_DETAILS,
             desc='Odoo onchange_parent_id / _fields_sync: when a contact is linked to a company, copy the '
                  'company address (Contact-type only, and only if the company has one), each of its Tax ID, '
                  'Company ID and DUNS that is set, and its salesperson for a contact who has none.',
             trigger_name="When a contact's Company or Address Type is set",
             event='create_or_update', fields=[fid('Company'), fid('Address Type')],
             filter=lambda t: {'logic': 'and', 'items': [when(t, 'Company', 'not_empty')]},
             steps=copy_steps, anchors={'company': 'Get the company'}),
        dict(name=PUSH_DETAILS,
             desc="Odoo _children_sync: a company's address goes to its Contact-type contacts; its Tax ID, "
                  'Company ID and DUNS go to all of its contacts.',
             trigger_name="When a company's address or identifiers change",
             event='update', fields=[fid(n) for n in ADDRESS + IDENTIFIERS + terms],
             # only records that have contacts under them, so ordinary contact edits start no run
             filter=lambda t: {'logic': 'and', 'items': [when(t, 'Contacts', 'not_empty')]},
             steps=push_steps, anchors={'all_contacts': 'Get its contacts'},
             only_contact_type='Get its Contact-type contacts'),
    ]

    for wf in workflows:
        pid = ids.setdefault('workflows', {}).get(wf['name'])
        if not pid:
            out = hap.run('workflow', 'create', '-c', ids['org'], '-n', wf['name'], '-a', ids['app'],
                          '--type', 'worksheet', '-d', wf['desc'])
            data = out.get('data', out) if isinstance(out, dict) else out
            pid = data if isinstance(data, str) else (data.get('id') or data.get('processId'))
            ids['workflows'][wf['name']] = pid
            json.dump(ids, open(hap.IDS_PATH, 'w'), ensure_ascii=False, indent=1)
            refs = {'trigger': {'nodeAlias': 'trigger'}, **{a: {'nodeAlias': a} for a in wf['anchors']}}
            hap.run('workflow', 'node', 'batch-add', pid,
                    '--nodes', json.dumps(wf['steps'](refs), ensure_ascii=False),
                    '--trigger-worksheet', WS, '--trigger-event', wf['event'],
                    '--trigger-fields', ','.join(wf['fields']), '--trigger-alias', 'trigger',
                    '--trigger-filter', json.dumps(wf['filter'](refs['trigger']), ensure_ascii=False))
            proc = hap.run('workflow', 'node', 'list', pid)
            if wf.get('only_contact_type'):
                # --nodes sends a search filter as operateCondition; the UI stores it as `filters` on the node
                node = next(n for n in proc['flowNodeMap'].values() if n['name'] == wf['only_contact_type'])
                o = option('Address Type', 'Contact')
                config = {'actionId': '401', 'appId': WS, 'selectNodeId': proc['startEventId'],
                          'fields': [{'fieldId': fid('Contacts')}],
                          'filters': [{'spliceType': 2, 'conditions': [[{
                              'nodeId': node['id'], 'nodeType': 13, 'actionId': '401', 'filedId': fid('Address Type'),
                              'filedValue': 'Address Type', 'filedTypeId': 11, 'enumDefault': 0, 'conditionId': '9',
                              'sourceType': 0, 'conditionValues': [{'value': {**o, 'score': None, 'index': None}}]}]]}]}
                hap.run('workflow', 'node', 'save', pid, node['id'], '--type', '13', '-c', json.dumps(config),
                        '-n', node['name'])
        else:
            proc = hap.run('workflow', 'node', 'list', pid)
            nodes = proc['flowNodeMap']
            start = proc['startEventId']
            by_name = {n['name']: n['id'] for n in nodes.values()}
            refs = {'trigger': {'nodeId': start}, **{a: {'nodeId': by_name[n]} for a, n in wf['anchors'].items()}}
            missing = [s for s in wf['steps'](refs) if s['name'] not in by_name]
            if missing:
                last = start
                while nodes[last].get('nextId') not in (None, '', '99'):
                    last = nodes[last]['nextId']
                hap.run('workflow', 'node', 'batch-add', pid, '--nodes', json.dumps(missing, ensure_ascii=False),
                        '--trigger-node-id', last, '--trigger-alias', 'last_step')
                print(f"{wf['name']}: appended {[s['name'] for s in missing]}")
            trig = hap.run('workflow', 'node', 'get', pid, start)
            trig = trig.get('data', trig)
            want = translate_condition_group(wf['filter'](refs['trigger']), {})
            shape = lambda groups: [[(c.get('filedId'), str(c.get('conditionId'))) for c in g] for g in groups or []]
            if (set(trig.get('assignFieldIds') or []) != set(wf['fields'])
                    or shape(trig.get('operateCondition')) != shape(want)):
                hap.run('workflow', 'node', 'save', pid, start, '--type', '0', '-n', wf['trigger_name'],
                        '-c', json.dumps({'appId': WS, 'appType': 1, 'triggerId': trig.get('triggerId'),
                                          'assignFieldIds': wf['fields'], 'operateCondition': want,
                                          'returns': []}, ensure_ascii=False))
                print(f"{wf['name']}: trigger fields/condition rewritten")
            proc = hap.run('workflow', 'node', 'list', pid)
        address_nodes(pid, wf['name'], f, option)
        if terms:
            term_nodes(pid, wf['name'], terms, fid)
        proc = hap.run('workflow', 'node', 'list', pid)
        # batch-add names the trigger in Chinese and drops branch path names
        hap.run('workflow', 'node', 'rename', pid, proc['startEventId'], '-n', wf['trigger_name'])
        for n in proc['flowNodeMap'].values():
            if n.get('typeId') == 2 and n.get('name') not in ('Yes', 'No'):
                hap.run('workflow', 'node', 'rename', pid, n['id'], '-n',
                        'Yes' if n.get('nextId') not in ('', None, '99') else 'No')
        print(wf['name'], publish(pid))
    for name in (COPY_DETAILS, PUSH_DETAILS):
        print(subprocess.run(['hap', 'workflow', 'structure', ids['workflows'][name]],
                             capture_output=True, text=True).stdout)


def node_fields(pid, workflow, node_id, name, select, source, f, names):
    """Bring an update step's `fields` up to the controls `names` now are, taken from node `source`.

    `batch-add` writes a step once and never again, so a step built from a control that has since been replaced
    keeps the dead id: it stays published, `isException` stays false, and the only sign is the server's
    `fieldValueName` reading "" (BUILDING.md). Sent back with `node save --type 6`, the whole list at once."""
    get = lambda: (lambda d: d.get('data', d))(hap.run('workflow', 'node', 'get', pid, node_id))
    want = [{'fieldId': f[n]['controlId'], 'type': f[n]['type'], 'addType': 0, 'fieldValue': '',
             'fieldValueId': f[n]['controlId'], 'nodeId': source, 'sureNodeId': source, 'nodeAppType': 1}
            for n in names]

    def source_of(x):
        """Which node an entry takes its value from. Sent as `nodeId` + `fieldValueId`, a **text** field comes
        back as the template `$<nodeId>-<fieldId>$` with `nodeId` emptied — the same binding written the other
        way (BUILDING.md), so it is read out of the template rather than compared as a difference for ever."""
        value = x.get('fieldValue') or ''
        if not x.get('nodeId') and value.startswith('$') and value.endswith('$') and '-' in value:
            return value[1:-1].split('-')[0]
        return x.get('nodeId')

    shape = lambda xs: [(x.get('fieldId'), source_of(x), x.get('fieldValueId')) for x in xs]
    d = get()
    if d.get('selectNodeId') != select or d.get('isException') or shape(d.get('fields') or []) != shape(want):
        hap.run('workflow', 'node', 'save', pid, node_id, '--type', '6', '-n', name, '-c', json.dumps(
            {'actionId': '2', 'appId': WS, 'appType': 1, 'selectNodeId': select, 'fields': want}))
        d = get()
        print(f'  {workflow}: {name!r} fields rewritten ({names})')
    if d.get('selectNodeId') != select or d.get('isException') or shape(d.get('fields') or []) != shape(want):
        sys.exit(f"{workflow}: {name!r} read back {d.get('selectNodeId')} {d.get('isException')} "
                 f"{shape(d.get('fields') or [])}")


def address_nodes(pid, workflow, f, option):
    """Re-point the nodes that name the six address fields, when one of them has changed control.

    Bundle 4 replaced Contacts' Country **text** with a relation to Countries, and `ADDRESS` is looked up by
    name — so this brings the two copy steps and the branch in front of the first of them to whatever the six
    names resolve to now. It writes nothing when they already agree."""
    proc = hap.run('workflow', 'node', 'list', pid)
    nodes, start = proc['flowNodeMap'], proc['startEventId']
    by_name = {n['name']: n for n in nodes.values()}
    get = lambda node_id: (lambda d: d.get('data', d))(hap.run('workflow', 'node', 'get', pid, node_id))
    if workflow == COPY_DETAILS:
        company = by_name[GET_COMPANY]['id']
        gateway = by_name[COPY_ADDRESS_BRANCH]
        yes = next(nodes[i] for i in gateway.get('flowIds') or []
                   if nodes[i].get('nextId') not in ('', None, '99'))
        kind = option('Address Type', 'Contact')
        # one AND-group per address field: the contact is Contact-type **and** the company has that field
        condition = [[{'nodeId': start, 'filedId': f['Address Type']['controlId'], 'filedValue': 'Address Type',
                       'filedTypeId': f['Address Type']['type'], 'enumDefault': 0, 'conditionId': '9',
                       'sourceType': 0,
                       'conditionValues': [{'value': {**kind, 'score': None, 'index': None}}]},
                      {'nodeId': company, 'filedId': f[n]['controlId'], 'filedValue': n,
                       'filedTypeId': f[n]['type'], 'enumDefault': f[n].get('enumDefault'), 'conditionId': '7',
                       'sourceType': 0, 'conditionValues': []}] for n in ADDRESS]
        shape = lambda groups: [[(c.get('nodeId'), c.get('filedId'), str(c.get('conditionId'))) for c in g]
                                for g in groups or []]
        if shape(get(yes['id']).get('conditions')) != shape(condition):
            hap.run('workflow', 'node', 'save', pid, yes['id'], '--type', '2', '-n', 'Yes',
                    '-c', json.dumps({'operateCondition': condition}, ensure_ascii=False))
            print(f'  {workflow}: {COPY_ADDRESS_BRANCH!r} condition rewritten')
            if shape(get(yes['id']).get('conditions')) != shape(condition):
                sys.exit(f"{workflow}: {COPY_ADDRESS_BRANCH!r} read back "
                         f"{shape(get(yes['id']).get('conditions'))}")
        node_fields(pid, workflow, by_name[COPY_ADDRESS_STEP]['id'], COPY_ADDRESS_STEP, start, company, f,
                    ADDRESS)
    else:
        node_fields(pid, workflow, by_name[PUSH_ADDRESS_STEP]['id'], PUSH_ADDRESS_STEP,
                    by_name[GET_CONTACT_TYPE]['id'], start, f, ADDRESS)


def term_nodes(pid, workflow, terms, fid):
    """The Payment Terms bundle's nodes, written again in the shape the server keeps and read back. A second
    `batch-add` drops a branch path's condition, and a Relation copied from another node is `nodeId` + `fieldValueId`
    (BUILDING.md); an update step must select a node that produces a record."""
    proc = hap.run('workflow', 'node', 'list', pid)
    nodes, start = proc['flowNodeMap'], proc['startEventId']
    by_name = {n['name']: n for n in nodes.values()}
    get = lambda node_id: (lambda d: d.get('data', d))(hap.run('workflow', 'node', 'get', pid, node_id))

    def ensure_step(name, select, source, fields):
        node = by_name[name]
        want = [{'fieldId': fid(n), 'type': 29, 'addType': 0, 'fieldValue': '', 'fieldValueId': fid(n),
                 'nodeId': source, 'sureNodeId': source, 'nodeAppType': 1} for n in fields]
        shape = lambda xs: [(x.get('fieldId'), x.get('nodeId'), x.get('fieldValueId')) for x in xs]
        d = get(node['id'])
        if d.get('selectNodeId') != select or d.get('isException') or shape(d.get('fields') or []) != shape(want):
            hap.run('workflow', 'node', 'save', pid, node['id'], '--type', '6', '-n', name, '-c', json.dumps(
                {'actionId': '2', 'appId': WS, 'appType': 1, 'selectNodeId': select, 'fields': want}))
            d = get(node['id'])
            print(f"  {workflow}: {name!r} rewritten")
        if d.get('selectNodeId') != select or d.get('isException') or shape(d.get('fields') or []) != shape(want):
            sys.exit(f"{workflow}: {name!r} read back {d.get('selectNodeId')} {d.get('isException')} {d.get('fields')}")

    if workflow == COPY_DETAILS:
        company = by_name['Get the company']['id']
        for n in terms:
            _, gateway_name, step = TERM_BRANCHES[n]
            gateway = by_name[gateway_name]
            paths = [nodes[i] for i in gateway.get('flowIds') or []]
            yes = next(x for x in paths if x.get('nextId') not in ('', None, '99'))
            condition = [[{'nodeId': company, 'filedId': fid(n), 'filedValue': n, 'filedTypeId': 29, 'enumDefault': 1,
                           'conditionId': '7', 'sourceType': 0, 'conditionValues': []}]]
            live = [[(c.get('nodeId'), c.get('filedId'), str(c.get('conditionId'))) for c in g]
                    for g in get(yes['id']).get('conditions') or []]
            if live != [[(company, fid(n), '7')]]:
                hap.run('workflow', 'node', 'save', pid, yes['id'], '--type', '2', '-n', 'Yes',
                        '-c', json.dumps({'operateCondition': condition}, ensure_ascii=False))
                print(f"  {workflow}: {gateway_name!r} condition written")
            ensure_step(step, start, company, [n])
    else:
        ensure_step(PUSH_TERMS_STEP, by_name['Get its contacts']['id'], start, terms)


def publish(pid):
    res = hap.run('workflow', 'publish', pid)
    return {k: res.get(k) for k in ('isPublish', 'processWarnings', 'errorNodeIds')}


def step_to194():
    """One-off: move the build of 15 Sep 2026 (Odoo 19.0 source) to Odoo saas~19.4, keeping every id."""
    ctrls = hap.controls(WS)
    hap.backup('contacts_controls_pre_to194', ctrls)
    ctrls = [c for c in ctrls if c['controlName'] != 'Company Type']          # 19.4 has no Person/Company switch
    if not any(c['controlName'] == 'DUNS' for c in ctrls):
        ctrls.append(ctl('TEXT', 'DUNS', alias='duns'))
    arrange(ctrls)
    C.save_controls(WS, ctrls)
    show()
    step_rules()
    step_views()

    ids = hap.ids()
    f = hap.by_name(c for c in hap.controls(WS) if c['type'] != 52)
    live = {c['controlId'] for c in f.values()}

    # copy-details: drop the "Company Type = Person" condition from the salesperson branch
    pid = ids['workflows'][COPY_DETAILS]
    proc = hap.run('workflow', 'node', 'list', pid)
    for n in proc['flowNodeMap'].values():
        if n.get('typeId') == 1 and n['name'] == 'A person without a salesperson?':
            hap.run('workflow', 'node', 'rename', pid, n['id'], '-n', 'A contact without a salesperson?')
        if n.get('typeId') == 2:
            node = hap.run('workflow', 'node', 'get', pid, n['id'])
            node = node.get('data', node)
            groups = node.get('conditions') or node.get('operateCondition') or []   # get says conditions, save says operateCondition
            kept = [[c for c in g if c.get('filedId') in live or c.get('filedId') == ''] for g in groups]
            if kept != groups:
                hap.run('workflow', 'node', 'save', pid, n['id'], '--type', '2', '-n', n['name'],
                        '-c', json.dumps({'operateCondition': kept}))
    print(COPY_DETAILS, publish(pid))

    # push-details: DUNS joins the trigger fields and the identifiers copied to every contact
    pid = ids['workflows'][PUSH_DETAILS]
    proc = hap.run('workflow', 'node', 'list', pid)
    trig = hap.run('workflow', 'node', 'get', pid, proc['startEventId'])
    trig = trig.get('data', trig)
    assign = trig.get('assignFieldIds') or []
    if f['DUNS']['controlId'] not in assign:
        hap.run('workflow', 'node', 'save', pid, proc['startEventId'], '--type', '0',
                '-n', "When a company's address or identifiers change", '-c', json.dumps({
                    'appId': WS, 'appType': 1, 'triggerId': trig.get('triggerId', '4'),
                    'assignFieldIds': assign + [f['DUNS']['controlId']], 'operateCondition': [], 'returns': []}))
    push = next(n for n in proc['flowNodeMap'].values() if n['name'].startswith('Copy Tax ID'))
    node = hap.run('workflow', 'node', 'get', pid, push['id'])
    node = node.get('data', node)
    fields = node.get('fields') or []
    if not any(x.get('fieldId') == f['DUNS']['controlId'] for x in fields):
        model = next(x for x in fields if x.get('fieldId') == f['Company ID']['controlId'])
        fields.append({**model, 'fieldId': f['DUNS']['controlId'], 'fieldValueId': f['DUNS']['controlId'],
                       'fieldName': 'DUNS'})
        hap.run('workflow', 'node', 'save', pid, push['id'], '--type', '6',
                '-n', 'Copy Tax ID, Company ID and DUNS to them', '-c', json.dumps({
                    'actionId': node.get('actionId', '2'), 'appId': WS, 'selectNodeId': node.get('selectNodeId'),
                    'fields': fields}, ensure_ascii=False))
    print(PUSH_DETAILS, publish(pid))
    for name in (COPY_DETAILS, PUSH_DETAILS):
        print(subprocess.run(['hap', 'workflow', 'structure', ids['workflows'][name]],
                             capture_output=True, text=True).stdout)


def show():
    ctrls = hap.controls(WS)
    tabs = {c['controlId']: c['controlName'] for c in ctrls if c['type'] == 52}
    for c in sorted(ctrls, key=lambda c: (c.get('row', 0), c.get('col', 0))):
        extra = []
        if c.get('attribute') == 1: extra.append('title')
        if c.get('required'): extra.append('required')
        if c.get('fieldPermission') not in (None, '', '111'): extra.append(f"perm={c['fieldPermission']}")
        if c.get('sectionId'): extra.append(f"tab={tabs.get(c['sectionId'], c['sectionId'])}")
        if c.get('dataSource'): extra.append(f"-> {c['dataSource']} pair={c.get('sourceControlId')}")
        if c.get('options'): extra.append('opts=' + '/'.join(o['value'] for o in c['options']))
        if c.get('hint'): extra.append(f"hint={c['hint']!r}")
        print(f"r{c.get('row', 0):<2} c{c.get('col', 0)} s{c.get('size', '?'):<2} {c['type']:>2} "
              f"{c['controlName']:<18} {c['controlId']}  {c.get('alias') or '':<17} {' '.join(extra)}")
    print(f'{len(ctrls)} controls')


if __name__ == '__main__':
    {'fields': step_fields, 'display': step_display, 'layout': step_layout, 'rules': step_rules,
     'views': step_views, 'buttons': step_buttons, 'automations': step_automations, 'to194': step_to194,
     'names': step_names, 'show': show}[sys.argv[1] if len(sys.argv) > 1 else 'show']()
