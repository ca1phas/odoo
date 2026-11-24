"""Wave 0 workflows #15 and #16 (native-catalogue/workflow-nodes.md §5.6), plus the "Rebuild Variants" button.

Buttons (custom actions) and the flows behind them:
- Activities "Mark Done" (dialog: Feedback): Active off (Odoo archives done activities), State Done, Done Date, Done By.
- Activities "Done & Schedule Next" (dialog: Feedback, Next Activity Type, Next Due Date, Next Summary): as Mark Done,
  then a new activity for the same person and record. Empty choices fall back as in Odoo 20: the type's suggested
  next activity, its schedule (days / weeks / months after the deadline or after today), its default summary.
- Contacts "Launch Plan" (dialog: a new Plan Launch: plan, plan date, who gets "Ask at launch" steps).
  "Activities - Launch plan" (Plan Launches create): refuses a plan with "Ask at launch" steps when nobody is chosen;
  otherwise one activity per step (due = plan date +/- interval; Specific User or the chosen person), then Done.
- Products "Rebuild Variants": adds a Variant Request.
Run: python step6_wf_activity_buttons.py
"""
import json
from lib import hap, APP, record, ledger
from wflib import S, F, batch_add, node_ids, publish, cond, lit, fld, option_key, set_decimals

STEP = 'v2 step 6 (#15, #16)'
A, T, PL, ST, L, C, P, Q = ('mail_activity', 'mail_activity_type', 'mail_activity_plan', 'mail_activity_plan_template',
                            'x_mail__plan_launch', 'res_partner', 'product_template', 'x_product__variant_queue')
PARAM = '<id>'
TODAY = {'nodeAlias': 'today', 'nodeType': 'compute', 'name': 'Today', 'config': {'mode': 'date', 'formula': '+0d', 'output_type': 'date'}}
TODAY_REF = {'kind': 'field', 'node': 'today', 'fieldId': 'date_fx_id'}


def a(f):
    return F(A, f)


def button(sheet, name, spec, module):
    """Create the button once (ledger); return (button id, process id)."""
    for oid, o in ledger()['objects'].items():
        if o['type'] == 'button' and o['name'] == f'{sheet}.{name}':
            return oid, o['note'].split('process ')[-1]
    r = hap('worksheet', 'create-custom-action', S[sheet], '-a', APP, '--action-spec', json.dumps(dict(spec, name=name), ensure_ascii=False))
    r = r.get('data', r)
    btn, pid = r.get('btnId') or r.get('actionId') or r.get('id'), r.get('processId')
    record(btn, 'button', f'{sheet}.{name}', module, f'{STEP}; process {pid}')
    record(pid, 'workflow', f'{sheet}.{name} (button flow)', module, STEP)
    return btn, pid


def done_fields():
    return [{'fieldId': a('active'), 'value': lit('0')},
            {'fieldId': a('x_mail__state'), 'value': lit(option_key(A, 'x_mail__state', 'Done'))},
            {'fieldId': a('date_done'), 'value': TODAY_REF},
            {'fieldId': a('x_mail__done_by'), 'value': {'kind': 'systemField', 'fieldId': 'triggeraid'}}]


def mark_done():
    btn, pid = button(A, 'Mark Done', {'type': 'updateCurrentRecord', 'updateFields': [a('feedback')], 'runWorkflowAfterSubmit': True,
                                       'enableWhen': {'logic': 'and', 'items': [{'field': a('active'), 'op': 'eq', 'value': '1'}]}}, 'mail')
    if 'Done' not in node_ids(pid)[0]:
        batch_add(pid, [TODAY, {'nodeAlias': 'w', 'nodeType': 'update_record', 'name': 'Done', 'config': {
            'worksheet': S[A], 'target': {'node': 'trigger'}, 'fields': done_fields()}}])
    return pid


def done_and_next():
    btn, pid = button(A, 'Done & Schedule Next', {
        'type': 'updateCurrentRecord', 'runWorkflowAfterSubmit': True,
        'updateFields': [a('feedback'), a('x_mail__next_type_id'), a('x_mail__next_date'), a('x_mail__next_summary')],
        'enableWhen': {'logic': 'and', 'items': [{'field': a('active'), 'op': 'eq', 'value': '1'}]}}, 'mail')
    names, d = node_ids(pid)
    if 'Next activity' in names:
        return pid
    t = lambda f: F(T, f)
    z = lambda node, f: f'IF(ISBLANK(${node}-{f}$), 0, ${node}-{f}$)'
    unit = f'CONCAT($nt-{t("delay_unit")}$, "")'
    offset = f'CONCAT("+", IF({unit}=="weeks", {z("nt", t("delay_count"))} * 7, {z("nt", t("delay_count"))}), IF({unit}=="months", "M", "d"))'
    base = f'IF(CONCAT($nt-{t("delay_from")}$, "")=="after previous activity completion date", $today-date_fx_id$, $trigger-{a("date_deadline")}$)'
    nodes = [
        TODAY,
        {'nodeAlias': 'cur', 'nodeType': 'get_relation', 'name': 'Current type',
         'config': {'worksheet': S[T], 'target': {'node': 'trigger'}, 'fields': [{'fieldId': a('activity_type_id')}]}},
        {'nodeAlias': 'given', 'nodeType': 'branch', 'name': 'Next type chosen?', 'config': {'mode': 'exclusive', 'paths': [
            {'alias': 'p_given', 'name': 'Chosen', 'condition': {'logic': 'and', 'items': [cond('trigger', a('summary'), 'not_empty')]},
             'nodes': []},
            {'alias': 'p_sugg', 'name': 'Use the suggested next type', 'nodes': [
                {'nodeAlias': 'sg', 'nodeType': 'update_record', 'name': 'Suggested next type', 'config': {
                    'worksheet': S[A], 'target': {'node': 'trigger'},
                    'fields': [{'fieldId': a('x_mail__next_type_id'), 'value': fld('cur', t('suggested_next_type_id'))}]}}]}]}},
        {'nodeAlias': 'me', 'nodeType': 'get_single', 'name': 'The activity, fresh', 'config': {
            'worksheet': S[A], 'filter': {'logic': 'and', 'items': [
                {'left': {'node': {'nodeAlias': 'me'}, 'fieldId': 'rowid'}, 'op': 'eq', 'type': 2,
                 'right': {'kind': 'field', 'node': {'nodeAlias': 'trigger'}, 'fieldId': 'rowid'}}]}}},
        {'nodeAlias': 'nt', 'nodeType': 'get_relation', 'name': 'Next type',
         'config': {'worksheet': S[T], 'target': {'node': 'me'}, 'fields': [{'fieldId': a('x_mail__next_type_id')}]}},
        {'nodeAlias': 'due', 'nodeType': 'compute', 'name': 'Next due date', 'config': {'mode': 'function', 'output_type': 'date',
            'formula': f'IF(ISBLANK($me-{a("x_mail__next_date")}$), DATEADD({base}, {offset}, 1), $me-{a("x_mail__next_date")}$)'}},
        {'nodeAlias': 'sm', 'nodeType': 'compute', 'name': 'Next summary', 'config': {'mode': 'function', 'output_type': 'text',
            'formula': (f'IF(ISBLANK($me-{a("x_mail__next_summary")}$), IF(ISBLANK($nt-{t("summary")}$), CONCAT($nt-{t("name")}$, ""), '
                        f'$nt-{t("summary")}$), $me-{a("x_mail__next_summary")}$)')}},
        {'nodeAlias': 'w', 'nodeType': 'update_record', 'name': 'Done', 'config': {
            'worksheet': S[A], 'target': {'node': 'trigger'}, 'fields': done_fields()}},
        {'nodeAlias': 'nx', 'nodeType': 'create_record', 'name': 'Next activity', 'config': {'worksheet': S[A], 'fields': [
            {'fieldId': a('summary'), 'value': fld('sm', 'string_fx_id')},
            {'fieldId': a('activity_type_id'), 'value': fld('me', a('x_mail__next_type_id'))},
            {'fieldId': a('date_deadline'), 'value': fld('due', 'string_fx_id')},
            {'fieldId': a('user_id'), 'value': fld('trigger', a('user_id'))},
            {'fieldId': a('note'), 'value': fld('nt', t('default_note'))},
            {'fieldId': a('x_contacts__partner_id'), 'value': fld('trigger', a('x_contacts__partner_id'))},
            {'fieldId': a('res_model'), 'value': fld('trigger', a('res_model'))},
            {'fieldId': a('res_id'), 'value': fld('trigger', a('res_id'))},
            {'fieldId': a('res_name'), 'value': fld('trigger', a('res_name'))},
            {'fieldId': a('active'), 'value': lit('1')}]}},
    ]
    batch_add(pid, nodes)
    patch_not_empty(pid, 'Next type chosen?', a('x_mail__next_type_id'), 'Chosen')
    return pid


def patch_not_empty(pid, gateway, field_id, name):
    """First path of `gateway`: relation `field_id` of the trigger is not empty (stored form; PLATFORM-ISSUES P22)."""
    names, d = node_ids(pid)
    start = d.get('startEventId') or next(k for k, v in d['flowNodeMap'].items() if v.get('typeId') == 0)
    nid = d['flowNodeMap'][names[gateway]]['flowIds'][0]
    hap('workflow', 'node', 'save', pid, nid, '--type', '2', '-c', json.dumps({'operateCondition': [[{
        'nodeId': start, 'nodeType': 0, 'appType': 1, 'filedId': field_id, 'filedTypeId': 29, 'enumDefault': 1,
        'conditionId': '31', 'conditionValues': []}]]}))
    hap('workflow', 'node', 'rename', pid, nid, '-n', name, ok_fail=True)


def launch_button():
    return button(C, 'Launch Plan', {'type': 'createRelatedRecord', 'relationField': F(C, 'x_mail__plan_launch_ids'),
                                     'runWorkflowAfterSubmit': False}, 'mail')


def launch_flow():
    from wflib import create_flow
    pid = create_flow('Activities - Launch plan', 'worksheet', 'mail', STEP,
                      'A new plan launch creates one activity per plan step (Odoo mail.activity.plan launch).')
    names, d = node_ids(pid)
    if 'Who gets the steps?' not in names:
        s = lambda f: F(ST, f)
        nodes = [
            {'nodeAlias': 'plan', 'nodeType': 'get_relation', 'name': 'The plan',
             'config': {'worksheet': S[PL], 'target': {'node': 'trigger'}, 'fields': [{'fieldId': F(L, 'x_mail__plan_id')}]}},
            {'nodeAlias': 'ct', 'nodeType': 'get_relation', 'name': 'The contact',
             'config': {'worksheet': S[C], 'target': {'node': 'trigger'}, 'fields': [{'fieldId': F(L, 'x_contacts__partner_id')}]}},
            {'nodeAlias': 'od', 'nodeType': 'get_relation_records', 'name': 'Steps assigned at launch',
             'config': {'worksheet': S[ST], 'target': {'node': 'plan'}, 'fields': [{'fieldId': F(PL, 'template_ids')}],
                        'filter': {'logic': 'and', 'items': [
                            {'left': {'node': {'nodeAlias': 'od'}, 'fieldId': s('responsible_type')}, 'op': 'eq',
                             'right': lit(option_key(ST, 'responsible_type', 'Ask at launch'))}]}}},
            {'nodeAlias': 'nod', 'nodeType': 'rollup', 'name': 'How many', 'config': {'data_source': {'node': 'od'}}},
            {'nodeAlias': 'who', 'nodeType': 'branch', 'name': 'Who gets the steps?', 'config': {'mode': 'exclusive', 'paths': [
                {'alias': 'p_refuse', 'name': 'Nobody chosen',
                 'condition': {'logic': 'and', 'items': [{'node': 'nod', 'field': 'number_fx_id', 'op': 'gt', 'type': 6, 'value': '0'},
                                                         cond('trigger', F(L, 'x_mail__assignee'), 'empty')]},
                 'nodes': [{'nodeAlias': 'no', 'nodeType': 'update_record', 'name': 'Refused', 'config': {
                     'worksheet': S[L], 'target': {'node': 'trigger'}, 'fields': [
                         {'fieldId': F(L, 'x_mail__status'), 'value': lit(option_key(L, 'x_mail__status', 'Refused'))},
                         {'fieldId': F(L, 'x_mail__message'), 'value': lit('This plan has steps assigned at launch: choose who gets them, then launch again.')}]}}]},
                {'alias': 'p_go', 'name': 'Launch', 'nodes': [
                    {'nodeAlias': 'steps', 'nodeType': 'get_relation_records', 'name': 'Its steps',
                     'config': {'worksheet': S[ST], 'target': {'node': 'plan'}, 'fields': [{'fieldId': F(PL, 'template_ids')}],
                                'sorts': [{'controlId': s('sequence'), 'controlType': 6, 'isAsc': True}]}},
                    {'nodeAlias': 'each', 'nodeType': 'sub_process', 'name': 'One activity per step', 'config': {
                        'data_source': {'node': 'steps'}, 'process': {
                            'name': 'Activities - one plan step', 'data_source': {'node': 'steps'}, 'execute_type': 3, 'wait_complete': True,
                            'parameters': [{'controlId': 'p_launch', 'name': 'p_launch', 'value': {'kind': 'field', 'node': 'trigger', 'fieldId': 'rowid'}}],
                            'nodes': []}}},
                    {'nodeAlias': 'ok', 'nodeType': 'update_record', 'name': 'Launched', 'config': {
                        'worksheet': S[L], 'target': {'node': 'trigger'}, 'fields': [
                            {'fieldId': F(L, 'x_mail__status'), 'value': lit(option_key(L, 'x_mail__status', 'Done'))},
                            {'fieldId': F(L, 'x_mail__name'), 'value': {'kind': 'template',
                             'value': f'$plan-{F(PL, "name")}$: $ct-{F(C, "complete_name")}$'}},
                            {'fieldId': F(L, 'x_mail__res_model'), 'value': lit('Contacts')},
                            {'fieldId': F(L, 'x_mail__res_id'), 'value': fld('ct', 'rowid')},
                            {'fieldId': F(L, 'x_mail__res_name'), 'value': fld('ct', F(C, 'complete_name'))}]}}]}]}}]
        batch_add(pid, nodes, '--trigger-worksheet', S[L], '--trigger-event', 'create')
        names, d = node_ids(pid)
        hap('workflow', 'node', 'rename', pid, d['flowNodeMap'][names['Who gets the steps?']]['flowIds'][0], '-n', 'Nobody chosen', ok_fail=True)
    # inner flow: one step
    sub = hap('workflow', 'node', 'get', pid, names['One activity per step'], '--type', '16'); sub = sub.get('data', sub)
    inner = sub['subProcessId']
    inames, idata = node_ids(inner)
    if 'The launch' not in inames:
        s = lambda f: F(ST, f)
        unit = f'CONCAT($trigger-{s("delay_unit")}$, "")'
        n = f'IF(ISBLANK($trigger-{s("delay_count")}$), 0, $trigger-{s("delay_count")}$)'
        offset = (f'CONCAT(IF(CONCAT($trigger-{s("delay_from")}$, "")=="Before Plan Date", "-", "+"), '
                  f'IF({unit}=="weeks", {n} * 7, {n}), IF({unit}=="months", "M", "d"))')
        mk = lambda alias, name, user: {'nodeAlias': alias, 'nodeType': 'create_record', 'name': name, 'config': {'worksheet': S[A], 'fields': [
            {'fieldId': a('summary'), 'value': fld('sm', 'string_fx_id')},
            {'fieldId': a('activity_type_id'), 'value': {'kind': 'record', 'node': 'tp'}},
            {'fieldId': a('date_deadline'), 'value': fld('due', 'string_fx_id')},
            {'fieldId': a('user_id'), 'value': user},
            {'fieldId': a('note'), 'value': fld('trigger', s('note'))},
            {'fieldId': a('x_contacts__partner_id'), 'value': fld('la', F(L, 'x_contacts__partner_id'))},
            {'fieldId': a('activity_plan_id'), 'value': fld('la', F(L, 'x_mail__plan_id'))},
            {'fieldId': a('activity_template_id'), 'value': {'kind': 'record', 'node': 'trigger'}},
            {'fieldId': a('x_mail__plan_launch_id'), 'value': {'kind': 'record', 'node': 'la'}},
            {'fieldId': a('res_model'), 'value': lit('Contacts')},
            {'fieldId': a('automated'), 'value': lit('1')},
            {'fieldId': a('active'), 'value': lit('1')}]}}
        nodes = [
            {'nodeAlias': 'la', 'nodeType': 'get_single', 'name': 'The launch', 'config': {
                'worksheet': S[L], 'filter': {'logic': 'and', 'items': [
                    {'left': {'node': {'nodeAlias': 'la'}, 'fieldId': 'rowid'}, 'op': 'eq', 'type': 2,
                     'right': {'kind': 'field', 'node': {'nodeId': PARAM}, 'fieldId': 'p_launch'}}]}}},
            {'nodeAlias': 'tp', 'nodeType': 'get_relation', 'name': 'Step type',
             'config': {'worksheet': S[T], 'target': {'node': 'trigger'}, 'fields': [{'fieldId': s('activity_type_id')}]}},
            {'nodeAlias': 'due', 'nodeType': 'compute', 'name': 'Due date', 'config': {'mode': 'function', 'output_type': 'date',
                'formula': f'DATEADD($la-{F(L, "x_mail__plan_date")}$, {offset}, 1)'}},
            {'nodeAlias': 'sm', 'nodeType': 'compute', 'name': 'Summary', 'config': {'mode': 'function', 'output_type': 'text',
                'formula': f'IF(ISBLANK($trigger-{s("summary")}$), CONCAT($tp-{F(T, "name")}$, ""), $trigger-{s("summary")}$)'}},
            {'nodeAlias': 'kind', 'nodeType': 'branch', 'name': 'Assignment?', 'config': {'mode': 'exclusive', 'paths': [
                {'alias': 'p_user', 'name': 'Specific User',
                 'condition': {'logic': 'and', 'items': [cond('trigger', s('responsible_type'), 'eq', option_key(ST, 'responsible_type', 'Specific User'))]},
                 'nodes': [mk('mk1', 'Activity for the step\'s user', fld('trigger', s('responsible_id')))]},
                {'alias': 'p_launch', 'name': 'Chosen at launch', 'nodes': [mk('mk2', 'Activity for the chosen person', fld('la', F(L, 'x_mail__assignee')))]}]}}]
        batch_add(inner, json.loads(json.dumps(nodes).replace('sub_trigger', 'trigger')), '--after',
                  idata.get('startEventId') or next(k for k, v in idata['flowNodeMap'].items() if v.get('typeId') == 0))
        inames, idata = node_ids(inner)
        hap('workflow', 'node', 'rename', inner, idata['flowNodeMap'][inames['Assignment?']]['flowIds'][0], '-n', 'Specific User', ok_fail=True)
    return pid


def rebuild_variants():
    btn, pid = button(P, 'Rebuild Variants', {'type': 'triggerWorkflow', 'confirm': True,
                                              'confirmMsg': 'Rebuild this product\'s variants from its attribute lines?'}, 'product')
    if 'Add a variant request' not in node_ids(pid)[0]:
        batch_add(pid, [{'nodeAlias': 'req', 'nodeType': 'create_record', 'name': 'Add a variant request', 'config': {
            'worksheet': S[Q], 'fields': [
                {'fieldId': F(Q, 'x_product__product_id'), 'value': {'kind': 'record', 'node': 'trigger'}},
                {'fieldId': F(Q, 'x_product__name'), 'value': {'kind': 'template', 'value': f'Rebuild requested: $trigger-{F(P, "name")}$'}}]}}])
    return pid


if __name__ == '__main__':
    for fn in (mark_done, done_and_next, launch_flow, rebuild_variants):
        pid = fn()
        r = publish(pid)
        print(fn.__name__, pid, 'published' if r.get('isPublish') else json.dumps(r, ensure_ascii=False)[:600])
    btn, _ = launch_button()
    print('Launch Plan button', btn)
