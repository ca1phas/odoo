"""Wave 0 (plan v2), step 4b: the Contacts sheet (res.partner) with native field types.

Raw keys come from native-catalogue/fields.md (tested live). Self-relations (parent/child, commercial entity) are
added after the sheet exists, because they point at the sheet itself. Run: python step4b_contacts.py
"""
import json
from sheetlib import F, ensure_sheet, ensure_reverse, raw_fields, apply_spec, sheets_by_alias
from lib import hap, APP, record

ON = [{'source': 'static', 'value': '1'}]
CONTACT_TAGS = '<uuid>'   # option set, see ids.json
MY = '{"name":"Malaysia","iso2":"my","dialCode":"60"}'
COMMON = '["MY","SG","ID","TH","VN","PH","BN","CN","HK","TW","JP","KR","IN","AU","GB","US"]'
TAGS = ['Vendor', 'Prospects', 'Employees', 'Consulting Services', 'Services', 'Vendor / Office Supplies',
        'Vendor / Desk Manufacturers']

SPEC = {
    'name': 'Contacts', 'alias': 'res_partner', 'module': 'base', 'group': 'Contacts', 'icon': 'sys_contacts_office',
    'title': 'Display Name',
    'desc': 'Companies and people: customers, vendors, employees and their addresses.',
    'fields': [
        F('Display Name', 'TEXT', 'complete_name', desc='How the contact appears in lists and pickers, for example "Acme, Jane Lee". Filled in automatically.'),
        F('Name', 'TEXT', 'name'),
        F('Company Type', 'FLAT_MENU', 'company_type', options=['Person', 'Company'],
          defaultValue=[{'source': 'static', 'value': 'Person'}]),
        F('Address Type', 'FLAT_MENU', 'type', options=['Contact', 'Invoice Address', 'Delivery Address', 'Other Address'],
          desc='For a person in a company: what this address is used for.',
          defaultValue=[{'source': 'static', 'value': 'Contact'}]),
        F('Job Position', 'TEXT', 'function'),
        F('Email', 'EMAIL', 'email'),
        F('Phone', 'MOBILE_PHONE', 'phone', advanced_setting={'defaultarea': MY}),
        F('Website', 'TEXT', 'website', advanced_setting={'analysislink': '1'}),
        F('Address', 'AREA_COUNTY', 'x_base__region', desc='Country and state.',
          extra={'enumDefault': 1, 'enumDefault2': 2}, advanced_setting={'chooserange': '', 'commcountries': COMMON}),
        F('Street', 'TEXT', 'street'),
        F('Street 2', 'TEXT', 'street2'),
        F('Zip', 'TEXT', 'zip'),
        F('City', 'TEXT', 'city'),
        F('Country', 'RELATE_SHEET', 'country_id', dataSource='@res_country', multi=False,
          desc='Set from the Address automatically.', config={'displayMode': 'dropdown'}),
        F('Location', 'LOCATION', 'x_base__location', desc='Optional map position, used by the map view.'),
        F('Tax ID', 'TEXT', 'vat', desc='Tax registration number, kept the same for a company and its people.'),
        F('Other Identifiers', 'TEXT', 'additional_identifiers', extra={'enumDefault': 1},
          desc='Other registration numbers, one per line.'),
        F('Reference', 'TEXT', 'ref'),
        F('Language', 'DROP_DOWN', 'lang', options=['English', 'Malay', 'Chinese (Simplified)'],
          defaultValue=[{'source': 'static', 'value': 'English'}]),
        F('Salesperson', 'USER_PICKER', 'user_id', extra={'userPermission': 1}),
        F('Tags', 'MULTI_SELECT', 'category_id', options=TAGS,
          extra={'dataSource': CONTACT_TAGS, 'enumDefault2': 1},
          advanced_setting={'checktype': '1', 'allowadd': '1'}),
        F('Industry', 'RELATE_SHEET', 'industry_id', dataSource='@res_partner_industry', multi=False,
          config={'displayMode': 'dropdown'}),
        F('Notes', 'RICH_TEXT', 'comment'),
        F('Image', 'ATTACHMENT', 'image_1920'),
        F('Barcode', 'TEXT', 'barcode'),
        F('Employee', 'SWITCH', 'employee'),
        F('Active', 'SWITCH', 'active', defaultValue=ON),
        F('Company Name', 'TEXT', 'commercial_company_name', desc='Name of the company this contact belongs to. Filled in automatically.'),
    ],
}

if __name__ == '__main__':
    ws, raw, fixed = ensure_sheet(SPEC, 'v2 step 4b')
    have = {c.get('alias'): c for c in raw}
    # self-relations, added once
    if 'parent_id' not in have:
        hap('worksheet', 'add-fields', ws, '--controls', json.dumps([{
            'type': 29, 'controlName': 'Related Company', 'alias': 'parent_id', 'dataSource': ws, 'enumDefault': 1,
            'desc': 'The company this person or address belongs to.',
            'advancedSetting': {'bidirectional': '1', 'showtype': '3'}}], ensure_ascii=False))
    if 'commercial_partner_id' not in have:
        hap('worksheet', 'add-fields', ws, '--controls', json.dumps([{
            'type': 29, 'controlName': 'Commercial Entity', 'alias': 'commercial_partner_id', 'dataSource': ws,
            'enumDefault': 1, 'desc': 'The company that holds the tax ID and invoices for this contact. Filled in automatically.',
            'advancedSetting': {'showtype': '3'}}], ensure_ascii=False))
    raw = raw_fields(ws)
    by = {c.get('alias'): c for c in raw}
    for a in ('parent_id', 'commercial_partner_id'):
        record(by[a]['controlId'], 'field', f'Contacts.{by[a]["controlName"]}', 'base', 'v2 step 4b')
    rev = ensure_reverse(ws, by['parent_id']['controlId'], 'child_ids', 'Contacts & Addresses', 'base', '6')
    print('Contacts', ws, 'fields', len(raw_fields(ws)), 'fixes', fixed, '| reverse', rev['controlId'])
    others = [c for c in raw_fields(ws) if c['type'] == 29 and c.get('sourceControlId') == by['commercial_partner_id']['controlId']]
    print('reverse fields made for commercial_partner_id:', [(c['controlName'], c.get('alias')) for c in others])
