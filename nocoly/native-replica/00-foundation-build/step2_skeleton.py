"""Wave 0, step 2: the app skeleton. Menu groups and the empty roles (00-foundation.md §3 and §6).

Re-runnable: it reads the live groups and roles first and only creates or renames what is missing.

Groups (top level, in this order), each Odoo app's setup lists in its own "Configuration" child group:
  Contacts (› Configuration), Products (› Configuration), Activities (› Configuration), Settings, System Tables
Roles: Employee (the default member role, renamed), Master Data Manager (new), Read Only (the default read-only role, renamed)
"""
import json
from lib import APP, hap, app_info, sections_flat, roles, record, backup

TOP = [('Contacts', 'contacts'), ('Products', 'product'), ('Activities', 'mail'), ('Settings', 'base'), ('System Tables', 'system')]
CHILD = [('Contacts', 'contacts'), ('Products', 'product'), ('Activities', 'mail')]  # parent name -> "Configuration" child
log = []

info = app_info()
backup('step2-app-info-before', info)
secs = sections_flat(info)
top = {s['name']: s for s in secs if s['parent'] is None}

# 1. top-level groups. The app was created with one unnamed group: it becomes "Contacts".
if 'Contacts' not in top:
    blank = [s for s in secs if s['parent'] is None and not s['name']]
    if blank:
        hap('app', 'edit-section', APP, blank[0]['id'], '-n', 'Contacts')
        log.append(f"renamed the unnamed group {blank[0]['id']} to Contacts")
for name, _ in TOP:
    if name not in top and name != 'Contacts':
        hap('app', 'add-section', APP, '-n', name)
        log.append(f'created group {name}')
secs = sections_flat()
top = {s['name']: s for s in secs if s['parent'] is None}

# 2. "Configuration" child groups
for parent, _ in CHILD:
    pid = top[parent]['id']
    if not any(s['parent'] == pid and s['name'] == 'Configuration' for s in secs):
        hap('app', 'add-section', APP, '-n', 'Configuration', '--parent-id', pid)
        log.append(f'created group {parent} › Configuration')

# 3. order of the top-level groups (new groups go to the top, so sort with the full list)
secs = sections_flat()
top = {s['name']: s for s in secs if s['parent'] is None}
others = [s['id'] for s in secs if s['parent'] is None and s['name'] not in dict(TOP)]
order = [top[n]['id'] for n, _ in TOP] + others
current = [s['id'] for s in secs if s['parent'] is None]
if current != order:
    hap('app', 'sort-sections', APP, *order)
    log.append('sorted the top-level groups')

# 4. roles
rs = roles()
backup('step2-roles-before', rs)
names = {r['name']: r for r in rs}
for old, new in (('\u6210\u5458', 'Employee'), ('\u53ea\u8bfb', 'Read Only')):  # HAP's default role names, stored in Chinese
    if new not in names and old in names:
        hap('app', 'role', 'rename', APP, names[old]['id'], '-n', new)
        log.append(f'renamed role {old} to {new}')
if 'Master Data Manager' not in names:
    # Scope 0 (per sheet) is refused while the app has no sheets, so the role starts as view-only (20).
    # Its per-sheet rights are set in step 6, when the sheets exist (create-fine, the role has no members).
    hap('app', 'role', 'create', '-a', APP, '--name', 'Master Data Manager', '--type', '0', '--permission-scope', '20',
        '--description', 'Creates and edits contacts, products, pricelists, units, currencies and activity types. '
                         'Sheet rights are set as each sheet is built.')
    log.append('created role Master Data Manager')

# 5. read back and record in the ledger
secs = sections_flat()
top = {s['name']: s for s in secs if s['parent'] is None}
for name, module in TOP:
    record(top[name]['id'], 'group', name, module, 'step 2')
for parent, module in CHILD:
    c = [s for s in secs if s['parent'] == top[parent]['id'] and s['name'] == 'Configuration']
    record(c[0]['id'], 'group', f'{parent} › Configuration', module, 'step 2')
rs = {r['name']: r for r in roles()}
for name, module in (('Employee', 'base'), ('Master Data Manager', 'base'), ('Read Only', 'system')):
    record(rs[name]['id'], 'role', name, module, 'step 2')

print('\n'.join(log) or 'nothing to change')
print('top-level order now:', [s['name'] for s in secs if s['parent'] is None])
print('children:', [(next(t['name'] for t in secs if t['id'] == s['parent']), s['name']) for s in secs if s['parent']])
print('roles:', [(r['name'], r['roleType']) for r in rs.values()])
