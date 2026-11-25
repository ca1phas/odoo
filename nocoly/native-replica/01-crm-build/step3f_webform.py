"""CRM Phase A, step 3f: web enquiries from the public form (01-crm.md §4 L12; Odoo website_crm, which a public form
replaces: no inbound mail in HAP).

  W1 CRM - Web enquiry   Leads created by the public form (Creator = "user-publicform", shown as Public Form):
                         type Lead, medium Website, team Website (Odoo website_crm: website team, Website medium; a lead
                         when the lead step is used, decision 1). The source stays empty: Odoo takes it from the visitor's
                         UTM cookies, which a public form does not have.
The public form itself (Edit Form > Extend > Public Form) shows Opportunity (subject), Email, Phone, Notes (message),
Company Name and Contact Name; it was switched on and set in the editor (24 Nov 2026).
Run: python step3f_webform.py
"""
import json
from crmwf import *  # noqa: F401,F403
from crmwf import L, TM
from step3_wf_core import build, done

if __name__ == '__main__':
    refresh()
    M = 'utm_medium'
    nodes = [single('qm', 'Medium Website', M, [fi('qm', F(M, 'name'), 'eq', lit('Website'))]),
             single('qt', 'Team Website', TM, [fi('qt', t('name'), 'eq', lit('Website')), fi('qt', t('active'), 'checked')]),
             upd('w', 'Web enquiry', [{'fieldId': l('type'), 'value': lit(option_key(L, 'type', 'Lead'))},
                                      {'fieldId': l('medium_id'), 'value': rec('qm')},
                                      {'fieldId': l('team_id'), 'value': rec('qt')}])]
    pid, new = build('CRM - Web enquiry',
                     'A lead sent through the public form: type Lead, medium Website, team Website (Odoo website_crm).',
                     nodes, '--trigger-worksheet', S[L], '--trigger-event', 'create',
                     '--trigger-filter', json.dumps({'logic': 'and', 'items': [
                         {'node': 'trigger', 'field': 'caid', 'op': 'eq', 'value': 'user-publicform', 'type': 26}]}))
    names, m, sid = flow_map(pid)
    print('trigger condition:', json.dumps(node_get(pid, sid, 0).get('operateCondition'), ensure_ascii=False)[:500])
    done(pid, 'W1 Web enquiry')
