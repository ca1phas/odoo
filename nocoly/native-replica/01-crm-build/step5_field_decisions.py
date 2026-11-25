"""CRM field decisions for the no-feature-cut check (01-crm.md §5, acceptance test 18).

Every Odoo 20 field that crm, sales_team or utm declare on a model with a HAP sheet is either built (a HAP field
carries its name as alias) or has a decision here. Vocabulary as in wave 0: skip (not needed in HAP, with the reason),
hap (HAP does it its own way), native:<field> (built in another form), later:<module or phase> (comes later).
Run: python step5_field_decisions.py   (writes field-decisions.csv)
"""
import csv, os

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE_B = 'later:crm-phase-b'
REC = (PHASE_B, 'Recurring revenues: phase B (decision 2)')
SCORE = (PHASE_B, 'Predictive lead scoring: phase B (decision 4)')
ASSIGN = (PHASE_B, 'Rule-based assignment: phase B')
BLACKLIST = ('later:mass_mailing', 'Blacklists come with mass mailing and SMS marketing')
ALIAS = ('skip', 'Mail alias: HAP has no inbound e-mail; the public form replaces it (decision 6)')
COLOUR = ('skip', 'Kanban colour index; HAP boards colour cards by an option field')
CURRENCY = ('skip', 'Company currency (MYR); one company')

D = {
    'crm.lead': {
        'duration_tracking': ('skip', "Odoo's time-in-stage tracking; HAP keeps each record's field log"),
        'utm_reference': ('later:mass_mailing', 'Reference to the mailing or event that made the lead; comes with those bridges'),
        'my_activity_date_deadline': ('native:activity_date_deadline', 'Next Activity rollup and the My Activities board'),
        'phone_sanitized': ('skip', 'Normalised phone for duplicates and blacklists; the HAP phone field stores the international number'),
        'phone_formatted': ('skip', 'Display helper'),
        'phone_mobile_search': ('skip', 'Search helper'),
        'phone_sanitized_blacklisted': BLACKLIST, 'phone_blacklisted': BLACKLIST, 'is_blacklisted': BLACKLIST,
        'partner_is_blacklisted': BLACKLIST,
        'email_normalized': ('skip', 'Normalised e-mail for duplicates and blacklists; Similar Leads compares the e-mail'),
        'email_domain_criterion': ('skip', 'Company e-mail domain for duplicates; Similar Leads compares e-mail, customer and phone'),
        'user_company_ids': ('hap', "Companies of the salesperson; one company"),
        'lead_properties': ('skip', 'No per-team dynamic fields in HAP (plan §1)'),
        'color': COLOUR,
        'recurring_revenue': REC, 'recurring_plan': REC, 'recurring_revenue_monthly': REC,
        'recurring_revenue_monthly_prorated': REC, 'recurring_revenue_prorated': REC,
        'company_currency': CURRENCY,
        'date_automation_last': ASSIGN,
        'phone_state': SCORE, 'email_state': SCORE, 'is_automated_probability': SCORE,
        'lang_code': ('skip', 'Display helper of the language; HAP uses a dropdown'),
        'lang_active_count': ('skip', 'Form helper: how many languages are active'),
        'state_id': ('native:x_crm__region', 'The state is part of the native Region field (Address)'),
        'duplicate_lead_count': ('native:duplicate_lead_ids', 'The Similar Leads tab shows the count'),
        'partner_email_update': ('hap', 'Odoo form warning; CRM - E-mail and phone to the customer writes the change'),
        'partner_phone_update': ('hap', 'Odoo form warning; CRM - E-mail and phone to the customer writes the change'),
    },
    'crm.stage': {
        'team_count': ('skip', 'Number of teams, used by Odoo to hide the Teams field; HAP always shows it'),
    },
    'crm.team': {
        'currency_id': CURRENCY,
        'is_membership_multi': ('hap', 'HAP lets a member be in several teams'),
        'member_company_ids': ('hap', 'One company'),
        'member_warning': ('skip', 'Odoo form warning about members in other teams'),
        'crm_team_member_ids': ASSIGN, 'crm_team_member_all_ids': ASSIGN,
        'color': COLOUR,
        'favorite_user_ids': ('skip', "Odoo dashboard favourites; HAP has its own favourites"),
        'is_favorite': ('skip', "Odoo dashboard favourites; HAP has its own favourites"),
        'dashboard_button_name': ('skip', 'Dashboard helper'),
        'assignment_enabled': ASSIGN, 'assignment_auto_enabled': ASSIGN, 'assignment_max': ASSIGN, 'assignment_domain': ASSIGN,
        'show_assignment_max': ASSIGN, 'lead_unassigned_count': ASSIGN, 'lead_all_assigned_month_count': ASSIGN,
        'lead_all_assigned_month_exceeded': ASSIGN,
        'opportunity_count': ('native:x_crm__lead_ids', "The team's Opportunities tab shows them"),
        'lead_properties_definition': ('skip', 'No per-team dynamic fields in HAP (plan §1)'),
    },
    'utm.campaign': {
        'is_auto_campaign': ('later:mass_mailing', 'Marks campaigns made automatically by mailings and other apps'),
        'color': COLOUR,
        'use_leads': ('skip', 'Tells Odoo whether to label the count Leads or Opportunities'),
    },
}
for f in ('alias_id', 'alias_name', 'alias_domain_id', 'alias_domain', 'alias_defaults', 'alias_email', 'alias_full_name',
          'alias_model_id', 'alias_force_thread_id', 'alias_parent_model_id', 'alias_parent_thread_id', 'alias_contact',
          'alias_incoming_local', 'alias_bounced_content', 'alias_status'):
    D['crm.team'][f] = ALIAS

if __name__ == '__main__':
    p = os.path.join(HERE, 'field-decisions.csv')
    with open(p, 'w', encoding='utf-8', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['model', 'field', 'decision', 'reason'])
        n = 0
        for model, fields in D.items():
            for field, (decision, reason) in sorted(fields.items()):
                w.writerow([model, field, decision, reason])
                n += 1
    print(n, 'decisions written to', p)
