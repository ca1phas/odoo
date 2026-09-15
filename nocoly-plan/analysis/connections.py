import json, collections, itertools
SP='/tmp/claude-0/-home-user-odoo/9afe9781-77eb-5337-9b42-0f955ae77d73/scratchpad'
D=json.load(open(SP+'/manifests.json'))

APPS=[("Website","website","Website"),("eCommerce","website_sale","Website"),("Blog","website_blog","Website"),
 ("Forum","website_forum","Website"),("eLearning","website_slides","Website"),("Live Chat","im_livechat","Website"),
 ("CRM","crm","Sales"),("Sales","sale","Sales"),("Point of Sale","point_of_sale","Sales"),
 ("Invoicing","account","Finance"),("Expenses","hr_expense","Finance"),
 ("Inventory","stock","Inventory & Manufacturing"),("Manufacturing","mrp","Inventory & Manufacturing"),
 ("Purchase","purchase","Inventory & Manufacturing"),("Maintenance","maintenance","Inventory & Manufacturing"),
 ("Employees","hr","Human Resources"),("Recruitment","hr_recruitment","Human Resources"),
 ("Time Off","hr_holidays","Human Resources"),("Fleet","fleet","Human Resources"),
 ("Email Marketing","mass_mailing","Marketing"),("SMS Marketing","mass_mailing_sms","Marketing"),
 ("Events","event","Marketing"),("Survey","survey","Marketing"),
 ("Project","project","Services"),("Timesheet","hr_timesheet","Services"),
 ("Discuss","mail","Productivity"),("Repair","repair","Inventory & Manufacturing"),
]
ROOT2LABEL={m:l for l,m,c in APPS}
ROOTS=set(ROOT2LABEL)

FRAMEWORK={'base','web','base_setup','bus','web_tour','html_editor','html_builder','http_routing',
 'auth_signup','portal','digest','onboarding','iap','mail_bot','resource','resource_mail','phone_validation',
 'google_recaptcha','social_media','attachment_indexation','barcodes','barcodes_gs1_nomenclature','spreadsheet',
 'gamification','link_tracker','partner_autocomplete','google_address_autocomplete','iot_base','web_editor','rating','portal_rating','website_mail','website_partner','website_profile','contacts','calendar','sms','utm','analytic','uom','payment','website_payment','mail_group'}
MASTER={'product','account','uom','analytic','payment','utm','sales_team','stock_account','delivery'}

def closure(m,seen=None):
    if seen is None: seen=set()
    for d in D.get(m,{}).get('depends',[]):
        if d not in seen: seen.add(d); closure(d,seen)
    return seen

def roots_of(m):
    return {r for r in ROOTS if r in (closure(m)|{m})}

# bridges
bridges=collections.defaultdict(set)   # app -> set of (other_app, bridge_module)
allb=[]
for m,v in D.items():
    if m.startswith('l10n_') or m.startswith('test_'): continue
    if not v['auto_install'] or len(v['depends'])<2: continue
    br=[roots_of(d) for d in v['depends']]
    rs=roots_of(m)
    for a,b in itertools.combinations(sorted(rs),2):
        if any(a in x and b not in x for x in br) and any(b in x and a not in x for x in br):
            bridges[a].add((b,m)); bridges[b].add((a,m)); allb.append((a,b,m))

out={}
for label,mod,cat in APPS:
    if mod not in D: continue
    cl=closure(mod)
    hard_apps=sorted(ROOT2LABEL[r] for r in (cl & ROOTS))
    master=sorted(cl & MASTER)
    conn=collections.defaultdict(list)
    for other,bm in bridges.get(mod,()):
        conn[ROOT2LABEL[other]].append(bm)
    out[label]={'module':mod,'category':cat,'depends':D[mod]['depends'],
      'closure':len(cl),'requires_apps':hard_apps,'master':master,
      'connects':{k:sorted(set(v)) for k,v in sorted(conn.items())},
      'bridge_total':len(set(bm for _,bm in bridges.get(mod,())))}
json.dump(out,open(SP+'/connections.json','w'),indent=1)

for label,mod,cat in APPS:
    if label not in out: continue
    o=out[label]
    print(f"\n{'='*76}\n{label}  ({o['module']})   [{cat}]   closure={o['closure']}")
    print(f"  REQUIRES apps : {', '.join(o['requires_apps']) or '— none —'}")
    print(f"  master data   : {', '.join(o['master']) or '—'}")
    print(f"  CONNECTS to   : {o['bridge_total']} bridge modules")
    for k,v in o['connects'].items():
        print(f"     ↔ {k:<18} {', '.join(v[:5])}{'  +'+str(len(v)-5) if len(v)>5 else ''}")
