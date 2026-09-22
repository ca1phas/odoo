#!/usr/bin/env python3
"""Reseed ERP Master with the demo dataset — MyTech Products & Services Sdn Bhd.

The story and every value live in `nocoly/data/demo.json`; this file only writes them. Requirements and the
feature-coverage list: `nocoly/worksheets/22-demo-data.md`. Generic helpers: `common.py`. Run from the repo root
with the CLI's interpreter:

    ~/.hap-venv/bin/python nocoly/build/demo.py plan       # dry run: what would be deleted, what would be
                                                           #   created, per worksheet; resolves every reference
                                                           #   demo.json makes against the live configuration.
                                                           #   **Writes nothing at all.**
    ~/.hap-venv/bin/python nocoly/build/demo.py backup     # export every record of every worksheet this
                                                           #   builder touches to backups/demo-preseed-<stamp>/,
                                                           #   with a manifest naming exactly the rows `wipe`
                                                           #   may delete
    ~/.hap-venv/bin/python nocoly/build/demo.py wipe       # delete them — refuses unless a matching backup
                                                           #   exists. Children before parents.
    ~/.hap-venv/bin/python nocoly/build/demo.py tags       # Contact Tags: the two categories, then their tags
    ~/.hap-venv/bin/python nocoly/build/demo.py contacts   # Contacts: companies and individuals, then the
                                                           #   people and delivery addresses under them
    ~/.hap-venv/bin/python nocoly/build/demo.py products   # Products (each one's first variant is created by
                                                           #   the app's own automation)
    ~/.hap-venv/bin/python nocoly/build/demo.py variants   # the extra variants of the three products that have
                                                           #   them, and each variant's own reference
    ~/.hap-venv/bin/python nocoly/build/demo.py orders     # Orders
    ~/.hap-venv/bin/python nocoly/build/demo.py orderlines # Order Lines, including the discount lines
    ~/.hap-venv/bin/python nocoly/build/demo.py invoices   # Invoices, with the Number built the way Confirm
                                                           #   would build it
    ~/.hap-venv/bin/python nocoly/build/demo.py invlines   # Invoice Lines, then settle their Taxes
    ~/.hap-venv/bin/python nocoly/build/demo.py seed       # every seed step above, then check
    ~/.hap-venv/bin/python nocoly/build/demo.py check      # read everything back: counts, the buckets, the
                                                           #   views, overdue documents and every document's
                                                           #   figures against its own lines
    ~/.hap-venv/bin/python nocoly/build/demo.py show       # the dataset as demo.json states it (no call out)

**Every step reads the live state first and is safe to re-run**; a second run writes nothing. Nothing is deleted
outside `wipe`, and `wipe` deletes only the rows the newest backup's manifest names.

**Dates are offsets from the day this runs.** demo.json never carries a fixed date, so a reseed six months from
now still reads as "the last twelve months".

**Record numbers are never written for Orders.** Orders' Number is an auto-number control (type 33), so the
platform mints it; the demo keys an order on its Customer Reference (a template on its Template Name) and
records the rowid and the minted Number in ids.json. **Reset the auto-number in the browser between `wipe` and
`orders`** — the worksheet's "..." menu, *Reset Auto-number* — or the demo starts where the last build left off.
No other wiped worksheet carries an auto-number.

An invoice Number *is* written, because Invoices' Number is a plain text control that the Confirm workflow
fills. Here it is built the same way Confirm would: `<journal prefix>/<year of the Accounting Date>/<n padded to
five>`, with an `R` in front for a credit note on a journal that has a Dedicated Credit Note Sequence, and the
word "Draft" on an unnumbered draft.

**Records are read through GetRowDetail's `rowData`**, one call per record through the CLI's own session. It is
the only complete read: the record listing blanks a hidden control and leaves a Text or Number its view does not
show out of the row altogether, and `record get` drops a control added after the record existed (BUILDING.md).
`rowData` is keyed by controlId and carried every one of Orders' 53 fields, hidden ones included, in 0.15 s.

**Fields the app's own automations own are not written and not compared**, only reported:
  * a child contact's address, Tax ID, Company ID, DUNS, payment terms and salesperson — copied down from its
    company by *copy company details to its contact* and *push company address and Tax ID to its contacts*;
  * an invoice's Untaxed Amount, Tax, Total and Amount Due — written by *Roll the lines up into the invoice*;
  * an order's Untaxed Amount, Tax and Total — 汇总 over the Order Lines subtable, computed server-side;
  * an invoice line's Account — filled by *fill the account of a new line*;
  * a product's first variant — created by *create a new product's variant*, which copies the product's
    Internal Reference, Cost, Weight and Volume down with it. On a product that has several variants those
    fields are therefore written **only when the product is created**: changing one later copies it onto every
    one of its variants and would wipe the per-variant references (*copy a product's Internal Reference, Cost,
    Weight and Volume to its active variant* gets **all** the active variants). A drift there is reported, never
    written.
  * an order's Signature — writing one on a Quotation or a Quotation Sent order fires *Signed: confirm the
    order*, which confirms it. The image therefore goes only on an order that is already a Sales Order, which is
    what Odoo's own online signing produces.

**No control, view, rule, button or workflow is touched.** This builder writes records and nothing else, and it
never opens the Sales app.
"""
import datetime
import json
import os
import sys
import time
from collections import Counter

import common as C
import hap

APP = hap.ids()['app']
KEY = 'Demo: '                                     # ids.json key prefix for everything this dataset owns
DATA_PATH = os.path.join(hap.HERE, os.pardir, 'data', 'demo.json')
BACKUP_PREFIX = 'demo-preseed-'

# ── the worksheets, and what happens to each ────────────────────────────────
#
# REBUILT: every record goes and is written again from demo.json (bar KEEP_IDS).
# CONFIG:  configuration the demo relies on — only the rows the test builds left behind go.
REBUILT = ('Contact Tags', 'Contacts', 'Products', 'Product Variants',
           'Orders', 'Order Lines', 'Invoices', 'Invoice Lines')
CONFIG = ('Countries', 'States', 'Taxes', 'Chart of Accounts', 'Journals', 'Payment Terms',
          'Payment Term Lines', 'Units & Packagings', 'Product Categories', 'Incoterms')

# The delete order: children before parents.
WIPE_ORDER = ('Invoice Lines', 'Order Lines', 'Invoices', 'Orders', 'Product Variants', 'Products',
              'Contacts', 'Contact Tags', 'Payment Term Lines', 'Payment Terms', 'States', 'Taxes',
              'Chart of Accounts', 'Journals', 'Units & Packagings', 'Product Categories', 'Incoterms',
              'Countries')

# The records that survive the wipe: Odoo's Discount product and its variant, which Orders' *Apply Discount*
# writes its lines with. ids.json holds both ids and this builder keeps them in step.
KEEP_IDS = ('Products: Discount', 'Product Variants: Discount')

# The control a configuration worksheet's test leftovers are recognised by, beside its title. A row counts as a
# leftover when either reads "TEST…" or contains " TEST ". `plan` prints the list and `backup` pins it, so the
# rule never decides anything on its own.
NAME_CONTROL = {'Countries': 'Country Name', 'States': 'State Name', 'Taxes': 'Tax Name',
                'Chart of Accounts': 'Account Name', 'Journals': 'Journal Name',
                'Payment Terms': 'Payment Terms', 'Payment Term Lines': 'Display name',
                'Units & Packagings': 'Unit Name', 'Product Categories': 'Name',
                'Incoterms': 'Name'}
# A Payment Term Line carries no name of its own: it is a leftover when its Payment Terms is one.
CHILD_OF = {'Payment Term Lines': ('Payment Terms', 'Payment Terms')}
# Worksheets that point at themselves: a record is deleted after every record of the same worksheet that names
# it as its parent, so a hierarchy never loses its middle.
SELF_PARENT = {'Contact Tags': 'Category', 'Contacts': 'Company', 'Product Categories': 'Parent Category'}


def ws(name):
    wid = hap.ids()['worksheets'].get(name)
    if not wid:
        sys.exit(f'{name} is not in ids.json worksheets — nothing here can run')
    return wid


# ── demo.json ───────────────────────────────────────────────────────────────

_DATA = None


def data():
    global _DATA
    if _DATA is None:
        with open(DATA_PATH) as f:
            _DATA = json.load(f)
    return _DATA


TODAY = datetime.date.today()


def day(offset):
    """A date offset in days from the seeding day, as 'YYYY-MM-DD'."""
    return (TODAY + datetime.timedelta(days=int(offset))).isoformat()


def moment(offset, clock='09:00:00'):
    """A date-time offset in days from the seeding day, as 'YYYY-MM-DD HH:MM:SS'."""
    return f'{day(offset)} {clock}'


# ── reading: GetRowDetail's rowData, the only complete read ─────────────────

_SESSION = None
_CONTROLS = {}


def session():
    global _SESSION
    if _SESSION is None:
        from hap_cli.core.session import Session
        _SESSION = Session.load(None)
    return _SESSION


def controls(name):
    """The worksheet's controls by name, read once per run."""
    if name not in _CONTROLS:
        _CONTROLS[name] = C.fields(ws(name))
    return _CONTROLS[name]


def title_control(name):
    c = next((c for c in hap.controls(ws(name)) if c.get('attribute') == 1), None)
    if not c:
        sys.exit(f'{name} has no title control')
    return c


def row(name, rowid):
    """One record as GetRowDetail's `rowData` — every control, keyed by controlId, hidden ones included."""
    res = session().api_call('Worksheet', 'GetRowDetail', {'worksheetId': ws(name), 'rowId': rowid})
    raw = res.get('rowData') if isinstance(res, dict) else None
    if not isinstance(raw, str):
        raise RuntimeError(f'GetRowDetail on {name}/{rowid} answered '
                           f'{json.dumps(res, ensure_ascii=False)[:200]}')
    return json.loads(raw)


def all_rows(name):
    """{rowid: rowData} for every record of the worksheet — one GetRowDetail each, complete."""
    return {r['rowid']: row(name, r['rowid']) for r in scan(name).values()}


def scan(name, fresh=False):
    """{rowid: the record listing's row}, keyed by controlId — one or two HTTP calls for the whole worksheet.

    Cheap but **not complete**: a hidden control reads back empty and a Text or Number the worksheet's view
    does not show has no key at all (BUILDING.md). Used only where the title, a relation or a dropdown is
    enough — recognising the test leftovers, counting rows — never to compare a seeded value."""
    if fresh or name not in _SCAN:
        _SCAN[name] = {r['rowid']: r for r in C.records(ws(name), APP)}
    return _SCAN[name]


_SCAN = {}


def rowid_list(name, fresh=True):
    return list(scan(name, fresh=fresh))


# ── normalising a rowData value ─────────────────────────────────────────────

def raw(d, f, name):
    return d.get(f[name]['controlId'])


def t(d, f, name):
    v = raw(d, f, name)
    return '' if v is None else (v if isinstance(v, str) else str(v))


def n(d, f, name, dot=2):
    try:
        return round(float(raw(d, f, name) or 0), dot)
    except (TypeError, ValueError):
        return 0.0


def sw(d, f, name):
    return '1' if str(raw(d, f, name)) in ('1', 'True', 'true') else '0'


def dateonly(d, f, name):
    return t(d, f, name)[:10]


def stamp(d, f, name):
    return t(d, f, name)[:19]


def _items(v):
    if isinstance(v, str):
        if not v.startswith('['):
            return [v] if v else []
        try:
            return json.loads(v)
        except ValueError:
            return []
    return v if isinstance(v, list) else []


def opt(d, f, name):
    """A single select as its label. `rowData` hands back the option keys, not the labels."""
    labels = {o['key']: o['value'] for o in f[name].get('options') or []}
    keys = [x.get('key') if isinstance(x, dict) else x for x in _items(raw(d, f, name))]
    return (labels.get(keys[0], keys[0]) or '') if keys else ''


def rel_names(d, f, name):
    return [x.get('name') for x in _items(raw(d, f, name)) if isinstance(x, dict)]


def rel_ids(d, f, name):
    return [x.get('sid') for x in _items(raw(d, f, name)) if isinstance(x, dict)]


def one_name(d, f, name):
    got = rel_names(d, f, name)
    return got[0] if got else ''


def one_id(d, f, name):
    got = rel_ids(d, f, name)
    return got[0] if got else ''


def option_key(control, label):
    key = next((o['key'] for o in control.get('options') or [] if o['value'] == label), None)
    if key is None:
        sys.exit(f"{control['controlName']}: no option {label!r} "
                 f"(it has {[o['value'] for o in control.get('options') or []]})")
    return key


def titles(name, control_name=None):
    """{title: rowid} of a worksheet, for resolving a Relation by the name a person would type."""
    cid = (controls(name)[control_name] if control_name else title_control(name))['controlId']
    out = {}
    for r in C.records(ws(name), APP):
        out.setdefault(r.get(cid), r['rowid'])
    return out


# ── writing ─────────────────────────────────────────────────────────────────

_ME = None


def salesperson():
    """The account the profile is signed in as, read rather than hard-coded (invoices.salesperson_id)."""
    global _ME
    if _ME is None:
        _ME = hap.run('auth', 'whoami')['id']
    return _ME


def write(name, rowid, values, label):
    body = json.dumps(values, ensure_ascii=False)
    if rowid:
        hap.run('worksheet', 'record', 'update', ws(name), rowid, '-a', APP, '--fields-json', body)
        return rowid, 'updated'
    made = C.row_id(hap.run('worksheet', 'record', 'create', ws(name), '-a', APP, '--fields-json', body))
    if not made:
        sys.exit(f'{name}: {label} was not created ({body[:200]})')
    return made, 'created'


def remember(worksheet, key, rowid):
    C.remember('records', f'{KEY}{worksheet} {key}', rowid)


def remembered(worksheet, key):
    return hap.ids().get('records', {}).get(f'{KEY}{worksheet} {key}')


def differences(got, want):
    return {k: (got.get(k), v) for k, v in want.items() if got.get(k) != v}


def split_owned(label, diffs, owned):
    """Print the drift an automation owns and return what this builder owns."""
    theirs = {k: v for k, v in diffs.items() if k in owned}
    if theirs:
        print(f"  {label}: the app's own automations own "
              f'{json.dumps(theirs, ensure_ascii=False, default=str)}')
    return {k: v for k, v in diffs.items() if k not in owned}


def fail(step, bad):
    if bad:
        sys.exit(f'{step}: read back with differences\n    ' + '\n    '.join(bad))
    return 0


# ── 1 · the rows the wipe covers ────────────────────────────────────────────

def keep_ids():
    ids = hap.ids().get('records', {})
    return {ids[k] for k in KEEP_IDS if ids.get(k)}


def identity(name, record, title_cid):
    """What `wipe` checks a row still reads as before it deletes it. For a worksheet whose rows share a title —
    Payment Term Lines' "100 Percent · 30 · Days after invoice date" is on two different terms — the parent's
    name is part of it, so the guard still tells them apart."""
    got = str(record.get(title_cid) or '')
    if name in CHILD_OF:
        control, _target = CHILD_OF[name]
        parent = rel_names(record, controls(name), control)
        if parent:
            got = f'{got}  <- {parent[0]}'
    return got


def is_leftover(name, record, title_cid, name_cid, parent_leftovers):
    if name in CHILD_OF:
        control, _target = CHILD_OF[name]
        return bool(set(rel_ids(record, controls(name), control)) & parent_leftovers)
    for cid in (title_cid, name_cid):
        value = record.get(cid) or '' if cid else ''
        value = value if isinstance(value, str) else str(value)
        if value.startswith('TEST') or ' TEST ' in f' {value} ':
            return True
    return False


def children_first(name, todo, rows):
    """Order a worksheet's delete list so a parent goes after every child of its own worksheet."""
    control = SELF_PARENT.get(name)
    if not control or control not in controls(name):
        return todo
    depth, index = {}, {rowid: ident for rowid, ident in todo}

    def level(rowid, seen=()):
        if rowid in depth:
            return depth[rowid]
        parent = one_id(rows.get(rowid, {}), controls(name), control)
        depth[rowid] = 0 if (not parent or parent not in index or rowid in seen) else \
            1 + level(parent, seen + (rowid,))
        return depth[rowid]

    return sorted(todo, key=lambda pair: -level(pair[0]))


# The order the delete lists are *computed* in: a parent worksheet before the child that reads it.
COMPUTE_ORDER = tuple(w for w in WIPE_ORDER if w not in CHILD_OF) + tuple(CHILD_OF)


def deletions():
    """{worksheet: [(rowid, identity), ...]} — every row the wipe covers, read off the live app.

    A rebuilt worksheet gives up all of its records but KEEP_IDS; a configuration worksheet gives up only the
    rows the test builds left behind. Each list is ordered children-first."""
    keep, out = keep_ids(), {}
    for name in COMPUTE_ORDER:
        tid = title_control(name)['controlId']
        rows = scan(name)                       # the listing is enough: a title, a relation and a name
        if name in REBUILT:
            todo = [(rowid, identity(name, d, tid)) for rowid, d in rows.items() if rowid not in keep]
        else:
            name_cid = (controls(name).get(NAME_CONTROL.get(name)) or {}).get('controlId')
            parents = set()
            if name in CHILD_OF:
                _control, target = CHILD_OF[name]
                parents = {rowid for rowid, _ in out.get(target, [])}
            todo = [(rowid, identity(name, d, tid)) for rowid, d in rows.items()
                    if is_leftover(name, d, tid, name_cid, parents)]
        out[name] = children_first(name, todo, rows)
    return out


# ── 2 · backup ──────────────────────────────────────────────────────────────

def slug(name):
    return name.lower().replace(' & ', '-').replace(' ', '-')


def step_backup():
    """Export every record of every worksheet this builder touches, and pin the rows `wipe` may delete.

    Each worksheet gets `<folder>/<worksheet>.json`: `rows`, the full listing of every record, and `detail`,
    GetRowDetail's complete `rowData` for every row the wipe would delete. The file's row count is verified
    against the live count, and `_manifest.json` records the counts, every live rowid and the exact delete
    list. `wipe` reads the newest manifest and will not go past it."""
    root = os.path.join(hap.BACKUPS, f'{BACKUP_PREFIX}{datetime.datetime.now():%Y%m%d-%H%M%S}')
    os.makedirs(root, exist_ok=True)
    planned = deletions()
    manifest = {'stamp': os.path.basename(root), 'app': APP, 'taken_on': TODAY.isoformat(),
                'keep': sorted(keep_ids()), 'worksheets': {}}
    total_rows = total_delete = 0
    for name in WIPE_ORDER:
        wid = ws(name)
        rows = C.records(wid, APP)
        live = {r['rowid'] for r in rows}
        todo = [(rowid, ident) for rowid, ident in planned[name] if rowid in live]
        detail = {rowid: row(name, rowid) for rowid, _ in todo}
        path = os.path.join(root, f'{slug(name)}.json')
        with open(path, 'w') as f:
            json.dump({'worksheet': name, 'worksheetId': wid, 'count': len(rows), 'rows': rows,
                       'detail': detail}, f, ensure_ascii=False, indent=1)
        back = json.load(open(path))
        if len(back['rows']) != len(rows) or back['count'] != len(rows):
            sys.exit(f'{name}: the backup holds {len(back["rows"])} rows and the worksheet {len(rows)} '
                     '— stopping')
        if sorted(back['detail']) != sorted(r for r, _ in todo):
            sys.exit(f'{name}: the backup detail covers {len(back["detail"])} of {len(todo)} rows to delete')
        manifest['worksheets'][name] = {'worksheetId': wid, 'count': len(rows), 'file': f'{slug(name)}.json',
                                        'rowids': sorted(live),
                                        'delete': [[rowid, ident] for rowid, ident in todo]}
        total_rows += len(rows)
        total_delete += len(todo)
        print(f'  {name:<20} {len(rows):>5} rows backed up, {len(todo):>4} of them named for deletion  '
              f'-> {os.path.basename(path)}')
    manifest['signature_image'] = keep_signature(root)
    with open(os.path.join(root, '_manifest.json'), 'w') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)
    print(f'  {total_rows} records of {len(WIPE_ORDER)} worksheets in {root}')
    print(f"  {total_delete} named for deletion; every file's row count matches the live count")
    return 0


def keep_signature(root):
    """Keep the signature image the wipe is about to take away.

    The two signed demo orders reuse the image a browser test left on a live order (the owner's decision, 23 Sep
    2026), and the wipe deletes the order that holds it — so the image is copied into ids.json under
    `Orders: signature image` while it is still readable. Nothing else about that order is kept.

    **What is kept is the path, not the URL the read hands back.** A HAP signature URL carries a time-limited
    token (`?e=<epoch>&token=…`) and the server mints a fresh one on **every** read — the same image read twice
    two hours apart came back with two different `e=` values — so the stored value is the path and the token is
    decoration. Keeping the path means the id in ids.json never goes stale; whether writing it back into a
    signature control stores is what `orders` proves, and it reports either way."""
    have = signature_image()
    if have:
        print(f'  signature image already kept in ids.json: {have}')
        return have
    f = controls('Orders')
    found = {}
    for rowid in scan('Orders'):
        d = row('Orders', rowid)
        got = t(d, f, 'Signature')
        if got:
            found[rowid] = (got, t(d, f, 'Signed By'), t(d, f, 'Number'))
    if not found:
        print('  no live order carries a Signature, so the two signed demo orders will carry Signed By and '
              'Signed On and no image')
        return ''
    # the owner named the browser-signed order; fall back to whichever is there
    rowid = next((r for r, (_u, by, _no) in found.items() if 'browser' in by.lower()), sorted(found)[0])
    url, by, number = found[rowid]
    path = url.split('?')[0]
    C.remember('records', SIGNATURE_SOURCE, path)
    print(f'  signature image kept in ids.json from {number} ({by!r}), without its per-read token: {path}')
    print(f'  {len(found)} live order(s) carry one: '
          + ', '.join(f'{no} ({b!r})' for _r, (_u, b, no) in sorted(found.items(), key=lambda x: x[1][2])))
    return path


def newest_backup():
    if not os.path.isdir(hap.BACKUPS):
        return None
    folders = sorted(d for d in os.listdir(hap.BACKUPS)
                     if d.startswith(BACKUP_PREFIX)
                     and os.path.isfile(os.path.join(hap.BACKUPS, d, '_manifest.json')))
    return os.path.join(hap.BACKUPS, folders[-1]) if folders else None


def checked_manifest():
    """The newest backup's manifest, with every check `wipe` refuses to run without: it exists, it is of this
    app, it covers every worksheet, every file's row count matches its own manifest entry, and **every record
    that is live now is in it** — so a row the owner added after the backup stops the wipe instead of being
    swept up."""
    root = newest_backup()
    if not root:
        sys.exit(f'no {BACKUP_PREFIX}* backup with a manifest in {hap.BACKUPS} — run `backup` first')
    manifest = json.load(open(os.path.join(root, '_manifest.json')))
    if manifest.get('app') != APP:
        sys.exit(f'{root}: the backup is of app {manifest.get("app")}, not {APP}')
    problems = []
    for name in WIPE_ORDER:
        entry = manifest['worksheets'].get(name)
        if not entry:
            problems.append(f'{name} is not in the manifest')
            continue
        path = os.path.join(root, entry['file'])
        if not os.path.isfile(path):
            problems.append(f'{name}: {entry["file"]} is missing')
            continue
        saved = json.load(open(path))
        if len(saved['rows']) != entry['count']:
            problems.append(f'{name}: {entry["file"]} holds {len(saved["rows"])} rows, '
                            f'the manifest says {entry["count"]}')
        live = set(rowid_list(name))
        unbacked = sorted(live - set(entry['rowids']))
        if unbacked:
            problems.append(f'{name}: {len(unbacked)} live record(s) are not in the backup '
                            f'({unbacked[:5]}) — re-run `backup`')
    if problems:
        sys.exit(f'the backup in {root} does not match the live app:\n    ' + '\n    '.join(problems))
    print(f"  backup {os.path.basename(root)}: every worksheet present, every file's row count matches, "
          'every live record is in it')
    return root, manifest


# ── 3 · wipe ────────────────────────────────────────────────────────────────

def step_wipe():
    """Delete the rows the newest backup's manifest names, children before parents — and nothing else.

    Re-running is a no-op once the named rows are gone, whatever else the worksheets hold, so it is safe to run
    again after a seed. The delete is **soft** — `--permanent` is not passed, so each row goes to the
    worksheet's recycle bin — and `--trigger-workflow` is written out in full because the CLI sends
    `triggerWorkflow: false` without it (BUILDING.md), which would leave an invoice's amounts stale with no
    error at all."""
    root, manifest = checked_manifest()
    keep = keep_ids()
    done = left = 0
    for name in WIPE_ORDER:
        entry = manifest['worksheets'][name]
        approved = {rowid: ident for rowid, ident in entry['delete']}
        order = [rowid for rowid, _ in entry['delete']]
        live = set(rowid_list(name))
        todo = [rowid for rowid in order if rowid in live]
        if not todo:
            print(f'  {name:<20} nothing of the {len(approved)} named rows is still live '
                  f'({len(live)} record(s) left)')
            left += len(live)
            continue
        if set(todo) & keep:
            sys.exit(f'{name}: the manifest names a record ids.json keeps ({sorted(set(todo) & keep)})')
        tid = title_control(name)['controlId']
        for rowid in todo:
            got = identity(name, row(name, rowid), tid)
            if got != approved[rowid]:
                sys.exit(f'{name} {rowid} now reads {got!r}, the backup named {approved[rowid]!r} — stopping')
        for rowid in todo:
            hap.run('worksheet', 'record', 'delete', ws(name), '--row-ids', rowid, '-a', APP,
                    '--trigger-workflow', '-y')
        back = set(rowid_list(name))
        still = sorted(set(todo) & back)
        if still:
            sys.exit(f'{name}: {still} read back from the worksheet — the delete did not store')
        done += len(todo)
        left += len(back)
        print(f'  {name:<20} {len(todo):>4} deleted, {len(back):>5} record(s) left')
    print(f'  {done} records deleted, {left} left across the {len(WIPE_ORDER)} worksheets')
    print(f'  kept: {sorted(keep)} — the Discount product and its variant')
    print("  NEXT, in the browser: Orders' \"...\" menu > Reset Auto-number > next record 1. "
          'Then run the seed steps.')
    return 0


# ── 4 · Contact Tags ────────────────────────────────────────────────────────

def tag_path(t_, by_key):
    """A tag's Complete Name as the worksheet computes it: "<category> / <name>"."""
    return f"{by_key[t_['parent']]['name']} / {t_['name']}" if t_['parent'] else t_['name']


def tag_state(d):
    f = controls('Contact Tags')
    return dict(path=t(d, f, 'Complete Name'), name=t(d, f, 'Name'), color=opt(d, f, 'Color'),
                parent=one_name(d, f, 'Category'), active=sw(d, f, 'Active'))


def tag_want(t_, by_key):
    return dict(name=t_['name'], color=t_['color'], active='1',
                parent=tag_path(by_key[t_['parent']], by_key) if t_['parent'] else '')


def step_tags():
    """The two categories and the eight tags under them. Categories first: Complete Name concatenates the
    category's name, so a tag written before its category would read back without it."""
    f = controls('Contact Tags')
    cid = lambda name: f[name]['controlId']
    by_key = {x['key']: x for x in data()['tags']}
    live = {rowid: tag_state(d) for rowid, d in all_rows('Contact Tags').items()}
    wrote = 0
    for t_ in sorted(data()['tags'], key=lambda x: (x['parent'] is not None, x['name'])):
        path = tag_path(t_, by_key)
        want = tag_want(t_, by_key)
        rowid = remembered('Contact Tags', t_['key'])
        got = live.get(rowid) or next((v for v in live.values() if v['path'] == path), None)
        if got and not differences(got, want):
            remember('Contact Tags', t_['key'], next(r for r, v in live.items() if v is got))
            continue
        values = [{'id': cid('Name'), 'value': t_['name']},
                  {'id': cid('Color'), 'value': [option_key(f['Color'], t_['color'])]},
                  {'id': cid('Active'), 'value': '1'}]
        if t_['parent']:
            parent_path = tag_path(by_key[t_['parent']], by_key)
            parent = next((r for r, v in live.items() if v['path'] == parent_path), None)
            if not parent:
                sys.exit(f"{path}: its category {parent_path!r} is not on the worksheet yet")
            values.append({'id': cid('Category'), 'value': [parent]})
        target = next((r for r, v in live.items() if v is got), None)
        rowid, how = write('Contact Tags', target, values, path)
        wrote += 1
        live[rowid] = tag_state(row('Contact Tags', rowid))
        print(f'  {how} {path}: {rowid}')
        remember('Contact Tags', t_['key'], rowid)
    return tags_verify(wrote=wrote)


def tags_verify(wrote=None):
    by_key = {x['key']: x for x in data()['tags']}
    live = {rowid: tag_state(d) for rowid, d in all_rows('Contact Tags').items()}
    bad = []
    for t_ in data()['tags']:
        got = live.get(remembered('Contact Tags', t_['key']))
        if not got:
            bad.append(f"{tag_path(t_, by_key)} is not on the worksheet")
            continue
        diffs = differences(got, tag_want(t_, by_key))
        if diffs:
            bad.append(f"{tag_path(t_, by_key)}: {json.dumps(diffs, ensure_ascii=False, default=str)}")
    print(f"  {len(data()['tags'])} tags in the dataset, {len(live)} on the worksheet"
          + (f', {wrote} written this run' if wrote is not None else ''))
    return fail('tags', bad)


# ── 5 · Contacts ────────────────────────────────────────────────────────────

CONTACT_TEXT = {'name': 'Name', 'email': 'Email', 'phone': 'Phone', 'job': 'Job Position',
                'website': 'Website', 'vat': 'Tax ID', 'company_registry': 'Company ID',
                'street': 'Street', 'street2': 'Street 2', 'city': 'City', 'zip': 'ZIP',
                'ref': 'Reference'}
# what the company's own automations own on a child contact
CHILD_OWNED = ('street', 'street2', 'city', 'zip', 'state', 'country', 'vat', 'company_registry',
               'customer_terms', 'vendor_terms')


def contact_state(d):
    f = controls('Contacts')
    out = {k: t(d, f, name) for k, name in CONTACT_TEXT.items()}
    out.update(display=t(d, f, 'Display Name'), company=one_name(d, f, 'Company'),
               type=opt(d, f, 'Address Type'), state=one_name(d, f, 'State'),
               country=one_name(d, f, 'Country'), tags=sorted(rel_names(d, f, 'Tags')),
               customer_terms=one_name(d, f, 'Customer Payment Terms'),
               vendor_terms=one_name(d, f, 'Vendor Payment Terms'), active=sw(d, f, 'Active'))
    return out


def contact_want(c, display_of, tag_names, states_short):
    want = {k: (c.get(k) or '') for k in CONTACT_TEXT}
    want.update(type=c['type'], active='1',
                tags=sorted(tag_names[x] for x in c.get('tags', [])),
                company=display_of(c['company']) if c['company'] else '')
    if c['company']:
        for k in CHILD_OWNED:
            want.pop(k, None)
        return want
    want['state'] = states_short.get(c.get('state'), '') if c.get('state') else ''
    want['country'] = c.get('country') or ''
    want['customer_terms'] = c.get('customer_terms') or ''
    want['vendor_terms'] = c.get('vendor_terms') or ''
    return want


def tag_names_by_key():
    by_key = {x['key']: x for x in data()['tags']}
    return {k: tag_path(v, by_key) for k, v in by_key.items()}


def step_contacts():
    """The fifteen companies and individuals, then the people and delivery addresses under them.

    A child contact's address, identifiers and payment terms are **not written**: *copy company details to its
    contact* fills them from the company a moment after the row is saved, and *push company address and Tax ID
    to its contacts* re-fills them whenever the company changes. demo.json states them only on the company —
    which also means a delivery address that differs from its company's cannot be expressed in this app."""
    f = controls('Contacts')
    cid = lambda name: f[name]['controlId']
    tag_rows, tag_label = titles('Contact Tags'), tag_names_by_key()
    terms, states, countries = titles('Payment Terms'), titles('States'), titles('Countries')
    states_short = {x.split(' (')[0]: x for x in states}
    live = {rowid: contact_state(d) for rowid, d in all_rows('Contacts').items()}
    mine = {}
    wrote = 0
    for c in data()['contacts']:
        display_of = lambda key: mine.get(key, {}).get('display', '')
        want = contact_want(c, display_of, tag_label, states_short)
        rowid = remembered('Contacts', c['key'])
        got = live.get(rowid)
        if not got:
            rowid = next((r for r, v in live.items()
                          if v['name'] == c['name']
                          and v['company'] == (display_of(c['company']) if c['company'] else '')), None)
            got = live.get(rowid)
        if got and not differences(got, want):
            mine[c['key']] = dict(got, rowid=rowid)
            remember('Contacts', c['key'], rowid)
            continue
        values = [{'id': cid(name), 'value': (c.get(k) or '')} for k, name in CONTACT_TEXT.items()
                  if not (c['company'] and k in CHILD_OWNED)]
        values += [{'id': cid('Address Type'), 'value': [option_key(f['Address Type'], c['type'])]},
                   {'id': cid('Active'), 'value': '1'},
                   {'id': cid('Tags'), 'value': [tag_rows[tag_label[x]] for x in c.get('tags', [])]}]
        if c.get('notes'):
            values.append({'id': cid('Notes'), 'value': f"<p>{c['notes']}</p>"})
        if c['company']:
            parent = mine.get(c['company'], {}).get('rowid')
            if not parent:
                sys.exit(f"{c['key']}: its company {c['company']} is not on the worksheet yet")
            values.append({'id': cid('Company'), 'value': [parent]})
        else:
            values.append({'id': cid('Salesperson'), 'value': [salesperson()]})
            values.append({'id': cid('State'),
                           'value': [states[states_short[c['state']]]] if c.get('state') else []})
            values.append({'id': cid('Country'),
                           'value': [countries[c['country']]] if c.get('country') else []})
            for k, name in (('customer_terms', 'Customer Payment Terms'),
                            ('vendor_terms', 'Vendor Payment Terms')):
                values.append({'id': cid(name), 'value': [terms[c[k]]] if c.get(k) else []})
        rowid, how = write('Contacts', rowid, values, c['key'])
        wrote += 1
        live[rowid] = contact_state(row('Contacts', rowid))
        mine[c['key']] = dict(live[rowid], rowid=rowid)
        print(f"  {how} {c['key']:<12} {live[rowid]['display']}: {rowid}")
        remember('Contacts', c['key'], rowid)
    return contacts_verify(wrote=wrote)


def contacts_verify(wrote=None):
    tag_label = tag_names_by_key()
    states_short = {x.split(' (')[0]: x for x in titles('States')}
    live = {rowid: contact_state(d) for rowid, d in all_rows('Contacts').items()}
    mine = {c['key']: live.get(remembered('Contacts', c['key']), {}) for c in data()['contacts']}
    bad = []
    for c in data()['contacts']:
        got = mine[c['key']]
        if not got:
            bad.append(f"{c['key']} is not on the worksheet")
            continue
        want = contact_want(c, lambda key: mine.get(key, {}).get('display', ''), tag_label, states_short)
        diffs = split_owned(c['key'], differences(got, want), CHILD_OWNED)
        if diffs:
            bad.append(f"{c['key']}: {json.dumps(diffs, ensure_ascii=False, default=str)}")
    print(f"  {len(data()['contacts'])} contacts in the dataset, {len(live)} on the worksheet"
          + (f', {wrote} written this run' if wrote is not None else ''))
    return fail('contacts', bad)


# ── 6 · Products ────────────────────────────────────────────────────────────

# copied down to *every* active variant whenever one of them changes on the product
PRODUCT_COPIED = ('internal_reference', 'cost')


def product_state(d):
    f = controls('Products')
    return dict(name=t(d, f, 'Name'), internal_reference=t(d, f, 'Internal Reference'),
                type=opt(d, f, 'Product Type'), list_price=n(d, f, 'Sales Price'), cost=n(d, f, 'Cost'),
                unit=one_name(d, f, 'Unit'), category=one_name(d, f, 'Category'),
                sales_taxes=sorted(rel_names(d, f, 'Sales Taxes')),
                purchase_taxes=sorted(rel_names(d, f, 'Purchase Taxes')),
                sales=sw(d, f, 'Sales'), purchase=sw(d, f, 'Purchase'), active=sw(d, f, 'Active'),
                sales_description=t(d, f, 'Sales Description'))


def product_want(p):
    return dict(name=p['name'], internal_reference=p['internal_reference'], type=p['type'],
                list_price=round(float(p['list_price']), 2), cost=round(float(p['cost']), 2),
                unit=p['unit'], category=p['category'], sales_taxes=sorted(p['sales_taxes']),
                purchase_taxes=sorted(p['purchase_taxes']),
                sales='1' if p['sales'] else '0', purchase='1' if p['purchase'] else '0',
                active='1' if p['active'] else '0', sales_description=p['sales_description'])


def step_products():
    """The nineteen products. Each one's first variant is created by *create a new product's variant* a moment
    after the row is written, so nothing here creates it.

    On a product that already exists **and has several variants**, Internal Reference and Cost are not written
    when they differ: any change to them is copied onto *every* active variant, which would wipe the
    per-variant references. The difference is reported instead."""
    f = controls('Products')
    cid = lambda name: f[name]['controlId']
    taxes, units, cats = titles('Taxes'), titles('Units & Packagings'), titles('Product Categories')
    live = {rowid: product_state(d) for rowid, d in all_rows('Products').items()}
    wrote, notes = 0, []
    for p in data()['products']:
        want = product_want(p)
        rowid = remembered('Products', p['key'])
        got = live.get(rowid)
        if not got:
            rowid = next((r for r, v in live.items()
                          if v['internal_reference'] == p['internal_reference']
                          and v['name'] == p['name']), None)
            got = live.get(rowid)
        diffs = differences(got, want) if got else dict(want)
        if got and len(p['variants']) > 1:
            frozen = {k: v for k, v in diffs.items() if k in PRODUCT_COPIED}
            if frozen:
                notes.append(f"{p['key']}: {json.dumps(frozen, ensure_ascii=False, default=str)} left as it "
                             'is — writing it would copy it onto every one of its variants')
            diffs = {k: v for k, v in diffs.items() if k not in PRODUCT_COPIED}
        if got and not diffs:
            remember('Products', p['key'], rowid)
            continue
        values = [
            {'id': cid('Name'), 'value': p['name']},
            {'id': cid('Internal Reference'), 'value': p['internal_reference']},
            {'id': cid('Product Type'), 'value': [option_key(f['Product Type'], p['type'])]},
            {'id': cid('Sales Price'), 'value': p['list_price']},
            {'id': cid('Cost'), 'value': p['cost']},
            {'id': cid('Unit'), 'value': [units[p['unit']]]},
            {'id': cid('Category'), 'value': [cats[p['category']]]},
            {'id': cid('Sales Taxes'), 'value': [taxes[x] for x in p['sales_taxes']]},
            {'id': cid('Purchase Taxes'), 'value': [taxes[x] for x in p['purchase_taxes']]},
            {'id': cid('Sales'), 'value': '1' if p['sales'] else '0'},
            {'id': cid('Purchase'), 'value': '1' if p['purchase'] else '0'},
            {'id': cid('Active'), 'value': '1' if p['active'] else '0'},
            {'id': cid('Sales Description'), 'value': p['sales_description']},
            {'id': cid('Favorite'), 'value': '0'},
            {'id': cid('Weight'), 'value': 0},
            {'id': cid('Volume'), 'value': 0},
        ]
        if got and len(p['variants']) > 1:
            values = [v for v in values if v['id'] not in (cid('Internal Reference'), cid('Cost'))]
        rowid, how = write('Products', rowid, values, p['key'])
        wrote += 1
        live[rowid] = product_state(row('Products', rowid))
        print(f"  {how} {p['key']:<12} {p['name']}: {rowid}")
        remember('Products', p['key'], rowid)
    for note in notes:
        print(f'  {note}')
    if wrote:
        settle_variants()
    return products_verify(wrote=wrote)


def products_verify(wrote=None):
    live = {rowid: product_state(d) for rowid, d in all_rows('Products').items()}
    bad = []
    for p in data()['products']:
        got = live.get(remembered('Products', p['key']))
        if not got:
            bad.append(f"{p['key']} is not on the worksheet")
            continue
        diffs = differences(got, product_want(p))
        if diffs and len(p['variants']) > 1:
            diffs = split_owned(p['key'], diffs, PRODUCT_COPIED)
        if diffs:
            bad.append(f"{p['key']}: {json.dumps(diffs, ensure_ascii=False, default=str)}")
    print(f"  {len(data()['products'])} products in the dataset, {len(live)} on the worksheet"
          + (f', {wrote} written this run' if wrote is not None else ''))
    return fail('products', bad)


# ── 7 · Product Variants ────────────────────────────────────────────────────

def variant_state(d):
    f = controls('Product Variants')
    return dict(display=t(d, f, 'Display Name'), product=one_id(d, f, 'Product'),
                internal_reference=t(d, f, 'Internal Reference'), barcode=t(d, f, 'Barcode'),
                cost=n(d, f, 'Cost'), active=sw(d, f, 'Active'))


def settle_variants(seconds=30):
    """Wait for *create a new product's variant* to land on every product the dataset names.

    It is a worksheet-event workflow, so it runs a few seconds **after** the product is written (BUILDING.md);
    a variants step that reads too early sees no variant and would create a second one."""
    wanted = {remembered('Products', p['key']) for p in data()['products']} - {None}
    missing = sorted(wanted)
    for _ in range(seconds):
        have = {v['product'] for v in (variant_state(d) for d in all_rows('Product Variants').values())}
        missing = sorted(wanted - have)
        if not missing:
            print(f'  every one of the {len(wanted)} products has its first variant')
            return True
        time.sleep(1)
    print(f'  waited {seconds}s and {len(missing)} product(s) still have no variant ({missing[:3]}) — '
          'the variants step will create them')
    return False


def variant_specs():
    """[(product key, variant key, reference, barcode, cost, active, is_first)] for the whole dataset."""
    out = []
    for p in data()['products']:
        active = '1' if p['active'] else '0'
        if not p['variants']:
            out.append((p['key'], p['key'], p['internal_reference'], '',
                        round(float(p['cost']), 2), active, True))
            continue
        for i, v in enumerate(p['variants']):
            out.append((p['key'], v['key'], v['internal_reference'], v['barcode'],
                        round(float(v['cost']), 2), active, i == 0))
    return out


def step_variants():
    """Give the automatically created variant its own reference, and create the extra variants of the three
    products that have more than one.

    A variant carries no attribute of its own — the app has no product-attribute model — so the storage and
    colour of a myBook or a myPhone live in its Internal Reference and its Barcode, and the Display Name reads
    "[MYB-AIR13-512-MID] myBook Air 13"". Written on the variant, never on the product: the product's own
    Internal Reference and Cost are copied down to *all* of its variants."""
    f = controls('Product Variants')
    cid = lambda name: f[name]['controlId']
    settle_variants()
    live = {rowid: variant_state(d) for rowid, d in all_rows('Product Variants').items()}
    wrote = 0
    for pkey, vkey, ref, barcode, cost, active, is_first in variant_specs():
        product_row = remembered('Products', pkey)
        if not product_row:
            sys.exit(f'{pkey} is not in ids.json — run `products` first')
        want = dict(product=product_row, internal_reference=ref, barcode=barcode, cost=cost, active=active)
        rowid = remembered('Product Variants', vkey)
        got = live.get(rowid)
        if not got:
            mine = {r: v for r, v in live.items() if v['product'] == product_row}
            rowid = next((r for r, v in mine.items() if v['internal_reference'] == ref), None)
            if rowid is None and is_first:
                # the variant the automation made carries the product's own reference, or none at all
                rowid = next((r for r, v in mine.items() if v['internal_reference'] in ('', ref)), None)
            got = live.get(rowid)
        if got and not differences(got, want):
            remember('Product Variants', vkey, rowid)
            continue
        values = [{'id': cid('Internal Reference'), 'value': ref},
                  {'id': cid('Barcode'), 'value': barcode},
                  {'id': cid('Cost'), 'value': cost},
                  {'id': cid('Active'), 'value': active},
                  {'id': cid('Product'), 'value': [product_row]}]
        rowid, how = write('Product Variants', rowid, values, vkey)
        wrote += 1
        live[rowid] = variant_state(row('Product Variants', rowid))
        print(f'  {how} {vkey:<22} ({pkey}): {rowid}')
        remember('Product Variants', vkey, rowid)
    return variants_verify(wrote=wrote)


def variants_verify(wrote=None):
    live = {rowid: variant_state(d) for rowid, d in all_rows('Product Variants').items()}
    bad = []
    for pkey, vkey, ref, barcode, cost, active, _first in variant_specs():
        got = live.get(remembered('Product Variants', vkey))
        if not got:
            bad.append(f'{vkey} is not on the worksheet')
            continue
        want = dict(product=remembered('Products', pkey), internal_reference=ref, barcode=barcode,
                    cost=cost, active=active)
        diffs = differences(got, want)
        if diffs:
            bad.append(f'{vkey}: {json.dumps(diffs, ensure_ascii=False, default=str)}')
    print(f'  {len(variant_specs())} variants in the dataset, {len(live)} on the worksheet'
          + (f', {wrote} written this run' if wrote is not None else ''))
    return fail('variants', bad)


# ── 8 · Orders ──────────────────────────────────────────────────────────────

# Never written: the Number is minted by the auto-number control and the three amounts are 汇总 over the
# subtable. The Signature is written separately, last, and only on a Sales Order.
ORDER_ROLLED_UP = ('untaxed', 'tax', 'total')
SIGNATURE_SOURCE = 'Orders: signature image'      # the ids.json key holding the image the signed orders reuse


def order_state(d):
    f = controls('Orders')
    return dict(
        number=t(d, f, 'Number'), status=opt(d, f, 'Status'),
        customer=one_name(d, f, 'Customer'), customer_id=one_id(d, f, 'Customer'),
        invoice_address=one_name(d, f, 'Invoice Address'),
        delivery_address=one_name(d, f, 'Delivery Address'),
        date=stamp(d, f, 'Quotation/Order Date'), expiry=dateonly(d, f, 'Expiration'),
        delivery_date=stamp(d, f, 'Delivery Date'),
        invoice_status=opt(d, f, 'Invoice Status'), delivery_status=opt(d, f, 'Delivery Status'),
        payment_terms=one_name(d, f, 'Payment Terms'), locked=sw(d, f, 'Locked'),
        invoicing_closed=sw(d, f, 'Invoicing Closed'), is_template=sw(d, f, 'Is Template'),
        template_name=t(d, f, 'Template Name'), signature=t(d, f, 'Signature'),
        signed_by=t(d, f, 'Signed By'), signed_on=stamp(d, f, 'Signed On'),
        discount_type=opt(d, f, 'Discount Type'), discount_value=n(d, f, 'Discount Value'),
        tax_mode=opt(d, f, 'Tax Mode'), reference=t(d, f, 'Customer Reference'),
        incoterm=one_name(d, f, 'Incoterm'), incoterm_location=t(d, f, 'Incoterm Location'),
        source_document=t(d, f, 'Source Document'),
        online_signature=sw(d, f, 'Online Signature'), online_payment=sw(d, f, 'Online Payment'),
        untaxed=n(d, f, 'Untaxed Amount'), tax=n(d, f, 'Tax'), total=n(d, f, 'Total'))


def order_key_of(state):
    return state['template_name'] or state['reference']


def order_want(o, display_of, incoterm_of):
    return dict(
        status=o['status'],
        customer=display_of(o['customer']) if o['customer'] else '',
        invoice_address=display_of(o['invoice_address']) if o.get('invoice_address') else '',
        delivery_address=display_of(o['delivery_address']) if o.get('delivery_address') else '',
        date=moment(o['date_offset']),
        expiry=day(o['expiry_offset']) if o['expiry_offset'] is not None else '',
        delivery_date=moment(o['delivery_date_offset']) if o['delivery_date_offset'] is not None else '',
        invoice_status=o['invoice_status'], delivery_status=o['delivery_status'] or '',
        payment_terms=o['payment_terms'] or '',
        locked='1' if o['locked'] else '0', invoicing_closed='1' if o['invoicing_closed'] else '0',
        is_template='1' if o['is_template'] else '0', template_name=o['template_name'] or '',
        signed_by=o['signed']['by'] if o['signed'] else '',
        signed_on=moment(o['signed']['days'], '14:30:00') if o['signed'] else '',
        discount_type=o['discount_type'] or '', discount_value=round(float(o['discount_value'] or 0), 2),
        tax_mode=o['tax_mode'], reference='' if o['is_template'] else o['key'],
        incoterm=incoterm_of(o['incoterm']) if o['incoterm'] else '',
        incoterm_location=o['incoterm_location'] or '',
        source_document=o['source_document'] or '',
        online_signature='1' if o['online_signature'] else '0',
        online_payment='1' if o['online_payment'] else '0')


def signature_image():
    """The signature image the two signed demo orders reuse, from ids.json. Absent, the two carry Signed By and
    Signed On and no image, and the step says so."""
    return hap.ids().get('records', {}).get(SIGNATURE_SOURCE) or ''


def incoterms_by_code():
    """{code: (Display Name, rowid)} — demo.json names an Incoterm by its three-letter code."""
    f = controls('Incoterms')
    tid = title_control('Incoterms')['controlId']
    code = f['Code']['controlId']
    return {str(r.get(code) or ''): (str(r.get(tid) or ''), r['rowid'])
            for r in C.records(ws('Incoterms'), APP)}


def contact_display_map():
    live = all_rows('Contacts')
    f = controls('Contacts')
    out = {}
    for c in data()['contacts']:
        rowid = remembered('Contacts', c['key'])
        d = live.get(rowid)
        out[c['key']] = (rowid, t(d, f, 'Display Name') if d else '')
    return out


def step_orders():
    """The thirty-six orders, keyed on Customer Reference (a template on its Template Name).

    The Number is **not** written: it is an auto-number control, so the platform mints it and this step records
    what it minted under ids.json `numbers`. The three amounts are 汇总 over the Order Lines subtable and are
    written by nobody.

    The Signature is written **last, and only on an order that is already a Sales Order**: *Signed: confirm the
    order* fires when a Signature appears on a Quotation or a Quotation Sent order and confirms it, so a signed
    quotation cannot stay a quotation in this app."""
    f = controls('Orders')
    cid = lambda name: f[name]['controlId']
    contacts = contact_display_map()
    display_of = lambda key: contacts[key][1]
    terms, incoterms = titles('Payment Terms'), incoterms_by_code()
    live = {rowid: order_state(d) for rowid, d in all_rows('Orders').items()}
    image = signature_image()
    wrote, to_sign = 0, []
    for o in data()['orders']:
        want = order_want(o, display_of, lambda code: incoterms[code][0])
        rowid = remembered('Orders', o['key'])
        got = live.get(rowid)
        if not got:
            rowid = next((r for r, v in live.items() if order_key_of(v) == o['key']), None)
            got = live.get(rowid)
        if got and not differences(got, want):
            remember('Orders', o['key'], rowid)
            C.remember('numbers', KEY + o['key'], got['number'])
            if o['signed'] and image and got['signature'].split('?')[0] != image:
                to_sign.append((rowid, o))
            continue
        values = [
            {'id': cid('Status'), 'value': [option_key(f['Status'], o['status'])]},
            {'id': cid('Quotation/Order Date'), 'value': want['date']},
            {'id': cid('Invoice Status'), 'value': [option_key(f['Invoice Status'], o['invoice_status'])]},
            {'id': cid('Tax Mode'), 'value': [option_key(f['Tax Mode'], o['tax_mode'])]},
            {'id': cid('Salesperson'), 'value': [salesperson()]},
            {'id': cid('Locked'), 'value': want['locked']},
            {'id': cid('Invoicing Closed'), 'value': want['invoicing_closed']},
            {'id': cid('Is Template'), 'value': want['is_template']},
            {'id': cid('Template Name'), 'value': want['template_name']},
            {'id': cid('Customer Reference'), 'value': want['reference']},
            {'id': cid('Online Signature'), 'value': want['online_signature']},
            {'id': cid('Online Payment'), 'value': want['online_payment']},
            {'id': cid('Expiration'), 'value': want['expiry']},
            {'id': cid('Delivery Date'), 'value': want['delivery_date']},
            {'id': cid('Incoterm Location'), 'value': want['incoterm_location']},
            {'id': cid('Source Document'), 'value': want['source_document']},
            {'id': cid('Signed By'), 'value': want['signed_by']},
            {'id': cid('Signed On'), 'value': want['signed_on']},
            {'id': cid('Discount Value'), 'value': want['discount_value']},
            {'id': cid('Delivery Status'),
             'value': [option_key(f['Delivery Status'], o['delivery_status'])] if o['delivery_status']
                      else []},
            {'id': cid('Discount Type'),
             'value': [option_key(f['Discount Type'], o['discount_type'])] if o['discount_type'] else []},
            {'id': cid('Payment Terms'),
             'value': [terms[o['payment_terms']]] if o['payment_terms'] else []},
            {'id': cid('Incoterm'), 'value': [incoterms[o['incoterm']][1]] if o['incoterm'] else []},
        ]
        for key, control in (('customer', 'Customer'), ('invoice_address', 'Invoice Address'),
                             ('delivery_address', 'Delivery Address')):
            target = o.get(key)
            values.append({'id': cid(control), 'value': [contacts[target][0]] if target else []})
        rowid, how = write('Orders', rowid, values, o['key'])
        wrote += 1
        live[rowid] = order_state(row('Orders', rowid))
        print(f"  {how} {o['key']:<22} {live[rowid]['status']:<15} {live[rowid]['number']}: {rowid}")
        remember('Orders', o['key'], rowid)
        C.remember('numbers', KEY + o['key'], live[rowid]['number'])
        if o['signed'] and image:
            to_sign.append((rowid, o))
    for rowid, o in to_sign:
        state = order_state(row('Orders', rowid))
        if state['status'] != 'Sales Order':
            print(f"  {o['key']}: not signed — its Status is {state['status']!r}, and a Signature written "
                  'there would confirm the order; the image goes only on a Sales Order')
            continue
        hap.run('worksheet', 'record', 'update', ws('Orders'), rowid, '-a', APP, '--fields-json',
                json.dumps([{'id': cid('Signature'), 'value': image}], ensure_ascii=False))
        back = order_state(row('Orders', rowid))['signature']
        if back.split('?')[0] == image:
            print(f"  {o['key']}: Signature written and read back")
        elif back:
            print(f"  {o['key']}: the Signature stored something else — {back!r}")
        else:
            print(f"  {o['key']}: the Signature image did NOT store — Signed By and Signed On are set and "
                  'the image is left empty')
    if not image:
        print(f'  ids.json has no {SIGNATURE_SOURCE!r}, so the two signed orders carry Signed By and Signed '
              'On and no image')
    return orders_verify(wrote=wrote)


def orders_verify(wrote=None):
    contacts = contact_display_map()
    incoterms = incoterms_by_code()
    live = {rowid: order_state(d) for rowid, d in all_rows('Orders').items()}
    bad = []
    for o in data()['orders']:
        got = live.get(remembered('Orders', o['key']))
        if not got:
            bad.append(f"{o['key']} is not on the worksheet")
            continue
        want = order_want(o, lambda key: contacts[key][1], lambda code: incoterms[code][0])
        diffs = differences(got, want)
        if diffs:
            bad.append(f"{o['key']} ({got['number']}): "
                       f'{json.dumps(diffs, ensure_ascii=False, default=str)}')
    print(f"  {len(data()['orders'])} orders in the dataset, {len(live)} on the worksheet"
          + (f', {wrote} written this run' if wrote is not None else ''))
    return fail('orders', bad)


# ── 9 · Order Lines ─────────────────────────────────────────────────────────

def order_line_state(d):
    f = controls('Order Lines')
    return dict(order=one_id(d, f, 'Orders'), sequence=int(n(d, f, 'Sequence', 0)),
                kind=opt(d, f, 'Display Type'), product=one_id(d, f, 'Product'),
                description=t(d, f, 'Description'), quantity=n(d, f, 'Quantity'),
                unit=one_name(d, f, 'Unit'), price=n(d, f, 'Unit Price'), discount=n(d, f, 'Discount'),
                taxes=sorted(rel_names(d, f, 'Taxes')), delivered=n(d, f, 'Quantity Delivered'),
                invoiced=n(d, f, 'Quantity Invoiced'), subtotal=n(d, f, 'Subtotal'),
                total=n(d, f, 'Total'))


def variant_row(key):
    if key == 'DISCOUNT':
        got = hap.ids().get('records', {}).get('Product Variants: Discount')
        if not got:
            sys.exit('ids.json has no "Product Variants: Discount" — the Discount variant must exist')
        return got
    got = remembered('Product Variants', key)
    if not got:
        sys.exit(f'the variant {key} is not in ids.json — run `variants` first')
    return got


def delivered_for(o, l):
    """Quantity Delivered, so Delivery Status is not a label with nothing behind it: every product line of a
    fully delivered order, the first two of a partly delivered one, none anywhere else."""
    if l['kind'] != 'Product' or l['product'] == 'DISCOUNT':
        return 0.0
    if o['delivery_status'] == 'Fully Delivered':
        return round(float(l['quantity']), 2)
    if o['delivery_status'] == 'Partially Delivered' and l['sequence'] <= 20:
        return round(float(l['quantity']), 2)
    return 0.0


def invoiced_for(o, l):
    """Quantity Invoiced, so Invoice Status is not a label with nothing behind it."""
    if l['kind'] != 'Product' or l['product'] == 'DISCOUNT':
        return 0.0
    if o['invoice_status'] in ('Fully Invoiced', 'Upselling Opportunity'):
        return round(float(l['quantity']), 2)
    return 0.0


def order_line_want(o, l, order_row):
    product = l['kind'] == 'Product'
    return dict(order=order_row, sequence=l['sequence'], kind=l['kind'],
                product=variant_row(l['product']) if product else '',
                description=l['description'],
                quantity=round(float(l.get('quantity') or 0), 2) if product else 0.0,
                unit=(l.get('unit') or '') if product else '',
                price=round(float(l.get('price') or 0), 2) if product else 0.0,
                discount=round(float(l.get('discount') or 0), 2) if product else 0.0,
                taxes=sorted(l.get('taxes') or []) if product else [],
                delivered=delivered_for(o, l), invoiced=invoiced_for(o, l))


def step_orderlines():
    """Every order's lines, matched on (the order's rowid, Sequence) — never on its Number, which the platform
    mints and which a Section or a Note shares with its siblings.

    The Orders relation is written as the relation the subtable is built on, so the row shows inside its order
    straight away. Quantity Delivered and Quantity Invoiced are filled to agree with the order's own Delivery
    Status and Invoice Status, so no status label stands on nothing."""
    f = controls('Order Lines')
    cid = lambda name: f[name]['controlId']
    taxes, units = titles('Taxes'), titles('Units & Packagings')
    live = {}
    for rowid, d in all_rows('Order Lines').items():
        s = order_line_state(d)
        live[(s['order'], s['sequence'])] = (rowid, s)
    wrote = 0
    for o in data()['orders']:
        order_row = remembered('Orders', o['key'])
        if not order_row:
            sys.exit(f"the order {o['key']} is not in ids.json — run `orders` first")
        for l in o['lines']:
            want = order_line_want(o, l, order_row)
            rowid, got = live.get((order_row, l['sequence']), (None, None))
            if got and not differences(got, want):
                continue
            values = [
                {'id': cid('Orders'), 'value': [order_row]},
                {'id': cid('Sequence'), 'value': l['sequence']},
                {'id': cid('Display Type'), 'value': [option_key(f['Display Type'], l['kind'])]},
                {'id': cid('Description'), 'value': l['description']},
                {'id': cid('Quantity'), 'value': want['quantity']},
                {'id': cid('Unit Price'), 'value': want['price']},
                {'id': cid('Discount'), 'value': want['discount']},
                {'id': cid('Quantity Delivered'), 'value': want['delivered']},
                {'id': cid('Quantity Invoiced'), 'value': want['invoiced']},
                {'id': cid('Product'), 'value': [want['product']] if want['product'] else []},
                {'id': cid('Unit'), 'value': [units[l['unit']]] if want['unit'] else []},
                {'id': cid('Taxes'), 'value': [taxes[x] for x in want['taxes']]},
            ]
            rowid, how = write('Order Lines', rowid, values, f"{o['key']} line {l['sequence']}")
            wrote += 1
            live[(order_row, l['sequence'])] = (rowid, order_line_state(row('Order Lines', rowid)))
            print(f"  {how} {o['key']:<22} line {l['sequence']:<4} {l['description'][:44]}")
    return orderlines_verify(wrote=wrote)


def orderlines_verify(wrote=None):
    live = {}
    for rowid, d in all_rows('Order Lines').items():
        s = order_line_state(d)
        live[(s['order'], s['sequence'])] = s
    bad, wanted = [], 0
    for o in data()['orders']:
        order_row = remembered('Orders', o['key'])
        for l in o['lines']:
            wanted += 1
            got = live.get((order_row, l['sequence']))
            if not got:
                bad.append(f"{o['key']} line {l['sequence']} is not on the worksheet")
                continue
            diffs = differences(got, order_line_want(o, l, order_row))
            if diffs:
                bad.append(f"{o['key']} line {l['sequence']}: "
                           f'{json.dumps(diffs, ensure_ascii=False, default=str)}')
    print(f'  {wanted} order lines in the dataset, {len(live)} on the worksheet'
          + (f', {wrote} written this run' if wrote is not None else ''))
    return fail('order lines', bad)


# ── 10 · Invoices ───────────────────────────────────────────────────────────

CREDIT_NOTES = ('Customer Credit Note', 'Vendor Credit Note')
DRAFT_NUMBER = 'Draft'                            # what an unnumbered draft's Number holds
INVOICE_ROLLED_UP = ('untaxed', 'tax', 'total', 'residual')


def journal_info():
    """{Journal Name: (Sequence Prefix, Dedicated Credit Note Sequence, rowid)}."""
    f = controls('Journals')
    out = {}
    for rowid, d in all_rows('Journals').items():
        out[t(d, f, 'Journal Name')] = (t(d, f, 'Sequence Prefix'),
                                        sw(d, f, 'Dedicated Credit Note Sequence'), rowid)
    return out


def invoice_numbers(journals):
    """{invoice key: its Number} — the sequence Confirm would have minted, built here because the seed writes
    posted and cancelled documents straight in.

    `<prefix>/<year of the Accounting Date>/<n padded to five>`, with an `R` in front for a credit note on a
    journal that has a Dedicated Credit Note Sequence: Odoo's `sequence.mixin`, as `invoices.py numbering`
    reproduces it. Numbered documents are taken in Accounting Date order within each prefix and year, so the
    series reads the way it would have grown."""
    out, counters = {}, {}
    numbered = [i for i in data()['invoices'] if i['numbered']]
    for i in sorted(numbered, key=lambda x: (x['accounting_date_offset'], x['key'])):
        prefix, refund, _rowid = journals[i['journal']]
        head = ('R' if i['type'] in CREDIT_NOTES and refund == '1' else '') + prefix
        series = f'{head}/{day(i["accounting_date_offset"])[:4]}/'
        counters[series] = counters.get(series, 0) + 1
        out[i['key']] = f'{series}{counters[series]:05d}'
    for i in data()['invoices']:
        out.setdefault(i['key'], DRAFT_NUMBER)
    return out


def invoice_state(d):
    f = controls('Invoices')
    return dict(number=t(d, f, 'Number'), type=opt(d, f, 'Type'), status=opt(d, f, 'Status'),
                partner=one_name(d, f, 'Customer / Vendor'),
                delivery_address=one_name(d, f, 'Delivery Address'),
                invoice_date=dateonly(d, f, 'Invoice Date'), date=dateonly(d, f, 'Accounting Date'),
                due=dateonly(d, f, 'Due Date'), terms=one_name(d, f, 'Payment Terms'),
                journal=one_name(d, f, 'Journal'), tax_mode=opt(d, f, 'Tax mode'),
                reference=t(d, f, 'Customer Reference'),
                payment_reference=t(d, f, 'Payment Reference'),
                delivery_date=dateonly(d, f, 'Delivery Date'), auto_post=opt(d, f, 'Auto-post'),
                source_document=t(d, f, 'Source Document'),
                untaxed=n(d, f, 'Untaxed Amount'), tax=n(d, f, 'Tax'), total=n(d, f, 'Total'),
                residual=n(d, f, 'Amount Due'))


def invoice_want(i, display_of, numbers):
    """What a document should read as. A `None` means *the app owns it*: `invoices_verify` drops those from the
    comparison. A document that states no Payment Terms leaves **both** its Payment Terms and its Due Date to
    *Payment Terms follow the Customer / Vendor* and *Due Date follows the Payment Terms*."""
    app_owned = i['payment_terms'] is None
    return dict(number=numbers[i['key']], type=i['type'], status=i['status'],
                partner=display_of(i['partner']),
                delivery_address=display_of(i['delivery_address']) if i.get('delivery_address') else '',
                invoice_date=day(i['invoice_date_offset']), date=day(i['accounting_date_offset']),
                due=None if (app_owned or i['due_offset'] is None) else day(i['due_offset']),
                terms=None if app_owned else i['payment_terms'], journal=i['journal'],
                tax_mode=i['tax_mode'],
                reference=i['customer_reference'], payment_reference=i['payment_reference'] or '',
                delivery_date=(day(i['delivery_date_offset'])
                               if i['delivery_date_offset'] is not None else ''),
                auto_post='No', source_document='')


def step_invoices():
    """The twenty-eight documents, keyed on Customer Reference.

    The Number is built here the way Confirm would build it — see `invoice_numbers`; a draft carries the word
    "Draft". The Due Date is written where demo.json states one and **left to the app** where it does not:
    *Due Date follows the Payment Terms* and *Payment Terms follow the Customer / Vendor* own it, and one
    document in the dataset is there to show that. The four amounts are never written — *Roll the lines up into
    the invoice* owns them. A Cancelled document is seeded like any other: the rule that closes a posted or
    cancelled document for editing is an interaction rule, and an interaction rule is browser-side only."""
    f = controls('Invoices')
    cid = lambda name: f[name]['controlId']
    contacts = contact_display_map()
    display_of = lambda key: contacts[key][1]
    journals = journal_info()
    numbers = invoice_numbers(journals)
    terms = titles('Payment Terms')
    live = {rowid: invoice_state(d) for rowid, d in all_rows('Invoices').items()}
    wrote = 0
    for i in data()['invoices']:
        want = invoice_want(i, display_of, numbers)
        compare = {k: v for k, v in want.items() if v is not None}
        rowid = remembered('Invoices', i['key'])
        got = live.get(rowid)
        if not got:
            rowid = next((r for r, v in live.items() if v['reference'] == i['customer_reference']), None)
            got = live.get(rowid)
        if got and not differences(got, compare):
            remember('Invoices', i['key'], rowid)
            continue
        values = [
            {'id': cid('Number'), 'value': want['number']},
            {'id': cid('Type'), 'value': [option_key(f['Type'], i['type'])]},
            {'id': cid('Status'), 'value': [option_key(f['Status'], i['status'])]},
            {'id': cid('Customer / Vendor'), 'value': [contacts[i['partner']][0]]},
            {'id': cid('Invoice Date'), 'value': want['invoice_date']},
            {'id': cid('Accounting Date'), 'value': want['date']},
            {'id': cid('Journal'), 'value': [journals[i['journal']][2]]},
            {'id': cid('Tax mode'), 'value': [option_key(f['Tax mode'], i['tax_mode'])]},
            {'id': cid('Customer Reference'), 'value': want['reference']},
            {'id': cid('Payment Reference'), 'value': want['payment_reference']},
            {'id': cid('Salesperson'), 'value': [salesperson()]},
            {'id': cid('Auto-post'), 'value': [option_key(f['Auto-post'], 'No')]},
            {'id': cid('Delivery Date'), 'value': want['delivery_date']},
            {'id': cid('Delivery Address'),
             'value': [contacts[i['delivery_address']][0]] if i.get('delivery_address') else []},
        ]
        # a document that states no Payment Terms sends no Payment Terms cell at all: the automation fills it
        # from the customer on create, and sending an empty cell on a later run would clear what it wrote
        # without the automation firing again (it triggers on create and on a Customer change, nothing else)
        if i['payment_terms'] is not None:
            values.append({'id': cid('Payment Terms'),
                           'value': [terms[i['payment_terms']]] if i['payment_terms'] else []})
        if want['due'] is not None:
            values.append({'id': cid('Due Date'), 'value': want['due']})
        rowid, how = write('Invoices', rowid, values, i['key'])
        wrote += 1
        live[rowid] = invoice_state(row('Invoices', rowid))
        print(f"  {how} {i['key']:<22} {want['number']:<18} {i['type']:<22} {i['status']}: {rowid}")
        remember('Invoices', i['key'], rowid)
    return invoices_verify(wrote=wrote, settle=4)


def invoices_verify(wrote=None, settle=1):
    """Compare every document with demo.json. The Due Date is compared only where demo.json states one, and
    the four amounts never. `settle` re-reads while the Due Date automations are still landing."""
    contacts = contact_display_map()
    numbers = invoice_numbers(journal_info())
    live, bad = {}, []
    for attempt in range(max(settle, 1)):
        live = {rowid: invoice_state(d) for rowid, d in all_rows('Invoices').items()}
        bad = []
        for i in data()['invoices']:
            got = live.get(remembered('Invoices', i['key']))
            if not got:
                bad.append(f"{i['key']} is not on the worksheet")
                continue
            want = {k: v for k, v in invoice_want(i, lambda key: contacts[key][1], numbers).items()
                    if v is not None}
            diffs = differences(got, want)
            if diffs:
                bad.append(f"{i['key']} ({got['number']}): "
                           f'{json.dumps(diffs, ensure_ascii=False, default=str)}')
        if not bad or attempt == max(settle, 1) - 1:
            break
        time.sleep(4)
    print(f"  {len(data()['invoices'])} documents in the dataset, {len(live)} on the worksheet"
          + (f', {wrote} written this run' if wrote is not None else ''))
    for i in data()['invoices']:
        if i['payment_terms'] is not None and i['due_offset'] is not None:
            continue
        got = live.get(remembered('Invoices', i['key'])) or {}
        print(f"  {i['key']}: left to the app — Payment Terms {got.get('terms', '—')!r}, "
              f"Due Date {got.get('due', '—')!r}")
    return fail('invoices', bad)


# ── 11 · Invoice Lines ──────────────────────────────────────────────────────

def invoice_line_state(d):
    f = controls('Invoice Lines')
    return dict(invoice=one_id(d, f, 'Invoice'), sequence=int(n(d, f, 'Sequence', 0)),
                kind=opt(d, f, 'Display Type'), product=one_id(d, f, 'Product'),
                label=t(d, f, 'Label'), account=one_name(d, f, 'Account'),
                quantity=n(d, f, 'Quantity'), unit=one_name(d, f, 'Unit'),
                price=n(d, f, 'Unit Price'), discount=n(d, f, 'Discount (%)'),
                taxes=sorted(rel_names(d, f, 'Taxes')), subtotal=n(d, f, 'Subtotal'),
                total=n(d, f, 'Total'))


def invoice_line_want(l, invoice_row):
    product = l['kind'] == 'Product'
    return dict(invoice=invoice_row, sequence=l['sequence'], kind=l['kind'],
                product=variant_row(l['product']) if product else '', label=l['label'],
                quantity=round(float(l.get('quantity') or 0), 2) if product else 0.0,
                unit=(l.get('unit') or '') if product else '',
                price=round(float(l.get('price') or 0), 2) if product else 0.0,
                discount=round(float(l.get('discount') or 0), 2) if product else 0.0,
                taxes=sorted(l.get('taxes') or []) if product else [])


def settle_line_taxes(seconds=40):
    """Wait for the line automations to land, then put right whatever they left different.

    *fill the account of a new line* and the tax automation are worksheet-event workflows: they run **after**
    the save, so the Taxes a create sends can be overwritten a second later (invlines.settle_taxes). Every
    product line is polled together rather than one at a time, so the whole set settles in one wait instead of
    one per line."""
    f = controls('Invoice Lines')
    taxes = titles('Taxes')
    wanted = {}
    for i in data()['invoices']:
        invoice_row = remembered('Invoices', i['key'])
        for l in i['lines']:
            if l['kind'] == 'Product':
                wanted[(invoice_row, l['sequence'])] = (f"{i['key']} line {l['sequence']}",
                                                        sorted(l.get('taxes') or []))
    stragglers = {}
    for _ in range(max(seconds // 3, 1)):
        live = {}
        for rowid, d in all_rows('Invoice Lines').items():
            s = invoice_line_state(d)
            live[(s['invoice'], s['sequence'])] = (rowid, s)
        stragglers = {k: v for k, v in wanted.items()
                      if k in live and live[k][1]['taxes'] != v[1]}
        if not stragglers:
            print(f'  every one of the {len(wanted)} product lines carries the taxes the dataset states')
            return 0
        time.sleep(3)
    for k, (label, want) in stragglers.items():
        rowid = live[k][0]
        hap.run('worksheet', 'record', 'update', ws('Invoice Lines'), rowid, '-a', APP, '--fields-json',
                json.dumps([{'id': f['Taxes']['controlId'], 'value': [taxes[x] for x in want]}]))
        got = invoice_line_state(row('Invoice Lines', rowid))['taxes']
        if got != want:
            sys.exit(f'{label}: Taxes read back {got}, want {want}')
        print(f'  {label}: Taxes written by hand ({want})')
    return 0


def step_invlines():
    """Every document's lines, matched on (the document's rowid, Sequence) — never on its Number, because a
    draft's Number is the word "Draft" and a Number-keyed index would merge every draft into one.

    The Account is **not written**: *fill the account of a new line* fills it from the product or its category.
    The Taxes are written and then settled against the same automation, which fills a product line's taxes from
    the product a moment after the row is saved."""
    f = controls('Invoice Lines')
    cid = lambda name: f[name]['controlId']
    taxes, units = titles('Taxes'), titles('Units & Packagings')
    live = {}
    for rowid, d in all_rows('Invoice Lines').items():
        s = invoice_line_state(d)
        live[(s['invoice'], s['sequence'])] = (rowid, s)
    wrote = 0
    for i in data()['invoices']:
        invoice_row = remembered('Invoices', i['key'])
        if not invoice_row:
            sys.exit(f"the document {i['key']} is not in ids.json — run `invoices` first")
        for l in i['lines']:
            want = invoice_line_want(l, invoice_row)
            rowid, got = live.get((invoice_row, l['sequence']), (None, None))
            if got and not differences({k: v for k, v in got.items() if k != 'account'}, want):
                continue
            values = [
                {'id': cid('Invoice'), 'value': [invoice_row]},
                {'id': cid('Sequence'), 'value': l['sequence']},
                {'id': cid('Display Type'), 'value': [option_key(f['Display Type'], l['kind'])]},
                {'id': cid('Label'), 'value': l['label']},
                {'id': cid('Quantity'), 'value': want['quantity']},
                {'id': cid('Unit Price'), 'value': want['price']},
                {'id': cid('Discount (%)'), 'value': want['discount']},
                {'id': cid('Product'), 'value': [want['product']] if want['product'] else []},
                {'id': cid('Unit'), 'value': [units[l['unit']]] if want['unit'] else []},
                {'id': cid('Taxes'), 'value': [taxes[x] for x in want['taxes']]},
            ]
            rowid, how = write('Invoice Lines', rowid, values, f"{i['key']} line {l['sequence']}")
            wrote += 1
            live[(invoice_row, l['sequence'])] = (rowid, invoice_line_state(row('Invoice Lines', rowid)))
            print(f"  {how} {i['key']:<22} line {l['sequence']:<4} {l['label'][:44]}")
    settle_line_taxes()
    return invlines_verify(wrote=wrote)


def invlines_verify(wrote=None):
    live = {}
    for rowid, d in all_rows('Invoice Lines').items():
        s = invoice_line_state(d)
        live[(s['invoice'], s['sequence'])] = s
    bad, wanted, no_account = [], 0, []
    for i in data()['invoices']:
        invoice_row = remembered('Invoices', i['key'])
        for l in i['lines']:
            wanted += 1
            got = live.get((invoice_row, l['sequence']))
            if not got:
                bad.append(f"{i['key']} line {l['sequence']} is not on the worksheet")
                continue
            diffs = differences({k: v for k, v in got.items() if k != 'account'},
                                invoice_line_want(l, invoice_row))
            if diffs:
                bad.append(f"{i['key']} line {l['sequence']}: "
                           f'{json.dumps(diffs, ensure_ascii=False, default=str)}')
            if l['kind'] == 'Product' and not got['account']:
                no_account.append(f"{i['key']} line {l['sequence']}")
    print(f'  {wanted} invoice lines in the dataset, {len(live)} on the worksheet'
          + (f', {wrote} written this run' if wrote is not None else ''))
    if no_account:
        print(f'  {len(no_account)} product line(s) carry no Account — the account automation fills it a '
              f'moment after the write: {no_account[:5]}')
    return fail('invoice lines', bad)


# ── 12 · plan ───────────────────────────────────────────────────────────────

def resolve_references():
    """Every configuration record demo.json points at, resolved against the live app."""
    gaps = []
    terms, states, countries = titles('Payment Terms'), titles('States'), titles('Countries')
    short_states = {x.split(' (')[0] for x in states}
    taxes, units, cats = titles('Taxes'), titles('Units & Packagings'), titles('Product Categories')
    incoterms, journals = incoterms_by_code(), journal_info()
    for c in data()['contacts']:
        for value, pool, what in ((c.get('state'), short_states, 'state'),
                                  (c.get('country'), set(countries), 'country'),
                                  (c.get('customer_terms'), set(terms), 'payment term'),
                                  (c.get('vendor_terms'), set(terms), 'payment term')):
            if value and value not in pool:
                gaps.append(f"contact {c['key']}: {what} {value!r} is not in the app")
    for p in data()['products']:
        if p['unit'] not in units:
            gaps.append(f"product {p['key']}: unit {p['unit']!r} is not in Units & Packagings")
        if p['category'] not in cats:
            gaps.append(f"product {p['key']}: category {p['category']!r} is not in Product Categories")
        for x in p['sales_taxes'] + p['purchase_taxes']:
            if x not in taxes:
                gaps.append(f"product {p['key']}: tax {x!r} is not in Taxes")
    for o in data()['orders']:
        if o['payment_terms'] and o['payment_terms'] not in terms:
            gaps.append(f"order {o['key']}: payment term {o['payment_terms']!r} is not in the app")
        if o['incoterm'] and o['incoterm'] not in incoterms:
            gaps.append(f"order {o['key']}: incoterm {o['incoterm']!r} is not in Incoterms")
        for l in o['lines']:
            for x in l.get('taxes') or []:
                if x not in taxes:
                    gaps.append(f"order {o['key']} line {l['sequence']}: tax {x!r} is not in Taxes")
            if l.get('unit') and l['unit'] not in units:
                gaps.append(f"order {o['key']} line {l['sequence']}: unit {l['unit']!r} is not in the app")
    for i in data()['invoices']:
        if i['journal'] not in journals:
            gaps.append(f"invoice {i['key']}: journal {i['journal']!r} is not in Journals")
        if i['payment_terms'] and i['payment_terms'] not in terms:
            gaps.append(f"invoice {i['key']}: payment term {i['payment_terms']!r} is not in the app")
        for l in i['lines']:
            for x in l.get('taxes') or []:
                if x not in taxes:
                    gaps.append(f"invoice {i['key']} line {l['sequence']}: tax {x!r} is not in Taxes")
            if l.get('unit') and l['unit'] not in units:
                gaps.append(f"invoice {i['key']} line {l['sequence']}: unit {l['unit']!r} is not in the app")
    return gaps


def creations():
    """{worksheet: how many records the seed would write}."""
    d = data()
    return {'Contact Tags': len(d['tags']), 'Contacts': len(d['contacts']),
            'Products': len(d['products']), 'Product Variants': len(variant_specs()),
            'Orders': len(d['orders']),
            'Order Lines': sum(len(o['lines']) for o in d['orders']),
            'Invoices': len(d['invoices']),
            'Invoice Lines': sum(len(i['lines']) for i in d['invoices'])}


def step_plan():
    """The dry run. Reads the live app, resolves every reference demo.json makes, and prints what `wipe` would
    delete and what the seed steps would create, per worksheet. **Writes nothing at all** — no record, no id,
    no backup file."""
    print(f'  demo.json: {os.path.getsize(DATA_PATH)} bytes; the seeding day would be {TODAY}, and every '
          'date in it is an offset from that day')
    gaps = resolve_references()
    if gaps:
        print(f'  {len(gaps)} reference(s) demo.json makes are not in the app:')
        for g in gaps:
            print(f'    {g}')
    else:
        print('  every configuration record demo.json points at resolves to exactly one live record')
    planned, make = deletions(), creations()
    print(f'\n  {"worksheet":<20} {"live":>6} {"delete":>7} {"kept":>6} {"create":>7}')
    totals = [0, 0, 0]
    for name in WIPE_ORDER:
        live = len(rowid_list(name))
        gone = len(planned[name])
        new = make.get(name, 0)
        totals = [totals[0] + live, totals[1] + gone, totals[2] + new]
        print(f'  {name:<20} {live:>6} {gone:>7} {live - gone:>6} {new:>7}'
              + ('' if name in REBUILT else '   configuration: only its test leftovers'))
    print(f'  {"":<20} {totals[0]:>6} {totals[1]:>7} {"":>6} {totals[2]:>7}')
    print(f'\n  kept through the wipe: {sorted(keep_ids())} — the Discount product and its variant')
    print('  the rows named for deletion in the configuration worksheets:')
    for name in CONFIG:
        if planned[name]:
            print(f'    {name}: ' + ', '.join(repr(i) for _r, i in planned[name]))
    orders, invoices = data()['orders'], data()['invoices']
    print('\n  what the demo would hold:')
    print(f"    orders by Status: {dict(Counter(o['status'] for o in orders))}")
    print(f"    of them templates {sum(1 for o in orders if o['is_template'])}, "
          f"locked {sum(1 for o in orders if o['locked'])}, "
          f"invoicing closed {sum(1 for o in orders if o['invoicing_closed'])}, "
          f"signed {sum(1 for o in orders if o['signed'])}")
    print(f"    Sales Orders by Invoice Status: "
          f"{dict(Counter(o['invoice_status'] for o in orders if o['status'] == 'Sales Order'))}")
    print(f"    Sales Orders by Delivery Status: "
          f"{dict(Counter(o['delivery_status'] for o in orders if o['delivery_status']))}")
    open_quotes = [o for o in orders if o['status'].startswith('Quotation') and not o['is_template']]
    print(f"    open quotations expiring within 7 days: "
          f"{sorted(o['key'] for o in open_quotes if 0 <= (o['expiry_offset'] or 0) <= 7)}")
    print(f"    open quotations already expired: "
          f"{sorted(o['key'] for o in open_quotes if (o['expiry_offset'] or 0) < 0)}")
    print(f"    orders carrying discount lines: "
          f"{sorted((o['key'], o['discount_type'], o['discount_value']) for o in orders if o['discount_type'])}")
    print(f"    orders with an Incoterm: "
          f"{sorted((o['key'], o['incoterm']) for o in orders if o['incoterm'])}")
    print(f"    orders with a Section or a Note line: "
          f"{sorted(o['key'] for o in orders if any(l['kind'] != 'Product' for l in o['lines']))}")
    print(f"    orders marked to be invoiced once the order -> invoice link exists: "
          f"{sorted(o['key'] for o in orders if o['to_invoice_later'])}")
    print(f"    documents by Type/Status: {dict(Counter((i['type'], i['status']) for i in invoices))}")
    overdue = [i for i in invoices if i['status'] == 'Posted' and i['due_offset'] is not None
               and -60 <= i['due_offset'] < 0]
    print(f"    posted documents overdue on the demo day (due in the last 60 days): "
          f"{sorted((i['key'], i['due_offset']) for i in overdue)}")
    print(f"    documents whose Due Date is left to the app: "
          f"{sorted(i['key'] for i in invoices if i['due_offset'] is None)}")
    print('    the Number each numbered document would take: '
          + ', '.join(f'{k}={v}' for k, v in sorted(invoice_numbers(journal_info()).items())
                      if v != DRAFT_NUMBER))
    print(f"\n  auto-numbered worksheets among those wiped: Orders (Number, a type-33 auto-number) and no "
          "other. Reset it in the browser between `wipe` and `orders`.")
    image = signature_image()
    print('  the signature image the two signed orders would reuse: '
          + (image[:70] + '…' if image
             else f'not in ids.json under {SIGNATURE_SOURCE!r} — they would carry Signed By and Signed On '
                  'and no image'))
    print('  nothing was written: `plan` makes no change of any kind')
    return 0


# ── 13 · check ──────────────────────────────────────────────────────────────

def view_rows(name, view_name):
    live = {v['name']: v['viewId'] for v in hap.listing('worksheet', 'view', 'list', ws(name), '-a', APP)}
    if view_name not in live:
        return None
    res = hap.run('worksheet', 'record', 'list', ws(name), '-a', APP, '-n', '500',
                  '--view-id', live[view_name], '--use-field-id-as-key')
    d = res.get('data', res) if isinstance(res, dict) else res
    return (d.get('rows') if isinstance(d, dict) else d) or []


def step_check():
    """Read the whole dataset back and print the figures: the counts, the buckets, the views, the overdue
    documents, and every document's own arithmetic."""
    problems = []
    make = creations()
    print('── records ' + '─' * 58)
    for name in REBUILT:
        live = len(rowid_list(name))
        kept = 1 if name in ('Products', 'Product Variants') else 0
        want = make[name] + kept
        print(f'  {name:<20} {live:>5} records (the dataset asks for {make[name]}'
              + (' + the Discount product it keeps' if kept else '') + ')')
        if live != want:
            problems.append(f'{name} holds {live} records, expected {want}')

    print('\n── the dataset, field by field ' + '─' * 38)
    for label, fn in (('tags', tags_verify), ('contacts', contacts_verify), ('products', products_verify),
                      ('variants', variants_verify), ('orders', orders_verify),
                      ('order lines', orderlines_verify), ('invoices', invoices_verify),
                      ('invoice lines', invlines_verify)):
        print(f'  {label}:')
        fn()

    print('\n── orders ' + '─' * 59)
    live = {rowid: order_state(d) for rowid, d in all_rows('Orders').items()}
    mine = {o['key']: live[remembered('Orders', o['key'])] for o in data()['orders']
            if remembered('Orders', o['key']) in live}
    print(f"  by Status: {dict(Counter(v['status'] for v in mine.values()))}")
    print(f"  templates {sum(1 for v in mine.values() if v['is_template'] == '1')}, "
          f"locked {sum(1 for v in mine.values() if v['locked'] == '1')}, "
          f"invoicing closed {sum(1 for v in mine.values() if v['invoicing_closed'] == '1')}, "
          f"with a signature image {sum(1 for v in mine.values() if v['signature'])}, "
          f"with Signed By {sum(1 for v in mine.values() if v['signed_by'])}")
    print(f"  Sales Orders by Invoice Status: "
          f"{dict(Counter(v['invoice_status'] for v in mine.values() if v['status'] == 'Sales Order'))}")
    print(f"  Sales Orders by Delivery Status: "
          f"{dict(Counter(v['delivery_status'] for v in mine.values() if v['status'] == 'Sales Order'))}")
    today, week = TODAY.isoformat(), (TODAY + datetime.timedelta(days=7)).isoformat()
    quotes = [v for v in mine.values() if v['status'].startswith('Quotation') and v['is_template'] == '0']
    print(f"  quotations expiring within the week: "
          f"{sorted(v['number'] for v in quotes if today <= v['expiry'] <= week)}")
    print(f"  quotations already expired: "
          f"{sorted(v['number'] for v in quotes if v['expiry'] and v['expiry'] < today)}")
    numbers = sorted(v['number'] for v in mine.values())
    print(f'  the Numbers the auto-number minted: {numbers[0]} … {numbers[-1]} ({len(numbers)} of them)')
    lines = [order_line_state(d) for d in all_rows('Order Lines').values()]
    for key, v in sorted(mine.items()):
        rowid = remembered('Orders', key)
        own = [l for l in lines if l['order'] == rowid and l['kind'] == 'Product']
        untaxed = round(sum(l['subtotal'] for l in own), 2)
        if abs(untaxed - v['untaxed']) > 0.01:
            problems.append(f"{key} ({v['number']}): Untaxed Amount {v['untaxed']} against its lines' "
                            f'{untaxed}')
    print("  every order's Untaxed Amount against the sum of its own lines: "
          + ('all agree' if not problems else 'see the differences at the end'))

    print('\n── invoices ' + '─' * 57)
    ilive = {rowid: invoice_state(d) for rowid, d in all_rows('Invoices').items()}
    docs = {i['key']: ilive[remembered('Invoices', i['key'])] for i in data()['invoices']
            if remembered('Invoices', i['key']) in ilive}
    print(f"  by Type/Status: {dict(Counter((v['type'], v['status']) for v in docs.values()))}")
    overdue = sorted((v for v in docs.values()
                      if v['status'] == 'Posted' and v['due'] and v['due'] < today and v['residual'] > 0),
                     key=lambda v: v['due'])
    print(f'  overdue on {today} ({len(overdue)}): '
          + ', '.join(f"{v['number']} due {v['due']} RM {v['residual']:,.2f}" for v in overdue))
    print(f"  drafts whose Number reads {DRAFT_NUMBER!r}: "
          f"{sum(1 for v in docs.values() if v['number'] == DRAFT_NUMBER)}")
    print(f"  credit notes: {sorted(v['number'] for v in docs.values() if v['type'] in CREDIT_NOTES)}")
    print(f"  vendor bills: {sorted(v['number'] for v in docs.values() if v['type'] == 'Vendor Bill')}")
    ilines = [invoice_line_state(d) for d in all_rows('Invoice Lines').values()]
    stale = []
    for key, v in sorted(docs.items()):
        rowid = remembered('Invoices', key)
        own = [l for l in ilines if l['invoice'] == rowid and l['kind'] == 'Product']
        untaxed = round(sum(l['subtotal'] for l in own), 2)
        total = round(sum(l['total'] for l in own), 2)
        if abs(untaxed - v['untaxed']) > 0.01 or abs(total - v['total']) > 0.01:
            stale.append(f"{key} ({v['number']}): Untaxed {v['untaxed']} / Total {v['total']} against its "
                         f"lines' {untaxed} / {total}")
    problems += stale
    print("  every document's amounts against the sum of its own lines: "
          + ('all agree' if not stale else f'{len(stale)} out of step — the roll-up has not caught up'))

    print('\n── views ' + '─' * 60)
    for name, views in (('Orders', ('Quotations', 'Orders', 'Templates')),
                        ('Invoices', ('Invoices', 'Bills', 'Journal Entries'))):
        for v in views:
            rows = view_rows(name, v)
            if rows is None:
                problems.append(f'{name}: the view {v!r} is gone')
                continue
            print(f'  {name:<10} {v:<16} {len(rows):>4} rows')
            if not rows and v != 'Journal Entries':
                problems.append(f'{name}: the view {v!r} is empty')

    print('\n── check ' + '─' * 60)
    if problems:
        print('  DIFFERENCES\n    ' + '\n    '.join(problems))
    else:
        print('  OK — every record, every bucket and every view as demo.json states it')
    return len(problems)


# ── 14 · the whole seed ─────────────────────────────────────────────────────

SEED_STEPS = ('tags', 'contacts', 'products', 'variants', 'orders', 'orderlines', 'invoices', 'invlines')


def step_seed():
    for name in SEED_STEPS:
        print(f'\n── {name} ' + '─' * 60)
        STEPS[name]()
    print('\n── check ' + '─' * 60)
    return step_check()


def step_show():
    """The dataset as demo.json states it. Makes no call to the app."""
    d = data()
    for line in d['_note']:
        print(f'  {line}\n')
    print(f"  {d['company']} — {d['country']}, {d['currency']}\n")
    for name, count in creations().items():
        print(f'  {name:<20} {count:>5}')
    print('\n  products:')
    for p in d['products']:
        refs = ', '.join(v['internal_reference'] for v in p['variants']) or p['internal_reference']
        print(f"    {p['key']:<12} {p['name']:<20} {p['group']:<18} {p['category']:<24} "
              f"RM {p['list_price']:>9,.2f}  {'' if p['active'] else 'ARCHIVED  '}{refs}")
    print('\n  orders:')
    for o in d['orders']:
        print(f"    {o['key']:<22} {o['status']:<15} day{o['date_offset']:>5} "
              f"exp{('' if o['expiry_offset'] is None else o['expiry_offset']):>5}  "
              f"{len(o['lines'])} lines  {o['demonstrates']}")
    print('\n  documents:')
    for i in d['invoices']:
        print(f"    {i['key']:<22} {i['type']:<22} {i['status']:<10} day{i['invoice_date_offset']:>5} "
              f"due{('auto' if i['due_offset'] is None else i['due_offset']):>6}  "
              f"{len(i['lines'])} lines  {i['demonstrates']}")
    return 0


STEPS = {
    'plan': step_plan,
    'backup': step_backup,
    'wipe': step_wipe,
    'tags': step_tags,
    'contacts': step_contacts,
    'products': step_products,
    'variants': step_variants,
    'orders': step_orders,
    'orderlines': step_orderlines,
    'invoices': step_invoices,
    'invlines': step_invlines,
    'seed': step_seed,
    'check': step_check,
    'show': step_show,
}

if __name__ == '__main__':
    step = sys.argv[1] if len(sys.argv) > 1 else 'plan'
    if step not in STEPS:
        raise SystemExit(f"Unknown step {step!r}; choose from {', '.join(STEPS)}")
    if STEPS[step](*sys.argv[2:]):
        sys.exit(1)
