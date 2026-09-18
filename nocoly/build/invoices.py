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
    ~/.hap-venv/bin/python nocoly/build/invoices.py rules       # 2. the seven interaction rules (upsert by name)
    ~/.hap-venv/bin/python nocoly/build/invoices.py views       # 3. Invoices, Bills and Journal Entries
    ~/.hap-venv/bin/python nocoly/build/invoices.py buttons     # 4. Confirm / Cancel / Reset to Draft and their
                                                                #    workflows, numbering included
    ~/.hap-venv/bin/python nocoly/build/invoices.py customers   # 5. the three tenant customers, into Contacts
    ~/.hap-venv/bin/python nocoly/build/invoices.py seed        # 6. the three tenant invoices, then verify
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
from datetime import date
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
OPTIONS = {'Type': TYPE_OPTIONS, 'Status': STATUS_OPTIONS, 'Tax mode': TAX_MODE_OPTIONS,
           'Auto-post': AUTO_POST_OPTIONS}
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

# Odoo saas~19.4 view_move_form on HAP's 12-column grid. Odoo's header buttons become Confirm / Cancel / Reset to
# Draft and Status as a read-only field; the h1 Number follows; then Odoo's left column (the partner) beside its
# right column (the dates, the journal and the tax mode); then Odoo's three notebook pages as HAP tabs.
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
    OTHER_INFO: (12, 0, 12, None),
    'Invoice': (13, 0, 12, OTHER_INFO),          # Odoo's <group name="invoice"> heading (divider, type 22)
    NOTE_OTHER: (14, 0, 12, OTHER_INFO),
    'Customer Reference': (15, 0, 6, OTHER_INFO), 'Salesperson': (15, 1, 6, OTHER_INFO),
    'Recipient Bank': (16, 0, 6, OTHER_INFO),     'Payment Reference': (16, 1, 6, OTHER_INFO),
    'Delivery Date': (17, 0, 6, OTHER_INFO),
    'Accounting': (18, 0, 12, OTHER_INFO),       # Odoo's <group name="accounting_info_group"> heading
    'Source Document': (19, 0, 6, OTHER_INFO),   'Auto-post': (19, 1, 6, OTHER_INFO),
    'Auto-post until': (20, 0, 6, OTHER_INFO),
    MYINVOIS: (21, 0, 12, None),
    NOTE_MYINVOIS: (22, 0, 12, MYINVOIS),
}

# What each remark block says, as the HTML the block stores (worksheets/06-invoices.md §1).
HTML = {
    # Rewritten by `taxes.py note` on 18 Sep 2026: 06 wrote this while the lines and the taxes were both still
    # to come, and both of its sentences went false — 07 made three amounts roll-ups and bundle 6 the fourth.
    NOTE_LINES: "<p><strong>Odoo's Invoice Lines tab</strong> holds the product lines — product, label, "
                'quantity, unit, unit price, discount, taxes, subtotal and total — with <em>Add a line</em>, '
                '<em>Add a section</em>, <em>Add a note</em> and the product <em>Catalog</em>, and under them '
                'the totals and the payments already made.</p>'
                '<p><strong>All four amounts are roll-ups of these lines.</strong> Untaxed Amount is the sum '
                'of their Subtotal; <strong>Tax</strong> is the sum of their Total less that, and stopped '
                'being a figure seeded from the tenant when the Taxes bundle arrived; Total and Amount Due '
                'are the sum of their Total. The payments already made, and the tax and payment-term lines '
                "Odoo writes itself, are not built.</p>",
    NOTE_OTHER: "<p><strong>Also on Odoo's Other Info tab:</strong> Sales Team and the marketing fields, a Payment "
                'QR-code, the Incoterm and its location, Fiscal Position, Payment Method, and — on a vendor bill — '
                'the source email and the OCR extraction.</p>'
                '<p>Sales Team comes with the Sales app, the QR-code and Payment Method with the Payments bundle, '
                'and Fiscal Position, Incoterms and Cash Rounding each with their own table.</p>',
    NOTE_MYINVOIS: "<p><strong>MyInvois is Malaysia's e-invoicing clearance.</strong> Odoo's "
                   "<code>l10n_my_edi</code> module puts the document's MyInvois state, its Tax Exemption Reason "
                   'and a Customs Form Reference here, and adds the <em>Send To MyInvois</em>, <em>Request '
                   'Cancel</em> and <em>Reload Data</em> buttons to the header.</p>'
                   '<p>The whole tab comes with the e-invoicing bundle; the tab is kept so the place it belongs is '
                   'already marked.</p>',
}

HINTS = {  # Odoo's placeholders on this form; every other field's placeholder is cleared
    'Invoice Date': 'Today',
    'Payment Terms': 'Payment Terms',
    'Payment Reference': 'Standard communication',
    'Terms and Conditions': 'Terms and Conditions',
}
DESC = {  # Odoo field help, verbatim where Odoo has one (addons/account/models/account_move.py)
    'Number': 'Written by Confirm from the Journal\'s Sequence Prefix and the year of the Accounting Date — '
              'INV/2026/00001. A draft holds the word "Draft" until then, as Odoo shows it.',
    'Type': "One model holds every accounting document; the Type decides which one it is. Odoo's menus — Invoices, "
            'Credit Notes, Bills, Refunds, Journal Entries — are filtered views of this one table.',
    'Status': 'Draft until Confirm posts the document; Cancel makes it Cancelled, Reset to Draft takes it back. '
              "Odoo's header status bar.",
    'Customer / Vendor': 'Odoo labels the one field Customer on a customer document and Vendor on a vendor one; '
                         'HAP cannot rename a field from a rule, so it carries both words.',
    'Delivery Address': 'The delivery address will be used in the computation of the fiscal position.',
    'Invoice Date': 'Odoo labels it Bill Date on a vendor document, where it is required. Confirm fills it with '
                    'today when it is empty.',
    'Accounting Date': 'The date the entry is booked under, and the year the number is taken from.',
    'Due Date': 'Odoo shows the Due Date or the Payment Terms: setting terms computes the date.',
    'Payment Terms': '',                          # Odoo's field has no help; the stand-in's description went with it
    'Journal': 'The book the entry is written in. Its Sequence Prefix is what Confirm numbers the document with, '
               'so it cannot be changed once the document is numbered.',
    'Tax mode': "Whether a line's Amount is its subtotal or its total. Odoo requires it on every invoice, credit "
                'note and receipt: "The document tax mode must be set."',
    'Terms and Conditions': 'Odoo\'s placeholder here is "Terms and Conditions"; HAP never shows a Rich text '
                            "field's placeholder, so it is said here instead.",
    'Untaxed Amount': 'Seeded from the tenant and read-only; 07 Invoice Lines makes it a roll-up of the lines.',
    'Tax': 'Seeded from the tenant and read-only; 07 Invoice Lines makes it a roll-up of the lines.',
    'Total': 'Seeded from the tenant and read-only; 07 Invoice Lines makes it a roll-up of the lines.',
    'Amount Due': 'Seeded from the tenant and read-only; it equals the Total until the Payments bundle can settle '
                  'a document.',
    'Customer Reference': "Odoo shows the same field as Bill Reference in the main group of a vendor document.",
    'Salesperson': '',
    'Recipient Bank': 'A stand-in: Odoo points at a res.partner.bank record, and bank accounts are not in Phase 1. '
                      'Odoo\'s help: "Bank Account Number to which the invoice will be paid. A Company bank account '
                      'if this is a Customer Invoice or Vendor Credit Note, otherwise a Partner bank account '
                      'number."',
    'Payment Reference': 'The payment reference to set on journal items.',
    'Delivery Date': '',
    'Source Document': 'The document(s) that generated the invoice.',
    'Auto-post': 'Specify whether this entry is posted automatically on its accounting date, and any similar '
                 'recurring invoices.',
    'Auto-post until': 'This recurring move will be posted up to and including this date.',
    # The two dividers carry no description: HAP renders a type-22 divider's `desc` nowhere at all.
    'Invoice': '', 'Accounting': '',
}
REQUIRED = {'Type', 'Accounting Date', 'Journal', 'Auto-post'}   # Tax mode and Invoice Date are required by a rule
READONLY = {'Number', 'Status', 'Untaxed Amount', 'Tax', 'Total', 'Amount Due', 'Source Document'}
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
    'Amount Due': {'defsource': C.static_default(0)},
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
                 if c['controlName'] not in PLACE and c['controlId'] not in FIRST_BUILD]
    for name, opts in OPTIONS.items():
        c = next((c for c in ctrls if c['controlName'] == name), None)
        if c:
            live = [(o['key'], o['value']) for o in c.get('options') or [] if not o.get('isDeleted')]
            if live != [(o['key'], o['value']) for o in opts]:
                problems.append(f'{name} options changed: {live}')
    rules = {r['name'] for r in hap.listing('worksheet', 'rules', WORKSHEET)}
    problems += [f'unknown rule {n!r}' for n in rules - set(RULES)]
    buttons = {b['name'] for b in hap.listing('worksheet', 'custom-actions', WORKSHEET)}
    problems += [f'unknown button {n!r}' for n in buttons - set(BUTTONS)]
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
RULE_CLOSED = 'A posted or cancelled document is closed for editing'
RULE_DUE_OR_TERMS = 'Due Date or Payment Terms'                   # bundle 3, Payment Terms
RULE_NO_DUE_ON_ENTRY = 'No due date on a journal entry'           # bundle 3, Payment Terms

CLOSED_FIELDS = ['Type', 'Customer / Vendor', 'Journal', 'Invoice Date', 'Accounting Date', 'Due Date',
                 'Payment Terms', 'Tax mode', LINES]
# LINES is 07's mounted 子表. It joined the list on 16 Sep 2026, at the end of Phase 1: the rule was written
# before Invoice Lines existed, so a posted document still offered *Add a row* where Odoo locks a posted
# move's lines (07's difference 11). A rule item acts on a control, and a 子表 is one.
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
    # <field name="auto_post_until" invisible="auto_post == 'no'"/>
    RULE_AUTO_POST: ('Auto-post', [o['value'] for o in AUTO_POST_OPTIONS if o['value'] != 'No'],
                     ['Auto-post until'], C.SHOW),
    # readonly="state != 'draft'" across the form. 'Payment Terms' is the relation since bundle 3 (the rule named the
    # text stand-in until it was deleted)
    RULE_CLOSED: ('Status', ['Posted', 'Cancelled'], CLOSED_FIELDS, C.READONLY),
    # <field name="invoice_date_due" invisible="invoice_payment_term_id"/>: with a term the date is computed (D)
    RULE_DUE_OR_TERMS: ('Payment Terms', None, ['Due Date'], C.HIDE),
    # <div name="due_date" invisible="move_type not in (…the six invoice and receipt types…)">: neither on an entry
    RULE_NO_DUE_ON_ENTRY: ('Type', ['Journal Entry'], ['Due Date', 'Payment Terms'], C.HIDE),
}


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
    C.upsert_rules(WORKSHEET, rules, 'invoices_rules_pre_rules')
    for r in hap.listing('worksheet', 'rules', WORKSHEET):
        C.remember('rules', KEY + r['name'], r['ruleId'])


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
    n = f'IF({highest} == "", SUM($count-{NUMBER_FX}$, 1), SUM(RIGHT({highest}, 5), 1))'
    fresh = f'CONCAT($prefix-{STRING_FX}$, RIGHT(CONCAT("0000", {n}), 5))'
    return f'IF({held} == "" || {held} == "{DRAFT}", {fresh}, {held})'


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


# ── 5 · the three customers, into Contacts ──────────────────────────────────

CONTACT_FIELDS = {'name': 'Name', 'email': 'Email', 'phone': 'Phone', 'street': 'Street', 'street2': 'Street 2',
                  'city': 'City', 'state': 'State', 'zip': 'ZIP', 'country': 'Country', 'comment': 'Notes'}


def seed_file():
    return json.loads(SEED.read_text(encoding='utf-8'))


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
    got = {k: d.get(k) or '' for k in CONTACT_FIELDS}
    got['type'] = option_label(d.get('type'))
    got['user_id'] = ([x.get('accountId') for x in d.get('user_id') or []] or [''])[0]
    got['active'] = str(d.get('active')) in ('1', 'True', 'true')
    return got


def contact_differences(live, p):
    want = {k: p.get(k) or '' for k in CONTACT_FIELDS}
    want.update(type='Contact', user_id=salesperson_id(), active=True)
    return {k: (live.get(k), v) for k, v in want.items() if live.get(k) != v}


def step_customers():
    """The three companies the tenant's invoices point at, into Contacts — records only. Matched by Name and
    compared field by field, so a second run writes nothing; no field, view, rule or other record in Contacts is
    touched, and the other worksheets' controls are compared by id before and after."""
    before = signatures()
    f = C.fields(CONTACTS)
    cid = lambda n: f[n]['controlId']
    contact = next(o['key'] for o in f['Address Type']['options'] if o['value'] == 'Contact')
    live = contacts_by_name()
    hap.backup('invoices_contacts_pre_customers', {n: r.get('rowid') for n, r in live.items()})
    for p in seed_file()['partners']:
        row = live.get(p['name'])
        if row and not contact_differences(read_contact(row['rowid']), p):
            continue
        values = [{'id': cid(CONTACT_FIELDS[k]), 'value': p[k]} for k in CONTACT_FIELDS if p.get(k)]
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
    """The tenant's three invoices, matched by Customer Reference (SCG-PO-88213, KKD-2026-009, STL-2026-0042).
    Their customers must be in Contacts already — run `customers` first."""
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
    print(f"  3 in the seed file; {bad} missing or differing; {len(extra)} not in it {extra}")
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
    if set(f) != set(PLACE):
        problems.append(f'controls {sorted(set(f) ^ set(PLACE))}')
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
                       'Amount Due': '0'}.items():
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
    for name, (driver, labels, targets, kind) in RULES.items():
        r = rules.get(name)
        if not r:
            problems.append(f'rule {name!r} missing')
            continue
        conds = [g for group in r['filters'] for g in group.get('groupFilters', [])]
        got = (r['type'], r['disabled'], {i['type'] for i in r['ruleItems']},
               [(names.get(c['controlId']), c['filterType']) for c in conds],
               sorted(LABEL.get(driver, {}).get(v) for c in conds for v in c.get('values', [])),
               [names.get(c['controlId']) for i in r['ruleItems'] for c in i['controls']])
        want = (C.INTERACTION, False, {kind}, [(driver, C.NOT_EMPTY if labels is None else C.EQ)],
                sorted(labels or []), targets)
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
        conds = [(names.get(x['controlId']), x['filterType'],
                  sorted(LABEL['Status'].get(y, y) for y in x.get('values') or [])) for x in b.get('filters') or []]
        if conds != [('Status', EQ_SINGLE, sorted(labels))] or (b.get('confirmMsg') or '') != confirm:
            problems.append(f"button {name}: filters={conds} confirm={b.get('confirmMsg')!r}")
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
    print('  check: ' + ('OK — controls, tabs, options, defaults, rules, views, buttons and the numbering '
                         'workflow as specified' if not problems
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
    'show': show,
}

if __name__ == '__main__':
    step = sys.argv[1] if len(sys.argv) > 1 else 'check'
    if step not in STEPS:
        raise SystemExit(f"Unknown step {step!r}; choose from {', '.join(STEPS)}")
    result = STEPS[step](*sys.argv[2:])
    if step in ('verify', 'check', 'all', 'selfcheck') and result:
        sys.exit(1)
