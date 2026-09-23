"""Orders › start a quotation from a template.

The owner's design (23 Sep 2026): a toggle **Create from Template** on a new quotation; ticking it shows **Quotation
Template**, a Relation back to Orders that offers only templates (Is Template ticked); choosing one fills in the rest.

Odoo's own mechanism is `sale_management`: `sale.order.sale_order_template_id`, whose onchange
(addons/sale_management/models/sale_order.py:84-120) replaces the order lines with the template's, and whose computes
(:35-75) copy note, require_signature, require_payment, prepayment_percent, validity_date and journal_id. Here a
template is an order with Is Template ticked (16-orders.md §1.1 of 17), so the Relation points at Orders itself.

What fills, and how — all in the open form, before the save:

| Target | Mechanism |
|---|---|
| Order Lines | the subtable's default is a **query worksheet**: Order Lines whose Orders is the chosen template, sorted by Sequence, each row copied column by column (QUERY_COLUMNS) |
| Terms and conditions · Journal · Online Signature · Online Payment · Prepayment Percentage | a dynamic default read through the Quotation Template relation (`defsource` rcid) — the shape Payment Terms uses through Customer |

Not copied, on purpose: Customer and the addresses (a template has no customer in Odoo), Payment Terms (follows the
customer, and one `defsource` cannot hold both), Expiration (Odoo adds the template's number of days to today; the
default today + N stays), Tax Mode (required with a static default; see 16-orders.md).

Steps (each reads live state first; a re-run saves nothing):

    controls  append Create from Template and Quotation Template
    place     put them on a new row right after Number
    views     make sure the All view does not hide them (it would hide them in its forms too)
    rules     the toggle only on a new quotation; the relation only when it is ticked, read-only once saved
    fills     the relation-read defaults (FILLS)
    mode      the Create Quotation | Create Template switch at the top of a new record
    flag      the workflow that ticks Is Template on a record created as a template
    taxmode   Tax Mode from the template, Tax Excluded when there is none
    query     the Order Lines query and the subtable's pointer at it
    check     everything above, read back
"""
import json, sys

import common as C
import hap

APP = hap.ids()['app']
ORDERS = '6ab09897e43d174ab3752d7b'
OLINES = '6ab0c740e43d174ab37535b2'

TOGGLE = 'Create from Template'
TEMPLATE = 'Quotation Template'
DESC = {
    TOGGLE: 'Tick to start this quotation from a saved template.',
    TEMPLATE: 'The template this quotation starts from. Choosing one fills in its order lines, terms and conditions, '
              'journal, and online signature and payment settings.',
}
HINT = {TEMPLATE: 'Choose a template'}
ALIAS = {TOGGLE: '', TEMPLATE: 'sale_order_template_id'}
# A new row right after Number; every row from 2 down moves one row lower.
PLACE_AFTER_ROW = 1
PLACE = {TOGGLE: (2, 0, 6), TEMPLATE: (2, 1, 6)}

# Orders controls filled through the relation: target name -> the same control on the template.
FILLS = ['Terms and conditions', 'Journal', 'Online Signature', 'Online Payment', 'Prepayment Percentage', 'Tags',
         'Incoterm', 'Incoterm Location']

# Order Lines columns a template line hands to the new line. Quantities delivered and invoiced, the invoice links and
# every computed column start fresh.
QUERY_COLUMNS = ['Sequence', 'Display Type', 'Product', 'Description', 'Quantity', 'Unit', 'Unit Price', 'Discount',
                 'Taxes', 'Lead Time', 'Optional Line']
QUERY_ROWS = 200

RULES = [
    ('Create from Template only on a new quotation', 'HIDE', 'Number not empty'),
    ('Quotation Template when starting from a template', 'SHOW', 'toggle ticked, or a template chosen'),
    ('Quotation Template fixed once saved', 'READONLY', 'Number not empty'),
]


def guard():
    app = hap.run('app', 'info', '-a', APP).get('data', {})
    names = {i['id'] for s in app.get('sections', []) for i in s['items']}
    if app.get('name') not in hap.APP_NAMES or ORDERS not in names or OLINES not in names:
        sys.exit(f'the profile does not reach {hap.APP_NAMES[0]} › Sales › Orders and Order Lines')
    return C.fields(ORDERS), C.fields(OLINES)


def is_template(of):
    return of['Is Template']['controlId']


# ── controls ────────────────────────────────────────────────────────────────

def wanted_controls(of):
    return {
        TOGGLE: C.control('SWITCH', TOGGLE, PLACE[TOGGLE], alias=ALIAS[TOGGLE], hint='', desc=DESC[TOGGLE],
                          advanced_setting={'defsource': C.static_default(0)}),
        TEMPLATE: C.control('RELATE_SHEET', TEMPLATE, PLACE[TEMPLATE], alias=ALIAS[TEMPLATE], hint=HINT[TEMPLATE],
                            desc=DESC[TEMPLATE], data_source=ORDERS, multi=False,
                            advanced_setting={'bidirectional': '0', 'showtype': '3',
                                              'filters': C.active_picker(is_template(of))}),
    }


def step_controls():
    of, _ = guard()
    want = wanted_controls(of)
    missing = [c for n, c in want.items() if n not in of]
    if not missing:
        print(f'  {TOGGLE} and {TEMPLATE} are on Orders: {of[TOGGLE]["controlId"]}, {of[TEMPLATE]["controlId"]}')
    else:
        live = C.append_checked(ORDERS, missing, 'templates_orders_pre_controls', 'controls')
        for n in want:
            if n not in live:
                sys.exit(f'{n} did not store')
        of = live
    for n in want:
        C.remember('controls', f'Orders: {n}', of[n]['controlId'])
    # What the append does not carry reliably: the picker filter, the one-way flag, the alias, the text.
    t = of[TEMPLATE]
    # The template is shown by its Template Name, not its S-number; the toggle is a switch like Is Template.
    name_id = of['Template Name']['controlId']
    spec = {t['controlId']: {'alias': ALIAS[TEMPLATE], 'desc': DESC[TEMPLATE], 'hint': HINT[TEMPLATE],
                             'advancedSetting.filters': C.active_picker(is_template(of)),
                             'advancedSetting.showtitleid': name_id,
                             'advancedSetting.chooseshowids': json.dumps([name_id], separators=(',', ':'))},
            of[TOGGLE]['controlId']: {'desc': DESC[TOGGLE], 'advancedSetting.showtype': '1'}}
    spec = {cid: {k: v for k, v in s.items() if not stored(of, cid, k, v)} for cid, s in spec.items()}
    spec = {cid: s for cid, s in spec.items() if s}
    if not spec:
        print('  their alias, text and picker filter are as specified; nothing saved')
        return
    C.pinned_write(ORDERS, spec, 'templates_orders_pre_attrs', 'controls/attrs')


def stored(of, cid, key, value):
    c = next(c for c in of.values() if c['controlId'] == cid)
    if key.startswith('advancedSetting.'):
        got = (c.get('advancedSetting') or {}).get(key.split('.', 1)[1])
        if key.endswith('.filters'):
            return C.picker_state(got) == C.picker_state(value)
        return got == value
    return c.get(key) == value


def step_place():
    of, _ = guard()
    ctrls, version = C.controls_with_version(ORDERS)
    by = {c['controlName']: c for c in ctrls if c['controlName'] in PLACE}
    if len(by) != 2:
        sys.exit('run `controls` first')
    if all((by[n].get('row'), by[n].get('col')) == PLACE[n][:2] for n in PLACE):
        print(f'  {TOGGLE} and {TEMPLATE} already sit on row {PLACE[TOGGLE][0]}; nothing saved')
        return
    ours = {by[n]['controlId'] for n in PLACE}
    spec = {}
    for c in ctrls:
        if c['controlId'] in ours:
            row, col, size = PLACE[c['controlName']]
            spec[c['controlId']] = {'row': row, 'col': col, 'size': size}
        elif PLACE_AFTER_ROW < (c.get('row') or 0) < 9999:
            spec[c['controlId']] = {'row': c['row'] + 1}
    print(f'  {len(spec) - 2} controls move one row down to make room after Number')
    C.pinned_write(ORDERS, spec, 'templates_orders_pre_place', 'place')


# ── views ───────────────────────────────────────────────────────────────────
#
# All shows every field as a column, these two included. Hiding them there is not an option: a view's hidden fields
# are hidden in the record form opened from that view too, + Record included — tried on 23 Sep 2026, and the toggle
# vanished from All's create form. `views` only undoes that trial.

ALL_VIEW = '6ab09897e43d174ab3752d7f'


def step_views():
    of, _ = guard()
    ours = [of[n]['controlId'] for n in (TOGGLE, TEMPLATE)]
    info = C.view_info(ORDERS, APP, ALL_VIEW)
    hidden = list(info.get('controls') or [])
    if not any(c in hidden for c in ours):
        print(f'  All does not hide {TOGGLE} or {TEMPLATE}; nothing saved')
        return
    hap.backup('templates_orders_all_view', info)
    want = [c for c in hidden if c not in ours]
    hap.run('worksheet', 'view', 'update', ORDERS, ALL_VIEW, '-a', APP,
            '--view-json', json.dumps({'controls': want}), '--edit-attrs', 'controls')
    back = C.view_info(ORDERS, APP, ALL_VIEW)
    if sorted(back.get('controls') or []) != sorted(want):
        sys.exit(f'All did not store: {back.get("controls")}')
    print(f'  All: {TOGGLE} and {TEMPLATE} shown again (hidden fields now {want})')


# ── rules ───────────────────────────────────────────────────────────────────

def step_rules():
    of, _ = guard()
    number, toggle, template = of['Number'], of[TOGGLE], of[TEMPLATE]
    rules = [
        (RULES[0][0], C.INTERACTION, [C.cond(number, C.NOT_EMPTY)], [C.item(C.HIDE, toggle)], {}),
        # Either condition: a rule does not read the toggle once another rule has hidden it (a saved order).
        (RULES[1][0], C.INTERACTION, C.any_of([C.cond(toggle, C.EQ, 1)], [C.cond(template, C.NOT_EMPTY)]),
         [C.item(C.SHOW, template)], {}),
        (RULES[2][0], C.INTERACTION, [C.cond(number, C.NOT_EMPTY)], [C.item(C.READONLY, template)], {}),
    ]
    if MODE in of:
        mine = {r[0] for r in mode_rules(of)}
        rules = [r for r in rules if r[0] not in mine] + mode_rules(of)
    C.upsert_rules(ORDERS, rules, 'templates_orders_rules')


# ── the relation-read defaults ──────────────────────────────────────────────

def fill_source(of, name):
    return json.dumps([{'rcid': of[TEMPLATE]['controlId'], 'cid': of[name]['controlId'], 'staticValue': '',
                        'isAsync': False, 'type': 0}], separators=(',', ':'))


def fill_state(value):
    try:
        return [(e.get('rcid'), e.get('cid'), e.get('staticValue') or '') for e in json.loads(value or '[]')]
    except ValueError:
        return value


def step_fills():
    of, _ = guard()
    spec = {}
    for name in FILLS:
        c = of[name]
        a = c.get('advancedSetting') or {}
        want = fill_source(of, name)
        if fill_state(a.get('defsource')) != fill_state(want) or a.get('defaulttype') not in ('', None, '0'):
            spec[c['controlId']] = {'advancedSetting.defsource': want, 'advancedSetting.defaulttype': '0'}
            print(f'  {name}: default {a.get("defsource") or "none"} (type {a.get("defaulttype")!r}) -> '
                  f'the chosen template\'s {name}')
    if not spec:
        print(f'  {FILLS} already read from {TEMPLATE}; nothing saved')
        return
    C.pinned_write(ORDERS, spec, 'templates_orders_pre_fills', 'fills')


# ── Tax Mode ────────────────────────────────────────────────────────────────
#
# Tax Mode is required and defaults to Tax Excluded; one `defsource` cannot hold that static value and a read through
# the relation (a single select merges both into one list). So a hidden, live lookup reads the template's Tax Mode,
# and Tax Mode's function default reads the lookup — tried before `defsource`, whose static Tax Excluded stays.

TAX_LOOKUP = 'Template Tax Mode'
TAX_LOOKUP_PLACE = (9999, 0, 6)
# Inside a function a lookup of a single select is not its text (the probe on Customer Reference, 23 Sep 2026, came
# back empty once a template was chosen, and Tax Mode with it), while a select on the record itself is. So a hidden
# text formula holds each order's Tax Mode as text, and the lookup reads that.
TAX_TEXT = 'Tax Mode name'
TAX_TEXT_PLACE = (9999, 1, 6)


def tax_function(of):
    # A function default replaces the static one outright (an empty result is not a fall-through), so it carries
    # its own fallback.
    lk = of[TAX_LOOKUP]['controlId']
    return json.dumps({'type': 'mdfunction', 'expression': f'IF(ISBLANK(${lk}$),"Tax Excluded",${lk}$)', 'status': 1},
                      separators=(',', ':'))


def text_source(of):
    return json.dumps({'type': 'mdfunction', 'expression': f"CONCAT(${of['Tax Mode']['controlId']}$,\"\")",
                       'status': 1}, ensure_ascii=False)


def step_taxmode():
    of, _ = guard()
    if TAX_TEXT not in of:
        c = C.control('FORMULA_FUNC', TAX_TEXT, TAX_TEXT_PLACE, alias='', hint='', desc='',
                      advanced_setting={'analysislink': '1', 'sorttype': 'en'},
                      extra={'enumDefault2': 2, 'dot': 0, 'dataSource': text_source(of)})
        c['fieldPermission'] = '011'
        of = C.append_checked(ORDERS, [c], 'templates_orders_pre_taxtext', 'taxmode/text')
    t = of[TAX_TEXT]
    if json.loads(t.get('dataSource') or '{}').get('expression') != json.loads(text_source(of))['expression']:
        C.pinned_write(ORDERS, {t['controlId']: {'dataSource': text_source(of), 'enumDefault2': 2}},
                       'templates_orders_pre_taxtext_fx', 'taxmode/text formula')
        of, _ = guard()
    C.remember('controls', f'Orders: {TAX_TEXT}', of[TAX_TEXT]['controlId'])
    if TAX_LOOKUP not in of:
        c = C.control('SHEET_FIELD', TAX_LOOKUP, TAX_LOOKUP_PLACE, alias='', hint='', desc='',
                      data_source=of[TEMPLATE]['controlId'], source_control_id=of[TAX_TEXT]['controlId'],
                      extra={'dot': 0})
        c['fieldPermission'] = '011'
        c['dataSource'] = f"${of[TEMPLATE]['controlId']}$"
        of = C.append_checked(ORDERS, [c], 'templates_orders_pre_taxlookup', 'taxmode/lookup')
    lk = of[TAX_LOOKUP]
    if lk.get('sourceControlId') != of[TAX_TEXT]['controlId']:
        C.pinned_write(ORDERS, {lk['controlId']: {'sourceControlId': of[TAX_TEXT]['controlId']}},
                       'templates_orders_pre_taxlookup_src', 'taxmode/lookup reads the text')
        of, _ = guard()
        lk = of[TAX_LOOKUP]
    C.remember('controls', f'Orders: {TAX_LOOKUP}', lk['controlId'])
    print(f"  {TAX_LOOKUP}: {lk['controlId']} reads {TAX_TEXT} {lk.get('sourceControlId')}")
    a = of['Tax Mode'].get('advancedSetting') or {}
    want = tax_function(of)
    if a.get('defaulttype') == '1' and json.loads(a.get('defaultfunc') or '{}').get('expression') == \
            json.loads(want)['expression']:
        print('  Tax Mode already defaults from the template; nothing saved')
        return
    C.pinned_write(ORDERS, {of['Tax Mode']['controlId']: {'advancedSetting.defaulttype': '1',
                                                           'advancedSetting.defaultfunc': want}},
                   'templates_orders_pre_taxmode', 'taxmode')


# ── a new template is a template ────────────────────────────────────────────

FLAG_WORKFLOW = 'Orders: a record created as a template is ticked Is Template'


def step_flag():
    import o2i
    of, _ = guard()
    m = of[MODE]
    pid = o2i.ensure_workflow(FLAG_WORKFLOW, 'Ticks Is Template on a record created with Create Template.')
    proc, byname = o2i.nodes_by_name(pid)
    if 'Tick Is Template' not in byname:
        hap.run('workflow', 'node', 'batch-add', pid, '-a', APP, '--trigger-worksheet', ORDERS,
                '--trigger-event', 'create',
                '--trigger-filter', json.dumps({'logic': 'and', 'items': [
                    {'node': 'trigger', 'field': m['controlId'], 'op': 'eq',
                     'value': option_key(m, MODE_TEMPLATE)}]}),
                '--nodes', json.dumps([{'nodeAlias': 'tick', 'nodeType': 'update_record', 'name': 'Tick Is Template',
                                        'config': {'worksheetId': ORDERS, 'target': {'node': 'trigger'},
                                                   'fields': [{'fieldId': of['Is Template']['controlId'],
                                                               'value': {'kind': 'literal', 'value': '1'}}]}}]))
        proc, byname = o2i.nodes_by_name(pid)
        hap.run('workflow', 'node', 'rename', pid, proc['startEventId'], '-n', 'When an order is created as a template')
        print(f'  {FLAG_WORKFLOW}: nodes added')
    else:
        print(f'  {FLAG_WORKFLOW}: {sorted(byname)} already there')
    hap.run('workflow', 'publish', pid)
    print(f'  published {pid}')


# ── Create Quotation | Create Template ───────────────────────────────────────
#
# The owner's switch at the very top of a new record (23 Sep 2026). Create Template ticks Is Template and hides every
# field a template does not hand on; Create Quotation offers Create from Template. Shown only while creating.

MODE = 'Create'
MODE_QUOTATION, MODE_TEMPLATE = 'Create Quotation', 'Create Template'
MODE_PLACE = (0, 0, 12)
# Every field a template does not hand on to the quotations made from it.
NOT_COPIED = ['Status', 'Locked', 'Customer', 'Invoice Address', 'Delivery Address', 'Expiration',
              'Quotation/Order Date', 'Delivery Date', 'Payment Terms', 'Invoice Status', 'Delivery Status',
              'Invoicing Closed', 'Signature', 'Signed By', 'Signed On', 'Signing Link', 'Invoices', 'Invoice Count',
              'Salesperson', 'Sales Teams', 'Customer Reference', 'Tracking', 'Source Document', TOGGLE, TEMPLATE]
MODE_RULES = [
    'Create switch only on a new record',
    'Is Template follows the Create switch on a new record',
    'A template shows only what it hands on',
]
# Tried and retired on 23 Sep 2026 (disabled, not deleted): orders.py's own Template Name rule now reads the switch;
# a second SHOW rule could not win against its HIDE, since a hide from any rule wins.
RETIRED_RULES = ['Template Name on a new template']


def option_key(c, value):
    return next(o['key'] for o in c['options'] if o['value'] == value and not o.get('isDeleted'))


def step_mode():
    of, _ = guard()
    if MODE not in of:
        c = C.control('FLAT_MENU', MODE, MODE_PLACE, alias='', hint='', desc='', options=[MODE_QUOTATION, MODE_TEMPLATE],
                      advanced_setting={'showtype': '1', 'direction': '2'})
        of = C.append_checked(ORDERS, [c], 'templates_orders_pre_mode', 'mode/control')
    C.remember('controls', f'Orders: {MODE}', of[MODE]['controlId'])
    m = of[MODE]
    quotation = option_key(m, MODE_QUOTATION)
    template = option_key(m, MODE_TEMPLATE)
    # Two radio buttons side by side: a tiled single select is type 9 with direction 2 (as Products' Product Type);
    # a type 11 with showtype 1 reads "Tiled" in the designer and still renders as a dropdown.
    spec = {m['controlId']: {'type': 9, 'advancedSetting.showtype': '1', 'advancedSetting.direction': '2',
                             'advancedSetting.hidetitle': '1',
                             'advancedSetting.defsource': json.dumps([{'cid': '', 'rcid': '', 'staticValue': quotation}],
                                                                     separators=(',', ':'))},
            # A function default on the (hidden) Is Template stored 0 on a Create Template record (S00049), so
            # `flag`'s workflow ticks it after the save instead, and none is kept here.
            of['Is Template']['controlId']: {'advancedSetting.defaulttype': '', 'advancedSetting.defaultfunc': ''}}
    spec = {cid: {k: v for k, v in sp.items() if not stored(of, cid, k, v)} for cid, sp in spec.items()}
    spec = {cid: sp for cid, sp in spec.items() if sp}
    if spec:
        C.pinned_write(ORDERS, spec, 'templates_orders_pre_mode_attrs', 'mode/attrs')
    else:
        print(f'  {MODE}: default, style and the Is Template link as specified; nothing saved')
    # the very top: row 0, everything else one row down
    ctrls, _v = C.controls_with_version(ORDERS)
    me = next(c for c in ctrls if c['controlId'] == m['controlId'])
    if (me.get('row'), me.get('col')) == MODE_PLACE[:2] and \
            not any(c.get('row') == 0 and c['controlId'] != me['controlId'] for c in ctrls):
        print(f'  {MODE} already sits alone on the top row')
    else:
        place = {me['controlId']: {'row': 0, 'col': 0, 'size': 12}}
        for c in ctrls:
            if c['controlId'] != me['controlId'] and (c.get('row') or 0) < 9999:
                place[c['controlId']] = {'row': (c.get('row') or 0) + 1}
        C.pinned_write(ORDERS, place, 'templates_orders_pre_mode_place', 'mode/place')
    print(f'  options: {MODE_QUOTATION}={quotation}  {MODE_TEMPLATE}={template}')


def mode_rules(of):
    m, number, it = of[MODE], of['Number'], of['Is Template']
    as_template = C.cond(m, C.EQ, option_key(m, MODE_TEMPLATE))
    as_quotation = C.cond(m, C.EQ, option_key(m, MODE_QUOTATION))
    creating = C.cond(number, C.EMPTY)
    saved = C.cond(number, C.NOT_EMPTY)
    return [
        (MODE_RULES[0], C.INTERACTION, [saved], [C.item(C.HIDE, m)], {}),
        (MODE_RULES[1], C.INTERACTION, [creating], [C.item(C.HIDE, it)], {}),
        (MODE_RULES[2], C.INTERACTION, C.any_of([as_template, creating], [C.cond(it, C.EQ, 1)]),
         [C.item(C.HIDE, *[of[n] for n in NOT_COPIED])], {}),
        # and the from-template pair belongs to Create Quotation
        (RULES[0][0], C.INTERACTION, C.any_of([saved], [as_template]), [C.item(C.HIDE, of[TOGGLE])], {}),
        (RULES[1][0], C.INTERACTION, C.any_of([C.cond(of[TOGGLE], C.EQ, 1), as_quotation],
                                              [saved, C.cond(of[TEMPLATE], C.NOT_EMPTY)]),
         [C.item(C.SHOW, of[TEMPLATE])], {}),
    ]


# ── the Order Lines query ───────────────────────────────────────────────────

def session():
    from hap_cli.core.session import Session
    return Session.load()


def queries():
    r = session().api_call('Worksheet', 'GetQueryBySheetId', {'worksheetId': ORDERS})
    return (r.get('data', r) or {}).get('queries') or []


def wanted_query(of, lf, qid=''):
    return {
        'id': qid, 'worksheetId': ORDERS, 'controlId': of['Order Lines']['controlId'], 'controlType': 34,
        'sourceId': OLINES, 'sourceType': 2,
        'items': [{'controlId': lf['Orders']['controlId'], 'dataType': 29, 'spliceType': 1, 'filterType': 51,
                   'dateRange': 0, 'dateRangeType': 0, 'value': '', 'values': [], 'minValue': '', 'maxValue': '',
                   'isAsc': False, 'advancedSetting': {}, 'isGroup': False, 'groupFilters': [], 'emptyRule': 3,
                   'dynamicSource': [{'rcid': '', 'cid': of[TEMPLATE]['controlId'], 'staticValue': '',
                                      'isAsync': False, 'type': 0}]}],
        'configs': [{'cid': lf[n]['controlId'], 'subCid': lf[n]['controlId']} for n in QUERY_COLUMNS],
        'moreType': 0, 'recordsNotFound': 0, 'queryCount': QUERY_ROWS, 'resultType': 0, 'eventType': 0,
        'moreSort': [{'controlId': lf['Sequence']['controlId'], 'isAsc': True}],
    }


def query_state(q):
    return (q.get('controlId'), q.get('sourceId'),
            sorted((i.get('controlId'), i.get('filterType'), tuple(d.get('cid') for d in i.get('dynamicSource') or []))
                   for i in q.get('items') or []),
            sorted((m.get('cid'), m.get('subCid')) for m in q.get('configs') or []),
            [(s.get('controlId'), s.get('isAsc')) for s in q.get('moreSort') or []], q.get('queryCount'))


def ours(of):
    return next((q for q in queries() if q.get('controlId') == of['Order Lines']['controlId']), None)


def step_query():
    of, lf = guard()
    # GetQueryBySheetId lists only the queries a control points at, so a saved query is proved after the pointer.
    live = ours(of)
    known = hap.ids().get('queries', {}).get('Orders: Order Lines from Quotation Template', '')
    want = wanted_query(of, lf, live['id'] if live else known)
    if live and query_state(live) == query_state(want):
        print(f'  the Order Lines query {live["id"]} is as specified; not re-saved')
        qid = live['id']
    else:
        hap.backup('templates_orders_queries', queries())
        r = session().api_call('Worksheet', 'SaveQuery', want)
        r = r.get('data', r) if isinstance(r, dict) and 'data' in r else r
        qid = (r or {}).get('id')
        if not qid:
            sys.exit(f'SaveQuery answered no id: {json.dumps(r, ensure_ascii=False)[:500]}')
        print(f'  SaveQuery stored {qid}')
    C.remember('queries', 'Orders: Order Lines from Quotation Template', qid)
    pointer = json.dumps({'id': qid, 'sourceId': OLINES}, separators=(',', ':'))
    a = of['Order Lines'].get('advancedSetting') or {}
    try:
        same = json.loads(a.get('dynamicsrc') or '{}') == json.loads(pointer) and a.get('defaulttype') == '2'
    except ValueError:
        same = False
    if same:
        print('  Order Lines already defaults from that query; nothing saved')
    else:
        C.pinned_write(ORDERS, {of['Order Lines']['controlId']: {'advancedSetting.dynamicsrc': pointer,
                                                                  'advancedSetting.defaulttype': '2'}},
                       'templates_orders_pre_query_pointer', 'query/pointer')
    live = ours(of)
    if not live or live['id'] != qid or query_state(live) != query_state(wanted_query(of, lf, qid)):
        sys.exit(f'the query did not read back as specified: {json.dumps(live, ensure_ascii=False)[:800]}')
    print(f'  the Order Lines query {qid} reads back as specified')


# ── check ───────────────────────────────────────────────────────────────────

def step_check():
    of, lf = guard()
    problems = []
    for n in (TOGGLE, TEMPLATE):
        if n not in of:
            problems.append(f'{n} is not on Orders')
    if problems:
        sys.exit('check: ' + '; '.join(problems))
    t = of[TEMPLATE]
    a = t.get('advancedSetting') or {}
    print(f'  {TEMPLATE}: {t["controlId"]} -> {t.get("dataSource")} alias={t.get("alias")!r} '
          f'row {t.get("row")} filters={C.picker_state(a.get("filters"))}')
    if t.get('dataSource') != ORDERS:
        problems.append(f'{TEMPLATE} does not point at Orders')
    if C.picker_state(a.get('filters')) != C.picker_state(C.active_picker(is_template(of))):
        problems.append(f'{TEMPLATE} offers more than templates')
    for n in PLACE:
        if (of[n].get('row'), of[n].get('col')) != PLACE[n][:2]:
            print(f'  note: {n} sits at row {of[n].get("row")} col {of[n].get("col")}, intended {PLACE[n][:2]}')
    live_rules = {r['name'] for r in hap.listing('worksheet', 'rules', ORDERS)}
    for name, *_ in RULES:
        print(f'  rule {name!r}: {"present" if name in live_rules else "MISSING"}')
        if name not in live_rules:
            problems.append(f'rule {name!r} missing')
    for name in FILLS:
        got = fill_state((of[name].get('advancedSetting') or {}).get('defsource'))
        ok = got == fill_state(fill_source(of, name))
        print(f'  {name}: {"reads the template" if ok else got}')
        if not ok:
            problems.append(f'{name} does not read the template')
    hidden = C.view_info(ORDERS, APP, ALL_VIEW).get('controls') or []
    if any(of[n]['controlId'] in hidden for n in (TOGGLE, TEMPLATE)):
        problems.append('the All view hides them, and so hides them in its forms')
    q = ours(of)
    ok = q and query_state(q) == query_state(wanted_query(of, lf, q['id']))
    print(f'  Order Lines query: {q["id"] if q else "none"} {"as specified" if ok else "DIFFERS"}')
    if not ok:
        problems.append('the Order Lines query is missing or differs')
    a = of['Order Lines'].get('advancedSetting') or {}
    print(f'  Order Lines default: type {a.get("defaulttype")!r} {a.get("dynamicsrc")}')
    if q and (a.get('defaulttype') != '2' or json.loads(a.get('dynamicsrc') or '{}').get('id') != q['id']):
        problems.append('Order Lines does not default from the query')
    # the switch, its workflow, Tax Mode
    if MODE in of:
        m = of[MODE]
        a = m.get('advancedSetting') or {}
        print(f"  {MODE}: type {m['type']} showtype {a.get('showtype')} direction {a.get('direction')} "
              f"row {m.get('row')} options {[o['value'] for o in m['options'] if not o.get('isDeleted')]}")
        if m['type'] != 9 or a.get('direction') != '2' or m.get('row') != 0:
            problems.append(f'{MODE} is not the tiled switch on the top row')
        for name in MODE_RULES:
            if name not in live_rules:
                problems.append(f'rule {name!r} missing')
        import o2i
        pid = o2i.workflow_id(FLAG_WORKFLOW)
        _, byname = o2i.nodes_by_name(pid) if pid else (None, {})
        print(f"  {FLAG_WORKFLOW}: {pid} steps {sorted(n for n in byname if n.startswith(('Tick', 'When')))}")
        if not pid or 'Tick Is Template' not in byname:
            problems.append(f'{FLAG_WORKFLOW} missing or empty')
    else:
        problems.append(f'{MODE} is not on Orders')
    for n in (TAX_TEXT, TAX_LOOKUP):
        if n not in of:
            problems.append(f'{n} is not on Orders')
    if TAX_LOOKUP in of and TAX_TEXT in of:
        ok = of[TAX_LOOKUP].get('sourceControlId') == of[TAX_TEXT]['controlId'] and \
            (of['Tax Mode'].get('advancedSetting') or {}).get('defaultfunc') and \
            json.loads(of['Tax Mode']['advancedSetting']['defaultfunc'])['expression'] == json.loads(tax_function(of))['expression']
        print(f"  Tax Mode: {'reads the template, Tax Excluded without one' if ok else 'DIFFERS'}")
        if not ok:
            problems.append('Tax Mode does not default from the template')
    print('check: ' + ('OK' if not problems else 'PROBLEMS\n  ' + '\n  '.join(problems)))
    if problems:
        sys.exit(1)


STEPS = {'controls': step_controls, 'taxmode': step_taxmode, 'mode': step_mode, 'flag': step_flag, 'place': step_place, 'views': step_views, 'rules': step_rules, 'fills': step_fills,
         'query': step_query, 'check': step_check}

if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] not in STEPS:
        sys.exit('steps: ' + ' '.join(STEPS))
    STEPS[sys.argv[1]]()
