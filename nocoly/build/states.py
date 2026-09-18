#!/usr/bin/env python3
"""Build the States worksheet (Odoo res.country.state, as on casimir.odoo.com saas~19.4) in ERP Master.

Bundle 5 of the six that join Phase 1. It adds the worksheet to the **Contacts** menu group after Countries,
seeds all 2 102 states, gives **Countries** the reverse list Odoo shows at the foot of its form, and then
**replaces Contacts' State text with a relation**: create it beside the stand-in, carry the eight contacts'
values across, read them back, re-point the two address workflows and only then delete the text control
(owner-approved, `DECISIONS.md` 17 Sep 2026). Last it builds Odoo's two address onchanges as workflows E and F
on Contacts, both **quiet**.

Requirements: nocoly/worksheets/12-states.md. Generic helpers: common.py. Run from the repo root with the
CLI's interpreter:

    ~/.hap-venv/bin/python nocoly/build/states.py create    # 0. the worksheet in the menu group Contacts,
                                                            #    after Countries
    ~/.hap-venv/bin/python nocoly/build/states.py fields    # 1. State Name / State Code / Country in one save
                                                            #    of the empty worksheet, then the hidden Country
                                                            #    Code lookup, the Display Name formula and the
                                                            #    hidden State key, one append each
    ~/.hap-venv/bin/python nocoly/build/states.py reverse   # 2. Countries gains **States** — the reverse of the
                                                            #    two-way relation — and its remark block's last
                                                            #    line is rewritten
    ~/.hap-venv/bin/python nocoly/build/states.py views     # 3. States — the only view: three columns, State
                                                            #    Code A→Z then Country, quick filter Country
    ~/.hap-venv/bin/python nocoly/build/states.py roles     # 4. roles.py's create step, which now carries this
                                                            #    worksheet into the four business roles
    ~/.hap-venv/bin/python nocoly/build/states.py unique    # 5. §1's Rules question: HAP takes *No duplicates*
                                                            #    on a formula control and never applies it —
                                                            #    `selfcheck` is what proves the second half
    ~/.hap-venv/bin/python nocoly/build/states.py seed      # 6. the 2 102 states, every one read back, and §1's
                                                            #    digests
    ~/.hap-venv/bin/python nocoly/build/states.py contacts  # 7. the relation State on Contacts, in the text
                                                            #    stand-in's cell (row 8, right half)
    ~/.hap-venv/bin/python nocoly/build/states.py carry     # 8. the eight contacts' State text onto the
                                                            #    relation, read back
    ~/.hap-venv/bin/python nocoly/build/states.py retire    # 9. re-point the two address automations, delete the
                                                            #    text control, scan for the dead id
    ~/.hap-venv/bin/python nocoly/build/states.py automations # 10. workflows E and F on Contacts, both quiet
    ~/.hap-venv/bin/python nocoly/build/states.py all       # every step above, then check

    ~/.hap-venv/bin/python nocoly/build/states.py verify    # the 2 102 live states against the extract, with
                                                            #    §1's digests
    ~/.hap-venv/bin/python nocoly/build/states.py check     # controls, permissions, view, roles, the reverse on
                                                            #    Countries, everything on Contacts and E and F
    ~/.hap-venv/bin/python nocoly/build/states.py selfcheck # E and F driven through the CLI on a TEST contact
    ~/.hap-venv/bin/python nocoly/build/states.py order     # the view's records in the view's own order
    ~/.hap-venv/bin/python nocoly/build/states.py state MY-10  # stored values by State Code
    ~/.hap-venv/bin/python nocoly/build/states.py deadrefs  # every view, rule, button, control and workflow node
                                                            #    scanned for the deleted control's id
    ~/.hap-venv/bin/python nocoly/build/states.py untouched # the other worksheets: control count and digest
    ~/.hap-venv/bin/python nocoly/build/states.py show      # the live control list

Every step reads the live state first and is safe to re-run; a second run writes nothing. **The one deletion is
Contacts' text control `6aa8a452f363582dd37a50e5`**, and `retire` refuses to make it until every contact's value
reads back from the relation. Nothing else is deleted and the Sales app is never written to.

The order matters: `fields` before `reverse` (the reverse carries the id the relation reserved), `seed` before
`carry` (the relation needs Selangor and Sarawak to point at), `carry` before `retire`, and `retire` before
`automations` — E and F resolve "State" by name, and until the stand-in is gone that name is ambiguous.

Records are created through the CLI's own session — `hap worksheet record batch-create` is one `AddWorksheetRow`
per row *and* one GetWorksheetControls per row, which is 4 204 HTTP calls for this seed; `batch` below is the
same encoder and the same write with the control list read once. Reads go the same way (`GetFilterRows` /
`GetRowDetail`), because 2 102 `record get` processes would be forty minutes.

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
SECTION = 'Contacts'
SECTION_ID = '6aa8a3a93e5e4ad5b852a6d3'
WORKSHEET = 'States'
KEY = WORKSHEET + ': '                            # ids.json key prefix for everything this worksheet owns
CON_KEY = 'Contacts: '
COUNTRIES = 'Countries'
ALIAS = 'res_country_state'
HERE = Path(__file__).resolve().parent
DATA = HERE.parent / 'data' / 'casimir-states.json'
OTHERS = ('Contacts', 'Countries', 'Units & Packagings', 'Products', 'Product Variants', 'Product Categories',
          'Chart of Accounts', 'Journals', 'Payment Terms', 'Payment Term Lines', 'Invoices', 'Invoice Lines')

# Contacts' text State — the one approved deletion of this bundle (DECISIONS.md, 17 Sep 2026)
TEXT_STANDIN = '6aa8a452f363582dd37a50e5'

SWITCH, TEXT, NUMBER, RELATION, LOOKUP, FORMULA, NOTE = 36, 2, 6, 29, 30, 53, 10010


def ws():
    return hap.ids()['worksheets'][WORKSHEET]


def con_ws():
    return hap.ids()['worksheets']['Contacts']


def cty_ws():
    return hap.ids()['worksheets'][COUNTRIES]


def refuse_sales():
    if APP == SALES_APP:
        sys.exit('ids.json points at the Sales app — refusing to write')


def session():
    from hap_cli.core.session import Session
    return Session.load(None)


def data():
    """The 2 102 states of the 19.4 extract, by "<country code>|<state code>" — Odoo's own natural key, the pair
    its `unique(country_id, code)` constraint is on. `xmlid` and `country_name` are in the file and are not
    built."""
    return {f"{s['country_code']}|{s['code']}": s for s in json.loads(DATA.read_text(encoding='utf-8'))}


# ── the form ────────────────────────────────────────────────────────────────

NAME = 'State Name'
CODE = 'State Code'
COUNTRY = 'Country'
DISPLAY = 'Display Name'
COUNTRY_CODE = 'Country Code'                     # the hidden stored lookup Display Name is built on
STATE_KEY = 'State key'                           # §1 › Rules: Odoo's unique(country_id, code) as one field

# §1's form layout: State Name | State Code · Country | Display Name, with the two hidden controls under them
# (a hidden control still needs a place, as 08's Parent Complete Name has one). HAP puts the title field at the
# top of the record, so Display Name shows twice there, as Complete Name does on a category.
PLACE = {
    NAME: (0, 0, 6), CODE: (0, 1, 6),
    COUNTRY: (1, 0, 6), DISPLAY: (1, 1, 6),
    COUNTRY_CODE: (2, 0, 6), STATE_KEY: (2, 1, 6),
}
HINTS = {}                                        # Odoo's state form has no placeholder on any field
DESC = {  # Odoo's field help where it has one (res_country.py); how a helper is computed otherwise
    NAME: 'Administrative divisions of a country. E.g. Fed. State, Department, Canton',
    CODE: 'The state code.',
    DISPLAY: 'How this state appears in lists and pickers: the State Name and the country\'s code in brackets '
             '— Odoo display_name, "Selangor (MY)".',
    COUNTRY_CODE: "The Country's Country Code (a stored lookup), which Display Name is built on.",
    STATE_KEY: "Odoo's constraint unique(country_id, code) as one field: the country's code, a bar and the "
               'State Code. Hidden, and it exists only to carry No duplicates.',
}
REQUIRED = {NAME, CODE, COUNTRY}                  # Odoo: all three required on the model
UNIQUE = {STATE_KEY}                              # §1 › Rules; nothing else, and *not* State Code
# A hidden field never shows as a table column, so Display Name — the title — is read-only and hidden on create
# ("100") rather than hidden, as 01's, 04's, 08's and 09's are. The two helpers are hidden outright.
PERMISSION = {DISPLAY: '100', COUNTRY_CODE: '011', STATE_KEY: '011'}
ALIASES = {NAME: 'name', CODE: 'code', COUNTRY: 'country_id', DISPLAY: 'display_name',
           COUNTRY_CODE: 'country_code',          # country_code is a helper, not a field of res.country.state
           STATE_KEY: 'state_key'}                # and so is state_key
ADVANCED = {  # the advancedSetting keys this script owns
    COUNTRY: {'bidirectional': '1', 'showtype': '3'},        # two-way; 3 = a dropdown
    DISPLAY: {'analysislink': '1', 'sorttype': 'en'},
    STATE_KEY: {'analysislink': '1', 'sorttype': 'en'},
}

# On Countries: the reverse of Country, the list Odoo draws at the foot of the country form.
REVERSE = 'States'
REVERSE_ALIAS = 'state_ids'
REVERSE_PLACE = (4, 0, 12)                        # under the remark block; a showtype-2 list renders as a tab
REVERSE_PERMISSION = '101'                        # read-only: a state is given its country on the state
REVERSE_COLUMNS = (NAME, CODE)                    # exactly Odoo's two columns there
REVERSE_DESC = ('The states of this country — Odoo state_ids, the reverse of Country on States. Set the country '
                'on the state.')
# Countries' remark block, whose last line §1 rewrites: the States are here now.
NOTE_NAME = 'Country form note'
NOTE_HTML = ("<p><strong>Also on Odoo's country form:</strong> the <strong>Currency</strong>, the country's "
             '<strong>flag</strong>, and — only in developer mode — the three <strong>Advanced Address '
             'Formatting</strong> fields: Input View, Layout in Reports and Customer Name Position. Odoo also '
             'keeps <strong>Country Groups</strong> on the model, on no view of the country.</p>'
             '<p>The <strong>States</strong> Odoo lists at the foot of the form are here, at the foot of this '
             'one; the currency, the flag and the address layout are not in Phase 1.</p>')


def function_source(expression):
    """dataSource of a function formula (type 53), as contacts.py and prodcat.py write it."""
    return json.dumps({'type': 'mdfunction', 'expression': expression, 'status': 1}, ensure_ascii=False)


def display_expression(f):
    """Odoo _compute_display_name on res.country.state: f"{name} ({country_id.code})".

    The country's code is read through the stored lookup Country Code, the way 08's Complete Name reads Parent
    Complete Name. A number formula has no CONCAT of text, so this is a function formula."""
    return f"CONCAT(${f[NAME]['controlId']}$,\" (\",${f[COUNTRY_CODE]['controlId']}$,\")\")"


def key_expression(f):
    """§1 › Rules: Odoo's `unique(country_id, code)` reduced to one value — the country's code, a bar and the
    state's code. The bar cannot occur in either half, so two different pairs cannot collide."""
    return f"CONCAT(${f[COUNTRY_CODE]['controlId']}$,\"|\",${f[CODE]['controlId']}$)"


EXPRESSION = {DISPLAY: display_expression, STATE_KEY: key_expression}


def desired(c):
    """The attributes `fields` owns on control c, as they should read back."""
    name = c['controlName']
    row, col, size = PLACE[name]
    want = {'row': row, 'col': col, 'size': size, 'sectionId': '', 'alias': ALIASES[name],
            'hint': HINTS.get(name, ''), 'desc': DESC.get(name, ''), 'required': name in REQUIRED,
            'unique': name in UNIQUE, 'fieldPermission': PERMISSION.get(name, '111'),
            'attribute': 1 if name == DISPLAY else 0}
    return want


def layout_differences(ctrls):
    out = {}
    for c in ctrls:
        if c['controlName'] not in PLACE:
            continue
        diff = {k: (c.get(k), v) for k, v in desired(c).items()
                if (c.get(k) or (0 if k == 'attribute' else '' if isinstance(v, str) else False)) != v}
        adv = c.get('advancedSetting') or {}
        diff.update({f'advancedSetting.{k}': (adv.get(k), v)
                     for k, v in (ADVANCED.get(c['controlName']) or {}).items() if adv.get(k) != v})
        if c['controlName'] in EXPRESSION:
            f = hap.by_name(ctrls)
            want = EXPRESSION[c['controlName']](f)
            got = json.loads(c.get('dataSource') or '{}').get('expression')
            if got != want:
                diff['expression'] = (got, want)
        if diff:
            out[c['controlName']] = diff
    return out


# ── the other worksheets, compared control by control ───────────────────────

SIGNATURE = ('controlName', 'type', 'alias', 'row', 'col', 'size', 'sectionId', 'required', 'attribute', 'unique',
             'fieldPermission', 'dataSource', 'sourceControlId', 'showControls', 'advancedSetting', 'desc', 'hint')


def control_state(c):
    import accounts                                # its comparable form: JSON settings parsed, defaults by id
    return accounts.control_state(c)


def snap(names=OTHERS):
    """{worksheet: {controlId: comparable control}} for the named worksheets (by ids.json name)."""
    return {name: {c['controlId']: control_state(c) for c in hap.controls(hap.ids()['worksheets'][name])}
            for name in names}


def expect(before, label, changed=None, new=None, gone=None):
    """Read the worksheets of `before` again and stop unless the only differences are those named
    (countries.expect, the same comparison)."""
    import countries
    return countries.expect(before, label, changed=changed, new=new, gone=gone)


def signature(worksheet_id):
    return sorted(json.dumps([c['controlId']] + [c.get(k) for k in SIGNATURE], sort_keys=True, ensure_ascii=False)
                  for c in hap.controls(worksheet_id))


def step_untouched():
    """Control count and digest of every other worksheet — run before and after a build."""
    for name in OTHERS:
        sig = signature(hap.ids()['worksheets'][name])
        print(f'  {name:<20} {len(sig):>2} controls  sha256:'
              f'{hashlib.sha256("".join(sig).encode()).hexdigest()[:16]}')


# ── guard ───────────────────────────────────────────────────────────────────

def guard(fresh=False):
    """Stop unless the profile reaches ERP Master › Contacts › States and the worksheet holds only this
    script's work. `fresh` allows the three stock controls of a brand-new worksheet."""
    refuse_sales()
    who = hap.run('auth', 'whoami')
    app = hap.run('app', 'info', '-a', APP).get('data', {})
    worksheet = hap.ids().get('worksheets', {}).get(WORKSHEET)
    section = next((s for s in app.get('sections', []) if any(i['id'] == worksheet for i in s['items'])), None)
    if app.get('name') != 'ERP Master' or not section or section['name'] != SECTION:
        sys.exit(f"profile {who.get('profile')!r} does not reach ERP Master › {SECTION} › {WORKSHEET}")
    problems, ctrls = [], hap.controls(worksheet)
    stock = {'Name', 'Description', 'Attachment', '名称', '描述', '附件'}
    known = set(PLACE) | (stock if fresh else set())
    problems += [f"unknown control {c['controlName']!r} ({c['controlId']})" for c in ctrls
                 if c['controlName'] not in known]
    if len(hap.by_name(ctrls)) != len(ctrls):
        problems.append(f'two controls share a name: {sorted(c["controlName"] for c in ctrls)}')
    views = {v['name'] for v in hap.listing('worksheet', 'view', 'list', worksheet, '-a', APP)}
    problems += [f'unknown view {n!r}' for n in views - {VIEW, 'All', '全部'}]
    buttons = {b['name'] for b in hap.listing('worksheet', 'custom-actions', worksheet)}
    problems += [f'unknown button {n!r}' for n in buttons]          # §1: this worksheet has no buttons
    rules = {r['name'] for r in hap.listing('worksheet', 'rules', worksheet)}
    problems += [f'unknown rule {n!r}' for n in rules]              # §1: and no rules
    if problems:
        sys.exit(f"{WORKSHEET} differs from this script's work — stopping:\n  " + '\n  '.join(problems))
    print(f"  guard: profile {os.environ.get('HAP_PROFILE') or who.get('profile')!r}, ERP Master › {SECTION} › "
          f"{WORKSHEET}, {len(ctrls)} controls, {len(rules)} rules, {len(buttons)} buttons, views {sorted(views)}")
    return ctrls


# ── 0 · the worksheet ───────────────────────────────────────────────────────

REMARK = ('Odoo res.country.state: the second half of an address — 2 102 states in 74 of the 251 countries, '
          "each with its code and the country it belongs to")
ICON = 'sys_9_2_map'                              # `hap icon search 地图`; a name outside the catalogue answers
                                                  # 400 and leaves a broken icon URL for ever


def step_create():
    """The worksheet in the Contacts menu group, after Countries.

    The menu group is looked up by its **id**, never through `common.ensure_section`: that helper re-sorts the
    app's groups, and ERP Master carries a CRM group another administrator is building in
    (`countries.step_create`, 18 Sep). `worksheet create --section-id` appends, which is where §1 wants it."""
    refuse_sales()
    sections = C.app_info(APP)['sections']
    section = next((s for s in sections if s['id'] == SECTION_ID), None)
    if not section or section['name'] != SECTION:
        sys.exit(f'menu group {SECTION_ID} is {section and section["name"]!r}, not {SECTION!r}')
    C.remember('sections', SECTION, SECTION_ID)
    wid = C.ensure_worksheet(APP, SECTION_ID, WORKSHEET, alias=ALIAS, icon=ICON, remark=REMARK)
    C.remember('worksheets', WORKSHEET, wid)
    for s in C.app_info(APP)['sections']:
        print(f"  {s['name']:<10} {s['id']}  {[(i['name'], i['id'], i.get('alias')) for i in s['items']]}")


# ── 1 · the controls ────────────────────────────────────────────────────────

def step_fields():
    """The five controls, in three passes, the way 01's Display Name was built.

    1. **One full save of the empty worksheet** — State Name (reusing the stock title's id, so nothing is
       deleted that is not meant to be), State Code and the two-way Country relation.
    2. The **stored lookup Country Code**, appended with `add-fields` and re-saved so the server mints its id.
    3. The **Display Name formula** over that minted id, the same way. A formula saved under a client-side id
       computes nothing (BUILDING.md), so each of the two is appended on its own and read back before the next.

    Then one placing save: rows, sizes, aliases, descriptions, permissions and the title field. Display Name is
    the only control carrying `attribute` 1 in that save, so the title is not the coin toss BUILDING.md warns of.
    """
    existing = guard(fresh=True)
    f = hap.by_name(existing)
    if not any(n in f for n in PLACE) and len(existing) <= 3:
        hap.backup('states_controls_pre_fields', existing)
        name = C.control('TEXT', NAME, PLACE[NAME], alias=ALIASES[NAME], hint='', desc=DESC[NAME], required=True,
                         is_title=True)
        title = next((c for c in existing if c.get('attribute') == 1), None)
        if title:
            name['controlId'] = title['controlId']
        code = C.control('TEXT', CODE, PLACE[CODE], alias=ALIASES[CODE], hint='', desc=DESC[CODE], required=True)
        country = C.control('RELATE_SHEET', COUNTRY, PLACE[COUNTRY], alias=ALIASES[COUNTRY], hint='', desc='',
                            required=True, data_source=cty_ws(), multi=False,
                            advanced_setting=dict(ADVANCED[COUNTRY]))
        before = snap()
        C.save_controls(ws(), [name, code, country])
        expect(before, f'{WORKSHEET}: the first save (no other worksheet may change)')
        print(f'  first save: {[NAME, CODE, COUNTRY]} (the stock title id {title and title["controlId"]} reused '
              f'for {NAME})')
    f = fields_of(ws())
    if COUNTRY not in f:
        sys.exit(f'{COUNTRY} is missing — the first save did not happen')
    if COUNTRY_CODE not in f:
        cty = hap.by_name(hap.controls(cty_ws()))
        before = snap()
        C.add_fields(ws(), [C.control('SHEET_FIELD', COUNTRY_CODE, PLACE[COUNTRY_CODE],
                                      alias=ALIASES[COUNTRY_CODE], hint='', desc=DESC[COUNTRY_CODE],
                                      data_source=f[COUNTRY]['controlId'],
                                      source_control_id=cty['Country Code']['controlId'],
                                      extra={'strDefault': '00'})])         # '00' = stored
        expect(before, f'{WORKSHEET}: the {COUNTRY_CODE} lookup added', new={WORKSHEET: {COUNTRY_CODE}})
        print(f'  added: {COUNTRY_CODE} (a stored lookup of {COUNTRIES} / Country Code through {COUNTRY})')
        f = fields_of(ws())
    if DISPLAY not in f:
        before = snap()
        C.add_fields(ws(), [C.control('FORMULA_FUNC', DISPLAY, PLACE[DISPLAY], alias=ALIASES[DISPLAY], hint='',
                                      desc=DESC[DISPLAY], advanced_setting=dict(ADVANCED[DISPLAY]),
                                      extra={'enumDefault2': 2,                       # 2 = a text result
                                             'dataSource': function_source(display_expression(f))})])
        expect(before, f'{WORKSHEET}: the {DISPLAY} formula added', new={WORKSHEET: {DISPLAY}})
        print(f'  added: {DISPLAY}')
        f = fields_of(ws())
    if STATE_KEY not in f:
        # §1 › Rules, answered by `unique`: HAP does take *No duplicates* on a function formula, so Odoo's
        # `unique(country_id, code)` is built as one — the switch goes on in the placing save below, after the
        # formula has been minted and can compute.
        before = snap()
        C.add_fields(ws(), [C.control('FORMULA_FUNC', STATE_KEY, PLACE[STATE_KEY], alias=ALIASES[STATE_KEY],
                                      hint='', desc=DESC[STATE_KEY],
                                      advanced_setting=dict(ADVANCED[STATE_KEY]),
                                      extra={'enumDefault2': 2,
                                             'dataSource': function_source(key_expression(f))})])
        expect(before, f'{WORKSHEET}: the {STATE_KEY} formula added', new={WORKSHEET: {STATE_KEY}})
        print(f'  added: {STATE_KEY}')
    ctrls = hap.controls(ws())
    changed = layout_differences(ctrls)
    if changed:
        f = hap.by_name(ctrls)
        for c in ctrls:
            if c['controlName'] in changed:
                c.update(desired(c))
                c['advancedSetting'] = {**(c.get('advancedSetting') or {}), **(ADVANCED.get(c['controlName']) or {})}
                if c['controlName'] in EXPRESSION:
                    c['dataSource'] = function_source(EXPRESSION[c['controlName']](f))
        for c in ctrls:                            # the title moves in one save: 1 on Display Name, 0 elsewhere
            c['attribute'] = 1 if c['controlName'] == DISPLAY else 0
        before = snap()
        C.save_controls(ws(), ctrls)
        expect(before, f'{WORKSHEET}: places, permissions, descriptions and the title')
        print('  updated:', json.dumps(changed, ensure_ascii=False))
    left = layout_differences(hap.controls(ws()))
    if left:
        sys.exit(f'the controls read back with differences: {json.dumps(left, ensure_ascii=False)}')
    for c in hap.controls(ws()):
        C.remember('controls', KEY + c['controlName'], c['controlId'])
    C.show(ws())


def fields_of(worksheet_id):
    return hap.by_name(c for c in hap.controls(worksheet_id) if c['type'] != C.TAB)


# ── 2 · the reverse on Countries ────────────────────────────────────────────

def step_reverse():
    """Countries gains **States**, the reverse half of the two-way relation, and its remark block's last line is
    rewritten.

    A two-way Relation saved on another worksheet gets **no reverse at all**: the server only reserves the id in
    `sourceControlId` and leaves it dangling (BUILDING.md). The reverse is saved here the way `mount-subtable`
    completes HAP's 已有关联 handshake — same controlId, `sourceControlId` pointing back at the forward control,
    `sourceControlType` 6, `enumDefault` 2 — which is `prodcat.ensure_reverses`, the pattern that paired
    Products' Category with Product Categories' Products.

    `showtype` "2" makes it a **list at the foot of the country form** rather than a field in the grid, and a
    list with no `showControls` shows its row count over the words *No visible fields* — so the two columns
    Odoo shows there, State Name and State Code, are named by controlId."""
    guard()
    forward = fields_of(ws())[COUNTRY]
    reserved = forward.get('sourceControlId')
    if not reserved:
        sys.exit(f'{COUNTRY} has no sourceControlId — it was saved one-way; re-create it')
    f = fields_of(ws())
    columns = [f[n]['controlId'] for n in REVERSE_COLUMNS]
    ctrls, version = C.controls_with_version(cty_ws())
    reverse = next((c for c in ctrls if c['controlId'] == reserved), None)
    row, col, size = REVERSE_PLACE
    if not reverse:
        hap.backup('states_countries_controls_pre_reverse', ctrls)
        reverse = C.control('RELATE_SHEET', REVERSE, REVERSE_PLACE, alias=REVERSE_ALIAS, hint='',
                            desc=REVERSE_DESC, data_source=ws(), multi=True,
                            advanced_setting={'showtype': '2'})      # 2 = the related records as a list
        reverse.update(controlId=reserved, sourceControlId=forward['controlId'], sourceControlType=6,
                       showControls=columns, fieldPermission=REVERSE_PERMISSION)
        before = snap()
        C.save_controls(cty_ws(), ctrls + [reverse], version=version)
        expect(before, f'{COUNTRIES}: the reverse {REVERSE} saved', new={COUNTRIES: {REVERSE}})
        print(f"  {REVERSE}: reverse {reserved} saved, pairing with {COUNTRY} ({forward['controlId']})")
        ctrls, version = C.controls_with_version(cty_ws())
        reverse = next(c for c in ctrls if c['controlId'] == reserved)
    want = dict(controlName=REVERSE, alias=REVERSE_ALIAS, row=row, col=col, size=size, sectionId='', hint='',
                desc=REVERSE_DESC, required=False, fieldPermission=REVERSE_PERMISSION, showControls=columns,
                dataSource=ws(), sourceControlId=forward['controlId'])
    note = next((c for c in ctrls if c['controlName'] == NOTE_NAME), None)
    if not note:
        sys.exit(f'{COUNTRIES} has no remark block {NOTE_NAME!r}')
    changed = {k: (reverse.get(k), v) for k, v in want.items() if reverse.get(k) != v}
    if (reverse.get('advancedSetting') or {}).get('showtype') != '2':
        changed['advancedSetting.showtype'] = ((reverse.get('advancedSetting') or {}).get('showtype'), '2')
    if note.get('dataSource') != NOTE_HTML:
        changed[NOTE_NAME] = 'the last line rewritten'
    if changed:
        hap.backup('states_countries_controls_pre_reverse_layout', ctrls)
        reverse.update(want)
        reverse['advancedSetting'] = {**(reverse.get('advancedSetting') or {}), 'showtype': '2'}
        note['dataSource'] = NOTE_HTML
        before = snap()
        C.save_controls(cty_ws(), ctrls, version=version)
        expect(before, f'{COUNTRIES}: the reverse placed and the remark block rewritten',
               changed={COUNTRIES: {REVERSE: {'*'}, NOTE_NAME: {'dataSource'}}})
        print('  updated:', json.dumps(changed, ensure_ascii=False)[:400])
    reverse = next(c for c in hap.controls(cty_ws()) if c['controlId'] == reserved)
    if reverse.get('sourceControlId') != forward['controlId'] or reverse.get('enumDefault') != 2:
        sys.exit(f'{REVERSE} read back {json.dumps(reverse, ensure_ascii=False)[:300]}')
    C.remember('controls', f'{COUNTRIES}: {REVERSE}', reserved)
    names = {c['controlId']: c['controlName'] for c in hap.controls(ws())}
    print(f"  {COUNTRIES} / {REVERSE}: {reverse['controlId']} row={reverse.get('row')} size={reverse.get('size')} "
          f"alias={reverse.get('alias')!r} perm={reverse.get('fieldPermission')} "
          f"showtype={(reverse.get('advancedSetting') or {}).get('showtype')!r} "
          f"columns={[names.get(x, x) for x in reverse.get('showControls') or []]} "
          f"pair={reverse.get('sourceControlId')} enumDefault={reverse.get('enumDefault')}")


# ── 3 · the States view ─────────────────────────────────────────────────────

VIEW = 'States'
COLUMNS = (NAME, CODE, COUNTRY)                   # base.view_country_state_tree, the same three columns


def step_views():
    """States, the only view: every state, State Name · State Code · Country, sorted **State Code A→Z then
    Country** — Odoo's `_order = 'code, id'` with the country name standing in for the record id — and a
    **Country quick filter**, which is what Odoo's one group-by stands for.

    A view sorts on a Relation by the related record's title, and Countries' title is Country Name, so the
    second key reads as §1's "then Country Name". There is no Archived view: res.country.state has no active
    field.

    A quick filter named in `--view-spec` as a **bare control id** — the way `contacts.py` names its three —
    is stored with an empty `advancedSetting`, and HAP then draws it at its own defaults. Named as the spec
    adapter's object instead, `{fieldId, selectionType, displayType}` lowers to `allowitem` "2" (is any of)
    and `direction` "2" (a dropdown) — the shape Products' Category filter carries and the one already proved
    in the UI on a relation (BUILDING.md, 17 Sep) — and it is written identically on every run."""
    guard()
    f = fields_of(ws())
    columns = [f[n]['controlId'] for n in COLUMNS]
    spec = dict(viewType='table', tableFields=columns,
                quickFilters=[{'fieldId': f[COUNTRY]['controlId'], 'selectionType': 'multiple',
                               'displayType': 'dropdown'}])
    views = {VIEW: (spec, C.sort_spec([f[CODE], f[COUNTRY]]), columns)}
    for name, vid in C.upsert_views(ws(), APP, views, 'states_views_pre_views', default_view=VIEW).items():
        C.remember('views', KEY + name, vid)
    print('  order:', C.sort_views(ws(), APP, list(views)))
    C.print_views(ws(), APP)
    for v in hap.listing('worksheet', 'view', 'list', ws(), '-a', APP):
        info = C.view_info(ws(), APP, v['viewId'])
        names = {c['controlId']: c['controlName'] for c in hap.controls(ws())}
        print(f"  quick filters: {[(names.get(q['controlId']), q.get('advancedSetting')) for q in info.get('fastFilters') or []]}")


# ── 4 · roles ───────────────────────────────────────────────────────────────

def step_roles():
    """roles.py owns the app's roles; its ORDER and its four matrices now carry States — **the same cell each
    role has for Contacts** (owner, 18 Sep 2026, mid-build): Accounting Administrator full, Accountant and
    Invoicing view · add · edit, Accounting Read-only view. Odoo's `ir.model.access.csv` gives
    `res.country.state` to `base.group_partner_manager` — a contact manager — with read, write, create and
    delete, so a role that may create a contact creates the state that contact sits in. Countries does not
    change: `res.country` sits behind `base.group_system` (12 §1 › Roles)."""
    import roles
    return roles.step_create()


# ── 5 · §1's Rules question ─────────────────────────────────────────────────

def step_unique():
    """§1's *Rules*: **does HAP take *No duplicates* on a formula control?**

    Odoo's constraint is `unique(country_id, code)`, a pair; HAP's *No duplicates* is one field, and §1 asks
    whether the pair can be reached through a hidden formula of `country code + "|" + state code`. Whether the
    switch may be sent at all was answered on the **empty** worksheet on 18 Sep 2026 by putting it on the
    Display Name formula — itself unique across all 2 102 states — and reading it back: the save was accepted
    and `unique` read back `True`. The probe was reverted in the same run and **State key** built instead,
    which is the field `fields` now carries the switch on.

    This step reports where that stands. *Whether the switch is enforced* is a different question, and it is
    `selfcheck` that answers it: the switch reading back True on a formula is not proof that the server
    compares a value it computes after the write."""
    guard()
    f = fields_of(ws())
    key = f.get(STATE_KEY)
    if not key:
        sys.exit(f'{STATE_KEY} is not built — run `fields` first')
    print(f"  {STATE_KEY}: {key['controlId']} type {key['type']} (function formula), "
          f"unique reads {key.get('unique')!r}, perm {key.get('fieldPermission')}, "
          f"expression {json.loads(key.get('dataSource') or '{}').get('expression')}")
    if not key.get('unique'):
        print(f'  DIFF  HAP did not keep No duplicates on {STATE_KEY}')
        return 1
    print(f'  HAP takes No duplicates on a function formula: the switch was accepted on the empty worksheet '
          f'(the Display Name probe, reverted) and is stored on {STATE_KEY}. Whether it is **enforced** is '
          f'`selfcheck`.')
    return 0


# ── 6 · the 2 102 states ────────────────────────────────────────────────────

# §1's digests, from the 19.4 extract (reference/odoo-19.4/res.country.state.md › The records).
DIGESTS = {'count': 2102, 'countries': 74, 'MY': 16, 'GB': 119, 'LV': 119, 'IT': 111, 'SA': 13}
MALAYSIA_CODES = ['MY-%02d' % n for n in range(1, 17)]
MALAYSIA_NAMES = ['Johor', 'Kedah', 'Kelantan', 'Melaka', 'Negeri Sembilan', 'Pahang', 'Pulau Pinang', 'Perak',
                  'Perlis', 'Selangor', 'Terengganu', 'Sabah', 'Sarawak', 'Kuala Lumpur', 'Labuan', 'Putrajaya']


def rows(worksheet_id, page_size=1000):
    """Every record of a worksheet, keyed by controlId, through the CLI's own session (Worksheet/GetFilterRows —
    what `record list` calls)."""
    from hap_cli.core import record as rec
    s, out, page = session(), [], 1
    while True:
        got = rec.get_records(s, worksheet_id, page_size=page_size, page_index=page)['data'] or []
        out += got
        if len(got) < page_size:
            return out
        page += 1


def row_detail(worksheet_id, rowid):
    """One record's stored values keyed by controlId (Worksheet/GetRowDetail — what `record get` calls)."""
    from hap_cli.core import record as rec
    detail = rec.get_record(session(), worksheet_id, rowid)
    raw = detail.get('rowData') if isinstance(detail, dict) else None
    return json.loads(raw) if isinstance(raw, str) else (raw or {})


def relation(value):
    """A Relation cell: [{'sid': rowid, 'name': title}, …] as a list of (rowid, title)."""
    if isinstance(value, str):
        value = json.loads(value) if value.startswith('[') else []
    if not isinstance(value, list):
        return []
    return [(v.get('sid'), v.get('name')) for v in value if isinstance(v, dict)]


def batch(worksheet_id, raw_rows, label='', every=200):
    """Create one record per `{controlId: value}` dict — `hap worksheet record batch-create --rows-json`, made
    through the CLI's own session.

    The command is one **AddWorksheetRow per row** (its own help says 每行一次调用), and `batch_create_rows`
    also re-reads the worksheet's controls for every row it encodes — 4 204 HTTP calls for 2 102 states, on top
    of a `--rows-json` argument far past the kernel's 128 KiB limit for one argument. This is the same encoder
    (`_legacy_cell_entry`, so a Relation becomes `[{"sid": …}]` and nothing is sent raw) and the same write,
    with the control list read once. Returns the new rowids in order."""
    from hap_cli.core import record as rec
    s = session()
    by_id = {c['controlId']: c for c in hap.controls(worksheet_id)}
    out, started = [], time.time()
    for i, raw in enumerate(raw_rows, 1):
        controls = [{'controlId': cid, 'type': by_id[cid]['type'],
                     'controlName': by_id[cid].get('controlName', ''), 'dot': by_id[cid].get('dot', 0),
                     **rec._legacy_cell_entry(by_id[cid], value)} for cid, value in raw.items()]
        res = rec.create_record(s, worksheet_id, controls, trigger_workflow=True)
        rowid = (res or {}).get('rowid') or ((res or {}).get('data') or {}).get('rowid')
        if not rowid:
            raise RuntimeError(f'row {i} was not created: {json.dumps(res, ensure_ascii=False)[:300]}')
        out.append(rowid)
        if every and (i % every == 0 or i == len(raw_rows)):
            print(f'  {label}{i}/{len(raw_rows)} created ({time.time() - started:.0f}s)')
    return out


def read_states():
    """Every state by "<country code>|<state code>", read back field by field.

    `GetFilterRows` does not return every column — a Text the view does not show has no key at all, and a
    **hidden** control comes back empty whatever it is (BUILDING.md) — so the hidden Country Code lookup is not
    read here; Display Name carries the same code and is checked instead. The ids this worksheet needs are
    compared with the first row and, if any is missing, every record is read with `GetRowDetail`."""
    f = fields_of(ws())
    ids = {n: f[n]['controlId'] for n in (NAME, CODE, COUNTRY, DISPLAY)}
    listed = rows(ws())
    if listed and any(cid not in listed[0] for cid in ids.values()):
        listed = [{**r, **row_detail(ws(), r['rowid'])} for r in listed]
    out = {}
    for r in listed:
        linked = relation(r.get(ids[COUNTRY]))
        s = dict(rowid=r['rowid'], name=r.get(ids[NAME]) or '', code=r.get(ids[CODE]) or '',
                 country=linked[0][1] if linked else None, country_rowid=linked[0][0] if linked else None,
                 display_name=r.get(ids[DISPLAY]) or '')
        out[s['rowid']] = s
    return out


def by_key(live, countries_by_rowid):
    """The live states keyed the way `data()` keys the extract: "<country code>|<state code>"."""
    out = {}
    for s in live.values():
        code = countries_by_rowid.get(s['country_rowid'], {}).get('code')
        out[f"{code}|{s['code']}" if code else s['rowid']] = s
    return out


def countries():
    """The live countries by rowid and by name (countries.read_countries, which knows their columns)."""
    import countries as cty
    live = cty.read_countries()
    return {c['rowid']: c for c in live.values()}, {c['name']: c for c in live.values()}


def remember_records(mapping):
    """ids.json records, written in one pass — `common.remember` re-reads and re-writes the file per key."""
    ids = hap.ids()
    records = ids.setdefault('records', {})
    if any(records.get(k) != v for k, v in mapping.items()):
        records.update(mapping)
        C.save_ids(ids)


def step_seed(*only):
    """The 2 102 states of the extract, created in one batch and every one read back. `only` limits it to
    country codes.

    Required is form-side only (BUILDING.md), so the three values are checked here before anything is written;
    a state already stored as the extract has it is left alone, so a second run writes nothing. **ids.json does
    not get 2 102 keys** — the states are identified by Odoo's own natural key, which reads back from the
    worksheet; only Malaysia's sixteen are recorded, the ones a later bundle or a test might point at."""
    guard()
    f = fields_of(ws())
    reference = data()
    by_rowid, by_name = countries()
    bad = [s for s in reference.values() if not s['name'] or not s['code'] or s['country_name'] not in by_name]
    if bad:
        sys.exit(f'the extract carries {len(bad)} states HAP would store but §1 forbids: '
                 f'{[(s["country_code"], s["code"]) for s in bad][:10]}')
    live = by_key(read_states(), by_rowid)
    hap.backup('states_records_pre_seed', live)
    fresh, updates = [], []
    for key, e in reference.items():
        if only and e['country_code'] not in only:
            continue
        current = live.get(key)
        want = (e['name'], e['code'], by_name[e['country_name']]['rowid'])
        if current and (current['name'], current['code'], current['country_rowid']) == want:
            continue
        cells = {f[NAME]['controlId']: e['name'], f[CODE]['controlId']: e['code'],
                 f[COUNTRY]['controlId']: [want[2]]}
        (updates if current else fresh).append((key, e, current, cells))
    for key, e, current, cells in updates:
        hap.run('worksheet', 'record', 'update', ws(), current['rowid'], '-a', APP, '--fields-json',
                json.dumps([{'id': cid, 'value': v} for cid, v in cells.items()], ensure_ascii=False))
        print(f"  updated {key} {e['name']}")
    if fresh:
        print(f'  creating {len(fresh)} states…')
        batch(ws(), [cells for _, _, _, cells in fresh], label='')
    print(f'  {len(fresh) + len(updates)} states written')
    live = read_states()
    keyed = by_key(live, by_rowid)
    remember_records({KEY + k: s['rowid'] for k, s in keyed.items()
                      if k.startswith('MY|') and k in reference})       # not the two TEST states
    return step_verify(*only, live=live)


def digests(keyed):
    """§1's digests over the seeded states."""
    countries_seen = {k.split('|')[0] for k in keyed}
    out = {'count': len(keyed), 'countries': len(countries_seen)}
    for code in ('MY', 'GB', 'LV', 'IT', 'SA'):
        out[code] = sum(1 for k in keyed if k.startswith(code + '|'))
    return out


def step_verify(*only, live=None):
    """Every live state against the 19.4 extract, field by field, then §1's digests and Malaysia's sixteen."""
    reference = data()
    by_rowid, _ = countries()
    live = read_states() if live is None else live
    keyed = by_key(live, by_rowid)
    bad, missing = {}, []
    for key, e in reference.items():
        if only and e['country_code'] not in only:
            continue
        current = keyed.get(key)
        if not current:
            missing.append(key)
            continue
        want = {'name': e['name'], 'code': e['code'], 'country': e['country_name'],
                'display_name': f"{e['name']} ({e['country_code']})"}
        diff = {k: (current[k], v) for k, v in want.items() if current[k] != v}
        if diff:
            bad[key] = diff
    extra = sorted(k for k in keyed if k not in reference)
    print(f'  {len(reference)} states in the extract; {len(missing)} missing {missing[:10]}; '
          f'{len(bad)} differing {json.dumps(bad, ensure_ascii=False)[:400]}; '
          f'{len(extra)} live records outside it {extra[:10]}')
    got = digests({k: v for k, v in keyed.items() if k in reference})
    from_data = digests(reference)
    for key, want in DIGESTS.items():
        mark = 'OK  ' if got.get(key) == want == from_data.get(key) else 'DIFF'
        print(f'  {mark}  {key:<10} live {got.get(key):<8} §1 {want:<8} extract {from_data.get(key)}')
    my = [keyed.get(f'MY|{c}') for c in MALAYSIA_CODES]
    ok = all(s and s['name'] == n for s, n in zip(my, MALAYSIA_NAMES))
    print(f"  {'OK  ' if ok else 'DIFF'}  Malaysia   " +
          ' · '.join(f"{c} {(s or {}).get('name')}" for c, s in zip(MALAYSIA_CODES, my)))
    sel = keyed.get('MY|MY-10')
    print(f"            Display Name reads {sel and sel['display_name']!r} for {sel and sel['name']!r}")
    return (len(missing) + len(bad) + sum(1 for k in DIGESTS if got.get(k) != DIGESTS[k]) + (0 if ok else 1))


def step_state(*codes):
    """The stored values of states by State Code (every country that has one)."""
    by_rowid, _ = countries()
    keyed = by_key(read_states(), by_rowid)
    for key in sorted(keyed):
        if not codes or key.split('|')[1] in codes or key in codes:
            print(f'  {key}: ' + json.dumps(keyed[key], ensure_ascii=False))


def step_order():
    """The view's records in the order the view returns them (its own sort)."""
    f = fields_of(ws())
    code, name = f[CODE]['controlId'], f[NAME]['controlId']
    for v in hap.listing('worksheet', 'view', 'list', ws(), '-a', APP):
        res = hap.run('worksheet', 'record', 'list', ws(), '-a', APP, '-n', '30', '--view-id', v['viewId'],
                      '--use-field-id-as-key')
        d = res.get('data', res) if isinstance(res, dict) else res
        listed = (d.get('rows') if isinstance(d, dict) else d) or []
        print(f"  {v['name']} (first {len(listed)}): " +
              ', '.join(f"{r.get(code)} {r.get(name)}" for r in listed[:12]))


# ── 7 · the relation on Contacts ────────────────────────────────────────────

CON_FIELD = 'State'                               # the relation's name, once the stand-in has given it up
STANDIN_NAME = 'State (text stand-in)'            # the stand-in's name while both exist
STANDIN_PARKED = (26, 0, 6)                       # under Parent name, out of the relation's cell, until it goes
CON_PLACE = (8, 1, 6)                             # contacts.PLACE['State'] — beside City, where the text was


def state_relation():
    """A one-way Relation → States, single, shown as a dropdown, **not narrowed by the contact's country**.

    Odoo's partner form passes `default_country_id`, which `name_search` does not narrow on, so its picker
    offers every state in the world labelled with its country code — and so does this one (§1 › Not built now:
    a HAP relation *can* be filtered by another control, so leaving it open is a decision, not a limit).
    Sent without a controlId so the server mints it, and — `bidirectional` "0" — States gets no reverse: Odoo's
    state form does not list the partners of a state."""
    return C.control('RELATE_SHEET', CON_FIELD, CON_PLACE, alias='state_id', hint='', desc='',
                     data_source=ws(), multi=False,
                     advanced_setting={'bidirectional': '0', 'showtype': '3'})   # 3 = dropdown


def con_relation(ctrls=None):
    return next((c for c in (ctrls if ctrls is not None else hap.controls(con_ws()))
                 if c['type'] == RELATION and c.get('dataSource') == ws()), None)


def standin(ctrls=None):
    return next((c for c in (ctrls if ctrls is not None else hap.controls(con_ws()))
                 if c['controlId'] == TEXT_STANDIN), None)


def step_contacts():
    """§1's step on Contacts: the relation State in the text control's cell — row 8, right half, beside City —
    while the stand-in still holds its values.

    Both cannot share a name or a cell, so the stand-in is renamed "State (text stand-in)" and parked under
    Parent name first (one save), the relation is appended (`add-fields`, which parks it at row 9999) and then
    placed (a second save). The **alias `state_id` is free from the start** — the stand-in holds `state` — so
    there is no alias hand-over of the kind bundle 3 needed. Every save of Contacts pins HAP's optimistic lock:
    another administrator is building CRM worksheets in this app."""
    guard()
    ctrls, version = C.controls_with_version(con_ws())
    rel, text = con_relation(ctrls), standin(ctrls)
    before = snap()
    if not rel:
        if not text:
            sys.exit('neither the stand-in nor the relation is on Contacts — stopping')
        print('  backup:', hap.backup('states_contacts_controls_pre_relation', ctrls))
        if (text['controlName'], text['row'], text['col']) != (STANDIN_NAME, *STANDIN_PARKED[:2]):
            text.update(controlName=STANDIN_NAME, row=STANDIN_PARKED[0], col=STANDIN_PARKED[1],
                        size=STANDIN_PARKED[2])
            C.save_controls(con_ws(), ctrls, version=version)
            before = expect(before, 'the stand-in renamed and parked',
                            changed={'Contacts': {CON_FIELD: {'controlName', 'row', 'col', 'size'}}})
        C.append_controls(con_ws(), [state_relation()])
        before = expect(before, 'the relation added', new={'Contacts': {CON_FIELD}})
    ctrls, version = C.controls_with_version(con_ws())
    rel = con_relation(ctrls)
    row, col, size = CON_PLACE
    want = dict(controlName=CON_FIELD, alias='state_id', row=row, col=col, size=size, sectionId='', hint='',
                desc='', required=False)
    if any(rel.get(k) != v for k, v in want.items()) or rel.get('fieldPermission') != '111':
        rel.update(want, fieldPermission='111')
        C.save_controls(con_ws(), ctrls, version=version)
        before = expect(before, 'the relation placed and aliased',
                        changed={'Contacts': {CON_FIELD: {'row', 'col', 'size', 'alias', 'fieldPermission',
                                                          'hint', 'desc'}}})
    rel = con_relation()
    C.remember('controls', CON_KEY + CON_FIELD, rel['controlId'])
    adv = rel.get('advancedSetting') or {}
    print(f"  {CON_FIELD}: {rel['controlId']} row={rel['row']} col={rel['col']} size={rel['size']} "
          f"alias={rel.get('alias')!r} one-way={adv.get('bidirectional')!r} showtype={adv.get('showtype')!r} "
          f"target={rel.get('dataSource')} source={rel.get('sourceControlId')!r}")
    text = standin()
    print(f"  stand-in: {text and (text['controlName'], text['row'], text['col'], text.get('alias'))}")
    if rel.get('sourceControlId') in {c['controlId'] for c in hap.controls(ws())}:
        sys.exit('States gained a reverse control — the relation was meant to be one-way')


# ── 8 · carry the contacts' values ──────────────────────────────────────────

def read_contacts():
    """Every contact's State text, State relation and Country relation, by Display Name.

    `record get` keys a value by the control's **alias** — the stand-in's `state`, the relation's `state_id` —
    so the two never collide here."""
    out = {}
    for r in C.records(con_ws(), APP):
        d = hap.run('worksheet', 'record', 'get', con_ws(), r['rowid'], '-a', APP)['data']
        state, country = relation(d.get('state_id')), relation(d.get('country_id'))
        out[d.get('complete_name') or r['rowid']] = dict(
            rowid=r['rowid'], name=d.get('name'), text=d.get('state'),
            state=state[0][1] if state else None, state_rowid=state[0][0] if state else None,
            country=country[0][1] if country else None, country_rowid=country[0][0] if country else None,
            active=d.get('active'))
    return out


# The eight contacts whose State text read a Malaysian state when this bundle found them (§1): seven Selangor
# and one Sarawak. Written down by Display Name so that `verify` still means something once the text control is
# gone — after the deletion there is nothing left to compare the relation with.
CARRIED = {'Klinik Kesihatan Damansara': 'Selangor',
           'Sarawak Timber Logistics': 'Sarawak',
           'Sunway Construction Group': 'Selangor',
           'TEST QA Trading Sdn Bhd': 'Selangor',
           'TEST QA Trading Sdn Bhd, TEST Person One': 'Selangor',
           'TEST QA Trading Sdn Bhd, TEST Person Three': 'Selangor',
           'TEST QA Trading Sdn Bhd, TEST Person Two': 'Selangor',
           'TEST QA Trading Sdn Bhd, TEST UI Country Person': 'Selangor'}
CARRIED_COUNTRY = 'MY'                            # every one of them is in Malaysia


def step_carry():
    """Every contact whose State text names a Malaysian state is given the relation, and every value is read
    back. Once the stand-in has been deleted there is no text left to read, so the table above drives it."""
    guard()
    rel = con_relation()
    if not rel:
        sys.exit('run `contacts` first')
    by_rowid, _ = countries()
    keyed = by_key(read_states(), by_rowid)
    live = read_contacts()
    hap.backup('states_contacts_records_pre_carry', live)
    text_gone = standin() is None
    for display, c in sorted(live.items()):
        text = (CARRIED.get(display, '') if text_gone else (c['text'] or '')).strip()
        if not text:
            continue
        want = next((s for k, s in keyed.items()
                     if k.startswith(CARRIED_COUNTRY + '|') and s['name'] == text), None)
        if not want:
            sys.exit(f'{display}: the State text reads {text!r}, which is no state of {CARRIED_COUNTRY}')
        if c['state_rowid'] == want['rowid']:
            continue
        hap.run('worksheet', 'record', 'update', con_ws(), c['rowid'], '-a', APP, '--fields-json',
                json.dumps([{'id': rel['controlId'], 'value': [want['rowid']]}]))
        print(f"  {display}: State set to {want['display_name']}")
    return verify_carry()


def verify_carry():
    """Every contact named in CARRIED holds its state; while the text control still exists, the relation must
    also equal the text on every contact, carried or not."""
    live, text_gone = read_contacts(), standin() is None
    bad = 0
    for display, c in sorted(live.items()):
        text = (c['text'] or '').strip()
        want = CARRIED.get(display)
        stored = (c['state'] or '').split(' (')[0] or None          # the relation reads "Selangor (MY)"
        ok = (stored == want) if display in CARRIED else (text_gone or stored == (text or None))
        if not text_gone and display in CARRIED and text != want:
            ok = False                                              # the text moved under us: CARRIED is stale
        bad += not ok
        print(f"  {'OK  ' if ok else 'DIFF'}  {display[:46]:<46} "
              + (f'text {text or "—":<10} ' if not text_gone else '')
              + f"relation {c['state'] or '—':<16} country {c['country'] or '—':<10} active={c['active']}"
              + ('' if display in CARRIED or not c['state'] else '   (not in CARRIED)'))
    carried = sum(1 for c in live.values() if c['state'])
    print(f'  carry: {len(live)} contacts, {len(CARRIED)} to carry a state, {carried} carrying the relation '
          f"— {bad} differing (the text control is {'gone' if text_gone else 'still there'})")
    return bad


# ── 9 · retire the stand-in ─────────────────────────────────────────────────

CON_WORKFLOWS = ('Contacts: copy company details to its contact',
                 'Contacts: push company address and Tax ID to its contacts')


def step_retire():
    """§1's last step on Contacts. Refuses unless every contact reads back from the relation. Then:

    1. `contacts.py automations` re-points the two address-sync workflows, which name the State control in
       **four** places — the branch in front of *Copy the company address*, that step's `fields`, and *Copy the
       address to them*'s `fields`, plus the trigger's `assignFieldIds` on the push workflow. Every one of them
       resolves the six address fields **by name**, so once the stand-in is renamed "State" means the relation;
    2. the stand-in `6aa8a452f363582dd37a50e5` is deleted — a full save of Contacts that leaves it out, the
       owner's approved deletion;
    3. `contacts.py layout` proves that script is in step with the worksheet it owns (it must change nothing),
       and every view, rule, button, control and workflow node is scanned for the dead id.

    §1 puts the deletion before the re-pointing. It is done the other way round on purpose, as bundle 4 did: a
    deleted control stays in every view, quick filter, rule and workflow step that names it and nothing cleans
    it up (BUILDING.md).

    §1 also says **no view points at State** — the tables show Display Name · Email · Phone · Country and the
    Kanban card Email · Phone · City · Country. That is checked here rather than assumed."""
    import contacts
    guard()
    rel = con_relation()
    if not rel:
        sys.exit('run `contacts` first')
    if verify_carry():
        sys.exit('not every contact reads back from the relation — refusing to delete the stand-in')
    pointing = views_naming(TEXT_STANDIN)
    print(f"  views naming the stand-in: {pointing or 'none — §1 is right that no view points at State'}")
    before = snap()
    print('  ── contacts.py automations')
    print('  backup:', hap.backup('states_contacts_workflows_pre_retire',
                                  {name: workflow_nodes(hap.ids()['workflows'][name]) for name in CON_WORKFLOWS}))
    contacts.step_automations()
    before = expect(before, 'contacts.py automations (no control may change)')
    text = standin()
    if text:
        ctrls, version = C.controls_with_version(con_ws())
        print('  backup:', hap.backup('states_contacts_controls_pre_retire', ctrls))
        print(f"  deleting {text['controlName']!r} {TEXT_STANDIN} (type {text['type']}, alias "
              f"{text.get('alias')!r}, row {text['row']}) — the owner-approved deletion")
        C.save_controls(con_ws(), [c for c in ctrls if c['controlId'] != TEXT_STANDIN], version=version)
        before = expect(before, 'the stand-in deleted', gone={'Contacts': {TEXT_STANDIN}})
        if standin():
            sys.exit('the stand-in is still there after the save')
    else:
        print('  the stand-in is already gone')
    print('  ── contacts.py layout')
    contacts.step_layout()
    expect(before, 'contacts.py layout (no control may change)')
    return verify_carry() + step_deadrefs()


def views_naming(cid):
    """Contacts' views that carry a control id — as a column, a card field, a quick filter or a sort."""
    out = []
    for v in hap.listing('worksheet', 'view', 'list', con_ws(), '-a', APP):
        info = C.view_info(con_ws(), APP, v['viewId'])
        where = [k for k in ('showControls', 'displayControls', 'controlsSorts')
                 if cid in (info.get(k) or [])]
        where += ['fastFilters'] if cid in [q['controlId'] for q in info.get('fastFilters') or []] else []
        where += ['sort'] if cid in [info.get('sortCid')] + [s['controlId'] for s in info.get('moreSort') or []] \
            else []
        if where:
            out.append(f"{v['name']}:{'/'.join(where)}")
    return out


CATALOGUE_KEYS = ('flowNodeList', 'flowNodeAppDtos', 'formulaMap', 'controls', 'addControls', 'filedControls',
                  'relationControls', 'appList')


def workflow_nodes(pid):
    """Every node of a workflow with its full configuration, through the CLI's own session."""
    from hap_cli.core import flow_node, workflow as wf_mod
    s = session()
    proc = wf_mod.get_process_by_id(s, pid) or {}
    return {node_id: flow_node.get_node_detail(s, pid, node_id, app_id=APP)
            for node_id in (proc.get('flowNodeMap') or {})}


def step_deadrefs(dead=TEXT_STANDIN):
    """Every view, rule, button, control and workflow node of the app scanned for a control id — the deleted
    stand-in's. A node's control catalogue lists every control of a worksheet, dead or alive, so it is left out
    of the scan (payterms.deadrefs)."""
    hits = []
    for name in OTHERS + (WORKSHEET,):
        w = hap.ids()['worksheets'].get(name)
        if not w:
            continue
        for v in hap.listing('worksheet', 'view', 'list', w, '-a', APP):
            if dead in json.dumps(C.view_info(w, APP, v['viewId'])):
                hits.append(f"{name} view {v['name']!r}")
        for r in hap.listing('worksheet', 'rules', w):
            if dead in json.dumps(r):
                hits.append(f"{name} rule {r['name']!r}")
        for b in hap.listing('worksheet', 'custom-actions', w):
            if dead in json.dumps(b):
                hits.append(f"{name} button {b['name']!r}")
        for c in hap.controls(w):
            if c['controlId'] != dead and dead in json.dumps({k: v for k, v in c.items()
                                                              if k != 'relationControls'}):
                hits.append(f"{name} control {c['controlName']!r}")
    pids = {w.get('id') or w.get('processId'): w.get('name') for w in hap.listing('workflow', 'list', APP)}
    pids.update({v: k for k, v in hap.ids()['workflows'].items()})
    nodes = 0
    for pid, name in pids.items():
        for node_id, d in workflow_nodes(pid).items():
            nodes += 1
            if dead in json.dumps({k: v for k, v in (d or {}).items() if k not in CATALOGUE_KEYS}):
                hits.append(f'workflow {name!r} node {node_id} ({(d or {}).get("name")!r})')
    print(f"  deadrefs {dead}: {len(OTHERS) + 1} worksheets' views, rules, buttons and controls, and "
          f"{len(pids)} workflows ({nodes} nodes) scanned — {hits or 'no reference'}")
    return len(hits)


# ── 10 · workflows E and F ──────────────────────────────────────────────────

WF_E = 'Contacts: the Country follows the State'
WF_F = 'Contacts: a State that belongs elsewhere is cleared'
E_TRIGGER = "When a contact's State is set or changed"
F_TRIGGER = "When a contact's Country changes and it has a State"
GET_STATE = 'Get the state'
GATEWAY = "The state's Country is not the contact's Country?"
PATH_YES, PATH_NO = 'Yes — the state belongs to another country', 'No — they already agree'
E_STEP = 'Write the Country from the state'
F_STEP = 'Clear the State'
# 触发其他工作流 (pd-openweb WorkflowSettings/ProcessConfig, `hap workflow config-get` / `config-set`):
# 0 允许触发 — HAP's default · 1 只能触发指定工作流 · 2 不允许触发. E writes the Country and F writes the State, which
# are each other's trigger field, so both are set to 2 and neither can start the other (§1; the pattern bundle 3
# set for C and Confirm).
NO_OTHER_WORKFLOWS = 2
# A Relation compared with another node's Relation is conditionId 33, the workflow filter's "is" (BUILDING.md,
# `variants.py`, `journals.py`). Its opposite is not in hap-cli's operator table, so the gateway is written the
# way round that needs only 33: the **conditioned** path is "they are the same" and carries nothing, and the
# **default** path — a branch path with no condition is the else (hap-cli `_build_branch`) — carries the write.
RELATION_IS = '33'


def read(*args):
    out = hap.run(*args)
    return out.get('data', out) if isinstance(out, dict) else out


def node_get(pid, node_id):
    return read('workflow', 'node', 'get', pid, node_id)


def ensure_quiet(pid, label):
    """Make the workflow's own writes start no other workflow: 触发其他工作流 set to 不允许触发 (`triggerType` 2).
    The whole config goes back as read — what the editor's Save sends — and every other key is read back
    unchanged. Like the editor's save it leaves unpublished changes; publishing is the caller's
    (`payterms.ensure_quiet`)."""
    cfg = read('workflow', 'config-get', pid)
    if (cfg.get('triggerType'), list(cfg.get('processIds') or [])) == (NO_OTHER_WORKFLOWS, []):
        return False
    print('  backup:', hap.backup('states_process_config_pre_quiet',
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


def same_country_condition(state_node, trigger, state_country, con_country):
    """The gateway's one condition: the state's Country **is** the contact's Country (conditionId 33, with the
    comparison value taken from the trigger record)."""
    return [[{'nodeId': state_node, 'filedId': state_country['controlId'], 'filedValue': COUNTRY,
              'filedTypeId': RELATION, 'enumDefault': state_country.get('enumDefault'),
              'conditionId': RELATION_IS, 'sourceType': 0,
              'conditionValues': [{'nodeId': trigger, 'controlId': con_country['controlId']}]}]]


def condition_shape(groups):
    return [[(c.get('nodeId'), c.get('filedId'), str(c.get('conditionId')),
              [(v.get('nodeId'), v.get('controlId')) for v in c.get('conditionValues') or []]) for c in g]
            for g in groups or []]


def step_state_of(pid, node_id):
    d = node_get(pid, node_id)
    return dict(selectNodeId=d.get('selectNodeId'), appId=d.get('appId'), isException=bool(d.get('isException')),
                fields=[(x.get('fieldId'), x.get('nodeId') or '', x.get('fieldValueId') or '',
                         bool(x.get('isClear'))) for x in d.get('fields') or []])


def save_update(pid, node_id, name, select_node, fields):
    """An update step writing exactly `fields` on the record `select_node` produced (payterms.save_update)."""
    want = (select_node, con_ws(), False, [(x['fieldId'], x.get('nodeId') or '', x.get('fieldValueId') or '',
                                            bool(x.get('isClear'))) for x in fields])
    s = step_state_of(pid, node_id)
    if (s['selectNodeId'], s['appId'], s['isException'], s['fields']) == want:
        return False
    hap.run('workflow', 'node', 'save', pid, node_id, '--type', '6', '-n', name, '-c', json.dumps(
        {'actionId': '2', 'appId': con_ws(), 'appType': 1, 'selectNodeId': select_node, 'fields': fields},
        ensure_ascii=False))
    s = step_state_of(pid, node_id)
    if (s['selectNodeId'], s['appId'], s['isException'], s['fields']) != want:
        sys.exit(f'{name}: read back {s}, want {want}')
    return True


def trigger_state(pid, start):
    d = node_get(pid, start)
    return dict(name=d.get('name'), appId=d.get('appId'), fields=sorted(d.get('assignFieldIds') or []),
                condition=condition_shape(d.get('operateCondition')))


def workflow_skeleton(step_name, step_fields_fn, state_rel):
    """The nodes `batch-add` makes: the fresh read of the state, the gateway, and the write on its else path.

    `batch-add` writes neither a branch path's condition in a second call nor a step's field bindings in the
    shape the server keeps, so both are saved again afterwards and read back (`wire_workflow`)."""
    return [
        {'nodeAlias': 'state', 'nodeType': 'get_relation', 'name': GET_STATE,
         'config': {'target': {'node': {'nodeAlias': 'trigger'}}, 'fields': [{'fieldId': state_rel['controlId']}],
                    'worksheet': ws()}},
        {'nodeAlias': 'gate', 'nodeType': 'branch', 'name': GATEWAY, 'config': {'mode': 'exclusive', 'paths': [
            {'alias': 'gate_same', 'name': PATH_NO},                  # conditioned below: they already agree
            {'alias': 'gate_differs', 'name': PATH_YES, 'nodes': [    # no condition: the default/else path
                {'nodeAlias': 'write', 'nodeType': 'update_record', 'name': step_name,
                 'config': {'target': {'node': {'nodeAlias': 'trigger'}}, 'fields': step_fields_fn()}}]}]}},
    ]


def step_automations():
    """Odoo's two address onchanges on res.partner, as workflows on Contacts — §1's E and F.

    * **E** `_onchange_state`: the State is set or changed and is not empty → read the state → unless its
      Country is already the contact's, write the contact's Country from it.
    * **F** `_onchange_country_id`: the Country changes while a State is set → read the state → unless its
      Country is the contact's, empty the State (`isClear`, the editor's 清空: sent as a plain empty value the
      entry is dropped on save and the step writes nothing — BUILDING.md).

    Both are 新增或更新 narrowed to one field, so E runs on a create only when the create writes a State, and on
    an update whenever State is in the write. Both are **quiet** (`triggerType` 2): E writes the Country, which
    is F's trigger field, and F writes the State, which is E's, so without it each would start the other."""
    guard()
    f = hap.by_name(c for c in hap.controls(con_ws()) if c['type'] != C.TAB)
    if standin():
        sys.exit('the stand-in is still on Contacts — run `retire` first, so that "State" means the relation')
    state_rel, con_country = f[CON_FIELD], f['Country']
    state_country = fields_of(ws())[COUNTRY]
    changed_any = 0
    for label, name, trigger_name, trigger_field, step_name in (
            ('E', WF_E, E_TRIGGER, state_rel, E_STEP), ('F', WF_F, F_TRIGGER, con_country, F_STEP)):
        def step_fields_fn(label=label, state_country=state_country, con_country=con_country,
                           state_rel=state_rel):
            return ([{'fieldId': con_country['controlId'], 'valueRef': {
                'kind': 'field', 'node': {'nodeAlias': 'state'}, 'fieldId': state_country['controlId'],
                'nodeAppId': ws()}}] if label == 'E' else
                    [{'fieldId': state_rel['controlId'], 'value': ''}])
        desc = ('Odoo res.partner._onchange_state: setting a state sets the Country. When the state the contact '
                "now points at belongs to another country, the contact's Country is written from it."
                if label == 'E' else
                'Odoo res.partner._onchange_country_id: changing the country clears a State that belongs to '
                'another country.')
        changed_any += wire(label, name, desc, trigger_name, trigger_field, state_rel, state_country,
                            con_country, step_name, step_fields_fn)
    for name in (WF_E, WF_F):
        print(C.structure(hap.ids()['workflows'][name]))
    return 0


def wire(label, name, desc, trigger_name, trigger_field, state_rel, state_country, con_country,
         step_name, step_fields_fn):
    """Create the workflow if it is missing, then bring its trigger, its gateway and its write into the shape
    the server keeps, make it quiet and publish. Writes nothing when everything already agrees."""
    ids = hap.ids()
    pid = ids.setdefault('workflows', {}).get(name)
    if not pid:
        live = {w.get('name'): (w.get('id') or w.get('processId')) for w in hap.listing('workflow', 'list', APP)}
        pid = live.get(name)          # `workflow create` can time out having created it (BUILDING.md)
    if not pid:
        out = hap.run('workflow', 'create', '-c', ids['org'], '-n', name, '-a', APP, '--type', 'worksheet',
                      '-d', desc)
        d = out.get('data', out) if isinstance(out, dict) else out
        pid = d if isinstance(d, str) else (d.get('id') or d.get('processId'))
        print(f'  {label}: workflow created {pid}')
    C.remember('workflows', name, pid)
    proc = hap.run('workflow', 'node', 'list', pid)
    start = proc['startEventId']
    by_name = {n['name']: n for n in proc['flowNodeMap'].values()}
    changed = False
    if GET_STATE not in by_name:
        spec = workflow_skeleton(step_name, step_fields_fn, state_rel)
        hap.run('workflow', 'node', 'batch-add', pid, '--nodes', json.dumps(spec, ensure_ascii=False),
                '--trigger-worksheet', con_ws(), '--trigger-event', 'create_or_update',
                '--trigger-fields', trigger_field['controlId'], '--trigger-alias', 'trigger',
                '--trigger-filter', json.dumps({'logic': 'and', 'items': [
                    {'left': {'node': {'nodeAlias': 'trigger'}, 'fieldId': state_rel['controlId'],
                              '_filedTypeId': RELATION, '_enumDefault': state_rel.get('enumDefault')},
                     'op': 'not_empty'}]}, ensure_ascii=False))
        print(f'  {label}: steps added')
        changed = True
        proc = hap.run('workflow', 'node', 'list', pid)
        by_name = {n['name']: n for n in proc['flowNodeMap'].values()}
    nodes = proc['flowNodeMap']
    gate = by_name[GATEWAY]
    paths = [nodes[i] for i in gate.get('flowIds') or []]
    if len(paths) != 2:
        sys.exit(f'{label}: the gateway has {len(paths)} paths, want 2')
    # the path that runs into the write is the else path; the other carries the "they agree" condition
    write_path = next((p for p in paths if p.get('nextId') not in ('', None, '99')), None)
    same_path = next(p for p in paths if p is not write_path)
    write_node = nodes[write_path['nextId']]
    # 1 · the trigger: one field, and "the State is not empty"
    want_condition = [[{'nodeId': start, 'filedId': state_rel['controlId'], 'filedValue': CON_FIELD,
                        'filedTypeId': RELATION, 'enumDefault': state_rel.get('enumDefault'),
                        'conditionId': '7', 'sourceType': 0, 'conditionValues': []}]]
    want_trigger = dict(name=trigger_name, appId=con_ws(), fields=[trigger_field['controlId']],
                        condition=condition_shape(want_condition))
    if trigger_state(pid, start) != want_trigger:
        trig = node_get(pid, start)
        hap.run('workflow', 'node', 'save', pid, start, '--type', '0', '-n', trigger_name, '-c', json.dumps(
            {'appId': con_ws(), 'appType': 1, 'triggerId': trig.get('triggerId'),
             'assignFieldIds': [trigger_field['controlId']], 'operateCondition': want_condition,
             'returns': []}, ensure_ascii=False))
        if trigger_state(pid, start)['name'] != trigger_name:
            hap.run('workflow', 'node', 'rename', pid, start, '-n', trigger_name)
        got = trigger_state(pid, start)
        if got != want_trigger:
            sys.exit(f'{label}: trigger read back {got}, want {want_trigger}')
        print(f'  {label}: trigger rewritten')
        changed = True
    # 2 · the gateway's two paths: the condition on the "they agree" one, no condition on the else
    want_same = condition_shape(same_country_condition(by_name[GET_STATE]['id'], start, state_country,
                                                       con_country))
    if condition_shape(node_get(pid, same_path['id']).get('conditions')) != want_same:
        hap.run('workflow', 'node', 'save', pid, same_path['id'], '--type', '2', '-n', PATH_NO, '-c', json.dumps(
            {'operateCondition': same_country_condition(by_name[GET_STATE]['id'], start, state_country,
                                                        con_country)}, ensure_ascii=False))
        if condition_shape(node_get(pid, same_path['id']).get('conditions')) != want_same:
            sys.exit(f"{label}: the {PATH_NO!r} condition read back "
                     f"{condition_shape(node_get(pid, same_path['id']).get('conditions'))}")
        print(f'  {label}: {PATH_NO!r} condition written')
        changed = True
    if node_get(pid, write_path['id']).get('conditions'):
        sys.exit(f'{label}: the else path {PATH_YES!r} carries a condition; it must have none')
    for node, wanted in ((same_path, PATH_NO), (write_path, PATH_YES)):
        if nodes[node['id']].get('name') != wanted:
            hap.run('workflow', 'node', 'rename', pid, node['id'], '-n', wanted)
            changed = True
    # 3 · the write itself
    if label == 'E':
        fields = [{'fieldId': con_country['controlId'], 'type': RELATION, 'addType': 0, 'fieldValue': '',
                   'fieldValueId': state_country['controlId'], 'nodeId': by_name[GET_STATE]['id'],
                   'sureNodeId': by_name[GET_STATE]['id'], 'nodeAppType': 1}]
    else:
        fields = [{'fieldId': state_rel['controlId'], 'type': RELATION, 'addType': 0, 'fieldValue': '',
                   'fieldValueId': '', 'nodeId': '', 'isClear': True}]
    changed |= save_update(pid, write_node['id'], step_name, start, fields)
    # 4 · quiet, then publish
    changed |= ensure_quiet(pid, label)
    info = read('workflow', 'get', pid)
    if (info.get('explain') or '') != desc:
        hap.run('workflow', 'update', pid, '-n', name, '-d', desc)
        changed = True
    if changed or not info.get('enabled') or info.get('publishStatus') != 2:
        result = C.publish(pid)
        print(f'  {label}: published {result}')
        if not result.get('isPublish'):
            sys.exit(f'{label}: publish failed: {result}')
    print(f"  {label} {name}: {pid} — trigger {trigger_state(pid, start)}, quiet "
          f"{read('workflow', 'config-get', pid).get('triggerType')}")
    return changed


# ── self-check ──────────────────────────────────────────────────────────────

TEST_CONTACT = 'TEST State Contact'                # selfcheck's own contact; left in Contacts
TEST_STATES = {'TEST State One': 'ZZ-01', 'TEST State Two': 'ZZ-02'}   # selfcheck's own states, left in States


def attempt(*args):
    """Run a write expected to be refused; return (refused, message) — countries.attempt."""
    try:
        out = hap.run(*args)
    except RuntimeError as error:
        return True, str(error)[:300]
    d = out.get('data', out) if isinstance(out, dict) else {}
    code = (out.get('resultCode') if isinstance(out, dict) else None) or \
           (d.get('resultCode') if isinstance(d, dict) else None)
    return code not in (None, 1), json.dumps(out, ensure_ascii=False)[:200]


def unique_probe():
    """§1's *Rules*, proved on the two TEST states: is `State key`'s No duplicates enforced?

    TEST State Two's State Code is set to TEST State One's — both Malaysian, so both keys become `MY|ZZ-01` —
    and the answer is read back. The code is restored in the same run, so nothing duplicate is left behind."""
    f = fields_of(ws())
    by_code = {}
    for r in rows(ws()):
        name = r.get(f[NAME]['controlId'])
        if name in TEST_STATES:
            by_code[name] = r['rowid']
    missing = [n for n in TEST_STATES if n not in by_code]
    if missing:
        print(f'  0. the TEST states {missing} are gone — the No-duplicates probe is skipped')
        return []
    one, two = by_code['TEST State One'], by_code['TEST State Two']
    key = lambda rowid: row_detail(ws(), rowid).get(f[STATE_KEY]['controlId'])
    refused, message = attempt('worksheet', 'record', 'update', ws(), two, '-a', APP, '--fields-json',
                               json.dumps([{'id': f[CODE]['controlId'], 'value': TEST_STATES['TEST State One']}]))
    after = (key(one), key(two))
    hap.run('worksheet', 'record', 'update', ws(), two, '-a', APP, '--fields-json',
            json.dumps([{'id': f[CODE]['controlId'], 'value': TEST_STATES['TEST State Two']}]))
    # The write being **accepted** is the recorded answer (§2, and BUILDING.md): the switch is stored on a
    # formula control and never applied. It is printed as a known difference rather than a failure — what
    # would be news is HAP starting to enforce it, and that is what returns a problem.
    print(f"  {'CHANGED' if refused else 'KNOWN  '} 0. {STATE_KEY} No duplicates on a second state of the same "
          f"country: {'refused' if refused else 'ACCEPTED'} — {message[:110]}")
    print(f'        the two keys then read {after}; restored to {key(two)!r}. HAP stores No duplicates on a '
          f'function formula and never applies it (a Text field carrying the same switch refuses this write '
          f'with resultCode 11 — 11 §2)')
    return [] if not refused else [f'0. No duplicates on the {STATE_KEY} formula **refused** the write — HAP '
                                   f'now enforces the switch on a formula control; 12 §2 says it does not']


def quiesce(fn, quiet_for=10, limit=90):
    """Poll `fn` until its answer has not changed for `quiet_for` seconds, and return it.

    A worksheet-event workflow registers about five seconds after the write that starts it and writes a second
    or two later, so a test that reads back the moment the write returns is reading the record *before* the
    workflow has touched it — and a test that writes again straight away races the run still in flight. The
    first `selfcheck` run did exactly that: E's run for the Johor write evaluated its gateway four seconds
    **after** the next write had set the Country to Singapore, found the two disagreeing and wrote Malaysia
    back over it, and F then correctly saw a state whose country matched. Both workflows were right and the
    test was wrong. So every step here waits for the record to stop moving."""
    last, since, deadline = fn(), time.time(), time.time() + limit
    while time.time() < deadline:
        time.sleep(2)
        now = fn()
        if now != last:
            last, since = now, time.time()
        elif time.time() - since >= quiet_for:
            break
    return last


def step_selfcheck():
    """Drive **State key's No duplicates** and then **E and F** through the CLI.

    0. §1's *Rules*, the part `unique` cannot answer: the switch is **stored** on a function formula and
       **never enforced**. TEST State Two's State Code is set to TEST State One's, which makes the two keys
       `MY|ZZ-01` and `MY|ZZ-01`, and the write is accepted — where the same write on a **Text** field carrying
       the switch is refused with `resultCode 11` (bundle 4's Countries selfcheck). The code is put back in the
       same run. A duplicate `record create` was tried once, on 18 Sep 2026 while the worksheet held nothing
       but these two records, and was accepted as well.

    Then E and F on one TEST contact — the only way to see, without the browser, that the gateway's relation
    comparison really fires:

      1. a contact is given **Selangor (MY)** while its Country is empty → E writes **Malaysia**;
      2. the same contact is given **Johor (MY)**, a state of the country it already holds → E has nothing to
         do and the Country stays Malaysia (the "they agree" path);
      3. the contact's Country is changed to **Singapore** → F clears the State;
      4. the contact is given **Aceh (ID)**, a state of another country → E moves the Country to Indonesia.

    TEST State Contact is created once and left in Contacts."""
    guard()
    f = hap.by_name(c for c in hap.controls(con_ws()) if c['type'] != C.TAB)
    rel, con_country = f[CON_FIELD], f['Country']
    by_rowid, by_name = countries()
    keyed = by_key(read_states(), by_rowid)
    live = read_contacts()
    problems = []
    problems += unique_probe()
    contact = live.get(TEST_CONTACT)
    if not contact:
        kind = next(o['key'] for o in f['Address Type']['options'] if o['value'] == 'Contact')
        rowid = C.row_id(hap.run('worksheet', 'record', 'create', con_ws(), '-a', APP, '--fields-json',
                                 json.dumps([{'id': f['Name']['controlId'], 'value': TEST_CONTACT},
                                             {'id': f['Address Type']['controlId'], 'value': [kind]},
                                             {'id': f['Active']['controlId'], 'value': 1}])))
        print(f'  created {TEST_CONTACT}: {rowid}')
    else:
        rowid = contact['rowid']
    C.remember('records', CON_KEY + TEST_CONTACT, rowid)

    def stored():
        d = hap.run('worksheet', 'record', 'get', con_ws(), rowid, '-a', APP)['data']
        state, country = relation(d.get('state_id')), relation(d.get('country_id'))
        return ((state[0][1] if state else None), (country[0][1] if country else None))

    def write(control, value):
        hap.run('worksheet', 'record', 'update', con_ws(), rowid, '-a', APP, '--fields-json',
                json.dumps([{'id': control['controlId'], 'value': value}]))

    def check(n, what, want):
        got = quiesce(stored)
        print(f"  {'OK  ' if got == want else 'DIFF'}  {n}. {what}: state {got[0]!r} country {got[1]!r}"
              + ('' if got == want else f' — want {want}'))
        if got != want:
            problems.append(f'{n}. {what}: {got} != {want}')

    write(rel, [])                                  # start from nothing, whatever a previous run left
    write(con_country, [])
    print(f'  {TEST_CONTACT} reset: {quiesce(stored)}')
    write(rel, [keyed['MY|MY-10']['rowid']])        # 1 · Selangor, no country yet
    check(1, 'E writes the Country from a new State', ('Selangor (MY)', 'Malaysia'))
    write(rel, [keyed['MY|MY-01']['rowid']])        # 2 · Johor, same country
    check(2, 'E leaves a State of the same country alone', ('Johor (MY)', 'Malaysia'))
    write(con_country, [by_name['Singapore']['rowid']])          # 3 · a country the state does not belong to
    check(3, 'F clears a State that belongs elsewhere', (None, 'Singapore'))
    write(rel, [keyed['ID|AC']['rowid']])                        # 4 · Aceh, Indonesia
    check(4, 'E moves the contact to the state\'s country', ('Aceh (ID)', 'Indonesia'))
    print('  selfcheck: ' + ('OK — E writes the Country from the State, leaves it alone when they already '
                             'agree, and F clears a State of another country'
                             if not problems else 'DIFFERENCES\n    ' + '\n    '.join(problems)))
    return len(problems)


# ── check ───────────────────────────────────────────────────────────────────

def roles_differences():
    """States' entry in the four business roles: the same cell each has for Contacts (§1 › Roles, owner
    18 Sep)."""
    import roles
    out = []
    if WORKSHEET not in roles.ORDER:
        return [f'roles.py ORDER does not carry {WORKSHEET}']
    live = {r['name']: r for r in roles.roles()}
    for name, (_, matrix) in roles.ROLES.items():
        want = matrix.get('Contacts')
        if matrix.get(WORKSHEET) != want:
            out.append(f'roles.py gives {name} {matrix.get(WORKSHEET)!r} on {WORKSHEET}, want {want!r} '
                       f'(its Contacts cell)')
        r = live.get(name)
        if not r:
            out.append(f'role {name!r} is missing')
            continue
        scope, add = roles.scopes(r['roleId']).get(WORKSHEET, (None, None))
        if roles.cell(scope, add) != want:
            out.append(f'{name} / {WORKSHEET}: {roles.cell(scope, add)!r}, want {want!r}')
    return out


def con_differences():
    """What this bundle put on Contacts, read back: the relation, the untouched views, the stand-in's absence
    and workflows E and F."""
    import contacts
    ctrls = hap.controls(con_ws())
    f = hap.by_name(c for c in ctrls if c['type'] != C.TAB)
    out = []
    rel = f.get(CON_FIELD)
    if not rel:
        return [f'Contacts has no {CON_FIELD} control']
    row, col, size = contacts.PLACE[CON_FIELD][:3]
    adv = rel.get('advancedSetting') or {}
    want = {'type': RELATION, 'alias': 'state_id', 'dataSource': ws(), 'enumDefault': 1, 'required': False,
            'sectionId': '', 'row': row, 'col': col, 'size': size, 'fieldPermission': '111'}
    diff = {k: (rel.get(k), v) for k, v in want.items() if rel.get(k) != v}
    if diff:
        out.append(f'Contacts / {CON_FIELD}: {diff}')
    if (adv.get('bidirectional'), adv.get('showtype')) != ('0', '3'):
        out.append(f"Contacts / {CON_FIELD}: bidirectional {adv.get('bidirectional')!r} showtype "
                   f"{adv.get('showtype')!r}, want '0' / '3' (one-way, a dropdown)")
    if standin(ctrls):
        out.append(f'the text stand-in {TEXT_STANDIN} is still on Contacts')
    if rel.get('sourceControlId') in {c['controlId'] for c in hap.controls(ws())}:
        out.append(f'{WORKSHEET} carries a reverse of {CON_FIELD}; the relation is meant to be one-way')
    naming = views_naming(rel['controlId'])
    if naming:                                      # §1: no view points at State
        out.append(f'a Contacts view names {CON_FIELD}: {naming}')
    for name in (WF_E, WF_F):
        pid = hap.ids().get('workflows', {}).get(name)
        if not pid:
            out.append(f'workflow {name!r} is not in ids.json')
            continue
        info = read('workflow', 'get', pid)
        cfg = read('workflow', 'config-get', pid)
        if not info.get('enabled') or info.get('publishStatus') != 2:
            out.append(f'{name}: enabled={info.get("enabled")} publishStatus={info.get("publishStatus")}')
        if cfg.get('triggerType') != NO_OTHER_WORKFLOWS:
            out.append(f'{name}: triggerType {cfg.get("triggerType")}, want {NO_OTHER_WORKFLOWS} (quiet)')
        proc = hap.run('workflow', 'node', 'list', pid)
        names = {n['name'] for n in proc['flowNodeMap'].values()}
        for wanted in (GET_STATE, GATEWAY, PATH_YES, PATH_NO, E_STEP if name == WF_E else F_STEP):
            if wanted not in names:
                out.append(f'{name}: no node {wanted!r}')
        trig = trigger_state(pid, proc['startEventId'])
        field = f[CON_FIELD] if name == WF_E else f['Country']
        if trig['fields'] != [field['controlId']]:
            out.append(f'{name}: trigger fields {trig["fields"]}, want {[field["controlId"]]}')
        if [c[2] for g in trig['condition'] for c in g] != ['7']:
            out.append(f'{name}: trigger condition {trig["condition"]}')
    return out


def cty_differences():
    """The reverse on Countries and the rewritten remark block."""
    ctrls = hap.controls(cty_ws())
    f = hap.by_name(ctrls)
    out = []
    forward = fields_of(ws()).get(COUNTRY)
    reverse = f.get(REVERSE)
    if not reverse:
        return [f'{COUNTRIES} has no {REVERSE} control']
    row, col, size = REVERSE_PLACE
    names = {c['controlId']: c['controlName'] for c in hap.controls(ws())}
    want = {'type': RELATION, 'alias': REVERSE_ALIAS, 'dataSource': ws(), 'enumDefault': 2, 'required': False,
            'sectionId': '', 'row': row, 'col': col, 'size': size, 'fieldPermission': REVERSE_PERMISSION,
            'sourceControlId': forward['controlId'], 'sourceControlType': 6, 'desc': REVERSE_DESC}
    diff = {k: (reverse.get(k), v) for k, v in want.items() if reverse.get(k) != v}
    if diff:
        out.append(f'{COUNTRIES} / {REVERSE}: {diff}')
    if (reverse.get('advancedSetting') or {}).get('showtype') != '2':
        out.append(f"{COUNTRIES} / {REVERSE}: showtype "
                   f"{(reverse.get('advancedSetting') or {}).get('showtype')!r}, want '2' (a list)")
    columns = [names.get(x, x) for x in reverse.get('showControls') or []]
    if columns != list(REVERSE_COLUMNS):
        out.append(f'{COUNTRIES} / {REVERSE}: columns {columns}, want {list(REVERSE_COLUMNS)}')
    if forward.get('controlId') != reverse.get('sourceControlId') or \
            forward.get('sourceControlId') != reverse.get('controlId'):
        out.append(f'{COUNTRIES} / {REVERSE}: the pair does not close '
                   f'({forward.get("sourceControlId")} vs {reverse.get("controlId")})')
    note = f.get(NOTE_NAME)
    if not note or note.get('dataSource') != NOTE_HTML:
        out.append(f'{COUNTRIES} / {NOTE_NAME}: the remark block still reads the old last line')
    return out


def step_check():
    """The controls with their places, permissions, descriptions and the title, the view, the roles' entry, the
    reverse on Countries and everything this bundle put on Contacts, against §1; non-zero on a difference."""
    ctrls = hap.controls(ws())
    f = hap.by_name(ctrls)
    names = {c['controlId']: c['controlName'] for c in ctrls}
    problems = []
    if set(f) != set(PLACE):
        problems.append(f'controls {sorted(set(f) ^ set(PLACE))}')
    problems += [f'{n}: {d}' for n, d in layout_differences(ctrls).items()]
    if f.get(DISPLAY, {}).get('attribute') != 1:
        problems.append('the title field is '
                        f'{next((c["controlName"] for c in ctrls if c.get("attribute") == 1), None)!r}')
    for name, kind in ((NAME, TEXT), (CODE, TEXT), (COUNTRY, RELATION), (DISPLAY, FORMULA),
                       (COUNTRY_CODE, LOOKUP), (STATE_KEY, FORMULA)):
        if f.get(name, {}).get('type') != kind:
            problems.append(f'{name} is type {f.get(name, {}).get("type")}, want {kind}')
    if f.get(COUNTRY, {}).get('dataSource') != cty_ws():
        problems.append(f'{COUNTRY} points at {f.get(COUNTRY, {}).get("dataSource")}, want {COUNTRIES}')
    if f.get(COUNTRY_CODE, {}).get('dataSource') != f"${f[COUNTRY]['controlId']}$":
        problems.append(f'{COUNTRY_CODE} reads through {f.get(COUNTRY_CODE, {}).get("dataSource")}')
    if f.get(COUNTRY_CODE, {}).get('strDefault') != '00':
        problems.append(f'{COUNTRY_CODE} strDefault {f.get(COUNTRY_CODE, {}).get("strDefault")!r}, want "00" '
                        '(stored)')
    views = {v['name']: C.view_info(ws(), APP, v['viewId'])
             for v in hap.listing('worksheet', 'view', 'list', ws(), '-a', APP)}
    if list(views) != [VIEW]:
        problems.append(f'views {list(views)}')
    v = views.get(VIEW, {})
    got = dict(columns=[names.get(x) for x in v.get('showControls', [])],
               sort=[(names.get(s['controlId']), s['isAsc']) for s in v.get('moreSort', [])],
               sortCid=names.get(v.get('sortCid')), sortType=v.get('sortType'),
               filters=[(names.get(x['controlId']), x['filterType']) for x in v.get('filters', [])],
               quick=[names.get(q['controlId']) for q in v.get('fastFilters', [])])
    want = dict(columns=list(COLUMNS), sort=[(CODE, True), (COUNTRY, True)], sortCid=CODE, sortType=2,
                filters=[], quick=[COUNTRY])
    if got != want:
        problems.append(f'view {VIEW}: {got} != {want}')
    if hap.listing('worksheet', 'custom-actions', ws()):
        problems.append('this worksheet has a button; §1 gives it none')
    if hap.listing('worksheet', 'rules', ws()):
        problems.append('this worksheet has a rule; §1 gives it none')
    problems += roles_differences()
    problems += cty_differences()
    problems += con_differences()
    print('  check: ' + ('OK — the six controls with their places, descriptions and permissions, Display Name '
                         'the title, the States view sorted State Code then Country with a Country quick '
                         'filter, the four business roles carrying States at their Contacts cell, Countries '
                         'holding the reverse list and the rewritten remark block, State key carrying No '
                         'duplicates (stored, never applied), and Contacts carrying the one-way relation in '
                         'place of the deleted text control with E and F published and quiet'
                         if not problems else 'DIFFERENCES\n    ' + '\n    '.join(problems)))
    return len(problems)


def step_all():
    for name in ('create', 'fields', 'reverse', 'views', 'roles', 'unique', 'seed', 'contacts', 'carry',
                 'retire', 'automations'):
        print(f'\n── {name} ' + '─' * 60)
        STEPS[name]()
    print('\n── check ' + '─' * 60)
    return step_check()


def show():
    C.show(ws())


STEPS = {
    'create': step_create,
    'fields': step_fields,
    'reverse': step_reverse,
    'views': step_views,
    'roles': step_roles,
    'unique': step_unique,
    'seed': step_seed,
    'contacts': step_contacts,
    'carry': step_carry,
    'retire': step_retire,
    'automations': step_automations,
    'all': step_all,
    'verify': step_verify,
    'check': step_check,
    'selfcheck': step_selfcheck,
    'deadrefs': step_deadrefs,
    'order': step_order,
    'state': step_state,
    'untouched': step_untouched,
    'show': show,
}

if __name__ == '__main__':
    step = sys.argv[1] if len(sys.argv) > 1 else 'check'
    if step not in STEPS:
        raise SystemExit(f"Unknown step {step!r}; choose from {', '.join(STEPS)}")
    result = STEPS[step](*sys.argv[2:])
    if step in ('verify', 'check', 'all', 'selfcheck', 'roles', 'carry', 'retire', 'deadrefs',
                'automations') and result:
        sys.exit(1)
