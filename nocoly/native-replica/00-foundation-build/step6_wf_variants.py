"""Wave 0 workflow #8: variants from attribute lines (native-catalogue/workflow-nodes.md §5.2), native only.

Requests (queue pattern): a line created / changed / deleted, a new product, or the "Rebuild Variants" button adds a
row to Variant Requests. "Products - Build variants" runs on each new request, strictly one at a time:
 1. PTAV sync: for each line, for each of its values, find or create the product's PTAV (Key "<product>|<value>"),
    mark it active with this run; PTAVs not confirmed by this run are deactivated.
 2. Any "Dynamically" line: nothing is created (as Odoo), the request is marked Skipped.
 3. Combinations: a seed row, then for each "Instantly" line (sorted by attribute name) every open row is expanded with
    each active PTAV of that line (Key + "|<PTAV id>", Values + PTAV, Names + ", <value>"); expanded rows are marked Done.
 4. Variants: each open row finds its variant by product + Combination Key, or creates it; found or created variants
    are active with this run; the product's other variants are archived. The run's rows are deleted.
"Never" lines take part in step 1 only. Sub-processes see nothing of the outer flow, so the run id, product and line
travel as sub-process parameters, read inside from the fixed "This process parameter" node.
Run: python step6_wf_variants.py [requests] [build]
"""
import json, sys
from lib import hap, APP
from wflib import (S, F, create_flow, batch_add, node_ids, publish, cond, lit, fld, set_decimals, option_key,
                   inner_flows)

STEP = 'v2 step 6 (#8)'
P, L, A, AV, T, V = ('product_template', 'product_template_attribute_line', 'product_attribute', 'product_attribute_value',
                     'product_template_attribute_value', 'product_product')
Q, C = 'x_product__variant_queue', 'x_product__combination'
PARAM = '<id>'          # the fixed id of a flow's "This process parameter" node


def prm(name):
    return {'kind': 'field', 'node': {'nodeId': PARAM}, 'fieldId': name}


def by_id(alias, name, sheet, ref, execute_type=0):
    return {'nodeAlias': alias, 'nodeType': 'get_single', 'name': name,
            'config': {'worksheet': S[sheet], 'execute_type': execute_type, 'filter': {'logic': 'and', 'items': [
                {'left': {'node': {'nodeAlias': alias}, 'fieldId': 'rowid'}, 'op': 'eq', 'type': 2, 'right': ref}]}}}


def sub(alias, name, source, params, execute_type=2, inner_name=None):
    return {'nodeAlias': alias, 'nodeType': 'sub_process', 'name': name,
            'config': {'data_source': {'node': source}, 'process': {
                'name': inner_name or name, 'data_source': {'node': source}, 'execute_type': execute_type,
                'wait_complete': True, 'parameters': [{'controlId': k, 'name': k, 'value': v} for k, v in params.items()],
                'nodes': []}}}


def inner_of(pid, node_name):
    names, d = node_ids(pid)
    s = hap('workflow', 'node', 'get', pid, names[node_name], '--type', '16')
    s = s.get('data', s)
    return s['subProcessId']


def start_of(pid):
    names, d = node_ids(pid)
    return d.get('startEventId') or next(k for k, v in d['flowNodeMap'].items() if v.get('typeId') == 0)


def add_inner(inner, nodes):
    """Nodes written straight into an inner flow call its record 'trigger' (the CLI refuses 'sub_trigger' there)."""
    if not nodes:
        return
    first = nodes[0].get('name')
    if first in node_ids(inner)[0]:
        return
    nodes = json.loads(json.dumps(nodes).replace('sub_trigger', 'trigger'))
    batch_add(inner, nodes, '--after', start_of(inner))


def batch_412(pid, name, after, sheet, fields, condition):
    names, _ = node_ids(pid)
    if name not in names:
        hap('workflow', 'node', 'add', pid, '--type', '13', '-n', name, '--after', after, '-a', '412', '--app-id', S[sheet])
        names, _ = node_ids(pid)
    hap('workflow', 'node', 'save-get-more', pid, names[name], '-a', '412', '--app-id', S[sheet],
        '-f', json.dumps(fields), '--condition', json.dumps(condition))
    return names[name]


# ---------------------------------------------------------------- requests
def request_flows():
    out = []
    lab = F(Q, 'x_product__name')
    specs = [
        ('Products - Request variants (line saved)', L, 'create_or_update', [F(L, 'attribute_id'), F(L, 'value_ids')],
         fld('trigger', F(L, 'product_tmpl_id')), f'Line saved: $trigger-{F(L, "x_product__label")}$'),
        ('Products - Request variants (line deleted)', L, 'delete', [], fld('trigger', F(L, 'product_tmpl_id')),
         f'Line deleted: $trigger-{F(L, "x_product__label")}$'),
        ('Products - Request variants (new product)', P, 'create', [], {'kind': 'record', 'node': 'trigger'},
         f'New product: $trigger-{F(P, "name")}$'),
    ]
    for name, sheet, event, tfields, product, text in specs:
        pid = create_flow(name, 'worksheet', 'product', STEP, 'Adds a Variant Request; the build flow does the work one at a time.')
        if 'Add a variant request' not in node_ids(pid)[0]:
            args = ['--trigger-worksheet', S[sheet], '--trigger-event', event]
            if tfields:
                args += ['--trigger-fields', ','.join(tfields)]
            batch_add(pid, [{'nodeAlias': 'req', 'nodeType': 'create_record', 'name': 'Add a variant request',
                             'config': {'worksheet': S[Q], 'fields': [
                                 {'fieldId': F(Q, 'x_product__product_id'), 'value': product},
                                 {'fieldId': lab, 'value': {'kind': 'template', 'value': text}}]}}], *args)
        out.append(pid)
    return out


# ---------------------------------------------------------------- build
def build_flow():
    pid = create_flow('Products - Build variants', 'worksheet', 'product', STEP,
                      'Builds a product\'s variants from its attribute lines (Odoo _create_variant_ids), one request at a time.')
    names, _ = node_ids(pid)
    run = fld('trigger', 'rowid')
    if 'Sync attribute values' not in names:
        nodes = [
            {'nodeAlias': 'prod', 'nodeType': 'get_relation', 'name': 'The product',
             'config': {'worksheet': S[P], 'target': {'node': 'trigger'}, 'fields': [{'fieldId': F(Q, 'x_product__product_id')}]}},
            {'nodeAlias': 'lines', 'nodeType': 'get_relation_records', 'name': 'Its attribute lines',
             'config': {'worksheet': S[L], 'target': {'node': 'prod'}, 'fields': [{'fieldId': F(P, 'attribute_line_ids')}]}},
            sub('s1', 'Sync attribute values', 'lines', {'p_run': run, 'p_product': fld('prod', 'rowid')},
                inner_name='Products - variants: values of one line'),
        ]
        batch_add(pid, nodes, '--trigger-worksheet', S[Q], '--trigger-event', 'create')
        names, _ = node_ids(pid)
    # S1: one line -> its values -> S2
    s1 = inner_of(pid, 'Sync attribute values')
    add_inner(s1, [
        {'nodeAlias': 'vals', 'nodeType': 'get_relation_records', 'name': 'Its values',
         'config': {'worksheet': S[AV], 'target': {'node': 'sub_trigger'}, 'fields': [{'fieldId': F(L, 'value_ids')}]}},
        sub('s2', 'One PTAV per value', 'vals', {'p_run': prm('p_run'), 'p_product': prm('p_product'),
                                                  'p_line': fld('sub_trigger', 'rowid')},
            inner_name='Products - variants: PTAV of one value')])
    # S2: one attribute value -> find or create its PTAV
    s2 = inner_of(s1, 'One PTAV per value')
    key = {'kind': 'field', 'node': 'k', 'fieldId': 'string_fx_id'}
    find = lambda alias, name, et: {'nodeAlias': alias, 'nodeType': 'get_single', 'name': name, 'config': {
        'worksheet': S[T], 'execute_type': et, 'filter': {'logic': 'and', 'items': [
            {'left': {'node': {'nodeAlias': alias}, 'fieldId': F(T, 'x_product__key')}, 'op': 'eq',
             'right': {'kind': 'field', 'node': {'nodeAlias': 'k'}, 'fieldId': 'string_fx_id'}}]}}}
    add_inner(s2, [
        by_id('pp', 'The product', P, prm('p_product')),
        by_id('ll', 'The line', L, prm('p_line')),
        {'nodeAlias': 'k', 'nodeType': 'compute', 'name': 'PTAV key',
         'config': {'mode': 'function', 'output_type': 'text', 'formula': 'CONCAT($pp-rowid$, "|", $sub_trigger-rowid$)'}},
        find('have', 'Existing PTAV', 2),
        {'nodeAlias': 'isnew', 'nodeType': 'branch', 'name': 'Exists?', 'config': {'result_branch': True, 'paths': [
            {'alias': 'p_no', 'result_type': 'no_data', 'name': 'New', 'nodes': [
                {'nodeAlias': 'mk', 'nodeType': 'create_record', 'name': 'Create the PTAV', 'config': {'worksheet': S[T], 'fields': [
                    {'fieldId': F(T, 'name'), 'value': fld('sub_trigger', F(AV, 'name'))},
                    {'fieldId': F(T, 'product_tmpl_id'), 'value': {'kind': 'record', 'node': 'pp'}},
                    {'fieldId': F(T, 'product_attribute_value_id'), 'value': {'kind': 'record', 'node': 'sub_trigger'}},
                    {'fieldId': F(T, 'attribute_id'), 'value': fld('ll', F(L, 'attribute_id'))},
                    {'fieldId': F(T, 'price_extra'), 'value': fld('sub_trigger', F(AV, 'default_extra_price'))},
                    {'fieldId': F(T, 'x_product__key'), 'value': key}]}}]},
            {'alias': 'p_yes', 'result_type': 'has_data', 'name': 'Exists', 'nodes': []}]}},
        find('got', 'The PTAV', 0),
        {'nodeAlias': 'mark', 'nodeType': 'update_record', 'name': 'Active in this run', 'config': {
            'worksheet': S[T], 'target': {'node': 'got'}, 'fields': [
                {'fieldId': F(T, 'ptav_active'), 'value': lit('1')},
                {'fieldId': F(T, 'x_product__run'), 'value': prm('p_run')},
                {'fieldId': F(T, 'attribute_line_id'), 'value': {'kind': 'record', 'node': 'll'}}]}}])
    names, _ = node_ids(pid)
    after = names['Sync attribute values']
    batch_412(pid, 'Deactivate PTAVs not in this run', after, T, [{'fieldId': F(T, 'ptav_active'), 'type': 36, 'fieldValue': '0'}],
              {'logic': 'and', 'items': [
                  {'field': F(T, 'product_tmpl_id'), 'op': 'eq', 'value': {'kind': 'field', 'node': names['The product'], 'fieldId': 'rowid'}},
                  {'field': F(T, 'x_product__run'), 'op': 'ne', 'value': {'kind': 'field', 'node': start_of(pid), 'fieldId': 'rowid'}}]})
    build_combinations(pid)
    return pid


def lines_query(alias, name, create_variant_key, sorts):
    return {'nodeAlias': alias, 'nodeType': 'get_multiple', 'name': name, 'config': {
        'worksheet': S[L], 'count': 100, 'sorts': sorts, 'filter': {'logic': 'and', 'items': [
            {'left': {'node': {'nodeAlias': alias}, 'fieldId': F(L, 'product_tmpl_id')}, 'op': 'eq',
             'right': {'kind': 'field', 'node': {'nodeAlias': 'prod'}, 'fieldId': 'rowid'}},
            {'left': {'node': {'nodeAlias': alias}, 'fieldId': F(L, 'x_product__create_variant')}, 'op': 'eq', 'type': 9,
             'right': lit(create_variant_key)}]}}}


def rows_query(alias, name, run_ref):
    return {'nodeAlias': alias, 'nodeType': 'get_multiple', 'name': name, 'config': {
        'worksheet': S[C], 'count': 1000, 'filter': {'logic': 'and', 'items': [
            {'left': {'node': {'nodeAlias': alias}, 'fieldId': F(C, 'x_product__run')}, 'op': 'eq', 'right': run_ref},
            {'left': {'node': {'nodeAlias': alias}, 'fieldId': F(C, 'x_product__done')}, 'op': 'unchecked'}]}}}


def build_combinations(pid):
    """Steps 2-4: dynamic check, combinations, variants, archive, clean-up, request Done."""
    names, d = node_ids(pid)
    run = {'kind': 'field', 'node': 'trigger', 'fieldId': 'rowid'}
    status = lambda label: lit(option_key(Q, 'x_product__status', label))
    cv = lambda label: option_key(A, 'create_variant', label)
    ck = lambda a: F(C, a)
    if 'Dynamic attribute?' not in names:
        build_nodes = [
            {'nodeAlias': 'seed', 'nodeType': 'create_record', 'name': 'Seed combination', 'config': {
                'worksheet': S[C], 'fields': [
                    {'fieldId': ck('x_product__run'), 'value': run},
                    {'fieldId': ck('x_product__product_id'), 'value': {'kind': 'record', 'node': 'prod'}}]}},
            lines_query('alines', 'Lines that create variants', cv('Instantly'),
                        [{'controlId': F(L, 'x_product__attribute_name'), 'controlType': 30, 'isAsc': True}]),
            sub('s3', 'Expand with each line', 'alines', {'p_run': run}, inner_name='Products - variants: expand one line'),
            rows_query('final', 'Finished combinations', run),
            sub('s5', 'One variant per combination', 'final', {'p_run': run}, execute_type=3,
                inner_name='Products - variants: find or create one variant'),
            {'nodeAlias': 'fin', 'nodeType': 'update_record', 'name': 'Request done', 'config': {
                'worksheet': S[Q], 'target': {'node': 'trigger'},
                'fields': [{'fieldId': F(Q, 'x_product__status'), 'value': status('Done')}]}}]
        nodes = [
            lines_query('dyn', 'Dynamic lines', cv('Dynamically'), []),
            {'nodeAlias': 'ndyn', 'nodeType': 'rollup', 'name': 'How many dynamic', 'config': {'data_source': {'node': 'dyn'}}},
            {'nodeAlias': 'isdyn', 'nodeType': 'branch', 'name': 'Dynamic attribute?', 'config': {'mode': 'exclusive', 'paths': [
                {'alias': 'p_dyn', 'name': 'Has a dynamic attribute',
                 'condition': {'logic': 'and', 'items': [{'node': 'ndyn', 'field': 'number_fx_id', 'op': 'gt', 'type': 6, 'value': '0'}]},
                 'nodes': [{'nodeAlias': 'skip', 'nodeType': 'update_record', 'name': 'Skipped: dynamic', 'config': {
                     'worksheet': S[Q], 'target': {'node': 'trigger'}, 'fields': [
                         {'fieldId': F(Q, 'x_product__status'), 'value': status('Skipped')},
                         {'fieldId': F(Q, 'x_product__message'),
                          'value': lit('A "Dynamically" attribute: variants are created when ordered, as in Odoo.')}]}}]},
                {'alias': 'p_go', 'name': 'Build', 'nodes': build_nodes}]}}]
        batch_add(pid, nodes, '--after', names['Deactivate PTAVs not in this run'], '--alias', f"prod={names['The product']}")
        names, d = node_ids(pid)
    # S3: one line -> each open row -> S4
    s3 = inner_of(pid, 'Expand with each line')
    add_inner(s3, [rows_query('open', 'Open combinations', prm('p_run')),
                   sub('s4', 'Each open combination', 'open', {'p_run': prm('p_run'), 'p_line': fld('trigger', 'rowid')},
                       inner_name='Products - variants: expand one combination')])
    # S4: one open row x the line's active PTAVs
    s4 = inner_of(s3, 'Each open combination')
    add_inner(s4, [
        {'nodeAlias': 'vals', 'nodeType': 'get_multiple', 'name': 'Active values of the line', 'config': {
            'worksheet': S[T], 'count': 100, 'filter': {'logic': 'and', 'items': [
                {'left': {'node': {'nodeAlias': 'vals'}, 'fieldId': F(T, 'attribute_line_id')}, 'op': 'eq', 'right': prm('p_line')},
                {'left': {'node': {'nodeAlias': 'vals'}, 'fieldId': F(T, 'ptav_active')}, 'op': 'checked'}]}}},
        {'nodeAlias': 'new', 'nodeType': 'create_record', 'name': 'One new combination per value', 'config': {
            'worksheet': S[C], 'target': {'node': 'vals'}, 'fields': [
                {'fieldId': ck('x_product__key'), 'value': {'kind': 'template', 'value': f'$trigger-{ck("x_product__key")}$|$vals-rowid$'}},
                {'fieldId': ck('x_product__names'), 'value': {'kind': 'template', 'value': f'$trigger-{ck("x_product__names")}$, $vals-{F(T, "name")}$'}},
                {'fieldId': ck('x_product__run'), 'value': fld('trigger', ck('x_product__run'))},
                {'fieldId': ck('x_product__product_id'), 'value': fld('trigger', ck('x_product__product_id'))},
                {'fieldId': ck('x_product__ptav_ids'), 'value': fld('trigger', ck('x_product__ptav_ids'))},
                {'fieldId': ck('x_product__ptav_ids'), 'op': 'append', 'value': {'kind': 'record', 'node': 'vals'}}]}},
        {'nodeAlias': 'dn', 'nodeType': 'update_record', 'name': 'Expanded', 'config': {
            'worksheet': S[C], 'target': {'node': 'trigger'}, 'fields': [{'fieldId': ck('x_product__done'), 'value': lit('1')}]}}])
    # S5: one finished row -> its variant
    s5 = inner_of(pid, 'One variant per combination')
    add_inner(s5, [
        {'nodeAlias': 'pp', 'nodeType': 'get_relation', 'name': 'The product', 'config': {
            'worksheet': S[P], 'target': {'node': 'trigger'}, 'fields': [{'fieldId': ck('x_product__product_id')}]}},
        {'nodeAlias': 'dname', 'nodeType': 'compute', 'name': 'Variant name', 'config': {'mode': 'function', 'output_type': 'text',
            'formula': f'IF(ISBLANK($trigger-{ck("x_product__names")}$), $pp-{F(P, "name")}$, '
                       f'CONCAT($pp-{F(P, "name")}$, " (", MID($trigger-{ck("x_product__names")}$, 3, 500), ")"))'}},
        {'nodeAlias': 'have', 'nodeType': 'get_single', 'name': 'Existing variant', 'config': {
            'worksheet': S[V], 'execute_type': 2, 'filter': {'logic': 'and', 'items': [
                {'left': {'node': {'nodeAlias': 'have'}, 'fieldId': F(V, 'product_tmpl_id')}, 'op': 'eq',
                 'right': {'kind': 'field', 'node': {'nodeAlias': 'pp'}, 'fieldId': 'rowid'}},
                {'left': {'node': {'nodeAlias': 'have'}, 'fieldId': F(V, 'combination_indices')}, 'op': 'eq',
                 'right': fld({'nodeAlias': 'trigger'}, ck('x_product__key'))}]}}},
        {'nodeAlias': 'ex', 'nodeType': 'branch', 'name': 'Variant exists?', 'config': {'result_branch': True, 'paths': [
            {'alias': 'p_new', 'result_type': 'no_data', 'name': 'New variant', 'nodes': [
                {'nodeAlias': 'mkv', 'nodeType': 'create_record', 'name': 'Create the variant', 'config': {'worksheet': S[V], 'fields': [
                    {'fieldId': F(V, 'product_tmpl_id'), 'value': {'kind': 'record', 'node': 'pp'}},
                    {'fieldId': F(V, 'product_template_attribute_value_ids'), 'value': fld('trigger', ck('x_product__ptav_ids'))},
                    {'fieldId': F(V, 'combination_indices'), 'value': fld('trigger', ck('x_product__key'))},
                    {'fieldId': F(V, 'display_name'), 'value': fld('dname', 'string_fx_id')},
                    {'fieldId': F(V, 'x_product__run'), 'value': prm('p_run')}]}}]},
            {'alias': 'p_old', 'result_type': 'has_data', 'name': 'Existing variant', 'nodes': [
                {'nodeAlias': 'keep', 'nodeType': 'update_record', 'name': 'Keep it active', 'config': {
                    'worksheet': S[V], 'target': {'node': 'have'}, 'fields': [
                        {'fieldId': F(V, 'active'), 'value': lit('1')},
                        {'fieldId': F(V, 'x_product__run'), 'value': prm('p_run')}]}}]}]}}])
    # archive the product's variants not confirmed by this run, then delete this run's rows (before "Request done")
    names, d = node_ids(pid)
    a = batch_412(pid, 'Archive variants not in this run', names['One variant per combination'], V,
                  [{'fieldId': F(V, 'active'), 'type': 36, 'fieldValue': '0'}],
                  {'logic': 'and', 'items': [
                      {'field': F(V, 'product_tmpl_id'), 'op': 'eq', 'value': {'kind': 'field', 'node': names['The product'], 'fieldId': 'rowid'}},
                      {'field': F(V, 'x_product__run'), 'op': 'ne', 'value': {'kind': 'field', 'node': start_of(pid), 'fieldId': 'rowid'}},
                      {'field': F(V, 'active'), 'op': 'checked'}]})
    names, _ = node_ids(pid)
    delete_name = 'Delete the combinations of this run'
    if delete_name not in names:
        hap('workflow', 'node', 'add', pid, '--type', '13', '-n', delete_name, '--after', a, '-a', '413', '--app-id', S[C])
        names, _ = node_ids(pid)
    hap('workflow', 'node', 'save-get-more', pid, names[delete_name], '-a', '413', '--app-id', S[C], '--permanent',
        '--condition', json.dumps({'logic': 'and', 'items': [
            {'field': F(C, 'x_product__run'), 'op': 'eq', 'value': {'kind': 'field', 'node': start_of(pid), 'fieldId': 'rowid'}}]}))


if __name__ == '__main__':
    todo = sys.argv[1:] or ['requests', 'build']
    if 'requests' in todo:
        for pid in request_flows():
            r = publish(pid)
            print('request flow', pid, 'published' if r.get('isPublish') else json.dumps(r, ensure_ascii=False)[:500])
    if 'build' in todo:
        pid = build_flow()
        hap('workflow', 'config-set', pid, '-c', json.dumps({'executeType': 3}))
        r = publish(pid)
        print('build flow', pid, 'published' if r.get('isPublish') else json.dumps(r, ensure_ascii=False)[:800])
