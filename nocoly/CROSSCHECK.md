# Cross-check against Odoo's live screens

The owner asked, on 18 September 2026: *"for each worksheet, workflow, and others core functionalities that have
yet to be cross-checked against Odoo, UI check them."* This page is that pass. Each worksheet was opened **side by
side** — the model in casimir.odoo.com (Odoo saas~19.4) in one tab, the worksheet in ERP Master in the other — and
what the two screens show is compared here. Nothing in casimir was created or changed.

Before this pass, several worksheets had only ever been compared against **extracts** of the tenant (`get_views`,
`fields_get`, record reads) rather than against its screens: 08 and 09 had never been compared at all, 02 was
written when the tenant's screen for it could not be reached, and 04 and 06 were compared from data alone.

*The same page, for a reviewer: https://claude.ai/artifact/PWWjfHTutqNycCMcBXZBzn*

## What the pass found

**All ten worksheets now stand beside Odoo's own screens**, and nothing built is wrong. Five had never had this
comparison: 08 and 09 had never been compared at all, and 02, 04 and 06 had been written from extracts because
their pages "would not render" — which turned out to be a browser trap, not the tenant (below).

**Three new differences, every one cosmetic.**

| # | Worksheet | Difference |
|---|---|---|
| 1 | 02 Units & Packagings | Odoo's **form** labels the ratio *Quantity*; only its list header says *Contains*. Ours says Contains in both places |
| 2 | 06 Invoices | Odoo's list header for the untaxed figure reads *Tax Excluded*; ours reads *Untaxed Amount* (Odoo's own field label) |
| 3 | 06 Invoices | Ours shows a **Journal** column where Odoo's list shows **Last Reminder** and keeps Journal hidden, and Odoo **totals** its three money columns at the foot |

Nothing moves a value, nothing changes a rule, and no test result changes. Differences 1 and 2 are label
one-liners if the owner wants Odoo's exact wording. (05's ordering disagreement — three journals sharing sequence
10, Odoo breaking the tie by record id and ours by name — was already written down as its difference 2, and the
screens confirm it.)

**Two earlier notes are corrected** — 02's test 19 ("the tenant does not show a Units & Packagings menu") and, with
it, the reason 04 and 06 were never compared on screen.

**Nothing was written to casimir.** Every screen was opened read-only, and the few RPC reads used for the arch
audit are reads.

## The finding that colours the whole pass

**The reference tenant's own screens hide every account field.** casimir's administrator (uid 2) holds
`account.group_account_invoice`, `account.group_account_manager`, `account.group_account_basic` and
`product.group_product_variant`, `product.group_product_pricelist`, `uom.group_uom` — but **not**
`account.group_account_readonly`, **not** `account.group_account_user` and not `analytic.group_analytic_accounting`
(read from `res.groups.all_user_ids`; the Accounting groups belong to the full Accounting app, which this Invoicing
trial does not carry). Odoo's own form views put these behind exactly those groups:

| Field in Odoo | Group it needs | In ERP Master |
|---|---|---|
| `product.category` → whole *Accounting* page (Income, Expense Account) | `account.group_account_readonly` | Accounting tab, built by bundle 2 |
| `product.template` → *Accounting* page (`property_account_income_id`, `property_account_expense_id`) | `account.group_account_readonly` | Accounting tab, hidden from the Invoicing role |
| `account.journal` → `default_account_id`, `suspense_account_id`, `profit_account_id`, `loss_account_id`, `payment_account_id` | `account.group_account_readonly` | Five accounts, hidden from the Invoicing role |
| `account.move.line` → `account_id`, `date` | `account.group_account_readonly` | Account, hidden from the Invoicing role |
| `res.partner` → `property_account_receivable_id`, `property_account_payable_id`, `autopost_bills` | `account.group_account_user` | Receivable/Payable built, hidden from Invoicing **and** Accounting Read-only |
| `res.partner` → `property_payment_term_id`, `property_supplier_payment_term_id` | `account.group_account_invoice` or `…_readonly` | Built by bundle 3, visible to the accounting roles |
| `account.move` → `account_id`, `review_state`, `state` (`group_account_secured`) | readonly / user / secured | — |

Two things follow. **First, our role-hiding is faithful**: every field bundle 2 hid from the Invoicing role is a
field Odoo hides from everyone below `group_account_readonly`. **Second, a reviewer sitting in casimir will not
find these fields on its screens at all** — they exist on the model and hold values (they were read over RPC), but
that tenant's user may not see them. Where this pass says "Odoo's screen does not show it", that is what it means.

Fields Odoo restricts that we have **not** built, all of them already in a *Not built now* list: `autopost_bills`,
`property_inbound_payment_method_line_id`, `property_outbound_payment_method_line_id`, `last_reminder`,
`property_product_pricelist` (Contacts); `analytic_distribution` and the Analytic page (Invoices, Invoice Lines);
`bank_statements_source`, `restrict_mode_hash_table`, the *Automation* group (Journals).

## 08 · Product Categories — `product.category`

Checked 18 Sep 2026. Odoo: *Invoicing › Configuration › Product Categories*; the form of **Goods / Consumables**.

| | Odoo's screen | ERP Master |
|---|---|---|
| List | One column, *Product Category*, showing the display name; 7 rows; roots first (Expenses, Goods, Services) then each parent's children | Three columns — **Complete Name · Parent Category · # Products** — sorted Complete Name A→Z, so children follow their parent; quick filter *Parent Category* |
| Form | Title label *Category* over the name; one field, **Parent**; a *Products* stat button reading **2** | **Name**, then Parent Category \| Complete Name, **# Products** 2, then tabs Accounting · Child Categories (1) · Products (2) |
| Accounting | **Not on the screen** — the page is `groups="account.group_account_readonly"` | Accounting tab: Income Account *410000 Trade Income*, Expense Account *510000 Costs* |
| # Products | Stat button 2 for Consumables — same as ours | 2 |

**No new differences.** The two already recorded stand: the list sort (ours is the sort `_order = 'complete_name'`
asks for, which the tenant cannot do because `complete_name` is not stored there) and **# Products for a parent**
(Odoo's stat button counts the subtree — Goods reads 11 there, 0 here; the help text promises ours).

## 09 · Chart of Accounts — `account.account`

Checked 18 Sep 2026. Odoo: *Invoicing › Configuration › Chart of Accounts*; the form of **124000 Account
Receivable**.

| | Odoo's screen | ERP Master |
|---|---|---|
| List | **Code · Account Name · Type · Payment Reconciliation**, 87 rows, code order — the same four columns in the same order as ours, row for row | The same, 87 accounts plus the two `TEST` ones; *Chart of Accounts* and *Archived* views |
| Narrowing | A left rail — **All · 1 · 2 · 3 · 4 · 5 · 9** — a search panel on `root_id`, the code's first digit | No rail; quick filters **Type** (a dropdown) and **Internal Group** (a search box) |
| Form | Code and Account Name as the title pair, one tab *Accounting*: Type · Default Taxes · Fiscal Category · Tags on the left, Non Trade · Payment Reconciliation (with a *→ Reconcile* link) · **Active as a toggle** · Parent Account on the right, then a *Description* block; a **Balance** stat button reading 13,483.54 | Code \| Account Name · Display Name · Type \| Internal Group · Payment Reconciliation \| Non Trade · Parent Account · Description, with **Archive / Unarchive** buttons in place of the Active toggle |

**No new differences.** Everything on Odoo's form that is missing from ours is already in *Not built now* — Default
Taxes (bundle 6), Fiscal Category, Tags, the Balance stat button, the → Reconcile link and **the root side panel**
("the code sort already lines them up"). Active behind two buttons is the house pattern, recorded in §1.

**One open question is now answered.** §3's third point said the *Internal Group* quick filter was expected to
render as a search box rather than a list of the six groups, "pending the UI". It does: on the worksheet's own
screen **Type** is a dropdown reading *Please select* and **Internal Group** is a text box reading *Search*. So
Odoo's five internal-group filters (Equity · Assets · Liability · Income · Expenses) are reached here by typing,
and the Type dropdown covers Odoo's other two (Receivable · Payable) by picking.

## 02 · Units & Packagings — `uom.uom`

Checked 18 Sep 2026, and **this one had never been seen**: when the worksheet was written the tenant appeared to
have no screen for units, so test 19 was answered from the extract alone. It has one. *Sales › Products › Units &
Packagings* is there, the units setting (`group_uom`) is on, and the list and form both render.

| | Odoo's screen | ERP Master |
|---|---|---|
| List | **Unit Name · Contains · Reference Unit** with a drag handle, 14 units: Minutes, Units, Hours, mm, m², ml, g, KWH, Pack of 6, Days, m, L, kg, t | The same three columns and the same 14 units (plus three `TEST` ones) |
| Contains | **Blank** for a unit that is its own reference (Units, Hours, mm, m², ml, g, KWH); *0.017 Hours* for Minutes, *6.000 Units* for Pack of 6 | **1** where Odoo shows blank — the recorded difference: a HAP table cannot empty one cell |
| Order | `sequence, relative_uom_id, id` — within the same sequence the tenant's own order (Units, Hours, mm, m², ml, g, KWH) | Sequence, then **Unit Name**, so the same block reads g, Hours, KWH, m², ml, mm, Units. Recorded in §1 |
| Form | **Unit Name** · **UN/ECE Code** (MIN) · **Quantity** 0.01667 *Hours*; a *Packaging Barcodes* stat button | Unit Name · **Contains** \| Reference Unit, with Archive / Unarchive |

**One new difference, and it is a label.** Odoo's form calls the ratio **Quantity**; only its list header calls it
*Contains*. Ours says Contains in both places. The field, its help text and its value are the same;
`10-payment-terms.md` set the house rule that a label follows Odoo's form, so this is worth fixing when the
worksheet is next touched — it is cosmetic and nothing depends on it.

Everything else on Odoo's form is already in *Not built now*: **UN/ECE Code** (`unece_code`, e-invoicing) and the
**Packaging Barcodes** button (`product.uom`).

**A correction to §3's test 19.** It reads "the tenant does not show a Units & Packagings menu (its units setting
is off), so there is no screen to compare". The menu is there and active, `group_uom` is on, and the comparison
above is the screen-to-screen one that test was waiting for. What had really happened is the trap below.

### The trap that hid three screens

**Odoo does not render in a background tab.** Its client waits for an animation frame, and Chrome gives none to a
tab that is not visible, so the page stops after its top bar and control panel: `document.visibilityState` reads
*hidden*, `main.o_content` is empty, and every screenshot is a dark rectangle. Nocoly's own app renders in the
same state, which is why only the Odoo side ever looked broken. **A screenshot forces one frame**, so the recipe
is *navigate → wait → screenshot → screenshot*: the first is blank and pays for the paint, the second is the
page. Three "the tenant has no screen for this" notes — Units & Packagings here, and Products and Product
Variants below — were this trap, not the tenant. Recorded in `BUILDING.md`.

## 03 · Products — `product.template`

Checked 18 Sep 2026. Odoo: *Invoicing › Customers › Products*, the kanban and the forms of **27" 4K Monitor**
(2 variants) and **[CONS-0001] A4 Copy Paper** (1 variant).

| | Odoo's screen | ERP Master |
|---|---|---|
| Default view | Kanban cards: name, "2 Variants" where there are any, price, internal reference, a *Sales* filter chip | The *Products* gallery: name, Internal Reference, Sales Price, Unit — plus *List* and *Archived* views and a **Category** quick filter |
| Form head | ☆ beside the name, then ☑ Sales ☑ Purchase and the image; stat buttons Variants · Documents · Sold | Name, then **Favorite** (a checkbox) \| Sales \| Purchase, then Image — HAP has no star and no stat buttons (§1) |
| Tabs | General Information · Attributes & Variants · Sales · Prices · Inventory | General Information · Sales · Inventory · **Accounting** (bundle 2; in Odoo the same fields sit on an *Accounting* page behind `group_account_readonly`) |
| General Information | left Product Type (Goods · Service · Combo) · Invoicing Policy · Track Inventory · Free To Use · Malaysian classification code; right Sales Price *per Units* · Sales Taxes · Cost *per Units* · Purchase Taxes · Category · Reference · Barcode · Tags · Malaysian Customs Tariff Code; then *Internal Notes* | Product Type \| Sales Price · Unit \| Cost · Category \| Internal Reference · Internal Notes — the pairing §1 describes, with Category where bundle 1 put it |
| A product with several variants | **Cost and Reference disappear from the form** — they belong to the variant | Not applicable: one variant per product (04) |

**No new differences.** Everything of Odoo's that is missing is in *Not built now* or a later bundle: Invoicing
Policy, Track Inventory and Free To Use (stock), Sales and Purchase Taxes (bundle 6), Barcode, Tags, the two
Malaysian e-invoicing codes, the Attributes & Variants and Prices tabs, and the three stat buttons.

**The two divergences Teh Li Wei introduced are still there**, and Odoo's own defaults confirm them:
`default_get` on the tenant answers `sale_ok: true`, **`purchase_ok: true`**, `type: consu`, `uom_id: Units`,
`list_price: 1` — so Odoo ticks **Purchase** on a new product where ours leaves it clear, and Odoo has no
uniqueness on a product's name where ours refuses a duplicate. Both are with him; nothing new to add.

## 04 · Product Variants — `product.product`

Checked 18 Sep 2026 — the second worksheet that had only ever been compared against data.

**There is no Product Variants menu on the tenant.** The model's only window action is the *Variants* stat button
on a product, and opening it on its own (`/odoo/action-282`) throws Odoo's *Oops!* dialog — its context reads
`search_default_product_tmpl_id: active_id`, and there is no active id when it is reached directly. Through the
button it works, and that is the screen compared here.

| | Odoo's screen (the 27" 4K Monitor's two variants) | ERP Master |
|---|---|---|
| Columns | **Name · Attributes · Sales Price · Cost · Barcode · On Hand · Free To Use · Unit ·** *View* | **Display Name · Sales Price · Cost · Barcode · Unit**, with quick filters Product Type · Sales · Purchase · Favorite and an *Archived* view |
| Rows | Two variants of one product — *Silver* RM 1,950.00 and *Black* RM 1,890.00, the attribute's extra price included | One variant per product, named "[Internal Reference] Name" — the recorded design: attributes are not built, so a product has exactly one variant |
| Scope | The list is always filtered to one product | The whole catalogue, 19 rows with the `TEST` ones |

**No new differences.** *Attributes* has nothing to show without the Attributes & Variants tab; *On Hand* and
*Free To Use* are stock. The one thing worth writing down is the missing menu: a reviewer who tries to open
Product Variants in Odoo will get an error dialog, and should open a product and press **Variants** instead.

## 01 · Contacts — `res.partner`

Checked 18 Sep 2026, re-checked after bundles 2 and 3 added fields to it. Odoo: *Contacts*; the form of **Klinik
Kesihatan Damansara**, one of the three customers seeded into the app.

| | Odoo's screen | ERP Master |
|---|---|---|
| List | Name · Email · Phone · Activities · Country · Last Reminder, 11 contacts, with sale and invoice badges | Display Name · Email · Phone · Country; quick filters Salesperson · Company · Country; *Contacts*, *Kanban* and *Archived* views |
| Form head | Avatar, name, *Company Employer*, email, phone; Address block; **Tax ID** with a **+** that offers Company ID and DUNS; **SST** and **TTx** under it; right Job Position · Website · Tags; six stat buttons | Name · Company · Email \| Phone · Job Position \| Website · **Tax ID \| Company ID** · **DUNS** · Address · Image · Display Name |
| Tabs | Contacts · Sales & Purchase · Invoicing · Notes | The same four |
| Sales & Purchase | *SALES*: Salesperson **Casimir** · Pricelist *Default (MYR)* · **Payment Terms 21 Days** · Payment Method · Incoterm — *PURCHASE*: Payment Terms · Payment Method | *Sales*: Salesperson **Casimir Chiong Ming Yuan** · **Customer Payment Terms 21 Days**; *Purchase*: Vendor Payment Terms |
| Invoicing | *GENERAL*: Bank accounts · Ignore Abnormal Invoice Amount · Ignore Abnormal Invoice Date — *CUSTOMER INVOICES*: Invoice sending · eInvoice format · Routing ID. **Account Receivable and Account Payable are not shown** (`account.group_account_user`) | **Account Receivable 124000 · Account Payable 221100** — the fields Odoo's own screen hides from this user, built by bundle 2 and hidden from the Invoicing and Accounting Read-only roles |

**No new differences.** SST and TTx are in *Not built now* with the Malaysian e-invoicing localisation; Company ID
and DUNS are the two identifiers behind Odoo's **+**, shown here as plain fields, which §1 already says; Pricelist,
Payment Method, Incoterm, bank accounts and the abnormal-invoice switches are all listed there too.

**Bundle 3 lands where Odoo puts it**: the customer's term is under *Sales* and the vendor's under *Purchase*, and
the value on this contact — **21 Days** — is the same on both screens.

## 05 · Journals — `account.journal`

Checked 18 Sep 2026; the earlier comparison had been partial. Odoo: *Invoicing › Configuration › Accounting ›
Journals*; the form of **Sales**.

| | Odoo's screen | ERP Master |
|---|---|---|
| List | **Journal Name · Type · Sequence Prefix · Default Account**, 7 journals with a drag handle | The same four columns, the same 7 journals (plus two `TEST` ones) and a *Type* quick filter — the Default Account column arrived with bundle 2 and matches Odoo's list |
| Order | Sales · Purchases · Bank · Miscellaneous Operations · **Exchange Difference · Cash Basis Taxes** · Tax Returns | … · **Cash Basis Taxes · Exchange Difference** · Tax Returns |
| Account names | *Trade Income*, *Costs*, *Bank* — the name alone | *410000 Trade Income*, *510000 Costs*, *120001 Bank* — code and name, the one Display Name this app gives an account (09's *Not built now*) |
| Form | Journal Name · Type · Sequence Prefix; tabs **Journal Entries · Advanced Settings**; Journal Entries holds **only Dedicated Credit Note Sequence** | Journal Name · Type \| Sequence Prefix · **Sequence** · the same two tabs; Journal Entries holds **Default Account** *410000 Trade Income*, Dedicated Credit Note Sequence, then the remark block |

**No new differences.** The one thing the two lists disagree about is already §3's difference 2: the tenant gives
EXCH, CABA and TAX the same sequence — 10 — and Odoo falls back on the record id, which puts Exchange Difference
before Cash Basis Taxes, while ours breaks the tie on Journal Name. Seen on both screens today, exactly as written.

The rest confirms what §1 says: **Sequence** is a plain field here because a HAP table has no drag handle, and the
five accounts Odoo hides from this tenant's user (`account.group_account_readonly`) are the ones bundle 2 built and
hid from the Invoicing role — Odoo's Journal Entries tab shows casimir a single checkbox.

## 06 · Invoices — `account.move`

Checked 18 Sep 2026 — the third worksheet that had only been compared against data. Odoo: *Invoicing › Customers ›
Invoices*; the form of **INV/2026/00001**, posted, for Klinik Kesihatan Damansara.

| | Odoo's screen | ERP Master |
|---|---|---|
| List | **Number · Customer · Invoice Date · Due Date · Last Reminder · Tax Excluded · Total · Amount Due · Status**, 7 documents, money columns **totalled at the foot**, an *Invoices or Receipts* filter chip | **Number · Customer / Vendor · Invoice Date · Due Date · Journal · Untaxed Amount · Total · Amount Due · Status**; views *Invoices · Bills · Journal Entries*; quick filters Type and Status |
| A draft's number | Odoo prints **`/`** | The word **Draft** in the field — §1's recorded choice |
| Dates | Relative — *4 days ago*, *In 14 days*, *Next month* | The date itself |
| Form head | Send · Print · Pay · Preview · Credit Note · **Reset to Draft**, and a Draft → **Posted** status bar; "Customer Invoice" over the number | **Confirm · Cancel · Reset to Draft** (the first two greyed on a posted document) and **Status** as a read-only field |
| Body | Customer and its address · Delivery Address; right **Invoice Date** *Sep 11* and **Payment terms** *21 Days* | Status \| Type · Number · Customer / Vendor \| Invoice Date · Delivery Address \| Accounting Date · **Due Date \| Payment Terms** · Journal \| Tax mode |
| Tabs | **Invoice Lines · Other Info · MyInvois** | The same three |
| Lines | Product · Quantity · Unit · Price · Taxes · Amount, each with its description beneath; then Untaxed Amount **RM 11,432.00** and SST 10% RM 1,143.20 | The 07 subtable — Sequence · Display Type · Product · Label · Account · Quantity · Unit · Unit Price …, then Untaxed Amount · Tax · Total · Amount Due |

**The payment-terms rule is confirmed on both screens.** Odoo's form shows *Payment terms* and **no Due Date**
(`invisible="invoice_payment_term_id"`); ours does exactly the same — INV/2026/00010, with 30 Days, shows the term
and no date, and INV/2026/00003, with no term, shows an empty Due Date beside an empty Payment Terms. That is
bundle 3's *Due Date or Payment Terms* rule behaving as Odoo's attribute does.

**Two new differences, both small and both cosmetic.**

1. Odoo's list header for `amount_untaxed` reads **Tax Excluded**; ours reads **Untaxed Amount** — Odoo's own
   field label, overridden in its list the way *Contains* overrides *Quantity* on a unit.
2. Ours carries a **Journal** column where Odoo's list carries **Last Reminder** and keeps Journal optional-hidden;
   and Odoo **totals** the three money columns at the foot of the list, which ours does not.

## 07 · Invoice Lines — `account.move.line`

Checked 18 Sep 2026 with the same two documents.

Odoo has **no standalone list of invoice lines** — only the columns inside an invoice and the *Journal Items*
list. Inside the invoice its columns are *Product · Quantity · Unit · Price · Taxes · Amount*, with each line's
description on a second row under the product. Ours are *Sequence · Display Type · Product · Label · Account ·
Quantity · Unit · Unit Price …* — §1's order, leading with the two fields Odoo handles with a drag handle and a
row type. The worksheet's own **Lines** view (Number · Label · Account · Product · Quantity · Unit · Unit Price …)
is ours, standing in for Journal Items.

**No new differences.** The seeded lines add to the same figures as the tenant's, which 07's test 20 had already
proved against these very documents.

## 10 · Payment Terms — `account.payment.term`

Checked 18 Sep 2026, the day after it was built. Odoo: *Invoicing › Configuration › Payment Terms*; the form of
**2/7 Net 30**, the one term with an early-discount line.

| | Odoo's screen | ERP Master |
|---|---|---|
| List | One column, *Payment Terms*, with drag handles — Immediate Payment · 15 Days · 21 Days · 30 Days · 45 Days · End of Following Month · 10 Days after End of Next Month · 30% Now, Balance 60 Days · 2/7 Net 30 · 90 days, on the 10th | The same ten in the same order, plus **Description on the Invoice** as a second column, the five `TEST` terms and an *Archived* view |
| Form head | Payment Terms; **Early Discount ☑ · 2.00 % if paid within · 7 days** on one line; *Reduced tax: On early payment* | Payment Terms · Early Discount ☑ · **Discount %** 2.00 \| **Discount Days** 7 · Reduced tax *On early payment* — the same fields, two labelled boxes instead of a sentence |
| Lines | *DUE TERMS*: Due **100.000000 Percent**, After **30 Days after invoice date**, and *Add a line* | *Due Terms(1)*: Due · **Value** 100 · Percent · After **30** · Delay Type *Days after invoice date* · Days on the next month, and *Add a row* |
| Preview | *PREVIEW*: Show installment dates ☑, an example of 1,000.00 on Sep 18, then **"Payment terms: 30 Days, 2% Early Payment Discount under 7 days"**, the discount RM 980.00 before 09/25/2026 and the installment due 10/18/2026 | Show installment dates ☑ · **Description on the Invoice**: *"Payment terms: 30 Days, 2% Early Payment Discount under 7 days"* — Odoo's own sentence, computed the same way · Sequence 10 |

**No new differences.** The live example — Odoo's *1,000.00 on Sep 18* with the dates it would fall on — is the
one part of Odoo's screen ours does not have, and it is already in *Not built now*: it is a preview widget, not a
stored field. Everything the term is made of matches, name for name and value for value.

## Workflows and core functions

The behaviours behind the worksheets were checked the same way — Odoo's screen beside ours — wherever the tenant
can show them without being written to.

| Behaviour | What Odoo's screen shows | In ERP Master |
|---|---|---|
| **Numbering** (Invoices' *Confirm*) | Posted documents read **INV/2026/00001 · 00002 · 00003**, drafts read `/` | Confirm writes `<journal prefix>/<year>/<5 digits>`, one past the highest already issued — INV/2026/00010 was produced this way on 17 Sep |
| **Due Date from the term** (automation D, and the *Due Date or Payment Terms* rule) | The invoice form shows **Payment terms 21 Days** and **no Due Date**; the list's due dates are the terms' dates | The same: a document with a term shows the term alone, one without shows an empty Due Date. INV/2026/00010's 30 Days gives 2026-10-20 from 2026-09-20 |
| **The term on a contact** (automation C) | Klinik Kesihatan Damansara carries **Payment Terms 21 Days** under *Sales & Purchase › SALES* | The same contact, the same tab, **Customer Payment Terms 21 Days** |
| **Complete Name** (Product Categories' formula chain) | The category tree reads *Goods / Consumables*, and its form shows Parent *Goods* | *Goods / Consumables*, computed from the parent's own Complete Name |
| **Payment Reconciliation follows Type** (accounts automation A) | 124000 Account Receivable has the box ticked; so do the other receivable and payable accounts | The same 87 accounts, the same boxes |
| **Product → variant** (workflows A/B/C) | A product's *Variants* button opens its variants; a template with several hides Cost and Reference, which belong to the variant | One variant per product, and Products is the master of code, cost, weight, volume and favourite |

Three behaviours could **not** be compared, and none of them is a gap in the build: Journals' **archive guard**
(Odoo's refusal message is copied from its source; firing it on the tenant would mean writing there), the invoice
**line account fill** (automation B, same reason), and the **role-by-role field hiding**, which needs a second
Odoo user — casimir is the only one, and the groups it lacks are exactly what the top of this page describes.

## 11 · Countries — `res.country`

Checked 18 Sep 2026, the day it was built — the first worksheet compared against Odoo as part of its own UI test
rather than afterwards. Odoo: *Contacts › Configuration › Localization › Countries*; the form of **Malaysia**.

| | Odoo's screen | ERP Master |
|---|---|---|
| List | **Country Name · Country Code**, 251 rows, name order, and **no New button** — the list carries `create="0" delete="0"` | The same two columns and the same 251 countries (plus the build's `TEST Country`); New belongs to the app Administrator alone, which is how Roles says the same thing |
| Order | Afghanistan … Zambia, Zimbabwe, **Åland Islands** — the tenant's collation sorts Å after Z | Afghanistan, **Åland Islands**, Albania … — the one row of 251 where the two disagree |
| Form | Country Name · **Currency** · Country Code on the left; Country Calling Code · Vat Label · Zip Required · State Required on the right; the **flag**; *Advanced Address Formatting* (Input View · Layout in Reports · Customer Name Position), which shows here only because the tenant's user holds `base.group_no_one`; then the **States** list | Country Name \| Country Calling Code · Country Code \| Vat Label · Zip Required \| State Required, then the remark block naming every one of those |
| Malaysia | *Malaysia · MYR · MY · 60 · no VAT label · ZIP required · state not required*, sixteen states from Johor | The same six values |
| On a contact | Country is a dropdown, `no_open` and `no_create`, and setting it **clears a State** that belongs elsewhere | A dropdown that **does** open the country and **does** offer + Record; State is still Text, so nothing to clear until bundle 5 |

**No surprises.** Everything of Odoo's that is missing is in *Not built now* — the currency, the flag, the three
address-formatting fields, the country groups and the states. The four differences the UI test found are in §3 of
the worksheet; the sharpest is that Odoo's picker cannot invent a country and HAP's can, which Roles rather than
the field is what settles here.

## 12 · States — `res.country.state`

Checked 18 Sep 2026, the day it was built. Odoo: *Contacts › Configuration › Localization › **Fed. States***; the
state picker on a contact, tested three ways over RPC.

| | Odoo's screen | ERP Master |
|---|---|---|
| List | **State Name · State Code · Country**, 2 102 rows, 80 to a page, **editable in place** with a *New* button; ordered `code, id`, so it reads Aveiro (PT) 01, Архангай (MN) 01, Amazonas (PE) 01, Azuay (EC) 01, Beja (PT) 02 … | The same three columns and the same 2 102 states (plus three `TEST` ones), sorted State Code then **Country Name**, with a *Country* quick filter; a state is edited in its own record |
| Form | One group: State Name · State Code · Country (`no_open`, `no_create`) | State Name \| State Code · Country \| **Display Name** — *Selangor (MY)*, Odoo's own `_compute_display_name`, read-only |
| A country's states | The editable list at the foot of the country form, State Name · State Code | The **States** tab at the foot of a country, the same two columns, newest first |
| The picker on a contact | **Every state in the world**, labelled *Selangor (MY)* — the partner form passes `default_country_id`, which `name_search` does not narrow on | The same: typing *Aceh* on a Malaysian contact offers **Aceh (ID)** |
| Country and state in step | Two onchanges: a state sets the country, a country clears a state that belongs elsewhere | Workflows E and F, both proved — and a save that changes **both** does both things at once, which Odoo's form never does (§3, difference 3) |
| One code per country | `unique(country_id, code)` — *"The code of the state must be unique by country!"*, refused by the database | **Caught, not refused.** HAP has no pair constraint, so a duplicate saves and is then marked: no key, a ticked *Duplicate code*, a workflow run stopped at its abort node, and a row in the *Duplicate codes* view until the code is mended |
| Access | `base.group_partner_manager` — a **contact manager** — creates, edits and deletes; every internal user reads | Each role's Contacts cell: Accountant and Invoicing add and edit, Read-only reads, Accounting Administrator deletes. Seen with role debugging: as *Invoicing*, States offers **+ Record** where **Countries does not** |

**No surprises.** The differences are the ones §3 records, and every one of them is HAP's shape rather than a
misreading of Odoo: the tie-break at equal code, the composite constraint, both workflows firing in one save, and
the relation list's newest-first order.
