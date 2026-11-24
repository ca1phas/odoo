"""Create or complete one worksheet from a spec, then read it back (wave 0, step 4).

A spec is a dict: name, alias (Odoo model with "_"), module, group ("Settings" or "Contacts/Configuration"), icon,
desc, title (field name), visibility, fields: [F(...)], reverse: {relation field alias: (reverse alias, reverse name, module)}.

Field aliases and descriptions are passed through FieldSpec's `extra` (raw control keys), then checked on readback
and fixed with an app-editor field.update when the server dropped them.
"""
import json, os, tempfile
from lib import APP, hap, unwrap, app_info, sections_flat, record

HERE = os.path.dirname(os.path.abspath(__file__))


def F(name, type_, alias, module=None, desc='', **kw):
    """One field. kw: required, options, dataSource ('@<sheet alias>'), multi, config, dot, default, extra."""
    f = {'type': type_, 'name': name, '_alias': alias, '_module': module, '_desc': desc}
    for k in ('required', 'options', 'multi', 'config', 'dataSource', 'advanced_setting', 'defaultValue'):
        if k in kw:
            f[k] = kw[k]
    extra = dict(kw.get('extra', {}))
    extra['alias'] = alias
    if desc:
        extra['desc'] = desc
    if 'dot' in kw:
        extra['dot'] = kw['dot']
    f['extra'] = extra
    return f


def sheets_by_alias():
    info = app_info()
    out = {}
    for s in sections_flat(info):
        for i in s['items']:
            if i.get('type') == 0:
                out[i.get('alias') or i['id']] = {'id': i['id'], 'name': i['name'], 'section': s['id']}
    return out


def section_ids(path):
    secs = sections_flat()
    top, _, child = path.partition('/')
    t = next(s for s in secs if s['parent'] is None and s['name'] == top)
    if not child:
        return t['id'], None
    c = next(s for s in secs if s['parent'] == t['id'] and s['name'] == child)
    return c['id'], t['id']


def raw_fields(ws, parent=None):
    args = ['worksheet', 'fields', ws, '-a', APP, '--raw'] + (['--parent', parent] if parent else [])
    return hap(*args)


def apply_spec(ops):
    spec = {'app': APP, 'ops': ops}
    fd, p = tempfile.mkstemp(suffix='.json', dir=os.path.join(HERE, 'backups'))
    os.close(fd)
    json.dump(spec, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
    return hap('app-editor', 'apply', p)


def ensure_sheet(spec, step='step 4'):
    """Create the sheet if its alias is not in the app, fix aliases/descriptions, record everything. Returns the sheet id."""
    os.makedirs(os.path.join(HERE, 'backups'), exist_ok=True)
    have = sheets_by_alias()
    if spec['alias'] not in have:
        aliases = {k: v['id'] for k, v in have.items()}
        fields = []
        for f in spec['fields']:
            g = {k: v for k, v in f.items() if not k.startswith('_')}
            ds = g.get('dataSource')
            if isinstance(ds, str) and ds.startswith('@'):
                g['dataSource'] = aliases[ds[1:]]
            fields.append(g)
        sec, parent = section_ids(spec['group'])
        # `worksheet create --fields` takes the JSON itself (no @file, unlike update-fields)
        args = ['worksheet', 'create', APP, spec['name'], '--section-id', sec, '--icon', spec.get('icon', 'table'),
                '--alias', spec['alias'], '--desc', spec.get('desc', ''), '--fields', json.dumps(fields, ensure_ascii=False),
                '--title-name', spec['title']]
        if parent:
            args += ['--parent-group-id', parent]
        hap(*args)
        have = sheets_by_alias()
    ws = have[spec['alias']]['id']
    if spec.get('visibility'):
        hap('worksheet', 'update', ws, '--visibility', spec['visibility'], '-a', APP)

    raw = raw_fields(ws)
    by_name = {c['controlName']: c for c in raw}
    fixes, missing = [], []
    for f in spec['fields']:
        c = by_name.get(f['name']) or next((x for x in raw if x.get('alias') == f['_alias']), None)
        if not c:
            missing.append(f['name'])
            continue
        want = {'alias': f['_alias']}
        if f['_desc']:
            want['desc'] = f['_desc']
        if 'dot' in f['extra']:
            want['dot'] = f['extra']['dot']
        diff = {k: v for k, v in want.items() if c.get(k) != v}
        if diff:
            fixes.append({'type': 'field.update', 'worksheet': ws, 'field': c['controlId'], 'set': diff})
    if missing:
        raise RuntimeError(f"{spec['name']}: fields missing after create: {missing}")
    for op in fixes:  # one op per spec: a failure must not stop the others silently
        apply_spec([op])
    raw = raw_fields(ws)
    by_alias = {c.get('alias'): c for c in raw}
    bad = [f['_alias'] for f in spec['fields'] if f['_alias'] not in by_alias]
    if bad:
        raise RuntimeError(f"{spec['name']}: aliases still missing after the fix: {bad}")
    record(ws, 'worksheet', spec['name'], spec['module'], step)
    for f in spec['fields']:
        c = by_alias[f['_alias']]
        record(c['controlId'], 'field', f"{spec['name']}.{f['name']}", f['_module'] or spec['module'], step)
    return ws, raw, len(fixes)


HIDDEN = '011'   # fieldPermission: visible / editable / shown on create


def by_alias(ws):
    return {c.get('alias'): c for c in raw_fields(ws)}


def add_once(ws, control, module=None, label=None, step='step 4'):
    """Add one raw control unless its alias is already on the sheet; record it; return the field as read back."""
    have = by_alias(ws)
    if control['alias'] not in have:
        hap('worksheet', 'add-fields', ws, '--controls', json.dumps([control], ensure_ascii=False))
        have = by_alias(ws)
    if control['alias'] not in have:
        raise RuntimeError(f"{control['alias']} not on {ws} after add-fields")
    c = have[control['alias']]
    if module:
        record(c['controlId'], 'field', label or c['controlName'], module, step)
    return c


def set_show(ws, field_id, ids):
    """Columns a multi relation shows (CLI-made ones have none: PLATFORM-ISSUES P5)."""
    c = next(x for x in raw_fields(ws) if x['controlId'] == field_id)
    if (c.get('showControls') or []) != ids:
        apply_spec([{'type': 'field.update', 'worksheet': ws, 'field': field_id, 'set': {'showControls': ids}}])


def ensure_self_relation(ws, alias, name, rev_alias, rev_name, module, sheet_name, step, desc='', showtype_rev='6'):
    """Single self-relation plus its multi reverse. add-fields does not create the reverse side (P17), so
    pair-relation is run when it is missing; then the reverse gets its alias, name and display."""
    c = add_once(ws, {'type': 29, 'controlName': name, 'alias': alias, 'dataSource': ws, 'enumDefault': 1, 'desc': desc,
                      'advancedSetting': {'bidirectional': '1', 'showtype': '3'}}, module, f'{sheet_name}.{name}', step)
    rev = [x for x in raw_fields(ws) if x['type'] == 29 and x.get('sourceControlId') == c['controlId']
           and x['controlId'] != c['controlId']]
    if not rev:
        hap('worksheet', 'pair-relation', ws, c['controlId'], '--name', rev_name)
    r = ensure_reverse(ws, c['controlId'], rev_alias, rev_name, module, showtype_rev, step)
    return c, r


def ensure_reverse(target_ws, relation_control_id, alias, name, module, showtype=None, step='step 4'):
    """Name, alias and display of the reverse field a two-way relation created on the target sheet."""
    raw = raw_fields(target_ws)
    c = next((x for x in raw if x.get('sourceControlId') == relation_control_id and x['type'] == 29), None)
    if not c:
        raise RuntimeError(f'no reverse field for {relation_control_id} on {target_ws}')
    want = {'alias': alias, 'controlName': name}
    diff = {k: v for k, v in want.items() if c.get(k) != v}
    if showtype and (c.get('advancedSetting') or {}).get('showtype') != showtype:
        adv = dict(c.get('advancedSetting') or {})
        adv['showtype'] = showtype
        diff['advancedSetting'] = adv
    if diff:
        apply_spec([{'type': 'field.update', 'worksheet': target_ws, 'field': c['controlId'], 'set': diff}])
    raw = raw_fields(target_ws)
    c = next(x for x in raw if x['controlId'] == c['controlId'])
    if c.get('alias') != alias or c.get('controlName') != name:
        raise RuntimeError(f'reverse field not fixed: {c.get("controlName")} / {c.get("alias")}')
    record(c['controlId'], 'field', f'reverse {name}', module, step)
    return c
