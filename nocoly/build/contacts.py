#!/usr/bin/env python3
"""Build the Contacts worksheet (Odoo res.partner) in ERP Master.

    ~/.hap-venv/bin/python nocoly/build/contacts.py fields   # 1. controls, in one save
    ~/.hap-venv/bin/python nocoly/build/contacts.py layout   # 2. tabs, company filter, reverse columns
    ~/.hap-venv/bin/python nocoly/build/contacts.py rules    # 3. interaction + validation rules (upsert by name)
    ~/.hap-venv/bin/python nocoly/build/contacts.py views    # 4. Contacts / Kanban / Archived views (upsert by name)
    ~/.hap-venv/bin/python nocoly/build/contacts.py buttons  # 5. Archive / Unarchive buttons and their workflows
    ~/.hap-venv/bin/python nocoly/build/contacts.py automations  # 6. company -> contact sync workflows
    ~/.hap-venv/bin/python nocoly/build/contacts.py show     # print the live control list

Requirements: nocoly/worksheets/01-contacts.md.

`fields` replaces the whole control set, so it only runs on a worksheet that has
no records yet. After that, append with `hap worksheet add-fields`.
"""
import json, subprocess, sys, uuid

from hap_cli.core import worksheet_templates as wt
from hap_cli.core.app_creator.fields import bidirectional_relation_control, field_permission_str

import hap

WS = hap.ids()['worksheets']['Contacts']
MALAYSIA = json.dumps({'name': 'Malaysia', 'iso2': 'my', 'dialCode': '60'})


def options(labels, default):
    """Option dicts with stable keys, the default marked."""
    return [{'key': str(uuid.uuid4()), 'value': v, 'index': i + 1, 'checked': v == default,
             'isDeleted': False, 'color': c}
            for i, (v, c) in enumerate(zip(labels, ['#C9E6FC', '#C3F2F2', '#C2F1D2', '#FFE7B1']))]


def default_option(opts):
    key = next(o['key'] for o in opts if o['checked'])
    return json.dumps([{'cid': '', 'rcid': '', 'staticValue': key}])


def ctl(kind, name, row, col=0, size=12, alias='', hint=None, **kw):
    c = wt.build_control(kind, name, row=row, col=col, size=size, hint=hint, **kw)
    c['alias'] = alias
    return c


def step_fields():
    existing = hap.controls(WS)
    if len(existing) > 3:
        sys.exit(f'Contacts already has {len(existing)} controls — refusing to replace them.')
    hap.backup('contacts_controls_pre_fields', existing)
    keep = hap.by_name(existing)                      # reuse the default Name and Attachment ids

    company_type = options(['Person', 'Company'], default='Company')
    address_type = options(['Contact', 'Invoice', 'Delivery', 'Other'], default='Contact')

    c = []
    # header
    c.append(ctl('FLAT_MENU', 'Company Type', 0, alias='company_type', required=True,
                 options=company_type, advanced_setting={'defsource': default_option(company_type)}))
    name = ctl('TEXT', 'Name', 1, alias='name', hint='e.g. Brandon Freeman', is_title=True)
    name['controlId'] = keep['Name']['controlId']
    c.append(name)
    c.append(ctl('EMAIL', 'Email', 2, 0, 6, alias='email', hint='Email'))
    c.append(ctl('MOBILE_PHONE', 'Phone', 2, 1, 6, alias='phone', hint='Phone',
                 advanced_setting={'defaultarea': MALAYSIA}))
    # company, address type and the right-hand column
    company = bidirectional_relation_control(
        'Company', target_worksheet_id=WS, host_worksheet_id=WS,
        forward_id=str(uuid.uuid4()), reverse_id=str(uuid.uuid4()), reverse_name='Contacts',
        multi=False, display='dropdown', reverse_display='table')
    company.update(row=3, col=0, size=6, alias='parent_id', hint='Company Name...')
    company['sourceControl'].update(alias='child_ids')
    c.append(company)
    c.append(ctl('TEXT', 'Job Position', 3, 1, 6, alias='function', hint='e.g. Sales Director'))
    c.append(ctl('DROP_DOWN', 'Address Type', 4, 0, 6, alias='type', hint='Select', required=True,
                 options=address_type, advanced_setting={'defsource': default_option(address_type)}))
    c.append(ctl('TEXT', 'Tax ID', 4, 1, 6, alias='vat', hint='e.g. BE0477472701'))
    c.append(ctl('TEXT', 'Website', 5, 0, 6, alias='website', hint='e.g. https://www.odoo.com'))
    # address
    c.append(ctl('SPLIT_LINE', 'Address', 6))
    c.append(ctl('TEXT', 'Street', 7, 0, 6, alias='street', hint='Street...'))
    c.append(ctl('TEXT', 'Street 2', 7, 1, 6, alias='street2', hint='Street 2...'))
    c.append(ctl('TEXT', 'City', 8, 0, 6, alias='city', hint='City'))
    c.append(ctl('TEXT', 'State', 8, 1, 6, alias='state', hint='State'))
    c.append(ctl('TEXT', 'ZIP', 9, 0, 6, alias='zip', hint='ZIP'))
    c.append(ctl('TEXT', 'Country', 9, 1, 6, alias='country', hint='Country'))
    image = ctl('ATTACHMENT', 'Image', 10, alias='image_1920', hint='Upload an image')
    image['controlId'] = keep['Attachment']['controlId']
    c.append(image)
    # tabs (their children are assigned in the layout step, once ids are real)
    c.append(ctl('SECTION', 'Contacts', 11))
    c.append(ctl('SECTION', 'Sales & Purchase', 13))
    c.append(ctl('SPLIT_LINE', 'Sales', 14))
    c.append(ctl('USER_PICKER', 'Salesperson', 15, 0, 6, alias='user_id', hint='Salesperson'))
    c.append(ctl('SPLIT_LINE', 'Misc', 16))
    c.append(ctl('TEXT', 'Company ID', 17, 0, 6, alias='company_registry', hint='Company ID'))
    c.append(ctl('TEXT', 'Reference', 17, 1, 6, alias='ref', hint='Reference'))
    c.append(ctl('SECTION', 'Notes', 18))
    c.append(ctl('RICH_TEXT', 'Notes', 19, alias='comment', hint='Internal notes...'))
    # hidden
    active = ctl('SWITCH', 'Active', 20, 0, 6, alias='active',
                 advanced_setting={'defsource': json.dumps([{'cid': '', 'rcid': '', 'staticValue': '1'}])})
    active['fieldPermission'] = field_permission_str(hidden=True)
    c.append(active)

    hap.run('worksheet', 'update-fields', WS, '--controls', json.dumps(c, ensure_ascii=False))
    show()


def step_layout():
    ctrls = hap.controls(WS)
    hap.backup('contacts_controls_pre_layout', ctrls)
    tabs = {c['controlName']: c['controlId'] for c in ctrls if c['type'] == 52}
    field = {c['controlName']: c for c in ctrls if c['type'] != 52}
    in_tab = {'Contacts': tabs['Contacts'],
              'Sales': tabs['Sales & Purchase'], 'Salesperson': tabs['Sales & Purchase'],
              'Misc': tabs['Sales & Purchase'], 'Company ID': tabs['Sales & Purchase'],
              'Reference': tabs['Sales & Purchase'],
              'Notes': tabs['Notes']}
    for c in ctrls:
        if c['type'] != 52 and c['controlName'] in in_tab:
            c['sectionId'] = in_tab[c['controlName']]

    ct = field['Company Type']
    company_key = next(o['key'] for o in ct['options'] if o['value'] == 'Company')
    only_companies = [{'controlId': ct['controlId'], 'dataType': 9, 'spliceType': 1, 'filterType': 2,
                       'values': [company_key], 'value': '', 'isDynamicsource': False,
                       'dynamicSource': []}]
    for c in ctrls:
        if c['type'] == 29 and c['controlName'] == 'Company':
            c['advancedSetting']['filters'] = json.dumps(only_companies)
        if c['type'] == 29 and c['controlName'] == 'Contacts':
            # the server parks a new reverse control at row 9999, width 0, without its alias
            c.update(row=12, col=0, size=12, alias='child_ids')
            cols = [field[n]['controlId'] for n in ('Name', 'Address Type', 'Email', 'Phone', 'Job Position')]
            c['showControls'] = cols
            c['advancedSetting']['controlssorts'] = json.dumps(cols)

    hap.run('worksheet', 'update-fields', WS, '--controls', json.dumps(ctrls, ensure_ascii=False))
    show()


SHOW, HIDE, REQUIRE, ERROR = 1, 2, 5, 6          # rule item types
EQ, NE, EMPTY, NOT_EMPTY = 2, 6, 7, 8             # filter operators


def cond(c, op, key=None):
    return {'controlId': c['controlId'], 'dataType': c['type'], 'spliceType': 1, 'filterType': op,
            'value': '', 'values': [key] if key else [], 'dynamicSource': [], 'isGroup': False}


def any_of(*groups):
    """OR of AND-groups: any_of([a, b], [c]) == (a and b) or c."""
    return [{'controlId': '', 'dataType': 1, 'spliceType': 2, 'filterType': 0, 'value': '', 'values': [],
             'dynamicSource': [], 'isGroup': True, 'groupFilters': list(g)} for g in groups]


def item(kind, *ctrls, message=''):
    return {'type': kind, 'isAll': False, 'message': message,
            'controls': [{'isCustom': False, 'controlId': c['controlId'], 'childControlIds': [],
                          'permission': [], 'type': '', 'value': ''} for c in ctrls]}


def step_rules():
    f = hap.by_name(c for c in hap.controls(WS) if c['type'] != 52)
    key = lambda field, label: next(o['key'] for o in f[field]['options'] if o['value'] == label)
    company, person = key('Company Type', 'Company'), key('Company Type', 'Person')
    contact = key('Address Type', 'Contact')
    ct, parent = f['Company Type'], f['Company']

    rules = [  # (name, type 0=interaction 1=validation, filters, items)
        ('Company is hidden on companies', 0,
         any_of([cond(ct, EQ, company), cond(parent, EMPTY)]), [item(HIDE, parent)]),
        ('Job Position only for persons', 0,
         any_of([cond(ct, EQ, company)]), [item(HIDE, f['Job Position'])]),
        ('Address Type only under a company', 0,
         any_of([cond(parent, EMPTY)]), [item(HIDE, f['Address Type'])]),
        ('Company ID only on stand-alone companies', 0,
         any_of([cond(ct, EQ, person)], [cond(parent, NOT_EMPTY)]), [item(HIDE, f['Company ID'])]),
        ('Name is required for contacts', 0,
         any_of([cond(f['Address Type'], EQ, contact)]), [item(REQUIRE, f['Name'])]),
        ('Contacts require a name', 1,
         any_of([cond(f['Address Type'], EQ, contact), cond(f['Name'], EMPTY)]),
         [item(ERROR, f['Name'], message='Contacts require a name')]),
    ]
    live = {r['name']: r for r in hap.listing('worksheet', 'rules', WS)}
    hap.backup('contacts_rules_pre_rules', list(live.values()))
    for name, kind, filters, items in rules:
        args = ['worksheet', 'save-rule', WS, '--name', name, '--type', str(kind),
                '--filters', json.dumps(filters), '--rule-items', json.dumps(items, ensure_ascii=False)]
        if kind == 1:
            args += ['--check-type', '1', '--hint-type', '0']      # enforce on API writes too
        if name in live:
            args += ['--rule-id', live[name]['ruleId']]
        hap.run(*args)
    for r in hap.listing('worksheet', 'rules', WS):
        acts = [(i['type'], [c['controlId'][-4:] for c in i['controls']], i.get('message', '')) for i in r['ruleItems']]
        print(f"type={r['type']} check={r.get('checkType')} disabled={r['disabled']}  {r['name']:<42} {acts}")


def step_views():
    app = hap.ids()['app']
    f = hap.by_name(c for c in hap.controls(WS) if c['type'] != 52)
    i = lambda *names: [f[n]['controlId'] for n in names]
    active = lambda op: {'type': 'group', 'logic': 'AND', 'children': [
        {'type': 'condition', 'field': f['Active']['controlId'], 'operator': op, 'value': ['1']}]}
    # Odoo _order is complete_name ASC. --view-spec ignores sort keys, so sort is set with --view-json below.
    sort = {'sortCid': f['Name']['controlId'], 'sortType': 2,
            'moreSort': [{'controlId': f['Name']['controlId'], 'dataType': 2, 'spliceType': 0, 'filterType': 0,
                          'dateRange': 0, 'dateRangeType': 0, 'value': '', 'values': [], 'minValue': '',
                          'maxValue': '', 'isAsc': True, 'dynamicSource': [], 'advancedSetting': {},
                          'isGroup': False, 'groupFilters': [], 'emptyRule': 0}]}
    by_name = {}
    views = {  # Odoo Contacts menu: list first, then kanban; archived behind the "Archived" filter
        'Contacts': dict(viewType='table', filter=active('eq'),
                         tableFields=i('Name', 'Email', 'Phone', 'Country', 'Company', 'Salesperson'),
                         quickFilters=i('Company Type', 'Salesperson', 'Company', 'Country'), **by_name),
        'Kanban': dict(viewType='gallery', filter=active('eq'),
                       card={'titleField': f['Name']['controlId'],
                             'displayFields': i('Email', 'Phone', 'City', 'Country'),
                             'coverField': f['Image']['controlId'], 'coverDirection': 'left',
                             'coverDisplayMode': 'square'}, **by_name),
        'Archived': dict(viewType='table', filter=active('ne'),
                         tableFields=i('Name', 'Email', 'Phone', 'Country', 'Company', 'Salesperson'),
                         **by_name),
    }
    live = hap.listing('worksheet', 'view', 'list', WS, '-a', app)
    hap.backup('contacts_views_pre_views', live)
    live = {v['name']: v['viewId'] for v in live}
    if 'Contacts' not in live and 'All' in live:                            # the default view becomes Contacts
        live['Contacts'] = live.pop('All')
    for name, spec in views.items():
        spec = {'name': name, **spec}
        if name in live:
            hap.run('worksheet', 'view', 'update', WS, live[name], '-a', app, '--view-spec', json.dumps(spec))
        else:
            hap.run('worksheet', 'view', 'create', WS, name, '-a', app, '--view-spec', json.dumps(spec))
    for v in hap.listing('worksheet', 'view', 'list', WS, '-a', app):
        hap.run('worksheet', 'view', 'update', WS, v['viewId'], '-a', app,
                '--view-json', json.dumps(sort), '--edit-attrs', 'sortCid,sortType,moreSort')
    names = {c['controlId']: c['controlName'] for c in f.values()}
    for v in hap.listing('worksheet', 'view', 'list', WS, '-a', app):
        print(f"{v['name']:<9} type={v['viewType']} sort={names.get(v.get('sortCid'), v.get('sortCid'))}/{v.get('sortType')} "
              f"filters={len(v.get('filters') or [])} fast={[names.get(x['controlId']) for x in v.get('fastFilters') or []]} "
              f"columns={[names.get(x, x) for x in v.get('displayControls') or []]} cover={names.get(v.get('coverCid'), '')}")


def button_workflow(process_id, fields, node_name):
    """Trigger by button -> update the triggering record -> publish (as lib/button_flows.py in the Sales repo)."""
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
    hap.run('workflow', 'publish', process_id)


def step_buttons():
    app = hap.ids()['app']
    f = hap.by_name(c for c in hap.controls(WS) if c['type'] != 52)
    active = f['Active']['controlId']
    when = lambda op: {'type': 'group', 'logic': 'AND', 'children': [
        {'type': 'condition', 'field': active, 'operator': op, 'value': ['1']}]}
    buttons = [  # Odoo ⚙ Actions › Archive / Unarchive
        ({'name': 'Archive', 'type': 'triggerWorkflow', 'enableWhen': when('eq'), 'isBatch': True,
          'confirm': True, 'confirmMsg': 'Are you sure that you want to archive this record?',
          'sureName': 'Archive', 'cancelName': 'Cancel'}, '0', 'Archive the contact'),
        ({'name': 'Unarchive', 'type': 'triggerWorkflow', 'enableWhen': when('ne'), 'isBatch': True},
         '1', 'Unarchive the contact'),
    ]
    live = hap.listing('worksheet', 'custom-actions', WS)
    hap.backup('contacts_buttons_pre_buttons', live)
    live = {b['name']: b for b in live}
    ids = hap.ids()
    for spec, value, node_name in buttons:
        if spec['name'] in live:
            # create-custom-action --action-spec ignores --btn-id and always adds a new button (hap-cli 0.8.31)
            print(f"  {spec['name']}: exists ({live[spec['name']]['btnId']}); not re-created")
            continue
        args = ['worksheet', 'create-custom-action', WS, '-a', app, '--action-spec', json.dumps(spec)]
        out = hap.run(*args)
        data = out.get('data', out) if isinstance(out, dict) else {}
        pid = data.get('processId') or ids.get('workflows', {}).get(spec['name'])
        if not pid:
            sys.exit(f"{spec['name']}: no processId in create-custom-action output: {out}")
        ids.setdefault('workflows', {})[spec['name']] = pid
        button_workflow(pid, [{'fieldId': active, 'value': value}], node_name)
    for b in hap.listing('worksheet', 'custom-actions', WS):
        ids.setdefault('buttons', {})[b['name']] = b['btnId']
    json.dump(ids, open(hap.IDS_PATH, 'w'), ensure_ascii=False, indent=1)
    for b in hap.listing('worksheet', 'custom-actions', WS):
        print(f"{b['name']:<10} btnId={b['btnId']} clickType={b.get('clickType')} workflowType={b.get('workflowType')} "
              f"isBatch={b.get('isBatch')} filters={len(b.get('filters') or [])} confirm={b.get('confirmMsg', '')!r}")


ADDRESS = ['Street', 'Street 2', 'City', 'State', 'ZIP', 'Country']


def step_automations():
    """Odoo res.partner._fields_sync, company -> contacts. Upstream sync (contact -> company) is left out."""
    ids = hap.ids()
    f = hap.by_name(c for c in hap.controls(WS) if c['type'] != 52)
    fid = lambda n: f[n]['controlId']
    option = lambda field, label: next({'key': o['key'], 'value': o['value'], 'isDeleted': False}
                                       for o in f[field]['options'] if o['value'] == label)
    trigger = {'nodeAlias': 'trigger'}

    def when(node, name, op, label=None):
        item = {'left': {'node': {'nodeAlias': node}, 'fieldId': fid(name), '_filedTypeId': f[name]['type']},
                'op': op}
        if label:
            item['right'] = {'kind': 'literal', 'value': option(name, label)}
        return item

    def copy(names, source):
        return [{'fieldId': fid(n), 'valueRef': {'kind': 'field', 'node': {'nodeAlias': source},
                                                 'fieldId': fid(n), 'nodeAppId': WS}} for n in names]

    def update(alias, name, target, names, source):
        return {'nodeAlias': alias, 'nodeType': 'update_record', 'name': name,
                'config': {'target': {'node': target}, 'fields': copy(names, source)}}

    def branch(alias, name, condition, then):
        return {'nodeAlias': alias, 'nodeType': 'branch', 'name': name, 'config': {'paths': [
            {'alias': alias + '_yes', 'name': 'Yes', 'condition': condition, 'nodes': [then]},
            {'alias': alias + '_no', 'name': 'No'}]}}

    workflows = [
        dict(name='Contacts: copy company details to its contact',
             desc='Odoo onchange_parent_id / _fields_sync: when a contact is linked to a company, copy the '
                  'company address (Contact-type only, and only if the company has one), its Tax ID, and its '
                  'salesperson for a person who has none.',
             event='create_or_update', fields=[fid('Company'), fid('Address Type')],
             filter={'logic': 'and', 'items': [when('trigger', 'Company', 'not_empty')]},
             nodes=[
                 {'nodeAlias': 'company', 'nodeType': 'get_relation', 'name': 'Get the company',
                  'config': {'target': {'node': trigger}, 'fields': [{'fieldId': fid('Company')}], 'worksheet': WS}},
                 branch('address', 'Contact-type, and the company has an address?',
                        {'groups': [{'items': [when('trigger', 'Address Type', 'eq', 'Contact'),
                                               when('company', n, 'not_empty')]} for n in ADDRESS]},
                        update('copy_address', 'Copy the company address', trigger, ADDRESS, 'company')),
                 branch('vat', 'The company has a Tax ID?',
                        {'logic': 'and', 'items': [when('company', 'Tax ID', 'not_empty')]},
                        update('copy_vat', 'Copy the Tax ID', trigger, ['Tax ID'], 'company')),
                 branch('salesperson', 'A person without a salesperson?',
                        {'logic': 'and', 'items': [when('trigger', 'Company Type', 'eq', 'Person'),
                                                   when('trigger', 'Salesperson', 'empty'),
                                                   when('company', 'Salesperson', 'not_empty')]},
                        update('copy_salesperson', 'Copy the salesperson', trigger, ['Salesperson'], 'company')),
             ]),
        dict(name='Contacts: push company address and Tax ID to its contacts',
             desc="Odoo _children_sync: a company's address goes to its Contact-type contacts; its Tax ID and "
                  'Company ID go to all of its contacts.',
             event='update', fields=[fid(n) for n in ADDRESS + ['Tax ID', 'Company ID']], filter=None,
             nodes=[
                 {'nodeAlias': 'all_contacts', 'nodeType': 'get_relation_records', 'name': 'Get its contacts',
                  'config': {'target': {'node': trigger}, 'fields': [{'fieldId': fid('Contacts')}], 'worksheet': WS}},
                 update('push_vat', 'Copy Tax ID and Company ID to them', {'nodeAlias': 'all_contacts'},
                        ['Tax ID', 'Company ID'], 'trigger'),
                 {'nodeAlias': 'contact_type', 'nodeType': 'get_relation_records',
                  'name': 'Get its Contact-type contacts',
                  'config': {'target': {'node': trigger}, 'fields': [{'fieldId': fid('Contacts')}], 'worksheet': WS}},
                 update('push_address', 'Copy the address to them', {'nodeAlias': 'contact_type'}, ADDRESS, 'trigger'),
             ],
             only_contact_type='Get its Contact-type contacts'),
    ]

    for wf in workflows:
        pid = ids.setdefault('workflows', {}).get(wf['name'])
        if pid:
            print(f"{wf['name']}: exists ({pid}); not rebuilt")
            continue
        out = hap.run('workflow', 'create', '-c', ids['org'], '-n', wf['name'], '-a', ids['app'],
                      '--type', 'worksheet', '-d', wf['desc'])
        data = out.get('data', out) if isinstance(out, dict) else out
        pid = data if isinstance(data, str) else (data.get('id') or data.get('processId'))
        ids['workflows'][wf['name']] = pid
        json.dump(ids, open(hap.IDS_PATH, 'w'), ensure_ascii=False, indent=1)
        args = ['workflow', 'node', 'batch-add', pid, '--nodes', json.dumps(wf['nodes'], ensure_ascii=False),
                '--trigger-worksheet', WS, '--trigger-event', wf['event'],
                '--trigger-fields', ','.join(wf['fields']), '--trigger-alias', 'trigger']
        if wf['filter']:
            args += ['--trigger-filter', json.dumps(wf['filter'], ensure_ascii=False)]
        hap.run(*args)
        if wf.get('only_contact_type'):
            # --nodes sends a search filter as operateCondition; the UI stores it as `filters` on the node itself
            proc = hap.run('workflow', 'node', 'list', pid)
            node = next(n for n in proc['flowNodeMap'].values() if n['name'] == wf['only_contact_type'])
            o = option('Address Type', 'Contact')
            config = {'actionId': '401', 'appId': WS, 'selectNodeId': proc['startEventId'],
                      'fields': [{'fieldId': fid('Contacts')}],
                      'filters': [{'spliceType': 2, 'conditions': [[{
                          'nodeId': node['id'], 'nodeType': 13, 'actionId': '401', 'filedId': fid('Address Type'),
                          'filedValue': 'Address Type', 'filedTypeId': 11, 'enumDefault': 0, 'conditionId': '9',
                          'sourceType': 0, 'conditionValues': [{'value': {**o, 'score': None, 'index': None}}]}]]}]}
            hap.run('workflow', 'node', 'save', pid, node['id'], '--type', '13', '-c', json.dumps(config),
                    '-n', node['name'])
        print(hap.run('workflow', 'publish', pid))
    for name, pid in ids['workflows'].items():
        if name.startswith('Contacts:'):
            print(subprocess.run(['hap', 'workflow', 'structure', pid], capture_output=True, text=True).stdout)


def show():
    ctrls = hap.controls(WS)
    tabs = {c['controlId']: c['controlName'] for c in ctrls if c['type'] == 52}
    for c in sorted(ctrls, key=lambda c: (c.get('row', 0), c.get('col', 0))):
        extra = []
        if c.get('attribute') == 1: extra.append('title')
        if c.get('required'): extra.append('required')
        if c.get('fieldPermission') not in (None, '', '111'): extra.append(f"perm={c['fieldPermission']}")
        if c.get('sectionId'): extra.append(f"tab={tabs.get(c['sectionId'], c['sectionId'])}")
        if c.get('dataSource'): extra.append(f"-> {c['dataSource']} pair={c.get('sourceControlId')}")
        if c.get('options'): extra.append('opts=' + '/'.join(o['value'] for o in c['options']))
        print(f"r{c.get('row', 0):<2} c{c.get('col', 0)} s{c.get('size', '?'):<2} {c['type']:>2} "
              f"{c['controlName']:<18} {c['controlId']}  {c.get('alias') or '':<17} {' '.join(extra)}")
    print(f'{len(ctrls)} controls')


if __name__ == '__main__':
    {'fields': step_fields, 'layout': step_layout, 'rules': step_rules, 'views': step_views,
     'buttons': step_buttons, 'automations': step_automations,
     'show': show}[sys.argv[1] if len(sys.argv) > 1 else 'show']()
