"""Wave 0 workflow #7: unit factor, path and level (native-catalogue/workflow-nodes.md §5.1).

"Units - Factor and path" (create or update of Contains / Reference Unit):
- with a reference unit: read it fresh; if its path already holds this unit, a loop -> put the last valid reference
  unit back; else factor = Contains x reference factor, path = reference path + own id + "/", level + 1;
- without: factor = Contains, path = "/id/", level 1;
- then every unit below it (path contains its id), level by level, one at a time, recomputes from its own
  reference unit (no recursion needed; Odoo stores parent_path the same way).
Function results are string_fx_id (numbers too, as the UI stores them; PLATFORM-ISSUES P21). The record id is
`rowid`. The PBP "Units - Convert quantity" (<id>) was built and checked by hand (see BUILD-LOG).
Run: python step6_wf_units.py
"""
import json
from lib import hap
from wflib import S, F, create_flow, batch_add, node_ids, publish, cond, lit, fld

STEP = 'v2 step 6 (#7)'
U = 'uom_uom'


def f(a):
    return F(U, a)


def upd(alias, name, target, fields):
    return {'nodeAlias': alias, 'nodeType': 'update_record', 'name': name,
            'config': {'worksheet': S[U], 'target': {'node': target}, 'fields': fields}}


def fx(alias, name, formula):
    return {'nodeAlias': alias, 'nodeType': 'compute', 'name': name,
            'config': {'mode': 'function', 'output_type': 'text', 'formula': formula}}


def recompute(prefix, rec, ref):
    """Nodes that recompute `rec` from its reference unit `ref` (already read)."""
    return [fx(f'{prefix}fac', 'Absolute quantity', f'$${rec}-{f("relative_factor")}$ * $${ref}-{f("factor")}$'.replace('$$', '$')),
            fx(f'{prefix}path', 'Path', f'CONCAT(${ref}-{f("parent_path")}$, ${rec}-rowid$, "/")'),
            fx(f'{prefix}lvl', 'Level', f'${ref}-{f("x_uom__level")}$ + 1'),
            upd(f'{prefix}w', 'Write factor, path, level', rec, [
                {'fieldId': f('factor'), 'value': fld(f'{prefix}fac', 'string_fx_id')},
                {'fieldId': f('parent_path'), 'value': fld(f'{prefix}path', 'string_fx_id')},
                {'fieldId': f('x_uom__level'), 'value': fld(f'{prefix}lvl', 'string_fx_id')},
                {'fieldId': f('x_uom__last_valid_uom_id'), 'value': fld(rec, f('relative_uom_id'))}])]


def build():
    pid = create_flow('Units - Factor and path', 'worksheet', 'uom', STEP,
                      'Absolute quantity, path and level from the reference unit, for the unit and every unit below it; '
                      'a reference that would make a loop is put back (Odoo uom.uom factor and parent_path).')
    if 'Has reference unit?' in node_ids(pid)[0]:
        return pid
    nodes = [
        {'nodeAlias': 'has', 'nodeType': 'branch', 'name': 'Has reference unit?', 'config': {'mode': 'exclusive', 'paths': [
            {'alias': 'p_ref', 'name': 'With a reference unit',
             'condition': {'logic': 'and', 'items': [cond('trigger', f('name'), 'not_empty')]},   # patched to "is not empty"
             'nodes': [
                 {'nodeAlias': 'ref', 'nodeType': 'get_relation', 'name': 'Reference unit',
                  'config': {'worksheet': S[U], 'target': {'node': 'trigger'}, 'fields': [{'fieldId': f('relative_uom_id')}]}},
                 {'nodeAlias': 'loop', 'nodeType': 'branch', 'name': 'Loop?', 'config': {'mode': 'exclusive', 'paths': [
                     {'alias': 'p_loop', 'name': 'Would make a loop',
                      'condition': {'logic': 'and', 'items': [
                          {'node': 'ref', 'field': f('parent_path'), 'op': 'contains', 'type': 2,
                           'value': {'kind': 'field', 'node': 'trigger', 'fieldId': 'rowid'}}]},
                      'nodes': [upd('back', 'Put the last valid reference back', 'trigger', [
                          {'fieldId': f('relative_uom_id'), 'value': fld('trigger', f('x_uom__last_valid_uom_id'))}])]},
                     {'alias': 'p_ok', 'name': 'No loop', 'nodes': recompute('', 'trigger', 'ref')}]}}]},
            {'alias': 'p_top', 'name': 'Top unit', 'nodes': [
                fx('tpath', 'Path', 'CONCAT("/", $trigger-rowid$, "/")'),
                upd('tw', 'Write factor, path, level', 'trigger', [
                    {'fieldId': f('factor'), 'value': fld('trigger', f('relative_factor'))},
                    {'fieldId': f('parent_path'), 'value': fld('tpath', 'string_fx_id')},
                    {'fieldId': f('x_uom__level'), 'value': lit('1')},
                    {'fieldId': f('x_uom__last_valid_uom_id'), 'op': 'clear', 'value': {'kind': 'empty'}}])]}]}},
        {'nodeAlias': 'below', 'nodeType': 'get_multiple', 'name': 'Units below it',
         'config': {'worksheet': S[U], 'sorts': [{'controlId': f('x_uom__level'), 'controlType': 6, 'isAsc': True}],
                    'filter': {'logic': 'and', 'items': [
                        {'left': {'node': {'nodeAlias': 'below'}, 'fieldId': f('parent_path')}, 'op': 'contains',
                         'right': {'kind': 'field', 'node': {'nodeAlias': 'trigger'}, 'fieldId': 'rowid'}},
                        {'left': {'node': {'nodeAlias': 'below'}, 'fieldId': 'rowid'}, 'op': 'ne', 'type': 2,
                         'right': {'kind': 'field', 'node': {'nodeAlias': 'trigger'}, 'fieldId': 'rowid'}}]}}},
        {'nodeAlias': 'each', 'nodeType': 'sub_process', 'name': 'Recompute each, top first',
         'config': {'data_source': {'node': 'below'}, 'process': {
             'name': 'Units - recompute one unit below', 'data_source': {'node': 'below'}, 'execute_type': 2, 'wait_complete': True,
             'nodes': [{'nodeAlias': 'sref', 'nodeType': 'get_relation', 'name': 'Its reference unit',
                        'config': {'worksheet': S[U], 'target': {'node': 'sub_trigger'},
                                   'fields': [{'fieldId': f('relative_uom_id')}]}}] + recompute('s', 'sub_trigger', 'sref')}}},
    ]
    batch_add(pid, nodes, '--trigger-worksheet', S[U], '--trigger-event', 'create_or_update',
              '--trigger-fields', ','.join([f('relative_factor'), f('relative_uom_id')]))
    return pid


def patch(pid):
    """'Has reference unit?' first path: relation is not empty (stored form; PLATFORM-ISSUES P22)."""
    names, d = node_ids(pid)
    start = d.get('startEventId') or next(k for k, v in d['flowNodeMap'].items() if v.get('typeId') == 0)
    gw = d['flowNodeMap'][names['Has reference unit?']]
    nid = gw['flowIds'][0]
    cond31 = [[{'nodeId': start, 'nodeType': 0, 'appType': 1, 'filedId': f('relative_uom_id'), 'filedTypeId': 29,
                'enumDefault': 1, 'conditionId': '31', 'conditionValues': []}]]
    hap('workflow', 'node', 'save', pid, nid, '--type', '2', '-c', json.dumps({'operateCondition': cond31}))
    hap('workflow', 'node', 'rename', pid, nid, '-n', 'With a reference unit', ok_fail=True)
    lg = d['flowNodeMap'][names['Loop?']]
    hap('workflow', 'node', 'rename', pid, lg['flowIds'][0], '-n', 'Would make a loop', ok_fail=True)


if __name__ == '__main__':
    pid = build()
    patch(pid)
    r = publish(pid)
    print('units flow', pid, 'published' if r.get('isPublish') else json.dumps(r, ensure_ascii=False)[:800])
