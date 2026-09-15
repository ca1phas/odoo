import html
SP='/tmp/claude-0/-home-user-odoo/9afe9781-77eb-5337-9b42-0f955ae77d73/scratchpad'
e=lambda s: html.escape(s, quote=True)

FOUND=[["Customers","Products","Product Variants","Categories","Units & Packagings","Sales Teams"],
       ["Pricelists","Price Rules","Attributes","Attribute Values","Attr. Lines","Attr. Values (tpl)"],
       ["Combo Choices","Combo Items","Taxes","Fiscal Positions","Payment Terms","Payment Methods"],
       ["Incoterms","Invoices","Invoice Lines","Activity Types","Activity Plans","Plan Steps"],
       ["Campaigns","Sources","Mediums","Projects","Sales Teams (cfg)"]]

TOWERS=[
 ("Sales","BUILT","built",None,
  ["Orders","Order Lines","Templates","Template Lines","Headers/Footers","Settings","Services & Material"]),
 ("CRM","PHASE 1","todo","+1 control on Orders",
  ["Leads","Stages","Lost Reasons","Recurring Plans"]),
 ("Purchase","PHASE 2","todo","+3 Orders · +1 Invoices",
  ["Purchase Orders","PO Lines","Bill Matching"]),
 ("Inventory","PHASE 3","todo","+27 Orders & Lines",
  ["Transfers","Stock Moves","Move Lines","Locations","Warehouses","Operation Types","Lots / Serials","Routes","Rules","On Hand"]),
 ("Project","PHASE 4","todo","+17 Orders & Lines",
  ["Tasks","Task Stages","Milestones","Project Stages","Tags","Collaborators"]),
 ("Manufacturing","PHASE 4","todo","+2 on Orders",
  ["Mfg Orders","Bills of Materials","BoM Lines","Work Centers","Operations","Unbuild Orders"]),
]

W,H=1120,730
FX,FW=40,1040
FOUND_TOP,BR_H,BR_G=552,25,4
TW,TG=158,18
TX0=(W-(len(TOWERS)*TW+(len(TOWERS)-1)*TG))/2
NAME_Y,TAG_Y,BASE=500,470,466

o=[f'<svg viewBox="0 0 {W} {H}" role="img" class="brickssvg" aria-label="A build diagram: a foundation slab of 29 shared Nocoly worksheets already built, carrying six app towers — Sales already built, then CRM, Purchase, Inventory, Project and Manufacturing to be added one phase at a time, each attaching to Sales by a small number of appended controls.">']

# foundation
fh=len(FOUND)*(BR_H+BR_G)+14
o.append(f'<rect class="fslab" x="{FX}" y="{FOUND_TOP}" width="{FW}" height="{fh}" rx="2"/>')
o.append(f'<text class="flabel" x="{FX+10}" y="{FOUND_TOP-8}">FOUNDATION — 29 shared worksheets, already built · reused by every app above</text>')
for r,row in enumerate(FOUND):
    n=len(row); bw=(FW-20-(n-1)*6)/n
    for c,name in enumerate(row):
        x=FX+10+c*(bw+6); y=FOUND_TOP+7+r*(BR_H+BR_G)
        o.append(f'<g><rect class="brick found" x="{x:.1f}" y="{y}" width="{bw:.1f}" height="{BR_H}" rx="1.5"/>'
                 f'<text class="btext found" x="{x+bw/2:.1f}" y="{y+BR_H/2+3.4}" text-anchor="middle">{e(name)}</text></g>')

# towers
for i,(app,badge,state,tag,sheets) in enumerate(TOWERS):
    x=TX0+i*(TW+TG)
    o.append(f'<rect class="nameband {state}" x="{x:.1f}" y="{NAME_Y}" width="{TW}" height="28" rx="2"/>')
    o.append(f'<text class="nameapp {state}" x="{x+10:.1f}" y="{NAME_Y+19}">{e(app)}</text>')
    o.append(f'<text class="badge {state}" x="{x+TW-9:.1f}" y="{NAME_Y+18}" text-anchor="end">{e(badge)}</text>')
    if tag:
        o.append(f'<rect class="tagbrick" x="{x:.1f}" y="{TAG_Y}" width="{TW}" height="24" rx="1.5"/>')
        o.append(f'<text class="tagtext" x="{x+TW/2:.1f}" y="{TAG_Y+15.5}" text-anchor="middle">{e(tag)}</text>')
    else:
        o.append(f'<text class="tagnone" x="{x+TW/2:.1f}" y="{TAG_Y+15.5}" text-anchor="middle">everything attaches here</text>')
    for j,s in enumerate(sheets):
        y=BASE-(j+1)*(BR_H+BR_G)
        o.append(f'<g><rect class="brick {state}" x="{x:.1f}" y="{y}" width="{TW}" height="{BR_H}" rx="1.5"/>'
                 f'<text class="btext {state}" x="{x+TW/2:.1f}" y="{y+BR_H/2+3.4}" text-anchor="middle">{e(s)}</text></g>')
    top=BASE-len(sheets)*(BR_H+BR_G)
    o.append(f'<text class="count" x="{x+TW/2:.1f}" y="{top-8}" text-anchor="middle">{len(sheets)} worksheets</text>')

o.append('</svg>')
open(SP+'/bricks.svg','w').write("\n".join(o))
print("bricks.svg bytes:",len("\n".join(o)),
      "| tallest top:",BASE-max(len(t[4]) for t in TOWERS)*(BR_H+BR_G))
