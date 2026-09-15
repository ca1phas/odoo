import re,glob,collections
CORE={'res.partner':'Contacts','uom.uom':'Units & Packagings','product.category':'Product Categories',
 'product.template':'Products','product.product':'Product Variants','account.account':'Chart of Accounts',
 'account.journal':'Journals','account.tax':'Taxes','account.payment.term':'Payment Terms',
 'account.payment.method':'Payment Methods','account.move':'Invoices','account.move.line':'Invoice Lines',
 'account.payment':'Payments','mail.activity.type':'Activity Types'}
CORE_MODS={'base','uom','product','account','mail','analytic'}
# find required=True Many2one fields pointing at each core model, declared in a core module
req=collections.defaultdict(list)
fld=re.compile(r"(\w+)\s*=\s*fields\.Many2one\((.{0,400}?)\)\s*\n", re.S)
for f in glob.glob('addons/*/models/*.py')+glob.glob('odoo/addons/base/models/*.py'):
    mod=f.split('/')[1] if f.startswith('addons/') else 'base'
    if mod not in CORE_MODS: continue
    src=open(f,encoding='utf-8',errors='ignore').read()
    # owning model per class block
    for blk in re.split(r'\nclass ', src):
        own=re.search(r"_(?:name|inherit)\s*=\s*['\"]([a-z0-9_.]+)['\"]", blk)
        own=own.group(1) if own else '?'
        for m in fld.finditer(blk):
            body=m.group(2)
            tgt=re.search(r"['\"]([a-z0-9_.]+)['\"]", body)
            if not tgt: continue
            tgt=tgt.group(1)
            if tgt in CORE and 'required=True' in body:
                req[tgt].append(f"{own}.{m.group(1)}  [{mod}]")
print(f"{'worksheet':<22}{'required=True references from core modules'}")
print("="*92)
for m,label in CORE.items():
    rs=sorted(set(req.get(m,[])))
    mark='CORE ' if rs else 'check'
    print(f"[{mark}] {label:<22}{'; '.join(rs[:3]) if rs else '— no required reference found —'}")
