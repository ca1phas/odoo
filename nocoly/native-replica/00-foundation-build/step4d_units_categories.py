"""Wave 0 (plan v2), step 4d: Units (uom.uom) and Product Categories (product.category).

Both are trees: a single self-relation plus its reverse list (pair-relation, because add-fields alone makes one side:
PLATFORM-ISSUES P17). Factor, path, level, full name and ancestor keys are written by workflows #7 and #10
(native-catalogue/workflow-nodes.md §5.1 and #10), so they carry "Kept up to date automatically" and become
read-only on the form in the screens step. Helper fields that users never need are hidden (fieldPermission "011").
Run: python step4d_units_categories.py
"""
from sheetlib import F, ensure_sheet, ensure_self_relation, add_once, set_show, by_alias, HIDDEN

ON = [{'source': 'static', 'value': '1'}]
ONE = [{'source': 'static', 'value': '1'}]
STEP = 'v2 step 4d'
AUTO = 'Kept up to date automatically.'

UNITS = {
    'name': 'Units', 'alias': 'uom_uom', 'module': 'uom', 'group': 'Products/Configuration', 'icon': 'sys_math_office',
    'title': 'Unit Name',
    'desc': 'Units of measure. Each unit is defined from a reference unit: 1 Dozens contains 12 Units.',
    'fields': [
        F('Unit Name', 'TEXT', 'name', required=True),
        F('Contains', 'NUMBER', 'relative_factor', dot=6, required=True, defaultValue=ONE,
          desc='How many reference units one of this unit contains, for example 12 for Dozens. 1 when there is no reference unit.'),
        F('Absolute Quantity', 'NUMBER', 'factor', dot=6,
          desc='How many of the top unit of its chain this unit makes, for example 1000 for kg in g. ' + AUTO),
        F('Parent Path', 'TEXT', 'parent_path', desc='The chain of units from the top, by record id. ' + AUTO),
        F('Level', 'NUMBER', 'x_uom__level', dot=0, desc='Depth in the chain: 1 for a top unit. ' + AUTO),
        F('Sequence', 'NUMBER', 'sequence', dot=0),
        F('Active', 'SWITCH', 'active', defaultValue=ON),
    ],
}

CATEG = {
    'name': 'Product Categories', 'alias': 'product_category', 'module': 'product', 'group': 'Products/Configuration',
    'icon': 'sys_8_4_folder', 'title': 'Complete Name',
    'desc': 'Product categories, nested as in "Furniture / Office".',
    'fields': [
        F('Complete Name', 'TEXT', 'complete_name', desc='Full name with the parents, for example "Furniture / Office". ' + AUTO),
        F('Name', 'TEXT', 'name', required=True),
        F('Parent Path', 'TEXT', 'parent_path', desc='The chain of categories from the top, by record id. ' + AUTO),
        F('Category Number', 'AUTO_ID', 'x_product__number', desc='Creation order; pricelists use it to break ties, as Odoo does.'),
    ] + [F(f'Ancestor Key {i}', 'TEXT', f'x_product__ancestor_{i}',
           desc=f'Record id of the category {i - 1} level(s) up (1 = itself), for pricelist rules. ' + AUTO)
         for i in range(1, 6)],
}


def hide(ws, aliases):
    from sheetlib import apply_spec
    have = by_alias(ws)
    ops = [{'type': 'field.update', 'worksheet': ws, 'field': have[a]['controlId'], 'set': {'fieldPermission': HIDDEN}}
           for a in aliases if have[a].get('fieldPermission') != HIDDEN]
    for op in ops:
        apply_spec([op])
    return len(ops)


if __name__ == '__main__':
    # Units
    uws, uraw, ufix = ensure_sheet(UNITS, STEP)
    ref, rel = ensure_self_relation(uws, 'relative_uom_id', 'Reference Unit', 'related_uom_ids', 'Related UoMs', 'uom', 'Units',
                                    STEP, desc='The unit this one is defined from. Leave empty for the top unit of a chain.')
    last = add_once(uws, {'type': 29, 'controlName': 'Last Valid Reference Unit', 'alias': 'x_uom__last_valid_uom_id',
                          'dataSource': uws, 'enumDefault': 1, 'fieldPermission': HIDDEN,
                          'desc': 'The reference unit before the last change; restored when a change would make a loop. ' + AUTO,
                          'advancedSetting': {'showtype': '3'}}, 'uom', 'Units.Last Valid Reference Unit', STEP)
    u = by_alias(uws)
    set_show(uws, rel['controlId'], [u[a]['controlId'] for a in ('name', 'relative_factor', 'factor', 'active')])
    print('Units', uws, 'fields', len(u), 'fixes', ufix, '| reverse', rel['controlId'], '| hidden', hide(uws, ['x_uom__last_valid_uom_id']))

    # Product Categories
    cws, craw, cfix = ensure_sheet(CATEG, STEP)
    par, chi = ensure_self_relation(cws, 'parent_id', 'Parent Category', 'child_id', 'Child Categories', 'product',
                                    'Product Categories', STEP, desc='Leave empty for a top category.')
    lastc = add_once(cws, {'type': 29, 'controlName': 'Last Valid Parent', 'alias': 'x_product__last_valid_parent_id',
                           'dataSource': cws, 'enumDefault': 1, 'fieldPermission': HIDDEN,
                           'desc': 'The parent before the last change; restored when a change would make a loop. ' + AUTO,
                           'advancedSetting': {'showtype': '3'}}, 'product', 'Product Categories.Last Valid Parent', STEP)
    c = by_alias(cws)
    set_show(cws, chi['controlId'], [c[a]['controlId'] for a in ('name', 'complete_name')])
    n = hide(cws, ['x_product__last_valid_parent_id'] + [f'x_product__ancestor_{i}' for i in range(1, 6)])
    print('Product Categories', cws, 'fields', len(c), 'fixes', cfix, '| reverse', chi['controlId'], '| hidden', n)
