"""Wave 0 workflows #1, #2, #3, #5 and Country from Region (native-catalogue/workflow-nodes.md §5, rows 1-5).

C1 "Contacts - Sync from company" (create or update of Name, Related Company, Address Type, Address, Company Type):
   with a company -> read it (get_relation, fresh), Display Name "Company, Person" (#1), commercial entity, company
   name, Tax ID, other identifiers and industry from it (#2); a Contact-type person also takes its address and
   country (#3). Without a company -> Display Name = Name, commercial entity = itself, Country from the Region.
C2 "Contacts - Push company changes to people" (update of a company's name, display name, Tax ID, identifiers,
   industry or address): rewrite its people (#1/#2) and the address of its Contact-type people (#3).
C3 "Contacts - Language from company" (create with a company): the person takes the company's language (#5).
Country from Region: a query on Countries where Countries.Region *contains* the contact's Region. A Region value
read in a function is a Chinese path (Malaysia/Selangor, in Simplified Chinese), not the code, so the code cannot be cut out of it.
Run: python step6_wf_contacts.py
"""
import json
from wflib import S, F, option_key, create_flow, batch_add, node_ids, publish, cond, lit, fld

STEP = 'v2 step 6 (#1-#5)'
C, K = 'res_partner', 'res_country'
COMMERCIAL = ['vat', 'additional_identifiers', 'industry_id']
ADDRESS = ['street', 'street2', 'zip', 'city', 'x_base__region', 'country_id']


def f(a):
    return F(C, a)


def copy(node, aliases):
    return [{'fieldId': f(a), 'value': fld(node, f(a))} for a in aliases]


def country_query(alias, source):
    return {'nodeAlias': alias, 'nodeType': 'get_single', 'name': 'Country of the address',
            'config': {'worksheet': S[K], 'execute_type': 2,
                       'filter': {'logic': 'and', 'items': [
                           {'left': {'node': {'nodeAlias': alias}, 'fieldId': F(K, 'x_base__region')}, 'op': 'contains',
                            'right': {'kind': 'field', 'node': {'nodeAlias': source}, 'fieldId': f('x_base__region')}}]}}}


def upd(alias, name, fields):
    return {'nodeAlias': alias, 'nodeType': 'update_record', 'name': name,
            'config': {'worksheet': S[C], 'target': {'node': 'trigger'}, 'fields': fields}}


def c1():
    pid = create_flow('Contacts - Sync from company', 'worksheet', 'base', STEP,
                      'Display name, commercial entity, tax ID, identifiers, industry and (for Contact-type people) '
                      'address from the company; Country from the address (Odoo res.partner #1-#3).')
    if 'Has company?' in node_ids(pid)[0]:
        return pid
    dn = (f'IF(ISBLANK($trigger-{f("name")}$), CONCAT($parent-{f("complete_name")}$, ", ", STRING($trigger-{f("type")}$)), '
          f'CONCAT($parent-{f("complete_name")}$, ", ", $trigger-{f("name")}$))')
    child_common = [{'fieldId': f('complete_name'), 'value': fld('dn', 'string_fx_id')},
                    {'fieldId': f('commercial_partner_id'), 'value': fld('parent', f('commercial_partner_id'))},
                    {'fieldId': f('commercial_company_name'), 'value': fld('parent', f('commercial_company_name'))}] \
        + copy('parent', COMMERCIAL)
    nodes = [{'nodeAlias': 'has', 'nodeType': 'branch', 'name': 'Has company?', 'config': {'mode': 'exclusive', 'paths': [
        {'alias': 'p_child', 'name': 'With a company',
         'condition': {'logic': 'and', 'items': [cond('trigger', f('name'), 'not_empty')]},  # patched below
         'nodes': [
             {'nodeAlias': 'parent', 'nodeType': 'get_relation', 'name': 'The company',
              'config': {'worksheet': S[C], 'target': {'node': 'trigger'}, 'fields': [{'fieldId': f('parent_id')}]}},
             {'nodeAlias': 'dn', 'nodeType': 'compute', 'name': 'Display name',
              'config': {'mode': 'function', 'output_type': 'text', 'formula': dn}},
             {'nodeAlias': 'kind', 'nodeType': 'branch', 'name': 'Contact type?', 'config': {'mode': 'exclusive', 'paths': [
                 {'alias': 'p_contact', 'name': 'Contact',
                  'condition': {'logic': 'and', 'items': [cond('trigger', f('type'), 'eq', option_key(C, 'type', 'Contact'))]},
                  'nodes': [upd('w_contact', 'Company fields and address', child_common + copy('parent', ADDRESS))]},
                 {'alias': 'p_addr', 'name': 'Other address types',
                  'nodes': [country_query('q_own', 'trigger'),
                            upd('w_addr', 'Company fields, own country',
                                child_common + [{'fieldId': f('country_id'), 'value': {'kind': 'record', 'node': 'q_own'}}])]},
             ]}}]},
        {'alias': 'p_top', 'name': 'No company',  # also a company under a parent company (people_only patch)
         'nodes': [
             country_query('q_top', 'trigger'),
             {'nodeAlias': 'co', 'nodeType': 'branch', 'name': 'Company?', 'config': {'mode': 'exclusive', 'paths': [
                 {'alias': 'p_co', 'name': 'Company',
                  'condition': {'logic': 'and', 'items': [cond('trigger', f('company_type'), 'eq', option_key(C, 'company_type', 'Company'))]},
                  'nodes': [upd('w_co', 'Itself as commercial entity', [
                      {'fieldId': f('complete_name'), 'value': fld('trigger', f('name'))},
                      {'fieldId': f('commercial_partner_id'), 'value': {'kind': 'record', 'node': 'trigger'}},
                      {'fieldId': f('commercial_company_name'), 'value': fld('trigger', f('name'))},
                      {'fieldId': f('country_id'), 'value': {'kind': 'record', 'node': 'q_top'}}])]},
                 {'alias': 'p_person', 'name': 'Individual',
                  'nodes': [upd('w_person', 'Itself, no company name', [
                      {'fieldId': f('complete_name'), 'value': fld('trigger', f('name'))},
                      {'fieldId': f('commercial_partner_id'), 'value': {'kind': 'record', 'node': 'trigger'}},
                      {'fieldId': f('commercial_company_name'), 'op': 'clear', 'value': {'kind': 'empty'}},
                      {'fieldId': f('country_id'), 'value': {'kind': 'record', 'node': 'q_top'}}])]},
             ]}}]},
    ]}}]
    batch_add(pid, nodes, '--trigger-worksheet', S[C], '--trigger-event', 'create_or_update',
              '--trigger-fields', ','.join(f(a) for a in ('name', 'parent_id', 'type', 'x_base__region', 'company_type')))
    return pid


def c2():
    pid = create_flow('Contacts - Push company changes to people', 'worksheet', 'base', STEP,
                      'A company\'s name, tax ID, identifiers, industry and address are copied to its people (Odoo #1-#3).')
    if 'Its people' in node_ids(pid)[0]:
        return pid
    nodes = [
        {'nodeAlias': 'people', 'nodeType': 'get_relation_records', 'name': 'Its people',
         'config': {'worksheet': S[C], 'target': {'node': 'trigger'}, 'fields': [{'fieldId': f('child_ids')}]}},
        {'nodeAlias': 'w_people', 'nodeType': 'update_record', 'name': 'Company fields on people',
         'config': {'worksheet': S[C], 'target': {'node': 'people'}, 'fields': [
             {'fieldId': f('complete_name'), 'value': {'kind': 'template',
                                                       'value': f'$trigger-{f("complete_name")}$, $people-{f("name")}$'}},
             {'fieldId': f('commercial_partner_id'), 'value': fld('trigger', f('commercial_partner_id'))},
             {'fieldId': f('commercial_company_name'), 'value': fld('trigger', f('commercial_company_name'))}]
             + copy('trigger', COMMERCIAL)}},
        {'nodeAlias': 'contacts', 'nodeType': 'get_relation_records', 'name': 'Its Contact-type people',
         'config': {'worksheet': S[C], 'target': {'node': 'trigger'}, 'fields': [{'fieldId': f('child_ids')}],
                    'filter': {'logic': 'and', 'items': [
                        {'left': {'node': {'nodeAlias': 'contacts'}, 'fieldId': f('type')}, 'op': 'eq',
                         'right': lit(option_key(C, 'type', 'Contact'))}]}}},
        {'nodeAlias': 'w_addr', 'nodeType': 'update_record', 'name': 'Address on Contact-type people',
         'config': {'worksheet': S[C], 'target': {'node': 'contacts'}, 'fields': copy('trigger', ADDRESS)}},
    ]
    batch_add(pid, nodes, '--trigger-worksheet', S[C], '--trigger-event', 'update',
              '--trigger-fields', ','.join(f(a) for a in ['name', 'complete_name', 'commercial_company_name'] + COMMERCIAL + ADDRESS),
              '--trigger-filter', json.dumps({'logic': 'and', 'items': [
                  cond('trigger', f('company_type'), 'eq', option_key(C, 'company_type', 'Company'))]}))
    return pid


def c3():
    pid = create_flow('Contacts - Language from company', 'worksheet', 'base', STEP,
                      'A new person under a company takes the company\'s language (Odoo #5).')
    if 'Has company?' in node_ids(pid)[0]:
        return pid
    nodes = [{'nodeAlias': 'has', 'nodeType': 'branch', 'name': 'Has company?', 'config': {'mode': 'exclusive', 'paths': [
        {'alias': 'p_child', 'name': 'With a company',
         'condition': {'logic': 'and', 'items': [cond('trigger', f('name'), 'not_empty')]},  # patched below
         'nodes': [{'nodeAlias': 'parent', 'nodeType': 'get_relation', 'name': 'The company',
                    'config': {'worksheet': S[C], 'target': {'node': 'trigger'}, 'fields': [{'fieldId': f('parent_id')}]}},
                   upd('w_lang', 'Language', copy('parent', ['lang']))]},
        {'alias': 'p_none', 'name': 'No company', 'nodes': []}]}}]
    batch_add(pid, nodes, '--trigger-worksheet', S[C], '--trigger-event', 'create')
    return pid


def patch_has_company(pid, people_only=False):
    """The CLI has no 'relation is not empty' (it maps not_empty to id 7, which relations lack; raw ids are refused:
    PLATFORM-ISSUES P22). Write the stored condition (conditionId 31) on the 'With a company' path.
    people_only (C1, 24 Nov): Odoo makes a company its own commercial entity and keeps its own name even under a
    parent company (_compute_commercial_partner, _compute_complete_name), so only a Person takes the company path."""
    from lib import hap
    names, d = node_ids(pid)
    start = d.get('startEventId') or next(k for k, v in d['flowNodeMap'].items() if v.get('typeId') == 0)
    # batch-add does not keep a path's name when the path has a condition: take the gateway's first path
    gw = d['flowNodeMap'][names['Has company?']]
    nid = gw['flowIds'][0]
    hap('workflow', 'node', 'rename', pid, nid, '-n', 'Person with a company' if people_only else 'With a company', ok_fail=True)
    group = [{'nodeId': start, 'nodeType': 0, 'appType': 1, 'filedId': f('parent_id'), 'filedTypeId': 29,
              'enumDefault': 1, 'conditionId': '31', 'conditionValues': []}]
    if people_only:
        group.append({'nodeId': start, 'nodeType': 0, 'appType': 1, 'filedId': f('company_type'), 'filedTypeId': 9,
                      'enumDefault': 0, 'conditionId': '9',
                      'conditionValues': [{'value': {'key': option_key(C, 'company_type', 'Person'), 'value': 'Person'}}]})
    hap('workflow', 'node', 'save', pid, nid, '--type', '2', '-c', json.dumps({'operateCondition': [group]}))


def c4():
    """C4 "Contacts - Country from Region" (24 Nov fix). A query whose filter value is empty fails the whole run
    ("the filter value is empty: Region", PLATFORM-ISSUES P33), so the country queries inside C1 stopped C1 for every contact without a
    Region: no display name, no commercial entity. The country now has its own flow whose trigger condition is
    "Region is not empty"; C1 keeps only the company copy (a Contact-type person takes the company's country)."""
    from lib import hap
    pid = create_flow('Contacts - Country from Region', 'worksheet', 'base', 'v2 step 6 (fix 24 Nov)',
                      "Country = the Countries row whose Region contains the contact's Region. Runs only when the "
                      'Region is filled; without a Region the country is left as it is.')
    if 'Country of the address' not in node_ids(pid)[0]:
        q = country_query('q', 'trigger')
        q['config'].pop('execute_type', None)
        q['config']['ifEmpty'] = 'continue'
        batch_add(pid, [q, upd('w', 'Country from the Region',
                                [{'fieldId': f('country_id'), 'value': {'kind': 'record', 'node': 'q'}}])],
                  '--trigger-worksheet', S[C], '--trigger-event', 'create_or_update',
                  '--trigger-fields', f('x_base__region'))
        names, d = node_ids(pid)
        start = next(k for k, v in d['flowNodeMap'].items() if v.get('typeId') == 0)
        hap('workflow', 'node', 'rename', pid, start, '-n', 'Region filled in', ok_fail=True)
    return pid


def split_country(pid):
    """Patch C1 as built on 23 Nov: drop its two country queries and the country writes that used them."""
    from lib import hap
    names, d = node_ids(pid)
    m = d['flowNodeMap']
    for name in ('Itself as commercial entity', 'Itself, no company name', 'Company fields, own country'):
        nid = names.get(name)
        if not nid:
            continue
        n = hap('workflow', 'node', 'get', pid, nid, '--type', '6')
        n = n.get('data', n)
        keep = [x for x in n.get('fields') or [] if x.get('fieldId') != f('country_id')]
        if len(keep) != len(n.get('fields') or []):
            # node get also returns read-only context (controls, flowNodeList, formulaMap, selectNodeObj): too long
            # for a command line and not part of the step. Save the step's own settings.
            cfg = {k: n.get(k) for k in ('name', 'actionId', 'appId', 'appType', 'selectNodeId', 'executeType', 'filters', 'sorts', 'conditions', 'operateCondition') if n.get(k) is not None}
            cfg['fields'] = keep
            hap('workflow', 'node', 'save', pid, nid, '--type', '6', '-c', json.dumps(cfg, ensure_ascii=False))
    for nid, v in m.items():
        if v.get('name') == 'Country of the address':
            hap('workflow', 'node', 'delete', pid, nid, '-y')
    if names.get('Company fields, own country'):
        hap('workflow', 'node', 'rename', pid, names['Company fields, own country'], '-n', 'Company fields, own address')
    # batch-add drops the names of paths (PLATFORM-ISSUES P23): name them
    for gw, labels in (('Has company?', ('Person with a company', 'No company')), ('Contact type?', ('Contact', 'Other address types')),
                       ('Company?', ('Company', 'Individual'))):
        for path, label in zip(m[names[gw]]['flowIds'], labels):
            if m[path].get('name') != label:
                hap('workflow', 'node', 'rename', pid, path, '-n', label, ok_fail=True)


if __name__ == '__main__':
    for fn in (c1, c2, c3, c4):
        pid = fn()
        if fn in (c1, c3):
            patch_has_company(pid, people_only=fn is c1)
        if fn is c1:
            split_country(pid)
        r = publish(pid)
        print(fn.__name__, pid, 'published' if r.get('isPublish') else json.dumps(r, ensure_ascii=False)[:700])
