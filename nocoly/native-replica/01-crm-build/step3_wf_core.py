"""CRM Phase A, step 3: the lead flows L1-L4 (01-crm.md §4), from Odoo 20 crm/models/crm_lead.py.

  F1 CRM - New lead defaults          create: team from the salesperson, first stage of the team, dates
  F2 CRM - Customer details           customer chosen: company, contact, job, website, e-mail, phone, language, address, name
  F3 CRM - E-mail and phone to the customer   lead e-mail / phone changed: written back to the customer when they differ
  F4 CRM - Stage rules                stage changed: last stage update, won stage = probability 100 / won / closed, else pending
  F5 CRM - Salesperson changes        assignment date; team recomputed when the salesperson is not in it
  F6 CRM - Team changes               stage kept only if it belongs to the team, else the team's first stage
  F7 CRM - Country from Region        lead Region -> Country (as Contacts)
  F8 CRM - Day counters               days from creation to assignment / closing

Odoo rules followed exactly (write(), _compute_*): see 01-crm-build/KNOWLEDGE.md §4. Phase A limit: the automated
probability is not recomputed (predictive lead scoring is phase B), so leaving a won stage keeps the probability.
Relation conditions are patched raw (P22); clears are patched raw (P27); path names are restored (P23).
Run: python step3_wf_core.py f8 f7 f3 f2 f4 ...   (each builds once, patches, publishes, prints the result)
"""
import json, sys
from crmwf import *  # noqa: F401,F403
from crmwf import L, TM, SG, C, K

STEP = 'crm step 3'
INT_DAYS = 'ABS(INT(${n}-number_fx_id$))'


def won_key(label):
    return option_key(L, 'won_status', label)


def clear_in(pid, node_name, field_id, field_type):
    """Replace the placeholder write of `field_id` in an update step by a stored clear (isClear, P27)."""
    names, m, _ = flow_map(pid)
    nid = names[node_name]
    n = node_get(pid, nid, 6)
    cfg = {k: n.get(k) for k in ('name', 'actionId', 'appId', 'appType', 'selectNodeId') if n.get(k) is not None}
    clear = {'fieldId': field_id, 'type': field_type, 'fieldValue': '', 'fieldValueId': '', 'nodeId': '', 'isClear': True, 'addType': 0}
    fields = [clear if f.get('fieldId') == field_id else f for f in n.get('fields') or []]
    if not any(f.get('fieldId') == field_id for f in fields):
        fields.append(clear)   # the step was built without the field: add the clear
    cfg['fields'] = fields
    hap('workflow', 'node', 'save', pid, nid, '--type', '6', '-c', json.dumps(cfg, ensure_ascii=False))
    back = node_get(pid, nid, 6).get('fields') or []
    if not any(f.get('fieldId') == field_id and f.get('isClear') for f in back):
        raise RuntimeError(f'{node_name}: clear of {field_id} not kept')


def build(name, desc, nodes, *trigger, module='crm', type_='worksheet'):
    from wflib import create_flow
    pid = create_flow(name, type_, module, STEP, desc)
    names, _ = node_ids(pid)
    first = nodes[0].get('name')
    if first in names:
        return pid, False
    batch_add(pid, nodes, *trigger)
    return pid, True


def done(pid, label):
    moved = group_filters(pid)   # OR filters of query steps must sit in the grouped slot (P41)
    if moved:
        print(f'{label}: grouped filter slot for {moved}')
    anyof = multi_relation_any(pid)   # "equals" on Sales Teams compares the whole set: use "is any of"
    if anyof:
        print(f'{label}: "is any of" in {anyof}')
    r = publish(pid)
    ok = isinstance(r, dict) and (r.get('isPublish') or (r.get('data') or {}).get('isPublish'))
    print(f'{label}: {pid} {"published" if ok else json.dumps(r, ensure_ascii=False)[:600]}')
    return ok


# ---- F8 ------------------------------------------------------------------------------------------------------------

def f8():
    counters = []
    for key, date_f, day_f, label in (('o', 'date_open', 'day_open', 'Assignment'), ('c', 'date_closed', 'day_close', 'Closed')):
        counters.append(branch(f'{key}b', f'{label} date set?', [
            path(f'{key}y', f'{label} date set', [
                {'nodeAlias': f'{key}d', 'nodeType': 'compute', 'name': f'Days to {label.lower()} (exact)',
                 'config': {'mode': 'date_diff', 'start': ref('trigger', 'ctime'), 'end': ref('trigger', l(date_f)), 'out_unit': 'day'}},
                {'nodeAlias': f'{key}i', 'nodeType': 'compute', 'name': f'Days to {label.lower()}',
                 'config': {'mode': 'function', 'output_type': 'text', 'formula': INT_DAYS.format(n=f'{key}d')}},
                # a function step's result is read as string_fx_id, also into a number field (as in wave 0; number_fx_id
                # from a function step is refused at publish: "step(s) have no valid operation")
                upd(f'{key}w', f'Write days to {label.lower()}', [{'fieldId': l(day_f), 'value': ref(f'{key}i', 'string_fx_id')}])],
                [cond('trigger', l(date_f), 'not_empty')]),
            path(f'{key}n', f'No {label.lower()} date', [
                upd(f'{key}x', f'Clear days to {label.lower()}', [{'fieldId': l(day_f), 'value': lit('0')}])])]))
    pid, new = build('CRM - Day counters', 'Days from creation to assignment and to closing (Odoo day_open, day_close).',
                     counters, '--trigger-worksheet', S[L], '--trigger-event', 'create_or_update',
                     '--trigger-fields', f"{l('date_open')},{l('date_closed')}")
    if new:
        clear_in(pid, 'Clear days to assignment', l('day_open'), 6)
        clear_in(pid, 'Clear days to closed', l('day_close'), 6)
        name_paths(pid, 'Assignment date set?', ['Assignment date set', 'No assignment date'])
        name_paths(pid, 'Closed date set?', ['Closed date set', 'No closed date'])
    return done(pid, 'F8 Day counters')


# ---- F7 ------------------------------------------------------------------------------------------------------------

def f7():
    nodes = [single('q', 'Country of the address', K, [fi('q', F(K, 'x_base__region'), 'contains', fref('trigger', l('x_crm__region')))]),
             upd('w', 'Country from the Region', [{'fieldId': l('country_id'), 'value': rec('q')}])]
    pid, new = build('CRM - Country from Region', "Country = the Countries row whose Region contains the lead's Region; "
                     'runs only when the Region is filled (as Contacts - Country from Region).',
                     nodes, '--trigger-worksheet', S[L], '--trigger-event', 'create_or_update',
                     '--trigger-fields', l('x_crm__region'),
                     '--trigger-filter', json.dumps({'logic': 'and', 'items': [cond('trigger', l('x_crm__region'), 'not_empty')]}))
    return done(pid, 'F7 Country from Region')


# ---- F3 ------------------------------------------------------------------------------------------------------------

def f3():
    nodes = [
        relation('cu', 'The customer', C, l('partner_id')),
        branch('eb', 'E-mail differs?', [
            path('ey', 'E-mail differs', [upd('ew', "Customer's e-mail", [{'fieldId': c('email'), 'value': ref('trigger', l('email_from'))}],
                                              sheet=C, target='cu')],
                 [cond('trigger', l('email_from'), 'ne', ref('cu', c('email')))]),
            path('en', 'Same e-mail', [])]),
        branch('pb', 'Phone differs?', [
            path('py', 'Phone differs', [upd('pw', "Customer's phone", [{'fieldId': c('phone'), 'value': ref('trigger', l('phone'))}],
                                             sheet=C, target='cu')],
                 [cond('trigger', l('phone'), 'ne', ref('cu', c('phone')))]),
            path('pn', 'Same phone', [])]),
    ]
    pid, new = build('CRM - E-mail and phone to the customer',
                     "Editing the lead's e-mail or phone writes it to the customer when they differ (Odoo _inverse_email_from, "
                     '_inverse_phone). Only from the lead to the customer; the other way is the customer flow.',
                     nodes, '--trigger-worksheet', S[L], '--trigger-event', 'update',
                     '--trigger-fields', f"{l('email_from')},{l('phone')}")
    if new:
        patch_trigger(pid, lambda sid, groups: [[rel_cond_on(sid, 0, l('partner_id'), empty=False)]])
        name_paths(pid, 'E-mail differs?', ['E-mail differs', 'Same e-mail'])
        name_paths(pid, 'Phone differs?', ['Phone differs', 'Same phone'])
    return done(pid, 'F3 E-mail and phone to the customer')


# ---- F2 ------------------------------------------------------------------------------------------------------------

def f2():
    def fx(alias, name, formula):
        return {'nodeAlias': alias, 'nodeType': 'compute', 'name': name,
                'config': {'mode': 'function', 'output_type': 'text', 'formula': formula}}
    keep_or = lambda cu_f, lead_f: f'IF(ISBLANK($cu-{c(cu_f)}$), $trigger-{l(lead_f)}$, $cu-{c(cu_f)}$)'
    nodes = [
        relation('cu', 'The customer', C, l('partner_id')),
        fx('pn', 'Company name', keep_or('commercial_company_name', 'partner_name')),
        fx('cn', 'Contact name', f'IF(CONCAT($cu-{c("company_type")}$, "")=="Company", $trigger-{l("contact_name")}$, $cu-{c("name")}$)'),
        fx('fn', 'Job position', keep_or('function', 'function')),
        fx('wb', 'Website', keep_or('website', 'website')),
        fx('em', 'E-mail', keep_or('email', 'email_from')),
        fx('ph', 'Phone', keep_or('phone', 'phone')),
        fx('nm', 'Name', f'IF(ISBLANK($trigger-{l("name")}$), CONCAT($cu-{c("name")}$, "\'s opportunity"), $trigger-{l("name")}$)'),
        upd('w', 'Details from the customer', [
            {'fieldId': l('partner_name'), 'value': ref('pn', 'string_fx_id')},
            {'fieldId': l('contact_name'), 'value': ref('cn', 'string_fx_id')},
            {'fieldId': l('function'), 'value': ref('fn', 'string_fx_id')},
            {'fieldId': l('website'), 'value': ref('wb', 'string_fx_id')},
            {'fieldId': l('email_from'), 'value': ref('em', 'string_fx_id')},
            {'fieldId': l('phone'), 'value': ref('ph', 'string_fx_id')},
            {'fieldId': l('name'), 'value': ref('nm', 'string_fx_id')}]),
        branch('lb', 'Customer has a language?', [
            path('ly', 'Customer has a language', [upd('lw', 'Language from the customer', [{'fieldId': l('lang_id'), 'value': ref('cu', c('lang'))}])],
                 [cond('cu', c('lang'), 'not_empty', type=11)]),   # a condition on a related-record step needs its type
            path('ln', 'No language', [])]),
        branch('ab', 'Customer has an address?', [
            path('ay', 'Customer has an address', [upd('aw', 'Address from the customer', [
                {'fieldId': l('street'), 'value': ref('cu', c('street'))},
                {'fieldId': l('street2'), 'value': ref('cu', c('street2'))},
                {'fieldId': l('zip'), 'value': ref('cu', c('zip'))},
                {'fieldId': l('city'), 'value': ref('cu', c('city'))},
                {'fieldId': l('x_crm__region'), 'value': ref('cu', c('x_base__region'))},
                {'fieldId': l('country_id'), 'value': ref('cu', c('country_id'))}])],
                 [cond('cu', c(f), 'not_empty', type=24 if f == 'x_base__region' else 2) for f in ('street', 'street2', 'zip', 'city', 'x_base__region')], logic='or'),
            path('an', 'No address', [])]),
    ]
    pid, new = build('CRM - Customer details',
                     'Choosing a customer fills in the company name, contact name, job position, website, e-mail, phone, '
                     "language and the whole address (all or none), and names an unnamed lead \"<customer>'s opportunity\" "
                     '(Odoo _compute_partner_name, _compute_contact_name, _compute_partner_address_values, _compute_name ...).',
                     nodes, '--trigger-worksheet', S[L], '--trigger-event', 'create_or_update', '--trigger-fields', l('partner_id'))
    if new:
        patch_trigger(pid, lambda sid, groups: [[rel_cond_on(sid, 0, l('partner_id'), empty=False)]])
        name_paths(pid, 'Customer has a language?', ['Customer has a language', 'No language'])
        name_paths(pid, 'Customer has an address?', ['Customer has an address', 'No address'])
    return done(pid, 'F2 Customer details')


# ---- F4 ------------------------------------------------------------------------------------------------------------

def f4():
    won = lambda: [{'fieldId': l('probability'), 'value': lit('100')}, {'fieldId': l('automated_probability'), 'value': lit('100')},
                   {'fieldId': l('active'), 'value': lit('1')}]
    nodes = [
        relation('st', 'The stage', SG, l('stage_id')),
        upd('w0', 'Stage date', [{'fieldId': l('date_last_stage_update'), 'value': NOW},
                                 {'fieldId': l('is_rotting'), 'value': lit('0')}, {'fieldId': l('rotting_days'), 'value': lit('0')}]),
        branch('wb', 'Won stage?', [
            path('pa', 'Won stage, already won', [upd('wa', 'Still won', won())],
                 [cond('st', g('is_won'), 'checked', type=36), cond('trigger', l('won_status'), 'eq', won_key('Won'))]),
            path('pw', 'Won stage', [upd('ww', 'Won', won() + [{'fieldId': l('won_status'), 'value': lit(won_key('Won'))},
                                                              {'fieldId': l('date_closed'), 'value': NOW}])],
                 [cond('st', g('is_won'), 'checked', type=36)]),
            path('pl', 'Lost (archived, probability 0)', [upd('wl', 'Still lost', [
                {'fieldId': l('won_status'), 'value': lit(won_key('Lost'))}, {'fieldId': l('date_closed'), 'value': NOW}])],
                 [cond('trigger', l('active'), 'unchecked'), cond('trigger', l('probability'), 'eq', '0')]),
            path('pp', 'Other stage', [upd('wp', 'Pending', [
                {'fieldId': l('won_status'), 'value': lit(won_key('Pending'))}, {'fieldId': l('date_closed'), 'value': NOW}])])]),
    ]
    pid, new = build('CRM - Stage rules',
                     'Stage change: last stage update = now, rotting reset; a won stage sets probability and automated '
                     'probability 100, active, Won and the closed date (kept when it was already won); any other stage '
                     'clears the closed date and sets Pending (Lost stays Lost). Odoo crm.lead write(), _compute_won_status.',
                     nodes, '--trigger-worksheet', S[L], '--trigger-event', 'create_or_update', '--trigger-fields', l('stage_id'))
    if new:
        patch_trigger(pid, lambda sid, groups: [[rel_cond_on(sid, 0, l('stage_id'), empty=False)]])
        clear_in(pid, 'Still lost', l('date_closed'), 16)
        clear_in(pid, 'Pending', l('date_closed'), 16)
        name_paths(pid, 'Won stage?', ['Won stage, already won', 'Won stage', 'Lost (archived, probability 0)', 'Other stage'])
    return done(pid, 'F4 Stage rules')


# ---- first stage of a team (Odoo _stage_find(domain=[('fold', '=', False)])) ----------------------------------------
# A stage belongs to every team when its Sales Teams list is empty. "Relation is empty" cannot be written by the CLI
# (P22), so the query is built with a placeholder (stage name is empty: never true, the name is required) that
# patch_every_team() swaps for the stored "Sales Teams is empty" (conditionId 32).

PLACEHOLDER = lambda q: fi(q, g('name'), 'empty')


def team_stage_nodes(p, team_node, target='trigger'):
    q = f'{p}q'
    return [
        # filters are OR-of-AND only: (unfolded and this team) or (unfolded and every team)
        single(q, f'First stage of the team ({p})', SG, [
            {'logic': 'and', 'items': [fi(q, g('fold'), 'unchecked'), fi(q, g('team_ids'), 'eq', fref(team_node, l('team_id')))]},
            {'logic': 'and', 'items': [fi(q, g('fold'), 'unchecked'), PLACEHOLDER(q)]}], logic='or'),
        branch(f'{p}r', f'Stage found ({p})?', [
            path(f'{p}h', 'Found', [upd(f'{p}w', f'Stage of the team ({p})', [{'fieldId': l('stage_id'), 'value': rec(q)}], target=target)],
                 result_type='has_data')], result=True)]


def global_stage_nodes(p, target='trigger'):
    q = f'{p}q'
    return [
        single(q, f'First stage for every team ({p})', SG, [fi(q, g('fold'), 'unchecked'), PLACEHOLDER(q)]),
        branch(f'{p}r', f'Stage found ({p})?', [
            path(f'{p}h', 'Found', [upd(f'{p}w', f'Stage for every team ({p})', [{'fieldId': l('stage_id'), 'value': rec(q)}], target=target)],
                 result_type='has_data')], result=True)]


def patch_every_team(pid, node_name):
    """Swap the placeholder condition of a stage query for "Sales Teams is empty"; sort by sequence, then creation."""
    nid, typ, n = query_conditions(pid, node_name)
    name_f, teams_f = g('name'), g('team_ids')
    changed = 0
    for key in ('conditions', 'filters', 'operateCondition'):
        groups = n.get(key)
        if not isinstance(groups, list):
            continue
        for gr in groups:
            items = gr if isinstance(gr, list) else [gr]
            for x in items:
                if isinstance(x, dict) and x.get('filedId') == name_f:
                    x.update({'filedId': teams_f, 'filedTypeId': 29, 'enumDefault': 2, 'conditionId': '32',
                              'conditionValues': [], 'filedValue': 'Sales Teams'})
                    changed += 1
    if not changed:
        flat = json.dumps({k: n.get(k) for k in ('conditions', 'filters', 'operateCondition')}, ensure_ascii=False)
        if teams_f in flat and '"32"' in flat:
            return   # patched on an earlier run
        raise RuntimeError(f'{node_name}: placeholder not found in {flat[:600]}')
    save_query(pid, nid, typ, n)
    sort_by(pid, node_name, [(g('sequence'), 6, True), ('ctime', 16, True)])
    back = query_conditions(pid, node_name)[2]
    flat = json.dumps({k: back.get(k) for k in ('conditions', 'filters', 'operateCondition')})
    if name_f in flat or teams_f not in flat:
        raise RuntimeError(f'{node_name}: patch not kept')


def raw_only(pid, gateway, idx, conds_fn):
    """Path whose whole condition is raw: conds_fn(start id) -> OR-groups."""
    _, _, sid = flow_map(pid)
    patch_path(pid, gateway, idx, lambda groups: conds_fn(sid))


# ---- F6 ------------------------------------------------------------------------------------------------------------

def f6():
    ph = [cond('trigger', l('name'), 'not_empty')]   # placeholder, replaced by raw relation conditions
    nodes = [
        branch('sb', 'Stage for the new team?', [
            path('p1', 'No stage, no team', global_stage_nodes('g'), ph),
            path('p2', 'No stage', team_stage_nodes('t', 'trigger'), ph),
            path('p3', 'No team: stage kept', [], ph),
            path('p4', 'Check the stage', [
                relation('stc', 'The stage', SG, l('stage_id')),
                branch('fb', 'Stage fits the team?', [
                    path('f1', 'Stage fits the team', [], [cond('stc', g('team_ids'), 'eq', ref('trigger', l('team_id')), type=29)]),
                    path('f2', 'Stage of another team', team_stage_nodes('o', 'trigger'))])])])]
    pid, new = build('CRM - Team changes',
                     "Changing the team keeps the stage only when it is a stage of every team or of this team; otherwise "
                     "(or when there is no stage) the team's first unfolded stage is set (Odoo _compute_stage_id, _stage_find).",
                     nodes, '--trigger-worksheet', S[L], '--trigger-event', 'update', '--trigger-fields', l('team_id'))
    # the patches are idempotent: re-running f6 re-applies them to the built flow
    rel = lambda sid, f, empty: rel_cond_on(sid, 0, l(f), empty)
    raw_only(pid, 'Stage for the new team?', 0, lambda sid: [[rel(sid, 'stage_id', True), rel(sid, 'team_id', True)]])
    raw_only(pid, 'Stage for the new team?', 1, lambda sid: [[rel(sid, 'stage_id', True)]])
    raw_only(pid, 'Stage for the new team?', 2, lambda sid: [[rel(sid, 'team_id', True)]])
    fits = gateway_paths(pid, 'Stage fits the team?')[0]
    if not any(x.get('filedId') == g('team_ids') and str(x.get('conditionId')) == '32' for gr in path_condition(pid, fits) for x in gr):
        patch_path(pid, 'Stage fits the team?', 0,
                   lambda groups: groups + [[rel_cond(groups[0][0], g('team_ids'), empty=True, multi=True)]])
    for q in ('First stage for every team (g)', 'First stage of the team (t)', 'First stage of the team (o)'):
        patch_every_team(pid, q)
    name_paths(pid, 'Stage for the new team?', ['No stage, no team', 'No stage', 'No team: stage kept', 'Check the stage'])
    name_paths(pid, 'Stage fits the team?', ['Stage fits the team', 'Stage of another team'])
    return done(pid, 'F6 Team changes')


# ---- team of a salesperson (Odoo sales_team crm.team._get_default_team_id) ------------------------------------------
# 1-2: the salesperson's active teams (leader or member), those matching the record type first (Leads for a lead,
#      Pipeline for an opportunity), then by sequence; 4-5: any active team, matching ones first.
# Sorting by the switch, descending, puts the matching teams first. crm.team _order = sequence, create_date desc.

def team_nodes(p, flag):
    q1, q2 = f'{p}1', f'{p}2'
    member = fi(q1, t('member_ids'), 'in', fref('trigger', l('user_id')))
    leader = fi(q1, t('user_id'), 'eq', fref('trigger', l('user_id')))
    active = lambda q: fi(q, t('active'), 'checked')
    return [
        single(q1, f"The salesperson's team ({p})", TM, [{'logic': 'and', 'items': [active(q1), member]},
                                                         {'logic': 'and', 'items': [active(q1), leader]}], logic='or'),
        branch(f'{p}r1', f'In a team ({p})?', [
            path(f'{p}h1', 'In a team', [upd(f'{p}w1', f"Team of the salesperson ({p})", [{'fieldId': l('team_id'), 'value': rec(q1)}])],
                 result_type='has_data'),
            path(f'{p}n1', 'In no team', [
                single(q2, f'First active team ({p})', TM, [active(q2)]),
                branch(f'{p}r2', f'Any team ({p})?', [
                    path(f'{p}h2', 'Found', [upd(f'{p}w2', f'First active team ({p}) set', [{'fieldId': l('team_id'), 'value': rec(q2)}])],
                         result_type='has_data')], result=True)],
                 result_type='no_data')], result=True)]


def team_sorts(pid, p, flag):
    for q in (f"The salesperson's team ({p})", f'First active team ({p})'):
        sort_by(pid, q, [(t(flag), 36, False), (t('sequence'), 6, True), ('ctime', 16, False)])


def team_by_type(p):
    """Lead: teams with Leads first; opportunity: teams with Pipeline first."""
    return [branch(f'{p}ty', f'Lead or opportunity ({p})?', [
        path(f'{p}pl', 'Lead', team_nodes(f'{p}l', 'use_leads'), [cond('trigger', l('type'), 'eq', option_key(L, 'type', 'Lead'))]),
        path(f'{p}po', 'Opportunity', team_nodes(f'{p}o', 'use_opportunities'))])]


def team_patches(pid, p):
    team_sorts(pid, f'{p}l', 'use_leads')
    team_sorts(pid, f'{p}o', 'use_opportunities')
    name_paths(pid, f'Lead or opportunity ({p})?', ['Lead', 'Opportunity'])


# ---- F5 ------------------------------------------------------------------------------------------------------------

def f5():
    ph = [cond('trigger', l('name'), 'not_empty')]
    in_team = [cond('tm', t('member_ids'), 'in', ref('trigger', l('user_id')), type=26),
               cond('tm', t('user_id'), 'eq', ref('trigger', l('user_id')), type=26)]
    nodes = [
        branch('ub', 'Salesperson set?', [
            path('un', 'Salesperson removed', [upd('uc', 'Assignment date cleared', [{'fieldId': l('date_open'), 'value': NOW}])],
                 [cond('trigger', l('user_id'), 'empty')]),
            path('us', 'Salesperson set', [
                upd('ud', 'Assignment date', [{'fieldId': l('date_open'), 'value': NOW}]),
                branch('tb', 'Team of the salesperson?', [
                    path('tn', 'No team', team_by_type('a'), ph),
                    path('tt', 'Has a team', [
                        relation('tm', 'The team', TM, l('team_id')),
                        branch('ib', 'Salesperson in the team?', [
                            path('ii', 'In the team', [], in_team, logic='or'),
                            path('io', 'Not in the team', team_by_type('b'))])])])])])]
    pid, new = build('CRM - Salesperson changes',
                     "New salesperson: assignment date = now; when they are not the leader or a member of the record's team, "
                     "the team becomes their team (Odoo write(), _compute_team_id, _get_default_team_id). Removing the "
                     'salesperson clears the assignment date.',
                     nodes, '--trigger-worksheet', S[L], '--trigger-event', 'update', '--trigger-fields', l('user_id'))
    if new:
        clear_in(pid, 'Assignment date cleared', l('date_open'), 16)
    raw_only(pid, 'Team of the salesperson?', 0, lambda sid: [[rel_cond_on(sid, 0, l('team_id'), True)]])
    team_patches(pid, 'a')
    team_patches(pid, 'b')
    name_paths(pid, 'Salesperson set?', ['Salesperson removed', 'Salesperson set'])
    name_paths(pid, 'Team of the salesperson?', ['No team', 'Has a team'])
    name_paths(pid, 'Salesperson in the team?', ['In the team', 'Not in the team'])
    return done(pid, 'F5 Salesperson changes')


# ---- F1 ------------------------------------------------------------------------------------------------------------

def f1():
    ph_me = [cond('me', l('name'), 'not_empty', type=2)]
    nodes = [
        branch('tb', 'Team from the salesperson?', [
            path('tn', 'Salesperson, no team', team_by_type('n'), [cond('trigger', l('user_id'), 'not_empty')]),
            path('tg', 'Team given or no salesperson', [])]),
        fresh('me'),
        branch('sb', 'Stage of the new record?', [
            path('s1', 'No stage, no team', global_stage_nodes('g'), ph_me),
            path('s2', 'No stage', team_stage_nodes('t', 'me'), ph_me),
            path('s3', 'Stage given', [])]),
        upd('dt', 'Last stage update', [{'fieldId': l('date_last_stage_update'), 'value': NOW}]),
        branch('ub', 'Salesperson set?', [
            path('uy', 'Salesperson set', [upd('ud', 'Assignment date', [{'fieldId': l('date_open'), 'value': NOW}])],
                 [cond('trigger', l('user_id'), 'not_empty')]),
            path('un', 'No salesperson', [])])]
    pid, new = build('CRM - New lead defaults',
                     "A new lead or opportunity: team from the salesperson when none is given; the team's first unfolded "
                     'stage when none is given; last stage update and assignment date = now (Odoo _compute_team_id, '
                     '_compute_stage_id, _compute_date_open, _compute_date_last_stage_update).',
                     nodes, '--trigger-worksheet', S[L], '--trigger-event', 'create')
    # path conditions: "salesperson set and no team"; "no stage (and no team)" read on the fresh record
    patch_path(pid, 'Team from the salesperson?', 0,
               lambda groups: [[x for x in groups[0] if x.get('filedId') != l('team_id')] + [rel_cond(groups[0][0], l('team_id'), True)]]
               if groups else groups)
    patch_path(pid, 'Stage of the new record?', 0,
               lambda groups: [[rel_cond(groups[0][0], l('stage_id'), True), rel_cond(groups[0][0], l('team_id'), True)]])
    patch_path(pid, 'Stage of the new record?', 1, lambda groups: [[rel_cond(groups[0][0], l('stage_id'), True)]])
    for q in ('First stage for every team (g)', 'First stage of the team (t)'):
        patch_every_team(pid, q)
    team_patches(pid, 'n')
    name_paths(pid, 'Team from the salesperson?', ['Salesperson, no team', 'Team given or no salesperson'])
    name_paths(pid, 'Stage of the new record?', ['No stage, no team', 'No stage', 'Stage given'])
    name_paths(pid, 'Salesperson set?', ['Salesperson set', 'No salesperson'])
    return done(pid, 'F1 New lead defaults')


if __name__ == '__main__':
    refresh()
    for name in sys.argv[1:]:
        globals()[name]()
