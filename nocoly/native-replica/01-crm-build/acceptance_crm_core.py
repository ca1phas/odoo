"""API checks of the lead flows F1-F8 (step3_wf_core.py) with TEST records, deleted at the end.
The UI acceptance tests of 01-crm.md §9 come after the buttons and views; these checks catch flow faults early.

T1 new opportunity, no team or stage        -> team Sales (the build account leads it), stage New, dates, day 0, Pending
T2 customer chosen, no name                 -> name, contact, e-mail, phone, job, website, address, country, language
T3 lead e-mail changed                      -> the customer's e-mail follows
T4 stage Won, then back to New              -> 100 / 100 / Won / closed date; then Pending, closed date cleared
T5 team changed to Pre-Sales                -> the stage New (every team) is kept
T6 salesperson removed, then set again      -> assignment date cleared; set again: date, and team Sales (not a Pre-Sales member)
Run: python acceptance_crm_core.py   |   python acceptance_crm_core.py cleanup
"""
import json, os, sys, time
from crmlib import *  # noqa: F401,F403
from step2_seed import ME

IDS = os.path.join(HERE, 'backups', 'test-crm-core.json')
L, C = 'crm_lead', 'res_partner'
results = []
IGNORE_RULES = True    # write as a workflow does: the CLI's range pre-check on the Stage relation ignores the
                       # "Sales Teams is empty" half of its limit and refuses valid stages (PLATFORM-ISSUES P40)


def create(sheet, fields):
    extra = ['--ignore-rules'] if IGNORE_RULES else []
    r = hap('worksheet', 'record', 'create', S[sheet], '-a', APP, '--fields-json', json.dumps(fields, ensure_ascii=False), *extra)
    r = r.get('data', r) if isinstance(r, dict) else r          # {"resultCode": 1, "data": {"rowid": ...}}
    rid = r.get('rowid') or r.get('rowId')
    if not rid:
        raise RuntimeError(f'create on {sheet} gave no row id: {json.dumps(r, ensure_ascii=False)[:300]}')
    ids = json.load(open(IDS)) if os.path.exists(IDS) else []
    ids.append([sheet, rid])
    json.dump(ids, open(IDS, 'w'))
    return rid


def update(sheet, rid, fields):
    extra = ['--ignore-rules'] if IGNORE_RULES else []
    return hap('worksheet', 'record', 'update', S[sheet], rid, '-a', APP, '--fields-json', json.dumps(fields, ensure_ascii=False), *extra)


def get(sheet, rid):
    return unwrap(hap('worksheet', 'record', 'get', S[sheet], rid, '-a', APP))


def val(v):
    if isinstance(v, list):
        return ', '.join(str(x.get('name') or x.get('value') or x.get('fullname') or '') if isinstance(x, dict) else str(x) for x in v)
    if isinstance(v, dict):
        return v.get('path') or v.get('name') or json.dumps(v, ensure_ascii=False)
    return '' if v is None else str(v)


def wait(sheet, rid, check, timeout=60):
    end = time.time() + timeout
    while True:
        g = get(sheet, rid)
        bad = check(g)
        if not bad or time.time() > end:
            return g, bad
        time.sleep(4)


def expect(test, sheet, rid, wants, timeout=60):
    """wants = {alias: expected text, or a function(text) -> bool}."""
    def check(g):
        return [f'{a}={val(g.get(a))!r}' for a, w in wants.items()
                if not (w(val(g.get(a))) if callable(w) else val(g.get(a)) == w)]
    g, bad = wait(sheet, rid, check, timeout)
    results.append((test, not bad, bad))
    print(f"{test}: {'PASS' if not bad else 'FAIL ' + '; '.join(bad)}")
    return g


def team_id(name):
    return next(r['rowId'] for r in unwrap(hap('worksheet', 'record', 'list', S['crm_team'], '-a', APP, '-n', '50'))['rows'] if r.get('name') == name)


def stage_id(name):
    return next(r['rowId'] for r in unwrap(hap('worksheet', 'record', 'list', S['crm_stage'], '-a', APP, '-n', '50'))['rows'] if r.get('name') == name)


def main():
    refresh()
    set_ = lambda v: bool(v)
    # T1
    o1 = create(L, [{'id': 'name', 'value': 'TEST CRM 1 defaults'}, {'id': 'expected_revenue', 'value': 1000}])
    expect('T1 defaults', L, o1, {'team_id': 'Sales', 'stage_id': 'New', 'date_open': set_, 'date_last_stage_update': set_,
                                  'day_open': lambda v: v in ('0', '0.00'), 'won_status': 'Pending', 'user_id': os.environ.get('HAP_USER_NAME', '')})
    # T2
    pc = create(C, [{'id': 'name', 'value': 'TEST CRM Contact'}, {'id': 'email', 'value': 'test.crm@example.com'},
                    {'id': 'phone', 'value': '+60123456789'}, {'id': 'function', 'value': 'Buyer'},
                    {'id': 'website', 'value': 'https://example.com'}, {'id': 'street', 'value': '1 Jalan Test'},
                    {'id': 'city', 'value': 'Kuala Lumpur'}, {'id': 'zip', 'value': '50000'}, {'id': 'x_base__region', 'value': 'MY|MY-14'}])
    time.sleep(8)   # the Contacts flows fill display name and country first
    o2 = create(L, [{'id': 'partner_id', 'value': [pc]}])
    expect('T2 customer details', L, o2, {
        'name': "TEST CRM Contact's opportunity", 'contact_name': 'TEST CRM Contact', 'email_from': 'test.crm@example.com',
        'phone': lambda v: v.replace(' ', '').endswith('123456789'), 'function': 'Buyer', 'website': 'https://example.com',
        'street': '1 Jalan Test', 'city': 'Kuala Lumpur', 'zip': '50000', 'x_crm__region': set_, 'country_id': 'Malaysia',
        'lang_id': 'English'})
    # T3
    update(L, o2, [{'id': 'email_from', 'value': 'test.crm.new@example.com'}])
    expect('T3 e-mail to the customer', C, pc, {'email': 'test.crm.new@example.com'})
    # T4
    update(L, o1, [{'id': 'stage_id', 'value': [stage_id('Won')]}])
    expect('T4a won stage', L, o1, {'probability': lambda v: v.startswith('100'), 'automated_probability': lambda v: v.startswith('100'),
                                    'won_status': 'Won', 'date_closed': set_, 'day_close': lambda v: v in ('0', '0.00')})
    update(L, o1, [{'id': 'stage_id', 'value': [stage_id('New')]}])
    expect('T4b back to New', L, o1, {'won_status': 'Pending', 'date_closed': lambda v: not v, 'day_close': lambda v: v in ('', '0', '0.00')})
    # T5
    update(L, o1, [{'id': 'team_id', 'value': [team_id('Pre-Sales')]}])
    time.sleep(10)
    expect('T5 team changed, stage kept', L, o1, {'team_id': 'Pre-Sales', 'stage_id': 'New'})
    # T6
    update(L, o1, [{'id': 'user_id', 'value': []}])
    expect('T6a salesperson removed', L, o1, {'date_open': lambda v: not v, 'day_open': lambda v: v in ('', '0', '0.00')})
    update(L, o1, [{'id': 'user_id', 'value': [ME]}])
    expect('T6b salesperson set again', L, o1, {'date_open': set_, 'team_id': 'Sales'})
    print(f"{sum(1 for r in results if r[1])} of {len(results)} pass")


def cleanup():
    ids = json.load(open(IDS)) if os.path.exists(IDS) else []
    for sheet, rid in reversed(ids):
        r = hap('worksheet', 'record', 'delete', S[sheet], '-a', APP, '-y', '--no-trigger-workflow', '--row-ids', rid, ok_fail=True)
        print('deleted', sheet, rid, '' if not (isinstance(r, dict) and r.get('_error')) else r['_error'][:200])
    if os.path.exists(IDS):
        os.remove(IDS)


if __name__ == '__main__':
    refresh()
    cleanup() if sys.argv[1:] == ['cleanup'] else main()
