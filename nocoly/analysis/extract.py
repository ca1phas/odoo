import ast, json, os, sys

ROOTS = ['addons', 'odoo/addons']
data = {}
for root in ROOTS:
    for name in sorted(os.listdir(root)):
        p = os.path.join(root, name, '__manifest__.py')
        if not os.path.isfile(p):
            continue
        try:
            m = ast.literal_eval(open(p, encoding='utf-8').read())
        except Exception as e:
            print('ERR', name, e, file=sys.stderr); continue
        data[name] = {
            'path': os.path.join(root, name),
            'core': root.endswith('odoo/addons'),
            'depends': m.get('depends', []),
            'category': m.get('category', ''),
            'application': bool(m.get('application', False)),
            'auto_install': m.get('auto_install', False),
            'installable': m.get('installable', True),
            'name': m.get('name', name),
            'license': m.get('license',''),
        }
json.dump(data, open('nocoly/data/manifests.json','w'), indent=1)
print('modules:', len(data))
print('applications:', sum(1 for v in data.values() if v['application']))
print('auto_install (truthy):', sum(1 for v in data.values() if v['auto_install']))
print('not installable:', sum(1 for v in data.values() if not v['installable']))
