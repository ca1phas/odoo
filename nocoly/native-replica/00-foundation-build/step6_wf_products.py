"""Wave 0 workflows #11 (variant sales price), #9 (barcode uniqueness) and the combo item label.

#11 "Products - Variant price" (Variants: product, attribute values or Price Stamp change): Sales Price = product
    Sales Price + sum of its attribute values' Extra Price (rollup over a fresh read; Odoo lst_price).
    "Products - Sales price to variants" (product Sales Price change) and "Products - Extra price to variants" (PTAV
    Extra Price change) only stamp the affected variants, which starts the first flow for each of them.
#9  "Products - Product barcode check" / "Products - Variant barcode check": a barcode already used by another
    product or by a variant of another product is cleared, and the person who saved is told (Odoo _check_barcode_uniqueness).
"Products - Combo item label": a combo item's title is its variant's display name.
Run: python step6_wf_products.py
"""
import json
from lib import hap
from wflib import S, F, create_flow, batch_add, node_ids, publish, cond, lit, fld, set_decimals, clear_field

STEP = 'v2 step 6 (#9, #11)'
P, V, T, CI = 'product_template', 'product_product', 'product_template_attribute_value', 'product_combo_item'
NOW = {'kind': 'systemField', 'fieldId': 'nowTime'}


def rel(alias, name, sheet, target, field):
    return {'nodeAlias': alias, 'nodeType': 'get_relation', 'name': name,
            'config': {'worksheet': S[sheet], 'target': {'node': target}, 'fields': [{'fieldId': field}]}}


def rel_many(alias, name, sheet, target, field):
    return {'nodeAlias': alias, 'nodeType': 'get_relation_records', 'name': name,
            'config': {'worksheet': S[sheet], 'target': {'node': target}, 'fields': [{'fieldId': field}]}}


def variant_price():
    """The rollup node over a fetched set only counts records (its sum setting is not kept), so the variant's own
    Rollup field "Variant Price Extra" is refreshed (Calibrate, action 6) and read back fresh instead."""
    pid = create_flow('Products - Variant price', 'worksheet', 'product', STEP,
                      'Variant Sales Price = product Sales Price + extra prices of its attribute values (Odoo lst_price).')
    names, d = node_ids(pid)
    if 'Sales Price' not in names:
        x = F(V, 'product_template_attribute_value_ids')
        nodes = [rel('prod', 'The product', P, 'trigger', F(V, 'product_tmpl_id')),
                 {'nodeAlias': 'me', 'nodeType': 'get_single', 'name': 'The variant, fresh',
                  'config': {'worksheet': S[V], 'filter': {'logic': 'and', 'items': [
                      {'left': {'node': {'nodeAlias': 'me'}, 'fieldId': 'rowid'}, 'op': 'eq', 'type': 2,
                       'right': fld({'nodeAlias': 'trigger'}, 'rowid')}]}}},
                 {'nodeAlias': 'price', 'nodeType': 'compute', 'name': 'Sales Price',
                  'config': {'mode': 'function', 'output_type': 'number',
                             'formula': f'$prod-{F(P, "list_price")}$ + IF(ISBLANK($me-{F(V, "price_extra")}$), 0, $me-{F(V, "price_extra")}$)'}},
                 {'nodeAlias': 'w', 'nodeType': 'update_record', 'name': 'Write Sales Price',
                  'config': {'worksheet': S[V], 'target': {'node': 'trigger'},
                             'fields': [{'fieldId': F(V, 'lst_price'), 'value': fld('price', 'string_fx_id')}]}}]
        batch_add(pid, nodes, '--trigger-worksheet', S[V], '--trigger-event', 'create_or_update',
                  '--trigger-fields', ','.join([F(V, 'product_tmpl_id'), x, F(V, 'x_product__price_stamp')]))
        names, d = node_ids(pid)
    if 'Refresh rollups' not in names:
        start = d.get('startEventId') or next(k for k, v in d['flowNodeMap'].items() if v.get('typeId') == 0)
        hap('workflow', 'node', 'add', pid, '--type', '6', '-a', '6', '--app-id', S[V], '--after', names['The product'],
            '-n', 'Refresh rollups')
        names, d = node_ids(pid)
        # the UI stores the field to recalculate as {"type": 37, "isClear": true}; save-action keeps no fields here
        hap('workflow', 'node', 'save', pid, names['Refresh rollups'], '--type', '6', '-c', json.dumps({
            'name': 'Refresh rollups', 'actionId': '6', 'appId': S[V], 'appType': 1, 'selectNodeId': start,
            'fields': [{'fieldId': F(V, 'price_extra'), 'type': 37, 'fieldValue': '', 'fieldValueId': '', 'nodeId': '',
                        'isClear': True}]}))
    set_decimals(pid, names['Sales Price'], 2)
    return pid


def stamp_flow(name, desc, sheet, trigger_field, relation_field):
    pid = create_flow(name, 'worksheet', 'product', STEP, desc)
    if 'Its variants' not in node_ids(pid)[0]:
        nodes = [rel_many('vs', 'Its variants', V, 'trigger', relation_field),
                 {'nodeAlias': 'w', 'nodeType': 'update_record', 'name': 'Ask each variant for a new price',
                  'config': {'worksheet': S[V], 'target': {'node': 'vs'},
                             'fields': [{'fieldId': F(V, 'x_product__price_stamp'), 'value': NOW}]}}]
        batch_add(pid, nodes, '--trigger-worksheet', S[sheet], '--trigger-event', 'update', '--trigger-fields', trigger_field)
    return pid


def barcode_check(name, sheet, other):
    """sheet: the sheet whose barcode changed; other: the other sheet that shares the barcode space."""
    pid = create_flow(name, 'worksheet', 'product', STEP,
                      'A barcode already used by another product or variant is cleared, and the person who saved is told.')
    if 'Same barcode here' in node_ids(pid)[0]:
        return pid
    bc = F(sheet, 'barcode')
    same_here = {'nodeAlias': 'q1', 'nodeType': 'get_single', 'name': 'Same barcode here',
                 'config': {'worksheet': S[sheet], 'execute_type': 2, 'filter': {'logic': 'and', 'items': [
                     {'left': {'node': {'nodeAlias': 'q1'}, 'fieldId': bc}, 'op': 'eq', 'right': fld({'nodeAlias': 'trigger'}, bc)},
                     {'left': {'node': {'nodeAlias': 'q1'}, 'fieldId': 'rowid'}, 'op': 'ne', 'type': 2,
                      'right': fld({'nodeAlias': 'trigger'}, 'rowid')}]}}}
    nodes = [same_here]
    if sheet == P:      # a variant of ANOTHER product
        other_items = [{'left': {'node': {'nodeAlias': 'q2'}, 'fieldId': F(V, 'barcode')}, 'op': 'eq', 'right': fld({'nodeAlias': 'trigger'}, bc)},
                       {'left': {'node': {'nodeAlias': 'q2'}, 'fieldId': F(V, 'product_tmpl_id')}, 'op': 'ne',
                        'right': fld({'nodeAlias': 'trigger'}, 'rowid')}]
        label = f'$q1-{F(P, "name")}$ $q2-{F(V, "display_name")}$'
    else:               # ANOTHER product (not this variant's own)
        nodes.append(rel('prod', 'Its product', P, 'trigger', F(V, 'product_tmpl_id')))
        other_items = [{'left': {'node': {'nodeAlias': 'q2'}, 'fieldId': F(P, 'barcode')}, 'op': 'eq', 'right': fld({'nodeAlias': 'trigger'}, bc)},
                       {'left': {'node': {'nodeAlias': 'q2'}, 'fieldId': 'rowid'}, 'op': 'ne', 'type': 2,
                        'right': fld({'nodeAlias': 'prod'}, 'rowid')}]
        label = f'$q1-{F(V, "display_name")}$ $q2-{F(P, "name")}$'
    nodes.append({'nodeAlias': 'q2', 'nodeType': 'get_single', 'name': 'Same barcode on the other sheet',
                  'config': {'worksheet': S[other], 'execute_type': 2, 'filter': {'logic': 'and', 'items': other_items}}})
    nodes.append({'nodeAlias': 'dup', 'nodeType': 'branch', 'name': 'Used elsewhere?', 'config': {'mode': 'exclusive', 'paths': [
        {'alias': 'p_dup', 'name': 'Already used',
         'condition': {'logic': 'or', 'items': [cond('q1', bc, 'not_empty'), cond('q2', F(other, 'barcode'), 'not_empty')]},
         'nodes': [{'nodeAlias': 'clear', 'nodeType': 'update_record', 'name': 'Clear the barcode',
                    'config': {'worksheet': S[sheet], 'target': {'node': 'trigger'},
                               'fields': [{'fieldId': bc, 'value': lit('TO-CLEAR')}]}},   # patched to a real clear below
                   {'nodeAlias': 'tell', 'nodeType': 'notice', 'name': 'Tell the person who saved',
                    'config': {'accounts': [{'kind': 'triggerUser'}],
                               'content': f'Barcode $trigger-{bc}$ is already used by {label}. It was removed from $trigger-{F(sheet, "name" if sheet == P else "display_name")}$.'}}]},
        {'alias': 'p_ok', 'name': 'Unique', 'nodes': []}]}})
    batch_add(pid, nodes, '--trigger-worksheet', S[sheet], '--trigger-event', 'create_or_update', '--trigger-fields', bc,
              '--trigger-filter', json.dumps({'logic': 'and', 'items': [cond('trigger', bc, 'not_empty')]}))
    clear_field(pid, 'Clear the barcode', S[sheet], bc)
    return pid


def combo_label():
    pid = create_flow('Products - Combo item label', 'worksheet', 'product', STEP,
                      'A combo item is titled with its variant\'s display name.')
    if 'The variant' not in node_ids(pid)[0]:
        nodes = [rel('var', 'The variant', V, 'trigger', F(CI, 'product_id')),
                 {'nodeAlias': 'w', 'nodeType': 'update_record', 'name': 'Title',
                  'config': {'worksheet': S[CI], 'target': {'node': 'trigger'},
                             'fields': [{'fieldId': F(CI, 'x_product__label'), 'value': fld('var', F(V, 'display_name'))}]}}]
        batch_add(pid, nodes, '--trigger-worksheet', S[CI], '--trigger-event', 'create_or_update', '--trigger-fields', F(CI, 'product_id'))
    return pid


if __name__ == '__main__':
    built = [variant_price(),
             stamp_flow('Products - Sales price to variants', 'A product Sales Price change asks its variants for a new Sales Price.',
                        P, F(P, 'list_price'), F(P, 'product_variant_ids')),
             stamp_flow('Products - Extra price to variants', 'An attribute value Extra Price change asks its variants for a new Sales Price.',
                        T, F(T, 'price_extra'), F(T, 'ptav_product_variant_ids')),
             barcode_check('Products - Product barcode check', P, V),
             barcode_check('Products - Variant barcode check', V, P),
             combo_label()]
    for pid in built:
        r = publish(pid)
        print(pid, 'published' if r.get('isPublish') else json.dumps(r, ensure_ascii=False)[:600])
