"""Wave 0 (plan v2), step 4f: Pricelists, Pricelist Rules (subform), Combo Choices, Combo Items (subform).

Odoo 20 source (product/models/product_pricelist_item.py, read 23 Nov 2026) replaces plan v2's rule types:
compute_price is Discount / Surcharge / Fixed Price (no "Formula"). Discount and Surcharge share the old formula
(base - base x discount %, rounding, extra fee, min / max margin); Surcharge is stored as a negative discount.
Rule order: applied_on, min_quantity desc, categ_id desc, id desc. Category rules also match sub-categories.
Rule helper fields for the #12 search (hidden) are written by the rule flow.
Run: python step4f_pricelists_combos.py
"""
from lib import hap, APP, record
from sheetlib import (F, ensure_sheet, ensure_reverse, raw_fields, apply_spec, sheets_by_alias, add_once, set_show,
                      by_alias, HIDDEN)
from step4e_products import money, mount

STEP = 'v2 step 4f'
AUTO = 'Kept up to date automatically.'
ON = [{'source': 'static', 'value': '1'}]

PRICELISTS = {
    'name': 'Pricelists', 'alias': 'product_pricelist', 'module': 'product', 'group': 'Products', 'icon': 'sys_1_2_order',
    'title': 'Pricelist Name',
    'desc': 'Price rules for customers, countries or periods: discounts, surcharges and fixed prices.',
    'fields': [
        F('Pricelist Name', 'TEXT', 'name', required=True),
        F('Currency', 'RELATE_SHEET', 'currency_id', dataSource='@res_currency', multi=False, required=True,
          config={'displayMode': 'dropdown'}),
        F('Country Groups', 'RELATE_SHEET', 'country_group_ids', dataSource='@res_country_group', multi=True,
          config={'bidirectional': True, 'reverseName': 'Pricelists', 'displayMode': 'dropdown'},
          desc='Customers in these countries get this pricelist by default.'),
        F('Sequence', 'NUMBER', 'sequence', dot=0),
        F('Active', 'SWITCH', 'active', defaultValue=ON),
        F('Chain', 'TEXT', 'x_product__chain', desc='Pricelists this one is based on, to stop loops. ' + AUTO),
    ],
}

RULES = {
    'name': 'Pricelist Rules', 'alias': 'product_pricelist_item', 'module': 'product', 'group': 'System Tables',
    'icon': 'sys_folder-money_office', 'title': 'Applies To',
    'desc': 'One price rule of a pricelist. Edited inside the pricelist.',
    'fields': [
        F('Applies To', 'TEXT', 'name', desc='What the rule applies to, for example "Category: Office". ' + AUTO),
        F('Apply On', 'DROP_DOWN', 'applied_on', options=['All Products', 'Product Category', 'Product', 'Product Variant'],
          defaultValue=[{'source': 'static', 'value': 'All Products'}], required=True),
        F('Category', 'RELATE_SHEET', 'categ_id', dataSource='@product_category', multi=False,
          config={'displayMode': 'dropdown'}, desc='Also applies to its sub-categories.'),
        F('Product', 'RELATE_SHEET', 'product_tmpl_id', dataSource='@product_template', multi=False,
          config={'displayMode': 'dropdown'}),
        F('Variant', 'RELATE_SHEET', 'product_id', dataSource='@product_product', multi=False, config={'displayMode': 'dropdown'}),
        F('Packaging', 'RELATE_SHEET', 'uom_id', dataSource='@uom_uom', multi=False, config={'displayMode': 'dropdown'},
          desc='Only when selling in this unit. Leave empty for any unit.'),
        F('Min. Quantity', 'NUMBER', 'min_quantity', dot=2, desc='In the product\'s unit.'),
        F('Start Date', 'DATE_TIME', 'date_start'),
        F('End Date', 'DATE_TIME', 'date_end'),
        F('Price Type', 'DROP_DOWN', 'compute_price', options=['Discount', 'Surcharge', 'Fixed Price'],
          defaultValue=[{'source': 'static', 'value': 'Discount'}], required=True),
        money('Fixed Price', 'fixed_price', 'In the product\'s unit.'),
        F('Based On', 'DROP_DOWN', 'base', options=['Sales Price', 'Cost', 'Other Pricelist'],
          defaultValue=[{'source': 'static', 'value': 'Sales Price'}]),
        F('Other Pricelist', 'RELATE_SHEET', 'base_pricelist_id', dataSource='@product_pricelist', multi=False,
          config={'displayMode': 'dropdown'}),
        F('Discount', 'NUMBER', 'price_discount', dot=2, advanced_setting={'showtype': '0', 'suffix': '%'},
          desc='Percentage taken off the base price.'),
        F('Surcharge', 'NUMBER', 'price_markup', dot=2, advanced_setting={'showtype': '0', 'suffix': '%'},
          desc='Percentage added to the base price (Odoo stores it as a negative discount).'),
        money('Price Rounding', 'price_round', 'The price becomes a multiple of this, before the extra fee. '
              'For prices ending in 9.99: round to 10.00, extra fee -0.01.'),
        money('Extra Fee', 'price_surcharge', 'Fixed amount added (or taken off, if negative) after rounding.'),
        money('Min. Price Margin', 'price_min_margin', 'Smallest margin over the base price.'),
        money('Max. Price Margin', 'price_max_margin', 'Largest margin over the base price.'),
        F('Price', 'TEXT', 'price', desc='The rule in words, for example "10% discount on sales price". ' + AUTO),
        # helpers for the #12 rule search (native-catalogue/workflow-nodes.md §5.3), hidden
        F('Rank', 'NUMBER', 'x_product__rank', dot=0, desc='0 variant, 1 product, 2 category, 3 all products. ' + AUTO),
        F('Target Key', 'TEXT', 'x_product__target_key', desc='Record id of the variant, product or category, or ALL. ' + AUTO),
        F('Category Sort Key', 'NUMBER', 'x_product__categ_sort', dot=0, desc='Category Number, for Odoo\'s order. ' + AUTO),
        F('Effective Start', 'DATE_TIME', 'x_product__effective_start', desc='Start Date, or 1900-01-01. ' + AUTO),
        F('Effective End', 'DATE_TIME', 'x_product__effective_end', desc='End Date, or 2999-12-31. ' + AUTO),
        F('Rule Number', 'AUTO_ID', 'x_product__number', desc='Creation order; the newest rule wins a tie, as in Odoo.'),
    ],
}
RULE_HELPERS = ['x_product__rank', 'x_product__target_key', 'x_product__categ_sort', 'x_product__effective_start',
                'x_product__effective_end']

COMBOS = {
    'name': 'Combo Choices', 'alias': 'product_combo', 'module': 'product', 'group': 'Products/Configuration',
    'icon': 'sys_folder-edit_office', 'title': 'Name',
    'desc': 'A choice inside a combo product, for example "Desks": the customer picks one of its items.',
    'fields': [
        F('Name', 'TEXT', 'name', required=True),
        F('Sequence', 'NUMBER', 'sequence', dot=0),
    ],
}

COMBO_ITEMS = {
    'name': 'Combo Items', 'alias': 'product_combo_item', 'module': 'product', 'group': 'System Tables',
    'icon': 'sys_14_2_birthday', 'title': 'Item',
    'desc': 'One product a combo choice offers, with its extra price. Edited inside the combo choice.',
    'fields': [
        F('Item', 'TEXT', 'x_product__label', desc='The variant\'s name. ' + AUTO),
        F('Options', 'RELATE_SHEET', 'product_id', dataSource='@product_product', multi=False, required=True,
          config={'displayMode': 'dropdown'}, desc='The product variant offered.'),
        money('Extra Price', 'extra_price', 'Added to the combo price when this item is chosen.'),
    ],
}


def hide(ws, aliases):
    have = by_alias(ws)
    n = 0
    for a in aliases:
        if have[a].get('fieldPermission') != HIDDEN:
            apply_spec([{'type': 'field.update', 'worksheet': ws, 'field': have[a]['controlId'], 'set': {'fieldPermission': HIDDEN}}])
            n += 1
    return n


def company(ws, label):
    return add_once(ws, {'type': 29, 'controlName': 'Company', 'alias': 'company_id', 'dataSource': sheets['res_company']['id'],
                         'enumDefault': 1, 'fieldPermission': HIDDEN, 'advancedSetting': {'showtype': '3'},
                         'desc': 'Hidden while there is one company.'}, 'product', f'{label}.Company', STEP)


if __name__ == '__main__':
    sheets = sheets_by_alias()
    plws, plraw, f1 = ensure_sheet(PRICELISTS, STEP)
    pl = {c.get('alias'): c for c in plraw}
    rev = ensure_reverse(sheets['res_country_group']['id'], pl['country_group_ids']['controlId'], 'pricelist_ids', 'Pricelists',
                         'product', None, STEP)
    company(plws, 'Pricelists')
    rws, _, f2 = ensure_sheet(RULES, STEP)
    hidden = hide(rws, RULE_HELPERS) + hide(plws, ['x_product__chain'])
    r = by_alias(rws)
    sub, back = mount(plws, rws, 'Rules', 'Pricelist',
                      [r[a]['controlId'] for a in ('applied_on', 'categ_id', 'product_tmpl_id', 'product_id', 'min_quantity',
                                                   'compute_price', 'price', 'date_start', 'date_end')],
                      'item_ids', 'pricelist_id', 'product', 'Pricelists', 'Pricelist Rules')
    print('Pricelists', plws, '| Rules', rws, '| subform', sub['controlId'], '| back', back['controlId'],
          '| country-group reverse', rev['controlId'], '| fixes', f1, f2, '| hidden', hidden)

    cws, _, f3 = ensure_sheet(COMBOS, STEP)
    company(cws, 'Combo Choices')
    iws, _, f4 = ensure_sheet(COMBO_ITEMS, STEP)
    i = by_alias(iws)
    sub2, back2 = mount(cws, iws, 'Items', 'Combo', [i[a]['controlId'] for a in ('product_id', 'extra_price')],
                        'combo_item_ids', 'combo_id', 'product', 'Combo Choices', 'Combo Items')
    print('Combo Choices', cws, '| Combo Items', iws, '| subform', sub2['controlId'], '| back', back2['controlId'], '| fixes', f3, f4)

    # Products: Combo Choices (for Combo products)
    pws = sheets['product_template']['id']
    add_once(pws, {'type': 29, 'controlName': 'Combo Choices', 'alias': 'combo_ids', 'dataSource': cws, 'enumDefault': 2,
                   'desc': 'For a Combo product: the choices the customer makes.', 'advancedSetting': {'showtype': '2'}},
             'product', 'Products.Combo Choices', STEP)
    print('Products: Combo Choices added')
