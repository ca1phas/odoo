#!/usr/bin/env python3
"""Build the Taxes worksheet (Odoo account.tax, as on casimir.odoo.com saas~19.4) in ERP Master.

Bundle 6 of six, and the last of Phase 1. It adds the worksheet to the **Invoicing** menu group after Chart of
Accounts, seeds all 35 taxes, and then goes back to the four worksheets that left a hole for it: **Products**
gains Sales Taxes and Purchase Taxes, **Chart of Accounts** gains Default Taxes, **Invoice Lines** gains Taxes,
the hidden Tax rate roll-up and Total, and **Invoices' Tax stops being a seeded figure** — 07's two roll-up
workflows gain two steps each and start writing it.

Requirements: nocoly/worksheets/13-taxes.md. Generic helpers: common.py. Run from the repo root with the CLI's
interpreter:

    ~/.hap-venv/bin/python nocoly/build/taxes.py create      # 0. the worksheet in menu group Invoicing, right
                                                             #    after Chart of Accounts
    ~/.hap-venv/bin/python nocoly/build/taxes.py fields      # 1. the sixteen controls, the divider and the two
                                                             #    duplicate-check helpers, then one placing save
    ~/.hap-venv/bin/python nocoly/build/taxes.py rules       # 2. Odoo's own visibility, six interaction rules
    ~/.hap-venv/bin/python nocoly/build/taxes.py views       # 3. Taxes (opens first) and Archived
    ~/.hap-venv/bin/python nocoly/build/taxes.py dupview     # 3b. Duplicate names — the taxes G marked
    ~/.hap-venv/bin/python nocoly/build/taxes.py buttons     # 4. Archive / Unarchive, the house pair
    ~/.hap-venv/bin/python nocoly/build/taxes.py automations # 5. workflow G: the key and the duplicate check
    ~/.hap-venv/bin/python nocoly/build/taxes.py roles       # 6. roles.py's create step, which now carries this
                                                             #    worksheet into the four business roles
    ~/.hap-venv/bin/python nocoly/build/taxes.py seed        # 7. the 35 taxes, every one read back
    ~/.hap-venv/bin/python nocoly/build/taxes.py products    # 8. Sales Taxes and Purchase Taxes on Products,
                                                             #    and the 14 products' values
    ~/.hap-venv/bin/python nocoly/build/taxes.py accounts    # 9. Default Taxes on Chart of Accounts, empty
    ~/.hap-venv/bin/python nocoly/build/taxes.py lines       # 10. Taxes, Tax rate (汇总) and Total on Invoice
                                                             #     Lines, the Total column, the 8 lines' taxes
    ~/.hap-venv/bin/python nocoly/build/taxes.py rollup      # 11. 07's two roll-ups gain 2b and 3b and write
                                                             #     Tax; automation B fills the line's Taxes
    ~/.hap-venv/bin/python nocoly/build/taxes.py amounts     # 12. drive the roll-up over every invoice with
                                                             #     lines, so the three documents land on the
                                                             #     tenant's own figures
    ~/.hap-venv/bin/python nocoly/build/taxes.py all         # every step above, then check

    ~/.hap-venv/bin/python nocoly/build/taxes.py verify      # the 35 live taxes against the extract, with §1's
                                                             #    digests
    ~/.hap-venv/bin/python nocoly/build/taxes.py check       # controls, rules, views, buttons, roles, workflow
                                                             #    G, and everything on the four other worksheets
    ~/.hap-venv/bin/python nocoly/build/taxes.py selfcheck   # the duplicate check and the roll-up driven
                                                             #    through the CLI on TEST records
    ~/.hap-venv/bin/python nocoly/build/taxes.py measure     # §1's open questions 1 and 2, measured
    ~/.hap-venv/bin/python nocoly/build/taxes.py keys        # every Tax key read back, and what carries
                                                             #    Duplicate name
    ~/.hap-venv/bin/python nocoly/build/taxes.py order       # each view's records in the view's own order
    ~/.hap-venv/bin/python nocoly/build/taxes.py untouched   # every other worksheet's control count and digest
    ~/.hap-venv/bin/python nocoly/build/taxes.py show        # the live control list

Every step reads the live state first and is safe to re-run; a second run writes nothing. **Nothing is ever
deleted** — no control, view, rule, workflow, button or record — and the Sales app is never opened.

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
ORG = hap.ids()['org']
SALES_APP = '3e596740-d096-42cd-b948-0b62a0220927'   # the Nocoly Sales app: never written to
SECTION = 'Invoicing'
SECTION_ID = '6aa8f3ecbf00c316381dbbe8'
WORKSHEET = 'Taxes'
KEY = WORKSHEET + ': '                              # ids.json key prefix for everything this worksheet owns
ALIAS = 'account_tax'
HERE = Path(__file__).resolve().parent
DATA = HERE.parent / 'data' / 'casimir-taxes.json'

COUNTRIES = 'Countries'
PRODUCTS = 'Products'
ACCOUNTS = 'Chart of Accounts'
LINES = 'Invoice Lines'
INVOICES = 'Invoices'
# every worksheet of the app but this one — `untouched` and the before/after comparisons walk them
OTHERS = ('Contacts', 'Countries', 'States', 'Units & Packagings', 'Products', 'Product Variants',
          'Product Categories', 'Chart of Accounts', 'Journals', 'Payment Terms', 'Payment Term Lines',
          'Invoices', 'Invoice Lines')
TEXT, NUMBER, DROPDOWN, RELATION, FORMULA_NUMBER, SWITCH, ROLLUP = 2, 6, 11, 29, 31, 36, 37
RICH_TEXT, DIVIDER = 41, 22


def ws():
    return hap.ids()['worksheets'][WORKSHEET]


def wid(name):
    return hap.ids()['worksheets'][name]


def refuse_sales():
    if APP == SALES_APP:
        sys.exit('ids.json points at the Sales app — refusing to write')


def session():
    from hap_cli.core.session import Session
    return Session.load(None)


def data():
    return json.loads(DATA.read_text(encoding='utf-8'))


def taxes_data():
    """The 35 taxes of the 19.4 extract, by Odoo's own five-way key minus the company: `<country code>|<type>|
    `<scope>|<name>` — the pair §1's Tax key is built on."""
    out = {}
    for t in data()['taxes']:
        out[natural_key(t)] = t
    return out


def natural_key(t):
    scope = {'consu': 'consu', 'service': 'service'}.get(t['tax_scope'] or '', '')
    return f"MY|{t['type_tax_use']}|{scope}|{t['name']}"


# ── options ─────────────────────────────────────────────────────────────────
#
# Minted once, here, and never re-minted: records point at the keys.

def option(key, value, index, color):
    return {'key': key, 'value': value, 'isDeleted': False, 'index': index, 'checked': False, 'color': color}


TYPE_TAX_USE = [('sale', 'Sales', 'd4ecbc5c-c6d5-47a6-90ce-f0871737b853', '#C9E6FC'),
                ('purchase', 'Purchases', '18ccb45e-0e63-4735-9d37-83acb4a6c1e7', '#FFE7B1'),
                ('none', 'None', '180a7285-6d75-4de9-8c50-f137c3655e01', '#D2D2D2')]
TAX_SCOPE = [('consu', 'Goods', '82616339-a98c-42b8-bda3-78f93d0776eb', '#C9E6FC'),
             ('service', 'Services', '3f2107ce-a79c-48ad-90b7-4c46bc7db491', '#C2F1D2')]
AMOUNT_TYPE = [('group', 'Group of Taxes', '4bd0212d-22b1-47f4-b86c-cc0171176f92', '#D2D2D2'),
               ('fixed', 'Fixed', 'bf446977-718c-45bc-a317-78d2ed2ebd73', '#FFE7B1'),
               ('percent', 'Percentage', 'a7101f45-bf00-4b19-98bd-08c62094258a', '#C2F1D2'),
               ('division', 'Percentage Tax Included', '0c31954a-83c5-4c34-abe5-cfc17b40abd8', '#C3F2F2'),
               ('code', 'Custom Formula', '3f62c3a4-f800-4187-88ea-3aade6f78f3a', '#E6D7FA')]
# the tenant's ten account.tax.group records, in their own id order (reference › Tax groups)
TAX_GROUP = [('SST 5%', 'SST 5%', 'c2eaed68-dd87-4897-9a98-e38603957303', '#C9E6FC'),
             ('SST 6%', 'SST 6%', 'd2888283-403f-4ab2-92e9-228f8bed5897', '#C9E6FC'),
             ('SST 8%', 'SST 8%', '2edc86d9-0c4b-4c8e-8ad8-29a2460243e5', '#C9E6FC'),
             ('SST 10%', 'SST 10%', '4f165e84-8f38-4054-8064-16f95ef5f5e5', '#C9E6FC'),
             ('SST 25 Per Card', 'SST 25 Per Card', '4ed21435-e287-4357-ab8e-276b8aa93203', '#FFE7B1'),
             ('SST X Per Litre', 'SST X Per Litre', '52bebae1-cef2-4713-acd1-3ffd7b761e7a', '#FFE7B1'),
             ('SST X Per Kilogram', 'SST X Per Kilogram', '0ad8d0ee-c184-487e-a0da-4089b6248288', '#FFE7B1'),
             ('SST X %', 'SST X %', '8ee03859-1bd9-45d4-af29-99aa2151e7fd', '#FFE7B1'),
             ('Not Applicable', 'Not Applicable', 'b4086fbf-d994-4dfe-a756-61f78edace8b', '#D2D2D2'),
             ('Exempt', 'Exempt', 'd770f6b8-0c01-4e8b-84c3-9d6ff625fbc9', '#C2F1D2')]
PRICE_INCLUDE = [('tax_included', 'Tax Included', 'f08a0df2-5a27-4a5d-a05d-3cdf35cf1553', '#C2F1D2'),
                 ('tax_excluded', 'Tax Excluded', '8f12b1fe-fa67-49e1-a7b0-ee2068393fb3', '#FBD2BF')]

NAME, TYPE, SCOPE, COMPUTATION, AMOUNT = 'Tax Name', 'Tax Type', 'Tax Scope', 'Tax Computation', 'Amount'
FORMULA, DESCRIPTION, LABEL = 'Formula', 'Description', 'Label on Invoices'
GROUP, COUNTRY, PRICE_INC = 'Tax Group', 'Country', 'Included in Price'
AFFECT, AFFECTED, ACTIVE, SEQUENCE, NOTES = ('Affect Base of Subsequent Taxes', 'Base Affected by Previous Taxes',
                                             'Active', 'Sequence', 'Legal Notes')
ADVANCED_DIVIDER = 'Advanced Options'
DUPLICATE = 'Duplicate name'                        # §1's checkbox — workflow G ticks it
TAX_KEY = 'Tax key'                                 # §1's hidden Text key carrying No duplicates

OPTIONS = {TYPE: TYPE_TAX_USE, SCOPE: TAX_SCOPE, COMPUTATION: AMOUNT_TYPE, GROUP: TAX_GROUP,
           PRICE_INC: PRICE_INCLUDE}
OPTION_LIST = {name: [option(key, label, i + 1, color) for i, (_, label, key, color) in enumerate(rows)]
               for name, rows in OPTIONS.items()}
KEY_OF = {name: {label: key for _, label, key, _ in rows} for name, rows in OPTIONS.items()}
LABEL_OF_KEY = {name: {key: label for _, label, key, _ in rows} for name, rows in OPTIONS.items()}
LABEL_OF_ODOO = {name: {odoo: label for odoo, label, _, _ in rows} for name, rows in OPTIONS.items()}

PERCENT = KEY_OF[COMPUTATION]['Percentage']
GROUP_OF_TAXES = 'Group of Taxes'
CUSTOM_FORMULA = 'Custom Formula'
NOT_A_GROUP = ['Fixed', 'Percentage', 'Percentage Tax Included', 'Custom Formula']


# ── the form ────────────────────────────────────────────────────────────────
#
# §1's layout, on HAP's 12-column grid. One divider, no tab: Odoo's *Definition* page holds only the
# distribution lists, none of which is built, so it would be empty and a single tab is worse than none.

PLACE = {
    NAME: (0, 0, 6), TYPE: (0, 1, 6),
    COMPUTATION: (1, 0, 6), AMOUNT: (1, 1, 6),
    FORMULA: (2, 0, 6), SEQUENCE: (2, 1, 6),
    DESCRIPTION: (3, 0, 6), LABEL: (3, 1, 6),
    ADVANCED_DIVIDER: (4, 0, 12),
    SCOPE: (5, 0, 6), GROUP: (5, 1, 6),
    COUNTRY: (6, 0, 6), PRICE_INC: (6, 1, 6),
    AFFECT: (7, 0, 6), AFFECTED: (7, 1, 6),
    ACTIVE: (8, 0, 6), DUPLICATE: (8, 1, 6),
    NOTES: (9, 0, 12),
    TAX_KEY: (10, 0, 6),                            # hidden and read-only — off the grid as far as a person sees
}
TITLE = NAME
ALIASES = {NAME: 'name', TYPE: 'type_tax_use', SCOPE: 'tax_scope', COMPUTATION: 'amount_type', AMOUNT: 'amount',
           FORMULA: 'formula', DESCRIPTION: 'description', LABEL: 'invoice_label', GROUP: 'tax_group_id',
           COUNTRY: 'country_id', PRICE_INC: 'price_include_override', AFFECT: 'include_base_amount',
           AFFECTED: 'is_base_affected', ACTIVE: 'active', SEQUENCE: 'sequence', NOTES: 'invoice_legal_notes',
           ADVANCED_DIVIDER: '',
           DUPLICATE: 'duplicate_name',             # not an Odoo field
           TAX_KEY: 'tax_key'}                      # nor is this
HINTS = {PRICE_INC: 'Default'}                      # Odoo's placeholder on price_include_override; no other has one
DESC = {  # Odoo's help where it reads well for a user, else plain words — only what the field does
    # (owner's rule, 22 Sep 2026). Build notes and Odoo references: worksheets/13-taxes.md, foot.
    TYPE: "Determines where the tax is selectable. Note: 'None' means a tax can't be used by itself, however it "
          'can still be used in a group.',
    COMPUTATION: '- Group of Taxes: The tax is a set of sub taxes.\n'
                 '- Fixed: The tax amount stays the same whatever the price.\n'
                 '- Percentage: The tax amount is a % of the price.\n'
                 '- Percentage Tax Included: The tax amount is a division of the price.\n'
                 '- Custom Formula: the Formula below computes the amount.',
    FORMULA: 'The formula that computes the tax amount when Tax Computation is Custom Formula.',
    DESCRIPTION: 'A short line shown beside the tax name, e.g. SST 10%.',
    LABEL: 'The name of the tax as printed on invoices.',
    GROUP: 'The group this tax is reported under.',
    COUNTRY: 'The country for which this tax is applicable.',
    PRICE_INC: "Overrides the Company's default on whether the price you use on the product and invoices "
               'includes this tax.',
    AFFECT: 'If set, taxes with a higher sequence than this one will be affected by it, provided they accept it.',
    AFFECTED: 'If set, taxes with a lower sequence might affect this one, provided they try to do it.',
    ACTIVE: 'Untick to hide the tax without deleting it.',
    SEQUENCE: 'The sequence field is used to define order in which the tax lines are applied.',
    DUPLICATE: 'Ticked when another tax of the same country, type and scope already has this Tax Name.',
    TAX_KEY: '',
}
REQUIRED = {NAME, TYPE, COMPUTATION, AMOUNT, COUNTRY, SEQUENCE}   # **not** Tax Group: a rule hides it (BUILDING.md)
UNIQUE = {TAX_KEY}                                  # §1 › Rules; and *not* Tax Name
# "100" = read-only and hidden on create · "011" = hidden · "001" = hidden and read-only
PERMISSION = {DUPLICATE: '100', TAX_KEY: '001'}
DOT = {AMOUNT: 4, SEQUENCE: 0}                      # Odoo float(16, 4) and an integer
KIND = {NAME: 'TEXT', TYPE: 'DROP_DOWN', SCOPE: 'DROP_DOWN', COMPUTATION: 'DROP_DOWN', AMOUNT: 'NUMBER',
        FORMULA: 'TEXT', DESCRIPTION: 'TEXT', LABEL: 'TEXT', GROUP: 'DROP_DOWN', COUNTRY: 'RELATE_SHEET',
        PRICE_INC: 'DROP_DOWN', AFFECT: 'SWITCH', AFFECTED: 'SWITCH', ACTIVE: 'SWITCH', SEQUENCE: 'NUMBER',
        NOTES: 'RICH_TEXT', ADVANCED_DIVIDER: 'SPLIT_LINE', DUPLICATE: 'SWITCH', TAX_KEY: 'TEXT'}
FORMULA_DEFAULT = 'price_unit * 0.10'


def advanced(name):
    """The advancedSetting keys this script owns on control `name`. Country's static default is added by
    `country_default()` once Malaysia is seeded."""
    out = {}
    if name in OPTIONS:
        out['showtype'] = '0'                       # a dropdown list. **Not '2'** — on a type 11 that is the
                                                    # progress-bar style, which drew Tax Type and Tax Scope as
                                                    # sliders in the table (UI test, 18 Sep). Every other
                                                    # Dropdown in the app carries '0'; all thirteen were checked
    if name in (AFFECT, AFFECTED, ACTIVE, DUPLICATE):
        out['showtype'] = '0'                       # a checkbox
    defaults = {TYPE: KEY_OF[TYPE]['Sales'], COMPUTATION: PERCENT, AMOUNT: 0, SEQUENCE: 1,
                FORMULA: FORMULA_DEFAULT, AFFECT: 0, AFFECTED: 1, ACTIVE: 1}
    if name in defaults:
        out['defsource'] = C.static_default(defaults[name])
    if name == COUNTRY:
        out['showtype'] = '3'                       # 3 = a dropdown, as States' Country is
        out['bidirectional'] = '0'                  # one-way: Odoo's tax form lists neither the products nor
        default = country_default()                 # the lines that use it (§1 › Fields)
        if default:
            out['defsource'] = default
    return out


def country_default():
    """A static Relation default pointing at Malaysia, as products.py writes Unit's. Empty until Countries holds
    it, so `fields` can run before anything is seeded."""
    rowid = hap.ids().get('records', {}).get('Countries: MY')
    if not rowid:
        rowid = next((r['rowid'] for r in C.records(wid(COUNTRIES), APP)
                      if r.get(hap.by_name(hap.controls(wid(COUNTRIES)))['Country Name']['controlId']) == 'Malaysia'),
                     None)
    return json.dumps([{'cid': '', 'rcid': '', 'staticValue': json.dumps([rowid])}]) if rowid else None


JSON_KEYS = ('filters', 'filterregex', 'controlssorts', 'customShowControls')


def setting_state(key, value):
    import accounts
    if key == 'defsource':
        return accounts.defsource_state(value)
    if key in JSON_KEYS and isinstance(value, str) and value:
        try:
            return json.loads(value)
        except ValueError:
            return value
    return value


def option_state(options):
    return [(o.get('key'), o.get('value'), o.get('index')) for o in options or [] if not o.get('isDeleted')]


def desired(c):
    """The attributes the placing save owns on control c, as they should read back."""
    name = c['controlName']
    row, col, size = PLACE[name]
    want = {'row': row, 'col': col, 'size': size, 'sectionId': '', 'alias': ALIASES[name],
            'hint': HINTS.get(name, ''), 'desc': DESC.get(name, ''), 'required': name in REQUIRED,
            'unique': name in UNIQUE, 'fieldPermission': PERMISSION.get(name, '111'),
            'attribute': 1 if name == TITLE else 0}
    if name in DOT:
        want['dot'] = DOT[name]
    return want


def layout_differences(ctrls):
    out = {}
    for c in ctrls:
        name = c['controlName']
        if name not in PLACE:
            continue
        diff = {k: (c.get(k), v) for k, v in desired(c).items()
                if (c.get(k) or (0 if k in ('attribute', 'dot') else '' if isinstance(v, str) else False)) != v}
        settings = c.get('advancedSetting') or {}
        diff.update({f'advancedSetting.{k}': (settings.get(k), v) for k, v in advanced(name).items()
                     if setting_state(k, settings.get(k)) != setting_state(k, v)})
        if name in OPTIONS and option_state(c.get('options')) != option_state(OPTION_LIST[name]):
            diff['options'] = (option_state(c.get('options')), option_state(OPTION_LIST[name]))
        if diff:
            out[name] = diff
    return out


def new_control(name):
    return C.control(KIND[name], name, PLACE[name], alias=ALIASES[name], hint=HINTS.get(name, ''),
                     desc=DESC.get(name, ''), required=name in REQUIRED, unique=name in UNIQUE,
                     options=[dict(o) for o in OPTION_LIST[name]] if name in OPTIONS else None,
                     data_source=wid(COUNTRIES) if name == COUNTRY else None,
                     multi=False if name == COUNTRY else None,
                     advanced_setting=advanced(name) or None,
                     extra={'dot': DOT[name]} if name in DOT else None)


# ── the other worksheets, compared control by control ───────────────────────

SIGNATURE = ('controlName', 'type', 'alias', 'row', 'col', 'size', 'sectionId', 'required', 'attribute', 'unique',
             'fieldPermission', 'dataSource', 'sourceControlId', 'showControls', 'advancedSetting', 'desc', 'hint')


def control_state(c):
    import accounts
    return accounts.control_state(c)


def snap(names=OTHERS):
    return {name: {c['controlId']: control_state(c) for c in hap.controls(wid(name))} for name in names}


def expect(before, label, changed=None, new=None, gone=None):
    import countries
    return countries.expect(before, label, changed=changed, new=new, gone=gone)


def signature(worksheet_id):
    return sorted(json.dumps([c['controlId']] + [c.get(k) for k in SIGNATURE], sort_keys=True, ensure_ascii=False)
                  for c in hap.controls(worksheet_id))


def step_untouched():
    """Control count and digest of every other worksheet — run before and after a build."""
    for name in OTHERS:
        sig = signature(wid(name))
        print(f'  {name:<20} {len(sig):>2} controls  sha256:'
              f'{hashlib.sha256("".join(sig).encode()).hexdigest()[:16]}')


# ── guard ───────────────────────────────────────────────────────────────────

VIEW, ARCHIVED, DUP_VIEW = 'Taxes', 'Archived', 'Duplicate names'
BUTTONS = ('Archive', 'Unarchive')
STOCK = {'Name', 'Description', 'Attachment', '名称', '描述', '附件'}


def guard(fresh=False):
    """Stop unless the profile reaches ERP Master › Invoicing › Taxes and the worksheet holds only this script's
    work. `fresh` allows the three stock controls of a brand-new worksheet."""
    refuse_sales()
    who = hap.run('auth', 'whoami')
    app = hap.run('app', 'info', '-a', APP).get('data', {})
    worksheet = hap.ids().get('worksheets', {}).get(WORKSHEET)
    section = next((s for s in app.get('sections', []) if any(i['id'] == worksheet for i in s['items'])), None)
    if app.get('name') != 'ERP Master' or not section or section['id'] != SECTION_ID:
        sys.exit(f"profile {who.get('profile')!r} does not reach ERP Master › {SECTION} › {WORKSHEET}")
    problems, ctrls = [], hap.controls(worksheet)
    known = set(PLACE) | (STOCK if fresh else set())
    problems += [f"unknown control {c['controlName']!r} ({c['controlId']})" for c in ctrls
                 if c['controlName'] not in known]
    if len(hap.by_name(ctrls)) != len(ctrls):
        problems.append(f'two controls share a name: {sorted(c["controlName"] for c in ctrls)}')
    views = {v['name'] for v in hap.listing('worksheet', 'view', 'list', worksheet, '-a', APP)}
    problems += [f'unknown view {n!r}' for n in views - {VIEW, ARCHIVED, DUP_VIEW, 'All', '全部'}]
    buttons = {b['name'] for b in hap.listing('worksheet', 'custom-actions', worksheet)}
    problems += [f'unknown button {n!r}' for n in buttons - set(BUTTONS)]
    rules = {r['name'] for r in hap.listing('worksheet', 'rules', worksheet)}
    problems += [f'unknown rule {n!r}' for n in rules - set(RULES)]
    if problems:
        sys.exit(f"{WORKSHEET} differs from this script's work — stopping:\n  " + '\n  '.join(problems))
    print(f"  guard: profile {os.environ.get('HAP_PROFILE') or who.get('profile')!r}, ERP Master › {SECTION} › "
          f"{WORKSHEET}, {len(ctrls)} controls, {len(rules)} rules, {len(buttons)} buttons, views {sorted(views)}")
    return ctrls


# ── 0 · the worksheet ───────────────────────────────────────────────────────

REMARK = ('Odoo account.tax: the taxes a line carries — 35 of them, ten active, every one a Malaysian SST '
          'percentage. What turns a subtotal into a total')
ICON = 'sys_percentage_finance'                     # `hap icon search percent`; every active tax is a percentage


def step_create():
    """The worksheet in the existing Invoicing menu group, then moved in front of Journals — Odoo's Accounting
    configuration lists Chart of Accounts, then Taxes, then Journals.

    The menu group is looked up by its **id** and `common.ensure_section` is never called: that helper re-sorts
    the app's top-level groups, and ERP Master carries a CRM group another administrator is building in
    (`countries.step_create`, 18 Sep). `app sort-worksheets` reorders one group only, and this group is
    entirely this build's."""
    refuse_sales()
    sections = C.app_info(APP)['sections']
    section = next((s for s in sections if s['id'] == SECTION_ID), None)
    if not section or section['name'] != SECTION:
        sys.exit(f'menu group {SECTION_ID} is {section and section["name"]!r}, not {SECTION!r}')
    C.remember('sections', SECTION, SECTION_ID)
    worksheet = C.ensure_worksheet(APP, SECTION_ID, WORKSHEET, alias=ALIAS, icon=ICON, remark=REMARK)
    C.remember('worksheets', WORKSHEET, worksheet)
    items = next(s for s in C.app_info(APP)['sections'] if s['id'] == SECTION_ID)['items']
    ids = [i['id'] for i in items]
    coa = wid(ACCOUNTS)
    order = [i for i in ids if i != worksheet]
    order.insert(order.index(coa) + 1, worksheet)
    if order != ids:
        hap.run('app', 'sort-worksheets', APP, SECTION_ID, *order)
    for s in C.app_info(APP)['sections']:
        print(f"  {s['name']:<10} {[(i['name'], i['id']) for i in s['items']]}")


# ── 1 · the controls ────────────────────────────────────────────────────────

def fields_of(worksheet_id):
    return hap.by_name(c for c in hap.controls(worksheet_id) if c['type'] != C.TAB)


def step_fields():
    """Every control of §1's form, in two passes and one placing save.

    1. **One full save of the empty worksheet** carrying the sixteen Odoo fields, the *Advanced Options*
       divider and the two duplicate-check helpers — the stock title control's id is reused for Tax Name, so
       the save that leaves Description and Attachment out deletes nothing that was not meant to go.
    2. Anything missing afterwards (a re-run on a worksheet that already holds records) is appended with
       `add-fields`, which parks it at row 9999.

    Then one placing save for rows, sizes, aliases, descriptions, hints, permissions, decimals, the options,
    the defaults and the title field. Nothing here is a formula, so no id has to be re-minted between passes.
    """
    existing = guard(fresh=True)
    f = hap.by_name(existing)
    order = list(PLACE)
    if not any(n in f for n in PLACE if n not in STOCK) and len(existing) <= 3:
        hap.backup('taxes_controls_pre_fields', existing)
        controls = []
        title = next((c for c in existing if c.get('attribute') == 1), None)
        for name in order:
            c = new_control(name)
            if name == NAME and title:
                c['controlId'] = title['controlId']
                c['attribute'] = title.get('attribute', 0)
            controls.append(c)
        before = snap()
        C.save_controls(ws(), controls)
        expect(before, f'{WORKSHEET}: the first save (no other worksheet may change)')
        print(f'  first save: {len(controls)} controls (the stock title id '
              f'{title and title["controlId"]} reused for {NAME})')
    missing = [n for n in order if n not in fields_of(ws())]
    if missing:
        before = snap()
        C.append_controls(ws(), [new_control(n) for n in missing])
        expect(before, f'{WORKSHEET}: {missing} appended', new={WORKSHEET: set(missing)})
        print(f'  appended: {missing}')
    drop_stock()
    place_controls('the controls placed')


def drop_stock():
    """The stock controls a new worksheet comes with, once nothing of §1's form is on them.

    `worksheet create` ships **Name** (the title), **Description** and **Attachment**, and a first
    `update-fields` save that leaves one out deletes it (BUILDING.md) — which is how every worksheet here was
    built, Description's id reused for this form's own Description. On a first run the append above lands
    beside the stock Name and Attachment rather than replacing them, so they are dropped in a save of their
    own. Guarded three ways: the worksheet must hold **no records**, the control must be one of the three
    stock names, and it must not be one this form uses."""
    ctrls, version = C.controls_with_version(ws())
    stray = [c for c in ctrls if c['controlName'] in STOCK and c['controlName'] not in PLACE]
    if not stray:
        return False
    if C.records(ws(), APP):
        sys.exit(f'{WORKSHEET} holds records and still carries the stock controls '
                 f'{[c["controlName"] for c in stray]} — refusing to save them away')
    hap.backup('taxes_controls_pre_drop_stock', ctrls)
    before = snap()
    C.save_controls(ws(), [c for c in ctrls if c not in stray], version=version)
    expect(before, f'{WORKSHEET}: the stock controls dropped (no other worksheet may change)')
    print(f'  dropped the stock controls {[(c["controlName"], c["controlId"]) for c in stray]} — the worksheet '
          f'was created empty and holds no records')
    return True


def place_controls(label):
    """One full save bringing every control into PLACE's rows, aliases, descriptions, permissions, decimals,
    options and defaults, and the title onto Tax Name."""
    ctrls, version = C.controls_with_version(ws())
    changed = layout_differences(ctrls)
    if changed:
        for c in ctrls:
            name = c['controlName']
            if name in changed:
                c.update(desired(c))
                c['advancedSetting'] = {**(c.get('advancedSetting') or {}), **advanced(name)}
                if name in OPTIONS:
                    c['options'] = [dict(o) for o in OPTION_LIST[name]]
        for c in ctrls:                               # the title moves in one save: 1 on Tax Name, 0 on the rest
            c['attribute'] = 1 if c['controlName'] == TITLE else 0
        before = snap()
        C.save_controls(ws(), ctrls, version=version)
        expect(before, f'{WORKSHEET}: {label}')
        print('  updated:', json.dumps(changed, ensure_ascii=False)[:1200])
    left = layout_differences(hap.controls(ws()))
    if left:
        sys.exit(f'the controls read back with differences: {json.dumps(left, ensure_ascii=False)}')
    for c in hap.controls(ws()):
        C.remember('controls', KEY + c['controlName'], c['controlId'])
    C.show(ws())


# ── 2 · the rules ───────────────────────────────────────────────────────────
#
# §1's five rules, as six business rules: HAP needs a second rule to make a field a rule hides required, and
# §1's rule 5 (Duplicate name read-only and off the create form) is a **field permission** — "100" — exactly as
# States built the same control, not a rule at all.
#
# A rule applies its action while its condition holds and the opposite when it fails (BUILDING.md), so the form
# is chosen by what a **new** tax should show. Tax Computation is required and defaults to Percentage, so on a
# new record it is never empty: Amount and the three price/base fields are written as *hide · is any of*, which
# leaves them visible from the start, and Formula as *show · is Custom Formula*, which keeps it hidden.

RULE_AMOUNT = 'Amount is not offered for a group of taxes or a custom formula'
RULE_FORMULA_SHOWN = 'Formula is only for a custom formula'
RULE_FORMULA_REQUIRED = 'Formula is required for a custom formula'
RULE_GROUP_HIDDEN = 'Tax Group is not offered for a group of taxes'
RULE_GROUP_REQUIRED = 'Tax Group is required unless the computation is a group of taxes'
RULE_GROUP_SETTINGS = 'A group of taxes carries no price or base settings'

# name -> (the Tax Computation labels the condition holds for, [(item type, [controls])])
RULES = {
    # <field name="amount" invisible="amount_type not in ('fixed', 'percent', 'division')"/>
    RULE_AMOUNT: ([GROUP_OF_TAXES, CUSTOM_FORMULA], [(C.HIDE, [AMOUNT])]),
    # account_tax_python: invisible="amount_type != 'code'" required="amount_type == 'code'"
    RULE_FORMULA_SHOWN: ([CUSTOM_FORMULA], [(C.SHOW, [FORMULA])]),
    RULE_FORMULA_REQUIRED: ([CUSTOM_FORMULA], [(C.REQUIRE, [FORMULA])]),
    # <field name="tax_group_id" invisible="amount_type == 'group'" required="amount_type != 'group'"/>
    RULE_GROUP_HIDDEN: ([GROUP_OF_TAXES], [(C.HIDE, [GROUP])]),
    RULE_GROUP_REQUIRED: (NOT_A_GROUP, [(C.REQUIRE, [GROUP])]),
    # the three invisible="amount_type == 'group'" fields of Advanced Options
    RULE_GROUP_SETTINGS: ([GROUP_OF_TAXES], [(C.HIDE, [PRICE_INC, AFFECT, AFFECTED])]),
}


def rule_payload(f, name):
    labels, items = RULES[name]
    condition = {'controlId': f[COMPUTATION]['controlId'], 'dataType': DROPDOWN, 'spliceType': 1,
                 'filterType': C.EQ, 'value': '', 'values': [KEY_OF[COMPUTATION][l] for l in labels],
                 'dynamicSource': [], 'isGroup': False}
    return C.any_of([condition]), [C.item(kind, *[f[n] for n in targets]) for kind, targets in items]


def rule_state(r, names):
    groups = [sorted((names.get(c['controlId'], c['controlId']), c['filterType'],
                      tuple(sorted(LABEL_OF_KEY[COMPUTATION].get(v, v) for v in c.get('values') or [])))
                     for c in g.get('groupFilters') or []) for g in r.get('filters') or []]
    return dict(type=r['type'], disabled=r['disabled'], groups=groups,
                items=[(i['type'], sorted(names.get(x['controlId']) for x in i['controls']))
                       for i in r.get('ruleItems') or []])


def rule_want(name):
    labels, items = RULES[name]
    return dict(type=C.INTERACTION, disabled=False,
                groups=[[(COMPUTATION, C.EQ, tuple(sorted(labels)))]],
                items=[(kind, sorted(targets)) for kind, targets in items])


def rule_differences():
    names = {c['controlId']: c['controlName'] for c in hap.controls(ws())}
    live = {r['name']: r for r in hap.listing('worksheet', 'rules', ws())}
    return ({name: (rule_state(live[name], names) if name in live else None, rule_want(name))
             for name in RULES if name not in live or rule_state(live[name], names) != rule_want(name)}, live)


def step_rules():
    """Odoo's own visibility, read off the 19.4 arch (§1 › Rules)."""
    guard()
    f = fields_of(ws())
    todo, live = rule_differences()
    hap.backup('taxes_rules_pre_rules', list(live.values()))
    for name in todo:
        filters, items = rule_payload(f, name)
        args = ['worksheet', 'save-rule', ws(), '--name', name, '--type', str(C.INTERACTION),
                '--filters', json.dumps(filters, ensure_ascii=False),
                '--rule-items', json.dumps(items, ensure_ascii=False)]
        if name in live:
            args += ['--rule-id', live[name]['ruleId']]
        hap.run(*args)
        print(f"  {'updated' if name in live else 'created'}: {name}")
    left, live = rule_differences()
    if left:
        sys.exit(f'rules read back with differences: {json.dumps(left, ensure_ascii=False, default=str)}')
    if not todo:
        print('  rules already as specified; nothing saved')
    names = {c['controlId']: c['controlName'] for c in hap.controls(ws())}
    for name, r in live.items():
        C.remember('rules', KEY + name, r['ruleId'])
        print(f"  {r['ruleId']}  {name}: {json.dumps(rule_state(r, names), ensure_ascii=False)}")


# ── 3 · the views ───────────────────────────────────────────────────────────

COLUMNS = (NAME, DESCRIPTION, TYPE, SCOPE, LABEL, ACTIVE)   # account.view_tax_tree, its optional columns off
DUP_COLUMNS = (NAME, TYPE, SCOPE, COUNTRY, DUPLICATE)       # States' *Duplicate codes*, with this form's fields
CTIME = {'controlId': 'ctime', 'type': 16, 'controlName': 'Created'}    # the system field 创建时间


def view_sort(f):
    """Odoo `_order = 'sequence,id'`: Sequence ascending, then created — all 35 share sequence 1, so the list
    reads in creation order, which is Payment Terms' arrangement exactly (BUILDING.md: `ctime` works as a sort
    key in `moreSort`)."""
    return C.sort_spec([f[SEQUENCE], CTIME])


def view_specs(f):
    columns = [f[n]['controlId'] for n in COLUMNS]
    sort = view_sort(f)
    # Odoo's action opens the list with `active_test: False`, so it shows all 35 and draws the inactive ones
    # muted. There is therefore **no Active filter** on the main view — §1's own call.
    quick = [{'fieldId': f[TYPE]['controlId'], 'selectionType': 'multiple', 'displayType': 'dropdown'},
             {'fieldId': f[SCOPE]['controlId'], 'selectionType': 'multiple', 'displayType': 'dropdown'},
             {'fieldId': f[ACTIVE]['controlId']}]
    return {VIEW: (dict(viewType='table', tableFields=columns, quickFilters=quick), sort, columns),
            ARCHIVED: (dict(viewType='table', tableFields=columns,
                            filter=C.switch_filter(f[ACTIVE], 'ne')), sort, columns)}


def view_state(info, names):
    quick = []
    for q in info.get('fastFilters') or []:
        s = q.get('advancedSetting') or {}
        quick.append((names.get(q['controlId']), s.get('allowitem'), s.get('direction')))
    return dict(columns=[names.get(x, x) for x in info.get('showControls') or []],
                sort=[(names.get(s['controlId'], s['controlId']), s['isAsc']) for s in info.get('moreSort') or []],
                sortCid=names.get(info.get('sortCid'), info.get('sortCid')), sortType=info.get('sortType'),
                filters=[(names.get(x['controlId']), x['filterType'], tuple(x.get('values') or []))
                         for x in info.get('filters') or [] if x.get('controlId')],
                quick=quick)


def view_want(name):
    sort = [(SEQUENCE, True), ('Created', True)]
    if name == VIEW:
        return dict(columns=list(COLUMNS), sort=sort, sortCid=SEQUENCE, sortType=2, filters=[],
                    quick=[(TYPE, '2', '2'), (SCOPE, '2', '2'), (ACTIVE, None, None)])
    if name == ARCHIVED:
        return dict(columns=list(COLUMNS), sort=sort, sortCid=SEQUENCE, sortType=2,
                    filters=[(ACTIVE, C.NE, ('1',))], quick=[])
    return dict(columns=list(DUP_COLUMNS), sort=sort, sortCid=SEQUENCE, sortType=2,
                filters=[(DUPLICATE, C.EQ, ('1',))], quick=[])


def view_names():
    names = {c['controlId']: c['controlName'] for c in hap.controls(ws())}
    names['ctime'] = 'Created'
    return names


def view_differences(wanted):
    names = view_names()
    live = hap.listing('worksheet', 'view', 'list', ws(), '-a', APP)
    out = {}
    for name in wanted:
        v = next((x for x in live if x['name'] == name), None)
        got = view_state(C.view_info(ws(), APP, v['viewId']), names) if v else None
        if got != view_want(name):
            out[name] = (got, view_want(name))
    return out


def step_views():
    """**Taxes**, the view that opens first — Odoo's own six columns and **all 35 rows**, because the action
    turns `active_test` off — and **Archived**, the house's seventh, for the Unarchive button.

    The quick filters stand in for Odoo's search facets: Tax Type and Tax Scope as *is any of* dropdowns (the
    spec adapter's object form, which lowers to `allowitem` "2" / `direction` "2" and is written identically on
    every run) and Active as a plain checkbox filter, which takes no such settings.

    `dupview` owns §1's third view and this step never names it, so its columns and filter are left alone."""
    guard()
    f = fields_of(ws())
    views = view_specs(f)
    todo = view_differences(views)
    if todo:
        for name, vid in C.upsert_views(ws(), APP, views, 'taxes_views_pre_views', default_view=VIEW).items():
            C.remember('views', KEY + name, vid)
        print('  order:', C.sort_views(ws(), APP, list(views)))
    left = view_differences(views)
    if left:
        sys.exit(f'views read back with differences: {json.dumps(left, ensure_ascii=False, default=str)}')
    print('  updated:', ', '.join(todo) if todo else 'nothing (already as specified)')
    for v in hap.listing('worksheet', 'view', 'list', ws(), '-a', APP):
        C.remember('views', KEY + v['name'], v['viewId'])
    C.print_views(ws(), APP)


# ── 3b · the Duplicate names view ───────────────────────────────────────────

def step_dupview():
    """§1's third view: **Duplicate names** — the taxes *Duplicate name* is ticked on.

    Odoo has no such view because its database refuses the second tax outright; here the duplicate is created
    and then named by workflow **G**, and without this view the tick can only be read by opening a record.
    States' *Duplicate codes* verbatim, with this form's five columns.

    The two views `views` owns are not touched, and that is checked rather than assumed: this step sends only
    its own view to `upsert_views`, names the three to `sort_views` (which leaves every view it is not given
    where it is) and then compares the other two before and after."""
    guard()
    f = fields_of(ws())
    columns = [f[n]['controlId'] for n in DUP_COLUMNS]
    views = {DUP_VIEW: (dict(viewType='table', tableFields=columns,
                             filter=C.switch_filter(f[DUPLICATE], 'eq')), view_sort(f), columns)}
    before = {v['name']: C.view_info(ws(), APP, v['viewId'])
              for v in hap.listing('worksheet', 'view', 'list', ws(), '-a', APP)}
    if view_differences(views):
        for name, vid in C.upsert_views(ws(), APP, views, 'taxes_views_pre_dupview').items():
            C.remember('views', KEY + name, vid)
    print('  order:', C.sort_views(ws(), APP, [VIEW, ARCHIVED, DUP_VIEW]))
    after = {v['name']: C.view_info(ws(), APP, v['viewId'])
             for v in hap.listing('worksheet', 'view', 'list', ws(), '-a', APP)}
    keys = ('showControls', 'sortCid', 'sortType', 'moreSort', 'filters', 'fastFilters', 'advancedSetting')
    for name in (VIEW, ARCHIVED):
        moved = [k for k in keys if (before.get(name) or {}).get(k) != after[name].get(k)]
        if name in before and moved:
            sys.exit(f'the {name} view changed: {moved}')
    print(f'  {VIEW} and {ARCHIVED}: unchanged ({len(keys)} attributes compared)')
    left = view_differences(views)
    if left:
        sys.exit(f'views read back with differences: {json.dumps(left, ensure_ascii=False, default=str)}')
    C.print_views(ws(), APP)


# ── 4 · the buttons ─────────────────────────────────────────────────────────

MSG_ARCHIVE = 'Are you sure that you want to archive this record?'
BUTTON_STEP = {'Archive': ('Archive the tax', '0'), 'Unarchive': ('Unarchive the tax', '1')}


def step_buttons():
    """Odoo ⚙ Actions › Archive / Unarchive, the house pair — the seventh worksheet to carry them. `active` is
    a real Odoo field here and 25 of the 35 records use it."""
    guard()
    active = fields_of(ws())[ACTIVE]['controlId']
    when = lambda op: {'type': 'group', 'logic': 'AND', 'children': [
        {'type': 'condition', 'field': active, 'operator': op, 'value': ['1']}]}
    buttons = [
        ({'name': 'Archive', 'type': 'triggerWorkflow', 'enableWhen': when('eq'), 'isBatch': True,
          'confirm': True, 'confirmMsg': MSG_ARCHIVE, 'sureName': 'Archive', 'cancelName': 'Cancel'},
         [{'fieldId': active, 'value': '0'}], BUTTON_STEP['Archive'][0]),
        ({'name': 'Unarchive', 'type': 'triggerWorkflow', 'enableWhen': when('ne'), 'isBatch': True},
         [{'fieldId': active, 'value': '1'}], BUTTON_STEP['Unarchive'][0]),
    ]
    before = snap()
    C.upsert_buttons(ws(), APP, buttons, KEY, 'taxes_buttons_pre_buttons')
    expect(before, f'{WORKSHEET}: buttons (no other worksheet may change)')
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
        proc = hap.run('workflow', 'node', 'list', pid)
        byname = {n['name']: n for n in proc['flowNodeMap'].values()}
        step, value = BUTTON_STEP[name]
        start = proc['startEventId']
        node = byname.get(step)
        if not node or proc['flowNodeMap'][start].get('nextId') != node['id']:
            out.append(f'{name} workflow: the trigger does not run into {step!r}')
            continue
        s = step_state_of(pid, node['id'])
        if s['selectNodeId'] != start or s['fields'] != [(active, '', '', False, value)] or s['isException']:
            out.append(f'{name} workflow step: {s}')
        info = hap.run('workflow', 'get', pid)
        info = info.get('data', info)
        if not info.get('enabled') or info.get('publishStatus') != 2:
            out.append(f"{name} workflow enabled={info.get('enabled')} publishStatus={info.get('publishStatus')}")
    return out


def step_state_of(pid, node_id):
    import states as S
    return S.step_state_of(pid, node_id)


# ── 5 · workflow G: the key and the duplicate check ─────────────────────────
#
# §1's *Rules*, as the pair bundle 5 proved: a hidden **Text** Tax key carrying HAP's *No duplicates*, a
# read-only **Duplicate name** checkbox, and one quiet workflow that works the key out, looks for another tax
# already holding it, marks the duplicate and stops before writing.
#
# Two things differ from States' G, both because Odoo's constraint here is five-way rather than two:
#
#  * the key is `<country code>|<tax type>|<tax scope>|<tax name>`, and a workflow formula renders a **dropdown
#    as its label**, so Tax Type and Tax Scope are translated back to Odoo's own keys with IF (`Sales` →
#    `sale`, `Goods` → `consu`, an empty scope → the empty string);
#  * Odoo skips the constraint entirely when `type_tax_use = 'none'`, so the **trigger** carries the condition
#    *Tax Type is any of Sales, Purchases* — conditionId 1, the operator automation B uses on Display Type —
#    and a tax of type None never starts a run, gets no key and is never marked.

WF_G = 'Taxes: the key and the duplicate check'
G_TRIGGER = "When a tax's Name, Type, Scope or Country is written"
GET_COUNTRY = 'Get the country'
KEY_STEP = 'Work out the key'
FIND_STEP = 'Another tax with this key?'
DUP_GATEWAY = 'Is there one?'
PATH_DUP = 'Yes — another tax already holds this key'
PATH_FREE = 'No — this key is free'
TICK_STEP = f'Tick {DUPLICATE}'
UNTICK_STEP = f'Untick {DUPLICATE}'
CLEAR_STEP = f'Clear the {TAX_KEY}'
STOP_STEP = 'Stop — a duplicate gets no key'
WRITE_KEY_STEP = f'Write the {TAX_KEY}'
G_NODES = (GET_COUNTRY, KEY_STEP, FIND_STEP, DUP_GATEWAY, TICK_STEP, UNTICK_STEP, CLEAR_STEP, STOP_STEP,
           WRITE_KEY_STEP)
ABORT = 30                                          # flowNodeType 中止流程 — the only way to stop a run inside
STRING_FX = 'string_fx_id'                          # a function formula node's own text result
EQ_ID, NE_ID, NOT_EMPTY_ID, IS_ANY_OF = '9', '10', '7', '1'
NO_OTHER_WORKFLOWS = 2                              # 触发其他工作流: 0 允许 · 1 指定 · 2 不允许
G_DESC = ("Odoo's constraint unique(company, name, type_tax_use, tax_scope, country_id) on account.tax, as far "
          'as HAP can carry it: the key is worked out and written to the hidden Tax key, which carries No '
          'duplicates, and a tax whose key another tax already holds is marked with Duplicate name. A tax whose '
          'Tax Type is None is exempt, as it is in Odoo. HAP runs a workflow after the save, so the duplicate '
          'is created and then named — Odoo refuses it outright.')


def read(*args):
    out = hap.run(*args)
    return out.get('data', out) if isinstance(out, dict) else out


def node_get(pid, node_id):
    return read('workflow', 'node', 'get', pid, node_id)


def ensure_quiet(pid, label):
    """触发其他工作流 set to 不允许触发 (`triggerType` 2) — the standing rule for a workflow writing its own
    record. The whole config goes back as read, as the editor's Save sends it; publishing is the caller's."""
    cfg = read('workflow', 'config-get', pid)
    if (cfg.get('triggerType'), list(cfg.get('processIds') or [])) == (NO_OTHER_WORKFLOWS, []):
        return False
    print('  backup:', hap.backup('taxes_process_config_pre_quiet',
                                  {'processId': pid, 'label': label, 'config': cfg}))
    send = dict(cfg, triggerType=NO_OTHER_WORKFLOWS, processIds=[], value=(cfg.get('value') or '').strip(),
                revokeNodeIds=(cfg.get('revokeNodeIds') or []) if cfg.get('allowRevoke') else [])
    hap.run('workflow', 'config-set', pid, '-c', json.dumps(send, ensure_ascii=False))
    got = read('workflow', 'config-get', pid)
    moved = sorted(k for k in set(cfg) | set(got)
                   if k not in ('triggerType', 'processIds') and got.get(k) != cfg.get(k))
    if (got.get('triggerType'), list(got.get('processIds') or [])) != (NO_OTHER_WORKFLOWS, []) or moved:
        sys.exit(f"{label}: process config read back triggerType {got.get('triggerType')} processIds "
                 f"{got.get('processIds')}; other keys changed {moved}")
    print(f"  {label}: 触发其他工作流 set to 不允许触发 (triggerType {cfg.get('triggerType')} → {NO_OTHER_WORKFLOWS})")
    return True


def key_expression(f, cty_f):
    """`<country code>|<tax type>|<tax scope>|<tax name>` — Odoo's five-way key without the company, which one
    app copy is.

    The country's code is read from the **country record** the first step fetched, not from a lookup on the
    tax: a lookup is a value HAP recomputes on save and the run would be reading it while it is being written.
    Inside a workflow formula a dropdown renders its **label**, so the two selections are translated back to
    Odoo's own keys; a workflow formula compares with `==`, never `=` (BUILDING.md), and CONCAT is the only
    way to join text — `+` would be read as an octal literal."""
    code = f"$country-{cty_f['Country Code']['controlId']}$"
    use = f"$trigger-{f[TYPE]['controlId']}$"
    scope = f"$trigger-{f[SCOPE]['controlId']}$"
    name = f"$trigger-{f[NAME]['controlId']}$"
    use_key = f'IF({use}=="Sales","sale",IF({use}=="Purchases","purchase","none"))'
    scope_key = f'IF({scope}=="Goods","consu",IF({scope}=="Services","service",""))'
    return f'CONCAT({code},"|",{use_key},"|",{scope_key},"|",{name})'


def g_nodes(f):
    """The chain `batch-add` makes. The search filter and the branch-path conditions are written again
    afterwards — batch-add sends `operateCondition`, which the UI never reads.

    **The tick comes before the key write, and they are two steps**, so that whatever happens to the key write
    the mark stands; and **the duplicate path ends in an abort** (中止流程, node type 30), because a workflow's
    own update step is not subject to *No duplicates* (measured on States, 18 Sep) — nothing but this
    workflow's shape keeps the key unique. A branch converges, so an empty path is not a stop."""
    tick = lambda alias, name, value: {
        'nodeAlias': alias, 'nodeType': 'update_record', 'name': name,
        'config': {'target': {'node': {'nodeAlias': 'trigger'}}, 'worksheet': ws(),
                   'fields': [{'fieldId': f[DUPLICATE]['controlId'], 'type': SWITCH, 'value': value}]}}
    clear = {'nodeAlias': 'clear', 'nodeType': 'update_record', 'name': CLEAR_STEP,
             'config': {'target': {'node': {'nodeAlias': 'trigger'}}, 'worksheet': ws(), 'fields': []}}
    return [
        {'nodeAlias': 'country', 'nodeType': 'get_relation', 'name': GET_COUNTRY,
         'config': {'target': {'node': {'nodeAlias': 'trigger'}},
                    'fields': [{'fieldId': f[COUNTRY]['controlId']}], 'worksheet': wid(COUNTRIES)}},
        {'nodeAlias': 'key', 'nodeType': 'compute', 'name': KEY_STEP,
         'config': {'mode': 'function', 'output_type': 'text', 'formula': 'CONCAT("","")'}},
        {'nodeAlias': 'found', 'nodeType': 'get_single', 'name': FIND_STEP,
         'config': {'worksheet': ws(), 'execute_type': 2}},          # 2 = carry on when nothing is found
        {'nodeAlias': 'gate', 'nodeType': 'branch', 'name': DUP_GATEWAY, 'config': {'mode': 'exclusive',
         'paths': [{'alias': 'dup', 'name': PATH_DUP, 'nodes': [tick('tick', TICK_STEP, '1'), clear]},
                   {'alias': 'free', 'name': PATH_FREE, 'nodes': [tick('untick', UNTICK_STEP, '0')]}]}},
        {'nodeAlias': 'write', 'nodeType': 'update_record', 'name': WRITE_KEY_STEP,
         'config': {'target': {'node': {'nodeAlias': 'trigger'}}, 'worksheet': ws(), 'fields': []}},
    ]


def key_search_filter(node_id, key_field, key_node, trigger):
    """A tax whose **Tax key** is the key just worked out and which is **not** the record that started the run.

    The self-exclusion is what makes the check safe to re-run: a field-narrowed trigger fires whenever one of
    its fields is in the write, changed or not, so a save that re-sends an unchanged Tax Name would otherwise
    find the record's own key and call it a duplicate (BUILDING.md; States' G, 18 Sep)."""
    return [
        {'nodeId': node_id, 'nodeType': 7, 'actionId': '406', 'filedId': key_field['controlId'],
         'filedValue': TAX_KEY, 'filedTypeId': TEXT, 'enumDefault': 0, 'conditionId': EQ_ID, 'sourceType': 0,
         'conditionValues': [{'nodeId': key_node, 'controlId': STRING_FX, 'value': ''}]},
        {'nodeId': node_id, 'nodeType': 7, 'actionId': '406', 'filedId': 'rowid', 'filedValue': 'Record ID',
         'filedTypeId': TEXT, 'enumDefault': 0, 'conditionId': NE_ID, 'sourceType': 0,
         'conditionValues': [{'nodeId': trigger, 'controlId': 'rowid', 'value': '', 'sureNodeId': trigger}]},
    ]


def g_trigger_condition(f, start):
    """*Tax Type is any of Sales, Purchases* — Odoo skips `_constrains_name` when `type_tax_use = 'none'`."""
    return [[{'nodeId': start, 'filedId': f[TYPE]['controlId'], 'filedValue': TYPE, 'filedTypeId': DROPDOWN,
              'enumDefault': 0, 'conditionId': IS_ANY_OF, 'sourceType': 0,
              'conditionValues': [{'value': {'key': KEY_OF[TYPE][label], 'value': label, 'isDeleted': False}}
                                  for label in ('Sales', 'Purchases')]}]]


def g_trigger_shape(groups):
    return [[(c.get('filedId'), str(c.get('conditionId')),
              sorted(((v.get('value') or {}).get('key') if isinstance(v.get('value'), dict) else v.get('value'))
                     for v in c.get('conditionValues') or []))
             for c in group] for group in groups or []]


def g_trigger_state(pid, start):
    t = node_get(pid, start)
    return dict(name=t.get('name'), appId=t.get('appId'), fields=sorted(t.get('assignFieldIds') or []),
                condition=g_trigger_shape(t.get('operateCondition')))


def step_automations():
    """**G** — *Taxes: the key and the duplicate check*, §1's *Rules* as a workflow.

      1. **Get the country** — the trigger's Country, so the country's code is read from the country;
      2. **Work out the key** — a text function formula, `<country code>|<type>|<scope>|<name>`;
      3. **Another tax with this key?** — a search of Taxes, Tax key = that, Record ID ≠ the trigger, oldest
         first, carrying on when nothing is found;
      4. **Is there one?** — an exclusive gateway. The conditioned path is *yes* (the found tax's Tax key is
         not empty): tick Duplicate name, clear the key, **stop** (中止流程). The default path unticks it and
         runs on into
      5. **Write the Tax key**.

    G is **quiet** (`triggerType` 2): it writes Duplicate name and Tax key on its own worksheet, and a quiet
    workflow starts nothing anywhere."""
    guard()
    import states as S
    f = fields_of(ws())
    cty_f = hap.by_name(hap.controls(wid(COUNTRIES)))
    ids = hap.ids()
    pid = ids.setdefault('workflows', {}).get(WF_G)
    if not pid:
        live = {w.get('name'): (w.get('id') or w.get('processId')) for w in hap.listing('workflow', 'list', APP)}
        pid = live.get(WF_G)          # `workflow create` can time out having created it (BUILDING.md)
    if not pid:
        out = hap.run('workflow', 'create', '-c', ORG, '-n', WF_G, '-a', APP, '--type', 'worksheet', '-d', G_DESC)
        d = out.get('data', out) if isinstance(out, dict) else out
        pid = d if isinstance(d, str) else (d.get('id') or d.get('processId'))
        print(f'  G: workflow created {pid}')
    C.remember('workflows', WF_G, pid)
    proc = hap.run('workflow', 'node', 'list', pid)
    start = proc['startEventId']
    by_name = {n['name']: n for n in proc['flowNodeMap'].values()}
    changed = False
    if GET_COUNTRY not in by_name:
        hap.run('workflow', 'node', 'batch-add', pid, '--nodes', json.dumps(g_nodes(f), ensure_ascii=False),
                '--trigger-worksheet', ws(), '--trigger-event', 'create_or_update',
                '--trigger-fields', ','.join([f[NAME]['controlId'], f[TYPE]['controlId'],
                                              f[SCOPE]['controlId'], f[COUNTRY]['controlId']]),
                '--trigger-alias', 'trigger')
        print('  G: steps added')
        changed = True
        proc = hap.run('workflow', 'node', 'list', pid)
        by_name = {n['name']: n for n in proc['flowNodeMap'].values()}
    if STOP_STEP not in by_name and CLEAR_STEP in by_name:
        # 中止流程 has no builder in hap-cli's DSL: add it by hand, last in the duplicate path, so the run stops
        # before the key write a duplicate must never reach.
        hap.run('workflow', 'node', 'add', pid, '--type', str(ABORT), '-n', STOP_STEP,
                '--after', by_name[CLEAR_STEP]['id'])
        print(f'  G: {STOP_STEP!r} (中止流程) added after {CLEAR_STEP!r}')
        changed = True
        proc = hap.run('workflow', 'node', 'list', pid)
        by_name = {n['name']: n for n in proc['flowNodeMap'].values()}
    for name in G_NODES:
        if name not in by_name:
            sys.exit(f'G: the workflow has no node {name!r} — {sorted(by_name)}')
    # 1 · the trigger: Taxes, 新增或更新, narrowed to four fields, condition "Tax Type is any of Sales, Purchases"
    want_fields = sorted([f[NAME]['controlId'], f[TYPE]['controlId'], f[SCOPE]['controlId'],
                          f[COUNTRY]['controlId']])
    want_trigger = dict(name=G_TRIGGER, appId=ws(), fields=want_fields,
                        condition=g_trigger_shape(g_trigger_condition(f, start)))
    if g_trigger_state(pid, start) != want_trigger:
        trig = node_get(pid, start)
        hap.run('workflow', 'node', 'save', pid, start, '--type', '0', '-n', G_TRIGGER, '-c', json.dumps(
            {'appId': ws(), 'appType': 1, 'triggerId': trig.get('triggerId'), 'assignFieldIds': want_fields,
             'operateCondition': g_trigger_condition(f, start), 'returns': []}, ensure_ascii=False))
        if g_trigger_state(pid, start)['name'] != G_TRIGGER:
            hap.run('workflow', 'node', 'rename', pid, start, '-n', G_TRIGGER)
        got = g_trigger_state(pid, start)
        if got != want_trigger:
            sys.exit(f'G: trigger read back {got}, want {want_trigger}')
        print('  G: trigger rewritten')
        changed = True
    # 2 · the key formula, over the country step and the trigger record
    node_ids = {'trigger': start, 'country': by_name[GET_COUNTRY]['id'], 'key': by_name[KEY_STEP]['id']}
    expression = (key_expression(f, cty_f).replace('$trigger-', f"${node_ids['trigger']}-")
                                          .replace('$country-', f"${node_ids['country']}-"))
    changed |= S.set_formula(pid, by_name[KEY_STEP], expression)
    # 3 · the search: another tax holding that key, oldest first
    changed |= S.save_search(pid, by_name[FIND_STEP], ws(),
                             key_search_filter(by_name[FIND_STEP]['id'], f[TAX_KEY], node_ids['key'], start))
    # 4 · the gateway's two paths: the condition on the duplicate one, none on the default
    nodes = proc['flowNodeMap']
    paths = [nodes[i] for i in by_name[DUP_GATEWAY].get('flowIds') or []]
    if len(paths) != 2:
        sys.exit(f'G: the gateway has {len(paths)} paths, want 2')
    dup_path = next((p for p in paths if nodes.get(p.get('nextId') or '', {}).get('name') == TICK_STEP), None)
    free_path = next((p for p in paths if p is not dup_path), None)
    if not dup_path or nodes.get(free_path.get('nextId') or '', {}).get('name') != UNTICK_STEP:
        sys.exit(f'G: the gateway paths do not lead to {TICK_STEP!r} and {UNTICK_STEP!r}')
    found_key = [[{'nodeId': by_name[FIND_STEP]['id'], 'filedId': f[TAX_KEY]['controlId'],
                   'filedValue': TAX_KEY, 'filedTypeId': TEXT, 'enumDefault': 0, 'conditionId': NOT_EMPTY_ID,
                   'sourceType': 0, 'conditionValues': []}]]
    changed |= S.save_path(pid, dup_path, PATH_DUP, found_key)
    changed |= S.save_path(pid, free_path, PATH_FREE, [])
    if node_get(pid, free_path['id']).get('conditions'):
        sys.exit(f'G: the else path {PATH_FREE!r} carries a condition; it must have none')
    # 5 · the two ticks, the clear and the key write
    for node_name, value in ((TICK_STEP, '1'), (UNTICK_STEP, '0')):
        changed |= S.save_update(pid, by_name[node_name]['id'], node_name, start,
                                 [{'fieldId': f[DUPLICATE]['controlId'], 'type': SWITCH, 'addType': 0,
                                   'fieldValue': value, 'fieldValueId': '', 'nodeId': ''}], worksheet=ws())
    changed |= S.save_update(pid, by_name[CLEAR_STEP]['id'], CLEAR_STEP, start,
                             [{'fieldId': f[TAX_KEY]['controlId'], 'type': TEXT, 'addType': 0,
                               'fieldValue': '', 'fieldValueId': '', 'nodeId': '', 'isClear': True}],
                             worksheet=ws())
    changed |= S.save_update(pid, by_name[WRITE_KEY_STEP]['id'], WRITE_KEY_STEP, start,
                             [{'fieldId': f[TAX_KEY]['controlId'], 'type': TEXT, 'addType': 0,
                               'fieldValue': f"${node_ids['key']}-{STRING_FX}$", 'fieldValueId': '',
                               'nodeId': ''}], worksheet=ws())
    # 6 · quiet, then publish
    changed |= ensure_quiet(pid, 'G')
    info = read('workflow', 'get', pid)
    if (info.get('explain') or '') != G_DESC:
        hap.run('workflow', 'update', pid, '-n', WF_G, '-d', G_DESC)
        changed = True
    if changed or not info.get('enabled') or info.get('publishStatus') != 2:
        result = C.publish(pid)
        print(f'  G: published {result}')
        if not result.get('isPublish'):
            sys.exit(f'G: publish failed: {result}')
    print(C.structure(pid))
    print(f"  G {WF_G}: {pid} — trigger {g_trigger_state(pid, start)}, quiet "
          f"{read('workflow', 'config-get', pid).get('triggerType')}")
    return 0


# ── 6 · roles ───────────────────────────────────────────────────────────────

def step_roles():
    """roles.py owns the app's roles; its ORDER and its four matrices now carry Taxes with **Chart of Accounts'
    row unchanged** — Accounting Administrator full, Accountant, Invoicing and Accounting Read-only view.
    `account.tax` has exactly the access shape of `account.account` in the same `ir.model.access.csv`
    (13-taxes.md §1 › Roles), so no new decision was needed."""
    import roles
    before = snap()
    roles.step_create()
    expect(before, 'roles (no worksheet control may change)')
    return roles.step_check()


# ── 7 · the 35 taxes ────────────────────────────────────────────────────────

# §1's own three figures for the extract; `names` and `fnv` are printed beside them with no §1 column, because
# §1's are not reproducible. §1 says "fourteen of the 35 names are shared by two records", where the file holds
# **eight** names shared by two records (sixteen records), leaving **27** distinct names; and §1 quotes an
# FNV-1a of `0x4d7cffdc` without saying how the 35 per-record digests are combined, so its number cannot be
# recomputed. What this step proves instead is that the **live** records and the **extract** give the same
# digest, which is the claim that matters (§2 › Where the build departed from §1).
DIGESTS = {'count': 35, 'active': 10, 'amount_sum': 139.0}


def listed(v):
    if isinstance(v, str):
        v = json.loads(v) if v.startswith('[') else []
    return v if isinstance(v, list) else []


def option_label(v, control):
    """A single select read back through **GetRowDetail** is a JSON list of the option **keys** — not the
    `[{"value": …}]` the v3 `record get` hands back — so the label is looked up in this script's own option
    table (Found while building)."""
    keys = [x.get('key') if isinstance(x, dict) else x for x in listed(v)]
    return LABEL_OF_KEY[control].get(keys[0], keys[0]) if keys else ''


def relation_names(v):
    return [x.get('name') for x in listed(v) if isinstance(x, dict)]


def flag(v):
    return str(v) in ('1', 'True', 'true')


def number(v, places):
    try:
        return round(float(v or 0), places)
    except (TypeError, ValueError):
        return None


def read_tax(rowid, detail=None):
    """One tax's stored values, keyed by controlId — through the session's GetRowDetail, because `record list`
    returns only the default view's columns and blanks a hidden control (BUILDING.md)."""
    import states as S
    f = fields_of(ws())
    d = detail if detail is not None else S.row_detail(ws(), rowid)
    cid = lambda n: d.get(f[n]['controlId'])
    countries = relation_names(cid(COUNTRY))
    return dict(rowid=rowid, name=cid(NAME) or '', type=option_label(cid(TYPE), TYPE),
                scope=option_label(cid(SCOPE), SCOPE), computation=option_label(cid(COMPUTATION), COMPUTATION),
                amount=number(cid(AMOUNT), 4), formula=cid(FORMULA) or '', description=cid(DESCRIPTION) or '',
                label=cid(LABEL) or '', group=option_label(cid(GROUP), GROUP),
                country=countries[0] if countries else '', sequence=number(cid(SEQUENCE), 0),
                active=flag(cid(ACTIVE)), affect=flag(cid(AFFECT)), affected=flag(cid(AFFECTED)),
                price_include=option_label(cid(PRICE_INC), PRICE_INC), key=cid(TAX_KEY) or '',
                duplicate=flag(cid(DUPLICATE)))


def read_taxes():
    """Every tax, by rowid."""
    import states as S
    return {r['rowid']: read_tax(r['rowid']) for r in S.rows(ws())}


def live_key(t):
    """The natural key of a live tax, from what a person can see — not from the hidden Tax key."""
    use = {'Sales': 'sale', 'Purchases': 'purchase', 'None': 'none'}.get(t['type'], '')
    scope = {'Goods': 'consu', 'Services': 'service'}.get(t['scope'], '')
    return f"MY|{use}|{scope}|{t['name']}"


def expected(e):
    return dict(name=e['name'], type=LABEL_OF_ODOO[TYPE][e['type_tax_use']],
                scope=LABEL_OF_ODOO[SCOPE].get(e['tax_scope'] or '', ''),
                computation=LABEL_OF_ODOO[COMPUTATION][e['amount_type']], amount=round(float(e['amount']), 4),
                formula=e['formula'], description=e['description'] or '', label=e['invoice_label'] or '',
                group=e['tax_group'], country=e['country'], sequence=float(e['sequence']),
                active=bool(e['active']), affect=False, affected=True, price_include='')


def values_for(f, e, malaysia):
    """The record write for one tax. **Active is always explicit** (BUILDING.md), and so are the two base
    switches — every one of the 35 is Affect Base off, Base Affected on."""
    want = expected(e)
    cells = [{'id': f[NAME]['controlId'], 'value': want['name']},
             {'id': f[TYPE]['controlId'], 'value': [KEY_OF[TYPE][want['type']]]},
             {'id': f[COMPUTATION]['controlId'], 'value': [KEY_OF[COMPUTATION][want['computation']]]},
             {'id': f[AMOUNT]['controlId'], 'value': want['amount']},
             {'id': f[FORMULA]['controlId'], 'value': want['formula']},
             {'id': f[DESCRIPTION]['controlId'], 'value': want['description']},
             {'id': f[LABEL]['controlId'], 'value': want['label']},
             {'id': f[GROUP]['controlId'], 'value': [KEY_OF[GROUP][want['group']]]},
             {'id': f[COUNTRY]['controlId'], 'value': [malaysia]},
             {'id': f[SEQUENCE]['controlId'], 'value': want['sequence']},
             {'id': f[ACTIVE]['controlId'], 'value': 1 if want['active'] else 0},
             {'id': f[AFFECT]['controlId'], 'value': 0},
             {'id': f[AFFECTED]['controlId'], 'value': 1}]
    if want['scope']:
        cells.append({'id': f[SCOPE]['controlId'], 'value': [KEY_OF[SCOPE][want['scope']]]})
    return cells


def malaysia_rowid():
    cty = wid(COUNTRIES)
    name_cid = hap.by_name(hap.controls(cty))['Country Name']['controlId']
    rows = [r['rowid'] for r in C.records(cty, APP) if r.get(name_cid) == 'Malaysia']
    if len(rows) != 1:
        sys.exit(f'{len(rows)} countries are called Malaysia')
    C.remember('records', 'Countries: MY', rows[0])
    return rows[0]


def differences(live, want, keys=None):
    return {k: (live.get(k), v) for k, v in want.items() if (keys is None or k in keys) and live.get(k) != v}


def step_seed():
    """The 35 taxes of the extract, matched by Odoo's own natural key — country, type, scope and name, the four
    the constraint is on. A tax already stored as the extract has it is left alone, so a second run writes
    nothing.

    Every create carries Tax Name, Tax Type, Tax Scope and Country, so **workflow G runs once per record** and
    writes the 35 keys itself; `keys` reads them back and backfills anything a run missed. 35 runs is a
    rounding error against the organisation's quota — States' 2 102 were backfilled through the API for exactly
    that reason."""
    guard()
    import states as S
    f = fields_of(ws())
    reference = taxes_data()
    malaysia = malaysia_rowid()
    live = {live_key(t): t for t in read_taxes().values()}
    hap.backup('taxes_records_pre_seed', live)
    fresh, updates = [], []
    for key, e in reference.items():
        current = live.get(key)
        cells = values_for(f, e, malaysia)
        if current and not differences(current, expected(e)):
            continue
        (updates if current else fresh).append((key, e, current, cells))
    for key, e, current, cells in updates:
        hap.run('worksheet', 'record', 'update', ws(), current['rowid'], '-a', APP,
                '--fields-json', json.dumps(cells, ensure_ascii=False))
        print(f"  updated {key}: {differences(current, expected(e))}")
    for key, e, _, cells in fresh:
        rowid = C.row_id(hap.run('worksheet', 'record', 'create', ws(), '-a', APP,
                                 '--fields-json', json.dumps(cells, ensure_ascii=False)))
        print(f'  created {key}: {rowid}')
    print(f'  {len(fresh) + len(updates)} taxes written')
    if fresh or updates:
        time.sleep(20)                                # let G's runs land before the keys are read
    remember_records()
    return step_verify()


def remember_records():
    ids = hap.ids()
    records = ids.setdefault('records', {})
    mapping = {KEY + k: t['rowid'] for k, t in ((live_key(t), t) for t in read_taxes().values())
               if not t['name'].startswith('TEST')}
    if any(records.get(k) != v for k, v in mapping.items()):
        records.update(mapping)
        C.save_ids(ids)


def fnv1a(text):
    h = 0x811c9dc5
    for b in text.encode('utf-8'):
        h = ((h ^ b) * 0x01000193) & 0xffffffff
    return h


def digest_of(rows):
    """§1's own digest: FNV-1a over `name|type|scope|computation|amount|active|description|label|group` of
    every record, in the extract's order."""
    h = 0
    for r in rows:
        line = '|'.join([r['name'], r['type'], r['scope'], r['computation'], f"{r['amount']:g}",
                         '1' if r['active'] else '0', r['description'], r['label'], r['group']])
        h ^= fnv1a(line)
    return h


def step_verify():
    """Every live tax against the 19.4 extract, field by field, then §1's digests."""
    reference = taxes_data()
    live = {live_key(t): t for t in read_taxes().values()}
    bad, missing = {}, []
    for key, e in reference.items():
        current = live.get(key)
        if not current:
            missing.append(key)
            continue
        diff = differences(current, expected(e))
        if diff:
            bad[key] = diff
    extra = sorted(k for k in live if k not in reference)
    print(f'  {len(reference)} taxes in the extract; {len(missing)} missing {missing[:5]}; '
          f'{len(bad)} differing {json.dumps(bad, ensure_ascii=False)[:500]}; '
          f'{len(extra)} live records outside it {extra[:5]}')
    seeded = [live[k] for k in reference if k in live]
    got = {'count': len(seeded), 'active': sum(1 for t in seeded if t['active']),
           'amount_sum': round(sum(t['amount'] for t in seeded), 4),
           'names': len({t['name'] for t in seeded}), 'fnv': hex(digest_of(seeded))}
    want = {'count': len(reference), 'active': sum(1 for e in reference.values() if e['active']),
            'amount_sum': round(sum(float(e['amount']) for e in reference.values()), 4),
            'names': len({e['name'] for e in reference.values()}),
            'fnv': hex(digest_of([expected(e) for e in reference.values()]))}
    for key in ('count', 'active', 'amount_sum', 'names', 'fnv'):
        mark = 'OK  ' if got[key] == want[key] else 'DIFF'
        note = '' if key not in DIGESTS else f"  §1 {DIGESTS[key]}{'' if DIGESTS[key] == want[key] else '  ← §1 differs'}"
        print(f'  {mark}  {key:<11} live {got[key]!s:<14} extract {want[key]}{note}')
    return len(missing) + len(bad) + sum(1 for k in got if got[k] != want[k])


def key_column():
    """The taxes whose **Tax key** is empty and the ones carrying **Duplicate name**, in two filtered calls.

    A hidden control comes back from `GetFilterRows` as the empty string whatever it holds (BUILDING.md), so
    the keys cannot be read from the list — but a **filter** on it still works, which is how the backfill finds
    its work without reading 35 records one at a time."""
    from hap_cli.core import record as rec
    f = fields_of(ws())
    s = session()
    empty = {r['rowid'] for r in (rec.get_records(s, ws(), page_size=1000,
                                                  filters=[C.cond(f[TAX_KEY], C.EMPTY)])['data'] or [])}
    ticked = {r['rowid'] for r in (rec.get_records(s, ws(), page_size=1000,
                                                   filters=[C.cond(f[DUPLICATE], C.EQ, 1)])['data'] or [])}
    return empty, ticked


def write_field(worksheet, rowid, control, value):
    """One `record update` through the session; returns (ok, resultCode, message)."""
    from hap_cli.core import record as rec
    try:
        rec.update_record(session(), worksheet, rowid,
                          [{'controlId': control['controlId'], 'value': value}], trigger_workflow=True)
        return True, 1, ''
    except Exception as error:                      # hap_cli raises APIError on resultCode != 1
        return False, getattr(error, 'code', None), str(error)[:200]


def step_keys(*args):
    """Every tax's **Tax key**, read back one record at a time, against the key its own fields imply — and the
    backfill for anything workflow G's run missed.

    The seed's 35 creates each start G, which writes the key; this step is the check, and it repairs rather
    than merely reporting, because a key written through the API carries none of G's trigger fields and so
    starts nothing."""
    f = fields_of(ws())
    live = read_taxes()
    empty, ticked = key_column()
    bad, fixed = {}, []
    for rowid, t in live.items():
        want = live_key(t) if t['type'] != 'None' else ''
        if t['key'] == want:
            continue
        if not t['key'] and want and 'norepair' not in args:
            ok, code, message = write_field(ws(), rowid, f[TAX_KEY], want)
            fixed.append((t['name'], want, ok, code))
            if ok:
                continue
        bad[f"{t['name']} ({rowid[:8]})"] = (t['key'], want)
    print(f'  {len(live)} taxes: {len(live) - len(empty)} carried a {TAX_KEY} before this step, {len(empty)} '
          f'did not, {len(ticked)} carry {DUPLICATE}')
    for name, want, ok, code in fixed:
        print(f'  backfilled {name!r} -> {want!r} ({"ok" if ok else f"REFUSED resultCode {code}"})')
    if bad:
        print(f'  DIFF  {len(bad)} keys differ: {json.dumps(bad, ensure_ascii=False)[:600]}')
    else:
        print(f'  OK    every tax holds the {TAX_KEY} its Country, Tax Type, Tax Scope and Tax Name imply')
    for rowid in sorted(ticked):
        t = live.get(rowid) or {}
        print(f"    {DUPLICATE}: {t.get('name')!r} key {t.get('key')!r}")
    return len(bad)


# ── 10 · Taxes, Tax rate and Total on Invoice Lines ─────────────────────────

LINE_TAXES, LINE_RATE, LINE_TOTAL = 'Taxes', 'Tax rate', 'Total'
EQ_SINGLE = 51                                      # the filter editor's "is" on a single select (BUILDING.md)


def rate_filter(f):
    """The 汇总's own filter — the view-editor enum, as Payment Terms' *Percent total* carries it: **Tax
    Computation is Percentage**. §1's open question 2 is whether `filterType` 51 takes on a **Dropdown** (type
    11) of the related worksheet, where bundle 3 only ever proved it on a single select of a mounted 子表."""
    return [{'controlId': f[COMPUTATION]['controlId'], 'dataType': DROPDOWN, 'spliceType': 1,
             'filterType': EQ_SINGLE, 'dateRange': 0, 'dateRangeType': 0, 'value': '',
             'values': [KEY_OF[COMPUTATION]['Percentage']], 'minValue': '', 'maxValue': '', 'isAsc': False,
             'dynamicSource': [], 'isGroup': False, 'groupFilters': None, 'emptyRule': 0}]


def total_expression(lf):
    """Odoo `price_total` for a percentage tax: Subtotal × (1 + the rate ÷ 100).

    A HAP **number** formula is plain arithmetic over `$controlId$` and needs no `c` prefix without a
    function. Whether it may read a **汇总** at all is §1's open question 1 — `measure` answers it."""
    return f"${lf['Subtotal']['controlId']}$*(1+${lf[LINE_RATE]['controlId']}$/100)"


def step_lines():
    """**Taxes**, **Tax rate** and **Total** on Invoice Lines, then the places, the rule, the columns and the
    eight seeded lines' taxes.

    Three appends, because each control is built on the one before it and a control added with `add-fields`
    keeps its client-side id until a full save re-mints it (BUILDING.md):

      1. **Taxes** — a Relation → Taxes, **multiple**, one-way, unfiltered. Odoo's own context on `tax_ids` is
         `{'active_test': False}` and it carries no Tax Type domain, so the picker offers every tax, archived
         ones included;
      2. **Tax rate** — a 汇总 (type 37) over that relation, `sourceControlId` the Taxes worksheet's **Amount**,
         aggregate **sum**, filtered to Tax Computation is Percentage. Hidden and read-only;
      3. **Total** — a number formula, 2 decimals, `Subtotal × (1 + Tax rate ÷ 100)`.

    The placing, the *A section or a note carries no figures* rule and the two column lists are **invlines.py's
    own steps**, whose spec now carries the three controls: `layout` puts Taxes between Discount (%) and
    Subtotal and Total after Subtotal (Odoo's own column order) and re-places the subtable on Invoices,
    `rules` adds the three to what a section hides, `views` adds Total to the standalone list."""
    guard()
    import invlines as L
    L.guard()
    tf = fields_of(ws())
    lf = C.fields(L.ws())
    if LINE_TAXES not in lf:
        before = snap()
        hap.backup('taxes_invlines_controls_pre_lines', hap.controls(L.ws()))
        C.append_controls(L.ws(), [C.control('RELATE_SHEET', LINE_TAXES, L.PLACE[LINE_TAXES],
                                             alias=L.ALIAS[LINE_TAXES], hint='', desc=L.DESC[LINE_TAXES],
                                             data_source=ws(), multi=True,
                                             advanced_setting={'bidirectional': '0', 'showtype': '3'})])
        expect(before, f'{LINES}: {LINE_TAXES} added', new={LINES: {LINE_TAXES}})
        lf = C.fields(L.ws())
        print(f"  {LINES} / {LINE_TAXES}: {lf[LINE_TAXES]['controlId']} (multiple, one-way, unfiltered)")
    if LINE_RATE not in lf:
        from hap_cli.core.app_creator.fields import rollup_control
        c = rollup_control(LINE_RATE, via_control_id=lf[LINE_TAXES]['controlId'],
                           source_control_id=tf[AMOUNT]['controlId'], aggregate='sum',
                           filters=rate_filter(tf))
        row, col, size = L.PLACE[LINE_RATE]
        c.update(controlName=LINE_RATE, alias=L.ALIAS[LINE_RATE], row=row, col=col, size=size,
                 dot=L.DOT[LINE_RATE], desc=L.DESC[LINE_RATE], hint='', fieldPermission=L.PERMISSION[LINE_RATE])
        before = snap()
        C.add_fields(L.ws(), [c])
        expect(before, f'{LINES}: {LINE_RATE} added', new={LINES: {LINE_RATE}},
               changed={LINES: {n: {'*'} for n in L.PLACE}})
        lf = C.fields(L.ws())
        print(f"  {LINES} / {LINE_RATE}: {lf[LINE_RATE]['controlId']} (汇总, sum of {WORKSHEET}/{AMOUNT} "
              f"through {LINE_TAXES}, filtered {COMPUTATION} is Percentage)")
    if LINE_TOTAL not in lf:
        row, col, size = L.PLACE[LINE_TOTAL]
        # `nullzero "1"`: the server's default for a Formula is "0", and with it a blank Subtotal or Tax rate makes
        # Total store **nothing** (invlines.py BLANK_IS_ZERO, proved 23 Sep 2026). `L.step_layout()` below carries
        # the same key, so a Total created before the fix is corrected rather than left.
        c = C.control('FORMULA_NUMBER', LINE_TOTAL, (row, col, size), alias=L.ALIAS[LINE_TOTAL], hint='',
                      desc=L.DESC[LINE_TOTAL], readonly=True, advanced_setting=dict(L.BLANK_IS_ZERO),
                      extra={'dot': L.DOT[LINE_TOTAL], 'dataSource': total_expression(lf)})
        before = snap()
        C.add_fields(L.ws(), [c])
        expect(before, f'{LINES}: {LINE_TOTAL} added', new={LINES: {LINE_TOTAL}},
               changed={LINES: {n: {'*'} for n in L.PLACE}})
        lf = C.fields(L.ws())
        print(f"  {LINES} / {LINE_TOTAL}: {lf[LINE_TOTAL]['controlId']} = {total_expression(C.fields(L.ws()))}")
    want = total_expression(lf)
    if lf[LINE_TOTAL].get('dataSource') != want:
        ctrls, version = C.controls_with_version(L.ws())
        for c in ctrls:
            if c['controlName'] == LINE_TOTAL:
                c['dataSource'] = want
        C.save_controls(L.ws(), ctrls, version=version)
        print(f'  {LINE_TOTAL}: expression rewritten to {want}')
    # places, the rule and the two column lists are invlines.py's own steps, against its own (extended) spec
    L.step_layout()
    L.step_rules()
    L.step_views()
    for c in hap.controls(L.ws()):
        C.remember('controls', f'{LINES}: ' + c['controlName'], c['controlId'])
    return step_line_taxes()


# The tenant's own taxes on the eight seeded lines (reference/odoo-19.4/account.tax.md › Taxes in use):
# SCG-PO-88213's three and INV/2026/00001's three take 10% G, STL-2026-0042's two take 8% S.
#
# Each names the **natural key**, not the name, because two taxes are called *10% G* and two *8% S* — a Sales
# one and a Purchases one. All three of these documents are **Customer Invoices** (06's own seed: SCG-PO-88213
# and STL-2026-0042 are drafts, KKD-2026-009 is INV/2026/00001), so all three take the **Sales** tax, which is
# also what automation B's tax fill writes on a customer branch. The key of the index is the document's
# **Customer Reference**, as `invlines.invoice_numbers()` returns it: two of the three are unnumbered drafts.
LINE_TAX_SEED = {'SCG-PO-88213': 'MY|sale|consu|10% G',
                 'KKD-2026-009': 'MY|sale|consu|10% G',
                 'STL-2026-0042': 'MY|sale|service|8% S'}


def step_line_taxes():
    """The eight seeded lines' Taxes, from the tenant's own documents."""
    import invlines as L
    lf = C.fields(L.ws())
    by_key = {k: t['rowid'] for k, t in ((live_key(t), t) for t in read_taxes().values())}
    documents = L.invoice_numbers()
    wanted = {}
    for ref, key in LINE_TAX_SEED.items():
        if ref not in documents:
            sys.exit(f'the document {ref} is not in {INVOICES}')
        if key not in by_key:
            sys.exit(f'no tax {key!r} — run `seed` first')
        wanted[documents[ref][0]] = (key, by_key[key])
    written = 0
    for line in L.read_lines().values():
        want = wanted.get(line['invoice_row'])
        if not want or line['display_type'] != 'Product':
            continue
        d = hap.run('worksheet', 'record', 'get', L.ws(), line['rowid'], '-a', APP)['data']
        got = [x.get('sid') for x in L.relation_cells(d.get('tax_ids'))]
        if got == [want[1]]:
            continue
        hap.run('worksheet', 'record', 'update', L.ws(), line['rowid'], '-a', APP, '--fields-json',
                json.dumps([{'id': lf[LINE_TAXES]['controlId'], 'value': [want[1]]}]))
        written += 1
        print(f"  {line['move_name'] or line['invoice']} line {line['sequence']}: {LINE_TAXES} = {want[0]}")
    print(f'  {written} lines given their taxes')
    return line_report()


def line_report():
    import invlines as L
    lf = C.fields(L.ws())
    import states as S
    bad = 0
    for line in sorted(L.read_lines().values(), key=lambda x: (x['invoice'], x['sequence'])):
        d = hap.run('worksheet', 'record', 'get', L.ws(), line['rowid'], '-a', APP)['data']
        detail = S.row_detail(L.ws(), line['rowid'])
        rate = number(detail.get(lf[LINE_RATE]['controlId']), 4)
        total = number(detail.get(lf[LINE_TOTAL]['controlId']), 2)
        taxes = L.relation_names(d.get('tax_ids'))
        want = round(line['subtotal'] * (1 + (rate or 0) / 100), 2)
        ok = total == want
        bad += not ok
        print(f"  {'OK  ' if ok else 'DIFF'}  {line['invoice'][:22]:<22} seq {line['sequence']:<4} "
              f"subtotal {line['subtotal']:>12,.2f}  taxes {taxes}  rate {rate}  total {total}"
              + ('' if ok else f' — want {want}'))
    return bad


# ── 8 · Sales Taxes and Purchase Taxes on Products ──────────────────────────
#
# Odoo's product form carries them in the right column of *General Information*: Sales Price · **Sales Taxes** ·
# Cost · **Purchase Taxes** · Category · Reference. HAP's grid pairs a row rather than stacking two columns, so
# each takes a full-width row of its own straight after the money field it follows — which is Odoo's sequence.
# Everything below them in the General Information tab, and the three tabs under it, moves down two rows.
#
# **products.py is not run.** Its own PLACE predates another administrator's edits — it still puts Product Type
# at row 4, Active at row 15 and knows neither the re-created Favorite nor Delivery Time — so running its
# `layout` would rewrite the live form. This step does its own placing save instead, pinned to the control
# set's version so an edit made between the read and the save is refused rather than overwritten.

SALES_TAXES, PURCHASE_TAXES = 'Sales Taxes', 'Purchase Taxes'
PRODUCT_TAXES = {SALES_TAXES: ('taxes_id', 'Sales', 12),
                 PURCHASE_TAXES: ('supplier_taxes_id', 'Purchases', 12)}
PRODUCT_DESC = {
    SALES_TAXES: 'Default taxes used when selling this product.',
    PURCHASE_TAXES: 'Default taxes used when buying this product.',
}
PRODUCT_AFTER = {SALES_TAXES: 'Sales Price', PURCHASE_TAXES: 'Cost'}   # the control each one follows
PICKER_BASE = {'spliceType': 1, 'dateRange': 0, 'dateRangeType': 0, 'minValue': None, 'maxValue': None,
               'isAsc': False, 'advancedSetting': None, 'isGroup': False, 'groupFilters': None, 'emptyRule': 0}


def tax_picker(use):
    """A Relation's picker filter over Taxes: **Tax Type is `use` and Active is ticked**. A picker filter runs in
    the **browser only** (BUILDING.md), so the UI pass is what proves it.

    The Active half was added on 21 Sep 2026 at the owner's ruling *"follow whichever used by Odoo"*. Odoo's
    `product.template.taxes_id` carries `domain=[('type_tax_use','=','sale')]` on a field whose `active_test` is
    **on**, so an archived tax is never offered on a product. **The invoice line is deliberately the other way** —
    `account.move.line.tax_ids` carries `context={'active_test': False}` — so `lines()` leaves that picker
    unfiltered and must stay that way (13 §3, difference 2)."""
    f = fields_of(ws())
    return json.dumps([{'controlId': f[TYPE]['controlId'], 'dataType': DROPDOWN, **PICKER_BASE,
                        'filterType': C.EQ, 'value': '', 'values': [KEY_OF[TYPE][use]], 'dynamicSource': []},
                       {'controlId': f[ACTIVE]['controlId'], 'dataType': SWITCH, **PICKER_BASE,
                        'filterType': C.EQ, 'value': '', 'values': ['1'], 'dynamicSource': []}],
                      ensure_ascii=False, separators=(',', ':'))


def picker_state(value):
    try:
        items = json.loads(value) if isinstance(value, str) else (value or [])
    except ValueError:
        return value
    return sorted((i.get('controlId'), i.get('dataType'), i.get('filterType'), tuple(sorted(i.get('values') or [])))
                  for i in items)


def absent(live, want):
    """A control attribute the server leaves out reads back as None; compare it as the empty value of the type
    wanted, never with `or`, which would make col 0 and required False look like differences."""
    if live is not None:
        return live
    return '' if isinstance(want, str) else (False if isinstance(want, bool) else 0)


def product_rows(ctrls):
    """{controlId: row} for every Products control once the two tax relations sit where Odoo has them.

    Nothing is hard-coded and nothing is shifted by a fixed amount. The form's **existing row groups** are read
    in their own order, each tax relation is inserted as a group of its own straight after the group holding the
    control it follows (Sales Price, then Cost), and the groups are renumbered 0…n. That is idempotent — a
    second run computes the rows the form already has — and it does not depend on `products.py`'s PLACE, which
    predates another administrator's edits.

    Two things it must not do, both found while building:

    * a blanket "+2 to every row from 6 down" is wrong — the first insertion moves Unit and Cost by **one**,
      the second moves everything under them by two, and Purchase Taxes landed on Unit's row;
    * and it must key by **controlId**, never by name: Products carries a *Sales* checkbox and a *Sales* tab,
      and a name-keyed map put the checkbox on the tab's row.
    """
    parked = [c for c in ctrls if c['controlName'] not in PRODUCT_TAXES and c.get('row', 0) >= 9999]
    if parked:
        sys.exit(f"{PRODUCTS} carries controls nobody has placed: "
                 f"{[(c['controlName'], c['controlId']) for c in parked]} — stopping rather than renumbering "
                 f'a form somebody else is in the middle of')
    taxes = {c['controlName']: c['controlId'] for c in ctrls if c['controlName'] in PRODUCT_TAXES}
    groups, seen = [], {}
    for c in sorted((c for c in ctrls if c['controlName'] not in PRODUCT_TAXES),
                    key=lambda c: (c.get('row', 0), c.get('col', 0))):
        row = c.get('row', 0)
        if row not in seen:
            seen[row] = len(groups)
            groups.append([])
        groups[seen[row]].append(c['controlId'])
    by_id = {c['controlId']: c for c in ctrls}
    index_of = lambda name: max((i for i, g in enumerate(groups)
                                 if any(by_id[cid]['controlName'] == name for cid in g)), default=None)
    for name in sorted(PRODUCT_TAXES, key=lambda n: -(index_of(PRODUCT_AFTER[n]) or 0)):
        after = PRODUCT_AFTER[name]
        at = index_of(after)
        if at is None:
            sys.exit(f'{PRODUCTS} has no {after!r} for {name} to follow')
        if name not in taxes:
            sys.exit(f'{PRODUCTS} has no {name} to place')
        groups.insert(at + 1, [taxes[name]])
    return {cid: i for i, g in enumerate(groups) for cid in g}


def product_taxes_desired(name, rows, control):
    alias, use, size = PRODUCT_TAXES[name]
    return {'row': rows[control['controlId']], 'col': 0, 'size': size, 'alias': alias, 'hint': '',
            'desc': PRODUCT_DESC[name], 'required': False, 'fieldPermission': '111', 'dataSource': ws()}


def step_products():
    """**Sales Taxes** and **Purchase Taxes** on Products, and the 14 products' values.

    Odoo defaults both from the company (`account_sale_tax_id` 10% G, `account_purchase_tax_id` 0% NA). **No
    default is built** — a HAP Relation defaults to a fixed record, and a company-level setting is not one of
    the six worksheets (§1 › Not built now) — so the values are written here instead: the **8 goods** take
    *10% G* and *0% NA*, the **6 services** take *8% S* and *0% NA*."""
    guard()
    products = wid(PRODUCTS)
    by_key = {k: t['rowid'] for k, t in ((live_key(t), t) for t in read_taxes().values())}
    f = hap.by_name(hap.controls(products))
    new = [n for n in PRODUCT_TAXES if n not in f]
    if new:
        before = snap()
        hap.backup('taxes_products_controls_pre_products', hap.controls(products))
        C.append_controls(products, [
            C.control('RELATE_SHEET', n, (0, 0, PRODUCT_TAXES[n][2]), alias=PRODUCT_TAXES[n][0], hint='',
                      desc=PRODUCT_DESC[n], data_source=ws(), multi=True,
                      advanced_setting={'bidirectional': '0', 'showtype': '3',
                                        'filters': tax_picker(PRODUCT_TAXES[n][1])}) for n in new])
        expect(before, f'{PRODUCTS}: {new} added', new={PRODUCTS: set(new)})
        print(f'  added: {new}')
    place_product_taxes()
    return seed_product_taxes(by_key)


def product_layout_differences(ctrls):
    """What the placing save still has to do: the two new controls' place, alias, help and picker, and every
    control whose row the insertion moves."""
    out = {}
    f = hap.by_name(ctrls)
    rows = product_rows(ctrls)
    for name in PRODUCT_TAXES:
        c = f.get(name)
        if not c:
            out[name] = 'missing'
            continue
        diff = {k: (c.get(k), v) for k, v in product_taxes_desired(name, rows, c).items()
                if absent(c.get(k), v) != v}
        picker = (c.get('advancedSetting') or {}).get('filters')
        want = tax_picker(PRODUCT_TAXES[name][1])
        if picker_state(picker) != picker_state(want):
            diff['picker'] = (picker_state(picker), picker_state(want))
        if (c.get('advancedSetting') or {}).get('bidirectional') != '0':
            diff['bidirectional'] = ((c.get('advancedSetting') or {}).get('bidirectional'), '0')
        if diff:
            out[name] = diff
    moved = [c for c in ctrls
             if c['controlName'] not in PRODUCT_TAXES and c.get('row') != rows.get(c['controlId'])]
    if moved:
        out['rows'] = {f"{c['controlName']} ({c['controlId']})": (c.get('row'), rows[c['controlId']])
                       for c in sorted(moved, key=lambda c: c.get('row', 0))}
    return out


def place_product_taxes():
    """One save of Products: the two relations into their rows with their aliases, help and picker filters, and
    every control the insertion moves renumbered with them. The control set's `version` is pinned, so a change
    another administrator makes between the read and this save is **refused** (code 10, 数据过时) rather than
    silently overwritten (BUILDING.md)."""
    products = wid(PRODUCTS)
    ctrls, version = C.controls_with_version(products)
    f = hap.by_name(ctrls)
    if any(n not in f for n in PRODUCT_TAXES):
        sys.exit(f'{PRODUCTS} is missing {[n for n in PRODUCT_TAXES if n not in f]}')
    todo = product_layout_differences(ctrls)
    if not todo:
        print(f'  {PRODUCTS}: the two relations are already in place; nothing saved')
        return False
    hap.backup('taxes_products_controls_pre_place', ctrls)
    rows = product_rows(ctrls)
    general = next((c for c in ctrls if c['type'] == C.TAB and c['controlName'] == 'General Information'), None)
    if not general:
        sys.exit(f'{PRODUCTS} has no General Information tab')
    for c in ctrls:
        name = c['controlName']
        if name in PRODUCT_TAXES:
            c.update(product_taxes_desired(name, rows, c))
            c['sectionId'] = general['controlId']
            c['advancedSetting'] = {**(c.get('advancedSetting') or {}), 'bidirectional': '0', 'showtype': '3',
                                    'filters': tax_picker(PRODUCT_TAXES[name][1])}
        else:
            c['row'] = rows[c['controlId']]
    before = snap()
    C.save_controls(products, ctrls, version=version)
    expect(before, f'{PRODUCTS}: the two relations placed',
           changed={PRODUCTS: {c['controlName']: {'row'} for c in ctrls} |
                    {n: {'*'} for n in PRODUCT_TAXES}})
    left = product_layout_differences(hap.controls(products))
    if left:
        sys.exit(f'{PRODUCTS} read back with differences: {json.dumps(left, ensure_ascii=False)[:600]}')
    print('  placed:', json.dumps(todo, ensure_ascii=False)[:800])
    for c in hap.controls(products):
        if c['controlName'] in PRODUCT_TAXES:
            C.remember('controls', f'{PRODUCTS}: ' + c['controlName'], c['controlId'])
    C.show(products)
    return True


GOODS_TAXES = ('MY|sale|consu|10% G', 'MY|purchase||0% NA')
SERVICE_TAXES = ('MY|sale|service|8% S', 'MY|purchase||0% NA')


def seed_product_taxes(by_key):
    """The 14 products' values: the 8 goods take 10% G / 0% NA, the 6 services 8% S / 0% NA."""
    products = wid(PRODUCTS)
    f = hap.by_name(hap.controls(products))
    written, bad = 0, 0
    for r in C.records(products, APP):
        d = hap.run('worksheet', 'record', 'get', products, r['rowid'], '-a', APP)['data']
        kind = option_label_v3(d.get('type'))
        name = d.get('name') or ''
        if name.startswith('TEST'):
            continue
        keys = SERVICE_TAXES if kind == 'Service' else GOODS_TAXES
        want = [[by_key[keys[0]]], [by_key[keys[1]]]]
        got = [[x.get('sid') for x in listed(d.get('taxes_id'))],
               [x.get('sid') for x in listed(d.get('supplier_taxes_id'))]]
        if got == want:
            continue
        hap.run('worksheet', 'record', 'update', products, r['rowid'], '-a', APP, '--fields-json', json.dumps(
            [{'id': f[SALES_TAXES]['controlId'], 'value': want[0]},
             {'id': f[PURCHASE_TAXES]['controlId'], 'value': want[1]}]))
        back = hap.run('worksheet', 'record', 'get', products, r['rowid'], '-a', APP)['data']
        names = ([x.get('name') for x in listed(back.get('taxes_id'))],
                 [x.get('name') for x in listed(back.get('supplier_taxes_id'))])
        ok = [[x.get('sid') for x in listed(back.get('taxes_id'))],
              [x.get('sid') for x in listed(back.get('supplier_taxes_id'))]] == want
        written += 1
        bad += not ok
        print(f"  {'OK  ' if ok else 'DIFF'}  {name:<46} {kind:<8} sales {names[0]} purchase {names[1]}")
    print(f'  {written} products written')
    return bad


def option_label_v3(v):
    """A single select read back through the **v3** `record get`, which hands back `[{key, value}]`."""
    labels = [x.get('value') if isinstance(x, dict) else x for x in listed(v)]
    return labels[0] if labels else ''


# ── 9 · Default Taxes on Chart of Accounts ──────────────────────────────────

DEFAULT_TAXES = 'Default Taxes'


def step_accounts():
    """**Default Taxes** (`tax_ids`) on Chart of Accounts — 09 § *Not built now* named this as the one field
    the Taxes bundle had to come back for.

    A Relation → Taxes, **multiple**, one-way, not required, on the form under Type, where Odoo's *Accounting*
    tab puts it (Type · Default Taxes · Fiscal Category · Tags · Deferred). **No values**: not one of the
    tenant's accounts has a Default Tax, so it is added empty and nothing is seeded. The column stays switched
    off, as it is on Odoo's own list and as 09's *Chart of Accounts* view already records.

    The placing is `accounts.py layout`'s, whose own PLACE now carries the field — the same arrangement
    products.py has for the two account fields bundle 2 added to it."""
    guard()
    import accounts as A
    A.guard()
    coa = wid(ACCOUNTS)
    f = hap.by_name(hap.controls(coa))
    if DEFAULT_TAXES not in f:
        before = snap()
        hap.backup('taxes_accounts_controls_pre_accounts', hap.controls(coa))
        row, col, size = A.PLACE[DEFAULT_TAXES]
        C.append_controls(coa, [C.control('RELATE_SHEET', DEFAULT_TAXES, (row, col, size),
                                          alias=A.ALIASES[DEFAULT_TAXES], hint='', desc=A.DESC[DEFAULT_TAXES],
                                          data_source=ws(), multi=True,
                                          advanced_setting={'bidirectional': '0', 'showtype': '3'})])
        expect(before, f'{ACCOUNTS}: {DEFAULT_TAXES} added', new={ACCOUNTS: {DEFAULT_TAXES}})
        print(f'  added: {DEFAULT_TAXES}')
    before = snap()
    A.step_layout()
    expect(before, f'{ACCOUNTS}: placed by accounts.py layout',
           changed={ACCOUNTS: {c['controlName']: {'row', 'col', 'size', 'alias', 'desc', 'fieldPermission'}
                               for c in hap.controls(coa)}})
    c = hap.by_name(hap.controls(coa))[DEFAULT_TAXES]
    if (c.get('dataSource') != ws() or c.get('enumDefault') != 2
            or (c.get('advancedSetting') or {}).get('bidirectional') != '0'):
        sys.exit(f'{DEFAULT_TAXES} read back {json.dumps({k: c.get(k) for k in ("dataSource", "enumDefault")})} '
                 f"bidirectional {(c.get('advancedSetting') or {}).get('bidirectional')!r}")
    C.remember('controls', f'{ACCOUNTS}: ' + DEFAULT_TAXES, c['controlId'])
    # §1: no account has a Default Tax, so nothing is seeded — and that is checked rather than assumed.
    import states as S
    filled = [r['rowid'] for r in S.rows(coa) if listed(r.get(c['controlId']))]
    print(f"  {DEFAULT_TAXES}: {c['controlId']} row={c.get('row')} size={c.get('size')} "
          f"alias={c.get('alias')!r} multiple={c.get('enumDefault') == 2}; "
          f'{len(filled)} accounts carry one (§1: none)')
    return len(filled)


# ── 11 · the roll-up, and the tax fill inside automation B ──────────────────
#
# 07 built two workflows with five steps each — one for 新增或更新, one for 删除, because HAP's worksheet trigger
# takes one event. Each gains **two steps**, step 4's formula changes and step 5 writes one field more:
#
#   2   sum of the product lines' Subtotal (汇总, 107)          unchanged
#   2b  sum of the same lines' Total, same filter               NEW
#   3   Untaxed Amount = $2$+0                                  unchanged
#   3b  Tax = $2b$-$2$                                          NEW
#   4   Total and Amount Due = $2b$+0                           was $2$+$the invoice's stored Tax$
#   5   writes Untaxed Amount, Total, Amount Due **and Tax**    Tax was read and never written
#
# Σ Total − Σ Subtotal is the document's tax exactly, because each line's Total is itself rounded to two
# decimals and the company rounds per line (`tax_calculation_rounding_method = round_per_line`).

ROLLUPS = {'Roll the lines up into the invoice': 'create_or_update',
           'Roll the lines up when a line is deleted': 'delete'}
SUM_STEP = "The sum of the invoice's product lines"
SUM_TOTAL_STEP = "The sum of the same lines' Total"
UNTAXED_STEP = 'The Untaxed Amount'
TAX_STEP = 'The Tax'
TOTAL_STEP = 'The Total and the Amount Due'
WRITE_STEP = 'Write the amounts into the invoice'
GET_INVOICE = 'Get the invoice'
NUMBER_FX = 'number_fx_id'
WORKSHEET_TOTAL, NUMBER_FORMULA = '107', '100'
FORMULA_NODE = 9
MONEY_DOT = 2
RELATION_EQ, DROPDOWN_IS_ANY_OF = '33', '1'
ROLLUP_DESC = ("Odoo's account.move `_compute_amount`: Untaxed Amount is the sum of the lines' Subtotal, Total "
               "is the sum of the lines' Total, and the Tax is the difference — which is exact, because each "
               'line rounds its own tax to two decimals, as the company does (round_per_line). Amount Due is '
               'the Total until the Payments bundle can settle a document.')


def rollup_ids():
    import invlines as L
    lf = C.fields(L.ws())
    inv = hap.ids()['controls']
    return dict(lines=L.ws(), invoices=wid(INVOICES), line_invoice=lf['Invoice']['controlId'],
                line_type=lf['Display Type']['controlId'], line_subtotal=lf['Subtotal']['controlId'],
                line_total=lf[LINE_TOTAL]['controlId'], product_line=L.PRODUCT_LINE,
                untaxed=inv['Invoices: Untaxed Amount'], tax=inv['Invoices: Tax'],
                total=inv['Invoices: Total'], due=inv['Invoices: Amount Due'])


def rollup_filter(x, node_id, invoice_node):
    """The same filter step 2 carries: the lines of **this** invoice whose Display Type is Product. A 107
    node's conditions have their own `nodeId` rewritten by the server to the aggregate node; what binds the
    sum to a record is the comparison value's `nodeId` (BUILDING.md)."""
    return [[
        {'nodeId': node_id, 'nodeType': 18, 'appType': 1, 'actionId': WORKSHEET_TOTAL,
         'filedId': x['line_invoice'], 'filedValue': 'Invoice', 'filedTypeId': RELATION, 'enumDefault': 1,
         'conditionId': RELATION_EQ, 'sourceType': 2,
         'conditionValues': [{'nodeId': invoice_node, 'controlId': 'rowid'}]},
        {'nodeId': node_id, 'nodeType': 18, 'appType': 1, 'actionId': WORKSHEET_TOTAL,
         'filedId': x['line_type'], 'filedValue': 'Display Type', 'filedTypeId': DROPDOWN, 'enumDefault': 0,
         'conditionId': DROPDOWN_IS_ANY_OF, 'sourceType': 0,
         'conditionValues': [{'value': {'key': x['product_line'], 'value': 'Product', 'isDeleted': False}}]},
    ]]


def total_state(pid, node_id):
    d = node_get(pid, node_id)
    return dict(actionId=str(d.get('actionId')), appId=d.get('appId'),
                reportControlId=d.get('reportControlId'), reportType=d.get('reportType'),
                filters=[(c.get('filedId'), str(c.get('conditionId')),
                          [(v.get('nodeId') or '', v.get('controlId') or '',
                            (v.get('value') or {}).get('key') if isinstance(v.get('value'), dict) else '')
                           for v in c.get('conditionValues') or []])
                         for flt in d.get('filters') or [] for group in flt.get('conditions') or []
                         for c in group])


def save_total(pid, node, x, invoice_node, field):
    """A 汇总 step (9 / 107): the worksheet, the column summed and the filter, read back."""
    conditions = rollup_filter(x, node['id'], invoice_node)
    want = dict(actionId=WORKSHEET_TOTAL, appId=x['lines'], reportControlId=field, reportType=3,
                filters=[(c.get('filedId'), str(c.get('conditionId')),
                          [(v.get('nodeId') or '', v.get('controlId') or '',
                            (v.get('value') or {}).get('key') if isinstance(v.get('value'), dict) else '')
                           for v in c.get('conditionValues') or []])
                         for group in conditions for c in group])
    if total_state(pid, node['id']) == want:
        return False
    hap.run('workflow', 'node', 'save', pid, node['id'], '--type', str(FORMULA_NODE), '-n', node['name'],
            '-c', json.dumps({'actionId': WORKSHEET_TOTAL, 'name': node['name'], 'execute': True,
                              'appId': x['lines'], 'appType': 1, 'reportControlId': field, 'reportType': 3,
                              'filters': [{'spliceType': 1, 'conditions': conditions}]}, ensure_ascii=False))
    got = total_state(pid, node['id'])
    if got != want:
        sys.exit(f"{node['name']}: read back {json.dumps(got, ensure_ascii=False)}, want "
                 f'{json.dumps(want, ensure_ascii=False)}')
    return True


def save_number(pid, node, expression):
    """A number formula step (9 / 100), 2 decimals, empty-as-0 — invlines.set_formula's contract."""
    want = {'formulaValue': expression, 'number': MONEY_DOT, 'nullZero': True}
    got = node_get(pid, node['id'])
    if all(got.get(k) == v for k, v in want.items()):
        return False
    hap.run('workflow', 'node', 'save', pid, node['id'], '--type', str(FORMULA_NODE), '-n', node['name'],
            '-c', json.dumps({'actionId': NUMBER_FORMULA, 'name': node['name'], 'execute': True,
                              'formulaValue': expression, 'number': MONEY_DOT, 'nullZero': True,
                              'type': NUMBER}, ensure_ascii=False))
    back = node_get(pid, node['id'])
    if any(back.get(k) != v for k, v in want.items()):
        sys.exit(f"{node['name']}: read back {[(k, back.get(k)) for k in want]}")
    return True


def from_formula(field_id, node_id):
    """One field write taking a formula node's numeric result. `nodeAppType` is sent as 1 and the server
    stores 11 — it is not compared (invlines.from_formula sends the same)."""
    return {'fieldId': field_id, 'type': NUMBER, 'addType': 0, 'fieldValue': '', 'fieldValueId': NUMBER_FX,
            'nodeId': node_id, 'sureNodeId': node_id, 'nodeAppType': 1, 'nodeTypeId': FORMULA_NODE,
            'nodeActionId': NUMBER_FORMULA}


def write_state(pid, node_id):
    d = node_get(pid, node_id)
    return dict(selectNodeId=d.get('selectNodeId'), appId=d.get('appId'),
                isException=bool(d.get('isException')),
                fields=sorted((f.get('fieldId'), f.get('nodeId') or '', f.get('fieldValueId') or '')
                              for f in d.get('fields') or []))


def insert_node(pid, name, after, node_type, action_id, app_id=None):
    """`node add` inserts a node **after** `after` — the only way to put a step in the middle of a chain
    (`batch-add` can only append to the end). A data or aggregate node's worksheet must be given at create
    time: a later `saveNode` cannot attach `appId` (BUILDING.md)."""
    args = ['workflow', 'node', 'add', pid, '--type', str(node_type), '-n', name, '--after', after,
            '-a', action_id]
    if app_id:
        args += ['--app-id', app_id]
    hap.run(*args)
    proc = hap.run('workflow', 'node', 'list', pid)
    node = next((n for n in proc['flowNodeMap'].values() if n.get('name') == name), None)
    if not node:
        sys.exit(f'{name}: the node was not created')
    print(f"  added {name!r} ({node['id']}) after {after}")
    return proc, node


def step_rollup():
    """07's two roll-up workflows gain steps **2b** and **3b**, step 4 changes and step 5 writes **Tax** — and
    automation B gains the tax fill. `amounts` then drives them over every invoice that has lines."""
    guard()
    x = rollup_ids()
    changed_any = 0
    for name in ROLLUPS:
        pid = hap.ids()['workflows']['Invoice Lines: ' + name]
        proc = hap.run('workflow', 'node', 'list', pid)
        by_name = {n['name']: n for n in proc['flowNodeMap'].values()}
        for want in (GET_INVOICE, SUM_STEP, UNTAXED_STEP, TOTAL_STEP, WRITE_STEP):
            if want not in by_name:
                sys.exit(f'{name}: the workflow has no node {want!r} — {sorted(by_name)}')
        hap.backup(f"taxes_rollup_pre_{name.split()[-1]}",
                   {n: node_get(pid, node['id']) for n, node in by_name.items() if node.get('typeId') != 0})
        changed = False
        if SUM_TOTAL_STEP not in by_name:
            proc, _ = insert_node(pid, SUM_TOTAL_STEP, by_name[SUM_STEP]['id'], FORMULA_NODE,
                                  WORKSHEET_TOTAL, app_id=x['lines'])
            by_name = {n['name']: n for n in proc['flowNodeMap'].values()}
            changed = True
        if TAX_STEP not in by_name:
            proc, _ = insert_node(pid, TAX_STEP, by_name[UNTAXED_STEP]['id'], FORMULA_NODE, NUMBER_FORMULA)
            by_name = {n['name']: n for n in proc['flowNodeMap'].values()}
            changed = True
        chain, node = [], proc['flowNodeMap'][proc['startEventId']].get('nextId')
        while node and node in proc['flowNodeMap']:
            chain.append(proc['flowNodeMap'][node]['name'])
            node = proc['flowNodeMap'][node].get('nextId')
        want_chain = [GET_INVOICE, SUM_STEP, SUM_TOTAL_STEP, UNTAXED_STEP, TAX_STEP, TOTAL_STEP, WRITE_STEP]
        if chain != want_chain:
            sys.exit(f'{name}: the steps run {chain}, want {want_chain}')
        sums, invoice = by_name[SUM_STEP]['id'], by_name[GET_INVOICE]['id']
        totals = by_name[SUM_TOTAL_STEP]['id']
        changed |= save_total(pid, by_name[SUM_TOTAL_STEP], x, invoice, x['line_total'])
        changed |= save_number(pid, by_name[UNTAXED_STEP], f'${sums}-{NUMBER_FX}$+0')
        changed |= save_number(pid, by_name[TAX_STEP], f'${totals}-{NUMBER_FX}$-${sums}-{NUMBER_FX}$')
        changed |= save_number(pid, by_name[TOTAL_STEP], f'${totals}-{NUMBER_FX}$+0')
        fields = [from_formula(x['untaxed'], by_name[UNTAXED_STEP]['id']),
                  from_formula(x['tax'], by_name[TAX_STEP]['id']),
                  from_formula(x['total'], by_name[TOTAL_STEP]['id']),
                  from_formula(x['due'], by_name[TOTAL_STEP]['id'])]
        want = dict(selectNodeId=invoice, appId=x['invoices'], isException=False,
                    fields=sorted((f['fieldId'], f['nodeId'], f['fieldValueId']) for f in fields))
        if write_state(pid, by_name[WRITE_STEP]['id']) != want:
            hap.run('workflow', 'node', 'save', pid, by_name[WRITE_STEP]['id'], '--type', '6',
                    '-n', WRITE_STEP, '-c', json.dumps(
                        {'actionId': '2', 'appId': x['invoices'], 'appType': 1, 'selectNodeId': invoice,
                         'fields': fields}, ensure_ascii=False))
            got = write_state(pid, by_name[WRITE_STEP]['id'])
            if got != want:
                sys.exit(f'{name} / {WRITE_STEP}: read back {got}, want {want}')
            print(f'  {WRITE_STEP}: now writes Untaxed Amount, Tax, Total and Amount Due')
            changed = True
        info = read('workflow', 'get', pid)
        if (info.get('explain') or '') != ROLLUP_DESC:
            hap.run('workflow', 'update', pid, '-n', name, '-d', ROLLUP_DESC)
            changed = True
        if changed or not info.get('enabled') or info.get('publishStatus') != 2:
            result = C.publish(pid)
            print(f'  {name}: published {result}')
            if not result.get('isPublish'):
                sys.exit(f'{name}: publish failed: {result}')
        else:
            print(f'  {name}: already built; not re-published')
        changed_any += changed
        print(C.structure(pid))
    return step_tax_fill()


# ── automation B's tax fill ─────────────────────────────────────────────────

def step_tax_fill():
    """**Automation B gains the tax fill** — §1's third open question, answered: it **fits**.

    09 built two workflows (*fill the account of a new line* and *…when the Product changes*) whose gateway
    already reads the invoice, the variant, the product, the category and the journal and branches
    customer/vendor. The tax fill is the same journey with one more field on four of the seven paths' update
    steps: on a **customer** path the product's **Sales Taxes**, on a **vendor** path its **Purchase Taxes**,
    both taken from the *Get the product* step. **Nothing was rebuilt** — no node, path or condition was
    added, moved or re-conditioned; each of the four steps gained one entry in its `fields` list.

    The three **journal-default** paths write no tax, as §1 says. They are reached when the product and its
    category give no account, and on this tenant every product and every category carries both, so in
    practice they are reached only by a line with no product at all — and a line with no product has no tax
    to take."""
    import accounts as A
    x = A.b_ids()
    if not x.get('line_taxes'):
        sys.exit('Invoice Lines has no Taxes control — run `lines` first')
    problems = []
    for workflow in (A.B_NEW_LINE, A.B_PRODUCT_CHANGED):
        pid = A.b_workflow_id(workflow)
        if not pid:
            sys.exit(f'{workflow}: not built')
        proc, byname = A.nodes_by_name(pid)
        hap.backup(f"taxes_automation_b_pre_tax_fill_{workflow.split()[-1]}",
                   {n: node_get(pid, node['id']) for n, node in byname.items() if node.get('typeId') == 6})
        changed = False
        for step, (source, control) in A.b_tax_fill(x).items():
            node = byname.get(step)
            if not node:
                sys.exit(f'{workflow}: no step {step!r}')
            fields = node_get(pid, node['id']).get('fields') or []
            want = A.b_tax_entry(x, byname, source, control)
            entry = next((f for f in fields if f.get('fieldId') == want['fieldId']), None)
            if entry and all(entry.get(k) == v for k, v in want.items()):
                continue
            if entry:
                entry.update(want)
            else:
                fields.append(want)
            hap.run('workflow', 'node', 'save', pid, node['id'], '--type', '6', '-n', step, '-c', json.dumps(
                {'actionId': '2', 'appId': x['lines'], 'appType': 1, 'selectNodeId': proc['startEventId'],
                 'fields': fields}, ensure_ascii=False))
            changed = True
            print(f"  {workflow.split(':')[1].strip()} / {step}: + Taxes from {control['controlName']}")
        info = hap.run('workflow', 'get', pid)
        info = info.get('data', info)
        if changed or not info.get('enabled') or info.get('publishStatus') != 2:
            result = C.publish(pid)
            print(f'  {workflow}: published {result}')
            if not result.get('isPublish'):
                sys.exit(f'{workflow}: publish failed: {result}')
        else:
            print(f'  {workflow}: the tax fill is already in; not re-published')
        problems += A.automation_b_differences(workflow, x)
    for p in problems:
        print(f'  DIFF  {p}')
    if not problems:
        print('  automation B reads back in full: five searches, seven paths, and the four product paths now '
              'writing the line\'s Taxes beside its Account')
    return len(problems)


# ── 12 · the amounts ────────────────────────────────────────────────────────

TENANT_AMOUNTS = {'SCG-PO-88213': (104603.20, 10460.32, 115063.52),
                  'KKD-2026-009': (11432.00, 1143.20, 12575.20),
                  'STL-2026-0042': (180000.00, 14400.00, 194400.00)}


def line_sums():
    """{invoice rowid: (Σ Subtotal, Σ Total)} over the product lines, from what is stored on the lines — the
    same two sums the roll-up's steps 2 and 2b make."""
    import invlines as L
    import states as S
    lf = C.fields(L.ws())
    out = {}
    for r in S.rows(L.ws()):
        detail = S.row_detail(L.ws(), r['rowid'])
        keys = listed(detail.get(lf['Display Type']['controlId']))
        if keys and keys[0] != L.PRODUCT_LINE:
            continue
        invoice = [x.get('sid') for x in listed(detail.get(lf['Invoice']['controlId']))]
        if not invoice:
            continue
        sub = number(detail.get(lf['Subtotal']['controlId']), 2) or 0.0
        total = number(detail.get(lf[LINE_TOTAL]['controlId']), 2) or 0.0
        a, b = out.get(invoice[0], (0.0, 0.0))
        out[invoice[0]] = (round(a + sub, 2), round(b + total, 2))
    return out


def step_amounts(*only):
    """Drive the roll-up over every invoice that has product lines, so that **Tax stops being a seeded
    figure**.

    Nothing is written into the invoice by hand: each document's own roll-up workflow is started on one of its
    lines (`hap workflow trigger <processId> -s <rowid>`, which runs a **worksheet-event** workflow on one
    record just as it runs a button's), and the amounts are read back afterwards. A `record update` that
    changes nothing fires no workflow (BUILDING.md), so nudging a line would mean writing a value and writing
    it back — this starts the run without touching a record at all."""
    guard()
    import invlines as L
    pid = hap.ids()['workflows']['Invoice Lines: Roll the lines up into the invoice']
    lines_by_invoice = {}
    for line in L.read_lines().values():
        if line['invoice_row'] and line['display_type'] == 'Product':
            lines_by_invoice.setdefault(line['invoice_row'], []).append(line['rowid'])
    sums = line_sums()
    references = {v[0]: k for k, v in L.invoice_numbers().items()}
    hap.backup('taxes_invoices_pre_amounts', {r: L.read_amounts(r) for r in sums})
    bad, driven = 0, 0
    for rowid in sorted(sums, key=lambda r: references.get(r, '')):
        ref = references.get(rowid, rowid[:8])
        if only and ref not in only:
            continue
        untaxed, total = sums[rowid]
        want = dict(untaxed=untaxed, tax=round(total - untaxed, 2), total=total, residual=total)
        got = L.read_amounts(rowid)
        if all(got[k] == v for k, v in want.items()):
            print(f"  OK    {ref:<34} {got['number']:<16} untaxed={got['untaxed']:>12,.2f} "
                  f"tax={got['tax']:>10,.2f} total={got['total']:>12,.2f} due={got['residual']:>12,.2f}")
            continue
        hap.run('workflow', 'trigger', pid, '-s', lines_by_invoice[rowid][0])
        driven += 1
        back = got
        for _ in range(12):
            time.sleep(3)
            back = L.read_amounts(rowid)
            if all(back[k] == v for k, v in want.items()):
                break
        ok = all(back[k] == v for k, v in want.items())
        bad += not ok
        print(f"  {'OK  ' if ok else 'DIFF'}  {ref:<34} {back['number']:<16} "
              f"untaxed={back['untaxed']:>12,.2f} tax={back['tax']:>10,.2f} total={back['total']:>12,.2f} "
              f"due={back['residual']:>12,.2f}" + ('' if ok else f' — want {want} (was {got})'))
    print(f'  {driven} invoices driven through the roll-up')
    for ref, (untaxed, tax, total) in TENANT_AMOUNTS.items():
        rowid = L.invoice_numbers().get(ref, (None,))[0]
        got = L.read_amounts(rowid) if rowid else {}
        ok = (got.get('untaxed'), got.get('tax'), got.get('total')) == (untaxed, tax, total)
        bad += not ok
        print(f"  {'OK  ' if ok else 'DIFF'}  §1's figure  {ref:<16} untaxed {got.get('untaxed'):>12,.2f} "
              f"tax {got.get('tax'):>10,.2f} total {got.get('total'):>12,.2f}"
              + ('' if ok else f' — §1 {untaxed:,.2f} / {tax:,.2f} / {total:,.2f}'))
    return bad


# ── §1's open questions, measured ───────────────────────────────────────────

TEST_PERCENT = 'TEST Percent 3'                     # a Percentage tax of 3 — the 汇总 must count it
TEST_FIXED = 'TEST Fixed 7'                         # a Fixed tax of 7 — the 汇总's filter must leave it out
TEST_NONE = 'TEST Type None'                        # Tax Type None: Odoo exempts it, and so does G
TEST_LINE_INVOICE = 'TEST PT D probe'               # a TEST document with no lines of its own
TEST_LINE_LABEL = 'TEST Tax rate probe'


def ensure_test_tax(name, computation, amount, use='Sales', scope=''):
    """A TEST tax, created once and left in the worksheet."""
    f = fields_of(ws())
    live = {t['name']: t for t in read_taxes().values()}
    if name in live:
        return live[name]['rowid']
    cells = [{'id': f[NAME]['controlId'], 'value': name},
             {'id': f[TYPE]['controlId'], 'value': [KEY_OF[TYPE][use]]},
             {'id': f[COMPUTATION]['controlId'], 'value': [KEY_OF[COMPUTATION][computation]]},
             {'id': f[AMOUNT]['controlId'], 'value': amount},
             {'id': f[GROUP]['controlId'], 'value': [KEY_OF[GROUP]['Not Applicable']]},
             {'id': f[COUNTRY]['controlId'], 'value': [malaysia_rowid()]},
             {'id': f[SEQUENCE]['controlId'], 'value': 1},
             {'id': f[ACTIVE]['controlId'], 'value': 1},
             {'id': f[AFFECT]['controlId'], 'value': 0},
             {'id': f[AFFECTED]['controlId'], 'value': 1}]
    if scope:
        cells.append({'id': f[SCOPE]['controlId'], 'value': [KEY_OF[SCOPE][scope]]})
    rowid = C.row_id(hap.run('worksheet', 'record', 'create', ws(), '-a', APP,
                             '--fields-json', json.dumps(cells, ensure_ascii=False)))
    C.remember('records', KEY + name, rowid)
    print(f'  created {name!r} ({computation} {amount}): {rowid}')
    return rowid


def ensure_test_line():
    """A TEST invoice line with **no Product**, so automation B's tax fill cannot touch its Taxes and the
    probe measures the 汇总 alone."""
    import invlines as L
    lf = C.fields(L.ws())
    live = {l['label']: l for l in L.read_lines().values()}
    if TEST_LINE_LABEL in live:
        return live[TEST_LINE_LABEL]['rowid']
    documents = L.invoice_numbers()
    if TEST_LINE_INVOICE not in documents:
        sys.exit(f'no TEST invoice {TEST_LINE_INVOICE!r} to hang the probe line on')
    rowid = C.row_id(hap.run('worksheet', 'record', 'create', L.ws(), '-a', APP, '--fields-json', json.dumps([
        {'id': lf['Invoice']['controlId'], 'value': [documents[TEST_LINE_INVOICE][0]]},
        {'id': lf['Sequence']['controlId'], 'value': 100},
        {'id': lf['Display Type']['controlId'], 'value': [L.PRODUCT_LINE]},
        {'id': lf['Label']['controlId'], 'value': TEST_LINE_LABEL},
        {'id': lf['Quantity']['controlId'], 'value': 1},
        {'id': lf['Unit Price']['controlId'], 'value': 100},
        {'id': lf['Discount (%)']['controlId'], 'value': 0}], ensure_ascii=False)))
    C.remember('records', f'{LINES}: {TEST_LINE_LABEL}', rowid)
    print(f'  created the probe line {rowid}')
    time.sleep(8)
    return rowid


def line_rate_and_total(rowid):
    import invlines as L
    import states as S
    lf = C.fields(L.ws())
    d = S.row_detail(L.ws(), rowid)
    return (number(d.get(lf['Subtotal']['controlId']), 2), number(d.get(lf[LINE_RATE]['controlId']), 4),
            number(d.get(lf[LINE_TOTAL]['controlId']), 2))


def set_line_taxes(rowid, rowids):
    import invlines as L
    lf = C.fields(L.ws())
    hap.run('worksheet', 'record', 'update', L.ws(), rowid, '-a', APP, '--fields-json',
            json.dumps([{'id': lf[LINE_TAXES]['controlId'], 'value': rowids}]))
    time.sleep(4)


def step_measure():
    """§1's two roll-up questions, measured on a TEST line that carries no Product.

    1. **Does a 汇总 over a multi-Relation follow the relation, and can a number formula read it?**
    2. **Can that 汇总 carry a filter on a Dropdown (type 11) of the related worksheet?**"""
    guard()
    percent = ensure_test_tax(TEST_PERCENT, 'Percentage', 3)
    fixed = ensure_test_tax(TEST_FIXED, 'Fixed', 7)
    line = ensure_test_line()
    results = []
    for label, taxes, want_rate in (('no taxes', [], 0.0),
                                    (f'{TEST_PERCENT} alone', [percent], 3.0),
                                    (f'{TEST_PERCENT} + {TEST_FIXED}', [percent, fixed], 3.0),
                                    (f'{TEST_FIXED} alone', [fixed], 0.0)):
        set_line_taxes(line, taxes)
        subtotal, rate, total = line_rate_and_total(line)
        want_total = round((subtotal or 0) * (1 + want_rate / 100), 2)
        ok = (rate or 0.0) == want_rate and total == want_total
        results.append((label, ok, rate, total, want_rate, want_total))
        print(f"  {'OK  ' if ok else 'DIFF'}  {label:<28} subtotal {subtotal}  Tax rate {rate}  Total {total}"
              + ('' if ok else f'  — want rate {want_rate}, total {want_total}'))
    set_line_taxes(line, [percent])
    reads = [r for r in results if r[3] is not None]
    filtered = results[2][1] and results[3][1]
    print()
    print('  1. A **汇总 over a multi-Relation follows the relation**, and **a number formula can read it**: '
          f'{len(reads)}/{len(results)} probes returned a Total, and it changed with every change of the '
          'relation, through the API alone — so Total is a formula, not a workflow. What a 汇总 does while a '
          'form is **open** (10 §3 found it holds only the saved rows of a 子表) is for §3.')
    print(f"  2. The 汇总's filter **does** take on a Dropdown (type 11) of the related worksheet: "
          f"{'a Fixed tax of 7 added nothing to the rate' if filtered else 'A FIXED TAX WAS COUNTED — the filter did not take'}"
          f' (filterType {EQ_SINGLE}, the same "is" bundle 3 proved on a single select of a 子表).')
    return sum(0 if ok else 1 for _, ok, *_ in results)


# ── self-check ──────────────────────────────────────────────────────────────

TEST_PROBE = 'TEST Duplicate Probe'                 # the duplicate check's own record, left in the worksheet


def tax_state(rowid):
    import states as S
    f = fields_of(ws())
    d = S.row_detail(ws(), rowid)
    return (d.get(f[TAX_KEY]['controlId']) or '', flag(d.get(f[DUPLICATE]['controlId'])))


def rowid_of(name):
    """The probe record of that name — **the one that holds the four-part key** when more than one shares it.

    Exercising the duplicate check through the **UI** leaves a second record with the probe's name behind, which
    is exactly what the house rule asks for (13 §3 tests 13–14). A plain `{name: rowid}` map then keeps whichever
    came last, and the selfcheck drove the *marked* record instead of its own probe: 0c and 0e reported the
    marked record's `('', True)` and read as DIFF although **G had behaved correctly in every probe**
    (18 Sep 2026). Preferring the holder of the key makes a re-run mean what it says; the note says when the
    name is shared, because 0c's premise — that the name is free for this record — depends on it."""
    same = [t for t in read_taxes().values() if t['name'] == name]
    if not same:
        return None
    if len(same) > 1:
        print(f'  note: {len(same)} taxes are named {name!r}; the probe is the one holding its key')
    keyed = [t for t in same if (t.get('key') or t.get('tax_key') or '') == live_key(t)]
    return (keyed or same)[0]['rowid']


def rename_tax(rowid, name):
    f = fields_of(ws())
    hap.run('worksheet', 'record', 'update', ws(), rowid, '-a', APP, '--fields-json',
            json.dumps([{'id': f[NAME]['controlId'], 'value': name}], ensure_ascii=False))


def step_selfcheck():
    """§1's *Rules* and the roll-up, driven through the CLI.

    0a. the **API** refuses a duplicate written into the unique Text Tax key (`resultCode` 11);
    0b. a **create** that does not send the key — the shape of a form save, since the form never renders a
        hidden read-only control — is **accepted**, so the duplicate record still exists and G runs on it;
    0c. a free name: G unticks Duplicate name and writes the key, and the run completes (status 2);
    0d. a name another tax of the same country, type and scope holds: G ticks Duplicate name, clears the key
        and **stops** (status 3, 中止) — the stop is what keeps the key unique, because a workflow's update
        step is not checked against *No duplicates*;
    0e. a save that re-sends an **unchanged** Tax Name does not mark the record as its own duplicate;
    0f. a tax whose **Tax Type is None** starts no run at all, gets no key and is never marked — Odoo skips
        `_constrains_name` for exactly that case;
    0g. the **roll-up**: the probe line's tax changes and the invoice's Untaxed Amount, Tax, Total and Amount
        Due follow."""
    guard()
    import states as S
    import invlines as L
    f = fields_of(ws())
    pid = hap.ids()['workflows'][WF_G]
    problems = []
    percent = ensure_test_tax(TEST_PERCENT, 'Percentage', 3)
    ensure_test_tax(TEST_FIXED, 'Fixed', 7)
    none_tax = ensure_test_tax(TEST_NONE, 'Percentage', 0, use='None')
    probe = rowid_of(TEST_PROBE)
    if not probe:
        known = {r['id'] for r in (hap.run('approval', 'history', '--process-id', pid, '-n', '20')
                                   or {}).get('data') or []}
        probe = ensure_test_tax(TEST_PROBE, 'Percentage', 1)
        C.remember('records', KEY + TEST_PROBE, probe)
        print(f'  OK    0b. a tax **created** through the API with no {TAX_KEY} in the write: accepted, {probe} '
              f'— nothing in HAP refuses the record itself, and a form sends no hidden read-only control either')
        for line in S.run_report(S.runs_since(pid, known, want=1)):
            print(f'        G on the create: {line}')
    else:
        print(f'  OK    0b. {TEST_PROBE} is already there ({probe}) — the create was accepted on an earlier run')
    S.quiesce(lambda: tax_state(probe))
    # 0a · the API refuses a duplicate key on the Text control
    percent_key, _ = tax_state(percent)
    refused, message = S.attempt('worksheet', 'record', 'update', ws(), probe, '-a', APP, '--fields-json',
                                 json.dumps([{'id': f[TAX_KEY]['controlId'], 'value': percent_key}]))
    print(f"  {'OK  ' if refused else 'DIFF'}  0a. a {TAX_KEY} another tax holds, written through the API: "
          f"{'refused' if refused else 'ACCEPTED'} — {message[:140]}")
    if not refused:
        problems.append(f'0a. No duplicates on the {TAX_KEY} Text control did not refuse an API write')
    S.quiesce(lambda: tax_state(probe))
    # 0d / 0c · drive G onto the duplicate name and back off it
    for label, name, want_dup, want_key, want_status in (
            (f'0d. renamed to {TEST_PERCENT}: {DUPLICATE} is ticked, the key is cleared and the run stops '
             f'before the key write', TEST_PERCENT, True, '', 3),
            (f'0c. renamed back to {TEST_PROBE}, a free name: {DUPLICATE} is unticked and the key is written',
             TEST_PROBE, False, f'MY|sale||{TEST_PROBE}', 2)):
        known = {r['id'] for r in (hap.run('approval', 'history', '--process-id', pid, '-n', '20')
                                   or {}).get('data') or []}
        rename_tax(probe, name)
        runs = S.runs_since(pid, known, want=1)
        got = S.quiesce(lambda: tax_state(probe))
        status = [r.get('status') for r in runs]
        ok = got == (want_key, want_dup) and want_status in status
        print(f"  {'OK  ' if ok else 'DIFF'}  {label}: {TAX_KEY} {got[0]!r} {DUPLICATE} {got[1]}, run status "
              f"{status}" + ('' if ok else f' — want {(want_key, want_dup)} and status {want_status}'))
        for line in S.run_report(runs):
            print(f'        G: {line}')
        if not ok:
            problems.append(f'{label}: {got} status {status} != {(want_key, want_dup)} status {want_status}')
    # 0e · an unchanged Tax Name re-sent with a new Description must not mark the record
    known = {r['id'] for r in (hap.run('approval', 'history', '--process-id', pid, '-n', '20')
                               or {}).get('data') or []}
    hap.run('worksheet', 'record', 'update', ws(), probe, '-a', APP, '--fields-json', json.dumps(
        [{'id': f[NAME]['controlId'], 'value': TEST_PROBE},
         {'id': f[DESCRIPTION]['controlId'], 'value': 'the duplicate check probe'}], ensure_ascii=False))
    runs = S.runs_since(pid, known, want=1)
    got = S.quiesce(lambda: tax_state(probe))
    ok = got == (f'MY|sale||{TEST_PROBE}', False)
    print(f"  {'OK  ' if ok else 'DIFF'}  0e. an unchanged Tax Name re-sent with a new Description: {TAX_KEY} "
          f"{got[0]!r} {DUPLICATE} {got[1]} — the search excludes the record that started the run"
          + ('' if ok else f" — want ('MY|sale||{TEST_PROBE}', False)"))
    for line in S.run_report(runs):
        print(f'        G: {line}')
    if not ok:
        problems.append(f'0e. re-sending an unchanged Tax Name gave {got}')
    # 0f · Tax Type None is exempt
    known = {r['id'] for r in (hap.run('approval', 'history', '--process-id', pid, '-n', '20')
                               or {}).get('data') or []}
    rename_tax(none_tax, TEST_NONE + ' ')
    rename_tax(none_tax, TEST_NONE)
    runs = S.runs_since(pid, known, want=1, seconds=40)
    got = tax_state(none_tax)
    ok = got == ('', False) and not runs
    print(f"  {'OK  ' if ok else 'DIFF'}  0f. a tax whose {TYPE} is None: {TAX_KEY} {got[0]!r} {DUPLICATE} "
          f"{got[1]}, {len(runs)} runs in 40 s — Odoo skips its constraint for type None and so does G's "
          f'trigger condition' + ('' if ok else " — want ('', False) and no run"))
    if not ok:
        problems.append(f'0f. a None-typed tax gave {got} with {len(runs)} runs')
    # 0g · the roll-up end to end
    line = ensure_test_line()
    documents = L.invoice_numbers()
    invoice = documents[TEST_LINE_INVOICE][0]
    for label, taxes, rate in (('with no tax', [], 0.0), (f'with {TEST_PERCENT}', [percent], 3.0)):
        set_line_taxes(line, taxes)
        subtotal, got_rate, got_total = line_rate_and_total(line)
        want_tax = round(round(subtotal * rate / 100, 2), 2)
        amounts = S.quiesce(lambda: tuple(L.read_amounts(invoice)[k] for k in ('untaxed', 'tax', 'total',
                                                                               'residual')))
        ok = amounts == (subtotal, want_tax, round(subtotal + want_tax, 2), round(subtotal + want_tax, 2))
        print(f"  {'OK  ' if ok else 'DIFF'}  0g. the roll-up {label}: the line is {subtotal} at {got_rate}%, "
              f"total {got_total}; the invoice reads untaxed/tax/total/due {amounts}"
              + ('' if ok else f' — want ({subtotal}, {want_tax}, …)'))
        if not ok:
            problems.append(f'0g. the roll-up {label} left the invoice at {amounts}')
    set_line_taxes(line, [percent])
    for p in problems:
        print(f'  DIFF  {p}')
    return len(problems)


# ── check ───────────────────────────────────────────────────────────────────

def g_differences(f):
    """Workflow G read back against §1: its nodes, the chain, the trigger, the key formula, the search, the
    gateway's two paths, the abort and the three writes."""
    import states as S
    pid = hap.ids().get('workflows', {}).get(WF_G)
    if not pid:
        return [f'workflow G {WF_G!r} is not built']
    out = []
    proc = hap.run('workflow', 'node', 'list', pid)
    start = proc['startEventId']
    by_name = {n['name']: n for n in proc['flowNodeMap'].values()}
    missing = [n for n in G_NODES if n not in by_name]
    if missing:
        return [f'G is missing {missing}']
    want_fields = sorted([f[NAME]['controlId'], f[TYPE]['controlId'], f[SCOPE]['controlId'],
                          f[COUNTRY]['controlId']])
    want_trigger = dict(name=G_TRIGGER, appId=ws(), fields=want_fields,
                        condition=g_trigger_shape(g_trigger_condition(f, start)))
    got = g_trigger_state(pid, start)
    if got != want_trigger:
        out.append(f'G trigger {got} != {want_trigger}')
    cty_f = hap.by_name(hap.controls(wid(COUNTRIES)))
    want_expr = (key_expression(f, cty_f).replace('$trigger-', f'${start}-')
                                         .replace('$country-', f"${by_name[GET_COUNTRY]['id']}-"))
    if node_get(pid, by_name[KEY_STEP]['id']).get('formulaValue') != want_expr:
        out.append(f"G / {KEY_STEP}: {node_get(pid, by_name[KEY_STEP]['id']).get('formulaValue')!r} != "
                   f'{want_expr!r}')
    search = node_get(pid, by_name[FIND_STEP]['id'])
    conds = [(c.get('filedId'), str(c.get('conditionId'))) for flt in search.get('filters') or []
             for group in flt.get('conditions') or [] for c in group]
    if conds != [(f[TAX_KEY]['controlId'], EQ_ID), ('rowid', NE_ID)] or search.get('appId') != ws():
        out.append(f"G / {FIND_STEP}: appId {search.get('appId')} filters {conds}")
    if by_name[STOP_STEP].get('typeId') != ABORT or by_name[STOP_STEP].get('nextId') not in ('', '99', None):
        out.append(f"G / {STOP_STEP}: typeId {by_name[STOP_STEP].get('typeId')} "
                   f"next {by_name[STOP_STEP].get('nextId')}")
    if by_name[CLEAR_STEP].get('nextId') != by_name[STOP_STEP]['id']:
        out.append(f'G: {CLEAR_STEP!r} does not run into {STOP_STEP!r}')
    if by_name[TICK_STEP].get('nextId') != by_name[CLEAR_STEP]['id']:
        out.append(f'G: {TICK_STEP!r} does not run into {CLEAR_STEP!r}')
    for node_name, want in ((TICK_STEP, ('1', False)), (UNTICK_STEP, ('0', False)),
                            (CLEAR_STEP, ('', True)),
                            (WRITE_KEY_STEP, (f"${by_name[KEY_STEP]['id']}-{STRING_FX}$", False))):
        s = S.step_state_of(pid, by_name[node_name]['id'])
        field = f[DUPLICATE]['controlId'] if node_name in (TICK_STEP, UNTICK_STEP) else f[TAX_KEY]['controlId']
        if s['selectNodeId'] != start or s['isException'] or \
                s['fields'] != [(field, '', '', want[1], want[0])]:
            out.append(f'G / {node_name}: {s}')
    cfg = read('workflow', 'config-get', pid)
    if cfg.get('triggerType') != NO_OTHER_WORKFLOWS:
        out.append(f"G is not quiet: triggerType {cfg.get('triggerType')}")
    info = read('workflow', 'get', pid)
    if not info.get('enabled') or info.get('publishStatus') != 2:
        out.append(f"G enabled={info.get('enabled')} publishStatus={info.get('publishStatus')}")
    return out


def rollup_differences():
    """The two roll-ups read back: the seven steps in order, the three formulas and step 5's four writes."""
    x = rollup_ids()
    out = []
    for name in ROLLUPS:
        pid = hap.ids()['workflows']['Invoice Lines: ' + name]
        proc = hap.run('workflow', 'node', 'list', pid)
        by_name = {n['name']: n for n in proc['flowNodeMap'].values()}
        chain, node = [], proc['flowNodeMap'][proc['startEventId']].get('nextId')
        while node and node in proc['flowNodeMap']:
            chain.append(proc['flowNodeMap'][node]['name'])
            node = proc['flowNodeMap'][node].get('nextId')
        want_chain = [GET_INVOICE, SUM_STEP, SUM_TOTAL_STEP, UNTAXED_STEP, TAX_STEP, TOTAL_STEP, WRITE_STEP]
        if chain != want_chain:
            out.append(f'{name}: the steps run {chain}')
            continue
        sums, totals = by_name[SUM_STEP]['id'], by_name[SUM_TOTAL_STEP]['id']
        want_total_state = dict(actionId=WORKSHEET_TOTAL, appId=x['lines'], reportControlId=x['line_total'],
                                reportType=3,
                                filters=[(c.get('filedId'), str(c.get('conditionId')),
                                          [(v.get('nodeId') or '', v.get('controlId') or '',
                                            (v.get('value') or {}).get('key')
                                            if isinstance(v.get('value'), dict) else '')
                                           for v in c.get('conditionValues') or []])
                                         for group in rollup_filter(x, totals, by_name[GET_INVOICE]['id'])
                                         for c in group])
        if total_state(pid, totals) != want_total_state:
            out.append(f'{name} / {SUM_TOTAL_STEP}: {total_state(pid, totals)} != {want_total_state}')
        for node_name, expression in ((UNTAXED_STEP, f'${sums}-{NUMBER_FX}$+0'),
                                      (TAX_STEP, f'${totals}-{NUMBER_FX}$-${sums}-{NUMBER_FX}$'),
                                      (TOTAL_STEP, f'${totals}-{NUMBER_FX}$+0')):
            d = node_get(pid, by_name[node_name]['id'])
            if (d.get('formulaValue'), d.get('number'), d.get('nullZero')) != (expression, MONEY_DOT, True):
                out.append(f"{name} / {node_name}: {d.get('formulaValue')!r} number {d.get('number')} "
                           f"nullZero {d.get('nullZero')}, want {expression!r} / {MONEY_DOT} / True")
        fields = [from_formula(x['untaxed'], by_name[UNTAXED_STEP]['id']),
                  from_formula(x['tax'], by_name[TAX_STEP]['id']),
                  from_formula(x['total'], by_name[TOTAL_STEP]['id']),
                  from_formula(x['due'], by_name[TOTAL_STEP]['id'])]
        want = dict(selectNodeId=by_name[GET_INVOICE]['id'], appId=x['invoices'], isException=False,
                    fields=sorted((f['fieldId'], f['nodeId'], f['fieldValueId']) for f in fields))
        if write_state(pid, by_name[WRITE_STEP]['id']) != want:
            out.append(f'{name} / {WRITE_STEP}: {write_state(pid, by_name[WRITE_STEP]["id"])} != {want}')
        info = read('workflow', 'get', pid)
        if not info.get('enabled') or info.get('publishStatus') != 2:
            out.append(f"{name}: enabled={info.get('enabled')} publishStatus={info.get('publishStatus')}")
    return out


def other_worksheet_differences():
    """Everything this bundle put on the other three worksheets."""
    import accounts as A
    import invlines as L
    out = []
    pctrls = hap.controls(wid(PRODUCTS))
    pf = hap.by_name(pctrls)
    for name, diff in product_layout_differences(pctrls).items():
        out.append(f'{PRODUCTS} / {name}: {json.dumps(diff, ensure_ascii=False, default=str)[:300]}')
    for name, (alias, use, size) in PRODUCT_TAXES.items():
        c = pf.get(name)
        if not c:
            out.append(f'{PRODUCTS} has no {name}')
        elif (c.get('dataSource'), c.get('enumDefault'), c.get('alias')) != (ws(), 2, alias):
            out.append(f"{PRODUCTS} / {name}: ds {c.get('dataSource')} multi {c.get('enumDefault')} "
                       f"alias {c.get('alias')!r}")
    af = hap.by_name(hap.controls(wid(ACCOUNTS)))
    c = af.get(DEFAULT_TAXES)
    if not c:
        out.append(f'{ACCOUNTS} has no {DEFAULT_TAXES}')
    elif (c.get('dataSource'), c.get('enumDefault'), c.get('alias'),
          (c.get('row'), c.get('col'), c.get('size'))) != (ws(), 2, 'tax_ids', A.PLACE[DEFAULT_TAXES]):
        out.append(f"{ACCOUNTS} / {DEFAULT_TAXES}: ds {c.get('dataSource')} multi {c.get('enumDefault')} "
                   f"at {(c.get('row'), c.get('col'), c.get('size'))}")
    lf = hap.by_name(hap.controls(L.ws()))
    for name, kind in ((LINE_TAXES, RELATION), (LINE_RATE, ROLLUP), (LINE_TOTAL, FORMULA_NUMBER)):
        c = lf.get(name)
        if not c or c.get('type') != kind:
            out.append(f"{LINES} / {name}: type {c and c.get('type')}, want {kind}")
    if lf.get(LINE_TAXES, {}).get('dataSource') != ws() or lf.get(LINE_TAXES, {}).get('enumDefault') != 2:
        out.append(f"{LINES} / {LINE_TAXES}: ds {lf.get(LINE_TAXES, {}).get('dataSource')} "
                   f"multi {lf.get(LINE_TAXES, {}).get('enumDefault')}")
    if (lf.get(LINE_TAXES, {}).get('advancedSetting') or {}).get('filters'):
        out.append(f'{LINES} / {LINE_TAXES} carries a picker filter; §1 says unfiltered')
    rate = lf.get(LINE_RATE, {})
    want_rate = (f"${lf[LINE_TAXES]['controlId']}$", fields_of(ws())[AMOUNT]['controlId'], 5, '001')
    got_rate = (rate.get('dataSource'), rate.get('sourceControlId'), rate.get('enumDefault'),
                rate.get('fieldPermission'))
    if got_rate != want_rate:
        out.append(f'{LINES} / {LINE_RATE}: {got_rate} != {want_rate} (through / of / sum / hidden+read-only)')
    if picker_state((rate.get('advancedSetting') or {}).get('filters')) != picker_state(
            json.dumps(rate_filter(fields_of(ws())))):
        out.append(f'{LINES} / {LINE_RATE} filter: {(rate.get("advancedSetting") or {}).get("filters")}')
    want_expr = total_expression(lf)
    if lf.get(LINE_TOTAL, {}).get('dataSource') != want_expr:
        out.append(f"{LINES} / {LINE_TOTAL}: {lf.get(LINE_TOTAL, {}).get('dataSource')!r} != {want_expr!r}")
    return out


def step_check():
    """The whole bundle read back against §1; non-zero on a difference."""
    ctrls = hap.controls(ws())
    f = hap.by_name(ctrls)
    names = {c['controlId']: c['controlName'] for c in ctrls}
    problems = []
    if set(f) != set(PLACE):
        problems.append(f'controls {sorted(set(f) ^ set(PLACE))}')
    problems += [f'{n}: {d}' for n, d in layout_differences(ctrls).items()]
    if f.get(TITLE, {}).get('attribute') != 1:
        problems.append('the title field is '
                        f'{next((c["controlName"] for c in ctrls if c.get("attribute") == 1), None)!r}')
    for name, kind in ((NAME, TEXT), (TYPE, DROPDOWN), (SCOPE, DROPDOWN), (COMPUTATION, DROPDOWN),
                       (AMOUNT, NUMBER), (FORMULA, TEXT), (DESCRIPTION, TEXT), (LABEL, TEXT),
                       (GROUP, DROPDOWN), (COUNTRY, RELATION), (PRICE_INC, DROPDOWN), (AFFECT, SWITCH),
                       (AFFECTED, SWITCH), (ACTIVE, SWITCH), (SEQUENCE, NUMBER), (NOTES, RICH_TEXT),
                       (ADVANCED_DIVIDER, DIVIDER), (DUPLICATE, SWITCH), (TAX_KEY, TEXT)):
        if f.get(name, {}).get('type') != kind:
            problems.append(f'{name} is type {f.get(name, {}).get("type")}, want {kind}')
    if not f.get(TAX_KEY, {}).get('unique'):
        problems.append(f'{TAX_KEY} does not carry No duplicates')
    if f.get(NAME, {}).get('unique'):
        problems.append(f'{NAME} carries No duplicates; §1 says it must not')
    if f.get(COUNTRY, {}).get('dataSource') != wid(COUNTRIES):
        problems.append(f'{COUNTRY} points at {f.get(COUNTRY, {}).get("dataSource")}')
    left, live = rule_differences()
    if left:
        problems.append(f'rules {json.dumps(left, ensure_ascii=False, default=str)[:400]}')
    if set(live) != set(RULES):
        problems.append(f'rules {sorted(live)}')
    views = [v['name'] for v in hap.listing('worksheet', 'view', 'list', ws(), '-a', APP)]
    if views != [VIEW, ARCHIVED, DUP_VIEW]:
        problems.append(f'views {views}, want {[VIEW, ARCHIVED, DUP_VIEW]}')
    for name, (got, want) in view_differences((VIEW, ARCHIVED, DUP_VIEW)).items():
        problems.append(f'view {name}: {got} != {want}')
    problems += button_differences()
    problems += g_differences(f)
    problems += other_worksheet_differences()
    problems += rollup_differences()
    import roles
    if roles.step_check():
        problems.append('roles differ — see roles.py check')
    print('  check: ' + ('OK — the nineteen controls with their places, options, defaults and permissions, Tax '
                         'Name the title, the six rules, the three views in order, the Archive/Unarchive pair, '
                         'workflow G published and quiet with its duplicate path ticking, clearing and ending '
                         'in an abort, the four business roles carrying Taxes at Chart of Accounts\' cell, the '
                         'two picker-filtered relations on Products, Default Taxes on Chart of Accounts, '
                         'Taxes / Tax rate / Total on Invoice Lines, and both roll-ups writing Tax'
                         if not problems else 'DIFFERENCES\n    ' + '\n    '.join(problems)))
    return len(problems)


def step_order():
    """Each view's records in the order the view returns them."""
    f = fields_of(ws())
    name, active = f[NAME]['controlId'], f[ACTIVE]['controlId']
    for v in hap.listing('worksheet', 'view', 'list', ws(), '-a', APP):
        res = hap.run('worksheet', 'record', 'list', ws(), '-a', APP, '-n', '40', '--view-id', v['viewId'],
                      '--use-field-id-as-key')
        d = res.get('data', res) if isinstance(res, dict) else res
        listed_rows = (d.get('rows') if isinstance(d, dict) else d) or []
        print(f"  {v['name']} ({len(listed_rows)}): " +
              ', '.join(f"{r.get(name)}{'' if flag(r.get(active)) else ' (archived)'}" for r in listed_rows[:20]))


# ── the remark block on Invoices ───────────────────────────────────────────
#
# 06 wrote it while the lines and the taxes were both still to come, so it told the reader that the four amounts
# were "read-only figures seeded from the tenant" and that "Taxes themselves need the Taxes bundle". 07 made three
# of them roll-ups and this bundle made the fourth, so both sentences are now false. Found in the browser on the
# UI test, 18 Sep 2026 (13-taxes.md §3). Rewritten again on 22 Sep 2026 for the app's users (owner's rule): the
# text is the same as `invoices.py` HTML[NOTE_LINES], and the one this step wrote on 18 Sep is kept word for word
# at the foot of 06-invoices.md.

INVOICES_WS = '6aa90facf363582dd37a62f7'   # the worksheet id; INVOICES above is its name
LINES_NOTE = '6aa9f846e54d2a34fa4dfedc'
LINES_NOTE_TEXT = ('<p>Add the products, sections and notes of this document in the table below. Untaxed Amount, '
                   'Tax, Total and Amount Due are worked out from these lines.</p>')


def step_note():
    """Bring 06's Invoice Lines remark block up to date. Idempotent: a second run saves nothing."""
    ctrls, version = C.controls_with_version(INVOICES_WS)
    note = next((c for c in ctrls if c['controlId'] == LINES_NOTE), None)
    if note is None:
        print(f'  the Invoice Lines remark block {LINES_NOTE} is not on Invoices; nothing written')
        return 1
    if note.get('dataSource') == LINES_NOTE_TEXT:
        print('  the remark block on Invoices already reads as specified; nothing saved')
        return 0
    hap.backup('invoices_lines_note_pre_taxes', note)
    note['dataSource'] = LINES_NOTE_TEXT
    C.save_controls(INVOICES_WS, ctrls, version=version)
    again, _ = C.controls_with_version(INVOICES_WS)
    back = next(c for c in again if c['controlId'] == LINES_NOTE)
    if back.get('dataSource') != LINES_NOTE_TEXT:
        print('  the remark block did not read back as sent')
        return 1
    print('  the remark block on Invoices rewritten: the four amounts are roll-ups, and Tax is no longer seeded')
    return 0


def step_all():
    for name in ('create', 'fields', 'rules', 'views', 'dupview', 'buttons', 'automations', 'roles', 'seed',
                 'products', 'accounts', 'lines', 'rollup', 'amounts', 'note'):
        print(f'\n── {name} ' + '─' * 60)
        STEPS[name]()
    print('\n── check ' + '─' * 60)
    return step_check()


def show():
    C.show(ws())


STEPS = {
    'create': step_create,
    'fields': step_fields,
    'rules': step_rules,
    'views': step_views,
    'dupview': step_dupview,
    'buttons': step_buttons,
    'automations': step_automations,
    'roles': step_roles,
    'seed': step_seed,
    'products': step_products,
    'accounts': step_accounts,
    'lines': step_lines,
    'rollup': step_rollup,
    'amounts': step_amounts,
    'note': step_note,
    'all': step_all,
    'verify': step_verify,
    'check': step_check,
    'selfcheck': step_selfcheck,
    'measure': step_measure,
    'keys': step_keys,
    'order': step_order,
    'untouched': step_untouched,
    'show': show,
}

if __name__ == '__main__':
    step = sys.argv[1] if len(sys.argv) > 1 else 'check'
    if step not in STEPS:
        raise SystemExit(f"Unknown step {step!r}; choose from {', '.join(STEPS)}")
    result = STEPS[step](*sys.argv[2:])
    if step in ('verify', 'check', 'all', 'selfcheck', 'measure', 'keys', 'roles', 'lines', 'products',
                'accounts', 'rollup', 'amounts', 'seed', 'note') and result:
        sys.exit(1)
