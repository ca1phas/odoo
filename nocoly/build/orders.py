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
    ~/.hap-venv/bin/python nocoly/build/orders.py buttons  # 13. Part 2 of the button build: Confirm · Cancel ·
                                                           #     Set to Quotation · Mark as Sent, their
                                                           #     workflows, and Odoo's missing-product guard
                                                           #     on Confirm; and Part 3, Deliver, with its
                                                           #     get-multiple and per-line sub-process; and
                                                           #     §14c, Apply Discount and its two children
    ~/.hap-venv/bin/python nocoly/build/orders.py selfcheck# 13b. press all four through the CLI on one tenant
                                                           #     order and put it back, and prove the guard
                                                           #     refuses the order whose lines have no Product
    ~/.hap-venv/bin/python nocoly/build/orders.py selfdeliver# 13b2. press Deliver on one Sales Order through the CLI,
                                                           #     read every line back both ways, restore it, and
                                                           #     ask the server where the button is offered
    ~/.hap-venv/bin/python nocoly/build/orders.py discountproduct # 14. Odoo's Discount product (a record in
                                                           #     Products, never a control) and its variant
    ~/.hap-venv/bin/python nocoly/build/orders.py discountline # 14a. prove a Discount line is an ordinary product
                                                           #     line: add one to S00006, read it, delete it
    ~/.hap-venv/bin/python nocoly/build/orders.py discountfields # 14b. Discount Type and Discount Value, appended
                                                           #     (`buttons` then builds Apply Discount, §14c)
    ~/.hap-venv/bin/python nocoly/build/orders.py selfdiscount # 14d. press Apply Discount on S00006 through the
                                                           #     CLI — Global 10%, again, Fixed 1,000, 0 — and
                                                           #     the one-tax-group name on another order; restore
    ~/.hap-venv/bin/python nocoly/build/orders.py terms    # 15a. Terms and conditions (Odoo's `note`), appended
    ~/.hap-venv/bin/python nocoly/build/orders.py templates# 15b. point the three Word templates' Terms placeholder
                                                           #     at it — a file change in nocoly/print-templates/
    ~/.hap-venv/bin/python nocoly/build/orders.py print    # 15c. upload the general template as System Print
                                                           #     'Quotation / Order' on Orders
    ~/.hap-venv/bin/python nocoly/build/orders.py selfprint# 15d. fill it for one order through the CLI, with and
                                                           #     without a TEST Terms value; put the order back
    ~/.hap-venv/bin/python nocoly/build/orders.py send     # 16. rewire the owner's Send Quotation: batch on the
                                                           #     button, and its workflow — the customer's email
                                                           #     guard, the order's file from 'Quotation / Order',
                                                           #     Odoo's email with it attached, Quotation → Quotation
                                                           #     Sent. Publishes; **never presses it** (real email)
    ~/.hap-venv/bin/python nocoly/build/orders.py sendreach# 16b. read-only: whose inbox each order's Send reaches
    ~/.hap-venv/bin/python nocoly/build/orders.py signlink # 17a. Signing Link, appended (read-only, "100")
    ~/.hap-venv/bin/python nocoly/build/orders.py sign     # 17b/c. Sign & Accept: the Share for Signature button
                                                           #     and its Get Link workflow (a single-use, no-login
                                                           #     fill-in link into Signing Link), and the workflow
                                                           #     'Signed: confirm the order'. Publishes; presses
                                                           #     nothing
    ~/.hap-venv/bin/python nocoly/build/orders.py signtest # 17d. the TEST quotations for the browser test, each
                                                           #     pressed once through the button API; prints links
    ~/.hap-venv/bin/python nocoly/build/orders.py selfsign # 17e. sign a third TEST quotation through the API four
                                                           #     ways and read every run and cell back
    ~/.hap-venv/bin/python nocoly/build/orders.py incoterm # 18. Incoterm (Relation → Incoterms, active only),
                                                           #     appended; the alias `incoterm_location` on the
                                                           #     owner's Incoterm Location — one pinned save
    ~/.hap-venv/bin/python nocoly/build/orders.py selfincoterm # 18b. set both on the TEST order, read them back
                                                           #     through both read paths, put them back
    ~/.hap-venv/bin/python nocoly/build/orders.py check    # read rules, Expiration, the roll-ups, the two new
                                                           #    controls, the views, the five buttons with their
                                                           #    workflows and the seed back, and report drift;
                                                           #    since §14 also the Discount product, the two
                                                           #    discount fields and Apply Discount; since §16 Send;
                                                           #    since §17 Sign & Accept; since §18 Incoterm
    ~/.hap-venv/bin/python nocoly/build/orders.py show     # the live controls and rules

**Field names (aliases), 23 Sep 2026.** Orders was built before the app-wide convention that a control's alias is
its **Odoo field name**, so all 45 carried `alias=''` while every other worksheet had them (16-orders.md §7.2
item 7). Twenty-six were filled in from the §2 table in **one version-pinned save**, done by hand rather than by a
step: `state locked name partner_id partner_invoice_id partner_shipping_id validity_date date_order
commitment_date invoice_status payment_term_id delivery_status document_tax_mode order_line amount_untaxed
amount_tax amount_total require_payment require_signature prepayment_percent user_id team_id tag_ids
client_order_ref journal_id origin`. They join the nine this build had set (`invoicing_closed is_template
template_name signature signed_by signed_on access_url discount_type discount_value`), Terms and conditions'
`note`, and §18's `incoterm` / `incoterm_location`; sections (t52) and dividers (t22) take none. The read-back
showed no control's place or size moved. Five of them are **ours, not Odoo's** — `sale.order` has no
`is_template`, `template_name`, `discount_type`, `discount_value` or `access_url`.


**There is no `fields` or `layout` step, and there must not be one** — `views` writes one view of its own,
`seed` writes records and `buttons` writes custom actions and their workflows; none of them replaces a control.
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
import datetime, json, os, re, shutil, sys, time, zipfile
from xml.etree import ElementTree

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

# **The owner renamed and extended this rule on 22 Sep 2026** — same ruleId 6ab0ba6d805aef703286d6fb, same
# condition (Status is Sales Order), and a second item beside HIDE Expiration: SHOW Invoicing Closed, so the
# checkbox only appears on a confirmed order (Odoo's Close / Reopen Invoicing are header buttons of a `sale`
# order only). The builder adopts both the name and the item; `upsert_rules` matches by name, so the old name
# here would have created a duplicate without the second item. The ids.json key keeps the **original** name
# (`RULE_IDS_KEY`), because an ids.json key is never renamed.
RULE_EXPIRATION = 'Expiration is for an unconfirmed quotation, only show Invoicing Closed for Sales Orders'
RULE_IDS_KEY = {RULE_EXPIRATION: 'Expiration is for an unconfirmed quotation'}
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
        # The owner's second item (22 Sep 2026): SHOW Invoicing Closed under the same condition, so it is off the
        # form on a quotation and on a cancelled order. Only once §6b has appended the control.
        (RULE_EXPIRATION, C.INTERACTION, C.any_of([is_any_of(f, 'Status', ['Sales Order'])]),
         [C.item(C.HIDE, *ctrl([EXPIRATION]))]
         + ([C.item(C.SHOW, f[INVOICING_CLOSED])] if INVOICING_CLOSED in f else []), {}),
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
        C.remember('rules', KEY + RULE_IDS_KEY.get(name, name), live[name]['ruleId'])
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
# `cardstyle` joins the list for the owner's *Sign & Accept* control (type 49, a 查询按钮), whose
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
    'Orders': '6ab0c740e43d174ab37535b1',          # the back-relation to Orders (LINES_ORDERS)
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
# recreate from (the owner's decision, relayed 21 Sep 2026). Both are this app's own invention; their `desc`
# says only what they do, for the app's users (owner's rule, 22 Sep 2026), so that is recorded here and in 16.
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
    IS_TEMPLATE: 'Tick to keep this quotation as a template instead of sending it. Recreate from the record menu to '
                 'start a quotation from this template: Recreate copies the order lines, Copy does not.',
    TEMPLATE_NAME: 'The name shown for this template in the Templates view.',
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
# is recorded in ODOO_INVOICING_CLOSED_LABEL and 16-orders.md; a `desc` in this app never names Odoo.
#
# **Permissions.** All four carry `fieldPermission` **"100"** — read-only and hidden on create, which is
# **Status**' own permission and for the same reason: a button or a workflow writes them and nobody types them.
# The step asserts Status still reads "100" before copying it. It does not stop the buttons: **an API write
# ignores field permission** (Prepayment Percentage is "011", hidden, and seeded fine on 21 Sep), and a
# workflow's write is not the form's either.
#
# **Invoicing Closed is the exception since 22 Sep 2026: "110"** — editable, off the create form, the same as
# Locked. The owner deleted the Close Invoicing and Reopen Invoicing buttons (§13) and made the checkbox itself
# the control, shown only on a Sales Order by RULE_EXPIRATION's second item. So `part1_spec` expects "110" for it
# and "100" for the other three, and neither `part1` nor `check` treats the owner's "110" as drift. The owner
# also shortened its `desc` the same day; `PART1_DESC` carries their text.
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
# fieldPermission per control. Invoicing Closed is the owner's "110" (see above); the other three stay "100".
PART1_PERMISSION = {INVOICING_CLOSED: '110', SIGNATURE_FIELD: '100', SIGNED_BY: '100', SIGNED_ON: '100'}
PART1_PLACE = {INVOICING_CLOSED: (24, 0, 6),   # (row, col, size) — only `size` survives the append
               SIGNATURE_FIELD: (25, 0, 12),   # a signature pad wants the full width
               SIGNED_BY: (26, 0, 6), SIGNED_ON: (26, 1, 6)}
# Each type's own neighbours on this worksheet decide the placeholder: the three checkboxes all carry "", and
# both datetimes carry HAP's own "Please select date". A read-only control never shows a placeholder anyway, so
# this is consistency rather than behaviour — and the spec below deliberately does **not** assert it, as §6 does
# not, so a server-side normalisation cannot put the step into a repair loop.
PART1_HINT = {INVOICING_CLOSED: '', SIGNATURE_FIELD: '', SIGNED_BY: '', SIGNED_ON: 'Please select date'}
PART1_DESC = {
    # The owner's own text, 22 Sep 2026. It no longer names Odoo's label (ODOO_INVOICING_CLOSED_LABEL), so the
    # name divergence is traceable from here and from 16-orders.md, not from the app.
    INVOICING_CLOSED: 'Stop asking for this order to be invoiced, without cancelling it',
    SIGNATURE_FIELD: 'The signature the customer drew when accepting the quotation online. Filled in automatically '
                     'and cleared by Set to Quotation.',
    SIGNED_BY: 'The name the customer gave when accepting the quotation online. Filled in automatically.',
    SIGNED_ON: 'When the customer accepted the quotation online. Filled in automatically.',
}


def part1_controls():
    """The four controls, as `append_controls` takes them (its own copy drops the `controlId`).

    `showtype` "1" on the checkbox is what the owner's own three checkboxes on this worksheet carry (Locked,
    Online Payment, Online Signature) and what §6 gave Is Template; hap-cli's SWITCH template defaults to "0",
    which would draw this one differently from its four neighbours. The datetime's `showtype` "1" is hap-cli's
    own template default and is what Quotation/Order Date and Delivery Date both read."""
    def built(name, kind, **kw):
        return C.control(kind, name, PART1_PLACE[name], alias=PART1_ALIAS[name], hint=PART1_HINT[name],
                         desc=PART1_DESC[name], extra={'fieldPermission': PART1_PERMISSION[name]}, **kw)
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
                'fieldPermission': PART1_PERMISSION[n]} for n in PART1}
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
    print(f'  Status reads fieldPermission {status_perm!r}; {SIGNATURE_FIELD}, {SIGNED_BY} and {SIGNED_ON} copy '
          f'it, {INVOICING_CLOSED} carries the owner\'s {PART1_PERMISSION[INVOICING_CLOSED]!r}')
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
    print(f'  Odoo\'s own label for {INVOICING_CLOSED} is {ODOO_INVOICING_CLOSED_LABEL!r} — the owner\'s desc '
          'no longer carries it (22 Sep 2026)')
    parked = [n for n in PART1 if f[n].get('row') == 9999]
    if parked:
        print('  placement outstanding — the owner places these in the designer; intended (row, col, size): '
              + ', '.join(f'{n} {PART1_PLACE[n]}' for n in parked))
    else:
        print('  placement: all four placed by the owner')
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
# What each view must return is **derived from the live records**, not fixed: exactly the orders whose Status is
# one of the view's and whose Is Template is not ticked (Templates: exactly those ticked). It used to be the seed's
# counts — Quotations 6 · Orders 4 · Templates 0 — and that broke on 22 Sep 2026, when the owner's Confirm on app
# S00017 legitimately moved one order from Quotations to Orders. A view that returns other rows than these is a
# defect in its filter, so `views` and `check` both assert it, row for row.
VIEW_ROWS = (VIEW_QUOTATIONS, VIEW_ORDERS, VIEW_TEMPLATES)

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


def view_filter_state(filters):
    """A stored or wanted **view or button** filter (`controlId`, `filterType`, `values` per condition) in
    comparable form: the server fills in keys neither the translator nor the view editor sends (`minValue`,
    `emptyRule`, `advancedSetting` …) and returns an option list in the options' own order, so a filter is compared
    by what it *means* — never byte for byte.

    **Not `filter_state`.** Until 22 Sep 2026 this and §14's workflow-filter reader were both called that, and the
    later `def` replaced this one before anything ran: every view and button comparison read both sides as [] and
    agreed whatever was stored. `wf_filter_state` is the other one."""
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
    wrote = False
    # `C.upsert_views` re-sends the whole view unconditionally (three saves in the app log on 22 Sep 2026, all
    # identical), so it is called only when Templates is missing or differs from what `check` compares.
    if VIEW_TEMPLATES in live and templates_state(f, C.view_info(ws(), APP, live[VIEW_TEMPLATES])) == \
            templates_wanted(f, columns):
        print(f'  {VIEW_TEMPLATES}: already as specified; nothing saved')
        C.remember('views', KEY + VIEW_TEMPLATES, live[VIEW_TEMPLATES])
    else:
        for name, vid in C.upsert_views(ws(), APP, views, 'orders_views_pre_templates').items():
            C.remember('views', KEY + name, vid)
        wrote = True
    for name in FILTERED_VIEWS:
        vid, want = live[name], view_filter(f, VIEW_STATES[name])
        info = C.view_info(ws(), APP, vid)
        if view_filter_state(info.get('filters')) == view_filter_state(want):
            print(f"  {name}: already filtered to Status is any of {list(VIEW_STATES[name])} and "
                  f'{IS_TEMPLATE} not ticked; nothing saved')
        else:
            edit_view(vid, 'filters', want)
            back = C.view_info(ws(), APP, vid)
            if view_filter_state(back.get('filters')) != view_filter_state(want):
                sys.exit(f'{name}: the filter read back as {view_filter_state(back.get("filters"))}, wanted '
                         f'{view_filter_state(want)} — the save did not store')
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


def expected_rows():
    """{view name: the set of rowids it must return}, from every live order read with `record get` (Status and
    Is Template both come back on that path — CLAUDE.md, *Reading records*)."""
    f = C.fields(ws())
    label = {v: k for k, v in STATUS_KEYS.items()}
    want = {name: set() for name in VIEW_ROWS}
    for r in C.records(ws(), APP):
        d = read_record(ws(), r['rowid'])
        status = {label.get(k, k) for k in read_cell(f['Status'], d) or []}
        if read_cell(f[IS_TEMPLATE], d) == '1':
            want[VIEW_TEMPLATES].add(r['rowid'])
            continue
        for name in FILTERED_VIEWS:
            if status & set(VIEW_STATES[name]):
                want[name].add(r['rowid'])
    return want


def templates_state(f, info):
    """The Templates view as `views` writes it: name, filter, sort and columns."""
    return (info.get('name'),
            [(c['controlId'], c['filterType'], c.get('values')) for c in info.get('filters') or []],
            [(s['controlId'], s.get('isAsc')) for s in info.get('moreSort') or []],
            list(info.get('showControls') or []))


def templates_wanted(f, columns):
    return (VIEW_TEMPLATES, [(f[IS_TEMPLATE]['controlId'], C.EQ, ['1'])],
            [(f[TEMPLATE_NAME]['controlId'], True)], list(columns))


def report_view_rows():
    """Each view's rows beside the live orders whose Status (and Is Template) say it must return them."""
    live, bad, want = view_ids(), [], expected_rows()
    for name in VIEW_ROWS:
        if name not in live:
            bad.append(f'{name} is missing')
            continue
        got = {r['rowid'] for r in view_rows(live[name])}
        ok = got == want[name]
        print(f"  {'OK  ' if ok else 'DIFF'} {name} returns {len(got)} row(s), expected {len(want[name])} "
              f"(the live orders its filter names{'' if ok else f'; extra {sorted(got - want[name])}, missing {sorted(want[name] - got)}'})")
        if not ok:
            bad.append(f'{name} returns {len(got)} row(s), expected {len(want[name])}')
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
# **The match key is the app's Number, through ids.json `numbers`.** Orders' Number is an **auto-number control
# (type 33)**: a seeded order gets whatever the app's counter issues next and can never carry the tenant's
# S00010–S00022, so the first seed records the tenant name → assigned Number mapping under `numbers` — and from
# then on that Number is the key, because an auto-number is issued once and never changes. Whether Number should
# become a plain text control that carries Odoo's own numbers is the owner's decision; nothing here changes it.
#
# **It used to be (Customer, Quotation/Order Date), and that key broke on 22 Sep 2026.** Confirm writes
# `date_order = now` by design (`_prepare_confirmation_values`), so the owner's Confirm on app S00017 (tenant
# S00022) at 10:58 moved the order off its key: `check` called it "not on the worksheet" and `seed` would have
# created a duplicate. Any confirmed order does this. (Customer, Date) survives only as the fallback for a tenant
# order with no Number recorded yet — i.e. the very first seed, or a reseed after the owner cleared the records.
#
# **The fields a button owns are never compared on an order that exists** — Status, Quotation/Order Date and
# §6b's four (`BUTTON_OWNED`). The seed writes Status and the date when it *creates* an order; after that Confirm,
# Cancel, Set to Quotation and Mark as Sent own them, and a pressed button legitimately leaves them different from
# the seed. Comparing them would make `check` fail and `seed` revert the button's work on every confirmed order.
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


# Written by a button, not by the seed, once an order exists — see the section head.
BUTTON_OWNED = ('Status', 'Quotation/Order Date') + PART1


def order_key(customer_rowid, date):
    """The fallback match for a tenant order with no Number in ids.json yet: (Customer, Quotation/Order Date).
    Only sound before any button has run on the order — Confirm overwrites the date."""
    return (customer_rowid or '', date or '')


def live_orders(f):
    """({Number: (rowid, record)}, {(Customer, Date): (rowid, record)}) over every live order, each read with
    `record get` — `record list` drops what a control hides (CLAUDE.md, *Reading records*)."""
    by_number, by_key = {}, {}
    for r in C.records(ws(), APP):
        d = read_record(ws(), r['rowid'])
        by_number[read_cell(f['Number'], d)] = (r['rowid'], d)
        by_key[order_key((read_cell(f[CUSTOMER], d) or [None])[0], read_cell(f['Quotation/Order Date'], d))] = \
            (r['rowid'], d)
    return by_number, by_key


def match_order(o, customer_rowid, by_number, by_key):
    """(rowid, record) of the live order seeded from tenant order `o`, or (None, {}).

    The recorded Number first; (Customer, Date) only when ids.json has no Number for it, **or** its Number is
    not live (the owner cleared the records for a reseed and the Number is stale)."""
    number = hap.ids().get('numbers', {}).get(KEY + o['name'])
    if number and number in by_number:
        return by_number[number]
    return by_key.get(order_key(customer_rowid, o['date_order']), (None, {}))


def seed_compared(want):
    """`want` without the fields a button owns, for comparing against an order that already exists."""
    return {k: v for k, v in want.items() if k not in BUTTON_OWNED}


def seeded_orders():
    """{tenant name: (rowid, Number)} for every seeded order that is live, matched as `match_order` does."""
    f = C.fields(ws())
    data, _lines = seed_data()
    by_number, by_key = live_orders(f)
    contacts = titles(*CONTACTS)
    out = {}
    for o in data['orders']:
        rows = contacts.get(o['partner']) or []
        rowid, d = match_order(o, rows[0] if len(rows) == 1 else None, by_number, by_key)
        if rowid:
            out[o['name']] = (rowid, read_cell(f['Number'], d))
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
    """The tenant's twelve orders, matched by their app Number (ids.json `numbers`) and re-running to nothing.

    On an order that already exists, the fields a button owns (`BUTTON_OWNED`: Status, Quotation/Order Date and
    §6b's four) are **neither compared nor written** — Confirm overwrites the date and every button moves Status,
    so after a button has run those legitimately differ from the seed, and writing them back would undo it. They
    are written only when the seed creates the order.

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
    by_number, by_key = live_orders(f)
    gaps, numbers, problems, planned = {}, {}, [], []
    for o in data['orders']:
        want = order_want(f, o, index, gaps)
        rowid, record = match_order(o, (want.get(CUSTOMER) or [None])[0], by_number, by_key)
        if rowid:
            want = seed_compared(want)
        planned.append((o, want, rowid, record))
    if any(not rowid or differences(f, record, want) for _o, want, rowid, record in planned):
        hap.backup('orders_records_pre_seed', {rowid: d for rowid, d in by_number.values()})
    for o, want, rowid, record in planned:
        existed = bool(rowid)
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
            print(f"  {o['name']}: {'updated' if existed else 'created'} as {numbers[o['name']]} ({rowid})")
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


# ── 13 · the four state buttons, Confirm's guard, and Deliver ───────────────
#
# **Part 2 of the Orders button build** — 16-orders.md §3's twenty actions. Part 1 (§6b) appended the four
# controls these buttons write; these are the ones that are **nothing but a state change**, plus the one guard
# Odoo puts in front of a state change.
#
# **Four, not six, since 22 Sep 2026.** The owner deleted *Close Invoicing* and *Reopen Invoicing* and their
# workflows (6ab10714789584ded32f164d and 6ab10717886e6e7c8b38701c read back `deleted: True`), and made the
# Invoicing Closed checkbox itself editable ("110") and shown only on a Sales Order (RULE_EXPIRATION). This builder
# owns neither button any more and must never recreate them; their ids.json entries were removed.
#
# **Why buttons at all.** Status carries `fieldPermission` "100" — read-only and hidden on create — so nobody can
# type an order from a Quotation into a Sales Order. Before this step nothing in the app could move an order's
# state at all.
#
# Every condition below is Odoo's, read off the `sale.order` form arch and the server actions on casimir:
#
# | Button | `enableWhen` | writes | `isBatch` |
# |---|---|---|---|
# | Confirm            | Status is Quotation or Quotation Sent          | Status → Sales Order **and Quotation/Order Date → now** | yes |
# | Cancel             | Status is Quotation, Quotation Sent or Sales Order, **and Locked is not ticked** | Status → Cancelled | no |
# | Set to Quotation   | Status is Cancelled or Quotation Sent          | Status → Quotation, **and Signature, Signed By and Signed On cleared** | no |
# | Mark as Sent       | Status is Quotation                            | Status → Quotation Sent | yes |
# | Deliver            | Status is Sales Order (our judgment — see *Deliver* below) | each product line's Quantity Delivered → its own Quantity, through a sub-process | yes |
#
# `isBatch` mirrors each Odoo action's own `binding_view_types`: *Confirm Orders* (502) and *Mark as Sent* (501)
# are bound to the **list**, so their singular twins here carry batch and HAP gives us the batch form for free.
# The other two are header buttons on one record in Odoo and stay single here.
#
# **Cancel's `enableWhen` is the whole of Odoo's lock check.** `action_cancel` raises *"You cannot cancel a
# locked order. Please unlock it first."*; here the button is simply not offered while Locked is ticked, which is
# the same protection one dialog earlier, so the confirmation asks only whether to cancel the order — the shape
# `invoices.py`'s `MSG_CANCEL` takes.
#
# **Confirm overwrites the date unconditionally.** `_prepare_confirmation_values` returns
# `{'state': 'sale', 'date_order': fields.Datetime.now()}` — there is no "only if empty" branch, unlike the
# Invoice Date that `invoices.py step_numbering` fills, so the date write sits in the same update step as the
# Status write rather than behind a branch. The field is type **16** (DATE_TIME), not the 15 Invoices' date is.
#
# **Confirm does not number anything.** Number is an auto-number control here (16-orders.md §3), so none of
# `invoices.py`'s `sequence.mixin` chain is repeated.
#
# ── Confirm's guard ─────────────────────────────────────────────────────────
#
# Odoo refuses to confirm with *"Some order lines are missing a product, you need to correct them before going
# further."* when any line that is not a section, subsection or note — and not a down payment, which is not
# modelled here — has no Product (`_confirmation_error_message`, sale_order.py:1210).
#
# This **cannot be an `enableWhen`**: a button condition compares fields of the order, and this one aggregates
# over the Order Lines subtable. So it is built the way `invoices.py step_numbering` builds its count and
# `journals.py step_draftguard` builds Odoo's archive refusal — a 汇总 step over the child worksheet and a
# branch on its result:
#
#     Trigger by button
#       → Product lines with no product          a 汇总 (107) count over Order Lines: the Orders relation is
#                                                this order, Display Type is Product, Product is empty
#       → Is a product line missing its product?
#            · Yes (one or more) → Some order lines are missing a product      (站内通知) — the path ends
#            · No                → Confirm the order                          Status and the date
#       (nothing after the gateway)
#
# **The update has to sit inside the *No* path, not on the trunk.** A HAP branch *converges*: an empty path and a
# path whose steps have run both carry on to whatever follows the gateway, so an update left on the trunk would
# run for a refused order too. `C.upsert_buttons` builds it on the trunk (that is all a one-step button
# workflow is), and `ensure_product_guard` then moves it onto the No path with the same three-move dance
# `journals.py` uses — there is no "move a node" call in HAP: add a second update inside the path, copy the
# configuration onto it, read it back, and only then delete the old one. All of it happens on the draft, and
# `hap workflow rollback <pid> -y` restores the last published version.
#
# **The abort node is deliberately absent.** The first cut of the journals guard ended its refusal path in a
# 中止流程, which stops the run before the trunk update — and draws HAP's own untranslated **中止** toast
# (15 §6.6). With the update off the trunk the refusal path simply ends, so no abort is needed and no Chinese
# reaches the screen.
#
# **What the user sees when Confirm is refused, and the defect that comes with it** (15 §6.7, still open):
# the order is not confirmed, the notification *【Some order lines are missing a product】Some order lines are
# missing a product, you need to correct them before going further.* arrives in the notification centre — and
# the toast on screen is HAP's ordinary green tick, the button's `advancedSetting.tiptext`, which reads
# **"Operation completed"**. The run *completes*: the branch path ends, nothing aborts, and HAP cannot tell a
# guarded end from a successful one. Nothing in a workflow node changes that; the one knob that exists is the
# button's own `tiptext`, which is a single string for **both** outcomes, so wording it as a refusal would lie
# on every successful Confirm. It is recorded here and left to the owner, exactly as 15 §6.7 leaves the
# identical defect on Journals' Archive.

MSG_CANCEL = 'Are you sure you want to cancel this order?'
# Odoo's own text, verbatim (addons/sale/models/sale_order.py:1216).
MSG_NO_PRODUCT = 'Some order lines are missing a product, you need to correct them before going further.'

CONFIRM, CANCEL = 'Confirm', 'Cancel'
SET_TO_QUOTATION, MARK_AS_SENT = 'Set to Quotation', 'Mark as Sent'
# Close Invoicing and Reopen Invoicing were deleted by the owner on 22 Sep 2026 — see the section head.
BUTTONS = (CONFIRM, CANCEL, SET_TO_QUOTATION, MARK_AS_SENT)

# The owner's: their *Send Quotation* button with its own workflow. `step_buttons` compares it, byte for byte,
# before and after everything it writes — `buttons` never writes it. It is rewired by its own step, `send` (§16), at
# the owner's request of 22 Sep 2026: same button, same workflow, their nodes kept.
#
# **Their *Sign & Accept* SEARCH_BTN placeholder (type 49) is gone: the owner deleted it on 22 Sep 2026**, once §17
# was to build Sign & Accept as a Get Link workflow instead. Until then every step here compared it byte for byte and
# `check` failed without it; now nothing expects it, and `check` only notes it if that id ever comes back. It had been
# renamed from *Sign & Acccept* (three c's) the same day; no ids.json key ever carried it.
OWNERS_BUTTON = 'Send Quotation'
OWNERS_BUTTON_ID = '6ab0aac1e54d2a34fa4e7c1b'
OWNERS_WORKFLOW = '6ab0aac1789584ded3230fe1'
OWNERS_CONTROL, OWNERS_CONTROL_ID = 'Sign & Accept', '6ab0f80f7d58b0f449317238'     # deleted by the owner, 22 Sep
SEARCH_BTN = 49

# Each button's one update step. The name is what the workflow editor and `workflow structure` show.
STEP = {CONFIRM: 'Confirm the order',
        CANCEL: 'Cancel the order',
        SET_TO_QUOTATION: 'Set the order back to a quotation',
        MARK_AS_SENT: 'Mark the quotation as sent'}

# Confirm's guard, in order. The 站内通知's **name is part of what the user reads** — HAP renders the
# notification as 【<node name>】<message> — so it is named as the heading Odoo's dialog does not have.
COUNT_STEP = 'Product lines with no product'
PRODUCT_BRANCH = 'Is a product line missing its product?'
TELL_STEP = 'Some order lines are missing a product'
GUARD_STEPS = (COUNT_STEP, PRODUCT_BRANCH, TELL_STEP, STEP[CONFIRM])

DROPDOWN, RELATION, NUMBER, MEMBER = 11, 29, 6, 26
NOTICE, ABORT, BRANCH_PATH, UPDATE_NODE = 27, 30, 2, 6      # flowNodeType: 站内通知 · 中止流程 · a path · 数据操作
NUMBER_FX = 'number_fx_id'                     # a 汇总 step's own numeric result field
WORKSHEET_TOTAL = '107'                        # a workflow 汇总 step over a whole worksheet
# workflow conditionIds — a different enum from the worksheet filter's (BUILDING.md).
EMPTY, IS_ANY_OF, RELATION_EQ, AT_LEAST_ONE = '8', '1', '33', '14'
SYSTEM_NODE = '5d39140d381d42d20db0c4da'       # the fixed 系统 node: current time, trigger time, trigger user
LINES_ORDERS = '6ab0c740e43d174ab37535b1'      # Order Lines' back-relation to Orders — the 子表's own parent link

# The person who pressed the button. HAP's fixed 系统 node carries them as `triggeraid`; `kind: triggerUser` in
# hap-cli's DSL keys `uaid` off the trigger node instead, which on a button trigger reads back as **Last
# modifier** — the order's last editor rather than whoever clicked (journals.py, 21 Sep 2026).
TRIGGER_USER = {'type': 6, 'entityId': SYSTEM_NODE, 'entityName': 'System', 'roleId': 'triggeraid',
                'roleTypeId': 0, 'roleName': 'Trigger', 'controlType': MEMBER, 'avatar': '', 'count': 0,
                'appType': 100, 'actionId': ''}


def status_when(f, labels, also=None):
    """A button's `enableWhen`: *Status is any of `labels`*, optionally AND-ed with one more condition.

    The three buttons that test a second field go through the same builder rather than hand-rolling a group
    each: `translate_filter_group` flattens an AND group into the wire's condition list with `spliceType` 1 on
    every condition, so a second child *is* the AND. `status_is` is §9's — a view's and a button's condition on
    a single select are the same filterType 51 (BUILDING.md)."""
    children = [status_is(f, labels)]
    if also is not None:
        children.append(also)
    return {'type': 'group', 'logic': 'AND', 'children': children}


def switch_when(f, field, ticked):
    """A checkbox condition for a button's `enableWhen`: ticked (`eq`) or not ticked (`ne`) against "1" — the
    shape `not_a_template` already uses on this worksheet for the Templates filters."""
    return {'field': f[field]['controlId'], 'dataType': CHECKBOX,
            'operator': 'eq' if ticked else 'ne', 'value': ['1']}


BUTTON_DESC = {
    CONFIRM: 'Confirm this quotation as a sales order and set the Quotation/Order Date to now. Not possible while a '
             'product line has no product.',
    CANCEL: 'Cancel this order. Not available on a locked order: untick Locked first.',
    SET_TO_QUOTATION: 'Put a cancelled or already-sent order back to a plain quotation, clearing the '
                      'signature the customer left.',
    MARK_AS_SENT: 'Mark this quotation as sent without emailing it — for a quotation sent some other way.',
}


def button_specs(f):
    """The four buttons as `C.upsert_buttons` takes them: (action spec, the workflow's field writes, step name).

    The field writes here are only what `batch-add` puts on the new update step; `set_writes` rewrites every one
    of them afterwards in the shape the server actually stores, and is what the step verifies."""
    status = f['Status']['controlId']
    # A workflow update step stores a dropdown as the **bare option key** in `fieldValue`: a list is refused
    # with an HTTP 500 from flowNode/saveNode, and a JSON array string is accepted and stored empty
    # (BUILDING.md, found while building Invoices).
    to_status = lambda label: {'fieldId': status, 'type': DROPDOWN, 'value': STATUS_KEYS[label]}
    spec = lambda name, **kw: dict({'name': name, 'type': 'triggerWorkflow', 'desc': BUTTON_DESC[name]}, **kw)
    return [
        (spec(CONFIRM, isBatch=True,
              enableWhen=status_when(f, ['Quotation', 'Quotation Sent'])),
         [to_status('Sales Order')], STEP[CONFIRM]),
        (spec(CANCEL, isBatch=False, confirm=True, confirmMsg=MSG_CANCEL, sureName='Cancel order',
              cancelName='Back',
              enableWhen=status_when(f, ['Quotation', 'Quotation Sent', 'Sales Order'],
                                     switch_when(f, 'Locked', False))),
         [to_status('Cancelled')], STEP[CANCEL]),
        (spec(SET_TO_QUOTATION, isBatch=False,
              enableWhen=status_when(f, ['Cancelled', 'Quotation Sent'])),
         [to_status('Quotation')], STEP[SET_TO_QUOTATION]),
        (spec(MARK_AS_SENT, isBatch=True,
              enableWhen=status_when(f, ['Quotation'])),
         [to_status('Quotation Sent')], STEP[MARK_AS_SENT]),
    ]


def patch(field_id, kind, value='', node='', source='', system=False, clear=False):
    """One field write for an update step, in the shape the server actually stores (`invoices.patch`):

    a dropdown as its bare option key in `fieldValue`; a **text** taken from another node as the template
    `$<nodeId>-<fieldId>$`, again in `fieldValue`; every other type from a node as `nodeId` + `fieldValueId`, and
    from the fixed 系统 node with `nodeTypeId` / `nodeAppType` 100 — send `appType` instead and the server
    rewrites it, so the comparison below would re-save for ever.

    **Emptying a field needs `isClear: true`** — the editor's 清空. Sent as a plain empty `fieldValue` the entry
    is **dropped on save**: `fields` reads back without it, with no error, and the step writes nothing
    (BUILDING.md; measured again here on Set to Quotation's three signature fields, 21 Sep 2026)."""
    wire = {'fieldId': field_id, 'type': kind, 'addType': 0, 'fieldValue': value, 'fieldValueId': '', 'nodeId': ''}
    if clear:
        wire['isClear'] = True
    if system:
        wire.update(nodeId=SYSTEM_NODE, sureNodeId=SYSTEM_NODE, fieldValueId=source, nodeTypeId=100,
                    nodeAppType=100)
    elif node and kind == TEXT:
        wire['fieldValue'] = f'${node}-{source}$'
    elif node:
        wire.update(nodeId=node, sureNodeId=node, fieldValueId=source, nodeAppType=1)
    return wire


def writes_wanted(f):
    """{button name: [the field writes its update step must carry]} — the second column of §13's table.

    **Confirm's date is "now"**, taken from the 系统 node's `nowTime` the way `invoices.step_numbering` fills an
    empty Invoice Date — but with no branch in front of it, because `_prepare_confirmation_values` overwrites
    `date_order` unconditionally, and with type **16** (DATE_TIME) where Invoices' date is a 15."""
    status = f['Status']['controlId']
    date = f['Quotation/Order Date']['controlId']
    return {
        CONFIRM: [patch(status, DROPDOWN, value=STATUS_KEYS['Sales Order']),
                  patch(date, DATE_TIME, source='nowTime', system=True)],
        CANCEL: [patch(status, DROPDOWN, value=STATUS_KEYS['Cancelled'])],
        SET_TO_QUOTATION: [patch(status, DROPDOWN, value=STATUS_KEYS['Quotation']),
                           patch(f[SIGNATURE_FIELD]['controlId'], SIGN_PAD, clear=True),
                           patch(f[SIGNED_BY]['controlId'], TEXT, clear=True),
                           patch(f[SIGNED_ON]['controlId'], DATE_TIME, clear=True)],
        MARK_AS_SENT: [patch(status, DROPDOWN, value=STATUS_KEYS['Quotation Sent'])],
    }


# ── the workflow calls these four share with journals.py and invoices.py ─────

def nodes_by_name(pid):
    proc = hap.run('workflow', 'node', 'list', pid)
    return proc, {n['name']: n for n in proc['flowNodeMap'].values()}


def read_node(pid, node_id):
    """One node's configuration, unwrapped (`node get` answers either shape)."""
    got = hap.run('workflow', 'node', 'get', pid, node_id)
    return got.get('data', got)


def set_writes(pid, node, wanted, select_node):
    """Give an update step exactly these field writes, keeping the rest of its configuration; True when it
    changed. `select_node` is the node whose record is written: an update step pointed at another **update**
    step comes back `isException: true` and stores no field at all (BUILDING.md)."""
    d = read_node(pid, node['id'])
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
    hap.run('workflow', 'node', 'save', pid, node['id'], '--type', str(UPDATE_NODE), '-c', json.dumps(
        {'actionId': d.get('actionId', '2'), 'appId': d.get('appId') or ws(), 'appType': 1,
         'selectNodeId': select_node, 'fields': fields}, ensure_ascii=False), '-n', node['name'])
    back = read_node(pid, node['id'])
    if back.get('isException'):
        sys.exit(f"{node['name']}: reads back isException — `hap workflow rollback {pid} -y` restores the "
                 f'last published version')
    return True


def write_state(entry):
    """One stored field write in comparable form: the server adds `fieldValueName`, `sourceType` and friends."""
    return dict({k: entry.get(k) for k in ('fieldId', 'type', 'addType', 'fieldValue', 'fieldValueId', 'nodeId')},
                isClear=bool(entry.get('isClear')))


def writes_live(pid, node_id):
    return [write_state(x) for x in read_node(pid, node_id).get('fields') or []]


def branch_paths(proc, gateway_id, yes_next=None):
    """A gateway's two paths: the refusal path, then the clean one. Both carry a step once the guard is
    restructured, so "the one that carries a step" no longer tells them apart — the refusal path is the one
    that runs into `yes_next`, the 站内通知 node, and the caller passes its id. Before that node exists the
    fall-back is the old rule (journals.py)."""
    paths = [n for n in proc['flowNodeMap'].values()
             if n.get('typeId') == BRANCH_PATH and n.get('prveId') == gateway_id]
    if len(paths) != 2:
        sys.exit(f'{PRODUCT_BRANCH}: {len(paths)} paths, expected 2')
    yes = next((p for p in paths if p.get('nextId') == yes_next), None) if yes_next else None
    if not yes:
        yes = next((p for p in paths if p.get('nextId') not in (None, '', '99')), None) or paths[0]
    return yes, next(p for p in paths if p['id'] != yes['id'])


def save_path(pid, path, name, conditions):
    """A branch path's name and condition. `node get` returns them as `conditions`; `node save --type 2` wants
    `operateCondition`, and neither `batch-add` nor `node save -n` sets the name (BUILDING.md)."""
    got = read_node(pid, path['id'])
    key = lambda c: {k: c.get(k) for k in ('nodeId', 'filedId', 'conditionId')}
    changed = [[key(c) for c in g] for g in got.get('conditions') or []] != \
              [[key(c) for c in g] for g in conditions]
    if changed:
        hap.run('workflow', 'node', 'save', pid, path['id'], '--type', str(BRANCH_PATH),
                '-c', json.dumps({'operateCondition': conditions}, ensure_ascii=False), '-n', name)
    if path.get('name') != name:
        hap.run('workflow', 'node', 'rename', pid, path['id'], '-n', name)
        changed = True
    return changed


def save_notice(pid, node, content, account):
    """The 站内通知 step's message and its one recipient, read back first. The node's `flowNodeMap` "106" — the
    in-app-message channel config the server needs or the node counts as incomplete — goes back exactly as it
    came (BUILDING.md: without it publish fails with warningType 200)."""
    got = read_node(pid, node['id'])
    channel = got.get('flowNodeMap') or {}
    key = lambda a: {k: a.get(k) for k in ('type', 'entityId', 'roleId', 'controlType')}
    if got.get('sendContent') == content and channel.get('106', {}).get('name') == node['name'] \
            and [key(a) for a in got.get('accounts') or []] == [key(account)]:
        return False
    if '106' in channel:                           # the channel config carries the node name too
        channel['106']['name'] = node['name']
    hap.run('workflow', 'node', 'save', pid, node['id'], '--type', str(NOTICE), '-c', json.dumps(
        {'appType': got.get('appType', 1), 'selectNodeId': '', 'sendContent': content,
         'accounts': [account], 'formProperties': [], 'showTitle': True,
         'flowNodeMap': channel}, ensure_ascii=False), '-n', node['name'])
    back = read_node(pid, node['id'])
    if back.get('sendContent') != content:
        sys.exit(f"{node['name']}: message read back {back.get('sendContent')!r}")
    return True


# ── Confirm's guard: the count, the branch, the notice ──────────────────────

def guard_nodes():
    """The 汇总 count and the branch, for `batch-add` in front of Confirm's update step.

    The count is over **Order Lines**, the child worksheet, and its three conditions are Odoo's:
    the line belongs to this order (conditionId 33, a Relation compared with another node's record — here the
    trigger order's own rowid), its Display Type **is Product** (so a Section, Subsection or Note is exempt, as
    Odoo exempts a `display_type`), and its Product **is empty**. The server rewrites each condition's `nodeId`
    to the 汇总 node's own id, so what `left.node` says does not matter; what does is the comparison value."""
    line = lambda name, kind: {'node': {'nodeAlias': 'trigger'}, 'fieldId': CHILD[name], '_filedTypeId': kind}
    return [
        {'nodeAlias': 'orphans', 'nodeType': 'rollup', 'name': COUNT_STEP,
         'config': {'mode': 'worksheet', 'worksheet': LINES_WS, 'aggregate': 'count', 'filter': {
             'logic': 'and', 'items': [
                 {'left': {'node': {'nodeAlias': 'trigger'}, 'fieldId': LINES_ORDERS, '_filedTypeId': RELATION},
                  'op': RELATION_EQ,
                  'right': {'kind': 'field', 'node': {'nodeAlias': 'trigger'}, 'fieldId': 'rowid'}},
                 {'left': line('Display Type', DROPDOWN), 'op': IS_ANY_OF,
                  'right': {'kind': 'literal',
                            'values': [{'key': PRODUCT_LINE, 'value': 'Product', 'isDeleted': False}]}},
                 {'left': line('Product', RELATION), 'op': EMPTY},
             ]}}},
        {'nodeAlias': 'product_branch', 'nodeType': 'branch', 'name': PRODUCT_BRANCH, 'config': {'paths': [
            {'alias': 'missing', 'name': 'Yes', 'nodes': [
                {'nodeAlias': 'tell', 'nodeType': 'send_internal_notice', 'name': TELL_STEP,
                 'config': {'content': MSG_NO_PRODUCT, 'accounts': [dict(TRIGGER_USER)]}}]},
            {'alias': 'clean', 'name': 'No'}]}},
    ]


def at_least_one(count_node):
    """The Yes path's condition: the 汇总 step's own numeric result is 1 or more."""
    return [[{'nodeId': count_node, 'filedId': NUMBER_FX, 'filedValue': COUNT_STEP, 'filedTypeId': NUMBER,
              'conditionId': AT_LEAST_ONE, 'sourceType': 0, 'conditionValues': [{'value': '1'}]}]]


def ensure_product_guard(f):
    """Odoo's *"Some order lines are missing a product…"* in front of Confirm's update step. Returns True when
    something was written. Re-runnable: every node is matched by name and read back before it is written."""
    pid = hap.ids()['workflows'][KEY + CONFIRM]
    proc, byname = nodes_by_name(pid)
    if STEP[CONFIRM] not in byname:
        sys.exit(f'{STEP[CONFIRM]!r} is not in the {CONFIRM} workflow — `upsert_buttons` did not build it')
    print('  backup:', hap.backup('orders_confirm_workflow_pre_guard', proc))
    changed = COUNT_STEP not in byname
    if changed:
        # batch-add inserts after the trigger, so the update step that was the whole workflow becomes what the
        # branch converges on — and the move below then takes it off that trunk.
        hap.run('workflow', 'node', 'batch-add', pid, '--nodes', json.dumps(guard_nodes(), ensure_ascii=False),
                '--trigger-node-id', proc['startEventId'], '--trigger-alias', 'trigger')
        proc, byname = nodes_by_name(pid)
        for name in GUARD_STEPS:
            if name not in byname:
                sys.exit(f'{name!r} is not in the workflow after batch-add: {sorted(byname)}')
    yes, no = branch_paths(proc, byname[PRODUCT_BRANCH]['id'], byname[TELL_STEP]['id'])
    if byname[STEP[CONFIRM]].get('prveId') != no['id']:
        # Move the update off the converged trunk and onto the *No* path. There is no "move a node" call:
        # `node add --type 6 --after <the path node>` makes a second one inside the path — the path's `nextId`
        # becomes it — its configuration is copied over, read back, and only then is the old node deleted
        # (journals.py, 15 §6.6). All of it is on the draft; `workflow rollback <pid> -y` undoes it.
        old = byname[STEP[CONFIRM]]
        cfg = read_node(pid, old['id'])
        moving = STEP[CONFIRM] + ' (moving)'
        added = hap.run('workflow', 'node', 'add', pid, '--type', str(UPDATE_NODE), '-n', moving,
                        '--after', no['id'], '-a', cfg['actionId'], '--app-id', cfg['appId'])
        new_id = (added.get('addFlowNodes') or [{}])[0].get('id') or \
            next(n['id'] for n in nodes_by_name(pid)[0]['flowNodeMap'].values() if n.get('name') == moving)
        hap.run('workflow', 'node', 'save', pid, new_id, '--type', str(UPDATE_NODE), '-n', STEP[CONFIRM],
                '-c', json.dumps({'actionId': cfg['actionId'], 'appId': cfg['appId'],
                                  'appType': cfg.get('appType') or 1, 'selectNodeId': cfg['selectNodeId'],
                                  'fields': cfg['fields']}, ensure_ascii=False))
        back = read_node(pid, new_id)
        if back.get('isException') or [x['fieldId'] for x in back.get('fields') or []] != \
                [x['fieldId'] for x in cfg.get('fields') or []]:
            sys.exit(f'{STEP[CONFIRM]} on the No path reads back exception={back.get("isException")} '
                     f'fields={[x.get("fieldId") for x in back.get("fields") or []]} — nothing was deleted; '
                     f'`hap workflow rollback {pid} -y` restores the published version')
        hap.run('workflow', 'node', 'delete', pid, old['id'], '-y')
        proc, byname = nodes_by_name(pid)
        yes, no = branch_paths(proc, byname[PRODUCT_BRANCH]['id'], byname[TELL_STEP]['id'])
        changed = True
        print(f"  {STEP[CONFIRM]!r}: moved from the trunk onto the No path ({old['id']} -> {new_id})")
    for node in [n for n in proc['flowNodeMap'].values() if n.get('typeId') == ABORT]:
        # No abort is ever built here; one could only arrive by hand, and it is what draws the untranslated
        # 中止 toast the journals restructuring removed (15 §6.6).
        hap.run('workflow', 'node', 'delete', pid, node['id'], '-y')
        print(f"  abort node {node.get('name')!r} deleted — the refusal path just ends after the notice")
        changed = True
    if changed:
        proc, byname = nodes_by_name(pid)
        yes, no = branch_paths(proc, byname[PRODUCT_BRANCH]['id'], byname[TELL_STEP]['id'])
    changed |= save_notice(pid, byname[TELL_STEP], MSG_NO_PRODUCT, dict(TRIGGER_USER))
    changed |= save_path(pid, yes, 'Yes', at_least_one(byname[COUNT_STEP]['id']))
    changed |= save_path(pid, no, 'No', [])
    return changed


# ── Deliver: Part 3, the fifth button ───────────────────────────────────────
#
# Odoo's server action 504, `deliver_sold_quantity`, bound to the form and the list: it sets **each order line's
# Delivered quantity to that line's own Quantity** — the shortcut for an order that never passes through
# Inventory. The method is Enterprise/saas-only and is not in the 19.0 Community checkout, so its own guard cannot
# be read; the button here is **enabled when Status is Sales Order**, which is **our judgment, not Odoo's arch**
# (a quotation has nothing to deliver, a cancelled order must not be delivered).
#
# **The value differs per line**, so this is not one constant written to a set of records: a HAP update step over
# a get-multiple set writes the same value into every record, and there is no "this record's own field" among the
# values it can take. What HAP does have is the **sub-process (子流程, flowNodeType 16)**: it runs a child workflow
# once per record of a get-multiple set, and inside the child that record *is* the trigger — so an update step on
# the child's trigger can take the value from the child's trigger:
#
#     Trigger by button (on an order; isBatch, so once per selected order)
#       → This order's product lines        get-multiple (13 / 400) over Order Lines: Orders is this order,
#                                           Display Type is Product — sections, subsections and notes excluded
#       → Deliver each product line         sub-process (16) over that set, one line at a time (executeType 2),
#                                           the parent waiting for it (nextExecute)
#            └ child workflow "Deliver: one product line"
#                Trigger: one Order Line     (the record the sub-process hands in)
#                  → Delivered = Quantity    update the trigger line: Quantity Delivered ← the trigger line's
#                                            own Quantity
#
# Quantity Delivered is `101` read-only on the form; a workflow writes it regardless (CLAUDE.md). Nothing is
# written to Orders itself. The child workflow is published before the parent, as hap-cli's app creator does.
DELIVER = 'Deliver'
DELIVER_LINES = "This order's product lines"
DELIVER_EACH = 'Deliver each product line'
DELIVER_INNER = 'Deliver: one product line'
DELIVER_STEP = 'Delivered = Quantity'
DELIVER_STEPS = (DELIVER_LINES, DELIVER_EACH)
SUB_PROCESS, GET_MANY = 16, 13                  # flowNodeType
FROM_WORKSHEET, FROM_RECORD = '400', '401'      # get-multiple actionId · a value taken from the sub-process's record
SEQUENTIAL = 2                                  # a sub-process's executeType: 1 parallel · 2 one at a time
DELIVER_DESC = "Set every product line's Quantity Delivered to its Quantity. Available on a sales order only."
# (2) Proved by `selfdeliver` on this order: a Sales Order whose product lines carry different Quantities and
# no Delivered.
DELIVER_ORDER = 'S00006'
DELIVER_REFUSED_ON = 'S00013'                   # a Quotation: the button must be offered disabled there


def deliver_spec(f):
    return {'name': DELIVER, 'type': 'triggerWorkflow', 'desc': DELIVER_DESC, 'isBatch': True,
            'enableWhen': status_when(f, ['Sales Order'])}


def lines_filter(pid, node_id, trigger_id):
    """The get-multiple step's `filters`, in the shape the server stores for Confirm's count (read off it on
    22 Sep 2026): the line's Orders relation equals the triggering order's Record ID (conditionId 33), and its
    Display Type is any of Product (conditionId 1, the option as a value object). `batch-add` sends a search
    step's filter as `operateCondition`, which is not what the node keeps (BUILDING.md), so it is saved here."""
    base = {'nodeId': node_id, 'nodeType': GET_MANY, 'actionId': FROM_WORKSHEET, 'sourceType': 0}
    return [{'spliceType': 1, 'conditions': [[
        dict(base, filedId=LINES_ORDERS, filedValue='Orders', filedTypeId=RELATION, enumDefault=1,
             conditionId=RELATION_EQ, sourceType=33,
             conditionValues=[{'nodeId': trigger_id, 'controlId': 'rowid'}]),
        dict(base, filedId=CHILD['Display Type'], filedValue='Display Type', filedTypeId=DROPDOWN, enumDefault=0,
             conditionId=IS_ANY_OF,
             conditionValues=[{'value': {'key': PRODUCT_LINE, 'value': 'Product', 'isDeleted': False,
                                         'score': None, 'index': None}}]),
    ]]}]


def lines_filter_state(filters):
    """(field, conditionId, compared with) per condition — what `check` and the step compare."""
    return [(c.get('filedId'), c.get('conditionId'),
             [v.get('controlId') or (v.get('value') or {}).get('key') for v in c.get('conditionValues') or []],
             [v.get('nodeId') or '' for v in c.get('conditionValues') or []])
            for flt in filters or [] for g in flt.get('conditions') or [] for c in g]


def deliver_write(inner_start):
    """The child's one field write: Quantity Delivered (a number, type 6) from the child trigger's Quantity."""
    return dict(patch(CHILD['Quantity Delivered'], NUMBER, node=inner_start, source=CHILD['Quantity']),
                nodeActionId=FROM_RECORD)


def deliver_nodes():
    """The two parent steps and the child's one, for `batch-add` on an empty button workflow."""
    return [
        {'nodeAlias': 'lines', 'nodeType': 'get_multiple', 'name': DELIVER_LINES,
         'config': {'worksheet': LINES_WS, 'filter': {'logic': 'and', 'items': [
             {'left': {'node': {'nodeAlias': 'trigger'}, 'fieldId': LINES_ORDERS, '_filedTypeId': RELATION},
              'op': RELATION_EQ, 'right': {'kind': 'field', 'node': {'nodeAlias': 'trigger'}, 'fieldId': 'rowid'}},
             {'left': {'node': {'nodeAlias': 'trigger'}, 'fieldId': CHILD['Display Type'],
                       '_filedTypeId': DROPDOWN},
              'op': IS_ANY_OF, 'right': {'kind': 'literal',
                                         'values': [{'key': PRODUCT_LINE, 'value': 'Product', 'isDeleted': False}]}},
         ]}}},
        {'nodeAlias': 'each', 'nodeType': 'sub_process', 'name': DELIVER_EACH,
         'config': {'target': {'kind': 'record', 'node': {'nodeAlias': 'lines'}},
                    'process': {'name': DELIVER_INNER, 'nodes': [
                        {'nodeAlias': 'deliver', 'nodeType': 'update_record', 'name': DELIVER_STEP,
                         'config': {'worksheet': LINES_WS, 'target': {'node': {'nodeAlias': 'sub_trigger'}},
                                    'fields': [{'fieldId': CHILD['Quantity Delivered'], 'type': NUMBER,
                                                'valueRef': {'node': {'nodeAlias': 'sub_trigger'},
                                                             'fieldId': CHILD['Quantity']}}]}}]},
                    'execution': {'mode': 'sequential_each', 'continueAfterComplete': True}}},
    ]


def deliver_inner(pid, proc=None):
    """(the child workflow's id, its node list) — read off the sub-process step's `subProcessId`."""
    proc, byname = nodes_by_name(pid) if proc is None else (proc, {n['name']: n for n in proc['flowNodeMap'].values()})
    node = byname.get(DELIVER_EACH)
    if not node:
        return '', None
    inner = read_node(pid, node['id']).get('subProcessId') or ''
    return inner, (hap.run('workflow', 'node', 'list', inner) if inner else None)


def ensure_deliver_button(f):
    """The button itself: created once by name (`create-custom-action` ignores `--btn-id` and would add a
    duplicate), its workflow id recorded. Returns (workflow id, True when created)."""
    live = {b['name']: b for b in hap.listing('worksheet', 'custom-actions', ws())}
    key = KEY + DELIVER
    if DELIVER in live:
        pid = hap.ids().get('workflows', {}).get(key)
        if not pid:
            sys.exit(f'{DELIVER} exists ({live[DELIVER]["btnId"]}) but ids.json has no workflow for it — read '
                     f'its processId off the button before building')
        return pid, False
    hap.backup('orders_buttons_pre_deliver', list(live.values()))
    out = hap.run('worksheet', 'create-custom-action', ws(), '-a', APP, '--action-spec',
                  json.dumps(deliver_spec(f), ensure_ascii=False))
    data = out.get('data', out) if isinstance(out, dict) else {}
    pid = data.get('processId')
    if not pid:
        sys.exit(f'{DELIVER}: no processId in create-custom-action output: {out}')
    C.remember('workflows', key, pid)
    btn = next((b for b in hap.listing('worksheet', 'custom-actions', ws()) if b['name'] == DELIVER), None)
    if not btn:
        sys.exit(f'{DELIVER}: created, but it does not come back from custom-actions')
    C.remember('buttons', key, btn['btnId'])
    return pid, True


def ensure_deliver(f):
    """Build or repair Deliver's workflow and its child. Returns True when something was written. Re-runnable:
    the steps are added only to an empty workflow, the filter and the child's write are compared before they are
    saved, and the two workflows are published only when something changed."""
    pid, changed = ensure_deliver_button(f)
    proc, byname = nodes_by_name(pid)
    trigger = proc['startEventId']
    if proc['flowNodeMap'][trigger].get('nextId') in (None, '', '99'):
        hap.run('workflow', 'node', 'batch-add', pid, '--nodes', json.dumps(deliver_nodes(), ensure_ascii=False),
                '--trigger-node-id', trigger, '--trigger-alias', 'trigger')
        proc, byname = nodes_by_name(pid)
        changed = True
    missing = [n for n in DELIVER_STEPS if n not in byname]
    if missing:
        sys.exit(f'{DELIVER} workflow {pid}: {missing} missing ({sorted(byname)}) — it has steps this builder did '
                 f'not make; read it before writing')
    print('  backup:', hap.backup('orders_deliver_workflow', proc))
    lines = byname[DELIVER_LINES]
    got = read_node(pid, lines['id'])
    want = lines_filter(pid, lines['id'], trigger)
    if lines_filter_state(got.get('filters')) != lines_filter_state(want) or got.get('appId') != LINES_WS:
        hap.run('workflow', 'node', 'save', pid, lines['id'], '--type', str(GET_MANY), '-n', DELIVER_LINES,
                '-c', json.dumps({'actionId': FROM_WORKSHEET, 'appId': LINES_WS, 'appType': 1,
                                  'selectNodeId': '', 'filters': want, 'operateCondition': [],
                                  'execute': got.get('execute', False)}, ensure_ascii=False))
        back = read_node(pid, lines['id'])
        if lines_filter_state(back.get('filters')) != lines_filter_state(want):
            sys.exit(f'{DELIVER_LINES}: filter reads back {lines_filter_state(back.get("filters"))}, wanted '
                     f'{lines_filter_state(want)} — `hap workflow rollback {pid} -y` restores the published one')
        changed = True
    each = read_node(pid, byname[DELIVER_EACH]['id'])
    if (each.get('selectNodeId'), each.get('executeType')) != (lines['id'], SEQUENTIAL):
        sys.exit(f'{DELIVER_EACH}: runs over {each.get("selectNodeId")!r} with executeType '
                 f'{each.get("executeType")!r}, wanted {lines["id"]!r} one line at a time')
    inner, iproc = deliver_inner(pid, proc)
    if not inner:
        sys.exit(f'{DELIVER_EACH}: no child workflow (subProcessId empty)')
    C.remember('workflows', KEY + DELIVER_INNER, inner)
    ibyname = {n['name']: n for n in iproc['flowNodeMap'].values()}
    if DELIVER_STEP not in ibyname:
        sys.exit(f'{DELIVER_INNER} {inner}: no {DELIVER_STEP!r} ({sorted(ibyname)})')
    istart, step = iproc['startEventId'], ibyname[DELIVER_STEP]
    want_write = [write_state(deliver_write(istart))]
    d = read_node(inner, step['id'])
    inner_changed = False
    if [write_state(x) for x in d.get('fields') or []] != want_write or d.get('selectNodeId') != istart:
        hap.run('workflow', 'node', 'save', inner, step['id'], '--type', str(UPDATE_NODE), '-n', DELIVER_STEP,
                '-c', json.dumps({'actionId': '2', 'appId': LINES_WS, 'appType': 1, 'selectNodeId': istart,
                                  'fields': [deliver_write(istart)]}, ensure_ascii=False))
        inner_changed = True
    back = read_node(inner, step['id'])
    if back.get('isException') or [write_state(x) for x in back.get('fields') or []] != want_write:
        sys.exit(f'{DELIVER_STEP}: reads back exception={back.get("isException")} '
                 f'{[write_state(x) for x in back.get("fields") or []]}, wanted {want_write}')
    if changed or inner_changed:
        print(f'  {DELIVER_INNER}: {C.publish(inner)}')
        print(f'  {DELIVER}: {C.publish(pid)}')
    else:
        print(f'  {DELIVER}: already built; not re-published')
    return changed or inner_changed


def deliver_problems():
    """Deliver read back: the button, the parent's two steps and filter, the sub-process, the child's write."""
    problems = []
    f = hap.by_name(c for c in hap.controls(ws()) if c['type'] != C.TAB)
    b = next((x for x in hap.listing('worksheet', 'custom-actions', ws()) if x['name'] == DELIVER), None)
    if b is None:
        return [f'the {DELIVER!r} button is missing — run `buttons`']
    if button_state(b) != button_wanted(deliver_spec(f)):
        return [f'{DELIVER}: stored {button_state(b)}, wanted {button_wanted(deliver_spec(f))} — run `buttons`']
    pid = hap.ids().get('workflows', {}).get(KEY + DELIVER)
    if not pid:
        return [f'{DELIVER}: no workflow id in ids.json — run `buttons`']
    proc, byname = nodes_by_name(pid)
    steps = [n['name'] for n in proc['flowNodeMap'].values() if n.get('typeId') not in (None, 0, 100) and n.get('prveId')]
    if sorted(steps) != sorted(DELIVER_STEPS):
        return [f'{DELIVER}: workflow holds {steps}, wanted {list(DELIVER_STEPS)} — run `buttons`']
    fm, trigger = proc['flowNodeMap'], proc['startEventId']
    lines, each = byname[DELIVER_LINES], byname[DELIVER_EACH]
    if fm[trigger].get('nextId') != lines['id'] or lines.get('nextId') != each['id'] or \
            each.get('nextId') not in (None, '', '99'):
        problems.append(f'{DELIVER}: the chain is not trigger → {DELIVER_LINES!r} → {DELIVER_EACH!r} → end')
    got = read_node(pid, lines['id'])
    want = lines_filter(pid, lines['id'], trigger)
    if (got.get('actionId'), got.get('appId')) != (FROM_WORKSHEET, LINES_WS) or \
            lines_filter_state(got.get('filters')) != lines_filter_state(want):
        problems.append(f'{DELIVER_LINES}: {got.get("actionId")}/{got.get("appId")} '
                        f'{lines_filter_state(got.get("filters"))}, wanted {lines_filter_state(want)}')
    sub = read_node(pid, each['id'])
    if (sub.get('selectNodeId'), sub.get('executeType')) != (lines['id'], SEQUENTIAL):
        problems.append(f'{DELIVER_EACH}: over {sub.get("selectNodeId")!r} executeType {sub.get("executeType")!r}')
    inner, iproc = deliver_inner(pid, proc)
    istep = next((n for n in (iproc or {}).get('flowNodeMap', {}).values() if n['name'] == DELIVER_STEP), None)
    if not istep:
        problems.append(f'{DELIVER_INNER} {inner!r}: no {DELIVER_STEP!r}')
    else:
        d = read_node(inner, istep['id'])
        live = [write_state(x) for x in d.get('fields') or []]
        if d.get('isException') or live != [write_state(deliver_write(iproc['startEventId']))] or \
                d.get('selectNodeId') != iproc['startEventId']:
            problems.append(f'{DELIVER_STEP}: exception={d.get("isException")} {live}')
    if not problems:
        print(f"  OK  {DELIVER:<17} btnId={b['btnId']} isBatch={bool(b.get('isBatch'))} when Status is Sales Order\n"
              f'        then {DELIVER_LINES!r} (Orders is this order, Display Type is Product) → {DELIVER_EACH!r}, '
              f'one at a time → child {inner}: Quantity Delivered = its own Quantity')
    return problems


def buttons_offered(rowid):
    """{button name: offered?} for one order, **evaluated by the server**: `GetWorksheetBtns` with a `rowId`
    answers each button's `disabled` against that record's own values — the same call the record page makes, so it
    tests `enableWhen` without a browser (22 Sep 2026)."""
    from hap_cli.core.session import Session
    got = Session.load(None).api_call('Worksheet', 'GetWorksheetBtns',
                                      {'appId': APP, 'worksheetId': ws(), 'rowId': rowid, 'viewId': ''})
    got = got.get('data', got) if isinstance(got, dict) else got
    return {b['name']: not b.get('disabled') for b in got or []}


# ── what the owner owns, compared before and after ──────────────────────────

def owners_button_state():
    """The owner's *Send Quotation* button and its workflow, as one comparable blob: the custom action exactly
    as `custom-actions` returns it, plus every node of workflow 6ab0aac1789584ded3230fe1."""
    live = [b for b in hap.listing('worksheet', 'custom-actions', ws()) if b['name'] == OWNERS_BUTTON]
    if len(live) != 1 or live[0]['btnId'] != OWNERS_BUTTON_ID:
        sys.exit(f'{OWNERS_BUTTON!r} is not the one button {OWNERS_BUTTON_ID} — read the worksheet again '
                 f'before writing anything')
    proc = hap.run('workflow', 'node', 'list', OWNERS_WORKFLOW)
    return json.dumps({'button': live[0], 'workflow': proc}, ensure_ascii=False, sort_keys=True, default=str)


def untouched_state():
    """Everything this step must not change: the owner's button and its workflow, and the whole control set's
    signature — `step_buttons` writes no control at all, so *nothing* here may move."""
    return {'the owner\'s ' + OWNERS_BUTTON: owners_button_state(),
            'the control set': json.dumps(signature(hap.controls(ws())), ensure_ascii=False, sort_keys=True,
                                          default=str)}


def compare_untouched(before):
    after = untouched_state()
    moved = sorted(k for k in before if before[k] != after[k])
    if moved:
        sys.exit(f'{WORKSHEET}: {moved} changed while the buttons were built — nothing here writes a control '
                 f"or the owner's button, so this is a bug or someone else saved at the same moment")
    print(f'  untouched, byte for byte: {sorted(before)}')


# ── the step ────────────────────────────────────────────────────────────────

def button_state(b):
    """One stored button in comparable form: its condition, its batch flag and its confirmation.

    The confirmation is read as `enableConfirm` **or** `clickType` 2, because those are the two ways the same
    thing is written: the spec adapter sends 二次确认 as `clickType` 2, and the server stores it as `clickType`
    **1** with `enableConfirm` true — which is exactly what the owner's own *Send Quotation* carries. Comparing
    `clickType` alone would make this step's verification fail on every run."""
    return (view_filter_state(b.get('filters')), bool(b.get('isBatch')),
            bool(b.get('enableConfirm')) or b.get('clickType') == 2,
            b.get('workflowType'), b.get('confirmMsg') or '', b.get('sureName') or '',
            b.get('cancelName') or '')


def button_wanted(spec):
    """The same, from a spec: what `build_button_payload` will lower it to."""
    from hap_cli.core.action_spec_adapter import build_button_payload
    return button_state(build_button_payload(spec))


def step_buttons():
    """Odoo's four state buttons, their one-step workflows, and the product guard in front of Confirm; and
    Deliver (Part 3) with its get-multiple, its per-line sub-process and the child workflow — `ensure_deliver`.

    Writes **no control, no rule and no view**, and nothing at all on Order Lines: the whole of it is custom
    actions and their own workflows. The owner's *Send Quotation* button and its workflow are compared byte for
    byte before and after.

    Re-runnable: a button that exists by name is never re-created (`create-custom-action --action-spec` ignores
    `--btn-id` and would add a duplicate), every workflow node is matched by name and read back before it is
    written, and each workflow is republished only when something changed."""
    f = guard()
    for name in PART1:
        if name not in f:
            sys.exit(f'{name} is not on {WORKSHEET} — run `part1` first; two of these buttons write it')
    if f['Status'].get('fieldPermission') != READ_ONLY_PERMISSION:
        sys.exit(f"Status carries fieldPermission {f['Status'].get('fieldPermission')!r}, not "
                 f'{READ_ONLY_PERMISSION!r} — these buttons exist because nobody may type it')
    missing = [n for n in DISCOUNT_FIELDS if n not in f]
    if missing:
        sys.exit(f'{missing} are not on {WORKSHEET} — run `discountfields` first; {APPLY} reads them')
    discount_variant()                             # exits unless `discountproduct` has recorded it
    before = untouched_state()
    specs = button_specs(f)
    C.upsert_buttons(ws(), APP, specs, KEY, 'orders_buttons_pre_buttons')
    wanted, trouble = writes_wanted(f), []
    for spec, _, step in specs:
        name = spec['name']
        pid = hap.ids()['workflows'][KEY + name]
        proc, byname = nodes_by_name(pid)
        if step not in byname:
            sys.exit(f'{name}: {step!r} is not in workflow {pid} — {sorted(byname)}')
        changed = set_writes(pid, byname[step], wanted[name], proc['startEventId'])
        if name == CONFIRM:
            changed |= ensure_product_guard(f)
        print(f"  {name}: {C.publish(pid) if changed else 'already built; not re-published'}")
        live = writes_live(pid, nodes_by_name(pid)[1][step]['id'])
        if live != [write_state(x) for x in wanted[name]]:
            trouble.append(f'{name}: {step!r} stored {json.dumps(live, ensure_ascii=False)}, wanted '
                           f'{json.dumps([write_state(x) for x in wanted[name]], ensure_ascii=False)}')
    ensure_deliver(f)
    ensure_apply(f)
    specs_by_name = dict({s['name']: s for s, _, _ in specs}, **{DELIVER: deliver_spec(f), APPLY: apply_spec(f)})
    for b in hap.listing('worksheet', 'custom-actions', ws()):
        if b['name'] not in specs_by_name:
            continue
        spec = specs_by_name[b['name']]
        if button_state(b) != button_wanted(spec):
            trouble.append(f'{b["name"]}: stored {button_state(b)}, wanted {button_wanted(spec)}')
    trouble += deliver_problems()
    trouble += apply_problems(f)
    compare_untouched(before)
    if trouble:
        sys.exit('  ' + '\n  '.join(trouble))
    for name in BUTTONS + (DELIVER, DELIVER_INNER, APPLY, A_INNER, A_PRICE_INNER):
        print(C.structure(hap.ids()['workflows'][KEY + name]))
    return True


# ── 13b · driving all four from the CLI ─────────────────────────────────────
#
# `hap workflow trigger <processId> -s <rowid>` runs a button's workflow on one record, which is the only check
# of a button this repo can make without a browser (BUILDING.md). It runs the **workflow**, so it does not test
# `enableWhen` — whether the button is offered, greyed out or hidden is the UI test's — but it does test every
# write and the guard.
#
# **It runs on the tenant's own orders, because nothing may be created or deleted here.** Two of the twelve
# happen to be exactly the two cases needed, which is why no TEST order was made:
#
#   * **S00009** (a Quotation Sent whose two lines both carry a Product) is driven through all four buttons and
#     then put back to the Quotation Sent it started as, with its seeded date;
#   * **S00016** (a Quotation Sent with **two product lines that have no Product**) is the guard's own case: it
#     is confirmed and must come back **unchanged**.
#
# **This step is the proof the restore worked**, not `check`: it reads the five cells back against what it
# started from. `check` no longer compares the fields a button owns (Status, Quotation/Order Date and §6b's four)
# against the seed, because after a real Confirm they legitimately differ from it — see `step_seed`.
#
# It and `selfdeliver` are the two steps here that write records by design; neither is part of a "saves
# nothing" re-run.
CLEAN_ORDER, GUARDED_ORDER = 'S00009', 'S00016'
SIGNER, SIGNED_AT = 'TEST signer', '2026-09-20 10:11:12'


def by_number():
    """{Number: rowid} over the live orders."""
    f = C.fields(ws())
    return {read_cell(f['Number'], read_record(ws(), r['rowid'])): r['rowid'] for r in C.records(ws(), APP)}


def order_state(f, rowid):
    """The five cells these buttons (and the owner's Invoicing Closed checkbox) write, read back."""
    d = read_record(ws(), rowid)
    return {n: read_cell(f[n], d) for n in ('Status', 'Quotation/Order Date', INVOICING_CLOSED,
                                            SIGNED_BY, SIGNED_ON)}


def status_label(keys):
    label = {v: k for k, v in STATUS_KEYS.items()}
    return '/'.join(label.get(k, k) for k in keys or []) or '(empty)'


def press(name, rowid):
    hap.run('workflow', 'trigger', hap.ids()['workflows'][KEY + name], '-s', rowid)


def wait_until(f, rowid, wanted, seconds=30):
    for _ in range(seconds):
        state = order_state(f, rowid)
        if wanted(state):
            return state
        time.sleep(1)
    return order_state(f, rowid)


def write_cells(rowid, values):
    """`record update` — it ignores field permission and every interaction rule, which is how a read-only Status
    is put back (BUILDING.md)."""
    hap.run('worksheet', 'record', 'update', ws(), rowid, '-a', APP,
            '--fields-json', json.dumps(values, ensure_ascii=False))


def step_selfcheck():
    """Press all four buttons through the CLI on S00009 and put it back, then press Confirm on S00016 — the order
    whose two product lines have no Product — and prove it does not move."""
    f = guard()
    rows = by_number()
    for number in (CLEAN_ORDER, GUARDED_ORDER):
        if number not in rows:
            sys.exit(f'{number} is not on {WORKSHEET} — this step drives the tenant orders and creates none')
    clean, guarded = rows[CLEAN_ORDER], rows[GUARDED_ORDER]
    cid = lambda n: f[n]['controlId']
    problems = []

    # ── the guard: an order with two product lines and no Product must not move ──
    was = order_state(f, guarded)
    print(f'  {GUARDED_ORDER} before: {status_label(was["Status"])}, date {was["Quotation/Order Date"]!r} '
          f'(two of its five lines are product lines with no Product)')
    press(CONFIRM, guarded)
    after = wait_until(f, guarded, lambda s: s['Status'] != was['Status'], seconds=12)
    if after == was:
        print(f'  OK    {CONFIRM} on {GUARDED_ORDER} was refused: still {status_label(after["Status"])}, date '
              f'still {after["Quotation/Order Date"]!r}')
    else:
        problems.append(f'{CONFIRM} on {GUARDED_ORDER} moved the order: {was} -> {after}')

    # ── the happy path: every button in turn, then back where it started ──
    start = order_state(f, clean)
    if status_label(start['Status']) != 'Quotation Sent':
        sys.exit(f'{CLEAN_ORDER} is {status_label(start["Status"])}, expected Quotation Sent — put it back '
                 f'first (`seed` does not: Status is a button\'s field, not the seed\'s, once an order exists)')
    print(f'  {CLEAN_ORDER} before: {status_label(start["Status"])}, date {start["Quotation/Order Date"]!r}')
    now = time.strftime('%Y-%m-%d %H:%M:%S')
    got = {}
    for name, wanted in ((CONFIRM, 'Sales Order'), (CANCEL, 'Cancelled'), (SET_TO_QUOTATION, 'Quotation'),
                         (MARK_AS_SENT, 'Quotation Sent')):
        if name == CANCEL:
            # Give Set to Quotation something to clear. Signature itself is control type 42 and is not written
            # here — a signature pad's value is not something `record update` can put in honestly — so the
            # clear of Signature is the one write of the four this step cannot prove; the UI test signs and
            # then presses Set to Quotation.
            write_cells(clean, [{'id': cid(SIGNED_BY), 'value': SIGNER},
                                {'id': cid(SIGNED_ON), 'value': SIGNED_AT}])
        press(name, clean)
        state = wait_until(f, clean, lambda s, w=wanted: status_label(s['Status']) == w)
        got[name] = state
        print(f"  {name:<17} -> {status_label(state['Status']):<14} date={state['Quotation/Order Date']!r} "
              f"{INVOICING_CLOSED}={state[INVOICING_CLOSED]!r} {SIGNED_BY}={state[SIGNED_BY]!r} "
              f"{SIGNED_ON}={state[SIGNED_ON]!r}")
    # Odoo's `_prepare_confirmation_values` overwrites `date_order` unconditionally, so the date must have moved
    # off the seeded one and onto the confirmation time.
    confirmed = got[CONFIRM]['Quotation/Order Date']
    if status_label(got[CONFIRM]['Status']) != 'Sales Order':
        problems.append(f'{CONFIRM}: Status {status_label(got[CONFIRM]["Status"])}')
    if confirmed == start['Quotation/Order Date'] or confirmed[:10] != now[:10]:
        problems.append(f'{CONFIRM}: Quotation/Order Date is {confirmed!r} — it was '
                        f'{start["Quotation/Order Date"]!r} and the confirmation ran at {now}')
    else:
        print(f'  OK    {CONFIRM} moved Quotation/Order Date {start["Quotation/Order Date"]!r} -> '
              f'{confirmed!r} (the run was at {now})')
    if status_label(got[CANCEL]['Status']) != 'Cancelled':
        problems.append(f'{CANCEL}: Status {status_label(got[CANCEL]["Status"])}')
    requoted = got[SET_TO_QUOTATION]
    if status_label(requoted['Status']) != 'Quotation':
        problems.append(f'{SET_TO_QUOTATION}: Status {status_label(requoted["Status"])}')
    if (requoted[SIGNED_BY], requoted[SIGNED_ON]) != ('', ''):
        problems.append(f'{SET_TO_QUOTATION} did not clear the signature fields: '
                        f'{SIGNED_BY}={requoted[SIGNED_BY]!r} {SIGNED_ON}={requoted[SIGNED_ON]!r}')
    else:
        print(f'  OK    {SET_TO_QUOTATION} cleared {SIGNED_BY} and {SIGNED_ON} '
              f'(Signature itself is type {SIGN_PAD} and is for the UI test)')
    if status_label(got[MARK_AS_SENT]['Status']) != 'Quotation Sent':
        problems.append(f'{MARK_AS_SENT}: Status {status_label(got[MARK_AS_SENT]["Status"])}')

    # ── put the order back exactly as the seed wrote it ──
    write_cells(clean, [{'id': cid('Status'), 'value': [start['Status'][0]]},
                        {'id': cid('Quotation/Order Date'), 'value': start['Quotation/Order Date']},
                        {'id': cid(INVOICING_CLOSED), 'value': start[INVOICING_CLOSED]},
                        {'id': cid(SIGNED_BY), 'value': start[SIGNED_BY]},
                        {'id': cid(SIGNED_ON), 'value': start[SIGNED_ON]}])
    back = order_state(f, clean)
    if back != start:
        problems.append(f'{CLEAN_ORDER} was not restored: {start} -> {back}')
    else:
        print(f'  OK    {CLEAN_ORDER} restored: {status_label(back["Status"])}, date '
              f'{back["Quotation/Order Date"]!r} — `check` re-compares it against the seed')
    if problems:
        print('  selfcheck: ' + '\n             '.join(problems))
        sys.exit(1)
    print(f'  selfcheck: OK — all four buttons drive {CLEAN_ORDER} and the guard refuses {GUARDED_ORDER}')
    return True


# ── 13b2 · driving Deliver from the CLI ─────────────────────────────────────
#
# `selfdeliver` presses Deliver on DELIVER_ORDER through `workflow trigger`, as `selfcheck` presses the other
# four, reads every line of every order back through **both** read paths (`record get` and the `common.records`
# listing — neither is complete on its own, CLAUDE.md), and then **restores** each line's Quantity Delivered to
# what it was, so `check` stays green. It also asks the server which orders the button is offered on
# (`buttons_offered`), which is the one test of its `enableWhen` short of a browser. Like `selfcheck` it writes
# records by design and is not part of a "saves nothing" re-run.
LINE_FIELDS = ('Display Type', 'Quantity', 'Quantity Delivered')


def line_cells(f_lines, rowid):
    """Every control of one Order Line through `record get`, in `read_cell`'s comparable form."""
    d = read_record(LINES_WS, rowid)
    return {n: read_cell(c, d) for n, c in f_lines.items() if c['type'] in READERS}


def listed_lines(f_lines):
    """{line rowid: {name: value}} for every Order Line through the `common.records` listing."""
    out = {}
    for r in C.records(LINES_WS, APP):
        out[r['rowid']] = {n: READERS[c['type']](r.get(c['controlId'])) for n, c in f_lines.items()
                           if c['type'] in READERS}
    return out


def lines_of(listing, order_rowid):
    return [rid for rid, cells in listing.items() if cells.get('Orders') == [order_rowid]]


def wait_delivered(f_lines, rowids, seconds=60):
    for _ in range(seconds):
        got = {r: line_cells(f_lines, r) for r in rowids}
        if all(g['Quantity Delivered'] == g['Quantity'] for g in got.values()):
            return got
        time.sleep(1)
    return {r: line_cells(f_lines, r) for r in rowids}


def step_selfdeliver():
    """Press Deliver on DELIVER_ORDER and prove each product line's Quantity Delivered became its own Quantity
    and that nothing else moved; put every line back; and prove the button is offered on a Sales Order only."""
    f = guard()
    f_lines = hap.by_name(c for c in hap.controls(LINES_WS) if c['type'] != C.TAB)
    rows, problems = by_number(), []
    for number in (DELIVER_ORDER, DELIVER_REFUSED_ON):
        if number not in rows:
            sys.exit(f'{number} is not on {WORKSHEET} — this step drives the tenant orders and creates none')
    order = rows[DELIVER_ORDER]

    # ── where the button is offered, by the server's own evaluation ──
    for number, rowid in sorted(rows.items()):
        status = status_label(order_state(f, rowid)['Status'])
        offered = buttons_offered(rowid).get(DELIVER)
        if offered is None:
            problems.append(f'{DELIVER} is not among the buttons of {number}')
        elif offered != (status == 'Sales Order'):
            problems.append(f'{DELIVER} is {"offered" if offered else "not offered"} on {number} ({status})')
    quotation = status_label(order_state(f, rows[DELIVER_REFUSED_ON])['Status'])
    if quotation != 'Quotation':
        sys.exit(f'{DELIVER_REFUSED_ON} is {quotation}, expected a Quotation')
    if not problems:
        print(f'  OK    {DELIVER} is offered on every Sales Order and on nothing else — disabled on '
              f'{DELIVER_REFUSED_ON} ({quotation}), per GetWorksheetBtns with its rowId')

    # ── before ──
    before_list = listed_lines(f_lines)
    mine = lines_of(before_list, order)
    before = {r: line_cells(f_lines, r) for r in mine}
    product = [r for r in mine if before[r]['Display Type'] == [PRODUCT_LINE]]
    if len(product) < 2 or any(before[r]['Quantity Delivered'] not in (0, None) for r in product):
        sys.exit(f'{DELIVER_ORDER} has {len(product)} product line(s) with Delivered '
                 f'{[before[r]["Quantity Delivered"] for r in product]} — it needs two or more at 0')
    if status_label(order_state(f, order)['Status']) != 'Sales Order':
        sys.exit(f'{DELIVER_ORDER} is not a Sales Order')
    order_before = read_record(ws(), order)
    print(f'  {DELIVER_ORDER} before ({len(mine)} lines, {len(product)} product):')
    for r in mine:
        print(f"    {r}  {before[r]['Display Type']}  Quantity {before[r]['Quantity']}  "
              f"Delivered {before[r]['Quantity Delivered']} (listing: {before_list[r]['Quantity Delivered']})")

    # ── press ──
    press(DELIVER, order)
    after = wait_delivered(f_lines, product)
    after_list = listed_lines(f_lines)
    for r in mine:
        a, al = line_cells(f_lines, r), after_list.get(r, {})
        want = a['Quantity'] if r in product else before[r]['Quantity Delivered']
        ok = a['Quantity Delivered'] == want and al.get('Quantity Delivered') == want
        print(f"  {'OK  ' if ok else 'FAIL'}  {r}  Quantity {a['Quantity']}  Delivered {before[r]['Quantity Delivered']}"
              f" -> {a['Quantity Delivered']} (record get) / {al.get('Quantity Delivered')} (listing)")
        if not ok:
            problems.append(f'{r}: Delivered {a["Quantity Delivered"]}/{al.get("Quantity Delivered")}, wanted {want}')
        moved = sorted(n for n in before[r] if n != 'Quantity Delivered' and a[n] != before[r][n])
        if moved:
            problems.append(f'{r}: {moved} moved as well')
    others = sorted(r for r in before_list if r not in mine and before_list[r] != after_list.get(r))
    if others:
        problems.append(f'{len(others)} line(s) of other orders moved: {others}')
    else:
        print(f'  OK    none of the other {len(before_list) - len(mine)} Order Lines moved (listing, every field)')
    order_after = read_record(ws(), order)
    if {k: v for k, v in order_after.items() if k not in ('utime', 'uaid')} != \
            {k: v for k, v in order_before.items() if k not in ('utime', 'uaid')}:
        print(f'  note: the {DELIVER_ORDER} record itself reads differently after the run — only its roll-ups '
              f'should; compare: {sorted(k for k in order_after if order_after.get(k) != order_before.get(k))}')

    # ── put every line back ──
    for r in product:
        hap.run('worksheet', 'record', 'update', LINES_WS, r, '-a', APP, '--fields-json',
                json.dumps([{'id': CHILD['Quantity Delivered'], 'value': before[r]['Quantity Delivered'] or 0}]))
    back_list = listed_lines(f_lines)
    for r in mine:
        back = line_cells(f_lines, r)
        if back != before[r] or back_list.get(r) != before_list[r]:
            problems.append(f'{r} was not restored: {before[r]} -> {back} (listing {back_list.get(r)})')
    if not any('not restored' in p for p in problems):
        print(f'  OK    restored: every line of {DELIVER_ORDER} reads as before through both paths')
    if problems:
        print('  selfdeliver: ' + '\n               '.join(problems))
        sys.exit(1)
    print(f'  selfdeliver: OK — {DELIVER} set {len(product)} product lines of {DELIVER_ORDER} to their own '
          f'Quantity, moved nothing else, and is offered on Sales Orders only')
    return True


# ── 14 · Discount, Piece 1: the Discount product ────────────────────────────
#
# Odoo's discount wizard (addons/sale/wizard/sale_order_discount.py) writes a discount as **order lines** on a
# product of its own, created the first time the wizard runs (`_get_discount_product`) with
# `_prepare_discount_product_values`: name *Discount*, type *service*, invoice_policy *order*, list_price 0,
# **no taxes** (`taxes_id: None`) and the category *Services*. This step creates that product once, in Products,
# as a **record write only** — Products' controls are another administrator's and nothing here saves one.
#
# Its variant is made the way every product's is: Product Variants' automation *create a new product's variant*
# (variants.py §9, a worksheet-create trigger) runs on the create. The step waits for it, and falls back to
# `variants.py seed Discount` — the same one-variant upsert — only if the automation has not delivered.
#
# Divergences, recorded: Products has **no Invoicing Policy** control, so `invoice_policy 'order'` has nowhere to
# go; Odoo leaves `supplier_taxes_id` at the company's default purchase tax, which the tenant (expired) can no
# longer tell us, so Purchase Taxes stays empty like Sales Taxes. Odoo keeps the product on
# `company.sale_discount_product_id`; here its ids live in ids.json (`Products: Discount`,
# `Product Variants: Discount`), where the Apply Discount workflow reads the variant from (`discount_variant`).
PRODUCTS_WS = '6aa8ea0c4a22ad87b728cf0b'
VARIANTS_WS = '6aa90c161204328eb1af1b82'
DISCOUNT_PRODUCT = 'Discount'
SERVICES_CATEGORY = 'f762ae70-04c2-410e-aa18-a9f5abbbf5ae'      # Product Categories / Services
UNITS_UOM = '1c6ae984-a3ca-4721-be6f-e04481d8310c'              # Units & Packagings / Units — Odoo's default uom
PRODUCT_KEY, VARIANT_KEY = 'Products: ' + DISCOUNT_PRODUCT, 'Product Variants: ' + DISCOUNT_PRODUCT


def discount_variant():
    vid = hap.ids().get('records', {}).get(VARIANT_KEY)
    if not vid:
        sys.exit(f'ids.json has no {VARIANT_KEY!r} — run `discountproduct` first')
    return vid


def discount_product_values(pf):
    kinds = {o['value']: o['key'] for o in pf['Product Type']['options'] if not o.get('isDeleted')}
    cid = lambda n: pf[n]['controlId']
    return [{'id': cid('Name'), 'value': DISCOUNT_PRODUCT},
            {'id': cid('Product Type'), 'value': [kinds['Service']]},
            {'id': cid('Sales'), 'value': 1}, {'id': cid('Purchase'), 'value': 1},   # Odoo's defaults, both True
            {'id': cid('Sales Price'), 'value': '0'}, {'id': cid('Cost'), 'value': '0'},
            {'id': cid('Unit'), 'value': [UNITS_UOM]},
            {'id': cid('Category'), 'value': [SERVICES_CATEGORY]},
            {'id': cid('Internal Reference'), 'value': ''}, {'id': cid('Sales Description'), 'value': ''},
            {'id': cid('Weight'), 'value': '0'}, {'id': cid('Volume'), 'value': '0'},
            {'id': cid('Favorite'), 'value': 0}, {'id': cid('Active'), 'value': 1}]


def discount_product_problems(pid):
    """What the Discount product reads back as, against Odoo's values — both read paths."""
    import products as P
    got = P.read_product(pid)
    d = read_record(PRODUCTS_WS, pid)
    pf = C.fields(PRODUCTS_WS)
    listing = next((r for r in C.records(PRODUCTS_WS, APP) if r['rowid'] == pid), {})
    want = dict(name=DISCOUNT_PRODUCT, type='Service', sale_ok=True, purchase_ok=True, active=True,
                list_price=0, standard_price=0, uom='Units')
    problems = [f'{DISCOUNT_PRODUCT}: {k} reads {got.get(k)!r}, wanted {v!r}' for k, v in want.items() if got.get(k) != v]
    for name, wanted in (('Category', [SERVICES_CATEGORY]), ('Sales Taxes', []), ('Purchase Taxes', [])):
        c = pf[name]
        for path, value in (('record get', read_cell(c, d)), ('listing', relation_ids(listing.get(c['controlId'])))):
            if value != wanted:
                problems.append(f'{DISCOUNT_PRODUCT}: {name} reads {value} through {path}, wanted {wanted}')
    return problems


def find_discount_product():
    name = C.fields(PRODUCTS_WS)['Name']['controlId']
    rows = [r['rowid'] for r in C.records(PRODUCTS_WS, APP) if r.get(name) == DISCOUNT_PRODUCT]
    if len(rows) > 1:
        sys.exit(f'{len(rows)} products are named {DISCOUNT_PRODUCT!r}: {rows} — resolve by hand first')
    return rows[0] if rows else None


def discount_variant_of(pid, seconds=0):
    """The Discount product's own variant (its oldest), waiting up to `seconds` for automation A."""
    import variants as V
    for _ in range(max(seconds, 1)):
        product = C.fields(VARIANTS_WS)['Product']['controlId']
        mine = [r['rowid'] for r in C.records(VARIANTS_WS, APP) if relation_ids(r.get(product)) == [pid]]
        if mine:
            got = sorted((V.read_variant(r) for r in mine), key=lambda v: (v['created'], v['rowid']))
            return got[0]['rowid'], len(got)
        if seconds:
            time.sleep(1)
    return None, 0


def discount_variant_problems(pid, vid):
    """The variant against its product, as variants.py compares every one (copies, lookups, Display Name).
    Lookups settle asynchronously after a create, so a fresh variant gets a few seconds."""
    import products as P
    import variants as V
    for _ in range(15):
        diffs = V.product_differences(V.read_variant(vid), P.read_product(pid))
        if not diffs:
            return []
        time.sleep(1)
    return [f'the {DISCOUNT_PRODUCT} variant {vid} differs from its product: {diffs}']


def step_discountproduct():
    """Create Odoo's Discount product once, see that its variant exists, and record both ids."""
    import variants as V
    pid = find_discount_product()
    if pid is None:
        values = discount_product_values(C.fields(PRODUCTS_WS))
        pid = C.row_id(hap.run('worksheet', 'record', 'create', PRODUCTS_WS, '-a', APP,
                               '--fields-json', json.dumps(values, ensure_ascii=False)))
        if not pid:
            sys.exit(f'{DISCOUNT_PRODUCT}: record create returned no rowid')
        print(f'  created the product {DISCOUNT_PRODUCT}: {pid}')
    else:
        print(f'  the product {DISCOUNT_PRODUCT} exists: {pid}')
    problems = discount_product_problems(pid)
    if problems:
        sys.exit('\n'.join(problems) + '\n  — the product is not written again by this step; correct it by hand')
    if hap.ids().get('records', {}).get(PRODUCT_KEY) != pid:
        C.remember('records', PRODUCT_KEY, pid)
    vid, count = discount_variant_of(pid, seconds=30)
    if vid is None:
        print("  automation A delivered no variant in 30 s — running variants.py's seed for this product only")
        V.step_seed(DISCOUNT_PRODUCT)
        vid, count = discount_variant_of(pid, seconds=10)
    if vid is None or count != 1:
        sys.exit(f'{DISCOUNT_PRODUCT}: {count} variant(s) — wanted exactly one')
    if hap.ids().get('records', {}).get(VARIANT_KEY) != vid:
        C.remember('records', VARIANT_KEY, vid)
    problems = discount_variant_problems(pid, vid)
    if problems:
        sys.exit('\n'.join(problems))
    print(f'  OK    {DISCOUNT_PRODUCT}: product {pid}, variant {vid} — Service, RM 0.00, no taxes, Services, Units')


# The proof Piece 2 stands on: a discount line is an ordinary product line. One is added to DISCOUNT_ORDER with
# Unit Price −100 and 10% G, read back through both paths — Subtotal −100, Tax Amount −10, Total −110 — and the
# order's three roll-ups must drop by exactly that; then the line is deleted (soft, to the recycle bin: it is this
# step's own test data) and the order must read as before.
DISCOUNT_ORDER = 'S00006'                       # a Sales Order with three lines at 10% G and one at 8% S
TAX_10G = '1fd5f54c-c22a-45d9-8c74-38d29b52b183'
TOTALS = ('Untaxed Amount', 'Tax', 'Total')


def order_totals(f, rowid):
    """The three roll-ups through `record get` and through the listing."""
    d = read_record(ws(), rowid)
    row = next((r for r in C.records(ws(), APP) if r['rowid'] == rowid), {})
    return ({n: read_cell(f[n], d) for n in TOTALS},
            {n: number_of(row.get(f[n]['controlId'])) for n in TOTALS})


def wait_totals(f, rowid, wanted, seconds=40):
    for _ in range(seconds):
        got = order_totals(f, rowid)
        if got[0] == wanted and got[1] == wanted:
            return got
        time.sleep(1)
    return order_totals(f, rowid)


def step_discountline():
    f = guard()
    f_lines = hap.by_name(c for c in hap.controls(LINES_WS) if c['type'] != C.TAB)
    order = by_number()[DISCOUNT_ORDER]
    before = order_totals(f, order)
    if before[0] != before[1]:
        sys.exit(f'{DISCOUNT_ORDER}: the two read paths disagree before anything is written: {before}')
    print(f'  {DISCOUNT_ORDER} before: {before[0]}')
    values = [{'id': CHILD['Orders'], 'value': [order]}, {'id': CHILD['Display Type'], 'value': [PRODUCT_LINE]},
              {'id': CHILD['Product'], 'value': [discount_variant()]},
              {'id': CHILD['Description'], 'value': 'TEST discount line'},
              {'id': CHILD['Quantity'], 'value': '1'}, {'id': CHILD['Unit Price'], 'value': '-100'},
              # Discount % must be written as 0: Subtotal's formula is not null-as-zero, so an empty Discount
              # computes Subtotal — and with it Tax Amount, Total and the order's roll-ups — **empty**.
              {'id': CHILD['Discount'], 'value': '0'},
              {'id': CHILD['Taxes'], 'value': [TAX_10G]}, {'id': CHILD['Sequence'], 'value': '999'}]
    line = C.row_id(hap.run('worksheet', 'record', 'create', LINES_WS, '-a', APP,
                            '--fields-json', json.dumps(values, ensure_ascii=False)))
    problems = []
    try:
        time.sleep(3)
        got, listed = line_cells(f_lines, line), listed_lines(f_lines).get(line, {})
        for n, want in (('Subtotal', -100.0), ('Tax Amount', -10.0), ('Total', -110.0)):
            ok = got[n] == want and listed.get(n) == want
            print(f"  {'OK  ' if ok else 'FAIL'}  line {n}: {got[n]} (record get) / {listed.get(n)} (listing), "
                  f'wanted {want}')
            if not ok:
                problems.append(f'line {n} {got[n]}/{listed.get(n)}, wanted {want}')
        wanted = {n: round(before[0][n] + d, 2) for n, d in zip(TOTALS, (-100, -10, -110))}
        after = wait_totals(f, order, wanted)
        for n in TOTALS:
            ok = after[0][n] == wanted[n] and after[1][n] == wanted[n]
            print(f"  {'OK  ' if ok else 'FAIL'}  {DISCOUNT_ORDER} {n}: {before[0][n]} -> {after[0][n]} (record get) / "
                  f'{after[1][n]} (listing), wanted {wanted[n]}')
            if not ok:
                problems.append(f'{DISCOUNT_ORDER} {n} {after}, wanted {wanted[n]}')
    finally:
        hap.run('worksheet', 'record', 'delete', LINES_WS, '--row-ids', line, '-a', APP, '-y')
    back = wait_totals(f, order, before[0])
    if back != before:
        problems.append(f'{DISCOUNT_ORDER} after the delete: {back}, wanted {before}')
    else:
        print(f'  OK    the test line {line} deleted; {DISCOUNT_ORDER} reads {back[0]} again through both paths')
    if problems:
        print('  discountline: ' + '\n                '.join(problems))
        sys.exit(1)
    print('  discountline: OK — a Discount line is an ordinary product line and the roll-ups carry it')


# ── 14b · Discount, Piece 2: the wizard's two fields ─────────────────────────
#
# Odoo's discount is a **transient wizard** (`sale.order.discount`): a dialog holding discount_type and the
# percentage or amount, gone once applied. HAP has no transient record a button can open, so the two inputs live
# on the order itself and the Apply Discount button reads them. Only Odoo's `so_discount` and `amount` modes are
# offered: its third, `sol_discount` *On All Order Lines*, writes each line's own Discount %, which the subtable's
# Batch Operation already does. Appended with `C.append_controls` (the server mints the ids, nothing else is
# re-sent); **placement is the owner's** — `add-fields` parks a new control at row 9999.
DISCOUNT_TYPE, DISCOUNT_VALUE = 'Discount Type', 'Discount Value'
DISCOUNT_FIELDS = (DISCOUNT_TYPE, DISCOUNT_VALUE)
GLOBAL_DISCOUNT, FIXED_AMOUNT = 'Global Discount', 'Fixed Amount'      # Odoo's labels for so_discount · amount
DISCOUNT_OPTIONS = (GLOBAL_DISCOUNT, FIXED_AMOUNT)
DISCOUNT_ALIAS = {DISCOUNT_TYPE: 'discount_type', DISCOUNT_VALUE: 'discount_value'}
DISCOUNT_PLACE = {DISCOUNT_TYPE: (30, 0, 6), DISCOUNT_VALUE: (30, 1, 6)}   # intent: side by side, above the
                                                                           # totals; only `size` survives
DISCOUNT_DESC = {
    DISCOUNT_TYPE: 'Global Discount takes Discount Value as a percentage off the order. Fixed Amount takes it as an '
                   'amount in RM off the order total, tax included. Press Apply Discount to add the discount lines. '
                   "To discount single lines, use the lines' Discount instead.",
    # The owner's own text, typed in the designer on 22 Sep 2026 — kept exactly as stored (typos included) so
    # `check` does not fail on it and no step writes over it. A corrected wording is the owner's to choose.
    DISCOUNT_VALUE: 'EIther % (e.g. 10%) or Whole Amound (e.g. 100)',
}


def discount_controls():
    return {
        DISCOUNT_TYPE: C.control('DROP_DOWN', DISCOUNT_TYPE, DISCOUNT_PLACE[DISCOUNT_TYPE],
                                 alias=DISCOUNT_ALIAS[DISCOUNT_TYPE], hint='', desc=DISCOUNT_DESC[DISCOUNT_TYPE],
                                 options=list(DISCOUNT_OPTIONS)),
        DISCOUNT_VALUE: C.control('NUMBER', DISCOUNT_VALUE, DISCOUNT_PLACE[DISCOUNT_VALUE],
                                  alias=DISCOUNT_ALIAS[DISCOUNT_VALUE], hint='', desc=DISCOUNT_DESC[DISCOUNT_VALUE],
                                  extra={'dot': 2}),
    }


def discount_fields_problems(f):
    problems = []
    for n in DISCOUNT_FIELDS:
        c = f.get(n)
        if c is None:
            problems.append(f'{n} is not on {WORKSHEET} — run `discountfields`')
            continue
        want = {'type': DROPDOWN if n == DISCOUNT_TYPE else NUMBER, 'alias': DISCOUNT_ALIAS[n],
                'desc': DISCOUNT_DESC[n], 'required': False}
        got = {k: c.get(k) for k in want}
        if got != want:
            problems.append(f'{n}: {({k: v for k, v in got.items() if want[k] != v})}, wanted '
                            f'{({k: v for k, v in want.items() if got[k] != v})}')
        if n == DISCOUNT_TYPE:
            labels = [o['value'] for o in c.get('options') or [] if not o.get('isDeleted')]
            if labels != list(DISCOUNT_OPTIONS):
                problems.append(f'{n}: options {labels}, wanted {list(DISCOUNT_OPTIONS)}')
        if n == DISCOUNT_VALUE and c.get('dot') != 2:
            problems.append(f'{n}: {c.get("dot")} decimals, wanted 2')
        if (f.get(n) or {}).get('controlId') and hap.ids().get('controls', {}).get(KEY + n) != c['controlId']:
            problems.append(f'{n}: ids.json does not hold {c["controlId"]} — run `discountfields`')
    return problems


def step_discountfields():
    """Append Discount Type and Discount Value if they are missing, and read them back."""
    f = guard()
    missing = [n for n in DISCOUNT_FIELDS if n not in f]
    if missing:
        hap.backup('orders_controls_pre_discount', hap.controls(ws()))
        b = discount_controls()
        C.append_controls(ws(), [b[n] for n in missing])
        f = C.fields(ws())
        for n in missing:
            if n not in f:
                sys.exit(f'{n} did not come back from the worksheet — the append did not store')
            print(f"  added {n}: {f[n]['controlId']} (t{f[n]['type']}, row {f[n].get('row')})")
    else:
        print(f'  {list(DISCOUNT_FIELDS)} are already on {WORKSHEET}; nothing appended')
    for n in DISCOUNT_FIELDS:
        if hap.ids().get('controls', {}).get(KEY + n) != f[n]['controlId']:
            C.remember('controls', KEY + n, f[n]['controlId'])
    problems = discount_fields_problems(f)
    if problems:
        sys.exit('\n'.join(problems) + '\n  — not repaired automatically: read the control before a pinned save')
    for n in DISCOUNT_FIELDS:
        c = f[n]
        print(f"  OK  {n:<15} {c['controlId']} t{c['type']} alias={c['alias']} r{c.get('row')}c{c.get('col')} "
              f"s{c.get('size')}" + (f" options={[o['value'] for o in c['options'] if not o.get('isDeleted')]}"
                                    if c.get('options') else f" dot={c.get('dot')}"))
    parked = [n for n in DISCOUNT_FIELDS if f[n].get('row') == 9999]
    if parked:
        print('  placement outstanding — the owner places these in the designer; intended (row, col, size): '
              + ', '.join(f'{n} {DISCOUNT_PLACE[n]}' for n in parked))


# ── 14c · Discount, Piece 2: the Apply Discount button ──────────────────────
#
# Odoo's `sale.order.discount` → `_create_discount_lines`: one negative line on the Discount product **per tax
# combination** of the order's product lines, `price_unit` the group's share, `tax_ids` the group's taxes,
# quantity 1, sequence 999. Grouped here, not one line per product line — the fallback the brief allowed was not
# needed:
#
#     Trigger by button (one order)
#       → The Discount product            get-single, Product Variants, rowid = ids.json's variant
#       → This order's discount lines     get-multiple: Orders is this order, Product is the Discount variant
#       → Remove them                     delete, to the recycle bin — so the button can be pressed again
#       → Is there a discount to apply?   No: Discount Value empty, or 0, or Discount Type empty (nothing more)
#         Yes ↓
#           This order's product lines    get-multiple (fetched once): Orders is this order, Display Type Product
#           Their total, tax included     worksheet total (107): Σ Total of those lines, after the removal
#           The discount's label          "Discount 10.00%" (Global) / "Discount" (Fixed) — see below
#           What the discount is taken over   "100" (Global) / Their total, tax included (Fixed), as text
#           Add each product line to its tax group's discount line   sub-process, one line at a time, passing
#             └ child A "Apply Discount: one product line"            the label as a parameter
#                 The Discount product · The line's taxes (its own Taxes, in the taxes' Sequence order)
#                 The line's tax group    code block: label + "- On products with the following taxes " +
#                                         the names joined by ", " — Odoo's multi-combination line name
#                 Its tax group's discount line   get-single: same order, Discount product, that Description
#                   Found     → Unit Price −= the line's Subtotal
#                   Not found → create it: Unit Price −Subtotal, the line's Taxes, qty 1, seq 999, Discount 0,
#                               Units, Display Type Product
#           This order's discount lines, one per tax group   → How many tax groups (object count)
#           Only one tax group?  Yes → Description = the plain label (Odoo's single-combination name)
#           Price each tax group's discount line   sub-process, passing Discount Value and the divisor
#             └ child B "Apply Discount: one tax group"
#                 The discount on this tax group   number formula, 2 decimals: Unit Price × Value ÷ divisor
#                 Set its Unit Price
#
# So a group's line first accumulates −(the group's subtotal), then is priced once: round(group × Value ÷ 100) for
# Global Discount, round(Value × group ÷ Σ product lines' Total) for Fixed Amount — Odoo's rounding per group, not
# per line. That is Odoo 19's `account.tax._reduce_base_lines_to_target_amount`: `percentage = amount ÷
# total_amount`, where total_amount is Σ(total_excluded + tax_amount) — the **tax-included** total — and each tax
# group's discount base is its untaxed subtotal × percentage. Its tax is then the group's rate on that base, so the
# discount lines' Totals sum to −Value and **the order's Total drops by the amount**, as in Odoo. The Fixed
# denominator is summed **inside the run, after the removal**, never read off the order's Total roll-up.
#
# Divergences from Odoo, each deliberate:
#   * the button is **Apply Discount**, not Odoo's *Discount*, so it is not mistaken for the lines' Discount %;
#   * it **replaces** this order's Discount lines (any line on the Discount product) instead of adding more —
#     Odoo's wizard stacks a second discount when pressed twice; the owner chose replace, and Value 0 removes;
#   * the wizard is two fields on the order (§14b), not a dialog; Odoo's third mode, On All Order Lines, is the
#     subtable's Batch Operation on Discount %;
#   * Odoo nudges the discount lines so a Fixed Amount reconciles to the cent (`_reduce_base_lines_to_target_amount`
#     spreads the rounding delta; the lines also carry `extra_tax_data`); nothing here adjusts cents — the order's
#     Total can miss the amount by a cent or so, and `selfdiscount` reports the residual exactly. Until 22 Sep 2026
#     the amount was spread over the **untaxed** subtotals, so RM 1,000 off took ~RM 1,099 off the Total;
#   * Odoo refuses a percentage above 100 (`_check_discount_amount`); nothing here does;
#   * the wizard's lines carry `extra_tax_data` so their tax is the exact complement of the order's; here each
#     discount line's tax is its own Subtotal × rate, like every other line.
APPLY = 'Apply Discount'
APPLY_DESC = ('Add discount lines for the Discount Type and Discount Value, replacing any discount lines already on '
              'the order. With Discount Value empty or 0, removes them. Not available on a locked or cancelled order.')
# the parent's steps
A_VARIANT = 'The Discount product'
A_OLD = "This order's discount lines"
A_REMOVE = 'Remove them'
A_BRANCH = 'Is there a discount to apply?'
A_LINES = "This order's product lines"
A_LABEL = "The discount's label"
A_EACH = "Add each product line to its tax group's discount line"
A_GROUPS = "This order's discount lines, one per tax group"
A_COUNT = 'How many tax groups'
A_PRICE = "Price each tax group's discount line"
A_SINGLE = 'One tax group: plain description'
A_ONE = 'Only one tax group?'
# the two children
A_INNER = 'Apply Discount: one product line'
A_PRICE_INNER = 'Apply Discount: one tax group'
DELETE_NODE = '3'
UNITS_LINE = UNITS_UOM


def apply_spec(f):
    """Offered unless Locked is ticked or Status is Cancelled — Odoo's `invisible="locked or state == 'cancel'"`."""
    return {'name': APPLY, 'type': 'triggerWorkflow', 'desc': APPLY_DESC, 'isBatch': False,
            'enableWhen': {'type': 'group', 'logic': 'AND', 'children': [
                {'field': f['Status']['controlId'], 'dataType': DROPDOWN, 'operator': 'ne',
                 'value': [STATUS_KEYS['Cancelled']]},
                switch_when(f, 'Locked', False)]}}


def ensure_apply_button(f):
    live = {b['name']: b for b in hap.listing('worksheet', 'custom-actions', ws())}
    key = KEY + APPLY
    if APPLY in live:
        pid = hap.ids().get('workflows', {}).get(key)
        if not pid:
            sys.exit(f'{APPLY} exists ({live[APPLY]["btnId"]}) but ids.json has no workflow for it')
        return pid, False
    hap.backup('orders_buttons_pre_apply_discount', list(live.values()))
    out = hap.run('worksheet', 'create-custom-action', ws(), '-a', APP, '--action-spec',
                  json.dumps(apply_spec(f), ensure_ascii=False))
    data = out.get('data', out) if isinstance(out, dict) else {}
    pid = data.get('processId')
    if not pid:
        sys.exit(f'{APPLY}: no processId in create-custom-action output: {out}')
    C.remember('workflows', key, pid)
    btn = next((b for b in hap.listing('worksheet', 'custom-actions', ws()) if b['name'] == APPLY), None)
    if not btn:
        sys.exit(f'{APPLY}: created, but it does not come back from custom-actions')
    C.remember('buttons', key, btn['btnId'])
    return pid, True


PARAM_NODE = '6038a1cbf18158039fb40e68'         # the fixed 本流程参数 node every process carries
STRING_FX = 'string_fx_id'
NUMBER_FORMULA, FUNCTION_FORMULA, OBJECT_TOTAL = '100', '106', '105'
FORMULA_NODE = 9
A_TOTAL = 'Their total, tax included'
A_TOTAL_WAS = 'Their subtotal'                  # its name while it summed Subtotal; `sync_apply` renames it
A_DIVISOR = 'What the discount is taken over'
# child A
A_A_VARIANT = 'The Discount product'
A_TAXES = "The line's taxes"
A_KEY = "The line's tax group"
TAXES_WS = '6aad1034805aef703286ac2f'
TAX_NAME, TAX_SEQUENCE = '6aad104e7d58b0f4493141f9', '6aad104e7d58b0f4493141fe'   # Taxes' Tax Name · Sequence
FROM_RELATION = '401'                           # a get-multiple over a record's own Relation
A_GROUP = "Its tax group's discount line"
A_FOUND = 'Does the tax group have its line yet?'
A_ADD = "Add the line's subtotal to it"
A_NEG = "The line's subtotal, negated"
A_CREATE = "Create the tax group's discount line"
# child B
A_SHARE = 'The discount on this tax group'
A_SET = 'Set its Unit Price'
LABEL_PARAM, VALUE_PARAM, DIVISOR_PARAM = 'label', 'value', 'divisor'


def discount_label_formula(type_ref, value_ref):
    """Odoo's line name, from `_prepare_global_discount_so_lines`: "Discount %(percent)s%%" with the percentage as
    `float_repr(…, Discount precision 2)` — so **10 reads "10.00"** — or plain "Discount" for a fixed amount.
    HAP's function formulas have no number formatting, so the two decimals are built by hand."""
    v = value_ref
    two = f'RIGHT(CONCAT("0", ROUND({v}*100, 0) - INT({v})*100), 2)'
    return (f'IF({type_ref} == "{GLOBAL_DISCOUNT}", CONCAT("Discount ", INT({v}), ".", {two}, "%"), '
            f'"Discount")')


def apply_nodes(f, params):
    """The whole Apply Discount workflow for one `batch-add` on its empty button workflow."""
    t = lambda fid: f'$trigger-{fid}$'
    typ, val = f[DISCOUNT_TYPE]['controlId'], f[DISCOUNT_VALUE]['controlId']
    trig = {'nodeAlias': 'trigger'}
    orders_is = lambda node, field: {'left': {'node': trig, 'fieldId': LINES_ORDERS, '_filedTypeId': RELATION},
                                     'op': RELATION_EQ, 'right': {'kind': 'field', 'node': node, 'fieldId': field}}
    product_is = lambda alias: {'left': {'node': trig, 'fieldId': CHILD['Product'], '_filedTypeId': RELATION},
                                'op': RELATION_EQ,
                                'right': {'kind': 'field', 'node': {'nodeAlias': alias}, 'fieldId': 'rowid'}}
    variant = lambda alias, name: {
        'nodeAlias': alias, 'nodeType': 'get_single', 'name': name,
        'config': {'worksheet': VARIANTS_WS, 'execute_type': 0, 'filter': {'logic': 'and', 'items': [
            {'left': {'node': trig, 'fieldId': 'rowid', '_filedTypeId': TEXT}, 'op': 'eq',
             'right': {'kind': 'literal', 'value': discount_variant()}}]}}}
    param = lambda name: f'${PARAM_NODE}-{params[name]}$'
    sub = {'nodeAlias': 'sub_trigger'}
    child_a = [
        variant('a_variant', A_A_VARIANT),
        {'nodeAlias': 'a_taxes', 'nodeType': 'get_relation_records', 'name': A_TAXES,
         'config': {'worksheet': TAXES_WS, 'target': {'node': sub}, 'fields': [{'fieldId': CHILD['Taxes']}],
                    'sorts': [{'controlId': TAX_SEQUENCE, 'controlType': NUMBER, 'isAsc': True}]}},
        {'nodeAlias': 'a_group', 'nodeType': 'get_single', 'name': A_GROUP,
         'config': {'worksheet': LINES_WS, 'execute_type': 2, 'filter': {'logic': 'and', 'items': [
             {'left': {'node': sub, 'fieldId': LINES_ORDERS, '_filedTypeId': RELATION}, 'op': RELATION_EQ,
              'right': {'kind': 'field', 'node': sub, 'fieldId': LINES_ORDERS}},
             {'left': {'node': sub, 'fieldId': CHILD['Product'], '_filedTypeId': RELATION}, 'op': RELATION_EQ,
              'right': {'kind': 'field', 'node': {'nodeAlias': 'a_variant'}, 'fieldId': 'rowid'}},
             # the third condition — Description is the code block's key — is saved by `sync_apply`,
             # because `batch-add` cannot make the code block (BUILDING.md) and so nothing here can name it
             ]}}},
        {'nodeAlias': 'a_found', 'nodeType': 'branch', 'name': A_FOUND, 'config': {'paths': [
            {'alias': 'a_has', 'result_type': 'has_data', 'name': 'Yes', 'nodes': [
                {'nodeAlias': 'a_add', 'nodeType': 'update_record', 'name': A_ADD,
                 'config': {'worksheet': LINES_WS, 'target': {'node': {'nodeAlias': 'a_group'}},
                            'fields': [{'fieldId': CHILD['Unit Price'], 'type': 8, 'addType': 2,
                                        'valueRef': {'node': sub, 'fieldId': CHILD['Subtotal']}}]}}]},
            {'alias': 'a_none', 'result_type': 'no_data', 'name': 'No', 'nodes': [
                {'nodeAlias': 'a_neg', 'nodeType': 'compute', 'name': A_NEG,
                 'config': {'mode': 'number', 'formula': f'0-$sub_trigger-{CHILD["Subtotal"]}$'}},
                {'nodeAlias': 'a_create', 'nodeType': 'create_record', 'name': A_CREATE,
                 'config': {'worksheet': LINES_WS, 'fields': [
                     {'fieldId': LINES_ORDERS, 'type': RELATION,
                      'valueRef': {'node': sub, 'fieldId': LINES_ORDERS}},
                     {'fieldId': CHILD['Display Type'], 'type': DROPDOWN, 'value': PRODUCT_LINE},
                     {'fieldId': CHILD['Product'], 'type': RELATION,
                      'valueRef': {'node': {'nodeAlias': 'a_variant'}, 'fieldId': 'rowid'}},
                     {'fieldId': CHILD['Description'], 'type': TEXT, 'value': ''},      # `sync_apply` binds it
                     {'fieldId': CHILD['Quantity'], 'type': NUMBER, 'value': '1'},
                     {'fieldId': CHILD['Unit Price'], 'type': 8,
                      'valueRef': {'node': {'nodeAlias': 'a_neg'}, 'fieldId': NUMBER_FX, 'nodeActionId': '100'}},
                     {'fieldId': CHILD['Discount'], 'type': NUMBER, 'value': '0'},
                     {'fieldId': CHILD['Taxes'], 'type': RELATION,
                      'valueRef': {'node': sub, 'fieldId': CHILD['Taxes']}},
                     {'fieldId': CHILD['Sequence'], 'type': NUMBER, 'value': '999'},
                 ]}}]},
        ]}},
    ]
    child_b = [
        {'nodeAlias': 'b_share', 'nodeType': 'compute', 'name': A_SHARE,
         'config': {'mode': 'number', 'formula': f'$sub_trigger-{CHILD["Unit Price"]}$*{param(VALUE_PARAM)}'
                                                 f'/{param(DIVISOR_PARAM)}'}},
        {'nodeAlias': 'b_set', 'nodeType': 'update_record', 'name': A_SET,
         'config': {'worksheet': LINES_WS, 'target': {'node': sub},
                    'fields': [{'fieldId': CHILD['Unit Price'], 'type': 8,
                                'valueRef': {'node': {'nodeAlias': 'b_share'}, 'fieldId': NUMBER_FX,
                                             'nodeActionId': '100'}}]}},
    ]
    lines_of_order = {'logic': 'and', 'items': [
        orders_is(trig, 'rowid'),
        {'left': {'node': trig, 'fieldId': CHILD['Display Type'], '_filedTypeId': DROPDOWN}, 'op': IS_ANY_OF,
         'right': {'kind': 'literal', 'values': [{'key': PRODUCT_LINE, 'value': 'Product', 'isDeleted': False}]}}]}
    discount_lines = {'logic': 'and', 'items': [orders_is(trig, 'rowid'), product_is('variant')]}
    value_empty = {'left': {'node': trig, 'fieldId': val, '_filedTypeId': NUMBER}, 'op': EMPTY}
    value_zero = {'left': {'node': trig, 'fieldId': val, '_filedTypeId': NUMBER}, 'op': 'eq',
                  'right': {'kind': 'literal', 'value': '0'}}
    type_empty = {'left': {'node': trig, 'fieldId': typ, '_filedTypeId': DROPDOWN}, 'op': EMPTY}
    return [
        variant('variant', A_VARIANT),
        {'nodeAlias': 'old', 'nodeType': 'get_multiple', 'name': A_OLD,
         'config': {'worksheet': LINES_WS, 'filter': discount_lines}},
        {'nodeAlias': 'remove', 'nodeType': 'delete_record', 'name': A_REMOVE,
         'config': {'worksheet': LINES_WS, 'target': {'node': {'nodeAlias': 'old'}}}},
        {'nodeAlias': 'gate', 'nodeType': 'branch', 'name': A_BRANCH, 'config': {'paths': [
            {'alias': 'nothing', 'name': 'No', 'condition': {'logic': 'or',
                                                            'items': [value_empty, value_zero, type_empty]}},
            {'alias': 'apply', 'name': 'Yes', 'nodes': [
                {'nodeAlias': 'lines', 'nodeType': 'get_multiple', 'name': A_LINES,
                 'config': {'worksheet': LINES_WS, 'filter': lines_of_order}},
                {'nodeAlias': 'total', 'nodeType': 'rollup', 'name': A_TOTAL,
                 'config': {'mode': 'worksheet', 'worksheet': LINES_WS, 'aggregate': 'sum',
                            'field': CHILD['Total'], 'filter': lines_of_order}},
                {'nodeAlias': 'label', 'nodeType': 'compute', 'name': A_LABEL,
                 'config': {'mode': 'function', 'output_type': 'text',
                            'formula': discount_label_formula(t(typ), t(val))}},
                {'nodeAlias': 'divisor', 'nodeType': 'compute', 'name': A_DIVISOR,
                 'config': {'mode': 'function', 'output_type': 'text',
                            'formula': f'CONCAT(IF({t(typ)} == "{GLOBAL_DISCOUNT}", 100, '
                                       f'$total-{NUMBER_FX}$))'}},
                {'nodeAlias': 'each', 'nodeType': 'sub_process', 'name': A_EACH,
                 'config': {'target': {'kind': 'record', 'node': {'nodeAlias': 'lines'}},
                            'process': {'name': A_INNER, 'nodes': child_a, 'parameters': [
                                {'name': LABEL_PARAM, 'controlId': params[LABEL_PARAM],
                                 'value': {'kind': 'field', 'node': {'nodeAlias': 'label'}, 'fieldId': STRING_FX}}]},
                            'execution': {'mode': 'sequential_each', 'continueAfterComplete': True}}},
                {'nodeAlias': 'groups', 'nodeType': 'get_multiple', 'name': A_GROUPS,
                 'config': {'worksheet': LINES_WS, 'filter': discount_lines}},
                {'nodeAlias': 'count', 'nodeType': 'rollup', 'name': A_COUNT,
                 'config': {'source': {'node': {'nodeAlias': 'groups'}}, 'aggregate': 'count'}},
                {'nodeAlias': 'single', 'nodeType': 'branch', 'name': A_ONE, 'config': {'paths': [
                    {'alias': 'one', 'name': 'Yes', 'condition': {'logic': 'and', 'items': [
                        {'left': {'node': {'nodeAlias': 'count'}, 'fieldId': NUMBER_FX, '_filedTypeId': NUMBER},
                         'op': 'eq', 'right': {'kind': 'literal', 'value': '1'}}]},
                     'nodes': [{'nodeAlias': 'plain', 'nodeType': 'update_record', 'name': A_SINGLE,
                                'config': {'worksheet': LINES_WS, 'target': {'node': {'nodeAlias': 'groups'}},
                                           'fields': [{'fieldId': CHILD['Description'], 'type': TEXT,
                                                       'value': f'$label-{STRING_FX}$'}]}}]},
                    {'alias': 'several', 'name': 'No'}]}},
                {'nodeAlias': 'price', 'nodeType': 'sub_process', 'name': A_PRICE,
                 'config': {'target': {'kind': 'record', 'node': {'nodeAlias': 'groups'}},
                            'process': {'name': A_PRICE_INNER, 'nodes': child_b, 'parameters': [
                                {'name': VALUE_PARAM, 'controlId': params[VALUE_PARAM],
                                 'value': {'kind': 'field', 'node': trig, 'fieldId': val}},
                                {'name': DIVISOR_PARAM, 'controlId': params[DIVISOR_PARAM],
                                 'value': {'kind': 'field', 'node': {'nodeAlias': 'divisor'},
                                           'fieldId': STRING_FX}}]},
                            'execution': {'mode': 'sequential_each', 'continueAfterComplete': True}}},
            ]}]}},
    ]


GET_ONE = 7
FROM_SHEET_ONE = '406'
WORKSHEET_TOTAL_NODE = '107'
CONTINUE_IF_NONE = 2                            # a search step's executeType: carry on when nothing is found
STOP_IF_NONE = 0


# `check` runs the same comparisons as the build with DRIFT set to a list: every step that would write appends what
# it found instead, and nothing is saved.
DRIFT = None


def drifted(what):
    """True when a write is due — recorded instead of made while `check` is reading."""
    if DRIFT is None:
        return False
    DRIFT.append(what)
    return True


def wf_cond(node_id, kind, action, field, name, type_id, condition, values, enum_default=0, source_type=0):
    """One stored filter condition, in the shape `lines_filter` writes and the server keeps."""
    return {'nodeId': node_id, 'nodeType': kind, 'actionId': action, 'filedId': field, 'filedValue': name,
            'filedTypeId': type_id, 'enumDefault': enum_default, 'conditionId': condition,
            'sourceType': source_type, 'conditionValues': values}


def order_is(node_id, kind, action, value_node, value_field='rowid'):
    """The line belongs to `value_node`'s order: its rowid, or its own Orders relation (conditionId 33)."""
    return wf_cond(node_id, kind, action, LINES_ORDERS, 'Orders', RELATION, RELATION_EQ,
                   [{'nodeId': value_node, 'controlId': value_field}], enum_default=1, source_type=33)


def product_is_node(node_id, kind, action, variant_node):
    return wf_cond(node_id, kind, action, CHILD['Product'], 'Product', RELATION, RELATION_EQ,
                   [{'nodeId': variant_node, 'controlId': 'rowid'}], enum_default=1, source_type=33)


def is_product_line(node_id, kind, action):
    return wf_cond(node_id, kind, action, CHILD['Display Type'], 'Display Type', DROPDOWN, IS_ANY_OF,
                   [{'value': {'key': PRODUCT_LINE, 'value': 'Product', 'isDeleted': False, 'score': None,
                               'index': None}}])


def is_the_variant(node_id):
    return wf_cond(node_id, GET_ONE, FROM_SHEET_ONE, 'rowid', 'Record ID', TEXT, '9',
                   [{'value': discount_variant()}])


def filters_of(*conds):
    return [{'spliceType': 1, 'conditions': [list(conds)]}]


def wf_filter_state(filters_):
    """A **workflow step's** `filters` (`filedId`, `conditionId`, `conditionValues`) as (field, conditionId, compared
    with) per condition — what the builder and `check` compare. A view's or button's filter is `view_filter_state`;
    this one reads such a filter as []."""
    out = []
    for flt in filters_ or []:
        for g in flt.get('conditions') or []:
            for c in g:
                vals = []
                for v in c.get('conditionValues') or []:
                    value = v.get('value')
                    if isinstance(value, dict):
                        value = value.get('key')
                    vals.append((v.get('nodeId') or '', v.get('controlId') or '', value or ''))
                out.append((c.get('filedId'), c.get('conditionId'), vals))
    return out


def sync_search(pid, node, worksheet, filters_, kind, action, execute_type=None, execute=None):
    """A get-single (7) or get-multiple (13) step's worksheet, `filters`, not-found behaviour and fetch mode.
    `batch-add` writes a search step's filter as `operateCondition`, which is not what the step reads."""
    got = read_node(pid, node['id'])
    same = wf_filter_state(got.get('filters')) == wf_filter_state(filters_) and got.get('appId') == worksheet and \
        (execute_type is None or got.get('executeType') == execute_type) and \
        (execute is None or bool(got.get('execute')) == execute)
    if same:
        return False
    if drifted(f"{node['name']}: filter {wf_filter_state(got.get('filters'))} on {got.get('appId')} "
               f"executeType={got.get('executeType')} execute={got.get('execute')}"):
        return True
    cfg = {'actionId': action, 'appId': worksheet, 'appType': 1, 'selectNodeId': '', 'filters': filters_,
           'operateCondition': []}
    if kind == GET_ONE:
        cfg['sorts'] = got.get('sorts') or [{'controlId': 'ctime', 'controlType': 16, 'isAsc': True}]
        cfg['executeType'] = execute_type if execute_type is not None else got.get('executeType', 0)
    else:
        cfg['execute'] = execute if execute is not None else got.get('execute', False)
    hap.run('workflow', 'node', 'save', pid, node['id'], '--type', str(kind), '-n', node['name'],
            '-c', json.dumps(cfg, ensure_ascii=False))
    back = read_node(pid, node['id'])
    if wf_filter_state(back.get('filters')) != wf_filter_state(filters_) or back.get('appId') != worksheet:
        sys.exit(f"{node['name']}: filter reads back {wf_filter_state(back.get('filters'))}, wanted "
                 f'{wf_filter_state(filters_)} — `hap workflow rollback {pid} -y` restores the published version')
    return True


def set_entries(pid, node, wanted):
    """Give a create or update step these field writes, keeping every other entry and its configuration;
    True when it wrote. Compared on what `write_state` reads."""
    d = read_node(pid, node['id'])
    fields = list(d.get('fields') or [])
    changed = False
    for want in wanted:
        entry = next((x for x in fields if x.get('fieldId') == want['fieldId']), None)
        if entry and write_state(entry) == write_state(want):
            continue
        if entry:
            entry.update(want)
        else:
            fields.append(want)
        changed = True
    if not changed:
        return False
    if drifted(f"{node['name']}: field writes differ from {[w['fieldId'] for w in wanted]}"):
        return True
    hap.run('workflow', 'node', 'save', pid, node['id'], '--type', str(UPDATE_NODE), '-n', node['name'],
            '-c', json.dumps({'actionId': d.get('actionId'), 'appId': d.get('appId'), 'appType': 1,
                              'selectNodeId': d.get('selectNodeId') or '', 'fields': fields}, ensure_ascii=False))
    back = {x.get('fieldId'): write_state(x) for x in read_node(pid, node['id']).get('fields') or []}
    bad = [w['fieldId'] for w in wanted if back.get(w['fieldId']) != write_state(w)]
    if bad or read_node(pid, node['id']).get('isException'):
        sys.exit(f"{node['name']}: {bad} read back {[back.get(b) for b in bad]}")
    return True


def sync_related(pid, node, select, field, sorts):
    """A get-multiple step over a record's own Relation (13 / 401): the records `field` of `select` points at,
    in `sorts` order. Odoo joins a line's tax names in the taxes' own order — `account.tax` is ordered by
    sequence, then id."""
    got = read_node(pid, node['id'])
    key = lambda d: (d.get('selectNodeId'), [x.get('fieldId') for x in d.get('fields') or []],
                     [(x.get('controlId'), bool(x.get('isAsc'))) for x in d.get('sorts') or []])
    want = (select, [field], [(x['controlId'], x['isAsc']) for x in sorts])
    if key(got) == want and not got.get('isException'):
        return False
    if drifted(f"{node['name']}: {key(got)}, wanted {want}"):
        return True
    hap.run('workflow', 'node', 'save', pid, node['id'], '--type', str(GET_MANY), '-n', node['name'],
            '-c', json.dumps({'actionId': FROM_RELATION, 'appId': TAXES_WS, 'appType': 1, 'selectNodeId': select,
                              'fields': [{'fieldId': field}], 'sorts': sorts, 'execute': True},
                             ensure_ascii=False))
    back = read_node(pid, node['id'])
    if key(back) != want or back.get('isException'):
        sys.exit(f"{node['name']}: reads back {key(back)} exception={back.get('isException')}, wanted {want}")
    return True


def sync_total(pid, node, filters_, field):
    """A worksheet-total step (9 / 107): the sum of `field` over the lines `filters_` names."""
    got = read_node(pid, node['id'])
    want = {'reportControlId': field, 'reportType': 3, 'appId': LINES_WS}
    same = wf_filter_state(got.get('filters')) == wf_filter_state(filters_)
    if same and all(got.get(k) == v for k, v in want.items()):
        return False
    if drifted(f"{node['name']}: {({k: got.get(k) for k in want})} {wf_filter_state(got.get('filters'))}"):
        return True
    hap.run('workflow', 'node', 'save', pid, node['id'], '--type', str(FORMULA_NODE), '-n', node['name'],
            '-c', json.dumps({'actionId': WORKSHEET_TOTAL_NODE, 'appId': LINES_WS, 'appType': 1, 'execute': True,
                              'reportControlId': field, 'reportType': 3, 'filters': filters_,
                              'number': 2, 'nullZero': True}, ensure_ascii=False))
    back = read_node(pid, node['id'])
    if any(back.get(k) != v for k, v in want.items()) or \
            wf_filter_state(back.get('filters')) != wf_filter_state(filters_):
        sys.exit(f"{node['name']}: reads back {({k: back.get(k) for k in want})} "
                 f"{wf_filter_state(back.get('filters'))}")
    return True


def sync_formula(pid, node, action, expression, number=2, null_zero=True, out_type=None):
    """A formula step's expression, decimals and empty-as-0 (invlines.set_formula's contract). A 106 carries its
    output type (text 2) so its result is `string_fx_id`."""
    got = read_node(pid, node['id'])
    want = {'formulaValue': expression, 'number': number, 'nullZero': null_zero}
    if all(got.get(k) == v for k, v in want.items()) and not got.get('isException'):
        return False
    if drifted(f"{node['name']}: {({k: got.get(k) for k in want})} exception={got.get('isException')}"):
        return True
    cfg = {'actionId': action, 'name': node['name'], 'execute': True, 'formulaValue': expression,
           'number': number, 'nullZero': null_zero}
    if out_type is not None:
        cfg['type'] = out_type
    elif action == NUMBER_FORMULA:
        cfg['type'] = NUMBER
    hap.run('workflow', 'node', 'save', pid, node['id'], '--type', str(FORMULA_NODE), '-n', node['name'],
            '-c', json.dumps(cfg, ensure_ascii=False))
    back = read_node(pid, node['id'])
    if any(back.get(k) != v for k, v in want.items()) or back.get('isException'):
        sys.exit(f"{node['name']}: reads back {({k: back.get(k) for k in want})} exception={back.get('isException')}")
    return True


def sync_path_names(pid, gateway, names_by_next):
    """Name each path of a gateway by the node it runs into (`None` for the empty one). `batch-add` leaves the
    two default paths unnamed (BUILDING.md)."""
    proc = hap.run('workflow', 'node', 'list', pid)
    changed = False
    for p in proc['flowNodeMap'].values():
        if p.get('typeId') != BRANCH_PATH or p.get('prveId') != gateway['id']:
            continue
        key = p.get('nextId') if p.get('nextId') not in (None, '', '99') else None
        want = names_by_next.get(key)
        if want and p.get('name') != want:
            if not drifted(f"{gateway['name']}: a path is named {p.get('name')!r}, wanted {want!r}"):
                hap.run('workflow', 'node', 'rename', pid, p['id'], '-n', want)
            changed = True
    return changed


JAVASCRIPT, CODE_NODE = '102', 14
SUBTRACT = 2                                    # a field write's addType: 0 set · 1 add · 2 subtract
KEY_OUT = 'key'


def key_code():
    """Child A's code block: the tax group's key, which is also Odoo's line name for it when an order has several
    tax combinations — `"%(label)s- On products with the following taxes %(taxes)s"` with the names joined by
    ", " (`_prepare_global_discount_so_lines`; the missing space before the dash is Odoo's own). HAP's function
    formulas render a Relation as its **count** and a get-multiple field as nothing, so the names are joined here.
    A get-multiple field reaches a code block as a list, parsed whether it is a JSON array or plain text."""
    return """function list(v) {
  if (v === undefined || v === null) return [];
  if (Array.isArray(v)) return v;
  var s = String(v).trim();
  if (!s) return [];
  try { var j = JSON.parse(s); return Array.isArray(j) ? j : [j]; } catch (e) { return [s]; }
}
function name(x) {
  while (x && typeof x === 'object') x = Array.isArray(x) ? x[0] : (x.name || x.value || '');
  return x === undefined || x === null ? '' : String(x).trim();
}
var names = list(input.names).map(name).filter(function (x) { return x !== ''; });
output = {
  key: (String(input.label || '') + '- On products with the following taxes ' + names.join(', ')).replace(/\\s+$/, ''),
  seen: JSON.stringify({names: input.names, taxes: input.taxes})
};
"""


def key_inputs(a_start, taxes_node, label_ref):
    return [{'name': 'label', 'value': label_ref},
            {'name': 'names', 'value': f'${taxes_node}-{TAX_NAME}$'},
            {'name': 'taxes', 'value': f'${a_start}-{CHILD["Taxes"]}$'}]


KEY_TEST = {'label': 'Discount 10.00%', 'names': '["10% G","Exempt C 1,2"]', 'taxes': '[]'}


def ensure_key_code(pid, byname, a_start, label_ref):
    """The code block after the taxes step: added with `node add --type 14` (batch-add refuses one), saved with
    its inputs and code, then run once through codeTest, which registers its `key` output."""
    import base64
    from hap_cli.core import flow_node
    from hap_cli.core.session import Session
    b64 = lambda text: base64.b64encode(text.encode('utf-8')).decode('ascii')
    changed = False
    if A_KEY not in byname and drifted(f'{A_KEY}: the code block is missing'):
        return True
    if A_KEY not in byname:
        hap.run('workflow', 'node', 'add', pid, '--type', str(CODE_NODE), '-n', A_KEY,
                '--after', byname[A_TAXES]['id'], '-a', JAVASCRIPT)
        byname = nodes_by_name(pid)[1]
        changed = True
    node = byname[A_KEY]
    got = read_node(pid, node['id'])
    code, inputs = key_code(), key_inputs(a_start, byname[A_TAXES]['id'], label_ref)
    live = got.get('code') or ''                   # stored as plain text, though it is sent base64-encoded
    live_inputs = [(x.get('name'), x.get('value')) for x in got.get('inputDatas') or [] if x.get('name')]
    stale = live.strip() != code.strip() or live_inputs != [(x['name'], x['value']) for x in inputs]
    if (stale or str(got.get('actionId')) != JAVASCRIPT or KEY_OUT not in
            {c.get('controlId') for c in got.get('controls') or []}) and \
            drifted(f'{A_KEY}: code, inputs {live_inputs} or its {KEY_OUT!r} output differ'):
        return True
    if stale:
        flow_node.save_node(Session.load(None), pid, node['id'], CODE_NODE,
                            {'actionId': JAVASCRIPT, 'inputDatas': inputs, 'code': b64(code),
                             'testMap': got.get('testMap') or {}, 'version': got.get('version') or '',
                             'maxRetries': got.get('maxRetries', 1)}, name=A_KEY)
        changed = True
    got = read_node(pid, node['id'])
    if changed or KEY_OUT not in {c.get('controlId') for c in got.get('controls') or []}:
        test = flow_node.test_code(Session.load(None), pid, node['id'], b64(code),
                                   [{**x, 'value': KEY_TEST[x['name']]} for x in inputs],
                                   action_id=JAVASCRIPT, version=got.get('version') or '')
        print(f'  codeTest: {json.dumps(test, ensure_ascii=False)[:400]}')
        got = read_node(pid, node['id'])
        if KEY_OUT not in {c.get('controlId') for c in got.get('controls') or []}:
            sys.exit(f'{A_KEY}: codeTest registered no {KEY_OUT!r} output: {got.get("controls")}')
    return changed


def lit(field, kind, value):
    """A field write of a constant, in the shape the server stores."""
    return {'fieldId': field, 'type': kind, 'addType': 0, 'fieldValue': value, 'fieldValueId': '', 'nodeId': ''}


def ref(field, kind, node, source, node_type, action, add=0):
    """A field write taken from another step's record or result: `nodeId` + `fieldValueId`. The binding keys the
    server also needs (`nodeAppType`, `nodeTypeId`, `nodeActionId`) are sent but not compared — it rewrites them
    (a sub-process record's "401" reads back "400", a formula's `nodeAppType` 1 reads back 11; BUILDING.md)."""
    return {'fieldId': field, 'type': kind, 'addType': add, 'fieldValue': '', 'fieldValueId': source,
            'nodeId': node, 'sureNodeId': node, 'nodeAppType': 1, 'nodeTypeId': node_type, 'nodeActionId': action}


def apply_writes(pid, by, kids):
    """[(process, step, its field writes)] for the four steps that write Order Lines.

    The created discount line is Odoo's `_prepare_global_discount_so_lines` line: the Discount product, quantity
    1, the group's (negative) amount as unit price, the group's taxes, sequence 999 — plus what this app needs a
    line to carry: Display Type *Product*, Discount 0 (Subtotal's formula is not null-as-zero, so an empty
    Discount computes everything empty) and the unit, Units (the variant's own Unit is a lookup, which a step
    cannot bind to a Relation, so the record is named)."""
    a_pid, b_pid = kids[A_INNER], kids[A_PRICE_INNER]
    a_proc, a_by = nodes_by_name(a_pid)
    b_proc, b_by = nodes_by_name(b_pid)
    a_start, b_start = a_proc['startEventId'], b_proc['startEventId']
    from_line = lambda field, kind, source, add=0: ref(field, kind, a_start, source, 0, FROM_RECORD, add)
    return [
        (a_pid, A_CREATE, [
            from_line(LINES_ORDERS, RELATION, LINES_ORDERS),
            lit(CHILD['Display Type'], DROPDOWN, PRODUCT_LINE),
            ref(CHILD['Product'], RELATION, a_by[A_A_VARIANT]['id'], 'rowid', GET_ONE, FROM_SHEET_ONE),
            lit(CHILD['Description'], TEXT, f"${a_by[A_KEY]['id']}-{KEY_OUT}$"),
            lit(CHILD['Quantity'], NUMBER, '1'),
            ref(CHILD['Unit Price'], 8, a_by[A_NEG]['id'], NUMBER_FX, FORMULA_NODE, NUMBER_FORMULA),
            lit(CHILD['Discount'], NUMBER, '0'),
            from_line(CHILD['Taxes'], RELATION, CHILD['Taxes']),
            lit(CHILD['Sequence'], NUMBER, '999'),
            lit(CHILD['Unit'], RELATION, UNITS_UOM)]),
        (a_pid, A_ADD, [from_line(CHILD['Unit Price'], 8, CHILD['Subtotal'], add=SUBTRACT)]),
        (b_pid, A_SET, [ref(CHILD['Unit Price'], 8, b_by[A_SHARE]['id'], NUMBER_FX, FORMULA_NODE, NUMBER_FORMULA)]),
        (pid, A_SINGLE, [lit(CHILD['Description'], TEXT, f"${by[A_LABEL]['id']}-{STRING_FX}$")]),
    ]


def apply_children(pid, byname):
    """{A_INNER: child A's process id, A_PRICE_INNER: child B's} — read off the two sub-process steps."""
    out = {}
    for step, inner in ((A_EACH, A_INNER), (A_PRICE, A_PRICE_INNER)):
        node = byname.get(step)
        out[inner] = read_node(pid, node['id']).get('subProcessId') if node else ''
    return out


def sub_params(pid, node):
    """{parameter name: its controlId} passed by a sub-process step, and the values it passes."""
    d = read_node(pid, node['id'])
    names = {v['controlId']: v['controlName'] for v in d.get('subProcessVariables') or []}
    return {names.get(x['fieldId'], x['fieldId']): (x['fieldId'], x.get('fieldValue')) for x in d.get('fields') or []}


def apply_wanted(f, pid):
    """Every step of the three workflows, as the builder wants it: [(process id, step name, kind, what)]."""
    proc, by = nodes_by_name(pid)
    trigger = proc['startEventId']
    typ, val = f[DISCOUNT_TYPE]['controlId'], f[DISCOUNT_VALUE]['controlId']
    t = lambda fid: f'${trigger}-{fid}$'
    kids = apply_children(pid, by)
    a_pid, b_pid = kids[A_INNER], kids[A_PRICE_INNER]
    a_proc, a_by = nodes_by_name(a_pid)
    b_proc, b_by = nodes_by_name(b_pid)
    a_start, b_start = a_proc['startEventId'], b_proc['startEventId']
    pa, pb = sub_params(pid, by[A_EACH]), sub_params(pid, by[A_PRICE])
    param = lambda p, name: f'${PARAM_NODE}-{p[name][0]}$'
    n = lambda b, name: b[name]['id']
    many = lambda b, name, *conds: filters_of(*conds)
    return proc, by, kids, [
        (pid, A_VARIANT, 'search', dict(worksheet=VARIANTS_WS, kind=GET_ONE, action=FROM_SHEET_ONE,
                                        execute_type=STOP_IF_NONE,
                                        filters=filters_of(is_the_variant(n(by, A_VARIANT))))),
        (pid, A_OLD, 'search', dict(worksheet=LINES_WS, kind=GET_MANY, action=FROM_WORKSHEET, execute=True,
                                    filters=filters_of(order_is(n(by, A_OLD), GET_MANY, FROM_WORKSHEET, trigger),
                                                       product_is_node(n(by, A_OLD), GET_MANY, FROM_WORKSHEET,
                                                                       n(by, A_VARIANT))))),
        (pid, A_LINES, 'search', dict(worksheet=LINES_WS, kind=GET_MANY, action=FROM_WORKSHEET, execute=True,
                                      filters=filters_of(order_is(n(by, A_LINES), GET_MANY, FROM_WORKSHEET, trigger),
                                                         is_product_line(n(by, A_LINES), GET_MANY, FROM_WORKSHEET)))),
        (pid, A_TOTAL, 'total', dict(field=CHILD['Total'], filters=filters_of(
            order_is(n(by, A_TOTAL), 18, WORKSHEET_TOTAL_NODE, trigger),
            is_product_line(n(by, A_TOTAL), 18, WORKSHEET_TOTAL_NODE)))),
        (pid, A_LABEL, 'formula', dict(action=FUNCTION_FORMULA, number=2, null_zero=False, out_type=TEXT,
                                       expression=discount_label_formula(t(typ), t(val)))),
        (pid, A_DIVISOR, 'formula', dict(action=FUNCTION_FORMULA, number=2, null_zero=False, out_type=TEXT,
                                         expression=f'CONCAT(IF({t(typ)} == "{GLOBAL_DISCOUNT}", 100, '
                                                    f'${n(by, A_TOTAL)}-{NUMBER_FX}$))')),
        (pid, A_GROUPS, 'search', dict(worksheet=LINES_WS, kind=GET_MANY, action=FROM_WORKSHEET, execute=True,
                                       filters=filters_of(order_is(n(by, A_GROUPS), GET_MANY, FROM_WORKSHEET, trigger),
                                                          product_is_node(n(by, A_GROUPS), GET_MANY, FROM_WORKSHEET,
                                                                          n(by, A_VARIANT))))),
        (a_pid, A_A_VARIANT, 'search', dict(worksheet=VARIANTS_WS, kind=GET_ONE, action=FROM_SHEET_ONE,
                                            execute_type=STOP_IF_NONE,
                                            filters=filters_of(is_the_variant(n(a_by, A_A_VARIANT))))),
        (a_pid, A_TAXES, 'related', dict(select=a_start, field=CHILD['Taxes'],
                                         sorts=[{'controlId': TAX_SEQUENCE, 'controlType': NUMBER, 'isAsc': True}])),
        (a_pid, A_GROUP, 'search', dict(worksheet=LINES_WS, kind=GET_ONE, action=FROM_SHEET_ONE,
                                        execute_type=CONTINUE_IF_NONE, filters=filters_of(
                order_is(n(a_by, A_GROUP), GET_ONE, FROM_SHEET_ONE, a_start, LINES_ORDERS),
                product_is_node(n(a_by, A_GROUP), GET_ONE, FROM_SHEET_ONE, n(a_by, A_A_VARIANT)),
                wf_cond(n(a_by, A_GROUP), GET_ONE, FROM_SHEET_ONE, CHILD['Description'], 'Description', TEXT, '9',
                        [{'nodeId': n(a_by, A_KEY), 'controlId': KEY_OUT}])))),
        (a_pid, A_NEG, 'formula', dict(action=NUMBER_FORMULA, number=2, null_zero=True,
                                       expression=f'0-${a_start}-{CHILD["Subtotal"]}$')),
        (b_pid, A_SHARE, 'formula', dict(action=NUMBER_FORMULA, number=2, null_zero=True,
                                         expression=f'${b_start}-{CHILD["Unit Price"]}$*{param(pb, VALUE_PARAM)}'
                                                    f'/{param(pb, DIVISOR_PARAM)}')),
    ]


def rename_total(pid):
    """The denominator step was *Their subtotal* while Fixed Amount was spread over the untaxed subtotals; it sums
    the product lines' tax-included **Total** now (Odoo's `_reduce_base_lines_to_target_amount`), so its name says
    so. True when it renamed; under `check`, a pending rename is recorded as drift instead."""
    by = nodes_by_name(pid)[1]
    if A_TOTAL in by or A_TOTAL_WAS not in by:
        return False
    if not drifted(f'{A_TOTAL_WAS!r} is still named so; wanted {A_TOTAL!r}'):
        hap.run('workflow', 'node', 'rename', pid, by[A_TOTAL_WAS]['id'], '-n', A_TOTAL)
        if A_TOTAL not in nodes_by_name(pid)[1]:
            sys.exit(f'{A_TOTAL_WAS!r}: renamed to {A_TOTAL!r}, but it does not read back so')
    return True


def sync_apply(f, pid):
    """Bring every step of Apply Discount and its two children to what `apply_wanted` says; True if written."""
    renamed = rename_total(pid)
    proc, by = nodes_by_name(pid)
    kids = apply_children(pid, by)
    changed = {pid: renamed, kids[A_INNER]: False, kids[A_PRICE_INNER]: False}
    a_proc, a_by = nodes_by_name(kids[A_INNER])
    changed[kids[A_INNER]] |= sync_related(kids[A_INNER], a_by[A_TAXES], a_proc['startEventId'], CHILD['Taxes'],
                                           [{'controlId': TAX_SEQUENCE, 'controlType': NUMBER, 'isAsc': True}])
    label = sub_params(pid, by[A_EACH])[LABEL_PARAM][0]
    changed[kids[A_INNER]] |= ensure_key_code(kids[A_INNER], a_by, a_proc['startEventId'],
                                              f'${PARAM_NODE}-{label}$')
    proc, by, kids, wanted = apply_wanted(f, pid)
    for p, name, kind, w in wanted:
        node = nodes_by_name(p)[1][name]
        if kind == 'search':
            hit = sync_search(p, node, w['worksheet'], w['filters'], w['kind'], w['action'],
                              execute_type=w.get('execute_type'), execute=w.get('execute'))
        elif kind == 'related':
            hit = sync_related(p, node, w['select'], w['field'], w['sorts'])
        elif kind == 'total':
            hit = sync_total(p, node, w['filters'], w['field'])
        else:
            hit = sync_formula(p, node, w['action'], w['expression'], number=w['number'],
                               null_zero=w['null_zero'], out_type=w.get('out_type'))
        if hit:
            print(f'  {name}: written')
        changed[p] |= hit
    by = nodes_by_name(pid)[1]
    for p, name, wanted_writes in apply_writes(pid, by, kids):
        changed[p] |= set_entries(p, nodes_by_name(p)[1][name], wanted_writes)
    a_by = nodes_by_name(kids[A_INNER])[1]
    changed[pid] |= sync_path_names(pid, by[A_BRANCH], {by[A_LINES]['id']: 'Yes', None: 'No'})
    changed[pid] |= sync_path_names(pid, by[A_ONE], {by[A_SINGLE]['id']: 'Yes', None: 'No'})
    changed[kids[A_INNER]] |= sync_path_names(kids[A_INNER], a_by[A_FOUND],
                                              {a_by[A_ADD]['id']: 'Found', a_by[A_NEG]['id']: 'Not found'})
    return changed


def ensure_apply(f):
    """Build or repair Apply Discount: the button once, the three workflows from `apply_nodes` onto an empty
    button workflow, then every step brought to `apply_wanted`; publish the children, then the parent, and only
    what changed."""
    from hap_cli.core.workflow_node_dsl import _new_control_id
    pid, created = ensure_apply_button(f)
    proc, by = nodes_by_name(pid)
    trigger = proc['startEventId']
    if proc['flowNodeMap'][trigger].get('nextId') in (None, '', '99'):
        params = {n: _new_control_id() for n in (LABEL_PARAM, VALUE_PARAM, DIVISOR_PARAM)}
        hap.run('workflow', 'node', 'batch-add', pid, '--nodes', json.dumps(apply_nodes(f, params), ensure_ascii=False),
                '--trigger-node-id', trigger, '--trigger-alias', 'trigger')
        created = True
    print('  backup:', hap.backup('orders_apply_discount_workflow', nodes_by_name(pid)[0]))
    changed = sync_apply(f, pid)
    kids = apply_children(pid, nodes_by_name(pid)[1])
    for name, inner in kids.items():
        if hap.ids().get('workflows', {}).get(KEY + name) != inner:
            C.remember('workflows', KEY + name, inner)
    if created or any(changed.values()):
        for name, inner in kids.items():
            print(f'  {name}: {C.publish(inner)}')
        print(f'  {APPLY}: {C.publish(pid)}')
    else:
        print(f'  {APPLY}: already built; not re-published')
    return created or any(changed.values())


PARENT_STEPS = (A_VARIANT, A_OLD, A_REMOVE, A_BRANCH, A_LINES, A_TOTAL, A_LABEL, A_DIVISOR, A_EACH, A_GROUPS,
                A_COUNT, A_ONE, A_SINGLE, A_PRICE)
INNER_STEPS = (A_A_VARIANT, A_TAXES, A_KEY, A_GROUP, A_FOUND, A_ADD, A_NEG, A_CREATE)
PRICE_STEPS = (A_SHARE, A_SET)


def steps_of(proc):
    return sorted(n['name'] for n in proc['flowNodeMap'].values()
                  if n.get('typeId') not in (None, 0, 100, BRANCH_PATH) and n.get('prveId'))


def apply_structure(f, pid):
    """What `sync_apply` does not repair, read back: the button, the three workflows' steps, the chain's
    record sources, the delete, the two sub-processes and what they pass, the two gateways' conditions, and
    that all three workflows are published. Returns a list of problems."""
    problems = []
    b = next((x for x in hap.listing('worksheet', 'custom-actions', ws()) if x['name'] == APPLY), None)
    if b is None:
        return [f'the {APPLY!r} button is missing — run `buttons`']
    if button_state(b) != button_wanted(apply_spec(f)) or (b.get('desc') or '') != APPLY_DESC:
        problems.append(f'{APPLY}: stored {button_state(b)} desc={b.get("desc")!r}, wanted '
                        f'{button_wanted(apply_spec(f))}')
    proc, by = nodes_by_name(pid)
    kids = apply_children(pid, by)
    for p, wanted in ((pid, PARENT_STEPS), (kids[A_INNER], INNER_STEPS), (kids[A_PRICE_INNER], PRICE_STEPS)):
        got = steps_of(nodes_by_name(p)[0]) if p else []
        if got != sorted(wanted):
            problems.append(f'workflow {p}: steps {got}, wanted {sorted(wanted)}')
    if problems:
        return problems
    trigger = proc['startEventId']
    typ, val = f[DISCOUNT_TYPE]['controlId'], f[DISCOUNT_VALUE]['controlId']
    a_proc, a_by = nodes_by_name(kids[A_INNER])
    b_proc, b_by = nodes_by_name(kids[A_PRICE_INNER])
    sources = [(pid, by, A_REMOVE, '3', A_OLD), (pid, by, A_SINGLE, '2', A_GROUPS),
               (kids[A_INNER], a_by, A_ADD, '2', A_GROUP), (kids[A_INNER], a_by, A_CREATE, '1', None),
               (kids[A_PRICE_INNER], b_by, A_SET, '2', b_proc['startEventId']),
               (pid, by, A_COUNT, OBJECT_TOTAL, A_GROUPS)]
    for p, names, step, action, source in sources:
        d = read_node(p, names[step]['id'])
        want_select = names[source]['id'] if source in names else (source or '')
        if (str(d.get('actionId')), d.get('selectNodeId') or '', bool(d.get('destroy')), bool(d.get('isException'))) \
                != (action, want_select, False, False):
            problems.append(f"{step}: actionId={d.get('actionId')} over {d.get('selectNodeId')!r} "
                            f"destroy={d.get('destroy')} exception={d.get('isException')}, wanted {action} over "
                            f'{want_select!r}, to the recycle bin')
    for step, over, inner, passes in (
            (A_EACH, A_LINES, kids[A_INNER], {LABEL_PARAM: f"${by[A_LABEL]['id']}-{STRING_FX}$"}),
            (A_PRICE, A_GROUPS, kids[A_PRICE_INNER], {VALUE_PARAM: f'${trigger}-{val}$',
                                                     DIVISOR_PARAM: f"${by[A_DIVISOR]['id']}-{STRING_FX}$"})):
        d = read_node(pid, by[step]['id'])
        got = {k: v[1] for k, v in sub_params(pid, by[step]).items()}
        if (d.get('selectNodeId'), d.get('executeType'), bool(d.get('nextExecute')), d.get('subProcessId'), got) != \
                (by[over]['id'], SEQUENTIAL, True, inner, passes):
            problems.append(f"{step}: over {d.get('selectNodeId')} executeType={d.get('executeType')} "
                            f"waits={d.get('nextExecute')} child={d.get('subProcessId')} passes {got}")
    paths = {n['id']: n for n in proc['flowNodeMap'].values() if n.get('typeId') == BRANCH_PATH}
    cond = lambda p_id: [[(c.get('filedId'), c.get('conditionId'),
                           [v.get('value') for v in c.get('conditionValues') or []]) for c in g]
                         for g in read_node(pid, p_id).get('conditions') or []]
    for gateway, wanted in ((A_BRANCH, {'No': [[(val, EMPTY, [])], [(val, '9', ['0'])], [(typ, EMPTY, [])]],
                                        'Yes': []}),
                            (A_ONE, {'Yes': [[(NUMBER_FX, '9', ['1'])]], 'No': []})):
        got = {p['name']: cond(p['id']) for p in paths.values() if p.get('prveId') == by[gateway]['id']}
        if got != wanted:
            problems.append(f'{gateway}: paths {got}, wanted {wanted}')
    for p in (pid, kids[A_INNER], kids[A_PRICE_INNER]):
        got = hap.run('workflow', 'get', p)
        got = got.get('data', got) if isinstance(got, dict) else {}
        if not got.get('enabled', True) or got.get('publishStatus') not in (None, 2):
            problems.append(f"workflow {p}: enabled={got.get('enabled')} publishStatus={got.get('publishStatus')} "
                            '— run `buttons` (it republishes what changed)')
    return problems


def apply_problems(f):
    """Apply Discount read back: its structure, then every step `sync_apply` owns compared without writing."""
    global DRIFT
    pid = hap.ids().get('workflows', {}).get(KEY + APPLY)
    if not pid:
        return [f'{APPLY}: no workflow id in ids.json — run `buttons`']
    problems = apply_structure(f, pid)
    if problems:
        return problems
    DRIFT = []
    try:
        sync_apply(f, pid)
        problems += [f'{APPLY}: {d}' for d in DRIFT]
    finally:
        DRIFT = None
    kids = apply_children(pid, nodes_by_name(pid)[1])
    for name, inner in kids.items():
        if hap.ids().get('workflows', {}).get(KEY + name) != inner:
            problems.append(f'{name}: ids.json does not hold {inner} — run `buttons`')
    if not problems:
        print(f"  OK  {APPLY:<17} btnId={hap.ids()['buttons'].get(KEY + APPLY)} isBatch=False when Status is not "
              f'Cancelled and Locked is not ticked\n'
              f'        then remove the Discount lines → if Discount Value is set, per product line ({A_INNER} '
              f'{kids[A_INNER]}) add its Subtotal to its tax group\'s Discount line, creating it the first time → '
              f'one tax group: its line named plainly ("Discount 10.00%" / "Discount") → per group ({A_PRICE_INNER} {kids[A_PRICE_INNER]}) '
              f'Unit Price × Value ÷ (100 | the product lines\' Total, tax included)')
    return problems


# ── 14d · driving Apply Discount from the CLI ───────────────────────────────
#
# `selfdiscount` presses the button through `hap workflow trigger`, as `selfdeliver` does, on DISCOUNT_ORDER — a
# Sales Order whose lines carry two tax combinations — and reads every line and the three roll-ups back through
# **both** read paths after each press: Global Discount 10%, the same again (still one set of lines), Fixed
# Amount 1,000, then 0 (every Discount line gone). It then proves the one-tax-group naming on the first order
# whose product lines share one tax combination, and puts both orders back exactly as they were. Like
# `selfdeliver`, it writes records by design and is not part of a "saves nothing" re-run.
from decimal import Decimal, ROUND_HALF_UP


def cents(x):
    return float(Decimal(str(x)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


def tax_order():
    """{tax rowid: (Sequence, Tax Name)} — Odoo joins a line's tax names in `account.tax` order."""
    tf = C.fields(TAXES_WS)
    return {r['rowid']: (number_of(r.get(tf['Sequence']['controlId'])) or 0, r.get(tf['Tax Name']['controlId']) or '')
            for r in C.records(TAXES_WS, APP)}


def order_lines(f_lines, order):
    """{line rowid: cells} for one order, through `record get`, and the same through the listing."""
    listing = listed_lines(f_lines)
    mine = lines_of(listing, order)
    return {r: line_cells(f_lines, r) for r in mine}, {r: listing[r] for r in mine}, listing


def discount_state(f, order):
    d = read_record(ws(), order)
    row = next((r for r in C.records(ws(), APP) if r['rowid'] == order), {})
    get = (read_cell(f[DISCOUNT_TYPE], d), read_cell(f[DISCOUNT_VALUE], d))
    listed = (option_keys(row.get(f[DISCOUNT_TYPE]['controlId'])), number_of(row.get(f[DISCOUNT_VALUE]['controlId'])))
    return get, listed


def set_discount(f, order, label, value):
    """Write Discount Type and Value, and read them back — a write that times out has been seen to land, so
    the read-back decides, not the answer."""
    key = option_key(f[DISCOUNT_TYPE], label) if label else None
    values = [{'id': f[DISCOUNT_TYPE]['controlId'], 'value': [key] if key else []},
              {'id': f[DISCOUNT_VALUE]['controlId'], 'value': '' if value is None else str(value)}]
    want = ([key] if key else [], None if value is None else float(value))
    for attempt in range(3):
        try:
            write_cells(order, values)
        except RuntimeError as e:
            print(f'    (the write answered {str(e)[:80]}… — reading it back)')
        for _ in range(10):
            got = discount_state(f, order)
            if got[0] == want and got[1] == want:
                return
            time.sleep(2)
    sys.exit(f'Discount Type/Value read back {discount_state(f, order)}, wanted {want}')


def expected_discount(before, taxes, label_kind, value):
    """Odoo's discount lines for these product lines: {sorted tax ids: (description, unit price)}, and what a Fixed
    Amount is taken over — Σ of the product lines' **Total**, tax included (`_reduce_base_lines_to_target_amount`).
    Each group's untaxed discount is its Subtotal × Value ÷ that sum."""
    groups, total = {}, 0
    for cells in before.values():
        if cells['Display Type'] != [PRODUCT_LINE]:
            continue
        groups.setdefault(tuple(sorted(cells['Taxes'])), []).append(cells['Subtotal'] or 0)
        total += cells['Total'] or 0
    label = f'Discount {Decimal(str(value)).quantize(Decimal("0.01"))}%' if label_kind == GLOBAL_DISCOUNT \
        else 'Discount'
    out = {}
    for key, subtotals in groups.items():
        g = sum(subtotals)
        share = cents(g * value / 100) if label_kind == GLOBAL_DISCOUNT else cents(value * g / total)
        names = ', '.join(taxes[t][1] for t in sorted(key, key=lambda t: taxes.get(t, (0, ''))))
        text = label if len(groups) == 1 else f'{label}- On products with the following taxes {names}'
        out[key] = (text, -share)
    return out, total


def wait_discount(f_lines, order, count, seconds=90):
    for _ in range(seconds // 3):
        got, listed, _ = order_lines(f_lines, order)
        disc = [r for r, c in got.items() if c['Product'] == [discount_variant()]]
        if len(disc) == count and all(got[r]['Subtotal'] is not None for r in disc):
            return
        time.sleep(3)


def check_press(f, f_lines, order, number, before, before_totals, taxes, label, value, problems):
    """Press, then compare every line and the roll-ups with Odoo's result, through both read paths."""
    want, total = expected_discount(before, taxes, label, value) if value else ({}, 0)
    press(APPLY, order)
    wait_discount(f_lines, order, len(want))
    time.sleep(3)
    got, listed, _ = order_lines(f_lines, order)
    disc = {r: c for r, c in got.items() if r not in before}
    gone = [r for r in before if r not in got]
    if gone:
        problems.append(f'{number}: lines {gone} disappeared')
    for r in before:
        if r in got and got[r] != before[r]:
            problems.append(f'{number}: line {r} moved: {before[r]} -> {got[r]}')
    seen = {}
    for r, c in disc.items():
        key = tuple(sorted(c['Taxes']))
        seen.setdefault(key, []).append(r)
        text, price = want.get(key, (None, None))
        exp = {'Orders': [order], 'Display Type': [PRODUCT_LINE], 'Product': [discount_variant()],
               'Description': text, 'Quantity': 1.0, 'Unit Price': price, 'Discount': 0.0, 'Sequence': 999.0,
               'Unit': [UNITS_UOM], 'Subtotal': price}
        bad = {k: (c.get(k), v) for k, v in exp.items() if c.get(k) != v}
        bad.update({f'{k} (listing)': (listed[r].get(k), v) for k, v in exp.items() if listed[r].get(k) != v})
        tax_ok = c['Tax Amount'] == listed[r]['Tax Amount'] and c['Total'] == listed[r]['Total'] and \
            c['Total'] == cents((c['Subtotal'] or 0) + (c['Tax Amount'] or 0))
        print(f"    {'OK  ' if not bad and tax_ok else 'FAIL'}  {c['Description']!r}  Unit Price {c['Unit Price']}  "
              f"Subtotal {c['Subtotal']}  Tax {c['Tax Amount']}  Total {c['Total']}  taxes "
              f"{[taxes.get(t, (0, t))[1] for t in c['Taxes']]}  (listing: {listed[r]['Subtotal']} / "
              f"{listed[r]['Tax Amount']} / {listed[r]['Total']})")
        if bad or not tax_ok:
            problems.append(f'{number} {label} {value}: line {r} {bad or "tax/total disagree"}')
    if sorted(seen) != sorted(want) or any(len(v) != 1 for v in seen.values()):
        problems.append(f'{number} {label} {value}: {len(disc)} discount line(s) over tax groups '
                        f'{[[taxes.get(t, (0, t))[1] for t in k] for k in seen]}, wanted one per group '
                        f'{[[taxes.get(t, (0, t))[1] for t in k] for k in want]}')
    drop = {'Untaxed Amount': cents(sum(c['Subtotal'] or 0 for c in disc.values())),
            'Tax': cents(sum(c['Tax Amount'] or 0 for c in disc.values())),
            'Total': cents(sum(c['Total'] or 0 for c in disc.values()))}
    wanted_totals = {n: cents(before_totals[n] + drop[n]) for n in TOTALS}
    after = wait_totals(f, order, wanted_totals)
    ok = after[0] == wanted_totals and after[1] == wanted_totals
    print(f"    {'OK  ' if ok else 'FAIL'}  {number} totals {before_totals} -> {after[0]} (record get) / "
          f'{after[1]} (listing); the discount lines sum to {drop}')
    if not ok:
        problems.append(f'{number} {label} {value}: totals {after}, wanted {wanted_totals}')
    return disc, drop, total


def single_group_order(f, f_lines, rows):
    """The first order (by number) with two or more product lines, all on one tax combination, no Discount line,
    not locked and not cancelled — the case Odoo names its line plainly."""
    listing = listed_lines(f_lines)
    for number, rowid in sorted(rows.items()):
        if number == DISCOUNT_ORDER:
            continue
        d = read_record(ws(), rowid)
        if read_cell(f['Locked'], d) == '1' or read_cell(f['Status'], d) == [STATUS_KEYS['Cancelled']]:
            continue
        mine = [listing[r] for r in lines_of(listing, rowid)]
        product = [c for c in mine if c['Display Type'] == [PRODUCT_LINE]]
        if len(product) >= 2 and len({tuple(sorted(c['Taxes'])) for c in product}) == 1 and \
                not any(c['Product'] == [discount_variant()] for c in mine) and \
                all(c['Subtotal'] is not None for c in product):
            return number, rowid
    return None, None


def step_selfdiscount():
    f = guard()
    f_lines = hap.by_name(c for c in hap.controls(LINES_WS) if c['type'] != C.TAB)
    rows, problems, taxes = by_number(), [], tax_order()
    order = rows[DISCOUNT_ORDER]

    # ── where the button is offered, by the server's own evaluation ──
    for number, rowid in sorted(rows.items()):
        d = read_record(ws(), rowid)
        wanted = read_cell(f['Status'], d) != [STATUS_KEYS['Cancelled']] and read_cell(f['Locked'], d) != '1'
        offered = buttons_offered(rowid).get(APPLY)
        if offered != wanted:
            problems.append(f'{APPLY} is {"offered" if offered else "not offered"} on {number} '
                            f'({status_label(read_cell(f["Status"], d))}, Locked {read_cell(f["Locked"], d)})')
    if not problems:
        print(f'  OK    {APPLY} is offered on every order that is neither locked nor cancelled, and on no other '
              f'(GetWorksheetBtns with each rowId)')

    # ── before ──
    start = discount_state(f, order)
    before, before_listed, before_all = order_lines(f_lines, order)
    before_totals = order_totals(f, order)
    if before_totals[0] != before_totals[1] or start[0] != start[1]:
        sys.exit(f'{DISCOUNT_ORDER}: the two read paths disagree before anything is written: {before_totals} {start}')
    if any(c['Product'] == [discount_variant()] for c in before.values()):
        sys.exit(f'{DISCOUNT_ORDER} already carries a Discount line — clear it with Value 0 first')
    before_totals = before_totals[0]
    print(f'  {DISCOUNT_ORDER} before: Discount Type/Value {start[0]}, totals {before_totals}')
    for r, c in sorted(before.items(), key=lambda x: x[1]['Sequence'] or 0):
        print(f"    {r}  {c['Description']!r}  Subtotal {c['Subtotal']}  taxes "
              f"{[taxes.get(t, (0, t))[1] for t in c['Taxes']]}")

    runs = ((GLOBAL_DISCOUNT, 10, 'Global Discount 10%'), (GLOBAL_DISCOUNT, 10, 'pressed again'),
            (FIXED_AMOUNT, 1000, 'Fixed Amount 1,000'), (FIXED_AMOUNT, 0, 'Value 0'))
    for label, value, title in runs:
        print(f'  ── {title} ──')
        set_discount(f, order, label, value)
        disc, drop, total = check_press(f, f_lines, order, DISCOUNT_ORDER, before, before_totals, taxes, label,
                                        value, problems)
        if title == 'Global Discount 10%' and drop['Untaxed Amount'] != -24722.50:
            problems.append(f'Global 10%: the untaxed total dropped by {drop["Untaxed Amount"]}, wanted -24722.50')
        if label == FIXED_AMOUNT and value:
            # Odoo: the order's Total drops by exactly the amount. Odoo gets there by nudging cents; nothing here
            # does, so a residual is reported to the cent — and more than a cent per tax group is a wrong split.
            residual = cents(drop['Total'] + float(value))
            print(f"    {'OK  ' if not residual else 'NOTE'}  the order's Total dropped by {-drop['Total']:.2f} for a "
                  f'Fixed Amount of {float(value):.2f} — residual {residual:+.2f} (Odoo corrects cents; this does '
                  f"not); untaxed {drop['Untaxed Amount']:+.2f}, tax {drop['Tax']:+.2f}")
            if abs(residual) > 0.01 * len(disc):
                problems.append(f'Fixed {value}: the Total dropped by {-drop["Total"]}, a residual of {residual}')
        if not value and disc:
            problems.append(f'Value 0 left {len(disc)} discount line(s)')

    # ── back as it was ──
    set_discount(f, order, None, None)
    after, after_listed, after_all = order_lines(f_lines, order)
    end = discount_state(f, order)
    if after != before or after_listed != before_listed or end != start or \
            order_totals(f, order) != (before_totals, before_totals):
        problems.append(f'{DISCOUNT_ORDER} was not restored: {end} {order_totals(f, order)}')
    else:
        print(f'  OK    {DISCOUNT_ORDER} reads as before through both paths: no Discount line, Discount Type and '
              f'Value empty, totals {before_totals}')
    others = sorted(r for r in before_all if r not in before and before_all[r] != after_all.get(r))
    if others:
        problems.append(f'{len(others)} line(s) of other orders moved: {others}')

    # ── one tax group: Odoo's plain name ──
    number, rowid = single_group_order(f, f_lines, rows)
    if not number:
        print('  note: no order has product lines on a single tax combination — the plain-name path is untested')
    else:
        print(f'  ── one tax group, on {number} ──')
        s_start = discount_state(f, rowid)
        s_before, s_listed, _ = order_lines(f_lines, rowid)
        s_totals = order_totals(f, rowid)[0]
        set_discount(f, rowid, GLOBAL_DISCOUNT, 10)
        check_press(f, f_lines, rowid, number, s_before, s_totals, taxes, GLOBAL_DISCOUNT, 10, problems)
        set_discount(f, rowid, GLOBAL_DISCOUNT, 0)
        check_press(f, f_lines, rowid, number, s_before, s_totals, taxes, GLOBAL_DISCOUNT, 0, problems)
        set_discount(f, rowid, None, None)
        s_after, s_after_listed, _ = order_lines(f_lines, rowid)
        if s_after != s_before or s_after_listed != s_listed or discount_state(f, rowid) != s_start or \
                order_totals(f, rowid) != (s_totals, s_totals):
            problems.append(f'{number} was not restored')
        else:
            print(f'  OK    {number} reads as before through both paths')
    if problems:
        print('  selfdiscount: ' + '\n                '.join(problems))
        sys.exit(1)
    print(f'  selfdiscount: OK — {APPLY} writes Odoo\'s discount lines, one per tax combination, replaces them on '
          f'a second press, removes them at 0, and {DISCOUNT_ORDER} is back as it was')


# ── 15 · Download: Terms and conditions, the templates, System Print ────────
#
# Odoo's *Download* (`sale.action_report_saleorder` — the tenant labels the button Download, the 19.0 source Print,
# and both hide it on a Sales Order) renders the quotation / order PDF. Here it is **System Print with a Word
# template**: native, so no button and no workflow (16-orders.md §3 row 2 and §9).
#
# 15a · **Terms and conditions** is Odoo's `sale.order.note`: `fields.Html(string="Terms and conditions",
# compute='_compute_note', store=True, readonly=False, precompute=True)` (addons/sale/models/sale_order.py). The
# form puts it on the Order Lines page in `note_group`, below the lines — the note on the left (colspan 4 of 6), the
# tax totals on the right — with the placeholder "Terms and conditions..." and **no readonly and no invisible
# condition**, in the 19.0 source and in the tenant extract alike. So no rule here names it.
#
# Rich text (41), modelled on Invoices' Terms and Conditions (`narration`, INVOICES_TERMS): full width,
# fieldPermission "111", Odoo's placeholder as the hint (HAP never draws a rich text's hint — BUILDING.md — so the
# hint is consistency, not behaviour). **Default empty**: Odoo's compute fills it from the company's default terms
# (`account.use_invoice_terms` with `invoice_terms` / `invoice_terms_html`), and this app has no company settings.
# That divergence is in 16-orders.md §9 and DECISIONS.md, never in the app.
#
# Appended with `C.append_controls`, never `C.add_fields`. The payload carries the Order Lines tab's `sectionId`,
# which `add-fields` keeps (BUILDING.md), so the control lands at the foot of that tab; its row is parked at 9999
# and **placement is the owner's**. TERMS_PLACE is the intent: a full-width row of its own directly below the lines
# and above Untaxed Amount · Tax · Total, which is where Invoices keeps its Terms and Conditions. Odoo sets it
# *beside* the totals; a HAP row cannot copy that, since a row has no row-span and the three totals fill row 12.
TERMS = 'Terms and conditions'
RICH_TEXT = 41
TERMS_ALIAS = 'note'
TERMS_TAB = '6ab0bfaf7d58b0f449316ad7'           # the Order Lines tab (type 52), not the subtable of that name
TERMS_PLACE = (12, 0, 12)                        # (row, col, size) in TERMS_TAB — only `size` survives the append
TERMS_HINT = 'Terms and conditions...'           # Odoo's placeholder
TERMS_PERMISSION = '111'                         # what Invoices' Terms and Conditions carries
TERMS_DESC = 'The terms printed at the foot of the quotation or order.'
INVOICES_TERMS = ('6aa90facf363582dd37a62f7', '6aa9f847e54d2a34fa4dfef2')     # Invoices › Terms and Conditions


def terms_control():
    return C.control('RICH_TEXT', TERMS, TERMS_PLACE, alias=TERMS_ALIAS, hint=TERMS_HINT, desc=TERMS_DESC,
                     extra={'fieldPermission': TERMS_PERMISSION, 'sectionId': TERMS_TAB})


def terms_spec():
    """What the control must read back as. Its tab, row and width are placement, the owner's, so not asserted."""
    return {'type': RICH_TEXT, 'alias': TERMS_ALIAS, 'desc': TERMS_DESC, 'hint': TERMS_HINT, 'required': False,
            'fieldPermission': TERMS_PERMISSION}


def terms_problems(f):
    c = f.get(TERMS)
    if c is None:
        return [f'{TERMS} is not on {WORKSHEET} — run `terms`']
    problems = []
    diff = drift(c, terms_spec())
    if diff:
        problems.append(f'{TERMS}: {json.dumps(diff, ensure_ascii=False, default=str)}')
    if c.get('default') or (c.get('advancedSetting') or {}).get('defsource'):
        problems.append(f"{TERMS}: carries a default ({c.get('default')!r} / "
                        f"{(c.get('advancedSetting') or {}).get('defsource')!r}); Odoo's comes from company "
                        'settings this app does not have, so it is empty here')
    if hap.ids().get('controls', {}).get(KEY + TERMS) != c['controlId']:
        problems.append(f'{TERMS}: ids.json does not hold {c["controlId"]} — run `terms`')
    return problems


def rules_naming(cid):
    return [r['name'] for r in hap.listing('worksheet', 'rules', ws())
            if any(x['controlId'] == cid for i in r['ruleItems'] for x in i['controls'])
            or any(x.get('controlId') == cid for g in r['filters'] for x in (g.get('groupFilters') or [g]))]


def step_terms():
    """Append Terms and conditions if it is missing, and read it back."""
    f = guard()
    if TERMS in f:
        print(f'  {TERMS} is already on {WORKSHEET}; nothing appended')
    else:
        model = next((c for c in hap.controls(INVOICES_TERMS[0]) if c['controlId'] == INVOICES_TERMS[1]), None)
        if not model or model['type'] != RICH_TEXT or model.get('fieldPermission') != TERMS_PERMISSION:
            sys.exit(f"Invoices' Terms and Conditions {INVOICES_TERMS[1]} no longer reads as the rich text, "
                     f'permission {TERMS_PERMISSION}, this control copies — re-read it before appending')
        tabs = {c['controlId']: c['controlName'] for c in hap.controls(ws()) if c['type'] == C.TAB}
        if tabs.get(TERMS_TAB) != ORDER_LINES:
            sys.exit(f'{TERMS_TAB} is {tabs.get(TERMS_TAB)!r}, not the {ORDER_LINES!r} tab — re-read the worksheet')
        hap.backup('orders_controls_pre_terms', hap.controls(ws()))
        C.append_controls(ws(), [terms_control()])
        f = C.fields(ws())
        if TERMS not in f:
            sys.exit(f'{TERMS} did not come back from the worksheet — the append did not store')
        print(f"  added {TERMS}: {f[TERMS]['controlId']} (t{f[TERMS]['type']}, row {f[TERMS].get('row')})")
    c = f[TERMS]
    if hap.ids().get('controls', {}).get(KEY + TERMS) != c['controlId']:
        C.remember('controls', KEY + TERMS, c['controlId'])
    problems = terms_problems(f)
    if problems:
        sys.exit('\n'.join(problems) + '\n  — not repaired automatically: read the control before a pinned save')
    tabs = {x['controlId']: x['controlName'] for x in hap.controls(ws()) if x['type'] == C.TAB}
    print(f"  OK  {TERMS:<21} {c['controlId']} t{c['type']} alias={c['alias']} perm={c.get('fieldPermission')} "
          f"tab={tabs.get(c.get('sectionId'), c.get('sectionId') or '-')} r{c.get('row')}c{c.get('col')} "
          f"s{c.get('size')} default empty")
    named = rules_naming(c['controlId'])
    print(f'  rules: {named or "none name it"} — Odoo puts no readonly or invisible condition on the field')
    if c.get('row') == 9999:
        print(f'  placement outstanding — the owner places it in the designer; intended: the {ORDER_LINES} tab, '
              f'(row, col, size) {TERMS_PLACE}, below the lines and above the totals')


# 15b · **The three Word templates** in nocoly/print-templates/ were re-pointed from the Sales app's control ids to
# ERP Master's on 21 Sep 2026, all but one placeholder: Terms & Conditions, which still named the Sales app's own
# rich text (SALES_TERMS, read to identify it and never written). `templates` re-points that one placeholder in all
# three files to the control 15a appended and changes nothing else: every other part of the .docx is copied byte for
# byte under its own ZipInfo, and the read-back proves the only difference is that id. The placeholder syntax is
# `#{<control id>}`, `#{<relation>.<control>}` into a related record or the lines, and a trailing `[S]` on some.
#
#   * TEMPLATE_GENERAL heads the page "<Status> # <Number>" — Quotation, Quotation Sent, Sales Order or Cancelled —
#     so it serves every state, as Odoo's one report does ("Quotation" / "Order" by state);
#   * TEMPLATE_QUOTATION heads it "Quotation # <Number>", TEMPLATE_ORDER "Order # <Number>".
PRINT_TEMPLATES = os.path.normpath(os.path.join(hap.HERE, os.pardir, 'print-templates'))
TEMPLATE_GENERAL = 'quotation_order_template.docx'
TEMPLATE_QUOTATION = 'quotation_template_quotation.docx'
TEMPLATE_ORDER = 'quotation_template_order.docx'
TEMPLATE_FILES = (TEMPLATE_GENERAL, TEMPLATE_QUOTATION, TEMPLATE_ORDER)
TEMPLATE_HEADS = {TEMPLATE_GENERAL: None, TEMPLATE_QUOTATION: 'Quotation # ', TEMPLATE_ORDER: 'Order # '}
TEMPLATE_PART = 'word/document.xml'
SALES_TERMS = '6a9e38cd4a22ad87b727b5d9'         # the Sales app's Orders › Terms and Conditions
PLACEHOLDER = re.compile(r'#\{([0-9a-f]{24})(?:\.([0-9a-f]{24}))?(?:\[[A-Z]\])?\}')


def placeholder(cid):
    return '#{' + cid + '}'


def template_parts(path):
    with zipfile.ZipFile(path) as z:
        return {i.filename: z.read(i) for i in z.infolist()}


def template_text(path):
    """The document's visible text, one paragraph a line."""
    xml = template_parts(path)[TEMPLATE_PART].decode('utf-8')
    return re.sub(r'<[^>]+>', '', xml.replace('</w:p>', '\n'))


def repoint(path, old, new):
    """Rewrite the .docx at `path` with `old` replaced by `new` in its document part; every other part is copied
    byte for byte under its own ZipInfo (name, date, compression, order)."""
    tmp = path + '.tmp'
    with zipfile.ZipFile(path) as src, zipfile.ZipFile(tmp, 'w') as dst:
        for info in src.infolist():
            data = src.read(info)
            if info.filename == TEMPLATE_PART:
                data = data.replace(old.encode(), new.encode())
            dst.writestr(info, data)
    os.replace(tmp, path)


def template_problems(f):
    """Each template must be a valid .docx whose Terms placeholder names this app's control, and every placeholder
    must name a live control — on Orders, or on the worksheet a relation or the lines subtable leads to."""
    problems = []
    if TERMS not in f:
        return [f'{TERMS} is not on {WORKSHEET} — run `terms`']
    orders = {c['controlId']: c for c in hap.controls(ws())}
    targets = {}
    for name in TEMPLATE_FILES:
        path = os.path.join(PRINT_TEMPLATES, name)
        with zipfile.ZipFile(path) as z:
            if z.testzip() is not None:
                problems.append(f'{name}: a corrupt zip member')
                continue
        parts = template_parts(path)
        for part, data in parts.items():
            if part.endswith('.xml') or part.endswith('.rels'):
                try:
                    ElementTree.fromstring(data)
                except ElementTree.ParseError as e:
                    problems.append(f'{name}: {part} is not well-formed XML ({e})')
        xml = parts[TEMPLATE_PART].decode('utf-8')
        counts = (xml.count(placeholder(SALES_TERMS)), xml.count(placeholder(f[TERMS]['controlId'])))
        if counts != (0, 1):
            problems.append(f'{name}: {counts[0]} Sales-app and {counts[1]} ERP Master Terms placeholders, wanted '
                            '0 and 1 — run `templates`')
        found = re.findall(r'#\{[^}]*\}', xml)
        for raw in found:
            m = PLACEHOLDER.fullmatch(raw)
            if not m:
                problems.append(f'{name}: {raw} is not a placeholder this check can read')
                continue
            head, tail = m.groups()
            if head not in orders:
                problems.append(f'{name}: {raw} — {head} is not a control on {WORKSHEET}')
            elif tail:
                target = (orders[head].get('dataSource') or '').strip('$')
                if target not in targets:
                    targets[target] = {c['controlId'] for c in hap.controls(target)} if target else set()
                if tail not in targets[target]:
                    problems.append(f'{name}: {raw} — {tail} is not on {orders[head]["controlName"]}\'s worksheet')
        head = TEMPLATE_HEADS[name]
        text = template_text(path)
        general = f"{placeholder(CONTROLS['Status'])} # {placeholder(CONTROLS['Number'])}"
        if head is None and general not in text:
            problems.append(f'{name}: does not head the page with Status before the Number')
        if head is not None and f"{head}{placeholder(CONTROLS['Number'])}" not in text:
            problems.append(f'{name}: does not head the page "{head}<Number>"')
    return problems


def step_templates():
    """Re-point the Terms placeholder in the three templates at this app's control, and read the files back."""
    f = guard()
    if TERMS not in f:
        sys.exit(f'{TERMS} is not on {WORKSHEET} — run `terms` first')
    old, new = placeholder(SALES_TERMS), placeholder(f[TERMS]['controlId'])
    for name in TEMPLATE_FILES:
        path = os.path.join(PRINT_TEMPLATES, name)
        before = template_parts(path)
        xml = before[TEMPLATE_PART].decode('utf-8')
        counts = (xml.count(old), xml.count(new))
        if counts == (0, 1):
            print(f'  {name}: already names {new}; nothing saved')
            continue
        if counts != (1, 0):
            sys.exit(f'{name}: {counts[0]} {old} and {counts[1]} {new}, wanted one of the first and none of the '
                     'second — left alone')
        os.makedirs(hap.BACKUPS, exist_ok=True)
        stamp = time.strftime('%Y%m%d-%H%M%S')
        kept = os.path.join(hap.BACKUPS, f'print-templates_{name[:-5]}_pre_terms_{stamp}.docx')
        shutil.copy2(path, kept)
        repoint(path, old, new)
        after = template_parts(path)
        changed = sorted(p for p in set(before) | set(after) if before.get(p) != after.get(p))
        if (changed != [TEMPLATE_PART] or list(after) != list(before)
                or after[TEMPLATE_PART] != before[TEMPLATE_PART].replace(old.encode(), new.encode())):
            shutil.copy2(kept, path)
            sys.exit(f'{name}: the rewrite changed {changed}, not only the Terms id — the original is put back')
        print(f'  {name}: {old} -> {new} (original kept as {os.path.relpath(kept, hap.HERE)})')
    problems = template_problems(f)
    if problems:
        sys.exit('\n'.join(problems))
    for name in TEMPLATE_FILES:
        n = len(re.findall(r'#\{[^}]*\}', template_parts(os.path.join(PRINT_TEMPLATES, name))[TEMPLATE_PART]
                           .decode('utf-8')))
        kind = ('general: heads the page "<Status> # <Number>"' if TEMPLATE_HEADS[name] is None
                else f'heads the page "{TEMPLATE_HEADS[name]}<Number>"')
        print(f'  OK  {name:<34} {kind}; {n} placeholders, every one a live control; valid zip and XML')


# 15c · **System Print.** HAP's main-site API has no single "upload a Word template" call, but pd-openweb — the
# platform's own open-source front end — shows the three the designer makes (src/pages/FormSet/components/
# EditPrint.jsx, `createUploader` and `onOk`):
#
#   1. `Qiniu/GetUploadToken {files: [{bucket: 3, ext: '.docx'}], type: 33}`, then the bytes to the file store —
#      hap-cli's own `upload._post_to_store`, which mirrors pd-openweb's uploader; the store answers the file `key`;
#   2. `AppManagement/GetToken {worksheetId, tokenType: 5}` — 5 is "Word print";
#   3. POST `<worksheet info downLoadUrl>/PrintTemplate/EditPrint` with `{token, worksheetId, accountId, doc: key,
#      fileName, id: '', type: 2, name, allowDownloadPermission: 0, allowEditAfterPrint: false,
#      advanceSettings: []}` — type 2 is Word; an empty `id` creates.
#
# `Worksheet/GetPrintList {worksheetId}` reads the result back. Only the general template is uploaded, as
# PRINT_NAME; the Quotation-only and Order-only files stay on disk. The Sales app's three Word templates carry the
# same defaults (download permission 0, no edit after print, no advance settings, range 1), read on 22 Sep 2026.
PRINT_NAME = 'Quotation / Order'
PRINT_KEY = KEY + PRINT_NAME                     # ids.json › prints
WORD_PRINT = 2                                   # a print template's type: 0 system · 2 Word · 5 Excel
WORD_PRINT_TOKEN = 5                             # AppManagement/GetToken tokenType: 3 export · 4 import · 5 Word print
PRINT_UPLOAD = 33                                # Qiniu/GetUploadToken `type` of the print-template uploader
DOC_BUCKET = 3                                   # the file store's document bucket


def print_templates():
    from hap_cli.core.session import Session
    out = Session.load(None).api_call('Worksheet', 'GetPrintList', {'worksheetId': ws()})
    return out if isinstance(out, list) else []


def print_problems():
    live = [p for p in print_templates() if p.get('name') == PRINT_NAME]
    if not live:
        return [f'no {PRINT_NAME!r} print template on {WORKSHEET} — run `print`, or upload it in the browser']
    if len(live) > 1:
        return [f'{len(live)} print templates named {PRINT_NAME!r}: {[p["id"] for p in live]}']
    p = live[0]
    want = {'type': WORD_PRINT, 'formName': TEMPLATE_GENERAL, 'disabled': False, 'worksheetId': ws()}
    got = {k: p.get(k) for k in want}
    problems = [f'{PRINT_NAME!r}: {got}, wanted {want}'] if got != want else []
    if hap.ids().get('prints', {}).get(PRINT_KEY) != p['id']:
        problems.append(f'{PRINT_NAME!r}: ids.json does not hold {p["id"]} — run `print`')
    return problems


def step_print():
    """Upload the general template as the System Print template PRINT_NAME on Orders, if it is not there."""
    from hap_cli.core import upload
    from hap_cli.core.session import Session
    f = guard()
    problems = template_problems(f)
    if problems:
        sys.exit('the template on disk is not ready:\n' + '\n'.join(problems))
    live = [p for p in print_templates() if p.get('name') == PRINT_NAME]
    if live:
        print(f'  {PRINT_NAME!r} is already on {WORKSHEET} ({live[0]["id"]}); nothing uploaded')
    else:
        s = Session.load(None)
        info = s.api_call('Worksheet', 'GetWorksheetInfo', {'worksheetId': ws(), 'getTemplate': False,
                                                            'getViews': False})
        base = (info or {}).get('downLoadUrl')
        if not base:
            sys.exit(f'GetWorksheetInfo gave no downLoadUrl: {json.dumps(info, ensure_ascii=False)[:300]}')
        path = os.path.join(PRINT_TEMPLATES, TEMPLATE_GENERAL)
        content = open(path, 'rb').read()
        token = s.api_call('Qiniu', 'GetUploadToken', {'files': [{'bucket': DOC_BUCKET, 'ext': '.docx'}],
                                                        'type': PRINT_UPLOAD})
        token = token[0] if isinstance(token, list) and token else token
        if not isinstance(token, dict) or not token.get('uptoken') or not token.get('key'):
            sys.exit(f'GetUploadToken answered {str(token)[:200]}')
        stored = upload._post_to_store(upload.upload_host(s), token, content,
                                       original_name=TEMPLATE_GENERAL[:-5], ext='.docx')
        key = stored.get('key') or token['key']
        print(f'  uploaded {TEMPLATE_GENERAL} ({len(content)} bytes) to the document store as {key}')
        word = s.api_call('AppManagement', 'GetToken', {'worksheetId': ws(), 'tokenType': WORD_PRINT_TOKEN})
        if not isinstance(word, str) or not word:
            sys.exit(f'AppManagement/GetToken answered {str(word)[:200]}')
        res = s._post(base.rstrip('/') + '/PrintTemplate/EditPrint', {
            'token': word, 'worksheetId': ws(), 'accountId': s.account_id, 'doc': key,
            'fileName': TEMPLATE_GENERAL, 'id': '', 'type': WORD_PRINT, 'name': PRINT_NAME,
            'allowDownloadPermission': 0, 'allowEditAfterPrint': False, 'advanceSettings': []}, 60)
        print(f'  EditPrint answered {json.dumps(res, ensure_ascii=False)[:200]}')
        live = [p for p in print_templates() if p.get('name') == PRINT_NAME]
        if len(live) != 1:
            sys.exit(f'{len(live)} print templates named {PRINT_NAME!r} read back — the upload did not store as '
                     'one template')
    C.remember('prints', PRINT_KEY, live[0]['id'])
    problems = print_problems()
    if problems:
        sys.exit('\n'.join(problems))
    p = live[0]
    print(f"  OK  {PRINT_NAME!r} {p['id']}: Word (type {p['type']}), file {p['formName']}, range {p.get('range')}, "
          f"views {p.get('views')}, filters {p.get('filters')}, download permission "
          f"{p.get('allowDownloadPermission')}, edit after print {p.get('allowEditAfterPrint')}")


# 15d · **Printing from the CLI.** pd-openweb's print page (src/pages/Print/core/util.js `getDownLoadUrl`) fills a
# Word template for one record with POST `<downLoadUrl>/ExportWord/GetWordPath {id, rowId, accountId, worksheetId,
# appId, projectId, t, viewId, token, download: 0}` — the token again `AppManagement/GetToken` type 5 — and gets
# back the address of the filled .docx. `selfprint` fills PRINT_NAME for PRINT_ORDER and reads the document **in
# memory** (nothing is written to disk); then puts a TEST value in the order's Terms and conditions, fills it again
# to prove that placeholder, and clears the value, read back empty through both read paths.
PRINT_ORDER = 'S00017'                           # a Sales Order with a customer, so the address block prints
TERMS_TEST = 'TEST terms - printed by System Print'
STATUS_HEAD = re.compile(r'(Quotation|Quotation Sent|Sales Order|Cancelled) # (S\d{5})')


def render(rowid):
    """The filled template's text for one order, a paragraph a line."""
    import io, requests
    from hap_cli.core.session import Session
    s = Session.load(None)
    info = s.api_call('Worksheet', 'GetWorksheetInfo', {'worksheetId': ws(), 'getTemplate': False,
                                                        'getViews': False})
    token = s.api_call('AppManagement', 'GetToken', {'worksheetId': ws(), 'viewId': '', 'tokenType': WORD_PRINT_TOKEN})
    url = s._post(info['downLoadUrl'].rstrip('/') + '/ExportWord/GetWordPath', {
        'id': hap.ids()['prints'][PRINT_KEY], 'rowId': rowid, 'accountId': s.account_id, 'worksheetId': ws(),
        'appId': APP, 'projectId': info['projectId'], 't': int(time.time() * 1000), 'viewId': '', 'token': token,
        'download': 0}, 90)
    if not isinstance(url, str) or not url.startswith('http'):
        sys.exit(f'GetWordPath answered {str(url)[:200]}')
    got = requests.get(url, timeout=60)
    got.raise_for_status()
    xml = zipfile.ZipFile(io.BytesIO(got.content)).read(TEMPLATE_PART).decode('utf-8')
    return [line for line in re.sub(r'<[^>]+>', '', xml.replace('</w:p>', '\n')).splitlines() if line.strip()]


def terms_cells(f, rowid):
    """Terms and conditions through both read paths: `record get`, then the listing."""
    cid = f[TERMS]['controlId']
    listed = next((r for r in C.records(ws(), APP) if r.get('rowid') == rowid), {})
    return read_record(ws(), rowid).get(cid), listed.get(cid)


def step_selfprint():
    """Fill the System Print template for PRINT_ORDER, once as it stands and once with a TEST Terms value, and put
    the order back."""
    f = guard()
    problems = print_problems()
    if problems:
        sys.exit('\n'.join(problems))
    rowid = by_number().get(PRINT_ORDER)
    if not rowid:
        sys.exit(f'{PRINT_ORDER} is not on {WORKSHEET}')
    before = terms_cells(f, rowid)
    if any(before):
        sys.exit(f'{PRINT_ORDER} already carries Terms and conditions {before} — not overwriting it')
    problems = []
    lines = render(rowid)
    heads = [m.groups() for m in map(STATUS_HEAD.fullmatch, lines) if m]
    if [h[1] for h in heads] != [PRINT_ORDER]:
        problems.append(f'the page is not headed "<Status> # {PRINT_ORDER}": {heads}')
    if any('#{' in line for line in lines):
        problems.append(f"placeholders left unfilled: {[line for line in lines if '#{' in line]}")
    for label in ('Untaxed Amount', 'Total', 'Terms &amp; Conditions'):
        if label not in lines:
            problems.append(f'{label!r} is not on the page')
    print(f'  {PRINT_ORDER}: {len(lines)} lines, headed {heads}, no placeholder left; the Terms heading prints '
          f'with nothing under it')
    try:
        write_cells(rowid, [{'id': f[TERMS]['controlId'], 'value': TERMS_TEST}])
        stored = terms_cells(f, rowid)
        print(f'  wrote {TERMS_TEST!r}; read back {stored}')
        lines = render(rowid)
        at = lines.index('Terms &amp; Conditions') if 'Terms &amp; Conditions' in lines else -1
        if at < 0 or TERMS_TEST not in lines[at + 1:at + 3]:
            problems.append(f'the TEST terms did not print under the Terms heading: {lines[at:at + 3]}')
        else:
            print(f'  printed under the Terms heading: {lines[at + 1]!r}')
    finally:
        write_cells(rowid, [{'id': f[TERMS]['controlId'], 'value': ''}])
    after = terms_cells(f, rowid)
    if any(after):
        problems.append(f'{PRINT_ORDER} still carries Terms and conditions {after} after the clear')
    if problems:
        print('  selfprint: ' + '\n             '.join(problems))
        sys.exit(1)
    print(f'  selfprint: OK — {PRINT_NAME!r} fills for {PRINT_ORDER}, prints its Terms and conditions, and the '
          f'order is back as it was (Terms and conditions empty on both read paths)')


# ── 16 · Send: the owner's Send Quotation, rewired ──────────────────────────
#
# Odoo's *Send* (`action_quotation_send`, addons/sale/models/sale_order.py:1069, 19.0 source) opens the mail
# composer on the order, addressed to the customer, with the template `_find_mail_template` (:1125) picks: *Sales:
# Send Quotation* (`email_template_edi_sale`) while the order is not a sale, *Sales: Order Confirmation*
# (`mail_template_sale_confirmation`) once it is (data/mail_template_data.xml). Both attach the quotation / order
# report (`report_template_ids` → `sale.action_report_saleorder`, named `Quotation - S00017` / `Order - S00017` by its
# `print_report_name`). Posting the message with `mark_so_as_sent` (`message_post`, :1716) writes **Quotation →
# Quotation Sent** and nothing else: `self.filtered(lambda o: o.state == 'draft')`. The form's two Send buttons are
# `invisible="state != 'draft'"` and `invisible="state not in ('sent', 'sale')"` (views/sale_order_views.xml
# 288–296, 336–342) — together, **every state but Cancelled**. *Send an email* (server action 505,
# `model_sale_order_send_mail`, bound to list, kanban and form) is the batch form.
#
# The owner built *Send Quotation* and a first workflow by hand on 21 Sep 2026 (it ran once, on S00004, to a TEST
# contact). It is **rewired, not replaced**: the button keeps its id, name, description, confirmation and condition
# (Status is Quotation, Quotation Sent or Sales Order — already Odoo's), and gains `isBatch`. **No node of theirs is
# deleted**: Get Customer, its found / not-found branch, their two-path branch, *Email quotation* and *Set Status:
# Quotation Sent* all stay, and the new steps are inserted around them:
#
#     Trigger by button (isBatch: once per selected order)
#       → Get Customer                         the owner's: the record the Customer relation points at
#       → (found / not found)                  the owner's result branch on it
#           not found → Missing customer                   站内通知 to the presser — the path ends
#           found     → Amount and signature               code block: Total as "RM 1,234.50"; "--" + Salesperson
#                     → Quotation or order?                the owner's branch (was *Branch*), exclusive, three paths
#                          Quotation         Status is Quotation or Quotation Sent, and the Email is not empty
#                              → Quotation file              获取记录打印文件: "Quotation / Order", "Quotation - S00017"
#                              → Email quotation             the owner's, rewritten to Odoo's quotation template
#                              → Set Status: Quotation Sent  the owner's
#                          Order             Status is Sales Order, and the Email is not empty
#                              → Order file                  "Order - S00017"
#                              → Email order confirmation    Odoo's confirmation template
#                          No email address  the Email is empty
#                              → Missing email address       站内通知 to the presser — the path ends
#
# **The status write sits on the Quotation path, which also carries Quotation Sent.** Writing Quotation Sent over
# Quotation Sent leaves it as it is, so the result is Odoo's "only a Quotation moves"; no workflow on Orders
# listens to Status (the app's worksheet-event workflows were read on 22 Sep 2026: none on Orders), so the
# same-value write starts nothing. A Sales Order runs the Order path, which writes nothing.
#
# **Two templates, two email steps.** Odoo's quotation template has a sale branch of its own, but the template that
# is actually used for a sales order is the confirmation template, so each path carries the text of the template
# Odoo would pick. The subject is Odoo's `{company} Quotation|Order (Ref {number})`; the company is **MyTech Products &
# Services**, the name the print templates head their page with (there are no company settings in this app). It was
# *casimir* until the 23 Sep 2026 demo rename. Odoo's optional
# *(with reference: …)* for a Source Document and its product-document list are not carried.
#
# **The amount is formatted by a code block** because a workflow text template inserts a number as stored; Odoo
# writes `format_amount(amount_total, currency)`, "RM 271,743.50". The same block turns the Salesperson into Odoo's
# signature ("--" and the salesperson's name, or nothing when there is none). Its logic is proved by `codeTest`,
# which only runs the code (no email): the three cases in SEND_CODE_TESTS must answer exactly as listed.
#
# **Nothing here sends email.** The step builds, publishes and reads back; it never triggers the workflow.
SEND = OWNERS_BUTTON
COMPANY = 'MyTech Products & Services'       # print-templates/quotation_order_template.docx heads its page with it
CONTACTS_WS = CONTACTS[0]
CONTACT_EMAIL, CONTACT_NAME = '6aa8a452f363582dd37a50d9', '6aa8a3b34a22ad87b728c4ff'
# the steps, by name — the owner's names are kept where the node is theirs
S_CUSTOMER = 'Get Customer'                  # the owner's
S_CODE = 'Amount and signature'
S_KIND = 'Quotation or order?'
S_KIND_WAS = 'Branch'                        # the owner's name for it, renamed on the first run
S_PRINT_Q, S_PRINT_O = 'Quotation file', 'Order file'
S_EMAIL_Q = 'Email quotation'                # the owner's
S_EMAIL_O = 'Email order confirmation'
S_STATUS = 'Set Status: Quotation Sent'      # the owner's
# A 站内通知 reads 【<node name>】<content> in the notification centre, so these two names are user-facing headings.
# *Missing email address* is Odoo's own label for a mail that could not go out for want of an address.
S_NO_CUSTOMER = 'Missing customer'
S_NO_EMAIL = 'Missing email address'
P_QUOTATION, P_ORDER, P_NO_EMAIL = 'Quotation', 'Order', 'No email address'
SEND_STEPS = (S_CUSTOMER, S_CODE, S_KIND, S_PRINT_Q, S_EMAIL_Q, S_STATUS, S_PRINT_O, S_EMAIL_O, S_NO_EMAIL,
              S_NO_CUSTOMER)
GATEWAY, FILE_NODE, EMAIL_NODE = 1, 18, 11   # flowNodeType: 分支 · 获取记录打印文件 · 发送邮件
FILE_APP, EMAIL_APP = 14, 3                  # the appType the editor adds those two with (CreateNodeDialog.jsx)
SEND_EMAIL, RELATED_RECORD = '202', '20'
FOUND, NOT_FOUND = 3, 4                      # a result branch's paths: 有数据 · 无数据
PLAIN_TEXT = 1                               # an email step's emailContentType: 1 text · 2 rich text · 3 MJML
NOT_EMPTY = '7'
# A PDF costs organisation credits per file on nocoly.com ("生成PDF文件的费用将自动从组织信用点中扣除",
# pd-openweb Detail/File) and needs the platform's conversion service (`wpsConfig`); see `send_pdf`.
SEND_PDF = True
MSG_NO_CUSTOMER = '{number} was not sent: it has no customer. Choose the customer, then send it again.'
MSG_NO_EMAIL = ("{number} was not sent: the customer has no email address. Add one to the customer's contact, then "
                'send it again.')
SEND_CODE_OUT = ('amount', 'signature')


def send_texts(trigger, code, f):
    """{step name: what it carries} — the two emails' subject and body, the two files' names, the two notices'
    messages. `$<node>-<field>$` is a workflow template: the trigger order's Number, the code block's outputs."""
    number = f"${trigger}-{f['Number']['controlId']}$"
    amount, sign = f'${code}-amount$', f'${code}-signature$'
    closing = f'Do not hesitate to contact us if you have any questions.\n{sign}'
    return {
        S_EMAIL_Q: (f'{COMPANY} Quotation (Ref {number})',
                    f'Hello,\n\nYour quotation {number} amounting in {amount} is ready for review.\n\n{closing}'),
        S_EMAIL_O: (f'{COMPANY} Order (Ref {number})',
                    f'Hello,\n\nYour order {number} amounting in {amount} has been confirmed.\n'
                    f'Thank you for your trust!\n\n{closing}'),
        S_PRINT_Q: f'Quotation - {number}',
        S_PRINT_O: f'Order - {number}',
        S_NO_CUSTOMER: MSG_NO_CUSTOMER.format(number=number),
        S_NO_EMAIL: MSG_NO_EMAIL.format(number=number),
    }


def send_code():
    """The code block: `amount` is the Total as Odoo's `format_amount` writes it for RM, "RM 271,743.50"; `signature`
    is "--" and the Salesperson's name on the next line, or empty with no salesperson — Odoo prints the salesperson's
    signature under the text only when there is one. A Member reaches a code block as JSON or as a name, so both are
    read; `seen` keeps the raw inputs for the run history."""
    return r"""function text(v) { return v === undefined || v === null ? '' : String(v).trim(); }
function money(v) {
  var s = text(v), n = parseFloat(s.replace(/[^0-9.\-]/g, ''));
  if (!s || isNaN(n)) return s;
  var parts = Math.abs(n).toFixed(2).split('.');
  return 'RM ' + (n < 0 ? '-' : '') + parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',') + '.' + parts[1];
}
function people(v) {
  var s = text(v);
  if (!s) return '';
  try {
    var j = JSON.parse(s);
    if (!Array.isArray(j)) j = [j];
    return j.map(function (x) {
      return x && typeof x === 'object' ? text(x.fullname || x.fullName || x.name) : text(x);
    }).filter(function (x) { return x; }).join(', ');
  } catch (e) { return s; }
}
var who = people(input.salesperson);
output = {
  amount: money(input.total),
  signature: who ? '--\n' + who : '',
  seen: JSON.stringify({total: input.total, salesperson: input.salesperson})
};
"""


def send_code_inputs(trigger, f):
    return [{'name': 'total', 'value': f"${trigger}-{f['Total']['controlId']}$"},
            {'name': 'salesperson', 'value': f"${trigger}-{f['Salesperson']['controlId']}$"}]


# (inputs, the outputs they must give). The last case runs last, so it is the one whose outputs are registered.
SEND_CODE_TESTS = [
    ({'total': '1,234', 'salesperson': ''}, {'amount': 'RM 1,234.00', 'signature': ''}),
    ({'total': '74.8', 'salesperson': 'Casimir Chiong Ming Yuan'},
     {'amount': 'RM 74.80', 'signature': '--\nCasimir Chiong Ming Yuan'}),
    ({'total': '271743.5', 'salesperson': '[{"accountId":"TEST","fullname":"Casimir Chiong Ming Yuan"}]'},
     {'amount': 'RM 271,743.50', 'signature': '--\nCasimir Chiong Ming Yuan'}),
]


# ── the button ──────────────────────────────────────────────────────────────

# What the button editor sends back on a save besides the name and texts (pd-openweb CreateCustomBtn.jsx).
BTN_SAVE_KEYS = ('isAllView', 'color', 'icon', 'writeControls', 'relationControl', 'writeType', 'writeObject',
                 'clickType', 'showType', 'advancedSetting', 'enableConfirm', 'verifyPwd', 'workflowType', 'isBatch')
BTN_VOLATILE = ('isBatch', 'updateTime', 'updateAccountId')
SEND_STATES = ('Quotation', 'Quotation Sent', 'Sales Order')


def send_button():
    live = [b for b in hap.listing('worksheet', 'custom-actions', ws()) if b['btnId'] == OWNERS_BUTTON_ID]
    if len(live) != 1 or live[0]['name'] != SEND:
        sys.exit(f'{OWNERS_BUTTON_ID} is not the one {SEND!r} button — read the worksheet before writing')
    return live[0]


def send_button_problems(b):
    """The button against what §16 needs: Odoo's states, batch, a workflow run, the confirmation kept."""
    label = {v: k for k, v in STATUS_KEYS.items()}
    conds = [(c.get('controlId'), c.get('filterType'), sorted(label.get(v, v) for v in c.get('values') or []))
             for c in b.get('filters') or []]
    want = [(CONTROLS['Status'], C.EQ, sorted(SEND_STATES))]
    problems = []
    if conds != want and [(cid, ft if ft != 51 else C.EQ, v) for cid, ft, v in conds] != want:
        problems.append(f'{SEND}: offered when {conds}, wanted Status is any of {list(SEND_STATES)}')
    if not b.get('isBatch'):
        problems.append(f'{SEND}: not usable on a selection (isBatch false) — run `send`')
    if b.get('workflowType') != 1 or b.get('showType') != 2 or not b.get('enableConfirm'):
        problems.append(f"{SEND}: workflowType={b.get('workflowType')} showType={b.get('showType')} "
                        f"enableConfirm={b.get('enableConfirm')}")
    return problems


def ensure_send_batch():
    """`isBatch` on, and nothing else about the owner's button changed: the save sends back exactly what the button
    editor sends, as read, and every key but `isBatch` is compared before and after."""
    from hap_cli.core.session import Session
    b = send_button()
    if b.get('isBatch'):
        return False
    if drifted(f'{SEND}: isBatch is off'):
        return True
    params = {'btnId': b['btnId'], 'name': b['name'], 'worksheetId': ws(), 'filters': b.get('filters') or [],
              'confirmMsg': b.get('confirmMsg') or '', 'sureName': b.get('sureName') or '',
              'cancelName': b.get('cancelName') or '', 'workflowId': b.get('workflowId') or '',
              'desc': b.get('desc') or '', 'appId': APP, 'addRelationControlId': b.get('addRelationControl') or '',
              **{k: b.get(k) for k in BTN_SAVE_KEYS}}
    params['isBatch'] = True
    got = Session.load(None).api_call('Worksheet', 'SaveWorksheetBtn', params)
    after = send_button()
    moved = sorted(k for k in set(b) | set(after) if k not in BTN_VOLATILE and b.get(k) != after.get(k))
    if not after.get('isBatch') or moved:
        sys.exit(f'{SEND}: SaveWorksheetBtn answered {got!r}; isBatch={after.get("isBatch")}, and {moved} changed '
                 f'with it — the button as it was is in backups/orders_send_pre_rebuild_*.json')
    print(f'  {SEND}: isBatch on; every other key of the button read back unchanged')
    return True


# ── the workflow, found by position ─────────────────────────────────────────

def chain(fm, start):
    """The node ids that follow `start` along `nextId`, up to the end of its path."""
    out, nid = [], fm[start].get('nextId')
    while nid not in (None, '', '99') and nid in fm and nid not in out:
        out.append(nid)
        nid = fm[nid].get('nextId')
    return out


def send_graph(pid):
    """The workflow's nodes by role. The owner left the result branch and its paths unnamed, so they are found by
    position: the step after the trigger is Get Customer, the gateway after it is its found / not-found branch, and
    the found path runs (through the code block, once it exists) into the second gateway."""
    proc = hap.run('workflow', 'node', 'list', pid)
    fm = proc['flowNodeMap']
    g = {'fm': fm, 'trigger': proc['startEventId']}
    cust = fm.get(fm[g['trigger']].get('nextId')) or {}
    if (cust.get('typeId'), str(cust.get('actionId')), cust.get('name')) != (UPDATE_NODE, RELATED_RECORD, S_CUSTOMER):
        sys.exit(f"{SEND}: the step after the trigger is {cust.get('name')!r} (type {cust.get('typeId')}), not the "
                 f'owner\'s {S_CUSTOMER!r} — read workflow {pid} before writing')
    g['customer'] = cust['id']
    gw = fm.get(cust.get('nextId')) or {}
    paths = {fm[p].get('resultTypeId'): p for p in gw.get('flowIds') or [] if p in fm}
    if gw.get('typeId') != GATEWAY or set(paths) != {FOUND, NOT_FOUND}:
        sys.exit(f'{SEND}: {S_CUSTOMER!r} is not followed by its found / not-found branch ({gw.get("typeId")}, '
                 f'{sorted(paths)})')
    g['result'], g['found'], g['none'] = gw['id'], paths[FOUND], paths[NOT_FOUND]
    nxt = fm.get(fm[g['found']].get('nextId')) or {}
    g['code'] = ''
    if nxt.get('typeId') == CODE_NODE:
        g['code'] = nxt['id']
        nxt = fm.get(nxt.get('nextId')) or {}
    if nxt.get('typeId') != GATEWAY or nxt.get('name') not in (S_KIND, S_KIND_WAS):
        sys.exit(f"{SEND}: the found path runs into {nxt.get('name')!r} (type {nxt.get('typeId')}), not the "
                 f'owner\'s branch')
    g['kind'] = nxt['id']
    ids = [p for p in nxt.get('flowIds') or [] if p in fm]
    # The owner's two paths come first, in the gateway's own order (Quotation · Order); the third is added after.
    g['paths'] = dict(zip((P_QUOTATION, P_ORDER, P_NO_EMAIL), ids))
    return g


def add_step(pid, prev_id, name, type_id, action='', app_type=None, app_id=''):
    """The step `name` directly after `prev_id`, inserted there when it is not (the path's next step then follows
    it). Returns (its id, True when added). A step of that name anywhere else stops the run."""
    from hap_cli.core import flow_node
    from hap_cli.core.session import Session
    fm = hap.run('workflow', 'node', 'list', pid)['flowNodeMap']
    old = fm[prev_id].get('nextId') or ''
    if old in fm and fm[old].get('name') == name:
        if fm[old].get('typeId') != type_id:
            sys.exit(f'{name!r} after {prev_id} is a type {fm[old].get("typeId")}, not {type_id}')
        return old, False
    elsewhere = [n['id'] for n in fm.values() if n.get('name') == name]
    if elsewhere:
        sys.exit(f'{name!r} is in workflow {pid} ({elsewhere}) but not after {fm[prev_id].get("name") or prev_id!r}'
                 ' — read it before writing')
    if drifted(f'{name!r} is missing after {fm[prev_id].get("name") or prev_id!r}'):
        return None, True
    flow_node.add_node(Session.load(None), pid, type_id, prev_id, name=name, action_id=action, app_id=app_id,
                       extra={'appType': app_type} if app_type is not None else None)
    fm = hap.run('workflow', 'node', 'list', pid)['flowNodeMap']
    new = fm[prev_id].get('nextId') or ''
    if new not in fm or fm[new].get('name') != name or fm[new].get('typeId') != type_id or \
            (fm[new].get('nextId') or '') not in ({old} if old else {'', '99'}):
        sys.exit(f'{name!r}: added after {prev_id}, but the chain reads {prev_id} → {new} '
                 f'({fm.get(new, {}).get("name")!r}) → {fm.get(new, {}).get("nextId")!r}, wanted → {old!r} — '
                 f'`hap workflow rollback {pid} -y` restores the published version')
    print(f'  {name!r}: added after {fm[prev_id].get("name") or prev_id!r} ({new})')
    return new, True


def add_path(pid, gateway_id):
    """A third path on the gateway (the editor's + on a branch: flowNode/add, typeId 2, prveId the gateway)."""
    from hap_cli.core import flow_node
    from hap_cli.core.session import Session
    fm = hap.run('workflow', 'node', 'list', pid)['flowNodeMap']
    before = list(fm[gateway_id].get('flowIds') or [])
    if drifted(f'{S_KIND!r} has {len(before)} paths, wanted 3'):
        return None
    flow_node.add_node(Session.load(None), pid, BRANCH_PATH, gateway_id)
    fm = hap.run('workflow', 'node', 'list', pid)['flowNodeMap']
    after = list(fm[gateway_id].get('flowIds') or [])
    added = [p for p in after if p not in before]
    if len(added) != 1 or after[:len(before)] != before:
        sys.exit(f'{S_KIND}: paths {before} became {after} — `hap workflow rollback {pid} -y` restores the '
                 f'published version')
    print(f'  {S_KIND!r}: third path added ({added[0]})')
    return added[0]


# ── the steps' configuration, compared before it is written ─────────────────

def cond(node_id, node_type, app_type, action, field, name, type_id, condition, values=()):
    """One branch-path condition, as `node save --type 2` takes it in `operateCondition`."""
    return {'nodeId': node_id, 'nodeType': node_type, 'appType': app_type, 'actionId': action, 'filedId': field,
            'filedValue': name, 'filedTypeId': type_id, 'enumDefault': 0, 'conditionId': condition,
            'sourceType': 0, 'conditionValues': list(values)}


def send_conditions(g):
    """{path name: its OR-of-AND condition groups} for the branch *Quotation or order?*."""
    status = lambda labels: cond(g['trigger'], 0, 8, '', CONTROLS['Status'], 'Status', DROPDOWN, IS_ANY_OF, [
        {'value': {'key': STATUS_KEYS[x], 'value': x, 'isDeleted': False, 'score': None, 'index': None}}
        for x in labels])
    email = lambda op: cond(g['customer'], UPDATE_NODE, 1, RELATED_RECORD, CONTACT_EMAIL, 'Email', 5, op)
    return {P_QUOTATION: [[status(['Quotation', 'Quotation Sent']), email(NOT_EMPTY)]],
            P_ORDER: [[status(['Sales Order']), email(NOT_EMPTY)]],
            P_NO_EMAIL: [[email(EMPTY)]]}


def cond_state(groups):
    return [[(c.get('nodeId'), c.get('filedId'), str(c.get('conditionId')),
              sorted(((v.get('value') or {}).get('key') if isinstance(v.get('value'), dict) else v.get('value'))
                     or '' for v in c.get('conditionValues') or []))
             for c in g] for g in groups or []]


def sync_path(pid, path_id, name, groups):
    """A path's name and condition groups; True when written."""
    got = read_node(pid, path_id)
    fm = hap.run('workflow', 'node', 'list', pid)['flowNodeMap']
    changed = False
    if cond_state(got.get('conditions')) != cond_state(groups):
        if drifted(f'path {name!r}: {cond_state(got.get("conditions"))}, wanted {cond_state(groups)}'):
            return True
        hap.run('workflow', 'node', 'save', pid, path_id, '--type', str(BRANCH_PATH),
                '-c', json.dumps({'operateCondition': groups}, ensure_ascii=False), '-n', name)
        back = read_node(pid, path_id)
        if cond_state(back.get('conditions')) != cond_state(groups):
            sys.exit(f'path {name!r}: condition reads back {cond_state(back.get("conditions"))}, wanted '
                     f'{cond_state(groups)} — `hap workflow rollback {pid} -y` restores the published version')
        changed = True
    if fm[path_id].get('name') != name:
        if drifted(f'path {fm[path_id].get("name")!r} should be named {name!r}'):
            return True
        hap.run('workflow', 'node', 'rename', pid, path_id, '-n', name)
        changed = True
    return changed


def sync_name(pid, node_id, name):
    fm = hap.run('workflow', 'node', 'list', pid)['flowNodeMap']
    if fm[node_id].get('name') == name:
        return False
    if drifted(f'{fm[node_id].get("name")!r} should be named {name!r}'):
        return True
    hap.run('workflow', 'node', 'rename', pid, node_id, '-n', name)
    return True


def sync_send_code(pid, node_id, trigger, f):
    """The code block's inputs and code, then codeTest — which runs only the code — on every case of
    SEND_CODE_TESTS; each must answer exactly as listed, and the last registers the outputs."""
    import base64
    from hap_cli.core import flow_node
    from hap_cli.core.session import Session
    b64 = lambda text: base64.b64encode(text.encode('utf-8')).decode('ascii')
    code, inputs = send_code(), send_code_inputs(trigger, f)
    got = read_node(pid, node_id)
    live_inputs = [(x.get('name'), x.get('value')) for x in got.get('inputDatas') or [] if x.get('name')]
    outputs = {c.get('controlId') for c in got.get('controls') or []}
    stale = (got.get('code') or '').strip() != code.strip() or \
        live_inputs != [(x['name'], x['value']) for x in inputs] or str(got.get('actionId')) != JAVASCRIPT
    if not stale and set(SEND_CODE_OUT) <= outputs:
        return False
    if drifted(f'{S_CODE}: code, inputs {live_inputs} or outputs {sorted(outputs)} differ'):
        return True
    if stale:
        flow_node.save_node(Session.load(None), pid, node_id, CODE_NODE,
                            {'actionId': JAVASCRIPT, 'inputDatas': inputs, 'code': b64(code),
                             'testMap': got.get('testMap') or {}, 'version': got.get('version') or '',
                             'maxRetries': got.get('maxRetries', 1)}, name=S_CODE)
        got = read_node(pid, node_id)
        if (got.get('code') or '').strip() != code.strip():
            sys.exit(f'{S_CODE}: the code did not store')
    for case, want in SEND_CODE_TESTS:
        test = flow_node.test_code(Session.load(None), pid, node_id, b64(code),
                                   [{**x, 'value': case[x['name']]} for x in inputs],
                                   action_id=JAVASCRIPT, version=got.get('version') or '')
        answer = code_answer(test)
        if {k: answer.get(k) for k in want} != want:
            sys.exit(f'{S_CODE}: codeTest on {case} answered {answer} ({json.dumps(test, ensure_ascii=False)[:500]}),'
                     f' wanted {want}')
        print(f'  codeTest {case} → {({k: answer.get(k) for k in want})}')
    got = read_node(pid, node_id)
    if not set(SEND_CODE_OUT) <= {c.get('controlId') for c in got.get('controls') or []}:
        sys.exit(f'{S_CODE}: codeTest registered {[c.get("controlId") for c in got.get("controls") or []]}, '
                 f'wanted {list(SEND_CODE_OUT)}')
    return True


def code_answer(test):
    """{output key: value} out of a codeTest answer, whichever of its shapes it comes in."""
    data = test.get('data', test) if isinstance(test, dict) else test
    for key in ('controls', 'outputs', 'output'):
        if isinstance(data, dict) and key in data:
            data = data[key]
            break
    if isinstance(data, list):
        return {c.get('controlId') or c.get('name'): c.get('value') for c in data if isinstance(c, dict)}
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except ValueError:
            return {}
    return data if isinstance(data, dict) else {}


def send_pdf(pid, node_id):
    """Whether the file steps also make a PDF: SEND_PDF, and only where the platform has the conversion service."""
    return SEND_PDF and bool(read_node(pid, node_id).get('wpsConfig'))


def sync_file(pid, node_id, name, select, file_name, pdf):
    """A 获取记录打印文件 step: the record (the trigger order), the System Print template, the file name, PDF."""
    from hap_cli.core import flow_node
    from hap_cli.core.session import Session
    template = hap.ids()['prints'][PRINT_KEY]
    got = read_node(pid, node_id)
    state = lambda d: (d.get('selectNodeId'), d.get('appId'), d.get('fileName'), bool(d.get('pdf')))
    want = (select, template, file_name, pdf)
    if state(got) == want:
        return False
    if drifted(f'{name}: {state(got)}, wanted {want}'):
        return True
    # The templates on offer depend on the record chosen, so they are read as the editor reads them once the
    # record is picked: getNodeDetail with that `selectNodeId` (pd-openweb Detail/File `getNodeDetail(props, sId)`).
    offered = Session.load(None).workflow_call('flowNode/getNodeDetail', {
        'processId': pid, 'nodeId': node_id, 'flowNodeType': FILE_NODE, 'selectNodeId': select}, method='GET')
    offered = (offered.get('data', offered) if isinstance(offered, dict) else {}).get('appList') or []
    if template not in {a.get('id') for a in offered}:
        sys.exit(f'{name}: {PRINT_NAME!r} {template} is not among the templates this step offers '
                 f'({[(a.get("id"), a.get("name")) for a in offered]})')
    flow_node.save_node(Session.load(None), pid, node_id, FILE_NODE,
                        {'selectNodeId': select, 'appId': template, 'fileName': file_name, 'pdf': pdf}, name=name)
    back = read_node(pid, node_id)
    if state(back) != want:
        sys.exit(f'{name}: reads back {state(back)}, wanted {want} — `hap workflow rollback {pid} -y` restores '
                 f'the published version')
    return True


def file_output(pid, email_id, file_id, pdf):
    """The file step's output an email can attach: what the email step's attachment picker offers from it."""
    from hap_cli.core.session import Session
    dtos = Session.load(None).workflow_call('flowNode/getFlowNodeAppDtos', {
        'processId': pid, 'nodeId': email_id, 'type': 14, 'enumDefault': 0}, method='GET')
    dtos = dtos.get('data', dtos) if isinstance(dtos, dict) else dtos
    entry = next((d for d in dtos or [] if d.get('nodeId') == file_id), None)
    controls = [c for c in (entry or {}).get('controls') or [] if c.get('type') == 14]
    pick = [c for c in controls if ('pdf' in (c.get('controlName') or '').lower()) == pdf]
    if len(pick) != 1:
        sys.exit(f'{file_id}: the attachment picker offers {[(c.get("controlId"), c.get("controlName")) for c in controls]}'
                 f' from it — wanted one {"PDF" if pdf else "Word"} file')
    return pick[0]


def email_account(g):
    """The customer's Email, reached through Get Customer — the recipient the owner's step already carries."""
    return {'type': 6, 'entityId': g['customer'], 'entityName': S_CUSTOMER, 'roleId': CONTACT_EMAIL,
            'roleTypeId': 0, 'roleName': 'Email', 'avatar': '', 'count': 0, 'controlType': 5,
            'flowNodeType': UPDATE_NODE, 'actionId': RELATED_RECORD, 'appType': 1}


def email_state(d):
    fields = {x.get('fieldId'): x for x in d.get('fields') or []}
    value = lambda k: (fields.get(k) or {}).get('fieldValue') or ''
    attach = fields.get('attachments') or {}
    return {'subject': value('subject'), 'content': value('content'), 'sender_name': value('sender_name'),
            'reply_email': value('reply_email'), 'attachment': (attach.get('nodeId') or '', attach.get('fieldValueId') or ''),
            'to': [(a.get('type'), a.get('entityId'), a.get('roleId')) for a in d.get('accounts') or []],
            'cc': len(d.get('ccAccounts') or []), 'bcc': len(d.get('bcAccounts') or []),
            'contentType': d.get('emailContentType'), 'exception': bool(d.get('isException'))}


def sync_email(pid, node_id, name, subject, body, account, attach):
    """An email step: to the customer's Email, the subject and body, the company as sender name, the file step's
    output attached, no reply address, cc or bcc, plain text."""
    from hap_cli.core import flow_node
    from hap_cli.core.session import Session
    got = read_node(pid, node_id)
    want = {'subject': subject, 'content': body, 'sender_name': COMPANY, 'reply_email': '',
            'attachment': (attach['nodeId'], attach['controlId']), 'to': [(6, account['entityId'], CONTACT_EMAIL)],
            'cc': 0, 'bcc': 0, 'contentType': PLAIN_TEXT, 'exception': False}
    if email_state(got) == want:
        return False
    if drifted(f'{name}: {email_state(got)}, wanted {want}'):
        return True
    fields = [dict(x) for x in got.get('fields') or []]
    by = {x.get('fieldId'): x for x in fields}
    missing = {'subject', 'content', 'sender_name', 'reply_email', 'attachments'} - set(by)
    if missing:
        sys.exit(f'{name}: the step carries no {sorted(missing)} field')
    for key, value in (('subject', subject), ('content', body), ('sender_name', COMPANY), ('reply_email', '')):
        by[key].update(fieldValue=value, nodeId='', fieldValueId='', isClear=False)
    by['attachments'].update(fieldValue='', nodeId=attach['nodeId'], sureNodeId=attach['nodeId'],
                             fieldValueId=attach['controlId'], nodeTypeId=FILE_NODE, nodeAppType=FILE_APP,
                             isClear=False)
    flow_node.save_node(Session.load(None), pid, node_id, EMAIL_NODE, {
        'fields': fields, 'actionId': SEND_EMAIL, 'appType': EMAIL_APP, 'accounts': [account], 'ccAccounts': [],
        'bcAccounts': [], 'emailContentType': PLAIN_TEXT, 'mjmlValue': '', 'mjmlHtml': ''}, name=name)
    back = email_state(read_node(pid, node_id))
    if back != want:
        sys.exit(f'{name}: reads back {back}, wanted {want} — `hap workflow rollback {pid} -y` restores the '
                 f'published version')
    return True


def sync_notice(pid, node_id, name, content, account=None):
    """A 站内通知 to the person who pressed the button — Confirm's guard (`save_notice`), compared first — or to
    `account` when one is given (§17 tells the order's Salesperson)."""
    account = account or TRIGGER_USER
    got = read_node(pid, node_id)
    key = lambda a: (a.get('type'), a.get('entityId'), a.get('roleId'))
    channel = got.get('flowNodeMap') or {}
    named = '106' not in channel or (channel['106'] or {}).get('name') == name
    if got.get('sendContent') == content and named and \
            [key(a) for a in got.get('accounts') or []] == [key(account)]:
        return False
    if drifted(f'{name}: message {got.get("sendContent")!r} to {[key(a) for a in got.get("accounts") or []]}'):
        return True
    return save_notice(pid, {'id': node_id, 'name': name}, content, dict(account))


def status_write_problems(pid, node_id, trigger):
    d = read_node(pid, node_id)
    live = [write_state(x) for x in d.get('fields') or []]
    want = [write_state(patch(CONTROLS['Status'], DROPDOWN, value=STATUS_KEYS['Quotation Sent']))]
    if (str(d.get('actionId')), d.get('selectNodeId'), live, bool(d.get('isException'))) != ('2', trigger, want, False):
        return [f'{S_STATUS}: actionId={d.get("actionId")} on {d.get("selectNodeId")} writes {live} '
                f'exception={d.get("isException")}, wanted Status = Quotation Sent on the trigger order']
    return []


def sync_send(f, pid):
    """Bring every step of the Send workflow to what §16 says. Returns True when something was written; under
    DRIFT (`check`) it writes nothing and records each difference."""
    changed = False
    g = send_graph(pid)
    code, hit = add_step(pid, g['found'], S_CODE, CODE_NODE, action=JAVASCRIPT)
    changed |= hit
    if code is None:
        return True
    changed |= sync_name(pid, g['kind'], S_KIND)
    g = send_graph(pid)
    if len(g['paths']) == 2:
        if add_path(pid, g['kind']) is None:
            return True
        changed = True
        g = send_graph(pid)
    if len(g['paths']) != 3:
        sys.exit(f'{S_KIND}: {len(g["paths"])} paths — this builder knows the owner\'s two and its own third')
    fm = g['fm']
    q_names = [fm[n].get('name') for n in chain(fm, g['paths'][P_QUOTATION])]
    if S_EMAIL_Q not in q_names or S_STATUS not in q_names:
        sys.exit(f'{S_KIND}: its first path runs {q_names}, not the owner\'s {S_EMAIL_Q!r} → {S_STATUS!r}')
    texts = send_texts(g['trigger'], code, f)
    changed |= sync_send_code(pid, code, g['trigger'], f)
    for name, groups in send_conditions(g).items():
        changed |= sync_path(pid, g['paths'][name], name, groups)
    steps = {}
    for name, prev, type_id, action, app_type in (
            (S_PRINT_Q, g['paths'][P_QUOTATION], FILE_NODE, '', FILE_APP),
            (S_PRINT_O, g['paths'][P_ORDER], FILE_NODE, '', FILE_APP),
            (S_EMAIL_O, S_PRINT_O, EMAIL_NODE, SEND_EMAIL, EMAIL_APP),
            (S_NO_EMAIL, g['paths'][P_NO_EMAIL], NOTICE, '', None),
            (S_NO_CUSTOMER, g['none'], NOTICE, '', None)):
        steps[name], hit = add_step(pid, steps.get(prev, prev), name, type_id, action=action, app_type=app_type)
        changed |= hit
        if steps[name] is None:
            return True
    g = send_graph(pid)
    fm = g['fm']
    steps[S_EMAIL_Q] = next(n for n in chain(fm, g['paths'][P_QUOTATION]) if fm[n].get('name') == S_EMAIL_Q)
    pdf = send_pdf(pid, steps[S_PRINT_Q])
    for name in (S_PRINT_Q, S_PRINT_O):
        changed |= sync_file(pid, steps[name], name, g['trigger'], texts[name], pdf)
    account = email_account(g)
    for name, file_step in ((S_EMAIL_Q, S_PRINT_Q), (S_EMAIL_O, S_PRINT_O)):
        subject, body = texts[name]
        attach = dict(file_output(pid, steps[name], steps[file_step], pdf), nodeId=steps[file_step])
        changed |= sync_email(pid, steps[name], name, subject, body, account, attach)
    for name in (S_NO_EMAIL, S_NO_CUSTOMER):
        changed |= sync_notice(pid, steps[name], name, texts[name])
    return changed


def send_structure(f, pid):
    """What `sync_send` leaves to position, read back: every path's chain, exactly, and that nothing follows a
    gateway or a notice; the owner's Get Customer and status write as they must be; no abort node. Returns
    (problems, the graph)."""
    g = send_graph(pid)
    fm, problems = g['fm'], []
    names = lambda start: [fm[n].get('name') for n in chain(fm, start)]
    want = {'the trigger': (g['trigger'], [S_CUSTOMER]),
            'found': (g['found'], [S_CODE, S_KIND]),
            'not found': (g['none'], [S_NO_CUSTOMER]),
            P_QUOTATION: (g['paths'].get(P_QUOTATION), [S_PRINT_Q, S_EMAIL_Q, S_STATUS]),
            P_ORDER: (g['paths'].get(P_ORDER), [S_PRINT_O, S_EMAIL_O]),
            P_NO_EMAIL: (g['paths'].get(P_NO_EMAIL), [S_NO_EMAIL])}
    for label, (start, steps) in want.items():
        got = names(start) if start else None
        if label == 'the trigger':
            got = got[:1] if got else got
            if fm[g['result']].get('nextId') not in (None, '', '99'):
                problems.append(f"the found / not-found branch runs into {fm[fm[g['result']]['nextId']].get('name')!r}")
        if got != steps:
            problems.append(f'{label}: runs {got}, wanted {steps}')
    if fm[g['kind']].get('nextId') not in (None, '', '99'):
        problems.append(f'{S_KIND!r} runs into {fm[fm[g["kind"]]["nextId"]].get("name")!r} — nothing may follow it')
    if [fm[p].get('name') for p in fm[g['kind']].get('flowIds') or []] != [P_QUOTATION, P_ORDER, P_NO_EMAIL]:
        problems.append(f'{S_KIND}: paths {[fm[p].get("name") for p in fm[g["kind"]].get("flowIds") or []]}')
    aborts = [n.get('name') for n in fm.values() if n.get('typeId') == ABORT]
    if aborts:
        problems.append(f'abort node(s) {aborts} — an aborted run draws HAP\'s untranslated 中止 toast')
    extra = sorted(n.get('name') for n in fm.values() if n.get('typeId') not in (None, 0, 100, BRANCH_PATH, GATEWAY)
                   and n.get('prveId') and n.get('name') not in SEND_STEPS)
    if extra:
        problems.append(f'steps this builder does not know: {extra}')
    cust = read_node(pid, g['customer'])
    fields = [x.get('fieldId') for x in cust.get('fields') or []]
    if (str(cust.get('actionId')), cust.get('selectNodeId'), fields) != (RELATED_RECORD, g['trigger'],
                                                                          [CONTROLS['Customer']]):
        problems.append(f"{S_CUSTOMER}: actionId={cust.get('actionId')} from {cust.get('selectNodeId')} over "
                        f'{fields}, wanted the trigger order\'s Customer')
    status = next((n for n in chain(fm, g['paths'].get(P_QUOTATION) or g['found']) if fm[n].get('name') == S_STATUS),
                  None)
    problems += status_write_problems(pid, status, g['trigger']) if status else [f'{S_STATUS!r} is missing']
    return problems, g


def send_published(pid):
    got = hap.run('workflow', 'get', pid)
    got = got.get('data', got) if isinstance(got, dict) else {}
    if not got.get('enabled') or got.get('publishStatus') != 2:
        return [f'workflow {pid}: enabled={got.get("enabled")} publishStatus={got.get("publishStatus")} — '
                'unpublished changes; run `send`']
    return []


def send_offered():
    """{order number: offered?} as the server evaluates the button on each order (GetWorksheetBtns with a rowId —
    what the record page asks; no workflow runs)."""
    f = C.fields(ws())
    out = {}
    for r in C.records(ws(), APP):
        out[r.get(f['Number']['controlId'])] = (buttons_offered(r['rowid']).get(SEND),
                                                status_label(json_keys(r.get(f['Status']['controlId']))))
    return out


def json_keys(raw):
    try:
        raw = json.loads(raw) if isinstance(raw, str) else raw
    except ValueError:
        return [raw]
    return [x.get('key') if isinstance(x, dict) else x for x in raw or []]


def send_problems(f):
    """The Send button and workflow read back: the button, the structure, every step's configuration compared
    without writing, the enabled states as the server evaluates them, and that the workflow is published."""
    global DRIFT
    b = send_button()
    problems = send_button_problems(b)
    pid = hap.ids().get('workflows', {}).get(KEY + SEND)
    if pid != OWNERS_WORKFLOW:
        return problems + [f'{SEND}: ids.json holds workflow {pid!r}, not {OWNERS_WORKFLOW} — run `send`']
    found, g = send_structure(f, pid)
    problems += found
    if found:
        return problems
    DRIFT = []
    try:
        sync_send(f, pid)
        problems += [f'{SEND}: {d}' for d in DRIFT]
    finally:
        DRIFT = None
    problems += send_published(pid)
    offered = send_offered()
    wrong = {n: (on, st) for n, (on, st) in offered.items() if bool(on) != (st in SEND_STATES)}
    if wrong:
        problems.append(f'{SEND}: offered wrongly on {wrong} — it must be offered exactly on {list(SEND_STATES)}')
    if not problems:
        print(f"  OK  {SEND:<17} btnId={b['btnId']} isBatch={bool(b.get('isBatch'))} when Status is any of "
              f'{list(SEND_STATES)} (server: offered on '
              f"{sorted(n for n, (on, _) in offered.items() if on)}, not on "
              f"{sorted(n for n, (on, _) in offered.items() if not on)})\n"
              f'        then {S_CUSTOMER} → not found: {S_NO_CUSTOMER!r} | found: {S_CODE} → {S_KIND} '
              f'[{P_QUOTATION}: {S_PRINT_Q} → {S_EMAIL_Q} → {S_STATUS} | {P_ORDER}: {S_PRINT_O} → {S_EMAIL_O} | '
              f'{P_NO_EMAIL}: {S_NO_EMAIL!r}] — published, nothing sent')
    return problems


def send_untouched():
    """What `send` must not move: every other button and the whole control set."""
    others = sorted((b for b in hap.listing('worksheet', 'custom-actions', ws()) if b['btnId'] != OWNERS_BUTTON_ID),
                    key=lambda b: b['btnId'])
    return {'the other buttons': json.dumps(others, ensure_ascii=False, sort_keys=True, default=str),
            'the control set': json.dumps(signature(hap.controls(ws())), ensure_ascii=False, sort_keys=True,
                                          default=str)}


def step_send():
    """§16: rewire the owner's *Send Quotation* — `isBatch` on the button, then the workflow brought to §16's
    shape around the owner's own steps. Publishes only when something changed; **never triggers it** — pressing it
    emails a real customer. Re-runnable: every step is found by position or name and compared before it is
    written; a second run saves and publishes nothing."""
    f = guard()
    for name in ('Number', 'Total', 'Salesperson', 'Customer', 'Status'):
        if name not in f:
            sys.exit(f'{name} is not on {WORKSHEET}; the Send workflow reads it')
    if hap.ids().get('prints', {}).get(PRINT_KEY) is None or print_problems():
        sys.exit(f'System Print {PRINT_NAME!r} is not in place — run `print` first; {SEND} attaches it')
    before = send_untouched()
    pid = OWNERS_WORKFLOW
    proc = hap.run('workflow', 'node', 'list', pid)
    if read_node(pid, proc['startEventId']).get('triggerId') != OWNERS_BUTTON_ID:
        sys.exit(f'workflow {pid} is not started by {SEND} {OWNERS_BUTTON_ID}')
    C.remember('workflows', KEY + SEND, pid)
    C.remember('buttons', KEY + SEND, OWNERS_BUTTON_ID)
    print('  backup:', hap.backup('orders_send_pre_rebuild', {
        'button': send_button(), 'workflow': proc,
        'nodes': {nid: {k: v for k, v in read_node(pid, nid).items()
                        if k not in ('flowNodeList', 'flowNodeAppDtos', 'controls', 'appList')}
                  for nid, n in proc['flowNodeMap'].items() if n.get('typeId') not in (None, 100)}}))
    changed = ensure_send_batch()
    wrote = sync_send(f, pid)
    problems, g = send_structure(f, pid)
    if problems:
        sys.exit('  not published:\n  ' + '\n  '.join(problems) +
                 f'\n  `hap workflow rollback {pid} -y` restores the published version')
    if wrote or send_published(pid):
        res = C.publish(pid)
        print(f'  {SEND}: {res}')
        if not res.get('isPublish') or res.get('processWarnings') or res.get('errorNodeIds'):
            sys.exit(f'{SEND}: publish answered {res} — the draft stays unpublished; '
                     f'`hap workflow rollback {pid} -y` restores the published version')
    else:
        print(f'  {SEND}: already built; not re-published')
    after = send_untouched()
    moved = sorted(k for k in before if before[k] != after[k])
    if moved:
        sys.exit(f'{WORKSHEET}: {moved} changed while {SEND} was rebuilt — `send` writes none of them')
    print(f'  untouched, byte for byte: {sorted(before)}')
    problems = send_problems(f)
    if problems:
        sys.exit('  ' + '\n  '.join(problems))
    print(C.structure(pid))
    return changed or wrote


def step_sendreach():
    """Read-only: whose inbox each order's Send would reach — every order, its state, whether the server offers
    the button on it, its customer and whether that customer has an Email (both record read paths)."""
    f = guard()
    emails = {}
    for r in C.records(CONTACTS_WS, APP):
        listed = r.get(CONTACT_EMAIL) or ''
        got = read_record(CONTACTS_WS, r['rowid'])
        emails[r['rowid']] = (r.get(CONTACT_NAME), listed or got.get('email') or got.get(CONTACT_EMAIL) or '')
    offered = send_offered()
    for r in sorted(C.records(ws(), APP), key=lambda r: r.get(f['Number']['controlId']) or ''):
        number = r.get(f['Number']['controlId'])
        cust = [x.get('sid') for x in json.loads(r.get(f['Customer']['controlId']) or '[]')] \
            if isinstance(r.get(f['Customer']['controlId']), str) else \
            [x.get('sid') for x in r.get(f['Customer']['controlId']) or []]
        who = [emails.get(c, ('?', '')) for c in cust]
        on, state = offered.get(number, (None, '?'))
        print(f"  {number}  {state:<15} {'offered' if on else 'not offered':<12} "
              + (', '.join(f"{n}: {'has an email' if e else 'no email'}" for n, e in who) or 'no customer'))
    print('  contacts with an email: ' + ', '.join(sorted(n for n, e in emails.values() if e)))


# ── 17 · Sign & Accept: the customer signs and accepts online ───────────────
#
# Odoo's *Accept & Sign* is a **portal** action, not a back-end button (16-orders.md §3 row 8): the customer opens the
# quotation's portal page and signs, and `portal_quote_accept` (addons/sale/controllers/portal.py:318, 19.0 source)
# refuses unless `_has_to_be_signed()` (sale_order.py:1896) — Status Quotation or Quotation Sent, not expired
# (`validity_date < today`, so the Expiration day itself still counts), Online Signature ticked, no signature yet —
# then writes `signed_by`, `signed_on = now` and `signature`, and, **unless online payment is required**
# (`_has_to_be_paid`), confirms through `_validate_order` → `action_confirm`: the same missing-product check as the
# Confirm button, then Status → Sales Order and the date → now. It also posts the signed PDF on the chatter and emails
# the confirmation; neither is built here (credits — see 16-orders.md §11).
#
# **The owner chose the platform's own no-login form for it: the workflow Get Link node (获取链接, flowNodeType 15),
# fill-in type (填写链接, `linkType` 2).** pd-openweb `WorkflowSettings/Detail/Link/index.jsx` is the node's editor and
# what `sync_link` sends: `selectNodeId` (the record), `linkType`, `linkName`, `formProperties` (one entry per control,
# `property` 1 view · 2 edit · 3 edit and required · 4 hidden), `time` (the link's validity: `enable`, `type` 1 a
# duration · 2 a date, `executeTime` the date's source, `dayTime` the hour on a Date field — "08:00" unless set),
# `password`, `submitButtonName`, `submitType` (0: after submitting, neither view nor modify), `modifyTime`,
# `addNotAllowView` (a control added later is hidden by default) and `viewId`. The editor adds the node with
# `typeId 15, appType 13` and no action (CreateNodeDialog.jsx).
#
#     Share for Signature (button, one order; offered while Status is Quotation or Quotation Sent, Online Signature
#     is ticked, Signature is empty and Expiration is empty or today or later)
#       Trigger by button
#         → Does the quotation expire?                        branch on Expiration
#              Expiration is set  → Signing link until the expiration date     Get Link, ends at 23:59 that day
#                                 → Save the link (until the expiration date)  Signing Link ← the link
#              No expiration date → Signing link with no end date             Get Link, no end
#                                 → Save the link (no end date)                Signing Link ← the link
#
#     Signed: confirm the order (worksheet event: an order updated, Signature among the fields written, and only
#     while Signature is filled, Status is Quotation or Quotation Sent and Online Signature is ticked)
#       → Set Signed On                                        Signed On ← now
#       → Product lines with no product                        Confirm's own count
#       → Is a product line missing its product?
#            Yes → Quotation signed, not confirmed             站内通知 to the Salesperson — the path ends
#            No  → Is online payment required?
#                    Yes → Quotation signed, payment due       站内通知 — it stays a quotation, as Odoo's does
#                    No  → Confirm the order                   Confirm's own writes: Status, Quotation/Order Date
#                        → Quotation signed                    站内通知: "S000xx was signed by <Signed By>."
#
# **Set to Quotation clears Signature**, which is a write of Signature, so the second workflow is narrowed by a
# trigger condition rather than a first branch: a cleared Signature fails it and **no run starts at all**.
#
# **Divergences** (DECISIONS.md, *Orders · Sign & Accept*): the customer types their name — Odoo pre-fills it with the
# portal partner's; no signed PDF and no confirmation email yet (credits); a signature whose order fails the product
# check **stays** (Odoo rolls the whole request back, signature included) and the salesperson is told; "online
# payment required" is the Online Payment checkbox alone — Odoo also needs a positive total and no payment done.
SIGNING_LINK = 'Signing Link'
# Odoo has no field for the link itself; `portal.mixin`'s `access_url` is the nearest — the customer-facing URL of the
# document, which `get_portal_url()` completes with the access token. The alias follows the convention (Odoo names).
SIGNING_LINK_ALIAS = 'access_url'
# Intent, for the owner: its own full-width row directly under Signature, Signed By and Signed On (row 6 when this was
# written). `add-fields` parks it at row 9999 and only a full save places it — the owner's to do in the designer.
SIGNING_LINK_PLACE = (7, 0, 12)
SIGNING_LINK_PERMISSION = READ_ONLY_PERMISSION    # "100": read-only and off the create form; a workflow writes it
SIGNING_LINK_DESC = 'Copy this link and send it to the customer so they can sign and accept the quotation online.'


def signing_link_control():
    """A single-line Text: HAP has no URL control, and a Text's `analysislink` "1" — every Text on Orders carries it
    — draws a URL in it as a link the salesperson can open or copy."""
    return C.control('TEXT', SIGNING_LINK, SIGNING_LINK_PLACE, alias=SIGNING_LINK_ALIAS, hint='',
                     desc=SIGNING_LINK_DESC, extra={'fieldPermission': SIGNING_LINK_PERMISSION},
                     advanced_setting={'analysislink': '1'})


def signing_link_spec():
    """What it must read back as. Row, column and tab are placement — the owner's — so not asserted."""
    return {'type': TEXT, 'alias': SIGNING_LINK_ALIAS, 'desc': SIGNING_LINK_DESC, 'required': False,
            'fieldPermission': SIGNING_LINK_PERMISSION, 'enumDefault': 2, 'advancedSetting.analysislink': '1'}


def signing_link_problems(f):
    c = f.get(SIGNING_LINK)
    if c is None:
        return [f'{SIGNING_LINK} is not on {WORKSHEET} — run `signlink`']
    problems = []
    diff = drift(c, signing_link_spec())
    if diff:
        problems.append(f'{SIGNING_LINK}: {json.dumps(diff, ensure_ascii=False, default=str)} — run `signlink`')
    if hap.ids().get('controls', {}).get(KEY + SIGNING_LINK) != c['controlId']:
        problems.append(f'{SIGNING_LINK}: ids.json does not hold {c["controlId"]} — run `signlink`')
    return problems


def step_signlink():
    """Append Signing Link if it is missing, repair what the append did not store in one version-pinned save limited
    to that control (`step_part1`'s pattern), and read it back. Re-running saves nothing."""
    f = guard()
    for name in PART1[1:]:
        if name not in f:
            sys.exit(f'{name} is not on {WORKSHEET} — run `part1` first')
    if SIGNING_LINK in f:
        print(f'  {SIGNING_LINK} is already on {WORKSHEET}; nothing appended')
    else:
        hap.backup('orders_controls_pre_signlink', hap.controls(ws()))
        C.append_controls(ws(), [signing_link_control()])
        f = C.fields(ws())
        if SIGNING_LINK not in f:
            sys.exit(f'{SIGNING_LINK} did not come back from the worksheet — the append did not store')
        print(f"  added {SIGNING_LINK}: {f[SIGNING_LINK]['controlId']} (t{f[SIGNING_LINK]['type']}, row "
              f"{f[SIGNING_LINK].get('row')} col {f[SIGNING_LINK].get('col')} size {f[SIGNING_LINK].get('size')})")
    c = f[SIGNING_LINK]
    spec = signing_link_spec()
    stale = drift(c, spec)
    if stale:
        print('  the append did not store everything; repairing in one version-pinned save:')
        for k, (got, want) in stale.items():
            print(f'    {SIGNING_LINK}.{k}: {got!r} -> {want!r}')
        if not pinned_write('signlink', {c['controlId']: {k: spec[k] for k in stale}},
                            'orders_controls_pre_signlink_repair'):
            sys.exit('the repair found nothing to write, which contradicts the drift above')
        f = C.fields(ws())
        c = f[SIGNING_LINK]
    C.remember('controls', KEY + SIGNING_LINK, c['controlId'])
    problems = signing_link_problems(f)
    if problems:
        sys.exit('\n'.join(problems))
    print(f"  OK  {SIGNING_LINK:<13} {c['controlId']} t{c['type']} alias={c.get('alias')} "
          f"perm={c.get('fieldPermission')} analysislink={(c.get('advancedSetting') or {}).get('analysislink')} "
          f"r{c.get('row')}c{c.get('col')}s{c.get('size')} desc={c.get('desc')!r}")
    if c.get('row') == 9999:
        print(f'  placement outstanding — the owner places it in the designer; intended (row, col, size) '
              f'{SIGNING_LINK_PLACE}: its own row under {SIGNATURE_FIELD}, {SIGNED_BY} and {SIGNED_ON}')
    return True


# ── 17b · Share for Signature: the button and its Get Link workflow ─────────
SIGN = 'Share for Signature'
SIGN_DESC = ('Create the link the customer opens to sign and accept this quotation online, and put it in Signing Link. '
             'The link works once, and not after the Expiration date.')
SIGN_STATES = ('Quotation', 'Quotation Sent')
L_BRANCH = 'Does the quotation expire?'
L_DATED_PATH, L_OPEN_PATH = 'Expiration is set', 'No expiration date'
L_DATED, L_OPEN = 'Signing link until the expiration date', 'Signing link with no end date'
L_SAVE_DATED, L_SAVE_OPEN = 'Save the link (until the expiration date)', 'Save the link (no end date)'
SIGN_STEPS = (L_BRANCH, L_DATED, L_SAVE_DATED, L_OPEN, L_SAVE_OPEN)
LINK_NODE, LINK_APP = 15, 13                    # flowNodeType 获取链接 · the appType the editor adds it with
FILL_IN = 2                                     # linkType: 1 share (view only) · 2 fill-in · 5 internal
SUBMIT_TEXT = 'Accept & Sign'                   # Odoo's portal button (sale_portal_templates.xml:385)
NO_REVISIT = 0                                  # submitType: 0 neither view nor modify once submitted
AT_A_DATE = 2                                   # time.type: 1 a duration · 2 a date
LAST_MINUTE = '23:59'                           # dayTime on a Date: the link lasts the whole Expiration day
VIEW, EDIT, REQUIRED, HIDDEN = 1, 2, 3, 4       # a formProperties entry's `property`
DATE = 15
NOT_EMPTY_WF = '7'                              # a workflow condition's 不为空 (a Date's; a Signature's is 31)
# The button's own filter (pd-openweb WorkSheetFilter/enum.js): FILTER_CONDITION_TYPE.DATE_GTE 晚于等于, and
# DATE_OPTIONS' 今天 as its `dateRange`. The filter editor writes a Date's *on or after today* as exactly this pair;
# the number comparison GTE 14, which hap-cli's `ge` lowers to, is not the date one.
DATE_GTE, TODAY_RANGE = 34, 1
SPLICE_AND, SPLICE_OR = 1, 2                    # FILTER_RELATION_TYPE
# What the customer sees on the link, read-only — Odoo's portal page shows the same: the header, the customer and
# its two addresses, the dates, the payment terms, the lines, the totals and the terms (sale_portal_templates.xml).
# The *Order Lines* here is the subtable; its tab (TERMS_TAB) is shown with it.
SIGN_VIEW = ('Number', 'Status', 'Customer', 'Invoice Address', 'Delivery Address', 'Expiration',
             'Quotation/Order Date', 'Delivery Date', 'Payment Terms', ORDER_LINES, 'Untaxed Amount', 'Tax', 'Total',
             TERMS)
SIGN_EDIT = (SIGNATURE_FIELD, SIGNED_BY)        # the two the customer fills in, both required
# Everything else — Signing Link, Locked, Is Template, Discount Type and Value, Invoicing Closed, Signed On, the
# Other Info tab and all it holds — is hidden, and a control added later is hidden too (`addNotAllowView`).


def not_expired(f):
    """*Expiration is empty, or on or after today* — the two wire conditions, OR-ed. Odoo's `is_expired` is
    `validity_date < today`, so a quotation can still be signed on its Expiration day; the link it creates lasts until
    23:59 that day (`LAST_MINUTE`)."""
    c = f['Expiration']
    base = {'controlId': c['controlId'], 'dataType': c['type'], 'spliceType': SPLICE_OR, 'dateRange': 0,
            'isDynamicsource': False, 'dynamicSource': []}
    return [dict(base, filterType=C.EMPTY),
            dict(base, filterType=DATE_GTE, dateRange=TODAY_RANGE, values=[])]


def sign_filters(f):
    """The button's wire `filters`: two groups AND-ed — (Status is Quotation or Quotation Sent **and** Online
    Signature is ticked **and** Signature is empty) **and** (Expiration is empty **or** on or after today). That is
    `_has_to_be_signed` whole.

    Groups, because a button's condition mixes AND and OR only that way: the filter editor (pd-openweb
    `FilterConfig` with `supportGroup`, which the button's `ShowBtnFilterDialog` passes) reads a list whose first
    entry `isGroup` as groups throughout, one relation between them and one inside each (`model.formatForSave`).
    The first group is hap-cli's own lowering of the three conditions, unchanged; the second is `not_expired`, built
    by hand because the translator has no date comparison and no `dateRange`."""
    from hap_cli.core import filter_translator as flt
    wire = flt.translate_filter_group({'type': 'group', 'logic': 'AND', 'children': [{
        'type': 'group', 'logic': 'AND', 'children': [
            status_is(f, list(SIGN_STATES)),
            switch_when(f, 'Online Signature', True),
            {'field': f[SIGNATURE_FIELD]['controlId'], 'dataType': SIGN_PAD, 'operator': 'isempty'}]}]})
    return wire + [dict(wire[0], groupFilters=not_expired(f))]


def sign_spec(f):
    """Offered while Status is Quotation or Quotation Sent, Online Signature is ticked, Signature is empty and the
    quotation has not expired — `_has_to_be_signed`, expiry included (`sign_filters`)."""
    return {'name': SIGN, 'type': 'triggerWorkflow', 'desc': SIGN_DESC, 'isBatch': False,
            'enableWhen': sign_filters(f)}


def btn_conditions(filters):
    """A button's stored condition in comparable form: (control, relation, filterType, dateRange, sorted values) per
    condition, and ('group', relation, its conditions) per group — a group's own `controlId` is empty, so reading only
    the top level would call any two groups equal."""
    out = []
    for c in filters or []:
        if c.get('isGroup'):
            out.append(('group', c.get('spliceType'), btn_conditions(c.get('groupFilters'))))
        else:
            out.append((c.get('controlId'), c.get('spliceType'), c.get('filterType'), c.get('dateRange') or 0,
                        sorted(c.get('values') or [])))
    return out


def sign_button_problems(f, b):
    from hap_cli.core.action_spec_adapter import build_button_payload
    want = build_button_payload(sign_spec(f))
    problems = []
    if btn_conditions(b.get('filters')) != btn_conditions(want['filters']):
        problems.append(f'{SIGN}: offered when {btn_conditions(b.get("filters"))}, wanted '
                        f'{btn_conditions(want["filters"])}')
    if bool(b.get('isBatch')) or b.get('workflowType') != 1 or (b.get('desc') or '') != SIGN_DESC:
        problems.append(f"{SIGN}: isBatch={b.get('isBatch')} workflowType={b.get('workflowType')} "
                        f"desc={b.get('desc')!r}")
    return problems


def ensure_sign_when(f):
    """The live button's condition brought to `sign_filters`, **and nothing else about it changed**: a
    `SaveWorksheetBtn` sending back exactly what the button editor sends, as read, with only `filters` replaced —
    `ensure_send_batch`'s pattern. Every other key is compared before and after. Returns True when it wrote."""
    from hap_cli.core.session import Session
    live = [b for b in hap.listing('worksheet', 'custom-actions', ws()) if b['name'] == SIGN]
    if len(live) != 1:
        sys.exit(f'{len(live)} buttons are called {SIGN!r} — read the worksheet before writing')
    b, want = live[0], sign_filters(f)
    if btn_conditions(b.get('filters')) == btn_conditions(want):
        return False
    if drifted(f'{SIGN}: offered when {btn_conditions(b.get("filters"))}, wanted {btn_conditions(want)}'):
        return True
    print('  backup:', hap.backup('orders_buttons_pre_sign_expiry', b))
    params = {'btnId': b['btnId'], 'name': b['name'], 'worksheetId': ws(), 'filters': want,
              'confirmMsg': b.get('confirmMsg') or '', 'sureName': b.get('sureName') or '',
              'cancelName': b.get('cancelName') or '', 'workflowId': b.get('workflowId') or '',
              'desc': b.get('desc') or '', 'appId': APP, 'addRelationControlId': b.get('addRelationControl') or '',
              **{k: b.get(k) for k in BTN_SAVE_KEYS}}
    got = Session.load(None).api_call('Worksheet', 'SaveWorksheetBtn', params)
    after = next((x for x in hap.listing('worksheet', 'custom-actions', ws()) if x['btnId'] == b['btnId']), {})
    moved = sorted(k for k in set(b) | set(after)
                   if k not in ('filters', 'updateTime', 'updateAccountId') and b.get(k) != after.get(k))
    if btn_conditions(after.get('filters')) != btn_conditions(want) or moved:
        sys.exit(f'{SIGN}: SaveWorksheetBtn answered {got!r}; the condition reads back '
                 f'{btn_conditions(after.get("filters"))}, wanted {btn_conditions(want)}, and {moved} changed with it '
                 f'— the button as it was is in backups/orders_buttons_pre_sign_expiry_*.json')
    print(f'  {SIGN}: condition now {btn_conditions(after.get("filters"))}; every other key read back unchanged')
    return True


def ensure_sign_button(f):
    """The button, created once by name (`create-custom-action` ignores `--btn-id`). Returns its workflow id."""
    live = {b['name']: b for b in hap.listing('worksheet', 'custom-actions', ws())}
    key = KEY + SIGN
    if SIGN in live:
        pid = hap.ids().get('workflows', {}).get(key)
        if not pid:
            sys.exit(f'{SIGN} exists ({live[SIGN]["btnId"]}) but ids.json has no workflow for it')
        C.remember('buttons', key, live[SIGN]['btnId'])
        return pid
    if drifted(f'the {SIGN!r} button is missing'):
        return None
    hap.backup('orders_buttons_pre_share_for_signature', list(live.values()))
    out = hap.run('worksheet', 'create-custom-action', ws(), '-a', APP, '--action-spec',
                  json.dumps(sign_spec(f), ensure_ascii=False))
    data = out.get('data', out) if isinstance(out, dict) else {}
    pid = data.get('processId')
    if not pid:
        sys.exit(f'{SIGN}: no processId in create-custom-action output: {out}')
    C.remember('workflows', key, pid)
    btn = next((b for b in hap.listing('worksheet', 'custom-actions', ws()) if b['name'] == SIGN), None)
    if not btn:
        sys.exit(f'{SIGN}: created, but it does not come back from custom-actions')
    C.remember('buttons', key, btn['btnId'])
    print(f"  {SIGN}: created, btnId {btn['btnId']}, workflow {pid}")
    return pid


def expires_conditions(trigger):
    """The *Expiration is set* path: Expiration is not empty. The other path has no condition — the else."""
    return [[cond(trigger, 0, 8, '', CONTROLS['Expiration'], 'Expiration', DATE, NOT_EMPTY_WF)]]


def sign_graph(pid):
    """{name: node id} for the workflow's steps, the gateway's two paths by position (the order `batch-add` gave
    them: dated first), and the trigger."""
    proc = hap.run('workflow', 'node', 'list', pid)
    fm = proc['flowNodeMap']
    g = {'fm': fm, 'trigger': proc['startEventId']}
    gw = fm.get(fm[g['trigger']].get('nextId')) or {}
    if gw.get('typeId') != GATEWAY or gw.get('name') != L_BRANCH:
        return g
    g['gateway'] = gw['id']
    paths = [p for p in gw.get('flowIds') or [] if p in fm]
    g['paths'] = dict(zip((L_DATED_PATH, L_OPEN_PATH), paths))
    g['extra_paths'] = paths[2:]
    return g


def add_sign_branch(pid, trigger):
    """The gateway and its two empty paths, in one `batch-add` right after the trigger."""
    if drifted(f'{L_BRANCH!r} is missing after the trigger'):
        return
    nodes = [{'nodeAlias': 'expires', 'nodeType': 'branch', 'name': L_BRANCH, 'config': {'paths': [
        {'alias': 'dated', 'name': L_DATED_PATH, 'condition': {'logic': 'and', 'items': [
            {'left': {'node': {'nodeAlias': 'trigger'}, 'fieldId': CONTROLS['Expiration'], '_filedTypeId': DATE,
                      '_filedValue': 'Expiration'}, 'op': 'not_empty'}]}},
        {'alias': 'open', 'name': L_OPEN_PATH}]}}]
    hap.run('workflow', 'node', 'batch-add', pid, '--nodes', json.dumps(nodes, ensure_ascii=False),
            '--trigger-node-id', trigger, '--trigger-alias', 'trigger')
    print(f'  {L_BRANCH!r}: added with its two paths')


# The subtable's columns the customer sees on the link, read-only: Odoo's portal lines show the product, description,
# quantity and unit, unit price, discount, taxes and amounts. Sequence, Display Type, the delivered and invoiced
# quantities and the hidden helpers are not shown.
LINK_COLUMNS = ('Product', 'Description', 'Quantity', 'Unit', 'Unit Price', 'Discount', 'Taxes', 'Tax Amount',
                'Subtotal', 'Total')
SUBTABLE_LOCKED = {'workflow': True, 'allowAdd': '0', 'allowEdit': '0', 'allowCancel': '0', 'allowExport': '0'}


def link_detail(pid, node_id, trigger):
    """The Get Link node as the editor reads it once the record is picked: `getNodeDetail` with `selectNodeId` set is
    what fills `formProperties` with the worksheet's controls (Link/index.jsx `getNodeDetail(props, sId)`)."""
    from hap_cli.core import flow_node
    from hap_cli.core.session import Session
    d = flow_node.get_node_detail(Session.load(None), pid, node_id, LINK_NODE, select_node_id=trigger)
    return d.get('data', d) if isinstance(d, dict) else {}


def wanted_property(item, f):
    """1 view · 3 edit and required · 4 hidden, for one top-level control of the link's form."""
    if item.get('id') in {f[n]['controlId'] for n in SIGN_EDIT}:
        return REQUIRED
    if item.get('id') in {f[n]['controlId'] for n in SIGN_VIEW} | {TERMS_TAB}:
        return VIEW
    return HIDDEN


def link_properties(items, f):
    """The whole `formProperties` list with each entry's `property` set, and the Order Lines subtable's own column
    permissions switched on (`workflow`) with no add, edit, delete or export and only LINK_COLUMNS shown."""
    columns = {CHILD[n] for n in LINK_COLUMNS}
    out = []
    for item in items:
        item = dict(item, property=wanted_property(item, f))
        if item.get('id') == f[ORDER_LINES]['controlId']:
            item.update(SUBTABLE_LOCKED)
            item['subFormProperties'] = [dict(s, property=VIEW if s.get('id') in columns else HIDDEN)
                                         for s in item.get('subFormProperties') or []]
        out.append(item)
    return out


def properties_state(items):
    """{control id: property}, and for the subtable its switches and {column id: property}."""
    out = {}
    for item in items or []:
        out[item.get('id')] = item.get('property')
        if item.get('detailTable'):
            out[item.get('id') + ':columns'] = (
                tuple(str(item.get(k)) for k in SUBTABLE_LOCKED),
                tuple(sorted((s.get('id'), s.get('property')) for s in item.get('subFormProperties') or [])))
    return out


def link_time(trigger, dated):
    """`time` for the dated link: at a date (type 2) taken from the trigger order's Expiration, at 23:59 — a Date
    field's `dayTime`, which the editor defaults to 08:00 (Deadline/index.jsx). Odoo's `is_expired` is
    `validity_date < today`, so the Expiration day itself is still signable. None for the open link."""
    if not dated:
        return {'enable': False, 'actions': []}
    return {'enable': True, 'type': AT_A_DATE, 'actions': [], 'dayTime': LAST_MINUTE, 'executeTime': {
        'fieldActionId': '', 'fieldAppType': 8, 'fieldNodeType': 0, 'fieldNodeId': trigger,
        'fieldNodeName': 'Trigger by button', 'fieldControlId': CONTROLS['Expiration'],
        'fieldControlName': 'Expiration', 'fieldControlType': DATE, 'fieldValue': '', 'sourceType': 0}}


def time_state(t):
    t = t or {}
    e = t.get('executeTime') or {}
    if not t.get('enable'):
        return (False,)
    return (True, t.get('type'), e.get('fieldNodeId'), e.get('fieldControlId'), t.get('dayTime'))


def link_state(d):
    return {'record': d.get('selectNodeId'), 'linkType': d.get('linkType'), 'submit': d.get('submitButtonName'),
            'submitType': d.get('submitType'), 'password': d.get('password') or '',
            'addNotAllowView': bool(d.get('addNotAllowView')), 'time': time_state(d.get('time')),
            'properties': properties_state(d.get('formProperties'))}


def link_wanted(d, f, trigger, dated):
    return {'record': trigger, 'linkType': FILL_IN, 'submit': SUBMIT_TEXT, 'submitType': NO_REVISIT, 'password': '',
            'addNotAllowView': True, 'time': time_state(link_time(trigger, dated)),
            'properties': properties_state(link_properties(d.get('formProperties') or [], f))}


def sync_link(pid, node_id, name, trigger, f, dated):
    """One Get Link step: this order, fill-in, Signature and Signed By editable and required, SIGN_VIEW read-only,
    everything else hidden, "Accept & Sign", no view or change once submitted, and — on the dated path — the end of
    the Expiration day. Compared first; saved as the editor saves it; read back."""
    from hap_cli.core import flow_node
    from hap_cli.core.session import Session
    d = link_detail(pid, node_id, trigger)
    want = link_wanted(d, f, trigger, dated)
    if link_state(d) == want:
        return False
    if drifted(f'{name}: {link_state(d)}, wanted {want}'):
        return True
    missing = [n for n in SIGN_VIEW + SIGN_EDIT if f[n]['controlId'] not in {x.get('id') for x in d['formProperties']}]
    if missing:
        sys.exit(f'{name}: the node offers no {missing} — read it before writing')
    flow_node.save_node(Session.load(None), pid, node_id, LINK_NODE, {
        'actionId': d.get('actionId') or '', 'selectNodeId': trigger, 'linkType': FILL_IN,
        'linkName': d.get('linkName') or '', 'formProperties': link_properties(d['formProperties'], f),
        'time': link_time(trigger, dated), 'password': '', 'submitButtonName': SUBMIT_TEXT,
        'submitType': NO_REVISIT, 'modifyTime': -1, 'addNotAllowView': True, 'viewId': ''}, name=name)
    back = link_detail(pid, node_id, trigger)
    if link_state(back) != want:
        got = link_state(back)
        sys.exit(f'{name}: reads back differently — ' + '; '.join(
            f'{k}: {got[k]} (wanted {want[k]})' for k in want if got[k] != want[k]))
    return True


LINK_OUT = 'link'                               # the Get Link step's one output: the URL, a Text


def sign_share_steps(pid, g):
    """{step name: id} along each path, adding what is missing in place (`add_step`). None when `check` found a
    step missing."""
    steps = {}
    for name, prev, type_id, action, app_type, app_id in (
            (L_DATED, g['paths'][L_DATED_PATH], LINK_NODE, '', LINK_APP, ''),
            (L_SAVE_DATED, L_DATED, UPDATE_NODE, '2', 1, ws()),
            (L_OPEN, g['paths'][L_OPEN_PATH], LINK_NODE, '', LINK_APP, ''),
            (L_SAVE_OPEN, L_OPEN, UPDATE_NODE, '2', 1, ws())):
        steps[name], _ = add_step(pid, steps.get(prev, prev), name, type_id, action=action, app_type=app_type,
                                  app_id=app_id)
        if steps[name] is None:
            return None
    return steps


def save_link_writes(f, link_id):
    """Signing Link ← the Get Link step's URL, a text template `$<link step>-link$`."""
    return [patch(f[SIGNING_LINK]['controlId'], TEXT, node=link_id, source=LINK_OUT)]


def sync_sign_share(f, pid):
    """Bring Share for Signature's workflow to §17's shape; True when something was written. Under DRIFT (`check`)
    it writes nothing and records each difference."""
    changed = False
    g = sign_graph(pid)
    if 'gateway' not in g:
        if drifted(f'{L_BRANCH!r} is missing after the trigger'):
            return True
        fm = g['fm']
        if fm[g['trigger']].get('nextId') not in (None, '', '99'):
            sys.exit(f"{SIGN}: the trigger runs into {fm.get(fm[g['trigger']]['nextId'], {}).get('name')!r}, not "
                     f'{L_BRANCH!r} — read workflow {pid} before writing')
        add_sign_branch(pid, g['trigger'])
        changed = True
        g = sign_graph(pid)
    if len(g.get('paths') or {}) != 2 or g['extra_paths']:
        sys.exit(f'{L_BRANCH}: paths {g.get("paths")} + {g.get("extra_paths")} — this builder knows two')
    for name, groups in ((L_DATED_PATH, expires_conditions(g['trigger'])), (L_OPEN_PATH, [])):
        changed |= sync_path(pid, g['paths'][name], name, groups)
    steps = sign_share_steps(pid, g)
    if steps is None:
        return True
    for link, save, dated in ((L_DATED, L_SAVE_DATED, True), (L_OPEN, L_SAVE_OPEN, False)):
        changed |= sync_link(pid, steps[link], link, g['trigger'], f, dated)
        wanted = save_link_writes(f, steps[link])
        live = writes_live(pid, steps[save])
        node = read_node(pid, steps[save])
        if live != [write_state(x) for x in wanted] or node.get('selectNodeId') != g['trigger'] or \
                node.get('isException'):
            if drifted(f'{save}: writes {live} on {node.get("selectNodeId")}'):
                continue
            set_writes(pid, {'id': steps[save], 'name': save}, wanted, g['trigger'])
            changed = True
            if writes_live(pid, steps[save]) != [write_state(x) for x in wanted]:
                sys.exit(f'{save}: reads back {writes_live(pid, steps[save])} — `hap workflow rollback {pid} -y` '
                         f'restores the published version')
    return changed


def sign_share_structure(pid):
    """Every path's chain exactly, nothing after the gateway, no step this builder does not know."""
    g = sign_graph(pid)
    if 'gateway' not in g:
        return [f'{SIGN}: {L_BRANCH!r} is not the step after the trigger — run `sign`'], g
    fm, problems = g['fm'], []
    names = lambda start: [fm[n].get('name') for n in chain(fm, start)]
    for path, want in ((L_DATED_PATH, [L_DATED, L_SAVE_DATED]), (L_OPEN_PATH, [L_OPEN, L_SAVE_OPEN])):
        pid_ = (g.get('paths') or {}).get(path)
        got = names(pid_) if pid_ else None
        if got != want or (pid_ and fm[pid_].get('name') != path):
            problems.append(f'{SIGN}: path {fm.get(pid_, {}).get("name")!r} runs {got}, wanted {path!r}: {want}')
    if fm[g['gateway']].get('nextId') not in (None, '', '99'):
        problems.append(f'{SIGN}: {L_BRANCH!r} runs into {fm[fm[g["gateway"]]["nextId"]].get("name")!r}')
    extra = sorted(n.get('name') for n in fm.values() if n.get('typeId') not in (None, 0, 100, BRANCH_PATH)
                   and n.get('prveId') and n.get('name') not in SIGN_STEPS)
    if extra:
        problems.append(f'{SIGN}: steps this builder does not know: {extra}')
    return problems, g


def workflow_published(pid, label):
    got = hap.run('workflow', 'get', pid)
    got = got.get('data', got) if isinstance(got, dict) else {}
    if not got.get('enabled') or got.get('publishStatus') != 2:
        return [f'{label} {pid}: enabled={got.get("enabled")} publishStatus={got.get("publishStatus")} — '
                'unpublished changes; run `sign`']
    return []


def sign_offered():
    """{order number: (offered?, Status, Online Signature ticked?, signed?, Expiration)}, the button as the server
    evaluates it on each order (`buttons_offered`), and the four cells its condition reads through **both** read
    paths."""
    f = C.fields(ws())
    out = {}
    for r in C.records(ws(), APP):
        d = read_record(ws(), r['rowid'])
        ticked = '1' in (READERS[CHECKBOX](r.get(f['Online Signature']['controlId'])),
                         read_cell(f['Online Signature'], d))
        signed = bool(r.get(f[SIGNATURE_FIELD]['controlId']) or read_cell(f[SIGNATURE_FIELD], d))
        expires = (r.get(f['Expiration']['controlId']) or read_cell(f['Expiration'], d) or '')[:10]
        out[r.get(f['Number']['controlId'])] = (buttons_offered(r['rowid']).get(SIGN),
                                                status_label(json_keys(r.get(f['Status']['controlId']))),
                                                ticked, signed, expires)
    return out


def sign_expected(v, today):
    """Whether the button should be offered on an order read by `sign_offered`: `_has_to_be_signed`. `today` is this
    machine's date; the server's "today" is the app's — the same while both run in +08:00."""
    _offered, status, ticked, signed, expires = v
    return status in SIGN_STATES and ticked and not signed and (not expires or expires >= today)


def sign_share_problems(f):
    """The button, its workflow read back without writing, published, and offered exactly where it should be."""
    global DRIFT
    live = {b['name']: b for b in hap.listing('worksheet', 'custom-actions', ws())}
    b = live.get(SIGN)
    if b is None:
        return [f'the {SIGN!r} button is missing — run `sign`']
    problems = sign_button_problems(f, b)
    pid = hap.ids().get('workflows', {}).get(KEY + SIGN)
    if not pid:
        return problems + [f'{SIGN}: no workflow id in ids.json — run `sign`']
    found, g = sign_share_structure(pid)
    problems += found
    if found:
        return problems
    DRIFT = []
    try:
        sync_sign_share(f, pid)
        problems += [f'{SIGN}: {d}' for d in DRIFT]
    finally:
        DRIFT = None
    problems += workflow_published(pid, SIGN)
    offered, today = sign_offered(), datetime.date.today().isoformat()
    wrong = {n: v for n, v in offered.items() if bool(v[0]) != sign_expected(v, today)}
    if wrong:
        problems.append(f'{SIGN}: offered wrongly on {wrong} — (offered, Status, Online Signature, signed, '
                        f'Expiration), today {today}')
    if not problems:
        print(f"  OK  {SIGN:<19} btnId={b['btnId']} isBatch=False when Status is Quotation or Quotation Sent, "
              f'Online Signature is ticked, Signature is empty and Expiration is empty or {today} or later '
              f"(server: offered on {sorted(n for n, v in offered.items() if v[0])}; expired, so not: "
              f"{sorted(n for n, v in offered.items() if v[4] and v[4] < today and v[1] in SIGN_STATES)})\n"
              f'        then {L_BRANCH} [{L_DATED_PATH}: {L_DATED} (ends {LAST_MINUTE} on Expiration) → '
              f'{L_SAVE_DATED} | {L_OPEN_PATH}: {L_OPEN} → {L_SAVE_OPEN}] — fill-in, "{SUBMIT_TEXT}", '
              f'{", ".join(SIGN_EDIT)} required, single use; published')
    return problems


# ── 17c · Signed: confirm the order — the worksheet-event workflow ──────────
SIGNED_WF = 'Signed: confirm the order'
SIGNED_WF_DESC = ('When the customer signs a quotation through its signing link: record when, confirm it unless it asks '
                  'for online payment, and tell the salesperson.')
W_TRIGGER = 'The customer signed'
W_SIGNED_ON = 'Set Signed On'
W_PAY = 'Is online payment required?'
W_PAY_YES, W_PAY_NO = 'Online payment', 'No online payment'
# A 站内通知 reads 【<node name>】<content>, so these three names are headings the salesperson reads.
N_MISSING = 'Quotation signed, not confirmed'
N_PAYMENT = 'Quotation signed, payment due'
N_SIGNED = 'Quotation signed'
SIGNED_STEPS = (W_SIGNED_ON, COUNT_STEP, PRODUCT_BRANCH, N_MISSING, W_PAY, N_PAYMENT, STEP[CONFIRM], N_SIGNED)
MSG_SIGNED = '{number} was signed by {who}.'
MSG_PAYMENT = '{number} was signed by {who}. It stays a quotation because it asks for online payment.'
MSG_MISSING = ('{number} was signed by {who}, but it was not confirmed: some order lines are missing a product. '
               'Correct them, then confirm it.')
UPDATED = '4'                                   # a worksheet trigger's triggerId: 1 created · 2 either · 4 updated
SIG_NOT_EMPTY, TICKED = '31', '29'              # workflow conditionIds: a Signature's 不为空 · a checkbox's 选中
SALESPERSON_ID = '6ab0bff27d58b0f449316ae1'     # Orders › Salesperson, the owner's Member control


def salesperson(trigger):
    """The order's Salesperson (a Member control) as a notice's recipient — the shape `email_account` gives a
    field of a step, with a Member's control type."""
    return {'type': 6, 'entityId': trigger, 'entityName': W_TRIGGER, 'roleId': SALESPERSON_ID,
            'roleTypeId': 0, 'roleName': 'Salesperson', 'controlType': MEMBER, 'flowNodeType': 0, 'appType': 1,
            'avatar': '', 'count': 0, 'actionId': ''}


def signed_trigger_conditions(trigger, f):
    """Signature is not empty, Status is Quotation or Quotation Sent, Online Signature is ticked — one AND group."""
    status = cond(trigger, 0, 1, '', CONTROLS['Status'], 'Status', DROPDOWN, IS_ANY_OF, [
        {'value': {'key': STATUS_KEYS[x], 'value': x, 'isDeleted': False, 'score': None, 'index': None}}
        for x in SIGN_STATES])
    return [[cond(trigger, 0, 1, '', f[SIGNATURE_FIELD]['controlId'], SIGNATURE_FIELD, SIGN_PAD, SIG_NOT_EMPTY),
             status,
             cond(trigger, 0, 1, '', CONTROLS['Online Signature'], 'Online Signature', CHECKBOX, TICKED)]]


def signed_texts(trigger, f):
    number = f"${trigger}-{f['Number']['controlId']}$"
    who = f"${trigger}-{f[SIGNED_BY]['controlId']}$"
    return {N_MISSING: MSG_MISSING.format(number=number, who=who),
            N_PAYMENT: MSG_PAYMENT.format(number=number, who=who),
            N_SIGNED: MSG_SIGNED.format(number=number, who=who)}


def signed_nodes(f, trigger):
    """Every step for one `batch-add` on the new workflow. The field writes and messages here are only what
    `batch-add` needs to make each step; `sync_signed` rewrites every one in the shape the server stores."""
    t = {'nodeAlias': 'trigger'}
    now = lambda name: {'fieldId': f[name]['controlId'], 'type': DATE_TIME,
                        'valueRef': {'kind': 'system', 'field': 'nowTime'}}
    tell = lambda alias, name: {'nodeAlias': alias, 'nodeType': 'send_internal_notice', 'name': name,
                                'config': {'content': name, 'accounts': [salesperson(trigger)]}}
    return [
        {'nodeAlias': 'signed_on', 'nodeType': 'update_record', 'name': W_SIGNED_ON,
         'config': {'target': {'node': t}, 'fields': [now(SIGNED_ON)]}},
        guard_nodes()[0],
        {'nodeAlias': 'product_branch', 'nodeType': 'branch', 'name': PRODUCT_BRANCH, 'config': {'paths': [
            {'alias': 'missing', 'name': 'Yes', 'nodes': [tell('tell_missing', N_MISSING)]},
            {'alias': 'clean', 'name': 'No', 'nodes': [
                {'nodeAlias': 'pay_branch', 'nodeType': 'branch', 'name': W_PAY, 'config': {'paths': [
                    {'alias': 'pay', 'name': W_PAY_YES, 'nodes': [tell('tell_payment', N_PAYMENT)]},
                    {'alias': 'no_pay', 'name': W_PAY_NO, 'nodes': [
                        {'nodeAlias': 'confirm', 'nodeType': 'update_record', 'name': STEP[CONFIRM],
                         'config': {'target': {'node': t}, 'fields': [
                             {'fieldId': f['Status']['controlId'], 'type': DROPDOWN,
                              'value': STATUS_KEYS['Sales Order']}, now('Quotation/Order Date')]}},
                        tell('tell_signed', N_SIGNED)]}]}}]}]}},
    ]


def signed_workflow_id():
    pid = hap.ids().get('workflows', {}).get(KEY + SIGNED_WF)
    if pid:
        return pid
    return {w['name']: w.get('id') or w.get('processId') for w in hap.listing('workflow', 'list', APP)}.get(SIGNED_WF)


def trigger_state(pid, trigger):
    t = read_node(pid, trigger)
    return (t.get('appId'), str(t.get('triggerId')), sorted(t.get('assignFieldIds') or []),
            cond_state(t.get('operateCondition') or t.get('conditions')))


def sync_signed_trigger(pid, trigger, f):
    want = signed_trigger_conditions(trigger, f)
    target = (ws(), UPDATED, [f[SIGNATURE_FIELD]['controlId']], cond_state(want))
    changed = False
    if trigger_state(pid, trigger) != target:
        if drifted(f'{W_TRIGGER}: {trigger_state(pid, trigger)}, wanted {target}'):
            return True
        hap.run('workflow', 'node', 'save', pid, trigger, '--type', '0', '-n', W_TRIGGER, '-c', json.dumps(
            {'appId': ws(), 'appType': 1, 'triggerId': UPDATED, 'assignFieldIds': [f[SIGNATURE_FIELD]['controlId']],
             'operateCondition': want, 'returns': []}, ensure_ascii=False))
        if trigger_state(pid, trigger) != target:
            sys.exit(f'{W_TRIGGER}: reads back {trigger_state(pid, trigger)}, wanted {target} — '
                     f'`hap workflow rollback {pid} -y` restores the published version')
        changed = True
    changed |= sync_name(pid, trigger, W_TRIGGER)
    return changed


def signed_graph(pid):
    proc, byname = nodes_by_name(pid)
    return proc, byname, proc['startEventId']


def pay_paths(proc, gateway_id, yes_next):
    paths = [n for n in proc['flowNodeMap'].values() if n.get('typeId') == BRANCH_PATH and n.get('prveId') == gateway_id]
    yes = next((p for p in paths if p.get('nextId') == yes_next), None)
    if len(paths) != 2 or yes is None:
        sys.exit(f'{W_PAY}: paths {[(p.get("name"), p.get("nextId")) for p in paths]} — expected two, one running '
                 f'into {N_PAYMENT!r}')
    return yes, next(p for p in paths if p['id'] != yes['id'])


def sync_signed(f, pid):
    """Bring the workflow to §17c's shape; True when something was written. Under DRIFT (`check`) it records."""
    changed = False
    proc, byname, trigger = signed_graph(pid)
    if W_SIGNED_ON not in byname:
        if drifted(f'{SIGNED_WF}: its steps are missing'):
            return True
        if proc['flowNodeMap'][trigger].get('nextId') not in (None, '', '99'):
            sys.exit(f'{SIGNED_WF}: the trigger runs into a step this builder did not make — read {pid}')
        hap.run('workflow', 'node', 'batch-add', pid, '--nodes', json.dumps(signed_nodes(f, trigger), ensure_ascii=False),
                '--trigger-worksheet', ws(), '--trigger-event', 'update', '--trigger-fields',
                f[SIGNATURE_FIELD]['controlId'], '--trigger-alias', 'trigger')
        proc, byname, trigger = signed_graph(pid)
        missing = [n for n in SIGNED_STEPS if n not in byname]
        if missing:
            sys.exit(f'{SIGNED_WF}: {missing} are not in the workflow after batch-add: {sorted(byname)}')
        changed = True
        print(f'  {SIGNED_WF}: steps added')
    changed |= sync_signed_trigger(pid, trigger, f)
    wanted = writes_wanted(f)[CONFIRM]
    for name, writes in ((W_SIGNED_ON, [patch(f[SIGNED_ON]['controlId'], DATE_TIME, source='nowTime', system=True)]),
                         (STEP[CONFIRM], wanted)):
        node = read_node(pid, byname[name]['id'])
        if writes_live(pid, byname[name]['id']) != [write_state(x) for x in writes] or \
                node.get('selectNodeId') != trigger or node.get('isException'):
            if drifted(f'{name}: writes {writes_live(pid, byname[name]["id"])} on {node.get("selectNodeId")}'):
                continue
            set_writes(pid, byname[name], writes, trigger)
            changed = True
            if writes_live(pid, byname[name]['id']) != [write_state(x) for x in writes]:
                sys.exit(f'{name}: reads back {writes_live(pid, byname[name]["id"])}')
    count = read_node(pid, byname[COUNT_STEP]['id'])
    if count_problems(count, trigger):
        sys.exit(f'{COUNT_STEP}: {count_problems(count, trigger)} — batch-add wrote it this way; read {pid}')
    yes, no = branch_paths(proc, byname[PRODUCT_BRANCH]['id'], byname[N_MISSING]['id'])
    if DRIFT is None:
        changed |= save_path(pid, yes, 'Yes', at_least_one(byname[COUNT_STEP]['id']))
        changed |= save_path(pid, no, 'No', [])
    else:
        for path, name, groups in ((yes, 'Yes', at_least_one(byname[COUNT_STEP]['id'])), (no, 'No', [])):
            got = read_node(pid, path['id'])
            key = lambda c: (c.get('nodeId'), c.get('filedId'), str(c.get('conditionId')))
            if [[key(c) for c in g] for g in got.get('conditions') or []] != [[key(c) for c in g] for g in groups] \
                    or path.get('name') != name:
                drifted(f'{PRODUCT_BRANCH} path {path.get("name")!r}: {got.get("conditions")}')
    pay_yes, pay_no = pay_paths(proc, byname[W_PAY]['id'], byname[N_PAYMENT]['id'])
    changed |= sync_path(pid, pay_yes['id'], W_PAY_YES, [[cond(trigger, 0, 1, '', CONTROLS['Online Payment'],
                                                               'Online Payment', CHECKBOX, TICKED)]])
    changed |= sync_path(pid, pay_no['id'], W_PAY_NO, [])
    texts = signed_texts(trigger, f)
    for name in (N_MISSING, N_PAYMENT, N_SIGNED):
        changed |= sync_notice(pid, byname[name]['id'], name, texts[name], salesperson(trigger))
    info = hap.run('workflow', 'get', pid)
    info = info.get('data', info) if isinstance(info, dict) else {}
    if (info.get('name'), info.get('explain') or '') != (SIGNED_WF, SIGNED_WF_DESC):
        if not drifted(f'{SIGNED_WF}: name / description {info.get("name")!r} / {info.get("explain")!r}'):
            hap.run('workflow', 'update', pid, '-n', SIGNED_WF, '-d', SIGNED_WF_DESC)
        changed = True
    return changed


def count_problems(count, trigger):
    """Confirm's count, read off another workflow: Order Lines where Orders is this order, Display Type is Product and
    Product is empty (`guard_problems`' own comparison)."""
    conds = [c for flt in count.get('filters') or [] for group in flt.get('conditions') or [] for c in group]
    got = [(c['filedId'], c['conditionId'],
            [v.get('controlId') or (v.get('value') or {}).get('value') for v in c['conditionValues']]) for c in conds]
    want = [(LINES_ORDERS, RELATION_EQ, ['rowid']), (CHILD['Display Type'], IS_ANY_OF, ['Product']),
            (CHILD['Product'], EMPTY, [])]
    problems = []
    if (count.get('actionId'), count.get('appId'), count.get('reportControlId'), count.get('reportType')) != \
            (WORKSHEET_TOTAL, LINES_WS, '', 0):
        problems.append(f"actionId={count.get('actionId')} appId={count.get('appId')}")
    if got != want:
        problems.append(f'filter {got}, wanted {want}')
    elif [v.get('nodeId') for c in conds for v in c['conditionValues']][:1] != [trigger]:
        problems.append('the Orders relation is not compared with the triggering order')
    return problems


def signed_structure(pid):
    proc, byname, trigger = signed_graph(pid)
    fm, problems = proc['flowNodeMap'], []
    missing = [n for n in SIGNED_STEPS if n not in byname]
    if missing:
        return [f'{SIGNED_WF}: {missing} missing — run `sign`']
    names = lambda start: [fm[n].get('name') for n in chain(fm, start)]
    yes, no = branch_paths(proc, byname[PRODUCT_BRANCH]['id'], byname[N_MISSING]['id'])
    pay_yes, pay_no = pay_paths(proc, byname[W_PAY]['id'], byname[N_PAYMENT]['id'])
    for label, start, want in (('the trigger', trigger, [W_SIGNED_ON, COUNT_STEP, PRODUCT_BRANCH]),
                               ('Yes', yes['id'], [N_MISSING]), ('No', no['id'], [W_PAY]),
                               (W_PAY_YES, pay_yes['id'], [N_PAYMENT]),
                               (W_PAY_NO, pay_no['id'], [STEP[CONFIRM], N_SIGNED])):
        if names(start) != want:
            problems.append(f'{SIGNED_WF}: {label} runs {names(start)}, wanted {want}')
    for name in (PRODUCT_BRANCH, W_PAY):
        if fm[byname[name]['id']].get('nextId') not in (None, '', '99'):
            problems.append(f'{SIGNED_WF}: {name!r} runs into {fm[fm[byname[name]["id"]]["nextId"]].get("name")!r}')
    aborts = [n.get('name') for n in fm.values() if n.get('typeId') == ABORT]
    extra = sorted(n.get('name') for n in fm.values() if n.get('typeId') not in (None, 0, 100, BRANCH_PATH)
                   and n.get('prveId') and n.get('name') not in SIGNED_STEPS)
    if aborts or extra:
        problems.append(f'{SIGNED_WF}: abort nodes {aborts}, unknown steps {extra}')
    return problems


def signed_problems(f):
    global DRIFT
    pid = signed_workflow_id()
    if not pid:
        return [f'{SIGNED_WF}: not built — run `sign`']
    problems = signed_structure(pid)
    if problems:
        return problems
    DRIFT = []
    try:
        sync_signed(f, pid)
        problems += [f'{SIGNED_WF}: {d}' for d in DRIFT]
    finally:
        DRIFT = None
    problems += workflow_published(pid, SIGNED_WF)
    if not problems:
        print(f'  OK  {SIGNED_WF!r} {pid}: when an order is updated with {SIGNATURE_FIELD} written, and only while '
              f'it is filled, Status is Quotation or Quotation Sent and Online Signature is ticked\n'
              f'        → {W_SIGNED_ON} = now → {COUNT_STEP} → {PRODUCT_BRANCH} [Yes: 【{N_MISSING}】 | No: {W_PAY} '
              f'[{W_PAY_YES}: 【{N_PAYMENT}】 | {W_PAY_NO}: {STEP[CONFIRM]} (Status, Quotation/Order Date = now) → '
              f'【{N_SIGNED}】]] — to the Salesperson; published')
    return problems


def ensure_signed_workflow(f):
    pid = signed_workflow_id()
    if not pid:
        if drifted(f'{SIGNED_WF} does not exist'):
            return None, True
        out = hap.run('workflow', 'create', '-c', hap.ids()['org'], '-a', APP, '-n', SIGNED_WF, '--type', 'worksheet',
                      '-d', SIGNED_WF_DESC)
        data = out.get('data', out) if isinstance(out, dict) else out
        pid = data if isinstance(data, str) else (data.get('processId') or data.get('id'))
        if not pid:
            sys.exit(f'{SIGNED_WF}: no process id in `workflow create` output: {out}')
        print(f'  created {SIGNED_WF!r}: {pid}')
    C.remember('workflows', KEY + SIGNED_WF, pid)
    proc = hap.run('workflow', 'node', 'list', pid)
    hap.backup('orders_signed_workflow_pre_sign', proc)
    return pid, sync_signed(f, pid)


def sign_untouched():
    """What `sign` must not move: every other button, and the whole control set."""
    others = sorted((b for b in hap.listing('worksheet', 'custom-actions', ws()) if b['name'] != SIGN),
                    key=lambda b: b['btnId'])
    return {'the other buttons': json.dumps(others, ensure_ascii=False, sort_keys=True, default=str),
            'the control set': json.dumps(signature(hap.controls(ws())), ensure_ascii=False, sort_keys=True,
                                          default=str)}


def step_sign():
    """§17: Share for Signature and its Get Link workflow, and *Signed: confirm the order*. Publishes each workflow
    only when something changed or it has unpublished changes; presses nothing and sends nothing. Re-runnable."""
    f = guard()
    for name in PART1[1:] + (SIGNING_LINK, 'Online Signature', 'Online Payment', 'Expiration', 'Number'):
        if name not in f:
            sys.exit(f'{name} is not on {WORKSHEET} — run `part1` / `signlink` first')
    before = sign_untouched()
    pid = ensure_sign_button(f)
    C.remember('workflows', KEY + SIGN, pid)
    if not ensure_sign_when(f):
        print(f'  {SIGN}: condition already as built; not saved')
    print('  backup:', hap.backup('orders_sign_share_pre_sign', hap.run('workflow', 'node', 'list', pid)))
    wrote = sync_sign_share(f, pid)
    problems, _ = sign_share_structure(pid)
    if problems:
        sys.exit('  not published:\n  ' + '\n  '.join(problems))
    if wrote or workflow_published(pid, SIGN):
        res = C.publish(pid)
        print(f'  {SIGN}: {res}')
        if not res.get('isPublish') or res.get('processWarnings') or res.get('errorNodeIds'):
            sys.exit(f'{SIGN}: publish answered {res} — the draft stays unpublished')
    else:
        print(f'  {SIGN}: already built; not re-published')
    spid, swrote = ensure_signed_workflow(f)
    problems = signed_structure(spid)
    if problems:
        sys.exit('  not published:\n  ' + '\n  '.join(problems))
    if swrote or workflow_published(spid, SIGNED_WF):
        res = C.publish(spid)
        print(f'  {SIGNED_WF}: {res}')
        if not res.get('isPublish') or res.get('processWarnings') or res.get('errorNodeIds'):
            sys.exit(f'{SIGNED_WF}: publish answered {res}')
    else:
        print(f'  {SIGNED_WF}: already built; not re-published')
    after = sign_untouched()
    moved = sorted(k for k in before if before[k] != after[k])
    if moved:
        sys.exit(f'{WORKSHEET}: {moved} changed while §17 was built — `sign` writes none of them')
    print(f'  untouched, byte for byte: {sorted(before)}')
    problems = sign_share_problems(f) + signed_problems(f)
    if problems:
        sys.exit('  ' + '\n  '.join(problems))
    print(C.structure(pid))
    print(C.structure(spid))
    return True


# ── 17d · the two TEST quotations for the browser test ─────────────────────
#
# `signtest` makes (once) TEST quotations for TEST Person One — one product line, Online Signature ticked — and
# presses Share for Signature on each through the button API (`process/startProcess`, what the record page's button
# sends), which spends no credits and sends nothing. It then reads Signing Link back through both read paths and
# prints it. The first two are the brief's: Expiration a week out, without and with Online Payment. The other three
# are for the expiry: Expiration today (the link must work until 23:59 tonight), yesterday (born expired), and none
# (the no-end path). An order is found again by its Customer Reference; one whose link is already there is not
# pressed again, so a re-run writes nothing.
SIGN_TESTS = {                                   # Customer Reference: (Online Payment, Expiration in days from today)
    'TEST Sign & Accept': ('0', 7),
    'TEST Sign & Accept, online payment': ('1', 7),
    'TEST Sign & Accept, expires today': ('0', 0),
    'TEST Sign & Accept, expired yesterday': ('0', -1),
    'TEST Sign & Accept, no expiration': ('0', None),
}
TEST_CUSTOMER = 'TEST QA Trading Sdn Bhd, TEST Person One'
TEST_SALESPERSON = 'Casimir'                    # resolved through the directory, as the seed does
TEST_DAYS = 7


def sign_test_orders(f):
    """{Customer Reference: rowid} for the TEST orders that exist, through both read paths."""
    ref = f['Customer Reference']
    out = {}
    for r in C.records(ws(), APP):
        value = r.get(ref['controlId']) or read_cell(ref, read_record(ws(), r['rowid']))
        if value in SIGN_TESTS:
            if value in out:
                sys.exit(f'two orders carry the Customer Reference {value!r} — read them before writing')
            out[value] = r['rowid']
    return out


def template_line():
    """The Order Line a TEST line copies: the first product line of the seeded orders that has a Product, a Unit and
    Taxes, by order Number and Sequence — a real product, priced and taxed as the seed has it."""
    f_lines = hap.by_name(c for c in hap.controls(LINES_WS) if c['type'] != C.TAB)
    numbers = {rowid: number for number, rowid in by_number().items()}
    found = []
    for r in C.records(LINES_WS, APP):
        d = read_record(LINES_WS, r['rowid'])
        cell = lambda n: read_cell(f_lines[n], d)
        order = (cell('Orders') or [None])[0]
        if cell('Display Type') == [PRODUCT_LINE] and cell('Product') and cell('Unit') and cell('Taxes') and \
                numbers.get(order, '').startswith('S000') and cell('Product') != [discount_variant()]:
            found.append((numbers[order], cell('Sequence') or 0, r['rowid'], {n: cell(n) for n in (
                'Product', 'Description', 'Unit', 'Unit Price', 'Taxes')}))
    if not found:
        sys.exit('no seeded product line with a Product, a Unit and Taxes to copy')
    return sorted(found, key=lambda x: (x[0], x[1]))[0]


def create_sign_test(f, ref, online_payment, line, days=TEST_DAYS):
    index = titles(*CONTACTS).get(TEST_CUSTOMER) or []
    if len(index) != 1:
        sys.exit(f'{TEST_CUSTOMER!r} matches {len(index)} contacts — nothing created')
    people = members({TEST_SALESPERSON})
    if TEST_SALESPERSON not in people:
        sys.exit(f'{TEST_SALESPERSON!r} does not resolve to one member — nothing created')
    today = time.strftime('%Y-%m-%d')
    expires = '' if days is None else time.strftime('%Y-%m-%d', time.localtime(time.time() + days * 86400))
    cid = lambda n: f[n]['controlId']
    values = [{'id': cid('Status'), 'value': [STATUS_KEYS['Quotation']]},
              {'id': cid(CUSTOMER), 'value': index},
              {'id': cid('Invoice Address'), 'value': index},
              {'id': cid('Delivery Address'), 'value': index},
              {'id': cid('Quotation/Order Date'), 'value': time.strftime('%Y-%m-%d %H:%M:%S')},
              {'id': cid('Expiration'), 'value': expires},
              {'id': cid('Tax Mode'), 'value': [option_key(f['Tax Mode'], 'Tax Excluded')]},
              {'id': cid('Invoice Status'), 'value': [option_key(f['Invoice Status'], 'Nothing to Invoice')]},
              {'id': cid('Online Signature'), 'value': '1'},
              {'id': cid('Online Payment'), 'value': online_payment},
              {'id': cid('Prepayment Percentage'), 'value': '100'},
              {'id': cid('Locked'), 'value': '0'},
              {'id': cid(IS_TEMPLATE), 'value': '0'},
              {'id': cid('Salesperson'), 'value': [people[TEST_SALESPERSON]]},
              {'id': cid('Customer Reference'), 'value': ref}]
    rowid = write_record(ws(), None, values)
    src = line[3]
    write_record(LINES_WS, None, [
        {'id': CHILD['Orders'], 'value': [rowid]}, {'id': CHILD['Display Type'], 'value': [PRODUCT_LINE]},
        {'id': CHILD['Product'], 'value': src['Product']}, {'id': CHILD['Description'], 'value': src['Description']},
        {'id': CHILD['Quantity'], 'value': '1'}, {'id': CHILD['Unit'], 'value': src['Unit']},
        {'id': CHILD['Unit Price'], 'value': str(src['Unit Price'])}, {'id': CHILD['Discount'], 'value': '0'},
        {'id': CHILD['Taxes'], 'value': src['Taxes']}, {'id': CHILD['Sequence'], 'value': '10'}])
    print(f'  created {ref!r}: {rowid} — {TEST_CUSTOMER}, Expiration {expires} (made {today}), Online Payment '
          f'{online_payment}, one line copied from {line[0]} ({src["Description"]!r}, {src["Unit Price"]})')
    return rowid


def signing_link_cells(f, rowid):
    """Signing Link through `record get` and through the listing."""
    c = f[SIGNING_LINK]
    got = read_cell(c, read_record(ws(), rowid))
    row = next((r for r in C.records(ws(), APP) if r['rowid'] == rowid), {})
    return got, row.get(c['controlId']) or ''


LINK_EXPIRED = 17                               # GetLinkDetail's resultCode for 链接已失效 (ShareState/index.jsx)


def link_answer(url):
    """(resultCode, linkState, submit button, rowId) — what the public page's first call, `Worksheet/GetLinkDetail
    {id}`, answers for a link. Read-only: it is what opening the link does before the form loads; it submits
    nothing. linkState 0 is open, 1 already submitted."""
    from hap_cli.core.session import Session
    got = Session.load(None).api_call('Worksheet', 'GetLinkDetail', {'id': url.rstrip('/').rsplit('/', 1)[-1]})
    got = got.get('data', got) if isinstance(got, dict) else {}
    return got.get('resultCode'), got.get('linkState'), got.get('submitBtnName'), got.get('rowId')


def press_sign(rowid):
    """Share for Signature through the button API — `process/startProcess {appId: <worksheet>, triggerId: <btnId>,
    sources: [rowid]}`, what pd-openweb sends when the button is clicked on a record."""
    from hap_cli.core import workflow as wf
    from hap_cli.core.session import Session
    btn = hap.ids()['buttons'][KEY + SIGN]
    return wf.start_process(Session.load(None), ws(), btn, sources=[rowid])


def order_cells(f, rowid, names):
    d = read_record(ws(), rowid)
    return {n: read_cell(f[n], d) for n in names}


def step_signtest():
    """The two TEST quotations and their signing links. Creates what is missing, presses only where no link is
    stored yet, and prints each link for the browser test."""
    f = guard()
    if not hap.ids().get('buttons', {}).get(KEY + SIGN) or signed_workflow_id() is None:
        sys.exit(f'{SIGN} or {SIGNED_WF!r} is not built — run `sign` first')
    orders = sign_test_orders(f)
    share = hap.ids()['workflows'][KEY + SIGN]
    missing = [ref for ref in SIGN_TESTS if ref not in orders]
    if missing:
        line = template_line()
        for ref in missing:
            orders[ref] = create_sign_test(f, ref, SIGN_TESTS[ref][0], line, SIGN_TESTS[ref][1])
        time.sleep(3)
    numbers = {rowid: number for number, rowid in by_number().items()}
    problems = []
    for ref in SIGN_TESTS:
        rowid = orders[ref]
        C.remember('records', KEY + ref, rowid)
        state = order_cells(f, rowid, ('Status', 'Online Signature', 'Online Payment', 'Expiration', SIGNED_BY))
        links = signing_link_cells(f, rowid)
        offered = buttons_offered(rowid).get(SIGN)
        print(f"  {numbers.get(rowid)} {ref!r} ({rowid}): {status_label(state['Status'])}, Online Signature "
              f"{state['Online Signature']}, Online Payment {state['Online Payment']}, Expiration "
              f"{state['Expiration']!r}; {SIGN} {'offered' if offered else 'NOT offered'}")
        if not any(links):
            if not offered:
                problems.append(f'{ref}: no link, and {SIGN} is not offered on it')
                continue
            before = {r['id'] for r in all_runs_of(share)}
            print(f'  pressing {SIGN} on {numbers.get(rowid)}: {press_sign(rowid)}')
            for _ in range(60):
                links = signing_link_cells(f, rowid)
                if all(links):
                    break
                time.sleep(1)
            runs = new_runs(share, before, 1, seconds=30)
            steps = run_steps(runs[0]['id'])[0] if len(runs) == 1 else []
            want = [L_DATED, L_SAVE_DATED] if state['Expiration'] else [L_OPEN, L_SAVE_OPEN]
            print(f"        run {[(r['id'], r.get('status')) for r in runs]} through {steps}")
            if len(runs) != 1 or runs[0].get('status') != 2 or steps[-2:] != want:
                problems.append(f'{ref}: the run went {steps}, wanted it to end {want}')
        if not all(links) or links[0] != links[1]:
            problems.append(f'{ref}: Signing Link reads {links[0]!r} (record get) / {links[1]!r} (listing)')
            continue
        print(f'  OK  {numbers.get(rowid)} Signing Link (both read paths): {links[0]}')
        answer = link_answer(links[0])
        expired = bool(state['Expiration']) and state['Expiration'] < time.strftime('%Y-%m-%d')
        if state[SIGNED_BY]:
            print(f'        signed by {state[SIGNED_BY]!r}; the link answers {answer} (linkState 1: submitted)')
        elif expired:
            ok = answer[0] == LINK_EXPIRED
            print(f"  {'OK  ' if ok else 'FAIL'}      Expiration {state['Expiration']} is past: the link answers {answer}, "
                  f'wanted resultCode {LINK_EXPIRED} (link expired)')
            if not ok:
                problems.append(f'{ref}: an expired link answers {answer}')
        else:
            ok = answer == (1, 0, SUBMIT_TEXT, rowid)
            print(f"  {'OK  ' if ok else 'FAIL'}      the link is open: {answer}")
            if not ok:
                problems.append(f'{ref}: the link answers {answer}, wanted (1, 0, {SUBMIT_TEXT!r}, {rowid})')
    if problems:
        sys.exit('  ' + '\n  '.join(problems))
    return True


# ── 17e · driving *Signed: confirm the order* from the CLI ──────────────────
#
# `selfsign` proves everything downstream of the link without a browser, on a third TEST quotation of its own (never
# on the two `signtest` makes for the browser test, which it would confirm). A `record update` that writes Signature
# and Signed By is the same worksheet event the link's submission is expected to be — the one thing it cannot show is
# that the link's submission *is* such an event, which is the browser test's first check. Four cases, each read back
# through the workflow's run list (a new run told apart by instance id) and the order's cells:
#
#   A  signed, lines complete, no online payment → one run: Set Signed On → count → No → No online payment → Confirm
#      the order → 【Quotation signed】; Status Sales Order, Quotation/Order Date and Signed On now
#   B  Set to Quotation on it                    → **no run** (Signature cleared fails the trigger condition)
#   C  a product line with no product, signed    → one run ending 【Quotation signed, not confirmed】; still a Quotation,
#                                                  Signed On set, the signature kept
#   D  that line made a Note, Online Payment ticked, signed → one run ending 【Quotation signed, payment due】; still a
#      Quotation
#
# The clear before C and D writes Signature empty, which must start no run either. Like `selfcheck` this step
# writes records by design (TEST ones only) and is not part of a "saves nothing" re-run; each run starts by putting
# the order back to a clean quotation. The three notices go to the order's Salesperson (the owner) in the app.
SIGN_CLI = 'TEST Sign & Accept, CLI run'
SIGN_CLI_LINE = 'TEST line with no product'


def upload_signature():
    """A small PNG scribble uploaded to the file store, as a Signature's value: the stored file's URL without the
    temporary token (`hap guide record`: a Signature is an image URL, uploaded first)."""
    import math, struct, tempfile, zlib
    w, h = 240, 80
    ink = {(x, int(40 + 18 * math.sin(x / 14.0) * math.cos(x / 37.0)) + dy) for x in range(20, 220) for dy in (-1, 0, 1)}
    raw = b''.join(b'\x00' + b''.join(b'\x00\x00\x00' if (x, y) in ink else b'\xff\xff\xff' for x in range(w))
                   for y in range(h))
    chunk = lambda t, d: struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    png = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) +
           chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))
    with tempfile.NamedTemporaryFile(suffix='.png', prefix='test-signature-', delete=False) as fh:
        fh.write(png)
    try:
        got = hap.run('upload', fh.name, '--worksheet-id', ws(), '-a', APP)
    finally:
        os.unlink(fh.name)
    got = got[0] if isinstance(got, list) else (got.get('data') or [got])[0]
    return got['serverName'] + got['key']


def all_runs_of(pid):
    rows, page = [], 1
    while True:
        got = hap.run('approval', 'history', '--process-id', pid, '-n', '50', '-p', str(page))
        data = (got.get('data', got) if isinstance(got, dict) else got) or []
        rows += data
        if len(data) < 50:
            return rows
        page += 1


def new_runs(pid, before, n, seconds=90):
    """The runs started since `before` (a set of instance ids) once `n` of them have finished; with n 0 it waits
    `seconds` and returns whatever appeared."""
    deadline = time.time() + seconds
    while True:
        new = [r for r in all_runs_of(pid) if r['id'] not in before]
        done = n > 0 and len(new) >= n and all(r.get('status') != 1 for r in new)
        if done or time.time() > deadline:
            if done:
                time.sleep(4)
                new = [r for r in all_runs_of(pid) if r['id'] not in before]
            return new
        time.sleep(3)


def run_steps(instance_id):
    """(the steps one run passed through, in order; [(notice text as sent, its recipient)] of its 站内通知 steps)."""
    d = hap.run('approval', 'history-detail', instance_id)
    d = d.get('data', d) if isinstance(d, dict) else {}
    works = d.get('works') or []
    notices = [(i.get('opinion'), (i.get('workItemAccount') or {}).get('fullName'))
               for w in works if (w.get('flowNode') or {}).get('type') == NOTICE for i in w.get('workItems') or []]
    return [(w.get('flowNode') or {}).get('name') for w in works], notices


def sign_cells(f, rowid):
    """Status, the date, the signature trio and Online Payment — `record get`, with Signature also through the
    listing (neither read path is complete)."""
    got = order_cells(f, rowid, ('Status', 'Quotation/Order Date', SIGNED_BY, SIGNED_ON, 'Online Payment'))
    d = read_record(ws(), rowid)
    row = next((r for r in C.records(ws(), APP) if r['rowid'] == rowid), {})
    got['Signature'] = bool(d.get(f[SIGNATURE_FIELD].get('alias') or '') or d.get(f[SIGNATURE_FIELD]['controlId'])
                            or row.get(f[SIGNATURE_FIELD]['controlId']))
    got['Status'] = status_label(got['Status'])
    return got


def step_selfsign():
    f = guard()
    spid = signed_workflow_id()
    if not spid:
        sys.exit(f'{SIGNED_WF!r} is not built — run `sign` first')
    f_lines = hap.by_name(c for c in hap.controls(LINES_WS) if c['type'] != C.TAB)
    display = {o['value']: o['key'] for o in f_lines['Display Type'].get('options') or [] if not o.get('isDeleted')}
    ref = f['Customer Reference']
    found = [r['rowid'] for r in C.records(ws(), APP)
             if (r.get(ref['controlId']) or read_cell(ref, read_record(ws(), r['rowid']))) == SIGN_CLI]
    if len(found) > 1:
        sys.exit(f'{len(found)} orders carry {SIGN_CLI!r}')
    rowid = found[0] if found else create_sign_test(f, SIGN_CLI, '0', template_line())
    C.remember('records', KEY + SIGN_CLI, rowid)
    number = {r: n for n, r in by_number().items()}.get(rowid)
    cid = lambda n: f[n]['controlId']
    problems = []
    since = lambda t: time.strftime('%Y-%m-%d %H:%M', time.localtime(t))

    def clean(label, extra=()):
        """Signature, Signed By and Signed On emptied (a write of Signature that must start no run), plus `extra`."""
        before = {r['id'] for r in all_runs_of(spid)}
        write_cells(rowid, [{'id': cid(SIGNATURE_FIELD), 'value': ''}, {'id': cid(SIGNED_BY), 'value': ''},
                            {'id': cid(SIGNED_ON), 'value': ''}] + list(extra))
        runs = new_runs(spid, before, 0, seconds=20)
        state = sign_cells(f, rowid)
        ok = not runs and not state['Signature'] and state[SIGNED_BY] == '' and state[SIGNED_ON] == ''
        print(f"  {'OK  ' if ok else 'FAIL'}  {label}: {state} — runs started: {[r['id'] for r in runs]}")
        if not ok:
            problems.append(f'{label}: {state}, runs {runs}')

    def sign(label, want_status, want_last):
        before = {r['id'] for r in all_runs_of(spid)}
        t0 = time.time()
        write_cells(rowid, [{'id': cid(SIGNED_BY), 'value': SIGNER}, {'id': cid(SIGNATURE_FIELD),
                                                                      'value': upload_signature()}])
        runs = new_runs(spid, before, 1)
        state = sign_cells(f, rowid)
        steps, notices = run_steps(runs[0]['id']) if len(runs) == 1 else ([], [])
        text = {N_SIGNED: MSG_SIGNED, N_MISSING: MSG_MISSING, N_PAYMENT: MSG_PAYMENT}[want_last].format(
            number=number, who=SIGNER)
        ok = len(runs) == 1 and runs[0].get('status') == 2 and steps[-1:] == [want_last] and \
            state['Status'] == want_status and state['Signature'] and state[SIGNED_BY] == SIGNER and \
            (state[SIGNED_ON] or '')[:16] >= since(t0 - 60) and [n[0] for n in notices] == [text] and \
            all(n[1] for n in notices)
        if want_status == 'Sales Order':
            ok &= (state['Quotation/Order Date'] or '')[:16] >= since(t0 - 60)
        print(f"  {'OK  ' if ok else 'FAIL'}  {label}: run {[(r['id'], r.get('status')) for r in runs]} through "
              f'{steps}\n        notice {notices}\n        order now {state}')
        if not ok:
            problems.append(f'{label}: runs {runs}, steps {steps}, notices {notices}, state {state}')

    print(f'  {number} {SIGN_CLI!r} ({rowid})')
    clean('reset to a clean quotation', [{'id': cid('Status'), 'value': [STATUS_KEYS['Quotation']]},
                                         {'id': cid('Online Payment'), 'value': '0'}])
    lines = [r for r in C.records(LINES_WS, APP)
             if (read_cell(f_lines['Orders'], read_record(LINES_WS, r['rowid'])) or [None])[0] == rowid]
    orphan = next((r['rowid'] for r in lines
                   if read_cell(f_lines['Description'], read_record(LINES_WS, r['rowid'])) == SIGN_CLI_LINE), None)
    if orphan:                                      # a re-run: the line is a Note since case D; case A needs it so
        write_record(LINES_WS, orphan, [{'id': CHILD['Display Type'], 'value': [display['Note']]}])
    sign('A  signed, lines complete, no online payment', 'Sales Order', N_SIGNED)
    before = {r['id'] for r in all_runs_of(spid)}
    press(SET_TO_QUOTATION, rowid)
    wait_until(f, rowid, lambda s: status_label(s['Status']) == 'Quotation')
    runs = new_runs(spid, before, 0, seconds=20)
    state = sign_cells(f, rowid)
    ok = not runs and state['Status'] == 'Quotation' and not state['Signature'] and not state[SIGNED_BY]
    print(f"  {'OK  ' if ok else 'FAIL'}  B  Set to Quotation: {state} — runs of {SIGNED_WF!r} started: "
          f"{[r['id'] for r in runs]}")
    if not ok:
        problems.append(f'B Set to Quotation: {state}, runs {runs}')
    if orphan:
        write_record(LINES_WS, orphan, [{'id': CHILD['Display Type'], 'value': [PRODUCT_LINE]}])
    else:
        orphan = write_record(LINES_WS, None, [
            {'id': CHILD['Orders'], 'value': [rowid]}, {'id': CHILD['Display Type'], 'value': [PRODUCT_LINE]},
            {'id': CHILD['Description'], 'value': SIGN_CLI_LINE}, {'id': CHILD['Quantity'], 'value': '1'},
            {'id': CHILD['Unit Price'], 'value': '0'}, {'id': CHILD['Discount'], 'value': '0'},
            {'id': CHILD['Sequence'], 'value': '20'}])
    sign('C  a product line with no product', 'Quotation', N_MISSING)
    write_record(LINES_WS, orphan, [{'id': CHILD['Display Type'], 'value': [display['Note']]}])
    clean('cleared before D (Signature written empty)', [{'id': cid('Online Payment'), 'value': '1'}])
    sign('D  online payment required', 'Quotation', N_PAYMENT)
    if problems:
        print('  selfsign: ' + '\n            '.join(problems))
        sys.exit(1)
    print(f'  selfsign: OK — {SIGNED_WF!r} confirms a signed quotation, refuses one with a product line that has no '
          f'product, leaves one that asks for online payment, and starts no run when Signature is cleared. '
          f'{number} is left signed, a Quotation with Online Payment ticked.')
    return True


# ── 13c · reading the four buttons and the guard back ───────────────────────

def button_problems():
    """Every difference between the four buttons — their conditions, batch flags, confirmations, workflows and
    Confirm's guard — and §13's spec, plus the owner's button and control read back. Printed by `check`."""
    ctrls = hap.controls(ws())
    f, problems = hap.by_name(c for c in ctrls if c['type'] != C.TAB), []
    names = {c['controlId']: c['controlName'] for c in ctrls}
    live = {b['name']: b for b in hap.listing('worksheet', 'custom-actions', ws())}
    label = {v: k for k, v in STATUS_KEYS.items()}
    wanted, workflows = writes_wanted(f), hap.ids().get('workflows', {})
    for spec, _, step in button_specs(f):
        name = spec['name']
        b = live.get(name)
        if b is None:
            problems.append(f'the {name!r} button is missing — run `buttons`')
            continue
        if button_state(b) != button_wanted(spec):
            problems.append(f'{name}: stored {button_state(b)}, wanted {button_wanted(spec)} — run `buttons`')
            continue
        conds = [(names.get(cid, cid), ftype, [label.get(v, v) for v in vals])
                 for cid, _dt, _sp, ftype, vals in view_filter_state(b.get('filters'))]
        print(f"  OK  {name:<17} btnId={b['btnId']} isBatch={bool(b.get('isBatch'))} "
              f"clickType={b.get('clickType')} confirm={b.get('confirmMsg') or ''!r}\n"
              f"        when {conds}")
        pid = workflows.get(KEY + name)
        if not pid:
            problems.append(f'{name}: no workflow id in ids.json — run `buttons`')
            continue
        proc, byname = nodes_by_name(pid)
        if step not in byname:
            problems.append(f'{name}: {step!r} is not in workflow {pid} ({sorted(byname)})')
            continue
        got = writes_live(pid, byname[step]['id'])
        want = [write_state(x) for x in wanted[name]]
        if got != want:
            problems.append(f'{name}: {step!r} writes {json.dumps(got, ensure_ascii=False)}, wanted '
                            f'{json.dumps(want, ensure_ascii=False)} — run `buttons`')
        else:
            print('        then ' + ', '.join(
                f"{names.get(x['fieldId'], x['fieldId'])} = "
                + (f"{label.get(x['fieldValue'], x['fieldValue'])!r}" if x['fieldValue'] != ''
                   else ('now' if x['nodeId'] == SYSTEM_NODE else 'cleared'))
                for x in got))
        if name != CONFIRM:
            steps = [n['name'] for n in proc['flowNodeMap'].values()
                     if n.get('typeId') not in (None, 0, 100) and n.get('prveId')]
            if steps != [step]:
                problems.append(f'{name}: workflow holds {steps}, wanted only [{step!r}] — Odoo checks nothing '
                                f'else on it')
    problems += guard_problems()
    problems += deliver_problems()
    problems += apply_problems(f)
    # The owner's: their Send Quotation is rewired by `send` (§16) and read back in full by `send_problems`; here
    # only that it is still there. Their Sign & Accept placeholder was deleted by the owner on 22 Sep 2026 (§17
    # builds Sign & Accept); it is only noted if that id ever comes back.
    b = live.get(OWNERS_BUTTON)
    if not b or b['btnId'] != OWNERS_BUTTON_ID:
        problems.append(f"the owner's {OWNERS_BUTTON!r} button {OWNERS_BUTTON_ID} is gone — this builder must "
                        f'never delete it')
    c = next((x for x in hap.controls(ws()) if x['controlId'] == OWNERS_CONTROL_ID), None)
    if c is None:
        print(f"  the owner's {OWNERS_CONTROL!r} placeholder {OWNERS_CONTROL_ID} (t{SEARCH_BTN}) — deleted by the "
              f'owner on 22 Sep 2026; §17 builds {SIGN!r} instead')
    else:
        print(f"  NOTE the owner's {OWNERS_CONTROL!r} {OWNERS_CONTROL_ID} t{c['type']} is back at r{c.get('row')}"
              f"c{c.get('col')}s{c.get('size')} — the owner's; this builder does not touch it")
    for name in BUTTONS + (DELIVER, APPLY):
        if live.get(name):
            C.remember('buttons', KEY + name, live[name]['btnId'])
    return problems


def guard_problems():
    """Confirm's product guard, read back: the chain, the count's three conditions, the branch condition, the
    notification and its recipient, that nothing follows the gateway, and that no abort node exists."""
    pid = hap.ids().get('workflows', {}).get(KEY + CONFIRM)
    if not pid:
        return [f'no workflow id for {CONFIRM} in ids.json — run `buttons`']
    proc, byname = nodes_by_name(pid)
    missing = [n for n in GUARD_STEPS if n not in byname]
    if missing:
        return [f'{CONFIRM} workflow: {missing} missing — run `buttons`']
    problems, chain = [], {n: byname[n]['id'] for n in GUARD_STEPS}
    ends = lambda node_id: proc['flowNodeMap'][node_id].get('nextId') in (None, '', '99')
    for node_id, nxt in ((proc['startEventId'], chain[COUNT_STEP]),
                         (chain[COUNT_STEP], chain[PRODUCT_BRANCH])):
        if proc['flowNodeMap'][node_id].get('nextId') != nxt:
            problems.append(f"{proc['flowNodeMap'][node_id]['name']!r} runs into "
                            f"{proc['flowNodeMap'].get(proc['flowNodeMap'][node_id].get('nextId'), {}).get('name')!r}")
    # Nothing follows the gateway and each path ends at its own last step: the update hangs off the *No* path,
    # so the refusal path needs no abort and HAP's untranslated 中止 toast is never drawn (15 §6.6).
    for name in (PRODUCT_BRANCH, TELL_STEP, STEP[CONFIRM]):
        if not ends(chain[name]):
            problems.append(f'{name!r} runs into '
                            f'{proc["flowNodeMap"].get(proc["flowNodeMap"][chain[name]].get("nextId"), {}).get("name")!r}'
                            ' — the gateway must converge on nothing and every path end at its last step')
    aborts = [n['name'] for n in proc['flowNodeMap'].values() if n.get('typeId') == ABORT]
    if aborts:
        problems.append(f"abort node(s) {aborts} in the {CONFIRM} workflow — an aborted run draws HAP's "
                        'untranslated 中止 toast (15 §6.6)')
    count = read_node(pid, chain[COUNT_STEP])
    if (count.get('actionId'), count.get('appId'), count.get('reportControlId'), count.get('reportType')) != \
            (WORKSHEET_TOTAL, LINES_WS, '', 0):
        problems.append(f"{COUNT_STEP}: actionId={count.get('actionId')} appId={count.get('appId')} "
                        f"reportControlId={count.get('reportControlId')!r} reportType={count.get('reportType')}")
    conds = [c for flt in count.get('filters') or [] for group in flt.get('conditions') or [] for c in group]
    got = [(c['filedId'], c['conditionId'],
            [v.get('controlId') or (v.get('value') or {}).get('value') for v in c['conditionValues']])
           for c in conds]
    want = [(LINES_ORDERS, RELATION_EQ, ['rowid']),
            (CHILD['Display Type'], IS_ANY_OF, ['Product']),
            (CHILD['Product'], EMPTY, [])]
    if got != want:
        problems.append(f'{COUNT_STEP} filter {got}, wanted {want}')
    elif [v.get('nodeId') for c in conds for v in c['conditionValues']][:1] != [proc['startEventId']]:
        problems.append(f'{COUNT_STEP}: the Orders relation is not compared with the triggering order')
    else:
        print(f'  OK  {COUNT_STEP} counts Order Lines where Orders is this order, Display Type is Product and '
              f'Product is empty')
    yes, no = branch_paths(proc, chain[PRODUCT_BRANCH], chain[TELL_STEP])
    for path, name, want_cond in ((yes, 'Yes', [(chain[COUNT_STEP], NUMBER_FX, AT_LEAST_ONE, ['1'])]),
                                  (no, 'No', [])):
        got = read_node(pid, path['id'])
        live = [(c['nodeId'], c['filedId'], c['conditionId'], [v.get('value') for v in c['conditionValues']])
                for g in got.get('conditions') or [] for c in g]
        if path.get('name') != name or live != want_cond:
            problems.append(f'branch path {path.get("name")!r}: {live}, wanted {want_cond}')
    for path, step in ((yes, TELL_STEP), (no, STEP[CONFIRM])):
        if path.get('nextId') != chain[step]:
            problems.append(f'branch path {path.get("name")!r} runs into '
                            f'{proc["flowNodeMap"].get(path.get("nextId"), {}).get("name")!r}, not {step!r}')
    tell = read_node(pid, chain[TELL_STEP])
    if tell.get('sendContent') != MSG_NO_PRODUCT:
        problems.append(f'{TELL_STEP}: message {tell.get("sendContent")!r}, wanted {MSG_NO_PRODUCT!r}')
    who = [(a.get('type'), a.get('entityId'), a.get('roleId')) for a in tell.get('accounts') or []]
    if who != [(TRIGGER_USER['type'], TRIGGER_USER['entityId'], TRIGGER_USER['roleId'])]:
        problems.append(f'{TELL_STEP}: recipient {who}, wanted the person who pressed the button')
    if not problems:
        print(f'  OK  {CONFIRM} refuses an order with a product line that has no Product: the count, the '
              f'branch, Odoo\'s own notification on the Yes path and the update on the No path — no abort node')
        print(f'  NOTE the refusal still draws HAP\'s green "Operation completed" toast (15 §6.7, unresolved): '
              f'the run completes, the order does not move, and the explanation waits in the notification '
              f'centre')
    return problems


# ── 18 · Incoterm: the Shipping pair, wired to the Incoterms worksheet ──────
#
# Odoo's `sale_stock` adds two fields to `sale.order` and shows them together in *Other Info › Shipping*:
# `incoterm` (Many2one account.incoterms, `options="{'no_open': True, 'no_create': True}"`) and `incoterm_location`
# (Char). The owner built **Incoterm Location** by hand on 21 Sep 2026 (6ab0c528e54d2a34fa4e8124, no alias); this step
# gives it its alias in one version-pinned save and appends **Incoterm** beside it — never a second Location.
#
# **Neither is locked on a confirmed, locked or cancelled order.** Odoo's view gives neither field a `readonly`
# (sale_stock/views/sale_order_views.xml:27-28, 19.0 source; the tenant extract's read-only table does not list them
# either), and `sale.order.write` refuses only a pricelist change on a confirmed order — so RULE_CONFIRMED and
# RULE_LOCKED do not name them. Odoo's `no_create` is the Roles' job here: every business role only views Incoterms.
#
# Appended with `C.append_controls` (the server mints the id); the payload carries the Other Info tab's `sectionId`,
# which `add-fields` keeps, so it lands at the foot of that tab at row 9999 — **placement is the owner's**.
INCOTERM, INCOTERM_LOCATION = 'Incoterm', 'Incoterm Location'
INCOTERM_FIELDS = (INCOTERM, INCOTERM_LOCATION)
INCOTERMS_WS = '6ab28ec1e43d174ab3cd760a'           # incoterms.py's worksheet
INCOTERM_LOCATION_ID = '6ab0c528e54d2a34fa4e8124'   # the owner's control, read off the app on 22 Sep 2026
OTHER_INFO_TAB = '6ab0c1cdbd43f55762c783db'         # the owner's Other Info tab (type 52)
INCOTERM_ALIAS = {INCOTERM: 'incoterm', INCOTERM_LOCATION: 'incoterm_location'}   # Odoo's names on sale.order
# Intent, for the owner: a full-width row of its own directly under the *Shipping* divider (row 22 today), so the tab
# reads Shipping › Incoterm › Incoterm Location — Odoo's order. Incoterm Location and everything under it move down
# one row. `add-fields` parks it at row 9999; only a full save places it.
INCOTERM_PLACE = (23, 0, 12)
INCOTERM_DESC = ('International Commercial Terms are a series of predefined commercial terms used in international '
                 'transactions.')                   # Odoo's help on the field, which reads well for a user


def incoterms_active():
    """The Incoterms worksheet's Active checkbox — what the picker filter tests."""
    active = C.fields(INCOTERMS_WS).get('Active')
    if not active or active['type'] != CHECKBOX:
        sys.exit(f'Incoterms has no Active checkbox ({active and active["type"]}) — run incoterms.py first')
    return active['controlId']


def incoterm_control():
    return C.control('RELATE_SHEET', INCOTERM, INCOTERM_PLACE, alias=INCOTERM_ALIAS[INCOTERM], hint='',
                     desc=INCOTERM_DESC, data_source=INCOTERMS_WS, multi=False,
                     advanced_setting={'bidirectional': '0', 'showtype': '3',
                                       'filters': C.active_picker(incoterms_active())},
                     extra={'fieldPermission': '111', 'sectionId': OTHER_INFO_TAB})


def incoterm_spec():
    """What each control must read back as, the picker filter aside (compared by meaning). Row, column and tab are
    placement — the owner's — so not asserted."""
    return {
        INCOTERM: {'type': RELATION, 'alias': INCOTERM_ALIAS[INCOTERM], 'desc': INCOTERM_DESC, 'hint': '',
                   'required': False, 'fieldPermission': '111', 'dataSource': INCOTERMS_WS, 'enumDefault': 1,
                   'advancedSetting.bidirectional': '0', 'advancedSetting.showtype': '3'},
        INCOTERM_LOCATION: {'type': TEXT, 'alias': INCOTERM_ALIAS[INCOTERM_LOCATION]},
    }


def incoterm_problems(f):
    problems = []
    counts = {}
    for c in hap.controls(ws()):
        counts[c['controlName']] = counts.get(c['controlName'], 0) + 1
    for n in INCOTERM_FIELDS:
        if counts.get(n, 0) != 1:
            problems.append(f'{WORKSHEET} carries {counts.get(n, 0)} controls named {n!r}, wanted exactly one')
    if f.get(INCOTERM_LOCATION, {}).get('controlId') != INCOTERM_LOCATION_ID:
        problems.append(f"{INCOTERM_LOCATION} is {f.get(INCOTERM_LOCATION, {}).get('controlId')}, not the owner's "
                        f'{INCOTERM_LOCATION_ID} — re-read the worksheet')
    spec = incoterm_spec()
    for n in INCOTERM_FIELDS:
        c = f.get(n)
        if c is None:
            problems.append(f'{n} is not on {WORKSHEET} — run `incoterm`')
            continue
        diff = C.drift(c, spec[n])
        if diff:
            problems.append(f'{n}: {json.dumps(diff, ensure_ascii=False, default=str)} — run `incoterm`')
        if hap.ids().get('controls', {}).get(KEY + n) != c['controlId']:
            problems.append(f'{n}: ids.json does not hold {c["controlId"]} — run `incoterm`')
    c = f.get(INCOTERM)
    if c:
        got = C.picker_state((c.get('advancedSetting') or {}).get('filters'))
        want = C.picker_state(C.active_picker(incoterms_active()))
        if got != want:
            problems.append(f'{INCOTERM} picker filter {got}, wanted {want} (Active is ticked) — run `incoterm`')
    title = [x['controlName'] for x in hap.controls(INCOTERMS_WS) if x.get('attribute') == 1]
    if title != ['Display Name']:
        problems.append(f'Incoterms\' title is {title}, not Display Name — the picker would not show "[FOB] FREE ON '
                        'BOARD"')
    back = [x['controlName'] for x in hap.controls(INCOTERMS_WS) if x.get('dataSource') == ws()]
    if back:
        problems.append(f'Incoterms carries {back} pointing back at {WORKSHEET} — {INCOTERM} must be one-way')
    return problems


def step_incoterm():
    """Append Incoterm if it is missing and give the owner's Incoterm Location its alias — plus anything the append did
    not store — in one version-pinned save limited to those two controls; read both back. Re-running saves nothing."""
    f = guard()
    counts = {}
    for c in hap.controls(ws()):
        counts[c['controlName']] = counts.get(c['controlName'], 0) + 1
    location = f.get(INCOTERM_LOCATION)
    if counts.get(INCOTERM_LOCATION) != 1 or not location or location['controlId'] != INCOTERM_LOCATION_ID \
            or location['type'] != TEXT:
        sys.exit(f"{INCOTERM_LOCATION} is not the owner's single Text {INCOTERM_LOCATION_ID} "
                 f"({counts.get(INCOTERM_LOCATION)} found, {location and (location['controlId'], location['type'])}) "
                 '— re-read the worksheet before writing')
    if counts.get(INCOTERM, 0) > 1:
        sys.exit(f'{WORKSHEET} already carries {counts[INCOTERM]} controls named {INCOTERM!r} — stopping')
    if INCOTERM in f:
        print(f'  {INCOTERM} is already on {WORKSHEET}; nothing appended')
    else:
        f = C.append_checked(ws(), [incoterm_control()], 'orders_controls_pre_incoterm', 'incoterm',
                             untouched=(INCOTERMS_WS,))
        c = f[INCOTERM]
        print(f"  added {INCOTERM}: {c['controlId']} (t{c['type']}, row {c.get('row')}, tab "
              f"{'Other Info' if c.get('sectionId') == OTHER_INFO_TAB else c.get('sectionId')!r})")
    spec = {}
    for n, want in incoterm_spec().items():
        stale = C.drift(f[n], want)
        if stale:
            spec[f[n]['controlId']] = {k: want[k] for k in stale}
    picker = C.active_picker(incoterms_active())
    if C.picker_state((f[INCOTERM].get('advancedSetting') or {}).get('filters')) != C.picker_state(picker):
        spec.setdefault(f[INCOTERM]['controlId'], {})['advancedSetting.filters'] = picker
    if spec:
        pinned_write('incoterm', spec, 'orders_controls_pre_incoterm_alias')
        f = C.fields(ws())
    else:
        print(f'  {list(INCOTERM_FIELDS)} already as specified; nothing saved')
    for n in INCOTERM_FIELDS:
        C.remember('controls', KEY + n, f[n]['controlId'])
    problems = incoterm_problems(f)
    if problems:
        sys.exit('\n'.join(problems))
    for n in INCOTERM_FIELDS:
        c = f[n]
        print(f"  OK  {n:<18} {c['controlId']} t{c['type']} alias={c.get('alias')} perm={c.get('fieldPermission')!r} "
              f"r{c.get('row')}c{c.get('col')}s{c.get('size')} tab="
              f"{'Other Info' if c.get('sectionId') == OTHER_INFO_TAB else c.get('sectionId')!r}")
    if f[INCOTERM].get('row') == 9999:
        print(f'  placement outstanding — the owner places {INCOTERM} in the designer; intended (row, col, size) '
              f'{INCOTERM_PLACE}: its own row directly under the Shipping divider, above {INCOTERM_LOCATION}')
    return True


INCOTERM_TEST = 'TEST Sign & Accept, CLI run'     # the TEST order `selfsign` keeps (ids.json records)
INCOTERM_TEST_CODE = 'FOB'


def incoterm_cell(value):
    """A single Relation's cell as (rowid, title) pairs, from `record get` (a list or its JSON) or the listing."""
    if isinstance(value, str):
        try:
            value = json.loads(value) if value.startswith('[') else []
        except ValueError:
            return value
    return [(v.get('sid') or v.get('rowid'), v.get('name')) for v in value or [] if isinstance(v, dict)]


def read_incoterm(rowid, f):
    """Incoterm and Incoterm Location on one order, through `record get` (by alias) and the listing (by id)."""
    got = hap.run('worksheet', 'record', 'get', ws(), rowid, '-a', APP)['data']
    listed = next((r for r in C.records(ws(), APP) if r['rowid'] == rowid), {})
    return {'get': (incoterm_cell(got.get(INCOTERM_ALIAS[INCOTERM])), got.get(INCOTERM_ALIAS[INCOTERM_LOCATION])),
            'list': (incoterm_cell(listed.get(f[INCOTERM]['controlId'])),
                     listed.get(f[INCOTERM_LOCATION]['controlId']))}


def step_selfincoterm():
    """On the TEST order: set Incoterm to FOB and Incoterm Location to a TEST place through `record update`, read both
    back through `record get` **and** the listing, then put both back as they were and read that back too."""
    f = guard()
    problems = incoterm_problems(f)
    if problems:
        sys.exit('\n'.join(problems))
    rowid = hap.ids()['records'][KEY + INCOTERM_TEST]
    fob = next((r['rowid'] for r in C.records(INCOTERMS_WS, APP)
                if r.get(C.fields(INCOTERMS_WS)['Code']['controlId']) == INCOTERM_TEST_CODE), None)
    if not fob:
        sys.exit(f'no Incoterm {INCOTERM_TEST_CODE} — run incoterms.py seed')
    before = read_incoterm(rowid, f)
    print(f'  {INCOTERM_TEST} ({rowid}) before: {before}')
    if before['get'] != before['list']:
        print('  NOTE the two read paths differ before the test')
    was_rows = [r for r, _ in before['get'][0]]
    was_text = before['get'][1] or ''
    write = lambda rows, text: hap.run('worksheet', 'record', 'update', ws(), rowid, '-a', APP, '--fields-json',
                                       json.dumps([{'id': f[INCOTERM]['controlId'], 'value': rows},
                                                   {'id': f[INCOTERM_LOCATION]['controlId'], 'value': text}]))
    write([fob], 'TEST Port Klang')
    time.sleep(3)
    during = read_incoterm(rowid, f)
    print(f'  set:   {during}')
    want = ([(fob, '[FOB] FREE ON BOARD')], 'TEST Port Klang')
    for path in ('get', 'list'):
        if during[path] != want:
            problems.append(f'{path}: {during[path]}, wanted {want}')
    write(was_rows, was_text)
    time.sleep(3)
    after = read_incoterm(rowid, f)
    print(f'  back:  {after}')
    if after['get'] != before['get'] or after['list'] != before['list']:
        problems.append(f'not put back: {after}, was {before}')
    print('  selfincoterm: ' + ('OK — Incoterm and Incoterm Location stored and read back through both paths, and put '
                                'back' if not problems else 'DIFFERENCES\n    ' + '\n    '.join(problems)))
    if problems:
        sys.exit(1)


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
    unknown = sorted(set(f) - set(CONTROLS) - set(NEW) - set(PART1) - set(DISCOUNT_FIELDS) - {TERMS, SIGNING_LINK}
                     - set(INCOTERM_FIELDS))
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
        if view_filter_state(info.get('filters')) != view_filter_state(want):
            problems.append(f"the owner's {name!r} view filters {view_filter_state(info.get('filters'))}, wanted "
                            f'{view_filter_state(want)} — run `views`')
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
    pid = hap.ids().get('records', {}).get(PRODUCT_KEY)
    if not pid:
        problems.append(f'no {PRODUCT_KEY!r} in ids.json — run `discountproduct`')
    else:
        found = discount_product_problems(pid)
        vid = hap.ids().get('records', {}).get(VARIANT_KEY)
        live_vid, count = discount_variant_of(pid)
        if (vid, count) != (live_vid, 1):
            found.append(f'the {DISCOUNT_PRODUCT} variant: ids.json {vid}, live {live_vid} ({count} variant(s))')
        else:
            found += discount_variant_problems(pid, vid)
        problems += found
        if not found:
            print(f'  OK  the {DISCOUNT_PRODUCT} product {pid} (Service, RM 0.00, no taxes, Services, Units) and its '
                  f'one variant {vid}')
    found = discount_fields_problems(f)
    problems += found
    if not found:
        print(f"  OK  {DISCOUNT_TYPE} {f[DISCOUNT_TYPE]['controlId']} ({' · '.join(DISCOUNT_OPTIONS)}) and "
              f"{DISCOUNT_VALUE} {f[DISCOUNT_VALUE]['controlId']} (2 decimals), aliases "
              f"{DISCOUNT_ALIAS[DISCOUNT_TYPE]} / {DISCOUNT_ALIAS[DISCOUNT_VALUE]}"
              + ('' if all(f[n].get('row') != 9999 for n in DISCOUNT_FIELDS)
                 else ' — still parked at row 9999, for the owner to place'))
    problems += button_problems()
    # §16: the owner's Send Quotation, rewired
    problems += send_problems(f)
    # §17: Sign & Accept — Signing Link, Share for Signature and its Get Link workflow, Signed: confirm the order
    found = signing_link_problems(f)
    problems += found
    if not found:
        c = f[SIGNING_LINK]
        print(f"  OK  {SIGNING_LINK} {c['controlId']} (text, alias {SIGNING_LINK_ALIAS}, permission "
              f'{SIGNING_LINK_PERMISSION})' + (' — still parked at row 9999, for the owner to place'
                                               if c.get('row') == 9999 else ''))
    problems += sign_share_problems(f)
    problems += signed_problems(f)
    # §18: Incoterm, and the alias on the owner's Incoterm Location
    found = incoterm_problems(f)
    problems += found
    if not found:
        c = f[INCOTERM]
        print(f"  OK  {INCOTERM} {c['controlId']} (Relation → Incoterms, one-way, dropdown, active only, alias "
              f"{INCOTERM_ALIAS[INCOTERM]}) and the owner's {INCOTERM_LOCATION} {INCOTERM_LOCATION_ID} (alias "
              f"{INCOTERM_ALIAS[INCOTERM_LOCATION]})" + (' — Incoterm still parked at row 9999, for the owner to place'
                                                         if c.get('row') == 9999 else ''))
    # §15: Terms and conditions, the three templates on disk, and the System Print template on Orders
    found = terms_problems(f)
    problems += found
    if not found:
        c = f[TERMS]
        print(f"  OK  {TERMS} {c['controlId']} (rich text, alias {TERMS_ALIAS}, permission {TERMS_PERMISSION}, "
              f'no default)' + (' — still parked at row 9999, for the owner to place' if c.get('row') == 9999 else ''))
        found = template_problems(f)
        problems += found
        if not found:
            print(f'  OK  the {len(TEMPLATE_FILES)} templates name {c["controlId"]} for Terms, every placeholder a '
                  f'live control; {TEMPLATE_GENERAL} is the general one')
    found = print_problems()
    problems += found
    if not found:
        print(f"  OK  System Print {PRINT_NAME!r} {hap.ids()['prints'][PRINT_KEY]} on {WORKSHEET}: Word, "
              f'{TEMPLATE_GENERAL}')
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
            # Not BUTTON_OWNED: a button that has run leaves those different from the seed by design.
            left = differences(f, read_record(ws(), rowid), seed_compared(order_want(f, o, index, gaps)))
            if left:
                problems.append(f"{o['name']} ({number}): {json.dumps(left, ensure_ascii=False, default=str)} "
                                '— run `seed`')
        report_gaps(gaps)
    if problems:
        print('  check: ' + '\n         '.join(problems))
        sys.exit(1)
    print(f'  check: OK — {len(RULES)} rules, the retired five, Expiration, three roll-ups at {MONEY_DOT} '
          f'decimals, the {len(SUBTABLE_COLUMNS)} subtable columns, {INVOICING_STATUS} at '
          f'{READ_ONLY_PERMISSION}, the {len(PART1)} controls of §6b at '
          f'{[PART1_PERMISSION[n] for n in PART1]}, '
          f'{len(VIEW_ROWS)} views returning exactly the orders their filters name, the {len(BUTTONS) + 2} buttons of '
          f"§13 and §14 with their workflows, the owner's {OWNERS_BUTTON!r} rewired "
          f'(§16, published, never pressed), '
          f'the {DISCOUNT_PRODUCT} product and variant, the {len(DISCOUNT_FIELDS)} discount fields, {TERMS}, the '
          f'{len(TEMPLATE_FILES)} templates and System Print {PRINT_NAME!r}, §17: {SIGNING_LINK}, {SIGN!r} and '
          f'{SIGNED_WF!r}, and §18: {INCOTERM} and {INCOTERM_LOCATION}')


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
         'wipe': step_wipe, 'seed': step_seed, 'figures': step_figures, 'buttons': step_buttons,
         'selfcheck': step_selfcheck, 'selfdeliver': step_selfdeliver,
         'discountproduct': step_discountproduct, 'discountline': step_discountline,
         'discountfields': step_discountfields, 'selfdiscount': step_selfdiscount,
         'terms': step_terms, 'templates': step_templates, 'print': step_print, 'selfprint': step_selfprint,
         'send': step_send, 'sendreach': step_sendreach, 'signlink': step_signlink, 'sign': step_sign,
         'signtest': step_signtest, 'selfsign': step_selfsign,
         'incoterm': step_incoterm, 'selfincoterm': step_selfincoterm,
         'check': step_check, 'show': step_show}

if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] not in STEPS:
        sys.exit(f'usage: {sys.argv[0]} {{{" | ".join(STEPS)}}}')
    print(f'{WORKSHEET}: {sys.argv[1]}')
    STEPS[sys.argv[1]]()
