"""CRM Phase A, step 3b: the buttons on Leads / Opportunities and their flows (01-crm.md §4 L5-L8, L11, L14).

  Won                     action_set_won: the team's first won stage after the current one (else the nearest before),
                          probability 100, Won, closed date; the stage rules flow (F4) runs on the stage change
  Lost (dialog)           crm.lead.lost wizard + action_set_lost: lost reason, closing note, archived, probability and
                          automated probability 0, Lost, closed date
  Restore                 action_restore: active, lost reason cleared, probability = automated probability, Pending
                          (Won when that is 100 in a won stage); closed date cleared when the probability is above 0
  Convert to Opportunity  Odoo 20 action_convert_to_opportunity (no dialog any more): the contact with the same e-mail,
                          else a new contact made from the lead (_create_customer); type Opportunity, conversion date,
                          the team's first stage when there is none (_stage_find without the fold filter)
  Schedule Meeting        a new Meeting linked to the record (createRelatedRecord; finished in the button editor, P38)
  Launch Plan             a new Plan Launch linked to the record (createRelatedRecord; finished in the button editor, P38)
Run: python step3b_buttons.py won lost restore convert related
"""
import json, sys
from crmwf import *  # noqa: F401,F403
from crmwf import L, TM, SG, C
from step3_wf_core import (clear_in, done, name_paths as _np, patch_every_team, raw_only, won_key, PLACEHOLDER)

STEP = 'crm step 3b'
ACTIVE = lambda v: {'field': l('active'), 'op': 'eq', 'value': v}


def button(name, spec, module='crm'):
    """Create the button once (ledger); return (button id, process id)."""
    for oid, o in ledger()['objects'].items():
        if o['type'] == 'button' and o['name'] == f'{L}.{name}':
            return oid, o['note'].split('process ')[-1]
    r = hap('worksheet', 'create-custom-action', S[L], '-a', APP, '--action-spec', json.dumps(dict(spec, name=name), ensure_ascii=False))
    r = r.get('data', r)
    btn, pid = r.get('btnId') or r.get('actionId') or r.get('id'), r.get('processId')
    record(btn, 'button', f'{L}.{name}', module, f'{STEP}; process {pid}')
    if pid:
        record(pid, 'workflow', f'Leads / Opportunities.{name} (button flow)', module, STEP)
    return btn, pid


def built(pid, first_node):
    return first_node in node_ids(pid)[0]


# ---- Won -----------------------------------------------------------------------------------------------------------

def won_query(q, name, team, seq_item, asc):
    """Won stages of every team or of the record's team, with a sequence condition; placeholder = "every team"."""
    base = [fi(q, g('is_won'), 'checked')] + ([seq_item] if seq_item else [])
    if team:
        items = [{'logic': 'and', 'items': base + [fi(q, g('team_ids'), 'eq', fref('trigger', l('team_id')))]},
                 {'logic': 'and', 'items': base + [PLACEHOLDER(q)]}]
        return single(q, name, SG, items, logic='or'), asc
    return single(q, name, SG, base + [PLACEHOLDER(q)]), asc


WON_FIELDS = lambda q: [{'fieldId': l('stage_id'), 'value': rec(q)}, {'fieldId': l('probability'), 'value': lit('100')},
                        {'fieldId': l('automated_probability'), 'value': lit('100')}, {'fieldId': l('active'), 'value': lit('1')},
                        {'fieldId': l('won_status'), 'value': lit(won_key('Won'))}, {'fieldId': l('date_closed'), 'value': NOW}]


def won_chain(p, team, with_stage, st='st'):
    """Odoo: next((s for s in won_stages if s.sequence > current)), else the last with sequence <= current, else any."""
    nodes, queries = [], []
    if with_stage:
        after = fi(f'{p}1', g('sequence'), 'gt', fref(st, g('sequence')))
        before = fi(f'{p}2', g('sequence'), 'lte', fref(st, g('sequence')))
        q1, _ = won_query(f'{p}1', f'Won stage after the current one ({p})', team, after, True)
        q2, _ = won_query(f'{p}2', f'Won stage before the current one ({p})', team, before, False)
        nodes = [q1, branch(f'{p}r1', f'Found after ({p})?', [
            path(f'{p}h1', 'Found', [upd(f'{p}w1', f'Won ({p}1)', WON_FIELDS(f'{p}1'))], result_type='has_data'),
            path(f'{p}n1', 'Not found', [q2, branch(f'{p}r2', f'Found before ({p})?', [
                path(f'{p}h2', 'Found', [upd(f'{p}w2', f'Won ({p}2)', WON_FIELDS(f'{p}2'))], result_type='has_data')], result=True)],
                 result_type='no_data')], result=True)]
        queries = [(q1['name'], True), (q2['name'], False)]
    else:
        q1, _ = won_query(f'{p}1', f'First won stage ({p})', team, None, True)
        nodes = [q1, branch(f'{p}r1', f'Found ({p})?', [
            path(f'{p}h1', 'Found', [upd(f'{p}w1', f'Won ({p}1)', WON_FIELDS(f'{p}1'))], result_type='has_data')], result=True)]
        queries = [(q1['name'], True)]
    return nodes, queries


def won():
    btn, pid = button('Won', {'type': 'triggerWorkflow', 'enableWhen': {'logic': 'and', 'items': [
        ACTIVE('1'), {'field': l('won_status'), 'op': 'ne', 'value': won_key('Won')},
        {'field': l('type'), 'op': 'eq', 'value': option_key(L, 'type', 'Opportunity')}]}})
    ph = [cond('trigger', l('name'), 'not_empty')]
    chains = {k: won_chain(*k, st=f'st{k[0]}') for k in (('a', True, True), ('b', True, False), ('c', False, True), ('d', False, False))}
    if not built(pid, 'Team and stage?'):
        nodes = [branch('ts', 'Team and stage?', [
            path('pa', 'Team and stage', [relation('sta', 'The stage (a)', SG, l('stage_id'))] + chains[('a', True, True)][0], ph),
            path('pb', 'Team, no stage', chains[('b', True, False)][0], ph),
            path('pc', 'Stage, no team', [relation('stc', 'The stage (c)', SG, l('stage_id'))] + chains[('c', False, True)][0], ph),
            path('pd', 'No team, no stage', chains[('d', False, False)][0])])]
        batch_add(pid, nodes)
    rel = lambda sid, f, empty: rel_cond_on(sid, 0, l(f), empty)
    raw_only(pid, 'Team and stage?', 0, lambda sid: [[rel(sid, 'team_id', False), rel(sid, 'stage_id', False)]])
    raw_only(pid, 'Team and stage?', 1, lambda sid: [[rel(sid, 'team_id', False)]])
    raw_only(pid, 'Team and stage?', 2, lambda sid: [[rel(sid, 'stage_id', False)]])
    for nodes, queries in chains.values():
        for qname, asc in queries:
            patch_every_team(pid, qname)
            sort_by(pid, qname, [(g('sequence'), 6, asc), ('ctime', 16, asc)])
    _np(pid, 'Team and stage?', ['Team and stage', 'Team, no stage', 'Stage, no team', 'No team, no stage'])
    return done(pid, 'Won button')


# ---- Lost ----------------------------------------------------------------------------------------------------------

def lost():
    btn, pid = button('Lost', {'type': 'updateCurrentRecord', 'runWorkflowAfterSubmit': True,
                               'updateFields': [l('lost_reason_id'), l('x_crm__lost_feedback')],
                               'enableWhen': {'logic': 'and', 'items': [ACTIVE('1')]}})
    if not built(pid, 'Lost'):
        batch_add(pid, [upd('w', 'Lost', [
            {'fieldId': l('active'), 'value': lit('0')}, {'fieldId': l('probability'), 'value': lit('0')},
            {'fieldId': l('automated_probability'), 'value': lit('0')}, {'fieldId': l('won_status'), 'value': lit(won_key('Lost'))},
            {'fieldId': l('date_closed'), 'value': NOW}])])
    return done(pid, 'Lost button')


# ---- Restore -------------------------------------------------------------------------------------------------------

def restore():
    btn, pid = button('Restore', {'type': 'triggerWorkflow', 'enableWhen': {'logic': 'and', 'items': [ACTIVE('0')]}})
    if not built(pid, 'Restored'):
        batch_add(pid, [
            upd('w', 'Restored', [{'fieldId': l('active'), 'value': lit('1')},
                                  {'fieldId': l('probability'), 'value': ref('trigger', l('automated_probability'))},
                                  {'fieldId': l('won_status'), 'value': lit(won_key('Pending'))}]),
            branch('pb', 'Probability above 0?', [
                path('py', 'Above 0', [upd('wc', 'Closed date cleared', [{'fieldId': l('date_closed'), 'value': NOW}])],
                     [cond('trigger', l('automated_probability'), 'gt', '0')]),
                path('pn', 'Zero', [])]),
            relation('st', 'The stage', SG, l('stage_id')),
            branch('wb', 'Won again?', [
                path('wy', 'Won stage and 100', [upd('ww', 'Won', [{'fieldId': l('won_status'), 'value': lit(won_key('Won'))}])],
                     [cond('st', g('is_won'), 'checked', type=36), cond('trigger', l('automated_probability'), 'eq', '100')]),
                path('wn', 'Pending', [])])])
        clear_in(pid, 'Restored', l('lost_reason_id'), 29)
        clear_in(pid, 'Closed date cleared', l('date_closed'), 16)
        _np(pid, 'Probability above 0?', ['Above 0', 'Zero'])
        _np(pid, 'Won again?', ['Won stage and 100', 'Pending'])
    return done(pid, 'Restore button')


# ---- Convert to Opportunity ------------------------------------------------------------------------------------------

def new_customer(alias, name):
    """_create_customer / _prepare_customer_values: a person named after the contact name (else the lead's name)."""
    return [
        {'nodeAlias': f'{alias}n', 'nodeType': 'compute', 'name': f'Name of the new customer ({alias})',
         'config': {'mode': 'function', 'output_type': 'text',
                    'formula': f'IF(ISBLANK($trigger-{l("contact_name")}$), $trigger-{l("name")}$, $trigger-{l("contact_name")}$)'}},
        {'nodeAlias': alias, 'nodeType': 'create_record', 'name': name, 'config': {'worksheet': S[C], 'fields': [
            {'fieldId': c('name'), 'value': ref(f'{alias}n', 'string_fx_id')},
            {'fieldId': c('company_type'), 'value': lit(option_key(C, 'company_type', 'Person'))},
            {'fieldId': c('type'), 'value': lit(option_key(C, 'type', 'Contact'))},
            {'fieldId': c('email'), 'value': ref('trigger', l('email_from'))},
            {'fieldId': c('phone'), 'value': ref('trigger', l('phone'))},
            {'fieldId': c('function'), 'value': ref('trigger', l('function'))},
            {'fieldId': c('website'), 'value': ref('trigger', l('website'))},
            {'fieldId': c('street'), 'value': ref('trigger', l('street'))},
            {'fieldId': c('street2'), 'value': ref('trigger', l('street2'))},
            {'fieldId': c('zip'), 'value': ref('trigger', l('zip'))},
            {'fieldId': c('city'), 'value': ref('trigger', l('city'))},
            {'fieldId': c('x_base__region'), 'value': ref('trigger', l('x_crm__region'))},
            {'fieldId': c('country_id'), 'value': ref('trigger', l('country_id'))},
            {'fieldId': c('lang'), 'value': ref('trigger', l('lang_id'))},
            {'fieldId': c('user_id'), 'value': ref('trigger', l('user_id'))},
            {'fieldId': c('comment'), 'value': ref('trigger', l('description'))},
            {'fieldId': c('active'), 'value': lit('1')}]}},
        upd(f'{alias}w', f'Customer of the lead ({alias})', [{'fieldId': l('partner_id'), 'value': rec(alias)}])]


def stage_any_fold(p, team):
    """_stage_find(team_id=...) with no fold filter: first stage of every team (or of the team) by sequence."""
    q = f'{p}q'
    if team:
        items = [{'logic': 'and', 'items': [fi(q, g('team_ids'), 'eq', fref('trigger', l('team_id')))]},
                 {'logic': 'and', 'items': [PLACEHOLDER(q)]}]
        node = single(q, f'First stage ({p})', SG, items, logic='or')
    else:
        node = single(q, f'First stage ({p})', SG, [PLACEHOLDER(q)])
    return [node, branch(f'{p}r', f'Stage found ({p})?', [
        path(f'{p}h', 'Found', [upd(f'{p}w', f'Stage ({p})', [{'fieldId': l('stage_id'), 'value': rec(q)}])], result_type='has_data')],
        result=True)], node['name']


def convert():
    btn, pid = button('Convert to Opportunity', {'type': 'triggerWorkflow', 'enableWhen': {'logic': 'and', 'items': [
        ACTIVE('1'), {'field': l('type'), 'op': 'eq', 'value': option_key(L, 'type', 'Lead')}]}})
    ph = [cond('trigger', l('name'), 'not_empty')]
    st_team, q_team = stage_any_fold('t', True)
    st_none, q_none = stage_any_fold('g', False)
    if not built(pid, 'Has a customer?'):
        nodes = [
            branch('cb', 'Has a customer?', [
                path('cy', 'Has a customer', [], ph),
                path('cn', 'No customer', [branch('eb', 'Has an e-mail?', [
                    path('ey', 'Has an e-mail', [
                        single('m', 'Contact with the same e-mail', C, [fi('m', c('email'), 'eq', fref('trigger', l('email_from')))]),
                        branch('mr', 'Matching contact?', [
                            path('mh', 'Found', [upd('mw', 'Customer = the matching contact', [{'fieldId': l('partner_id'), 'value': rec('m')}])],
                                 result_type='has_data'),
                            path('mn', 'Not found', new_customer('nc1', 'New customer from the lead (1)'), result_type='no_data')],
                               result=True)],
                         [cond('trigger', l('email_from'), 'not_empty')]),
                    path('en', 'No e-mail', new_customer('nc2', 'New customer from the lead (2)'))])])]),
            upd('w', 'Opportunity', [{'fieldId': l('type'), 'value': lit(option_key(L, 'type', 'Opportunity'))},
                                     {'fieldId': l('date_conversion'), 'value': NOW}]),
            branch('sb', 'Stage?', [
                path('s1', 'No stage, team', st_team, ph),
                path('s2', 'No stage, no team', st_none, ph),
                path('s3', 'Has a stage', [])])]
        batch_add(pid, nodes)
    rel = lambda sid, f, empty: rel_cond_on(sid, 0, l(f), empty)
    raw_only(pid, 'Has a customer?', 0, lambda sid: [[rel(sid, 'partner_id', False)]])
    raw_only(pid, 'Stage?', 0, lambda sid: [[rel(sid, 'stage_id', True), rel(sid, 'team_id', False)]])
    raw_only(pid, 'Stage?', 1, lambda sid: [[rel(sid, 'stage_id', True)]])
    for q in (q_team, q_none):
        patch_every_team(pid, q)
    _np(pid, 'Has a customer?', ['Has a customer', 'No customer'])
    _np(pid, 'Has an e-mail?', ['Has an e-mail', 'No e-mail'])
    _np(pid, 'Stage?', ['No stage, team', 'No stage, no team', 'Has a stage'])
    return done(pid, 'Convert to Opportunity button')


# ---- related-record buttons (P38: finished in the button editor) -------------------------------------------------------

def related():
    out = {}
    for name, rel_alias in (('Schedule Meeting', 'calendar_event_ids'), ('Launch Plan', 'x_crm__plan_launch_ids')):
        out[name] = button(name, {'type': 'createRelatedRecord', 'relationField': l(rel_alias), 'runWorkflowAfterSubmit': False})
        print(name, out[name])
    return out


if __name__ == '__main__':
    refresh()
    for name in sys.argv[1:]:
        globals()[name]()
