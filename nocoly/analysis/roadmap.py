import json
D=json.load(open('nocoly/data/manifests.json'))
def closure(m,seen=None):
    if seen is None: seen=set()
    for d in D.get(m,{}).get('depends',[]):
        if d not in seen: seen.add(d); closure(d,seen)
    return seen
# modules already effectively realised in Nocoly Sales
HAVE={'base','web','base_setup','mail','bus','uom','product','account','sale','sale_management',
      'sales_team','utm','portal','payment','digest','analytic','resource','onboarding','html_editor',
      'phone_validation','account_payment','product_images','sale_pdf_quote_builder','spreadsheet'}
CAND=[('crm','CRM'),('purchase','Purchase'),('stock','Inventory'),('mrp','Manufacturing'),
      ('project','Project'),('point_of_sale','Point of Sale'),('hr','Employees'),
      ('repair','Repair'),('maintenance','Maintenance'),('website','Website'),
      ('mass_mailing','Email Marketing'),('event','Events'),('survey','Surveys'),
      ('hr_expense','Expenses'),('hr_timesheet','Timesheets'),('calendar','Calendar'),
      ('contacts','Contacts'),('hr_holidays','Time Off'),('fleet','Fleet'),('loyalty','Loyalty')]
print(f"{'App':<16}{'dep closure':>12}{'already have':>14}{'NEW modules':>13}  new modules to model")
print("="*110)
rows=[]
for m,label in CAND:
    if m not in D: continue
    cl=closure(m)|{m}
    new=sorted(cl-HAVE)
    rows.append((len(new),label,len(cl),len(cl)-len(new),new))
for n,label,tot,have,new in sorted(rows):
    print(f"{label:<16}{tot:>12}{have:>14}{n:>13}  {', '.join(new[:6])}{' …' if len(new)>6 else ''}")
