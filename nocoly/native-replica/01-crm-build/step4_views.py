"""CRM Phase A, step 4: views (01-crm.md §5), all native.

Leads / Opportunities: My Pipeline (board by stage, my open opportunities: Odoo's opening screen), Pipeline (everyone's),
Leads (the lead step, decision 1), Forecast (calendar by expected closing), Won, Lost, Rotting, Archived.
Meetings: Calendar. Campaigns: board by UTM stage (Odoo's default campaign view).
Run: python step4_views.py
"""
import json
from crmlib import *  # noqa: F401,F403

STEP = 'crm step 4'


def views_of(sheet):
    d = hap('worksheet', 'view', 'list', S[sheet], '-a', APP)
    d = d.get('data', d) if isinstance(d, dict) else d
    return d if isinstance(d, list) else (d.get('views') or [])


def view(sheet, name, module, *args):
    have = next((v for v in views_of(sheet) if v.get('name') == name), None)
    if have:
        return have.get('viewId') or have.get('id'), 'exists'
    r = hap('worksheet', 'view', 'create', S[sheet], name, '-a', APP, *args)
    r = r.get('data', r) if isinstance(r, dict) else r
    vid = r.get('viewId') or r.get('id')
    if vid:
        record(vid, 'view', f'{sheet}.{name}', module, STEP)
    return vid, 'created'


def spec(**kw):
    return ['--view-spec', json.dumps(kw, ensure_ascii=False)]


if __name__ == '__main__':
    refresh()
    L = 'crm_lead'
    f = lambda a: F(L, a)
    key = lambda a, label: option_key(L, a, label)
    opp, lead = key('type', 'Opportunity'), key('type', 'Lead')
    active = {'field': f('active'), 'op': 'eq', 'value': '1'}
    card = [f(a) for a in ('name', 'partner_id', 'expected_revenue', 'probability', 'priority', 'tag_ids', 'user_id',
                           'activity_date_deadline', 'rotting_days')]
    board = lambda flt: spec(viewType='board', config={'groupField': f('stage_id')}, tableFields=card,
                             sort=[{'fieldId': f('priority'), 'sortType': 2}],
                             quickFilters=[f('user_id'), f('team_id'), f('tag_ids')], filter={'logic': 'and', 'items': flt})
    cols = lambda *a: [f(x) for x in a]
    table = lambda flt, fields, sort=None: spec(viewType='sheet', tableFields=fields, filter={'logic': 'and', 'items': flt},
                                               **({'sort': sort} if sort else {}))
    out = []
    out.append(('My Pipeline', view(L, 'My Pipeline', 'crm', *board([{'field': f('user_id'), 'op': 'self'},
                                                                      {'field': f('type'), 'op': 'eq', 'value': opp}, active]))))
    out.append(('Pipeline', view(L, 'Pipeline', 'crm', *board([{'field': f('type'), 'op': 'eq', 'value': opp}, active]))))
    out.append(('Leads', view(L, 'Leads', 'crm', *table(
        [{'field': f('type'), 'op': 'eq', 'value': lead}, active],
        cols('name', 'partner_name', 'contact_name', 'email_from', 'phone', 'user_id', 'team_id', 'source_id', 'medium_id')))))
    out.append(('Forecast', view(L, 'Forecast', 'crm', '--view-type', 'calendar', '--begin-date', f('date_deadline'), '--filter-json',
                                 json.dumps({'logic': 'and', 'items': [{'field': f('type'), 'op': 'eq', 'value': opp}, active,
                                                                       {'field': f('won_status'), 'op': 'eq', 'value': key('won_status', 'Pending')}]}))))
    common = ('name', 'partner_id', 'expected_revenue', 'user_id', 'team_id', 'stage_id')
    out.append(('Won', view(L, 'Won', 'crm', *table([{'field': f('won_status'), 'op': 'eq', 'value': key('won_status', 'Won')}],
                                                       cols(*common, 'date_closed', 'day_close')))))
    out.append(('Lost', view(L, 'Lost', 'crm', *table([{'field': f('won_status'), 'op': 'eq', 'value': key('won_status', 'Lost')}],
                                                         cols(*common, 'lost_reason_id', 'x_crm__lost_feedback', 'date_closed')))))
    out.append(('Rotting', view(L, 'Rotting', 'crm', *table([{'field': f('is_rotting'), 'op': 'eq', 'value': '1'}, active],
                                                               cols(*common, 'rotting_days', 'date_last_stage_update'),
                                                               [{'fieldId': f('rotting_days'), 'sortType': 2}]))))
    out.append(('Archived', view(L, 'Archived', 'crm', *table([{'field': f('active'), 'op': 'ne', 'value': '1'}],
                                                                 cols(*common, 'won_status', 'lost_reason_id')))))
    M = 'calendar_event'
    out.append(('Meetings Calendar', view(M, 'Calendar', 'calendar', '--view-type', 'calendar', '--begin-date', F(M, 'start'),
                                          '--end-date', F(M, 'stop'))))
    U = 'utm_campaign'
    out.append(('Campaigns board', view(U, 'Campaigns', 'utm', *spec(viewType='board', config={'groupField': F(U, 'stage_id')},
                                                                      tableFields=[F(U, a) for a in ('title', 'user_id', 'tag_ids', 'crm_lead_count')]))))
    for name, r in out:
        print(name, r)
    # Boards: columns in stage order (advancedSetting.navsorts = the related sheet's Sequence, found by setting it once in
    # the view settings) and cards without the title repeated. The view-spec does not carry navsorts.
    seq = F('crm_stage', 'sequence')
    cards = [f(a) for a in ('partner_id', 'expected_revenue', 'probability', 'priority', 'tag_ids', 'user_id', 'activity_date_deadline')]
    for name in ('My Pipeline', 'Pipeline'):
        vid = next(v.get('viewId') or v.get('id') for v in views_of(L) if v.get('name') == name)
        hap('worksheet', 'view', 'update', S[L], vid, '--view-json', json.dumps(
            {'displayControls': cards, 'advancedSetting': {'navsorts': json.dumps([{'controlId': seq, 'isAsc': True}], separators=(',', ':'))}}),
            '--edit-attrs', 'displayControls,advancedSetting', '--edit-ad-keys', 'navsorts')
    U = 'utm_campaign'
    vid = next(v.get('viewId') or v.get('id') for v in views_of(U) if v.get('name') == 'Campaigns')
    hap('worksheet', 'view', 'update', S[U], vid, '--view-json', json.dumps(
        {'displayControls': [F(U, a) for a in ('user_id', 'tag_ids', 'crm_lead_count')],
         'advancedSetting': {'navsorts': json.dumps([{'controlId': F('utm_stage', 'sequence'), 'isAsc': True}], separators=(',', ':'))}}),
        '--edit-attrs', 'displayControls,advancedSetting', '--edit-ad-keys', 'navsorts')
    print('boards: card fields and column order set')

    # Stages: the All list in sequence order, as Odoo lists stages (found with Role Debug, 24 Nov 2026). HAP draws a list
    # from moreSort; sortCid / sortType alone do not change it. sortType 2 = ascending.
    st = S['crm_stage']
    vs = hap('worksheet', 'view', 'list', st, '-a', APP)
    vs = vs.get('data', vs) if isinstance(vs, dict) else vs
    vs = vs if isinstance(vs, list) else vs.get('views', [])
    vid = next((x.get('viewId') or x.get('id')) for x in vs if x.get('name') == 'All')
    info = unwrap(hap('worksheet', 'view', 'info', st, vid, '-a', APP))
    seq = F('crm_stage', 'sequence')
    if not (info.get('moreSort') and info['moreSort'][0].get('controlId') == seq and info['moreSort'][0].get('isAsc')):
        ms = dict((info.get('moreSort') or [{}])[0], controlId=seq, dataType=6, isAsc=True)
        hap('worksheet', 'view', 'update', st, vid, '-a', APP, '--view-json',
            json.dumps({'sortCid': seq, 'sortType': 2, 'moreSort': [ms]}), '--edit-attrs', 'sortCid,sortType,moreSort')
    print('Stages list sorted by sequence')
