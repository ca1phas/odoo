# 15 · UI conformance — Odoo against Nocoly, screen by screen

**Not a worksheet.** A review document, like `14-crm-conformance.md`. It records a side-by-side pass of the
casimir tenant (saas~19.4+e) against ERP Master, and — for Invoices and Invoice Lines — a **functional** pass
that actually pressed the buttons, ran the workflow, created a document and updated it.

| Date | 21 Sep 2026 |
|---|---|
| Tenant | casimir.odoo.com · Invoicing · **free trial expires in 1 day** |
| App | ERP Master `6cb4d051-a33c-4bf9-b56f-5f47f0e85dc9` |
| Method | two Chrome tabs side by side; Odoo's own `ir.ui.view` arch and `fields_get` read from the tenant over read-only RPC where a screen could not settle a question |

---

## 0 · What was covered, and what was not

| Worksheet | Lists & forms compared | Buttons · workflows · create · update exercised |
|---|---|---|
| 01 Contacts | yes | **yes** |
| 02 Units & Packagings | yes | **yes** |
| 03 Products | yes | **yes** |
| 04 Product Variants | yes | **yes** |
| 05 Journals | yes | **yes** |
| 06 Invoices | yes | **yes** |
| 07 Invoice Lines | yes | **yes** |

All seven are now covered both ways, on the owner's direction of 21 Sep — *"It should test the functionalities
of the buttons, workflows, creation, and updates as well"*. Section 4 is the functional pass on 06 and 07;
**section 6** is the functional pass on 01–05, run the same day.

---

## 1 · Defects (Invoices, worksheet 06)

### 1.1 Four controls stay editable on a posted or cancelled document

Our rule *A posted or cancelled document is closed for editing* names nine controls — Type · Customer/Vendor ·
Journal · Invoice Date · Accounting Date · Due Date · Payment Terms · Tax mode · Lines. Odoo's form carries
`readonly="state != 'draft'"` on four more that we leave open:

| Field | Odoo's attribute (read from the tenant) | Ours |
|---|---|---|
| `partner_shipping_id` **Delivery Address** | `readonly="state != 'draft'"` | editable dropdown on a posted document |
| `delivery_date` **Delivery Date** | `readonly="state != 'draft'"` | editable date picker |
| `auto_post` **Auto-post** | `readonly="state != 'draft'"` | editable dropdown |
| `auto_post_until` **Auto-post until** | `readonly="state != 'draft'"` | editable (when shown) |

Seen on the seeded **INV/2026/00001** and again on **INV/2026/00011**, posted during this pass: every other
header field rendered as plain read-only text while Delivery Address still drew its chevron.

**Fix:** add the four controls to the rule's target list in `nocoly/build/invoices.py`.

### 1.2 *Auto-post until* is shown where Odoo hides it

The tenant's arch reads `invisible="auto_post in ('no', 'at_date')"`. Our rule shows the field whenever
Auto-post is **not** *No*. Confirmed live: setting Auto-post to **At Date** made *Auto-post until* appear,
where Odoo keeps it hidden.

06 §2 quotes `invisible="auto_post == 'no'"` — that is the **19.0 repo checkout**, not the tenant. Same trap
as the Taxes form and the CRM feature groups: the repo at `7bbce824` is behind saas~19.4.

**Fix:** the rule's condition becomes *Auto-post is Monthly, Quarterly or Yearly*.

### 1.3 The Journal picker is unfiltered

Odoo's `account.move.journal_id` domain, read from the tenant with `fields_get`:

```
(company_id and [...company clauses...]) + ([('id', 'in', suitable_journal_ids)])
```

`suitable_journal_ids` narrows the list to the journals that fit the Type — a sale journal for a customer
invoice. **Our picker offers every journal**: Bank, Cash Basis Taxes, Exchange Difference, Miscellaneous
Operations, Tax Returns, and the four TEST journals.

This is not theoretical. **MISC/2026/00002** sits in our Invoices list — a sales-type document that was
confirmed while its Journal was *Miscellaneous Operations*, so Confirm numbered it from that journal's
prefix. Odoo would not have allowed the journal to be picked.

(The Invoices view itself is sound: its quick filter Type = *Journal Entry* returns **0 rows**, so no journal
entry leaks into it.)

**Fix:** a picker filter on the Journal relation, the same shape as `taxes.py`'s `tax_picker` — Journal Type
is Sales for the three customer types, Purchase for the three vendor types.

### 1.4 Auto-post is offered on receipts

Odoo: `invisible="move_type in ('out_receipt', 'in_receipt')"`. Ours shows Auto-post on every Type. Minor,
one more clause on an existing rule.

---

## 2 · Gaps that are not defects

| # | What | Status |
|---|---|---|
| 5 | **No Journal default on create.** Odoo defaults a customer invoice to the Sales journal; our create form leaves the required field empty | new — worth adding with 1.3 |
| 6 | **No Salesperson default.** Odoo defaults `invoice_user_id` to the current user; ours shows an empty **+** | new, minor |
| 7 | Picking a product fills **Account** and **Taxes** (automation B) but not **Label**, **Unit** or **Unit Price**. Odoo's onchange fills all five | Label and Unit are recorded in 07 §*Not built now*; **Unit Price is not recorded anywhere** — add it |
| 8 | Automations run **on save**, so Payment Terms appears only after Submit; Odoo fills it the moment the customer is picked | inherent to HAP; already understood, not written down |
| 9 | The four roll-up amounts need a **refresh** before they show; they read 0.00 immediately after a line is saved | inherent to HAP roll-ups |

---

## 3 · Presentation differences

**Invoices list.** Odoo 7 records, ours 25.

| Odoo | Ours |
|---|---|
| Number · Customer · Invoice Date · Due Date · **Last Reminder** · **Tax Excluded** · Total · Amount Due · Status | Number · Customer / Vendor · Invoice Date · Due Date · **Journal** · **Untaxed Amount** · Total · Amount Due · Status |
| `RM` prefix on every figure; relative dates (*In 11 days*, *7 days ago*) | bare figures; ISO dates |
| footer totals row (RM 300,721.20 · 327,176.32 · 324,148.52) | none |
| coloured badges, including **Paid** | plain text; no Paid (Payments bundle) |
| `/` on an unnumbered draft | the word **Draft** |
| New · Upload | **+ Record** |

**Invoice form.** Tabs match exactly — *Invoice Lines · Other Info · MyInvois*. Differences:

- Odoo puts the tax mode above the lines as a **Tax Excl. / Tax Incl.** toggle; ours is a *Tax mode* dropdown
  in the header block.
- Odoo breaks the tax down **per rate** under the lines (*SST 10%: RM 1,143.20*); ours shows one *Tax* figure.
- Odoo has smart buttons (*Journal Items*, *Sale Orders 1*) and a chatter; ours has HAP's *Comments / Log*.
- Odoo's header on a posted invoice: Send · Print · Pay · Preview · Credit Note · Reset to Draft. Ours: the
  three built buttons only — which is the documented Phase 1 scope.

**Line grid.**

| Odoo | Ours |
|---|---|
| Product · Label (italic second line) · Quantity · Unit · Price · Taxes · Amount | Sequence · Display Type · Product · Label · Account · Quantity · Unit · Unit Price · Discount (%) · Taxes · Subtotal · Total |
| optional columns: Malaysian classification code, Deferred Date, Disc.% | column picker over the same set |
| drag handles; **Add a line · Add a section · Add a note · Catalog** | a Sequence column; one **Add a row** + *Batch Operation* |

**Our *Lines* view is not Odoo's *Journal Items*.** Odoo's ledger list (17 rows, filter *Posted*) is
**Date · Journal Entry · Partner · Label · Debit · Credit · Matching**, and it holds the tax lines (*10% G*,
*8% S*), the payment-term lines and the payment entries that Odoo writes itself. Ours (39 rows) is
**Number · Label · Account · Product · Quantity · Unit · Unit Price · Discount (%) · Taxes · Subtotal · Total**
— the invoice lines a person edits, and nothing else. Double entry is out of Phase 1 by decision; the point
here is only that the two lists are not comparable and a reviewer should not expect them to be.

**A Section row keeps its figures.** Odoo's SQL constraint `check_non_accountable_fields_null` forbids a
balance on a non-accountable line. Our rule hides Product · Quantity · Unit · Unit Price · Discount (%) ·
Subtotal on the *form*, but the stored values survive and the **list still prints them** — `TEST section with
figures` shows Quantity 3.00 and Unit Price 100.00 in the Lines view. The roll-up filters on Display Type, so
no total is wrong; the display is.

---

## 4 · The functional pass — what works

Run on a document created from scratch in the UI on 21 Sep 2026 and left as
**INV/2026/00011**, Customer Reference *TEST UI run 21 Sep - delete me*.

| # | Step | Result |
|---|---|---|
| 1 | **+ Record** — defaults before touching anything | Status **Draft**, Number **Draft**, Type **Customer Invoice**, Accounting Date **2026-09-21**, Tax mode **Tax Excluded**, Payment Reference placeholder *Standard communication*, Invoice Date placeholder *Today* — all as Odoo shows them. Journal and Tax mode marked required |
| 2 | Add a row in the subtable | Sequence **10**, Display Type **Product**, Quantity **1.00** — the documented defaults |
| 3 | Pick a product (Ergonomic Office Chair) | Product set; Label, Unit, Unit Price stay empty (§2.7) |
| 4 | Submit | *Submitted successfully*; the record sorts to the top of the list (Accounting Date descending) |
| 5 | **Automation C** | Payment Terms filled itself with **21 Days** from Klinik Kesihatan Damansara |
| 6 | Rule · Due Date or Payment Terms | **Due Date disappeared** once Payment Terms held a value — as on Odoo's own form |
| 7 | **Automation B** | Account **410000 Trade Income** and Taxes **10% G** put on the line from the product |
| 8 | Update · Quantity 2, Unit Price 899 | Subtotal **1,798.00** computed live in the grid |
| 9 | Roll-ups (after refresh) | Untaxed **1,798.00** · Tax **179.80** · Total **1,977.80** · Amount Due **1,977.80** — cent for cent what Odoo computes for 2 × 899 at SST 10% |
| 10 | **Confirm** | Status → **Posted**; Number → **INV/2026/00011**, one past the highest; Invoice Date → **2026-09-21**; Payment Reference → **INV/2026/00011** |
| 11 | Posted document locks | Type · Customer/Vendor · Journal · Tax mode · Invoice Date · Accounting Date · Payment Terms all render as read-only text; the subtable loses **Add a row** and **Batch Operation** and Display Type loses its required marker. (Four fields stay open — §1.1) |
| 12 | **Reset to Draft** | Status → **Draft**, **Number kept** as INV/2026/00011; fields editable again |
| 13 | **Cancel** | Dialog *"Are you sure you want to cancel this document?"* → **Back** / **Cancel document**; Status → **Cancelled**, document locked again |
| 14 | **Reset to Draft** from Cancelled | Status → **Draft** |
| 15 | Button visibility | Draft → **Confirm · Cancel** enabled, Reset to Draft greyed. Posted or Cancelled → **Reset to Draft** alone. Odoo's own header does the same: Confirm · Cancel on the STL draft, Reset to Draft without Cancel on INV/2026/00001 |
| 16 | View filter | Invoices view, quick filter Type = *Journal Entry* → **0 rows**; no journal entry leaks in |

---

## 6 · The functional pass on 01–05

Run on 21 Sep 2026, after the owner asked for the same treatment the invoices got. Every rule was tripped
deliberately, every button pressed, and a record created and updated on each worksheet. **Everything below
passed** except §6.6, which is a new defect.

### 6.1 Contacts

| # | Step | Result |
|---|---|---|
| 1 | Create form with no Company | **Address Type is not on the form** — Odoo shows it only inside the Contacts-tab form |
| 2 | Set Company = TEST QA Trading Sdn Bhd | **Address Type appears**, required, defaulting to **Contact** |
| 3 | Submit with Name empty | Refused: *Please fill in Name* on the field and the dialog **"Please correct form errors — Contacts require a name"** — Odoo's `_check_name` message verbatim |
| 4 | Save with a name | **Automation A** copied the company's **Tax ID C2584563299, Company ID 202601000001, DUNS 123456789, Street, Street 2, City, ZIP, State *Selangor (MY)* and Country *Malaysia*** |
| 5 | Display Name | *TEST QA Trading Sdn Bhd, TEST UI 21Sep Person* — composed as Odoo composes it |
| 6 | The Invoicing tab | **hidden** on the contact, **shown** on the company — the bundle-2 rule works both ways |
| 7 | **Workflow E** · set State to *Jakarta (ID)* | Country became **Indonesia** |
| 8 | **Workflow F** · set Country back to *Malaysia* | State was **cleared** |
| 9 | **Automation B** · change the company's City to *TEST Shah Alam* | The contact's City followed, and its State came back from the company |
| 10 | **Archive** | *"Are you sure that you want to archive this record?"* · Cancel / Archive → the record left the Contacts view (19 → 18) and appeared in **Archived** |
| 11 | **Unarchive** | No confirmation; Archived went back to empty |

Two things a reviewer should know. **The address workflows are asynchronous** — E and F each took about
fifteen seconds and a refresh before the change showed, where Odoo's onchange fires as you pick. And the
**State picker offers states from any country** (it offered *Jakarta (ID)* on a Malaysian contact); Odoo
narrows it by country. Both are recorded in `12-states.md`; neither is new.

### 6.2 Units & Packagings

| # | Step | Result |
|---|---|---|
| 1 | Create form | Unit Name* · Contains* (default **1**) · Reference Unit, with Odoo's help text under Contains. Active is hidden, as it should be |
| 2 | Contains = **0** | **"The conversion ratio for a unit of measure cannot be 0!"** on the field, as you type — Odoo's `_factor_gt_zero` |
| 3 | Contains = 5, no Reference Unit → Submit | Refused with **"Reference unit of measure is missing."** on Reference Unit and in the dialog — Odoo's `_check_factor` |
| 4 | Reference Unit = Units → Submit | Saved |
| 5 | Point the new unit at **itself** | Not possible — the picker returns *No matching results*; it already excludes the record. A guard tighter than the rule |
| 6 | Point **TEST Box of 10** at **TEST Crate** (which sits below it) | **"Recursion Detected."** as you type — the ORM's `_parent_store_update` message. Cancelled; nothing saved |
| 7 | **Archive** / **Unarchive** | Confirmation, then the record moved to **Archived** (16 → 17) and back |

### 6.3 Products

| # | Step | Result |
|---|---|---|
| 1 | Create form defaults | **Sales ticked**, Favorite and Purchase clear, Product Type **Goods**, Sales Price **RM 1.00**, Unit **Units**, Cost **RM 0.00** — Odoo's own defaults; Name's placeholder is Odoo's *e.g. Cheese Burger* |
| 2 | Untick **Sales** | The **Sales tab disappears**; re-ticking brings it back |
| 3 | Product Type = **Service** | The **Inventory tab disappears** |
| 4 | Cost = **−5** | **"The cost of a product can't be negative."** as you type — Odoo's `_onchange_standard_price` |
| 5 | Sales Taxes picker | Offers only sales-type, active taxes (EX · 10% G · 8% S H · 8% S · 5% G and the TEST ones) — the bundle-6 picker filter holds |
| 6 | Submit, then reopen | The tab rules survive the save |
| 7 | **Archive** / **Unarchive** | Both work, with the confirmation on Archive only |

**Two of the eight create-form leaks are confirmed here**: **# Variants** and **Variants** both render on the
Create Record form, where Odoo has no such controls on a product that does not exist yet.

### 6.4 Product Variants

| # | Step | Result |
|---|---|---|
| 1 | **Automation A** — save a new product | A variant was created for it by itself; the product read **# Variants 1** and **Variants(1)** listed it with its columns |
| 2 | **Automation B** | The variant carried **Cost RM 12.00** and **Unit Units**, copied from the product |
| 3 | The variant form | Product read-only, Favorite/Sales/Purchase read-only, and the **Inventory tab hidden** because the product is a Service — the tab rules are inherited |
| 4 | **Create** | **There is no + Record button** — create is switched off, as Odoo's variant action is |
| 5 | **Archive the variant** | The **product was archived with it** — Odoo's `action_archive` leaves no template without an active variant |
| 6 | **Unarchive the variant** | The **product was unarchived with it** — `action_unarchive` |
| 7 | **Archive the product** | The **variant was archived with it** (automation C), and unarchiving the product brought it back |
| 8 | The archived product | **# Variants 0** beside **Variants(1)** — difference 6 seen live: the count is filtered to active variants as Odoo's is, and the list cannot be filtered |

### 6.5 Journals

| # | Step | Result |
|---|---|---|
| 1 | Create form | Journal Name* · Type* · Sequence Prefix* · Sequence **10**; Type offers Odoo's six — Sales · Purchase · Cash · Bank · Credit Card · Miscellaneous |
| 2 | Sequence Prefix = **INV** | **"Duplicates are not allowed"** as you type — the code's uniqueness guard |
| 3 | **Sales** journal | Advanced Settings tab present; **Communication Type** and **Communication Standard** shown and **both required**; **Dedicated Credit Note Sequence** shown; Dedicated Payment Sequence hidden |
| 4 | **Bank** journal | **Advanced Settings tab gone**; **Dedicated Payment Sequence** shown; Dedicated Credit Note Sequence hidden; Suspense, Profit and Loss Accounts present |
| 5 | **Miscellaneous** journal | Advanced Settings present, neither dedicated sequence |
| 6 | **Archive the Sales journal** (it has draft invoices) | **Refused.** Active untouched, the journal still in the list, and a **Workflow notification "Cannot archive this journal…"** in the message centre — Odoo's `_check_auto_post_draft_entries` |
| 7 | **Archive TEST Journal** (no entries) | Succeeded; **Unarchive** brought it back |

So all five Type rules, the code guard and both branches of the draft-entry check behave as specified.

### 6.6 New defect — the abort toast is untranslated

When the draft-entry guard stops the Archive, the message that appears **on screen at that moment** is a
toast reading **中止** with a warning icon. Odoo's explanation — *"You can not archive a journal containing
draft journal entries…"* — arrives only as a Workflow notification in the message centre, which a user has to
open.

That is HAP's own workflow-abort toast, and it is not localised. `05-journals.md` §2 already says HAP has no
dialog to raise from a button workflow and that the message therefore arrives as a notification; what it does
not say is that the user's immediate feedback is a Chinese word. Either the toast needs to be suppressed, or
the worksheet needs to tell a reviewer to expect it.

## 5 · Still owed

1. **Fix §1.1–1.4** in `invoices.py` — one implementation agent.
2. ~~The functional pass on 01–05~~ — **done on 21 Sep 2026, section 6.** It raised one new defect (§6.6,
   the untranslated abort toast) and confirmed two of the eight create-form leaks on Products.
3. **Record §2.7** (Unit Price is not filled from the product) in 07's *Not built now*.
4. **Test data.** Ours holds 25 invoices to Odoo's 7 and 39 invoice lines; the Journal picker shows four TEST
   journals and the Product picker several TEST products. A clean-up needs the owner's approval, as does
   deleting **INV/2026/00011**, left as a Draft by this pass.
5. **The trial.** casimir's banner said the free trial expires **in 1 day** on 21 Sep. Anything else that has
   to be read off the tenant should be read now.
