"""Wave 0 (plan v2), step 4c: Companies (res.company), Bank Accounts (res.partner.bank) and the hidden Company
field on Contacts and Bank Accounts.

Native choices (native-catalogue/fields.md):
- Companies show their contact's address, email, phone, tax ID and website through display-only Foreign Fields
  (type 30, strDefault "10"). Odoo keeps these on the partner as well, so there is one place to edit them.
- Bank Accounts keep Odoo's sanitized number in a Function formula field (type 53, UPPER + SUBSTITUTE).
- Company fields are hidden (fieldPermission "011": hidden / editable / shown on create) until multi-company.
Fields that point at the sheet being built (formula, foreign fields, company) are added after it exists.
Run: python step4c_companies_banks.py
"""
import json
from sheetlib import F, ensure_sheet, ensure_reverse, raw_fields, apply_spec, sheets_by_alias
from lib import hap, record

ON = [{'source': 'static', 'value': '1'}]
COMMON = '["MY","SG","ID","TH","VN","PH","BN","CN","HK","TW","JP","KR","IN","AU","GB","US"]'
HIDDEN = '011'
IMAGE = '{"type":"1","values":[]}'
STEP = 'v2 step 4c'

COMPANY = {
    'name': 'Companies', 'alias': 'res_company', 'module': 'base', 'group': 'Settings', 'icon': 'sys_18_1_apartment_house',
    'title': 'Company Name',
    'desc': 'Your own company: its contact, currency, logo and the texts printed on documents.',
    'fields': [
        F('Company Name', 'TEXT', 'name', required=True),
        F('Contact', 'RELATE_SHEET', 'partner_id', dataSource='@res_partner', multi=False, required=True,
          desc='The contact that holds the company address, tax ID, email and phone. Edit them there.',
          config={'displayMode': 'dropdown'}),
        F('Currency', 'RELATE_SHEET', 'currency_id', dataSource='@res_currency', multi=False, required=True,
          desc='Company currency.', config={'displayMode': 'dropdown'}),
        F('Logo', 'ATTACHMENT', 'logo_web', advanced_setting={'filetype': IMAGE}),
        F('Company Tagline', 'RICH_TEXT', 'report_header', desc='Printed under the logo on documents.'),
        F('Report Footer', 'RICH_TEXT', 'report_footer', desc='Printed at the bottom of documents, for example bank details.'),
        F('Company Details', 'RICH_TEXT', 'company_details', desc='Address block printed on documents.'),
        F('Primary Color', 'TEXT', 'primary_color', desc='Hex colour for printed documents, for example #875A7B.'),
        F('Secondary Color', 'TEXT', 'secondary_color', desc='Hex colour for printed documents, for example #8E8E8E.'),
        F('Sequence', 'NUMBER', 'sequence', dot=0),
        F('Active', 'SWITCH', 'active', defaultValue=ON),
    ],
}

# Odoo field on res.company -> the Contacts field it mirrors (all related to partner_id in Odoo)
FOREIGN = [('Address', 'x_base__region'), ('Street', 'street'), ('Street 2', 'street2'), ('Zip', 'zip'),
           ('City', 'city'), ('Email', 'email'), ('Phone', 'phone'), ('Website', 'website'), ('Tax ID', 'vat')]

BANK = {
    'name': 'Bank Accounts', 'alias': 'res_partner_bank', 'module': 'base', 'group': 'Contacts/Configuration',
    'icon': 'sys_atm_symbol', 'title': 'Account Number',
    'desc': 'Bank accounts of contacts and of your own company.',
    'fields': [
        F('Account Number', 'TEXT', 'account_number', required=True),
        F('Account Holder', 'RELATE_SHEET', 'partner_id', dataSource='@res_partner', multi=False, required=True,
          desc='The contact that owns this account.',
          config={'bidirectional': True, 'reverseName': 'Bank Accounts', 'displayMode': 'dropdown'}),
        F('Holder Name', 'TEXT', 'holder_name', desc='Name on the account, when it differs from the contact.'),
        F('Bank Name', 'TEXT', 'bank_name'),
        F('BIC/SWIFT', 'TEXT', 'bank_bic', desc='Bank identifier code, for example MBBEMYKL.'),
        F('Bank Address', 'AREA_COUNTY', 'x_base__region', desc='Country and state of the bank.',
          extra={'enumDefault': 1, 'enumDefault2': 2}, advanced_setting={'chooserange': '', 'commcountries': COMMON}),
        F('Street', 'TEXT', 'street'),
        F('Street 2', 'TEXT', 'street2'),
        F('Zip', 'TEXT', 'zip'),
        F('City', 'TEXT', 'city'),
        F('Trust Bank Account', 'SWITCH', 'allow_out_payment', desc='Payments may be sent to this account.'),
        F('Notes', 'TEXT', 'note', extra={'enumDefault': 1}),
        F('Sequence', 'NUMBER', 'sequence', dot=0),
        F('Active', 'SWITCH', 'active', defaultValue=ON),
    ],
}

# Odoo: sanitize = re.sub(r'\W+', '', number).upper(). HAP functions have no regex; the usual separators are removed.
SANITIZE = 'UPPER(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(${id}$," ",""),"-",""),".",""),"/",""))'


def by_alias(ws):
    return {c.get('alias'): c for c in raw_fields(ws)}


def add_once(ws, control):
    """Add one raw control unless its alias is already on the sheet; return the field as read back."""
    have = by_alias(ws)
    if control['alias'] not in have:
        hap('worksheet', 'add-fields', ws, '--controls', json.dumps([control], ensure_ascii=False))
        have = by_alias(ws)
    if control['alias'] not in have:
        raise RuntimeError(f"{control['alias']} not on {ws} after add-fields")
    return have[control['alias']]


def company_field(ws, companies, sheet_name, module):
    c = add_once(ws, {'type': 29, 'controlName': 'Company', 'alias': 'company_id', 'dataSource': companies,
                      'enumDefault': 1, 'fieldPermission': HIDDEN,
                      'desc': 'Hidden while there is one company. Shown when multi-company is switched on.',
                      'advancedSetting': {'showtype': '3'}})
    if c.get('fieldPermission') != HIDDEN:
        apply_spec([{'type': 'field.update', 'worksheet': ws, 'field': c['controlId'], 'set': {'fieldPermission': HIDDEN}}])
        c = by_alias(ws)['company_id']
    record(c['controlId'], 'field', f'{sheet_name}.Company', module, STEP)
    return c


if __name__ == '__main__':
    sheets = sheets_by_alias()
    contacts = sheets['res_partner']['id']

    # 1. Companies
    cws, craw, cfix = ensure_sheet(COMPANY, STEP)
    cfields = {c.get('alias'): c for c in craw}
    pfields = by_alias(contacts)
    rel = cfields['partner_id']['controlId']
    for name, src in FOREIGN:
        s = pfields[src]
        f = add_once(cws, {'type': 30, 'controlName': name, 'alias': src, 'dataSource': f'${rel}$',
                           'sourceControlId': s['controlId'], 'sourceControlType': s['type'], 'strDefault': '10',
                           'desc': 'From the company\'s contact.'})
        record(f['controlId'], 'field', f'Companies.{name}', 'base', STEP)
    print('Companies', cws, 'fields', len(raw_fields(cws)), 'fixes', cfix)

    # 2. Bank Accounts, with the reverse "Bank Accounts" tab on Contacts
    bws, braw, bfix = ensure_sheet(BANK, STEP)
    bfields = {c.get('alias'): c for c in braw}
    rev = ensure_reverse(contacts, bfields['partner_id']['controlId'], 'bank_ids', 'Bank Accounts', 'base', '6', STEP)
    num = bfields['account_number']['controlId']
    expr = SANITIZE.replace('{id}', num)
    s = add_once(bws, {'type': 53, 'controlName': 'Sanitized Account Number', 'alias': 'sanitized_account_number',
                       'enumDefault2': 2, 'desc': 'Account number without spaces, dashes, dots or slashes, in capitals. Used to find duplicates.',
                       'dataSource': json.dumps({'type': 'mdfunction', 'expression': expr, 'status': 1})})
    record(s['controlId'], 'field', 'Bank Accounts.Sanitized Account Number', 'base', STEP)
    # columns shown in the Contacts tab (a CLI-made multi relation has none: PLATFORM-ISSUES P5)
    bf = by_alias(bws)
    show = [bf[a]['controlId'] for a in ('account_number', 'bank_name', 'holder_name', 'allow_out_payment')]
    if (rev.get('showControls') or []) != show:
        apply_spec([{'type': 'field.update', 'worksheet': contacts, 'field': rev['controlId'], 'set': {'showControls': show}}])
    print('Bank Accounts', bws, 'fields', len(raw_fields(bws)), 'fixes', bfix, '| reverse', rev['controlId'])

    # 3. Hidden Company fields
    for ws, name in ((contacts, 'Contacts'), (bws, 'Bank Accounts')):
        c = company_field(ws, cws, name, 'base')
        print(name, 'company_id', c['controlId'], 'fieldPermission', c.get('fieldPermission'))
