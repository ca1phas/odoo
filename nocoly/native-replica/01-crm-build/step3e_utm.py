"""CRM Phase A, step 3e: unique UTM names (01-crm.md §4 L13; Odoo utm.mixin._get_unique_names).

Odoo gives a repeated medium, source or campaign identifier the smallest free counter: "Email", "Email [2]",
"Email [3]"... instead of refusing it, and computes a campaign's identifier from its name (title).
Here each flow tries the name, then " [2]" ... " [5]", and keeps the first one no other record has. With five
records of one name already, the name is left as typed (limit noted in BUILD-LOG). Odoo refuses a duplicate typed
on an existing record (database constraint); these flows rename it the same way instead.

  U1 UTM - Unique medium name                  Mediums, name set or changed
  U2 UTM - Unique source name                  Sources, name set or changed
  U3 UTM - Campaign identifier                 Campaigns, created: identifier = typed identifier, else the name
  U4 UTM - Campaign identifier from the name   Campaigns, name (title) changed: identifier recomputed from it
Run: python step3e_utm.py u1 u2 u3 u4
"""
import json, sys
from crmwf import *  # noqa: F401,F403
from step3_wf_core import build, done

STEP = 'crm step 3e'
TRIES = 5


def chain(sheet, k=1, write_first=False):
    """Try candidate k; if another record has it, try k+1 (nested in the no-data path)."""
    name_f = F(sheet, 'name')
    cand = f'c{k}'
    q = f'q{k}'
    formula = '$b-string_fx_id$' if k == 1 else f'CONCAT($b-string_fx_id$, " [{k}]")'
    write = [upd(f'w{k}', f'Name {"as typed" if k == 1 else f"with [{k}]"}', [{'fieldId': name_f, 'value': ref(cand, 'string_fx_id')}],
                 sheet=sheet)] if (k > 1 or write_first) else []
    taken = chain(sheet, k + 1, write_first) if k < TRIES else []
    return [
        {'nodeAlias': cand, 'nodeType': 'compute', 'name': f'Candidate {k}', 'config': {'mode': 'function', 'output_type': 'text', 'formula': formula}},
        single(q, f'Another record named like candidate {k}', sheet,
               [fi(q, name_f, 'eq', fref(cand, 'string_fx_id')), fi(q, 'rowid', 'ne', fref('trigger', 'rowid'), 2)]),
        branch(f'r{k}', f'Candidate {k} free?', [
            path(f'f{k}', 'Free', write, result_type='no_data'),
            path(f't{k}', 'Taken', taken, result_type='has_data')], result=True)]


def flow(name, sheet, desc, base_formula, *trigger, write_first=False):
    nodes = [{'nodeAlias': 'b', 'nodeType': 'compute', 'name': 'Name asked for',
              'config': {'mode': 'function', 'output_type': 'text', 'formula': base_formula}}] + chain(sheet, 1, write_first)
    pid, new = build(name, desc, nodes, '--trigger-worksheet', S[sheet], *trigger, module='utm')
    return done(pid, name)


def u1():
    return flow('UTM - Unique medium name', 'utm_medium', 'A medium name another medium has gets " [2]", " [3]"... (Odoo _get_unique_names).',
                f"$trigger-{F('utm_medium', 'name')}$", '--trigger-event', 'create_or_update', '--trigger-fields', F('utm_medium', 'name'),
                '--trigger-filter', json.dumps({'logic': 'and', 'items': [cond('trigger', F('utm_medium', 'name'), 'not_empty')]}))


def u2():
    return flow('UTM - Unique source name', 'utm_source', 'A source name another source has gets " [2]", " [3]"... (Odoo _get_unique_names).',
                f"$trigger-{F('utm_source', 'name')}$", '--trigger-event', 'create_or_update', '--trigger-fields', F('utm_source', 'name'),
                '--trigger-filter', json.dumps({'logic': 'and', 'items': [cond('trigger', F('utm_source', 'name'), 'not_empty')]}))


def u3():
    c = lambda f: F('utm_campaign', f)
    return flow('UTM - Campaign identifier', 'utm_campaign',
                'New campaign: identifier = the typed identifier, else the campaign name, made unique with " [2]"... (Odoo create, _compute_name).',
                f"IF(ISBLANK($trigger-{c('name')}$), $trigger-{c('title')}$, $trigger-{c('name')}$)",
                '--trigger-event', 'create', write_first=True)


def u4():
    c = lambda f: F('utm_campaign', f)
    return flow('UTM - Campaign identifier from the name', 'utm_campaign',
                'Campaign name changed: the identifier is recomputed from it, made unique (Odoo _compute_name on title).',
                f"$trigger-{c('title')}$", '--trigger-event', 'update', '--trigger-fields', c('title'), write_first=True)


if __name__ == '__main__':
    refresh()
    for name in sys.argv[1:]:
        globals()[name]()
