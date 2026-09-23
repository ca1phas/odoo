#!/usr/bin/env python3
"""Build the Incoterms worksheet (Odoo account.incoterms) in ERP Master.

Bundle `binc`: one worksheet, standing alone. Odoo ships the eleven ICC trade terms as data
(addons/account/data/account_incoterms_data.xml), so the seed needs no tenant. The wiring — Incoterm on Orders and
Invoices, Incoterm Location on Invoices — is a later step and is **not** done here: nothing in this script writes to
another worksheet. Requirements: nocoly/worksheets/19-incoterms.md. Generic helpers: common.py. Run from the repo root
with the CLI's interpreter:

    ~/.hap-venv/bin/python nocoly/build/incoterms.py create    # 0. the worksheet in menu group Invoicing, after
                                                               #    Payment Terms (Odoo: Configuration › Invoicing ›
                                                               #    Payment Terms, then Incoterms)
    ~/.hap-venv/bin/python nocoly/build/incoterms.py fields    # 1. the five controls in one pinned save of the empty
                                                               #    worksheet, then a pinned placing save if needed
    ~/.hap-venv/bin/python nocoly/build/incoterms.py rules     # 2. the code-length validation rule
    ~/.hap-venv/bin/python nocoly/build/incoterms.py views     # 3. All (active) and Archived
    ~/.hap-venv/bin/python nocoly/build/incoterms.py buttons   # 4. Archive / Unarchive, the house pair
    ~/.hap-venv/bin/python nocoly/build/incoterms.py roles     # 5. roles.py `plan`, then `create` only if the plan
                                                               #    touches nothing but this worksheet
    ~/.hap-venv/bin/python nocoly/build/incoterms.py seed      # 6. Odoo's eleven, matched by code, read back
    ~/.hap-venv/bin/python nocoly/build/incoterms.py all       # every step above, then check

    ~/.hap-venv/bin/python nocoly/build/incoterms.py check     # controls, rule, views, buttons, workflows, records
    ~/.hap-venv/bin/python nocoly/build/incoterms.py selfcheck # Display Name, the length rule on an API write and
                                                               #    Archive / Unarchive, on TEST Incoterm (left
                                                               #    archived)
    ~/.hap-venv/bin/python nocoly/build/incoterms.py records   # every record through both read paths
    ~/.hap-venv/bin/python nocoly/build/incoterms.py show      # the live control list

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
SECTION = 'Invoicing'
SECTION_ID = '6aa8f3ecbf00c316381dbbe8'
WORKSHEET = 'Incoterms'
KEY = WORKSHEET + ': '                              # ids.json key prefix for everything this worksheet owns
ALIAS = 'account_incoterms'
AFTER = 'Payment Term Lines'                        # the menu group reads … Payment Terms · Payment Term Lines
                                                    # (hidden) · Incoterms · Invoices …
REMARK = ('The international trade terms — FOB, CIF, DDP and the rest — that say who pays for and carries the risk '
          'of each leg of a shipment')
ICON = 'sys_7_1_truck'                              # `hap icon search 运输`


def ws():
    return hap.ids()['worksheets'][WORKSHEET]


def refuse_sales():
    if APP == SALES_APP:
        sys.exit('ids.json points at the Sales app — refusing to write')


# ── the form ────────────────────────────────────────────────────────────────

NAME, CODE, DISPLAY, ACTIVE, CODE_LEN = 'Name', 'Code', 'Display Name', 'Active', 'Code length'
STOCK = {'Name', 'Description', 'Attachment', '名称', '描述', '附件'}

# Odoo's form is one group, Name then Code. HAP draws the title (Display Name) at the head of the record; it also
# sits on the form, read-only and off the create form, as 04's Display Name does. The two hidden controls sit under.
PLACE = {
    NAME: (0, 0, 6), CODE: (0, 1, 6),
    DISPLAY: (1, 0, 6),
    ACTIVE: (2, 0, 6), CODE_LEN: (2, 1, 6),
}
KIND = {NAME: 'TEXT', CODE: 'TEXT', DISPLAY: 'FORMULA_FUNC', ACTIVE: 'SWITCH', CODE_LEN: 'FORMULA_FUNC'}
ALIASES = {NAME: 'name', CODE: 'code', DISPLAY: 'display_name', ACTIVE: 'active',
           CODE_LEN: 'code_length'}             # not an Odoo field: the length the rule reads
TITLE = DISPLAY
HINTS = {}                                          # Odoo's form carries no placeholder
DESC = {  # for the app's users only (owner's rule, 22 Sep 2026); Odoo's help where it reads well
    NAME: 'Incoterms are series of sales terms. They are used to divide transaction costs and responsibilities '
          'between buyer and seller and reflect state-of-the-art transportation practices.',
    CODE: 'The standard code of the term, at most three characters, e.g. FOB.',
    DISPLAY: 'How the term appears in lists and pickers: [Code] Name.',
    ACTIVE: 'Untick to hide an Incoterm you will not use.',
    CODE_LEN: '',                                   # a helper that needs no explanation has none
}
REQUIRED = {NAME, CODE}
PERMISSION = {DISPLAY: '100',                       # read-only · hidden on create (a hidden title is never a column)
              ACTIVE: '011', CODE_LEN: '011'}       # hidden
RESULT = {DISPLAY: 2, CODE_LEN: 6}                  # a function formula's result type: 2 text · 6 number
CODE_SIZE = 3                                       # Odoo code = fields.Char(size=3)


def ref(c):
    return f"${c['controlId']}$"


def function_source(expression):
    """dataSource of a function formula (type 53), as contacts.py and variants.py write it."""
    return json.dumps({'type': 'mdfunction', 'expression': expression, 'status': 1}, ensure_ascii=False)


def expression(name, f):
    code, title = ref(f[CODE]), ref(f[NAME])
    if name == DISPLAY:
        # Odoo _compute_display_name: '[code] name', or the name alone without a code — 04's expression
        return f'IF(ISBLANK({code}),TRIM({title}),CONCAT("[",TRIM({code}),"] ",TRIM({title})))'
    # The number of characters of the trimmed code (Odoo's web client strips what is typed), counted up to four —
    # 4 means "four or more", which is all the rule needs. HAP's function formula has **no LEN()**: a text or number
    # formula over LEN computes empty, while MID is there and counts from 1 (probed on the seeded records,
    # 22 Sep 2026). So each position is asked in turn whether it holds a character.
    trimmed = f'TRIM({code})'
    out = str(CODE_SIZE + 1)
    for n in range(CODE_SIZE + 1, 0, -1):
        out = f'IF(ISBLANK(MID({trimmed},{n},1)),{n - 1},{out})'
    return out


def advanced(name):
    """The advancedSetting keys this script owns on control `name`."""
    if name == ACTIVE:
        return {'showtype': '0', 'defsource': C.static_default(1)}      # Odoo's default is True
    if KIND[name] == 'FORMULA_FUNC':
        return {'analysislink': '1', 'sorttype': 'en'}
    return {}


def new_control(name, f):
    """A control for the first save. `f` maps names to the controls of the same save (client ids included), which
    the formulas read; the server rewrites those ids to the minted ones (BUILDING.md › Worksheets and fields)."""
    extra = {}
    if KIND[name] == 'FORMULA_FUNC':
        extra = {'enumDefault2': RESULT[name], 'dataSource': function_source(expression(name, f))}
        if RESULT[name] == 6:
            extra['dot'] = 0
    c = C.control(KIND[name], name, PLACE[name], alias=ALIASES[name], hint=HINTS.get(name, ''),
                  desc=DESC.get(name, ''), required=name in REQUIRED, advanced_setting=advanced(name) or None,
                  extra=extra or None)
    c['fieldPermission'] = PERMISSION.get(name, '111')
    c['attribute'] = 1 if name == TITLE else 0
    return c


def desired(c, f):
    """The attributes this script owns on control c, as they should read back."""
    name = c['controlName']
    row, col, size = PLACE[name]
    want = {'row': row, 'col': col, 'size': size, 'sectionId': '', 'alias': ALIASES[name],
            'hint': HINTS.get(name, ''), 'desc': DESC.get(name, ''), 'required': name in REQUIRED,
            'unique': False, 'fieldPermission': PERMISSION.get(name, '111'), 'attribute': 1 if name == TITLE else 0}
    if KIND[name] == 'FORMULA_FUNC':
        want['enumDefault2'] = RESULT[name]
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
                if (c.get(k) or (0 if k in ('attribute', 'enumDefault2') else '' if isinstance(v, str) else False))
                != v}
        settings = c.get('advancedSetting') or {}
        diff.update({f'advancedSetting.{k}': (settings.get(k), v) for k, v in advanced(name).items()
                     if settings.get(k) != v})
        if KIND[name] == 'FORMULA_FUNC' and all(n in f for n in (NAME, CODE)) \
                and expression_of(c) != expression(name, f):
            diff['expression'] = (expression_of(c), expression(name, f))
        if diff:
            out[name] = diff
    return out


def fields_of(worksheet_id=None):
    return hap.by_name(c for c in hap.controls(worksheet_id or ws()) if c['type'] != C.TAB)


# ── guard ───────────────────────────────────────────────────────────────────

VIEW, ARCHIVED = 'All', 'Archived'
BUTTONS = ('Archive', 'Unarchive')
RULE_LENGTH = 'Code has at most three characters'
RULES = (RULE_LENGTH,)
TEST_NAME, TEST_CODE = 'TEST Incoterm', 'TST'       # selfcheck's own record; left archived


def guard(fresh=False):
    """Stop unless the profile reaches ERP Master › Invoicing › Incoterms and the worksheet holds only this script's
    work. `fresh` allows the three stock controls of a brand-new worksheet. Returns the controls."""
    refuse_sales()
    who = hap.run('auth', 'whoami')
    app = C.app_info(APP)
    worksheet = hap.ids().get('worksheets', {}).get(WORKSHEET)
    section = next((s for s in app.get('sections', []) if any(i['id'] == worksheet for i in s['items'])), None)
    if app.get('name') not in hap.APP_NAMES or not section or section['id'] != SECTION_ID:
        sys.exit(f"profile {who.get('profile')!r} does not reach ERP Master › {SECTION} › {WORKSHEET}")
    problems, ctrls = [], hap.controls(worksheet)
    known = set(PLACE) | (STOCK if fresh else set())
    problems += [f"unknown control {c['controlName']!r} ({c['controlId']})" for c in ctrls
                 if c['controlName'] not in known]
    if len(hap.by_name(ctrls)) != len(ctrls):
        problems.append(f'two controls share a name: {sorted(c["controlName"] for c in ctrls)}')
    views = {v['name'] for v in hap.listing('worksheet', 'view', 'list', worksheet, '-a', APP)}
    problems += [f'unknown view {n!r}' for n in views - {VIEW, ARCHIVED, '全部'}]
    buttons = {b['name'] for b in hap.listing('worksheet', 'custom-actions', worksheet)}
    problems += [f'unknown button {n!r}' for n in buttons - set(BUTTONS)]
    rules = {r['name'] for r in hap.listing('worksheet', 'rules', worksheet)}
    problems += [f'unknown rule {n!r}' for n in rules - set(RULES)]
    f = hap.by_name(ctrls)
    if CODE in f and f[CODE].get('alias') == 'code':
        codes = {code for code, _ in SEED}
        problems += [f'unknown record {r["code"]!r} ({r["name"]!r})' for r in read_records().values()
                     if r['code'] not in codes and not str(r['name']).startswith('TEST')]
    if problems:
        sys.exit(f"{WORKSHEET} differs from this script's work — stopping:\n  " + '\n  '.join(problems))
    print(f"  guard: profile {os.environ.get('HAP_PROFILE') or who.get('profile')!r}, ERP Master › {SECTION} › "
          f"{WORKSHEET}, {len(ctrls)} controls, {len(rules)} rules, {len(buttons)} buttons, views {sorted(views)}")
    return ctrls


# ── 0 · the worksheet ───────────────────────────────────────────────────────

def step_create():
    """The worksheet in the existing Invoicing menu group, then moved to just after Payment Terms and its hidden
    lines — Odoo's Configuration › Invoicing menu lists Payment Terms (sequence 10), then Incoterms (20).

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

def step_fields():
    """The five controls in **one pinned save of the empty worksheet**: the stock title's id is reused for Name, the
    two other stock controls are left out, and Display Name carries the title (`attribute` 1) from the start — the
    only control with 1 in the save. The formulas are sent with client ids and read the client ids of Name and Code;
    the server mints real ones and rewrites the references. Then one pinned placing save if anything read back
    differently. A re-run on a built worksheet saves nothing."""
    existing = guard(fresh=True)
    f = hap.by_name(existing)
    if not any(n in f for n in PLACE if n not in STOCK) and len(existing) <= 3:
        ctrls, version = C.controls_with_version(ws())
        hap.backup('incoterms_controls_pre_fields', ctrls)
        title = next((c for c in ctrls if c.get('attribute') == 1), None)
        built = {}
        for name in (NAME, CODE, ACTIVE):
            built[name] = new_control(name, built)
        if title:
            built[NAME]['controlId'] = title['controlId']
        for name in (DISPLAY, CODE_LEN):
            built[name] = new_control(name, built)
        C.save_controls(ws(), [built[n] for n in PLACE], version=version)
        print(f'  first save: {list(PLACE)} (the stock title id {title and title["controlId"]} reused for {NAME})')
    missing = [n for n in PLACE if n not in fields_of()]
    if missing:
        sys.exit(f'controls missing after the first save: {missing} — this worksheet is no longer empty, so they '
                 'are not re-added here; look at it first')
    place_controls()


def place_controls():
    """One pinned full save bringing every control to PLACE, the descriptions, permissions, the formulas and the
    title — only when something differs."""
    ctrls, version = C.controls_with_version(ws())
    changed = layout_differences(ctrls)
    if changed:
        hap.backup('incoterms_controls_pre_place', ctrls)
        f = hap.by_name(ctrls)
        for c in ctrls:
            name = c['controlName']
            if name not in PLACE:
                continue
            c.update(desired(c, f))
            c['advancedSetting'] = {**(c.get('advancedSetting') or {}), **advanced(name)}
            if KIND[name] == 'FORMULA_FUNC':
                c['dataSource'] = function_source(expression(name, f))
        before = sorted(c['controlId'] for c in ctrls)
        C.save_controls(ws(), ctrls, version=version)
        after = sorted(c['controlId'] for c in hap.controls(ws()))
        if after != before:
            sys.exit(f'the placing save changed the control set: {sorted(set(after) ^ set(before))}')
        print('  placed:', json.dumps(changed, ensure_ascii=False)[:1500])
    else:
        print('  controls already as specified; nothing saved')
    left = layout_differences(hap.controls(ws()))
    if left:
        sys.exit(f'the controls read back with differences: {json.dumps(left, ensure_ascii=False)}')
    for c in hap.controls(ws()):
        C.remember('controls', KEY + c['controlName'], c['controlId'])
    C.show(ws())


# ── 2 · the rule ────────────────────────────────────────────────────────────
#
# Odoo's size=3 is a database limit with no wording of its own; 19 §2 asks for a validation rule with a message.
# No filter operator measures length (BUILDING.md › Worksheets and fields), so the rule reads the hidden Code length
# formula. Check type 1 — the form and the server; the server checks only a write that carries one of the condition
# fields, which is why Code itself is a condition too. Hint type 0 — while typing and on submit.

GT = 13
MSG_LENGTH = 'An Incoterm code has at most three characters.'


def length_filters(f):
    """Code is not empty AND Code length > 3. The length is a function formula with a number result, which the
    filter editor treats as a Number (dataType 6)."""
    over = {'controlId': f[CODE_LEN]['controlId'], 'dataType': 6, 'spliceType': 1, 'filterType': GT,
            'value': str(CODE_SIZE), 'values': [str(CODE_SIZE)], 'dynamicSource': [], 'isGroup': False}
    return C.any_of([C.cond(f[CODE], C.NOT_EMPTY), over])


def rule_state(r, names):
    groups = sorted(sorted((names.get(c['controlId'], c['controlId']), c['filterType'],
                            tuple(str(v) for v in c.get('values') or []))
                           for c in g.get('groupFilters') or []) for g in r.get('filters') or [])
    return dict(type=r['type'], disabled=r['disabled'], groups=groups, check=r.get('checkType'),
                hint=r.get('hintType'),
                items=[(i['type'], [names.get(x['controlId']) for x in i['controls']], i.get('message') or '')
                       for i in r.get('ruleItems') or []])


RULE_WANT = dict(type=C.VALIDATION, disabled=False,
                 groups=[sorted([(CODE, C.NOT_EMPTY, ()), (CODE_LEN, GT, (str(CODE_SIZE),))])],
                 check=1, hint=0, items=[(C.ERROR, [CODE], MSG_LENGTH)])


def rule_differences():
    names = {c['controlId']: c['controlName'] for c in hap.controls(ws())}
    live = {r['name']: r for r in hap.listing('worksheet', 'rules', ws())}
    r = live.get(RULE_LENGTH)
    state = rule_state(r, names) if r else None
    return (state if state != RULE_WANT else None), live


def step_rules():
    guard()
    wrong, live = rule_differences()
    if wrong is None and RULE_LENGTH in live:
        print('  rule already as specified; nothing saved')
    else:
        hap.backup('incoterms_rules_pre_rules', list(live.values()))
        f = fields_of()
        args = ['worksheet', 'save-rule', ws(), '--name', RULE_LENGTH, '--type', str(C.VALIDATION),
                '--filters', json.dumps(length_filters(f), ensure_ascii=False),
                '--rule-items', json.dumps([C.item(C.ERROR, f[CODE], message=MSG_LENGTH)], ensure_ascii=False),
                '--check-type', '1', '--hint-type', '0', '--enabled']
        if RULE_LENGTH in live:
            args += ['--rule-id', live[RULE_LENGTH]['ruleId']]
        hap.run(*args)
        print(f"  {'updated' if RULE_LENGTH in live else 'created'} {RULE_LENGTH!r}")
    wrong, live = rule_differences()
    if wrong is not None or RULE_LENGTH not in live:
        sys.exit(f'rule read back as {json.dumps(wrong, ensure_ascii=False)}, want {RULE_WANT}')
    C.remember('rules', KEY + RULE_LENGTH, live[RULE_LENGTH]['ruleId'])
    names = {c['controlId']: c['controlName'] for c in hap.controls(ws())}
    print(f"    {live[RULE_LENGTH]['ruleId']}  {json.dumps(rule_state(live[RULE_LENGTH], names), ensure_ascii=False)}")


# ── 3 · views ───────────────────────────────────────────────────────────────

COLUMNS = (CODE, NAME)                              # Odoo's list: code, name (active column_invisible)
CTIME = {'controlId': 'ctime', 'type': 16, 'controlName': 'Created'}   # no _order: creation order


def view_specs():
    f = fields_of()
    columns = [f[n]['controlId'] for n in COLUMNS]
    sort = C.sort_spec([CTIME])
    return {VIEW: (dict(viewType='table', filter=C.switch_filter(f[ACTIVE], 'eq'), tableFields=columns),
                   sort, columns),
            ARCHIVED: (dict(viewType='table', filter=C.switch_filter(f[ACTIVE], 'ne'), tableFields=columns),
                       sort, columns)}


def view_state(info):
    names = {c['controlId']: c['controlName'] for c in hap.controls(ws())}
    names['ctime'] = 'Created'
    return dict(columns=[names.get(x, x) for x in info.get('showControls') or []],
                sort=[(names.get(s['controlId'], s['controlId']), s['isAsc']) for s in info.get('moreSort') or []],
                sortCid=names.get(info.get('sortCid'), info.get('sortCid')), sortType=info.get('sortType'),
                filters=[(names.get(x['controlId']), x['filterType'], x.get('values'))
                         for x in info.get('filters') or []])


def view_want(name):
    return dict(columns=list(COLUMNS), sort=[('Created', True)], sortCid='Created', sortType=2,
                filters=[(ACTIVE, C.EQ if name == VIEW else C.NE, ['1'])])


def view_differences():
    live = hap.listing('worksheet', 'view', 'list', ws(), '-a', APP)
    out = {}
    if [v['name'] for v in live] != [VIEW, ARCHIVED]:
        out['order'] = [v['name'] for v in live]
    for name in (VIEW, ARCHIVED):
        v = next((x for x in live if x['name'] == name), None)
        state = view_state(C.view_info(ws(), APP, v['viewId'])) if v else None
        if state != view_want(name):
            out[name] = (state, view_want(name))
    return out


def step_views():
    """All (active Incoterms, the one that opens) and Archived, Code · Name, in creation order."""
    guard()
    todo = view_differences()
    if todo:
        C.upsert_views(ws(), APP, view_specs(), 'incoterms_views_pre_views', default_view=VIEW)
        print('  order:', C.sort_views(ws(), APP, [VIEW, ARCHIVED]))
    else:
        print('  views already as specified; nothing saved')
    left = view_differences()
    if left:
        sys.exit(f'views read back with differences: {json.dumps(left, ensure_ascii=False)}')
    for v in hap.listing('worksheet', 'view', 'list', ws(), '-a', APP):
        C.remember('views', KEY + v['name'], v['viewId'])
    C.print_views(ws(), APP)


# ── 4 · buttons ─────────────────────────────────────────────────────────────

MSG_ARCHIVE = 'Are you sure that you want to archive this record?'
BUTTON_STEP = {'Archive': ('Archive the Incoterm', '0'), 'Unarchive': ('Unarchive the Incoterm', '1')}


def step_buttons():
    """Odoo ⚙ Actions › Archive / Unarchive, as on Payment Terms and Taxes: each runs a one-step workflow that
    writes Active on the record it was pressed on; batch allowed, Archive asks first."""
    guard()
    active = fields_of()[ACTIVE]['controlId']
    when = lambda op: {'type': 'group', 'logic': 'AND', 'children': [
        {'type': 'condition', 'field': active, 'operator': op, 'value': ['1']}]}
    buttons = [
        ({'name': 'Archive', 'type': 'triggerWorkflow', 'enableWhen': when('eq'), 'isBatch': True,
          'confirm': True, 'confirmMsg': MSG_ARCHIVE, 'sureName': 'Archive', 'cancelName': 'Cancel'},
         [{'fieldId': active, 'value': '0'}], BUTTON_STEP['Archive'][0]),
        ({'name': 'Unarchive', 'type': 'triggerWorkflow', 'enableWhen': when('ne'), 'isBatch': True},
         [{'fieldId': active, 'value': '1'}], BUTTON_STEP['Unarchive'][0]),
    ]
    C.upsert_buttons(ws(), APP, buttons, KEY, 'incoterms_buttons_pre_buttons')
    problems = button_differences()
    if problems:
        sys.exit('buttons read back with differences:\n  ' + '\n  '.join(problems))
    for name in BUTTONS:
        print(C.structure(hap.ids()['workflows'][KEY + name]))


def button_differences():
    import accounts
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
        if conds != [(ACTIVE, op, ['1'])] or (b.get('confirmMsg') or '') != confirm or not b.get('isBatch'):
            out.append(f"button {name}: filters={conds} confirm={b.get('confirmMsg')!r} isBatch={b.get('isBatch')}")
        pid = hap.ids().get('workflows', {}).get(KEY + name)
        if not pid:
            out.append(f'no workflow id for {name}')
            continue
        proc, byname = accounts.nodes_by_name(pid)
        step, value = BUTTON_STEP[name]
        start = proc['startEventId']
        node = byname.get(step)
        if not node or proc['flowNodeMap'][start].get('nextId') != node['id']:
            out.append(f'{name} workflow: the trigger does not run into {step!r}')
            continue
        s = accounts.step_state(pid, node['id'])
        if s['selectNodeId'] != start or s['fields'] != [(active, value, '')] or s['isException']:
            out.append(f'{name} workflow step: {s}')
        info = hap.run('workflow', 'get', pid)
        info = info.get('data', info)
        if not info.get('enabled') or info.get('publishStatus') != 2:
            out.append(f"{name} workflow enabled={info.get('enabled')} publishStatus={info.get('publishStatus')}")
    return out


# ── 5 · roles ───────────────────────────────────────────────────────────────

def step_roles():
    """roles.py owns the app's roles; its ORDER and matrices carry Incoterms — Accounting Administrator full, the
    other three business roles view, as Payment Terms. `roles.step_plan` lists what its `create` step would write;
    `create` runs only when every change is on this worksheet (or on Contact Tags, the other worksheet of this
    brief). Otherwise the plan is printed and nothing is written."""
    import roles
    plan = roles.step_plan()
    foreign = sorted({w for changes in plan.values() for w in changes} - {WORKSHEET, 'Contact Tags'})
    if foreign:
        sys.exit(f'roles.py create would also change {foreign} — not run; see the plan above')
    if not any(plan.values()):
        print('  roles already as specified; nothing saved')
        return roles.step_check()
    roles.step_create()
    return roles.step_check()


# ── 6 · the eleven ──────────────────────────────────────────────────────────

SEED = [  # addons/account/data/account_incoterms_data.xml, in its order
    ('EXW', 'EX WORKS'),
    ('FCA', 'FREE CARRIER'),
    ('FAS', 'FREE ALONGSIDE SHIP'),
    ('FOB', 'FREE ON BOARD'),
    ('CFR', 'COST AND FREIGHT'),
    ('CIF', 'COST, INSURANCE AND FREIGHT'),
    ('CPT', 'CARRIAGE PAID TO'),
    ('CIP', 'CARRIAGE AND INSURANCE PAID TO'),
    ('DPU', 'DELIVERED AT PLACE UNLOADED'),
    ('DAP', 'DELIVERED AT PLACE'),
    ('DDP', 'DELIVERED DUTY PAID'),
]


def read_records(only=None):
    """{rowid: {...}} through **both** read paths: `common.records` (the listing, by control id — it blanks the
    hidden Active and Code length) and `record get` (by alias). Each field keeps both readings. `only` limits the
    `record get` calls to one rowid."""
    f = fields_of()
    out = {}
    for r in C.records(ws(), APP):
        if only and r['rowid'] != only:
            continue
        got = hap.run('worksheet', 'record', 'get', ws(), r['rowid'], '-a', APP)
        got = got.get('data', got) if isinstance(got, dict) else {}
        row = {'rowid': r['rowid'], 'ctime': got.get('_createdAt')}
        for name in PLACE:
            row[ALIASES[name] + '@list'] = r.get(f[name]['controlId'])
            row[ALIASES[name] + '@get'] = got.get(ALIASES[name])
        row['name'] = row['name@get'] if row['name@get'] is not None else row['name@list']
        row['code'] = row['code@get'] if row['code@get'] is not None else row['code@list']
        row['active'] = first(row['active@get'], row['active@list'])
        out[r['rowid']] = row
    return out


def first(*values):
    """The first reading that holds a value; '' and None are 'nothing read'."""
    return next((v for v in values if v not in (None, '')), None)


def flag(value):
    return str(value) in ('1', 'True', 'true')


def step_seed():
    """Odoo's eleven, matched by Code. A record already right is left alone; one that differs is updated; a missing
    one is created with Name, Code and **Active ticked explicitly** (an API write applies no default, and a record
    with no Active shows in neither view). One create per second, so creation order — the views' sort — is Odoo's
    order. Code is checked against the three-character limit here, since a create is not checked by the rule."""
    guard()
    for code, _ in SEED:
        if len(code) > CODE_SIZE:
            sys.exit(f'seed code {code!r} is longer than {CODE_SIZE}')
    f = fields_of()
    cid = lambda n: f[n]['controlId']
    live = {r['code']: r for r in read_records().values() if not str(r['name']).startswith('TEST')}
    hap.backup('incoterms_records_pre_seed', live)
    written = 0
    for code, name in SEED:
        current = live.get(code)
        if current and current['name'] == name and flag(current['active']):
            continue
        cells = [{'id': cid(NAME), 'value': name}, {'id': cid(CODE), 'value': code}, {'id': cid(ACTIVE), 'value': 1}]
        if current:
            hap.run('worksheet', 'record', 'update', ws(), current['rowid'], '-a', APP,
                    '--fields-json', json.dumps(cells, ensure_ascii=False))
            print(f'  updated {code}: was {current["name"]!r} active={current["active"]!r}')
        else:
            rowid = C.row_id(hap.run('worksheet', 'record', 'create', ws(), '-a', APP,
                                     '--fields-json', json.dumps(cells, ensure_ascii=False)))
            print(f'  created {code} {name}: {rowid}')
            time.sleep(1.1)
        written += 1
    print(f'  {written} records written' if written else '  the eleven already as specified; nothing written')
    if written:
        time.sleep(4)                                 # let the formulas settle before they are read back
    return verify_records(remember=True)


def verify_records(remember=False):
    """The eleven read back through both paths: Name, Code and Display Name from each, Active from `record get`
    (the listing blanks a hidden field, so its empty reading is reported, not trusted), Code length from either."""
    rows = read_records()
    by_code = {r['code']: r for r in rows.values() if not str(r['name']).startswith('TEST')}
    problems = []
    for code, name in SEED:
        r = by_code.get(code)
        if not r:
            problems.append(f'{code}: missing')
            continue
        display = f'[{code}] {name}'
        for path in ('list', 'get'):
            got = (r[f'name@{path}'], r[f'code@{path}'], r[f'display_name@{path}'])
            if got != (name, code, display):
                problems.append(f'{code} via {path}: {got}')
        if not flag(r['active@get']):
            problems.append(f"{code}: Active reads {r['active@get']!r} through record get "
                            f"(listing: {r['active@list']!r})")
        length = first(r['code_length@get'], r['code_length@list'])
        if length is None or float(length) != len(code):
            problems.append(f"{code}: Code length reads {r['code_length@get']!r} / {r['code_length@list']!r}")
    extra = sorted(set(by_code) - {c for c, _ in SEED})
    if extra:
        problems.append(f'records not in the seed: {extra}')
    for code, _ in SEED:
        r = by_code.get(code)
        if r:
            print(f"  {code}  {r['rowid']}  get: {r['name@get']!r} {r['display_name@get']!r} "
                  f"active={r['active@get']!r} len={r['code_length@get']!r}  |  list: {r['name@list']!r} "
                  f"{r['display_name@list']!r} active={r['active@list']!r} len={r['code_length@list']!r}")
    if remember and not problems:
        ids = hap.ids()                               # re-read immediately before the write: ids.json is shared
        records = ids.setdefault('records', {})
        mapping = {KEY + code: by_code[code]['rowid'] for code, _ in SEED}
        if any(records.get(k) != v for k, v in mapping.items()):
            records.update(mapping)
            C.save_ids(ids)
    print('  records: ' + ('OK — the eleven, by both read paths' if not problems
                           else 'DIFFERENCES\n    ' + '\n    '.join(problems)))
    return len(problems)


def view_rows(name):
    """The rows a view returns, in its own order, by Code."""
    view = next(v for v in hap.listing('worksheet', 'view', 'list', ws(), '-a', APP) if v['name'] == name)
    res = hap.run('worksheet', 'record', 'list', ws(), '-a', APP, '-n', '100', '--view-id', view['viewId'],
                  '--use-field-id-as-key')
    data = res.get('data', res) if isinstance(res, dict) else res
    rows = (data.get('rows') if isinstance(data, dict) else data) or []
    code = fields_of()[CODE]['controlId']
    return [r.get(code) for r in rows]


def step_records():
    verify_records()
    for name in (VIEW, ARCHIVED):
        print(f'  {name}: {view_rows(name)}')


# ── self-check ──────────────────────────────────────────────────────────────

def attempt(*args):
    """Run a write expected to be refused; return (refused, message)."""
    try:
        out = hap.run(*args)
    except RuntimeError as error:
        return True, str(error)[:300]
    data = out.get('data', out) if isinstance(out, dict) else {}
    code = (out.get('resultCode') if isinstance(out, dict) else None) or \
           (data.get('resultCode') if isinstance(data, dict) else None)
    return code not in (None, 1), json.dumps(out, ensure_ascii=False)[:300]


def read_one(rowid):
    return read_records(only=rowid).get(rowid)


def step_selfcheck():
    """Through the CLI, on TEST Incoterm (code TST):

      1. Display Name reads "[TST] TEST Incoterm" and Code length 3;
      2. an API update of Code to four characters — refused by the rule, or stored (the form is where it must
         hold; BUILDING.md says the server checks a rule on an update that writes one of its fields);
      3. Archive and Unarchive through their workflows, and the two views following;
      4. the record left **archived**, with its code back at TST."""
    guard()
    f = fields_of()
    cid = lambda n: f[n]['controlId']
    problems, notes = [], []
    test = next((r for r in read_records().values() if r['name'] == TEST_NAME), None)
    cells = [{'id': cid(NAME), 'value': TEST_NAME}, {'id': cid(CODE), 'value': TEST_CODE}, {'id': cid(ACTIVE), 'value': 1}]
    if not test:
        rowid = C.row_id(hap.run('worksheet', 'record', 'create', ws(), '-a', APP,
                                 '--fields-json', json.dumps(cells)))
        print(f'  created {TEST_NAME}: {rowid}')
    else:
        rowid = test['rowid']
        hap.run('worksheet', 'record', 'update', ws(), rowid, '-a', APP, '--fields-json', json.dumps(cells))
    C.remember('records', KEY + TEST_NAME, rowid)
    time.sleep(5)
    r = read_one(rowid)
    print(f"  1. {TEST_NAME}: Display Name {r['display_name@get']!r} (listing {r['display_name@list']!r}), "
          f"Code length {r['code_length@get']!r} (listing {r['code_length@list']!r})")
    if r['display_name@get'] != f'[{TEST_CODE}] {TEST_NAME}':
        problems.append(f"Display Name {r['display_name@get']!r}")
    if first(r['code_length@get'], r['code_length@list']) in (None, '') or \
            float(first(r['code_length@get'], r['code_length@list'])) != 3:
        problems.append(f"Code length {r['code_length@get']!r} / {r['code_length@list']!r}")

    refused, message = attempt('worksheet', 'record', 'update', ws(), rowid, '-a', APP, '--fields-json',
                               json.dumps([{'id': cid(CODE), 'value': 'TSTX'}]))
    time.sleep(4)
    r = read_one(rowid)
    print(f"  2. Code 'TSTX' through record update: {'refused' if refused else 'accepted'} — {message[:160]}; "
          f"Code now reads {r['code@get']!r}, Code length {r['code_length@get']!r}")
    notes.append(f"API update to a 4-character code {'refused' if refused else 'accepted'}")
    if r['code@get'] != TEST_CODE:
        hap.run('worksheet', 'record', 'update', ws(), rowid, '-a', APP, '--fields-json',
                json.dumps([{'id': cid(CODE), 'value': TEST_CODE}]))
        time.sleep(3)

    wf = hap.ids()['workflows']
    for button, want in (('Archive', False), ('Unarchive', True)):
        hap.run('workflow', 'trigger', wf[KEY + button], '-s', rowid)
        time.sleep(8)
        r = read_one(rowid)
        in_all, in_archived = TEST_CODE in view_rows(VIEW), TEST_CODE in view_rows(ARCHIVED)
        print(f"  3. {button}: Active {r['active@get']!r}; in {VIEW} {in_all}, in {ARCHIVED} {in_archived}")
        if flag(r['active@get']) != want or in_all != want or in_archived == want:
            problems.append(f'{button}: active={r["active@get"]!r} all={in_all} archived={in_archived}')
    hap.run('workflow', 'trigger', wf[KEY + 'Archive'], '-s', rowid)
    time.sleep(8)
    r = read_one(rowid)
    print(f"  4. left archived: Active {r['active@get']!r}, Code {r['code@get']!r}")
    if flag(r['active@get']) or r['code@get'] != TEST_CODE:
        problems.append(f"left as active={r['active@get']!r} code={r['code@get']!r}")
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
    """Controls, the rule, the views, the buttons and their workflows, the menu place and the eleven records, against
    this spec; exits non-zero on a difference."""
    problems = []
    ctrls = hap.controls(ws())
    f = hap.by_name(ctrls)
    if sorted(f) != sorted(PLACE):
        problems.append(f'controls {sorted(f)}')
    problems += [f'{n}: {d}' for n, d in layout_differences(ctrls).items()]
    title = [c['controlName'] for c in ctrls if c.get('attribute') == 1]
    if title != [TITLE]:
        problems.append(f'title {title}')
    wrong, live = rule_differences()
    if wrong is not None or RULE_LENGTH not in live or len(live) != 1:
        problems.append(f'rules {sorted(live)}: {wrong}')
    left = view_differences()
    if left:
        problems.append(f'views {json.dumps(left, ensure_ascii=False)}')
    problems += button_differences()
    problems += roles_differences()
    items = next(s for s in C.app_info(APP)['sections'] if s['id'] == SECTION_ID)['items']
    names = [i['name'] for i in items]
    if WORKSHEET not in names or names.index(WORKSHEET) != names.index(AFTER) + 1:
        problems.append(f'{SECTION} reads {names}')
    if verify_records():
        problems.append('records — see above')
    print('  check: ' + ('OK — five controls with their places, permissions and formulas, Display Name the title, '
                         'the length rule, All and Archived, Archive / Unarchive with published workflows, the four roles\' cells, the menu '
                         'place, and the eleven records'
                         if not problems else 'DIFFERENCES\n    ' + '\n    '.join(problems)))
    return len(problems)


def step_all():
    for name in ('create', 'fields', 'rules', 'views', 'buttons', 'roles', 'seed'):
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
    'buttons': step_buttons,
    'roles': step_roles,
    'seed': step_seed,
    'all': step_all,
    'check': step_check,
    'selfcheck': step_selfcheck,
    'records': step_records,
    'show': show,
}

if __name__ == '__main__':
    step = sys.argv[1] if len(sys.argv) > 1 else 'check'
    if step not in STEPS:
        raise SystemExit(f"Unknown step {step!r}; choose from {', '.join(STEPS)}")
    result = STEPS[step](*sys.argv[2:])
    if step in ('check', 'all', 'selfcheck', 'seed', 'roles') and result:
        sys.exit(1)
