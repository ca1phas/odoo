"""CRM Phase A, step 4: business rules on Leads / Opportunities.

  R-a  Lost reason when archived     Lost Reason and Closing Note show only on an archived record (Odoo form:
                                     lost_reason_id invisible="active"). Kept but turned OFF (24 Nov 2026): rules also
                                     apply inside a button dialog, and the Lost button's dialog is opened on an active
                                     record, so the rule emptied the dialog. Both fields now always show on the form.
  R-b  Name or customer              the form refuses a record with neither a name nor a customer (Odoo: name is
                                     required, and _compute_name fills it from the customer); form only, so flows and
                                     the public form are not affected
Run: python step4_rules.py
"""
import json
from crmlib import *  # noqa: F401,F403

STEP = 'crm step 4'


def rules(ws):
    d = hap('worksheet', 'rules', ws)
    d = d.get('data', d) if isinstance(d, dict) else d
    return d if isinstance(d, list) else (d.get('rules') or [])


def save(ws, name, type_, filters, items, *extra):
    have = next((r for r in rules(ws) if r.get('name') == name), None)
    if have:
        return have.get('ruleId') or have.get('id')
    r = hap('worksheet', 'save-rule', ws, '--name', name, '--type', str(type_),
            '--filters', json.dumps(filters, ensure_ascii=False), '--rule-items', json.dumps(items, ensure_ascii=False), *extra)
    r = r.get('data', r) if isinstance(r, dict) else r
    rid = (r.get('ruleId') or r.get('id')) if isinstance(r, dict) else r
    if not rid:
        rid = next((x.get('ruleId') or x.get('id') for x in rules(ws) if x.get('name') == name), None)
    record(rid, 'rule', f'Leads / Opportunities.{name}', 'crm', STEP)
    return rid


if __name__ == '__main__':
    refresh()
    L = S['crm_lead']
    f = lambda a: F('crm_lead', a)
    a = save(L, 'Lost reason when archived', 0,
             {'logic': 'and', 'items': [{'field': f('active'), 'op': 'ne', 'value': '1'}]},
             [{'action': 'show', 'fields': [f('lost_reason_id'), f('x_crm__lost_feedback')]}], '--disabled')
    b = save(L, 'Name or customer', 1,
             {'logic': 'and', 'items': [{'field': f('name'), 'op': 'empty'}, {'field': f('partner_id'), 'op': 'empty'}]},
             [{'action': 'error', 'fields': [f('name')], 'message': 'Give the opportunity a name, or choose a customer.'}],
             '--check-type', '0')
    print('rules:', a, b)
    for r in rules(L):
        print(' ', r.get('name'), json.dumps(r.get('filters') or r.get('filterControls'), ensure_ascii=False)[:300])
