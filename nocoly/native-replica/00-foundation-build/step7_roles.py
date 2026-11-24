"""Wave 0 (plan v2 §6): the Employee role per sheet.

Employee = read master data; create and edit their own activities (plus the plan launches and price checks they make).
"Own" (20) also covers records where the person is in a Members field set to "Members (view records)", so an activity
assigned to someone is visible to them. The System Tables are read-only for the role and hidden from members in the
navigation (app item display).

Why a new role, and why in-process:
- The old "Employee" was HAP's default member role, renamed, with "view all + manage own" (50) on every sheet.
  `app role set-permissions --permission-way 0 -P ...` cannot give it per-sheet rules: the server answers success and
  keeps the old sheet levels, in either shape (PLATFORM-ISSUES P36). It is renamed "Member (HAP default)" (no members;
  Li Wei decides whether to delete it).
- `app role create-fine` stores per-sheet scopes but sends no globalPermissions, so every app-wide switch (add record,
  export, discussion, log...) comes out off; a sheet with read scope 0 falls back to 20/20/20 with everything allowed
  (P37). The role is therefore created with the CLI's own V3 call plus the 8 global switches.
Run: python step7_roles.py
"""
import json
from hap_cli.core.session import Session
from hap_cli.core import role_perm_builder as rpb
from lib import hap, APP, PROFILE, backup, record
from wflib import S

OLD_EMPLOYEE = '<uuid>'
OWN_WORK = {'mail_activity', 'x_mail__plan_launch', 'x_product__price_check'}
DESC = ('Reads all master data (contacts, products, pricelists, units, currencies, activity setup). Creates and edits '
        'their own activities, plan launches and price checks; sees activities assigned to them. Plan v2 §6.')
GLOBALS = {'addRecord': True, 'share': False, 'import': False, 'export': True, 'log': True,
           'attachmentDownload': True, 'systemPrint': True, 'discuss': True}


def roles():
    r = hap('app', 'role', 'list', '-a', APP)
    return {x['name']: x['id'] for x in r.get('data', r).get('roles', [])}


def intents():
    out = []
    for alias, ws in S.items():
        if alias in OWN_WORK:
            out.append({'worksheetId': ws, 'recordDataScope': {'read': 20, 'edit': 20, 'delete': 20},
                        'recordActions': {'add': True, 'log': True, 'discuss': True, 'attachmentDownload': True, 'systemPrint': True},
                        'worksheetActions': {'export': True, 'discuss': True}})
        else:  # master data and System Tables: read only
            out.append({'worksheetId': ws, 'recordDataScope': {'read': 100, 'edit': 0, 'delete': 0},
                        'recordActions': {'add': False, 'log': True, 'discuss': True, 'attachmentDownload': True, 'systemPrint': True},
                        'worksheetActions': {'export': True, 'discuss': True}})
    return out


def employee():
    have = roles()
    if have.get('Employee') == OLD_EMPLOYEE:
        backup('role-employee-old', hap('app', 'role', 'permissions', '-a', APP, OLD_EMPLOYEE))
        hap('app', 'role', 'rename', APP, OLD_EMPLOYEE, '-n', 'Member (HAP default)')
        have = roles()
    if 'Employee' not in have:
        s = Session.load(PROFILE)
        body = {'name': 'Employee', 'description': DESC, 'type': 0, 'permissionScope': 0, 'hideAppForMembers': False,
                'globalPermissions': GLOBALS,
                'worksheetPermissions': [rpb.complete_worksheet_permission(s, APP, wp) for wp in intents()],
                'pagePermissions': []}
        s.v3_call('POST', '/v3/app/roles', app_id=APP, body=body)
        have = roles()
        record(have['Employee'], 'role', 'Employee (per sheet)', 'base', 'v2 step 5 (roles, 24 Nov): V3 create with globals')
    return have['Employee']


if __name__ == '__main__':
    rid = employee()
    inv = {v: k for k, v in S.items()}
    d = hap('app', 'role', 'permissions', '-a', APP, rid)
    d = d.get('data', d)
    print('Employee', rid, 'scope', d.get('permissionScope'), 'globals', d.get('globalPermissions'))
    for w in d['worksheetPermissions']:
        print(f"  {inv.get(w['id'], w['id']):<34} {w['recordDataScope']} add={w['recordActions'].get('add')} "
              f"export={w['worksheetActions'].get('export')} import={w['worksheetActions'].get('import')}")
    print('roles now:', list(roles()))
