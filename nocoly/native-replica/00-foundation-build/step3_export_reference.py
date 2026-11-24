"""Wave 0, step 3: export the reference data from the local Odoo 20 (00-foundation.md §8). Read-only.

Writes data/<name>.csv. English names (en_US). xmlid = Odoo's external id, kept as a stable key for later imports.
Needs Docker Desktop and the local Odoo (external/odoo20-local).
"""
import csv, io, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
COMPOSE = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..', 'external', 'odoo20-local', 'docker-compose.yml'))
OUT = os.path.join(HERE, 'data')


def xmlid(model, alias):
    return (f"(SELECT d.module || '.' || d.name FROM ir_model_data d WHERE d.model = '{model}' AND d.res_id = {alias}.id "
            f"ORDER BY d.id LIMIT 1)")


QUERIES = {
    'countries': f"""SELECT {xmlid('res.country', 'c')} AS xmlid, c.code, c.name->>'en_US' AS name, c.phone_code,
        cur.name AS currency, c.vat_label->>'en_US' AS vat_label, c.state_required, c.zip_applicability, c.name_position,
        c.address_format
        FROM res_country c LEFT JOIN res_currency cur ON cur.id = c.currency_id ORDER BY c.name->>'en_US'""",
    'states': f"""SELECT {xmlid('res.country.state', 's')} AS xmlid, c.code AS country_code, s.code, s.name
        FROM res_country_state s JOIN res_country c ON c.id = s.country_id ORDER BY c.code, s.name""",
    'country_groups': f"""SELECT {xmlid('res.country.group', 'g')} AS xmlid, g.code, g.name->>'en_US' AS name,
        (SELECT string_agg(c.code, ' ' ORDER BY c.code) FROM res_country_res_country_group_rel r JOIN res_country c
         ON c.id = r.res_country_id WHERE r.res_country_group_id = g.id) AS countries
        FROM res_country_group g ORDER BY g.name->>'en_US'""",
    'currencies': f"""SELECT {xmlid('res.currency', 'c')} AS xmlid, c.name, c.symbol, c.full_name, c.iso_numeric, c.decimal_places,
        c.rounding, c.position, c.currency_unit_label->>'en_US' AS currency_unit_label,
        c.currency_subunit_label->>'en_US' AS currency_subunit_label, c.active
        FROM res_currency c ORDER BY c.active DESC, c.name""",
    'currency_rates': """SELECT c.name AS currency, r.name AS date, r.rate, r.company_id
        FROM res_currency_rate r JOIN res_currency c ON c.id = r.currency_id ORDER BY c.name, r.name""",
    'units': f"""SELECT {xmlid('uom.uom', 'u')} AS xmlid, u.name->>'en_US' AS name, u.relative_factor,
        p.name->>'en_US' AS relative_uom, u.factor, u.active, u.sequence, u.parent_path
        FROM uom_uom u LEFT JOIN uom_uom p ON p.id = u.relative_uom_id ORDER BY u.parent_path""",
    'product_categories': f"""WITH RECURSIVE t AS (
          SELECT id, parent_id, name->>'en_US' AS name, (name->>'en_US')::text AS complete_name FROM product_category WHERE parent_id IS NULL
          UNION ALL SELECT c.id, c.parent_id, c.name->>'en_US', t.complete_name || ' / ' || (c.name->>'en_US')
          FROM product_category c JOIN t ON c.parent_id = t.id)
        SELECT {xmlid('product.category', 't')} AS xmlid, t.name, p.name->>'en_US' AS parent, t.complete_name
        FROM t LEFT JOIN product_category p ON p.id = t.parent_id ORDER BY t.complete_name""",
    'activity_types': f"""SELECT {xmlid('mail.activity.type', 'a')} AS xmlid, a.name->>'en_US' AS name, a.summary->>'en_US' AS summary,
        a.icon, a.category, a.decoration_type, a.delay_count, a.delay_unit, a.delay_from, coalesce(a.res_model, '') AS res_model,
        n.name->>'en_US' AS suggested_next, a.default_note->>'en_US' AS default_note, a.active, a.sequence
        FROM mail_activity_type a LEFT JOIN mail_activity_type n ON n.id = a.suggested_next_type_id ORDER BY a.sequence, a.id""",
    'industries': f"""SELECT {xmlid('res.partner.industry', 'i')} AS xmlid, i.name->>'en_US' AS name, i.full_name->>'en_US' AS full_name, i.active
        FROM res_partner_industry i ORDER BY i.name->>'en_US'""",
}


def copy(sql):
    q = 'COPY (' + ' '.join(sql.split()) + ') TO STDOUT WITH CSV HEADER'
    r = subprocess.run(['docker', 'compose', '-f', COMPOSE, 'exec', '-T', 'db', 'psql', '-U', 'odoo', '-d', 'odoo20',
                        '-v', 'ON_ERROR_STOP=1', '-q', '-c', q], capture_output=True)
    if r.returncode:
        sys.exit(r.stderr.decode('utf-8', 'replace'))
    return r.stdout.decode('utf-8')


os.makedirs(OUT, exist_ok=True)
for name, sql in QUERIES.items():
    text = copy(sql)
    open(os.path.join(OUT, name + '.csv'), 'w', encoding='utf-8', newline='').write(text)
    rows = list(csv.DictReader(io.StringIO(text)))
    extra = ''
    if 'active' in (rows[0] if rows else {}):
        extra = f", active {sum(r['active'] == 't' for r in rows)}"
    print(f'{name:20} {len(rows):5} rows{extra}')
