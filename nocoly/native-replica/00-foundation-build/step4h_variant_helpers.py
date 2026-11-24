"""Wave 0 (plan v2) helper sheets for #8 (variants), in System Tables:
- Variant Requests `x_product__variant_queue`: one row per "rebuild this product's variants" request (queue pattern,
  native-catalogue/workflow-nodes.md §4 rule 3: update triggers cannot run serially, a create-only flow can).
- Combinations `x_product__combination`: build rows of one run (key, attribute values, names), deleted after the run.
Also: variant Combination Keys are rewritten to the build format "|<PTAV id>" per value, lines ordered by attribute name.
Run: python step4h_variant_helpers.py
"""
import json
from lib import hap, APP
from sheetlib import F, ensure_sheet, by_alias, sheets_by_alias
from step4a_load_reference import rows_of

STEP = 'v2 step 6 (#8)'
AUTO = 'Kept up to date automatically.'

QUEUE = {
    'name': 'Variant Requests', 'alias': 'x_product__variant_queue', 'module': 'product', 'group': 'System Tables',
    'icon': 'sys_gear1_office', 'title': 'Request',
    'desc': 'Requests to rebuild a product\'s variants, handled one by one by the variant flow.',
    'fields': [
        F('Request', 'TEXT', 'x_product__name', desc='Product and reason. ' + AUTO),
        F('Product', 'RELATE_SHEET', 'x_product__product_id', dataSource='@product_template', multi=False, required=True,
          config={'displayMode': 'dropdown'}),
        F('Status', 'DROP_DOWN', 'x_product__status', options=['Waiting', 'Done', 'Skipped'], extra={'enumDefault2': 1},
          defaultValue=[{'source': 'static', 'value': 'Waiting'}]),
        F('Message', 'TEXT', 'x_product__message', desc=AUTO),
    ],
}

COMBOS = {
    'name': 'Combinations', 'alias': 'x_product__combination', 'module': 'product', 'group': 'System Tables',
    'icon': 'sys_gear1_office', 'title': 'Key',
    'desc': 'Work rows of one variant build: each row is one combination of attribute values. Deleted after the build.',
    'fields': [
        F('Key', 'TEXT', 'x_product__key', desc='"|<attribute value id>" per value, in line order. ' + AUTO),
        F('Run', 'TEXT', 'x_product__run', desc='The variant request being built. ' + AUTO),
        F('Product', 'RELATE_SHEET', 'x_product__product_id', dataSource='@product_template', multi=False,
          config={'displayMode': 'dropdown'}),
        F('Values', 'RELATE_SHEET', 'x_product__ptav_ids', dataSource='@product_template_attribute_value', multi=True),
        F('Names', 'TEXT', 'x_product__names', desc='", <value>" per value, for the variant name. ' + AUTO),
        F('Done', 'SWITCH', 'x_product__done', desc='Already expanded with the next attribute.'),
    ],
}


def attribute_name_field():
    """Stored foreign field "Attribute Name" on Attribute Lines: the build flow walks lines sorted by it, so the key
    order is stable (creation times tie when lines are imported together)."""
    from sheetlib import add_once
    S = {k: v['id'] for k, v in sheets_by_alias().items()}
    L, A = S['product_template_attribute_line'], S['product_attribute']
    rel = by_alias(L)['attribute_id']['controlId']
    return add_once(L, {'type': 30, 'controlName': 'Attribute Name', 'alias': 'x_product__attribute_name',
                        'dataSource': f'${rel}$', 'sourceControlId': by_alias(A)['name']['controlId'], 'sourceControlType': 2,
                        'strDefault': '00', 'desc': 'From the attribute; orders the lines when variants are built.'},
                    'product', 'Attribute Lines.Attribute Name', STEP)


def rekey_variants():
    """Variant keys in the build format: "|<PTAV row id>" per value, lines ordered by attribute name."""
    S = {k: v['id'] for k, v in sheets_by_alias().items()}
    V, T = S['product_product'], S['product_template_attribute_value']
    attr_of = {}
    for r in rows_of(T, 'attribute_id'):
        v = r.get('attribute_id')
        v = json.loads(v) if isinstance(v, str) and v.startswith('[') else v
        attr_of[r['rowId']] = (v[0].get('name') if isinstance(v, list) and v else '')
    changed = 0
    for r in rows_of(V, 'combination_indices'):
        g = hap('worksheet', 'record', 'get', V, r['rowId'], '-a', APP)
        g = g.get('data', g)
        ptavs = [x.get('sid') for x in (g.get('product_template_attribute_value_ids') or [])]
        ptavs.sort(key=lambda p: attr_of.get(p, ''))
        key = ''.join('|' + p for p in ptavs)
        if (g.get('combination_indices') or '') != key:
            hap('worksheet', 'record', 'update', V, r['rowId'], '-a', APP,
                '--fields-json', json.dumps([{'id': 'combination_indices', 'value': key}]))
            changed += 1
    return changed


if __name__ == '__main__':
    qws, _, f1 = ensure_sheet(QUEUE, STEP)
    cws, _, f2 = ensure_sheet(COMBOS, STEP)
    print('Variant Requests', qws, '| Combinations', cws, '| fixes', f1, f2)
    print('Attribute Name field', attribute_name_field()['controlId'])
    print('variant keys rewritten:', rekey_variants())
