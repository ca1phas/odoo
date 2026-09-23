#!/usr/bin/env python3
"""Build the Sales Dashboard: one custom page of charts in ERP Master's Sales menu group, after Order Lines.

Requirements and results: nocoly/worksheets/23-sales-dashboard.md. Run from the repo root with the CLI's interpreter:

    ~/.hap-venv/bin/python nocoly/build/dashboard.py page      # 1. the custom page, in Sales right after Order Lines
    ~/.hap-venv/bin/python nocoly/build/dashboard.py charts    # 2. every chart whose controls exist, created or
                                                               #    brought back to this spec
    ~/.hap-venv/bin/python nocoly/build/dashboard.py layout    # 3. the page: the date filter and the charts, placed
    ~/.hap-venv/bin/python nocoly/build/dashboard.py all       # 1-3, then check
    ~/.hap-venv/bin/python nocoly/build/dashboard.py check     # the page, every chart and its stored filter against
                                                               #    this spec, then every figure the charts draw
                                                               #    against the same figure computed from the records
    ~/.hap-venv/bin/python nocoly/build/dashboard.py data "Top customers"   # one chart's raw getData answer

Every step reads the live state first and is safe to re-run; a second run writes nothing.

**What this writes.** One custom page, the charts on it (HAP stores a chart as its own object against a worksheet —
`sourceType` 1, a chart made on a page, so none of them clutters a worksheet's own Statistics list), each chart's
stored condition filter (`SaveWorksheetFilter`, `module` 2), and the page's one filter group. **No worksheet control,
record, view or workflow is written**, and nothing is ever deleted: a chart this script no longer wants is left
alone and reported.

**Charts are verified two ways.** `check` compares the stored config with this spec, then asks the chart for the
numbers it draws (`report/getData`, the call the page itself makes) and compares them with the same numbers computed
here from the records (GetRowDetail's `rowData`, the one complete read — demo.py `all_rows`).
"""
import datetime, json, sys, uuid
from collections import Counter, defaultdict

import hap
import common as C

APP = hap.ids()['app']
KEY = 'Sales Dashboard: '                      # ids.json key prefix
PAGE_NAME = 'Sales Dashboard'
SECTION = 'Sales'
AFTER = None                                   # the sidebar item the page sits right after; None puts it first.
                                               # The owner moved it to the top of Sales on 23 Sep 2026.
WHERE = f'right after {AFTER}' if AFTER else 'first in the section'
ICON = 'sys_dashboard'
PAGE_DESC = 'Sales at a glance: confirmed sales, open quotations, invoicing and the best customers and products.'

# ── wire codes (pd-openweb) ─────────────────────────────────────────────────
NUMBER, COLUMN, PIE, RANKING = 10, 1, 3, 16          # reportType (Statistics/Charts/common.js; there is no 4)
SUM, COUNT = 1, 5                                    # yaxisList[].normType
MONTH = 3                                            # xaxes.particleSizeType
EQ, NE, EQ_SINGLE, NE_SINGLE, DATE_LT = 2, 6, 51, 52, 35   # FILTER_CONDITION_TYPE (WorkSheetFilter/enum.js)
TODAY = 1                                            # a date condition's dateRange: today
RANGE_ALL, RANGE_THIS_MONTH, RANGE_DYNAMIC = 0, 8, 21     # a chart's filter.rangeType (Statistics/common/timeUtils.js)
DESC = 2                                             # a sort direction: descending
CHART_COMPONENT, FILTER_COMPONENT = 1, 6             # custom-page component types (customPage/util.js)
DATEENUM = 17                                        # a page filter's "date is" (the preset-range picker)
RECORD_COUNT = {'controlId': 'record_count', 'controlName': 'Record count', 'type': 10000000}
MONEY_PREFIX = 'RM '                                 # every amount in the app is in ringgit; the controls carry no unit

# The last twelve months, month-aligned: from the first day of the month eleven months back to today.
LAST_12_MONTHS = {'startType': 5, 'startCount': 11, 'startUnit': 3, 'endType': 1, 'endCount': 1, 'endUnit': 1}

# ── the charts ──────────────────────────────────────────────────────────────
#
# Each: worksheet, reportType, title, description (user-facing: plain words, no field names), x (control name or
# None), grain, y [(control name | 'count', normType, label)], conditions [(control, op, option labels | None)],
# range (filterRangeId control name or 'ctime', rangeType, dynamicFilter), extras, and where it sits on the page.
# A condition's option labels are resolved to keys live; a control that is not on the worksheet yet makes the chart
# wait (reported, nothing written) — Overdue and Received this month wait on Invoices' payment controls.

CONFIRMED = 'Sales Order'
OPEN = ('Quotation', 'Quotation Sent')

CHARTS = {
    # The headlines are single-value cards, two rows of them (Orders, then Invoices). Two values in one card clipped
    # at the owner's ~1250 px page (coordinator, 23 Sep): with the 48-column grid's 10 px margins and the card's 15 px
    # padding, each half of a two-value card at 12 columns has ~111 px for its value, and "RM 1,382,807.20" at the
    # default 28 px needs ~190 px — a two-value card fits only from ~19 columns, so two of them and three singles
    # cannot share one row. A single value at 12 columns has ~242 px; at 16, ~345 px.
    'Confirmed sales': dict(
        ws='Orders', type=NUMBER,
        desc='The value of all confirmed sales orders, before tax.',
        y=[('Untaxed Amount', SUM, 'Untaxed amount')],
        where=[('Status', 'is', [CONFIRMED])],
        range=('Quotation/Order Date', RANGE_ALL, None),
        place=(0, 3, 12, 6)),
    'Open quotations': dict(
        ws='Orders', type=NUMBER,
        desc='How many quotations are waiting to be confirmed or cancelled. Templates are left out.',
        y=[('count', COUNT, 'Quotations')],
        where=[('Status', 'is', list(OPEN)), ('Is Template', 'unticked', None)],
        range=('Quotation/Order Date', RANGE_ALL, None),
        place=(12, 3, 12, 6)),
    'Value of open quotations': dict(
        ws='Orders', type=NUMBER,
        desc='What the quotations waiting to be confirmed or cancelled are worth, before tax. Templates are left out.',
        y=[('Untaxed Amount', SUM, 'Untaxed amount')],
        where=[('Status', 'is', list(OPEN)), ('Is Template', 'unticked', None)],
        range=('Quotation/Order Date', RANGE_ALL, None),
        place=(24, 3, 12, 6)),
    'Orders to invoice': dict(
        ws='Orders', type=NUMBER,
        desc='Orders with something ready to be invoiced.',
        y=[('count', COUNT, 'Orders')],
        where=[('Invoice Status', 'is', ['To Invoice'])],
        range=('Quotation/Order Date', RANGE_ALL, None),
        place=(36, 3, 12, 6)),
    'Overdue invoices': dict(
        ws='Invoices', type=NUMBER,
        desc='Posted customer invoices past their due date and not fully paid.',
        y=[('count', COUNT, 'Invoices')],
        where=[('Status', 'is', ['Posted']), ('Type', 'is', ['Customer Invoice']),
               ('Due Date', 'before today', None), ('Payment Status', 'is not', ['Paid'])],
        range=('Invoice Date', RANGE_ALL, None),
        place=(0, 9, 16, 6)),
    'Amount overdue': dict(
        ws='Invoices', type=NUMBER,
        desc='What is still due on posted customer invoices past their due date.',
        y=[('Amount Due', SUM, 'Amount due')],
        where=[('Status', 'is', ['Posted']), ('Type', 'is', ['Customer Invoice']),
               ('Due Date', 'before today', None), ('Payment Status', 'is not', ['Paid'])],
        range=('Invoice Date', RANGE_ALL, None),
        place=(16, 9, 16, 6)),
    'Received this month': dict(
        ws='Invoices', type=NUMBER,
        desc='Payments received this month on customer invoices.',
        y=[('Amount Paid', SUM, 'Amount received')],
        where=[('Type', 'is', ['Customer Invoice'])],
        range=('Last Payment Date', RANGE_THIS_MONTH, None),
        place=(32, 9, 16, 6)),
    'Monthly sales': dict(
        ws='Orders', type=COLUMN,
        desc='Confirmed sales by month over the last twelve months, before tax.',
        x='Quotation/Order Date', grain=MONTH,
        y=[('Untaxed Amount', SUM, 'Untaxed amount')],
        where=[('Status', 'is', [CONFIRMED])],
        range=('Quotation/Order Date', RANGE_DYNAMIC, LAST_12_MONTHS),
        place=(0, 15, 32, 11)),
    'Quotations and orders by status': dict(
        ws='Orders', type=PIE,
        desc='How many quotations and orders are at each stage. Templates are left out.',
        x='Status',
        y=[('count', COUNT, 'Orders')],
        where=[('Is Template', 'unticked', None)],
        range=('Quotation/Order Date', RANGE_ALL, None),
        place=(32, 15, 16, 11)),
    'Top customers': dict(
        ws='Orders', type=RANKING,
        desc='The ten customers with the most confirmed sales, before tax.',
        x='Customer',
        y=[('Untaxed Amount', SUM, 'Untaxed amount')],
        where=[('Status', 'is', [CONFIRMED])],
        range=('Quotation/Order Date', RANGE_ALL, None),
        top=10, place=(0, 26, 24, 11)),
    'Sales by salesperson': dict(
        ws='Orders', type=COLUMN, horizontal=True,
        desc='Confirmed sales by salesperson, before tax.',
        x='Salesperson',
        y=[('Untaxed Amount', SUM, 'Untaxed amount')],
        where=[('Status', 'is', [CONFIRMED])],
        range=('Quotation/Order Date', RANGE_ALL, None),
        sort_desc=True, place=(24, 26, 24, 11)),
    'Sales orders by invoicing status': dict(
        ws='Orders', type=PIE,
        desc='Confirmed sales orders by how far they have been invoiced.',
        x='Invoice Status',
        y=[('count', COUNT, 'Orders')],
        where=[('Status', 'is', [CONFIRMED])],
        range=('Quotation/Order Date', RANGE_ALL, None),
        place=(0, 37, 16, 11)),
    'Top products': dict(
        ws='Order Lines', type=RANKING,
        desc='The ten products with the most confirmed sales, before tax.',
        x='Product',
        y=[('Subtotal', SUM, 'Untaxed amount')],
        where=[('Display Type', 'is', ['Product']), ('Order Status', 'is', [CONFIRMED])],
        range=('ctime', RANGE_ALL, None),
        top=10, place=(16, 37, 32, 11)),
}

# The page's one filter: the order date, over every chart built on Orders. Invoices and Order Lines carry no order
# date (Order Lines will, once its lookups exist), so those charts are not bound to it.
PAGE_FILTER = dict(name='Order date', ws='Orders', control='Quotation/Order Date', place=(0, 0, 48, 3),
                   # the date field it reads on each worksheet; Order Lines' is the hidden lookup of its order's date.
                   # Lines that existed before that lookup was added (23 Sep) hold it empty until they are
                   # re-created, so until the reseed a date pick empties Top products (coordinator's call).
                   controls={'Orders': 'Quotation/Order Date', 'Order Lines': 'Order Date'})
FILTER_DATERANGE = '[1,2,3,4,5,6,7,8,9,12,13,14,15,16,17,52,21,22,23,51,31,32,33]'   # every preset the picker offers


# ── plumbing ────────────────────────────────────────────────────────────────

_SESSION = None


def session():
    global _SESSION
    if _SESSION is None:
        from hap_cli.core.session import Session
        _SESSION = Session.load(None)
    return _SESSION


def ws(name):
    return hap.ids()['worksheets'][name]


_CTRLS = {}


def ctrls(name, fresh=False):
    if fresh or name not in _CTRLS:
        _CTRLS[name] = hap.by_name(hap.controls(ws(name)))
    return _CTRLS[name]


def remembered(key):
    return hap.ids().get('dashboard', {}).get(KEY + key)


def remember(key, value):
    C.remember('dashboard', KEY + key, value)


def options_of(worksheet, c):
    """A dropdown's options — a lookup (30) carries none, so they are read off the control it shows."""
    if c['type'] == 30 and not c.get('options'):
        rel = next(r for r in ctrls(worksheet).values() if r['controlId'] == c['dataSource'].strip('$'))
        target = next(n for n, i in hap.ids()['worksheets'].items() if i == rel['dataSource'])
        c = next(x for x in ctrls(target).values() if x['controlId'] == c['sourceControlId'])
    return c.get('options') or []


def option_keys(c, labels, worksheet=None):
    live = {o['value']: o['key'] for o in options_of(worksheet, c) if not o.get('isDeleted')}
    missing = [l for l in labels if l not in live]
    if missing:
        sys.exit(f"{c['controlName']}: no option {missing} (it has {list(live)})")
    return [live[l] for l in labels]


def data_type(c):
    """A lookup (30) filters as the control it shows."""
    return c.get('sourceControlType') or c['type'] if c['type'] == 30 else c['type']


def missing_controls(spec):
    f = ctrls(spec['ws'])
    names = [n for n, _, _ in spec['y'] if n != 'count'] + [n for n, _, _ in spec['where']]
    names += [spec['x']] if spec.get('x') else []
    names += [spec['range'][0]] if spec['range'][0] != 'ctime' else []
    return [n for n in dict.fromkeys(names) if n not in f]


# ── a chart's spec ──────────────────────────────────────────────────────────

def conditions(spec):
    """The chart's condition filter, as the stored filter's `items`."""
    f, out = ctrls(spec['ws']), []
    for name, op, labels in spec['where']:
        c = f[name]
        base = {'controlId': c['controlId'], 'dataType': data_type(c), 'spliceType': 1, 'dateRange': 0,
                'dateRangeType': 0, 'value': '', 'values': [], 'minValue': '', 'maxValue': '', 'isAsc': False,
                'dynamicSource': [], 'isGroup': False, 'groupFilters': None}
        if op in ('is', 'is not'):
            out.append(dict(base, filterType=EQ_SINGLE if op == 'is' else NE_SINGLE, values=option_keys(c, labels, spec['ws'])))
        elif op == 'unticked':
            out.append(dict(base, filterType=NE, value='1', values=['1']))
        elif op == 'before today':
            out.append(dict(base, filterType=DATE_LT, dateRange=TODAY))
        else:
            sys.exit(f'unknown condition {op!r}')
    return out


def condition_state(items):
    """What a stored or wanted condition means — the server adds and reorders keys, so never byte for byte."""
    return sorted((i.get('controlId'), i.get('dataType'), i.get('filterType'), int(i.get('dateRange') or 0),
                   tuple(sorted(i.get('values') or []))) for i in items or [])


def yaxis(spec, name, norm, label):
    if name == 'count':
        c = RECORD_COUNT
        return {'controlId': c['controlId'], 'controlName': c['controlName'], 'controlType': c['type'],
                'normType': norm, 'rename': label, 'dot': 0, 'magnitude': 1, 'fixType': 0, 'suffix': '',
                'roundType': 2, 'dotFormat': '1', 'emptyShowType': 0, 'showNumber': True, 'thousandth': True,
                'hide': False, 'ydot': '', 'advancedSetting': {},
                'percent': {'enable': False, 'type': 2, 'dot': '2', 'dotFormat': '1', 'roundType': 2}}
    c = ctrls(spec['ws'])[name]
    return {'controlId': c['controlId'], 'controlName': c['controlName'], 'controlType': c['type'],
            'normType': norm, 'rename': label, 'dot': 2, 'magnitude': 1, 'fixType': 1, 'suffix': MONEY_PREFIX,
            'roundType': 2, 'dotFormat': '0',                  # '0' keeps both decimals: RM 1,383,107.20, not .2 'emptyShowType': 0, 'showNumber': True, 'thousandth': True,
            'hide': False, 'ydot': 2, 'advancedSetting': {},
            'percent': {'enable': False, 'type': 2, 'dot': '2', 'dotFormat': '1', 'roundType': 2}}


EMPTY_AXIS = {'controlId': '', 'sortType': 0, 'particleSizeType': 0, 'rename': '', 'emptyType': 0, 'fields': None,
              'subTotal': False, 'subTotalName': None, 'showFormat': '4', 'displayMode': 'text', 'controlName': '',
              'controlType': 0, 'dataSource': '', 'options': [], 'advancedSetting': None, 'relationControl': None,
              'cid': '', 'cname': '', 'xaxisEmpty': False, 'xaxisEmptyType': 0, 'c_Id': ''}


def xaxis(spec):
    if not spec.get('x'):
        return dict(EMPTY_AXIS)
    c = ctrls(spec['ws'])[spec['x']]
    return dict(EMPTY_AXIS, controlId=c['controlId'], controlName=c['controlName'], controlType=c['type'],
                particleSizeType=spec.get('grain', 0), dataSource=c.get('dataSource') or '',
                advancedSetting={}, cid=c['controlId'], cname=c['controlName'], c_Id=c['controlId'],
                sortType=1 if spec.get('grain') else 0)


def time_range(spec):
    rid, rtype, dynamic = spec['range']
    name = 'Creation time' if rid == 'ctime' else rid
    rid = rid if rid == 'ctime' else ctrls(spec['ws'])[rid]['controlId']
    return {'filterRangeId': rid, 'filterRangeName': name, 'rangeType': rtype, 'rangeValue': None,
            'today': True, 'ignoreToday': False, 'dynamicFilter': dynamic, 'customRangeValue': None,
            'startDate': '', 'endDate': ''}


def display(spec):
    """displaySetup: click-through on (showRowList — a click on the chart opens its records), a top-N cap, bars laid
    horizontally for Sales by salesperson, a legend and percentages on the pies."""
    return {'isPerPile': False, 'isPile': False, 'isAccumulate': False, 'accumulatePerPile': None,
            'isToday': False, 'isLifecycle': False, 'lifecycleValue': 0, 'contrastType': 0, 'fontStyle': 1,
            'showTotal': False, 'showTitle': True, 'showLegend': spec['type'] == PIE, 'legendType': 1,
            'showDimension': True, 'showNumber': True, 'showPercent': spec['type'] == PIE,
            'showXAxisCount': spec.get('top', 0), 'showChartType': 2 if spec.get('horizontal') else 1,
            'showPileTotal': True, 'hideOverlapText': False, 'showRowList': True, 'showControlIds': [],
            'auxiliaryLines': [], 'showOptionIds': [], 'contrast': False, 'colorRules': [],
            'percent': {'enable': False, 'type': 2, 'dot': '2', 'dotFormat': '1', 'roundType': 2},
            'mergeCell': True, 'previewUrl': None, 'imageUrl': None, 'xaxisEmpty': False,
            'xdisplay': {'showDial': True, 'showTitle': False, 'title': '', 'minValue': None, 'maxValue': None},
            'ydisplay': {'showDial': True, 'showTitle': False, 'title': '', 'minValue': None, 'maxValue': None,
                         'lineStyle': 1, 'showNumber': None}}


def sorts(spec, y):
    return [{y[0]['controlId']: DESC}] if spec['type'] == RANKING or spec.get('sort_desc') else []


def style(spec):
    return {'topStyle': 'crown', 'valueProgressVisible': True} if spec['type'] == RANKING else {}


def body(name, spec, filter_id):
    y = [yaxis(spec, *t) for t in spec['y']]
    return {'desc': spec['desc'], 'xaxes': xaxis(spec), 'yaxisList': y, 'yreportType': None,
            'displaySetup': display(spec), 'filter': dict(time_range(spec), filterId=filter_id),
            'sorts': sorts(spec, y), 'formulas': [], 'style': style(spec), 'split': dict(EMPTY_AXIS), 'splitId': '',
            'summary': {'controlId': '', 'type': 1, 'name': 'Total', 'number': True, 'percent': False, 'sum': 0,
                        'contrastSum': 0, 'contrastMapSum': 0, 'rename': ''},
            'sourceType': 1, 'auth': 1, 'isPublic': True}


# ── what a chart is, compared ───────────────────────────────────────────────

def chart_state(cfg):
    """The parts of a stored chart this script owns, in comparable form."""
    x, d, flt = cfg.get('xaxes') or {}, cfg.get('displaySetup') or {}, cfg.get('filter') or {}
    return dict(
        name=cfg.get('name'), desc=cfg.get('desc') or '', type=cfg.get('reportType'),
        x=(x.get('controlId') or '', x.get('particleSizeType') or 0),
        y=[(i.get('controlId'), i.get('normType'), i.get('rename') or '', i.get('fixType') or 0, i.get('suffix') or '',
            str(i.get('dotFormat')), i.get('dot'))
           for i in cfg.get('yaxisList') or []],
        range=(flt.get('filterRangeId'), flt.get('rangeType'), json.dumps(flt.get('dynamicFilter') or None,
                                                                         sort_keys=True)),
        rows=bool(d.get('showRowList')), top=d.get('showXAxisCount') or 0, legend=bool(d.get('showLegend')),
        horizontal=d.get('showChartType') == 2,
        sorts=json.dumps(cfg.get('sorts') or [], sort_keys=True),
        style=json.dumps({k: (cfg.get('style') or {}).get(k) for k in ('topStyle', 'valueProgressVisible')},
                         sort_keys=True))


def wanted_state(name, spec):
    return chart_state(dict(body(name, spec, None), name=name, reportType=spec['type']))


def alive(name):
    d = chart_data(name)
    return isinstance(d, dict) and d.get('status') == 1


def retired():
    return {v for k, v in hap.ids().get('dashboard', {}).items() if k.startswith(KEY + 'retired ')}


def get_chart(report_id):
    from hap_cli.core import chart as chart_mod
    for attempt in range(4):
        try:
            cfg = chart_mod.get_chart(session(), report_id)
            break
        except Exception as e:
            # Transient failures are real: on 23 Sep 2026 a read failed on the CLI's own access-check cache file
            # (another agent's hap run renamed it underneath), and `layout` then saved the page without that chart.
            last = e
    else:
        sys.exit(f'chart {report_id} did not read after 4 tries: {last}')
    cfg = cfg.get('data', cfg) if isinstance(cfg, dict) and 'data' in cfg and isinstance(cfg['data'], dict) else cfg
    return cfg if isinstance(cfg, dict) and cfg.get('name') is not None else None


def stored_conditions(filter_id):
    if not filter_id:
        return []
    res = session().api_call('Worksheet', 'GetWorksheetFilterById', {'filterId': filter_id})
    data = res.get('data', res) if isinstance(res, dict) else {}
    return (data or {}).get('items') or []


def save_filter(spec, filter_id=''):
    """Store the chart's condition filter (a new one, or the same id rewritten) and prove it read back."""
    items = conditions(spec)
    res = session().api_call('Worksheet', 'SaveWorksheetFilter',
                             {'filterId': filter_id or '', 'name': '', 'type': '', 'worksheetId': ws(spec['ws']),
                              'appId': APP, 'module': 2, 'items': items})
    fid = (res or {}).get('filterId') or ((res or {}).get('data') or {}).get('filterId')
    if not fid:
        sys.exit(f'SaveWorksheetFilter answered {res!r}')
    back = stored_conditions(fid)
    if condition_state(back) != condition_state(items):
        sys.exit(f'the condition filter {fid} read back as {condition_state(back)}, wanted {condition_state(items)}')
    return fid


def save_chart(name, spec, report_id, filter_id):
    from hap_cli.core import chart as chart_mod
    extra = body(name, spec, filter_id)
    if report_id:                                            # update: on top of the stored config, as the guide says
        live = get_chart(report_id) or {}
        extra = {**{k: v for k, v in live.items() if k not in ('controls', 'account', 'createdDate', 'views')},
                 **extra}
    res = chart_mod.save_chart(session(), report_id=report_id or '', app_id=ws(spec['ws']), name=name,
                               report_type=spec['type'], extra=extra)
    rid = res if isinstance(res, str) else (res or {}).get('reportId') or (res or {}).get('id') or \
        ((res or {}).get('data') if isinstance((res or {}).get('data'), str) else None)
    rid = rid or report_id
    if not rid:
        sys.exit(f'{name}: saveReportConfig answered {res!r}')
    back = get_chart(rid)
    if not back or chart_state(back) != wanted_state(name, spec):
        got = chart_state(back) if back else None
        want = wanted_state(name, spec)
        diff = {k: (got.get(k), want[k]) for k in want if not got or got.get(k) != want[k]}
        sys.exit(f'{name}: the chart {rid} read back with differences {json.dumps(diff, default=str)}')
    if (back.get('filter') or {}).get('filterId') != filter_id:
        sys.exit(f"{name}: the chart stored filterId {(back.get('filter') or {}).get('filterId')}, wanted {filter_id}")
    return rid


# ── 4 · the Order Lines lookups ─────────────────────────────────────────────
#
# So a line can be charted by its order's date, customer and salesperson — what Odoo's `sale.report` joins in SQL
# (18 §2). Three hidden lookups off the line's Orders relation. The fourth 18 §2 listed, **Order Status**, already
# exists (o2i.py, `6ab2cb9d805aef7032e32a68`) and is reused. Aliases: `order_partner_id` and `salesman_id` are
# `sale.order.line`'s own related fields (`sale/models/sale_order_line.py:48-55`, 19.0 source); the line has no
# order date of its own, so Order Date takes the name of the field it mirrors, `date_order`. Hidden (`011`), so
# never a column and never on the form; `add-fields` parks them at row 9999, and a hidden control needs no place.

OL_RELATION = 'Orders'                                # Order Lines' relation to its order
LOOKUPS = {  # name on Order Lines: (alias, control on Orders)
    'Order Date': ('date_order', 'Quotation/Order Date'),
    'Customer': ('order_partner_id', 'Customer'),
    'Salesperson': ('salesman_id', 'Salesperson'),
}
HIDDEN = '011'
STORED_LOOKUP = '00'


def lookup_spec(name):
    alias, source = LOOKUPS[name]
    rel = ctrls('Order Lines')[OL_RELATION]['controlId']
    return {'type': 30, 'alias': alias, 'desc': '', 'required': False, 'fieldPermission': HIDDEN,
            'dataSource': f'${rel}$', 'sourceControlId': ctrls('Orders')[source]['controlId'],
            'strDefault': STORED_LOOKUP}


def lookup_control(name):
    alias, source = LOOKUPS[name]
    c = C.control('SHEET_FIELD', name, (9999, 0, 6), alias=alias, hint='', desc='',
                  data_source=ctrls('Order Lines')[OL_RELATION]['controlId'],
                  source_control_id=ctrls('Orders')[source]['controlId'],
                  extra={'strDefault': STORED_LOOKUP, 'dot': 0})
    c['fieldPermission'] = HIDDEN
    return c


def step_lookups():
    live = ctrls('Order Lines', fresh=True)
    print(f'  Order Lines read live: {len(live)} controls')
    clash = [n for n in LOOKUPS if n in live and live[n]['type'] != 30]
    if clash:
        sys.exit(f'Order Lines already has {clash} as something other than a lookup — look before adding')
    missing = [n for n in LOOKUPS if n not in live]
    if missing:
        live = C.append_checked(ws('Order Lines'), [lookup_control(n) for n in missing],
                                'dashboard_orderlines_pre_lookups', 'lookups')
        _CTRLS['Order Lines'] = live
    else:
        print(f'  {list(LOOKUPS)} are already there; nothing appended')
    for n in LOOKUPS:
        stale = C.drift(live[n], lookup_spec(n))
        if stale:
            sys.exit(f'{n} read back with {stale} unlike the spec — not repaired here; look first')
        remember('Order Lines: ' + n, live[n]['controlId'])
        c = live[n]
        print(f"  OK  {n:<12} {c['controlId']} t{c['type']} alias={c.get('alias')!r} perm={c.get('fieldPermission')} "
              f"ds={c.get('dataSource')} src={c.get('sourceControlId')} row={c.get('row')}")
    return lookups_read()


def lookups_read():
    """Every order line's three lookups against its own order, through rowData (the complete read)."""
    import demo
    f = ctrls('Order Lines')
    orders = {k: d for k, d in all_rows('Orders').items()}
    fo = ctrls('Orders')
    bad, n = [], 0
    for rowid, d in all_rows('Order Lines').items():
        order = demo.one_id(d, f, OL_RELATION)
        if order not in orders:
            continue
        n += 1
        o = orders[order]
        want = (demo.t(o, fo, 'Quotation/Order Date')[:16], demo.one_id(o, fo, 'Customer'), salesperson(o))
        got = (demo.t(d, f, 'Order Date')[:16], demo.one_id(d, f, 'Customer'),
               (demo._items(demo.raw(d, f, 'Salesperson')) or [{}])[0].get('fullname', ''))
        if got != want:
            bad.append((rowid, got, want))
    print(f'  lookups read back on {n} order lines: ' + ('all match their order' if not bad else f'{len(bad)} differ'))
    for b in bad[:5]:
        print(f'    {b}')
    return 1 if bad else 0


# ── 1 · page ────────────────────────────────────────────────────────────────

def section():
    return next(s for s in C.app_info(APP)['sections'] if s['name'] == SECTION)


def step_page():
    s = section()
    page = next((i for i in s['items'] if i['type'] == 1 and i['name'] == PAGE_NAME), None)
    created = not page
    if page:
        print(f'  page {PAGE_NAME!r} exists: {page["id"]}')
    else:
        hap.run('custom-page', 'create', APP, PAGE_NAME, '--section-id', s['id'], '--icon', ICON)
        s = section()
        page = next((i for i in s['items'] if i['type'] == 1 and i['name'] == PAGE_NAME), None)
        if not page:
            sys.exit(f'custom-page create stored no page {PAGE_NAME!r} in {SECTION}')
        print(f'  page {PAGE_NAME!r} created: {page["id"]}')
    remember('page', page['id'])
    order = [i['id'] for i in s['items']]
    want = [i for i in order if i != page['id']]
    want.insert(want.index(next(i['id'] for i in s['items'] if i['name'] == AFTER)) + 1 if AFTER else 0, page['id'])
    if order != want and not created:
        # Placement is the owner's once the page exists: on 23 Sep 2026 a re-run found it out of place and moved it
        # back before this rule existed. Now a misplaced page is reported, and `check` flags it.
        print(f'  NOT moved: the sidebar reads {[i["name"] for i in s["items"]]} — the page is not '
              f'{WHERE}, and a page that exists is placed by the owner')
    elif order != want:
        hap.run('app', 'sort-worksheets', APP, s['id'], *want)
        if [i['id'] for i in section()['items']] != want:
            sys.exit(f'{SECTION}: the order read back as {[i["name"] for i in section()["items"]]}')
        print(f'  moved {WHERE}')
    else:
        print(f'  already {WHERE}')
    if page_info(page['id']).get('version'):
        write_desc(page['id'])
    else:
        print('  no layout stored yet — the description is written once `layout` has saved one')
    return page['id']


def write_desc(pid):
    """The page's description. `updatePage` answers 页面不存在 until the page has a stored layout."""
    if (page_info(pid).get('desc') or '') == PAGE_DESC:
        return
    hap.run('custom-page', 'update-config', pid, '--desc', PAGE_DESC)
    if (page_info(pid).get('desc') or '') != PAGE_DESC:
        sys.exit('the page description did not store')
    print('  description written')


def page_info(page_id):
    from hap_cli.core import page as page_mod
    res = page_mod.get_page(session(), page_id)
    return res.get('data', res) if isinstance(res, dict) and isinstance(res.get('data'), dict) else res


def page_id():
    pid = remembered('page')
    if not pid:
        sys.exit('no page in ids.json — run `page` first')
    return pid


# ── 2 · charts ──────────────────────────────────────────────────────────────

def step_charts():
    waiting = {}
    for name, spec in CHARTS.items():
        missing = missing_controls(spec)
        if missing:
            waiting[name] = missing
            print(f'  {name}: waiting — {spec["ws"]} has no {missing}; nothing written')
            continue
        rid = remembered(name)
        live = get_chart(rid) if rid else None
        if rid and not live:
            sys.exit(f'{name}: ids.json names chart {rid}, which no longer reads — look before rebuilding it')
        if live and not alive(name):
            # The config still reads, but the chart draws nothing (getData status 0, no name): what a page chart
            # became after one layout save left it off the page (23 Sep 2026). Re-saving it does not revive it, so a
            # new chart takes its place, on the same stored condition; the dead id is kept in ids.json as retired and
            # `layout` drops its component.
            remember('retired ' + name, rid)
            print(f'  {name}: chart {rid} no longer draws (getData status 0) — replacing it')
            fid = (live.get('filter') or {}).get('filterId')
            rid, live = None, None
            new = save_chart(name, spec, None, fid)
            remember(name, new)
            print(f'  {name}: created ({new}, filter {fid})')
            continue
        fid = (live.get('filter') or {}).get('filterId') if live else None
        filter_ok = bool(fid) and condition_state(stored_conditions(fid)) == condition_state(conditions(spec))
        chart_ok = bool(live) and chart_state(live) == wanted_state(name, spec)
        if filter_ok and chart_ok:
            print(f'  {name}: as specified ({rid}); nothing saved')
            continue
        if not filter_ok:
            fid = save_filter(spec, fid or '')
        rid = save_chart(name, spec, rid, fid)
        remember(name, rid)
        print(f'  {name}: {"updated" if live else "created"} ({rid}, filter {fid})')
    return waiting


# ── 3 · layout ──────────────────────────────────────────────────────────────

def layout_of(place):
    x, y, w, h = place
    return {'x': x, 'y': y, 'w': w, 'h': h, 'minW': 2, 'minH': 3}


def chart_component(name, spec, existing):
    rid = remembered(name)
    old = existing.get(rid) or {}
    comp = {'type': CHART_COMPONENT, 'value': rid, 'valueExtend': rid, 'worksheetId': ws(spec['ws']),
            'name': name, 'reportType': spec['type'], 'showChartType': 2 if spec.get('horizontal') else 1,
            'config': {'objectId': (old.get('config') or {}).get('objectId') or uuid.uuid4().hex},
            'web': {'title': '', 'titleVisible': False, 'visible': True, 'layout': layout_of(spec['place'])},
            'mobile': {'title': '', 'titleVisible': False, 'visible': True, 'layout': None}}
    if old.get('id'):
        comp['id'] = old['id']
    return comp


def page_filter(chart_comps):
    """The filter group's one filter — Order date, over every placed chart on Orders and Order Lines, each bound
    to its own worksheet's date field."""
    spec = PAGE_FILTER
    c = ctrls(spec['ws'])[spec['control']]
    field = {ws(w): ctrls(w)[n]['controlId'] for w, n in spec['controls'].items()}
    objects = [{'objectId': comp['config']['objectId'], 'type': 1, 'name': comp['name'],
                'worksheetId': comp['worksheetId'], 'controlId': field[comp['worksheetId']]}
               for comp in chart_comps if comp['worksheetId'] in field]
    return {'name': spec['name'], 'global': True, 'dataType': c['type'], 'filterType': DATEENUM,
            'dateRangeType': 3, 'dateRange': 0, 'objectControls': objects, 'controlId': c['controlId'],
            'values': [], 'value': '', 'minValue': '', 'maxValue': '',
            'advancedSetting': {'daterange': FILTER_DATERANGE}}


def filter_state(f):
    return (f.get('name'), f.get('dataType'), f.get('filterType'),     # the top-level controlId is not stored
            sorted((o.get('objectId'), o.get('controlId'), o.get('worksheetId')) for o in f.get('objectControls') or []),
            (f.get('advancedSetting') or {}).get('daterange'))


def filters_group(group_id):
    res = session().api_call('Worksheet', 'GetFiltersGroupByIds', {'filtersGroupIds': [group_id], 'appId': APP})
    data = res.get('data', res) if isinstance(res, dict) else res
    groups = data if isinstance(data, list) else (data or {}).get('data') or []
    return groups[0] if groups else None


def save_filters_group(pid, group_id, flt):
    res = session().api_call('Worksheet', 'SaveFiltersGroup',
                             {'filtersGroupId': group_id or '', 'name': '', 'enableBtn': False, 'appId': APP,
                              'pageId': pid, 'filters': [flt]})
    gid = (res or {}).get('filtersGroupId') or ((res or {}).get('data') or {}).get('filtersGroupId')
    if not gid:
        sys.exit(f'SaveFiltersGroup answered {res!r}')
    remember('page filter', gid)
    back = filters_group(gid)
    got = [filter_state(f) for f in (back or {}).get('filters') or []]
    if got != [filter_state(flt)]:
        sys.exit(f'the page filter group {gid} read back as {got}, wanted {[filter_state(flt)]}')
    return gid


def component_state(comp):
    lay = (comp.get('web') or {}).get('layout') or {}
    return (comp.get('type'), comp.get('value'), (comp.get('config') or {}).get('objectId'),
            tuple(lay.get(k) for k in ('x', 'y', 'w', 'h')), bool((comp.get('web') or {}).get('titleVisible')))


def step_layout():
    pid = page_id()
    info = page_info(pid)
    live = info.get('components') or []
    existing = {c.get('value'): c for c in live if c.get('type') == CHART_COMPONENT}
    placed = [n for n in CHARTS if remembered(n)]
    unread = [n for n in placed if not get_chart(remembered(n))]
    if unread:                                   # never save a page that silently drops a chart
        sys.exit(f'{unread} did not read back; the layout is not saved')
    charts = [chart_component(n, CHARTS[n], existing) for n in placed]
    known = {remembered(n) for n in CHARTS}
    foreign = [c for c in live if c.get('type') not in (CHART_COMPONENT, FILTER_COMPONENT)
               or (c.get('type') == CHART_COMPONENT and c.get('value') not in known | retired())]
    if foreign:
        print(f'  keeping {len(foreign)} component(s) this script does not own, where they are: '
              f'{[(c.get("type"), c.get("name") or c.get("value")) for c in foreign]}')
    old_filter = next((c for c in live if c.get('type') == FILTER_COMPONENT), None)
    flt = page_filter(charts)
    # The group id is remembered the moment it is minted: until the layout saves, the page does not reference it,
    # and a run that stopped between the two would otherwise mint another (two were orphaned that way, 23 Sep 2026).
    gid = (old_filter or {}).get('value') or remembered('page filter')
    group = filters_group(gid) if gid else None
    if not group or [filter_state(f) for f in group.get('filters') or []] != [filter_state(flt)]:
        gid = save_filters_group(pid, gid, flt)
        print(f'  page filter {PAGE_FILTER["name"]!r} over {len(flt["objectControls"])} charts saved ({gid})')
    remember('page filter', gid)
    fcomp = {'type': FILTER_COMPONENT, 'value': gid,
             'web': {'title': '', 'titleVisible': False, 'visible': True, 'layout': layout_of(PAGE_FILTER['place'])},
             'mobile': {'title': '', 'titleVisible': False, 'visible': True, 'layout': None}}
    if (old_filter or {}).get('id'):
        fcomp['id'] = old_filter['id']
    want = [fcomp] + charts + foreign
    if sorted(map(component_state, live)) == sorted(map(component_state, want)):
        print(f'  layout: {len(charts)} charts and the filter already placed; nothing saved')
        write_desc(pid)
        return
    hap.backup('dashboard_page_pre_layout', info)
    from hap_cli.core import page as page_mod
    cfg = dict(info.get('config') or {})
    cfg.setdefault('webNewCols', 48)
    res = page_mod.save_page(session(), pid, version=info.get('version') or 0, components=want,
                             adjust_screen=bool(info.get('adjustScreen')), config=cfg)
    back = page_info(pid)
    if sorted(map(component_state, back.get('components') or [])) != sorted(map(component_state, want)):
        sys.exit(f'the page layout read back differently (save answered {res!r})')
    print(f'  layout saved: the filter and {len(charts)} charts (version {back.get("version")})')
    write_desc(pid)


# ── check: the spec, then the figures ───────────────────────────────────────

def step_check():
    problems = []
    pid = page_id()
    s = section()
    names = [i['name'] for i in s['items']]
    print(f'  sidebar {SECTION}: {names}')
    if PAGE_NAME not in names or names.index(PAGE_NAME) != (names.index(AFTER) + 1 if AFTER else 0):
        problems.append(f'{PAGE_NAME} is not {WHERE}')
    info = page_info(pid)
    comps = {c.get('value'): c for c in info.get('components') or []}
    for name, spec in CHARTS.items():
        rid = remembered(name)
        missing = missing_controls(spec)
        if missing:
            print(f'  {name}: waiting on {spec["ws"]} {missing}')
            continue
        live = get_chart(rid) if rid else None
        if not live:
            problems.append(f'{name}: not built')
            continue
        if chart_state(live) != wanted_state(name, spec):
            problems.append(f'{name}: config differs from the spec')
        if not alive(name):
            problems.append(f'{name}: the chart draws nothing (getData status 0) — run `charts`')
        fid = (live.get('filter') or {}).get('filterId')
        if condition_state(stored_conditions(fid)) != condition_state(conditions(spec)):
            problems.append(f'{name}: stored conditions differ from the spec')
        comp = comps.get(rid)
        if not comp:
            problems.append(f'{name}: not on the page')
        elif component_state(comp)[3] != tuple(spec['place']):
            problems.append(f'{name}: placed at {component_state(comp)[3]}, the spec says {spec["place"]}')
    gid = remembered('page filter')
    group = filters_group(gid) if gid else None
    by_object = {(c.get('config') or {}).get('objectId'): c.get('value') for c in comps.values()}
    by_report = {remembered(n): n for n in CHARTS}
    bound = sorted(by_report.get(by_object.get(o.get('objectId')), str(o.get('objectId')))
                   for f in (group or {}).get('filters') or [] for o in f.get('objectControls') or [])
    want_bound = sorted(n for n, sp in CHARTS.items() if sp['ws'] in PAGE_FILTER['controls'] and remembered(n))
    if bound != want_bound:
        problems.append(f'the page filter binds {bound}, wanted {want_bound}')
    print(f'  page filter {PAGE_FILTER["name"]!r} binds: {bound}')
    print('\n── figures: what each chart draws against the records ' + '─' * 14)
    problems += figures()
    print('\n' + ('check: all agree' if not problems else 'check: PROBLEMS\n  ' + '\n  '.join(problems)))
    return 1 if problems else 0


def chart_data(name, filters=None):
    res = session().report_call('report/getData', {'reportId': remembered(name), 'pageId': page_id(),
                                                   'version': '6.5', 'reload': True, 'filters': filters or []})
    return res.get('data', res) if isinstance(res, dict) and isinstance(res.get('data'), dict) else res


def drawn(name, filters=None):
    """{series controlId: {x label: value}} of what a chart draws, from getData. Series are keyed by control, not by
    `key`: a number chart's `key` is the control's own name, not the label the chart shows."""
    d = chart_data(name, filters)
    vmap = next(iter((d.get('valueMap') or {}).values()), {}) if d.get('valueMap') else {}
    out = {}
    for series in d.get('map') or []:
        out[series.get('c_id')] = {vmap.get(p.get('x'), p.get('x')): round(float(p.get('v') or 0), 2)
                                   for p in series.get('value') or []}
    return out, d


def all_rows(name):
    """demo.all_rows, in parallel and with retries: GetRowDetail is the complete read, but on 23 Sep 2026 one call
    in ten stalled for 25 s or more, and a serial read of ~180 records ran past ten minutes."""
    import demo
    from concurrent.futures import ThreadPoolExecutor

    def one(rowid):
        for attempt in range(4):
            try:
                res = session().api_call('Worksheet', 'GetRowDetail', {'worksheetId': ws(name), 'rowId': rowid},
                                         timeout=15)
                return rowid, json.loads(res['rowData'])
            except Exception as e:
                last = e
        raise RuntimeError(f'GetRowDetail {name}/{rowid}: {last}')
    with ThreadPoolExecutor(8) as pool:
        return dict(pool.map(one, demo.rowid_list(name)))


def figures():
    """Compute every figure from the records and set it beside what the chart draws."""
    import demo
    problems = []
    orders = {k: demo.order_state(d) | {'salesperson': salesperson(d)} for k, d in all_rows('Orders').items()}
    real = [o for o in orders.values() if o['is_template'] == '0']
    confirmed = [o for o in orders.values() if o['status'] == CONFIRMED]
    today = datetime.date.today()
    start = (today.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
    for _ in range(10):
        start = (start - datetime.timedelta(days=1)).replace(day=1)
    by_month = defaultdict(float)
    for o in confirmed:
        if start.isoformat() <= o['date'][:10] <= today.isoformat():
            by_month[o['date'][:7]] += o['untaxed']
    line_rows = all_rows('Order Lines')
    lines = [demo.order_line_state(d) for d in line_rows.values()]
    by_product = defaultdict(float)
    names = product_names()
    for l in lines:
        if l['kind'] == 'Product' and orders.get(l['order'], {}).get('status') == CONFIRMED:
            by_product[names.get(l['product'], l['product'])] += l['subtotal']
    open_q = [o for o in real if o['status'] in OPEN]
    expect = {
        'Confirmed sales': {'Untaxed amount': total(confirmed)},
        'Open quotations': {'Quotations': len(open_q)},
        'Value of open quotations': {'Untaxed amount': total(open_q)},
        'Orders to invoice': {'Orders': sum(1 for o in orders.values() if o['invoice_status'] == 'To Invoice')},
        'Monthly sales': {k: round(v, 2) for k, v in sorted(by_month.items())},
        'Quotations and orders by status': dict(Counter(o['status'] for o in real)),
        'Top customers': top(by_key(confirmed, 'customer')),
        'Sales by salesperson': by_key(confirmed, 'salesperson'),
        'Sales orders by invoicing status': dict(Counter(o['invoice_status'] for o in confirmed)),
        'Top products': top(by_product),
    }
    invoice_figures(expect, today)
    for name, want in expect.items():
        if not remembered(name) or missing_controls(CHARTS[name]):
            continue
        got, raw = drawn(name)
        flat = flatten(got, CHARTS[name])
        ok = compare(flat, want)
        print(f'  {name}: ' + ('agrees' if ok else 'DIFFERS'))
        for k in sorted(set(want) | set(flat), key=str):
            print(f'      {str(k):<34} chart {fmt(flat.get(k)):>14}   records {fmt(want.get(k)):>14}')
        if not ok:
            problems.append(f'{name}: chart {flat} against records {want}')
    problems += page_filter_figures(orders, today, line_rows, names)
    return problems


LAST_MONTH = 8                                        # the page filter's "last month" preset (DATE_OPTIONS)


def page_filter_figures(orders, today, line_rows, names):
    """The page filter at work: the condition the page sends a bound chart when someone picks *Last month*
    (pd-openweb customPage filter `formatFiltersGroup`), passed to getData the same way, against the records."""
    first = today.replace(day=1)
    last = (first - datetime.timedelta(days=1)).replace(day=1)
    month = [o for o in orders.values() if last.isoformat() <= o['date'][:10] < first.isoformat()]
    c = ctrls('Orders')['Quotation/Order Date']
    flt = [[{'controlId': c['controlId'], 'dataType': c['type'], 'filterType': DATEENUM, 'dateRange': LAST_MONTH,
             'dateRangeType': 3, 'value': '', 'values': [], 'minValue': '', 'maxValue': '', 'spliceType': 1}]]
    want = {'Confirmed sales': {'Untaxed amount': total([o for o in month if o['status'] == CONFIRMED])},
            'Quotations and orders by status': dict(Counter(o['status'] for o in month if o['is_template'] == '0'))}
    # Top products filters on its own lines' Order Date lookup, so the records side reads that lookup too. Lines
    # older than the lookup hold it empty (until the reseed), so the order's own date is shown beside it.
    import demo
    fl = ctrls('Order Lines')
    lc = fl['Order Date']
    line_flt = [[dict(flt[0][0], controlId=lc['controlId'])]]
    by_lookup, by_order = defaultdict(float), defaultdict(float)
    for d in line_rows.values():
        l = demo.order_line_state(d)
        if l['kind'] != 'Product' or orders.get(l['order'], {}).get('status') != CONFIRMED:
            continue
        name = names.get(l['product'], l['product'])
        if last.isoformat() <= demo.t(d, fl, 'Order Date')[:10] < first.isoformat():
            by_lookup[name] += l['subtotal']
        if last.isoformat() <= orders[l['order']]['date'][:10] < first.isoformat():
            by_order[name] += l['subtotal']
    want['Top products'] = top({k: round(v, 2) for k, v in by_lookup.items()})
    held = sum(1 for d in line_rows.values() if demo.t(d, fl, 'Order Date'))
    print(f'\n── the page filter set to Last month ({last:%B %Y}) ' + '─' * 30)
    problems = []
    for name, expected in want.items():
        got, _ = drawn(name, line_flt if CHARTS[name]['ws'] == 'Order Lines' else flt)
        flat = flatten(got, CHARTS[name])
        ok = compare(flat, expected)
        print(f'  {name}: ' + ('agrees' if ok else 'DIFFERS'))
        for k in sorted(set(expected) | set(flat), key=str):
            print(f'      {str(k):<34} chart {fmt(flat.get(k)):>14}   records {fmt(expected.get(k)):>14}')
        if not ok:
            problems.append(f'{name} under the page filter: chart {flat} against records {expected}')
    print(f'      Order Lines holding an Order Date: {held} of {len(line_rows)}; by the order\'s own date, Top products '
          f'for {last:%B} would read {len(by_order)} products, RM {sum(by_order.values()):,.2f} (after the reseed)')
    return problems


def invoice_figures(expect, today):
    import demo
    f = ctrls('Invoices')
    if not missing_controls(CHARTS['Overdue invoices']) or not missing_controls(CHARTS['Received this month']):
        rows = all_rows('Invoices')
    if not missing_controls(CHARTS['Overdue invoices']):
        due = [d for d in rows.values()
               if demo.opt(d, f, 'Status') == 'Posted' and demo.opt(d, f, 'Type') == 'Customer Invoice'
               and demo.dateonly(d, f, 'Due Date') and demo.dateonly(d, f, 'Due Date') < today.isoformat()
               and demo.opt(d, f, 'Payment Status') != 'Paid']
        expect['Overdue invoices'] = {'Invoices': len(due)}
        expect['Amount overdue'] = {'Amount due': round(sum(demo.n(d, f, 'Amount Due') for d in due), 2)}
    if not missing_controls(CHARTS['Received this month']):
        month = today.isoformat()[:7]
        paid = [d for d in rows.values() if demo.opt(d, f, 'Type') == 'Customer Invoice'
                and demo.dateonly(d, f, 'Last Payment Date')[:7] == month]
        expect['Received this month'] = {'Amount received': round(sum(demo.n(d, f, 'Amount Paid') for d in paid), 2)}


def salesperson(d):
    import demo
    v = demo.raw(d, ctrls('Orders'), 'Salesperson')
    items = demo._items(v)
    return (items[0].get('fullname') or items[0].get('fullName') or '') if items else ''


def product_names():
    rows = C.records(ws('Product Variants'), APP)
    title = next(c for c in hap.controls(ws('Product Variants')) if c.get('attribute') == 1)['controlId']
    return {r['rowid']: r.get(title) for r in rows}


def total(orders):
    return round(sum(o['untaxed'] for o in orders), 2)


def by_key(orders, key):
    out = defaultdict(float)
    for o in orders:
        out[o[key]] += o['untaxed']
    return {k: round(v, 2) for k, v in out.items()}


def top(d, n=10):
    return dict(sorted(d.items(), key=lambda kv: -kv[1])[:n])


def flatten(got, spec):
    """A number chart's series by its label; any other chart's points by their x label."""
    if spec['type'] == NUMBER:
        labels = {('record_count' if n == 'count' else ctrls(spec['ws'])[n]['controlId']): label
                  for n, _, label in spec['y']}
        # A number chart with no matching record returns no series at all; it reads 0.
        return {label: next(iter(got.get(cid, {}).values()), 0) for cid, label in labels.items()}
    series = next(iter(got.values()), {})
    if spec.get('grain') == MONTH:
        return {month_key(k): v for k, v in series.items()}
    return series


def month_key(label):
    """'2026/09' / '2026-09' / '2026年9月' → '2026-09'."""
    digits = ''.join(ch if ch.isdigit() else ' ' for ch in str(label)).split()
    return f'{digits[0]}-{int(digits[1]):02d}' if len(digits) >= 2 else str(label)


def compare(got, want):
    if set(got) != set(want):
        return False
    return all(abs(float(got[k]) - float(want[k])) < 0.005 for k in want)


def fmt(v):
    return '—' if v is None else (f'{v:,.2f}' if isinstance(v, float) else str(v))


def step_data(name):
    got, raw = drawn(name)
    print(json.dumps(raw, ensure_ascii=False, indent=1)[:6000])
    print(json.dumps(got, ensure_ascii=False, indent=1))


def step_all():
    step_page()
    waiting = step_charts()
    step_layout()
    if waiting:
        print(f'\n  waiting: {waiting}')
    return step_check()


STEPS = {'page': step_page, 'charts': step_charts, 'layout': step_layout, 'check': step_check, 'data': step_data,
         'lookups': step_lookups,
         'all': step_all}

if __name__ == '__main__':
    step = sys.argv[1] if len(sys.argv) > 1 else 'check'
    if step not in STEPS:
        raise SystemExit(f"Unknown step {step!r}; choose from {', '.join(STEPS)}")
    result = STEPS[step](*sys.argv[2:])
    sys.exit(result if isinstance(result, int) else 0)
