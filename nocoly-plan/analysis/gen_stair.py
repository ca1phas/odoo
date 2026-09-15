import html
SP='/tmp/claude-0/-home-user-odoo/9afe9781-77eb-5337-9b42-0f955ae77d73/scratchpad'
e=lambda s: html.escape(str(s), quote=True)
PH=[(1,["Core","Foundation"],14,"found"),
    (2,["CRM"],4,"app"),(3,["Sales"],5,"app"),(4,["Point of","Sale"],12,"app"),
    (5,["Inventory &","Manufacturing"],45,"app"),(6,["Services"],12,"app"),
    (7,["Human","Resources"],35,"app"),(8,["Finance"],4,"app"),
    (9,["Marketing"],28,"app"),(10,["Website"],49,"app"),(11,["Productivity"],3,"app")]
W,H=1060,566
CW,CG=72,14
X0=(W-(len(PH)*CW+(len(PH)-1)*CG))/2
BASE,BH,BG=424,6,1.6
o=[f'<svg viewBox="0 0 {W} {H}" role="img" class="stairsvg" aria-label="Eleven phases. Phase one builds 36 shared foundation worksheets; the ten app phases after it add only their own, reaching 233 worksheets in total. Point of Sale in phase four carries a hard prerequisite on Inventory in phase five.">']
o.append(f'<line class="axis0" x1="{X0-16:.0f}" y1="{BASE+1}" x2="{X0+len(PH)*(CW+CG)-CG+16:.0f}" y2="{BASE+1}"/>')
OPT=22
run=0; xs={}
for n,name,cnt,kind in PH:
    x=X0+(n-1)*(CW+CG); xs[n]=x; run+=cnt+(OPT if n==1 else 0)
    for i in range(cnt):
        y=BASE-(i+1)*(BH+BG)
        o.append(f'<rect class="sb {kind}" x="{x:.0f}" y="{y:.1f}" width="{CW}" height="{BH}" rx="1"/>')
    extra=OPT if n==1 else 0
    for i in range(cnt,cnt+extra):
        y=BASE-(i+1)*(BH+BG)
        o.append(f'<rect class="sb opt" x="{x:.0f}" y="{y:.1f}" width="{CW}" height="{BH}" rx="1"/>')
    top=BASE-(cnt+extra)*(BH+BG)
    lbl=f"{cnt}+{extra}" if extra else str(cnt)
    o.append(f'<text class="scount {kind}" x="{x+CW/2:.0f}" y="{top-8:.0f}" text-anchor="middle">{lbl}</text>')
    o.append(f'<text class="sphase" x="{x+CW/2:.0f}" y="{BASE+20}" text-anchor="middle">PHASE {n}</text>')
    for k,line in enumerate(name):
        o.append(f'<text class="sname" x="{x+CW/2:.0f}" y="{BASE+38+k*13}" text-anchor="middle">{e(line)}</text>')
    o.append(f'<text class="srun" x="{x+CW/2:.0f}" y="{BASE+70}" text-anchor="middle">{run}</text>')
o.append(f'<text class="srunlbl" x="56" y="{BASE+70}" text-anchor="end">total</text>')
# prerequisite: phase 5 must precede phase 4 — arc bulges left, label inside the bulge
x4r=xs[4]+CW; x5l=xs[5]
top4=BASE-12*(BH+BG); top5=BASE-45*(BH+BG)
o.append(f'<path class="prereq" d="M{x5l:.0f},{top5-8:.0f} C{x5l-110:.0f},{top5+30:.0f} '
         f'{x4r-100:.0f},{top4-70:.0f} {x4r+6:.0f},{top4-7:.0f}" marker-end="url(#pa)"/>')
o.append(f'<text class="prereqlbl" x="232" y="188" text-anchor="middle">Point of Sale needs</text>')
o.append(f'<text class="prereqlbl" x="232" y="202" text-anchor="middle">Inventory first</text>')
o.insert(1,'<defs><marker id="pa" viewBox="0 0 10 8" refX="9" refY="4" markerWidth="7" markerHeight="6" orient="auto-start-reverse"><path d="M0,0 L10,4 L0,8 z" class="prereqhead"/></marker></defs>')
ly=BASE+100
o.append(f'<rect class="sb found" x="{X0:.0f}" y="{ly-8}" width="13" height="7" rx="1"/>')
o.append(f'<text class="sleg" x="{X0+20:.0f}" y="{ly}">core foundation — nothing runs without it</text>')
o.append(f'<rect class="sb opt" x="{X0+290:.0f}" y="{ly-8}" width="13" height="7" rx="1"/>')
o.append(f'<text class="sleg" x="{X0+310:.0f}" y="{ly}">optional feature bundles — land when first needed</text>')
o.append(f'<rect class="sb app" x="{X0+640:.0f}" y="{ly-8}" width="13" height="7" rx="1"/>')
o.append(f'<text class="sleg" x="{X0+660:.0f}" y="{ly}">a group’s own worksheets</text>')
o.append('</svg>')
open(SP+'/stair.svg','w').write("\n".join(o))
print("bytes",len("\n".join(o)),"| tallest top:",BASE-49*(BH+BG),"| total:",run)
