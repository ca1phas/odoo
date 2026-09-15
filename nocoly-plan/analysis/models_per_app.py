import re,glob,os,json
D = json.load(open('/tmp/claude-0/-home-user-odoo/9afe9781-77eb-5337-9b42-0f955ae77d73/scratchpad/manifests.json'))
def models_of(mod):
    out=set()
    for f in glob.glob(f'addons/{mod}/models/**/*.py',recursive=True)+glob.glob(f'addons/{mod}/wizard/**/*.py',recursive=True):
        src=open(f,encoding='utf-8',errors='ignore').read()
        for blk in re.split(r'\nclass ',src):
            mn=re.search(r"^\s*_name\s*=\s*['\"]([a-z0-9_.]+)['\"]",blk,re.M)
            if not mn: continue
            inh=re.search(r"^\s*_inherit\s*=\s*(.+)$",blk,re.M)
            if inh and mn.group(1) in inh.group(1): continue
            if re.search(r"TransientModel",blk): continue
            out.add(mn.group(1))
    return out
CAND=['crm','purchase','stock','mrp','project','account','point_of_sale','hr','hr_timesheet','repair','maintenance','website','sale']
print(f"{'app':<16} {'new persistent models (worksheets)':<36}")
print("="*88)
for a in CAND:
    ms=models_of(a)
    print(f"{a:<16} {len(ms):>3}   {', '.join(sorted(ms)[:9])}{' …' if len(ms)>9 else ''}")
print()
print("=== bridge module model counts (extra worksheets a bridge itself adds) ===")
for b in ['sale_stock','sale_purchase','sale_crm','sale_project','sale_mrp','stock_account','purchase_stock','account_payment']:
    if os.path.isdir(f'addons/{b}'):
        ms=models_of(b); print(f"  {b:<18} {len(ms)} new models  {sorted(ms)}")
