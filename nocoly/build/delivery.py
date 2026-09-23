"""Orders' Delivery Status, computed from the order lines (worksheets/16-orders.md › *Delivery status*).

Odoo computes `delivery_status` in `sale_stock` from the order's stock pickings. There are no pickings in this
app, so the figure is computed from the lines' own quantities instead (owner, 23 Sep 2026; DECISIONS.md):

    Status is not Sales Order                               -> Nothing to Deliver
    a Sales Order with no goods line                        -> Nothing to Deliver
    every goods line's Quantity Delivered >= Quantity       -> Fully Delivered
    some goods line has Quantity Delivered > 0              -> Partially Delivered
    otherwise                                               -> Not Delivered

A **goods line** is a product line whose product's Product Type is Goods (owner, 23 Sep 2026). Services, combos
and the Discount product never hold a delivery up — in Odoo only storable goods get a picking.

Over-delivery on one line never makes up for another line left undelivered: each line's shortfall is clamped at
zero before it is summed (Left to Deliver). Odoo's `started` state needs a picking and stays out.

It is the Invoice Status mechanism of o2i.py step `status`, reused: two hidden 汇总 on Orders, and three workflows
— the order's own Status, a line created or changed, a line deleted — that fetch the order as it now stands, read
the roll-ups through number formula steps and write one of the four options.

Steps, in order — each reads live state first, saves nothing when re-run, and reads back every write:

    ~/.hap-venv/bin/python nocoly/build/delivery.py helper     # 1 Left to Deliver clamped at zero, alias qty_to_deliver
    ~/.hap-venv/bin/python nocoly/build/delivery.py rollups    # 2 the two hidden 汇总 on Orders
    ~/.hap-venv/bin/python nocoly/build/delivery.py workflows  # 3 the three workflows, published; the owner's draft retired
    ~/.hap-venv/bin/python nocoly/build/delivery.py backfill   # 4 every existing order's Delivery Status from its lines
    ~/.hap-venv/bin/python nocoly/build/delivery.py selfcheck  # 5 the CLI drive on three TEST orders
    ~/.hap-venv/bin/python nocoly/build/delivery.py check      # read-only: controls, workflows, every order agrees
"""
import json, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import common as C
import hap
import o2i
from o2i import (APP, ORDERS, OLINES, NAME, DROPDOWN, NUMBER, RELATION, TEXT, ROLLUP, FUNCTION,
                 O_SUBTABLE, OL_DISPLAY_TYPE, OL_QUANTITY, OL_QTY_DELIVERED, OL_DESCRIPTION,
                 EQ_SINGLE, GT_NUMBER, GET_ONE, FROM_SHEET_ONE, EQ_C, GTE_C, IS_ANY_OF, NOT_EMPTY_C,
                 CREATE_OR_UPDATE, DELETE_EVENT,
                 fields, option_key, flt, function_source, function_expression, ensure_rollups, filter_state,
                 nodes_by_name, read_node, sync_trigger, sync_number_formula, cond, fx_cond, wf_filter_state,
                 option_values, save_path, paths_of, patch, set_entries, published_status, cell_labels, numeric)

SALES_APP = '3e596740-d096-42cd-b948-0b62a0220927'  # the brownfield Sales app — never written
ORG = o2i.ORG
DELIVERY_STATUS = '6ab0a9dabd43f55762c78048'          # Orders / Delivery Status, type 11, perm 100
OPTIONS = ('Nothing to Deliver', 'Not Delivered', 'Partially Delivered', 'Fully Delivered')

# ── 1 · the owner's helper on Order Lines ───────────────────────────────────

LEFT = 'Left to Deliver'                             # the owner's control, hidden, a function formula
LEFT_ID = '6ab380817d58b0f4498fde44'
LEFT_ALIAS = 'qty_to_deliver'

# Goods only (owner, 23 Sep 2026). Product Type reaches the line through the variant, whose own Product Type is a
# stored lookup of Products'. It must be **stored** here too ("00"): a display lookup ("10") is invisible to a
# server-side function formula — it read empty whatever the comparison — while a stored lookup of a dropdown
# renders as its label, as Order Status does for Invoice Status.
PRODUCT_TYPE = 'Product Type'                        # Order Lines, stored lookup, hidden
PRODUCT_TYPE_ID = '6ab39f1ee54d2a34faaab141'
VARIANT_PRODUCT_TYPE = '6aa90c9f4a22ad87b728e9f9'    # Product Variants / Product Type (lookup of Products')
OL_PRODUCT = '6ab0c864e43d174ab37535f8'
GOODS_KEY = '10ef80e0-9f19-4bca-b61d-6bdaee85f238'   # Products / Product Type = Goods
GOODS_FLAG = 'Goods line'                            # 1 on a product line of goods, else 0
GOODS_DELIVERED = 'Goods line delivered'             # 1 on a goods line with anything delivered, else 0


def blank_as_zero(ref):
    return f'IF(CONCAT({ref}, "") == "", 0, {ref})'


def goods_expression():
    return f'IF(${OL_DISPLAY_TYPE}$ == "Product" && ${PRODUCT_TYPE_ID}$ == "Goods", 1, 0)'


def goods_delivered_expression(lf):
    d = f'${OL_QTY_DELIVERED}$'
    return f"IF(${lf[GOODS_FLAG]['controlId']}$ == 1 && {blank_as_zero(d)} > 0, 1, 0)"


def left_expression(lf=None):
    """A product line's shortfall, never below zero — so an over-delivered line cannot cancel another line's
    shortfall in the order's sum. Sections, subsections and notes carry 0. A dropdown renders its label inside a
    worksheet function formula (BUILDING.md › Formulas and lookups).

    **A Quantity Delivered never written is empty, not 0**, and `Quantity − <empty>` computes empty: 15 of the
    142 lines stored nothing under the plain `MAX(0, Quantity − Quantity Delivered)` (23 Sep 2026). The empty
    value is caught as text — `CONCAT(x, "") == ""` — and taken as 0."""
    q, d = f'${OL_QUANTITY}$', f'${OL_QTY_DELIVERED}$'
    lf = lf or fields(OLINES)
    return (f"IF(${lf[GOODS_FLAG]['controlId']}$ == 1, "
            f'MAX(0, {q}-{blank_as_zero(d)}), 0)')


def left_spec(lf=None):
    return {'type': FUNCTION, 'alias': LEFT_ALIAS, 'desc': '', 'fieldPermission': '011', 'enumDefault2': 6,
            'dot': 2, 'dataSource': function_source(left_expression(lf))}


def ensure_goods(lf):
    """The stored Product Type lookup and the two goods flags on Order Lines. Returns the live controls."""
    if PRODUCT_TYPE not in lf:
        c = C.control('SHEET_FIELD', PRODUCT_TYPE, (9999, 0, 6), alias='product_type', hint='', desc='',
                      data_source=OL_PRODUCT, source_control_id=VARIANT_PRODUCT_TYPE, extra={'dot': 0})
        c.update(fieldPermission='011', dataSource=f'${OL_PRODUCT}$', strDefault='00')
        lf = C.append_checked(OLINES, [c], 'delivery_olines_pre_product_type', 'goods/lookup')
    if lf[PRODUCT_TYPE].get('strDefault') != '00':
        C.pinned_write(OLINES, {lf[PRODUCT_TYPE]['controlId']: {'strDefault': '00'}},
                       'delivery_olines_pre_pt_stored', 'goods/lookup stored')
        lf = fields(OLINES)
    for name, expr in ((GOODS_FLAG, lambda: goods_expression()),
                       (GOODS_DELIVERED, lambda: goods_delivered_expression(lf))):
        if name not in lf:
            c = C.control('FORMULA_FUNC', name, (9999, 0, 6), alias='', hint='', desc='',
                          advanced_setting={'analysislink': '1', 'sorttype': 'en'},
                          extra={'enumDefault2': 6, 'dot': 0, 'dataSource': function_source(expr())})
            c['fieldPermission'] = '011'
            lf = C.append_checked(OLINES, [c], f'delivery_olines_pre_{name.replace(" ", "_").lower()}', f'goods/{name}')
        if function_expression(lf[name]) != expr():
            C.pinned_write(OLINES, {lf[name]['controlId']: {'dataSource': function_source(expr())}},
                           f'delivery_olines_pre_{name.replace(" ", "_").lower()}_fx', f'goods/{name} formula')
            lf = fields(OLINES)
        C.remember('controls', f'Order Lines: {name}', lf[name]['controlId'])
    C.remember('controls', f'Order Lines: {PRODUCT_TYPE}', lf[PRODUCT_TYPE]['controlId'])
    return lf


# ── 2 · the two roll-ups on Orders ──────────────────────────────────────────

LEFT_SUM = 'Units left to deliver'                   # Σ Left to Deliver (goods lines only)
DELIVERED_COUNT = 'Product lines with deliveries'    # goods lines whose Quantity Delivered > 0 (the name predates
                                                     # goods-only; kept, as ids.json and the workflows name it)
GOODS_SUM = 'Goods lines'                            # how many goods lines — the workflows' "anything to deliver"
ROLLUPS = (LEFT_SUM, DELIVERED_COUNT, GOODS_SUM)
HIDDEN = '011'
# `append_controls` parks a new control at row 9999 and only a full save places one, so placement is the
# owner's. Both are hidden working figures: (row, col, size, where).
PLACE = {
    LEFT_SUM: (9999, 0, 6, 'hidden — a working figure, beside Product lines'),
    DELIVERED_COUNT: (9999, 0, 6, 'hidden — a working figure, beside Product lines'),
    GOODS_SUM: (9999, 0, 6, 'hidden — a working figure, beside Product lines'),
}


def register_rollups():
    """o2i.ensure_rollups reads a roll-up's place, alias, description and permission from o2i's own tables; the
    two controls of this bundle are entered there, keyed by name, before it is called."""
    for name in ROLLUPS:
        o2i.PLACE[name] = PLACE[name]
        o2i.ALIAS[name] = ''
        o2i.DESC[name] = ''
        o2i.PERM[name] = HIDDEN
        o2i.WHERE[name] = ORDERS


register_rollups()


def rollups_wanted():
    """Unfiltered sums of the line flags: the goods test lives on the line, where a stored lookup can see it."""
    lf = fields(OLINES)
    return {
        LEFT_SUM: (O_SUBTABLE, LEFT_ID, 5, [], 2),                                    # 5 = sum
        DELIVERED_COUNT: (O_SUBTABLE, lf[GOODS_DELIVERED]['controlId'], 5, [], 0),
        GOODS_SUM: (O_SUBTABLE, lf[GOODS_FLAG]['controlId'], 5, [], 0),
    }


# ── 3 · the workflows ───────────────────────────────────────────────────────

WF_SELF = "Orders: Delivery Status follows the order's own Status"
WF_LINES = 'Orders: Delivery Status follows its lines'
WF_DELETE = 'Orders: Delivery Status when a line is deleted'
WORKFLOWS = (WF_SELF, WF_LINES, WF_DELETE)
DRIVER = {WF_SELF: ORDERS, WF_LINES: OLINES, WF_DELETE: OLINES}
EVENT = {WF_SELF: 'create_or_update', WF_LINES: 'create_or_update', WF_DELETE: 'delete'}
TRIGGER_NAME = {
    WF_SELF: 'When an order is created or its Status changes',
    WF_LINES: 'When an order line is created or changed',
    WF_DELETE: 'When an order line is deleted',
}
WF_DESC = ("Keeps the order's Delivery Status in step with its lines: Nothing to Deliver unless the order is "
           "confirmed and has product lines; Fully Delivered once every product line is delivered in full; "
           "Partially Delivered once anything is delivered; otherwise Not Delivered.")

GUARD_BRANCH = 'Does the line belong to an order?'
GET_ORDER = 'Get the order as it now stands'
N_PROD_STEP = 'How many product lines'
LEFT_STEP = 'Units still to deliver'
N_DELIVERED_STEP = 'Product lines with anything delivered'
WHICH_BRANCH = 'Which Delivery Status?'
SET_FULL = 'Set Fully Delivered'
SET_PARTIAL = 'Set Partially Delivered'
SET_NOT = 'Set Not Delivered'
SET_NOTHING = 'Set Nothing to Deliver'
PATH_FULL = 'Every product line is delivered in full'
PATH_PARTIAL = 'Something is delivered'
PATH_NOT = 'Nothing is delivered yet'
PATH_NOTHING = 'Otherwise'
SET_LABEL = {SET_FULL: 'Fully Delivered', SET_PARTIAL: 'Partially Delivered', SET_NOT: 'Not Delivered',
             SET_NOTHING: 'Nothing to Deliver'}
PATHS = ((PATH_FULL, SET_FULL), (PATH_PARTIAL, SET_PARTIAL), (PATH_NOT, SET_NOT), (PATH_NOTHING, SET_NOTHING))

OWNERS_DRAFT = '6ab37f39a2c872a5c1474896'           # the owner's "Set Delivery Status", never published
OWNERS_DRAFT_NAME = 'Set Delivery Status'
RETIRED_NAME = 'ZZ obsolete – Set Delivery Status'


# ── guard ───────────────────────────────────────────────────────────────────

def guard():
    """The app is the one ids.json names and still carries one of its names; Orders and Order Lines are where
    ids.json says; nothing here is the Sales app."""
    ids = hap.ids()
    if ids.get('app') != APP or APP == SALES_APP:
        sys.exit(f'ids.json holds app {ids.get("app")}, this script is written for {APP}')
    app = hap.run('app', 'info', '-a', APP).get('data', {})
    if app.get('name') not in hap.APP_NAMES:
        sys.exit(f'app {APP} is named {app.get("name")!r}, expected one of {hap.APP_NAMES}')
    for ws in (ORDERS, OLINES):
        if ids['worksheets'].get(NAME[ws]) != ws:
            sys.exit(f'ids.json holds {NAME[ws]} = {ids["worksheets"].get(NAME[ws])}, wanted {ws}')
    of, lf = fields(ORDERS), fields(OLINES)
    ds = next((c for c in of.values() if c['controlId'] == DELIVERY_STATUS), None)
    if not ds or ds['controlName'] != 'Delivery Status' or ds['type'] != DROPDOWN:
        sys.exit(f'Orders / Delivery Status is not {DELIVERY_STATUS} (type 11) any more — read the worksheet')
    labels = [o['value'] for o in ds.get('options') or [] if not o.get('isDeleted')]
    if sorted(labels) != sorted(OPTIONS):
        sys.exit(f'Delivery Status offers {labels}, this script is written for {list(OPTIONS)}')
    left = lf.get(LEFT)
    if not left or left['controlId'] != LEFT_ID:
        sys.exit(f'Order Lines / {LEFT} is not {LEFT_ID} any more — read the worksheet')
    return of, lf


# ── 1 · helper ──────────────────────────────────────────────────────────────

def step_helper():
    """The goods lookup and flags, then Left to Deliver: a goods line's shortfall clamped at zero, alias
    `qty_to_deliver`."""
    of, lf = guard()
    lf = ensure_goods(lf)
    clash = [c['controlName'] for c in lf.values() if c.get('alias') == LEFT_ALIAS and c['controlId'] != LEFT_ID]
    spec = left_spec(lf)
    if clash:
        print(f'  alias {LEFT_ALIAS!r} is taken by {clash}; Left to Deliver keeps no alias')
        spec['alias'] = lf[LEFT].get('alias') or ''
    before = function_expression(lf[LEFT])
    if C.pinned_write(OLINES, {LEFT_ID: spec}, 'delivery_orderlines_pre_helper', 'helper'):
        print(f'  {LEFT} expression:\n      was {before}\n      now {left_expression(lf)}')
        time.sleep(8)
    c = fields(OLINES)[LEFT]
    print(f"  OK  Order Lines / {LEFT} {c['controlId']} t{c['type']} alias={c.get('alias')!r} "
          f"perm={c.get('fieldPermission')} dot={c.get('dot')}\n          {function_expression(c)}")
    C.remember('controls', 'Order Lines: ' + LEFT, LEFT_ID)
    prove_helper()


def line_rows():
    """Every order line with the three inputs, from the listing **and** `record get` (CLAUDE.md: neither read
    path is complete). Returns {rowid: {...}} and the list of lines where the two disagree."""
    lf = fields(OLINES)
    listed = {r['rowid']: r for r in C.records(OLINES, APP)}
    out, disagree = {}, []
    for rowid, r in listed.items():
        d = o2i.read_record(OLINES, rowid)
        got = {}
        for name, alias in (('Orders', 'order_id'), ('Display Type', 'display_type'),
                            ('Quantity', 'product_uom_qty'), ('Quantity Delivered', 'qty_delivered')):
            a, b = r.get(lf[name]['controlId']), d.get(alias)
            if name == 'Orders':
                a = [x.get('sid') for x in (json.loads(a) if isinstance(a, str) and a.startswith('[') else a) or []]
                b = [x.get('sid') for x in (json.loads(b) if isinstance(b, str) and b.startswith('[') else b) or []]
            elif name == 'Display Type':
                a, b = cell_labels(a), cell_labels(b)
            else:
                a, b = numeric(a), numeric(b)
            if a != b and not (a in (None, 0.0) and b in (None, 0.0)):
                disagree.append((rowid, name, a, b))
            got[name] = b if b not in (None, [], '') else a
        pt = d.get('product_type') if d.get('product_type') is not None else d.get(PRODUCT_TYPE_ID)
        got['Goods'] = got['Display Type'] == ['Product'] and (GOODS_KEY in str(pt) or 'Goods' in cell_labels(pt))
        got['Left'] = numeric(d.get(LEFT_ALIAS) if d.get(LEFT_ALIAS) is not None else d.get(LEFT_ID))
        got['Description'] = r.get(OL_DESCRIPTION)
        out[rowid] = got
    return out, disagree


def expected_left(line):
    if not line['Goods']:
        return 0.0
    return max(0.0, round((line['Quantity'] or 0) - (line['Quantity Delivered'] or 0), 2))


def prove_helper(lines=None):
    """Every line's stored Left to Deliver equals the clamped shortfall worked out here from its own inputs."""
    lines = lines or line_rows()[0]
    wrong = [(r, l['Description'], l['Left'], expected_left(l)) for r, l in lines.items()
             if l['Left'] != expected_left(l)]
    over = sum(1 for l in lines.values() if l['Goods']
               and (l['Quantity Delivered'] or 0) > (l['Quantity'] or 0))
    print(f'  {LEFT}: {len(lines) - len(wrong)} of {len(lines)} lines store the clamped shortfall '
          f'({over} over-delivered product line(s) read 0)')
    for w in wrong[:15]:
        print(f'    DIFFERS {w[0]} {str(w[1])[:40]!r}: stores {w[2]!r}, wanted {w[3]!r}')
    return wrong


# ── 2 · rollups ─────────────────────────────────────────────────────────────

def step_rollups():
    of, lf = guard()
    live = ensure_rollups(ORDERS, rollups_wanted(), 'delivery_orders_pre_rollups', 'rollups')
    nudge_rollups(live)
    o2i.report_parked(list(ROLLUPS), live)


def rollup_problems(of):
    """Orders whose two roll-ups do not hold what their lines say, as (Number, stored, worked out here)."""
    lines, _ = line_rows()
    grouped = by_order(lines)
    out = []
    for rowid, o in order_rows(of).items():
        product = [l for l in grouped.get(rowid, []) if l['Goods']]
        want = (round(sum(expected_left(l) for l in product), 2),
                sum(1 for l in product if (l['Quantity Delivered'] or 0) > 0))
        got = o['rollups'][1:]
        if tuple(numeric(x) for x in got) != tuple(float(x) for x in want):
            out.append((o['Number'], got, want))
    return out


def nudge_rollups(of):
    """**Both 汇总 were appended blank on every one of the 46 existing orders** — `record get` and GetRowDetail
    alike, after a minute (23 Sep 2026; BUILDING.md › *A 汇总 or Formula appended … was blank*). A definition
    change recomputes a 汇总 on every record (BUILDING.md, *# Variants*), so each one's filter is saved away and
    back — two version-pinned saves of these two controls only — and the result compared with the lines."""
    wrong = rollup_problems(of)
    if not wrong:
        print(f'  both roll-ups hold what the lines say on every order; nothing nudged')
        return False
    print(f'  {len(wrong)} order(s) whose roll-ups differ from their lines, e.g. {wrong[:3]} — forcing a recompute')
    wanted = rollups_wanted()
    ids = {n: of[n]['controlId'] for n in ROLLUPS}
    C.pinned_write(ORDERS, {ids[n]: {'advancedSetting.filters': ''} for n in ROLLUPS},
                   'delivery_orders_pre_nudge', 'rollups/nudge')
    C.pinned_write(ORDERS, {ids[n]: {'advancedSetting.filters': o2i.filters_json(wanted[n][3])} for n in ROLLUPS},
                   'delivery_orders_pre_nudge', 'rollups/restore')
    for _ in range(10):
        time.sleep(6)
        wrong = rollup_problems(of)
        if not wrong:
            print('  both roll-ups now hold what the lines say on every order')
            return True
    sys.exit(f'{len(wrong)} order(s) still differ after the recompute: {wrong[:10]}')


# ── 3 · workflows ───────────────────────────────────────────────────────────

def find_workflow(name):
    """By ids.json, then by name over **every** workflow of the app (79 on 23 Sep 2026 — `workflow list`
    answers 50 unless asked for more)."""
    pid = hap.ids().get('workflows', {}).get(name)
    if pid:
        return pid
    live = [w for w in hap.listing('workflow', 'list', APP, '-n', '500') if w['name'] == name]
    if len(live) > 1:
        sys.exit(f'{len(live)} workflows are named {name!r}: {[w["id"] for w in live]} — resolve by hand')
    return live[0]['id'] if live else None


def ensure_workflow(name):
    pid = find_workflow(name)
    if not pid:
        out = hap.run('workflow', 'create', '-c', ORG, '-a', APP, '-n', name, '--type', 'worksheet', '-d', WF_DESC)
        data = out.get('data', out) if isinstance(out, dict) else {}
        pid = data.get('processId') or data.get('id')
        if not pid:
            sys.exit(f'{name}: no processId in `workflow create` output: {out}')
        print(f'  created {name}: {pid}')
    C.remember('workflows', name, pid)
    return pid


def body():
    upd = lambda alias, name: {'nodeAlias': alias, 'nodeType': 'update_record', 'name': name,
                               'config': {'worksheet': ORDERS, 'target': {'node': {'nodeAlias': 'order'}},
                                          'fields': []}}
    return [
        {'nodeAlias': 'order', 'nodeType': 'get_single', 'name': GET_ORDER,
         'config': {'worksheet': ORDERS, 'execute_type': 0}},        # 0 = stop when there is no order
        {'nodeAlias': 'nprod', 'nodeType': 'compute', 'name': N_PROD_STEP,
         'config': {'mode': 'number', 'formula': '0+0'}},
        {'nodeAlias': 'left', 'nodeType': 'compute', 'name': LEFT_STEP,
         'config': {'mode': 'number', 'formula': '0+0'}},
        {'nodeAlias': 'ndel', 'nodeType': 'compute', 'name': N_DELIVERED_STEP,
         'config': {'mode': 'number', 'formula': '0+0'}},
        {'nodeAlias': 'which', 'nodeType': 'branch', 'name': WHICH_BRANCH, 'config': {'paths': [
            {'alias': 'p1', 'name': PATH_FULL, 'nodes': [upd('u1', SET_FULL)]},
            {'alias': 'p2', 'name': PATH_PARTIAL, 'nodes': [upd('u2', SET_PARTIAL)]},
            {'alias': 'p3', 'name': PATH_NOT, 'nodes': [upd('u3', SET_NOT)]},
            {'alias': 'p4', 'name': PATH_NOTHING, 'nodes': [upd('u4', SET_NOTHING)]},
        ]}},
    ]


def nodes_for(lf, driver):
    """On the two line-driven workflows the body sits in a guard path: a search step whose filter value is
    empty fails the whole run, and a line with no order would give it one (BUILDING.md; o2i.status_nodes).

    The path is created **without** its condition: hap-cli 0.9's `batch-add` refuses `not_empty` on a Relation
    ("It takes: all_contains, eq, ne"), which o2i's own guard was built with under 0.8. `build_workflow` then
    writes *Orders is not empty* with `node save --type 2`, the call o2i uses to re-save every path anyway."""
    if driver == ORDERS:
        return body()
    return [{'nodeAlias': 'guard', 'nodeType': 'branch', 'name': GUARD_BRANCH, 'config': {'paths': [
        {'alias': 'has_order', 'name': 'Yes', 'nodes': body()},
        {'alias': 'no_order', 'name': 'No'},
    ]}}]


def trigger_fields(of, lf):
    """Only the fields that can change the answer — every run counts against the workflow quota."""
    return {
        WF_SELF: [of['Status']['controlId']],
        WF_LINES: [lf['Orders']['controlId'], lf['Display Type']['controlId'], lf['Quantity']['controlId'],
                   lf['Quantity Delivered']['controlId']],
        WF_DELETE: [],                                   # a delete trigger takes no field narrowing
    }


def conditions(of, byname):
    """In order: the first path that holds wins. Each compares a number formula step's own result."""
    order = byname[GET_ORDER]['id']
    state = of['Status']
    confirmed = cond(order, state, IS_ANY_OF, option_values(state, ['Sales Order']))
    nprod, left, ndel = (byname[s]['id'] for s in (N_PROD_STEP, LEFT_STEP, N_DELIVERED_STEP))
    return {
        PATH_FULL: [[confirmed, fx_cond(nprod, GTE_C, 1), fx_cond(left, EQ_C, 0)]],
        PATH_PARTIAL: [[confirmed, fx_cond(nprod, GTE_C, 1), fx_cond(ndel, GTE_C, 1)]],
        PATH_NOT: [[confirmed, fx_cond(nprod, GTE_C, 1)]],
        PATH_NOTHING: [],                                # no condition: the default path
    }


def sync_search(pid, node, conditions):
    """The search step's filter — o2i.sync_search for one AND-group and a get-one step, **without `appType`**:
    since hap-cli 0.9 a whole-step save of a search step (type 7) refuses a key the step has no use for, and
    `appType` is one (23 Sep 2026). `executeType` 0 stops the run when no order is found."""
    groups = [conditions]
    got = read_node(pid, node['id'])
    if (wf_filter_state(got.get('filters')) == wf_filter_state([{'conditions': groups}])
            and [f.get('spliceType') for f in got.get('filters') or []] == [1]
            and got.get('appId') == ORDERS and got.get('executeType') == 0):
        return False
    cfg = {'actionId': FROM_SHEET_ONE, 'appId': ORDERS, 'selectNodeId': '',
           'filters': [{'spliceType': 1, 'conditions': groups}], 'operateCondition': [],
           'sorts': got.get('sorts') or [{'controlId': 'ctime', 'controlType': 16, 'isAsc': True}],
           'executeType': 0}
    hap.run('workflow', 'node', 'save', pid, node['id'], '--type', str(GET_ONE), '-n', node['name'],
            '-c', json.dumps(cfg, ensure_ascii=False))
    back = read_node(pid, node['id'])
    if wf_filter_state(back.get('filters')) != wf_filter_state([{'conditions': groups}]) \
            or back.get('appId') != ORDERS or back.get('executeType') != 0:
        sys.exit(f"{node['name']}: filter reads back {wf_filter_state(back.get('filters'))} — "
                 f"`hap workflow rollback {pid} -y` restores the published version")
    return True


def workflow_state(pid):
    w = hap.run('workflow', 'get', pid)
    w = w.get('data', w) if isinstance(w, dict) else {}
    return w.get('name'), w.get('enabled'), w.get('publishStatus')


def build_workflow(name, of, lf):
    pid = ensure_workflow(name)
    driver = DRIVER[name]
    proc, byname = nodes_by_name(pid)
    changed = GET_ORDER not in byname
    if changed:
        hap.backup(f'delivery_workflow_{pid}_pre_build', proc)
        hap.run('workflow', 'node', 'batch-add', pid, '--nodes', json.dumps(nodes_for(lf, driver), ensure_ascii=False),
                '--trigger-worksheet', driver, '--trigger-event', EVENT[name], '--trigger-alias', 'trigger')
        proc, byname = nodes_by_name(pid)
    missing = [n for n in (GET_ORDER, N_PROD_STEP, LEFT_STEP, N_DELIVERED_STEP, WHICH_BRANCH) + tuple(SET_LABEL)
               if n not in byname]
    if missing:
        sys.exit(f'{name} {pid}: {missing} missing ({sorted(byname)}) — `hap workflow rollback {pid} -y`')
    trigger = proc['startEventId']
    changed |= sync_trigger(pid, trigger, TRIGGER_NAME[name], driver,
                            DELETE_EVENT if EVENT[name] == 'delete' else CREATE_OR_UPDATE,
                            trigger_fields(of, lf)[name])
    source = 'rowid' if driver == ORDERS else lf['Orders']['controlId']
    find = {'nodeId': byname[GET_ORDER]['id'], 'nodeType': GET_ONE, 'actionId': FROM_SHEET_ONE,
            'filedId': 'rowid', 'filedValue': 'Record ID', 'filedTypeId': TEXT, 'enumDefault': 0,
            'conditionId': EQ_C, 'sourceType': 0,
            'conditionValues': [{'nodeId': trigger, 'controlId': source, 'value': '', 'sureNodeId': trigger}]}
    changed |= sync_search(pid, byname[GET_ORDER], [find])
    if driver != ORDERS:                                 # `batch-add` drops a branch path's name
        guard_paths = paths_of(proc, byname[GUARD_BRANCH]['id'])
        has = next(p for p in guard_paths if p.get('nextId') not in (None, '', '99'))
        has_not = next(p for p in guard_paths if p['id'] != has['id'])
        changed |= save_path(pid, has, 'Yes', [[cond(trigger, lf['Orders'], NOT_EMPTY_C)]])
        changed |= save_path(pid, has_not, 'No', [])
    order = byname[GET_ORDER]['id']
    expressions = {
        N_PROD_STEP: f"${order}-{of[GOODS_SUM]['controlId']}$+0",
        LEFT_STEP: f"${order}-{of[LEFT_SUM]['controlId']}$+0",
        N_DELIVERED_STEP: f"${order}-{of[DELIVERED_COUNT]['controlId']}$+0",
    }
    for step, expression in expressions.items():
        changed |= sync_number_formula(pid, byname[step], expression)
    want = conditions(of, byname)
    paths = paths_of(proc, byname[WHICH_BRANCH]['id'])
    if len(paths) != 4:
        sys.exit(f'{name}: {WHICH_BRANCH} has {len(paths)} paths, wanted 4')
    by_step = {proc['flowNodeMap'].get(p.get('nextId') or '', {}).get('name'): p for p in paths}
    for label, step in PATHS:
        path = by_step.get(step)
        if path is None:
            sys.exit(f'{name}: no branch path runs into {step!r}; found {sorted(k for k in by_step if k)}')
        changed |= save_path(pid, path, label, want[label])
    ds = of['Delivery Status']
    key = {o['value']: o['key'] for o in ds.get('options') or []}
    for step, label in SET_LABEL.items():
        changed |= set_entries(pid, byname[step], [patch(ds['controlId'], DROPDOWN, value=key[label])], order, ORDERS)
    _name, enabled, status = workflow_state(pid)
    if changed or status != 2 or not enabled:
        print(f'  {name}:', C.publish(pid))
        _name, enabled, status = workflow_state(pid)
        if status != 2 or not enabled:
            sys.exit(f'{name}: after publishing, publishStatus {status}, enabled {enabled}')
    else:
        print(f'  {name}: already built and published; nothing saved')
    return pid


def retire_owners_draft():
    """The owner's unpublished draft triggered on the Orders' Order Lines field, which a line edit never writes —
    so it never fired. It is renamed, left disabled and unpublished, and nothing in it is changed or deleted."""
    name, enabled, status = workflow_state(OWNERS_DRAFT)
    if name == RETIRED_NAME:
        print(f'  {OWNERS_DRAFT}: already {RETIRED_NAME!r} (enabled {enabled}, publishStatus {status}); nothing saved')
    elif name == OWNERS_DRAFT_NAME:
        hap.backup('delivery_owners_draft_pre_rename', hap.run('workflow', 'get', OWNERS_DRAFT))
        hap.run('workflow', 'update', OWNERS_DRAFT, '-n', RETIRED_NAME)
        name, enabled, status = workflow_state(OWNERS_DRAFT)
        if name != RETIRED_NAME:
            sys.exit(f'{OWNERS_DRAFT}: the rename read back {name!r}')
        print(f'  {OWNERS_DRAFT}: renamed {OWNERS_DRAFT_NAME!r} -> {RETIRED_NAME!r} '
              f'(enabled {enabled}, publishStatus {status})')
    else:
        print(f'  {OWNERS_DRAFT}: is named {name!r} — not the draft this step expects; left alone')
        return
    if enabled:
        print(f'  WARNING {OWNERS_DRAFT} is ENABLED — the owner turned it on; left as it is, report it')


def step_workflows():
    of, lf = guard()
    missing = [n for n in ROLLUPS if n not in of]
    if missing:
        sys.exit(f'Orders has no {missing} — run `rollups` first')
    for name in WORKFLOWS:
        build_workflow(name, of, lf)
    retire_owners_draft()
    for name in WORKFLOWS:
        print(C.structure(hap.ids()['workflows'][name]))


# ── the rule, worked out here ───────────────────────────────────────────────

def expected_status(order_status, lines):
    """The rule of this module's docstring, from an order's Status label and its lines (line_rows' shape)."""
    if order_status != 'Sales Order':
        return 'Nothing to Deliver'
    product = [l for l in lines if l['Goods']]
    if not product:
        return 'Nothing to Deliver'
    if all((l['Quantity Delivered'] or 0) >= (l['Quantity'] or 0) for l in product):
        return 'Fully Delivered'
    if any((l['Quantity Delivered'] or 0) > 0 for l in product):
        return 'Partially Delivered'
    return 'Not Delivered'


def from_rollups(order_status, nprod, left, ndel):
    """What the workflow's branch decides from the three roll-ups, in the same order as its paths."""
    nprod, left, ndel = (float(x or 0) for x in (nprod, left, ndel))
    if order_status == 'Sales Order' and nprod >= 1 and left == 0:
        return 'Fully Delivered'
    if order_status == 'Sales Order' and nprod >= 1 and ndel >= 1:
        return 'Partially Delivered'
    if order_status == 'Sales Order' and nprod >= 1:
        return 'Not Delivered'
    return 'Nothing to Deliver'


def order_rows(of):
    """{rowid: (Number, Status, Delivery Status, Customer Reference, roll-ups)} from the listing and `record get`."""
    listed = {r['rowid']: r for r in C.records(ORDERS, APP)}
    out = {}
    for rowid, r in listed.items():
        d = o2i.read_record(ORDERS, rowid)
        status = cell_labels(d.get('state')) or cell_labels(r.get(of['Status']['controlId']))
        ds_get, ds_list = cell_labels(d.get('delivery_status')), cell_labels(r.get(DELIVERY_STATUS))
        out[rowid] = {
            'Number': d.get('name') or r.get(of['Number']['controlId']),
            'Reference': d.get('client_order_ref') or '',
            'Status': status[0] if status else '',
            'Delivery Status': (ds_get or ds_list or [''])[0],
            'paths agree': ds_get == ds_list,
            'rollups': tuple(d.get(of[n]['controlId']) for n in (GOODS_SUM, LEFT_SUM, DELIVERED_COUNT)
                             if n in of),
        }
    return out


def by_order(lines):
    out = {}
    for rowid, l in lines.items():
        for o in l['Orders'] or []:
            out.setdefault(o, []).append(l)
    return out


# ── 4 · backfill ────────────────────────────────────────────────────────────

def step_backfill():
    """Every order's Delivery Status worked out from its lines, and written only where it differs."""
    from collections import Counter
    of, lf = guard()
    lines, disagree = line_rows()
    for d in disagree:
        print(f'  read paths disagree on line {d[0]} {d[1]}: listing {d[2]!r}, record get {d[3]!r}')
    orders = order_rows(of)
    grouped = by_order(lines)
    key = {o['value']: o['key'] for o in of['Delivery Status']['options']}
    before = Counter(o['Delivery Status'] or '(empty)' for o in orders.values())
    todo = {}
    for rowid, o in orders.items():
        want = expected_status(o['Status'], grouped.get(rowid, []))
        if o['Delivery Status'] != want:
            todo[rowid] = (o, want)
        if not o['paths agree']:
            print(f"  note: {o['Number']} — the two read paths disagree on Delivery Status")
    print(f'  {len(orders)} orders; by Delivery Status before: {dict(before)}')
    print(f'  {len(todo)} to write')
    hap.backup('delivery_orders_pre_backfill',
               {r: {k: v for k, v in o.items() if k != 'rollups'} for r, o in orders.items()})
    for rowid, (o, want) in sorted(todo.items(), key=lambda x: x[1][0]['Number'] or ''):
        hap.run('worksheet', 'record', 'update', ORDERS, rowid, '-a', APP, '--fields-json',
                json.dumps([{'id': DELIVERY_STATUS, 'value': [key[want]]}], ensure_ascii=False))
        back = cell_labels(o2i.read_record(ORDERS, rowid).get('delivery_status'))
        listed = next((cell_labels(r.get(DELIVERY_STATUS)) for r in C.records(ORDERS, APP) if r['rowid'] == rowid), None) \
            if back != [want] else [want]
        if back != [want] or listed != [want]:
            sys.exit(f"{o['Number']}: Delivery Status read back {back} / {listed}, wanted {want}")
        print(f"  {o['Number']:<8} {o['Status']:<15} {o['Delivery Status'] or '(empty)':<20} -> {want}   "
              f"{o['Reference'][:34]}")
    after = Counter(o['Delivery Status'] or '(empty)' for o in order_rows(of).values())
    print(f'  by Delivery Status after: {dict(after)}')


# ── 5 · selfcheck ───────────────────────────────────────────────────────────

NOCOLY = 'd31d1f6b-fb89-4f6f-be0e-8e953a0892ac'      # Contacts / Nocoly — the only TEST customer
RKEY = 'delivery: '
T_MAIN = 'TEST delivery status'
T_DELIVER = 'TEST delivery status – Deliver button'
T_EMPTY = 'TEST delivery status – no product lines'
T_SECTION = 'TEST delivery section'
T_A, T_B = 'TEST delivery line A', 'TEST delivery line B'
T_D1, T_D2 = 'TEST delivery Deliver line 1', 'TEST delivery Deliver line 2'
T_E_SECTION = 'TEST delivery section only'


def record_id(key):
    return hap.ids().get('records', {}).get(RKEY + key)


def ensure_order(of, reference):
    """A TEST order found by its Customer Reference (Orders' title is an auto Number), created if missing."""
    rowid = record_id(reference)
    live = {r['rowid']: r for r in C.records(ORDERS, APP)}
    if rowid not in live:
        ref = of['Customer Reference']['controlId']
        rowid = next((r for r, x in live.items() if (x.get(ref) or '') == reference), None)
    if not rowid:
        values = [
            {'id': of['Status']['controlId'], 'value': [option_key(ORDERS, 'Status', 'Sales Order')]},
            {'id': of['Quotation/Order Date']['controlId'], 'value': time.strftime('%Y-%m-%d 09:00:00')},
            {'id': of['Tax Mode']['controlId'], 'value': [option_key(ORDERS, 'Tax Mode', 'Tax Excluded')]},
            {'id': of['Customer']['controlId'], 'value': [NOCOLY]},
            {'id': of['Invoice Address']['controlId'], 'value': [NOCOLY]},
            {'id': of['Delivery Address']['controlId'], 'value': [NOCOLY]},
            {'id': of['Customer Reference']['controlId'], 'value': reference},
            {'id': of['Salesperson']['controlId'], 'value': [o2i.me()]},
        ]
        rowid = C.row_id(hap.run('worksheet', 'record', 'create', ORDERS, '-a', APP, '--fields-json',
                                 json.dumps(values, ensure_ascii=False)))
        print(f'  created {reference}: {rowid}')
    C.remember('records', RKEY + reference, rowid)
    return rowid


def ensure_line(lf, order, label, kind, seq, qty):
    """A TEST line of `order`, found by its Description; created if missing, otherwise put back to `qty` and
    nothing delivered. Returns its rowid."""
    rowid = record_id(label)
    live = {r['rowid']: r for r in C.records(OLINES, APP)}
    if rowid not in live:
        rowid = next((r for r, x in live.items() if (x.get(OL_DESCRIPTION) or '') == label
                      and order in [v.get('sid') for v in (x.get(lf['Orders']['controlId']) or [])]), None)
    values = [{'id': OL_QUANTITY, 'value': qty}, {'id': OL_QTY_DELIVERED, 'value': 0}]
    if rowid:
        write_line(rowid, qty=qty, delivered=0)
    else:
        values = [{'id': lf['Orders']['controlId'], 'value': [order]},
                  {'id': OL_DISPLAY_TYPE, 'value': [option_key(OLINES, 'Display Type', kind)]},
                  {'id': OL_DESCRIPTION, 'value': label},
                  {'id': lf['Sequence']['controlId'], 'value': seq},
                  {'id': lf['Unit Price']['controlId'], 'value': 1 if kind == 'Product' else 0}] + values
        rowid = C.row_id(hap.run('worksheet', 'record', 'create', OLINES, '-a', APP, '--fields-json',
                                 json.dumps(values, ensure_ascii=False)))
        print(f'  created {label}: {rowid}')
    C.remember('records', RKEY + label, rowid)
    return rowid


def write_line(rowid, qty=None, delivered=None):
    values = []
    if qty is not None:
        values.append({'id': OL_QUANTITY, 'value': qty})
    if delivered is not None:
        values.append({'id': OL_QTY_DELIVERED, 'value': delivered})
    hap.run('worksheet', 'record', 'update', OLINES, rowid, '-a', APP, '--fields-json', json.dumps(values))


def set_status(of, order, label):
    hap.run('worksheet', 'record', 'update', ORDERS, order, '-a', APP, '--fields-json',
            json.dumps([{'id': of['Status']['controlId'], 'value': [option_key(ORDERS, 'Status', label)]}]))


def poison(of, order, label):
    """Write a wrong Delivery Status by hand, so the next action has to be the one that puts it right — a check
    whose answer is already the current value would otherwise prove nothing. No workflow reads this field."""
    hap.run('worksheet', 'record', 'update', ORDERS, order, '-a', APP, '--fields-json',
            json.dumps([{'id': DELIVERY_STATUS, 'value': [option_key(ORDERS, 'Delivery Status', label)]}]))


def delivery_status(order):
    return (cell_labels(o2i.read_record(ORDERS, order).get('delivery_status')) or [''])[0]


def settle(order, want, seconds=75):
    """Poll until the order reads `want`, then hold for a few seconds more so a late run cannot change it."""
    got = ''
    for _ in range(seconds // 3):
        got = delivery_status(order)
        if got == want:
            time.sleep(6)
            got = delivery_status(order)
            if got == want:
                return got
        time.sleep(3)
    return got


def step_selfcheck():
    """Drive every rule through the CLI on three TEST orders whose customer is the Nocoly contact. Nothing is
    deleted but TEST line B of the main order (a soft delete — HAP's recycle bin), which is the deletion case."""
    of, lf = guard()
    problems = []

    def expect(label, order, want, poisoned=None):
        got = settle(order, want)
        mark = 'OK  ' if got == want else 'FAIL'
        print(f'  {mark} {label:<66} -> {got or "(empty)"}' + (f'  (was set to {poisoned} first)' if poisoned else ''))
        if got != want:
            problems.append(f'{label}: {got!r}, wanted {want!r}')

    # ── an order with no product line
    empty = ensure_order(of, T_EMPTY)
    ensure_line(lf, empty, T_E_SECTION, 'Section', 10, 0)
    set_status(of, empty, 'Sales Order')
    time.sleep(4)
    poison(of, empty, 'Not Delivered')
    time.sleep(2)
    set_status(of, empty, 'Quotation')
    expect('no product lines, Status -> Quotation', empty, 'Nothing to Deliver', 'Not Delivered')
    poison(of, empty, 'Not Delivered')
    time.sleep(2)
    set_status(of, empty, 'Sales Order')
    expect('no product lines (a section only), Status -> Sales Order', empty, 'Nothing to Deliver', 'Not Delivered')

    # ── the main order
    main = ensure_order(of, T_MAIN)
    set_status(of, main, 'Sales Order')
    ensure_line(lf, main, T_SECTION, 'Section', 10, 0)
    a = ensure_line(lf, main, T_A, 'Product', 20, 3)
    b = ensure_line(lf, main, T_B, 'Product', 30, 2)
    expect('A 0/3, B 0/2 — nothing delivered', main, 'Not Delivered')
    write_line(a, delivered=1)
    expect('A 1/3, B 0/2 — one line partly delivered', main, 'Partially Delivered')
    poison(of, main, 'Fully Delivered')
    time.sleep(2)
    write_line(a, delivered=5)
    expect('A 5/3 over-delivered, B 0/2 — the surplus must not cover B', main, 'Partially Delivered',
           'Fully Delivered')
    write_line(b, delivered=2)
    expect('A 5/3, B 2/2 — every line delivered', main, 'Fully Delivered')
    write_line(b, delivered=0)
    expect('A 5/3, B 0/2 again', main, 'Partially Delivered')
    hap.run('worksheet', 'record', 'delete', OLINES, '--row-ids', b, '-a', APP, '-y')
    ids = hap.ids()
    ids['records'].pop(RKEY + T_B, None)
    C.save_ids(ids)
    expect('line B (the undelivered one) deleted — A 5/3 is all that is left', main, 'Fully Delivered')
    set_status(of, main, 'Cancelled')
    expect('Status -> Cancelled', main, 'Nothing to Deliver')
    poison(of, main, 'Fully Delivered')
    time.sleep(2)
    set_status(of, main, 'Quotation')
    expect('Status -> Quotation (A 5/3 delivered)', main, 'Nothing to Deliver', 'Fully Delivered')
    set_status(of, main, 'Sales Order')
    expect('Status -> Sales Order again', main, 'Fully Delivered')

    # ── the Deliver button
    dorder = ensure_order(of, T_DELIVER)
    set_status(of, dorder, 'Sales Order')
    d1 = ensure_line(lf, dorder, T_D1, 'Product', 10, 4)
    d2 = ensure_line(lf, dorder, T_D2, 'Product', 20, 2.5)
    expect('Deliver order before the press — nothing delivered', dorder, 'Not Delivered')
    pid = hap.ids()['workflows']['Orders: Deliver']
    hap.run('workflow', 'trigger', pid, '-s', dorder)
    expect('Deliver pressed (every product line: Delivered = Quantity)', dorder, 'Fully Delivered')
    for rowid in (d1, d2):
        d = o2i.read_record(OLINES, rowid)
        print(f"       {d.get('name')}: Quantity {d.get('product_uom_qty')} Delivered {d.get('qty_delivered')}")

    print(f'  TEST records: {T_MAIN} {main} · {T_DELIVER} {dorder} · {T_EMPTY} {empty}')
    print('  selfcheck: ' + ('OK' if not problems else 'DIFFERENCES\n    ' + '\n    '.join(problems)))
    return len(problems)


# ── check — read-only ───────────────────────────────────────────────────────

def step_check():
    of, lf = guard()
    problems = []
    c = lf[LEFT]
    if function_expression(c) != left_expression() or c.get('alias') != LEFT_ALIAS:
        problems.append(f'{LEFT}: {function_expression(c)!r} alias {c.get("alias")!r}')
    print(f"  {LEFT}: {function_expression(c)}  alias={c.get('alias')!r} perm={c.get('fieldPermission')}")
    wanted = rollups_wanted()
    for n in ROLLUPS:
        if n not in of:
            problems.append(f'Orders has no {n!r}')
            continue
        via, source, agg, items, dot = wanted[n]
        r = of[n]
        ok = (r['type'] == ROLLUP and r.get('dataSource') == f'${via}$' and r.get('sourceControlId') == source
              and r.get('enumDefault') == agg and r.get('fieldPermission') == HIDDEN
              and filter_state((r.get('advancedSetting') or {}).get('filters')) == filter_state(items))
        print(f"  {'OK  ' if ok else 'DIFF'} Orders / {n:<30} {r['controlId']} row {r.get('row')}")
        if not ok:
            problems.append(f'{n} differs from its spec')
    for name in WORKFLOWS:
        pid = find_workflow(name)
        if not pid:
            problems.append(f'{name}: not built')
            continue
        wname, enabled, status = workflow_state(pid)
        print(f'  {name}: {pid} enabled={enabled} publishStatus={status}')
        if not enabled or status != 2:
            problems.append(f'{name}: enabled {enabled}, publishStatus {status}')
        proc, byname = nodes_by_name(pid)
        bad = [n for n in (GET_ORDER, N_PROD_STEP, LEFT_STEP, N_DELIVERED_STEP) + tuple(SET_LABEL)
               if n not in byname or read_node(pid, byname[n]['id']).get('isException')]
        if bad:
            problems.append(f'{name}: {bad} missing or in exception')
    dname, denabled, dstatus = workflow_state(OWNERS_DRAFT)
    print(f'  owner\'s draft {OWNERS_DRAFT}: {dname!r} enabled={denabled} publishStatus={dstatus}')
    if denabled:
        problems.append(f'the owner\'s draft {OWNERS_DRAFT} is enabled')
    lines, disagree = line_rows()
    problems += [f'{LEFT} differs on line {w[0]}' for w in prove_helper(lines)]
    grouped = by_order(lines)
    orders = order_rows(of)
    for rowid, o in sorted(orders.items(), key=lambda x: x[1]['Number'] or ''):
        want = expected_status(o['Status'], grouped.get(rowid, []))
        wf = from_rollups(o['Status'], *o['rollups']) if len(o['rollups']) == 3 else '?'
        flag = []
        if o['Delivery Status'] != want:
            flag.append(f'stores {o["Delivery Status"] or "(empty)"}')
        if wf != want:
            flag.append(f'roll-ups {o["rollups"]} would give {wf}')
        if flag:
            problems.append(f"{o['Number']} ({o['Status']}): wanted {want}; " + '; '.join(flag))
    print(f'  {len(orders)} orders compared with their lines and their roll-ups')
    o2i.report_parked(list(ROLLUPS), of)
    print('  check: ' + ('OK' if not problems else 'DIFFERENCES\n    ' + '\n    '.join(problems)))
    return len(problems)


def main():
    steps = {'helper': step_helper, 'rollups': step_rollups, 'workflows': step_workflows,
             'backfill': step_backfill, 'selfcheck': step_selfcheck, 'check': step_check}
    if len(sys.argv) != 2 or sys.argv[1] not in steps:
        sys.exit(f'usage: delivery.py <{"|".join(steps)}>')
    steps[sys.argv[1]]()


if __name__ == '__main__':
    main()
