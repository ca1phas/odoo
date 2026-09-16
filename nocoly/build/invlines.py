#!/usr/bin/env python3
"""Build the Invoice Lines worksheet (Odoo account.move.line, as on casimir.odoo.com saas~19.4) in ERP Master.

The last worksheet of Phase 1, and the one that makes 06's four amounts real. It is a worksheet in its own right
— Odoo's Journal Items are a standalone list too — **mounted as the subtable of the Invoices tab *Invoice
Lines***, under the remark block 06 left there. Requirements: nocoly/worksheets/07-invoice-lines.md. Generic
helpers: common.py. Run from the repo root with the CLI's interpreter:

    ~/.hap-venv/bin/python nocoly/build/invlines.py create     # 1. the worksheet, in menu group Invoicing after
                                                               #    Invoices, alias account_move_line
    ~/.hap-venv/bin/python nocoly/build/invlines.py fields     # 2. the eight plain controls, in one save that
                                                               #    reuses the stock title control for Label
    ~/.hap-venv/bin/python nocoly/build/invlines.py mount      # 3. mount the worksheet as the subtable of the
                                                               #    Invoices tab — which is also what creates the
                                                               #    Invoice relation here — and place it under the
                                                               #    remark block
    ~/.hap-venv/bin/python nocoly/build/invlines.py computed   # 4. Subtotal (formula) and the three lookups of
                                                               #    the invoice: Number, Accounting Date, Status
    ~/.hap-venv/bin/python nocoly/build/invlines.py layout     # 5. places, aliases, help, required, read-only,
                                                               #    defaults, decimals and the title field
    ~/.hap-venv/bin/python nocoly/build/invlines.py rules      # 6. a section or a note carries no figures
    ~/.hap-venv/bin/python nocoly/build/invlines.py views      # 7. Lines: columns, three-level sort, quick filter
    ~/.hap-venv/bin/python nocoly/build/invlines.py rollup     # 8. the two workflows that write 06's amounts
    ~/.hap-venv/bin/python nocoly/build/invlines.py seed       # 9. the eight lines of the three seeded documents
    ~/.hap-venv/bin/python nocoly/build/invlines.py amounts    # 10. recompute Untaxed Amount, Total and Amount
                                                               #    Due on every invoice that has lines
    ~/.hap-venv/bin/python nocoly/build/invlines.py all        # every step above, then check

    ~/.hap-venv/bin/python nocoly/build/invlines.py verify     # the live lines against the seed, and every
                                                               #    invoice's amounts against its own lines
    ~/.hap-venv/bin/python nocoly/build/invlines.py check      # controls, options, defaults, the rule, the view,
                                                               #    the mount and the two workflows against this
                                                               #    spec
    ~/.hap-venv/bin/python nocoly/build/invlines.py selfcheck  # the roll-up end to end through the CLI: add a
                                                               #    TEST line, change its quantity, and read the
                                                               #    invoice's amounts back each time
    ~/.hap-venv/bin/python nocoly/build/invlines.py order      # the view's records, in the view's own order
    ~/.hap-venv/bin/python nocoly/build/invlines.py lines "INV/2026/00001"   # one document's stored lines
    ~/.hap-venv/bin/python nocoly/build/invlines.py untouched  # the five worksheets that must not change, and
                                                               #    Invoices' 32 controls compared id by id
    ~/.hap-venv/bin/python nocoly/build/invlines.py show       # the live control list

Every step reads the live state first and is safe to re-run; a second run writes nothing.

**Nothing here deletes anything.** The only worksheets written to are Invoice Lines and Invoices, and on Invoices
only the mounted subtable control (new), the one row every control below it moves down to make room for it, and
the three amount values the roll-up owns.

**Deleting a line by hand needs two flags.** `hap worksheet record delete` prompts unless `-y` is passed — so it
hangs in a script — and it **suppresses workflows unless `--trigger-workflow` is passed**, which leaves the
invoice's amounts stale with no error at all (BUILDING.md). In full:

    hap worksheet record delete <invoice-lines-ws> --row-ids <rowid> -a <app> --trigger-workflow -y

`amounts` puts any invoice left stale by a delete without the flag back in step with its lines. Contacts, Units & Packagings, Products, Product Variants and Journals
are compared control by control before and after every save, and the Sales app is never opened.

Profile. hap-cli 0.8.31 picks the account as --profile > $HAP_PROFILE > the active profile, so this script passes
none and runs on any machine whose active profile reaches ERP Master.
"""
import hashlib
import json
import os
import sys
import time

import common as C
import hap

APP = hap.ids()['app']
ORG = hap.ids()['org']
SECTION = 'Invoicing'
WORKSHEET = 'Invoice Lines'                        # the ids.json key and the sidebar name
ALIAS_WORKSHEET = 'account_move_line'              # BUILDING.md: a worksheet's alias is its Odoo model
KEY = 'Invoice Lines: '                            # ids.json key prefix for everything this worksheet owns
INVOICES = hap.ids()['worksheets']['Invoices']
VARIANTS = hap.ids()['worksheets']['Product Variants']
UNITS = hap.ids()['worksheets']['Units & Packagings']
OTHERS = ('Contacts', 'Units & Packagings', 'Products', 'Product Variants', 'Journals')   # must stay untouched

SUBLIST = 34                                       # HAP's 子表: a worksheet mounted under a parent record
RELATION = 29                                      # 关联记录
DROPDOWN = 11                                      # 单选（下拉框）
NUMBER = 6
FORMULA_NUMBER = 31                                # a number formula field; Subtotal is one

# ── the Invoices controls this worksheet writes into or hangs off ───────────
# Read from ids.json rather than by name: 06 is out for review and none of these may be replaced.
INV = {name: hap.ids()['controls']['Invoices: ' + name] for name in
       ('Invoice Lines', 'Invoice Lines note', 'Terms and Conditions', 'Untaxed Amount', 'Tax', 'Total',
        'Amount Due', 'Number', 'Accounting Date', 'Status')}
LINES_FIELD = 'Lines'                              # the mounted subtable's own control name on Invoices
# Odoo's Invoice Lines tab shows the table with no heading of its own, so the subtable's name is kept as an
# internal label (advancedSetting.hidetitle "1"), the way the three remark blocks are.
LINES_ROW = 8                                      # right under the remark block at row 7; everything below
                                                   # moves down one row to make room


def option(key, value, index, color, checked=False):
    return {'key': key, 'value': value, 'isDeleted': False, 'index': index, 'checked': checked, 'color': color}


# Odoo's display_type, the four values a person can pick — its *Add a line*, *Add a section* and *Add a note*
# buttons. The keys are minted once here and never re-minted: records point at them.
DISPLAY_TYPE_OPTIONS = [
    option('7f1d6a5c-3c4e-4b8a-9d21-6b0f2a5e7c31', 'Product', 1, '#C9E6FC', True),
    option('2a90c7e4-1f63-4de5-8a07-4c3b91d0e6f2', 'Section', 2, '#FFE7B1'),
    option('b4e3f0a1-59d8-42c6-9f15-7e2d8c4a3b60', 'Subsection', 3, '#C3F2F2'),
    option('d8c25b37-6e14-4a09-bf83-1d59e7c204af', 'Note', 4, '#D2D2D2'),
]
OPTIONS = {'Display Type': DISPLAY_TYPE_OPTIONS}
LABEL = {name: {o['key']: o['value'] for o in opts} for name, opts in OPTIONS.items()}
OPTION_KEY = {name: {o['value']: o['key'] for o in opts} for name, opts in OPTIONS.items()}
PRODUCT_LINE = OPTION_KEY['Display Type']['Product']
TEXT_LINES = ['Section', 'Subsection', 'Note']     # Odoo's non-accountable display types

# ── 1 · the form ────────────────────────────────────────────────────────────

# Odoo's line columns on HAP's 12-column grid. The parent link first (Odoo's Journal Entry), then the two
# columns that decide what the line is, then Odoo's own column order, then the three read-only values the
# standalone list needs.
PLACE = {  # name -> (row, col, size)
    'Invoice': (0, 0, 12),
    'Sequence': (1, 0, 6), 'Display Type': (1, 1, 6),
    'Product': (2, 0, 12),
    'Label': (3, 0, 12),
    'Quantity': (4, 0, 6), 'Unit': (4, 1, 6),
    'Unit Price': (5, 0, 6), 'Discount (%)': (5, 1, 6),
    'Subtotal': (6, 0, 12),
    'Number': (7, 0, 6), 'Accounting Date': (7, 1, 6),
    'Status': (8, 0, 6),
}
TITLE = 'Label'                                    # Odoo's _rec_name on account.move.line is `name`
REQUIRED = {'Invoice', 'Display Type'}
READONLY = {'Subtotal', 'Number', 'Accounting Date', 'Status'}
HIDDEN = set()
DESC = {  # Odoo field help, verbatim where Odoo has one (addons/account/models/account_move_line.py)
    'Invoice': 'The document this line belongs to — Odoo labels it Journal Entry. It is also the link the '
               'subtable on the invoice is built on, so a line opened from inside an invoice carries it already.',
    'Sequence': 'Orders the lines within one invoice. Odoo reorders them by dragging a handle, which a HAP '
                'subtable has no equivalent for, so the number is the only way to move a line.',
    'Display Type': "Odoo's *Add a line*, *Add a section* and *Add a note*. A section, a subsection and a note "
                    'carry no figures: the rule hides Product, Quantity, Unit, Unit Price, Discount (%) and '
                    'Subtotal. The tax, payment-term, rounding and early-payment-discount lines Odoo writes '
                    'itself are not built.',
    'Product': 'The **variant**, never the template: every Odoo order line, stock move and invoice line points '
               'at product.product. Odoo also filters it by the document — sale_ok on a customer document, '
               'purchase_ok on a vendor one.',
    'Label': "Odoo fills it from the product's display name and its sales description when a product is chosen, "
             'on two lines. Here it is typed or seeded; on a section or a note it *is* the text.',
    'Quantity': 'The optional quantity expressed by this line, eg: number of product sold.',
    'Unit': "Odoo offers only the product's own unit and its packagings (allowed_uom_ids); every unit is offered "
            'here, because that domain needs a lookup of a relation, which HAP stores as a title.',
    'Unit Price': '',
    'Discount (%)': "Odoo's optional *Disc.%* column, hidden by default on the invoice form and used on five of "
                    "the tenant's lines.",
    'Subtotal': 'Quantity × Unit Price × (1 − Discount ÷ 100). Odoo shows this in its *Amount* column while the '
                'document is Tax Excluded, and the tax-inclusive total when it is Tax Included — which needs the '
                'Taxes bundle, so only the subtotal is built. The sum of these is the invoice Untaxed Amount.',
    'Number': "The invoice's Number, so the standalone list can show which document a line belongs to.",
    'Accounting Date': "The invoice's Accounting Date. Odoo stores it on the line and sorts the Journal Items "
                       'list on it.',
    'Status': "The invoice's Status. Odoo's Journal Items views filter Posted / Unposted on it.",
}
ADVANCED = {  # advancedSetting keys this script owns
    'Sequence': {'defsource': C.static_default(10)},
    'Display Type': {'defsource': C.static_default(PRODUCT_LINE)},
    'Quantity': {'defsource': C.static_default(1)},
    'Unit Price': {'defsource': C.static_default(0)},
    'Discount (%)': {'defsource': C.static_default(0), 'suffix': '%'},
}
DOT = {'Sequence': 0, 'Quantity': 2, 'Unit Price': 2, 'Discount (%)': 2, 'Subtotal': 2}
ALIAS = {'Invoice': 'move_id', 'Sequence': 'sequence', 'Display Type': 'display_type', 'Product': 'product_id',
         'Label': 'name', 'Quantity': 'quantity', 'Unit': 'product_uom_id', 'Unit Price': 'price_unit',
         'Discount (%)': 'discount', 'Subtotal': 'price_subtotal', 'Number': 'move_name',
         'Accounting Date': 'date', 'Status': 'parent_state'}
RELATIONS = {'Product': VARIANTS, 'Unit': UNITS}   # one-way; neither target gets a reverse field
LOOKUPS = [('Number', 'Number'), ('Accounting Date', 'Accounting Date'), ('Status', 'Status')]
FIGURES = ['Product', 'Quantity', 'Unit', 'Unit Price', 'Discount (%)', 'Subtotal']   # what a section hides


def ws():
    return hap.ids()['worksheets'][WORKSHEET]


def ctl(kind, name, advanced_setting=None, **kw):
    row, col, size = PLACE[name]
    advanced = {**(ADVANCED.get(name) or {}), **(advanced_setting or {})}
    return C.control(kind, name, (row, col, size), alias=ALIAS.get(name, ''), hint='', desc=DESC.get(name, ''),
                     readonly=name in READONLY, required=name in REQUIRED, options=OPTIONS.get(name),
                     advanced_setting=advanced or None, **kw)


# ── the worksheets that must not change ─────────────────────────────────────

SIGNATURE = ('controlName', 'type', 'alias', 'row', 'col', 'size', 'sectionId', 'required', 'attribute', 'unique',
             'fieldPermission', 'dataSource', 'sourceControlId', 'showControls', 'advancedSetting', 'desc', 'hint')


def signature_of(worksheet):
    return sorted(json.dumps([c['controlId']] + [c.get(k) for k in SIGNATURE], sort_keys=True, ensure_ascii=False)
                  for c in hap.controls(worksheet))


def signatures():
    """Every worksheet this build must leave alone, by control id."""
    return {name: signature_of(hap.ids()['worksheets'][name]) for name in OTHERS}


def check_untouched(before):
    after = signatures()
    for name in before:
        if after[name] != before[name]:
            sys.exit(f'{name} controls changed: {sorted(set(after[name]) ^ set(before[name]))}')
    print('  untouched: ' + ', '.join(f'{n} ({len(after[n])})' for n in after))


def invoices_controls():
    """Invoices' controls by id — the mounted subtable, which this build owns, left out, and with `row`, which
    the mount is allowed to move, left out of every other control's signature."""
    keep = tuple(k for k in SIGNATURE if k != 'row')
    return {c['controlId']: json.dumps([c.get(k) for k in keep], sort_keys=True, ensure_ascii=False)
            for c in hap.controls(INVOICES) if c['type'] != SUBLIST}


def check_invoices(before, allow_new=()):
    """Every Invoices control still there and unchanged but for its row; at most the named new ones added."""
    after = invoices_controls()
    lost = sorted(set(before) - set(after))
    changed = sorted(cid for cid in set(before) & set(after) if before[cid] != after[cid])
    names = {c['controlId']: c['controlName'] for c in hap.controls(INVOICES)}
    added = sorted(names[cid] for cid in set(after) - set(before))
    sub = sub_list()
    if sub and sub['controlName'] not in allow_new:
        added.append(sub['controlName'])
    if lost or changed:
        sys.exit(f'Invoices changed: lost={lost} changed={[(c, names.get(c)) for c in changed]}')
    if [a for a in added if a not in allow_new]:
        sys.exit(f'Invoices gained {added}, expected at most {list(allow_new)}')
    print(f'  Invoices: {len(after) + bool(sub)} controls, {len(before)} unchanged but for the row, '
          f'the mounted {LINES_FIELD} subtable this build owns aside')


def step_untouched():
    """Control count and digest of every worksheet this build must not change, plus Invoices."""
    for name, sig in signatures().items():
        print(f'  {name:<20} {len(sig):>2} controls  sha256:{hashlib.sha256("".join(sig).encode()).hexdigest()[:16]}')
    sig = signature_of(INVOICES)
    print(f'  {"Invoices":<20} {len(sig):>2} controls  sha256:{hashlib.sha256("".join(sig).encode()).hexdigest()[:16]}')


def save_worksheet_controls(worksheet, ctrls):
    """SaveWorksheetControls through the CLI's own session.

    `hap worksheet update-fields --controls` puts the whole control list on the command line, and once the
    mounted subtable carries its `relationControls` snapshot of all thirteen Invoice Lines controls, Invoices'
    list is past the kernel's argument limit — `OSError: [Errno 7] Argument list too long`. Same call, same
    optimistic-lock retry; only the transport differs (Found while building)."""
    from hap_cli.core.session import Session
    from hap_cli.core import worksheet as ws_mod
    return ws_mod.save_controls(Session.load(None), worksheet, ctrls)


def save_controls(ctrls):
    """A full save of Invoice Lines, proving the other worksheets' controls unchanged."""
    before, inv = signatures(), invoices_controls()
    save_worksheet_controls(ws(), ctrls)
    check_untouched(before)
    check_invoices(inv, allow_new=(LINES_FIELD,))


# ── guard ───────────────────────────────────────────────────────────────────

def guard(created=True):
    """Stop unless the profile reaches ERP Master › Invoicing and Invoice Lines holds only this script's work."""
    who = hap.run('auth', 'whoami')
    app = C.app_info(APP)
    section = next((s for s in app.get('sections', []) if s['name'] == SECTION), None)
    if app.get('name') != 'ERP Master' or not section:
        sys.exit(f"profile {who.get('profile')!r} does not reach ERP Master › {SECTION}")
    if not created:
        return None
    wid = hap.ids()['worksheets'].get(WORKSHEET)
    if not wid or not any(i['id'] == wid for i in section['items']):
        sys.exit(f'{WORKSHEET} is not in ERP Master › {SECTION} yet — run `create` first')
    ctrls = hap.controls(wid)
    stock = {'Name', 'Description', 'Attachment'}
    unknown = [c['controlName'] for c in ctrls if c['controlName'] not in PLACE and c['controlName'] not in stock]
    if unknown:
        sys.exit(f"{WORKSHEET} holds controls this script does not own: {unknown}")
    for name, opts in OPTIONS.items():
        c = next((c for c in ctrls if c['controlName'] == name), None)
        if c:
            live = [(o['key'], o['value']) for o in c.get('options') or [] if not o.get('isDeleted')]
            if live != [(o['key'], o['value']) for o in opts]:
                sys.exit(f'{name} options changed: {live}')
    rules = {r['name'] for r in hap.listing('worksheet', 'rules', wid)}
    views = {v['name'] for v in hap.listing('worksheet', 'view', 'list', wid, '-a', APP)}
    buttons = {b['name'] for b in hap.listing('worksheet', 'custom-actions', wid)}
    strays = ([f'rule {n!r}' for n in rules - {RULE_FIGURES}]
              + [f'view {n!r}' for n in views - set(VIEWS) - {'All', '全部'}]
              + [f'button {n!r}' for n in buttons])
    if strays:
        sys.exit(f'{WORKSHEET} holds {strays} — stopping')
    print(f"  guard: profile {os.environ.get('HAP_PROFILE') or who.get('profile')!r}, ERP Master › {SECTION} › "
          f"{WORKSHEET}, {len(ctrls)} controls, {len(rules)} rules, views {sorted(views)}")
    return ctrls


# ── 1 · the worksheet ───────────────────────────────────────────────────────

def step_create():
    """The worksheet, in menu group Invoicing right after Invoices."""
    guard(created=False)
    section = hap.ids()['sections'][SECTION]
    wid = C.ensure_worksheet(APP, section, WORKSHEET, alias=ALIAS_WORKSHEET, icon='sys_bullet-list_office',
                             remark='Odoo account.move.line: the product, section and note lines of an invoice. '
                                    'Mounted as the subtable of the Invoices tab Invoice Lines')
    C.remember('worksheets', WORKSHEET, wid)
    items = next(s for s in C.app_info(APP)['sections'] if s['id'] == section)['items']
    ids = [i['id'] for i in items]
    order = [i for i in ids if i not in (INVOICES, wid)] + [INVOICES, wid]     # Journals, Invoices, Invoice Lines
    if order != ids:
        hap.run('app', 'sort-worksheets', APP, section, *order)
    for s in C.app_info(APP)['sections']:
        print(f"  {s['name']:<10} {[(i['name'], i['id'], i.get('alias')) for i in s['items']]}")


# ── 2 · the eight plain controls ────────────────────────────────────────────

def step_fields():
    """One full save on the fresh worksheet. The stock title control's id becomes Label; the other two stock
    controls (Description, Attachment) have no counterpart on a journal item and are not carried over — the same
    first-save pattern Units & Packagings, Products and Product Variants were built with.

    Subtotal and the three lookups wait for `computed`: a formula or a lookup needs the ids of the controls it
    reads, and a lookup of the invoice needs the Invoice relation, which `mount` creates."""
    guard()
    existing = hap.controls(ws())
    if len(existing) > 3:
        print(f'  {WORKSHEET} already holds {len(existing)} controls; nothing saved')
        return C.show(ws())
    hap.backup('invlines_controls_pre_fields', existing)
    label = ctl('TEXT', 'Label', is_title=True, extra={'enumDefault': 1})       # 1 = multi-line, as Odoo's label
    title = next((c for c in existing if c.get('attribute') == 1), None)
    if title:
        label['controlId'] = title['controlId']
    controls = [
        label,
        ctl('NUMBER', 'Sequence', extra={'dot': DOT['Sequence']}),
        ctl('DROP_DOWN', 'Display Type'),
        ctl('RELATE_SHEET', 'Product', data_source=VARIANTS, multi=False,
            advanced_setting={'bidirectional': '0', 'showtype': '3'}),
        ctl('NUMBER', 'Quantity', extra={'dot': DOT['Quantity']}),
        ctl('RELATE_SHEET', 'Unit', data_source=UNITS, multi=False,
            advanced_setting={'bidirectional': '0', 'showtype': '3'}),
        ctl('NUMBER', 'Unit Price', extra={'dot': DOT['Unit Price']}),
        ctl('NUMBER', 'Discount (%)', extra={'dot': DOT['Discount (%)']}),
    ]
    save_controls(controls)
    C.show(ws())


# ── 3 · the mount ───────────────────────────────────────────────────────────

# What the subtable shows inside an invoice, in Odoo's own column order.
SUBTABLE_COLUMNS = ('Sequence', 'Display Type', 'Product', 'Label', 'Quantity', 'Unit', 'Unit Price',
                    'Discount (%)', 'Subtotal')


def sub_list(ctrls=None):
    """The mounted subtable control on Invoices, or None."""
    return next((c for c in (ctrls or hap.controls(INVOICES))
                 if c['type'] == SUBLIST and c.get('dataSource') == ws()), None)


def step_mount():
    """Mount Invoice Lines as the subtable of the Invoices tab *Invoice Lines*, under the remark block.

    `worksheet mount-subtable` does the whole of HAP's 已有关联 handshake: it appends a 子表 control (type 34)
    to Invoices with the child's controls as its `relationControls`, reads back the placeholder controlId the
    server reserves for the child-side back-relation, and then saves that relation on Invoice Lines with exactly
    that id — which is how the child rows show under the right parent. That back-relation is this worksheet's
    **Invoice** field: it is created here, not by `fields`.

    The mount lands the control at the bottom of the Invoices form, so a second save puts it inside the tab
    under the remark block and moves every control below it down one row to make room. Nothing else on Invoices
    changes: every control is compared by id, attribute by attribute, before and after."""
    guard()
    ctrls = hap.controls(INVOICES)
    before, others = invoices_controls(), signatures()
    if not sub_list(ctrls):
        hap.backup('invlines_invoices_pre_mount', ctrls)
        hap.backup('invlines_controls_pre_mount', hap.controls(ws()))
        columns = [C.fields(ws())[n]['controlId'] for n in SUBTABLE_COLUMNS if n in C.fields(ws())]
        out = hap.run('worksheet', 'mount-subtable', INVOICES, ws(), '--name', LINES_FIELD, '-a', APP,
                      '--show-controls', ','.join(columns), '--back-relate-name', 'Invoice')
        print('  mount:', json.dumps(out, ensure_ascii=False)[:400])
        ctrls = hap.controls(INVOICES)
    place_subtable()
    back = next((c for c in hap.controls(ws()) if c['type'] == RELATION and c.get('dataSource') == INVOICES), None)
    if not back:
        sys.exit('the Invoice back-relation was not created on Invoice Lines')
    print(f"  back-relation {back['controlName']!r} {back['controlId']} source={back.get('sourceControlId')}")
    C.show(INVOICES)


SUBTABLE_DESC = ("Odoo's Invoice Lines tab. The worksheet Invoice Lines, mounted here: the same rows are also a "
                 'list of their own in the sidebar, and the invoice sums them into Untaxed Amount.')


def place_subtable():
    """Put the mounted subtable inside the Invoice Lines tab, right under the remark block, with Odoo's column
    order — and give every other Invoices control the place `invoices.py` says it has.

    The row of everything below the subtable comes from **invoices.PLACE**, not from an increment: 06 owns the
    Invoices layout, its table was updated when the subtable was inserted (row 8, everything under it one row
    lower), and reading it back is what makes this step safe to re-run. An incrementing version shifted the
    form another row every time it ran. Nothing but `row` changes on 06's own controls."""
    import invoices as inv_build                   # 06 owns the Invoices layout; this reads it, never writes it
    ctrls = hap.controls(INVOICES)
    before, others = invoices_controls(), signatures()
    sub = sub_list(ctrls)
    if not sub:
        sys.exit('the subtable control is not on Invoices')
    if inv_build.PLACE.get(LINES_FIELD, (None,))[0] != LINES_ROW:
        sys.exit(f'invoices.PLACE does not put {LINES_FIELD!r} at row {LINES_ROW}')
    f = C.fields(ws())
    columns = [f[n]['controlId'] for n in SUBTABLE_COLUMNS if n in f]
    tab_ids = {c['controlName']: c['controlId'] for c in ctrls if c['type'] == C.TAB}
    changed = False
    for c in ctrls:
        place = inv_build.PLACE.get(c['controlName'])
        if place and c['row'] != place[0]:
            c['row'] = place[0]
            changed = True
        if c['controlId'] == sub['controlId']:
            adv = {**(c.get('advancedSetting') or {}), 'hidetitle': '1',
                   'controlssorts': json.dumps(columns, ensure_ascii=False)}
            want = {'col': place[1], 'size': place[2], 'sectionId': tab_ids.get(place[3], ''),
                    'advancedSetting': adv, 'showControls': columns, 'desc': SUBTABLE_DESC}
            if any(c.get(k) != v for k, v in want.items()):
                c.update(want)
                changed = True
    if changed:
        save_worksheet_controls(INVOICES, ctrls)
        check_untouched(others)
        check_invoices(before, allow_new=(LINES_FIELD,))
    else:
        print('  the subtable is already in its place; nothing saved')
    sub = sub_list()
    C.remember('controls', 'Invoices: ' + LINES_FIELD, sub['controlId'])
    names = {c['controlId']: c['controlName'] for c in hap.controls(ws())}
    print(f"  subtable {sub['controlId']} row={sub['row']} tab={sub.get('sectionId')} "
          f"source={sub.get('sourceControlId')} shows "
          f"{[names.get(x, x) for x in sub.get('showControls') or []]}")


# ── 4 · Subtotal and the three lookups ──────────────────────────────────────

def subtotal_expression(f):
    """Odoo `_compute_totals`, tax left out: quantity × price_unit × (1 − discount / 100).

    A HAP *number* formula is plain arithmetic over `$controlId$`; only its functions need the `c` prefix, and
    there are none here."""
    q, p, d = (f'${f[n]["controlId"]}$' for n in ('Quantity', 'Unit Price', 'Discount (%)'))
    return f'{q}*{p}*(1-{d}/100)'


def step_computed():
    """Subtotal, and the three stored lookups of the invoice the standalone list needs. Both need live control
    ids: `C.add_fields` appends them and then re-saves the whole set, which re-mints the client-side ids a bare
    `add-fields` would leave a formula computing nothing on."""
    guard()
    ctrls = hap.controls(ws())
    f = hap.by_name(ctrls)
    invoice = next((c for c in ctrls if c['type'] == RELATION and c.get('dataSource') == INVOICES), None)
    if not invoice:
        sys.exit('run `mount` first — the lookups read through the Invoice relation it creates')
    source = C.fields(INVOICES)
    new = []
    if 'Subtotal' not in f:
        new.append(ctl(FORMULA_NUMBER, 'Subtotal', extra={'dot': DOT['Subtotal'],
                                                          'dataSource': subtotal_expression(f)}))
    for name, field in LOOKUPS:
        if name not in f:
            new.append(ctl('SHEET_FIELD', name, data_source=invoice['controlId'],
                           source_control_id=source[field]['controlId'],
                           extra={'strDefault': '00', 'dot': 0}))       # '00' = a stored lookup, as on Variants
    if new:
        before, inv = signatures(), invoices_controls()
        hap.backup('invlines_controls_pre_computed', ctrls)
        C.add_fields(ws(), new)
        check_untouched(before)
        check_invoices(inv, allow_new=(LINES_FIELD,))
        print(f"  added: {[c['controlName'] for c in new]}")
    else:
        print('  Subtotal and the three lookups are already there; nothing saved')
    C.show(ws())


# ── 5 · the form ────────────────────────────────────────────────────────────

def desired(c):
    """The attributes `layout` owns on control c, as they should read back."""
    name = c['controlName']
    row, col, size = PLACE[name]
    want = {'row': row, 'col': col, 'size': size, 'desc': DESC.get(name, ''), 'hint': '',
            'required': name in REQUIRED, 'alias': ALIAS.get(name, ''),
            'attribute': 1 if name == TITLE else 0,
            'fieldPermission': '101' if name in READONLY else ('011' if name in HIDDEN else '111')}
    if name in DOT:
        want['dot'] = DOT[name]
    return want


def layout_differences(ctrls):
    out = {}
    normal = lambda k, v: (v or 0) if k == 'attribute' else v      # `attribute` is absent on a non-title control
    for c in ctrls:
        if c['controlName'] not in PLACE:
            continue
        diff = {k: (c.get(k), v) for k, v in desired(c).items() if normal(k, c.get(k)) != v}
        adv = c.get('advancedSetting') or {}
        diff.update({f'advancedSetting.{k}': (adv.get(k), v)
                     for k, v in ADVANCED.get(c['controlName'], {}).items() if adv.get(k) != v})
        if diff:
            out[c['controlName']] = diff
    return out


def step_layout():
    """Every control's place, alias, help, required, read-only, default, decimals and the title field, in one
    save. The Invoice relation the mount created is placed here too — and its `sourceControlId`, which is what
    pairs it with the subtable on Invoices, is read from the live control and sent back untouched."""
    ctrls = guard()
    missing = [n for n in PLACE if n not in {c['controlName'] for c in ctrls}]
    if missing:
        sys.exit(f'{missing} are not on the worksheet yet — run fields, mount and computed first')
    hap.backup('invlines_controls_pre_layout', ctrls)
    changed = layout_differences(ctrls)
    if changed:
        for c in ctrls:
            if c['controlName'] in changed:
                c.update(desired(c))
                c['advancedSetting'] = {**(c.get('advancedSetting') or {}), **ADVANCED.get(c['controlName'], {})}
        save_controls(ctrls)
        print('  updated:', json.dumps(changed, ensure_ascii=False))
    else:
        print('  layout already as specified; nothing saved')
    ctrls = hap.controls(ws())
    left = layout_differences(ctrls)
    if left:
        sys.exit(f'layout read back with differences: {json.dumps(left, ensure_ascii=False)}')
    for c in ctrls:
        C.remember('controls', KEY + c['controlName'], c['controlId'])
    place_subtable()                                # Subtotal exists by now: give the subtable its last column
    C.show(ws())


# ── 6 · the rule ────────────────────────────────────────────────────────────

RULE_FIGURES = 'A section or a note carries no figures'


def is_any_of(f, field, labels):
    """Condition: `field` is any of the labels. A business rule's "is any of" is filterType 2, several keys."""
    keys = [o['key'] for o in f[field]['options'] if o['value'] in labels]
    if len(keys) != len(labels):
        sys.exit(f'{field} options {labels} not all found')
    return {'controlId': f[field]['controlId'], 'dataType': f[field]['type'], 'spliceType': 1,
            'filterType': C.EQ, 'value': '', 'values': keys, 'dynamicSource': [], 'isGroup': False}


def step_rules():
    """Odoo's SQL `check_non_accountable_fields_null` — "Forbidden balance or account on non-accountable line".
    A section, a subsection and a note show their text and nothing else.

    Written as *hide · is any of*, not *show · is Product*: a rule applies its action while its condition holds
    and the opposite when it fails, so the hide form leaves the six fields **visible** on a new line whose
    Display Type has not been read yet, which is what a line is for."""
    guard()
    f = C.fields(ws())
    rules = [(RULE_FIGURES, C.INTERACTION, C.any_of([is_any_of(f, 'Display Type', TEXT_LINES)]),
              [C.item(C.HIDE, *[f[t] for t in FIGURES])], {})]
    C.upsert_rules(ws(), rules, 'invlines_rules_pre_rules')
    for r in hap.listing('worksheet', 'rules', ws()):
        C.remember('rules', KEY + r['name'], r['ruleId'])


# ── 7 · the view ────────────────────────────────────────────────────────────

VIEW_COLUMNS = ('Number', 'Label', 'Product', 'Quantity', 'Unit', 'Unit Price', 'Discount (%)', 'Subtotal')
VIEWS = ('Lines',)


def step_views():
    """Odoo's standalone *Journal Items* list, minus everything the Chart of Accounts and Taxes bundles bring.
    `_order` is `date desc, move_name desc, id`; the third level is Sequence ascending, which is the order the
    lines of one document are written in."""
    guard()
    f = C.fields(ws())
    columns = [f[n]['controlId'] for n in VIEW_COLUMNS]
    sort = C.sort_by([(f['Accounting Date'], False), (f['Number'], False), (f['Sequence'], True)])
    quick = [{'fieldId': f['Display Type']['controlId'], 'selectionType': 'multiple', 'displayType': 'dropdown'}]
    views = {'Lines': (dict(viewType='table', tableFields=columns, quickFilters=quick), sort, columns)}
    for name, vid in C.upsert_views(ws(), APP, views, 'invlines_views_pre_views', default_view='Lines').items():
        C.remember('views', KEY + name, vid)
    print('  order:', C.sort_views(ws(), APP, list(views)))
    C.print_views(ws(), APP)


# ── 8 · the roll-up ─────────────────────────────────────────────────────────

ROLLUP_WRITE = 'Roll the lines up into the invoice'
ROLLUP_DELETE = 'Roll the lines up when a line is deleted'
ROLLUPS = {ROLLUP_WRITE: 'create_or_update', ROLLUP_DELETE: 'delete'}
GET_INVOICE = 'Get the invoice'
SUM_STEP = "The sum of the invoice's product lines"
UNTAXED_STEP = 'The Untaxed Amount'
TOTAL_STEP = 'The Total and the Amount Due'
WRITE_STEP = "Write the amounts into the invoice"
ROLLUP_STEPS = (GET_INVOICE, SUM_STEP, UNTAXED_STEP, TOTAL_STEP, WRITE_STEP)
NUMBER_FX = 'number_fx_id'                         # a formula node's own numeric result
FORMULA_NUMBER_NODE = '100'                        # a workflow 计算 step: plain arithmetic, a numeric result
MONEY_DOT = 2                                      # a compute step's decimal places; the server default is 0
WORKSHEET_TOTAL_NODE = '107'                       # a workflow 汇总 step: an aggregate over a whole worksheet
RELATION_EQ = '33'                                 # a workflow filter comparing a Relation with a record
IS_ANY_OF = '1'
ROLLUP_DESC = ("Odoo's account.move `_compute_amount`, without the taxes: Untaxed Amount is the sum of the "
               'lines\' Subtotal, Total is that plus the Tax the tenant seeded, and Amount Due is the Total '
               'until the Payments bundle can settle a document. The Tax itself is never written.')


def untaxed_formula():
    """Untaxed Amount: the roll-up, forced into a number.

    `+0` rather than the roll-up on its own, because an invoice whose last product line has just gone reads the
    roll-up back as nothing at all, and an empty number formula input is 0 — which is the figure Odoo shows."""
    return f'$lines-{NUMBER_FX}$+0'


def total_formula(inv_f):
    """Total = the roll-up + the invoice's own Tax; Amount Due is the same figure.

    Both compute steps are **number** formulas (actionId 100) that read the **roll-up** node, not each other:
    a workflow formula node's result can only be bound by a later node when the node is a worksheet aggregate
    (107) or a number formula (100). A *function* formula's (106) `number_fx_id` comes back from the server
    with an empty type and name, and any node reading it goes `isException: true` and refuses to publish with
    warningType 200 (Found while building)."""
    return f'$lines-{NUMBER_FX}$+$invoice-{inv_f["Tax"]["controlId"]}$'


def rollup_nodes(f, inv_f):
    """Read the invoice, sum its product lines, and write the three amounts. The Tax is read but never written.

    The filter keeps the sum to lines of **this** invoice whose Display Type is Product: Odoo's amount_untaxed
    sums `invoice_line_ids`, and a section, a subsection or a note is not one of them."""
    return [
        {'nodeAlias': 'invoice', 'nodeType': 'get_single', 'name': GET_INVOICE,
         'config': {'worksheet': INVOICES, 'execute_type': 0}},        # 0 = stop when there is no invoice
        {'nodeAlias': 'lines', 'nodeType': 'rollup', 'name': SUM_STEP,
         'config': {'mode': 'worksheet', 'worksheet': ws(), 'aggregate': 'sum',
                    'field': f['Subtotal']['controlId'],
                    'filter': {'logic': 'and', 'items': [
                        {'left': {'node': {'nodeAlias': 'trigger'}, 'fieldId': f['Invoice']['controlId'],
                                  '_filedTypeId': RELATION},
                         'op': RELATION_EQ,
                         'right': {'kind': 'field', 'node': {'nodeAlias': 'invoice'}, 'fieldId': 'rowid'}},
                        {'left': {'node': {'nodeAlias': 'trigger'}, 'fieldId': f['Display Type']['controlId'],
                                  '_filedTypeId': DROPDOWN},
                         'op': IS_ANY_OF,
                         'right': {'kind': 'literal', 'values': [
                             {'key': PRODUCT_LINE, 'value': 'Product', 'isDeleted': False}]}},
                    ]}}},
        {'nodeAlias': 'untaxed', 'nodeType': 'compute', 'name': UNTAXED_STEP,
         'config': {'mode': 'number', 'formula': untaxed_formula()}},
        {'nodeAlias': 'total', 'nodeType': 'compute', 'name': TOTAL_STEP,
         'config': {'mode': 'number', 'formula': total_formula(inv_f)}},
        {'nodeAlias': 'write', 'nodeType': 'update_record', 'name': WRITE_STEP,
         'config': {'target': {'node': {'nodeAlias': 'invoice'}}, 'worksheet': INVOICES, 'fields': [
             {'fieldId': INV['Untaxed Amount'], 'type': NUMBER,
              'valueRef': {'node': {'nodeAlias': 'untaxed'}, 'fieldId': NUMBER_FX}},
             {'fieldId': INV['Total'], 'type': NUMBER,
              'valueRef': {'node': {'nodeAlias': 'total'}, 'fieldId': NUMBER_FX}},
             {'fieldId': INV['Amount Due'], 'type': NUMBER,
              'valueRef': {'node': {'nodeAlias': 'total'}, 'fieldId': NUMBER_FX}},
         ]}},
    ]


def nodes_by_name(pid):
    proc = hap.run('workflow', 'node', 'list', pid)
    return proc, {n['name']: n for n in proc['flowNodeMap'].values()}


def invoice_of(node_id, trigger, invoice_field):
    """Condition for GET_INVOICE: the invoice's Record ID equals the trigger line's Invoice."""
    return {'nodeId': node_id, 'nodeType': 7, 'actionId': '406', 'filedId': 'rowid', 'filedValue': 'Record ID',
            'filedTypeId': 2, 'enumDefault': 0, 'conditionId': '9', 'sourceType': 0, 'conditionValues': [
                {'nodeId': trigger, 'controlId': invoice_field, 'value': '', 'sureNodeId': trigger}]}


def save_search(pid, node, worksheet, conditions, execute_type=0):
    """A search node's filter the way the UI stores it: `filters`, not the `operateCondition` batch-add sends
    and the UI never reads (BUILDING.md). Returns True when the node was changed."""
    got = hap.run('workflow', 'node', 'get', pid, node['id'])
    got = got.get('data', got)
    live = [[{k: c.get(k) for k in ('filedId', 'conditionId')} for c in group]
            for flt in got.get('filters') or [] for group in flt.get('conditions') or []]
    if (got.get('appId') == worksheet
            and live == [[{k: c.get(k) for k in ('filedId', 'conditionId')} for c in conditions]]):
        return False
    hap.run('workflow', 'node', 'save', pid, node['id'], '--type', '7', '-c', json.dumps(
        {'actionId': '406', 'appId': worksheet, 'selectNodeId': '',
         'filters': [{'spliceType': 2, 'conditions': [conditions]}],
         'sorts': [{'controlId': 'ctime', 'controlType': 16, 'isAsc': True}],
         'executeType': execute_type}, ensure_ascii=False), '-n', node['name'])
    return True


def set_formula(pid, node, expression):
    """A number formula node's expression and its decimal places, read back.

    `number` is the node's **decimal places** and it defaults to **0**: the first build's roll-up wrote
    104,603.20 into the invoice as 104,603 and 115,063.52 as 115,064, with nothing anywhere to say so (Found
    while building). `nullZero` is "treat an empty input as 0" and defaults to **false**, which makes the whole
    expression compute empty as soon as one input is empty — the Total of a document whose Tax has never been
    filled came out 0.00 instead of the Untaxed Amount. A wrong expression is likewise stored happily and
    computes empty."""
    want = {'formulaValue': expression, 'number': MONEY_DOT, 'nullZero': True}
    got = hap.run('workflow', 'node', 'get', pid, node['id'])
    got = got.get('data', got)
    if all(got.get(k) == v for k, v in want.items()):
        return False
    hap.run('workflow', 'node', 'save', pid, node['id'], '--type', '9', '-c', json.dumps(
        {'actionId': FORMULA_NUMBER_NODE, 'name': node['name'], 'execute': True, 'formulaValue': expression,
         'number': MONEY_DOT, 'nullZero': True, 'type': NUMBER}, ensure_ascii=False), '-n', node['name'])
    back = hap.run('workflow', 'node', 'get', pid, node['id'])
    back = back.get('data', back)
    if any(back.get(k) != v for k, v in want.items()):
        sys.exit(f"{node['name']}: read back {[(k, back.get(k)) for k in want]}")
    return True


def from_formula(field_id, node_id, action_id=None):
    """One field write taking a formula node's numeric result — `number_fx_id`, with the source node's own
    kind. `nodeAppType` 1 and `nodeTypeId` 9 are what the server stores for a number formula (100) and for a
    worksheet aggregate (107); a function formula (106) comes back as appType 11 and cannot be bound at all."""
    return {'fieldId': field_id, 'type': NUMBER, 'addType': 0, 'fieldValue': '', 'fieldValueId': NUMBER_FX,
            'nodeId': node_id, 'sureNodeId': node_id, 'nodeAppType': 1, 'nodeTypeId': 9,
            'nodeActionId': action_id or FORMULA_NUMBER_NODE}


def set_fields(pid, node, wanted, select_node):
    """Give an update step exactly these field writes, keeping the rest of its configuration. `select_node` must
    name a node that produces a record — here the search step that found the invoice (BUILDING.md)."""
    d = hap.run('workflow', 'node', 'get', pid, node['id'])
    d = d.get('data', d)
    fields = list(d.get('fields') or [])
    changed = d.get('selectNodeId') != select_node
    for want in wanted:
        entry = next((x for x in fields if x.get('fieldId') == want['fieldId']), None)
        if entry and all(entry.get(k) == v for k, v in want.items()):
            continue
        if entry:
            entry.update(want)
        else:
            fields.append(want)
        changed = True
    if not changed:
        return False
    hap.run('workflow', 'node', 'save', pid, node['id'], '--type', '6', '-c', json.dumps(
        {'actionId': d.get('actionId', '2'), 'appId': d.get('appId') or INVOICES, 'appType': 1,
         'selectNodeId': select_node, 'fields': fields}, ensure_ascii=False), '-n', node['name'])
    return True


def workflow_id(name):
    key = KEY + name
    pid = hap.ids().get('workflows', {}).get(key)
    if pid:
        return pid
    live = {w['name']: w.get('id') or w.get('processId') for w in hap.listing('workflow', 'list', APP)}
    return live.get(name)


def step_rollup():
    """The two workflows that make 06's amounts real, one per worksheet event HAP can trigger on: a line added
    or changed, and a line deleted. HAP's worksheet-event trigger takes **one** event — 新增或更新 ('2') and
    删除 ('3') cannot share a trigger — so the same five steps are built twice.

    The update step writes Untaxed Amount, Total and Amount Due into 06's own Number controls; not one of the
    four is replaced, and the Tax is read for the Total and never written."""
    guard()
    f, inv_f = C.fields(ws()), C.fields(INVOICES)
    for name, event in ROLLUPS.items():
        pid = workflow_id(name)
        if not pid:
            out = hap.run('workflow', 'create', '-c', ORG, '-a', APP, '-n', name, '--type', 'worksheet',
                          '-d', ROLLUP_DESC)
            data = out.get('data', out) if isinstance(out, dict) else {}
            pid = data.get('processId') or data.get('id')
            if not pid:
                sys.exit(f'{name}: no processId in `workflow create` output: {out}')
            print(f'  created {name}: {pid}')
        C.remember('workflows', KEY + name, pid)
        proc, byname = nodes_by_name(pid)
        changed = GET_INVOICE not in byname
        if changed:
            hap.run('workflow', 'node', 'batch-add', pid, '--nodes',
                    json.dumps(rollup_nodes(f, inv_f), ensure_ascii=False),
                    '--trigger-worksheet', ws(), '--trigger-event', event, '--trigger-alias', 'trigger')
            proc, byname = nodes_by_name(pid)
        trigger = proc['startEventId']
        changed |= save_search(pid, byname[GET_INVOICE], INVOICES,
                               [invoice_of(byname[GET_INVOICE]['id'], trigger, f['Invoice']['controlId'])])
        alias = lambda text: (text.replace('$lines-', f"${byname[SUM_STEP]['id']}-")
                                  .replace('$invoice-', f"${byname[GET_INVOICE]['id']}-"))
        changed |= set_formula(pid, byname[UNTAXED_STEP], alias(untaxed_formula()))
        changed |= set_formula(pid, byname[TOTAL_STEP], alias(total_formula(inv_f)))
        changed |= set_fields(pid, byname[WRITE_STEP], [
            from_formula(INV['Untaxed Amount'], byname[UNTAXED_STEP]['id']),
            from_formula(INV['Total'], byname[TOTAL_STEP]['id']),
            from_formula(INV['Amount Due'], byname[TOTAL_STEP]['id'])], byname[GET_INVOICE]['id'])
        print(f'  {name}:', C.publish(pid) if changed else 'already built; not re-published')
        print(C.structure(pid))


# ── 9 · the eight lines ─────────────────────────────────────────────────────

# The lines of the three documents 06 seeded — eight of the tenant's 33 (worksheets/07-invoice-lines.md §1,
# reference/odoo-19.4/account.move.line.md). The other 25 belong to documents 06 did not seed, or are the tax
# and payment-term lines Odoo writes itself.
#
# [FURN-0001] Ergonomic Office Chair and [FURN-0002] Height-Adjustable Desk 140cm are the tenant's **archived
# original** variants, which Phase 1 does not hold: those lines point at the product's single active variant
# and keep the tenant's own Label, which is where the reference survives. The archived originals belong with
# the Product Variants bundle, and 04 is out for review.
# (Customer Reference of the document, Sequence, Product variant, Label, Quantity, Unit, Unit Price, Discount)
SEED = (
    ('SCG-PO-88213', 0, 'Height-Adjustable Desk 140cm', '[FURN-0002] Height-Adjustable Desk 140cm',
     40, 'Units', 1650.0, 8.0),
    ('SCG-PO-88213', 1, 'Ergonomic Office Chair', '[FURN-0001] Ergonomic Office Chair',
     40, 'Units', 899.0, 8.0),
    ('SCG-PO-88213', 2, '[FURN-0003] Steel Filing Cabinet 4-Drawer', '[FURN-0003] Steel Filing Cabinet 4-Drawer',
     15, 'Units', 720.0, 0.0),
    ('KKD-2026-009', 0, 'Ergonomic Office Chair', '[FURN-0001] Ergonomic Office Chair',
     8, 'Units', 899.0, 0.0),
    ('KKD-2026-009', 1, '[FURN-0003] Steel Filing Cabinet 4-Drawer', '[FURN-0003] Steel Filing Cabinet 4-Drawer',
     4, 'Units', 720.0, 0.0),
    ('KKD-2026-009', 2, '[CONS-0001] A4 Copy Paper (Box of 5 reams)', '[CONS-0001] A4 Copy Paper (Box of 5 reams)',
     20, 'Units', 68.0, 0.0),
    ('STL-2026-0042', 0, '[SRV-0003] Annual Support Retainer', '[SRV-0003] Annual Support Retainer',
     1, 'Units', 18000.0, 0.0),
    ('STL-2026-0042', 1, '[SW-0002] Nocoly HAP Licence — Pro', '[SW-0002] Nocoly HAP Licence — Pro',
     25, 'Units', 7200.0, 10.0),
)


def subtotal_of(qty, price, discount):
    return round(qty * price * (1 - discount / 100), 2)


def titles(worksheet, control_name):
    """{rowid: title} of a worksheet, for resolving a Relation by name."""
    f = C.fields(worksheet)
    cid = f[control_name]['controlId']
    return {r['rowid']: r.get(cid) for r in C.records(worksheet, APP)}


def row_of(index, name, what):
    rows = [r for r, t in index.items() if t == name]
    if len(rows) != 1:
        sys.exit(f'{what} {name!r}: {len(rows)} records match')
    return rows[0]


def relation_cells(value):
    """A Relation read back through `record get` is a list of {sid, name}."""
    if isinstance(value, str):
        value = json.loads(value) if value.startswith('[') else []
    return [x for x in (value or []) if isinstance(x, dict)]


def relation_names(value):
    return [x.get('name') for x in relation_cells(value)]


def option_label(v):
    if isinstance(v, str):
        v = json.loads(v) if v.startswith('[') else []
    labels = [x.get('value') if isinstance(x, dict) else x for x in (v if isinstance(v, list) else [])]
    return labels[0] if labels else None


def read_line(rowid):
    """One line through `record get` (keyed by alias); `record list` can return hidden fields empty."""
    d = hap.run('worksheet', 'record', 'get', ws(), rowid, '-a', APP)['data']
    first = lambda k: (relation_names(d.get(k)) or [''])[0]
    number = lambda k: round(float(d.get(k) or 0), 2)
    return dict(rowid=rowid, invoice_row=(relation_cells(d.get('move_id')) or [{}])[0].get('sid', ''),
                invoice=first('move_id'), sequence=int(float(d.get('sequence') or 0)),
                display_type=option_label(d.get('display_type')), product=first('product_id'),
                label=d.get('name') or '', quantity=number('quantity'), unit=first('product_uom_id'),
                price=number('price_unit'), discount=number('discount'), subtotal=number('price_subtotal'),
                move_name=d.get('move_name') or '', date=d.get('date') or '',
                status=option_label(d.get('parent_state')))


def read_lines():
    return {r['rowid']: read_line(r['rowid']) for r in C.records(ws(), APP)}


def expected(seed, invoice_row):
    ref, seq, product, label, qty, unit, price, discount = seed
    return dict(invoice_row=invoice_row, sequence=seq, display_type='Product', product=product, label=label,
                quantity=float(qty), unit=unit, price=price, discount=discount,
                subtotal=subtotal_of(qty, price, discount))


def differences(live, want):
    return {k: (live.get(k), v) for k, v in want.items() if live.get(k) != v}


def invoice_numbers():
    """{Customer Reference: (rowid, Number)} for the three seeded documents."""
    f = C.fields(INVOICES)
    ref, number = f['Customer Reference']['controlId'], f['Number']['controlId']
    return {r.get(ref): (r['rowid'], r.get(number)) for r in C.records(INVOICES, APP) if r.get(ref)}


def seed_key(line):
    """What matches a live line with a seeded one: the **invoice's rowid** and the Sequence. Not the invoice's
    Number — two of the three seeded documents are unnumbered drafts, and a draft's Number is the word
    "Draft", so a Number-keyed index silently merges them (Found while building)."""
    return (line['invoice_row'], line['sequence'])


def step_seed():
    """The eight lines, matched by (the document's Number, Sequence). A line's Invoice is written as the
    relation the subtable is built on, so the row shows inside its document straight away."""
    guard()
    f = C.fields(ws())
    cid = lambda n: f[n]['controlId']
    documents = invoice_numbers()
    variants, units = titles(VARIANTS, 'Display Name'), titles(UNITS, 'Unit Name')
    live = {seed_key(d): d for d in read_lines().values()}
    hap.backup('invlines_records_pre_seed', {f'{k[0]} {k[1]}': v for k, v in live.items()})
    for seed in SEED:
        ref = seed[0]
        if ref not in documents:
            sys.exit(f'the document {ref} is not in Invoices — run `invoices.py seed` first')
        rowid_invoice, number = documents[ref]
        want = expected(seed, rowid_invoice)
        got = live.get((rowid_invoice, seed[1]))
        if got and not differences(got, want):
            continue
        values = [
            {'id': cid('Invoice'), 'value': [rowid_invoice]},
            {'id': cid('Sequence'), 'value': seed[1]},
            {'id': cid('Display Type'), 'value': [PRODUCT_LINE]},
            {'id': cid('Product'), 'value': [row_of(variants, seed[2], 'variant')]},
            {'id': cid('Label'), 'value': seed[3]},
            {'id': cid('Quantity'), 'value': seed[4]},
            {'id': cid('Unit'), 'value': [row_of(units, seed[5], 'unit')]},
            {'id': cid('Unit Price'), 'value': seed[6]},
            {'id': cid('Discount (%)'), 'value': seed[7]},
        ]
        body = json.dumps(values, ensure_ascii=False)
        if got:
            hap.run('worksheet', 'record', 'update', ws(), got['rowid'], '-a', APP, '--fields-json', body)
            rowid = got['rowid']
            print(f'  updated {number} line {seed[1]}')
        else:
            rowid = C.row_id(hap.run('worksheet', 'record', 'create', ws(), '-a', APP, '--fields-json', body))
            print(f'  created {number} line {seed[1]}: {rowid}')
        C.remember('records', f'{KEY}{ref} line {seed[1]}', rowid)
    return step_verify()


# ── 10 · 06's amounts ───────────────────────────────────────────────────────

AMOUNTS = ('Untaxed Amount', 'Total', 'Amount Due')      # Tax is never written: it waits for the Taxes bundle


def sums_by_invoice():
    """{invoice rowid: the sum of its product lines' Subtotal}, from the live lines — the same arithmetic the
    two workflows do. Keyed by rowid: two of the three seeded documents are unnumbered drafts."""
    out = {}
    for line in read_lines().values():
        if line['display_type'] == 'Product' and line['invoice_row']:
            out[line['invoice_row']] = round(out.get(line['invoice_row'], 0.0) + line['subtotal'], 2)
    return out


def read_amounts(rowid):
    d = hap.run('worksheet', 'record', 'get', INVOICES, rowid, '-a', APP)['data']
    number = lambda k: round(float(d.get(k) or 0), 2)
    return dict(number=d.get('name') or '', untaxed=number('amount_untaxed'), tax=number('amount_tax'),
                total=number('amount_total'), residual=number('amount_residual'))


def amounts_for(rowid, untaxed):
    got = read_amounts(rowid)
    total = round(untaxed + got['tax'], 2)
    return got, dict(untaxed=untaxed, total=total, residual=total)


def step_amounts():
    """Untaxed Amount, Total and Amount Due on every invoice that has lines, from the lines themselves.

    This is the same arithmetic the two workflows do, run once over what is already stored — the workflows
    keep it true from here on. The Tax is read and left exactly as the tenant seeded it, so the totals land on
    the tenant's own figures and `invoices.py verify` still passes."""
    guard()
    f = C.fields(INVOICES)
    cid = lambda n: f[n]['controlId']
    sums, bad = sums_by_invoice(), 0
    hap.backup('invlines_invoices_pre_amounts', {r: read_amounts(r) for r in sums})
    for rowid, untaxed in sorted(sums.items()):
        got, want = amounts_for(rowid, untaxed)
        number = f'{got["number"]} ({rowid[:8]})'
        if all(got[k] == v for k, v in want.items()):
            print(f'  OK    {number:<30} untaxed={got["untaxed"]:>12,.2f} tax={got["tax"]:>10,.2f} '
                  f'total={got["total"]:>12,.2f} due={got["residual"]:>12,.2f}')
            continue
        hap.run('worksheet', 'record', 'update', INVOICES, rowid, '-a', APP, '--fields-json', json.dumps(
            [{'id': cid('Untaxed Amount'), 'value': want['untaxed']},
             {'id': cid('Total'), 'value': want['total']},
             {'id': cid('Amount Due'), 'value': want['residual']}]))
        back, _ = amounts_for(rowid, untaxed)
        ok = all(back[k] == v for k, v in want.items())
        bad += not ok
        print(f'  {"OK  " if ok else "DIFF"}  {number:<30} {got} -> {back}')
    return bad


# ── verify ──────────────────────────────────────────────────────────────────

def step_verify():
    """The eight lines against the seed, and every invoice's amounts against its own lines."""
    documents = invoice_numbers()
    live = {seed_key(d): d for d in read_lines().values()}
    bad = 0
    for seed in SEED:
        rowid_invoice, number = documents.get(seed[0], (None, None))
        got = live.get((rowid_invoice, seed[1]))
        if not got:
            print(f'  MISSING  {seed[0]} line {seed[1]}')
            bad += 1
            continue
        diffs = differences(got, expected(seed, rowid_invoice))
        bad += bool(diffs)
        print(f'  {"OK  " if not diffs else "DIFF"}  {seed[0]:<14} {number:<15} {seed[1]}  '
              f'{got["label"][:42]:<44}{got["quantity"]:>7,.2f} × {got["price"]:>10,.2f} − '
              f'{got["discount"]:>5,.2f}%  = {got["subtotal"]:>12,.2f}' + (f'  <- {diffs}' if diffs else ''))
    seeded = {(documents.get(x[0], (None, None))[0], x[1]) for x in SEED}
    extra = sorted(f'{live[k]["invoice"]} line {k[1]}' for k in live if k not in seeded)
    print(f'  {len(SEED)} in the seed; {bad} missing or differing; {len(extra)} not in it {extra}')
    for rowid, untaxed in sorted(sums_by_invoice().items()):
        got, want = amounts_for(rowid, untaxed)
        diffs = differences(got, want)
        bad += bool(diffs)
        print(f'  {"OK  " if not diffs else "DIFF"}  {got["number"]:<16} ({rowid[:8]}) '
              f'untaxed={got.get("untaxed")} tax={got.get("tax")} total={got.get("total")} '
              f'due={got.get("residual")}' + (f'  <- lines say {want}' if diffs else ''))
    return bad


def step_lines(*numbers):
    """One document's lines, in Sequence order."""
    lines = sorted(read_lines().values(), key=lambda d: (d['invoice'], d['invoice_row'], d['sequence']))
    for number in numbers or sorted({d['invoice'] for d in lines}):
        for d in [x for x in lines if x['invoice'] == number]:
            print(f'  {number}: ' + json.dumps(d, ensure_ascii=False))


def step_order():
    """The view's records in the order the view returns them. `record list --view-id` returns only the view's
    own columns, so Accounting Date and Sequence — sorted on but not shown — are read separately."""
    f = C.fields(ws())
    number, label = f['Number']['controlId'], f['Label']['controlId']
    rest = {d['rowid']: d for d in read_lines().values()}
    for v in hap.listing('worksheet', 'view', 'list', ws(), '-a', APP):
        res = hap.run('worksheet', 'record', 'list', ws(), '-a', APP, '-n', '100', '--view-id', v['viewId'],
                      '--use-field-id-as-key')
        data = res.get('data', res) if isinstance(res, dict) else res
        rows = (data.get('rows') if isinstance(data, dict) else data) or []
        print(f"  {v['name']} ({len(rows)}):")
        for r in rows:
            d = rest.get(r['rowid'], {})
            print(f"    {r.get(number) or d.get('move_name'):<18} [{d.get('date')}] seq={d.get('sequence')} "
                  f"{(r.get(label) or '')[:50]}")


# ── self-check: the roll-up, through the CLI ────────────────────────────────

TEST_LABEL = 'TEST roll-up line'


def wait_for(rowid, wanted, seconds=40):
    for _ in range(seconds):
        got = read_amounts(rowid)
        if wanted(got):
            return got
        time.sleep(1)
    return read_amounts(rowid)


def step_selfcheck():
    """The roll-up end to end, on a `TEST …` document, through the workflow rather than by arithmetic here:

      1. add a TEST line to it and read the invoice's Untaxed Amount, Total and Amount Due back;
      2. change the line's Quantity and read them back again.

    The line is **left in place** and named `TEST …`: nothing in this build deletes a record. The third case — a
    line removed — was proved once by hand on a line created for it (§2, *What the UI test found*): the delete
    roll-up fires and the invoice follows, provided the delete carries `--trigger-workflow`. Both workflows
    carry the same five steps; the delete one differs only in its trigger event, which `check` reads back."""
    guard()
    f = C.fields(ws())
    cid = lambda n: f[n]['controlId']
    inv_f = C.fields(INVOICES)
    ref_cid, number_cid = inv_f['Customer Reference']['controlId'], inv_f['Number']['controlId']
    target = next((r for r in C.records(INVOICES, APP) if (r.get(ref_cid) or '').startswith('TEST-SEQ-5')), None)
    if not target:
        sys.exit('no TEST-SEQ-5 document to test the roll-up on')
    rowid_invoice, number = target['rowid'], target.get(number_cid)
    variants, units = titles(VARIANTS, 'Display Name'), titles(UNITS, 'Unit Name')
    line = next((d for d in read_lines().values() if d['label'] == TEST_LABEL), None)
    base = round(sum(d['subtotal'] for d in read_lines().values()
                     if d['invoice_row'] == rowid_invoice and d['display_type'] == 'Product'
                     and d['label'] != TEST_LABEL), 2)
    bad = 0
    if not line:
        values = [{'id': cid('Invoice'), 'value': [rowid_invoice]},
                  {'id': cid('Sequence'), 'value': 900},
                  {'id': cid('Display Type'), 'value': [PRODUCT_LINE]},
                  {'id': cid('Product'), 'value': [row_of(variants, '[CONS-0002] Whiteboard Marker Set',
                                                          'variant')]},
                  {'id': cid('Label'), 'value': TEST_LABEL},
                  {'id': cid('Quantity'), 'value': 1},
                  {'id': cid('Unit'), 'value': [row_of(units, 'Units', 'unit')]},
                  {'id': cid('Unit Price'), 'value': 100},
                  {'id': cid('Discount (%)'), 'value': 10}]
        rowid = C.row_id(hap.run('worksheet', 'record', 'create', ws(), '-a', APP,
                                 '--fields-json', json.dumps(values, ensure_ascii=False)))
        C.remember('records', KEY + TEST_LABEL, rowid)
        print(f'  created {TEST_LABEL}: {rowid} on {number}')
        line = read_line(rowid)
    # Always write the Quantity, and two different ones: a `record update` that changes nothing fires no
    # worksheet-event workflow, so a check that only re-reads would pass on a stale value.
    for label, quantity in (('the Quantity set to 3', 3), ('the Quantity changed to 5', 5)):
        hap.run('worksheet', 'record', 'update', ws(), line['rowid'], '-a', APP, '--fields-json',
                json.dumps([{'id': cid('Quantity'), 'value': quantity}]))
        expect = round(base + quantity * 100 * 0.9, 2)
        got = wait_for(rowid_invoice, lambda d: d['untaxed'] == expect)
        want = dict(untaxed=expect, total=round(expect + got['tax'], 2))
        ok = got['untaxed'] == want['untaxed'] and got['total'] == want['total'] \
            and got['residual'] == want['total']
        bad += not ok
        print(f'  {"OK  " if ok else "DIFF"}  {label:<28} {number} untaxed={got["untaxed"]:,.2f} '
              f'tax={got["tax"]:,.2f} total={got["total"]:,.2f} due={got["residual"]:,.2f}'
              + ('' if ok else f'  <- wanted {want}'))
        line = read_line(line['rowid'])
    print(f'  {TEST_LABEL} is left on {number}; nothing was deleted. A line removed is §3, test in the UI.')
    return bad


# ── check: read the configuration back ──────────────────────────────────────

def step_check():
    """Controls, options, defaults, the rule, the view, the mount and the two workflows against this spec."""
    ctrls = hap.controls(ws())
    f = hap.by_name(ctrls)
    names = {c['controlId']: c['controlName'] for c in ctrls}
    problems = []
    if set(f) != set(PLACE):
        problems.append(f'controls {sorted(set(f) ^ set(PLACE))}')
    problems += [f'{n}: {d}' for n, d in layout_differences(ctrls).items()]
    for name, opts in OPTIONS.items():
        live = [(o['key'], o['value']) for o in f.get(name, {}).get('options', []) if not o.get('isDeleted')]
        if live != [(o['key'], o['value']) for o in opts]:
            problems.append(f'{name} options {live}')
    for name, want in (('Sequence', '10'), ('Display Type', 'Product'), ('Quantity', '1'),
                       ('Unit Price', '0'), ('Discount (%)', '0')):
        source = json.loads((f.get(name, {}).get('advancedSetting') or {}).get('defsource') or '[]')
        value = source[0]['staticValue'] if source else None
        label = next((o['value'] for o in f.get(name, {}).get('options', []) if o['key'] == value), value)
        if label != want:
            problems.append(f'{name} default {label!r}, want {want!r}')
    if f.get(TITLE, {}).get('attribute') != 1:
        problems.append(f'{TITLE} is not the title field')
    for name, target in RELATIONS.items():
        if f.get(name, {}).get('dataSource') != target:
            problems.append(f"{name} points at {f.get(name, {}).get('dataSource')}, want {target}")
    if f.get('Invoice', {}).get('dataSource') != INVOICES:
        problems.append(f"Invoice points at {f.get('Invoice', {}).get('dataSource')}")
    want_formula = subtotal_expression(f)
    if f.get('Subtotal', {}).get('dataSource') != want_formula:
        problems.append(f"Subtotal is {f.get('Subtotal', {}).get('dataSource')!r}, want {want_formula!r}")
    source = C.fields(INVOICES)
    for name, field in LOOKUPS:
        c = f.get(name, {})
        if (c.get('dataSource'), c.get('sourceControlId')) != (f"${f['Invoice']['controlId']}$",
                                                               source[field]['controlId']):
            problems.append(f"{name} looks up {c.get('dataSource')} / {c.get('sourceControlId')}")
    # the rule
    rules = {r['name']: r for r in hap.listing('worksheet', 'rules', ws())}
    r = rules.get(RULE_FIGURES)
    if not r:
        problems.append(f'rule {RULE_FIGURES!r} missing')
    else:
        conds = [g for group in r['filters'] for g in group.get('groupFilters', [])]
        got = (r['type'], r['disabled'], {i['type'] for i in r['ruleItems']},
               sorted(LABEL['Display Type'].get(v) for c in conds for v in c.get('values', [])),
               [names.get(c['controlId']) for i in r['ruleItems'] for c in i['controls']])
        if got != (C.INTERACTION, False, {C.HIDE}, sorted(TEXT_LINES), FIGURES):
            problems.append(f'rule {RULE_FIGURES!r}: {got}')
    if set(rules) != {RULE_FIGURES}:
        problems.append(f'rules {sorted(rules)}')
    # the view
    views = {v['name']: C.view_info(ws(), APP, v['viewId'])
             for v in hap.listing('worksheet', 'view', 'list', ws(), '-a', APP)}
    v = views.get('Lines', {})
    got = dict(columns=[names.get(x) for x in v.get('showControls', [])],
               sort=[(names.get(s['controlId']), s['isAsc']) for s in v.get('moreSort', [])],
               sortCid=names.get(v.get('sortCid')), sortType=v.get('sortType'),
               filters=[names.get(x['controlId']) for x in v.get('filters', [])],
               quick=[names.get(q['controlId']) for q in v.get('fastFilters', [])])
    want = dict(columns=list(VIEW_COLUMNS),
                sort=[('Accounting Date', False), ('Number', False), ('Sequence', True)],
                sortCid='Accounting Date', sortType=1, filters=[], quick=['Display Type'])
    if got != want:
        problems.append(f'view Lines: {got}')
    if list(views) != list(VIEWS):
        problems.append(f'views {list(views)}')
    # the mount
    sub = sub_list()
    inv_names = {c['controlId']: c['controlName'] for c in hap.controls(INVOICES)}
    if not sub:
        problems.append('the subtable is not on Invoices')
    else:
        columns = [names.get(x) for x in sub.get('showControls') or []]
        if columns != list(SUBTABLE_COLUMNS):
            problems.append(f'subtable columns {columns}')
        if sub.get('sectionId') != INV['Invoice Lines']:
            problems.append(f"subtable tab {inv_names.get(sub.get('sectionId'))}")
        if sub.get('sourceControlId') != f['Invoice']['controlId']:
            problems.append(f"subtable pairs with {sub.get('sourceControlId')}, "
                            f"Invoice is {f['Invoice']['controlId']}")
        order = sorted(hap.controls(INVOICES), key=lambda c: (c.get('row', 0), c.get('col', 0)))
        tab = [c['controlName'] for c in order if c.get('sectionId') == INV['Invoice Lines']]
        print(f'  the Invoices tab Invoice Lines now holds: {tab}')
        if tab != ['Invoice Lines note', LINES_FIELD, 'Terms and Conditions', 'Untaxed Amount', 'Tax', 'Total',
                   'Amount Due']:
            problems.append(f'the tab holds {tab}')
    # the two workflows
    for name, event in ROLLUPS.items():
        pid = hap.ids().get('workflows', {}).get(KEY + name)
        if not pid:
            problems.append(f'workflow {name!r} is not in ids.json')
            continue
        proc, byname = nodes_by_name(pid)
        missing = [n for n in ROLLUP_STEPS if n not in byname]
        if missing:
            problems.append(f'workflow {name!r} is missing {missing}')
        trigger = hap.run('workflow', 'node', 'get', pid, proc['startEventId'])
        trigger = trigger.get('data', trigger)
        want_id = {'create_or_update': '2', 'delete': '3'}[event]
        if str(trigger.get('triggerId')) != want_id or trigger.get('appId') != ws():
            problems.append(f"workflow {name!r} triggers on {trigger.get('appId')} / {trigger.get('triggerId')}, "
                            f'want {ws()} / {want_id}')
        info = hap.run('workflow', 'get', pid)
        info = info.get('data', info)
        print(f"  workflow {name:<46} {pid} triggerId={trigger.get('triggerId')} "
              f"published={info.get('publishStatus')} enabled={info.get('enabled')}")
    print('  check: ' + ('OK — controls, options, defaults, the rule, the view, the mount and the two '
                         'roll-up workflows as specified' if not problems
                         else 'DIFFERENCES\n    ' + '\n    '.join(problems)))
    return len(problems)


def step_all():
    for name in ('create', 'fields', 'mount', 'computed', 'layout', 'rules', 'views', 'rollup', 'seed',
                 'amounts'):
        print(f'\n── {name} ' + '─' * 60)
        STEPS[name]()
    print('\n── check ' + '─' * 60)
    return step_check()


def show():
    C.show(ws())


STEPS = {
    'create': step_create,
    'fields': step_fields,
    'mount': step_mount,
    'computed': step_computed,
    'layout': step_layout,
    'rules': step_rules,
    'views': step_views,
    'rollup': step_rollup,
    'seed': step_seed,
    'amounts': step_amounts,
    'all': step_all,
    'verify': step_verify,
    'check': step_check,
    'selfcheck': step_selfcheck,
    'order': step_order,
    'lines': step_lines,
    'untouched': step_untouched,
    'show': show,
}

if __name__ == '__main__':
    step = sys.argv[1] if len(sys.argv) > 1 else 'check'
    if step not in STEPS:
        raise SystemExit(f"Unknown step {step!r}; choose from {', '.join(STEPS)}")
    result = STEPS[step](*sys.argv[2:])
    if step in ('verify', 'check', 'all', 'selfcheck', 'amounts') and result:
        sys.exit(1)
