#!/usr/bin/env python3
"""Build the Units & Packagings worksheet (Odoo uom.uom, as on casimir.odoo.com saas~19.4) in ERP Master.

    ~/.hap-venv/bin/python nocoly/build/units.py create    # 0. menu group Products (after Contacts) and the worksheet
    ~/.hap-venv/bin/python nocoly/build/units.py fields    # 1. base controls, in one save (fresh worksheet only)
    ~/.hap-venv/bin/python nocoly/build/units.py computed  # 2. Sequence, Absolute Quantity, Parent Path and their lookups
    ~/.hap-venv/bin/python nocoly/build/units.py layout    # 3. positions, hints, permissions, Reference Unit picker
    ~/.hap-venv/bin/python nocoly/build/units.py rules     # 4. the three Odoo constraints (upsert by name)
    ~/.hap-venv/bin/python nocoly/build/units.py views     # 5. Units & Packagings / Archived tables
    ~/.hap-venv/bin/python nocoly/build/units.py buttons   # 6. Archive / Unarchive and their one-step workflows
    ~/.hap-venv/bin/python nocoly/build/units.py seed      # 7. the 30 standard units (upsert by Unit Name), then verify
    ~/.hap-venv/bin/python nocoly/build/units.py verify    # compare with the 19.4 extract; check the stored lookups
    ~/.hap-venv/bin/python nocoly/build/units.py unit km m  # live values of units by name, hidden fields included
    ~/.hap-venv/bin/python nocoly/build/units.py refresh   # re-save stale Reference Units so lookups catch up
    ~/.hap-venv/bin/python nocoly/build/units.py show      # print the live control list

Requirements: nocoly/worksheets/02-units-and-packagings.md. Generic helpers: common.py.
"""
import json, os, sys, time
from decimal import Decimal

import common as C
import hap

APP = hap.ids()['app']
SECTION, WORKSHEET = 'Products', 'Units & Packagings'
KEY = WORKSHEET + ': '                         # ids.json key prefix for everything this worksheet owns


def ws():
    return hap.ids()['worksheets'][WORKSHEET]


# Odoo saas~19.4 uom form: "Unit Name", then "Quantity: [Contains] [Reference Unit]" on one line.
# name -> (row, col, size); rows 2-5 hold the hidden fields and helpers.
PLACE = {
    'Unit Name': (0, 0, 12),
    'Contains': (1, 0, 6), 'Reference Unit': (1, 1, 6),
    'Absolute Quantity': (2, 0, 6), 'Sequence': (2, 1, 6),
    'Reference Absolute Quantity': (3, 0, 6), 'Active': (3, 1, 6),
    'Related UoMs': (4, 0, 12),
    'Parent Path': (5, 0, 6), 'Reference Parent Path': (5, 1, 6),
}
HINTS = {'Reference Unit': 'Reference Unit'}        # every other control gets no placeholder, as in Odoo
DESC = {  # Odoo field help where it has one; how a hidden helper is computed otherwise
    'Contains': 'How much bigger or smaller this unit is compared to the reference UoM for this unit',
    'Active': 'Uncheck the active field to disable a unit of measure without deleting it.',
    'Absolute Quantity': "Contains × the Reference Unit's Absolute Quantity, down the whole chain; "
                         'a unit without a Reference Unit has its own Contains. Odoo uom.uom factor.',
    'Sequence': 'min(int(Contains × 100), 1000) — Odoo _compute_sequence. Views sort on it.',
    'Reference Absolute Quantity': "The Reference Unit's Absolute Quantity (a stored lookup) for the "
                                   'Absolute Quantity formula.',
    'Related UoMs': 'The units whose Reference Unit is this one — Odoo related_uom_ids.',
    'Parent Path': "The record ids from the top of the chain down to this unit, each followed by '/' — "
                   'Odoo parent_path. The recursion check reads it.',
    'Reference Parent Path': "The Reference Unit's Parent Path (a stored lookup).",
}
HIDDEN = ['Absolute Quantity', 'Sequence', 'Reference Absolute Quantity', 'Active', 'Related UoMs',
          'Parent Path', 'Reference Parent Path']
CONTAINS_DOT, FACTOR_DOT = 7, 9       # 0.0166667 needs 7 decimals; 9 keeps chains of small units exact enough


def ctl(kind, name, alias='', **kw):
    return C.control(kind, name, PLACE[name], alias=alias, hint=HINTS.get(name), desc=DESC.get(name),
                     hidden=name in HIDDEN, **kw)


def formula(name, alias, expression, dot):
    """A number formula (FORMULA_NUMBER, custom expression); empty inputs count as 0."""
    return ctl('FORMULA_NUMBER', name, alias=alias, advanced_setting={'nullzero': '1', 'dotformat': '1'},
               extra={'dataSource': expression, 'dot': dot, 'enumDefault': 1})


def ref(c):
    return f"${c['controlId']}$"


# ── 0 · menu group and worksheet ────────────────────────────────────────────

def step_create():
    section = C.ensure_section(APP, SECTION, after='Contacts')
    C.remember('sections', SECTION, section)
    wid = C.ensure_worksheet(APP, section, WORKSHEET, alias='uom_uom', icon='sys_measure-big_office',
                             remark='Odoo uom.uom: units of measure and packagings, each a multiple of its reference unit')
    C.remember('worksheets', WORKSHEET, wid)
    for s in C.app_info(APP)['sections']:
        print(f"  {s['name']:<10} {s['id']}  {[(i['name'], i['id'], i.get('alias')) for i in s['items']]}")


# ── 1 · base controls ───────────────────────────────────────────────────────

def step_fields():
    existing = hap.controls(ws())
    if len(existing) > 3:
        sys.exit(f'{WORKSHEET} already has {len(existing)} controls — refusing to replace them.')
    hap.backup('units_controls_pre_fields', existing)
    title = next(c for c in existing if c.get('attribute') == 1)       # reuse the stock title control's id

    name = ctl('TEXT', 'Unit Name', alias='name', required=True, is_title=True)
    name['controlId'] = title['controlId']
    contains = ctl('NUMBER', 'Contains', alias='relative_factor', required=True,
                   advanced_setting={'defsource': C.static_default(1), 'dotformat': '1'},   # Odoo default=1.0
                   extra={'dot': CONTAINS_DOT})
    reference = ctl('RELATE_SHEET', 'Reference Unit', alias='relative_uom_id', data_source=ws(), multi=False)
    active = ctl('SWITCH', 'Active', alias='active', advanced_setting={'defsource': C.static_default(1)})
    hap.run('worksheet', 'update-fields', ws(), '--controls',
            json.dumps([name, contains, reference, active], ensure_ascii=False))
    C.show(ws())


# ── 2 · computed fields ─────────────────────────────────────────────────────

# A formula's functions are stored with a "c" prefix (cMIN, cINT, cROUNDUP): written without it, the
# server saves the expression and computes an empty value.

def sequence_expression(f):
    """Odoo _compute_sequence: min(int(relative_factor * 100), 1000)."""
    return f"cMIN(cINT({ref(f['Contains'])}*100),1000)"


def factor_expression(f):
    """Contains × (the Reference Unit's Absolute Quantity, or 1 when there is none).

    A number formula has no IF: with empty-as-0, MIN(1, ROUNDUP(ABS(x), 0)) is 1 for any non-zero x and 0
    for an empty lookup, so x + 1 − MIN(1, ROUNDUP(ABS(x), 0)) is x with a Reference Unit and 1 without."""
    c, x = ref(f['Contains']), ref(f['Reference Absolute Quantity'])
    return f'{c}*({x}+1-cMIN(1,cROUNDUP(cABS({x}),0)))'


def path_template(f):
    """Odoo parent_path: the Reference Unit's path, then this record's id and a slash."""
    return f"{ref(f['Reference Parent Path'])}$rowid$/"


def step_computed():
    f = C.fields(ws())
    new = []
    if 'Sequence' not in f:
        new.append(formula('Sequence', 'sequence', sequence_expression(f), 0))
    if 'Absolute Quantity' not in f:              # placeholder until the lookup exists; rewritten below
        new.append(formula('Absolute Quantity', 'factor', ref(f['Contains']), FACTOR_DOT))
    if new:
        C.add_fields(ws(), new)
    ctrls = hap.controls(ws())
    hap.backup('units_controls_pre_computed', ctrls)
    f = hap.by_name(ctrls)
    if 'Reference Absolute Quantity' not in f:
        # The lookup and the formula that uses it go in one save: if HAP refuses the self-referencing
        # chain (Absolute Quantity -> lookup -> the Reference Unit's Absolute Quantity), nothing is left behind.
        lookup = ctl('SHEET_FIELD', 'Reference Absolute Quantity', alias='relative_uom_factor',
                     data_source=f['Reference Unit']['controlId'], source_control_id=f['Absolute Quantity']['controlId'],
                     advanced_setting={'dotformat': '1'},
                     extra={'strDefault': '00', 'dot': FACTOR_DOT})       # '00' = stored, usable in formulas
        ctrls.append(lookup)
        f['Reference Absolute Quantity'] = lookup
        f['Absolute Quantity']['dataSource'] = factor_expression(f)
        hap.run('worksheet', 'update-fields', ws(), '--controls', json.dumps(ctrls, ensure_ascii=False))
    ctrls = hap.controls(ws())
    f = hap.by_name(ctrls)
    if 'Parent Path' not in f:
        # Odoo parent_path ("1/5/9/"), with record ids: what the recursion check reads. A placeholder until
        # its lookup exists. A concatenation can use the system field $rowid$.
        path = ctl('CONCATENATE', 'Parent Path', alias='parent_path', extra={'dataSource': '$rowid$/'})
        C.add_fields(ws(), [path])
        ctrls = hap.controls(ws())
        f = hap.by_name(ctrls)
    if 'Reference Parent Path' not in f:
        lookup = ctl('SHEET_FIELD', 'Reference Parent Path', alias='relative_uom_parent_path',
                     data_source=f['Reference Unit']['controlId'], source_control_id=f['Parent Path']['controlId'],
                     extra={'strDefault': '00'})
        ctrls.append(lookup)
        f['Reference Parent Path'] = lookup
        f['Parent Path']['dataSource'] = path_template(f)
        hap.run('worksheet', 'update-fields', ws(), '--controls', json.dumps(ctrls, ensure_ascii=False))
        ctrls = hap.controls(ws())
        f = hap.by_name(ctrls)
    want = {'Sequence': sequence_expression(f), 'Absolute Quantity': factor_expression(f),
            'Parent Path': path_template(f)}
    stale = {n: e for n, e in want.items() if f[n]['dataSource'] != e}
    for name, expression in stale.items():
        print(f"  {name}: read back {f[name]['dataSource']!r}; rewriting to {expression!r}")
        f[name]['dataSource'] = expression
    if stale:
        hap.run('worksheet', 'update-fields', ws(), '--controls', json.dumps(ctrls, ensure_ascii=False))
    C.show(ws())


# ── 3 · layout ──────────────────────────────────────────────────────────────

def step_layout():
    ctrls = hap.controls(ws())
    hap.backup('units_controls_pre_layout', ctrls)
    f = hap.by_name(ctrls)
    reference = f['Reference Unit']
    # A single self-relation comes back two-way: HAP adds its reverse, named "Child", at row 9999 with no
    # alias. It is Odoo's related_uom_ids, kept hidden.
    reverse = next(c for c in ctrls if c['controlId'] == reference['sourceControlId'])
    reverse.update(controlName='Related UoMs', alias='related_uom_ids')
    for c in ctrls:
        name = c['controlName']
        if name not in PLACE:
            continue
        row, col, size = PLACE[name]
        c.update(row=row, col=col, size=size, sectionId='', hint=HINTS.get(name, ''))
        if name in DESC:
            c['desc'] = DESC[name]
        c['fieldPermission'] = '011' if name in HIDDEN else '111'
    # Odoo's dropdown shows "Days  --8.0 Hours--" (formatted_display_name): the picker card shows Contains
    # and Reference Unit. Odoo's active_test leaves archived units out of the picker.
    reference['showControls'] = [f['Contains']['controlId'], f['Reference Unit']['controlId']]
    reference['advancedSetting']['filters'] = json.dumps([
        {'controlId': f['Active']['controlId'], 'dataType': 36, 'spliceType': 1, 'filterType': 2,
         'values': ['1'], 'value': '1', 'isDynamicsource': False, 'dynamicSource': []}])
    hap.run('worksheet', 'update-fields', ws(), '--controls', json.dumps(ctrls, ensure_ascii=False))
    C.show(ws())


# ── 4 · rules ───────────────────────────────────────────────────────────────

MSG_ZERO = 'The conversion ratio for a unit of measure cannot be 0!'
MSG_MISSING = 'Reference unit of measure is missing.'
MSG_RECURSION = 'Recursion Detected.'


ROWID = {'controlId': 'rowid', 'type': 2}          # the record-id system field, as a rule condition


def contains_own_id(c):
    """Condition: text control c contains this record's id (system field rowid, as a dynamic value)."""
    return {**C.cond(c, C.CONTAINS),
            'dynamicSource': [{'rcid': '', 'cid': 'rowid', 'staticValue': '', 'isAsync': False, 'type': 0}]}


def step_rules():
    f = C.fields(ws())
    enforce = lambda hint: {'check_type': 1, 'hint_type': hint}       # form and API writes
    rules = [  # (name, type, filters, items, options)
        ('Contains cannot be 0', C.VALIDATION,                         # SQL constraint _factor_gt_zero
         C.any_of([C.cond(f['Contains'], C.EQ, 0)]),
         [C.item(C.ERROR, f['Contains'], message=MSG_ZERO)], enforce(0)),
        ('A unit without a Reference Unit contains 1', C.VALIDATION,  # @constrains _check_factor, on save
         C.any_of([C.cond(f['Reference Unit'], C.EMPTY), C.cond(f['Contains'], C.NOT_EMPTY),
                   C.cond(f['Contains'], C.NE, 1)]),
         [C.item(C.ERROR, f['Reference Unit'], message=MSG_MISSING)], enforce(1)),
        # ORM _parent_store_update: the new Reference Unit's Parent Path must not contain this unit. The server
        # checks a rule only when one of its condition fields is in the write, so Reference Unit is a
        # condition too; the lookup is then read from the new Reference Unit. A unit not yet saved has no
        # id and nothing can point at it, so the rule waits for an id.
        ('Reference Unit cannot be the unit or one below it', C.VALIDATION,
         C.any_of([C.cond(f['Reference Unit'], C.NOT_EMPTY), C.cond(ROWID, C.NOT_EMPTY),
                   contains_own_id(f['Reference Parent Path'])]),
         [C.item(C.ERROR, f['Reference Unit'], message=MSG_RECURSION)], enforce(0)),
    ]
    C.upsert_rules(ws(), rules, 'units_rules_pre_rules')


# ── 5 · views ───────────────────────────────────────────────────────────────

def step_views():
    f = C.fields(ws())
    # Odoo list: sequence (drag handle), name, relative_factor, relative_uom_id. Odoo _order is
    # "sequence, relative_uom_id, id"; the planner chose Sequence then Unit Name.
    columns = [f[n]['controlId'] for n in ('Unit Name', 'Contains', 'Reference Unit')]
    sort = C.sort_spec([f['Sequence'], f['Unit Name']])
    views = {
        'Units & Packagings': (dict(viewType='table', filter=C.switch_filter(f['Active'], 'eq'),
                                    tableFields=columns), sort, columns),
        'Archived': (dict(viewType='table', filter=C.switch_filter(f['Active'], 'ne'),     # search filter Archived
                          tableFields=columns), sort, columns),
    }
    for name, vid in C.upsert_views(ws(), APP, views, 'units_views_pre_views', default_view=WORKSHEET).items():
        C.remember('views', KEY + name, vid)
    C.print_views(ws(), APP)


# ── 6 · buttons ─────────────────────────────────────────────────────────────

def step_buttons():
    active = C.fields(ws())['Active']['controlId']
    when = lambda op: {'type': 'group', 'logic': 'AND', 'children': [
        {'type': 'condition', 'field': active, 'operator': op, 'value': ['1']}]}
    buttons = [  # Odoo ⚙ Actions › Archive / Unarchive, as on Contacts
        ({'name': 'Archive', 'type': 'triggerWorkflow', 'enableWhen': when('eq'), 'isBatch': True,
          'confirm': True, 'confirmMsg': 'Are you sure that you want to archive this record?',
          'sureName': 'Archive', 'cancelName': 'Cancel'}, [{'fieldId': active, 'value': '0'}], 'Archive the unit'),
        ({'name': 'Unarchive', 'type': 'triggerWorkflow', 'enableWhen': when('ne'), 'isBatch': True},
         [{'fieldId': active, 'value': '1'}], 'Unarchive the unit'),
    ]
    C.upsert_buttons(ws(), APP, buttons, KEY, 'units_buttons_pre_buttons')
    for key in (KEY + 'Archive', KEY + 'Unarchive'):
        print(C.structure(hap.ids()['workflows'][key]))


# ── 7 · seed ────────────────────────────────────────────────────────────────

# Odoo's standard units (uom/data/uom_data.xml order, so creation order follows Odoo's ids; 19.4 names
# the tonne "t"). (Unit Name, Contains, Reference Unit, Active). References precede their dependents.
SEED = [
    ('Units', '1', None, True), ('Pack of 6', '6', 'Units', True), ('Dozens', '12', 'Units', False),
    ('Hours', '1', None, True), ('Days', '8', 'Hours', True), ('Minutes', '0.0166667', 'Hours', True),
    ('mm', '1', None, True), ('cm', '10', 'mm', False), ('m', '100', 'cm', True), ('km', '1000', 'm', False),
    ('m²', '1', None, True),
    ('ml', '1', None, True), ('L', '1000', 'ml', True), ('m³', '1000', 'L', False),
    ('g', '1', None, True), ('kg', '1000', 'g', True), ('t', '1000', 'kg', True),
    ('oz', '28.3495', 'g', False), ('lb', '16', 'oz', False),
    ('in', '2.54', 'cm', False), ('ft', '12', 'in', False), ('yd', '3', 'ft', False), ('mi', '1760', 'yd', False),
    ('ft²', '0.092903', 'm²', False),
    ('fl oz (US)', '0.0295735', 'L', False), ('qt (US)', '32', 'fl oz (US)', False), ('gal (US)', '4', 'qt (US)', False),
    ('in³', '0.0163871', 'L', False), ('ft³', '1728', 'in³', False),
    ('KWH', '1', None, True),
]
REFERENCE = os.path.join(hap.HERE, '..', 'reference', 'odoo-19.4', 'uom.uom.md')


def reference_table():
    """The 30 records of the 19.4 extract: name -> dict(contains, ref, factor, active, sequence)."""
    out = {}
    for line in open(REFERENCE):
        cells = [x.strip() for x in line.strip().strip('|').split('|')]
        if len(cells) == 7 and cells[4] in ('yes', 'no'):
            out[cells[0]] = dict(contains=cells[1], ref=cells[2] or None, factor=cells[3],
                                 active=cells[4] == 'yes', sequence=int(cells[5]))
    return out


def number(v):
    return Decimal(str(v)) if v not in (None, '') else None


def fmt(d):
    return 'None' if d is None else format(d.normalize(), 'f')


def read_unit(rowid):
    """One unit through `record get` (by alias). `record list` returns hidden fields empty."""
    d = hap.run('worksheet', 'record', 'get', ws(), rowid, '-a', APP)['data']
    refs = d.get('relative_uom_id') or []
    if isinstance(refs, str):
        refs = json.loads(refs) if refs.startswith('[') else []
    return dict(rowid=rowid, name=d.get('name'), contains=number(d.get('relative_factor')),
                ref=(refs[0].get('name') if refs else None), ref_rowid=(refs[0].get('sid') if refs else None),
                active=str(d.get('active')) == '1', sequence=number(d.get('sequence')),
                factor=number(d.get('factor')), ref_factor=number(d.get('relative_uom_factor')),
                path=d.get('parent_path') or '', ref_path=d.get('relative_uom_parent_path') or '',
                related=d.get('related_uom_ids'))


def read_units():
    """Live units by name (see read_unit)."""
    name = C.fields(ws())['Unit Name']['controlId']
    return {r[name]: read_unit(r['rowid']) for r in C.records(ws(), APP)}


def depth(unit, units):
    """How many Reference Units sit above a unit (a missing reference ends the chain; capped against cycles)."""
    by_row, n = {u['rowid']: u for u in units.values()}, 0
    while unit and unit['ref_rowid'] and n < 50:
        unit, n = by_row.get(unit['ref_rowid']), n + 1
    return n


def stale(units):
    """Units whose stored lookups do not match their Reference Unit's current values, top of the chain first."""
    by_row = {u['rowid']: u for u in units.values()}
    out = []
    for u in units.values():
        parent = by_row.get(u['ref_rowid'])
        want = (parent['factor'], parent['path']) if parent else (None, '')
        if (u['ref_factor'], u['ref_path']) != want or u['path'] != u['ref_path'] + u['rowid'] + '/':
            out.append(u)
    return sorted(out, key=lambda x: depth(x, units))


def refresh(units, rounds=4):
    """Re-save the Reference Unit of stale units (unchanged value) until the chain is consistent.

    A record-level save re-reads a stored lookup and passes the change down the chain; the recompute
    HAP runs after a formula or lookup definition changes does not chain, and can leave rows stale."""
    for _ in range(rounds):
        todo = stale(units)
        if not todo:
            return units
        top = depth(todo[0], units)
        for u in [u for u in todo if depth(u, units) == top]:
            print(f"  refreshing {u['name']} (lookups {u['ref_factor']}, {u['ref_path'][-9:]!r})")
            hap.run('worksheet', 'record', 'update', ws(), u['rowid'], '-a', APP, '--fields-json', json.dumps(
                [{'id': 'relative_uom_id', 'value': [u['ref_rowid']] if u['ref_rowid'] else []}]))
        time.sleep(8)
        units = read_units()
    return units


def printable(units):
    return {k: {f: (str(v) if isinstance(v, Decimal) else v) for f, v in u.items()} for k, u in units.items()}


def step_seed(*only):
    """Create the missing units and correct the ones that differ, in SEED order. `only` limits it to names."""
    f = C.fields(ws())
    cid = lambda n: f[n]['controlId']
    units = read_units()
    hap.backup('units_records_pre_seed', printable(units))
    for name, contains, reference, active in SEED:
        if only and name not in only:
            continue
        values = [{'id': cid('Unit Name'), 'value': name},
                  {'id': cid('Contains'), 'value': contains},
                  {'id': cid('Reference Unit'), 'value': [units[reference]['rowid']] if reference else []},
                  {'id': cid('Active'), 'value': 1 if active else 0}]        # always explicit on API writes
        live = units.get(name)
        if live and (live['contains'], live['ref'], live['active']) == (number(contains), reference, active):
            continue
        if live:
            hap.run('worksheet', 'record', 'update', ws(), live['rowid'], '-a', APP,
                    '--fields-json', json.dumps(values, ensure_ascii=False))
            rowid = live['rowid']
            print(f'  updated {name}')
        else:
            out = hap.run('worksheet', 'record', 'create', ws(), '-a', APP,
                          '--fields-json', json.dumps(values, ensure_ascii=False))
            rowid = C.row_id(out)
            print(f'  created {name}: {rowid}')
        got = units[name] = read_unit(rowid)
        if (got['name'], got['contains'], got['ref'], got['active']) != (name, number(contains), reference, active):
            sys.exit(f'{name}: read back {got}')
    time.sleep(8)                                   # stored lookups and the formulas on them settle asynchronously
    refresh(read_units())
    step_verify(*only)


def step_verify(*only):
    """Compare the live units with the 19.4 extract (Contains, Reference Unit, Active, Sequence, Absolute
    Quantity) and check every Parent Path against its Reference Unit's."""
    expected, units = reference_table(), read_units()
    names = {u['rowid']: n for n, u in units.items()}
    bad = 0
    for name, e in expected.items():
        if only and name not in only:
            continue
        u = units.get(name)
        if not u:
            print(f'  MISSING  {name}')
            bad += 1
            continue
        checks = {'contains': (u['contains'], number(e['contains'])), 'ref': (u['ref'], e['ref']),
                  'active': (u['active'], e['active']), 'sequence': (u['sequence'], number(e['sequence'])),
                  'factor': (u['factor'], number(e['factor']))}
        diffs = {k: (str(a), str(b)) for k, (a, b) in checks.items() if a != b}
        path = '/'.join(names.get(x, x[:8]) for x in u['path'].strip('/').split('/') if x)
        bad += bool(diffs)
        print(f"  {'OK  ' if not diffs else 'DIFF'}  {name:<11} contains={fmt(u['contains'])} ref={u['ref']} "
              f"active={u['active']} sequence={fmt(u['sequence'])} factor={fmt(u['factor'])} "
              f"path={path}" + (f'  <- {diffs}' if diffs else ''))
    inconsistent = [u['name'] for u in stale(units)]
    extra = sorted(set(units) - set(expected))
    print(f'  {bad} differing from the extract; {len(inconsistent)} with stale lookups {inconsistent}; '
          f'{len(extra)} not in the extract {extra}')
    return bad + len(inconsistent)


def step_unit(*names):
    """Print the live values of units by name, hidden fields included (Absolute Quantity, Sequence, paths)."""
    units = read_units()
    rows = {u['rowid']: n for n, u in units.items()}
    for name in names or sorted(units):
        u = units.get(name)
        if not u:
            print(f'  {name}: no such unit')
            continue
        path = '/'.join(rows.get(x, x[:8]) for x in u['path'].strip('/').split('/') if x)
        print(f"  {name}: contains={fmt(u['contains'])} reference={u['ref']} active={u['active']} "
              f"absolute quantity={fmt(u['factor'])} sequence={fmt(u['sequence'])} path={path} "
              f"related={u['related']} rowid={u['rowid']}")


def step_refresh():
    """Re-save the Reference Unit of every unit whose stored lookups are stale, top of the chain first."""
    left = stale(refresh(read_units()))
    print(f'  {len(left)} still stale {[u["name"] for u in left]}')


def show():
    C.show(ws())


if __name__ == '__main__':
    steps = {'create': step_create, 'fields': step_fields, 'computed': step_computed, 'layout': step_layout,
             'rules': step_rules, 'views': step_views, 'buttons': step_buttons,
             'seed': step_seed, 'verify': step_verify, 'unit': step_unit, 'refresh': step_refresh, 'show': show}
    steps[sys.argv[1] if len(sys.argv) > 1 else 'show'](*sys.argv[2:])
