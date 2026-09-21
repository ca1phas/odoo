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
    ~/.hap-venv/bin/python nocoly/build/orders.py check    # read rules, Expiration and the roll-ups back and
                                                           #    report drift
    ~/.hap-venv/bin/python nocoly/build/orders.py show     # the live controls and rules

**There is no `fields`, `layout`, `views`, `buttons`, `seed` or `records` step, and there must not be one.**
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
import json, sys

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
    ]


RULES = (RULE_EXPIRATION, RULE_CONFIRMED, RULE_LOCKED, RULE_TAX_MODE)


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
    for name in RULES:
        if name not in live:
            sys.exit(f'rule {name!r} did not come back from the worksheet')
        C.remember('rules', KEY + name, live[name]['ruleId'])
    print(f'  {len(live)} rules on {WORKSHEET}; the four above are this builder\'s '
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
JSON_KEYS = ('filters', 'filterregex', 'controlssorts', 'customShowControls', 'defsource', 'defaultfunc',
             'uniquecontrols', 'rowsummary')


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
    unknown = sorted(set(f) - set(CONTROLS))
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
    if problems:
        print('  check: ' + '\n         '.join(problems))
        sys.exit(1)
    print(f'  check: OK — {len(RULES)} rules, the retired five, Expiration, three roll-ups at {MONEY_DOT} '
          f'decimals and the {len(SUBTABLE_COLUMNS)} subtable columns')


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
         'dots': step_dots, 'check': step_check, 'show': step_show}

if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] not in STEPS:
        sys.exit(f'usage: {sys.argv[0]} {{{" | ".join(STEPS)}}}')
    print(f'{WORKSHEET}: {sys.argv[1]}')
    STEPS[sys.argv[1]]()
