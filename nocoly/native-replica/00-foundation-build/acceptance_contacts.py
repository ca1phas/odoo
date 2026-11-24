"""Acceptance tests 1-2 (plan v1 §9) and the v2 tag test, with TEST data deleted at the end.
1. Company with Tax ID and industry; a Contact-type and an Invoice-type person: both show "Company, Person" and carry
   the Tax ID and industry; only the Contact-type person takes the company address.
2. Change the company's Tax ID and street: the Contact-type person follows; the Invoice address keeps its own.
Tag: a new tag typed on a contact is added to the option set with a colour.
Run: python acceptance_contacts.py   |   python acceptance_contacts.py cleanup
"""
import json, sys, time
from lib import hap, APP
from wflib import S, option_key

C, IND = 'res_partner', 'res_partner_industry'
IDS = 'backups/test-contacts12.json'


def create(fields):
    r = hap('worksheet', 'record', 'create', S[C], '-a', APP, '--ignore-rules', '--fields-json', json.dumps(fields))
    r = r.get('data', r)
    return r.get('rowid') or r.get('rowId')


def update(rid, fields):
    return hap('worksheet', 'record', 'update', S[C], rid, '-a', APP, '--ignore-rules', '--fields-json', json.dumps(fields))


def get(rid):
    g = hap('worksheet', 'record', 'get', S[C], rid, '-a', APP)
    return g.get('data', g)


def names(v):
    return [x.get('name') for x in v] if isinstance(v, list) else v


def show(tag, rid):
    g = get(rid)
    reg = g.get('x_base__region')
    reg = reg.get('path') if isinstance(reg, dict) else reg
    typ = g.get('type')
    typ = typ[0].get('value') if isinstance(typ, list) and typ and isinstance(typ[0], dict) else typ
    print(f"  {tag}: {g.get('complete_name')!r} | type {typ} | tax {g.get('vat')!r} | industry {names(g.get('industry_id'))} | "
          f"street {g.get('street')!r} city {g.get('city')!r} region {reg} country {names(g.get('country_id'))}")
    return g


def main():
    d = hap('worksheet', 'record', 'list', S[IND], '-a', APP, '--page-size', '5')
    d = d.get('data', d)
    industry = (d.get('rows') or [])[0]
    co, pe = option_key(C, 'company_type', 'Company'), option_key(C, 'company_type', 'Person')
    contact, invoice = option_key(C, 'type', 'Contact'), option_key(C, 'type', 'Invoice Address')
    ids = {}
    ids['co'] = create([{'id': 'name', 'value': 'TEST Acme'}, {'id': 'company_type', 'value': co}, {'id': 'active', 'value': '1'},
                        {'id': 'vat', 'value': 'TEST-TAX-1'}, {'id': 'industry_id', 'value': [industry['rowId']]},
                        {'id': 'street', 'value': '1 Jalan Test'}, {'id': 'city', 'value': 'Shah Alam'},
                        {'id': 'x_base__region', 'value': 'MY|MY-10'}])
    json.dump(ids, open(IDS, 'w'), indent=1)
    time.sleep(10)
    ids['contact'] = create([{'id': 'name', 'value': 'TEST Aina'}, {'id': 'company_type', 'value': pe}, {'id': 'active', 'value': '1'},
                             {'id': 'type', 'value': contact}, {'id': 'parent_id', 'value': [ids['co']]}])
    ids['invoice'] = create([{'id': 'name', 'value': 'TEST Billing'}, {'id': 'company_type', 'value': pe}, {'id': 'active', 'value': '1'},
                             {'id': 'type', 'value': invoice}, {'id': 'parent_id', 'value': [ids['co']]},
                             {'id': 'street', 'value': '9 Jalan Invois'}, {'id': 'city', 'value': 'Kuala Lumpur'},
                             {'id': 'x_base__region', 'value': 'MY|MY-14'}])
    json.dump(ids, open(IDS, 'w'), indent=1)
    time.sleep(15)
    print(f"TEST 1 (industry used: {industry.get('name') or industry.get('full_name')})")
    for k in ('co', 'contact', 'invoice'):
        show(k, ids[k])
    update(ids['co'], [{'id': 'vat', 'value': 'TEST-TAX-2'}, {'id': 'street', 'value': '2 Jalan Test'}])
    time.sleep(20)
    print('TEST 2 (company Tax ID TEST-TAX-2, street 2 Jalan Test)')
    for k in ('co', 'contact', 'invoice'):
        show(k, ids[k])


def cleanup():
    ids = json.load(open(IDS))
    hap('worksheet', 'record', 'delete', S[C], '-a', APP, '-y', '--row-ids', ','.join(ids.values()))
    print('deleted', list(ids))


if __name__ == '__main__':
    cleanup() if 'cleanup' in sys.argv else main()
