"""CRM Phase A, step 2: seed and demo data from the local Odoo 20 (01-crm.md §8).

Only rows owned by crm, sales_team and utm (ir_model_data), as in wave 0:
- utm: 4 UTM stages, 6 mediums, 14 sources, 2 campaigns (Black Friday Sales, Christmas Special);
- sales_team: Sales, Pre-Sales, Website, Point of Sale (the Kiosk team belongs to pos_self_order_sale);
- crm: 4 stages, 3 lost reasons, 44 demo leads and opportunities with their 14 activities.
Odoo's demo users (Mitchell Admin, Marc Demo) do not exist in HAP: every salesperson, team leader and activity owner
is the build account, except Pre-Sales, whose only member is Marc Demo, so it is loaded without members.
Odoo date-times are UTC; HAP stores Malaysian time (UTC+8), so they are shifted by 8 hours.
Fields the CRM workflows maintain (won status, dates, day counters) keep Odoo's values. The CRM flows are built after
this step, so loading starts none of them; the wave 0 activity flows do run on the activities.
Run: python step2_seed.py export | load
"""
import datetime, json, os, re, sys
from crmlib import *  # noqa: F401,F403
sys.path.insert(0, W0)
from step3_export_demo import rows as odoo  # noqa: E402  (read-only SQL on the local Odoo database)
from step4a_load_reference import rows_of  # noqa: E402

DATA = os.path.join(HERE, 'data', 'crm-demo.json')
ME = os.environ.get('HAP_ACCOUNT_ID', '')   # the build account (HAP accountId); set it locally
DIAL = {'US': '1', 'BE': '32', 'FR': '33', 'GB': '44', 'MY': '60', 'ID': '62', 'IT': '39', 'BR': '55', 'AU': '61', 'RU': '7',
        'ES': '34', 'CN': '86', 'VE': '58', 'PE': '51', 'AR': '54', 'LI': '423', 'GR': '30', 'PT': '351', 'NL': '31', 'JP': '81'}
TYPE = {'lead': 'Lead', 'opportunity': 'Opportunity'}
WON = {'won': 'Won', 'lost': 'Lost', 'pending': 'Pending'}


def owned(model, alias, module):
    return f"EXISTS (SELECT 1 FROM ir_model_data d WHERE d.model = '{model}' AND d.res_id = {alias}.id AND d.module = '{module}')"


def export():
    d = {
        'utm_stage': odoo(f"SELECT s.id AS oid, s.name->>'en_US' AS name, s.sequence FROM utm_stage s WHERE {owned('utm.stage', 's', 'utm')} ORDER BY s.sequence, s.id"),
        'utm_medium': odoo(f"SELECT m.id AS oid, m.name, m.active FROM utm_medium m WHERE {owned('utm.medium', 'm', 'utm')} ORDER BY m.id"),
        'utm_source': odoo(f"SELECT s.id AS oid, s.name FROM utm_source s WHERE {owned('utm.source', 's', 'utm')} ORDER BY s.id"),
        'utm_campaign': odoo(f"""SELECT c.id AS oid, c.title->>'en_US' AS title, c.name, c.stage_id AS stage, c.active,
            (SELECT json_agg(t.name->>'en_US') FROM utm_tag_rel r JOIN utm_tag t ON t.id = r.tag_id WHERE r.campaign_id = c.id) AS tags
            FROM utm_campaign c WHERE {owned('utm.campaign', 'c', 'utm')} ORDER BY c.id"""),
        'crm_team': odoo(f"""SELECT t.id AS oid, t.name->>'en_US' AS name, t.sequence, t.active, t.user_id, t.use_leads,
            t.use_opportunities, t.assignment_optout,
            (SELECT json_agg(m.user_id) FROM crm_team_member m WHERE m.crm_team_id = t.id AND m.active) AS members
            FROM crm_team t WHERE {owned('crm.team', 't', 'sales_team')} ORDER BY t.sequence, t.id"""),
        'crm_stage': odoo(f"""SELECT s.id AS oid, s.name->>'en_US' AS name, s.sequence, s.is_won, s.fold, s.rotting_threshold_days,
            s.requirements, (SELECT json_agg(r.crm_team_id) FROM crm_stage_crm_team_rel r WHERE r.crm_stage_id = s.id) AS teams
            FROM crm_stage s WHERE {owned('crm.stage', 's', 'crm')} ORDER BY s.sequence, s.id"""),
        'crm_lost_reason': odoo(f"SELECT r.id AS oid, r.name->>'en_US' AS name, r.active FROM crm_lost_reason r WHERE {owned('crm.lost.reason', 'r', 'crm')} ORDER BY r.id"),
        'crm_lead': odoo(f"""SELECT l.id AS oid, l.name, l.type, l.active, l.won_status, l.probability, l.automated_probability,
            l.expected_revenue, l.priority, l.user_id, l.team_id AS team, l.stage_id AS stage,
            (SELECT complete_name FROM res_partner p WHERE p.id = l.partner_id) AS partner,
            l.partner_name, l.contact_name, l.function, l.email_from, l.phone, l.website, l.street, l.street2, l.zip, l.city,
            (SELECT code FROM res_country c WHERE c.id = l.country_id) AS country,
            (SELECT code FROM res_country_state s WHERE s.id = l.state_id) AS state,
            (SELECT code FROM res_lang g WHERE g.id = l.lang_id) AS lang, l.lost_reason_id AS lost_reason,
            l.campaign_id AS campaign, l.medium_id AS medium, l.source_id AS source, l.referred, l.description,
            l.date_deadline, l.date_open, l.date_closed, l.date_last_stage_update, l.date_conversion, l.day_open, l.day_close,
            (SELECT json_agg(t.name->>'en_US') FROM crm_tag_rel r JOIN crm_tag t ON t.id = r.tag_id WHERE r.lead_id = l.id) AS tags
            FROM crm_lead l WHERE {owned('crm.lead', 'l', 'crm')} ORDER BY l.id"""),
        'mail_activity': odoo(f"""SELECT a.id AS oid, a.res_id AS lead, a.summary, a.note, a.date_deadline, a.user_id,
            (SELECT name->>'en_US' FROM mail_activity_type t WHERE t.id = a.activity_type_id) AS type
            FROM mail_activity a WHERE a.res_model = 'crm.lead' AND {owned('mail.activity', 'a', 'crm')} ORDER BY a.id"""),
    }
    os.makedirs(os.path.dirname(DATA), exist_ok=True)
    json.dump(d, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print({k: len(v) for k, v in d.items()})


def batch(ws, rows, trigger=True, ignore_rules=False):
    """Create rows (one request per record) in chunks under ~15k characters of JSON (Windows command-line limit).
    ignore_rules: write fields the new-record form hides or makes read-only (the workflow-maintained ones), the way a
    workflow writes; without it the CLI refuses them."""
    ids, chunk, size = [], [], 0
    for r in rows + [None]:
        s = len(json.dumps(r, ensure_ascii=False)) if r else 0
        if r is None or (chunk and (size + s > 15000 or len(chunk) >= 20)):
            if chunk:
                args = ['worksheet', 'record', 'batch-create', ws, '-a', APP, '--rows', json.dumps(chunk, ensure_ascii=False)]
                if not trigger:
                    args.append('--no-workflow')
                if ignore_rules:
                    args.append('--ignore-rules')
                out = hap(*args)
                bad = [x for x in out.get('results', []) if x.get('resultCode') != 1]
                if bad or len(out.get('rowIds', [])) != len(chunk):
                    raise RuntimeError(f'batch-create on {ws}: {json.dumps(bad or out, ensure_ascii=False)[:600]}')
                ids += out['rowIds']
            chunk, size = [], 0
        if r is not None:
            chunk.append(r)
            size += s
    return ids


def clean(r):
    return {k: v for k, v in r.items() if v not in (None, '', [])}


def myt(ts):
    """Odoo UTC timestamp -> 'YYYY-MM-DD HH:MM:SS' in Malaysian time."""
    if not ts:
        return None
    t = datetime.datetime.fromisoformat(ts[:19]) + datetime.timedelta(hours=8)
    return t.strftime('%Y-%m-%d %H:%M:%S')


def phone(p, country):
    if not p:
        return None
    digits = re.sub(r'[^\d+]', '', p)
    return digits if digits.startswith('+') else '+' + DIAL.get(country or 'US', '1') + digits


def region(country, state):
    return (f'{country}|{country}-{state}' if state else country) if country else None


def load():
    D = json.load(open(DATA, encoding='utf-8'))
    refresh()
    ids = {}   # (sheet alias, odoo id) -> HAP row id

    def part(alias, rows_fn, key='name', ignore_rules=False):
        ws = S[alias]
        have = rows_of(ws, key)
        if have:
            print(f'{alias}: already holds {len(have)} rows, skipped')
            by = {r.get(key): r['rowId'] for r in have}
            for o in D[alias]:
                if o.get(key) in by:
                    ids[(alias, o['oid'])] = by[o[key]]
            return
        rows = [clean(rows_fn(o)) for o in D[alias]]
        for o, rid in zip(D[alias], batch(ws, rows, ignore_rules=ignore_rules)):
            ids[(alias, o['oid'])] = rid
        print(f'{alias}: {len(rows)} loaded')

    part('utm_stage', lambda o: {'name': o['name'], 'sequence': o['sequence']})
    part('utm_medium', lambda o: {'name': o['name'], 'active': o['active'] is not False})
    part('utm_source', lambda o: {'name': o['name']})
    part('utm_campaign', lambda o: {'title': o['title'], 'name': o['name'], 'user_id': [ME], 'active': o['active'] is not False,
                                    'stage_id': [ids[('utm_stage', o['stage'])]] if o['stage'] else None, 'tag_ids': o['tags']},
         key='title')
    part('crm_team', lambda o: {'name': o['name'], 'sequence': o['sequence'], 'active': o['active'] is not False,
                                'user_id': [ME] if o['user_id'] == 2 else None,
                                'member_ids': [ME] if 2 in (o['members'] or []) else None,
                                'use_leads': bool(o['use_leads']), 'use_opportunities': bool(o['use_opportunities']),
                                'assignment_optout': bool(o['assignment_optout'])})
    part('crm_stage', lambda o: {'name': o['name'], 'sequence': o['sequence'], 'is_won': bool(o['is_won']), 'fold': bool(o['fold']),
                                 'rotting_threshold_days': o['rotting_threshold_days'] or 0, 'requirements': o['requirements'],
                                 'team_ids': [ids[('crm_team', t)] for t in (o['teams'] or [])]})
    part('crm_lost_reason', lambda o: {'name': o['name'], 'active': o['active'] is not False})

    contacts = {r.get('complete_name'): r['rowId'] for r in rows_of(S['res_partner'], 'complete_name')}
    countries = {r.get('code'): r['rowId'] for r in rows_of(S['res_country'], 'code')}
    missing = sorted({o['partner'] for o in D['crm_lead'] if o['partner'] and o['partner'] not in contacts})
    if missing:
        print('customers not in Contacts (the lead keeps its company name, customer left empty):', missing)

    def lead(o):
        return {
            'name': o['name'], 'type': [TYPE[o['type']]], 'active': o['active'] is not False, 'won_status': [WON[o['won_status']]],
            'priority': int(o['priority'] or 0) or None, 'expected_revenue': o['expected_revenue'],
            'probability': o['probability'], 'automated_probability': o['automated_probability'],
            'user_id': [ME] if o['user_id'] else None, 'team_id': [ids[('crm_team', o['team'])]] if ('crm_team', o['team']) in ids else None,
            'stage_id': [ids[('crm_stage', o['stage'])]] if o['stage'] else None,
            'partner_id': [contacts[o['partner']]] if o['partner'] in contacts else None,
            'partner_name': o['partner_name'], 'contact_name': o['contact_name'], 'function': o['function'],
            'email_from': o['email_from'], 'phone': phone(o['phone'], o['country']), 'website': o['website'],
            'street': o['street'], 'street2': o['street2'], 'zip': o['zip'], 'city': o['city'],
            'x_crm__region': region(o['country'], o['state']),
            'country_id': [countries[o['country']]] if o['country'] in countries else None,
            'lang_id': ['English'] if o['lang'] == 'en_US' else None,
            'lost_reason_id': [ids[('crm_lost_reason', o['lost_reason'])]] if o['lost_reason'] else None,
            'campaign_id': [ids[('utm_campaign', o['campaign'])]] if ('utm_campaign', o['campaign']) in ids else None,
            'medium_id': [ids[('utm_medium', o['medium'])]] if ('utm_medium', o['medium']) in ids else None,
            'source_id': [ids[('utm_source', o['source'])]] if ('utm_source', o['source']) in ids else None,
            'referred': o['referred'], 'description': o['description'], 'tag_ids': o['tags'],
            'date_deadline': o['date_deadline'], 'date_open': myt(o['date_open']), 'date_closed': myt(o['date_closed']),
            'date_last_stage_update': myt(o['date_last_stage_update']), 'date_conversion': myt(o['date_conversion']),
            'day_open': o['day_open'], 'day_close': o['day_close'],
        }
    part('crm_lead', lead, ignore_rules=True)

    A = S['mail_activity']
    if any(r.get('x_crm__lead_id') for r in rows_of(A, 'x_crm__lead_id')):
        print('mail_activity: lead activities already loaded, skipped')
    else:
        types = {r.get('name'): r['rowId'] for r in rows_of(S['mail_activity_type'], 'name')}
        names = {o['oid']: o['name'] for o in D['crm_lead']}
        acts = [clean({'summary': a['summary'] or a['type'], 'activity_type_id': [types[a['type']]] if a['type'] in types else None,
                       'date_deadline': a['date_deadline'], 'user_id': [ME], 'note': a['note'],
                       'x_crm__lead_id': [ids[('crm_lead', a['lead'])]], 'res_model': 'Leads',
                       'res_id': ids[('crm_lead', a['lead'])], 'res_name': names[a['lead']], 'active': True})
                for a in D['mail_activity'] if ('crm_lead', a['lead']) in ids]
        batch(A, acts, ignore_rules=True)
        print(f'mail_activity: {len(acts)} lead activities loaded')
    json.dump({f'{k[0]}:{k[1]}': v for k, v in ids.items()}, open(os.path.join(HERE, 'data', 'crm-demo-ids.json'), 'w'), indent=0)


if __name__ == '__main__':
    {'export': export, 'load': load}[sys.argv[1]]()
