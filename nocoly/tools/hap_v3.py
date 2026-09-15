#!/usr/bin/env python3
"""Minimal Nocoly HAP v3 REST client. Verified against the live tenant 14 Sep 2026.

    export HAP_TOKEN=pat_…
    export HAP_APP=3e596740-d096-42cd-b948-0b62a0220927
    python3 nocoly/tools/hap_v3.py app
    python3 nocoly/tools/hap_v3.py worksheet 6a9e38ccf363582dd3794504
    python3 nocoly/tools/hap_v3.py relations 6a9e38ccf363582dd3794504

Use this when the hap CLI misbehaves, or from a ground-up build that has no
lib/ helpers yet. Reads only — nothing here writes.

Note: POST /v3/app/worksheets CREATES a worksheet; it is not a list endpoint.
"""
import json, os, sys, urllib.request

BASE = os.environ.get('HAP_BASE', 'https://www.nocoly.com/api/v3')

def get(path):
    token, app = os.environ['HAP_TOKEN'], os.environ['HAP_APP']
    req = urllib.request.Request(
        f'{BASE}/{path}',
        headers={'Authorization': f'Bearer {token}', 'HAP-Appid': app},
    )
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read())

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'app'
    if cmd == 'app':
        d = get('app')['data']
        print(f"{d['name']}  org {d['organizationId']}")
        for s in d.get('sections', []):
            sheets = s.get('worksheets') or []
            print(f"\n  {s['name']}  ({len(sheets)})")
            for w in sheets:
                print(f"    {w.get('worksheetId') or w.get('id')}  {w['name']}")
    elif cmd == 'worksheet':
        d = get(f'app/worksheets/{sys.argv[2]}')['data']
        fs = d.get('fields') or []
        print(f"{d['name']}  ({d.get('alias','')})  {len(fs)} fields")
        for f in fs:
            src = f' -> {f["dataSource"]}' if f.get('dataSource') else ''
            print(f"  {f.get('name',''):<30} {f.get('type','')}{src}")
    elif cmd == 'relations':
        # every Relation control stores a bare worksheetId in dataSource, with no
        # appId — which is what makes cross-app Relations possible at all.
        d = get(f'app/worksheets/{sys.argv[2]}')['data']
        rel = [f for f in (d.get('fields') or []) if f.get('type') == 'Relation']
        print(f"{d['name']}: {len(rel)} Relation controls")
        for f in rel:
            print(f"  {f['name']:<30} dataSource={f.get('dataSource')}  subType={f.get('subType')}")
    else:
        print(__doc__)
        sys.exit(1)

if __name__ == '__main__':
    main()
