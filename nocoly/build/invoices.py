#!/usr/bin/env python3
"""Build the Invoices worksheet (Odoo account.move, as on casimir.odoo.com saas~19.4) in ERP Master.

Teh Li Wei built the skeleton on 15 Sep 2026 — the worksheet, three tabs, two dividers, an empty remark block and
nine fields, with no rules, buttons, views or records. This script keeps every one of his control ids and closes
the gaps against the casimir reference: the fifteen fields Odoo's form needs that were missing, the three remark
blocks, Odoo's help and placeholders, the five interaction rules, Confirm / Cancel / Reset to Draft with the
numbering the Odoo `sequence.mixin` produces, the three list views, and the tenant's three invoices with their three
customers. Requirements: nocoly/worksheets/06-invoices.md. Generic helpers: common.py. Run from the repo root with
the CLI's interpreter:

    ~/.hap-venv/bin/python nocoly/build/invoices.py layout      # 1. rename three of Teh Li Wei's controls, add the
                                                                #    fifteen missing fields and the three remark
                                                                #    blocks, place everything in its tab, set the
                                                                #    title field, help, hints, defaults, decimals,
                                                                #    required and read-only
    ~/.hap-venv/bin/python nocoly/build/invoices.py rules       # 2. the eight interaction rules and the two journal
                                                                #    checks (upsert by name)
    ~/.hap-venv/bin/python nocoly/build/invoices.py views       # 3. Invoices, Bills and Journal Entries
    ~/.hap-venv/bin/python nocoly/build/invoices.py buttons     # 4. Confirm / Cancel / Reset to Draft and their
                                                                #    workflows, numbering included
    ~/.hap-venv/bin/python nocoly/build/invoices.py customers   # 5. the tenant customers, into Contacts
    ~/.hap-venv/bin/python nocoly/build/invoices.py seed        # 6. the tenant invoices, then verify
    ~/.hap-venv/bin/python nocoly/build/invoices.py all         # every step above, then check
    ~/.hap-venv/bin/python nocoly/build/invoices.py numbering   #    just the Confirm chain (part of `buttons`)

    ~/.hap-venv/bin/python nocoly/build/invoices.py verify      # compare the live documents with the seed file
    ~/.hap-venv/bin/python nocoly/build/invoices.py check       # controls, options, defaults, rules, views, buttons
                                                                #    and the numbering workflow against this spec
    ~/.hap-venv/bin/python nocoly/build/invoices.py selfcheck   # confirm five TEST drafts and read the numbers
                                                                #    back (INV, RINV, BILL, MISC), then Reset to
                                                                #    Draft and Cancel, both keeping the number
    ~/.hap-venv/bin/python nocoly/build/invoices.py order       # each view's records, in the view's own order
    ~/.hap-venv/bin/python nocoly/build/invoices.py document "INV/2026/00001"   # one document's stored values
    ~/.hap-venv/bin/python nocoly/build/invoices.py untouched   # the other five worksheets: control count and digest
    ~/.hap-venv/bin/python nocoly/build/invoices.py incoterm    # Incoterm (Relation → Incoterms, active only) and
                                                                #    Incoterm Location, appended; the rule hiding both
                                                                #    on a receipt (22 Sep 2026)
    ~/.hap-venv/bin/python nocoly/build/invoices.py selfincoterm # set both on a TEST invoice, read them back through
                                                                #    both read paths, put them back
    ~/.hap-venv/bin/python nocoly/build/invoices.py payments    # Register Payment (23 Sep 2026): Payment Status, Amount
                                                                #    Paid, Last Payment Date and the two hidden inputs,
                                                                #    appended; Amount Due made a Formula in place; the
                                                                #    two payment rules; the button, its fill-in form and
                                                                #    its workflow, published; Cancel and Reset to Draft
                                                                #    refused on a paid or partly paid document
    ~/.hap-venv/bin/python nocoly/build/invoices.py selfpayment # a part payment, a refused overpayment and the rest on
                                                                #    a TEST posted invoice, read back through both paths
    ~/.hap-venv/bin/python nocoly/build/invoices.py show        # the live control list

Every step reads the live worksheet first and is safe to re-run; a second run writes nothing.

**Payment Terms (bundle 3, 17 Sep 2026).** Teh Li Wei's text control Payment Terms (`6aa920d74a73a3142152e68d`) was
replaced by a relation to the Payment Terms worksheet and **deleted**, with the owner's approval, once its three values
had been carried into the relation and read back (`payterms.py`, `worksheets/10-payment-terms.md`). This script owns the
relation's place, alias and placeholder like any other control's, two new rules, and the dating chain at the end of
Confirm (built by `payterms.ensure_dating`), with Confirm's writes starting no other workflow so the Invoice Date it
fills does not date the invoice a second time through automation D (`payterms.ensure_quiet`, 17 Sep 2026);
`payterms.py` owns the relation's creation and picker filter, and automations C and D. The seed writes the relation,
by term name, and never text.

Nothing here touches the Sales app, any worksheet but Invoices, or anything in Contacts but the three customer
records this worksheet needs. Every write step compares the other worksheets' controls by id before and after.

Profile. hap-cli 0.8.31 picks the account as --profile > $HAP_PROFILE > the active profile, so this script passes
none and runs on any machine whose active profile reaches ERP Master.
"""
import hashlib
import json
import os
import re
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import common as C
import hap

APP = hap.ids()['app']
WORKSHEET = hap.ids()['worksheets'].get('Invoices', '6aa90facf363582dd37a62f7')
CONTACTS = hap.ids()['worksheets']['Contacts']
JOURNALS = hap.ids()['worksheets']['Journals']
ALIAS_WORKSHEET = 'account_move'                   # BUILDING.md: a worksheet's alias is its Odoo model
KEY = 'Invoices: '                                 # ids.json key prefix for everything this worksheet owns
HERE = Path(__file__).resolve().parent
SEED = HERE.parent / 'data' / 'casimir-invoice-seed.json'
OTHERS = ('Contacts', 'Units & Packagings', 'Products', 'Product Variants', 'Journals')   # must stay untouched

DIVIDER = 22                                       # HAP's 分段 divider: a heading; its `desc` renders nowhere
SUBLIST = 34                                       # the Invoice Lines worksheet, mounted by 07 (invlines.py)
NOTE = 10010                                       # HAP's remark block: HTML in `dataSource`, hidetitle "1"
RELATION = 29
DROPDOWN = 11


def option(key, value, index, color, checked=False):
    return {'key': key, 'value': value, 'isDeleted': False, 'index': index, 'checked': checked, 'color': color}


# Odoo's selections on account.move, in Odoo's own order. The keys are minted once here and never re-minted:
# records point at them.
TYPE_OPTIONS = [                                   # move_type
    option('2bb605fc-e40a-4a1d-983e-fb88e99993b8', 'Journal Entry', 1, '#D2D2D2'),
    option('af9b889e-8e84-41ba-ac42-39a1b7a26039', 'Customer Invoice', 2, '#C9E6FC', True),
    option('eab71e3d-2d43-4cd3-af65-28c3f35ebd8c', 'Customer Credit Note', 3, '#C3F2F2'),
    option('85e5899a-cc81-4f02-a4d1-a77fbd62ce55', 'Vendor Bill', 4, '#FFE7B1'),
    option('9811176a-1c10-40bd-99fa-adcf3e9245bf', 'Vendor Credit Note', 5, '#FBD2BF'),
    option('82d8153e-55f1-4482-9990-7a8071f0a1b3', 'Sales Receipt', 6, '#C2F1D2'),
    option('1a4c9b60-1c40-41b1-b734-3f891525b225', 'Purchase Receipt', 7, '#E6D7FA'),
]
STATUS_OPTIONS = [                                 # state
    option('0979d4bb-c722-4fa4-9591-1bfb0fb04d05', 'Draft', 1, '#D2D2D2', True),
    option('4524c691-8ce2-46bf-8a27-c2a857379a81', 'Posted', 2, '#C2F1D2'),
    option('4aebbafe-909e-468e-b5ff-9cbdee232765', 'Cancelled', 3, '#FBD2BF'),
]
TAX_MODE_OPTIONS = [                               # document_tax_mode (19.4 only; not in the 19.0 source)
    option('a28c4e64-a9eb-403c-b8e8-1b9d9d7e0d19', 'Tax Excluded', 1, '#C9E6FC', True),
    option('40d95be2-0c0b-42a0-b8cf-2bf313138913', 'Tax Included', 2, '#C3F2F2'),
]
AUTO_POST_OPTIONS = [                              # auto_post
    option('d4ba563c-b2e7-48b3-a6bb-017da4bea19a', 'No', 1, '#D2D2D2', True),
    option('8046aa91-295b-49dc-b6b8-abd35ebf6bf4', 'At Date', 2, '#C9E6FC'),
    option('666e9b3f-8e38-438d-a354-38b56737589a', 'Monthly', 3, '#C3F2F2'),
    option('744e55ed-97ff-4d75-bcd0-a32eceea3094', 'Quarterly', 4, '#C2F1D2'),
    option('f0b8149c-d6a9-4838-a9a4-6da7bc06919a', 'Yearly', 5, '#FFE7B1'),
]
PAYMENT_STATUS_OPTIONS = [                        # payment_state — the three of Odoo's seven this app can reach
    option('3d0c6b1e-5a52-4f0e-9c1a-8f1f6a0e2b41', 'Not Paid', 1, '#FBD2BF', True),
    option('b6f3c2d4-7e19-4a8b-a5d0-2c9e4f7b1a63', 'Partially Paid', 2, '#FFE7B1'),
    option('e8a1d5f7-3c64-4b2e-9f80-6d7c1b3a5e92', 'Paid', 3, '#C2F1D2'),
]
OPTIONS = {'Type': TYPE_OPTIONS, 'Status': STATUS_OPTIONS, 'Tax mode': TAX_MODE_OPTIONS,
           'Auto-post': AUTO_POST_OPTIONS, 'Payment Status': PAYMENT_STATUS_OPTIONS}
DEFAULT_OPTION = {name: next(o['key'] for o in opts if o['checked']) for name, opts in OPTIONS.items()}
LABEL = {name: {o['key']: o['value'] for o in opts} for name, opts in OPTIONS.items()}
OPTION_KEY = {name: {o['value']: o['key'] for o in opts} for name, opts in OPTIONS.items()}

CUSTOMER_TYPES = ['Customer Invoice', 'Customer Credit Note', 'Sales Receipt']     # Odoo is_sale_document(True)
VENDOR_TYPES = ['Vendor Bill', 'Vendor Credit Note', 'Purchase Receipt']          # Odoo is_purchase_document(True)
CREDIT_NOTES = ['Customer Credit Note', 'Vendor Credit Note']                     # Odoo's R + prefix sequences
# Odoo is_invoice(include_receipts=True): every type but a plain journal entry — what _post dates, and what the
# SQL constraint account_move_check_document_tax_mode_set covers.
INVOICE_TYPES = [o['value'] for o in TYPE_OPTIONS if o['value'] != 'Journal Entry']

# ── Teh Li Wei's skeleton, 15 controls, kept id for id ──────────────────────
# Three carry a name this build changes; the remark block also loses its clash with the divider above it.
FIRST_BUILD = {
    '6aa920d74a73a3142152e689': ('Customer', RELATION),
    '6aa920d74a73a3142152e68b': ('Invoice Date', 15),
    '6aa920d74a73a3142152e68c': ('Due Date', 15),
    # '6aa920d74a73a3142152e68d': ('Payment Terms* (Future Relation)', 2) — the text stand-in, deleted on 17 Sep 2026
    # by the Payment Terms bundle once a relation held its values; the relation took its place, name and alias.
    '6aa920d74a73a3142152e68e': ('Invoice Lines', C.TAB),
    '6aa920d74a73a3142152e68f': ('Other Info', C.TAB),
    '6aa920d74a73a3142152e690': ('Invoice', DIVIDER),
    '6aa920d74a73a3142152e691': ('Invoice', NOTE),
    '6aa920d74a73a3142152e692': ('Customer Reference', 2),
    '6aa920d74a73a3142152e693': ('Salesperson', 26),
    '6aa920d74a73a3142152e694': ('Recipient Bank (Relation in Odoo)', 2),
    '6aa920d74a73a3142152e695': ('Payment Reference', 2),
    '6aa920d74a73a3142152e696': ('Delivery Date', 15),
    '6aa920d74a73a3142152e697': ('Accounting', DIVIDER),
    '6aa920d74a73a3142152e698': ('MyInvois', C.TAB),
}
RENAME = {                                         # control id -> the name this build gives it
    '6aa920d74a73a3142152e689': 'Customer / Vendor',           # Odoo renames the one field per document type
    '6aa920d74a73a3142152e694': 'Recipient Bank',              # same
    '6aa920d74a73a3142152e691': 'Invoice note',                # a remark block's name is internal (hidetitle "1");
}                                                              # "Invoice" also clashed with the divider above it

# ── 1 · the form ────────────────────────────────────────────────────────────

INVOICE_LINES, OTHER_INFO, MYINVOIS = 'Invoice Lines', 'Other Info', 'MyInvois'
LINES = 'Lines'                                    # 07's mounted subtable, inside the Invoice Lines tab
NOTE_LINES, NOTE_OTHER, NOTE_MYINVOIS = 'Invoice Lines note', 'Invoice note', 'MyInvois note'
TABS = (INVOICE_LINES, OTHER_INFO, MYINVOIS)
JOURNAL_TYPE = 'Journal Type'                      # a stored lookup of the Journal's Type; see PLACE below

# Odoo saas~19.4 view_move_form on HAP's 12-column grid. Odoo's header buttons become Confirm / Cancel / Reset to
# Draft and Status as a read-only field; the h1 Number follows; then Odoo's left column (the partner) beside its
# right column (the dates, the journal and the tax mode); then Odoo's three notebook pages as HAP tabs.
# Rows from 12 down moved 3 lower on 23 Sep 2026, when Amount Paid, Last Payment Date, Payment Status and the
# two Register Payment inputs took rows 12-14 under the totals (PAYMENT_PLACE).
PLACE = {  # name -> (row, col, size, tab)
    'Status': (0, 0, 6, None),                   'Type': (0, 1, 6, None),
    'Number': (1, 0, 12, None),
    'Customer / Vendor': (2, 0, 6, None),        'Invoice Date': (2, 1, 6, None),
    'Delivery Address': (3, 0, 6, None),         'Accounting Date': (3, 1, 6, None),
    'Due Date': (4, 0, 6, None),                 'Payment Terms': (4, 1, 6, None),
    'Journal': (5, 0, 6, None),                  'Tax mode': (5, 1, 6, None),
    INVOICE_LINES: (6, 0, 12, None),
    NOTE_LINES: (7, 0, 12, INVOICE_LINES),
    # 07 Invoice Lines mounts its worksheet here as a 子表 (type 34), right under the remark block; everything
    # below it moved down one row to make room. `invlines.py place_subtable` owns the control itself.
    LINES: (8, 0, 12, INVOICE_LINES),
    'Terms and Conditions': (9, 0, 12, INVOICE_LINES),
    'Untaxed Amount': (10, 0, 6, INVOICE_LINES), 'Tax': (10, 1, 6, INVOICE_LINES),
    'Total': (11, 0, 6, INVOICE_LINES),          'Amount Due': (11, 1, 6, INVOICE_LINES),
    OTHER_INFO: (15, 0, 12, None),
    'Invoice': (16, 0, 12, OTHER_INFO),          # Odoo's <group name="invoice"> heading (divider, type 22)
    NOTE_OTHER: (17, 0, 12, OTHER_INFO),
    'Customer Reference': (18, 0, 6, OTHER_INFO), 'Salesperson': (18, 1, 6, OTHER_INFO),
    'Recipient Bank': (19, 0, 6, OTHER_INFO),     'Payment Reference': (19, 1, 6, OTHER_INFO),
    'Delivery Date': (20, 0, 6, OTHER_INFO),
    # Row 18 holds Sales Orders and Sales Order Count, placed 23 Sep 2026 when the order → invoice link
    # landed, so everything from Accounting down sits one row lower than the first build put it.
    'Accounting': (22, 0, 12, OTHER_INFO),       # Odoo's <group name="accounting_info_group"> heading
    'Source Document': (23, 0, 6, OTHER_INFO),   'Auto-post': (23, 1, 6, OTHER_INFO),
    'Auto-post until': (24, 0, 6, OTHER_INFO),
    # Not an Odoo field: a stored lookup of the Journal's Type, added 21 Sep 2026 so the two journal checks
    # below have something on this worksheet to compare (15 §1.3). Odoo reads `journal_id.type` straight off
    # the relation and stores nothing; a HAP rule condition can only name a control of its own worksheet.
    JOURNAL_TYPE: (24, 1, 6, OTHER_INFO),
    MYINVOIS: (26, 0, 12, None),
    NOTE_MYINVOIS: (27, 0, 12, MYINVOIS),
}

# What each remark block says, as the HTML the block stores. For the app's users only (owner, 22 Sep 2026): what
# that part of the form is for, in plain words. The Odoo text these replaced — the Invoice Lines one as
# `taxes.py note` had rewritten it on 18 Sep 2026 — is kept word for word at the foot of 06-invoices.md.
# `taxes.py` LINES_NOTE_TEXT carries the same Invoice Lines text, so its `note` step does not put the old one back.
HTML = {
    NOTE_LINES: '<p>Add the products, sections and notes of this document in the table below. Untaxed Amount, Tax, '
                'Total and Amount Due are worked out from these lines.</p>',
    NOTE_OTHER: "<p>More details for this document: the customer's or vendor's reference, the salesperson, the "
                'bank account it is paid into, the payment reference and the delivery date.</p>',
    NOTE_MYINVOIS: "<p>This tab is for MyInvois, Malaysia's e-invoicing system, and has nothing to fill in.</p>",
}

HINTS = {  # Odoo's placeholders on this form; every other field's placeholder is cleared
    'Invoice Date': 'Today',
    'Payment Terms': 'Payment Terms',
    'Payment Reference': 'Standard communication',
    'Terms and Conditions': 'Terms and Conditions',
}
DESC = {  # Odoo's help where it reads well for a user, else plain words — only what the field does
    # (owner's rule, 22 Sep 2026). Build notes and Odoo references: worksheets/06-invoices.md, foot.
    'Number': "Given when the document is confirmed, from the journal's Sequence Prefix and the year of the "
              'Accounting Date, e.g. INV/2026/00001. Shows "Draft" until then.',
    'Type': 'The kind of document: an invoice, credit note, bill, receipt or journal entry.',
    'Status': 'Draft until Confirm posts the document. Cancel makes it Cancelled, and Reset to Draft takes it back.',
    'Customer / Vendor': 'The customer on a customer document, the vendor on a vendor bill or vendor credit note.',
    'Delivery Address': 'The address the goods or services are delivered to.',
    'Invoice Date': "The date of the invoice or bill. Required on a bill. Confirm fills in today's date if it is "
                    'left blank.',
    'Accounting Date': 'The date the entry is booked under, and the year the number is taken from.',
    'Due Date': 'When payment is due. Choosing Payment Terms works it out.',
    'Payment Terms': '',                          # Odoo's field has no help; the stand-in's description went with it
    'Journal': 'The journal the document is recorded in. Its Sequence Prefix numbers the document, so it cannot be '
               'changed once the document has a number.',
    'Tax mode': 'Whether the line prices exclude or include tax.',
    'Terms and Conditions': '',
    'Untaxed Amount': "The sum of the lines' subtotals, before tax.",
    'Tax': 'The tax on the lines.',
    'Total': 'The amount to pay, tax included.',
    'Amount Due': 'What is still to be paid on this document: the Total less the Amount Paid.',
    'Customer Reference': "The customer's reference for this invoice, or the vendor's reference on a bill.",
    'Salesperson': '',
    'Recipient Bank': "The bank account the invoice will be paid into: the company's account on a customer invoice "
                      "or vendor credit note, otherwise the partner's.",
    'Payment Reference': 'The payment reference to set on journal items.',
    'Delivery Date': '',
    'Source Document': 'The document(s) that generated the invoice.',
    'Auto-post': 'Specify whether this entry is posted automatically on its accounting date, and any similar '
                 'recurring invoices.',
    'Auto-post until': 'This recurring move will be posted up to and including this date.',
    JOURNAL_TYPE: 'The type of the selected journal.',
    # The two dividers carry no description: HAP renders a type-22 divider's `desc` nowhere at all.
    'Invoice': '', 'Accounting': '',
}
REQUIRED = {'Type', 'Accounting Date', 'Journal', 'Auto-post'}   # Tax mode and Invoice Date are required by a rule
READONLY = {'Number', 'Status', 'Untaxed Amount', 'Tax', 'Total', 'Amount Due', 'Source Document', JOURNAL_TYPE}
TITLE = 'Number'
# A Date field's default of "today". `staticValue` is a **sentinel, not a day offset**: "2" with `time` "current"
# is HAP's 当天 (the current day) — the shape hap-cli's own captured payload asserts (tests/test_core.py
# `test_date_now_default`, "日期+默认值当天") and the one Teh Li Wei's UI-built Due Date carried. An empty
# `staticValue`, which the first cut of this script wrote, is stored happily and applies nothing.
TODAY = json.dumps([{'rcid': '', 'cid': '', 'staticValue': '2', 'time': 'current'}], separators=(',', ':'))
ADVANCED = {  # advancedSetting keys this script owns
    'Number': {'defsource': C.static_default('Draft')},
    'Type': {'defsource': C.static_default(DEFAULT_OPTION['Type'])},
    'Status': {'defsource': C.static_default(DEFAULT_OPTION['Status'])},
    'Accounting Date': {'defsource': TODAY},
    'Due Date': {'defsource': '[]'},              # the first build's "two days from today" — Odoo has no default
    'Invoice Date': {'defsource': '[]'},
    'Tax mode': {'defsource': C.static_default(DEFAULT_OPTION['Tax mode'])},
    'Auto-post': {'defsource': C.static_default(DEFAULT_OPTION['Auto-post'])},
    'Untaxed Amount': {'defsource': C.static_default(0)},
    'Tax': {'defsource': C.static_default(0)},
    'Total': {'defsource': C.static_default(0)},
    # Amount Due carried a static 0 until 23 Sep 2026, when `payments` made it a Formula (Total − Amount Paid);
    # a Formula carries no default, so it is no longer listed here.
    NOTE_LINES: {'hidetitle': '1'},
    NOTE_OTHER: {'hidetitle': '1'},
    NOTE_MYINVOIS: {'hidetitle': '1'},
}
AMOUNTS = ('Untaxed Amount', 'Tax', 'Total', 'Amount Due')
NEW = {  # controls this script adds: name -> (builder type, alias, extra control keys)
    'Number': ('TEXT', 'name', {'enumDefault': 2}),
    'Type': ('DROP_DOWN', 'move_type', {}),
    'Status': ('DROP_DOWN', 'state', {}),
    'Delivery Address': ('RELATE_SHEET', 'partner_shipping_id', {}),
    'Accounting Date': ('DATE', 'date', {}),
    'Journal': ('RELATE_SHEET', 'journal_id', {}),
    'Tax mode': ('DROP_DOWN', 'document_tax_mode', {}),
    'Terms and Conditions': ('RICH_TEXT', 'narration', {}),
    'Untaxed Amount': ('NUMBER', 'amount_untaxed', {'dot': 2}),
    'Tax': ('NUMBER', 'amount_tax', {'dot': 2}),
    'Total': ('NUMBER', 'amount_total', {'dot': 2}),
    'Amount Due': ('NUMBER', 'amount_residual', {'dot': 2}),
    'Source Document': ('TEXT', 'invoice_origin', {'enumDefault': 2}),
    'Auto-post': ('DROP_DOWN', 'auto_post', {}),
    'Auto-post until': ('DATE', 'auto_post_until', {}),
    # `journal_type` is not an Odoo field name — Odoo stores nothing for it — so the house convention
    # (an alias is the Odoo field) has nothing to offer here; the name says what the control holds.
    JOURNAL_TYPE: ('SHEET_FIELD', 'journal_type', {'strDefault': '00', 'dot': 0}),   # '00' = a stored lookup
    NOTE_LINES: (NOTE, '', {}),
    NOTE_MYINVOIS: (NOTE, '', {}),
}
RELATIONS = {'Delivery Address': CONTACTS, 'Journal': JOURNALS}      # one-way; neither target gets a reverse field
# The Payment Terms bundle's relation — one-way too. Not in NEW: payterms.py creates it (the text stand-in held the
# name and alias until it was deleted), and `check` reads its target back from here.
if hap.ids()['worksheets'].get('Payment Terms'):
    RELATIONS['Payment Terms'] = hap.ids()['worksheets']['Payment Terms']
# Odoo's field names on account.move. The skeleton's nine controls carry no alias at all, so giving them Odoo's
# name keeps nothing and breaks nothing — and makes `record get` read the worksheet in Odoo's own vocabulary.
ALIAS = dict({name: spec[1] for name, spec in NEW.items()}, **{
    'Customer / Vendor': 'partner_id', 'Invoice Date': 'invoice_date', 'Due Date': 'invoice_date_due',
    'Payment Terms': 'invoice_payment_term_id', 'Customer Reference': 'ref', 'Salesperson': 'invoice_user_id',
    'Recipient Bank': 'partner_bank_id', 'Payment Reference': 'payment_reference', 'Delivery Date': 'delivery_date',
})


def new_control(name):
    """A control to add. A remark block is sent as raw JSON (hap-cli has no builder for type 10010); a Relation is
    one-way, added without a client id so the server mints it and the target worksheet stays untouched."""
    kind, alias, extra = NEW[name]
    row, col, size, _ = PLACE[name]
    if kind == NOTE:
        return {'controlName': name, 'type': NOTE, 'row': row, 'col': col, 'size': size, 'alias': alias,
                'dataSource': HTML[name], 'advancedSetting': {'hidetitle': '1'}, 'desc': '', 'hint': '',
                'required': False, 'unique': False}
    if name == JOURNAL_TYPE:
        # A stored lookup reads *through* a Relation on this worksheet: `data_source` is the Journal
        # relation's controlId (the helper wraps it in "$…$") and `source_control_id` the column on
        # Journals. It stores the source dropdown's **option key**, the way Invoice Lines' Status does.
        live = hap.by_name(c for c in hap.controls(WORKSHEET) if c['type'] != C.TAB)
        if 'Journal' not in live:
            sys.exit(f'{JOURNAL_TYPE} reads through the Journal relation, which is not on the worksheet yet')
        return C.control(kind, name, (row, col, size), alias=alias, hint='', desc=DESC.get(name, ''),
                         readonly=True, data_source=live['Journal']['controlId'],
                         source_control_id=C.fields(JOURNALS)['Type']['controlId'], extra=extra)
    advanced = dict(ADVANCED.get(name) or {})
    if name in RELATIONS:
        advanced.update(bidirectional='0', showtype='3')                       # 3 = dropdown
    # The title field is not claimed here: two controls carrying attribute 1 in one save is undefined. The
    # layout save below moves it onto Number and clears it everywhere else in a single write.
    return C.control(kind, name, (row, col, size), alias=alias, hint=HINTS.get(name, ''), desc=DESC.get(name, ''),
                     readonly=name in READONLY, required=name in REQUIRED,
                     options=OPTIONS.get(name), data_source=RELATIONS.get(name),
                     multi=False if name in RELATIONS else None,
                     advanced_setting=advanced or None, extra=extra or None)


def desired(c, tab_ids):
    """The attributes `layout` owns on control c, as they should read back. A tab owns its place only; a divider
    its place and an empty description; a remark block its place and its HTML; a field all of it."""
    name = c['controlName']
    row, col, size, tab = PLACE[name]
    want = {'row': row, 'col': col, 'size': size, 'sectionId': tab_ids.get(tab, '') if tab else ''}
    if c['type'] in (C.TAB, SUBLIST):              # a 子表's columns, name and help belong to invlines.py
        return want
    if c['type'] == NOTE:
        want['dataSource'] = HTML[name]
        return want
    want['desc'] = DESC.get(name, '')
    if c['type'] == DIVIDER:
        return want
    want.update(hint=HINTS.get(name, ''), required=name in REQUIRED, alias=ALIAS.get(name, ''),
                attribute=1 if name == TITLE else 0,
                fieldPermission='101' if name in READONLY else '111')
    if name in AMOUNTS:
        want['dot'] = 2
    return want


def layout_differences(ctrls):
    tab_ids = {c['controlName']: c['controlId'] for c in ctrls if c['type'] == C.TAB}
    out = {}
    normal = lambda k, v: (v or 0) if k == 'attribute' else v      # `attribute` is absent on a non-title control
    for c in ctrls:
        if c['controlName'] not in PLACE:
            continue
        diff = {k: (c.get(k), v) for k, v in desired(c, tab_ids).items() if normal(k, c.get(k)) != v}
        adv = c.get('advancedSetting') or {}
        diff.update({f'advancedSetting.{k}': (adv.get(k), v)
                     for k, v in ADVANCED.get(c['controlName'], {}).items() if adv.get(k) != v})
        if diff:
            out[c['controlName']] = diff
    return out


# ── the other worksheets, untouched ─────────────────────────────────────────

SIGNATURE = ('controlName', 'type', 'alias', 'row', 'col', 'size', 'sectionId', 'required', 'attribute', 'unique',
             'fieldPermission', 'dataSource', 'sourceControlId', 'showControls', 'advancedSetting', 'desc', 'hint')


def signatures():
    """Every other Phase 1 worksheet's controls by id (a full save elsewhere can reorder their listing)."""
    return {name: sorted(json.dumps([c['controlId']] + [c.get(k) for k in SIGNATURE], sort_keys=True,
                                    ensure_ascii=False)
                         for c in hap.controls(hap.ids()['worksheets'][name])) for name in OTHERS}


def check_untouched(before):
    after = signatures()
    for name in before:
        if after[name] != before[name]:
            sys.exit(f'{name} controls changed: {sorted(set(after[name]) ^ set(before[name]))}')
    print('  untouched: ' + ', '.join(f'{n} ({len(after[n])})' for n in after))


def step_untouched():
    """Control count and digest of every other Phase 1 worksheet — run before and after a build."""
    for name, sig in signatures().items():
        digest = hashlib.sha256(''.join(sig).encode()).hexdigest()[:16]
        print(f'  {name:<20} {len(sig):>2} controls  sha256:{digest}')


def save_controls(ctrls):
    """A full SaveWorksheetControls save, proving the other worksheets' controls unchanged.

    Through the CLI's own session, not `worksheet update-fields --controls`: since 07 mounted Invoice Lines
    here, the 子表's `relationControls` snapshot pushes the control list past the kernel's command-line limit
    (`OSError: [Errno 7] Argument list too long`). Same call, same optimistic-lock retry."""
    from hap_cli.core.session import Session
    from hap_cli.core import worksheet as ws_mod
    before = signatures()
    ws_mod.save_controls(Session.load(None), WORKSHEET, ctrls)
    check_untouched(before)


# ── guard ───────────────────────────────────────────────────────────────────

def guard():
    """Stop unless the profile reaches ERP Master › Invoicing › Invoices and the worksheet holds only the skeleton
    plus this script's work. Returns the live controls."""
    who = hap.run('auth', 'whoami')
    app = hap.run('app', 'info', '-a', APP).get('data', {})
    section = next((s for s in app.get('sections', []) if any(i['id'] == WORKSHEET for i in s['items'])), None)
    if app.get('name') != 'ERP Master' or not section or section['name'] != 'Invoicing':
        sys.exit(f"profile {who.get('profile')!r} does not reach ERP Master › Invoicing › Invoices")
    problems, ctrls = [], hap.controls(WORKSHEET)
    by_id = {c['controlId']: c for c in ctrls}
    for cid, (name, kind) in FIRST_BUILD.items():
        c = by_id.get(cid)
        want = RENAME.get(cid, name)
        if not c or c['type'] != kind or c['controlName'] not in (name, want):
            problems.append(f"skeleton control {cid} ({name}) is {c and (c['controlName'], c['type'])}")
    problems += [f"unknown control {c['controlName']!r} ({c['controlId']})" for c in ctrls
                 if c['controlName'] not in PLACE and c['controlId'] not in FIRST_BUILD
                 and c['controlName'] not in INCOTERM_FIELDS + PAYMENT_FIELDS + O2I_FIELDS]
    for name, opts in OPTIONS.items():
        c = next((c for c in ctrls if c['controlName'] == name), None)
        if c:
            live = [(o['key'], o['value']) for o in c.get('options') or [] if not o.get('isDeleted')]
            if live != [(o['key'], o['value']) for o in opts]:
                problems.append(f'{name} options changed: {live}')
    rules = {r['name'] for r in hap.listing('worksheet', 'rules', WORKSHEET)}
    problems += [f'unknown rule {n!r}' for n in rules - set(RULES) - set(JOURNAL_CHECKS) - set(INCOTERM_RULES)
                 - set(PAYMENT_RULES)]
    buttons = {b['name'] for b in hap.listing('worksheet', 'custom-actions', WORKSHEET)}
    problems += [f'unknown button {n!r}' for n in buttons - set(BUTTONS) - {REGISTER_PAYMENT}]
    views = {v['name'] for v in hap.listing('worksheet', 'view', 'list', WORKSHEET, '-a', APP)}
    problems += [f'unknown view {n!r}' for n in views - set(VIEWS) - {'All'}]
    if problems:
        sys.exit("Invoices differs from the skeleton plus this script's work — stopping:\n  " + '\n  '.join(problems))
    print(f"  guard: profile {os.environ.get('HAP_PROFILE') or who.get('profile')!r}, ERP Master › Invoicing › "
          f"Invoices, {len(ctrls)} controls, {len(rules)} rules, {len(buttons)} buttons, views {sorted(views)}")
    return ctrls


def step_layout():
    """Rename three of Teh Li Wei's controls and his empty remark block, add the fifteen missing fields and the two
    missing remark blocks, then set every control's place and tab, alias, hint, help, required, read-only, default,
    decimals and the title field. The tabs already exist, so the fields can point at their ids in one save."""
    ctrls = guard()
    print('  backup:', hap.backup('invoices_controls_pre_layout', ctrls))
    item = next(i for s in C.app_info(APP)['sections'] for i in s['items'] if i['id'] == WORKSHEET)
    if item.get('alias') != ALIAS_WORKSHEET:        # the house convention: the Odoo model with underscores
        # `worksheet update --alias` answers "参数错误" without the app id, though common.ensure_worksheet
        # calls it without one on a freshly created worksheet.
        hap.run('worksheet', 'update', WORKSHEET, '--alias', ALIAS_WORKSHEET, '-a', APP)
        print(f"  worksheet alias {item.get('alias')!r} -> {ALIAS_WORKSHEET!r}")
    renamed = [c for c in ctrls if RENAME.get(c['controlId'], c['controlName']) != c['controlName']]
    if renamed:
        for c in renamed:
            c['controlName'] = RENAME[c['controlId']]
        save_controls(ctrls)
        ctrls = hap.controls(WORKSHEET)
        print('  renamed:', [c['controlName'] for c in renamed])
    have = {c['controlName'] for c in ctrls}
    missing = [n for n in NEW if n not in have]
    if missing:
        before = signatures()
        plain = [n for n in missing if n not in RELATIONS]
        if plain:
            C.add_fields(WORKSHEET, [new_control(n) for n in plain])
        relations = [n for n in missing if n in RELATIONS]
        if relations:                              # no client-side controlId: the server mints a one-way relation
            C.append_controls(WORKSHEET, [new_control(n) for n in relations])
        check_untouched(before)
        ctrls = hap.controls(WORKSHEET)
        print(f'  added: {missing}')
    changed = layout_differences(ctrls)
    if changed:
        tab_ids = {c['controlName']: c['controlId'] for c in ctrls if c['type'] == C.TAB}
        for c in ctrls:
            if c['controlName'] in changed:
                c.update(desired(c, tab_ids))
                c['advancedSetting'] = {**(c.get('advancedSetting') or {}), **ADVANCED.get(c['controlName'], {})}
        save_controls(ctrls)
        print('  updated:', json.dumps(changed, ensure_ascii=False))
    else:
        print('  layout already as specified; nothing saved')
    ctrls = hap.controls(WORKSHEET)
    left = layout_differences(ctrls)
    if left:
        sys.exit(f'layout read back with differences: {json.dumps(left, ensure_ascii=False)}')
    lost = [f'{cid} ({name})' for cid, (name, _) in FIRST_BUILD.items()
            if cid not in {c['controlId'] for c in ctrls}]
    if lost:
        sys.exit(f'skeleton control ids missing after the save: {lost}')
    for c in ctrls:
        C.remember('controls', KEY + c['controlName'], c['controlId'])
    C.show(WORKSHEET)


# ── 2 · rules ───────────────────────────────────────────────────────────────

RULE_DELIVERY = 'Delivery Address is for customer documents'
RULE_BILL_DATE = 'A vendor document must carry its date'
RULE_TAX_MODE = 'Every document but an entry has a tax mode'
RULE_AUTO_POST = 'Auto-post until follows Auto-post'
RULE_NO_AUTO_POST_ON_RECEIPT = 'Auto-post is not offered on a receipt'   # bundle 15, 21 Sep 2026
RULE_CLOSED = 'A posted or cancelled document is closed for editing'
RULE_DUE_OR_TERMS = 'Due Date or Payment Terms'                   # bundle 3, Payment Terms
RULE_NO_DUE_ON_ENTRY = 'No due date on a journal entry'           # bundle 3, Payment Terms

CLOSED_FIELDS = ['Type', 'Customer / Vendor', 'Journal', 'Invoice Date', 'Accounting Date', 'Due Date',
                 'Payment Terms', 'Tax mode', LINES,
                 'Delivery Address', 'Delivery Date', 'Auto-post', 'Auto-post until']
# LINES is 07's mounted 子表. It joined the list on 16 Sep 2026, at the end of Phase 1: the rule was written
# before Invoice Lines existed, so a posted document still offered *Add a row* where Odoo locks a posted
# move's lines (07's difference 11). A rule item acts on a control, and a 子表 is one.
# The last four joined on 21 Sep 2026 (15 §1.1): the tenant's arch carries `readonly="state != 'draft'"` on
# `partner_shipping_id`, `delivery_date`, `auto_post` and `auto_post_until` too, and the UI pass found Delivery
# Address still drawing its dropdown chevron on the posted INV/2026/00001 while every other header field was text.
# rule name -> (driving field, its option labels — or None for "the field is not empty" —, the controls it acts on, the
# rule item type). A rule applies its
# action while its condition holds and the opposite when it fails, so every `show` here also hides its field on a
# new record whose driver is still empty — which is what Odoo's `invisible` does.
RULES = {
    # <field name="partner_shipping_id" invisible="not is_sale_document(True)"/>
    RULE_DELIVERY: ('Type', CUSTOMER_TYPES, ['Delivery Address'], C.SHOW),
    # required="is_purchase_document(True)" on invoice_date (labelled Bill Date)
    RULE_BILL_DATE: ('Type', VENDOR_TYPES, ['Invoice Date'], C.REQUIRE),
    # SQL account_move_check_document_tax_mode_set: everything but a journal entry
    RULE_TAX_MODE: ('Type', INVOICE_TYPES, ['Tax mode'], C.REQUIRE),
    # The **tenant's** arch (saas~19.4): <field name="auto_post_until"
    #   invisible="auto_post in ('no', 'at_date')" readonly="state != 'draft'"/>
    # — so At Date hides it as No does: a document posted on one date needs no "until". The 19.0 repo checkout
    # at 7bbce824 still reads invisible="auto_post == 'no'", which is what the first cut of this rule followed
    # (15 §1.2; the same repo-behind-tenant trap as the Taxes form and the CRM feature groups).
    RULE_AUTO_POST: ('Auto-post', ['Monthly', 'Quarterly', 'Yearly'], ['Auto-post until'], C.SHOW),
    # <field name="auto_post" invisible="move_type in ('out_receipt', 'in_receipt')" .../>, the tenant again.
    # `hide · equals` rather than `show · equals`, so Auto-post is visible from the start on a new document
    # whose Type is still empty (BUILDING.md). Auto-post stays required on the control: it carries the default
    # **No**, so a receipt saves with the field hidden and filled, and Auto-post until stays hidden with it.
    RULE_NO_AUTO_POST_ON_RECEIPT: ('Type', ['Sales Receipt', 'Purchase Receipt'], ['Auto-post'], C.HIDE),
    # readonly="state != 'draft'" across the form. 'Payment Terms' is the relation since bundle 3 (the rule named the
    # text stand-in until it was deleted)
    RULE_CLOSED: ('Status', ['Posted', 'Cancelled'], CLOSED_FIELDS, C.READONLY),
    # <field name="invoice_date_due" invisible="invoice_payment_term_id"/>: with a term the date is computed (D)
    RULE_DUE_OR_TERMS: ('Payment Terms', None, ['Due Date'], C.HIDE),
    # <div name="due_date" invisible="move_type not in (…the six invoice and receipt types…)">: neither on an entry
    RULE_NO_DUE_ON_ENTRY: ('Type', ['Journal Entry'], ['Due Date', 'Payment Terms'], C.HIDE),
}


# ── the two journal checks ──────────────────────────────────────────────────
#
# Odoo narrows the Journal picker itself — `journal_id`'s domain is `[('id', 'in', suitable_journal_ids)]`, and
# `_get_suitable_journal_ids` keeps the journals whose Type is *sale* for the three customer types, *purchase*
# for the three vendor types and *general* for a journal entry — **and** refuses the save afterwards, in
# `@api.constrains('journal_id', 'move_type') _check_journal_move_type`:
#
#     if move.is_purchase_document(include_receipts=True) and move.journal_id.type != 'purchase':
#         raise ValidationError(_("Cannot create a purchase document in a non purchase journal"))
#     if move.is_sale_document(include_receipts=True) and move.journal_id.type != 'sale':
#         raise ValidationError(_("Cannot create a sale document in a non sale journal"))
#
# **The picker filter cannot be built.** A HAP Relation's picker filter compares a field of the *candidate*
# record with a literal or with a dynamic value read off the form (`dynamicSource`), and the value it would
# need here is the document's Type — an option **key** of this worksheet's own Type dropdown, which shares no
# key with Journals' Type dropdown, so the comparison could never match. Nothing in HAP maps one option set
# onto another, and a static filter is worse than none: it would have to name one journal type, and a journal
# entry legitimately uses Miscellaneous (15 §1.3, and `nocoly/worksheets/06-invoices.md` §2).
#
# So what is built is the **constraint**, with Odoo's two messages verbatim: two validation rules standing on
# the Journal Type lookup, refusing the save rather than preventing the choice. Odoo's own `_check_journal_move_type`
# says nothing about a journal entry, and neither do these — a journal entry may be written in any journal
# here, where Odoo's *picker* would have offered it only the Miscellaneous ones.
RULE_SALE_JOURNAL = 'A sale document must be in a sale journal'
RULE_PURCHASE_JOURNAL = 'A purchase document must be in a purchase journal'
MSG_SALE_JOURNAL = 'Cannot create a sale document in a non sale journal'
MSG_PURCHASE_JOURNAL = 'Cannot create a purchase document in a non purchase journal'
JOURNAL_CHECKS = {   # rule name -> (the document types it covers, the Journal Type it demands, Odoo's message)
    RULE_SALE_JOURNAL: (CUSTOMER_TYPES, 'Sales', MSG_SALE_JOURNAL),
    RULE_PURCHASE_JOURNAL: (VENDOR_TYPES, 'Purchase', MSG_PURCHASE_JOURNAL),
}


def journal_type_keys():
    """Journals' Type options by label. The lookup stores the **source dropdown's option key**, as Invoice
    Lines' Status lookup does, so that is what a condition on it compares."""
    return {o['value']: o['key'] for o in C.fields(JOURNALS)['Type']['options'] if not o.get('isDeleted')}


def journal_check_filters(f, labels, journal_type, keys):
    """Type is any of `labels` **and** Journal Type is filled **and** Journal Type is not `journal_type`.

    The "is filled" clause is what keeps the message off a document whose Journal has not been picked yet:
    an empty lookup is "not Sales" as far as the comparison goes. The lookup's `dataType` is **11**, the
    single select it mirrors, not 30 — the filter editor reads a type-30 lookup as its source control's
    type (pd-openweb `redefineComplexControl`), as Chart of Accounts' picker does for a text formula."""
    lookup = f[JOURNAL_TYPE]
    clause = lambda op, values: {'controlId': lookup['controlId'], 'dataType': DROPDOWN, 'spliceType': 1,
                                 'filterType': op, 'value': '', 'values': values, 'dynamicSource': [],
                                 'isGroup': False}
    return C.any_of([is_any_of(f, 'Type', labels), clause(C.NOT_EMPTY, []), clause(C.NE, [keys[journal_type]])])


def is_any_of(f, field, labels):
    """Condition: `field` is any of the labels (one filter, several option keys)."""
    keys = [o['key'] for o in f[field]['options'] if o['value'] in labels]
    if len(keys) != len(labels):
        sys.exit(f'{field} options {labels} not all found')
    return {'controlId': f[field]['controlId'], 'dataType': f[field]['type'], 'spliceType': 1,
            'filterType': C.EQ, 'value': '', 'values': keys, 'dynamicSource': [], 'isGroup': False}


def step_rules():
    ctrls = guard()
    f = hap.by_name(c for c in hap.controls(WORKSHEET) if c['type'] != C.TAB)       # the Lines subtable included
    when = lambda driver, labels: (C.cond(f[driver], C.NOT_EMPTY) if labels is None
                                   else is_any_of(f, driver, labels))
    rules = [(name, C.INTERACTION, C.any_of([when(driver, labels)]),
              [C.item(kind, *[f[t] for t in targets])], {})
             for name, (driver, labels, targets, kind) in RULES.items()]
    if JOURNAL_TYPE in f:
        keys = journal_type_keys()
        # Checked in the form and on API writes (check type 1), and shown as the Journal is picked rather than
        # only on submit (hint type 0) — the shape Chart of Accounts' _check_reconcile carries.
        rules += [(name, C.VALIDATION, journal_check_filters(f, labels, journal_type, keys),
                   [C.item(C.ERROR, f['Journal'], message=message)], {'check_type': 1, 'hint_type': 0})
                  for name, (labels, journal_type, message) in JOURNAL_CHECKS.items()]
    C.upsert_rules(WORKSHEET, rules, 'invoices_rules_pre_rules')
    for r in hap.listing('worksheet', 'rules', WORKSHEET):
        C.remember('rules', KEY + r['name'], r['ruleId'])


# ── 2b · Incoterm (22 Sep 2026) ─────────────────────────────────────────────
#
# `account.move.invoice_incoterm_id` (Many2one account.incoterms, labelled *Incoterm*) and `incoterm_location` (Char),
# the second and third fields of Odoo's *Accounting* group on the Other Info page, after the company. Odoo hides both
# on a receipt — `invisible="move_type in ('out_receipt', 'in_receipt')"` (account_move_views.xml:1541-1542, 19.0
# source) — which RULE_INCOTERM_RECEIPT builds, in the form RULE_NO_AUTO_POST_ON_RECEIPT already takes.
#
# **Neither is closed on a posted document.** Odoo's view gives neither a `readonly`, and `account.move.write`'s list of
# fields a posted move refuses (`unmodifiable_fields`: lines, dates, partner, payment terms, currency, fiscal position,
# cash rounding) does not name them — so RULE_CLOSED leaves them editable, as Odoo does.
#
# Appended with `C.append_controls` — the Incoterm Relation is one-way, so Incoterms is untouched — with the Other
# Info tab's `sectionId`, so both land at the foot of that tab at row 9999: **placement is the owner's**. Not in PLACE,
# so `layout` neither places nor judges them; `guard` and `check` know them from here.
INCOTERM, INCOTERM_LOCATION = 'Incoterm', 'Incoterm Location'
INCOTERM_FIELDS = (INCOTERM, INCOTERM_LOCATION)
INCOTERMS = hap.ids()['worksheets']['Incoterms']
INCOTERM_ALIAS = {INCOTERM: 'invoice_incoterm_id', INCOTERM_LOCATION: 'incoterm_location'}   # Odoo's names
# Intent, for the owner: the first row under the *Accounting* divider (row 18), Incoterm | Incoterm Location — Odoo's
# group reads company, incoterm, incoterm location — with Source Document · Auto-post and the row under them moving
# down one.
INCOTERM_PLACE = {INCOTERM: (19, 0, 6, OTHER_INFO), INCOTERM_LOCATION: (19, 1, 6, OTHER_INFO)}
INCOTERM_DESC = {INCOTERM: 'International Commercial Terms are a series of predefined commercial terms used in '
                           'international transactions.',          # Odoo's help on the field
                 INCOTERM_LOCATION: ''}                            # Odoo's field has no help
RULE_INCOTERM_RECEIPT = 'Incoterm is not offered on a receipt'
INCOTERM_RULES = {RULE_INCOTERM_RECEIPT: ('Type', ['Sales Receipt', 'Purchase Receipt'], list(INCOTERM_FIELDS),
                                          C.HIDE)}


def incoterms_active():
    active = C.fields(INCOTERMS).get('Active')
    if not active or active['type'] != 36:
        sys.exit('Incoterms has no Active checkbox — run incoterms.py first')
    return active['controlId']


def other_info_tab():
    """Teh Li Wei's Other Info tab, whose id the skeleton check already pins."""
    return next(cid for cid, (name, kind) in FIRST_BUILD.items() if name == OTHER_INFO and kind == C.TAB)


def incoterm_controls():
    tab = other_info_tab()
    return {
        INCOTERM: C.control('RELATE_SHEET', INCOTERM, INCOTERM_PLACE[INCOTERM][:3], alias=INCOTERM_ALIAS[INCOTERM],
                            hint='', desc=INCOTERM_DESC[INCOTERM], data_source=INCOTERMS, multi=False,
                            advanced_setting={'bidirectional': '0', 'showtype': '3',
                                              'filters': C.active_picker(incoterms_active())},
                            extra={'fieldPermission': '111', 'sectionId': tab}),
        INCOTERM_LOCATION: C.control('TEXT', INCOTERM_LOCATION, INCOTERM_PLACE[INCOTERM_LOCATION][:3],
                                     alias=INCOTERM_ALIAS[INCOTERM_LOCATION], hint='',
                                     desc=INCOTERM_DESC[INCOTERM_LOCATION],
                                     extra={'fieldPermission': '111', 'sectionId': tab}),
    }


def incoterm_spec():
    """What the two must read back as, the picker filter aside. Row and column are placement — the owner's."""
    tab = other_info_tab()
    return {
        INCOTERM: {'type': RELATION, 'alias': INCOTERM_ALIAS[INCOTERM], 'desc': INCOTERM_DESC[INCOTERM], 'hint': '',
                   'required': False, 'fieldPermission': '111', 'dataSource': INCOTERMS, 'enumDefault': 1,
                   'sectionId': tab, 'advancedSetting.bidirectional': '0', 'advancedSetting.showtype': '3'},
        INCOTERM_LOCATION: {'type': 2, 'alias': INCOTERM_ALIAS[INCOTERM_LOCATION], 'hint': '',
                            'desc': INCOTERM_DESC[INCOTERM_LOCATION], 'required': False, 'fieldPermission': '111',
                            'sectionId': tab, 'enumDefault': 2},
    }


def interaction_rule_state(r, names):
    """An interaction rule as (type, disabled, item types, [(driver, filterType)], option labels, targets) — what
    `check` compares for every rule in RULES and INCOTERM_RULES."""
    conds = [g for group in r['filters'] for g in group.get('groupFilters', [])]
    driver = names.get(conds[0]['controlId']) if conds else None
    return (r['type'], r['disabled'], {i['type'] for i in r['ruleItems']},
            [(names.get(c['controlId']), c['filterType']) for c in conds],
            sorted(LABEL.get(driver, {}).get(v) for c in conds for v in c.get('values', [])),
            [names.get(c['controlId']) for i in r['ruleItems'] for c in i['controls']])


def interaction_rule_want(driver, labels, targets, kind):
    return (C.INTERACTION, False, {kind}, [(driver, C.NOT_EMPTY if labels is None else C.EQ)], sorted(labels or []),
            list(targets))


def incoterm_problems(f):
    problems = []
    counts = {}
    for c in hap.controls(WORKSHEET):
        counts[c['controlName']] = counts.get(c['controlName'], 0) + 1
    spec = incoterm_spec()
    for n in INCOTERM_FIELDS:
        if counts.get(n, 0) != 1:
            problems.append(f'Invoices carries {counts.get(n, 0)} controls named {n!r}, wanted exactly one')
        c = f.get(n)
        if c is None:
            continue
        diff = C.drift(c, spec[n])
        if diff:
            problems.append(f'{n}: {json.dumps(diff, ensure_ascii=False, default=str)} — run `incoterm`')
        if hap.ids().get('controls', {}).get(KEY + n) != c['controlId']:
            problems.append(f'{n}: ids.json does not hold {c["controlId"]} — run `incoterm`')
    c = f.get(INCOTERM)
    if c:
        got = C.picker_state((c.get('advancedSetting') or {}).get('filters'))
        want = C.picker_state(C.active_picker(incoterms_active()))
        if got != want:
            problems.append(f'{INCOTERM} picker filter {got}, wanted {want} (Active is ticked) — run `incoterm`')
    inc = hap.controls(INCOTERMS)
    if [x['controlName'] for x in inc if x.get('attribute') == 1] != ['Display Name']:
        problems.append("Incoterms' title is not Display Name — the picker would not show \"[FOB] FREE ON BOARD\"")
    back = [x['controlName'] for x in inc if x.get('dataSource') == WORKSHEET]
    if back:
        problems.append(f'Incoterms carries {back} pointing back at Invoices — {INCOTERM} must be one-way')
    return problems


def step_incoterm():
    """Append Incoterm and Incoterm Location if they are missing, repair anything the append did not store in one
    version-pinned save limited to them, and write the receipt rule if it differs. Re-running saves nothing."""
    guard()
    f = hap.by_name(c for c in hap.controls(WORKSHEET) if c['type'] != C.TAB)
    missing = [n for n in INCOTERM_FIELDS if n not in f]
    if missing:
        built = incoterm_controls()
        f = C.append_checked(WORKSHEET, [built[n] for n in missing], 'invoices_controls_pre_incoterm', 'incoterm',
                             untouched=(INCOTERMS,))
    else:
        print(f'  {list(INCOTERM_FIELDS)} are already on Invoices; nothing appended')
    spec = {}
    for n, want in incoterm_spec().items():
        stale = C.drift(f[n], want)
        if stale:
            spec[f[n]['controlId']] = {k: want[k] for k in stale}
    picker = C.active_picker(incoterms_active())
    if C.picker_state((f[INCOTERM].get('advancedSetting') or {}).get('filters')) != C.picker_state(picker):
        spec.setdefault(f[INCOTERM]['controlId'], {})['advancedSetting.filters'] = picker
    if spec:
        C.pinned_write(WORKSHEET, spec, 'invoices_controls_pre_incoterm_repair', 'incoterm')
        f = hap.by_name(c for c in hap.controls(WORKSHEET) if c['type'] != C.TAB)
    else:
        print(f'  {list(INCOTERM_FIELDS)} already as specified; nothing saved')
    for n in INCOTERM_FIELDS:
        C.remember('controls', KEY + n, f[n]['controlId'])
    # the receipt rule — written only when the live one differs
    names = {c['controlId']: c['controlName'] for c in hap.controls(WORKSHEET)}
    live = {r['name']: r for r in hap.listing('worksheet', 'rules', WORKSHEET)}
    specs = []
    for name, (driver, labels, targets, kind) in INCOTERM_RULES.items():
        r = live.get(name)
        if r is None or interaction_rule_state(r, names) != interaction_rule_want(driver, labels, targets, kind):
            specs.append((name, C.INTERACTION, C.any_of([is_any_of(f, driver, labels)]),
                          [C.item(kind, *[f[t] for t in targets])], {}))
    if specs:
        C.upsert_rules(WORKSHEET, specs, 'invoices_rules_pre_incoterm')
        live = {r['name']: r for r in hap.listing('worksheet', 'rules', WORKSHEET)}
    else:
        print(f'  {list(INCOTERM_RULES)} already as specified; nothing saved')
    for name, (driver, labels, targets, kind) in INCOTERM_RULES.items():
        r = live.get(name)
        if r is None or interaction_rule_state(r, names) != interaction_rule_want(driver, labels, targets, kind):
            sys.exit(f'rule {name!r} read back as {r and interaction_rule_state(r, names)}')
        C.remember('rules', KEY + name, r['ruleId'])
        print(f"  OK  rule {name!r} {r['ruleId']}: hide {targets} while Type is any of {labels}")
    problems = incoterm_problems(f)
    if problems:
        sys.exit('\n'.join(problems))
    for n in INCOTERM_FIELDS:
        c = f[n]
        print(f"  OK  {n:<18} {c['controlId']} t{c['type']} alias={c.get('alias')} perm={c.get('fieldPermission')} "
              f"r{c.get('row')}c{c.get('col')}s{c.get('size')} tab={OTHER_INFO if c.get('sectionId') == other_info_tab() else c.get('sectionId')!r}")
    parked = [n for n in INCOTERM_FIELDS if f[n].get('row') == 9999]
    if parked:
        print('  placement outstanding — the owner places these in the designer; intended (row, col, size, tab): '
              + ', '.join(f'{n} {INCOTERM_PLACE[n]}' for n in parked)
              + ' — the first row under the Accounting divider')


INCOTERM_TEST = 'TEST-SEQ-1'                      # a TEST customer invoice `selfcheck` keeps (ids.json records)


def incoterm_cell(value):
    if isinstance(value, str):
        try:
            value = json.loads(value) if value.startswith('[') else []
        except ValueError:
            return value
    return [(v.get('sid') or v.get('rowid'), v.get('name')) for v in value or [] if isinstance(v, dict)]


def read_incoterm(rowid, f):
    got = hap.run('worksheet', 'record', 'get', WORKSHEET, rowid, '-a', APP)['data']
    listed = next((r for r in C.records(WORKSHEET, APP) if r['rowid'] == rowid), {})
    return {'get': (incoterm_cell(got.get(INCOTERM_ALIAS[INCOTERM])), got.get(INCOTERM_ALIAS[INCOTERM_LOCATION])),
            'list': (incoterm_cell(listed.get(f[INCOTERM]['controlId'])),
                     listed.get(f[INCOTERM_LOCATION]['controlId']))}


def step_selfincoterm():
    """On a TEST invoice: set Incoterm to CIF and Incoterm Location to a TEST place through `record update`, read both
    back through `record get` **and** the listing, then put both back as they were and read that back too."""
    guard()
    f = hap.by_name(c for c in hap.controls(WORKSHEET) if c['type'] != C.TAB)
    problems = incoterm_problems(f)
    if problems:
        sys.exit('\n'.join(problems))
    rowid = hap.ids()['records'][KEY + INCOTERM_TEST]
    code = C.fields(INCOTERMS)['Code']['controlId']
    cif = next((r['rowid'] for r in C.records(INCOTERMS, APP) if r.get(code) == 'CIF'), None)
    if not cif:
        sys.exit('no Incoterm CIF — run incoterms.py seed')
    before = read_incoterm(rowid, f)
    print(f'  {INCOTERM_TEST} ({rowid}) before: {before}')
    was_rows, was_text = [r for r, _ in before['get'][0]], before['get'][1] or ''
    write = lambda rows, text: hap.run('worksheet', 'record', 'update', WORKSHEET, rowid, '-a', APP, '--fields-json',
                                       json.dumps([{'id': f[INCOTERM]['controlId'], 'value': rows},
                                                   {'id': f[INCOTERM_LOCATION]['controlId'], 'value': text}]))
    write([cif], 'TEST Port of Singapore')
    time.sleep(3)
    during = read_incoterm(rowid, f)
    print(f'  set:   {during}')
    want = ([(cif, '[CIF] COST, INSURANCE AND FREIGHT')], 'TEST Port of Singapore')
    for path in ('get', 'list'):
        if during[path] != want:
            problems.append(f'{path}: {during[path]}, wanted {want}')
    write(was_rows, was_text)
    time.sleep(3)
    after = read_incoterm(rowid, f)
    print(f'  back:  {after}')
    if after != before:
        problems.append(f'not put back: {after}, was {before}')
    print('  selfincoterm: ' + ('OK — Incoterm and Incoterm Location stored and read back through both paths, and put '
                                'back' if not problems else 'DIFFERENCES\n    ' + '\n    '.join(problems)))
    return len(problems)


# ── 3 · views ───────────────────────────────────────────────────────────────

DOC_COLUMNS = ('Number', 'Customer / Vendor', 'Invoice Date', 'Due Date', 'Journal', 'Untaxed Amount', 'Total',
               'Amount Due', 'Status')
ENTRY_COLUMNS = ('Number', 'Accounting Date', 'Journal', 'Total', 'Status')
VIEWS = ('Invoices', 'Bills', 'Journal Entries')


EQ_SINGLE = 51           # a view's / button's "is" on a single-select: the filter translator's eq for dataType 11


def type_filter(f, labels):
    """--view-spec filter group: Type is any of the labels. A dropdown's `eq` becomes filterType 51."""
    keys = [OPTION_KEY['Type'][label] for label in labels]
    return {'type': 'group', 'logic': 'AND', 'children': [
        {'type': 'condition', 'field': f['Type']['controlId'], 'dataType': DROPDOWN, 'operator': 'eq',
         'value': keys}]}


def step_views():
    """Odoo's Invoices / Credit Notes, Bills / Refunds and Entries actions, each a table filtered on move_type,
    with the list's visible columns and Odoo's `_order` (date desc, name desc)."""
    guard()
    f = C.fields(WORKSHEET)
    docs = [f[n]['controlId'] for n in DOC_COLUMNS]
    entries = [f[n]['controlId'] for n in ENTRY_COLUMNS]
    sort = C.sort_by([(f['Accounting Date'], False), (f['Number'], False)])
    quick = [{'fieldId': f['Type']['controlId'], 'selectionType': 'multiple', 'displayType': 'dropdown'},
             {'fieldId': f['Status']['controlId'], 'selectionType': 'multiple', 'displayType': 'dropdown'}]
    views = {
        'Invoices': (dict(viewType='table', filter=type_filter(f, CUSTOMER_TYPES), tableFields=docs,
                          quickFilters=quick), sort, docs),
        'Bills': (dict(viewType='table', filter=type_filter(f, VENDOR_TYPES), tableFields=docs,
                       quickFilters=quick), sort, docs),
        'Journal Entries': (dict(viewType='table', filter=type_filter(f, ['Journal Entry']), tableFields=entries,
                                 quickFilters=quick), sort, entries),
    }
    for name, vid in C.upsert_views(WORKSHEET, APP, views, 'invoices_views_pre_views',
                                    default_view='Invoices').items():
        C.remember('views', KEY + name, vid)
    print('  order:', C.sort_views(WORKSHEET, APP, list(views)))
    C.print_views(WORKSHEET, APP)


# ── 4 · buttons ─────────────────────────────────────────────────────────────

MSG_CANCEL = 'Are you sure you want to cancel this document?'
BUTTONS = ('Confirm', 'Cancel', 'Reset to Draft')
POST_STEP = 'Post the document'
CANCEL_STEP = 'Cancel the document'
RESET_STEP = 'Reset the document to draft'


def status_when(f, labels, op):
    """A button condition: Status is (eq) / is not (ne) any of the labels."""
    return {'type': 'group', 'logic': 'AND', 'children': [
        {'type': 'condition', 'field': f['Status']['controlId'], 'dataType': DROPDOWN, 'operator': op,
         'value': [OPTION_KEY['Status'][x] for x in labels]}]}


def step_buttons():
    """Odoo's three header buttons. Confirm's workflow is extended by `numbering` into the sequence.mixin
    algorithm; Cancel and Reset to Draft are one update step each, and Reset keeps the Number."""
    guard()
    f = C.fields(WORKSHEET)
    status = f['Status']['controlId']
    # A workflow update step stores a dropdown as the bare option key in `fieldValue`. A list is refused with a
    # 500 from flowNode/saveNode, and a JSON array string is accepted and stored empty.
    to_status = lambda label: {'fieldId': status, 'type': DROPDOWN, 'value': OPTION_KEY['Status'][label]}
    buttons = [
        ({'name': 'Confirm', 'type': 'triggerWorkflow', 'enableWhen': status_when(f, ['Draft'], 'eq'),
          'isBatch': True}, [to_status('Posted')], POST_STEP),
        ({'name': 'Cancel', 'type': 'triggerWorkflow', 'enableWhen': status_when(f, ['Draft'], 'eq'),
          'isBatch': True, 'confirm': True, 'confirmMsg': MSG_CANCEL, 'sureName': 'Cancel document',
          'cancelName': 'Back'}, [to_status('Cancelled')], CANCEL_STEP),
        ({'name': 'Reset to Draft', 'type': 'triggerWorkflow',
          'enableWhen': status_when(f, ['Posted', 'Cancelled'], 'eq'), 'isBatch': True},
         [to_status('Draft')], RESET_STEP),
    ]
    C.upsert_buttons(WORKSHEET, APP, buttons, KEY, 'invoices_buttons_pre_buttons')
    for name, step, label in (('Cancel', CANCEL_STEP, 'Cancelled'), ('Reset to Draft', RESET_STEP, 'Draft')):
        pid = hap.ids()['workflows'][KEY + name]
        proc, byname = nodes_by_name(pid)
        trig = proc['startEventId']
        if set_fields(pid, byname[step], [patch(status, DROPDOWN, value=OPTION_KEY['Status'][label])], trig):
            print(f'  {name}:', C.publish(pid))
    step_numbering()
    for name in BUTTONS:
        print(C.structure(hap.ids()['workflows'][KEY + name]))


# ── 4b · the numbering Confirm has to reproduce ─────────────────────────────

GET_JOURNAL = 'Get the journal'
PREFIX_STEP = "The number's prefix and year"
COUNT_STEP = 'How many documents already carry it'
HIGHEST_STEP = 'The highest number already used'
NUMBER_STEP = 'The next number'
DATE_BRANCH = 'An invoice or receipt with no date?'
DATE_BRANCH_WAS = 'Is the Invoice Date empty?'     # the first cut, before Odoo's is_invoice() condition was added
DATE_STEP = "Fill in today's Invoice Date"
REFERENCE_BRANCH = 'A customer document without a Payment Reference?'
REFERENCE_STEP = 'Copy the Number to the Payment Reference'
NUMBERING_STEPS = (GET_JOURNAL, PREFIX_STEP, COUNT_STEP, HIGHEST_STEP, NUMBER_STEP, DATE_BRANCH, REFERENCE_BRANCH)
STRING_FX, NUMBER_FX = 'string_fx_id', 'number_fx_id'      # a formula node's own result field


def journal_of(node_id, trigger, journal_field):
    """Condition for GET_JOURNAL: the journal's record ID equals the trigger document's Journal."""
    return {'nodeId': node_id, 'nodeType': 7, 'actionId': '406', 'filedId': 'rowid', 'filedValue': 'Record ID',
            'filedTypeId': 2, 'enumDefault': 0, 'conditionId': '9', 'sourceType': 0, 'conditionValues': [
                {'nodeId': trigger, 'controlId': journal_field, 'value': '', 'sureNodeId': trigger}]}


def starts_with_prefix(node_id, number_field, prefix_node, kind=('7', '406')):
    """Condition: the searched document's Number starts with the prefix node's result ("INV/2026/").
    conditionId 5 is 开头是; the comparison value is another node's field, as {nodeId, controlId}."""
    return {'nodeId': node_id, 'nodeType': int(kind[0]), 'actionId': kind[1], 'filedId': number_field['controlId'],
            'filedValue': number_field['controlName'], 'filedTypeId': 2, 'enumDefault': 2, 'conditionId': '5',
            'sourceType': 0, 'conditionValues': [{'nodeId': prefix_node, 'controlId': STRING_FX, 'value': ''}]}


def prefix_formula(f, j):
    """sequence.mixin's prefix and year: "INV/2026/", or "RINV/2026/" for a credit note on a journal with a
    Dedicated Credit Note Sequence.

    A workflow function formula compares with **==**; a single `=` makes the whole expression compute empty
    without any error (Found while building). A dropdown compares against its label, a checkbox against 1."""
    credit = ' || '.join(f'$trigger-{f["Type"]["controlId"]}$ == "{label}"' for label in CREDIT_NOTES)
    return (f'CONCAT(IF(({credit}) && $journal-{j["Dedicated Credit Note Sequence"]["controlId"]}$ == 1, "R", ""), '
            f'$journal-{j["Sequence Prefix"]["controlId"]}$, "/", '
            f'YEAR($trigger-{f["Accounting Date"]["controlId"]}$), "/")')


def number_formula(f):
    """One past the **highest** number already issued under this prefix and year, padded to five digits — and the
    document's own Number when it already has one.

    Odoo `_post` sequences a move only when its `name` is unset, and `button_draft` keeps the name, so a document
    that is reset and confirmed again takes its old number back. The first cut counted instead of reading the
    highest, which handed a freed number to the next document; the search step above sorts on Number descending,
    and because the suffix is zero-padded to a fixed width a text sort is numeric order within one prefix and
    year. `count` is the empty case: nothing carries this prefix yet, so it is 0 and the first number is 00001."""
    number = f['Number']['controlId']
    held = f'$trigger-{number}$'
    highest = f'$highest-{number}$'
    # SUM(), not `+`: in a workflow formula `+` **concatenates** when either side is text ("5" + 1 is "51"), and
    # the result is then read back as an octal literal if it still has a leading zero ("00005" + 1 came out 41).
    # SUM() forces a numeric context; so would * 1 or INT(). There is no VALUE() and no LEN().
    # The test is on RIGHT(...), not on the field: the search can return a record whose Number is **null**
    # rather than "" — the document being confirmed itself, which the search cannot exclude — and `null == ""`
    # is false, so the else branch ran on a null and computed empty. RIGHT(null, 5) is "", which this catches
    # (23 Sep 2026: two confirmations with identical inputs, one numbered and one not).
    suffix = f'RIGHT({highest}, 5)'
    n = f'IF({suffix} == "", SUM($count-{NUMBER_FX}$, 1), SUM({suffix}, 1))'
    fresh = f'CONCAT($prefix-{STRING_FX}$, RIGHT(CONCAT("0000", {n}), 5))'
    # `CONCAT({held}, "")` rather than `{held}`: a document that has never been numbered holds **null**, not "",
    # and `null == ""` is false — so the else branch returned the null and the document posted with no number at
    # all. CONCAT normalises it (23 Sep 2026; the same null explains the else branch below).
    seen = f'CONCAT({held}, "")'
    return f'IF({seen} == "" || {seen} == "{DRAFT}", {fresh}, {held})'


def set_formula(pid, node, expression):
    """A formula node's expression, read back (a wrong expression is stored and computes empty)."""
    got = hap.run('workflow', 'node', 'get', pid, node['id'])
    got = got.get('data', got)
    if got.get('formulaValue') == expression:
        return False
    hap.run('workflow', 'node', 'save', pid, node['id'], '--type', '9', '-c', json.dumps(
        {'actionId': '106', 'name': node['name'], 'execute': True, 'formulaValue': expression, 'type': 2},
        ensure_ascii=False), '-n', node['name'])
    back = hap.run('workflow', 'node', 'get', pid, node['id'])
    back = back.get('data', back)
    if back.get('formulaValue') != expression:
        sys.exit(f"{node['name']}: expression read back {back.get('formulaValue')!r}")
    return True


def highest_node():
    """The one document with the greatest Number under this prefix and year, or nothing at all. Its filter and
    its Number-descending sort are written afterwards by `save_search`: `batch-add` sends `operateCondition`,
    which the UI never reads, and no sort at all."""
    return {'nodeAlias': 'highest', 'nodeType': 'get_single', 'name': HIGHEST_STEP,
            'config': {'worksheet': WORKSHEET, 'execute_type': 2}}      # 2 = carry on when nothing is found


def numbering_nodes(f, j):
    """The chain Confirm runs before it posts: the journal, the prefix, the count, the highest, the number."""
    return [
        {'nodeAlias': 'journal', 'nodeType': 'get_single', 'name': GET_JOURNAL,
         'config': {'worksheet': JOURNALS, 'execute_type': 2}},          # 2 = carry on when nothing is found
        {'nodeAlias': 'prefix', 'nodeType': 'compute', 'name': PREFIX_STEP,
         'config': {'mode': 'function', 'output_type': 'text', 'formula': prefix_formula(f, j)}},
        {'nodeAlias': 'count', 'nodeType': 'rollup', 'name': COUNT_STEP,
         'config': {'mode': 'worksheet', 'worksheet': WORKSHEET, 'aggregate': 'count', 'filter': {
             'logic': 'and', 'items': [{'left': {'node': {'nodeAlias': 'trigger'},
                                                 'fieldId': f['Number']['controlId'], '_filedTypeId': 2},
                                        'op': 'starts_with',
                                        'right': {'kind': 'field', 'node': {'nodeAlias': 'prefix'},
                                                  'fieldId': STRING_FX}}]}}},
        highest_node(),
        {'nodeAlias': 'number', 'nodeType': 'compute', 'name': NUMBER_STEP,
         'config': {'mode': 'function', 'output_type': 'text', 'formula': number_formula(f)}},
    ]


EMPTY, IS_ANY_OF = '8', '1'                        # workflow condition ids: 为空, 是其中一个
SYSTEM_NODE = '5d39140d381d42d20db0c4da'           # the fixed 系统 node: current time, trigger time, trigger user


def cond(node_id, field, condition_id, values=None):
    """One workflow condition on `field` of the record `node_id` produced."""
    return {'nodeId': node_id, 'filedId': field['controlId'], 'filedValue': field['controlName'],
            'filedTypeId': field['type'], 'conditionId': condition_id, 'sourceType': 0,
            'conditionValues': values or []}


def option_values(name, labels):
    return [{'value': {'key': OPTION_KEY[name][label], 'value': label, 'isDeleted': False}} for label in labels]


def fill_nodes():
    """The two branches Odoo's _post needs, built empty: batch-add makes the gateway, its two paths and the update
    step inside the first path, and `step_numbering` then writes the path conditions and the field to write. A
    field patch or a path condition sent through batch-add here is stored empty (Found while building)."""
    return [
        {'nodeAlias': 'date_branch', 'nodeType': 'branch', 'name': DATE_BRANCH, 'config': {'paths': [
            {'alias': 'no_date', 'name': 'Yes', 'nodes': [
                {'nodeAlias': 'set_date', 'nodeType': 'update_record', 'name': DATE_STEP,
                 'config': {'target': {'node': {'nodeAlias': 'posted'}}, 'worksheet': WORKSHEET, 'fields': []}}]},
            {'alias': 'has_date', 'name': 'No'}]}},
        {'nodeAlias': 'reference_branch', 'nodeType': 'branch', 'name': REFERENCE_BRANCH, 'config': {'paths': [
            {'alias': 'no_reference', 'name': 'Yes', 'nodes': [
                {'nodeAlias': 'set_reference', 'nodeType': 'update_record', 'name': REFERENCE_STEP,
                 'config': {'target': {'node': {'nodeAlias': 'posted'}}, 'worksheet': WORKSHEET, 'fields': []}}]},
            {'alias': 'has_reference', 'name': 'No'}]}},
    ]


def branch_paths(proc, gateway_id):
    """A gateway's two paths: the one that carries a step, then the fall-through."""
    paths = [n for n in proc['flowNodeMap'].values()
             if n.get('typeId') == 2 and n.get('prveId') == gateway_id]
    yes = next(p for p in paths if p.get('nextId') not in (None, '', '99'))
    no = next(p for p in paths if p['id'] != yes['id'])
    return yes, no


def save_path(pid, path, name, conditions):
    """A branch path's name and condition. `node get` returns them as `conditions`; `node save --type 2` wants
    `operateCondition`, and batch-add drops the path's name."""
    got = hap.run('workflow', 'node', 'get', pid, path['id'])
    got = got.get('data', got)
    live = [[{k: c.get(k) for k in ('nodeId', 'filedId', 'conditionId')} for c in group]
            for group in got.get('conditions') or []]
    want = [[{k: c.get(k) for k in ('nodeId', 'filedId', 'conditionId')} for c in group] for group in conditions]
    changed = live != want
    if changed:
        hap.run('workflow', 'node', 'save', pid, path['id'], '--type', '2',
                '-c', json.dumps({'operateCondition': conditions}, ensure_ascii=False), '-n', name)
    if path.get('name') != name:                   # batch-add drops a branch path's name, and `node save` with
        hap.run('workflow', 'node', 'rename', pid, path['id'], '-n', name)     # -n does not set it either
        changed = True
    return changed


def nodes_by_name(pid):
    proc = hap.run('workflow', 'node', 'list', pid)
    return proc, {n['name']: n for n in proc['flowNodeMap'].values()}


def save_search(pid, node, worksheet, conditions, kind=('7', '406'), execute_type=2, sorts=None):
    """Save a search node's filter and sort the way the UI stores them: `filters`, not `operateCondition` (which
    `node batch-add --nodes` sends and the UI never reads). Returns True when the node was changed."""
    sorts = sorts or [{'controlId': 'ctime', 'controlType': 16, 'isAsc': True}]
    got = hap.run('workflow', 'node', 'get', pid, node['id'])
    got = got.get('data', got)
    live = [[{k: c.get(k) for k in ('filedId', 'conditionId')} for c in group]
            for flt in got.get('filters') or [] for group in flt.get('conditions') or []]
    live_sorts = [{k: x.get(k) for k in ('controlId', 'isAsc')} for x in got.get('sorts') or []]
    if (got.get('appId') == worksheet
            and live == [[{k: c.get(k) for k in ('filedId', 'conditionId')} for c in conditions]]
            and live_sorts == [{k: x.get(k) for k in ('controlId', 'isAsc')} for x in sorts]):
        return False
    config = {'actionId': kind[1], 'appId': worksheet, 'selectNodeId': '',
              'filters': [{'spliceType': 2, 'conditions': [conditions]}],
              'sorts': sorts, 'executeType': execute_type}
    hap.run('workflow', 'node', 'save', pid, node['id'], '--type', kind[0],
            '-c', json.dumps(config, ensure_ascii=False), '-n', node['name'])
    return True


def step_numbering():
    """Extend Confirm's workflow with sequence.mixin: read the journal, build "<prefix>/<year>/", count the
    documents that already carry it, write "<prefix>/<year>/<n+1 padded to 5>" into Number, and fill in the
    Invoice Date and the Payment Reference Odoo fills on posting."""
    pid = hap.ids()['workflows'][KEY + 'Confirm']
    f, j = C.fields(WORKSHEET), C.fields(JOURNALS)
    proc, byname = nodes_by_name(pid)
    if GET_JOURNAL not in byname:
        # The numbering chain goes in front of the update that posts the document, so Number and Status are
        # written in one save; the two fill-in branches follow it.
        hap.run('workflow', 'node', 'batch-add', pid, '--nodes',
                json.dumps(numbering_nodes(f, j), ensure_ascii=False),
                '--trigger-node-id', proc['startEventId'], '--trigger-alias', 'trigger')
        proc, byname = nodes_by_name(pid)
    added_branches = DATE_BRANCH not in byname and DATE_BRANCH_WAS not in byname
    if added_branches:
        hap.run('workflow', 'node', 'batch-add', pid, '--nodes', json.dumps(fill_nodes(), ensure_ascii=False),
                '--trigger-node-id', byname[POST_STEP]['id'], '--trigger-alias', 'posted')
        proc, byname = nodes_by_name(pid)
    if DATE_BRANCH not in byname:                  # the first cut's name, before the is_invoice() condition
        hap.run('workflow', 'node', 'rename', pid, byname[DATE_BRANCH_WAS]['id'], '-n', DATE_BRANCH)
        proc, byname = nodes_by_name(pid)
        added_branches = True
    if HIGHEST_STEP not in byname:                 # added after the first build, between the count and the number
        hap.run('workflow', 'node', 'batch-add', pid, '--nodes', json.dumps([highest_node()], ensure_ascii=False),
                '--trigger-node-id', byname[COUNT_STEP]['id'], '--trigger-alias', 'counted')
        proc, byname = nodes_by_name(pid)
        added_branches = True
    trigger, changed = proc['startEventId'], added_branches or GET_JOURNAL not in byname
    changed |= save_search(pid, byname[GET_JOURNAL], JOURNALS,
                           [journal_of(byname[GET_JOURNAL]['id'], trigger, f['Journal']['controlId'])])
    # The greatest Number under this prefix and year: one record, sorted on Number descending. The suffix is
    # zero-padded to a fixed width, so within one prefix and year a text sort is numeric order.
    changed |= save_search(pid, byname[HIGHEST_STEP], WORKSHEET,
                           [starts_with_prefix(byname[HIGHEST_STEP]['id'], f['Number'],
                                               byname[PREFIX_STEP]['id'])],
                           sorts=[{'controlId': f['Number']['controlId'], 'controlType': 2, 'isAsc': False}])
    ids = {'trigger': trigger, 'journal': byname[GET_JOURNAL]['id'], 'prefix': byname[PREFIX_STEP]['id'],
           'count': byname[COUNT_STEP]['id'], 'highest': byname[HIGHEST_STEP]['id']}
    alias = lambda text: text.replace('$trigger-', f"${ids['trigger']}-").replace('$journal-', f"${ids['journal']}-") \
                             .replace('$prefix-', f"${ids['prefix']}-").replace('$count-', f"${ids['count']}-") \
                             .replace('$highest-', f"${ids['highest']}-")
    changed |= set_formula(pid, byname[PREFIX_STEP], alias(prefix_formula(f, j)))
    changed |= set_formula(pid, byname[NUMBER_STEP], alias(number_formula(f)))
    changed |= set_number(pid, f, byname, trigger)
    # An invoice or receipt with no Invoice Date gets today (Odoo _post, is_invoice(include_receipts=True) — a
    # plain journal entry is left alone); a customer document's empty Payment Reference gets the new number.
    yes, no = branch_paths(proc, byname[DATE_BRANCH]['id'])
    changed |= save_path(pid, yes, 'Yes', [[cond(trigger, f['Type'], IS_ANY_OF, option_values('Type',
                                                                                              INVOICE_TYPES)),
                                            cond(trigger, f['Invoice Date'], EMPTY)]])
    changed |= save_path(pid, no, 'No', [])
    changed |= set_fields(pid, byname[DATE_STEP],
                          [patch(f['Invoice Date']['controlId'], 15, source='nowTime', system=True)], trigger)
    yes, no = branch_paths(proc, byname[REFERENCE_BRANCH]['id'])
    changed |= save_path(pid, yes, 'Yes',
                         [[cond(trigger, f['Type'], IS_ANY_OF, option_values('Type', CUSTOMER_TYPES)),
                           cond(trigger, f['Payment Reference'], EMPTY)]])
    changed |= save_path(pid, no, 'No', [])
    changed |= set_fields(pid, byname[REFERENCE_STEP],
                          [patch(f['Payment Reference']['controlId'], 2, node=byname[NUMBER_STEP]['id'],
                                 source=STRING_FX)], trigger)
    # Odoo's _post fills an empty invoice date and the due date recomputes from it: once the Payment Terms bundle has
    # given Invoices its relation, Confirm ends with the same dating chain as automations C and D (payterms.py) — the
    # fresh document, its terms' lines, the code block, the Due Date. Its write of the Invoice Date would also start
    # automation D, dating the invoice a second time, so Confirm's writes start no other workflow (payterms.ensure_quiet:
    # 触发其他工作流 set to 不允许触发 — none of Confirm's other writes has a workflow to start).
    relation = next((c for c in hap.controls(WORKSHEET) if c['type'] == RELATION
                     and c.get('dataSource') == hap.ids()['worksheets'].get('Payment Terms')), None)
    if relation:
        import payterms
        changed |= payterms.ensure_dating(pid, byname[REFERENCE_BRANCH]['id'])
        changed |= payterms.ensure_quiet(pid, KEY + 'Confirm')
    print('  Confirm:', C.publish(pid) if changed else 'already built; not re-published')


def patch(field_id, kind, value='', node='', source='', system=False):
    """One field write for an update step, in the shape the server actually stores (Found while building):

    a dropdown as its bare option key in `fieldValue`; a **text** taken from another node as the template
    `$<nodeId>-<fieldId>$`, again in `fieldValue`; every other type from a node as `nodeId` + `fieldValueId`,
    and from the fixed 系统 node with `nodeTypeId` / `appType` 100."""
    wire = {'fieldId': field_id, 'type': kind, 'addType': 0, 'fieldValue': value, 'fieldValueId': '', 'nodeId': ''}
    if system:
        wire.update(nodeId=SYSTEM_NODE, sureNodeId=SYSTEM_NODE, fieldValueId=source, nodeTypeId=100,
                    nodeAppType=100)
    elif node and kind == 2:
        wire['fieldValue'] = f'${node}-{source}$'
    elif node:
        wire.update(nodeId=node, sureNodeId=node, fieldValueId=source, nodeAppType=1)
    return wire


def set_fields(pid, node, wanted, select_node):
    """Give an update step exactly these field writes, keeping the rest of its configuration; returns True when
    the step was changed. `select_node` is the node whose record is updated: an update step pointed at another
    update step comes back `isException: true` and stores no field at all (Found while building)."""
    d = hap.run('workflow', 'node', 'get', pid, node['id'])
    d = d.get('data', d)
    fields = list(d.get('fields') or [])
    changed = d.get('selectNodeId') != select_node
    for want in wanted:
        entry = next((x for x in fields if x.get('fieldId') == want['fieldId']), None)
        if entry and all(entry.get(k) == v for k, v in want.items()):
            continue
        if entry:
            entry.update(want)
        else:
            fields.append(want)
        changed = True
    if not changed:
        return False
    hap.run('workflow', 'node', 'save', pid, node['id'], '--type', '6', '-c', json.dumps(
        {'actionId': d.get('actionId', '2'), 'appId': d.get('appId') or WORKSHEET, 'appType': 1,
         'selectNodeId': select_node, 'fields': fields}, ensure_ascii=False), '-n', node['name'])
    return True


def set_number(pid, f, byname, trigger):
    """The step that posts the document writes both Status (Posted) and the Number the formula built."""
    return set_fields(pid, byname[POST_STEP], [
        patch(f['Status']['controlId'], DROPDOWN, value=OPTION_KEY['Status']['Posted']),
        patch(f['Number']['controlId'], 2, node=byname[NUMBER_STEP]['id'], source=STRING_FX)], trigger)


# ── 4c · Register Payment (23 Sep 2026) ─────────────────────────────────────
#
# The owner's small version of Odoo's payment step. Odoo's *Pay* button (`action_register_payment`,
# account_move_views.xml:734, 19.0 source) opens the `account.payment.register` wizard — an **amount** defaulting to
# what is left to pay and a **payment date** defaulting to today — which books an `account.payment`, posts its journal
# entry and reconciles it with the invoice; `payment_state` and `amount_residual` then follow from the reconciliation
# (`_compute_payment_state`, `_compute_amount`). **There is no Payments worksheet and no bank entry here** (the Payments
# bundle is a later phase), so the document itself carries the running result:
#
#   * **Payment Status** (`payment_state`) — three of Odoo's seven values: Not Paid · Partially Paid · Paid;
#   * **Amount Paid** — the running total received (Odoo computes `amount_paid` as total − residual);
#   * **Last Payment Date** — the latest payment's date (Odoo shows it in the payments widget);
#   * **Amount Due** (`amount_residual`) becomes a **Formula**, Total − Amount Paid, converted in place (6 → 31, the
#     control id kept) — so the roll-up can go on rewriting Total and the figure due still follows;
#   * **Payment Amount** and **Payment Date** — the wizard's two fields, hidden on the form and filled only through the
#     button's fill-in form (填写指定字段), which defaults them to the Amount Due and today.
#
# **Register Payment** is offered on a posted customer invoice, vendor bill or credit note that is not Paid. Its
# workflow adds the amount to Amount Paid, stamps Last Payment Date, sets Payment Status (Paid when nothing is left,
# Partially Paid when part of the Total is left, else Not Paid) and clears the two inputs. **An overpayment is
# refused** — Odoo would book it and leave the surplus as an outstanding credit; with no payment records there is
# nowhere to keep one. Two validation rules say so in the form and on API writes, and the workflow refuses it again.
# **Reset to Draft and Cancel are not offered on a paid or partly paid document**: with no payment record to
# unreconcile, resetting would leave Amount Paid attached to a draft. (Odoo 19.0 itself *does* allow resetting a paid
# invoice — `button_draft` keeps the reconciliation and `_compute_payment_state` covers drafts — so this is a
# divergence, recorded in 06 and DECISIONS.md.)

REGISTER_PAYMENT = 'Register Payment'
PAYMENT_STATUS, AMOUNT_PAID, LAST_PAYMENT_DATE = 'Payment Status', 'Amount Paid', 'Last Payment Date'
PAYMENT_AMOUNT, PAYMENT_DATE = 'Payment Amount', 'Payment Date'
PAYMENT_FIELDS = (PAYMENT_STATUS, AMOUNT_PAID, LAST_PAYMENT_DATE, PAYMENT_AMOUNT, PAYMENT_DATE)
O2I_FIELDS = ('Sales Orders', 'Sales Order Count')     # o2i.py's, on this worksheet since 23 Sep 2026
NUMBER, DATE, FORMULA = 6, 15, 31
NE_SINGLE = 52                                     # a button's / view's "is not" on a single select
GT, LE = 13, 16                                    # rule filter types: > and <=
FILL_REQUIRED = 3                                  # a fill-in field the button's form requires
PAYABLE_TYPES = ('Customer Invoice', 'Customer Credit Note', 'Vendor Bill', 'Vendor Credit Note')
UNPAID_ONLY = ('Cancel', 'Reset to Draft')         # the buttons refused on a paid or partly paid document
UNPAID_CONDITION = (PAYMENT_STATUS, NE_SINGLE, ('Paid', 'Partially Paid'))
ALL_LABELS = {o['key']: o['value'] for opts in OPTIONS.values() for o in opts}

PAYMENT_TYPE = {PAYMENT_STATUS: DROPDOWN, AMOUNT_PAID: NUMBER, LAST_PAYMENT_DATE: DATE,
                PAYMENT_AMOUNT: NUMBER, PAYMENT_DATE: DATE}
PAYMENT_KIND = {DROPDOWN: 'DROP_DOWN', NUMBER: 'NUMBER', DATE: 'DATE'}
PAYMENT_ALIAS = {PAYMENT_STATUS: 'payment_state',            # Odoo's field
                 AMOUNT_PAID: 'amount_paid',                 # Odoo's name for total − residual (_get_invoice_...)
                 LAST_PAYMENT_DATE: 'last_payment_date',     # no Odoo field; the name says what it holds
                 PAYMENT_AMOUNT: 'amount',                   # account.payment.register.amount
                 PAYMENT_DATE: 'payment_date'}               # account.payment.register.payment_date
PAYMENT_DESC = {  # for the app's users only (owner's rule, 22 Sep 2026)
    PAYMENT_STATUS: 'Whether this document has been paid: Not Paid, Partially Paid or Paid. Register Payment keeps '
                    'it up to date.',
    AMOUNT_PAID: 'The total of the payments registered on this document.',
    LAST_PAYMENT_DATE: 'The date of the latest payment registered on this document.',
    PAYMENT_AMOUNT: 'The amount of this payment. It cannot be more than the Amount Due.',
    PAYMENT_DATE: 'The date the payment was received or made.',
}
PAYMENT_PERM = {PAYMENT_STATUS: '101', AMOUNT_PAID: '101', LAST_PAYMENT_DATE: '101',
                PAYMENT_AMOUNT: '011', PAYMENT_DATE: '011'}           # the two inputs are hidden on the form
PAYMENT_DEFAULT = {PAYMENT_STATUS: C.static_default(OPTION_KEY['Payment Status']['Not Paid']),
                   AMOUNT_PAID: C.static_default(0)}
# Intent, for the owner — `append_controls` parks every new control at row 9999 of the Invoice Lines tab, and
# **placement is the owner's**: Amount Paid · Last Payment Date on the row under Total · Amount Due, Payment Status
# under them (Odoo shows it as a ribbon), and the two hidden inputs anywhere — they never show on the form. Other
# Info and everything under it would move down three rows.
PAYMENT_PLACE = {AMOUNT_PAID: (12, 0, 6, INVOICE_LINES), LAST_PAYMENT_DATE: (12, 1, 6, INVOICE_LINES),
                 PAYMENT_STATUS: (13, 0, 6, INVOICE_LINES),
                 PAYMENT_AMOUNT: (14, 0, 6, INVOICE_LINES), PAYMENT_DATE: (14, 1, 6, INVOICE_LINES)}
FORMULA_SETTING = {'roundtype': '2', 'sorttype': 'zh', 'nullzero': '1'}     # every number Formula in this app
NUMBER_ONLY = ('showtype', 'thousandth', 'min', 'max', 'numshow', 'defsource', 'defaulttype', 'defaultfunc')

RULE_NOT_MORE_THAN_DUE = 'A payment cannot be more than the amount due'
RULE_MORE_THAN_ZERO = 'A payment must be more than zero'
MSG_NOT_MORE_THAN_DUE = 'The payment cannot be more than the Amount Due.'
MSG_MORE_THAN_ZERO = 'Enter a payment amount greater than zero.'
PAYMENT_RULES = {RULE_NOT_MORE_THAN_DUE: MSG_NOT_MORE_THAN_DUE, RULE_MORE_THAN_ZERO: MSG_MORE_THAN_ZERO}
PAYMENT_BUTTON_DESC = 'Record a payment received or made on this document.'

PAY_PAID_STEP = 'The Amount Paid after this payment'
PAY_DUE_STEP = 'The Amount Due after this payment'
PAY_BRANCH = 'Can the payment be registered, and what is left to pay?'
PATH_REFUSED = 'No amount, no date, or more than the Amount Due'
PATH_PAID = 'Nothing is left to pay'
PATH_PARTIAL = 'Part of the Total is left to pay'
PATH_UNPAID = 'Otherwise'
SET_REFUSED = 'Clear the payment fields'
SET_PAID = 'Register the payment: Paid'
SET_PARTIAL = 'Register the payment: Partially Paid'
SET_UNPAID = 'Register the payment: Not Paid'
PAY_PATHS = ((PATH_REFUSED, SET_REFUSED, None), (PATH_PAID, SET_PAID, 'Paid'),
             (PATH_PARTIAL, SET_PARTIAL, 'Partially Paid'), (PATH_UNPAID, SET_UNPAID, 'Not Paid'))
PAY_STEPS = (PAY_PAID_STEP, PAY_DUE_STEP, PAY_BRANCH) + tuple(s for _, s, _ in PAY_PATHS)
FORMULA_NUMBER_NODE, NUMBER_FX_ID = '100', 'number_fx_id'
LE_C, LT_C, GT_C, EMPTY_C = '13', '11', '12', '8'  # workflow conditionIds: ≤ · < · > · 为空

# What the button editor sends back on a save besides the name and texts (pd-openweb CreateCustomBtn.jsx) —
# orders.BTN_SAVE_KEYS, BUILDING.md › Buttons.
BTN_SAVE_KEYS = ('isAllView', 'color', 'icon', 'writeControls', 'relationControl', 'writeType', 'writeObject',
                 'clickType', 'showType', 'advancedSetting', 'enableConfirm', 'verifyPwd', 'workflowType', 'isBatch')
BTN_VOLATILE = ('updateTime', 'updateAccountId')


def invoice_lines_tab():
    """Teh Li Wei's Invoice Lines tab, whose id the skeleton check already pins."""
    return next(cid for cid, (name, kind) in FIRST_BUILD.items() if name == INVOICE_LINES and kind == C.TAB)


def payment_controls():
    """The five controls to append, in the Invoice Lines tab (the append keeps `sectionId`; the row is 9999)."""
    tab = invoice_lines_tab()
    out = {}
    for n in PAYMENT_FIELDS:
        extra = {'fieldPermission': PAYMENT_PERM[n], 'sectionId': tab}
        if PAYMENT_TYPE[n] == NUMBER:
            extra['dot'] = 2
        out[n] = C.control(PAYMENT_KIND[PAYMENT_TYPE[n]], n, PAYMENT_PLACE[n][:3], alias=PAYMENT_ALIAS[n], hint='',
                           desc=PAYMENT_DESC[n], options=PAYMENT_STATUS_OPTIONS if n == PAYMENT_STATUS else None,
                           advanced_setting={'defsource': PAYMENT_DEFAULT[n]} if n in PAYMENT_DEFAULT else None,
                           extra=extra)
    return out


def payment_spec():
    """What the five must read back as. Row, column and tab are placement — the owner's — and are not judged."""
    out = {}
    for n in PAYMENT_FIELDS:
        s = {'type': PAYMENT_TYPE[n], 'alias': PAYMENT_ALIAS[n], 'desc': PAYMENT_DESC[n], 'hint': '',
             'required': False, 'fieldPermission': PAYMENT_PERM[n]}
        if PAYMENT_TYPE[n] == NUMBER:
            s['dot'] = 2
        if n in PAYMENT_DEFAULT:
            s['advancedSetting.defsource'] = PAYMENT_DEFAULT[n]
        out[n] = s
    return out


def amount_due_spec(f):
    """Amount Due as a Formula: Total − Amount Paid, two decimals, a blank Amount Paid counted as 0 (BUILDING.md:
    a number Formula computes nothing on a blank operand unless `nullzero` is "1")."""
    spec = {'type': FORMULA, 'alias': 'amount_residual', 'fieldPermission': '101', 'dot': 2, 'enumDefault': 0,
            'enumDefault2': 0, 'unit': '', 'desc': DESC['Amount Due'], 'hint': '',
            'dataSource': f"${f['Total']['controlId']}$-${f[AMOUNT_PAID]['controlId']}$"}
    spec.update({f'advancedSetting.{k}': v for k, v in FORMULA_SETTING.items()})
    return spec


def amount_due_leftovers(c):
    return {k: v for k, v in (c.get('advancedSetting') or {}).items() if k in NUMBER_ONLY and v not in (None, '')}


def ensure_amount_due():
    """Convert Amount Due **in place** from a Number (6) to a Formula (31), keeping its control id — the move Order
    Lines' Tax Amount, Total and Quantity Invoiced made (16 §7.3, 21 §14.3). One save pinned to the version it read,
    proved by signature diff to have changed Amount Due and nothing else. The values it held were the roll-up's copy
    of Total; they are backed up first."""
    ctrls, version = C.controls_with_version(WORKSHEET)
    f = hap.by_name(c for c in ctrls if c['type'] != C.TAB)
    c = f['Amount Due']
    want = amount_due_spec(f)
    stale, leftover = C.drift(c, want), amount_due_leftovers(c)
    if not stale and not leftover:
        print(f"  Amount Due is already the Formula {want['dataSource']}; nothing saved")
        return False
    surplus = {k: v for k, v in (c.get('advancedSetting') or {}).items()
               if k not in FORMULA_SETTING and k not in NUMBER_ONLY and v}
    if surplus:
        sys.exit(f'Amount Due carries advancedSetting {surplus} that a Formula does not and this step was not told '
                 'to drop — stopping rather than discarding them')
    values = {r['rowid']: r.get(c['controlId']) for r in C.records(WORKSHEET, APP)}
    print('  backup of the values Amount Due held:', hap.backup('invoices_amount_due_values_pre_formula', values))
    hap.backup('invoices_controls_pre_amount_due_formula', ctrls)
    before = C.control_signature(ctrls)
    c['advancedSetting'] = dict(FORMULA_SETTING)                 # the Number's own keys go with the type
    for key, value in want.items():
        if not key.startswith('advancedSetting.'):
            c[key] = value
    C.save_controls(WORKSHEET, ctrls, version=version)
    live = hap.controls(WORKSHEET)
    changed = C.changed_ids(before, C.control_signature(live))
    names = {x['controlId']: x['controlName'] for x in live}
    if changed != [c['controlId']]:
        sys.exit(f'payments: the conversion changed {[names.get(k, k) for k in changed]}, wanted only Amount Due')
    now = hap.by_name(x for x in live if x['type'] != C.TAB)['Amount Due']
    left = C.drift(now, want)
    if left or amount_due_leftovers(now):
        sys.exit(f'Amount Due read back with differences {json.dumps(left, ensure_ascii=False, default=str)} '
                 f'{amount_due_leftovers(now)}')
    print(f"  Amount Due: type 6 -> 31, {now['dataSource']} — {len(before)} controls compared, no other change")
    return True


def payment_rule_filters(f, name):
    """Payment Amount is filled **and** is more than the Amount Due (another field: `dynamicSource`), or is filled
    and not more than zero. "Is filled" keeps both off every save that does not register a payment."""
    pa = f[PAYMENT_AMOUNT]
    filled = C.cond(pa, C.NOT_EMPTY)
    if name == RULE_NOT_MORE_THAN_DUE:
        compare = {'controlId': pa['controlId'], 'dataType': NUMBER, 'spliceType': 1, 'filterType': GT, 'value': '',
                   'values': [], 'isGroup': False, 'dynamicSource': [
                       {'rcid': '', 'cid': f['Amount Due']['controlId'], 'staticValue': '', 'isAsync': False}]}
    else:
        compare = {'controlId': pa['controlId'], 'dataType': NUMBER, 'spliceType': 1, 'filterType': LE, 'value': '0',
                   'values': ['0'], 'dynamicSource': [], 'isGroup': False}
    return C.any_of([filled, compare])


def payment_rule_state(r, names):
    conds = [g for group in r['filters'] for g in group.get('groupFilters', [])]
    return (r['type'], r['disabled'], r.get('checkType'), r.get('hintType'),
            sorted((names.get(c['controlId']), c['filterType'], tuple(str(v) for v in c.get('values') or []),
                    tuple(names.get(d.get('cid'), d.get('cid')) for d in c.get('dynamicSource') or []))
                   for c in conds),
            [(i['type'], [names.get(x['controlId']) for x in i['controls']], i.get('message', ''))
             for i in r['ruleItems']])


def payment_rule_want(name):
    compare = ((PAYMENT_AMOUNT, GT, (), ('Amount Due',)) if name == RULE_NOT_MORE_THAN_DUE
               else (PAYMENT_AMOUNT, LE, ('0',), ()))
    return (C.VALIDATION, False, 1, 0, sorted([(PAYMENT_AMOUNT, C.NOT_EMPTY, (), ()), compare]),
            [(C.ERROR, [PAYMENT_AMOUNT], PAYMENT_RULES[name])])


def ensure_payment_rules(f):
    names = {c['controlId']: c['controlName'] for c in hap.controls(WORKSHEET)}
    live = {r['name']: r for r in hap.listing('worksheet', 'rules', WORKSHEET)}
    specs = [(name, C.VALIDATION, payment_rule_filters(f, name),
              [C.item(C.ERROR, f[PAYMENT_AMOUNT], message=message)], {'check_type': 1, 'hint_type': 0})
             for name, message in PAYMENT_RULES.items()
             if name not in live or payment_rule_state(live[name], names) != payment_rule_want(name)]
    if specs:
        C.upsert_rules(WORKSHEET, specs, 'invoices_rules_pre_payments')
        live = {r['name']: r for r in hap.listing('worksheet', 'rules', WORKSHEET)}
    else:
        print(f'  {list(PAYMENT_RULES)} already as specified; nothing saved')
    for name in PAYMENT_RULES:
        r = live.get(name)
        if r is None or payment_rule_state(r, names) != payment_rule_want(name):
            sys.exit(f'rule {name!r} read back as {r and payment_rule_state(r, names)}')
        C.remember('rules', KEY + name, r['ruleId'])
    return bool(specs)


# ── the buttons ──

def payment_enable_when(f):
    """Posted **and** a customer invoice, credit note or vendor bill **and** not Paid (Odoo's Pay button:
    `state != 'posted' or payment_state not in (…) or move_type not in (…)`)."""
    return {'type': 'group', 'logic': 'AND', 'children': [
        {'type': 'condition', 'field': f['Status']['controlId'], 'dataType': DROPDOWN, 'operator': 'eq',
         'value': [OPTION_KEY['Status']['Posted']]},
        {'type': 'condition', 'field': f['Type']['controlId'], 'dataType': DROPDOWN, 'operator': 'eq',
         'value': [OPTION_KEY['Type'][x] for x in PAYABLE_TYPES]},
        {'type': 'condition', 'field': f[PAYMENT_STATUS]['controlId'], 'dataType': DROPDOWN, 'operator': 'ne',
         'value': [OPTION_KEY['Payment Status']['Paid']]}]}


def payment_button_conditions():
    return sorted([('Status', EQ_SINGLE, ('Posted',)), ('Type', EQ_SINGLE, tuple(sorted(PAYABLE_TYPES))),
                   (PAYMENT_STATUS, NE_SINGLE, ('Paid',))])


def button_conditions(b, names):
    return sorted((names.get(x['controlId'], x['controlId']), x['filterType'],
                   tuple(sorted(ALL_LABELS.get(y, y) for y in x.get('values') or [])))
                  for x in b.get('filters') or [])


def payment_write_controls(f):
    """The fill-in form: Payment Amount defaulting to the record's Amount Due, Payment Date to today — the shape the
    Sales app's own Register Payment stores (`defsource` with a `cid`); both required."""
    return [{'controlId': f[PAYMENT_AMOUNT]['controlId'], 'type': FILL_REQUIRED,
             'defsource': json.dumps([{'rcid': '', 'cid': f['Amount Due']['controlId'], 'staticValue': ''}])},
            {'controlId': f[PAYMENT_DATE]['controlId'], 'type': FILL_REQUIRED, 'defsource': TODAY}]


def write_controls_state(items):
    return [(x.get('controlId'), x.get('type'), C.defsource_state(x.get('defsource') or ''))
            for x in items or []]


def payment_button_state(b, names):
    return dict(clickType=b.get('clickType'), writeType=b.get('writeType'), writeObject=b.get('writeObject'),
                workflowType=b.get('workflowType'), isBatch=bool(b.get('isBatch')), desc=b.get('desc') or '',
                filters=button_conditions(b, names), writeControls=write_controls_state(b.get('writeControls')))


def payment_button_want(f):
    return dict(clickType=3, writeType=1, writeObject=1, workflowType=1, isBatch=False, desc=PAYMENT_BUTTON_DESC,
                filters=payment_button_conditions(), writeControls=write_controls_state(payment_write_controls(f)))


def save_button_in_place(b, overrides, step):
    """`SaveWorksheetBtn` with the button's `btnId` and everything the button editor sends, as read, with only
    `overrides` changed — orders.ensure_send_batch. Every other key is compared before and after."""
    from hap_cli.core.session import Session
    params = {'btnId': b['btnId'], 'name': b['name'], 'worksheetId': WORKSHEET, 'filters': b.get('filters') or [],
              'confirmMsg': b.get('confirmMsg') or '', 'sureName': b.get('sureName') or '',
              'cancelName': b.get('cancelName') or '', 'workflowId': b.get('workflowId') or '',
              'desc': b.get('desc') or '', 'appId': APP, 'addRelationControlId': b.get('addRelationControl') or '',
              **{k: b.get(k) for k in BTN_SAVE_KEYS}}
    params.update(overrides)
    got = Session.load(None).api_call('Worksheet', 'SaveWorksheetBtn', params)
    after = next((x for x in hap.listing('worksheet', 'custom-actions', WORKSHEET) if x['btnId'] == b['btnId']), None)
    if after is None:
        sys.exit(f"{step}: {b['name']} is gone after SaveWorksheetBtn answered {got!r}")
    moved = sorted(k for k in set(b) | set(after)
                   if k not in BTN_VOLATILE and k not in overrides and b.get(k) != after.get(k))
    if moved:
        sys.exit(f"{step}: {b['name']}: {moved} changed with {sorted(overrides)} — the button as it was is in "
                 f'backups/invoices_buttons_pre_payments_*.json')
    return after


def payment_process_id(b):
    pid = hap.ids().get('workflows', {}).get(KEY + REGISTER_PAYMENT)
    if pid:
        return pid
    from hap_cli.core import worksheet as ws_mod
    from hap_cli.core.session import Session
    data = ws_mod.get_process_by_trigger_id(Session.load(None), WORKSHEET, b['btnId'])
    data = data.get('data', data) if isinstance(data, dict) else data
    pid = data[0]['id'] if isinstance(data, list) and data else None
    if not pid:
        sys.exit(f'{REGISTER_PAYMENT}: no workflow found for button {b["btnId"]}')
    C.remember('workflows', KEY + REGISTER_PAYMENT, pid)
    return pid


def ensure_payment_button(f):
    """The button, created once by name (create-custom-action ignores --btn-id and would add a duplicate), then
    brought to spec in place: the fill-in form and its defaults, the condition, no batch. Returns (button, changed)."""
    from hap_cli.core import filter_translator as flt
    names = {c['controlId']: c['controlName'] for c in hap.controls(WORKSHEET)}
    live = hap.listing('worksheet', 'custom-actions', WORKSHEET)
    b = next((x for x in live if x['name'] == REGISTER_PAYMENT), None)
    changed = False
    if b is None:
        hap.backup('invoices_buttons_pre_payments', live)
        spec = {'name': REGISTER_PAYMENT, 'type': 'updateCurrentRecord', 'runWorkflowAfterSubmit': True,
                'updateFields': [f[PAYMENT_AMOUNT]['controlId'], f[PAYMENT_DATE]['controlId']],
                'enableWhen': payment_enable_when(f), 'isBatch': False, 'desc': PAYMENT_BUTTON_DESC}
        out = hap.run('worksheet', 'create-custom-action', WORKSHEET, '-a', APP, '--action-spec',
                      json.dumps(spec, ensure_ascii=False))
        data = out.get('data', out) if isinstance(out, dict) else {}
        if data.get('processId'):
            C.remember('workflows', KEY + REGISTER_PAYMENT, data['processId'])
        b = next((x for x in hap.listing('worksheet', 'custom-actions', WORKSHEET) if x['name'] == REGISTER_PAYMENT),
                 None)
        if b is None:
            sys.exit(f'{REGISTER_PAYMENT} was not created: {out}')
        print(f"  {REGISTER_PAYMENT}: created {b['btnId']}")
        changed = True
    C.remember('buttons', KEY + REGISTER_PAYMENT, b['btnId'])
    want = payment_button_want(f)
    got = payment_button_state(b, names)
    if got != want:
        hap.backup('invoices_buttons_pre_payments', hap.listing('worksheet', 'custom-actions', WORKSHEET))
        overrides = {k: v for k, v in dict(
            clickType=3, writeType=1, writeObject=1, workflowType=1, isBatch=False, desc=PAYMENT_BUTTON_DESC,
            filters=flt.translate_filter_group(payment_enable_when(f)),
            writeControls=payment_write_controls(f)).items()}
        b = save_button_in_place(b, overrides, 'payments')
        got = payment_button_state(b, names)
        if got != want:
            sys.exit(f'{REGISTER_PAYMENT} read back {json.dumps(got, ensure_ascii=False, default=str)}\n'
                     f'  wanted {json.dumps(want, ensure_ascii=False, default=str)}')
        print(f'  {REGISTER_PAYMENT}: fill-in form, defaults, condition and batch written')
        changed = True
    else:
        print(f'  {REGISTER_PAYMENT}: already as specified')
    return b, changed


def ensure_unpaid_guards(f):
    """Cancel and Reset to Draft gain **Payment Status is not Paid or Partially Paid**, AND-ed with the Status
    condition they already carry — one in-place save each, nothing else about either button changed."""
    from hap_cli.core import filter_translator as flt
    names = {c['controlId']: c['controlName'] for c in hap.controls(WORKSHEET)}
    extra = {'type': 'condition', 'field': f[PAYMENT_STATUS]['controlId'], 'dataType': DROPDOWN, 'operator': 'ne',
             'value': [OPTION_KEY['Payment Status'][x] for x in ('Partially Paid', 'Paid')]}
    status_labels = {'Cancel': ['Draft'], 'Reset to Draft': ['Posted', 'Cancelled']}
    for name in UNPAID_ONLY:
        b = next(x for x in hap.listing('worksheet', 'custom-actions', WORKSHEET) if x['name'] == name)
        want = sorted([('Status', EQ_SINGLE, tuple(sorted(status_labels[name]))), UNPAID_CONDITION])
        if button_conditions(b, names) == want:
            print(f'  {name}: already refused on a paid or partly paid document')
            continue
        hap.backup('invoices_buttons_pre_payments', hap.listing('worksheet', 'custom-actions', WORKSHEET))
        group = status_when(f, status_labels[name], 'eq')
        group['children'].append(extra)
        b = save_button_in_place(b, {'filters': flt.translate_filter_group(group)}, 'payments')
        if button_conditions(b, names) != want:
            sys.exit(f'{name}: filters read back {button_conditions(b, names)}, wanted {want}')
        print(f'  {name}: now offered only while Payment Status is neither Paid nor Partially Paid')


# ── the workflow ──

def payment_nodes():
    """Two number formulas and a four-way exclusive branch (唯一分支), each path one update of the document. Path
    conditions and field writes are written afterwards: `batch-add` stores both empty (Found while building)."""
    upd = lambda alias, name: {'nodeAlias': alias, 'nodeType': 'update_record', 'name': name,
                               'config': {'target': {'node': {'nodeAlias': 'trigger'}}, 'worksheet': WORKSHEET,
                                          'fields': []}}
    return [
        {'nodeAlias': 'paid', 'nodeType': 'compute', 'name': PAY_PAID_STEP, 'config': {'mode': 'number',
                                                                                      'formula': '0+0'}},
        {'nodeAlias': 'due', 'nodeType': 'compute', 'name': PAY_DUE_STEP, 'config': {'mode': 'number',
                                                                                    'formula': '0+0'}},
        {'nodeAlias': 'which', 'nodeType': 'branch', 'name': PAY_BRANCH, 'config': {'paths': [
            {'alias': f'p{i}', 'name': path, 'nodes': [upd(f'u{i}', step)]}
            for i, (path, step, _) in enumerate(PAY_PATHS, 1)]}},
    ]


def read_node(pid, node_id):
    d = hap.run('workflow', 'node', 'get', pid, node_id)
    return d.get('data', d) if isinstance(d, dict) else {}


def sync_number_formula(pid, node, expression):
    """A number formula step (actionId 100): expression, two decimals, a blank input counted as 0 — both of which
    default the wrong way (invlines.set_formula)."""
    want = {'formulaValue': expression, 'number': 2, 'nullZero': True}
    if all(read_node(pid, node['id']).get(k) == v for k, v in want.items()):
        return False
    hap.run('workflow', 'node', 'save', pid, node['id'], '--type', '9', '-n', node['name'], '-c', json.dumps(
        {'actionId': FORMULA_NUMBER_NODE, 'name': node['name'], 'execute': True, 'formulaValue': expression,
         'number': 2, 'nullZero': True, 'type': NUMBER}, ensure_ascii=False))
    back = read_node(pid, node['id'])
    if any(back.get(k) != v for k, v in want.items()):
        sys.exit(f"{node['name']}: read back {[(k, back.get(k)) for k in want]}")
    return True


def value_state(v):
    if isinstance(v.get('value'), dict):
        return ('key', v['value'].get('key'))
    if v.get('controlId'):
        return ('field', v.get('nodeId') or '', v.get('controlId'))
    return ('value', str(v.get('value') or ''))


def path_conditions_state(groups):
    return [[(c.get('nodeId') or '', c.get('filedId'), str(c.get('conditionId')),
              tuple(value_state(v) for v in c.get('conditionValues') or [])) for c in g] for g in groups or []]


def save_payment_path(pid, path, name, conditions):
    """A branch path's name and condition, compared down to the values and the fields compared with."""
    got = read_node(pid, path['id'])
    want = path_conditions_state(conditions)
    changed = path_conditions_state(got.get('conditions')) != want
    if changed:
        hap.run('workflow', 'node', 'save', pid, path['id'], '--type', '2', '-n', name,
                '-c', json.dumps({'operateCondition': conditions}, ensure_ascii=False))
        back = path_conditions_state(read_node(pid, path['id']).get('conditions'))
        if back != want:
            sys.exit(f'{name}: the path condition read back {back}, wanted {want}')
    if got.get('name') != name:
        hap.run('workflow', 'node', 'rename', pid, path['id'], '-n', name)
        changed = True
    return changed


def fx_value(node_id, condition_id, values):
    return {'nodeId': node_id, 'filedId': NUMBER_FX_ID, 'filedValue': '', 'filedTypeId': NUMBER,
            'conditionId': condition_id, 'sourceType': 0, 'conditionValues': values}


def field_ref(node_id, control_id):
    return [{'nodeId': node_id, 'controlId': control_id, 'value': '', 'sureNodeId': node_id}]


def write_state(entry):
    """A field write reduced to what it means; `nodeAppType` is rewritten by the server (o2i.write_state)."""
    return (entry.get('fieldId'), entry.get('type'), entry.get('addType') or 0, entry.get('fieldValue') or '',
            entry.get('fieldValueId') or '', entry.get('nodeId') or '', bool(entry.get('isClear')))


def set_writes(pid, node, wanted, select_node):
    """Give an update step **exactly** these field writes on the record `select_node` produced, read back."""
    d = read_node(pid, node['id'])
    if (d.get('selectNodeId') == select_node and not d.get('isException')
            and sorted(write_state(x) for x in d.get('fields') or []) == sorted(write_state(w) for w in wanted)):
        return False
    hap.run('workflow', 'node', 'save', pid, node['id'], '--type', '6', '-n', node['name'], '-c', json.dumps(
        {'actionId': d.get('actionId') or '2', 'appId': WORKSHEET, 'appType': 1, 'selectNodeId': select_node,
         'fields': wanted}, ensure_ascii=False))
    back = read_node(pid, node['id'])
    got, want = sorted(write_state(x) for x in back.get('fields') or []), sorted(write_state(w) for w in wanted)
    if got != want or back.get('isException') or back.get('selectNodeId') != select_node:
        sys.exit(f"{node['name']}: read back {got} isException={back.get('isException')}\n  wanted {want}")
    return True


def clear(control):
    """An update step's write that empties a field: `isClear` (the editor's 清空). Sent as a plain empty value the
    entry is dropped on save and the step writes nothing (BUILDING.md › Workflows)."""
    return {'fieldId': control['controlId'], 'type': control['type'], 'addType': 0, 'fieldValue': '',
            'fieldValueId': '', 'nodeId': '', 'isClear': True}


def from_formula(control, node_id):
    """A number formula step's result into a Number — invlines.from_formula."""
    return {'fieldId': control['controlId'], 'type': NUMBER, 'addType': 0, 'fieldValue': '',
            'fieldValueId': NUMBER_FX_ID, 'nodeId': node_id, 'sureNodeId': node_id, 'nodeAppType': 1,
            'nodeTypeId': 9, 'nodeActionId': FORMULA_NUMBER_NODE}


def gateway_paths(proc, gateway_id):
    """A gateway's paths in the order its `flowIds` lists them — the order an exclusive branch tries them."""
    order = proc['flowNodeMap'][gateway_id].get('flowIds') or []
    return [proc['flowNodeMap'][i] for i in order if i in proc['flowNodeMap']]


def payment_path_conditions(f, trigger, due_node):
    """The four paths, tried in order. The first refuses what the two rules refuse in the form — again, for a run
    that did not come through the form; the next three read the Amount Due the payment leaves."""
    pa, pd = f[PAYMENT_AMOUNT], f[PAYMENT_DATE]
    return {
        PATH_REFUSED: [[cond(trigger, pa, EMPTY_C)], [cond(trigger, pa, LE_C, [{'value': '0'}])],
                       [cond(trigger, pa, GT_C, field_ref(trigger, f['Amount Due']['controlId']))],
                       [cond(trigger, pd, EMPTY_C)]],
        PATH_PAID: [[fx_value(due_node, LE_C, [{'value': '0'}])]],
        PATH_PARTIAL: [[fx_value(due_node, LT_C, field_ref(trigger, f['Total']['controlId']))]],
        PATH_UNPAID: [],                            # no condition: the default path of an exclusive branch
    }


def ensure_payment_workflow(f, pid):
    """Build the workflow once, then write every formula, path and field write that differs. Returns True when
    anything changed (the caller publishes)."""
    proc = hap.run('workflow', 'node', 'list', pid)
    trigger = proc['startEventId']
    byname = {n['name']: n for n in proc['flowNodeMap'].values()}
    changed = False
    if PAY_PAID_STEP not in byname:
        first = proc['flowNodeMap'][trigger].get('nextId')
        if first not in (None, '', '99'):
            sys.exit(f'{REGISTER_PAYMENT}: workflow {pid} has steps this script did not build — read it first')
        hap.run('workflow', 'node', 'batch-add', pid, '--nodes', json.dumps(payment_nodes(), ensure_ascii=False),
                '--trigger-node-id', trigger, '--trigger-alias', 'trigger')
        proc = hap.run('workflow', 'node', 'list', pid)
        byname = {n['name']: n for n in proc['flowNodeMap'].values()}
        changed = True
    missing = [s for s in PAY_STEPS if s not in byname]
    if missing:
        sys.exit(f'{REGISTER_PAYMENT}: workflow {pid} is missing {missing}')
    t = lambda name: f"${trigger}-{f[name]['controlId']}$"
    paid_node, due_node = byname[PAY_PAID_STEP]['id'], byname[PAY_DUE_STEP]['id']
    changed |= sync_number_formula(pid, byname[PAY_PAID_STEP], f"{t(AMOUNT_PAID)}+{t(PAYMENT_AMOUNT)}")
    changed |= sync_number_formula(pid, byname[PAY_DUE_STEP], f"{t('Amount Due')}-{t(PAYMENT_AMOUNT)}")
    gateway = byname[PAY_BRANCH]
    if gateway.get('gatewayType') != 2:              # 2 = 唯一分支: the first path whose condition holds
        from hap_cli.core.session import Session
        Session.load(None).workflow_call('flowNode/saveNode', {'nodeId': gateway['id'], 'processId': pid,
                                                               'gatewayType': 2})
        changed = True
    paths = gateway_paths(proc, gateway['id'])
    if len(paths) != len(PAY_PATHS):
        sys.exit(f'{PAY_BRANCH}: {len(paths)} paths, wanted {len(PAY_PATHS)}')
    conditions = payment_path_conditions(f, trigger, due_node)
    for path, (name, step, label) in zip(paths, PAY_PATHS):
        inside = proc['flowNodeMap'].get(path.get('nextId')) or {}
        if inside.get('name') != step:
            sys.exit(f'{PAY_BRANCH}: path {path.get("name")!r} leads to {inside.get("name")!r}, wanted {step!r}')
        changed |= save_payment_path(pid, path, name, conditions[name])
        writes = [clear(f[PAYMENT_AMOUNT]), clear(f[PAYMENT_DATE])]
        if label:
            writes += [from_formula(f[AMOUNT_PAID], paid_node),
                       patch(f[LAST_PAYMENT_DATE]['controlId'], DATE, node=trigger,
                             source=f[PAYMENT_DATE]['controlId']),
                       patch(f[PAYMENT_STATUS]['controlId'], DROPDOWN, value=OPTION_KEY['Payment Status'][label])]
        changed |= set_writes(pid, inside, writes, trigger)
    return changed


def backfill_payment_status(f):
    """Every document with no Payment Status reads Not Paid, as every Odoo move carries a `payment_state`. The
    control's default fills a new document in the form; the API applies no defaults, so a document written through
    the API before or after is filled here. `demo.py invoices` then writes the demo documents' own."""
    ps = f[PAYMENT_STATUS]['controlId']
    empty = [r['rowid'] for r in C.records(WORKSHEET, APP) if not r.get(ps)]
    for rowid in empty:
        hap.run('worksheet', 'record', 'update', WORKSHEET, rowid, '-a', APP, '--fields-json',
                json.dumps([{'id': ps, 'value': [OPTION_KEY['Payment Status']['Not Paid']]}]))
    if empty:
        time.sleep(2)
        still = [r['rowid'] for r in C.records(WORKSHEET, APP) if r['rowid'] in empty and not r.get(ps)]
        if still:
            sys.exit(f'payments: Payment Status did not store on {still}')
    print(f'  Payment Status filled with Not Paid on {len(empty)} document(s) that had none')


def step_payments():
    """Controls, Amount Due as a Formula, the two rules, the button, its workflow (published after every change),
    the guard on Cancel and Reset to Draft, and Payment Status on documents that have none. Re-running saves
    nothing."""
    guard()
    f = hap.by_name(c for c in hap.controls(WORKSHEET) if c['type'] != C.TAB)
    missing = [n for n in PAYMENT_FIELDS if n not in f]
    if missing:
        built = payment_controls()
        f = C.append_checked(WORKSHEET, [built[n] for n in missing], 'invoices_controls_pre_payments', 'payments')
    else:
        print(f'  {list(PAYMENT_FIELDS)} are already on Invoices; nothing appended')
    spec = {}
    for n, want in payment_spec().items():
        stale = C.drift(f[n], want)
        if stale:
            spec[f[n]['controlId']] = {k: want[k] for k in stale}
    live_opts = [(o['key'], o['value']) for o in f[PAYMENT_STATUS].get('options') or [] if not o.get('isDeleted')]
    if live_opts != [(o['key'], o['value']) for o in PAYMENT_STATUS_OPTIONS]:
        spec.setdefault(f[PAYMENT_STATUS]['controlId'], {})['options'] = PAYMENT_STATUS_OPTIONS
    if spec:
        C.pinned_write(WORKSHEET, spec, 'invoices_controls_pre_payments_repair', 'payments')
    else:
        print(f'  {list(PAYMENT_FIELDS)} already as specified; nothing saved')
    ensure_amount_due()
    f = hap.by_name(c for c in hap.controls(WORKSHEET) if c['type'] != C.TAB)
    for n in PAYMENT_FIELDS + ('Amount Due',):
        C.remember('controls', KEY + n, f[n]['controlId'])
    ensure_payment_rules(f)
    b, button_changed = ensure_payment_button(f)
    pid = payment_process_id(b)
    changed = ensure_payment_workflow(f, pid) or button_changed
    info = hap.run('workflow', 'get', pid)
    info = info.get('data', info) if isinstance(info, dict) else {}
    if changed or not info.get('enabled') or info.get('publishStatus') != 2:
        result = C.publish(pid)
        print(f'  {REGISTER_PAYMENT} workflow {pid}: published {result}')
        if not result.get('isPublish'):
            sys.exit(f'{REGISTER_PAYMENT}: publish failed: {result}')
    else:
        print(f'  {REGISTER_PAYMENT} workflow {pid}: already built and published; not re-published')
    ensure_unpaid_guards(f)
    backfill_payment_status(f)
    problems = payment_problems()
    if problems:
        sys.exit('payments: read back with differences\n  ' + '\n  '.join(problems))
    print(C.structure(pid))
    parked = [n for n in PAYMENT_FIELDS if f[n].get('row') == 9999]
    if parked:
        print('  placement outstanding — the owner places these in the designer; intended (row, col, size, tab): '
              + ', '.join(f'{n} {PAYMENT_PLACE[n]}' for n in parked))
    print('  payments: OK')


def payment_problems():
    """Everything `payments` builds, read back — for `check`."""
    ctrls = hap.controls(WORKSHEET)
    f = hap.by_name(c for c in ctrls if c['type'] != C.TAB)
    names = {c['controlId']: c['controlName'] for c in ctrls}
    problems = []
    counts = {}
    for c in ctrls:
        counts[c['controlName']] = counts.get(c['controlName'], 0) + 1
    for n, want in payment_spec().items():
        if counts.get(n, 0) != 1:
            problems.append(f'Invoices carries {counts.get(n, 0)} controls named {n!r}, wanted one — run `payments`')
            continue
        diff = C.drift(f[n], want)
        if diff:
            problems.append(f'{n}: {json.dumps(diff, ensure_ascii=False, default=str)} — run `payments`')
    if PAYMENT_STATUS not in f or AMOUNT_PAID not in f:
        return problems
    diff = C.drift(f['Amount Due'], amount_due_spec(f))
    if diff or amount_due_leftovers(f['Amount Due']):
        problems.append(f"Amount Due is not the Formula Total − Amount Paid: {json.dumps(diff, default=str)} "
                        f"{amount_due_leftovers(f['Amount Due'])}")
    rules = {r['name']: r for r in hap.listing('worksheet', 'rules', WORKSHEET)}
    for name in PAYMENT_RULES:
        r = rules.get(name)
        if r is None or payment_rule_state(r, names) != payment_rule_want(name):
            problems.append(f'rule {name!r}: {r and payment_rule_state(r, names)}')
    b = next((x for x in hap.listing('worksheet', 'custom-actions', WORKSHEET) if x['name'] == REGISTER_PAYMENT),
             None)
    if b is None:
        return problems + [f'button {REGISTER_PAYMENT} missing']
    if payment_button_state(b, names) != payment_button_want(f):
        problems.append(f'button {REGISTER_PAYMENT}: {payment_button_state(b, names)}')
    pid = hap.ids().get('workflows', {}).get(KEY + REGISTER_PAYMENT)
    if not pid:
        return problems + [f'{REGISTER_PAYMENT}: no workflow in ids.json']
    proc = hap.run('workflow', 'node', 'list', pid)
    byname = {n['name']: n for n in proc['flowNodeMap'].values()}
    missing = [s for s in PAY_STEPS if s not in byname]
    if missing:
        return problems + [f'{REGISTER_PAYMENT} workflow is missing {missing}']
    trigger = proc['startEventId']
    conditions = payment_path_conditions(f, trigger, byname[PAY_DUE_STEP]['id'])
    for path, (name, step, _) in zip(gateway_paths(proc, byname[PAY_BRANCH]['id']), PAY_PATHS):
        got = read_node(pid, path['id'])
        if got.get('name') != name or path_conditions_state(got.get('conditions')) != \
                path_conditions_state(conditions[name]):
            problems.append(f'{PAY_BRANCH}: path {got.get("name")!r} differs from {name!r}')
        inside = read_node(pid, path.get('nextId'))
        if inside.get('isException') or not inside.get('fields'):
            problems.append(f'{step}: isException={inside.get("isException")}, {len(inside.get("fields") or [])} '
                            'field writes')
    info = hap.run('workflow', 'get', pid)
    info = info.get('data', info) if isinstance(info, dict) else {}
    if not info.get('enabled') or info.get('publishStatus') != 2:
        problems.append(f"{REGISTER_PAYMENT} workflow: enabled={info.get('enabled')} "
                        f"publishStatus={info.get('publishStatus')} — run `payments`")
    return problems


# ── self-check: Register Payment on a TEST invoice ──────────────────────────

PAY_TEST = 'TEST Register Payment'                 # Customer Reference and Number of the TEST document
PAY_TEST_TOTAL = 1000.0


def buttons_offered(rowid):
    """{button name: offered?} for one document, evaluated by the server — `GetWorksheetBtns` with a `rowId` answers
    each button's `disabled` against the record's own values (orders.buttons_offered)."""
    from hap_cli.core.session import Session
    got = Session.load(None).api_call('Worksheet', 'GetWorksheetBtns',
                                      {'appId': APP, 'worksheetId': WORKSHEET, 'rowId': rowid, 'viewId': ''})
    got = got.get('data', got) if isinstance(got, dict) else got
    return {b['name']: not b.get('disabled') for b in got or []}


def payment_reading(rowid, f):
    """The payment fields through both read paths: `record get` (by alias) and the record listing (by id). The two
    inputs are hidden, so the listing reads them blank whatever they hold (CLAUDE.md › Reading records)."""
    got = hap.run('worksheet', 'record', 'get', WORKSHEET, rowid, '-a', APP)['data']
    listed = next((r for r in C.records(WORKSHEET, APP) if r['rowid'] == rowid), {})
    num = lambda v: None if v in (None, '') else round(float(v), 2)
    label = lambda v: option_label(v) if v not in (None, '') else None
    day_of = lambda v: (v or '')[:10]
    return {
        'get': dict(paid=num(got.get(PAYMENT_ALIAS[AMOUNT_PAID])), due=num(got.get('amount_residual')),
                    total=num(got.get('amount_total')), status=label(got.get(PAYMENT_ALIAS[PAYMENT_STATUS])),
                    last=day_of(got.get(PAYMENT_ALIAS[LAST_PAYMENT_DATE])),
                    amount=num(got.get(PAYMENT_ALIAS[PAYMENT_AMOUNT])),
                    date=day_of(got.get(PAYMENT_ALIAS[PAYMENT_DATE]))),
        'list': dict(paid=num(listed.get(f[AMOUNT_PAID]['controlId'])), due=num(listed.get(f['Amount Due']['controlId'])),
                     total=num(listed.get(f['Total']['controlId'])),
                     status=label(listed.get(f[PAYMENT_STATUS]['controlId'])),
                     last=day_of(listed.get(f[LAST_PAYMENT_DATE]['controlId']))),
    }


def step_selfpayment():
    """On a TEST posted customer invoice (Total 1,000.00, no lines, no email anywhere): a part payment of 400.00, an
    overpayment of 700.00 refused, then the remaining 600.00 — Amount Paid, Amount Due and Payment Status read back
    through both paths after each — and Register Payment, Cancel and Reset to Draft as the server offers them."""
    guard()
    problems = payment_problems()
    if problems:
        sys.exit('\n'.join(problems))
    f = C.fields(WORKSHEET)
    cid = lambda n: f[n]['controlId']
    today = date.today().isoformat()
    pid = hap.ids()['workflows'][KEY + REGISTER_PAYMENT]
    journals = titles(JOURNALS, 'Journal Name')
    partners = titles(CONTACTS, 'Name')
    customer = next((r for r, t in partners.items() if t and not str(t).startswith('TEST')), None)
    reset = [{'id': cid('Number'), 'value': PAY_TEST},
             {'id': cid('Type'), 'value': [OPTION_KEY['Type']['Customer Invoice']]},
             {'id': cid('Status'), 'value': [OPTION_KEY['Status']['Posted']]},
             {'id': cid('Customer / Vendor'), 'value': [customer] if customer else []},
             {'id': cid('Invoice Date'), 'value': today}, {'id': cid('Accounting Date'), 'value': today},
             {'id': cid('Journal'), 'value': [next(r for r, t in journals.items() if t == 'Sales')]},
             {'id': cid('Tax mode'), 'value': [OPTION_KEY['Tax mode']['Tax Excluded']]},
             {'id': cid('Auto-post'), 'value': [OPTION_KEY['Auto-post']['No']]},
             {'id': cid('Customer Reference'), 'value': PAY_TEST},
             {'id': cid('Untaxed Amount'), 'value': PAY_TEST_TOTAL}, {'id': cid('Tax'), 'value': 0},
             {'id': cid('Total'), 'value': PAY_TEST_TOTAL},
             {'id': cid(AMOUNT_PAID), 'value': 0}, {'id': cid(LAST_PAYMENT_DATE), 'value': ''},
             {'id': cid(PAYMENT_STATUS), 'value': [OPTION_KEY['Payment Status']['Not Paid']]},
             {'id': cid(PAYMENT_AMOUNT), 'value': ''}, {'id': cid(PAYMENT_DATE), 'value': ''}]
    rowid = next((r['rowid'] for r in C.records(WORKSHEET, APP) if r.get(cid('Customer Reference')) == PAY_TEST),
                 None)
    if rowid:
        hap.run('worksheet', 'record', 'update', WORKSHEET, rowid, '-a', APP, '--fields-json', json.dumps(reset))
        print(f'  {PAY_TEST} ({rowid}): put back to posted, Total {PAY_TEST_TOTAL:,.2f}, nothing paid')
    else:
        rowid = C.row_id(hap.run('worksheet', 'record', 'create', WORKSHEET, '-a', APP,
                                 '--fields-json', json.dumps(reset)))
        print(f'  {PAY_TEST}: created {rowid}')
    C.remember('records', KEY + PAY_TEST, rowid)
    time.sleep(2)
    bad = []

    def expect(label, want):
        got = payment_reading(rowid, f)
        for path in ('get', 'list'):
            diffs = {k: (got[path].get(k), v) for k, v in want.items() if k in got[path] and got[path].get(k) != v}
            if diffs:
                bad.append(f'{label} / {path}: {diffs}')
        print(f"  {label}\n    record get: {got['get']}\n    listing:    {got['list']}")
        return got

    def offered(label, want):
        got = buttons_offered(rowid)
        mine = {n: got.get(n) for n in (REGISTER_PAYMENT, 'Cancel', 'Reset to Draft', 'Confirm')}
        diffs = {n: (mine[n], v) for n, v in want.items() if mine[n] != v}
        if diffs:
            bad.append(f'{label}: buttons {diffs}')
        print(f'    offered: {mine}' + (f'  <- {diffs}' if diffs else ''))

    def pay(amount, when):
        """What the fill-in form does: store the two inputs (the button's workflow is then run on the record)."""
        try:
            return hap.run('worksheet', 'record', 'update', WORKSHEET, rowid, '-a', APP, '--fields-json', json.dumps(
                [{'id': cid(PAYMENT_AMOUNT), 'value': amount}, {'id': cid(PAYMENT_DATE), 'value': when}]))
        except RuntimeError as e:                  # a refused write can also come back as a failed command
            return str(e)

    def run_and_wait(before_paid):
        hap.run('workflow', 'trigger', pid, '-s', rowid)
        for _ in range(40):
            got = payment_reading(rowid, f)['get']
            if got['paid'] != before_paid and got['amount'] is None:
                return
            time.sleep(1)

    expect('0. posted, nothing paid', dict(paid=0.0, due=PAY_TEST_TOTAL, total=PAY_TEST_TOTAL, status='Not Paid'))
    offered('0', {REGISTER_PAYMENT: True, 'Reset to Draft': True, 'Cancel': False, 'Confirm': False})

    first_day = (date.today() - timedelta(days=3)).isoformat()
    pay(400, first_day)
    run_and_wait(0.0)
    expect('1. a part payment of 400.00', dict(paid=400.0, due=600.0, status='Partially Paid', last=first_day,
                                               amount=None, date=''))
    offered('1', {REGISTER_PAYMENT: True, 'Reset to Draft': False, 'Cancel': False})

    out = pay(700, today)
    stored = payment_reading(rowid, f)['get']
    refused = stored['amount'] is None
    print(f"  2. an overpayment of 700.00 (600.00 due): record update answered "
          f"{json.dumps(out, ensure_ascii=False)[:300]}; Payment Amount now {stored['amount']!r}")
    if not refused:
        bad.append('2: the rule let an overpayment of 700.00 store')
        run_and_wait(400.0)
        time.sleep(3)
    expect('2. after the refused overpayment', dict(paid=400.0, due=600.0, status='Partially Paid', last=first_day,
                                                    amount=None))
    out = pay(0, today)
    zero = payment_reading(rowid, f)['get']['amount']
    print(f"  2b. a payment of 0.00: record update answered {json.dumps(out, ensure_ascii=False)[:300]}; "
          f'Payment Amount now {zero!r}')
    if zero is not None:
        bad.append('2b: the rule let a payment of 0.00 store')
        hap.run('worksheet', 'record', 'update', WORKSHEET, rowid, '-a', APP, '--fields-json', json.dumps(
            [{'id': cid(PAYMENT_AMOUNT), 'value': ''}, {'id': cid(PAYMENT_DATE), 'value': ''}]))

    pay(600, today)
    run_and_wait(400.0)
    expect('3. the remaining 600.00', dict(paid=1000.0, due=0.0, status='Paid', last=today, amount=None, date=''))
    offered('3', {REGISTER_PAYMENT: False, 'Reset to Draft': False, 'Cancel': False})

    # A run that did not come through the form, with nothing filled in: the workflow's own refusal path must leave
    # the document exactly as it is.
    runs = lambda: len(hap.listing('approval', 'history', '--process-id', pid, '-n', '50'))
    ran = runs()
    hap.run('workflow', 'trigger', pid, '-s', rowid)
    for _ in range(20):
        if runs() > ran:
            break
        time.sleep(1)
    time.sleep(2)
    expect('4. the workflow run again with no amount and no date', dict(paid=1000.0, due=0.0, status='Paid',
                                                                         last=today, amount=None, date=''))
    print('  selfpayment: ' + ('OK — part payment, refused overpayment and zero, final payment, and the buttons '
                               'offered as specified' if not bad else 'DIFFERENCES\n    ' + '\n    '.join(bad)))
    return len(bad)


# ── 5 · the three customers, into Contacts ──────────────────────────────────

CONTACT_FIELDS = {'name': 'Name', 'email': 'Email', 'phone': 'Phone', 'street': 'Street', 'street2': 'Street 2',
                  'city': 'City', 'state': 'State', 'zip': 'ZIP', 'country': 'Country', 'comment': 'Notes'}
_SEEDABLE = {}


def seedable_contact_fields():
    """The seed-file fields this step still writes — the ones whose Contacts control is a **text** field.

    **State and Country are no longer among them.** Bundle 11 (Countries) and bundle 12 (States) turned those
    two Contacts controls into Relations, and a text write into a Relation is accepted and stores nothing: from
    then on this step found a difference on every run, re-wrote the same three records, and then failed its own
    read-back (found 21 Sep 2026, while seeding bundle 7's Casimir). Linking a contact to its country and state
    is those bundles' work, not this one's — the three customers' values are still in
    `data/casimir-invoice-seed.json` and 06 §1 records that they are not seeded."""
    if not _SEEDABLE:
        f = C.fields(CONTACTS)
        _SEEDABLE.update({k: n for k, n in CONTACT_FIELDS.items() if f[n]['type'] != RELATION})
    return _SEEDABLE


# ── bundle 7 · two more of the tenant's documents, read off casimir.odoo.com on 21 Sep 2026 ─────────────────
#
# §1 › Records passed over the tenant's records 4–8 as "demo and test traffic". Two of them are worth having
# after all, because between them they exercise three things the first three documents do not:
#
#   * **two different tax rates on one document** — INV/2026/00002 carries a 10 % line and an 8 % one;
#   * a **Section** line, which the roll-up must leave out (07 §1);
#   * **negative** lines, which it must take in.
#
# They are held here rather than in `data/casimir-invoice-seed.json`: that file is the 15 Sep extract and is
# left exactly as it was. `seed_file()` appends them, so every step — `customers`, `seed`, `verify` — reads
# all five documents without knowing the difference.
#
# **Three fields were not in the tenant reading and are not invented quietly** (06 §1 › Records):
#   * **Accounting Date** is required here, so both documents take the day their other dates carry, 2026-09-14
#     — which is also what Odoo's `_post` books a document under when its Invoice Date is that day;
#   * **Delivery Address** is Odoo's own default, the customer itself (`partner_shipping_id = partner_id`);
#   * **Payment Reference** is left **empty** on both rather than guessed, even on the posted one, where our
#     own Confirm would have written the number.
EXTRA_PARTNERS = [
    {
        'name': 'Casimir',                         # the tenant's own partner record; a contact, not a company
        'is_company': False,
        'type': 'contact',
        'email': '', 'phone': '', 'street': '', 'street2': '', 'city': '', 'state': '', 'zip': '',
        'country': '', 'user_id': 'Casimir', 'comment': '', 'active': True,
    },
]
EXTRA_MOVES = [
    {
        # The tenant's own demo run, and the document with two tax rates. **It is `paid` on the tenant, with
        # Amount Due 0.00**; our roll-up writes Amount Due = Σ Total unconditionally, because there is no
        # Payments model yet, so the seeded record reads 3,027.80. `amount_residual_tenant` keeps the tenant's
        # own figure beside it; nothing reads it, and Amount Due is never hand-written to force a match.
        'name': 'INV/2026/00002',
        'move_type': 'out_invoice',
        'state': 'posted',
        'partner': 'Casimir',
        'partner_shipping': 'Casimir',
        'invoice_date': '2026-09-14',
        'date': '2026-09-14',
        'invoice_date_due': '2026-09-14',
        'invoice_payment_term': '',
        'journal': 'Sales',
        'ref': 'TEST demo run - delete me',
        'payment_reference': '',
        'invoice_user_id': 'Casimir',
        'invoice_origin': '',
        'document_tax_mode': 'tax_excluded',
        'amount_untaxed': 2768.0,
        'amount_tax': 259.8,
        'amount_total': 3027.8,
        'amount_residual': 3027.8,
        'amount_residual_tenant': 0.0,
        'payment_state': 'paid',
        'narration': '',
        'delivery_date': '',
        'auto_post': 'no',
        'currency': 'MYR',
    },
    {
        # The cancelled S00021: never numbered, so its Number is the word "Draft", and the document that
        # carries the Section line and the two negative down payments.
        'name': '',
        'move_type': 'out_invoice',
        'state': 'cancel',
        'partner': 'Casimir',
        'partner_shipping': 'Casimir',
        'invoice_date': '',
        'date': '2026-09-14',
        'invoice_date_due': '2026-09-14',
        'invoice_payment_term': '',
        'journal': 'Sales',
        'ref': 'S00021',
        'payment_reference': '',
        'invoice_user_id': 'Casimir',
        'invoice_origin': '',
        'document_tax_mode': 'tax_excluded',
        'amount_untaxed': 1087.6,
        'amount_tax': 113.86,
        'amount_total': 1201.46,
        'amount_residual': 1201.46,
        'payment_state': 'not_paid',
        'narration': '',
        'delivery_date': '',
        'auto_post': 'no',
        'currency': 'MYR',
    },
]


def seed_file():
    """The 15 Sep extract, with bundle 7's two documents and their customer appended. Both lists are keyed —
    partners by Name, moves by Customer Reference — so nothing is added twice if the file ever gains them."""
    data = json.loads(SEED.read_text(encoding='utf-8'))
    have = {p['name'] for p in data['partners']}
    data['partners'] = data['partners'] + [p for p in EXTRA_PARTNERS if p['name'] not in have]
    refs = {m['ref'] for m in data['moves']}
    data['moves'] = data['moves'] + [m for m in EXTRA_MOVES if m['ref'] not in refs]
    return data


def contacts_by_name():
    f = C.fields(CONTACTS)
    name = f['Name']['controlId']
    return {r.get(name): r for r in C.records(CONTACTS, APP)}


def salesperson_id():
    """Casimir's HAP account id, read from the profile rather than hard-coded."""
    return hap.run('auth', 'whoami')['id']


def read_contact(rowid):
    """One customer as Contacts stores it, in the seed file's own vocabulary."""
    d = hap.run('worksheet', 'record', 'get', CONTACTS, rowid, '-a', APP)['data']
    got = {k: d.get(k) or '' for k in seedable_contact_fields()}
    got['type'] = option_label(d.get('type'))
    got['user_id'] = ([x.get('accountId') for x in d.get('user_id') or []] or [''])[0]
    got['active'] = str(d.get('active')) in ('1', 'True', 'true')
    return got


def contact_differences(live, p):
    want = {k: p.get(k) or '' for k in seedable_contact_fields()}
    want.update(type='Contact', user_id=salesperson_id(), active=True)
    return {k: (live.get(k), v) for k, v in want.items() if live.get(k) != v}


def step_customers():
    """The customers the tenant's invoices point at, into Contacts — the three companies of the 15 Sep extract
    and bundle 7's **Casimir**, the tenant's own contact. Records only. Matched by Name and
    compared field by field, so a second run writes nothing; no field, view, rule or other record in Contacts is
    touched, and the other worksheets' controls are compared by id before and after."""
    before = signatures()
    f = C.fields(CONTACTS)
    cid = lambda n: f[n]['controlId']
    left_out = [n for k, n in CONTACT_FIELDS.items() if k not in seedable_contact_fields()]
    if left_out:
        print(f'  not seeded here: {left_out} — a Relation on Contacts since bundles 11 and 12, and a text '
              f'write into one stores nothing (see seedable_contact_fields)')
    contact = next(o['key'] for o in f['Address Type']['options'] if o['value'] == 'Contact')
    live = contacts_by_name()
    hap.backup('invoices_contacts_pre_customers', {n: r.get('rowid') for n, r in live.items()})
    for p in seed_file()['partners']:
        row = live.get(p['name'])
        if row and not contact_differences(read_contact(row['rowid']), p):
            continue
        values = [{'id': cid(n), 'value': p[k]} for k, n in seedable_contact_fields().items() if p.get(k)]
        values += [{'id': cid('Address Type'), 'value': [contact]},
                   {'id': cid('Salesperson'), 'value': [salesperson_id()]},
                   {'id': cid('Active'), 'value': 1}]                # always explicit on API writes
        if row:
            hap.run('worksheet', 'record', 'update', CONTACTS, row['rowid'], '-a', APP,
                    '--fields-json', json.dumps(values, ensure_ascii=False))
            print(f"  updated {p['name']}: {row['rowid']}")
        else:
            rowid = C.row_id(hap.run('worksheet', 'record', 'create', CONTACTS, '-a', APP,
                                     '--fields-json', json.dumps(values, ensure_ascii=False)))
            print(f"  created {p['name']}: {rowid}")
    check_untouched(before)
    live = contacts_by_name()
    for p in seed_file()['partners']:
        row = live.get(p['name'])
        if not row:
            sys.exit(f"{p['name']} not in Contacts after the write")
        C.remember('records', KEY + 'customer ' + p['name'], row['rowid'])
        got = read_contact(row['rowid'])
        diffs = contact_differences(got, p)
        print(f"  {'OK  ' if not diffs else 'DIFF'}  {p['name']:<28} {got['city']} / {got['zip']} / "
              f"{got['email']} / {got['phone']}" + (f'  <- {diffs}' if diffs else ''))
        if diffs:
            sys.exit(f"{p['name']}: read back {diffs}")


# ── 6 · the three documents ─────────────────────────────────────────────────

TYPE_OF = {'entry': 'Journal Entry', 'out_invoice': 'Customer Invoice', 'out_refund': 'Customer Credit Note',
           'in_invoice': 'Vendor Bill', 'in_refund': 'Vendor Credit Note', 'out_receipt': 'Sales Receipt',
           'in_receipt': 'Purchase Receipt'}
STATE_OF = {'draft': 'Draft', 'posted': 'Posted', 'cancel': 'Cancelled'}
TAX_MODE_OF = {'tax_excluded': 'Tax Excluded', 'tax_included': 'Tax Included'}
DRAFT = 'Draft'                                    # what an unnumbered draft's Number holds


def expected(m):
    """One seeded document as the worksheet should store it."""
    return dict(number=m['name'] or DRAFT, type=TYPE_OF[m['move_type']], status=STATE_OF[m['state']],
                partner=m['partner'], shipping=m['partner_shipping'], invoice_date=m['invoice_date'],
                date=m['date'], due=m['invoice_date_due'], terms=m['invoice_payment_term'], journal=m['journal'],
                tax_mode=TAX_MODE_OF[m['document_tax_mode']], ref=m['ref'],
                payment_reference=m['payment_reference'], origin=m['invoice_origin'],
                delivery_date=m['delivery_date'], auto_post='No',
                untaxed=m['amount_untaxed'], tax=m['amount_tax'], total=m['amount_total'],
                residual=m['amount_residual'])


def titles(worksheet, control_name):
    """{rowid: title} of a related worksheet, for reading a Relation back as a name."""
    f = C.fields(worksheet)
    cid = f[control_name]['controlId']
    return {r['rowid']: r.get(cid) for r in C.records(worksheet, APP)}


def relation_names(value):
    """A Relation read back through `record get` is a JSON array of records; take their names."""
    if isinstance(value, str):
        value = json.loads(value) if value.startswith('[') else []
    return [x.get('name') for x in value if isinstance(x, dict)]


def option_label(v):
    if isinstance(v, str):
        v = json.loads(v) if v.startswith('[') else []
    labels = [x.get('value') if isinstance(x, dict) else x for x in (v if isinstance(v, list) else [])]
    return labels[0] if labels else None


def read_document(rowid):
    """One document through `record get` (keyed by alias); `record list` can return hidden fields empty."""
    d = hap.run('worksheet', 'record', 'get', WORKSHEET, rowid, '-a', APP)['data']
    number = lambda k: round(float(d.get(k) or 0), 2)
    first = lambda k: (relation_names(d.get(k)) or [''])[0]
    return dict(rowid=rowid, number=d.get('name') or '', type=option_label(d.get('move_type')),
                status=option_label(d.get('state')), partner=first('partner_id'),
                shipping=first('partner_shipping_id'), invoice_date=d.get('invoice_date') or '',
                date=d.get('date') or '', due=d.get('invoice_date_due') or '',
                terms=first('invoice_payment_term_id'), journal=first('journal_id'),     # the term's name (bundle 3)
                tax_mode=option_label(d.get('document_tax_mode')), ref=d.get('ref') or '',
                payment_reference=d.get('payment_reference') or '', origin=d.get('invoice_origin') or '',
                delivery_date=d.get('delivery_date') or '', auto_post=option_label(d.get('auto_post')),
                untaxed=number('amount_untaxed'), tax=number('amount_tax'), total=number('amount_total'),
                residual=number('amount_residual'))


def read_documents():
    return {r['rowid']: read_document(r['rowid']) for r in C.records(WORKSHEET, APP)}


def differences(live, m):
    return {k: (live.get(k), v) for k, v in expected(m).items() if live.get(k) != v}


def values_for(f, m, partners, journals):
    """The record write for one seeded document, with the Relations resolved to rowids."""
    want = expected(m)
    cid = lambda n: f[n]['controlId']
    key = lambda field, label: OPTION_KEY[field][label]
    rows = lambda ws_titles, name: [next(r for r, t in ws_titles.items() if t == name)]
    values = [
        {'id': cid('Number'), 'value': want['number']},
        {'id': cid('Type'), 'value': [key('Type', want['type'])]},
        {'id': cid('Status'), 'value': [key('Status', want['status'])]},
        {'id': cid('Customer / Vendor'), 'value': rows(partners, want['partner'])},
        {'id': cid('Delivery Address'), 'value': rows(partners, want['shipping'])},
        {'id': cid('Invoice Date'), 'value': want['invoice_date']},
        {'id': cid('Accounting Date'), 'value': want['date']},
        {'id': cid('Due Date'), 'value': want['due']},
        # a relation since bundle 3: the term's record, looked up by its name; never text
        {'id': cid('Payment Terms'), 'value': [hap.ids()['records']['Payment Terms: ' + want['terms']]]
                                              if want['terms'] else []},
        {'id': cid('Journal'), 'value': rows(journals, want['journal'])},
        {'id': cid('Tax mode'), 'value': [key('Tax mode', want['tax_mode'])]},
        {'id': cid('Untaxed Amount'), 'value': want['untaxed']},
        {'id': cid('Tax'), 'value': want['tax']},
        {'id': cid('Total'), 'value': want['total']},
        {'id': cid('Amount Due'), 'value': want['residual']},
        {'id': cid('Customer Reference'), 'value': want['ref']},
        {'id': cid('Salesperson'), 'value': [salesperson_id()]},
        {'id': cid('Payment Reference'), 'value': want['payment_reference']},
        {'id': cid('Delivery Date'), 'value': want['delivery_date']},
        {'id': cid('Source Document'), 'value': want['origin']},
        {'id': cid('Auto-post'), 'value': [key('Auto-post', want['auto_post'])]},
    ]
    return values


def seed_key(d):
    """What matches a live document with a seeded one: the Customer Reference, which is the tenant's own."""
    return d.get('ref')


def step_seed():
    """The tenant's invoices, matched by Customer Reference — SCG-PO-88213, KKD-2026-009 and STL-2026-0042
    from `data/casimir-invoice-seed.json`, and bundle 7's two (TEST demo run - delete me, S00021) from
    `EXTRA_MOVES` above. Their customers must be in Contacts already — run `customers` first.

    The four amounts are written here as the tenant reads them and then **recomputed by 07's roll-up** as soon
    as the document has lines; the two figures agree for every document but INV/2026/00002, whose Amount Due
    the tenant shows as 0.00 (see EXTRA_MOVES).

    A **Cancelled** document is seeded exactly like any other: *A posted or cancelled document is closed for
    editing* is an interaction rule, and an interaction rule is browser-side only — `record create` and
    `record update` write the fields it greys out (BUILDING.md, 07 difference 11)."""
    guard()
    f = C.fields(WORKSHEET)
    partners, journals = titles(CONTACTS, 'Name'), titles(JOURNALS, 'Journal Name')
    live = {seed_key(d): d for d in read_documents().values()}
    hap.backup('invoices_records_pre_seed', live)
    for m in seed_file()['moves']:
        got = live.get(m['ref'])
        if got and not differences(got, m):
            continue
        values = json.dumps(values_for(f, m, partners, journals), ensure_ascii=False)
        if got:
            hap.run('worksheet', 'record', 'update', WORKSHEET, got['rowid'], '-a', APP, '--fields-json', values)
            rowid = got['rowid']
            print(f"  updated {m['ref']}")
        else:
            rowid = C.row_id(hap.run('worksheet', 'record', 'create', WORKSHEET, '-a', APP, '--fields-json', values))
            print(f"  created {m['ref']}: {rowid}")
        back = read_document(rowid)
        if differences(back, m):
            sys.exit(f"{m['ref']}: read back {differences(back, m)}")
        C.remember('records', KEY + m['ref'], rowid)
    return step_verify()


def step_verify():
    """Compare the live documents with the seed file, field by field."""
    live = {seed_key(d): d for d in read_documents().values()}
    bad = 0
    for m in seed_file()['moves']:
        got = live.get(m['ref'])
        if not got:
            print(f"  MISSING  {m['ref']}")
            bad += 1
            continue
        diffs = differences(got, m)
        bad += bool(diffs)
        print(f"  {'OK  ' if not diffs else 'DIFF'}  {got['number']:<15} {got['type']:<18} {got['status']:<10} "
              f"{got['partner']:<28} {got['date']} total={got['total']}" + (f'  <- {diffs}' if diffs else ''))
    extra = sorted(f"{d['number']} ({ref})" for ref, d in live.items()
                   if ref not in {m['ref'] for m in seed_file()['moves']})
    print(f"  {len(seed_file()['moves'])} in the seed file; {bad} missing or differing; "
          f'{len(extra)} not in it {extra}')
    return bad


def step_document(*numbers):
    docs = read_documents()
    by_number = {d['number']: d for d in docs.values()}
    for number in numbers or sorted(by_number):
        d = by_number.get(number)
        print(f'  {number}: ' + (json.dumps(d, ensure_ascii=False) if d else 'no such document'))


def step_order():
    """Each view's records in the order the view returns them (its own filter and sort). `record list --view-id`
    returns only the view's own columns, so the Accounting Date it sorts on is read separately."""
    f = C.fields(WORKSHEET)
    number = f['Number']['controlId']
    dates = {d['rowid']: d['date'] for d in read_documents().values()}
    for v in hap.listing('worksheet', 'view', 'list', WORKSHEET, '-a', APP):
        res = hap.run('worksheet', 'record', 'list', WORKSHEET, '-a', APP, '-n', '100', '--view-id', v['viewId'],
                      '--use-field-id-as-key')
        data = res.get('data', res) if isinstance(res, dict) else res
        rows = (data.get('rows') if isinstance(data, dict) else data) or []
        print(f"  {v['name']} ({len(rows)}): "
              + ', '.join(f"{r.get(number)} [{dates.get(r['rowid'])}]" for r in rows))


# ── self-check: the numbering, through the CLI ──────────────────────────────

def test_document(f, ref, type_label, journal, partners, journals, today):
    cid = lambda n: f[n]['controlId']
    values = [{'id': cid('Number'), 'value': DRAFT},
              {'id': cid('Type'), 'value': [OPTION_KEY['Type'][type_label]]},
              {'id': cid('Status'), 'value': [OPTION_KEY['Status']['Draft']]},
              {'id': cid('Accounting Date'), 'value': today},
              {'id': cid('Journal'), 'value': [next(r for r, t in journals.items() if t == journal)]},
              {'id': cid('Auto-post'), 'value': [OPTION_KEY['Auto-post']['No']]},
              {'id': cid('Customer Reference'), 'value': ref}]
    if type_label != 'Journal Entry':              # Odoo's SQL constraint leaves an entry without a tax mode
        values += [{'id': cid('Tax mode'), 'value': [OPTION_KEY['Tax mode']['Tax Excluded']]},
                   {'id': cid('Customer / Vendor'),
                    'value': [next(r for r, t in partners.items() if t == 'Sunway Construction Group')]}]
    return values


def wait_for(rowid, wanted, seconds=30):
    for _ in range(seconds):
        d = read_document(rowid)
        if wanted(d):
            return d
        time.sleep(1)
    return read_document(rowid)


# The numbering the self-check proves: two Sales invoices in a row after the seeded INV/2026/00001; a credit note
# on the same journal, which has a Dedicated Credit Note Sequence (RINV); a bill on Purchases; and two plain
# entries on Miscellaneous Operations. Each also gives its view a row for the UI test.
# (ref, Type, Journal, the prefix Confirm must build, Payment Reference filled?, Invoice Date filled?)
TEST_DOCUMENTS = (('TEST-SEQ-1', 'Customer Invoice', 'Sales', 'INV', True, True),
                  ('TEST-SEQ-2', 'Customer Invoice', 'Sales', 'INV', True, True),
                  ('TEST-SEQ-3', 'Customer Credit Note', 'Sales', 'RINV', True, True),
                  ('TEST-SEQ-4', 'Vendor Bill', 'Purchases', 'BILL', False, True),
                  ('TEST-SEQ-5', 'Journal Entry', 'Miscellaneous Operations', 'MISC', False, False),
                  ('TEST-SEQ-6', 'Journal Entry', 'Miscellaneous Operations', 'MISC', False, False),
                  ('TEST-SEQ-7', 'Customer Invoice', 'Sales', 'INV', True, True))
TEST_REFS = tuple(d[0] for d in TEST_DOCUMENTS)
NUMBER_PATTERN = re.compile(r'^(.+)/(\d{4})/(\d{5})$')


def to_clean_draft(f, rowid):
    """Put a TEST document back to an unnumbered draft, so the self-check numbers the same way every run."""
    cid = lambda n: f[n]['controlId']
    hap.run('worksheet', 'record', 'update', WORKSHEET, rowid, '-a', APP, '--fields-json', json.dumps([
        {'id': cid('Number'), 'value': DRAFT},
        {'id': cid('Status'), 'value': [OPTION_KEY['Status']['Draft']]},
        {'id': cid('Invoice Date'), 'value': ''},
        {'id': cid('Payment Reference'), 'value': ''}]))


def numbered_as(number, prefix, year):
    """Does `number` read "<prefix>/<year>/<5 digits>"?"""
    got = NUMBER_PATTERN.match(number or '')
    return bool(got) and got.group(1) == prefix and got.group(2) == str(year)


def step_selfcheck():
    """Confirm the TEST drafts and read the numbers back: two Sales invoices in a row (so INV follows the seeded
    INV/2026/00001), a credit note on the same journal, which has a Dedicated Credit Note Sequence (RINV), a bill
    on Purchases, and two plain entries on Miscellaneous Operations (MISC), which must come back **without** an
    Invoice Date. Reset to Draft and Cancel then run on the credit note, both keeping the Number.

    A document that **already carries a number of the right shape is left alone**, whatever its Status — the
    numbers a Confirm produces depend on what is already posted, so re-running this after a UI test must not
    renumber what the test left behind. Worse, resetting a numbered document frees its number for the next
    Confirm, which then hands it to a different record: re-running an earlier version of this step took
    RINV/2026/00001 back off a cancelled document and re-issued RINV/2026/00002, which the UI test had already
    given to another record. Only an unnumbered draft is confirmed here."""
    guard()
    f = C.fields(WORKSHEET)
    partners, journals = titles(CONTACTS, 'Name'), titles(JOURNALS, 'Journal Name')
    today = date.today()
    live = {seed_key(d): d for d in read_documents().values()}
    workflows, bad = hap.ids()['workflows'], 0
    made = []
    for ref, type_label, journal, _, _, _ in TEST_DOCUMENTS:
        d = live.get(ref)
        if not d:
            rowid = C.row_id(hap.run('worksheet', 'record', 'create', WORKSHEET, '-a', APP, '--fields-json',
                                     json.dumps(test_document(f, ref, type_label, journal, partners, journals,
                                                              today.isoformat()), ensure_ascii=False)))
            print(f'  created {ref}: {rowid}')
            d = read_document(rowid)
        made.append(d)
        C.remember('records', KEY + ref, d['rowid'])
    for d, (ref, _, _, prefix, customer, dated) in zip(made, TEST_DOCUMENTS):
        if numbered_as(d['number'], prefix, today.year):
            print(f"  --    {ref:<12} already carries {d['number']} ({d['status']}); left as it stands")
            continue
        to_clean_draft(f, d['rowid'])
        hap.run('workflow', 'trigger', workflows[KEY + 'Confirm'], '-s', d['rowid'])
        after = wait_for(d['rowid'], lambda x: x['status'] == 'Posted' and x['number'] != DRAFT)
        # Odoo _post fills the Invoice Date on an invoice or receipt only, and the Payment Reference with the
        # number on a customer document only
        ok = (numbered_as(after['number'], prefix, today.year)
              and after['invoice_date'] == (today.isoformat() if dated else '')
              and after['payment_reference'] == (after['number'] if customer else ''))
        bad += not ok
        print(f"  {'OK  ' if ok else 'DIFF'}  Confirm {ref:<12} -> {after['number']:<18} "
              f"status={after['status']:<10} invoice date={after['invoice_date']!r} "
              f"payment reference={after['payment_reference']!r}"
              + ('' if ok else f"  <- wanted {prefix}/{today.year}/nnnnn, "
                               f"date {today.isoformat() if dated else ''!r}"))
    # Reset to Draft, Confirm again and Cancel, all on the credit note, all keeping the Number: Odoo `_post`
    # sequences a move only when its `name` is unset and `button_draft` keeps the name, so a document that is
    # reset and confirmed again takes its old number back rather than a new one.
    credit_note = read_document(made[2]['rowid'])
    for step, status in (('Reset to Draft', 'Draft'), ('Confirm', 'Posted'), ('Cancel', 'Cancelled')):
        hap.run('workflow', 'trigger', workflows[KEY + step], '-s', credit_note['rowid'])
        after = wait_for(credit_note['rowid'], lambda x, s=status: x['status'] == s)
        ok = after['status'] == status and after['number'] == credit_note['number']
        bad += not ok
        print(f"  {'OK  ' if ok else 'DIFF'}  {step:<14} {after['ref']} -> status={after['status']}, "
              f"number kept {after['number']!r}")
    return bad


# ── check: read the configuration back ──────────────────────────────────────

def step_check():
    """Controls, options, defaults, rules, views, buttons and the numbering workflow against this spec."""
    ctrls = hap.controls(WORKSHEET)
    f = hap.by_name(ctrls)
    names = {c['controlId']: c['controlName'] for c in ctrls}
    problems = []
    # o2i.py owns the two the order → invoice link added on 23 Sep 2026; this script neither writes nor places
    # them, and their rows are the owner's (Other Info › Invoice, row 18).
    known = set(PLACE) | set(INCOTERM_FIELDS) | set(O2I_FIELDS) | set(PAYMENT_FIELDS)
    if set(f) != known:
        problems.append(f'controls {sorted(set(f) ^ known)}')
    problems += [f'{n}: {d}' for n, d in layout_differences(ctrls).items()]
    for cid, (name, _) in FIRST_BUILD.items():
        want = RENAME.get(cid, name)
        if f.get(want, {}).get('controlId') != cid:
            problems.append(f"{want} id is {f.get(want, {}).get('controlId')}, skeleton {cid}")
    for name, opts in OPTIONS.items():
        live = [(o['key'], o['value']) for o in f.get(name, {}).get('options', []) if not o.get('isDeleted')]
        if live != [(o['key'], o['value']) for o in opts]:
            problems.append(f'{name} options {live}')
    for name, want in {'Number': 'Draft', 'Type': 'Customer Invoice', 'Status': 'Draft', 'Tax mode': 'Tax Excluded',
                       'Auto-post': 'No', 'Untaxed Amount': '0', 'Tax': '0', 'Total': '0',
                       PAYMENT_STATUS: 'Not Paid', AMOUNT_PAID: '0'}.items():
        if name not in f:
            continue
        source = json.loads((f[name].get('advancedSetting') or {}).get('defsource') or '[]')
        value = source[0]['staticValue'] if source else None
        label = next((o['value'] for o in f[name].get('options', []) if o['key'] == value), value)
        if label != want:
            problems.append(f'{name} default {label!r}, want {want!r}')
    # The three Date fields' defaults, compared as the stored string: a date default is a sentinel, not a value,
    # and the API applies no defaults at all, so the string itself is the only thing that can be checked here.
    for name, want in (('Accounting Date', TODAY), ('Invoice Date', '[]'), ('Due Date', '[]')):
        got = (f.get(name, {}).get('advancedSetting') or {}).get('defsource')
        print(f"  date default {name:<16} {got!r}" + ('' if got == want else f'  <- want {want!r}'))
        if got != want:
            problems.append(f'{name} defsource {got!r}, want {want!r}')
    if f.get(TITLE, {}).get('attribute') != 1:
        problems.append(f'{TITLE} is not the title field')
    for name, target in RELATIONS.items():
        if f.get(name, {}).get('dataSource') != target:
            problems.append(f"{name} points at {f.get(name, {}).get('dataSource')}, want {target}")
    rules = {r['name']: r for r in hap.listing('worksheet', 'rules', WORKSHEET)}
    for name, (driver, labels, targets, kind) in {**RULES, **INCOTERM_RULES}.items():
        r = rules.get(name)
        if not r:
            problems.append(f'rule {name!r} missing')
            continue
        got = interaction_rule_state(r, names)
        if got != interaction_rule_want(driver, labels, targets, kind):
            problems.append(f'rule {name!r}: {got}')
    problems += incoterm_problems(f)
    if JOURNAL_TYPE in f:
        keys = journal_type_keys()
        label_of = {k: v for v, k in keys.items()}
        for name, (labels, journal_type, message) in JOURNAL_CHECKS.items():
            r = rules.get(name)
            if not r:
                problems.append(f'rule {name!r} missing')
                continue
            conds = [g for group in r['filters'] for g in group.get('groupFilters', [])]
            got = (r['type'], r['disabled'], r.get('checkType'), r.get('hintType'),
                   sorted((names.get(c['controlId']), c['filterType'],
                           tuple(sorted(LABEL['Type'].get(v) or label_of.get(v) or v for v in c.get('values') or [])))
                          for c in conds),
                   [(i['type'], [names.get(c['controlId']) for c in i['controls']], i.get('message', ''))
                    for i in r['ruleItems']])
            want = (C.VALIDATION, False, 1, 0,
                    sorted([('Type', C.EQ, tuple(sorted(labels))), (JOURNAL_TYPE, C.NOT_EMPTY, ()),
                            (JOURNAL_TYPE, C.NE, (journal_type,))]),
                    [(C.ERROR, ['Journal'], message)])
            if got != want:
                problems.append(f'rule {name!r}: {got}')
    views = {v['name']: C.view_info(WORKSHEET, APP, v['viewId']) for v in
             hap.listing('worksheet', 'view', 'list', WORKSHEET, '-a', APP)}
    want_views = {'Invoices': (DOC_COLUMNS, CUSTOMER_TYPES), 'Bills': (DOC_COLUMNS, VENDOR_TYPES),
                  'Journal Entries': (ENTRY_COLUMNS, ['Journal Entry'])}
    for name, (columns, types) in want_views.items():
        v = views.get(name, {})
        got = dict(columns=[names.get(x) for x in v.get('showControls', [])],
                   sort=[(names.get(s['controlId']), s['isAsc']) for s in v.get('moreSort', [])],
                   sortCid=names.get(v.get('sortCid')), sortType=v.get('sortType'),
                   filters=[(names.get(x['controlId']), x['filterType'],
                             sorted(LABEL['Type'].get(y, y) for y in x.get('values') or []))
                            for x in v.get('filters', [])],
                   quick=[names.get(q['controlId']) for q in v.get('fastFilters', [])])
        want = dict(columns=list(columns), sort=[('Accounting Date', False), ('Number', False)],
                    sortCid='Accounting Date', sortType=1, filters=[('Type', EQ_SINGLE, sorted(types))],
                    quick=['Type', 'Status'])
        if got != want:
            problems.append(f'view {name}: {got}')
    if list(views) != list(VIEWS):
        problems.append(f'view order {list(views)}')
    buttons = {b['name']: b for b in hap.listing('worksheet', 'custom-actions', WORKSHEET)}
    for name, labels, confirm in (('Confirm', ['Draft'], ''), ('Cancel', ['Draft'], MSG_CANCEL),
                                  ('Reset to Draft', ['Posted', 'Cancelled'], '')):
        b = buttons.get(name)
        if not b:
            problems.append(f'button {name} missing')
            continue
        conds = button_conditions(b, names)
        want = [('Status', EQ_SINGLE, tuple(sorted(labels)))]
        if name in UNPAID_ONLY:                     # 23 Sep 2026: refused on a paid or partly paid document
            want.append(UNPAID_CONDITION)
        if conds != sorted(want) or (b.get('confirmMsg') or '') != confirm:
            problems.append(f"button {name}: filters={conds} confirm={b.get('confirmMsg')!r}")
    problems += payment_problems()
    pid = hap.ids().get('workflows', {}).get(KEY + 'Confirm')
    if pid:
        _, byname = nodes_by_name(pid)
        missing = [n for n in NUMBERING_STEPS + (POST_STEP,) if n not in byname]
        if missing:
            problems.append(f'Confirm workflow is missing {missing}')
    order = sorted(ctrls, key=lambda c: (c.get('row', 0), c.get('col', 0)))
    tab_ids = {c['controlName']: c['controlId'] for c in ctrls if c['type'] == C.TAB}
    for tab in TABS:
        print(f"  tab {tab}: {[c['controlName'] for c in order if c.get('sectionId') == tab_ids.get(tab)]}")
    print(f"  no tab: {[c['controlName'] for c in order if not c.get('sectionId') and c['type'] != C.TAB]}")
    parked = [n for n in INCOTERM_FIELDS if f.get(n, {}).get('row') == 9999]
    if parked:
        print(f'  NOTE {parked} still parked at row 9999 of Other Info, for the owner to place: '
              + ', '.join(f'{n} {INCOTERM_PLACE[n]}' for n in parked))
    print('  check: ' + ('OK — controls, tabs, options, defaults, rules, views, buttons and the numbering '
                         'workflow as specified, Incoterm with its receipt rule, and Register Payment' if not problems
                         else 'DIFFERENCES\n    ' + '\n    '.join(problems)))
    return len(problems)


def step_all():
    for name in ('layout', 'rules', 'views', 'buttons', 'customers', 'seed'):
        print(f'\n── {name} ' + '─' * 60)
        STEPS[name]()
    print('\n── check ' + '─' * 60)
    return step_check()


def show():
    C.show(WORKSHEET)


STEPS = {
    'layout': step_layout,
    'rules': step_rules,
    'views': step_views,
    'buttons': step_buttons,
    'numbering': step_numbering,
    'customers': step_customers,
    'seed': step_seed,
    'all': step_all,
    'verify': step_verify,
    'check': step_check,
    'selfcheck': step_selfcheck,
    'order': step_order,
    'document': step_document,
    'untouched': step_untouched,
    'incoterm': step_incoterm,
    'selfincoterm': step_selfincoterm,
    'payments': step_payments,
    'selfpayment': step_selfpayment,
    'show': show,
}

if __name__ == '__main__':
    step = sys.argv[1] if len(sys.argv) > 1 else 'check'
    if step not in STEPS:
        raise SystemExit(f"Unknown step {step!r}; choose from {', '.join(STEPS)}")
    result = STEPS[step](*sys.argv[2:])
    if step in ('verify', 'check', 'all', 'selfcheck', 'selfincoterm', 'selfpayment') and result:
        sys.exit(1)
