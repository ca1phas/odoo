#!/usr/bin/env python3
"""Build the Countries worksheet (Odoo res.country, as on casimir.odoo.com saas~19.4) in ERP Master.

Bundle 4 of the six that join Phase 1. It adds the worksheet to the **Contacts** menu group, seeds all 251
countries, and then **replaces Contacts' Country text with a relation**: create it beside the stand-in, carry
every contact's value across, read it back, re-point the three views that show Country, and only then delete
the text control (owner-approved, `DECISIONS.md` 17 Sep 2026). State stayed Text until bundle 5.

**States (bundle 5, 18 Sep 2026).** `states.py reverse` added the reverse control **States** to this worksheet
— the other half of the two-way Country relation on States — and rewrote the last line of the remark block.
Neither is owned here: `BUNDLE_5` below only keeps `guard` and `check` from calling the control unknown, and
`HTML` carries the new text so a re-run does not put the old line back (12-states.md).

Requirements: nocoly/worksheets/11-countries.md. Generic helpers: common.py. Run from the repo root with the
CLI's interpreter:

    ~/.hap-venv/bin/python nocoly/build/countries.py create    # 0. the worksheet in the menu group Contacts,
                                                               #    after Contacts itself
    ~/.hap-venv/bin/python nocoly/build/countries.py fields    # 1. the six controls and the remark block, one
                                                               #    save on the empty worksheet
    ~/.hap-venv/bin/python nocoly/build/countries.py views     # 2. Countries — the only view: two columns,
                                                               #    Country Name A→Z, no quick filter
    ~/.hap-venv/bin/python nocoly/build/countries.py roles     # 3. roles.py's create step, which now carries
                                                               #    this worksheet into the four business roles
    ~/.hap-venv/bin/python nocoly/build/countries.py seed      # 4. the 251 countries, every one read back, and
                                                               #    §1's six digests
    ~/.hap-venv/bin/python nocoly/build/countries.py contacts  # 5. the relation Country on Contacts, in the
                                                               #    text stand-in's cell (row 9, right half)
    ~/.hap-venv/bin/python nocoly/build/countries.py carry     # 6. every contact's Country text onto the
                                                               #    relation, read back
    ~/.hap-venv/bin/python nocoly/build/countries.py retire    # 7. re-point the views and the two address
                                                               #    workflows, delete the text control, scan
    ~/.hap-venv/bin/python nocoly/build/countries.py all       # every step above, then check

    ~/.hap-venv/bin/python nocoly/build/countries.py verify    # the 251 live countries against the extract,
                                                               #    with §1's six digests
    ~/.hap-venv/bin/python nocoly/build/countries.py check     # controls, permissions, view, roles' worksheet
                                                               #    and everything this bundle put on Contacts
    ~/.hap-venv/bin/python nocoly/build/countries.py selfcheck # No duplicates, the 2-character limit and the
                                                               #    Zip Required default, driven through the CLI
                                                               #    on TEST Country (left in the worksheet)
    ~/.hap-venv/bin/python nocoly/build/countries.py order     # the view's records in the view's own order
    ~/.hap-venv/bin/python nocoly/build/countries.py country MY  # stored values by Country Code
    ~/.hap-venv/bin/python nocoly/build/countries.py deadrefs  # every view, rule, button, control and workflow
                                                               #    node scanned for the deleted control's id
    ~/.hap-venv/bin/python nocoly/build/countries.py untouched # the other worksheets: control count and digest
    ~/.hap-venv/bin/python nocoly/build/countries.py show      # the live control list

Every step reads the live state first and is safe to re-run; a second run writes nothing. **The one deletion is
Contacts' text control `6aa8a452f363582dd37a50e7`**, and `retire` refuses to make it until every contact's
value reads back from the relation. Nothing else is deleted and the Sales app is never written to.

The order matters: `seed` before `carry` (the relation needs Malaysia to point at), `carry` before `retire`.

Records are created through the CLI, one call per country, and read back **through the CLI's own session** —
`record get` is 1.2 s of process start per record, which is five minutes for one read of 251 rows, and `check`
and `verify` read them all every time. Same calls, same account; only the transport differs (`common.py` does
the same for SaveWorksheetControls and SortWorksheetViews).

Profile. As in the other builders: --profile > $HAP_PROFILE > hap-cli's active profile.
"""
import hashlib
import json
import os
import sys
import uuid
from pathlib import Path

import common as C
import hap

APP = hap.ids()['app']
SALES_APP = '3e596740-d096-42cd-b948-0b62a0220927'   # the Nocoly Sales app: never written to
SECTION = 'Contacts'
SECTION_ID = '6aa8a3a93e5e4ad5b852a6d3'
WORKSHEET = 'Countries'
KEY = WORKSHEET + ': '                            # ids.json key prefix for everything this worksheet owns
CON_KEY = 'Contacts: '
ALIAS = 'res_country'
HERE = Path(__file__).resolve().parent
DATA = HERE.parent / 'data' / 'casimir-countries.json'
OTHERS = ('Contacts', 'States', 'Units & Packagings', 'Products', 'Product Variants', 'Product Categories',
          'Chart of Accounts', 'Journals', 'Payment Terms', 'Payment Term Lines', 'Invoices', 'Invoice Lines')
# Controls on this worksheet that a **later** bundle owns. States (`state_ids`) is the reverse half of the
# two-way Country relation on the States worksheet, saved there by `states.py reverse` (12 §1 › On Countries);
# it is read-only here, shown as a list at the foot of the form, and nothing in this file places or checks it —
# `guard` and `check` only have to stop calling it unknown. The remark block's last line was rewritten by the
# same step and HTML below carries the new text.
BUNDLE_5 = ('States',)

# Contacts' text Country — the one approved deletion of this bundle (DECISIONS.md, 17 Sep 2026)
TEXT_STANDIN = '6aa8a452f363582dd37a50e7'


def ws():
    return hap.ids()['worksheets'][WORKSHEET]


def con_ws():
    return hap.ids()['worksheets']['Contacts']


def refuse_sales():
    if APP == SALES_APP:
        sys.exit('ids.json points at the Sales app — refusing to write')


def session():
    from hap_cli.core.session import Session
    return Session.load(None)


def data():
    """The 251 countries of the 19.4 extract, by ISO code. `xmlid`, `currency` and `address_format` are in the
    file and are not built (§1 *Not built now*)."""
    return {c['code']: c for c in json.loads(DATA.read_text(encoding='utf-8'))}


# ── the form ────────────────────────────────────────────────────────────────

NAME = 'Country Name'
CODE = 'Country Code'
PHONE = 'Country Calling Code'
VAT = 'Vat Label'
ZIP_REQ = 'Zip Required'
STATE_REQ = 'State Required'
NOTE_NAME = 'Country form note'                   # type 10010: an internal label, the text is its dataSource

# §1's form layout. Odoo's two groups become paired rows on HAP's 12-column grid, as they do on Products, with
# the remark block full width under them. HAP puts the title field at the top of the record, so Country Name
# shows twice there, as Complete Name does on a category.
PLACE = {
    NAME: (0, 0, 6), PHONE: (0, 1, 6),
    CODE: (1, 0, 6), VAT: (1, 1, 6),
    ZIP_REQ: (2, 0, 6), STATE_REQ: (2, 1, 6),
    NOTE_NAME: (3, 0, 12),
}
HINTS = {}                                        # Odoo's country form has no placeholder on any field
DESC = {  # Odoo's field help where it has one (res_country.py); the rest have none
    CODE: 'The ISO country code in two chars. You can use this field for quick search.',
    VAT: 'Use this field if you want to change vat label.',
}
REQUIRED = {NAME, CODE}                           # Odoo: both required on the model
UNIQUE = {NAME, CODE}                             # Odoo's two SQL constraints, unique (name) and unique (code)
CODE_SIZE = 2                                     # Odoo code = fields.Char(size=2)
NOTE = 10010                                      # HAP's remark block: HTML in `dataSource`, `hidetitle` "1",
                                                  # the controlName an internal label. hap-cli has no builder,
                                                  # so its JSON is written out in full below (05's pattern)
SWITCH, TEXT, NUMBER, RELATION = 36, 2, 6, 29

# What the remark block says, as the HTML it stores. For the app's users only (owner, 22 Sep 2026): what the form
# holds, in plain words. The Odoo text it replaced — the version `states.py reverse` had rewritten — is kept word
# for word at the foot of 11-countries.md; `states.py` NOTE_HTML carries the same text as this.
HTML = {
    NOTE_NAME: "<p>The country's name, codes and address settings. Its states are listed at the foot of the "
               'form.</p>',
}
ADVANCED = {  # the advancedSetting keys this script owns
    # A form-side check, as 05's Sequence Prefix is: `record create` and `record update` store a longer value
    # without complaint (BUILDING.md), so the seed checks the length itself.
    CODE: {'checkrange': '1', 'min': '1', 'max': str(CODE_SIZE)},
    # Odoo renders phone_code with enable_formatting: false, so 1264, not 1,264. HAP's `thousandth` reads the
    # other way round from what its name suggests: "0" — the platform default every other Number in this app
    # carries — *draws* the separator, and "1" hides it. Proved in the browser on 18 Sep 2026: with "0" Anguilla
    # showed 1,264 and with "1" it shows 1264 (BUILDING.md).
    PHONE: {'thousandth': '1'},
    ZIP_REQ: {'defsource': C.static_default(1)},   # Odoo's default is true
    STATE_REQ: {'defsource': C.static_default(0)},
    NOTE_NAME: {'hidetitle': '1'},
}
NEW = {  # name -> (type, alias, extra control keys)
    NAME: ('TEXT', 'name', {}),
    CODE: ('TEXT', 'code', {}),
    PHONE: ('NUMBER', 'phone_code', {'dot': 0}),
    VAT: ('TEXT', 'vat_label', {}),
    ZIP_REQ: ('SWITCH', 'zip_required', {}),
    STATE_REQ: ('SWITCH', 'state_required', {}),
    NOTE_NAME: (NOTE, '', {}),
}
ALIASES = {name: alias for name, (_, alias, _) in NEW.items()}
FIELDS = (NAME, CODE, PHONE, VAT, ZIP_REQ, STATE_REQ)      # the six that hold a value


def new_control(name):
    """A control to add. The remark block is sent as raw JSON — `add-fields` mints its id, as it does for the
    controls hap-cli can build."""
    kind, alias, extra = NEW[name]
    row, col, size = PLACE[name]
    if kind == NOTE:
        # hap-cli has no builder for a remark block, so its JSON is written out in full — with a client-side
        # 32-hex controlId of its own, so that the one full save of an empty worksheet can place it like the
        # rest (`add-fields` mints one when it is added to a live worksheet instead).
        return {'controlId': uuid.uuid4().hex, 'controlName': name, 'type': NOTE, 'row': row, 'col': col,
                'size': size, 'alias': alias, 'dataSource': HTML[name],
                'advancedSetting': dict(ADVANCED[name]), 'desc': '', 'hint': '',
                'required': False, 'unique': False}
    advanced = dict(ADVANCED.get(name) or {})
    if kind == 'SWITCH':
        advanced.setdefault('showtype', '0')
    return C.control(kind, name, (row, col, size), alias=alias, hint=HINTS.get(name, ''), desc=DESC.get(name, ''),
                     required=name in REQUIRED, unique=name in UNIQUE, is_title=name == NAME,
                     advanced_setting=advanced or None, extra=extra or None)


def desired(c):
    """The attributes `fields` owns on control c, as they should read back."""
    name = c['controlName']
    row, col, size = PLACE[name]
    want = {'row': row, 'col': col, 'size': size, 'sectionId': ''}
    if c['type'] == NOTE:
        want['dataSource'] = HTML[name]
        return want
    want.update(alias=ALIASES[name], hint=HINTS.get(name, ''), desc=DESC.get(name, ''),
                required=name in REQUIRED, unique=name in UNIQUE, fieldPermission='111',
                attribute=1 if name == NAME else 0)
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
    """Read the worksheets of `before` again and stop unless the only differences are those named: `new`
    {worksheet: control names that may appear}, `changed` {worksheet: {control name: attributes that may
    change}} ('*' = any), `gone` {worksheet: control ids that may disappear}. Prints what did change.
    (payterms.expect, the same comparison.)"""
    after = snap(tuple(before))
    changed, new, gone = changed or {}, new or {}, gone or {}
    problems, seen, same = [], [], []
    for name in before:
        b, a = before[name], after[name]
        for cid in sorted(set(b) - set(a)):
            (seen if cid in gone.get(name, ()) else problems).append(
                f"{name}: {b[cid]['controlName']!r} ({cid}) is gone")
        for cid in sorted(set(a) - set(b)):
            (seen if a[cid]['controlName'] in new.get(name, ()) else problems).append(
                f"{name}: new control {a[cid]['controlName']!r} ({cid})")
        touched = False
        for cid in sorted(set(a) & set(b)):
            diff = [k for k in SIGNATURE if a[cid][k] != b[cid][k]]
            if not diff:
                continue
            touched = True
            allowed = changed.get(name, {}).get(b[cid]['controlName'], set())
            extra = [k for k in diff if k not in allowed and '*' not in allowed]
            if extra:
                problems.append(f"{name}: {b[cid]['controlName']!r} changed " + '; '.join(
                    f'{k} {json.dumps(b[cid][k], ensure_ascii=False)[:160]} -> '
                    f'{json.dumps(a[cid][k], ensure_ascii=False)[:160]}' for k in extra))
            else:
                seen.append(f"{name}: {b[cid]['controlName']!r} " + ', '.join(
                    f'{k} {b[cid][k]!r}→{a[cid][k]!r}' if k in ('row', 'col', 'size', 'controlName', 'alias') else k
                    for k in diff))
        if not touched and set(a) == set(b):
            same.append(f'{name} ({len(a)})')
    if problems:
        sys.exit(f'{label}: controls read back with differences nobody asked for — stopping:\n  '
                 + '\n  '.join(problems))
    print(f'  {label}: compared control by control')
    for line in seen:
        print(f'    {line}')
    print(f"    identical: {', '.join(same) or '—'}")
    return after


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

TEST_NAME = 'TEST Country'                        # selfcheck's own record; left in the worksheet
TEST_CODE = 'ZZZ'                                 # three characters on purpose — selfcheck 2


def guard(fresh=False):
    """Stop unless the profile reaches ERP Master › Contacts › Countries and the worksheet holds only this
    script's work. `fresh` allows the three stock controls of a brand-new worksheet. Returns the controls."""
    refuse_sales()
    who = hap.run('auth', 'whoami')
    app = hap.run('app', 'info', '-a', APP).get('data', {})
    worksheet = hap.ids().get('worksheets', {}).get(WORKSHEET)
    section = next((s for s in app.get('sections', []) if any(i['id'] == worksheet for i in s['items'])), None)
    if app.get('name') != 'ERP Master' or not section or section['name'] != SECTION:
        sys.exit(f"profile {who.get('profile')!r} does not reach ERP Master › {SECTION} › {WORKSHEET}")
    problems, ctrls = [], hap.controls(worksheet)
    stock = {'Name', 'Description', 'Attachment', '名称', '描述', '附件'}
    known = set(PLACE) | set(BUNDLE_5) | (stock if fresh else set())
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
    if all(n in hap.by_name(ctrls) for n in FIELDS):
        reference = data()
        problems += [f'unknown record {c["code"]!r} ({c["name"]!r})' for c in read_countries().values()
                     if c['code'] not in reference and not str(c['name']).startswith('TEST')]
    if problems:
        sys.exit(f"{WORKSHEET} differs from this script's work — stopping:\n  " + '\n  '.join(problems))
    print(f"  guard: profile {os.environ.get('HAP_PROFILE') or who.get('profile')!r}, ERP Master › {SECTION} › "
          f"{WORKSHEET}, {len(ctrls)} controls, {len(rules)} rules, {len(buttons)} buttons, views {sorted(views)}")
    return ctrls


# ── 0 · the worksheet ───────────────────────────────────────────────────────

REMARK = ("Odoo res.country: the list a contact's address hangs on — 251 countries with their ISO code, "
          'calling code and VAT label')
ICON = 'sys_16_5_globe_earth'                     # `hap icon search 地球` — the catalogue is 426 names, and a
                                                  # name that is not in it answers 400 and leaves a broken icon


def step_create():
    """The worksheet in the Contacts menu group, after Contacts itself.

    The menu group is looked up by its id rather than through `common.ensure_section`: that helper re-sorts the
    app's groups when the one it is given is not where it computes it should be, and ERP Master now carries a
    CRM group somebody else added. `worksheet create --section-id` appends, which is where §1 wants it."""
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


# ── 1 · the six controls and the remark block ───────────────────────────────

def step_fields():
    """The six fields and the remark block, in one save of the empty worksheet.

    A new worksheet comes with three stock controls — Name (the title), Description and Attachment — and a
    first full save that leaves one out deletes it, so Country Name reuses the stock title's id and the other
    two go. Country Name is the only control carrying `attribute` 1 in the save, so the title is not a coin
    toss. A re-run adds whatever is missing with `add-fields` and then places it, as 05 does."""
    existing = guard(fresh=True)
    f = hap.by_name(existing)
    if not any(n in f for n in PLACE) and len(existing) <= 3:
        hap.backup('countries_controls_pre_fields', existing)
        ctrls = [new_control(n) for n in PLACE]
        title = next((c for c in existing if c.get('attribute') == 1), None)
        if title:
            next(c for c in ctrls if c['controlName'] == NAME)['controlId'] = title['controlId']
        C.save_controls(ws(), ctrls)
        print(f'  first save: {list(PLACE)} (the stock title id {title and title["controlId"]} reused for {NAME})')
    else:
        missing = [n for n in PLACE if n not in f]
        if missing:
            before = snap()
            C.add_fields(ws(), [new_control(n) for n in missing])
            expect(before, f'{WORKSHEET}: add-fields {missing}')
            print(f'  added: {missing}')
    ctrls = hap.controls(ws())
    changed = layout_differences(ctrls)
    if changed:
        for c in ctrls:
            if c['controlName'] in changed:
                c.update(desired(c))
                c['advancedSetting'] = {**(c.get('advancedSetting') or {}), **(ADVANCED.get(c['controlName']) or {})}
        before = snap()
        C.save_controls(ws(), ctrls)
        expect(before, f'{WORKSHEET}: places, permissions, help and the title')
        print('  updated:', json.dumps(changed, ensure_ascii=False))
    left = layout_differences(hap.controls(ws()))
    if left:
        sys.exit(f'the controls read back with differences: {json.dumps(left, ensure_ascii=False)}')
    for c in hap.controls(ws()):
        C.remember('controls', KEY + c['controlName'], c['controlId'])
    C.show(ws())


def fields_of(worksheet_id):
    return hap.by_name(c for c in hap.controls(worksheet_id) if c['type'] != C.TAB)


# ── 2 · the Countries view ──────────────────────────────────────────────────

VIEW = 'Countries'
COLUMNS = (NAME, CODE)                            # base.view_country_tree, the same two columns


def step_views():
    """Countries, the only view: every country, Country Name · Country Code, sorted Country Name A→Z (Odoo's
    own `_order = 'name, id'`), and **no quick filter** — Odoo's search view carries no filter and no group-by.

    There is no Archived view: res.country has no active field."""
    guard()
    f = fields_of(ws())
    columns = [f[n]['controlId'] for n in COLUMNS]
    views = {VIEW: (dict(viewType='table', tableFields=columns), C.sort_spec([f[NAME]]), columns)}
    for name, vid in C.upsert_views(ws(), APP, views, 'countries_views_pre_views', default_view=VIEW).items():
        C.remember('views', KEY + name, vid)
    print('  order:', C.sort_views(ws(), APP, list(views)))
    C.print_views(ws(), APP)


# ── 3 · roles ───────────────────────────────────────────────────────────────

def step_roles():
    """roles.py owns the app's roles; its ORDER and its four matrices now carry Countries — **view for all
    four**, because Odoo's `ir.model.access.csv` gives res.country write, create and delete to
    `base.group_system` alone and none of the four business roles stands for it (§1 › Roles). This runs its
    `create` step, which upserts the roles and reconciles the scopes."""
    import roles
    return roles.step_create()


# ── 4 · the 251 countries ───────────────────────────────────────────────────

# §1's six digests, from the 19.4 extract (reference/odoo-19.4/res.country.md › The records).
DIGESTS = {'count': 251, 'vat_label': 54, 'state_required': 15, 'zip_required': 241, 'phone_code': 124769}
MALAYSIA = 'MY'


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


def flag(value):
    return str(value) == '1'


def number(value):
    return None if value in (None, '') else int(float(value))


def read_countries():
    """Every country by Country Code, read back field by field.

    `GetFilterRows` does not return every column — on Contacts it leaves out the text fields the default view
    does not show — so the ids this worksheet needs are checked against the first row and, if any is missing,
    every record is read with `GetRowDetail` instead."""
    f = fields_of(ws())
    ids = {n: f[n]['controlId'] for n in FIELDS}
    listed = rows(ws())
    if listed and any(cid not in listed[0] for cid in ids.values()):
        listed = [{**r, **row_detail(ws(), r['rowid'])} for r in listed]
    out = {}
    for r in listed:
        c = dict(rowid=r['rowid'], name=r.get(ids[NAME]) or '', code=r.get(ids[CODE]) or '',
                 phone_code=number(r.get(ids[PHONE])), vat_label=r.get(ids[VAT]) or '',
                 zip_required=flag(r.get(ids[ZIP_REQ])), state_required=flag(r.get(ids[STATE_REQ])))
        out[c['code'] or c['rowid']] = c
    return out


def want_country(e):
    """One country of the extract in the shape `read_countries` returns."""
    return dict(name=e['name'], code=e['code'], phone_code=e['phone_code'], vat_label=e['vat_label'] or '',
                zip_required=bool(e['zip_required']), state_required=bool(e['state_required']))


def country_values(f, e):
    return json.dumps([{'id': f[NAME]['controlId'], 'value': e['name']},
                       {'id': f[CODE]['controlId'], 'value': e['code']},
                       {'id': f[PHONE]['controlId'], 'value': e['phone_code']},
                       {'id': f[VAT]['controlId'], 'value': e['vat_label'] or ''},
                       {'id': f[ZIP_REQ]['controlId'], 'value': 1 if e['zip_required'] else 0},
                       {'id': f[STATE_REQ]['controlId'], 'value': 1 if e['state_required'] else 0}],
                      ensure_ascii=False)


def remember_records(mapping):
    """ids.json records, written in one pass — `common.remember` re-reads and re-writes the file per key, and
    there are 251 of them here."""
    ids = hap.ids()
    records = ids.setdefault('records', {})
    if any(records.get(k) != v for k, v in mapping.items()):
        records.update(mapping)
        C.save_ids(ids)


def step_seed(*only):
    """The 251 countries of the extract, created one per CLI call and every one read back. `only` limits it to
    ISO codes. A country already stored as the extract has it is left alone, so a second run writes nothing.

    Required, the 2-character limit and the Zip Required default are all **form-side only** (BUILDING.md), so
    the length and the two switches are checked here before anything is written."""
    guard()
    f = fields_of(ws())
    reference = data()
    bad = [c for c in reference.values() if len(c['code']) > CODE_SIZE or not c['name'] or not c['code']]
    if bad:
        sys.exit(f'the extract carries {len(bad)} countries HAP would store but §1 forbids: '
                 f'{[c["code"] for c in bad]}')
    live = read_countries()
    hap.backup('countries_records_pre_seed', live)
    written = 0
    for code, e in reference.items():
        if only and code not in only:
            continue
        want = want_country(e)
        current = live.get(code)
        if current and {k: current[k] for k in want} == want:
            continue
        values = country_values(f, e)
        if current:
            hap.run('worksheet', 'record', 'update', ws(), current['rowid'], '-a', APP, '--fields-json', values)
            print(f"  updated {code} {e['name']}")
        else:
            rowid = C.row_id(hap.run('worksheet', 'record', 'create', ws(), '-a', APP, '--fields-json', values))
            print(f"  created {code} {e['name']}: {rowid}")
        written += 1
    print(f'  {written} countries written')
    live = read_countries()
    remember_records({KEY + code: c['rowid'] for code, c in live.items() if code in reference})
    return step_verify(*only, live=live)


def digests(live=None, reference=None):
    """§1's six digests over the seeded countries (a TEST record is left out)."""
    reference = reference or data()
    live = {code: c for code, c in (live or read_countries()).items() if code in reference}
    return {'count': len(live),
            'vat_label': sum(1 for c in live.values() if c['vat_label']),
            'state_required': sum(1 for c in live.values() if c['state_required']),
            'zip_required': sum(1 for c in live.values() if c['zip_required']),
            'phone_code': sum(c['phone_code'] or 0 for c in live.values())}


def step_verify(*only, live=None):
    """Every live country against the 19.4 extract, field by field, then §1's six digests."""
    reference, live = data(), (read_countries() if live is None else live)
    bad, missing = {}, []
    for code, e in reference.items():
        if only and code not in only:
            continue
        current = live.get(code)
        if not current:
            missing.append(code)
            continue
        want = want_country(e)
        diff = {k: (current[k], v) for k, v in want.items() if current[k] != v}
        if diff:
            bad[code] = diff
    extra = sorted(c for c in live if c not in reference)
    print(f'  {len(reference)} countries in the extract; {len(missing)} missing {missing[:10]}; '
          f'{len(bad)} differing {json.dumps(bad, ensure_ascii=False)[:400]}; '
          f'{len(extra)} live records outside it {extra}')
    got, want = digests(live, reference), dict(DIGESTS)
    from_data = digests({c: want_country(e) | {'rowid': ''} for c, e in reference.items()}, reference)
    my = live.get(MALAYSIA)
    malaysia = my and (my['name'], my['code'], my['phone_code'], my['vat_label'], my['zip_required'],
                       my['state_required']) == ('Malaysia', 'MY', 60, '', True, False)
    for key in want:
        mark = 'OK  ' if got[key] == want[key] == from_data[key] else 'DIFF'
        print(f'  {mark}  {key:<16} live {got[key]:<8} §1 {want[key]:<8} extract {from_data[key]}')
    print(f"  {'OK  ' if malaysia else 'DIFF'}  Malaysia         "
          + (f"{my['name']} · {my['code']} · {my['phone_code']} · "
             f"{my['vat_label'] or 'no VAT label'} · {'ZIP required' if my['zip_required'] else 'no ZIP'} · "
             f"{'state required' if my['state_required'] else 'state not required'}" if my else 'missing'))
    return (len(missing) + len(bad) + sum(1 for k in want if got[k] != want[k] or want[k] != from_data[k])
            + (0 if malaysia else 1))


def step_country(*codes):
    """The stored values of countries by ISO code."""
    live = read_countries()
    for code in codes or sorted(live):
        print(f'  {code}: ' + json.dumps(live.get(code), ensure_ascii=False))


def step_order():
    """The view's records in the order the view returns them (its own sort)."""
    f = fields_of(ws())
    name = f[NAME]['controlId']
    for v in hap.listing('worksheet', 'view', 'list', ws(), '-a', APP):
        res = hap.run('worksheet', 'record', 'list', ws(), '-a', APP, '-n', '300', '--view-id', v['viewId'],
                      '--use-field-id-as-key')
        data_ = res.get('data', res) if isinstance(res, dict) else res
        listed = (data_.get('rows') if isinstance(data_, dict) else data_) or []
        names = [str(r.get(name)) for r in listed]
        print(f"  {v['name']} ({len(names)}): {', '.join(names[:8])} … {', '.join(names[-4:])}")


# ── 5 · the relation on Contacts ────────────────────────────────────────────

CON_FIELD = 'Country'                             # the relation's name, once the stand-in has given it up
STANDIN_NAME = 'Country (text stand-in)'          # the stand-in's name while both exist
STANDIN_PARKED = (26, 0, 6)                       # under Parent name, out of the relation's cell, until it goes
CON_PLACE = (9, 1, 6)                             # contacts.PLACE['Country'] — beside ZIP, where the text was


def country_relation():
    """A one-way Relation → Countries, single, shown as a dropdown. Sent without a controlId so the server
    mints it, and — `bidirectional` "0" — Countries gets no reverse control (Odoo's country form does not list
    the partners of a country; what it lists is the States, which are bundle 5's)."""
    return C.control('RELATE_SHEET', CON_FIELD, CON_PLACE, alias='country_id', hint='', desc='',
                     data_source=ws(), multi=False,
                     advanced_setting={'bidirectional': '0', 'showtype': '3'})   # 3 = dropdown


def con_relation(ctrls=None):
    return next((c for c in (ctrls if ctrls is not None else hap.controls(con_ws()))
                 if c['type'] == RELATION and c.get('dataSource') == ws()), None)


def standin(ctrls=None):
    return next((c for c in (ctrls if ctrls is not None else hap.controls(con_ws()))
                 if c['controlId'] == TEXT_STANDIN), None)


def step_contacts():
    """§1's step on Contacts: the relation Country in the text control's cell — row 9, right half, beside ZIP —
    while the stand-in still holds its values.

    Both cannot share a name or a cell, so the stand-in is renamed "Country (text stand-in)" and parked under
    Parent name first (one save), the relation is appended (`add-fields`, which parks it at row 9999) and then
    placed (a second save). The **alias `country_id` is free from the start** — the stand-in holds `country`,
    Odoo's own field name is `country_id` — so there is no alias hand-over of the kind bundle 3 needed. Every
    save is compared control by control."""
    guard()
    # Every save of Contacts here pins HAP's optimistic lock: another administrator is building CRM worksheets
    # in this app, and without the version hap-cli refetches the counter on a conflict and saves over whatever
    # they wrote in between (BUILDING.md).
    ctrls, version = C.controls_with_version(con_ws())
    rel, text = con_relation(ctrls), standin(ctrls)
    before = snap()
    if not rel:
        if not text:
            sys.exit('neither the stand-in nor the relation is on Contacts — stopping')
        print('  backup:', hap.backup('countries_contacts_controls_pre_relation', ctrls))
        if (text['controlName'], text['row'], text['col']) != (STANDIN_NAME, *STANDIN_PARKED[:2]):
            text.update(controlName=STANDIN_NAME, row=STANDIN_PARKED[0], col=STANDIN_PARKED[1],
                        size=STANDIN_PARKED[2])
            C.save_controls(con_ws(), ctrls, version=version)
            before = expect(before, 'the stand-in renamed and parked',
                            changed={'Contacts': {'Country': {'controlName', 'row', 'col', 'size'}}})
        C.append_controls(con_ws(), [country_relation()])
        before = expect(before, 'the relation added', new={'Contacts': {CON_FIELD}})
    ctrls, version = C.controls_with_version(con_ws())
    rel = con_relation(ctrls)
    row, col, size = CON_PLACE
    want = dict(controlName=CON_FIELD, alias='country_id', row=row, col=col, size=size, sectionId='', hint='',
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
        sys.exit('Countries gained a reverse control — the relation was meant to be one-way')


# ── 6 · carry the contacts' values ──────────────────────────────────────────

def relation(value):
    """A Relation cell: [{'sid': rowid, 'name': title}, …] as a list of (rowid, title)."""
    if isinstance(value, str):
        value = json.loads(value) if value.startswith('[') else []
    if not isinstance(value, list):
        return []
    return [(v.get('sid'), v.get('name')) for v in value if isinstance(v, dict)]


def read_contacts():
    """Every contact's Country text and Country relation, by Display Name.

    `record get` keys a value by the control's **alias** — the stand-in's `country`, the relation's
    `country_id` — so the two never collide here (bundle 3's stand-in and relation shared an alias and had to
    be told apart by controlId)."""
    out = {}
    for r in C.records(con_ws(), APP):
        d = hap.run('worksheet', 'record', 'get', con_ws(), r['rowid'], '-a', APP)['data']
        linked = relation(d.get('country_id'))
        out[d.get('complete_name') or r['rowid']] = dict(
            rowid=r['rowid'], name=d.get('name'), text=d.get('country'),
            country=linked[0][1] if linked else None, country_rowid=linked[0][0] if linked else None,
            active=d.get('active'))
    return out


# The eight contacts whose Country text read *Malaysia* when this bundle found them — every contact on the
# tenant is in Malaysia (§1), and the seven with no Country are bundle 3's TEST records and the two nameless
# addresses. Written down by Display Name so that `verify` still means something once the text control is gone:
# after the deletion there is nothing left to compare the relation with.
CARRIED = {'Klinik Kesihatan Damansara': 'Malaysia',
           'Sarawak Timber Logistics': 'Malaysia',
           'Sunway Construction Group': 'Malaysia',
           'TEST QA Trading Sdn Bhd': 'Malaysia',
           'TEST QA Trading Sdn Bhd, TEST Person One': 'Malaysia',
           'TEST QA Trading Sdn Bhd, TEST Person Three': 'Malaysia',
           'TEST QA Trading Sdn Bhd, TEST Person Two': 'Malaysia',
           'TEST Solo Trading': 'Malaysia'}


def step_carry():
    """Every contact whose Country text reads a country of the extract is given the relation, and every value
    is read back. §1: all of them read *Malaysia*, and so does the company on the tenant.

    Once the stand-in has been deleted there is no text left to read, so the table above drives it instead."""
    guard()
    rel = con_relation()
    if not rel:
        sys.exit('run `contacts` first')
    by_name = {c['name']: c for c in read_countries().values()}
    live = read_contacts()
    hap.backup('countries_contacts_records_pre_carry', live)
    text_gone = standin() is None
    for display, c in sorted(live.items()):
        text = (CARRIED.get(display, '') if text_gone else (c['text'] or '')).strip()
        if not text:
            continue
        want = by_name.get(text)
        if not want:
            sys.exit(f'{display}: the Country text reads {text!r}, which is no country of the extract')
        if c['country_rowid'] == want['rowid']:
            continue
        hap.run('worksheet', 'record', 'update', con_ws(), c['rowid'], '-a', APP, '--fields-json',
                json.dumps([{'id': rel['controlId'], 'value': [want['rowid']]}]))
        print(f'  {display}: Country set to {text}')
    return verify_carry()


def verify_carry():
    """Every contact named in CARRIED holds its country; while the text control still exists, the relation must
    also equal the text on every contact, carried or not."""
    live, text_gone = read_contacts(), standin() is None
    bad = 0
    for display, c in sorted(live.items()):
        text = (c['text'] or '').strip()
        want = CARRIED.get(display)
        ok = (c['country'] == want) if display in CARRIED else (text_gone or c['country'] == (text or None))
        if not text_gone and display in CARRIED and text != want:
            ok = False                                 # the text moved under us: CARRIED is out of date
        bad += not ok
        print(f"  {'OK  ' if ok else 'DIFF'}  {display[:44]:<44} "
              + (f'text {text or "—":<12} ' if not text_gone else '')
              + f"relation {c['country'] or '—':<12} active={c['active']}"
              + ('' if display in CARRIED or not c['country'] else '   (not in CARRIED)'))
    carried = sum(1 for c in live.values() if c['country'])
    print(f'  carry: {len(live)} contacts, {len(CARRIED)} to carry a country, {carried} carrying the relation '
          f"— {bad} differing (the text control is {'gone' if text_gone else 'still there'})")
    return bad


# ── 7 · retire the stand-in ─────────────────────────────────────────────────

# Contacts' two address automations copy the six address fields between a company and its contacts, so both
# name the text control — in an update step's `fields` and in the branch conditions in front of it. contacts.py
# builds them from its own ADDRESS list, which this bundle rewrote, so re-running `contacts.py automations`
# re-points them; it is run **before** the deletion, so no moment passes with a step pointing at a dead field.
CON_WORKFLOWS = ('Contacts: copy company details to its contact',
                 'Contacts: push company address and Tax ID to its contacts')


def step_retire():
    """§1's last step. Refuses unless every contact reads back from the relation. Then:

    1. `contacts.py views` re-points the **Country column** on *Contacts* and *Archived*, the **Country quick
       filter** on *Contacts* and the **country field on the Kanban card** — all three resolve the control by
       name, and the stand-in no longer answers to "Country";
    2. `contacts.py automations` re-points the two address-sync workflows, which copy the six address fields;
    3. the stand-in `6aa8a452f363582dd37a50e7` is deleted — a full save of Contacts that leaves it out, the
       owner's approved deletion;
    4. `contacts.py layout` is run to prove that script is in step with the worksheet it owns (it must change
       nothing), and every view, rule, button, control and workflow node is scanned for the dead id.

    §1 puts the deletion before the re-pointing. It is done the other way round on purpose: a deleted control
    stays in every view, quick filter, rule and workflow step that names it and nothing cleans it up
    (BUILDING.md), so re-pointing first is the order in which nothing is ever broken."""
    import contacts
    guard()
    rel = con_relation()
    if not rel:
        sys.exit('run `contacts` first')
    if verify_carry():
        sys.exit('not every contact reads back from the relation — refusing to delete the stand-in')
    before = snap()
    print('  ── contacts.py views')
    contacts.step_views()
    before = expect(before, 'contacts.py views (no control may change)')
    print('  ── contacts.py automations')
    print('  backup:', hap.backup('countries_contacts_workflows_pre_retire',
                                  {name: workflow_nodes(hap.ids()['workflows'][name]) for name in CON_WORKFLOWS}))
    contacts.step_automations()
    before = expect(before, 'contacts.py automations (no control may change)')
    text = standin()
    if text:
        ctrls, version = C.controls_with_version(con_ws())
        print('  backup:', hap.backup('countries_contacts_controls_pre_retire', ctrls))
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


CATALOGUE_KEYS = ('flowNodeList', 'flowNodeAppDtos', 'formulaMap', 'controls', 'addControls', 'filedControls',
                  'relationControls', 'appList')


def workflow_nodes(pid):
    """Every node of a workflow with its full configuration, through the CLI's own session — the same calls
    `workflow node list` and `workflow node get` make, without a process start each (the app carries thirty
    workflows and some hundreds of nodes)."""
    from hap_cli.core import flow_node, workflow as wf_mod
    s = session()
    proc = wf_mod.get_process_by_id(s, pid) or {}
    return {node_id: flow_node.get_node_detail(s, pid, node_id, app_id=APP)
            for node_id in (proc.get('flowNodeMap') or {})}


def step_deadrefs(dead=TEXT_STANDIN):
    """Every view, rule, button, control and workflow node of the app scanned for a control id — the deleted
    stand-in's. A node's control catalogue lists every control of a worksheet, dead or alive, so it is left
    out of the scan (payterms.deadrefs)."""
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


# ── self-check ──────────────────────────────────────────────────────────────

def attempt(*args):
    """Run a write expected to be refused; return (refused, message)."""
    try:
        out = hap.run(*args)
    except RuntimeError as error:
        return True, str(error)[:300]
    d = out.get('data', out) if isinstance(out, dict) else {}
    code = (out.get('resultCode') if isinstance(out, dict) else None) or \
           (d.get('resultCode') if isinstance(d, dict) else None)
    return code not in (None, 1), json.dumps(out, ensure_ascii=False)[:300]


def step_selfcheck():
    """Prove through the CLI what §1 asks the platform to do, and what it does not:

      1. **No duplicates** on Country Name and on Country Code is enforced on an API write — §1 leans on the
         field's own switch instead of Odoo's two SQL constraints;
      2. the **2-character limit is the form's only** — a three-character code is stored without complaint, as
         05's five-character Sequence Prefix is, which is why `seed` checks the length itself;
      3. **Zip Required's default does not apply through the API** — HAP applies a default in the form only, so
         a country created without it reads back unticked, ticked though the field is by default.

    TEST Country is created once and left in the worksheet, outside the 251."""
    guard()
    f = fields_of(ws())
    cid = lambda n: f[n]['controlId']
    live = read_countries()
    problems = []
    test = live.get(TEST_CODE)
    if not test:
        rowid = C.row_id(hap.run('worksheet', 'record', 'create', ws(), '-a', APP, '--fields-json', json.dumps(
            [{'id': cid(NAME), 'value': TEST_NAME}, {'id': cid(CODE), 'value': TEST_CODE}])))
        print(f'  created {TEST_NAME}: {rowid}')
    else:
        rowid = test['rowid']
    C.remember('records', KEY + TEST_NAME, rowid)
    back = {c['rowid']: c for c in read_countries().values()}[rowid]
    print(f"  2. a {len(TEST_CODE)}-character code on a field limited to {CODE_SIZE}: stored as "
          f"{back['code']!r} — the limit is the form's only")
    if back['code'] != TEST_CODE:
        problems.append(f'the over-long code read back {back["code"]!r}')
    print(f"  3. {ZIP_REQ} left out of the create: reads back "
          f"{'ticked' if back['zip_required'] else 'unticked'} (the field's default is ticked; the API "
          'applies no default)')
    if back['zip_required']:
        problems.append('Zip Required came back ticked — a default the API is not supposed to apply')

    refused, message = attempt('worksheet', 'record', 'update', ws(), rowid, '-a', APP, '--fields-json',
                               json.dumps([{'id': cid(NAME), 'value': 'Malaysia'}]))
    print(f"  1. {NAME} 'Malaysia' on a second record: {'refused' if refused else 'ACCEPTED'} — {message[:140]}")
    if not refused:
        problems.append('No duplicates on Country Name did not refuse the write')
    refused, message = attempt('worksheet', 'record', 'update', ws(), rowid, '-a', APP, '--fields-json',
                               json.dumps([{'id': cid(CODE), 'value': MALAYSIA}]))
    print(f"  1. {CODE} 'MY' on a second record: {'refused' if refused else 'ACCEPTED'} — {message[:140]}")
    if not refused:
        problems.append('No duplicates on Country Code did not refuse the write')
    back = {c['rowid']: c for c in read_countries().values()}[rowid]
    if (back['name'], back['code']) != (TEST_NAME, TEST_CODE):
        problems.append(f'{TEST_NAME} was changed by a refused write: {back}')
    print(f"  {TEST_NAME} after both refusals: {back['name']!r} / {back['code']!r}")
    print('  selfcheck: ' + ('OK — No duplicates enforced on both fields through the API, the 2-character '
                             'limit and the Zip Required default form-side only'
                             if not problems else 'DIFFERENCES\n    ' + '\n    '.join(problems)))
    return len(problems)


# ── check ───────────────────────────────────────────────────────────────────

def con_differences():
    """What this bundle put on Contacts, read back: the relation, the three views and the stand-in's absence."""
    import contacts
    ctrls = hap.controls(con_ws())
    f = hap.by_name(c for c in ctrls if c['type'] != C.TAB)
    out = []
    rel = f.get(CON_FIELD)
    if not rel:
        return [f'Contacts has no {CON_FIELD} control']
    row, col, size = contacts.PLACE[CON_FIELD][:3]
    adv = rel.get('advancedSetting') or {}
    want = {'type': RELATION, 'alias': 'country_id', 'dataSource': ws(), 'enumDefault': 1, 'required': False,
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
    cid = rel['controlId']
    for name, columns, quick, card in (('Contacts', True, True, False), ('Archived', True, False, False),
                                       ('Kanban', False, False, True)):
        view = next((v for v in hap.listing('worksheet', 'view', 'list', con_ws(), '-a', APP)
                     if v['name'] == name), None)
        if not view:
            out.append(f'Contacts has no {name} view')
            continue
        info = C.view_info(con_ws(), APP, view['viewId'])
        if columns and cid not in (info.get('showControls') or []):
            out.append(f'Contacts / {name}: {CON_FIELD} is not a column')
        if card and cid not in (info.get('displayControls') or []):
            out.append(f'Contacts / {name}: {CON_FIELD} is not on the card')
        if quick and cid not in [q['controlId'] for q in info.get('fastFilters') or []]:
            out.append(f'Contacts / {name}: no {CON_FIELD} quick filter')
    return out


def step_check():
    """The controls with their places, permissions, help, defaults and switches, the view, the roles' entry for
    this worksheet, and everything this bundle put on Contacts, against §1; non-zero on a difference."""
    ctrls = hap.controls(ws())
    f = hap.by_name(ctrls)
    names = {c['controlId']: c['controlName'] for c in ctrls}
    problems = []
    if set(f) != set(PLACE) | set(BUNDLE_5):
        problems.append(f'controls {sorted(set(f) ^ (set(PLACE) | set(BUNDLE_5)))}')
    problems += [f'{n}: {d}' for n, d in layout_differences(ctrls).items()]
    if f.get(NAME, {}).get('attribute') != 1:
        problems.append('the title field is '
                        f'{next((c["controlName"] for c in ctrls if c.get("attribute") == 1), None)!r}')
    for name, kind in ((NAME, TEXT), (CODE, TEXT), (VAT, TEXT), (PHONE, NUMBER),
                       (ZIP_REQ, SWITCH), (STATE_REQ, SWITCH), (NOTE_NAME, NOTE)):
        if f.get(name, {}).get('type') != kind:
            problems.append(f'{name} is type {f.get(name, {}).get("type")}, want {kind}')
    if f.get(PHONE, {}).get('dot') != 0:
        problems.append(f'{PHONE} has {f.get(PHONE, {}).get("dot")} decimals, want 0')
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
    want = dict(columns=list(COLUMNS), sort=[(NAME, True)], sortCid=NAME, sortType=2, filters=[], quick=[])
    if got != want:
        problems.append(f'view {VIEW}: {got} != {want}')
    if hap.listing('worksheet', 'custom-actions', ws()):
        problems.append('this worksheet has a button; §1 gives it none')
    if hap.listing('worksheet', 'rules', ws()):
        problems.append('this worksheet has a rule; §1 gives it none')
    problems += roles_differences()
    problems += con_differences()
    print('  check: ' + ('OK — the six controls and the remark block with their places, help, defaults and the '
                         'two No-duplicates switches, Country Name the title, the Countries view sorted A→Z '
                         'with no quick filter, view for all four business roles, and Contacts carrying the '
                         'one-way relation in place of the deleted text control'
                         if not problems else 'DIFFERENCES\n    ' + '\n    '.join(problems)))
    return len(problems)


def roles_differences():
    """Countries' entry in the four business roles: view for every one of them (§1 › Roles)."""
    import roles
    out = []
    if WORKSHEET not in roles.ORDER:
        return [f'roles.py ORDER does not carry {WORKSHEET}']
    live = {r['name']: r for r in roles.roles()}
    for name, (_, matrix) in roles.ROLES.items():
        if matrix.get(WORKSHEET) != roles.VIEW:
            out.append(f'roles.py gives {name} {matrix.get(WORKSHEET)!r} on {WORKSHEET}, want {roles.VIEW!r}')
        r = live.get(name)
        if not r:
            out.append(f'role {name!r} is missing')
            continue
        scope, add = roles.scopes(r['roleId']).get(WORKSHEET, (None, None))
        if roles.cell(scope, add) != roles.VIEW:
            out.append(f'{name} / {WORKSHEET}: {roles.cell(scope, add)!r}, want {roles.VIEW!r}')
    return out


def step_all():
    for name in ('create', 'fields', 'views', 'roles', 'seed', 'contacts', 'carry', 'retire'):
        print(f'\n── {name} ' + '─' * 60)
        STEPS[name]()
    print('\n── check ' + '─' * 60)
    return step_check()


def show():
    C.show(ws())


STEPS = {
    'create': step_create,
    'fields': step_fields,
    'views': step_views,
    'roles': step_roles,
    'seed': step_seed,
    'contacts': step_contacts,
    'carry': step_carry,
    'retire': step_retire,
    'all': step_all,
    'verify': step_verify,
    'check': step_check,
    'selfcheck': step_selfcheck,
    'deadrefs': step_deadrefs,
    'order': step_order,
    'country': step_country,
    'untouched': step_untouched,
    'show': show,
}

if __name__ == '__main__':
    step = sys.argv[1] if len(sys.argv) > 1 else 'check'
    if step not in STEPS:
        raise SystemExit(f"Unknown step {step!r}; choose from {', '.join(STEPS)}")
    result = STEPS[step](*sys.argv[2:])
    if step in ('verify', 'check', 'all', 'selfcheck', 'roles', 'carry', 'retire', 'deadrefs') and result:
        sys.exit(1)
