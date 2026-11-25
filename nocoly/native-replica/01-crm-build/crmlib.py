"""CRM build helpers: the wave 0 helpers (../00-foundation-build: lib, sheetlib, wflib, step9 layouts) with this
module's own ledger (01-crm-build/ids.json) and backups folder.

Import this module first in every CRM step script:  from crmlib import *
After creating sheets, call refresh() so wflib.S (sheet ids by alias) and the field-id cache see them.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
W0 = os.path.join(os.path.dirname(HERE), '00-foundation-build')
if W0 not in sys.path:
    sys.path.insert(0, W0)
os.makedirs(os.path.join(HERE, 'backups'), exist_ok=True)

import lib  # noqa: E402
lib.LEDGER = os.path.join(HERE, 'ids.json')   # record() writes here (the register reads every *-build/ids.json)
lib.HERE = HERE                                # backup() writes to 01-crm-build/backups
import sheetlib  # noqa: E402
sheetlib.HERE = HERE                           # temporary spec files
import wflib  # noqa: E402
wflib.HERE = HERE

from lib import hap, APP, unwrap, app_info, sections_flat, record, ledger, backup  # noqa: E402,F401
from sheetlib import (F as FS, ensure_sheet, ensure_reverse, raw_fields, apply_spec, sheets_by_alias, add_once,  # noqa: E402,F401
                      set_show, by_alias, HIDDEN)
from wflib import S, F, T, option_key, flows, find_flow, batch_add, node_ids, publish, cond, fld, lit  # noqa: E402,F401

ON = [{'source': 'static', 'value': '1'}]
ME = [{'source': 'system', 'value': 'currentUser'}]
AUTO = 'Kept up to date automatically.'
MYR = {'currency': '{"currencycode":"MYR","symbol":"RM"}', 'showformat': '1', 'roundtype': '2'}
# Odoo's tag colour index (1-11) -> its web palette
ODOO_COLOURS = {0: '#9E9E9E', 1: '#F06050', 2: '#F4A460', 3: '#F7CD1F', 4: '#6CC1ED', 5: '#814968', 6: '#EB7E7F',
                7: '#2C8397', 8: '#475577', 9: '#D6145F', 10: '#30C381', 11: '#9365B8'}


def refresh():
    """Re-read the sheet ids (new sheets) and drop the cached field ids."""
    S.clear()
    S.update({k: v['id'] for k, v in sheets_by_alias().items()})
    wflib._F.clear()
    return S


def money(name, alias, desc='', **kw):
    return FS(name, 'MONEY', alias, desc=desc, dot=2, advanced_setting=dict(MYR), **kw)


def optionset(name, options, module, step):
    """Option set by name (created once, with colours); returns (id, options as read)."""
    def find():
        d = hap('app', 'optionset', 'list', '-a', APP)
        sets = (d.get('data') or d).get('optionsets', []) if isinstance(d, dict) else d
        return next((s for s in sets or [] if s.get('name') == name), None)
    s = find()
    if not s:
        import json
        hap('app', 'optionset', 'create', '-a', APP, '--name', name, '--enable-color', '--options-json',
            json.dumps([{'value': v, 'index': i, 'color': c} for i, (v, c) in enumerate(options, 1)], ensure_ascii=False))
        s = find()
    record(s['id'], 'optionset', name, module, step)
    return s['id'], s.get('options') or []


def pair(ws, field_alias, target_ws, rev_alias, rev_name, module, step, showtype='6'):
    """Make a one-way relation two-way (pair-relation), then name the reverse side."""
    c = by_alias(ws)[field_alias]
    if not any(x['type'] == 29 and x.get('sourceControlId') == c['controlId'] for x in raw_fields(target_ws)):
        hap('worksheet', 'pair-relation', ws, c['controlId'], '--name', rev_name)
    return ensure_reverse(target_ws, c['controlId'], rev_alias, rev_name, module, showtype, step)
