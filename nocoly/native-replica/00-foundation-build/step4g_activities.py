"""Wave 0 (plan v2), step 4g: Activity Types, Activity Plans + Plan Steps (subform), Activities, Plan Launches.

Odoo 20 (mail): an activity type has one "Suggest Next Activity" (no trigger/chaining field any more), delay count,
unit (days / weeks / months) and type (after the previous activity's completion date or deadline). Plan steps are
"Before / After Plan Date"; assignment "Ask at launch", "Specific User", plus HR's Manager / Employee / Role.
State, Done Date and Done By are written by workflows #14 and #15; the launch flow (#16) fills Plan Launches.
Run: python step4g_activities.py
"""
from lib import hap, APP, record
from sheetlib import (F, ensure_sheet, ensure_reverse, raw_fields, apply_spec, sheets_by_alias, add_once, set_show,
                      by_alias, ensure_self_relation, HIDDEN)
from step4e_products import mount

STEP = 'v2 step 4g'
AUTO = 'Kept up to date automatically.'
ON = [{'source': 'static', 'value': '1'}]
MODELS = ['Contacts', 'Products', 'Variants', 'Employees']

TYPES = {
    'name': 'Activity Types', 'alias': 'mail_activity_type', 'module': 'mail', 'group': 'Activities/Configuration',
    'icon': 'sys_wand_office', 'title': 'Name',
    'desc': 'Kinds of activity (call, meeting, to-do) with their default summary, delay and next step.',
    'fields': [
        F('Name', 'TEXT', 'name', required=True),
        F('Default Summary', 'TEXT', 'summary'),
        F('Action', 'DROP_DOWN', 'category', options=['None', 'Upload Document', 'Phonecall', 'Meeting'],
          defaultValue=[{'source': 'static', 'value': 'None'}]),
        F('Decoration Type', 'DROP_DOWN', 'decoration_type', options=['Alert', 'Error'],
          desc='Highlights activities of this type.'),
        F('Icon', 'TEXT', 'icon', desc='Icon name, for example phone or calendar_today.'),
        F('Schedule', 'NUMBER', 'delay_count', dot=0, desc='Default delay before the due date.'),
        F('Delay Units', 'DROP_DOWN', 'delay_unit', options=['days', 'weeks', 'months'],
          defaultValue=[{'source': 'static', 'value': 'days'}], required=True),
        F('Delay Type', 'DROP_DOWN', 'delay_from',
          options=['after previous activity deadline', 'after previous activity completion date'],
          defaultValue=[{'source': 'static', 'value': 'after previous activity deadline'}], required=True),
        F('Model', 'DROP_DOWN', 'res_model', options=MODELS, desc='Leave empty to use this type on every sheet.'),
        F('Default User', 'USER_PICKER', 'default_user_id', extra={'userPermission': 1}),
        F('Default Note', 'RICH_TEXT', 'default_note'),
        F('Sequence', 'NUMBER', 'sequence', dot=0),
        F('Active', 'SWITCH', 'active', defaultValue=ON),
    ],
}

PLANS = {
    'name': 'Activity Plans', 'alias': 'mail_activity_plan', 'module': 'mail', 'group': 'Activities/Configuration',
    'icon': 'sys_tactic2_symbol', 'title': 'Name',
    'desc': 'A set of activities scheduled together, for example onboarding steps.',
    'fields': [
        F('Name', 'TEXT', 'name', required=True),
        F('Model', 'DROP_DOWN', 'res_model', options=MODELS, required=True, desc='The sheet this plan is launched from.'),
        F('Active', 'SWITCH', 'active', defaultValue=ON),
    ],
}

STEPS = {
    'name': 'Plan Steps', 'alias': 'mail_activity_plan_template', 'module': 'mail', 'group': 'System Tables',
    'icon': 'sys_tactic_activity', 'title': 'Summary',
    'desc': 'One activity of a plan. Edited inside the plan.',
    'fields': [
        F('Summary', 'TEXT', 'summary'),
        F('Activity Type', 'RELATE_SHEET', 'activity_type_id', dataSource='@mail_activity_type', multi=False, required=True,
          config={'displayMode': 'dropdown'}),
        F('Assignment', 'DROP_DOWN', 'responsible_type',
          options=['Ask at launch', 'Specific User', 'Role', 'Manager', 'Employee'],
          defaultValue=[{'source': 'static', 'value': 'Ask at launch'}], required=True),
        F('Assigned to', 'USER_PICKER', 'responsible_id', extra={'userPermission': 1}, desc='For "Specific User".'),
        F('Interval', 'NUMBER', 'delay_count', dot=0),
        F('Delay Units', 'DROP_DOWN', 'delay_unit', options=['days', 'weeks', 'months'],
          defaultValue=[{'source': 'static', 'value': 'days'}], required=True),
        F('Trigger', 'DROP_DOWN', 'delay_from', options=['Before Plan Date', 'After Plan Date'],
          defaultValue=[{'source': 'static', 'value': 'After Plan Date'}], required=True),
        F('Note', 'RICH_TEXT', 'note'),
        F('Sequence', 'NUMBER', 'sequence', dot=0),
    ],
}

ACTIVITIES = {
    'name': 'Activities', 'alias': 'mail_activity', 'module': 'mail', 'group': 'Activities', 'icon': 'sys_4_1_calendar',
    'title': 'Summary',
    'desc': 'Calls, meetings and to-dos scheduled on contacts and other records.',
    'fields': [
        F('Summary', 'TEXT', 'summary', required=True),
        F('Activity Type', 'RELATE_SHEET', 'activity_type_id', dataSource='@mail_activity_type', multi=False,
          config={'displayMode': 'dropdown'}),
        F('Due Date', 'DATE', 'date_deadline', required=True),
        F('Assigned to', 'USER_PICKER', 'user_id', extra={'userPermission': 1}, required=True),
        F('State', 'DROP_DOWN', 'x_mail__state', options=['Overdue', 'Today', 'Planned', 'Done'],
          extra={'enumDefault2': 1}, desc='From the due date in Malaysian time. ' + AUTO),
        F('Note', 'RICH_TEXT', 'note'),
        F('Done Date', 'DATE', 'date_done', desc=AUTO),
        F('Done By', 'USER_PICKER', 'x_mail__done_by', extra={'userPermission': 1}, desc=AUTO),
        F('Feedback', 'TEXT', 'feedback', extra={'enumDefault': 1}),
        F('Active', 'SWITCH', 'active', defaultValue=ON, desc='Done activities are archived (Active off), as in Odoo.'),
        F('Automated', 'SWITCH', 'automated', desc='Created by a workflow or a plan.'),
        F('Document Model', 'TEXT', 'res_model', desc='Sheet of the record this activity is about, for example Contacts.'),
        F('Document Name', 'TEXT', 'res_name'),
        F('Document ID', 'TEXT', 'res_id', desc='Record id of that record.'),
        F('Attachments', 'ATTACHMENT', 'attachment_ids'),
    ],
}

LAUNCHES = {
    'name': 'Plan Launches', 'alias': 'x_mail__plan_launch', 'module': 'mail', 'group': 'System Tables',
    'icon': 'sys_gear1_office', 'title': 'Launch',
    'desc': 'One launch of an activity plan on a record. The launch flow creates its activities.',
    'fields': [
        F('Launch', 'TEXT', 'x_mail__name', desc='Plan and record, for example "Onboarding: Acme". ' + AUTO),
        F('Plan', 'RELATE_SHEET', 'x_mail__plan_id', dataSource='@mail_activity_plan', multi=False, required=True,
          config={'displayMode': 'dropdown'}),
        F('Plan Date', 'DATE', 'x_mail__plan_date', required=True, desc='Step dates are counted from this date.'),
        F('Assigned to', 'USER_PICKER', 'x_mail__assignee', extra={'userPermission': 1},
          desc='For steps set to "Ask at launch".'),
        F('Document Model', 'TEXT', 'x_mail__res_model'),
        F('Document ID', 'TEXT', 'x_mail__res_id'),
        F('Document Name', 'TEXT', 'x_mail__res_name'),
        F('Status', 'DROP_DOWN', 'x_mail__status', options=['Waiting', 'Done', 'Refused'], extra={'enumDefault2': 1},
          defaultValue=[{'source': 'static', 'value': 'Waiting'}]),
        F('Message', 'TEXT', 'x_mail__message', desc='Why a launch was refused. ' + AUTO),
    ],
}
STATE_COLOURS = {'Overdue': '#F44336', 'Today': '#FF9800', 'Planned': '#4CAF50', 'Done': '#9E9E9E',
                 'Waiting': '#2196F3', 'Refused': '#F44336'}


def colour(ws, alias):
    c = by_alias(ws)[alias]
    opts = c.get('options') or []
    new = [dict(o, color=STATE_COLOURS.get(o['value'], o.get('color'))) for o in opts]
    if [o.get('color') for o in opts] != [o.get('color') for o in new] or c.get('enumDefault2') != 1:
        apply_spec([{'type': 'field.update', 'worksheet': ws, 'field': c['controlId'], 'set': {'options': new, 'enumDefault2': 1}}])


if __name__ == '__main__':
    sheets = sheets_by_alias()
    tws, _, f1 = ensure_sheet(TYPES, STEP)
    nxt, prev = ensure_self_relation(tws, 'suggested_next_type_id', 'Suggest Next Activity', 'previous_type_ids',
                                     'Preceding Activities', 'mail', 'Activity Types', STEP,
                                     desc='Offered as the next activity when one of this type is done.')
    print('Activity Types', tws, 'fixes', f1, '| next', nxt['controlId'], 'preceding', prev['controlId'])

    pws, _, f2 = ensure_sheet(PLANS, STEP)
    add_once(pws, {'type': 29, 'controlName': 'Company', 'alias': 'company_id', 'dataSource': sheets['res_company']['id'],
                   'enumDefault': 1, 'fieldPermission': HIDDEN, 'advancedSetting': {'showtype': '3'},
                   'desc': 'Hidden while there is one company.'}, 'mail', 'Activity Plans.Company', STEP)
    sws, _, f3 = ensure_sheet(STEPS, STEP)
    s = by_alias(sws)
    sub, back = mount(pws, sws, 'Activities', 'Plan',
                      [s[a]['controlId'] for a in ('activity_type_id', 'summary', 'responsible_type', 'responsible_id',
                                                   'delay_count', 'delay_unit', 'delay_from')],
                      'template_ids', 'plan_id', 'mail', 'Activity Plans', 'Plan Steps')
    print('Activity Plans', pws, '| Plan Steps', sws, '| subform', sub['controlId'], 'back', back['controlId'], '| fixes', f2, f3)

    aws, _, f4 = ensure_sheet(ACTIVITIES, STEP)
    lws, lraw, f5 = ensure_sheet(LAUNCHES, STEP)
    colour(aws, 'x_mail__state')
    colour(lws, 'x_mail__status')
    # relations that point at sheets made in this step
    add_once(aws, {'type': 29, 'controlName': 'Plan', 'alias': 'activity_plan_id', 'dataSource': pws, 'enumDefault': 1,
                   'advancedSetting': {'showtype': '3'}}, 'mail', 'Activities.Plan', STEP)
    add_once(aws, {'type': 29, 'controlName': 'Generated From', 'alias': 'activity_template_id', 'dataSource': sws,
                   'enumDefault': 1, 'advancedSetting': {'showtype': '3'}, 'desc': 'The plan step that created it.'},
             'mail', 'Activities.Generated From', STEP)
    # two-way: Activities.Plan Launch <-> Plan Launches.Activities
    if 'x_mail__plan_launch_id' not in by_alias(aws):
        hap('worksheet', 'add-fields', aws, '--controls', __import__('json').dumps([{
            'type': 29, 'controlName': 'Plan Launch', 'alias': 'x_mail__plan_launch_id', 'dataSource': lws, 'enumDefault': 1,
            'advancedSetting': {'showtype': '3'}}]))
    pl = by_alias(aws)['x_mail__plan_launch_id']
    record(pl['controlId'], 'field', 'Activities.Plan Launch', 'mail', STEP)
    if not any(c['type'] == 29 and c.get('sourceControlId') == pl['controlId'] for c in raw_fields(lws)):
        hap('worksheet', 'pair-relation', aws, pl['controlId'], '--name', 'Activities')
    rl = ensure_reverse(lws, pl['controlId'], 'x_mail__activity_ids', 'Activities', 'mail', '6', STEP)
    a = by_alias(aws)
    set_show(lws, rl['controlId'], [a[k]['controlId'] for k in ('summary', 'activity_type_id', 'date_deadline', 'user_id', 'x_mail__state')])
    # Contact link (owned by contacts): Activities.Contact <-> Contacts.Activities
    cws = sheets['res_partner']['id']
    if 'x_contacts__partner_id' not in by_alias(aws):
        hap('worksheet', 'add-fields', aws, '--controls', __import__('json').dumps([{
            'type': 29, 'controlName': 'Contact', 'alias': 'x_contacts__partner_id', 'dataSource': cws, 'enumDefault': 1,
            'advancedSetting': {'showtype': '3'}, 'desc': 'The contact this activity is about.'}]))
    ct = by_alias(aws)['x_contacts__partner_id']
    record(ct['controlId'], 'field', 'Activities.Contact', 'contacts', STEP)
    if not any(c['type'] == 29 and c.get('sourceControlId') == ct['controlId'] for c in raw_fields(cws)):
        hap('worksheet', 'pair-relation', aws, ct['controlId'], '--name', 'Activities')
    rc = ensure_reverse(cws, ct['controlId'], 'activity_ids', 'Activities', 'contacts', '6', STEP)
    set_show(cws, rc['controlId'], [a[k]['controlId'] for k in ('summary', 'activity_type_id', 'date_deadline', 'user_id', 'x_mail__state')])
    # Plan Launches: Contact (owned by contacts)
    add_once(lws, {'type': 29, 'controlName': 'Contact', 'alias': 'x_contacts__partner_id', 'dataSource': cws, 'enumDefault': 1,
                   'advancedSetting': {'showtype': '3'}}, 'contacts', 'Plan Launches.Contact', STEP)
    print('Activities', aws, 'fields', len(by_alias(aws)), '| Plan Launches', lws, '| fixes', f4, f5,
          '| launch reverse', rl['controlId'], '| contact reverse', rc['controlId'])
