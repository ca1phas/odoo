import json, collections, re
D = json.load(open('/tmp/claude-0/-home-user-odoo/9afe9781-77eb-5337-9b42-0f955ae77d73/scratchpad/manifests.json'))

l10n = [m for m in D if m.startswith('l10n_')]
test = [m for m in D if m.startswith('test_') or m.startswith('web_studio') or m=='base_import_module']
print(f"Total modules: {len(D)}")
print(f"  localization (l10n_*): {len(l10n)}")
print(f"  test_* modules       : {len(test)}")
core_biz = [m for m in D if m not in l10n and m not in test]
print(f"  business modules     : {len(core_biz)}")

ai = {m:v for m,v in D.items() if v['auto_install']}
ai_biz = {m:v for m,v in ai.items() if m in core_biz}
print(f"\nauto_install total: {len(ai)}  (business-only: {len(ai_biz)})")
listform = {m:v for m,v in ai_biz.items() if isinstance(v['auto_install'], (list,tuple))}
trueform = {m:v for m,v in ai_biz.items() if v['auto_install'] is True}
print(f"  auto_install=True (install when ALL depends present): {len(trueform)}")
print(f"  auto_install=[...] (install when listed present)    : {len(listform)}")

# A "bridge" = auto_install module whose job is to join >=2 other modules
bridges = {m:v for m,v in ai_biz.items() if len(v['depends'])>=2}
print(f"\nBRIDGE modules (auto_install, >=2 depends, non-l10n): {len(bridges)}")
print(f"  -> {len(bridges)/len(core_biz)*100:.0f}% of all business modules exist ONLY to join two apps")

print("\n" + "="*72)
print("SAMPLE BRIDGES around the Sales app (what 'Sales' gains per co-installed app)")
print("="*72)
for m,v in sorted(bridges.items()):
    if m.startswith('sale_') or m.endswith('_sale') or '_sale_' in m:
        print(f"  {m:<34} depends={v['depends']}")
