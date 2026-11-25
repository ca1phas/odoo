"""CRM Phase A, step 4: the CRM reporting page (01-crm.md §5: Odoo's Pipeline / Leads / Activities analysis and the
board's column totals, which HAP boards do not have), native charts on a custom page.
Run: python step4_page.py
"""
import json, secrets
from crmlib import *  # noqa: F401,F403

STEP = 'crm step 4'
PAGE_NAME = 'Reporting'


def page_id():
    for s in sections_flat():
        if s['name'] == 'CRM' and s['parent'] is None:
            for i in s['items']:
                if i.get('type') == 1 and i.get('name') == PAGE_NAME:
                    return i['id'], s['id']
            return None, s['id']


def ensure_page():
    pid, sec = page_id()
    if not pid:
        hap('worksheet', 'create', APP, PAGE_NAME, '--type', '1', '--section-id', sec, '--icon', 'sys_dashboard')
        pid, sec = page_id()
        record(pid, 'page', 'CRM › Reporting', 'crm', STEP)
    return pid


def charts_on(ws):
    d = hap('worksheet', 'chart', 'list', ws, ok_fail=True)
    d = d.get('data', d) if isinstance(d, dict) else d
    return d if isinstance(d, list) else (d.get('reports') or d.get('list') or [])


ALL_TIME = {'filterRangeId': 'ctime', 'filterRangeName': 'Creation Time', 'rangeType': 0, 'rangeValue': None, 'today': False}


def chart(page, sheet, name, rtype, spec):
    """A filter with conditions also needs the time range (the CLI fills it in only when there is no filter)."""
    ws = S[sheet]
    if 'filter' in spec:
        spec = dict(spec, filter=dict(ALL_TIME, **spec['filter']))
    have = next((r for r in charts_on(ws) if r.get('name') == name), None)
    if have:
        return have.get('id') or have.get('reportId'), rtype, ws, name
    r = hap('worksheet', 'chart', 'create', ws, '--name', name, '--report-type', str(rtype), '--page-id', page, '--app-id', APP,
            '-j', json.dumps(spec, ensure_ascii=False))
    r = r.get('data', r) if isinstance(r, dict) else r
    rid = r.get('reportId') or r.get('id')
    record(rid, 'chart', f'CRM › Reporting.{name}', 'crm', STEP)
    return rid, rtype, ws, name


if __name__ == '__main__':
    refresh()
    page = ensure_page()
    L = 'crm_lead'
    f = lambda a: F(L, a)
    k = lambda a, v: option_key(L, a, v)
    count = {'controlId': 'record_count', 'controlName': 'Records', 'controlType': 10000000, 'normType': 5}
    rev = {'controlId': f('expected_revenue'), 'controlType': 8, 'normType': 1}
    open_opps = {'logic': 'and', 'items': [{'field': f('type'), 'op': 'eq', 'value': k('type', 'Opportunity')},
                                           {'field': f('active'), 'op': 'eq', 'value': '1'},
                                           {'field': f('won_status'), 'op': 'eq', 'value': k('won_status', 'Pending')}]}
    tiles = [
        (chart(page, L, 'Open opportunities', 10, {'yaxisList': [count], 'filter': open_opps}), 12, 6),
        (chart(page, L, 'Expected revenue (open)', 10, {'yaxisList': [rev], 'filter': open_opps}), 12, 6),
        (chart(page, L, 'Won / Lost / Pending', 3, {'xaxes': {'controlId': f('won_status'), 'controlType': 11}, 'yaxisList': [count],
                                                    'filter': {'logic': 'and', 'items': [{'field': f('type'), 'op': 'eq', 'value': k('type', 'Opportunity')}]}}), 24, 12),
        (chart(page, L, 'Pipeline funnel (open opportunities by stage)', 6,
               {'xaxes': {'controlId': f('stage_id'), 'controlType': 29}, 'yaxisList': [count], 'filter': open_opps}), 24, 12),
        (chart(page, L, 'Expected revenue by stage', 1,
               {'xaxes': {'controlId': f('stage_id'), 'controlType': 29}, 'yaxisList': [rev, count], 'filter': open_opps}), 24, 12),
        (chart(page, L, 'Forecast: prorated revenue by expected closing month', 1,
               {'xaxes': {'controlId': f('date_deadline'), 'controlType': 15, 'particleSizeType': 3},
                'yaxisList': [{'controlId': f('prorated_revenue'), 'controlType': 31, 'normType': 1}], 'filter': open_opps}), 24, 12),
        (chart(page, L, 'Expected revenue by salesperson', 1,
               {'xaxes': {'controlId': f('user_id'), 'controlType': 26}, 'yaxisList': [rev], 'filter': open_opps}), 24, 12),
        (chart(page, L, 'Leads by source', 3, {'xaxes': {'controlId': f('source_id'), 'controlType': 29}, 'yaxisList': [count]}), 24, 12),
        (chart(page, L, 'Leads by campaign', 1, {'xaxes': {'controlId': f('campaign_id'), 'controlType': 29}, 'yaxisList': [count]}), 24, 12),
        (chart(page, 'mail_activity', 'Activities on leads by type', 1,
               {'xaxes': {'controlId': F('mail_activity', 'activity_type_id'), 'controlType': 29}, 'yaxisList': [count],
                'filter': {'logic': 'and', 'items': [{'field': F('mail_activity', 'res_model'), 'op': 'eq', 'value': 'Leads'},
                                                     {'field': F('mail_activity', 'active'), 'op': 'eq', 'value': '1'}]}}), 24, 12),
    ]
    # Stage charts in stage order: a custom dimension order is stored as sorts = [{<dimension field>: [row ids in order]}]
    # (set once in the chart editor, read back); the CLI has no option for it.
    from step4a_load_reference import rows_of
    stages = sorted(rows_of(S['crm_stage'], 'name', 'sequence', 'is_won'), key=lambda r: float(r.get('sequence') or 0))
    order = [r['rowId'] for r in stages if str(r.get('is_won')) != '1']
    for (rid, rtype, ws, name), _, _ in tiles:
        if name in ('Pipeline funnel (open opportunities by stage)', 'Expected revenue by stage'):
            hap('worksheet', 'chart', 'update', rid, '--app-id', ws, '--name', name, '--report-type', str(rtype),
                '-j', json.dumps({'sorts': [{f('stage_id'): order}]}))
    info = unwrap(hap('custom-page', 'info', page))
    version = info.get('version', 0)
    comps, x, y, rowh = [], 0, 0, 0
    for (rid, rtype, ws, name), w, h in tiles:
        if x + w > 48:
            x, y = 0, y + rowh
            rowh = 0
        comps.append({'type': 1, 'value': rid, 'worksheetId': ws, 'name': name, 'reportType': rtype,
                      'config': {'objectId': secrets.token_hex(16)},
                      'web': {'title': '', 'titleVisible': False, 'visible': True,
                              'layout': {'x': x, 'y': y, 'w': w, 'h': h, 'minW': 2, 'minH': 4}},
                      'mobile': {'title': '', 'titleVisible': False, 'visible': True, 'layout': None}})
        x += w
        rowh = max(rowh, h)
    hap('custom-page', 'save', page, '--version', str(version), '--components', json.dumps(comps, ensure_ascii=False))
    back = unwrap(hap('custom-page', 'info', page))
    print('page', page, 'components', len(back.get('components') or []), 'of', len(comps))
