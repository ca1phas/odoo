#!/usr/bin/env python3
"""Roles for ERP Master — the last piece of Phase 1, deferred by every worksheet's *Not built now*.

Two things:

  1. HAP's **five stock roles** are renamed from Chinese to English — Administrator · Operator · Developer ·
     Member · Read-only. Only the label changes; `roleType` and the members are never touched, so Casimir,
     Oscar Wong and Teh Li Wei stay app administrators exactly as they are.
  2. **Four business roles**, one per Odoo accounting group, each with per-worksheet access rules
     (`hap app role create-fine`). Nobody is assigned to any of them — who belongs in which role is the
     owner's call. The Chart of Accounts bundle added per-field hiding: the account fields Odoo keeps from its
     Invoicing and Read-only groups are hidden from those roles, field by field (HIDDEN_FIELDS). The Payment Terms
     bundle added Payment Terms and Payment Term Lines: Accounting Administrator full, the other three view — Odoo
     gives write, create and delete on both models to account.group_account_manager alone. The Countries bundle
     added Countries as the first worksheet **no** business role may write: Odoo's `ir.model.access.csv` reads
     res.country to everyone and writes it from `base.group_system` alone, which none of the four stands for
     (11-countries.md §1 › Roles), so only the app Administrator creates, edits or deletes a country. The States
     bundle added **States**, and it does **not** follow Countries: `ir.model.access.csv` writes
     res.country.state from `base.group_partner_manager` — a contact manager — so every role gets the same cell
     on States that it already has on **Contacts** (owner, 18 Sep 2026; 12-states.md §1 › Roles). The Taxes
     bundle added **Taxes** with **Chart of Accounts' row unchanged**: `account.tax` has exactly the access
     shape of `account.account` in the same file — `account.group_account_manager` reads, writes, creates and
     deletes, every other group reads — so Accounting Administrator is full and the other three view
     (13-taxes.md §1 › Roles). No field of it is hidden from a role: the two Odoo puts behind a group are one
     that is not built (`analytic`) and one that is developer mode (`is_base_affected`). On 22 Sep 2026
     **Incoterms** joined like Payment Terms (Accounting Administrator full, the other three view —
     account.group_account_manager alone writes account.incoterms) and **Contact Tags** like Countries (view for
     all four; only the app Administrator edits), both through `plan` then `create` (19-incoterms.md,
     20-contact-tags.md). The same day the owner moved **Contact Tags onto States' row**: Odoo's
     `ir.model.access.csv` writes res.partner.category from `base.group_partner_manager`, as it does
     res.country.state, and reads it to `base.group_user` — so whoever edits Contacts edits its tags.

Run from the repo root with the CLI's interpreter:

    ~/.hap-venv/bin/python nocoly/build/roles.py rename    # 1. the five stock roles, Chinese -> English
    ~/.hap-venv/bin/python nocoly/build/roles.py create    # 2. the four business roles (upsert by name), then each
                                                           #    one's description, per-worksheet scopes and export
                                                           #    right — which is also how a worksheet built after
                                                           #    the roles (a bundle) joins them
    ~/.hap-venv/bin/python nocoly/build/roles.py plan      # what `create` would write, role by role — writes
                                                           #    nothing
    ~/.hap-venv/bin/python nocoly/build/roles.py all       # both, then check
    ~/.hap-venv/bin/python nocoly/build/roles.py check     # read every role back against this spec
    ~/.hap-venv/bin/python nocoly/build/roles.py show      # the live roles, with their per-worksheet scopes

Every step reads the live roles first and is safe to re-run; a second run writes nothing. Nothing here deletes
a role, and no role is given a member.

Profile. As in the other builders: --profile > $HAP_PROFILE > hap-cli's active profile.
"""
import json
import os
import sys

import common as C
import hap

APP = hap.ids()['app']
WORKSHEETS = hap.ids()['worksheets']

# ── 1 · the five stock roles ────────────────────────────────────────────────
#
# HAP creates them with every app, Chinese-named. The house rule is English labels, as in Odoo
# (DECISIONS.md, 15 Sep 2026). `roleType` is HAP's own meaning for the role and is left alone:
# 100 administrator · 2 operator · 1 developer · 0 member / read-only.

STOCK = [  # (English name, the Chinese name HAP ships, roleType)
    ('Administrator', '管理员', 100),
    ('Operator', '运营者', 2),
    ('Developer', '开发者', 1),
    ('Member', '成员', 0),
    ('Read-only', '只读', 0),
]

# ── 2 · the four business roles ─────────────────────────────────────────────
#
# One per Odoo accounting group. The group names are the `name` fields of
# addons/account/security/account_security.xml, and the sentence after the dash is Odoo's own `comment` on
# the group where it has one, and the file's header comment (lines 31-35) where it has not.

FULL, EDIT, VIEW = 'full', 'view · add · edit', 'view'

ORDER = ['Contacts', 'Contact Tags', 'Countries', 'States', 'Units & Packagings', 'Products', 'Product Variants',
         'Product Categories', 'Chart of Accounts', 'Taxes', 'Journals', 'Payment Terms', 'Payment Term Lines',
         'Incoterms', 'Invoices', 'Invoice Lines', 'Orders', 'Order Lines']

# Worksheets no business role may write, whatever its accounting level: Odoo keeps them behind a group none of
# the four stands for. Countries is the first and, so far, the only one (base.group_system writes res.country;
# everybody else reads it). **States is deliberately not here**: Odoo writes res.country.state from
# base.group_partner_manager, a contact manager, so each role has the same cell on States that it has on
# Contacts (owner, 18 Sep 2026; 12-states.md §1 › Roles).
# **Contact Tags is not here either.** It joined on 22 Sep 2026 like Countries, and the owner moved it the same day
# to follow Odoo's access list rather than its menu: ir.model.access.csv reads res.partner.category to
# base.group_user and writes it from base.group_partner_manager (rows 79-80), exactly as res.country.state — so
# each role has the same cell on Contact Tags that it has on Contacts and States (20-contact-tags.md §6 › Roles).
# **Orders and Order Lines joined on 23 Sep 2026.** They were built after this table and so were never in it,
# which left every role on HAP's default for a new worksheet — read, edit **and delete**, plus add. The owner
# asked for Accounting Read-only to be view-only there, as it is everywhere else; the other three follow the
# app-wide rule that only Accounting Administrator deletes, so Accountant and Invoicing keep add and edit and
# lose delete. Odoo itself writes sale.order from the sales groups, none of which these four accounting roles
# stand for — a Sales role belongs here when Phase 3 gets one, and these cells should be revisited then.
VIEW_ONLY = {'Countries'}

ROLES = {
    'Accounting Administrator': (
        'Odoo group account.group_account_manager — "Administrator". Full access, including configuration '
        'rights. The only role here that may delete a record, and the only one that may export: Odoo keeps '
        'exporting behind its own group, base.group_allow_export, which is granted deliberately rather than '
        'implied by an accounting level. Countries is the exception to "full": Odoo writes res.country from '
        'base.group_system, the settings administrator, and this role is not that.',
        {name: VIEW if name in VIEW_ONLY else FULL for name in ORDER},
    ),
    'Accountant': (
        'Odoo group account.group_account_user — "Show Full Accounting Features". The accountant: can do '
        'everything except advanced configuration.',
        {'Contacts': EDIT, 'Contact Tags': EDIT, 'Countries': VIEW, 'States': EDIT, 'Units & Packagings': VIEW,
         'Products': VIEW, 'Product Variants': VIEW,
         'Product Categories': VIEW, 'Chart of Accounts': VIEW, 'Taxes': VIEW, 'Journals': EDIT,
         'Payment Terms': VIEW,
         'Payment Term Lines': VIEW, 'Incoterms': VIEW, 'Invoices': EDIT, 'Invoice Lines': EDIT,
         'Orders': EDIT, 'Order Lines': EDIT},
    ),
    'Invoicing': (
        'Odoo group account.group_account_invoice — "Invoicing". Invoices, payments and basic invoice '
        'reporting; cannot see accounting configuration, so Journals is read-only.',
        {'Contacts': EDIT, 'Contact Tags': EDIT, 'Countries': VIEW, 'States': EDIT, 'Units & Packagings': VIEW,
         'Products': VIEW, 'Product Variants': VIEW,
         'Product Categories': VIEW, 'Chart of Accounts': VIEW, 'Taxes': VIEW, 'Journals': VIEW,
         'Payment Terms': VIEW,
         'Payment Term Lines': VIEW, 'Incoterms': VIEW, 'Invoices': EDIT, 'Invoice Lines': EDIT,
         'Orders': EDIT, 'Order Lines': EDIT},
    ),
    'Accounting Read-only': (
        'Odoo group account.group_account_readonly — "Show Accounting Features - Readonly". Can see (and '
        'only see) everything.',
        {name: VIEW for name in ORDER},
    ),
}

# What each cell of that table is, in HAP's own terms. `recordDataScope` is the scope of the three record
# rights — 0 none · 20 own · 30 own and subordinates' · 100 every record — and `add` is the record-create
# right. Delete is 0 everywhere but Accounting Administrator, as the owner asked.
SCOPE = {
    FULL: ({'read': 100, 'edit': 100, 'delete': 100}, True),
    EDIT: ({'read': 100, 'edit': 100, 'delete': 0}, True),
    VIEW: ({'read': 100, 'edit': 0, 'delete': 0}, False),
}

# ── 3 · account fields hidden from a role ───────────────────────────────────
#
# Odoo hides the account fields from part of the accounting staff with `groups=` on its views (09-chart-of-accounts
# §1 › Roles). A HAP fine-grained role carries a switch per field: the Roles page's **新增 · 查看 · 编辑** (add · view ·
# edit) columns, stored on each sheet's `fields[]` as `notAdd` / `notRead` / `notEdit`. A hidden field here is all
# three — off the create form, not visible, not editable — which is what the page stores when a person unticks it
# (pd-openweb RoleSet/TooltipSetting: unticking 查看 clears 编辑 with it). The page also hides a **tab** once every
# field in it is hidden and shows it again as soon as one is visible; the three tabs this bundle added hold nothing
# but these accounts, so they follow them the same way. No other field or tab is touched.
ACCOUNT_READONLY_FIELDS = {   # groups="account.group_account_readonly": Invoicing does not see them
    'Journals': ['Default Account', 'Suspense Account', 'Profit Account', 'Loss Account', 'Private Share Account'],
    'Products': ['Income Account', 'Expense Account'],
    'Product Categories': ['Income Account', 'Expense Account'],
    'Invoice Lines': ['Account'],
}
ACCOUNT_USER_FIELDS = {       # groups="account.group_account_user": neither Invoicing nor Accounting Read-only
    'Contacts': ['Account Receivable', 'Account Payable'],
}
HIDDEN_FIELDS = {
    'Accounting Administrator': {},
    'Accountant': {},
    'Invoicing': {**ACCOUNT_READONLY_FIELDS, **ACCOUNT_USER_FIELDS},
    'Accounting Read-only': dict(ACCOUNT_USER_FIELDS),
}
OWNED_FIELDS = {**ACCOUNT_READONLY_FIELDS, **ACCOUNT_USER_FIELDS}   # the fields whose visibility this table decides
FIELD_SWITCHES = ('notRead', 'notEdit', 'notAdd')


def missing_owned(sheet, worksheet):
    """The fields OWNED_FIELDS names that this sheet does not list — none once bundle 2 is built."""
    names = {f['fieldName'] for f in sheet.get('fields') or [] if f.get('type') != 52}
    return [n for n in OWNED_FIELDS.get(worksheet) or [] if n not in names]


def field_targets(role, sheet, worksheet):
    """{fieldId: hidden} on one role's sheet for the fields OWNED_FIELDS decides — and for a tab holding nothing
    else, hidden exactly when all of them are. A field not built yet is left out (a build that has not reached
    bundle 2); `check` reports it."""
    owned = OWNED_FIELDS.get(worksheet) or []
    if not owned:
        return {}
    fields = sheet.get('fields') or []
    by_name = {f['fieldName']: f for f in fields if f.get('type') != 52}
    hidden = set(HIDDEN_FIELDS.get(role, {}).get(worksheet) or [])
    out = {by_name[n]['fieldId']: n in hidden for n in owned if n in by_name}
    for tab in (f for f in fields if f.get('type') == 52):
        children = [f for f in fields if f.get('sectionId') == tab['fieldId']]
        if children and all(c['fieldId'] in out for c in children):
            out[tab['fieldId']] = all(out[c['fieldId']] for c in children)
    return out


def field_state(sheet, targets):
    return {f['fieldId']: tuple(bool(f.get(k)) for k in FIELD_SWITCHES) for f in sheet.get('fields') or []
            if f['fieldId'] in targets}


# **Export** is the one right outside the owner's table that is set deliberately. Odoo keeps exporting behind
# its own group, `base.group_allow_export`, granted on purpose and not implied by an accounting level — so
# hap-cli's default of no export is faithful for three of the four roles, and Accounting Administrator, the
# Odoo Administrator, gets it (owner, 16 Sep 2026).
EXPORTERS = {'Accounting Administrator'}

# Everything else a role can be given — sharing a view, import, batch operations, record sharing, printing,
# the record log — is left at hap-cli's own defaults, the same for all four roles. The owner's table speaks to
# read, add, edit and delete only, and guessing at the rest would put settings in front of a reviewer that
# nobody asked for. They read back as (SHEET_SWITCHES below is the same list in the main site's own names,
# which is what a worksheet HAP added to a role by itself has to be brought back to):
DEFAULT_WORKSHEET_ACTIONS = {'shareView': False, 'import': False, 'export': False, 'discuss': True,
                             'batchOperation': False}
DEFAULT_RECORD_ACTIONS = {'share': False, 'discuss': True, 'systemPrint': False,
                          'attachmentDownload': True, 'log': False}


def worksheet_actions(name):
    """The worksheetActions a role should read back with: the defaults, plus export for an exporter."""
    return {**DEFAULT_WORKSHEET_ACTIONS, 'export': name in EXPORTERS}


def roles():
    """The live roles as the **app's own Roles page** sees them: AppManagement/GetRolesWithUsers, which is
    what pd-openweb calls, returning each role's stored name.

    Not `hap app role list`. That command is the V3 endpoint, and V3 renders HAP's own built-in label for the
    three typed roles — 管理员 · 运营者 · 开发者 — whatever the stored name is. `v3_names()` prints both."""
    from hap_cli.core import role as role_mod
    from hap_cli.core.session import Session
    return role_mod.get_roles(Session.load(None), APP)


def v3_rows():
    """{roleId: row} as `hap app role list` reports it — HAP's built-in label for a typed role, plus the
    department, department-tree, job and org-role members the main-site list leaves out."""
    out = hap.run('app', 'role', 'list', '-a', APP)
    data = out.get('data', out) if isinstance(out, dict) else out
    rows = (data or {}).get('roles', data if isinstance(data, list) else [])
    return {r.get('id') or r.get('roleId'): r for r in rows}


def by_name():
    return {r['name']: r for r in roles()}


def members(r):
    """The names of a role's member accounts."""
    return sorted(u.get('fullName') or u.get('fullname') or u['accountId'] for u in r.get('users') or [])


def unowned():
    """Worksheets of the app that the owner's table does not name — another administrator's, mid-build.

    They are reported and never written to: `reconcile` walks the role's matrix, so a sheet outside ORDER is
    read from the role model and posted back exactly as it was. Worth printing, because HAP adds every new
    worksheet to every fine-grained role on its own, at its own defaults — own records only, no create, and
    **export on** — so whoever owns them has the same reconciling to do (BUILDING.md)."""
    app = hap.run('app', 'info', '-a', APP).get('data', {})
    live = {i['name'] for s in app.get('sections', []) for i in s['items'] if i['type'] == 0}
    return sorted(live - set(ORDER)), live


def guard():
    """Stop unless the profile reaches ERP Master and the app holds every worksheet in ORDER."""
    who = hap.run('auth', 'whoami')
    app = hap.run('app', 'info', '-a', APP).get('data', {})
    if app.get('name') not in hap.APP_NAMES:
        sys.exit(f"profile {who.get('profile')!r} does not reach ERP Master (found {app.get('name')!r})")
    extra, live = unowned()
    if not set(ORDER) <= live:
        sys.exit(f'ERP Master holds {sorted(live)}, and the worksheets in ORDER '
                 f'{sorted(set(ORDER) - live)} are missing')
    if extra:
        print(f"  guard: {extra} are in the app and not in the owner's table — left exactly as they are")
    stock = {r['name'] for r in roles()}
    unknown = stock - {n for n, _, _ in STOCK} - {c for _, c, _ in STOCK} - set(ROLES)
    if unknown:
        sys.exit(f'unknown role(s) in the app — stopping: {sorted(unknown)}')
    if len(stock) != len(roles()):
        sys.exit(f'two roles share a name: {sorted(r["name"] for r in roles())}')
    print(f"  guard: profile {os.environ.get('HAP_PROFILE') or who.get('profile')!r}, ERP Master, "
          f"{len(live)} worksheets, {len(stock)} roles")


def step_rename():
    """Rename the five stock roles to English. Matched by id (ids.json), then by either spelling of the name;
    `roleType` and the members are not in the call — `role rename` reads the role and posts it back with only
    the name replaced."""
    guard()
    live = by_name()
    for english, chinese, role_type in STOCK:
        known = hap.ids().get('roles', {}).get(english)
        r = next((x for x in roles() if x['roleId'] == known), None) or live.get(english) or live.get(chinese)
        if not r:
            sys.exit(f'stock role {chinese!r} / {english!r} not found')
        if r['roleType'] != role_type:
            sys.exit(f"{r['name']!r} is roleType {r['roleType']}, expected {role_type}")
        if r['name'] != english:
            hap.run('app', 'role', 'rename', APP, r['roleId'], '-n', english)
        C.remember('roles', english, r['roleId'])
    v3 = v3_rows()
    for r in roles():
        if r['name'] in {n for n, _, _ in STOCK}:
            print(f"  {r['name']:<24} {r['roleId']} roleType={r['roleType']:<3} members={members(r) or '—'}"
                  f"   (hap app role list still calls it {v3.get(r['roleId'], {}).get('name')!r})")


def worksheet_permissions(role, matrix):
    """The --worksheet-permissions intent for one role: one entry per worksheet, in the table's order.

    create-fine fetches each worksheet's fields and views and fills the rest of the structure in; anything
    not named defaults to allowed, so the fields and views are all readable and the scope is what restricts."""
    out = []
    for name in ORDER:
        scope, add = SCOPE[matrix[name]]
        out.append({'worksheetId': WORKSHEETS[name], 'recordDataScope': dict(scope),
                    'recordActions': {'add': add},
                    'worksheetActions': {'export': role in EXPORTERS}})
    return out


# The V3 `worksheetActions.export` and the main-site model's `sheets[].worksheetExport.enable` are the same
# switch; create-fine writes the first, and there is no V3 call that edits a role afterwards. An existing role
# is changed the way the Roles page itself does it and the way `role rename` already does: read the whole
# appRoleModel with GetRoleDetail, change what must change, post it back with EditAppRole.
EXPORT_KEY = 'worksheetExport'
ADD_KEY = 'worksheetAddRecord'
# V3's per-worksheet `recordDataScope` {read, edit, delete} is `readLevel` / `editLevel` / `removeLevel` in the
# model the Roles page edits, and `recordActions.add` is `canAdd`. A write through either shows up in both.
LEVEL_KEY = {'read': 'readLevel', 'edit': 'editLevel', 'delete': 'removeLevel'}
# The action switches every worksheet of a business role carries, read off the seven sheets the roles were
# created with — they are
# identical in all four roles apart from the two the owner's table decides (`worksheetAddRecord` follows the
# create right, `worksheetExport` the exporter list). A worksheet created **after** a role is added to that role
# by HAP itself, with every switch on; this is the shape it is brought back to — "the same rule Products has".
SHEET_SWITCHES = {
    'worksheetShareView': False, 'worksheetImport': False, 'worksheetDiscuss': True, 'worksheetLogging': True,
    'worksheetBatchOperation': False, 'worksheetFilter': True, 'worksheetStats': True,
    'recordShare': False, 'recordDiscussion': True, 'recordSystemPrinting': False,
    'recordAttachmentDownload': True, 'recordLogging': False, 'payment': False,
}
# **Orders and Order Lines keep printing, and batch editing where the role may edit** (owner, 23 Sep 2026:
# "do what makes the most sense"). Printing a quotation or an order is the everyday act on these two, and a
# read-only accountant still needs a copy, so `recordSystemPrinting` is on for all four roles. Batch editing is
# an editing convenience, so it follows the add/edit right: on for Accounting Administrator, Accountant and
# Invoicing, off for Accounting Read-only. Everywhere else the table's own defaults still switch both off.
SHEET_SWITCH_OVERRIDES = {
    'Orders': {'recordSystemPrinting': True, 'worksheetBatchOperation': True},
    'Order Lines': {'recordSystemPrinting': True, 'worksheetBatchOperation': True},
}
PRINTERS_KEEP_BATCH = set(SHEET_SWITCH_OVERRIDES)

VIEW_RIGHTS = ('canRead', 'canEdit', 'canRemove')


def role_model(role_id):
    from hap_cli.core import role as role_mod
    from hap_cli.core.session import Session
    return role_mod.get_role_detail(Session.load(None), APP, role_id)


def save_role_model(role_id, model):
    from hap_cli.core.session import Session
    return Session.load(None).api_call('AppManagement', 'EditAppRole',
                                       {'appId': APP, 'roleId': role_id, 'appRoleModel': model})


def reconcile(name, role_id, description, matrix, dry=False):
    """Bring an existing business role's description, export right and per-worksheet scopes up to this spec,
    and nothing else.

    Everything not named here is posted back exactly as it was read, so the members, the field and view
    permissions and every other action switch cannot move. The scopes are in the call because **HAP adds a
    worksheet created after the role to every fine-grained role on its own**, at its own defaults — own records
    only (20 / 20 / 20), no create, and **export on** — which is neither the owner's table nor hap-cli's
    defaults. Product Categories arrived that way. Returns True when something was written."""
    model = role_model(role_id)
    want_export = name in EXPORTERS
    changed = [] if (model.get('description') or '') == description else ['description']
    model['description'] = description
    sheets = {s['sheetId']: s for s in model.get('sheets') or []}
    for worksheet, cell in matrix.items():
        sheet = sheets.get(WORKSHEETS[worksheet])
        if not sheet:
            sys.exit(f'{name}: the role has no entry for {worksheet}')
        scope, add = SCOPE[cell]
        for right, key in LEVEL_KEY.items():
            if sheet.get(key) != scope[right]:
                sheet[key] = scope[right]
                changed.append(f'{worksheet}.{key}')
        if bool(sheet.get('canAdd')) != add:
            sheet['canAdd'] = add
            changed.append(f'{worksheet}.canAdd')
        switches = {**SHEET_SWITCHES, **SHEET_SWITCH_OVERRIDES.get(worksheet, {})}
        if worksheet in PRINTERS_KEEP_BATCH and not add:
            switches = {**switches, 'worksheetBatchOperation': False}
        for key, value in {**switches, ADD_KEY: add, EXPORT_KEY: want_export}.items():
            if bool((sheet.get(key) or {}).get('enable')) != value:
                sheet.setdefault(key, {'enable': False, 'range': 1, 'allowExport': False})
                sheet[key]['enable'] = value
                changed.append(f'{worksheet}.{key}')
        # A sheet HAP added on its own arrives with its views unreadable — and a sheet whose views are all
        # unreadable is **dropped on save, with EditAppRole still answering 1**, so the levels above would
        # never stick. Every other sheet's views are fully allowed: the record scope is the gate.
        for view in sheet.get('views') or []:
            for key in VIEW_RIGHTS:
                if not view.get(key):
                    view[key] = True
                    changed.append(f'{worksheet}.{view["viewName"]}.{key}')
        # the account fields (and their own tabs) hidden from this role, or shown to it
        targets = field_targets(name, sheet, worksheet)
        for field in sheet.get('fields') or []:
            hide = targets.get(field['fieldId'])
            if hide is None:
                continue
            for key in FIELD_SWITCHES:
                if bool(field.get(key)) != hide:
                    field[key] = hide
                    changed.append(f'{worksheet}.{field["fieldName"]}.{key}')
    if dry:                                       # `plan`: what would be written, and nothing written
        return changed
    if not changed:
        return False
    save_role_model(role_id, model)
    back = {s['sheetId']: s for s in role_model(role_id).get('sheets') or []}
    wrong = {}
    for worksheet, cell in matrix.items():
        scope, add = SCOPE[cell]
        sheet = back.get(WORKSHEETS[worksheet], {})
        targets = field_targets(name, sheet, worksheet) if sheet else {}
        got = (tuple(sheet.get(LEVEL_KEY[r]) for r in ('read', 'edit', 'delete')), bool(sheet.get('canAdd')),
               {k: bool((sheet.get(k) or {}).get('enable')) for k in (*SHEET_SWITCHES, ADD_KEY, EXPORT_KEY)},
               all(v.get(k) for v in sheet.get('views') or [] for k in VIEW_RIGHTS), field_state(sheet, targets))
        want = (tuple(scope[r] for r in ('read', 'edit', 'delete')), add,
                {**SHEET_SWITCHES, ADD_KEY: add, EXPORT_KEY: want_export}, True,
                {fid: (hide,) * len(FIELD_SWITCHES) for fid, hide in targets.items()})
        if got != want:
            wrong[worksheet] = (got, want)
    if wrong:
        sys.exit(f'{name}: read back {json.dumps(wrong, ensure_ascii=False)}')
    print(f'  {name}: wrote {sorted(set(changed))}')
    return True


def step_plan():
    """What `create` would write, role by role, **without writing it**: {role: {worksheet names}} — 'description' for
    a role's description, and a note for a role that would be created. A builder adding a worksheet runs this first
    and runs `create` only when every change is on its own worksheet (incoterms.py, contacttags.py)."""
    guard()
    live = by_name()
    plan = {}
    for name, (description, matrix) in ROLES.items():
        if name not in live:
            plan[name] = {'(the role would be created)'}
        else:
            changed = reconcile(name, live[name]['roleId'], description, matrix, dry=True)
            plan[name] = {'description' if c == 'description' else c.split('.')[0] for c in changed}
            for entry in sorted(changed):
                print(f'  plan: {name} / {entry}')
        print(f"  plan: {name}: {sorted(plan[name]) or 'nothing to write'}")
    return plan


def step_create():
    """Create the four business roles, matched by name, then bring each one's description, export right and
    per-worksheet scopes up to this spec. No member is added to any of them."""
    guard()
    live = by_name()
    for name, (description, matrix) in ROLES.items():
        if name in live:
            print(f'  {name}: exists ({live[name]["roleId"]}); not re-created')
        else:
            hap.run('app', 'role', 'create-fine', APP, '-n', name, '-d', description,
                    '--worksheet-permissions',
                    json.dumps(worksheet_permissions(name, matrix), ensure_ascii=False))
            if name not in by_name():
                sys.exit(f'{name}: created but not in the role list')
            print(f'  {name}: created {by_name()[name]["roleId"]}')
        role_id = by_name()[name]['roleId']
        C.remember('roles', name, role_id)
        if reconcile(name, role_id, description, matrix):
            print(f"  {name}: description, scopes and export set (export "
                  f"{'on' if name in EXPORTERS else 'off'})")
    step_show()


def permissions(role_id):
    out = hap.run('app', 'role', 'permissions', role_id, '-a', APP)
    return out.get('data', out) if isinstance(out, dict) else {}


def live_names():
    """{worksheetId: name} for every worksheet of the app — ids.json knows only the ones this build owns, and
    another administrator's new worksheet joins every fine-grained role on its own."""
    app = hap.run('app', 'info', '-a', APP).get('data', {})
    return {i['id']: i['name'] for s in app.get('sections', []) for i in s['items'] if i['type'] == 0}


def scopes(role_id):
    """{worksheet name: (recordDataScope, add)} for a role, worksheets not in the role left out."""
    names = {**live_names(), **{wid: name for name, wid in WORKSHEETS.items()}}
    out = {}
    for w in permissions(role_id).get('worksheetPermissions') or []:
        out[names.get(w['id'], w['id'])] = (w.get('recordDataScope'), (w.get('recordActions') or {}).get('add'))
    return out


def cell(scope, add):
    """The table's word for a stored scope, or the raw values when it is none of the three."""
    for word, (want, want_add) in SCOPE.items():
        if scope == want and add == want_add:
            return word
    return f'{scope} add={add}'


def step_show():
    for r in roles():
        print(f"  {r['name']:<24} {r['roleId']} roleType={r['roleType']:<3} "
              f"permissionWay={r.get('permissionWay'):<3} members={members(r) or '—'}")
        if r['name'] in ROLES:
            live = scopes(r['roleId'])
            for name in ORDER:
                s, add = live.get(name, (None, None))
                print(f"      {name:<20} {cell(s, add)}")
            print(f"      {'export':<20} {'yes' if r['name'] in EXPORTERS else 'no'}")


def step_check():
    """Every role back against this spec; exits non-zero on a difference."""
    live = by_name()
    problems = []
    for english, chinese, role_type in STOCK:
        r = live.get(english)
        if not r:
            problems.append(f'stock role {english!r} missing (Chinese name still {chinese!r}?)')
        elif r['roleType'] != role_type:
            problems.append(f'{english}: roleType {r["roleType"]}, want {role_type}')
    admin = live.get('Administrator')
    if admin and members(admin) != ['Casimir Chiong Ming Yuan', 'Oscar Wong', 'Teh Li Wei']:
        problems.append(f'Administrator members {members(admin)}')
    v3 = v3_rows()
    for name, (description, matrix) in ROLES.items():
        r = live.get(name)
        if not r:
            problems.append(f'role {name!r} missing')
            continue
        row = v3.get(r['roleId'], {})
        if members(r) or row.get('accounts') or row.get('departments') or row.get('jobs') \
                or row.get('departmentTrees') or row.get('orgRoleIds'):
            problems.append(f'{name}: has members {members(r)} {row.get("departments")} {row.get("jobs")}')
        detail = permissions(r['roleId'])
        if detail.get('permissionScope') != 0:
            problems.append(f'{name}: permissionScope {detail.get("permissionScope")}, want 0 (per worksheet)')
        if (detail.get('description') or '') != description:
            problems.append(f'{name}: description {detail.get("description")!r}')
        got = scopes(r['roleId'])
        if not set(ORDER) <= set(got):
            problems.append(f'{name}: worksheets missing {sorted(set(ORDER) - set(got))}')
        for ws in sorted(set(got) - set(ORDER)):     # another administrator's, mid-build: reported, not owned
            s, add = got[ws]
            print(f"  note: {name} / {ws} is not in the owner's table — HAP put it there at {cell(s, add)!r}")
        for ws in ORDER:
            s, add = got.get(ws, (None, None))
            if cell(s, add) != matrix[ws]:
                problems.append(f'{name} / {ws}: {cell(s, add)!r}, want {matrix[ws]!r}')
        owned = {WORKSHEETS[n] for n in ORDER}
        for w in detail.get('worksheetPermissions') or []:
            if w['id'] not in owned:
                continue
            actions = {k: v for k, v in (w.get('worksheetActions') or {}).items()}
            record = {k: v for k, v in (w.get('recordActions') or {}).items() if k != 'add'}
            if actions != worksheet_actions(name):
                problems.append(f'{name} / {w["id"]}: worksheetActions {actions}')
            if record != DEFAULT_RECORD_ACTIONS:
                problems.append(f'{name} / {w["id"]}: recordActions {record}')
        # The same switch in the model the Roles page itself edits, so a difference between the two shows up
        # rather than hiding behind whichever call is read.
        model = role_model(r['roleId'])
        stored = {bool((s.get(EXPORT_KEY) or {}).get('enable')) for s in model['sheets']
                  if s['sheetId'] in owned}
        if stored != {name in EXPORTERS}:
            problems.append(f'{name}: {EXPORT_KEY}.enable {stored}, want {name in EXPORTERS}')
        # the account fields: hidden where 09 §1 hides them, visible everywhere else — read in the Roles page's own
        # model and again through V3's fieldPermissions, which names the same switches read · edit · add
        v3_fields = {w['id']: {f['id']: f for f in w.get('fieldPermissions') or []}
                     for w in detail.get('worksheetPermissions') or []}
        for sheet in model['sheets']:
            worksheet = next((n for n, wid in WORKSHEETS.items() if wid == sheet['sheetId']), None)
            if worksheet in OWNED_FIELDS and missing_owned(sheet, worksheet):
                problems.append(f'{name} / {worksheet}: the role lists no field {missing_owned(sheet, worksheet)}')
            targets = field_targets(name, sheet, worksheet) if worksheet in OWNED_FIELDS else {}
            if not targets:
                continue
            stored_fields = field_state(sheet, targets)
            wanted_fields = {fid: (hide,) * len(FIELD_SWITCHES) for fid, hide in targets.items()}
            if stored_fields != wanted_fields:
                problems.append(f'{name} / {worksheet}: fields {stored_fields} != {wanted_fields}')
            v3 = v3_fields.get(sheet['sheetId'], {})
            v3_stored = {fid: (not v3.get(fid, {}).get('read'), not v3.get(fid, {}).get('edit'),
                               not v3.get(fid, {}).get('add')) for fid in targets}
            if v3_stored != wanted_fields:
                problems.append(f'{name} / {worksheet}: V3 fieldPermissions {v3_stored} != {wanted_fields}')
    extra = set(live) - {n for n, _, _ in STOCK} - set(ROLES)
    if extra:
        problems.append(f'unexpected role(s) {sorted(extra)}')
    print('  check: ' + ('OK — five stock roles in English with their roleType and members, four business '
                         'roles with their per-worksheet scopes, export on Accounting Administrator alone, the '
                         'account fields hidden from Invoicing and Accounting Read-only as 09 §1 says, '
                         'and no members'
                         if not problems else 'DIFFERENCES\n    ' + '\n    '.join(problems)))
    return len(problems)


def step_all():
    for name in ('rename', 'create'):
        print(f'\n── {name} ' + '─' * 60)
        STEPS[name]()
    print('\n── check ' + '─' * 60)
    return step_check()


STEPS = {
    'rename': step_rename,
    'create': step_create,
    'plan': step_plan,
    'all': step_all,
    'check': step_check,
    'show': step_show,
}

if __name__ == '__main__':
    step = sys.argv[1] if len(sys.argv) > 1 else 'check'
    if step not in STEPS:
        raise SystemExit(f"Unknown step {step!r}; choose from {', '.join(STEPS)}")
    result = STEPS[step](*sys.argv[2:])
    sys.exit(1 if isinstance(result, int) and result else 0)
