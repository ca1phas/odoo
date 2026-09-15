import json, collections
D = json.load(open('/tmp/claude-0/-home-user-odoo/9afe9781-77eb-5337-9b42-0f955ae77d73/scratchpad/manifests.json'))

# transitive closure
def closure(m, seen=None):
    if seen is None: seen=set()
    for d in D.get(m,{}).get('depends',[]):
        if d not in seen:
            seen.add(d); closure(d, seen)
    return seen

# reverse deps
rev = collections.defaultdict(set)
for m,v in D.items():
    for d in v['depends']: rev[d].add(m)

print("="*70)
print("TOP 30 MOST DEPENDED-UPON MODULES (direct reverse-dependency count)")
print("="*70)
for m,c in sorted(((m,len(s)) for m,s in rev.items()), key=lambda x:-x[1])[:30]:
    v=D.get(m,{})
    print(f"{c:4d}  {m:<28} app={str(v.get('application',''))[:5]:<5} cat={v.get('category','')[:34]}")

print()
print("="*70)
print("THE 34 DECLARED APPLICATIONS: transitive dependency footprint")
print("="*70)
apps=[(m,v) for m,v in D.items() if v['application']]
rows=[]
for m,v in apps:
    cl=closure(m)
    rows.append((len(cl),m,v['category'],sorted(cl)))
for n,m,cat,cl in sorted(rows):
    print(f"{n:4d} deps  {m:<26} [{cat}]")
