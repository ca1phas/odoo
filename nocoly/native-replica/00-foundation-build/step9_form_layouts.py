"""Form layouts for the wave 0 sheets (Module Owner, 24 Nov 2026: "不要一个行就一个field罢了，那些短短的field甚至可以一行四个，整体要保持整齐").

HAP forms are a 12-column grid: size 3 = four per row, 4 = three, 6 = two, 9 + 3, 12 = full width.
Each LAYOUT entry is a list of rows. A row is a list of (field alias, size); a string row "§ Title" is a divider
(native 分段, type 22, created once). Sizes in a row add up to 12. Relation lists shown as tabs (showtype 6) and hidden
helper fields go after the listed rows. Read-only fields the workflows maintain (fieldPermission "101") become "100":
still shown on the record, but not on the new-record form, so dialogs such as Launch Plan show only what people fill in.

The whole field list is written back at once (`worksheet update-fields --controls @file`, the controls as read, only
row / col / size / fieldPermission changed), after a `--check` run.
Run: python step9_form_layouts.py <sheet alias> [...] | all      (add --dry to only print the plan)
"""
import json, os, sys, tempfile
from lib import hap, APP, HERE, backup, record
from sheetlib import raw_fields
from wflib import S

AUTO_RO, AUTO_RO_NOT_ON_CREATE = '101', '100'

LAYOUT = {
    'res_partner': [
        [('name', 6), ('company_type', 3), ('type', 3)],
        [('parent_id', 6), ('function', 3), ('lang', 3)],
        '§ Contact',
        [('email', 4), ('phone', 4), ('website', 4)],
        [('user_id', 3), ('category_id', 6), ('industry_id', 3)],
        '§ Address',
        [('x_base__region', 6), ('zip', 3), ('city', 3)],
        [('street', 6), ('street2', 6)],
        [('country_id', 3), ('x_base__location', 9)],
        '§ Tax and references',
        [('vat', 4), ('ref', 4), ('barcode', 4)],
        [('additional_identifiers', 12)],
        '§ Notes',
        [('comment', 12)],
        [('image_1920', 6), ('employee', 3), ('active', 3)],
        '§ Kept up to date automatically',
        [('complete_name', 4), ('commercial_partner_id', 4), ('commercial_company_name', 4)],
    ],
    'res_country': [
        [('name', 6), ('code', 3), ('phone_code', 3)],
        [('currency_id', 4), ('vat_label', 4), ('x_base__region', 4)],
        '§ Address format',
        [('zip_applicability', 4), ('name_position', 4), ('state_required', 4)],
        [('address_format', 12)],
    ],
    'res_country_group': [
        [('name', 6), ('code', 6)],
    ],
    'res_partner_industry': [
        [('name', 4), ('full_name', 4), ('active', 4)],
    ],
    'res_partner_bank': [
        [('account_number', 6), ('partner_id', 6)],
        [('holder_name', 6), ('sanitized_account_number', 6)],
        '§ Bank',
        [('bank_name', 6), ('bank_bic', 3), ('allow_out_payment', 3)],
        [('x_base__region', 6), ('zip', 3), ('city', 3)],
        [('street', 6), ('street2', 6)],
        '§ Other',
        [('note', 6), ('sequence', 3), ('active', 3)],
    ],
    'product_template': [
        [('name', 6), ('type', 6)],          # Product Type is a 3-option radio: it needs half a row
        [('categ_id', 6), ('sale_ok', 3), ('purchase_ok', 3)],
        [('default_code', 3), ('barcode', 3), ('is_storable', 3), ('is_favorite', 3)],
        '§ Prices and units',
        [('list_price', 3), ('standard_price', 3), ('uom_id', 3), ('uom_ids', 3)],
        [('product_tag_ids', 12)],
        [('combo_ids', 12)],
        [('attribute_line_ids', 12)],   # the sub-table has its own title
        '§ Descriptions',
        [('description_sale', 6), ('description_purchase', 6)],
        [('description', 12)],
        '§ Logistics',
        [('weight', 3), ('volume', 3), ('sequence', 3), ('active', 3)],
        '§ Images and documents',
        [('image_1920', 4), ('product_document_ids', 4), ('x_product__barcode_image', 4)],
    ],
    'product_product': [
        [('display_name', 6), ('product_tmpl_id', 6)],
        [('product_template_attribute_value_ids', 12)],
        [('default_code', 3), ('barcode', 3), ('lst_price', 3), ('standard_price', 3)],
        [('price_extra', 3), ('weight', 3), ('volume', 3), ('active', 3)],
        [('additional_product_tag_ids', 9), ('is_favorite', 3)],
        '§ Images',
        [('image_variant_1920', 6), ('x_product__barcode_image', 6)],
        '§ Kept up to date automatically',
        [('combination_indices', 6), ('x_product__run', 6)],
    ],
    'product_pricelist': [
        [('name', 6), ('currency_id', 3), ('sequence', 3)],
        [('country_group_ids', 9), ('active', 3)],
        [('item_ids', 12)],   # the sub-table has its own title
    ],
    'uom_uom': [
        [('name', 6), ('relative_uom_id', 6)],
        [('relative_factor', 3), ('factor', 3), ('x_uom__level', 3), ('sequence', 3)],
        [('parent_path', 9), ('active', 3)],
    ],
    'product_category': [
        [('name', 6), ('parent_id', 6)],
        [('complete_name', 6), ('x_product__number', 3), ('product_count', 3)],
        [('parent_path', 12)],
    ],
    'product_attribute': [
        [('name', 6), ('display_type', 3), ('sequence', 3)],
        [('create_variant', 9), ('active', 3)],
        [('value_ids', 12)],   # the sub-table has its own title
    ],
    'product_combo': [
        [('name', 9), ('sequence', 3)],
        [('combo_item_ids', 12)],
    ],
    'x_product__price_check': [
        [('x_product__pricelist_id', 6), ('x_product__product_id', 6)],
        [('x_product__variant_id', 6), ('x_product__qty', 3), ('x_product__date', 3)],
        '§ Result',
        [('x_product__price', 3), ('x_product__currency', 3), ('x_product__rule_id', 6)],
        [('x_product__rule_label', 6), ('x_product__name', 6)],
    ],
    'mail_activity': [
        [('summary', 6), ('activity_type_id', 3), ('date_deadline', 3)],
        [('user_id', 3), ('x_mail__state', 3), ('x_contacts__partner_id', 6)],
        [('note', 12)],
        [('attachment_ids', 12)],
        '§ Done',
        [('date_done', 3), ('x_mail__done_by', 3), ('active', 3), ('automated', 3)],
        [('feedback', 12)],
        '§ Next activity',
        [('x_mail__next_type_id', 4), ('x_mail__next_date', 4), ('x_mail__next_summary', 4)],
        '§ Source',
        [('res_model', 4), ('res_name', 4), ('res_id', 4)],
        [('activity_plan_id', 4), ('activity_template_id', 4), ('x_mail__plan_launch_id', 4)],
    ],
    'mail_activity_type': [
        [('name', 6), ('category', 3), ('res_model', 3)],
        [('summary', 6), ('decoration_type', 3), ('icon', 3)],
        '§ Schedule',
        [('delay_count', 3), ('delay_unit', 3), ('delay_from', 6)],
        [('suggested_next_type_id', 6), ('default_user_id', 3), ('active', 3)],
        [('default_note', 9), ('sequence', 3)],
    ],
    'mail_activity_plan': [
        [('name', 6), ('res_model', 3), ('active', 3)],
        [('template_ids', 12)],   # the sub-table has its own title
    ],
    'res_currency': [
        [('name', 3), ('full_name', 6), ('symbol', 3)],
        [('active', 3), ('position', 3), ('decimal_places', 3), ('rounding', 3)],
        [('currency_unit_label', 4), ('currency_subunit_label', 4), ('iso_numeric', 4)],
        '§ Current rate',
        [('rate', 4), ('inverse_rate', 4), ('rate_date', 4)],
    ],
    'res_currency_rate': [
        [('name', 4), ('currency_id', 4), ('rate', 4)],
    ],
    'res_company': [
        [('name', 6), ('partner_id', 6)],
        [('currency_id', 4), ('sequence', 4), ('active', 4)],
        '§ Address and contact',
        [('x_base__region', 6), ('zip', 3), ('city', 3)],
        [('street', 6), ('street2', 6)],
        [('email', 3), ('phone', 3), ('website', 3), ('vat', 3)],
        '§ Documents',
        [('logo_web', 6), ('primary_color', 3), ('secondary_color', 3)],
        [('report_header', 6), ('report_footer', 6)],
        [('company_details', 12)],
    ],
    'product_attribute_value': [
        [('name', 6), ('attribute_id', 3), ('sequence', 3)],
        [('html_color', 3), ('default_extra_price', 3), ('is_custom', 3), ('active', 3)],
    ],
    'product_template_attribute_line': [
        [('product_tmpl_id', 6), ('attribute_id', 3), ('sequence', 3)],
        [('value_ids', 9), ('active', 3)],
        [('x_product__label', 6), ('x_product__attribute_name', 3), ('x_product__create_variant', 3)],
    ],
    'product_template_attribute_value': [
        [('name', 6), ('product_tmpl_id', 6)],
        [('attribute_id', 4), ('product_attribute_value_id', 4), ('attribute_line_id', 4)],
        [('price_extra', 4), ('ptav_active', 4), ('sequence', 4)],
        '§ Kept up to date automatically',
        [('x_product__key', 6), ('x_product__run', 6)],
    ],
    'product_pricelist_item': [
        [('pricelist_id', 6), ('name', 6)],
        '§ Applies to',
        [('applied_on', 3), ('categ_id', 3), ('product_tmpl_id', 3), ('product_id', 3)],
        [('min_quantity', 3), ('uom_id', 3), ('date_start', 3), ('date_end', 3)],
        '§ Price computation',
        [('compute_price', 3), ('fixed_price', 3), ('price_discount', 3), ('price_markup', 3)],
        [('base', 3), ('base_pricelist_id', 3), ('price_round', 3), ('price_surcharge', 3)],
        [('price_min_margin', 3), ('price_max_margin', 3), ('price', 3), ('x_product__number', 3)],
    ],
    'product_combo_item': [
        [('combo_id', 4), ('product_id', 4), ('extra_price', 4)],
        [('x_product__label', 12)],
    ],
    'mail_activity_plan_template': [
        [('summary', 6), ('activity_type_id', 3), ('plan_id', 3)],
        [('responsible_type', 3), ('responsible_id', 6), ('sequence', 3)],
        [('delay_count', 3), ('delay_unit', 3), ('delay_from', 6)],
        [('note', 12)],
    ],
    'x_mail__plan_launch': [
        [('x_mail__plan_id', 6), ('x_mail__plan_date', 3), ('x_mail__assignee', 3)],
        [('x_contacts__partner_id', 6), ('x_mail__status', 6)],
        '§ Kept up to date automatically',
        [('x_mail__name', 12)],
        [('x_mail__message', 12)],
        [('x_mail__res_model', 4), ('x_mail__res_id', 4), ('x_mail__res_name', 4)],
    ],
    'x_product__variant_queue': [
        [('x_product__product_id', 6), ('x_product__status', 6)],
        [('x_product__name', 6), ('x_product__message', 6)],
    ],
    'x_product__combination': [
        [('x_product__product_id', 4), ('x_product__run', 4), ('x_product__done', 4)],
        [('x_product__key', 6), ('x_product__names', 6)],
        [('x_product__ptav_ids', 12)],
    ],
}


# Fields a person never fills when creating the record: hidden on the new-record form ("110" editable later, e.g.
# through a button dialog; "100" read-only, written by workflows).
NOT_ON_CREATE = {
    'mail_activity': {
        'feedback': '110', 'x_mail__next_type_id': '110', 'x_mail__next_date': '110', 'x_mail__next_summary': '110',
        'active': '110', 'automated': '100', 'res_model': '100', 'res_name': '100', 'res_id': '100',
        'activity_plan_id': '100', 'activity_template_id': '100', 'x_mail__plan_launch_id': '100',
    },
}


def module_of(alias):
    if alias.startswith(('mail_', 'x_mail__')):
        return 'mail'
    if alias.startswith('uom_'):
        return 'uom'
    if alias.startswith(('product_', 'x_product__')):
        return 'product'
    return 'base'


def controls(ws):
    d = raw_fields(ws)
    d = d.get('data', d) if isinstance(d, dict) else d
    return d if isinstance(d, list) else (d.get('controls') or [])


def ensure_dividers(alias):
    ws = S[alias]
    want = [r[2:] for r in LAYOUT[alias] if isinstance(r, str)]
    have = {c.get('controlName') for c in controls(ws) if c.get('type') == 22}
    new = [t for t in want if t not in have]
    if new:
        hap('worksheet', 'add-fields', ws, '--controls',
            json.dumps([{'type': 22, 'controlName': t, 'size': 12} for t in new], ensure_ascii=False))
        for c in controls(ws):
            if c.get('type') == 22 and c.get('controlName') in new:
                record(c['controlId'], 'field', f'{alias}.§ {c["controlName"]}', module_of(alias), 'v2 form layout (24 Nov)')
    return new


def plan(alias):
    ws = S[alias]
    ctrls = controls(ws)
    by_alias = {c.get('alias'): c for c in ctrls if c.get('alias')}
    dividers = {c.get('controlName'): c for c in ctrls if c.get('type') == 22}
    placed, rows = set(), []
    for row in LAYOUT[alias]:
        if isinstance(row, str):
            c = dividers[row[2:]]
            rows.append([(c, 12)])
        else:
            assert sum(s for _, s in row) <= 12, (alias, row)
            rows.append([(by_alias[a], s) for a, s in row])
        for c, _ in rows[-1]:
            placed.add(c['controlId'])
    rest = [c for c in ctrls if c['controlId'] not in placed]
    tabs = [c for c in rest if c.get('type') in (29, 34) and (c.get('advancedSetting') or {}).get('showtype') in ('2', '6')]
    hidden = [c for c in rest if str(c.get('fieldPermission', '')).startswith('0')]
    other = [c for c in rest if c not in tabs and c not in hidden]
    for c in other + tabs + hidden:
        rows.append([(c, 12)])
    for r, row in enumerate(rows):
        for col, (c, size) in enumerate(row):
            c['row'], c['col'], c['size'] = r, col, size
            if c.get('fieldPermission') == AUTO_RO:
                c['fieldPermission'] = AUTO_RO_NOT_ON_CREATE
            if c.get('alias') in NOT_ON_CREATE.get(alias, {}):
                c['fieldPermission'] = NOT_ON_CREATE[alias][c['alias']]
    # Relation lists shown as tabs are for reading the related records: not on the new-record form.
    for c in tabs:
        if (c.get('fieldPermission') or '111') == '111':
            c['fieldPermission'] = '110'
    # A divider whose fields are all hidden on the new-record form would show as an empty heading there.
    def on_create(c):
        p = c.get('fieldPermission') or '111'
        return p[0] == '1' and p[2] == '1'
    section, sections = None, {}
    for row in rows:
        for c, _ in row:
            if c.get('type') == 22:
                section = c
                sections[section['controlId']] = []
            elif section is not None and c in placed_controls(rows):
                sections[section['controlId']].append(c)
    for c in ctrls:
        if c.get('type') == 22 and c['controlId'] in sections:
            members = sections[c['controlId']]
            c['fieldPermission'] = '111' if any(on_create(m) for m in members) else '110'
    return ctrls, other


def placed_controls(rows):
    return [c for row in rows for c, _ in row]


def apply(alias, dry=False):
    new = [] if dry else ensure_dividers(alias)
    ctrls, other = plan(alias)
    if other:
        print(f'  {alias}: not in the layout, put at the end: {[c.get("alias") or c.get("controlName") for c in other]}')
    if dry:
        return
    backup(f'layout-before-{alias}', controls(S[alias]))
    fd, path = tempfile.mkstemp(suffix='.json', dir=os.path.join(HERE, 'backups'))
    os.close(fd)
    json.dump(ctrls, open(path, 'w', encoding='utf-8'), ensure_ascii=False)
    # --check exits 1 whenever it lists anything, including what is already wrong on the sheet ("current"), and
    # lib.hap cuts error output at 500 characters, so run it directly. Only issues the new layout would add
    # ("proposed" but not "current") stop the save.
    import subprocess
    from lib import PROFILE, ENV
    r = subprocess.run(['hap', '--profile', PROFILE, '--json', 'worksheet', 'update-fields', S[alias], '--controls', '@' + path,
                        '--check'], capture_output=True, env=ENV)
    out = r.stdout.decode('utf-8', 'replace').strip()
    if r.returncode != 0:
        try:
            rep = json.loads(out)
        except ValueError:
            print(f'  {alias}: CHECK FAILED {(out or r.stderr.decode("utf-8", "replace"))[:600]}')
            return
        key = lambda p: (p.get('kind'), p.get('controlId'), p.get('missing'))
        current = {key(p) for p in rep.get('current') or []}
        added = [p for p in rep.get('proposed') or [] if key(p) not in current]
        if added or rep.get('warnings'):
            print(f'  {alias}: CHECK FAILED {json.dumps(added or rep.get("warnings"), ensure_ascii=False)[:600]}')
            return
    res = hap('worksheet', 'update-fields', S[alias], '--controls', '@' + path, ok_fail=True)
    after = {c['controlId']: c for c in controls(S[alias])}
    wrong = [c.get('alias') or c.get('controlName') for c in ctrls
             if c['controlId'] not in after or (after[c['controlId']].get('row'), after[c['controlId']].get('col'),
                                                 after[c['controlId']].get('size')) != (c['row'], c['col'], c['size'])]
    print(f'  {alias}: dividers added {new}; saved {len(ctrls)} controls; '
          f'{"readback OK" if not wrong and len(after) == len(ctrls) else "READBACK DIFFERS " + str(wrong[:8]) + " count " + str(len(after))}'
          + ('' if not res.get('_error') else ' | save said: ' + res['_error'][:300]))


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    names = list(LAYOUT) if args == ['all'] else args
    for n in names:
        apply(n, dry='--dry' in sys.argv)
