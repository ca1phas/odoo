"""CRM Phase A, step 1b: form layouts for the CRM sheets (01-crm.md §3, rule of 24 Nov: short fields 3-4 per row).

Uses the wave 0 layout engine (../00-foundation-build/step9_form_layouts.py): rows on a 12-column grid, "§ Title"
dividers, relation lists as tabs at the end, read-only workflow fields hidden on the new-record form ("100").
The wave 0 sheets that carry CRM bridge fields (Activities, Plan Launches, Contacts) are laid out with their wave 0
layout plus the CRM field, here, so the wave 0 script never names a CRM field (it would break after a split).
Run: python step1b_layouts.py <sheet alias> [...] | all      (add --dry to only print the plan)
"""
import sys
from crmlib import *  # noqa: F401,F403
import step9_form_layouts as L9

RO = '100'   # read-only, shown on the record, not on the new-record form
NEW = '110'  # editable, not on the new-record form

CRM_LAYOUT = {
    'crm_lead': [
        [('name', 6), ('type', 3), ('priority', 3)],
        [('partner_id', 6), ('expected_revenue', 3), ('probability', 3)],
        [('email_from', 4), ('phone', 4), ('date_deadline', 4)],
        [('user_id', 3), ('team_id', 3), ('stage_id', 3), ('tag_ids', 3)],
        [('won_status', 4), ('lost_reason_id', 4), ('active', 4)],
        [('x_crm__lost_feedback', 12)],
        '§ Notes',
        [('description', 12)],
        '§ Company and contact',
        [('partner_name', 6), ('contact_name', 3), ('function', 3)],
        [('x_crm__region', 6), ('zip', 3), ('city', 3)],
        [('street', 6), ('street2', 6)],
        [('country_id', 3), ('website', 6), ('lang_id', 3)],
        '§ Marketing',
        [('campaign_id', 3), ('medium_id', 3), ('source_id', 3), ('referred', 3)],
        '§ Kept up to date automatically',
        [('prorated_revenue', 3), ('automated_probability', 3), ('date_open', 3), ('date_closed', 3)],
        [('date_last_stage_update', 4), ('date_conversion', 4), ('activity_date_deadline', 4)],
        [('day_open', 4), ('day_close', 4), ('is_rotting', 4)],
        [('rotting_days', 4), ('meeting_display_label', 4), ('meeting_display_date', 4)],
        # tabs, in this order (relation lists and the Similar Leads query show as tabs)
        [('activity_ids', 12)], [('calendar_event_ids', 12)], [('duplicate_lead_ids', 12)], [('x_crm__plan_launch_ids', 12)],
    ],
    'crm_team': [
        [('name', 6), ('user_id', 3), ('sequence', 3)],
        [('member_ids', 12)],
        [('use_leads', 3), ('use_opportunities', 3), ('assignment_optout', 3), ('active', 3)],
    ],
    'crm_stage': [
        [('name', 6), ('sequence', 3), ('is_won', 3)],
        [('team_ids', 9), ('fold', 3)],
        [('rotting_threshold_days', 3), ('requirements', 9)],
    ],
    'crm_lost_reason': [[('name', 6), ('active', 3), ('leads_count', 3)]],
    'utm_campaign': [
        [('title', 6), ('name', 6)],
        [('user_id', 3), ('stage_id', 3), ('active', 3), ('crm_lead_count', 3)],
        [('tag_ids', 12)],
    ],
    'utm_stage': [[('name', 9), ('sequence', 3)]],
    'utm_medium': [[('name', 9), ('active', 3)]],
    'utm_source': [[('name', 12)]],
    'calendar_event': [
        [('name', 6), ('start', 3), ('stop', 3)],
        [('allday', 3), ('duration', 3), ('user_id', 3), ('opportunity_id', 3)],
        [('partner_ids', 6), ('x_calendar__attendee_user_ids', 6)],
        [('location', 6), ('videocall_location', 6)],
        [('categ_ids', 6), ('privacy', 3), ('show_as', 3)],
        [('description', 12)],
        '§ Source',
        [('res_model', 6), ('res_id', 6)],
    ],
}
CRM_NOT_ON_CREATE = {
    'crm_lead': {a: RO for a in ('prorated_revenue', 'automated_probability', 'won_status', 'date_open', 'date_closed', 'date_last_stage_update',
                                 'date_conversion', 'day_open', 'day_close', 'is_rotting', 'rotting_days',
                                 'meeting_display_label', 'meeting_display_date')}
                | {'lost_reason_id': NEW, 'x_crm__lost_feedback': NEW, 'active': NEW, 'activity_date_deadline': RO,
                   'activity_ids': NEW, 'calendar_event_ids': NEW, 'duplicate_lead_ids': NEW, 'x_crm__plan_launch_ids': NEW},
    'calendar_event': {'duration': RO, 'res_model': RO, 'res_id': RO},
    'utm_campaign': {'crm_lead_count': RO},
    'crm_lost_reason': {'leads_count': RO},
}


def with_bridges():
    """Wave 0 layouts of the sheets that carry a CRM field, with that field placed."""
    out = {}
    act = [list(r) if not isinstance(r, str) else r for r in L9.LAYOUT['mail_activity']]
    i = next(n for n, r in enumerate(act) if not isinstance(r, str) and ('x_contacts__partner_id', 6) in r)
    act[i] = [('user_id', 3), ('x_mail__state', 3), ('x_contacts__partner_id', 3), ('x_crm__lead_id', 3)]
    out['mail_activity'] = act
    pl = [list(r) if not isinstance(r, str) else r for r in L9.LAYOUT['x_mail__plan_launch']]
    i = next(n for n, r in enumerate(pl) if not isinstance(r, str) and ('x_contacts__partner_id', 6) in r)
    pl[i] = [('x_contacts__partner_id', 4), ('x_crm__lead_id', 4), ('x_mail__status', 4)]
    out['x_mail__plan_launch'] = pl
    cp = [list(r) if not isinstance(r, str) else r for r in L9.LAYOUT['res_partner']]
    i = next(n for n, r in enumerate(cp) if not isinstance(r, str) and ('complete_name', 4) in r)
    cp[i] = [('complete_name', 3), ('commercial_partner_id', 3), ('commercial_company_name', 3), ('opportunity_count', 3)]
    out['res_partner'] = cp
    return out


def tooltips(alias):
    """Field descriptions as a "?" tooltip beside the label (Odoo's help tooltips), not text under the field, which
    breaks the rows of the form. Raw key advancedSetting.hinttype: "1" = Tooltips (set once in the designer, read back)."""
    ops = []
    for c in L9.controls(S[alias]):
        adv = dict(c.get('advancedSetting') or {})
        if c.get('desc') and adv.get('hinttype') != '1':
            adv['hinttype'] = '1'
            ops.append({'type': 'field.update', 'worksheet': S[alias], 'field': c['controlId'], 'set': {'advancedSetting': adv}})
    for op in ops:
        apply_spec([op])
    return len(ops)


def module_of(alias):
    return {'crm_team': 'sales_team', 'calendar_event': 'calendar'}.get(alias, 'utm' if alias.startswith('utm_') else 'crm')


if __name__ == '__main__':
    refresh()
    L9.LAYOUT.update(CRM_LAYOUT)
    L9.LAYOUT.update(with_bridges())
    for k, v in CRM_NOT_ON_CREATE.items():
        L9.NOT_ON_CREATE.setdefault(k, {}).update(v)
    L9.NOT_ON_CREATE['mail_activity']['x_crm__lead_id'] = '111'
    L9.NOT_ON_CREATE.setdefault('res_partner', {}).update({'opportunity_count': RO, 'opportunity_ids': NEW})
    L9.module_of = module_of
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    names = list(CRM_LAYOUT) + ['mail_activity', 'x_mail__plan_launch'] if args == ['all'] else args
    for n in names:
        if n in CRM_LAYOUT and '--dry' not in sys.argv:
            print(f'  {n}: descriptions as tooltips: {tooltips(n)}')
        L9.apply(n, dry='--dry' in sys.argv)
