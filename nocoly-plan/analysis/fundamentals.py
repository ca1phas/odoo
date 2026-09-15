import re,glob,collections,json,os
# how many DISTINCT modules point a relational field at each model
ref=collections.defaultdict(set)
inh=collections.defaultdict(set)
define={}
pat_rel=re.compile(r"fields\.(?:Many2one|Many2many|One2many)\(\s*['\"]([a-z0-9_.]+)['\"]|comodel_name\s*=\s*['\"]([a-z0-9_.]+)['\"]")
for f in glob.glob('addons/*/**/*.py',recursive=True)+glob.glob('odoo/addons/base/**/*.py',recursive=True):
    parts=f.split('/')
    mod = parts[1] if f.startswith('addons/') else 'base'
    if mod.startswith('l10n_') or mod.startswith('test_'): continue
    try: src=open(f,encoding='utf-8',errors='ignore').read()
    except: continue
    for m in pat_rel.finditer(src):
        ref[m.group(1) or m.group(2)].add(mod)
    for blk in re.split(r'\nclass ',src):
        mn=re.search(r"^\s*_name\s*=\s*['\"]([a-z0-9_.]+)['\"]",blk,re.M)
        ih=re.search(r"^\s*_inherit\s*=\s*(.+)$",blk,re.M)
        if mn:
            name=mn.group(1)
            if not (ih and name in ih.group(1)):
                if re.search(r"TransientModel|AbstractModel",blk): continue
                define.setdefault(name,mod)
        if ih:
            for t in re.findall(r"['\"]([a-z0-9_.]+)['\"]",ih.group(1)):
                inh[t].add(mod)
json.dump({k:sorted(v) for k,v in ref.items()},open('/tmp/claude-0/-home-user-odoo/9afe9781-77eb-5337-9b42-0f955ae77d73/scratchpad/refs.json','w'))
CORE={'base','uom','product','account','mail','analytic','sales_team','utm','resource','portal','payment','bus','web','base_setup','decimal_precision'}
rows=[]
for m,mods in ref.items():
    d=define.get(m)
    if not d: continue
    rows.append((len(mods),len(inh.get(m,())),m,d))
rows.sort(reverse=True)
print(f"{'refs':>5}{'ext':>5}  {'model':<34}{'defined in'}")
print("="*78)
for r,e,m,d in rows[:55]:
    star='  <-- CORE' if d in CORE else ''
    print(f"{r:>5}{e:>5}  {m:<34}{d}{star}")
