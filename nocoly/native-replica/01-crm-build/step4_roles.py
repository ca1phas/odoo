"""CRM Phase A, step 4: the sales roles (01-crm.md §6), owned by sales_team.

Odoo 20 rights (reference/odoo20-crm-access.csv):
- Salesperson  = Sales / User: Own Documents Only: leads create / read / update where they are the salesperson (Odoo
  also lets them see unassigned ones: here they read all and edit their own, decision 5), no delete; stages, teams and
  lost reasons read; campaigns, mediums, sources create / read / update (every internal user).
- Sales User   = Sales / User: All Documents: create / read / update every lead, no delete.
- Sales Manager = Sales / Administrator: everything on the CRM and Link Tracker sheets, configuration included.
"Own" follows the Salesperson field: its member permission is "Owner (edit and delete records)" (userPermission 2), as
the Organizer of a meeting. Deleting stays with the role's delete scope (none for salespeople).
Wave 0 sheets keep the Employee rules (master data read-only; own activities, plan launches and price checks); sales
roles may also add contacts and edit their own (Odoo salespeople create customers).
Roles are created with the CLI's V3 call plus the app-wide switches (P36, P37), as wave 0's Employee.
Run: python step4_roles.py
"""
import json
from hap_cli.core.session import Session
from hap_cli.core import role_perm_builder as rpb
from crmlib import *  # noqa: F401,F403
from lib import PROFILE

STEP = 'crm step 4 (roles): V3 create with globals'
GLOBALS = {'addRecord': True, 'share': False, 'import': False, 'export': True, 'log': True,
           'attachmentDownload': True, 'systemPrint': True, 'discuss': True}
OWN_WORK = {'mail_activity', 'x_mail__plan_launch', 'x_product__price_check'}
LINK = {'utm_campaign', 'utm_medium', 'utm_source'}
CONFIG = {'crm_stage', 'crm_team', 'crm_lost_reason', 'utm_stage'}
ROLES = {
    'Salesperson': ('Works their own leads and opportunities: reads all, edits those where they are the salesperson, '
                    'no delete. Reads the CRM configuration; adds campaigns, mediums and sources (Odoo Sales / User: Own '
                    'Documents Only). Plan 01-crm.md §6.'),
    'Sales User': ('Works every lead and opportunity: reads and edits all, no delete (Odoo Sales / User: All Documents). '
                   'Plan 01-crm.md §6.'),
    'Sales Manager': ('Everything on the CRM and Link Tracker sheets, configuration included (Odoo Sales / Administrator). '
                      'Plan 01-crm.md §6.'),
}


def scope(read, edit, delete, add):
    return {'recordDataScope': {'read': read, 'edit': edit, 'delete': delete},
            'recordActions': {'add': add, 'log': True, 'discuss': True, 'attachmentDownload': True, 'systemPrint': True},
            'worksheetActions': {'export': True, 'discuss': True}}


def rights(role, alias):
    mgr = role == 'Sales Manager'
    if alias == 'crm_lead':
        return {'Salesperson': scope(100, 20, 0, True), 'Sales User': scope(100, 100, 0, True)}.get(role, scope(100, 100, 100, True))
    if alias == 'calendar_event':
        return {'Salesperson': scope(100, 20, 20, True), 'Sales User': scope(100, 100, 20, True)}.get(role, scope(100, 100, 100, True))
    if alias in CONFIG:
        return scope(100, 100, 100, True) if mgr else scope(100, 0, 0, False)
    if alias in LINK:
        return scope(100, 100, 100, True) if mgr else scope(100, 100, 0, True)
    if alias == 'res_partner':
        return scope(100, 20, 0, True) if role == 'Salesperson' else scope(100, 100, 0, True)
    if alias in OWN_WORK:
        return scope(20, 20, 20, True)
    return scope(100, 0, 0, False)   # other master data and System Tables: read only


def roles():
    r = hap('app', 'role', 'list', '-a', APP)
    return {x['name']: x['id'] for x in r.get('data', r).get('roles', [])}


def grant_pages(s, have):
    """Every sales role sees the CRM Reporting page (Odoo: CRM > Reporting is open to salespeople).
    The roles were first created with no page rights, so the page was hidden from them (found with Role Debug,
    24 Nov 2026). V3 has no PUT for roles (405); PATCH works with the role's complete body, so the whole role is
    read, the page switched on, and every other key compared afterwards. Do not save these roles in the role editor:
    it shows their per-sheet rights as all-allowed (see BUILD-LOG, Roles), and saving would write that back."""
    page = ledger_id('page', 'CRM › Reporting')
    for name in ROLES:
        rid = have[name]
        before = s.v3_call('GET', '/v3/app/roles/{role_id}', app_id=APP, path_params={'role_id': rid})
        before = before.get('data', before)
        if all(p.get('enable') for p in before.get('pagePermissions') or [] if p.get('id') == page) and                 any(p.get('id') == page for p in before.get('pagePermissions') or []):
            print(name, 'Reporting page already on')
            continue
        backup(f'role-{name}', before)
        body = {k: v for k, v in before.items() if k != 'id'}
        body['pagePermissions'] = [p for p in body.get('pagePermissions') or [] if p.get('id') != page] + [{'id': page, 'enable': True}]
        s.v3_call('PATCH', '/v3/app/roles/{role_id}', app_id=APP, path_params={'role_id': rid}, body=body)
        after = s.v3_call('GET', '/v3/app/roles/{role_id}', app_id=APP, path_params={'role_id': rid})
        after = after.get('data', after)
        changed = [k for k in before if k != 'pagePermissions' and json.dumps(before[k], sort_keys=True) != json.dumps(after.get(k), sort_keys=True)]
        if changed or not any(p.get('id') == page and p.get('enable') for p in after.get('pagePermissions') or []):
            raise RuntimeError(f'{name}: page not granted cleanly, changed {changed}')
        print(name, 'Reporting page on; nothing else changed')


def ledger_id(type_, name):
    return next(k for k, v in ledger()['objects'].items() if v.get('type') == type_ and v.get('name') == name)


def member_owners():
    """Salesperson (leads) and Organizer (meetings): the person in the field owns the record."""
    for sheet, alias in (('crm_lead', 'user_id'), ('calendar_event', 'user_id')):
        c = by_alias(S[sheet])[alias]
        if c.get('userPermission') != 2:
            apply_spec([{'type': 'field.update', 'worksheet': S[sheet], 'field': c['controlId'], 'set': {'userPermission': 2}}])
        print(sheet, alias, 'userPermission', by_alias(S[sheet])[alias].get('userPermission'))


if __name__ == '__main__':
    refresh()
    member_owners()
    have = roles()
    s = Session.load(PROFILE)
    for name, desc in ROLES.items():
        if name in have:
            print(name, 'exists', have[name])
            continue
        body = {'name': name, 'description': desc, 'type': 0, 'permissionScope': 0, 'hideAppForMembers': False,
                'globalPermissions': GLOBALS,
                'worksheetPermissions': [rpb.complete_worksheet_permission(s, APP, dict(rights(name, alias), worksheetId=ws))
                                         for alias, ws in S.items()],
                'pagePermissions': []}
        s.v3_call('POST', '/v3/app/roles', app_id=APP, body=body)
        have = roles()
        record(have[name], 'role', name, 'sales_team', STEP)
        print(name, 'created', have[name])
    grant_pages(s, have)
    inv = {v: k for k, v in S.items()}
    for name in ROLES:
        d = hap('app', 'role', 'permissions', '-a', APP, have[name])
        d = d.get('data', d)
        rows = {inv.get(w['id'], w['id']): (w['recordDataScope'], w['recordActions'].get('add')) for w in d['worksheetPermissions']}
        print(name, 'globals add/export:', d['globalPermissions'].get('addRecord'), d['globalPermissions'].get('export'),
              '| lead', rows.get('crm_lead'), '| stage', rows.get('crm_stage'), '| campaign', rows.get('utm_campaign'),
              '| contacts', rows.get('res_partner'), '| products', rows.get('product_template'))
