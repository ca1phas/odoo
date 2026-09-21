#!/usr/bin/env python3
"""Business rules for the Orders worksheet (Odoo `sale.order`) in ERP Master — and, deliberately, nothing else.

    ~/.hap-venv/bin/python nocoly/build/orders.py rules    # 1. the three interaction rules (upsert by name)
    ~/.hap-venv/bin/python nocoly/build/orders.py retire   # 2. disable the hand-built rules those three supersede
    ~/.hap-venv/bin/python nocoly/build/orders.py expiry   # 3. clear `required` on Expiration, one version-pinned save
    ~/.hap-venv/bin/python nocoly/build/orders.py check    # read rules and Expiration back and report drift
    ~/.hap-venv/bin/python nocoly/build/orders.py show     # the live controls and rules

**There is no `fields`, `layout`, `views`, `buttons`, `seed` or `records` step, and there must not be one.**
The owner is building Orders **by hand in the browser** — on 21 Sep 2026 they added Delivery Date, Delivery
Status and Locked and six business rules between 11:51 and 12:23, while this script was being written. HAP has
no per-field endpoint: a layout step is a full `SaveWorksheetControls`, which replaces the whole control set and
would revert whatever the owner had typed since the read. `products.py` carries the same trap and the same
warning in its `perms` docstring — its `layout` step predates another administrator's changes and running it
would undo them. So this builder owns the **rules**, and the one field flag the owner explicitly approved.

Requirements: nocoly/worksheets/16-orders.md. Generic helpers: common.py.
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
    'Order Lines': '6ab0a592e43d174ab3752fe5',
    'Status': '6ab0a847e54d2a34fa4e7b96',
    'Delivery Date': '6ab0a9dabd43f55762c78047',
    'Delivery Status': '6ab0a9dabd43f55762c78048',
    'Locked': '6ab0af4f805aef703286d570',
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

# Odoo's `readonly="state in ['cancel','sale']"` covers eight fields on `sale.order`'s form. Five of them —
# **Pricelist, Tax mode, Online signature, Online payment and Prepayment %** — are not on the worksheet yet
# (16-orders.md §2 rows 10, 11, 17, 18, 19), so the rule is built with the three that are. Add them to this
# tuple the day the owner adds the controls; nothing else about the rule changes.
CONFIRMED_FIELDS = ('Customer', 'Expiration', 'Quotation/Order Date')
CONFIRMED_MISSING = ('Pricelist', 'Tax mode', 'Online signature', 'Online payment', 'Prepayment %')

LOCKED_FIELDS = ('Invoice Address', 'Delivery Address', 'Delivery Date')


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
    ]


def step_rules():
    """The three interaction rules, upserted by name so a re-run updates rather than duplicates."""
    f = guard()
    C.upsert_rules(ws(), rule_specs(f), 'orders_rules_pre_rules')
    live = {r['name']: r for r in hap.listing('worksheet', 'rules', ws())}
    for name in (RULE_EXPIRATION, RULE_CONFIRMED, RULE_LOCKED):
        if name not in live:
            sys.exit(f'rule {name!r} did not come back from the worksheet')
        C.remember('rules', KEY + name, live[name]['ruleId'])
    print(f'  {len(live)} rules on {WORKSHEET}; the three above are this builder\'s')
    return True


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


def control_state(c):
    """A control's attributes, with its JSON-valued `advancedSetting` keys **parsed** rather than compared as
    strings — the server re-serialises several of them on every read (BUILDING.md; `accounts.control_state`).

    A 子表's `relationControls` is the child worksheet's whole control snapshot, which the server also reshuffles,
    so it is reduced to the child controls' identity rather than compared byte for byte."""
    out = {k: c.get(k) for k in SIGNATURE}
    settings = dict(c.get('advancedSetting') or {})
    for key, value in settings.items():
        if key in JSON_KEYS and isinstance(value, str) and value:
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
    """Read the three rules, the retired ones and Expiration back, and report every drift."""
    f = guard()
    names = {c['controlId']: c['controlName'] for c in hap.controls(ws())}
    live = {r['name']: r for r in hap.listing('worksheet', 'rules', ws())}
    problems = []
    for name, kind, filters, items, _opts in rule_specs(f):
        r = live.get(name)
        if r is None:
            problems.append(f'rule {name!r} missing')
            continue
        want = (kind, False, condition_state(filters, names),
                [(i['type'], [names.get(c['controlId'], c['controlId']) for c in i['controls']]) for i in items])
        got = (r['type'], r['disabled'], condition_state(r['filters'], names),
               [(i['type'], [names.get(c['controlId'], c['controlId']) for c in i['controls']])
                for i in r['ruleItems']])
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
        if name not in (RULE_EXPIRATION, RULE_CONFIRMED, RULE_LOCKED) \
                and r['ruleId'] not in SUPERSEDED and r['ruleId'] not in KEPT:
            print(f"  new       {r['ruleId']} {name!r} — the owner's, not this builder's")
    if f[EXPIRATION].get('required'):
        problems.append(f'{EXPIRATION} is required again, and {RULE_EXPIRATION!r} hides it: '
                        'a hidden required field cannot be filled and the form cannot be saved — run `expiry`')
    else:
        print(f'  OK  {EXPIRATION} is not required (Odoo does not require validity_date)')
    # The line-level rule of 16-orders.md is not built and cannot be: see `step_show`.
    print(f'  not built: the line-level rule (Section / Subsection / Note carries no figures) — '
          f"the Order Lines child table is unreadable, see `show`")
    print(f'  not built: {CONFIRMED_MISSING[1]!r} read-only when Status is not Quotation, and '
          f"'Prepayment %' hidden when 'Online payment' is unticked — neither control exists")
    if problems:
        print('  check: ' + '\n         '.join(problems))
        sys.exit(1)
    print('  check: OK — three rules, the retired five, and Expiration')


def step_show():
    """The live controls and rules, and what the Order Lines child table answers."""
    guard()
    C.show(ws())
    for r in hap.listing('worksheet', 'rules', ws()):
        print(f"  {'disabled' if r['disabled'] else 'enabled ':<9} {r['ruleId']} {r['name']}")
    # Odoo's `sale_order_line_non_accountable_null_fields` is 16-orders.md's third hide rule, and its targets live
    # on the Order Lines subtable's child worksheet. That worksheet cannot be reached: its id was minted by the
    # subtable control itself (…fe5 the control, …fe6 the back-relation, …fe7 the worksheet, all in one second),
    # which is HAP's `child_fields` 子表 — a **hidden child table** with no entry in the app's sections. Both
    # `worksheet fields` (V3) and the main site's own `GetWorksheetControls` answer *Insufficient permissions*
    # for it, while the same calls read Invoice Lines — a *mounted* worksheet — fine. It is structural, not a
    # profile or a role-debug session (`app role list` answers normally). The only readable view of the child is
    # the parent control's `relationControls` snapshot, printed here.
    sub = next(c for c in hap.controls(ws()) if c['controlId'] == CONTROLS['Order Lines'])
    print(f"  Order Lines -> child worksheet {sub['dataSource']} (hidden child table), "
          f"{len(sub.get('relationControls') or [])} columns:")
    for r in sub.get('relationControls') or []:
        print(f"    t{r['type']:<3} {r['controlName']:<24} {r['controlId']}")


STEPS = {'rules': step_rules, 'retire': step_retire, 'expiry': step_expiry,
         'check': step_check, 'show': step_show}

if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] not in STEPS:
        sys.exit(f'usage: {sys.argv[0]} {{{" | ".join(STEPS)}}}')
    print(f'{WORKSHEET}: {sys.argv[1]}')
    STEPS[sys.argv[1]]()
