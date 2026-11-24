"""Wave 0 workflow #12: pricelist rule fields, the price function and the price checker (workflow-nodes.md §5.3),
following Odoo 20 (product_pricelist_item.py: Discount / Surcharge / Fixed Price; order applied_on, min_quantity desc,
categ_id desc, id desc; category rules match sub-categories).

"Products - Pricelist rule fields" (rule saved): Applies To text, Price text, and the hidden search helpers
Rank (0 variant, 1 product, 2 category, 3 all), Target Key (record id or ALL), Category Sort Key, Effective Start / End.
Run: python step6_wf_pricelist.py [rules]
"""
import json, sys
from lib import hap, APP
from wflib import S, F, create_flow, batch_add, node_ids, publish, cond, lit, fld, option_key

STEP = 'v2 step 6 (#12)'
R, K, P, V, PL = 'product_pricelist_item', 'product_category', 'product_template', 'product_product', 'product_pricelist'


def r(a):
    return F(R, a)


def upd(alias, name, fields):
    return {'nodeAlias': alias, 'nodeType': 'update_record', 'name': name,
            'config': {'worksheet': S[R], 'target': {'node': 'trigger'}, 'fields': fields}}


def rel(alias, name, sheet, field):
    return {'nodeAlias': alias, 'nodeType': 'get_relation', 'name': name,
            'config': {'worksheet': S[sheet], 'target': {'node': 'trigger'}, 'fields': [{'fieldId': field}]}}


def helpers(rank, target, name, categ_sort=None):
    out = [{'fieldId': r('x_product__rank'), 'value': lit(str(rank))},
           {'fieldId': r('x_product__target_key'), 'value': target},
           {'fieldId': r('name'), 'value': name}]
    if categ_sort is not None:
        out.append({'fieldId': r('x_product__categ_sort'), 'value': categ_sort})
    return out


def rule_fields():
    pid = create_flow('Products - Pricelist rule fields', 'worksheet', 'product', STEP,
                      'When a rule is saved: what it applies to, its price in words, and the hidden fields the price '
                      'function uses to find the rule Odoo would pick.')
    if 'Apply On?' in node_ids(pid)[0]:
        return pid
    ao = lambda label: option_key(R, 'applied_on', label)
    cp = lambda label: option_key(R, 'compute_price', label)
    tmpl = lambda t: {'kind': 'template', 'value': t}
    nodes = [
        {'nodeAlias': 'es', 'nodeType': 'compute', 'name': 'Effective start', 'config': {'mode': 'function', 'output_type': 'datetime',
            'formula': f'IF(ISBLANK($trigger-{r("date_start")}$), "1900-01-01 00:00", $trigger-{r("date_start")}$)'}},
        {'nodeAlias': 'ee', 'nodeType': 'compute', 'name': 'Effective end', 'config': {'mode': 'function', 'output_type': 'datetime',
            'formula': f'IF(ISBLANK($trigger-{r("date_end")}$), "2999-12-31 23:59", $trigger-{r("date_end")}$)'}},
        upd('wdates', 'Effective dates', [
            {'fieldId': r('x_product__effective_start'), 'value': fld('es', 'string_fx_id')},
            {'fieldId': r('x_product__effective_end'), 'value': fld('ee', 'string_fx_id')}]),
        {'nodeAlias': 'kind', 'nodeType': 'branch', 'name': 'Price Type?', 'config': {'mode': 'exclusive', 'paths': [
            {'alias': 'k_fix', 'name': 'Fixed Price',
             'condition': {'logic': 'and', 'items': [cond('trigger', r('compute_price'), 'eq', cp('Fixed Price'))]},
             'nodes': [upd('wfix', 'Price in words', [{'fieldId': r('price'), 'value': tmpl(f'$trigger-{r("fixed_price")}$')}])]},
            {'alias': 'k_sur', 'name': 'Surcharge',
             'condition': {'logic': 'and', 'items': [cond('trigger', r('compute_price'), 'eq', cp('Surcharge'))]},
             'nodes': [upd('wsur', 'Price in words', [{'fieldId': r('price'), 'value': tmpl(
                 f'$trigger-{r("price_markup")}$% surcharge on $trigger-{r("base")}$')}])]},
            {'alias': 'k_dis', 'name': 'Discount',
             'nodes': [upd('wdis', 'Price in words', [{'fieldId': r('price'), 'value': tmpl(
                 f'$trigger-{r("price_discount")}$% discount on $trigger-{r("base")}$')}])]}]}},
        {'nodeAlias': 'on', 'nodeType': 'branch', 'name': 'Apply On?', 'config': {'mode': 'exclusive', 'paths': [
            {'alias': 'a_var', 'name': 'Product Variant',
             'condition': {'logic': 'and', 'items': [cond('trigger', r('applied_on'), 'eq', ao('Product Variant'))]},
             'nodes': [rel('var', 'The variant', V, r('product_id')),
                       upd('wvar', 'Rank 0', helpers(0, fld('var', 'rowid'), tmpl(f'Variant: $var-{F(V, "display_name")}$')))]},
            {'alias': 'a_prod', 'name': 'Product',
             'condition': {'logic': 'and', 'items': [cond('trigger', r('applied_on'), 'eq', ao('Product'))]},
             'nodes': [rel('prod', 'The product', P, r('product_tmpl_id')),
                       upd('wprod', 'Rank 1', helpers(1, fld('prod', 'rowid'), tmpl(f'Product: $prod-{F(P, "name")}$')))]},
            {'alias': 'a_cat', 'name': 'Product Category',
             'condition': {'logic': 'and', 'items': [cond('trigger', r('applied_on'), 'eq', ao('Product Category'))]},
             'nodes': [rel('cat', 'The category', K, r('categ_id')),
                       upd('wcat', 'Rank 2', helpers(2, fld('cat', 'rowid'), tmpl(f'Category: $cat-{F(K, "complete_name")}$'),
                                                     fld('cat', F(K, 'x_product__number'))))]},
            {'alias': 'a_all', 'name': 'All Products',
             'nodes': [upd('wall', 'Rank 3', helpers(3, lit('ALL'), lit('All Products'), lit('0')))]}]}},
    ]
    batch_add(pid, nodes, '--trigger-worksheet', S[R], '--trigger-event', 'create_or_update',
              '--trigger-fields', ','.join(r(a) for a in ('applied_on', 'categ_id', 'product_tmpl_id', 'product_id', 'date_start',
                                                           'date_end', 'compute_price', 'base', 'base_pricelist_id',
                                                           'price_discount', 'price_markup', 'fixed_price')))
    names, d = node_ids(pid)
    for gw, first in (('Price Type?', ['Fixed Price', 'Surcharge']), ('Apply On?', ['Product Variant', 'Product', 'Product Category'])):
        for nid, nm in zip(d['flowNodeMap'][names[gw]]['flowIds'], first):
            hap('workflow', 'node', 'rename', pid, nid, '-n', nm, ok_fail=True)
    return pid


def price_pbp():
    """PBP "Products - Price for product". Inputs: Pricelist, Product, Variant (optional), Quantity, Date (record ids as
    text). Outputs: Price (in the pricelist currency), Rule (record id), Rule Label.
    One sorted query finds the rule Odoo would apply (8 OR-groups: all products, the variant, the product, the category
    and its 4 ancestors). The base price (MYR) is converted to the pricelist currency with the rate on the date
    (MYR is the company currency, rate 1). "Other Pricelist" bases are handled by price_chain() (a call of this PBP)."""
    import secrets
    from wflib import set_decimals, sort_single
    pid = create_flow('Products - Price for product', 'pbp', 'product', STEP,
                      'Shared function: the price of a product or variant on a pricelist for a quantity and date (Odoo _get_product_price).')
    names, d = node_ids(pid)
    start = d.get('startEventId') or names['PBP']
    s = hap('workflow', 'node', 'get', pid, start, '--type', '0'); s = s.get('data', s)
    if not s.get('controls'):
        batch_add(pid, [], '--trigger-pbp', json.dumps({'inputs': [
            {'name': 'Pricelist', 'type': 'text', 'required': True, 'alias': 'pricelist', 'desc': 'Record id in Pricelists.'},
            {'name': 'Product', 'type': 'text', 'required': True, 'alias': 'product', 'desc': 'Record id in Products.'},
            {'name': 'Variant', 'type': 'text', 'alias': 'variant', 'desc': 'Record id in Variants; empty for the product itself.'},
            {'name': 'Quantity', 'type': 'number', 'required': True, 'alias': 'qty', 'desc': 'In the product unit.'},
            {'name': 'Date', 'type': 'date', 'required': True, 'alias': 'date'}]}))
        s = hap('workflow', 'node', 'get', pid, start, '--type', '0'); s = s.get('data', s)
    inp = {c['alias']: c['controlId'] for c in s['controls']}
    tr = lambda k: {'kind': 'field', 'node': {'nodeAlias': 'trigger'}, 'fieldId': inp[k]}
    if 'Price' not in names:
        def by_rowid(alias, name, sheet, ref, et=0):
            return {'nodeAlias': alias, 'nodeType': 'get_single', 'name': name, 'config': {
                'worksheet': S[sheet], 'execute_type': et, 'filter': {'logic': 'and', 'items': [
                    {'left': {'node': {'nodeAlias': alias}, 'fieldId': 'rowid'}, 'op': 'eq', 'type': 2, 'right': ref}]}}}
        common = lambda: [
            {'left': {'node': {'nodeAlias': 'rule'}, 'fieldId': r('pricelist_id')}, 'op': 'eq', 'right': tr('pricelist')},
            {'left': {'node': {'nodeAlias': 'rule'}, 'fieldId': r('x_product__effective_start')}, 'op': 'lte', 'right': tr('date')},
            {'left': {'node': {'nodeAlias': 'rule'}, 'fieldId': r('x_product__effective_end')}, 'op': 'gte', 'right': tr('date')},
            {'left': {'node': {'nodeAlias': 'rule'}, 'fieldId': r('min_quantity')}, 'op': 'lte', 'right': tr('qty')}]
        target = lambda right: {'left': {'node': {'nodeAlias': 'rule'}, 'fieldId': r('x_product__target_key')}, 'op': 'eq', 'right': right}
        groups = [{'logic': 'and', 'items': common() + [target(lit('ALL'))]},
                  {'logic': 'and', 'items': common() + [target(tr('variant'))]},
                  {'logic': 'and', 'items': common() + [target(tr('product'))]}] + \
                 [{'logic': 'and', 'items': common() + [target({'kind': 'field', 'node': {'nodeAlias': 'cat'},
                                                                'fieldId': F(K, f'x_product__ancestor_{i}')})]} for i in range(1, 6)]
        R_ = lambda a: f'$rule-{r(a)}$'
        lst = f'IF(ISBLANK($va-rowid$), $pr-{F(P, "list_price")}$, $va-{F(V, "lst_price")}$)'
        cost = f'IF(ISBLANK($va-rowid$), $pr-{F(P, "standard_price")}$, $va-{F(V, "standard_price")}$)'
        rate = f'IF(ISBLANK($rt-{F("res_currency_rate", "rate")}$), IF(ISBLANK($rt0-{F("res_currency_rate", "rate")}$), 1, $rt0-{F("res_currency_rate", "rate")}$), $rt-{F("res_currency_rate", "rate")}$)'
        extra = f'IF(ISBLANK($va-{F(V, "price_extra")}$), 0, $va-{F(V, "price_extra")}$)'
        rate_q = lambda alias, name, dated: {'nodeAlias': alias, 'nodeType': 'get_single', 'name': name, 'config': {
            'worksheet': S['res_currency_rate'], 'execute_type': 2, 'filter': {'logic': 'and', 'items': [
                {'left': {'node': {'nodeAlias': alias}, 'fieldId': F('res_currency_rate', 'currency_id')}, 'op': 'eq',
                 'right': {'kind': 'field', 'node': {'nodeAlias': 'pl'}, 'fieldId': F(PL, 'currency_id')}}] + ([
                {'left': {'node': {'nodeAlias': alias}, 'fieldId': F('res_currency_rate', 'name')}, 'op': 'lte', 'right': tr('date')}]
                if dated else [])}}}
        nodes = [
            by_rowid('pl', 'The pricelist', PL, tr('pricelist')),
            by_rowid('pr', 'The product', P, tr('product')),
            by_rowid('va', 'The variant', V, tr('variant'), 2),
            {'nodeAlias': 'cat', 'nodeType': 'get_relation', 'name': 'Its category',
             'config': {'worksheet': S[K], 'target': {'node': 'pr'}, 'fields': [{'fieldId': F(P, 'categ_id')}]}},
            {'nodeAlias': 'rule', 'nodeType': 'get_single', 'name': 'The rule Odoo would apply',
             'config': {'worksheet': S[R], 'execute_type': 2, 'filter': {'logic': 'or', 'items': groups}}},
            rate_q('rt', 'Pricelist currency rate on the date', True),
            rate_q('rt0', 'Pricelist currency earliest rate', False),
            {'nodeAlias': 'base', 'nodeType': 'compute', 'name': 'Base price', 'config': {'mode': 'function', 'output_type': 'number',
                'formula': f'IF(STRING({R_("base")})=="Cost", {cost}, {lst}) * {rate}'}},
            {'nodeAlias': 'price', 'nodeType': 'compute', 'name': 'Price', 'config': {'mode': 'function', 'output_type': 'number',
                'formula': (
                    f'IF(ISBLANK($rule-rowid$), $base-string_fx_id$, '
                    f'IF(STRING({R_("compute_price")})=="Fixed Price", {R_("fixed_price")} + IF(STRING({R_("applied_on")})=="Product Variant", 0, {extra} * {rate}), '
                    f'MIN(MAX('
                    f'IF(OR(ISBLANK({R_("price_round")}), {R_("price_round")}==0), '
                    f'$base-string_fx_id$ * (1 - IF(STRING({R_("compute_price")})=="Surcharge", -{R_("price_markup")}, {R_("price_discount")}) / 100), '
                    f'ROUND($base-string_fx_id$ * (1 - IF(STRING({R_("compute_price")})=="Surcharge", -{R_("price_markup")}, {R_("price_discount")}) / 100) / {R_("price_round")}, 0) * {R_("price_round")}) '
                    f'+ IF(ISBLANK({R_("price_surcharge")}), 0, {R_("price_surcharge")}), '
                    f'IF(OR(ISBLANK({R_("price_min_margin")}), {R_("price_min_margin")}==0), -999999999, $base-string_fx_id$ + {R_("price_min_margin")})), '
                    f'IF(OR(ISBLANK({R_("price_max_margin")}), {R_("price_max_margin")}==0), 999999999, $base-string_fx_id$ + {R_("price_max_margin")}))))')}},
        ]
        batch_add(pid, nodes, '--after', start)
        names, d = node_ids(pid)
    for n in ('Base price', 'Price'):
        set_decimals(pid, names[n], 6)
    sort_single(pid, names['The rule Odoo would apply'], [(r('x_product__rank'), 6, True), (r('min_quantity'), 6, False),
                                                         (r('x_product__categ_sort'), 6, False), (r('x_product__number'), 33, False)])
    rate_f = F('res_currency_rate', 'name')
    sort_single(pid, names['Pricelist currency rate on the date'], [(rate_f, 15, False)])
    sort_single(pid, names['Pricelist currency earliest rate'], [(rate_f, 15, True)])
    out = names['Output Parameters']
    o = hap('workflow', 'node', 'get', pid, out, '--type', '20'); o = o.get('data', o)
    have = {v['controlName']: v['controlId'] for v in o.get('subProcessVariables') or []}
    var = lambda name, typ, dot, alias: {'controlId': have.get(name) or secrets.token_hex(12), 'controlName': name, 'type': typ,
                                         'dataSource': '', 'options': [], 'required': False, 'enumDefault': 0, 'enumDefault2': 0,
                                         'fieldPermission': '2', 'dot': dot, 'hide': False, 'attribute': 0, 'sourceControlType': 0,
                                         'unit': '', 'processVariableType': 2, 'originalType': 0, 'alias': alias}
    vs = [var('Price', 6, 2, 'price'), var('Rule', 2, 0, 'rule'), var('Rule Label', 2, 0, 'rule_label')]
    ref = lambda v, node, value_id, vtype, nt, act: {'fieldId': v['controlId'], 'fieldName': v['controlName'], 'type': v['type'],
                                                     'nodeId': node, 'sureNodeId': node, 'nodeTypeId': nt, 'nodeActionId': act,
                                                     'nodeAppType': 11 if nt == 9 else 1, 'fieldValueId': value_id,
                                                     'fieldValueType': str(vtype), 'fieldValueName': '', 'fieldValue': '',
                                                     'sourceType': 0, 'addType': 0}
    hap('workflow', 'node', 'save', pid, out, '--type', '20', '-c', json.dumps({
        'name': 'Output Parameters', 'actionId': '502', 'subProcessVariables': vs,
        'fields': [ref(vs[0], names['Price'], 'string_fx_id', 6, 9, '106'),
                   ref(vs[1], names['The rule Odoo would apply'], 'rowid', 2, 7, '406'),
                   ref(vs[2], names['The rule Odoo would apply'], r('name'), 2, 7, '406')]}))
    return pid


if __name__ == '__main__':
    todo = sys.argv[1:] or ['rules', 'pbp']
    if 'pbp' in todo:
        pid = price_pbp()
        rr = publish(pid)
        print('price pbp', pid, 'published' if rr.get('isPublish') else json.dumps(rr, ensure_ascii=False)[:800])
    if 'rules' in todo:
        pid = rule_fields()
        rr = publish(pid)
        print('rule fields', pid, 'published' if rr.get('isPublish') else json.dumps(rr, ensure_ascii=False)[:700])
