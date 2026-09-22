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
    ~/.hap-venv/bin/python nocoly/build/states.py views     # 3. States — the view that opens first: three
                                                            #    columns, State Code A→Z then Country, quick
                                                            #    filter Country
    ~/.hap-venv/bin/python nocoly/build/states.py dupview   # 3b. Duplicate codes — §1's second view: the same
                                                            #    three columns plus Duplicate code, filtered
                                                            #    to the states it is ticked on
    ~/.hap-venv/bin/python nocoly/build/states.py roles     # 4. roles.py's create step, which now carries this
                                                            #    worksheet into the four business roles
    ~/.hap-venv/bin/python nocoly/build/states.py key       # 1b. the State key **function formula** deleted
                                                            #    (owner-approved, 18 Sep) and rebuilt as a Text
                                                            #    control carrying No duplicates, beside the
                                                            #    read-only Duplicate code checkbox
    ~/.hap-venv/bin/python nocoly/build/states.py unique     # 5. where §1's Rules question stands: the switch
                                                            #    is on a Text control now, where HAP enforces it
    ~/.hap-venv/bin/python nocoly/build/states.py seed      # 6. the 2 102 states, every one read back, and §1's
                                                            #    digests
    ~/.hap-venv/bin/python nocoly/build/states.py contacts  # 7. the relation State on Contacts, in the text
                                                            #    stand-in's cell (row 8, right half)
    ~/.hap-venv/bin/python nocoly/build/states.py carry     # 8. the eight contacts' State text onto the
                                                            #    relation, read back
    ~/.hap-venv/bin/python nocoly/build/states.py retire    # 9. re-point the two address automations, delete the
                                                            #    text control, scan for the dead id
    ~/.hap-venv/bin/python nocoly/build/states.py automations # 10. workflows E and F on Contacts, both quiet
    ~/.hap-venv/bin/python nocoly/build/states.py duplicates # 11. workflow G on States: work the key out, look
                                                            #    for another state holding it, tick Duplicate
                                                            #    code, write the key. Quiet
    ~/.hap-venv/bin/python nocoly/build/states.py backfill  # 12. every state's key, and Duplicate code on the
                                                            #    ones that collide
    ~/.hap-venv/bin/python nocoly/build/states.py keys      # what the worksheet holds: keys, duplicates, and
                                                            #    every key read back one record at a time
                                                            #    (`keys sample` reads a dozen)
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
`automations` — E and F resolve "State" by name, and until the stand-in is gone that name is ambiguous. And
**`seed` before `duplicates`**: G fires on every create that carries a Country or a State Code, so building it
first would put 2 102 workflow runs through the organisation's quota to write keys that `backfill` writes
through the API in six minutes.

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
STATE_KEY = 'State key'                           # §1 › Rules: Odoo's unique(country_id, code) as one field —
                                                  # a **Text** control since 18 Sep 2026 (the formula that held
                                                  # the switch before it enforced nothing; the owner dropped it)
DUPLICATE = 'Duplicate code'                      # what a person actually sees: workflow G ticks it

# §1's form layout: State Name | State Code · Country | Display Name, then the read-only Duplicate code
# checkbox, with the two hidden controls under them (a hidden control still needs a place, as 08's Parent
# Complete Name has one). HAP puts the title field at the top of the record, so Display Name shows twice
# there, as Complete Name does on a category.
PLACE = {
    NAME: (0, 0, 6), CODE: (0, 1, 6),
    COUNTRY: (1, 0, 6), DISPLAY: (1, 1, 6),
    DUPLICATE: (2, 0, 6),
    COUNTRY_CODE: (3, 0, 6), STATE_KEY: (3, 1, 6),
}
HINTS = {}                                        # Odoo's state form has no placeholder on any field
DESC = {  # Odoo's help where it reads well for a user, else plain words — only what the field does
    # (owner's rule, 22 Sep 2026). Build notes and Odoo references: worksheets/12-states.md, foot.
    NAME: 'Administrative divisions of a country. E.g. Fed. State, Department, Canton',
    CODE: 'The state code.',
    DISPLAY: "How this state appears in lists and pickers: the State Name and the country's code in brackets, e.g. "
             '"Selangor (MY)".',
    COUNTRY_CODE: "The country's code.",
    STATE_KEY: '',
    DUPLICATE: 'Ticked when another state of the same country already has this State Code.',
}
REQUIRED = {NAME, CODE, COUNTRY}                  # Odoo: all three required on the model
UNIQUE = {STATE_KEY}                              # §1 › Rules; nothing else, and *not* State Code
# A hidden field never shows as a table column, so Display Name — the title — is read-only and hidden on create
# ("100") rather than hidden, as 01's, 04's, 08's and 09's are; Duplicate code is read-only the same way, and
# hidden on create because nothing has computed it yet. Country Code is hidden outright ("011"), and State key
# is hidden **and** read-only ("001"): nobody types a key.
PERMISSION = {DISPLAY: '100', DUPLICATE: '100', COUNTRY_CODE: '011', STATE_KEY: '001'}
ALIASES = {NAME: 'name', CODE: 'code', COUNTRY: 'country_id', DISPLAY: 'display_name',
           COUNTRY_CODE: 'country_code',          # country_code is a helper, not a field of res.country.state
           STATE_KEY: 'state_key',                # and so is state_key
           DUPLICATE: 'duplicate_code'}           # and so is duplicate_code
ADVANCED = {  # the advancedSetting keys this script owns
    COUNTRY: {'bidirectional': '1', 'showtype': '3'},        # two-way; 3 = a dropdown
    DISPLAY: {'analysislink': '1', 'sorttype': 'en'},
    DUPLICATE: {'showtype': '0'},                            # 0 = a checkbox, as Countries' two switches
}

# On Countries: the reverse of Country, the list Odoo draws at the foot of the country form.
REVERSE = 'States'
REVERSE_ALIAS = 'state_ids'
REVERSE_PLACE = (4, 0, 12)                        # under the remark block; a showtype-2 list renders as a tab
# Read-only — a state is given its country on the state — **and hidden on create** ("100") since 21 Sep 2026
# (15 §1): a "101" reverse renders on the Create Record form, where Odoo has no states list on a country that
# does not exist yet. "011" would take the table column with it; hidden-on-create does not (BUILDING.md), and
# PERMISSION above already carries "100" for two of this worksheet's own controls.
REVERSE_PERMISSION = '100'
REVERSE_COLUMNS = (NAME, CODE)                    # exactly Odoo's two columns there
REVERSE_DESC = 'The states of this country. To add one, set its Country on the state.'
# Countries' remark block, whose last line §1 rewrote once the States were there. Rewritten again for the app's
# users on 22 Sep 2026 (owner's rule): the same text as `countries.py` HTML, the Odoo text it replaced kept word for
# word at the foot of 11-countries.md.
NOTE_NAME = 'Country form note'
NOTE_HTML = ("<p>The country's name, codes and address settings. Its states are listed at the foot of the "
             'form.</p>')


def function_source(expression):
    """dataSource of a function formula (type 53), as contacts.py and prodcat.py write it."""
    return json.dumps({'type': 'mdfunction', 'expression': expression, 'status': 1}, ensure_ascii=False)


def display_expression(f):
    """Odoo _compute_display_name on res.country.state: f"{name} ({country_id.code})".

    The country's code is read through the stored lookup Country Code, the way 08's Complete Name reads Parent
    Complete Name. A number formula has no CONCAT of text, so this is a function formula."""
    return f"CONCAT(${f[NAME]['controlId']}$,\" (\",${f[COUNTRY_CODE]['controlId']}$,\")\")"


EXPRESSION = {DISPLAY: display_expression}


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
    problems += [f'unknown view {n!r}' for n in views - {VIEW, DUP_VIEW, 'All', '全部'}]
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
    # **State key and Duplicate code are `key`'s**, not this step's: the key was a function formula until
    # 18 Sep 2026, when the owner ruled that the formula be dropped because *No duplicates* on one enforces
    # nothing, and it is a Text control now (§1 › Rules, rewritten). `key` deletes the formula and builds the
    # two controls; both steps share the placing save below, which is driven by PLACE and reaches whatever is
    # live.
    return place_controls('places, permissions, descriptions and the title')


def place_controls(label):
    """One full save bringing every control that exists into PLACE's rows, aliases, descriptions, permissions
    and switches, and the title onto Display Name. Shared by `fields` and `key`: a control either step added
    arrives at row 9999 (`add-fields`) and only a full save places it."""
    ctrls, version = C.controls_with_version(ws())
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
        C.save_controls(ws(), ctrls, version=version)
        expect(before, f'{WORKSHEET}: {label}')
        print('  updated:', json.dumps(changed, ensure_ascii=False))
    left = layout_differences(hap.controls(ws()))
    if left:
        sys.exit(f'the controls read back with differences: {json.dumps(left, ensure_ascii=False)}')
    for c in hap.controls(ws()):
        C.remember('controls', KEY + c['controlName'], c['controlId'])
    C.show(ws())


def fields_of(worksheet_id):
    return hap.by_name(c for c in hap.controls(worksheet_id) if c['type'] != C.TAB)


# ── 1b · State key as a Text control, and the Duplicate code checkbox ────────

KEY_FORMULA = '6aace4a47d58b0f4493134f4'          # the function formula the owner dropped, 18 Sep 2026


def step_key():
    """§1's *Rules*, rewritten on 18 Sep 2026 after §3 test 7: **drop the State key function formula and build
    the pair that can actually do something.**

    The formula `6aace4a47d58b0f4493134f4` carried HAP's *No duplicates* and enforced nothing — not through
    the API (`selfcheck`) and not in the form (§3 test 7, in the browser). The owner's ruling was to drop it
    and enforce the pair some other way, and **this deletion is the owner's approval** (the second of this
    bundle, after Contacts' text stand-in); nothing else on this worksheet is ever deleted.

    In its place:

    * **State key**, a **Text** control — hidden and read-only ("001"), carrying *No duplicates*, holding
      `<country code>|<state code>`. On a Text control the switch is real: bundle 4 saw both a form save and
      an API write refused (`resultCode 11`). Nothing computes it; workflow **G** writes it (`duplicates`).
    * **Duplicate code**, a read-only checkbox on the form — what a person actually sees when G finds that
      another state of the same country already holds this code.

    Re-runnable: the deletion happens only while the formula is still there, each control is added only when
    it is missing, and the placing save writes only what differs."""
    guard()
    ctrls, version = C.controls_with_version(ws())
    old = next((c for c in ctrls if c['controlId'] == KEY_FORMULA), None)
    if old:
        if old['type'] != FORMULA or old['controlName'] != STATE_KEY:
            sys.exit(f'{KEY_FORMULA} is {old["controlName"]!r} type {old["type"]}, not the {STATE_KEY} formula '
                     f'— refusing to delete it')
        print('  backup:', hap.backup('states_controls_pre_key_deletion', ctrls))
        print(f'  deleting the {STATE_KEY} **function formula** {KEY_FORMULA} (type {old["type"]}, alias '
              f'{old.get("alias")!r}) — the owner-approved deletion of 18 Sep 2026: No duplicates on a formula '
              f'enforces nothing')
        before = snap()
        C.save_controls(ws(), [c for c in ctrls if c['controlId'] != KEY_FORMULA], version=version)
        expect(before, f'{WORKSHEET}: the {STATE_KEY} formula deleted (no other worksheet may change)')
        if next((c for c in hap.controls(ws()) if c['controlId'] == KEY_FORMULA), None):
            sys.exit('the formula is still there after the save')
        print(f'  deleted; {WORKSHEET} now has {len(hap.controls(ws()))} controls')
    f = fields_of(ws())
    if STATE_KEY not in f:
        # A Text control, appended without a controlId so the server mints one. `unique` — HAP's No duplicates
        # — is set here and read back by `check`; on a Text control it is enforced on API writes too.
        before = snap()
        C.append_controls(ws(), [C.control('TEXT', STATE_KEY, PLACE[STATE_KEY], alias=ALIASES[STATE_KEY],
                                           hint='', desc=DESC[STATE_KEY], unique=True)])
        expect(before, f'{WORKSHEET}: the {STATE_KEY} Text control added', new={WORKSHEET: {STATE_KEY}})
        print(f'  added: {STATE_KEY} (Text, No duplicates)')
    if DUPLICATE not in fields_of(ws()):
        before = snap()
        C.append_controls(ws(), [C.control('SWITCH', DUPLICATE, PLACE[DUPLICATE], alias=ALIASES[DUPLICATE],
                                           hint='', desc=DESC[DUPLICATE],
                                           advanced_setting=dict(ADVANCED[DUPLICATE]))])
        expect(before, f'{WORKSHEET}: the {DUPLICATE} checkbox added', new={WORKSHEET: {DUPLICATE}})
        print(f'  added: {DUPLICATE} (a checkbox, read-only on the form)')
    place_controls(f'{STATE_KEY} and {DUPLICATE} placed')
    f = fields_of(ws())
    key = f[STATE_KEY]
    if key['type'] != TEXT or not key.get('unique'):
        sys.exit(f'{STATE_KEY} read back type {key["type"]} unique {key.get("unique")!r}')
    print(f"  {STATE_KEY}: {key['controlId']} type {key['type']} (Text), unique {key.get('unique')!r}, "
          f"perm {key.get('fieldPermission')}, alias {key.get('alias')!r}")
    dup = f[DUPLICATE]
    print(f"  {DUPLICATE}: {dup['controlId']} type {dup['type']} (checkbox), perm "
          f"{dup.get('fieldPermission')}, alias {dup.get('alias')!r}")


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
DUP_VIEW = 'Duplicate codes'                      # §1's second view, added 18 Sep with the rebuilt check
DUP_COLUMNS = (NAME, CODE, COUNTRY, DUPLICATE)    # the same three, plus the tick itself


def step_views():
    """States, the view that opens first: every state, State Name · State Code · Country, sorted **State Code
    A→Z then Country** — Odoo's `_order = 'code, id'` with the country name standing in for the record id —
    and a **Country quick filter**, which is what Odoo's one group-by stands for.

    §1's second view is `dupview`'s and this step never touches it: it names only *States* to `upsert_views`
    and only *States* to `sort_views`, which leaves every view it is not given where it is.

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


# ── 3b · the Duplicate codes view ───────────────────────────────────────────

def step_dupview():
    """§1's second view: **Duplicate codes** — the states *Duplicate code* is ticked on.

    Odoo has no such view because its database refuses the second state outright; here the duplicate is
    created and then named by workflow **G**, and until this view there was nowhere to read the tick but the
    record itself. Columns are the States view's three plus the checkbox, sorted the same way, with the
    view's own filter **Duplicate code is checked** — the spec adapter's switch condition, the shape 02's
    *Archived* view uses on Active (`common.switch_filter`).

    It carries **no quick filter**, and the *States* view is not named here at all: this step sends only its
    own view to `upsert_views` and only the pair to `sort_views`, which keeps States opening first and leaves
    its columns, its sort and its Country quick filter exactly as `views` wrote them."""
    guard()
    f = fields_of(ws())
    if DUPLICATE not in f:
        sys.exit(f'{DUPLICATE} is not built — run `key` first')
    columns = [f[n]['controlId'] for n in DUP_COLUMNS]
    spec = dict(viewType='table', tableFields=columns, filter=C.switch_filter(f[DUPLICATE], 'eq'))
    views = {DUP_VIEW: (spec, C.sort_spec([f[CODE], f[COUNTRY]]), columns)}
    before = {v['name']: C.view_info(ws(), APP, v['viewId'])
              for v in hap.listing('worksheet', 'view', 'list', ws(), '-a', APP)}
    for name, vid in C.upsert_views(ws(), APP, views, 'states_views_pre_dupview').items():
        C.remember('views', KEY + name, vid)
    print('  order:', C.sort_views(ws(), APP, [VIEW, DUP_VIEW]))
    # the States view may not move: same columns, same sort, same quick filter, same filter
    after = {v['name']: C.view_info(ws(), APP, v['viewId'])
             for v in hap.listing('worksheet', 'view', 'list', ws(), '-a', APP)}
    keys = ('showControls', 'sortCid', 'sortType', 'moreSort', 'filters', 'fastFilters', 'advancedSetting')
    moved = [k for k in keys if (before.get(VIEW) or {}).get(k) != after[VIEW].get(k)]
    if VIEW in before and moved:
        sys.exit(f'the {VIEW} view changed: {moved}')
    print(f'  {VIEW}: unchanged ({len(keys)} attributes compared)')
    C.print_views(ws(), APP)
    names = {c['controlId']: c['controlName'] for c in hap.controls(ws())}
    v = after[DUP_VIEW]
    print(f"  {DUP_VIEW}: {v.get('viewId')} columns "
          f"{[names.get(x) for x in v.get('showControls') or []]} "
          f"filter {[(names.get(x['controlId']), x['filterType'], x.get('values')) for x in v.get('filters') or []]} "
          f"quick {[names.get(q['controlId']) for q in v.get('fastFilters') or []]}")
    listed = hap.run('worksheet', 'record', 'list', ws(), '-a', APP, '-n', '50', '--view-id', v['viewId'],
                     '--use-field-id-as-key')
    d = listed.get('data', listed) if isinstance(listed, dict) else listed
    rows_ = (d.get('rows') if isinstance(d, dict) else d) or []
    print(f'  it lists {len(rows_)}: ' + ', '.join(f"{r.get(f[NAME]['controlId'])!r} "
                                                   f"({r.get(f[CODE]['controlId'])})" for r in rows_))
    return 0


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
    """§1's *Rules*: where Odoo's `unique(country_id, code)` stands here.

    The first build put HAP's *No duplicates* on a hidden **function formula** of `country code + "|" + state
    code`. HAP stored the switch and enforced it nowhere — not through the API and not in the form (§3 test
    7) — and the owner ruled it out. It is a **Text** control now, written by workflow **G**.

    On a Text control the switch is real **on the open API**: a write of a value another record holds is
    refused with `resultCode 11` (bundle 4 on Countries' Country Code; `selfcheck` 0a here, and the backfill's
    2 104th key). It is **not** applied to a workflow's own update step — measured 18 Sep — so the pair is
    kept by G's shape rather than by the switch: the duplicate path ticks Duplicate code, clears the key and
    ends in an abort.

    This step reports what is stored; `selfcheck` drives what happens."""
    guard()
    f = fields_of(ws())
    key, dup = f.get(STATE_KEY), f.get(DUPLICATE)
    if not key or not dup:
        sys.exit(f'{STATE_KEY} / {DUPLICATE} are not built — run `key` first')
    print(f"  {STATE_KEY}: {key['controlId']} type {key['type']} "
          f"({'Text' if key['type'] == TEXT else 'NOT a Text control'}), unique reads {key.get('unique')!r}, "
          f"perm {key.get('fieldPermission')}, alias {key.get('alias')!r}")
    print(f"  {DUPLICATE}: {dup['controlId']} type {dup['type']} "
          f"({'a checkbox' if dup['type'] == SWITCH else 'NOT a checkbox'}), perm {dup.get('fieldPermission')}")
    pid = hap.ids().get('workflows', {}).get(WF_G)
    print(f"  workflow G {WF_G!r}: {pid or 'not built'}")
    problems = []
    if key['type'] != TEXT:
        problems.append(f'{STATE_KEY} is type {key["type"]}, not a Text control (2)')
    if not key.get('unique'):
        problems.append(f'{STATE_KEY} does not carry No duplicates')
    if any(c['controlId'] == KEY_FORMULA for c in hap.controls(ws())):
        problems.append(f'the old {STATE_KEY} formula {KEY_FORMULA} is still on the worksheet')
    for p in problems:
        print(f'  DIFF  {p}')
    if not problems:
        print(f'  Odoo unique(country_id, code) is carried by a **Text** control, written only by workflow G. '
              f'No duplicates on it refuses an **API** write ({STATE_KEY} resultCode 11) and is not applied to '
              f"G's own update step at all, so what keeps the key unique is G's shape — the duplicate path "
              f'ticks {DUPLICATE}, clears the key and ends in an abort, and never reaches the write.')
    return len(problems)


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
                         bool(x.get('isClear')), x.get('fieldValue') or '') for x in d.get('fields') or []])


def save_update(pid, node_id, name, select_node, fields, worksheet=None):
    """An update step writing exactly `fields` on the record `select_node` produced (payterms.save_update).

    A **text** entry taken from another node is stored as the template `$<nodeId>-<fieldId>$` in `fieldValue`
    with `nodeId` emptied, whichever shape it was sent in (BUILDING.md), so `fieldValue` is part of what is
    compared — otherwise a wrong template would read back as agreement."""
    worksheet = worksheet or con_ws()
    want = (select_node, worksheet, False,
            [(x['fieldId'], x.get('nodeId') or '', x.get('fieldValueId') or '', bool(x.get('isClear')),
              x.get('fieldValue') or '') for x in fields])
    s = step_state_of(pid, node_id)
    if (s['selectNodeId'], s['appId'], s['isException'], s['fields']) == want:
        return False
    hap.run('workflow', 'node', 'save', pid, node_id, '--type', '6', '-n', name, '-c', json.dumps(
        {'actionId': '2', 'appId': worksheet, 'appType': 1, 'selectNodeId': select_node, 'fields': fields},
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


# ── 11 · workflow G: the key and the duplicate check ────────────────────────

WF_G = 'States: the key and the duplicate check'
G_TRIGGER = "When a state's Country or State Code is written"
GET_COUNTRY = 'Get the country'
KEY_STEP = 'Work out the key'
FIND_STEP = 'Another state with this key?'
DUP_GATEWAY = 'Is there one?'
PATH_DUP = 'Yes — another state already holds this key'
PATH_FREE = 'No — this key is free'
TICK_STEP = f'Tick {DUPLICATE}'
UNTICK_STEP = f'Untick {DUPLICATE}'
CLEAR_STEP = f'Clear the {STATE_KEY}'
STOP_STEP = 'Stop — a duplicate gets no key'
WRITE_KEY_STEP = f'Write the {STATE_KEY}'
G_NODES = (GET_COUNTRY, KEY_STEP, FIND_STEP, DUP_GATEWAY, PATH_DUP, PATH_FREE, TICK_STEP, UNTICK_STEP,
           CLEAR_STEP, STOP_STEP, WRITE_KEY_STEP)
ABORT = 30                                        # flowNodeType 中止流程 — the only way to stop a run inside
STRING_FX = 'string_fx_id'                        # a function formula node's own text result
EQ, NE, NOT_EMPTY = '9', '10', '7'                # workflow conditionIds: 等于 · 不等于 · 不为空


def key_formula(f, cty_f):
    """`<country code>|<state code>` — Odoo's own natural key, the pair `unique(country_id, code)` is on.

    The country's code is read from the **country record** the first step fetched rather than from the hidden
    stored lookup on the state: the lookup is a value HAP recomputes on save and the run would be reading it
    at the moment it is being written, where the country record is simply there. A workflow formula compares
    with `==` and concatenates with CONCAT (`+` would concatenate as text and then read the result as octal —
    BUILDING.md), and neither half can contain a bar, so two different pairs cannot collide."""
    return (f"CONCAT($country-{cty_f['Country Code']['controlId']}$,\"|\",$trigger-{f[CODE]['controlId']}$)")


def g_nodes(f):
    """The chain `batch-add` makes. Its search filter and sort and its branch-path conditions are written
    again afterwards: batch-add sends `operateCondition`, which the UI never reads, and no sort at all.

    **The tick comes before the key write, and they are two steps** — §1 asks for the split, so that a
    refused key write cannot take the tick with it.

    **And the duplicate path ends in an abort** (中止流程, node type 30), so the run never reaches the key
    write at all. That is not belt and braces: a workflow's update step is **not** subject to *No duplicates*
    — measured on 18 Sep, the same write the open API refuses with `resultCode 11` is accepted from a step,
    and two states were left holding `MY|ZZ-01` — so nothing but this workflow's own shape keeps the key
    unique. A branch converges, so an empty path is not a stop (BUILDING.md); only the abort is. The
    duplicate path therefore reads **tick · clear the key · stop**, and the invariant it keeps is: *a state
    holds the key its own code implies, or holds none and carries Duplicate code.*"""
    tick = lambda alias, name, value: {
        'nodeAlias': alias, 'nodeType': 'update_record', 'name': name,
        'config': {'target': {'node': {'nodeAlias': 'trigger'}}, 'worksheet': ws(),
                   'fields': [{'fieldId': f[DUPLICATE]['controlId'], 'type': SWITCH, 'value': value}]}}
    clear = {'nodeAlias': 'clear', 'nodeType': 'update_record', 'name': CLEAR_STEP,
             'config': {'target': {'node': {'nodeAlias': 'trigger'}}, 'worksheet': ws(), 'fields': []}}
    return [
        {'nodeAlias': 'country', 'nodeType': 'get_relation', 'name': GET_COUNTRY,
         'config': {'target': {'node': {'nodeAlias': 'trigger'}},
                    'fields': [{'fieldId': f[COUNTRY]['controlId']}], 'worksheet': cty_ws()}},
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
    """The search step's filter: a state whose **State key** is the key just worked out and which is **not**
    the record that started the run.

    The self-exclusion is what makes the check safe to re-run: a field-narrowed trigger fires whenever one of
    its fields is in the write, changed or not (BUILDING.md), so a save that re-sends an unchanged State Code
    would otherwise find the record's own key and call it a duplicate. `conditionId` 10 is 不等于, and Record
    ID is a text field (`filedId` "rowid", `filedTypeId` 2), the same shape as the Record-ID *equals* every
    other search step here uses."""
    return [
        {'nodeId': node_id, 'nodeType': 7, 'actionId': '406', 'filedId': key_field['controlId'],
         'filedValue': STATE_KEY, 'filedTypeId': TEXT, 'enumDefault': 0, 'conditionId': EQ, 'sourceType': 0,
         'conditionValues': [{'nodeId': key_node, 'controlId': STRING_FX, 'value': ''}]},
        {'nodeId': node_id, 'nodeType': 7, 'actionId': '406', 'filedId': 'rowid', 'filedValue': 'Record ID',
         'filedTypeId': TEXT, 'enumDefault': 0, 'conditionId': NE, 'sourceType': 0,
         'conditionValues': [{'nodeId': trigger, 'controlId': 'rowid', 'value': '', 'sureNodeId': trigger}]},
    ]


def save_search(pid, node, worksheet, conditions, execute_type=2, sorts=None):
    """A search node's filter and sort the way the UI stores them — `filters`, not the `operateCondition`
    batch-add sends and the UI never reads (invlines.save_search)."""
    got = node_get(pid, node['id'])
    shape = lambda groups: [[{k: c.get(k) for k in ('filedId', 'conditionId')} for c in g] for g in groups]
    live = shape([g for flt in got.get('filters') or [] for g in flt.get('conditions') or []])
    want_sorts = sorts or [{'controlId': 'ctime', 'controlType': 16, 'isAsc': True}]
    if (got.get('appId') == worksheet and live == shape([conditions])
            and [(s.get('controlId'), s.get('isAsc')) for s in got.get('sorts') or []]
            == [(s['controlId'], s['isAsc']) for s in want_sorts]):
        return False
    hap.run('workflow', 'node', 'save', pid, node['id'], '--type', '7', '-n', node['name'], '-c', json.dumps(
        {'actionId': '406', 'appId': worksheet, 'selectNodeId': '',
         'filters': [{'spliceType': 2, 'conditions': [conditions]}], 'sorts': want_sorts,
         'executeType': execute_type}, ensure_ascii=False))
    got = node_get(pid, node['id'])
    if shape([g for flt in got.get('filters') or [] for g in flt.get('conditions') or []]) != shape([conditions]):
        sys.exit(f"{node['name']}: the filter read back {got.get('filters')}")
    return True


def set_formula(pid, node, expression):
    """A function formula node's expression, read back — a wrong one is stored and computes empty
    (invoices.set_formula; `type` 2 is a text result)."""
    if node_get(pid, node['id']).get('formulaValue') == expression:
        return False
    hap.run('workflow', 'node', 'save', pid, node['id'], '--type', '9', '-n', node['name'], '-c', json.dumps(
        {'actionId': '106', 'name': node['name'], 'execute': True, 'formulaValue': expression, 'type': 2},
        ensure_ascii=False))
    if node_get(pid, node['id']).get('formulaValue') != expression:
        sys.exit(f"{node['name']}: expression read back "
                 f"{node_get(pid, node['id']).get('formulaValue')!r}, want {expression!r}")
    return True


def save_path(pid, path, name, conditions):
    """A branch path's name and condition (invoices.save_path): `node get` answers `conditions`, `node save
    --type 2` wants `operateCondition`, and batch-add drops the name."""
    got = node_get(pid, path['id'])
    changed = condition_shape(got.get('conditions')) != condition_shape(conditions)
    if changed:
        hap.run('workflow', 'node', 'save', pid, path['id'], '--type', '2', '-n', name,
                '-c', json.dumps({'operateCondition': conditions}, ensure_ascii=False))
        if condition_shape(node_get(pid, path['id']).get('conditions')) != condition_shape(conditions):
            sys.exit(f'{name}: the condition read back {node_get(pid, path["id"]).get("conditions")}')
    if path.get('name') != name:
        hap.run('workflow', 'node', 'rename', pid, path['id'], '-n', name)
        changed = True
    return changed


def step_duplicates():
    """**G** — *States: the key and the duplicate check*, §1's *Rules* as a workflow.

    On create, and whenever **Country** or **State Code** is in a write, G works the key out, looks for
    another state that already holds it, ticks (or unticks) **Duplicate code**, and writes the key:

      1. **Get the country** — the trigger's Country, so the country's own code is read from the country;
      2. **Work out the key** — a text function formula, `<country code>|<state code>`;
      3. **Another state with this key?** — a search of States, State key = that, Record ID ≠ the trigger,
         oldest first, carrying on when nothing is found;
      4. **Is there one?** — an exclusive gateway. The conditioned path is *yes* (the found state's State key
         is not empty) and ticks Duplicate code; the default path unticks it. A branch converges, so both run
         on into
      5. **Write the State key** — which HAP refuses when the key is a duplicate, *after* the tick is in.

    §1 asks only for the tick; the untick is this build's addition, and it is what makes the pair honest when
    a duplicate is fixed by re-coding the state. G is **quiet** (`triggerType` 2): it writes Duplicate code
    and State key on its own worksheet, and neither is one of its trigger fields, but a quiet workflow starts
    nothing anywhere and that is the standing rule for a workflow writing its own record."""
    guard()
    f = fields_of(ws())
    cty_f = hap.by_name(hap.controls(cty_ws()))
    for name in (STATE_KEY, DUPLICATE):
        if name not in f:
            sys.exit(f'{name} is not built — run `key` first')
    ids = hap.ids()
    pid = ids.setdefault('workflows', {}).get(WF_G)
    if not pid:
        live = {w.get('name'): (w.get('id') or w.get('processId')) for w in hap.listing('workflow', 'list', APP)}
        pid = live.get(WF_G)          # `workflow create` can time out having created it (BUILDING.md)
    desc = ("Odoo's constraint unique(country_id, code) on res.country.state, as far as HAP can carry it: the "
            'key is worked out and written to the hidden State key, which carries No duplicates, and a state '
            'whose key another state already holds is marked with Duplicate code. HAP runs a workflow after '
            'the save, so the duplicate is created and then named — Odoo refuses it outright.')
    if not pid:
        out = hap.run('workflow', 'create', '-c', ids['org'], '-n', WF_G, '-a', APP, '--type', 'worksheet',
                      '-d', desc)
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
                '--trigger-fields', ','.join([f[COUNTRY]['controlId'], f[CODE]['controlId']]),
                '--trigger-alias', 'trigger')
        print('  G: steps added')
        changed = True
        proc = hap.run('workflow', 'node', 'list', pid)
        by_name = {n['name']: n for n in proc['flowNodeMap'].values()}
    if CLEAR_STEP not in by_name and TICK_STEP in by_name:
        # Added after the first cut, inside the duplicate path and after the tick: `batch-add` appends to an
        # existing chain when it is given that chain's last node (BUILDING.md).
        hap.run('workflow', 'node', 'batch-add', pid, '--trigger-node-id', by_name[TICK_STEP]['id'],
                '--trigger-alias', 'tick', '--nodes', json.dumps(
                    [{'nodeAlias': 'clear', 'nodeType': 'update_record', 'name': CLEAR_STEP,
                      'config': {'target': {'node': {'nodeAlias': 'tick'}}, 'worksheet': ws(),
                                 'fields': []}}], ensure_ascii=False))
        print(f'  G: {CLEAR_STEP!r} added after {TICK_STEP!r}')
        changed = True
        proc = hap.run('workflow', 'node', 'list', pid)
        by_name = {n['name']: n for n in proc['flowNodeMap'].values()}
    if STOP_STEP not in by_name and CLEAR_STEP in by_name:
        # 中止流程 has no builder in hap-cli's DSL (`batch-add` cannot make one): add it by hand, last in the
        # duplicate path, so the run stops before the key write a duplicate must never reach.
        hap.run('workflow', 'node', 'add', pid, '--type', str(ABORT), '-n', STOP_STEP,
                '--after', by_name[CLEAR_STEP]['id'])
        print(f'  G: {STOP_STEP!r} (中止流程) added after {CLEAR_STEP!r}')
        changed = True
        proc = hap.run('workflow', 'node', 'list', pid)
        by_name = {n['name']: n for n in proc['flowNodeMap'].values()}
    for name in (GET_COUNTRY, KEY_STEP, FIND_STEP, DUP_GATEWAY, TICK_STEP, UNTICK_STEP, CLEAR_STEP,
                 STOP_STEP, WRITE_KEY_STEP):
        if name not in by_name:
            sys.exit(f'G: the workflow has no node {name!r} — {sorted(by_name)}')
    # 1 · the trigger: States, 新增或更新, narrowed to Country and State Code, no condition
    want_fields = sorted([f[COUNTRY]['controlId'], f[CODE]['controlId']])
    want_trigger = dict(name=G_TRIGGER, appId=ws(), fields=want_fields, condition=[])
    if trigger_state(pid, start) != want_trigger:
        trig = node_get(pid, start)
        hap.run('workflow', 'node', 'save', pid, start, '--type', '0', '-n', G_TRIGGER, '-c', json.dumps(
            {'appId': ws(), 'appType': 1, 'triggerId': trig.get('triggerId'), 'assignFieldIds': want_fields,
             'operateCondition': [], 'returns': []}, ensure_ascii=False))
        if trigger_state(pid, start)['name'] != G_TRIGGER:
            hap.run('workflow', 'node', 'rename', pid, start, '-n', G_TRIGGER)
        got = trigger_state(pid, start)
        if got != want_trigger:
            sys.exit(f'G: trigger read back {got}, want {want_trigger}')
        print('  G: trigger rewritten')
        changed = True
    # 2 · the key formula, over the country step and the trigger record
    node_ids = {'trigger': start, 'country': by_name[GET_COUNTRY]['id'], 'key': by_name[KEY_STEP]['id']}
    expression = key_formula(f, cty_f).replace('$trigger-', f"${node_ids['trigger']}-") \
                                      .replace('$country-', f"${node_ids['country']}-")
    changed |= set_formula(pid, by_name[KEY_STEP], expression)
    # 3 · the search: another state holding that key, oldest first
    changed |= save_search(pid, by_name[FIND_STEP], ws(),
                           key_search_filter(by_name[FIND_STEP]['id'], f[STATE_KEY], node_ids['key'], start))
    # 4 · the gateway's two paths: the condition on the duplicate one, none on the default
    gate = by_name[DUP_GATEWAY]
    nodes = proc['flowNodeMap']
    paths = [nodes[i] for i in gate.get('flowIds') or []]
    if len(paths) != 2:
        sys.exit(f'G: the gateway has {len(paths)} paths, want 2')
    dup_path = next((p for p in paths if nodes.get(p.get('nextId') or '', {}).get('name') == TICK_STEP), None)
    free_path = next((p for p in paths if p is not dup_path), None)
    if not dup_path or nodes.get(free_path.get('nextId') or '', {}).get('name') != UNTICK_STEP:
        sys.exit(f'G: the gateway paths do not lead to {TICK_STEP!r} and {UNTICK_STEP!r}')
    found_key = [[{'nodeId': by_name[FIND_STEP]['id'], 'filedId': f[STATE_KEY]['controlId'],
                   'filedValue': STATE_KEY, 'filedTypeId': TEXT, 'enumDefault': 0, 'conditionId': NOT_EMPTY,
                   'sourceType': 0, 'conditionValues': []}]]
    changed |= save_path(pid, dup_path, PATH_DUP, found_key)
    changed |= save_path(pid, free_path, PATH_FREE, [])
    if node_get(pid, free_path['id']).get('conditions'):
        sys.exit(f'G: the else path {PATH_FREE!r} carries a condition; it must have none')
    # 5 · the two ticks and the key write
    for node_name, value in ((TICK_STEP, '1'), (UNTICK_STEP, '0')):
        changed |= save_update(pid, by_name[node_name]['id'], node_name, start,
                               [{'fieldId': f[DUPLICATE]['controlId'], 'type': SWITCH, 'addType': 0,
                                 'fieldValue': value, 'fieldValueId': '', 'nodeId': ''}], worksheet=ws())
    # `isClear` is the editor's 清空: sent as a plain empty value the entry is dropped on save (BUILDING.md)
    changed |= save_update(pid, by_name[CLEAR_STEP]['id'], CLEAR_STEP, start,
                           [{'fieldId': f[STATE_KEY]['controlId'], 'type': TEXT, 'addType': 0,
                             'fieldValue': '', 'fieldValueId': '', 'nodeId': '', 'isClear': True}],
                           worksheet=ws())
    changed |= save_update(pid, by_name[WRITE_KEY_STEP]['id'], WRITE_KEY_STEP, start,
                           [{'fieldId': f[STATE_KEY]['controlId'], 'type': TEXT, 'addType': 0,
                             'fieldValue': f"${node_ids['key']}-{STRING_FX}$", 'fieldValueId': '',
                             'nodeId': ''}], worksheet=ws())
    # 6 · quiet, then publish
    changed |= ensure_quiet(pid, 'G')
    info = read('workflow', 'get', pid)
    if (info.get('explain') or '') != desc:
        hap.run('workflow', 'update', pid, '-n', WF_G, '-d', desc)
        changed = True
    if changed or not info.get('enabled') or info.get('publishStatus') != 2:
        result = C.publish(pid)
        print(f'  G: published {result}')
        if not result.get('isPublish'):
            sys.exit(f'G: publish failed: {result}')
    print(C.structure(pid))
    print(f"  G {WF_G}: {pid} — trigger {trigger_state(pid, start)}, quiet "
          f"{read('workflow', 'config-get', pid).get('triggerType')}")
    return 0


# ── 12 · the backfill ───────────────────────────────────────────────────────

def key_column():
    """State key and Duplicate code by rowid, for every state.

    A **hidden** control comes back from `GetFilterRows` as the empty string whatever it holds — the hidden
    Country Code lookup does, and State key is hidden too — so the keys cannot be read from the list. What
    the list *can* do is answer a filter, which is how the backfill finds its work in one call: the states
    whose State key **is empty**. Duplicate code is a switch and the list returns it."""
    f = fields_of(ws())
    from hap_cli.core import record as rec
    s = session()
    empty, page = set(), 1
    while True:
        got = rec.get_records(s, ws(), page_size=1000, page_index=page,
                              filters=[C.cond(f[STATE_KEY], C.EMPTY)])['data'] or []
        empty |= {r['rowid'] for r in got}
        if len(got) < 1000:
            break
        page += 1
    ticked, page = set(), 1
    while True:
        got = rec.get_records(s, ws(), page_size=1000, page_index=page,
                              filters=[C.cond(f[DUPLICATE], C.EQ, 1)])['data'] or []
        ticked |= {r['rowid'] for r in got}
        if len(got) < 1000:
            break
        page += 1
    return empty, ticked


def wanted_keys():
    """{rowid: (key, ctime, name)} for every live state — the key Odoo's natural key gives it."""
    f = fields_of(ws())
    by_rowid, _ = countries()
    out = {}
    for r in rows(ws()):
        linked = relation(r.get(f[COUNTRY]['controlId']))
        code = by_rowid.get(linked[0][0], {}).get('code') if linked else None
        out[r['rowid']] = (f"{code}|{r.get(f[CODE]['controlId']) or ''}" if code else None,
                           r.get('ctime') or '', r.get(f[NAME]['controlId']) or '')
    return out


def write_field(rowid, control, value):
    """One `record update` through the session; returns (ok, resultCode, message)."""
    from hap_cli.core import record as rec
    try:
        rec.update_record(session(), ws(), rowid,
                          [{'controlId': control['controlId'], 'value': value}], trigger_workflow=True)
        return True, 1, ''
    except Exception as error:                      # hap_cli raises APIError on resultCode != 1
        return False, getattr(error, 'code', None), str(error)[:200]


def step_backfill(*only):
    """Give all 2 102 seeded states their **State key**, and tick **Duplicate code** on the ones that collide.

    The keys are written through the API rather than by re-saving every state and waiting for G: a write of
    State key alone carries neither of G's trigger fields, so it starts nothing, and 2 100 workflow runs
    would be an hour of quota. What G does on one record is proved in `selfcheck`.

    The order is Odoo's: the **oldest** state holding a key keeps it, and a state created later with a key
    another already holds is the duplicate. Nothing is ever written twice — a state that already holds its
    key is skipped, so a second run writes nothing at all."""
    guard()
    f = fields_of(ws())
    want, (empty, ticked) = wanted_keys(), key_column()
    bad = sorted(r for r, (k, _, _) in want.items() if not k)
    if bad:
        print(f'  {len(bad)} states have no country and so no key: {bad[:5]}')
    claimed = {}                                    # key -> the rowid that holds it
    for rowid, (key, _, _) in want.items():
        if key and rowid not in empty:
            claimed.setdefault(key, rowid)
    todo = sorted((r for r in empty if want.get(r, (None,))[0]), key=lambda r: (want[r][1], want[r][2]))
    if only:
        todo = [r for r in todo if want[r][0].split('|')[0] in only]
    print(f'  {len(want)} states; {len(empty)} without a key; {len(ticked)} already ticked; '
          f'{len(todo)} to write')
    wrote, marked, refused = 0, [], []
    started = time.time()
    for i, rowid in enumerate(todo, 1):
        key, ctime, name = want[rowid]
        if key in claimed:                          # an older state already holds it: this one is the duplicate
            if rowid in ticked:
                print(f'  DUPLICATE {name!r} ({key}) is already marked — nothing to write')
                continue
            ok, code, message = write_field(rowid, f[DUPLICATE], 1)
            marked.append((name, key, claimed[key]))
            if name.startswith('TEST'):            # a marked TEST record is worth pointing at from §2
                C.remember('records', KEY + name, rowid)
            print(f'  DUPLICATE {name!r} ({ctime}) holds {key}, which {claimed[key]} already has — '
                  f'{DUPLICATE} ticked ({"ok" if ok else f"REFUSED {code} {message}"})')
            probe = write_field(rowid, f[STATE_KEY], key)
            refused.append((name, key, probe))
            print(f'            the key write on it: '
                  f'{"ACCEPTED — No duplicates did not fire" if probe[0] else f"refused, resultCode {probe[1]}"}')
            continue
        ok, code, message = write_field(rowid, f[STATE_KEY], key)
        if not ok:
            sys.exit(f'{name!r}: the key {key} was refused (resultCode {code}) although nothing claims it — '
                     f'{message}')
        claimed[key] = rowid
        wrote += 1
        if i % 200 == 0 or i == len(todo):
            print(f'  {i}/{len(todo)} ({time.time() - started:.0f}s)')
    print(f'  backfill: {wrote} keys written, {len(marked)} duplicates marked')
    for name, key, holder in marked:
        print(f'    {DUPLICATE} ticked on {name!r} ({key}; first holder {holder})')
    for name, key, (ok, code, message) in refused:
        print(f'    the API on {name!r}: writing {key} a second time was '
              f'{"ACCEPTED — No duplicates did not fire" if ok else f"refused, resultCode {code}"}')
    return step_keys()


def step_keys(*only):
    """What the worksheet holds: how many states carry a key, which carry Duplicate code, and — read one
    record at a time, because a hidden control is blanked in the list — that every key is
    `<country code>|<state code>`. `keys sample` checks a handful instead of all 2 100."""
    f = fields_of(ws())
    want = wanted_keys()
    empty, ticked = key_column()
    print(f'  {len(want)} states: {len(want) - len(empty)} carry a {STATE_KEY}, {len(empty)} do not, '
          f'{len(ticked)} carry {DUPLICATE}')
    for rowid in sorted(empty, key=lambda r: want.get(r, ('', '', ''))[2]):
        key, ctime, name = want.get(rowid, (None, '', '?'))
        print(f'    no key:  {name!r} ({key}) created {ctime} — ticked={rowid in ticked}')
    for rowid in sorted(ticked, key=lambda r: want.get(r, ('', '', ''))[2]):
        key, ctime, name = want.get(rowid, (None, '', '?'))
        print(f'    ticked:  {name!r} ({key}) created {ctime} — key stored='
              f'{row_detail(ws(), rowid).get(f[STATE_KEY]["controlId"])!r}')
    sample = 'sample' in only
    check = [r for r in want if r not in empty]
    if sample:
        check = sorted(check, key=lambda r: want[r][2])[:12]
    bad, started = {}, time.time()
    for i, rowid in enumerate(check, 1):
        got = row_detail(ws(), rowid).get(f[STATE_KEY]['controlId'])
        if got != want[rowid][0]:
            bad[want[rowid][2]] = (got, want[rowid][0])
        if not sample and (i % 400 == 0 or i == len(check)):
            print(f'    read {i}/{len(check)} ({time.time() - started:.0f}s)')
    print(f'  {len(check)} keys read back one by one{" (sample)" if sample else ""}: '
          f'{len(bad)} differing {json.dumps(bad, ensure_ascii=False)[:300]}')
    unmarked = sorted(want.get(r, (None, '', '?'))[2] for r in empty if r not in ticked)
    if unmarked:                                    # a state with no key that nobody calls a duplicate
        print(f'  DIFF  {len(unmarked)} states carry neither a key nor {DUPLICATE}: {unmarked[:10]}')
    keyed_but_ticked = sorted(want.get(r, (None, '', '?'))[2] for r in ticked if r not in empty)
    if keyed_but_ticked:                            # the original of a pair, wrongly marked
        print(f'  DIFF  {len(keyed_but_ticked)} states carry both a key and {DUPLICATE}: {keyed_but_ticked}')
    return len(bad) + len(unmarked) + len(keyed_but_ticked)


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


TEST_DUP = 'TEST State Duplicate Two'              # selfcheck's own duplicate; created once, left in States
FREE_CODE = 'ZZ-09'                                # a code no state holds: the "this key is free" half of G


def runs_since(pid, known, want=1, seconds=90, settle=4):
    """The runs of `pid` that started since `known` (a set of instance ids), once `want` of them have finished.

    A run registers about five seconds after the write that starts it, and the listing lags, so runs are told
    apart by **instance id** and never by position (accounts.wait_new_runs)."""
    deadline = time.time() + seconds
    while True:
        got = (hap.run('approval', 'history', '--process-id', pid, '-n', '20') or {}).get('data') or []
        new = [r for r in got if r['id'] not in known]
        if (len(new) >= want and all(r.get('status') != 1 for r in new)) or time.time() > deadline:
            if new and settle:
                time.sleep(settle)
                got = (hap.run('approval', 'history', '--process-id', pid, '-n', '20') or {}).get('data') or []
                new = [r for r in got if r['id'] not in known]
            return new
        time.sleep(3)


def run_report(runs):
    """What each run did, node by node — the only way to see that a step was reached and what it answered."""
    out = []
    for r in runs:
        d = hap.run('approval', 'history-detail', r['id'])
        d = d.get('data', d) if isinstance(d, dict) else {}
        nodes = [((w.get('flowNode') or {}).get('name'), w.get('status'))
                 for w in d.get('works') or []]
        out.append(f"status {r.get('status')} cause {(r.get('instanceLog') or {}).get('cause')} "
                   f"{(r.get('instanceLog') or {}).get('causeMsg') or ''} :: "
                   + ' → '.join(f'{n}[{s}]' for n, s in nodes))
    return out


def duplicate_probe():
    """§1's rewritten *Rules*, driven through the CLI: **what HAP does with a duplicate now.**

    Five questions, in the order they matter:

    0a. the **API** refuses a duplicate written into the unique Text control (`resultCode 11`), where the
        formula it replaced accepted everything;
    0b. a **create** that does not send the key — the shape of a form save, since the form never renders a
        hidden read-only control — is **accepted**, so the duplicate record still exists, and G runs on it;
    0c. a free code: G unticks Duplicate code and writes the key, and the run completes (status 2);
    0d. a code another state holds: G ticks Duplicate code, clears the key and **stops** (status 3, 中止).
        The stop is what keeps the key unique — a workflow's update step is *not* checked against No
        duplicates (the first cut of G wrote `MY|ZZ-01` onto a second state and HAP took it, 18 Sep), so the
        run must never reach the write rather than rely on being refused;
    0e. a save that re-sends an **unchanged** State Code does **not** mark the record as its own duplicate —
        the search step excludes the record that started the run.
    """
    f = fields_of(ws())
    pid = hap.ids().get('workflows', {}).get(WF_G)
    if not pid:
        return [f'workflow G {WF_G!r} is not built']
    live = {r.get(f[NAME]['controlId']): r['rowid'] for r in rows(ws())}
    problems = []
    state = lambda rowid: (lambda d: (d.get(f[STATE_KEY]['controlId']) or '',
                                      str(d.get(f[DUPLICATE]['controlId']) or '0') in ('1', 'true')))(
        row_detail(ws(), rowid))
    one = live.get('TEST State One')
    two = live.get('TEST State Two')
    if not one or not two:
        return ['the TEST states of the build are gone — the duplicate probe is skipped']
    # 0a · the API refuses a duplicate key on the Text control
    one_key, _ = state(one)
    refused, message = attempt('worksheet', 'record', 'update', ws(), two, '-a', APP, '--fields-json',
                               json.dumps([{'id': f[STATE_KEY]['controlId'], 'value': one_key}]))
    print(f"  {'OK  ' if refused else 'DIFF'}  0a. a {STATE_KEY} another state holds, written through the API: "
          f"{'refused' if refused else 'ACCEPTED'} — {message[:150]}")
    if not refused:
        problems.append(f'0a. No duplicates on the {STATE_KEY} Text control did not refuse an API write')
    # 0b · a create that does not carry the key — what a form save sends — is accepted
    known = {r['id'] for r in (hap.run('approval', 'history', '--process-id', pid, '-n', '20')
                               or {}).get('data') or []}
    dup = live.get(TEST_DUP)
    if not dup:
        by_rowid, by_name = countries()
        created = hap.run('worksheet', 'record', 'create', ws(), '-a', APP, '--fields-json', json.dumps(
            [{'id': f[NAME]['controlId'], 'value': TEST_DUP},
             {'id': f[CODE]['controlId'], 'value': TEST_STATES['TEST State One']},
             {'id': f[COUNTRY]['controlId'], 'value': [by_name['Malaysia']['rowid']]}]))
        dup = C.row_id(created)
        print(f'  OK    0b. a second Malaysian {TEST_STATES["TEST State One"]} **created** through the API '
              f'with no {STATE_KEY} in the write: accepted, {dup} — nothing in HAP refuses the record itself, '
              f'and a form sends no hidden read-only control either')
        for line in run_report(runs_since(pid, known, want=1)):
            print(f'        G on the create: {line}')
    else:
        print(f'  OK    0b. {TEST_DUP} is already there ({dup}) — the create was accepted on an earlier run')
    C.remember('records', KEY + TEST_DUP, dup)
    # 0c/0d · drive G over it: a free code, then back onto the duplicate
    for label, code, want_dup, want_key, want_status in (
            (f'0c. a free code ({FREE_CODE}) unticks {DUPLICATE} and the key is written', FREE_CODE, False,
             f'MY|{FREE_CODE}', 2),
            (f'0d. back onto {TEST_STATES["TEST State One"]}: {DUPLICATE} is ticked, the key is cleared and '
             f'the run stops before the key write', TEST_STATES['TEST State One'], True, '', 3)):
        known = {r['id'] for r in (hap.run('approval', 'history', '--process-id', pid, '-n', '20')
                                   or {}).get('data') or []}
        hap.run('worksheet', 'record', 'update', ws(), dup, '-a', APP, '--fields-json',
                json.dumps([{'id': f[CODE]['controlId'], 'value': code}]))
        runs = runs_since(pid, known, want=1)
        got = quiesce(lambda: state(dup))
        # status 2 is 完成, 3 is a run that ended in an abort node (中止) — the visible mark on a duplicate
        status = [r.get('status') for r in runs]
        ok = got == (want_key, want_dup) and want_status in status
        print(f"  {'OK  ' if ok else 'DIFF'}  {label}: {STATE_KEY} {got[0]!r} {DUPLICATE} {got[1]}, run "
              f"status {status}" + ('' if ok else f' — want {(want_key, want_dup)} and status {want_status}'))
        for line in run_report(runs):
            print(f'        G: {line}')
        if not ok:
            problems.append(f'{label}: {got} status {status} != {(want_key, want_dup)} status {want_status}')
    # 0e · a save that re-sends an unchanged State Code must not mark the record as its own duplicate
    known = {r['id'] for r in (hap.run('approval', 'history', '--process-id', pid, '-n', '20')
                               or {}).get('data') or []}
    hap.run('worksheet', 'record', 'update', ws(), two, '-a', APP, '--fields-json',
            json.dumps([{'id': f[NAME]['controlId'], 'value': 'TEST State Two (renamed)'},
                        {'id': f[CODE]['controlId'], 'value': TEST_STATES['TEST State Two']}]))
    runs = runs_since(pid, known, want=1)
    got = quiesce(lambda: state(two))
    ok = got == (f'MY|{TEST_STATES["TEST State Two"]}', False)
    print(f"  {'OK  ' if ok else 'DIFF'}  0e. an unchanged State Code re-sent with a new State Name: "
          f"{STATE_KEY} {got[0]!r} {DUPLICATE} {got[1]} — the search excludes the record that started the run"
          + ('' if ok else f" — want ('MY|{TEST_STATES['TEST State Two']}', False)"))
    for line in run_report(runs):
        print(f'        G: {line}')
    if not ok:
        problems.append(f'0e. re-sending an unchanged State Code gave {got}')
    hap.run('worksheet', 'record', 'update', ws(), two, '-a', APP, '--fields-json',
            json.dumps([{'id': f[NAME]['controlId'], 'value': 'TEST State Two'},
                        {'id': f[CODE]['controlId'], 'value': TEST_STATES['TEST State Two']}]))
    quiesce(lambda: state(two))
    return problems


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
    problems += duplicate_probe()
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


def g_differences(f):
    """Workflow G read back: its nodes, its trigger, its search filter, its gateway and its two writes."""
    out = []
    pid = hap.ids().get('workflows', {}).get(WF_G)
    if not pid:
        return [f'workflow {WF_G!r} is not in ids.json']
    info = read('workflow', 'get', pid)
    cfg = read('workflow', 'config-get', pid)
    if not info.get('enabled') or info.get('publishStatus') != 2:
        out.append(f'{WF_G}: enabled={info.get("enabled")} publishStatus={info.get("publishStatus")}')
    if cfg.get('triggerType') != NO_OTHER_WORKFLOWS:
        out.append(f'{WF_G}: triggerType {cfg.get("triggerType")}, want {NO_OTHER_WORKFLOWS} (quiet)')
    proc = hap.run('workflow', 'node', 'list', pid)
    by_name = {n['name']: n for n in proc['flowNodeMap'].values()}
    for wanted in G_NODES:
        if wanted not in by_name:
            out.append(f'{WF_G}: no node {wanted!r}')
    if any(n not in by_name for n in G_NODES):
        return out
    trig = trigger_state(pid, proc['startEventId'])
    if trig['fields'] != sorted([f[COUNTRY]['controlId'], f[CODE]['controlId']]):
        out.append(f'{WF_G}: trigger fields {trig["fields"]}, want Country and State Code')
    if trig['condition']:
        out.append(f'{WF_G}: the trigger carries a condition {trig["condition"]}; every state needs a key')
    if trig['appId'] != ws():
        out.append(f'{WF_G}: the trigger is on {trig["appId"]}, not {WORKSHEET}')
    search = node_get(pid, by_name[FIND_STEP]['id'])
    conditions = [(c.get('filedId'), str(c.get('conditionId')))
                  for flt in search.get('filters') or [] for g in flt.get('conditions') or [] for c in g]
    if conditions != [(f[STATE_KEY]['controlId'], EQ), ('rowid', NE)]:
        out.append(f'{WF_G} / {FIND_STEP}: filter {conditions}')
    if str(search.get('executeType')) != '2':
        out.append(f'{WF_G} / {FIND_STEP}: executeType {search.get("executeType")}, want 2 (carry on when '
                   f'nothing is found)')
    key_node = by_name[KEY_STEP]['id']
    write = step_state_of(pid, by_name[WRITE_KEY_STEP]['id'])
    if write['fields'] != [(f[STATE_KEY]['controlId'], '', '', False, f'${key_node}-{STRING_FX}$')]:
        out.append(f'{WF_G} / {WRITE_KEY_STEP}: writes {write["fields"]}')
    for node_name, value in ((TICK_STEP, '1'), (UNTICK_STEP, '0')):
        s = step_state_of(pid, by_name[node_name]['id'])
        if s['fields'] != [(f[DUPLICATE]['controlId'], '', '', False, value)]:
            out.append(f'{WF_G} / {node_name}: writes {s["fields"]}')
    clear = step_state_of(pid, by_name[CLEAR_STEP]['id'])
    if clear['fields'] != [(f[STATE_KEY]['controlId'], '', '', True, '')]:
        out.append(f'{WF_G} / {CLEAR_STEP}: writes {clear["fields"]}, want one isClear entry')
    # The shape is what keeps the key unique: a workflow's write is **not** checked against No duplicates, so
    # the duplicate path must stop before the key write rather than rely on it being refused.
    nodes = {n['id']: n for n in proc['flowNodeMap'].values()}
    after_gate = nodes.get(by_name[DUP_GATEWAY].get('nextId') or '', {}).get('name')
    if after_gate != WRITE_KEY_STEP:
        out.append(f'{WF_G}: {WRITE_KEY_STEP!r} does not follow the gateway (it is {after_gate!r})')
    if nodes.get(by_name[TICK_STEP].get('nextId') or '', {}).get('name') != CLEAR_STEP:
        out.append(f'{WF_G}: {CLEAR_STEP!r} does not follow {TICK_STEP!r}')
    if nodes.get(by_name[CLEAR_STEP].get('nextId') or '', {}).get('name') != STOP_STEP:
        out.append(f'{WF_G}: the duplicate path does not end in {STOP_STEP!r} — a branch converges, so the '
                   f'run would reach {WRITE_KEY_STEP!r} and write a key another state holds')
    if by_name[STOP_STEP].get('typeId') != ABORT:
        out.append(f'{WF_G} / {STOP_STEP}: node type {by_name[STOP_STEP].get("typeId")}, want {ABORT} (中止流程)')
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
                       (COUNTRY_CODE, LOOKUP), (STATE_KEY, TEXT), (DUPLICATE, SWITCH)):
        if f.get(name, {}).get('type') != kind:
            problems.append(f'{name} is type {f.get(name, {}).get("type")}, want {kind}')
    if not f.get(STATE_KEY, {}).get('unique'):
        problems.append(f'{STATE_KEY} does not carry No duplicates')
    if any(c['controlId'] == KEY_FORMULA for c in ctrls):
        problems.append(f'the dropped {STATE_KEY} formula {KEY_FORMULA} is still on the worksheet')
    problems += g_differences(f)
    if f.get(COUNTRY, {}).get('dataSource') != cty_ws():
        problems.append(f'{COUNTRY} points at {f.get(COUNTRY, {}).get("dataSource")}, want {COUNTRIES}')
    if f.get(COUNTRY_CODE, {}).get('dataSource') != f"${f[COUNTRY]['controlId']}$":
        problems.append(f'{COUNTRY_CODE} reads through {f.get(COUNTRY_CODE, {}).get("dataSource")}')
    if f.get(COUNTRY_CODE, {}).get('strDefault') != '00':
        problems.append(f'{COUNTRY_CODE} strDefault {f.get(COUNTRY_CODE, {}).get("strDefault")!r}, want "00" '
                        '(stored)')
    views = {v['name']: C.view_info(ws(), APP, v['viewId'])
             for v in hap.listing('worksheet', 'view', 'list', ws(), '-a', APP)}
    if list(views) != [VIEW, DUP_VIEW]:            # in order: States opens first
        problems.append(f'views {list(views)}, want {[VIEW, DUP_VIEW]}')
    state = lambda v: dict(columns=[names.get(x) for x in v.get('showControls', [])],
                           sort=[(names.get(s['controlId']), s['isAsc']) for s in v.get('moreSort', [])],
                           sortCid=names.get(v.get('sortCid')), sortType=v.get('sortType'),
                           filters=[(names.get(x['controlId']), x['filterType'], tuple(x.get('values') or []))
                                    for x in v.get('filters', []) if x.get('controlId')],
                           quick=[names.get(q['controlId']) for q in v.get('fastFilters', [])])
    wanted = {
        VIEW: dict(columns=list(COLUMNS), sort=[(CODE, True), (COUNTRY, True)], sortCid=CODE, sortType=2,
                   filters=[], quick=[COUNTRY]),
        # Duplicate code is checked: filterType 2 (equals) with the switch's "1". No quick filter.
        DUP_VIEW: dict(columns=list(DUP_COLUMNS), sort=[(CODE, True), (COUNTRY, True)], sortCid=CODE,
                       sortType=2, filters=[(DUPLICATE, C.EQ, ('1',))], quick=[]),
    }
    for name, want in wanted.items():
        got = state(views.get(name, {}))
        if got != want:
            problems.append(f'view {name}: {got} != {want}')
    if hap.listing('worksheet', 'custom-actions', ws()):
        problems.append('this worksheet has a button; §1 gives it none')
    if hap.listing('worksheet', 'rules', ws()):
        problems.append('this worksheet has a rule; §1 gives it none')
    problems += roles_differences()
    problems += cty_differences()
    problems += con_differences()
    print('  check: ' + ('OK — the seven controls with their places, descriptions and permissions, Display '
                         'Name the title, the States view sorted State Code then Country with a Country quick '
                         'filter and the Duplicate codes view after it filtered to the ticked states, '
                         'the four business roles carrying States at their Contacts cell, Countries '
                         'holding the reverse list and the rewritten remark block, State key a hidden Text '
                         'control carrying No duplicates with the dropped formula gone, workflow G published '
                         'and quiet with its duplicate path ticking, clearing and ending in an abort before '
                         'the key write, and Contacts carrying the one-way relation in place of the deleted '
                         'text control with E and F published and quiet'
                         if not problems else 'DIFFERENCES\n    ' + '\n    '.join(problems)))
    return len(problems)


def step_all():
    for name in ('create', 'fields', 'key', 'reverse', 'views', 'dupview', 'roles', 'unique', 'seed',
                 'contacts', 'carry', 'retire', 'automations', 'duplicates', 'backfill'):
        print(f'\n── {name} ' + '─' * 60)
        STEPS[name]()
    print('\n── check ' + '─' * 60)
    return step_check()


def show():
    C.show(ws())


STEPS = {
    'create': step_create,
    'fields': step_fields,
    'key': step_key,
    'reverse': step_reverse,
    'views': step_views,
    'dupview': step_dupview,
    'roles': step_roles,
    'unique': step_unique,
    'seed': step_seed,
    'contacts': step_contacts,
    'carry': step_carry,
    'retire': step_retire,
    'automations': step_automations,
    'duplicates': step_duplicates,
    'backfill': step_backfill,
    'keys': step_keys,
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
                'automations', 'duplicates', 'backfill', 'keys', 'unique') and result:
        sys.exit(1)
