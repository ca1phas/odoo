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


def save_controls(ws, ctrls, version=None):
    """A full SaveWorksheetControls save of worksheet `ws` — exactly what `hap worksheet update-fields --controls`
    does — made through the CLI's own session instead of the command line.

    Every Relation control carries a `relationControls` snapshot of its target worksheet's controls, so a worksheet
    holding a few Relations to a large worksheet is past the kernel's 128 KiB limit on a single argument, and the
    command dies with `OSError: [Errno 7] Argument list too long` (Invoices once 07 mounted its subtable; Contacts,
    Products, Product Categories and Journals once bundle 2 gave them Relations to Chart of Accounts). Same call,
    same optimistic-lock retry; only the transport differs. Raises on a response that is not a success.

    `version` pins HAP's optimistic lock: pass the `version` that `controls_with_version` read together with the
    controls being sent, and a control save anyone made in between refuses this one (code 10, "数据过时") instead of
    being overwritten. Without it hap-cli refetches the counter on a conflict and saves anyway — fine for a worksheet
    nobody else edits, not for a surgical change to one another administrator is working on (Products, 17 Sep)."""
    from hap_cli.core import worksheet as ws_mod
    from hap_cli.core.session import Session
    resp = ws_mod.save_controls(Session.load(None), ws, relation_defaults_by_id(ctrls), version=version)
    if isinstance(resp, dict) and resp.get('code') not in (None, 1):
        raise RuntimeError(f'SaveWorksheetControls on {ws} answered {json.dumps(resp, ensure_ascii=False)[:400]}')
    return resp


def controls_with_version(ws):
    """The worksheet's controls and their optimistic-lock `version`, from one GetWorksheetControls call — the pair a
    read-modify-write hands to `save_controls(ws, ctrls, version=…)`."""
    from hap_cli.core.session import Session
    resp = Session.load(None).api_call('Worksheet', 'GetWorksheetControls',
                                       {'worksheetId': ws, 'getRelationSearch': True, 'resultType': 3})
    data = resp.get('data') if isinstance(resp, dict) else None
    if not isinstance(data, dict) or not isinstance(data.get('controls'), list) or not isinstance(data.get('version'), int):
        raise RuntimeError(f'GetWorksheetControls on {ws} answered {json.dumps(resp, ensure_ascii=False)[:300]}')
    return data['controls'], data['version']


def relation_defaults_by_id(ctrls):
    """The controls with every static Relation default put back in the form a save accepts: the record ids.

    The server stores a static Relation default sent as `["<rowid>"]` as the **whole record** — its JSON, `utime`
    included — and hands that back from GetWorksheetControls. Sent back in that long form, as any read-modify-write
    save does, the default is **cleared**: `staticValue` reads back `""`, with no error (proved on Contacts' two
    account defaults, 17 Sep 2026). hap-cli's own normaliser only rewrites dynamic defaults whose value starts with
    "{". Controls that need it are copied, so the caller's dicts stay as read."""
    out = []
    for c in ctrls:
        settings = c.get('advancedSetting')
        raw = settings.get('defsource') if isinstance(settings, dict) else None
        if c.get('type') != 29 or not isinstance(raw, str) or '{' not in raw:
            out.append(c)
            continue
        try:
            entries = json.loads(raw)
        except ValueError:
            out.append(c)
            continue
        changed = False
        for entry in entries if isinstance(entries, list) else []:
            static = entry.get('staticValue') if isinstance(entry, dict) else None
            if not (isinstance(static, str) and static.startswith('[')):
                continue
            try:
                items = json.loads(static)
            except ValueError:
                continue
            ids = []
            for item in items if isinstance(items, list) else []:
                if isinstance(item, str) and item.startswith('{'):
                    try:
                        item = json.loads(item).get('rowid') or item
                        changed = True
                    except (ValueError, AttributeError):
                        pass
                ids.append(item)
            entry['staticValue'] = json.dumps(ids)
        out.append({**c, 'advancedSetting': {**settings, 'defsource': json.dumps(entries, ensure_ascii=False)}}
                   if changed else c)
    return out


def add_fields(ws, ctrls):
    """Append controls, then re-save the whole set so they get server ids.

    add-fields stores a control under its client-side id, and a formula or concatenation saved that way
    computes nothing until a full save re-mints the id; lookups built on the client id would dangle. The re-save
    goes through save_controls: the whole control list no longer fits on a command line."""
    hap.run('worksheet', 'add-fields', ws, '--controls', json.dumps(ctrls, ensure_ascii=False))
    save_controls(ws, hap.controls(ws))


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


# ── a narrow, version-pinned control save, for any worksheet ────────────────
#
# orders.py has carried these for Orders since 21 Sep 2026 (`control_state`, `drift`, `pinned_write`); these are the
# worksheet-agnostic copies the Incoterm and Tags wiring (22 Sep 2026) uses on Invoices and Contacts. The pattern is
# products.py `step_perms`: read the controls with their version, change only the keys named, save pinned to that
# version, and prove by signature diff that only the named controls moved.

SIGNATURE_KEYS = ('controlName', 'type', 'alias', 'row', 'col', 'size', 'sectionId', 'required', 'attribute', 'unique',
                  'fieldPermission', 'dataSource', 'sourceControlId', 'sourceControlType', 'showControls', 'desc',
                  'hint', 'enumDefault', 'enumDefault2', 'strDefault', 'dot', 'unit', 'options', 'default', 'viewId',
                  'coverCid', 'noticeItem', 'half', 'defaultMen')
# advancedSetting keys whose value is JSON in a string: the server re-serialises them on read, so they are compared
# parsed (BUILDING.md; accounts.control_state).
JSON_SETTINGS = ('filters', 'filterregex', 'controlssorts', 'customShowControls', 'defsource', 'defaultfunc',
                 'uniquecontrols', 'rowsummary', 'cardstyle')


def defsource_state(value):
    """A `defsource` in comparable form: a static Relation default reduced to its record ids (the server stores the
    whole record, `utime` included), a member default to its sentinel — orders.defsource_state."""
    from hap_cli.core.worksheet import _DEFSOURCE_SENTINELS
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
        elif isinstance(static, str) and static.startswith('{'):
            try:
                static = next((v for v in json.loads(static).values() if v in _DEFSOURCE_SENTINELS), static)
            except (TypeError, ValueError, AttributeError):
                pass
        out.append((e.get('cid') or '', e.get('rcid') or '', static, e.get('time') or ''))
    return out


def parsed_setting(key, value):
    if key == 'defsource':
        return defsource_state(value)
    if key in JSON_SETTINGS and isinstance(value, str) and value:
        try:
            return json.loads(value)
        except ValueError:
            pass
    return value


def control_state(c, ignore_related=()):
    """A control's attributes, JSON-valued settings parsed and a Relation's `relationControls` snapshot reduced to
    the target controls' identity (the server reshuffles it). `ignore_related` leaves those control ids out of the
    snapshot: a Relation to its own worksheet (Contacts' Company) lists a control appended there a moment ago, which
    is the server describing the target, not a change to the Relation."""
    out = {k: c.get(k) for k in SIGNATURE_KEYS}
    out['advancedSetting'] = {k: parsed_setting(k, v) for k, v in (c.get('advancedSetting') or {}).items()}
    out['relationControls'] = sorted((r.get('controlId'), r.get('controlName'), r.get('type'), r.get('required'))
                                     for r in (c.get('relationControls') or [])
                                     if r.get('controlId') not in ignore_related)
    return out


def control_signature(ctrls, ignore_related=()):
    """{controlId: the control's state as a string} — what a before/after comparison of a save diffs."""
    return {c['controlId']: json.dumps(control_state(c, ignore_related), sort_keys=True, ensure_ascii=False,
                                       default=str)
            for c in ctrls}


def changed_ids(before, after):
    return sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))


def value_of(c, key):
    """A control's value for a plain key or an `advancedSetting.<key>`, JSON-valued settings parsed."""
    if key.startswith('advancedSetting.'):
        key = key.split('.', 1)[1]
        return parsed_setting(key, (c.get('advancedSetting') or {}).get(key))
    return c.get(key)


def drift(c, spec):
    """{key: (got, want)} for every key of `spec` — plain or `advancedSetting.<key>` — the control does not carry."""
    out = {}
    for k, v in spec.items():
        want = parsed_setting(k.split('.', 1)[1], v) if k.startswith('advancedSetting.') else v
        if value_of(c, k) != want:
            out[k] = (value_of(c, k), want)
    return out


def pinned_write(ws, spec, backup_name, step):
    """Write `spec` — {controlId: {key: value}} — in **one** SaveWorksheetControls pinned to the version it read, then
    prove by signature diff that only the controls `spec` names changed, and read them back. Returns True when it
    saved and False when there was nothing to write. Every other control and key goes back exactly as read."""
    ctrls, version = controls_with_version(ws)
    by_id = {c['controlId']: c for c in ctrls}
    missing = [cid for cid in spec if cid not in by_id]
    if missing:
        sys.exit(f'{step}: {missing} are not on {ws} — stopping')
    stale = {cid: drift(by_id[cid], spec[cid]) for cid in spec if drift(by_id[cid], spec[cid])}
    if not stale:
        print(f"  {step}: {sorted(by_id[cid]['controlName'] for cid in spec)} already as specified; nothing saved")
        return False
    for cid, diff in stale.items():
        for k, (got, want) in diff.items():
            print(f"  {by_id[cid]['controlName']}.{k}: {got!r} -> {want!r}")
    hap.backup(backup_name, ctrls)
    before = control_signature(ctrls)
    for cid, diff in stale.items():
        c = by_id[cid]
        for key in diff:
            value = spec[cid][key]
            if key.startswith('advancedSetting.'):
                c['advancedSetting'] = {**(c.get('advancedSetting') or {}), key.split('.', 1)[1]: value}
            else:
                c[key] = value
    save_controls(ws, ctrls, version=version)
    live = hap.controls(ws)
    after = control_signature(live)
    changed = changed_ids(before, after)
    names = {c['controlId']: c['controlName'] for c in live}
    if changed != sorted(stale):
        sys.exit(f'{step}: the save changed {[names.get(k, k) for k in changed]}, wanted only '
                 f'{[names.get(k, k) for k in sorted(stale)]}\n' +
                 '\n'.join(f'  {names.get(k, k)}\n    was {before.get(k)}\n    now {after.get(k)}' for k in changed))
    by_id = {c['controlId']: c for c in live}
    left = {names[cid]: drift(by_id[cid], spec[cid]) for cid in spec if drift(by_id[cid], spec[cid])}
    if left:
        sys.exit(f'{step}: read back with differences {json.dumps(left, ensure_ascii=False, default=str)}')
    print(f'  {step}: {sorted(names[cid] for cid in stale)} written — {len(before)} controls compared, no other change')
    return True


def append_checked(ws, ctrls, backup_name, step, untouched=()):
    """`append_controls`, proved: every control already on `ws` — and on each worksheet in `untouched` — reads back
    exactly as before, and the only new ones are those appended, by name. Returns the live controls by name."""
    hap.backup(backup_name, hap.controls(ws))
    others = {w: control_signature(hap.controls(w)) for w in untouched}
    before = control_signature(hap.controls(ws))
    append_controls(ws, ctrls)
    live = hap.controls(ws)
    new_ids = {c['controlId'] for c in live if c['controlId'] not in before}
    after = control_signature(live, ignore_related=new_ids)
    moved = [k for k in before if before[k] != after.get(k)]
    added = sorted(c['controlName'] for c in live if c['controlId'] in new_ids)
    if moved or added != sorted(c['controlName'] for c in ctrls):
        sys.exit(f'{step}: the append moved {moved} and added {added}, wanted only {[c["controlName"] for c in ctrls]}')
    for w, sig in others.items():
        if control_signature(hap.controls(w)) != sig:
            sys.exit(f'{step}: {w} changed under the append — a one-way Relation must leave its target alone')
    print(f"  {step}: appended {added}; {len(before)} existing controls unchanged"
          + (f", {', '.join(untouched)} untouched" if untouched else ''))
    return hap.by_name(c for c in live if c['type'] != TAB)


def active_picker(active_control_id):
    """A Relation's picker filter **Active is ticked** on the target's checkbox, as `advancedSetting.filters` — the
    shape Invoices' Payment Terms stores. Browser-only: the API's picker query ignores it (BUILDING.md)."""
    return json.dumps([{'controlId': active_control_id, 'dataType': 36, 'spliceType': 1, 'filterType': EQ,
                        'dateRange': 0, 'dateRangeType': 0, 'value': '1', 'values': ['1'], 'minValue': None,
                        'maxValue': None, 'isAsc': False, 'dynamicSource': [], 'advancedSetting': None,
                        'isGroup': False, 'groupFilters': None, 'emptyRule': 0}], separators=(',', ':'))


def picker_state(value):
    """A picker filter reduced to (control, dataType, filterType, values) — what it means, not how it is spelt."""
    try:
        items = json.loads(value) if isinstance(value, str) else (value or [])
    except ValueError:
        return value
    return sorted((i.get('controlId'), i.get('dataType'), i.get('filterType'), tuple(sorted(i.get('values') or [])))
                  for i in items or [])


# ── a line's tax rate the open form can compute ─────────────────────────────
#
# Tax rate (Order Lines, Invoice Lines) is a 汇总 **filtered** to percentage taxes, and pd-openweb's form computes a
# 汇总 while the form is open **only when it has no filter** (DataFormat.js: `if (advancedSetting.filters) return`).
# So on a new line Tax rate stays 0 until the save, and every Formula built on it shows no tax (owner, 23 Sep 2026).
# Two helpers per worksheet fix that without giving up the percentage rule:
#
#   * LIVE_ALL    — the same 汇总 **unfiltered**: the form sums the Amount of every tax picked, the moment it is picked
#                   (the picker's rows carry Amount). On the server it is the plain sum of all the line's taxes;
#   * LIVE_OTHERS — a **count** of the line's taxes that are *not* Percentage (the Tax rate filter with filterType
#                   52, "is not"). It has a filter, so the form never computes it: it is the saved line's own count.
#
# and the rate every Formula reads becomes LIVE_RATE_TEMPLATE, with no IF (a number formula has none):
#
#     R + U × (1 − min(1, |R| × 10000)) × (1 − min(1, N))
#
#   * a saved line: R is exact, so the result is R whenever R ≠ 0; when R = 0 it is U only if N = 0, and then every
#     tax is a percentage whose rates sum to 0, so U = 0 too. **The saved value is always Tax rate's own.**
#   * a line open in the form: R and N are what was saved — 0 on a new line — so the result is U, the live sum.
#   * a line saved **before** the helpers existed stores U and N blank, and a blank reads 0 (`nullzero "1"`): the
#     result is R. That is what keeps every figure on the seeded demo records exactly as it was.
# Limit: on an **already saved** line with a percentage tax, changing its taxes in the form shows the old rate until
# the save (R ≠ 0 wins). Rates carry 4 decimals, so |R| × 10000 ≥ 1 for any non-zero R.
# Why not a Lookup (type 30) of Amount: over a multi-record relation the server stores **nothing** on any read path,
# and the form shows only the **first** record's value (pd-openweb getOtherWorksheetFieldValue) — measured 23 Sep 2026.
LIVE_ALL, LIVE_OTHERS = 'Tax rate (all taxes)', 'Non-percentage taxes'
LIVE = (LIVE_ALL, LIVE_OTHERS)
LIVE_ALIAS = {LIVE_ALL: 'tax_rate_all', LIVE_OTHERS: 'tax_count_other'}
LIVE_DESC = {LIVE_ALL: "The combined rate of all this line's taxes, worked out as soon as a tax is picked.",
             LIVE_OTHERS: "How many of this line's taxes are not a percentage."}
LIVE_DOT = {LIVE_ALL: 4, LIVE_OTHERS: 0}
LIVE_PERMISSION = '011'                             # hidden: working figures, never typed and never a column
LIVE_RATE_TEMPLATE = '$R$+$U$*(1-cMIN(1,cABS($R$)*10000))*(1-cMIN(1,$N$))'
NE_SINGLE = 52                                      # a 汇总 filter's "is not" on a single select (EQ is 51)


def live_rate(rate_id, all_id, others_id):
    """LIVE_RATE_TEMPLATE over the three control ids."""
    return (LIVE_RATE_TEMPLATE.replace('$R$', f'${rate_id}$').replace('$U$', f'${all_id}$')
            .replace('$N$', f'${others_id}$'))


def other_taxes_filter(rate_filters):
    """Tax rate's own stored filter ("Tax Computation is Percentage", filterType 51) turned into "is not" (52), so
    the count and the rate cannot drift apart."""
    items = json.loads(rate_filters) if isinstance(rate_filters, str) else rate_filters
    if len(items) != 1 or items[0].get('filterType') != 51:
        sys.exit(f'Tax rate filter is {rate_filters!r} — expected one "is" condition (filterType 51) to invert')
    return json.dumps([{**items[0], 'filterType': NE_SINGLE}], ensure_ascii=False, separators=(',', ':'))


def live_rate_spec(relation_id, amount_col, name_col, rate_filters):
    """{name: {key: value}} — what the two helpers must read back as. The filter is compared by `live_rate_problems`
    for what it means (`picker_state`), not by spelling."""
    base = {'type': 37, 'dataSource': f'${relation_id}$', 'fieldPermission': LIVE_PERMISSION, 'required': False}
    return {LIVE_ALL: {**base, 'sourceControlId': amount_col, 'enumDefault': 5, 'dot': LIVE_DOT[LIVE_ALL],
                       'alias': LIVE_ALIAS[LIVE_ALL], 'desc': LIVE_DESC[LIVE_ALL]},
            LIVE_OTHERS: {**base, 'sourceControlId': name_col, 'enumDefault': 6, 'dot': LIVE_DOT[LIVE_OTHERS],
                          'alias': LIVE_ALIAS[LIVE_OTHERS], 'desc': LIVE_DESC[LIVE_OTHERS]}}


def live_rate_problems(f, relation_id, amount_col, name_col, rate_filters):
    """Every way the two live helpers on a worksheet (controls by name) differ from the spec — [] when right."""
    out = []
    spec = live_rate_spec(relation_id, amount_col, name_col, rate_filters)
    for name, want in spec.items():
        c = f.get(name)
        if c is None:
            out.append(f'{name} is missing')
            continue
        diff = drift(c, want)
        if diff:
            out.append(f'{name}: {json.dumps(diff, ensure_ascii=False, default=str)}')
    filters = {LIVE_ALL: [], LIVE_OTHERS: picker_state(other_taxes_filter(rate_filters))}
    for name, want in filters.items():
        if name in f and picker_state((f[name].get('advancedSetting') or {}).get('filters') or '[]') != want:
            out.append(f"{name} filter is {(f[name].get('advancedSetting') or {}).get('filters')!r}, want {want}")
    return out


def ensure_live_rate(ws, relation_id, amount_col, name_col, rate_filters, place, backup, step, untouched=()):
    """Append whichever of the two helpers `ws` lacks — `append_checked`, so no existing control moves — then repair
    any key the append did not store in one pinned write limited to them. `place` is the intended (row, col, size)
    per name; `add-fields` parks a new control at row 9999 and placing it is the owner's. Returns controls by name."""
    f = hap.by_name(c for c in hap.controls(ws) if c['type'] != TAB)
    spec = live_rate_spec(relation_id, amount_col, name_col, rate_filters)
    build = {
        LIVE_ALL: control('SUBTOTAL', LIVE_ALL, place[LIVE_ALL], alias=LIVE_ALIAS[LIVE_ALL], hint='',
                          desc=LIVE_DESC[LIVE_ALL], hidden=True, data_source=relation_id,
                          source_control_id=amount_col, extra={'enumDefault': 5, 'dot': LIVE_DOT[LIVE_ALL]},
                          advanced_setting={'roundtype': '2', 'sorttype': 'zh'}),
        LIVE_OTHERS: control('SUBTOTAL', LIVE_OTHERS, place[LIVE_OTHERS], alias=LIVE_ALIAS[LIVE_OTHERS], hint='',
                             desc=LIVE_DESC[LIVE_OTHERS], hidden=True, data_source=relation_id,
                             source_control_id=name_col, extra={'enumDefault': 6, 'dot': LIVE_DOT[LIVE_OTHERS]},
                             advanced_setting={'roundtype': '2', 'sorttype': 'zh',
                                               'filters': other_taxes_filter(rate_filters)}),
    }
    missing = [n for n in LIVE if n not in f]
    if missing:
        f = append_checked(ws, [build[n] for n in missing], backup, step, untouched)
    else:
        print(f'  {step}: {list(LIVE)} are already there; nothing appended')
    repair = {f[n]['controlId']: {k: v for k, v in want.items() if k in drift(f[n], want)}
              for n, want in spec.items() if drift(f[n], want)}
    if repair:
        pinned_write(ws, repair, backup + '_repair', step + ' repair')
        f = hap.by_name(c for c in hap.controls(ws) if c['type'] != TAB)
    left = live_rate_problems(f, relation_id, amount_col, name_col, rate_filters)
    if left:
        sys.exit(f'{step}: ' + '; '.join(left))
    for n in LIVE:
        print(f"  OK  {n} {f[n]['controlId']} t{f[n]['type']} perm {f[n]['fieldPermission']} "
              f"row {f[n].get('row')} (placing it is the owner's)")
    return f
