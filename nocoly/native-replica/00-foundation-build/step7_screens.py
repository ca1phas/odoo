"""Wave 0 (plan v2 §5), step 5 of §9: native screens.

1. Read-only fields: values the workflows maintain (fieldPermission "101": visible / not editable / shown on create).
2. Business rules (interaction, "hide" form so two rules never fight over one field): Odoo's invisible= attributes.
3. Views: kanban / gallery / hierarchy / calendar / filtered tables (plan §5).
Run: python step7_screens.py [readonly] [rules] [views]
"""
import json, sys
from lib import hap, APP, record
from sheetlib import by_alias, apply_spec
from wflib import S, F, option_key

STEP = 'v2 step 5 (screens)'
READONLY = '101'

AUTO_FIELDS = {
    'res_partner': ['complete_name', 'country_id', 'commercial_partner_id', 'commercial_company_name'],
    'uom_uom': ['factor', 'parent_path', 'x_uom__level'],
    'product_category': ['complete_name', 'parent_path'],
    'product_product': ['display_name', 'lst_price', 'combination_indices', 'x_product__run'],
    'product_template_attribute_value': ['x_product__key', 'x_product__run'],
    'product_template_attribute_line': ['x_product__label'],
    'product_pricelist_item': ['name', 'price'],
    'mail_activity': ['x_mail__state', 'date_done', 'x_mail__done_by'],
    'x_mail__plan_launch': ['x_mail__name', 'x_mail__status', 'x_mail__message', 'x_mail__res_model', 'x_mail__res_id', 'x_mail__res_name'],
    'x_product__price_check': ['x_product__name', 'x_product__price', 'x_product__rule_id', 'x_product__rule_label'],
    'res_currency': ['rate', 'inverse_rate', 'rate_date'],
}


def readonly():
    n = 0
    for sheet, aliases in AUTO_FIELDS.items():
        have = by_alias(S[sheet])
        for a in aliases:
            c = have[a]
            if c.get('fieldPermission') not in (READONLY, '100'):   # '100' = also hidden on create (step9, 24 Nov)
                apply_spec([{'type': 'field.update', 'worksheet': S[sheet], 'field': c['controlId'], 'set': {'fieldPermission': READONLY}}])
                n += 1
    return n


def rules_of(sheet):
    d = hap('worksheet', 'rules', S[sheet])
    d = d.get('data', d) if isinstance(d, dict) else d
    return d if isinstance(d, list) else (d.get('rules') or [])


def hide_rule(sheet, name, filters, aliases):
    if any(r.get('name') == name for r in rules_of(sheet)):
        return 'exists'
    hap('worksheet', 'save-rule', S[sheet], '--name', name, '--type', '0', '--filters', json.dumps(filters),
        '--rule-items', json.dumps([{'action': 'hide', 'fields': [F(sheet, a) for a in aliases]}]))
    return 'created'


def when(sheet, alias, op, label=None):
    item = {'field': F(sheet, alias), 'op': op}
    if label is not None:
        item['value'] = option_key(sheet, alias, label)
    return {'logic': 'and', 'items': [item]}


def rules():
    out = []
    C, P, R = 'res_partner', 'product_template', 'product_pricelist_item'
    out.append(hide_rule(C, 'Company: hide person fields', when(C, 'company_type', 'eq', 'Company'), ['parent_id', 'function', 'type']))
    out.append(hide_rule(C, 'Person: hide company fields', when(C, 'company_type', 'eq', 'Person'), ['industry_id']))
    out.append(hide_rule(P, 'Not goods: hide Track Inventory', when(P, 'type', 'ne', 'Goods'), ['is_storable']))
    out.append(hide_rule(P, 'Not a combo: hide Combo Choices', when(P, 'type', 'ne', 'Combo'), ['combo_ids']))
    out.append(hide_rule(R, 'Not on a category', when(R, 'applied_on', 'ne', 'Product Category'), ['categ_id']))
    out.append(hide_rule(R, 'Not on a product', when(R, 'applied_on', 'ne', 'Product'), ['product_tmpl_id']))
    out.append(hide_rule(R, 'Not on a variant', when(R, 'applied_on', 'ne', 'Product Variant'), ['product_id']))
    out.append(hide_rule(R, 'Fixed price: hide formula fields', when(R, 'compute_price', 'eq', 'Fixed Price'),
                         ['base', 'base_pricelist_id', 'price_discount', 'price_markup', 'price_round', 'price_surcharge',
                          'price_min_margin', 'price_max_margin']))
    out.append(hide_rule(R, 'Not fixed: hide Fixed Price', when(R, 'compute_price', 'ne', 'Fixed Price'), ['fixed_price']))
    out.append(hide_rule(R, 'Not a discount: hide Discount', when(R, 'compute_price', 'ne', 'Discount'), ['price_discount']))
    out.append(hide_rule(R, 'Not a surcharge: hide Surcharge', when(R, 'compute_price', 'ne', 'Surcharge'), ['price_markup']))
    out.append(hide_rule(R, 'Not on another pricelist', when(R, 'base', 'ne', 'Other Pricelist'), ['base_pricelist_id']))
    return out


def views_of(sheet):
    d = hap('worksheet', 'view', 'list', S[sheet], '-a', APP)
    d = d.get('data', d) if isinstance(d, dict) else d
    return d if isinstance(d, list) else (d.get('views') or [])


def view(sheet, name, *args):
    if any(v.get('name') == name for v in views_of(sheet)):
        return 'exists'
    r = hap('worksheet', 'view', 'create', S[sheet], name, '-a', APP, *args)
    r = r.get('data', r)
    vid = r.get('viewId') or r.get('id')
    if vid:
        record(vid, 'view', f'{sheet}.{name}', None, STEP)
    return 'created'


def views():
    out = []
    C, A = 'res_partner', 'mail_activity'
    out.append(view(C, 'Cards', '--view-type', 'gallery', '--cover-control', F(C, 'image_1920')))
    out.append(view(C, 'Companies & People', '--view-type', 'structure', '--child-type', '1', '--group-control', F(C, 'parent_id')))
    out.append(view('uom_uom', 'Unit Chains', '--view-type', 'structure', '--child-type', '1', '--group-control', F('uom_uom', 'relative_uom_id')))
    out.append(view('product_category', 'Category Tree', '--view-type', 'structure', '--child-type', '1',
                    '--group-control', F('product_category', 'parent_id')))
    out.append(view('product_template', 'Cards', '--view-type', 'gallery', '--cover-control', F('product_template', 'image_1920')))
    out.append(view(A, 'My Activities', '--view-type', 'board', '--group-control', F(A, 'x_mail__state'), '--filter-json', json.dumps(
        {'logic': 'and', 'items': [{'field': F(A, 'user_id'), 'op': 'self'}, {'field': F(A, 'active'), 'op': 'eq', 'value': '1'}]})))
    out.append(view(A, 'Calendar', '--view-type', 'calendar', '--begin-date', F(A, 'date_deadline')))
    out.append(view(A, 'Overdue', '--view-type', 'sheet', '--filter-json', json.dumps(
        {'logic': 'and', 'items': [{'field': F(A, 'x_mail__state'), 'op': 'eq', 'value': option_key(A, 'x_mail__state', 'Overdue')},
                                   {'field': F(A, 'active'), 'op': 'eq', 'value': '1'}]})))
    return out


if __name__ == '__main__':
    todo = sys.argv[1:] or ['readonly', 'rules', 'views']
    if 'readonly' in todo:
        print('read-only fields set:', readonly())
    if 'rules' in todo:
        print('rules:', rules())
    if 'views' in todo:
        print('views:', views())
