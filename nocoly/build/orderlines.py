#!/usr/bin/env python3
"""What Order Lines (Odoo `sale.order.line`) still owed in ERP Master — and nothing the owner built by hand.

    ~/.hap-venv/bin/python nocoly/build/orderlines.py fields     # 1. Tax rate (汇总), Lead Time, Optional Line,
                                                                 #    appended with no client-side id
    ~/.hap-venv/bin/python nocoly/build/orderlines.py computed   # 2. Orders and Description required — one
                                                                 #    pinned save
    ~/.hap-venv/bin/python nocoly/build/orderlines.py formulas   # 3. Subtotal, Tax Amount and Total stop being
                                                                 #    Currency controls carrying a function
                                                                 #    default and become type 31 Formulas — one
                                                                 #    pinned save
    ~/.hap-venv/bin/python nocoly/build/orderlines.py rules      # 4. a section or a note carries no figures
    ~/.hap-venv/bin/python nocoly/build/orderlines.py alias      # 5. the Odoo field names into `alias`, one
                                                                 #    pinned save
    ~/.hap-venv/bin/python nocoly/build/orderlines.py wipe       # 6. delete the two test lines the owner
                                                                 #    approved (children before parents)
    ~/.hap-venv/bin/python nocoly/build/orderlines.py seed       # 7. the tenant's thirty lines
    ~/.hap-venv/bin/python nocoly/build/orderlines.py figures    # 8. each line's computed Subtotal, Tax Amount
                                                                 #    and Total beside the tenant's own
    ~/.hap-venv/bin/python nocoly/build/orderlines.py check      # read everything back and report drift
    ~/.hap-venv/bin/python nocoly/build/orderlines.py show       # the live controls and rules

**The owner hand-built this worksheet in the browser**, sixteen controls between 21 Sep 2026's two rebuilds, and
they are still working in it. HAP has no per-field endpoint — hap-cli's own `field update` goes through
`SaveWorksheetControls` too — so an ordinary `layout` step would replace the whole control set and revert
whatever they had typed since the read. **There is therefore no `fields`-as-full-save, no `layout` and no
`views` step here, and there must not be one.** Every step that touches a *control* is one of two shapes
(`wipe`, `seed` and `figures` touch records, not controls):

  * an **append** (`common.append_controls`) — `AddWorksheetControls` with no `controlId`, so the server mints
    real ids and nothing that was already on the worksheet is re-sent;
  * a **narrow, version-pinned save** — `common.controls_with_version` then `common.save_controls(…,
    version=…)`, which refuses (code 10, 数据过时) if the owner saved in between, followed by a signature diff
    proving the save changed only the controls this step names. The pattern is `products.py step_perms`.

Nothing here opens the Sales app, and nothing here deletes or creates a **control**. `wipe` deletes the two
records the owner explicitly approved clearing and `seed` creates the tenant's thirty lines; both are scoped to
this worksheet's own rows. Requirements:
nocoly/worksheets/16-orders.md §2 (Lines) and §7.2. Generic helpers: common.py.
"""
import json
import sys

import common as C
import hap
import orders as O                                 # control_state / signature: one definition of a control's state

APP = hap.ids()['app']
SECTION, WORKSHEET = 'Sales', 'Order Lines'
KEY = WORKSHEET + ': '                             # ids.json key prefix for everything this worksheet owns

# The worksheet and its sixteen controls are the owner's, not this script's, so their ids are constants here
# rather than something a `create` step minted. Read off the app on 21 Sep 2026; `guard` checks every one of
# them, because a control the owner replaces rather than edits gets a new id and a rule or a roll-up that keeps
# the dead one is stored, published and silently does nothing (BUILDING.md).
WS = '6ab0c740e43d174ab37535b2'
ORDERS = '6ab09897e43d174ab3752d7b'                # the parent; only orders.py writes to it
INVLINES = '6aaa2b50e54d2a34fa4e0221'              # Invoice Lines — the reference for Tax rate and for the rule

NUMBER, CURRENCY, DROPDOWN, RELATION, FORMULA, SWITCH, ROLLUP = 6, 8, 11, 29, 31, 36, 37
EQ_SINGLE = 51                                     # a 汇总's own filter: the *view* editor's "is" (BUILDING.md)

CONTROLS = {                                       # name -> id, read off the app on 21 Sep 2026
    'Orders': '6ab0c740e43d174ab37535b1',
    'Sequence': '6ab0c740e43d174ab37535b7',
    'Display Type': '6ab0c864e43d174ab37535f7',
    'Product': '6ab0c864e43d174ab37535f8',
    'Description': '6ab0c864e43d174ab37535fa',
    'Quantity': '6ab0c864e43d174ab37535fb',
    'Quantity Invoiced': '6ab0c864e43d174ab37535fc',
    'Quantity Delivered': '6ab0c864e43d174ab37535fd',
    'Unit': '6ab0c984e43d174ab3753634',
    'Unit Price': '6ab0ca1be43d174ab3753657',
    'Discount': '6ab0ca1be43d174ab3753658',
    'Taxes': '6ab0c984e43d174ab3753636',
    'Tax Amount': '6ab0cad0805aef703286d83d',
    'Subtotal': '6ab0ca80805aef703286d82a',
    'Total': '6ab0cad0805aef703286d83e',
    'Product Unit': '6ab0c984e43d174ab3753638',
}

# Display Type's options, minted by the owner on their own control. Odoo's `display_type` — `line_section`,
# `line_subsection`, `line_note` — plus the explicit fourth value **Product** that stands for Odoo's NULL,
# exactly as Invoice Lines does (16-orders.md §2 › Lines).
DISPLAY_TYPE_KEYS = {
    'Product': '1d0faacc-2a0f-490d-b339-d077c034bc62',
    'Section': '95b10f68-72da-466f-80e5-1e43d694249e',
    'Subsection': '83f20d55-b006-4ce3-865f-5d054ad9261d',
    'Note': 'a9150ecb-c7fa-4601-b84a-da01a31f1003',
}
TEXT_LINES = ('Section', 'Subsection', 'Note')      # Odoo's non-accountable display types

# ── the Taxes worksheet, through Invoice Lines' own Tax rate ─────────────────
# Both ids belong to Taxes (13-taxes.md) and are read back off Invoice Lines' Tax rate at build time rather
# than trusted from here, so the two roll-ups cannot drift apart.
TAX_AMOUNT_COL = '6aad104e7d58b0f4493141fc'         # Taxes / Amount — what the 汇总 sums
TAX_COMPUTATION_COL = '6aad104e7d58b0f4493141fb'    # Taxes / Tax Computation — what its filter tests
TAX_PERCENTAGE = 'a7101f45-bf00-4b19-98bd-08c62094258a'
RATE = 'Tax rate'

# ── the three controls this builder appends ─────────────────────────────────
#
# `add-fields` **parks everything it adds at row 9999, col 0** whatever the payload says, and only a full save
# places a control (BUILDING.md). A full save is exactly what this builder must not make, so the places below
# are the intent recorded for the owner, not what will read back: they will find the three at the foot of the
# form and place them in the designer. `size` and the rest of the payload are kept.
NEW = ('Tax rate', 'Lead Time', 'Optional Line')
PLACE = {'Tax rate': (9, 0, 6), 'Lead Time': (9, 1, 6), 'Optional Line': (10, 0, 6)}
DOT = {'Tax rate': 4, 'Lead Time': 0}               # Odoo's amount is float(16, 4); customer_lead is a day count
DESC = {
    # Odoo `sale.order.line.customer_lead` help, verbatim
    'Lead Time': 'Number of days between the order confirmation and the shipping of the products.',
}

# Odoo field names. `sale.order.line` for all but two: **tax_rate** is a helper this app invented (Invoice
# Lines carries the same one) and **product_uom_name** is the related display field Odoo puts on the line.
ALIAS = {
    'Orders': 'order_id', 'Sequence': 'sequence', 'Display Type': 'display_type', 'Product': 'product_id',
    'Description': 'name', 'Quantity': 'product_uom_qty', 'Quantity Invoiced': 'qty_invoiced',
    'Quantity Delivered': 'qty_delivered', 'Unit': 'product_uom_id', 'Unit Price': 'price_unit',
    'Discount': 'discount', 'Taxes': 'tax_ids', 'Tax Amount': 'price_tax', 'Subtotal': 'price_subtotal',
    'Total': 'price_total', 'Lead Time': 'customer_lead', 'Optional Line': 'is_optional',
    'Tax rate': 'tax_rate', 'Product Unit': 'product_uom_name',
}

REQUIRED = ('Orders', 'Description')                # Odoo: order_id and name are both required=True

# The **worksheet's** own alias, which is a different thing from a control's: BUILDING.md's convention is the Odoo
# model name with underscores, and this worksheet was hand-built with none. Orders' is `quotation` and **keeps
# it** — the subtable, its back-relation and the roll-ups all reference that worksheet, and nothing here renames
# one that is already set.
WS_ALIAS = 'sale_order_line'


def ws():
    return hap.ids().get('worksheets', {}).get(WORKSHEET, WS)


# ── guard ───────────────────────────────────────────────────────────────────

def guard():
    """Stop unless the profile reaches ERP Master › Sales › Order Lines and the controls this builder names are
    the ones it was written against. Returns the live controls by name.

    Like `orders.guard` it deliberately does **not** insist the worksheet hold only the controls it knows: the
    owner is adding fields by hand, and a builder that stopped on an unfamiliar control would stop every time
    they did."""
    who = hap.run('auth', 'whoami')
    app = hap.run('app', 'info', '-a', APP).get('data', {})
    section = next((s for s in app.get('sections', []) if any(i['id'] == WS for i in s['items'])), None)
    if app.get('name') != 'ERP Master' or not section or section['name'] != SECTION:
        sys.exit(f"profile {who.get('profile')!r} does not reach ERP Master › {SECTION} › {WORKSHEET}")
    C.remember('worksheets', WORKSHEET, WS)
    C.remember('sections', SECTION, section['id'])
    f = C.fields(ws())
    problems = [f'{name} is {(f.get(name) or {}).get("controlId")}, expected {cid}'
                for name, cid in CONTROLS.items() if (f.get(name) or {}).get('controlId') != cid]
    if problems:
        sys.exit(f'{WORKSHEET}: ' + '; '.join(problems) + ' — re-read the worksheet before writing anything')
    parent = f['Orders']
    if parent['type'] != RELATION or parent.get('dataSource') != ORDERS:
        sys.exit(f'the Orders relation {parent["controlId"]} is t{parent["type"]} '
                 f'ds={parent.get("dataSource")!r}, expected a Relation (t{RELATION}) to Orders {ORDERS} — '
                 'it is the back-relation of the subtable and everything hangs off it')
    dt = f['Display Type']
    keys = {o['value']: o['key'] for o in dt.get('options') or [] if not o.get('isDeleted')}
    if any(keys.get(label) != key for label, key in DISPLAY_TYPE_KEYS.items()):
        sys.exit(f'Display Type options are {keys}, expected {DISPLAY_TYPE_KEYS} — re-read the option table')
    unknown = sorted(set(f) - set(CONTROLS) - set(NEW))
    if unknown:
        print(f'  note: {WORKSHEET} also carries {unknown} — added by the owner, and nothing here names them')
    for name, cid in CONTROLS.items():
        C.remember('controls', KEY + name, cid)
    return f


# ── the version-pinned save, and the proof it changed only what it meant to ─

def pinned_save(step, describe, apply, backup):
    """One `SaveWorksheetControls` of the list just read, with `apply` free to change the controls it is given,
    and a signature diff proving nothing else moved. Returns the ids that changed.

    `version` pins HAP's optimistic lock: a control save the owner makes between the read and the save refuses
    this one (code 10, 数据过时) instead of being overwritten, which is the whole point on a worksheet they are
    hand-building. The pattern is `products.py step_perms`; `orders.py step_expiry` is the same shape."""
    ctrls, version = C.controls_with_version(ws())
    hap.backup(backup, ctrls)
    before = O.signature(ctrls)
    wanted = apply(ctrls)
    if not wanted:
        print(f'  {step}: already as specified; nothing saved')
        return []
    C.save_controls(ws(), ctrls, version=version)
    live = hap.controls(ws())
    after = O.signature(live)
    changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    names = {c['controlId']: c['controlName'] for c in live}
    if changed != sorted(wanted):
        sys.exit(f'{step}: the save changed {[names.get(k, k) for k in changed]}, wanted only '
                 f'{[names.get(k, k) for k in sorted(wanted)]}\n' +
                 '\n'.join(f'  {names.get(k, k)}\n    was {before.get(k)}\n    now {after.get(k)}'
                           for k in changed))
    print(f'  {step}: {describe} — {len(before)} controls compared, no other change')
    return changed


# `orders.py` owns the one definition of a control's comparable state, and of the {key: (got, want)} drift over
# it; both are used here rather than copied, so a change to either reaches both worksheets.
drift, set_value = O.drift, O.set_value


# ── 1 · the three controls Order Lines was missing ──────────────────────────

def reference_rate():
    """Invoice Lines' own Tax rate, checked against what this build expects of it, and its filter **as stored**.

    The filter string is reused byte for byte rather than rebuilt, so the two worksheets' roll-ups cannot drift:
    both count only the taxes whose *Tax Computation* is **Percentage**, which is what stops a Fixed or Custom
    Formula tax adding its amount as if it were a rate. A 汇总's own filter is the **view** editor's enum, where
    a single select's "is" is `filterType` **51** — not the 2 a business rule uses (BUILDING.md)."""
    c = next((c for c in hap.controls(INVLINES) if c['controlName'] == RATE), None)
    if c is None or c['type'] != ROLLUP:
        sys.exit(f'Invoice Lines has no {RATE} 汇总 to copy — read {INVLINES} before running this step')
    raw = (c.get('advancedSetting') or {}).get('filters') or ''
    try:
        conds = json.loads(raw)
    except ValueError:
        sys.exit(f'Invoice Lines / {RATE}: advancedSetting.filters is not JSON: {raw[:200]!r}')
    got = [{k: f.get(k) for k in ('controlId', 'dataType', 'spliceType', 'filterType', 'values')} for f in conds]
    want = [{'controlId': TAX_COMPUTATION_COL, 'dataType': DROPDOWN, 'spliceType': 1,
             'filterType': EQ_SINGLE, 'values': [TAX_PERCENTAGE]}]
    if got != want:
        sys.exit(f'Invoice Lines / {RATE}: filter is {got}, expected {want}')
    if (c.get('sourceControlId'), c.get('enumDefault'), c.get('dot')) != (TAX_AMOUNT_COL, 5, DOT[RATE]):
        sys.exit(f'Invoice Lines / {RATE}: src={c.get("sourceControlId")} enumDefault={c.get("enumDefault")} '
                 f'dot={c.get("dot")}, expected {TAX_AMOUNT_COL} / 5 / {DOT[RATE]}')
    print(f"  reference: Invoice Lines / {RATE} {c['controlId']} — sum of Taxes/Amount through its Taxes "
          f'relation, Tax Computation is Percentage (filterType {EQ_SINGLE})')
    return c, raw


def new_controls(f, ref, filters):
    """The three controls, as `append_controls` takes them (its own copy drops the `controlId`)."""
    return {
        # Odoo has no `tax_rate` on a sale order line: it is the same helper Invoice Lines carries, and it is
        # what makes Tax Amount computable from the taxes the line points at. Hidden **and** read-only —
        # nobody types a roll-up.
        RATE: C.control('SUBTOTAL', RATE, PLACE[RATE], alias='', hint='', desc=ref.get('desc') or '',
                        hidden=True, readonly=True,
                        data_source=f['Taxes']['controlId'], source_control_id=TAX_AMOUNT_COL,
                        extra={'enumDefault': 5, 'dot': DOT[RATE]},
                        advanced_setting={'roundtype': '2', 'sorttype': 'zh', 'filters': filters}),
        # `customer_lead`, an integer number of days. Odoo defaults it to 0 and the form is the only thing that
        # applies a default here, so a line created through the API carries nothing.
        'Lead Time': C.control('NUMBER', 'Lead Time', PLACE['Lead Time'], alias='', hint='',
                               desc=DESC['Lead Time'], extra={'dot': DOT['Lead Time']},
                               advanced_setting={'defsource': C.static_default(0)}),
        # `is_optional` — Odoo's optional-products line.
        'Optional Line': C.control('SWITCH', 'Optional Line', PLACE['Optional Line'], alias='', hint='',
                                   desc=''),
    }


def new_spec(f, ref, filters):
    """What each appended control must read back as. `fieldPermission` is enforced on Tax rate only: a control
    added with `add-fields` stores it as `""` and only a save that sends `"111"` writes the default (BUILDING.md),
    and `""` is what every one of the owner's own controls on this worksheet reads — so Lead Time and Optional
    Line are left exactly as the append leaves them."""
    return {
        RATE: {'type': ROLLUP, 'dot': DOT[RATE], 'required': False, 'fieldPermission': '001',
               'enumDefault': 5, 'dataSource': f'${f["Taxes"]["controlId"]}$',
               'sourceControlId': TAX_AMOUNT_COL, 'desc': ref.get('desc') or '',
               'advancedSetting.filters': filters},
        'Lead Time': {'type': NUMBER, 'dot': DOT['Lead Time'], 'desc': DESC['Lead Time'],
                      'advancedSetting.defsource': C.static_default(0)},
        'Optional Line': {'type': SWITCH,
                          'advancedSetting.defsource': C.static_default(0)},
    }


def step_fields():
    """Append Tax rate, Lead Time and Optional Line — `AddWorksheetControls` with **no client-side id**, so the
    server mints real ids and not one of the owner's sixteen controls is re-sent.

    Not `C.add_fields`: that appends and then re-saves the whole control set, which is the clobber this builder
    exists to avoid. The 汇总 can be appended this way because nothing references *it* and everything *it*
    references — the Taxes relation and the Taxes worksheet's Amount — already carries a server id; the
    re-mint a formula needs does not apply.

    An append is then checked, and anything it dropped is repaired in one version-pinned save limited to the
    ids just minted."""
    f = guard()
    ref, filters = reference_rate()
    missing = [n for n in NEW if n not in f]
    if missing:
        hap.backup('orderlines_controls_pre_fields', hap.controls(ws()))
        built = new_controls(f, ref, filters)
        C.append_controls(ws(), [built[n] for n in missing])
        f = C.fields(ws())
        gone = [n for n in missing if n not in f]
        if gone:
            sys.exit(f'{gone} did not come back from the worksheet — the append did not store')
        for n in missing:
            print(f"  added {n}: {f[n]['controlId']} (t{f[n]['type']}, row {f[n].get('row')} — `add-fields` "
                  f'parks a new control at row 9999; the owner places it)')
    else:
        print(f'  {list(NEW)} are already on {WORKSHEET}; nothing appended')
    spec = new_spec(f, ref, filters)
    stale = {n: drift(f[n], spec[n]) for n in NEW if drift(f[n], spec[n])}
    if stale:
        print('  the append did not store everything; repairing in one pinned save:')
        for n, diff in stale.items():
            for k, (got, want) in diff.items():
                print(f'    {n}.{k}: {got!r} -> {want!r}')

        def apply(ctrls):
            ids = []
            for c in ctrls:
                if c['controlName'] in stale:
                    for k, (_got, _want) in stale[c['controlName']].items():
                        set_value(c, k, spec[c['controlName']][k])
                    ids.append(c['controlId'])
            return ids
        pinned_save('fields', f'{sorted(stale)} repaired', apply, 'orderlines_controls_pre_fields_repair')
        f = C.fields(ws())
        left = {n: drift(f[n], spec[n]) for n in NEW if drift(f[n], spec[n])}
        if left:
            sys.exit(f'{WORKSHEET}: read back with differences {json.dumps(left, ensure_ascii=False)}')
    for n in NEW:
        C.remember('controls', KEY + n, f[n]['controlId'])
    report(f)
    return True


# ── 2 · two fields become required ──────────────────────────────────────────

def computed_spec(f):
    """{control name: {key: value}} — everything the `computed` step owns.

    It owned Tax Amount's **function default** until 21 Sep 2026 as well; that is `formulas`' now, and the reason
    the two figures are computed a different way is in `step_formulas`."""
    return {  # Odoo `sale.order.line.order_id` is required=True, and 07's test 8 showed that requiring the parent
              # is what stops an orphan line being created from the standalone worksheet.
            'Orders': {'required': True},
            # Odoo `sale.order.line.name` is required=True too. Description already auto-fills from the Product
            # (the owner's dynamic default, cid 6aa90cd04720c515252bf923 through the Product relation), so the
            # flag costs a person nothing on a product line — and on a section or a note the text *is* the field.
            'Description': {'required': True}}


def step_computed():
    """`required` on Orders and Description — one version-pinned save that changes those two controls and
    nothing else."""
    f = guard()
    spec = computed_spec(f)
    stale = {n: drift(f[n], spec[n]) for n in spec if drift(f[n], spec[n])}
    for n, diff in stale.items():
        for k, (got, want) in diff.items():
            print(f'  {n}.{k}: {got!r} -> {want!r}')

    def apply(ctrls):
        ids = []
        for c in ctrls:
            if c['controlName'] in stale:
                for k in stale[c['controlName']]:
                    set_value(c, k, spec[c['controlName']][k])
                ids.append(c['controlId'])
        return ids
    changed = pinned_save('computed', f'{sorted(stale)} written', apply, 'orderlines_controls_pre_computed')
    f = C.fields(ws())
    left = {n: drift(f[n], spec[n]) for n in spec if drift(f[n], spec[n])}
    if left:
        sys.exit(f'computed read back with differences: {json.dumps(left, ensure_ascii=False)}')
    return bool(changed)


# ── 3 · Subtotal, Tax Amount and Total become Formulas ──────────────────────
#
# **A control whose value must exist on an API write must be a Formula.** A *function default*
# (`advancedSetting.defaulttype` "1" with a `defaultfunc`) is evaluated **client-side in the form** and the API
# applies no defaults at all (BUILDING.md), so a row written by a script stores nothing there. Two separate
# failures followed from the one cause:
#
#   * Tax rate is a 汇总 (type 37) computed on the server, so even **in the form** it has no value at the moment a
#     function default runs and the expression yields nothing. Proved in the UI on 21 Sep 2026: a line saved with a
#     percentage tax picked stored Tax Amount blank, and because Total's own function default was
#     `Subtotal + Tax Amount` it stored blank too — so the order's roll-ups read Untaxed 270 / Tax 0 / Total 0
#     while the line's Tax rate 汇总 held 3.0000 all along.
#   * **Subtotal's** own function default reads Quantity, Unit Price and Discount — plain numbers on its own row —
#     so it computes correctly *in the form*, which is why it was left alone at first. But all thirty seeded lines
#     were written through the API, so every one of them stored Subtotal **empty**, which left Tax Amount and
#     Total (Formulas built on it) empty as well and every order roll-up reading 0.00. The owner approved the
#     conversion on 21 Sep 2026 in exchange for losing the RM prefix: a Formula carries no currency. Nothing is
#     lost converting — every Subtotal was already blank.
#
# Invoice Lines is the working shape for all three: its Subtotal and Total are type 31 **Formulas**, the second
# reading the same kind of roll-up, and its stored rows are right (1798.00 → 1977.80 at 10 %, 850.00 → 918.00 at
# 8 %, 18000.00 → 19440.00 at 8 %). Both expressions are rebuilt from **07's own stored formulas** rather than from
# a string typed here, so the two worksheets cannot drift apart.
#
# One thing this step cannot copy from 07 and has to prove by reading records back: Order Lines' **Unit Price is a
# Currency (t8)** where Invoice Lines' is a plain Number (t6). `figures` is what says whether a type 31 formula
# reads a money operand.
CONVERT = ('Subtotal', 'Tax Amount', 'Total')
# Every operand, by name, with the ids read off the app on 21 Sep 2026. Confirmed by name at run time before any
# expression is written, because a formula built on a wrong id computes nothing and says nothing. Subtotal is both
# a converted control and the operand of the other two.
OPERANDS = {'Subtotal': '6ab0ca80805aef703286d82a', RATE: '6ab0d4bbe43d174ab3753780',
            'Quantity': '6ab0c864e43d174ab37535fb', 'Unit Price': '6ab0ca1be43d174ab3753657',
            'Discount': '6ab0ca1be43d174ab3753658'}
# Invoice Lines' two formulas with their own operands as placeholders: `$S$` Subtotal, `$R$` the Tax rate 汇总,
# `$Q$` Quantity, `$P$` Unit Price, `$D$` Discount.
TOTAL_TEMPLATE = '$S$*(1+$R$/100)'
# Odoo's `price_subtotal` is `quantity × price_unit × (1 − discount/100)`, which is what 07 stores as well.
SUBTOTAL_TEMPLATE = '$Q$*$P$*(1-$D$/100)'
# Odoo's `price_tax` is `price_total - price_subtotal`; arrived at from the rate it is the same figure.
TAX_TEMPLATE = '$S$*$R$/100'
SHAPE_KEYS = ('type', 'enumDefault', 'enumDefault2', 'fieldPermission', 'dot')
# What Invoice Lines' two Formulas must still carry for this step to copy them. Checked against the live controls
# rather than written onto them: a drift on 07 stops this build instead of being propagated to it.
WANT_SHAPE = {'type': FORMULA, 'enumDefault': 0, 'enumDefault2': 0, 'fieldPermission': '101', 'dot': 2}
WANT_SETTING = {'roundtype': '2', 'sorttype': 'zh', 'nullzero': '0'}
# A Formula has no currency and no default of its own, so these go. `showformat`, `prefix` and `suffix` are the
# rest of HAP's money formatting; `defaulttype` and `defaultfunc` are the function default that did not work.
DROPPED = ('currency', 'currencynames', 'showformat', 'prefix', 'suffix', 'defaulttype', 'defaultfunc')


def reference_formula(rate):
    """Invoice Lines' Subtotal and Total — the two type 31 Formulas in this app whose stored rows are proved
    right — read off the app, and the one shape both of them carry.

    Returns (shape, advancedSetting, {'Total': …, 'Subtotal': …}): each template is 07's own stored expression with
    its operands replaced by placeholders, so Order Lines' two are rebuilt from 07's formulas rather than from
    strings typed in this file and the two worksheets cannot drift apart. `rate` is Invoice Lines' Tax rate 汇总,
    as `reference_rate` read it."""
    live = hap.by_name(hap.controls(INVLINES))
    ref = {}
    for name in ('Subtotal', 'Total'):
        c = live.get(name)
        if c is None or c['type'] != FORMULA:
            sys.exit(f'Invoice Lines / {name} is {"missing" if c is None else "t" + str(c["type"])}, expected a '
                     f'Formula (t{FORMULA}) — it is the shape this step copies; read {INVLINES} first')
        ref[name] = c
    shapes = {n: {k: c.get(k) for k in SHAPE_KEYS} for n, c in ref.items()}
    settings = {n: dict(c.get('advancedSetting') or {}) for n, c in ref.items()}
    if shapes['Subtotal'] != shapes['Total'] or settings['Subtotal'] != settings['Total']:
        sys.exit(f'Invoice Lines\' two Formulas no longer carry one shape:\n'
                 f'  Subtotal {shapes["Subtotal"]} {settings["Subtotal"]}\n'
                 f'  Total    {shapes["Total"]} {settings["Total"]}\n'
                 '— there is no single shape to copy; read 07 before running this step')
    if shapes['Total'] != WANT_SHAPE or settings['Total'] != WANT_SETTING:
        sys.exit(f'Invoice Lines\' Formula shape has drifted from what this step was written against:\n'
                 f'  live {shapes["Total"]} {settings["Total"]}\n  want {WANT_SHAPE} {WANT_SETTING}')
    # Each reference expression back to a template, and each template checked against the constant above.
    # 07's own operand names differ from this worksheet's — its Discount is called *Discount (%)* — so they are
    # looked up by the names 07 uses and every one of them must be there.
    inv_ops = {}
    for label, name in (('$Q$', 'Quantity'), ('$P$', 'Unit Price'), ('$D$', 'Discount (%)')):
        c = live.get(name)
        if c is None:
            sys.exit(f'Invoice Lines / {name} is missing, so its Subtotal expression cannot be read as a '
                     f'template; read {INVLINES} first')
        inv_ops[label] = c['controlId']
    inv_ops['$S$'] = ref['Subtotal']['controlId']
    inv_ops['$R$'] = rate['controlId']
    templates, want = {}, {'Total': TOTAL_TEMPLATE, 'Subtotal': SUBTOTAL_TEMPLATE}
    for name in ('Total', 'Subtotal'):
        expr = ref[name].get('dataSource') or ''
        template = expr
        for label, cid in inv_ops.items():
            template = template.replace(f'${cid}$', label)
        if template != want[name]:
            sys.exit(f'Invoice Lines / {name} is {expr!r} — as a template {template!r}, not {want[name]!r}: it is '
                     f'no longer the expression this step copies, so there is nothing to copy')
        templates[name] = template
    shape, setting = shapes['Total'], settings['Total']
    print(f"  reference: Invoice Lines / Subtotal {ref['Subtotal']['controlId']} and Total "
          f"{ref['Total']['controlId']} — t{shape['type']} Formulas, perm {shape['fieldPermission']} (read-only), "
          f"dot {shape['dot']}, {setting}; Subtotal is {templates['Subtotal']}, Total is {templates['Total']}")
    return shape, setting, templates         # the live values, checked above, not the constants


def operands(f):
    """{name: controlId} for every operand the three expressions name, **confirmed by name on the live
    worksheet**.

    A formula built on an id that is not there stores, publishes and computes nothing — silently — so a missing or
    renumbered operand stops this step instead of being written into an expression."""
    out = {}
    for name, expected in OPERANDS.items():
        c = f.get(name)
        if c is None:
            sys.exit(f'{name} is not on {WORKSHEET}, so the expression has no operand to name'
                     + (' — run `fields` first' if name == RATE else ''))
        if c['controlId'] != expected:
            sys.exit(f'{name} is {c["controlId"]}, expected {expected} — the owner has replaced the control; '
                     're-read the worksheet before writing a formula on it')
        out[name] = c['controlId']
    # Subtotal is what this step converts, so it is the owner's Currency before the save and a Formula after it —
    # anything else means the control is not the one this step was written against.
    if f['Subtotal']['type'] not in (CURRENCY, FORMULA):
        sys.exit(f'Subtotal is t{f["Subtotal"]["type"]}, expected the owner\'s Currency (t{CURRENCY}) or the '
                 f'Formula (t{FORMULA}) this step converts it to')
    # Its own three operands must hold numbers. Unit Price is a Currency here where 07's is a plain Number, which
    # is the one difference between the two worksheets' Subtotals; `figures` is what proves a t8 operand computes.
    for name, kinds in (('Quantity', (NUMBER,)), ('Unit Price', (NUMBER, CURRENCY)), ('Discount', (NUMBER,))):
        if f[name]['type'] not in kinds:
            sys.exit(f'{name} is t{f[name]["type"]}, expected one of {kinds} — a formula over it would compute '
                     'nothing and say nothing')
    if f[RATE]['type'] != ROLLUP:
        sys.exit(f'{RATE} is t{f[RATE]["type"]}, expected a 汇总 (t{ROLLUP})')
    return out


def fill(template, ops):
    for label, name in (('$S$', 'Subtotal'), ('$R$', RATE), ('$Q$', 'Quantity'), ('$P$', 'Unit Price'),
                        ('$D$', 'Discount')):
        template = template.replace(label, f'${ops[name]}$')
    return template


def formula_spec(f, shape, setting, templates):
    """{control name: {key: value}} — everything the `formulas` step writes onto the three controls."""
    ops = operands(f)
    expression = {'Subtotal': fill(templates['Subtotal'], ops), 'Tax Amount': fill(TAX_TEMPLATE, ops),
                  'Total': fill(templates['Total'], ops)}
    return {n: {**shape, 'dataSource': expression[n],
                **{f'advancedSetting.{k}': v for k, v in setting.items()}} for n in CONVERT}


def surplus(c, setting):
    """The control's `advancedSetting` keys that the Formula shape does not carry, and what each holds."""
    return {k: v for k, v in (c.get('advancedSetting') or {}).items() if k not in setting}


def leftovers(c, setting):
    """The keys of `DROPPED` this control still carries a value for — what `formulas` has left to clear."""
    return {k: v for k, v in surplus(c, setting).items() if v and k in DROPPED}


def step_formulas():
    """Convert Subtotal, Tax Amount and Total from Currency (type 8) to **Formula** (type 31) — one version-pinned
    save that changes those three controls and nothing else.

    Each takes Invoice Lines' stored Formula shape (read-only `fieldPermission` "101", two decimals,
    `advancedSetting` `{roundtype, sorttype, nullzero}`) and its expression in `dataSource`: Subtotal
    `Quantity × Unit Price × (1 − Discount ÷ 100)` — the very expression Subtotal's function default carried — Tax
    Amount `Subtotal × Tax rate ÷ 100`, and Total `Subtotal × (1 + Tax rate ÷ 100)`, Invoice Lines' Total exactly,
    for parity, rather than the `Subtotal + Tax Amount` the function default used. All three aliases
    (`price_subtotal`, `price_tax`, `price_total`) are left as they are, because everything reads a value by them.

    The whole `advancedSetting` is **replaced** with the three keys a Formula carries, which is what drops the
    currency keys and the function default. Any other key still holding a value stops the step rather than being
    discarded quietly; the empties HAP leaves behind (`min`, `max`, `dynamicsrc`, `defsource`) go with the rest.
    Losing the RM prefix on Subtotal is the price of the conversion and the owner accepted it (21 Sep 2026).

    **No stored figure is lost.** All three were blank on every one of the thirty seeded lines and on the TEST
    record — a function default is the form's and the API applies none — which is the whole defect."""
    f = guard()
    rate, _filters = reference_rate()
    shape, setting, templates = reference_formula(rate)
    spec = formula_spec(f, shape, setting, templates)
    unknown = {n: {k: v for k, v in surplus(f[n], setting).items() if v and k not in DROPPED} for n in CONVERT}
    unknown = {n: u for n, u in unknown.items() if u}
    if unknown:
        sys.exit(f'{WORKSHEET}: {json.dumps(unknown, ensure_ascii=False)} — advancedSetting keys a Formula does '
                 'not carry and this step was not told to drop; stopping rather than discarding them')
    stale = {n: drift(f[n], spec[n]) for n in CONVERT}
    extra = {n: leftovers(f[n], setting) for n in CONVERT}
    todo = [n for n in CONVERT if stale[n] or extra[n]]
    for n in todo:
        for k, (got, want) in stale[n].items():
            print(f'  {n}.{k}:\n      was {got!r}\n      now {want!r}')
        for k, v in extra[n].items():
            print(f'  {n}.advancedSetting.{k}: {v!r} -> dropped')
    if not todo:
        print(f'  {list(CONVERT)} are already Formulas as specified; nothing saved')
        return False

    def apply(ctrls):
        ids = []
        for c in ctrls:
            if c['controlName'] in todo:
                c['advancedSetting'] = {}                  # the currency keys and the function default go
                for k, v in spec[c['controlName']].items():
                    set_value(c, k, v)
                ids.append(c['controlId'])
        return ids
    pinned_save('formulas', f'{todo} converted to Formulas', apply, 'orderlines_controls_pre_formulas')
    f = C.fields(ws())
    left = {n: drift(f[n], spec[n]) for n in CONVERT if drift(f[n], spec[n])}
    still = {n: leftovers(f[n], setting) for n in CONVERT if leftovers(f[n], setting)}
    if left or still:
        sys.exit(f'formulas read back with differences: {json.dumps(left, ensure_ascii=False)} '
                 f'and leftovers {json.dumps(still, ensure_ascii=False)}')
    check_subtotal(f)
    for n in CONVERT:
        c = f[n]
        print(f"  {n} {c['controlId']}: t{c['type']} alias={c.get('alias')} perm={c['fieldPermission']} "
              f"dot={c['dot']} dataSource={c['dataSource']} advancedSetting="
              f"{json.dumps(c.get('advancedSetting'), ensure_ascii=False, sort_keys=True)}")
    return True


def check_subtotal(f):
    """**No function default is left on any of the three computed controls.** That is the guarantee the conversion
    is for: a function default is evaluated in the form and the API applies none, so every figure written by a
    script stored empty while one remained. Named as its own check because the drift comparison above would pass
    just as happily on a control that had somehow kept `defaulttype` alongside the formula."""
    bad = {n: {k: v for k, v in (f[n].get('advancedSetting') or {}).items()
               if k in ('defaulttype', 'defaultfunc', 'defsource', 'dynamicsrc') and v}
           for n in CONVERT}
    bad = {n: v for n, v in bad.items() if v}
    if bad:
        sys.exit(f'{json.dumps(bad, ensure_ascii=False)} — a default is still set on a Formula, so a figure can '
                 'still be written by the form and not by the API; run `formulas`')
    print(f'  OK  {list(CONVERT)} carry no default of any kind — every figure is computed, in the form and on an '
          'API write alike')


# ── 4 · the line-level rule ─────────────────────────────────────────────────

RULE_FIGURES = 'A section or a note carries no figures'
# Odoo's SQL constraint `sale_order_line_non_accountable_null_fields`, the same one Invoice Lines implements as
# a rule. Written as *hide · is any of*, never *show · is Product*: a rule applies its action while its
# condition holds and the opposite when it fails, so the hide form leaves the figures **visible** on a new line
# whose Display Type has not been read yet, which is what a line is for (BUILDING.md).
FIGURES = ('Product', 'Quantity', 'Quantity Invoiced', 'Quantity Delivered', 'Unit', 'Unit Price', 'Discount',
           'Taxes', 'Tax Amount', 'Subtotal', 'Total', 'Lead Time', 'Optional Line')


def is_any_of(f, field, labels):
    """Condition: `field` is any of the labels — one filter carrying several option keys.

    A **business rule's** "is any of" on a single select is filterType **2** (`C.EQ`), not the 51 a view's, a
    button's or a 汇总's filter uses. It reads back in the options' own order, so `check` compares unordered."""
    c = f[field]
    keys = [o['key'] for o in c.get('options') or [] if o['value'] in labels and not o.get('isDeleted')]
    if sorted(keys) != sorted(DISPLAY_TYPE_KEYS[l] for l in labels):
        sys.exit(f'{field}: option keys for {labels} are {keys} — re-read the option table')
    return dict(C.cond(c, C.EQ), values=keys)


def rule_specs(f):
    """The one rule, as `upsert_rules` takes it: (name, type, filters, items, options)."""
    missing = [n for n in FIGURES if n not in f]
    if missing:
        sys.exit(f'{missing} are not on {WORKSHEET} yet — run `fields` first')
    return [(RULE_FIGURES, C.INTERACTION, C.any_of([is_any_of(f, 'Display Type', list(TEXT_LINES))]),
             [C.item(C.HIDE, *[f[n] for n in FIGURES])], {})]


def reference_rule():
    """Invoice Lines' own rule of the same name, printed so the two can be read side by side."""
    live = {r['name']: r for r in hap.listing('worksheet', 'rules', INVLINES)}
    r = live.get(RULE_FIGURES)
    if r is None:
        sys.exit(f'Invoice Lines has no rule named {RULE_FIGURES!r} to mirror')
    names = {c['controlId']: c['controlName'] for c in hap.controls(INVLINES)}
    groups = [[(f['dataType'], f['filterType'], len(f['values'])) for f in (g.get('groupFilters') or [g])]
              for g in r['filters']]
    print(f"  reference: Invoice Lines / {RULE_FIGURES!r} {r['ruleId']} — when {groups}, then "
          f"{[(i['type'], [names.get(c['controlId'], c['controlId']) for c in i['controls']]) for i in r['ruleItems']]}")
    return r


def step_rules():
    """The line-level rule, upserted by name so a re-run updates rather than duplicates.

    16-orders.md §6 recorded this rule as unbuildable, because the Order Lines of the time was a hidden
    `child_fields` child table no API call could read. The owner replaced it with a **mounted** worksheet on
    21 Sep 2026, so the blocker is gone (§7.2 item 6)."""
    f = guard()
    reference_rule()
    C.upsert_rules(ws(), rule_specs(f), 'orderlines_rules_pre_rules')
    live = {r['name']: r for r in hap.listing('worksheet', 'rules', ws())}
    if RULE_FIGURES not in live:
        sys.exit(f'rule {RULE_FIGURES!r} did not come back from the worksheet')
    C.remember('rules', KEY + RULE_FIGURES, live[RULE_FIGURES]['ruleId'])
    print(f'  {len(live)} rules on {WORKSHEET}; the one above is this builder\'s')
    return True


# ── 5 · the Odoo field names ────────────────────────────────────────────────

def alias_gaps(f):
    """{control name: alias} for every control that carries none. A control that already has one is left
    alone — an alias is what every view, filter and `record get` keys a value by, and renaming one silently
    re-points nothing."""
    unknown = sorted(n for n, c in f.items() if not c.get('alias') and n not in ALIAS)
    if unknown:
        sys.exit(f'{unknown} have no alias and this builder has no Odoo field name for them — '
                 'add it to ALIAS or leave the control to the owner')
    return {n: ALIAS[n] for n, c in f.items() if not c.get('alias') and ALIAS.get(n)}


def ws_item():
    """This worksheet's own entry in the app's menu groups — where the **worksheet** alias lives."""
    app = hap.run('app', 'info', '-a', APP).get('data', {})
    item = next((i for s in app.get('sections', []) for i in s['items'] if i['id'] == ws()), None)
    if item is None:
        sys.exit(f'{WORKSHEET} {ws()} is in no menu group of {APP} — nothing to alias')
    return item


def worksheet_alias():
    """Set the worksheet's own alias to `sale_order_line` if it carries none.

    `hap worksheet update --alias` answers 参数错误 unless the app id is passed (BUILDING.md), so it is. A
    worksheet that already carries an alias is **left alone**: a rename re-points nothing, and Orders' `quotation`
    is referenced by the subtable and the roll-ups."""
    item = ws_item()
    if item.get('alias') == WS_ALIAS:
        print(f'  worksheet alias is already {WS_ALIAS!r}; nothing saved')
        return False
    if item.get('alias'):
        print(f"  worksheet alias is {item['alias']!r}, not {WS_ALIAS!r} — the owner's; left as it is")
        return False
    print(f'  worksheet alias: {item.get("alias")!r} -> {WS_ALIAS!r}')
    hap.run('worksheet', 'update', ws(), '--alias', WS_ALIAS, '-a', APP)
    back = ws_item()
    if back.get('alias') != WS_ALIAS:
        sys.exit(f'the worksheet alias read back {back.get("alias")!r} — the update did not store')
    print(f'  worksheet alias stored: {back["alias"]!r}')
    return True


def step_alias():
    """Write the Odoo field names into `alias` on every control that has none, in one version-pinned save — and
    the Odoo **model** name into the worksheet's own alias.

    **Aliases are Odoo field names** (BUILDING.md), and all nineteen of this worksheet's controls were
    hand-built with none — so `record get` keys every value by its controlId, which no reader of this repo
    expects. Runs last, after `fields`, so the three appended controls get theirs in the same pass."""
    f = guard()
    renamed = worksheet_alias()
    gaps = alias_gaps(f)
    for n, a in sorted(gaps.items()):
        print(f'  {n}: alias -> {a}')

    def apply(ctrls):
        ids = []
        for c in ctrls:
            if c['controlName'] in gaps and not c.get('alias'):
                c['alias'] = gaps[c['controlName']]
                ids.append(c['controlId'])
        return ids
    changed = pinned_save('alias', f'{len(gaps)} aliases written', apply, 'orderlines_controls_pre_alias')
    f = C.fields(ws())
    wrong = {n: f[n].get('alias') for n, a in gaps.items() if f[n].get('alias') != a}
    if wrong:
        sys.exit(f'aliases read back {wrong} — the save did not store')
    extra = sorted(n for n in ALIAS if n in f and f[n].get('alias') != ALIAS[n])
    if extra:
        print(f'  note: {extra} carry an alias this builder did not write; left as the owner set them: '
              f'{ {n: f[n].get("alias") for n in extra} }')
    return bool(changed) or renamed


# ── 6 · the records the owner approved deleting ──────────────────────────────
#
# The owner approved clearing **these two worksheets' records and nothing else** (relayed 21 Sep 2026): the two
# hand-made lines here and the three orders above them, all test data. As on Orders the approval is pinned to
# the rows it covered, read off the app on 21 Sep 2026 — so this step can never grow into "delete whatever is
# there": once the two are gone it is a no-op, which is what makes it safe to re-run after the seed, and a third
# line the owner made in the meantime stops it rather than being swept up. The delete is a **soft** delete
# (`--permanent` is not passed), so each row goes to the worksheet's record recycle bin.
WIPE = {                                           # rowid -> the (order Number, Description) it must still carry
    '6d0f8acc-3a71-4719-9b05-76b2528d4e52': ('S00002', 'TEST rollup line'),
    'd06d417a-f50d-4792-b49e-b5664ebf8a89': ('S00005', 'TEST rollup line'),
}


def step_wipe():
    """Delete the two test lines the owner approved clearing. Run **before** `orders.py wipe`: children first,
    because a line whose parent is gone is an orphan."""
    guard()
    return bool(O.wipe_records(ws(), WORKSHEET, WIPE,
                               lambda d: ((O.relation_names(d.get('order_id')) or [''])[0],
                                          d.get('name') or '')))


# ── 7 · the tenant's thirty lines ───────────────────────────────────────────
#
# `nocoly/data/sale-orders-casimir.json` again — `orders.py` owns the loader, the relation resolver and the
# read-back-by-control-type, so the two halves of one seed cannot drift apart. Its `_note` explains the
# **Sequence renumbering**: Odoo's own `sequence` is 10 on nearly every line, so the file renumbers 10, 20, 30
# in Odoo's own returned order, which is what keeps the lines in their on-screen order here.
#
# **The match key is (the order's rowid, Sequence)** — not the order's Number, which the app's auto-number
# control minted and which says nothing about which tenant order a line belongs to. `invlines.py seed_key` keys
# its lines the same way and for the same reason.
#
# **Subtotal, Tax Amount and Total are never written.** All three are type 31 Formulas (§3): Subtotal from
# Quantity, Unit Price and Discount on its own row, and the other two from Subtotal and the Tax rate 汇总. A
# Formula's value is the server's, so a seeded line carries all three the moment it is written — which is exactly
# what a *function default* did not do. The seed's figures are read back and compared in `figures`, and a mismatch
# is reported, never repaired.
NOT_WRITTEN = ('Subtotal', 'Tax Amount', 'Total', 'Tax rate', 'Product Unit')

# The seed names five variants this app does not hold, and creating them would mean writing to Product
# Variants, which this build may not touch. Each stands for the product's single active variant, exactly as
# `invlines.py`'s own SEED rows do and for the same reason: Phase 1 keeps one placeholder variant per product,
# so the tenant's archived originals ([FURN-0001], [FURN-0002], [IT-0002]) and its colour variants
# (Ergonomic Office Chair Blue / Red) have no record of their own. The line keeps the **tenant's own
# Description**, which is where the reference survives.
VARIANT_STANDS_FOR = {
    '[IT-0002] 27" 4K Monitor': '27" 4K Monitor',
    '[FURN-0001] Ergonomic Office Chair': 'Ergonomic Office Chair',
    '[FURN-0002] Height-Adjustable Desk 140cm': 'Height-Adjustable Desk 140cm',
    'Ergonomic Office Chair (Red)': 'Ergonomic Office Chair',
    'Ergonomic Office Chair (Blue)': 'Ergonomic Office Chair',
}
# A tax is named by **Tax Name and Tax Type**, never by name alone: this app holds four taxes called *10% G* and
# *8% S* — a Sales one and a Purchases one of each — so the seed's bare names are resolved against the **Sales**
# ones. Every one of the twelve orders is a customer document, and `invlines.py` resolves its own the same way.
TAX_TYPE = 'Sales'


def tax_index():
    """{(Tax Name, Tax Type): [rowid, ...]} over the Taxes worksheet."""
    taxes = C.fields(TAXES())
    name, kind = taxes['Tax Name'], taxes['Tax Type']
    labels = {o['key']: o['value'] for o in kind.get('options') or []}
    out = {}
    for r in C.records(TAXES(), APP):
        keys = O.option_keys(r.get(kind['controlId']))
        out.setdefault((r.get(name['controlId']), labels.get(keys[0]) if keys else None), []).append(r['rowid'])
    return out


def VARIANTS():
    return C.fields(ws())['Product']['dataSource']


def UNITS():
    return C.fields(ws())['Unit']['dataSource']


def TAXES():
    return C.fields(ws())['Taxes']['dataSource']


def line_key(order_rowid, sequence):
    return (order_rowid or '', None if sequence is None else round(float(sequence), 2))


def line_want(f, line, order_rowid, index, gaps):
    """{control name: value} — every cell the seed writes on one line, and nothing else.

    A row with **no product and no unit** — S00021's Down Payments section and its two down-payment rows —
    simply sends neither cell, exactly as `invlines.py` does for its own section row. A product the app cannot
    resolve is left out too, and reported."""
    want = {
        'Orders': [order_rowid],
        'Sequence': float(line['sequence']),
        'Display Type': [O.option_key(f['Display Type'], line['display_type'])],
        'Description': line['description'] or '',
        'Quantity': round(float(line['quantity']), 2),
        'Quantity Invoiced': round(float(line['qty_invoiced']), 2),
        'Quantity Delivered': round(float(line['qty_delivered']), 2),
        'Unit Price': round(float(line['unit_price']), 2),
        'Discount': round(float(line['discount']), 2),
        'Lead Time': round(float(line['lead_time']), 2),
        'Optional Line': '1' if line['optional_line'] else '0',
    }
    if line['product']:
        rowid = O.resolve(index['variants'], VARIANT_STANDS_FOR.get(line['product'], line['product']),
                          'product variant', gaps)
        if rowid:
            want['Product'] = [rowid]
    if line['unit']:
        rowid = O.resolve(index['units'], line['unit'], 'unit', gaps)
        if rowid:
            want['Unit'] = [rowid]
    if line['taxes']:
        rows = [O.resolve(index['taxes'], (name, TAX_TYPE), 'tax', gaps) for name in line['taxes']]
        if all(rows):
            want['Taxes'] = rows
    return want


def step_seed():
    """The tenant's thirty lines, matched by (the order's rowid, Sequence) and re-running to nothing.

    Runs **after** `orders.py seed`: a line's Orders relation is the back-relation the subtable is built on, so
    the row shows inside its order straight away, and an order that is not there yet has no rowid to point at."""
    f = guard()
    data, grouped = O.seed_data()
    orders = O.seeded_orders()
    absent = [o['name'] for o in data['orders'] if o['name'] not in orders]
    if absent:
        sys.exit(f'{absent} are not on Orders — run `orders.py seed` first')
    index = {'variants': O.titles(VARIANTS(), 'Display Name'), 'units': O.titles(UNITS(), 'Unit Name'),
             'taxes': tax_index()}
    live = {}
    for r in C.records(ws(), APP):
        d = O.read_record(ws(), r['rowid'])
        live[line_key((O.read_cell(f['Orders'], d) or [None])[0], O.read_cell(f['Sequence'], d))] = (r['rowid'], d)
    hap.backup('orderlines_records_pre_seed', {rowid: d for rowid, d in live.values()})
    gaps, problems, made = {}, [], 0
    for o in data['orders']:
        order_rowid, number = orders[o['name']]
        for line in grouped.get(o['name'], []):
            want = line_want(f, line, order_rowid, index, gaps)
            key = line_key(order_rowid, line['sequence'])
            rowid, record = live.get(key, (None, {}))
            diff = O.differences(f, record, want) if rowid else None
            if rowid and not diff:
                continue
            values = ([{'id': f[n]['controlId'], 'value': want[n]} for n in diff] if rowid else
                      [{'id': f[n]['controlId'], 'value': v} for n, v in want.items()
                       if v not in ('', [], None)])
            was = rowid
            rowid = O.write_record(ws(), rowid, values)
            record = O.read_record(ws(), rowid)
            made += 1
            print(f"  {o['name']} ({number}) line {line['sequence']}: "
                  f"{'updated' if was else 'created'} {rowid}")
            left = O.differences(f, record, want)
            if left:
                problems.append(f"{o['name']} line {line['sequence']}: "
                                f'{json.dumps(left, ensure_ascii=False, default=str)}')
            C.remember('records', f"{KEY}{o['name']} line {line['sequence']}", rowid)
    print(f'  {made} line(s) written this run; {len(data["lines"])} in the seed')
    O.report_gaps(gaps)
    print(f'  never written by the seed: {list(NOT_WRITTEN)} — computed by the app and compared in `figures`')
    if problems:
        sys.exit('  the seed read back with differences:\n    ' + '\n    '.join(problems))
    return bool(made)


# ── 8 · the figures: what the app computed against what the tenant holds ────

# Not `FIGURES` — that name is the *rule*'s list of the thirteen controls a section hides, and shadowing it
# emptied the rule's targets on the first run of this step.
COMPUTED = (('Subtotal', 'subtotal'), ('Tax Amount', 'tax_amount'), ('Total', 'total'))


def step_figures():
    """Each seeded line's computed Subtotal, Tax Amount and Total beside the tenant's own — reported, never
    repaired: a mismatch is a finding about the three Formulas and the Tax rate 汇总 they stand on, not about the
    data. It is also what answers the one thing §3 could not copy from Invoice Lines — whether a type 31 formula
    reads a **Currency** operand, since Unit Price is a t8 here and a plain Number there."""
    f = guard()
    data, grouped = O.seed_data()
    orders = O.seeded_orders()
    live = {}
    for r in C.records(ws(), APP):
        d = O.read_record(ws(), r['rowid'])
        live[line_key((O.read_cell(f['Orders'], d) or [None])[0], O.read_cell(f['Sequence'], d))] = d
    diffs, seen = 0, 0
    for o in data['orders']:
        if o['name'] not in orders:
            print(f"  {o['name']}: not seeded — run `orders.py seed`")
            continue
        order_rowid, number = orders[o['name']]
        for line in grouped.get(o['name'], []):
            d = live.get(line_key(order_rowid, line['sequence']))
            if d is None:
                print(f"  MISSING {o['name']} line {line['sequence']} — run `seed`")
                diffs += 1
                continue
            seen += 1
            got = [(name, O.read_cell(f[name], d), round(line[key], 2)) for name, key in COMPUTED]
            bad = [x for x in got if x[1] != x[2]]
            diffs += len(bad)
            print(f"  {'DIFF' if bad else 'OK  '} {o['name']}/{number} line {line['sequence']:>3}  "
                  + '  '.join(f'{n}={v if v is not None else "(empty)"}/{w}' for n, v, w in got)
                  + f"  rate={O.read_cell(f['Tax rate'], d)}")
    print(f'  {seen} line(s) compared, {diffs} figure(s) differ from the tenant '
          f'(app value / tenant value above)')
    return diffs


# ── check ───────────────────────────────────────────────────────────────────

def condition_state(filters, names):
    """A rule's filter as (control name, spliceType, filterType, value, sorted values) groups."""
    return [[(names.get(c['controlId'], c['controlId']), c['spliceType'], c['filterType'], c['value'],
              sorted(c['values'])) for c in (g.get('groupFilters') or [g])] for g in filters]


def report(f=None):
    """Everything this builder owns, as it reads back."""
    f = f or C.fields(ws())
    for n in list(CONTROLS) + list(NEW):
        c = f.get(n)
        if not c:
            print(f'  {n:<20} MISSING')
            continue
        print(f"  {n:<20} {c['controlId']} t{c['type']:<3} alias={c.get('alias') or '-':<18} "
              f"req={str(bool(c.get('required'))):<5} perm={c.get('fieldPermission') or '-':<4} "
              f"dot={c.get('dot')} r{c.get('row')}c{c.get('col')}"
              f"{'  =' + c['dataSource'] if c['type'] == FORMULA else ''}")


def step_check():
    """Read every control, the rule and the aliases back, and report every drift."""
    f = guard()
    ref, filters = reference_rate()
    problems = []
    if RATE not in f:
        problems.append(f'{RATE} is missing — run `fields`')
    for n in NEW:
        if n not in f:
            problems.append(f'{n} is missing — run `fields`')
    if RATE in f and all(n in f for n in NEW):
        spec = new_spec(f, ref, filters)
        for n in NEW:
            diff = drift(f[n], spec[n])
            if diff:
                problems.append(f'{n}: {json.dumps(diff, ensure_ascii=False)}')
            else:
                print(f'  OK  {n} as specified ({f[n]["controlId"]})')
        cspec = computed_spec(f)
        for n, want in cspec.items():
            diff = drift(f[n], want)
            if diff:
                problems.append(f'{n}: {json.dumps(diff, ensure_ascii=False)}')
            else:
                print(f'  OK  {n} {sorted(want)}')
        # the three converted Formulas, and the proof no function default is left on any of them
        shape, setting, templates = reference_formula(ref)
        fspec = formula_spec(f, shape, setting, templates)
        for n in CONVERT:
            diff = drift(f[n], fspec[n])
            extra = leftovers(f[n], setting)
            if diff or extra:
                problems.append(f'{n}: {json.dumps(diff, ensure_ascii=False)}'
                                f'{" leftovers " + json.dumps(extra, ensure_ascii=False) if extra else ""}'
                                ' — run `formulas`')
            else:
                print(f'  OK  {n} t{FORMULA} = {f[n]["dataSource"]} (perm {f[n]["fieldPermission"]}, '
                      f'dot {f[n]["dot"]})')
        check_subtotal(f)
        for n in REQUIRED:
            if not f[n].get('required'):
                problems.append(f'{n} is not required — run `computed`')
        names = {c['controlId']: c['controlName'] for c in hap.controls(ws())}
        live = {r['name']: r for r in hap.listing('worksheet', 'rules', ws())}
        for name, kind, rfilters, items, _opts in rule_specs(f):
            r = live.get(name)
            if r is None:
                problems.append(f'rule {name!r} missing — run `rules`')
                continue
            want = (kind, False, condition_state(rfilters, names),
                    [(i['type'], sorted(names.get(c['controlId'], c['controlId']) for c in i['controls']))
                     for i in items])
            got = (r['type'], r['disabled'], condition_state(r['filters'], names),
                   [(i['type'], sorted(names.get(c['controlId'], c['controlId']) for c in i['controls']))
                    for i in r['ruleItems']])
            if got != want:
                problems.append(f'rule {name!r}:\n    want {want}\n    got  {got}')
            else:
                print(f"  OK  {name!r}\n        when {got[2]}\n        then {got[3]}  (ruleId {r['ruleId']})")
        for name, r in live.items():
            if name != RULE_FIGURES:
                print(f"  new       {r['ruleId']} {name!r} — the owner's, not this builder's")
    gaps = alias_gaps(f)
    if gaps:
        problems.append(f'{sorted(gaps)} still carry no alias — run `alias`')
    else:
        print(f'  OK  every control carries an alias')
    item = ws_item()
    if item.get('alias') != WS_ALIAS:
        problems.append(f'the worksheet alias is {item.get("alias")!r}, not {WS_ALIAS!r} — run `alias`')
    else:
        print(f'  OK  the worksheet alias is {WS_ALIAS!r} (Odoo `sale.order.line`)')
    wrong = {n: f[n].get('alias') for n in ALIAS if n in f and f[n].get('alias') != ALIAS[n]}
    if wrong:
        print(f'  note: aliases that differ from this builder\'s table: {wrong}')
    print(f'  not built: no `invoice_lines` link, so Quantity Invoiced has no source and stays manual; '
          f'Quantity Delivered waits on Inventory (16-orders.md §4)')
    print(f'  not built: the three appended controls are at row {f[RATE].get("row") if RATE in f else "?"} — '
          f'`add-fields` parks a new control and only a full save places one, which this builder must not make')
    data, grouped = O.seed_data()
    orders = O.seeded_orders()
    missing_orders = [o['name'] for o in data['orders'] if o['name'] not in orders]
    if missing_orders:
        problems.append(f'{missing_orders} are not on Orders — run `orders.py seed`')
    else:
        index = {'variants': O.titles(VARIANTS(), 'Display Name'), 'units': O.titles(UNITS(), 'Unit Name'),
                 'taxes': tax_index()}
        live = {}
        for r in C.records(ws(), APP):
            d = O.read_record(ws(), r['rowid'])
            live[line_key((O.read_cell(f['Orders'], d) or [None])[0], O.read_cell(f['Sequence'], d))] = d
        gaps, absent, drifted = {}, [], []
        for o in data['orders']:
            order_rowid, number = orders[o['name']]
            for line in grouped.get(o['name'], []):
                key = line_key(order_rowid, line['sequence'])
                want = line_want(f, line, order_rowid, index, gaps)
                if key not in live:
                    absent.append(f"{o['name']} line {line['sequence']}")
                    continue
                left = O.differences(f, live[key], want)
                if left:
                    drifted.append(f"{o['name']} line {line['sequence']}: "
                                   f'{json.dumps(left, ensure_ascii=False, default=str)}')
        extra = len(live) - (len(data['lines']) - len(absent))
        if absent:
            problems.append(f'{len(absent)} seeded line(s) are missing ({absent}) — run `seed`')
        if drifted:
            problems.append(f'{len(drifted)} seeded line(s) differ — run `seed`:\n    ' + '\n    '.join(drifted))
        if not absent and not drifted:
            print(f"  OK  all {len(data['lines'])} seeded lines are live and as the seed writes them"
                  + (f' ({extra} other line(s) on the worksheet)' if extra else ''))
        O.report_gaps(gaps)
    report(f)
    if problems:
        print('  check: ' + '\n         '.join(problems))
        sys.exit(1)
    print(f'  check: OK — {len(NEW)} appended controls, {list(CONVERT)} as Formulas with no default left, '
          f'two required fields, one rule, {len(ALIAS)} aliases')


def step_show():
    """The live controls and rules."""
    guard()
    C.show(ws())
    for r in hap.listing('worksheet', 'rules', ws()):
        print(f"  {'disabled' if r['disabled'] else 'enabled ':<9} {r['ruleId']} {r['name']}")


STEPS = {'fields': step_fields, 'computed': step_computed, 'formulas': step_formulas, 'rules': step_rules,
         'alias': step_alias, 'wipe': step_wipe, 'seed': step_seed, 'figures': step_figures,
         'check': step_check, 'show': step_show}

if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] not in STEPS:
        sys.exit(f'usage: {sys.argv[0]} {{{" | ".join(STEPS)}}}')
    print(f'{WORKSHEET}: {sys.argv[1]}')
    STEPS[sys.argv[1]]()
