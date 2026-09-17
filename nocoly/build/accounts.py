#!/usr/bin/env python3
"""Build the Chart of Accounts worksheet (Odoo account.account, as on casimir.odoo.com saas~19.4) in ERP Master.

Bundle 2 of the six that join Phase 1 — **part A, the worksheet itself**. Part B, the account fields this bundle
brings to Contacts, Products, Product Categories, Journals and Invoice Lines (and their per-field hiding in the
roles), is a separate build: nothing here writes to any other worksheet. Requirements:
nocoly/worksheets/09-chart-of-accounts.md §1. Generic helpers: common.py. Run from the repo root with the CLI's
interpreter:

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

Every step reads the live state first and is safe to re-run; a second run writes nothing to HAP. Every write step
stops unless the profile reaches ERP Master › Invoicing › Chart of Accounts and the worksheet holds only this
script's own work, and compares the other eight worksheets' controls id by id before and after.

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
}

if __name__ == '__main__':
    step = sys.argv[1] if len(sys.argv) > 1 else 'check'
    if step not in STEPS:
        raise SystemExit(f"Unknown step {step!r}; choose from {', '.join(STEPS)}")
    result = STEPS[step](*sys.argv[2:])
    if step in ('verify', 'check', 'all', 'selfcheck', 'roles', 'seed', 'runs') and result:
        sys.exit(1)
