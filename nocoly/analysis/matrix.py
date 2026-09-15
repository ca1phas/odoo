import json, collections, itertools
D = json.load(open('nocoly/data/manifests.json'))
ROOTS = ['sale','stock','account','purchase','mrp','project','crm','hr','website','point_of_sale',
         'mail','mass_mailing','event','hr_timesheet','hr_expense','hr_holidays','repair','maintenance',
         'survey','calendar','fleet','loyalty','delivery','payment','sign','documents','helpdesk','lunch']
ROOTS=[r for r in ROOTS if r in D]

def closure(m, seen=None):
    if seen is None: seen=set()
    for d in D.get(m,{}).get('depends',[]):
        if d not in seen:
            seen.add(d); closure(d, seen)
    return seen

# roots each module touches (itself included)
def roots_of(m):
    c = closure(m) | {m}
    return {r for r in ROOTS if r in c}

l10n=lambda m: m.startswith('l10n_') or m.startswith('test_')
pairs=collections.defaultdict(list)
for m,v in D.items():
    if l10n(m) or not v['auto_install'] or len(v['depends'])<2: continue
    rs = roots_of(m)
    # direct-parent roots only: the roots named (transitively) by each separate dep branch
    branch_roots=[roots_of(d) for d in v['depends']]
    for a,b in itertools.combinations(sorted(rs),2):
        if any(a in br and b not in br for br in branch_roots) and any(b in br and a not in br for br in branch_roots):
            pairs[(a,b)].append(m)

print("="*78)
print("APP-PAIR COUPLING: number of bridge modules joining each pair (top 30)")
print("="*78)
for (a,b),ms in sorted(pairs.items(), key=lambda x:-len(x[1]))[:30]:
    print(f"  {len(ms):3d}  {a:<16} <-> {b:<16} e.g. {', '.join(sorted(ms)[:3])}")

print()
print("="*78)
print("COUPLING LOAD PER APP (total bridges touching it)")
print("="*78)
load=collections.Counter()
for (a,b),ms in pairs.items():
    load[a]+=len(ms); load[b]+=len(ms)
for r,c in load.most_common():
    print(f"  {c:4d}  {r}")
