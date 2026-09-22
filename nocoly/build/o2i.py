"""Bundle `bo2i` — the order → invoice link (worksheets/21-order-to-invoice.md).

Odoo's sales-to-invoicing chain hangs off one stored many-to-many,
`sale_order_line_invoice_rel`, between `sale.order.line` and `account.move.line`
(`addons/sale/models/sale_order_line.py:257-261`, `addons/sale/models/account_move_line.py:12-16`).
Every figure a user reads is derived from it. ERP Master holds both ends as real worksheets and
nothing joined them; this script joins them and builds what the join makes possible.

Steps, in order — each reads live state first, saves nothing when re-run, and reads back every write:

    ~/.hap-venv/bin/python nocoly/build/o2i.py lookups     # 1 the two type-30 lookups
    ~/.hap-venv/bin/python nocoly/build/o2i.py relations   # 2 the two Relation pairs and the two counts
    ~/.hap-venv/bin/python nocoly/build/o2i.py qty         # 3 the quantity roll-ups, Quantity Invoiced 6 -> 31
    ~/.hap-venv/bin/python nocoly/build/o2i.py toinvoice   # 4 Quantity To Invoice, Line Invoice Status, 5 counts
    ~/.hap-venv/bin/python nocoly/build/o2i.py status      # 5 the three Invoice Status workflows
    ~/.hap-venv/bin/python nocoly/build/o2i.py views       # 6 To Invoice / To Upsell, Lines to Invoice
    ~/.hap-venv/bin/python nocoly/build/o2i.py guards      # 7 the two automation gates
    ~/.hap-venv/bin/python nocoly/build/o2i.py create      # 8 Create Invoice, the button and its workflow
    ~/.hap-venv/bin/python nocoly/build/o2i.py repair      # 9 rebuild Orders' Invoices from the lines
    ~/.hap-venv/bin/python nocoly/build/o2i.py selfcheck   # 10 the CLI drive of steps 5 and 8
    ~/.hap-venv/bin/python nocoly/build/o2i.py check       # read-only: every control, workflow and view

Every control save on the four worksheets the owner hand-edits is **version-pinned** and proved by
signature diff (`products.py:297` `step_perms`). New controls are appended with `append_controls`,
which parks them at row 9999 — **placement is the owner's**, and each control's intended place is
recorded in `PLACE`.
"""
import json, subprocess, sys, time

sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))

import common as C
import hap

APP = '6cb4d051-a33c-4bf9-b56f-5f47f0e85dc9'
ORG = 'f887b7cc-6832-416c-8e7e-c730aec70a21'

ORDERS = '6ab09897e43d174ab3752d7b'
OLINES = '6ab0c740e43d174ab37535b2'
INVOICES = '6aa90facf363582dd37a62f7'
ILINES = '6aaa2b50e54d2a34fa4e0221'

KEY = {ORDERS: 'Orders: ', OLINES: 'Order Lines: ', INVOICES: 'Invoices: ', ILINES: 'Invoice Lines: '}
NAME = {ORDERS: 'Orders', OLINES: 'Order Lines', INVOICES: 'Invoices', ILINES: 'Invoice Lines'}

TEXT, NUMBER, CURRENCY, DROPDOWN, RELATION, LOOKUP, FORMULA = 2, 6, 8, 11, 29, 30, 31
SUBTABLE, SWITCH, ROLLUP, FUNCTION = 34, 36, 37, 53

# ── the controls this bundle owns ────────────────────────────────────────────
#
# Names are Odoo's English labels; aliases are Odoo field names. A control with no alias is one Odoo
# has no stored field for (a working figure of ours, or the reverse of a computed relation).

DOC_TYPE = 'Document Type'                       # Invoice Lines, lookup of the invoice's Type
ORDER_STATE = 'Order Status'                      # Order Lines, lookup of the order's Status
OL_INVOICE_LINES = 'Invoice Lines'                # Order Lines -> Invoice Lines, the m2m
IL_ORDER_LINES = 'Sales Order Lines'              # its reverse on Invoice Lines
O_INVOICES = 'Invoices'                           # Orders -> Invoices, the header denormalisation
I_ORDERS = 'Sales Orders'                         # its reverse on Invoices
O_INVOICE_COUNT = 'Invoice Count'
I_ORDER_COUNT = 'Sales Order Count'
QTY_INVOICES = 'Qty on invoices'                  # Order Lines, working 汇总
QTY_REFUNDS = 'Qty on credit notes'               # Order Lines, working 汇总
QTY_INVOICED = 'Quantity Invoiced'                # Order Lines, an existing Number converted to a Formula
QTY_TO_INVOICE = 'Quantity To Invoice'            # Order Lines, function formula
LINE_STATUS = 'Line Invoice Status'               # Order Lines, function formula, a number 0-3
INVOICEABLE = 'Invoiceable line'                  # Order Lines, function formula, 1 when Create Invoice takes it
N_TO_INVOICE = 'Lines to invoice'                 # Orders, the five filtered counts over the subtable
N_NOTHING = 'Lines not to invoice'
N_INVOICED = 'Lines invoiced'
N_UPSELLING = 'Lines upselling'
N_PRODUCT = 'Product lines'

ALIAS = {DOC_TYPE: 'move_type', ORDER_STATE: 'state', OL_INVOICE_LINES: 'invoice_lines',
         IL_ORDER_LINES: 'sale_line_ids', O_INVOICES: 'invoice_ids', I_ORDERS: '',
         O_INVOICE_COUNT: 'invoice_count', I_ORDER_COUNT: 'sale_order_count',
         QTY_INVOICES: '', QTY_REFUNDS: '', QTY_TO_INVOICE: 'qty_to_invoice',
         LINE_STATUS: 'invoice_status', INVOICEABLE: '', N_TO_INVOICE: '', N_NOTHING: '',
         N_INVOICED: '', N_UPSELLING: '', N_PRODUCT: ''}

# Descriptions are for the app's users (owner's rule, 22 Sep 2026): what the control does, in plain
# words, no Odoo and no field names. A working figure nobody sees carries none.
DESC = {
    DOC_TYPE: '', ORDER_STATE: '',
    OL_INVOICE_LINES: 'The invoice lines that have billed this order line.',
    IL_ORDER_LINES: 'The order lines this invoice line bills.',
    O_INVOICES: 'The invoices made from this order.',
    I_ORDERS: 'The sales orders this invoice bills.',
    O_INVOICE_COUNT: 'How many invoices have been made from this order.',
    I_ORDER_COUNT: 'How many sales orders this invoice bills.',
    QTY_INVOICES: '', QTY_REFUNDS: '',
    QTY_TO_INVOICE: 'How much of this line is still waiting to be invoiced.',
    LINE_STATUS: '', INVOICEABLE: '', N_TO_INVOICE: '', N_NOTHING: '', N_INVOICED: '',
    N_UPSELLING: '', N_PRODUCT: '',
}

# `add-fields` parks every new control at row 9999 and only a full save places one, so **placement is
# the owner's**. This is the intent, per 21 §4.2, as (row, col, size, tab or divider).
PLACE = {
    DOC_TYPE: (9999, 0, 6, 'hidden — not a column of the invoice line grid'),
    ORDER_STATE: (9999, 0, 6, 'hidden — not a column of the order line grid'),
    OL_INVOICE_LINES: (9999, 0, 12, 'hidden — a link, not a figure a person reads in the grid'),
    IL_ORDER_LINES: (9999, 0, 12, 'hidden — not a column of the invoice line grid'),
    # The owner placed these four on 23 Sep 2026 and set their `showControls` so the lists show real columns.
    # No step of this script writes a row, a column or a `showControls` on any of them: `count_spec` compares
    # only the keys it owns, and the relations themselves are compared not at all once they exist.
    O_INVOICES: (9999, 0, 6, 'placed by the owner — Other Info › Invoicing'),
    O_INVOICE_COUNT: (9999, 0, 6, 'placed by the owner — beside Invoices'),
    I_ORDERS: (9999, 0, 6, 'placed by the owner — Other Info › Invoice'),
    I_ORDER_COUNT: (9999, 0, 6, 'placed by the owner — beside Sales Orders'),
    QTY_INVOICES: (9999, 0, 6, 'hidden — a working figure'),
    QTY_REFUNDS: (9999, 0, 6, 'hidden — a working figure'),
    QTY_TO_INVOICE: (9999, 0, 6, 'the subtable grid, right after Quantity Invoiced'),
    LINE_STATUS: (9999, 0, 6, 'hidden — a working figure'),
    INVOICEABLE: (9999, 0, 6, 'hidden — a working figure'),
    N_TO_INVOICE: (9999, 0, 6, 'hidden — a working figure'),
    N_NOTHING: (9999, 0, 6, 'hidden — a working figure'),
    N_INVOICED: (9999, 0, 6, 'hidden — a working figure'),
    N_UPSELLING: (9999, 0, 6, 'hidden — a working figure'),
    N_PRODUCT: (9999, 0, 6, 'hidden — a working figure'),
}

HIDDEN = '011'                                    # hidden: never a column, never on a form
READONLY = '101'
UNRESTRICTED = '111'
PERM = {DOC_TYPE: HIDDEN, ORDER_STATE: HIDDEN, OL_INVOICE_LINES: HIDDEN, IL_ORDER_LINES: HIDDEN,
        O_INVOICES: READONLY, I_ORDERS: READONLY, O_INVOICE_COUNT: READONLY,
        I_ORDER_COUNT: READONLY, QTY_INVOICES: HIDDEN, QTY_REFUNDS: HIDDEN,
        QTY_TO_INVOICE: READONLY, LINE_STATUS: HIDDEN, INVOICEABLE: HIDDEN,
        N_TO_INVOICE: HIDDEN, N_NOTHING: HIDDEN,
        N_INVOICED: HIDDEN, N_UPSELLING: HIDDEN, N_PRODUCT: HIDDEN}

WHERE = {DOC_TYPE: ILINES, ORDER_STATE: OLINES, OL_INVOICE_LINES: OLINES, IL_ORDER_LINES: ILINES,
         O_INVOICES: ORDERS, I_ORDERS: INVOICES, O_INVOICE_COUNT: ORDERS, I_ORDER_COUNT: INVOICES,
         QTY_INVOICES: OLINES, QTY_REFUNDS: OLINES, QTY_TO_INVOICE: OLINES, LINE_STATUS: OLINES,
         INVOICEABLE: OLINES,
         N_TO_INVOICE: ORDERS, N_NOTHING: ORDERS, N_INVOICED: ORDERS, N_UPSELLING: ORDERS,
         N_PRODUCT: ORDERS}


# ── live state ──────────────────────────────────────────────────────────────

def fields(ws):
    return hap.by_name(c for c in hap.controls(ws) if c['type'] != C.TAB)


def option_key(ws, control_name, label):
    """An option's key, read live — never the one written in a brief."""
    c = fields(ws).get(control_name)
    if c is None:
        sys.exit(f'{NAME[ws]} has no control {control_name!r}')
    key = next((o['key'] for o in c.get('options') or [] if o.get('value') == label), None)
    if not key:
        sys.exit(f'{NAME[ws]} / {control_name} has no option {label!r}; it has '
                 f'{[o.get("value") for o in c.get("options") or []]}')
    return key


def guard():
    """Every worksheet this bundle touches is where ids.json says, and none of them is the Sales app."""
    ids = hap.ids()
    if ids.get('app') != APP:
        sys.exit(f'ids.json holds app {ids.get("app")}, this script is written for {APP}')
    for ws, name in NAME.items():
        if ids['worksheets'].get(name) != ws:
            sys.exit(f'ids.json holds {name} = {ids["worksheets"].get(name)}, wanted {ws}')
    return {ws: fields(ws) for ws in NAME}


def remember(name, control_id):
    C.remember('controls', KEY[WHERE[name]] + name, control_id)


# ── a version-pinned append ─────────────────────────────────────────────────

def pinned_append(ws, ctrls, backup, step, untouched=()):
    """Add controls in **one** SaveWorksheetControls pinned to the version it read, and prove by signature
    diff that every control already there came back exactly as it was.

    `append_controls` (AddWorksheetControls) is the safe way to add, and `C.append_checked` proves it — but a
    control that must carry a **reserved controlId** (the reverse half of a two-way Relation) cannot be added
    that way: `append_controls` strips the id so the server mints its own. That one needs a full save, and a
    full save on a worksheet the owner hand-edits must be pinned."""
    live, version = C.controls_with_version(ws)
    before = C.control_signature(live)
    others = {w: C.control_signature(hap.controls(w)) for w in untouched}
    hap.backup(backup, live)
    C.save_controls(ws, live + list(ctrls), version=version)
    after_live = hap.controls(ws)
    new_ids = {c['controlId'] for c in after_live if c['controlId'] not in before}
    after = C.control_signature(after_live, ignore_related=new_ids)
    moved = [k for k in before if before[k] != after.get(k)]
    added = sorted(c['controlName'] for c in after_live if c['controlId'] in new_ids)
    want = sorted(c['controlName'] for c in ctrls)
    if moved or added != want:
        names = {c['controlId']: c['controlName'] for c in after_live}
        sys.exit(f'{step}: the pinned save moved {[names.get(m, m) for m in moved]} and added {added}, '
                 f'wanted only {want}\n' +
                 '\n'.join(f'  {names.get(k, k)}\n    was {before.get(k)}\n    now {after.get(k)}' for k in moved))
    for w, sig in others.items():
        if C.control_signature(hap.controls(w)) != sig:
            sys.exit(f'{step}: {NAME.get(w, w)} changed under the save')
    print(f'  {step}: {added} saved onto {NAME[ws]}; {len(before)} existing controls unchanged'
          + (f", {[NAME.get(w, w) for w in untouched]} untouched" if untouched else ''))
    return fields(ws)


def report_parked(names, live):
    parked = [n for n in names if live.get(n, {}).get('row') == 9999]
    if parked:
        print('  placement outstanding — the owner places these in the designer; intended:')
        for n in parked:
            row, col, size, where = PLACE[n]
            print(f'    {n:<22} ({row}, {col}, {size})  {where}')


# ── 1 · the two lookups ─────────────────────────────────────────────────────
#
# Odoo's line-level status and quantity rules read the parent document's state: `sale.order.line`
# leans on `order_id.state` (`sale_order_line.py:1048-1104`) and `qty_invoiced` skips an invoice line
# whose move is cancelled and signs a refund the other way (`sale_order_line.py:984-1017`). Neither
# worksheet carries the parent's state, so each gets a type-30 lookup of it. A lookup of a single
# select stores the **source** control's option key and the editors read it as type 11 (BUILDING.md),
# which is what lets a 汇总's filter and a workflow path compare it.

LOOKUP_SPEC = {
    # name: (worksheet, the Relation it travels, the source control on the other side)
    DOC_TYPE: (ILINES, '6aaa2baae43d174ab3749dea', '6aa9f847e54d2a34fa4dfeee'),   # Invoice -> Invoices' Type
    ORDER_STATE: (OLINES, '6ab0c740e43d174ab37535b1', '6ab0a847e54d2a34fa4e7b96'),  # Orders -> Orders' Status
}


# `strDefault` decides whether a lookup is **stored**. hap-cli's SHEET_FIELD default is "10" — a display
# lookup: the value renders in the form and `record get` answers with it, but nothing is written into the
# record's own column, so **a 汇总's filter over it matches nothing** and computes 0.00 with no error
# anywhere. Measured on 23 Sep 2026: Document Type as "10", *is Customer Invoice* on an invoice line that
# plainly was one, summed 0.00; *is not Customer Invoice* on the same line summed 3.00. Invoice Lines' own
# three lookups (Number, Accounting Date, Status) carry **"00"**, a stored lookup, and they filter
# correctly — `invlines.py:546` already names it "'00' = a stored lookup, as on Variants".
STORED_LOOKUP = '00'


def lookup_control(name):
    ws, via, source = LOOKUP_SPEC[name]
    row, col, size, _ = PLACE[name]
    c = C.control('SHEET_FIELD', name, (row, col, size), alias=ALIAS[name], hint='', desc=DESC[name],
                  data_source=via, source_control_id=source,
                  extra={'strDefault': STORED_LOOKUP, 'dot': 0})
    c['fieldPermission'] = PERM[name]
    return c


def lookup_spec(name):
    ws, via, source = LOOKUP_SPEC[name]
    return {'type': LOOKUP, 'alias': ALIAS[name], 'desc': DESC[name], 'required': False,
            'fieldPermission': PERM[name], 'dataSource': f'${via}$', 'sourceControlId': source,
            'strDefault': STORED_LOOKUP}


def step_lookups():
    """Invoice Lines' Document Type and Order Lines' Order Status, both hidden.

    A lookup added to a live worksheet computes on every existing record at once (BUILDING.md), so all
    39 invoice lines carry their document's Type and all 37 order lines their order's Status the moment
    the control is saved, with no nudge."""
    live = guard()
    for name in (DOC_TYPE, ORDER_STATE):
        ws = WHERE[name]
        if name not in live[ws]:
            C.append_checked(ws, [lookup_control(name)], f'o2i_{NAME[ws].lower().replace(" ", "")}_pre_lookups',
                             f'lookups/{name}')
            live[ws] = fields(ws)
        else:
            print(f'  {NAME[ws]} / {name} is already there; nothing appended')
        want = lookup_spec(name)
        stale = C.drift(live[ws][name], want)
        if stale:
            C.pinned_write(ws, {live[ws][name]['controlId']: {k: want[k] for k in stale}},
                           f'o2i_{NAME[ws].lower().replace(" ", "")}_pre_lookup_repair', f'lookups/{name}')
            live[ws] = fields(ws)
        remember(name, live[ws][name]['controlId'])
        c = live[ws][name]
        print(f"  OK  {NAME[ws]} / {name:<14} {c['controlId']} t{c['type']} alias={c.get('alias')!r} "
              f"perm={c.get('fieldPermission')} ds={c.get('dataSource')} src={c.get('sourceControlId')}")
    for name in (DOC_TYPE, ORDER_STATE):
        report_parked([name], live[WHERE[name]])
    check_lookups_read()


def check_lookups_read():
    """Every existing record computed the lookup. `record get` is the read path that returns a hidden field;
    the listing drops it (CLAUDE.md), so this reads the one that works and says how many rows answered."""
    for name in (DOC_TYPE, ORDER_STATE):
        ws = WHERE[name]
        c = fields(ws)[name]
        rows = C.records(ws, APP)
        got = {}
        for r in rows:
            d = hap.run('worksheet', 'record', 'get', ws, r['rowid'], '-a', APP)
            d = d.get('data', d) if isinstance(d, dict) else {}
            got[r['rowid']] = cell_labels(d.get(c['controlId']) or d.get(c.get('alias') or '_'))
        filled = sum(1 for v in got.values() if v)
        counts = {}
        for v in got.values():
            counts[tuple(v)] = counts.get(tuple(v), 0) + 1
        print(f'  {NAME[ws]} / {name}: {filled} of {len(rows)} records carry a value — {counts}')


def cell_labels(value):
    """A stored single-select or lookup-of-a-single-select cell as its labels."""
    if isinstance(value, str):
        if not value:
            return []
        try:
            value = json.loads(value)
        except ValueError:
            return [value]
    if isinstance(value, dict):
        value = [value]
    out = []
    for v in value or []:
        out.append(v.get('value') if isinstance(v, dict) else v)
    return [x for x in out if x]


# ── 2 · the two Relation pairs, and the two counts ──────────────────────────
#
# 21 §4.1: the line-level many-to-many is Odoo's one stored link. HAP's 关联记录 lets each side be
# 单条 or 多条 independently, so 多 ↔ 多 is expressible — nothing in this app paired two multiples
# before, which is why `relations` proves it before anything is built on it.
#
# 21 §4.2: the order's own invoice list is a **denormalisation**, because a 汇总 cannot cross two
# relation hops (`sale.order.invoice_ids` is `order_line.invoice_lines.move_id`). It is written by
# Create Invoice, so it can drift, and step 9 rebuilds it from the lines.

RELATION_PAIRS = {
    # forward name: (forward worksheet, target worksheet, reverse name, forward multiple)
    OL_INVOICE_LINES: (OLINES, ILINES, IL_ORDER_LINES, True),
    O_INVOICES: (ORDERS, INVOICES, I_ORDERS, True),
}
# count name: (the multi-Relation it counts, the worksheet that Relation points at)
COUNTS = {O_INVOICE_COUNT: (O_INVOICES, INVOICES), I_ORDER_COUNT: (I_ORDERS, ORDERS)}


def forward_control(name):
    ws, target, _reverse, multi = RELATION_PAIRS[name]
    row, col, size, _ = PLACE[name]
    c = C.control('RELATE_SHEET', name, (row, col, size), alias=ALIAS[name], hint='', desc=DESC[name],
                  data_source=target, multi=multi,
                  advanced_setting={'showtype': '2', 'bidirectional': '1'})   # 2 = the records as a list
    c['fieldPermission'] = PERM[name]
    return c


def reverse_control(name, reserved, forward_id, target):
    row, col, size, _ = PLACE[name]
    c = C.control('RELATE_SHEET', name, (row, col, size), alias=ALIAS[name], hint='', desc=DESC[name],
                  data_source=target, multi=True, advanced_setting={'showtype': '2'})
    c.update(controlId=reserved, sourceControlId=forward_id, sourceControlType=6,
             fieldPermission=PERM[name])
    return c


def count_control(name, via_id):
    """A 汇总 counting the records of a multi-Relation. A count still needs a column named on the target
    worksheet in `sourceControlId` — the title serves (BUILDING.md)."""
    row, col, size, _ = PLACE[name]
    target = COUNTS[name][1]
    title = next((c['controlId'] for c in hap.controls(target) if c.get('attribute') == 1), None)
    if not title:
        sys.exit(f'{NAME[target]} has no title control, so a count 汇总 has no column to name')
    c = C.control('SUBTOTAL', name, (row, col, size), alias=ALIAS[name], hint='', desc=DESC[name],
                  data_source=via_id, source_control_id=title, extra={'enumDefault': 6, 'dot': 0})
    c['fieldPermission'] = PERM[name]
    return c


def count_spec(name, via_id):
    target = COUNTS[name][1]
    title = next(c['controlId'] for c in hap.controls(target) if c.get('attribute') == 1)
    return {'type': ROLLUP, 'alias': ALIAS[name], 'desc': DESC[name], 'fieldPermission': PERM[name],
            'dataSource': f'${via_id}$', 'sourceControlId': title, 'enumDefault': 6, 'dot': 0}


def step_relations():
    """Both Relation pairs, then both count 汇总.

    The handshake, from BUILDING.md: a two-way Relation added to another worksheet with `add-fields` gets
    **no reverse at all** — the server only reserves the id in `sourceControlId`. The reverse is saved on
    the target by hand, carrying that reserved controlId, `sourceControlId` = the forward control,
    `sourceControlType` 6 and `enumDefault` 2. What was unproven here is a **多 ↔ 多** pair: both sides
    multiple. The reverse half of the handshake is always `enumDefault` 2, so the only new thing is the
    forward side being multiple too."""
    live = guard()
    for name, (ws, target, reverse, _multi) in RELATION_PAIRS.items():
        if name not in live[ws]:
            C.append_checked(ws, [forward_control(name)], f'o2i_{NAME[ws].lower().replace(" ", "")}_pre_relations',
                             f'relations/{name}', untouched=(target,))
            live[ws] = fields(ws)
        else:
            print(f'  {NAME[ws]} / {name} is already there; nothing appended')
        forward = live[ws][name]
        reserved = forward.get('sourceControlId')
        if not reserved:
            sys.exit(f'{NAME[ws]} / {name} has no sourceControlId — it was saved one-way; it cannot be paired')
        have = {c['controlId']: c for c in hap.controls(target)}
        if reserved not in have:
            pinned_append(target, [reverse_control(reverse, reserved, forward['controlId'], ws)],
                          f'o2i_{NAME[target].lower().replace(" ", "")}_pre_reverse', f'relations/{reverse}')
        else:
            print(f'  {NAME[target]} / {have[reserved]["controlName"]} already carries the reserved id {reserved}')
        live[ws], live[target] = fields(ws), fields(target)
        back = next((c for c in hap.controls(target) if c['controlId'] == reserved), None)
        if back is None:
            sys.exit(f'{reverse}: the reverse {reserved} is still not on {NAME[target]}')
        if back.get('sourceControlId') != forward['controlId'] or back.get('enumDefault') != 2:
            sys.exit(f'{reverse}: reverse read back {json.dumps(back, ensure_ascii=False)[:400]}')
        remember(name, forward['controlId'])
        C.remember('controls', KEY[target] + reverse, reserved)
        print(f"  OK  {NAME[ws]} / {name:<18} {forward['controlId']} enumDefault={forward.get('enumDefault')} "
              f"alias={forward.get('alias')!r} perm={forward.get('fieldPermission')} -> {NAME[target]}")
        print(f"  OK  {NAME[target]} / {back['controlName']:<18} {back['controlId']} "
              f"enumDefault={back.get('enumDefault')} alias={back.get('alias')!r} "
              f"perm={back.get('fieldPermission')} sourceControlType={back.get('sourceControlType')}")
    for name, (via, _target) in COUNTS.items():
        ws = WHERE[name]
        via_id = fields(ws)[via]['controlId']
        if name not in live[ws]:
            C.append_checked(ws, [count_control(name, via_id)],
                             f'o2i_{NAME[ws].lower().replace(" ", "")}_pre_counts', f'relations/{name}')
            live[ws] = fields(ws)
        else:
            print(f'  {NAME[ws]} / {name} is already there; nothing appended')
        want = count_spec(name, via_id)
        stale = C.drift(live[ws][name], want)
        if stale:
            C.pinned_write(ws, {live[ws][name]['controlId']: {k: want[k] for k in stale}},
                           f'o2i_{NAME[ws].lower().replace(" ", "")}_pre_count_repair', f'relations/{name}')
            live[ws] = fields(ws)
        remember(name, live[ws][name]['controlId'])
        c = live[ws][name]
        print(f"  OK  {NAME[ws]} / {name:<18} {c['controlId']} t{c['type']} enumDefault={c.get('enumDefault')} "
              f"alias={c.get('alias')!r} ds={c.get('dataSource')} src={c.get('sourceControlId')}")
    names = [OL_INVOICE_LINES, IL_ORDER_LINES, O_INVOICES, I_ORDERS, O_INVOICE_COUNT, I_ORDER_COUNT]
    report_parked(names, {n: fields(WHERE[n]).get(n, {}) for n in names})


# ── the TEST fixture every later step is proved on ──────────────────────────
#
# Nothing is ever pressed or written on one of the app's own orders and invoices. `fixture` builds a
# TEST order with Odoo's four line kinds — a section, two product lines and a note — and, for the
# probes that run before Create Invoice exists, a TEST invoice with one line.

TEST_ORDER = 'TEST o2i order'                     # its Customer Reference; Orders' title is an auto Number
TEST_INVOICE = 'TEST o2i probe invoice'           # its Customer Reference
TEST_SECTION = 'TEST o2i section'
TEST_CHAIR = 'TEST o2i chair'
TEST_DESK = 'TEST o2i desk'
TEST_NOTE = 'TEST o2i note'
TEST_PROBE_LINE = 'TEST o2i probe line'
TEST_ORDER_LINES = (TEST_SECTION, TEST_CHAIR, TEST_DESK, TEST_NOTE)
# A second order that names **no Journal**, for the fallback of §14.9. Its own Journal is never filled, so
# `fixture` must not top it up — `order_want(journal=False)` leaves the key out altogether.
TEST_ORDER_NO_JOURNAL = 'TEST o2i order without a journal'
TEST_NJ_LINE = 'TEST o2i no-journal line'
RKEY = 'o2i: '                                    # ids.json `records` prefix for this bundle


def record_id(name):
    return hap.ids().get('records', {}).get(RKEY + name)


def read_record(ws, rowid):
    """One record through `record get`, which returns hidden fields the listing drops (CLAUDE.md)."""
    return hap.run('worksheet', 'record', 'get', ws, rowid, '-a', APP)['data']


def write_record(ws, rowid, values):
    body = json.dumps(values, ensure_ascii=False)
    if rowid:
        hap.run('worksheet', 'record', 'update', ws, rowid, '-a', APP, '--fields-json', body)
        return rowid
    return C.row_id(hap.run('worksheet', 'record', 'create', ws, '-a', APP, '--fields-json', body))


def cell(c, record):
    """A record's raw value for control `c`. `record get` keys a value by the control's alias when it has
    one and by its controlId otherwise (BUILDING.md)."""
    return record.get(c.get('alias') or c['controlId'])


def numeric(value):
    if value in (None, '', []):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


def title_row(ws, title):
    """The rowid of the record whose title field reads `title`, or None."""
    t = next(c for c in hap.controls(ws) if c.get('attribute') == 1)
    for r in C.records(ws, APP):
        if (r.get(t['controlId']) or '') == title:
            return r['rowid']
        got = cell(t, read_record(ws, r['rowid']))
        if got == title:
            return r['rowid']
    return None


def variant_row():
    """Any active product variant, for the TEST lines — read live, never an id written here."""
    vf = C.fields('6aa90c161204328eb1af1b82')
    rows = C.records('6aa90c161204328eb1af1b82', APP)
    display = vf['Display Name']['controlId']
    for r in rows:
        if (r.get(display) or '').startswith('[FURN-0003]'):
            return r['rowid'], r.get(display)
    return (rows[0]['rowid'], rows[0].get(display)) if rows else (None, None)


def sales_journal():
    jf = C.fields('6aa8f5191204328eb1af162a')
    name = jf['Journal Name']['controlId'] if 'Journal Name' in jf else \
        next(c['controlId'] for c in hap.controls('6aa8f5191204328eb1af162a') if c.get('attribute') == 1)
    for r in C.records('6aa8f5191204328eb1af162a', APP):
        if (r.get(name) or '') == 'Sales':
            return r['rowid']
    sys.exit('no Journal named Sales')


def unit_row():
    uf = C.fields('6aa8d14d4a73a3142152d3f6')
    name = next(c['controlId'] for c in hap.controls('6aa8d14d4a73a3142152d3f6') if c.get('attribute') == 1)
    for r in C.records('6aa8d14d4a73a3142152d3f6', APP):
        if (r.get(name) or '') == 'Units':
            return r['rowid']
    return None


TAX_10 = 'Taxes: MY|sale|consu|10% G'             # ids.json; a Sales tax, 10 %
CUSTOMER = 'Invoices: customer Sunway Construction Group'
TERM_45 = 'Payment Terms: 45 Days'


def order_want(f, today, reference=TEST_ORDER, journal=True):
    ids = hap.ids()['records']
    want = {
        'Status': [option_key(ORDERS, 'Status', 'Sales Order')],
        'Quotation/Order Date': f'{today} 09:00:00',
        'Tax Mode': [option_key(ORDERS, 'Tax Mode', 'Tax Excluded')],
        'Customer': [ids[CUSTOMER]],
        'Invoice Address': [ids[CUSTOMER]],
        'Delivery Address': [ids[CUSTOMER]],
        'Payment Terms': [ids[TERM_45]],
        'Customer Reference': reference,
        'Terms and conditions': '<p>TEST o2i terms.</p>',
        'Incoterm Location': 'TEST o2i place',
        'Salesperson': [me()],
    }
    if journal:
        want['Journal'] = [sales_journal()]
    return want


def me():
    """The account this CLI runs as — the fixture's Salesperson, which is required on an order."""
    d = read_record(ORDERS, [r['rowid'] for r in C.records(ORDERS, APP)][0])
    owner = d.get('_owner') or {}
    return owner.get('accountId')


def line_want(f, order_rowid, kind, label, seq, qty=None, price=None, variant=None, unit=None, tax=None):
    want = {'Orders': [order_rowid], 'Display Type': [option_key(OLINES, 'Display Type', kind)],
            'Description': label, 'Sequence': seq}
    if kind == 'Product':
        want.update({'Quantity': qty, 'Unit Price': price, 'Discount': 0})
        if variant:
            want['Product'] = [variant]
        if unit:
            want['Unit'] = [unit]
        if tax:
            want['Taxes'] = [tax]
    return want


def ensure_record(ws, key, want, match):
    """Create or top up one TEST record, matched by `match` (a rowid or None). Returns (rowid, created)."""
    f = fields(ws)
    rowid = record_id(key) or match
    if rowid:
        live = {r['rowid'] for r in C.records(ws, APP)}
        if rowid not in live:
            rowid = None
    if rowid:
        record = read_record(ws, rowid)
        # **Only empty cells are filled.** A value a test moved — a quantity pressed up to prove a partial
        # invoice — is left where the test left it, so re-running the fixture writes nothing.
        diff = {n: v for n, v in want.items()
                if not same(f[n], record, v) and cell(f[n], record) in (None, '', [], '0', 0)}
        kept = {n: cell(f[n], record) for n, v in want.items()
                if not same(f[n], record, v) and n not in diff}
        if diff:
            write_record(ws, rowid, [{'id': f[n]['controlId'], 'value': want[n]} for n in diff])
            print(f'  {NAME[ws]} / {key}: filled the empty {sorted(diff)}')
        if kept:
            print(f'  {NAME[ws]} / {key}: left as a test moved them — '
                  f'{json.dumps(kept, ensure_ascii=False, default=str)[:200]}')
        C.remember('records', RKEY + key, rowid)
        return rowid, False
    rowid = write_record(ws, None, [{'id': f[n]['controlId'], 'value': v} for n, v in want.items()
                                    if v not in ('', [], None)])
    C.remember('records', RKEY + key, rowid)
    print(f'  {NAME[ws]} / {key}: created {rowid}')
    return rowid, True


def same(c, record, want):
    got = cell(c, record)
    if c['type'] in (RELATION, SUBTABLE):
        ids = [v.get('sid') or v.get('rowid') for v in (json.loads(got) if isinstance(got, str) and got.startswith('[')
                                                        else got) or [] if isinstance(v, dict)]
        return ids == list(want or [])
    if c['type'] == DROPDOWN:
        keys = [v.get('key') for v in (got or []) if isinstance(v, dict)]
        return keys == list(want or [])
    if c['type'] == 26:                                       # a Member cell is a list of account objects
        return [v.get('accountId') for v in (got or []) if isinstance(v, dict)] == list(want or [])
    if c['type'] in (NUMBER, CURRENCY):
        return numeric(got) == numeric(want)
    if c['type'] == 16:                                       # a date-time comes back as the stored string
        return (got or '')[:10] == str(want)[:10]
    return (got or '') == (want or '')


def step_fixture():
    """The TEST order with its four lines, and the TEST invoice with one line. Re-running writes nothing."""
    guard()
    today = time.strftime('%Y-%m-%d')
    of, lf, inf, ilf = fields(ORDERS), fields(OLINES), fields(INVOICES), fields(ILINES)
    order, _ = ensure_record(ORDERS, TEST_ORDER, order_want(of, today), None)
    variant, variant_name = variant_row()
    unit = unit_row()
    tax = hap.ids()['records'][TAX_10]
    lines = [
        (TEST_SECTION, dict(kind='Section', label=TEST_SECTION, seq=10)),
        (TEST_CHAIR, dict(kind='Product', label=TEST_CHAIR, seq=20, qty=10, price=100, variant=variant,
                          unit=unit, tax=tax)),
        (TEST_DESK, dict(kind='Product', label=TEST_DESK, seq=30, qty=4, price=250, variant=variant,
                         unit=unit, tax=tax)),
        (TEST_NOTE, dict(kind='Note', label=TEST_NOTE, seq=40)),
    ]
    for key, kw in lines:
        ensure_record(OLINES, key, line_want(lf, order, **kw), title_row(OLINES, key))
    invoice_want = {
        'Type': [option_key(INVOICES, 'Type', 'Customer Invoice')],
        'Status': [option_key(INVOICES, 'Status', 'Draft')],
        'Accounting Date': today,
        'Journal': [sales_journal()],
        'Auto-post': [option_key(INVOICES, 'Auto-post', 'No')],
        'Customer Reference': TEST_INVOICE,
    }
    invoice, _ = ensure_record(INVOICES, TEST_INVOICE, invoice_want, None)
    probe_want = {'Invoice': [invoice], 'Display Type': [option_key(ILINES, 'Display Type', 'Product')],
                  'Label': TEST_PROBE_LINE, 'Sequence': 10, 'Quantity': 3, 'Unit Price': 100,
                  'Discount (%)': 0}
    ensure_record(ILINES, TEST_PROBE_LINE, probe_want, title_row(ILINES, TEST_PROBE_LINE))
    # the second order: everything the first has except a Journal
    nj, _ = ensure_record(ORDERS, TEST_ORDER_NO_JOURNAL,
                          order_want(of, today, reference=TEST_ORDER_NO_JOURNAL, journal=False), None)
    ensure_record(OLINES, TEST_NJ_LINE,
                  line_want(lf, nj, kind='Product', label=TEST_NJ_LINE, seq=10, qty=5, price=60,
                            variant=variant, unit=unit, tax=tax),
                  title_row(OLINES, TEST_NJ_LINE))
    print(f'  fixture: order {order} ({read_record(ORDERS, order).get("name")}), invoice {invoice}, '
          f'variant {variant_name!r}')
    print(f'  fixture: order with no journal {nj} ({read_record(ORDERS, nj).get("name")}), '
          f"its Journal reads {read_record(ORDERS, nj).get('journal_id')!r}")
    return order


# ── filters, the shape a 汇总 stores ────────────────────────────────────────
#
# A 汇总's own `advancedSetting.filters` is the worksheet filter shape, not a workflow's: a single
# select's "is" is `filterType` **51** and its "is not" **52** (hap_cli.filter_translator:120-130),
# where a business rule writes 2 and 6. A type-30 lookup of a single select is read by the editors as
# its **source** type, 11, and compares the source worksheet's option keys (BUILDING.md).

EQ_SINGLE, NE_SINGLE = 51, 52
EQ_NUMBER, GT_NUMBER = 2, 13


def flt(control_id, data_type, filter_type, values=(), value=''):
    return {'controlId': control_id, 'dataType': data_type, 'spliceType': 1, 'filterType': filter_type,
            'dateRange': 0, 'dateRangeType': 0, 'value': value, 'values': list(values), 'minValue': '',
            'maxValue': '', 'isAsc': False, 'dynamicSource': [], 'advancedSetting': None, 'isGroup': False,
            'groupFilters': None, 'emptyRule': 0}


def filters_json(items):
    return json.dumps(items, ensure_ascii=False)


def filter_state(value):
    """A 汇总's filter reduced to what it means — (control, dataType, filterType, values, value)."""
    try:
        items = json.loads(value) if isinstance(value, str) and value else (value or [])
    except ValueError:
        return value
    return [(i.get('controlId'), i.get('dataType'), i.get('filterType'),
             tuple(i.get('values') or []), i.get('value') or '') for i in items or []]


def rollup_control(name, via_id, source_control_id, aggregate, items=(), dot=2):
    row, col, size, _ = PLACE[name]
    adv = {'filters': filters_json(list(items))} if items else {}
    c = C.control('SUBTOTAL', name, (row, col, size), alias=ALIAS[name], hint='', desc=DESC[name],
                  data_source=via_id, source_control_id=source_control_id,
                  advanced_setting=adv or None, extra={'enumDefault': aggregate, 'dot': dot})
    c['fieldPermission'] = PERM[name]
    return c


def rollup_spec(name, via_id, source_control_id, aggregate, dot=2):
    return {'type': ROLLUP, 'alias': ALIAS[name], 'desc': DESC[name], 'fieldPermission': PERM[name],
            'dataSource': f'${via_id}$', 'sourceControlId': source_control_id, 'enumDefault': aggregate,
            'dot': dot}


def ensure_rollups(ws, wanted, backup, step):
    """Append the 汇总 that are missing, then bring every one's shape and filter to `wanted` in one pinned
    save. `wanted` is {name: (via, source, aggregate, filter items, dot)}."""
    live = fields(ws)
    missing = [n for n in wanted if n not in live]
    if missing:
        C.append_checked(ws, [rollup_control(n, *wanted[n][:3], items=wanted[n][3], dot=wanted[n][4])
                              for n in missing], backup, step)
        live = fields(ws)
    else:
        print(f'  {list(wanted)} are already on {NAME[ws]}; nothing appended')
    spec = {}
    for n, (via, source, agg, items, dot) in wanted.items():
        want = rollup_spec(n, via, source, agg, dot)
        stale = C.drift(live[n], want)
        if stale:
            spec.setdefault(live[n]['controlId'], {}).update({k: want[k] for k in stale})
        got = filter_state((live[n].get('advancedSetting') or {}).get('filters'))
        if got != filter_state(list(items)):
            print(f'  {n}.filters: {got} -> {filter_state(list(items))}')
            spec.setdefault(live[n]['controlId'], {})['advancedSetting.filters'] = \
                filters_json(list(items)) if items else ''
    if spec:
        C.pinned_write(ws, spec, backup + '_repair', step)
        live = fields(ws)
    else:
        print(f'  {list(wanted)} already as specified; nothing saved')
    for n in wanted:
        remember(n, live[n]['controlId'])
        c = live[n]
        print(f"  OK  {NAME[ws]} / {n:<22} {c['controlId']} t{c['type']} agg={c.get('enumDefault')} "
              f"dot={c.get('dot')} ds={c.get('dataSource')} src={c.get('sourceControlId')} "
              f"filters={filter_state((c.get('advancedSetting') or {}).get('filters'))}")
    return live


# ── 3 · the quantity roll-ups, and Quantity Invoiced as a Formula ───────────
#
# Odoo `sale_order_line.py:984-1017`: `qty_invoiced` is the sum over `invoice_lines` of the quantity,
# **plus** for an `out_invoice` and **minus** for an `out_refund`, skipping only lines whose move is
# cancelled — so a **draft** invoice already counts. HAP has no signed aggregate, so it is two 汇총 and
# a subtraction: one over customer invoices, one over customer credit notes, both excluding cancelled
# documents, and Quantity Invoiced is their difference.

IL_QUANTITY = '6aaa2b81e54d2a34fa4e022f'          # Invoice Lines / Quantity
IL_STATUS = '6aaa2c18e43d174ab3749df4'            # Invoice Lines / Status, a lookup of the invoice's Status
IL_SUBTOTAL = '6aaa2c18e43d174ab3749df1'          # Invoice Lines / Subtotal
OL_QUANTITY = '6ab0c864e43d174ab37535fb'
OL_QTY_DELIVERED = '6ab0c864e43d174ab37535fd'
OL_QTY_INVOICED = '6ab0c864e43d174ab37535fc'
OL_DISPLAY_TYPE = '6ab0c864e43d174ab37535f7'
OL_DESCRIPTION = '6ab0c864e43d174ab37535fa'       # Order Lines' title — what a count 汇총 names
O_SUBTABLE = '6ab0c740e43d174ab37535b0'           # Orders / Order Lines, the 子表 the counts travel
FORMULA_SETTING = {'roundtype': '2', 'sorttype': 'zh', 'nullzero': '1'}
# What Quantity Invoiced carries as a Number and a Formula does not.
NUMBER_ONLY = ('showtype', 'thousandth', 'min', 'max', 'numshow', 'defsource', 'defaulttype', 'defaultfunc')


def qty_wanted():
    """The two working 汇총 of §6.1, read against the live option keys."""
    il, ol = fields(ILINES), fields(OLINES)
    via = ol[OL_INVOICE_LINES]['controlId']
    doc_type = il[DOC_TYPE]['controlId']
    cancelled = option_key(INVOICES, 'Status', 'Cancelled')
    invoice = option_key(INVOICES, 'Type', 'Customer Invoice')
    credit = option_key(INVOICES, 'Type', 'Customer Credit Note')
    not_cancelled = flt(IL_STATUS, DROPDOWN, NE_SINGLE, [cancelled])
    return {
        QTY_INVOICES: (via, IL_QUANTITY, 5, [not_cancelled, flt(doc_type, DROPDOWN, EQ_SINGLE, [invoice])], 2),
        QTY_REFUNDS: (via, IL_QUANTITY, 5, [not_cancelled, flt(doc_type, DROPDOWN, EQ_SINGLE, [credit])], 2),
    }


def qty_invoiced_spec(live):
    """Quantity Invoiced as a Formula: the two roll-ups subtracted, Invoice Lines' own Formula shape."""
    expression = f"${live[QTY_INVOICES]['controlId']}$-${live[QTY_REFUNDS]['controlId']}$"
    spec = {'type': FORMULA, 'alias': 'qty_invoiced', 'fieldPermission': READONLY, 'dot': 2,
            'enumDefault': 0, 'enumDefault2': 0, 'dataSource': expression, 'unit': ''}
    spec.update({f'advancedSetting.{k}': v for k, v in FORMULA_SETTING.items()})
    return spec


def step_qty():
    """Qty on invoices, Qty on credit notes, and **Quantity Invoiced converted in place from a Number
    (type 6) to a Formula (type 31)**.

    The conversion keeps the control id, so the section rule, the subtable's columns and every alias reader
    go on working — the move Tax Amount and Total on this very worksheet already made on 21 Sep 2026. It
    **discards whatever is typed in Quantity Invoiced on the existing lines**: a Formula cannot be typed
    into. Those values are read into the backup before the save so they can be quoted afterwards."""
    live = guard()
    wanted = qty_wanted()
    ol = ensure_rollups(OLINES, wanted, 'o2i_orderlines_pre_qty', 'qty')
    want = qty_invoiced_spec(ol)
    surplus = {k: v for k, v in (ol[QTY_INVOICED].get('advancedSetting') or {}).items()
               if k not in FORMULA_SETTING and k not in NUMBER_ONLY and v}
    if surplus:
        sys.exit(f'{QTY_INVOICED} carries advancedSetting {surplus} that a Formula does not and this step '
                 'was not told to drop — stopping rather than discarding them')
    stale = C.drift(ol[QTY_INVOICED], want)
    if not stale:
        print(f'  {QTY_INVOICED} is already a Formula as specified; nothing saved')
    else:
        typed = typed_quantities()
        path = hap.backup('o2i_orderlines_quantity_invoiced_typed_values', typed)
        filled = {k: v for k, v in typed.items() if v not in (None, 0.0)}
        print(f'  {QTY_INVOICED} is t{ol[QTY_INVOICED]["type"]} on {len(typed)} lines; '
              f'{len(filled)} carry a value. Backed up to {path}')
        if filled:
            print('    ' + json.dumps(filled, ensure_ascii=False))
        ctrls, version = C.controls_with_version(OLINES)
        by_id = {c['controlId']: c for c in ctrls}
        before = C.control_signature(ctrls)
        hap.backup('o2i_orderlines_pre_conversion', ctrls)
        c = by_id[OL_QTY_INVOICED]
        c['advancedSetting'] = dict(FORMULA_SETTING)               # the Number's own keys go with the type
        for key, value in want.items():
            if key.startswith('advancedSetting.'):
                continue
            c[key] = value
        C.save_controls(OLINES, ctrls, version=version)
        after = C.control_signature(hap.controls(OLINES))
        changed = C.changed_ids(before, after)
        if changed != [OL_QTY_INVOICED]:
            names = {x['controlId']: x['controlName'] for x in hap.controls(OLINES)}
            sys.exit(f'qty: the conversion changed {[names.get(k, k) for k in changed]}, wanted only '
                     f'{QTY_INVOICED}')
        ol = fields(OLINES)
        left = C.drift(ol[QTY_INVOICED], want)
        if left:
            sys.exit(f'{QTY_INVOICED} read back with differences {json.dumps(left, ensure_ascii=False)}')
        print(f'  {QTY_INVOICED}: type 6 -> 31, expression {want["dataSource"]}')
    still = {k: v for k, v in (ol[QTY_INVOICED].get('advancedSetting') or {}).items()
             if k in ('defaulttype', 'defaultfunc', 'defsource') and v}
    if still:
        sys.exit(f'{QTY_INVOICED} still carries a default {still} — a Formula must carry none')
    c = ol[QTY_INVOICED]
    print(f"  OK  Order Lines / {QTY_INVOICED:<22} {c['controlId']} t{c['type']} perm={c['fieldPermission']} "
          f"dot={c['dot']} ds={c['dataSource']} adv="
          f"{json.dumps(c.get('advancedSetting'), ensure_ascii=False, sort_keys=True)}")
    check_subtable_columns()
    report_parked([QTY_INVOICES, QTY_REFUNDS], ol)


def typed_quantities():
    """{order line rowid: its Quantity Invoiced} before the conversion — the only copy of those figures."""
    out = {}
    c = fields(OLINES)[QTY_INVOICED]
    for r in C.records(OLINES, APP):
        out[r['rowid']] = numeric(r.get(c['controlId']))
    return out


def check_subtable_columns():
    """Quantity Invoiced is still a column of the Orders subtable, and the section rule still hides it."""
    sub = next(c for c in hap.controls(ORDERS) if c['controlId'] == O_SUBTABLE)
    if OL_QTY_INVOICED not in (sub.get('showControls') or []):
        sys.exit(f'{QTY_INVOICED} is no longer a column of the Orders subtable')
    rule = next((r for r in hap.listing('worksheet', 'rules', OLINES)
                 if any(x['controlId'] == OL_QTY_INVOICED for i in r['ruleItems'] for x in i['controls'])), None)
    if rule is None:
        sys.exit(f'no Order Lines rule names {QTY_INVOICED} any more')
    print(f"  OK  {QTY_INVOICED} is still a column of the Orders subtable and still a target of "
          f"{rule['name']!r}")


# ── 4 · Quantity To Invoice, the line's status, and the five counts ─────────
#
# Odoo `sale_order_line.py:1048-1075`: `qty_to_invoice` is `product_uom_qty − qty_invoiced` when the
# product's `invoice_policy` is `order` — which is every line here, because Products has no Invoicing
# Policy control and `order` is Odoo's default — and **0** when the order is not confirmed or the line
# has a display type. `invoice_status` (`:1078-1104`) is a five-test ladder; it becomes a number
# 0 nothing · 1 to invoice · 2 invoiced · 3 upselling, in Odoo's own test order.
#
# Both are **function formulas (type 53)**, not function *defaults*: a default is evaluated in the
# browser and would store empty on every API write, and Quantity Invoiced is a 汇총 that has no value
# while the form is open (CLAUDE.md › Computation).

TEXT_RESULT, NUMBER_RESULT = 2, 6                 # a function formula's enumDefault2
FUNCTION_SETTING = {'analysislink': '1', 'sorttype': 'en'}
PLACEHOLDER = '0'                                 # what a new function formula is appended carrying


def function_source(expression):
    """dataSource of a function formula (type 53), as contacts.py, prodcat.py and incoterms.py write it."""
    return json.dumps({'type': 'mdfunction', 'expression': expression, 'status': 1}, ensure_ascii=False)


def function_expression(c):
    raw = (c or {}).get('dataSource') or ''
    try:
        return json.loads(raw).get('expression')
    except ValueError:
        return raw


def function_control(name, expression, result=NUMBER_RESULT, dot=2):
    row, col, size, _ = PLACE[name]
    c = C.control('FORMULA_FUNC', name, (row, col, size), alias=ALIAS[name], hint='', desc=DESC[name],
                  advanced_setting=dict(FUNCTION_SETTING),
                  extra={'enumDefault2': result, 'dot': dot, 'dataSource': function_source(expression)})
    c['fieldPermission'] = PERM[name]
    return c


def function_spec(name, expression, result=NUMBER_RESULT, dot=2):
    spec = {'type': FUNCTION, 'alias': ALIAS[name], 'desc': DESC[name], 'fieldPermission': PERM[name],
            'enumDefault2': result, 'dot': dot, 'dataSource': function_source(expression)}
    spec.update({f'advancedSetting.{k}': v for k, v in FUNCTION_SETTING.items()})
    return spec


def to_invoice_expression(ol):
    """Odoo `_compute_qty_to_invoice`: the ordered quantity less what is invoiced, and 0 unless the order is
    confirmed and the line is a product line.

    A worksheet function formula renders a dropdown — and a **stored lookup of** a dropdown — as its
    **label**, which is what these two comparisons stand on (measured on the TEST order, 23 Sep 2026)."""
    state = f"${ol[ORDER_STATE]['controlId']}$"
    kind = f'${OL_DISPLAY_TYPE}$'
    return (f'IF({state} == "Sales Order" && {kind} == "Product", '
            f'${OL_QUANTITY}$-${OL_QTY_INVOICED}$, 0)')


def line_status_expression(ol):
    """Odoo `_compute_invoice_status` on the line (`sale_order_line.py:1078-1104`), in its own test order,
    as a number: 0 nothing to invoice · 1 to invoice · 2 invoiced · 3 upselling.

    The down-payment test (`is_downpayment and untaxed_amount_to_invoice == 0` -> invoiced) is skipped:
    this bundle builds no down payments. The invoicing-policy test in Odoo's upselling branch is always
    true here — Products has no Invoicing Policy, so every line is *Ordered quantities* (21 §3.5)."""
    state = f"${ol[ORDER_STATE]['controlId']}$"
    kind = f'${OL_DISPLAY_TYPE}$'
    to_inv = f"${ol[QTY_TO_INVOICE]['controlId']}$"
    qty, delivered, invoiced = f'${OL_QUANTITY}$', f'${OL_QTY_DELIVERED}$', f'${OL_QTY_INVOICED}$'
    return (f'IF({state} != "Sales Order" || {kind} != "Product", 0, '
            f'IF({to_inv} != 0, 1, '
            f'IF({qty} >= 0 && {delivered} > {qty}, 3, '
            f'IF({invoiced} >= {qty}, 2, 0))))')


def invoiceable_expression(ol):
    """1 when Create Invoice must take this line, 0 when it must not — Odoo's `_get_invoiceable_lines`
    (`sale_order.py:1501-1550`) reduced to one number per line.

    **This control is not in 21's spec, and it is here because HAP's workflow filter has no OR.** A get-records
    step's filter is one AND list: its wrapper `spliceType` joins *every* condition, and a filter sent as two
    groups with `spliceType` 2 OR-ed the conditions themselves — which on 23 Sep 2026 made Create Invoice's
    get-multiple return **every order line in the app**, not this order's. `batch-add` refuses the OR outright
    (`筛选条件配置不正确`) and `node save --type 13` accepts it and then does not mean it. So the OR lives here,
    in one formula on the line, and the step's filter is a flat AND: *this order's lines where Invoiceable line
    is 1*. It also makes the section behaviour of §12.4 a single expression the owner can change."""
    state = f"${ol[ORDER_STATE]['controlId']}$"
    kind = f'${OL_DISPLAY_TYPE}$'
    to_inv = f"${ol[QTY_TO_INVOICE]['controlId']}$"
    display = ' || '.join(f'{kind} == "{k}"' for k in ('Section', 'Subsection', 'Note'))
    return (f'IF({kind} == "Product", '
            f'IF({state} == "Sales Order" && {to_inv} > 0, 1, 0), '
            f'IF({display}, 1, 0))')


COUNT_OF = {N_TO_INVOICE: 1, N_NOTHING: 0, N_INVOICED: 2, N_UPSELLING: 3, N_PRODUCT: None}


def count_wanted():
    """The five filtered counts of §6.2 over the Orders 子表."""
    ol = fields(OLINES)
    product = option_key(OLINES, 'Display Type', 'Product')
    is_product = flt(OL_DISPLAY_TYPE, DROPDOWN, EQ_SINGLE, [product])
    status_id = ol[LINE_STATUS]['controlId']
    out = {}
    for name, value in COUNT_OF.items():
        items = [is_product]
        if value is not None:
            # a function formula is read by the editors as its **result** type, so a number (6)
            items = items + [flt(status_id, NUMBER, EQ_NUMBER, [str(value)], str(value))]
        out[name] = (O_SUBTABLE, OL_DESCRIPTION, 6, items, 0)
    return out


def step_toinvoice():
    """Quantity To Invoice and Line Invoice Status on Order Lines, the five counts on Orders, and Quantity
    To Invoice added to the Orders subtable grid.

    Adding a control to a worksheet does not add it to the 子表 grid — a row panel draws the *subtable's*
    `showControls` — so Quantity To Invoice is invisible from inside an order until the Orders subtable
    lists it. That goes in with `advancedSetting.controlssorts`, in the same pinned save."""
    live = guard()
    ol = live[OLINES]
    for name, expression in ((QTY_TO_INVOICE, to_invoice_expression), (LINE_STATUS, line_status_expression),
                             (INVOICEABLE, invoiceable_expression)):
        if name not in ol:
            # Appended with the placeholder `0`, so the pinned save below always writes the real expression.
            # **A function formula added with add-fields computes nothing until a full save** — measured
            # 23 Sep 2026: both of these were appended carrying their final expression, read back exactly as
            # sent, and stored empty on all 41 lines; the first pinned save that changed the expression filled
            # every one within seconds. (A 汇总 appended the same way computes at once — Product lines did.)
            C.append_checked(OLINES, [function_control(name, PLACEHOLDER)],
                             'o2i_orderlines_pre_toinvoice', f'toinvoice/{name}')
            ol = fields(OLINES)
        want = function_spec(name, expression(ol), dot=0 if name != QTY_TO_INVOICE else 2)
        stale = C.drift(ol[name], want)
        if stale:
            if 'dataSource' in stale:
                print(f'  {name} expression:\n      was {function_expression(ol[name])}\n'
                      f'      now {expression(ol)}')
            C.pinned_write(OLINES, {ol[name]['controlId']: {k: want[k] for k in stale}},
                           'o2i_orderlines_pre_toinvoice_repair', f'toinvoice/{name}')
            ol = fields(OLINES)
        else:
            print(f'  Order Lines / {name} already as specified; nothing saved')
        remember(name, ol[name]['controlId'])
        c = ol[name]
        print(f"  OK  Order Lines / {name:<20} {c['controlId']} t{c['type']} result={c.get('enumDefault2')} "
              f"dot={c.get('dot')} perm={c.get('fieldPermission')}\n          {function_expression(c)}")
    for name, expression in ((QTY_TO_INVOICE, to_invoice_expression), (LINE_STATUS, line_status_expression),
                             (INVOICEABLE, invoiceable_expression)):
        nudge_formula(name, expression)
    ensure_rollups(ORDERS, count_wanted(), 'o2i_orders_pre_counts', 'toinvoice/counts')
    ensure_subtable_column(fields(OLINES)[QTY_TO_INVOICE]['controlId'])
    names = [QTY_TO_INVOICE, LINE_STATUS, INVOICEABLE] + list(COUNT_OF)
    report_parked(names, {n: fields(WHERE[n]).get(n, {}) for n in names})


def nudge_formula(name, expression):
    """Make sure the formula has actually **computed**, and force a recompute when it has not.

    A function formula appended with `add-fields` reads back exactly as sent and stores nothing until a full
    save changes it. The test is the TEST order's chair line, where the answer cannot legitimately be empty:
    a confirmed order, a product line, a Quantity. Re-running a computed formula nudges nothing."""
    ol = fields(OLINES)
    rowid = record_id(TEST_CHAIR)
    if not rowid:
        print(f'  {name}: no TEST fixture to prove the formula on — run `fixture`')
        return False
    got = cell(ol[name], read_record(OLINES, rowid))
    if got not in (None, ''):
        print(f'  {name} computes: {TEST_CHAIR} reads {got!r}')
        return False
    print(f'  {name} stored nothing on {TEST_CHAIR} — forcing a recompute with one pinned save')
    cid = ol[name]['controlId']
    C.pinned_write(OLINES, {cid: {'dataSource': function_source(PLACEHOLDER)}},
                   'o2i_orderlines_pre_nudge', f'toinvoice/{name} nudge')
    C.pinned_write(OLINES, {cid: {'dataSource': function_source(expression(fields(OLINES)))}},
                   'o2i_orderlines_pre_nudge', f'toinvoice/{name}')
    time.sleep(6)
    got = cell(fields(OLINES)[name], read_record(OLINES, rowid))
    if got in (None, ''):
        sys.exit(f'{name} still stores nothing on {TEST_CHAIR} after a forced recompute')
    print(f'  {name} computes: {TEST_CHAIR} reads {got!r}')
    return True


def ensure_subtable_column(control_id):
    """Quantity To Invoice as a column of the Orders 子表, right after Quantity Invoiced — `showControls`
    and `advancedSetting.controlssorts` in one pinned save."""
    sub = next(c for c in hap.controls(ORDERS) if c['controlId'] == O_SUBTABLE)
    columns = list(sub.get('showControls') or [])
    if control_id in columns:
        print(f'  {QTY_TO_INVOICE} is already a column of the Orders subtable; nothing saved')
        return False
    at = columns.index(OL_QTY_INVOICED) + 1 if OL_QTY_INVOICED in columns else len(columns)
    columns.insert(at, control_id)
    C.pinned_write(ORDERS, {O_SUBTABLE: {'showControls': columns,
                                         'advancedSetting.controlssorts': json.dumps(columns)}},
                   'o2i_orders_pre_subtable_column', 'toinvoice/subtable column')
    back = next(c for c in hap.controls(ORDERS) if c['controlId'] == O_SUBTABLE)
    if (back.get('showControls') or []) != columns:
        sys.exit(f'the Orders subtable columns read back {back.get("showControls")}, wanted {columns}')
    print(f'  {QTY_TO_INVOICE} added to the Orders subtable grid at position {at} of {len(columns)}')
    return True


# ── workflow plumbing ───────────────────────────────────────────────────────
#
# The shapes a workflow node actually stores, as invoices.py:906-1077 and orders.py:3600-4000 established:
# `batch-add` writes a search step's filter as `operateCondition`, which the UI never reads, and drops a
# branch path's name and condition; a dropdown is written as its bare option key; a formula node's numeric
# result binds only from a number formula (100) or a worksheet total (107).

UPDATE_NODE, GET_ONE, FORMULA_NODE, GET_MANY = 6, 7, 9, 13
FROM_SHEET_ONE, FROM_WORKSHEET, NUMBER_FORMULA, FUNCTION_FORMULA, WORKSHEET_TOTAL = '406', '400', '100', '106', '107'
NUMBER_FX, STRING_FX = 'number_fx_id', 'string_fx_id'
IS_ANY_OF, NOT_ANY_OF, EQ_C, GTE_C, LT_C, EMPTY_C, NOT_EMPTY_C = '1', '2', '9', '14', '11', '8', '7'
RELATION_EQ = '33'
CREATE_OR_UPDATE, DELETE_EVENT = '2', '3'
MONEY_DOT = 2


def published_status(pid):
    w = hap.run('workflow', 'get', pid)
    w = w.get('data', w) if isinstance(w, dict) else {}
    return w.get('publishStatus')


def read_node(pid, node_id):
    d = hap.run('workflow', 'node', 'get', pid, node_id)
    return d.get('data', d) if isinstance(d, dict) else {}


def nodes_by_name(pid):
    proc = hap.run('workflow', 'node', 'list', pid)
    return proc, {n['name']: n for n in proc['flowNodeMap'].values()}


def workflow_id(name):
    pid = hap.ids().get('workflows', {}).get(name)
    if pid:
        return pid
    live = {w['name']: (w.get('id') or w.get('processId')) for w in hap.listing('workflow', 'list', APP)}
    return live.get(name)


def ensure_workflow(name, desc):
    """The worksheet-event workflow `name`, created if it is not there. `hap workflow create` can time out
    having created it, so it is always looked up by name first (BUILDING.md)."""
    pid = workflow_id(name)
    if not pid:
        out = hap.run('workflow', 'create', '-c', ORG, '-a', APP, '-n', name, '--type', 'worksheet', '-d', desc)
        data = out.get('data', out) if isinstance(out, dict) else {}
        pid = data.get('processId') or data.get('id')
        if not pid:
            sys.exit(f'{name}: no processId in `workflow create` output: {out}')
        print(f'  created {name}: {pid}')
    C.remember('workflows', name, pid)
    return pid


def trigger_state(t):
    return (t.get('appId'), str(t.get('triggerId')), sorted(t.get('assignFieldIds') or []), t.get('name'))


def sync_trigger(pid, start, name, worksheet, event, trigger_fields):
    """The trigger's worksheet, event and field narrowing, rewritten only when they differ.

    A 新增或更新 trigger narrowed to fields fires on a create only when the create writes one of them, and on
    an update whenever one of them is in the write, changed or not (BUILDING.md). That is exactly Odoo's own
    `modified(vals)` behaviour for a stored compute."""
    want = (worksheet, event, sorted(trigger_fields), name)
    got = trigger_state(read_node(pid, start))
    if got == want:
        return False
    if got[:3] == want[:3]:                            # only the name differs — `batch-add` names a worksheet
        hap.run('workflow', 'node', 'rename', pid, start, '-n', name)   # trigger 工作表事件触发 (BUILDING.md)
        if trigger_state(read_node(pid, start)) != want:
            sys.exit(f'{name}: the trigger read back {trigger_state(read_node(pid, start))}, wanted {want}')
        print(f'  {name}: trigger renamed')
        return True
    hap.backup(f'o2i_workflow_{pid}_trigger', read_node(pid, start))
    hap.run('workflow', 'node', 'save', pid, start, '--type', '0', '-n', name, '-c', json.dumps(
        {'appId': worksheet, 'appType': 1, 'triggerId': event, 'assignFieldIds': list(trigger_fields),
         'operateCondition': [], 'returns': []}, ensure_ascii=False))
    back = trigger_state(read_node(pid, start))
    if back != want:
        hap.run('workflow', 'rollback', pid, '-y')
        sys.exit(f'{name}: the trigger read back {back}, wanted {want}; the draft was rolled back')
    print(f'  {name}: trigger rewritten to {want}')
    return True


def wf_filter_state(filters_):
    out = []
    for flt_ in filters_ or []:
        for g in flt_.get('conditions') or []:
            for c in g:
                vals = []
                for v in c.get('conditionValues') or []:
                    value = v.get('value')
                    if isinstance(value, dict):
                        value = value.get('key')
                    vals.append((v.get('nodeId') or '', v.get('controlId') or '', value or ''))
                out.append((c.get('filedId'), str(c.get('conditionId')), tuple(vals)))
    return out


def sync_search(pid, node, worksheet, conditions, kind=GET_ONE, action=FROM_SHEET_ONE, execute_type=0,
                execute=None, sorts=None, splice=1):
    """`conditions` is one AND-group, or a list of AND-groups OR-ed together.

    **The OR lives here, not in `batch-add`.** A `get_multiple` sent an OR-of-AND filter through
    `batch-add --nodes` is refused outright — `flowNode/batchAdd` answers `筛选条件配置不正确` — because that
    call sends the filter as `operateCondition`, which is a single AND list. `node save --type 13` sends
    `filters`, whose `conditions` **is** a list of AND-groups, and takes it (measured 23 Sep 2026). So a search
    step with an OR is built with a flat filter and given the real one here."""
    groups = conditions if conditions and isinstance(conditions[0], list) else [conditions]
    got = read_node(pid, node['id'])
    # **The wrapper `spliceType` joins every condition the step holds**: 1 AND, 2 OR. It is compared, not
    # ignored — a two-condition filter saved with 2 is an OR, which is how *Find the invoice just made* came to
    # read "this order's Source Document **or** any draft".
    live_splice = [f.get('spliceType') for f in got.get('filters') or []]
    same = (wf_filter_state(got.get('filters')) == wf_filter_state([{'conditions': groups}])
            and live_splice == [splice]
            and got.get('appId') == worksheet
            and (kind != GET_ONE or got.get('executeType') == execute_type)
            and (execute is None or bool(got.get('execute')) == execute))
    if same:
        return False
    cfg = {'actionId': action, 'appId': worksheet, 'appType': 1, 'selectNodeId': '',
           'filters': [{'spliceType': splice, 'conditions': groups}], 'operateCondition': []}
    if kind == GET_ONE:
        cfg['sorts'] = sorts or got.get('sorts') or [{'controlId': 'ctime', 'controlType': 16, 'isAsc': True}]
        cfg['executeType'] = execute_type
    else:
        cfg['execute'] = True if execute is None else execute
        if sorts:
            cfg['sorts'] = sorts
    hap.run('workflow', 'node', 'save', pid, node['id'], '--type', str(kind), '-n', node['name'],
            '-c', json.dumps(cfg, ensure_ascii=False))
    back = read_node(pid, node['id'])
    if wf_filter_state(back.get('filters')) != wf_filter_state([{'conditions': groups}]) \
            or [f.get('spliceType') for f in back.get('filters') or []] != [splice] \
            or back.get('appId') != worksheet:
        sys.exit(f"{node['name']}: filter reads back {wf_filter_state(back.get('filters'))}, wanted "
                 f"{wf_filter_state([{'conditions': groups}])} — `hap workflow rollback {pid} -y` restores "
                 'the published version')
    return True


def sync_number_formula(pid, node, expression):
    """A number formula node (actionId 100): its expression, two decimals and `nullZero`.

    `number` is the node's **decimal places** and defaults to 0; `nullZero` is "treat an empty input as 0" and
    defaults to false, which makes the whole expression compute empty as soon as one input is empty
    (BUILDING.md, and invlines.set_formula)."""
    want = {'formulaValue': expression, 'number': MONEY_DOT, 'nullZero': True}
    got = read_node(pid, node['id'])
    if all(got.get(k) == v for k, v in want.items()):
        return False
    hap.run('workflow', 'node', 'save', pid, node['id'], '--type', str(FORMULA_NODE), '-n', node['name'],
            '-c', json.dumps({'actionId': NUMBER_FORMULA, 'name': node['name'], 'execute': True,
                              'formulaValue': expression, 'number': MONEY_DOT, 'nullZero': True,
                              'type': NUMBER}, ensure_ascii=False))
    back = read_node(pid, node['id'])
    if any(back.get(k) != v for k, v in want.items()):
        sys.exit(f"{node['name']}: read back {[(k, back.get(k)) for k in want]}, wanted {want}")
    return True


def cond(node_id, field, condition_id, values=None):
    """One workflow condition on `field` of the record node `node_id` produced."""
    return {'nodeId': node_id, 'filedId': field['controlId'], 'filedValue': field['controlName'],
            'filedTypeId': field['type'], 'conditionId': condition_id, 'sourceType': 0,
            'conditionValues': values or []}


def fx_cond(node_id, condition_id, value):
    """One condition on a formula node's own numeric result."""
    return {'nodeId': node_id, 'filedId': NUMBER_FX, 'filedValue': '', 'filedTypeId': NUMBER,
            'conditionId': condition_id, 'sourceType': 0, 'conditionValues': [{'value': str(value)}]}


def option_values(control, labels):
    by_label = {o['value']: o['key'] for o in control.get('options') or []}
    missing = [x for x in labels if x not in by_label]
    if missing:
        sys.exit(f"{control['controlName']} has no option(s) {missing}")
    return [{'value': {'key': by_label[x], 'value': x, 'isDeleted': False}} for x in labels]


def condition_state(group):
    """One AND-group of path conditions as (the node it reads, the field, the operator, the values compared).

    **`nodeId` belongs in it**: the four status paths compare the same `number_fx_id` with the same operator
    and differ only in which formula node they read, so a comparison that left the node out would call two
    different paths identical and never notice a wrong binding."""
    return [(c.get('nodeId') or '', c.get('filedId'), str(c.get('conditionId')),
             tuple(sorted((v.get('value') or {}).get('key') if isinstance(v.get('value'), dict)
                          else str(v.get('value') or '') for v in c.get('conditionValues') or [])))
            for c in group]


def path_state(d):
    return [condition_state(g) for g in d.get('conditions') or []]


def save_path(pid, path, name, conditions):
    """A branch path's name and condition. `node get` returns them as `conditions`; `node save --type 2` wants
    `operateCondition`, and neither `batch-add` nor `node save -n` sets the name — that needs `node rename`."""
    got = read_node(pid, path['id'])
    want = [condition_state(g) for g in conditions]
    changed = path_state(got) != want
    if changed:
        hap.run('workflow', 'node', 'save', pid, path['id'], '--type', '2',
                '-c', json.dumps({'operateCondition': conditions}, ensure_ascii=False), '-n', name)
        if path_state(read_node(pid, path['id'])) != want:
            sys.exit(f'{name}: the path condition read back {path_state(read_node(pid, path["id"]))}, '
                     f'wanted {want}')
    if got.get('name') != name:
        hap.run('workflow', 'node', 'rename', pid, path['id'], '-n', name)
        changed = True
    return changed


def paths_of(proc, gateway_id):
    """A gateway's paths in the order its `flowIds` lists them."""
    gateway = proc['flowNodeMap'][gateway_id]
    order = gateway.get('flowIds') or []
    paths = {n['id']: n for n in proc['flowNodeMap'].values()
             if n.get('typeId') == 2 and n.get('prveId') == gateway_id}
    out = [paths[i] for i in order if i in paths]
    return out + [p for i, p in paths.items() if i not in order]


def patch(field_id, kind, value='', node='', source='', system=False):
    """One field write for a create or update step, in the shape the server stores (invoices.patch)."""
    wire = {'fieldId': field_id, 'type': kind, 'addType': 0, 'fieldValue': value, 'fieldValueId': '', 'nodeId': ''}
    if system:
        wire.update(nodeId=SYSTEM_NODE, sureNodeId=SYSTEM_NODE, fieldValueId=source, nodeTypeId=100,
                    nodeAppType=100)
    elif node and kind == TEXT:
        wire['fieldValue'] = f'${node}-{source}$'
    elif node:
        wire.update(nodeId=node, sureNodeId=node, fieldValueId=source, nodeAppType=1)
    return wire


SYSTEM_NODE = '5d39140d381d42d20db0c4da'          # the fixed 系统 node: current time, trigger time, trigger user


def write_state(entry):
    """A field write reduced to what it means. `nodeAppType` is left out: the server rewrites it (11 for a
    formula result, whatever was sent), so a step that compared it would re-save for ever (BUILDING.md)."""
    return (entry.get('fieldId'), entry.get('type'), entry.get('addType') or 0, entry.get('fieldValue') or '',
            entry.get('fieldValueId') or '', entry.get('nodeId') or '')


def set_entries(pid, node, wanted, select_node, worksheet):
    """Give a create or update step these field writes, keeping its other configuration. `select_node` must
    name a node that produces a record — the trigger or a search step; pointed at another update step the node
    comes back `isException: true` with no fields at all (BUILDING.md)."""
    d = read_node(pid, node['id'])
    entries = list(d.get('fields') or [])
    changed = bool(select_node) and d.get('selectNodeId') != select_node
    for want in wanted:
        entry = next((x for x in entries if x.get('fieldId') == want['fieldId']), None)
        if entry and write_state(entry) == write_state(want):
            continue
        if entry:
            entry.update(want)
        else:
            entries.append(want)
        changed = True
    if not changed:
        return False
    cfg = {'actionId': d.get('actionId') or '2', 'appId': d.get('appId') or worksheet, 'appType': 1,
           'selectNodeId': select_node if select_node is not None else (d.get('selectNodeId') or ''),
           'fields': entries}
    hap.run('workflow', 'node', 'save', pid, node['id'], '--type', str(UPDATE_NODE), '-n', node['name'],
            '-c', json.dumps(cfg, ensure_ascii=False))
    back = read_node(pid, node['id'])
    got = {x.get('fieldId'): write_state(x) for x in back.get('fields') or []}
    bad = [w['fieldId'] for w in wanted if got.get(w['fieldId']) != write_state(w)]
    if bad or back.get('isException'):
        sys.exit(f"{node['name']}: {bad} read back {[got.get(b) for b in bad]} "
                 f"isException={back.get('isException')}")
    return True


# ── 5 · the order's Invoice Status ──────────────────────────────────────────
#
# Odoo `sale_order.py:620-665` computes `invoice_status` from the order's own `state` and its lines'
# `invoice_status`, over the lines that are neither down payments nor display types. A Dropdown cannot be
# computed in HAP at all, so it is a workflow write — the same answer 06's four amounts took. The compute
# depends on three events and a worksheet-event trigger takes **one** (BUILDING.md), so it is three
# workflows with one body.

STATUS_SELF = "Orders: Invoice Status follows the order's own Status"
STATUS_LINES = 'Orders: Invoice Status follows its lines'
STATUS_DELETE = 'Orders: Invoice Status when a line is deleted'
STATUS_WORKFLOWS = (STATUS_SELF, STATUS_LINES, STATUS_DELETE)

GUARD_BRANCH = 'Does the line belong to an order?'
GET_ORDER = 'Get the order as it now stands'
N_PROD_STEP = 'How many product lines'
N_TOINV_STEP = 'How many of them are still to invoice'
N_NOTINV_STEP = 'Product lines not yet invoiced'
N_NOTUPS_STEP = 'Product lines neither invoiced nor upselling'
WHICH_BRANCH = 'Which Invoice Status?'
SET_TO_INVOICE = 'Set To Invoice'
SET_INVOICED = 'Set Fully Invoiced'
SET_UPSELLING = 'Set Upselling Opportunity'
SET_NOTHING = 'Set Nothing to Invoice'
PATH_TO_INVOICE = 'Something is still to invoice'
PATH_INVOICED = 'Every product line is invoiced'
PATH_UPSELLING = 'Every product line is invoiced or upselling'
PATH_NOTHING = 'Otherwise'
STATUS_DESC = ("Odoo sale.order _compute_invoice_status (sale/models/sale_order.py:620-665): an order that is "
               "not confirmed reads Nothing to Invoice; a line still to invoice makes the order To Invoice; "
               "all product lines invoiced makes it Fully Invoiced; all invoiced or upselling makes it an "
               "Upselling Opportunity. Odoo's discount-only refinement (_can_be_invoiced_alone) is not built.")
STATUS_LABEL = {SET_TO_INVOICE: 'To Invoice', SET_INVOICED: 'Fully Invoiced',
                SET_UPSELLING: 'Upselling Opportunity', SET_NOTHING: 'Nothing to Invoice'}


def status_body(of, order_alias='order'):
    """The five decision steps and the four writes, as one `batch-add` payload."""
    n_prod = f"$order-{of[N_PRODUCT]['controlId']}$"
    n_toinv = f"$order-{of[N_TO_INVOICE]['controlId']}$"
    n_inv = f"$order-{of[N_INVOICED]['controlId']}$"
    n_ups = f"$order-{of[N_UPSELLING]['controlId']}$"
    upd = lambda alias, name: {'nodeAlias': alias, 'nodeType': 'update_record', 'name': name,
                               'config': {'worksheet': ORDERS, 'target': {'node': {'nodeAlias': 'order'}},
                                          'fields': []}}
    return [
        {'nodeAlias': 'order', 'nodeType': 'get_single', 'name': GET_ORDER,
         'config': {'worksheet': ORDERS, 'execute_type': 0}},        # 0 = stop when there is no order
        {'nodeAlias': 'nprod', 'nodeType': 'compute', 'name': N_PROD_STEP,
         'config': {'mode': 'number', 'formula': f'{n_prod}+0'}},
        {'nodeAlias': 'ntoinv', 'nodeType': 'compute', 'name': N_TOINV_STEP,
         'config': {'mode': 'number', 'formula': f'{n_toinv}+0'}},
        {'nodeAlias': 'notinv', 'nodeType': 'compute', 'name': N_NOTINV_STEP,
         'config': {'mode': 'number', 'formula': f'{n_prod}-{n_inv}'}},
        {'nodeAlias': 'notups', 'nodeType': 'compute', 'name': N_NOTUPS_STEP,
         'config': {'mode': 'number', 'formula': f'{n_prod}-{n_inv}-{n_ups}'}},
        {'nodeAlias': 'which', 'nodeType': 'branch', 'name': WHICH_BRANCH, 'config': {'paths': [
            {'alias': 'p1', 'name': PATH_TO_INVOICE, 'nodes': [upd('u1', SET_TO_INVOICE)]},
            {'alias': 'p2', 'name': PATH_INVOICED, 'nodes': [upd('u2', SET_INVOICED)]},
            {'alias': 'p3', 'name': PATH_UPSELLING, 'nodes': [upd('u3', SET_UPSELLING)]},
            {'alias': 'p4', 'name': PATH_NOTHING, 'nodes': [upd('u4', SET_NOTHING)]},
        ]}},
    ]


def status_nodes(of, lf, driver):
    """The whole workflow. On the two line-driven ones the body sits inside a guard path, because **a search
    step whose filter value is empty fails the whole run** — a line with no Orders would kill it (BUILDING.md,
    and 07's automation B)."""
    body = status_body(of)
    if driver == ORDERS:
        return body
    return [{'nodeAlias': 'guard', 'nodeType': 'branch', 'name': GUARD_BRANCH, 'config': {'paths': [
        {'alias': 'has_order', 'name': 'Yes',
         'condition': {'logic': 'and', 'items': [
             {'left': {'node': {'nodeAlias': 'trigger'}, 'fieldId': lf['Orders']['controlId'],
                       '_filedTypeId': RELATION}, 'op': 'not_empty'}]},
         'nodes': body},
        {'alias': 'no_order', 'name': 'No'},
    ]}}]


def status_conditions(pid, of, byname):
    """The four path conditions, in Odoo's own order. Each compares a number formula node's own result, which
    is the shape BUILDING.md documents for an aggregate feeding a branch."""
    order = byname[GET_ORDER]['id']
    state = of['Status']
    confirmed = cond(order, state, IS_ANY_OF, option_values(state, ['Sales Order']))
    nprod, ntoinv = byname[N_PROD_STEP]['id'], byname[N_TOINV_STEP]['id']
    notinv, notups = byname[N_NOTINV_STEP]['id'], byname[N_NOTUPS_STEP]['id']
    return {
        PATH_TO_INVOICE: [[confirmed, fx_cond(ntoinv, GTE_C, 1)]],
        PATH_INVOICED: [[confirmed, fx_cond(nprod, GTE_C, 1), fx_cond(notinv, EQ_C, 0)]],
        PATH_UPSELLING: [[confirmed, fx_cond(nprod, GTE_C, 1), fx_cond(notups, EQ_C, 0)]],
        PATH_NOTHING: [],                               # no condition: the default path (hap-cli _build_branch)
    }


STATUS_TRIGGER_NAME = {
    STATUS_SELF: 'When an order is created or its Status changes',
    STATUS_LINES: 'When an order line is created or changed',
    STATUS_DELETE: 'When an order line is deleted',
}


def status_trigger_fields(of, lf):
    """Narrowed to the fields that can change the answer — every run counts against the workflow quota
    (BUILDING.md), and 21 §11.2 asks for exactly this. Odoo's own compute depends on `state` and
    `order_line.invoice_status`, which here is Display Type, Quantity, Quantity Delivered and the Invoice
    Lines link. **Invoicing Closed is deliberately not a trigger field**: Odoo's `invoicing_closed` is not in
    `_compute_invoice_status` at all, it is read by the Close Invoicing buttons, so it cannot change the
    answer (21 §6.4)."""
    return {
        STATUS_SELF: [of['Status']['controlId']],
        STATUS_LINES: [lf['Orders']['controlId'], lf['Display Type']['controlId'],
                       lf['Quantity']['controlId'], lf['Quantity Delivered']['controlId'],
                       lf[OL_INVOICE_LINES]['controlId']],
        STATUS_DELETE: [],                              # a delete trigger takes no field narrowing
    }


def step_status():
    """The three workflows that write Orders' Invoice Status, and the alias on the control itself."""
    live = guard()
    of, lf = live[ORDERS], live[OLINES]
    for name in (N_PRODUCT, N_TO_INVOICE, N_INVOICED, N_UPSELLING):
        if name not in of:
            sys.exit(f'Orders has no {name!r} — run `toinvoice` first')
    if of['Invoice Status'].get('alias') != 'invoice_status':
        C.pinned_write(ORDERS, {of['Invoice Status']['controlId']: {'alias': 'invoice_status'}},
                       'o2i_orders_pre_status_alias', 'status/alias')
        of = fields(ORDERS)
    else:
        print("  Orders / Invoice Status already carries the alias 'invoice_status'; nothing saved")
    fields_by_wf = status_trigger_fields(of, lf)
    driver = {STATUS_SELF: ORDERS, STATUS_LINES: OLINES, STATUS_DELETE: OLINES}
    event = {STATUS_SELF: 'create_or_update', STATUS_LINES: 'create_or_update', STATUS_DELETE: 'delete'}
    for name in STATUS_WORKFLOWS:
        pid = ensure_workflow(name, STATUS_DESC)
        proc, byname = nodes_by_name(pid)
        changed = GET_ORDER not in byname
        if changed:
            hap.run('workflow', 'node', 'batch-add', pid, '--nodes',
                    json.dumps(status_nodes(of, lf, driver[name]), ensure_ascii=False),
                    '--trigger-worksheet', driver[name], '--trigger-event', event[name],
                    '--trigger-alias', 'trigger')
            proc, byname = nodes_by_name(pid)
        changed |= sync_trigger(pid, proc['startEventId'], STATUS_TRIGGER_NAME[name], driver[name],
                                event[name] == 'delete' and DELETE_EVENT or CREATE_OR_UPDATE,
                                fields_by_wf[name])
        trigger = proc['startEventId']
        # The order: its own rowid on the Orders-driven workflow, the line's Orders relation on the other two.
        if driver[name] == ORDERS:
            find = {'nodeId': byname[GET_ORDER]['id'], 'nodeType': GET_ONE, 'actionId': FROM_SHEET_ONE,
                    'filedId': 'rowid', 'filedValue': 'Record ID', 'filedTypeId': TEXT, 'enumDefault': 0,
                    'conditionId': EQ_C, 'sourceType': 0,
                    'conditionValues': [{'nodeId': trigger, 'controlId': 'rowid', 'value': '',
                                         'sureNodeId': trigger}]}
        else:
            find = {'nodeId': byname[GET_ORDER]['id'], 'nodeType': GET_ONE, 'actionId': FROM_SHEET_ONE,
                    'filedId': 'rowid', 'filedValue': 'Record ID', 'filedTypeId': TEXT, 'enumDefault': 0,
                    'conditionId': EQ_C, 'sourceType': 0,
                    'conditionValues': [{'nodeId': trigger, 'controlId': lf['Orders']['controlId'],
                                         'value': '', 'sureNodeId': trigger}]}
        changed |= sync_search(pid, byname[GET_ORDER], ORDERS, [find], execute_type=0)
        if GUARD_BRANCH in byname:                      # `batch-add` drops a branch path's name (BUILDING.md)
            guard_paths = paths_of(proc, byname[GUARD_BRANCH]['id'])
            has = next(p for p in guard_paths if p.get('nextId') not in (None, '', '99'))
            has_not = next(p for p in guard_paths if p['id'] != has['id'])
            changed |= save_path(pid, has, 'Yes', [[cond(trigger, lf['Orders'], NOT_EMPTY_C)]])
            changed |= save_path(pid, has_not, 'No', [])
        order_node = byname[GET_ORDER]['id']
        expressions = {
            N_PROD_STEP: f"${order_node}-{of[N_PRODUCT]['controlId']}$+0",
            N_TOINV_STEP: f"${order_node}-{of[N_TO_INVOICE]['controlId']}$+0",
            N_NOTINV_STEP: f"${order_node}-{of[N_PRODUCT]['controlId']}$-"
                           f"${order_node}-{of[N_INVOICED]['controlId']}$",
            N_NOTUPS_STEP: f"${order_node}-{of[N_PRODUCT]['controlId']}$-"
                           f"${order_node}-{of[N_INVOICED]['controlId']}$-"
                           f"${order_node}-{of[N_UPSELLING]['controlId']}$",
        }
        for step, expression in expressions.items():
            changed |= sync_number_formula(pid, byname[step], expression)
        conditions = status_conditions(pid, of, byname)
        gateway = byname[WHICH_BRANCH]['id']
        want_names = [PATH_TO_INVOICE, PATH_INVOICED, PATH_UPSELLING, PATH_NOTHING]
        paths = paths_of(proc, gateway)
        if len(paths) != 4:
            sys.exit(f'{name}: {WHICH_BRANCH} has {len(paths)} paths, wanted 4')
        by_step = {}
        for path in paths:
            step = proc['flowNodeMap'].get(path.get('nextId') or '', {}).get('name')
            by_step[step] = path
        for label, step in ((PATH_TO_INVOICE, SET_TO_INVOICE), (PATH_INVOICED, SET_INVOICED),
                            (PATH_UPSELLING, SET_UPSELLING), (PATH_NOTHING, SET_NOTHING)):
            path = by_step.get(step)
            if path is None:
                sys.exit(f'{name}: no branch path runs into {step!r}; found {sorted(k for k in by_step if k)}')
            changed |= save_path(pid, path, label, conditions[label])
        status = of['Invoice Status']
        by_key = {o['value']: o['key'] for o in status.get('options') or []}
        for step, label in STATUS_LABEL.items():
            if label not in by_key:
                sys.exit(f'Orders / Invoice Status has no option {label!r}')
            changed |= set_entries(pid, byname[step],
                                   [patch(status['controlId'], DROPDOWN, value=by_key[label])],
                                   order_node, ORDERS)
        print(f'  {name}:', C.publish(pid) if changed else 'already built; not re-published')
    for name in STATUS_WORKFLOWS:
        print(C.structure(hap.ids()['workflows'][name]))


# ── 6 · the To Invoice and To Upsell lists ──────────────────────────────────
#
# Odoo has both a pair of **search filters** (`sale/views/sale_order_views.xml:994-995`) and a pair of
# **dedicated actions** with the same domains (`:1172`, `:1188`) — the Sales overview's *Orders to Invoice*
# and *Orders to Upsell*. The quick filter on Invoice Status that the Orders view already carries covers the
# filter half and starts working the day step 5 writes the field, so nothing is built for it; the two
# actions become two views. Both are placed **after** Orders so the default view does not change.

ORDERS_VIEW = 'Orders'
TO_INVOICE_VIEW = 'To Invoice'
TO_UPSELL_VIEW = 'To Upsell'
VIEW_ORDER = ('All', 'Quotations', ORDERS_VIEW, TO_INVOICE_VIEW, TO_UPSELL_VIEW, 'Templates')


def orders_view():
    vid = next((v['viewId'] for v in hap.listing('worksheet', 'view', 'list', ORDERS, '-a', APP)
                if v['name'] == ORDERS_VIEW), None)
    if not vid:
        sys.exit(f'Orders has no view named {ORDERS_VIEW!r} to copy')
    return C.view_info(ORDERS, APP, vid)


def step_views():
    """To Invoice and To Upsell: the Orders view's own columns and filters plus one Invoice Status value, and
    **Invoice Count** added to the columns, because the point of the lists is to see what has been billed.

    Invoice Status is deliberately **not** added to the Quotations view: it means nothing on an unconfirmed
    order, since Odoo's compute returns `no` for every order that is not confirmed
    (`sale_order.py:628-629`)."""
    live = guard()
    of = live[ORDERS]
    base = orders_view()
    columns = list(base.get('showControls') or []) + [of[O_INVOICE_COUNT]['controlId']]
    status = of['Status']['controlId']
    template = of['Is Template']['controlId']
    invoice_status = of['Invoice Status']['controlId']
    sales_order = option_key(ORDERS, 'Status', 'Sales Order')

    def spec(label):
        return {'type': 'group', 'logic': 'AND', 'children': [
            {'type': 'condition', 'field': status, 'dataType': DROPDOWN, 'operator': 'eq',
             'value': [sales_order]},
            {'type': 'condition', 'field': template, 'operator': 'ne', 'value': ['1']},
            {'type': 'condition', 'field': invoice_status, 'dataType': DROPDOWN, 'operator': 'eq',
             'value': [option_key(ORDERS, 'Invoice Status', label)]}]}

    sort = {'sortCid': base.get('sortCid') or '', 'sortType': base.get('sortType') or 0,
            'moreSort': base.get('moreSort') or []}
    views = {
        TO_INVOICE_VIEW: (dict(viewType='table', filter=spec('To Invoice'), tableFields=columns), sort, columns),
        TO_UPSELL_VIEW: (dict(viewType='table', filter=spec('Upselling Opportunity'), tableFields=columns),
                         sort, columns),
    }
    for name, vid in C.upsert_views(ORDERS, APP, views, 'o2i_orders_views_pre_views').items():
        C.remember('views', KEY[ORDERS] + name, vid)
    print('  order:', C.sort_views(ORDERS, APP, [n for n in VIEW_ORDER]))
    C.print_views(ORDERS, APP)
    names = {c['controlId']: c['controlName'] for c in hap.controls(ORDERS)}
    for name in (TO_INVOICE_VIEW, TO_UPSELL_VIEW):
        info = C.view_info(ORDERS, APP, hap.ids()['views'][KEY[ORDERS] + name])
        got = [(names.get(f.get('controlId')), f.get('filterType'), tuple(f.get('values') or []))
               for f in info.get('filters') or []]
        if len(got) != 3 or (info.get('showControls') or []) != columns:
            sys.exit(f'{name} read back filters {got} columns {info.get("showControls")}')
        print(f'  OK  {name}: {got}')


# ── 7 · the two automations that would silently undo a faithful copy ────────
#
# 21 §5.6. Two workflows built earlier write fields Create Invoice must be allowed to set:
#
#   a. *Invoice Lines: fill the account of a new line* (6aab44254f2a99acac0f026f) writes **Account and
#      Taxes** from the **product**, where Odoo copies the taxes from the **order line**
#      (`sale_order_line.py:1543`).
#   b. *Invoices: Payment Terms follow the Customer / Vendor* (6aab8f1016473257ad5c91e0) writes the
#      **customer's** payment term, where Odoo's `_prepare_invoice` passes the **order's**
#      (`sale_order.py:1443`). Odoo's own `_compute_invoice_payment_term_id` is `precompute=True`
#      (`account/models/account_move.py:409`), so an explicit value in the create vals wins.
#
# Only (b) can be gated with a filter and nothing else, so only (b) is changed here. See `taxes_gate_report`.

PT_WORKFLOW = 'Invoices: Payment Terms follow the Customer / Vendor'
PT_PID = '6aab8f1016473257ad5c91e0'
PT_CUSTOMER_PATH = "Customer document — the contact's Customer Payment Terms"
PT_VENDOR_PATH = "Vendor document — the contact's Vendor Payment Terms"
PT_ELSE_PATH = 'Otherwise — the Payment Terms are left as they are'
ACCOUNT_WORKFLOW = 'Invoice Lines: fill the account of a new line'
ACCOUNT_PID = '6aab44254f2a99acac0f026f'
ACCOUNT_TAX_STEPS = ("Take the product's Income Account", "Take the category's Income Account",
                     "Take the product's Expense Account", "Take the category's Expense Account")
IL_TAXES = '6aad1419bd43f55762c758ab'


def type_condition(conditions, invoices_type_id):
    """The Type condition of a live path, as read — reused so the gate invents no option key of its own."""
    for group in conditions or []:
        for c in group:
            if c.get('filedId') == invoices_type_id:
                return json.loads(json.dumps(c))       # a copy; the caller puts it in a new group
    return None


def step_guards():
    """Gate *Invoices: Payment Terms follow the Customer / Vendor* on the invoice's Payment Terms being empty,
    and report — without touching it — what gating the account automation's Taxes write would take.

    What changes: two **path conditions** gain one condition each, and the else path gains the two OR-groups
    that keep it total. No node is added, removed or re-pointed, and no field write is touched. A run that
    matched no path of an exclusive gateway stops there with `causeMsg` 未通过分支 (BUILDING.md), which would
    take the Due Date chain down with it — hence the two new else groups."""
    guard()
    inf = fields(INVOICES)
    pid = PT_PID
    if workflow_id(PT_WORKFLOW) != pid:
        sys.exit(f'{PT_WORKFLOW!r} is {workflow_id(PT_WORKFLOW)}, not {pid} — read the app before gating it')
    proc, byname = nodes_by_name(pid)
    hap.backup('o2i_payment_terms_workflow_pre_gate',
               {n['id']: read_node(pid, n['id']) for n in proc['flowNodeMap'].values()})
    trigger = proc['startEventId']
    terms = inf['Payment Terms']
    type_id = inf['Type']['controlId']
    paths = {}
    for n in proc['flowNodeMap'].values():
        if n.get('typeId') == 2:
            d = read_node(pid, n['id'])
            paths[d.get('name')] = (n, d)
    for wanted in (PT_CUSTOMER_PATH, PT_VENDOR_PATH, PT_ELSE_PATH):
        if wanted not in paths:
            sys.exit(f'{PT_WORKFLOW}: no path named {wanted!r}; it has {sorted(k for k in paths if k)}')
    empty = cond(trigger, terms, EMPTY_C)
    not_empty = cond(trigger, terms, NOT_EMPTY_C)
    changed = False
    for name in (PT_CUSTOMER_PATH, PT_VENDOR_PATH):
        node, d = paths[name]
        groups = json.loads(json.dumps(d.get('conditions') or []))
        if not groups:
            sys.exit(f'{name}: no condition at all; this step will not invent one')
        if any(c.get('filedId') == terms['controlId'] for c in groups[0]):
            print(f'  {name}: already gated on {terms["controlName"]} being empty; nothing saved')
            continue
        groups[0] = list(groups[0]) + [empty]
        changed |= save_path(pid, node, name, groups)
        print(f'  {name}: + "{terms["controlName"]} is empty"')
    node, d = paths[PT_ELSE_PATH]
    groups = json.loads(json.dumps(d.get('conditions') or []))
    have = sum(1 for g in groups for c in g if c.get('filedId') == terms['controlId']
               and str(c.get('conditionId')) == NOT_EMPTY_C)
    if have >= 2:
        print(f'  {PT_ELSE_PATH}: already catches an invoice that arrives with a term; nothing saved')
    else:
        cust = type_condition(paths[PT_CUSTOMER_PATH][1].get('conditions'), type_id)
        vend = type_condition(paths[PT_VENDOR_PATH][1].get('conditions'), type_id)
        if not cust or not vend:
            sys.exit('the customer and vendor paths no longer carry a Type condition to copy')
        groups = groups + [[cust, not_empty], [vend, not_empty]]
        changed |= save_path(pid, node, PT_ELSE_PATH, groups)
        print(f'  {PT_ELSE_PATH}: + two groups, "a customer/vendor document whose {terms["controlName"]} '
              'is already set"')
    print(f'  {PT_WORKFLOW}:', C.publish(pid) if changed else 'already gated; not re-published')
    report_gate(pid)
    taxes_gate_report()


def report_gate(pid):
    proc = hap.run('workflow', 'node', 'list', pid)
    names = {n['id']: n['name'] for n in proc['flowNodeMap'].values()}
    for n in proc['flowNodeMap'].values():
        if n.get('typeId') != 2:
            continue
        d = read_node(pid, n['id'])
        groups = [[(c.get('filedValue'), c.get('conditionId'),
                    [(v.get('value') or {}).get('value') if isinstance(v.get('value'), dict) else v.get('value')
                     for v in c.get('conditionValues') or []]) for c in g] for g in d.get('conditions') or []]
        print(f'  path {d.get("name")!r} -> {names.get(n.get("nextId")) or "(nothing)"}')
        for g in groups:
            print(f'      {g}')


def taxes_gate_report():
    """What gating the account automation's Taxes write would take — **reported, never done here.**

    21 §3.4 says one step carries the Taxes entry. Read live on 23 Sep 2026, **four** do — every step that
    takes an account from a product or a category also writes that product's Sales or Purchase Taxes. So the
    gate is not one filter: each of the four paths would have to split into "the line already carries taxes"
    and "it does not", which is four gateways, eight paths and four duplicate update steps inside a built,
    reviewed workflow. The brief's instruction for that case is to stop and report."""
    proc, byname = nodes_by_name(ACCOUNT_PID)
    writes = []
    for step in ACCOUNT_TAX_STEPS:
        node = byname.get(step)
        if node is None:
            print(f'  {ACCOUNT_WORKFLOW}: no step named {step!r} any more')
            continue
        d = read_node(ACCOUNT_PID, node['id'])
        entries = [(x.get('fieldId'), x.get('fieldValueName')) for x in d.get('fields') or []]
        if any(fid == IL_TAXES for fid, _ in entries):
            writes.append((step, node['id'], entries))
    print(f'\n  NOT CHANGED — {ACCOUNT_WORKFLOW} ({ACCOUNT_PID})')
    print(f'  {len(writes)} of its steps write Invoice Lines / Taxes from the product, not one as 21 §3.4 says:')
    for step, node_id, entries in writes:
        print(f'    {step!r} {node_id}: {entries}')
    print('  Gating those on "Taxes is empty" needs a gateway and a duplicate write inside each of the four '
          'paths — not a filter — so it is left exactly as it was. Until the owner decides, an invoice line '
          "Create Invoice makes carries the **product's** taxes, not the order line's (21 §12 divergence 6).")


# ── 8 · Create Invoice ──────────────────────────────────────────────────────
#
# Odoo's *Create Invoice* (`sale/views/sale_order_views.xml:271-279`) opens the
# `sale.advance.payment.inv` wizard, whose default is a regular invoice:
# `_create_invoices(final=…, grouped=…)` (`sale/wizard/sale_make_invoice_advance.py:140-141`).
# `_prepare_invoice` (`sale_order.py:1413-1451`) builds the header, `_get_invoiceable_lines` (`:1501-1550`)
# picks the lines and `_prepare_invoice_line` (`sale_order_line.py:1513-1558`) builds each one — and writes
# `sale_line_ids = [Command.link(self.id)]` **inside the create**, which is what the invoice line's Sales
# Order Lines write below reproduces exactly.
#
# Odoo's second Create Invoice button (`:280-287`, a percentage down payment when there is nothing to
# invoice yet) is **not** built: it belongs with down payments (21 §7).

CREATE_BUTTON = 'Create Invoice'
CREATE_DESC = ('Makes a draft invoice for everything on this order that has not been invoiced yet. '
               'Over a selection, makes one invoice for each order you selected.')
GET_ORDER_NOW = 'Get the order as it now stands'
COUNT_TO_INVOICE = 'How many lines are there to invoice?'
ANYTHING_BRANCH = 'Is there anything to invoice?'
NOTHING_NOTICE = 'Nothing to invoice'
MAKE_INVOICE = 'Make the invoice'
FIND_INVOICE = 'Find the invoice just made'
LINES_TO_INVOICE = 'The lines to invoice'
EACH_LINE = 'One invoice line per order line'
INNER_FLOW = 'Create Invoice: one order line'
INNER_GET_INVOICE = 'Get the invoice'
KIND_BRANCH = 'What kind of line is it?'
MAKE_LINE = {'Product': 'Make the invoice line', 'Section': 'Carry the section heading',
             'Subsection': 'Carry the subsection heading', 'Note': 'Carry the note'}
# A branch path must not share a name with the step inside it: `nodes_by_name` keys the whole flow by name,
# and a path (typeId 2) that shadowed its own create step made the step read back with no fields at all.
KIND_PATH = {'Product': 'A product line', 'Section': 'A section', 'Subsection': 'A subsection',
             'Note': 'A note'}
INVOICE_PARAM = 'invoice'
PARAM_NODE = '6038a1cbf18158039fb40e68'           # the fixed 本流程参数 node every process carries
NOTICE = 27
MSG_NOTHING = ('There is nothing left to invoice on this order. Everything on it has been invoiced already, '
               'or the quantities still to invoice are zero.')
TRIGGER_USER = {'type': 6, 'entityId': SYSTEM_NODE, 'entityName': 'System', 'roleId': 'triggeraid',
                'roleTypeId': 0, 'roleName': 'Trigger', 'controlType': 26, 'avatar': '', 'count': 0,
                'appType': 100, 'actionId': ''}
GT_ZERO = 13                                      # a view/rollup filter's "greater than"
LINE_KINDS = ('Product', 'Section', 'Subsection', 'Note')
JOURNALS = '6aa8f5191204328eb1af162a'
J_TYPE = '6aa8f6c81204328eb1af1678'               # Journals / Type
J_SEQUENCE = '6aa9dabcbd43f55762c6f430'           # Journals / Sequence
J_PREFIX = '6aa8f6c81204328eb1af1677'             # Journals / Sequence Prefix (Odoo's `code`)
J_ACTIVE = '6aa8f6c81204328eb1af167b'             # Journals / Active
SALES_JOURNAL = 'The sales journal to fall back on'
JOURNAL_BRANCH = 'Does the order name a journal?'
SET_JOURNAL = "Take the company's sales journal"
CHECKED_C = '29'                                  # a workflow condition on a checkbox: 选中


def create_spec(of):
    """The button. Odoo's own is `invisible="invoice_status != 'to invoice'"`, and Invoicing Closed is where
    Odoo's `invisible` would put it if `_compute_invoice_status` used it (21 §6.4). **Batch on**: Odoo offers
    the same action over a list selection (`sale_order_views.xml:121-124`)."""
    return {'name': CREATE_BUTTON, 'type': 'triggerWorkflow', 'desc': CREATE_DESC, 'isBatch': True,
            'enableWhen': {'type': 'group', 'logic': 'AND', 'children': [
                {'field': of['Status']['controlId'], 'dataType': DROPDOWN, 'operator': 'eq',
                 'value': [option_key(ORDERS, 'Status', 'Sales Order')]},
                {'field': of['Invoice Status']['controlId'], 'dataType': DROPDOWN, 'operator': 'eq',
                 'value': [option_key(ORDERS, 'Invoice Status', 'To Invoice')]},
                {'field': of[
                    'Invoicing Closed']['controlId'], 'dataType': SWITCH, 'operator': 'ne', 'value': ['1']}]}}


def ensure_create_button(of):
    """The button, created once. `create-custom-action --action-spec` ignores `--btn-id`, so a button that
    exists by name is never re-created — it would be added twice."""
    live = {b['name']: b for b in hap.listing('worksheet', 'custom-actions', ORDERS)}
    key = KEY[ORDERS] + CREATE_BUTTON
    if CREATE_BUTTON in live:
        pid = hap.ids().get('workflows', {}).get(key)
        if not pid:
            sys.exit(f'{CREATE_BUTTON} exists ({live[CREATE_BUTTON]["btnId"]}) but ids.json has no workflow')
        C.remember('buttons', key, live[CREATE_BUTTON]['btnId'])
        return pid, False
    hap.backup('o2i_orders_buttons_pre_create', list(live.values()))
    out = hap.run('worksheet', 'create-custom-action', ORDERS, '-a', APP, '--action-spec',
                  json.dumps(create_spec(of), ensure_ascii=False))
    data = out.get('data', out) if isinstance(out, dict) else {}
    pid = data.get('processId')
    if not pid:
        sys.exit(f'{CREATE_BUTTON}: no processId in create-custom-action output: {out}')
    C.remember('workflows', key, pid)
    btn = next((b for b in hap.listing('worksheet', 'custom-actions', ORDERS) if b['name'] == CREATE_BUTTON), None)
    if not btn:
        sys.exit(f'{CREATE_BUTTON}: created, but it does not come back from custom-actions')
    C.remember('buttons', key, btn['btnId'])
    print(f'  {CREATE_BUTTON}: button {btn["btnId"]}, workflow {pid}')
    return pid, True


def header_fields(of, inf):
    """§5.3 — `_prepare_invoice`, field by field, with Odoo's source beside each.

    **Sales Orders is written here, not appended afterwards.** It is the reverse half of Orders' Invoices, and
    a two-way Relation's reverse is writable: measured 23 Sep 2026, writing Invoices / Sales Orders made the
    order's own Invoices list and its Invoice Count follow at once. So the header relation is written in the
    same create as the rest — no second update step, no append, and no window in which the invoice exists
    unattached."""
    o = lambda name: of[name]['controlId']
    invoice_key = option_key(INVOICES, 'Type', 'Customer Invoice')
    draft_key = option_key(INVOICES, 'Status', 'Draft')
    return [
        # 'move_type': 'out_invoice'
        {'fieldId': inf['Type']['controlId'], 'type': DROPDOWN, 'value': invoice_key},
        # a new move is a draft
        {'fieldId': inf['Status']['controlId'], 'type': DROPDOWN, 'value': draft_key},
        # 'partner_id': self.partner_invoice_id
        {'fieldId': inf['Customer / Vendor']['controlId'], 'type': RELATION,
         'valueRef': {'kind': 'field', 'node': {'nodeAlias': 'order'}, 'fieldId': o('Invoice Address')}},
        # 'partner_shipping_id': self.partner_shipping_id
        {'fieldId': inf['Delivery Address']['controlId'], 'type': RELATION,
         'valueRef': {'kind': 'field', 'node': {'nodeAlias': 'order'}, 'fieldId': o('Delivery Address')}},
        # 'invoice_origin': self.name — and the key node 5 finds the new invoice by
        {'fieldId': inf['Source Document']['controlId'], 'type': TEXT,
         'valueRef': {'kind': 'field', 'node': {'nodeAlias': 'order'}, 'fieldId': o('Number')}},
        # 'ref': self.client_order_ref or self.name
        {'fieldId': inf['Customer Reference']['controlId'], 'type': TEXT,
         'valueRef': {'kind': 'field', 'node': {'nodeAlias': 'order'}, 'fieldId': o('Customer Reference')}},
        # 'invoice_payment_term_id': self.payment_term_id
        {'fieldId': inf['Payment Terms']['controlId'], 'type': RELATION,
         'valueRef': {'kind': 'field', 'node': {'nodeAlias': 'order'}, 'fieldId': o('Payment Terms')}},
        # 'journal_id': self.journal_id
        {'fieldId': inf['Journal']['controlId'], 'type': RELATION,
         'valueRef': {'kind': 'field', 'node': {'nodeAlias': 'order'}, 'fieldId': o('Journal')}},
        # 'invoice_user_id', 'user_id': self.user_id
        {'fieldId': inf['Salesperson']['controlId'], 'type': 26,
         'valueRef': {'kind': 'field', 'node': {'nodeAlias': 'order'}, 'fieldId': o('Salesperson')}},
        # 'narration': self.note
        {'fieldId': inf['Terms and Conditions']['controlId'], 'type': 41,
         'valueRef': {'kind': 'field', 'node': {'nodeAlias': 'order'}, 'fieldId': o('Terms and conditions')}},
        # not in _prepare_invoice — carried on purpose so the two documents' amounts agree (21 §9, §12.11)
        {'fieldId': inf['Tax mode']['controlId'], 'type': DROPDOWN,
         'valueRef': {'kind': 'field', 'node': {'nodeAlias': 'order'}, 'fieldId': o('Tax Mode')}},
        # sale_stock/models/sale_order.py:300 invoice_vals['invoice_incoterm_id'] = self.incoterm.id
        {'fieldId': inf['Incoterm']['controlId'], 'type': RELATION,
         'valueRef': {'kind': 'field', 'node': {'nodeAlias': 'order'}, 'fieldId': o('Incoterm')}},
        # sale_stock/models/account_move.py:129-137 — a compute over the orders behind the lines; one order
        # per invoice here, so a copy is the same answer (21 §9, §12.12)
        {'fieldId': inf['Incoterm Location']['controlId'], 'type': TEXT,
         'valueRef': {'kind': 'field', 'node': {'nodeAlias': 'order'}, 'fieldId': o('Incoterm Location')}},
        # sale_stock uses effective_date (when it actually shipped), which needs Inventory (21 §12.10)
        {'fieldId': inf['Delivery Date']['controlId'], 'type': 15,
         'valueRef': {'kind': 'field', 'node': {'nodeAlias': 'order'}, 'fieldId': o('Delivery Date')}},
        # Odoo's invoice_ids is a compute over the lines; here it is stored, and written from this side
        {'fieldId': inf[I_ORDERS]['controlId'], 'type': RELATION,
         'valueRef': {'kind': 'field', 'node': {'nodeAlias': 'order'}, 'fieldId': 'rowid'}},
        # Not in `_prepare_invoice` — these two are `account.move`'s own **field defaults**, which Odoo's create
        # applies just the same: `date = fields.Date.context_today` (`account/models/account_move.py:377-383`)
        # and `auto_post` default 'no' (`:565-575`). Both are required here, so leaving them empty would make a
        # created invoice one a person could not save from the form.
        {'fieldId': inf['Accounting Date']['controlId'], 'type': 15, 'valueRef': {'kind': 'system',
                                                                                 'field': 'nowTime'}},
        {'fieldId': inf['Auto-post']['controlId'], 'type': DROPDOWN,
         'value': option_key(INVOICES, 'Auto-post', 'No')},
        # Invoice Date, Due Date and Number are left empty: Odoo leaves them, and 06's Confirm fills the
        # Invoice Date and the Number while the Due Date automation fills the due date.
    ]


def line_fields(of, lf, ilf, kind):
    """§5.5 — `_prepare_invoice_line`. On a Section, a Subsection or a Note only the Display Type, the
    Sequence and the Label are written: Odoo forces `account_id = False` there
    (`sale_order_line.py:1556-1557`) and 07's own rule hides the figures.

    **Sales Order Lines is written in the create**, which is where Odoo writes it
    (`'sale_line_ids': [Command.link(self.id)]`). It is the reverse half of Order Lines' Invoice Lines and a
    reverse is writable (measured 23 Sep 2026), so the link exists the instant the line does — there is no
    window in which an invoice line has no order line, and no `addType` append anywhere."""
    sub = {'nodeAlias': 'sub_trigger'}
    line = lambda name: lf[name]['controlId']
    out = [
        {'fieldId': ilf['Invoice']['controlId'], 'type': RELATION,
         'valueRef': {'kind': 'field', 'node': {'nodeAlias': 'invoice'}, 'fieldId': 'rowid'}},
        {'fieldId': ilf[IL_ORDER_LINES]['controlId'], 'type': RELATION,
         'valueRef': {'kind': 'field', 'node': sub, 'fieldId': 'rowid'}},
        {'fieldId': ilf['Display Type']['controlId'], 'type': DROPDOWN,
         'value': option_key(ILINES, 'Display Type', kind)},
        {'fieldId': ilf['Sequence']['controlId'], 'type': NUMBER,
         'valueRef': {'kind': 'field', 'node': sub, 'fieldId': line('Sequence')}},
        {'fieldId': ilf['Label']['controlId'], 'type': TEXT,
         'valueRef': {'kind': 'field', 'node': sub, 'fieldId': line('Description')}},
    ]
    if kind != 'Product':
        return out
    return out + [
        {'fieldId': ilf['Product']['controlId'], 'type': RELATION,
         'valueRef': {'kind': 'field', 'node': sub, 'fieldId': line('Product')}},
        # 'quantity': self.qty_to_invoice
        {'fieldId': ilf['Quantity']['controlId'], 'type': NUMBER,
         'valueRef': {'kind': 'field', 'node': sub, 'fieldId': line(QTY_TO_INVOICE)}},
        {'fieldId': ilf['Unit']['controlId'], 'type': RELATION,
         'valueRef': {'kind': 'field', 'node': sub, 'fieldId': line('Unit')}},
        {'fieldId': ilf['Unit Price']['controlId'], 'type': NUMBER,
         'valueRef': {'kind': 'field', 'node': sub, 'fieldId': line('Unit Price')}},
        {'fieldId': ilf['Discount (%)']['controlId'], 'type': NUMBER,
         'valueRef': {'kind': 'field', 'node': sub, 'fieldId': line('Discount')}},
        # 'tax_ids': Command.set(self.tax_ids.ids) — the **order line's** taxes, not the product's (21 §5.6)
        {'fieldId': ilf['Taxes']['controlId'], 'type': RELATION,
         'valueRef': {'kind': 'field', 'node': sub, 'fieldId': line('Taxes')}},
        # Account is not written: 07's own automation supplies it, as Odoo derives it
    ]


def lines_filter_flat(of, lf):
    """The placeholder filter the get-multiple is **created** with: the lines of this order. `batch-add` cannot
    carry the real one (see `sync_search`), so it carries the AND half and `step_create` writes the OR."""
    return {'logic': 'and', 'items': [
        {'left': {'node': {'nodeAlias': 'order'}, 'fieldId': lf['Orders']['controlId'],
                  '_filedTypeId': RELATION}, 'op': RELATION_EQ,
         'right': {'kind': 'field', 'node': {'nodeAlias': 'order'}, 'fieldId': 'rowid'}}]}


def lines_filter_groups(lf, node_id, order_node):
    """§5.4 — which order lines the loop takes: **this order's lines whose Invoiceable line reads 1**.

    That is one flat AND, and it has to be: a get-records step's `filters` wrapper carries **one**
    `spliceType` for every condition it holds, so two groups cannot be OR-ed (see
    `invoiceable_expression`). The OR of §5.4 — a product line with something left to invoice, **or** any
    Section, Subsection or Note — lives in the formula instead, which also keeps §12.4's section behaviour in
    one editable place.

    Zero quantities are excluded by the formula's `> 0`, which is Odoo's `float_is_zero(qty_to_invoice)` skip
    (`sale_order.py:1512`); a **negative** Quantity To Invoice is excluded too, which is Odoo's behaviour until
    `final` — the deduct-down-payments pass — exists (`:1513`). Odoo's *all display types → no invoice* rule
    (`:1580`) is reproduced by the guard, which counts **product** lines only."""
    belongs = {'nodeId': node_id, 'nodeType': GET_MANY, 'actionId': FROM_WORKSHEET,
               'filedId': lf['Orders']['controlId'], 'filedValue': 'Orders', 'filedTypeId': RELATION,
               'enumDefault': 1, 'conditionId': RELATION_EQ, 'sourceType': 33,
               'conditionValues': [{'nodeId': order_node, 'controlId': 'rowid'}]}
    invoiceable = {'nodeId': node_id, 'nodeType': GET_MANY, 'actionId': FROM_WORKSHEET,
                   'filedId': lf[INVOICEABLE]['controlId'], 'filedValue': INVOICEABLE,
                   'filedTypeId': NUMBER, 'enumDefault': 0, 'conditionId': EQ_C, 'sourceType': 0,
                   'conditionValues': [{'value': '1'}]}
    return [belongs, invoiceable]


def create_nodes(of, lf, inf, ilf):
    """The whole Create Invoice workflow, for one `batch-add` on the empty button workflow."""
    inner = [
        # An inner flow reaches the outer flow **only through parameters**, and a sub-process parameter is
        # text (`workflow_node_dsl._save_sub_process`: every processVariables entry is "type": 2). So the
        # invoice's row id travels down as text and the inner flow turns it back into a record.
        {'nodeAlias': 'invoice', 'nodeType': 'get_single', 'name': INNER_GET_INVOICE,
         'config': {'worksheet': INVOICES, 'execute_type': 0}},
        {'nodeAlias': 'kind', 'nodeType': 'branch', 'name': KIND_BRANCH, 'config': {'paths': [
            {'alias': f'k{i}', 'name': KIND_PATH[k], 'nodes': [
                {'nodeAlias': f'make{i}', 'nodeType': 'create_record', 'name': MAKE_LINE[k],
                 'config': {'worksheet': ILINES, 'fields': line_fields(of, lf, ilf, k)}}]}
            for i, k in enumerate(LINE_KINDS)]}},
    ]
    return [
        # A button's condition is evaluated on the row the browser last rendered, so the order is re-read
        # inside the run: that is what makes a double press safe (21 §5.7).
        {'nodeAlias': 'order', 'nodeType': 'get_single', 'name': GET_ORDER_NOW,
         'config': {'worksheet': ORDERS, 'execute_type': 0}},
        {'nodeAlias': 'count', 'nodeType': 'rollup', 'name': COUNT_TO_INVOICE,
         'config': {'mode': 'worksheet', 'worksheet': OLINES, 'aggregate': 'count', 'filter': {
             'logic': 'and', 'items': [
                 {'left': {'node': {'nodeAlias': 'order'}, 'fieldId': lf['Orders']['controlId'],
                           '_filedTypeId': RELATION}, 'op': RELATION_EQ,
                  'right': {'kind': 'field', 'node': {'nodeAlias': 'order'}, 'fieldId': 'rowid'}},
                 {'left': {'node': {'nodeAlias': 'order'}, 'fieldId': lf['Display Type']['controlId'],
                           '_filedTypeId': DROPDOWN}, 'op': 'in',
                  'right': {'kind': 'literal', 'values': [
                      {'key': option_key(OLINES, 'Display Type', 'Product'), 'value': 'Product',
                       'isDeleted': False}]}},
                 {'left': {'node': {'nodeAlias': 'order'}, 'fieldId': lf[QTY_TO_INVOICE]['controlId'],
                           '_filedTypeId': NUMBER}, 'op': 'gt', 'right': {'kind': 'literal', 'value': '0'}},
             ]}}},
        {'nodeAlias': 'anything', 'nodeType': 'branch', 'name': ANYTHING_BRANCH, 'config': {'paths': [
            # A notice, not an abort: an aborted run draws HAP's own toast, a warning icon and the
            # untranslated 中止, while a run that simply ends draws nothing (BUILDING.md, 21 §5.7).
            {'alias': 'nothing', 'name': 'No', 'nodes': [
                {'nodeAlias': 'tell', 'nodeType': 'send_internal_notice', 'name': NOTHING_NOTICE,
                 'config': {'content': MSG_NOTHING, 'accounts': [dict(TRIGGER_USER)]}}]},
            {'alias': 'yes', 'name': 'Yes', 'nodes': [
                {'nodeAlias': 'make', 'nodeType': 'create_record', 'name': MAKE_INVOICE,
                 'config': {'worksheet': INVOICES, 'fields': header_fields(of, inf)}},
                {'nodeAlias': 'found', 'nodeType': 'get_single', 'name': FIND_INVOICE,
                 'config': {'worksheet': INVOICES, 'execute_type': 0}},
                {'nodeAlias': 'lines', 'nodeType': 'get_multiple', 'name': LINES_TO_INVOICE,
                 'config': {'worksheet': OLINES, 'filter': lines_filter_flat(of, lf),
                            'sorts': [{'controlId': lf['Sequence']['controlId'], 'controlType': NUMBER,
                                       'isAsc': True}]}},
                {'nodeAlias': 'each', 'nodeType': 'sub_process', 'name': EACH_LINE,
                 'config': {'target': {'kind': 'record', 'node': {'nodeAlias': 'lines'}},
                            'process': {'name': INNER_FLOW, 'nodes': inner, 'parameters': [
                                {'name': INVOICE_PARAM,
                                 'value': {'kind': 'field', 'node': {'nodeAlias': 'found'},
                                           'fieldId': 'rowid'}}]},
                            'execution': {'mode': 'sequential_each', 'continueAfterComplete': True}}},
            ]},
        ]}},
    ]


def journal_nodes(found_id, order_id):
    """The journal fallback, for one `batch-add` **after** *Find the invoice just made* — so the invoice carries
    a journal before its lines exist, which matters because 07's account automation reads the invoice's journal
    for its last fallback (*Take the journal's Default Account*).

    Odoo's `_prepare_invoice` sets `journal_id` **only when the order has one** (`sale_order.py:1449-1450`).
    Everything else gets it from `account.move._compute_journal_id` -> `_search_default_journal`
    (`account/models/account_move.py:898-938`), which searches `account.journal` for a valid type — `sale` for
    an `out_invoice` — and takes the **first** in the model's own order, `_order = 'sequence, type, code'`
    (`account/models/account_journal.py:45`). So: the active Sales journal with the lowest Sequence, ties broken
    by Sequence Prefix. Odoo raises a UserError when there is none; here the search carries on (`execute_type`
    2) and the Journal is simply left empty, because a button workflow cannot put an error in front of a user.

    The search is shaped exactly like 06's own *Get the journal* (`invoices.py` `step_numbering`): a `get_single`
    on Journals whose filter goes in as `filters` with `node save --type 7`."""
    return [
        {'nodeAlias': 'sales_journal', 'nodeType': 'get_single', 'name': SALES_JOURNAL,
         'config': {'worksheet': JOURNALS, 'execute_type': 2}},
        {'nodeAlias': 'journal_branch', 'nodeType': 'branch', 'name': JOURNAL_BRANCH, 'config': {'paths': [
            {'alias': 'no_journal', 'name': 'No', 'nodes': [
                {'nodeAlias': 'set_journal', 'nodeType': 'update_record', 'name': SET_JOURNAL,
                 'config': {'worksheet': INVOICES, 'target': {'node': {'nodeId': found_id}}, 'fields': []}}]},
            {'alias': 'has_journal', 'name': 'Yes'}]}},
    ]


def sales_journal_filter(node_id):
    """Type is Sales, and Active ticked — Odoo's search excludes archived records, so an archived journal is
    not a candidate."""
    return [
        {'nodeId': node_id, 'nodeType': GET_ONE, 'actionId': FROM_SHEET_ONE, 'filedId': J_TYPE,
         'filedValue': 'Type', 'filedTypeId': DROPDOWN, 'enumDefault': 0, 'conditionId': IS_ANY_OF,
         'sourceType': 0, 'conditionValues': option_values(fields(JOURNALS)['Type'], ['Sales'])},
        {'nodeId': node_id, 'nodeType': GET_ONE, 'actionId': FROM_SHEET_ONE, 'filedId': J_ACTIVE,
         'filedValue': 'Active', 'filedTypeId': SWITCH, 'enumDefault': 0, 'conditionId': CHECKED_C,
         'sourceType': 0, 'conditionValues': []},
    ]


def ensure_journal_fallback(pid, of, inf, proc, byname):
    """Add and configure the journal fallback; True when anything was written."""
    changed = SALES_JOURNAL not in byname
    if changed:
        # `batch-add` inserts after the node named, and the rest of the chain becomes what the branch converges
        # on (BUILDING.md, and orders.ensure_product_guard) — so the two nodes land between *Find the invoice
        # just made* and *The lines to invoice*.
        hap.run('workflow', 'node', 'batch-add', pid, '--nodes',
                json.dumps(journal_nodes(byname[FIND_INVOICE]['id'], byname[GET_ORDER_NOW]['id']),
                           ensure_ascii=False),
                '--trigger-node-id', byname[FIND_INVOICE]['id'], '--trigger-alias', 'found')
        proc, byname = nodes_by_name(pid)
        for name in (SALES_JOURNAL, JOURNAL_BRANCH, SET_JOURNAL):
            if name not in byname:
                sys.exit(f'{name!r} is not in the workflow after batch-add: {sorted(byname)}')
    changed |= sync_search(pid, byname[SALES_JOURNAL], JOURNALS,
                           sales_journal_filter(byname[SALES_JOURNAL]['id']), execute_type=2,
                           sorts=[{'controlId': J_SEQUENCE, 'controlType': NUMBER, 'isAsc': True},
                                  {'controlId': J_PREFIX, 'controlType': TEXT, 'isAsc': True}])
    no, yes = None, None
    for path in paths_of(proc, byname[JOURNAL_BRANCH]['id']):
        nxt = proc['flowNodeMap'].get(path.get('nextId') or '', {}).get('name')
        if nxt == SET_JOURNAL:
            no = path
        else:
            yes = path
    if not no or not yes:
        sys.exit(f'{JOURNAL_BRANCH}: could not tell the two paths apart')
    changed |= save_path(pid, no, 'No', [[cond(byname[GET_ORDER_NOW]['id'], of['Journal'], EMPTY_C)]])
    changed |= save_path(pid, yes, 'Yes', [])
    changed |= set_entries(pid, byname[SET_JOURNAL],
                          [patch(inf['Journal']['controlId'], RELATION,
                                 node=byname[SALES_JOURNAL]['id'], source='rowid')],
                          byname[FIND_INVOICE]['id'], INVOICES)
    return changed


def sub_params(pid, node):
    """{parameter name: its controlId} of a sub-process step, and the value it passes."""
    d = read_node(pid, node['id'])
    names = {v['controlId']: v['controlName'] for v in d.get('subProcessVariables') or []}
    return {names.get(x['fieldId'], x['fieldId']): (x['fieldId'], x.get('fieldValue'))
            for x in d.get('fields') or []}


def inner_process_id(pid, node):
    return read_node(pid, node['id']).get('subProcessId')


def save_notice(pid, node, content, account):
    """The 站内通知 step's message and its one recipient. The node's `flowNodeMap` "106" — the channel config
    the server needs or publish fails with warningType 200 — goes back exactly as it came (BUILDING.md)."""
    got = read_node(pid, node['id'])
    channel = got.get('flowNodeMap') or {}
    key = lambda a: {k: a.get(k) for k in ('type', 'entityId', 'roleId', 'controlType')}
    if got.get('sendContent') == content and channel.get('106', {}).get('name') == node['name'] \
            and [key(a) for a in got.get('accounts') or []] == [key(account)]:
        return False
    if '106' in channel:
        channel['106']['name'] = node['name']
    hap.run('workflow', 'node', 'save', pid, node['id'], '--type', str(NOTICE), '-c', json.dumps(
        {'appType': got.get('appType', 1), 'selectNodeId': '', 'sendContent': content,
         'accounts': [account], 'formProperties': [], 'showTitle': True,
         'flowNodeMap': channel}, ensure_ascii=False), '-n', node['name'])
    back = read_node(pid, node['id'])
    if back.get('sendContent') != content:
        sys.exit(f"{node['name']}: message read back {back.get('sendContent')!r}")
    return True


def step_create():
    """The Create Invoice button and its workflow, and the child flow that makes one invoice line per line."""
    live = guard()
    of, lf, inf, ilf = live[ORDERS], live[OLINES], live[INVOICES], live[ILINES]
    for name, ws in ((QTY_TO_INVOICE, OLINES), (OL_INVOICE_LINES, OLINES), (I_ORDERS, INVOICES),
                     (IL_ORDER_LINES, ILINES)):
        if name not in live[ws]:
            sys.exit(f'{NAME[ws]} has no {name!r} — run the earlier steps first')
    pid, fresh = ensure_create_button(of)
    proc, byname = nodes_by_name(pid)
    changed = GET_ORDER_NOW not in byname
    if changed:
        trigger = proc['startEventId']
        first = proc['flowNodeMap'][trigger].get('nextId')
        if first not in (None, '', '99'):
            sys.exit(f'{CREATE_BUTTON}: its workflow already has steps that this script did not build '
                     f'({proc["flowNodeMap"][first].get("name")!r}) — stopping rather than appending to them')
        hap.run('workflow', 'node', 'batch-add', pid, '--nodes',
                json.dumps(create_nodes(of, lf, inf, ilf), ensure_ascii=False),
                '--trigger-node-id', trigger, '--trigger-alias', 'trigger')
        proc, byname = nodes_by_name(pid)
        for name in (GET_ORDER_NOW, COUNT_TO_INVOICE, ANYTHING_BRANCH, NOTHING_NOTICE, MAKE_INVOICE,
                     FIND_INVOICE, LINES_TO_INVOICE, EACH_LINE):
            if name not in byname:
                sys.exit(f'{name!r} is not in the workflow after batch-add: {sorted(byname)}')
    trigger = proc['startEventId']
    # node 1: the order, by its own rowid — `batch-add` writes a search step's filter as `operateCondition`
    changed |= sync_search(pid, byname[GET_ORDER_NOW], ORDERS, [{
        'nodeId': byname[GET_ORDER_NOW]['id'], 'nodeType': GET_ONE, 'actionId': FROM_SHEET_ONE,
        'filedId': 'rowid', 'filedValue': 'Record ID', 'filedTypeId': TEXT, 'enumDefault': 0,
        'conditionId': EQ_C, 'sourceType': 0,
        'conditionValues': [{'nodeId': trigger, 'controlId': 'rowid', 'value': '', 'sureNodeId': trigger}]}],
        execute_type=0)
    # node 5: the invoice just made — the newest draft whose Source Document is this order's Number. Source
    # Document is `101` read-only and a workflow write ignores permission, which is why it can carry the key.
    changed |= sync_search(pid, byname[FIND_INVOICE], INVOICES, [
        {'nodeId': byname[FIND_INVOICE]['id'], 'nodeType': GET_ONE, 'actionId': FROM_SHEET_ONE,
         'filedId': inf['Source Document']['controlId'], 'filedValue': 'Source Document', 'filedTypeId': TEXT,
         'enumDefault': 2, 'conditionId': EQ_C, 'sourceType': 0,
         'conditionValues': [{'nodeId': byname[GET_ORDER_NOW]['id'], 'controlId': of['Number']['controlId'],
                              'value': ''}]},
        {'nodeId': byname[FIND_INVOICE]['id'], 'nodeType': GET_ONE, 'actionId': FROM_SHEET_ONE,
         'filedId': inf['Status']['controlId'], 'filedValue': 'Status', 'filedTypeId': DROPDOWN,
         'enumDefault': 0, 'conditionId': IS_ANY_OF, 'sourceType': 0,
         'conditionValues': option_values(inf['Status'], ['Draft'])}],
        execute_type=0, sorts=[{'controlId': 'ctime', 'controlType': 16, 'isAsc': False}])
    # node 3's paths: the guard the double press runs into
    yes, no = None, None
    for path in paths_of(proc, byname[ANYTHING_BRANCH]['id']):
        nxt = proc['flowNodeMap'].get(path.get('nextId') or '', {}).get('name')
        if nxt == NOTHING_NOTICE:
            no = path
        elif nxt == MAKE_INVOICE:
            yes = path
    if not yes or not no:
        sys.exit(f'{ANYTHING_BRANCH}: could not tell the two paths apart')
    count_node = byname[COUNT_TO_INVOICE]['id']
    changed |= save_path(pid, yes, 'Yes', [[fx_cond(count_node, GTE_C, 1)]])
    changed |= save_path(pid, no, 'No', [[fx_cond(count_node, LT_C, 1)]])
    changed |= save_notice(pid, byname[NOTHING_NOTICE], MSG_NOTHING, dict(TRIGGER_USER))
    # node 6: the real filter, two OR-ed AND-groups, sorted Sequence ascending
    changed |= sync_search(pid, byname[LINES_TO_INVOICE], OLINES,
                           lines_filter_groups(lf, byname[LINES_TO_INVOICE]['id'],
                                               byname[GET_ORDER_NOW]['id']),
                           kind=GET_MANY, action=FROM_WORKSHEET, execute=True, splice=1,
                           sorts=[{'controlId': lf['Sequence']['controlId'], 'controlType': NUMBER,
                                   'isAsc': True}])
    # the header write, re-asserted in place (batch-add stores a create step's fields, but a text entry comes
    # back as a template and a Relation as nodeId+fieldValueId, so it is compared on `write_state`)
    changed |= set_entries(pid, byname[MAKE_INVOICE], header_entries(of, inf, byname), None, INVOICES)
    # the journal fallback for an order that names none
    changed |= ensure_journal_fallback(pid, of, inf, proc, byname)
    proc, byname = nodes_by_name(pid)
    # the inner flow
    inner_pid = inner_process_id(pid, byname[EACH_LINE])
    if not inner_pid:
        sys.exit(f'{EACH_LINE}: no subProcessId — the sub-process was not built')
    C.remember('workflows', KEY[ORDERS] + INNER_FLOW, inner_pid)
    params = sub_params(pid, byname[EACH_LINE])
    if INVOICE_PARAM not in params:
        sys.exit(f'{EACH_LINE}: no parameter named {INVOICE_PARAM!r}; it passes {sorted(params)}')
    param_id, param_value = params[INVOICE_PARAM]
    want_param = f"${byname[FIND_INVOICE]['id']}-rowid$"
    if param_value != want_param:
        sys.exit(f'{EACH_LINE}: the {INVOICE_PARAM} parameter passes {param_value!r}, wanted {want_param!r}')
    inner_proc, inner_by = nodes_by_name(inner_pid)
    inner_changed = False
    inner_changed |= sync_search(inner_pid, inner_by[INNER_GET_INVOICE], INVOICES, [{
        'nodeId': inner_by[INNER_GET_INVOICE]['id'], 'nodeType': GET_ONE, 'actionId': FROM_SHEET_ONE,
        'filedId': 'rowid', 'filedValue': 'Record ID', 'filedTypeId': TEXT, 'enumDefault': 0,
        'conditionId': EQ_C, 'sourceType': 0,
        'conditionValues': [{'nodeId': PARAM_NODE, 'controlId': param_id, 'value': ''}]}], execute_type=0)
    kinds = {}
    for path in paths_of(inner_proc, inner_by[KIND_BRANCH]['id']):
        nxt = inner_proc['flowNodeMap'].get(path.get('nextId') or '', {}).get('name')
        for k in LINE_KINDS:
            if nxt == MAKE_LINE[k]:
                kinds[k] = path
    missing = [k for k in LINE_KINDS if k not in kinds]
    if missing:
        sys.exit(f'{KIND_BRANCH}: no path runs into the create step for {missing}')
    start = inner_proc['startEventId']
    for k in LINE_KINDS:
        inner_changed |= save_path(inner_pid, kinds[k], KIND_PATH[k],
                                   [[cond(start, lf['Display Type'], IS_ANY_OF,
                                          option_values(lf['Display Type'], [k]))]])
        inner_changed |= set_entries(inner_pid, inner_by[MAKE_LINE[k]],
                                    line_entries(of, lf, ilf, k, start, inner_by), None, ILINES)
    # A `saveNode` marks the workflow as having unpublished changes even when it stores the same value, so the
    # published state is read, not assumed: `publishStatus` 2 is published, 1 is "there are changes".
    inner_dirty = published_status(inner_pid) != 2
    if inner_changed or inner_dirty:
        print(f'  {INNER_FLOW}:', C.publish(inner_pid))
        changed = True
    else:
        print(f'  {INNER_FLOW}: already built; not re-published')
    if changed or published_status(pid) != 2:
        print(f'  {CREATE_BUTTON}:', C.publish(pid))
    else:
        print(f'  {CREATE_BUTTON}: already built; not re-published')
    print(C.structure(pid))
    print(C.structure(inner_pid))
    report_create_binding(pid, byname)


def header_entries(of, inf, byname):
    """`header_fields` as stored field writes, bound to the live node ids."""
    node = byname[GET_ORDER_NOW]['id']
    out = []
    for f in header_fields(of, inf):
        if 'value' in f:
            out.append(patch(f['fieldId'], f['type'], value=f['value']))
        elif f['valueRef'].get('kind') == 'system':
            out.append(patch(f['fieldId'], f['type'], source=f['valueRef']['field'], system=True))
        else:
            out.append(patch(f['fieldId'], f['type'], node=node, source=f['valueRef']['fieldId']))
    return out


def line_entries(of, lf, ilf, kind, sub_start, inner_by):
    node_of = {'sub_trigger': sub_start, 'invoice': inner_by[INNER_GET_INVOICE]['id']}
    out = []
    for f in line_fields(of, lf, ilf, kind):
        if 'value' in f:
            out.append(patch(f['fieldId'], f['type'], value=f['value']))
        else:
            alias = f['valueRef']['node']['nodeAlias']
            out.append(patch(f['fieldId'], f['type'], node=node_of[alias], source=f['valueRef']['fieldId']))
    return out


def report_create_binding(pid, byname):
    """21 §13: **can a `create_record` node's own record be bound by a later node?** If it can, node 5 — the
    get_single that finds the invoice just made — disappears. The answer is read off the catalogue the server
    hands the node that follows the create: `workflow node get` on any node returns `flowNodeList`, the nodes
    and fields that node may reference (BUILDING.md)."""
    after = read_node(pid, byname[FIND_INVOICE]['id'])
    catalogue = {n.get('nodeId') or n.get('id'): n for n in after.get('flowNodeList') or []}
    make_id = byname[MAKE_INVOICE]['id']
    entry = catalogue.get(make_id)
    print(f'\n  {MAKE_INVOICE} ({make_id}) in the catalogue of {FIND_INVOICE}: '
          f'{"listed" if entry else "NOT listed"}')
    if entry:
        controls = entry.get('controls') or []
        print(f'    name={entry.get("name")!r} type={entry.get("nodeTypeId") or entry.get("nodeType")} '
              f'appId={entry.get("appId")} controls={len(controls)}')
        print(f'    a later node can therefore bind it; {FIND_INVOICE} is kept as the re-read that also '
              'proves the invoice reached the worksheet')


# ── 9 · the repair step ─────────────────────────────────────────────────────
#
# 21 §4.2 and §11.3. Odoo's `sale.order.invoice_ids` is a **compute** over `order_line.invoice_lines.move_id`
# (`sale_order.py:571-579`); here it is a stored Relation written by Create Invoice, so it can drift — a line
# deleted by hand, a run that died between the invoice and its lines. This step rebuilds it from the lines and
# reports every order where the two disagreed, plus the two half-finished shapes §11.3 names.

CUSTOMER_DOCS = ('Customer Invoice', 'Customer Credit Note')


def relation_rows(ws, rowid, control_id):
    """The records a Relation on one record points at, through `record relations` — the only read path that
    returns them: both halves of a 多↔多 come back from `record get` as a **row count**, and the listing drops
    them altogether when the control is hidden."""
    out, page = [], 1
    while True:
        res = hap.run('worksheet', 'record', 'relations', ws, rowid, control_id, '-a', APP, '-n', '200',
                      '-p', str(page))
        data = res.get('data', res) if isinstance(res, dict) else res
        rows = (data.get('rows') if isinstance(data, dict) else data) or []
        out += [r.get('rowId') or r.get('rowid') for r in rows]
        if len(rows) < 200:
            return [r for r in out if r]
        page += 1


def invoice_of_line():
    """{invoice line rowid: (its invoice rowid, its Document Type label)} for every invoice line."""
    ilf = fields(ILINES)
    doc = ilf[DOC_TYPE]['controlId']
    out = {}
    for r in C.records(ILINES, APP):
        d = read_record(ILINES, r['rowid'])
        move = [x.get('sid') for x in (d.get('move_id') or []) if isinstance(x, dict)]
        labels = cell_labels(d.get(ilf[DOC_TYPE].get('alias') or doc))
        out[r['rowid']] = (move[0] if move else None, labels[0] if labels else None)
    return out


def step_repair():
    """Rebuild Orders' Invoices from its lines' Invoice Lines and report every disagreement. Re-running the step
    reports nothing and saves nothing.

    Odoo's `_get_invoiced` keeps only moves whose `move_type` is `out_invoice` or `out_refund`
    (`sale_order.py:576`), so a Vendor Bill or a Journal Entry that somehow reached an order's lines is left out
    of the rebuilt list — and reported."""
    live = guard()
    of, lf = live[ORDERS], live[OLINES]
    invoices_control = of[O_INVOICES]['controlId']
    link = lf[OL_INVOICE_LINES]['controlId']
    per_line = invoice_of_line()
    orders = {r['rowid']: read_record(ORDERS, r['rowid']) for r in C.records(ORDERS, APP)}
    order_of_line, want = {}, {rowid: set() for rowid in orders}
    skipped, orphan_lines = [], []
    for r in C.records(OLINES, APP):
        d = read_record(OLINES, r['rowid'])
        parent = [x.get('sid') for x in (d.get('order_id') or []) if isinstance(x, dict)]
        order_of_line[r['rowid']] = parent[0] if parent else None
        if str(d.get('invoice_lines') or '0') in ('0', ''):
            continue
        for il in relation_rows(OLINES, r['rowid'], link):
            move, kind = per_line.get(il, (None, None))
            if not move:
                orphan_lines.append((il, r['rowid']))
                continue
            if kind not in CUSTOMER_DOCS:
                skipped.append((il, kind, order_of_line[r['rowid']]))
                continue
            if order_of_line[r['rowid']] in want:
                want[order_of_line[r['rowid']]].add(move)
    problems, fixed = [], 0
    hap.backup('o2i_orders_invoices_pre_repair',
               {rowid: relation_rows(ORDERS, rowid, invoices_control) for rowid in orders})
    for rowid, d in orders.items():
        got = set(relation_rows(ORDERS, rowid, invoices_control))
        if got == want[rowid]:
            continue
        print(f"  {d.get('name')}: Invoices held {len(got)} invoice(s), its lines say {len(want[rowid])}"
              f"\n    only on the order: {sorted(got - want[rowid])}"
              f"\n    only on the lines: {sorted(want[rowid] - got)}")
        write_record(ORDERS, rowid, [{'id': invoices_control, 'value': sorted(want[rowid])}])
        time.sleep(2)
        back = set(relation_rows(ORDERS, rowid, invoices_control))
        if back != want[rowid]:
            problems.append(f"{d.get('name')}: rebuilt list reads back {sorted(back)}, wanted "
                            f'{sorted(want[rowid])}')
        fixed += 1
    # §11.3's half-finished shapes
    headers = []
    inf = fields(INVOICES)
    lines_per_invoice = {}
    for il, (move, _kind) in per_line.items():
        if move:
            lines_per_invoice[move] = lines_per_invoice.get(move, 0) + 1
    for r in C.records(INVOICES, APP):
        d = read_record(INVOICES, r['rowid'])
        origin = d.get('invoice_origin') or ''
        if origin and not lines_per_invoice.get(r['rowid']):
            headers.append((r['rowid'], origin, d.get('name') or '(no number)'))
    print(f'  {fixed} order(s) rebuilt of {len(orders)}')
    if orphan_lines:
        print(f'  {len(orphan_lines)} invoice line(s) are linked to an order line but belong to no invoice: '
              f'{orphan_lines[:10]}')
    if skipped:
        print(f'  {len(skipped)} invoice line(s) on an order line belong to a document that is not a customer '
              f'invoice or credit note, and are left out as Odoo leaves them out: {skipped[:10]}')
    if headers:
        print(f'  {len(headers)} invoice(s) carry a Source Document and have no lines — a run that died '
              f'between the header and its lines, or a hand-emptied invoice:')
        for rowid, origin, number in headers:
            print(f'    {number} ({rowid}) from {origin}')
    if problems:
        sys.exit('  repair read back with differences:\n    ' + '\n    '.join(problems))
    return bool(fixed)


# ── 10 · the CLI self-check ─────────────────────────────────────────────────

def order_snapshot(rowid, of, lf):
    d = read_record(ORDERS, rowid)
    return {
        'Status': cell_labels(d.get('state')),
        'Invoice Status': cell_labels(d.get('invoice_status')),
        'Invoice Count': d.get('invoice_count'),
        'counts': {n: d.get(of[n]['controlId']) for n in
                   (N_PRODUCT, N_TO_INVOICE, N_NOTHING, N_INVOICED, N_UPSELLING)},
    }


def expected_status(snapshot):
    """The value §6.4's five ordered tests must produce, computed here from the same five counts."""
    prod, to_inv, _nothing, invoiced, upselling = (int(snapshot['counts'][n] or 0) for n in
                                                   (N_PRODUCT, N_TO_INVOICE, N_NOTHING, N_INVOICED,
                                                    N_UPSELLING))
    if snapshot['Status'] != ['Sales Order']:
        return ['Nothing to Invoice']
    if to_inv >= 1:
        return ['To Invoice']
    if prod >= 1 and invoiced == prod:
        return ['Fully Invoiced']
    if prod >= 1 and invoiced + upselling == prod:
        return ['Upselling Opportunity']
    return ['Nothing to Invoice']


def wait_for(fn, wanted, seconds=40):
    for _ in range(seconds):
        got = fn()
        if got == wanted:
            return got
        time.sleep(1)
    return fn()


def run_count(pid):
    runs = hap.run('approval', 'history', '--process-id', pid, '-n', '50')
    rows = (runs.get('data') or runs) if isinstance(runs, dict) else runs
    rows = rows.get('list') if isinstance(rows, dict) else rows
    return [(r.get('instanceId') or r.get('id'), r.get('status'), r.get('createDate')) for r in rows or []]


def step_selfcheck():
    """Drive steps 5 and 8 from the CLI on the TEST order, and put everything back.

    **It creates no invoice.** The TEST order is Fully Invoiced once `create` has run on it, so the press here
    proves the *guard*: the run takes the No path, ends at the notice and makes nothing. The invoice-making path
    was driven once while the bundle was built and its invoice is recorded in ids.json; a second one would be a
    record nobody can delete (06 has no Archive), which 21 §11.3 says to avoid."""
    live = guard()
    of, lf = live[ORDERS], live[OLINES]
    order = record_id(TEST_ORDER)
    if not order:
        sys.exit('no TEST order — run `fixture` first')
    problems = []
    start = order_snapshot(order, of, lf)
    print(f'  {TEST_ORDER}: {json.dumps(start, ensure_ascii=False)}')
    if start['Invoice Status'] != expected_status(start):
        problems.append(f"Invoice Status {start['Invoice Status']} does not match its own counts "
                        f"({expected_status(start)})")
    # ── the status workflow, driven by the order's own Status
    status = of['Status']
    was = [next(o['key'] for o in status['options'] if o['value'] == v) for v in start['Status']]
    for label, wanted in (('Quotation', ['Nothing to Invoice']), ('Sales Order', None)):
        write_record(ORDERS, order, [{'id': status['controlId'],
                                      'value': [option_key(ORDERS, 'Status', label)]}])
        want = wanted or expected_status({**order_snapshot(order, of, lf), 'Status': ['Sales Order']})
        got = wait_for(lambda: order_snapshot(order, of, lf)['Invoice Status'], want)
        print(f'  Status -> {label:<12} Invoice Status {got}  (wanted {want})')
        if got != want:
            problems.append(f'Status {label}: Invoice Status {got}, wanted {want}')
    if was:
        write_record(ORDERS, order, [{'id': status['controlId'], 'value': was}])
        time.sleep(4)
    # ── the status workflow, driven by a line
    chair = record_id(TEST_CHAIR)
    if chair:
        line = read_record(OLINES, chair)
        qty = numeric(line.get('product_uom_qty'))
        write_record(OLINES, chair, [{'id': lf['Quantity']['controlId'], 'value': (qty or 0) + 3}])
        got = wait_for(lambda: order_snapshot(order, of, lf)['Invoice Status'], ['To Invoice'])
        print(f'  {TEST_CHAIR} Quantity {qty} -> {(qty or 0) + 3}: Invoice Status {got} (wanted To Invoice)')
        if got != ['To Invoice']:
            problems.append(f'a line-driven change left Invoice Status {got}, wanted To Invoice')
        write_record(OLINES, chair, [{'id': lf['Quantity']['controlId'], 'value': qty}])
        back = wait_for(lambda: order_snapshot(order, of, lf)['Invoice Status'], start['Invoice Status'])
        print(f'  put back: Invoice Status {back} (wanted {start["Invoice Status"]})')
        if back != start['Invoice Status']:
            problems.append(f'after putting the quantity back, Invoice Status {back}, wanted '
                            f'{start["Invoice Status"]}')
    # ── Create Invoice pressed with nothing to invoice
    pid = hap.ids()['workflows'][KEY[ORDERS] + CREATE_BUTTON]
    proc, byname = nodes_by_name(pid)
    names = {n['id']: n['name'] for n in proc['flowNodeMap'].values()}
    invoices_before = {r['rowid'] for r in C.records(INVOICES, APP)}
    runs_before = {i for i, _s, _d in run_count(pid)}
    hap.run('workflow', 'trigger', pid, '-s', order)
    time.sleep(20)
    made = [r['rowid'] for r in C.records(INVOICES, APP) if r['rowid'] not in invoices_before]
    new_runs = [r for r in run_count(pid) if r[0] not in runs_before]
    print(f'  Create Invoice pressed with nothing to invoice: {len(made)} invoice(s) made, '
          f'{len(new_runs)} new run(s)')
    if made:
        problems.append(f'the press made {made}, and the order had nothing to invoice')
    for instance, status_code, when in new_runs:
        det = hap.run('approval', 'history-detail', instance)
        det = det.get('data', det) if isinstance(det, dict) else {}
        # a work item names its node under `flowNode.id`, not `flowNodeId`
        node_id = lambda w: (w.get('flowNode') or {}).get('id') if isinstance(w.get('flowNode'), dict) \
            else w.get('flowNodeId')
        passed = [names.get(node_id(w), node_id(w)) for w in det.get('works') or []]
        print(f'    run {instance} status {status_code} at {when} passed {passed}')
        if NOTHING_NOTICE not in passed:
            problems.append(f'the run did not reach {NOTHING_NOTICE!r}; it passed {passed}')
        if status_code != 2:
            problems.append(f'the run ended with status {status_code}, wanted 2 (a notice, not an abort)')
    # ── the invoice the build made, still as it should be
    made_before = record_id('TEST o2i invoice from Create Invoice')
    if made_before:
        d = read_record(INVOICES, made_before)
        inf = fields(INVOICES)
        checks = {
            'Type': cell_labels(d.get('move_type')) == ['Customer Invoice'],
            'Source Document': (d.get('invoice_origin') or '') == (read_record(ORDERS, order).get('name') or ''),
            'Payment Terms': bool(d.get('invoice_payment_term_id')),
            'Accounting Date': bool(d.get('date')),
            'Sales Orders': str(d.get(inf[I_ORDERS]['controlId']) or '0') != '0',
        }
        print(f'  the invoice the build made ({made_before}): {checks}')
        problems += [f'the built invoice fails {k}' for k, v in checks.items() if not v]
    print('  selfcheck: ' + ('OK' if not problems else 'DIFFERENCES\n    ' + '\n    '.join(problems)))
    return len(problems)


# ── check — read-only ───────────────────────────────────────────────────────

ALL_CONTROLS = (DOC_TYPE, ORDER_STATE, OL_INVOICE_LINES, IL_ORDER_LINES, O_INVOICES, I_ORDERS,
                O_INVOICE_COUNT, I_ORDER_COUNT, QTY_INVOICES, QTY_REFUNDS, QTY_TO_INVOICE, LINE_STATUS,
                INVOICEABLE, N_TO_INVOICE, N_NOTHING, N_INVOICED, N_UPSELLING, N_PRODUCT)


def check_journal_fallback(live):
    """The invoice **must** carry a Journal: it is required on Invoices, so without one the document cannot be
    confirmed from the form (found in the browser on 23 Sep 2026). Asserted three ways — the chain is there, it
    is configured as Odoo picks the journal, and every invoice this bundle's presses made carries one."""
    of, inf = live[ORDERS], live[INVOICES]
    pid = hap.ids()['workflows'][KEY[ORDERS] + CREATE_BUTTON]
    proc, byname = nodes_by_name(pid)
    problems = []
    print('  the journal fallback')
    for name in (SALES_JOURNAL, JOURNAL_BRANCH, SET_JOURNAL):
        if name not in byname:
            problems.append(f'{CREATE_BUTTON} has no step {name!r}')
    if problems:
        print('    missing: ' + ', '.join(problems))
        return problems
    # it sits between the invoice and its lines, so 07's account automation can read the journal
    after_found = proc['flowNodeMap'][byname[FIND_INVOICE]['id']].get('nextId')
    if after_found != byname[SALES_JOURNAL]['id']:
        problems.append(f'{SALES_JOURNAL!r} does not follow {FIND_INVOICE!r}')
    converges = proc['flowNodeMap'][byname[JOURNAL_BRANCH]['id']].get('nextId')
    if converges != byname[LINES_TO_INVOICE]['id']:
        problems.append(f'{JOURNAL_BRANCH!r} does not converge on {LINES_TO_INVOICE!r}')
    s = read_node(pid, byname[SALES_JOURNAL]['id'])
    got = (s.get('appId'), s.get('executeType'),
           [(x.get('controlId'), bool(x.get('isAsc'))) for x in s.get('sorts') or []],
           [f.get('spliceType') for f in s.get('filters') or []],
           wf_filter_state(s.get('filters')))
    want = (JOURNALS, 2, [(J_SEQUENCE, True), (J_PREFIX, True)], [1],
            wf_filter_state([{'conditions': [sales_journal_filter(byname[SALES_JOURNAL]['id'])]}]))
    print(f'    {SALES_JOURNAL}: worksheet Journals, Type is Sales and Active ticked, '
          f'sorted Sequence then Sequence Prefix ascending, carry on when there is none')
    if got != want:
        problems.append(f'{SALES_JOURNAL}: reads back {got}, wanted {want}')
    # the branch writes only when the order names no journal
    no = next((p for p in paths_of(proc, byname[JOURNAL_BRANCH]['id'])
               if proc['flowNodeMap'].get(p.get('nextId') or '', {}).get('name') == SET_JOURNAL), None)
    if no is None:
        problems.append(f'{JOURNAL_BRANCH}: no path runs into {SET_JOURNAL!r}')
    else:
        want_path = [condition_state([cond(byname[GET_ORDER_NOW]['id'], of['Journal'], EMPTY_C)])]
        if path_state(read_node(pid, no['id'])) != want_path:
            problems.append(f'the {SET_JOURNAL!r} path is not conditioned on the order\'s Journal being empty')
    u = read_node(pid, byname[SET_JOURNAL]['id'])
    entry = next((x for x in u.get('fields') or [] if x.get('fieldId') == inf['Journal']['controlId']), None)
    if not entry or entry.get('nodeId') != byname[SALES_JOURNAL]['id'] or entry.get('fieldValueId') != 'rowid':
        problems.append(f'{SET_JOURNAL} does not write Invoices / Journal from {SALES_JOURNAL!r}')
    if u.get('selectNodeId') != byname[FIND_INVOICE]['id']:
        problems.append(f'{SET_JOURNAL} updates {u.get("selectNodeId")}, wanted the invoice it just made')
    # and the invoices the presses actually made
    for key in ('TEST o2i invoice from Create Invoice', 'TEST o2i second invoice from Create Invoice',
                'TEST o2i invoice from an order with no journal'):
        rowid = record_id(key)
        if not rowid:
            continue
        d = read_record(INVOICES, rowid)
        journal = [x.get('name') for x in (d.get('journal_id') or []) if isinstance(x, dict)]
        print(f'    {key}: Journal {journal}')
        if not journal:
            problems.append(f'{key} ({rowid}) carries no Journal')
    return problems


def step_check():
    """Every control, workflow, view and button this bundle owns, read off the app. Writes nothing."""
    live = guard()
    problems = []
    print('  controls')
    for name in ALL_CONTROLS:
        ws = WHERE[name]
        c = live[ws].get(name)
        if c is None:
            problems.append(f'{NAME[ws]} has no {name!r}')
            continue
        recorded = hap.ids().get('controls', {}).get(KEY[ws] + name)
        if recorded != c['controlId']:
            problems.append(f'ids.json holds {recorded} for {name!r}, live is {c["controlId"]}')
        extra = ''
        if c['type'] == FUNCTION:
            extra = f' fx={function_expression(c)[:70]}'
        elif c['type'] == ROLLUP:
            extra = f' ds={c.get("dataSource")} agg={c.get("enumDefault")} ' \
                    f'filters={filter_state((c.get("advancedSetting") or {}).get("filters"))}'
        elif c['type'] == FORMULA:
            extra = f' ds={c.get("dataSource")}'
        elif c['type'] == LOOKUP:
            extra = f' ds={c.get("dataSource")} src={c.get("sourceControlId")} strDefault={c.get("strDefault")}'
        elif c['type'] == RELATION:
            extra = f' -> {c.get("dataSource")} enumDefault={c.get("enumDefault")} ' \
                    f'sourceControlType={c.get("sourceControlType")}'
        print(f"    {NAME[ws]:<14} {name:<20} {c['controlId']} t{c['type']:<3} alias={c.get('alias') or '-':<18} "
              f"perm={c.get('fieldPermission')} r{c.get('row')}{extra}")
    print('  Quantity Invoiced (converted in place)')
    qi = live[OLINES][QTY_INVOICED]
    print(f"    {qi['controlId']} t{qi['type']} perm={qi.get('fieldPermission')} ds={qi.get('dataSource')} "
          f"adv={json.dumps(qi.get('advancedSetting'), sort_keys=True)}")
    if qi['type'] != FORMULA:
        problems.append(f'{QTY_INVOICED} is t{qi["type"]}, wanted a Formula (t{FORMULA})')
    sub = next(c for c in hap.controls(ORDERS) if c['controlId'] == O_SUBTABLE)
    if live[OLINES][QTY_TO_INVOICE]['controlId'] not in (sub.get('showControls') or []):
        problems.append(f'{QTY_TO_INVOICE} is not a column of the Orders subtable')
    print('  workflows')
    for name in list(STATUS_WORKFLOWS) + [KEY[ORDERS] + CREATE_BUTTON, KEY[ORDERS] + INNER_FLOW]:
        pid = hap.ids().get('workflows', {}).get(name)
        if not pid:
            problems.append(f'ids.json has no workflow {name!r}')
            continue
        w = hap.run('workflow', 'get', pid)
        w = w.get('data', w) if isinstance(w, dict) else {}
        proc = hap.run('workflow', 'node', 'list', pid)
        print(f"    {name:<52} {pid} publishStatus={w.get('publishStatus')} "
              f"enabled={w.get('enabled')} nodes={len(proc['flowNodeMap'])}")
        if w.get('publishStatus') != 2:
            problems.append(f'{name}: publishStatus {w.get("publishStatus")}, wanted 2')
    problems += check_journal_fallback(live)
    print('  the gated automations')
    for label, pid in ((PT_WORKFLOW, PT_PID), (ACCOUNT_WORKFLOW, ACCOUNT_PID)):
        w = hap.run('workflow', 'get', pid)
        w = w.get('data', w) if isinstance(w, dict) else {}
        print(f'    {label:<52} {pid} publishStatus={w.get("publishStatus")}')
    inf = fields(INVOICES)
    proc = hap.run('workflow', 'node', 'list', PT_PID)
    gated = 0
    for n in proc['flowNodeMap'].values():
        if n.get('typeId') != 2:
            continue
        d = read_node(PT_PID, n['id'])
        if d.get('name') in (PT_CUSTOMER_PATH, PT_VENDOR_PATH):
            if any(c.get('filedId') == inf['Payment Terms']['controlId'] and str(c.get('conditionId')) == EMPTY_C
                   for g in d.get('conditions') or [] for c in g):
                gated += 1
    print(f'    Payment Terms gated on being empty: {gated} of 2 paths')
    if gated != 2:
        problems.append(f'the Payment Terms automation is gated on {gated} of 2 paths')
    print('  views and the button')
    C.print_views(ORDERS, APP)
    for b in hap.listing('worksheet', 'custom-actions', ORDERS):
        if b['name'] == CREATE_BUTTON:
            print(f"    {b['name']} btnId={b['btnId']} isBatch={b.get('isBatch')} "
                  f"filters={[(f['filterType'], f.get('values')) for f in b.get('filters') or []]}")
    parked = [(n, live[WHERE[n]][n].get('row')) for n in ALL_CONTROLS
              if n in live[WHERE[n]] and live[WHERE[n]][n].get('row') == 9999]
    if parked:
        print(f'  {len(parked)} control(s) still at row 9999 — placement is the owner\'s:')
        for n, _row in parked:
            r, col, size, where = PLACE[n]
            print(f'    {NAME[WHERE[n]]:<14} {n:<20} intended ({r}, {col}, {size})  {where}')
    print('  check: ' + ('OK' if not problems else 'DIFFERENCES\n    ' + '\n    '.join(problems)))
    return len(problems)


def main():
    steps = {'lookups': step_lookups, 'relations': step_relations, 'fixture': step_fixture,
             'qty': step_qty, 'toinvoice': step_toinvoice, 'status': step_status, 'views': step_views,
             'guards': step_guards, 'create': step_create, 'repair': step_repair,
             'selfcheck': step_selfcheck, 'check': step_check}
    if len(sys.argv) != 2 or sys.argv[1] not in steps:
        sys.exit(f'usage: o2i.py <{"|".join(steps)}>')
    steps[sys.argv[1]]()


if __name__ == '__main__':
    main()
