"""CRM Phase A, step 3d: meetings (01-crm.md §4 L14) and rotting (L10).

HAP formulas have no live "now", so a hidden helper field on the lead, Refreshed At (x_crm__refresh), carries the
time of the last refresh, and one lead flow recomputes from it:
  R1 CRM - Refresh a lead        Leads, Refreshed At changed: next / last meeting (Odoo _compute_meeting_display) and
                                 rotting (mail.tracking.duration.mixin _compute_rotting: pending opportunities whose
                                 stage has Days to Rot > 0 and whose last stage update is older than that)
  M1 Meetings - Duration         Meetings, start / end changed: duration in hours
  M2 CRM - Meeting changed       Meetings with an opportunity, created or changed: refresh that lead
  M3 CRM - Meeting deleted       Meetings with an opportunity, deleted: refresh that lead
  D1 CRM - Daily refresh         every day 00:10: refresh the pending open opportunities, and the leads whose next
                                 meeting has passed (one batch update; R1 then runs per lead)
Run: python step3d_meetings_rotting.py helper r1 m1 m2 m3 d1
"""
import json, sys
from crmwf import *  # noqa: F401,F403
from crmwf import L, SG
from step3_wf_core import build, clear_in, done, INT_DAYS

STEP = 'crm step 3d'
M = 'calendar_event'


def m(f):
    return F(M, f)


def helper():
    c = add_once(S[L], {'type': 16, 'controlName': 'Refreshed At', 'alias': 'x_crm__refresh', 'fieldPermission': HIDDEN,
                        'desc': 'When rotting and the meeting dates were last recomputed (daily, and when a meeting changes). '
                                'Hidden helper.'}, 'crm', 'Leads / Opportunities.Refreshed At', STEP)
    print('helper', c['controlId'])


def r1():
    lead_meetings = lambda q: fi(q, m('opportunity_id'), 'eq', fref('trigger', 'rowid'))
    show = lambda alias, label, date: upd(alias, f'{label}', [
        {'fieldId': l('meeting_display_label'), 'value': lit(label)}] + ([{'fieldId': l('meeting_display_date'), 'value': date}] if date else
                                                                         [{'fieldId': l('meeting_display_date'), 'value': NOW}]))
    nodes = [
        single('nx', 'Next meeting', M, [lead_meetings('nx'), fi('nx', m('start'), 'gt', fref('trigger', l('x_crm__refresh')))]),
        branch('nb', 'A meeting ahead?', [
            path('nh', 'Next meeting', [show('wn', 'Next Meeting', ref('nx', m('start')))], result_type='has_data'),
            path('nn', 'None ahead', [
                single('ls', 'Last meeting', M, [lead_meetings('ls')]),
                branch('lb', 'Any meeting?', [
                    path('lh', 'Last meeting', [show('wl', 'Last Meeting', ref('ls', m('start')))], result_type='has_data'),
                    path('ln', 'No meeting', [show('wo', 'No Meeting', None)], result_type='no_data')], result=True)],
                 result_type='no_data')], result=True),
        branch('rb', 'Can rot?', [
            path('ry', 'Pending open opportunity', [
                relation('st', 'The stage', SG, l('stage_id')),
                {'nodeAlias': 'dd', 'nodeType': 'compute', 'name': 'Days since the last stage change (exact)',
                 'config': {'mode': 'date_diff', 'start': ref('trigger', l('date_last_stage_update')),
                            'end': ref('trigger', l('x_crm__refresh')), 'out_unit': 'day'}},
                {'nodeAlias': 'di', 'nodeType': 'compute', 'name': 'Days since the last stage change',
                 'config': {'mode': 'function', 'output_type': 'text', 'formula': INT_DAYS.format(n='dd')}},
                branch('xb', 'Rotting?', [
                    path('xy', 'Rotting', [upd('wr', 'Rotting', [{'fieldId': l('is_rotting'), 'value': lit('1')},
                                                                 {'fieldId': l('rotting_days'), 'value': ref('di', 'string_fx_id')}])],
                         [cond('st', g('rotting_threshold_days'), 'gt', '0', type=6),
                          {'node': 'dd', 'field': 'number_fx_id', 'op': 'gt', 'type': 6,
                           'value': ref('st', g('rotting_threshold_days'))}]),
                    path('xn', 'Not rotting', [upd('wf', 'Not rotting', [{'fieldId': l('is_rotting'), 'value': lit('0')},
                                                                         {'fieldId': l('rotting_days'), 'value': lit('0')}])])])],
                 [cond('trigger', l('type'), 'eq', option_key(L, 'type', 'Opportunity')),
                  cond('trigger', l('won_status'), 'eq', option_key(L, 'won_status', 'Pending')),
                  cond('trigger', l('active'), 'checked'), cond('trigger', l('date_last_stage_update'), 'not_empty')]),
            path('rn', 'Cannot rot', [upd('wz', 'Not rotting (closed)', [{'fieldId': l('is_rotting'), 'value': lit('0')},
                                                                          {'fieldId': l('rotting_days'), 'value': lit('0')}])])])]
    pid, new = build('CRM - Refresh a lead',
                     'Next or last meeting (Odoo _compute_meeting_display) and rotting (Odoo _compute_rotting): a pending '
                     "open opportunity is rotting when its stage's Days to Rot is above 0 and its last stage change is older. "
                     'Runs when Refreshed At changes: daily, and when one of its meetings changes.',
                     nodes, '--trigger-worksheet', S[L], '--trigger-event', 'update', '--trigger-fields', l('x_crm__refresh'))
    if new:
        clear_in(pid, 'No Meeting', l('meeting_display_date'), 15)
    for q, asc in (('Next meeting', True), ('Last meeting', False)):
        sort_by(pid, q, [(m('start'), 16, asc)])
    patch_path(pid, 'Can rot?', 0, lambda groups: [[x for x in groups[0] if x.get('filedId') != l('stage_id')]
                                                    + [rel_cond(groups[0][0], l('stage_id'), False)]])
    name_paths(pid, 'Can rot?', ['Pending open opportunity', 'Cannot rot'])
    name_paths(pid, 'Rotting?', ['Rotting', 'Not rotting'])
    return done(pid, 'R1 Refresh a lead')


def m1():
    # Minutes, then / 60: a date difference in hours is whole hours only (1.5 h gives 1), and Odoo's duration is a
    # float. The unit is set raw afterwards: hap-cli numbers the units differently from the product (P42).
    nodes = [{'nodeAlias': 'dh', 'nodeType': 'compute', 'name': 'Minutes from start to end',
              'config': {'mode': 'date_diff', 'start': ref('trigger', m('start')), 'end': ref('trigger', m('stop')), 'out_unit': 'day'}},
             {'nodeAlias': 'dt', 'nodeType': 'compute', 'name': 'Duration',
              'config': {'mode': 'function', 'output_type': 'text', 'formula': 'ROUND($dh-number_fx_id$/60, 2)'}},
             upd('w', 'Write the duration', [{'fieldId': m('duration'), 'value': ref('dt', 'string_fx_id')}], sheet=M)]
    pid, new = build('Meetings - Duration', 'Duration in hours from start to end (Odoo calendar.event duration).',
                     nodes, '--trigger-worksheet', S[M], '--trigger-event', 'create_or_update',
                     '--trigger-fields', f"{m('start')},{m('stop')}",
                     '--trigger-filter', json.dumps({'logic': 'and', 'items': [cond('trigger', m('start'), 'not_empty'),
                                                                               cond('trigger', m('stop'), 'not_empty')]}),
                     module='calendar')
    save_compute(pid, 'Minutes from start to end', outUnit=DATE_DIFF_UNITS['minute'])
    return done(pid, 'M1 Meetings - Duration')


def touch(name, event, fields, desc):
    nodes = [relation('ld', 'The lead', L, m('opportunity_id')),
             upd('w', 'Refresh the lead', [{'fieldId': l('x_crm__refresh'), 'value': NOW}], target='ld')]
    args = ['--trigger-worksheet', S[M], '--trigger-event', event] + (['--trigger-fields', fields] if fields else [])
    pid, new = build(name, desc, nodes, *args)
    patch_trigger(pid, lambda sid, groups: [[rel_cond_on(sid, 0, m('opportunity_id'), empty=False)]])
    return pid


def m2():
    pid = touch('CRM - Meeting changed', 'create_or_update', f"{m('start')},{m('opportunity_id')}",
                "A meeting of an opportunity was created or moved: the opportunity's next / last meeting is recomputed.")
    return done(pid, 'M2 Meeting changed')


def m3():
    pid = touch('CRM - Meeting deleted', 'delete', None,
                "A meeting of an opportunity was deleted: the opportunity's next / last meeting is recomputed.")
    return done(pid, 'M3 Meeting deleted')


def d1():
    q = 'up'
    pending = [fi(q, l('active'), 'checked'), fi(q, l('type'), 'eq', lit(option_key(L, 'type', 'Opportunity'))),
               fi(q, l('won_status'), 'eq', lit(option_key(L, 'won_status', 'Pending')))]
    passed = [fi(q, l('meeting_display_label'), 'eq', lit('Next Meeting')),
              fi(q, l('meeting_display_date'), 'lt', {'kind': 'systemField', 'fieldId': 'nowTime'})]
    nodes = [{'nodeAlias': q, 'nodeType': 'query_update', 'name': 'Refresh pending opportunities and passed meetings',
              'config': {'worksheet': S[L], 'filter': {'logic': 'or', 'items': [{'logic': 'and', 'items': pending},
                                                                                  {'logic': 'and', 'items': passed}]},
                         'fields': [{'fieldId': l('x_crm__refresh'), 'value': NOW}]}}]
    pid, new = build('CRM - Daily refresh', 'Every day at 00:10: stamps Refreshed At on the pending open opportunities and on '
                     'the leads whose next meeting has passed; CRM - Refresh a lead then recomputes each of them.',
                     nodes, '--trigger-schedule', json.dumps({'repeat': 'day', 'interval': 1, 'start_time': '2026-11-25 00:10'}),
                     type_='scheduled')
    return done(pid, 'D1 Daily refresh')


if __name__ == '__main__':
    refresh()
    for name in sys.argv[1:]:
        globals()[name]()
        refresh()
