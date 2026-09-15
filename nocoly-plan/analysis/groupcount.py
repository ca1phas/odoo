import re,glob,os
def models(mod):
    out=set()
    for f in glob.glob(f'addons/{mod}/models/**/*.py',recursive=True):
        src=open(f,encoding='utf-8',errors='ignore').read()
        for blk in re.split(r'\nclass ',src):
            mn=re.search(r"^\s*_name\s*=\s*['\"]([a-z0-9_.]+)['\"]",blk,re.M)
            if not mn: continue
            ih=re.search(r"^\s*_inherit\s*=\s*(.+)$",blk,re.M)
            if ih and mn.group(1) in ih.group(1): continue
            if re.search(r"TransientModel|AbstractModel",blk): continue
            if re.match(r"(theme\.|ir\.|report\.)",mn.group(1)): continue
            out.add(mn.group(1))
    return out
GROUPS={
 "Point of Sale":["point_of_sale"],
 "Inventory & Manufacturing":["purchase","stock","mrp","maintenance","repair"],
 "Services":["project","hr_timesheet"],
 "Human Resources":["hr","hr_recruitment","hr_holidays","fleet"],
 "Finance":["hr_expense"],
 "Marketing":["mass_mailing","mass_mailing_sms","event","survey"],
 "Website":["website","website_sale","website_blog","website_forum","website_slides","im_livechat"],
 "Productivity":["mail"],
}
for g,mods in GROUPS.items():
    tot=set(); parts=[]
    for m in mods:
        s=models(m); tot|=s; parts.append(f"{m}:{len(s)}")
    print(f"{g:<28}{len(tot):>4}   {' '.join(parts)}")
