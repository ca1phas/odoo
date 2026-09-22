#!/usr/bin/env python3
"""Build the Product Categories worksheet (Odoo product.category, as on casimir.odoo.com saas~19.4) in ERP Master.

Bundle 1 of the six that join Phase 1. It adds the worksheet, gives **Products** the Category field it never had,
and seeds the tenant's seven categories and all fourteen products' categories. Nothing is replaced or deleted.
Requirements: nocoly/worksheets/08-product-categories.md. Generic helpers: common.py. Run from the repo root with
the CLI's interpreter:

    ~/.hap-venv/bin/python nocoly/build/prodcat.py create    # 0. the worksheet in the menu group Products
    ~/.hap-venv/bin/python nocoly/build/prodcat.py fields    # 1. Name and Parent Category, one save on the empty
                                                             #    worksheet; the self-relation brings its own reverse
    ~/.hap-venv/bin/python nocoly/build/prodcat.py products  # 2. Category on Products (add-fields, two-way, so the
                                                             #    reverse **Products** lands here) and the Category
                                                             #    quick filter on its Products and List views
    ~/.hap-venv/bin/python nocoly/build/prodcat.py computed  # 3. Parent Complete Name (stored lookup), Complete Name
                                                             #    (function formula) and # Products (汇总, type 37)
    ~/.hap-venv/bin/python nocoly/build/prodcat.py layout    # 4. the two reverses renamed, places, title field,
                                                             #    permissions, help and hints
    ~/.hap-venv/bin/python nocoly/build/prodcat.py views     # 5. Categories — the only view: columns, sort, quick filter
    ~/.hap-venv/bin/python nocoly/build/prodcat.py roles     # 6. roles.py's create step, which now carries this
                                                             #    worksheet into the four business roles
    ~/.hap-venv/bin/python nocoly/build/prodcat.py seed      # 7. the seven categories (parents first), then every
                                                             #    product's Category, then verify
    ~/.hap-venv/bin/python nocoly/build/prodcat.py all       # every step above, then check

    ~/.hap-venv/bin/python nocoly/build/prodcat.py verify    # the live categories and the products' categories
                                                             #    against the 19.4 extract, # Products included
    ~/.hap-venv/bin/python nocoly/build/prodcat.py check     # controls, permissions, formula, lookup, roll-up, view,
                                                             #    Products' Category and its quick filters
    ~/.hap-venv/bin/python nocoly/build/prodcat.py selfcheck # the recursion chain and the roll-up, driven through the
                                                             #    CLI on TEST Category (left in the worksheet)
    ~/.hap-venv/bin/python nocoly/build/prodcat.py order     # the view's records in the order the view sorts them
    ~/.hap-venv/bin/python nocoly/build/prodcat.py category "Goods"   # stored values by Name, hidden fields included
    ~/.hap-venv/bin/python nocoly/build/prodcat.py untouched # the other worksheets: control count and digest
    ~/.hap-venv/bin/python nocoly/build/prodcat.py show      # the live control list

Every step reads the live state first and is safe to re-run; a second run writes nothing. Every write step stops
unless the profile reaches ERP Master › Products › Product Categories and the worksheet holds only this script's
own work. **Products is written to with `add-fields` only** — never a full `update-fields` replace — and its
other nineteen controls are compared id by id before and after every call.

Profile. As in the other builders: --profile > $HAP_PROFILE > hap-cli's active profile.
"""
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import common as C
import hap

APP = hap.ids()['app']
SECTION = 'Products'
WORKSHEET = 'Product Categories'
KEY = WORKSHEET + ': '                            # ids.json key prefix for everything this worksheet owns
ALIAS = 'product_category'
HERE = Path(__file__).resolve().parent
REFERENCE = HERE.parent / 'reference' / 'odoo-19.4' / 'product.category.md'
PRODUCTS = hap.ids()['worksheets']['Products']
PRODUCTS_TAB = 'General Information'              # the tab on Products that gains Category
OTHERS = ('Contacts', 'Units & Packagings', 'Product Variants', 'Journals', 'Invoices', 'Invoice Lines')


def ws():
    return hap.ids()['worksheets'][WORKSHEET]


# ── the form ────────────────────────────────────────────────────────────────

NAME = 'Name'
COMPLETE = 'Complete Name'
PARENT = 'Parent Category'
CHILDREN = 'Child Categories'
PRODUCTS_REL = 'Products'                         # the reverse of Category on Products
COUNT = '# Products'
PARENT_COMPLETE = 'Parent Complete Name'          # hidden; Complete Name is built on it
CATEGORY = 'Category'                             # the control this bundle adds to Products
# The Chart of Accounts bundle (09-chart-of-accounts.md, built by accounts.py `categories`) brings Odoo's page
# Accounting and its two accounts. accounts.py adds them with `add-fields`, which parks a control at row 9999; this
# script's `layout` places them, as products.py places Products' Category.
ACCOUNTING, INCOME, EXPENSE = 'Accounting', 'Income Account', 'Expense Account'
BUNDLE_2 = (ACCOUNTING, INCOME, EXPENSE)

# §1's form layout: Name; Parent Category | Complete Name; Child Categories | # Products; Products. The hidden
# lookup sits under them all — a hidden control still needs a place.
#
# Bundle 2's tab Accounting (Income Account | Expense Account) goes in at row 2, and the rows under it moved down
# two. The row decides where the tab sits in the bar HAP draws at the foot of the record: pd-openweb's
# getControlsByTab lists the type-52 tabs and the showtype-6 relation lists together in row order — Child
# Categories is one — and the showtype-2 lists after all of them — Products is one. At row 2 the bar reads
# Accounting · Child Categories · Products: Odoo's own page first, HAP's two lists together. (At a row under the
# lists it would split them: Child Categories · Accounting · Products.)
PLACE = {
    NAME: (0, 0, 12),
    PARENT: (1, 0, 6), COMPLETE: (1, 1, 6),
    ACCOUNTING: (2, 0, 12),
    INCOME: (3, 0, 6), EXPENSE: (3, 1, 6),
    CHILDREN: (4, 0, 6), COUNT: (4, 1, 6),
    PRODUCTS_REL: (5, 0, 12),
    PARENT_COMPLETE: (6, 0, 6),
}
TAB_OF = {INCOME: ACCOUNTING, EXPENSE: ACCOUNTING}   # the controls that sit inside a tab
HINTS = {NAME: 'e.g. Lamps'}                      # Odoo's placeholder; every other control gets none
DESC = {  # Odoo's help where it reads well for a user, else plain words — only what the field does
    # (owner's rule, 22 Sep 2026). Build notes and Odoo references: worksheets/08-product-categories.md, foot.
    COMPLETE: 'The full path of the category, e.g. All / Saleable.',
    CHILDREN: 'The categories under this one.',
    PRODUCTS_REL: 'The products in this category. To add one, set its Category on the product.',
    COUNT: 'The number of products under this category (Does not consider the children categories)',
    PARENT_COMPLETE: '',
    # bundle 2: Odoo's help on property_account_income_categ_id / property_account_expense_categ_id (product.py)
    INCOME: 'This account will be used when validating a customer invoice.',
    EXPENSE: 'The expense is recorded on this account when a vendor bill is confirmed.',
}
REQUIRED = {NAME}
# A hidden field never shows as a table column, so Complete Name — the title, and a view column — is read-only
# and hidden on create ("100") rather than hidden, as Contacts' and Product Variants' Display Name are.
# The two reverses and the roll-up are read-only **and hidden on create** ("100") since 21 Sep 2026 (15 §1):
# they were "101" and so rendered on the Create Record form, where Odoo — whose smart buttons only exist on a
# saved record — shows nothing of the kind. "011" would have been wrong: a hidden field never shows as a table
# column either, and Child Categories, Products and # Products are columns of this worksheet's views.
PERMISSION = {
    COMPLETE: '100',                              # read-only · hidden on create
    CHILDREN: '100', PRODUCTS_REL: '100', COUNT: '100',        # read-only · hidden on create
    PARENT_COMPLETE: '011',                       # hidden
}
ROLLUP = 37                                       # HAP's 汇总; hap-cli's builder is app_creator.fields.rollup_control
COUNT_AGGREGATE = 6                               # enumDefault 6 = count (1 avg · 2 max · 3 min · 5 sum)

# What each control is: (type, alias, builder kwargs). The two reverses are made by the server, not here.
NEW = {
    NAME: ('TEXT', 'name', {'required': True}),
    PARENT: ('RELATE_SHEET', 'parent_id', {}),
    COMPLETE: ('FORMULA_FUNC', 'complete_name', {}),
    PARENT_COMPLETE: ('SHEET_FIELD', 'parent_complete_name', {}),   # not an Odoo field
    COUNT: (ROLLUP, 'product_count', {}),
    CHILDREN: (None, 'child_id', {}),             # the reverse of Parent Category
    PRODUCTS_REL: (None, 'product_ids', {}),      # the reverse of Category on Products; not an Odoo field
    # bundle 2, added by accounts.py: a tab, and two one-way Relations to Chart of Accounts
    ACCOUNTING: ('SECTION', '', {}),
    INCOME: ('RELATE_SHEET', 'property_account_income_categ_id', {}),
    EXPENSE: ('RELATE_SHEET', 'property_account_expense_categ_id', {}),
}
ALIASES = {name: alias for name, (_, alias, _) in NEW.items()}


def ref(c):
    return f"${c['controlId']}$"


def function_source(expression):
    """dataSource of a function formula (type 53), as contacts.py and variants.py write it."""
    return json.dumps({'type': 'mdfunction', 'expression': expression, 'status': 1}, ensure_ascii=False)


def complete_name_expression(f):
    """Odoo _compute_complete_name: the parent's complete name, ' / ', this name — recursive through the stored
    lookup, which chains the way Units & Packagings' Absolute Quantity does up a unit chain. A number formula
    has no IF, so this is a function formula; TRIM as on Contacts and Product Variants."""
    name, parent = ref(f[NAME]), ref(f[PARENT_COMPLETE])
    return f'IF(ISBLANK({parent}),TRIM({name}),CONCAT({parent}," / ",TRIM({name})))'


# ── the other worksheets, untouched ─────────────────────────────────────────

SIGNATURE = ('controlName', 'type', 'alias', 'row', 'col', 'size', 'sectionId', 'required', 'attribute', 'unique',
             'fieldPermission', 'dataSource', 'sourceControlId', 'showControls', 'advancedSetting', 'desc', 'hint')


def signature(worksheet_id):
    """A worksheet's controls by id, position in the listing not compared."""
    return sorted(json.dumps([c['controlId']] + [c.get(k) for k in SIGNATURE], sort_keys=True, ensure_ascii=False)
                  for c in hap.controls(worksheet_id))


def signatures(names=OTHERS):
    return {name: signature(hap.ids()['worksheets'][name]) for name in names}


def check_untouched(before, names=OTHERS):
    after = signatures(names)
    for name in before:
        if after[name] != before[name]:
            sys.exit(f'{name} controls changed: {sorted(set(after[name]) ^ set(before[name]))}')
    print('  untouched: ' + ', '.join(f'{n} ({len(after[n])})' for n in after))


def step_untouched():
    """Control count and digest of every other worksheet — run before and after a build."""
    for name, sig in {**signatures(), 'Products': signature(PRODUCTS)}.items():
        digest = hashlib.sha256(''.join(sig).encode()).hexdigest()[:16]
        print(f'  {name:<20} {len(sig):>2} controls  sha256:{digest}')


# ── guard ───────────────────────────────────────────────────────────────────

TEST_NAME = 'TEST Category'                       # selfcheck's own record; left in the worksheet


def guard(fresh=False):
    """Stop unless the profile reaches ERP Master › Products › Product Categories and the worksheet holds only
    this script's work. `fresh` allows the three stock controls of a brand-new worksheet. Returns the controls."""
    who = hap.run('auth', 'whoami')
    app = hap.run('app', 'info', '-a', APP).get('data', {})
    worksheet = hap.ids().get('worksheets', {}).get(WORKSHEET)
    section = next((s for s in app.get('sections', []) if any(i['id'] == worksheet for i in s['items'])), None)
    if app.get('name') != 'ERP Master' or not section or section['name'] != SECTION:
        sys.exit(f"profile {who.get('profile')!r} does not reach ERP Master › {SECTION} › {WORKSHEET}")
    problems, ctrls = [], hap.controls(worksheet)
    stock = {'Name', 'Description', 'Attachment', '名称', '描述', '附件'}
    known = set(PLACE) | (stock if fresh else set())
    # A reverse control the server minted is known by its id, whatever it is called: a two-way Relation's
    # reverse arrives as "Child" (a self-relation) or named after the source worksheet, and `layout` renames it.
    f = hap.by_name(ctrls)
    reverses = {f[PARENT]['sourceControlId']} if PARENT in f else set()
    category = products_fields().get(CATEGORY)
    if category:
        reverses.add(category.get('sourceControlId'))
    problems += [f"unknown control {c['controlName']!r} ({c['controlId']})" for c in ctrls
                 if c['controlName'] not in known and c['controlId'] not in reverses]
    if len(f) != len(ctrls):
        problems.append(f'two controls share a name: {sorted(c["controlName"] for c in ctrls)}')
    views = {v['name'] for v in hap.listing('worksheet', 'view', 'list', worksheet, '-a', APP)}
    problems += [f'unknown view {n!r}' for n in views - {'Categories', 'All', '全部'}]
    buttons = {b['name'] for b in hap.listing('worksheet', 'custom-actions', worksheet)}
    problems += [f'unknown button {n!r}' for n in buttons]          # §1: this worksheet has no buttons
    rules = {r['name'] for r in hap.listing('worksheet', 'rules', worksheet)}
    problems += [f'unknown rule {n!r}' for n in rules]              # §1: and no rules
    if NAME in f and f[NAME].get('alias') == 'name':
        live = {hap.run('worksheet', 'record', 'get', worksheet, r['rowid'], '-a', APP)['data'].get('name')
                for r in C.records(worksheet, APP)}
        problems += [f'unknown record {n!r}' for n in live
                     if n not in reference_categories() and not str(n).startswith('TEST')]
    if problems:
        sys.exit(f"{WORKSHEET} differs from this script's work — stopping:\n  " + '\n  '.join(problems))
    print(f"  guard: profile {os.environ.get('HAP_PROFILE') or who.get('profile')!r}, ERP Master › {SECTION} › "
          f"{WORKSHEET}, {len(ctrls)} controls, {len(rules)} rules, {len(buttons)} buttons, views {sorted(views)}")
    return ctrls


# ── 0 · the worksheet ───────────────────────────────────────────────────────

REMARK = ('Odoo product.category: the tree a catalogue hangs on — every product belongs to one category, and a '
          'category may sit under another')
ICON = 'sys_8_4_folder'                           # `hap icon search 文件夹` — the catalogue is 426 names, and a
                                                  # name that is not in it answers 400 and leaves a broken icon


def step_create():
    section = C.ensure_section(APP, SECTION, after='Contacts')
    C.remember('sections', SECTION, section)
    wid = C.ensure_worksheet(APP, section, WORKSHEET, alias=ALIAS, icon=ICON, remark=REMARK)
    C.remember('worksheets', WORKSHEET, wid)
    for s in C.app_info(APP)['sections']:
        print(f"  {s['name']:<10} {s['id']}  {[(i['name'], i['id'], i.get('alias')) for i in s['items']]}")


# ── 1 · Name and Parent Category ────────────────────────────────────────────

def step_fields():
    """Name (the stock title control's id reused) and Parent Category, in one save of the empty worksheet.

    A single Relation to its own worksheet always comes back two-way: the server adds the reverse — Odoo's
    child_id — at row 9999 with no alias, and `layout` names and places it."""
    guard(fresh=True)
    existing = hap.controls(ws())
    f = hap.by_name(existing)
    if NAME in f and PARENT in f:
        print(f'  {NAME} and {PARENT} already exist; nothing saved')
        return C.show(ws())
    if len(existing) > 3:
        sys.exit(f'{WORKSHEET} already has {len(existing)} controls — refusing to replace them.')
    hap.backup('prodcat_controls_pre_fields', existing)
    name = C.control('TEXT', NAME, PLACE[NAME], alias=ALIASES[NAME], hint=HINTS[NAME], required=True,
                     is_title=True)
    name['controlId'] = next(c for c in existing if c.get('attribute') == 1)['controlId']
    parent = C.control('RELATE_SHEET', PARENT, PLACE[PARENT], alias=ALIASES[PARENT], hint='', data_source=ws(),
                       multi=False, advanced_setting={'showtype': '3', 'bidirectional': '1'})   # 3 = dropdown
    C.save_controls(ws(), [name, parent])
    ensure_reverses()
    C.show(ws())


# ── 2 · Category on Products ────────────────────────────────────────────────

def products_fields():
    return hap.by_name(c for c in hap.controls(PRODUCTS) if c['type'] != C.TAB)


# Where Category sits on Products' form: after Cost, before Internal Reference, which is Odoo's own order
# (right column: Sales Price · Sales Taxes · Cost · Purchase Taxes · Category · Reference).
# AddWorksheetControls **parks every control it adds at row 9999, col 0**, whatever row and col the payload
# carries (it does keep `size` and `sectionId`), and only a full save of the control set can move one — so
# `fields` adds it and **`products.py layout` places it**, that step being 03's own read-modify-write: it reads
# the live controls and sends the same list back. Products' PLACE carries Category and Internal Reference on
# row 6. Re-running `prodcat fields` never moves it back; this is only what `check` expects to find.
CATEGORY_PLACE = (9, 0, 6)                        # Internal Reference sits beside it at (9, 1)
# Row 9, not 6, since 21 Sep 2026: the Taxes bundle put Sales Taxes and Purchase Taxes above it, which is
# where Odoo's own form has them (Sales Price · Sales Taxes · Cost · Purchase Taxes · Category · Reference).
# `products.py` PLACE is the single source for the row; this constant follows it.


def category_control(tab_id):
    """Odoo product.template.categ_id: a single two-way Relation, not required, no default, on the tab General
    Information. Two-way, so its reverse is this worksheet's Products list."""
    control = C.control('RELATE_SHEET', CATEGORY, CATEGORY_PLACE, alias='categ_id', hint='', desc='',
                        data_source=ws(), multi=False,
                        advanced_setting={'showtype': '3', 'bidirectional': '1'})
    control['sectionId'] = tab_id
    return control


def step_products():
    """Give Products its Category control and both its views a Category quick filter.

    `add-fields` only: `update-fields` replaces the whole control set, and Products is live. The control is sent
    without a client-side id so the server mints one, which is how hap-cli's own builder adds a relation."""
    guard()
    ctrls = hap.controls(PRODUCTS)
    hap.backup('products_controls_pre_category', ctrls)
    f = hap.by_name(c for c in ctrls if c['type'] != C.TAB)
    tab = next(c for c in ctrls if c['type'] == C.TAB and c['controlName'] == PRODUCTS_TAB)
    if CATEGORY not in f:
        before = signatures()
        others = signature(PRODUCTS)
        C.append_controls(PRODUCTS, [category_control(tab['controlId'])])
        check_untouched(before)
        after = {json.loads(s)[0] for s in signature(PRODUCTS)}
        lost = [json.loads(s)[0] for s in others if json.loads(s)[0] not in after]
        if lost:
            sys.exit(f'Products lost control(s) {lost}')
        print(f'  Products: {CATEGORY} added')
    category = products_fields()[CATEGORY]
    C.remember('controls', 'Products: ' + CATEGORY, category['controlId'])
    print(f"  Products / {CATEGORY}: {category['controlId']} at row {category.get('row')} col "
          f"{category.get('col')} size {category.get('size')} in the tab {PRODUCTS_TAB} — add-fields parks a "
          f'new control at row 9999; `products.py layout` moves it to {CATEGORY_PLACE}')
    ensure_reverses()
    quick_filters(category)
    C.print_views(PRODUCTS, APP)


def reverse_pairs():
    """The two-way Relations whose reverse belongs on this worksheet: (name, the forward control, the worksheet
    the reverse points back at)."""
    f = C.fields(ws())
    out = [(CHILDREN, f[PARENT], ws())] if PARENT in f else []
    category = products_fields().get(CATEGORY)
    return out + ([(PRODUCTS_REL, category, PRODUCTS)] if category else [])


def ensure_reverses():
    """Make sure each two-way Relation's reverse is a real control here, carrying the id the server reserved.

    The two halves behave differently:

    * A **self**-relation's reverse is made by the server itself, in the same `update-fields` save that creates
      the relation (Parent Category's "Child", at row 9999 width 0). It must not be written by hand: saving a
      control that carries the reserved id makes the server mint its own reverse **as well**, and the worksheet
      then holds two controls with the same controlId. So a missing one is reported, not repaired.
    * A relation added to **another** worksheet with `add-fields` gets no reverse at all: the server only
      reserves the id in `sourceControlId` and leaves it dangling. That one is saved here the way hap-cli's
      `mount-subtable` completes HAP's 已有关联 handshake — same controlId, `sourceControlId` pointing back at
      the forward control."""
    ctrls = hap.controls(ws())
    have = {c['controlId'] for c in ctrls}
    new = []
    for name, forward, source in reverse_pairs():
        reserved = forward.get('sourceControlId')
        if not reserved:
            sys.exit(f'{name}: {forward["controlName"]} has no sourceControlId — it was saved one-way')
        if reserved in have:
            continue
        if source == ws():
            sys.exit(f'{name}: {forward["controlName"]} points at the reserved id {reserved} and no control '
                     'carries it. The server makes a self-relation\'s reverse itself, and writing one by hand '
                     'duplicates the control — re-create Parent Category instead (the worksheet must be empty).')
        row, col, size = PLACE[name]
        control = C.control('RELATE_SHEET', name, (row, col, size), alias=ALIASES[name], hint='',
                            desc=DESC.get(name, ''), data_source=source, multi=True,
                            advanced_setting={'showtype': '2'})              # 2 = the related records as a list
        control.update(controlId=reserved, sourceControlId=forward['controlId'], sourceControlType=6,
                       fieldPermission=PERMISSION[name])
        new.append(control)
        print(f"  {name}: reverse {reserved} saved, pairing with {forward['controlName']} "
              f"({forward['controlId']})")
    if new:
        before = signatures()
        C.save_controls(ws(), ctrls + new)
        check_untouched(before)
    for name, forward, _ in reverse_pairs():
        reverse = next((c for c in hap.controls(ws()) if c['controlId'] == forward.get('sourceControlId')), None)
        if not reverse:
            sys.exit(f'{name}: the reverse {forward.get("sourceControlId")} is still not on {WORKSHEET}')
        if reverse.get('sourceControlId') != forward['controlId'] or reverse.get('enumDefault') != 2:
            sys.exit(f'{name}: reverse read back {json.dumps(reverse, ensure_ascii=False)[:300]}')
        print(f"  reverse of {forward['controlName']}: {reverse['controlName']!r} {reverse['controlId']} "
              f"row={reverse.get('row')} size={reverse.get('size')} alias={reverse.get('alias')!r}")


PRODUCT_VIEWS = ('Products', 'List')              # §1: a quick filter on both, and no new column


def quick_filters(category):
    """Add a Category quick filter to Products' two views, keeping every other quick filter as it is.

    Only `fastFilters` is sent (`--edit-attrs fastFilters`), so the views' filters, sort and columns are not
    re-written. §1 adds no column: Odoo's list carries categ_id as optional="hide"."""
    for name in PRODUCT_VIEWS:
        view = next(v for v in hap.listing('worksheet', 'view', 'list', PRODUCTS, '-a', APP) if v['name'] == name)
        info = C.view_info(PRODUCTS, APP, view['viewId'])
        live = info.get('fastFilters') or []
        if any(q['controlId'] == category['controlId'] for q in live):
            print(f'  Products / {name}: Category quick filter already there')
            continue
        hap.backup(f'products_view_{name}_pre_quickfilter', info)
        item = {'controlId': category['controlId'],
                'advancedSetting': {'allowitem': '2', 'direction': '2'}}     # 2 = any of, shown as a dropdown
        hap.run('worksheet', 'view', 'update', PRODUCTS, view['viewId'], '-a', APP,
                '--view-json', json.dumps({'fastFilters': live + [item]}, ensure_ascii=False),
                '--edit-attrs', 'fastFilters')
        back = [q['controlId'] for q in C.view_info(PRODUCTS, APP, view['viewId']).get('fastFilters') or []]
        if back != [q['controlId'] for q in live] + [category['controlId']]:
            sys.exit(f'Products / {name}: quick filters read back {back}')
        print(f'  Products / {name}: Category quick filter added')


# ── 3 · Complete Name, its lookup and the roll-up ───────────────────────────

def step_computed():
    """Complete Name (a text function formula), the stored lookup it reads, and # Products (a 汇总 over the
    Products relation, count).

    The lookup and the final expression go in one save, as Units & Packagings does: if HAP refuses a lookup of a
    formula on the same worksheet, nothing is left behind. `add-fields` stores a control under its client-side
    id and a formula saved that way computes nothing, so C.add_fields re-saves the set to re-mint it."""
    guard()
    f = C.fields(ws())
    if COMPLETE not in f:
        # a placeholder expression until the lookup exists; rewritten in the save below
        formula = C.control('FORMULA_FUNC', COMPLETE, PLACE[COMPLETE], alias=ALIASES[COMPLETE], hint='',
                            advanced_setting={'analysislink': '1', 'sorttype': 'en'},
                            extra={'enumDefault2': 2,                                   # 2 = a text result
                                   'dataSource': function_source(f'TRIM({ref(f[NAME])})')})
        C.add_fields(ws(), [formula])
        f = C.fields(ws())
        print(f'  {COMPLETE} added')
    ctrls = hap.controls(ws())
    hap.backup('prodcat_controls_pre_computed', ctrls)
    f = hap.by_name(ctrls)
    if PARENT_COMPLETE not in f:
        lookup = C.control('SHEET_FIELD', PARENT_COMPLETE, PLACE[PARENT_COMPLETE], alias=ALIASES[PARENT_COMPLETE],
                           hint='', data_source=f[PARENT]['controlId'],
                           source_control_id=f[COMPLETE]['controlId'],
                           extra={'strDefault': '00'})              # '00' = stored, so a formula can read it
        ctrls.append(lookup)
        f[PARENT_COMPLETE] = lookup
        f[COMPLETE]['dataSource'] = function_source(complete_name_expression(f))
        C.save_controls(ws(), ctrls)
        print(f'  {PARENT_COMPLETE} added and {COMPLETE} rewritten to read it')
    f = C.fields(ws())
    if COUNT not in f:
        products = f.get(PRODUCTS_REL) or reverse_control()
        if not products:
            sys.exit(f'the {PRODUCTS_REL} relation is not here yet — run the `products` step first')
        C.add_fields(ws(), [rollup_control(products)])
        print(f'  {COUNT} added')
    ctrls = hap.controls(ws())
    f = hap.by_name(ctrls)
    expression = complete_name_expression(f)
    if json.loads(f[COMPLETE].get('dataSource') or '{}').get('expression') != expression:
        print(f"  {COMPLETE}: read back {f[COMPLETE].get('dataSource')!r}; rewriting")
        f[COMPLETE]['dataSource'] = function_source(expression)
        C.save_controls(ws(), ctrls)
    print('  ' + json.dumps(computed_state(), ensure_ascii=False))
    C.show(ws())


def reverse_control():
    """The reverse of Products.Category on this worksheet, whatever it is called at the time."""
    category = products_fields().get(CATEGORY)
    if not category:
        return None
    return next((c for c in hap.controls(ws()) if c['controlId'] == category.get('sourceControlId')), None)


def rollup_control(products):
    """# Products: HAP's 汇总 (type 37) over the Products relation, counting the related records.

    hap-cli has a builder — app_creator.fields.rollup_control — which maps aggregate "count" to enumDefault 6
    and writes `dataSource` as $<the bridge relation>$ with `sourceControlId` the column being aggregated. A
    count still needs a column named; Products' own title (Name) is the one used."""
    from hap_cli.core.app_creator.fields import rollup_control as build
    control = build(COUNT, via_control_id=products['controlId'],
                    source_control_id=products_fields()[NAME]['controlId'], aggregate='count')
    row, col, size = PLACE[COUNT]
    control.update(controlName=COUNT, alias=ALIASES[COUNT], row=row, col=col, size=size, dot=0,
                   desc=DESC[COUNT], hint='')
    return control


def computed_state():
    """What the three computed controls read back as: the formula, the lookup's source, the roll-up's bridge."""
    f = C.fields(ws())
    names = {c['controlId']: c['controlName'] for c in hap.controls(ws())}
    names.update({c['controlId']: c['controlName'] for c in hap.controls(PRODUCTS)})
    readable = lambda s: ''.join(names.get(x, x) if len(x) == 24 else x for x in (s or '').split('$'))
    out = {}
    if COMPLETE in f:
        out[COMPLETE] = dict(type=f[COMPLETE]['type'], result=f[COMPLETE].get('enumDefault2'),
                             expression=readable(json.loads(f[COMPLETE].get('dataSource') or '{}')
                                                 .get('expression')))
    if PARENT_COMPLETE in f:
        out[PARENT_COMPLETE] = dict(type=f[PARENT_COMPLETE]['type'], stored=f[PARENT_COMPLETE].get('strDefault'),
                                    through=readable(f[PARENT_COMPLETE].get('dataSource')),
                                    of=names.get(f[PARENT_COMPLETE].get('sourceControlId')))
    if COUNT in f:
        out[COUNT] = dict(type=f[COUNT]['type'], aggregate=f[COUNT].get('enumDefault'),
                          enumDefault2=f[COUNT].get('enumDefault2'), dot=f[COUNT].get('dot'),
                          through=readable(f[COUNT].get('dataSource')),
                          of=names.get(f[COUNT].get('sourceControlId')))
    return out


# ── 4 · layout ──────────────────────────────────────────────────────────────

# HAP renders a list-style Relation (`showtype` 2) as a **tab at the foot of the record**, not as a field in the
# form grid — and a list with no `showControls` shows the row count over the words *No visible fields*. These are
# the columns each of the two lists shows. The ids are read live, because they live on two different worksheets:
# Child Categories' columns belong to this worksheet, Products' to Products.
LIST_COLUMNS = {CHILDREN: (None, (COMPLETE, COUNT)),
                PRODUCTS_REL: (PRODUCTS, ('Name', 'Internal Reference'))}
_list_columns = {}


def list_columns(name):
    """The controlIds of the columns relation list `name` shows, resolved once per run."""
    if name not in _list_columns:
        source, wanted = LIST_COLUMNS[name]
        f = hap.by_name(c for c in hap.controls(source or ws()) if c['type'] != C.TAB)
        _list_columns[name] = [f[w]['controlId'] for w in wanted]
    return _list_columns[name]


def desired(c, tab_ids):
    """The attributes `layout` owns on control c, as they should read back. A tab owns its place only."""
    name = c['controlName']
    row, col, size = PLACE[name]
    out = {'row': row, 'col': col, 'size': size, 'sectionId': tab_ids.get(TAB_OF[name], '') if name in TAB_OF else ''}
    if c['type'] == C.TAB:
        return out
    out.update({'alias': ALIASES[name], 'hint': HINTS.get(name, ''), 'desc': DESC.get(name, ''),
                'required': name in REQUIRED, 'fieldPermission': PERMISSION.get(name, '111'),
                'attribute': 1 if name == COMPLETE else 0})
    if name in LIST_COLUMNS:
        out['showControls'] = list_columns(name)
    return out


def layout_differences(ctrls):
    tab_ids = {c['controlName']: c['controlId'] for c in ctrls if c['type'] == C.TAB}
    out = {}
    for c in ctrls:
        if c['controlName'] not in PLACE:
            continue
        diff = {k: (c.get(k), v) for k, v in desired(c, tab_ids).items()
                if (c.get(k) or (0 if k == 'attribute' else '' if isinstance(v, str) else False)) != v}
        if diff:
            out[c['controlName']] = diff
    return out


def step_layout():
    """Name the two reverse controls, place everything, and move the title to Complete Name.

    A reverse control arrives at row 9999 with width 0 and no alias, so this is where Child Categories and
    Products get their names, aliases, places and their read-only permission. The title field moves in one full
    save: `attribute` 1 on Complete Name and 0 on every other control, all in the same update-fields."""
    guard()
    ensure_reverses()
    ctrls = hap.controls(ws())
    hap.backup('prodcat_controls_pre_layout', ctrls)
    f = hap.by_name(ctrls)
    for control_name, forward, _ in reverse_pairs():
        if control_name in f:
            continue
        reverse = next(c for c in ctrls if c['controlId'] == forward['sourceControlId'])
        print(f"  {reverse['controlName']!r} ({reverse['controlId']}) renamed to {control_name!r}")
        reverse['controlName'] = control_name
    # Bundle 2's tab and accounts are placed when they are there; accounts.py adds them.
    missing = [n for n in PLACE if n not in {c['controlName'] for c in ctrls} and n not in BUNDLE_2]
    if missing:
        sys.exit(f'controls missing — run the earlier steps first: {missing}')
    changed = layout_differences(ctrls)
    # `f` was read before the renames above, so a control whose name is not in it is one this step just renamed
    if changed or any(c['controlName'] not in f for c in ctrls):
        tab_ids = {c['controlName']: c['controlId'] for c in ctrls if c['type'] == C.TAB}
        for c in ctrls:
            if c['controlName'] in PLACE:
                c.update(desired(c, tab_ids))
        before = signatures()
        # Through the CLI's session: the account Relations' snapshots of Chart of Accounts put the control list past
        # the kernel's argument limit, and common.save_controls keeps their static defaults (BUILDING.md).
        C.save_controls(ws(), ctrls)
        check_untouched(before)
    left = layout_differences(hap.controls(ws()))
    if left:
        sys.exit(f'layout read back with differences: {json.dumps(left, ensure_ascii=False)}')
    print('  updated:', json.dumps(changed, ensure_ascii=False) if changed else 'nothing (already as specified)')
    for c in hap.controls(ws()):
        C.remember('controls', KEY + c['controlName'], c['controlId'])
    C.show(ws())


# ── 5 · the Categories view ─────────────────────────────────────────────────

COLUMNS = (COMPLETE, PARENT, COUNT)
VIEW = 'Categories'


def step_views():
    """Categories, the only view: every category, Complete Name · Parent Category · # Products, sorted on
    Complete Name A→Z (Odoo's own _order), with a Parent Category quick filter (its search view's second field).

    There is no Archived view: product.category has no active field."""
    guard()
    f = C.fields(ws())
    columns = [f[n]['controlId'] for n in COLUMNS]
    quick = [{'fieldId': f[PARENT]['controlId'], 'selectionType': 'multiple', 'displayType': 'dropdown'}]
    views = {VIEW: (dict(viewType='table', tableFields=columns, quickFilters=quick),
                    C.sort_spec([f[COMPLETE]]), columns)}
    for name, vid in C.upsert_views(ws(), APP, views, 'prodcat_views_pre_views', default_view=VIEW).items():
        C.remember('views', KEY + name, vid)
    print('  order:', C.sort_views(ws(), APP, list(views)))
    C.print_views(ws(), APP)


# ── 6 · roles ───────────────────────────────────────────────────────────────

def step_roles():
    """roles.py owns the app's roles; its ORDER and its four matrices now carry Product Categories, with the
    same rule Products has. This runs its `create` step, which upserts the roles and reconciles the scopes."""
    import roles
    return roles.step_create()


# ── 7 · seed ────────────────────────────────────────────────────────────────

def reference_categories():
    """The seven categories of the 19.4 extract: name -> dict(id, parent, complete_name, odoo_count)."""
    out, section = {}, ''
    for line in REFERENCE.read_text(encoding='utf-8').splitlines():
        if line.startswith('#'):
            section = line.strip('# ')
            continue
        cells = [x.strip() for x in line.strip().strip('|').split('|')] if line.startswith('|') else []
        if section.startswith('Records') and len(cells) == 5 and cells[0].isdigit():
            out[cells[1]] = dict(id=int(cells[0]), parent=None if cells[2] == '—' else cells[2],
                                 complete_name=cells[3], odoo_count=int(cells[4]))
    return dict(sorted(out.items(), key=lambda kv: (kv[1]['parent'] is not None, kv[1]['id'])))


def reference_products():
    """Every product's category in the 19.4 extract: product name -> complete name of its category."""
    out, section = {}, ''
    for line in REFERENCE.read_text(encoding='utf-8').splitlines():
        if line.startswith('#'):
            section = line.strip('# ')
            continue
        cells = [x.strip() for x in line.strip().strip('|').split('|')] if line.startswith('|') else []
        if section.startswith("Every product's category") and len(cells) == 2 and cells[0] not in ('Product', '---'):
            out[cells[0]] = cells[1]
    return out


def expected_counts():
    """# Products per category as **this** build computes it: the products in the category itself, not in its
    children (Odoo's help, not Odoo's code — see §1)."""
    by_complete = {e['complete_name']: name for name, e in reference_categories().items()}
    counts = {name: 0 for name in reference_categories()}
    for complete in reference_products().values():
        counts[by_complete[complete]] += 1
    return counts


def relation(value):
    """A Relation cell from `record get`: [{'sid': rowid, 'name': title}, …] — as a list of (rowid, title)."""
    if isinstance(value, str):
        value = json.loads(value) if value.startswith('[') else []
    if not isinstance(value, list):
        return []
    return [(v.get('sid'), v.get('name')) for v in value if isinstance(v, dict)]


def related_count(value):
    """How many records a Relation cell holds. The **reverse** half of a two-way Relation comes back from
    `record get` as a row count — an integer, not the rows — the way a 子表 does; the forward half comes back
    as the list."""
    return value if isinstance(value, int) else len(relation(value))


def read_category(rowid):
    """One category through `record get` (by alias); `record list` can return hidden fields empty."""
    d = hap.run('worksheet', 'record', 'get', ws(), rowid, '-a', APP)['data']
    parents = relation(d.get('parent_id'))
    count = d.get('product_count')
    return dict(rowid=rowid, name=d.get('name'), complete_name=d.get('complete_name') or '',
                parent=(parents[0][1] if parents else None),
                parent_rowid=(parents[0][0] if parents else None),
                parent_complete_name=d.get('parent_complete_name') or '',
                children=related_count(d.get('child_id')),
                products=related_count(d.get('product_ids')),
                count=int(float(count)) if count not in (None, '') else None)


def read_categories():
    """Every category by Name, each read with `record get`.

    Not from `record list`: that returns only the **default view's columns** — every other field comes back as
    an empty string, Name included here, because the Categories view shows Complete Name, Parent Category and
    # Products."""
    return {c['name']: c for c in (read_category(r['rowid']) for r in C.records(ws(), APP))}


def read_products():
    """Every product by Name: rowid and the title of its Category (read one by one, as above)."""
    out = {}
    for r in C.records(PRODUCTS, APP):
        d = hap.run('worksheet', 'record', 'get', PRODUCTS, r['rowid'], '-a', APP)['data']
        categories = relation(d.get('categ_id'))
        out[d.get('name')] = dict(rowid=r['rowid'], category=(categories[0][1] if categories else None),
                                  category_rowid=(categories[0][0] if categories else None))
    return out


def step_seed(*only):
    """The seven categories, parents before children, then every product's Category. `only` limits it to
    category names. Everything written is read back."""
    guard()
    f = C.fields(ws())
    cid = lambda n: f[n]['controlId']
    categories = read_categories()
    hap.backup('prodcat_records_pre_seed', categories)
    for name, e in reference_categories().items():
        if only and name not in only:
            continue
        live = categories.get(name)
        parent_rowid = categories[e['parent']]['rowid'] if e['parent'] else None
        if live and (live['name'], live['parent']) == (name, e['parent']):
            continue
        values = json.dumps([{'id': cid(NAME), 'value': name},
                             {'id': cid(PARENT), 'value': [parent_rowid] if parent_rowid else []}],
                            ensure_ascii=False)
        if live:
            hap.run('worksheet', 'record', 'update', ws(), live['rowid'], '-a', APP, '--fields-json', values)
            rowid = live['rowid']
            print(f'  updated {name}')
        else:
            rowid = C.row_id(hap.run('worksheet', 'record', 'create', ws(), '-a', APP, '--fields-json', values))
            print(f'  created {name}: {rowid}')
        categories[name] = read_category(rowid)
        if (categories[name]['name'], categories[name]['parent']) != (name, e['parent']):
            sys.exit(f'{name}: read back {categories[name]}')
    for name, category in read_categories().items():
        C.remember('records', KEY + name, category['rowid'])
    seed_products(categories)
    time.sleep(6)                                  # stored lookups, the formula on them and the roll-up settle
    return step_verify(*only)


def seed_products(categories):
    """Every product's Category, from the extract. Products' own records are the only thing written there."""
    products = read_products()
    hap.backup('products_records_pre_category', products)
    category_id = C.fields(PRODUCTS)[CATEGORY]['controlId']
    by_complete = {c['complete_name']: name for name, c in read_categories().items()}
    for product, complete in reference_products().items():
        live = products.get(product)
        if not live:
            sys.exit(f'product {product!r} is not in {SECTION} › Products')
        want = by_complete.get(complete)
        if not want:
            sys.exit(f'no category reads {complete!r} — seed the categories first')
        if live['category_rowid'] == categories[want]['rowid']:
            continue
        hap.run('worksheet', 'record', 'update', PRODUCTS, live['rowid'], '-a', APP, '--fields-json',
                json.dumps([{'id': category_id, 'value': [categories[want]['rowid']]}], ensure_ascii=False))
        print(f'  {product}: Category set to {complete}')
    back = read_products()                         # a Relation reads back as the related record's **title**,
    wrong = {p: (back[p]['category'], complete)    # which here is the Complete Name
             for p, complete in reference_products().items() if back[p]['category'] != complete}
    if wrong:
        sys.exit(f'products read back with the wrong category: {wrong}')


def step_verify(*only):
    """Compare the live categories with the 19.4 extract — Parent, Complete Name and # Products — and every
    product's Category with it."""
    reference, categories = reference_categories(), read_categories()
    counts = expected_counts()
    bad = 0
    for name, e in reference.items():
        if only and name not in only:
            continue
        live = categories.get(name)
        if not live:
            print(f'  MISSING  {name}')
            bad += 1
            continue
        # A Relation reads back as the related record's **title**, which here is its Complete Name.
        children = sum(1 for x in categories.values() if x['parent'] == e['complete_name'])   # a TEST child counts
        want = {'parent': reference[e['parent']]['complete_name'] if e['parent'] else None,
                'complete_name': e['complete_name'], 'count': counts[name],
                'products': counts[name], 'children': children}
        diffs = {k: (live.get(k), v) for k, v in want.items() if live.get(k) != v}
        bad += bool(diffs)
        print(f"  {'OK  ' if not diffs else 'DIFF'}  {name:<17} parent={str(live['parent']):<9} "
              f"complete={live['complete_name']:<26} #products={live['count']} "
              f"children={live['children']} products={live['products']}"
              + (f'  <- {diffs}' if diffs else ''))
    products, wanted = read_products(), reference_products()
    wrong = {p: (products.get(p, {}).get('category'), c) for p, c in wanted.items()
             if products.get(p, {}).get('category') != c}
    blank = sorted(p for p, v in products.items() if not v['category'])
    extra = sorted(set(categories) - set(reference))
    print(f'  {len(reference)} categories in the extract; {bad} missing or differing; '
          f'{len(extra)} not in the extract {extra}')
    print(f'  {len(wanted)} products in the extract; {len(wrong)} with the wrong category {wrong}; '
          f'{len(blank)} of {len(products)} products with no category {blank}')
    return bad + len(wrong)


def step_category(*names):
    """Print the stored values of categories by Name, hidden fields included."""
    categories = read_categories()
    for name in names or sorted(categories):
        c = categories.get(name)
        print(f'  {name}: ' + (json.dumps(c, ensure_ascii=False) if c else 'no such category'))


def step_order():
    """The view's records in the order the view returns them (its own sort)."""
    f = C.fields(ws())
    complete = f[COMPLETE]['controlId']
    for v in hap.listing('worksheet', 'view', 'list', ws(), '-a', APP):
        res = hap.run('worksheet', 'record', 'list', ws(), '-a', APP, '-n', '100', '--view-id', v['viewId'],
                      '--use-field-id-as-key')
        data = res.get('data', res) if isinstance(res, dict) else res
        rows = (data.get('rows') if isinstance(data, dict) else data) or []
        print(f"  {v['name']} ({len(rows)}): " + ', '.join(str(r.get(complete)) for r in rows))


# ── self-check: the recursion chain and the roll-up, through the CLI ────────

def attempt(*args):
    """Run a write expected to be refused; return (refused, message)."""
    try:
        out = hap.run(*args)
    except RuntimeError as error:
        return True, str(error)[:300]
    data = out.get('data', out) if isinstance(out, dict) else {}
    code = (out.get('resultCode') if isinstance(out, dict) else None) or \
           (data.get('resultCode') if isinstance(data, dict) else None)
    return code not in (None, 1), json.dumps(out, ensure_ascii=False)[:300]


def step_selfcheck():
    """Prove through the CLI what §1 asks the platform to do:

      1. a third level — TEST Category under Goods / Consumables — reads "Goods / Consumables / TEST Category",
         which is one level deeper than the tenant goes;
      2. renaming a parent carries down the chain;
      3. # Products counts the products of the category itself and follows a product moving in and out;
      4. a category may be made its own parent — §1's test 12, which HAP has no way to refuse.

    TEST Category is left in the worksheet, with no products and no children."""
    guard()
    f = C.fields(ws())
    cid = lambda n: f[n]['controlId']
    categories = read_categories()
    problems = []
    consumables, goods = categories['Consumables'], categories['Goods']
    test = categories.get(TEST_NAME)
    if not test:
        rowid = C.row_id(hap.run('worksheet', 'record', 'create', ws(), '-a', APP, '--fields-json', json.dumps(
            [{'id': cid(NAME), 'value': TEST_NAME}, {'id': cid(PARENT), 'value': [consumables['rowid']]}])))
        print(f'  created {TEST_NAME}: {rowid}')
    else:
        rowid = test['rowid']
        hap.run('worksheet', 'record', 'update', ws(), rowid, '-a', APP, '--fields-json', json.dumps(
            [{'id': cid(PARENT), 'value': [consumables['rowid']]}]))
    C.remember('records', KEY + TEST_NAME, rowid)
    time.sleep(6)
    test = read_category(rowid)
    print(f"  1. three levels: {TEST_NAME} under Consumables reads {test['complete_name']!r} "
          f"(lookup {test['parent_complete_name']!r})")
    if test['complete_name'] != 'Goods / Consumables / TEST Category':
        problems.append(f"three levels: {test['complete_name']!r}")

    hap.run('worksheet', 'record', 'update', ws(), goods['rowid'], '-a', APP,
            '--fields-json', json.dumps([{'id': cid(NAME), 'value': 'TEST Goods'}]))
    time.sleep(8)
    renamed = read_category(rowid)
    print(f"  2. renaming Goods to 'TEST Goods' makes it {renamed['complete_name']!r}")
    if renamed['complete_name'] != 'TEST Goods / Consumables / TEST Category':
        problems.append(f"rename down the chain: {renamed['complete_name']!r} "
                        f"(Consumables reads {read_category(consumables['rowid'])['complete_name']!r})")
    hap.run('worksheet', 'record', 'update', ws(), goods['rowid'], '-a', APP,
            '--fields-json', json.dumps([{'id': cid(NAME), 'value': 'Goods'}]))
    time.sleep(8)
    if read_category(rowid)['complete_name'] != 'Goods / Consumables / TEST Category':
        problems.append('Goods was renamed back and the chain did not follow')

    products = read_products()
    marker, product = 'A4 Copy Paper (Box of 5 reams)', None
    product = products[marker]
    category_id = C.fields(PRODUCTS)[CATEGORY]['controlId']
    hap.run('worksheet', 'record', 'update', PRODUCTS, product['rowid'], '-a', APP, '--fields-json',
            json.dumps([{'id': category_id, 'value': [rowid]}]))
    time.sleep(6)
    moved = (read_category(rowid)['count'], read_category(consumables['rowid'])['count'])
    print(f'  3. moving {marker!r} into {TEST_NAME}: # Products {moved[0]} there, {moved[1]} on Consumables')
    if moved != (1, 1):
        problems.append(f'roll-up after the move: {moved}, want (1, 1)')
    hap.run('worksheet', 'record', 'update', PRODUCTS, product['rowid'], '-a', APP, '--fields-json',
            json.dumps([{'id': category_id, 'value': [consumables['rowid']]}]))
    time.sleep(6)
    back = (read_category(rowid)['count'], read_category(consumables['rowid'])['count'])
    print(f'  3. and back: # Products {back[0]} on {TEST_NAME}, {back[1]} on Consumables')
    if back != (0, 2):
        problems.append(f'roll-up after moving it back: {back}, want (0, 2)')

    refused, message = attempt('worksheet', 'record', 'update', ws(), rowid, '-a', APP, '--fields-json',
                               json.dumps([{'id': cid(PARENT), 'value': [rowid]}]))
    time.sleep(6)
    itself = read_category(rowid)
    print(f"  4. {TEST_NAME} as its own parent: {'refused' if refused else 'accepted'}; it now reads "
          f"{itself['complete_name']!r} (parent {itself['parent']!r})")
    hap.run('worksheet', 'record', 'update', ws(), rowid, '-a', APP, '--fields-json',
            json.dumps([{'id': cid(PARENT), 'value': [consumables['rowid']]}]))
    time.sleep(6)
    restored = read_category(rowid)
    print(f"  4. put back under Consumables: {restored['complete_name']!r}")
    if restored['complete_name'] != 'Goods / Consumables / TEST Category':
        problems.append(f"after the recursion test: {restored['complete_name']!r}")

    print('  selfcheck: ' + ('OK — three levels, a rename down the chain, the roll-up both ways, and the '
                             'recursion case recorded'
                             if not problems else 'DIFFERENCES\n    ' + '\n    '.join(problems)))
    return len(problems)


# ── check ───────────────────────────────────────────────────────────────────

def step_check():
    """Controls, permissions, the formula, the lookup, the roll-up, the view, Products' Category and its two
    quick filters, against this spec; exits non-zero on a difference."""
    ctrls = hap.controls(ws())
    f = hap.by_name(ctrls)
    names = {c['controlId']: c['controlName'] for c in ctrls}
    problems = []
    if set(f) != set(PLACE):
        problems.append(f'controls {sorted(set(f) ^ set(PLACE))}')
    problems += [f'{n}: {d}' for n, d in layout_differences(ctrls).items()]
    if f.get(COMPLETE, {}).get('attribute') != 1:
        problems.append(f'the title field is {next((c["controlName"] for c in ctrls if c.get("attribute") == 1), None)!r}')
    state = computed_state()
    want_state = {
        COMPLETE: dict(type=53, result=2, expression=f'IF(ISBLANK({PARENT_COMPLETE}),TRIM({NAME}),'
                                                     f'CONCAT({PARENT_COMPLETE}," / ",TRIM({NAME})))'),
        PARENT_COMPLETE: dict(type=30, stored='00', through=PARENT, of=COMPLETE),
        COUNT: dict(type=ROLLUP, aggregate=COUNT_AGGREGATE, enumDefault2=6, dot=0, through=PRODUCTS_REL,
                    of=NAME),
    }
    for name, want in want_state.items():
        if state.get(name) != want:
            problems.append(f'{name}: {state.get(name)} != {want}')
    if f.get(PARENT, {}).get('dataSource') != ws() or f.get(PARENT, {}).get('enumDefault') != 1:
        problems.append(f'{PARENT}: dataSource {f.get(PARENT, {}).get("dataSource")} '
                        f'enumDefault {f.get(PARENT, {}).get("enumDefault")}')
    for name in (CHILDREN, PRODUCTS_REL):
        if f.get(name, {}).get('enumDefault') != 2:
            problems.append(f'{name} is not a multi-record relation ({f.get(name, {}).get("enumDefault")})')
    if f.get(CHILDREN, {}).get('sourceControlId') != f.get(PARENT, {}).get('controlId'):
        problems.append(f'{CHILDREN} is not the reverse of {PARENT}')
    views = {v['name']: C.view_info(ws(), APP, v['viewId'])
             for v in hap.listing('worksheet', 'view', 'list', ws(), '-a', APP)}
    if list(views) != [VIEW]:
        problems.append(f'views {list(views)}')
    v = views.get(VIEW, {})
    got = dict(columns=[names.get(x) for x in v.get('showControls', [])],
               sort=[(names.get(s['controlId']), s['isAsc']) for s in v.get('moreSort', [])],
               sortCid=names.get(v.get('sortCid')), sortType=v.get('sortType'),
               filters=[(names.get(x['controlId']), x['filterType']) for x in v.get('filters', [])],
               quick=[(names.get(q['controlId']), (q.get('advancedSetting') or {}).get('allowitem'))
                      for q in v.get('fastFilters', [])])
    want = dict(columns=list(COLUMNS), sort=[(COMPLETE, True)], sortCid=COMPLETE, sortType=2, filters=[],
                quick=[(PARENT, '2')])
    if got != want:
        problems.append(f'view {VIEW}: {got} != {want}')
    if hap.listing('worksheet', 'custom-actions', ws()):
        problems.append('this worksheet has a button; §1 gives it none')
    if hap.listing('worksheet', 'rules', ws()):
        problems.append('this worksheet has a rule; §1 gives it none')
    problems += products_differences()
    print('  check: ' + ('OK — the controls with their places and permissions (bundle 2\'s Accounting tab and its '
                         'two accounts among them), Complete Name the title and '
                         'built on the lookup, the roll-up over Products, the Categories view, and Products\' '
                         'Category with a quick filter on both its views'
                         if not problems else 'DIFFERENCES\n    ' + '\n    '.join(problems)))
    return len(problems)


def products_differences():
    """What this bundle added to Products, read back: the Category control and the two quick filters."""
    ctrls = hap.controls(PRODUCTS)
    f = hap.by_name(c for c in ctrls if c['type'] != C.TAB)
    tab = next((c for c in ctrls if c['type'] == C.TAB and c['controlName'] == PRODUCTS_TAB), None)
    out = []
    category = f.get(CATEGORY)
    if not category:
        return [f'Products has no {CATEGORY} control']
    row, col, size = CATEGORY_PLACE
    want = {'type': 29, 'alias': 'categ_id', 'dataSource': ws(), 'enumDefault': 1, 'required': False,
            'sectionId': tab['controlId'], 'row': row, 'col': col, 'size': size}
    diff = {k: (category.get(k), v) for k, v in want.items() if category.get(k) != v}
    if diff:
        out.append(f'Products / {CATEGORY}: {diff}')
    if (category.get('advancedSetting') or {}).get('bidirectional') != '1':
        out.append(f'Products / {CATEGORY} is not two-way')
    for name in PRODUCT_VIEWS:
        view = next((v for v in hap.listing('worksheet', 'view', 'list', PRODUCTS, '-a', APP)
                     if v['name'] == name), None)
        info = C.view_info(PRODUCTS, APP, view['viewId']) if view else {}
        quick = [q['controlId'] for q in info.get('fastFilters') or []]
        if category['controlId'] not in quick:
            out.append(f'Products / {name}: no Category quick filter')
        if category['controlId'] in (info.get('showControls') or []):
            out.append(f'Products / {name}: Category is a column; §1 adds none')
    return out


def step_all():
    for name in ('create', 'fields', 'products', 'computed', 'layout', 'views', 'roles', 'seed'):
        print(f'\n── {name} ' + '─' * 60)
        STEPS[name]()
    print('\n── check ' + '─' * 60)
    return step_check()


def show():
    C.show(ws())


STEPS = {
    'create': step_create,
    'fields': step_fields,
    'products': step_products,
    'computed': step_computed,
    'layout': step_layout,
    'views': step_views,
    'roles': step_roles,
    'seed': step_seed,
    'all': step_all,
    'verify': step_verify,
    'check': step_check,
    'selfcheck': step_selfcheck,
    'order': step_order,
    'category': step_category,
    'untouched': step_untouched,
    'show': show,
}

if __name__ == '__main__':
    step = sys.argv[1] if len(sys.argv) > 1 else 'check'
    if step not in STEPS:
        raise SystemExit(f"Unknown step {step!r}; choose from {', '.join(STEPS)}")
    result = STEPS[step](*sys.argv[2:])
    if step in ('verify', 'check', 'all', 'selfcheck', 'roles') and result:
        sys.exit(1)
