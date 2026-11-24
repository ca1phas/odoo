"""Wave 0 workflow #13: currency conversion and current rates (native-catalogue/workflow-nodes.md §5.4).

PBP "Settings - Convert amount" (inputs Amount, From Currency, To Currency, Date): rate of each currency on or before
the date, else its earliest rate, else 1 (Odoo _get_rates); amount x rate(to) / rate(from), rounded to the target
currency's rounding (Odoo _convert). Rates are per 1 unit of the company currency MYR (rebased 23 Nov 2026).
"Settings - Current rate on change" (rate create or update) and "Settings - Daily current rates" (00:05): the
currency's Current Rate, Inverse Rate and Last Rate Update = its latest rate dated today or earlier.
Run: python step6_wf_currency.py [pbp] [change] [delete] [daily]
"""
import json, secrets, sys
from lib import hap, APP
from wflib import S, F, create_flow, batch_add, node_ids, publish, cond, lit, fld, sort_single

STEP = 'v2 step 6 (#13)'
R, CUR = 'res_currency_rate', 'res_currency'
TODAY = {'nodeAlias': 'today', 'nodeType': 'compute', 'name': 'Today',
         'config': {'mode': 'date', 'formula': '+0d', 'output_type': 'date'}}


def rate_query(alias, name, currency_ref, date_ref=None):
    items = [{'left': {'node': {'nodeAlias': alias}, 'fieldId': F(R, 'currency_id')}, 'op': 'eq', 'right': currency_ref}]
    if date_ref:
        items.append({'left': {'node': {'nodeAlias': alias}, 'fieldId': F(R, 'name')}, 'op': 'lte', 'right': date_ref})
    return {'nodeAlias': alias, 'nodeType': 'get_single', 'name': name,
            'config': {'worksheet': S[R], 'execute_type': 2, 'filter': {'logic': 'and', 'items': items}}}


def pbp():
    pid = create_flow('Settings - Convert amount', 'pbp', 'base', STEP,
                      'Shared function: converts an amount between currencies on a date (Odoo res.currency _convert).')
    names, d = node_ids(pid)
    start = d.get('startEventId') or names['PBP']
    s = hap('workflow', 'node', 'get', pid, start, '--type', '0'); s = s.get('data', s)
    if not s.get('controls'):
        batch_add(pid, [], '--trigger-pbp', json.dumps({'inputs': [
            {'name': 'Amount', 'type': 'number', 'required': True, 'alias': 'amount'},
            {'name': 'From Currency', 'type': 'text', 'required': True, 'alias': 'from_currency', 'desc': 'Record id in Currencies.'},
            {'name': 'To Currency', 'type': 'text', 'required': True, 'alias': 'to_currency', 'desc': 'Record id in Currencies.'},
            {'name': 'Date', 'type': 'date', 'required': True, 'alias': 'date', 'desc': 'Rate date: the latest rate on or before it.'}]}))
        s = hap('workflow', 'node', 'get', pid, start, '--type', '0'); s = s.get('data', s)
    inp = {c['alias']: c['controlId'] for c in s['controls']}
    if 'Converted amount' not in names:
        tr = lambda k: {'kind': 'field', 'node': {'nodeAlias': 'trigger'}, 'fieldId': inp[k]}
        rate = F(R, 'rate')
        pick = lambda a, b: f'IF(ISBLANK(${a}-{rate}$), IF(ISBLANK(${b}-{rate}$), 1, ${b}-{rate}$), ${a}-{rate}$)'
        x = f'$trigger-{inp["amount"]}$ * {pick("rt", "rt0")} / {pick("rf", "rf0")}'
        rnd = f'IF(ISBLANK($cur-{F(CUR, "rounding")}$), 0.01, $cur-{F(CUR, "rounding")}$)'
        nodes = [rate_query('rf', 'From rate on the date', tr('from_currency'), tr('date')),
                 rate_query('rf0', 'From earliest rate', tr('from_currency')),
                 rate_query('rt', 'To rate on the date', tr('to_currency'), tr('date')),
                 rate_query('rt0', 'To earliest rate', tr('to_currency')),
                 {'nodeAlias': 'cur', 'nodeType': 'get_single', 'name': 'To currency',
                  'config': {'worksheet': S[CUR], 'execute_type': 2, 'filter': {'logic': 'and', 'items': [
                      {'left': {'node': {'nodeAlias': 'cur'}, 'fieldId': 'rowid'}, 'op': 'eq', 'type': 2, 'right': tr('to_currency')}]}}},
                 {'nodeAlias': 'res', 'nodeType': 'compute', 'name': 'Converted amount',
                  'config': {'mode': 'function', 'output_type': 'number', 'formula': f'ROUND(({x}) / {rnd}, 0) * {rnd}'}}]
        batch_add(pid, nodes, '--after', start)
        names, d = node_ids(pid)
    date_f = F(R, 'name')
    sort_single(pid, names['From rate on the date'], [(date_f, 15, False)])
    sort_single(pid, names['To rate on the date'], [(date_f, 15, False)])
    sort_single(pid, names['From earliest rate'], [(date_f, 15, True)])
    sort_single(pid, names['To earliest rate'], [(date_f, 15, True)])
    out = names['Output Parameters']
    o = hap('workflow', 'node', 'get', pid, out, '--type', '20'); o = o.get('data', o)
    vid = (o.get('subProcessVariables') or [{}])[0].get('controlId') or secrets.token_hex(12)
    res = names['Converted amount']
    hap('workflow', 'node', 'save', pid, out, '--type', '20', '-c', json.dumps({
        'name': 'Output Parameters', 'actionId': '502',
        'subProcessVariables': [{'controlId': vid, 'controlName': 'Amount', 'type': 6, 'dataSource': '', 'options': [],
                                 'required': False, 'enumDefault': 0, 'enumDefault2': 0, 'fieldPermission': '2', 'dot': 2,
                                 'hide': False, 'attribute': 0, 'sourceControlType': 0, 'unit': '', 'processVariableType': 2,
                                 'originalType': 0, 'alias': 'amount'}],
        'fields': [{'fieldId': vid, 'fieldName': 'Amount', 'type': 6, 'nodeId': res, 'sureNodeId': res, 'nodeTypeId': 9,
                    'nodeActionId': '106', 'nodeAppType': 11, 'fieldValueId': 'string_fx_id', 'fieldValueType': '6',
                    'fieldValueName': 'Result', 'fieldValue': '', 'sourceType': 0, 'addType': 0}]}))
    return pid


def current_rate_nodes(prefix, cur_node):
    """Nodes that set `cur_node` (a currency record) from its latest rate dated today or earlier."""
    rate = F(R, 'rate')
    q = rate_query(f'{prefix}latest', 'Latest rate up to today', {'kind': 'record', 'node': {'nodeAlias': cur_node}}
                   if False else {'kind': 'field', 'node': {'nodeAlias': cur_node}, 'fieldId': 'rowid'},
                   {'kind': 'field', 'node': {'nodeAlias': f'{prefix}today'}, 'fieldId': 'date_fx_id'})
    return [dict(TODAY, nodeAlias=f'{prefix}today'), q,
            {'nodeAlias': f'{prefix}inv', 'nodeType': 'compute', 'name': 'Inverse rate',
             'config': {'mode': 'function', 'output_type': 'number', 'formula': f'1 / ${prefix}latest-{rate}$'}},
            {'nodeAlias': f'{prefix}w', 'nodeType': 'update_record', 'name': 'Current rate on the currency',
             'config': {'worksheet': S[CUR], 'target': {'node': cur_node}, 'fields': [
                 {'fieldId': F(CUR, 'rate'), 'value': fld(f'{prefix}latest', rate)},
                 {'fieldId': F(CUR, 'inverse_rate'), 'value': fld(f'{prefix}inv', 'string_fx_id')},
                 {'fieldId': F(CUR, 'rate_date'), 'value': fld(f'{prefix}latest', F(R, 'name'))}]}}]


def on_change():
    pid = create_flow('Settings - Current rate on change', 'worksheet', 'base', STEP,
                      'A new or changed rate updates its currency\'s Current Rate, Inverse Rate and Last Rate Update.')
    names, _ = node_ids(pid)
    if 'The currency' not in names:
        nodes = [{'nodeAlias': 'cur', 'nodeType': 'get_relation', 'name': 'The currency',
                  'config': {'worksheet': S[CUR], 'target': {'node': 'trigger'}, 'fields': [{'fieldId': F(R, 'currency_id')}]}}] \
            + current_rate_nodes('', 'cur')
        batch_add(pid, nodes, '--trigger-worksheet', S[R], '--trigger-event', 'create_or_update',
                  '--trigger-fields', ','.join([F(R, 'name'), F(R, 'rate'), F(R, 'currency_id')]))
        names, _ = node_ids(pid)
    sort_single(pid, names['Latest rate up to today'], [(F(R, 'name'), 15, False)])
    return pid


def on_delete():
    pid = create_flow('Settings - Current rate on delete', 'worksheet', 'base', STEP,
                      'A deleted rate makes its currency take its latest remaining rate dated today or earlier.')
    names, _ = node_ids(pid)
    if 'The currency' not in names:
        nodes = [{'nodeAlias': 'cur', 'nodeType': 'get_relation', 'name': 'The currency',
                  'config': {'worksheet': S[CUR], 'target': {'node': 'trigger'}, 'fields': [{'fieldId': F(R, 'currency_id')}]}}]             + current_rate_nodes('', 'cur')
        batch_add(pid, nodes, '--trigger-worksheet', S[R], '--trigger-event', 'delete')
        names, _ = node_ids(pid)
    sort_single(pid, names['Latest rate up to today'], [(F(R, 'name'), 15, False)])
    from wflib import set_decimals
    set_decimals(pid, names['Inverse rate'], 6)
    return pid


def daily():
    pid = create_flow('Settings - Daily current rates', 'scheduled', 'base', STEP,
                      'Every day at 00:05: each active currency takes its latest rate dated today or earlier.')
    names, _ = node_ids(pid)
    if 'Active currencies' not in names:
        nodes = [{'nodeAlias': 'curs', 'nodeType': 'get_multiple', 'name': 'Active currencies',
                  'config': {'worksheet': S[CUR], 'filter': {'logic': 'and', 'items': [
                      {'left': {'node': {'nodeAlias': 'curs'}, 'fieldId': F(CUR, 'active')}, 'op': 'checked'}]}}},
                 {'nodeAlias': 'each', 'nodeType': 'sub_process', 'name': 'Each currency',
                  'config': {'data_source': {'node': 'curs'}, 'process': {
                      'name': 'Settings - current rate of one currency', 'data_source': {'node': 'curs'}, 'execute_type': 3,
                      'wait_complete': True, 'nodes': current_rate_nodes('s', 'sub_trigger')}}}]
        batch_add(pid, nodes, '--trigger-schedule', json.dumps({'repeat': 'day', 'interval': 1, 'start_time': '2026-11-24 00:05'}))
        names, _ = node_ids(pid)
    sub = hap('workflow', 'node', 'get', pid, names['Each currency'], '--type', '16'); sub = sub.get('data', sub)
    inner = sub.get('subProcessId')
    inames, _ = node_ids(inner)
    sort_single(inner, inames['Latest rate up to today'], [(F(R, 'name'), 15, False)])
    return pid


if __name__ == '__main__':
    todo = sys.argv[1:] or ['pbp', 'change', 'daily']
    for name, fn in (('pbp', pbp), ('change', on_change), ('delete', on_delete), ('daily', daily)):
        if name in todo:
            pid = fn()
            r = publish(pid)
            print(name, pid, 'published' if r.get('isPublish') else json.dumps(r, ensure_ascii=False)[:700])
