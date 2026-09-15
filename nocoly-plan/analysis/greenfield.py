import json, collections
SP='/tmp/claude-0/-home-user-odoo/9afe9781-77eb-5337-9b42-0f955ae77d73/scratchpad'
D=json.load(open(SP+'/manifests.json'))

def closure(m,seen=None):
    if seen is None: seen=set()
    for d in D.get(m,{}).get('depends',[]):
        if d not in seen: seen.add(d); closure(d,seen)
    return seen

APPS={'Sales':'sale','CRM':'crm','Invoicing':'account','Purchase':'purchase','Inventory':'stock',
 'Manufacturing':'mrp','Project':'project','Employees':'hr','Timesheet':'hr_timesheet',
 'Expenses':'hr_expense','Point of Sale':'point_of_sale','Events':'event','Email Marketing':'mass_mailing',
 'Website':'website','eCommerce':'website_sale','Survey':'survey','Maintenance':'maintenance',
 'Recruitment':'hr_recruitment','Time Off':'hr_holidays','Fleet':'fleet','Repair':'repair'}

# how many apps need each foundation module
need=collections.Counter()
for label,m in APPS.items():
    for d in closure(m): need[d]+=1
FOUND=['base','web','mail','base_setup','uom','product','analytic','account','portal','payment',
       'utm','sales_team','resource','digest','contacts','calendar','rating','sms','bus']
print("FOUNDATION MODULE — how many of the 21 apps require it")
print("="*60)
for m in sorted(FOUND,key=lambda x:-need[x]):
    if m in D: print(f"  {need[m]:>3}/21  {m}")

# topological install order of the foundation
order=[]; seen=set()
def visit(m):
    if m in seen or m not in D: return
    seen.add(m)
    for d in D[m]['depends']: visit(d)
    order.append(m)
for m in ['account','sale','crm','uom','product']: visit(m)
print("\nODOO'S OWN INSTALL ORDER to reach a working Sales system")
print("="*60)
print("  " + " → ".join(order))

# minimal slice: what does a bare quotation actually touch?
print("\nAPP → foundation modules it alone requires")
print("="*60)
for label in ['Invoicing','Sales','CRM','Purchase','Inventory']:
    cl=closure(APPS[label])
    f=sorted(x for x in cl if x in FOUND)
    print(f"  {label:<14} {len(cl):>2} modules · foundation: {', '.join(f)}")
