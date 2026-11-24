"""Wave 0, step 3 (demo part): export the demo subset from the local Odoo 20 into data/demo.json. Read-only.

Subset (00-foundation.md §8, decision 5 of v1), chosen by the module that owns each row (ir_model_data):
- contacts: the main company's partner and people, and the 7 demo companies owned by `base` with their people
  (system and user partners such as OdooBot or Mitchell Admin are left out);
- the main company (res.company 1);
- product attributes and values owned by `product`; the 34 product templates owned by `product` with their
  attribute lines, template attribute values (extra prices) and variants;
- combos whose items are all product-owned (3 of Odoo's 8; the other 5 belong to point_of_sale / pos_restaurant);
- the 4 demo pricelists and their rules (owned by website_sale; loaded as test data);
- activity types owned by `mail` (from data/activity_types.csv) and the 2 demo activity plans (owned by `hr`).
Odoo ids are kept as "oid" keys; the loader maps them to HAP record ids.
Needs Docker Desktop and the local Odoo database (external/odoo20-local).
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
COMPOSE = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..', 'external', 'odoo20-local', 'docker-compose.yml'))


def rows(sql):
    q = f"SELECT coalesce(json_agg(t), '[]'::json) FROM ({' '.join(sql.split())}) t"
    r = subprocess.run(['docker', 'compose', '-f', COMPOSE, 'exec', '-T', 'db', 'psql', '-U', 'odoo', '-d', 'odoo20',
                        '-v', 'ON_ERROR_STOP=1', '-At', '-c', q], capture_output=True)
    if r.returncode:
        sys.exit(r.stderr.decode('utf-8', 'replace'))
    return json.loads(r.stdout.decode('utf-8'))


def owned(model, alias, module):
    return f"EXISTS (SELECT 1 FROM ir_model_data d WHERE d.model = '{model}' AND d.res_id = {alias}.id AND d.module = '{module}')"


PARTNER_COLS = """p.id AS oid, p.name, p.is_company, p.type, p.function, p.email, p.phone, p.website, p.street, p.street2,
    p.zip, p.city, s.code AS state, c.code AS country, p.vat, p.ref, p.lang, p.comment, p.parent_id AS parent,
    p.commercial_partner_id AS commercial, p.commercial_company_name, p.complete_name, p.employee, p.barcode, p.active,
    (SELECT name->>'en_US' FROM res_partner_industry i WHERE i.id = p.industry_id) AS industry,
    (SELECT json_agg(CASE WHEN cat.parent_id IS NULL THEN cat.name->>'en_US'
                     ELSE (SELECT pc.name->>'en_US' FROM res_partner_category pc WHERE pc.id = cat.parent_id) || ' / ' || (cat.name->>'en_US') END)
       FROM res_partner_res_partner_category_rel r JOIN res_partner_category cat ON cat.id = r.category_id
      WHERE r.partner_id = p.id) AS tags"""

SQL = {
    'company': """SELECT co.id AS oid, co.name, co.partner_id AS partner, co.report_header, co.report_footer, co.company_details,
        co.primary_color, co.secondary_color, cur.name AS currency FROM res_company co JOIN res_currency cur ON cur.id = co.currency_id
        WHERE co.id = 1""",
    'contacts': f"""SELECT {PARTNER_COLS} FROM res_partner p LEFT JOIN res_country_state s ON s.id = p.state_id
        LEFT JOIN res_country c ON c.id = p.country_id
        WHERE p.id = (SELECT partner_id FROM res_company WHERE id = 1)
           OR p.parent_id = (SELECT partner_id FROM res_company WHERE id = 1)
           OR (p.is_company AND {owned('res.partner', 'p', 'base')})
           OR p.parent_id IN (SELECT q.id FROM res_partner q WHERE q.is_company AND {owned('res.partner', 'q', 'base')})
        ORDER BY p.parent_id NULLS FIRST, p.id""",
    'attributes': f"""SELECT a.id AS oid, a.name->>'en_US' AS name, a.create_variant, a.display_type, a.sequence, a.active,
        (SELECT json_agg(json_build_object('oid', v.id, 'name', v.name->>'en_US', 'html_color', v.html_color,
                 'is_custom', v.is_custom, 'default_extra_price', v.default_extra_price, 'sequence', v.sequence, 'active', v.active)
                 ORDER BY v.sequence, v.id) FROM product_attribute_value v WHERE v.attribute_id = a.id) AS values
        FROM product_attribute a WHERE {owned('product.attribute', 'a', 'product')} ORDER BY a.sequence, a.id""",
    'products': f"""SELECT t.id AS oid, t.name->>'en_US' AS name, t.type, t.is_storable, t.list_price,
        (SELECT complete_name FROM (WITH RECURSIVE r AS (SELECT id, parent_id, (name->>'en_US')::text AS n FROM product_category
          WHERE parent_id IS NULL UNION ALL SELECT c.id, c.parent_id, r.n || ' / ' || (c.name->>'en_US') FROM product_category c JOIN r ON c.parent_id = r.id)
          SELECT n AS complete_name, id FROM r) x WHERE x.id = t.categ_id) AS categ,
        t.default_code, t.barcode, t.sale_ok, t.purchase_ok, (SELECT name->>'en_US' FROM uom_uom u WHERE u.id = t.uom_id) AS uom,
        (SELECT json_agg(u.name->>'en_US') FROM product_template_uom_uom_rel r JOIN uom_uom u ON u.id = r.uom_uom_id
          WHERE r.product_template_id = t.id) AS uoms,
        t.description, t.description_sale->>'en_US' AS description_sale, t.description_purchase->>'en_US' AS description_purchase,
        t.weight, t.volume, t.is_favorite, t.sequence, t.active,
        (SELECT json_agg(r.product_combo_id) FROM product_combo_product_template_rel r WHERE r.product_template_id = t.id) AS combos,
        (SELECT json_agg(json_build_object('oid', l.id, 'attribute', l.attribute_id, 'sequence', l.sequence, 'active', l.active,
                 'values', (SELECT json_agg(r.product_attribute_value_id) FROM product_attribute_value_product_template_attribute_line_rel r
                            WHERE r.product_template_attribute_line_id = l.id)) ORDER BY l.sequence, l.id)
           FROM product_template_attribute_line l WHERE l.product_tmpl_id = t.id) AS lines,
        (SELECT json_agg(json_build_object('oid', v.id, 'value', v.product_attribute_value_id, 'line', v.attribute_line_id,
                 'price_extra', v.price_extra, 'active', v.ptav_active, 'sequence', v.sequence))
           FROM product_template_attribute_value v WHERE v.product_tmpl_id = t.id) AS ptavs,
        (SELECT json_agg(json_build_object('oid', p.id, 'default_code', p.default_code, 'barcode', p.barcode,
                 'standard_price', (SELECT (value)::float FROM jsonb_each_text(p.standard_price) LIMIT 1),
                 'weight', p.weight, 'volume', p.volume, 'active', p.active, 'is_favorite', p.is_favorite,
                 'combination_indices', p.combination_indices,
                 'ptavs', (SELECT json_agg(r.product_template_attribute_value_id) FROM product_variant_combination r
                           WHERE r.product_product_id = p.id)) ORDER BY p.id)
           FROM product_product p WHERE p.product_tmpl_id = t.id) AS variants
        FROM product_template t WHERE {owned('product.template', 't', 'product')} ORDER BY t.id""",
    'combos': """SELECT c.id AS oid, c.name->>'en_US' AS name, c.sequence,
        (SELECT json_agg(json_build_object('product', i.product_id, 'extra_price', i.extra_price) ORDER BY i.id)
           FROM product_combo_item i WHERE i.combo_id = c.id) AS items
        FROM product_combo c WHERE NOT EXISTS (SELECT 1 FROM product_combo_item i JOIN product_product p ON p.id = i.product_id
          WHERE i.combo_id = c.id AND NOT EXISTS (SELECT 1 FROM ir_model_data d WHERE d.model = 'product.template'
          AND d.res_id = p.product_tmpl_id AND d.module = 'product')) ORDER BY c.id""",
    'pricelists': """SELECT pl.id AS oid, pl.name->>'en_US' AS name, cur.name AS currency, pl.sequence, pl.active,
        (SELECT json_agg(g.name->>'en_US') FROM res_country_group_pricelist_rel r JOIN res_country_group g ON g.id = r.res_country_group_id
          WHERE r.pricelist_id = pl.id) AS country_groups,
        (SELECT json_agg(json_build_object('oid', i.id, 'applied_on', i.applied_on, 'categ', i.categ_id, 'product_tmpl', i.product_tmpl_id,
                 'product', i.product_id, 'min_quantity', i.min_quantity, 'date_start', i.date_start, 'date_end', i.date_end,
                 'compute_price', i.compute_price, 'fixed_price', i.fixed_price, 'base', i.base, 'base_pricelist', i.base_pricelist_id,
                 'price_discount', i.price_discount, 'price_round', i.price_round, 'price_surcharge', i.price_surcharge,
                 'price_min_margin', i.price_min_margin, 'price_max_margin', i.price_max_margin) ORDER BY i.id)
           FROM product_pricelist_item i WHERE i.pricelist_id = pl.id) AS items
        FROM product_pricelist pl JOIN res_currency cur ON cur.id = pl.currency_id ORDER BY pl.id""",
    'plans': """SELECT p.id AS oid, p.name, p.res_model, p.active,
        (SELECT json_agg(json_build_object('summary', t.summary, 'type', (SELECT name->>'en_US' FROM mail_activity_type a WHERE a.id = t.activity_type_id),
                 'responsible_type', t.responsible_type, 'delay_count', t.delay_count, 'delay_unit', t.delay_unit,
                 'delay_from', t.delay_from, 'note', t.note, 'sequence', t.sequence) ORDER BY t.sequence, t.id)
           FROM mail_activity_plan_template t WHERE t.plan_id = p.id) AS steps
        FROM mail_activity_plan p ORDER BY p.id""",
    'categories': """SELECT id AS oid, name->>'en_US' AS name FROM product_category""",
}

if __name__ == '__main__':
    out = {k: rows(v) for k, v in SQL.items()}
    json.dump(out, open(os.path.join(HERE, 'data', 'demo.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print({k: len(v) for k, v in out.items()})
