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
    fills     the relation-read defaults on the five controls
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
FILLS = ['Terms and conditions', 'Journal', 'Online Signature', 'Online Payment', 'Prepayment Percentage']

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
    print('check: ' + ('OK' if not problems else 'PROBLEMS\n  ' + '\n  '.join(problems)))
    if problems:
        sys.exit(1)


STEPS = {'controls': step_controls, 'place': step_place, 'views': step_views, 'rules': step_rules, 'fills': step_fills,
         'query': step_query, 'check': step_check}

if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] not in STEPS:
        sys.exit('steps: ' + ' '.join(STEPS))
    STEPS[sys.argv[1]]()
