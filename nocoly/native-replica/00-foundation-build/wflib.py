"""Helpers for the wave 0 workflows (step 4 of §9): create once, bind the trigger and nodes with batch-add,
publish, record in the ledger. Names start with the owner prefix from register/conventions.json
("Contacts - ", "Units - ", "Products - ", "Activities - ", "Settings - ").

Node specs are hap-cli's high-level `batch-add` DSL (hap guide workflow). Compute results are read as
number_fx_id (numbers) or string_fx_id (text, dates). get_single has no sort in the DSL: add it afterwards with
`node save-search --sorts` (sort_single()).
"""
import json, os, tempfile
from lib import hap, APP, record
from sheetlib import by_alias, sheets_by_alias

HERE = os.path.dirname(os.path.abspath(__file__))
S = {k: v['id'] for k, v in sheets_by_alias().items()}
_F = {}


def F(sheet, alias):
    """Field id by sheet alias and field alias (cached)."""
    if sheet not in _F:
        _F[sheet] = {k: v['controlId'] for k, v in by_alias(S[sheet]).items() if k}
    return _F[sheet][alias]


def T(sheet, alias):
    """Field type by sheet alias and field alias."""
    return by_alias(S[sheet])[alias]['type']


def option_key(sheet, alias, label):
    c = by_alias(S[sheet])[alias]
    return next(o['key'] for o in c['options'] if o['value'] == label)


def flows():
    d = hap('workflow', 'list', APP, '-n', '200')
    d = d.get('data', d) if isinstance(d, dict) else d
    if isinstance(d, dict):
        d = d.get('processes') or d.get('list') or []
    return d or []


def find_flow(name):
    for f in flows():
        if f.get('name') == name:
            return f.get('id') or f.get('processId')
    return None


def create_flow(name, type_, module, step, desc=''):
    """Create the flow unless the ledger already has one with this name; return its process id."""
    from lib import ledger
    for oid, o in ledger()['objects'].items():
        if o['type'] == 'workflow' and o['name'] == name:
            return oid
    d = hap('workflow', 'create', '-n', name, '-a', APP, '--type', type_, *(['-d', desc] if desc else []))
    d = d.get('data', d)
    pid = d.get('id') or d.get('processId')
    record(pid, 'workflow', name, module, step)
    return pid


def batch_add(pid, nodes, *extra):
    fd, p = tempfile.mkstemp(suffix='.json', dir=os.path.join(HERE, 'backups'))
    os.close(fd)
    json.dump(nodes, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
    return hap('workflow', 'node', 'batch-add', pid, '-a', APP, '--nodes', '@' + p, *extra)


def structure(pid):
    return hap('workflow', 'structure', pid)


def node_ids(pid):
    """{node name: node id} from the flow structure."""
    d = hap('workflow', 'node', 'list', pid)
    d = d.get('data', d)
    out = {}
    for nid, n in (d.get('flowNodeMap') or {}).items():
        out.setdefault(n.get('name'), nid)
    return out, d


def publish(pid):
    return hap('workflow', 'publish', pid, ok_fail=True)


def sort_single(pid, node_id, sorts):
    """Sort a get_single node (first record wins): sorts = [(field id, field type, ascending)]."""
    return hap('workflow', 'node', 'save-search', pid, node_id,
               '--sorts', json.dumps([{'controlId': c, 'controlType': t, 'isAsc': a} for c, t, a in sorts]))


def cond(node, field, op, value=None, **kw):
    c = {'node': node, 'field': field, 'op': op}
    if value is not None:
        c['value'] = value
    c.update(kw)
    return c


def fld(node, field_id):
    return {'kind': 'field', 'node': node, 'fieldId': field_id}


def lit(v):
    return {'kind': 'literal', 'value': v}


def set_decimals(pid, node_id, n=6):
    """Function compute nodes are created with 0 decimals ("number": 0) and round their result to an integer
    (PLATFORM-ISSUES P25). Rewrite the node with n decimals."""
    d = hap('workflow', 'node', 'get', pid, node_id, '--type', '9')
    d = d.get('data', d)
    if d.get('number') == n:
        return False
    cfg = {k: d.get(k) for k in ('name', 'actionId', 'formulaValue', 'type', 'execute', 'nullZero') if k in d}
    cfg['number'] = n
    hap('workflow', 'node', 'save', pid, node_id, '--type', '9', '-c', json.dumps(cfg, ensure_ascii=False))
    return True


def inner_flows(pid):
    """Process ids of the sub-processes inside a flow."""
    names, d = node_ids(pid)
    out = []
    for nid, n in (d.get('flowNodeMap') or {}).items():
        if n.get('typeId') == 16:
            s = hap('workflow', 'node', 'get', pid, nid, '--type', '16')
            s = s.get('data', s)
            if s.get('subProcessId'):
                out.append(s['subProcessId'])
    return out


def clear_field(pid, node_name, worksheet, field_id, field_type=2):
    """A DSL "clear" writes "" and the CLI then refuses the step ("none of its field writes were kept", PLATFORM-ISSUES
    P27), also through save-action. The UI stores {"isClear": true, "fieldValue": ""}; write that with a raw node save."""
    names, d = node_ids(pid)
    nid = names[node_name]
    n = hap('workflow', 'node', 'get', pid, nid, '--type', '6')
    n = n.get('data', n)
    cfg = {k: n.get(k) for k in ('name', 'actionId', 'appId', 'appType', 'selectNodeId') if n.get(k) is not None}
    cfg['fields'] = [{'fieldId': field_id, 'type': field_type, 'fieldValue': '', 'fieldValueId': '', 'nodeId': '',
                      'isClear': True, 'addType': 0}]
    hap('workflow', 'node', 'save', pid, nid, '--type', '6', '-c', json.dumps(cfg, ensure_ascii=False))
    n = hap('workflow', 'node', 'get', pid, nid, '--type', '6')
    n = n.get('data', n)
    return [(f.get('fieldId'), f.get('isClear')) for f in n.get('fields') or []]
