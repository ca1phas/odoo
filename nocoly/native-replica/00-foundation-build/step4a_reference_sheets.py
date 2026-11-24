"""Wave 0, step 4a: the reference sheets (currencies, rates, countries, states, country groups, industries).

Fields follow Odoo 20's stored fields of module base (catalogue/odoo-20.0/odoo-fields.csv). Company fields wait
for the Companies sheet (step 4b). Run: python step4a_reference_sheets.py [alias ...]
"""
import sys
from sheetlib import F, ensure_sheet, ensure_reverse, sheets_by_alias
from lib import record

ON = [{'source': 'static', 'value': '1'}]

SPECS = [
    {'name': 'Currencies', 'alias': 'res_currency', 'module': 'base', 'group': 'Settings', 'icon': 'sys_currency-dollar_finance',
     'title': 'Currency',
     'desc': 'Currencies and their exchange rates.',
     'fields': [
         F('Currency', 'TEXT', 'name', desc='ISO 4217 code, for example MYR.', required=True),
         F('Name', 'TEXT', 'full_name', desc='Full name, for example Malaysian ringgit.'),
         F('Symbol', 'TEXT', 'symbol', desc='Shown next to amounts, for example RM.', required=True),
         F('Active', 'SWITCH', 'active', defaultValue=ON),
         F('Current Rate', 'NUMBER', 'rate', desc='Units of this currency for one unit of the company currency, from the latest rate. Kept up to date automatically.', dot=6),
         F('Inverse Rate', 'NUMBER', 'inverse_rate', desc='Company currency for one unit of this currency. Kept up to date automatically.', dot=6),
         F('Last Rate Update', 'DATE', 'rate_date', desc='Date of the rate in use.'),
         F('Decimal Places', 'NUMBER', 'decimal_places', dot=0),
         F('Rounding Factor', 'NUMBER', 'rounding', desc='Smallest coin, for example 0.01.', dot=6),
         F('Symbol Position', 'DROP_DOWN', 'position', options=['After Amount', 'Before Amount'],
           desc='Whether the symbol is placed before or after the amount.'),
         F('Currency Unit', 'TEXT', 'currency_unit_label', desc='Name of the main unit, for example Ringgit.'),
         F('Currency Subunit', 'TEXT', 'currency_subunit_label', desc='Name of the subunit, for example Sen.'),
         F('Currency Numeric Code', 'NUMBER', 'iso_numeric', desc='ISO 4217 numeric code.', dot=0),
     ]},
    {'name': 'Currency Rates', 'alias': 'res_currency_rate', 'module': 'base', 'group': 'Settings', 'icon': 'sys_currency-exchange_finance',
     'title': 'Date',
     'desc': 'One exchange rate per currency and date. The latest one becomes the currency\'s current rate.',
     'fields': [
         F('Date', 'DATE', 'name', required=True),
         F('Currency', 'RELATE_SHEET', 'currency_id', required=True, dataSource='@res_currency', multi=False,
           config={'bidirectional': True, 'reverseName': 'Rates', 'displayMode': 'dropdown'}),
         F('Technical Rate', 'NUMBER', 'rate', desc='Units of this currency for one unit of the company currency.', dot=6, required=True),
     ],
     'reverse': {'currency_id': ('rate_ids', 'Rates', 'base', '6')}},
    {'name': 'Countries', 'alias': 'res_country', 'module': 'base', 'group': 'Contacts/Configuration', 'icon': 'sys_16_5_globe_earth',
     'title': 'Country Name',
     'desc': 'Countries with their codes, phone prefix, currency and address rules.',
     'fields': [
         F('Country Name', 'TEXT', 'name', required=True),
         F('Country Code', 'TEXT', 'code', desc='Two-letter ISO code, for example MY. Must be unique.', required=True),
         F('Phone Prefix', 'NUMBER', 'phone_code', dot=0),
         F('Currency', 'RELATE_SHEET', 'currency_id', dataSource='@res_currency', multi=False, config={'displayMode': 'dropdown'}),
         F('Vat Label', 'TEXT', 'vat_label', desc='Name of the tax ID in this country, for example SST No.'),
         F('State Required', 'SWITCH', 'state_required'),
         F('Zip', 'DROP_DOWN', 'zip_applicability', options=['Required', 'Optional', 'Not Applicable']),
         F('Customer Name Position', 'DROP_DOWN', 'name_position', options=['Before Address', 'After Address']),
         F('Layout in Reports', 'TEXT', 'address_format', desc='Address layout with placeholders such as %(street)s and %(zip)s.',
           extra={'enumDefault': 1}),
         # Native Region, Global range, country level (raw keys from native-catalogue/fields.md)
         F('Region', 'AREA_COUNTY', 'x_base__region',
           desc='The same country in the built-in region list. Addresses are picked from that list and linked back to this country.',
           extra={'enumDefault': 1, 'enumDefault2': 1},
           advanced_setting={'commcountries': '["MY","SG","ID","TH","VN","PH","BN","CN","HK","TW","JP","KR","IN","AU","GB","US"]'}),
     ]},
    {'name': 'Country Groups', 'alias': 'res_country_group', 'module': 'base', 'group': 'Contacts/Configuration', 'icon': 'sys_globe3_place',
     'title': 'Name',
     'desc': 'Groups of countries, for example Europe or ASEAN, used by pricelists and taxes.',
     'fields': [
         F('Name', 'TEXT', 'name', required=True),
         F('Code', 'TEXT', 'code'),
         F('Countries', 'RELATE_SHEET', 'country_ids', dataSource='@res_country', multi=True,
           config={'bidirectional': True, 'reverseName': 'Country Groups', 'displayMode': 'tabTable'}),
     ],
     'reverse': {'country_ids': ('country_group_ids', 'Country Groups', 'base', None)}},
    {'name': 'Industries', 'alias': 'res_partner_industry', 'module': 'base', 'group': 'Contacts/Configuration', 'icon': 'sys_18_2_factory',
     'title': 'Name',
     'desc': 'Industries used to classify companies.',
     'fields': [
         F('Name', 'TEXT', 'name', required=True),
         F('Full Name', 'TEXT', 'full_name'),
         F('Active', 'SWITCH', 'active', defaultValue=ON),
     ]},
]

if __name__ == '__main__':
    only = set(sys.argv[1:])
    for spec in SPECS:
        if only and spec['alias'] not in only:
            continue
        ws, raw, fixed = ensure_sheet(spec, 'step 4a')
        rev = []
        for rel_alias, (alias, name, module, showtype) in (spec.get('reverse') or {}).items():
            rel = next(c for c in raw if c.get('alias') == rel_alias)
            c = ensure_reverse(rel['dataSource'], rel['controlId'], alias, name, module, showtype, 'step 4a')
            rev.append(f"{name} ({c['controlId']})")
        print(f"{spec['name']:16} {ws}  fields {len(raw)}, alias/desc fixes {fixed}" + (f", reverse: {', '.join(rev)}" if rev else ''))
