"""Print cached Nocoly Help pages (help.nocoly.com, cached 3 Nov 2026) from the knowledge base's corpus. Read-only.

  python -I read_pages.py --list --prefix worksheet           # URLs, titles and sizes in this slice
  python -I read_pages.py --prefix worksheet --part 1/2       # full text of the first half of the slice
  python -I read_pages.py --prefix worksheet --part 1/2 --offset 10 --limit 5   # pages 11-15 of that half
  python -I read_pages.py --other                             # every page outside the main slices

Prefixes are the first path segment after the host, comma-separated: worksheet, workflow, application, view, ...
"""
import argparse, os, sqlite3, sys

sys.stdout.reconfigure(encoding='utf-8')

DB = os.environ.get('NOCOLY_CORPUS') or os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..',
                                   'knowledge-base', 'nocoly-mingdao', 'research', 'corpus.sqlite'))
MAIN = ['worksheet', 'workflow', 'application', 'role', 'portal', 'plugin', 'extensions', 'view', 'custom-page',
        'chart', 'custom-action']

ap = argparse.ArgumentParser()
ap.add_argument('--prefix', default='')
ap.add_argument('--other', action='store_true')
ap.add_argument('--exclude', default='', help='with --other: more first segments to leave out, comma-separated')
ap.add_argument('--part', default='1/1')
ap.add_argument('--offset', type=int, default=0)
ap.add_argument('--limit', type=int, default=0)
ap.add_argument('--list', action='store_true')
a = ap.parse_args()

c = sqlite3.connect(f'file:{DB}?mode=ro', uri=True)
rows = c.execute("SELECT url, title, body FROM pages WHERE url LIKE 'https://help.nocoly.com/%' ORDER BY url").fetchall()


def seg(url):
    p = url[len('https://help.nocoly.com/'):].strip('/').split('/')
    return p[0] if p and p[0] else ''


if a.other:
    skip = set(MAIN) | set(filter(None, a.exclude.split(',')))
    rows = [r for r in rows if seg(r[0]) not in skip]
elif a.prefix:
    want = set(a.prefix.split(','))
    rows = [r for r in rows if seg(r[0]) in want]
k, n = map(int, a.part.split('/'))
size = -(-len(rows) // n)
rows = rows[(k - 1) * size:k * size]
rows = rows[a.offset:a.offset + a.limit] if a.limit else rows[a.offset:]
if a.list:
    for i, (u, t, b) in enumerate(rows):
        print(f'{i:3} {len(b or ""):7} {u}  | {t}')
    print(f'{len(rows)} pages, {sum(len(r[2] or "") for r in rows)} characters')
else:
    for u, t, b in rows:
        print(f'\n===== {u}\n# {t}\n{b or "(no text)"}')
