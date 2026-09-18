#!/usr/bin/env python3
"""Build Payment Terms (Odoo account.payment.term and account.payment.term.line, as on casimir.odoo.com saas~19.4)
in ERP Master — bundle 3 of the six.

It adds the worksheet **Payment Terms** with **Payment Term Lines** mounted inside it as the *Due Terms* table, seeds
the tenant's ten terms and eleven lines, and then **replaces the text stand-in on Invoices** with a real relation:
create it, carry the three values, read them back, delete the text control (owner-approved, DECISIONS 16 Sep 2026)
and re-point the read-only rule. Invoices gains automations C (the term follows the Customer / Vendor) and D (the Due
Date follows the term), Confirm dates the invoice it fills an Invoice Date on, and Contacts gains Customer and Vendor
Payment Terms, carried by its two sync automations. Requirements: nocoly/worksheets/10-payment-terms.md. Run from
the repo root with the CLI's interpreter:

    ~/.hap-venv/bin/python nocoly/build/payterms.py baseline    # snapshot every worksheet (controls, rules, views,
                                                                #    buttons, records), workflows and roles
    ~/.hap-venv/bin/python nocoly/build/payterms.py create      # 1. both worksheets in Invoicing after Journals; the
                                                                #    lines hidden from the sidebar
    ~/.hap-venv/bin/python nocoly/build/payterms.py fields      # 2. the plain controls of both, one save each
    ~/.hap-venv/bin/python nocoly/build/payterms.py mount       # 3. Payment Term Lines mounted as Due Terms
    ~/.hap-venv/bin/python nocoly/build/payterms.py computed    # 4. the lines' Display name; Percent total, Line count
    ~/.hap-venv/bin/python nocoly/build/payterms.py layout      # 5. places, permissions, help, hints, title fields
    ~/.hap-venv/bin/python nocoly/build/payterms.py rules       # 6. the four term rules and the three line rules
    ~/.hap-venv/bin/python nocoly/build/payterms.py buttons     # 7. Archive / Unarchive
    ~/.hap-venv/bin/python nocoly/build/payterms.py views       # 8. Payment Terms, Archived; Lines
    ~/.hap-venv/bin/python nocoly/build/payterms.py roles       # 9. roles.py create (both worksheets join the roles)
    ~/.hap-venv/bin/python nocoly/build/payterms.py seed        # 10. the ten terms and their eleven lines
    ~/.hap-venv/bin/python nocoly/build/payterms.py invoices    # 11. the relation on Invoices, placed beside Due Date
    ~/.hap-venv/bin/python nocoly/build/payterms.py automations # 12. D, D on a create with no Customer / Vendor, C,
                                                                #     and Confirm's dating (invoices.py numbering)
    ~/.hap-venv/bin/python nocoly/build/payterms.py carry       # 13. the three values into the relation, read back
    ~/.hap-venv/bin/python nocoly/build/payterms.py retire      # 14. delete the text control, alias the relation,
                                                                #     re-point the rule, the two new rules
    ~/.hap-venv/bin/python nocoly/build/payterms.py contacts    # 15. Customer / Vendor Payment Terms on Contacts, the
                                                                #     two sync automations, the three contacts

    ~/.hap-venv/bin/python nocoly/build/payterms.py verify      # terms and lines against the extract; the references
    ~/.hap-venv/bin/python nocoly/build/payterms.py check       # the configuration against §1
    ~/.hap-venv/bin/python nocoly/build/payterms.py selfcheck   # automations C, D, Confirm and the contacts' sync on
                                                                #    TEST records (left in place); `selfcheck c
                                                                #    confirm` runs only those parts (d · c · confirm ·
                                                                #    once · contacts); `once`: each action dates an
                                                                #    invoice exactly once
    ~/.hap-venv/bin/python nocoly/build/payterms.py order       # each view's records in the view's own order
    ~/.hap-venv/bin/python nocoly/build/payterms.py deadrefs    # every view, rule and workflow node scanned for the
                                                                #    deleted text control's id
    ~/.hap-venv/bin/python nocoly/build/payterms.py records     # every record against the baseline snapshot
    ~/.hap-venv/bin/python nocoly/build/payterms.py all         # create … contacts, automations, carry, retire, then
                                                                #    check
    ~/.hap-venv/bin/python nocoly/build/payterms.py show        # the live controls of both worksheets

Every step reads the live state first and is safe to re-run. **The one deletion is the Invoices text control
`6aa920d74a73a3142152e68d`**, and `retire` refuses to make it until the three documents' values read back from the
relation. Nothing else is deleted, and the Sales app is never written to.

The order matters once: `contacts` before `automations` (C reads the contacts' terms), `automations` before `carry`
(so the carried values start D, whose dates must equal the tenant's), `carry` before `retire`.

Profile. As in the other builders: --profile > $HAP_PROFILE > hap-cli's active profile.
"""
import base64
import calendar
import datetime
import json
import os
import sys
import time
from pathlib import Path

import common as C
import hap

APP = hap.ids()['app']
ORG = hap.ids()['org']
SALES_APP = '3e596740-d096-42cd-b948-0b62a0220927'   # the Nocoly Sales app: never written to
SECTION = 'Invoicing'
TERMS_WS = 'Payment Terms'
LINES_WS = 'Payment Term Lines'
KEY = TERMS_WS + ': '                                 # ids.json prefixes
LINE_KEY = LINES_WS + ': '
INV_KEY = 'Invoices: '
CON_KEY = 'Contacts: '
HERE = Path(__file__).resolve().parent
DATA = HERE.parent / 'data' / 'casimir-payment-terms.json'
TEXT_STANDIN = '6aa920d74a73a3142152e68d'             # Invoices' text Payment Terms — the one approved deletion
ALL_WORKSHEETS = ('Contacts', 'Units & Packagings', 'Products', 'Product Variants', 'Product Categories',
                  'Chart of Accounts', 'Journals', 'Invoices', 'Invoice Lines')


def wid(name):
    return hap.ids()['worksheets'][name]


def terms_ws():
    return wid(TERMS_WS)


def lines_ws():
    return wid(LINES_WS)


def data():
    return json.loads(DATA.read_text(encoding='utf-8'))


def read(*args, tries=4):
    """A read through the CLI, retried on a timeout or a dropped connection."""
    for attempt in range(tries):
        try:
            return hap.run(*args)
        except RuntimeError as error:
            if attempt == tries - 1 or not any(x in str(error) for x in ('Timeout', 'ConnectionError', 'timed out')):
                raise
            time.sleep(5)


def refuse_sales():
    if APP == SALES_APP:
        sys.exit('ids.json points at the Sales app — refusing to write')


# ── baseline: everything before the first write ─────────────────────────────

def snapshot_worksheet(name, records=True):
    w = wid(name)
    out = {'id': w, 'controls': hap.controls(w), 'rules': hap.listing('worksheet', 'rules', w),
           'buttons': hap.listing('worksheet', 'custom-actions', w),
           'views': [C.view_info(w, APP, v['viewId']) for v in hap.listing('worksheet', 'view', 'list', w, '-a', APP)]}
    if records:
        out['records'] = {r['rowid']: read('worksheet', 'record', 'get', w, r['rowid'], '-a', APP)['data']
                          for r in C.records(w, APP)}
    return out


def workflow_nodes(pid):
    """Every node of a workflow with its full configuration (`node get`)."""
    proc = read('workflow', 'node', 'list', pid)
    out = {}
    for node_id in proc.get('flowNodeMap') or {}:
        got = read('workflow', 'node', 'get', pid, node_id)
        out[node_id] = got.get('data', got) if isinstance(got, dict) else got
    return {'list': proc, 'nodes': out}


def step_baseline():
    """Snapshot the nine worksheets (controls, rules, buttons, views, every record through `record get`), every
    workflow of the app node by node, and the roles — before the first write of this bundle."""
    from hap_cli.core import role as role_mod
    from hap_cli.core.session import Session
    snap = {'taken': datetime.datetime.now().isoformat(), 'worksheets': {}, 'workflows': {}, 'roles': {}}
    for name in ALL_WORKSHEETS:
        snap['worksheets'][name] = snapshot_worksheet(name)
        print(f"  {name:<20} {len(snap['worksheets'][name]['controls'])} controls, "
              f"{len(snap['worksheets'][name]['records'])} records")
    for w in hap.listing('workflow', 'list', APP):
        pid = w.get('id') or w.get('processId')
        snap['workflows'][pid] = {'name': w.get('name'), **workflow_nodes(pid)}
    print(f"  {len(snap['workflows'])} workflows")
    session = Session.load(None)
    for r in role_mod.get_roles(session, APP):
        snap['roles'][r['roleId']] = {'name': r['name'], 'model': role_mod.get_role_detail(session, APP, r['roleId'])}
    print(f"  {len(snap['roles'])} roles")
    print('  saved', hap.backup('payterms_snapshot_baseline', snap))



# ── the two forms ───────────────────────────────────────────────────────────

def option(key, value, index, color, checked=False):
    return {'key': key, 'value': value, 'isDeleted': False, 'index': index, 'checked': checked, 'color': color}


# Odoo's selections, in Odoo's order. The keys are minted once here and never re-minted: records, rules, the
# automations and the code block point at them. (odoo value, label, key)
VALUE = [('percent', 'Percent', '5e48b2b8-241f-49d3-997b-0ca3194603f9'),
         ('fixed', 'Fixed', '68c45b22-6811-4a32-893a-0ca1eb2fb1a2')]
DELAY = [('days_after', 'Days after invoice date', 'bdbf57ea-0bb6-4bd2-aabc-8206c6144b2c'),
         ('days_after_end_of_month', 'Days after end of month', '1fe2f58f-1f11-454f-aea4-7695970c619d'),
         ('days_after_end_of_next_month', 'Days after end of next month', '33049fe8-863c-4ddb-b9de-df7ec7468a90'),
         ('days_end_of_month_on_the', 'Days end of month on the', '440c6586-b2a4-484c-b3e2-c7ad2c1ca2f1')]
REDUCED_TAX = [('included', 'On early payment', 'fe33ead7-44e6-4f14-8935-d6652ed3ab91'),
               ('excluded', 'Never', 'bf553d11-0141-4b6b-a26c-ab112b879345'),
               ('mixed', 'Always (upon invoice)', 'b6a24be7-3506-463d-8b69-cfe045672856')]
COLORS = ['#C9E6FC', '#C3F2F2', '#C2F1D2', '#FFE7B1']
SELECTIONS = {'Value': VALUE, 'Delay Type': DELAY, 'Reduced tax': REDUCED_TAX}
OPTIONS = {name: [option(key, label, i + 1, COLORS[i], checked=(i == 0)) for i, (_, label, key) in enumerate(sel)]
           for name, sel in SELECTIONS.items()}                    # Odoo's default is the first of each
KEY_OF = {name: {odoo: key for odoo, _, key in sel} for name, sel in SELECTIONS.items()}
LABEL_OF_KEY = {name: {key: label for _, label, key in sel} for name, sel in SELECTIONS.items()}
KEY_OF_LABEL = {name: {label: key for _, label, key in sel} for name, sel in SELECTIONS.items()}
DELAY_CODE = {key: odoo for odoo, _, key in DELAY}                 # what the code block reads

# Payment Terms (account.payment.term)
NAME, EARLY, DISC_PCT, DISC_DAYS, REDUCED = 'Payment Terms', 'Early Discount', 'Discount %', 'Discount Days', 'Reduced tax'
DUE_TERMS, SHOW_INST, NOTE, SEQUENCE, ACTIVE = 'Due Terms', 'Show installment dates', 'Description on the Invoice', \
    'Sequence', 'Active'
PCT_TOTAL, LINE_COUNT = 'Percent total', 'Line count'
# Payment Term Lines (account.payment.term.line)
TERM, DUE, VALUE_F, AFTER, DELAY_F, NEXT_MONTH, LINE_TITLE = 'Payment Terms', 'Due', 'Value', 'After', 'Delay Type', \
    'Days on the next month', 'Display name'

# §1's form layout: name -> (row, col, size). No tabs: Odoo's form has none. The hidden controls sit under the rest.
TERM_PLACE = {
    NAME: (0, 0, 12),
    EARLY: (1, 0, 12),
    DISC_PCT: (2, 0, 6), DISC_DAYS: (2, 1, 6),
    REDUCED: (3, 0, 6),
    DUE_TERMS: (4, 0, 12),
    SHOW_INST: (5, 0, 12),
    NOTE: (6, 0, 12),
    SEQUENCE: (7, 0, 6),
    ACTIVE: (8, 0, 6),
    PCT_TOTAL: (9, 0, 6), LINE_COUNT: (9, 1, 6),
}
LINE_PLACE = {
    TERM: (0, 0, 12),
    LINE_TITLE: (1, 0, 12),
    DUE: (2, 0, 6), VALUE_F: (2, 1, 6),
    AFTER: (3, 0, 6), DELAY_F: (3, 1, 6),
    NEXT_MONTH: (4, 0, 6),
}
TERM_ALIAS = {NAME: 'name', EARLY: 'early_discount', DISC_PCT: 'discount_percentage', DISC_DAYS: 'discount_days',
              REDUCED: 'early_pay_discount_computation', DUE_TERMS: 'line_ids', SHOW_INST: 'display_on_invoice',
              NOTE: 'note', SEQUENCE: 'sequence', ACTIVE: 'active',
              PCT_TOTAL: 'percent_total', LINE_COUNT: 'line_count'}          # the two helpers are not Odoo fields
LINE_ALIAS = {TERM: 'payment_id', DUE: 'value_amount', VALUE_F: 'value', AFTER: 'nb_days', DELAY_F: 'delay_type',
              NEXT_MONTH: 'days_next_month', LINE_TITLE: 'display_name'}
TERM_HINT = {NAME: 'e.g. 30 days', NOTE: 'Description on invoice (e.g. Payment terms: 30 days after invoice date)'}
LINE_HINT = {}
TERM_DESC = {  # Odoo's help, verbatim, where it has one (addons/account/models/account_payment_term.py)
    DISC_PCT: 'Early Payment Discount granted for this payment term',
    DISC_DAYS: 'Number of days before the early payment proposition expires',
    SEQUENCE: 'Terms are listed by this number, lowest first — Odoo sets it by dragging the term in its list.',
    ACTIVE: 'If the active field is set to False, it will allow you to hide the payment terms without removing it.',
    DUE_TERMS: 'When the invoice falls due: each line gives a date, and the Due Date of an invoice on this term is '
               'the latest of them. The worksheet Payment Term Lines, mounted here.',
    PCT_TOTAL: "The sum of Due over the Due Terms lines whose Value is Percent — Odoo's check that the "
               'percentages add up to 100 reads it.',
    LINE_COUNT: 'How many Due Terms lines the term has — the early discount rule reads it.',
}
LINE_DESC = {
    DUE: 'For percent enter a ratio between 0-100.',
    VALUE_F: 'Select here the kind of valuation related to this payment terms line.',
    TERM: 'The term this line belongs to — the link the Due Terms table on the term is built on.',
    LINE_TITLE: 'Due, Value, After and Delay Type — how a line reads wherever HAP shows its title.',
}
TERM_REQUIRED = {NAME, SEQUENCE}
LINE_REQUIRED = {TERM, VALUE_F, DELAY_F}
TERM_PERMISSION = {ACTIVE: '011', PCT_TOTAL: '011', LINE_COUNT: '011'}      # hidden
LINE_PERMISSION = {LINE_TITLE: '100'}                                       # read-only · hidden on create
TERM_TITLE, LINE_TITLE_FIELD = NAME, LINE_TITLE
DUE_DOT = 6                                                                 # Odoo's decimal precision Payment Terms
TERM_ADVANCED = {  # advancedSetting keys this script owns
    EARLY: {'defsource': C.static_default(0)},
    DISC_PCT: {'defsource': C.static_default(2)},
    DISC_DAYS: {'defsource': C.static_default(10)},
    REDUCED: {'defsource': C.static_default(KEY_OF['Reduced tax']['included'])},
    SHOW_INST: {'defsource': C.static_default(1)},
    SEQUENCE: {'defsource': C.static_default(10)},
    ACTIVE: {'defsource': C.static_default(1)},
}
LINE_ADVANCED = {
    DUE: {'dotformat': '1'},                     # 省略末尾的 0: 6 decimals kept, trailing zeros not shown
    VALUE_F: {'defsource': C.static_default(KEY_OF['Value']['percent'])},
    AFTER: {'defsource': C.static_default(0)},
    DELAY_F: {'defsource': C.static_default(KEY_OF['Delay Type']['days_after'])},
    NEXT_MONTH: {'defsource': C.static_default(10)},
}
TERM_DOT = {DISC_PCT: 2, DISC_DAYS: 0, SEQUENCE: 0}
LINE_DOT = {DUE: DUE_DOT, AFTER: 0, NEXT_MONTH: 0}
TERM_KIND = {NAME: 'TEXT', EARLY: 'SWITCH', DISC_PCT: 'NUMBER', DISC_DAYS: 'NUMBER', REDUCED: 'DROP_DOWN',
             SHOW_INST: 'SWITCH', NOTE: 'RICH_TEXT', SEQUENCE: 'NUMBER', ACTIVE: 'SWITCH'}
LINE_KIND = {DUE: 'NUMBER', VALUE_F: 'DROP_DOWN', AFTER: 'NUMBER', DELAY_F: 'DROP_DOWN', NEXT_MONTH: 'NUMBER'}
SUBTABLE_COLUMNS = (DUE, VALUE_F, AFTER, DELAY_F, NEXT_MONTH)
SUBLIST, RELATION, ROLLUP, FORMULA = 34, 29, 37, 53
SUM, COUNT = 5, 6                                # a roll-up's enumDefault

SPEC = {  # worksheet -> its tables
    TERMS_WS: dict(place=TERM_PLACE, alias=TERM_ALIAS, hint=TERM_HINT, desc=TERM_DESC, required=TERM_REQUIRED,
                   permission=TERM_PERMISSION, title=TERM_TITLE, advanced=TERM_ADVANCED, dot=TERM_DOT,
                   kind=TERM_KIND),
    LINES_WS: dict(place=LINE_PLACE, alias=LINE_ALIAS, hint=LINE_HINT, desc=LINE_DESC, required=LINE_REQUIRED,
                   permission=LINE_PERMISSION, title=LINE_TITLE_FIELD, advanced=LINE_ADVANCED, dot=LINE_DOT,
                   kind=LINE_KIND),
}


def ctl(worksheet, name):
    """A plain control of either worksheet, from SPEC."""
    s = SPEC[worksheet]
    row, col, size = s['place'][name]
    extra = {'dot': s['dot'][name]} if name in s['dot'] else None
    return C.control(s['kind'][name], name, (row, col, size), alias=s['alias'][name], hint=s['hint'].get(name, ''),
                     desc=s['desc'].get(name, ''), required=name in s['required'],
                     options=OPTIONS.get(name) if s['kind'][name] == 'DROP_DOWN' else None,
                     advanced_setting=dict(s['advanced'].get(name) or {}) or None, extra=extra)


# ── the other worksheets, compared control by control ───────────────────────

def control_state(c):
    import accounts                                # its comparable form: JSON settings parsed, Relation defaults by id
    return accounts.control_state(c)


def snap(names):
    """{worksheet: {controlId: comparable control}} for the named worksheets (by ids.json name)."""
    return {name: {c['controlId']: control_state(c) for c in hap.controls(wid(name))} for name in names}


def expect(before, label, changed=None, new=None, gone=None):
    """Read the worksheets of `before` again and stop unless the only differences are those named: `new` {worksheet:
    control names that may appear}, `changed` {worksheet: {control name: attributes that may change}} ('*' = any),
    `gone` {worksheet: control ids that may disappear}. Prints what did change."""
    import accounts
    after = snap(tuple(before))
    changed, new, gone = changed or {}, new or {}, gone or {}
    problems, seen, same = [], [], []
    for name in before:
        b, a = before[name], after[name]
        for cid in sorted(set(b) - set(a)):
            (seen if cid in gone.get(name, ()) else problems).append(
                f"{name}: {b[cid]['controlName']!r} ({cid}) is gone")
        for cid in sorted(set(a) - set(b)):
            (seen if a[cid]['controlName'] in new.get(name, ()) else problems).append(
                f"{name}: new control {a[cid]['controlName']!r} ({cid})")
        touched = False
        for cid in sorted(set(a) & set(b)):
            diff = [k for k in accounts.SIGNATURE if a[cid][k] != b[cid][k]]
            if not diff:
                continue
            touched = True
            allowed = changed.get(name, {}).get(b[cid]['controlName'], set())
            extra = [k for k in diff if k not in allowed and '*' not in allowed]
            if extra:
                problems.append(f"{name}: {b[cid]['controlName']!r} changed " + '; '.join(
                    f'{k} {json.dumps(b[cid][k], ensure_ascii=False)[:160]} -> '
                    f'{json.dumps(a[cid][k], ensure_ascii=False)[:160]}' for k in extra))
            else:
                seen.append(f"{name}: {b[cid]['controlName']!r} " + ', '.join(
                    f'{k} {b[cid][k]!r}→{a[cid][k]!r}' if k in ('row', 'col', 'size', 'controlName', 'alias') else k
                    for k in diff))
        if not touched and set(a) == set(b):
            same.append(f'{name} ({len(a)})')
    if problems:
        sys.exit(f'{label}: controls read back with differences nobody asked for — stopping:\n  '
                 + '\n  '.join(problems))
    print(f'  {label}: compared control by control')
    for line in seen:
        print(f'    {line}')
    print(f"    identical: {', '.join(same) or '—'}")
    return after


def rules_of(worksheet_id):
    return {r['name']: r for r in hap.listing('worksheet', 'rules', worksheet_id)}


def views_of(worksheet_id):
    return {v['name']: v for v in hap.listing('worksheet', 'view', 'list', worksheet_id, '-a', APP)}


# ── guard ───────────────────────────────────────────────────────────────────

STOCK = {'Name', 'Description', 'Attachment', '名称', '描述', '附件'}


def app_sections():
    return C.app_info(APP)['sections']


def guard(fresh=False):
    """Stop unless the profile reaches ERP Master › Invoicing and both worksheets hold only this script's work.
    `fresh` allows the stock controls of a brand-new worksheet."""
    refuse_sales()
    who = hap.run('auth', 'whoami')
    app = hap.run('app', 'info', '-a', APP).get('data', {})
    section = next((s for s in app.get('sections', []) if s['name'] == SECTION), None)
    if app.get('name') != 'ERP Master' or not section:
        sys.exit(f"profile {who.get('profile')!r} does not reach ERP Master › {SECTION}")
    problems = []
    for name, spec in SPEC.items():
        w = hap.ids()['worksheets'].get(name)
        if not w or not any(i['id'] == w for i in section['items']):
            sys.exit(f'{name} is not in ERP Master › {SECTION} — run `create` first')
        ctrls = hap.controls(w)
        known = set(spec['place']) | ({DUE_TERMS} if name == TERMS_WS else set()) | (STOCK if fresh else set())
        back = {c['controlId'] for c in ctrls if c['type'] == RELATION and c.get('dataSource') == hap.ids()[
            'worksheets'].get(TERMS_WS)}                   # the mount's back-relation, before `layout` names it
        problems += [f"{name}: unknown control {c['controlName']!r} ({c['controlId']})" for c in ctrls
                     if c['controlName'] not in known and c['controlId'] not in back]
        if len({c['controlName'] for c in ctrls}) != len(ctrls):
            problems.append(f"{name}: two controls share a name {sorted(c['controlName'] for c in ctrls)}")
        problems += [f'{name}: unknown rule {n!r}' for n in set(rules_of(w)) - set(RULES[name])]
        problems += [f'{name}: unknown view {n!r}' for n in set(views_of(w)) - set(VIEWS[name]) - {'All', '全部'}]
        buttons = {b['name'] for b in hap.listing('worksheet', 'custom-actions', w)}
        problems += [f'{name}: unknown button {n!r}' for n in buttons - set(BUTTONS.get(name, ()))]
    if problems:
        sys.exit("Payment Terms differs from this script's work — stopping:\n  " + '\n  '.join(problems))
    print(f"  guard: profile {os.environ.get('HAP_PROFILE') or who.get('profile')!r}, ERP Master › {SECTION} › "
          f"{TERMS_WS} and {LINES_WS}")


# ── 1 · the worksheets ──────────────────────────────────────────────────────

REMARKS = {TERMS_WS: 'Odoo account.payment.term: when an invoice falls due — "30 Days", "End of Following Month", '
                     '"30% Now, Balance 60 Days"',
           LINES_WS: 'Odoo account.payment.term.line: the lines of a payment term. Mounted as the Due Terms table '
                     'of Payment Terms, and hidden from the sidebar'}
ALIASES = {TERMS_WS: 'account_payment_term', LINES_WS: 'account_payment_term_line'}
ICONS = {TERMS_WS: 'sys_money-time_symbol', LINES_WS: 'sys_timeline_symbol'}     # `hap icon search 时间`
HIDDEN = 2                                      # HomeApp/SetWorksheetStatus: 1 shown · 2 hidden · 3 PC · 4 mobile


def main_site_items():
    """{worksheetId: item} from HomeApp/GetApp — the main-site view of the sidebar, with `status`."""
    from hap_cli.core.session import Session
    got = Session.load(None).api_call('HomeApp', 'GetApp', {'appId': APP, 'getSection': True})
    got = got.get('data', got)
    return {w['workSheetId']: w for s in got.get('sections') or [] for w in s.get('workSheetInfo') or []}


def step_create():
    """Both worksheets in Invoicing, ordered Chart of Accounts · Journals · Payment Terms · Payment Term Lines ·
    Invoices · Invoice Lines, and the lines hidden from the sidebar (HomeApp/SetWorksheetStatus, status 2)."""
    refuse_sales()
    section = hap.ids()['sections'][SECTION]
    if C.app_info(APP).get('name') != 'ERP Master':
        sys.exit('the profile does not reach ERP Master')
    before = snap(ALL_WORKSHEETS)
    for name in (TERMS_WS, LINES_WS):
        elsewhere = [s['name'] for s in app_sections() if s['id'] != section for i in s['items'] if i['name'] == name]
        if elsewhere:
            sys.exit(f'{name} already exists in {elsewhere}')
        w = C.ensure_worksheet(APP, section, name, alias=ALIASES[name], remark=REMARKS[name], icon=ICONS[name])
        C.remember('worksheets', name, w)
    items = [i['id'] for i in next(s for s in app_sections() if s['id'] == section)['items']]
    new = (terms_ws(), lines_ws())
    rest = [i for i in items if i not in new]
    at = rest.index(wid('Journals')) + 1
    order = rest[:at] + list(new) + rest[at:]
    if items != order:
        hap.run('app', 'sort-worksheets', APP, section, *order)
    back = [i['id'] for i in next(s for s in app_sections() if s['id'] == section)['items']]
    if back != order:
        sys.exit(f'{SECTION} reads back {back}, wanted {order}')
    if main_site_items().get(lines_ws(), {}).get('status') != HIDDEN:
        from hap_cli.core.session import Session
        ok = Session.load(None).api_call('HomeApp', 'SetWorksheetStatus',
                                         {'appId': APP, 'worksheetId': lines_ws(), 'status': HIDDEN})
        print(f'  {LINES_WS}: SetWorksheetStatus {HIDDEN} answered {ok!r}')
    item = main_site_items().get(lines_ws(), {})
    if item.get('status') != HIDDEN:
        sys.exit(f"{LINES_WS}: status reads back {item.get('status')!r}, wanted {HIDDEN}")
    expect(before, 'create')
    names = {v: k for k, v in hap.ids()['worksheets'].items()}
    for s in app_sections():
        if s['id'] == section:
            print(f"  {s['name']}: " + ' · '.join(f"{i['name']} ({i['id']}, {i.get('alias')})" for i in s['items']))
    print(f"  sidebar status (main site): " + ', '.join(f"{names.get(k, k)}={v.get('status')}"
                                                        for k, v in main_site_items().items() if k in
                                                        (terms_ws(), lines_ws())))


# ── 2 · the plain controls ──────────────────────────────────────────────────

def ref(c):
    return f"${c['controlId']}$"


def function_source(expression):
    """dataSource of a function formula (type 53)."""
    return json.dumps({'type': 'mdfunction', 'expression': expression, 'status': 1}, ensure_ascii=False)


def line_title_expression(f):
    """"100 Percent · 30 · Days after invoice date": Due, Value, After and Delay Type. A function formula sees a
    dropdown as its label; an empty After reads as nothing, which is what the line holds."""
    return f'CONCAT({ref(f[DUE])}," ",{ref(f[VALUE_F])}," · ",{ref(f[AFTER])}," · ",{ref(f[DELAY_F])})'


def step_fields():
    """One full save of each brand-new worksheet. Payment Terms reuses the stock title control's id for its name;
    Payment Term Lines takes Display name — a function formula over controls minted in the same save — as its
    title. The stock Description and Attachment of both worksheets, and the lines' stock Name, have no counterpart
    in §1 and are not sent, so the first save leaves them out — the first-save pattern every worksheet of this app
    was built with (08, 09)."""
    guard(fresh=True)
    before = snap(ALL_WORKSHEETS)
    for name in (TERMS_WS, LINES_WS):
        w = wid(name)
        existing = hap.controls(w)
        have = {c['controlName'] for c in existing}
        wanted = set(SPEC[name]['kind'])
        if wanted <= have:
            print(f'  {name}: the plain controls are already there; nothing saved')
            continue
        if have - STOCK:
            sys.exit(f'{name} already holds {sorted(have - STOCK)} — refusing to replace its controls')
        hap.backup(f'payterms_{ALIASES[name]}_controls_pre_fields', existing)
        ctrls = [ctl(name, n) for n in SPEC[name]['kind']]
        title = next(c for c in existing if c.get('attribute') == 1)
        if name == TERMS_WS:
            ctrls[0]['controlId'] = title['controlId']                        # NAME is first in TERM_KIND
            ctrls[0]['attribute'] = 1
        else:
            f = {c['controlName']: c for c in ctrls}
            row, col, size = LINE_PLACE[LINE_TITLE]
            formula = C.control('FORMULA_FUNC', LINE_TITLE, (row, col, size), alias=LINE_ALIAS[LINE_TITLE], hint='',
                                desc=LINE_DESC[LINE_TITLE], advanced_setting={'analysislink': '1', 'sorttype': 'en'},
                                extra={'enumDefault2': 2, 'dataSource': function_source(line_title_expression(f))})
            formula['attribute'] = 1
            formula['fieldPermission'] = LINE_PERMISSION[LINE_TITLE]
            ctrls.append(formula)
        C.save_controls(w, ctrls)
        print(f'  {name}: saved {[c["controlName"] for c in ctrls]}')
    expect(before, 'fields')
    for name in (TERMS_WS, LINES_WS):
        C.show(wid(name))


# ── 3 · the mount ───────────────────────────────────────────────────────────

def sub_list(ctrls=None):
    """The mounted Due Terms control on Payment Terms, or None."""
    return next((c for c in (ctrls if ctrls is not None else hap.controls(terms_ws()))
                 if c['type'] == SUBLIST and c.get('dataSource') == lines_ws()), None)


def back_relation(ctrls=None):
    """The lines' relation to their term — created by the mount, named by `layout`."""
    return next((c for c in (ctrls if ctrls is not None else hap.controls(lines_ws()))
                 if c['type'] == RELATION and c.get('dataSource') == terms_ws()), None)


def step_mount():
    """Mount Payment Term Lines as the Due Terms table of Payment Terms: `worksheet mount-subtable` makes the 子表
    on the term and the back-relation on the line carrying the id the server reserved (BUILDING.md). `layout`
    places both."""
    guard()
    before = snap(ALL_WORKSHEETS)
    if not sub_list():
        hap.backup('payterms_terms_controls_pre_mount', hap.controls(terms_ws()))
        hap.backup('payterms_lines_controls_pre_mount', hap.controls(lines_ws()))
        f = C.fields(lines_ws())
        columns = [f[n]['controlId'] for n in SUBTABLE_COLUMNS]
        out = hap.run('worksheet', 'mount-subtable', terms_ws(), lines_ws(), '--name', DUE_TERMS, '-a', APP,
                      '--show-controls', ','.join(columns), '--back-relate-name', TERM)
        print('  mount:', json.dumps(out, ensure_ascii=False)[:400])
    else:
        print(f'  {DUE_TERMS} is already mounted; nothing done')
    expect(before, 'mount')
    sub, back = sub_list(), back_relation()
    if not sub or not back:
        sys.exit(f'mount read back: subtable {bool(sub)}, back-relation {bool(back)}')
    if sub.get('sourceControlId') != back['controlId'] or back.get('sourceControlId') != sub['controlId']:
        sys.exit(f"the pair does not point at each other: {sub.get('sourceControlId')} / {back.get('sourceControlId')}")
    print(f"  {DUE_TERMS} {sub['controlId']} ↔ {back['controlName']!r} {back['controlId']} on {LINES_WS}")


# ── 4 · the roll-ups ────────────────────────────────────────────────────────

EQ_SINGLE = 51                                   # the filter editor's "is" on a single select (BUILDING.md)


def percent_filter(lf):
    """The roll-up's own filter — the view-editor enum: Value is Percent."""
    return [{'controlId': lf[VALUE_F]['controlId'], 'dataType': 11, 'spliceType': 1, 'filterType': EQ_SINGLE,
             'dateRange': 0, 'dateRangeType': 0, 'value': '', 'values': [KEY_OF['Value']['percent']],
             'minValue': '', 'maxValue': '', 'isAsc': False, 'dynamicSource': [], 'isGroup': False,
             'groupFilters': None, 'emptyRule': 0}]


def rollup(name, sub, source, aggregate, filters=None, dot=0):
    from hap_cli.core.app_creator.fields import rollup_control
    c = rollup_control(name, via_control_id=sub['controlId'], source_control_id=source['controlId'],
                       aggregate=aggregate, filters=filters)
    row, col, size = TERM_PLACE[name]
    c.update(controlName=name, alias=TERM_ALIAS[name], row=row, col=col, size=size, dot=dot, desc=TERM_DESC[name],
             hint='', fieldPermission=TERM_PERMISSION[name])
    return c


def rollup_state():
    f = C.fields(terms_ws())
    lf = C.fields(lines_ws())
    names = {c['controlId']: c['controlName'] for c in hap.controls(lines_ws())}
    names.update({c['controlId']: c['controlName'] for c in hap.controls(terms_ws())})
    out = {}
    for n in (PCT_TOTAL, LINE_COUNT):
        c = f.get(n)
        if not c:
            continue
        flt = json.loads((c.get('advancedSetting') or {}).get('filters') or '[]')
        out[n] = dict(type=c['type'], aggregate=c.get('enumDefault'), through=names.get((c.get('dataSource') or '').strip('$')),
                      of=names.get(c.get('sourceControlId')), dot=c.get('dot'),
                      filters=[(names.get(x.get('controlId')), x.get('filterType'),
                                [LABEL_OF_KEY['Value'].get(v, v) for v in x.get('values') or []]) for x in flt])
    return out


ROLLUP_WANT = {PCT_TOTAL: dict(type=ROLLUP, aggregate=SUM, through=DUE_TERMS, of=DUE, dot=DUE_DOT,
                               filters=[(VALUE_F, EQ_SINGLE, ['Percent'])]),
               LINE_COUNT: dict(type=ROLLUP, aggregate=COUNT, through=DUE_TERMS, of=LINE_TITLE, dot=0, filters=[])}


def step_computed():
    """Percent total — the sum of Due over the Due Terms rows whose Value is Percent — and Line count, both HAP
    汇总 (type 37) over the mounted table. Added with `add-fields` and re-saved (common.add_fields), as # Products
    was on Product Categories. The lines' Display name was made by `fields`."""
    guard()
    sub = sub_list()
    if not sub:
        sys.exit('run `mount` first')
    f, lf = C.fields(terms_ws()), C.fields(lines_ws())
    new = []
    if PCT_TOTAL not in f:
        new.append(rollup(PCT_TOTAL, sub, lf[DUE], 'sum', filters=percent_filter(lf), dot=DUE_DOT))
    if LINE_COUNT not in f:
        new.append(rollup(LINE_COUNT, sub, lf[LINE_TITLE], 'count'))
    if new:
        before = snap(ALL_WORKSHEETS)
        hap.backup('payterms_terms_controls_pre_computed', hap.controls(terms_ws()))
        C.add_fields(terms_ws(), new)
        expect(before, 'computed')
    state = rollup_state()
    print('  ' + json.dumps(state, ensure_ascii=False))
    if state != ROLLUP_WANT:
        sys.exit(f'roll-ups read back {state}, want {ROLLUP_WANT}')


# ── 5 · layout ──────────────────────────────────────────────────────────────

def desired(worksheet, c):
    """The attributes `layout` owns on control c, as they should read back."""
    s = SPEC[worksheet]
    name = c['controlName']
    if worksheet == TERMS_WS and name == DUE_TERMS:
        row, col, size = TERM_PLACE[name]
        columns = [C.fields(lines_ws())[n]['controlId'] for n in SUBTABLE_COLUMNS]
        return {'row': row, 'col': col, 'size': size, 'sectionId': '', 'alias': TERM_ALIAS[name],
                'desc': TERM_DESC[name], 'showControls': columns}
    row, col, size = s['place'][name]
    out = {'row': row, 'col': col, 'size': size, 'sectionId': '', 'alias': s['alias'][name],
           'hint': s['hint'].get(name, ''), 'desc': s['desc'].get(name, ''), 'required': name in s['required'],
           'fieldPermission': s['permission'].get(name, '111'), 'attribute': 1 if name == s['title'] else 0}
    if name in s['dot']:
        out['dot'] = s['dot'][name]
    return out


DEFAULT_ROW_ID = 'temp-6c1d6a2e-0b8f-4f53-9d52-6f3a2d9e41b7'   # the editor mints `temp-<uuid>` for a default row


def due_terms_default(columns=None):
    """Odoo's _default_line_ids — a new term starts with one line, 100 Percent, 0 days after the invoice date — as a
    子表's custom default (自定义默认值, pd-openweb DynamicDefaultValue/inputTypes/SubSheet/CustomDefaultValue): the rows
    as a JSON string in `defsource[0].staticValue`, each keyed by the table's column ids plus pid, rowid and
    childrenids, a dropdown cell as its key list in a string. Like every default, the form applies it and the API
    does not."""
    lf = C.fields(lines_ws())
    row = {lf[DUE]['controlId']: '100', lf[VALUE_F]['controlId']: json.dumps([KEY_OF['Value']['percent']]),
           lf[AFTER]['controlId']: '0', lf[DELAY_F]['controlId']: json.dumps([KEY_OF['Delay Type']['days_after']]),
           lf[NEXT_MONTH]['controlId']: '10', 'pid': '', 'rowid': DEFAULT_ROW_ID, 'childrenids': ''}
    return json.dumps([{'rcid': '', 'cid': '', 'staticValue': json.dumps([row], ensure_ascii=False), 'isAsync': False}],
                      ensure_ascii=False)


def advanced_want(worksheet, c):
    if worksheet == TERMS_WS and c['controlName'] == DUE_TERMS:
        columns = [C.fields(lines_ws())[n]['controlId'] for n in SUBTABLE_COLUMNS]
        return {'controlssorts': json.dumps(columns, ensure_ascii=False), 'defsource': due_terms_default(),
                'dynamicsrc': '', 'defaulttype': '0'}
    return SPEC[worksheet]['advanced'].get(c['controlName'], {})


def layout_differences(worksheet, ctrls):
    out = {}
    places = dict(SPEC[worksheet]['place'], **({DUE_TERMS: None} if worksheet == TERMS_WS else {}))
    for c in ctrls:
        if c['controlName'] not in places:
            continue
        want = desired(worksheet, c)
        diff = {k: (c.get(k), v) for k, v in want.items()
                if (c.get(k) if k != 'attribute' else (c.get(k) or 0)) != v}
        adv = c.get('advancedSetting') or {}
        parsed = lambda k, v: (json.loads(v or '[]') if k == 'controlssorts' else
                               [dict(e, staticValue=json.loads(e.get('staticValue') or '[]')) for e in json.loads(v or '[]')]
                               if k == 'defsource' and worksheet == TERMS_WS and c['controlName'] == DUE_TERMS else v or '')
        diff.update({f'advancedSetting.{k}': (adv.get(k), v) for k, v in advanced_want(worksheet, c).items()
                     if parsed(k, adv.get(k)) != parsed(k, v)})
        if diff:
            out[c['controlName']] = diff
    return out


def step_layout():
    """Name the mount's back-relation, then place, alias, describe and permission every control of both
    worksheets, with Payment Terms and Display name as their titles — one read-modify-write save per worksheet."""
    guard()
    before = snap(ALL_WORKSHEETS)
    for worksheet in (LINES_WS, TERMS_WS):
        w = wid(worksheet)
        ctrls = hap.controls(w)
        if worksheet == LINES_WS:
            back = back_relation(ctrls)
            if back and back['controlName'] != TERM:
                print(f"  {back['controlName']!r} ({back['controlId']}) renamed to {TERM!r}")
                back['controlName'] = TERM
        places = set(SPEC[worksheet]['place']) | ({DUE_TERMS} if worksheet == TERMS_WS else set())
        missing = sorted(places - {c['controlName'] for c in ctrls})
        if missing:
            sys.exit(f'{worksheet}: {missing} are not there yet — run the earlier steps')
        changed = layout_differences(worksheet, ctrls)
        renamed = worksheet == LINES_WS and any(c['controlId'] == back_relation()['controlId'] and
                                                 c['controlName'] != back_relation()['controlName'] for c in ctrls)
        if changed or renamed:
            hap.backup(f'payterms_{ALIASES[worksheet]}_controls_pre_layout', ctrls)
            for c in ctrls:
                if c['controlName'] in places:
                    c.update(desired(worksheet, c))
                    c['advancedSetting'] = {**(c.get('advancedSetting') or {}), **advanced_want(worksheet, c)}
            C.save_controls(w, ctrls)
            print(f'  {worksheet}: updated ' + json.dumps(changed, ensure_ascii=False)[:1500])
        else:
            print(f'  {worksheet}: layout already as specified; nothing saved')
        left = layout_differences(worksheet, hap.controls(w))
        if left:
            sys.exit(f'{worksheet}: layout read back with differences: {json.dumps(left, ensure_ascii=False)}')
        prefix = KEY if worksheet == TERMS_WS else LINE_KEY
        for c in hap.controls(w):
            C.remember('controls', prefix + c['controlName'], c['controlId'])
    expect(before, 'layout', changed={TERMS_WS: {n: {'*'} for n in set(TERM_PLACE) | {DUE_TERMS}},
                                      LINES_WS: {n: {'*'} for n in LINE_PLACE} | {'Payment Terms': {'*'}}})
    for worksheet in (TERMS_WS, LINES_WS):
        C.show(wid(worksheet))


# ── 6 · rules ───────────────────────────────────────────────────────────────

GT, GTE, LT, LTE = 13, 14, 15, 16                 # the filter enum's number comparisons
R_DISCOUNT = 'The discount is set only for an early discount'
R_PERCENT = 'The percentages must add up to 100'
R_SINGLE = 'An early discount needs a single line'
R_POSITIVE = 'An early discount must be positive'
R_DAYS = 'An early discount needs days'
R_NEXT_MONTH = 'Days on the next month only for "Days end of month on the"'
R_PERCENT_RANGE = 'A percentage lies between 0 and 100'
R_DAYS_RANGE = 'The days added lie between 0 and 31'
MSG = {  # Odoo's messages, verbatim (the trailing space of the second one dropped)
    R_PERCENT: 'The Payment Term must have at least one percent line and the sum of the percent must be 100%.',
    R_SINGLE: 'The Early Payment Discount functionality can only be used with payment terms using a single 100% line.',
    R_POSITIVE: 'The Early Payment Discount must be strictly positive.',
    R_DAYS: 'The Early Payment Discount days must be strictly positive.',
    R_PERCENT_RANGE: 'Percentages on the Payment Terms lines must be between 0 and 100.',
    R_DAYS_RANGE: 'The days added must be between 0 and 31.',
}
PERCENT = ('Value', ['Percent'])
ON_THE = ('Delay Type', ['Days end of month on the'])
# worksheet -> rule name -> (type, OR of AND-groups of (control, operator, value), items, validation options).
# A value is a number, 1 for a ticked checkbox, None for "empty", or (selection, labels) for "is any of".
# Every "only for" interaction rule is a **show** while its condition holds, the house form (Journals, Chart of
# Accounts): §1's "hide while Early Discount is unchecked" and "hide while Delay Type is not …" read the same on
# every record that has a value, and a show also keeps the field hidden where the driver is empty.
RULES = {
    TERMS_WS: {
        R_DISCOUNT: (C.INTERACTION, [[(EARLY, C.EQ, 1)]], [(C.SHOW, [DISC_PCT, DISC_DAYS, REDUCED], '')], None),
        # _check_lines. Percent total is a roll-up: never in a write, so the server never checks this one and the
        # form is where it holds; shown on submit only, since a new term starts with no lines at all
        R_PERCENT: (C.VALIDATION, [[(PCT_TOTAL, C.NE, 100)], [(PCT_TOTAL, C.EMPTY, None)]],
                    [(C.ERROR, [DUE_TERMS], MSG[R_PERCENT])], {'check_type': 1, 'hint_type': 1}),
        R_SINGLE: (C.VALIDATION, [[(EARLY, C.EQ, 1), (LINE_COUNT, GT, 1)]],
                   [(C.ERROR, [EARLY], MSG[R_SINGLE])], {'check_type': 1, 'hint_type': 0}),
        R_POSITIVE: (C.VALIDATION, [[(EARLY, C.EQ, 1), (DISC_PCT, LTE, 0)], [(EARLY, C.EQ, 1), (DISC_PCT, C.EMPTY, None)]],
                     [(C.ERROR, [DISC_PCT], MSG[R_POSITIVE])], {'check_type': 1, 'hint_type': 0}),
        R_DAYS: (C.VALIDATION, [[(EARLY, C.EQ, 1), (DISC_DAYS, LTE, 0)], [(EARLY, C.EQ, 1), (DISC_DAYS, C.EMPTY, None)]],
                 [(C.ERROR, [DISC_DAYS], MSG[R_DAYS])], {'check_type': 1, 'hint_type': 0}),
    },
    LINES_WS: {
        R_NEXT_MONTH: (C.INTERACTION, [[(DELAY_F, C.EQ, ON_THE)]], [(C.SHOW, [NEXT_MONTH], '')], None),
        R_PERCENT_RANGE: (C.VALIDATION, [[(VALUE_F, C.EQ, PERCENT), (DUE, LT, 0)],
                                         [(VALUE_F, C.EQ, PERCENT), (DUE, GT, 100)]],
                          [(C.ERROR, [DUE], MSG[R_PERCENT_RANGE])], {'check_type': 1, 'hint_type': 0}),
        R_DAYS_RANGE: (C.VALIDATION, [[(NEXT_MONTH, LT, 0)], [(NEXT_MONTH, GT, 31)]],
                       [(C.ERROR, [NEXT_MONTH], MSG[R_DAYS_RANGE])], {'check_type': 1, 'hint_type': 0}),
    },
}

# Disabled after the UI test of 17 Sep 2026: a 汇总 over a 子表 does not follow the rows being edited in the open
# form, so both rules judged the saved lines and refused every new term — its default 100 % row included. They stay
# built, and disabled, so they can be switched back on the day HAP's roll-ups follow unsaved rows (10 §3).
DISABLED = {R_PERCENT, R_SINGLE}


def rule_condition(f, name, op, value):
    c = f[name]
    if isinstance(value, tuple):
        selection, labels = value
        return {'controlId': c['controlId'], 'dataType': c['type'], 'spliceType': 1, 'filterType': op, 'value': '',
                'values': [KEY_OF_LABEL[selection][label] for label in labels], 'dynamicSource': [], 'isGroup': False}
    return C.cond(c, op, value)


def rule_payload(worksheet, f, rule):
    kind, groups, items, options = RULES[worksheet][rule]
    filters = C.any_of(*[[rule_condition(f, *cond) for cond in group] for group in groups])
    return filters, [C.item(t, *[f[n] for n in targets], message=msg) for t, targets, msg in items], options


def all_controls(w):
    """Every control by name, a subtable included (C.fields leaves out tabs only)."""
    return hap.by_name(c for c in hap.controls(w) if c['type'] != C.TAB)


def rule_state(r, names):
    groups = sorted(sorted((names.get(c['controlId'], c['controlId']), c['filterType'],
                            tuple(sorted(str(v) for v in c.get('values') or [])))
                           for c in g.get('groupFilters') or []) for g in r.get('filters') or [])
    out = dict(type=r['type'], disabled=r['disabled'], groups=groups,
               items=[(i['type'], [names.get(x['controlId']) for x in i['controls']], i.get('message') or '')
                      for i in r.get('ruleItems') or []])
    if r['type'] == C.VALIDATION:
        out.update(check=r.get('checkType'), hint=r.get('hintType'))
    return out


def rule_want(worksheet, rule):
    kind, groups, items, options = RULES[worksheet][rule]

    def values(v):
        if isinstance(v, tuple):
            return tuple(sorted(KEY_OF_LABEL[v[0]][label] for label in v[1]))
        return () if v is None else (str(v),)
    out = dict(type=kind, disabled=rule in DISABLED,
               groups=sorted(sorted((n, op, values(v)) for n, op, v in g) for g in groups),
               items=[(t, list(targets), msg) for t, targets, msg in items])
    if kind == C.VALIDATION:
        out.update(check=options['check_type'], hint=options['hint_type'])
    return out


def rule_differences(worksheet):
    w = wid(worksheet)
    names = {c['controlId']: c['controlName'] for c in hap.controls(w)}
    live = rules_of(w)
    return {n: (rule_state(live[n], names) if n in live else None, rule_want(worksheet, n))
            for n in RULES[worksheet] if n not in live or rule_state(live[n], names) != rule_want(worksheet, n)}, live


def step_rules():
    guard()
    before = snap(ALL_WORKSHEETS)
    for worksheet in (TERMS_WS, LINES_WS):
        w = wid(worksheet)
        f = all_controls(w)
        todo, live = rule_differences(worksheet)
        hap.backup(f'payterms_{ALIASES[worksheet]}_rules_pre_rules', list(live.values()))
        for rule in todo:
            kind = RULES[worksheet][rule][0]
            filters, items, options = rule_payload(worksheet, f, rule)
            args = ['worksheet', 'save-rule', w, '--name', rule, '--type', str(kind),
                    '--filters', json.dumps(filters, ensure_ascii=False),
                    '--rule-items', json.dumps(items, ensure_ascii=False)]
            if kind == C.VALIDATION:
                args += ['--check-type', str(options['check_type']), '--hint-type', str(options['hint_type'])]
            args.append('--disabled' if rule in DISABLED else '--enabled')
            if rule in live:
                args += ['--rule-id', live[rule]['ruleId']]
            hap.run(*args)
            print(f"  {worksheet}: {'updated' if rule in live else 'created'} {rule!r}")
        left, live = rule_differences(worksheet)
        if left:
            sys.exit(f'{worksheet}: rules read back with differences: {json.dumps(left, ensure_ascii=False)}')
        if not todo:
            print(f'  {worksheet}: rules already as specified; nothing saved')
        names = {c['controlId']: c['controlName'] for c in hap.controls(w)}
        prefix = KEY if worksheet == TERMS_WS else LINE_KEY
        for rule, r in live.items():
            C.remember('rules', prefix + rule, r['ruleId'])
            print(f"    {r['ruleId']}  {rule}: {json.dumps(rule_state(r, names), ensure_ascii=False)}")
    expect(before, 'rules')


# ── 7 · buttons ─────────────────────────────────────────────────────────────

MSG_ARCHIVE = 'Are you sure that you want to archive this record?'
BUTTON_STEP = {'Archive': ('Archive the payment term', '0'), 'Unarchive': ('Unarchive the payment term', '1')}
BUTTONS = {TERMS_WS: ('Archive', 'Unarchive')}


def step_buttons():
    """Odoo ⚙ Actions › Archive / Unarchive, as on Journals and Chart of Accounts."""
    guard()
    import accounts
    active = C.fields(terms_ws())[ACTIVE]['controlId']
    when = lambda op: {'type': 'group', 'logic': 'AND', 'children': [
        {'type': 'condition', 'field': active, 'operator': op, 'value': ['1']}]}
    buttons = [
        ({'name': 'Archive', 'type': 'triggerWorkflow', 'enableWhen': when('eq'), 'isBatch': True,
          'confirm': True, 'confirmMsg': MSG_ARCHIVE, 'sureName': 'Archive', 'cancelName': 'Cancel'},
         [{'fieldId': active, 'value': '0'}], BUTTON_STEP['Archive'][0]),
        ({'name': 'Unarchive', 'type': 'triggerWorkflow', 'enableWhen': when('ne'), 'isBatch': True},
         [{'fieldId': active, 'value': '1'}], BUTTON_STEP['Unarchive'][0]),
    ]
    before = snap(ALL_WORKSHEETS)
    C.upsert_buttons(terms_ws(), APP, buttons, KEY, 'payterms_buttons_pre_buttons')
    expect(before, 'buttons')
    problems = button_differences()
    if problems:
        sys.exit('buttons read back with differences:\n  ' + '\n  '.join(problems))
    for name in BUTTONS[TERMS_WS]:
        print(C.structure(hap.ids()['workflows'][KEY + name]))


def button_differences():
    import accounts
    ctrls = hap.controls(terms_ws())
    names = {c['controlId']: c['controlName'] for c in ctrls}
    active = hap.by_name(ctrls)[ACTIVE]['controlId']
    live = {b['name']: b for b in hap.listing('worksheet', 'custom-actions', terms_ws())}
    out = []
    if sorted(live) != sorted(BUTTONS[TERMS_WS]):
        out.append(f'buttons {sorted(live)}')
    for name, op, confirm in (('Archive', C.EQ, MSG_ARCHIVE), ('Unarchive', C.NE, '')):
        b = live.get(name)
        if not b:
            continue
        conds = [(names.get(x['controlId']), x['filterType'], x.get('values')) for x in b.get('filters') or []]
        if conds != [(ACTIVE, op, ['1'])] or (b.get('confirmMsg') or '') != confirm:
            out.append(f"button {name}: filters={conds} confirm={b.get('confirmMsg')!r}")
        pid = hap.ids().get('workflows', {}).get(KEY + name)
        if not pid:
            out.append(f'no workflow id for {name}')
            continue
        proc, byname = accounts.nodes_by_name(pid)
        step, value = BUTTON_STEP[name]
        start = proc['startEventId']
        node = byname.get(step)
        if not node or proc['flowNodeMap'][start].get('nextId') != node['id']:
            out.append(f'{name} workflow: the trigger does not run into {step!r}')
            continue
        s = accounts.step_state(pid, node['id'])
        if s['selectNodeId'] != start or s['fields'] != [(active, value, '')] or s['isException']:
            out.append(f'{name} workflow step: {s}')
        info = hap.run('workflow', 'get', pid)
        info = info.get('data', info)
        if not info.get('enabled') or info.get('publishStatus') != 2:
            out.append(f"{name} workflow enabled={info.get('enabled')} publishStatus={info.get('publishStatus')}")
    return out


# ── 8 · views ───────────────────────────────────────────────────────────────

VIEW, ARCHIVED, LINES_VIEW = 'Payment Terms', 'Archived', 'Lines'
VIEWS = {TERMS_WS: (VIEW, ARCHIVED), LINES_WS: (LINES_VIEW,)}
TERM_COLUMNS = (NAME, NOTE)
LINE_COLUMNS = (TERM, DUE, VALUE_F, AFTER, DELAY_F, NEXT_MONTH)
CTIME = {'controlId': 'ctime', 'type': 16, 'controlName': 'Created'}   # the system field 创建时间


def view_specs(worksheet):
    f = C.fields(wid(worksheet))
    if worksheet == TERMS_WS:
        columns = [f[n]['controlId'] for n in TERM_COLUMNS]
        sort = C.sort_spec([f[SEQUENCE], CTIME])                  # Odoo's _order = "sequence, id"
        return {VIEW: (dict(viewType='table', filter=C.switch_filter(f[ACTIVE], 'eq'), tableFields=columns),
                       sort, columns),
                ARCHIVED: (dict(viewType='table', filter=C.switch_filter(f[ACTIVE], 'ne'), tableFields=columns),
                           sort, columns)}
    columns = [f[n]['controlId'] for n in LINE_COLUMNS]
    return {LINES_VIEW: (dict(viewType='table', tableFields=columns), C.sort_spec([f[TERM], CTIME]), columns)}


def view_state(worksheet, info):
    names = {c['controlId']: c['controlName'] for c in hap.controls(wid(worksheet))}
    names['ctime'] = 'Created'
    return dict(columns=[names.get(x, x) for x in info.get('showControls') or []],
                sort=[(names.get(s['controlId'], s['controlId']), s['isAsc']) for s in info.get('moreSort') or []],
                sortCid=names.get(info.get('sortCid'), info.get('sortCid')), sortType=info.get('sortType'),
                filters=[(names.get(x['controlId']), x['filterType'], x.get('values')) for x in info.get('filters') or []])


def view_want(worksheet, name):
    if worksheet == TERMS_WS:
        return dict(columns=list(TERM_COLUMNS), sort=[(SEQUENCE, True), ('Created', True)], sortCid=SEQUENCE,
                    sortType=2, filters=[(ACTIVE, C.EQ if name == VIEW else C.NE, ['1'])])
    return dict(columns=list(LINE_COLUMNS), sort=[(TERM, True), ('Created', True)], sortCid=TERM, sortType=2,
                filters=[])


def view_differences(worksheet):
    live = hap.listing('worksheet', 'view', 'list', wid(worksheet), '-a', APP)
    out = {}
    if [v['name'] for v in live] != list(VIEWS[worksheet]):
        out['order'] = [v['name'] for v in live]
    for name in VIEWS[worksheet]:
        v = next((x for x in live if x['name'] == name), None)
        state = view_state(worksheet, C.view_info(wid(worksheet), APP, v['viewId'])) if v else None
        if state != view_want(worksheet, name):
            out[name] = (state, view_want(worksheet, name))
    return out


def step_views():
    guard()
    before = snap(ALL_WORKSHEETS)
    for worksheet in (TERMS_WS, LINES_WS):
        todo = view_differences(worksheet)
        if todo:
            views = view_specs(worksheet)
            prefix = KEY if worksheet == TERMS_WS else LINE_KEY
            for name, vid in C.upsert_views(wid(worksheet), APP, views, f'payterms_{ALIASES[worksheet]}_views_pre_views',
                                            default_view=VIEWS[worksheet][0]).items():
                C.remember('views', prefix + name, vid)
            print(f'  {worksheet} order:', C.sort_views(wid(worksheet), APP, list(views)))
        left = view_differences(worksheet)
        if left:
            print(f'  {worksheet}: views read back with differences: {json.dumps(left, ensure_ascii=False)}')
        print(f"  {worksheet}: updated {', '.join(todo) if todo else 'nothing (already as specified)'}")
        C.print_views(wid(worksheet), APP)
    expect(before, 'views')


# ── 9 · roles ───────────────────────────────────────────────────────────────

def step_roles():
    """roles.py owns the roles; its ORDER and matrices now carry both worksheets — Accounting Administrator full,
    the other three view, Odoo's access list for account.payment.term(.line). HAP added both worksheets to every
    role by itself at its own defaults; `create` reconciles them."""
    import roles
    before = snap(ALL_WORKSHEETS)
    roles.step_create()
    expect(before, 'roles')
    return roles.step_check()


# ── 10 · the ten terms and their eleven lines ───────────────────────────────

def listed(v):
    if isinstance(v, str):
        try:
            v = json.loads(v) if v.startswith('[') else v
        except ValueError:
            pass
    return v if isinstance(v, list) else []


def option_label(v):
    labels = [x.get('value') if isinstance(x, dict) else x for x in listed(v)]
    return labels[0] if labels else None


def relation(v):
    """A Relation cell from `record get`: [(rowid, title)]."""
    return [(x.get('sid'), x.get('name')) for x in listed(v) if isinstance(x, dict)]


def flag(v):
    return str(v) in ('1', 'True', 'true')


def number(v):
    return None if v in (None, '') else float(v)


def read_term(rowid):
    d = read('worksheet', 'record', 'get', terms_ws(), rowid, '-a', APP)['data']
    return dict(rowid=rowid, name=d.get('name') or '', early_discount=flag(d.get('early_discount')),
                discount_percentage=number(d.get('discount_percentage')),
                discount_days=number(d.get('discount_days')),
                reduced_tax=option_label(d.get('early_pay_discount_computation')),
                display_on_invoice=flag(d.get('display_on_invoice')), note=d.get('note') or '',
                sequence=number(d.get('sequence')), active=flag(d.get('active')),
                percent_total=number(d.get('percent_total')), line_count=number(d.get('line_count')),
                lines=d.get('line_ids'), created=d.get('_createdAt') or d.get('ctime') or '')


def read_line(rowid):
    d = read('worksheet', 'record', 'get', lines_ws(), rowid, '-a', APP)['data']
    term = relation(d.get('payment_id'))
    return dict(rowid=rowid, term_rowid=term[0][0] if term else None, term=term[0][1] if term else None,
                value_amount=number(d.get('value_amount')), value=option_label(d.get('value')),
                nb_days=number(d.get('nb_days')), delay_type=option_label(d.get('delay_type')),
                days_next_month=number(d.get('days_next_month')), display_name=d.get('display_name') or '',
                created=d.get('_createdAt') or d.get('ctime') or '')


def read_terms():
    return {t['rowid']: t for t in (read_term(r['rowid']) for r in C.records(terms_ws(), APP))}


def read_lines():
    return {x['rowid']: x for x in (read_line(r['rowid']) for r in C.records(lines_ws(), APP))}


def lines_by_term(lines=None):
    """{term rowid: [line, …] in creation order}."""
    out = {}
    for line in sorted((lines or read_lines()).values(), key=lambda x: (x['created'], x['rowid'])):
        out.setdefault(line['term_rowid'], []).append(line)
    return out


def labels(json_data):
    return json_data['labels']


def want_term(t, lab):
    return dict(name=t['name'], early_discount=t['early_discount'], discount_percentage=float(t['discount_percentage']),
                discount_days=float(t['discount_days']),
                reduced_tax=lab['early_pay_discount_computation'][t['early_pay_discount_computation']],
                display_on_invoice=t['display_on_invoice'], note=t['note'], sequence=float(t['sequence']),
                active=t['active'])


def want_line(x, lab, term_name):
    return dict(term=term_name, value_amount=float(x['value_amount']), value=lab['value'][x['value']],
                nb_days=float(x['nb_days']), delay_type=lab['delay_type'][x['delay_type']],
                days_next_month=float(int(x['days_next_month'])))


def title_of_line(w):
    """What Display name should read: "100 Percent · 30 · Days after invoice date"."""
    due = w['value_amount']
    due = str(int(due)) if due == int(due) else f'{due:g}'
    return f"{due} {w['value']} · {int(w['nb_days'])} · {w['delay_type']}"


def term_values(f, w):
    cid = lambda n: f[n]['controlId']
    return [{'id': cid(NAME), 'value': w['name']},
            {'id': cid(EARLY), 'value': 1 if w['early_discount'] else 0},
            {'id': cid(DISC_PCT), 'value': w['discount_percentage']},
            {'id': cid(DISC_DAYS), 'value': w['discount_days']},
            {'id': cid(REDUCED), 'value': [KEY_OF_LABEL['Reduced tax'][w['reduced_tax']]]},
            {'id': cid(SHOW_INST), 'value': 1 if w['display_on_invoice'] else 0},
            {'id': cid(NOTE), 'value': w['note']},
            {'id': cid(SEQUENCE), 'value': w['sequence']},
            {'id': cid(ACTIVE), 'value': 1 if w['active'] else 0}]


def line_values(lf, term_rowid, w):
    cid = lambda n: lf[n]['controlId']
    return [{'id': cid(TERM), 'value': [term_rowid]},
            {'id': cid(DUE), 'value': w['value_amount']},
            {'id': cid(VALUE_F), 'value': [KEY_OF_LABEL['Value'][w['value']]]},
            {'id': cid(AFTER), 'value': w['nb_days']},
            {'id': cid(DELAY_F), 'value': [KEY_OF_LABEL['Delay Type'][w['delay_type']]]},
            {'id': cid(NEXT_MONTH), 'value': w['days_next_month']}]


def diff(live, want):
    return {k: (live.get(k), v) for k, v in want.items() if live.get(k) != v}


def step_seed():
    """The tenant's ten terms, created in its id order — so creation order breaks the Sequence tie as Odoo's id
    does — each followed by its lines. Matched by name (terms) and by position in creation order (lines); only a
    differing record is written, and each is read back at once."""
    guard()
    before = snap(ALL_WORKSHEETS)
    js = data()
    lab = labels(js)
    f, lf = all_controls(terms_ws()), all_controls(lines_ws())
    terms = {t['name']: t for t in read_terms().values()}
    grouped = lines_by_term()
    hap.backup('payterms_records_pre_seed', {'terms': terms, 'lines': grouped})
    for t in sorted(js['payment_terms'], key=lambda x: x['id']):
        want = want_term(t, lab)
        live = terms.get(t['name'])
        if live and not diff(live, want):
            rowid = live['rowid']
        else:
            body = json.dumps(term_values(f, want), ensure_ascii=False)
            if live:
                read('worksheet', 'record', 'update', terms_ws(), live['rowid'], '-a', APP, '--fields-json', body, tries=1)
                rowid = live['rowid']
                print(f"  updated {t['name']}")
            else:
                rowid = C.row_id(hap.run('worksheet', 'record', 'create', terms_ws(), '-a', APP, '--fields-json', body))
                print(f"  created {t['name']}: {rowid}")
                time.sleep(1.5)                     # a distinct creation second for every term: the view's tie-break
            back = read_term(rowid)
            if diff(back, want):
                sys.exit(f"{t['name']}: read back {diff(back, want)}")
        C.remember('records', KEY + t['name'], rowid)
        have = grouped.get(rowid, [])
        for i, x in enumerate(t['lines']):
            w = want_line(x, lab, t['name'])
            got = have[i] if i < len(have) else None
            if got and not diff(got, w):
                C.remember('records', f"{LINE_KEY}{t['name']} line {i + 1}", got['rowid'])
                continue
            body = json.dumps(line_values(lf, rowid, w), ensure_ascii=False)
            if got:
                hap.run('worksheet', 'record', 'update', lines_ws(), got['rowid'], '-a', APP, '--fields-json', body)
                line_rowid = got['rowid']
                print(f"    updated {t['name']} line {i + 1}")
            else:
                line_rowid = C.row_id(hap.run('worksheet', 'record', 'create', lines_ws(), '-a', APP,
                                              '--fields-json', body))
                print(f"    created {t['name']} line {i + 1}: {line_rowid}")
                time.sleep(1.1)
            back = read_line(line_rowid)
            if diff(back, w):
                sys.exit(f"{t['name']} line {i + 1}: read back {diff(back, w)}")
            C.remember('records', f"{LINE_KEY}{t['name']} line {i + 1}", line_rowid)
        if len(have) > len(t['lines']):
            print(f"  NOTE {t['name']} has {len(have)} lines, the extract {len(t['lines'])} — the extra ones are left")
    expect(before, 'seed')
    time.sleep(5)                                    # the roll-ups and the title formula settle
    return verify_terms()


def verify_terms():
    """Every term and line against the extract, the two roll-ups and every line's Display name included."""
    js = data()
    lab = labels(js)
    terms = {t['name']: t for t in read_terms().values()}
    grouped = lines_by_term()
    bad = 0
    for t in sorted(js['payment_terms'], key=lambda x: x['id']):
        live = terms.get(t['name'])
        if not live:
            print(f"  MISSING  {t['name']}")
            bad += 1
            continue
        want = dict(want_term(t, lab), percent_total=float(sum(x['value_amount'] for x in t['lines']
                                                               if x['value'] == 'percent')),
                    line_count=float(len(t['lines'])))
        d = diff(live, want)
        lines = grouped.get(live['rowid'], [])
        line_diffs = []
        for i, x in enumerate(t['lines']):
            w = want_line(x, lab, t['name'])
            w['display_name'] = title_of_line(w)
            got = lines[i] if i < len(lines) else {}
            if diff(got, w):
                line_diffs.append((i + 1, diff(got, w)))
        if len(lines) != len(t['lines']):
            line_diffs.append(('count', len(lines), len(t['lines'])))
        bad += bool(d or line_diffs)
        print(f"  {'OK  ' if not (d or line_diffs) else 'DIFF'}  {t['id']:>2} {t['name']:<32} seq={live['sequence']:g} "
              f"early={int(live['early_discount'])} {live['discount_percentage']:g}%/{live['discount_days']:g}d "
              f"{live['reduced_tax']!r} show={int(live['display_on_invoice'])} active={int(live['active'])} "
              f"total={live['percent_total']} lines={live['line_count']} note={live['note']!r}")
        for line in lines:
            print(f"          {line['display_name']!r:<48} next month {line['days_next_month']}")
        if d or line_diffs:
            print(f'        <- {d} {line_diffs}')
    extra = sorted(n for n in terms if n not in {t['name'] for t in js['payment_terms']})
    print(f"  {len(js['payment_terms'])} terms and {sum(len(t['lines']) for t in js['payment_terms'])} lines in the "
          f"extract; {bad} missing or differing; {len(extra)} terms not in the extract {extra}")
    return bad


# ── 11 · the relation on Invoices ───────────────────────────────────────────

INV_FIELD = 'Payment Terms'                           # the relation's name, once the stand-in has given it up
STANDIN_NAME = 'Payment Terms (text stand-in)'        # the stand-in's name while both exist
STANDIN_PARKED = (23, 0, 6)                           # under MyInvois, out of the relation's cell, until it is deleted
INV_PLACE = (4, 1, 6)                                 # Due Date | Payment Terms


def inv_ws():
    return wid('Invoices')


def picker_active():
    """The picker filter every payment-term Relation carries: the candidate's Active is checked (the UI's shape,
    as accounts.account_picker writes it). A picker filter runs in the browser only (BUILDING.md)."""
    import accounts
    active = C.fields(terms_ws())[ACTIVE]['controlId']
    return json.dumps([{'controlId': active, 'dataType': 36, **accounts.PICKER_BASE, 'filterType': C.EQ,
                        'value': '1', 'values': ['1'], 'dynamicSource': []}], ensure_ascii=False, separators=(',', ':'))


def term_relation(name, place, alias='', hint='', desc='', tab_id=''):
    """A one-way Relation → Payment Terms, single, shown as a dropdown, with the Active picker filter. Sent without a
    controlId so the server mints it, and — `bidirectional` "0" — Payment Terms gets no reverse control."""
    control = C.control('RELATE_SHEET', name, place, alias=alias, hint=hint, desc=desc, data_source=terms_ws(),
                        multi=False, advanced_setting={'bidirectional': '0', 'showtype': '3',
                                                       'filters': picker_active()})
    control['sectionId'] = tab_id
    return control


def inv_relation(ctrls=None):
    return next((c for c in (ctrls if ctrls is not None else hap.controls(inv_ws()))
                 if c['type'] == RELATION and c.get('dataSource') == terms_ws()), None)


def standin(ctrls=None):
    return next((c for c in (ctrls if ctrls is not None else hap.controls(inv_ws()))
                 if c['controlId'] == TEXT_STANDIN), None)


def picker_state(value):
    import accounts
    return accounts.picker_state(value)


def step_invoices():
    """§1 step 1 on Invoices: the relation Payment Terms beside Due Date, while the stand-in still holds its values.

    Both cannot share a name or a cell, so the stand-in is renamed "Payment Terms (text stand-in)" and parked under
    MyInvois first (one save), the relation is appended (`add-fields`, which parks it at row 9999) and then placed
    at row 4, right half (a second save). The stand-in keeps the alias `invoice_payment_term_id` until `retire`
    deletes it; the relation gets it there. Every save is compared control by control."""
    guard()
    ctrls = hap.controls(inv_ws())
    rel, text = inv_relation(ctrls), standin(ctrls)
    before = snap(ALL_WORKSHEETS)
    if not rel:
        if not text:
            sys.exit('neither the stand-in nor the relation is on Invoices — stopping')
        print('  backup:', hap.backup('payterms_invoices_controls_pre_relation', ctrls))
        if (text['controlName'], text['row'], text['col']) != (STANDIN_NAME, *STANDIN_PARKED[:2]):
            text.update(controlName=STANDIN_NAME, row=STANDIN_PARKED[0], col=STANDIN_PARKED[1], size=STANDIN_PARKED[2])
            C.save_controls(inv_ws(), ctrls)
            before = expect(before, 'the stand-in renamed and parked',
                            changed={'Invoices': {'Payment Terms': {'controlName', 'row', 'col', 'size'}}})
        C.append_controls(inv_ws(), [term_relation(INV_FIELD, INV_PLACE, hint='Payment Terms')])
        before = expect(before, 'the relation added', new={'Invoices': {INV_FIELD}})
    ctrls = hap.controls(inv_ws())
    rel = inv_relation(ctrls)
    row, col, size = INV_PLACE
    want = dict(controlName=INV_FIELD, row=row, col=col, size=size, sectionId='', hint='Payment Terms', desc='',
                required=False)
    if any(rel.get(k) != v for k, v in want.items()) or rel.get('fieldPermission') != '111':
        rel.update(want, fieldPermission='111')
        C.save_controls(inv_ws(), ctrls)
        before = expect(before, 'the relation placed', changed={'Invoices': {INV_FIELD: {'row', 'col', 'size',
                                                                                          'fieldPermission', 'hint'}}})
    rel = inv_relation()
    C.remember('controls', INV_KEY + INV_FIELD, rel['controlId'])
    print(f"  {INV_FIELD}: {rel['controlId']} row={rel['row']} col={rel['col']} size={rel['size']} "
          f"alias={rel.get('alias')!r} picker={picker_state((rel.get('advancedSetting') or {}).get('filters'))} "
          f"one-way={(rel.get('advancedSetting') or {}).get('bidirectional')!r} source={rel.get('sourceControlId')!r}")
    text = standin()
    print(f"  stand-in: {text and (text['controlName'], text['row'], text['col'], text.get('alias'))}")
    terms_ids = {c['controlId'] for c in hap.controls(terms_ws())}
    if rel.get('sourceControlId') in terms_ids:
        sys.exit('Payment Terms gained a reverse control — the relation was meant to be one-way')


# ── 12 · automations C and D, and Confirm's dating ──────────────────────────

SYSTEM_NODE = '5d39140d381d42d20db0c4da'          # the fixed 系统 node: nowTime, triggeraid, …
EQUALS_ID, IS_ANY_OF_ID, NOT_EMPTY_ID, EMPTY_ID, RELATION_EQ_ID = '9', '1', '7', '8', '33'
EXCLUSIVE = 2                                     # gatewayType 唯一分支
CONTINUE, STOP = 2, 0                             # a search step's executeType when nothing is found
IGNORE_WHEN_ABNORMAL = 1
JAVASCRIPT = '102'
CODE_NODE = 14
DATE = 15

AUTO_D = 'Invoices: Due Date follows the Payment Terms'
AUTO_C = 'Invoices: Payment Terms follow the Customer / Vendor'
DESC_D = ("Odoo account.move _compute_invoice_date_due: when an invoice's Payment Terms, Invoice Date or Accounting "
          'Date changes, and it has Payment Terms, its Due Date becomes the latest date the term\'s lines give from '
          'the Invoice Date — or the Accounting Date, or today.')
DESC_C = ("Odoo account.move _compute_invoice_payment_term_id: when an invoice is created or its Customer / Vendor "
          "changes, a customer document takes the contact's Customer Payment Terms and a vendor document its Vendor "
          'Payment Terms — each only when the contact has one — and a journal entry none; then the invoice is dated '
          'from its terms as automation D dates it.')
TRIGGER_D = "When an invoice's Payment Terms or dates change"
# D on a create: C's trigger (新增或更新 narrowed to Customer / Vendor) starts no run on a create that does not write
# Customer / Vendor (self-check, 17 Sep 2026), so an invoice created with Payment Terms and no contact would stay
# undated. This workflow dates exactly that case; every other create is C's.
AUTO_D_NEW = 'Invoices: Due Date of a new invoice with no Customer / Vendor'
DESC_D_NEW = ("Odoo account.move _compute_invoice_date_due, on a create automation C does not see: an invoice created with "
              "Payment Terms and no Customer / Vendor is dated from its term's lines, as automation D dates it.")
TRIGGER_D_NEW = 'When an invoice is created with Payment Terms and no Customer / Vendor'
TRIGGER_C = "When an invoice is created or its Customer / Vendor changes"

# The dating chain — the same five nodes at the end of C, D and Confirm (`ensure_dating`).
GET_INVOICE = 'Get the invoice as it now stands'
HAS_TERMS = 'Does the invoice have Payment Terms?'
PATH_TERMS = 'It has Payment Terms'
PATH_NO_TERMS = 'It has none — the Due Date is left as it is'
GET_LINES = "Get the term's lines"
COMPUTE_DUE = 'Compute the Due Date from the lines'
WRITE_DUE = 'Write the Due Date'
DATING = (GET_INVOICE, HAS_TERMS, GET_LINES, COMPUTE_DUE, WRITE_DUE)
CODE_INPUTS = ('invoice_date', 'accounting_date', 'today', 'current_due', 'delay', 'after', 'next_month')

# C's gateway: which Payment Terms the document takes.
GET_CONTACT = 'Get the customer / vendor'
C_GATEWAY = 'Which Payment Terms does the document take?'
C_PATH_ENTRY = 'Journal Entry — no Payment Terms'
C_PATH_CUSTOMER = "Customer document — the contact's Customer Payment Terms"
C_PATH_VENDOR = "Vendor document — the contact's Vendor Payment Terms"
C_PATH_KEEP = 'Otherwise — the Payment Terms are left as they are'
C_STEP_ENTRY = 'Empty the Payment Terms'
C_STEP_CUSTOMER = "Take the customer's Customer Payment Terms"
C_STEP_VENDOR = "Take the vendor's Vendor Payment Terms"
CUSTOMER_TERMS, VENDOR_TERMS = 'Customer Payment Terms', 'Vendor Payment Terms'

# 触发其他工作流, a workflow's process config `triggerType` (pd-openweb WorkflowSettings/ProcessConfig; `hap workflow
# config-get` / `config-set`): 0 允许触发, HAP's default — the workflow's writes start the event workflows they match (on
# its own worksheet only those narrowed to trigger fields) · 1 只能触发指定工作流, the ones in `processIds` · 2 不允许触发.
# C and Confirm date the invoice themselves, so their writes — C's Payment Terms, Confirm's Invoice Date — must not
# start D as well: each change dates the invoice once (owner, 17 Sep 2026: "Remove one"). D and D on a create write only
# the Due Date, which starts nothing, and keep the default.
NO_OTHER_WORKFLOWS = 2


def js_code():
    """The code block: Odoo's account.payment.term.line _get_due_date for every line, and the latest of them.

    The inputs arrive as text. A field of a get-multiple step reaches a code block as a list — parsed here whether it
    comes as a JSON array or comma-separated — and a dropdown as its key, its label or an option object, so every
    form is recognised. Dates are read as YYYY-MM-DD and computed in UTC, so no time zone moves a day."""
    known = {}
    for odoo, label, key in DELAY:
        known.update({key: odoo, label: odoo, odoo: odoo})
    return """var KNOWN = %s;
function list(v) {
  if (v === undefined || v === null) return [];
  if (Array.isArray(v)) return v;
  var s = String(v).trim();
  if (!s) return [];
  try { var j = JSON.parse(s); return Array.isArray(j) ? j : [j]; } catch (e) { return s.split(','); }
}
function scalar(v) {
  while (v && typeof v === 'object') v = Array.isArray(v) ? v[0] : (v.key || v.value || v.name || '');
  return v === undefined || v === null ? '' : String(v).trim();
}
function delayOf(v) {
  var s = scalar(v);
  if (KNOWN[s]) return KNOWN[s];
  var raw = typeof v === 'string' ? v : JSON.stringify(v);
  for (var k in KNOWN) { if (raw.indexOf(k) >= 0) return KNOWN[k]; }
  return 'days_after';
}
function int(v, dflt) { var n = parseInt(scalar(v), 10); return isNaN(n) ? dflt : n; }
function ymd(v) {
  var m = String(v || '').match(/(\\d{4})-(\\d{1,2})-(\\d{1,2})/);
  return m ? new Date(Date.UTC(+m[1], +m[2] - 1, +m[3])) : null;
}
function iso(d) { return d ? d.toISOString().slice(0, 10) : ''; }
var ref = ymd(input.invoice_date) || ymd(input.accounting_date) || ymd(input.today);
if (!ref) { var now = new Date(); ref = new Date(Date.UTC(now.getFullYear(), now.getMonth(), now.getDate())); }
var delays = list(input.delay), after = list(input.after), next = list(input.next_month);
var due = null;
for (var i = 0; i < delays.length; i++) {
  var kind = delayOf(delays[i]), n = int(after[i], 0), d;
  var y = ref.getUTCFullYear(), m = ref.getUTCMonth(), day = ref.getUTCDate();
  if (kind === 'days_after_end_of_month') {
    d = new Date(Date.UTC(y, m + 1, n));
  } else if (kind === 'days_after_end_of_next_month') {
    d = new Date(Date.UTC(y, m + 2, n));
  } else if (kind === 'days_end_of_month_on_the') {
    var x = new Date(Date.UTC(y, m, day + n)), xy = x.getUTCFullYear(), xm = x.getUTCMonth(), on = int(next[i], 1);
    if (on <= 0) {
      d = new Date(Date.UTC(xy, xm + 1, 0));
    } else {
      var last = new Date(Date.UTC(xy, xm + 2, 0)).getUTCDate();
      d = new Date(Date.UTC(xy, xm + 1, Math.min(on, last)));
    }
  } else {
    d = new Date(Date.UTC(y, m, day + n));
  }
  if (!due || d.getTime() > due.getTime()) due = d;
}
output = {
  due_date: due ? iso(due) : String(input.current_due || '').slice(0, 10),
  lines: String(delays.length),
  reference: iso(ref),
  seen: JSON.stringify({delay: input.delay, after: input.after, next_month: input.next_month})
};
""" % json.dumps(known, ensure_ascii=False)


def b64(text):
    return base64.b64encode(text.replace('\t', '    ').encode('utf-8')).decode('ascii')


def session():
    from hap_cli.core.session import Session
    return Session.load(None)


def nodes_by_name(pid):
    proc = read('workflow', 'node', 'list', pid)
    return proc, {n['name']: n for n in proc['flowNodeMap'].values()}


def node_get(pid, node_id):
    d = read('workflow', 'node', 'get', pid, node_id)
    return d.get('data', d) if isinstance(d, dict) else {}


def workflow_id(name):
    pid = hap.ids().get('workflows', {}).get(name)
    if pid:
        return pid
    return {w['name']: w.get('id') or w.get('processId') for w in hap.listing('workflow', 'list', APP)}.get(name)


def ensure_workflow(name, desc):
    pid = workflow_id(name)
    if not pid:
        out = hap.run('workflow', 'create', '-c', ORG, '-n', name, '-a', APP, '--type', 'worksheet', '-d', desc)
        got = out.get('data', out) if isinstance(out, dict) else out
        pid = got if isinstance(got, str) else (got.get('id') or got.get('processId'))
        if not pid:
            sys.exit(f'no process id in `workflow create` output: {out}')
        print(f'  created {name}: {pid}')
    C.remember('workflows', name, pid)
    info = read('workflow', 'get', pid)
    info = info.get('data', info)
    changed = False
    if (info.get('name'), info.get('explain') or '') != (name, desc):
        hap.run('workflow', 'update', pid, '-n', name, '-d', desc)
        changed = True
    return pid, changed


def inv_fields():
    return all_controls(inv_ws())


def cond(node_id, control, condition_id, values=None, type_id=None):
    """One workflow condition on `control` of the record `node_id` produced."""
    return {'nodeId': node_id, 'filedId': control['controlId'], 'filedValue': control['controlName'],
            'filedTypeId': type_id or control['type'], 'enumDefault': control.get('enumDefault', 0) if
            control['type'] == RELATION else 0, 'conditionId': condition_id, 'sourceType': 0,
            'conditionValues': values or []}


def type_is(node_id, f, labels):
    import invoices as I
    return cond(node_id, f['Type'], IS_ANY_OF_ID, [{'value': {'key': I.OPTION_KEY['Type'][label], 'value': label,
                                                              'isDeleted': False}} for label in labels])


def path_state(pid, node_id):
    d = node_get(pid, node_id)
    return [[(c.get('nodeId'), c.get('filedId'), str(c.get('conditionId')),
              sorted(((v.get('value') or {}).get('key') if isinstance(v.get('value'), dict) else v.get('value'))
                     for v in c.get('conditionValues') or []))
             for c in group] for group in d.get('conditions') or d.get('operateCondition') or []]


def condition_shape(groups):
    return [[(c['nodeId'], c['filedId'], c['conditionId'], sorted(v['value']['key'] for v in c['conditionValues']))
             for c in group] for group in groups]


def set_path(pid, node, name, groups):
    changed = False
    if path_state(pid, node['id']) != condition_shape(groups):
        hap.run('workflow', 'node', 'save', pid, node['id'], '--type', '2',
                '-c', json.dumps({'operateCondition': groups}, ensure_ascii=False), '-n', name)
        changed = True
    if node.get('name') != name:
        hap.run('workflow', 'node', 'rename', pid, node['id'], '-n', name)
        changed = True
    if path_state(pid, node['id']) != condition_shape(groups):
        sys.exit(f'path {name!r}: condition read back {path_state(pid, node["id"])}')
    return changed


def search_state(pid, node_id):
    d = node_get(pid, node_id)
    conds = [(c.get('filedId'), str(c.get('conditionId')), c.get('ignoreEmpty') or 0,
              [(v.get('nodeId'), v.get('controlId')) for v in c.get('conditionValues') or []])
             for flt in d.get('filters') or [] for group in flt.get('conditions') or [] for c in group]
    return dict(appId=d.get('appId'), actionId=str(d.get('actionId')), executeType=d.get('executeType'),
                execute=d.get('execute'), filters=conds)


def save_search(pid, node, worksheet, condition, execute_type, node_type=7, action_id='406', select=''):
    """A search (7/406) or get-multiple (13/400) step's filter the way the UI stores it: `filters`. A search carries
    `executeType` (what to do when nothing is found); a get-multiple step has none, and carries `execute` — true
    fetches the records when the step runs, false (the default) again every time a later step reads them."""
    multiple = node_type == 13
    want = dict(appId=worksheet, actionId=action_id, executeType=None if multiple else execute_type,
                execute=True if multiple else search_state(pid, node['id'])['execute'],
                filters=[(condition['filedId'], condition['conditionId'], condition.get('ignoreEmpty') or 0,
                          [(v.get('nodeId'), v.get('controlId')) for v in condition['conditionValues']])])
    if search_state(pid, node['id']) == want:
        return False
    config = {'actionId': action_id, 'appId': worksheet, 'selectNodeId': select,
              'filters': [{'spliceType': 2, 'conditions': [[condition]]}],
              'sorts': [{'controlId': 'ctime', 'controlType': 16, 'isAsc': True}]}
    config.update({'execute': True} if multiple else {'executeType': execute_type})
    hap.run('workflow', 'node', 'save', pid, node['id'], '--type', str(node_type), '-n', node['name'],
            '-c', json.dumps(config, ensure_ascii=False))
    got = search_state(pid, node['id'])
    if got != want:
        sys.exit(f"{node['name']}: read back {got}, want {want}")
    return True


def record_id_is(node_id, source_node, field_id, ignore=False):
    c = {'nodeId': node_id, 'nodeType': 7, 'actionId': '406', 'filedId': 'rowid', 'filedValue': 'Record ID',
         'filedTypeId': 2, 'enumDefault': 0, 'conditionId': EQUALS_ID, 'sourceType': 0,
         'conditionValues': [{'nodeId': source_node, 'controlId': field_id, 'value': '', 'sureNodeId': source_node}]}
    if ignore:
        c['ignoreEmpty'] = IGNORE_WHEN_ABNORMAL
    return c


def step_state(pid, node_id):
    d = node_get(pid, node_id)
    return dict(selectNodeId=d.get('selectNodeId'), appId=d.get('appId'), isException=bool(d.get('isException')),
                fields=[(x.get('fieldId'), x.get('nodeId') or '', x.get('fieldValueId') or '', x.get('fieldValue') or '',
                         bool(x.get('isClear'))) for x in d.get('fields') or []])


def save_update(pid, node, worksheet, select_node, fields):
    """An update step writing exactly `fields` on the record `select_node` produced."""
    want = (select_node, worksheet, False, [(x['fieldId'], x.get('nodeId') or '', x.get('fieldValueId') or '',
                                             x.get('fieldValue') or '', bool(x.get('isClear'))) for x in fields])
    s = step_state(pid, node['id'])
    if (s['selectNodeId'], s['appId'], s['isException'], s['fields']) == want:
        return False
    hap.run('workflow', 'node', 'save', pid, node['id'], '--type', '6', '-n', node['name'], '-c', json.dumps(
        {'actionId': '2', 'appId': worksheet, 'appType': 1, 'selectNodeId': select_node, 'fields': fields},
        ensure_ascii=False))
    s = step_state(pid, node['id'])
    if (s['selectNodeId'], s['appId'], s['isException'], s['fields']) != want:
        sys.exit(f"{node['name']}: read back {s}, want {want}")
    return True


def from_node(field_id, kind, node_id, source):
    """A field write taking another node's field: `nodeId` + `fieldValueId` (BUILDING.md)."""
    return {'fieldId': field_id, 'type': kind, 'addType': 0, 'fieldValue': '', 'fieldValueId': source,
            'nodeId': node_id, 'sureNodeId': node_id, 'nodeAppType': 1}


def empty_value(field_id, kind):
    """A field write that empties the field: `isClear` true, the editor's 清空 (pd-openweb UpdateFields). Sent as a plain
    empty value, the write is dropped from the step on save — `fields` reads back [] with no error."""
    return {'fieldId': field_id, 'type': kind, 'addType': 0, 'fieldValue': '', 'fieldValueId': '', 'nodeId': '',
            'isClear': True}


def dating_nodes():
    """The chain's skeleton for `batch-add`: the fresh read of the invoice, the gateway on its Payment Terms, and in
    its first path the lines and the update step. The code block goes in between them afterwards — `batch-add`
    refuses a code node (BUILDING.md) — and every filter, path and field write is saved again and read back."""
    return [
        {'nodeAlias': 'fresh', 'nodeType': 'get_single', 'name': GET_INVOICE,
         'config': {'worksheet': inv_ws(), 'execute_type': STOP}},
        {'nodeAlias': 'has_terms', 'nodeType': 'branch', 'name': HAS_TERMS, 'config': {'mode': 'exclusive', 'paths': [
            {'alias': 'terms_yes', 'name': PATH_TERMS, 'nodes': [
                {'nodeAlias': 'lines', 'nodeType': 'get_multiple', 'name': GET_LINES,
                 'config': {'worksheet': lines_ws()}},
                {'nodeAlias': 'write_due', 'nodeType': 'update_record', 'name': WRITE_DUE,
                 'config': {'target': {'node': {'nodeAlias': 'fresh'}}, 'worksheet': inv_ws(), 'fields': []}}]},
            {'alias': 'terms_no', 'name': PATH_NO_TERMS}]}},
    ]


def code_inputs(byname, f, lf):
    fresh, lines = byname[GET_INVOICE]['id'], byname[GET_LINES]['id']
    ref = lambda node, control: f'${node}-{control}$'
    return [{'name': 'invoice_date', 'value': ref(fresh, f['Invoice Date']['controlId'])},
            {'name': 'accounting_date', 'value': ref(fresh, f['Accounting Date']['controlId'])},
            {'name': 'today', 'value': ref(SYSTEM_NODE, 'nowTime')},
            {'name': 'current_due', 'value': ref(fresh, f['Due Date']['controlId'])},
            {'name': 'delay', 'value': ref(lines, lf[DELAY_F]['controlId'])},
            {'name': 'after', 'value': ref(lines, lf[AFTER]['controlId'])},
            {'name': 'next_month', 'value': ref(lines, lf[NEXT_MONTH]['controlId'])}]


TEST_INPUTS = {'invoice_date': '2026-09-17', 'accounting_date': '2026-09-17', 'today': '2026-09-17 12:00',
               'current_due': '', 'delay': json.dumps([KEY_OF['Delay Type']['days_after']] * 2),
               'after': '["0","60"]', 'next_month': '["10","10"]'}


def ensure_code_node(pid, byname, f, lf):
    """The code block between the lines and the update step: added with `node add --type 14`, saved with its inputs
    and code (base64, as the editor sends it), then run once through codeTest, which is what registers its output
    fields for the update step to read."""
    changed = False
    if COMPUTE_DUE not in byname:
        out = hap.run('workflow', 'node', 'add', pid, '--type', str(CODE_NODE), '-n', COMPUTE_DUE,
                      '--after', byname[GET_LINES]['id'], '-a', JAVASCRIPT)
        print(f'  code block added: {json.dumps(out, ensure_ascii=False)[:300]}')
        _, byname = nodes_by_name(pid)
        changed = True
    node = byname[COMPUTE_DUE]
    code, inputs = js_code(), code_inputs(byname, f, lf)
    got = node_get(pid, node['id'])
    live_code = ''
    try:
        live_code = base64.b64decode(got.get('code') or '').decode('utf-8')
    except (ValueError, UnicodeDecodeError):
        live_code = got.get('code') or ''
    live_inputs = [(x.get('name'), x.get('value')) for x in got.get('inputDatas') or [] if x.get('name')]
    if live_code.strip() != code.strip() or live_inputs != [(x['name'], x['value']) for x in inputs] or \
            str(got.get('actionId')) != JAVASCRIPT:
        from hap_cli.core import flow_node
        res = flow_node.save_node(session(), pid, node['id'], CODE_NODE,
                                  {'actionId': JAVASCRIPT, 'inputDatas': inputs, 'code': b64(code),
                                   # `testMap` is required: saveNode answers HTTP 500 without it (BUILDING.md)
                                   'testMap': got.get('testMap') or {}, 'version': got.get('version') or '',
                                   'maxRetries': got.get('maxRetries', 1)}, name=COMPUTE_DUE)
        print(f'  code block saved: {json.dumps(res, ensure_ascii=False)[:200]}')
        changed = True
    got = node_get(pid, node['id'])
    outputs = {c.get('controlId') or c.get('controlName') for c in got.get('controls') or []}
    if changed or not {'due_date', 'lines', 'reference'} <= outputs:
        from hap_cli.core import flow_node
        test = flow_node.test_code(session(), pid, node['id'], b64(code),
                                   [{**x, 'value': TEST_INPUTS[x['name']]} for x in inputs],
                                   action_id=JAVASCRIPT, version=got.get('version') or '')
        print(f'  codeTest: {json.dumps(test, ensure_ascii=False)[:600]}')
        if (test or {}).get('status') not in (1, None) and not (test or {}).get('data'):
            sys.exit(f'the code block did not run: {test}')
        got = node_get(pid, node['id'])
        print(f"  outputs registered: {[(c.get('controlId'), c.get('type')) for c in got.get('controls') or []]}")
    return changed


def ensure_dating(pid, after_node_id, alias='anchor'):
    """The dating chain, appended after `after_node_id` when it is not there, then every part brought up to spec:
    the fresh read of the invoice (Record ID = the trigger's), the gateway's two paths, the lines of the invoice's
    term (Payment Terms = the invoice's), the code block and the Due Date write. Returns True when anything was
    written; publishing is the caller's."""
    changed = False
    proc, byname = nodes_by_name(pid)
    if GET_INVOICE not in byname:
        hap.run('workflow', 'node', 'batch-add', pid, '--nodes', json.dumps(dating_nodes(), ensure_ascii=False),
                '--trigger-node-id', after_node_id, '--trigger-alias', alias)
        proc, byname = nodes_by_name(pid)
        changed = True
        print(f'  dating chain appended after {proc["flowNodeMap"][after_node_id]["name"]!r}')
    f, lf = inv_fields(), all_controls(lines_ws())
    start = proc['startEventId']
    changed |= save_search(pid, byname[GET_INVOICE], inv_ws(), record_id_is(byname[GET_INVOICE]['id'], start, 'rowid'),
                           STOP)
    gateway = byname[HAS_TERMS]
    paths = [proc['flowNodeMap'][i] for i in gateway.get('flowIds') or []]
    if len(paths) != 2:
        sys.exit(f'{HAS_TERMS}: {len(paths)} paths — left for a person to look at')
    yes = next(p for p in paths if p.get('nextId') not in (None, '', '99'))
    no = next(p for p in paths if p['id'] != yes['id'])
    fresh = byname[GET_INVOICE]['id']
    rel = f[INV_FIELD]
    changed |= set_path(pid, yes, PATH_TERMS, [[cond(fresh, rel, NOT_EMPTY_ID)]])
    changed |= set_path(pid, no, PATH_NO_TERMS, [[cond(fresh, rel, EMPTY_ID)]])
    lines_node = byname[GET_LINES]
    line_cond = {'nodeId': lines_node['id'], 'nodeType': 13, 'actionId': '400', 'filedId': lf[TERM]['controlId'],
                 'filedValue': TERM, 'filedTypeId': RELATION, 'enumDefault': 1, 'conditionId': RELATION_EQ_ID,
                 'sourceType': 0, 'conditionValues': [{'nodeId': fresh, 'controlId': rel['controlId'], 'value': '',
                                                       'sureNodeId': fresh}]}
    changed |= save_search(pid, lines_node, lines_ws(), line_cond, CONTINUE, node_type=13, action_id='400')
    proc, byname = nodes_by_name(pid)
    changed |= ensure_code_node(pid, byname, f, lf)
    proc, byname = nodes_by_name(pid)
    code_node = byname[COMPUTE_DUE]['id']
    changed |= save_update(pid, byname[WRITE_DUE], inv_ws(), fresh,
                           [from_node(f['Due Date']['controlId'], DATE, code_node, 'due_date')])
    order = dating_order(pid)
    if order != [GET_INVOICE, HAS_TERMS, PATH_TERMS, GET_LINES, COMPUTE_DUE, WRITE_DUE]:
        sys.exit(f'the dating chain reads {order}')
    return changed


def dating_order(pid):
    """The chain as it runs: the fresh read, the gateway, the Payment Terms path and the three steps in it."""
    proc, byname = nodes_by_name(pid)
    fm = proc['flowNodeMap']
    if GET_INVOICE not in byname:
        return []
    out, node = [GET_INVOICE], fm[byname[GET_INVOICE]['id']].get('nextId')
    if node in fm:
        out.append(fm[node]['name'])
        yes = next((fm[i] for i in fm[node].get('flowIds') or [] if fm[i].get('nextId') not in (None, '', '99')), None)
        if yes:
            out.append(yes['name'])
            n = yes.get('nextId')
            while n in fm:
                out.append(fm[n]['name'])
                n = fm[n].get('nextId')
    return out


def show():
    for name in (TERMS_WS, LINES_WS):
        print(f'── {name}')
        C.show(wid(name))


def step_order():
    """Each view's records in the order the view returns them, with the creation time that breaks a Sequence tie."""
    terms = read_terms()
    for v in hap.listing('worksheet', 'view', 'list', terms_ws(), '-a', APP):
        rows = C.records_in_view(terms_ws(), v['viewId']) if hasattr(C, 'records_in_view') else view_rows(terms_ws(), v)
        print(f"  {TERMS_WS} / {v['name']} ({len(rows)}):")
        for r in rows:
            t = terms.get(r['rowid'], {})
            print(f"    seq={t.get('sequence')} created={t.get('created')} {t.get('name')}")
    lines = read_lines()
    for v in hap.listing('worksheet', 'view', 'list', lines_ws(), '-a', APP):
        rows = view_rows(lines_ws(), v)
        print(f"  {LINES_WS} / {v['name']} ({len(rows)}):")
        for r in rows:
            x = lines.get(r['rowid'], {})
            print(f"    {x.get('term')!s:<34} created={x.get('created')} {x.get('display_name')}")


def view_rows(worksheet_id, view):
    res = read('worksheet', 'record', 'list', worksheet_id, '-a', APP, '-n', '200', '--view-id', view['viewId'],
               '--use-field-id-as-key')
    got = res.get('data', res) if isinstance(res, dict) else res
    return (got.get('rows') if isinstance(got, dict) else got) or []


# ── 15 · Contacts ───────────────────────────────────────────────────────────

CON_FIELDS = {  # name -> (alias, the tab)
    CUSTOMER_TERMS: ('property_payment_term_id', 'Sales & Purchase'),
    VENDOR_TERMS: ('property_supplier_payment_term_id', 'Sales & Purchase'),
}
CON_SEED = {'Sunway Construction Group': '30 Days', 'Klinik Kesihatan Damansara': '21 Days',
            'Sarawak Timber Logistics': '45 Days'}             # §1 Records: Customer Payment Terms; no vendor terms
CON_MOVED = ('Misc', 'Reference', 'Invoicing', 'Account Receivable', 'Account Payable', 'Notes', 'Active',
             'Display Name', 'Parent name')


def con_ws():
    return wid('Contacts')


def con_differences():
    """The two relations as §1 and contacts.py want them: alias, tab, place, one-way, the Active picker, desc."""
    import contacts
    ctrls = hap.controls(con_ws())
    tabs = {c['controlName']: c['controlId'] for c in ctrls if c['type'] == C.TAB}
    f = hap.by_name(c for c in ctrls if c['type'] != C.TAB)
    out = {}
    for name, (alias, tab) in CON_FIELDS.items():
        c = f.get(name)
        if not c:
            out[name] = 'missing'
            continue
        row, col, size, _ = contacts.PLACE[name]
        adv = c.get('advancedSetting') or {}
        got = dict(type=c['type'], dataSource=c.get('dataSource'), enumDefault=c.get('enumDefault'), alias=c.get('alias'),
                   sectionId=c.get('sectionId'), place=(c.get('row'), c.get('col'), c.get('size')), hint=c.get('hint') or '',
                   desc=c.get('desc') or '', required=bool(c.get('required')), fieldPermission=c.get('fieldPermission'),
                   bidirectional=adv.get('bidirectional'), showtype=adv.get('showtype'),
                   picker=picker_state(adv.get('filters')))
        want = dict(type=RELATION, dataSource=terms_ws(), enumDefault=1, alias=alias, sectionId=tabs[tab],
                    place=(row, col, size), hint='', desc=contacts.DESC[name], required=False, fieldPermission='111',
                    bidirectional='0', showtype='3', picker=picker_state(picker_active()))
        d = {k: (got[k], v) for k, v in want.items() if got[k] != v}
        if d:
            out[name] = d
    return out


def read_contact_terms(rowid):
    d = read('worksheet', 'record', 'get', con_ws(), rowid, '-a', APP)['data']
    first = lambda k: (relation(d.get(k)) or [(None, None)])[0]
    return dict(rowid=rowid, name=d.get('name'), company=(relation(d.get('parent_id')) or [(None, None)])[0][1],
                customer=first('property_payment_term_id')[1], vendor=first('property_supplier_payment_term_id')[1],
                customer_rowid=first('property_payment_term_id')[0], vendor_rowid=first('property_supplier_payment_term_id')[0],
                vat=d.get('vat') or '')


def step_contacts():
    """Customer and Vendor Payment Terms on Contacts' tab Sales & Purchase: added here with `add-fields` (parked at
    row 9999), placed by `contacts.py layout`, which owns the form; the two sync automations extended by
    `contacts.py automations`, which owns them; then the three companies' Customer Payment Terms."""
    import contacts
    guard()
    ctrls = hap.controls(con_ws())
    tabs = {c['controlName']: c['controlId'] for c in ctrls if c['type'] == C.TAB}
    have = {c['controlName'] for c in ctrls if c['type'] != C.TAB}
    missing = [n for n in CON_FIELDS if n not in have]
    before = snap(ALL_WORKSHEETS)
    if missing:
        print('  backup:', hap.backup('payterms_contacts_controls_pre_add', ctrls))
        C.append_controls(con_ws(), [term_relation(n, contacts.PLACE[n][:3], alias=CON_FIELDS[n][0],
                                                   desc=contacts.DESC[n], tab_id=tabs[CON_FIELDS[n][1]])
                                     for n in missing])
        before = expect(before, f'Contacts: add-fields {missing}', new={'Contacts': set(missing)})
    todo = con_differences()
    if todo:
        print(f'  Contacts: {json.dumps(todo, ensure_ascii=False)[:600]}; contacts.py layout places them')
        contacts.step_layout()
        before = expect(before, 'contacts.py layout', changed={'Contacts': {
            **{n: {'row', 'col', 'size', 'fieldPermission', 'sectionId'} for n in CON_FIELDS},
            **{n: {'row'} for n in CON_MOVED}}})
    left = con_differences()
    owned = {'alias', 'desc', 'hint', 'required', 'fieldPermission', 'bidirectional', 'showtype', 'picker'}
    if left and all(isinstance(d, dict) and set(d) <= owned for d in left.values()):
        # what this script owns and contacts.py's layout never writes: `add-fields` stores fieldPermission "" (BUILDING.md)
        ctrls = hap.controls(con_ws())
        print('  backup:', hap.backup('payterms_contacts_controls_pre_settings', ctrls))
        for c in ctrls:
            if c['controlName'] in left:
                alias = CON_FIELDS[c['controlName']][0]
                c.update(alias=alias, desc=contacts.DESC[c['controlName']], hint='', required=False, fieldPermission='111')
                c['advancedSetting'] = {**(c.get('advancedSetting') or {}), 'bidirectional': '0', 'showtype': '3',
                                        'filters': picker_active()}
        C.save_controls(con_ws(), ctrls)
        before = expect(before, 'Contacts: the relations\' own settings', changed={'Contacts': {
            n: {'alias', 'desc', 'hint', 'required', 'fieldPermission', 'advancedSetting'} for n in left}})
        left = con_differences()
    if left:
        sys.exit(f'Contacts: read back {json.dumps(left, ensure_ascii=False)}')
    for c in hap.controls(con_ws()):
        if c['controlName'] in CON_FIELDS:
            C.remember('controls', CON_KEY + c['controlName'], c['controlId'])
    print('  Contacts: both relations as specified')
    print('  ── contacts.py automations')
    contacts.step_automations()
    expect(before, 'contacts.py automations (no control may change)')
    seed_contacts()


def seed_contacts():
    f = all_controls(con_ws())
    terms = {t['name']: t['rowid'] for t in read_terms().values()}
    names = {r['rowid']: r for r in C.records(con_ws(), APP)}
    live = {}
    for rowid in names:
        c = read_contact_terms(rowid)
        live[c['name']] = c
    hap.backup('payterms_contacts_records_pre_seed', live)
    for name, term in CON_SEED.items():
        c = live.get(name)
        if not c:
            sys.exit(f'{name} is not in Contacts')
        if (c['customer'], c['vendor']) == (term, None):
            print(f'  OK    {name:<28} Customer Payment Terms {term} (already)')
            continue
        hap.run('worksheet', 'record', 'update', con_ws(), c['rowid'], '-a', APP, '--fields-json', json.dumps(
            [{'id': f[CUSTOMER_TERMS]['controlId'], 'value': [terms[term]]}]))
        back = read_contact_terms(c['rowid'])
        ok = (back['customer'], back['vendor']) == (term, None)
        print(f"  {'OK  ' if ok else 'DIFF'}  {name:<28} Customer Payment Terms {back['customer']}, Vendor "
              f"{back['vendor']}")
        if not ok:
            sys.exit(f'{name}: read back {back}')


def trigger_state(pid, start):
    t = node_get(pid, start)
    shape = [[(c.get('filedId'), str(c.get('conditionId'))) for c in group] for group in t.get('operateCondition') or []]
    return dict(appId=t.get('appId'), triggerId=str(t.get('triggerId')), fields=sorted(t.get('assignFieldIds') or []),
                condition=shape, name=t.get('name'))


def ensure_trigger(pid, start, event_id, fields, dsl_filter, name):
    """A worksheet-event trigger on Invoices: event, fields and condition, saved and read back."""
    from hap_cli.core.workflow_node_dsl import translate_condition_group
    want_condition = translate_condition_group(dsl_filter, {'trigger': start}) if dsl_filter else []
    want = dict(appId=inv_ws(), triggerId=event_id, fields=sorted(fields),
                condition=[[(c.get('filedId'), str(c.get('conditionId'))) for c in g] for g in want_condition], name=name)
    live = trigger_state(pid, start)
    changed = False
    if {k: live[k] for k in ('appId', 'triggerId', 'fields', 'condition')} != \
            {k: want[k] for k in ('appId', 'triggerId', 'fields', 'condition')}:
        hap.run('workflow', 'node', 'save', pid, start, '--type', '0', '-n', name, '-c', json.dumps(
            {'appId': inv_ws(), 'appType': 1, 'triggerId': event_id, 'assignFieldIds': fields,
             'operateCondition': want_condition, 'returns': []}, ensure_ascii=False))
        changed = True
    if trigger_state(pid, start)['name'] != name:
        hap.run('workflow', 'node', 'rename', pid, start, '-n', name)
        changed = True
    live = trigger_state(pid, start)
    if live != want:
        sys.exit(f'trigger read back {live}, want {want}')
    return changed


def quiet_state(pid):
    """(triggerType, processIds) of a workflow's process config — (2, []) when its writes start no other workflow."""
    cfg = read('workflow', 'config-get', pid)
    return cfg.get('triggerType'), list(cfg.get('processIds') or [])


def ensure_quiet(pid, label):
    """Make the workflow's own writes start no other workflow: its process config's 触发其他工作流 set to 不允许触发
    (`triggerType` 2). The whole config goes back as read — what the editor's Save sends (`revokeNodeIds` kept only
    while revoking is allowed, `value` trimmed) — and every other key is read back unchanged. Like the editor's save it
    leaves the workflow with unpublished changes: publishing is the caller's. Returns True when written."""
    cfg = read('workflow', 'config-get', pid)
    if (cfg.get('triggerType'), list(cfg.get('processIds') or [])) == (NO_OTHER_WORKFLOWS, []):
        return False
    print('  backup:', hap.backup('payterms_process_config_pre_quiet', {'processId': pid, 'label': label, 'config': cfg}))
    send = dict(cfg, triggerType=NO_OTHER_WORKFLOWS, processIds=[], value=(cfg.get('value') or '').strip(),
                revokeNodeIds=(cfg.get('revokeNodeIds') or []) if cfg.get('allowRevoke') else [])
    hap.run('workflow', 'config-set', pid, '-c', json.dumps(send, ensure_ascii=False))
    got = read('workflow', 'config-get', pid)
    moved = sorted(k for k in set(cfg) | set(got) if k not in ('triggerType', 'processIds') and got.get(k) != cfg.get(k))
    if (got.get('triggerType'), list(got.get('processIds') or [])) != (NO_OTHER_WORKFLOWS, []) or moved:
        sys.exit(f"{label}: process config read back triggerType {got.get('triggerType')} processIds "
                 f"{got.get('processIds')}; other keys changed {moved}")
    print(f"  {label}: 触发其他工作流 set to 不允许触发 (triggerType {cfg.get('triggerType')} → {NO_OTHER_WORKFLOWS})")
    return True


def publish_if(pid, changed, label):
    info = read('workflow', 'get', pid)
    info = info.get('data', info)
    if changed or not info.get('enabled') or info.get('publishStatus') != 2:
        result = C.publish(pid)
        print(f'  {label}: published {result}')
        if not result.get('isPublish'):
            sys.exit(f'{label}: publish failed: {result}')
    else:
        print(f'  {label}: already built and published; nothing written')


def build_d():
    """D · Due Date follows the Payment Terms: on an update that writes Payment Terms, Invoice Date or Accounting Date
    (仅更新 '4', narrowed to those three) of an invoice that has Payment Terms — the dating chain, nothing else. A
    create is C's: C dates the invoice it has just given its terms."""
    f = inv_fields()
    pid, changed = ensure_workflow(AUTO_D, DESC_D)
    proc, byname = nodes_by_name(pid)
    start = proc['startEventId']
    rel = f[INV_FIELD]
    dsl = {'logic': 'and', 'items': [{'left': {'node': {'nodeAlias': 'trigger'}, 'fieldId': rel['controlId'],
                                               '_filedTypeId': RELATION, '_enumDefault': 1, '_filedValue': INV_FIELD},
                                      'op': 'not_empty'}]}
    fields = [rel['controlId'], f['Invoice Date']['controlId'], f['Accounting Date']['controlId']]
    if GET_INVOICE not in byname:
        print('  backup:', hap.backup('payterms_automation_d_pre_build', proc))
        hap.run('workflow', 'node', 'batch-add', pid, '--nodes', json.dumps(dating_nodes(), ensure_ascii=False),
                '--trigger-worksheet', inv_ws(), '--trigger-event', 'update', '--trigger-fields', ','.join(fields),
                '--trigger-alias', 'trigger', '--trigger-filter', json.dumps(dsl, ensure_ascii=False))
        changed = True
    changed |= ensure_trigger(pid, start, '4', fields, dsl, TRIGGER_D)
    changed |= ensure_dating(pid, start)
    proc, _ = nodes_by_name(pid)
    if proc['flowNodeMap'][start].get('nextId') != nodes_by_name(pid)[1][GET_INVOICE]['id']:
        sys.exit(f'{AUTO_D}: the trigger does not run into {GET_INVOICE!r}')
    publish_if(pid, changed, AUTO_D)
    return pid


def d_new_filter(f):
    rel, partner = f[INV_FIELD], f['Customer / Vendor']
    return {'logic': 'and', 'items': [
        {'left': {'node': {'nodeAlias': 'trigger'}, 'fieldId': rel['controlId'], '_filedTypeId': RELATION,
                  '_enumDefault': 1, '_filedValue': INV_FIELD}, 'op': 'not_empty'},
        {'left': {'node': {'nodeAlias': 'trigger'}, 'fieldId': partner['controlId'], '_filedTypeId': RELATION,
                  '_enumDefault': 1, '_filedValue': partner['controlName']}, 'op': 'empty'}]}


def build_d_new():
    """D on a create (新增 '1') of an invoice with Payment Terms and no Customer / Vendor — the dating chain."""
    f = inv_fields()
    pid, changed = ensure_workflow(AUTO_D_NEW, DESC_D_NEW)
    proc, byname = nodes_by_name(pid)
    start = proc['startEventId']
    dsl = d_new_filter(f)
    if GET_INVOICE not in byname:
        print('  backup:', hap.backup('payterms_automation_d_new_pre_build', proc))
        hap.run('workflow', 'node', 'batch-add', pid, '--nodes', json.dumps(dating_nodes(), ensure_ascii=False),
                '--trigger-worksheet', inv_ws(), '--trigger-event', 'create', '--trigger-alias', 'trigger',
                '--trigger-filter', json.dumps(dsl, ensure_ascii=False))
        changed = True
    changed |= ensure_trigger(pid, start, '1', [], dsl, TRIGGER_D_NEW)
    changed |= ensure_dating(pid, start)
    if nodes_by_name(pid)[0]['flowNodeMap'][start].get('nextId') != nodes_by_name(pid)[1][GET_INVOICE]['id']:
        sys.exit(f'{AUTO_D_NEW}: the trigger does not run into {GET_INVOICE!r}')
    publish_if(pid, changed, AUTO_D_NEW)
    return pid


def c_paths(start, contact, f, cf):
    """C's gateway: (path name, condition groups, update step, the field write). Exhaustive, so that every document
    reaches the dating chain behind the gateway — a run that matches no path stops at the gateway (BUILDING.md)."""
    import invoices as I
    rel, partner = f[INV_FIELD], f['Customer / Vendor']
    return [
        (C_PATH_ENTRY, [[type_is(start, f, ['Journal Entry'])]], C_STEP_ENTRY, empty_value(rel['controlId'], RELATION)),
        (C_PATH_CUSTOMER, [[type_is(start, f, I.CUSTOMER_TYPES), cond(start, partner, NOT_EMPTY_ID),
                            cond(contact, cf[CUSTOMER_TERMS], NOT_EMPTY_ID)]],
         C_STEP_CUSTOMER, from_node(rel['controlId'], RELATION, contact, cf[CUSTOMER_TERMS]['controlId'])),
        (C_PATH_VENDOR, [[type_is(start, f, I.VENDOR_TYPES), cond(start, partner, NOT_EMPTY_ID),
                          cond(contact, cf[VENDOR_TERMS], NOT_EMPTY_ID)]],
         C_STEP_VENDOR, from_node(rel['controlId'], RELATION, contact, cf[VENDOR_TERMS]['controlId'])),
        (C_PATH_KEEP, [[type_is(start, f, I.CUSTOMER_TYPES), cond(start, partner, EMPTY_ID)],
                       [type_is(start, f, I.CUSTOMER_TYPES), cond(contact, cf[CUSTOMER_TERMS], EMPTY_ID)],
                       [type_is(start, f, I.VENDOR_TYPES), cond(start, partner, EMPTY_ID)],
                       [type_is(start, f, I.VENDOR_TYPES), cond(contact, cf[VENDOR_TERMS], EMPTY_ID)],
                       [cond(start, f['Type'], EMPTY_ID)]], None, None),
    ]


def c_nodes():
    paths = []
    for i, (name, _, step, _) in enumerate(c_paths('x', 'x', inv_fields(), all_controls(con_ws()))):
        p = {'alias': f'c_path{i}', 'name': name}
        if step:
            p['nodes'] = [{'nodeAlias': f'c_step{i}', 'nodeType': 'update_record', 'name': step,
                           'config': {'target': {'node': {'nodeAlias': 'trigger'}}, 'worksheet': inv_ws(), 'fields': []}}]
        paths.append(p)
    return [{'nodeAlias': 'contact', 'nodeType': 'get_single', 'name': GET_CONTACT,
             'config': {'worksheet': con_ws(), 'execute_type': CONTINUE}},
            {'nodeAlias': 'which_terms', 'nodeType': 'branch', 'name': C_GATEWAY,
             'config': {'mode': 'exclusive', 'paths': paths}}] + dating_nodes()


def build_c():
    """C · Payment Terms follow the Customer / Vendor: on a create, or an update writing Customer / Vendor (新增或更新
    '2' narrowed to it, which fires on a create only when the create writes it — BUILDING.md). The contact is read with
    its condition ignored when abnormal, so a document with no Customer / Vendor carries on, and every path guards the
    relation it was found through. Then the dating chain on every path: C dates the invoice itself, and its process
    config lets none of its writes start another workflow (`ensure_quiet`), so its write of the Payment Terms does not
    start D as well — one dating per run, whether or not the term changed."""
    f, cf = inv_fields(), all_controls(con_ws())
    pid, changed = ensure_workflow(AUTO_C, DESC_C)
    proc, byname = nodes_by_name(pid)
    start = proc['startEventId']
    partner = f['Customer / Vendor']
    if C_GATEWAY not in byname:
        print('  backup:', hap.backup('payterms_automation_c_pre_build', proc))
        hap.run('workflow', 'node', 'batch-add', pid, '--nodes', json.dumps(c_nodes(), ensure_ascii=False),
                '--trigger-worksheet', inv_ws(), '--trigger-event', 'create_or_update',
                '--trigger-fields', partner['controlId'], '--trigger-alias', 'trigger')
        changed = True
    changed |= ensure_trigger(pid, start, '2', [partner['controlId']], None, TRIGGER_C)
    proc, byname = nodes_by_name(pid)
    contact = byname[GET_CONTACT]['id']
    changed |= save_search(pid, byname[GET_CONTACT], con_ws(),
                           record_id_is(contact, start, partner['controlId'], ignore=True), CONTINUE)
    gateway = byname[C_GATEWAY]
    fm = proc['flowNodeMap']
    paths = [fm[i] for i in gateway.get('flowIds') or []]
    specs = c_paths(start, contact, f, cf)
    if len(paths) != len(specs):
        sys.exit(f'{C_GATEWAY}: {len(paths)} paths, want {len(specs)} — left for a person to look at')
    by_step = {}
    for node in paths:
        nxt = fm.get(node.get('nextId'))
        by_step.setdefault(nxt.get('name') if nxt else None, []).append((node, nxt))
    for name, groups, step, write in specs:
        found = by_step.get(step) or []
        if len(found) != 1:
            sys.exit(f'{AUTO_C}: {len(found)} path(s) run into {step!r} — left for a person to look at')
        node, nxt = found[0]
        changed |= set_path(pid, node, name, groups)
        if step:
            changed |= save_update(pid, nxt, inv_ws(), start, [write])
    changed |= ensure_dating(pid, gateway['id'])
    changed |= ensure_quiet(pid, AUTO_C)
    publish_if(pid, changed, AUTO_C)
    return pid


def step_automations():
    """C and D on Invoices, and the dating chain at the end of Confirm (invoices.py `numbering`, which owns Confirm)."""
    guard()
    if not inv_relation():
        sys.exit('run `invoices` first — the automations read and write the relation')
    import invoices
    before = snap(ALL_WORKSHEETS)
    print(f'  ── {AUTO_D}')
    build_d()
    print(f'  ── {AUTO_D_NEW}')
    build_d_new()
    print(f'  ── {AUTO_C}')
    build_c()
    print('  ── Invoices: Confirm (invoices.py numbering)')
    invoices.step_numbering()
    expect(before, 'automations (no control may change)')
    for name in (AUTO_D, AUTO_D_NEW, AUTO_C, INV_KEY + 'Confirm'):
        print(C.structure(hap.ids()['workflows'][name]))


# ── 13 · carry the three values ─────────────────────────────────────────────

CARRY = {'SCG-PO-88213': ('30 Days', '2026-10-09'), 'KKD-2026-009': ('21 Days', '2026-10-02'),
         'STL-2026-0042': ('45 Days', '2026-10-29')}         # §1 step 2, with the tenant's due dates


def read_invoice_terms(rowid, rel_id=None):
    """A document's Payment Terms as the relation holds them, the stand-in's text while it exists, and its dates."""
    d = read('worksheet', 'record', 'get', inv_ws(), rowid, '-a', APP)['data']
    rel_id = rel_id or inv_relation()['controlId']
    rel_alias = inv_relation().get('alias') if rel_id is None else None
    value = d.get(rel_id) if rel_id in d else d.get('invoice_payment_term_id')
    text = d.get('invoice_payment_term_id') if isinstance(d.get('invoice_payment_term_id'), str) and rel_id in d else None
    linked = relation(value)
    return dict(rowid=rowid, ref=d.get('ref') or '', number=d.get('name') or '', term=linked[0][1] if linked else None,
                term_rowid=linked[0][0] if linked else None, text=text, invoice_date=d.get('invoice_date') or '',
                date=d.get('date') or '', due=d.get('invoice_date_due') or '',
                type=option_label(d.get('move_type')), status=option_label(d.get('state')),
                partner=(relation(d.get('partner_id')) or [(None, None)])[0][1])


def step_carry():
    """§1 steps 2 and 3: the three documents' terms written into the relation — only where it does not hold them
    yet — each write starting automation D, whose Due Date must equal the tenant's; then every document read back,
    the three with their term and every other with none."""
    import accounts
    guard()
    rel = inv_relation()
    if not rel:
        sys.exit('run `invoices` first')
    terms = {t['name']: t['rowid'] for t in read_terms().values()}
    records = hap.ids()['records']
    pid = hap.ids()['workflows'][AUTO_D]
    hap.backup('payterms_invoices_records_pre_carry', {ref: read_invoice_terms(records[INV_KEY + ref], rel['controlId'])
                                                       for ref in CARRY})
    for ref, (term, due) in CARRY.items():
        rowid = records[INV_KEY + ref]
        d = read_invoice_terms(rowid, rel['controlId'])
        if d['ref'] != ref:
            sys.exit(f'{ref}: ids.json points at {d["ref"]!r}')
        if d['term'] == term:
            print(f"  --    {ref:<14} already carries {term} (Due Date {d['due']})")
            continue
        if standin() and d['text'] != term:
            sys.exit(f"{ref}: the stand-in holds {d['text']!r}, §1 says {term!r} — stopping")
        snapshot = run_snapshot(pid)
        hap.run('worksheet', 'record', 'update', inv_ws(), rowid, '-a', APP, '--fields-json',
                json.dumps([{'id': rel['controlId'], 'value': [terms[term]]}]))
        runs = wait_new_runs(pid, snapshot, 1, seconds=120)
        back = read_invoice_terms(rowid, rel['controlId'])
        ok = back['term'] == term and back['due'] == due
        print(f"  {'OK  ' if ok else 'DIFF'}  {ref:<14} {back['number']:<15} text {back['text']!r} → relation "
              f"{back['term']!r}; Invoice Date {back['invoice_date'] or '—'}, Accounting Date {back['date']}; Due Date "
              f"{back['due']} (tenant {due}); automation D runs {[(r['id'], r.get('status')) for r in runs]}")
        if not ok:
            sys.exit(f'{ref}: read back {back}')
    return verify_carry()


def verify_carry():
    rel = inv_relation()
    records = hap.ids()['records']
    carried = {records[INV_KEY + ref]: ref for ref in CARRY}
    bad = 0
    for r in C.records(inv_ws(), APP):
        d = read_invoice_terms(r['rowid'], rel['controlId'])
        if r['rowid'] in carried:
            term, due = CARRY[carried[r['rowid']]]
            ok = (d['term'], d['due']) == (term, due) and (d['text'] in (None, term))
        else:
            ok = d['term'] is None or d['ref'].startswith('TEST')
        bad += not ok
        if r['rowid'] in carried or d['term'] or not ok:
            print(f"  {'OK  ' if ok else 'DIFF'}  {d['ref'] or '(no reference)':<24} {d['number']:<16} relation "
                  f"{d['term']!r:<28} text {d['text']!r:<10} due {d['due']}")
    others = sum(1 for r in C.records(inv_ws(), APP) if r['rowid'] not in carried)
    print(f"  carry: {len(CARRY)} documents carry their term; the other {others} documents checked — "
          f"{bad} differing (a TEST document may carry a term the self-check gave it)")
    return bad


# ── 14 · retire the stand-in ────────────────────────────────────────────────

def rule_controls(rule):
    return [c['controlId'] for i in rule.get('ruleItems') or [] for c in i.get('controls') or []]


def step_retire():
    """§1 steps 4 and 5. Refuses unless the three documents read back from the relation. Then:

    1. the read-only rule *A posted or cancelled document is closed for editing* is given the relation **beside** the
       stand-in, so that no moment passes with the relation unlocked;
    2. the stand-in `6aa920d74a73a3142152e68d` is deleted — a full save of Invoices that leaves it out, the owner's
       approved deletion — and the rule read back, to see what a deletion does to a rule naming the control;
    3. `invoices.py layout` gives the relation the alias `invoice_payment_term_id` and its placeholder (it owns them);
    4. `invoices.py rules` writes the read-only rule by name — the relation alone — and the two new rules."""
    import invoices
    guard()
    rel = inv_relation()
    if not rel:
        sys.exit('run `invoices` first')
    if verify_carry():
        sys.exit('the three documents do not all read back from the relation — refusing to delete the stand-in')
    rules = rules_of(inv_ws())
    closed = rules[invoices.RULE_CLOSED]
    text = standin()
    before = snap(ALL_WORKSHEETS)
    if text:
        if rel['controlId'] not in rule_controls(closed):
            print('  backup:', hap.backup('payterms_invoices_rules_pre_retire', list(rules.values())))
            items = json.loads(json.dumps(closed['ruleItems']))
            items[0]['controls'].append({'isCustom': False, 'controlId': rel['controlId'], 'childControlIds': [],
                                         'permission': [], 'type': '', 'value': ''})
            hap.run('worksheet', 'save-rule', inv_ws(), '--rule-id', closed['ruleId'], '--name', closed['name'],
                    '--type', str(closed['type']), '--filters', json.dumps(closed['filters'], ensure_ascii=False),
                    '--rule-items', json.dumps(items, ensure_ascii=False))
            closed = rules_of(inv_ws())[invoices.RULE_CLOSED]
            print(f"  {invoices.RULE_CLOSED!r} now names both: stand-in {TEXT_STANDIN in rule_controls(closed)}, "
                  f"relation {rel['controlId'] in rule_controls(closed)}")
        ctrls = hap.controls(inv_ws())
        print('  backup:', hap.backup('payterms_invoices_controls_pre_retire', ctrls))
        print(f"  deleting {text['controlName']!r} {TEXT_STANDIN} (type {text['type']}, alias {text.get('alias')!r}, "
              f"row {text['row']}) — the owner-approved deletion")
        C.save_controls(inv_ws(), [c for c in ctrls if c['controlId'] != TEXT_STANDIN])
        before = expect(before, 'the stand-in deleted', gone={'Invoices': {TEXT_STANDIN}})
        if standin():
            sys.exit('the stand-in is still there after the save')
        closed = rules_of(inv_ws())[invoices.RULE_CLOSED]
        print(f"  after the deletion the rule names the dead id: {TEXT_STANDIN in rule_controls(closed)}; "
              f"its controls {rule_controls(closed)}")
        hap.backup('payterms_invoices_rule_after_delete', closed)
    else:
        print('  the stand-in is already gone')
    print('  ── invoices.py layout')
    invoices.step_layout()
    before = expect(before, 'invoices.py layout', changed={'Invoices': {INV_FIELD: {'alias', 'hint', 'desc'}}})
    print('  ── invoices.py rules')
    invoices.step_rules()
    expect(before, 'invoices.py rules (no control may change)')
    rel = inv_relation()
    C.remember('controls', INV_KEY + INV_FIELD, rel['controlId'])
    for name, r in rules_of(inv_ws()).items():
        C.remember('rules', INV_KEY + name, r['ruleId'])
    names = {c['controlId']: c['controlName'] for c in hap.controls(inv_ws())}
    closed = rules_of(inv_ws())[invoices.RULE_CLOSED]
    print(f"  {invoices.RULE_CLOSED!r}: {[names.get(x, 'DEAD ' + x) for x in rule_controls(closed)]}")
    print(f"  relation {rel['controlId']} alias {rel.get('alias')!r} hint {rel.get('hint')!r} desc {rel.get('desc')!r}")
    return verify_carry() + deadrefs()


CATALOGUE_KEYS = ('flowNodeList', 'flowNodeAppDtos', 'formulaMap', 'controls', 'addControls', 'filedControls',
                  'relationControls', 'appList')


def deadrefs(dead=TEXT_STANDIN):
    """Every view, rule, button and workflow node of the app scanned for a control id — the deleted stand-in's."""
    hits = []
    for name in ALL_WORKSHEETS + (TERMS_WS, LINES_WS):
        w = wid(name)
        for v in hap.listing('worksheet', 'view', 'list', w, '-a', APP):
            if dead in json.dumps(C.view_info(w, APP, v['viewId'])):
                hits.append(f"{name} view {v['name']!r}")
        for r in hap.listing('worksheet', 'rules', w):
            if dead in json.dumps(r):
                hits.append(f"{name} rule {r['name']!r}")
        for b in hap.listing('worksheet', 'custom-actions', w):
            if dead in json.dumps(b):
                hits.append(f"{name} button {b['name']!r}")
        for c in hap.controls(w):
            if c['controlId'] != dead and dead in json.dumps({k: v for k, v in c.items() if k != 'relationControls'}):
                hits.append(f"{name} control {c['controlName']!r}")
    flows = hap.listing('workflow', 'list', APP)
    pids = {w.get('id') or w.get('processId'): w.get('name') for w in flows}
    pids.update({v: k for k, v in hap.ids()['workflows'].items()})
    nodes = 0
    for pid, name in pids.items():
        for node_id, d in workflow_nodes(pid)['nodes'].items():
            nodes += 1
            # the catalogue keys list every control of the worksheet, a live one or not: what a node *uses* is elsewhere
            if dead in json.dumps({k: v for k, v in (d or {}).items() if k not in CATALOGUE_KEYS}):
                hits.append(f'workflow {name!r} node {node_id}')
    print(f"  deadrefs {dead}: {len(ALL_WORKSHEETS) + 2} worksheets' views, rules, buttons and controls, and "
          f"{len(pids)} workflows ({nodes} nodes) scanned — {hits or 'no reference'}")
    return len(hits)


# ── self-check: C, D, Confirm and the contacts' sync, through the CLI ───────

TEST_TERMS = {  # the TEST terms the walks need: name -> [(Due, Value, After, Delay Type, Days on the next month)]
    'TEST PT 15 Days after End of Month': [(100, 'percent', 15, 'days_after_end_of_month', 10)],
    'TEST PT 30 Days, on the 31st': [(100, 'percent', 30, 'days_end_of_month_on_the', 31)],
    'TEST PT empty After': [(50, 'percent', None, 'days_after_end_of_next_month', 10),
                            (50, 'percent', 5, 'days_after', 10)],
    'TEST PT fixed line': [(100, 'percent', 30, 'days_after', 10), (50, 'fixed', 0, 'days_after', 10)],
}


def ensure_test_term(name, lines):
    """A TEST term with its lines, created once (Sequence 90, active); never rewritten."""
    tf, lf = all_controls(terms_ws()), all_controls(lines_ws())
    live = {t['name']: t for t in read_terms().values()}
    if name in live:
        return live[name]['rowid']
    rowid = C.row_id(hap.run('worksheet', 'record', 'create', terms_ws(), '-a', APP, '--fields-json', json.dumps([
        {'id': tf[NAME]['controlId'], 'value': name}, {'id': tf[SEQUENCE]['controlId'], 'value': 90},
        {'id': tf[ACTIVE]['controlId'], 'value': 1}, {'id': tf[SHOW_INST]['controlId'], 'value': 1},
        {'id': tf[EARLY]['controlId'], 'value': 0}, {'id': tf[DISC_PCT]['controlId'], 'value': 2},
        {'id': tf[DISC_DAYS]['controlId'], 'value': 10},
        {'id': tf[REDUCED]['controlId'], 'value': [KEY_OF['Reduced tax']['included']]}], ensure_ascii=False)))
    for due, value, after, delay, next_month in lines:
        values = [{'id': lf[TERM]['controlId'], 'value': [rowid]}, {'id': lf[DUE]['controlId'], 'value': due},
                  {'id': lf[VALUE_F]['controlId'], 'value': [KEY_OF['Value'][value]]},
                  {'id': lf[DELAY_F]['controlId'], 'value': [KEY_OF['Delay Type'][delay]]},
                  {'id': lf[NEXT_MONTH]['controlId'], 'value': next_month}]
        if after is not None:
            values.append({'id': lf[AFTER]['controlId'], 'value': after})
        hap.run('worksheet', 'record', 'create', lines_ws(), '-a', APP, '--fields-json', json.dumps(values))
        time.sleep(1.2)
    print(f'  created {name}: {rowid}')
    return rowid


def all_runs(pid, page_size=100):
    """Every run of a workflow, newest first, paging by row count (`count` is per page — BUILDING.md); reads retried."""
    rows, page = [], 1
    while True:
        out = read('approval', 'history', '--process-id', pid, '-n', str(page_size), '-p', str(page))
        got = (out or {}).get('data') or []
        rows += got
        if len(got) < page_size:
            return rows
        page += 1


def run_snapshot(pid):
    rows = all_runs(pid)
    return {r['id'] for r in rows}, max((r.get('createDate') or '' for r in rows), default='')


def wait_new_runs(pid, snapshot, n, seconds=120, settle=3):
    """The runs started since `snapshot`, told apart by instance id, once there are `n` and none is running
    (accounts.wait_new_runs, with its reads retried on a timeout)."""
    ids, latest = snapshot
    deadline = time.time() + seconds
    while True:
        new = [r for r in all_runs(pid) if r['id'] not in ids and (r.get('createDate') or '') >= latest]
        done = n > 0 and len(new) >= n and all(r.get('status') != 1 for r in new)
        if done or time.time() > deadline:
            if done and settle:
                time.sleep(settle)
                new = [r for r in all_runs(pid) if r['id'] not in ids and (r.get('createDate') or '') >= latest]
            return new
        time.sleep(2)


class Check:
    def __init__(self):
        self.bad, self.limits = 0, 0

    def report(self, ok, label, detail='', limit=False):
        word = 'LIMIT ' if limit else ('OK    ' if ok else 'DIFF  ')
        self.bad += (not ok) and not limit
        self.limits += limit
        print(f'  {word}{label}: {detail}')


def run_names(instance_id):
    import accounts
    return [name for _, name in accounts.run_nodes(instance_id)]


def runs_desc(runs):
    out = []
    for r in runs:
        passed = run_names(r['id'])
        took = next((p for p in passed if p in (C_STEP_ENTRY, C_STEP_CUSTOMER, C_STEP_VENDOR)), None)
        cause = (r.get('instanceLog') or {}).get('causeMsg') or ''
        out.append(f"{r.get('status')}{' ' + took if took else ''}{' · dated' if WRITE_DUE in passed else ''}"
                   f"{' · ' + cause if cause else ''}")
    return out


def invoice_values(f, ref, type_label, journal, partner=None, term=None, invoice_date='', date='2026-09-17', due=None):
    import invoices as I
    journals = I.titles(I.JOURNALS, 'Journal Name')
    cid = lambda n: f[n]['controlId']
    values = [{'id': cid('Number'), 'value': 'Draft'}, {'id': cid('Type'), 'value': [I.OPTION_KEY['Type'][type_label]]},
              {'id': cid('Status'), 'value': [I.OPTION_KEY['Status']['Draft']]},
              {'id': cid('Accounting Date'), 'value': date}, {'id': cid('Invoice Date'), 'value': invoice_date},
              {'id': cid('Journal'), 'value': [next(r for r, t in journals.items() if t == journal)]},
              {'id': cid('Auto-post'), 'value': [I.OPTION_KEY['Auto-post']['No']]},
              {'id': cid('Customer Reference'), 'value': ref}]
    if type_label != 'Journal Entry':
        values.append({'id': cid('Tax mode'), 'value': [I.OPTION_KEY['Tax mode']['Tax Excluded']]})
    if partner:
        values.append({'id': cid('Customer / Vendor'), 'value': [partner]})
    if term:
        values.append({'id': cid(INV_FIELD), 'value': [term]})
    if due:
        values.append({'id': cid('Due Date'), 'value': due})
    return values


def documents_by_ref():
    rel = inv_relation()['controlId']
    return {d['ref']: d for d in (read_invoice_terms(r['rowid'], rel) for r in C.records(inv_ws(), APP))}


def contacts_by_name():
    return {c['name']: c for c in (read_contact_terms(r['rowid']) for r in C.records(con_ws(), APP))}


def step_selfcheck(*parts):
    """`parts` limits the walk to some of d · c · confirm · once · contacts (all by default). Prove through the CLI, on
    TEST records left in place: D on every Delay Type, the fallbacks and the clamp; C on a customer, a vendor, a contact
    with no terms, a change of Customer, a journal entry and a document with no Customer / Vendor; Confirm dating the
    invoice it fills an Invoice Date on; `once` — every action dating an invoice exactly once (`once_check`); the
    contacts' copy and push, an empty term included. `DIFF` is the build not doing what §1 says; `LIMIT` is platform
    behaviour recorded."""
    import accounts
    import invoices as I
    guard()
    want = lambda part: not parts or part in parts
    check = Check()
    today = datetime.date.today()
    f, cf = inv_fields(), all_controls(con_ws())
    rel = f[INV_FIELD]['controlId']
    records = hap.ids()['records']
    pid_c, pid_d, pid_confirm = (hap.ids()['workflows'][n] for n in (AUTO_C, AUTO_D, INV_KEY + 'Confirm'))
    terms = {t['name']: t['rowid'] for t in read_terms().values()}
    for name, lines in TEST_TERMS.items():
        terms[name] = ensure_test_term(name, lines)
        C.remember('records', KEY + name, terms[name])
    time.sleep(5)
    fixed = read_term(terms['TEST PT fixed line'])
    check.report((fixed['percent_total'], fixed['line_count']) == (100.0, 2.0),
                 "Percent total counts Percent lines only (TEST PT fixed line: 100 Percent + 50 Fixed)",
                 f"Percent total {fixed['percent_total']}, Line count {fixed['line_count']}")
    before = snap(ALL_WORKSHEETS)

    def wait(pids, snaps, n=1, seconds=90):
        return {k: wait_new_runs(p, snaps[k], n if k == 'expect' else 0, seconds=seconds)
                for k, p in pids.items()}

    def write_and_wait(rowid, values, expect_pid, others, seconds=90):
        """Write, wait for one run of `expect_pid` (when given), then collect any run of the others — told apart by
        instance id (accounts.wait_new_runs). With no run expected it waits 20 s, a run registering about 5 s after."""
        pids = dict(others, **({'expect': expect_pid} if expect_pid else {}))
        snaps = {k: run_snapshot(p) for k, p in pids.items()}
        hap.run('worksheet', 'record', 'update', inv_ws(), rowid, '-a', APP, '--fields-json',
                json.dumps(values, ensure_ascii=False))
        got = {}
        if expect_pid:
            got['expect'] = wait_new_runs(expect_pid, snaps['expect'], 1, seconds=seconds)
        else:
            time.sleep(20)
        for k in others:
            got[k] = wait_new_runs(others[k], snaps[k], 0, seconds=3)
        return got

    # ── D ────────────────────────────────────────────────────────────────
    docs = documents_by_ref() if want('d') else {}
    probe = docs.get('TEST PT D probe') if want('d') else {'rowid': records.get(INV_KEY + 'TEST PT D probe')}
    if not probe:
        rowid = C.row_id(hap.run('worksheet', 'record', 'create', inv_ws(), '-a', APP, '--fields-json', json.dumps(
            invoice_values(f, 'TEST PT D probe', 'Customer Invoice', 'Sales', invoice_date='2026-09-17'))))
        time.sleep(8)
    else:
        rowid = probe['rowid']
    C.remember('records', INV_KEY + 'TEST PT D probe', rowid)
    walk = [  # (label, Payment Terms, Invoice Date, Accounting Date, expected Due Date)
        ('30 Days from the Invoice Date 2026-09-17', '30 Days', '2026-09-17', '2026-09-17', '2026-10-17'),
        ('30 Days, no Invoice Date: the Accounting Date 2026-09-09', '30 Days', '', '2026-09-09', '2026-10-09'),
        ('End of Following Month', 'End of Following Month', '2026-09-17', '2026-09-17', '2026-10-31'),
        ('10 Days after End of Next Month', '10 Days after End of Next Month', '2026-09-17', '2026-09-17', '2026-11-10'),
        ('30% Now, Balance 60 Days (the latest of two lines)', '30% Now, Balance 60 Days', '2026-09-17', '2026-09-17',
         '2026-11-16'),
        ('90 days, on the 10th', '90 days, on the 10th', '2026-09-17', '2026-09-17', '2027-01-10'),
        ('a Days after end of month line (TEST PT 15 Days after End of Month)', 'TEST PT 15 Days after End of Month',
         '2026-09-17', '2026-09-17', '2026-10-15'),
        ('the clamp: day 31 landing in November (TEST PT 30 Days, on the 31st)', 'TEST PT 30 Days, on the 31st',
         '2026-09-17', '2026-09-17', '2026-11-30'),
        ('a line with an empty After, before a line with one (TEST PT empty After)', 'TEST PT empty After',
         '2026-09-17', '2026-09-17', '2026-10-31'),
        ('the day-31 line from a date in October: 2026-10-15 + 30 → 2026-11-14, on to December 31st',
         'TEST PT 30 Days, on the 31st', '2026-10-15', '2026-10-15', '2026-12-31'),
        ('both dates empty: today', '30 Days', '', '', (today + datetime.timedelta(days=30)).isoformat()),
    ]
    for label, term, invoice_date, date, due_want in (walk if want('d') else []):
        now = read_invoice_terms(rowid, rel)
        if (now['term'], now['invoice_date'], now['date']) == (term, invoice_date, date):
            # the same write again would change nothing and start nothing: move the Accounting Date off and back
            write_and_wait(rowid, [{'id': f['Accounting Date']['controlId'], 'value': '2026-01-01'}], pid_d, {})
        got = write_and_wait(rowid, [{'id': rel, 'value': [terms[term]]},
                                     {'id': f['Invoice Date']['controlId'], 'value': invoice_date},
                                     {'id': f['Accounting Date']['controlId'], 'value': date}], pid_d,
                             {'C': pid_c})
        back = read_invoice_terms(rowid, rel)
        check.report(back['due'] == due_want and len(got['expect']) == 1 and not got['C'],
                     f'D · {label}', f"Due Date {back['due']} (want {due_want}); D {runs_desc(got['expect'])}, C {len(got['C'])}")
    if not want('d'):
        before_due = None
    else:
        before_due = read_invoice_terms(rowid, rel)['due']
    if want('d'):
        got = write_and_wait(rowid, [{'id': rel, 'value': []},
                                     {'id': f['Invoice Date']['controlId'], 'value': '2026-09-20'}],
                             None, {'D': pid_d, 'C': pid_c})
        back = read_invoice_terms(rowid, rel)
        check.report(back['due'] == before_due and not got['D'] and back['term'] is None,
                     'D · Payment Terms emptied (with a new Invoice Date): the trigger condition starts no run, the Due '
                     'Date is left as it is', f"Due Date {back['due']} (was {before_due}); D runs {len(got['D'])}")

    # ── C ────────────────────────────────────────────────────────────────
    pid_d_new = hap.ids()['workflows'][AUTO_D_NEW]
    contacts = contacts_by_name()
    vendor = ensure_contact(cf, 'TEST PT Vendor Co', customer=terms['45 Days'], vendor=terms['15 Days'])
    no_terms = ensure_contact(cf, 'TEST PT No Terms Co')
    sunway = contacts['Sunway Construction Group']['rowid']
    cases = [  # (ref, Type, journal, partner, term on create, Invoice Date, Due Date on create, want term, want due)
        ('TEST PT C customer', 'Customer Invoice', 'Sales', sunway, None, '2026-09-17', None, '30 Days', '2026-10-17'),
        ('TEST PT C vendor bill', 'Vendor Bill', 'Purchases', vendor, None, '2026-09-17', None, '15 Days', '2026-10-02'),
        ('TEST PT C contact without terms', 'Customer Invoice', 'Sales', no_terms, terms['21 Days'], '2026-09-17', None,
         '21 Days', '2026-10-08'),
        # created before `Invoices: Due Date of a new invoice with no Customer / Vendor` existed: C started no run and the
        # invoice stayed undated — the evidence for that workflow, left as it is
        ('TEST PT C no customer', 'Customer Invoice', 'Sales', None, terms['45 Days'], '2026-09-17', None, '45 Days',
         ''),
        ('TEST PT new invoice without a customer', 'Customer Invoice', 'Sales', None, terms['45 Days'], '2026-09-17',
         None, '45 Days', '2026-11-01'),
        ('TEST PT C journal entry', 'Journal Entry', 'Miscellaneous Operations', sunway, terms['30 Days'], '',
         '2026-12-31', None, '2026-12-31'),
    ]
    docs = documents_by_ref()
    for ref, type_label, journal, partner, term, invoice_date, due, want_term, want_due in (cases if want('c') else []):
        d = docs.get(ref)
        if d:
            if ref == 'TEST PT C contact without terms' and d['partner'] == 'Sunway Construction Group':
                want_term, want_due = '30 Days', '2026-10-17'        # as the Customer change below leaves it
            check.report((d['term'], d['due']) == (want_term, want_due), f'C · {ref} (created in an earlier run)',
                         f"Payment Terms {d['term']}, Due Date {d['due']}")
            C.remember('records', INV_KEY + ref, d['rowid'])
            continue
        snaps = {k: run_snapshot(p) for k, p in (('C', pid_c), ('D', pid_d), ('D new', pid_d_new))}
        new_row = C.row_id(hap.run('worksheet', 'record', 'create', inv_ws(), '-a', APP, '--fields-json', json.dumps(
            invoice_values(f, ref, type_label, journal, partner=partner, term=term, invoice_date=invoice_date,
                           due=due))))
        C.remember('records', INV_KEY + ref, new_row)
        # C runs on a create that writes Customer / Vendor; D on a create writes nothing of its own — it runs when C's
        # write of the terms starts it; the create-time D runs on a create with terms and no Customer / Vendor
        by_c = partner is not None
        runs_c = wait_new_runs(pid_c, snaps['C'], 1 if by_c else 0, seconds=90 if by_c else 25)
        runs_new = wait_new_runs(pid_d_new, snaps['D new'], 0 if by_c else 1, seconds=5 if by_c else 90)
        runs_d = wait_new_runs(pid_d, snaps['D'], 0, seconds=15)
        back = read_invoice_terms(new_row, rel)
        ok = (back['term'], back['due']) == (want_term, want_due) and len(runs_c) == int(by_c) and \
            len(runs_new) == int(not by_c and term is not None)
        check.report(ok, f'C · {ref}', f"Payment Terms {back['term']} (want {want_term}), Due Date {back['due']} (want "
                     f"{want_due}); C {runs_desc(runs_c)}, D (create) {runs_desc(runs_new)}, D {runs_desc(runs_d)}")
        # until 17 Sep 2026 C's write of the Payment Terms started D as well (a LIMIT line then); C now starts no other
        # workflow (NO_OTHER_WORKFLOWS), so a run of D here is a second dating
        check.report(not runs_d, f"C · {ref}: C's write of the Payment Terms starts no run of automation D",
                     f'D {runs_desc(runs_d)}')
    change = documents_by_ref()['TEST PT C contact without terms']
    if not want('c'):
        pass
    elif change['partner'] != 'Sunway Construction Group':
        got = write_and_wait(change['rowid'], [{'id': f['Customer / Vendor']['controlId'], 'value': [sunway]}], pid_c,
                             {'D': pid_d})
        back = read_invoice_terms(change['rowid'], rel)
        check.report((back['term'], back['due']) == ('30 Days', '2026-10-17') and not got['D'],
                     'C · the Customer changed to Sunway Construction Group on TEST PT C contact without terms',
                     f"Payment Terms {back['term']}, Due Date {back['due']}; C {runs_desc(got['expect'])}, D {runs_desc(got['D'])}")
    else:
        check.report((change['term'], change['due']) == ('30 Days', '2026-10-17'),
                     'C · the Customer changed to Sunway Construction Group (in an earlier run)',
                     f"Payment Terms {change['term']}, Due Date {change['due']}")

    # ── Confirm ──────────────────────────────────────────────────────────
    ref = 'TEST PT Confirm'
    d = documents_by_ref().get(ref)
    if not want('confirm'):
        pass
    elif not d:
        snaps = {k: run_snapshot(p) for k, p in (('C', pid_c), ('D', pid_d))}
        new_row = C.row_id(hap.run('worksheet', 'record', 'create', inv_ws(), '-a', APP, '--fields-json', json.dumps(
            invoice_values(f, ref, 'Customer Invoice', 'Sales', partner=sunway, date='2026-09-01'))))
        C.remember('records', INV_KEY + ref, new_row)
        wait_new_runs(pid_c, snaps['C'], 1, seconds=90)
        d = read_invoice_terms(new_row, rel)
        check.report((d['term'], d['invoice_date'], d['due']) == ('30 Days', '', '2026-10-01'),
                     'Confirm · the TEST draft as C left it: no Invoice Date, dated from the Accounting Date 2026-09-01',
                     f"Payment Terms {d['term']}, Invoice Date {d['invoice_date'] or '—'}, Due Date {d['due']}")
        snaps = {k: run_snapshot(p) for k, p in (('confirm', pid_confirm), ('D', pid_d), ('C', pid_c))}
        hap.run('workflow', 'trigger', pid_confirm, '-s', d['rowid'])
        runs = wait_new_runs(pid_confirm, snaps['confirm'], 1, seconds=120)
        runs_d = wait_new_runs(pid_d, snaps['D'], 0, seconds=15)
        back = read_invoice_terms(d['rowid'], rel)
        want_due = (today + datetime.timedelta(days=30)).isoformat()
        check.report((back['status'], back['invoice_date'], back['due']) == ('Posted', today.isoformat(), want_due),
                     'Confirm · posts it, fills the Invoice Date with today and dates it from that',
                     f"{back['number']} {back['status']}, Invoice Date {back['invoice_date']}, Due Date {back['due']} "
                     f"(want {want_due}); Confirm {runs_desc(runs)}")
        # until 17 Sep 2026 this write started D as well (a LIMIT line then); Confirm now starts no other workflow
        check.report(not runs_d, "Confirm · its write of the Invoice Date starts no run of automation D",
                     f'D runs {runs_desc(runs_d)}')
    else:
        check.report(d['status'] == 'Posted' and d['due'] and d['invoice_date'] and
                     d['due'] == (datetime.date.fromisoformat(d['invoice_date']) + datetime.timedelta(days=30)).isoformat(),
                     'Confirm · TEST PT Confirm (confirmed in an earlier run)',
                     f"{d['number']} {d['status']}, Invoice Date {d['invoice_date']}, Due Date {d['due']}")

    # ── once: every action dates an invoice exactly once ─────────────────
    if want('once'):
        once_check(check, f, today)

    # ── Contacts ─────────────────────────────────────────────────────────
    if want('contacts'):
        contacts_check(check, cf, terms)

    # the vendor bill on Purchases is cancelled, so Purchases holds no new draft for its archive guard
    bill = documents_by_ref().get('TEST PT C vendor bill')
    if bill and bill['status'] == 'Draft':
        snap_cancel = run_snapshot(hap.ids()['workflows'][INV_KEY + 'Cancel'])
        hap.run('workflow', 'trigger', hap.ids()['workflows'][INV_KEY + 'Cancel'], '-s', bill['rowid'])
        wait_new_runs(hap.ids()['workflows'][INV_KEY + 'Cancel'], snap_cancel, 1, seconds=60)
    bill = documents_by_ref().get('TEST PT C vendor bill')
    check.report(bill and bill['status'] == 'Cancelled', "'TEST PT C vendor bill' cancelled through the Cancel workflow",
                 bill and bill['status'])
    expect(before, 'selfcheck (no control may change)')
    print(f"  selfcheck: {'OK' if not check.bad else f'{check.bad} DIFF'}; platform limits recorded: {check.limits}")
    return check.bad


def once_check(check, f, today):
    """Each action dates the invoice exactly once, with the dates C, D and Confirm always gave — on `TEST PT once …`
    invoices created here when missing (a re-run reads them back). A dating run is a run that passed *Write the Due
    Date*; the four Invoices workflows that date an invoice are watched after every action, and any run not expected
    fails the line."""
    rel = f[INV_FIELD]['controlId']
    pids = {'C': hap.ids()['workflows'][AUTO_C], 'D': hap.ids()['workflows'][AUTO_D],
            'D (create)': hap.ids()['workflows'][AUTO_D_NEW], 'Confirm': hap.ids()['workflows'][INV_KEY + 'Confirm']}
    contacts = contacts_by_name()
    sunway, vendor_co, no_terms = (contacts[n]['rowid'] for n in ('Sunway Construction Group', 'TEST PT Vendor Co',
                                                                    'TEST PT No Terms Co'))
    terms = {t['name']: t['rowid'] for t in read_terms().values()}

    def act(label, do, expect, want):
        """Run `do` (it returns the invoice's rowid), wait for the expected runs ({workflow: n}), then look for any other
        run no sooner than 30 s after the write and 10 s after the expected runs ended — a run registers about 5 s
        after the write that starts it (C's term write started D 5 s after C, 17 Sep) — and compare the invoice with
        `want`."""
        snaps = {k: run_snapshot(p) for k, p in pids.items()}
        written = time.time()
        rowid = do()
        for k, n in expect.items():
            wait_new_runs(pids[k], snaps[k], n, seconds=120)
        time.sleep(max(10, 30 - (time.time() - written)))
        runs = {k: wait_new_runs(p, snaps[k], 0, seconds=1) for k, p in pids.items()}      # every run since the write
        dated = [k for k, rs in runs.items() for r in rs if WRITE_DUE in run_names(r['id'])]
        back = read_invoice_terms(rowid, rel)
        got = {k: back[k] for k in want}
        ok = got == want and len(dated) == 1 and all(len(runs[k]) == n for k, n in expect.items()) and \
            not any(runs[k] for k in pids if k not in expect) and all(r.get('status') == 2 for rs in runs.values() for r in rs)
        check.report(ok, f'once · {label}', f"{json.dumps(got, ensure_ascii=False)}; runs "
                     + (', '.join(f'{k} {runs_desc(rs)} {[r["id"] for r in rs]}' for k, rs in runs.items() if rs) or 'none')
                     + f'; dating runs {len(dated)} {dated}')
        return rowid

    def create(ref, partner, term=None, invoice_date='2026-09-17', date='2026-09-17'):
        def do():
            rowid = C.row_id(hap.run('worksheet', 'record', 'create', inv_ws(), '-a', APP, '--fields-json', json.dumps(
                invoice_values(f, ref, 'Customer Invoice', 'Sales', partner=partner, term=term, invoice_date=invoice_date,
                               date=date))))
            C.remember('records', INV_KEY + ref, rowid)
            return rowid
        return do

    def update(rowid, values):
        return lambda: (hap.run('worksheet', 'record', 'update', inv_ws(), rowid, '-a', APP, '--fields-json',
                                json.dumps(values, ensure_ascii=False)), rowid)[1]

    def earlier(ref, want):
        d = documents_by_ref()[ref]
        C.remember('records', INV_KEY + ref, d['rowid'])
        check.report({k: d[k] for k in want} == want, f'once · {ref} (in an earlier run)',
                     json.dumps({k: d[k] for k in want}, ensure_ascii=False))
        return d['rowid']

    docs = documents_by_ref()
    # 1 · a customer with Customer Payment Terms: C takes the term and dates the invoice; its term write starts no D
    ref = 'TEST PT once customer'
    row = earlier(ref, {'term': '30 Days'}) if ref in docs else \
        act(f'{ref}: created on Sunway Construction Group (30 Days), Invoice Date 2026-09-17', create(ref, sunway),
            {'C': 1}, {'term': '30 Days', 'due': '2026-10-17'})
    # 2 · then its Invoice Date changes: D dates it
    if documents_by_ref()[ref]['invoice_date'] != '2026-09-20':
        act(f'{ref}: Invoice Date changed to 2026-09-20', update(row, [{'id': f['Invoice Date']['controlId'],
                                                                         'value': '2026-09-20'}]),
            {'D': 1}, {'invoice_date': '2026-09-20', 'due': '2026-10-20'})
    else:
        earlier(ref, {'invoice_date': '2026-09-20', 'due': '2026-10-20'})
    # 3 · a customer without terms and a typed term: C leaves the term and dates the invoice
    ref = 'TEST PT once typed term'
    row = earlier(ref, {'term': docs[ref]['term']}) if ref in docs else \
        act(f'{ref}: created on TEST PT No Terms Co with 21 Days typed', create(ref, no_terms, terms['21 Days']),
            {'C': 1}, {'term': '21 Days', 'due': '2026-10-08'})
    # 4 · then its customer changes to one with other terms: C writes them and dates it; no D
    if documents_by_ref()[ref]['partner'] != 'TEST PT Vendor Co':
        act(f'{ref}: Customer changed to TEST PT Vendor Co (45 Days)',
            update(row, [{'id': f['Customer / Vendor']['controlId'], 'value': [vendor_co]}]),
            {'C': 1}, {'partner': 'TEST PT Vendor Co', 'term': '45 Days', 'due': '2026-11-01'})
    else:
        earlier(ref, {'partner': 'TEST PT Vendor Co', 'term': '45 Days', 'due': '2026-11-01'})
    # 5 · the customer's own term typed as well: C's write changes nothing — the case a dating left to D would miss
    ref = 'TEST PT once same term'
    if ref in docs:
        earlier(ref, {'term': '30 Days', 'due': '2026-10-18'})
    else:
        act(f'{ref}: created on Sunway Construction Group with its 30 Days typed, Invoice Date 2026-09-18',
            create(ref, sunway, terms['30 Days'], invoice_date='2026-09-18', date='2026-09-18'),
            {'C': 1}, {'term': '30 Days', 'due': '2026-10-18'})
    # 6 · Confirm on a draft with a term and no Invoice Date: today, the Due Date from it, one dating
    ref = 'TEST PT once Confirm'
    if ref in docs and docs[ref]['status'] == 'Posted':
        d = docs[ref]
        earlier(ref, {'status': 'Posted', 'invoice_date': d['invoice_date'], 'due': (
            datetime.date.fromisoformat(d['invoice_date']) + datetime.timedelta(days=30)).isoformat() if d['invoice_date'] else 'a date'})
        return
    row = docs[ref]['rowid'] if ref in docs else \
        act(f'{ref}: created on Sunway Construction Group, no Invoice Date, Accounting Date 2026-09-01',
            create(ref, sunway, invoice_date='', date='2026-09-01'), {'C': 1},
            {'term': '30 Days', 'invoice_date': '', 'due': '2026-10-01'})
    act(f'{ref}: Confirm', lambda: (hap.run('workflow', 'trigger', pids['Confirm'], '-s', row), row)[1], {'Confirm': 1},
        {'status': 'Posted', 'invoice_date': today.isoformat(),
         'due': (today + datetime.timedelta(days=30)).isoformat()})


def ensure_contact(cf, name, company=None, customer=None, vendor=None, vat=None):
    """A TEST contact, created once with what it is given; returns its rowid."""
    live = contacts_by_name()
    if name in live:
        C.remember('records', CON_KEY + name, live[name]['rowid'])
        return live[name]['rowid']
    contact_key = next(o['key'] for o in cf['Address Type']['options'] if o['value'] == 'Contact')
    values = [{'id': cf['Name']['controlId'], 'value': name}, {'id': cf['Address Type']['controlId'], 'value': [contact_key]},
              {'id': cf['Active']['controlId'], 'value': 1}]
    if company:
        values.append({'id': cf['Company']['controlId'], 'value': [company]})
    if customer:
        values.append({'id': cf[CUSTOMER_TERMS]['controlId'], 'value': [customer]})
    if vendor:
        values.append({'id': cf[VENDOR_TERMS]['controlId'], 'value': [vendor]})
    if vat:
        values.append({'id': cf['Tax ID']['controlId'], 'value': vat})
    rowid = C.row_id(hap.run('worksheet', 'record', 'create', con_ws(), '-a', APP, '--fields-json',
                             json.dumps(values, ensure_ascii=False)))
    C.remember('records', CON_KEY + name, rowid)
    print(f'  created {name}: {rowid}')
    return rowid


def contacts_check(check, cf, terms):
    import accounts
    import contacts
    pid_copy = hap.ids()['workflows'][contacts.COPY_DETAILS]
    pid_push = hap.ids()['workflows'][contacts.PUSH_DETAILS]
    company = ensure_contact(cf, 'TEST PT Company', customer=terms['21 Days'], vendor=terms['15 Days'], vat='TEST-PT-VAT')
    live = contacts_by_name()
    if 'TEST PT Person' not in live:
        snap_copy = run_snapshot(pid_copy)
        person = ensure_contact(cf, 'TEST PT Person', company=company)
        runs = wait_new_runs(pid_copy, snap_copy, 1, seconds=90)
        back = read_contact_terms(person)
        check.report((back['customer'], back['vendor'], back['vat']) == ('21 Days', '15 Days', 'TEST-PT-VAT'),
                     "Contacts · a contact given a company with terms takes them (copy company details)",
                     f"Customer {back['customer']}, Vendor {back['vendor']}, Tax ID {back['vat']!r}; runs "
                     f"{[(r['id'], r.get('status')) for r in runs]}")
    person = contacts_by_name()['TEST PT Person']['rowid']

    def company_write(label, values, want):
        snap_push = run_snapshot(pid_push)
        hap.run('worksheet', 'record', 'update', con_ws(), company, '-a', APP, '--fields-json',
                json.dumps(values, ensure_ascii=False))
        runs = wait_new_runs(pid_push, snap_push, 1, seconds=90)
        back = read_contact_terms(person)
        got = (back['customer'], back['vendor'], back['vat'])
        check.report(got == want, f'Contacts · {label}', f"TEST PT Person: Customer {got[0]}, Vendor {got[1]}, Tax ID "
                     f"{got[2]!r} (want {want}); push runs {[(r['id'], r.get('status')) for r in runs]}")
        return got

    now = read_contact_terms(company)
    if now['customer'] != '45 Days':
        company_write("the company's Customer Payment Terms changed to 45 Days reach its contact (push)",
                      [{'id': cf[CUSTOMER_TERMS]['controlId'], 'value': [terms['45 Days']]}],
                      ('45 Days', '15 Days', 'TEST-PT-VAT'))
    # §1: the push writes an empty term to the contacts, as Odoo does — unless the existing push leaves an empty Tax ID
    # behind, in which case the terms do the same. So the Tax ID is emptied first and the terms judged against it.
    vat_cleared = read_contact_terms(person)['vat'] == ''
    if read_contact_terms(company)['vat']:
        got = company_write("the company's Tax ID emptied: what the existing push does with an empty value",
                            [{'id': cf['Tax ID']['controlId'], 'value': ''}], ('45 Days', '15 Days', ''))
        vat_cleared = got[2] == ''
    if read_contact_terms(company)['vendor'] is not None:
        want_vendor = None if vat_cleared else '15 Days'
        company_write("the company's Vendor Payment Terms emptied: the push "
                      + ('writes the empty value to its contact, as it does the Tax ID' if vat_cleared else
                         'leaves the contact\'s term, as it leaves the Tax ID'),
                      [{'id': cf[VENDOR_TERMS]['controlId'], 'value': []}], ('45 Days', want_vendor, ''))
    back = read_contact_terms(person)
    check.report((back['customer'], back['vat']) == ('45 Days', '') and back['vendor'] in (None, '15 Days'),
                 'Contacts · TEST PT Person as the walk leaves it',
                 f"Customer {back['customer']}, Vendor {back['vendor']}, Tax ID {back['vat']!r}")


# ── check: the configuration read back against §1 ───────────────────────────

def code_state(pid, node_id):
    got = node_get(pid, node_id)
    try:
        code = base64.b64decode(got.get('code') or '').decode('utf-8')
    except (ValueError, UnicodeDecodeError):
        code = got.get('code') or ''
    return dict(actionId=str(got.get('actionId')), code=code.strip(),
                inputs=[(x.get('name'), x.get('value')) for x in got.get('inputDatas') or [] if x.get('name')],
                outputs=sorted(c.get('controlId') for c in got.get('controls') or []))


def dating_differences(pid, label):
    """The dating chain of one workflow, node by node, read only."""
    out = []
    proc, byname = nodes_by_name(pid)
    start = proc['startEventId']
    order = dating_order(pid)
    if order != [GET_INVOICE, HAS_TERMS, PATH_TERMS, GET_LINES, COMPUTE_DUE, WRITE_DUE]:
        return [f'{label}: the dating chain reads {order}']
    f, lf = inv_fields(), all_controls(lines_ws())
    rel = f[INV_FIELD]
    fresh = byname[GET_INVOICE]['id']
    want = dict(appId=inv_ws(), actionId='406', executeType=STOP, execute=search_state(pid, fresh)['execute'],
                filters=[('rowid', EQUALS_ID, 0, [(start, 'rowid')])])
    if search_state(pid, fresh) != want:
        out.append(f'{label} / {GET_INVOICE}: {search_state(pid, fresh)}')
    gateway = byname[HAS_TERMS]
    fm = proc['flowNodeMap']
    paths = {fm[i]['name']: fm[i] for i in gateway.get('flowIds') or []}
    if gateway.get('gatewayType') != EXCLUSIVE or sorted(paths) != sorted([PATH_TERMS, PATH_NO_TERMS]):
        out.append(f"{label} / {HAS_TERMS}: gatewayType {gateway.get('gatewayType')} paths {sorted(paths)}")
    else:
        for name, cid in ((PATH_TERMS, NOT_EMPTY_ID), (PATH_NO_TERMS, EMPTY_ID)):
            if path_state(pid, paths[name]['id']) != [[(fresh, rel['controlId'], cid, [])]]:
                out.append(f'{label} / {name}: {path_state(pid, paths[name]["id"])}')
        if paths[PATH_NO_TERMS].get('nextId') not in (None, '', '99'):
            out.append(f'{label} / {PATH_NO_TERMS} runs into a step')
    lines = byname[GET_LINES]['id']
    want = dict(appId=lines_ws(), actionId='400', executeType=None, execute=True,
                filters=[(lf[TERM]['controlId'], RELATION_EQ_ID, 0, [(fresh, rel['controlId'])])])
    if search_state(pid, lines) != want:
        out.append(f'{label} / {GET_LINES}: {search_state(pid, lines)}')
    code = code_state(pid, byname[COMPUTE_DUE]['id'])
    want = dict(actionId=JAVASCRIPT, code=js_code().strip(),
                inputs=[(x['name'], x['value']) for x in code_inputs(byname, f, lf)],
                outputs=sorted(['due_date', 'lines', 'reference', 'seen']))
    if code != want:
        out.append(f"{label} / {COMPUTE_DUE}: {[k for k in want if code[k] != want[k]]}")
    s = step_state(pid, byname[WRITE_DUE]['id'])
    if (s['selectNodeId'], s['appId'], s['isException'], s['fields']) != \
            (fresh, inv_ws(), False, [(f['Due Date']['controlId'], byname[COMPUTE_DUE]['id'], 'due_date', '', False)]):
        out.append(f'{label} / {WRITE_DUE}: {s}')
    info = read('workflow', 'get', pid)
    info = info.get('data', info)
    if not info.get('enabled') or info.get('publishStatus') != 2:
        out.append(f"{label}: enabled={info.get('enabled')} publishStatus={info.get('publishStatus')}")
    return out


def automation_differences():
    import invoices as I
    out = []
    f, cf = inv_fields(), all_controls(con_ws())
    rel = f[INV_FIELD]
    # D
    pid = hap.ids()['workflows'][AUTO_D]
    proc, byname = nodes_by_name(pid)
    start = proc['startEventId']
    t = trigger_state(pid, start)
    want = dict(appId=inv_ws(), triggerId='4', fields=sorted([rel['controlId'], f['Invoice Date']['controlId'],
                                                              f['Accounting Date']['controlId']]),
                condition=[[(rel['controlId'], NOT_EMPTY_ID)]], name=TRIGGER_D)
    if t != want:
        out.append(f'D trigger {t} != {want}')
    if proc['flowNodeMap'][start].get('nextId') != byname.get(GET_INVOICE, {}).get('id'):
        out.append('D: the trigger does not run into the chain')
    info = read('workflow', 'get', pid)
    info = info.get('data', info)
    if (info.get('name'), info.get('explain')) != (AUTO_D, DESC_D):
        out.append(f"D name/description {info.get('name')!r}")
    out += dating_differences(pid, 'D')
    # D on a create
    pid = hap.ids()['workflows'][AUTO_D_NEW]
    proc, byname = nodes_by_name(pid)
    start = proc['startEventId']
    t = trigger_state(pid, start)
    want = dict(appId=inv_ws(), triggerId='1', fields=[],
                condition=[[(rel['controlId'], NOT_EMPTY_ID), (f['Customer / Vendor']['controlId'], EMPTY_ID)]],
                name=TRIGGER_D_NEW)
    if t != want:
        out.append(f'D (create) trigger {t} != {want}')
    if proc['flowNodeMap'][start].get('nextId') != byname.get(GET_INVOICE, {}).get('id'):
        out.append('D (create): the trigger does not run into the chain')
    info = read('workflow', 'get', pid)
    info = info.get('data', info)
    if (info.get('name'), info.get('explain')) != (AUTO_D_NEW, DESC_D_NEW):
        out.append(f"D (create) name/description {info.get('name')!r}")
    out += dating_differences(pid, 'D (create)')
    # C
    pid = hap.ids()['workflows'][AUTO_C]
    proc, byname = nodes_by_name(pid)
    fm, start = proc['flowNodeMap'], proc['startEventId']
    t = trigger_state(pid, start)
    want = dict(appId=inv_ws(), triggerId='2', fields=[f['Customer / Vendor']['controlId']], condition=[], name=TRIGGER_C)
    if t != want:
        out.append(f'C trigger {t} != {want}')
    info = read('workflow', 'get', pid)
    info = info.get('data', info)
    if (info.get('name'), info.get('explain')) != (AUTO_C, DESC_C):
        out.append(f"C name/description {info.get('name')!r}")
    contact = byname[GET_CONTACT]['id']
    if fm[start].get('nextId') != contact or fm[contact].get('nextId') != byname[C_GATEWAY]['id'] or \
            fm[byname[C_GATEWAY]['id']].get('nextId') != byname[GET_INVOICE]['id']:
        out.append('C: the trigger does not run contact → gateway → dating chain')
    want = dict(appId=con_ws(), actionId='406', executeType=CONTINUE, execute=search_state(pid, contact)['execute'],
                filters=[('rowid', EQUALS_ID, IGNORE_WHEN_ABNORMAL, [(start, f['Customer / Vendor']['controlId'])])])
    if search_state(pid, contact) != want:
        out.append(f'C / {GET_CONTACT}: {search_state(pid, contact)}')
    gateway = byname[C_GATEWAY]
    paths = [fm[i] for i in gateway.get('flowIds') or []]
    specs = c_paths(start, contact, f, cf)
    if gateway.get('gatewayType') != EXCLUSIVE or [p['name'] for p in paths] != [s_[0] for s_ in specs]:
        out.append(f"C / gateway: type {gateway.get('gatewayType')} paths {[p['name'] for p in paths]}")
    for node, (name, groups, step, write) in zip(paths, specs):
        if path_state(pid, node['id']) != condition_shape(groups):
            out.append(f'C / path {name!r}: {path_state(pid, node["id"])}')
        nxt = fm.get(node.get('nextId'))
        if (nxt or {}).get('name') != step:
            out.append(f"C / path {name!r} runs into {(nxt or {}).get('name')!r}")
        elif step:
            s = step_state(pid, nxt['id'])
            wanted = (start, inv_ws(), False, [(write['fieldId'], write.get('nodeId') or '', write.get('fieldValueId') or '',
                                                '', bool(write.get('isClear')))])
            if (s['selectNodeId'], s['appId'], s['isException'], s['fields']) != wanted:
                out.append(f'C / {step!r}: {s}')
    out += dating_differences(pid, 'C')
    if quiet_state(pid) != (NO_OTHER_WORKFLOWS, []):
        out.append(f'C: 触发其他工作流 reads {quiet_state(pid)} — its write of the Payment Terms would start D as well')
    # Confirm
    pid = hap.ids()['workflows'][INV_KEY + 'Confirm']
    proc, byname = nodes_by_name(pid)
    if proc['flowNodeMap'][byname[I.REFERENCE_BRANCH]['id']].get('nextId') != byname.get(GET_INVOICE, {}).get('id'):
        out.append('Confirm: the dating chain does not follow the Payment Reference branch')
    out += dating_differences(pid, 'Confirm')
    if quiet_state(pid) != (NO_OTHER_WORKFLOWS, []):
        out.append(f'Confirm: 触发其他工作流 reads {quiet_state(pid)} — its write of the Invoice Date would start D as well')
    return out


def contacts_sync_differences():
    import contacts
    out = []
    cf = all_controls(con_ws())
    fid = lambda n: cf[n]['controlId']
    pid = hap.ids()['workflows'][contacts.COPY_DETAILS]
    proc, byname = nodes_by_name(pid)
    fm, start = proc['flowNodeMap'], proc['startEventId']
    company = byname['Get the company']['id']
    last = byname['The company has a DUNS?']
    for n in (CUSTOMER_TERMS, VENDOR_TERMS):
        _, gateway_name, step = contacts.TERM_BRANCHES[n]
        g = byname.get(gateway_name)
        if not g or last.get('nextId') != g['id']:
            out.append(f'copy: {gateway_name!r} does not follow {last.get("name")!r}')
            continue
        paths = [fm[i] for i in g.get('flowIds') or []]
        yes = next((p for p in paths if p.get('nextId') not in (None, '', '99')), None)
        if not yes or path_state(pid, yes['id']) != [[(company, fid(n), NOT_EMPTY_ID, [])]] or \
                sorted(p['name'] for p in paths) != ['No', 'Yes']:
            out.append(f'copy: {gateway_name!r} paths')
        s = step_state(pid, byname[step]['id'])
        if (s['selectNodeId'], s['isException'], s['fields']) != (start, False, [(fid(n), company, fid(n), '', False)]):
            out.append(f'copy: {step!r} {s}')
        last = g
    info = read('workflow', 'get', pid)
    info = info.get('data', info)
    if info.get('publishStatus') != 2 or not info.get('enabled'):
        out.append('copy: not published')
    pid = hap.ids()['workflows'][contacts.PUSH_DETAILS]
    proc, byname = nodes_by_name(pid)
    start = proc['startEventId']
    t = node_get(pid, start)
    if not {fid(CUSTOMER_TERMS), fid(VENDOR_TERMS)} <= set(t.get('assignFieldIds') or []):
        out.append(f"push: trigger fields {t.get('assignFieldIds')}")
    s = step_state(pid, byname[contacts.PUSH_TERMS_STEP]['id'])
    if (s['selectNodeId'], s['isException'], s['fields']) != (byname['Get its contacts']['id'], False,
                                                              [(fid(n), start, fid(n), '', False)
                                                               for n in (CUSTOMER_TERMS, VENDOR_TERMS)]):
        out.append(f'push: {contacts.PUSH_TERMS_STEP!r} {s}')
    info = read('workflow', 'get', pid)
    info = info.get('data', info)
    if info.get('publishStatus') != 2 or not info.get('enabled'):
        out.append('push: not published')
    return out


def step_check():
    """Everything this bundle built, read back: the sidebar, both worksheets' controls, options, defaults, roll-ups,
    title formula, the mount, rules, buttons and views; the relation on Invoices, its rules and the stand-in's
    absence; Contacts' two terms and their sync; automations C, D and Confirm's chain node by node; the roles."""
    import invoices
    import roles
    problems = []
    section = next(s for s in app_sections() if s['name'] == SECTION)
    names = [i['name'] for i in section['items']]
    if names != ['Chart of Accounts', 'Journals', TERMS_WS, LINES_WS, 'Invoices', 'Invoice Lines']:
        problems.append(f'Invoicing reads {names}')
    status = {k: v.get('status') for k, v in main_site_items().items()}
    if (status.get(terms_ws()), status.get(lines_ws())) != (1, HIDDEN):
        problems.append(f'sidebar status {status.get(terms_ws())} / {status.get(lines_ws())}')
    for i in section['items']:
        if i['name'] in ALIASES and (i.get('alias'), i.get('remark'), i.get('iconUrl', '').rsplit('/', 1)[-1]) != \
                (ALIASES[i['name']], REMARKS[i['name']], ICONS[i['name']] + '.svg'):
            problems.append(f"{i['name']}: alias/remark/icon {i.get('alias')!r} {i.get('iconUrl')!r}")
    for worksheet in (TERMS_WS, LINES_WS):
        ctrls = hap.controls(wid(worksheet))
        want = set(SPEC[worksheet]['place']) | ({DUE_TERMS} if worksheet == TERMS_WS else set())
        if {c['controlName'] for c in ctrls} != want or len(ctrls) != len(want):
            problems.append(f'{worksheet}: controls {sorted(c["controlName"] for c in ctrls)}')
        problems += [f'{worksheet} / {n}: {d}' for n, d in layout_differences(worksheet, ctrls).items()]
        f = hap.by_name(ctrls)
        for n, opts in OPTIONS.items():
            if n in f and [(o['key'], o['value']) for o in f[n]['options'] if not o.get('isDeleted')] != \
                    [(o['key'], o['value']) for o in opts]:
                problems.append(f'{worksheet} / {n}: options')
        for n, adv in SPEC[worksheet]['advanced'].items():
            live = f.get(n, {}).get('advancedSetting') or {}
            for k, v in adv.items():
                if (json.loads(live.get(k) or '[]')[0]['staticValue'] if k == 'defsource' and live.get(k) else live.get(k)) != \
                        (json.loads(v)[0]['staticValue'] if k == 'defsource' else v):
                    problems.append(f'{worksheet} / {n}: {k} {live.get(k)!r}')
    lf = all_controls(lines_ws())
    if json.loads(lf[LINE_TITLE]['dataSource']).get('expression') != line_title_expression(lf) or \
            lf[LINE_TITLE].get('enumDefault2') != 2:
        problems.append('Display name expression')
    if rollup_state() != ROLLUP_WANT:
        problems.append(f'roll-ups {rollup_state()}')
    sub, back = sub_list(), back_relation()
    if not sub or not back or sub.get('sourceControlId') != back['controlId'] or back.get('sourceControlId') != sub['controlId']:
        problems.append('the mount does not pair')
    for worksheet in (TERMS_WS, LINES_WS):
        todo, live = rule_differences(worksheet)
        problems += [f'{worksheet} rule {n!r}: {d}' for n, d in todo.items()]
        if set(live) != set(RULES[worksheet]):
            problems.append(f'{worksheet} rules {sorted(live)}')
        problems += [f'{worksheet} views: {d}' for d in [view_differences(worksheet)] if d]
    problems += button_differences()
    rel = inv_relation()
    if standin():
        problems.append('the stand-in is still on Invoices')
    want = dict(controlName=INV_FIELD, alias='invoice_payment_term_id', row=INV_PLACE[0], col=INV_PLACE[1],
                size=INV_PLACE[2], hint='Payment Terms', desc='', required=False, enumDefault=1, fieldPermission='111')
    diff_ = {k: (rel.get(k), v) for k, v in want.items() if rel.get(k) != v}
    adv = rel.get('advancedSetting') or {}
    if (adv.get('bidirectional'), adv.get('showtype'), picker_state(adv.get('filters'))) != \
            ('0', '3', picker_state(picker_active())):
        diff_['advancedSetting'] = (adv.get('bidirectional'), adv.get('showtype'), adv.get('filters'))
    if rel.get('sourceControlId') in {c['controlId'] for c in hap.controls(terms_ws())}:
        diff_['reverse'] = 'Payment Terms carries a reverse control'
    if diff_:
        problems.append(f'Invoices / {INV_FIELD}: {diff_}')
    problems += [f'Contacts / {n}: {d}' for n, d in con_differences().items()]
    problems += automation_differences()
    problems += contacts_sync_differences()
    print('  ── invoices.py check')
    problems += ['invoices.py check'] if invoices.step_check() else []
    print('  ── roles.py check')
    problems += ['roles.py check'] if roles.step_check() else []
    print('  check: ' + ('OK — Payment Terms and Payment Term Lines in Invoicing after Journals, the lines hidden from '
                         'the sidebar; controls, options, defaults, roll-ups, title formula, mount, rules, buttons and '
                         'views; the relation on Invoices with its rules and no stand-in; Contacts\' two terms and '
                         'their sync; automations C and D and Confirm\'s dating chain, C and Confirm starting no other '
                         'workflow; the roles'
                         if not problems else 'DIFFERENCES\n    ' + '\n    '.join(problems)))
    return len(problems)


def step_verify():
    """The terms and lines against the extract, the three documents' relation, the three contacts' terms."""
    bad = verify_terms()
    bad += verify_carry()
    live = contacts_by_name()
    for name, term in CON_SEED.items():
        c = live.get(name, {})
        ok = (c.get('customer'), c.get('vendor')) == (term, None)
        bad += not ok
        print(f"  {'OK  ' if ok else 'DIFF'}  Contacts {name:<28} Customer Payment Terms {c.get('customer')}, "
              f"Vendor Payment Terms {c.get('vendor')}")
    others = sorted(f"{n}: {c['customer']}/{c['vendor']}" for n, c in live.items()
                    if n not in CON_SEED and (c['customer'] or c['vendor']))
    print(f'  contacts with terms beyond the seed (TEST ones only): {others}')
    bad += sum(1 for o in others if not o.startswith('TEST'))
    return bad


def latest_baseline():
    found = sorted(Path(hap.BACKUPS).glob('payterms_snapshot_baseline_*.json'))
    return found[-1] if found else None


BUNDLE_KEYS = {  # record keys this bundle may change: worksheet -> aliases
    'Invoices': {'invoice_payment_term_id', 'invoice_date_due', INV_FIELD},
    'Contacts': {'property_payment_term_id', 'property_supplier_payment_term_id'},
}


def step_records(path=None):
    """Every record of the nine worksheets against the baseline snapshot, field by field through `record get`: nothing
    may differ but what this bundle writes — Invoices' Payment Terms (text → relation) and, on the three carried
    documents, a Due Date equal to the tenant's; Contacts' two terms — and the only new records must be TEST ones."""
    path = Path(path) if path else latest_baseline()
    snap_ = json.loads(path.read_text(encoding='utf-8'))
    bad = 0
    carried = {hap.ids()['records'][INV_KEY + ref]: due for ref, (_, due) in CARRY.items()}
    for worksheet, entry in snap_['worksheets'].items():
        live = {r['rowid']: read('worksheet', 'record', 'get', entry['id'], r['rowid'], '-a', APP)['data']
                for r in C.records(entry['id'], APP)}
        allowed = BUNDLE_KEYS.get(worksheet, set()) | {c['controlId'] for c in hap.controls(entry['id'])
                                                       if c['controlName'] in (INV_FIELD, CUSTOMER_TERMS, VENDOR_TERMS)
                                                       and worksheet in BUNDLE_KEYS}
        gone = sorted(set(entry['records']) - set(live))
        added = sorted(set(live) - set(entry['records']))
        changed = {}
        for rowid, before in entry['records'].items():
            after = live.get(rowid)
            if after is None:
                continue
            keys = [k for k in sorted(set(before) | set(after)) if not k.startswith('_')
                    and before.get(k) != after.get(k) and not (k not in before and after.get(k) in ('', None, [], 0))]
            unexpected = [k for k in keys if k not in allowed]
            if worksheet == 'Invoices' and 'invoice_date_due' in keys and after.get('invoice_date_due') != carried.get(rowid):
                unexpected.append('invoice_date_due')
            if worksheet == 'Contacts' and any(k in keys for k in BUNDLE_KEYS['Contacts']) and \
                    not str(after.get('name') or '').startswith('TEST') and after.get('name') not in CON_SEED:
                unexpected.append('terms on a contact outside the seed')
            if unexpected:
                changed[rowid] = {k: (before.get(k), after.get(k)) for k in unexpected if k in before or k in after}
        names = {r: [str(live[r].get(k) or '') for k in ('name', 'ref', 'display_name', 'complete_name')] for r in added}
        titles = [next((n for n in names[r] if n.startswith('TEST')), names[r][0] or r) for r in added]
        strays = [t for t in titles if not str(t).startswith('TEST')]
        bad += len(gone) + len(changed) + len(strays)
        print(f"  {'OK  ' if not (gone or changed or strays) else 'DIFF'}  {worksheet:<20} {len(entry['records'])} before, "
              f"{len(live)} now; {len(changed)} changed beyond this bundle's fields; gone {gone}; new {titles}")
        for rowid, d in changed.items():
            print(f'        {rowid}: ' + json.dumps(d, ensure_ascii=False)[:600])
    print(f'  records against {path.name}: {bad} difference(s)')
    return bad


def step_all():
    for name in ('create', 'fields', 'mount', 'computed', 'layout', 'rules', 'buttons', 'views', 'roles', 'seed',
                 'invoices', 'contacts', 'automations', 'carry', 'retire'):
        print(f'\n── {name} ' + '─' * 60)
        STEPS[name]()
    print('\n── check ' + '─' * 60)
    return step_check()


STEPS = {
    'baseline': step_baseline, 'create': step_create, 'fields': step_fields, 'mount': step_mount,
    'computed': step_computed, 'layout': step_layout, 'rules': step_rules, 'buttons': step_buttons,
    'views': step_views, 'roles': step_roles, 'seed': step_seed, 'invoices': step_invoices,
    'contacts': step_contacts, 'automations': step_automations, 'carry': step_carry, 'retire': step_retire,
    'all': step_all, 'verify': step_verify, 'check': step_check, 'selfcheck': step_selfcheck, 'order': step_order,
    'deadrefs': deadrefs, 'records': step_records, 'show': show,
}

if __name__ == '__main__':
    step = sys.argv[1] if len(sys.argv) > 1 else 'check'
    if step not in STEPS:
        raise SystemExit(f"Unknown step {step!r}; choose from {', '.join(STEPS)}")
    result = STEPS[step](*sys.argv[2:])
    if step in ('verify', 'check', 'all', 'selfcheck', 'records', 'deadrefs', 'retire', 'carry', 'seed', 'roles') \
            and result:
        sys.exit(1)
