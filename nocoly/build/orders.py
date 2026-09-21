#!/usr/bin/env python3
"""Business rules for the Orders worksheet (Odoo `sale.order`) in ERP Master, and the two narrow field saves the
owner approved — deliberately nothing else.

    ~/.hap-venv/bin/python nocoly/build/orders.py rules    # 1. the four interaction rules (upsert by name, and
                                                           #    only the ones whose live state differs)
    ~/.hap-venv/bin/python nocoly/build/orders.py retire   # 2. disable the hand-built rules those rules supersede
    ~/.hap-venv/bin/python nocoly/build/orders.py expiry   # 3. clear `required` on Expiration, one version-pinned save
    ~/.hap-venv/bin/python nocoly/build/orders.py totals   # 4. wire the three roll-ups over the Order Lines
                                                           #    subtable and repair its column list — one
                                                           #    version-pinned save
    ~/.hap-venv/bin/python nocoly/build/orders.py dots     # 5. two decimals on those three roll-ups, so a money
                                                           #    total draws 270.00 — one version-pinned save
    ~/.hap-venv/bin/python nocoly/build/orders.py controls # 6. Is Template and Template Name, appended
    ~/.hap-venv/bin/python nocoly/build/orders.py part1    # 6b. Part 1 of the button build: the four controls
                                                           #    four of Odoo's twenty Orders actions write —
                                                           #    Invoicing Closed, Signature, Signed By, Signed On
    ~/.hap-venv/bin/python nocoly/build/orders.py customer # 7. clear `required` on Customer, one pinned save
    ~/.hap-venv/bin/python nocoly/build/orders.py invstatus# 8. Invoicing Status stops being hidden, so it can be
                                                           #    a column and a quick filter — one pinned save
    ~/.hap-venv/bin/python nocoly/build/orders.py views    # 9. Templates, and the filters Quotations and Orders
                                                           #    were missing (All is never touched)
    ~/.hap-venv/bin/python nocoly/build/orders.py wipe     # 10. delete the three test orders the owner approved
    ~/.hap-venv/bin/python nocoly/build/orders.py seed     # 11. the tenant's twelve orders
    ~/.hap-venv/bin/python nocoly/build/orders.py figures  # 12. the three roll-ups beside the tenant's amounts
    ~/.hap-venv/bin/python nocoly/build/orders.py check    # read rules, Expiration, the roll-ups, the two new
                                                           #    controls, the view and the seed back, and
                                                           #    report drift
    ~/.hap-venv/bin/python nocoly/build/orders.py show     # the live controls and rules

**There is no `fields`, `layout` or `buttons` step, and there must not be one** — `views` writes one view of
its own and `seed` writes records, neither of which replaces a control.
The owner is building Orders **by hand in the browser** — on 21 Sep 2026 they added Delivery Date, Delivery
Status and Locked and six business rules between 11:51 and 12:23 while this script was being written, and then
rebuilt the worksheet from twelve controls to thirty-five. HAP has no per-field endpoint: a layout step is a
full `SaveWorksheetControls`, which replaces the whole control set and would revert whatever the owner had
typed since the read. `products.py` carries the same trap and the same warning in its `perms` docstring — its
`layout` step predates another administrator's changes and running it would undo them.

So every step here that touches a control is a **narrow, version-pinned save**: `common.controls_with_version`
then `common.save_controls(…, version=…)`, which refuses (code 10, 数据过时) if the owner saved in between,
followed by a signature diff proving the save changed only the controls that step names. `expiry`, `totals` and
`dots` are all that shape, and `products.py step_perms` is the pattern. Nothing here deletes anything.

Requirements: nocoly/worksheets/16-orders.md (§7.1 for what `totals` does). Order Lines, the child worksheet,
is `orderlines.py`'s — run its `fields` step before `totals`, so the columns the subtable names all exist.
Generic helpers: common.py.
"""
import json, os, sys

import common as C
import hap

APP = hap.ids()['app']
SECTION, WORKSHEET = 'Sales', 'Orders'
KEY = WORKSHEET + ': '                         # ids.json key prefix for everything this worksheet owns

# The worksheet is the owner's, not this script's, so its id is a constant here rather than something a `create`
# step minted. Read off the app on 21 Sep 2026; `guard` records it in ids.json and re-reads it from there after.
WS = '6ab09897e43d174ab3752d7b'


def ws():
    return hap.ids().get('worksheets', {}).get(WORKSHEET, WS)


# ── the controls this builder names ─────────────────────────────────────────
#
# Looked up by name at run time and checked against these ids: a control the owner replaces rather than edits
# gets a new id, and a rule that keeps the dead one is stored, published and silently does nothing
# (BUILDING.md — deleting a control does not take it out of the rules that name it).
CONTROLS = {                                   # name -> id, read off the app on 21 Sep 2026
    'Number': '6ab0a141805aef703286cf7f',
    'Customer': '6ab0a141805aef703286cf80',
    'Expiration': '6ab0a141805aef703286cf82',
    'Invoice Address': '6ab0a141805aef703286cf83',
    'Delivery Address': '6ab0a141805aef703286cf85',
    'Quotation/Order Date': '6ab0a425805aef703286cfdb',
    'Payment Terms': '6ab0a425805aef703286cfdc',
    # The **mounted** Order Lines subtable of the evening rebuild. It replaced the hidden `child_fields` child
    # table 6ab0a592e43d174ab3752fe5 that §6 could not read, which no longer exists — so the id this table
    # carried until 21 Sep 2026 is dead, and `guard` is what would have caught a rule still naming it.
    # Note that Orders carries **two** controls called *Order Lines*: the type-52 tab
    # (6ab0bfaf7d58b0f449316ad7) and this type-34 subtable. `common.fields` leaves tabs out, so a lookup by
    # name here is the subtable (BUILDING.md: a tab and a field can share a name).
    'Order Lines': '6ab0c740e43d174ab37535b0',
    'Status': '6ab0a847e54d2a34fa4e7b96',
    'Delivery Date': '6ab0a9dabd43f55762c78047',
    'Delivery Status': '6ab0a9dabd43f55762c78048',
    'Locked': '6ab0af4f805aef703286d570',
    # the evening rebuild's controls the rules and the roll-ups name
    'Tax Mode': '6ab0bfaf7d58b0f449316ad8',
    'Online Signature': '6ab0c23fe54d2a34fa4e8051',
    'Online Payment': '6ab0c324805aef703286d776',
    'Prepayment Percentage': '6ab0c324805aef703286d777',
    'Untaxed Amount': '6ab0c740e43d174ab37535b8',
    'Tax': '6ab0c740e43d174ab37535b9',
    'Total': '6ab0c740e43d174ab37535ba',
    # Odoo's `invoice_status`. The worksheet calls it *Invoice Status*; 16-orders.md and the Odoo menus call the
    # same thing Invoicing Status. §8 takes it out of hiding so it can be a column and a quick filter.
    'Invoice Status': '6ab0c5eae54d2a34fa4e8131',
}
EXPIRATION = 'Expiration'
DRIVERS = ('Status', 'Locked')                 # the two controls the three rules stand on

# Status' options (dataSource 8534fb85-9e1a-470c-99af-b5c485b2d534), read off the app on 21 Sep 2026. Odoo's
# `state`: draft · sent · sale, with cancel off the status bar.
STATUS_KEYS = {
    'Quotation': 'e43e8565-506a-47c9-9883-29aabeded2c0',              # draft
    'Quotation Sent': '9dee5df2-d1d3-4382-aa22-37fedeabcba0',         # sent
    'Sales Order': 'df9b6145-8288-489c-b823-e572fd22a5cb',            # sale
    'Cancelled': 'a3d06913-ae24-4a9e-8082-6994f2e18025',              # cancel
}


# ── 1 · the three rules ─────────────────────────────────────────────────────
#
# A rule applies its action while its condition holds and **the opposite when it fails** (BUILDING.md), so a
# *hide* rule shows its targets otherwise and a *read-only* rule makes them editable otherwise. Every rule here
# is therefore written `<action> · equals`, never `<opposite action> · not equals`: on a new order, whose Status
# is still empty and whose Locked is unticked, no condition holds, so every field is visible and editable — which
# is what Odoo's `invisible` and `readonly` do.

RULE_EXPIRATION = 'Expiration is for an unconfirmed quotation'
RULE_CONFIRMED = 'A confirmed or cancelled order is closed for editing'
RULE_LOCKED = 'A locked or cancelled order is closed for editing'
RULE_TAX_MODE = 'Tax Mode is fixed once the quotation is confirmed'
# The two the template flag brings with it (§6 below builds the controls they stand on).
RULE_CUSTOMER = 'A quotation needs a customer, a template does not'
RULE_TEMPLATE_NAME = 'Template Name is for templates'

# Odoo's `readonly="state in ['cancel','sale']"` covers eight fields on `sale.order`'s form. Three of them were
# on the worksheet when the rule was first built; the evening rebuild of 21 Sep 2026 added **Online Signature,
# Online Payment and Prepayment Percentage**, which join it here (16-orders.md §7.1 item 3).
#
# **Tax Mode is deliberately not among them.** Odoo's `readonly` on `document_tax_mode` is `state != 'draft'` —
# stricter, since it also covers *Quotation Sent* — and it gets RULE_TAX_MODE of its own. Two rules with
# different conditions acting on one control would fight: a rule applies its action while its condition holds
# and **the opposite when it fails**, so on a sent quotation this rule would make Tax Mode editable at the same
# moment the other made it read-only.
CONFIRMED_FIELDS = ('Customer', 'Expiration', 'Quotation/Order Date',
                    'Online Signature', 'Online Payment', 'Prepayment Percentage')
# Pricelist is the last of Odoo's eight still absent, deferred to its own bundle (16-orders.md §7.1 item 6).
CONFIRMED_MISSING = ('Pricelist',)

LOCKED_FIELDS = ('Invoice Address', 'Delivery Address', 'Delivery Date')
TAX_MODE_FIELDS = ('Tax Mode',)


def is_any_of(f, field, labels):
    """Condition: `field` is any of the labels — one filter carrying several option keys.

    A **business rule's** "is any of" on a single select is filterType **2**, not the 51 a view's or a button's
    condition uses (BUILDING.md; `C.EQ` is 2). HAP's own rule editor writes 51 for a single-option *equals* —
    three of the owner's hand-built rules on this worksheet carry it — so both shapes exist on Orders. 2 is what
    every rule this repo has built and proved in the UI carries, including Invoices' eight.
    """
    c = f[field]
    keys = [o['key'] for o in c['options'] if o['value'] in labels and not o.get('isDeleted')]
    if len(keys) != len(labels):
        sys.exit(f'{field}: options {labels} not all found among {[o["value"] for o in c["options"]]}')
    wanted = [STATUS_KEYS[l] for l in labels]
    if sorted(keys) != sorted(wanted):
        sys.exit(f'{field}: option keys for {labels} are {keys}, expected {wanted} — re-read the option table')
    return dict(C.cond(c, C.EQ), values=keys)


def is_ticked(f, field):
    """Condition: a checkbox (type 36) is ticked.

    `C.cond(c, C.EQ, 1)` stores **both** shapes seen in the app — `value` "1" (what HAP's own rule editor wrote
    for the owner's *Read-only when Locked*) and `values` ["1"] (what `taxes.py`'s picker work found, and what
    Products' live *Sales tab only for products that can be sold* carries with filterType 6). Neither is known to
    exclude the other, so the superset is sent; which one the browser actually reads is for the UI pass.
    """
    return C.cond(f[field], C.EQ, 1)


def either(*conds):
    """One filter group whose conditions are OR-ed, as HAP's own rule editor writes an OR.

    **HAP does express an OR across two different controls**, and the proof is on this worksheet: the owner's
    hand-built *Read-only when status is Cancelled or Locked* (6ab0b0f3…) holds one group carrying a Status
    condition and a Locked condition with **`spliceType` 2** on each. `spliceType` 1 is AND, 2 is OR, and the
    editor stamps the group's operator onto every condition in it — a lone condition therefore reads 1.
    `C.any_of` OR-s whole *groups* the same way; one group of OR-ed conditions is the shape the editor produces,
    so it is the shape used here.
    """
    return C.any_of([dict(c, spliceType=2) for c in conds])


def rule_specs(f):
    """The three rules as `upsert_rules` takes them: (name, type, filters, items, options)."""
    ctrl = lambda names: [f[n] for n in names]
    return [
        # <field name="validity_date" invisible="state == 'sale'"/>. `hide · equals`, so Expiration is visible on
        # a new quotation whose Status is still empty. It is also read-only from RULE_CONFIRMED while Status is
        # Cancelled, which Odoo does too — the two rules act on the same field and do not contradict each other.
        (RULE_EXPIRATION, C.INTERACTION, C.any_of([is_any_of(f, 'Status', ['Sales Order'])]),
         [C.item(C.HIDE, *ctrl([EXPIRATION]))], {}),
        # readonly="state in ['cancel','sale']" — Odoo's `sale.order` form, on eight fields; three exist here.
        (RULE_CONFIRMED, C.INTERACTION, C.any_of([is_any_of(f, 'Status', ['Sales Order', 'Cancelled'])]),
         [C.item(C.READONLY, *ctrl(CONFIRMED_FIELDS))], {}),
        # readonly="state == 'cancel' or locked" — the one rule on this worksheet that needs an OR across two
        # different controls. Odoo drives `locked` from its Lock / Unlock buttons; here it is an ordinary
        # editable checkbox and those buttons are not built (owner's decision, 21 Sep 2026 — 16-orders.md §3).
        (RULE_LOCKED, C.INTERACTION,
         either(is_ticked(f, 'Locked'), is_any_of(f, 'Status', ['Cancelled'])),
         [C.item(C.READONLY, *ctrl(LOCKED_FIELDS))], {}),
        # readonly="state != 'draft'" on `document_tax_mode` — the one field Odoo locks earlier than the rest.
        # Written `READONLY · is any of` the three non-draft statuses rather than `is not Quotation`, so that the
        # inverse leaves the field editable exactly where it should: on a new order whose Status is still empty,
        # and on a Quotation. That is the form every rule in this file takes, and the reason is in the comment
        # above RULE_EXPIRATION.
        (RULE_TAX_MODE, C.INTERACTION,
         C.any_of([is_any_of(f, 'Status', ['Quotation Sent', 'Sales Order', 'Cancelled'])]),
         [C.item(C.READONLY, *ctrl(TAX_MODE_FIELDS))], {}),
    ] + (template_rule_specs(f) if all(n in f for n in NEW) else [])


def template_rule_specs(f):
    """The two rules the template flag needs, as `upsert_rules` takes them.

    * *A quotation needs a customer, a template does not* — REQUIRE on Customer while **Is Template is not
      ticked**. The condition is `NE` (6) against "1", the operator the owner's own *Hide Delivery Status when
      Quotation is not Sales Order* already uses successfully on this worksheet. A rule applies its action
      while its condition holds and **the opposite when it fails**, so the inverse leaves Customer optional on
      a template — which is the whole point, and why `customer` had to take `required` off the control first: a
      rule cannot relax a field-level Required.
    * *Template Name is for templates* — two items on one rule, both conditioned on **Is Template is ticked**:
      SHOW it, and REQUIRE it. Two items rather than one rule each because a field a rule hides must not be
      required on the field itself (BUILDING.md), and the show half is what hides it on an ordinary quotation.
    """
    return [
        (RULE_CUSTOMER, C.INTERACTION, C.any_of([C.cond(f[IS_TEMPLATE], C.NE, 1)]),
         [C.item(C.REQUIRE, f[CUSTOMER])], {}),
        (RULE_TEMPLATE_NAME, C.INTERACTION, C.any_of([is_ticked(f, IS_TEMPLATE)]),
         [C.item(C.SHOW, f[TEMPLATE_NAME]), C.item(C.REQUIRE, f[TEMPLATE_NAME])], {}),
    ]


RULES = (RULE_EXPIRATION, RULE_CONFIRMED, RULE_LOCKED, RULE_TAX_MODE, RULE_CUSTOMER, RULE_TEMPLATE_NAME)


def step_rules():
    """The four interaction rules, upserted by name so a re-run updates rather than duplicates — and **only the
    ones whose live state differs from the spec**.

    The filter is what keeps the two rules this pass does not change byte-identical: `save-rule` re-sends a
    rule's whole payload, and a rule nobody is changing has no business being written at all. The comparison is
    the same one `check` makes."""
    f = guard()
    names = {c['controlId']: c['controlName'] for c in hap.controls(ws())}
    live = {r['name']: r for r in hap.listing('worksheet', 'rules', ws())}
    specs = [spec for spec in rule_specs(f) if rule_differs(spec, live.get(spec[0]), names)]
    if specs:
        C.upsert_rules(ws(), specs, 'orders_rules_pre_rules')
    else:
        print('  the four rules are already as specified; nothing saved')
    live = {r['name']: r for r in hap.listing('worksheet', 'rules', ws())}
    wanted = [spec[0] for spec in rule_specs(f)]
    for name in wanted:
        if name not in live:
            sys.exit(f'rule {name!r} did not come back from the worksheet')
        C.remember('rules', KEY + name, live[name]['ruleId'])
    if not all(n in f for n in NEW):
        print(f'  note: {list(NEW)} are not on the worksheet, so {RULE_CUSTOMER!r} and {RULE_TEMPLATE_NAME!r} '
              'were not built — run `controls` first')
    print(f'  {len(live)} rules on {WORKSHEET}; the {len(wanted)} above are this builder\'s '
          f'({[s[0] for s in specs]} written this run)')
    return bool(specs)


def rule_differs(spec, live, names):
    """True when the live rule is missing, disabled, or does not match the spec's condition and actions."""
    name, kind, filters, items, _opts = spec
    if live is None:
        return True
    return (kind, False, condition_state(filters, names), item_state(items, names)) != \
           (live['type'], live['disabled'], condition_state(live['filters'], names),
            item_state(live['ruleItems'], names))


def item_state(items, names):
    """A rule's actions as (type, sorted control names) — HAP returns the controls in its own order."""
    return [(i['type'], sorted(names.get(c['controlId'], c['controlId']) for c in i['controls']))
            for i in items]


# ── 2 · the hand-built rules these three supersede ──────────────────────────
#
# The owner hand-built six rules in the browser between 11:52 and 12:23 on 21 Sep 2026 — the three above, plus
# experiments — and then approved removing the ones the three replace (relayed 21 Sep 2026). **They are disabled,
# not deleted**: `disabled` is a flag on the rule and `save-rule --enabled` puts any of them straight back, while
# the CLI cannot delete a rule at all (BUILDING.md: disable it and delete it in the UI). Each is sent back in
# full — name, type, filters, ruleItems, checkType, hintType exactly as read — with only `disabled` flipped, so
# nothing about it is lost.
SUPERSEDED = {                                 # ruleId -> (its name, what it did, which of the three replaces it)
    '6ab0ad7ce43d174ab37532c2': (
        'Read-only when status is Sales Order or Cancelled',
        'Status is Sales Order or Cancelled -> read-only Customer, Expiration, Quotation/Order Date',
        RULE_CONFIRMED),                       # the same condition and the same three targets, filterType 2
    '6ab0aff8e54d2a34fa4e7dbb': (
        'Hide when status is Sales Order',
        'Status is Sales Order -> hide Expiration',
        RULE_EXPIRATION),                      # the same rule, written with filterType 51
    '6ab0b117e54d2a34fa4e7f0e': (
        'Read-only when Locked',
        'Locked is ticked -> read-only Invoice Address, Delivery Address, Delivery Date',
        RULE_LOCKED),                          # the Locked half of it; RULE_LOCKED adds Odoo's `state == cancel`
    '6ab0b0f3e43d174ab37533d2': (
        'Read-only when status is Cancelled or Locked',
        'Status is Cancelled or Locked is ticked -> read-only Delivery Date',
        RULE_LOCKED),                          # a subset: the same condition over one of the same three targets
    '6ab0afcebd43f55762c78212': (
        'Read-only when status is Sales Order',
        'Status is Sales Order or Locked is ticked -> read-only Invoice Address, Delivery Address',
        RULE_LOCKED),                          # see below — superseded **and** wrong against Odoo
}
# That last one is not only superseded. Its name says Sales Order and its filter says Sales Order **or** Locked,
# and Odoo's `readonly` on `partner_invoice_id` / `partner_shipping_id` is `state == 'cancel' or locked` — it says
# nothing about `sale`. So it froze both addresses on every plain confirmed order, which Odoo leaves editable, and
# it contradicted the owner's own *Read-only when Locked* on exactly those records (a rule reverses its action
# when its condition fails, so one made them read-only while the other made them editable).

KEPT = {                                       # left alone on purpose; `check` prints it every run
    '6ab0aa0fe43d174ab3753143': (
        'Hide Delivery Status when Quotation is not Sales Order',
        'Status is not Sales Order -> hide Delivery Status'),
}


def rule_payload(r):
    """The arguments that re-send a live rule unchanged."""
    return ['--name', r['name'], '--type', str(r['type']),
            '--check-type', str(r.get('checkType', 0)), '--hint-type', str(r.get('hintType', 0)),
            '--filters', json.dumps(r['filters'], ensure_ascii=False),
            '--rule-items', json.dumps(r['ruleItems'], ensure_ascii=False)]


def rule_state(r):
    """Everything about a rule but its `disabled` flag, for a before/after comparison."""
    return json.dumps({k: r.get(k) for k in ('name', 'type', 'checkType', 'hintType', 'filters', 'ruleItems')},
                      sort_keys=True, ensure_ascii=False)


def step_retire():
    """Disable the five hand-built rules the three above supersede, and leave every other rule alone."""
    guard()
    live = {r['ruleId']: r for r in hap.listing('worksheet', 'rules', ws())}
    mine = {r['name'] for r in live.values()} & {RULE_EXPIRATION, RULE_CONFIRMED, RULE_LOCKED}
    if len(mine) != 3:
        sys.exit(f'the three rules are not all live ({sorted(mine)}) — run `rules` before `retire`')
    hap.backup('orders_rules_pre_retire', list(live.values()))
    before, done = {}, []
    for rid, (name, does, replaced_by) in SUPERSEDED.items():
        r = live.get(rid)
        if r is None:
            print(f'  {rid} ({name}) is no longer on the worksheet — nothing to disable')
            continue
        if r['name'] != name:
            sys.exit(f'{rid} is named {r["name"]!r}, not {name!r} — the owner has rewritten it; stopping')
        if r['disabled']:
            print(f'  {rid} {name!r}: already disabled')
            continue
        before[rid] = rule_state(r)
        hap.run('worksheet', 'save-rule', ws(), '--rule-id', rid, '--disabled', *rule_payload(r))
        done.append((rid, name, does, replaced_by))
    back = {r['ruleId']: r for r in hap.listing('worksheet', 'rules', ws())}
    for rid, was in before.items():
        r = back.get(rid)
        if r is None:
            sys.exit(f'{rid} vanished from the worksheet — the disable deleted it')
        if not r['disabled']:
            sys.exit(f'{rid} ({r["name"]!r}) read back enabled — the disable did not store')
        if rule_state(r) != was:
            sys.exit(f'{rid} ({r["name"]!r}) changed as well as being disabled:\n  was {was}\n  now {rule_state(r)}')
    for rid, name, does, replaced_by in done:
        print(f'  disabled {rid}  {name!r}\n              was: {does}\n              now: {replaced_by!r}')
    for rid, (name, does) in KEPT.items():
        r = back.get(rid)
        print(f"  kept     {rid}  {name!r} ({'enabled' if r and not r['disabled'] else 'not live / disabled'})"
              f'\n              does: {does} — no rule of this builder touches Delivery Status')
    return bool(done)


# ── 3 · Expiration stops being required ─────────────────────────────────────
#
# Odoo does **not** require `sale.order.validity_date`, and RULE_EXPIRATION hides the field while Status is Sales
# Order. A field a rule hides must not be required on the field itself — it can never be filled and the form
# cannot be saved (BUILDING.md; Journals' Communication Type and Communication Standard had their Required taken
# off the control for exactly this reason on 16 Sep, 05-journals.md §3). Invoices' Auto-post is the one field in
# this app that is required and hidden by a rule, and only because it carries the default **No**, so it is always
# filled by the time the rule hides it. Expiration's default is a *function* — DATEADD(DATENOW(),"+1M",1) — which
# the form applies and the API does not, so an order created through the API would carry no Expiration at all.
#
# The owner approved clearing the flag (relayed 21 Sep 2026). **It is the only field write this builder makes.**
SIGNATURE = ('controlName', 'type', 'alias', 'row', 'col', 'size', 'sectionId', 'required', 'attribute', 'unique',
             'fieldPermission', 'dataSource', 'sourceControlId', 'sourceControlType', 'showControls', 'desc',
             'hint', 'enumDefault', 'enumDefault2', 'strDefault', 'dot', 'unit', 'options', 'default', 'viewId',
             'coverCid', 'noticeItem', 'half', 'defaultMen')
# `cardstyle` joins the list for the owner's *Sign & Acccept* control (type 49, a 查询按钮), whose
# `advancedSetting.cardstyle` is a JSON object in a string: BUILDING.md's rule is that the server re-serialises
# JSON-valued `advancedSetting` keys on save, so a byte comparison of one would report a change nobody made and
# stop a pinned save that had already gone through. Comparison only — nothing here writes it.
JSON_KEYS = ('filters', 'filterregex', 'controlssorts', 'customShowControls', 'defsource', 'defaultfunc',
             'uniquecontrols', 'rowsummary', 'cardstyle')


def defsource_state(value):
    """An `advancedSetting.defsource` in comparable form, because two kinds of default are stored in one form and
    saved in another, and a read-modify-write would otherwise report a change nobody made:

    * a **static Relation** default stores the whole related record, `utime` included, so it is reduced to the
      record's rowid — `accounts.defsource_state`, and what `common.save_controls` sends back;
    * a **member / department** default is returned long — `{"accountId": "user-self", "name": "Current user"}`
      on Orders' Salesperson — and only the bare sentinel `"user-self"` may be saved, which is the rewrite
      hap-cli's own `_normalize_defsource` makes on the way out. Both forms are reduced to the sentinel here so
      that they compare equal.
    """
    from hap_cli.core.worksheet import _DEFSOURCE_SENTINELS
    try:
        entries = json.loads(value) if value else []
    except (TypeError, ValueError):
        return value
    out = []
    for e in entries if isinstance(entries, list) else []:
        if not isinstance(e, dict):
            out.append(e)
            continue
        static = e.get('staticValue')
        if isinstance(static, str) and static.startswith('['):          # a Relation default: the record ids
            try:
                static = tuple((json.loads(x).get('rowid') if isinstance(x, str) and x.startswith('{') else x)
                               for x in json.loads(static))
            except (TypeError, ValueError, AttributeError):
                pass
        elif isinstance(static, str) and static.startswith('{'):        # a member default: the sentinel
            try:
                obj = json.loads(static)
                static = next((v for v in obj.values() if v in _DEFSOURCE_SENTINELS), static)
            except (TypeError, ValueError, AttributeError):
                pass
        out.append((e.get('cid') or '', e.get('rcid') or '', static, e.get('time') or ''))
    return out


def control_state(c):
    """A control's attributes, with its JSON-valued `advancedSetting` keys **parsed** rather than compared as
    strings — the server re-serialises several of them on every read (BUILDING.md; `accounts.control_state`).

    A 子表's `relationControls` is the child worksheet's whole control snapshot, which the server also reshuffles,
    so it is reduced to the child controls' identity rather than compared byte for byte."""
    out = {k: c.get(k) for k in SIGNATURE}
    settings = dict(c.get('advancedSetting') or {})
    for key, value in settings.items():
        if key == 'defsource':
            settings[key] = defsource_state(value)
        elif key in JSON_KEYS and isinstance(value, str) and value:
            try:
                settings[key] = json.loads(value)
            except ValueError:
                pass
    out['advancedSetting'] = settings
    out['relationControls'] = sorted((r.get('controlId'), r.get('controlName'), r.get('type'), r.get('required'))
                                     for r in (c.get('relationControls') or []))
    return out


def signature(ctrls):
    return {c['controlId']: json.dumps(control_state(c), sort_keys=True, ensure_ascii=False) for c in ctrls}


def step_expiry():
    """Clear `required` on Expiration in one version-pinned save that changes nothing else.

    HAP has no per-field endpoint — hap-cli's own `field update` goes through `save_controls` too — so this is a
    full `SaveWorksheetControls` of the list just read, with one boolean flipped. `version` pins the optimistic
    lock: an edit the owner makes between the read and the save refuses this one (code 10, 数据过时) instead of
    being overwritten, which matters here because they are working in the browser at the same time."""
    f = guard()
    if not f[EXPIRATION].get('required'):
        print(f'  {EXPIRATION} is already not required; nothing saved')
        return False
    ctrls, version = C.controls_with_version(ws())
    hap.backup('orders_controls_pre_expiry', ctrls)
    target = next((c for c in ctrls if c['controlId'] == CONTROLS[EXPIRATION]), None)
    if target is None or target['controlName'] != EXPIRATION:
        sys.exit(f'{CONTROLS[EXPIRATION]} is not {EXPIRATION} in the control list — stopping')
    before = signature(ctrls)
    target['required'] = False
    C.save_controls(ws(), ctrls, version=version)
    after = signature(hap.controls(ws()))
    changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    if changed != [CONTROLS[EXPIRATION]]:
        names = {c['controlId']: c['controlName'] for c in hap.controls(ws())}
        sys.exit(f'the save changed {[names.get(k, k) for k in changed]}, wanted only {EXPIRATION}\n' +
                 '\n'.join(f'  {names.get(k, k)}\n    was {before.get(k)}\n    now {after.get(k)}' for k in changed))
    live = {c['controlName']: c for c in hap.controls(ws())}
    if live[EXPIRATION].get('required'):
        sys.exit(f'{EXPIRATION} read back required — the save did not store')
    print(f'  {EXPIRATION} ({CONTROLS[EXPIRATION]}): required True -> False; '
          f'{len(before)} controls compared, no other change')
    return True


# ── 4 · the three roll-ups, and the subtable's columns ──────────────────────
#
# 16-orders.md §7.1 items 1 and the column half of it. Both changes are on controls the owner built and neither
# can be made any other way, so they go in **one** version-pinned save whose signature diff must name exactly
# the four controls below.

ORDER_LINES = 'Order Lines'                    # the mounted 子表 on Orders (type 34)
LINES_WS = '6ab0c740e43d174ab37535b2'          # the child worksheet — orderlines.py's
SUBLIST, ROLLUP = 34, 37
SUM = 5                                        # 汇总 enumDefault: 1 avg · 2 max · 3 min · 5 sum · 6 count
EQ_SINGLE = 51                                 # a 汇总's own filter: the *view* editor's "is" (BUILDING.md)
INVLINES_WS = '6aaa2b50e54d2a34fa4e0221'       # Invoice Lines — the shape both halves of this step copy

# The child controls each roll-up sums, read off Order Lines on 21 Sep 2026. `orderlines.py` owns them; they are
# named here because a 汇总's `sourceControlId` is a control id on the *other* worksheet and nothing else can
# express it.
CHILD = {
    'Display Type': '6ab0c864e43d174ab37535f7',
    'Sequence': '6ab0c740e43d174ab37535b7',
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
}
PRODUCT_LINE = '1d0faacc-2a0f-490d-b339-d077c034bc62'      # Display Type / Product, the owner's own option key

# Odoo's `amount_untaxed`, `amount_tax` and `amount_total` sum `order_line`; a section, a subsection and a note
# are not order lines. The filter matters more here than the equivalent does on an invoice, because a HAP
# section **keeps whatever figures were typed into it** before its Display Type was changed — the line-level
# rule only hides them.
ROLLUPS = {                                    # name -> the child control it sums
    'Untaxed Amount': 'Subtotal',
    'Tax': 'Tax Amount',
    'Total': 'Total',
}
# What the grid inside an order shows, in Odoo's own column order — the convention is Invoices' *Lines*
# subtable (6aaa2baae43d174ab3749de9). The parent relation is left out, as Invoice's is; so are the two hidden
# controls (Tax rate, Product Unit) and the two optional ones orderlines.py appends (Lead Time, Optional Line),
# which the owner can add by hand.
SUBTABLE_COLUMNS = ('Sequence', 'Display Type', 'Product', 'Description', 'Quantity', 'Quantity Delivered',
                    'Quantity Invoiced', 'Unit', 'Unit Price', 'Taxes', 'Discount', 'Tax Amount', 'Subtotal',
                    'Total')
# The dead id the subtable was carrying: `showControls` and `advancedSetting.controlssorts` both named
# 6ab0c740e43d174ab37535b6, a control that is not on Order Lines any more, so the grid drew one *Sequence*
# column and none of the line fields. Nothing cleans a dead id out of a column list (BUILDING.md says the same
# of a view's sort and a rule's controls) — it is dropped by rewriting the list.
DEAD_COLUMN = '6ab0c740e43d174ab37535b6'


def product_lines_filter():
    """The roll-ups' own filter: Display Type **is Product**.

    A 汇总's `advancedSetting.filters` is the **view** editor's enum, where a single select's "is" is `filterType`
    **51** — not the 2 a business rule uses. Proved on a Dropdown of a related worksheet by Invoice Lines' *Tax
    rate*, and on the single select of a mounted 子表 by Payment Terms' *Percent total* (BUILDING.md)."""
    return [{'controlId': CHILD['Display Type'], 'dataType': 11, 'spliceType': 1, 'filterType': EQ_SINGLE,
             'dateRange': 0, 'dateRangeType': 0, 'value': '', 'values': [PRODUCT_LINE], 'minValue': '',
             'maxValue': '', 'isAsc': False, 'dynamicSource': [], 'advancedSetting': None, 'isGroup': False,
             'groupFilters': None, 'emptyRule': 0}]


def check_filter_shape():
    """Cross-check `product_lines_filter` against Invoice Lines' *Tax rate*, the one 汇总 filter in this app that
    is proved to compute, so the two cannot drift into different shapes."""
    c = next((c for c in hap.controls(INVLINES_WS) if c['controlName'] == 'Tax rate'), None)
    if c is None or c['type'] != ROLLUP:
        sys.exit('Invoice Lines has no Tax rate 汇总 to compare the filter shape with')
    try:
        live = json.loads((c.get('advancedSetting') or {}).get('filters') or '[]')
    except ValueError:
        sys.exit('Invoice Lines / Tax rate: advancedSetting.filters is not JSON')
    mine = product_lines_filter()
    if len(live) != 1 or set(live[0]) != set(mine[0]) or \
            [live[0][k] for k in ('dataType', 'spliceType', 'filterType')] != \
            [mine[0][k] for k in ('dataType', 'spliceType', 'filterType')]:
        sys.exit(f'the 汇总 filter shape has drifted from Invoice Lines / Tax rate:\n'
                 f'  theirs {json.dumps(live, ensure_ascii=False)}\n  mine   {json.dumps(mine, ensure_ascii=False)}')
    print(f"  reference: Invoice Lines / Tax rate {c['controlId']} — same filter shape, filterType {EQ_SINGLE}")


def totals_spec():
    """{control id: {key: value}} — everything the `totals` step writes, and nothing else.

    `fieldPermission` is left as the owner set it: this step wires the aggregation and repairs the column list, and
    does not restyle a control they built. `dot` was left alone here too and is `step_dots`' now — it is the one
    thing about these three that had to change for a money total to read as money."""
    columns = [CHILD[n] for n in SUBTABLE_COLUMNS]
    spec = {CONTROLS[ORDER_LINES]: {'showControls': columns,
                                    'advancedSetting.controlssorts': json.dumps(columns, ensure_ascii=False)}}
    for name, child in ROLLUPS.items():
        spec[CONTROLS[name]] = {'dataSource': f'${CONTROLS[ORDER_LINES]}$',
                                'sourceControlId': CHILD[child],
                                'enumDefault': SUM,
                                'advancedSetting.filters': json.dumps(product_lines_filter(), ensure_ascii=False)}
    return spec


def parsed(key, value):
    if key in JSON_KEYS and isinstance(value, str) and value:
        try:
            return json.loads(value)
        except ValueError:
            pass
    return value


def value_of(c, key):
    """A control's value for a plain key or an `advancedSetting.<key>`, JSON-valued keys parsed."""
    if key.startswith('advancedSetting.'):
        key = key.split('.', 1)[1]
        return parsed(key, (c.get('advancedSetting') or {}).get(key))
    return parsed(key, c.get(key))


def set_value(c, key, value):
    if key.startswith('advancedSetting.'):
        c['advancedSetting'] = {**(c.get('advancedSetting') or {}), key.split('.', 1)[1]: value}
    else:
        c[key] = value


def drift(c, spec):
    """{key: (got, want)} for every key of `spec` the control does not already carry."""
    return {k: (value_of(c, k), parsed(k.split('.')[-1], v)) for k, v in spec.items()
            if value_of(c, k) != parsed(k.split('.')[-1], v)}


def pinned_write(step, spec, backup):
    """Write `spec` — {control id: {key: value}} — in **one** version-pinned `SaveWorksheetControls` of the whole
    control list, with a signature diff proving the save changed only the controls `spec` names, and a read-back.
    Returns True when it saved and False when there was nothing to write.

    `version` pins HAP's optimistic lock: a control save the owner makes between the read and the save refuses this
    one (code 10, 数据过时) instead of being overwritten, which is the whole point on a worksheet they are
    hand-building in the browser. `products.py step_perms` is the pattern, and `step_expiry` is the same shape
    written out longhand for one boolean. Every key of every control `spec` does not name goes back exactly as it
    was read."""
    by_id = {c['controlId']: c for c in hap.controls(ws())}
    names = {cid: by_id[cid]['controlName'] for cid in spec}
    stale = {cid: drift(by_id[cid], spec[cid]) for cid in spec if drift(by_id[cid], spec[cid])}
    for cid, diff in stale.items():
        for k, (got, want) in diff.items():
            print(f'  {names[cid]}.{k}:\n      was {got!r}\n      now {want!r}')
    if not stale:
        print(f'  {step}: {sorted(names.values())} are already as specified; nothing saved')
        return False
    ctrls, version = C.controls_with_version(ws())
    hap.backup(backup, ctrls)
    before = signature(ctrls)
    for c in ctrls:
        if c['controlId'] in stale:
            for key in stale[c['controlId']]:
                set_value(c, key, spec[c['controlId']][key])
    C.save_controls(ws(), ctrls, version=version)
    live = hap.controls(ws())
    after = signature(live)
    changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    live_names = {c['controlId']: c['controlName'] for c in live}
    if changed != sorted(stale):
        sys.exit(f'{step}: the save changed {[live_names.get(k, k) for k in changed]}, wanted only '
                 f'{[live_names.get(k, k) for k in sorted(stale)]}\n' +
                 '\n'.join(f'  {live_names.get(k, k)}\n    was {before.get(k)}\n    now {after.get(k)}'
                           for k in changed))
    by_id = {c['controlId']: c for c in live}
    left = {live_names[cid]: drift(by_id[cid], spec[cid]) for cid in spec if drift(by_id[cid], spec[cid])}
    if left:
        sys.exit(f'{step} read back with differences: {json.dumps(left, ensure_ascii=False, default=str)}')
    print(f'  {step}: {sorted(names[cid] for cid in stale)} written — {len(before)} controls compared, '
          f'no other change')
    return True


def step_totals():
    """Wire the three roll-ups over the Order Lines subtable and rewrite the subtable's column list, in one
    version-pinned save that changes those four controls and nothing else.

    The roll-ups were built by hand as 汇总 (type 37) with `dataSource` and `sourceControlId` empty and
    `enumDefault` **6**, which is *count*: all three aggregated nothing at all. The working shape is Invoice
    Lines' *Tax rate* — `dataSource` the `$…$`-wrapped bridge control, `sourceControlId` a control on the
    bridge's target worksheet, and a filter in the view editor's enum.

    Run **after** `orderlines.py fields`: the column list names only controls the owner built, but the step is
    cheaper to reason about when the child worksheet is already final."""
    f = guard()
    check_filter_shape()
    sub = f[ORDER_LINES]
    if sub['type'] != SUBLIST or sub.get('dataSource') != LINES_WS:
        sys.exit(f'{ORDER_LINES} {sub["controlId"]} is t{sub["type"]} ds={sub.get("dataSource")!r}, expected a '
                 f'mounted 子表 (t{SUBLIST}) over {LINES_WS}')
    live_child = {c['controlId']: c['controlName'] for c in hap.controls(LINES_WS)}
    missing = {n: cid for n, cid in CHILD.items() if live_child.get(cid) != n}
    if missing:
        sys.exit(f'Order Lines does not carry {missing} under those ids — re-read the child worksheet')
    if DEAD_COLUMN in live_child:
        sys.exit(f'{DEAD_COLUMN} is a live control on Order Lines after all ({live_child[DEAD_COLUMN]!r}) — '
                 'do not drop it from the column list')
    for name in ROLLUPS:
        c = f[name]
        if c['type'] != ROLLUP:
            sys.exit(f'{name} {c["controlId"]} is t{c["type"]}, expected a 汇总 (t{ROLLUP})')
    if not pinned_write('totals', totals_spec(), 'orders_controls_pre_totals'):
        return False
    for name in list(ROLLUPS) + [ORDER_LINES]:
        C.remember('controls', KEY + name, CONTROLS[name])
    print(f'  columns: {list(SUBTABLE_COLUMNS)}')
    return True


# ── 5 · the roll-ups draw money ─────────────────────────────────────────────
#
# All three were hand-built with `dot` **0**, so an order's Untaxed Amount drew `270` where every other money
# figure in the app draws `270.00` — Order Lines' own Subtotal, Tax Amount and Total all carry 2, and so do Invoice
# Lines'. `dot` is the only thing this step writes: not `fieldPermission`, not the unit, not the aggregation
# `totals` wired.
MONEY_DOT = 2


def dots_spec():
    """{control id: {'dot': 2}} for the three roll-ups — everything the `dots` step writes."""
    return {CONTROLS[name]: {'dot': MONEY_DOT} for name in ROLLUPS}


def step_dots():
    """Two decimals on Untaxed Amount, Tax and Total, in one version-pinned save that changes those three
    controls and nothing else.

    **A figure a roll-up has already aggregated keeps the rounding it was aggregated with.** The recompute HAP
    runs when a definition changes treats each record on its own and can leave rows stale (BUILDING.md), and it
    rounds to the 汇总's `dot` of the moment: the one TEST order's Tax read `8.00` after `orderlines.py formulas`
    made the line compute 8.10, because this step had not run yet. Re-saving the order or its line refreshes it.
    So run `dots` **before** the child's figures change, or expect the first order to need one more save."""
    f = guard()
    for name in ROLLUPS:
        if f[name]['type'] != ROLLUP:
            sys.exit(f'{name} {f[name]["controlId"]} is t{f[name]["type"]}, expected a 汇总 (t{ROLLUP})')
    return pinned_write('dots', dots_spec(), 'orders_controls_pre_dots')


# ── 6 · Is Template and Template Name ───────────────────────────────────────
#
# **Neither is an Odoo field.** `sale.order` has no `is_template` and no `template_name`: Odoo keeps a quotation
# template in a model of its own, `sale.order.template`, and this app instead marks an *order* as the thing to
# recreate from (the owner's decision, relayed 21 Sep 2026). Both are this app's own invention and their `desc`
# says so.
#
# They are **appended** with `common.append_controls` — `AddWorksheetControls` with no client-side id, so the
# server mints real ones and not one of the owner's thirty-five controls is re-sent. `add-fields` parks a new
# control at row 9999 col 0 whatever the payload carries, and only a full save places one, which this builder
# must not make (see the module docstring) — so `NEW_PLACE` is the intent recorded for the owner, not what will
# read back: they will find both at the foot of the form and place them in the designer.
IS_TEMPLATE, TEMPLATE_NAME = 'Is Template', 'Template Name'
NEW = (IS_TEMPLATE, TEMPLATE_NAME)
CHECKBOX, TEXT = 36, 2
NEW_TYPE = {IS_TEMPLATE: CHECKBOX, TEMPLATE_NAME: TEXT}
NEW_PLACE = {IS_TEMPLATE: (23, 0, 6), TEMPLATE_NAME: (23, 1, 6)}
NEW_ALIAS = {IS_TEMPLATE: 'is_template', TEMPLATE_NAME: 'template_name'}
NEW_DESC = {
    IS_TEMPLATE: 'A template is a quotation kept to be recreated from, not sent to a customer. Use the record '
                 "menu's Recreate to start a real quotation from it — Recreate copies the order lines, Copy "
                 'does not. Not an Odoo field: `sale.order` has no `is_template`.',
    TEMPLATE_NAME: 'What this template is called in the Templates view. Not an Odoo field: `sale.order` has no '
                   '`template_name`.',
}


def new_controls():
    """The two controls, as `append_controls` takes them (its own copy drops the `controlId`).

    `showtype` "1" is what the owner's own three checkboxes on this worksheet carry (Locked, Online Payment,
    Online Signature); hap-cli's SWITCH template defaults to "0", which would draw this one differently from
    its three neighbours."""
    return {
        IS_TEMPLATE: C.control('SWITCH', IS_TEMPLATE, NEW_PLACE[IS_TEMPLATE], alias=NEW_ALIAS[IS_TEMPLATE],
                               hint='', desc=NEW_DESC[IS_TEMPLATE],
                               advanced_setting={'showtype': '1', 'itemnames': '', 'sorttype': 'zh'}),
        TEMPLATE_NAME: C.control('TEXT', TEMPLATE_NAME, NEW_PLACE[TEMPLATE_NAME], alias=NEW_ALIAS[TEMPLATE_NAME],
                                 hint='', desc=NEW_DESC[TEMPLATE_NAME]),
    }


def new_spec():
    """What each appended control must read back as. `fieldPermission` is deliberately left as the append
    leaves it (`""`): `add-fields` stores it empty and only a save that sends `"111"` writes the platform
    default (BUILDING.md), and `""` is what most of the owner's own controls on this worksheet read."""
    return {
        IS_TEMPLATE: {'type': CHECKBOX, 'alias': NEW_ALIAS[IS_TEMPLATE], 'desc': NEW_DESC[IS_TEMPLATE],
                      'required': False,
                      'advancedSetting.defsource': C.static_default(0),
                      'advancedSetting.showtype': '1'},
        TEMPLATE_NAME: {'type': TEXT, 'alias': NEW_ALIAS[TEMPLATE_NAME], 'desc': NEW_DESC[TEMPLATE_NAME],
                        'required': False, 'enumDefault': 2},
    }


def step_controls():
    """Append Is Template and Template Name, then check the append stored everything and repair what it did not
    in one version-pinned save limited to the two ids just minted.

    Not `C.add_fields`: that appends and then re-saves the whole control set, which is exactly the clobber this
    builder exists to avoid on a worksheet the owner is hand-building. The pattern is
    `orderlines.py step_fields`."""
    f = guard()
    missing = [n for n in NEW if n not in f]
    if missing:
        hap.backup('orders_controls_pre_controls', hap.controls(ws()))
        built = new_controls()
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
    spec = new_spec()
    stale = {n: drift(f[n], spec[n]) for n in NEW if drift(f[n], spec[n])}
    if stale:
        print('  the append did not store everything; repairing in one pinned save:')
        for n, diff in stale.items():
            for k, (got, want) in diff.items():
                print(f'    {n}.{k}: {got!r} -> {want!r}')
        if not pinned_write('controls', {f[n]['controlId']: {k: spec[n][k] for k in stale[n]} for n in stale},
                            'orders_controls_pre_controls_repair'):
            sys.exit('the repair found nothing to write, which contradicts the drift above')
        f = C.fields(ws())
        left = {n: drift(f[n], spec[n]) for n in NEW if drift(f[n], spec[n])}
        if left:
            sys.exit(f'{WORKSHEET}: read back with differences {json.dumps(left, ensure_ascii=False)}')
    for n in NEW:
        C.remember('controls', KEY + n, f[n]['controlId'])
        c = f[n]
        print(f"  {n:<14} {c['controlId']} t{c['type']:<3} alias={c.get('alias') or '-':<14} "
              f"perm={c.get('fieldPermission') or '-':<4} r{c.get('row')}c{c.get('col')}")
    return True


# ── 6b · the four controls the Orders buttons write ─────────────────────────
#
# **Part 1 of the Orders button build** — 16-orders.md's twenty Orders actions. Not one of these four is a
# button, and they go first because **four of Odoo's twenty actions are nothing but a write to them** and cannot
# be built until they exist:
#
#   * *Close Invoicing* and *Reopen Invoicing* are **only** a write and a clear of Invoicing Closed;
#   * *Sign & Accept* writes the three signature fields, and *Set to Quotation* clears them.
#
# Odoo's own field metadata, read off casimir on 21 Sep 2026 — `invoicing_closed` boolean · `signature` binary ·
# `signed_by` char · `signed_on` datetime, all four **stored**. `SIGNATURE` is control type **42** in hap-cli's
# own `FIELD_TYPES`; an Attachment (14) is **not** a substitute — HAP draws a signature pad for 42 and a file
# picker for 14, and the customer signing on a shared page draws rather than uploads.
#
# **Naming.** The control is *Invoicing Closed*, not Odoo's own label *Manually Closed For Invoicing*, and that
# divergence is deliberate: the label is never shown on Odoo's own form — the field appears only inside the
# Reopen button's `invisible` condition — and the short name matches the two buttons that drive it. Odoo's label
# is recorded in the control's `desc` so the divergence stays traceable from the app itself.
#
# **Permissions.** All four carry `fieldPermission` **"100"** — read-only and hidden on create, which is
# **Status**' own permission and for the same reason: a button or a workflow writes them and nobody types them.
# The step asserts Status still reads "100" before copying it. It does not stop the buttons: **an API write
# ignores field permission** (Prepayment Percentage is "011", hidden, and seeded fine on 21 Sep), and a
# workflow's write is not the form's either.
#
# Appended with `common.append_controls`, as §6 is and for the same reason — `AddWorksheetControls` with no
# client-side id, so the server mints real ids and not one of the owner's controls is re-sent. `C.add_fields`
# would follow the append with an **unpinned full re-save**, the clobber this builder exists to avoid.
#
# **Placement is the owner's.** `add-fields` parks a new control at **row 9999, col 0** whatever `row` and `col`
# the payload carries, and only a full `SaveWorksheetControls` places one — which this builder must never make.
# `size` *is* kept, so the widths below are real; `PART1_PLACE`'s rows and columns are the intent recorded for
# the owner, exactly as `NEW_PLACE` is for Is Template and Template Name. No `sectionId` is sent either, so all
# four land in the form's main body rather than in a tab; if the owner would rather have the signature trio sit
# under *Other Info › Confirmation* beside Online Signature, that is a placement decision and theirs to make in
# the designer.
INVOICING_CLOSED = 'Invoicing Closed'
# **Not `SIGNATURE`** — that name is this module's signature-diff key tuple, and a module-level constant defined
# later silently replaces an earlier one of the same name. It is the hazard §8 hit with `INVOICE_STATUS` and
# `orderlines.FIGURES`, and here it would have quietly broken every `signature()` call in the file.
SIGNATURE_FIELD = 'Signature'
SIGNED_BY, SIGNED_ON = 'Signed By', 'Signed On'
PART1 = (INVOICING_CLOSED, SIGNATURE_FIELD, SIGNED_BY, SIGNED_ON)
SIGN_PAD, DATE_TIME = 42, 16                   # hap-cli's FIELD_TYPES: SIGNATURE 42 · DATE_TIME 16
ODOO_INVOICING_CLOSED_LABEL = 'Manually Closed For Invoicing'
PART1_TYPE = {INVOICING_CLOSED: CHECKBOX, SIGNATURE_FIELD: SIGN_PAD, SIGNED_BY: TEXT, SIGNED_ON: DATE_TIME}
PART1_ALIAS = {INVOICING_CLOSED: 'invoicing_closed', SIGNATURE_FIELD: 'signature',
               SIGNED_BY: 'signed_by', SIGNED_ON: 'signed_on'}
PART1_PLACE = {INVOICING_CLOSED: (24, 0, 6),   # (row, col, size) — only `size` survives the append
               SIGNATURE_FIELD: (25, 0, 12),   # a signature pad wants the full width
               SIGNED_BY: (26, 0, 6), SIGNED_ON: (26, 1, 6)}
# Each type's own neighbours on this worksheet decide the placeholder: the three checkboxes all carry "", and
# both datetimes carry HAP's own "Please select date". A read-only control never shows a placeholder anyway, so
# this is consistency rather than behaviour — and the spec below deliberately does **not** assert it, as §6 does
# not, so a server-side normalisation cannot put the step into a repair loop.
PART1_HINT = {INVOICING_CLOSED: '', SIGNATURE_FIELD: '', SIGNED_BY: '', SIGNED_ON: 'Please select date'}
PART1_DESC = {
    INVOICING_CLOSED: 'Stop asking for this order to be invoiced, without cancelling it. Written by the Close '
                      'Invoicing button and cleared by Reopen Invoicing — never typed, which is why it is '
                      'read-only and hidden on create. Odoo calls the same field "'
                      + ODOO_INVOICING_CLOSED_LABEL + '"; the shorter name here matches the two buttons that '
                      'drive it.',
    SIGNATURE_FIELD: 'The signature the customer drew when they accepted this quotation on a shared page. '
                     'Written by Sign & Accept and cleared by Set to Quotation — never typed, which is why it '
                     'is read-only and hidden on create. The Online Signature checkbox is only a request for a '
                     'signature and stores nothing; this is where the signature itself lands.',
    SIGNED_BY: 'The name the customer gave when they accepted this quotation on a shared page. Written by Sign '
               '& Accept and cleared by Set to Quotation — never typed, which is why it is read-only and hidden '
               'on create. Online Signature is only the request; this is who signed.',
    SIGNED_ON: 'When the customer accepted this quotation on a shared page. Written by Sign & Accept and '
               'cleared by Set to Quotation — never typed, which is why it is read-only and hidden on create. '
               'Online Signature is only the request; this is when the signature arrived.',
}


def part1_controls():
    """The four controls, as `append_controls` takes them (its own copy drops the `controlId`).

    `showtype` "1" on the checkbox is what the owner's own three checkboxes on this worksheet carry (Locked,
    Online Payment, Online Signature) and what §6 gave Is Template; hap-cli's SWITCH template defaults to "0",
    which would draw this one differently from its four neighbours. The datetime's `showtype` "1" is hap-cli's
    own template default and is what Quotation/Order Date and Delivery Date both read."""
    def built(name, kind, **kw):
        return C.control(kind, name, PART1_PLACE[name], alias=PART1_ALIAS[name], hint=PART1_HINT[name],
                         desc=PART1_DESC[name], extra={'fieldPermission': READ_ONLY_PERMISSION}, **kw)
    return {
        INVOICING_CLOSED: built(INVOICING_CLOSED, 'SWITCH',
                                advanced_setting={'showtype': '1', 'itemnames': '', 'sorttype': 'zh'}),
        SIGNATURE_FIELD: built(SIGNATURE_FIELD, 'SIGNATURE'),
        SIGNED_BY: built(SIGNED_BY, 'TEXT'),
        SIGNED_ON: built(SIGNED_ON, 'DATE_TIME', advanced_setting={'showtype': '1'}),
    }


def part1_spec():
    """What each appended control must read back as — {name: {key: value}}, in `drift`'s form.

    Unlike §6's `new_spec` this **does** pin `fieldPermission`: "" is not an acceptable resting state for a
    control four buttons write and nobody may type. BUILDING.md records that `add-fields` stores a new control's
    permission as "" whatever the payload carried, so the append is expected to leave all four wrong and
    `step_part1`'s one pinned save is expected to fix them — which is why the spec, not the payload, is what the
    step verifies against.

    The server fills `allowtime`, `showformat`, `sorttype`, `analysislink`, `max` and `min` in on its own, so
    none of them is asserted; nor is `hint` (see `PART1_HINT`)."""
    spec = {n: {'type': PART1_TYPE[n], 'alias': PART1_ALIAS[n], 'desc': PART1_DESC[n], 'required': False,
                'fieldPermission': READ_ONLY_PERMISSION} for n in PART1}
    spec[INVOICING_CLOSED]['advancedSetting.defsource'] = C.static_default(0)   # a new order is not closed
    spec[INVOICING_CLOSED]['advancedSetting.showtype'] = '1'
    spec[SIGNED_BY]['enumDefault'] = 2                                         # a single-line text
    spec[SIGNED_ON]['advancedSetting.showtype'] = '1'
    return spec


def step_part1():
    """Append Invoicing Closed, Signature, Signed By and Signed On, then check the append stored everything and
    repair what it did not in one version-pinned save limited to the four ids just minted.

    Not `C.add_fields`: that appends and then re-saves the whole control set **unpinned**, which is exactly the
    clobber this builder exists to avoid on a worksheet the owner is hand-building. `step_controls` is the
    pattern, and nothing here deletes anything or touches Order Lines."""
    f = guard()
    status_perm = f['Status'].get('fieldPermission')
    if status_perm != READ_ONLY_PERMISSION:
        sys.exit(f'Status carries fieldPermission {status_perm!r}, not {READ_ONLY_PERMISSION!r} — it is the '
                 f'permission these four copy, and the reason for copying it; re-read the worksheet')
    print(f'  Status reads fieldPermission {status_perm!r}; all four copy it')
    missing = [n for n in PART1 if n not in f]
    if missing:
        hap.backup('orders_controls_pre_part1', hap.controls(ws()))
        b = part1_controls()
        C.append_controls(ws(), [b[n] for n in missing])
        f = C.fields(ws())
        gone = [n for n in missing if n not in f]
        if gone:
            sys.exit(f'{gone} did not come back from the worksheet — the append did not store')
        for n in missing:
            print(f"  added {n}: {f[n]['controlId']} (t{f[n]['type']}, row {f[n].get('row')} col "
                  f"{f[n].get('col')} size {f[n].get('size')} — `add-fields` parks a new control at row 9999, "
                  f'and only a full save places one)')
    else:
        print(f'  {list(PART1)} are already on {WORKSHEET}; nothing appended')
    spec = part1_spec()
    stale = {n: drift(f[n], spec[n]) for n in PART1 if drift(f[n], spec[n])}
    if stale:
        print('  the append did not store everything; repairing in one version-pinned save:')
        for n, diffs in stale.items():
            for k, (got, want) in diffs.items():
                print(f'    {n}.{k}: {got!r} -> {want!r}')
        if not pinned_write('part1', {f[n]['controlId']: {k: spec[n][k] for k in stale[n]} for n in stale},
                            'orders_controls_pre_part1_repair'):
            sys.exit('the repair found nothing to write, which contradicts the drift above')
        f = C.fields(ws())
        left = {n: drift(f[n], spec[n]) for n in PART1 if drift(f[n], spec[n])}
        if left:
            sys.exit(f'{WORKSHEET}: read back with differences '
                     f'{json.dumps(left, ensure_ascii=False, default=str)}')
    for n in PART1:
        C.remember('controls', KEY + n, f[n]['controlId'])
        c = f[n]
        print(f"  {n:<17} {c['controlId']} t{c['type']:<3} alias={c.get('alias') or '-':<17} "
              f"perm={c.get('fieldPermission') or '-':<4} r{c.get('row')}c{c.get('col')} s{c.get('size'):<3} "
              f"hint={c.get('hint')!r} desc={len(c.get('desc') or '')} chars")
    print(f'  Odoo\'s own label for {INVOICING_CLOSED} is {ODOO_INVOICING_CLOSED_LABEL!r}, recorded in its desc')
    print('  placement outstanding — the owner places all four in the designer; intended (row, col, size): '
          + ', '.join(f'{n} {PART1_PLACE[n]}' for n in PART1))
    return True


# ── 7 · Customer stops being required on the control ────────────────────────
#
# **A rule cannot relax a field-level Required.** A required field is required whatever any rule says, so
# RULE_CUSTOMER below can only make Customer *conditionally* required once the flag is off the control — the
# same reasoning that took Expiration's flag off in `expiry`, and the same reasoning behind BUILDING.md's rule
# that a field a rule hides must not be required on the field itself.
#
# Odoo does require `sale.order.partner_id`. This app keeps that for a real quotation, through the rule; a
# template is the exception the owner asked for (relayed 21 Sep 2026).
CUSTOMER = 'Customer'


def step_customer():
    """Clear `required` on Customer in one version-pinned save that changes nothing else."""
    f = guard()
    if not f[CUSTOMER].get('required'):
        print(f'  {CUSTOMER} is already not required; nothing saved')
        return False
    return pinned_write('customer', {CONTROLS[CUSTOMER]: {'required': False}}, 'orders_controls_pre_customer')


# ── 8 · Invoicing Status stops being hidden ─────────────────────────────────
#
# **A hidden control is not a column and cannot be a quick filter.** BUILDING.md: a hidden field never shows as a
# table column even when the view names it — which is exactly what the owner's *Orders* view was doing, listing
# Invoice Status among its `showControls` and drawing nothing — and the list calls behind views blank it.
#
# The control was built `fieldPermission` **"001"**: hidden *and* read-only. The right permission for a value the
# app computes and nobody types is the one **Status** already carries, **"100"** — read-only and hidden on create,
# visible everywhere else. (The three places are hidden · read-only · hidden on create, and `0` switches each one
# on, so "100" reads: not hidden, read-only, hidden on create.) Nothing else about the control changes: not its
# options, not its place, not its name.
# **Not `INVOICE_STATUS`** — that name is §11's Odoo `invoice_status` -> label map, and a module-level constant
# defined later silently replaces an earlier one of the same name: the first cut of this step died on
# `CONTROLS[INVOICE_STATUS]` with "cannot use 'dict' as a dict key". The same hazard as `orderlines.FIGURES`.
INVOICING_STATUS = 'Invoice Status'      # the control's name on the worksheet
READ_ONLY_PERMISSION = '100'                   # read-only and hidden on create — Status' own permission


def step_invstatus():
    """Take Invoicing Status out of hiding — `fieldPermission` "001" -> "100" — in one version-pinned save that
    changes nothing else, so it can serve as a column and as the `views` step's quick filter."""
    f = guard()
    want = f['Status'].get('fieldPermission')
    if want != READ_ONLY_PERMISSION:
        sys.exit(f'Status carries fieldPermission {want!r}, not {READ_ONLY_PERMISSION!r} — it is the permission '
                 f'this step copies onto {INVOICING_STATUS}; re-read the worksheet')
    return pinned_write('invstatus', {CONTROLS[INVOICING_STATUS]: {'fieldPermission': READ_ONLY_PERMISSION}},
                        'orders_controls_pre_invstatus')


# ── 9 · the views ───────────────────────────────────────────────────────────
#
# **All is the system default and is never touched here**, whatever it shows. *Quotations* and *Orders* are the
# owner's, hand-built with column sets and **no filters at all**, so every order appeared in both; the owner asked
# for them to be completed (relayed 21 Sep 2026), and this step writes their **filters** and *Orders*' **quick
# filter** and nothing else about them. *Templates* is this builder's own, from first to last.
#
# Every write to one of the owner's two views goes through `--view-json … --edit-attrs <the one attribute>`, the
# surgical form BUILDING.md documents: SaveWorksheetView applies only the attributes named in `editAttrs`, so the
# columns, the sort and the name read back untouched. `--view-spec` is deliberately **not** used on them — it
# derives `editAttrs` from everything the spec produced, and a spec carrying `tableFields` would rewrite the
# owner's column list.
#
# **Odoo's own definitions**, read off casimir (16-orders.md §5): both menus point at `sale.order` and neither
# action carries a domain — the filtering is done by named search filters.
#
#   * Quotations, action 497, `sale.order.search.inherit.quotation`: filter `draft` "Quotations" is
#     `state in ('draft','sent')`;
#   * Orders, action 496, `sale.order.search.inherit.sale`: filter `sales` "Sales Orders" is `state = 'sale'`,
#     and it is that action's **default** filter.
#
# Each gains *Is Template is not ticked* as well, which is this app's own addition: Odoo keeps a quotation
# template in a model of its own, so it has nothing to exclude, while here a template is an order (§6).
VIEW_TEMPLATES = 'Templates'
VIEW_QUOTATIONS, VIEW_ORDERS = 'Quotations', 'Orders'
FILTERED_VIEWS = (VIEW_QUOTATIONS, VIEW_ORDERS)        # the owner's two, whose filters this step now owns
UNTOUCHED_VIEWS = ('All',)                             # the system default: never written, filter or otherwise
# Odoo `state` -> Status, per view. The labels are looked up in the live option table, never assumed.
VIEW_STATES = {VIEW_QUOTATIONS: ('Quotation', 'Quotation Sent'),     # Odoo's `draft` filter
               VIEW_ORDERS: ('Sales Order',)}                        # Odoo's `sales` filter
# What each view must return once it is filtered, from the twelve seeded orders: Sales Order 4 · Quotation Sent 3
# · Quotation 3 · Cancelled 2, and no record with Is Template ticked. A count that does not match is a defect in
# the filter, so `views` and `check` both assert it.
VIEW_ROWS = {VIEW_QUOTATIONS: 6, VIEW_ORDERS: 4, VIEW_TEMPLATES: 0}

# ── Orders' quick filter ────────────────────────────────────────────────────
#
# Odoo's *Orders* search view carries two more named filters beside `sales` — `to_invoice` "To Invoice"
# (`invoice_status = 'to invoice'`) and `upselling` "To Upsell" (`invoice_status = 'upselling'`), which are also
# two menu actions of their own (499 and 500). **HAP's quick filter is a field, not a fixed-domain filter**: one
# quick filter on Invoicing Status covers both of those and hands back the other two states as well, so it is
# built as one field rather than as two or four named filters.
#
# The shape is the spec adapter's own `{fieldId, selectionType, displayType}` object, lowered by
# `_quick_filter_item` to `advancedSetting` `allowitem` "2" (any of) and `direction` "2" (a dropdown) — the same
# lowering `--view-spec quickFilters` performs, reached directly so the save can stay a one-attribute
# `--edit-attrs fastFilters` edit of the owner's view. A bare control id would store an **empty**
# `advancedSetting`, which is the trap BUILDING.md records.
QUICK_FILTER = {'fieldId': CONTROLS[INVOICING_STATUS], 'selectionType': 'multiple', 'displayType': 'dropdown'}


def quick_filters():
    """Orders' `fastFilters`, as the spec adapter lowers the `quickFilters` object."""
    from hap_cli.core import view_spec_adapter as vsa
    return [vsa._quick_filter_item(dict(QUICK_FILTER))]


def not_a_template(f):
    """*Is Template is not ticked* — the condition that keeps a template out of a list of real orders."""
    return {'field': f[IS_TEMPLATE]['controlId'], 'dataType': CHECKBOX, 'operator': 'ne', 'value': ['1']}


def status_is(f, labels):
    """*Status is any of …*. A view's condition on a single select is **filterType 51**, not the 2 a business rule
    uses, and 51 with several option keys means "is any of" (BUILDING.md) — which is what the CLI's own
    translator emits for `eq` on a `dataType` 11, so the mapping is not written out here."""
    c = f['Status']
    return {'field': c['controlId'], 'dataType': c['type'], 'operator': 'eq',
            'value': [option_key(c, label) for label in labels]}


def view_filter(f, labels):
    """The wire `filters` for one of the owner's two views: Status is any of `labels` **and** not a template."""
    from hap_cli.core import filter_translator as flt
    return flt.translate_filter_group({'type': 'group', 'logic': 'AND',
                                       'children': [status_is(f, labels), not_a_template(f)]})


def filter_state(filters):
    """A stored or wanted filter in comparable form: the server fills in keys neither the translator nor the view
    editor sends (`minValue`, `emptyRule`, `advancedSetting` …) and returns an option list in the options' own
    order, so a filter is compared by what it *means* — never byte for byte."""
    return [(c.get('controlId'), c.get('dataType'), c.get('spliceType'), c.get('filterType'),
             tuple(sorted(c.get('values') or []))) for c in filters or []]


def quick_filter_state(fast):
    """`fastFilters` in comparable form: the control and the two settings that make it a multi-select dropdown."""
    return [(q.get('controlId'), (q.get('advancedSetting') or {}).get('allowitem'),
             (q.get('advancedSetting') or {}).get('direction')) for q in fast or []]


def edit_view(vid, attr, value):
    """Write one attribute of a view and nothing else — `editAttrs` is what SaveWorksheetView applies."""
    hap.run('worksheet', 'view', 'update', ws(), vid, '-a', APP,
            '--view-json', json.dumps({attr: value}, ensure_ascii=False), '--edit-attrs', attr)


def view_rows(vid):
    """Every row the view returns, its filter and sort applied — `record list --view-id`."""
    out, page = [], 1
    while True:
        res = hap.run('worksheet', 'record', 'list', ws(), '-a', APP, '--view-id', vid, '-n', '200',
                      '-p', str(page), '--use-field-id-as-key')
        data = res.get('data', res) if isinstance(res, dict) else res
        rows = (data.get('rows') if isinstance(data, dict) else data) or []
        out += rows
        if len(rows) < 200:
            return out
        page += 1


def view_ids():
    return {v['name']: v['viewId'] for v in hap.listing('worksheet', 'view', 'list', ws(), '-a', APP)}


def step_views():
    """*Templates* (this builder's own), and the filters the owner's *Quotations* and *Orders* were missing —
    plus *Orders*' quick filter on Invoicing Status. *All* is not touched.

    `C.upsert_views` writes only the views it is given and `C.sort_views` is deliberately not called: it would
    re-order the whole view bar, and a new view is appended last, which is where it belongs."""
    f = guard()
    for n in NEW:
        if n not in f:
            sys.exit(f'{n} is not on {WORKSHEET} — run `controls` first')
    if f[INVOICING_STATUS].get('fieldPermission') != READ_ONLY_PERMISSION:
        sys.exit(f'{INVOICING_STATUS} carries fieldPermission '
                 f'{f[INVOICING_STATUS].get("fieldPermission")!r}: a hidden control is neither a column nor a '
                 'quick filter — run `invstatus` first')
    i = lambda *names: [f[n]['controlId'] for n in names]
    columns = i(TEMPLATE_NAME, 'Number', CUSTOMER, 'Quotation/Order Date', 'Total', 'Status')
    views = {VIEW_TEMPLATES: (dict(viewType='table', filter=C.switch_filter(f[IS_TEMPLATE], 'eq'),
                                   tableFields=columns),
                              C.sort_spec([f[TEMPLATE_NAME]]), columns)}
    live = view_ids()
    missing = [n for n in FILTERED_VIEWS if n not in live]
    if missing:
        sys.exit(f"{missing} are not on {WORKSHEET} — they are the owner's views and this step does not "
                 'create them')
    hap.backup('orders_views_pre_views', [C.view_info(ws(), APP, v) for v in live.values()])
    for name, vid in C.upsert_views(ws(), APP, views, 'orders_views_pre_templates').items():
        C.remember('views', KEY + name, vid)
    wrote = False
    for name in FILTERED_VIEWS:
        vid, want = live[name], view_filter(f, VIEW_STATES[name])
        info = C.view_info(ws(), APP, vid)
        if filter_state(info.get('filters')) == filter_state(want):
            print(f"  {name}: already filtered to Status is any of {list(VIEW_STATES[name])} and "
                  f'{IS_TEMPLATE} not ticked; nothing saved')
        else:
            edit_view(vid, 'filters', want)
            back = C.view_info(ws(), APP, vid)
            if filter_state(back.get('filters')) != filter_state(want):
                sys.exit(f'{name}: the filter read back as {filter_state(back.get("filters"))}, wanted '
                         f'{filter_state(want)} — the save did not store')
            print(f"  {name}: filtered to Status is any of {list(VIEW_STATES[name])} and {IS_TEMPLATE} not "
                  f'ticked ({vid})')
            wrote = True
        C.remember('views', KEY + name, vid)
    vid, want = live[VIEW_ORDERS], quick_filters()
    info = C.view_info(ws(), APP, vid)
    if quick_filter_state(info.get('fastFilters')) == quick_filter_state(want):
        print(f'  {VIEW_ORDERS}: the {INVOICING_STATUS} quick filter is already as specified; nothing saved')
    else:
        edit_view(vid, 'fastFilters', want)
        back = C.view_info(ws(), APP, vid)
        if quick_filter_state(back.get('fastFilters')) != quick_filter_state(want):
            sys.exit(f'{VIEW_ORDERS}: fastFilters read back as {quick_filter_state(back.get("fastFilters"))}, '
                     f'wanted {quick_filter_state(want)} — the save did not store')
        print(f'  {VIEW_ORDERS}: quick filter on {INVOICING_STATUS} — any of, as a dropdown '
              f'({json.dumps(back.get("fastFilters"), ensure_ascii=False)})')
        wrote = True
    C.print_views(ws(), APP)
    report_view_rows()
    print(f"  {list(UNTOUCHED_VIEWS)} not touched: the system default is the owner's, and it carries no filter, "
          f'so **templates appear in it** — {template_filter_note()}')
    return wrote


def report_view_rows():
    """Each view's row count beside what the twelve seeded orders say it must be."""
    live, bad = view_ids(), []
    for name, want in VIEW_ROWS.items():
        if name not in live:
            bad.append(f'{name} is missing')
            continue
        got = len(view_rows(live[name]))
        print(f"  {'OK  ' if got == want else 'DIFF'} {name} returns {got} row(s), expected {want}")
        if got != want:
            bad.append(f'{name} returns {got} row(s), expected {want}')
    return bad


def template_filter_note():
    f = C.fields(ws())
    cid = (f.get(IS_TEMPLATE) or {}).get('controlId', '<Is Template>')
    return (f'it needs the condition {IS_TEMPLATE} ({cid}) filterType {C.NE} (is not) value "1", '
            f'values ["1"], dataType {CHECKBOX}')


# ── 10 · the records the owner approved deleting ─────────────────────────────
#
# The owner approved clearing **these two worksheets' records and nothing else** (relayed 21 Sep 2026): the
# three hand-made orders and the two lines under them, all test data. The approval is pinned to the records it
# covered — every row that was live when it was given, read off the app at 16:0x on 21 Sep 2026 — so this step
# can never grow into "delete whatever is there": once the three are gone it is a no-op, and a fourth order the
# owner made in the meantime stops it rather than being swept up.
#
# The delete is a **soft** delete: `--permanent` is not passed, so each row goes to the worksheet's record
# recycle bin. `--trigger-workflow` is written out in full because the CLI sends `triggerWorkflow: false`
# without it (BUILDING.md), and `-y` because the command otherwise prompts and a script then hangs.
WIPE = {                                       # rowid -> the Number it must still carry
    '81d3b6a8-25f9-4c0c-820f-07339353ed4b': 'S00002',
    '2007c59b-7b82-4324-9bd0-1ce17c67812d': 'S00004',
    'de9055e0-09b2-4cb9-bdad-668b031ff2d2': 'S00005',
}


def read_record(worksheet, rowid):
    """One record through `record get`, which returns every control — `record list` blanks a hidden field and
    leaves a Text or Number its view does not show out of the row altogether (BUILDING.md)."""
    return hap.run('worksheet', 'record', 'get', worksheet, rowid, '-a', APP)['data']


def wipe_records(worksheet, label, approved, identify):
    """Delete the approved records, and only those. `identify` returns a record's identity for the check that
    it is still the row the approval named; a record the approval does not name is left where it is.

    Returns the number deleted. Idempotent: once the approved rows are gone this is a no-op, whatever else the
    worksheet holds — which is what makes it safe to re-run after the seed."""
    live = {r['rowid']: r for r in C.records(worksheet, APP)}
    todo = [rowid for rowid in approved if rowid in live]
    others = sorted(set(live) - set(approved))
    if not todo:
        print(f'  {label}: none of the {len(approved)} approved records is still live; nothing deleted'
              + (f' ({len(others)} other records left untouched)' if others else ''))
        return 0
    if others:
        sys.exit(f'{label} holds {len(others)} record(s) the owner\'s deletion did not cover '
                 f'({others}) while {len(todo)} approved record(s) are still live — the approval names exactly '
                 f'{sorted(approved)}; stopping rather than widening it')
    full = {rowid: read_record(worksheet, rowid) for rowid in todo}
    hap.backup(f'{label.lower().replace(" ", "")}_records_pre_wipe', full)
    for rowid in todo:
        got, want = identify(full[rowid]), approved[rowid]
        if got != want:
            sys.exit(f'{label} {rowid} reads {got!r}, and the approval named {want!r} — stopping')
    for rowid in todo:
        hap.run('worksheet', 'record', 'delete', worksheet, '--row-ids', rowid, '-a', APP,
                '--trigger-workflow', '-y')
        print(f'  deleted {rowid}  {approved[rowid]!r}')
    back = C.records(worksheet, APP)
    still = [r['rowid'] for r in back if r['rowid'] in approved]
    if still:
        sys.exit(f'{label}: {still} read back from the worksheet — the delete did not store')
    print(f'  {label}: {len(todo)} deleted, {len(back)} record(s) left')
    return len(todo)


def step_wipe():
    """Delete the three test orders the owner approved clearing. Run **after** `orderlines.py wipe`: a line
    whose parent is gone is an orphan, and the child worksheet's own approval covers both of its rows."""
    guard()
    if any(r['rowid'] in WIPE for r in C.records(ws(), APP)):
        parents = set()
        for r in C.records(LINES_WS, APP):
            parents |= set(relation_ids(read_record(LINES_WS, r['rowid']).get('order_id')))
        blocked = sorted(parents & set(WIPE))
        if blocked:
            sys.exit(f'Order Lines still holds rows under {[WIPE[b] for b in blocked]} — run '
                     '`orderlines.py wipe` first (children before parents)')
    return bool(wipe_records(ws(), WORKSHEET, WIPE, lambda d: d.get(CONTROLS['Number']) or ''))


# ── 11 · the tenant's twelve orders ─────────────────────────────────────────
#
# `nocoly/data/sale-orders-casimir.json`, read off casimir over read-only RPC on 21 Sep 2026: twelve orders and
# thirty lines. The file is the source — nothing here re-derives it — and its `_note` explains the Sequence
# renumbering, which matters because Odoo's own `sequence` is 10 on nearly every line.
#
# **The match key is (Customer, Quotation/Order Date)**, unique across all twelve, because Orders' Number is an
# **auto-number control (type 33)**: a seeded order gets whatever the app's counter issues next and can never
# carry the tenant's S00010–S00022. `seeded_orders` is that index, and the tenant name → assigned Number
# mapping goes into ids.json under `numbers` so the seed stays traceable. Whether Number should become a plain
# text control that carries Odoo's own numbers is the owner's decision; nothing here changes the control.
SEED_PATH = os.path.join(hap.HERE, os.pardir, 'data', 'sale-orders-casimir.json')

# {worksheet id: the control whose value is a record's title}, for resolving a Relation by display name at run
# time. Every one of these worksheets is somebody else's builder's and nothing here writes to them.
CONTACTS = ('6aa8a3b34a22ad87b728c4fe', 'Display Name')
PAYMENT_TERMS = ('6aab893fe43d174ab374ce17', 'Payment Terms')
SALES_TEAMS = ('6aad0f727d58b0f4493141c4', 'Sales Team')

# Odoo `sale.order.state` -> Status, `invoice_status` -> Invoice Status (the control the brief calls Invoicing
# Status), `document_tax_mode` -> Tax Mode. Every label is looked up in the live option table, never assumed.
STATE_STATUS = {'draft': 'Quotation', 'sent': 'Quotation Sent', 'sale': 'Sales Order', 'cancel': 'Cancelled'}
INVOICE_STATUS = {'to invoice': 'To Invoice', 'invoiced': 'Fully Invoiced', 'no': 'Nothing to Invoice',
                  'upselling': 'Upselling Opportunity'}
TAX_MODES = {'tax_excluded': 'Tax Excluded', 'tax_included': 'Tax Included'}

# **Prepayment Percentage is a unit conversion, not a copy.** Odoo stores `prepayment_percent` as a *ratio* —
# 1.0 on every one of the twelve, meaning 100 % — while this control is a plain Number carrying
# `advancedSetting.suffix` "%", so the tenant's raw 1 would draw "1.00 %" where the tenant's own form shows 100.
# **The owner chose this app's convention: a percentage** (relayed 21 Sep 2026), so the seed multiplies by 100
# and the app stores 100. The extract keeps the tenant's raw value — `sale-orders-casimir.json` still says
# `"prepayment_percent": 1`, and its `_note` records the conversion — because an extract records what the tenant
# holds and a builder is where a convention is applied.
PREPAYMENT_RATIO_TO_PERCENT = 100
# The four of §6b join it: `sale-orders-casimir.json` carries no `invoicing_closed`, `signature`, `signed_by` or
# `signed_on` key at all — none of the tenant's twelve orders was ever signed or manually closed — so there is
# nothing to write and nothing to compare. They are written by buttons, not by a seed.
NOT_SEEDED = ('Delivery Status', 'Journal', 'Tags', 'Template', 'Incoterm Location', TEMPLATE_NAME) + PART1


_SEED = None


def seed_data():
    """The seed file and its lines grouped by order, with the sanity check the brief asks for: every order's
    lines must sum exactly to its `amount_untaxed`. Read and checked once per run."""
    global _SEED
    if _SEED is not None:
        return _SEED
    with open(SEED_PATH) as fh:
        data = json.load(fh)
    lines = {}
    for line in data['lines']:
        lines.setdefault(line['order'], []).append(line)
    if len(data['orders']) != 12 or len(data['lines']) != 30:
        sys.exit(f"the seed holds {len(data['orders'])} orders and {len(data['lines'])} lines, expected 12 / 30")
    bad = [f"{o['name']}: its lines sum to {round(sum(l['subtotal'] for l in lines.get(o['name'], [])), 2)}, "
           f"amount_untaxed is {round(o['amount_untaxed'], 2)}"
           for o in data['orders']
           if round(sum(l['subtotal'] for l in lines.get(o['name'], [])), 2) != round(o['amount_untaxed'], 2)]
    if bad:
        sys.exit('the seed does not add up:\n  ' + '\n  '.join(bad))
    names = [o['name'] for o in data['orders']]
    if len(set(names)) != len(names):
        sys.exit(f'the seed names an order twice: {names}')
    print(f"  seed: data/{os.path.basename(SEED_PATH)} — {len(data['orders'])} orders, {len(data['lines'])} "
          f"lines; every order's lines sum exactly to its amount_untaxed")
    _SEED = (data, lines)
    return _SEED


# ── reading a cell back, by control type ────────────────────────────────────

def relation_cells(value):
    """A Relation read back through `record get` is a list of {sid, name} (a JSON string on some paths)."""
    if isinstance(value, str):
        value = json.loads(value) if value.startswith('[') else []
    return [x for x in (value or []) if isinstance(x, dict)]


def relation_ids(value):
    return [x.get('sid') for x in relation_cells(value)]


def relation_names(value):
    return [x.get('name') for x in relation_cells(value)]


def member_ids(value):
    return [x.get('accountId') for x in relation_cells(value)]


def option_keys(value):
    """A single select through the v3 `record get` is [{key, value}]; through GetRowDetail it is a list of bare
    keys (BUILDING.md). Both are reduced to the keys."""
    if isinstance(value, str):
        value = json.loads(value) if value.startswith('[') else ([value] if value else [])
    return [x.get('key') if isinstance(x, dict) else x for x in (value or [])]


def number_of(value):
    return None if value in (None, '') else round(float(value), 2)


READERS = {29: relation_ids, 26: member_ids, 11: option_keys, 9: option_keys,
           36: lambda v: '1' if str(v) == '1' else '0',
           6: number_of, 8: number_of, 31: number_of, 37: number_of, 53: lambda v: v or '',
           2: lambda v: v or '', 15: lambda v: v or '', 16: lambda v: v or '', 33: lambda v: v or ''}


def read_cell(c, record):
    """The value of control `c` on a record, in the form `want` is written in. `record get` keys a value by the
    control's **alias**, and by its controlId when it has none (BUILDING.md) — Orders carries no aliases at
    all, Order Lines carries one on every control."""
    raw = record.get(c.get('alias') or c['controlId'])
    return READERS.get(c['type'], lambda v: v)(raw)


def differences(c_by_name, live, want):
    """{control name: (got, wanted)} for every cell of `want` the record does not already carry."""
    out = {}
    for name, value in want.items():
        got = read_cell(c_by_name[name], live)
        if got != value:
            out[name] = (got, value)
    return out


# ── resolving a seeded relation by display name ─────────────────────────────

def titles(worksheet, control_name):
    """{title: [rowid, ...]} over a worksheet, for resolving a Relation by display name.

    `record list` leaves a Text the default view does not show out of the row altogether, so a title that comes
    back missing is re-read with `record get` rather than treated as empty (BUILDING.md)."""
    f = C.fields(worksheet)
    c = f[control_name]
    out = {}
    for r in C.records(worksheet, APP):
        title = r.get(c['controlId'])
        if title in (None, ''):
            title = read_cell(c, read_record(worksheet, r['rowid']))
        out.setdefault(title, []).append(r['rowid'])
    return out


def resolve(index, name, what, gaps):
    """The one record titled `name`, or None with the gap recorded. Nothing here creates a record in another
    worksheet: this build may only touch Orders and Order Lines, so a name the app does not hold leaves the
    cell empty and is reported."""
    rows = index.get(name) or []
    if len(rows) == 1:
        return rows[0]
    gaps.setdefault((what, name), 0)
    gaps[(what, name)] += 1
    return None


def option_key(c, label):
    keys = [o['key'] for o in c.get('options') or [] if o['value'] == label and not o.get('isDeleted')]
    if len(keys) != 1:
        sys.exit(f"{c['controlName']}: {label!r} matches {len(keys)} live options among "
                 f"{[o['value'] for o in c.get('options') or []]}")
    return keys[0]


def order_key(customer_rowid, date):
    """What matches a live order with a seeded one: (Customer, Quotation/Order Date). Not the Number — that is
    an auto-number control and the app's own counter owns it."""
    return (customer_rowid or '', date or '')


def seeded_orders():
    """{tenant name: (rowid, Number)} for every seeded order that is live, matched on (Customer, Date)."""
    f = C.fields(ws())
    data, _lines = seed_data()
    live = {}
    for r in C.records(ws(), APP):
        d = read_record(ws(), r['rowid'])
        live[order_key((read_cell(f[CUSTOMER], d) or [None])[0], read_cell(f['Quotation/Order Date'], d))] = \
            (r['rowid'], read_cell(f['Number'], d))
    contacts = titles(*CONTACTS)
    out, gaps = {}, {}
    for o in data['orders']:
        rows = contacts.get(o['partner']) or []
        key = order_key(rows[0] if len(rows) == 1 else None, o['date_order'])
        if key in live:
            out[o['name']] = live[key]
    return out


def order_want(f, o, index, gaps):
    """{control name: value} — every cell the seed writes on one order, and nothing else.

    A relation the app cannot resolve is **left out of `want` altogether**, so it is neither written nor
    compared and a later run picks it up the day the record exists; every one of them is reported."""
    contacts, payterms, teams, salespeople = index['contacts'], index['payterms'], index['teams'], index['people']
    want = {
        'Status': [option_key(f['Status'], STATE_STATUS[o['state']])],
        'Invoice Status': [option_key(f['Invoice Status'], INVOICE_STATUS[o['invoice_status']])],
        'Tax Mode': [option_key(f['Tax Mode'], TAX_MODES[o['tax_mode']])],
        'Quotation/Order Date': o['date_order'],
        'Expiration': o['validity_date'] or '',
        'Customer Reference': o['client_order_ref'] or '',
        'Source Document': o['origin'] or '',
        'Online Signature': '1' if o['require_signature'] else '0',
        'Online Payment': '1' if o['require_payment'] else '0',
        # Odoo's ratio as this app's percentage: 1.0 -> 100. The control is hidden (fieldPermission "011"), which
        # changes nothing here — a hidden control is written and read back by the API like any other, and only
        # `record list` blanks it, which is why every read goes through `record get` (BUILDING.md).
        'Prepayment Percentage': round(float(o['prepayment_percent']) * PREPAYMENT_RATIO_TO_PERCENT, 2),
        'Locked': '1' if o['locked'] else '0',
        IS_TEMPLATE: '0',                      # a seeded order is never a template
    }
    if o['commitment_date']:
        want['Delivery Date'] = o['commitment_date']
    for field, name, kind, idx in ((CUSTOMER, o['partner'], 'contact', contacts),
                                   ('Invoice Address', o['invoice_address'], 'contact', contacts),
                                   ('Delivery Address', o['delivery_address'], 'contact', contacts),
                                   ('Payment Terms', o['payment_term'], 'payment term', payterms),
                                   ('Sales Teams', o['sales_team'], 'sales team', teams)):
        if not name:
            continue
        rowid = resolve(idx, name, kind, gaps)
        if rowid:
            want[field] = [rowid]
    if o['salesperson']:
        account = salespeople.get(o['salesperson'])
        if account:
            want['Salesperson'] = [account]
        else:
            gaps.setdefault(('member', o['salesperson']), 0)
            gaps[('member', o['salesperson'])] += 1
    return want


def members(names):
    """{name: accountId} for the seed's salespeople, resolved through the organisation's own directory.

    `contact search` is a keyword search, so a name that matches more than one member is refused rather than
    guessed — the tenant's "Casimir" is this organisation's "Casimir Chiong Ming Yuan"."""
    out = {}
    for name in sorted(names):
        res = hap.run('contact', 'search', name)
        users = (res or {}).get('users') or []
        if len(users) == 1:
            out[name] = users[0]['id']
            print(f"  salesperson {name!r} -> {users[0]['name']} ({users[0]['id']})")
        else:
            print(f'  salesperson {name!r}: {len(users)} members match '
                  f"{[u['name'] for u in users]} — left empty and reported")
    return out


def seed_index(data):
    return {'contacts': titles(*CONTACTS), 'payterms': titles(*PAYMENT_TERMS), 'teams': titles(*SALES_TEAMS),
            'people': members({o['salesperson'] for o in data['orders'] if o['salesperson']})}


def write_record(worksheet, rowid, values):
    body = json.dumps(values, ensure_ascii=False)
    if rowid:
        hap.run('worksheet', 'record', 'update', worksheet, rowid, '-a', APP, '--fields-json', body)
        return rowid
    return C.row_id(hap.run('worksheet', 'record', 'create', worksheet, '-a', APP, '--fields-json', body))


def step_seed():
    """The tenant's twelve orders, matched by (Customer, Quotation/Order Date) and re-running to nothing.

    Nothing is written to any other worksheet: a Customer, an Invoice or Delivery Address, a Payment Term or a
    Sales Team whose record this app does not hold is left empty and reported, because creating it would mean
    writing to Contacts, Payment Terms or Sales Teams.

    **The one value the seed converts rather than copies is Prepayment Percentage** — Odoo's `prepayment_percent`
    is a ratio (1.0 = 100 %) and this control is a Number with a "%" suffix, so the seed writes
    `prepayment_percent × 100` and the app stores 100. The extract keeps the tenant's raw 1; see
    `PREPAYMENT_RATIO_TO_PERCENT` above and the seed file's `_note`."""
    f = guard()
    for n in NEW:
        if n not in f:
            sys.exit(f'{n} is not on {WORKSHEET} — run `controls` first')
    if f[CUSTOMER].get('required'):
        sys.exit(f'{CUSTOMER} still carries `required` on the control, so an order with no customer cannot be '
                 'seeded — run `customer` first')
    data, lines = seed_data()
    index = seed_index(data)
    live = {}
    for r in C.records(ws(), APP):
        d = read_record(ws(), r['rowid'])
        live[order_key((read_cell(f[CUSTOMER], d) or [None])[0],
                       read_cell(f['Quotation/Order Date'], d))] = (r['rowid'], d)
    hap.backup('orders_records_pre_seed', {rowid: d for rowid, d in live.values()})
    gaps, numbers, problems = {}, {}, []
    for o in data['orders']:
        want = order_want(f, o, index, gaps)
        key = order_key((want.get(CUSTOMER) or [None])[0], want['Quotation/Order Date'])
        rowid, record = live.get(key, (None, {}))
        diff = differences(f, record, want) if rowid else want
        if rowid and not diff:
            numbers[o['name']] = read_cell(f['Number'], record)
            print(f"  {o['name']}: already seeded as {numbers[o['name']]} ({rowid})")
        else:
            values = ([{'id': f[n]['controlId'], 'value': want[n]} for n in diff] if rowid else
                      [{'id': f[n]['controlId'], 'value': v} for n, v in want.items()
                       if v not in ('', [], None)])
            rowid = write_record(ws(), rowid, values)
            record = read_record(ws(), rowid)
            numbers[o['name']] = read_cell(f['Number'], record)
            print(f"  {o['name']}: {'updated' if key in live else 'created'} as {numbers[o['name']]} ({rowid})")
        left = differences(f, record, want)
        if left:
            problems.append(f"{o['name']} ({numbers[o['name']]}): {json.dumps(left, ensure_ascii=False, default=str)}")
        C.remember('records', KEY + o['name'], rowid)
        C.remember('numbers', KEY + o['name'], numbers[o['name']])
    print(f'  tenant name -> assigned Number: '
          + ', '.join(f'{n} -> {numbers[n]}' for n in (o['name'] for o in data['orders'])))
    report_gaps(gaps)
    print(f'  not seeded (no tenant value, or out of this build\'s scope): {list(NOT_SEEDED)}')
    if problems:
        sys.exit('  the seed read back with differences:\n    ' + '\n    '.join(problems))
    return True


def report_gaps(gaps):
    if not gaps:
        print('  every relation the seed names resolved to exactly one record')
        return
    print(f'  {len(gaps)} name(s) the seed points at are not in this app, so the cell was left empty:')
    for (what, name), count in sorted(gaps.items()):
        print(f'    {what:<13} {name!r} — on {count} cell(s); create it in its own worksheet and re-run `seed`')


# ── 12 · the figures: what the app computed against what the tenant holds ────
#
# Untaxed Amount, Tax and Total are 汇总 over the Order Lines subtable and the seed writes none of them —
# nothing here "fixes" a figure, because a mismatch is a finding about the roll-ups and the line formulas
# they sum, not about the data.
AMOUNTS = (('Untaxed Amount', 'amount_untaxed'), ('Tax', 'amount_tax'), ('Total', 'amount_total'))


def step_figures():
    """Each seeded order's three roll-ups beside the tenant's own amount_untaxed / amount_tax / amount_total."""
    f = guard()
    data, _lines = seed_data()
    live = seeded_orders()
    diffs = 0
    for o in data['orders']:
        if o['name'] not in live:
            print(f"  {o['name']}: not seeded — run `seed`")
            diffs += 1
            continue
        rowid, number = live[o['name']]
        d = read_record(ws(), rowid)
        got = [(name, read_cell(f[name], d), round(o[key], 2)) for name, key in AMOUNTS]
        bad = [x for x in got if x[1] != x[2]]
        diffs += len(bad)
        print(f"  {'DIFF' if bad else 'OK  '} {o['name']} -> {number}  "
              + '  '.join(f'{n}={v if v is not None else "(empty)"}/{w}' for n, v, w in got))
    print(f'  {diffs} figure(s) differ from the tenant (app value / tenant value above)')
    return diffs


# ── the guard ───────────────────────────────────────────────────────────────

def guard():
    """Stop unless the profile reaches ERP Master › Sales › Orders and the controls this builder names are the
    ones it was written against. Returns the live controls by name.

    It deliberately does **not** insist the worksheet hold only the controls it knows: the owner is adding fields
    by hand, and a builder that stopped on an unfamiliar control would stop every time they did."""
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
        sys.exit(f'{WORKSHEET}: ' + '; '.join(problems) + ' — re-read the worksheet before writing a rule')
    unknown = sorted(set(f) - set(CONTROLS) - set(NEW) - set(PART1))
    if unknown:
        print(f'  note: {WORKSHEET} also carries {unknown} — added by the owner, and no rule here names them')
    for name in CONTROLS:
        C.remember('controls', KEY + name, CONTROLS[name])
    return f


# ── check ───────────────────────────────────────────────────────────────────

def condition_state(filters, names):
    """A rule's filter as (control name, spliceType, filterType, value, sorted values) groups, for comparison."""
    return [[(names.get(c['controlId'], c['controlId']), c['spliceType'], c['filterType'], c['value'],
              sorted(c['values'])) for c in (g.get('groupFilters') or [g])] for g in filters]


def step_check():
    """Read the four rules, the retired ones, Expiration and the three roll-ups back, and report every drift."""
    f = guard()
    names = {c['controlId']: c['controlName'] for c in hap.controls(ws())}
    live = {r['name']: r for r in hap.listing('worksheet', 'rules', ws())}
    problems = []
    for name, kind, filters, items, _opts in rule_specs(f):
        r = live.get(name)
        if r is None:
            problems.append(f'rule {name!r} missing')
            continue
        want = (kind, False, condition_state(filters, names), item_state(items, names))
        got = (r['type'], r['disabled'], condition_state(r['filters'], names),
               item_state(r['ruleItems'], names))
        if got != want:
            problems.append(f'rule {name!r}:\n    want {want}\n    got  {got}')
        else:
            print(f"  OK  {name!r}\n        when {got[2]}\n        then {got[3]}  (ruleId {r['ruleId']})")
    by_id = {r['ruleId']: r for r in live.values()}
    for rid, (name, does, replaced_by) in SUPERSEDED.items():
        r = by_id.get(rid)
        if r is None:
            print(f'  gone      {rid} {name!r} — deleted in the UI')
        elif not r['disabled']:
            problems.append(f'{rid} {name!r} is enabled again; it duplicates {replaced_by!r} — run `retire`')
        else:
            print(f'  disabled  {rid} {name!r}')
    for rid, (name, does) in KEPT.items():
        r = by_id.get(rid)
        print(f"  kept      {rid} {name!r} — {'enabled' if r and not r['disabled'] else 'not enabled'}")
    for name, r in live.items():
        if name not in RULES and r['ruleId'] not in SUPERSEDED and r['ruleId'] not in KEPT:
            print(f"  new       {r['ruleId']} {name!r} — the owner's, not this builder's")
    if f[EXPIRATION].get('required'):
        problems.append(f'{EXPIRATION} is required again, and {RULE_EXPIRATION!r} hides it: '
                        'a hidden required field cannot be filled and the form cannot be saved — run `expiry`')
    else:
        print(f'  OK  {EXPIRATION} is not required (Odoo does not require validity_date)')
    # the three roll-ups and the subtable's columns
    by_id = {c['controlId']: c for c in hap.controls(ws())}
    for cid, want in totals_spec().items():
        diff = drift(by_id[cid], want)
        if diff:
            problems.append(f'{names[cid]}: {json.dumps(diff, ensure_ascii=False, default=str)} — run `totals`')
        elif cid == CONTROLS[ORDER_LINES]:
            print(f'  OK  {ORDER_LINES} shows {list(SUBTABLE_COLUMNS)}')
        else:
            print(f"  OK  {names[cid]} = sum of Order Lines / "
                  f"{ {v: k for k, v in CHILD.items()}[want['sourceControlId']]}, product lines only")
    for cid, want in dots_spec().items():
        diff = drift(by_id[cid], want)
        if diff:
            problems.append(f'{names[cid]}: {json.dumps(diff, ensure_ascii=False, default=str)} — run `dots`')
    if not any(drift(by_id[cid], want) for cid, want in dots_spec().items()):
        print(f'  OK  {sorted(ROLLUPS)} all carry dot {MONEY_DOT}, so a money total draws 270.00')
    print(f'  not built: {CONFIRMED_MISSING[0]!r} read-only with the rest of Odoo\'s eight — the control does '
          f'not exist, deferred to its own bundle')
    print(f"  the owner's: 'Only require Prepayment Percentage if Online Payment is needed' — a SHOW rule on a "
          f"field whose fieldPermission is 011 (hidden by design); left exactly as it is")
    # the two appended controls, Customer's flag, the Templates view and the seed
    missing = [n for n in NEW if n not in f]
    if missing:
        problems.append(f'{missing} are not on the worksheet — run `controls`')
    else:
        spec = new_spec()
        for n in NEW:
            diff = drift(f[n], spec[n])
            if diff:
                problems.append(f'{n}: {json.dumps(diff, ensure_ascii=False)} — run `controls`')
            else:
                print(f"  OK  {n} as specified ({f[n]['controlId']}, alias {f[n].get('alias')})")
    # §6b's four, the controls four of Odoo's twenty Orders actions write
    missing = [n for n in PART1 if n not in f]
    if missing:
        problems.append(f'{missing} are not on the worksheet — run `part1`')
    else:
        spec = part1_spec()
        for n in PART1:
            diff = drift(f[n], spec[n])
            if diff:
                problems.append(f'{n}: {json.dumps(diff, ensure_ascii=False, default=str)} — run `part1`')
            else:
                print(f"  OK  {n} as specified ({f[n]['controlId']}, t{f[n]['type']}, alias "
                      f"{f[n].get('alias')}, fieldPermission {f[n].get('fieldPermission')})")
        if not any(drift(f[n], spec[n]) for n in PART1):
            parked = [n for n in PART1 if f[n].get('row') == 9999]
            print(f'  {"NOTE" if parked else "OK  "} placement: '
                  + (f'{parked} still parked at row 9999 — the owner places them in the designer; intended '
                     + ', '.join(f'{n} {PART1_PLACE[n]}' for n in parked)
                     if parked else
                     'all four placed, at ' + ', '.join(f"{n} r{f[n].get('row')}c{f[n].get('col')}"
                                                        f"s{f[n].get('size')}" for n in PART1)))
    if f[CUSTOMER].get('required'):
        problems.append(f'{CUSTOMER} carries `required` on the control, so {RULE_CUSTOMER!r} cannot relax it on '
                        'a template — run `customer`')
    else:
        print(f'  OK  {CUSTOMER} is not required on the control; {RULE_CUSTOMER!r} requires it conditionally')
    if f[INVOICING_STATUS].get('fieldPermission') != READ_ONLY_PERMISSION:
        problems.append(f'{INVOICING_STATUS} carries fieldPermission '
                        f'{f[INVOICING_STATUS].get("fieldPermission")!r}, not {READ_ONLY_PERMISSION!r}: hidden, so '
                        'it is neither a column nor a quick filter — run `invstatus`')
    else:
        print(f'  OK  {INVOICING_STATUS} fieldPermission {READ_ONLY_PERMISSION} — read-only and hidden on create, '
              f"as Status' own is; visible as a column and usable as a quick filter")
    views = view_ids()
    if VIEW_TEMPLATES not in views:
        problems.append(f'the {VIEW_TEMPLATES!r} view is missing — run `views`')
    elif IS_TEMPLATE in f:
        info = C.view_info(ws(), APP, views[VIEW_TEMPLATES])
        flt = [(c['controlId'], c['filterType'], c.get('values')) for c in info.get('filters') or []]
        want = [(f[IS_TEMPLATE]['controlId'], C.EQ, ['1'])]
        sort = [(names.get(s['controlId'], s['controlId']), s.get('isAsc')) for s in info.get('moreSort') or []]
        lead = (info.get('showControls') or [None])[0]
        if flt != want:
            problems.append(f'the {VIEW_TEMPLATES!r} view filters {flt}, wanted {want} — run `views`')
        elif sort != [(TEMPLATE_NAME, True)] or lead != f[TEMPLATE_NAME]['controlId']:
            problems.append(f'the {VIEW_TEMPLATES!r} view sorts {sort} and leads with {names.get(lead, lead)!r}, '
                            f'wanted {[(TEMPLATE_NAME, True)]} and {TEMPLATE_NAME!r} — run `views`')
        else:
            print(f'  OK  {VIEW_TEMPLATES} filters {IS_TEMPLATE} is ticked, sorts by {TEMPLATE_NAME} ascending '
                  f'and leads with it ({views[VIEW_TEMPLATES]})')
    for name in FILTERED_VIEWS:
        if name not in views:
            problems.append(f"the owner's {name!r} view is missing")
            continue
        info = C.view_info(ws(), APP, views[name])
        want = view_filter(f, VIEW_STATES[name])
        if filter_state(info.get('filters')) != filter_state(want):
            problems.append(f"the owner's {name!r} view filters {filter_state(info.get('filters'))}, wanted "
                            f'{filter_state(want)} — run `views`')
        else:
            print(f'  OK  {name} filters Status is any of {list(VIEW_STATES[name])} and {IS_TEMPLATE} not '
                  f'ticked ({views[name]})')
    if VIEW_ORDERS in views:
        got = quick_filter_state(C.view_info(ws(), APP, views[VIEW_ORDERS]).get('fastFilters'))
        if got != quick_filter_state(quick_filters()):
            problems.append(f'{VIEW_ORDERS} carries fastFilters {got}, wanted '
                            f'{quick_filter_state(quick_filters())} — run `views`')
        else:
            print(f'  OK  {VIEW_ORDERS} has a quick filter on {INVOICING_STATUS}, any of, as a dropdown')
    problems += report_view_rows()
    for name in UNTOUCHED_VIEWS:
        info = C.view_info(ws(), APP, views[name]) if name in views else {}
        if not (info.get('filters') or []):
            print(f"  the owner's {name!r} view has no filter, so **templates appear in it** — "
                  f'{template_filter_note()}')
    data, _lines = seed_data()
    seeded = seeded_orders()
    absent = [o['name'] for o in data['orders'] if o['name'] not in seeded]
    if absent:
        problems.append(f'{len(absent)} seeded order(s) are not on the worksheet ({absent}) — run `seed`')
    else:
        print(f'  OK  all {len(seeded)} seeded orders are live: '
              + ', '.join(f'{n} -> {seeded[n][1]}' for n in (o['name'] for o in data['orders'])))
        index, gaps = seed_index(data), {}
        for o in data['orders']:
            rowid, number = seeded[o['name']]
            left = differences(f, read_record(ws(), rowid), order_want(f, o, index, gaps))
            if left:
                problems.append(f"{o['name']} ({number}): {json.dumps(left, ensure_ascii=False, default=str)} "
                                '— run `seed`')
        report_gaps(gaps)
    if problems:
        print('  check: ' + '\n         '.join(problems))
        sys.exit(1)
    print(f'  check: OK — {len(RULES)} rules, the retired five, Expiration, three roll-ups at {MONEY_DOT} '
          f'decimals, the {len(SUBTABLE_COLUMNS)} subtable columns, {INVOICING_STATUS} at '
          f'{READ_ONLY_PERMISSION}, the {len(PART1)} controls of §6b at {READ_ONLY_PERMISSION} and '
          f'{len(VIEW_ROWS)} views returning {list(VIEW_ROWS.values())} rows')


def step_show():
    """The live controls and rules, and the Order Lines subtable's own columns."""
    guard()
    C.show(ws())
    for r in hap.listing('worksheet', 'rules', ws()):
        print(f"  {'disabled' if r['disabled'] else 'enabled ':<9} {r['ruleId']} {r['name']}")
    # Odoo's `sale_order_line_non_accountable_null_fields` is 16-orders.md's third hide rule, and its targets
    # live on the child worksheet. §6 recorded it as unbuildable, and it was: the Order Lines of the time was a
    # `child_fields` 子表 — a **hidden child table** whose id the subtable control itself had minted (…fe5 the
    # control, …fe6 the back-relation, …fe7 the worksheet, all in one second), with no entry in the app's
    # sections, and both `worksheet fields` (V3) and the main site's own `GetWorksheetControls` answered
    # *Insufficient permissions* for it. The owner replaced it on 21 Sep 2026 with a **mounted** worksheet,
    # 6ab0c740e43d174ab37535b2, which reads like any other and is `orderlines.py`'s — so the rule is built there.
    sub = next(c for c in hap.controls(ws()) if c['controlId'] == CONTROLS[ORDER_LINES])
    names = {c['controlId']: c['controlName'] for c in hap.controls(sub['dataSource'])}
    print(f"  {ORDER_LINES} -> mounted worksheet {sub['dataSource']}, "
          f"{len(sub.get('relationControls') or [])} controls; columns: "
          f"{[names.get(x, x + ' (DEAD)') for x in sub.get('showControls') or []]}")
    for r in sub.get('relationControls') or []:
        print(f"    t{r['type']:<3} {r['controlName']:<24} {r['controlId']}")


STEPS = {'rules': step_rules, 'retire': step_retire, 'expiry': step_expiry, 'totals': step_totals,
         'dots': step_dots, 'controls': step_controls, 'part1': step_part1, 'customer': step_customer,
         'invstatus': step_invstatus, 'views': step_views,
         'wipe': step_wipe, 'seed': step_seed, 'figures': step_figures,
         'check': step_check, 'show': step_show}

if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] not in STEPS:
        sys.exit(f'usage: {sys.argv[0]} {{{" | ".join(STEPS)}}}')
    print(f'{WORKSHEET}: {sys.argv[1]}')
    STEPS[sys.argv[1]]()
