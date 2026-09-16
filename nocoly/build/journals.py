#!/usr/bin/env python3
"""Build the Journals worksheet (Odoo account.journal, as on casimir.odoo.com saas~19.4) in ERP Master.

Teh Li Wei built the first cut on 15 Sep 2026 — the worksheet, six controls and the two views. This script keeps
his control ids, aliases and option keys and closes the gaps against the casimir reference: Sequence (which he
removed), the two dedicated-sequence checkboxes, Odoo's two notebook tabs with a heading and a remark block each,
Odoo's help and placeholders, the Sequence Prefix limit and uniqueness, the five rules, Archive / Unarchive and the
seven journals. Requirements: nocoly/worksheets/05-journals.md. Generic helpers: common.py. Run from the repo root
with the CLI's interpreter:

    ~/.hap-venv/bin/python nocoly/build/journals.py layout     # 1. Sequence, the two dedicated sequences, the tabs
                                                               #    Journal Entries and Advanced Settings, each with a
                                                               #    divider heading and a remark block; places, tabs,
                                                               #    help, hints, required, Prefix ≤ 5 and unique
    ~/.hap-venv/bin/python nocoly/build/journals.py rules      # 2. what Type shows, requires and hides (upsert by name)
    ~/.hap-venv/bin/python nocoly/build/journals.py views      # 3. Journals and Archived: columns, sort, Type quick filter
    ~/.hap-venv/bin/python nocoly/build/journals.py buttons    # 4. Archive / Unarchive and their one-step workflows
    ~/.hap-venv/bin/python nocoly/build/journals.py draftguard # 4b. Odoo's refusal to archive a journal that still
                                                               #    has draft entries, into the Archive workflow
    ~/.hap-venv/bin/python nocoly/build/journals.py seed       # 5. the 7 journals of the reference (upsert by Sequence
                                                               #    Prefix), then verify
    ~/.hap-venv/bin/python nocoly/build/journals.py all        # every step above, then check

    ~/.hap-venv/bin/python nocoly/build/journals.py verify     # compare the live journals with the reference
    ~/.hap-venv/bin/python nocoly/build/journals.py check      # read controls, tabs, rules, views and buttons back
                                                               #    against this spec
    ~/.hap-venv/bin/python nocoly/build/journals.py selfcheck  # the API writes the worksheet must refuse, and both buttons,
                                                               #    on TEST Journal (TSTJ), which is left active
    ~/.hap-venv/bin/python nocoly/build/journals.py draftcheck # the archive guard both ways: TEST draft guard (TSTDG),
                                                               #    which holds a TEST draft entry, must refuse to
                                                               #    archive; TEST Journal, which holds none, must not
    ~/.hap-venv/bin/python nocoly/build/journals.py order      # each view's records, in the order the view sorts them
    ~/.hap-venv/bin/python nocoly/build/journals.py journal "Bank"   # stored values by Journal Name, hidden fields included
    ~/.hap-venv/bin/python nocoly/build/journals.py untouched  # Contacts, Units & Packagings, Products and Product
                                                               #    Variants: control count and digest, compared by id
    ~/.hap-venv/bin/python nocoly/build/journals.py show       # the live control list

Every step reads the live worksheet first and is safe to re-run; a second run writes nothing.

Profile. hap-cli 0.8.31 picks the account as --profile > $HAP_PROFILE > the active profile, so this script passes
none and runs on any machine whose active profile reaches ERP Master; name another one in the environment:

    HAP_PROFILE=fbmy-nocoly ~/.hap-venv/bin/python nocoly/build/journals.py check

Every write step stops unless the profile reaches ERP Master › Invoicing › Journals and the worksheet holds only
the first build plus this script's own work. Worksheet 06 Invoices is Teh Li Wei's; nothing here touches it.
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
WORKSHEET = hap.ids()['worksheets']['Journals']
KEY = 'Journals: '                                # ids.json key prefix for everything this worksheet owns
HERE = Path(__file__).resolve().parent
REFERENCE = HERE.parent / 'reference' / 'odoo-19.4' / 'account.journal.md'
OTHERS = ('Contacts', 'Units & Packagings', 'Products', 'Product Variants')   # must stay untouched


def option(key, value, index, color, checked=False):
    return {'key': key, 'value': value, 'isDeleted': False, 'index': index, 'checked': checked, 'color': color}


# The first build's option keys. Records point at them, so they are never re-minted.
TYPE_OPTIONS = [
    option('1eb997f4-66ba-4ee1-b310-2cc245807aa1', 'Sales', 1, '#C9E6FC'),
    option('3649719d-d164-49bc-ac0e-026a83917942', 'Purchase', 2, '#C3F2F2'),
    option('97f495e4-79bf-405a-9f01-93e53b3c7f2c', 'Cash', 3, '#C2F1D2'),
    option('ab62f2c4-8e86-4028-8f28-c8700eef77e8', 'Bank', 4, '#FFE7B1'),
    option('b3fa50b5-9807-456d-ac71-bb2176b545bb', 'Credit Card', 5, '#FBD2BF'),
    option('f342c982-c1d1-40c1-8bd8-308e0f77a94a', 'Miscellaneous', 6, '#D2D2D2'),
]
COMMUNICATION_TYPE_OPTIONS = [
    option('46c0154b-ad58-4c28-9ff0-896972093807', 'Based on Customer', 1, '#C9E6FC'),
    option('3758ebd7-5b28-41ec-964d-9a3747316617', 'Based on Invoice', 2, '#C3F2F2', True),
]
COMMUNICATION_STANDARD_OPTIONS = [
    option('09f530e3-f017-46fe-8a4f-2ba6fb5e6cb8', 'Full Reference (INV/2024/00001)', 1, '#C9E6FC', True),
    option('b7cc8520-1f95-455b-a0b7-1be84a127c27', 'European (RF83INV202400001)', 2, '#C3F2F2'),
    option('8ca4b321-5330-4f8f-be61-a4012450214b', 'Numbers only (202400001)', 3, '#C2F1D2'),
]
OPTIONS = {'Type': TYPE_OPTIONS, 'Communication Type': COMMUNICATION_TYPE_OPTIONS,
           'Communication Standard': COMMUNICATION_STANDARD_OPTIONS}
DEFAULT_OPTION = {name: next(o['key'] for o in opts if o['checked'])          # Odoo default_get
                  for name, opts in OPTIONS.items() if any(o['checked'] for o in opts)}

# Teh Li Wei's controls as they stand live (he removed his Sequence field at 17:27 on 15 Sep 2026, so this
# script adds it back with a new id). Kept by every step here.
FIRST_BUILD = {
    '6aa8f6c81204328eb1af1676': ('Journal Name', 2),
    '6aa8f6c81204328eb1af1677': ('Sequence Prefix', 2),
    '6aa8f6c81204328eb1af1678': ('Type', 11),
    '6aa8f6c81204328eb1af1679': ('Communication Type', 11),
    '6aa8f6c81204328eb1af167a': ('Communication Standard', 11),
    '6aa8f6c81204328eb1af167b': ('Active', 36),
}

# ── 1 · the form ────────────────────────────────────────────────────────────

# Odoo saas~19.4 view_account_journal_form on HAP's 12-column grid: Journal Name; Type · Sequence Prefix; then
# Odoo's two notebook pages as HAP tabs — Journal Entries (page name="bank_account") and Advanced Settings. Each
# tab also carries a remark block naming what Odoo shows there and which bundle or table brings it (owner,
# 16 Sep 2026). Sequence is on no Odoo form: it is the list's drag handle, and a HAP table has none (its help
# says so). Active is hidden and belongs to no tab.
JOURNAL_ENTRIES, ADVANCED_SETTINGS = 'Journal Entries', 'Advanced Settings'
REMARK_ENTRIES = "Also on Odoo's Journal Entries tab"       # type 22: the heading only (its desc renders nowhere)
REMARK_ADVANCED = "Also on Odoo's Advanced Settings tab"
NOTE_ENTRIES, NOTE_ADVANCED = 'Journal Entries note', 'Advanced Settings note'   # type 10010: the text itself
TABS = (JOURNAL_ENTRIES, ADVANCED_SETTINGS)
PLACE = {  # name -> (row, col, size, tab)
    'Journal Name': (0, 0, 12, None),
    'Type': (1, 0, 6, None), 'Sequence Prefix': (1, 1, 6, None),
    'Sequence': (2, 0, 6, None),
    JOURNAL_ENTRIES: (3, 0, 12, None),
    'Dedicated Credit Note Sequence': (4, 0, 6, JOURNAL_ENTRIES),
    'Dedicated Payment Sequence': (4, 1, 6, JOURNAL_ENTRIES),
    REMARK_ENTRIES: (5, 0, 12, JOURNAL_ENTRIES),
    NOTE_ENTRIES: (6, 0, 12, JOURNAL_ENTRIES),
    ADVANCED_SETTINGS: (7, 0, 12, None),
    'Communication Type': (8, 0, 6, ADVANCED_SETTINGS),
    'Communication Standard': (8, 1, 6, ADVANCED_SETTINGS),
    REMARK_ADVANCED: (9, 0, 12, ADVANCED_SETTINGS),
    NOTE_ADVANCED: (10, 0, 12, ADVANCED_SETTINGS),
    'Active': (11, 0, 6, None),
}
# What each tab's remark block says, as the HTML the block stores. A remark block renders this; a divider's
# description renders nowhere, so the dividers keep their heading and nothing else.
HTML = {
    NOTE_ENTRIES: "<p><strong>Also on Odoo's Journal Entries tab:</strong> the Invoice report, and — on Bank and "
                  'Credit Card journals — the Bank Account Number, BIC and Bank Feeds. Odoo also lists this '
                  "journal's payment method lines on its Incoming and Outgoing Payments tabs.</p>"
                  '<p>The bank fields come with bank accounts, the report with the invoice report templates, and '
                  'the payment method lines with the Payments bundle.</p>',
    NOTE_ADVANCED: "<p><strong>Also on Odoo's Advanced Settings tab:</strong> Automation (Self Billing), Emails "
                   '(Email Alias and Send Copy To) and Electronic Data Interchange.</p>'
                   '<p>Self Billing and the EDI settings come with e-invoicing; the alias needs a mail alias and '
                   'incoming mail.</p>',
}
HINTS = {  # Odoo's placeholders on this form; every other field's placeholder is cleared
    'Journal Name': 'e.g. Customer Invoices',     # Odoo computes name_placeholder from Type
    'Sequence Prefix': 'e.g. INV',
}
DESC = {  # Odoo field help, verbatim (addons/account/models/account_journal.py)
    'Type': "Select 'Sale' for customer invoices journals.\n"
            "Select 'Purchase' for vendor bills journals.\n"
            "Select 'Cash', 'Bank' or 'Credit Card' for journals that are used in customer or vendor payments.\n"
            "Select 'General' for miscellaneous operations journals.",
    'Sequence Prefix': 'Shorter name used for display. The journal entries of this journal will also be named '
                       'using this prefix by default.',
    'Sequence': 'Used to order Journals in the dashboard view.\n'
                'A HAP table has no drag handle, so a journal is moved up or down the list by changing this '
                'number. Odoo gives every new journal 10.',
    'Communication Type': 'You can set here the default communication that will appear on customer invoices, once '
                          'validated, to help the customer to refer to that particular invoice when making the '
                          'payment.',
    'Communication Standard': 'You can choose different models for each type of reference. The default one is the '
                              'Odoo reference.',
    'Dedicated Credit Note Sequence': "Check this box if you don't want to share the same sequence for invoices "
                                      'and credit notes made from this journal',
    'Dedicated Payment Sequence': "Check this box if you don't want to share the same sequence on payments and "
                                  'bank transactions posted on this journal',
    'Active': 'Set active to false to hide the Journal without removing it.',
    # The two dividers carry no description: HAP renders a type-22 divider's `desc` nowhere at all — not even as a
    # tooltip (UI test, 16 Sep 2026). Their text lives in the remark blocks below them, in HTML.
}
# Odoo: name and code required always, type required; the two communication fields are required on the model but
# only ever shown for Sales, so here a rule requires them instead — a hidden required field can never be filled.
REQUIRED = {'Journal Name', 'Type', 'Sequence Prefix'}
HIDDEN = {'Active'}
UNIQUE = {'Sequence Prefix'}                      # SQL account_journal_code_company_uniq
CODE_SIZE = 5                                     # Odoo code = fields.Char(size=5)
ADVANCED = {  # advancedSetting keys this script owns
    'Sequence Prefix': {'checkrange': '1', 'min': '1', 'max': str(CODE_SIZE)},
    'Sequence': {'defsource': C.static_default(10)},
    'Dedicated Credit Note Sequence': {'defsource': C.static_default(0)},
    'Dedicated Payment Sequence': {'defsource': C.static_default(0)},
    'Active': {'defsource': C.static_default(1)},
    'Communication Type': {'defsource': C.static_default(DEFAULT_OPTION['Communication Type'])},
    'Communication Standard': {'defsource': C.static_default(DEFAULT_OPTION['Communication Standard'])},
    NOTE_ENTRIES: {'hidetitle': '1'},              # the remark block's controlName is an internal label only
    NOTE_ADVANCED: {'hidetitle': '1'},
}
DIVIDER = 22                                      # HAP's 分段 divider (hap-cli "SPLIT_LINE"): a heading, no more —
                                                  # whatever is put in its `desc` is never rendered
NOTE = 10010                                      # HAP's remark block: HTML in `dataSource`, `hidetitle` "1", and
                                                  # the controlName only an internal label. hap-cli has no builder
                                                  # for it, so its JSON is written out in full below
NEW = {  # controls this script adds: (type, alias, extra control keys)
    'Sequence': ('NUMBER', 'sequence', {'dot': 0}),
    'Dedicated Credit Note Sequence': ('SWITCH', 'refund_sequence', {}),
    'Dedicated Payment Sequence': ('SWITCH', 'payment_sequence', {}),
    JOURNAL_ENTRIES: ('SECTION', '', {}),
    ADVANCED_SETTINGS: ('SECTION', '', {}),
    REMARK_ENTRIES: ('SPLIT_LINE', '', {}),
    REMARK_ADVANCED: ('SPLIT_LINE', '', {}),
    NOTE_ENTRIES: (NOTE, '', {}),
    NOTE_ADVANCED: (NOTE, '', {}),
}


def new_control(name):
    """A control to add. The remark block is sent as raw JSON — `add-fields` mints its id, as it does for the
    controls hap-cli can build."""
    kind, alias, extra = NEW[name]
    row, col, size, _ = PLACE[name]
    if kind == NOTE:
        return {'controlName': name, 'type': NOTE, 'row': row, 'col': col, 'size': size, 'alias': alias,
                'dataSource': HTML[name], 'advancedSetting': {'hidetitle': '1'}, 'desc': '', 'hint': '',
                'required': False, 'unique': False}
    return C.control(kind, name, (row, col, size), alias=alias, hint=HINTS.get(name, ''), desc=DESC.get(name, ''),
                     hidden=name in HIDDEN, required=name in REQUIRED, unique=name in UNIQUE,
                     advanced_setting=dict(ADVANCED.get(name, {}), showtype='0') if kind == 'SWITCH'
                     else ADVANCED.get(name) or None, extra=extra or None)


def desired(c, tab_ids):
    """The attributes `layout` owns on control c, as they should read back. A tab owns its place only; a divider
    its place and an empty description; a remark block its place and its HTML; a field all of it."""
    name = c['controlName']
    row, col, size, tab = PLACE[name]
    want = {'row': row, 'col': col, 'size': size, 'sectionId': tab_ids.get(tab, '') if tab else ''}
    if c['type'] == C.TAB:
        return want
    if c['type'] == NOTE:
        want['dataSource'] = HTML[name]
        return want
    want['desc'] = DESC.get(name, '')
    if c['type'] == DIVIDER:
        return want
    want.update(hint=HINTS.get(name, ''), required=name in REQUIRED, unique=name in UNIQUE,
                fieldPermission='011' if name in HIDDEN else '111')
    return want


def layout_differences(ctrls):
    tab_ids = {c['controlName']: c['controlId'] for c in ctrls if c['type'] == C.TAB}
    out = {}
    for c in ctrls:
        if c['controlName'] not in PLACE:
            continue
        diff = {k: (c.get(k), v) for k, v in desired(c, tab_ids).items() if c.get(k) != v}
        adv = c.get('advancedSetting') or {}
        diff.update({f'advancedSetting.{k}': (adv.get(k), v)
                     for k, v in ADVANCED.get(c['controlName'], {}).items() if adv.get(k) != v})
        if diff:
            out[c['controlName']] = diff
    return out


# ── the other worksheets, untouched ─────────────────────────────────────────

SIGNATURE = ('controlName', 'type', 'alias', 'row', 'col', 'size', 'sectionId', 'required', 'attribute', 'unique',
             'fieldPermission', 'dataSource', 'sourceControlId', 'showControls', 'advancedSetting', 'desc', 'hint')


def signatures():
    """Every other Phase 1 worksheet's controls by id (a full save elsewhere can reorder their listing)."""
    return {name: sorted(json.dumps([c['controlId']] + [c.get(k) for k in SIGNATURE], sort_keys=True,
                                    ensure_ascii=False)
                         for c in hap.controls(hap.ids()['worksheets'][name])) for name in OTHERS}


def check_untouched(before):
    after = signatures()
    for name in before:
        if after[name] != before[name]:
            sys.exit(f'{name} controls changed: {sorted(set(after[name]) ^ set(before[name]))}')
    print('  untouched: ' + ', '.join(f'{n} ({len(after[n])})' for n in after))


def step_untouched():
    """Control count and digest of every other Phase 1 worksheet — run before and after a build."""
    for name, sig in signatures().items():
        digest = hashlib.sha256(''.join(sig).encode()).hexdigest()[:16]
        print(f'  {name:<20} {len(sig):>2} controls  sha256:{digest}')


def save_controls(ctrls):
    """A full update-fields save, proving the other worksheets' controls unchanged."""
    before = signatures()
    hap.run('worksheet', 'update-fields', WORKSHEET, '--controls', json.dumps(ctrls, ensure_ascii=False))
    check_untouched(before)


# ── guard ───────────────────────────────────────────────────────────────────

TEST_NAME = 'TEST Journal'
TEST_CODE = 'TSTJ'


def guard():
    """Stop unless the profile reaches ERP Master › Invoicing › Journals and the worksheet holds only the first
    build plus this script's work. Returns the live controls."""
    who = hap.run('auth', 'whoami')
    app = hap.run('app', 'info', '-a', APP).get('data', {})
    section = next((s for s in app.get('sections', []) if any(i['id'] == WORKSHEET for i in s['items'])), None)
    if app.get('name') != 'ERP Master' or not section or section['name'] != 'Invoicing':
        sys.exit(f"profile {who.get('profile')!r} does not reach ERP Master › Invoicing › Journals")
    problems, ctrls = [], hap.controls(WORKSHEET)
    by_id = {c['controlId']: c for c in ctrls}
    for cid, (name, kind) in FIRST_BUILD.items():
        c = by_id.get(cid)
        if not c or (c['controlName'], c['type']) != (name, kind):
            problems.append(f"first-build control {cid} ({name}) is {c and (c['controlName'], c['type'])}")
    problems += [f"unknown control {c['controlName']!r} ({c['controlId']})" for c in ctrls
                 if c['controlName'] not in PLACE]
    names = hap.by_name(ctrls)
    if len(names) != len(ctrls):                   # a tab and a field may share a name; here none may
        problems.append(f'two controls share a name: {sorted(c["controlName"] for c in ctrls)}')
    for name, opts in OPTIONS.items():
        live = [(o['key'], o['value']) for o in names.get(name, {}).get('options', []) if not o.get('isDeleted')]
        if live != [(o['key'], o['value']) for o in opts]:
            problems.append(f'{name} options changed: {live}')
    rules = {r['name'] for r in hap.listing('worksheet', 'rules', WORKSHEET)}
    problems += [f'unknown rule {n!r}' for n in rules - set(RULES)]
    buttons = {b['name'] for b in hap.listing('worksheet', 'custom-actions', WORKSHEET)}
    problems += [f'unknown button {n!r}' for n in buttons - {'Archive', 'Unarchive'}]
    views = {v['name'] for v in hap.listing('worksheet', 'view', 'list', WORKSHEET, '-a', APP)}
    problems += [f'unknown view {n!r}' for n in views - {'Journals', 'Archived'}]
    if 'Sequence Prefix' in names:
        title, prefix = names['Journal Name']['controlId'], names['Sequence Prefix']['controlId']
        codes = {r.get(prefix): r.get(title) for r in C.records(WORKSHEET, APP)}
        problems += [f'unknown record {n!r} ({code})' for code, n in codes.items()
                     if code not in reference_table() and not str(n).startswith('TEST')]
    if problems:
        sys.exit('Journals differs from the first build plus this script\'s work — stopping:\n  '
                 + '\n  '.join(problems))
    print(f"  guard: profile {os.environ.get('HAP_PROFILE') or who.get('profile')!r}, ERP Master › Invoicing › "
          f"Journals, {len(ctrls)} controls, {len(rules)} rules, {len(buttons)} buttons, views {sorted(views)}")
    return ctrls


def step_layout():
    """Add what is missing — Sequence, the two dedicated sequences, the two tabs and their remark blocks — then
    set every control's place and tab, hint, help, required, visibility, default, and Sequence Prefix's
    5-character limit and No duplicates. The tabs are saved first so the fields can point at their ids."""
    ctrls = guard()
    print('  backup:', hap.backup('journals_controls_pre_layout', ctrls))
    missing = [n for n in NEW if n not in {c['controlName'] for c in ctrls}]
    if missing:
        before = signatures()
        C.add_fields(WORKSHEET, [new_control(n) for n in missing])
        check_untouched(before)
        ctrls = hap.controls(WORKSHEET)
        print(f'  added: {missing}')
    changed = layout_differences(ctrls)
    if changed:
        tab_ids = {c['controlName']: c['controlId'] for c in ctrls if c['type'] == C.TAB}
        for c in ctrls:
            if c['controlName'] in changed:
                c.update(desired(c, tab_ids))
                c['advancedSetting'] = {**(c.get('advancedSetting') or {}), **ADVANCED.get(c['controlName'], {})}
        save_controls(ctrls)
        print('  updated:', json.dumps(changed, ensure_ascii=False))
    else:
        print('  layout already as specified; nothing saved')
    ctrls = hap.controls(WORKSHEET)
    left = layout_differences(ctrls)
    if left:
        sys.exit(f'layout read back with differences: {json.dumps(left, ensure_ascii=False)}')
    lost = [f'{cid} ({name})' for cid, (name, _) in FIRST_BUILD.items()
            if cid not in {c['controlId'] for c in ctrls}]
    if lost:
        sys.exit(f'first-build control ids missing after the save: {lost}')
    for c in ctrls:
        C.remember('controls', KEY + c['controlName'], c['controlId'])
    C.show(WORKSHEET)


# ── 2 · rules ───────────────────────────────────────────────────────────────

RULE_COMMUNICATIONS = 'Payment Communications only for Sales'
RULE_COMMUNICATIONS_REQ = 'Payment Communications are required for Sales'
RULE_CREDIT_NOTE = 'Dedicated Credit Note Sequence only for Sales and Purchase'
RULE_PAYMENT = 'Dedicated Payment Sequence only for Bank, Cash and Credit Card'
RULE_ADVANCED_TAB = 'Advanced Settings hidden for Bank and Cash journals'
# rule name -> (Type options, controls it acts on, rule item type). A rule applies its action while its condition
# holds and reverses it when it does not, so every show rule here also hides its fields while Type is empty — and
# the one hide rule shows its tab for every other type, and on a new record, which is what Odoo's `invisible` does.
RULES = {
    # <group string="Payment Communications" invisible="type != 'sale'">
    RULE_COMMUNICATIONS: (['Sales'], ['Communication Type', 'Communication Standard'], C.SHOW),
    # required=True on the model, but only reachable on a Sales journal's form
    RULE_COMMUNICATIONS_REQ: (['Sales'], ['Communication Type', 'Communication Standard'], C.REQUIRE),
    # <field name="refund_sequence" invisible="type not in ['sale', 'purchase']"/>
    RULE_CREDIT_NOTE: (['Sales', 'Purchase'], ['Dedicated Credit Note Sequence'], C.SHOW),
    # <field name="payment_sequence" invisible="type not in ('bank', 'cash', 'credit')"/>
    RULE_PAYMENT: (['Bank', 'Cash', 'Credit Card'], ['Dedicated Payment Sequence'], C.SHOW),
    # <page name="advanced_settings" invisible="type in ['bank', 'cash']"> — the tab control, contents and all.
    # Journal Entries has no such condition and stays visible for every type.
    RULE_ADVANCED_TAB: (['Bank', 'Cash'], [ADVANCED_SETTINGS], C.HIDE),
}


def type_is(f, labels):
    """Condition: Type is any of the labels (one filter, several option keys)."""
    keys = [o['key'] for o in f['Type']['options'] if o['value'] in labels]
    if len(keys) != len(labels):
        sys.exit(f'Type options {labels} not all found')
    return {'controlId': f['Type']['controlId'], 'dataType': f['Type']['type'], 'spliceType': 1,
            'filterType': C.EQ, 'value': '', 'values': keys, 'dynamicSource': [], 'isGroup': False}


def step_rules():
    ctrls = guard()
    f = hap.by_name(ctrls)                         # tabs included: one rule targets the Advanced Settings tab
    rules = [(name, C.INTERACTION, C.any_of([type_is(f, types)]),
              [C.item(kind, *[f[t] for t in targets])], {})
             for name, (types, targets, kind) in RULES.items()]
    C.upsert_rules(WORKSHEET, rules, 'journals_rules_pre_rules')
    for r in hap.listing('worksheet', 'rules', WORKSHEET):
        C.remember('rules', KEY + r['name'], r['ruleId'])


# ── 3 · views ───────────────────────────────────────────────────────────────

COLUMNS = ('Journal Name', 'Type', 'Sequence Prefix')
SORT = ('Sequence', 'Type', 'Sequence Prefix')                # Odoo _order "sequence, type, code"


def step_views():
    """Journals and Archived. Odoo's list is Journal Name · Type · Sequence Prefix (Default Account waits for
    Chart of Accounts); its search filters Sales · Purchases · Liquidity · Miscellaneous become one Type quick
    filter that takes several types at once (Liquidity = Cash + Bank + Credit Card)."""
    guard()
    f = C.fields(WORKSHEET)
    columns = [f[n]['controlId'] for n in COLUMNS]
    sort = C.sort_spec([f[n] for n in SORT])
    quick = [{'fieldId': f['Type']['controlId'], 'selectionType': 'multiple', 'displayType': 'dropdown'}]
    views = {
        'Journals': (dict(viewType='table', filter=C.switch_filter(f['Active'], 'eq'), tableFields=columns,
                          quickFilters=quick), sort, columns),
        'Archived': (dict(viewType='table', filter=C.switch_filter(f['Active'], 'ne'), tableFields=columns,
                          quickFilters=quick), sort, columns),      # Odoo's Archived search filter
    }
    for name, vid in C.upsert_views(WORKSHEET, APP, views, 'journals_views_pre_views',
                                    default_view='Journals').items():
        C.remember('views', KEY + name, vid)
    print('  order:', C.sort_views(WORKSHEET, APP, list(views)))
    C.print_views(WORKSHEET, APP)


# ── 4 · buttons ─────────────────────────────────────────────────────────────

MSG_ARCHIVE = 'Are you sure that you want to archive this record?'


def step_buttons():
    guard()
    active = C.fields(WORKSHEET)['Active']['controlId']
    when = lambda op: {'type': 'group', 'logic': 'AND', 'children': [
        {'type': 'condition', 'field': active, 'operator': op, 'value': ['1']}]}
    buttons = [  # Odoo ⚙ Actions › Archive / Unarchive, as on Contacts, Units & Packagings and Products
        ({'name': 'Archive', 'type': 'triggerWorkflow', 'enableWhen': when('eq'), 'isBatch': True,
          'confirm': True, 'confirmMsg': MSG_ARCHIVE, 'sureName': 'Archive', 'cancelName': 'Cancel'},
         [{'fieldId': active, 'value': '0'}], 'Archive the journal'),
        ({'name': 'Unarchive', 'type': 'triggerWorkflow', 'enableWhen': when('ne'), 'isBatch': True},
         [{'fieldId': active, 'value': '1'}], 'Unarchive the journal'),
    ]
    C.upsert_buttons(WORKSHEET, APP, buttons, KEY, 'journals_buttons_pre_buttons')
    for key in (KEY + 'Archive', KEY + 'Unarchive'):
        print(C.structure(hap.ids()['workflows'][key]))


# ── 4b · the archive guard ──────────────────────────────────────────────────
#
# Odoo `_check_auto_post_draft_entries` (addons/account/models/account_journal.py:686) refuses to archive a
# journal that still has draft entries. It waited for 06 Invoices, which is where a draft entry lives; the
# note was left in §1 *Not built now* and in DECISIONS.md on 16 Sep 2026.
#
# The check goes inside the Archive **button's** workflow, in front of the step that unchecks Active:
#
#     Trigger by button
#       → Draft entries in this journal          a 汇总 step (107): how many Invoices point at this journal
#                                                with Status Draft
#       → Does the journal still hold draft entries?
#            · Yes (one or more)  → Tell the user the journal cannot be archived   (站内通知)
#                                 → Stop — leave Active alone                      (中止流程, node type 30)
#            · No                 → (nothing)
#       → Archive the journal                    the first build's update step, untouched
#
# The abort node is what makes the guard work: a HAP branch **converges**, so an empty path and a path whose
# steps have run both carry on to whatever follows the gateway. Only 中止流程 stops the run before it reaches
# the update. Unarchive gets no such check — Odoo's constraint deliberately fires on archiving only
# (`self.filtered(lambda j: not j.active)`).

INVOICES = hap.ids()['worksheets']['Invoices']
ARCHIVE_STEP = 'Archive the journal'                # the first build's update step; never touched
COUNT_STEP = 'Draft entries in this journal'
DRAFT_BRANCH = 'Does the journal still hold draft entries?'
# The 站内通知 step's **name is part of what the user reads**: HAP renders the notification as
# 【<node name>】<message>. So the step is named as the heading Odoo's dialog does not have, rather than as
# what it does. 'Tell the user the journal cannot be archived' was the first cut's name and is renamed.
TELL_STEP = 'Cannot archive this journal'
TELL_STEP_WAS = 'Tell the user the journal cannot be archived'
STOP_STEP = 'Stop — leave Active alone'
GUARD_STEPS = (COUNT_STEP, DRAFT_BRANCH, TELL_STEP, STOP_STEP, ARCHIVE_STEP)   # the chain, in order

NUMBER_FX = 'number_fx_id'                          # a formula node's own numeric result
WORKSHEET_TOTAL = '107'                             # a workflow 汇总 step over a whole worksheet
ABORT, NOTICE, BRANCH_PATH = 30, 27, 2              # flowNodeType: 中止流程 · 站内通知 · a branch path
AT_LEAST_ONE, RELATION_EQ, IS_ANY_OF = '14', '33', '1'   # workflow conditionIds: 大于等于, a Relation, 是其中一个
NUMBER, DROPDOWN, RELATION, MEMBER = 6, 11, 29, 26

# The person who pressed the button. HAP's fixed 系统 node carries it as `triggeraid` ("Trigger", a member
# field); `kind: triggerUser` in hap-cli's DSL means something else here — it keys `uaid` off the trigger
# node, which on a button trigger the server reads back as **Last modifier**, the journal's last editor
# rather than whoever clicked Archive. `translate_accounts` passes a dict with no `kind` through untouched,
# so the recipient goes in wire-shaped.
SYSTEM_NODE = '5d39140d381d42d20db0c4da'
TRIGGER_USER = {'type': 6, 'entityId': SYSTEM_NODE, 'entityName': 'System', 'roleId': 'triggeraid',
                'roleTypeId': 0, 'roleName': 'Trigger', 'controlType': MEMBER, 'avatar': '', 'count': 0,
                'appType': 100, 'actionId': ''}

# Odoo's own text, verbatim (account_journal.py:694). Its three steps name Odoo's menus, not this app's —
# the equivalent here is Invoicing › Invoices, the Journal Entries view or the Status quick filter.
DRAFT_MESSAGE = ("You can not archive a journal containing draft journal entries.\n\n"
                 "To proceed:\n"
                 "1/ go to Accounting > Accounting > Journal Entries\n"
                 "2/ filter on this journal and on 'Unposted' entries\n"
                 "3/ select them all and post or delete them through the action menu")


def invoice_fields():
    return C.fields(INVOICES)


def draft_key(inv):
    return next(o['key'] for o in inv['Status']['options'] if o['value'] == 'Draft')


def guard_nodes(inv):
    """The count and the branch, for `batch-add` in front of the update step.

    The 汇总 step's filter is the journal's own rowid against the Invoices Journal field (conditionId 33, a
    Relation compared with another node's record) and Status is Draft. The server rewrites each condition's
    `nodeId` to the 汇总 node's own id, so what `left.node` says does not matter; what does is the
    comparison value, which is the **trigger** journal."""
    return [
        {'nodeAlias': 'drafts', 'nodeType': 'rollup', 'name': COUNT_STEP,
         'config': {'mode': 'worksheet', 'worksheet': INVOICES, 'aggregate': 'count',
                    'filter': {'logic': 'and', 'items': [
                        {'left': {'node': {'nodeAlias': 'trigger'}, 'fieldId': inv['Journal']['controlId'],
                                  '_filedTypeId': RELATION},
                         'op': RELATION_EQ,
                         'right': {'kind': 'field', 'node': {'nodeAlias': 'trigger'}, 'fieldId': 'rowid'}},
                        {'left': {'node': {'nodeAlias': 'trigger'}, 'fieldId': inv['Status']['controlId'],
                                  '_filedTypeId': DROPDOWN},
                         'op': IS_ANY_OF,
                         'right': {'kind': 'literal', 'values': [
                             {'key': draft_key(inv), 'value': 'Draft', 'isDeleted': False}]}},
                    ]}}},
        {'nodeAlias': 'draft_branch', 'nodeType': 'branch', 'name': DRAFT_BRANCH, 'config': {'paths': [
            {'alias': 'has_drafts', 'name': 'Yes', 'nodes': [
                {'nodeAlias': 'tell', 'nodeType': 'send_internal_notice', 'name': TELL_STEP,
                 'config': {'content': DRAFT_MESSAGE, 'accounts': [dict(TRIGGER_USER)]}}]},
            {'alias': 'no_drafts', 'name': 'No'}]}},
    ]


def at_least_one_draft(count_node):
    """The Yes path's condition: the 汇总 step's own numeric result is 1 or more."""
    return [[{'nodeId': count_node, 'filedId': NUMBER_FX, 'filedValue': COUNT_STEP, 'filedTypeId': NUMBER,
              'conditionId': AT_LEAST_ONE, 'sourceType': 0, 'conditionValues': [{'value': '1'}]}]]


def branch_paths(proc, gateway_id):
    """A gateway's two paths: the one that carries a step, then the fall-through."""
    paths = [n for n in proc['flowNodeMap'].values()
             if n.get('typeId') == BRANCH_PATH and n.get('prveId') == gateway_id]
    if len(paths) != 2:
        sys.exit(f'{DRAFT_BRANCH}: {len(paths)} paths, expected 2')
    yes = next((p for p in paths if p.get('nextId') not in (None, '', '99')), None)
    return yes or paths[0], next(p for p in paths if p['id'] != (yes or paths[0])['id'])


def save_path(pid, path, name, conditions):
    """A branch path's name and condition. `node get` returns them as `conditions`; `node save --type 2`
    wants `operateCondition`, and neither `batch-add` nor `node save -n` sets the name (BUILDING.md)."""
    got = hap.run('workflow', 'node', 'get', pid, path['id'])
    got = got.get('data', got)
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
    """The 站内通知 step's message and its one recipient, read back first. The node's `flowNodeMap` "106" —
    the in-app-message channel config the server needs or the node counts as incomplete — is sent back
    exactly as it came (BUILDING.md: without it publish fails with warningType 200)."""
    got = hap.run('workflow', 'node', 'get', pid, node['id'])
    got = got.get('data', got)
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
    back = hap.run('workflow', 'node', 'get', pid, node['id'])
    back = back.get('data', back)
    if back.get('sendContent') != content:
        sys.exit(f"{node['name']}: message read back {back.get('sendContent')!r}")
    return True


def nodes_by_name(pid):
    proc = hap.run('workflow', 'node', 'list', pid)
    return proc, {n['name']: n for n in proc['flowNodeMap'].values()}


def guard_differences():
    """The Archive workflow's draft-entry guard, read back: the chain, the count's filter, the branch
    condition, the message and its recipient, and that Unarchive still has no guard at all."""
    inv, problems = C.fields(INVOICES), []
    pid = hap.ids()['workflows'][KEY + 'Archive']
    proc, byname = nodes_by_name(pid)
    missing = [n for n in GUARD_STEPS if n not in byname]
    if missing:
        return [f'Archive workflow: {missing} missing']
    chain = {n: byname[n]['id'] for n in GUARD_STEPS}
    want_next = [(proc['startEventId'], chain[COUNT_STEP]), (chain[COUNT_STEP], chain[DRAFT_BRANCH]),
                 (chain[DRAFT_BRANCH], chain[ARCHIVE_STEP]), (chain[TELL_STEP], chain[STOP_STEP])]
    for node_id, nxt in want_next:
        if proc['flowNodeMap'][node_id].get('nextId') != nxt:
            problems.append(f"{proc['flowNodeMap'][node_id]['name']!r} runs into "
                            f"{proc['flowNodeMap'].get(proc['flowNodeMap'][node_id].get('nextId'), {}).get('name')!r}")
    if proc['flowNodeMap'][chain[STOP_STEP]].get('typeId') != ABORT:
        problems.append(f'{STOP_STEP!r} is node type {proc["flowNodeMap"][chain[STOP_STEP]].get("typeId")}, '
                        f'not {ABORT} (中止流程) — a branch converges, so only an abort stops the update')
    count = hap.run('workflow', 'node', 'get', pid, chain[COUNT_STEP])
    count = count.get('data', count)
    if (count.get('actionId'), count.get('appId'), count.get('reportControlId'), count.get('reportType')) != \
            (WORKSHEET_TOTAL, INVOICES, '', 0):
        problems.append(f"{COUNT_STEP}: actionId={count.get('actionId')} appId={count.get('appId')} "
                        f"reportControlId={count.get('reportControlId')!r} reportType={count.get('reportType')}")
    conds = [c for flt in count.get('filters') or [] for group in flt.get('conditions') or [] for c in group]
    got = [(c['filedId'], c['conditionId'],
            [v.get('controlId') or (v.get('value') or {}).get('value') for v in c['conditionValues']])
           for c in conds]
    want = [(inv['Journal']['controlId'], RELATION_EQ, ['rowid']),
            (inv['Status']['controlId'], IS_ANY_OF, ['Draft'])]
    if got != want:
        problems.append(f'{COUNT_STEP} filter {got}')
    if [v.get('nodeId') for c in conds for v in c['conditionValues']][:1] != [proc['startEventId']]:
        problems.append(f'{COUNT_STEP}: the Journal is not compared with the triggering journal')
    yes, no = branch_paths(proc, chain[DRAFT_BRANCH])
    for path, name, want_cond in ((yes, 'Yes', [(chain[COUNT_STEP], NUMBER_FX, AT_LEAST_ONE, ['1'])]),
                                  (no, 'No', [])):
        got = hap.run('workflow', 'node', 'get', pid, path['id'])
        got = got.get('data', got)
        live = [(c['nodeId'], c['filedId'], c['conditionId'], [v.get('value') for v in c['conditionValues']])
                for g in got.get('conditions') or [] for c in g]
        if path.get('name') != name or live != want_cond:
            problems.append(f'branch path {path.get("name")!r}: {live}')
    tell = hap.run('workflow', 'node', 'get', pid, chain[TELL_STEP])
    tell = tell.get('data', tell)
    if tell.get('sendContent') != DRAFT_MESSAGE:
        problems.append(f'{TELL_STEP}: message {tell.get("sendContent")!r}')
    who = [(a.get('type'), a.get('entityId'), a.get('roleId')) for a in tell.get('accounts') or []]
    if who != [(TRIGGER_USER['type'], TRIGGER_USER['entityId'], TRIGGER_USER['roleId'])]:
        problems.append(f'{TELL_STEP}: recipient {who}')
    unarchive, un_named = nodes_by_name(hap.ids()['workflows'][KEY + 'Unarchive'])
    steps = [n['name'] for n in unarchive['flowNodeMap'].values()
             if n.get('typeId') not in (None, 0, 100) and n.get('prveId')]
    if steps != ['Unarchive the journal']:
        problems.append(f'Unarchive has steps {steps}; Odoo checks nothing on unarchiving')
    return problems


def step_draftguard():
    """Odoo's "You can not archive a journal containing draft journal entries." into the Archive workflow.

    Re-runnable: the nodes are matched by name, the branch condition is read back before it is written, and
    the workflow is republished only when something changed."""
    guard()
    pid = hap.ids()['workflows'][KEY + 'Archive']
    proc, byname = nodes_by_name(pid)
    if ARCHIVE_STEP not in byname:
        sys.exit(f'{ARCHIVE_STEP!r} is not in the Archive workflow — run `buttons` first')
    print('  backup:', hap.backup('journals_archive_workflow_pre_draftguard', proc))
    inv = invoice_fields()
    changed = COUNT_STEP not in byname
    if changed:
        # In front of the update step: batch-add inserts after the trigger, so the existing
        # "Archive the journal" becomes what the branch converges on.
        hap.run('workflow', 'node', 'batch-add', pid, '--nodes',
                json.dumps(guard_nodes(inv), ensure_ascii=False),
                '--trigger-node-id', proc['startEventId'], '--trigger-alias', 'trigger')
        proc, byname = nodes_by_name(pid)
    if TELL_STEP not in byname and TELL_STEP_WAS in byname:
        hap.run('workflow', 'node', 'rename', pid, byname[TELL_STEP_WAS]['id'], '-n', TELL_STEP)
        proc, byname = nodes_by_name(pid)
        changed = True
    if STOP_STEP not in byname:
        # 中止流程 (node type 30) has no builder in hap-cli's DSL; add it by hand, last in the Yes path.
        hap.run('workflow', 'node', 'add', pid, '--type', str(ABORT), '-n', STOP_STEP,
                '--after', byname[TELL_STEP]['id'])
        proc, byname = nodes_by_name(pid)
        changed = True
    changed |= save_notice(pid, byname[TELL_STEP], DRAFT_MESSAGE, dict(TRIGGER_USER))
    yes, no = branch_paths(proc, byname[DRAFT_BRANCH]['id'])
    changed |= save_path(pid, yes, 'Yes', at_least_one_draft(byname[COUNT_STEP]['id']))
    changed |= save_path(pid, no, 'No', [])
    print(f"  {'published' if changed else 'already built; not re-published'}:",
          C.publish(pid) if changed else '')
    print(C.structure(pid))


# ── 5 · seed and verify ─────────────────────────────────────────────────────

TYPES = [o['value'] for o in TYPE_OPTIONS]


def reference_table():
    """The journals of the 19.4 extract by Sequence Prefix, in Odoo id order (its table "Records")."""
    out, section = {}, ''
    for line in REFERENCE.read_text(encoding='utf-8').splitlines():
        if line.startswith('#'):
            section = line.strip('# ')
            continue
        cells = [x.strip() for x in line.strip().strip('|').split('|')] if line.startswith('|') else []
        if section.startswith('Records') and len(cells) == 13 and cells[2] in TYPES:
            out[cells[3]] = dict(id=int(cells[0]), name=cells[1], type=cells[2], code=cells[3],
                                 sequence=int(cells[4]), invoice_reference_type=cells[5],
                                 invoice_reference_model=cells[6], refund_sequence=cells[7] == 'yes',
                                 payment_sequence=cells[8] == 'yes', active='all active' in section)
    return dict(sorted(out.items(), key=lambda kv: kv[1]['id']))


def listed(v):
    """A record-get option value (a list, or a JSON string of one) as a list."""
    if isinstance(v, str):
        v = json.loads(v) if v.startswith('[') else []
    return v if isinstance(v, list) else []


def option_label(v):
    labels = [x.get('value') if isinstance(x, dict) else x for x in listed(v)]
    return labels[0] if labels else None


def read_journal(rowid):
    """One journal through `record get` (by alias); `record list` can return hidden fields empty."""
    d = hap.run('worksheet', 'record', 'get', WORKSHEET, rowid, '-a', APP)['data']
    flag = lambda k: str(d.get(k)) in ('1', 'True', 'true')
    number = d.get('sequence')
    return dict(rowid=rowid, name=d.get('name'), type=option_label(d.get('type')), code=d.get('code') or '',
                sequence=int(float(number)) if number not in (None, '') else None,
                invoice_reference_type=option_label(d.get('invoice_reference_type')),
                invoice_reference_model=option_label(d.get('invoice_reference_model')),
                refund_sequence=flag('refund_sequence'), payment_sequence=flag('payment_sequence'),
                active=flag('active'))


def read_journals():
    """Every journal, archived or not, by rowid."""
    return {r['rowid']: read_journal(r['rowid']) for r in C.records(WORKSHEET, APP)}


def standard_label(short):
    """'Full Reference' (the extract's short form) -> 'Full Reference (INV/2024/00001)'."""
    return next(o['value'] for o in COMMUNICATION_STANDARD_OPTIONS if o['value'].split(' (')[0] == short)


def expected(e):
    return dict(name=e['name'], type=e['type'], code=e['code'], sequence=e['sequence'],
                invoice_reference_type=e['invoice_reference_type'],
                invoice_reference_model=standard_label(e['invoice_reference_model']),
                refund_sequence=e['refund_sequence'], payment_sequence=e['payment_sequence'], active=e['active'])


def differences(live, e):
    return {k: (live.get(k), v) for k, v in expected(e).items() if live.get(k) != v}


def values_for(f, e):
    key = lambda name, label: next(o['key'] for o in f[name]['options'] if o['value'] == label)
    want = expected(e)
    cid = lambda n: f[n]['controlId']
    return [{'id': cid('Journal Name'), 'value': want['name']},
            {'id': cid('Type'), 'value': [key('Type', want['type'])]},
            {'id': cid('Sequence Prefix'), 'value': want['code']},
            {'id': cid('Sequence'), 'value': str(want['sequence'])},
            {'id': cid('Communication Type'), 'value': [key('Communication Type', want['invoice_reference_type'])]},
            {'id': cid('Communication Standard'),
             'value': [key('Communication Standard', want['invoice_reference_model'])]},
            {'id': cid('Dedicated Credit Note Sequence'), 'value': 1 if want['refund_sequence'] else 0},
            {'id': cid('Dedicated Payment Sequence'), 'value': 1 if want['payment_sequence'] else 0},
            {'id': cid('Active'), 'value': 1 if want['active'] else 0}]    # always explicit on API writes


def step_seed(*only):
    """Create the missing journals and correct the ones that differ, matched by Sequence Prefix; `only` limits it
    to Sequence Prefixes. Creation order follows Odoo's ids."""
    guard()
    f = C.fields(WORKSHEET)
    journals = {j['code']: j for j in read_journals().values()}
    print('  backup:', hap.backup('journals_records_pre_seed', journals))
    for code, e in reference_table().items():
        if only and code not in only:
            continue
        live = journals.get(code)
        if live and not differences(live, e):
            continue
        values = json.dumps(values_for(f, e), ensure_ascii=False)
        if live:
            hap.run('worksheet', 'record', 'update', WORKSHEET, live['rowid'], '-a', APP, '--fields-json', values)
            rowid = live['rowid']
            print(f"  updated {code} {e['name']}")
        else:
            rowid = C.row_id(hap.run('worksheet', 'record', 'create', WORKSHEET, '-a', APP, '--fields-json', values))
            print(f"  created {code} {e['name']}: {rowid}")
        got = read_journal(rowid)
        if differences(got, e):
            sys.exit(f'{code}: read back {differences(got, e)}')
    step_verify(*only)


def step_verify(*only):
    """Compare the live journals with the 19.4 extract, field by field."""
    reference = reference_table()
    journals = {j['code']: j for j in read_journals().values()}
    bad = 0
    for code, e in reference.items():
        if only and code not in only:
            continue
        live = journals.get(code)
        if not live:
            print(f"  MISSING  {code:<5} {e['name']}")
            bad += 1
            continue
        diffs = differences(live, e)
        bad += bool(diffs)
        print(f"  {'OK  ' if not diffs else 'DIFF'}  {code:<5} {live['name']:<25} {live['type']:<13} "
              f"seq={live['sequence']:<3} {live['invoice_reference_type']} / {live['invoice_reference_model']} "
              f"credit-note-seq={int(live['refund_sequence'])} payment-seq={int(live['payment_sequence'])} "
              f"active={int(live['active'])}" + (f'  <- {diffs}' if diffs else ''))
    extra = sorted(f"{j['name']} ({code}, active={int(j['active'])})" for code, j in journals.items()
                   if code not in reference)
    print(f'  {len(reference)} in the extract; {bad} missing or differing; {len(extra)} not in the extract {extra}')
    return bad


def step_journal(*names):
    """Print the stored values of journals by Journal Name, hidden fields included."""
    journals = {j['name']: j for j in read_journals().values()}
    for name in names or sorted(journals):
        j = journals.get(name)
        print(f'  {name}: ' + (json.dumps(j, ensure_ascii=False) if j else 'no such journal'))


def step_order():
    """Each view's records in the order the view returns them (its own filter and sort)."""
    f = C.fields(WORKSHEET)
    name, code = f['Journal Name']['controlId'], f['Sequence Prefix']['controlId']
    sequences = {j['rowid']: j['sequence'] for j in read_journals().values()}
    for v in hap.listing('worksheet', 'view', 'list', WORKSHEET, '-a', APP):
        res = hap.run('worksheet', 'record', 'list', WORKSHEET, '-a', APP, '-n', '100', '--view-id', v['viewId'],
                      '--use-field-id-as-key')
        data = res.get('data', res) if isinstance(res, dict) else res
        rows = (data.get('rows') if isinstance(data, dict) else data) or []
        print(f"  {v['name']} ({len(rows)}): "
              + ', '.join(f"{r[name]} [{r[code]}, {sequences.get(r['rowid'])}]" for r in rows))


# ── self-check: the writes the worksheet must refuse, and both buttons ──────

TEST_JOURNAL = dict(id=0, name=TEST_NAME, type='Miscellaneous', code=TEST_CODE, sequence=99,
                    invoice_reference_type='Based on Invoice', invoice_reference_model='Full Reference',
                    refund_sequence=False, payment_sequence=False, active=True)
TOO_LONG = 'TSTLNG'                               # 6 characters; Odoo's code is Char(size=5)


def attempt(*args):
    """Run a write expected to be refused; return (refused, message)."""
    try:
        out = hap.run(*args)
    except RuntimeError as error:
        return True, str(error)[:400]
    data = out.get('data', out) if isinstance(out, dict) else {}
    code = out.get('resultCode') if isinstance(out, dict) else None
    inner = data.get('resultCode') if isinstance(data, dict) else None
    return (code not in (None, 1) or inner not in (None, 1)), json.dumps(out, ensure_ascii=False)[:400]


def step_selfcheck():
    """Writes through the API that Journals must refuse, then Archive and Unarchive.

    Uses one record, TEST Journal (TSTJ, Miscellaneous, Sequence 99), created if missing and left **active** for
    the reviewer. A write that is not refused is undone (a created record is recoded and archived) and reported."""
    guard()
    f = C.fields(WORKSHEET)
    test = next((j for j in read_journals().values() if j['name'] == TEST_NAME), None)
    if not test:
        rowid = C.row_id(hap.run('worksheet', 'record', 'create', WORKSHEET, '-a', APP, '--fields-json',
                                 json.dumps(values_for(f, TEST_JOURNAL), ensure_ascii=False)))
        test = read_journal(rowid)
        print(f'  created {TEST_NAME}: {rowid}')
        if differences(test, TEST_JOURNAL):
            sys.exit(f'{TEST_NAME}: read back {differences(test, TEST_JOURNAL)}')
    rowid = test['rowid']
    prefix = f['Sequence Prefix']['controlId']
    results = []

    def create(label, code):
        name = f'TEST {label}'
        check = f'create a journal with Sequence Prefix {code!r}'
        stray = next((j for j in read_journals().values() if j['name'] == name), None)
        if stray:            # an earlier run's write went through; do not pile up another copy of it
            results.append((check, False, f"accepted in an earlier run: {name} ({stray['rowid']}), recoded "
                                          f"{stray['code']!r} and archived"))
            return
        refused, message = attempt('worksheet', 'record', 'create', WORKSHEET, '-a', APP, '--fields-json',
                                   json.dumps(values_for(f, {**TEST_JOURNAL, 'name': name, 'code': code}),
                                              ensure_ascii=False))
        stray = next((j for j in read_journals().values() if j['name'] == name), None)
        if stray:                                  # not refused, or refused after writing: put it out of the way
            hap.run('worksheet', 'record', 'update', WORKSHEET, stray['rowid'], '-a', APP, '--fields-json',
                    json.dumps([{'id': prefix, 'value': f"T{stray['rowid'][:4]}"},
                                {'id': f['Active']['controlId'], 'value': 0}]))
            message += f"  -> a record was created: {name} ({stray['rowid']}) recoded and archived"
            refused = False
        results.append((check, refused, message))

    def update(label, code):
        refused, message = attempt('worksheet', 'record', 'update', WORKSHEET, rowid, '-a', APP,
                                   '--fields-json', json.dumps([{'id': prefix, 'value': code}]))
        now = read_journal(rowid)['code']
        if now != TEST_CODE:
            hap.run('worksheet', 'record', 'update', WORKSHEET, rowid, '-a', APP, '--fields-json',
                    json.dumps([{'id': prefix, 'value': TEST_CODE}]))
            message += f'  -> stored {now!r}; restored {TEST_CODE!r}'
            refused = False
        results.append((f'set {TEST_NAME}\'s Sequence Prefix to {code!r}', refused, message))

    create('duplicate prefix', 'INV')              # account_journal_code_company_uniq
    create('long prefix', TOO_LONG)                # Char(size=5)
    update('duplicate prefix', 'BILL')
    update('long prefix', TOO_LONG)
    for check, refused, message in results:
        print(f"  {'refused ' if refused else 'ACCEPTED'}  {check}\n      {message}")

    active = lambda: read_journal(rowid)['active']
    workflows = hap.ids()['workflows']
    for step, want in (('Archive', False), ('Unarchive', True)):    # left active for the reviewer
        if active() == want:
            print(f'  {TEST_NAME} is already active={int(want)}; {step} not triggered')
            continue
        hap.run('workflow', 'trigger', workflows[KEY + step], '-s', rowid)
        for _ in range(20):
            if active() == want:
                break
            time.sleep(1)
        print(f'  workflow trigger {step}: {TEST_NAME} active={int(active())} (expected {int(want)})')
    print(f'  {TEST_NAME} {rowid}: {json.dumps(read_journal(rowid), ensure_ascii=False)}')
    return sum(1 for _, refused, _ in results if not refused)


# ── the archive guard, proved both ways ─────────────────────────────────────

GUARD_JOURNAL = dict(id=0, name='TEST draft guard', type='Miscellaneous', code='TSTDG', sequence=99,
                     invoice_reference_type='Based on Invoice', invoice_reference_model='Full Reference',
                     refund_sequence=False, payment_sequence=False, active=True)
GUARD_DOCUMENT = 'TEST draft guard'                 # its Customer Reference, the way 06 names a TEST document
DRAFT = 'Draft'                                     # what an unnumbered draft's Number holds


def invoice_option(inv, name, label):
    return next(o['key'] for o in inv[name]['options'] if o['value'] == label)


def draft_documents(inv):
    """{rowid: (Customer Reference, Journal rowid, Status)} for every document, through `record list`."""
    cid = lambda n: inv[n]['controlId']
    out = {}
    for r in C.records(INVOICES, APP):
        journal = r.get(cid('Journal')) or ''
        if isinstance(journal, str) and journal.startswith('['):
            journal = json.loads(journal)
        first = journal[0] if isinstance(journal, list) and journal else {}
        status = r.get(cid('Status')) or ''
        if isinstance(status, str) and status.startswith('['):
            status = json.loads(status)
        label = (status[0].get('value') if isinstance(status, list) and status and isinstance(status[0], dict)
                 else status)
        out[r['rowid']] = (r.get(cid('Customer Reference')) or '',
                           first.get('sid') or first.get('rowid') or first.get('sourcevalue') or '', label)
    return out


def ensure_guard_records():
    """The TEST journal the guard is proved on, and the TEST draft entry that must stop it. Both created if
    missing, neither ever deleted: they are the reviewer's evidence."""
    f, inv = C.fields(WORKSHEET), C.fields(INVOICES)
    journal = next((j for j in read_journals().values() if j['name'] == GUARD_JOURNAL['name']), None)
    if not journal:
        rowid = C.row_id(hap.run('worksheet', 'record', 'create', WORKSHEET, '-a', APP, '--fields-json',
                                 json.dumps(values_for(f, GUARD_JOURNAL), ensure_ascii=False)))
        journal = read_journal(rowid)
        print(f"  created {GUARD_JOURNAL['name']}: {rowid}")
    docs = draft_documents(inv)
    doc = next((rid for rid, (ref, _, _) in docs.items() if ref == GUARD_DOCUMENT), None)
    if not doc:
        cid = lambda n: inv[n]['controlId']
        doc = C.row_id(hap.run('worksheet', 'record', 'create', INVOICES, '-a', APP, '--fields-json', json.dumps([
            {'id': cid('Number'), 'value': DRAFT},
            {'id': cid('Type'), 'value': [invoice_option(inv, 'Type', 'Journal Entry')]},
            {'id': cid('Status'), 'value': [invoice_option(inv, 'Status', 'Draft')]},
            {'id': cid('Accounting Date'), 'value': time.strftime('%Y-%m-%d')},
            {'id': cid('Journal'), 'value': [journal['rowid']]},
            {'id': cid('Auto-post'), 'value': [invoice_option(inv, 'Auto-post', 'No')]},
            {'id': cid('Customer Reference'), 'value': GUARD_DOCUMENT}], ensure_ascii=False)))
        print(f'  created the draft entry {GUARD_DOCUMENT}: {doc}')
    C.remember('records', KEY + GUARD_JOURNAL['name'], journal['rowid'])
    C.remember('records', KEY + 'draft entry ' + GUARD_DOCUMENT, doc)
    return journal['rowid'], doc


def archive_attempt(rowid, seconds=25):
    """Trigger Archive and wait for Active to go, or for the guard to stop it. Returns the stored Active."""
    before = len(hap.listing('approval', 'history', '--process-id', hap.ids()['workflows'][KEY + 'Archive']))
    hap.run('workflow', 'trigger', hap.ids()['workflows'][KEY + 'Archive'], '-s', rowid)
    for _ in range(seconds):
        if not read_journal(rowid)['active']:
            break
        time.sleep(1)
    runs = hap.listing('approval', 'history', '--process-id', hap.ids()['workflows'][KEY + 'Archive'])
    return read_journal(rowid)['active'], len(runs) - before


def step_draftcheck():
    """Prove the archive guard both ways, on TEST records only.

    A journal with a draft entry must refuse to archive and keep Active checked; a journal with none must
    archive exactly as before. The tenant's seven journals are never touched — the Sales journal does hold
    two seeded drafts, and archiving it is not how this is tested."""
    guard()
    inv = C.fields(INVOICES)
    guarded, document = ensure_guard_records()
    clean = next((j for j in read_journals().values() if j['name'] == TEST_NAME), None)
    if not clean:
        sys.exit(f'{TEST_NAME} is missing — run `selfcheck` first')
    if not clean['active']:
        hap.run('workflow', 'trigger', hap.ids()['workflows'][KEY + 'Unarchive'], '-s', clean['rowid'])
        time.sleep(5)
    bad = 0
    lines = {ref for ref, journal, status in draft_documents(inv).values()
             if journal == guarded and status == 'Draft'}
    print(f"  {GUARD_JOURNAL['name']} ({guarded}) holds draft documents {sorted(lines)}")

    active, runs = archive_attempt(guarded)
    ok = active is True
    bad += not ok
    print(f"  {'REFUSED ' if ok else 'ARCHIVED'}  {GUARD_JOURNAL['name']}: Active={int(active)} after Archive "
          f"({runs} new workflow run) — expected Active=1, the guard stops the flow before the update")

    active, runs = archive_attempt(clean['rowid'])
    ok = active is False
    bad += not ok
    print(f"  {'archived' if ok else 'REFUSED '}  {TEST_NAME}: Active={int(active)} after Archive "
          f'({runs} new workflow run) — expected Active=0, it holds no draft entry')
    if not active:                                  # put it back the way the reviewer found it
        hap.run('workflow', 'trigger', hap.ids()['workflows'][KEY + 'Unarchive'], '-s', clean['rowid'])
        for _ in range(20):
            if read_journal(clean['rowid'])['active']:
                break
            time.sleep(1)
        print(f"  {TEST_NAME} unarchived again: active={int(read_journal(clean['rowid'])['active'])}")
    print(f"  {GUARD_JOURNAL['name']} {guarded}: "
          f'{json.dumps(read_journal(guarded), ensure_ascii=False)}')
    return bad


# ── check: read the configuration back ──────────────────────────────────────

def step_check():
    """Controls, options, defaults, rules, views and buttons against this spec; exits non-zero on a difference."""
    ctrls = hap.controls(WORKSHEET)
    f = hap.by_name(ctrls)
    names = {c['controlId']: c['controlName'] for c in ctrls}
    problems = []
    if set(f) != set(PLACE):
        problems.append(f'controls {sorted(set(f) ^ set(PLACE))}')
    problems += [f'{n}: {d}' for n, d in layout_differences(ctrls).items()]
    for cid, (name, _) in FIRST_BUILD.items():
        if f.get(name, {}).get('controlId') != cid:
            problems.append(f"{name} id is {f.get(name, {}).get('controlId')}, first build {cid}")
    for name, opts in OPTIONS.items():
        live = [(o['key'], o['value']) for o in f.get(name, {}).get('options', []) if not o.get('isDeleted')]
        if live != [(o['key'], o['value']) for o in opts]:
            problems.append(f'{name} options {live}')
    for name, want in {'Communication Type': 'Based on Invoice',
                       'Communication Standard': 'Full Reference (INV/2024/00001)',
                       'Active': '1', 'Sequence': '10', 'Dedicated Credit Note Sequence': '0',
                       'Dedicated Payment Sequence': '0'}.items():
        if name not in f:
            continue                               # already reported as a missing control
        source = json.loads((f[name].get('advancedSetting') or {}).get('defsource') or '[]')
        value = source[0]['staticValue'] if source else None
        label = next((o['value'] for o in f[name].get('options', []) if o['key'] == value), value)
        if label != want:
            problems.append(f'{name} default {label!r}, want {want!r}')
    if f.get('Journal Name', {}).get('attribute') != 1:
        problems.append('Journal Name is not the title field')
    if 'Sequence' in f and (f['Sequence']['type'] != 6 or f['Sequence'].get('dot') != 0):
        problems.append(f"Sequence is type {f['Sequence']['type']} with {f['Sequence'].get('dot')} decimals")
    rules = {r['name']: r for r in hap.listing('worksheet', 'rules', WORKSHEET)}
    keys = {o['key']: o['value'] for o in f.get('Type', {}).get('options', [])}
    for name, (types, targets, kind) in RULES.items():
        r = rules.get(name)
        if not r:
            problems.append(f'rule {name!r} missing')
            continue
        conds = [g for group in r['filters'] for g in group.get('groupFilters', [])]
        got = (r['type'], r['disabled'], {i['type'] for i in r['ruleItems']},
               sorted(keys.get(v) for c in conds for v in c.get('values', [])),   # stored in option order
               [names.get(c['controlId']) for i in r['ruleItems'] for c in i['controls']])
        if got != (C.INTERACTION, False, {kind}, sorted(types), targets):
            problems.append(f'rule {name!r}: {got}')
    views = {v['name']: C.view_info(WORKSHEET, APP, v['viewId']) for v in
             hap.listing('worksheet', 'view', 'list', WORKSHEET, '-a', APP)}
    for name, op in (('Journals', C.EQ), ('Archived', C.NE)):
        v = views.get(name, {})
        got = dict(columns=[names.get(x) for x in v.get('showControls', [])],
                   sort=[(names.get(s['controlId']), s['isAsc']) for s in v.get('moreSort', [])],
                   sortCid=names.get(v.get('sortCid')), sortType=v.get('sortType'),
                   filters=[(names.get(x['controlId']), x['filterType'], x.get('values'))
                            for x in v.get('filters', [])],
                   quick=[(names.get(q['controlId']), (q.get('advancedSetting') or {}).get('allowitem'))
                          for q in v.get('fastFilters', [])])
        want = dict(columns=list(COLUMNS), sort=[(s, True) for s in SORT], sortCid=SORT[0], sortType=2,
                    filters=[('Active', op, ['1'])], quick=[('Type', '2')])
        if got != want:
            problems.append(f'view {name}: {got}')
    if list(views) != ['Journals', 'Archived']:
        problems.append(f'view order {list(views)}')
    buttons = {b['name']: b for b in hap.listing('worksheet', 'custom-actions', WORKSHEET)}
    for name, op, confirm in (('Archive', C.EQ, MSG_ARCHIVE), ('Unarchive', C.NE, '')):
        b = buttons.get(name)
        if not b:
            problems.append(f'button {name} missing')
            continue
        conds = [(names.get(x['controlId']), x['filterType'], x.get('values')) for x in b.get('filters') or []]
        if conds != [('Active', op, ['1'])] or (b.get('confirmMsg') or '') != confirm:
            problems.append(f"button {name}: filters={conds} confirm={b.get('confirmMsg')!r}")
    problems += guard_differences()
    order = sorted(ctrls, key=lambda c: (c.get('row', 0), c.get('col', 0)))
    tab_ids = {c['controlName']: c['controlId'] for c in ctrls if c['type'] == C.TAB}
    for tab in TABS:
        print(f"  tab {tab}: {[c['controlName'] for c in order if c.get('sectionId') == tab_ids.get(tab)]}")
    print(f"  no tab: {[c['controlName'] for c in order if not c.get('sectionId') and c['type'] != C.TAB]}")
    print('  check: ' + ('OK — controls, tabs, options, defaults, rules, views, buttons and the archive '
                         'guard as specified'
                         if not problems else 'DIFFERENCES\n    ' + '\n    '.join(problems)))
    return len(problems)


def step_all():
    for name in ('layout', 'rules', 'views', 'buttons', 'draftguard', 'seed'):
        print(f'\n── {name} ' + '─' * 60)
        STEPS[name]()
    print('\n── check ' + '─' * 60)
    return step_check()


def show():
    C.show(WORKSHEET)


STEPS = {
    'layout': step_layout,
    'rules': step_rules,
    'views': step_views,
    'buttons': step_buttons,
    'draftguard': step_draftguard,
    'seed': step_seed,
    'all': step_all,
    'verify': step_verify,
    'check': step_check,
    'selfcheck': step_selfcheck,
    'draftcheck': step_draftcheck,
    'order': step_order,
    'journal': step_journal,
    'untouched': step_untouched,
    'show': show,
}

if __name__ == '__main__':
    step = sys.argv[1] if len(sys.argv) > 1 else 'check'
    if step not in STEPS:
        raise SystemExit(f"Unknown step {step!r}; choose from {', '.join(STEPS)}")
    result = STEPS[step](*sys.argv[2:])
    if step in ('verify', 'check', 'all', 'selfcheck') and result:
        sys.exit(1)
