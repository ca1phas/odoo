"""Wave 0 workflows #14: activity State from the due date (native-catalogue/workflow-nodes.md §5.5).

A. "Activities - State on save": create or update of Due Date / Active, active activities only ->
   compute today (date mode "+0d", server time UTC+8 = Malaysian time) -> exclusive branch
   Overdue (due < today) / Today (due = today) / Planned (else) -> write State.
B. "Activities - Daily state refresh": every day 00:05 -> compute today -> three batch updates (action 412) for
   the active activities whose State is out of date. Each batch takes up to 1,000 rows; wave 0 volumes are far below.
Run: python step6_wf_activity_state.py
"""
import json
from lib import hap, APP, record
from wflib import S, F, T, option_key, create_flow, batch_add, node_ids, publish, cond, lit

STEP = 'v2 step 6 (#14)'
A = 'mail_activity'


def state(label):
    return lit(option_key(A, 'x_mail__state', label))


def flow_a():
    pid = create_flow('Activities - State on save', 'worksheet', 'mail', STEP,
                      'Sets State (Overdue / Today / Planned) from the due date when an activity is saved (Odoo _compute_state).')
    names, _ = node_ids(pid)
    if 'Today' in names:
        return pid
    today = {'kind': 'field', 'node': 'today', 'fieldId': 'string_fx_id'}
    nodes = [
        {'nodeAlias': 'today', 'nodeType': 'compute', 'name': 'Today',
         'config': {'mode': 'date', 'formula': '+0d', 'output_type': 'date'}},
        {'nodeAlias': 'route', 'nodeType': 'branch', 'name': 'By due date',
         'config': {'mode': 'exclusive', 'paths': [
             {'alias': 'p_over', 'name': 'Overdue',
              'condition': {'logic': 'and', 'items': [cond('trigger', F(A, 'date_deadline'), 'lt', today)]},
              'nodes': [{'nodeAlias': 'w_over', 'nodeType': 'update_record', 'name': 'State Overdue',
                         'config': {'worksheet': S[A], 'target': {'node': 'trigger'},
                                    'fields': [{'fieldId': F(A, 'x_mail__state'), 'value': state('Overdue')}]}}]},
             {'alias': 'p_today', 'name': 'Today',
              'condition': {'logic': 'and', 'items': [cond('trigger', F(A, 'date_deadline'), 'eq', today)]},
              'nodes': [{'nodeAlias': 'w_today', 'nodeType': 'update_record', 'name': 'State Today',
                         'config': {'worksheet': S[A], 'target': {'node': 'trigger'},
                                    'fields': [{'fieldId': F(A, 'x_mail__state'), 'value': state('Today')}]}}]},
             {'alias': 'p_plan', 'name': 'Planned',
              'nodes': [{'nodeAlias': 'w_plan', 'nodeType': 'update_record', 'name': 'State Planned',
                         'config': {'worksheet': S[A], 'target': {'node': 'trigger'},
                                    'fields': [{'fieldId': F(A, 'x_mail__state'), 'value': state('Planned')}]}}]},
         ]}},
    ]
    batch_add(pid, nodes, '--trigger-worksheet', S[A], '--trigger-event', 'create_or_update',
              '--trigger-fields', ','.join([F(A, 'date_deadline'), F(A, 'active')]),
              '--trigger-filter', json.dumps({'logic': 'and', 'items': [cond('trigger', F(A, 'active'), 'checked')]}))
    return pid


if __name__ == "__main__" and "b" not in __import__("sys").argv[1:]:
    pid = flow_a()
    print('flow A', pid, json.dumps(publish(pid), ensure_ascii=False)[:600])


def flow_b():
    """Daily refresh: compute today, then three batch updates (412) for active activities whose State is stale."""
    pid = create_flow('Activities - Daily state refresh', 'scheduled', 'mail', STEP,
                      'Every day at 00:05 Malaysian time: moves active activities to Overdue / Today / Planned.')
    names, _ = node_ids(pid)
    if 'Today' not in names:
        batch_add(pid, [{'nodeAlias': 'today', 'nodeType': 'compute', 'name': 'Today',
                         'config': {'mode': 'date', 'formula': '+0d', 'output_type': 'date'}}],
                  '--trigger-schedule', json.dumps({'repeat': 'day', 'interval': 1, 'start_time': '2026-11-24 00:05'}))
        names, _ = node_ids(pid)
    prev = names['Today']
    today = {'kind': 'field', 'node': names['Today'], 'fieldId': 'date_fx_id'}
    for label, op in (('Overdue', 'lt'), ('Today', 'eq'), ('Planned', 'gt')):
        name = f'Set {label}'
        if name not in names:
            r = hap('workflow', 'node', 'add', pid, '--type', '13', '-n', name, '--after', prev, '-a', '412', '--app-id', S[A])
            names, _ = node_ids(pid)
        nid = names[name]
        hap('workflow', 'node', 'save-get-more', pid, nid, '-a', '412', '--app-id', S[A],
            '-f', json.dumps([{'fieldId': F(A, 'x_mail__state'), 'type': 11, 'fieldValue': option_key(A, 'x_mail__state', label)}]),
            '--condition', json.dumps({'logic': 'and', 'items': [
                {'field': F(A, 'active'), 'op': 'checked'},
                {'field': F(A, 'x_mail__state'), 'op': 'ne', 'value': option_key(A, 'x_mail__state', label)},
                {'field': F(A, 'date_deadline'), 'op': op, 'value': today}]}))
        prev = nid
    return pid


if __name__ == '__main__' and 'b' in __import__('sys').argv[1:]:
    pid = flow_b()
    print('flow B', pid, json.dumps(publish(pid), ensure_ascii=False)[:600])
