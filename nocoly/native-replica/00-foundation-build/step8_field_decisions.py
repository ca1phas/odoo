"""Field decisions for the uom, product and mail fields the coverage check still showed as OPEN (24 Nov 2026).
Appends to field-decisions.csv only the (model, field) pairs that have no decision yet.
Vocabulary as before: skip (not needed in HAP), hap (HAP does it its own way), native:<what> (built in another form),
later:<module> (comes with a later module or step).
Run: python step8_field_decisions.py
"""
import csv, os

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, 'field-decisions.csv')

IMG = ('skip', 'Resized copy of the image; HAP makes its own thumbnails')
CUR = ('skip', 'Company currency (MYR); one company in wave 0')
MULTI = ('later:multi-company', 'Comes with multi-company')
STOCK = ('later:stock', 'Stock quantities come with the Inventory module')
PURCHASE = ('later:purchase', 'Vendor prices come with the Purchase module')
REVERSE = ('skip', 'Reverse list; open the related sheet filtered by this record')
HELPER = ('skip', 'Odoo form or onchange helper, not data')
ACTIVITY_MIXIN = ('skip', 'Activity mixin helper; HAP shows activities through the Activities sheet')
UNIT_PRICE = ('later:ecommerce', 'Price per base unit is shown by the e-shop and POS')
ROLES = ('later:roles', 'Activity roles (assign by role) come with HR roles; plans use a person or "Ask at launch"')
TEMPLATES = ('later:mail', 'Email templates come with the email module')
PROPS = ('skip', 'No HAP equivalent for per-parent dynamic fields (plan v2)')
TEMPLATE = ('native:template', 'Variant reads it through its Product relation (Odoo _inherits)')

D = {
    'mail.activity': {
        'can_write': ('hap', 'HAP role permissions decide who can edit'),
        'res_access_create': ('hap', 'HAP role permissions decide access'),
        'res_access_read': ('hap', 'HAP role permissions decide access'),
        'res_access_unlink': ('hap', 'HAP role permissions decide access'),
        'res_access_write': ('hap', 'HAP role permissions decide access'),
        'icon': ('skip', 'Icon of the activity type, display only'),
        'mail_template_ids': TEMPLATES,
        'phone': ('skip', "The related contact's phone, read through the Contact relation"),
        'res_model_id': ('native:res_model', 'Stored as Related Document Model text plus the Contact relation'),
        'res_model_name': ('skip', 'Display name of the model, display only'),
        'role_id': ROLES,
        'state': ('native:x_mail__state', 'Built as State (stored), set on save and refreshed daily by #14'),
        'technical_usage': ('skip', 'Technical marker for system activities'),
        'user_tz': ('hap', 'HAP members carry their own time zone'),
    },
    'mail.activity.plan': {
        'has_user_on_demand': ('native:responsible_type', 'Steps with "Ask at launch" make the launch ask for a person'),
        'res_model_id': ('skip', 'Plans apply to Contacts only in wave 0'),
        'steps_count': ('hap', 'Count shown on the Plan Steps tab'),
    },
    'mail.activity.plan.template': {
        'company_id': MULTI,
        'icon': ('skip', 'Icon of the activity type, display only'),
        'res_model': ('skip', "The plan's model, fixed to Contacts in wave 0"),
        'role_id': ROLES,
        'suggested_next_type_id': ('skip', 'Read through the Activity Type'),
    },
    'mail.activity.type': {
        'default_role_id': ROLES,
        'delay_label': ('skip', 'Display text of the delay'),
        'initial_res_model': HELPER,
        'kpi_provider_visibility': ('skip', 'Visibility in Odoo KPI digests, which HAP does not have'),
        'mail_template_ids': TEMPLATES,
        'res_model_change': HELPER,
    },
    'product.attribute': {
        'attribute_line_ids': REVERSE,
        'number_related_products': ('skip', 'Count of products using the attribute, display only'),
        'product_tmpl_ids': REVERSE,
        'template_value_ids': REVERSE,
    },
    'product.attribute.value': {
        'color': ('skip', 'Kanban colour index; the value keeps its HTML colour'),
        'default_extra_price_changed': HELPER,
        'display_type': ('skip', 'Read through the Attribute relation'),
        'image': ('later:ecommerce', 'Value images are for the e-shop configurator'),
        'is_used_on_products': ('skip', 'Delete guard; HAP keeps the relation and warns'),
        'pav_attribute_line_ids': REVERSE,
    },
    'product.category': {
        'company_id': MULTI,
        'product_properties_definition': PROPS,
    },
    'product.combo': {
        'base_price': ('later:sale', 'Lowest item price, used when combos are sold (wave 1)'),
        'combo_item_count': ('hap', 'Count shown on the Combo Items tab'),
        'currency_id': CUR,
    },
    'product.combo.item': {
        'company_id': MULTI,
        'currency_id': CUR,
        'lst_price': ('skip', 'Read through the Product relation'),
    },
    'product.pricelist': {
        'my_activity_date_deadline': ACTIVITY_MIXIN,
    },
    'product.pricelist.item': {
        'allowed_uom_ids': HELPER,
        'company_id': MULTI,
        'currency_id': ('skip', "The pricelist's currency, read through the Pricelist relation"),
        'is_plain_discount': HELPER,
        'is_pricelist_required': HELPER,
        'product_uom_name': HELPER,
        'product_variant_count': HELPER,
        'rule_tip': ('native:price', 'The rule texts Applies To and Price are written by the rule flow'),
    },
    'product.template.attribute.line': {
        'product_template_value_ids': ('native:x_product__build', 'The variant build flow keeps the Product Attribute Values'),
        'value_count': ('skip', 'Count of values, display only'),
    },
    'product.template.attribute.value': {
        'color': ('skip', 'Kanban colour index'),
        'currency_id': CUR,
        'display_type': ('skip', 'Read through the Attribute relation'),
        'excluded_value_ids': ('later:exclusions', 'Attribute exclusions are out of scope for wave 0'),
        'html_color': ('skip', 'Read through the Attribute Value relation'),
        'image': ('skip', 'Read through the Attribute Value relation'),
        'is_custom': ('skip', 'Read through the Attribute Value relation'),
        'show_price_extra': HELPER,
    },
    'res.company': {k: ('hap', 'HAP sends email through its own mail service and organisation settings') for k in (
        'alias_domain_id', 'bounce_email', 'bounce_formatted', 'catchall_email', 'catchall_formatted',
        'default_from_email', 'email_formatted', 'email_primary_color', 'email_secondary_color')},
    'res.partner': {
        'channel_ids': ('hap', 'HAP chat and record discussions replace Odoo Discuss'),
        'channel_member_ids': ('hap', 'HAP chat and record discussions replace Odoo Discuss'),
        'rtc_session_ids': ('hap', 'HAP chat and record discussions replace Odoo Discuss'),
        'is_in_call': ('hap', 'HAP chat and record discussions replace Odoo Discuss'),
        'email_normalized': ('skip', 'Search helper; the Email field is validated by HAP'),
        'is_blacklisted': ('later:mass-mailing', 'Comes with email marketing'),
        'is_pricelist_manually_set': ('later:sale', "The customer's pricelist comes with Sales (wave 1)"),
        'property_product_pricelist': ('later:sale', "The customer's pricelist comes with Sales (wave 1)"),
        'specific_property_product_pricelist': ('later:sale', "The customer's pricelist comes with Sales (wave 1)"),
        'my_activity_date_deadline': ACTIVITY_MIXIN,
    },
    'uom.uom': {
        'product_uom_ids': REVERSE,
    },
}

TEMPLATE_SPECIFIC = {
    'base_unit_count': UNIT_PRICE, 'base_unit_id': UNIT_PRICE, 'base_unit_name': UNIT_PRICE, 'base_unit_price': UNIT_PRICE,
    'can_image_1024_be_zoomed': IMG, 'image_1024': IMG, 'image_128': IMG, 'image_256': IMG, 'image_512': IMG,
    'color': ('skip', 'Kanban colour index'), 'cost_currency_id': CUR, 'currency_id': CUR,
    'fixed_pricelist_rule_ids': REVERSE, 'pricelist_rule_ids': REVERSE,
    'free_qty': STOCK, 'incoming_qty': STOCK, 'outgoing_qty': STOCK, 'qty_available': STOCK, 'virtual_available': STOCK,
    'has_configurable_attributes': HELPER, 'is_dynamically_created': HELPER, 'is_product_variant': HELPER,
    'import_attribute_values': ('skip', 'Import helper'), 'my_activity_date_deadline': ACTIVITY_MIXIN,
    'product_document_count': ('hap', 'The Documents attachment field shows its files'),
    'product_properties': PROPS, 'product_tooltip': HELPER,
    'product_variant_count': ('hap', 'Count shown on the Variants tab'), 'product_variant_id': HELPER,
    'seller_ids': PURCHASE, 'variant_seller_ids': PURCHASE,
    'service_tracking': ('later:sale', 'What a sold service creates (task, project) comes with Sales and Project'),
    'show_qty_update_button': HELPER, 'show_sales_price_page': HELPER,
    'uom_name': HELPER, 'volume_uom_name': HELPER, 'weight_uom_name': HELPER,
    'valid_product_template_attribute_line_ids': HELPER,
}
D['product.template'] = dict(TEMPLATE_SPECIFIC)

VARIANT_SPECIFIC = dict(TEMPLATE_SPECIFIC)
VARIANT_SPECIFIC.update({
    'can_image_variant_1024_be_zoomed': IMG, 'image_variant_1024': IMG, 'image_variant_128': IMG,
    'image_variant_256': IMG, 'image_variant_512': IMG,
    'catalog_is_in_order': ('skip', 'Order catalog helper'),
    'code': HELPER, 'partner_ref': HELPER,
    'all_product_tag_ids': ('native:additional_product_tag_ids', "The product's tags through the relation plus the variant's Additional Tags"),
    'extra_uom_ids': ('later:uom', 'Extra units per variant come with packaging rules'),
    'product_document_ids': ('hap', 'The Documents attachment field holds the files'),
    'product_template_variant_value_ids': HELPER,
    'product_uom_ids': ('native:template', 'Packagings are kept on the product'),
    'uom_ids': ('native:template', 'Units are kept on the product'),
    'product_variant_ids': ('hap', 'The Variants tab of the product'),
})


def variant_decision(field):
    return VARIANT_SPECIFIC.get(field, TEMPLATE)


def main(open_fields):
    have = set()
    with open(CSV, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            have.add((r['model'], r['field']))
    rows = []
    for model, field in open_fields:
        if (model, field) in have:
            continue
        if model == 'product.product':
            dec = variant_decision(field)
        else:
            dec = D.get(model, {}).get(field)
        if not dec:
            print('NO DECISION', model, field)
            continue
        rows.append([model, field, dec[0], dec[1]])
    raw = open(CSV, 'rb').read()
    nl = '\r\n' if b'\r\n' in raw else '\n'
    with open(CSV, 'a', encoding='utf-8', newline='') as f:
        w = csv.writer(f, lineterminator=nl)
        if not raw.endswith(nl.encode()):
            f.write(nl)
        w.writerows(rows)
    return rows


if __name__ == '__main__':
    import glob, re
    cov = sorted(glob.glob(os.path.join(HERE, '..', 'register', 'scans', '*', 'coverage.md')))[-1]
    cur, opens = None, []
    for line in open(cov, encoding='utf-8'):
        m = re.match(r'## `(.+?)`', line)
        if m:
            cur = m.group(1)
        elif line.startswith('| `') and line.rstrip().endswith('| OPEN |'):
            opens.append((cur, line.split('|')[1].strip().strip('`')))
    added = main(opens)
    print(f'{len(opens)} OPEN in {os.path.relpath(cov, HERE)}; {len(added)} decisions added')
