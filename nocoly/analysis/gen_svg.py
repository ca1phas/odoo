import json, math
SP='nocoly/data'
C=json.load(open(SP+'/connections.json'))
E=json.load(open(SP+'/edges.json'))

ORDER=[("Sales",["CRM","Sales","Point of Sale"]),
       ("Finance",["Invoicing","Expenses"]),
       ("Inventory & Manufacturing",["Purchase","Inventory","Manufacturing","Repair","Maintenance"]),
       ("Services",["Project","Timesheet"]),
       ("Human Resources",["Employees","Recruitment","Time Off","Fleet"]),
       ("Marketing",["Events","Email Marketing","SMS Marketing","Survey"]),
       ("Website",["Website","eCommerce","eLearning","Forum","Live Chat","Blog"]),
       ("Productivity",["Discuss"])]
N=sum(len(v) for _,v in ORDER)
assert N==len(C), (N,len(C))

W,H=900,900; cx=cy=450.0; R=272.0; LR=284.0
GAP=5.0; span=(360.0-GAP*len(ORDER))/N
ang={}; cat_span={}
a=-90.0+GAP/2
for cat,apps in ORDER:
    start=a
    for app in apps:
        ang[app]=a+span/2; a+=span
    cat_span[cat]=(start,a); a+=GAP

def pt(deg,r):
    t=math.radians(deg); return cx+r*math.cos(t), cy+r*math.sin(t)
def arc(r,a0,a1,sweep=1):
    x0,y0=pt(a0,r); x1,y1=pt(a1,r)
    d=(a1-a0)%360 if sweep else (a0-a1)%360
    large=1 if d>180 else 0
    return f"M{x0:.1f},{y0:.1f}A{r},{r} 0 {large} {sweep} {x1:.1f},{y1:.1f}"

out=[]
out.append(f'<svg viewBox="0 0 {W} {H}" role="img" class="netsvg" '
           f'aria-label="Connectivity map of 27 Odoo apps: 74 pairs joined by bridge modules, '
           f'with Sales, Invoicing, Inventory and Manufacturing forming the densest cluster.">')
# category arcs (outside the app-label band) with names on text paths
CR, CTR = 388.0, 396.0
out.append('<defs>')
for i,(cat,(a0,a1)) in enumerate(cat_span.items()):
    mid=(a0+a1)/2 % 360
    # widen the text path when the label is longer than the category's own arc
    need=len(cat)*7.6/(CTR*math.pi/180)
    half=max((a1-a0)/2-1.2, need/2)
    half=min(half, (a1-a0)/2+GAP/2-0.6)
    m=(a0+a1)/2
    if 5 < mid < 175:                      # bottom half: reverse so text reads upright
        out.append(f'<path id="cp{i}" d="{arc(CTR,m+half,m-half,0)}" fill="none"/>')
    else:
        out.append(f'<path id="cp{i}" d="{arc(CTR,m-half,m+half,1)}" fill="none"/>')
out.append('</defs>')
out.append('<g class="catarcs">')
for i,(cat,(a0,a1)) in enumerate(cat_span.items()):
    out.append(f'<path class="catarc" d="{arc(CR,a0+1.2,a1-1.2)}" fill="none"/>')
    label=cat.replace("&","&amp;")
    out.append(f'<text class="catlabel"><textPath href="#cp{i}" startOffset="50%" '
               f'text-anchor="middle">{label}</textPath></text>')
out.append('</g>')
# edges
out.append('<g class="edges" fill="none">')
for k,w in sorted(E.items(), key=lambda kv: kv[1]):
    a_,b_=k.split('|')
    if a_ not in ang or b_ not in ang: continue
    A,B=ang[a_],ang[b_]
    x0,y0=pt(A,R-6); x1,y1=pt(B,R-6)
    sep=abs((A-B+180)%360-180)
    cr=(R-6)*math.cos(math.radians(sep/2))*0.55
    bis=A+((B-A+540)%360-180)/2
    qx,qy=pt(bis,cr)
    sw=round(0.7+w*0.34,2); op=round(min(0.62,0.20+w*0.038),3)
    out.append(f'<path class="edge" data-a="{a_}" data-b="{b_}" '
               f'd="M{x0:.1f},{y0:.1f}Q{qx:.1f},{qy:.1f} {x1:.1f},{y1:.1f}" '
               f'stroke-width="{sw}" opacity="{op}"><title>{a_} ↔ {b_} · '
               f'{w} bridge module{"s" if w>1 else ""}</title></path>')
out.append('</g>')
# nodes + labels
out.append('<g class="nodes">')
for cat,apps in ORDER:
    for app in apps:
        A=ang[app]; x,y=pt(A,R-6)
        bt=C[app]['bridge_total']
        r=round(2.2+math.sqrt(bt)*0.95,2)
        flip = 90<((A+360)%360)<270
        rot=A+180 if flip else A
        anc="end" if flip else "start"
        cls="node"+(" iso" if bt==0 else "")
        out.append(f'<g class="napp{" iso" if bt==0 else ""}" data-app="{app}" tabindex="0">'
                   f'<circle class="{cls}" cx="{x:.1f}" cy="{y:.1f}" r="{r}"/>'
                   f'<text class="nlabel" transform="translate({cx},{cy}) rotate({rot:.2f}) '
                   f'translate({(LR)*(-1 if flip else 1):.1f},0) rotate({180 if flip else 0})" '
                   f'text-anchor="{anc}" dy=".32em">{app}</text>'
                   f'<title>{app} · {bt} bridge module{"s" if bt!=1 else ""}</title></g>')
out.append('</g></svg>')
svg="\n".join(out)
open(SP+'/net.svg','w').write(svg)
print("svg bytes:",len(svg),"| nodes:",N,"| edges drawn:",sum(1 for k in E))
