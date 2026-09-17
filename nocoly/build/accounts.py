#!/usr/bin/env python3
"""Build the Chart of Accounts worksheet (Odoo account.account, as on casimir.odoo.com saas~19.4) in ERP Master.

Bundle 2 of the six that join Phase 1, in two parts. **Part A** is the worksheet itself, and none of its steps
writes to another worksheet. **Part B** brings the account fields to Contacts, Products, Product Categories,
Journals and Invoice Lines (and the lines table inside Invoices), automation B that fills a line's account, the
per-field hiding in the roles, and the tenant's references. Requirements: nocoly/worksheets/09-chart-of-accounts.md
§1. Generic helpers: common.py. Run from the repo root with the CLI's interpreter:

    ~/.hap-venv/bin/python nocoly/build/accounts.py create      # 0. the worksheet, first in the menu group Invoicing
    ~/.hap-venv/bin/python nocoly/build/accounts.py fields      # 1. the stored fields and Parent Account, in one save
                                                                #    of the empty worksheet; the self-relation brings
                                                                #    its own reverse
    ~/.hap-venv/bin/python nocoly/build/accounts.py computed    # 2. Display Name and Internal Group, two text
                                                                #    function formulas
    ~/.hap-venv/bin/python nocoly/build/accounts.py layout      # 3. places, the title, permissions, help, hints,
                                                                #    Code's format check, Parent Account's picker
                                                                #    filter, the reverse named Child Accounts, hidden
    ~/.hap-venv/bin/python nocoly/build/accounts.py rules       # 4. two interaction rules and the validation rule
    ~/.hap-venv/bin/python nocoly/build/accounts.py automation  # 5. A · Payment Reconciliation follows Type
    ~/.hap-venv/bin/python nocoly/build/accounts.py buttons     # 6. Archive / Unarchive and their one-step workflows
    ~/.hap-venv/bin/python nocoly/build/accounts.py views       # 7. Chart of Accounts (opens first) and Archived
    ~/.hap-venv/bin/python nocoly/build/accounts.py roles       # 8. roles.py's create step, which now carries this
                                                                #    worksheet into the four business roles
    ~/.hap-venv/bin/python nocoly/build/accounts.py seed        # 9. the 87 accounts, each read back; then automation
                                                                #    A's runs on them are awaited, then verify
    ~/.hap-venv/bin/python nocoly/build/accounts.py all         # every step above, then check

    ~/.hap-venv/bin/python nocoly/build/accounts.py check       # the configuration against §1: menu place, controls,
                                                                #    formulas, rules, automation A, buttons, views
    ~/.hap-venv/bin/python nocoly/build/accounts.py verify      # the live accounts against casimir-accounts.json,
                                                                #    Display Name and Internal Group included
    ~/.hap-venv/bin/python nocoly/build/accounts.py runs        # automation A's run history: status and the path
                                                                #    each run took
    ~/.hap-venv/bin/python nocoly/build/accounts.py selfcheck   # what §1 relies on the platform for, driven through
                                                                #    the CLI on TEST Account (left in the worksheet)
    ~/.hap-venv/bin/python nocoly/build/accounts.py order       # each view's records in the view's own order
    ~/.hap-venv/bin/python nocoly/build/accounts.py account 410000   # stored values by Code, hidden fields included
    ~/.hap-venv/bin/python nocoly/build/accounts.py untouched   # every other worksheet: control count and digest
    ~/.hap-venv/bin/python nocoly/build/accounts.py show        # the live control list

Part B — each step adds with `add-fields`, places through the worksheet's own script (its `layout`, `rules`,
`views`, whose tables carry this bundle's additions) and reads everything back:

    ~/.hap-venv/bin/python nocoly/build/accounts.py contacts      # B1. tab Invoicing, Account Receivable / Payable,
                                                                  #     the tab's rule (contacts.py layout, rules)
    ~/.hap-venv/bin/python nocoly/build/accounts.py products      # B2. tab Accounting, Income / Expense Account
                                                                  #     (products.py layout)
    ~/.hap-venv/bin/python nocoly/build/accounts.py categories    # B3. tab Accounting, Income / Expense Account with
                                                                  #     their defaults (prodcat.py layout)
    ~/.hap-venv/bin/python nocoly/build/accounts.py journals      # B4. the five accounts, their five rules, the
                                                                  #     Default Account column (journals.py layout,
                                                                  #     rules, views)
    ~/.hap-venv/bin/python nocoly/build/accounts.py lines         # B5. Account, the figures rule, the Lines column
                                                                  #     and the Invoices subtable column (invlines.py
                                                                  #     layout, rules, views)
    ~/.hap-venv/bin/python nocoly/build/accounts.py automation-b  # B6. automation B, two workflows with one body
    ~/.hap-venv/bin/python nocoly/build/accounts.py visibility    # B7. the fields hidden by role (roles.py create)
    ~/.hap-venv/bin/python nocoly/build/accounts.py references    # B8. Records step 2, each read back
    ~/.hap-venv/bin/python nocoly/build/accounts.py all-b         # every part B step above, then check-b

    ~/.hap-venv/bin/python nocoly/build/accounts.py check-b       # part B's configuration against §1
    ~/.hap-venv/bin/python nocoly/build/accounts.py verify-b      # the references read back
    ~/.hap-venv/bin/python nocoly/build/accounts.py selfcheck-b   # automation B proved on TEST records (left in place)
    ~/.hap-venv/bin/python nocoly/build/accounts.py runs-b        # automation B's run history by status and step
    ~/.hap-venv/bin/python nocoly/build/accounts.py rerun-b       # the owning steps this bundle extended, run again:
                                                                  #     each must write nothing
    ~/.hap-venv/bin/python nocoly/build/accounts.py records-b     # every record against the pre-part-B snapshot in
                                                                  #     backups/ (not committed)

Every step reads the live state first and is safe to re-run; a second run writes nothing to HAP. Every part A write
step stops unless the profile reaches ERP Master › Invoicing › Chart of Accounts and the worksheet holds only this
script's own work, and compares the other eight worksheets' controls id by id before and after. Every part B write
is bracketed by a control-by-control comparison of all nine worksheets, allowing only the changes it names.

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
SALES_APP = '3e596740-d096-42cd-b948-0b62a0220927'   # the Nocoly Sales app: never written to
SECTION = 'Invoicing'
WORKSHEET = 'Chart of Accounts'
KEY = WORKSHEET + ': '                              # ids.json key prefix for everything this worksheet owns
ALIAS = 'account_account'
HERE = Path(__file__).resolve().parent
DATA = HERE.parent / 'data' / 'casimir-accounts.json'
OTHERS = ('Contacts', 'Units & Packagings', 'Products', 'Product Variants', 'Product Categories', 'Journals',
          'Invoices', 'Invoice Lines')             # every other worksheet: never written to here


def ws():
    return hap.ids()['worksheets'][WORKSHEET]


def section_id():
    return hap.ids()['sections'][SECTION]


def data():
    return json.loads(DATA.read_text(encoding='utf-8'))


# ── Type: Odoo's 19 options ─────────────────────────────────────────────────

def option(key, value, index, color):
    return {'key': key, 'value': value, 'isDeleted': False, 'index': index, 'checked': False, 'color': color}


# (Odoo key, Odoo label, the option key minted once for this worksheet). Records point at the keys: never re-mint.
TYPES = [
    ('asset_receivable', 'Receivable', 'c7b90c3b-457c-4913-8749-d9edac56b9f4'),
    ('asset_cash', 'Bank and Cash', '7e3ac986-c95a-47ce-942d-c66fff73edc0'),
    ('asset_current', 'Current Assets', 'de6328c9-137a-48d2-bb9a-d5d758c28e95'),
    ('asset_non_current', 'Non-current Assets', '8c3d1fe7-3677-402f-9032-5be8a87ac898'),
    ('asset_prepayments', 'Prepayments', 'bb5a3d4a-776b-45db-aefa-6bd67d83e0b6'),
    ('asset_fixed', 'Fixed Assets', '6117ca95-426e-4b31-ace6-8aff539a0198'),
    ('liability_payable', 'Payable', 'f17a5ca2-25bf-420d-8e73-559566c5ca5e'),
    ('liability_credit_card', 'Credit Card', 'bd2ebed9-35f9-4d7f-b43f-a424fffa2b1b'),
    ('liability_current', 'Current Liabilities', '73595cbf-a706-426a-9f0a-2c446cdad7cf'),
    ('liability_non_current', 'Non-current Liabilities', '0bb77823-a71d-4a19-be0c-4d0a4d02e9be'),
    ('equity', 'Equity', '75c354ab-0ab9-4c2a-9757-58abbd15b4d2'),
    ('equity_unaffected', 'Current Year Earnings', '0bb83869-f1e5-459c-9f99-fa75ee3f50c5'),
    ('income', 'Income', '319660de-d2d9-4bce-a00a-0c62603e8294'),
    ('income_other', 'Other Income', '1a018b62-bd81-4fe4-87f0-2f9b7aec8002'),
    ('expense', 'Expenses', 'ad1c3081-d55e-4212-9637-9747cdd8ee59'),
    ('expense_other', 'Other Expenses', '104203cc-4a0b-4efa-b5d4-ff87042d35e1'),
    ('expense_depreciation', 'Depreciation', '39489910-b2d9-450a-868c-9c2653b19aae'),
    ('expense_direct_cost', 'Cost of Revenue', 'e66993f1-dcd1-4b93-a8d2-b281ff4f6ae0'),
    ('off_balance', 'Off-Balance Sheet', 'a899104b-0d2b-4687-91c4-cbed93163df7'),
]
# Odoo internal_group = account_type.split('_')[0], with its selection labels
INTERNAL_GROUP = {'asset': 'Asset', 'liability': 'Liability', 'equity': 'Equity', 'income': 'Income',
                  'expense': 'Expense', 'off': 'Off Balance'}
GROUPS = ('Asset', 'Liability', 'Equity', 'Income', 'Expense', 'Off Balance')
GROUP_COLOR = {'Asset': '#C9E6FC', 'Liability': '#FFE7B1', 'Equity': '#E6D7FA', 'Income': '#C2F1D2',
               'Expense': '#FBD2BF', 'Off Balance': '#D2D2D2'}   # colours by group (the dropdown shows none)


def group_of(odoo_key):
    return INTERNAL_GROUP[odoo_key.split('_', 1)[0]]


TYPE_OPTIONS = [option(key, label, i + 1, GROUP_COLOR[group_of(odoo)]) for i, (odoo, label, key) in enumerate(TYPES)]
OPTION_KEY = {label: key for _, label, key in TYPES}
LABEL_OF_KEY = {key: label for _, label, key in TYPES}
LABEL_OF_ODOO = {odoo: label for odoo, label, _ in TYPES}
GROUP_OF_LABEL = {label: group_of(odoo) for odoo, label, _ in TYPES}
LABELS = [label for _, label, _ in TYPES]


# ── the form ────────────────────────────────────────────────────────────────

CODE, NAME, DISPLAY, TYPE, GROUP = 'Code', 'Account Name', 'Display Name', 'Type', 'Internal Group'
RECONCILE, NON_TRADE, PARENT, DESCRIPTION, ACTIVE = ('Payment Reconciliation', 'Non Trade', 'Parent Account',
                                                     'Description', 'Active')
CHILDREN = 'Child Accounts'                         # the reverse of Parent Account, made by the server

# §1's form layout, no tabs: Code (4) | Account Name (8); Display Name; Type | Internal Group; Payment
# Reconciliation | Non Trade; Parent Account; Description. The two hidden controls sit under it all — a hidden
# control still needs a place.
PLACE = {
    CODE: (0, 0, 4), NAME: (0, 1, 8),
    DISPLAY: (1, 0, 12),
    TYPE: (2, 0, 6), GROUP: (2, 1, 6),
    RECONCILE: (3, 0, 6), NON_TRADE: (3, 1, 6),
    PARENT: (4, 0, 6),
    DESCRIPTION: (5, 0, 12),
    ACTIVE: (6, 0, 6),
    CHILDREN: (7, 0, 12),
}
ALIASES = {CODE: 'code', NAME: 'name', DISPLAY: 'display_name', TYPE: 'account_type', GROUP: 'internal_group',
           RECONCILE: 'reconcile', NON_TRADE: 'non_trade', PARENT: 'parent_id', DESCRIPTION: 'description',
           ACTIVE: 'active', CHILDREN: 'child_ids'}
HINTS = {CODE: 'e.g. 101000', NAME: 'e.g. Current Assets', PARENT: 'Root account',
         DESCRIPTION: 'Enter description here...'}   # Odoo's placeholders; every other control gets none
DESC = {  # Odoo's field help, verbatim, where it has one (19.4 labels and help); how a helper is computed otherwise
    TYPE: 'Account Type is used for information purpose, to generate country-specific legal reports, and set the '
          'rules to close a fiscal year and generate opening entries.',
    RECONCILE: 'This account is used in bank reconciliation. Currency rate difference entries will be automatically '
               'created if needed.',
    NON_TRADE: 'If set, this account will belong to Non Trade Receivable/Payable in reports and filters.\n'
               'If not, this account will belong to Trade Receivable/Payable in reports and filters.',
    DISPLAY: 'The Code, a space and the Account Name — Odoo display_name, as an accounting user sees it. It is the '
             'title: what every list, card and picker shows.',
    GROUP: 'Asset, Liability, Equity, Income, Expense or Off Balance, from the Type — Odoo internal_group. Odoo '
           'keeps it out of sight and filters on it; here a view can show it and filter on it.',
    CHILDREN: 'The accounts whose Parent Account is this one — Odoo child_ids. Hidden: Odoo shows an account\'s '
              'children only by indenting its list.',
}
REQUIRED = {CODE, NAME, TYPE}
UNIQUE = {CODE}                                     # Odoo _ensure_code_is_unique, per company = per app copy
TITLE = DISPLAY
# "100" = read-only and hidden on create (a hidden field never shows as a table column); "011" = hidden
PERMISSION = {DISPLAY: '100', GROUP: '100', ACTIVE: '011', CHILDREN: '011'}

# Odoo ACCOUNT_CODE_REGEX and _check_account_code's message without its "(account code: %s)" — a HAP message is
# static. HAP's text control carries it as advancedSetting.filterregex (the field editor's 限定输入格式): a JSON
# list of {name, value, err}, checked by the form (pd-openweb formUtils checkValueByFilterRegex).
CODE_FORMAT = [{'name': 'Letters, digits and dots', 'value': '^[A-Za-z0-9.]+$',
                'err': 'The account code can only contain alphanumeric characters and dots.'}]
ADVANCED = {  # advancedSetting keys this script owns; Parent Account's `filters` is built by picker_filters()
    CODE: {'filterregex': json.dumps(CODE_FORMAT, ensure_ascii=False)},
    TYPE: {'showtype': '0'},
    RECONCILE: {'defsource': C.static_default(0), 'showtype': '0'},
    NON_TRADE: {'defsource': C.static_default(0), 'showtype': '0'},
    ACTIVE: {'defsource': C.static_default(1), 'showtype': '0'},
    PARENT: {'showtype': '3', 'bidirectional': '1'},       # 3 = dropdown; a self-relation is two-way regardless
}
JSON_SETTINGS = ('filterregex', 'filters')          # compared parsed, not as strings

# (hap-cli builder type, extra control keys) of the controls this script creates. The reverse is the server's.
KIND = {CODE: ('TEXT', {}), NAME: ('TEXT', {}), TYPE: ('DROP_DOWN', {}), RECONCILE: ('SWITCH', {}),
        NON_TRADE: ('SWITCH', {}), PARENT: ('RELATE_SHEET', {}), DESCRIPTION: ('TEXT', {'enumDefault': 1}),
        ACTIVE: ('SWITCH', {}), DISPLAY: ('FORMULA_FUNC', {'enumDefault2': 2}),
        GROUP: ('FORMULA_FUNC', {'enumDefault2': 2})}
STORED = (CODE, NAME, TYPE, RECONCILE, NON_TRADE, PARENT, DESCRIPTION, ACTIVE)   # step 1
COMPUTED = (DISPLAY, GROUP)                                                      # step 2
FORMULA = 53
TEXT_RESULT = 2                                     # enumDefault2 2 = a function formula with a text result


def ref(c):
    return f"${c['controlId']}$"


def function_source(expression):
    """dataSource of a function formula (type 53), as contacts.py, variants.py and prodcat.py write it."""
    return json.dumps({'type': 'mdfunction', 'expression': expression, 'status': 1}, ensure_ascii=False)


def display_name_expression(f):
    """Odoo _compute_display_name for an accounting user: f"{code} {name}" when there is a code, else the name —
    which TRIM gives in one expression."""
    return f'TRIM(CONCAT({ref(f[CODE])}," ",{ref(f[NAME])}))'


def internal_group_expression(f):
    """Odoo internal_group = account_type.split('_')[0]. A function formula sees a dropdown as its **label**, so the
    six groups are spelled out over the 19 labels; an empty Type gives an empty group, as Odoo's does."""
    t = ref(f[TYPE])
    expression = '""'
    for group in reversed(GROUPS):
        labels = [label for label in LABELS if GROUP_OF_LABEL[label] == group]
        test = ','.join(f'{t}=="{label}"' for label in labels)
        expression = f'IF({test if len(labels) == 1 else f"OR({test})"},"{group}",{expression})'
    return expression


EXPRESSIONS = {DISPLAY: display_name_expression, GROUP: internal_group_expression}


def expression_of(c):
    try:
        return json.loads(c.get('dataSource') or '{}').get('expression')
    except (TypeError, ValueError):
        return None


def picker_filters(f):
    """Parent Account's picker: active accounts other than this one. HAP's filter cannot follow a tree, so Odoo's
    `['!', ('id', 'child_of', id)]` is only half built — the account itself is excluded by comparing the
    candidate's Display Name with this record's (the way 04's Extra Packagings excludes the product's unit). The
    UI saves a text formula's condition with dataType 2 (pd-openweb redefineComplexControl), and so does this."""
    base = {'spliceType': 1, 'dateRange': 0, 'dateRangeType': 0, 'minValue': None, 'maxValue': None, 'isAsc': False,
            'advancedSetting': None, 'isGroup': False, 'groupFilters': None, 'emptyRule': 0}
    return json.dumps([
        {'controlId': f[ACTIVE]['controlId'], 'dataType': 36, **base, 'filterType': C.EQ, 'value': '1',
         'values': ['1'], 'dynamicSource': []},
        {'controlId': f[DISPLAY]['controlId'], 'dataType': 2, **base, 'filterType': C.NE, 'value': '', 'values': [],
         'dynamicSource': [{'rcid': '', 'cid': f[DISPLAY]['controlId'], 'staticValue': '', 'isAsync': False,
                            'type': 0}]},
    ], ensure_ascii=False, separators=(',', ':'))


def setting_state(key, value):
    """An advancedSetting value in comparable form: the JSON-valued ones parsed down to what matters."""
    if key not in JSON_SETTINGS:
        return value
    try:
        items = json.loads(value or '[]')
    except (TypeError, ValueError):
        return value
    if key == 'filterregex':
        return [(i.get('name'), i.get('value'), i.get('err')) for i in items]
    return [(i.get('controlId'), i.get('dataType'), i.get('filterType'), i.get('values') or [],
             [d.get('cid') for d in i.get('dynamicSource') or []]) for i in items]


def advanced(name, f):
    out = dict(ADVANCED.get(name) or {})
    if name == PARENT and DISPLAY in f and ACTIVE in f:
        out['filters'] = picker_filters(f)
    return out


def new_control(name, f=None):
    """A control to create, built by hap-cli's own builder. Formulas need the live ids they read."""
    kind, extra = KIND[name]
    extra = dict(extra)
    settings = dict(ADVANCED.get(name) or {})
    if kind == 'FORMULA_FUNC':
        settings = {'analysislink': '1', 'sorttype': 'en'}
        extra['dataSource'] = function_source(EXPRESSIONS[name](f))
    return C.control(kind, name, PLACE[name], alias=ALIASES[name], hint=HINTS.get(name, ''), desc=DESC.get(name, ''),
                     hidden=PERMISSION.get(name) == '011', required=name in REQUIRED, unique=name in UNIQUE,
                     options=[dict(o) for o in TYPE_OPTIONS] if name == TYPE else None,
                     data_source=ws() if name == PARENT else None, multi=False if name == PARENT else None,
                     advanced_setting=settings or None, extra=extra or None)


def desired(c, f):
    """The attributes `layout` owns on control c, as they should read back."""
    name = c['controlName']
    row, col, size = PLACE[name]
    return {'row': row, 'col': col, 'size': size, 'sectionId': '', 'alias': ALIASES[name],
            'hint': HINTS.get(name, ''), 'desc': DESC.get(name, ''), 'required': name in REQUIRED,
            'unique': name in UNIQUE, 'fieldPermission': PERMISSION.get(name, '111'),
            'attribute': 1 if name == TITLE else 0}


def option_state(options):
    return [(o.get('key'), o.get('value'), o.get('index')) for o in options or [] if not o.get('isDeleted')]


def layout_differences(ctrls):
    f = hap.by_name(ctrls)
    out = {}
    for c in ctrls:
        name = c['controlName']
        if name not in PLACE:
            continue
        diff = {k: (c.get(k), v) for k, v in desired(c, f).items()
                if (c.get(k) or (0 if k == 'attribute' else '' if isinstance(v, str) else False)) != v}
        settings = c.get('advancedSetting') or {}
        diff.update({f'advancedSetting.{k}': (settings.get(k), v) for k, v in advanced(name, f).items()
                     if setting_state(k, settings.get(k)) != setting_state(k, v)})
        if name == TYPE and option_state(c.get('options')) != option_state(TYPE_OPTIONS):
            diff['options'] = (option_state(c.get('options')), option_state(TYPE_OPTIONS))
        if diff:
            out[name] = diff
    return out


# ── the other worksheets, untouched ─────────────────────────────────────────

SIGNATURE = ('controlName', 'type', 'alias', 'row', 'col', 'size', 'sectionId', 'required', 'attribute', 'unique',
             'fieldPermission', 'dataSource', 'sourceControlId', 'showControls', 'advancedSetting', 'desc', 'hint')


def signature(worksheet_id):
    """A worksheet's controls by id, position in the listing not compared."""
    return sorted(json.dumps([c['controlId']] + [c.get(k) for k in SIGNATURE], sort_keys=True, ensure_ascii=False)
                  for c in hap.controls(worksheet_id))


def signatures():
    return {name: signature(hap.ids()['worksheets'][name]) for name in OTHERS}


def check_untouched(before):
    after = signatures()
    for name in before:
        if after[name] != before[name]:
            sys.exit(f'{name} controls changed: {sorted(set(after[name]) ^ set(before[name]))}')
    print('  untouched: ' + ', '.join(f'{n} ({len(after[n])})' for n in after))


def step_untouched():
    """Control count and digest of every other worksheet — run before and after a build."""
    for name, sig in signatures().items():
        digest = hashlib.sha256(''.join(sig).encode()).hexdigest()[:16]
        print(f'  {name:<20} {len(sig):>2} controls  sha256:{digest}')


def save_controls(ctrls):
    """A full update-fields save of this worksheet, proving the other worksheets' controls unchanged."""
    before = signatures()
    hap.run('worksheet', 'update-fields', ws(), '--controls', json.dumps(ctrls, ensure_ascii=False))
    check_untouched(before)


# ── guard ───────────────────────────────────────────────────────────────────

STOCK = {'Name', 'Description', 'Attachment', '名称', '描述', '附件'}   # what `worksheet create` puts on a new sheet
TEST_CODE, TEST_NAME = 'TEST01', 'TEST Account'    # selfcheck's own record; left in the worksheet
VIEW, ARCHIVED = 'Chart of Accounts', 'Archived'
BUTTONS = ('Archive', 'Unarchive')


def app_sections():
    return C.app_info(APP)['sections']


def guard(fresh=False):
    """Stop unless the profile reaches ERP Master › Invoicing › Chart of Accounts and the worksheet holds only this
    script's work. `fresh` allows the three stock controls of a brand-new worksheet. Returns the controls."""
    who = hap.run('auth', 'whoami')
    if APP == SALES_APP:
        sys.exit('ids.json points at the Sales app — refusing to write')
    app = hap.run('app', 'info', '-a', APP).get('data', {})
    worksheet = hap.ids().get('worksheets', {}).get(WORKSHEET)
    section = next((s for s in app.get('sections', []) if any(i['id'] == worksheet for i in s['items'])), None)
    if app.get('name') != 'ERP Master' or not section or section['id'] != section_id() or \
            section['name'] != SECTION:
        sys.exit(f"profile {who.get('profile')!r} does not reach ERP Master › {SECTION} › {WORKSHEET}")
    problems, ctrls = [], hap.controls(worksheet)
    f = hap.by_name(ctrls)
    known = set(PLACE) | (STOCK if fresh else set())
    # A self-relation's reverse is made by the server as "Child"; it is known by its reserved id until `layout`
    # names it.
    reverses = {f[PARENT].get('sourceControlId')} if PARENT in f else set()
    problems += [f"unknown control {c['controlName']!r} ({c['controlId']})" for c in ctrls
                 if c['controlName'] not in known and c['controlId'] not in reverses]
    if len(f) != len(ctrls):
        problems.append(f'two controls share a name: {sorted(c["controlName"] for c in ctrls)}')
    views = {v['name'] for v in hap.listing('worksheet', 'view', 'list', worksheet, '-a', APP)}
    problems += [f'unknown view {n!r}' for n in views - {VIEW, ARCHIVED, 'All', '全部'}]
    buttons = {b['name'] for b in hap.listing('worksheet', 'custom-actions', worksheet)}
    problems += [f'unknown button {n!r}' for n in buttons - set(BUTTONS)]
    rules = {r['name'] for r in hap.listing('worksheet', 'rules', worksheet)}
    problems += [f'unknown rule {n!r}' for n in rules - set(RULES)]
    if CODE in f and f[CODE].get('alias') == 'code':
        codes = {a['code'] for a in data()['accounts']}
        for code, (rowid, name) in record_index().items():
            if code not in codes and not str(code).startswith('TEST') and not str(name).startswith('TEST'):
                problems.append(f'unknown record {code!r} {name!r} ({rowid})')
    if problems:
        sys.exit(f"{WORKSHEET} differs from this script's work — stopping:\n  " + '\n  '.join(problems))
    print(f"  guard: profile {os.environ.get('HAP_PROFILE') or who.get('profile')!r}, ERP Master › {SECTION} › "
          f"{WORKSHEET}, {len(ctrls)} controls, {len(rules)} rules, {len(buttons)} buttons, views {sorted(views)}")
    return ctrls


# ── 0 · the worksheet ───────────────────────────────────────────────────────

REMARK = ('Odoo account.account: the chart of accounts — every amount Odoo posts lands on one of these accounts')
ICON = 'sys_books_office'                           # `hap icon list`: books, for the ledger's accounts


def section_items():
    section = next(s for s in app_sections() if s['id'] == section_id())
    return section['items']


def step_create():
    """The worksheet in the existing menu group Invoicing, then moved to the top of the group: Odoo's
    Configuration menu lists Chart of Accounts before Journals."""
    who = hap.run('auth', 'whoami')
    sections = app_sections()
    app = C.app_info(APP)
    section = next((s for s in sections if s['id'] == section_id()), None)
    if APP == SALES_APP or app.get('name') != 'ERP Master' or not section or section['name'] != SECTION:
        sys.exit(f"profile {who.get('profile')!r} does not reach ERP Master › {SECTION}")
    elsewhere = [(s['name'], i['id']) for s in sections if s['id'] != section_id() for i in s['items']
                 if i['name'] == WORKSHEET]
    if elsewhere:
        sys.exit(f'{WORKSHEET} already exists in another menu group: {elsewhere}')
    before = signatures()
    wid = C.ensure_worksheet(APP, section_id(), WORKSHEET, alias=ALIAS, icon=ICON, remark=REMARK)
    C.remember('worksheets', WORKSHEET, wid)
    items = [i['id'] for i in section_items()]
    order = [wid] + [i for i in items if i != wid]
    if items != order:
        hap.run('app', 'sort-worksheets', APP, section_id(), *order)
        print(f'  {WORKSHEET} moved to the top of {SECTION}')
    back = [i['id'] for i in section_items()]
    if back != order:
        sys.exit(f'{SECTION} reads back in the order {back}, wanted {order}')
    check_untouched(before)
    for s in app_sections():
        print(f"  {s['name']:<10} {s['id']}  {[(i['name'], i['id'], i.get('alias')) for i in s['items']]}")


# ── 1 · the stored fields and Parent Account ────────────────────────────────

def step_fields():
    """Code, Account Name, Type, Payment Reconciliation, Non Trade, Parent Account, Description and Active, in one
    save of the empty worksheet. The stock Name and Description controls are reused for Account Name and
    Description (same type), so the save removes only the stock Attachment, which §1 does not have.

    A single Relation to its own worksheet always comes back two-way: the server adds the reverse — Odoo's
    child_ids — as "Child", at row 9999 with no alias, and `layout` names, places and hides it."""
    ctrls = guard(fresh=True)
    f = hap.by_name(ctrls)
    if all(n in f for n in STORED):
        print(f'  {len(STORED)} stored fields already exist; nothing saved')
        return C.show(ws())
    if set(f) - STOCK:
        sys.exit(f'{WORKSHEET} already holds {sorted(set(f) - STOCK)} — refusing to replace its controls')
    if C.records(ws(), APP):
        sys.exit(f'{WORKSHEET} has records — refusing a full save of its controls')
    hap.backup('accounts_controls_pre_fields', ctrls)
    stock = {c['controlName']: c for c in ctrls}
    controls = []
    for name in STORED:
        c = new_control(name)
        reuse = {NAME: ('Name', '名称'), DESCRIPTION: ('Description', '描述')}.get(name, ())
        old = next((stock[s] for s in reuse if s in stock and stock[s]['type'] == c['type']), None)
        if old:                                     # same type: keep the stock id (the title stays on it for now)
            c['controlId'] = old['controlId']
            c['attribute'] = old.get('attribute', 0)
        controls.append(c)
    save_controls(controls)
    back = hap.by_name(hap.controls(ws()))
    missing = [n for n in STORED if n not in back]
    if missing:
        sys.exit(f'after the save, missing {missing}')
    reverse = back[PARENT].get('sourceControlId')
    if not any(c['controlId'] == reverse for c in hap.controls(ws())):
        sys.exit(f'{PARENT} came back without its reverse ({reverse})')
    print(f"  saved {list(STORED)}; the reverse of {PARENT} is {reverse}")
    C.show(ws())


# ── 2 · Display Name and Internal Group ─────────────────────────────────────

def computed_state(ctrls=None):
    ctrls = ctrls or hap.controls(ws())
    names = {c['controlId']: c['controlName'] for c in ctrls}
    readable = lambda s: ''.join(names.get(x, x) if len(x) == 24 else x for x in (s or '').split('$'))
    f = hap.by_name(ctrls)
    return {n: dict(type=f[n]['type'], result=f[n].get('enumDefault2'), expression=readable(expression_of(f[n])))
            for n in COMPUTED if n in f}


def step_computed():
    """Display Name (Odoo display_name) and Internal Group (Odoo internal_group), text function formulas.

    `add-fields` stores a control under its client-side id and a formula saved that way computes nothing, so
    C.add_fields re-saves the whole set to re-mint the ids (the worksheet has no records yet)."""
    guard()
    f = C.fields(ws())
    missing = [n for n in COMPUTED if n not in f]
    if missing:
        if C.records(ws(), APP):
            sys.exit(f'{WORKSHEET} has records — add the formulas by hand')
        before = signatures()
        C.add_fields(ws(), [new_control(n, f) for n in missing])
        check_untouched(before)
        print(f'  added {missing}')
    ctrls = hap.controls(ws())
    f = hap.by_name(ctrls)
    wrong = [n for n in COMPUTED if expression_of(f[n]) != EXPRESSIONS[n](f) or f[n].get('enumDefault2') != TEXT_RESULT]
    if wrong:
        for n in wrong:
            f[n]['dataSource'] = function_source(EXPRESSIONS[n](f))
            f[n]['enumDefault2'] = TEXT_RESULT
        save_controls(ctrls)
        f = C.fields(ws())
        still = [n for n in COMPUTED if expression_of(f[n]) != EXPRESSIONS[n](f)]
        if still:
            sys.exit(f'formulas read back wrong: {still}')
        print(f'  rewritten {wrong}')
    for name, state in computed_state().items():
        print(f'  {name}: {json.dumps(state, ensure_ascii=False)}')


# ── 3 · layout ──────────────────────────────────────────────────────────────

def step_layout():
    """Name the server's reverse Child Accounts, place everything, move the title to Display Name, and set
    permissions, help, hints, required, No duplicates, the options, Code's format check and Parent Account's
    picker filter — in one full save, read back."""
    ctrls = guard()
    f = hap.by_name(ctrls)
    missing = [n for n in PLACE if n != CHILDREN and n not in f]
    if missing:
        sys.exit(f'controls missing — run the earlier steps first: {missing}')
    hap.backup('accounts_controls_pre_layout', ctrls)
    renamed = False
    reverse = next((c for c in ctrls if c['controlId'] == f[PARENT].get('sourceControlId')), None)
    if not reverse:
        sys.exit(f'{PARENT} has no reverse control — re-create the relation on the empty worksheet')
    if reverse['controlName'] != CHILDREN:
        print(f"  {reverse['controlName']!r} ({reverse['controlId']}) renamed {CHILDREN!r}")
        reverse['controlName'] = CHILDREN
        renamed = True
    f = hap.by_name(ctrls)
    changed = layout_differences(ctrls)
    if changed or renamed:
        for c in ctrls:
            name = c['controlName']
            if name not in PLACE:
                continue
            c.update(desired(c, f))
            c['advancedSetting'] = {**(c.get('advancedSetting') or {}), **advanced(name, f)}
            if name == TYPE:
                c['options'] = [dict(o) for o in TYPE_OPTIONS]
        save_controls(ctrls)
    left = layout_differences(hap.controls(ws()))
    if left:
        sys.exit(f'layout read back with differences: {json.dumps(left, ensure_ascii=False)}')
    print('  updated:', json.dumps(changed, ensure_ascii=False) if changed or renamed
          else 'nothing (already as specified)')
    for c in hap.controls(ws()):
        C.remember('controls', KEY + c['controlName'], c['controlId'])
    C.show(ws())


# ── 4 · rules ───────────────────────────────────────────────────────────────

RULE_RECONCILE_HIDDEN = 'Payment Reconciliation is not offered for bank, card and off-balance accounts'
RULE_NON_TRADE = 'Non Trade only for receivable and payable accounts'
RULE_RECONCILABLE = 'A receivable or payable account must be reconcilable'
MSG_RECONCILABLE = 'You cannot have a receivable/payable account that is not reconcilable.'
# rule name -> (rule type, AND-ed conditions, items, validation options). A condition is ('type', labels) — Type is
# any of — or ('unchecked', control). An interaction rule applies its action while the condition holds and the
# opposite when it does not:
#  * the hide rule leaves Payment Reconciliation visible on a new record with no Type, as Odoo's `invisible` does;
#  * "Non Trade only for…" is written as a **show** on Receivable or Payable, the house form of an "only for" rule
#    (Journals): §1's "hide when Type is not Receivable or Payable, an empty Type included" is exactly what a show
#    rule does, where a hide on "is not" would depend on how the server compares an empty option (BUILDING.md).
RULES = {
    # <label for="reconcile" invisible="account_type in ('asset_cash', 'liability_credit_card', 'off_balance')"/>
    RULE_RECONCILE_HIDDEN: (C.INTERACTION, [('type', ['Bank and Cash', 'Credit Card', 'Off-Balance Sheet'])],
                            [(C.HIDE, [RECONCILE], '')], None),
    # <field name="non_trade" invisible="account_type not in ('liability_payable', 'asset_receivable')"/>
    RULE_NON_TRADE: (C.INTERACTION, [('type', ['Receivable', 'Payable'])], [(C.SHOW, [NON_TRADE], '')], None),
    # @api.constrains _check_reconcile. Checked in the form and on API writes (check type 1); shown as the user
    # picks the Type as well as on submit (hint type 0) — HAP cannot tick the box before the save (§2).
    RULE_RECONCILABLE: (C.VALIDATION, [('type', ['Receivable', 'Payable']), ('unchecked', RECONCILE)],
                        [(C.ERROR, [RECONCILE], MSG_RECONCILABLE)], {'check_type': 1, 'hint_type': 0}),
}


def rule_payload(f, name):
    kind, conditions, items, options = RULES[name]
    group = []
    for what, arg in conditions:
        if what == 'type':
            group.append({'controlId': f[TYPE]['controlId'], 'dataType': 11, 'spliceType': 1, 'filterType': C.EQ,
                          'value': '', 'values': [OPTION_KEY[label] for label in arg], 'dynamicSource': [],
                          'isGroup': False})
        else:                                       # a checkbox that is not ticked, as Products' Sales rule
            group.append(C.cond(f[arg], C.NE, 1))
    return C.any_of(group), [C.item(t, *[f[n] for n in targets], message=msg) for t, targets, msg in items], options


def rule_state(r, names):
    groups = [sorted((names.get(c['controlId'], c['controlId']), c['filterType'],
                      tuple(sorted(LABEL_OF_KEY.get(v, v) for v in c.get('values') or [])))
                     for c in g.get('groupFilters') or []) for g in r.get('filters') or []]
    out = dict(type=r['type'], disabled=r['disabled'], groups=groups,
               items=[(i['type'], [names.get(x['controlId']) for x in i['controls']], i.get('message') or '')
                      for i in r.get('ruleItems') or []])
    if r['type'] == C.VALIDATION:
        out.update(check=r.get('checkType'), hint=r.get('hintType'))
    return out


def rule_want(name):
    kind, conditions, items, options = RULES[name]
    group = sorted((TYPE, C.EQ, tuple(sorted(arg))) if what == 'type' else (arg, C.NE, ('1',))
                   for what, arg in conditions)
    out = dict(type=kind, disabled=False, groups=[group], items=[(t, list(targets), msg) for t, targets, msg in items])
    if kind == C.VALIDATION:
        out.update(check=options['check_type'], hint=options['hint_type'])
    return out


def rule_differences():
    names = {c['controlId']: c['controlName'] for c in hap.controls(ws())}
    live = {r['name']: r for r in hap.listing('worksheet', 'rules', ws())}
    return {name: (rule_state(live[name], names) if name in live else None, rule_want(name))
            for name in RULES if name not in live or rule_state(live[name], names) != rule_want(name)}, live


def step_rules():
    guard()
    f = C.fields(ws())
    todo, live = rule_differences()
    hap.backup('accounts_rules_pre_rules', list(live.values()))
    before = signatures()
    for name in todo:
        kind = RULES[name][0]
        filters, items, options = rule_payload(f, name)
        args = ['worksheet', 'save-rule', ws(), '--name', name, '--type', str(kind),
                '--filters', json.dumps(filters, ensure_ascii=False),
                '--rule-items', json.dumps(items, ensure_ascii=False)]
        if kind == C.VALIDATION:
            args += ['--check-type', str(options['check_type']), '--hint-type', str(options['hint_type'])]
        if name in live:
            args += ['--rule-id', live[name]['ruleId']]
        hap.run(*args)
        print(f"  {'updated' if name in live else 'created'}: {name}")
    check_untouched(before)
    left, live = rule_differences()
    if left:
        sys.exit(f'rules read back with differences: {json.dumps(left, ensure_ascii=False, default=str)}')
    if not todo:
        print('  rules already as specified; nothing saved')
    names = {c['controlId']: c['controlName'] for c in hap.controls(ws())}
    for name, r in live.items():
        C.remember('rules', KEY + name, r['ruleId'])
        print(f"  {r['ruleId']}  {name}: {json.dumps(rule_state(r, names), ensure_ascii=False)}")


# ── 5 · automation A ────────────────────────────────────────────────────────

AUTOMATION = KEY + 'Payment Reconciliation follows Type'
AUTOMATION_DESC = ("Odoo account.account _compute_reconcile: when an account is created or its Type changes, Payment "
                   "Reconciliation is unchecked for Income, Other Income, Expenses, Other Expenses, Depreciation, Cost "
                   "of Revenue, Equity and Current Year Earnings; checked for Receivable and Payable; unchecked for "
                   "Bank and Cash, Credit Card and Off-Balance Sheet; and left as it is for every other asset or "
                   "liability type.")
TRIGGER_NAME = 'When an account is created or its Type changes'
GATEWAY = 'What does the Type do to Payment Reconciliation?'
CREATE_OR_UPDATE = '2'                              # worksheet trigger: 新增或更新记录, narrowed to Type on update
# §1's table, branch for branch: (path name, Type labels, update step name or None, the value written)
PATHS = [
    ('Income, Expense or Equity — unchecked',
     ['Income', 'Other Income', 'Expenses', 'Other Expenses', 'Depreciation', 'Cost of Revenue', 'Equity',
      'Current Year Earnings'], 'Uncheck Payment Reconciliation (income, expense, equity)', '0'),
    ('Receivable or Payable — checked', ['Receivable', 'Payable'], 'Check Payment Reconciliation', '1'),
    ('Bank and Cash, Credit Card or Off-Balance Sheet — unchecked',
     ['Bank and Cash', 'Credit Card', 'Off-Balance Sheet'],
     'Uncheck Payment Reconciliation (bank, card, off-balance)', '0'),
    ('Any other asset or liability type — left as it is',
     ['Current Assets', 'Non-current Assets', 'Prepayments', 'Fixed Assets', 'Current Liabilities',
      'Non-current Liabilities'], None, None),
]
IS_ANY_OF = '1'                                     # workflow conditionId 是其中一个
SWITCH = 36
EXCLUSIVE = 2                                       # gatewayType 2 = 唯一分支: the first matching path runs


def path_for(label):
    return next((p for p in PATHS if label in p[1]), None)


def expected_run(label):
    """What run_path must report for a run on this Type: the path's name, or NO_STEP for the path that writes
    nothing (a run's detail never lists a path node)."""
    name, _, step, _ = path_for(label)
    return name if step else NO_STEP


def type_condition(trigger, f, labels):
    """A path's condition as the server stores it: Type (on the trigger record) is any of the labels."""
    return [[{'nodeId': trigger, 'filedId': f[TYPE]['controlId'], 'filedValue': TYPE, 'filedTypeId': 11,
              'enumDefault': 0, 'conditionId': IS_ANY_OF, 'sourceType': 0,
              'conditionValues': [{'value': {'key': OPTION_KEY[label], 'value': label, 'isDeleted': False}}
                                  for label in labels]}]]


def automation_nodes(f):
    """The gateway, its four paths and the three update steps, for `batch-add`. Path names and conditions and
    the steps' field writes are written again afterwards and read back: batch-add is known to drop them."""
    def path(i, name, labels, step, value):
        out = {'alias': f'path{i}', 'name': name, 'condition': {'logic': 'and', 'items': [
            {'left': {'node': {'nodeAlias': 'trigger'}, 'fieldId': f[TYPE]['controlId'], '_filedTypeId': 11,
                      '_filedValue': TYPE},
             'op': 'in', 'right': {'kind': 'literal', 'values': [
                 {'key': OPTION_KEY[label], 'value': label, 'isDeleted': False} for label in labels]}}]}}
        if step:
            out['nodes'] = [{'nodeAlias': f'step{i}', 'nodeType': 'update_record', 'name': step,
                             'config': {'target': {'node': {'nodeAlias': 'trigger'}}, 'worksheet': ws(),
                                        'fields': [{'fieldId': f[RECONCILE]['controlId'], 'type': SWITCH,
                                                    'value': value}]}}]
        return out
    return [{'nodeAlias': 'which', 'nodeType': 'branch', 'name': GATEWAY,
             'config': {'mode': 'exclusive', 'paths': [path(i, *p) for i, p in enumerate(PATHS)]}}]


def nodes_by_name(pid):
    proc = hap.run('workflow', 'node', 'list', pid)
    return proc, {n['name']: n for n in proc['flowNodeMap'].values()}


def node_get(pid, node_id):
    d = hap.run('workflow', 'node', 'get', pid, node_id)
    return d.get('data', d) if isinstance(d, dict) else {}


def automation_pid():
    pid = hap.ids().get('workflows', {}).get(AUTOMATION)
    if pid:
        return pid
    live = {w['name']: w.get('id') or w.get('processId') for w in hap.listing('workflow', 'list', APP)}
    return live.get(AUTOMATION)


def trigger_state(pid, start):
    t = node_get(pid, start)
    return dict(appId=t.get('appId'), triggerId=str(t.get('triggerId')), fields=sorted(t.get('assignFieldIds') or []),
                condition=t.get('operateCondition') or [], name=t.get('name'))


def path_state(pid, node_id):
    d = node_get(pid, node_id)
    return [[(c.get('nodeId'), c.get('filedId'), str(c.get('conditionId')),
              sorted(((v.get('value') or {}).get('key') if isinstance(v.get('value'), dict) else v.get('value'))
                     for v in c.get('conditionValues') or []))
             for c in group] for group in d.get('conditions') or d.get('operateCondition') or []]


def step_state(pid, node_id):
    d = node_get(pid, node_id)
    return dict(selectNodeId=d.get('selectNodeId'), appId=d.get('appId'), isException=d.get('isException'),
                fields=[(x.get('fieldId'), str(x.get('fieldValue')), x.get('nodeId') or '') for x in
                        d.get('fields') or []])


def automation_differences(pid, f):
    """automation A read back against PATHS: the trigger, the gateway and its paths in order, every condition,
    every step's field write, and the published state."""
    proc, byname = nodes_by_name(pid)
    start = proc['startEventId']
    out = []
    t = trigger_state(pid, start)
    want = dict(appId=ws(), triggerId=CREATE_OR_UPDATE, fields=[f[TYPE]['controlId']], condition=[],
                name=TRIGGER_NAME)
    if t != want:
        out.append(f'trigger {t} != {want}')
    gateway = byname.get(GATEWAY)
    if not gateway or gateway.get('typeId') != 1:
        return out + [f'gateway {GATEWAY!r} missing']
    if proc['flowNodeMap'][start].get('nextId') != gateway['id']:
        out.append('the trigger does not run into the gateway')
    if gateway.get('gatewayType') != EXCLUSIVE:
        out.append(f"gatewayType {gateway.get('gatewayType')}, want {EXCLUSIVE}")
    if gateway.get('nextId') not in ('99', '', None):
        out.append(f"the gateway runs into {gateway.get('nextId')} — nothing should follow it")
    paths = {p.get('name'): p for p in (proc['flowNodeMap'][i] for i in gateway.get('flowIds') or [])}
    if sorted(paths) != sorted(p[0] for p in PATHS) or len(gateway.get('flowIds') or []) != len(PATHS):
        out.append(f"paths {list(paths)}")
    for name, labels, step, value in PATHS:
        node = paths.get(name)
        if not node:
            continue
        want = [[(start, f[TYPE]['controlId'], IS_ANY_OF, sorted(OPTION_KEY[label] for label in labels))]]
        if path_state(pid, node['id']) != want:
            out.append(f'path {name!r}: condition {path_state(pid, node["id"])}')
        nxt = proc['flowNodeMap'].get(node.get('nextId'))
        if step is None:
            if nxt:
                out.append(f'path {name!r} runs into {nxt.get("name")!r}; it must write nothing')
            continue
        if not nxt or nxt.get('name') != step or nxt.get('typeId') != 6:
            out.append(f'path {name!r} runs into {nxt and nxt.get("name")!r}, want {step!r}')
            continue
        if nxt.get('nextId') not in ('', '99', None):
            out.append(f'{step!r} is followed by {nxt.get("nextId")}')
        s = step_state(pid, nxt['id'])
        if (s['selectNodeId'], s['appId'], bool(s['isException']), s['fields']) != \
                (start, ws(), False, [(f[RECONCILE]['controlId'], value, '')]):
            out.append(f'{step!r}: {s}')
    info = hap.run('workflow', 'get', pid)
    info = info.get('data', info)
    if (info.get('name'), info.get('explain') or '') != (AUTOMATION, AUTOMATION_DESC):
        out.append(f"name / description {info.get('name')!r} / {info.get('explain')!r}")
    if not info.get('enabled') or info.get('publishStatus') != 2:
        out.append(f"enabled={info.get('enabled')} publishStatus={info.get('publishStatus')}")
    return out


def set_path(pid, node, name, condition):
    """A branch path's condition (node save --type 2 wants `operateCondition`) and its name (only `node rename`
    sets it). Returns True when something was written."""
    changed = False
    if path_state(pid, node['id']) != [[(c['nodeId'], c['filedId'], c['conditionId'],
                                         sorted(v['value']['key'] for v in c['conditionValues']))
                                        for c in group] for group in condition]:
        hap.run('workflow', 'node', 'save', pid, node['id'], '--type', '2',
                '-c', json.dumps({'operateCondition': condition}, ensure_ascii=False), '-n', name)
        changed = True
    if node.get('name') != name:
        hap.run('workflow', 'node', 'rename', pid, node['id'], '-n', name)
        changed = True
    return changed


def set_step(pid, node, f, value, start):
    """An update step writes Payment Reconciliation = value on the trigger record, and nothing else."""
    s = step_state(pid, node['id'])
    if s['selectNodeId'] == start and s['fields'] == [(f[RECONCILE]['controlId'], value, '')] and not s['isException']:
        return False
    hap.run('workflow', 'node', 'save', pid, node['id'], '--type', '6', '-c', json.dumps(
        {'actionId': '2', 'appId': ws(), 'appType': 1, 'selectNodeId': start,
         'fields': [{'fieldId': f[RECONCILE]['controlId'], 'type': SWITCH, 'addType': 0, 'fieldValue': value,
                     'fieldValueId': '', 'nodeId': ''}]}, ensure_ascii=False), '-n', node['name'])
    return True


def step_automation():
    """A · Payment Reconciliation follows Type — Odoo's _compute_reconcile as a worksheet-event workflow: on a record
    created, or its Type changed, a gateway with §1's four paths; three write the box, the fourth writes nothing.

    Creates the workflow if it is missing, then brings every part up to spec in place and republishes only when
    something was written. No step is ever deleted."""
    guard()
    f = C.fields(ws())
    pid = automation_pid()
    before = signatures()
    changed = False
    if not pid:
        out = hap.run('workflow', 'create', '-c', hap.ids()['org'], '-n', AUTOMATION, '-a', APP,
                      '--type', 'worksheet', '-d', AUTOMATION_DESC)
        data_ = out.get('data', out) if isinstance(out, dict) else out
        pid = data_ if isinstance(data_, str) else (data_.get('id') or data_.get('processId'))
        if not pid:
            sys.exit(f'no process id in `workflow create` output: {out}')
        C.remember('workflows', AUTOMATION, pid)
        print(f'  created {AUTOMATION}: {pid}')
    C.remember('workflows', AUTOMATION, pid)
    proc, byname = nodes_by_name(pid)
    print('  backup:', hap.backup('accounts_automation_pre_automation', proc))
    if GATEWAY not in byname:
        hap.run('workflow', 'node', 'batch-add', pid, '--nodes', json.dumps(automation_nodes(f), ensure_ascii=False),
                '--trigger-worksheet', ws(), '--trigger-event', 'create_or_update',
                '--trigger-fields', f[TYPE]['controlId'], '--trigger-alias', 'trigger')
        proc, byname = nodes_by_name(pid)
        changed = True
        print('  gateway, paths and steps added')
    start = proc['startEventId']
    t = trigger_state(pid, start)
    if (t['appId'], t['triggerId'], t['fields'], t['condition']) != (ws(), CREATE_OR_UPDATE,
                                                                     [f[TYPE]['controlId']], []):
        hap.run('workflow', 'node', 'save', pid, start, '--type', '0', '-n', TRIGGER_NAME, '-c', json.dumps(
            {'appId': ws(), 'appType': 1, 'triggerId': CREATE_OR_UPDATE, 'assignFieldIds': [f[TYPE]['controlId']],
             'operateCondition': [], 'returns': []}))
        changed = True
        print('  trigger rewritten')
    if trigger_state(pid, start)['name'] != TRIGGER_NAME:
        hap.run('workflow', 'node', 'rename', pid, start, '-n', TRIGGER_NAME)
        changed = True
    info = hap.run('workflow', 'get', pid)
    info = info.get('data', info)
    if (info.get('name'), info.get('explain') or '') != (AUTOMATION, AUTOMATION_DESC):
        hap.run('workflow', 'update', pid, '-n', AUTOMATION, '-d', AUTOMATION_DESC)
        changed = True
    proc, byname = nodes_by_name(pid)
    gateway = byname[GATEWAY]
    paths = [proc['flowNodeMap'][i] for i in gateway.get('flowIds') or []]
    if len(paths) != len(PATHS):
        sys.exit(f'{GATEWAY}: {len(paths)} paths, want {len(PATHS)} — left for a person to look at')
    print(f"  paths as the gateway lists them: {[p.get('name') for p in paths]}")
    # A path is recognised by the update step it runs into — batch-add names steps as given, but may drop a path's
    # own name and condition — and the path that writes nothing by having no step. Never by position.
    by_step = {}
    for node in paths:
        nxt = proc['flowNodeMap'].get(node.get('nextId'))
        by_step.setdefault(nxt.get('name') if nxt else None, []).append((node, nxt))
    for name, labels, step, value in PATHS:
        found = by_step.get(step) or []
        if len(found) != 1:
            sys.exit(f'{GATEWAY}: {len(found)} path(s) run into {step!r} — left for a person to look at')
        node, nxt = found[0]
        if step and nxt.get('typeId') != 6:
            sys.exit(f'path {node.get("name")!r} runs into {nxt.get("name")!r}, which is not an update step')
        changed |= set_path(pid, node, name, type_condition(start, f, labels))
        if step:
            changed |= set_step(pid, nxt, f, value, start)
    info = hap.run('workflow', 'get', pid)
    info = info.get('data', info)
    if changed or not info.get('enabled') or info.get('publishStatus') != 2:
        result = C.publish(pid)
        print('  published:', result)
        if not result.get('isPublish'):
            sys.exit(f'publish failed: {result}')
    else:
        print('  already built and published; nothing written')
    check_untouched(before)
    left = automation_differences(pid, C.fields(ws()))
    if left:
        sys.exit('automation A read back with differences:\n  ' + '\n  '.join(left))
    print(C.structure(pid))


# ── 6 · buttons ─────────────────────────────────────────────────────────────

MSG_ARCHIVE = 'Are you sure that you want to archive this record?'
BUTTON_STEP = {'Archive': ('Archive the account', '0'), 'Unarchive': ('Unarchive the account', '1')}


def step_buttons():
    """Odoo ⚙ Actions › Archive / Unarchive, as on Journals: shown by Active, one update step each."""
    guard()
    active = C.fields(ws())[ACTIVE]['controlId']
    when = lambda op: {'type': 'group', 'logic': 'AND', 'children': [
        {'type': 'condition', 'field': active, 'operator': op, 'value': ['1']}]}
    buttons = [
        ({'name': 'Archive', 'type': 'triggerWorkflow', 'enableWhen': when('eq'), 'isBatch': True,
          'confirm': True, 'confirmMsg': MSG_ARCHIVE, 'sureName': 'Archive', 'cancelName': 'Cancel'},
         [{'fieldId': active, 'value': '0'}], BUTTON_STEP['Archive'][0]),
        ({'name': 'Unarchive', 'type': 'triggerWorkflow', 'enableWhen': when('ne'), 'isBatch': True},
         [{'fieldId': active, 'value': '1'}], BUTTON_STEP['Unarchive'][0]),
    ]
    before = signatures()
    C.upsert_buttons(ws(), APP, buttons, KEY, 'accounts_buttons_pre_buttons')
    check_untouched(before)
    problems = button_differences()
    if problems:
        sys.exit('buttons read back with differences:\n  ' + '\n  '.join(problems))
    for name in BUTTONS:
        print(C.structure(hap.ids()['workflows'][KEY + name]))


def button_differences():
    ctrls = hap.controls(ws())
    names = {c['controlId']: c['controlName'] for c in ctrls}
    active = hap.by_name(ctrls)[ACTIVE]['controlId']
    live = {b['name']: b for b in hap.listing('worksheet', 'custom-actions', ws())}
    out = []
    if sorted(live) != sorted(BUTTONS):
        out.append(f'buttons {sorted(live)}')
    for name, op, confirm in (('Archive', C.EQ, MSG_ARCHIVE), ('Unarchive', C.NE, '')):
        b = live.get(name)
        if not b:
            continue
        conds = [(names.get(x['controlId']), x['filterType'], x.get('values')) for x in b.get('filters') or []]
        if conds != [(ACTIVE, op, ['1'])] or (b.get('confirmMsg') or '') != confirm:
            out.append(f"button {name}: filters={conds} confirm={b.get('confirmMsg')!r}")
        pid = hap.ids().get('workflows', {}).get(KEY + name)
        if not pid:
            out.append(f'no workflow id for {name}')
            continue
        proc, byname = nodes_by_name(pid)
        step, value = BUTTON_STEP[name]
        start = proc['startEventId']
        node = byname.get(step)
        if not node or proc['flowNodeMap'][start].get('nextId') != node['id']:
            out.append(f'{name} workflow: the trigger does not run into {step!r}')
            continue
        s = step_state(pid, node['id'])
        if s['selectNodeId'] != start or s['fields'] != [(active, value, '')] or s['isException']:
            out.append(f'{name} workflow step: {s}')
        info = hap.run('workflow', 'get', pid)
        info = info.get('data', info)
        if not info.get('enabled') or info.get('publishStatus') != 2:
            out.append(f"{name} workflow enabled={info.get('enabled')} publishStatus={info.get('publishStatus')}")
    return out


# ── 7 · views ───────────────────────────────────────────────────────────────

COLUMNS = (CODE, NAME, TYPE, RECONCILE)             # Odoo's list, with its optional columns left off
TEXT, LIKE = 2, 1                                   # a text quick filter: dataType 2, filterType 1 (contains)


def view_specs(f):
    """Chart of Accounts (active accounts) and Archived (the *Inactive Accounts* filter): Odoo's list columns,
    `_order = "code, placeholder_code"` as Code A→Z. The Type quick filter takes several types at once, which is
    how Odoo's Receivable and Payable filters are covered; Internal Group covers its Equity · Assets · Liability ·
    Income · Expenses filters.

    The Internal Group quick filter is written the way the view editor saves one on a text formula: the editor
    redefines a type-53 control to its result type (pd-openweb `redefineComplexControl`), so it is a **text**
    filter — dataType 2, filterType 1 ("contains", the editor's default) — not a list of options."""
    columns = [f[n]['controlId'] for n in COLUMNS]
    sort = C.sort_spec([f[CODE]])
    quick = [{'fieldId': f[TYPE]['controlId'], 'selectionType': 'multiple', 'displayType': 'dropdown'},
             {'controlId': f[GROUP]['controlId'], 'dataType': TEXT, 'filterType': LIKE}]
    return {
        VIEW: (dict(viewType='table', filter=C.switch_filter(f[ACTIVE], 'eq'), tableFields=columns,
                    quickFilters=quick), sort, columns),
        ARCHIVED: (dict(viewType='table', filter=C.switch_filter(f[ACTIVE], 'ne'), tableFields=columns), sort,
                   columns),
    }


def view_state(info, names):
    quick = []
    for q in info.get('fastFilters') or []:
        s = q.get('advancedSetting') or {}
        quick.append((names.get(q['controlId']), q.get('dataType'), q.get('filterType'), s.get('allowitem'),
                      s.get('direction')))
    return dict(columns=[names.get(x) for x in info.get('showControls') or []],
                sort=[(names.get(s['controlId']), s['isAsc']) for s in info.get('moreSort') or []],
                sortCid=names.get(info.get('sortCid')), sortType=info.get('sortType'),
                filters=[(names.get(x['controlId']), x['filterType'], x.get('values')) for x in info.get('filters') or []],
                quick=quick)


def view_want(name):
    quick = [(TYPE, 11, 0, '2', '2'), (GROUP, TEXT, LIKE, None, None)] if name == VIEW else []
    return dict(columns=list(COLUMNS), sort=[(CODE, True)], sortCid=CODE, sortType=2,
                filters=[(ACTIVE, C.EQ if name == VIEW else C.NE, ['1'])], quick=quick)


def view_differences():
    names = {c['controlId']: c['controlName'] for c in hap.controls(ws())}
    live = hap.listing('worksheet', 'view', 'list', ws(), '-a', APP)
    out = {}
    if [v['name'] for v in live] != [VIEW, ARCHIVED]:
        out['order'] = [v['name'] for v in live]
    for name in (VIEW, ARCHIVED):
        v = next((x for x in live if x['name'] == name), None)
        state = view_state(C.view_info(ws(), APP, v['viewId']), names) if v else None
        if state != view_want(name):
            out[name] = (state, view_want(name))
    return out


def step_views():
    guard()
    f = C.fields(ws())
    todo = view_differences()
    if todo:
        before = signatures()
        views = view_specs(f)
        for name, vid in C.upsert_views(ws(), APP, views, 'accounts_views_pre_views', default_view=VIEW).items():
            C.remember('views', KEY + name, vid)
        print('  order:', C.sort_views(ws(), APP, list(views)))
        check_untouched(before)
    left = view_differences()
    if left:
        sys.exit(f'views read back with differences: {json.dumps(left, ensure_ascii=False, default=str)}')
    print('  updated:', ', '.join(todo) if todo else 'nothing (already as specified)')
    for v in hap.listing('worksheet', 'view', 'list', ws(), '-a', APP):
        C.remember('views', KEY + v['name'], v['viewId'])
    C.print_views(ws(), APP)
    names = {c['controlId']: c['controlName'] for c in hap.controls(ws())}
    for v in hap.listing('worksheet', 'view', 'list', ws(), '-a', APP):
        info = C.view_info(ws(), APP, v['viewId'])
        print(f"  {v['name']} quick filters: {json.dumps(info.get('fastFilters'), ensure_ascii=False)}"
              if info.get('fastFilters') else f"  {v['name']}: no quick filters")


# ── 8 · roles ───────────────────────────────────────────────────────────────

def step_roles():
    """roles.py owns the app's roles; its ORDER and its four matrices now carry Chart of Accounts with the rule
    Products has — Accounting Administrator full, the other three view (Odoo's access list: write, create and
    delete on account.account for group_account_manager alone). Per-field hiding is part B's."""
    import roles
    before = signatures()
    roles.step_create()
    check_untouched(before)
    return roles.step_check()


# ── 9 · seed, verify and the automation's runs ──────────────────────────────

def reference_accounts():
    """The 87 accounts of the extract, in code order, with the Type labels checked against Odoo's selection."""
    d = data()
    if [(t['key'], t['label']) for t in d['account_types']] != [(odoo, label) for odoo, label, _ in TYPES]:
        sys.exit('casimir-accounts.json account_types differ from TYPES')
    return d['accounts']


def listed(v):
    if isinstance(v, str):
        v = json.loads(v) if v.startswith('[') else []
    return v if isinstance(v, list) else []


def option_label(v):
    labels = [x.get('value') if isinstance(x, dict) else x for x in listed(v)]
    return labels[0] if labels else None


def relation(value):
    return [(x.get('sid'), x.get('name')) for x in listed(value) if isinstance(x, dict)]


def flag(v):
    return str(v) in ('1', 'True', 'true')


def read_account(rowid):
    """One account through `record get` (by alias): `record list` returns only the default view's columns."""
    d = hap.run('worksheet', 'record', 'get', ws(), rowid, '-a', APP)['data']
    parents = relation(d.get('parent_id'))
    children = d.get('child_ids')
    return dict(rowid=rowid, code=d.get('code') or '', name=d.get('name') or '', display_name=d.get('display_name') or '',
                type=option_label(d.get('account_type')), internal_group=d.get('internal_group') or '',
                reconcile=flag(d.get('reconcile')), non_trade=flag(d.get('non_trade')), active=flag(d.get('active')),
                parent=parents[0][1] if parents else None, parent_rowid=parents[0][0] if parents else None,
                description=d.get('description') or '',
                children=children if isinstance(children, int) else len(relation(children)))


def read_accounts():
    """Every account, archived or not, by Code — each one read with `record get`."""
    return {a['code']: a for a in (read_account(r['rowid']) for r in C.records(ws(), APP))}


def record_index():
    """{Code: (rowid, Account Name)} of every account, archived or not, from one `record list`. It returns only the
    default view's columns; Code and Account Name are two of them, and a row without them is read with `record get`."""
    f = C.fields(ws())
    out = {}
    for r in C.records(ws(), APP):
        code, name = r.get(f[CODE]['controlId']), r.get(f[NAME]['controlId'])
        if code in (None, ''):
            got = read_account(r['rowid'])
            code, name = got['code'], got['name']
        out[code] = (r['rowid'], name)
    return out


def expected(a):
    label = LABEL_OF_ODOO[a['type']]
    return dict(code=a['code'], name=a['name'], display_name=f"{a['code']} {a['name']}".strip(), type=label,
                internal_group=GROUP_OF_LABEL[label], reconcile=a['reconcile'], non_trade=a['non_trade'],
                active=a['active'], parent=None, description='')


def differences(live, want, keys=None):
    return {k: (live.get(k), v) for k, v in want.items() if (keys is None or k in keys) and live.get(k) != v}


WRITTEN = ('code', 'name', 'type', 'reconcile', 'non_trade', 'active', 'parent', 'description')


def values_for(f, want, keys):
    """The record write for the stored fields in `keys`. Active is always explicit on an API write."""
    cid = lambda n: f[n]['controlId']
    field = {'code': lambda: (CODE, want['code']), 'name': lambda: (NAME, want['name']),
             'type': lambda: (TYPE, [OPTION_KEY[want['type']]] if want['type'] else []),
             'reconcile': lambda: (RECONCILE, 1 if want['reconcile'] else 0),
             'non_trade': lambda: (NON_TRADE, 1 if want['non_trade'] else 0),
             'active': lambda: (ACTIVE, 1 if want['active'] else 0),
             'parent': lambda: (PARENT, [want['parent_rowid']] if want.get('parent_rowid') else []),
             'description': lambda: (DESCRIPTION, want.get('description') or '')}
    return [{'id': cid(field[k]()[0]), 'value': field[k]()[1]} for k in keys]


PAGE = 100


def run_page(pid, page=1):
    """One page of a workflow's runs, newest first. A read, so a dropped connection is retried."""
    for tries in range(4):
        try:
            out = hap.run('approval', 'history', '--process-id', pid, '-n', str(PAGE), '-p', str(page))
            return (out or {}).get('data') or []
        except RuntimeError as error:
            if tries == 3 or 'ConnectionError' not in str(error):
                raise
            time.sleep(5)


def all_runs(pid):
    """Every run of a workflow, newest first. The history's `count` is **the number of rows on the page returned**,
    not the total (`-n 50` gives 50, then 37 on page 2), so the total is found by paging."""
    rows, page = [], 1
    while True:
        got = run_page(pid, page)
        rows += got
        if len(got) < PAGE:
            return rows
        page += 1


def run_count(pid):
    return len(all_runs(pid))


def run_snapshot(pid):
    """The runs there are now, to tell new ones apart later: their ids, and the latest creation time among them."""
    rows = all_runs(pid)
    return {r['id'] for r in rows}, max((r.get('createDate') or '' for r in rows), default='')


def wait_new_runs(pid, snapshot, n, seconds=120, settle=3):
    """The runs started since `snapshot`, once there are `n` of them and none is still running (status 1).

    New runs are told apart **by instance id**, never by position or by the list's length: the history listing
    can lag by a row, and a run registers some seconds after the write that starts it (5 s here). With n = 0 it
    simply waits `seconds` and returns whatever appeared. Newest first."""
    ids, latest = snapshot
    deadline = time.time() + seconds
    while True:
        rows = all_runs(pid)
        new = [r for r in rows if r['id'] not in ids and (r.get('createDate') or '') >= latest]
        done = n > 0 and len(new) >= n and all(r.get('status') != 1 for r in new)
        if done or time.time() > deadline:
            if done and settle:                     # a second run would register within the same few seconds
                time.sleep(settle)
                rows = all_runs(pid)
                new = [r for r in rows if r['id'] not in ids and (r.get('createDate') or '') >= latest]
            return new
        time.sleep(2)


def run_nodes(instance_id):
    d = hap.run('approval', 'history-detail', instance_id)
    d = d.get('data', d) if isinstance(d, dict) else {}
    return [((w.get('flowNode') or {}).get('type'), (w.get('flowNode') or {}).get('name')) for w in d.get('works') or []]


NO_STEP = 'no update step (the path that writes nothing, or no path at all)'


def run_path(instance_id):
    """Which of §1's paths a run took, from the nodes its detail lists. The detail lists the trigger, the gateway
    and the steps that ran — **never a branch path node** — so a path is known by its update step, and a run
    through the fourth path (which has none) cannot be told apart from a run that matched no path."""
    passed = [name for _, name in run_nodes(instance_id)]
    for name, _, step, _ in PATHS:
        if name in passed or (step and step in passed):
            return name
    return NO_STEP if GATEWAY in passed else 'did not reach the gateway'


def step_seed(*only):
    """The 87 accounts, matched by Code: created when missing, and only the differing stored fields written when
    not. Each is read back at once. Automation A fires on every create (and on a Type change), so the step then
    waits for those runs to finish and compares every account — Payment Reconciliation included — with the
    extract. `only` limits it to codes."""
    guard()
    f = C.fields(ws())
    pid = automation_pid()
    if not pid:
        sys.exit('automation A is not built — run `automation` first: the seed is meant to go through it')
    accounts = [a for a in reference_accounts() if not only or a['code'] in only]
    live = read_accounts()
    hap.backup('accounts_records_pre_seed', live)
    runs_before = run_snapshot(pid)
    before = signatures()
    created, updated, type_changes = [], [], 0
    for a in accounts:
        want = expected(a)
        have = live.get(a['code'])
        if have and not differences(have, want, WRITTEN):
            continue
        if have:
            keys = [k for k in WRITTEN if have.get(k) != want[k]]
            hap.run('worksheet', 'record', 'update', ws(), have['rowid'], '-a', APP, '--fields-json',
                    json.dumps(values_for(f, want, keys), ensure_ascii=False))
            rowid = have['rowid']
            type_changes += 'type' in keys
            updated.append((a['code'], keys))
            print(f"  updated {a['code']} {a['name']}: {keys}")
        else:
            keys = [k for k in WRITTEN if k not in ('parent', 'description')]
            rowid = C.row_id(hap.run('worksheet', 'record', 'create', ws(), '-a', APP, '--fields-json',
                                     json.dumps(values_for(f, want, keys), ensure_ascii=False)))
            created.append(a['code'])
            print(f"  created {a['code']} {a['name']}: {rowid}")
        got = read_account(rowid)
        wrong = differences(got, want, [k for k in WRITTEN if k != 'reconcile'])
        if wrong:
            sys.exit(f"{a['code']}: read back {wrong}")
        C.remember('records', KEY + a['code'], rowid)
    check_untouched(before)
    expect = len(created) + type_changes
    if expect:
        print(f'  waiting for automation A: {expect} run(s) expected ({len(created)} creates, {type_changes} Type '
              f'changes), {len(runs_before[0])} before')
        runs = wait_new_runs(pid, runs_before, expect, seconds=60 + 6 * expect)
        print(f'  automation A: {len(runs)} new run(s); statuses {sorted({r.get("status") for r in runs})} '
              f'(2 = completed) — `runs` reads the path each one took')
    for code, (rowid, _) in record_index().items():
        if code in {a['code'] for a in accounts}:
            C.remember('records', KEY + code, rowid)
    return step_verify(*only)


def step_verify(*only):
    """Every account of the extract against the live worksheet — Code, Account Name, Type, Payment Reconciliation,
    Non Trade, Active, no parent, no description — plus the computed Display Name and Internal Group."""
    accounts = [a for a in reference_accounts() if not only or a['code'] in only]
    live = read_accounts()
    bad = 0
    for a in accounts:
        have = live.get(a['code'])
        if not have:
            print(f"  MISSING  {a['code']} {a['name']}")
            bad += 1
            continue
        diffs = differences(have, expected(a))
        bad += bool(diffs)
        print(f"  {'OK  ' if not diffs else 'DIFF'}  {have['display_name']:<44} {have['type']:<24} "
              f"{have['internal_group']:<9} reconcile={int(have['reconcile'])} non_trade={int(have['non_trade'])} "
              f"active={int(have['active'])}" + (f'  <- {diffs}' if diffs else ''))
    extra = sorted(f"{c} {v['name']}" for c, v in live.items() if c not in {a['code'] for a in reference_accounts()})
    by_type = {}
    for a in accounts:
        by_type[LABEL_OF_ODOO[a['type']]] = by_type.get(LABEL_OF_ODOO[a['type']], 0) + 1
    print(f'  {len(accounts)} accounts in the extract; {bad} missing or differing; {len(extra)} not in the extract '
          f'{extra}')
    print(f'  reconcile on: {sorted(c for c, v in live.items() if v["reconcile"] and c in {a["code"] for a in accounts})}')
    return bad


def step_runs(*args):
    """automation A's runs: how many, their status, and the path each one took (read from each run's detail)."""
    pid = automation_pid()
    if not pid:
        sys.exit('automation A is not built')
    limit = int(args[0]) if args else None
    rows = all_runs(pid)
    rows = rows[:limit] if limit else rows
    # A run's title is the record's title when it ran — the Display Name — which ties a run to a seeded account.
    seeded = {f"{a['code']} {a['name']}": LABEL_OF_ODOO[a['type']] for a in reference_accounts()}
    tally, statuses, per_account, wrong = {}, {}, {}, []
    for r in rows:
        path = run_path(r['id'])
        tally.setdefault(path, []).append(r.get('title'))
        statuses[r.get('status')] = statuses.get(r.get('status'), 0) + 1
        label = seeded.get(r.get('title'))
        if label:
            per_account[r['title']] = per_account.get(r['title'], 0) + 1
            if path != expected_run(label):
                wrong.append((r['title'], label, path))
    print(f'  {len(rows)} run(s) read; status counts {statuses} (2 completed · 1 running · 3 stopped · 4 failed)')
    for path, titles in tally.items():
        print(f'  {len(titles):>3}  {path}')
    print(f'  seeded accounts with a run: {len(per_account)} of {len(seeded)}; with more than one: '
          f'{sorted(t for t, n in per_account.items() if n > 1)}; without: {sorted(set(seeded) - set(per_account))}')
    print(f'  runs whose path is not the one the account\'s Type calls for: {wrong}')
    return len(wrong)


def step_account(*codes):
    live = read_accounts()
    for code in codes or sorted(live):
        a = live.get(code)
        print(f'  {code}: ' + (json.dumps(a, ensure_ascii=False) if a else 'no such account'))


def step_order():
    """Each view's records in the order the view returns them (its own filter and sort)."""
    code = C.fields(ws())[CODE]['controlId']
    for v in hap.listing('worksheet', 'view', 'list', ws(), '-a', APP):
        res = hap.run('worksheet', 'record', 'list', ws(), '-a', APP, '-n', '200', '--view-id', v['viewId'],
                      '--use-field-id-as-key')
        d = res.get('data', res) if isinstance(res, dict) else res
        rows = (d.get('rows') if isinstance(d, dict) else d) or []
        codes = [r.get(code) for r in rows]
        print(f"  {v['name']} ({len(rows)}): " + ', '.join(str(c) for c in codes))
        print(f"    sorted A→Z as text: {codes == sorted(codes)}")


# ── self-check: what §1 relies on the platform for, through the CLI ─────────

def attempt(*args):
    """Run a write expected to be refused; return (refused, message)."""
    try:
        out = hap.run(*args)
    except RuntimeError as error:
        return True, str(error)[:400]
    d = out.get('data', out) if isinstance(out, dict) else {}
    code = out.get('resultCode') if isinstance(out, dict) else None
    inner = d.get('resultCode') if isinstance(d, dict) else None
    return (code not in (None, 1) or inner not in (None, 1)), json.dumps(out, ensure_ascii=False)[:400]


# The walk through all 19 types, in Odoo's order, on TEST Account. (Type, Payment Reconciliation written with it
# or None, what it must read afterwards.) Where the box is not written it keeps the previous value, so the
# "left as it is" types are proved both unchecked (Current Assets, Current Liabilities) and checked (Prepayments,
# Fixed Assets), and the "unchecked" ones are always reached with the box ticked.
WALK = [
    ('Receivable', 1, True), ('Bank and Cash', None, False), ('Current Assets', None, False),
    ('Non-current Assets', 1, True), ('Prepayments', None, True), ('Fixed Assets', None, True),
    ('Payable', None, True), ('Credit Card', None, False), ('Current Liabilities', None, False),
    ('Non-current Liabilities', 1, True), ('Equity', None, False), ('Current Year Earnings', 1, False),
    ('Income', 1, False), ('Other Income', 1, False), ('Expenses', 1, False), ('Other Expenses', 1, False),
    ('Depreciation', 1, False), ('Cost of Revenue', 1, False), ('Off-Balance Sheet', 1, False),
]


def step_selfcheck():
    """Prove through the CLI what §1 asks of the platform, on TEST Account (TEST01), which is left active as a
    Current Assets account with the box unchecked:

      1. automation A on a create and on every one of the 19 types — the run, the path it took (by instance id)
         and the box — with Internal Group read back each time;
      2. an empty Type (the API ignores Required), and a write that sends Type unchanged;
      3. the validation rule on API writes — including a Type change it refuses before automation A can run;
      4. Code: No duplicates on create and update, and the format check on an API write;
      5. Parent Account: the relation and its hidden reverse, and the account as its own parent;
      6. Archive and Unarchive through their workflows, which must not start automation A.

    `DIFF` is a build that does not do what §1 says; `LIMIT` is platform behaviour §1 did not expect, recorded
    for §2 and not counted as a failure."""
    guard()
    f = C.fields(ws())
    cid = lambda n: f[n]['controlId']
    pid = automation_pid()
    index = record_index()
    if '410000' not in index:
        sys.exit('seed first: the self-check uses 410000 Trade Income as a parent')
    problems, limits = [], []
    before = signatures()

    def write(rowid, values, expect_runs):
        """An update, then the automation A runs it started (by id). A run registers some seconds after the
        write, so a write that should start none is watched for 12 s."""
        snap = run_snapshot(pid)
        hap.run('worksheet', 'record', 'update', ws(), rowid, '-a', APP, '--fields-json',
                json.dumps(values, ensure_ascii=False))
        return wait_new_runs(pid, snap, expect_runs, seconds=90 if expect_runs else 12)

    def refused_write(args, watch=12):
        snap = run_snapshot(pid)
        refused, message = attempt(*args)
        return refused, message, wait_new_runs(pid, snap, 0, seconds=watch)

    def check(label, ok, detail):
        print(f"  {'OK   ' if ok else 'DIFF '}  {label}: {detail}")
        if not ok:
            problems.append(f'{label}: {detail}')

    def limit(label, detail):
        print(f'  LIMIT  {label}: {detail}')
        limits.append(f'{label}: {detail}')

    def described(runs):
        return f"{len(runs)} run(s) {[(r.get('createDate'), r.get('status'), run_path(r['id'])) for r in runs]}"

    # 1 · the TEST account, created or brought back to its resting state
    if TEST_CODE not in index:
        want = dict(code=TEST_CODE, name=TEST_NAME, type='Current Assets', reconcile=False, non_trade=False,
                    active=True)
        snap = run_snapshot(pid)
        rowid = C.row_id(hap.run('worksheet', 'record', 'create', ws(), '-a', APP, '--fields-json', json.dumps(
            values_for(f, want, ['code', 'name', 'type', 'reconcile', 'non_trade', 'active']), ensure_ascii=False)))
        runs = wait_new_runs(pid, snap, 1)
        got = read_account(rowid)
        check('create a Current Assets account', len(runs) == 1 and run_path(runs[0]['id']) == NO_STEP
              and not got['reconcile'], f"{described(runs)}, reconcile={int(got['reconcile'])}")
    else:
        rowid = index[TEST_CODE][0]
        test = read_account(rowid)
        rest = dict(code=TEST_CODE, name=TEST_NAME, type='Current Assets', reconcile=False, non_trade=False,
                    active=True, parent=None, description='')
        keys = [k for k, v in rest.items() if test.get(k) != v]
        if keys:
            write(rowid, values_for(f, rest, keys), 1 if 'type' in keys else 0)
            print(f'  {TEST_NAME} brought back to its resting state: {keys}')
    C.remember('records', KEY + TEST_CODE, rowid)
    got = read_account(rowid)
    check('Display Name and Internal Group', (got['display_name'], got['internal_group']) ==
          (f'{TEST_CODE} {TEST_NAME}', 'Asset'), f"{got['display_name']!r} / {got['internal_group']!r}")

    for label, box, want_box in WALK:
        values = [{'id': cid(TYPE), 'value': [OPTION_KEY[label]]}]
        if box is not None:
            values.append({'id': cid(RECONCILE), 'value': box})
        runs = write(rowid, values, 1)
        got = read_account(rowid)
        paths = [run_path(r['id']) for r in runs]
        check(f'Type → {label}', (paths, got['reconcile'], got['internal_group'], got['type']) ==
              ([expected_run(label)], want_box, GROUP_OF_LABEL[label], label),
              f"{described(runs)}, reconcile={int(got['reconcile'])} (want {int(want_box)}), "
              f"group {got['internal_group']!r}")

    # 2 · an empty Type, then a write that sends the unchanged Type with another field
    runs = write(rowid, [{'id': cid(TYPE), 'value': []}], 1)
    got = read_account(rowid)
    causes = [((r.get('instanceLog') or {}).get('cause'), (r.get('instanceLog') or {}).get('causeMsg')) for r in runs]
    check('Type emptied through the API: no path matches, nothing is written',
          got['type'] is None and got['internal_group'] == '' and not got['reconcile'] and len(runs) == 1
          and runs[0].get('status') == 3, f"type {got['type']!r}, group {got['internal_group']!r}, "
                                          f"reconcile={int(got['reconcile'])}, {described(runs)}, cause {causes}")
    limit('an exclusive gateway that no path matches', f'ends the run with status 3, cause {causes} — '
                                                       'unlike the path that writes nothing, which completes (2)')
    runs = write(rowid, [{'id': cid(TYPE), 'value': [OPTION_KEY['Current Assets']]}], 1)
    got = read_account(rowid)
    check('back to Current Assets', got['type'] == 'Current Assets' and not got['reconcile'] and len(runs) == 1,
          f"{described(runs)}, reconcile={int(got['reconcile'])}")
    runs = write(rowid, [{'id': cid(TYPE), 'value': [OPTION_KEY['Current Assets']]},
                         {'id': cid(NON_TRADE), 'value': 1}], 0)
    limit('a write that sends Type unchanged with a real change to Non Trade',
          f'starts automation A all the same: {described(runs)} — the trigger narrowed to Type fires when Type '
          f'is in the write, not only when it changes')
    runs = write(rowid, [{'id': cid(NON_TRADE), 'value': 0}], 0)
    check('a write of Non Trade alone starts no run', not runs, described(runs))

    # 3 · the validation rule, on the API
    refused, message, runs = refused_write(('worksheet', 'record', 'update', ws(), rowid, '-a', APP, '--fields-json',
                                            json.dumps([{'id': cid(TYPE), 'value': [OPTION_KEY['Receivable']]}])))
    got = read_account(rowid)
    check('Current Assets (box unchecked) → Receivable, box not sent: refused, so automation A never runs',
          refused and got['type'] == 'Current Assets' and not runs,
          f"{'refused' if refused else 'ACCEPTED'}; type now {got['type']!r}; {described(runs)}; {message[:150]}")
    stray_code = 'TEST02'
    stray = record_index().get(stray_code)
    if stray:
        C.remember('records', KEY + stray_code, stray[0])
        got2 = read_account(stray[0])
        limit('create a Payable account with the box unchecked (validation rule, check type 1)',
              f'accepted in an earlier run — {stray_code} {got2["name"]!r} is {got2["type"]}, '
              f'reconcile={int(got2["reconcile"])}, active={int(got2["active"])}')
    else:
        snap = run_snapshot(pid)
        refused, message = attempt('worksheet', 'record', 'create', ws(), '-a', APP, '--fields-json', json.dumps(
            values_for(f, dict(code=stray_code, name='TEST refused payable', type='Payable', reconcile=False,
                               non_trade=False, active=True),
                       ['code', 'name', 'type', 'reconcile', 'non_trade', 'active']), ensure_ascii=False))
        stray = record_index().get(stray_code)
        if refused and not stray:
            check('create a Payable account with the box unchecked', True, f'refused; {message[:150]}')
        else:
            C.remember('records', KEY + stray_code, stray[0])
            runs = wait_new_runs(pid, snap, 1)
            got2 = read_account(stray[0])
            write(stray[0], [{'id': cid(ACTIVE), 'value': 0}], 0)   # out of the way, not deleted
            limit('create a Payable account with the box unchecked (validation rule, check type 1)',
                  f'ACCEPTED — the server does not check the rule on a create; automation A then ran '
                  f'({described(runs)}) and left reconcile={int(got2["reconcile"])}; {stray_code} archived')
    runs = write(rowid, [{'id': cid(TYPE), 'value': [OPTION_KEY['Receivable']]}, {'id': cid(RECONCILE), 'value': 1}], 1)
    check('Current Assets → Receivable with the box ticked in the same write', [run_path(r['id']) for r in runs] ==
          [expected_run('Receivable')] and read_account(rowid)['reconcile'], described(runs))
    refused, message, runs = refused_write(('worksheet', 'record', 'update', ws(), rowid, '-a', APP, '--fields-json',
                                            json.dumps([{'id': cid(RECONCILE), 'value': 0}])), watch=5)
    got = read_account(rowid)
    check('untick the box on a Receivable account', refused and got['reconcile'],
          f"{'refused' if refused else 'ACCEPTED'}; reconcile={int(got['reconcile'])}; {message[:150]}")
    if not got['reconcile']:
        write(rowid, [{'id': cid(RECONCILE), 'value': 1}], 0)

    # 4 · Code
    before_count = len(C.records(ws(), APP))
    refused, message, _ = refused_write(('worksheet', 'record', 'create', ws(), '-a', APP, '--fields-json', json.dumps(
        values_for(f, dict(code='410000', name='TEST duplicate code', type='Income', reconcile=False,
                           non_trade=False, active=True), ['code', 'name', 'type', 'reconcile', 'non_trade', 'active']),
        ensure_ascii=False)), watch=3)
    after_count = len(C.records(ws(), APP))
    check('create an account with Code 410000 (No duplicates)', refused and after_count == before_count,
          f"{'refused' if refused else 'ACCEPTED'}; {after_count - before_count} record(s) added; {message[:150]}")
    refused, message, _ = refused_write(('worksheet', 'record', 'update', ws(), rowid, '-a', APP, '--fields-json',
                                         json.dumps([{'id': cid(CODE), 'value': '410000'}])), watch=0)
    got = read_account(rowid)
    check("set TEST Account's Code to 410000", refused and got['code'] == TEST_CODE,
          f"{'refused' if refused else 'ACCEPTED'}; code {got['code']!r}; {message[:150]}")
    if got['code'] != TEST_CODE:
        write(rowid, [{'id': cid(CODE), 'value': TEST_CODE}], 0)
    refused, message, _ = refused_write(('worksheet', 'record', 'update', ws(), rowid, '-a', APP, '--fields-json',
                                         json.dumps([{'id': cid(CODE), 'value': 'TEST-01'}])), watch=0)
    got = read_account(rowid)
    limit("Code 'TEST-01' (a hyphen) through the API", f"{'refused' if refused else 'accepted'} — stored "
                                                        f"{got['code']!r}: the format check is the form's")
    if got['code'] != TEST_CODE:
        write(rowid, [{'id': cid(CODE), 'value': TEST_CODE}], 0)
        got = read_account(rowid)
        check('Code restored, and Display Name follows', got['display_name'] == f'{TEST_CODE} {TEST_NAME}',
              got['display_name'])

    # 5 · Parent Account and its hidden reverse
    parent = read_account(index['410000'][0])
    write(rowid, [{'id': cid(PARENT), 'value': [parent['rowid']]}], 0)
    got, up = read_account(rowid), read_account(parent['rowid'])
    check('Parent Account → 410000', got['parent'] == '410000 Trade Income' and up['children'] == parent['children'] + 1,
          f"parent {got['parent']!r}; 410000's Child Accounts {parent['children']} → {up['children']}")
    refused, message, _ = refused_write(('worksheet', 'record', 'update', ws(), rowid, '-a', APP, '--fields-json',
                                         json.dumps([{'id': cid(PARENT), 'value': [rowid]}])), watch=0)
    got = read_account(rowid)
    limit('TEST Account as its own parent through the API', f"{'refused' if refused else 'accepted'} — parent "
                                                            f"reads {got['parent']!r}; the picker filter is the "
                                                            f"browser's")
    write(rowid, [{'id': cid(PARENT), 'value': []}], 0)
    got, up = read_account(rowid), read_account(parent['rowid'])
    check('Parent Account cleared', got['parent'] is None and up['children'] == parent['children'],
          f"parent {got['parent']!r}; 410000's Child Accounts {up['children']}")

    # 6 · Archive / Unarchive, and automation A left alone
    workflows = hap.ids()['workflows']
    for name, want in (('Archive', False), ('Unarchive', True)):
        snap = run_snapshot(pid)
        hap.run('workflow', 'trigger', workflows[KEY + name], '-s', rowid)
        for _ in range(30):
            if read_account(rowid)['active'] == want:
                break
            time.sleep(1)
        runs = wait_new_runs(pid, snap, 0, seconds=10)
        check(f'{name} through its workflow', read_account(rowid)['active'] == want and not runs,
              f"active={int(read_account(rowid)['active'])}; automation A: {described(runs)}")

    # rest: Current Assets, box unchecked
    runs = write(rowid, [{'id': cid(TYPE), 'value': [OPTION_KEY['Current Assets']]},
                         {'id': cid(RECONCILE), 'value': 0}], 1)
    got = read_account(rowid)
    check('back to rest: Current Assets, box unchecked', (got['type'], got['reconcile'], len(runs)) ==
          ('Current Assets', False, 1), described(runs))
    print(f'  {TEST_NAME} {rowid}: {json.dumps(got, ensure_ascii=False)}')
    check_untouched(before)
    print('  selfcheck: ' + ('OK' if not problems else 'DIFFERENCES\n    ' + '\n    '.join(problems)))
    print(f'  platform limits recorded: {len(limits)}')
    for line in limits:
        print(f'    {line}')
    return len(problems)


# ── check ───────────────────────────────────────────────────────────────────

def step_check():
    """The configuration against §1; exits non-zero on a difference."""
    problems = []
    item = next((i for s in app_sections() for i in s['items'] if i['id'] == ws()), None)
    if [i['id'] for i in section_items()][:1] != [ws()]:
        problems.append(f"{WORKSHEET} is not first in {SECTION}: {[i['name'] for i in section_items()]}")
    if not item or (item.get('alias'), item.get('remark')) != (ALIAS, REMARK) or \
            not str(item.get('iconUrl')).endswith(f'/{ICON}.svg'):
        problems.append(f'worksheet alias / remark / icon: {item}')
    ctrls = hap.controls(ws())
    f = hap.by_name(ctrls)
    if set(f) != set(PLACE):
        problems.append(f'controls {sorted(set(f) ^ set(PLACE))}')
    problems += [f'{n}: {d}' for n, d in layout_differences(ctrls).items()]
    kinds = {CODE: 2, NAME: 2, DISPLAY: FORMULA, TYPE: 11, GROUP: FORMULA, RECONCILE: 36, NON_TRADE: 36,
             PARENT: 29, DESCRIPTION: 2, ACTIVE: 36, CHILDREN: 29}
    problems += [f'{n} is type {f[n]["type"]}, want {t}' for n, t in kinds.items() if n in f and f[n]['type'] != t]
    if f.get(CODE, {}).get('enumDefault') != 2 or f.get(DESCRIPTION, {}).get('enumDefault') != 1:
        problems.append('Code must be single-line text and Description multi-line')
    if [c['controlName'] for c in ctrls if c.get('attribute') == 1] != [TITLE]:
        problems.append(f"title field(s) {[c['controlName'] for c in ctrls if c.get('attribute') == 1]}")
    for name in COMPUTED:
        if name in f and (expression_of(f[name]) != EXPRESSIONS[name](f) or f[name].get('enumDefault2') != TEXT_RESULT):
            problems.append(f'{name}: {computed_state(ctrls).get(name)}')
    parent, children = f.get(PARENT, {}), f.get(CHILDREN, {})
    if (parent.get('dataSource'), parent.get('enumDefault')) != (ws(), 1) or \
            children.get('controlId') != parent.get('sourceControlId') or \
            (children.get('dataSource'), children.get('enumDefault'), children.get('sourceControlId')) != \
            (ws(), 2, parent.get('controlId')):
        problems.append(f"{PARENT} / {CHILDREN} are not a paired self-relation: "
                        f"{parent.get('dataSource')} {parent.get('enumDefault')} {parent.get('sourceControlId')} / "
                        f"{children.get('controlId')} {children.get('dataSource')} {children.get('enumDefault')} "
                        f"{children.get('sourceControlId')}")
    left, _ = rule_differences()
    problems += [f'rule {n!r}: {live} != {want}' for n, (live, want) in left.items()]
    pid = automation_pid()
    problems += automation_differences(pid, f) if pid else ['automation A missing']
    problems += button_differences()
    problems += [f'view {n}: {d}' for n, d in view_differences().items()]
    workflows = {w['name'] for w in hap.listing('workflow', 'list', APP)}
    if AUTOMATION not in workflows:
        problems.append('automation A not in the app\'s workflow list')
    print(f"  section {SECTION}: {[i['name'] for i in section_items()]}")
    print('  computed: ' + json.dumps(computed_state(ctrls), ensure_ascii=False))
    print('  check: ' + ('OK — first in Invoicing; eleven controls with their places, permissions, help, hints and '
                         'Code\'s format check; Display Name the title; the two formulas; the self-relation and its '
                         'hidden reverse; the three rules; automation A published with its four paths; Archive / '
                         'Unarchive; the two views'
                         if not problems else 'DIFFERENCES\n    ' + '\n    '.join(problems)))
    return len(problems)


def step_all():
    for name in ('create', 'fields', 'computed', 'layout', 'rules', 'automation', 'buttons', 'views', 'roles', 'seed'):
        print(f'\n── {name} ' + '─' * 60)
        STEPS[name]()
    print('\n── check ' + '─' * 60)
    return step_check()


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# Part B — the account fields this bundle brings to the worksheets already built
# (09 §1 › "What this bundle brings to the worksheets already built", automation B, Roles, Records step 2)
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
#
# Every account field is a **one-way** Relation → Chart of Accounts (single, dropdown), required nowhere on the field,
# whose picker lists active accounts only. Who owns what:
#
#  * **this script** adds the controls with `add-fields` (which parks them at row 9999) and owns what no other step
#    rewrites: the Relation itself, its alias, its picker filter and its static default — and automation B, the
#    references and the checks;
#  * **each worksheet's own script** places them: its `layout` step is the full read-modify-write save that moves a
#    control, so its PLACE (and tab rows) carry them, and so do its descriptions and placeholders wherever that step
#    rewrites them;
#  * **its rules and views steps** carry the rule and column changes in their own fixed lists, so a re-run of any of
#    them keeps what this bundle added — the account steps here run exactly those steps;
#  * **roles.py** owns the per-field hiding.
#
# Every write is bracketed by a control-by-control comparison of all nine worksheets (`b_snapshot` / `b_expect`): on
# the worksheet written, only the controls named may change, and only in the attributes named; the others must read
# back identical.

B_TOUCHED = ('Contacts', 'Products', 'Product Categories', 'Journals', 'Invoice Lines', 'Invoices')
B_ALL = B_TOUCHED + ('Units & Packagings', 'Product Variants', WORKSHEET)
RELATION, SUBTABLE = 29, 34
PLACE_KEYS = {'row', 'col', 'size', 'sectionId'}
OWNER = {'Contacts': 'contacts', 'Products': 'products', 'Product Categories': 'prodcat', 'Journals': 'journals',
         'Invoice Lines': 'invlines', 'Invoices': 'invoices'}

# Odoo ACCOUNT_DOMAIN (addons/account/models/product.py): the income-and-expense filter on Products' and Product
# Categories' accounts.
INCOME_EXPENSE = ('not in', ['Receivable', 'Payable', 'Bank and Cash', 'Credit Card', 'Off-Balance Sheet'])
# The tenant's invoice form narrows the line's account_id to these (the model itself only drops Off-Balance Sheet).
LINE_ACCOUNTS = ('not in', ['Receivable', 'Payable', 'Off-Balance Sheet'])

# worksheet -> [(control name, alias = Odoo's field, picker (op, Type labels) or None for every active account,
#               the Code of a static default or None)]
B_FIELDS = {
    'Contacts': [('Account Receivable', 'property_account_receivable_id', ('in', ['Receivable']), '124000'),
                 ('Account Payable', 'property_account_payable_id', ('in', ['Payable']), '221100')],
    'Products': [('Income Account', 'property_account_income_id', INCOME_EXPENSE, None),
                 ('Expense Account', 'property_account_expense_id', INCOME_EXPENSE, None)],
    'Product Categories': [('Income Account', 'property_account_income_categ_id', INCOME_EXPENSE, '410000'),
                           ('Expense Account', 'property_account_expense_categ_id', INCOME_EXPENSE, '510000')],
    'Journals': [('Default Account', 'default_account_id', None, None),
                 ('Suspense Account', 'suspense_account_id', ('in', ['Current Assets']), None),
                 ('Profit Account', 'profit_account_id', ('in', ['Income', 'Other Income']), None),
                 ('Loss Account', 'loss_account_id', ('in', ['Expenses']), None),
                 ('Private Share Account', 'non_deductible_account_id', None, None)],
    'Invoice Lines': [('Account', 'account_id', LINE_ACCOUNTS, None)],
}
# The tab each worksheet's accounts sit in. Journals' tab exists; the other three arrive with this bundle.
B_TAB = {'Contacts': 'Invoicing', 'Products': 'Accounting', 'Product Categories': 'Accounting',
         'Journals': 'Journal Entries'}
B_NEW_TAB = ('Contacts', 'Products', 'Product Categories')


def wid_of(worksheet):
    return hap.ids()['worksheets'][worksheet]


def owner(worksheet):
    """The build script that owns a worksheet — its places, descriptions and placeholders, and its own steps."""
    import importlib
    return importlib.import_module(OWNER[worksheet])


def spec_of(worksheet, name):
    return next((alias, picker, default) for n, alias, picker, default in B_FIELDS[worksheet] if n == name)


def place_of(worksheet, name, tab=False):
    """(row, col, size, tab name or None) of a control, from its owner's own tables. `tab` says the control is a tab:
    Contacts and Products keep their tabs' rows apart, and a tab can share its name with a field there ("Notes",
    "Sales")."""
    m = owner(worksheet)
    if worksheet == 'Contacts':
        return (m.TABS[name], 0, 12, None) if tab else m.PLACE[name]
    if worksheet == 'Products':
        return (m.TAB_ROWS[name], 0, 12, None) if tab else m.PLACE[name]
    if worksheet == 'Product Categories':
        row, col, size = m.PLACE[name]
        return row, col, size, m.TAB_OF.get(name)
    if worksheet in ('Journals', 'Invoices'):
        return m.PLACE[name]
    row, col, size = m.PLACE[name]                  # Invoice Lines has no tabs
    return row, col, size, None


def desc_of(worksheet, name):
    return owner(worksheet).DESC.get(name, '')


def hint_of(worksheet, name):
    return '' if worksheet == 'Invoice Lines' else getattr(owner(worksheet), 'HINTS', {}).get(name, '')


_coa_fields = {}


def coa_fields():
    """Chart of Accounts' controls by name, read once per run: this bundle never writes to them."""
    if not _coa_fields:
        _coa_fields.update(C.fields(ws()))
    return _coa_fields


def account_rowid(code):
    rowid = hap.ids().get('records', {}).get(KEY + code) or record_index().get(code, (None,))[0]
    if not rowid:
        sys.exit(f'no account {code} in {WORKSHEET}')
    return rowid


PICKER_BASE = {'spliceType': 1, 'dateRange': 0, 'dateRangeType': 0, 'minValue': None, 'maxValue': None,
               'isAsc': False, 'advancedSetting': None, 'isGroup': False, 'groupFilters': None, 'emptyRule': 0}


def account_picker(picker):
    """A Relation's picker filter over Chart of Accounts, in the shape the UI saves: Active is checked, and — when
    `picker` is given — Type is any of (EQ) or none of (NE) the labels, several option keys in one condition. A
    picker filter runs in the browser only (BUILDING.md), so the UI pass proves it."""
    f = coa_fields()
    items = [{'controlId': f[ACTIVE]['controlId'], 'dataType': SWITCH, **PICKER_BASE, 'filterType': C.EQ,
              'value': '1', 'values': ['1'], 'dynamicSource': []}]
    if picker:
        op, labels = picker
        items.append({'controlId': f[TYPE]['controlId'], 'dataType': 11, **PICKER_BASE,
                      'filterType': C.EQ if op == 'in' else C.NE, 'value': '',
                      'values': [OPTION_KEY[label] for label in labels], 'dynamicSource': []})
    return json.dumps(items, ensure_ascii=False, separators=(',', ':'))


def picker_state(value):
    """A picker filter in comparable form: its conditions (AND-ed, so unordered), each with its values unordered."""
    try:
        items = json.loads(value) if isinstance(value, str) else (value or [])
    except ValueError:
        return value
    return sorted((i.get('controlId'), i.get('dataType'), i.get('filterType'), tuple(sorted(i.get('values') or [])),
                   tuple(d.get('cid') for d in i.get('dynamicSource') or [])) for i in items)


def account_default(code):
    """A static Relation default, as products.py writes Unit's: the record id in a JSON list. The server stores the
    whole record in its place (BUILDING.md), so it is read back with default_rowids."""
    return json.dumps([{'cid': '', 'rcid': '', 'staticValue': json.dumps([account_rowid(code)])}])


def defsource_state(value):
    """An advancedSetting.defsource in comparable form. A static Relation default stores the whole related record,
    `utime` included, so a save of that record changes the string without anyone touching the control: the record
    is reduced to its rowid (BUILDING.md, "A control-set digest is not a reliable untouched signal")."""
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
        if isinstance(static, str) and static.startswith('['):
            try:
                static = tuple((json.loads(x).get('rowid') if isinstance(x, str) and x.startswith('{') else x)
                               for x in json.loads(static))
            except (TypeError, ValueError, AttributeError):
                pass
        out.append((e.get('cid') or '', e.get('rcid') or '', static, e.get('time') or ''))
    return out


def default_rowids(value):
    return [x for entry in defsource_state(value) if isinstance(entry, tuple) and isinstance(entry[2], tuple)
            for x in entry[2]]


JSON_KEYS = ('filters', 'filterregex', 'controlssorts', 'customShowControls')


def control_state(c):
    """A control's SIGNATURE attributes, with its JSON-valued advancedSetting keys parsed and a static Relation
    default reduced to record ids."""
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
    return out


def b_snapshot(names=B_ALL):
    return {name: {c['controlId']: control_state(c) for c in hap.controls(wid_of(name))} for name in names}


def b_expect(before, label, changed=None, new=None):
    """Read the worksheets of `before` again and stop unless the only differences are the ones named: `new` —
    {worksheet: control names that may appear} — and `changed` — {worksheet: {control name: attributes that may
    change}}. Prints what did change, control by control."""
    after = b_snapshot(tuple(before))
    changed, new = changed or {}, new or {}
    problems, seen, same = [], [], []
    for name in before:
        b, a = before[name], after[name]
        problems += [f"{name}: {b[cid]['controlName']!r} ({cid}) is gone" for cid in sorted(set(b) - set(a))]
        for cid in sorted(set(a) - set(b)):
            if a[cid]['controlName'] in new.get(name, ()):
                seen.append(f"{name} + {a[cid]['controlName']!r} {cid}")
            else:
                problems.append(f"{name}: an unexpected new control {a[cid]['controlName']!r} ({cid})")
        touched = False
        for cid in sorted(set(a) & set(b)):
            diff = [k for k in SIGNATURE if a[cid][k] != b[cid][k]]
            if not diff:
                continue
            touched = True
            allowed = changed.get(name, {}).get(b[cid]['controlName'], set())
            extra = [k for k in diff if k not in allowed]
            if extra:
                problems.append(f"{name}: {b[cid]['controlName']!r} changed " + '; '.join(
                    f'{k} {json.dumps(b[cid][k], ensure_ascii=False)[:160]} -> '
                    f'{json.dumps(a[cid][k], ensure_ascii=False)[:160]}' for k in extra))
            else:
                seen.append(f"{name}: {b[cid]['controlName']!r} {', '.join(f'{k} {b[cid][k]!r}→{a[cid][k]!r}' if k in PLACE_KEYS else k for k in diff)}")
        if not touched and set(a) == set(b):
            same.append(f'{name} ({len(a)})')
    if problems:
        sys.exit(f'{label}: controls read back with differences nobody asked for — stopping:\n  '
                 + '\n  '.join(problems))
    print(f'  {label}: compared control by control')
    for line in seen:
        print(f'    {line}')
    print(f"    identical: {', '.join(same)}")
    return after


def rule_snapshot(worksheet):
    """{ruleId: comparable rule} of a worksheet's business rules."""
    out = {}
    for r in hap.listing('worksheet', 'rules', wid_of(worksheet)):
        groups = [sorted((g.get('controlId'), g.get('dataType'), g.get('filterType'), tuple(sorted(g.get('values') or [])))
                         for g in f.get('groupFilters') or []) for f in r.get('filters') or []]
        items = [(i['type'], [x['controlId'] for x in i.get('controls') or []], i.get('message') or '')
                 for i in r.get('ruleItems') or []]
        out[r['ruleId']] = dict(name=r['name'], type=r['type'], disabled=r['disabled'], groups=groups, items=items,
                                check=r.get('checkType'), hint=r.get('hintType'))
    return out


def rules_expect(before, worksheet, label, new=(), changed=()):
    """Stop unless the rules read back as before, but for the rules named in `new` (added) and `changed`."""
    after = rule_snapshot(worksheet)
    problems = [f"rule {before[r]['name']!r} is gone" for r in set(before) - set(after)]
    problems += [f"unexpected new rule {after[r]['name']!r}" for r in set(after) - set(before)
                 if after[r]['name'] not in new]
    problems += [f"rule {before[r]['name']!r} changed: {before[r]} -> {after[r]}" for r in set(before) & set(after)
                 if before[r] != after[r] and before[r]['name'] not in changed]
    if problems:
        sys.exit(f'{label}: rules read back with differences nobody asked for — stopping:\n  ' + '\n  '.join(problems))
    added = [after[r]['name'] for r in set(after) - set(before)]
    moved = [after[r]['name'] for r in set(after) & set(before) if before[r] != after[r]]
    print(f'  {label}: {len(after)} rules compared; added {added}; changed {moved}; every other rule identical')
    return after


def view_snapshot(worksheet):
    """{viewId: comparable view} — name, filters, sort, columns, quick filters and the column display settings."""
    out = {}
    for v in hap.listing('worksheet', 'view', 'list', wid_of(worksheet), '-a', APP):
        info = C.view_info(wid_of(worksheet), APP, v['viewId'])
        settings = info.get('advancedSetting') or {}
        out[v['viewId']] = dict(
            name=info.get('name'), type=info.get('viewType'),
            filters=[(x.get('controlId'), x.get('dataType'), x.get('filterType'), x.get('values')) for x in info.get('filters') or []],
            sortCid=info.get('sortCid'), sortType=info.get('sortType'),
            moreSort=[(s.get('controlId'), s.get('isAsc')) for s in info.get('moreSort') or []],
            showControls=info.get('showControls'), displayControls=info.get('displayControls'),
            customShowControls=settings.get('customShowControls'), customdisplay=settings.get('customdisplay'),
            fastFilters=[(q.get('controlId'), q.get('dataType'), q.get('filterType'),
                          (q.get('advancedSetting') or {}).get('allowitem'), (q.get('advancedSetting') or {}).get('direction'))
                         for q in info.get('fastFilters') or []],
            coverCid=info.get('coverCid'))
    return out


def views_expect(before, worksheet, label, changed=None):
    """Stop unless every view reads back as before, but for `changed` — {view name: attributes that may change}."""
    after = view_snapshot(worksheet)
    changed = changed or {}
    problems = []
    if list(after) != list(before):
        problems.append(f'views {[before[v]["name"] for v in before]} -> {[after[v]["name"] for v in after]}')
    for vid in set(before) & set(after):
        diff = [k for k in before[vid] if before[vid][k] != after[vid][k]]
        extra = [k for k in diff if k not in changed.get(before[vid]['name'], ())]
        if extra:
            problems.append(f"view {before[vid]['name']!r}: " + '; '.join(f'{k} {before[vid][k]} -> {after[vid][k]}'
                                                                         for k in extra))
    if problems:
        sys.exit(f'{label}: views read back with differences nobody asked for — stopping:\n  ' + '\n  '.join(problems))
    print(f'  {label}: {len(after)} views compared; changed ' +
          str({before[v]['name']: [k for k in before[v] if before[v][k] != after[v][k]] for v in before
               if v in after and before[v] != after[v]}))
    return after


def account_control(worksheet, name, tab_id):
    """One account field to add: a one-way Relation → Chart of Accounts, single, shown as a dropdown, with its picker
    filter and its static default. Built by hap-cli's own builder; sent without a controlId so the server mints it
    and — `bidirectional` "0" — the Chart of Accounts gets no reverse control."""
    alias, picker, default = spec_of(worksheet, name)
    row, col, size, _ = place_of(worksheet, name)
    settings = {'bidirectional': '0', 'showtype': '3', 'filters': account_picker(picker)}
    if default:
        settings['defsource'] = account_default(default)
    control = C.control('RELATE_SHEET', name, (row, col, size), alias=alias, hint=hint_of(worksheet, name),
                        desc=desc_of(worksheet, name), data_source=ws(), multi=False, advanced_setting=settings)
    control['sectionId'] = tab_id
    return control


def b_add(worksheet):
    """Add what is missing of this bundle's controls on a worksheet with `add-fields`: the tab first, when the bundle
    brings one, then the account Relations carrying the tab's id. `add-fields` parks everything at row 9999; the
    owner's `layout` step places it. Returns the names added."""
    wid = wid_of(worksheet)
    ctrls = hap.controls(wid)
    tabs = {c['controlName']: c for c in ctrls if c['type'] == C.TAB}
    fields = {c['controlName']: c for c in ctrls if c['type'] != C.TAB}
    tab = B_TAB.get(worksheet)
    wanted = [n for n, _, _, _ in B_FIELDS[worksheet] if n not in fields]
    tab_missing = bool(tab) and tab not in tabs
    if tab_missing and worksheet not in B_NEW_TAB:
        sys.exit(f'{worksheet} has no tab {tab!r} — its own script builds it')
    if not wanted and not tab_missing:
        print(f"  {worksheet}: {', '.join(n for n, _, _, _ in B_FIELDS[worksheet])} already there; nothing added")
        return []
    print('  backup:', hap.backup(f"accounts_b_{OWNER[worksheet]}_controls_pre_add", ctrls))
    before = b_snapshot()
    added = []
    if tab_missing:
        row, col, size, _ = place_of(worksheet, tab, tab=True)
        C.append_controls(wid, [C.control('SECTION', tab, (row, col, size))])
        added.append(tab)
        tabs = {c['controlName']: c for c in hap.controls(wid) if c['type'] == C.TAB}
        if tab not in tabs:
            sys.exit(f'{worksheet}: the tab {tab!r} did not read back after add-fields')
    if wanted:
        C.append_controls(wid, [account_control(worksheet, n, tabs[tab]['controlId'] if tab else '') for n in wanted])
        added += wanted
    b_expect(before, f'{worksheet}: add-fields {added}', new={worksheet: set(added)})
    return added


def owner_place_differences(worksheet, ctrls=None):
    """{control name: {attribute: (live, want)}} for every control whose place its owner's tables give and whose
    live row, col, size or tab differs — what the owner's `layout` step would move."""
    ctrls = ctrls or hap.controls(wid_of(worksheet))
    tab_ids = {c['controlName']: c['controlId'] for c in ctrls if c['type'] == C.TAB}
    out = {}
    for c in ctrls:
        name = c['controlName']
        try:
            row, col, size, tab = place_of(worksheet, name, tab=c['type'] == C.TAB)
        except KeyError:
            continue
        want = dict(row=row, col=col, size=size, sectionId=tab_ids.get(tab, '') if tab else '')
        diff = {k: (c.get(k) or ('' if k == 'sectionId' else c.get(k)), v) for k, v in want.items()
                if (c.get(k) or ('' if k == 'sectionId' else c.get(k))) != v}
        if diff:
            out[f'{name} (tab)' if c['type'] == C.TAB else name] = diff
    return out


def b_field_differences(worksheet, ctrls=None):
    """This bundle's controls on one worksheet read back against 09 §1 and the owner's tables: the tab and its
    place; each account's type, target, single-ness, alias, description, placeholder, not required, visible, place,
    tab, one-way-ness, dropdown, picker filter and static default. Records every id in ids.json."""
    ctrls = ctrls or hap.controls(wid_of(worksheet))
    tabs = {c['controlName']: c for c in ctrls if c['type'] == C.TAB}
    fields = {c['controlName']: c for c in ctrls if c['type'] != C.TAB}
    out = []
    tab = B_TAB.get(worksheet)
    if tab and tab not in tabs:
        return [f'{worksheet}: no tab {tab!r}']
    if tab and worksheet in B_NEW_TAB:
        t = tabs[tab]
        C.remember('controls', f'{worksheet}: {tab}', t['controlId'])
        row, col, size, _ = place_of(worksheet, tab, tab=True)
        if (t.get('row'), t.get('col'), t.get('size'), t.get('sectionId') or '') != (row, col, size, ''):
            out.append(f"{worksheet} / tab {tab}: row {t.get('row')} col {t.get('col')} size {t.get('size')} "
                       f"section {t.get('sectionId')!r}, want {(row, col, size)}")
    coa_ids = {c['controlId'] for c in hap.controls(ws())}
    for name, alias, picker, default in B_FIELDS[worksheet]:
        c = fields.get(name)
        if not c:
            out.append(f'{worksheet}: no {name!r}')
            continue
        C.remember('controls', f'{worksheet}: {name}', c['controlId'])
        row, col, size, in_tab = place_of(worksheet, name)
        want = dict(type=RELATION, dataSource=ws(), enumDefault=1, alias=alias, desc=desc_of(worksheet, name),
                    hint=hint_of(worksheet, name), required=False, fieldPermission='111', attribute=0, row=row,
                    col=col, size=size, sectionId=tabs[in_tab]['controlId'] if in_tab else '')
        got = {k: c.get(k) for k in want}
        for k in ('desc', 'hint', 'sectionId', 'alias'):
            got[k] = got[k] or ''
        got['attribute'] = got['attribute'] or 0
        diff = {k: (got[k], v) for k, v in want.items() if got[k] != v}
        settings = c.get('advancedSetting') or {}
        if (settings.get('bidirectional'), settings.get('showtype')) != ('0', '3'):
            diff['one-way dropdown'] = ((settings.get('bidirectional'), settings.get('showtype')), ('0', '3'))
        if picker_state(settings.get('filters')) != picker_state(account_picker(picker)):
            diff['picker'] = (settings.get('filters'), account_picker(picker))
        want_default = [account_rowid(default)] if default else []
        if default_rowids(settings.get('defsource')) != want_default:
            diff['default'] = (default_rowids(settings.get('defsource')), want_default)
        if c.get('sourceControlId') in coa_ids:
            diff['reverse'] = (c.get('sourceControlId'), 'a one-way Relation has no control on Chart of Accounts')
        if diff:
            out.append(f'{worksheet} / {name}: ' + json.dumps(diff, ensure_ascii=False, default=str)[:900])
    return out


def b_place(worksheet, extra_changes=None):
    """Run the owner's own `layout` step when a control is not where the owner's tables put it, bracketed by the
    control-by-control comparison: only row, col, size and tab may move, and only on the controls it had to move.
    `extra_changes` names further attributes that step is known to rewrite on a control."""
    moves = owner_place_differences(worksheet)
    if not moves:
        print(f'  {worksheet}: every control already where {OWNER[worksheet]}.py puts it; its layout step not run')
        return
    print(f'  {worksheet}: {OWNER[worksheet]}.py layout moves ' +
          json.dumps({n: {k: v for k, v in d.items()} for n, d in moves.items()}, ensure_ascii=False))
    before = b_snapshot()
    owner(worksheet).step_layout()
    allowed = {name.removesuffix(' (tab)'): set(PLACE_KEYS) for name in moves}
    for name, keys in (extra_changes or {}).items():
        allowed[name] = allowed.get(name, set()) | set(keys)
    b_expect(before, f'{worksheet}: {OWNER[worksheet]}.py layout', changed={worksheet: allowed})
    left = owner_place_differences(worksheet)
    if left:
        sys.exit(f'{worksheet}: still out of place after its layout step: {left}')


def b_settings(worksheet):
    """Bring what this script owns on each account field back to spec when it has drifted — alias, description,
    placeholder, not required, visible, one-way dropdown, picker filter, static default — in one full save through
    common.save_controls, bracketed by the comparison. Place is the owner's `layout`'s, and is not touched here."""
    wid = wid_of(worksheet)
    ctrls = hap.controls(wid)
    fields = {c['controlName']: c for c in ctrls if c['type'] != C.TAB}
    todo = []
    for name, alias, picker, default in B_FIELDS[worksheet]:
        c = fields.get(name)
        if not c:
            sys.exit(f'{worksheet}: {name!r} is missing — run this step again to add it')
        settings = dict(c.get('advancedSetting') or {})
        want_settings = {'bidirectional': '0', 'showtype': '3'}
        stale = [k for k, v in want_settings.items() if settings.get(k) != v]
        if picker_state(settings.get('filters')) != picker_state(account_picker(picker)):
            stale.append('filters')
        want_default = [account_rowid(default)] if default else []
        if default_rowids(settings.get('defsource')) != want_default:
            stale.append('defsource')
        attrs = dict(alias=alias, desc=desc_of(worksheet, name), hint=hint_of(worksheet, name), required=False,
                     fieldPermission='111')
        stale += [k for k, v in attrs.items() if (c.get(k) or ('' if isinstance(v, str) else c.get(k))) != v]
        if stale:
            todo.append((name, stale))
            c.update(attrs)
            settings.update(want_settings, filters=account_picker(picker))
            if default:
                settings['defsource'] = account_default(default)
            elif default_rowids(settings.get('defsource')):
                settings['defsource'] = '[]'
            c['advancedSetting'] = settings
    if not todo:
        print(f'  {worksheet}: alias, help, placeholder, picker and default already as specified; nothing saved')
        return
    print('  backup:', hap.backup(f"accounts_b_{OWNER[worksheet]}_controls_pre_settings", hap.controls(wid)))
    before = b_snapshot()
    C.save_controls(wid, ctrls)
    b_expect(before, f'{worksheet}: account settings {todo}',
             changed={worksheet: {name: {'alias', 'desc', 'hint', 'required', 'fieldPermission', 'advancedSetting'}
                                  for name, _ in todo}})


def b_report(worksheet, problems):
    if problems:
        sys.exit(f'{worksheet} read back with differences:\n  ' + '\n  '.join(problems))
    print(f"  {worksheet}: read back as specified — {', '.join(n for n, _, _, _ in B_FIELDS[worksheet])}")


# ── B1 · Contacts ───────────────────────────────────────────────────────────

def contacts_rule_want():
    """The Invoicing tab rule as rule_snapshot reads it: hide the tab while Company is not empty."""
    import contacts as K
    ctrls = hap.controls(K.WS)
    company = next(c for c in ctrls if c['controlName'] == 'Company' and c['type'] != C.TAB)
    tab = next(c for c in ctrls if c['controlName'] == 'Invoicing' and c['type'] == C.TAB)
    return dict(name=K.RULE_INVOICING, type=C.INTERACTION, disabled=False,
                groups=[[(company['controlId'], RELATION, C.NOT_EMPTY, ())]],
                items=[(C.HIDE, [tab['controlId']], '')], check=0, hint=0)


def contacts_rule_differences():
    import contacts as K
    live = next((r for r in rule_snapshot('Contacts').values() if r['name'] == K.RULE_INVOICING), None)
    want = contacts_rule_want()
    keys = ('name', 'type', 'disabled', 'groups', 'items')
    return [] if live and {k: live[k] for k in keys} == {k: want[k] for k in keys} else \
        [f'rule {K.RULE_INVOICING!r}: {live} != {want}']


def step_b_contacts():
    """Contacts (01): the tab **Invoicing** between Sales & Purchase and Notes, hidden while Company is set, holding
    **Account Receivable** (Type = Receivable, default 124000) and **Account Payable** (Type = Payable, default
    221100). Placed by contacts.py `layout`; the rule by contacts.py `rules`."""
    guard()
    import contacts as K
    b_add('Contacts')
    b_place('Contacts')
    b_settings('Contacts')
    b_report('Contacts', b_field_differences('Contacts'))
    if contacts_rule_differences():
        before = rule_snapshot('Contacts')
        print('  backup:', hap.backup('accounts_b_contacts_rules_pre_rules', list(before.values())))
        views = b_snapshot(('Contacts',))
        K.step_rules()
        rules_expect(before, 'Contacts', 'contacts.py rules', new=(K.RULE_INVOICING,))
        b_expect(views, 'Contacts: after the rules step')
    else:
        print(f'  rule {K.RULE_INVOICING!r} already as specified; contacts.py rules not run')
    problems = contacts_rule_differences()
    rule = next(r for r, x in rule_snapshot('Contacts').items() if x['name'] == K.RULE_INVOICING)
    C.remember('rules', 'Contacts: ' + K.RULE_INVOICING, rule)
    if problems:
        sys.exit('\n'.join(problems))
    print(f'  rule {K.RULE_INVOICING!r} ({rule}): hide the tab Invoicing while Company is not empty')
    K.show()


# ── B2 · Products ──────────────────────────────────────────────────────────

def step_b_products():
    """Products (03): the tab **Accounting** after Inventory, holding **Income Account** and **Expense Account** —
    the income-and-expense filter, placeholder "From Category", Odoo's help and no default (an empty account is what
    makes a product use its category's). Placed by products.py `layout`, which also writes their placeholder, help
    and visibility from its own tables."""
    guard()
    b_add('Products')
    b_place('Products', extra_changes={n: {'fieldPermission', 'hint', 'desc'} for n in ('Income Account',
                                                                                        'Expense Account')})
    b_settings('Products')
    b_report('Products', b_field_differences('Products'))
    C.show(wid_of('Products'))


# ── B3 · Product Categories ────────────────────────────────────────────────

def step_b_categories():
    """Product Categories (08): the tab **Accounting** holding **Income Account** (default 410000 Trade Income) and
    **Expense Account** (default 510000 Costs) — the income-and-expense filter and Odoo's help. Placed by prodcat.py
    `layout`, at row 2: HAP's tab bar lists type-52 tabs and showtype-6 relation lists (Child Categories) in row
    order and showtype-2 lists (Products) after them (pd-openweb getControlsByTab), so the bar reads Accounting ·
    Child Categories · Products — what the browser shows is for the UI pass."""
    guard()
    b_add('Product Categories')
    b_place('Product Categories', extra_changes={n: {'fieldPermission'} for n in ('Income Account',
                                                                                  'Expense Account')})
    tabs = [(c['controlName'], c['row'], (c.get('advancedSetting') or {}).get('showtype'))
            for c in hap.controls(wid_of('Product Categories'))
            if c['type'] == C.TAB or (c['type'] == RELATION and (c.get('advancedSetting') or {}).get('showtype') in ('2', '6'))]
    in_rows = sorted((row, name) for name, row, show in tabs if show != '2')
    print('  the tab bar, as pd-openweb getControlsByTab orders it: '
          + ' · '.join([name for _, name in in_rows] + [name for name, _, show in sorted(tabs, key=lambda t: t[1])
                                                        if show == '2']))
    b_settings('Product Categories')
    b_report('Product Categories', b_field_differences('Product Categories'))
    C.show(wid_of('Product Categories'))


# ── B4 · Journals ──────────────────────────────────────────────────────────

def journals_rule_names():
    import journals as J
    return (J.RULE_DEFAULT_REQ, J.RULE_SUSPENSE, J.RULE_SUSPENSE_REQ, J.RULE_PROFIT_LOSS, J.RULE_PRIVATE_SHARE)


def journals_rule_differences():
    """The five account rules read back against journals.RULES: an interaction rule, not disabled, one item of the
    kind named, Type any of the types named, acting on the controls named."""
    import journals as J
    ctrls = hap.controls(J.WORKSHEET)
    f, names = hap.by_name(ctrls), {c['controlId']: c['controlName'] for c in ctrls}
    keys = {o['key']: o['value'] for o in f['Type']['options']}
    live = {r['name']: r for r in hap.listing('worksheet', 'rules', J.WORKSHEET)}
    out = []
    for name in journals_rule_names():
        types, targets, kind = J.RULES[name]
        r = live.get(name)
        if not r:
            out.append(f'rule {name!r} missing')
            continue
        conds = [g for group in r['filters'] for g in group.get('groupFilters', [])]
        got = (r['type'], r['disabled'], [i['type'] for i in r['ruleItems']],
               [(names.get(c['controlId']), c['filterType'], sorted(keys.get(v) for v in c.get('values', [])))
                for c in conds],
               [names.get(c['controlId']) for i in r['ruleItems'] for c in i['controls']])
        want = (C.INTERACTION, False, [kind], [('Type', C.EQ, sorted(types))], list(targets))
        if got != want:
            out.append(f'rule {name!r}: {got} != {want}')
        else:
            C.remember('rules', J.KEY + name, r['ruleId'])
    return out


def columns_of(worksheet, view_names):
    names = {c['controlId']: c['controlName'] for c in hap.controls(wid_of(worksheet))}
    views = {v['name']: v['viewId'] for v in hap.listing('worksheet', 'view', 'list', wid_of(worksheet), '-a', APP)}
    out = {}
    for name in view_names:
        info = C.view_info(wid_of(worksheet), APP, views[name]) if name in views else {}
        settings = info.get('advancedSetting') or {}
        out[name] = ([names.get(x, x) for x in info.get('showControls') or []],
                     [names.get(x, x) for x in json.loads(settings.get('customShowControls') or '[]')])
    return out


def step_b_journals():
    """Journals (05): on the tab Journal Entries, above the two dedicated sequences, **Default Account**, **Suspense
    Account**, **Profit Account**, **Loss Account** and **Private Share Account** with §1's pickers and help; the
    visibility and requirement rules by Type; and a **Default Account** column after Sequence Prefix on both views.
    Placed by journals.py `layout`, the rules by its `rules` and the columns by its `views` — whose lists carry them."""
    guard()
    import journals as J
    J.guard()
    b_add('Journals')
    b_place('Journals', extra_changes={n: {'fieldPermission'} for n in J.ACCOUNTS})
    b_settings('Journals')
    b_report('Journals', b_field_differences('Journals'))
    if journals_rule_differences():
        before, ctrls = rule_snapshot('Journals'), b_snapshot(('Journals',))
        print('  backup:', hap.backup('accounts_b_journals_rules_pre_rules', list(before.values())))
        J.step_rules()
        rules_expect(before, 'Journals', 'journals.py rules', new=journals_rule_names())
        b_expect(ctrls, 'Journals: after the rules step')
    else:
        print('  the five account rules already as specified; journals.py rules not run')
    problems = journals_rule_differences()
    if problems:
        sys.exit('Journals rules read back with differences:\n  ' + '\n  '.join(problems))
    print(f'  rules: {list(journals_rule_names())} read back as specified')
    want = list(J.COLUMNS)
    if any(cols != (want, want) for cols in columns_of('Journals', ('Journals', 'Archived')).values()):
        before, ctrls = view_snapshot('Journals'), b_snapshot(('Journals',))
        print('  backup:', hap.backup('accounts_b_journals_views_pre_views', before))
        J.step_views()
        column_keys = ('showControls', 'customShowControls', 'displayControls')
        views_expect(before, 'Journals', 'journals.py views', changed={'Journals': column_keys, 'Archived': column_keys})
        b_expect(ctrls, 'Journals: after the views step')
    else:
        print('  both views already show Default Account after Sequence Prefix; journals.py views not run')
    got = columns_of('Journals', ('Journals', 'Archived'))
    if any(cols != (want, want) for cols in got.values()):
        sys.exit(f'Journals views read back {got}, want {want}')
    print(f'  views: {got}')
    C.show(J.WORKSHEET)


# ── B5 · Invoice Lines, and the lines table inside Invoices ────────────────

def lines_rule_differences():
    """07's rule *A section or a note carries no figures* read back against invlines.FIGURES, Account included."""
    import invlines as L
    ctrls = hap.controls(L.ws())
    names = {c['controlId']: c['controlName'] for c in ctrls}
    r = next((r for r in hap.listing('worksheet', 'rules', L.ws()) if r['name'] == L.RULE_FIGURES), None)
    if not r:
        return [f'rule {L.RULE_FIGURES!r} missing']
    conds = [g for group in r['filters'] for g in group.get('groupFilters', [])]
    got = (r['type'], r['disabled'], [i['type'] for i in r['ruleItems']],
           sorted(L.LABEL['Display Type'].get(v) for c in conds for v in c.get('values', [])),
           [names.get(c['controlId']) for i in r['ruleItems'] for c in i['controls']])
    want = (C.INTERACTION, False, [C.HIDE], sorted(L.TEXT_LINES), list(L.FIGURES))
    return [] if got == want else [f'rule {L.RULE_FIGURES!r}: {got} != {want}']


def subtable_columns():
    import invlines as L
    names = {c['controlId']: c['controlName'] for c in hap.controls(L.ws())}
    sub = L.sub_list()
    settings = (sub or {}).get('advancedSetting') or {}
    return ([names.get(x, x) for x in (sub or {}).get('showControls') or []],
            [names.get(x, x) for x in json.loads(settings.get('controlssorts') or '[]')])


def step_b_lines():
    """Invoice Lines (07), and the lines table inside Invoices (06): **Account** after Label — active accounts whose
    Type is not Receivable, Payable or Off-Balance Sheet — joining the rule *A section or a note carries no figures*,
    and a column after Label on the Lines view and in the Invoices subtable. Placed by invlines.py `layout`, which
    also re-places the subtable (`place_subtable`, a save of Invoices through the CLI's session — `update-fields
    --controls` cannot carry Invoices); the rule by its `rules`, the column by its `views`."""
    guard()
    import invlines as L
    L.guard()
    b_add('Invoice Lines')
    ctrls = hap.controls(L.ws())
    moves, pending = owner_place_differences('Invoice Lines', ctrls), L.layout_differences(ctrls)
    want_columns = list(L.SUBTABLE_COLUMNS)
    if moves or pending or subtable_columns() != (want_columns, want_columns):
        print(f'  Invoice Lines: invlines.py layout — moves {json.dumps(moves, ensure_ascii=False)}; '
              f'differences {json.dumps(pending, ensure_ascii=False)[:600]}; subtable {subtable_columns()}')
        before = b_snapshot()
        L.step_layout()
        allowed = {name: set(PLACE_KEYS) for name in moves}
        for name, diff in pending.items():
            allowed.setdefault(name, set()).update(k.split('.')[0] for k in diff)
        b_expect(before, 'invlines.py layout (Invoice Lines, and the subtable on Invoices)',
                 changed={'Invoice Lines': allowed, 'Invoices': {L.LINES_FIELD: {'showControls', 'advancedSetting'}}})
    else:
        print('  Invoice Lines: every control in place and the subtable already shows Account; layout not run')
    left = owner_place_differences('Invoice Lines') or L.layout_differences(hap.controls(L.ws()))
    if left:
        sys.exit(f'Invoice Lines still differs after its layout step: {left}')
    if subtable_columns() != (want_columns, want_columns):
        sys.exit(f'the Invoices subtable reads back {subtable_columns()}, want {want_columns}')
    print(f'  the Invoices subtable {L.LINES_FIELD!r} shows {subtable_columns()[0]}')
    b_settings('Invoice Lines')
    b_report('Invoice Lines', b_field_differences('Invoice Lines'))
    if lines_rule_differences():
        before, ctrls = rule_snapshot('Invoice Lines'), b_snapshot(('Invoice Lines',))
        print('  backup:', hap.backup('accounts_b_invlines_rules_pre_rules', list(before.values())))
        L.step_rules()
        rules_expect(before, 'Invoice Lines', 'invlines.py rules', changed=(L.RULE_FIGURES,))
        b_expect(ctrls, 'Invoice Lines: after the rules step')
    else:
        print(f'  rule {L.RULE_FIGURES!r} already hides Account; invlines.py rules not run')
    problems = lines_rule_differences()
    if problems:
        sys.exit('\n'.join(problems))
    print(f'  rule {L.RULE_FIGURES!r} hides {L.FIGURES}')
    want = list(L.VIEW_COLUMNS)
    if columns_of('Invoice Lines', ('Lines',))['Lines'] != (want, want):
        before, ctrls = view_snapshot('Invoice Lines'), b_snapshot(('Invoice Lines',))
        print('  backup:', hap.backup('accounts_b_invlines_views_pre_views', before))
        L.step_views()
        views_expect(before, 'Invoice Lines', 'invlines.py views',
                     changed={'Lines': ('showControls', 'customShowControls', 'displayControls')})
        b_expect(ctrls, 'Invoice Lines: after the views step')
    else:
        print('  the Lines view already shows Account after Label; invlines.py views not run')
    got = columns_of('Invoice Lines', ('Lines',))['Lines']
    if got != (want, want):
        sys.exit(f'the Lines view reads back {got}, want {want}')
    print(f'  view Lines: {got[0]}')
    C.show(L.ws())


# ── B6 · automation B — Invoice Lines: fill the account ─────────────────────
#
# Odoo account.move.line _compute_account_id, as 09 §1 tabulates it, for a Product line:
#
#   customer document (Customer Invoice, Customer Credit Note, Sales Receipt)
#       the product's Income Account → its category's Income Account → the invoice journal's Default Account
#   vendor document (Vendor Bill, Vendor Credit Note, Purchase Receipt)
#       the product's Expense Account → its category's Expense Account → the journal's Default Account
#   Journal Entry
#       the journal's Default Account
#
# **and the journal's Default Account fills only an empty Account** — Odoo's `accounts['income'] or line.account_id`:
# when the product and its category give nothing, the line keeps the account it has, and the journal's default is
# used only when it has none (the coordinator's call of 17 Sep 2026, over §1's flattened "first of"). The product's
# and the category's accounts replace whatever the line carries. The line's Product is a **variant**, so "the product"
# is the variant's Product; Odoo walks up the category's parents, and every category here carries both accounts, so
# the category read is the product's own.
#
# **A search step whose filter value is empty fails the run** — status 4, cause 100000 "筛选条件值为空 记录ID" — even
# when it is told to carry on when nothing is found (the self-check's line with no Product, 17 Sep 2026). So each
# search's condition carries HAP's **条件异常时忽略** (`ignoreEmpty` 1, "ignore the condition when it is abnormal"),
# which the condition editor offers on a dynamic value, and every path of the gateway checks the Relation each record
# it reads was found through: a search whose condition was ignored may hand back any record, and no path reads one.
#
# Two workflows with one body, because HAP's worksheet trigger takes one event (BUILDING.md): a line **created with
# no Account** (新增 '1', condition: Display Type is Product and Account is empty — a line created with an Account keeps
# it), and a line whose **Product changes** (仅更新 '4', narrowed to Product, condition: Display Type is Product). The
# body reads the invoice, the variant, the product, the category and the journal with five search steps (Record ID =
# the Relation on the record before it; carry on when nothing is found), then one exclusive gateway whose seven paths
# are §1's table, each written out in full — its guards included — so that no path depends on the order the gateway
# reads them in. A run that matches none — a journal entry on a journal with no Default Account, or a Product change
# that finds nothing on the product or its category for a line that already has an Account — stops at the gateway
# with 40002 "未通过分支" and writes nothing, as automation A does on an empty Type.
#
# Neither workflow starts the other: both write Account alone, and the second is narrowed to Product. Nor do their
# writes start 07's roll-up, which runs for every API write of a line and for none of automation B's (BUILDING.md).

B_NEW_LINE = 'Invoice Lines: fill the account of a new line'
B_PRODUCT_CHANGED = 'Invoice Lines: fill the account when the Product changes'
B_EVENTS = {B_NEW_LINE: ('create', '1'), B_PRODUCT_CHANGED: ('update', '4')}
B_TRIGGER_NAMES = {B_NEW_LINE: 'When a product line is created with no Account',
                   B_PRODUCT_CHANGED: "When a product line's Product changes"}
B_DESC_COMMON = ("Odoo account.move.line _compute_account_id: a product line's Account becomes the product's Income "
                 "Account, else its category's, on a customer document; the Expense Accounts on a vendor document. The "
                 "invoice journal's Default Account fills it only while it is still empty, and is the only source on a "
                 "journal entry. Otherwise Account is left as it is.")
B_DESCS = {B_NEW_LINE: 'Runs when a product line is created with no Account. ' + B_DESC_COMMON,
           B_PRODUCT_CHANGED: "Runs when a product line's Product changes. " + B_DESC_COMMON}
B_GET_INVOICE, B_GET_VARIANT, B_GET_PRODUCT = 'Get the invoice', 'Get the product variant', 'Get the product'
B_GET_CATEGORY, B_GET_JOURNAL = "Get the product's category", "Get the invoice's journal"
B_GATEWAY = 'Which account does the line take?'
B_SEARCH_ORDER = (B_GET_INVOICE, B_GET_VARIANT, B_GET_PRODUCT, B_GET_CATEGORY, B_GET_JOURNAL)
CONTINUE_WHEN_NOT_FOUND = 2                        # a search step's executeType: 0 stop · 1 add a record · 2 carry on
EMPTY_ID, NOT_EMPTY_ID, EQUALS_ID = '8', '7', '9'  # workflow conditionIds 为空 · 不为空 · 等于
IGNORE_WHEN_ABNORMAL = 1                           # a condition's ignoreEmpty: the editor's 条件异常时忽略


def b_ids():
    """Every control id automation B reads or writes, by the worksheet it lives on."""
    ids = hap.ids()['worksheets']
    lines, invoices = C.fields(ids['Invoice Lines']), C.fields(ids['Invoices'])
    variants, products = C.fields(ids['Product Variants']), C.fields(ids['Products'])
    categories, journals = C.fields(ids['Product Categories']), C.fields(ids['Journals'])
    return dict(
        lines=ids['Invoice Lines'], invoices=ids['Invoices'], variants=ids['Product Variants'],
        products=ids['Products'], categories=ids['Product Categories'], journals=ids['Journals'],
        line_invoice=lines['Invoice'], line_product=lines['Product'], line_type=lines['Display Type'],
        line_account=lines['Account'], invoice_type=invoices['Type'], invoice_journal=invoices['Journal'],
        variant_product=variants['Product'], product_category=products['Category'],
        product_income=products['Income Account'], product_expense=products['Expense Account'],
        category_income=categories['Income Account'], category_expense=categories['Expense Account'],
        journal_default=journals['Default Account'])


def b_searches(x):
    """(step name, worksheet, the step whose record carries the Relation — None for the trigger, the Relation)."""
    return [(B_GET_INVOICE, x['invoices'], None, x['line_invoice']),
            (B_GET_VARIANT, x['variants'], None, x['line_product']),
            (B_GET_PRODUCT, x['products'], B_GET_VARIANT, x['variant_product']),
            (B_GET_CATEGORY, x['categories'], B_GET_PRODUCT, x['product_category']),
            (B_GET_JOURNAL, x['journals'], B_GET_INVOICE, x['invoice_journal'])]


def b_paths(x):
    """§1's table as seven paths: (path name, [condition groups — any one matches], the update step, the step and
    control it takes Account from). A condition is (the step whose record is read — None for the trigger line —,
    the control, an operator: 'set', 'empty' or a list of Type labels).

    Each group carries its own guards: the line names its invoice; a product or category account is read only when
    the line names a product, the variant names its product and — for the category — the product names its category;
    the journal's account only when the invoice names its journal. The journal paths list the four ways the product
    and category yield nothing, and **every journal group requires the line's Account to be empty**: the journal's
    Default Account fills only an empty Account, as Odoo's `accounts['income'] or line.account_id` does (the
    coordinator's call of 17 Sep 2026). The product's and the category's accounts replace whatever the line has."""
    import invoices as I
    line_invoice, line_product = x['line_invoice'], x['line_product']
    has = lambda node, control: (node, control, 'set')
    lacks = lambda node, control: (node, control, 'empty')
    doc = lambda types: (B_GET_INVOICE, x['invoice_type'], list(types))
    journal = [has(B_GET_INVOICE, x['invoice_journal']), has(B_GET_JOURNAL, x['journal_default']),
               lacks(None, x['line_account'])]
    product_known = [has(None, line_product), has(B_GET_VARIANT, x['variant_product'])]
    category_known = product_known + [has(B_GET_PRODUCT, x['product_category'])]

    def nothing_from(product_account, category_account):
        """The four ways the product and its category give no account."""
        return [[lacks(None, line_product)],
                [has(None, line_product), lacks(B_GET_VARIANT, x['variant_product'])],
                product_known + [lacks(B_GET_PRODUCT, product_account), lacks(B_GET_PRODUCT, x['product_category'])],
                category_known + [lacks(B_GET_PRODUCT, product_account), lacks(B_GET_CATEGORY, category_account)]]

    out = []
    for side, types, product_account, category_account, word in (
            ('Customer document', I.CUSTOMER_TYPES, x['product_income'], x['category_income'], 'Income'),
            ('Vendor document', I.VENDOR_TYPES, x['product_expense'], x['category_expense'], 'Expense')):
        base = [has(None, line_invoice), doc(types)]
        out += [
            (f"{side} — the product's {word} Account", [base + product_known + [has(B_GET_PRODUCT, product_account)]],
             f"Take the product's {word} Account", (B_GET_PRODUCT, product_account)),
            (f"{side} — the category's {word} Account",
             [base + category_known + [lacks(B_GET_PRODUCT, product_account), has(B_GET_CATEGORY, category_account)]],
             f"Take the category's {word} Account", (B_GET_CATEGORY, category_account)),
            (f"{side} — the journal's Default Account",
             [base + journal + group for group in nothing_from(product_account, category_account)],
             f"Take the journal's Default Account ({side.lower()})", (B_GET_JOURNAL, x['journal_default'])),
        ]
    out.append(("Journal entry — the journal's Default Account",
                 [[has(None, line_invoice), doc(['Journal Entry'])] + journal],
                 "Take the journal's Default Account (journal entry)", (B_GET_JOURNAL, x['journal_default'])))
    return out


def b_nodes(x):
    """The five searches and the gateway with its seven paths and steps, for `batch-add`. Search filters, path names
    and conditions and the steps' field writes are all written again afterwards and read back: batch-add sends a
    search's filter as `operateCondition`, which the UI never reads, and drops path names (BUILDING.md)."""
    alias = {B_GET_INVOICE: 'invoice', B_GET_VARIANT: 'variant', B_GET_PRODUCT: 'product',
             B_GET_CATEGORY: 'category', B_GET_JOURNAL: 'journal'}
    nodes = [{'nodeAlias': alias[name], 'nodeType': 'get_single', 'name': name,
              'config': {'worksheet': worksheet, 'execute_type': CONTINUE_WHEN_NOT_FOUND}}
             for name, worksheet, _, _ in b_searches(x)]
    paths = []
    for i, (name, _, step, (source, control)) in enumerate(b_paths(x)):
        paths.append({'alias': f'path{i}', 'name': name, 'nodes': [
            {'nodeAlias': f'step{i}', 'nodeType': 'update_record', 'name': step,
             'config': {'target': {'node': {'nodeAlias': 'trigger'}}, 'worksheet': x['lines'],
                        'fields': [{'fieldId': x['line_account']['controlId'], 'type': RELATION,
                                    'valueRef': {'kind': 'field', 'node': {'nodeAlias': alias[source]},
                                                 'fieldId': control['controlId']}}]}}]})
    nodes.append({'nodeAlias': 'which', 'nodeType': 'branch', 'name': B_GATEWAY,
                  'config': {'mode': 'exclusive', 'paths': paths}})
    return nodes


def b_trigger_filter(x, workflow):
    """The trigger's condition: a product line — and, for a new line, one with no Account."""
    import invlines as L
    items = [{'left': {'node': {'nodeAlias': 'trigger'}, 'fieldId': x['line_type']['controlId'], '_filedTypeId': 11,
                       '_filedValue': 'Display Type'},
              'op': 'in', 'right': {'kind': 'literal', 'values': [{'key': L.PRODUCT_LINE, 'value': 'Product',
                                                                   'isDeleted': False}]}}]
    if workflow == B_NEW_LINE:
        items.append({'left': {'node': {'nodeAlias': 'trigger'}, 'fieldId': x['line_account']['controlId'],
                               '_filedTypeId': RELATION, '_enumDefault': 1, '_filedValue': 'Account'}, 'op': 'empty'})
    return {'logic': 'and', 'items': items}


def b_trigger_want(x, workflow):
    import invlines as L
    fields = [x['line_product']['controlId']] if workflow == B_PRODUCT_CHANGED else []
    shape = [[(x['line_type']['controlId'], '1', [L.PRODUCT_LINE])] +
             ([(x['line_account']['controlId'], EMPTY_ID, [])] if workflow == B_NEW_LINE else [])]
    return dict(appId=x['lines'], triggerId=B_EVENTS[workflow][1], fields=sorted(fields), condition=shape,
                name=B_TRIGGER_NAMES[workflow])


def b_trigger_state(pid, start):
    t = node_get(pid, start)
    shape = [[(c.get('filedId'), str(c.get('conditionId')),
               sorted(((v.get('value') or {}).get('key') if isinstance(v.get('value'), dict) else v.get('value'))
                      for v in c.get('conditionValues') or []))
              for c in group] for group in t.get('operateCondition') or []]
    return dict(appId=t.get('appId'), triggerId=str(t.get('triggerId')), fields=sorted(t.get('assignFieldIds') or []),
                condition=shape, name=t.get('name'))


def b_search_condition(node_id, source_id, relation):
    """Record ID equals the Relation on the source record — the UI's shape of a search filter (invoices.journal_of)
    — ignored when abnormal: an empty Relation would otherwise fail the whole run."""
    return {'nodeId': node_id, 'nodeType': 7, 'actionId': '406', 'filedId': 'rowid', 'filedValue': 'Record ID',
            'filedTypeId': 2, 'enumDefault': 0, 'conditionId': EQUALS_ID, 'sourceType': 0,
            'ignoreEmpty': IGNORE_WHEN_ABNORMAL,
            'conditionValues': [{'nodeId': source_id, 'controlId': relation['controlId'], 'value': '',
                                 'sureNodeId': source_id}]}


def b_search_state(pid, node_id):
    d = node_get(pid, node_id)
    conds = [(c.get('filedId'), str(c.get('conditionId')), c.get('ignoreEmpty'),
              [(v.get('nodeId'), v.get('controlId')) for v in c.get('conditionValues') or []])
             for flt in d.get('filters') or [] for group in flt.get('conditions') or [] for c in group]
    return dict(appId=d.get('appId'), actionId=str(d.get('actionId')), executeType=d.get('executeType'), filters=conds)


def b_search_want(worksheet, source_id, relation):
    return dict(appId=worksheet, actionId='406', executeType=CONTINUE_WHEN_NOT_FOUND,
                filters=[('rowid', EQUALS_ID, IGNORE_WHEN_ABNORMAL, [(source_id, relation['controlId'])])])


def b_path_conditions(x, start, byname, groups):
    """A path's condition groups in the wire shape `node save --type 2` takes (`operateCondition`)."""
    import invoices as I
    out = []
    for group in groups:
        wire = []
        for node, control, op in group:
            node_id = start if node is None else byname[node]['id']
            if isinstance(op, list):
                wire.append({'nodeId': node_id, 'filedId': control['controlId'], 'filedValue': control['controlName'],
                             'filedTypeId': 11, 'enumDefault': 0, 'conditionId': IS_ANY_OF, 'sourceType': 0,
                             'conditionValues': [{'value': {'key': I.OPTION_KEY['Type'][label], 'value': label,
                                                            'isDeleted': False}} for label in op]})
            else:
                wire.append({'nodeId': node_id, 'filedId': control['controlId'], 'filedValue': control['controlName'],
                             'filedTypeId': RELATION, 'enumDefault': 1,
                             'conditionId': EMPTY_ID if op == 'empty' else NOT_EMPTY_ID, 'sourceType': 0,
                             'conditionValues': []})
        out.append(wire)
    return out


def b_step_fields(x, byname, source, control):
    node = byname[source]['id']
    return [{'fieldId': x['line_account']['controlId'], 'type': RELATION, 'addType': 0, 'fieldValue': '',
             'fieldValueId': control['controlId'], 'nodeId': node, 'sureNodeId': node, 'nodeAppType': 1}]


def b_step_state(pid, node_id):
    d = node_get(pid, node_id)
    return dict(selectNodeId=d.get('selectNodeId'), appId=d.get('appId'), isException=bool(d.get('isException')),
                fields=[(f.get('fieldId'), f.get('nodeId'), f.get('fieldValueId')) for f in d.get('fields') or []])


def b_workflow_id(workflow):
    pid = hap.ids().get('workflows', {}).get(workflow)
    if pid:
        return pid
    return {w['name']: w.get('id') or w.get('processId') for w in hap.listing('workflow', 'list', APP)}.get(workflow)


def automation_b_differences(workflow, x=None):
    """One of the two workflows read back against §1: trigger, the five searches in order with their filters, the
    gateway and its seven paths with their conditions, each path's one update step, name, description, published."""
    x = x or b_ids()
    pid = b_workflow_id(workflow)
    if not pid:
        return [f'{workflow}: not built']
    proc, byname = nodes_by_name(pid)
    start, out = proc['startEventId'], []
    t, want = b_trigger_state(pid, start), b_trigger_want(x, workflow)
    if t != want:
        out.append(f'{workflow}: trigger {t} != {want}')
    missing = [n for n in B_SEARCH_ORDER + (B_GATEWAY,) if n not in byname]
    if missing:
        return out + [f'{workflow}: missing {missing}']
    chain, node = [], proc['flowNodeMap'][start].get('nextId')
    while node and node in proc['flowNodeMap'] and proc['flowNodeMap'][node].get('typeId') == 7:
        chain.append(proc['flowNodeMap'][node]['name'])
        node = proc['flowNodeMap'][node].get('nextId')
    if chain != list(B_SEARCH_ORDER) or node != byname[B_GATEWAY]['id']:
        out.append(f'{workflow}: the trigger runs through {chain} into {proc["flowNodeMap"].get(node, {}).get("name")!r}')
    for name, worksheet, source, relation in b_searches(x):
        source_id = start if source is None else byname[source]['id']
        got = b_search_state(pid, byname[name]['id'])
        want = b_search_want(worksheet, source_id, relation)
        if got != want:
            out.append(f'{workflow} / {name}: {got} != {want}')
    gateway = byname[B_GATEWAY]
    if gateway.get('gatewayType') != EXCLUSIVE or gateway.get('nextId') not in ('99', '', None):
        out.append(f"{workflow}: gateway type {gateway.get('gatewayType')} next {gateway.get('nextId')}")
    paths = [proc['flowNodeMap'][i] for i in gateway.get('flowIds') or []]
    specs = b_paths(x)
    if [p.get('name') for p in paths] != [s[0] for s in specs]:
        out.append(f"{workflow}: paths {[p.get('name') for p in paths]}")
    for node, (name, groups, step, (source, control)) in zip(paths, specs):
        want = [[(c['nodeId'], c['filedId'], c['conditionId'],
                  sorted(v['value']['key'] for v in c['conditionValues']))
                 for c in group] for group in b_path_conditions(x, start, byname, groups)]
        if path_state(pid, node['id']) != want:
            out.append(f'{workflow} / path {name!r}: {path_state(pid, node["id"])} != {want}')
        nxt = proc['flowNodeMap'].get(node.get('nextId'))
        if not nxt or nxt.get('name') != step or nxt.get('typeId') != 6 or nxt.get('nextId') not in ('', '99', None):
            out.append(f'{workflow} / path {name!r} runs into {nxt and nxt.get("name")!r}')
            continue
        got = b_step_state(pid, nxt['id'])
        wanted = dict(selectNodeId=start, appId=x['lines'], isException=False,
                      fields=[(x['line_account']['controlId'], byname[source]['id'], control['controlId'])])
        if got != wanted:
            out.append(f'{workflow} / {step!r}: {got} != {wanted}')
    info = hap.run('workflow', 'get', pid)
    info = info.get('data', info)
    if (info.get('name'), info.get('explain') or '') != (workflow, B_DESCS[workflow]):
        out.append(f"{workflow}: name / description {info.get('name')!r} / {info.get('explain')!r}")
    if not info.get('enabled') or info.get('publishStatus') != 2:
        out.append(f"{workflow}: enabled={info.get('enabled')} publishStatus={info.get('publishStatus')}")
    return out


def build_automation_b(workflow, x):
    """Create one of the two workflows if missing, then bring every part up to spec in place, republishing only when
    something was written. No node is ever deleted."""
    from hap_cli.core.workflow_node_dsl import translate_condition_group
    pid = b_workflow_id(workflow)
    if not pid:
        out = hap.run('workflow', 'create', '-c', hap.ids()['org'], '-n', workflow, '-a', APP, '--type', 'worksheet',
                      '-d', B_DESCS[workflow])
        data_ = out.get('data', out) if isinstance(out, dict) else out
        pid = data_ if isinstance(data_, str) else (data_.get('id') or data_.get('processId'))
        if not pid:
            sys.exit(f'no process id in `workflow create` output: {out}')
        print(f'  created {workflow}: {pid}')
    C.remember('workflows', workflow, pid)
    proc, byname = nodes_by_name(pid)
    print('  backup:', hap.backup('accounts_b_automation_' + B_EVENTS[workflow][0], proc))
    changed = False
    if B_GATEWAY not in byname:
        args = ['workflow', 'node', 'batch-add', pid, '--nodes', json.dumps(b_nodes(x), ensure_ascii=False),
                '--trigger-worksheet', x['lines'], '--trigger-event', B_EVENTS[workflow][0], '--trigger-alias', 'trigger',
                '--trigger-filter', json.dumps(b_trigger_filter(x, workflow), ensure_ascii=False)]
        if workflow == B_PRODUCT_CHANGED:
            args += ['--trigger-fields', x['line_product']['controlId']]
        hap.run(*args)
        proc, byname = nodes_by_name(pid)
        changed = True
        print('  searches, gateway, paths and steps added')
    start = proc['startEventId']
    want = b_trigger_want(x, workflow)
    live = b_trigger_state(pid, start)
    if {k: live[k] for k in ('appId', 'triggerId', 'fields', 'condition')} != \
            {k: want[k] for k in ('appId', 'triggerId', 'fields', 'condition')}:
        condition = translate_condition_group(b_trigger_filter(x, workflow), {'trigger': start})
        hap.run('workflow', 'node', 'save', pid, start, '--type', '0', '-n', B_TRIGGER_NAMES[workflow], '-c', json.dumps(
            {'appId': x['lines'], 'appType': 1, 'triggerId': B_EVENTS[workflow][1], 'assignFieldIds': want['fields'],
             'operateCondition': condition, 'returns': []}, ensure_ascii=False))
        changed = True
        print(f'  trigger rewritten: {b_trigger_state(pid, start)}')
    if b_trigger_state(pid, start)['name'] != B_TRIGGER_NAMES[workflow]:
        hap.run('workflow', 'node', 'rename', pid, start, '-n', B_TRIGGER_NAMES[workflow])
        changed = True
    info = hap.run('workflow', 'get', pid)
    info = info.get('data', info)
    if (info.get('name'), info.get('explain') or '') != (workflow, B_DESCS[workflow]):
        hap.run('workflow', 'update', pid, '-n', workflow, '-d', B_DESCS[workflow])
        changed = True
    proc, byname = nodes_by_name(pid)
    for name, worksheet, source, relation in b_searches(x):
        node = byname[name]
        source_id = start if source is None else byname[source]['id']
        want_state = b_search_want(worksheet, source_id, relation)
        if b_search_state(pid, node['id']) != want_state:
            hap.run('workflow', 'node', 'save', pid, node['id'], '--type', '7', '-n', name, '-c', json.dumps(
                {'actionId': '406', 'appId': worksheet, 'selectNodeId': '',
                 'filters': [{'spliceType': 2, 'conditions': [[b_search_condition(node['id'], source_id, relation)]]}],
                 'sorts': [{'controlId': 'ctime', 'controlType': 16, 'isAsc': True}],
                 'executeType': CONTINUE_WHEN_NOT_FOUND}, ensure_ascii=False))
            changed = True
            got = b_search_state(pid, node['id'])
            if got != want_state:
                sys.exit(f'{workflow} / {name}: read back {got}, want {want_state}')
    gateway = byname[B_GATEWAY]
    paths = [proc['flowNodeMap'][i] for i in gateway.get('flowIds') or []]
    specs = b_paths(x)
    if len(paths) != len(specs):
        sys.exit(f'{workflow}: {len(paths)} paths, want {len(specs)} — left for a person to look at')
    by_step = {}
    for node in paths:
        nxt = proc['flowNodeMap'].get(node.get('nextId'))
        by_step.setdefault(nxt.get('name') if nxt else None, []).append((node, nxt))
    for name, groups, step, (source, control) in specs:
        found = by_step.get(step) or []
        if len(found) != 1 or found[0][1].get('typeId') != 6:
            sys.exit(f'{workflow}: {len(found)} path(s) run into {step!r} — left for a person to look at')
        node, nxt = found[0]
        changed |= set_path(pid, node, name, b_path_conditions(x, start, byname, groups))
        wanted = b_step_fields(x, byname, source, control)
        state = b_step_state(pid, nxt['id'])
        if (state['selectNodeId'], state['fields'], state['isException']) != \
                (start, [(x['line_account']['controlId'], byname[source]['id'], control['controlId'])], False):
            hap.run('workflow', 'node', 'save', pid, nxt['id'], '--type', '6', '-n', step, '-c', json.dumps(
                {'actionId': '2', 'appId': x['lines'], 'appType': 1, 'selectNodeId': start, 'fields': wanted},
                ensure_ascii=False))
            changed = True
    proc, _ = nodes_by_name(pid)
    order = [proc['flowNodeMap'][i].get('name') for i in proc['flowNodeMap'][gateway['id']].get('flowIds') or []]
    if order != [s[0] for s in specs]:
        print(f'  note: the gateway lists its paths as {order}')
    info = hap.run('workflow', 'get', pid)
    info = info.get('data', info)
    if changed or not info.get('enabled') or info.get('publishStatus') != 2:
        result = C.publish(pid)
        print('  published:', result)
        if not result.get('isPublish'):
            sys.exit(f'{workflow}: publish failed: {result}')
    else:
        print(f'  {workflow}: already built and published; nothing written')
    left = automation_b_differences(workflow, x)
    if left:
        sys.exit(f'{workflow} read back with differences:\n  ' + '\n  '.join(left))
    print(C.structure(pid))


def step_b_automation():
    """B · Invoice Lines: fill the account — the two workflows, built and read back."""
    guard()
    x = b_ids()
    before = b_snapshot()
    for workflow in (B_NEW_LINE, B_PRODUCT_CHANGED):
        print(f'  ── {workflow}')
        build_automation_b(workflow, x)
    b_expect(before, 'automation B (no control may change)')


# ── B7 · the account fields hidden by role ──────────────────────────────────

def step_b_visibility():
    """Roles (§1): Journals' five accounts, Products' and Product Categories' Income and Expense Account and Invoice
    Lines' Account hidden from **Invoicing**; Contacts' Account Receivable and Account Payable hidden from Invoicing
    and **Accounting Read-only**. HAP's fine-grained role carries a switch per field, so this is built field by field
    — by roles.py, which owns the roles (HIDDEN_FIELDS), through its `create` step. No control may change."""
    guard()
    import roles
    before = b_snapshot()
    roles.step_create()
    b_expect(before, 'roles.py create (no control may change)')
    return roles.step_check()


# ── B8 · the references — Records step 2 ────────────────────────────────────
#
# Every contact → 124000 / 221100 and every category → 410000 / 510000 (the company defaults every one of them
# reads on the tenant, TEST records included); INV, BILL and BNK1 as the extract's journal table; the eight tenant
# invoice lines → 410000; nothing on Products. Codes come from data/casimir-accounts.json, never from here. Only a
# differing value is written, each record is read back at once, and nothing is ever cleared: a record the extract
# says carries no account and does carry one is reported, not overwritten.

def account_code_of():
    return {rowid: code for code, (rowid, _) in record_index().items()}


def read_accounts_on(worksheet, rowid):
    """(the record as `record get` returns it, {account field: the rowid it points at, or None})."""
    d = hap.run('worksheet', 'record', 'get', wid_of(worksheet), rowid, '-a', APP)['data']
    out = {}
    for name, alias, _, _ in B_FIELDS[worksheet]:
        linked = relation(d.get(alias))
        out[name] = linked[0][0] if linked else None
    return d, out


def reference_plan():
    """[(worksheet, rowid, title, {account field: Code, or None for "carries none"}, write?)] — every record Records
    step 2 speaks for. `write` is False where the extract says the record carries nothing: that is checked, never
    written."""
    d = data()
    defaults = d['company_defaults']
    plan = []
    receivable = defaults['res.partner.property_account_receivable_id']
    payable = defaults['res.partner.property_account_payable_id']
    for r in C.records(wid_of('Contacts'), APP):
        plan.append(('Contacts', r['rowid'], None, {'Account Receivable': receivable, 'Account Payable': payable}, True))
    income = defaults['product.category.property_account_income_categ_id']
    expense = defaults['product.category.property_account_expense_categ_id']
    for r in C.records(wid_of('Product Categories'), APP):
        plan.append(('Product Categories', r['rowid'], None, {'Income Account': income, 'Expense Account': expense},
                     True))
    for r in C.records(wid_of('Products'), APP):
        plan.append(('Products', r['rowid'], None, {'Income Account': None, 'Expense Account': None}, False))
    field_of = {alias: name for name, alias, _, _ in B_FIELDS['Journals']}
    journals = {code: values for code, values in d['journals'].items() if not code.startswith('_')}
    for r in C.records(wid_of('Journals'), APP):
        got = hap.run('worksheet', 'record', 'get', wid_of('Journals'), r['rowid'], '-a', APP)['data']
        codes = {name: None for name in field_of.values()}
        codes.update({field_of[alias]: code for alias, code in journals.get(got.get('code'), {}).items()})
        plan.append(('Journals', r['rowid'], None, codes, got.get('code') in journals))
    import invlines as L
    documents = L.invoice_numbers()
    lines = {L.seed_key(line): line for line in L.read_lines().values()}
    for ref, codes in d['invoice_lines'].items():
        if ref.startswith('_'):
            continue
        invoice_row = documents.get(ref, (None,))[0]
        for sequence, code in enumerate(codes):
            line = lines.get((invoice_row, sequence))
            if not line:
                sys.exit(f'no line {sequence} on {ref} — run invlines.py seed first')
            plan.append(('Invoice Lines', line['rowid'], f'{ref} line {sequence}', {'Account': code}, True))
    return plan


def title_of(worksheet, d, fallback):
    if worksheet in ('Contacts', 'Product Categories'):
        return d.get('complete_name') or fallback or '(no name)'
    if worksheet == 'Journals':
        return f"{d.get('code')} {d.get('name')}"
    return fallback or d.get('name') or '(no name)'


def step_b_references():
    """Records step 2, written where a value differs and read back record by record; then 07's amounts checked,
    since every line write starts the roll-up."""
    guard()
    controls = b_snapshot()
    codes = account_code_of()
    plan = reference_plan()
    backup = {}
    wrote, reported = [], []
    for worksheet, rowid, title, want, write in plan:
        d, have = read_accounts_on(worksheet, rowid)
        title = title_of(worksheet, d, title)
        backup[f'{worksheet} {rowid}'] = {n: codes.get(v, v) for n, v in have.items()}
        want_ids = {n: (account_rowid(code) if code else None) for n, code in want.items()}
        differing = [n for n in want if have[n] != want_ids[n]]
        if not differing:
            continue
        to_write = [n for n in differing if write and want_ids[n]]
        left = [n for n in differing if n not in to_write]
        if left:
            reported.append(f'{worksheet} {title}: ' + ', '.join(f'{n} is {codes.get(have[n], have[n])}, the extract '
                                                                   f'says {want[n]}' for n in left))
        if not to_write:
            continue
        if not wrote:
            print('  backup:', hap.backup('accounts_b_records_pre_references', backup))
        fields = {name: c['controlId'] for name, c in C.fields(wid_of(worksheet)).items()}
        hap.run('worksheet', 'record', 'update', wid_of(worksheet), rowid, '-a', APP, '--fields-json', json.dumps(
            [{'id': fields[n], 'value': [want_ids[n]]} for n in to_write], ensure_ascii=False))
        _, back = read_accounts_on(worksheet, rowid)
        wrong = {n: codes.get(back[n], back[n]) for n in to_write if back[n] != want_ids[n]}
        if wrong:
            sys.exit(f'{worksheet} {title}: read back {wrong}, want { {n: want[n] for n in to_write} }')
        wrote.append((worksheet, title, {n: want[n] for n in to_write}))
        print(f"  {worksheet:<18} {title:<48} " + ', '.join(f'{n} {want[n]}' for n in to_write))
    hap.backup('accounts_b_records_pre_references_all', backup)
    print(f'  {len(wrote)} record(s) written and read back; {len(plan) - len(wrote)} already as the extract has them')
    for line in reported:
        print(f'  NOT WRITTEN  {line}')
    b_expect(controls, 'references (no control may change)')
    if any(w == 'Invoice Lines' for w, _, _ in wrote):
        print('  every line write starts 07\'s roll-up once; waiting for the runs to settle')
        time.sleep(25)
    import invlines as L
    bad = L.step_verify()
    return verify_b_references() + bad + len(reported)


def verify_b_references():
    """Records step 2 read back: every record of the plan, then the lines outside the seed (TEST lines) shown as they
    are."""
    codes = account_code_of()
    bad, seen = 0, set()
    for worksheet, rowid, title, want, write in reference_plan():
        d, have = read_accounts_on(worksheet, rowid)
        seen.add(rowid)
        got = {n: codes.get(v, v) for n, v in have.items()}
        ok = got == want
        bad += not ok
        print(f"  {'OK  ' if ok else 'DIFF'}  {worksheet:<18} {title_of(worksheet, d, title):<48} "
              + ', '.join(f'{n} {got[n] or "—"}' for n in got) + ('' if ok else f'   <- want {want}'))
    for r in C.records(wid_of('Invoice Lines'), APP):
        if r['rowid'] in seen:
            continue
        d, have = read_accounts_on('Invoice Lines', r['rowid'])
        print(f"  ·     Invoice Lines      {(d.get('move_name') or '') + ' ' + (d.get('name') or '')[:38]:<48} "
              f"Account {codes.get(have['Account'], have['Account']) or '—'}   (not in the seed)")
    print(f'  references: {bad} differing')
    return bad


# ── B9 · automation B, proved through the CLI on TEST records ───────────────
#
# Four TEST documents, each a draft named by its Customer Reference, and the TEST lines on them. The documents on
# the tenant's journals are new ones — Sales already holds drafts, and the bill on Purchases is cancelled at the end
# through the Cancel button's own workflow, so no tenant journal gains a draft entry its Archive guard would count.

B_TEST_DOCUMENTS = {  # Customer Reference -> (Type, the journal's Sequence Prefix)
    'TEST B customer invoice': ('Customer Invoice', 'INV'),
    'TEST B vendor bill': ('Vendor Bill', 'BILL'),
    'TEST B journal entry': ('Journal Entry', 'TSTDG'),     # TEST draft guard: Miscellaneous, no Default Account
    'TEST B entry on Sales': ('Journal Entry', 'INV'),
}
B_CANCEL_AFTER = ('TEST B vendor bill',)
B_TEST_PRODUCT, B_TEST_VARIANT = 'TEST Product', '[TEST-0001] TEST Product'   # TEST-0001; category TEST UI renamed
B_PLAIN_VARIANT = '[CONS-0002] Whiteboard Marker Set'   # no account of its own; category Goods / Consumables
B_NO_CATEGORY_VARIANT = '[TEST-0004] TEST Variant From UI'   # a TEST product with no category and no account
B_OWN_INCOME, B_OWN_EXPENSE, B_EXPLICIT = '420000', '510100', '421000'   # tenant accounts, none of them a TEST one


def b_documents():
    """The four TEST documents, created when missing: {Customer Reference: rowid}."""
    import invoices as I
    inv = C.fields(wid_of('Invoices'))
    cid = lambda n: inv[n]['controlId']
    refs = {r.get(cid('Customer Reference')): r['rowid'] for r in C.records(wid_of('Invoices'), APP)}
    journals = {}
    for r in C.records(wid_of('Journals'), APP):
        journals[hap.run('worksheet', 'record', 'get', wid_of('Journals'), r['rowid'], '-a', APP)['data'].get('code')] = \
            r['rowid']
    out = {}
    for ref, (kind, code) in B_TEST_DOCUMENTS.items():
        rowid = refs.get(ref)
        if not rowid:
            values = [{'id': cid('Number'), 'value': I.DRAFT},
                      {'id': cid('Type'), 'value': [I.OPTION_KEY['Type'][kind]]},
                      {'id': cid('Status'), 'value': [I.OPTION_KEY['Status']['Draft']]},
                      {'id': cid('Accounting Date'), 'value': time.strftime('%Y-%m-%d')},
                      {'id': cid('Journal'), 'value': [journals[code]]},
                      {'id': cid('Auto-post'), 'value': [I.OPTION_KEY['Auto-post']['No']]},
                      {'id': cid('Customer Reference'), 'value': ref}]
            if kind != 'Journal Entry':
                values.append({'id': cid('Tax mode'), 'value': [I.OPTION_KEY['Tax mode']['Tax Excluded']]})
            rowid = C.row_id(hap.run('worksheet', 'record', 'create', wid_of('Invoices'), '-a', APP, '--fields-json',
                                     json.dumps(values, ensure_ascii=False)))
            print(f'  created the TEST document {ref!r} ({kind}, journal {code}): {rowid}')
        C.remember('records', 'Invoices: ' + ref, rowid)
        out[ref] = rowid
    return out


def b_run_steps(instance_id):
    """The update step a run of automation B took, or None when it wrote nothing."""
    passed = [name for _, name in run_nodes(instance_id)]
    return next((name for name in passed if name.startswith('Take ')), None)


def b_described(runs):
    return [(r.get('createDate'), r.get('status'), b_run_steps(r['id']),
             (r.get('instanceLog') or {}).get('cause'), (r.get('instanceLog') or {}).get('causeMsg')) for r in runs]


def step_b_selfcheck():
    """Prove automation B through the CLI, on TEST records only — as built since 17 Sep 2026 11:42, when the journal's
    Default Account became a fill for an **empty** Account only (the coordinator's call; Odoo's rule).

    **The new-line workflow**, each case on a *TEST B2* line created once (a re-run finds it by its Label — the
    Invoice Lines title, which is also each run's title — and re-reads the run its create started):

      1. a customer invoice line whose product has no account of its own takes the category's 410000;
      2. a product given its own Income Account (420000) gives that one;
      4. a vendor bill line takes the category's Expense Account, 510000;
      5. a line created with an explicit Account (421000) keeps it, and no run starts;
      6. a line on a journal entry whose journal has no Default Account is left empty — no path matches;
      7. a product line with no Product takes the journal's Default Account;
      8. a journal entry on a journal with a Default Account takes it;
      9. a Section line starts no run;
     10. a product with no category (and no account of its own) takes the journal's Default Account.

    **The Product-change workflow** then walks every path of the gateway on the same lines, each walk ending where it
    started (a line found elsewhere, after an interrupted run, is first brought back, unchecked). An Account written
    alone starts neither workflow — that is how a walk empties the line or gives it an explicit account:

      3.  customer: the product's own Income Account, then the category's, each replacing the line's (line 1);
      3p. a product with no category and no account: a line **with** an Account keeps it; the same change on a line
          **without** one takes the journal's Default Account (line 2);
      3v. vendor: the product's own Expense Account; no Product keeps it; the category's replaces it; emptied, no
          Product takes the journal's 510000 (line 4);
      3n. customer, no Product: a line with an explicit Account keeps it; the category's replaces it; emptied, no
          Product takes the journal's 410000 (line 7);
      3e. a journal entry on Sales keeps an explicit Account and, emptied, takes the journal's; one on a journal with
          no Default Account stays empty either way (lines 8 and 6);

    and a write that leaves Product out starts neither workflow. The TEST product's own accounts are put back at the
    end. The *TEST B* lines of the builds before are no longer written to; the first build's failed run on *TEST B
    no product* is re-read as the LIMIT it recorded. `DIFF` is the build not doing what §1 and the coordinator's call
    say; `LIMIT` is platform behaviour recorded, not counted."""
    guard()
    import invlines as L
    x = b_ids()
    pids = {w: b_workflow_id(w) for w in (B_NEW_LINE, B_PRODUCT_CHANGED)}
    if not all(pids.values()):
        sys.exit('automation B is not built — run `automation-b` first')
    controls = b_snapshot()
    docs = b_documents()
    variants, units = L.titles(wid_of('Product Variants'), 'Display Name'), L.titles(wid_of('Units & Packagings'),
                                                                                     'Unit Name')
    variant_row = lambda name: L.row_of(variants, name, 'variant')
    unit_row = L.row_of(units, 'Units', 'unit')
    codes = account_code_of()
    lines_f = C.fields(wid_of('Invoice Lines'))
    lcid = lambda n: lines_f[n]['controlId']
    problems, limits = [], []

    def check(label, ok, detail):
        print(f"  {'OK   ' if ok else 'DIFF '}  {label}: {detail}")
        if not ok:
            problems.append(f'{label}: {detail}')

    def limit(label, detail):
        print(f'  LIMIT  {label}: {detail}')
        limits.append(f'{label}: {detail}')

    def account(rowid):
        return codes.get(read_accounts_on('Invoice Lines', rowid)[1]['Account'])

    def existing(label):
        return next((r['rowid'] for r in C.records(wid_of('Invoice Lines'), APP)
                     if (r.get(lcid('Label')) or '') == label), None)

    def runs_titled(workflow, label):
        return [r for r in all_runs(pids[workflow]) if r.get('title') == label]

    def write(action, expect_new, expect_changed):
        """Run `action` and return the new runs of each workflow, told apart by instance id: the runs expected are
        waited for first, then a short window is watched for the ones that must not come (a run registers some
        seconds after its write)."""
        snaps = {w: run_snapshot(pids[w]) for w in pids}
        result = action()
        got = {}
        for workflow, n in sorted(((B_NEW_LINE, expect_new), (B_PRODUCT_CHANGED, expect_changed)),
                                  key=lambda item: -item[1]):
            got[workflow] = wait_new_runs(pids[workflow], snaps[workflow], n, seconds=90 if n else 12)
        return result, got[B_NEW_LINE], got[B_PRODUCT_CHANGED]

    def line(label, doc, sequence, variant=None, kind='Product', explicit=None):
        """A TEST line, created once: (rowid, the new-line runs its create started, the change runs, created now)."""
        rowid = existing(label)
        if rowid:                                   # the run its create started: the oldest one bearing its title
            C.remember('records', 'Invoice Lines: ' + label, rowid)
            return rowid, runs_titled(B_NEW_LINE, label)[-1:], [], False
        values = [{'id': lcid('Invoice'), 'value': [docs[doc]]}, {'id': lcid('Sequence'), 'value': sequence},
                  {'id': lcid('Display Type'), 'value': [L.OPTION_KEY['Display Type'][kind]]},
                  {'id': lcid('Label'), 'value': label}]
        if kind == 'Product':
            values += [{'id': lcid('Quantity'), 'value': 1}, {'id': lcid('Unit'), 'value': [unit_row]},
                       {'id': lcid('Unit Price'), 'value': 10}, {'id': lcid('Discount (%)'), 'value': 0}]
            if variant:
                values.append({'id': lcid('Product'), 'value': [variant_row(variant)]})
        if explicit:
            values.append({'id': lcid('Account'), 'value': [account_rowid(explicit)]})
        expect = 1 if kind == 'Product' and not explicit else 0
        created, new, changed = write(lambda: C.row_id(hap.run('worksheet', 'record', 'create', wid_of('Invoice Lines'),
                                                                 '-a', APP, '--fields-json',
                                                                 json.dumps(values, ensure_ascii=False))), expect, 0)
        C.remember('records', 'Invoice Lines: ' + label, created)
        print(f'  created {label!r} on {doc}: {created}')
        return created, new, changed, True

    # the TEST product's own accounts, for the paths that read them; put back at the end
    products = {hap.run('worksheet', 'record', 'get', wid_of('Products'), r['rowid'], '-a', APP)['data'].get('name'):
                r['rowid'] for r in C.records(wid_of('Products'), APP)}
    product = products[B_TEST_PRODUCT]
    product_fields = C.fields(wid_of('Products'))

    def set_own(income, expense):
        hap.run('worksheet', 'record', 'update', wid_of('Products'), product, '-a', APP, '--fields-json', json.dumps(
            [{'id': product_fields['Income Account']['controlId'], 'value': [account_rowid(income)] if income else []},
             {'id': product_fields['Expense Account']['controlId'],
              'value': [account_rowid(expense)] if expense else []}]))
        got = read_accounts_on('Products', product)[1]
        return codes.get(got['Income Account']), codes.get(got['Expense Account'])

    was = tuple(codes.get(v) for v in read_accounts_on('Products', product)[1].values())
    if any(v not in (None, B_OWN_INCOME, B_OWN_EXPENSE) for v in was):
        sys.exit(f'{B_TEST_PRODUCT} carries accounts of its own {was} — left for a person to look at')
    check(f'{B_TEST_PRODUCT} given its own Income and Expense Accounts',
          set_own(B_OWN_INCOME, B_OWN_EXPENSE) == (B_OWN_INCOME, B_OWN_EXPENSE), f'{B_OWN_INCOME} / {B_OWN_EXPENSE}')

    # ── the new-line workflow ──
    tests = [
        ('1. customer invoice, the product has no account of its own', 'TEST B2 category account',
         'TEST B customer invoice', 1010, B_PLAIN_VARIANT, 'Product', None,
         "Take the category's Income Account", '410000'),
        ('2. customer invoice, the product has its own Income Account', 'TEST B2 product account',
         'TEST B customer invoice', 1020, B_TEST_VARIANT, 'Product', None, "Take the product's Income Account",
         B_OWN_INCOME),
        ('4. vendor bill', 'TEST B2 vendor bill line', 'TEST B vendor bill', 1010, B_PLAIN_VARIANT, 'Product', None,
         "Take the category's Expense Account", '510000'),
        ('5. created with an explicit Account', 'TEST B2 explicit account', 'TEST B customer invoice', 1030,
         B_PLAIN_VARIANT, 'Product', B_EXPLICIT, None, B_EXPLICIT),
        ('6. journal entry on a journal with no Default Account', 'TEST B2 entry without default',
         'TEST B journal entry', 1010, B_PLAIN_VARIANT, 'Product', None, None, None),
        ('7. a product line with no Product', 'TEST B2 no product', 'TEST B customer invoice', 1045, None, 'Product',
         None, "Take the journal's Default Account (customer document)", '410000'),
        ('8. journal entry on a journal with a Default Account', 'TEST B2 entry on Sales line', 'TEST B entry on Sales',
         1010, B_PLAIN_VARIANT, 'Product', None, "Take the journal's Default Account (journal entry)", '410000'),
        ('9. a Section line', 'TEST B2 section', 'TEST B customer invoice', 1050, None, 'Section', None, None, None),
        ('10. a product with no category and no account of its own', 'TEST B2 product without a category',
         'TEST B customer invoice', 1060, B_NO_CATEGORY_VARIANT, 'Product', None,
         "Take the journal's Default Account (customer document)", '410000'),
    ]
    rows = {}
    old = existing('TEST B no product')
    if old:                                          # the first build's evidence, kept and not written to
        C.remember('records', 'Invoice Lines: TEST B no product', old)
        first = runs_titled(B_NEW_LINE, 'TEST B no product')[-1:]
        limit('a product line with no Product, in the first build (a search on an empty Relation)',
              f'{b_described(first)} — the run failed at "Get the product variant"; Account '
              f'{account(old) or "—"}. The search steps now ignore an abnormal condition and the paths guard it (7)')
    for title, label, doc, sequence, variant, kind, explicit, step, want in tests:
        rowid, new, changed, fresh = line(label, doc, sequence, variant, kind, explicit)
        rows[label] = rowid
        got = account(rowid)
        steps = [b_run_steps(r['id']) for r in new]
        if kind != 'Product' or explicit:
            ok = not new and not changed and got == want
            detail = f'no run of either workflow ({len(new)} / {len(changed)}); Account {got or "—"}'
        elif step is None:
            causes = [((r.get('instanceLog') or {}).get('cause'), (r.get('instanceLog') or {}).get('causeMsg'))
                      for r in new]
            ok = len(new) == 1 and steps == [None] and new[0].get('status') == 3 and got is None and not changed
            detail = f'{len(new)} run(s) {b_described(new)}; Account {got or "—"}; causes {causes}'
        else:
            ok = len(new) == 1 and steps == [step] and new[0].get('status') == 2 and got == want and not changed
            detail = f'{len(new)} run(s) {b_described(new)}; Account {got or "—"}'
        check(title + ('' if fresh else ' (created in an earlier run; the run its create started re-read)'), ok,
              detail)

    # ── the Product-change workflow, through every path of the final gateway ──
    def change(title, rowid, variant, step, want):
        """Set the line's Product (None clears it); one run of the change workflow must take `step` (None: no path,
        the run stops at the gateway) and Account must then read `want`."""
        value = [variant_row(variant)] if variant else []
        _, new, changed = write(lambda: hap.run('worksheet', 'record', 'update', wid_of('Invoice Lines'), rowid, '-a',
                                                APP, '--fields-json', json.dumps([{'id': lcid('Product'),
                                                                                   'value': value}])), 0, 1)
        got = account(rowid)
        steps = [b_run_steps(r['id']) for r in changed]
        status = [r.get('status') for r in changed]
        ok = not new and steps == [step] and status == [2 if step else 3] and got == want
        check(f'{title}: Product → {variant or "none"}', ok,
              f'{len(changed)} change run(s) {b_described(changed)}, {len(new)} new-line run(s); Account {got or "—"}')

    def set_account(title, rowid, code):
        """Write Account alone (None empties it): neither workflow may start, and Account must then read `code`."""
        value = [account_rowid(code)] if code else []
        _, new, changed = write(lambda: hap.run('worksheet', 'record', 'update', wid_of('Invoice Lines'), rowid, '-a',
                                                APP, '--fields-json', json.dumps([{'id': lcid('Account'),
                                                                                   'value': value}])), 0, 0)
        got = account(rowid)
        check(f'{title}: Account → {code or "none"}, written alone', not new and not changed and got == code,
              f'{len(new)} / {len(changed)} run(s); Account {got or "—"}')

    def walk(title, rowid, start, stops):
        """Walk a line from `start` — (variant or None, account code or None), where the walk also ends — through
        `stops`: ('product', variant or None, the step the change run takes or None, the Account then) or ('account',
        code or None). A line found elsewhere (an interrupted run) is first brought to `start`, unchecked."""
        now = (read_line_product(rowid), account(rowid))
        if now != start:
            variant, code = start
            if now[0] != variant:
                write(lambda: hap.run('worksheet', 'record', 'update', wid_of('Invoice Lines'), rowid, '-a', APP,
                                      '--fields-json', json.dumps([{'id': lcid('Product'), 'value':
                                                                    [variant_row(variant)] if variant else []}])), 0, 1)
            if account(rowid) != code:
                hap.run('worksheet', 'record', 'update', wid_of('Invoice Lines'), rowid, '-a', APP, '--fields-json',
                        json.dumps([{'id': lcid('Account'), 'value': [account_rowid(code)] if code else []}]))
            back = (read_line_product(rowid), account(rowid))
            print(f'  setup  {title}: found at {now}, brought to {back}')
            if back != start:
                sys.exit(f'{title}: could not bring the line to {start}; it reads {back}')
        for stop in stops:
            if stop[0] == 'product':
                change(title, rowid, *stop[1:])
            else:
                set_account(title, rowid, stop[1])

    customer_default = "Take the journal's Default Account (customer document)"
    walk('3. customer invoice (line 1)', rows['TEST B2 category account'], (B_PLAIN_VARIANT, '410000'), [
        ('product', B_TEST_VARIANT, "Take the product's Income Account", B_OWN_INCOME),
        ('product', B_PLAIN_VARIANT, "Take the category's Income Account", '410000')])
    walk('3p. customer invoice, a product with no category (line 2)', rows['TEST B2 product account'],
         (B_TEST_VARIANT, B_OWN_INCOME), [
             ('product', B_NO_CATEGORY_VARIANT, None, B_OWN_INCOME),          # the line has an Account: it keeps it
             ('product', B_TEST_VARIANT, "Take the product's Income Account", B_OWN_INCOME),
             ('account', None),
             ('product', B_NO_CATEGORY_VARIANT, customer_default, '410000'),  # the same change, no Account: the journal's
             ('product', B_TEST_VARIANT, "Take the product's Income Account", B_OWN_INCOME)])
    walk('3v. vendor bill (line 4)', rows['TEST B2 vendor bill line'], (B_PLAIN_VARIANT, '510000'), [
        ('product', B_TEST_VARIANT, "Take the product's Expense Account", B_OWN_EXPENSE),
        ('product', None, None, B_OWN_EXPENSE),
        ('product', B_PLAIN_VARIANT, "Take the category's Expense Account", '510000'),
        ('account', None),
        ('product', None, "Take the journal's Default Account (vendor document)", '510000'),
        ('product', B_PLAIN_VARIANT, "Take the category's Expense Account", '510000')])
    walk('3n. customer invoice, no Product (line 7)', rows['TEST B2 no product'], (None, '410000'), [
        ('product', B_PLAIN_VARIANT, "Take the category's Income Account", '410000'),
        ('account', B_EXPLICIT),
        ('product', None, None, B_EXPLICIT),
        ('product', B_PLAIN_VARIANT, "Take the category's Income Account", '410000'),
        ('account', None),
        ('product', None, customer_default, '410000')])
    walk('3e. journal entry on Sales (line 8)', rows['TEST B2 entry on Sales line'], (B_PLAIN_VARIANT, '410000'), [
        ('account', B_EXPLICIT),
        ('product', B_TEST_VARIANT, None, B_EXPLICIT),
        ('account', None),
        ('product', B_PLAIN_VARIANT, "Take the journal's Default Account (journal entry)", '410000')])
    walk('3e. journal entry with no Default Account (line 6)', rows['TEST B2 entry without default'],
         (B_PLAIN_VARIANT, None), [
             ('product', B_TEST_VARIANT, None, None),
             ('product', B_PLAIN_VARIANT, None, None)])

    first = rows['TEST B2 category account']
    _, new, changed = write(lambda: hap.run('worksheet', 'record', 'update', wid_of('Invoice Lines'), first, '-a', APP,
                                            '--fields-json', json.dumps([{'id': lcid('Quantity'), 'value': 2}])), 0, 0)
    check('3b. a write that leaves Product out (Quantity 2) starts neither workflow', not new and not changed,
          f'{len(new)} / {len(changed)} run(s); Account {account(first)}')
    hap.run('worksheet', 'record', 'update', wid_of('Invoice Lines'), first, '-a', APP, '--fields-json',
            json.dumps([{'id': lcid('Quantity'), 'value': 1}]))

    check(f'{B_TEST_PRODUCT} put back: no account of its own', set_own(None, None) == (None, None), '— / —')
    for ref in B_CANCEL_AFTER:
        status = hap.run('worksheet', 'record', 'get', wid_of('Invoices'), docs[ref], '-a', APP)['data'].get('state')
        if option_label(status) != 'Cancelled':
            hap.run('workflow', 'trigger', hap.ids()['workflows']['Invoices: Cancel'], '-s', docs[ref])
            for _ in range(30):
                status = hap.run('worksheet', 'record', 'get', wid_of('Invoices'), docs[ref], '-a',
                                 APP)['data'].get('state')
                if option_label(status) == 'Cancelled':
                    break
                time.sleep(1)
        check(f'{ref!r} cancelled through the Cancel workflow, so Purchases holds no new draft',
              option_label(status) == 'Cancelled', option_label(status))
    b_expect(controls, 'selfcheck-b (no control may change)')
    print('  TEST records: ' + json.dumps({**{f'Invoices: {k}': v for k, v in docs.items()},
                                          **{f'Invoice Lines: {k}': v for k, v in rows.items()}}, ensure_ascii=False))
    print('  selfcheck-b: ' + ('OK' if not problems else 'DIFFERENCES\n    ' + '\n    '.join(problems)))
    print(f'  platform limits recorded: {len(limits)}')
    return len(problems)


# ── B10 · checks ────────────────────────────────────────────────────────────

def step_b_check():
    """Part B's configuration read back against §1, exiting non-zero on a difference: each worksheet's accounts
    (type, target, alias, help, placeholder, place, tab, one-way dropdown, picker, default) and new tab, every
    control where its owner puts it and the owners' own layout checks, the Contacts tab rule, the five Journals rules
    and both Journals views' columns, the Invoice Lines rule, its Lines view and the Invoices subtable's columns,
    automation B's two workflows, the roles' per-field hiding (roles.py check), and a Chart of Accounts that gained
    nothing."""
    import invlines as L
    import journals as J
    import prodcat as P
    import roles
    problems = []
    for worksheet in B_FIELDS:
        problems += b_field_differences(worksheet)
        moves = owner_place_differences(worksheet)
        if moves:
            problems.append(f'{worksheet}: out of the place its script gives it: {moves}')
    problems += [f'prodcat.py layout: {n} {d}' for n, d in P.layout_differences(hap.controls(P.ws())).items()]
    problems += [f'journals.py layout: {n} {d}' for n, d in J.layout_differences(hap.controls(J.WORKSHEET)).items()]
    problems += [f'invlines.py layout: {n} {d}' for n, d in L.layout_differences(hap.controls(L.ws())).items()]
    problems += contacts_rule_differences() + journals_rule_differences() + lines_rule_differences()
    want = list(J.COLUMNS)
    for view, cols in columns_of('Journals', ('Journals', 'Archived')).items():
        if cols != (want, want):
            problems.append(f'Journals / {view}: columns {cols}')
    if columns_of('Invoice Lines', ('Lines',))['Lines'] != (list(L.VIEW_COLUMNS),) * 2:
        problems.append(f"Invoice Lines / Lines: columns {columns_of('Invoice Lines', ('Lines',))['Lines']}")
    if subtable_columns() != (list(L.SUBTABLE_COLUMNS),) * 2:
        problems.append(f'Invoices / {L.LINES_FIELD}: columns {subtable_columns()}')
    x = b_ids()
    for workflow in (B_NEW_LINE, B_PRODUCT_CHANGED):
        problems += automation_b_differences(workflow, x)
    coa = hap.by_name(hap.controls(ws()))
    if set(coa) != set(PLACE):
        problems.append(f'Chart of Accounts controls {sorted(set(coa) ^ set(PLACE))} — part B adds nothing there')
    tabs = [(c['controlName'], c['row'], (c.get('advancedSetting') or {}).get('showtype'))
            for c in hap.controls(wid_of('Product Categories'))
            if c['type'] == C.TAB or (c['type'] == RELATION and (c.get('advancedSetting') or {}).get('showtype') in ('2', '6'))]
    bar = [n for _, n in sorted((row, n) for n, row, show in tabs if show != '2')] + \
          [n for n, _, show in sorted(tabs, key=lambda t: t[1]) if show == '2']
    print(f"  Product Categories' tab bar, as pd-openweb orders it: {' · '.join(bar)}")
    problems += [f'roles: {n} difference(s) — see above' for n in [roles.step_check()] if n]
    print('  check-b: ' + ('OK — the accounts on Contacts, Products, Product Categories, Journals and Invoice Lines '
                           'with their tabs, places, pickers and defaults; the rules, columns and subtable; automation '
                           'B published with its guarded paths, the journal\'s Default Account only on an empty Account; '
                           'the roles\' per-field hiding; Chart of Accounts '
                           'unchanged' if not problems else 'DIFFERENCES\n    ' + '\n    '.join(problems)))
    return len(problems)


def step_b_runs():
    """Automation B's run history: per workflow, the runs by status and by the step they took."""
    for workflow in (B_NEW_LINE, B_PRODUCT_CHANGED):
        rows = all_runs(b_workflow_id(workflow))
        statuses, steps = {}, {}
        for r in rows:
            statuses[r.get('status')] = statuses.get(r.get('status'), 0) + 1
            key = (r.get('status'), b_run_steps(r['id']) or ((r.get('instanceLog') or {}).get('causeMsg') or 'no step'))
            steps.setdefault(key, []).append(r.get('title'))
        print(f'  {workflow}: {len(rows)} run(s), status counts {statuses} (2 completed · 3 stopped · 4 failed)')
        for (status, step), titles in sorted(steps.items(), key=lambda kv: str(kv[0])):
            print(f'    {len(titles):>2}  [{status}] {step}  {sorted(set(titles))}')


def step_b_rerun():
    """The owning scripts' steps whose tables this bundle extended, run again: each must write nothing — every
    control, and the rules and views of its own worksheet, compared before and after — and then check-b passes."""
    guard()
    import contacts as K
    import invlines as L
    import journals as J
    import prodcat as P
    import products as PR
    import roles
    steps = [('contacts.py layout', 'Contacts', K.step_layout), ('contacts.py rules', 'Contacts', K.step_rules),
             ('products.py layout', 'Products', PR.step_layout), ('prodcat.py layout', 'Product Categories', P.step_layout),
             ('journals.py layout', 'Journals', J.step_layout), ('journals.py rules', 'Journals', J.step_rules),
             ('journals.py views', 'Journals', J.step_views), ('invlines.py layout', 'Invoice Lines', L.step_layout),
             ('invlines.py rules', 'Invoice Lines', L.step_rules), ('invlines.py views', 'Invoice Lines', L.step_views),
             ('roles.py create', None, roles.step_create)]
    for label, worksheet, run in steps:
        print(f'\n  ── {label}')
        controls = b_snapshot()
        rules = rule_snapshot(worksheet) if worksheet else None
        views = view_snapshot(worksheet) if worksheet else None
        run()
        b_expect(controls, f'{label}, run again')
        if worksheet:
            rules_expect(rules, worksheet, f'{label}, run again')
            views_expect(views, worksheet, f'{label}, run again')
    print()
    return step_b_check()


def latest_baseline():
    found = sorted(Path(hap.BACKUPS).glob('partb_snapshot_baseline_*.json'))
    return found[-1] if found else None


def step_b_records(path=None):
    """Every record of the nine worksheets against the snapshot taken before part B (`backups/partb_snapshot_
    baseline_*.json`, not committed), field by field through `record get`: nothing may differ but the account fields
    this bundle seeds (verify-b reads those), and the only new records must be TEST ones."""
    path = Path(path) if path else latest_baseline()
    if not path or not path.exists():
        sys.exit('no baseline snapshot: backups/partb_snapshot_baseline_*.json')
    snap = json.loads(path.read_text(encoding='utf-8'))
    seeded = {alias for fields in B_FIELDS.values() for _, alias, _, _ in fields}
    bad = 0
    for worksheet, entry in snap['worksheets'].items():
        live = {}
        for r in C.records(entry['id'], APP):
            live[r['rowid']] = hap.run('worksheet', 'record', 'get', entry['id'], r['rowid'], '-a', APP)['data']
        gone = sorted(set(entry['records']) - set(live))
        added = sorted(set(live) - set(entry['records']))
        changed = {}
        for rowid, before in entry['records'].items():
            after = live.get(rowid)
            if after is None:
                continue
            # A control added since the snapshot reads back as a key of its own — a tab as "" — so a key that did not
            # exist before and holds nothing now is not a change to the record.
            keys = [k for k in sorted(set(before) | set(after)) if not k.startswith('_') and k not in seeded
                    and before.get(k) != after.get(k) and not (k not in before and after.get(k) in ('', None, [], 0))]
            if keys:
                changed[rowid] = {k: (before.get(k), after.get(k)) for k in keys}
        # A new record is a TEST one when any of its names says so: an Invoices document's title is its Number
        # ("Draft"), and its Customer Reference (`ref`) carries the TEST name.
        names = {r: [str(live[r].get(k) or '') for k in ('name', 'ref', 'display_name', 'complete_name')] for r in added}
        titles = [next((n for n in names[r] if n.startswith('TEST')), names[r][0] or r) for r in added]
        strays = [t for t in titles if not str(t).startswith('TEST')]
        bad += len(gone) + len(changed) + len(strays)
        print(f"  {'OK  ' if not (gone or changed or strays) else 'DIFF'}  {worksheet:<20} {len(entry['records'])} "
              f"before, {len(live)} now; {len(changed)} changed beyond the account references; gone {gone}; "
              f"new {titles}")
        for rowid, diff in changed.items():
            print(f'        {rowid}: ' + json.dumps(diff, ensure_ascii=False)[:600])
    print(f'  records-b against {path.name}: {bad} difference(s)')
    return bad


def read_line_product(rowid):
    d = hap.run('worksheet', 'record', 'get', wid_of('Invoice Lines'), rowid, '-a', APP)['data']
    linked = relation(d.get('product_id'))
    return linked[0][1] if linked else None


def step_b_all():
    for name in ('contacts', 'products', 'categories', 'journals', 'lines', 'automation-b', 'visibility',
                 'references'):
        print(f'\n── {name} ' + '─' * 60)
        STEPS[name]()
    print('\n── check-b ' + '─' * 60)
    return step_b_check()


def show():
    C.show(ws())


STEPS = {
    'create': step_create,
    'fields': step_fields,
    'computed': step_computed,
    'layout': step_layout,
    'rules': step_rules,
    'automation': step_automation,
    'buttons': step_buttons,
    'views': step_views,
    'roles': step_roles,
    'seed': step_seed,
    'all': step_all,
    'check': step_check,
    'verify': step_verify,
    'runs': step_runs,
    'selfcheck': step_selfcheck,
    'order': step_order,
    'account': step_account,
    'untouched': step_untouched,
    'show': show,
    # part B
    'contacts': step_b_contacts,
    'products': step_b_products,
    'categories': step_b_categories,
    'journals': step_b_journals,
    'lines': step_b_lines,
    'automation-b': step_b_automation,
    'visibility': step_b_visibility,
    'references': step_b_references,
    'verify-b': verify_b_references,
    'selfcheck-b': step_b_selfcheck,
    'check-b': step_b_check,
    'runs-b': step_b_runs,
    'rerun-b': step_b_rerun,
    'records-b': step_b_records,
    'all-b': step_b_all,
}

if __name__ == '__main__':
    step = sys.argv[1] if len(sys.argv) > 1 else 'check'
    if step not in STEPS:
        raise SystemExit(f"Unknown step {step!r}; choose from {', '.join(STEPS)}")
    result = STEPS[step](*sys.argv[2:])
    if step in ('verify', 'check', 'all', 'selfcheck', 'roles', 'seed', 'runs', 'visibility', 'references',
                'verify-b', 'selfcheck-b', 'check-b', 'rerun-b', 'records-b', 'all-b') and result:
        sys.exit(1)
