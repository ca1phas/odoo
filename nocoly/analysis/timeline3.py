SP='nocoly/data'
import json
L,M,LN,T = 0.5,2.0,3.0,8.0        # worksheet + its controls + form
WF   = 1.5                         # each button workflow
VIEW = 4.0                         # views per app
RULE = 3.0                         # roles + validation rules per app
RPT  = 6.0                         # reporting pages / pivots per app
DOC  = 5.0                         # PDF + email templates, document-producing apps only
UIT  = 0.4                         # UI click-through pass, per worksheet
F    = 1.25                        # correction loop (lower than before: testing now explicit)
WEEK = 40.0
def h(ws=0,lk=0,ms=0,ln=0,tx=0,apps=0,docs=0,wf=0,extra=0):
    base = lk*L+ms*M+ln*LN+tx*T
    return round((base + wf*WF + apps*(VIEW+RULE+RPT) + docs*DOC + ws*UIT + extra)*F,1)

BUND={'btax':h(ws=1,ms=1),'bcoa':h(ws=1,ms=1,extra=1),'bcat':h(ws=1,lk=1),'bterm':h(ws=1,lk=1,ln=1),
 'bpay':h(ws=2,lk=1,tx=1,wf=2),'bvar':h(ws=4,lk=2,ms=2,wf=2),'bpl':h(ws=2,ms=2,wf=2),
 'butm':h(ws=3,lk=3),'bteam':h(ws=1,ms=1),'bana':h(ws=2,ms=2),'bplan':h(ws=3,lk=3),
 'bgeo':h(ws=2,lk=2,extra=1),'bfp':h(ws=1,ms=1,ln=1),'binc':h(ws=1,lk=1),'bcur':h(ws=1,lk=1),
 'bcombo':h(ws=2,lk=1,ms=1),'btag':h(ws=1,lk=1),
 'bqtpl':h(ws=2,ms=1,ln=1),'bqb':h(ws=1,lk=1)}
CORE=h(ws=7,lk=1,ms=4,ln=1,tx=1,apps=1,wf=2)
BUND_APP=h(apps=1)   # the Configuration section the bundles share
PHASE={2:h(ws=4,lk=3,tx=1,apps=1,wf=3),
 3:h(ws=2,ln=1,tx=1,apps=1,docs=1,wf=14,extra=1),
 4:h(ws=12,lk=7,ms=2,ln=1,tx=2,apps=1,docs=1,wf=8),
 5:h(ws=45,lk=26,ms=10,ln=3,tx=6,apps=5,docs=3,wf=20,extra=12),
 6:h(ws=12,lk=7,ms=2,ln=1,tx=2,apps=2,wf=8,extra=8),
 7:h(ws=35,lk=21,ms=9,ln=2,tx=3,apps=4,docs=1,wf=12),
 8:h(ws=4,lk=1,ms=1,ln=1,tx=1,apps=1,docs=1,wf=4),
 9:h(ws=28,lk=15,ms=8,ln=2,tx=3,apps=3,docs=2,wf=12),
 10:h(ws=49,lk=24,ms=16,ln=3,tx=6,apps=6,wf=10,extra=80),
 11:h(ws=3,lk=3,apps=1)}
tb=sum(BUND.values())+BUND_APP
tot=CORE+tb+sum(PHASE.values())
print("BACK-TEST against the existing Sales build (33 ws, 16 workflows, 1 app, documents):")
bt=h(ws=33,lk=18,ms=10,ln=3,tx=2,apps=1,docs=1,wf=16)
print(f"   model predicts {bt:.0f} h · actually spent ≈100 h · build is 88% with the UI pass paused")
print(f"   → implied remaining ≈ {bt-100:.0f} h, which is the 12% tail + the unfinished click-through\n")
NAME={'2':'CRM','3':'Sales','4':'Point of Sale','5':'Inventory & Manufacturing','6':'Services',
      '7':'Human Resources','8':'Finance','9':'Marketing','10':'Website','11':'Productivity'}
WS={'2':4,'3':2,'4':12,'5':45,'6':12,'7':35,'8':4,'9':28,'10':49,'11':3}
print(f"{'ph':<4}{'phase':<26}{'ws':>4}{'hours':>8}{'weeks':>7}{'cum':>7}")
print("="*58)
cum=0
for n,nm,ws,hrs in [('1','Core Foundation',7,CORE),('1','Optional bundles',32,tb)]+[(k,NAME[k],WS[k],PHASE[int(k)]) for k in NAME]:
    cum+=hrs/WEEK
    print(f"{n:<4}{nm:<26}{ws:>4}{hrs:>8.0f}{hrs/WEEK:>7.1f}{cum:>7.1f}")
print("="*58)
print(f"    TOTAL {tot:.0f} h = {tot/WEEK:.0f} weeks ≈ {tot/WEEK/4.345:.1f} months")
print(f"    without Website + Inventory&Mfg: {(tot-PHASE[10]-PHASE[5])/WEEK:.0f} weeks ≈ {(tot-PHASE[10]-PHASE[5])/WEEK/4.345:.1f} months")
json.dump({'core':CORE,'bundles':BUND,'bundleApp':BUND_APP,'phases':{str(k):v for k,v in PHASE.items()},'week':WEEK},
          open(SP+'/hours.json','w'),indent=0)
