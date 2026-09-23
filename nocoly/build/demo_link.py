"""Link the demo's customer invoices to the orders they bill, line by line (Invoice Lines' Sales Order Lines)."""
import sys, json, subprocess; sys.path.insert(0,'/home/cas/odoo/nocoly/build')
import common as C
APP='6cb4d051-a33c-4bf9-b56f-5f47f0e85dc9'
ids=json.load(open('/home/cas/odoo/nocoly/build/ids.json')); ws=ids['worksheets']; rec=ids['records']
PAIRS = {  # invoice key -> order key (the invoices mirror their orders by reference)
 'INV-SMBD-0418':'SMBD-PO-2025-0418','INV-PKK-4471':'PKK-PO-4471','INV-KMA-0093':'KMA-2025-0093',
 'INV-SRW-114':'SRW-PO-2025-114','INV-GGR-88231':'GGR-PO-88231','INV-JPNJ-007A':'JPNJ-T-2026-007',
 'INV-JPNJ-007B':'JPNJ-T-2026-007','INV-HPSC-0221':'HPSC-PO-2026-0221','INV-MPSP-0455':'MPSP-PO-2026-0455',
 'INV-NURUL-0044':'NURUL-2026-0044','INV-KTN-0119':'KTN-PO-2026-0119','INV-GGR-91104':'GGR-PO-91104'}
OL, IL = ws['Order Lines'], ws['Invoice Lines']
of, lf = C.fields(OL), C.fields(IL)
def rid(v):
    try: return [x.get('sid') or x.get('rowid') for x in json.loads(v)] if isinstance(v,str) and v.startswith('[') else (v or [])
    except Exception: return []
olines = C.records(OL, APP); ilines = C.records(IL, APP)
def prod(r, f): 
    v=r.get(f['Product']['controlId']); x=rid(v); return x[0] if x else None
def kind(r, f): return str(r.get(f['Display Type']['controlId']))
wrote = skipped = 0; unmatched = []
used = set()
for inv_key, ord_key in PAIRS.items():
    inv, order = rec[f'Demo: Invoices {inv_key}'], rec[f'Demo: Orders {ord_key}']
    mine_o = sorted([r for r in olines if order in str(r.get(of['Orders']['controlId'])) and 'Product' in kind(r,of)],
                    key=lambda r: float(r.get(of['Sequence']['controlId']) or 0))
    mine_i = sorted([r for r in ilines if inv in str(r.get(lf['Invoice']['controlId'])) and 'Product' in kind(r,lf)],
                    key=lambda r: float(r.get(lf['Sequence']['controlId']) or 0))
    for il in mine_i:
        p = prod(il, lf)
        match = next((ol for ol in mine_o if prod(ol, of) == p and (inv_key.endswith(('A','B')) or ol['rowid'] not in used)), None)
        if not match:
            unmatched.append(f'{inv_key}: a line with product {p} has no order line'); continue
        used.add(match['rowid'])
        have = rid(il.get(lf['Sales Order Lines']['controlId']))
        if have == [match['rowid']]:
            skipped += 1; continue
        r = subprocess.run(['/home/cas/.hap-venv/bin/hap','worksheet','record','update',IL,il['rowid'],'-a',APP,
                            '--fields-json',json.dumps([{'id':lf['Sales Order Lines']['controlId'],'value':[match['rowid']]}])],
                           capture_output=True, text=True)
        if r.returncode: sys.exit(r.stderr[-300:])
        wrote += 1
print(f'linked {wrote} invoice lines, {skipped} already linked')
print('unmatched:', unmatched or 'none')
