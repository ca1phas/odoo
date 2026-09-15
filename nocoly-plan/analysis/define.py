import os,re,glob
targets=['res.partner','product.template','product.product','uom.uom','res.company','res.currency',
         'account.tax','res.users','product.pricelist','account.payment.term','account.move',
         'sale.order','stock.picking','crm.lead','purchase.order','mrp.production','project.project','hr.employee']
found={t:[] for t in targets}
files=glob.glob('addons/*/models/*.py')+glob.glob('odoo/addons/base/models/*.py')+glob.glob('addons/*/models/**/*.py',recursive=True)
for f in set(files):
    src=open(f,encoding='utf-8',errors='ignore').read()
    # split into class blocks
    for blk in re.split(r'\nclass ', src):
        mn=re.search(r"^\s*_name\s*=\s*['\"]([a-z0-9_.]+)['\"]", blk, re.M)
        if not mn: continue
        name=mn.group(1)
        if name not in found: continue
        inh=re.search(r"^\s*_inherit\s*=\s*(.+)$", blk, re.M)
        inherits_self = bool(inh and name in inh.group(1))
        if not inherits_self:
            mod=f.split('/')[1] if f.startswith('addons/') else 'base'
            found[name].append(mod)
for t in targets:
    print(f"  {t:<22} TRUE DEFINITION IN: {sorted(set(found[t])) or '?'}")
