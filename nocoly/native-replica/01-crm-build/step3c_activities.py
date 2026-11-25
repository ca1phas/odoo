"""CRM Phase A, step 3c: activities and activity plans on leads (01-crm.md §4 L11).

  A1 CRM - Activity on a lead       Activities: the Lead link and the document fields (model "Leads", id, name) kept
                                    in step, whichever was filled (the lead's Activities tab fills the link; Done &
                                    Schedule Next copies the document fields)
  A2 CRM - Launch plan on a lead    Plan Launches with a lead: one activity per plan step, as the wave 0 launch flow does
                                    for contacts (Odoo mail.activity.plan launch), linked to the lead
  A3 guard on the wave 0 flow       "Activities - Launch plan" (owned by mail) now starts only when the launch has a
                                    contact, so lead launches are left to A2. Nothing else in that flow changes.
Run: python step3c_activities.py a1 a2 a3
"""
import json, sys
from crmwf import *  # noqa: F401,F403
from crmwf import L, A, PL
from step3_wf_core import build, done, raw_only

STEP = 'crm step 3c'
T, PLAN, ST = 'mail_activity_type', 'mail_activity_plan', 'mail_activity_plan_template'
PARAM = '<id>'   # the parameter step of a sub-process (fixed id), as in wave 0


def a(f):
    return F(A, f)


def a1():
    nodes = [branch('lb', 'Lead link or document?', [
        path('p1', 'Lead set, document missing', [
            relation('ld', 'The lead', L, a('x_crm__lead_id'), source='trigger'),
            upd('w1', 'Document = the lead', [{'fieldId': a('res_model'), 'value': lit('Leads')},
                                              {'fieldId': a('res_id'), 'value': ref('ld', 'rowid')},
                                              {'fieldId': a('res_name'), 'value': ref('ld', l('name'))}], sheet=A)],
             [cond('trigger', a('res_model'), 'empty')]),
        path('p2', 'Document is a lead, link missing', [
            single('q', 'The lead of the document', L, [fi('q', 'rowid', 'eq', fref('trigger', a('res_id')), 2)]),
            branch('qr', 'Lead found?', [
                path('qh', 'Found', [upd('w2', 'Link to the lead', [{'fieldId': a('x_crm__lead_id'), 'value': rec('q')},
                                                                     {'fieldId': a('res_name'), 'value': ref('q', l('name'))}], sheet=A)],
                     result_type='has_data')], result=True)],
             [cond('trigger', a('res_model'), 'eq', 'Leads'), cond('trigger', a('res_id'), 'not_empty')]),
        path('p3', 'Nothing to do', [])])]
    pid, new = build('CRM - Activity on a lead',
                     "Keeps an activity's Lead link and its document fields (model Leads, id, name) in step: the lead's "
                     "Activities tab sets the link, Done & Schedule Next copies the document fields.",
                     nodes, '--trigger-worksheet', S[A], '--trigger-event', 'create_or_update',
                     '--trigger-fields', f"{a('x_crm__lead_id')},{a('res_model')},{a('res_id')}")
    lead = lambda groups, empty: rel_cond(groups[0][0], a('x_crm__lead_id'), empty)
    patch_path(pid, 'Lead link or document?', 0,
               lambda groups: [[x for x in groups[0] if x.get('filedId') != a('x_crm__lead_id')] + [lead(groups, False)]])
    patch_path(pid, 'Lead link or document?', 1,
               lambda groups: [[x for x in groups[0] if x.get('filedId') != a('x_crm__lead_id')] + [lead(groups, True)]])
    name_paths(pid, 'Lead link or document?', ['Lead set, document missing', 'Document is a lead, link missing', 'Nothing to do'])
    return done(pid, 'A1 Activity on a lead')


def a2():
    """The wave 0 launch flow (00-foundation-build/step6_wf_activity_buttons.py launch_flow), for a lead."""
    s = lambda f: F(ST, f)
    nodes = [
        relation('plan', 'The plan', PLAN, F(PL, 'x_mail__plan_id')),
        relation('ld', 'The lead', L, F(PL, 'x_crm__lead_id')),
        {'nodeAlias': 'od', 'nodeType': 'get_relation_records', 'name': 'Steps assigned at launch',
         'config': {'worksheet': S[ST], 'target': {'node': 'plan'}, 'fields': [{'fieldId': F(PLAN, 'template_ids')}],
                    'filter': {'logic': 'and', 'items': [
                        {'left': {'node': {'nodeAlias': 'od'}, 'fieldId': s('responsible_type')}, 'op': 'eq',
                         'right': lit(option_key(ST, 'responsible_type', 'Ask at launch'))}]}}},
        {'nodeAlias': 'nod', 'nodeType': 'rollup', 'name': 'How many', 'config': {'data_source': {'node': 'od'}}},
        branch('who', 'Who gets the steps?', [
            path('p_refuse', 'Nobody chosen', [upd('no', 'Refused', [
                {'fieldId': F(PL, 'x_mail__status'), 'value': lit(option_key(PL, 'x_mail__status', 'Refused'))},
                {'fieldId': F(PL, 'x_mail__message'), 'value': lit('This plan has steps assigned at launch: choose who gets them, then launch again.')}],
                sheet=PL)],
                 [{'node': 'nod', 'field': 'number_fx_id', 'op': 'gt', 'type': 6, 'value': '0'},
                  cond('trigger', F(PL, 'x_mail__assignee'), 'empty')]),
            path('p_go', 'Launch', [
                {'nodeAlias': 'steps', 'nodeType': 'get_relation_records', 'name': 'Its steps',
                 'config': {'worksheet': S[ST], 'target': {'node': 'plan'}, 'fields': [{'fieldId': F(PLAN, 'template_ids')}],
                            'sorts': [{'controlId': s('sequence'), 'controlType': 6, 'isAsc': True}]}},
                {'nodeAlias': 'each', 'nodeType': 'sub_process', 'name': 'One activity per step', 'config': {
                    'data_source': {'node': 'steps'}, 'process': {
                        'name': 'CRM - one plan step on a lead', 'data_source': {'node': 'steps'}, 'execute_type': 3, 'wait_complete': True,
                        'parameters': [{'controlId': 'p_launch', 'name': 'p_launch', 'value': {'kind': 'field', 'node': 'trigger', 'fieldId': 'rowid'}}],
                        'nodes': []}}},
                upd('ok', 'Launched', [
                    {'fieldId': F(PL, 'x_mail__status'), 'value': lit(option_key(PL, 'x_mail__status', 'Done'))},
                    {'fieldId': F(PL, 'x_mail__name'), 'value': {'kind': 'template', 'value': f'$plan-{F(PLAN, "name")}$: $ld-{l("name")}$'}},
                    {'fieldId': F(PL, 'x_mail__res_model'), 'value': lit('Leads')},
                    {'fieldId': F(PL, 'x_mail__res_id'), 'value': ref('ld', 'rowid')},
                    {'fieldId': F(PL, 'x_mail__res_name'), 'value': ref('ld', l('name'))}], sheet=PL)])])]
    pid, new = build('CRM - Launch plan on a lead',
                     'A new plan launch with a lead creates one activity per plan step, linked to the lead (the wave 0 '
                     'launch flow does the same for contacts).',
                     nodes, '--trigger-worksheet', S[PL], '--trigger-event', 'create')
    patch_trigger(pid, lambda sid, groups: [[rel_cond_on(sid, 0, F(PL, 'x_crm__lead_id'), empty=False)]])
    name_paths(pid, 'Who gets the steps?', ['Nobody chosen', 'Launch'])
    names, m, _ = flow_map(pid)
    sub = node_get(pid, names['One activity per step'], 16)
    inner = sub['subProcessId']
    inames, idata = node_ids(inner)
    if 'The launch' not in inames:
        unit = f'CONCAT($trigger-{s("delay_unit")}$, "")'
        n = f'IF(ISBLANK($trigger-{s("delay_count")}$), 0, $trigger-{s("delay_count")}$)'
        offset = (f'CONCAT(IF(CONCAT($trigger-{s("delay_from")}$, "")=="Before Plan Date", "-", "+"), '
                  f'IF({unit}=="weeks", {n} * 7, {n}), IF({unit}=="months", "M", "d"))')
        mk = lambda alias, name, user: {'nodeAlias': alias, 'nodeType': 'create_record', 'name': name, 'config': {'worksheet': S[A], 'fields': [
            {'fieldId': a('summary'), 'value': ref('sm', 'string_fx_id')},
            {'fieldId': a('activity_type_id'), 'value': rec('tp')},
            {'fieldId': a('date_deadline'), 'value': ref('due', 'string_fx_id')},
            {'fieldId': a('user_id'), 'value': user},
            {'fieldId': a('note'), 'value': ref('trigger', s('note'))},
            {'fieldId': a('x_crm__lead_id'), 'value': ref('la', F(PL, 'x_crm__lead_id'))},
            {'fieldId': a('activity_plan_id'), 'value': ref('la', F(PL, 'x_mail__plan_id'))},
            {'fieldId': a('activity_template_id'), 'value': rec('trigger')},
            {'fieldId': a('x_mail__plan_launch_id'), 'value': rec('la')},
            {'fieldId': a('res_model'), 'value': lit('Leads')},
            {'fieldId': a('automated'), 'value': lit('1')},
            {'fieldId': a('active'), 'value': lit('1')}]}}
        inner_nodes = [
            {'nodeAlias': 'la', 'nodeType': 'get_single', 'name': 'The launch', 'config': {
                'worksheet': S[PL], 'filter': {'logic': 'and', 'items': [
                    {'left': {'node': {'nodeAlias': 'la'}, 'fieldId': 'rowid'}, 'op': 'eq', 'type': 2,
                     'right': {'kind': 'field', 'node': {'nodeId': PARAM}, 'fieldId': 'p_launch'}}]}}},
            relation('tp', 'Step type', T, s('activity_type_id')),
            {'nodeAlias': 'due', 'nodeType': 'compute', 'name': 'Due date', 'config': {'mode': 'function', 'output_type': 'date',
                'formula': f'DATEADD($la-{F(PL, "x_mail__plan_date")}$, {offset}, 1)'}},
            {'nodeAlias': 'sm', 'nodeType': 'compute', 'name': 'Summary', 'config': {'mode': 'function', 'output_type': 'text',
                'formula': f'IF(ISBLANK($trigger-{s("summary")}$), CONCAT($tp-{F(T, "name")}$, ""), $trigger-{s("summary")}$)'}},
            branch('kind', 'Assignment?', [
                path('p_user', 'Specific User', [mk('mk1', "Activity for the step's user", ref('trigger', s('responsible_id')))],
                     [cond('trigger', s('responsible_type'), 'eq', option_key(ST, 'responsible_type', 'Specific User'))]),
                path('p_launch', 'Chosen at launch', [mk('mk2', 'Activity for the chosen person', ref('la', F(PL, 'x_mail__assignee')))])])]
        batch_add(inner, inner_nodes, '--after',
                  idata.get('startEventId') or next(k for k, v in idata['flowNodeMap'].items() if v.get('typeId') == 0))
        record(inner, 'workflow', 'CRM - one plan step on a lead (inner)', 'crm', STEP)
    name_paths(inner, 'Assignment?', ['Specific User', 'Chosen at launch'])
    return done(pid, 'A2 Launch plan on a lead')


def a3():
    """Guard on the wave 0 flow: start only when the launch has a contact. The flow is owned by mail (wave 0 ledger)."""
    import os
    w0 = json.load(open(os.path.join(W0, 'ids.json'), encoding='utf-8'))
    pid = next(k for k, v in w0['objects'].items() if v['type'] == 'workflow' and v['name'] == 'Activities - Launch plan')
    patch_trigger(pid, lambda sid, groups: [[rel_cond_on(sid, 0, F(PL, 'x_contacts__partner_id'), empty=False)]])
    return done(pid, 'A3 guard on Activities - Launch plan (wave 0)')


if __name__ == '__main__':
    refresh()
    for name in sys.argv[1:]:
        globals()[name]()
