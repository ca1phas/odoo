"""Generic helpers for the ERP Master worksheet builders, over the hap CLI.

Run builders with the CLI's own interpreter so `hap_cli` imports:

    ~/.hap-venv/bin/python nocoly/build/<worksheet>.py <step>

Nothing here knows about a particular worksheet: ids.json, menu-group and worksheet
upserts, controls on HAP's 12-column form grid, business-rule filters and upsert by
name, table views with the sort and column fixes, Archive/Unarchive-style buttons
with their one-step workflows, workflow publishing, record paging, and the control
printout. Every upsert matches by name, so a step can be re-run.

contacts.py predates this module and still carries its own copies.
"""
import json, subprocess, sys

from hap_cli.core import worksheet_templates as wt
from hap_cli.core.app_creator.fields import field_permission_str

import hap

TAB = 52                                          # a form tab (SECTION) control


# ── ids.json ────────────────────────────────────────────────────────────────

def save_ids(ids):
    with open(hap.IDS_PATH, 'w') as f:
        json.dump(ids, f, ensure_ascii=False, indent=1)


def remember(kind, key, value):
    """Store ids[kind][key] = value in ids.json (other keys untouched)."""
    ids = hap.ids()
    if ids.setdefault(kind, {}).get(key) != value:
        ids[kind][key] = value
        save_ids(ids)


# ── menu groups and worksheets ──────────────────────────────────────────────

def app_info(app):
    return hap.run('app', 'info', '-a', app)['data']


def ensure_section(app, name, after=None):
    """Id of the top-level menu group `name`, created (right after `after`) if missing."""
    sections = app_info(app)['sections']
    found = next((s for s in sections if s['name'] == name), None)
    if not found:
        hap.run('app', 'add-section', app, '--name', name)
        sections = app_info(app)['sections']
        found = next(s for s in sections if s['name'] == name)
        print(f'  menu group {name!r} created: {found["id"]}')
    order = [s['id'] for s in sections if s['id'] != found['id']]
    at = order.index(next(s['id'] for s in sections if s['name'] == after)) + 1 if after else len(order)
    order.insert(at, found['id'])
    if order != [s['id'] for s in sections]:           # a new group is inserted first; put it back in place
        hap.run('app', 'sort-sections', app, *order)
    return found['id']


def ensure_worksheet(app, section_id, name, alias, remark, icon):
    """Id of worksheet `name` in the menu group, created if missing; alias and remark checked."""
    def lookup():
        section = next(s for s in app_info(app)['sections'] if s['id'] == section_id)
        return next((i for i in section['items'] if i['type'] == 0 and i['name'] == name), None)
    item = lookup()
    if not item:
        hap.run('worksheet', 'create', app, name, '--section-id', section_id, '--alias', alias,
                '--remark', remark, '--icon', icon,
                '--icon-url', f'https://www.nocoly.com/file/mdpub/customIcon/{icon}.svg')
        item = lookup()
        print(f'  worksheet {name!r} created: {item["id"]}')
    if item.get('alias') != alias:
        hap.run('worksheet', 'update', item['id'], '--alias', alias)
        item = lookup()
    if item.get('alias') != alias or item.get('remark') != remark:
        sys.exit(f'{name}: alias/remark read back as {item.get("alias")!r} / {item.get("remark")!r}')
    return item['id']


# ── controls ────────────────────────────────────────────────────────────────

def control(kind, name, place, alias='', hint=None, desc=None, hidden=False, readonly=False, **kw):
    """wt.build_control at place = (row, col, size), with alias, description and permissions."""
    row, col, size = place
    c = wt.build_control(kind, name, row=row, col=col, size=size, hint=hint, **kw)
    c['alias'] = alias
    if desc is not None:
        c['desc'] = desc
    if hidden or readonly:
        c['fieldPermission'] = field_permission_str(hidden=hidden, readonly=readonly)
    return c


def static_default(value):
    """advancedSetting.defsource for a static default value."""
    return json.dumps([{'cid': '', 'rcid': '', 'staticValue': str(value)}])


def fields(ws):
    """Live controls by name, tabs left out."""
    return hap.by_name(c for c in hap.controls(ws) if c['type'] != TAB)


def add_fields(ws, ctrls):
    """Append controls, then re-save the whole set so they get server ids.

    add-fields stores a control under its client-side id, and a formula or concatenation saved that way
    computes nothing until a full save re-mints the id; lookups built on the client id would dangle."""
    hap.run('worksheet', 'add-fields', ws, '--controls', json.dumps(ctrls, ensure_ascii=False))
    hap.run('worksheet', 'update-fields', ws, '--controls', json.dumps(hap.controls(ws), ensure_ascii=False))


def append_controls(ws, ctrls):
    """Append controls with no client-side id, so the server mints real ones, and nothing else is re-sent.

    This is how hap-cli's own app builder adds a one-way Relation: AddWorksheetControls without a
    controlId. A Relation to another worksheet stays one-way (advancedSetting.bidirectional '0'), and the
    target worksheet is not touched."""
    ctrls = [{k: v for k, v in c.items() if k != 'controlId'} for c in ctrls]
    hap.run('worksheet', 'add-fields', ws, '--controls', json.dumps(ctrls, ensure_ascii=False))


def show(ws):
    """Print the live control list in form order."""
    ctrls = hap.controls(ws)
    tabs = {c['controlId']: c['controlName'] for c in ctrls if c['type'] == TAB}
    for c in sorted(ctrls, key=lambda c: (c.get('row', 0), c.get('col', 0))):
        extra = []
        if c.get('attribute') == 1: extra.append('title')
        if c.get('required'): extra.append('required')
        if c.get('fieldPermission') not in (None, '', '111'): extra.append(f"perm={c['fieldPermission']}")
        if c.get('sectionId'): extra.append(f"tab={tabs.get(c['sectionId'], c['sectionId'])}")
        if c['type'] in (6, 8, 30, 31, 53): extra.append(f"dot={c.get('dot')}")
        if c.get('dataSource'): extra.append(f"ds={c['dataSource']}")
        if c.get('sourceControlId'): extra.append(f"src={c['sourceControlId']}")
        if c.get('options'): extra.append('opts=' + '/'.join(o['value'] for o in c['options']))
        if c.get('hint'): extra.append(f"hint={c['hint']!r}")
        print(f"r{c.get('row', 0):<2} c{c.get('col', 0)} s{c.get('size', '?'):<2} {c['type']:>2} "
              f"{c['controlName']:<28} {c['controlId']}  {c.get('alias') or '':<20} {' '.join(extra)}")
    print(f'{len(ctrls)} controls')


# ── business rules ──────────────────────────────────────────────────────────

SHOW, HIDE, READONLY, REQUIRE, ERROR = 1, 2, 4, 5, 6      # rule item types
CONTAINS, EQ, NE, EMPTY, NOT_EMPTY = 1, 2, 6, 7, 8         # filter operators
INTERACTION, VALIDATION = 0, 1                            # rule types
OPTION_TYPES = (9, 10, 11)


def cond(c, op, value=None):
    """One filter condition on control c. Options take their key; numbers and switches a value."""
    values = [] if value is None else [str(value)]
    return {'controlId': c['controlId'], 'dataType': c['type'], 'spliceType': 1, 'filterType': op,
            'value': '' if value is None or c['type'] in OPTION_TYPES else str(value),
            'values': values, 'dynamicSource': [], 'isGroup': False}


def any_of(*groups):
    """OR of AND-groups: any_of([a, b], [c]) == (a and b) or c."""
    return [{'controlId': '', 'dataType': 1, 'spliceType': 2, 'filterType': 0, 'value': '', 'values': [],
             'dynamicSource': [], 'isGroup': True, 'groupFilters': list(g)} for g in groups]


def item(kind, *ctrls, message=''):
    return {'type': kind, 'isAll': False, 'message': message,
            'controls': [{'isCustom': False, 'controlId': c['controlId'], 'childControlIds': [],
                          'permission': [], 'type': '', 'value': ''} for c in ctrls]}


def upsert_rules(ws, rules, backup_name):
    """rules: [(name, type, filters, items, options)], options {'check_type', 'hint_type'}. Matched by name."""
    live = {r['name']: r for r in hap.listing('worksheet', 'rules', ws)}
    hap.backup(backup_name, list(live.values()))
    for name, kind, filters, items, opts in rules:
        args = ['worksheet', 'save-rule', ws, '--name', name, '--type', str(kind),
                '--filters', json.dumps(filters), '--rule-items', json.dumps(items, ensure_ascii=False)]
        if kind == VALIDATION:
            args += ['--check-type', str(opts.get('check_type', 1)), '--hint-type', str(opts.get('hint_type', 0))]
        if name in live:
            args += ['--rule-id', live[name]['ruleId']]
        hap.run(*args)
    names = {c['controlId']: c['controlName'] for c in hap.controls(ws)}
    for r in hap.listing('worksheet', 'rules', ws):
        acts = [(i['type'], [names.get(c['controlId'], c['controlId']) for c in i['controls']], i.get('message', ''))
                for i in r['ruleItems']]
        print(f"  type={r['type']} check={r.get('checkType')} hint={r.get('hintType')} disabled={r['disabled']}  "
              f"{r['name']:<48} {acts}")


# ── views ───────────────────────────────────────────────────────────────────

def sort_spec(ctrls):
    """sortCid/sortType/moreSort for an ascending sort on the controls, in order."""
    return {'sortCid': ctrls[0]['controlId'], 'sortType': 2,
            'moreSort': [{'controlId': c['controlId'], 'dataType': c['type'], 'spliceType': 0, 'filterType': 0,
                          'dateRange': 0, 'dateRangeType': 0, 'value': '', 'values': [], 'minValue': '',
                          'maxValue': '', 'isAsc': True, 'dynamicSource': [], 'advancedSetting': {},
                          'isGroup': False, 'groupFilters': [], 'emptyRule': 0} for c in ctrls]}


def sort_by(pairs):
    """sortCid/sortType/moreSort for [(control, ascending), ...]: sort_spec with a direction per control.
    sortType follows the first control: 2 ascending, 1 descending."""
    spec = sort_spec([c for c, _ in pairs])
    for s, (_, asc) in zip(spec['moreSort'], pairs):
        s['isAsc'] = asc
    spec['sortType'] = 2 if pairs[0][1] else 1
    return spec


def sort_views(ws, app, names):
    """Put the views in this order (the first opens by default); views not named keep their place after.

    `hap worksheet view sort` sends no appId, and SortWorksheetViews then answers false and changes nothing;
    the same call with the appId works, so it goes through the CLI's session."""
    from hap_cli.core.session import Session
    live = hap.listing('worksheet', 'view', 'list', ws, '-a', app)
    by_name = {v['name']: v['viewId'] for v in live}
    order = [by_name[n] for n in names] + [v['viewId'] for v in live if v['name'] not in names]
    if order != [v['viewId'] for v in live]:
        ok = Session.load(None).api_call('Worksheet', 'SortWorksheetViews',
                                         {'appId': app, 'worksheetId': ws, 'viewIds': order})
        if ok is not True:
            sys.exit(f'SortWorksheetViews answered {ok!r}')
    return [v['name'] for v in hap.listing('worksheet', 'view', 'list', ws, '-a', app)]


def switch_filter(c, op):
    """--view-spec filter group: checkbox c equal (eq) or not equal (ne) to checked."""
    return {'type': 'group', 'logic': 'AND', 'children': [
        {'type': 'condition', 'field': c['controlId'], 'operator': op, 'value': ['1']}]}


def upsert_views(ws, app, views, backup_name, default_view=None):
    """views: {name: (spec, sort, columns)} with sort from sort_spec() and table columns as control ids.

    --view-spec ignores sort keys and sets only displayControls on a table (which then shows
    every field), so sort and columns are written with --view-json afterwards.
    The worksheet's default view ('All') is renamed to `default_view` on first run.
    """
    live = hap.listing('worksheet', 'view', 'list', ws, '-a', app)
    hap.backup(backup_name, live)
    live = {v['name']: v['viewId'] for v in live}
    if default_view and default_view not in live:
        for stock in ('All', '全部'):
            if stock in live:
                live[default_view] = live.pop(stock)
                break
    for name, (spec, sort, columns) in views.items():
        spec = {'name': name, **spec}
        if name in live:
            hap.run('worksheet', 'view', 'update', ws, live[name], '-a', app, '--view-spec', json.dumps(spec))
        else:
            hap.run('worksheet', 'view', 'create', ws, name, '-a', app, '--view-spec', json.dumps(spec))
    live = {v['name']: v for v in hap.listing('worksheet', 'view', 'list', ws, '-a', app)}
    for name, (spec, sort, columns) in views.items():
        vid = live[name]['viewId']
        hap.run('worksheet', 'view', 'update', ws, vid, '-a', app,
                '--view-json', json.dumps(sort), '--edit-attrs', 'sortCid,sortType,moreSort')
        if columns is not None:
            hap.run('worksheet', 'view', 'update', ws, vid, '-a', app, '--view-json', json.dumps({
                'showControls': columns,
                'advancedSetting': {'customdisplay': '1', 'customShowControls': json.dumps(columns)}}),
                '--edit-attrs', 'showControls,advancedSetting', '--edit-ad-keys', 'customdisplay,customShowControls')
        if view_info(ws, app, vid).get('name') != name:
            hap.run('worksheet', 'view', 'update', ws, vid, '-a', app, '--name', name)
    return {name: live[name]['viewId'] for name in views}


def view_info(ws, app, view_id):
    out = hap.run('worksheet', 'view', 'info', ws, view_id, '-a', app)
    return out.get('data', out) if isinstance(out, dict) else {}


def print_views(ws, app):
    names = {c['controlId']: c['controlName'] for c in hap.controls(ws)}
    for v in hap.listing('worksheet', 'view', 'list', ws, '-a', app):
        info = view_info(ws, app, v['viewId'])
        flt = [(names.get(f['controlId'], f['controlId']), f['filterType'], f.get('values')) for f in info.get('filters') or []]
        print(f"  {info['name']:<20} {v['viewId']} type={info['viewType']} "
              f"sort={[(names.get(s['controlId']), 'asc' if s['isAsc'] else 'desc') for s in info.get('moreSort') or []]} "
              f"(sortCid={names.get(info.get('sortCid'))}/{info.get('sortType')}) filters={flt} "
              f"columns={[names.get(x, x) for x in info.get('showControls') or []]}")


# ── buttons and workflows ───────────────────────────────────────────────────

def publish(pid):
    res = hap.run('workflow', 'publish', pid)
    return {k: res.get(k) for k in ('isPublish', 'processWarnings', 'errorNodeIds')}


def button_workflow(process_id, fields, node_name):
    """Trigger by button -> update the triggering record -> publish. Left alone if it has steps."""
    proc = hap.run('workflow', 'node', 'list', process_id)
    trigger = proc['startEventId']
    first = proc['flowNodeMap'][trigger].get('nextId')
    if first not in (None, '', '99'):                 # '99' is the end marker; virtual nodes hang off-chain
        print(f'  {node_name}: workflow {process_id} already has steps; left as is')
        return
    spec = [{'nodeAlias': 'upd', 'nodeType': 'update_record', 'name': node_name,
             'config': {'target': {'node': {'nodeAlias': 'trigger'}}, 'fields': fields}}]
    hap.run('workflow', 'node', 'batch-add', process_id, '--nodes', json.dumps(spec),
            '--trigger-node-id', trigger, '--trigger-alias', 'trigger')
    print(f'  {node_name}:', publish(process_id))


def upsert_buttons(ws, app, buttons, ids_prefix, backup_name):
    """buttons: [(action_spec, update_fields, node_name)]. A button that exists by name is not re-created
    (create-custom-action --action-spec ignores --btn-id and would add a duplicate).
    ids.json keys are '<ids_prefix><button name>' in both 'buttons' and 'workflows'."""
    live = hap.listing('worksheet', 'custom-actions', ws)
    hap.backup(backup_name, live)
    live = {b['name']: b for b in live}
    for spec, update_fields, node_name in buttons:
        key = ids_prefix + spec['name']
        if spec['name'] in live:
            print(f"  {spec['name']}: exists ({live[spec['name']]['btnId']}); not re-created")
            pid = hap.ids().get('workflows', {}).get(key)
        else:
            out = hap.run('worksheet', 'create-custom-action', ws, '-a', app, '--action-spec', json.dumps(spec))
            data = out.get('data', out) if isinstance(out, dict) else {}
            pid = data.get('processId')
            if not pid:
                sys.exit(f"{spec['name']}: no processId in create-custom-action output: {out}")
            remember('workflows', key, pid)
        if pid:
            button_workflow(pid, update_fields, node_name)
    for b in hap.listing('worksheet', 'custom-actions', ws):
        remember('buttons', ids_prefix + b['name'], b['btnId'])
        print(f"  {b['name']:<10} btnId={b['btnId']} clickType={b.get('clickType')} workflowType={b.get('workflowType')} "
              f"isBatch={b.get('isBatch')} filters={[(f['filterType'], f.get('values')) for f in b.get('filters') or []]} "
              f"confirm={b.get('confirmMsg', '')!r} sure={b.get('sureName', '')!r}")


def structure(pid):
    return subprocess.run(['hap', 'workflow', 'structure', pid], capture_output=True, text=True).stdout


# ── records ─────────────────────────────────────────────────────────────────

def records(ws, app, page_size=200):
    """Every record, keyed by field id (plus rowid), archived or not. Hidden fields come back empty:
    read those with `record get`. Pages on row count, as `total` lags just after a write."""
    out, page = [], 1
    while True:
        res = hap.run('worksheet', 'record', 'list', ws, '-a', app, '-n', str(page_size), '-p', str(page),
                      '--use-field-id-as-key')
        data = res.get('data', res) if isinstance(res, dict) else res
        rows = (data.get('rows') if isinstance(data, dict) else data) or []
        out += rows
        if len(rows) < page_size:
            return out
        page += 1


def row_id(created):
    """rowid from a record create response; refuses anything but resultCode 1."""
    data = created.get('data', created) if isinstance(created, dict) else {}
    if isinstance(created, dict) and created.get('resultCode') not in (None, 1):
        raise RuntimeError(f'record not saved: {created}')
    if isinstance(data, dict):
        if data.get('resultCode') not in (None, 1):
            raise RuntimeError(f'record not saved: {created}')
        inner = data.get('data') if isinstance(data.get('data'), dict) else data
        return inner.get('rowid') or inner.get('rowId')
    return None
