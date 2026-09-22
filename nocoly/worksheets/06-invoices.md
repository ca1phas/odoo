# 06 · Invoices

| | |
|---|---|
| Nocoly app | ERP Master · menu group **Invoicing** |
| Worksheet | Invoices |
| Odoo model | `account.move` |
| Reference | **casimir.odoo.com — Odoo saas~19.4+e**: fields, form, list, kanban, search, the seven window actions, defaults, `_order`, the SQL constraint and all 8 records, extracted read-only to `nocoly/reference/odoo-19.4/account.move.md`. Numbering, which the tenant cannot show from the outside, is read from the Odoo 19.0 source in this repo — `addons/account/models/account_move.py` and `sequence.mixin`. The three seeded documents and their customers were re-read from the tenant on 16 Sep 2026 into `nocoly/data/casimir-invoice-seed.json` |
| Phase | 1 — core worksheet 6 of 7 |
| Status | Skeleton first built by **Teh Li Wei** on 15 Sep 2026 (15 controls, 3 tabs, no rules, buttons or records). Completed against the casimir reference, seeded and self-checked with the hap CLI on 16 Sep 2026 — 32 controls, 5 rules, 3 buttons, 3 views, 3 documents and their 3 customers. **UI-tested the same day: 25 of 25 pass.** The test found one defect (Accounting Date had no default) and one detail to tighten (Confirm dated a Journal Entry); both were fixed and re-checked, and the numbering was then changed to take one past the **highest** number rather than one past a count, which retires a difference (§2). At the end of Phase 1 the same day, 07's **difference 11** was resolved: the Invoice Lines subtable joined the read-only rule, and **test 25** showed a posted document's lines locked — no *Add a row*, no *Batch Operation* (§1). **Bundle 15, 21 Sep 2026** — the four defects the screen-by-screen pass raised (`15-ui-conformance.md` §1) were closed: four more controls joined the read-only rule, *Auto-post until* now follows the tenant's arch rather than the 19.0 repo's, Auto-post is hidden on a receipt, and Odoo's `_check_journal_move_type` arrived as two validation rules over a new **Journal Type** lookup — Odoo's *picker* narrowing could not be built and is recorded as a gap (§2). Tests 12, 13 and the new 26 need a re-run in the browser. **Ready for review** |

`account.move` is one model behind seven menus. A customer invoice, a vendor bill, either kind of credit note, a
receipt and a plain journal entry are all the same record; **Type** decides which, and the menus in Odoo are just
filtered views of the one table. A document starts as a **Draft** with no number, and confirming it posts it and
gives it a number from its **Journal** — INV/2026/00001 on the Sales journal — which is the link back to 05.
The lines that carry the amounts arrive with 07 Invoice Lines.

## 1 · Requirements

### Fields

Labels are Odoo 19.4's; aliases are Odoo's field names on `account.move`. Descriptions are Odoo's own `help`,
verbatim, where Odoo has one. Fields marked *kept* already exist from the first build and keep their control id and
alias.

| # | Field | Odoo field | Nocoly type | Required | Default | Notes |
|---|---|---|---|---|---|---|
| 1 | Number | `name` | Text · **title field** · read-only | — | `Draft` | Written by **Confirm**. Odoo stores `/` on an unnumbered draft and displays "Draft"; here the field literally holds the word until it is posted. Read-only, so it is never typed by hand. Not *No duplicates*: several drafts share the word Draft |
| 2 | Type | `move_type` | Single Select, dropdown | yes | Customer Invoice | **Journal Entry · Customer Invoice · Customer Credit Note · Vendor Bill · Vendor Credit Note · Sales Receipt · Purchase Receipt** — Odoo's `entry`, `out_invoice`, `out_refund`, `in_invoice`, `in_refund`, `out_receipt`, `in_receipt`. Odoo's own default is `entry`; every invoice menu overrides it with `default_move_type`, and this worksheet is the Invoices menu. Quick filter on every view |
| 3 | Status | `state` | Single Select, dropdown · read-only | — | Draft | **Draft · Posted · Cancelled**. Odoo's header status bar; moved only by the three buttons |
| 4 | Customer / Vendor *(kept)* | `partner_id` | Relation → **Contacts**, single | — | — | Odoo renames the one field per type — *Customer* on customer documents, *Vendor* on vendor ones. HAP cannot rename a field from a rule, so it carries both words (§3, differences) |
| 5 | Delivery Address | `partner_shipping_id` | Relation → **Contacts**, single | — | — | Odoo's help: "The delivery address will be used in the computation of the fiscal position." Customer documents only, by rule |
| 6 | Invoice Date *(kept)* | `invoice_date` | Date | by rule | — | Placeholder "Today"; Odoo fills it on confirmation when it is empty, and **Confirm** does the same here. Labelled *Bill Date* and required on vendor documents in Odoo — here the rule requires it and the label stays (§3) |
| 7 | Accounting Date | `date` | Date | yes | today | The date the entry is booked under, and the year the number is taken from. Odoo shows it on vendor documents, and on customer ones only once it differs from the invoice date |
| 8 | Due Date *(kept)* | `invoice_date_due` | Date | — | — | Odoo's "Due Date *or* Payment Terms": setting terms computes the date. The first build's default is removed — Odoo has none. That default was **today**, not "two days from today" as it first read: `staticValue` "2" with `time` "current" is HAP's *current day* sentinel, not a day offset (`BUILDING.md`) |
| 9 | Payment Terms *(kept)* | `invoice_payment_term_id` | Text | — | — | A **stand-in**: plain text holding the Odoo term's name ("30 Days"), described as such on the field, until the Payment Terms table arrives. It was `Payment Terms* (Future Relation)` in the first build. **Replaced in bundle 3 (17 Sep 2026)** by a Relation → Payment Terms with the same name, alias and place; the text control `6aa920d74a73a3142152e68d` was deleted, with the owner's approval, once its three values were in the relation and read back — `10-payment-terms.md` |
| 10 | Journal | `journal_id` | Relation → **Journals**, single | yes | — | Odoo shows it only when several journals suit the type, and defaults it to the first that does; here it is always visible and required, because its Sequence Prefix is what **Confirm** numbers with. Read-only once the document is numbered |
| 11 | Tax mode | `document_tax_mode` | Single Select, dropdown | by rule | Tax Excluded | **Tax Excluded · Tax Included** — Odoo's `tax_excluded`, `tax_included`; decides whether a line's Amount is its subtotal or its total. Odoo's SQL constraint `account_move_check_document_tax_mode_set` requires it on every invoice, credit note and receipt — "The document tax mode must be set." — so a rule requires it for every type but Journal Entry |
| 12 | Terms and Conditions | `narration` | Rich text | — | — | Tab **Invoice Lines**, under where the lines will be. Placeholder "Terms and Conditions" |
| 13 | Untaxed Amount | `amount_untaxed` | Number, 2 decimals · read-only | — | 0 | Tab **Invoice Lines**. Seeded from the tenant and read-only; 07 Invoice Lines makes it a roll-up of the lines |
| 14 | Tax | `amount_tax` | Number, 2 decimals · read-only | — | 0 | Same |
| 15 | Total | `amount_total` | Number, 2 decimals · read-only | — | 0 | Same |
| 16 | Amount Due | `amount_residual` | Number, 2 decimals · read-only | — | 0 | Same. Equal to Total until the Payments bundle can settle a document |
| 17 | Customer Reference *(kept)* | `ref` | Text | — | — | Tab **Other Info**. Odoo shows the same field as *Bill Reference* in the main group of a vendor document |
| 18 | Salesperson *(kept)* | `invoice_user_id` | Member | — | — | Tab **Other Info**. Odoo's `res.users`; HAP members are the app's users |
| 19 | Recipient Bank *(kept)* | `partner_bank_id` | Text | — | — | Tab **Other Info**. A **stand-in**, described as such: Odoo points at a `res.partner.bank` record, and bank accounts are not in Phase 1. It was `Recipient Bank (Relation in Odoo)` |
| 20 | Payment Reference *(kept)* | `payment_reference` | Text | — | — | Tab **Other Info**. Odoo's help: "The payment reference to set on journal items." Placeholder "Standard communication". **Confirm** fills it with the Number on a customer document, which is what the tenant's posted invoice shows |
| 21 | Delivery Date *(kept)* | `delivery_date` | Date | — | — | Tab **Other Info** |
| 22 | Source Document | `invoice_origin` | Text · read-only | — | — | Tab **Other Info**, group Accounting. The sales order the document came from (S00011). Read-only, as in Odoo, and seeded; nothing in Phase 1 writes it |
| 23 | Auto-post | `auto_post` | Single Select, dropdown | yes | No | Tab **Other Info**, group Accounting. **No · At Date · Monthly · Quarterly · Yearly** — Odoo's `no`, `at_date`, `monthly`, `quarterly`, `yearly` |
| 24 | Auto-post until | `auto_post_until` | Date | — | — | Same group. Shown only when Auto-post is **Monthly, Quarterly or Yearly**, by rule — the tenant hides it for *At Date* as well as *No* |
| 25 | Journal Type | *(none — Odoo reads `journal_id.type`)* | Stored lookup → Journals' Type, read through **Journal** · read-only | — | — | Tab **Other Info**, beside Auto-post until. **Not an Odoo field.** Added 21 Sep 2026 so the two journal checks have something on this worksheet to compare: a HAP rule condition can only name a control of its own worksheet. It stores the source dropdown's option key, as Invoice Lines' Status lookup does, and populated on all 36 live documents the moment it was saved. Alias `journal_type`, which is not an Odoo field name — the house convention has nothing to offer for a control Odoo does not have |

**Added since by bundles:** **Payment Terms** (`invoice_payment_term_id`) is a relation to Payment Terms in place of the text stand-in (row 9 above), beside Due Date, locked by the posted-or-cancelled rule; two rules — *Due Date or Payment Terms* (Due Date hidden while a term is set) and *No due date on a journal entry* (Due Date and Payment Terms hidden); automation **C** (a customer or vendor document takes the contact's Customer or Vendor Payment Terms, a journal entry none) and automation **D** (the Due Date follows the term's lines), and **Confirm** dates the invoice after it fills an empty Invoice Date — bundle 3, `10-payment-terms.md`.

`account.move` has **no `active` field** — a document is cancelled, never archived — so this is the first worksheet
in the app with no Active checkbox and no Archive / Unarchive buttons. Say so in §2 rather than leaving a reviewer
to wonder.

Six controls hold no data: the three tabs kept from the first build, the two dividers inside Other Info
(*Invoice*, *Accounting*), and the remark blocks. The first build left an empty remark block (type 10010) under the
*Invoice* divider; fill it, and add one to **Invoice Lines** and one to **MyInvois** the way 05 Journals did — a
divider for the heading, a remark block for the text, because a divider renders its description nowhere
(`BUILDING.md`).

As the three blocks render:

> **The lines arrive with 07 Invoice Lines.** Odoo's Invoice Lines tab holds the product lines — product, label,
> quantity, unit, unit price, taxes and subtotal — with *Add a line*, *Add a section*, *Add a note* and the product
> *Catalog*, and under them the totals and the payments already made.
>
> Until then, Untaxed Amount, Tax, Total and Amount Due are read-only figures seeded from the tenant; 07 turns them
> into roll-ups of the lines. Taxes themselves need the Taxes bundle.

> **Also on Odoo's Other Info tab:** Sales Team and the marketing fields, a Payment QR-code, the Incoterm and its
> location, Fiscal Position, Payment Method, and — on a vendor bill — the source email and the OCR extraction.
>
> Sales Team comes with the Sales app, the QR-code and Payment Method with the Payments bundle, and Fiscal
> Position, Incoterms and Cash Rounding each with their own table.

> **MyInvois is Malaysia's e-invoicing clearance.** Odoo's `l10n_my_edi` module puts the document's MyInvois state,
> its Tax Exemption Reason and a Customs Form Reference here, and adds the *Send To MyInvois*, *Request Cancel* and
> *Reload Data* buttons to the header.
>
> The whole tab comes with the e-invoicing bundle; the tab is kept so the place it belongs is already marked.

**Replaced on 22 Sep 2026** for the app's users: each block now says what that part of the form is for. The
texts above, and the Invoice Lines text `taxes.py note` wrote on 18 Sep 2026, are kept at the foot of this file.

### Form layout

| Odoo 19.4 (`view_move_form`) | Nocoly |
|---|---|
| Header: Confirm · Send · Print · Pay · Preview · Credit Note · Cancel · Reset to Draft · Lock · MyInvois buttons; status bar Draft → Posted (Cancelled) | Three buttons — **Confirm · Cancel · Reset to Draft** — and Status as a read-only field |
| Alerts (duplicate, outstanding credits, sale warning), ribbons (Paid, Sent, Reversed …), smart buttons (Payments, Journal Items, Reversals …) | — none; they need payments, reversals and lines (Not built now) |
| Type selector (invoice / receipt, drafts only) | **Type**, a plain dropdown covering all seven types |
| h1: Number, or "Draft" | **Number**, read-only, holding *Draft* until Confirm |
| Left: Customer \| Vendor · Delivery Address · Bill Reference · Auto-Complete | **Customer / Vendor** · **Delivery Address** (customer documents) |
| Right: Invoice Date \| Bill Date · Accounting Date · Payment Reference · Recipient Bank · Due Date "or" Payment Terms · Journal · Tax Excl./Incl. | **Invoice Date** · **Accounting Date** · **Due Date** \| **Payment Terms** · **Journal** · **Tax mode**. Payment Reference and Recipient Bank stay on Other Info, where Odoo puts them for customer documents |
| Tab *Invoice Lines*: the lines, Terms and Conditions, the totals, payments and Amount Due | **Tab Invoice Lines**: the remark block, **Terms and Conditions**, then **Untaxed Amount · Tax · Total · Amount Due** |
| Tab *Other Info* › groups Invoice, Accounting, Extraction, Marketing | **Tab Other Info**: divider *Invoice* + remark block, then Customer Reference · Salesperson · Recipient Bank · Payment Reference · Delivery Date; divider *Accounting*, then Source Document · Auto-post · Auto-post until |
| Tab *MyInvois* | **Tab MyInvois**: the remark block |
| Chatter | HAP's own discussion |

### Rules

A HAP rule applies its action while its condition holds and the opposite when it fails, so a *show* rule hides its
field on a new record whose Type is still empty — which is what Odoo's `invisible` does — and that is the way round
to write them.

| Rule | When | Effect | Odoo source |
|---|---|---|---|
| Delivery Address is for customer documents | Type is Customer Invoice, Customer Credit Note or Sales Receipt | show **Delivery Address** | `<field name="partner_shipping_id" invisible="not is_sale_document(True)"/>` |
| A vendor document must carry its date | Type is Vendor Bill, Vendor Credit Note or Purchase Receipt | **require** **Invoice Date** | `required="is_purchase_document(True)"` on `invoice_date` (labelled Bill Date) |
| Every document but an entry has a tax mode | Type is not Journal Entry | **require** **Tax mode** | SQL `account_move_check_document_tax_mode_set` |
| Auto-post until follows Auto-post | Auto-post is **Monthly, Quarterly or Yearly** | show **Auto-post until** | **the tenant's** `invisible="auto_post in ('no', 'at_date')"` — see the note under this table |
| Auto-post is not offered on a receipt | Type is Sales Receipt or Purchase Receipt | **hide** **Auto-post** | the tenant's `invisible="move_type in ('out_receipt', 'in_receipt')"` on `auto_post` |
| A posted or cancelled document is closed for editing | Status is Posted or Cancelled | make **Type · Customer/Vendor · Journal · Invoice Date · Accounting Date · Due Date · Payment Terms · Tax mode · Lines · Delivery Address · Delivery Date · Auto-post · Auto-post until** read-only | `readonly="state != 'draft'"` across the form; `journal_id` is read-only once numbered; a posted move's `line_ids` are locked |
| **A sale document must be in a sale journal** *(validation)* | Type is Customer Invoice, Customer Credit Note or Sales Receipt **and** Journal Type is filled **and** Journal Type is not *Sales* | error on **Journal**: *"Cannot create a sale document in a non sale journal"* | `@api.constrains('journal_id', 'move_type') _check_journal_move_type` |
| **A purchase document must be in a purchase journal** *(validation)* | Type is Vendor Bill, Vendor Credit Note or Purchase Receipt **and** Journal Type is filled **and** Journal Type is not *Purchase* | error on **Journal**: *"Cannot create a purchase document in a non purchase journal"* | the same constraint's other half |

**The last four rules changed or arrived on 21 Sep 2026**, from the screen-by-screen pass in `15-ui-conformance.md`
§1. Three things a reviewer should know about them.

*Auto-post until.* This table used to quote `invisible="auto_post == 'no'"` and the rule showed the field for every
value but *No*. That quote is the **19.0 repo checkout at `7bbce824`**, not the tenant: casimir (saas~19.4) carries
`invisible="auto_post in ('no', 'at_date')" readonly="state != 'draft'"`, so *At Date* hides it too — a document
posted on one date needs no "until". Same repo-behind-tenant trap as the Taxes form and the CRM feature groups.

*Auto-post on a receipt.* The tenant also carries `invisible="move_type in ('out_receipt', 'in_receipt')"` on
`auto_post`. The rule is written *hide · equals*, not *show · equals*, so Auto-post is visible from the start on a
document whose Type is still empty. **Auto-post stays required on the control** even though a rule can hide it —
normally a mistake (`BUILDING.md`: a field a rule hides must not be required) — because it carries the default
**No**, so a receipt is always saved with the field filled.

*The two journal checks* are Odoo's `_check_journal_move_type`, with its two messages verbatim. They are not the
picker narrowing Odoo also has; that could not be built — see §2 *Found while building*.

The last rule depends on HAP offering a read-only action on interaction rules. **Check it before building**: if
there is none, leave the rule out, record it in §2 *Found while building* and in the differences, and do not fake it
with a hide rule — a hidden field is worse than an editable one here.

**Lines — the mounted Invoice Lines subtable — joined that list on 16 Sep 2026**, at the end of Phase 1. The rule
was written before 07 mounted the 子表, so a posted document still offered *Add a row* where Odoo locks a posted
move's lines; 07 recorded it as its difference 11 and left it to the owner because it touches 06's rule. The
control (`6aaa2baae43d174ab3749de9`) is now the rule's ninth target and HAP stored it like any other.

**It works — a HAP read-only rule hides a 子表's row controls.** Test 25, in the browser: on the posted
**INV/2026/00001** the Invoice Lines table shows **no *Add a row* and no *Batch Operation***, and the Display
Type column has lost its required asterisk; on the **Sunway Construction Group draft** both controls are there
and the table is fully editable. So a posted document's lines are closed, as in Odoo, and **07's difference 11
is resolved**.

Nothing is validated on save. Odoo's own guards on this model are the tax-mode constraint above, which the rule
covers, and the numbering uniqueness that **Confirm** produces by construction.

### Buttons

| Button | Shown when | Does | Confirmation |
|---|---|---|---|
| **Confirm** | Status is Draft | Status → **Posted**; assigns the **Number**; fills **Invoice Date** with today when it is empty; fills **Payment Reference** with the new Number on a customer document when it is empty | none — Odoo posts straight away |
| **Cancel** | Status is Draft | Status → **Cancelled** | "Are you sure you want to cancel this document?" · Cancel document / Back |
| **Reset to Draft** | Status is Posted or Cancelled | Status → **Draft**, **keeping the Number** — Odoo does not give it back | none |

**Numbering, which Confirm has to reproduce** (`sequence.mixin`, and the tenant's own INV/2026/00001):

```
prefix = the Journal's Sequence Prefix                     e.g. INV
       = "R" + prefix   for a Customer or Vendor Credit Note whose Journal
                        has Dedicated Credit Note Sequence checked         e.g. RINV
year   = the year of the Accounting Date                                   2026
n      = 1 + how many documents already hold a Number starting "<prefix>/<year>/"
Number = "<prefix>/<year>/<n padded to 5 digits>"                          INV/2026/00001
```

so the second Sales invoice of 2026 becomes INV/2026/00002, a credit note off the same journal RINV/2026/00001, and
a bill BILL/2026/00001. Two people confirming at the same instant could collide; note it rather than build locking.

### Views

| View | Type | Shows | Odoo 19.4 |
|---|---|---|---|
| Invoices — opens first | table | Type is Customer Invoice, Customer Credit Note or Sales Receipt. Columns **Number · Customer/Vendor · Invoice Date · Due Date · Journal · Untaxed Amount · Total · Amount Due · Status**, sorted **Accounting Date descending, then Number descending**. Quick filters Type and Status | The *Invoices* and *Credit Notes* actions — `move_type in (out_invoice, out_refund, out_receipt)` — and the list's visible columns |
| Bills | table | The three vendor types, the same columns and sort | The *Bills* and *Refunds* actions |
| Journal Entries | table | Type is Journal Entry. Columns **Number · Accounting Date · Journal · Total · Status** | The Accounting *Entries* action |

`_order` is `date desc, name desc, invoice_date desc, id desc`; HAP sorts on the first two. Odoo's Draft / Posted /
Cancelled and Invoices / Receipts / Credit Notes search filters become the two quick filters. Odoo's kanban, pivot,
graph and activity views are not reproduced.

### Not built now, and why

| Odoo 19.4 field / feature | Why not now |
|---|---|
| Invoice Lines and Journal Items (`invoice_line_ids`, `line_ids`), *Add a line / section / note*, the Catalog | **07 Invoice Lines** (`account.move.line`), the next worksheet. The tab and its remark block are already here |
| Taxes on those lines, and so real Untaxed Amount / Tax / Total | The **Taxes** bundle. The four amounts are seeded read-only figures until 07 |
| ~~Payment Terms (`invoice_payment_term_id`) as a relation~~ | **Built on 17 Sep 2026 by the Payment Terms bundle** (`worksheets/10-payment-terms.md`): the relation replaced the text stand-in, and the Due Date is computed from the term |
| Recipient Bank (`partner_bank_id`) as a relation | `res.partner.bank` records; a text stand-in again |
| Payments — *Pay*, Payment Status (`payment_state`), the Payments and Reversals smart buttons, outstanding credits, `matched_payment_ids` | The **Payments** bundle. Amount Due therefore equals Total, and no document can be marked paid |
| **Credit Note** (`action_reverse`), Reversal of / Reversal Move (`reversed_entry_id`, `reversal_move_ids`) | Reversing copies the lines with the sign flipped, so it needs 07. The Type options for both credit notes are already here |
| *Send*, *Print*, *Preview*, Sent (`is_move_sent`, `move_sent_values`), the invoice PDF (`invoice_pdf_report_*`), UBL/CII (`ubl_cii_xml_*`) | Reports and outgoing mail; nothing here renders a PDF |
| Currency (`currency_id`) | Currencies bundle; one currency (MYR) per app copy, and Odoo hides the field on a single-currency database |
| Commercial Entity (`commercial_partner_id`) | Odoo computes it from the partner's parent; a lookup could do it, but nothing in Phase 1 reads it |
| Fiscal Position, Incoterm and its location, Cash Rounding, Payment Method, Ledger | Each is its own table and its own bundle |
| Sales Team (`team_id`), the UTM fields, Source Document being written | The **Sales** app — out of Phase 1 by the owner's direction. Source Document is kept read-only so the seeded S00011 stays visible |
| MyInvois state, Tax Exemption Reason, Customs Form Reference (`l10n_my_edi_*`) and the three MyInvois buttons | The **e-invoicing** bundle; the tab and its remark block mark the place |
| Auto-Complete (`invoice_vendor_bill_id`), quick edit (`quick_edit_mode`, `quick_edit_total_amount`), OCR (`extract_*`), To Review (`review_state`), Last Reminder (`account_followup`), deferred entries and the signature (`account_accountant`) | Each needs a module or a flow that is not in Phase 1 |
| Lock / hash (`restrict_mode_hash_table`, `inalterable_hash`, `secure_sequence_number`) and Odoo's refusal to change a journal's hashing once it has entries — the note left open in 05 | Hashing a chain of posted entries is its own piece of work; 05's Archive check ("you cannot archive a journal containing draft journal entries") can be added now that drafts exist, and is tracked as a follow-up on 05, not built here |
| Duplicate and abnormal-amount warnings (`duplicated_ref_ids`, `abnormal_*_warning`, `alerts`), the partner credit warning | They are onchange-time alerts with no HAP equivalent |
| Company (`company_id`) | One company per app copy (Direction, 15 Sep) |
| ~~Roles~~ | **Set on 16 Sep 2026** for the whole app, at the end of Phase 1: five stock roles renamed to English and four business roles, one per Odoo accounting group, each with a rule for this worksheet. The table is in `REVIEWING.md` › *Phase 1 · Roles* |

### Records

The tenant's three genuine customer invoices, seeded from `data/casimir-invoice-seed.json`, and — **added on
21 Sep 2026** — two more read off the tenant that day and held in `invoices.py`'s own `EXTRA_MOVES`. Of the
tenant's records 4–8, originally all passed over as demo and test traffic, two turned out to be worth having:
between them they exercise three things the first three do not — **two different tax rates on one document**, a
**Section** line, and **negative** lines. The empty draft and the payment entry are still not seeded.

| Number | Type | Status | Customer | Invoice Date | Accounting Date | Due Date | Terms | Journal | Reference | Source | Untaxed | Tax | Total |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Draft | Customer Invoice | Draft | Sunway Construction Group | — | 2026-09-09 | 2026-10-09 | 30 Days | Sales | SCG-PO-88213 | S00011 | 104,603.20 | 10,460.32 | 115,063.52 |
| INV/2026/00001 | Customer Invoice | Posted | Klinik Kesihatan Damansara | 2026-09-11 | 2026-09-11 | 2026-10-02 | 21 Days | Sales | KKD-2026-009 | S00014 | 11,432.00 | 1,143.20 | 12,575.20 |
| Draft | Customer Invoice | Draft | Sarawak Timber Logistics | — | 2026-09-14 | 2026-10-29 | 45 Days | Sales | STL-2026-0042 | S00016 | 180,000.00 | 14,400.00 | 194,400.00 |
| **INV/2026/00002** | Customer Invoice | **Posted** | Casimir | 2026-09-14 | 2026-09-14 | 2026-09-14 | — | Sales | TEST demo run - delete me | — | 2,768.00 | **259.80** | 3,027.80 |
| **Draft** | Customer Invoice | **Cancelled** | Casimir | — | 2026-09-14 | 2026-09-14 | — | Sales | S00021 | — | 1,087.60 | **113.86** | 1,201.46 |

All five are Tax Excluded, Auto-post *No*, Salesperson Casimir and Amount Due equal to Total; INV/2026/00001
carries its own number as the Payment Reference. The last two have **no payment term**, which is why their Due
Date is the only date of their own they carry, and the cancelled one was never numbered, so its Number is the
word *Draft*.

**Three fields of those two were not in the tenant reading, and none is invented quietly.** Accounting Date is
required here, so both take 2026-09-14, the day their other dates carry and the day Odoo's `_post` would book
the first under; Delivery Address is Odoo's own default, the customer itself; and **Payment Reference is left
empty on both** — even on the posted one, where our own Confirm would have written the number — rather than
guessed. The tenant's own `odoo_id` for neither was read, so neither carries one.

**Amount Due on INV/2026/00002 is a difference, not a defect.** The tenant shows it `paid`, with Amount Due
0.00 against a total of 3,027.80. The roll-up writes Amount Due = Σ Total unconditionally, because there is no
Payments model until that bundle, so the seeded record reads **3,027.80**. It is *not* hand-written to force a
match; the tenant's own figure is kept beside it in `EXTRA_MOVES` as `amount_residual_tenant`.

**Their customers go into Contacts first.** Contacts held only `TEST …` records, so the three companies are
seeded there from the same file — name, Address Type *Contact*, email, phone, street, city, ZIP,
salesperson and the tenant's own note — and **Casimir**, the tenant's own contact, is created beside them with
its name alone, since the two documents above carry nothing else of it. They are real records, not `TEST …`. The
tenant's `res.partner` has no `company_registry` and no `duns` field, so Contacts' Company ID and DUNS stay empty
on them. **Nothing else in Contacts may be touched** — no field, no view, no rule; records only.

**State and Country are no longer seeded here** (found 21 Sep 2026). Bundle 11 (Countries) and bundle 12 (States)
turned those two Contacts controls into **Relations**, and a text write into a Relation is accepted and stores
nothing — so from bundle 12 on, `customers` found a difference on every run, re-wrote the same three records and
then failed its own read-back. `seedable_contact_fields()` now leaves out any seed field whose Contacts control
is a Relation, and says so when it runs. The three customers' State and Country values are still in the seed
file and the three records still read empty: **linking a contact to its country and state is bundles 11 and 12's
work, and has not been done for them.** One for the owner.

## 2 · Build

Built by `nocoly/build/invoices.py` — steps `layout → rules → views → buttons → customers → seed`, or `all` for
every one of them followed by `check`. Each step reads the live worksheet first, refuses to run unless the profile
reaches ERP Master › Invoicing › Invoices and the worksheet holds only Teh Li Wei's skeleton plus this script's own
work, reads back what it wrote, and is safe to re-run: a second `all` created, added, renamed and updated nothing
and re-published no workflow. Helpers: `check` reads controls, their tabs, options, defaults, rules, views, buttons
and the numbering chain back against the spec, `verify` compares every document with the seed file, `numbering`
rebuilds just the Confirm chain, `selfcheck` confirms five TEST drafts and reads the numbers back, `order` prints
each view's records in the view's own order, `document "<Number>"` one document's stored values, `untouched` the
other five worksheets' control count and digest, and `show` the control list. The profile comes from `$HAP_PROFILE`
and otherwise from hap-cli's active profile; **nothing in `common.py` changed**.

| Element | Built | Id |
|---|---|---|
| App | ERP Master | `6cb4d051-a33c-4bf9-b56f-5f47f0e85dc9` |
| Menu group | Invoicing — Journals, Invoices | `6aa8f3ecbf00c316381dbbe8` |
| Worksheet | Invoices, alias **`account_move`** (was `invoices`) | `6aa90facf363582dd37a62f7` |
| Controls | **34**: the 25 fields (Payment Terms became a relation in bundle 3 and Journal Type arrived in bundle 15), the mounted Lines subtable, 3 tabs, 2 divider headings and 3 remark blocks | — |
| Kept from the skeleton, fields | Customer / Vendor · Invoice Date · Due Date · Payment Terms · Customer Reference · Salesperson · Recipient Bank · Payment Reference · Delivery Date | `6aa920d74a73a3142152e689` · `…68b` · `…68c` · `…68d` · `…692` · `…693` · `…694` · `…695` · `…696` |
| Kept from the skeleton, structure | Tabs Invoice Lines · Other Info · MyInvois; dividers Invoice · Accounting; remark block *Invoice note* | `…68e` · `…68f` · `…698`; `…690` · `…697`; `…691` |
| Added, fields | Number · Type · Status | `6aa9f847e54d2a34fa4dfeed` · `…eee` · `…eef` |
| | Accounting Date · Tax mode · Terms and Conditions | `6aa9f847e54d2a34fa4dfef0` · `…ef1` · `…ef2` |
| | Untaxed Amount · Tax · Total · Amount Due | `6aa9f847e54d2a34fa4dfef3` · `…ef4` · `…ef5` · `…ef6` |
| | Source Document · Auto-post · Auto-post until | `6aa9f847e54d2a34fa4dfef7` · `…ef8` · `…ef9` |
| Added, relations (one-way) | Delivery Address → Contacts · Journal → Journals | `6aa9f848805aef703286517a` · `6aa9f848805aef703286517c` |
| Added, remark blocks (type 10010, HTML) | Invoice Lines note · MyInvois note | `6aa9f846e54d2a34fa4dfedc` · `6aa9f846e54d2a34fa4dfedd` |
| Rules | Delivery Address is for customer documents · A vendor document must carry its date · Every document but an entry has a tax mode · Auto-post until follows Auto-post · A posted or cancelled document is closed for editing | `6aa9f86de54d2a34fa4dff23` · `6aa9f86d805aef7032865182` · `6aa9f86e7d58b0f44930e8b1` · `6aa9f86fe54d2a34fa4dff25` · `6aa9f86f805aef7032865184` |
| Rules, bundle 15 (21 Sep 2026) | Auto-post is not offered on a receipt *(interaction)* · A sale document must be in a sale journal · A purchase document must be in a purchase journal *(both validation, check type 1)* | `6ab0a730805aef703286d1c1` · `6ab0aa83805aef703286d2da` · `6ab0aa847d58b0f449316788` |
| Controls, bundle 15 | **Journal Type**, a stored lookup of Journals' Type through the Journal relation, read-only, on Other Info | `6ab0aa1de54d2a34fa4e7c07` |
| Views | Invoices (the skeleton's own view, renamed from *All*) · Bills · Journal Entries | `6aa90facf363582dd37a62fb` · `6aa9f87d7d58b0f44930e8b5` · `6aa9f87e7d58b0f44930e8b7` |
| Buttons | Confirm · Cancel · Reset to Draft | `6aa9f89be43d174ab3749b55` · `6aa9f990bd43f55762c6f603` · `6aa9f993805aef7032865196` |
| Button workflows | Confirm (the numbering: a search, two formulas, a count, three updates and two branches) · Cancel · Reset to Draft, one update step each — all published | `6aa9f89b4f2a99acac043704` · `6aa9f99016473257ad4d3bc6` · `6aa9f9938e75db182e78a8b3` |
| Records | the **5** tenant invoices, their **4** customers in Contacts, and 5 `TEST-SEQ-…` documents (§3) | — |
| | bundle 7's two, added 21 Sep 2026 — INV/2026/00002 · the cancelled S00021 | `80aad832-11c4-4db5-b3e9-5bafe19440bd` · `29369e7c-b89b-4b20-95c8-bc31651a0e1a` |
| | their customer, **Casimir**, in Contacts | `f16e2722-576e-4975-9b09-e0882622e61a` |

Every id is in `nocoly/build/ids.json` under "Invoices: …" keys, the seeded rows in a new `records` section; no
existing key was renamed. `worksheets` gained the key "Invoices".

**Bundle 7 (21 Sep 2026) added records and nothing else.** Two more of the tenant's documents and their
customer; no control, rule, view, button, workflow or view column changed, and `check` reads back exactly what
it did before. The two documents' data lives in `invoices.py`'s own `EXTRA_MOVES` and `EXTRA_PARTNERS` rather
than in `data/casimir-invoice-seed.json`, which stays as the 15 Sep extract; `seed_file()` appends them, keyed
by Customer Reference and by Name, so `customers`, `seed` and `verify` read all five documents without knowing
the difference. Their six lines are 07's, and what they proved is in 07 §2 › *Bundle 7*. The one change to an
existing step is `seedable_contact_fields()` (§1 › Records) — the fix for `customers` re-writing the same three
contacts on every run since bundle 12.

**`account.move` has no `active` field.** A document is cancelled, never archived, so Invoices is the first
worksheet in ERP Master with **no Active checkbox, no Archived view and no Archive / Unarchive buttons** — its
three buttons move Status instead. Nothing here is hidden from a view by an archive flag; the three views divide
the one table by Type, the way Odoo's seven menus do.

**History.** **Teh Li Wei built the skeleton on 15 Sep 2026** — the worksheet and its `invoices` alias, three tabs
(Invoice Lines, Other Info, MyInvois), two divider headings inside Other Info (Invoice, Accounting), an empty
remark block under the first of them, and nine fields with their ids: a Customer relation to Contacts, Invoice
Date (which he made the title field), Due Date, `Payment Terms* (Future Relation)`, Customer Reference,
Salesperson, `Recipient Bank (Relation in Odoo)`, Payment Reference and Delivery Date. No rules, buttons, records,
aliases or views but the stock *All*. That skeleton is the base of everything here; the owner then asked us to
finish the worksheet against casimir. What changed on 16 Sep 2026, and why:

| Change | Why |
|---|---|
| **Fifteen fields added** — Number, Type, Status, Delivery Address, Accounting Date, Journal, Tax mode, Terms and Conditions, Untaxed Amount, Tax, Total, Amount Due, Source Document, Auto-post, Auto-post until | §1's field table: without Type the seven Odoo menus cannot be told apart, without Journal and Number nothing can be posted, and without the four amounts the tenant's figures have nowhere to live |
| Three controls renamed: **Customer → Customer / Vendor**, **Payment Terms\* (Future Relation) → Payment Terms**, **Recipient Bank (Relation in Odoo) → Recipient Bank**; both stand-in markers moved into the field's description | Odoo renames the one `partner_id` field per document type, so the label has to carry both words; a label is not the place for a build note, and a reviewer comparing Odoo side by side should read Odoo's own label |
| The empty remark block renamed **Invoice → Invoice note** and filled with its HTML, `hidetitle` "1", width 12 | It shared its name with the divider above it, which makes any name-keyed lookup ambiguous; a remark block's `controlName` is an internal label once `hidetitle` is "1", so the rename is invisible in the UI |
| **Number is the title field**, read-only, default "Draft"; Invoice Date is no longer the title | Odoo's h1 is the number, and a HAP record's title is what every picker, card and relation shows. An invoice picked on a line must read INV/2026/00001, not a date |
| **Two remark blocks added**, in Invoice Lines and MyInvois | §1's three blocks; the Other Info one already existed and was filled |
| Odoo's help, verbatim where Odoo has one (Delivery Address, Payment Reference, Source Document, Auto-post, Auto-post until, Recipient Bank); a written explanation where it has none | A reviewer can compare them with Odoo's tooltips |
| Placeholders **Today** (Invoice Date, the skeleton's own), **Standard communication** (Payment Reference) and **Terms and Conditions**; every invented placeholder cleared ("Please fill in the text content", "Please select date", "Please select a member") | Odoo's own placeholders are the three kept; the rest are HAP's defaults, which say nothing |
| Due Date's default removed — and it was **today**, not "two days from today": `staticValue` "2" is HAP's sentinel for the current day, not an offset (below) | Odoo has no default on `invoice_date_due`; the date comes from the payment terms |
| **Accounting Date defaults to today** — the one defect the UI test found, fixed the same day | §1 asks for it. The first cut wrote `staticValue` "" with `time` "current", which HAP stores happily and applies to nothing; the field came up empty on the create form |
| Five interaction rules, three buttons with their workflows, three views, three customers and three documents | The skeleton had none — 0 rules, 0 buttons, 0 records, one stock view |
| The worksheet alias `invoices` → **`account_move`** | `BUILDING.md`: a worksheet's alias is its Odoo model with underscores, as on all five worksheets before it. The worksheet had no records and nothing referenced the alias |

### Decisions taken while building

| Decision | Why |
|---|---|
| **The Invoice Lines and MyInvois tabs get a remark block and no divider**, unlike Journals' two tabs | §1's form-layout table names a divider only inside Other Info (*Invoice*, *Accounting* — Odoo's own group headings) and says "the remark block" for the other two tabs. Each block already opens with its own bold lead-in, so a divider would repeat it. Adding a divider later costs one save; removing one needs the owner's approval |
| **The nine skeleton controls are given Odoo's field names as aliases** (`partner_id`, `invoice_date`, …) although §1 says a kept field keeps its alias | They had no alias at all — every one was empty — so there was nothing to keep, and `record get` now reads the whole worksheet in Odoo's vocabulary, which is what the seed and verify steps compare on |
| **Confirm writes Number and Status in one update step**, and two branches after it fill the Invoice Date and the Payment Reference | One write for the two fields that must change together; the two fill-ins are conditional, and a HAP field patch has no "only if empty" |
| **The number is one past the highest already issued, not one past a count** — a search step sorted on Number descending, limited to one record, filtered on the same prefix | §1 specifies the count. The count breaks the moment a number is freed: the UI test's Reset-to-Draft left INV/2026/00002 unused, and the next count-based Confirm would have re-issued INV/2026/00005, which a record already held. Reading the highest survives gaps, deletions and resets, and needs no new field |
| **Confirm assigns a Number only when the document has none** — empty or the word "Draft" — and otherwise leaves the one it has | Odoo `_post` sequences a move only when `name` is unset, and `button_draft` keeps the name, so a reset document takes its old number back on the next post. It also stops us making new gaps, and removes the stale-Payment-Reference oddity: the number never changes, so the reference never goes stale |
| **The numbering still does not reserve.** Two people confirming in the same second read the same highest number and produce the same next one | Odoo's `sequence.mixin` takes a row lock; HAP has no equivalent through the CLI. The Number is deliberately **not** *No duplicates* — several drafts share the word "Draft" — so a collision would be stored, not refused. It is a race on the highest number now rather than on a count, which is a narrower window but not a closed one |
| **Reset to Draft keeps the Number**, and so does Cancel | Odoo does not give a number back; the gap would be worse than the reuse |
| The Confirm chain reads the journal with a **search on Journals** (Record ID equals the trigger's Journal) rather than a *get related record* step | `BUILDING.md`: a get-related-record step cannot start from a button's trigger record |
| ~~**Invoice Date is filled on a Journal Entry too**~~ — **changed after the UI test**: the branch now reads *An invoice or receipt with no date?*, Type is any of the six non-entry types **and** Invoice Date empty | §1's button table has no type condition, but Odoo's `_post` dates `is_invoice(include_receipts=True)` only. One extra condition on a branch path that already existed, so it was a clean change; TEST-SEQ-6, a Journal Entry confirmed afterwards, comes back with **no** Invoice Date |

### Both of §1's conditional pieces could be built

- **A HAP interaction rule does have a read-only action** — rule item **type 4**, one of six (1 show · 2 hide ·
  4 read-only · 5 required · 6 error message · 7 whole record read-only). *A posted or cancelled document is closed
  for editing* is built as written: one rule, condition Status is Posted or Cancelled, acting on Type,
  Customer / Vendor, Journal, Invoice Date, Accounting Date, Due Date, Payment Terms and Tax mode. It reads back
  with type 4 and all eight controls. Nothing was faked with a hide rule. Like every interaction rule it is
  browser-side only: the API still writes a posted document, which is how the self-check puts a TEST document back
  to a draft. **Test 12 is where it is proved.**

  **A ninth control joined that rule on 16 Sep 2026**, at the end of Phase 1: **Lines**
  (`6aaa2baae43d174ab3749de9`), 07's mounted Invoice Lines 子表 (control type 34). The rule predates the mount,
  so a posted document still offered *Add a row* where Odoo locks a posted move's lines — 07's difference 11,
  left to the owner because it is 06's rule. One line in `invoices.py` (`CLOSED_FIELDS`), one `rules` run, and
  the rule reads back with nine controls, the subtable stored like any other target (`childControlIds: []`,
  `permission: []` — the server changed nothing).

  **A read-only rule over a 子表 hides its row controls** — the first thing in this app to establish it, and
  nothing else in ERP Master or in the brownfield Sales app uses the combination. It could not be established
  from the CLI: a read-only rule is browser-side, so no reading distinguishes "greys the table" from "hides the
  row controls" from "does nothing", and the API writes a posted document's lines either way. **Test 25 settled
  it in the browser**: the posted **INV/2026/00001** shows its Invoice Lines table with **no *Add a row* and no
  *Batch Operation***, and the Display Type column's required asterisk gone; the **Sunway Construction Group
  draft** keeps both controls and stays editable. A posted document's lines are now closed, as in Odoo, and
  07's difference 11 is resolved.
- **A HAP workflow can do everything the numbering needs.** It can *query records* (a search step, flowNodeType 7,
  and a get-records step, 13), *count* them (a formula step, flowNodeType 9, actionId **107** — a worksheet total
  with `reportControlId` empty and `reportType` 0, which is "record count", plus its own filter), and do *string
  formatting* (a formula step, actionId **106** — a function formula whose result is text). It has **no code
  node**: hap-cli refuses `nodeType: "code"` outright ("cannot be created through batch-add yet"), so a code step
  would have to be added and configured by hand in the UI. None was needed.

**The numbering chain**, in the Confirm workflow `6aa9f89b4f2a99acac043704`:

| # | Step | Kind | Does | Id |
|---|---|---|---|---|
| 1 | Get the journal | search (7 / 406) | Journals where Record ID equals the trigger's Journal | `6aa9f99da1c923a16efad72a` |
| 2 | The number's prefix and year | function formula (9 / 106), text | `CONCAT(IF((Type == "Customer Credit Note" \|\| Type == "Vendor Credit Note") && journal.Dedicated Credit Note Sequence == 1, "R", ""), journal.Sequence Prefix, "/", YEAR(Accounting Date), "/")` → `INV/2026/` or `RINV/2026/` | `6aa9f99da1c923a16efad744` |
| 3 | How many documents already carry it | worksheet total (9 / 107), count | Invoices where Number **starts with** step 2's result. Only the empty case is read now: 0 when nothing carries the prefix yet | `6aa9f99ea1c923a16efad76b` |
| 4 | The highest number already used | search (7 / 406) | **One** document, Invoices where Number starts with step 2's result, **sorted Number descending**. The suffix is zero-padded to a fixed width, so within one prefix and year a text sort is numeric order — INV/2026/00010 sorts above INV/2026/00009 | `6aaa15188e75db182e79a03e` |
| 5 | The next number | function formula (9 / 106), text | `IF(Number is empty or "Draft", CONCAT(prefix, RIGHT(CONCAT("0000", IF(highest == "", SUM(count, 1), SUM(RIGHT(highest, 5), 1))), 5)), Number)` → one past the highest, or **the number the document already has** | `6aa9f99fa1c923a16efad792` |
| 6 | Post the document | update (6 / 2) | Status → Posted, Number → step 5's result | `6aa9f89c8e75db182e789eeb` |
| 7 | An invoice or receipt with no date? | branch (1) | Type is any of the **six non-entry types** and Invoice Date is empty → *Fill in today's Invoice Date* (`6aa9f9a116473257ad4d3cc3`), the 系统 node's Current time. Odoo `_post`, `is_invoice(include_receipts=True)` | `6aa9f9a116473257ad4d3c8e` |
| 8 | A customer document without a Payment Reference? | branch (1) | Type is any of the three customer types **and** Payment Reference is empty → *Copy the Number to the Payment Reference* (`6aa9f9a216473257ad4d3d2d`) | `6aa9f9a216473257ad4d3cf7` |

Cancel (`6aa9f99016473257ad4d3bc6`) and Reset to Draft (`6aa9f9938e75db182e78a8b3`) are one update step each —
Status to Cancelled and back to Draft — and neither touches the Number.

### Self-checks through the CLI

(`invoices.py check`, `verify`, `selfcheck`, `order`, `untouched`; the TEST records are listed in §3.)

- **Configuration** — `check` reads back OK: 32 controls in their places with the right aliases, hints, help,
  required, read-only and decimals; Number the title field with the default "Draft"; the four option lists with
  their keys and defaults (Customer Invoice, Draft, Tax Excluded, No); both relations pointing at Contacts and
  Journals; the five rules enabled with one condition each; the three views with their columns, two-level sort,
  Type filter and Type + Status quick filters, in that order; the three buttons with their Status conditions and
  Cancel's confirmation; and the seven numbering steps present in the Confirm workflow.
- **The tabs** — `check` prints what each holds, read from every control's stored `sectionId`: Invoice Lines — the
  remark block, Terms and Conditions, Untaxed Amount, Tax, Total, Amount Due; Other Info — the Invoice divider,
  the remark block, Customer Reference, Salesperson, Recipient Bank, Payment Reference, Delivery Date, the
  Accounting divider, Source Document, Auto-post, Auto-post until; MyInvois — the remark block; on no tab — Status,
  Type, Number, Customer / Vendor, Invoice Date, Delivery Address, Accounting Date, Due Date, Payment Terms,
  Journal, Tax mode. All three remark blocks read their HTML back exactly as sent, `hidetitle` "1", width 12.
- **The three documents** — `verify`: "3 in the seed file; 0 missing or differing", every one of twenty stored
  values compared against `data/casimir-invoice-seed.json`, Relations read back by name.
- **The three customers** — `customers` compares every field it writes and re-reads each record: name, Address
  Type *Contact*, email, phone, street, city, state, ZIP, country, the tenant's note and Salesperson Casimir, with
  Active explicit. Company ID and DUNS stay empty, as §1 says. A second run writes nothing.
- **The numbering, end to end** — `selfcheck` confirms a TEST draft per prefix and checks the number's shape,
  the Invoice Date and the Payment Reference:

  | Document | Type | Journal | Number | Invoice Date | Payment Reference |
  |---|---|---|---|---|---|
  | TEST-SEQ-1 | Customer Invoice | Sales | **INV/2026/00002** — after the seeded INV/2026/00001 | today | INV/2026/00002 |
  | TEST-SEQ-2 | Customer Invoice | Sales | **INV/2026/00003** | today | INV/2026/00003 |
  | TEST-SEQ-3 | Customer Credit Note | Sales (Dedicated Credit Note Sequence) | **RINV/2026/00001** | today | RINV/2026/00001 |
  | TEST-SEQ-4 | Vendor Bill | Purchases | **BILL/2026/00001** | today | *(empty — not a customer document)* |
  | TEST-SEQ-5 | Journal Entry | Miscellaneous Operations | **MISC/2026/00001** | today *(before the fix below)* | *(empty)* |
  | TEST-SEQ-6 | Journal Entry | Miscellaneous Operations | **MISC/2026/00003** | **empty** — the is_invoice() fix | *(empty)* |
  | TEST-SEQ-7 | Customer Invoice | Sales | **INV/2026/00006** — one past the highest, over the gap at 00002 | today | INV/2026/00006 |

  **Reset to Draft** on TEST-SEQ-3 set Status to Draft and kept its number, **Confirm** posted it again and kept
  the number rather than issuing a new one, and **Cancel** set it to Cancelled and kept it a third time.

  Two more cases were checked by hand on TEST-SEQ-7 and are not part of the repeatable step: a **prefix nothing
  carries yet** (the document moved to a Journal Entry on the Bank journal, which holds no documents at all)
  numbered **BNK1/2026/00001** — the count step's empty case — and moving it back to a Sales customer invoice
  numbered it INV/2026/00006 again.

  The step **leaves alone any TEST document that already carries a number of the right shape**, whatever its
  Status, and confirms only an unnumbered draft. That rule was learned the hard way: an earlier version reset
  every one of them on each run, and re-running it after the UI test took RINV/2026/00001 back off a cancelled
  document and re-issued **RINV/2026/00002 — a number the UI test had already given to another record**. The
  duplicate was undone by putting RINV/2026/00001 back on TEST-SEQ-3, and no two documents in the worksheet share
  a number now. It is the clearest demonstration there is of *the numbering counts, it does not reserve*.
- **The views** — `order` returns each view in its own filter and sort: Invoices (6) RINV/2026/00001,
  INV/2026/00003, INV/2026/00002 (all 2026-09-16), Draft (2026-09-14), INV/2026/00001 (2026-09-11), Draft
  (2026-09-09); Bills (1) BILL/2026/00001; Journal Entries (1) MISC/2026/00001. That is Odoo's `date desc,
  name desc`.
- **Idempotent** — every step was run twice and `all` three times: the second runs added no control, rule, view,
  button or record, re-created no workflow ("already has steps; left as is"), re-published nothing ("already
  built; not re-published") and wrote no field ("layout already as specified; nothing saved").
- **Nothing else was touched.** The other five worksheets' controls were compared by id before and after every
  save, and the digests are the same at the end as at the start: Contacts 30 `9f7e59498c3081a1`, Units &
  Packagings 10 `e57dc8775cd5038b`, Products 19 `a8f9911118fda7d7`, Product Variants 20 `6eba14458f20e2a6`,
  Journals 15 `3d6313d3be876df3`. Their rules, buttons and views also read back unchanged (3 / 2 / 3, 3 / 2 / 2,
  3 / 2 / 3, 2 / 2 / 2 and 5 / 2 / 2). Contacts gained three records and nothing else. The Sales app
  `3e596740-d096-42cd-b948-0b62a0220927` was never opened. The app's own operation log for 16 Sep 2026 holds
  1 145 entries, every one of them this session's (Journals 732 from the morning's work, Invoices 268, Contacts
  52); no other account wrote to ERP Master while this was built.

The five rules, the three remark blocks, the placeholders, the descriptions, the quick filters and the buttons'
conditions are browser behaviour: HAP stores them as configured and only the UI test can show them working. It
did, on 16 Sep 2026, and the **read-only rule** — the one control this app had not used before — behaves as
designed: the eight fields are locked on a posted and on a cancelled document and editable on a draft.

**What the UI test changed.** Two things, both re-checked through the CLI afterwards:

| Change | Why |
|---|---|
| **Accounting Date now defaults to today.** `advancedSetting.defsource` went from `staticValue` "" to **"2"** with `time` "current" | §1 asks for it and the field came up empty. `staticValue` is a sentinel, not a day offset — "2" is HAP's 当天 (Found while building). `check` now prints and compares all three Date defaults, and re-running `layout` writes nothing |
| **Confirm no longer dates a Journal Entry.** The branch became *An invoice or receipt with no date?* — Type is any of the six non-entry types **and** Invoice Date empty | Odoo `_post` dates `is_invoice(include_receipts=True)` only. One condition added to a path that already existed; TEST-SEQ-6, confirmed afterwards, comes back with no Invoice Date, and the Confirm workflow re-published clean |
| **The number now comes from the highest already issued, and a document that has one keeps it.** A search step — one record, Number descending, same prefix filter — joined the chain between the count and the number, and the number formula reads it and short-circuits when the document is already numbered | The count-based version would have re-issued INV/2026/00005 over the gap the UI test opened. The proof is TEST-SEQ-7, confirmed afterwards as **INV/2026/00006**, and TEST-SEQ-3, confirmed a second time and keeping RINV/2026/00001 |

### Found while building

- **A Relation's picker filter cannot follow another dropdown on the same form, and that is why Odoo's Journal
  domain is not built** (21 Sep 2026, `15-ui-conformance.md` §1.3). Odoo narrows the picker itself:
  `journal_id`'s domain is `[('id', 'in', suitable_journal_ids)]`, and `_get_suitable_journal_ids` keeps the
  journals whose Type is **sale** for the three customer types, **purchase** for the three vendor types and
  **general** — Miscellaneous — for a journal entry (`account_move.py`, `_get_invoice_filter_type_domain`; the
  19.0 checkout and the tenant's `fields_get` agree). Ours offered every journal.
  A HAP picker filter compares a field of the **candidate** record with a literal, or with a value read off the
  form being edited (`dynamicSource` — three of them are already in this app: Products' Packagings, Product
  Variants' Extra Packagings and Chart of Accounts' Parent Account, all comparing a **record id or a text
  value**). The value this one needs is the document's Type, and a dropdown's form value is an **option key** of
  *this* worksheet's Type control. Journals' Type is a different dropdown with its own keys — `1eb997f4…` Sales
  against `af9b889e…` Customer Invoice — and nothing in HAP maps one option set onto another, so the comparison
  could never match. Seven document types collapse onto three journal types, so the keys cannot be made to agree
  either. A **static** filter is worse than none: it would have to name one journal type, and a journal entry
  legitimately uses Miscellaneous. **The only conceivable shape** is a pair of computed text bridges — a text of
  the journal's Type on Journals, a text of the wanted journal type on Invoices, compared as text — which adds a
  control to two worksheets for a filter that runs in the browser only and so cannot be proved from the CLI at
  all. It was not built.
- **…so what is built is Odoo's constraint instead, which it turns out Odoo also has.**
  `@api.constrains('journal_id', 'move_type') _check_journal_move_type` raises *"Cannot create a sale document in
  a non sale journal"* and *"Cannot create a purchase document in a non purchase journal"*. Two validation rules
  (check type 1, hint type 0) carry those two messages verbatim, standing on a new stored lookup **Journal Type**
  (field 25). **Proved through the CLI, both ways**, by `record update` sending Type unchanged — the condition
  field has to be in the write (`BUILDING.md`):
  - **refused, `resultCode 32`**: MISC/2026/00002, a *Customer Credit Note* in *Miscellaneous Operations* — the
    document 15 §1.3 found — and **INV/2026/00004, a *Vendor Bill* numbered from the *Sales* journal**, which the
    conformance pass had not spotted. Both are live seeded documents and were left as they are for the owner;
    editing either in the form now raises the message until its Journal is corrected, exactly as Odoo would;
  - **accepted**: INV/2026/00002 (Customer Invoice · Sales), MISC/2026/00001 and MISC/2026/00003 (Journal Entry ·
    Miscellaneous Operations — neither half of Odoo's constraint covers an entry, and neither do these rules),
    and a draft whose Journal had been emptied, which is what the *Journal Type is filled* clause is for.

  Two differences remain, both in §3: Odoo **prevents the choice** where this **refuses the save**, and a journal
  entry may be written in any journal here where Odoo's picker would have offered it only the Miscellaneous ones.
  And `record create` is not rule-checked at all (`BUILDING.md`), so a seed or import can still write a mismatched
  document through the API; the form checks it.
- **A search step can sort, can be limited to one record, and its record's fields reach a later formula.** That is
  the whole of what the highest-number step needs: `sorts` `[{controlId, controlType, isAsc: false}]` on the
  *search* node (flowNodeType 7, actionId 406, which returns a single record by definition), a filter whose
  comparison value is an earlier **formula node's** result (`{nodeId, controlId: "string_fx_id"}`, conditionId 5
  = 开头是), and `$<searchNodeId>-<controlId>$` in the next formula. When it finds nothing, that reference reads
  back as the empty string, which an `IF(… == "", …)` can test. `batch-add` sends the filter as `operateCondition`
  and no sort at all, so both go in afterwards with `node save --type 7`.
- **`+` concatenates in a workflow formula whenever either side is text, and the result is then read as an octal
  literal.** `"5" + 1` is `51`; `"00005" + 1` is **41** — "000051" parsed as octal. `RIGHT("INV/2026/00005", 5)`
  is the text "00005", so `RIGHT(…) + 1` silently produced 41 and the padded number came out `00041`. Force a
  numeric context: **`SUM(x, 1)`** (used here), `x * 1 + 1` or `INT(x) + 1` all give 6. There is **no `VALUE()`
  and no `LEN()`** — both compute the whole expression empty, with no error.
- **A workflow function formula compares with `==`, never `=`.** `IF(1 = 1, "A", "B")` is stored without complaint,
  publishes cleanly and computes **empty** — and an empty result silently poisons the whole `CONCAT` around it. The
  first numbering run produced `00007` for every document: the prefix had evaporated, so the count's *starts with*
  filter matched every record in the worksheet. `IF(1 == 1, …)` works. `&&` and `||` are the boolean operators;
  a ternary (`a ? b : c`) and `IIF()` both compute empty as well. `CONCAT`, `IF`, `YEAR`, `RIGHT` and arithmetic
  inside a formula all work, and **there is no error anywhere** — the only symptom is a wrong value in a record.
- **Inside a formula a dropdown renders its label and a checkbox renders `true`/`false`, but the checkbox compares
  equal to `1`.** `CONCAT("[", Type, "]")` gives `[Customer Credit Note]`; `CONCAT("[", Dedicated Credit Note
  Sequence, "]")` gives `[true]`, while `IF(that == 1, …)` is the comparison that works.
- **A workflow update step stores a dropdown as the bare option key** in `fieldValue`. A Python list (which is what
  `common.button_workflow`'s `value` would naturally carry for an option field) makes `flowNode/saveNode` answer
  **HTTP 500**; a JSON array string (`"[\"<key>\"]"`) is accepted and stored empty. Only the key on its own sticks.
- **A text field taken from another node is a template, not a reference.** `fieldValue` must hold
  `$<nodeId>-<fieldId>$`; `nodeId` + `fieldValueId` — which is right for every other type — stores nothing. A value
  from the fixed 系统 node (Current time) uses `nodeId` + `fieldValueId` + `nodeTypeId` 100, and the server rewrites
  the `appType` 100 it is sent into **`nodeAppType`** 100, so a step that compares what it sent with what came back
  re-saves for ever unless it sends `nodeAppType`.
- **An update step pointed at another update step stores no fields at all.** `selectNodeId` must name a node that
  produces a record — the trigger, or a search step. Given another update step the server answers `isException:
  true` with `fields: []`, and every field write is dropped silently. This is what `batch-add` does when the second
  batch is anchored on the first batch's last step: the branches came out with empty update steps and the workflow
  refused to publish with `warningType 103`.
- **`batch-add` drops a branch path's name and its condition** when the path is added in a second call.
  `node save --type 2` with `operateCondition` sets the condition but **not** the name, even with `-n`; the name
  needs `workflow node rename`. (`node get` returns the condition as `conditions`, which is not the key `save`
  accepts — already in `BUILDING.md`.)
- **`hap worksheet update --alias` fails with "参数错误" unless `-a/--app-id` is passed**, although
  `common.ensure_worksheet` calls it without one — it works there because the worksheet is being created in the
  same breath.
- **A view's or a button's condition on a single select is filterType 51, not 2.** hap-cli's filter translator maps
  `eq` to 51 (EQ_FOR_SINGLE) when the condition carries `dataType` 9 or 11, and to 2 without it. 51 with several
  option keys means "is any of" — that is how *Reset to Draft* is enabled on Posted **or** Cancelled. A business
  rule's filter is the other enum, where the same "is any of" is filterType 2 (Journals' Type rules).
- **A Relation's `sourceControlId` can point at a control that does not exist.** Teh Li Wei's Customer field
  reserved `6aa920d74a73a3142152e68a` on Contacts and no reverse control was ever created there; re-sending the
  control in a full save does not create one either. The two relations added here carry
  `advancedSetting.bidirectional` "0" and were appended without a client-side id, and Contacts' and Journals'
  30 and 15 controls are unchanged.
- **`record list --view-id` returns only the view's own columns**, so a value the view sorts on but does not show
  (the Accounting Date on Invoices and Bills) comes back empty and has to be read separately.
- **A Date field's default is a sentinel, not a value.** `defsource` `staticValue` **"2"** with `time` "current" is
  HAP's 当天 — the current day — and that is what Teh Li Wei's Due Date carried, so his default was *today*, not
  "today + 2" as the number suggests. An **empty** `staticValue` with the same `time` is stored without complaint
  and applies nothing at all: that is why Accounting Date came up blank on the create form. The shape is confirmed
  by hap-cli's own captured payload (`tests/test_core.py::test_date_now_default`, "日期+默认值当天") and by the
  backup of the skeleton. **The API applies no defaults**, so the stored string is the only thing a script can
  check — `invoices.py check` prints all three Date defaults verbatim and compares them.

**And five things only the UI test could show** (the planner's, 16 Sep 2026):

- **A button whose condition fails is hidden, not greyed out.** A draft shows Confirm and Cancel only; a posted or
  cancelled document shows Reset to Draft only. `BUILDING.md` and the Journals hand-off both say the inapplicable
  button greys out — on Journals it does. Reviewers comparing the two worksheets will notice.
- **HAP marks read-only three different ways in the DOM**, which matters for anyone testing a read-only rule: a
  text, number or date control gets the class `controlDisabled` on its `.customFormControlBox`; a relation gets
  `readonly` on `.RelateRecordDropdown-selected`; and a read-only field with **no value renders as an empty
  `<div class="customFormNull">`** — indistinguishable from an empty editable field unless you know to look.
- **A relation picker offers archived records.** The Journal picker lists the archived TEST Sales journal beside
  Sales; Odoo hides archived journals. Left as it is — a picker filter is browser-side only and would have to be
  proved in the UI (§3, differences).
- **Re-confirming a document keeps the old Payment Reference.** Confirm only fills it when it is empty, so after a
  Reset to Draft and a second Confirm the document carries a new Number and the *previous* Payment Reference
  (§3, difference 3).
- **A newly created record stays in a view whose Type filter excludes it until the page is reloaded.** A Vendor
  Bill created from the Invoices view sat there until refresh, then dropped out correctly. HAP's list, not the
  view's filter.

## 3 · Test list

To run in the Nocoly UI, in Chrome, against `~/.hap-venv/bin/python nocoly/build/invoices.py document
"<Number>"` / `order` / `verify` / `check` from the repo root for the stored values. Test records are named
`TEST …`; the **five** tenant invoices and their **four** customers are real records and must come through the
test unchanged (`verify` at the end). Two of those five — INV/2026/00002 and the cancelled S00021 — arrived with
bundle 7 on 21 Sep 2026 and are **not** `TEST …` records, whatever their Customer Reference says: the tenant's
own reference on the first is the string "TEST demo run - delete me".

**The numbers a Confirm produces depend on what is already posted**, so the expected numbers below are the ones
the first run through this list produced. **The worksheet now stands at**: INV/2026/00001 (seeded), 00003, 00004,
00005 and 00006; RINV/2026/00001 and 00002; BILL/2026/00001 and 00002; MISC/2026/00001, 00002 and 00003 — fourteen
documents, no two sharing a number. The next Sales invoice confirmed will be **INV/2026/00007**. Run
`invoices.py order` before repeating any of tests 15–19 and shift the expected numbers accordingly.

> **INV/2026/00002 is an unused gap** — test 18 reset it to draft and re-confirmed it as INV/2026/00005. The
> numbering was changed afterwards (§2) to take **one past the highest number already issued** rather than one
> past a count, so the gap is harmless: the next Confirm goes to 00007, not back over 00005. **Test 18 now
> expects the number to stay put**, which is what Odoo does, so no new gap can open either.

| # | Check | Steps | Expected | Result |
|---|---|---|---|---|
| 1 | Menu and views | Open ERP Master → menu group **Invoicing** → Invoices | Invoicing lists Journals then Invoices. Invoices opens on the **Invoices** table; its view list is Invoices · Bills · Journal Entries, in that order |  **Pass** — Invoicing lists Journals then Invoices, and the three views in that order |
| 2 | The Invoices table | The Invoices view | 6 rows, columns **Number · Customer / Vendor · Invoice Date · Due Date · Journal · Untaxed Amount · Total · Amount Due · Status**, in this order: RINV/2026/00001, INV/2026/00003, INV/2026/00002 (all 16 Sep), Draft (Sarawak Timber Logistics, due 2026-10-29), INV/2026/00001 (Klinik Kesihatan Damansara), Draft (Sunway Construction Group). No Type, Accounting Date, Tax or Salesperson column. BILL/2026/00001 and MISC/2026/00001 are **not** here |  **Pass** — the nine columns in that order, and none of Type, Accounting Date, Tax or Salesperson |
| 3 | The Bills table | Switch to **Bills** | 1 row, BILL/2026/00001, the same nine columns. No customer document |  **Pass** |
| 4 | The Journal Entries table | Switch to **Journal Entries** | 1 row, MISC/2026/00001, columns **Number · Accounting Date · Journal · Total · Status** only |  **Pass** — its own five columns, not the Invoices ones |
| 5 | Quick filters | Invoices → the **Type** quick filter: pick Customer Invoice, then Customer Credit Note, then clear; then the **Status** quick filter: Posted, then Draft, then clear | **Customer Invoice → 5 rows** (INV/2026/00001, 00002, 00003 and the two seeded drafts). **Customer Credit Note → RINV/2026/00001 alone.** Sales Receipt → nothing. **Posted → 3** (the three INV numbers), **Draft → the two seeded drafts**, **Cancelled → RINV/2026/00001**. Cleared → 6. Neither filter can reach a row the view's own Type filter excludes: picking Vendor Bill leaves the table empty rather than showing BILL/2026/00001 |  **Pass** — and picking Vendor Bill inside the Invoices view gives “No matching records found”, so a quick filter cannot reach past the view's own filter |
| 6 | The posted seeded invoice, field by field | Open **INV/2026/00001** | Number INV/2026/00001 (read-only), Type Customer Invoice, Status **Posted**, Customer / Vendor Klinik Kesihatan Damansara, Invoice Date 2026-09-11, Accounting Date 2026-09-11, Due Date 2026-10-02, Payment Terms "21 Days", Journal Sales, Tax mode Tax Excluded. Tab **Invoice Lines**: the remark block, Terms and Conditions (empty), Untaxed Amount 11,432.00, Tax 1,143.20, Total 12,575.20, Amount Due 12,575.20. Tab **Other Info**: heading *Invoice*, the remark block, Customer Reference KKD-2026-009, Salesperson Casimir, Recipient Bank empty, Payment Reference **INV/2026/00001**, Delivery Date empty; heading *Accounting*, Source Document **S00014**, Auto-post No, no Auto-post until. Tab **MyInvois**: the remark block only |  **Pass** — every value as listed, Payment Reference INV/2026/00001 and Source Document S00014, all three tabs |
| 7 | The two seeded drafts | Open the **Sunway Construction Group** draft, then the **Sarawak Timber Logistics** one | Number reads **Draft** in both, Status Draft, Invoice Date **empty**, Accounting Date 2026-09-09 / 2026-09-14, Due Date 2026-10-09 / 2026-10-29, Payment Terms "30 Days" / "45 Days", Source Document S00011 / S00016, totals 115,063.52 / 194,400.00, Amount Due equal to the Total, Payment Reference empty. Close without saving |  **Pass** |
| 8 | Read-only fields on a draft | On the Sunway draft, try to type in **Number**, **Status**, **Untaxed Amount**, **Tax**, **Total**, **Amount Due** and **Source Document** | None of the seven accepts input on a draft; the other fields do. Close without saving |  **Pass** — and a read-only field with no value renders as *nothing at all*, not as an empty box, which is worth knowing when checking a rule |
| 9 | A new record and the defaults | Invoices → + Record; look before touching anything | Number **Draft**, Type **Customer Invoice**, Status **Draft**, Accounting Date **today**, Tax mode **Tax Excluded**, Auto-post **No**, the four amounts **0.00**, Due Date and Invoice Date **empty** (no "two days from today"). Type, Accounting Date, Journal and Auto-post are marked required. **Delivery Address is shown** (the Type is already a customer one) and **Auto-post until is not** |  **Pass**, after a fix — on the first run **Accounting Date came up empty**; the default was re-encoded and the create form now opens with today. Everything else was right first time |
| 10 | Rule · Delivery Address is for customer documents | On that new record, switch Type through Vendor Bill, Journal Entry, Purchase Receipt, then back to Sales Receipt and Customer Credit Note | **Delivery Address disappears** for the three vendor types and for Journal Entry, and comes back for Customer Invoice, Customer Credit Note and Sales Receipt |  **Pass** — gone for the three vendor types and for Journal Entry, back for Customer Invoice, Customer Credit Note and Sales Receipt |
| 11 | Rule · a vendor document must carry its date, and · every document but an entry has a tax mode | Same record: set Type **Vendor Bill**, fill Customer / Vendor and Journal, clear Invoice Date and Tax mode → Submit. Then fill the Invoice Date → Submit. Then set Type **Journal Entry**, clear Tax mode → Submit | Vendor Bill: refused, **Invoice Date** and **Tax mode** both marked required. With both filled it saves. Journal Entry: Tax mode is **not** required and the record saves without one; Invoice Date is not required either. Name the saved record `TEST UI rules` and keep it for test 20 |  **Pass** — “Please fill in Invoice Date” and “Please fill in Accounting Date” on a Vendor Bill; with both filled it saved; a Journal Entry needs neither the date nor a tax mode |
| 12 | Rule · a posted or cancelled document is closed for editing | Open **INV/2026/00001** (Posted). Then open the Sunway draft. Then open a cancelled document — Cancel the `TEST UI rules` record from test 11 first if none is to hand | On the posted invoice, **Type, Customer / Vendor, Journal, Invoice Date, Accounting Date, Due Date, Payment Terms, Tax mode, Delivery Address, Delivery Date, Auto-post and Auto-post until are all read-only**, and the Lines table offers neither *Add a row* nor *Batch Operation*; Customer Reference, Salesperson, Recipient Bank, Payment Reference and Terms and Conditions stay editable. On the **draft** they are all editable again. On the **cancelled** document they are read-only, as on the posted one |  **Re-run needed for the last four.** The 16 Sep pass proved the first eight on Posted *and* Cancelled, with a draft fully editable. 15 §1.1 then found **Delivery Address, Delivery Date, Auto-post and Auto-post until** still editable on the posted INV/2026/00001 — the tenant carries `readonly="state != 'draft'"` on all four — and they joined the rule on 21 Sep 2026. An interaction rule is browser-side, so only the UI can show it |
| 13 | Rule · Auto-post until follows Auto-post, and · Auto-post is not offered on a receipt | On a draft, Other Info → set Auto-post to **Monthly**, then **At Date**, then back to **No**. Then set Type to **Sales Receipt**, and to **Purchase Receipt** | **Auto-post until appears for Monthly, Quarterly and Yearly only** — **At Date** hides it, as *No* does. On either receipt type the **Auto-post dropdown itself disappears** (and Auto-post until with it); it comes back on every other Type. Close without saving |  **Re-run needed.** The 16 Sep pass read “Auto-post until appears for Monthly and is gone again for No”, which was right for the rule as it then stood; 15 §1.2 found *At Date* showing it too, and both rules were rewritten on 21 Sep 2026. Nothing here is provable from the CLI |
| 14 | The three tabs and their notes | On any document, open **Invoice Lines**, **Other Info** and **MyInvois** | Each tab renders its remark block as a paragraph of text — *The lines arrive with 07 Invoice Lines.*, *Also on Odoo's Other Info tab:*, *MyInvois is Malaysia's e-invoicing clearance.* — with the bold lead-in, no field label and no input. Other Info also shows the two divider headings **Invoice** and **Accounting** above their groups |  **Pass** — all three blocks render with their bold lead-in, no label and no input, and Other Info also shows the Invoice and Accounting headings |
| 15 | **Confirm · the numbering** | New record: Type Customer Invoice, Customer / Vendor Sunway Construction Group, Journal **Sales**, Accounting Date today, Customer Reference `TEST UI 1` → Submit. Open it and press **Confirm**. Repeat with `TEST UI 2` | No confirmation dialog. The first becomes **INV/2026/00004**, the second **INV/2026/00005** — the numbers follow each other. Both: Status **Posted**, Invoice Date **today** (it was empty), Payment Reference **the same number**. `invoices.py document "INV/2026/00004"` confirms the stored values |  **Pass** — run on the vendor bill from test 11: Confirm with no dialog, Status Posted, **INV/2026/00004** — a Vendor Bill written in the Sales journal, so the prefix follows the *journal*, not the type, as in Odoo. Its Payment Reference stayed empty, being a vendor document. Two Sales invoices numbered one after the other were proved by the CLI self-check rather than in the browser |
| 16 | Confirm · a credit note on a journal with a dedicated sequence | New record: Type **Customer Credit Note**, Journal **Sales** (Dedicated Credit Note Sequence ticked), Accounting Date today, Customer Reference `TEST UI 3` → Submit → **Confirm** | The number is **RINV/2026/00002** — the R prefix, and its own counter, separate from INV |  **Pass** — **RINV/2026/00002**, the R prefix on its own counter. The draft was written with the CLI and confirmed with the button |
| 17 | Confirm · a journal without a dedicated sequence, and a vendor document | New record: Type **Customer Credit Note**, Journal **Miscellaneous Operations** (no Dedicated Credit Note Sequence), Customer Reference `TEST UI 4` → Submit → Confirm. Then a **Vendor Bill** on **Purchases**, Invoice Date today, Customer Reference `TEST UI 5` → Submit → Confirm | The credit note becomes **MISC/2026/00002** — **no R**, because that journal has no dedicated credit note sequence. The bill becomes **BILL/2026/00002**, and its **Payment Reference stays empty** — Odoo fills it on customer documents only |  **Pass** — **MISC/2026/00002** with no R, and **BILL/2026/00002** whose Payment Reference stayed empty. Both drafts written with the CLI, both confirmed with the button |
| 18 | Reset to Draft keeps the Number, and so does confirming again | On `TEST UI 1` (INV/2026/00004, Posted) press **Reset to Draft**; then press **Confirm** again | No confirmation. Status goes back to **Draft** and the Number **stays INV/2026/00004** — it is not given back and not blanked. The eight fields of test 12 become editable again. Confirming a second time posts it and **keeps INV/2026/00004** — no new number, no new gap, and the Payment Reference still matches. That is Odoo's own behaviour (`_post` sequences only an unset name). **Re-run after the numbering change of §2** |  **Pass** — re-run after the numbering was changed to read the highest number and to leave an existing one alone: **INV/2026/00004 survived Reset to Draft and a second Confirm**, as Odoo does. No gap, and nothing to shift for the next reviewer |
| 19 | Cancel and its confirmation | On `TEST UI 2` (Posted) look at the buttons; then on a **draft** press **Cancel**, first answering *Back*, then *Cancel document* | A posted or cancelled document shows **Reset to Draft only** — Confirm and Cancel are **hidden, not greyed out** (§2, and unlike Journals); a draft shows **Confirm and Cancel only**. Cancel asks "**Are you sure you want to cancel this document?**" with **Cancel document** / **Back**. *Back* changes nothing; *Cancel document* sets Status to **Cancelled** and leaves the Number as it was |  **Pass** — “Are you sure you want to cancel this document?” with Cancel document / Back; *Back* changed nothing, *Cancel document* set Cancelled and kept BILL/2026/00002. The button that does not apply is **hidden, not greyed out** |
| 20 | The relation pickers | On a draft, open the **Customer / Vendor**, **Delivery Address** and **Journal** pickers | The first two list Contacts — the three seeded companies among them, shown by their Display Name — and the third lists the Journals worksheet: Sales, Purchases, Bank, Miscellaneous Operations, Cash Basis Taxes, Exchange Difference, Tax Returns and TEST Journal. All three are single-select dropdowns |  **Pass** — all three are single-select and list the right worksheet. Two things to note: the Journal picker also offers the **archived** TEST Sales journal, and on one attempt the Contacts picker drew the matching company as two identical rows (Contacts holds exactly one, checked through the CLI, so nothing is duplicated in the data) |
| 21 | Placeholders and help | A new record: look at **Invoice Date** and **Payment Reference** before typing; then read the field help on Delivery Address, Payment Reference, Source Document, Auto-post, Auto-post until and Recipient Bank | "**Today**" and "**Standard communication**" show as placeholders. The six descriptions are Odoo's `help` word for word (Delivery Address "The delivery address will be used in the computation of the fiscal position.", Payment Reference "The payment reference to set on journal items.", Source Document "The document(s) that generated the invoice.", and so on). **Terms and Conditions shows no placeholder** — HAP never renders a Rich text field's hint — and says so in its description instead |  **Pass** — both placeholders, Odoo's help word for word, and every field carries its description under the label in the create form |
| 22 | The three customers in Contacts | Contacts → find **Sunway Construction Group**, **Klinik Kesihatan Damansara** and **Sarawak Timber Logistics** | Three company records, Address Type **Contact**, with the tenant's email, phone, street (Level 8, Wisma Perdana), city, state, ZIP, country Malaysia, Salesperson Casimir and the note "Seeded reference account — … sector."; **Company ID and DUNS empty** (the tenant has neither field). Contacts' own fields, views and rules are exactly as 01 left them, and its seven `TEST …` records are untouched |  **Pass** — Address Type Contact, the tenant's address, Salesperson Casimir, phone shown as 03-5631 2000, Company ID and DUNS empty; Contacts holds ten records, the seven `TEST …` and these three |
| 23 | The three documents survive the test | `~/.hap-venv/bin/python nocoly/build/invoices.py verify` and `check` | `verify`: "3 in the seed file; **0 missing or differing**", the TEST documents listed as not in it. `check`: "OK — controls, tabs, options, defaults, rules, views, buttons and the numbering workflow as specified" |  **Pass** — “3 in the seed file; 0 missing or differing”, and `check` reports controls, tabs, options, defaults, rules, views, buttons and the numbering workflow as specified |
| 24 | Odoo side by side | casimir.odoo.com → Invoicing › Customers › Invoices, and INV/2026/00001's form | The same customer invoices with the same numbers, customers, dates and totals; the form shows the same Customer, Invoice Date, Due Date, Payment Terms, Journal and Tax Excl./Incl. in the same places, and the same Other Info group. Everything Odoo shows that is not here is in *Not built now* |  **Pass** — the tenant still shows the same three documents with the same numbers, customers, dates and totals. Read from the tenant's own records: its web list view would not open in the test tab |
| 25 | A posted document's lines are read-only | Open **INV/2026/00001** (Posted) → tab **Invoice Lines** → the Lines table. Then the same on the Sunway Construction Group **draft** | The rule *A posted or cancelled document is closed for editing* now names the subtable, so the posted document's table should be locked and the draft's should not. Nothing about this could be proved through the CLI: an interaction rule is browser-side, and the API writes a posted document's lines either way | **Pass** — on **INV/2026/00001** the table has **no *Add a row* and no *Batch Operation***, and the Display Type column has lost its required asterisk; on the **Sunway draft** both controls are there and the table is editable as before. A HAP read-only rule over a 子表 hides the row controls, which is the first time this app has established that. Odoo locks a posted move's lines the same way — so difference 11 of 07 is resolved, not documented |
| 26 | The two journal checks | On a **draft**, set Type **Customer Invoice** and Journal **Miscellaneous Operations**. Then Type **Vendor Bill** with Journal **Sales**. Then put each back to a journal that suits it. Then a **Journal Entry** on Miscellaneous Operations | The first raises *"Cannot create a sale document in a non sale journal"* on the Journal field, the second *"Cannot create a purchase document in a non purchase journal"*; the message should appear as the Journal is picked, not only on Submit, and Submit should be refused while it stands. A journal entry is refused nothing, whichever journal it uses | **Proved through the CLI, not the browser.** `record update` sending Type was refused `resultCode 32` on MISC/2026/00002 (Customer Credit Note · Miscellaneous Operations) and on INV/2026/00004 (Vendor Bill · Sales), and accepted on INV/2026/00002 (Customer Invoice · Sales), on MISC/2026/00001 and MISC/2026/00003 (Journal Entry · Miscellaneous Operations) and on a draft whose Journal had been emptied. Whether the message reaches the **form** as the Journal is picked — which needs the Journal Type lookup to recompute in the open form — is for the UI pass |

### Differences from Odoo to look for

1. **One field, two words.** Odoo renames `partner_id` per document type — *Customer* on a customer document,
   *Vendor* on a vendor one — and `invoice_date` likewise (*Invoice Date* / *Bill Date*). HAP cannot rename a field
   from a rule, so Customer / Vendor carries both words and Invoice Date keeps the customer wording; the rule makes
   it required on a vendor document instead.
2. **Journal and Accounting Date are always shown.** Odoo shows the Journal only when several journals suit the
   type, and the Accounting Date only on vendor documents or once a posted customer invoice's date differs. Here
   both are always visible and required — the Journal because its Sequence Prefix is what Confirm numbers with.
3. ~~**Confirming twice gives a new number.**~~ **Settled on 16 Sep 2026** — Confirm now assigns a Number only to
   a document that has none, so a reset document keeps its number and takes it back on the next Confirm, exactly
   as Odoo does (`_post` sequences only an unset `name`, `button_draft` keeps it). The Payment Reference therefore
   cannot go stale either. `TEST-SEQ-1` still shows the old behaviour — INV/2026/00005 beside Payment Reference
   INV/2026/00002 — because it was confirmed twice before the change; nothing confirmed since can repeat it.
4. **The numbering does not reserve.** Two people confirming in the same second read the same highest number and
   produce the same next one — a race on the highest rather than on a count, which is a narrower window but not a
   closed one. Number deliberately allows duplicates, since several drafts read "Draft", so a collision would be
   stored rather than refused. Odoo takes a row lock; HAP has no equivalent through the CLI.
5. **A relation picker offers archived records.** The Journal picker lists the archived TEST Sales journal beside
   Sales; Odoo's Journal field hides archived journals. A picker filter is browser-side only and was not built.
6. **A button whose condition fails is hidden, not greyed out** — so a posted document shows only Reset to Draft.
   Odoo greys its header buttons out, and so does Journals' Archive / Unarchive; this worksheet differs from both.
7. **A newly created record stays in a view whose Type filter excludes it until the page is reloaded** — a Vendor
   Bill created from the Invoices view sits there until refresh. HAP's list, not the view's filter.
8. **A draft's Number literally reads "Draft".** Odoo stores `/` on an unnumbered draft and displays *Draft*; here
   the field holds the word, because it is the worksheet's title and a HAP title shows in every picker.
9. **No Active field, no Archive.** `account.move` has none; a document is cancelled instead. So Invoices has no
   Archived view and no Archive / Unarchive buttons, unlike the five worksheets before it.
10. **Payment Terms and Recipient Bank are text stand-ins**, and the four amounts are seeded read-only figures
   until 07 Invoice Lines. Each says so in its own description.
11. **Odoo's header carries ten buttons**, ribbons, alerts and smart buttons; here there are three buttons and a
   read-only Status field. The rest are in *Not built now*.
12. ~~**A posted document's lines are editable.**~~ **Settled on 16 Sep 2026**: the Invoice Lines subtable joined
   the read-only rule (§1), and test 25 showed it working — the posted INV/2026/00001 offers neither *Add a row*
   nor *Batch Operation*, while the Sunway draft offers both. A posted document's lines are closed for editing,
   as in Odoo, and 07's difference 11 is resolved with it.

13. **The list's untaxed column, and what sits beside it.** Seen on screen 18 Sep 2026 (`CROSSCHECK.md`): Odoo's
   list heads `amount_untaxed` **Tax Excluded** where ours uses Odoo's own field label, *Untaxed Amount*; ours
   carries a **Journal** column where Odoo's list carries **Last Reminder** and keeps Journal hidden; and Odoo
   **totals** Tax Excluded, Total and Amount Due at the foot of the list, which ours does not.

14. **A paid document still shows its Total as Amount Due.** Added 21 Sep 2026 with bundle 7's
   **INV/2026/00002**, the first seeded document the tenant shows as `paid`: the tenant reads Amount Due
   **0.00** against a total of 3,027.80, ours reads **3,027.80**. The roll-up writes Amount Due = Σ Total
   unconditionally, because nothing in the app can settle a document until the **Payments** bundle — Amount Due's
   own description has said so since 06 was built. It is deliberately **not** hand-written to match: the tenant's
   figure is kept beside it in `invoices.py` as `amount_residual_tenant`, and the day Payments arrives it becomes
   Total less what is paid. Every other figure on that document agrees with the tenant to the cent.

15. **A cancelled document's fields are locked in the browser only.** The rule *A posted or cancelled document
   is closed for editing* is an interaction rule, so bundle 7's cancelled S00021 was created with Status
   **Cancelled** in one `record create`, given its six lines, and had all four amounts written into it by the
   roll-up — none of it refused. Odoo blocks the equivalent writes in the ORM. Not a defect of the rule (07's
   difference 11 records the same thing for the lines); it is the reason a build script can seed a cancelled
   document at all, and the reason a rule is never the place to put a real constraint.

16. **The Journal picker is not narrowed by the document Type, and the check comes on save instead.** Added
   21 Sep 2026 (15 §1.3). Odoo does **both**: `journal_id`'s domain offers only the journals whose Type suits the
   document — sale for the three customer types, purchase for the three vendor ones, *general* (Miscellaneous) for
   a journal entry — and `_check_journal_move_type` refuses the save afterwards. **Only the refusal is built**, as
   the two validation rules in §1, with Odoo's two messages verbatim. So:
   - our picker still lists **every** journal, archived ones included (difference 5), and a person can pick a
     wrong one and only learn of it when the form refuses;
   - a **journal entry** may be written in any journal here, where Odoo would have offered it the Miscellaneous
     ones alone — Odoo's constraint says nothing about an entry either, so this half is only the picker;
   - `record create` is not rule-checked, so an import can still write a mismatched document through the API.

   Why the picker could not be built is in §2 *Found while building*: a HAP picker filter can read a value off the
   form, but a dropdown's form value is an option key of **this** worksheet's control, and Journals' Type is a
   different dropdown with its own keys.

17. **Two live documents are on the wrong journal, and the new rules now refuse to save them.** MISC/2026/00002
   is a *Customer Credit Note* written in *Miscellaneous Operations* (which is why it carries a MISC number), and
   **INV/2026/00004 is a *Vendor Bill* numbered from the *Sales* journal** — found by the CLI on 21 Sep 2026 while
   the rules were being proved, and not by the screen pass. Both were left exactly as they are: they are the
   evidence for tests 15 and 17, and changing seeded data needs the owner. Anyone opening either in the form will
   now meet the message until its Journal is corrected, which is what Odoo would do as well.

18. **The form carries a field Odoo's does not: *Journal Type*.** A read-only lookup of the Journal's own Type,
   on the Other Info tab beside Auto-post until, added 21 Sep 2026 because a HAP rule condition can only name a
   control of its own worksheet and the two journal checks have to compare it. Odoo reads `journal_id.type`
   straight off the relation and puts nothing on the form. It is read-only everywhere, and the posted-or-cancelled
   rule does not name it — it cannot be typed into in any state.


### Test records left in the worksheet

Eleven, as the worksheet stands after the UI test and the two fixes that followed it. `invoices.py selfcheck`
created the seven `TEST-SEQ-…` and now leaves any of them that already carries a well-formed number alone, so
re-running it changes none of these.

**The gap at INV/2026/00002 is gone** — bundle 7 seeded a real document there on 21 Sep 2026, the tenant's own
INV/2026/00002. Two entries below still talk about it as a gap, and both still mean what they say: TEST-SEQ-1's
stale **Payment Reference** reads INV/2026/00002 and is not a link to anything, and TEST-SEQ-7 took the number
*past* the gap rather than into it. The numbering is unaffected — Confirm reads the **highest** number under the
prefix, which is INV/2026/00010, not the first free one.

| Record | Number | Type · Journal | Status | What it is evidence for |
|---|---|---|---|---|
| **TEST-SEQ-1** | INV/2026/**00005** | Customer Invoice · Sales | Posted | Confirmed as INV/2026/00002, then reset and re-confirmed by test 18 — the number gap and the stale Payment Reference (difference 3) |
| **TEST-SEQ-2** | INV/2026/00003 | Customer Invoice · Sales | Posted | The counter following the seeded INV/2026/00001 |
| **TEST-SEQ-3** | RINV/2026/00001 | Customer Credit Note · Sales | **Cancelled** | The credit-note sequence on a journal with Dedicated Credit Note Sequence ticked; and Reset to Draft, a **second Confirm** and Cancel all keeping the number |
| **TEST-SEQ-4** | BILL/2026/00001 | Vendor Bill · Purchases | Posted | The prefix follows the journal; the Payment Reference stays empty on a vendor document |
| **TEST-SEQ-5** | MISC/2026/00001 | Journal Entry · Miscellaneous Operations | Posted | A document with no Tax mode and no partner. **Carries an Invoice Date**: it was confirmed before the is_invoice() fix |
| **TEST-SEQ-6** | MISC/2026/00003 | Journal Entry · Miscellaneous Operations | Posted | The **is_invoice() fix**: a Journal Entry confirmed afterwards comes back with **no Invoice Date** |
| **TEST-SEQ-7** | INV/2026/**00006** | Customer Invoice · Sales | Posted | The **numbering fix**: confirmed over the unused gap at INV/2026/00002, it took one past the highest (00006). The count-based version would have handed it INV/2026/00005, which TEST-SEQ-1 already holds |
| **TEST UI rules** | INV/2026/**00004** | **Vendor Bill · Sales** | Posted | Test 11's required-field checks; and, by accident, that the prefix follows the **journal**, not the Type — a Vendor Bill on the Sales journal is numbered INV. Its Customer Reference could not be set and is empty |
| **TEST UI 3** | RINV/2026/00002 | Customer Credit Note · Sales | Posted | Test 16 |
| **TEST UI 4** | MISC/2026/00002 | Customer Credit Note · Miscellaneous Operations | Posted | Test 17 — **no R**, because that journal has no dedicated credit note sequence. Its Auto-post was toggled Monthly and back to No for test 13 |
| **TEST UI 5** | BILL/2026/00002 | Vendor Bill · Purchases | **Cancelled** | Tests 17 and 19 |

No two of them share a number. All are to be removed after sign-off, with the owner's approval. The **five**
tenant invoices (SCG-PO-88213, KKD-2026-009, STL-2026-0042, and bundle 7's TEST demo run - delete me and
S00021) and the **four** customers in Contacts are real records and stay; `verify` confirms all five unchanged
after the test. **INV/2026/00002 is one of the five, not a test record** — the words "TEST demo run - delete me"
are the tenant's own Customer Reference on it, copied as read.


## Descriptions rewritten for the app's users (22 Sep 2026)

The owner's rule of 22 Sep 2026: a description in the app says only what the field or button does, for the people using it — no Odoo, no field or model names, no divergences, no build notes. The texts below were rewritten or emptied on the live app and in the builder's constants. The old text is kept here, word for word, because it carried the Odoo references and build reasoning that are no longer in the app.

| Control | Key | Before | After |
|---|---|---|---|
| Customer / Vendor | desc | Odoo labels the one field Customer on a customer document and Vendor on a vendor one; HAP cannot rename a field from a rule, so it carries both words. | The customer on a customer document, the vendor on a vendor bill or vendor credit note. |
| Invoice Date | desc | Odoo labels it Bill Date on a vendor document, where it is required. Confirm fills it with today when it is empty. | The date of the invoice or bill. Required on a bill. Confirm fills in today's date if it is left blank. |
| Due Date | desc | Odoo shows the Due Date or the Payment Terms: setting terms computes the date. | When payment is due. Choosing Payment Terms works it out. |
| Customer Reference | desc | Odoo shows the same field as Bill Reference in the main group of a vendor document. | The customer's reference for this invoice, or the vendor's reference on a bill. |
| Recipient Bank | desc | A stand-in: Odoo points at a res.partner.bank record, and bank accounts are not in Phase 1. Odoo's help: "Bank Account Number to which the invoice will be paid. A Company bank account if this is a Customer Invoice or Vendor Credit Note, otherwise a Partner bank account number." | The bank account the invoice will be paid into: the company's account on a customer invoice or vendor credit note, otherwise the partner's. |
| Number | desc | Written by Confirm from the Journal's Sequence Prefix and the year of the Accounting Date — INV/2026/00001. A draft holds the word "Draft" until then, as Odoo shows it. | Given when the document is confirmed, from the journal's Sequence Prefix and the year of the Accounting Date, e.g. INV/2026/00001. Shows "Draft" until then. |
| Type | desc | One model holds every accounting document; the Type decides which one it is. Odoo's menus — Invoices, Credit Notes, Bills, Refunds, Journal Entries — are filtered views of this one table. | The kind of document: an invoice, credit note, bill, receipt or journal entry. |
| Status | desc | Draft until Confirm posts the document; Cancel makes it Cancelled, Reset to Draft takes it back. Odoo's header status bar. | Draft until Confirm posts the document. Cancel makes it Cancelled, and Reset to Draft takes it back. |
| Tax mode | desc | Whether a line's Amount is its subtotal or its total. Odoo requires it on every invoice, credit note and receipt: "The document tax mode must be set." | Whether the line prices exclude or include tax. |
| Terms and Conditions | desc | Odoo's placeholder here is "Terms and Conditions"; HAP never shows a Rich text field's placeholder, so it is said here instead. | *(empty)* |
| Untaxed Amount | desc | Seeded from the tenant and read-only; 07 Invoice Lines makes it a roll-up of the lines. | The sum of the lines' subtotals, before tax. |
| Tax | desc | Seeded from the tenant and read-only; 07 Invoice Lines makes it a roll-up of the lines. | The tax on the lines. |
| Total | desc | Seeded from the tenant and read-only; 07 Invoice Lines makes it a roll-up of the lines. | The amount to pay, tax included. |
| Amount Due | desc | Seeded from the tenant and read-only; it equals the Total until the Payments bundle can settle a document. | What is still to be paid on this document. |
| Delivery Address | desc | The delivery address will be used in the computation of the fiscal position. | The address the goods or services are delivered to. |
| Journal | desc | The book the entry is written in. Its Sequence Prefix is what Confirm numbers the document with, so it cannot be changed once the document is numbered. | The journal the document is recorded in. Its Sequence Prefix numbers the document, so it cannot be changed once the document has a number. |
| Lines | desc | Odoo's Invoice Lines tab. The worksheet Invoice Lines, mounted here: the same rows are also a list of their own in the sidebar, and the invoice sums them into Untaxed Amount. | The products, sections and notes on this document. |
| Journal Type | desc | The Journal's own Type, read through the Journal relation and stored here. Odoo has no such field — it reads journal_id.type directly — but a HAP business rule can only compare a control of its own worksheet, and this is what the two journal checks stand on: Odoo's @api.constrains('journal_id', 'move_type') _check_journal_move_type, which refuses a sale document in a non-sale journal and a purchase document in a non-purchase journal. | The type of the selected journal. |

### Form texts replaced (22 Sep 2026)

The same rule, applied to the text on the form. The three remark blocks named what Odoo shows on each tab and which
bundle brings it; the owner had them rewritten in place for the app's users — nothing hidden or deleted — in one
version-pinned save of the three controls. Each now says what that part of the form is for. The old text is kept
here word for word, HTML as stored; the Invoice Lines one is the version `taxes.py note` wrote on 18 Sep 2026, which
`taxes.py` LINES_NOTE_TEXT now carries in its new form too, so neither builder puts the old text back.

| Control | Tab | Type | Key |
|---|---|---|---|
| Invoice Lines note, `6aa9f846e54d2a34fa4dfedc` | Invoice Lines | 10010 | dataSource |
| Invoice note, `6aa920d74a73a3142152e691` | Other Info, under the *Invoice* divider | 10010 | dataSource |
| MyInvois note, `6aa9f846e54d2a34fa4dfedd` | MyInvois | 10010 | dataSource |

Invoice Lines note, before:

```html
<p><strong>Odoo's Invoice Lines tab</strong> holds the product lines — product, label, quantity, unit, unit price, discount, taxes, subtotal and total — with <em>Add a line</em>, <em>Add a section</em>, <em>Add a note</em> and the product <em>Catalog</em>, and under them the totals and the payments already made.</p><p><strong>All four amounts are roll-ups of these lines.</strong> Untaxed Amount is the sum of their Subtotal; <strong>Tax</strong> is the sum of their Total less that, and stopped being a figure seeded from the tenant when the Taxes bundle arrived; Total and Amount Due are the sum of their Total. The payments already made, and the tax and payment-term lines Odoo writes itself, are not built.</p>
```

after:

```html
<p>Add the products, sections and notes of this document in the table below. Untaxed Amount, Tax, Total and Amount Due are worked out from these lines.</p>
```

Invoice note, before:

```html
<p><strong>Also on Odoo's Other Info tab:</strong> Sales Team and the marketing fields, a Payment QR-code, the Incoterm and its location, Fiscal Position, Payment Method, and — on a vendor bill — the source email and the OCR extraction.</p><p>Sales Team comes with the Sales app, the QR-code and Payment Method with the Payments bundle, and Fiscal Position, Incoterms and Cash Rounding each with their own table.</p>
```

after:

```html
<p>More details for this document: the customer's or vendor's reference, the salesperson, the bank account it is paid into, the payment reference and the delivery date.</p>
```

MyInvois note, before:

```html
<p><strong>MyInvois is Malaysia's e-invoicing clearance.</strong> Odoo's <code>l10n_my_edi</code> module puts the document's MyInvois state, its Tax Exemption Reason and a Customs Form Reference here, and adds the <em>Send To MyInvois</em>, <em>Request Cancel</em> and <em>Reload Data</em> buttons to the header.</p><p>The whole tab comes with the e-invoicing bundle; the tab is kept so the place it belongs is already marked.</p>
```

after:

```html
<p>This tab is for MyInvois, Malaysia's e-invoicing system, and has nothing to fill in.</p>
```
