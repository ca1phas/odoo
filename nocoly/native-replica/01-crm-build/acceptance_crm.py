"""CRM Phase A acceptance tests (01-crm.md §9), the readback part, with TEST records deleted at the end.
UI parts (tests 1, 9, 12 button, 16, 17, the dialogs) are checked in the browser and noted in BUILD-LOG.md.

Buttons are run the way wave 0 ran its dialog buttons: the dialog fields are written, then the button's flow is
triggered on the record (`workflow trigger -s`), which is what pressing it does.
Run: python acceptance_crm.py   |   python acceptance_crm.py cleanup
"""
import datetime, json, os, sys, time
from crmlib import *  # noqa: F401,F403
from step2_seed import ME
import acceptance_crm_core as core
from acceptance_crm_core import create, update, get, val, expect, team_id, stage_id

core.IDS = os.path.join(HERE, 'backups', 'test-crm-acceptance.json')


def _update(sheet, rid, fields):
    """Writes as a workflow or custom action does (--ignore-rules): the CLI's own range check on the Stage relation
    cannot evaluate the "Sales Teams is empty" half of its limit and refuses valid stages (PLATFORM-ISSUES P40)."""
    return hap('worksheet', 'record', 'update', S[sheet], rid, '-a', APP, '--ignore-rules',
               '--fields-json', json.dumps(fields, ensure_ascii=False))


core.update = _update
update = _update
core.IGNORE_RULES = True
L, C = 'crm_lead', 'res_partner'
set_ = lambda v: bool(v)
is0 = lambda v: v in ('', '0', '0.00')


def button_flow(name):
    o = next(v for k, v in ledger()['objects'].items() if v['type'] == 'button' and v['name'] == f'{L}.{name}')
    return o['note'].split('process ')[-1]


def press(name, rid):
    return hap('workflow', 'trigger', button_flow(name), '-s', rid, ok_fail=True)


def key(sheet, alias, label):
    return option_key(sheet, alias, label)


def row_by(sheet, field, value):
    rows = unwrap(hap('worksheet', 'record', 'list', S[sheet], '-a', APP, '-n', '200', '--fields', field))['rows']
    return next((r['rowId'] for r in rows if r.get(field) == value), None)


def main():
    refresh()
    opp = [key(L, 'type', 'Opportunity')]
    lead = [key(L, 'type', 'Lead')]
    # 2, 3: customer details and e-mail back to the customer
    pc = create(C, [{'id': 'name', 'value': 'TEST CRM Acc Customer'}, {'id': 'email', 'value': 'test.acc@example.com'},
                    {'id': 'phone', 'value': '+60122222222'}, {'id': 'city', 'value': 'Penang'}, {'id': 'street', 'value': '2 Lebuh Test'},
                    {'id': 'x_base__region', 'value': 'MY|MY-07'}])
    time.sleep(8)
    o2 = create(L, [{'id': 'partner_id', 'value': [pc]}])
    expect('2 customer details', L, o2, {'name': "TEST CRM Acc Customer's opportunity", 'contact_name': 'TEST CRM Acc Customer',
                                         'email_from': 'test.acc@example.com', 'city': 'Penang', 'street': '2 Lebuh Test',
                                         'country_id': 'Malaysia', 'lang_id': 'English', 'phone': lambda v: v.endswith('122222222')})
    update(L, o2, [{'id': 'email_from', 'value': 'test.acc.changed@example.com'}])
    expect('3 e-mail to the customer', C, pc, {'email': 'test.acc.changed@example.com'})
    # 4: won stage and back (the "drag")
    update(L, o2, [{'id': 'stage_id', 'value': [stage_id('Won')]}])
    expect('4a won stage', L, o2, {'probability': lambda v: v.startswith('100'), 'won_status': 'Won', 'date_closed': set_})
    update(L, o2, [{'id': 'stage_id', 'value': [stage_id('Qualified')]}])
    expect('4b back to Qualified', L, o2, {'won_status': 'Pending', 'date_closed': lambda v: not v})
    # 5: Won button in Proposition
    o5 = create(L, [{'id': 'name', 'value': 'TEST CRM 5 won button'}, {'id': 'stage_id', 'value': [stage_id('Proposition')]},
                    {'id': 'probability', 'value': 40}])
    time.sleep(10)
    press('Won', o5)
    expect('5 Won button', L, o5, {'stage_id': 'Won', 'probability': lambda v: v.startswith('100'), 'won_status': 'Won', 'date_closed': set_})
    # 6: Lost with reason and note, then Restore
    o6 = create(L, [{'id': 'name', 'value': 'TEST CRM 6 lost'}, {'id': 'probability', 'value': 30}])
    time.sleep(10)
    update(L, o6, [{'id': 'lost_reason_id', 'value': [row_by('crm_lost_reason', 'name', 'Too expensive')]},
                   {'id': 'x_crm__lost_feedback', 'value': 'TEST: price too high'}])
    press('Lost', o6)
    expect('6a Lost button', L, o6, {'active': '0', 'probability': is0, 'automated_probability': is0, 'won_status': 'Lost',
                                     'lost_reason_id': 'Too expensive', 'x_crm__lost_feedback': 'TEST: price too high', 'date_closed': set_})
    press('Restore', o6)
    expect('6b Restore button', L, o6, {'active': '1', 'lost_reason_id': '', 'won_status': 'Pending', 'probability': is0,
                                        'x_crm__lost_feedback': 'TEST: price too high'})
    # 7: prorated revenue
    o7 = create(L, [{'id': 'name', 'value': 'TEST CRM 7 prorated'}, {'id': 'expected_revenue', 'value': 10000}, {'id': 'probability', 'value': 50}])
    expect('7 prorated revenue', L, o7, {'prorated_revenue': lambda v: v.replace(',', '').startswith('5000')})
    # 8: convert to opportunity: (a) contact with the same e-mail, (b) new contact from the contact name, (c) new contact named after the lead
    ca = create(C, [{'id': 'name', 'value': 'TEST CRM Convert Match'}, {'id': 'email', 'value': 'test.convert.match@example.com'}])
    la = create(L, [{'id': 'name', 'value': 'TEST CRM 8a'}, {'id': 'type', 'value': lead}, {'id': 'email_from', 'value': 'test.convert.match@example.com'}])
    lb = create(L, [{'id': 'name', 'value': 'TEST CRM 8b'}, {'id': 'type', 'value': lead}, {'id': 'email_from', 'value': 'test.convert.new@example.com'},
                    {'id': 'contact_name', 'value': 'TEST CRM Convert Person'}])
    lc = create(L, [{'id': 'name', 'value': 'TEST CRM 8c no e-mail'}, {'id': 'type', 'value': lead}])
    time.sleep(10)
    for rid in (la, lb, lc):
        press('Convert to Opportunity', rid)
    expect('8a convert: matching contact', L, la, {'type': 'Opportunity', 'date_conversion': set_, 'partner_id': 'TEST CRM Convert Match', 'stage_id': set_})
    expect('8b convert: new contact', L, lb, {'type': 'Opportunity', 'date_conversion': set_, 'partner_id': lambda v: 'TEST CRM Convert Person' in v})
    expect('8c convert: contact named after the lead', L, lc, {'type': 'Opportunity', 'partner_id': lambda v: 'TEST CRM 8c no e-mail' in v})
    for name in ('TEST CRM Convert Person', 'TEST CRM 8c no e-mail'):   # contacts the flow made: delete them in cleanup too
        rid = row_by(C, 'name', name)
        if rid:
            ids = json.load(open(core.IDS)); ids.append([C, rid]); json.dump(ids, open(core.IDS, 'w'))
    # 10: rotting
    o10 = create(L, [{'id': 'name', 'value': 'TEST CRM 10 rotting'}, {'id': 'stage_id', 'value': [stage_id('Proposition')]}])
    time.sleep(12)
    six = (datetime.datetime.now() - datetime.timedelta(days=6, hours=1)).strftime('%Y-%m-%d %H:%M:%S')
    hap('worksheet', 'record', 'update', S[L], o10, '-a', APP, '--ignore-rules', '--fields-json',
        json.dumps([{'id': 'date_last_stage_update', 'value': six}]))
    time.sleep(4)
    hap('worksheet', 'record', 'update', S[L], o10, '-a', APP, '--ignore-rules', '--fields-json',
        json.dumps([{'id': 'x_crm__refresh', 'value': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]))
    expect('10a rotting after 6 days in Proposition', L, o10, {'is_rotting': '1', 'rotting_days': '6'})
    update(L, o10, [{'id': 'stage_id', 'value': [stage_id('Qualified')]}])
    expect('10b stage change: not rotting', L, o10, {'is_rotting': '0', 'rotting_days': is0})
    # 11: an activity added from the lead (lead link only) gets its document fields; next activity date; plan launch
    due = (datetime.date.today() + datetime.timedelta(days=3)).isoformat()
    a11 = create('mail_activity', [{'id': 'summary', 'value': 'TEST CRM 11 call'}, {'id': 'date_deadline', 'value': due},
                                   {'id': 'user_id', 'value': [ME]}, {'id': 'x_crm__lead_id', 'value': [o7]}])
    expect('11a activity document fields', 'mail_activity', a11, {'res_model': 'Leads', 'res_id': o7, 'res_name': 'TEST CRM 7 prorated'})
    expect('11b next activity date on the lead', L, o7, {'activity_date_deadline': lambda v: v.startswith(due)})
    plan = row_by('mail_activity_plan', 'name', 'Onboarding') or unwrap(hap('worksheet', 'record', 'list', S['mail_activity_plan'], '-a', APP, '-n', '5'))['rows'][0]['rowId']
    pl = create('x_mail__plan_launch', [{'id': 'x_mail__plan_id', 'value': [plan]}, {'id': 'x_mail__plan_date', 'value': datetime.date.today().isoformat()},
                                        {'id': 'x_mail__assignee', 'value': [ME]}, {'id': 'x_crm__lead_id', 'value': [o7]}])
    expect('11c plan launched on the lead', 'x_mail__plan_launch', pl, {'x_mail__status': 'Done', 'x_mail__res_model': 'Leads',
                                                                        'x_contacts__partner_id': ''}, timeout=90)
    acts = [r for r in unwrap(hap('worksheet', 'record', 'list', S['mail_activity'], '-a', APP, '-n', '200', '--fields', 'x_mail__plan_launch_id',
                                  '--fields', 'x_crm__lead_id'))['rows'] if val(r.get('x_mail__plan_launch_id'))]
    mine = [r for r in acts if any(x.get('sid') == pl or x.get('rowid') == pl for x in (r.get('x_mail__plan_launch_id') or []) if isinstance(x, dict))]
    ok = mine and all(val(r.get('x_crm__lead_id')) == 'TEST CRM 7 prorated' for r in mine)
    core.results.append(('11d plan activities linked to the lead', bool(ok), [] if ok else [f'{len(mine)} activities']))
    print(f"11d plan activities linked to the lead: {'PASS' if ok else 'FAIL'} ({len(mine)} activities)")
    for r in mine:
        ids = json.load(open(core.IDS)); ids.append(['mail_activity', r['rowId']]); json.dump(ids, open(core.IDS, 'w'))
    # 12: a meeting on the opportunity: duration, next meeting
    start = (datetime.datetime.now() + datetime.timedelta(days=2)).replace(hour=10, minute=0, second=0)
    m12 = create('calendar_event', [{'id': 'name', 'value': 'TEST CRM 12 meeting'}, {'id': 'start', 'value': start.strftime('%Y-%m-%d %H:%M:%S')},
                                    {'id': 'stop', 'value': (start + datetime.timedelta(hours=1, minutes=30)).strftime('%Y-%m-%d %H:%M:%S')},
                                    {'id': 'opportunity_id', 'value': [o7]}])
    expect('12a meeting duration', 'calendar_event', m12, {'duration': lambda v: v.startswith('1.5')})
    expect('12b next meeting on the opportunity', L, o7, {'meeting_display_label': 'Next Meeting',
                                                          'meeting_display_date': lambda v: v.startswith(start.date().isoformat())}, timeout=90)
    # 14: unique UTM names
    st = row_by('utm_stage', 'name', 'New')
    c1 = create('utm_campaign', [{'id': 'title', 'value': 'TEST Promo'}, {'id': 'stage_id', 'value': [st]}, {'id': 'user_id', 'value': [ME]}])
    expect('14a campaign identifier from the name', 'utm_campaign', c1, {'name': 'TEST Promo'})
    c2 = create('utm_campaign', [{'id': 'title', 'value': 'TEST Promo'}, {'id': 'stage_id', 'value': [st]}, {'id': 'user_id', 'value': [ME]}])
    expect('14b second campaign identifier', 'utm_campaign', c2, {'name': 'TEST Promo [2]'})
    for sheet in ('utm_medium', 'utm_source'):
        # one after the other, as people add them: two creates in the same second race (each flow sees the other)
        a = create(sheet, [{'id': 'name', 'value': 'TEST Channel'}])
        expect(f'14c {sheet} kept', sheet, a, {'name': 'TEST Channel'})
        time.sleep(10)
        b = create(sheet, [{'id': 'name', 'value': 'TEST Channel'}])
        expect(f'14d {sheet} renamed', sheet, b, {'name': 'TEST Channel [2]'})
    # 15: the salesperson's team, and a stage of one team only
    tt = create('crm_team', [{'id': 'name', 'value': 'TEST Team Pre'}, {'id': 'sequence', 'value': -1}, {'id': 'member_ids', 'value': [ME]},
                             {'id': 'use_opportunities', 'value': '1'}, {'id': 'active', 'value': '1'}])
    ts = create('crm_stage', [{'id': 'name', 'value': 'TEST Team Stage'}, {'id': 'sequence', 'value': 0}, {'id': 'team_ids', 'value': [tt]}])
    o15 = create(L, [{'id': 'name', 'value': 'TEST CRM 15 team'}])
    expect('15a team of the salesperson', L, o15, {'team_id': 'TEST Team Pre', 'stage_id': 'TEST Team Stage'}, timeout=90)
    o15b = create(L, [{'id': 'name', 'value': 'TEST CRM 15 other team'}, {'id': 'team_id', 'value': [team_id('Sales')]}])
    expect('15b another team does not get it', L, o15b, {'team_id': 'Sales', 'stage_id': 'New'})
    update(L, o15, [{'id': 'team_id', 'value': [team_id('Sales')]}])
    expect('15c team changed: stage of the new team', L, o15, {'team_id': 'Sales', 'stage_id': 'New'})
    # Odoo's domain team_ids = team matches a stage whose teams include the team, among others
    create('crm_stage', [{'id': 'name', 'value': 'TEST Shared Stage'}, {'id': 'sequence', 'value': 0},
                         {'id': 'team_ids', 'value': [tt, team_id('Sales')]}])
    o15d = create(L, [{'id': 'name', 'value': 'TEST CRM 15 shared stage'}, {'id': 'team_id', 'value': [team_id('Sales')]}])
    expect('15d stage shared by two teams', L, o15d, {'team_id': 'Sales', 'stage_id': 'TEST Shared Stage'})
    print(f"{sum(1 for r in core.results if r[1])} of {len(core.results)} pass")


if __name__ == '__main__':
    refresh()
    core.cleanup() if sys.argv[1:] == ['cleanup'] else main()
