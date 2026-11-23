"""Export every model and field of the local Odoo 20 with the module that owns it (Odoo side of the register).

Reads the local Odoo database (`external/odoo20-local`, database `odoo20`) through `docker compose exec db psql`.
Docker Desktop must be running. Read-only: only SELECT statements run.

Writes, next to modules.json:
- odoo-models.csv : model, label, transient, modules (space-separated, first = the module that defines the model)
- odoo-fields.csv : model, name, ttype, relation, store, required, readonly, computed, is_related, label, modules
  (same columns as foundation-fields.csv; first module = the module that declares the field)

Notes:
- `computed` comes from ir_model_fields.compute, which Odoo fills only for custom (manual) fields.
  For a computed field of a normal module, read `store` = f instead.
- The export is of the modules installed locally (267, see external/odoo20-local/README.md).

Usage: python -I odoo_export.py [--out DIR] [--check foundation-fields.csv]
"""
import argparse, csv, io, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
COMPOSE = os.path.normpath(os.path.join(HERE, '..', 'odoo20-local', 'docker-compose.yml'))

MODELS_SQL = """
COPY (
  SELECT m.model, coalesce(m.name->>'en_US', m.model) AS label, m.transient,
         coalesce((SELECT string_agg(d.module, ' ' ORDER BY d.id) FROM ir_model_data d
                   WHERE d.model = 'ir.model' AND d.res_id = m.id), '') AS modules
  FROM ir_model m ORDER BY m.model
) TO STDOUT WITH CSV HEADER
"""

FIELDS_SQL = """
COPY (
  SELECT f.model, f.name, f.ttype, coalesce(f.relation, '') AS relation, f.store, f.required, f.readonly,
         (f.compute IS NOT NULL AND f.compute <> '') AS computed,
         (f.related IS NOT NULL AND f.related <> '') AS is_related,
         coalesce(f.field_description->>'en_US', f.name) AS label,
         coalesce((SELECT string_agg(d.module, ' ' ORDER BY d.id) FROM ir_model_data d
                   WHERE d.model = 'ir.model.fields' AND d.res_id = f.id), '') AS modules
  FROM ir_model_fields f ORDER BY f.model, f.id
) TO STDOUT WITH CSV HEADER
"""


def psql(sql):
    cmd = ['docker', 'compose', '-f', COMPOSE, 'exec', '-T', 'db',
           'psql', '-U', 'odoo', '-d', 'odoo20', '-v', 'ON_ERROR_STOP=1', '-q', '-c', ' '.join(sql.split())]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        sys.exit('psql failed: ' + r.stderr.decode('utf-8', 'replace'))
    return r.stdout.decode('utf-8')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(HERE, 'odoo-20.0'))
    ap.add_argument('--check', help='an older field CSV; report rows that differ for the models it covers')
    a = ap.parse_args()
    models, fields = psql(MODELS_SQL), psql(FIELDS_SQL)
    for name, text in (('odoo-models.csv', models), ('odoo-fields.csv', fields)):
        with open(os.path.join(a.out, name), 'w', encoding='utf-8', newline='') as f:
            f.write(text)
    nm = len(list(csv.DictReader(io.StringIO(models))))
    rows = list(csv.DictReader(io.StringIO(fields)))
    print(f'models {nm}, fields {len(rows)} -> {a.out}')
    if a.check:
        old = list(csv.DictReader(open(a.check, encoding='utf-8')))
        keep = {r['model'] for r in old}
        new = {(r['model'], r['name']): r for r in rows if r['model'] in keep}
        oldk = {(r['model'], r['name']): r for r in old}
        missing = sorted(set(oldk) - set(new))
        extra = sorted(set(new) - set(oldk))
        changed = [k for k in oldk if k in new and oldk[k] != new[k]]
        print(f'check against {os.path.basename(a.check)}: {len(oldk)} old rows, missing {len(missing)}, extra {len(extra)}, changed {len(changed)}')
        for k in changed[:10]:
            print('  changed', k, {c: (oldk[k][c], new[k][c]) for c in oldk[k] if oldk[k][c] != new[k][c]})
        for k in (missing + extra)[:10]:
            print('  missing' if k in missing else '  extra', k)


if __name__ == '__main__':
    main()
