#!/usr/bin/env python3
"""Build the Contact Tags worksheet (Odoo res.partner.category) in ERP Master.

Bundle `btag`: one worksheet, standing alone, and **empty** — Odoo ships no tags and the tenant's own are no longer
readable. The parent (labelled *Category*, as Odoo labels it) and the Complete Name follow 08 Product Categories:
a single self-relation that the server makes two-way, a stored lookup of the parent's Complete Name, and a text
function formula on top of it. Active is a **visible toggle** and there are no Archive / Unarchive buttons. The
wiring — Tags on Contacts — is a later step and is **not** done here: nothing in this script writes to another
worksheet. Requirements: nocoly/worksheets/20-contact-tags.md. Generic helpers: common.py. Run from the repo root
with the CLI's interpreter:

    ~/.hap-venv/bin/python nocoly/build/contacttags.py create    # 0. the worksheet in menu group Contacts, right
                                                                 #    after Contacts (Odoo: Configuration › Contact
                                                                 #    Tags comes before Localization)
    ~/.hap-venv/bin/python nocoly/build/contacttags.py fields    # 1. three pinned saves: the six controls on the empty
                                                                 #    worksheet; the parent's lookup with Complete
                                                                 #    Name rewritten on it; then places, the reverse
                                                                 #    Child Tags, permissions, the picker filter
    ~/.hap-venv/bin/python nocoly/build/contacttags.py views     # 2. All (active, by Name), By Category, Archived
    ~/.hap-venv/bin/python nocoly/build/contacttags.py roles     # 3. roles.py `plan`, then `create` only if the plan
                                                                 #    touches nothing but this worksheet
    ~/.hap-venv/bin/python nocoly/build/contacttags.py all       # every step above, then check

    ~/.hap-venv/bin/python nocoly/build/contacttags.py check     # controls, formula, lookup, picker filter, views,
                                                                 #    no rules and no buttons, the menu place
    ~/.hap-venv/bin/python nocoly/build/contacttags.py selfcheck # three levels, a rename down the chain, the reverse,
                                                                 #    a tag as its own parent and the Active toggle,
                                                                 #    on three TEST tags (left archived)
    ~/.hap-venv/bin/python nocoly/build/contacttags.py show      # the live control list

Every step reads the live state first and is safe to re-run; a second run writes nothing. Every full control save is
pinned to the version it read (CLAUDE.md › Saving controls). Nothing is deleted, apart from the two stock controls
(Description, Attachment) the first save of the brand-new worksheet leaves out (DECISIONS.md, 17 Sep 2026).

Profile. As in the other builders: --profile > $HAP_PROFILE > hap-cli's active profile.
"""
import json
import os
import sys
import time

import common as C
import hap

APP = hap.ids()['app']
SALES_APP = '3e596740-d096-42cd-b948-0b62a0220927'   # the Nocoly Sales app: never written to
SECTION = 'Contacts'
SECTION_ID = '6aa8a3a93e5e4ad5b852a6d3'
WORKSHEET = 'Contact Tags'
KEY = WORKSHEET + ': '                              # ids.json key prefix for everything this worksheet owns
ALIAS = 'res_partner_category'
AFTER = 'Contacts'                                  # the menu group reads Contacts · Contact Tags · Countries · States
REMARK = 'Labels for contacts — "VIP", "Supplier / Local" — which can sit under a parent tag'
ICON = 'sys_8_2_bookmark_ribbon'                    # `hap icon search 书签`


def ws():
    return hap.ids()['worksheets'][WORKSHEET]


def refuse_sales():
    if APP == SALES_APP:
        sys.exit('ids.json points at the Sales app — refusing to write')


# ── the form ────────────────────────────────────────────────────────────────

NAME, COMPLETE, CATEGORY, CHILDREN = 'Name', 'Complete Name', 'Category', 'Child Tags'
COLOR, ACTIVE, PARENT_COMPLETE = 'Color', 'Active', 'Parent Complete Name'
STOCK = {'Name', 'Description', 'Attachment', '名称', '描述', '附件'}

# Odoo's form is one group of four columns: Name | Color, Category | Active. Complete Name — the title, which HAP
# also draws at the head of the record — sits under them, read-only and off the create form, as on 08. The children
# are a list at the foot of the record; the hidden lookup sits under everything.
PLACE = {
    NAME: (0, 0, 6), COLOR: (0, 1, 6),
    CATEGORY: (1, 0, 6), ACTIVE: (1, 1, 6),
    COMPLETE: (2, 0, 6),
    CHILDREN: (3, 0, 12),
    PARENT_COMPLETE: (4, 0, 6),
}
ALIASES = {NAME: 'name', COMPLETE: 'display_name', CATEGORY: 'parent_id', CHILDREN: 'child_ids', COLOR: 'color',
           ACTIVE: 'active',
           PARENT_COMPLETE: 'parent_complete_name'}     # not an Odoo field: Complete Name is built on it
TITLE = COMPLETE
HINTS = {NAME: 'e.g. "Consulting Services"'}        # Odoo's placeholder; no other control has one
DESC = {  # for the app's users only (owner's rule, 22 Sep 2026)
    COMPLETE: 'The full path of the tag, e.g. Supplier / Local.',
    CATEGORY: 'The tag this one sits under.',
    CHILDREN: 'The tags under this one.',
    COLOR: 'A colour to tell the tag apart.',
    ACTIVE: 'Switch off to hide the tag without deleting it.',
}
REQUIRED = {NAME}
PERMISSION = {COMPLETE: '100', CHILDREN: '100',     # read-only · hidden on create (both are table columns or lists)
              PARENT_COMPLETE: '011'}               # hidden

# Odoo's twelve colours (web/static/src/core/colorlist/colorlist.js) and their swatches ($o-colors in
# web/static/src/scss/secondary_variables.scss), index 0 to 11. The keys are minted once, here, and never re-minted.
COLORS = [
    ('a6d55751-5d09-4b7e-99f2-33a29ed335ee', 'No color', '#a2a2a2'),
    ('25741f23-e576-4daf-9e94-a1d36d8e44d2', 'Red', '#ee2d2d'),
    ('ccf71c91-5e6b-4be1-babf-91f513240c52', 'Orange', '#dc8534'),
    ('ca251661-ecfa-4866-8460-f0b694b28239', 'Yellow', '#e8bb1d'),
    ('9286a856-bc6a-4afd-b15c-097948013953', 'Cyan', '#5794dd'),
    ('0134a975-379e-4d6c-acdf-a5084701fea3', 'Purple', '#9f628f'),
    ('9262c828-aa61-4a8e-8638-3c4cafb5f63e', 'Almond', '#db8865'),
    ('873ad934-fc4f-4583-a6ca-e09660af83f2', 'Teal', '#41a9a2'),
    ('50d498f2-5495-46b0-a885-d03975ecfd54', 'Blue', '#304be0'),
    ('ca866523-fe8c-46d2-846c-df947aa96ef5', 'Raspberry', '#ee2f8a'),
    ('a97d49c7-3ea1-4fec-8d2d-0a118bf75208', 'Green', '#61c36e'),
    ('27fcf08c-209f-43de-b17e-848eda406fb6', 'Violet', '#9872e6'),
]
NO_COLOR = COLORS[0][0]
OPTIONS = [{'key': k, 'value': v, 'isDeleted': False, 'index': i + 1, 'checked': False, 'color': color}
           for i, (k, v, color) in enumerate(COLORS)]


def option_state(options):
    return [(o.get('key'), o.get('value'), o.get('index'), (o.get('color') or '').lower())
            for o in options or [] if not o.get('isDeleted')]


def ref(c):
    return f"${c['controlId']}$"


def function_source(expression):
    """dataSource of a function formula (type 53), as contacts.py and variants.py write it."""
    return json.dumps({'type': 'mdfunction', 'expression': expression, 'status': 1}, ensure_ascii=False)


def complete_name_expression(f):
    """Odoo _compute_display_name: every ancestor's name down to this one, joined by ' / ' — recursive through the
    stored lookup of the parent's Complete Name, exactly as 08's Complete Name."""
    name, parent = ref(f[NAME]), ref(f[PARENT_COMPLETE])
    return f'IF(ISBLANK({parent}),TRIM({name}),CONCAT({parent}," / ",TRIM({name})))'


def picker_filters(f):
    """Category's picker: active tags other than this one — Odoo's list carries domain [('id', '!=', id)], and a
    Many2one picker offers active records only. The tag itself is left out by comparing the candidate's Complete
    Name with this record's (09's Parent Account); a text formula's condition is dataType 2."""
    base = {'spliceType': 1, 'dateRange': 0, 'dateRangeType': 0, 'minValue': None, 'maxValue': None, 'isAsc': False,
            'advancedSetting': None, 'isGroup': False, 'groupFilters': None, 'emptyRule': 0}
    return json.dumps([
        {'controlId': f[ACTIVE]['controlId'], 'dataType': 36, **base, 'filterType': C.EQ, 'value': '1',
         'values': ['1'], 'dynamicSource': []},
        {'controlId': f[COMPLETE]['controlId'], 'dataType': 2, **base, 'filterType': C.NE, 'value': '', 'values': [],
         'dynamicSource': [{'rcid': '', 'cid': f[COMPLETE]['controlId'], 'staticValue': '', 'isAsync': False,
                            'type': 0}]},
    ], ensure_ascii=False, separators=(',', ':'))


def filters_state(value):
    try:
        items = json.loads(value or '[]')
    except (TypeError, ValueError):
        return value
    return [(i.get('controlId'), i.get('dataType'), i.get('filterType'), i.get('values') or [],
             [d.get('cid') for d in i.get('dynamicSource') or []]) for i in items]


def advanced(name, f):
    """The advancedSetting keys this script owns on control `name` (JSON-valued ones compared parsed)."""
    if name == ACTIVE:
        return {'showtype': '1', 'defsource': C.static_default(1)}      # 1 = a switch — Odoo's boolean_toggle
    if name == COLOR:
        return {'showtype': '0', 'defsource': C.static_default(NO_COLOR)}   # 0 = a dropdown list
    if name == COMPLETE:
        return {'analysislink': '1', 'sorttype': 'en'}
    if name == CATEGORY:
        out = {'showtype': '3', 'bidirectional': '1'}                   # 3 = a dropdown
        if all(n in f for n in (ACTIVE, COMPLETE)):
            out['filters'] = picker_filters(f)
        return out
    return {}


def setting_differences(name, c, f):
    settings = c.get('advancedSetting') or {}
    out = {}
    for k, v in advanced(name, f).items():
        got = settings.get(k)
        same = filters_state(got) == filters_state(v) if k == 'filters' else got == v
        if not same:
            out[f'advancedSetting.{k}'] = (got, v)
    return out


def child_columns(f):
    return [f[NAME]['controlId'], f[COLOR]['controlId']]


def desired(c, f):
    """The attributes this script owns on control c, as they should read back."""
    name = c['controlName']
    row, col, size = PLACE[name]
    want = {'row': row, 'col': col, 'size': size, 'sectionId': '', 'alias': ALIASES[name],
            'hint': HINTS.get(name, ''), 'desc': DESC.get(name, ''), 'required': name in REQUIRED,
            'unique': False, 'fieldPermission': PERMISSION.get(name, '111'), 'attribute': 1 if name == TITLE else 0}
    if name == CHILDREN and all(n in f for n in (NAME, COLOR)):
        want['showControls'] = child_columns(f)
    if name == COLOR:
        want['enumDefault2'] = 1                    # the options' colours switched on (the owner's Orders Status
                                                    # carries 1; every dropdown left at 0 draws no colour)
    return want


def expression_of(c):
    try:
        return json.loads(c.get('dataSource') or '{}').get('expression')
    except ValueError:
        return None


def layout_differences(ctrls):
    f = hap.by_name(ctrls)
    out = {}
    for c in ctrls:
        name = c['controlName']
        if name not in PLACE:
            continue
        diff = {k: (c.get(k), v) for k, v in desired(c, f).items()
                if (c.get(k) or (0 if k in ('attribute', 'enumDefault2') else [] if isinstance(v, list)
                                 else '' if isinstance(v, str) else False)) != v}
        diff.update(setting_differences(name, c, f))
        if name == COLOR and option_state(c.get('options')) != option_state(OPTIONS):
            diff['options'] = (option_state(c.get('options')), option_state(OPTIONS))
        if name == COMPLETE and PARENT_COMPLETE in f and expression_of(c) != complete_name_expression(f):
            diff['expression'] = (expression_of(c), complete_name_expression(f))
        if diff:
            out[name] = diff
    return out


def fields_of():
    return hap.by_name(c for c in hap.controls(ws()) if c['type'] != C.TAB)


def reverse_of(ctrls):
    """The reverse of Category — the control the server made for the self-relation — whatever it is called."""
    category = next((c for c in ctrls if c['controlName'] == CATEGORY), None)
    reserved = category and category.get('sourceControlId')
    return next((c for c in ctrls if reserved and c['controlId'] == reserved), None)


# ── guard ───────────────────────────────────────────────────────────────────

VIEW, BY_CATEGORY, ARCHIVED = 'All', 'By Category', 'Archived'
VIEWS = (VIEW, BY_CATEGORY, ARCHIVED)
TESTS = ('TEST Parent Tag', 'TEST Child Tag', 'TEST Grandchild Tag')   # selfcheck's own records; left archived


def guard(fresh=False):
    """Stop unless the profile reaches ERP Master › Contacts › Contact Tags and the worksheet holds only this
    script's work. `fresh` allows the three stock controls of a brand-new worksheet. Returns the controls.

    Records are not checked: the worksheet starts empty and the people using it add their own tags."""
    refuse_sales()
    who = hap.run('auth', 'whoami')
    app = C.app_info(APP)
    worksheet = hap.ids().get('worksheets', {}).get(WORKSHEET)
    section = next((s for s in app.get('sections', []) if any(i['id'] == worksheet for i in s['items'])), None)
    if app.get('name') != 'ERP Master' or not section or section['id'] != SECTION_ID:
        sys.exit(f"profile {who.get('profile')!r} does not reach ERP Master › {SECTION} › {WORKSHEET}")
    problems, ctrls = [], hap.controls(worksheet)
    known = set(PLACE) | (STOCK if fresh else set())
    reverse = reverse_of(ctrls)
    problems += [f"unknown control {c['controlName']!r} ({c['controlId']})" for c in ctrls
                 if c['controlName'] not in known and c is not reverse]
    if len(hap.by_name(ctrls)) != len(ctrls):
        problems.append(f'two controls share a name: {sorted(c["controlName"] for c in ctrls)}')
    views = {v['name'] for v in hap.listing('worksheet', 'view', 'list', worksheet, '-a', APP)}
    problems += [f'unknown view {n!r}' for n in views - set(VIEWS) - {'全部'}]
    buttons = {b['name'] for b in hap.listing('worksheet', 'custom-actions', worksheet)}
    problems += [f'unknown button {n!r}' for n in buttons]          # 20 §3: no buttons
    rules = {r['name'] for r in hap.listing('worksheet', 'rules', worksheet)}
    problems += [f'unknown rule {n!r}' for n in rules]              # and no rules
    if problems:
        sys.exit(f"{WORKSHEET} differs from this script's work — stopping:\n  " + '\n  '.join(problems))
    print(f"  guard: profile {os.environ.get('HAP_PROFILE') or who.get('profile')!r}, ERP Master › {SECTION} › "
          f"{WORKSHEET}, {len(ctrls)} controls, {len(rules)} rules, {len(buttons)} buttons, views {sorted(views)}")
    return ctrls


# ── 0 · the worksheet ───────────────────────────────────────────────────────

def step_create():
    """The worksheet in the existing Contacts menu group, moved to just after Contacts itself: Odoo's Contacts ›
    Configuration menu opens with Contact Tags (sequence 1), before Localization's Countries and States (5).

    The menu group is looked up by its **id**; `common.ensure_section` is never called, because it re-sorts the
    app's top-level groups (BUILDING.md). `app sort-worksheets` reorders this one group only."""
    refuse_sales()
    section = next((s for s in C.app_info(APP)['sections'] if s['id'] == SECTION_ID), None)
    if not section or section['name'] != SECTION:
        sys.exit(f'menu group {SECTION_ID} is {section and section["name"]!r}, not {SECTION!r}')
    worksheet = C.ensure_worksheet(APP, SECTION_ID, WORKSHEET, alias=ALIAS, icon=ICON, remark=REMARK)
    C.remember('worksheets', WORKSHEET, worksheet)
    items = next(s for s in C.app_info(APP)['sections'] if s['id'] == SECTION_ID)['items']
    ids = [i['id'] for i in items]
    after = next((i['id'] for i in items if i['name'] == AFTER), None)
    if not after:
        sys.exit(f'{AFTER!r} is not in {SECTION}')
    order = [i for i in ids if i != worksheet]
    order.insert(order.index(after) + 1, worksheet)
    if order != ids:
        hap.run('app', 'sort-worksheets', APP, SECTION_ID, *order)
        back = [i['id'] for i in next(s for s in C.app_info(APP)['sections'] if s['id'] == SECTION_ID)['items']]
        if back != order:
            sys.exit(f'{SECTION} reads back {back}, wanted {order}')
        print(f'  moved {WORKSHEET} after {AFTER}')
    section = next(s for s in C.app_info(APP)['sections'] if s['id'] == SECTION_ID)
    print(f"  {section['name']}: {[(i['name'], i['id']) for i in section['items']]}")


# ── 1 · the controls ────────────────────────────────────────────────────────

def first_controls(title_id):
    """The first save: Name (on the stock title's id), Color, Category, Active and Complete Name — the last with a
    placeholder expression, since the lookup it reads is not there yet — and Complete Name the only title."""
    built = {
        NAME: C.control('TEXT', NAME, PLACE[NAME], alias=ALIASES[NAME], hint=HINTS[NAME], required=True),
        COLOR: C.control('DROP_DOWN', COLOR, PLACE[COLOR], alias=ALIASES[COLOR], hint='', desc=DESC[COLOR],
                         options=[dict(o) for o in OPTIONS], advanced_setting=advanced(COLOR, {})),
        CATEGORY: C.control('RELATE_SHEET', CATEGORY, PLACE[CATEGORY], alias=ALIASES[CATEGORY], hint='',
                            desc=DESC[CATEGORY], data_source=ws(), multi=False,
                            advanced_setting=advanced(CATEGORY, {})),
        ACTIVE: C.control('SWITCH', ACTIVE, PLACE[ACTIVE], alias=ALIASES[ACTIVE], hint='', desc=DESC[ACTIVE],
                          advanced_setting=advanced(ACTIVE, {})),
    }
    if title_id:
        built[NAME]['controlId'] = title_id
    built[COMPLETE] = C.control('FORMULA_FUNC', COMPLETE, PLACE[COMPLETE], alias=ALIASES[COMPLETE], hint='',
                                desc=DESC[COMPLETE], advanced_setting=advanced(COMPLETE, {}),
                                extra={'enumDefault2': 2,                              # 2 = a text result
                                       'dataSource': function_source(f'TRIM({ref(built[NAME])})')})
    for name, c in built.items():
        c['fieldPermission'] = PERMISSION.get(name, '111')
        c['attribute'] = 1 if name == TITLE else 0
    return [built[n] for n in (NAME, COLOR, CATEGORY, ACTIVE, COMPLETE)]


def step_fields():
    """Three pinned saves, each only when it is needed:

      1. the empty worksheet gets Name (the stock title's id reused), Color, Category, Active and Complete Name; the
         other two stock controls are left out. A single Relation to its own worksheet comes back two-way: the
         server adds the reverse itself, as "Child" at row 9999 (BUILDING.md);
      2. Parent Complete Name — a stored lookup through Category of the parent's Complete Name — and Complete Name
         rewritten to read it, in one save, as 08 does;
      3. places, aliases, descriptions, permissions, the reverse renamed Child Tags with its columns, and
         Category's picker filter."""
    existing = guard(fresh=True)
    f = hap.by_name(existing)
    if not any(n in f for n in PLACE if n not in STOCK) and len(existing) <= 3:
        ctrls, version = C.controls_with_version(ws())
        hap.backup('contacttags_controls_pre_fields', ctrls)
        title = next((c for c in ctrls if c.get('attribute') == 1), None)
        C.save_controls(ws(), first_controls(title and title['controlId']), version=version)
        print(f'  first save: {[NAME, COLOR, CATEGORY, ACTIVE, COMPLETE]} (the stock title id '
              f'{title and title["controlId"]} reused for {NAME})')
    f = fields_of()
    missing = [n for n in (NAME, COLOR, CATEGORY, ACTIVE, COMPLETE) if n not in f]
    if missing:
        sys.exit(f'controls missing after the first save: {missing} — the worksheet is no longer empty, so they are '
                 'not re-added here; look at it first')
    if not reverse_of(hap.controls(ws())):
        sys.exit(f"{CATEGORY}'s reverse is not on the worksheet (reserved id {f[CATEGORY].get('sourceControlId')!r}). "
                 'The server makes a self-relation\'s reverse itself, and writing one by hand duplicates the control '
                 '(BUILDING.md) — look at it first')
    if PARENT_COMPLETE not in f:
        ctrls, version = C.controls_with_version(ws())
        hap.backup('contacttags_controls_pre_lookup', ctrls)
        f = hap.by_name(ctrls)
        lookup = C.control('SHEET_FIELD', PARENT_COMPLETE, PLACE[PARENT_COMPLETE], alias=ALIASES[PARENT_COMPLETE],
                           hint='', data_source=f[CATEGORY]['controlId'], source_control_id=f[COMPLETE]['controlId'],
                           extra={'strDefault': '00'})              # '00' = stored, so a formula can read it
        lookup['fieldPermission'] = PERMISSION[PARENT_COMPLETE]
        ctrls.append(lookup)
        f[PARENT_COMPLETE] = lookup
        f[COMPLETE]['dataSource'] = function_source(complete_name_expression(f))
        C.save_controls(ws(), ctrls, version=version)
        print(f'  {PARENT_COMPLETE} added and {COMPLETE} rewritten to read it')
    place_controls()


def place_controls():
    """One pinned full save for everything `desired` and `advanced` own, the reverse's name included — only when
    something differs. The control set itself must not change."""
    ctrls, version = C.controls_with_version(ws())
    reverse = reverse_of(ctrls)
    renamed = reverse is not None and reverse['controlName'] != CHILDREN
    if renamed:
        print(f"  {reverse['controlName']!r} ({reverse['controlId']}) renamed to {CHILDREN!r}")
        reverse['controlName'] = CHILDREN
    changed = layout_differences(ctrls)
    if changed or renamed:
        hap.backup('contacttags_controls_pre_place', ctrls)
        f = hap.by_name(ctrls)
        for c in ctrls:
            name = c['controlName']
            if name not in PLACE:
                continue
            c.update(desired(c, f))
            c['advancedSetting'] = {**(c.get('advancedSetting') or {}), **advanced(name, f)}
            if name == COLOR:
                c['options'] = [dict(o) for o in OPTIONS]
            if name == COMPLETE:
                c['dataSource'] = function_source(complete_name_expression(f))
        before = sorted(c['controlId'] for c in ctrls)
        C.save_controls(ws(), ctrls, version=version)
        after = sorted(c['controlId'] for c in hap.controls(ws()))
        if after != before:
            sys.exit(f'the placing save changed the control set: {sorted(set(after) ^ set(before))}')
        print('  placed:', json.dumps(changed, ensure_ascii=False)[:2000])
    else:
        print('  controls already as specified; nothing saved')
    left = layout_differences(hap.controls(ws()))
    if left:
        sys.exit(f'the controls read back with differences: {json.dumps(left, ensure_ascii=False)}')
    for c in hap.controls(ws()):
        C.remember('controls', KEY + c['controlName'], c['controlId'])
    print('  ' + json.dumps(computed_state(), ensure_ascii=False))
    C.show(ws())


def computed_state():
    """Complete Name, its lookup and the reverse, read back with ids turned into names."""
    ctrls = hap.controls(ws())
    f = hap.by_name(ctrls)
    names = {c['controlId']: c['controlName'] for c in ctrls}
    readable = lambda s: ''.join(names.get(x, x) if len(x) == 24 else x for x in (s or '').split('$'))
    out = {}
    if COMPLETE in f:
        out[COMPLETE] = dict(type=f[COMPLETE]['type'], result=f[COMPLETE].get('enumDefault2'),
                             expression=readable(expression_of(f[COMPLETE])))
    if PARENT_COMPLETE in f:
        out[PARENT_COMPLETE] = dict(type=f[PARENT_COMPLETE]['type'], stored=f[PARENT_COMPLETE].get('strDefault'),
                                    through=readable(f[PARENT_COMPLETE].get('dataSource')),
                                    of=names.get(f[PARENT_COMPLETE].get('sourceControlId')))
    if CATEGORY in f:
        out[CATEGORY] = dict(type=f[CATEGORY]['type'], target=f[CATEGORY].get('dataSource') == ws(),
                             single=f[CATEGORY].get('enumDefault') == 1,
                             reverse=names.get(f[CATEGORY].get('sourceControlId')))
    if CHILDREN in f:
        out[CHILDREN] = dict(type=f[CHILDREN]['type'], multi=f[CHILDREN].get('enumDefault') == 2,
                             pairs_with=names.get(f[CHILDREN].get('sourceControlId')),
                             columns=[names.get(x) for x in f[CHILDREN].get('showControls') or []])
    return out


COMPUTED_WANT = {
    COMPLETE: dict(type=53, result=2, expression=f'IF(ISBLANK({PARENT_COMPLETE}),TRIM({NAME}),'
                                                 f'CONCAT({PARENT_COMPLETE}," / ",TRIM({NAME})))'),
    PARENT_COMPLETE: dict(type=30, stored='00', through=CATEGORY, of=COMPLETE),
    CATEGORY: dict(type=29, target=True, single=True, reverse=CHILDREN),
    CHILDREN: dict(type=29, multi=True, pairs_with=CATEGORY, columns=[NAME, COLOR]),
}


# ── 2 · views ───────────────────────────────────────────────────────────────

COLUMNS = (NAME, CATEGORY, COLOR)                   # Odoo's list: name, parent_id labelled Category, color
CTIME = {'controlId': 'ctime', 'type': 16, 'controlName': 'Created'}
RELATION_GROUP = 11                                 # a Relation's group-by filterType (captured from the UI,
                                                    # Nocoly Sales app, 13 Sep 2026)


def group_setting(f):
    return {'groupsetting': json.dumps([{'controlId': f[CATEGORY]['controlId'], 'filterType': RELATION_GROUP}],
                                       separators=(',', ':')),
            'groupsorts': '', 'groupcustom': '', 'groupshow': '0', 'groupfilters': '[]', 'groupopen': ''}


def view_specs():
    f = fields_of()
    columns = [f[n]['controlId'] for n in COLUMNS]
    sort = C.sort_spec([f[NAME], CTIME])            # Odoo's _order = 'name, id'
    active = lambda op: dict(viewType='table', filter=C.switch_filter(f[ACTIVE], op), tableFields=columns)
    return {VIEW: (active('eq'), sort, columns), BY_CATEGORY: (active('eq'), sort, columns),
            ARCHIVED: (active('ne'), sort, columns)}


def view_state(info):
    names = {c['controlId']: c['controlName'] for c in hap.controls(ws())}
    names['ctime'] = 'Created'
    group = json.loads((info.get('advancedSetting') or {}).get('groupsetting') or '[]')
    return dict(columns=[names.get(x, x) for x in info.get('showControls') or []],
                sort=[(names.get(s['controlId'], s['controlId']), s['isAsc']) for s in info.get('moreSort') or []],
                sortCid=names.get(info.get('sortCid'), info.get('sortCid')), sortType=info.get('sortType'),
                filters=[(names.get(x['controlId']), x['filterType'], x.get('values'))
                         for x in info.get('filters') or []],
                group=[(names.get(g.get('controlId')), g.get('filterType')) for g in group])


def view_want(name):
    return dict(columns=list(COLUMNS), sort=[(NAME, True), ('Created', True)], sortCid=NAME, sortType=2,
                filters=[(ACTIVE, C.NE if name == ARCHIVED else C.EQ, ['1'])],
                group=[(CATEGORY, RELATION_GROUP)] if name == BY_CATEGORY else [])


def view_differences():
    live = hap.listing('worksheet', 'view', 'list', ws(), '-a', APP)
    out = {}
    if [v['name'] for v in live] != list(VIEWS):
        out['order'] = [v['name'] for v in live]
    for name in VIEWS:
        v = next((x for x in live if x['name'] == name), None)
        state = view_state(C.view_info(ws(), APP, v['viewId'])) if v else None
        if state != view_want(name):
            out[name] = (state, view_want(name))
    return out


def step_views():
    """All (active tags, the one that opens), By Category (the same, grouped by Category — Odoo's search offers
    that group-by) and Archived; Name · Category · Color, sorted by Name then creation. The grouping is written
    with `--edit-ad-keys`, so nothing else of the view is re-sent."""
    guard()
    todo = view_differences()
    if todo:
        C.upsert_views(ws(), APP, view_specs(), 'contacttags_views_pre_views', default_view=VIEW)
        f = fields_of()
        view = next(v for v in hap.listing('worksheet', 'view', 'list', ws(), '-a', APP) if v['name'] == BY_CATEGORY)
        setting = group_setting(f)
        hap.run('worksheet', 'view', 'update', ws(), view['viewId'], '-a', APP,
                '--view-json', json.dumps({'advancedSetting': setting}),
                '--edit-attrs', 'advancedSetting', '--edit-ad-keys', ','.join(setting))
        print('  order:', C.sort_views(ws(), APP, list(VIEWS)))
    else:
        print('  views already as specified; nothing saved')
    left = view_differences()
    if left:
        sys.exit(f'views read back with differences: {json.dumps(left, ensure_ascii=False)}')
    for v in hap.listing('worksheet', 'view', 'list', ws(), '-a', APP):
        C.remember('views', KEY + v['name'], v['viewId'])
        info = C.view_info(ws(), APP, v['viewId'])
        print(f"  {v['name']:<12} {v['viewId']}  {json.dumps(view_state(info), ensure_ascii=False)}")


# ── 3 · roles ───────────────────────────────────────────────────────────────

def step_roles():
    """roles.py owns the app's roles; its ORDER and matrices carry Contact Tags — **the cell each role has on
    Contacts and States** (Accounting Administrator full; Accountant and Invoicing view · add · edit; Accounting
    Read-only view). Odoo's ir.model.access.csv reads res.partner.category to base.group_user and writes it from
    base.group_partner_manager, as it does res.country.state (owner, 22 Sep 2026). `roles.step_plan` lists what
    `create` would write; `create` runs only when every change is on this worksheet or on Incoterms."""
    import roles
    plan = roles.step_plan()
    foreign = sorted({w for changes in plan.values() for w in changes} - {WORKSHEET, 'Incoterms'})
    if foreign:
        sys.exit(f'roles.py create would also change {foreign} — not run; see the plan above')
    if not any(plan.values()):
        print('  roles already as specified; nothing saved')
        return roles.step_check()
    roles.step_create()
    return roles.step_check()


# ── self-check ──────────────────────────────────────────────────────────────

def relation(value):
    """A Relation cell from `record get`: [{'sid': rowid, 'name': title}, …] — as a list of (rowid, title)."""
    if isinstance(value, str):
        value = json.loads(value) if value.startswith('[') else []
    if not isinstance(value, list):
        return []
    return [(v.get('sid'), v.get('name')) for v in value if isinstance(v, dict)]


def read_tag(rowid):
    """One tag through `record get` (by alias) and through the listing (by control id)."""
    d = hap.run('worksheet', 'record', 'get', ws(), rowid, '-a', APP)['data']
    f = fields_of()
    listed = next((r for r in C.records(ws(), APP) if r['rowid'] == rowid), {})
    parents = relation(d.get('parent_id'))
    children = d.get('child_ids')
    return dict(rowid=rowid, name=d.get('name'), complete=d.get('display_name') or '',
                complete_list=listed.get(f[COMPLETE]['controlId']),
                parent=parents[0][1] if parents else None, parent_rowid=parents[0][0] if parents else None,
                parent_complete=d.get('parent_complete_name') or '',
                children=children if isinstance(children, int) else len(relation(children)),
                active=d.get('active'), active_list=listed.get(f[ACTIVE]['controlId']),
                color=d.get('color'))


def view_names(name):
    view = next(v for v in hap.listing('worksheet', 'view', 'list', ws(), '-a', APP) if v['name'] == name)
    res = hap.run('worksheet', 'record', 'list', ws(), '-a', APP, '-n', '200', '--view-id', view['viewId'],
                  '--use-field-id-as-key')
    data = res.get('data', res) if isinstance(res, dict) else res
    rows = (data.get('rows') if isinstance(data, dict) else data) or []
    name_id = fields_of()[NAME]['controlId']
    return [r.get(name_id) for r in rows]


def attempt(*args):
    try:
        out = hap.run(*args)
    except RuntimeError as error:
        return True, str(error)[:300]
    data = out.get('data', out) if isinstance(out, dict) else {}
    code = (out.get('resultCode') if isinstance(out, dict) else None) or \
           (data.get('resultCode') if isinstance(data, dict) else None)
    return code not in (None, 1), json.dumps(out, ensure_ascii=False)[:300]


def step_selfcheck():
    """Through the CLI, on three TEST tags:

      1. three levels read "TEST Parent Tag / TEST Child Tag / TEST Grandchild Tag";
      2. renaming the parent carries down the chain, and back;
      3. the parent's Child Tags counts the child;
      4. a tag made its own parent — the picker filter is the browser's only, so the API is expected to accept it;
         what Complete Name then reads is recorded, and the parent is put back;
      5. switching Active off moves a tag from All to Archived;
      6. all three are left **archived** (Active off)."""
    guard()
    f = fields_of()
    cid = lambda n: f[n]['controlId']
    live = {r.get(cid(NAME)): r['rowid'] for r in C.records(ws(), APP)}
    problems, notes, rowids = [], [], {}
    parent = None
    for name in TESTS:
        cells = [{'id': cid(NAME), 'value': name}, {'id': cid(ACTIVE), 'value': 1}]
        if parent:
            cells.append({'id': cid(CATEGORY), 'value': [parent]})
        if name in live:
            rowid = live[name]
            hap.run('worksheet', 'record', 'update', ws(), rowid, '-a', APP, '--fields-json', json.dumps(cells))
        else:
            rowid = C.row_id(hap.run('worksheet', 'record', 'create', ws(), '-a', APP,
                                     '--fields-json', json.dumps(cells)))
            print(f'  created {name}: {rowid}')
        rowids[name] = rowid
        C.remember('records', KEY + name, rowid)
        parent = rowid
        time.sleep(3)
    time.sleep(6)
    top, mid, leaf = (rowids[n] for n in TESTS)
    want = ' / '.join(TESTS)
    t = read_tag(leaf)
    print(f"  1. three levels: {t['complete']!r} (listing {t['complete_list']!r}; lookup {t['parent_complete']!r}); "
          f"Color {t['color']!r} — an API create applies no default")
    if t['complete'] != want:
        problems.append(f"three levels: {t['complete']!r}")

    hap.run('worksheet', 'record', 'update', ws(), top, '-a', APP,
            '--fields-json', json.dumps([{'id': cid(NAME), 'value': 'TEST Renamed Tag'}]))
    time.sleep(10)
    renamed = read_tag(leaf)['complete']
    print(f"  2. renaming the parent: the grandchild reads {renamed!r}")
    if renamed != 'TEST Renamed Tag / TEST Child Tag / TEST Grandchild Tag':
        problems.append(f'rename down the chain: {renamed!r}')
    hap.run('worksheet', 'record', 'update', ws(), top, '-a', APP,
            '--fields-json', json.dumps([{'id': cid(NAME), 'value': TESTS[0]}]))
    time.sleep(10)
    if read_tag(leaf)['complete'] != want:
        problems.append('the parent was renamed back and the chain did not follow')

    t = read_tag(top)
    print(f"  3. {TESTS[0]}: Child Tags {t['children']!r}")
    if t['children'] != 1:
        problems.append(f"Child Tags of the parent: {t['children']!r}")

    refused, message = attempt('worksheet', 'record', 'update', ws(), top, '-a', APP, '--fields-json',
                               json.dumps([{'id': cid(CATEGORY), 'value': [top]}]))
    time.sleep(6)
    itself = read_tag(top)
    print(f"  4. {TESTS[0]} as its own parent through the API: {'refused' if refused else 'accepted'}; it read "
          f"{itself['complete']!r}")
    notes.append(f"own parent through the API {'refused' if refused else 'accepted'} ({itself['complete']!r})")
    hap.run('worksheet', 'record', 'update', ws(), top, '-a', APP, '--fields-json',
            json.dumps([{'id': cid(CATEGORY), 'value': []}]))
    time.sleep(8)
    if read_tag(top)['complete'] != TESTS[0] or read_tag(leaf)['complete'] != want:
        problems.append(f"after clearing the parent: {read_tag(top)['complete']!r} / {read_tag(leaf)['complete']!r}")

    hap.run('worksheet', 'record', 'update', ws(), leaf, '-a', APP, '--fields-json',
            json.dumps([{'id': cid(ACTIVE), 'value': 0}]))
    time.sleep(4)
    in_all, in_archived = TESTS[2] in view_names(VIEW), TESTS[2] in view_names(ARCHIVED)
    print(f'  5. {TESTS[2]} switched off: in {VIEW} {in_all}, in {ARCHIVED} {in_archived}')
    if in_all or not in_archived:
        problems.append(f'Active off: all={in_all} archived={in_archived}')

    for name in TESTS:
        hap.run('worksheet', 'record', 'update', ws(), rowids[name], '-a', APP, '--fields-json',
                json.dumps([{'id': cid(ACTIVE), 'value': 0}]))
    time.sleep(4)
    left = {n: read_tag(rowids[n])['active'] for n in TESTS}
    print(f'  6. left archived: {left}')
    if any(str(v) not in ('0', '', 'None') for v in left.values()):
        problems.append(f'left active: {left}')
    print('  selfcheck: ' + ('OK — ' + '; '.join(notes) if not problems
                             else 'DIFFERENCES\n    ' + '\n    '.join(problems)))
    return len(problems)


def roles_differences():
    """This worksheet's cell in each business role, read back against roles.py's table."""
    import roles
    out = []
    for role, (_, matrix) in roles.ROLES.items():
        role_id = hap.ids()['roles'].get(role)
        got = roles.cell(*roles.scopes(role_id).get(WORKSHEET, (None, None))) if role_id else None
        if got != matrix.get(WORKSHEET):
            out.append(f'role {role}: {got!r}, want {matrix.get(WORKSHEET)!r}')
    return out


# ── check ───────────────────────────────────────────────────────────────────

def step_check():
    """Controls, the formula, the lookup, the reverse, the picker filter, the views, no rules and no buttons, and
    the menu place, against this spec; exits non-zero on a difference."""
    problems = []
    ctrls = hap.controls(ws())
    f = hap.by_name(ctrls)
    if sorted(f) != sorted(PLACE):
        problems.append(f'controls {sorted(f)}')
    problems += [f'{n}: {d}' for n, d in layout_differences(ctrls).items()]
    title = [c['controlName'] for c in ctrls if c.get('attribute') == 1]
    if title != [TITLE]:
        problems.append(f'title {title}')
    state = computed_state()
    for name, want in COMPUTED_WANT.items():
        if state.get(name) != want:
            problems.append(f'{name}: {state.get(name)} != {want}')
    left = view_differences()
    if left:
        problems.append(f'views {json.dumps(left, ensure_ascii=False)}')
    if hap.listing('worksheet', 'custom-actions', ws()):
        problems.append('this worksheet has a button; 20 §3 gives it none')
    if hap.listing('worksheet', 'rules', ws()):
        problems.append('this worksheet has a rule; 20 §3 gives it none')
    problems += roles_differences()
    items = next(s for s in C.app_info(APP)['sections'] if s['id'] == SECTION_ID)['items']
    names = [i['name'] for i in items]
    if WORKSHEET not in names or names.index(WORKSHEET) != names.index(AFTER) + 1:
        problems.append(f'{SECTION} reads {names}')
    print('  check: ' + ('OK — seven controls with their places and permissions, Complete Name the title and built '
                         'on the lookup, Category two-way with Child Tags and its picker filter, the twelve colours, '
                         'All · By Category · Archived, no rules and no buttons, the four roles\' cells and the menu place'
                         if not problems else 'DIFFERENCES\n    ' + '\n    '.join(problems)))
    return len(problems)


def step_all():
    for name in ('create', 'fields', 'views', 'roles'):
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
    'all': step_all,
    'check': step_check,
    'selfcheck': step_selfcheck,
    'show': show,
}

if __name__ == '__main__':
    step = sys.argv[1] if len(sys.argv) > 1 else 'check'
    if step not in STEPS:
        raise SystemExit(f"Unknown step {step!r}; choose from {', '.join(STEPS)}")
    result = STEPS[step](*sys.argv[2:])
    if step in ('check', 'all', 'selfcheck', 'roles') and result:
        sys.exit(1)
