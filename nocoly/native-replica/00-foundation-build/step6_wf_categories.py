"""Wave 0 workflow #10: category full name, path and ancestor keys (native-catalogue/workflow-nodes.md row 10).

"Products - Category name and path" (create or update of Name / Parent Category): the same shape as #7 units.
Complete Name = parent's + " / " + Name (Odoo _compute_complete_name); Parent Path = parent's + own id + "/";
Ancestor Key 1 = itself, 2..5 = the parent's 1..4 (for the #12 pricelist rule search); a parent that would make a
loop is put back. Then every category below (path contains its id), in path order (a parent's path sorts before
its children's), one at a time, is recomputed from its own parent.
Run: python step6_wf_categories.py
"""
import json
from lib import hap
from wflib import S, F, create_flow, batch_add, node_ids, publish, cond, lit, fld

STEP = 'v2 step 6 (#10)'
K = 'product_category'


def f(a):
    return F(K, a)


def upd(alias, name, target, fields):
    return {'nodeAlias': alias, 'nodeType': 'update_record', 'name': name,
            'config': {'worksheet': S[K], 'target': {'node': target}, 'fields': fields}}


def fx(alias, name, formula):
    return {'nodeAlias': alias, 'nodeType': 'compute', 'name': name,
            'config': {'mode': 'function', 'output_type': 'text', 'formula': formula}}


def recompute(prefix, rec, par):
    anc = [{'fieldId': f('x_product__ancestor_1'), 'value': {'kind': 'field', 'node': rec, 'fieldId': 'rowid'}}] + \
          [{'fieldId': f(f'x_product__ancestor_{i}'), 'value': fld(par, f(f'x_product__ancestor_{i - 1}'))} for i in range(2, 6)]
    return [fx(f'{prefix}cn', 'Complete name', f'CONCAT(${par}-{f("complete_name")}$, " / ", ${rec}-{f("name")}$)'),
            fx(f'{prefix}path', 'Path', f'CONCAT(${par}-{f("parent_path")}$, ${rec}-rowid$, "/")'),
            upd(f'{prefix}w', 'Write name, path, ancestors', rec, [
                {'fieldId': f('complete_name'), 'value': fld(f'{prefix}cn', 'string_fx_id')},
                {'fieldId': f('parent_path'), 'value': fld(f'{prefix}path', 'string_fx_id')},
                {'fieldId': f('x_product__last_valid_parent_id'), 'value': fld(rec, f('parent_id'))}] + anc)]


def build():
    pid = create_flow('Products - Category name and path', 'worksheet', 'product', STEP,
                      'Complete name ("Furniture / Office"), path and ancestor keys from the parent, for the category and '
                      'every category below it; a parent that would make a loop is put back (Odoo product.category).')
    if 'Has parent?' in node_ids(pid)[0]:
        return pid
    top_fields = [
        {'fieldId': f('complete_name'), 'value': fld('trigger', f('name'))},
        {'fieldId': f('parent_path'), 'value': fld('tpath', 'string_fx_id')},
        {'fieldId': f('x_product__ancestor_1'), 'value': {'kind': 'field', 'node': 'trigger', 'fieldId': 'rowid'}},
        {'fieldId': f('x_product__last_valid_parent_id'), 'op': 'clear', 'value': {'kind': 'empty'}}] + \
        [{'fieldId': f(f'x_product__ancestor_{i}'), 'op': 'clear', 'value': {'kind': 'empty'}} for i in range(2, 6)]
    nodes = [
        {'nodeAlias': 'has', 'nodeType': 'branch', 'name': 'Has parent?', 'config': {'mode': 'exclusive', 'paths': [
            {'alias': 'p_par', 'name': 'With a parent',
             'condition': {'logic': 'and', 'items': [cond('trigger', f('name'), 'not_empty')]},   # patched to "is not empty"
             'nodes': [
                 {'nodeAlias': 'par', 'nodeType': 'get_relation', 'name': 'Parent category',
                  'config': {'worksheet': S[K], 'target': {'node': 'trigger'}, 'fields': [{'fieldId': f('parent_id')}]}},
                 {'nodeAlias': 'loop', 'nodeType': 'branch', 'name': 'Loop?', 'config': {'mode': 'exclusive', 'paths': [
                     {'alias': 'p_loop', 'name': 'Would make a loop',
                      'condition': {'logic': 'and', 'items': [
                          {'node': 'par', 'field': f('parent_path'), 'op': 'contains', 'type': 2,
                           'value': {'kind': 'field', 'node': 'trigger', 'fieldId': 'rowid'}}]},
                      'nodes': [upd('back', 'Put the last valid parent back', 'trigger', [
                          {'fieldId': f('parent_id'), 'value': fld('trigger', f('x_product__last_valid_parent_id'))}])]},
                     {'alias': 'p_ok', 'name': 'No loop', 'nodes': recompute('', 'trigger', 'par')}]}}]},
            {'alias': 'p_top', 'name': 'Top category', 'nodes': [
                fx('tpath', 'Path', 'CONCAT("/", $trigger-rowid$, "/")'),
                upd('tw', 'Write name, path, ancestors', 'trigger', top_fields)]}]}},
        {'nodeAlias': 'below', 'nodeType': 'get_multiple', 'name': 'Categories below it',
         'config': {'worksheet': S[K], 'sorts': [{'controlId': f('parent_path'), 'controlType': 2, 'isAsc': True}],
                    'filter': {'logic': 'and', 'items': [
                        {'left': {'node': {'nodeAlias': 'below'}, 'fieldId': f('parent_path')}, 'op': 'contains',
                         'right': {'kind': 'field', 'node': {'nodeAlias': 'trigger'}, 'fieldId': 'rowid'}},
                        {'left': {'node': {'nodeAlias': 'below'}, 'fieldId': 'rowid'}, 'op': 'ne', 'type': 2,
                         'right': {'kind': 'field', 'node': {'nodeAlias': 'trigger'}, 'fieldId': 'rowid'}}]}}},
        {'nodeAlias': 'each', 'nodeType': 'sub_process', 'name': 'Recompute each, top first',
         'config': {'data_source': {'node': 'below'}, 'process': {
             'name': 'Products - recompute one category below', 'data_source': {'node': 'below'}, 'execute_type': 2,
             'wait_complete': True,
             'nodes': [{'nodeAlias': 'spar', 'nodeType': 'get_relation', 'name': 'Its parent',
                        'config': {'worksheet': S[K], 'target': {'node': 'sub_trigger'}, 'fields': [{'fieldId': f('parent_id')}]}}]
                      + recompute('s', 'sub_trigger', 'spar')}}},
    ]
    batch_add(pid, nodes, '--trigger-worksheet', S[K], '--trigger-event', 'create_or_update',
              '--trigger-fields', ','.join([f('name'), f('parent_id')]))
    return pid


def patch(pid):
    """'Has parent?' first path: relation is not empty (stored form; PLATFORM-ISSUES P22)."""
    names, d = node_ids(pid)
    start = d.get('startEventId') or next(k for k, v in d['flowNodeMap'].items() if v.get('typeId') == 0)
    nid = d['flowNodeMap'][names['Has parent?']]['flowIds'][0]
    cond31 = [[{'nodeId': start, 'nodeType': 0, 'appType': 1, 'filedId': f('parent_id'), 'filedTypeId': 29,
                'enumDefault': 1, 'conditionId': '31', 'conditionValues': []}]]
    hap('workflow', 'node', 'save', pid, nid, '--type', '2', '-c', json.dumps({'operateCondition': cond31}))
    hap('workflow', 'node', 'rename', pid, nid, '-n', 'With a parent', ok_fail=True)
    hap('workflow', 'node', 'rename', pid, d['flowNodeMap'][names['Loop?']]['flowIds'][0], '-n', 'Would make a loop', ok_fail=True)


if __name__ == '__main__':
    pid = build()
    patch(pid)
    r = publish(pid)
    print('category flow', pid, 'published' if r.get('isPublish') else json.dumps(r, ensure_ascii=False)[:800])
