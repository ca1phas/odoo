import re,glob,collections
TARGETS={
 'account.tax':'Taxes','account.account':'Chart of Accounts','product.category':'Product Categories',
 'account.payment.term':'Payment Terms','account.payment.method':'Payment Methods','account.payment':'Payments',
 'product.attribute':'Attributes','product.attribute.value':'Attribute Values',
 'product.template.attribute.line':'Attr Lines','product.template.attribute.value':'Tmpl Attr Values',
 'product.pricelist':'Pricelists','product.pricelist.item':'Price Rules',
 'utm.campaign':'Campaigns','utm.source':'Sources','utm.medium':'Mediums','crm.team':'Sales Teams',
 'account.analytic.account':'Analytic Accounts','account.analytic.line':'Analytic Lines',
 'mail.activity.type':'Activity Types','mail.activity.plan':'Activity Plans',
 'res.country':'Countries','res.country.state':'States','account.fiscal.position':'Fiscal Positions',
 'account.incoterms':'Incoterms','res.currency':'Currencies',
 'product.combo':'Combo Choices','product.combo.item':'Combo Items','res.partner.category':'Contact Tags',
}
req=collections.defaultdict(set)
fld=re.compile(r"(\w+)\s*=\s*fields\.Many2one\((.{0,600}?)\)\s*\n", re.S)
for f in glob.glob('addons/*/models/**/*.py',recursive=True)+glob.glob('odoo/addons/base/models/*.py'):
    mod=f.split('/')[1] if f.startswith('addons/') else 'base'
    if mod.startswith('l10n_') or mod.startswith('test_'): continue
    src=open(f,encoding='utf-8',errors='ignore').read()
    for blk in re.split(r'\nclass ', src):
        own=re.search(r"_(?:name|inherit)\s*=\s*['\"]([a-z0-9_.]+)['\"]", blk)
        own=own.group(1) if own else '?'
        for m in fld.finditer(blk):
            b=m.group(2)
            t=re.search(r"['\"]([a-z0-9_.]+)['\"]", b)
            if not t: continue
            t=t.group(1)
            if t in TARGETS and 'required=True' in b:
                req[t].add(f"{own}.{m.group(1)} [{mod}]")
SELF={'account.payment.term':'account.payment.term','product.attribute':'product.attribute',
      'res.country':'res.country.state','product.pricelist':'product.pricelist',
      'account.payment.method':'account.payment.method','product.combo':'product.combo',
      'mail.activity.type':'mail.activity','product.template.attribute.line':'product.template.attribute',
      'product.attribute.value':'product.attribute','account.analytic.account':'account.analytic'}
print(f"{'worksheet':<20}{'required=True references (external only)'}")
print("="*100)
for m,label in TARGETS.items():
    rs=sorted(x for x in req.get(m,()) if not x.startswith(SELF.get(m,'\0')))
    ext=[x for x in rs if not x.split('.')[0]+'.'+x.split('.')[1] == m]
    print(f"  {label:<20}{'; '.join(rs[:4]) if rs else '— none —'}")
