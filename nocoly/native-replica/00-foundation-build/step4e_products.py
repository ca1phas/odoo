"""Wave 0 (plan v2), step 4e: the product sheets.

Attribute Values, Attributes (Values = subform on the existing Attribute Values sheet), Products, Attribute Lines
(subform on Products), Product Attribute Values (PTAV), Variants (two-way to Products), the Product Tags option set,
and the Product Count rollup on Product Categories. Odoo models: product.attribute(.value),
product.template(.attribute.line/.attribute.value), product.product, product.tag.

Native choices: MYR Currency fields; Level (1 star) for Favourite; Barcode display field fed by the barcode text;
multi-select with an option set for tags; Rollup for counts and the variants' extra-price sum (#11).
Subforms use `worksheet mount-subtable`, which also creates the child-side relation back to the parent; that
relation then gets the Odoo alias (attribute_id, product_tmpl_id).
Run: python step4e_products.py
"""
import json
from lib import hap, APP, record
from sheetlib import (F, ensure_sheet, ensure_reverse, raw_fields, apply_spec, sheets_by_alias, add_once, set_show,
                      by_alias, HIDDEN)

ON = [{'source': 'static', 'value': '1'}]
STEP = 'v2 step 4e'
AUTO = 'Kept up to date automatically.'
MYR = {'currency': '{"currencycode":"MYR","symbol":"RM"}', 'showformat': '1', 'roundtype': '2'}
TAG_SET_NAME = 'Product Tags'


def money(name, alias, desc='', **kw):
    return F(name, 'MONEY', alias, desc=desc, dot=2, advanced_setting=dict(MYR), **kw)


ATTR_VALUES = {
    'name': 'Attribute Values', 'alias': 'product_attribute_value', 'module': 'product', 'group': 'System Tables',
    'icon': 'sys_pins_traffic', 'title': 'Value',
    'desc': 'Values of a product attribute, for example Red or XL. Edited inside the attribute.',
    'fields': [
        F('Value', 'TEXT', 'name', required=True),
        F('Color', 'TEXT', 'html_color', desc='Hex colour shown for colour attributes, for example #FF0000.'),
        F('Free Text', 'SWITCH', 'is_custom', desc='The customer types their own value, for example an engraving text.'),
        money('Default Extra Price', 'default_extra_price', 'Added to the sales price of new variants with this value.'),
        F('Sequence', 'NUMBER', 'sequence', dot=0),
        F('Active', 'SWITCH', 'active', defaultValue=ON),
    ],
}

ATTRIBUTES = {
    'name': 'Attributes', 'alias': 'product_attribute', 'module': 'product', 'group': 'Products/Configuration',
    'icon': 'sys_grain-effect_symbol', 'title': 'Attribute',
    'desc': 'Product attributes such as Color or Size, with their values.',
    'fields': [
        F('Attribute', 'TEXT', 'name', required=True),
        F('Display Type', 'DROP_DOWN', 'display_type', options=['Radio', 'Pills', 'Select', 'Color', 'Multi-checkbox'],
          defaultValue=[{'source': 'static', 'value': 'Radio'}], desc='How the values are shown when a product is configured.'),
        F('Variant Creation', 'FLAT_MENU', 'create_variant', options=['Instantly', 'Dynamically', 'Never'],
          defaultValue=[{'source': 'static', 'value': 'Instantly'}],
          desc='Instantly: all variants are created when the product is saved. Dynamically: only when ordered. '
               'Never: the value is only noted on the order line.'),
        F('Sequence', 'NUMBER', 'sequence', dot=0),
        F('Active', 'SWITCH', 'active', defaultValue=ON),
    ],
}

PRODUCTS = {
    'name': 'Products', 'alias': 'product_template', 'module': 'product', 'group': 'Products', 'icon': 'sys_bag_clothes',
    'title': 'Name',
    'desc': 'Goods, services and combos you sell or buy. Products with attributes have variants.',
    'fields': [
        F('Name', 'TEXT', 'name', required=True),
        F('Product Type', 'FLAT_MENU', 'type', options=['Goods', 'Service', 'Combo'],
          defaultValue=[{'source': 'static', 'value': 'Goods'}],
          desc='Goods: physical items. Service: work or time. Combo: a set of choices sold as one product.'),
        F('Track Inventory', 'SWITCH', 'is_storable', desc='Keep stock quantities for this product (goods only).'),
        F('Product Category', 'RELATE_SHEET', 'categ_id', dataSource='@product_category', multi=False,
          config={'bidirectional': True, 'reverseName': 'Products', 'displayMode': 'dropdown'}),
        money('Sales Price', 'list_price', 'Price before pricelist rules and variant extras.'),
        money('Cost', 'standard_price', 'Cost of one unit, used for margins and cost-based pricelists.'),
        F('Internal Reference', 'TEXT', 'default_code'),
        F('Barcode', 'TEXT', 'barcode', desc='Scan or type it. Must be unique across products and variants.'),
        F('Sales', 'SWITCH', 'sale_ok', defaultValue=ON, desc='Can be sold.'),
        F('Purchase', 'SWITCH', 'purchase_ok', defaultValue=ON, desc='Can be purchased.'),
        F('Unit', 'RELATE_SHEET', 'uom_id', dataSource='@uom_uom', multi=False, required=True,
          config={'displayMode': 'dropdown'}, desc='Unit used for stock, sales and purchases.'),
        F('Packagings', 'RELATE_SHEET', 'uom_ids', dataSource='@uom_uom', multi=True,
          desc='Other units this product is sold or bought in, for example Pack of 6.'),
        F('Description', 'RICH_TEXT', 'description', desc='Internal notes.'),
        F('Sales Description', 'TEXT', 'description_sale', extra={'enumDefault': 1},
          desc='Printed on quotations and invoices.'),
        F('Purchase Description', 'TEXT', 'description_purchase', extra={'enumDefault': 1},
          desc='Printed on purchase orders.'),
        F('Weight', 'NUMBER', 'weight', dot=2, advanced_setting={'showtype': '0', 'suffix': 'kg'}),
        F('Volume', 'NUMBER', 'volume', dot=4, advanced_setting={'showtype': '0', 'suffix': 'm³'}),
        F('Image', 'ATTACHMENT', 'image_1920', advanced_setting={'filetype': '{"type":"1","values":[]}'}),
        F('Favorite', 'SCORE', 'is_favorite', advanced_setting={'max': '1', 'itemicon': 'star'}),
        F('Documents', 'ATTACHMENT', 'product_document_ids', desc='Data sheets, manuals and other files.'),
        F('Sequence', 'NUMBER', 'sequence', dot=0),
        F('Active', 'SWITCH', 'active', defaultValue=ON),
    ],
}

ATTR_LINES = {
    'name': 'Attribute Lines', 'alias': 'product_template_attribute_line', 'module': 'product', 'group': 'System Tables',
    'icon': 'sys_filter-organization_symbol', 'title': 'Line',
    'desc': 'One attribute of a product and the values it uses. Edited inside the product.',
    'fields': [
        F('Line', 'TEXT', 'x_product__label', desc='Attribute and values, for example "Color: Red, Blue". ' + AUTO),
        F('Attribute', 'RELATE_SHEET', 'attribute_id', dataSource='@product_attribute', multi=False, required=True,
          config={'displayMode': 'dropdown'}),
        F('Values', 'RELATE_SHEET', 'value_ids', dataSource='@product_attribute_value', multi=True, required=True,
          desc='Only values of the chosen attribute can be picked.'),
        F('Sequence', 'NUMBER', 'sequence', dot=0),
        F('Active', 'SWITCH', 'active', defaultValue=ON),
    ],
}

PTAV = {
    'name': 'Product Attribute Values', 'alias': 'product_template_attribute_value', 'module': 'product',
    'group': 'System Tables', 'icon': 'sys_pilcrow_finance', 'title': 'Value',
    'desc': 'One attribute value as used by one product, with its extra price. Created by the variant flow.',
    'fields': [
        F('Value', 'TEXT', 'name', desc='Value name. ' + AUTO),
        F('Product', 'RELATE_SHEET', 'product_tmpl_id', dataSource='@product_template', multi=False,
          config={'displayMode': 'dropdown'}),
        F('Attribute Value', 'RELATE_SHEET', 'product_attribute_value_id', dataSource='@product_attribute_value',
          multi=False, config={'displayMode': 'dropdown'}),
        F('Attribute', 'RELATE_SHEET', 'attribute_id', dataSource='@product_attribute', multi=False,
          config={'displayMode': 'dropdown'}),
        F('Attribute Line', 'RELATE_SHEET', 'attribute_line_id', dataSource='@product_template_attribute_line',
          multi=False, config={'displayMode': 'dropdown'}),
        money('Extra Price', 'price_extra', 'Added to the sales price of the variants that have this value.'),
        F('Active', 'SWITCH', 'ptav_active', defaultValue=ON),
        F('Key', 'TEXT', 'x_product__key', desc='Product id and value id, used to find this row again. ' + AUTO),
        F('Run', 'TEXT', 'x_product__run', desc='Last variant build that confirmed this row. ' + AUTO),
        F('Sequence', 'NUMBER', 'sequence', dot=0),
    ],
}

VARIANTS = {
    'name': 'Variants', 'alias': 'product_product', 'module': 'product', 'group': 'Products', 'icon': 'sys_ayout-grid_symbol',
    'title': 'Display Name',
    'desc': 'Each sellable combination of a product\'s attribute values. Created by the variant flow.',
    'fields': [
        F('Display Name', 'TEXT', 'display_name', desc='Product name with its values, for example "Desk (Steel, White)". ' + AUTO),
        F('Product', 'RELATE_SHEET', 'product_tmpl_id', dataSource='@product_template', multi=False, required=True,
          config={'bidirectional': True, 'reverseName': 'Variants', 'displayMode': 'dropdown'}),
        F('Attribute Values', 'RELATE_SHEET', 'product_template_attribute_value_ids',
          dataSource='@product_template_attribute_value', multi=True),
        F('Combination Key', 'TEXT', 'combination_indices', desc='Sorted ids of its attribute values. ' + AUTO),
        F('Internal Reference', 'TEXT', 'default_code'),
        F('Barcode', 'TEXT', 'barcode', desc='Scan or type it. Must be unique across products and variants.'),
        money('Cost', 'standard_price'),
        money('Sales Price', 'lst_price', 'Product price plus the extra prices of its values. ' + AUTO),
        F('Weight', 'NUMBER', 'weight', dot=2, advanced_setting={'showtype': '0', 'suffix': 'kg'}),
        F('Volume', 'NUMBER', 'volume', dot=4, advanced_setting={'showtype': '0', 'suffix': 'm³'}),
        F('Variant Image', 'ATTACHMENT', 'image_variant_1920', advanced_setting={'filetype': '{"type":"1","values":[]}'}),
        F('Favorite', 'SCORE', 'is_favorite', advanced_setting={'max': '1', 'itemicon': 'star'}),
        F('Active', 'SWITCH', 'active', defaultValue=ON),
        F('Run', 'TEXT', 'x_product__run', desc='Last variant build that confirmed this variant. ' + AUTO),
    ],
}


def tag_set():
    d = hap('app', 'optionset', 'list', '-a', APP)
    sets = (d.get('data') or d).get('optionsets', []) if isinstance(d, dict) else d
    for s in sets or []:
        if s.get('name') == TAG_SET_NAME:
            return s['id'], s.get('options') or []
    # An empty option set is refused (PLATFORM-ISSUES P7) and Odoo's demo has no product tags: one starter tag.
    hap('app', 'optionset', 'create', '-a', APP, '--name', TAG_SET_NAME, '--enable-color',
        '--options-json', json.dumps([{'value': 'Featured', 'index': 1, 'color': '#2196F3'}]))
    return tag_set()


def mount(parent, child, name, back_name, show_ids, field_alias, back_alias, module, parent_name, child_name):
    """Subform on an existing sheet; the child-side relation back to the parent gets back_alias."""
    have = by_alias(parent)
    if field_alias not in have:
        hap('worksheet', 'mount-subtable', parent, child, '--name', name, '-a', APP, '--back-relate-name', back_name,
            '--show-controls', ','.join(show_ids))
        have = by_alias(parent)
        sub = next(c for c in raw_fields(parent) if c['type'] == 34 and c['controlName'] == name)
        apply_spec([{'type': 'field.update', 'worksheet': parent, 'field': sub['controlId'], 'set': {'alias': field_alias}}])
        have = by_alias(parent)
    sub = have[field_alias]
    record(sub['controlId'], 'field', f'{parent_name}.{name}', module, STEP)
    back = next((c for c in hap('worksheet', 'fields', child, '-a', APP, '--raw', '--parent', parent)
                 if c['controlId'] == sub.get('sourceControlId')), None)
    if back is None:
        raise RuntimeError(f'no back relation for {name}')
    if back.get('alias') != back_alias:
        apply_spec([{'type': 'field.update', 'worksheet': child, 'field': back['controlId'],
                     'set': {'alias': back_alias, 'controlName': back_name}}])
    record(back['controlId'], 'field', f'{child_name}.{back_name}', module, STEP)
    return sub, back


if __name__ == '__main__':
    sheets = sheets_by_alias()

    vws, _, f1 = ensure_sheet(ATTR_VALUES, STEP)
    aws, _, f2 = ensure_sheet(ATTRIBUTES, STEP)
    v = by_alias(vws)
    sub, back = mount(aws, vws, 'Values', 'Attribute', [v[a]['controlId'] for a in ('name', 'html_color', 'default_extra_price', 'is_custom')],
                      'value_ids', 'attribute_id', 'product', 'Attributes', 'Attribute Values')
    print('Attribute Values', vws, '| Attributes', aws, '| subform', sub['controlId'], 'back', back['controlId'], 'fixes', f1, f2)

    pws, praw, f3 = ensure_sheet(PRODUCTS, STEP)
    p = {c.get('alias'): c for c in praw}
    rev = ensure_reverse(sheets['product_category']['id'], p['categ_id']['controlId'], 'x_product__product_ids', 'Products',
                         'product', '6', STEP)
    tag_id, tag_opts = tag_set()
    record(tag_id, 'optionset', TAG_SET_NAME, 'product', STEP)
    add_once(pws, {'type': 10, 'controlName': 'Tags', 'alias': 'product_tag_ids', 'dataSource': tag_id, 'enumDefault2': 1,
                   'options': [{'key': o['key'], 'value': o['value'], 'index': o.get('index', 1), 'color': o.get('color', '')}
                               for o in tag_opts],
                   'advancedSetting': {'checktype': '1', 'allowadd': '1'}}, 'product', 'Products.Tags', STEP)
    p = by_alias(pws)
    add_once(pws, {'type': 47, 'controlName': 'Barcode Image', 'alias': 'x_product__barcode_image', 'enumDefault': 1,
                   'dataSource': f"${p['barcode']['controlId']}$", 'advancedSetting': {'width': '160'}},
             'product', 'Products.Barcode Image', STEP)
    add_once(pws, {'type': 29, 'controlName': 'Company', 'alias': 'company_id', 'dataSource': sheets['res_company']['id'],
                   'enumDefault': 1, 'fieldPermission': HIDDEN, 'advancedSetting': {'showtype': '3'},
                   'desc': 'Hidden while there is one company.'}, 'product', 'Products.Company', STEP)
    print('Products', pws, 'fields', len(by_alias(pws)), 'fixes', f3, '| category reverse', rev['controlId'])

    lws, _, f4 = ensure_sheet(ATTR_LINES, STEP)
    l = by_alias(lws)
    add_once(lws, {'type': 30, 'controlName': 'Variant Creation', 'alias': 'x_product__create_variant',
                   'dataSource': f"${l['attribute_id']['controlId']}$", 'sourceControlId': by_alias(aws)['create_variant']['controlId'],
                   'sourceControlType': 11, 'strDefault': '00', 'desc': 'From the attribute.'},
             'product', 'Attribute Lines.Variant Creation', STEP)
    l = by_alias(lws)
    sub2, back2 = mount(pws, lws, 'Attributes & Variants', 'Product',
                        [l[a]['controlId'] for a in ('attribute_id', 'value_ids', 'x_product__create_variant')],
                        'attribute_line_ids', 'product_tmpl_id', 'product', 'Products', 'Attribute Lines')
    print('Attribute Lines', lws, 'fixes', f4, '| subform', sub2['controlId'], 'back', back2['controlId'])

    tws, _, f5 = ensure_sheet(PTAV, STEP)
    print('PTAV', tws, 'fixes', f5)

    xws, xraw, f6 = ensure_sheet(VARIANTS, STEP)
    x = {c.get('alias'): c for c in xraw}
    rev2 = ensure_reverse(pws, x['product_tmpl_id']['controlId'], 'product_variant_ids', 'Variants', 'product', '6', STEP)
    x = by_alias(xws)
    set_show(pws, rev2['controlId'], [x[a]['controlId'] for a in ('display_name', 'default_code', 'lst_price', 'active')])
    add_once(xws, {'type': 10, 'controlName': 'Variant Tags', 'alias': 'additional_product_tag_ids', 'dataSource': tag_id,
                   'enumDefault2': 1, 'options': [{'key': o['key'], 'value': o['value'], 'index': o.get('index', 1),
                                                   'color': o.get('color', '')} for o in tag_opts],
                   'advancedSetting': {'checktype': '1', 'allowadd': '1'}}, 'product', 'Variants.Variant Tags', STEP)
    add_once(xws, {'type': 47, 'controlName': 'Barcode Image', 'alias': 'x_product__barcode_image', 'enumDefault': 1,
                   'dataSource': f"${x['barcode']['controlId']}$", 'advancedSetting': {'width': '160'}},
             'product', 'Variants.Barcode Image', STEP)
    t = by_alias(tws)
    add_once(xws, {'type': 37, 'controlName': 'Variant Price Extra', 'alias': 'price_extra', 'enumDefault': 5, 'enumDefault2': 6,
                   'dot': 2, 'dataSource': f"${x['product_template_attribute_value_ids']['controlId']}$",
                   'sourceControlId': t['price_extra']['controlId'], 'advancedSetting': {'suffix': '', 'prefix': 'RM'},
                   'desc': 'Sum of the extra prices of its values.'}, 'product', 'Variants.Variant Price Extra', STEP)
    set_show(xws, x['product_template_attribute_value_ids']['controlId'],
             [t[a]['controlId'] for a in ('name', 'attribute_id', 'price_extra')])
    print('Variants', xws, 'fields', len(by_alias(xws)), 'fixes', f6, '| reverse on Products', rev2['controlId'])

    # Product Count on categories (Rollup: number of records in the Products reverse list)
    cws = sheets['product_category']['id']
    add_once(cws, {'type': 37, 'controlName': 'Product Count', 'alias': 'product_count', 'enumDefault': 6, 'enumDefault2': 6,
                   'dot': 0, 'dataSource': f"${rev['controlId']}$", 'sourceControlId': '',
                   'desc': 'Products in this category (not counting sub-categories).'}, 'product', 'Product Categories.Product Count', STEP)
    print('Product Categories: Product Count added')
