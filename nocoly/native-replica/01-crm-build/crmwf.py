"""Workflow helpers for the CRM flows (step 3): field shortcuts, filter items, and the raw patches the CLI DSL cannot
write itself (relation empty / not empty, PLATFORM-ISSUES P22; clearing a field, P27; path names, P23).

Stored condition rules (Mingdao flow): operateCondition is a list of OR-groups, each a list of AND-ed conditions.
Relation "is not empty" = conditionId 31, "is empty" = 32. A condition names its node by nodeId / nodeType / appType.
"""
import json
from crmlib import *  # noqa: F401,F403
from crmlib import unwrap

L, TM, SG, C, K, A, PL = 'crm_lead', 'crm_team', 'crm_stage', 'res_partner', 'res_country', 'mail_activity', 'x_mail__plan_launch'
NOW = {'kind': 'systemField', 'fieldId': 'nowTime'}


def l(a):
    return F(L, a)


def t(a):
    return F(TM, a)


def g(a):
    return F(SG, a)


def c(a):
    return F(C, a)


def ref(node, fid):
    """Value / condition reference to a column of another step (conditions and writes)."""
    return {'kind': 'field', 'node': node, 'fieldId': fid}


def rec(node):
    return {'kind': 'record', 'node': node}


def fi(q, fid, op, right=None, type_=None):
    """One query-filter item: column `fid` of the queried sheet (step `q` itself) against `right`."""
    it = {'left': {'node': {'nodeAlias': q}, 'fieldId': fid}, 'op': op}
    if right is not None:
        it['right'] = right
    if type_ is not None:
        it['type'] = type_
    return it


def fref(node, fid):
    """Right side of a query-filter item: a column of another step."""
    return {'kind': 'field', 'node': {'nodeAlias': node}, 'fieldId': fid}


def upd(alias, name, fields, sheet=L, target='trigger'):
    return {'nodeAlias': alias, 'nodeType': 'update_record', 'name': name,
            'config': {'worksheet': S[sheet], 'target': {'node': target}, 'fields': fields}}


def single(alias, name, sheet, items, logic='and', if_empty=True):
    cfg = {'worksheet': S[sheet], 'filter': {'logic': logic, 'items': items}}
    if if_empty:
        cfg['ifEmpty'] = 'continue'
    return {'nodeAlias': alias, 'nodeType': 'get_single', 'name': name, 'config': cfg}


def fresh(alias, name='The record, fresh', sheet=L):
    return single(alias, name, sheet, [fi(alias, 'rowid', 'eq', fref('trigger', 'rowid'), 2)], if_empty=False)


def relation(alias, name, sheet, field_id, source='trigger'):
    return {'nodeAlias': alias, 'nodeType': 'get_relation', 'name': name,
            'config': {'worksheet': S[sheet], 'target': {'node': source}, 'fields': [{'fieldId': field_id}]}}


def branch(alias, name, paths, result=False):
    cfg = {'paths': paths}
    if result:
        cfg['result_branch'] = True
    else:
        cfg['mode'] = 'exclusive'
    return {'nodeAlias': alias, 'nodeType': 'branch', 'name': name, 'config': cfg}


def path(alias, name, nodes, items=None, logic='and', result_type=None):
    p = {'alias': alias, 'name': name, 'nodes': nodes}
    if items:
        p['condition'] = {'logic': logic, 'items': items}
    if result_type:
        p['result_type'] = result_type
    return p


# ---- reading a built flow -------------------------------------------------------------------------------------------

def flow_map(pid):
    names, d = node_ids(pid)
    return names, d['flowNodeMap'], d.get('startEventId') or next(k for k, v in d['flowNodeMap'].items() if v.get('typeId') == 0)


def node_get(pid, nid, type_):
    return unwrap(hap('workflow', 'node', 'get', pid, nid, '--type', str(type_)))


def gateway_paths(pid, gateway):
    names, m, _ = flow_map(pid)
    return m[names[gateway]]['flowIds']


def name_paths(pid, gateway, labels):
    """batch-add drops the names of paths with a condition (P23)."""
    names, m, _ = flow_map(pid)
    for pth, label in zip(m[names[gateway]]['flowIds'], labels):
        if label and m[pth].get('name') != label:
            hap('workflow', 'node', 'rename', pid, pth, '-n', label, ok_fail=True)


# ---- raw relation conditions ------------------------------------------------------------------------------------------

def rel_cond(like, field_id, empty, multi=False):
    """A stored relation empty / not-empty condition on the same step as the stored condition `like`."""
    out = {k: like[k] for k in ('nodeId', 'nodeType', 'appType', 'nodeName', 'actionId') if k in like}
    out.update({'filedId': field_id, 'filedTypeId': 29, 'enumDefault': 2 if multi else 1,
                'conditionId': '32' if empty else '31', 'conditionValues': [], 'sourceType': 0})
    return out


def rel_cond_on(node_id, node_type, field_id, empty, multi=False, app_type=1):
    return {'nodeId': node_id, 'nodeType': node_type, 'appType': app_type, 'filedId': field_id, 'filedTypeId': 29,
            'enumDefault': 2 if multi else 1, 'conditionId': '32' if empty else '31', 'conditionValues': [], 'sourceType': 0}


def path_condition(pid, pth):
    """A path's stored condition is in the flow map entry (node get returns it under another key)."""
    return flow_map(pid)[1][pth].get('operateCondition') or []


def patch_path(pid, gateway, idx, build):
    """Rewrite the condition of path `idx` of `gateway`. build(groups) gets the stored OR-groups (the DSL placeholder
    included) and returns the new ones."""
    pth = gateway_paths(pid, gateway)[idx]
    groups = build([list(gr) for gr in path_condition(pid, pth)])
    hap('workflow', 'node', 'save', pid, pth, '--type', '2', '-c', json.dumps({'operateCondition': groups}, ensure_ascii=False))
    back = path_condition(pid, pth)
    ids = lambda gs: [[(x.get('filedId'), str(x.get('conditionId'))) for x in gr] for gr in gs]
    if ids(back) != ids(groups):
        raise RuntimeError(f'path {gateway}[{idx}] not saved as sent: {ids(back)} != {ids(groups)}')
    return back


def patch_trigger(pid, build):
    """Rewrite the trigger condition (start node). The step's own settings are sent back unchanged."""
    names, m, sid = flow_map(pid)
    n = node_get(pid, sid, 0)
    cfg = {k: n.get(k) for k in ('name', 'desc', 'appId', 'appType', 'triggerId', 'assignFieldIds') if n.get(k) is not None}
    cfg['operateCondition'] = build(sid, [list(gr) for gr in (n.get('operateCondition') or [])])
    hap('workflow', 'node', 'save', pid, sid, '--type', '0', '-c', json.dumps(cfg, ensure_ascii=False))
    back = node_get(pid, sid, 0)
    keep = {k: back.get(k) for k in ('appId', 'triggerId', 'assignFieldIds')}
    if keep != {k: n.get(k) for k in ('appId', 'triggerId', 'assignFieldIds')}:
        raise RuntimeError(f'trigger settings changed by the save: {keep}')
    return back.get('operateCondition')


def query_conditions(pid, node_name):
    """The stored filter of a get_single / query step (for raw patches)."""
    names, m, _ = flow_map(pid)
    nid = names[node_name]
    return nid, m[nid].get('typeId'), node_get(pid, nid, m[nid].get('typeId'))


QUERY_KEYS = ('actionId', 'appId', 'conditions', 'destroy', 'execute', 'executeType', 'fields', 'filters', 'findFields',
              'ignoreError', 'link', 'name', 'operateCondition', 'random', 'returnNew', 'selectNodeId', 'sorts')


def save_query(pid, nid, type_, n, **changes):
    """A whole-step save clears every setting it does not name: send all of a query step's own settings back."""
    cfg = {k: n.get(k) for k in QUERY_KEYS if n.get(k) is not None}
    cfg.update(changes)
    hap('workflow', 'node', 'save', pid, nid, '--type', str(type_), '-c', json.dumps(cfg, ensure_ascii=False))
    return node_get(pid, nid, type_)


def sort_by(pid, node_name, sorts):
    """sorts = [(field id, field type, ascending)]."""
    names, m, _ = flow_map(pid)
    return hap('workflow', 'node', 'save-search', pid, names[node_name],
               '--sorts', json.dumps([{'controlId': f, 'controlType': ty, 'isAsc': a} for f, ty, a in sorts]))


#: Output units of a date-difference step as the product numbers them (the designer's list: Year, Month, Day, Hour,
#: Minute, Second). hap-cli 0.9.14 numbers them differently (minute 1, hour 2, ...), so its "hour" is stored as Month
#: and the result is 0 (PLATFORM-ISSUES P42). Day happens to agree (3).
DATE_DIFF_UNITS = {'year': 1, 'month': 2, 'day': 3, 'hour': 4, 'minute': 5, 'second': 6}
COMPUTE_KEYS = ('actionId', 'endTime', 'execute', 'formulaMap', 'formulaValue', 'isException', 'name', 'nullZero', 'number',
                'outUnit', 'startTime', 'type')


def save_compute(pid, node_name, **changes):
    """Re-save a compute step with all its own settings plus the changes (a whole-step save clears what it does not name)."""
    names, m, _ = flow_map(pid)
    nid = names[node_name]
    n = node_get(pid, nid, 9)
    cfg = {k: n.get(k) for k in COMPUTE_KEYS if n.get(k) is not None}
    cfg.update(changes)
    hap('workflow', 'node', 'save', pid, nid, '--type', '9', '-c', json.dumps(cfg, ensure_ascii=False))
    back = node_get(pid, nid, 9)
    lost = [k for k in cfg if back.get(k) in (None, '') and cfg[k] not in (None, '')]
    wrong = [k for k in changes if back.get(k) != changes[k]]
    if lost or wrong:
        raise RuntimeError(f'{node_name}: lost {lost}, not kept {wrong}')
    return back


#: On a multi-record relation, "equals" (9) / "not equal to" (10) compare the whole set: a stage of two teams does not
#: "equal" one of them. Odoo's `team_ids = team` means "the teams include it", which is "is any of" (33) / "is none of"
#: (34) in the designer's list (found with acceptance test 15d, 24 Nov 2026).
MULTI_REL_OPS = {'9': '33', '10': '34'}


def _multi_rel_fix(conds):
    n = 0
    for c in conds:
        if c.get('filedTypeId') == 29 and c.get('enumDefault') == 2 and str(c.get('conditionId')) in MULTI_REL_OPS:
            c['conditionId'] = MULTI_REL_OPS[str(c['conditionId'])]
            n += 1
    return n


def multi_relation_any(pid):
    """Turn "equals" on a multi-record relation into "is any of" in every query step and branch path of a flow."""
    names, m, _ = flow_map(pid)
    changed = []
    for nid, node in m.items():
        if node.get('typeId') == 7:
            n = node_get(pid, nid, 7)
            groups = [g['conditions'][0] for g in (n.get('filters') or []) if g.get('conditions')] + list(n.get('conditions') or [])
            if sum(_multi_rel_fix(gr) for gr in groups):
                save_query(pid, nid, 7, n)
                changed.append(node.get('name'))
        elif node.get('typeId') == 2 and node.get('operateCondition'):
            groups = [list(gr) for gr in node['operateCondition']]
            if sum(_multi_rel_fix(gr) for gr in groups):
                hap('workflow', 'node', 'save', pid, nid, '--type', '2', '-c', json.dumps({'operateCondition': groups}, ensure_ascii=False))
                changed.append(node.get('name'))
    return changed


def group_filters(pid):
    """Move the OR groups of every "get single record from a worksheet" step into the grouped filter slot.

    The CLI writes a get_single filter in the old single-condition slot (`conditions`). With two or more OR groups
    there, the editor shows them correctly but the engine ignores the whole filter and returns the first record by
    the sort (found 24 Nov 2026: the Won button picked New; PLATFORM-ISSUES P41). The product's own switch ("Use the
    supported and/or combined filters") makes each OR group its own filter group, spliceType 2; this does the same.
    Returns the names of the steps changed."""
    names, m, _ = flow_map(pid)
    changed = []
    for nid, node in m.items():
        if node.get('typeId') != 7:
            continue
        n = node_get(pid, nid, 7)
        groups = n.get('conditions') or []
        if str(n.get('actionId')) != '406' or len(groups) < 2:
            continue
        back = save_query(pid, nid, 7, n, conditions=[], filters=[{'spliceType': 2, 'conditions': [g]} for g in groups])
        if back.get('conditions') or len(back.get('filters') or []) != len(groups) or back.get('sorts') != n.get('sorts'):
            raise RuntimeError(f"{node.get('name')}: grouped filter or sort not kept")
        changed.append(node.get('name'))
    return changed
