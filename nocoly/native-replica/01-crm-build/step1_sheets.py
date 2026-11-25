"""CRM Phase A, step 1: menu groups, option sets and worksheets (01-crm.md §3), with the bridge fields on wave 0 sheets.

Odoo 20 models: utm.stage / medium / source / campaign (utm), crm.team (sales_team), crm.stage / lost.reason / lead (crm),
calendar.event (calendar, only the part CRM uses). Native types only. Fields written by workflows are read-only and
say so in their description; the form layouts come in step1b_layouts.py.

Built here, not in the plan's first draft:
- the lead's Region field is `x_crm__region` (owned by crm; the plan wrote x_base__region);
- Meetings link to a lead through Odoo's own field name `opportunity_id`;
- Days to Assign / Close and Duration are numbers written by workflows (date differences), not formula fields.
Fields the CLI cannot make reliably (rollup with a filter, earliest-date rollup, Query Records "Similar Leads") are added
in the designer afterwards and recorded in the ledger by step1c_ui_fields.py.
Run: python step1_sheets.py
"""
import json
from crmlib import *  # noqa: F401,F403
from crmlib import FS as F

STEP = 'crm step 1'
MY = '{"name":"Malaysia","iso2":"my","dialCode":"60"}'
COMMON = '["MY","SG","ID","TH","VN","PH","BN","CN","HK","TW","JP","KR","IN","AU","GB","US"]'
DD = {'displayMode': 'dropdown'}
UNIQUE = 'Unique: a repeated name gets " [2]", " [3]" as in Odoo. '

TOP = [('Contacts', None), ('Products', None), ('Activities', None), ('CRM', 'crm'), ('Link Tracker', 'utm'),
       ('Settings', None), ('System Tables', None)]

UTM_STAGES = {
    'name': 'UTM Stages', 'alias': 'utm_stage', 'module': 'utm', 'group': 'Link Tracker', 'icon': 'sys_tactic_activity',
    'title': 'Stage Name', 'desc': 'Stages of a marketing campaign, for example New, Schedule, Design and Sent.',
    'fields': [F('Stage Name', 'TEXT', 'name', required=True), F('Sequence', 'NUMBER', 'sequence', dot=0)],
}
MEDIUMS = {
    'name': 'Mediums', 'alias': 'utm_medium', 'module': 'utm', 'group': 'Link Tracker', 'icon': 'sys_pins_traffic',
    'title': 'Medium Name', 'desc': 'How a lead or visitor reached you, for example Email, Phone or Website.',
    'fields': [F('Medium Name', 'TEXT', 'name', required=True, desc=UNIQUE.strip()),
               F('Active', 'SWITCH', 'active', defaultValue=ON)],
}
SOURCES = {
    'name': 'Sources', 'alias': 'utm_source', 'module': 'utm', 'group': 'Link Tracker', 'icon': 'sys_grain-effect_symbol',
    'title': 'Source Name', 'desc': 'Where a lead or visitor came from, for example Google, Facebook or a newsletter.',
    'fields': [F('Source Name', 'TEXT', 'name', required=True, desc=UNIQUE.strip())],
}
CAMPAIGNS = {
    'name': 'Campaigns', 'alias': 'utm_campaign', 'module': 'utm', 'group': 'Link Tracker', 'icon': 'sys_wand_office',
    'title': 'Campaign Name', 'desc': 'Marketing campaigns that leads and sales are attributed to.',
    'fields': [
        F('Campaign Name', 'TEXT', 'title', required=True),
        F('Campaign Identifier', 'TEXT', 'name', desc=UNIQUE + 'Filled in from the campaign name when empty. Used in links and reports.'),
        F('Responsible', 'USER_PICKER', 'user_id', required=True, extra={'userPermission': 1}, defaultValue=ME),
        F('Stage', 'RELATE_SHEET', 'stage_id', dataSource='@utm_stage', multi=False, required=True, config=DD),
        F('Active', 'SWITCH', 'active', defaultValue=ON),
    ],
}
TEAMS = {
    'name': 'Sales Teams', 'alias': 'crm_team', 'module': 'sales_team', 'group': 'CRM/Configuration', 'icon': 'sys_contacts_office',
    'title': 'Sales Team', 'desc': 'Sales teams with their leader and salespeople. New opportunities take the salesperson\'s team.',
    'fields': [
        F('Sales Team', 'TEXT', 'name', required=True),
        F('Sequence', 'NUMBER', 'sequence', dot=0),
        F('Team Leader', 'USER_PICKER', 'user_id', extra={'userPermission': 1}),
        F('Salespersons', 'USER_PICKER', 'member_ids', extra={'userPermission': 1, 'enumDefault': 1}),
        F('Leads', 'SWITCH', 'use_leads', desc='The team qualifies leads before they become opportunities.'),
        F('Pipeline', 'SWITCH', 'use_opportunities', defaultValue=ON, desc='The team works opportunities in the pipeline.'),
        F('Skip Auto Assignment', 'SWITCH', 'assignment_optout', desc='Leave the team out of rule-based lead assignment.'),
        F('Active', 'SWITCH', 'active', defaultValue=ON),
    ],
}
STAGES = {
    'name': 'Stages', 'alias': 'crm_stage', 'module': 'crm', 'group': 'CRM/Configuration', 'icon': 'sys_tactic2_symbol',
    'title': 'Stage Name', 'desc': 'Pipeline stages, in sequence order. A won stage closes the opportunity as won.',
    'fields': [
        F('Stage Name', 'TEXT', 'name', required=True),
        F('Sequence', 'NUMBER', 'sequence', dot=0),
        F('Is Won Stage', 'SWITCH', 'is_won', desc='Opportunities in this stage are won, with probability 100.'),
        F('Folded in Pipeline', 'SWITCH', 'fold',
          desc='Odoo folds this column on the board. HAP boards do not fold columns: hide it in the board settings instead.'),
        F('Days to Rot', 'NUMBER', 'rotting_threshold_days', dot=0,
          desc='An opportunity left in this stage longer than this is rotting. 0 = never.'),
        F('Requirements', 'TEXT', 'requirements', extra={'enumDefault': 1},
          desc='What must be done before an opportunity moves on (Odoo shows it as a tooltip).'),
        F('Sales Teams', 'RELATE_SHEET', 'team_ids', dataSource='@crm_team', multi=True,
          desc='Leave empty to use the stage in every team.'),
    ],
}
LOST = {
    'name': 'Lost Reasons', 'alias': 'crm_lost_reason', 'module': 'crm', 'group': 'CRM/Configuration', 'icon': 'sys_pins_traffic',
    'title': 'Description', 'desc': 'Why opportunities are lost, chosen in the Lost dialog.',
    'fields': [F('Description', 'TEXT', 'name', required=True), F('Active', 'SWITCH', 'active', defaultValue=ON)],
}
LEADS = {
    'name': 'Leads / Opportunities', 'alias': 'crm_lead', 'module': 'crm', 'group': 'CRM', 'icon': 'sys_4_1_calendar',
    'title': 'Opportunity',
    'desc': 'Leads and opportunities (Odoo crm.lead). The pipeline board shows the opportunities by stage.',
    'fields': [
        F('Opportunity', 'TEXT', 'name', desc="Left empty with a customer chosen, it becomes \"<customer>'s opportunity\"."),
        F('Type', 'DROP_DOWN', 'type', options=['Lead', 'Opportunity'], required=True,
          defaultValue=[{'source': 'static', 'value': 'Opportunity'}],
          desc='Leads are not yet qualified; opportunities are in the pipeline. The Leads views are used only when a customer wants the lead step.'),
        F('Priority', 'SCORE', 'priority', advanced_setting={'max': '3', 'itemicon': 'star'}),
        F('Customer', 'RELATE_SHEET', 'partner_id', dataSource='@res_partner', multi=False,
          desc='Choosing a customer fills in the company, contact, e-mail, phone, language and address.'),
        money('Expected Revenue', 'expected_revenue'),
        F('Probability', 'NUMBER', 'probability', dot=2, advanced_setting={'suffix': '%'}, desc='Chance of winning, 0 to 100.'),
        F('Automated Probability', 'NUMBER', 'automated_probability', dot=2, advanced_setting={'suffix': '%'},
          desc="Odoo's predictive lead score. Seed records keep Odoo's value; new records get one with lead scoring (phase B). " + AUTO),
        F('Email', 'EMAIL', 'email_from', desc='Changing it also changes the customer\'s e-mail.'),
        F('Phone', 'MOBILE_PHONE', 'phone', advanced_setting={'defaultarea': MY}, desc='Changing it also changes the customer\'s phone.'),
        F('Expected Closing', 'DATE', 'date_deadline'),
        F('Salesperson', 'USER_PICKER', 'user_id', extra={'userPermission': 1}, defaultValue=ME),
        F('Sales Team', 'RELATE_SHEET', 'team_id', dataSource='@crm_team', multi=False, config=DD,
          desc="Set from the salesperson's team when empty."),
        F('Stage', 'RELATE_SHEET', 'stage_id', dataSource='@crm_stage', multi=False, config=DD,
          desc='Set to the first stage of the team when empty.'),
        F('Won Status', 'DROP_DOWN', 'won_status', options=['Pending', 'Won', 'Lost'], extra={'enumDefault2': 1},
          defaultValue=[{'source': 'static', 'value': 'Pending'}],
          desc='Won = probability 100 in a won stage; Lost = archived with probability 0; otherwise Pending. ' + AUTO),
        F('Lost Reason', 'RELATE_SHEET', 'lost_reason_id', dataSource='@crm_lost_reason', multi=False, config=DD),
        F('Closing Note', 'TEXT', 'x_crm__lost_feedback', extra={'enumDefault': 1}, desc='Why it was lost, from the Lost dialog.'),
        F('Notes', 'RICH_TEXT', 'description'),
        F('Company Name', 'TEXT', 'partner_name'),
        F('Contact Name', 'TEXT', 'contact_name'),
        F('Job Position', 'TEXT', 'function'),
        F('Address', 'AREA_COUNTY', 'x_crm__region', desc='Country and state.',
          extra={'enumDefault': 1, 'enumDefault2': 2}, advanced_setting={'chooserange': '', 'commcountries': COMMON}),
        F('Street', 'TEXT', 'street'),
        F('Street 2', 'TEXT', 'street2'),
        F('Zip', 'TEXT', 'zip'),
        F('City', 'TEXT', 'city'),
        F('Country', 'RELATE_SHEET', 'country_id', dataSource='@res_country', multi=False, config=DD,
          desc='Set from the Address automatically.'),
        F('Website', 'TEXT', 'website', advanced_setting={'analysislink': '1'}),
        F('Language', 'DROP_DOWN', 'lang_id', options=['English', 'Malay', 'Chinese (Simplified)']),
        F('Campaign', 'RELATE_SHEET', 'campaign_id', dataSource='@utm_campaign', multi=False, config=DD),
        F('Medium', 'RELATE_SHEET', 'medium_id', dataSource='@utm_medium', multi=False, config=DD),
        F('Source', 'RELATE_SHEET', 'source_id', dataSource='@utm_source', multi=False, config=DD),
        F('Referred By', 'TEXT', 'referred'),
        F('Assignment Date', 'DATE_TIME', 'date_open', desc='When the salesperson was set. ' + AUTO),
        F('Closed Date', 'DATE_TIME', 'date_closed', desc=AUTO),
        F('Last Stage Update', 'DATE_TIME', 'date_last_stage_update', desc=AUTO),
        F('Conversion Date', 'DATE_TIME', 'date_conversion', desc='When the lead became an opportunity. ' + AUTO),
        F('Days to Assign', 'NUMBER', 'day_open', dot=2, desc='Days from creation to assignment. ' + AUTO),
        F('Days to Close', 'NUMBER', 'day_close', dot=2, desc='Days from creation to closing. ' + AUTO),
        F('Rotting', 'SWITCH', 'is_rotting', desc='Left in its stage longer than the stage allows. Refreshed daily. ' + AUTO),
        F('Days in Stage', 'NUMBER', 'rotting_days', dot=0, desc='Days since the last stage change, for rotting opportunities. ' + AUTO),
        F('Meeting Date', 'DATE', 'meeting_display_date', desc='Date of the next meeting, or of the last one when none is planned. ' + AUTO),
        F('Meeting', 'TEXT', 'meeting_display_label', desc='"Next Meeting", "Last Meeting" or "No Meeting". ' + AUTO),
        F('Active', 'SWITCH', 'active', defaultValue=ON, desc='Lost opportunities are archived (Active off), as in Odoo.'),
    ],
}
MEETINGS = {
    'name': 'Meetings', 'alias': 'calendar_event', 'module': 'calendar', 'group': 'CRM', 'icon': 'sys_4_1_calendar',
    'title': 'Meeting Subject', 'desc': 'Meetings with customers and colleagues (Odoo calendar.event), shown in a calendar view.',
    'fields': [
        F('Meeting Subject', 'TEXT', 'name', required=True),
        F('Start', 'DATE_TIME', 'start', required=True),
        F('End', 'DATE_TIME', 'stop', required=True),
        F('All Day', 'SWITCH', 'allday'),
        F('Duration', 'NUMBER', 'duration', dot=2, advanced_setting={'suffix': 'h'}, desc='Hours from start to end. ' + AUTO),
        F('Organizer', 'USER_PICKER', 'user_id', extra={'userPermission': 1}, defaultValue=ME),
        F('Attendees', 'RELATE_SHEET', 'partner_ids', dataSource='@res_partner', multi=True, desc='Contacts invited.'),
        F('Attendee Users', 'USER_PICKER', 'x_calendar__attendee_user_ids', extra={'userPermission': 1, 'enumDefault': 1},
          desc='Colleagues invited (Odoo invites users through their contacts).'),
        F('Location', 'TEXT', 'location'),
        F('Meeting URL', 'TEXT', 'videocall_location', advanced_setting={'analysislink': '1'}),
        F('Description', 'RICH_TEXT', 'description'),
        F('Privacy', 'DROP_DOWN', 'privacy', options=['Public', 'Private', 'Only internal users']),
        F('Show as', 'DROP_DOWN', 'show_as', options=['Busy', 'Available'], defaultValue=[{'source': 'static', 'value': 'Busy'}]),
        F('Document Model', 'TEXT', 'res_model', desc='Sheet of the record this meeting is about, for example Leads.'),
        F('Document ID', 'TEXT', 'res_id', desc='Record id of that record.'),
    ],
}
CRM_TAGS = [('Product', 1), ('Software', 2), ('Services', 3), ('Information', 4), ('Design', 5), ('Training', 6),
            ('Consulting', 7), ('Other', 8)]
UTM_TAGS = [('Marketing', 1)]
MEETING_TAGS = [('Customer Meeting', 5), ('Internal Meeting', 5), ('Off-site Meeting', 2), ('Open Discussion', 8),
                ('Feedback Meeting', 10)]


def groups():
    secs = sections_flat()
    top = {s['name']: s for s in secs if s['parent'] is None}
    for name, _ in TOP:
        if name not in top:
            hap('app', 'add-section', APP, '-n', name)
    secs = sections_flat()
    top = {s['name']: s for s in secs if s['parent'] is None}
    if not any(s['parent'] == top['CRM']['id'] and s['name'] == 'Configuration' for s in secs):
        hap('app', 'add-section', APP, '-n', 'Configuration', '--parent-id', top['CRM']['id'])
    secs = sections_flat()
    top = {s['name']: s for s in secs if s['parent'] is None}
    order = [top[n]['id'] for n, _ in TOP] + [s['id'] for s in secs if s['parent'] is None and s['name'] not in dict(TOP)]
    if [s['id'] for s in secs if s['parent'] is None] != order:
        hap('app', 'sort-sections', APP, *order)
    record(top['CRM']['id'], 'group', 'CRM', 'crm', STEP)
    record(top['Link Tracker']['id'], 'group', 'Link Tracker', 'utm', STEP)
    conf = next(s for s in sections_flat() if s['parent'] == top['CRM']['id'] and s['name'] == 'Configuration')
    record(conf['id'], 'group', 'CRM › Configuration', 'crm', STEP)
    return [s['name'] for s in sections_flat() if s['parent'] is None]


def tag_field(ws, name, alias, set_id, opts, module, label):
    return add_once(ws, {'type': 10, 'controlName': name, 'alias': alias, 'dataSource': set_id, 'enumDefault2': 1,
                         'options': [{'key': o['key'], 'value': o['value'], 'index': o.get('index', 1), 'color': o.get('color', '')}
                                     for o in opts],
                         'advancedSetting': {'checktype': '1', 'allowadd': '1'}}, module, label, STEP)


def add_option(ws, alias, label):
    """Append one option to a single-select field (keeps the existing keys). The new option needs its own key:
    field.update stores an option sent without one with an empty key (PLATFORM-ISSUES P39)."""
    import uuid
    c = by_alias(ws)[alias]
    opts = c.get('options') or []
    if any(o['value'] == label for o in opts):
        return False
    new = [dict(o) for o in opts] + [{'key': str(uuid.uuid4()), 'value': label,
                                      'index': max([o.get('index', 0) for o in opts] + [0]) + 1,
                                      'isDeleted': False, 'color': '#2196F3'}]
    apply_spec([{'type': 'field.update', 'worksheet': ws, 'field': c['controlId'], 'set': {'options': new}}])
    return True


if __name__ == '__main__':
    print('groups:', groups())
    crm_tags = optionset('CRM Tags', [(n, ODOO_COLOURS[c]) for n, c in CRM_TAGS], 'sales_team', STEP)
    utm_tags = optionset('UTM Tags', [(n, ODOO_COLOURS[c]) for n, c in UTM_TAGS], 'utm', STEP)
    meeting_tags = optionset('Meeting Tags', [(n, ODOO_COLOURS[c]) for n, c in MEETING_TAGS], 'calendar', STEP)
    print('option sets:', crm_tags[0], utm_tags[0], meeting_tags[0])

    made = {}
    for spec in (UTM_STAGES, MEDIUMS, SOURCES, CAMPAIGNS, TEAMS, STAGES, LOST, LEADS, MEETINGS):
        ws, raw, fixes = ensure_sheet(spec, STEP)
        made[spec['alias']] = ws
        print(f"{spec['name']}: {ws}, {len(raw)} fields, alias fixes {fixes}")
    refresh()
    L, C, A, PL = S['crm_lead'], S['res_partner'], S['mail_activity'], S['x_mail__plan_launch']

    # option-set fields
    tag_field(S['utm_campaign'], 'Tags', 'tag_ids', utm_tags[0], utm_tags[1], 'utm', 'Campaigns.Tags')
    tag_field(L, 'Tags', 'tag_ids', crm_tags[0], crm_tags[1], 'crm', 'Leads / Opportunities.Tags')
    tag_field(S['calendar_event'], 'Tags', 'categ_ids', meeting_tags[0], meeting_tags[1], 'calendar', 'Meetings.Tags')

    # hidden company fields (one company for now, as in wave 0)
    for sheet, module, label in (('crm_team', 'sales_team', 'Sales Teams.Company'), ('crm_lead', 'crm', 'Leads / Opportunities.Company')):
        add_once(S[sheet], {'type': 29, 'controlName': 'Company', 'alias': 'company_id', 'dataSource': S['res_company'],
                            'enumDefault': 1, 'fieldPermission': HIDDEN, 'advancedSetting': {'showtype': '3'},
                            'desc': 'Hidden while there is one company.'}, module, label, STEP)

    # prorated revenue: native number formula
    lf = by_alias(L)
    add_once(L, {'type': 31, 'controlName': 'Prorated Revenue', 'alias': 'prorated_revenue',
                 'dataSource': f"${lf['expected_revenue']['controlId']}$*${lf['probability']['controlId']}$/100",
                 'enumDefault': 1, 'dot': 2, 'advancedSetting': {'prefix': 'RM', 'nullzero': '1', 'roundtype': '2', 'thousandth': '1'},
                 'desc': 'Expected revenue × probability.'}, 'crm', 'Leads / Opportunities.Prorated Revenue', STEP)

    # two-way relations, reverse sides named as in Odoo where Odoo has the field
    print('Contacts.Opportunities', pair(L, 'partner_id', C, 'opportunity_ids', 'Opportunities', 'crm', STEP)['controlId'])
    print('Sales Teams.Opportunities', pair(L, 'team_id', S['crm_team'], 'x_crm__lead_ids', 'Opportunities', 'crm', STEP)['controlId'])
    print('Lost Reasons.Leads', pair(L, 'lost_reason_id', S['crm_lost_reason'], 'x_crm__lead_ids', 'Leads', 'crm', STEP)['controlId'])
    print('Campaigns.Leads', pair(L, 'campaign_id', S['utm_campaign'], 'x_crm__lead_ids', 'Leads', 'crm', STEP)['controlId'])

    # counts (rollups without a filter; the filtered opportunity count on Contacts is made in the designer)
    for sheet, rel, alias, name, desc in (
            ('crm_lost_reason', 'x_crm__lead_ids', 'leads_count', 'Leads Count', 'Leads and opportunities lost for this reason, archived ones included.'),
            ('utm_campaign', 'x_crm__lead_ids', 'crm_lead_count', 'Leads Count', 'Leads and opportunities of this campaign.')):
        r = by_alias(S[sheet])[rel]
        add_once(S[sheet], {'type': 37, 'controlName': name, 'alias': alias, 'enumDefault': 6, 'enumDefault2': 6, 'dot': 0,
                            'dataSource': f"${r['controlId']}$", 'sourceControlId': '', 'desc': desc},
                 'crm', f'{sheet}.{name}', STEP)

    # Activities and Plan Launches: the lead link (owned by crm), two-way
    add_once(A, {'type': 29, 'controlName': 'Lead / Opportunity', 'alias': 'x_crm__lead_id', 'dataSource': L, 'enumDefault': 1,
                 'advancedSetting': {'showtype': '3'}, 'desc': 'The lead or opportunity this activity is about.'},
             'crm', 'Activities.Lead / Opportunity', STEP)
    ra = pair(A, 'x_crm__lead_id', L, 'activity_ids', 'Activities', 'crm', STEP)
    a = by_alias(A)
    set_show(L, ra['controlId'], [a[k]['controlId'] for k in ('summary', 'activity_type_id', 'date_deadline', 'user_id', 'x_mail__state')])
    add_once(PL, {'type': 29, 'controlName': 'Lead / Opportunity', 'alias': 'x_crm__lead_id', 'dataSource': L, 'enumDefault': 1,
                  'advancedSetting': {'showtype': '3'}, 'desc': 'The lead or opportunity the plan is launched on.'},
             'crm', 'Plan Launches.Lead / Opportunity', STEP)
    rp = pair(PL, 'x_crm__lead_id', L, 'x_crm__plan_launch_ids', 'Plan Launches', 'crm', STEP)

    # Meetings: the opportunity link (Odoo's calendar.event.opportunity_id, owned by crm), two-way
    M = S['calendar_event']
    add_once(M, {'type': 29, 'controlName': 'Opportunity', 'alias': 'opportunity_id', 'dataSource': L, 'enumDefault': 1,
                 'advancedSetting': {'showtype': '3'}, 'desc': 'The lead or opportunity this meeting is about.'},
             'crm', 'Meetings.Opportunity', STEP)
    rm = pair(M, 'opportunity_id', L, 'calendar_event_ids', 'Meetings', 'crm', STEP)
    m = by_alias(M)
    set_show(L, rm['controlId'], [m[k]['controlId'] for k in ('name', 'start', 'stop', 'user_id')])

    # "Leads" in Applies to of Activity Types and Activity Plans
    for sheet in ('mail_activity_type', 'mail_activity_plan'):
        print(sheet, 'Leads option added' if add_option(S[sheet], 'res_model', 'Leads') else 'Leads option already there')

    print('Leads fields:', len(by_alias(L)), '| Meetings fields:', len(by_alias(M)))
