# 10 · Payment Terms

| | |
|---|---|
| Nocoly app | ERP Master · menu group **Invoicing**, after Journals — Odoo's *Configuration ▸ Invoicing ▸ Payment Terms* |
| Worksheets | **Payment Terms**, and **Payment Term Lines** mounted inside it as the *Due Terms* table |
| Odoo models | `account.payment.term`, `account.payment.term.line` |
| Reference | **casimir.odoo.com — Odoo saas~19.4+e**: both models' fields by module, constraints, defaults, every view's raw arch, the window action and menu, the decimal precision, all 10 terms and 11 lines, every field in the database that points at either model, the invoice-form and contact-form arch that places them, and the payment terms of every invoice, contact and sales order — extracted read-only to `nocoly/reference/odoo-19.4/account.payment.term.md`, with the data in `nocoly/data/casimir-payment-terms.json`. Behaviour the tenant cannot show — the constraints, the line defaults, how a term dates an invoice, how a company's terms reach its contacts — is read from the Odoo 19.0 source in this repo: `addons/account/models/account_payment_term.py`, `account_move.py`, `partner.py`, `odoo/addons/base/models/res_partner.py` |
| Phase | 1 — **bundle 3 of 6** (Product Categories · Chart of Accounts · Payment Terms · Countries · States · Taxes) |
| Status | §1 written 17 Sep 2026 · built and self-checked through the CLI the same day (§2) · **UI-tested 17–18 Sep 2026: 21 of 22 pass, 1 fails** (§3) · ready for review — the two rules standing on roll-ups are built and **disabled**, a HAP roll-up not following unsaved subtable rows · each invoice is dated once since the *trigger other workflows* switch (§2) · the Invoices text stand-in was deleted after its three values were carried into the relation and read back |

A payment term says when an invoice falls due: "30 Days", "End of Following Month", "30% Now, Balance 60 Days". The
tenant carries the 10 terms Odoo's chart template installs. This bundle builds the table of terms with its lines,
and then **replaces the text stand-in on Invoices** with a real relation — the first bundle that deletes something,
under the owner's standing rule of 16 Sep (`DECISIONS.md`): create the relation, carry the values, read them back,
delete the text field. Invoices gain what the term is for: **the Due Date is computed from it**, and the term comes
from the customer or vendor. Contacts gain Odoo's **Customer and Vendor Payment Terms**.

It stops short of installments. Odoo turns a term into one receivable or payable journal item per installment,
each with its own amount and date; that is double entry, which is not built. Here a term gives an invoice its due
date — the latest installment's date, which is what Odoo's Due Date is too.

## 1 · Requirements

### Fields — Payment Terms

Labels are Odoo 19.4's; aliases are Odoo field names. Descriptions are Odoo's `help`, verbatim, where it has one.

| # | Field | Odoo field | Nocoly type | Required | Default | Notes |
|---|---|---|---|---|---|---|
| 1 | Payment Terms | `name` | Text · **title field** | yes | — | Placeholder "e.g. 30 days" |
| 2 | Early Discount | `early_discount` | Checkbox | — | unchecked | |
| 3 | Discount % | `discount_percentage` | Number, 2 decimals | — | 2 | Odoo's help. Shown only with Early Discount |
| 4 | Discount Days | `discount_days` | Number, integer | — | 10 | Odoo's help. Shown only with Early Discount |
| 5 | Reduced tax | `early_pay_discount_computation` | Dropdown: **On early payment · Never · Always (upon invoice)** | — | On early payment | Odoo's field is *Cash Discount Tax Reduction*; its form labels it "Reduced tax:" and that is the label here. Odoo's default comes from the company's country — Belgium Always, the Netherlands Never, everywhere else On early payment — so Malaysia's is fixed. Shown only with Early Discount |
| 6 | Due Terms | `line_ids` | **Subtable** — the Payment Term Lines worksheet | — | — | Odoo's group title. Columns **Due · Value · After · Delay Type · Days on the next month**, in that order. The heading may be hidden if the tab or divider above already says *Due Terms* |
| 7 | Show installment dates | `display_on_invoice` | Checkbox | — | checked | Tells the printed invoice to list the installments. Kept because it is on Odoo's form and every term carries it; nothing reads it yet |
| 8 | Description on the Invoice | `note` | Rich text | no | — | Placeholder "Description on invoice (e.g. Payment terms: 30 days after invoice date)". The printed invoice's wording; carried from the tenant as it is (`<p>Payment terms: 30 Days</p>`) |
| 9 | Sequence | `sequence` | Number, integer | yes | 10 | Odoo orders terms by dragging a handle in its list. HAP has no handle, so the number is on the form, last, with the description "Terms are listed by this number, lowest first — Odoo sets it by dragging the term in its list." |
| 10 | Active | `active` | Checkbox | — | checked | **Hidden.** Set by Archive / Unarchive; the two views filter on it |
| — | Percent total | helper | **Roll-up (type 37)** of *Due* over the Due Terms rows whose *Value* is Percent, sum | — | — | **Hidden.** Feeds the first rule below |
| — | Line count | helper | **Roll-up (type 37)**, count of the Due Terms rows | — | — | **Hidden.** Feeds the second rule below |

### Fields — Payment Term Lines

| # | Field | Odoo field | Nocoly type | Required | Default | Notes |
|---|---|---|---|---|---|---|
| 1 | Payment Terms | `payment_id` | Relation → Payment Terms (single), the subtable's back-relation | yes | — | Created by the mount (`BUILDING.md`). Not a column of the subtable |
| 2 | Due | `value_amount` | Number | — | — | Odoo's help "For percent enter a ratio between 0-100." Odoo keeps **6 decimals** (decimal precision *Payment Terms*): use 6 if HAP can hide trailing zeros; otherwise 2, and say so in §2 |
| 3 | Value | `value` | Dropdown: **Percent · Fixed** | yes | Percent | Odoo's help |
| 4 | After | `nb_days` | Number, integer | — | 0 | Odoo's field is *Days*; its list heads the column *After*, and the column is what people see |
| 5 | Delay Type | `delay_type` | Dropdown: **Days after invoice date · Days after end of month · Days after end of next month · Days end of month on the** | yes | Days after invoice date | |
| 6 | Days on the next month | `days_next_month` | Number, integer | — | 10 | Odoo stores two characters and checks they make a number from 0 to 31; a Number field makes "not a number" impossible, so one rule is left (below). Shown only for *Days end of month on the* |
| — | Display name | helper | Function formula, text · **title field** | — | — | "100 Percent · 30 · Days after invoice date" — Due, Value, After and Delay Type, so a line reads as itself wherever HAP shows its title. Read-only and hidden on create ("100") |

Payment Term Lines is **hidden from the sidebar** if HAP lets a worksheet be hidden there — Odoo gives the lines no
menu. If HAP cannot, it takes an ordinary entry after Payment Terms, as Invoice Lines did, and §2 says so.

### Form layout — Payment Terms

| Odoo 19.4 | Nocoly |
|---|---|
| *Archived* ribbon | HAP shows nothing; the Archived view and the Unarchive button say it |
| h1: Payment Terms | Payment Terms (12) |
| Early Discount · "Discount % % if paid within Discount Days days" · "Reduced tax:" | Early Discount (12) · Discount % \| Discount Days · Reduced tax (6) |
| Group *Due Terms*: the editable line list | Due Terms, full width |
| Group *Preview*: Show installment dates · Example amount on date · Description on the Invoice · the installment preview | Show installment dates (12) · Description on the Invoice, full width — the example and the preview are not built |
| — | Sequence (6) |

No tabs: Odoo's form has none.

### Rules — Payment Terms

| Rule | Type | When | Effect | Odoo source |
|---|---|---|---|---|
| The discount is set only for an early discount | interaction | Early Discount is unchecked | hide **Discount %**, **Discount Days**, **Reduced tax** | `invisible="not early_discount"` |
| The percentages must add up to 100 | validation | Percent total ≠ 100 (an empty total included) | "The Payment Term must have at least one percent line and the sum of the percent must be 100%." | `_check_lines` |
| An early discount needs a single line | validation | Early Discount is checked **and** Line count > 1 | "The Early Payment Discount functionality can only be used with payment terms using a single 100% line." | `_check_lines` |
| An early discount must be positive | validation | Early Discount is checked **and** Discount % ≤ 0 (empty included) | "The Early Payment Discount must be strictly positive." | `_check_lines` |
| An early discount needs days | validation | Early Discount is checked **and** Discount Days ≤ 0 (empty included) | "The Early Payment Discount days must be strictly positive." | `_check_lines` |

**The first two rules stand on a roll-up seeing rows not yet saved.** Whether HAP's roll-up over a subtable follows
the rows being edited in the open form is not something the CLI can show. Build both; record their ids in §2 so
they can be disabled at once if the UI test finds that a new term with correct lines is refused.

### Rules — Payment Term Lines

| Rule | Type | When | Effect | Odoo source |
|---|---|---|---|---|
| Days on the next month only for "Days end of month on the" | interaction | Delay Type is not *Days end of month on the* | hide **Days on the next month** | `invisible="not display_days_next_month"` |
| A percentage lies between 0 and 100 | validation | Value is Percent **and** (Due < 0 **or** Due > 100) | "Percentages on the Payment Terms lines must be between 0 and 100." | `_check_percent` |
| The days added lie between 0 and 31 | validation | Days on the next month < 0 **or** > 31 | "The days added must be between 0 and 31." | `_check_valid_char_value` |

Whether a line worksheet's own rules act on its rows inside the parent's subtable is also a UI question (07's rule
was proved on the line form). §2 reports what the build could see; the UI test settles it.

### Buttons — Payment Terms

| Button | Shown when | Does | Confirmation |
|---|---|---|---|
| Archive | Active is checked | Active → unchecked | "Are you sure that you want to archive this record?" · Archive / Cancel |
| Unarchive | Active is unchecked | Active → checked | none |

### Views

| Worksheet | View | Type | Shows | Odoo 19.4 |
|---|---|---|---|---|
| Payment Terms | Payment Terms — opens first | table | Active terms. Columns **Payment Terms · Description on the Invoice**; sorted **Sequence ascending, then created ascending** (Odoo's `sequence, id`). If a HAP view holds one sort only, Sequence, and §2 says which order ties come in | The list is the handle and the name; the kanban card is the name and the description |
| Payment Terms | Archived | table | Inactive terms, the same columns and sort | The *Archived* filter |
| Payment Term Lines | Lines | table | Every line. Columns **Payment Terms · Due · Value · After · Delay Type · Days on the next month**, sorted by Payment Terms then created | — (Odoo has no list of lines) |

### What this bundle brings to the worksheets already built

Every payment-term field below is a **one-way** Relation → Payment Terms (single, dropdown) — no reverse field on
Payment Terms — whose picker lists **active terms only** and shows the name. None is required, as none is in Odoo.

#### Invoices (06) — the text stand-in is replaced

| Step | Detail |
|---|---|
| 1 · Create | **Payment Terms** (`invoice_payment_term_id`), placeholder "Payment Terms", no description — Odoo's field has no help, and the stand-in's description goes with the stand-in. It takes the text control's place: **Due Date \| Payment Terms**, row 4, right half. The text control holds the alias `invoice_payment_term_id` until step 4, so the relation gets it afterwards |
| 2 · Carry | The three documents that carry a term, by Customer Reference: **SCG-PO-88213** (Sunway draft) → *30 Days* · **KKD-2026-009** (INV/2026/00001, posted) → *21 Days* · **STL-2026-0042** (Sarawak draft) → *45 Days*. Every other document's text is empty (checked 17 Sep). The posted invoice's form is read-only in the browser only; the API writes it |
| 3 · Read back | All three through the CLI, by record id, and every other document empty |
| 4 · Delete | **The text control `6aa920d74a73a3142152e68d`** — owner-approved (DECISIONS 16 Sep), and the only thing this bundle deletes. Then give the relation its alias |
| 5 · Re-point | The rule *A posted or cancelled document is closed for editing* names the text control — put the relation in its place. **No view names it**: the Invoices, Bills and Journal Entries views' columns, quick filters and sorts were checked 17 Sep, and no workflow reads or writes it. `build/invoices.py` must stop referring to the text control, so that a re-run neither recreates it nor writes text into the relation |

**Two new rules on Invoices**, both Odoo's `due_date` block:

| Rule | Type | When | Effect | Odoo source |
|---|---|---|---|---|
| Due Date or Payment Terms | interaction | Payment Terms is not empty | hide **Due Date** | `invoice_date_due invisible="invoice_payment_term_id"` — with a term, the form shows the term and the date is computed |
| No due date on a journal entry | interaction | Type is Journal Entry | hide **Due Date** and **Payment Terms** | the block is `invisible="move_type not in (…the six invoice and receipt types…)"`. Until now Due Date showed on an entry; that was a gap in 06, closed here because it is the same block |

**C · Invoices: Payment Terms follow the Customer / Vendor** — on an invoice **created**, or its **Customer / Vendor
changed**. Odoo's `_compute_invoice_payment_term_id`:

| Type is… | Payment Terms becomes |
|---|---|
| Customer Invoice · Customer Credit Note · Sales Receipt | the contact's **Customer Payment Terms** — or, when the contact has none, **left as it is** |
| Vendor Bill · Vendor Credit Note · Purchase Receipt | the contact's **Vendor Payment Terms** — or left as it is |
| Journal Entry | empty |

An invoice with no Customer / Vendor is left as it is (guard the read: an empty search fails the whole run —
`BUILDING.md`). C then **dates the invoice** as D does, because a workflow's write starts no other workflow.

**D · Invoices: Due Date follows the Payment Terms** — on an invoice's **Payment Terms**, **Invoice Date** or
**Accounting Date changed**; after C; and after **Confirm** fills an empty Invoice Date with today (Odoo's `_post`
does, and the date recomputes from it — so Confirm must run it too). Only when Payment Terms is set; with no term
the Due Date is left as it is. Odoo's `_compute_invoice_date_due`:

- The reference date is the **Invoice Date**, or when it is empty the **Accounting Date**, or when that is empty today.
- Each line of the term gives a date; **Due Date becomes the latest of them**:

| Delay Type | The line's date |
|---|---|
| Days after invoice date | reference + After days |
| Days after end of month | last day of the reference's month + After days |
| Days after end of next month | last day of the month after the reference's + After days |
| Days end of month on the | Days on the next month is 0 (or less): the last day of the month of (reference + After days). Otherwise: (reference + After days), moved one month on, to that day of the month — **clamped to the month's last day** (the 31st in November is the 30th) |

An empty After counts as 0. The tenant's own figures are the check: *21 Days* from 2026-09-11 → **2026-10-02**,
*30 Days* from 2026-09-09 → **2026-10-09**, *45 Days* from 2026-09-14 → **2026-10-29**; and from 2026-09-17, *End of
Following Month* → **2026-10-31**, *10 Days after End of Next Month* → **2026-11-10**, *30% Now, Balance 60 Days* →
**2026-11-16**, *90 days, on the 10th* → **2027-01-10**. A HAP code block (node type 14) over the term's lines is
the expected way to take the latest of several dates; if the organisation cannot run one, say what was built instead.

Odoo dates an invoice from its term **only once it has lines**; D does not wait for them (§3).

#### Contacts (01)

| Change | Detail |
|---|---|
| **Customer Payment Terms** (`property_payment_term_id`) and **Vendor Payment Terms** (`property_supplier_payment_term_id`) | On the tab **Sales & Purchase**, in Odoo's order — Sales, Purchase, Misc: **Salesperson \| Customer Payment Terms · Vendor Payment Terms \| Reference**. Odoo's form labels both *Payment Terms* under the headings Sales and Purchase; HAP's tab has no such headings, so the labels are Odoo's field names. **Not hidden for a contact under a company** — Odoo shows them there |
| A company's terms reach its contacts | Both are Odoo **commercial fields**. Extend the two existing Contacts automations as they already treat Tax ID: *copy company details to its contact* copies each term **the company has**; *push company address and Tax ID to its contacts* adds both terms to its trigger fields and writes the company's terms to **all** its contacts — **an empty term included**, as Odoo's `_commercial_sync_to_descendants` writes it. If the existing push leaves an empty Tax ID behind rather than clearing it, do the same for the terms and say so in §2 |
| Seed | The tenant's customer terms, for the contacts this app has: **Sunway Construction Group → 30 Days**, **Klinik Kesihatan Damansara → 21 Days**, **Sarawak Timber Logistics → 45 Days**. No vendor terms (none on the tenant); the tenant's other five partners with terms are not in the app and are not created |
| Not now | 01's *Not built now* row "Pricelist, Payment Terms, Payment Method, Incoterm, Fiscal Position" loses Payment Terms; add an *Added since by bundles* line |

**Roles on Contacts and Invoices: nothing to hide.** Odoo's contact form shows both terms to Billing and to
Read-only, and every accounting group has one of the two; the invoice's term has no group.

### Roles

**Payment Terms and Payment Term Lines join the four business roles** in `build/roles.py`: Accounting
Administrator *full*; Accountant, Invoicing and Accounting Read-only *view* — Odoo's access list gives write, create
and delete on both models to `account.group_account_manager` alone, and read to every internal user. Remember HAP
adds a new worksheet to every role by itself with every switch on (`BUILDING.md`).

### Not built now, and why

| Odoo 19.4 field / feature | Why not now |
|---|---|
| The *Preview* group: Example amount and date, and the "#1 Installment of RM 1,000.00 due on …" lines | Computed on the fly across the lines for a made-up invoice; a HAP formula cannot walk a subtable's rows. Automation D gives a real invoice the same date |
| Installments: each installment's amount (the last line takes the balance), the payment-term journal items on the receivable or payable account, the installments printed on the invoice | Double entry and invoice printing are not built; *Show installment dates* and *Description on the Invoice* are kept for the day they are |
| The early payment discount on an invoice and its payment (discounted amount, discount date, cash-discount lines) | Payments and double entry |
| A new term starting with one line — 100 Percent, 0 days | A HAP subtable starts empty; if HAP can seed a default row, build it and say so in §2 |
| A new line's defaults: Due = 100 − the other percent lines, After = the previous line's + 30 | Computed from sibling rows while typing; a HAP default cannot read them |
| Company (`company_id`) | One company per app copy |
| Reordering by dragging | Sequence is typed instead |
| Refusing to delete a term an invoice uses ("Uh-oh! Those payment terms are quite popular…"), and a contact's term being `ondelete='restrict'` | HAP has no hook before a delete. Only Accounting Administrator can delete; Archive is the way to retire a term (§3) |
| Duplicating names the copy "… (copy)" | HAP's duplicate keeps the name |
| Translations of the name and description | One language |
| Dating an invoice only once it has lines | D dates it as soon as it has a term (§3) |
| The term and the date appearing as the customer is picked | Workflows run after the save (§3) |
| Contacts: *Payment Method* in Sales and in Purchase | Payments — not among the six bundles |
| Sales orders' Payment Terms | Sales is not this app |

### Records

1. **The 10 terms** from `data/casimir-payment-terms.json`, **in the tenant's id order** (Immediate Payment first,
   90 days, on the 10th last) so that creation order breaks the Sequence tie as Odoo's id does: name, Early
   Discount, Discount %, Discount Days, Reduced tax, Show installment dates, Description on the Invoice, Sequence
   10, active — **with their 11 lines**. Read every term and line back.
2. **Then the references**, each read back: the three invoices (step 2 above), the three contacts.

No `TEST …` record is needed to seed; the build and the test list add their own.

## 2 · Build

Built on 17 Sep 2026 (14:30–16:35) by `nocoly/build/payterms.py` — steps `create → fields → mount → computed → layout →
rules → buttons → views → roles → seed → invoices → contacts → automations → carry → retire`, or `all`, then `check`.
Helpers: `baseline` snapshots the nine existing worksheets (controls, rules, buttons, views, every record through
`record get`), every workflow node by node and every role before the first write
(`backups/payterms_snapshot_baseline_20260917-143042.json`, not committed); `records` compares every record with it;
`verify` reads the terms, lines, carried documents and seeded contacts against the extract; `selfcheck [d c confirm
contacts]` drives the automations on TEST records; `order` prints each view in its own order; `deadrefs` scans every
view, rule, button, control and workflow node of the app for a control id; `show` prints both worksheets. Every write
step compares the nine existing worksheets control by control before and after (`expect`), allowing only the changes it
names, and every step was run a second time and wrote nothing (*Self-checks*).

**Scripts changed**, beyond the new `payterms.py`:

| Script | Change |
|---|---|
| `invoices.py` | `FIRST_BUILD` and `RENAME` no longer carry the deleted stand-in `6aa920d74a73a3142152e68d` (left as a comment). `HINTS` "Payment Terms" and `DESC` "" for the relation; `RELATIONS` gains Payment Terms (read back by `check`; the relation is not in `NEW`, `payterms.py` creates it). `RULES` gains *Due Date or Payment Terms* (a "not empty" driver, `labels` None) and *No due date on a journal entry*; `rules` and `check` handle the not-empty form. `read_document` reads the term as the relation's title and `values_for` writes the relation by term name — the seed never writes text. `numbering` ends Confirm with `payterms.ensure_dating` once the relation exists, and — since 17 Sep, 22:47 — sets Confirm's writes to start no other workflow (`payterms.ensure_quiet`; *One dating per action*, below) |
| `contacts.py` | `PLACE` / `TABS`: Customer Payment Terms beside Salesperson (row 15), Vendor Payment Terms (row 16), Misc and everything under it one row down. `DESC` for both terms. `automations`: two branches on *copy company details*, one step and two trigger fields on *push company address and Tax ID*, and `term_nodes`, which writes and reads those nodes back |
| `roles.py` | `ORDER` and the Accountant and Invoicing matrices carry Payment Terms and Payment Term Lines (*view*); Accounting Administrator (*full*) and Accounting Read-only (*view*) take them from `ORDER` |

Nothing in `common.py`, `hap.py` or `accounts.py` changed for this bundle (`payterms.py` imports `accounts`' comparison
helpers). (`common.py` gained `controls_with_version` and a `version` argument to `save_controls` later on 17 Sep, for
the restore of Products' Favorite — `03-products.md` §2.)

### What was built

| Element | Built | Id |
|---|---|---|
| Worksheet | **Payment Terms**, alias `account_payment_term`, icon `sys_money-time_symbol`, in Invoicing after Journals | `6aab893fe43d174ab374ce17` |
| Worksheet | **Payment Term Lines**, alias `account_payment_term_line`, icon `sys_timeline_symbol`, after Payment Terms and **hidden from the sidebar** (`HomeApp/SetWorksheetStatus` status 2) | `6aab89417d58b0f449311705` |
| Menu group | Invoicing: Chart of Accounts · Journals · Payment Terms · Payment Term Lines (hidden) · Invoices · Invoice Lines | `6aa8f3ecbf00c316381dbbe8` |
| Payment Terms | Payment Terms (the stock title's id) · Early Discount · Discount % · Discount Days · Reduced tax · Due Terms · Show installment dates · Description on the Invoice · Sequence · Active · Percent total · Line count | `…ce18` · `6aab8963bd43f55762c727d5` · `…d6` · `…d7` · `…d8` · `6aab8982e43d174ab374ce29` · `6aab8963bd43f55762c727d9` · `…da` · `…db` · `…dc` · `6aab89a6e54d2a34fa4e28ac` · `…ad` |
| Payment Term Lines | Payment Terms (the mount's back-relation) · Display name · Due · Value · After · Delay Type · Days on the next month | `6aab8982e43d174ab374ce2a` · `6aab8964bd43f55762c727f7` · `…f2` · `…f3` · `…f4` · `…f5` · `…f6` |
| Rules — Payment Terms | The discount is set only for an early discount · The percentages must add up to 100 · An early discount needs a single line · An early discount must be positive · An early discount needs days | `6aab8a2be43d174ab374ce4a` · `6aab8a2be54d2a34fa4e28c2` · `6aab8a2cbd43f55762c7281a` · `6aab8a2de54d2a34fa4e28c4` · `6aab8a2d805aef7032868028` |
| Rules — Payment Term Lines | Days on the next month only for "Days end of month on the" · A percentage lies between 0 and 100 · The days added lie between 0 and 31 | `6aab8a327d58b0f449311722` · `6aab8a33e54d2a34fa4e28c6` · `6aab8a34e43d174ab374ce65` |
| Buttons / their workflows | Archive · Unarchive | `6aab8a517d58b0f449311726` / `6aab8a5116473257ad5c43d2` · `6aab8a557d58b0f449311728` / `6aab8a554f2a99acac142214` |
| Views | Payment Terms (the stock view, renamed; opens first) · Archived · Lines | `6aab893fe43d174ab374ce1b` · `6aab8a7ce43d174ab374ce6e` · `6aab89417d58b0f449311709` |
| Invoices | **Payment Terms**, the relation that replaced the text stand-in; rules *Due Date or Payment Terms* · *No due date on a journal entry*; the stand-in **deleted** | `6aab8b6b7d58b0f449311740`; `6aab95d4805aef703286828c` · `6aab95d4bd43f55762c72c01`; `6aa920d74a73a3142152e68d` |
| Automation D | *Invoices: Due Date follows the Payment Terms* | `6aab8d164f2a99acac144995` |
| Automation D on a create | *Invoices: Due Date of a new invoice with no Customer / Vendor* — **not in §1** (*What §1 expects and HAP does not do*, 2) | `6aab9e0d87707da9d61d3b82` |
| Automation C | *Invoices: Payment Terms follow the Customer / Vendor* | `6aab8f1016473257ad5c91e0` |
| Confirm | its workflow gains the dating chain | `6aa9f89b4f2a99acac043704` |
| Contacts | Customer Payment Terms · Vendor Payment Terms; the two sync automations extended | `6aab8c437d58b0f449311755` · `6aab8c437d58b0f449311757`; `6aa8a7ff8475f61d4cc65bb9` · `6aa8a8048475f61d4cc65ebe` |
| Records | 10 terms, 11 lines; the three documents' relation; the three contacts' Customer Payment Terms | *Records* |

Every id is in `ids.json`: the two worksheets under `worksheets`; "Payment Terms: …" and "Payment Term Lines: …" keys for
controls, rules, views, buttons, workflows and records (lines as "Payment Term Lines: <term> line <n>"); "Invoices: …"
for the relation, the two rules, C, D, D on a create and the TEST documents; "Contacts: …" for the two terms and the TEST
contacts. `Invoices: Payment Terms` now holds the relation's id, as `invoices.py layout` records every control by name;
the stand-in's id is kept under **`Invoices: Payment Terms (text stand-in, deleted 17 Sep 2026)`**. No key was renamed.

#### The forms

**Payment Terms** — no tabs, as Odoo's form has none:

| Row | Left | Right |
|---|---|---|
| 0 | **Payment Terms** (12) — the title, required, "e.g. 30 days" | |
| 1 | Early Discount (12) — default unchecked | |
| 2 | Discount % (6) — 2 decimals, default 2, Odoo's help | Discount Days (6) — integer, default 10, Odoo's help |
| 3 | Reduced tax (6) — On early payment · Never · Always (upon invoice), default On early payment | |
| 4 | **Due Terms** (12) — the Payment Term Lines subtable; columns Due · Value · After · Delay Type · Days on the next month (`showControls` and `controlssorts`); its heading shown; **a default row, 100 Percent · 0 · Days after invoice date** | |
| 5 | Show installment dates (12) — default checked | |
| 6 | Description on the Invoice (12) — Rich text, Odoo's placeholder | |
| 7 | **Sequence** (6) — integer, required, default 10, §1's description | |
| 8 | Active (6) — hidden ("011"), default checked, Odoo's help | |
| 9 | Percent total (6) — hidden 汇总, sum of Due over Due Terms where Value is Percent, 6 decimals | Line count (6) — hidden 汇总, count of Due Terms |

**Payment Term Lines:**

| Row | Left | Right |
|---|---|---|
| 0 | **Payment Terms** (12) — the back-relation, required, alias `payment_id` | |
| 1 | Display name (12) — function formula, the title, read-only and hidden on create ("100") | |
| 2 | Due (6) — 6 decimals, trailing zeros not shown (`dotformat` "1"), Odoo's help | **Value** (6) — Percent · Fixed, required, default Percent, Odoo's help |
| 3 | After (6) — integer, default 0 | **Delay Type** (6) — Odoo's four, required, default Days after invoice date |
| 4 | Days on the next month (6) — integer, default 10 | |

Display name is `CONCAT(Due," ",Value," · ",After," · ",Delay Type)` and reads "100 Percent · 30 · Days after invoice
date" on every seeded line — a function formula drops the trailing zeros itself. The first save of each brand-new
worksheet reused the stock title's id for *Payment Terms* and did not send the stock Description and Attachment (nor, on
the lines, the stock Name), which that save therefore removed — the first-save pattern of 08 and 09; those stock
placeholders were never part of the app (*For a second opinion*, 1).

**The mount.** `worksheet mount-subtable` made Due Terms and the back-relation, named *Payment Terms* at once, paired
both ways (`sourceControlId` of each names the other). `layout` placed both, gave the back-relation its alias and made it
required, and gave Due Terms its columns and default row. Descriptions this build wrote where Odoo has no help: Due
Terms, the back-relation, Display name, Percent total, Line count (one line each on what they are).

#### Rules

| Rule | Id | Built as |
|---|---|---|
| The discount is set only for an early discount | `6aab8a2be43d174ab374ce4a` | interaction · **show** Discount %, Discount Days, Reduced tax while Early Discount is checked |
| The percentages must add up to 100 | `6aab8a2be54d2a34fa4e28c2` | validation · Percent total ≠ 100 **or** empty → Odoo's message on **Due Terms** · check type 1 · hint **1 (on submit)** |
| An early discount needs a single line | `6aab8a2cbd43f55762c7281a` | validation · Early Discount checked and Line count > 1 → message on Early Discount · 1 · 0 |
| An early discount must be positive | `6aab8a2de54d2a34fa4e28c4` | validation · Early Discount checked and (Discount % ≤ 0 or empty) → on Discount % · 1 · 0 |
| An early discount needs days | `6aab8a2d805aef7032868028` | validation · Early Discount checked and (Discount Days ≤ 0 or empty) → on Discount Days · 1 · 0 |
| Days on the next month only for "Days end of month on the" | `6aab8a327d58b0f449311722` | interaction · **show** Days on the next month while Delay Type is Days end of month on the |
| A percentage lies between 0 and 100 | `6aab8a33e54d2a34fa4e28c6` | validation · Value is Percent and (Due < 0 or Due > 100) → on Due · 1 · 0 |
| The days added lie between 0 and 31 | `6aab8a34e43d174ab374ce65` | validation · Days on the next month < 0 or > 31 → on Days on the next month · 1 · 0 |

The first two stand on roll-ups (§1): if the UI test finds a correct new term refused, disable `6aab8a2be54d2a34fa4e28c2`
and `6aab8a2cbd43f55762c7281a` (`save-rule --rule-id … --disabled`). Check type 1 changes nothing for them on the API:
the server checks a rule only when a condition field is in the write, and a roll-up never is. Odoo's message
"…using a single 100% line. " is stored without its trailing space.

#### Buttons and views

**Archive** (shown while Active is checked; *"Are you sure that you want to archive this record?"* · Archive / Cancel)
and **Unarchive** (shown while Active is unchecked), each a one-step workflow writing Active — the Journals and Chart of
Accounts pattern, both published.

| View | Id | Built |
|---|---|---|
| Payment Terms | `6aab893fe43d174ab374ce1b` | Active is checked · columns Payment Terms · Description on the Invoice · sort **Sequence ascending, then created ascending** (`moreSort` Sequence, `ctime`) — HAP holds both, so Odoo's `sequence, id` is built as asked |
| Archived | `6aab8a7ce43d174ab374ce6e` | Active is not checked · the same columns and sort |
| Lines | `6aab89417d58b0f449311709` | every line · Payment Terms · Due · Value · After · Delay Type · Days on the next month · sort Payment Terms, then created |

`order`: the ten terms, all Sequence 10, come back in creation order — Immediate Payment … 90 days, on the 10th — and the
four TEST terms (Sequence 90) after them. The Lines view sorts Payment Terms **by the term's title as text** ("10 Days
after End of Next Month", "15 Days", "2/7 Net 30", "21 Days", …), a term's lines in creation order.

#### The relation on Invoices — §1's five steps

1. **Create** (`invoices`, 14:40). The stand-in was renamed *Payment Terms (text stand-in)* and parked at row 23 (one
   save), the relation appended with `add-fields` (one-way, dropdown, the Active picker filter, placeholder "Payment
   Terms", no description, no alias) and placed at row 4, right half (a second save). Each save was compared control by
   control: only the stand-in's name and place, then the new control, then its place and permission changed.
2. **Carry** (`carry`, after automation D was built, so that each write started D): SCG-PO-88213 → 30 Days,
   KKD-2026-009 → 21 Days, STL-2026-0042 → 45 Days, each only after reading the stand-in's text as §1 says.
3. **Read back**: all three by record id — relation and Due Date — and every other document: no relation (the TEST
   documents made later by the self-check carry theirs). Each carry started one run of D, and **the three Due Dates
   stayed the tenant's**: 2026-10-09 (from the Accounting Date 2026-09-09), 2026-10-02, 2026-10-29.
4. **Delete** (`retire`, 15:24). Refused unless step 3 reads back. The read-only rule was first given the relation
   **beside** the stand-in, so the relation was never unlocked; then a full save of Invoices that left out
   `6aa920d74a73a3142152e68d` deleted it (backup `payterms_invoices_controls_pre_retire_20260917-152433.json`). The
   comparison allowed exactly that id to go. `invoices.py layout` then gave the relation the alias
   `invoice_payment_term_id` — its only change.
5. **Re-point**: **after the deletion the rule still named the dead id** (HAP does not clean a rule); `invoices.py
   rules` rewrote it by name — Type, Customer / Vendor, Journal, Invoice Date, Accounting Date, Due Date, **Payment Terms
   (the relation)**, Tax mode, Lines — and added the two new rules. `deadrefs` before the deletion found the id in that
   rule alone; after it, **no reference** in any view, rule, button, control or workflow node of the 11 worksheets and 29
   workflows (342 nodes). `invoices.py check` and `verify` pass on the relation.

The two new rules are interaction rules: *Due Date or Payment Terms* hides Due Date while Payment Terms is not empty;
*No due date on a journal entry* hides Due Date and Payment Terms while Type is Journal Entry. Both hide Due Date: how
two hide rules combine is for the browser.

#### Automations C and D, and Confirm

**The dating chain** — the same five nodes at the end of C, D, D on a create and Confirm (`ensure_dating`):

1. *Get the invoice as it now stands* — a search, Record ID = the trigger's, so C reads its own write and Confirm the
   Invoice Date it has just filled;
2. *Does the invoice have Payment Terms?* — exclusive: *It has Payment Terms* (not empty) / *It has none — the Due Date
   is left as it is* (empty, no step);
3. *Get the term's lines* — get-multiple (13/400), Payment Terms = the invoice's Payment Terms, `execute` true;
4. *Compute the Due Date from the lines* — a **JavaScript code block** (14/102). Inputs: the invoice's Invoice Date,
   Accounting Date and Due Date, the system's current time, and the lines' Delay Type, After and Days on the next month
   (lists). It applies Odoo's `_get_due_date` to every line — reference date Invoice Date, else Accounting Date, else
   today; the four Delay Types; the clamp; an empty After as 0 — and outputs the latest date as `due_date`, or the
   current Due Date when the term has no lines (Odoo keeps it). Before it went in, the same code ran locally against
   `dateutil.relativedelta` on 2000 random dates and line sets: 0 mismatches;
5. *Write the Due Date* — Due Date = the code's `due_date`, on the invoice the search found.

| Workflow | Trigger | Before the chain | Node ids (chain: search · gateway · lines · code · write) |
|---|---|---|---|
| **D** `6aab8d164f2a99acac144995` | 仅更新 ('4') narrowed to Payment Terms, Invoice Date, Accounting Date · condition Payment Terms not empty · *When an invoice's Payment Terms or dates change* | — | `6aab8d19a1c923a16e07c3e4` · `6aab8d1a4f2a99acac144ac7` · `6aab8d1ba1c923a16e07c416` · `6aab8d8b16473257ad5c7502` · `6aab8d1ba1c923a16e07c432` |
| **D on a create** `6aab9e0d87707da9d61d3b82` | 新增 ('1') · Payment Terms not empty **and** Customer / Vendor empty · *When an invoice is created with Payment Terms and no Customer / Vendor* | — | `6aab9e0f16473257ad5df60d` · `6aab9e1087707da9d61d3c10` · `6aab9e1016473257ad5df666` · `6aab9e1e87707da9d61d3e28` · `6aab9e1187707da9d61d3c2c` |
| **C** `6aab8f1016473257ad5c91e0` | 新增或更新 ('2') narrowed to Customer / Vendor, no condition · *When an invoice is created or its Customer / Vendor changes* | *Get the customer / vendor* `6aab8f3116473257ad5c945f` (Contacts, Record ID = Customer / Vendor, carries on when nothing is found, condition ignored when abnormal) → exclusive gateway *Which Payment Terms does the document take?* `6aab8f3216473257ad5c9470`, below | `6aab8f3416473257ad5c94f5` · `6aab8f3416473257ad5c9506` · `6aab8f3516473257ad5c9526` · `6aab8f8d16473257ad5c9ef4` · `6aab8f3516473257ad5c9537` |
| **Confirm** `6aa9f89b4f2a99acac043704` | the button | its existing chain, after *A customer document without a Payment Reference?* | `6aab8f9e16473257ad5ca479` · `6aab8f9e16473257ad5ca4a3` · `6aab8f9e16473257ad5ca4e4` · `6aab8faa16473257ad5ca7f8` · `6aab8f9f16473257ad5ca50e` |

C's gateway — every path written out, so that every document reaches the chain (a run matching no path stops at the
gateway):

| Path | Id | Condition groups (any one) | Step · write |
|---|---|---|---|
| Journal Entry — no Payment Terms | `6aab8f3216473257ad5c9471` | Type is Journal Entry | *Empty the Payment Terms* `6aab8f3216473257ad5c9490` · Payment Terms emptied (`isClear`) |
| Customer document — the contact's Customer Payment Terms | `6aab8f3216473257ad5c9472` | Type is Customer Invoice, Customer Credit Note or Sales Receipt · Customer / Vendor not empty · the contact's Customer Payment Terms not empty | *Take the customer's Customer Payment Terms* `6aab8f3316473257ad5c94a9` |
| Vendor document — the contact's Vendor Payment Terms | `6aab8f3316473257ad5c94be` | Vendor Bill, Vendor Credit Note or Purchase Receipt · Customer / Vendor not empty · Vendor Payment Terms not empty | *Take the vendor's Vendor Payment Terms* `6aab8f3316473257ad5c94cf` |
| Otherwise — the Payment Terms are left as they are | `6aab8f3316473257ad5c94dc` | customer type and no Customer / Vendor · customer type and no Customer Payment Terms · vendor type and no Customer / Vendor · vendor type and no Vendor Payment Terms · Type empty | none |

All five workflows' nodes read back as built (`check`); all published.

**One dating per action — 17 Sep 2026, 22:40–23:05** (the owner's answer to *For a second opinion* 3: "Remove one").
Until then C's write of the Payment Terms and Confirm's write of the Invoice Date each started D, so those invoices
were dated twice (difference 1). HAP has no switch on an update step or a trigger that stops that; it has one on the
**writing** workflow — *触发其他工作流* in its process config, `triggerType` **0** allow (the default) · **1** only
the workflows named · **2** not allowed (`BUILDING.md`, Workflows). The fix uses it instead of deleting C's and
Confirm's dating chains: **no node was deleted, added or changed**.

| Workflow | Id | Change |
|---|---|---|
| C | `6aab8f1016473257ad5c91e0` | 触发其他工作流 0 → **2 不允许触发** (22:46), every other config key read back unchanged; republished |
| Confirm | `6aa9f89b4f2a99acac043704` | the same (22:47) |
| D · D on a create | `6aab8d164f2a99acac144995` · `6aab9e0d87707da9d61d3b82` | unchanged (0): they write only the Due Date, which starts nothing |

C and Confirm keep the dating chains listed above and date the invoice themselves; their writes now start nothing.
Nothing else is lost: the only event workflows on Invoices are C, D and D on a create, and neither C nor Confirm writes
another worksheet. Why the switch rather than removing the chain from C's two term-writing paths and from Confirm: it
was found and proved first, it deletes nothing, and it dates an invoice whose term C writes **unchanged** — a write that
changes nothing starts no D, so a chain left to D would never date *TEST PT once same term*.

`payterms.py`: `ensure_quiet` sets the switch (called by `build_c`, and by `invoices.py numbering` for Confirm) and
backs up the config it replaces (`backups/payterms_process_config_pre_quiet_20260917-224643.json` · `-224703.json`);
`check` reads it back on both; `selfcheck` counts a D run after C or Confirm as a `DIFF` (it was a `LIMIT` line) and
has a new part `once`. The `automations` step, run a second time, wrote nothing; `check` passes but for the two roll-up
rules disabled during the UI test, which the script still specifies as enabled.

Evidence — runs from `hap approval history`; a *dating run* is one that passed *Write the Due Date*:

- **Before** (22:40, C still at 0) — *TEST PT twice (before the switch)*, created on Sunway Construction Group with
  Invoice Date 2026-09-17: C `6aabfbce16473257ad61429a` dated it at 22:40:14 and D `6aabfbd316473257ad6142c3` dated it
  again at 22:40:19 — **two dating runs**, Due Date 2026-10-17.
- **After** — `selfcheck once` (runs 22:51–22:56). Each line waits for the run it expects, then reads the runs of all four
  workflows no sooner than 30 s after the write; any other run fails the line:

```
OK    once · TEST PT once customer: created on Sunway Construction Group (30 Days), Invoice Date 2026-09-17: {"term": "30 Days", "due": "2026-10-17"}; runs C ["2 Take the customer's Customer Payment Terms · dated"] ['6aabfe578e75db182e89bc5c']; dating runs 1 ['C']
OK    once · TEST PT once customer: Invoice Date changed to 2026-09-20: {"invoice_date": "2026-09-20", "due": "2026-10-20"}; runs D ['2 · dated'] ['6aabfe9787707da9d6204d3b']; dating runs 1 ['D']
OK    once · TEST PT once typed term: created on TEST PT No Terms Co with 21 Days typed: {"term": "21 Days", "due": "2026-10-08"}; runs C ['2 · dated'] ['6aabfec687707da9d6204e45']; dating runs 1 ['C']
OK    once · TEST PT once typed term: Customer changed to TEST PT Vendor Co (45 Days): {"partner": "TEST PT Vendor Co", "term": "45 Days", "due": "2026-11-01"}; runs C ["2 Take the customer's Customer Payment Terms · dated"] ['6aabff068e75db182e89c1cd']; dating runs 1 ['C']
OK    once · TEST PT once same term: created on Sunway Construction Group with its 30 Days typed, Invoice Date 2026-09-18: {"term": "30 Days", "due": "2026-10-18"}; runs C ["2 Take the customer's Customer Payment Terms · dated"] ['6aabff344f2a99acac1873ba']; dating runs 1 ['C']
OK    once · TEST PT once Confirm: created on Sunway Construction Group, no Invoice Date, Accounting Date 2026-09-01: {"term": "30 Days", "invoice_date": "", "due": "2026-10-01"}; runs C ["2 Take the customer's Customer Payment Terms · dated"] ['6aabff6216473257ad61641b']; dating runs 1 ['C']
OK    once · TEST PT once Confirm: Confirm: {"status": "Posted", "invoice_date": "2026-09-17", "due": "2026-10-17"}; runs Confirm ['2 · dated'] ['6aabff89a1c923a16e0b5b09']; dating runs 1 ['Confirm']
selfcheck (no control may change): compared control by control
  identical: Contacts (35), Units & Packagings (10), Products (24), Product Variants (20), Product Categories (10), Chart of Accounts (11), Journals (20), Invoices (33), Invoice Lines (14)
selfcheck: OK; platform limits recorded: 0
```

Confirm took **INV/2026/00008**. Not covered, and for the browser (*For the UI test* 8): a browser create with a term
and no customer, if the form sends the empty Customer / Vendor (C and D on a create would both date it); and one save
changing the customer and a date together, which starts C and D at once, as before.

#### Contacts

**Customer Payment Terms** (`property_payment_term_id`) and **Vendor Payment Terms** (`property_supplier_payment_term_id`)
— one-way Relations → Payment Terms, dropdown, the Active picker filter, no placeholder, not required, not hidden for a
contact under a company — on Sales & Purchase: **Salesperson | Customer Payment Terms** (row 15), **Vendor Payment Terms**
(row 16), then the Misc divider and Reference. `contacts.py layout` moved Misc 16 → 17, Reference 17 → 18, the tab
Invoicing 18 → 19 and its two accounts 19 → 20, the tab Notes 20 → 21, Notes 21 → 22, Active 22 → 23, Display Name 23 →
24, Parent name 24 → 25. A description on each (Odoo has no help): what takes the term and how a company's reaches its
contacts.

*Contacts: copy company details to its contact* gained **The company has Customer Payment Terms?** → *Copy the Customer
Payment Terms* and **The company has Vendor Payment Terms?** → *Copy the Vendor Payment Terms*, after the DUNS branch
(each copies only a term the company has). *Contacts: push company address and Tax ID to its contacts* gained both
terms among its trigger fields and **Copy the Payment Terms to them**, writing both terms from the company to all its
contacts (`Get its contacts`). Both workflows republished and read back node by node.

#### Roles

`payterms.py roles` ran `roles.py create`. HAP had added both worksheets to all four business roles at its own defaults
(own records, no create, every switch on); `reconcile` wrote their entries — Accounting Administrator full, Accountant,
Invoicing and Accounting Read-only view, the action switches, the views' flags — and nothing else. `roles.py check`: OK.
Nothing hidden per field (§1).

#### Records

- **The ten terms**, created in the tenant's id order, a second apart, each followed by its lines — 11 lines — and read
  back at once; `verify`: 10 OK, 0 missing or differing, every Percent total 100 and Line count as the extract.
- **The three documents' Payment Terms**, carried and read back (above).
- **The three contacts' Customer Payment Terms**: Sunway Construction Group → 30 Days, Klinik Kesihatan Damansara → 21
  Days, Sarawak Timber Logistics → 45 Days; no Vendor Payment Terms. None of the three has contacts under it, so no push
  ran.

#### What §1 expects and HAP does not do

**1 · "A workflow's write starts no other workflow" does not hold by default — and is now set so for C and Confirm.**
C's write of Payment Terms on its own trigger record **started D** (every time C wrote a term), and Confirm's write of
the Invoice Date **started D** too, so each such document was dated twice, to the same date. **Fixed on 17 Sep
(owner: "Remove one"; *One dating per action*, below):** HAP's process config *触发其他工作流* decides whether a
workflow's writes start other workflows, and C and Confirm now have it at *不允许触发*. Both keep their own dating
chain, so every action dates an invoice once. What remains: a user save that changes Customer / Vendor **and** a date
together starts both C and D at once, as it did before — two datings from one save, racing (*For the UI test*).

**2 · C starts no run on a create that does not write Customer / Vendor.** §1: C runs "on an invoice created". HAP's
新增或更新 trigger narrowed to Customer / Vendor fired for every API create carrying one and for none without one, so
*TEST PT C no customer*, created with 45 Days and an Invoice Date, stayed **undated**. Built instead of leaving it: **D
on a create** — 新增, when Payment Terms is set and Customer / Vendor is empty — which dated *TEST PT new invoice without
a customer* 2026-11-01. It is a workflow §1 does not name. If the browser's create sends an empty Customer / Vendor, C
runs as well and both date the invoice the same way.

**3 · Whether the roll-ups follow unsaved rows, the line rules act inside the subtable, the validation messages show on a
subtable, the default row appears, two hide rules on Due Date combine, the pickers leave archived terms out, and the
hidden worksheet looks hidden** — all stored and read back, none visible to the CLI (*For the UI test*).

**4 · A code block's inputs and outputs are not readable after a run.** `approval history-detail` lists the code node
with no data, so the form in which a get-multiple step's lists arrive was not seen; the code accepts a JSON array or
comma-separated text, and the two-line terms (30% Now, Balance 60 Days; TEST PT empty After) prove the lists arrive
aligned, an empty After keeping its place.

#### Decisions taken while building

- **The stock controls of the two new worksheets were not carried** by their first save (Description, Attachment; the
  lines' Name) — see *For a second opinion*, 1.
- **Vendor Payment Terms sits on its own row above the Misc divider**, not §1's "Vendor Payment Terms | Reference": the
  tab has Sales and Misc dividers, and beside Reference the term would read as a Misc field. Reference moved one row down.
- **Both "only for" interaction rules are shows** (discount fields while Early Discount is checked; Days on the next
  month while Delay Type is *Days end of month on the*) — §1 words them as hides on the opposite condition; the house
  form, identical on every record with a value (Journals, Chart of Accounts).
- **Validation messages** attach to Due Terms (percentages), Early Discount, Discount %, Discount Days, Due and Days on
  the next month. *The percentages must add up to 100* shows **on submit only**: a new term starts with Percent total
  empty and would show the message before a line is typed. The others show as typed.
- **Due keeps 6 decimals and hides trailing zeros** (`dotformat` "1") — §1's preferred case.
- **Due Terms keeps its heading**: no tab or divider above it says *Due Terms*.
- **§1's *Not built now* row "a new term starting with one line"** — HAP can seed a default row, so it is built:
  100 Percent · 0 · Days after invoice date. §1's line defaults computed from sibling rows are not.
- **D runs on update only**; a create is C's, or D on a create's. D keeps §1's single condition, a term — C empties a
  journal entry's term, so D never dates one that way.
- **The dating chain re-reads the invoice** before reading its term and dates, so C's and Confirm's own writes are seen.
- **Confirm dates the invoice whenever it has a term**, not only when it filled the Invoice Date — the same date either
  way, and one less branch.
- **C and Confirm start no other workflow, and keep their chains** (17 Sep, the owner's "Remove one"), rather than
  losing the chain from C's two term-writing paths and from Confirm. The switch was found and proved first; it deletes
  no node, and it also covers the case a chain left to D would miss — C writing the term the invoice already carries,
  a write that changes nothing and so starts no D (*TEST PT once same term*).
- **C's gateway names an "Otherwise" path** covering every other document, so each reaches the chain.
- **The contact is read with its condition ignored when abnormal** (automation B's guard), and every C path checks
  Customer / Vendor before trusting it.
- **The stand-in was renamed and parked while both existed**, and the relation got the alias only after the deletion, as
  §1 orders.
- **The read-only rule named both controls between steps 4 and 5**, so no moment passed with the term editable on a
  posted invoice.
- **`Invoices: Payment Terms` in `ids.json` now points at the relation**; the stand-in's id is kept under its own key.
- **`invoices.py seed` writes the relation by term name**, so a re-seed carries the terms rather than text.
- **The Contacts terms and Due Terms got descriptions** where Odoo has none.
- **The TEST terms are active** (Sequence 90, after the tenant's ten), so they appear in the pickers until archived.

#### For a second opinion

1. **The stock controls.** The first save of each new worksheet left out HAP's stock Description and Attachment (and
   the lines' stock Name), which removes them — how 08 and 09 were built. The brief says to delete nothing but the
   stand-in; these were placeholders HAP put on worksheets this run created, never part of the app, and keeping them would
   put three fields §1 does not have on the forms. Say if that should be done differently next time.
2. **D on a create** — a fifth workflow §1 does not name (difference 2). Keep it, or accept that an invoice created
   without a Customer / Vendor is dated only when its term or a date is next changed?
3. **The duplicate D runs** after C's term write and after Confirm (difference 1) — **answered 17 Sep: "Remove one"**;
   removed by setting C's and Confirm's *触发其他工作流* to *不允许触发* (*One dating per action*).
4. **Vendor Payment Terms' row** (decisions) and the **on-submit hint** on the percentages rule.

#### Found while building

All in `BUILDING.md`:

- **A code block is buildable through the CLI**: `node add --type 14 -a 102`, `saveNode` with **`testMap` required** (HTTP
  500 without it) and the code base64-encoded, then **`codeTest` to register the outputs**; an update step binds a Date
  to an output as `nodeId` + `fieldValueId`; a get-multiple step's fields arrive as aligned lists.
- **A get-multiple step has `execute`, not `executeType`.**
- **An update step empties a field with `isClear: true`**; a plain empty value is dropped from the step on save.
- **新增或更新 narrowed to fields fires on a create only when the create writes one of them** (the earlier bullet said
  every create).
- **A workflow's write of its own trigger record started another workflow of the same worksheet** (C → D; Confirm → D).
  Found on 17 Sep why: a workflow's process config *触发其他工作流* (`triggerType` 0 allow — the default, under which a
  same-worksheet workflow starts only if it is narrowed to trigger fields · 1 only the named · 2 not allowed), and it
  is how the second dating was removed.
- **Deleting a control leaves it named in a rule**; a scan for dead ids must skip a node's control catalogue keys.
- **`HomeApp/SetWorksheetStatus`** hides a worksheet from the sidebar, readable only from `HomeApp/GetApp`.
- **A 汇总 takes a filter** (filterType 51 on a single select); **a 子表 takes default rows**; **`dotformat`** hides a
  Number's trailing zeros; **a function formula renders a Number without trailing zeros and an empty one as nothing**.
- **A view sorts a Relation by title text, and `ctime` works as a second sort key.**
- **`record get` keys an alias-less control by its id**; **`--back-relate-name` names the back-relation**, alias empty.
- **An empty value in the push is written as empty** (Tax ID and a term alike).
- **`workflow create` can time out having created nothing**; a second `batch-add` once kept its branch conditions.
- **`contacts.py layout` does not write `fieldPermission`**, so `add-fields`' "" stays until a save sets "111".

#### For the UI test

Only the browser can show these; each is stored and read back:

1. **The sidebar**: Payment Terms after Journals; Payment Term Lines hidden — for an administrator and for a role member.
2. **A new term's form**: the default Due Terms row (100 Percent · 0 · Days after invoice date); the discount fields
   appear only with Early Discount ticked.
3. **The roll-up rules in the open form**: a new term with correct lines (e.g. 30 Percent + 70 Percent) saves; lines
   adding to 90 are refused with the percentages message — and where it shows; Early Discount with two lines refused.
   If a correct term is refused, disable `6aab8a2be54d2a34fa4e28c2` and `6aab8a2cbd43f55762c7281a`.
4. **The line rules inside the subtable**: Days on the next month hidden unless Delay Type is *Days end of month on the*;
   Due 120 on a Percent line and Days on the next month 40 refused — in the subtable and on the line form.
5. **The subtable's columns** in §1's order, and Display name absent from them; Due shown without trailing zeros.
6. **Archive / Unarchive** on a TEST term, and the Archived view; the Payment Terms view's order.
7. **Invoices**: Payment Terms beside Due Date; Due Date hidden while a term is set; both hidden on a journal entry; the
   term locked on a posted invoice (INV/2026/00001); the picker offers active terms only.
8. **C and D from the form**: pick a customer with terms on a new invoice and save (term and Due Date appear after the
   save, in seconds); change the Invoice Date and the Due Date follows; a new invoice with a term and no customer is dated
   — and whether the form's create starts C (difference 2). **Since 17 Sep, count the runs** after each save
   (`hap approval history --process-id …` for C `6aab8f1016473257ad5c91e0`, D `6aab8d164f2a99acac144995` and D on a
   create `6aab9e0d87707da9d61d3b82`): one run dates the invoice — C's after a customer is picked, D's after a date or
   term change. Two cases the CLI cannot settle: a **browser create with a term and no customer** — if the form sends
   the empty Customer / Vendor, C runs beside D on a create and both date it; and a **save changing the customer and a
   date together**, which starts C and D at once by design of their triggers.
9. **Confirm** on a draft with a term and no Invoice Date — **one run, Confirm's**, and none of D since 17 Sep.
10. **Contacts**: the two terms on Sales & Purchase, visible for a contact under a company; the pickers; giving a contact
    a company copies its terms.

#### Self-checks through the CLI

`check` (16:21–16:27) — every part above read back, `invoices.py check` and `roles.py check` included:

```
check: OK — controls, tabs, options, defaults, rules, views, buttons and the numbering workflow as specified
check: OK — five stock roles in English with their roleType and members, four business roles with their per-worksheet
scopes, export on Accounting Administrator alone, the account fields hidden from Invoicing and Accounting Read-only as
09 §1 says, and no members
check: OK — Payment Terms and Payment Term Lines in Invoicing after Journals, the lines hidden from the sidebar;
controls, options, defaults, roll-ups, title formula, mount, rules, buttons and views; the relation on Invoices with its
rules and no stand-in; Contacts' two terms and their sync; automations C and D and Confirm's dating chain; the roles
```

`verify` (16:30):

```
OK     1 Immediate Payment                seq=10 early=0 2%/10d 'On early payment' show=1 active=1 total=100.0 lines=1.0 note='<p>Payment terms: Immediate Payment</p>'
          '100 Percent · 0 · Days after invoice date'      next month 10.0
…
OK     8 30% Now, Balance 60 Days         seq=10 early=0 2%/10d 'On early payment' show=1 active=1 total=100.0 lines=2.0 …
          '30 Percent · 0 · Days after invoice date'       next month 10.0
          '70 Percent · 60 · Days after invoice date'      next month 10.0
OK     9 2/7 Net 30                       seq=10 early=1 2%/7d 'On early payment' show=1 active=1 total=100.0 lines=1.0 note='<p>Payment terms: 30 Days, 2% Early Payment Discount under 7 days</p>'
OK    10 90 days, on the 10th             seq=10 early=0 2%/10d … total=100.0 lines=1.0 …
          '100 Percent · 90 · Days end of month on the'    next month 10.0
10 terms and 11 lines in the extract; 0 missing or differing; 4 terms not in the extract [the four TEST PT terms]
OK    STL-2026-0042            Draft            relation '45 Days'   due 2026-10-29
OK    KKD-2026-009             INV/2026/00001   relation '21 Days'   due 2026-10-02
OK    SCG-PO-88213             Draft            relation '30 Days'   due 2026-10-09
carry: 3 documents carry their term; the other 24 documents checked — 0 differing
OK    Contacts Sunway Construction Group    Customer Payment Terms 30 Days, Vendor Payment Terms None
OK    Contacts Klinik Kesihatan Damansara   Customer Payment Terms 21 Days, Vendor Payment Terms None
OK    Contacts Sarawak Timber Logistics     Customer Payment Terms 45 Days, Vendor Payment Terms None
```

`carry` (15:00–15:02), each write with the D run it started:

```
OK    SCG-PO-88213   Draft           text '30 Days' → relation '30 Days'; Invoice Date —, Accounting Date 2026-09-09; Due Date 2026-10-09 (tenant 2026-10-09); automation D runs [('6aab901f16473257ad5cac9c', 2)]
OK    KKD-2026-009   INV/2026/00001  text '21 Days' → relation '21 Days'; Invoice Date 2026-09-11, Accounting Date 2026-09-11; Due Date 2026-10-02 (tenant 2026-10-02); automation D runs [('6aab90394f2a99acac1468e9', 2)]
OK    STL-2026-0042  Draft           text '45 Days' → relation '45 Days'; Invoice Date —, Accounting Date 2026-09-14; Due Date 2026-10-29 (tenant 2026-10-29); automation D runs [('6aab90454f2a99acac14694a', 2)]
```

`retire` (15:24):

```
'A posted or cancelled document is closed for editing' now names both: stand-in True, relation True
deleting 'Payment Terms (text stand-in)' 6aa920d74a73a3142152e68d (type 2, alias 'invoice_payment_term_id', row 23) — the owner-approved deletion
the stand-in deleted: compared control by control
  Invoices: 'Payment Terms (text stand-in)' (6aa920d74a73a3142152e68d) is gone
  identical: Contacts (35), Units & Packagings (10), Products (23), Product Variants (20), Product Categories (10), Chart of Accounts (11), Journals (20), Invoice Lines (14)
after the deletion the rule names the dead id: True
invoices.py layout: Invoices: 'Payment Terms' alias ''→'invoice_payment_term_id'
'A posted or cancelled document is closed for editing': ['Type', 'Customer / Vendor', 'Journal', 'Invoice Date', 'Accounting Date', 'Due Date', 'Payment Terms', 'Tax mode', 'Lines']
deadrefs 6aa920d74a73a3142152e68d: 11 worksheets' views, rules, buttons and controls, and 29 workflows (342 nodes) scanned — no reference
```

`selfcheck` — the first run, 15:38–15:52, as printed (lines shortened). Its four `DIFF` lines are the two differences
above, not a wrong date: three are C's term write starting D (`D 1`; difference 1 — the script then reported those runs
as a `LIMIT` line of their own, and since the evening of 17 Sep, when C and Confirm stopped starting D, as a `DIFF`),
and one is the undated create (difference 2), which led to D on a create. The Confirm `LIMIT` printed as `OK` in that
run (a reporting slip since fixed):

```
OK     Percent total counts Percent lines only (TEST PT fixed line: 100 Percent + 50 Fixed): Percent total 100.0, Line count 2.0
OK     D · 30 Days from the Invoice Date 2026-09-17: Due Date 2026-10-17; D ['2 · dated'], C 0
OK     D · 30 Days, no Invoice Date: the Accounting Date 2026-09-09: Due Date 2026-10-09
OK     D · End of Following Month: Due Date 2026-10-31
OK     D · 10 Days after End of Next Month: Due Date 2026-11-10
OK     D · 30% Now, Balance 60 Days (the latest of two lines): Due Date 2026-11-16
OK     D · 90 days, on the 10th: Due Date 2027-01-10
OK     D · a Days after end of month line (TEST PT 15 Days after End of Month): Due Date 2026-10-15
OK     D · the clamp: day 31 landing in November (TEST PT 30 Days, on the 31st): Due Date 2026-11-30
OK     D · a line with an empty After, before a line with one (TEST PT empty After): Due Date 2026-10-31
OK     D · the day-31 line from 2026-10-15 + 30 → 2026-11-14, on to December 31st: Due Date 2026-12-31
OK     D · both dates empty: today: Due Date 2026-10-17
OK     D · Payment Terms emptied (with a new Invoice Date): the trigger condition starts no run, the Due Date is left as it is: D runs 0
DIFF   C · TEST PT C customer: Payment Terms 30 Days (want 30 Days), Due Date 2026-10-17 (want 2026-10-17); C ["2 Take the customer's Customer Payment Terms · dated"], D 1
DIFF   C · TEST PT C vendor bill: Payment Terms 15 Days (want 15 Days), Due Date 2026-10-02 (want 2026-10-02); C ["2 Take the vendor's Vendor Payment Terms · dated"], D 1
OK     C · TEST PT C contact without terms: Payment Terms 21 Days (want 21 Days), Due Date 2026-10-08 (want 2026-10-08); C ['2 · dated'], D 0
DIFF   C · TEST PT C no customer: Payment Terms 45 Days (want 45 Days), Due Date  (want 2026-11-01); C [], D 0
OK     C · TEST PT C journal entry: Payment Terms None (want None), Due Date 2026-12-31 (want 2026-12-31); C ['2 Empty the Payment Terms'], D 0
DIFF   C · the Customer changed to Sunway Construction Group on TEST PT C contact without terms: Payment Terms 30 Days, Due Date 2026-10-17; C ["2 Take the customer's Customer Payment Terms · dated"], D 1
OK     Confirm · the TEST draft as C left it: no Invoice Date, dated from the Accounting Date 2026-09-01: Payment Terms 30 Days, Invoice Date —, Due Date 2026-10-01
OK     Confirm · posts it, fills the Invoice Date with today and dates it from that: INV/2026/00007 Posted, Invoice Date 2026-09-17, Due Date 2026-10-17 (want 2026-10-17); Confirm ['2 · dated']
OK     Confirm · its write of the Invoice Date starts automation D as well: D runs ['2 · dated']
OK     Contacts · a contact given a company with terms takes them (copy company details): Customer 21 Days, Vendor 15 Days, Tax ID 'TEST-PT-VAT'
OK     Contacts · the company's Customer Payment Terms changed to 45 Days reach its contact (push): Customer 45 Days, Vendor 15 Days
OK     Contacts · the company's Tax ID emptied: what the existing push does with an empty value: Tax ID '' — cleared
OK     Contacts · the company's Vendor Payment Terms emptied: the push writes the empty value to its contact, as it does the Tax ID: Vendor None
OK     'TEST PT C vendor bill' cancelled through the Cancel workflow: Cancelled
selfcheck (no control may change): controls read back with differences nobody asked for — stopping:
  Units & Packagings: 'Unit Name' changed unique false -> true; … 'Related UoMs' changed row 4 -> 5 …   (see below)
```

After D on a create was built, `selfcheck c confirm` (16:08, which created *TEST PT new invoice without a customer* and
then stopped on a read timeout in the run history; run again at 16:17):

```
OK    C · TEST PT C customer (created in an earlier run): Payment Terms 30 Days, Due Date 2026-10-17
OK    C · TEST PT C vendor bill (created in an earlier run): Payment Terms 15 Days, Due Date 2026-10-02
OK    C · TEST PT C contact without terms (created in an earlier run): Payment Terms 30 Days, Due Date 2026-10-17
OK    C · TEST PT C no customer (created in an earlier run): Payment Terms 45 Days, Due Date
OK    C · TEST PT new invoice without a customer (created in an earlier run): Payment Terms 45 Days, Due Date 2026-11-01
OK    C · TEST PT C journal entry (created in an earlier run): Payment Terms None, Due Date 2026-12-31
OK    C · the Customer changed to Sunway Construction Group (in an earlier run): Payment Terms 30 Days, Due Date 2026-10-17
OK    Confirm · TEST PT Confirm (confirmed in an earlier run): INV/2026/00007 Posted, Invoice Date 2026-09-17, Due Date 2026-10-17
OK    'TEST PT C vendor bill' cancelled through the Cancel workflow: Cancelled
selfcheck (no control may change): compared control by control
  identical: Contacts (35), Units & Packagings (10), Products (22), Product Variants (20), Product Categories (10), Chart of Accounts (11), Journals (20), Invoices (33), Invoice Lines (14)
selfcheck: OK; platform limits recorded: 0
```

and the run of *D on a create* for that document, `6aab9fff87707da9d61d683b` at 16:08:31, status 2, through the trigger,
*Get the invoice as it now stands*, *Does the invoice have Payment Terms?*, *Get the term's lines*, *Compute the Due Date
from the lines* and *Write the Due Date*; C has no run for it.

**What the push does with an empty value**: it **clears** it — the contact's Tax ID became empty when the company's was
emptied, and its Vendor Payment Terms likewise, as Odoo's `_commercial_sync_to_descendants` writes it.

The first `selfcheck` stopped at its closing comparison: **Units & Packagings had changed during the run — by Teh Li
Wei**, whose edits the app log records at 15:46:21 (*Edited business rules: Reference Unit cannot be the unit or one
below it*) and 15:46:31 (*Modified worksheet [Units & Packagings]*). Later he modified **Products** (16:11:33, the
*Favorite* control gone) and created a Products rule (16:17:43). None of it is this build's.

**Every step run again** (16:28–16:33), each writing nothing: `create` (order and hidden status as they were), `fields`,
`mount`, `computed`, `layout`, `rules`, `buttons`, `views` ("already as specified" / "nothing saved") and `invoices`;
`carry` reads all three as carried; `invoices.py layout` "nothing saved", `invoices.py numbering`
"already built; not re-published"; every run of `automations` after the first wrote nothing to D, C or Confirm. (`contacts.py
automations` republishes both sync workflows whenever it runs, as it always has, so it was not re-run.)

`records` against the baseline — every record of the nine worksheets:

```
OK    Contacts             10 before, 14 now; 0 changed beyond this bundle's fields; new [the four TEST PT contacts]
OK    Units & Packagings   33 before, 33 now; 0 changed
DIFF  Products             18 before, 18 now; 18 changed: {"is_favorite": ["0", null]} on every product
OK    Product Variants     19 before, 19 now; 0 changed
OK    Product Categories   11 before, 11 now; 0 changed
OK    Chart of Accounts    90 before, 90 now; 0 changed
OK    Journals             11 before, 11 now; 0 changed
OK    Invoices             19 before, 27 now; 0 changed beyond this bundle's fields; new [the eight TEST PT documents]
OK    Invoice Lines        29 before, 29 now; 0 changed
```

— the Products difference is the *Favorite* control Teh Li Wei removed at 16:11, on every product; nothing of this
bundle writes Products. Invoices' Payment Terms (text → relation) and Contacts' two terms are this bundle's fields.

#### TEST records left

| Record | Worksheet | Id | Left as |
|---|---|---|---|
| TEST PT empty After | Payment Terms | `ad924eb7-4407-4ce5-805d-f77ad72a9f36` | 50 Percent · (empty) · Days after end of next month; 50 Percent · 5 · Days after invoice date |
| TEST PT 15 Days after End of Month | Payment Terms | `6d183df3-86dc-44a5-ad3f-a197f2c14d9f` | 100 Percent · 15 · Days after end of month |
| TEST PT 30 Days, on the 31st | Payment Terms | `8b11a484-8e01-4252-8230-31ed610de57e` | 100 Percent · 30 · Days end of month on the · 31 |
| TEST PT fixed line | Payment Terms | `ae7486d4-5a3f-43c7-97dd-f797fd3f8653` | 100 Percent · 30; 50 Fixed · 0 |
| TEST PT D probe | Invoices | `1bbc2d27-6674-4a7f-94e7-b754f61444c6` | Draft customer invoice on Sales, no customer, no term, Invoice Date 2026-09-20, Due Date 2026-10-17 |
| TEST PT C customer | Invoices | `caff3141-f454-4329-9339-823efad3011d` | Draft, Sunway, 30 Days, due 2026-10-17 |
| TEST PT C vendor bill | Invoices | `b0d48fd7-51f2-461e-b854-f8dca9aa8e28` | TEST PT Vendor Co, 15 Days, due 2026-10-02 — **Cancelled** through the Cancel workflow, so Purchases holds no new draft |
| TEST PT C contact without terms | Invoices | `6cba315e-a643-44db-a783-0acf45780acb` | Draft, created on TEST PT No Terms Co with 21 Days, then Customer → Sunway: 30 Days, due 2026-10-17 |
| TEST PT C no customer | Invoices | `1f818b98-c8a2-4a8c-a116-a87edc14b1ef` | Draft, 45 Days, **no Due Date** — the evidence for difference 2 |
| TEST PT new invoice without a customer | Invoices | `62b10691-c32c-493f-8b97-088208ee993d` | Draft, 45 Days, due 2026-11-01 |
| TEST PT C journal entry | Invoices | `d269046b-f10d-4655-8cd9-4f3efe20c8c1` | Draft entry on Miscellaneous Operations, Sunway, no term, Due Date 2026-12-31 |
| TEST PT Confirm | Invoices | `ad2fc781-b8b4-40e6-8bd1-805cc4eb30be` | **INV/2026/00007, Posted**, Sunway, 30 Days, Invoice Date 2026-09-17, due 2026-10-17 |
| TEST PT Vendor Co | Contacts | `3c315cf4-1c76-4895-bee0-b91ed281d7b8` | Customer 45 Days, Vendor 15 Days |
| TEST PT No Terms Co | Contacts | `73bf65be-6e45-4ffb-b4ac-2619efdc8cc0` | no terms |
| TEST PT Company | Contacts | `69783455-0ee7-4c21-9640-02f2ea11ce41` | Customer 45 Days, no Vendor, no Tax ID |
| TEST PT Person | Contacts | `a2178fa3-2b44-4040-9477-3697822650cd` | under TEST PT Company: Customer 45 Days, no Vendor, no Tax ID |

Added on 17 Sep, 22:40–22:56, by *One dating per action* (none of them touches the tenant's documents or contacts):

| Record | Worksheet | Id | Left as |
|---|---|---|---|
| TEST PT twice (before the switch) | Invoices | `29f90226-0ce7-46b6-8a52-4ceeb149467b` | Draft, Sunway, 30 Days, Invoice Date 2026-09-17, due 2026-10-17 — the control run, dated twice |
| TEST PT once customer | Invoices | `b24859c8-d3bb-484e-bd7f-6dd01d59208c` | Draft, Sunway, 30 Days, Invoice Date 2026-09-20, due 2026-10-20 |
| TEST PT once typed term | Invoices | `6f44ca68-8887-484c-9b05-53970f50240e` | Draft, created on TEST PT No Terms Co with 21 Days, then Customer → TEST PT Vendor Co: 45 Days, due 2026-11-01 |
| TEST PT once same term | Invoices | `a2f3da54-33c4-4937-8ccf-18630e33c37b` | Draft, Sunway, 30 Days typed, Invoice Date 2026-09-18, due 2026-10-18 |
| TEST PT once Confirm | Invoices | `6f236c81-b045-4b38-95d5-b59ace27fe16` | **INV/2026/00008, Posted**, Sunway, 30 Days, Accounting Date 2026-09-01, Invoice Date 2026-09-17, due 2026-10-17 |

Confirm on TEST PT Confirm took **INV/2026/00007**, the next Sales number, and on TEST PT once Confirm **INV/2026/00008**.
Nothing was written to the tenant's documents beyond their Payment Terms, nor to any tenant contact beyond the three
Customer Payment Terms.

## 3 · Test list

**21 of 22 pass, 1 fails.** Run in the Nocoly UI in Chrome on 17 and 18 Sep 2026, with every stored value read
back through `hap worksheet record get` and every workflow's runs counted with `hap approval history`. The one
failure is answered: the two rules that stand on roll-ups are **built and disabled** (test 5, difference 1).

| # | Test | Result |
|---|---|---|
| 1 | The sidebar and the two worksheets | **Pass.** Invoicing reads Chart of Accounts · Journals · **Payment Terms** · Invoices · Invoice Lines. **Payment Term Lines is hidden**: an administrator sees it with a struck-through eye beside its name, and opening it shows its own table |
| 2 | The Payment Terms view | **Pass.** 14 rows — the tenant's ten in Odoo's own order (Immediate Payment … 90 days, on the 10th), then the four `TEST PT` terms — columns **Payment Terms · Description on the Invoice**, each description the tenant's ("Payment terms: 30 Days") |
| 3 | A term, field by field | **Pass.** *30% Now, Balance 60 Days*: Early Discount unchecked with the three discount fields hidden; **Due Terms (2)** reading 30 Percent · 0 · Days after invoice date and 70 Percent · 60 · Days after invoice date, Due without trailing zeros and Days on the next month blank; Show installment dates ticked; the description; Sequence 10 |
| 4 | A new term's form | **Pass.** Payment Terms placeholder "e.g. 30 days"; **Due Terms opens with one row, 100 Percent · 0 · Days after invoice date**; Sequence 10 with its description; ticking **Early Discount** brings out Discount % 2.00, Discount Days 10 and Reduced tax *On early payment*, each with Odoo's help |
| 5 | The percentages must add up to 100, and an early discount needs a single line | **Fail — both rules disabled.** A **correct** new term (the default 100 % row alone) was refused with "The Payment Term must have at least one percent line and the sum of the percent must be 100%."; lines of 100 + 0 + 0 were refused too. A 汇总 over a 子表 does not follow the rows being edited, so Percent total and Line count read the **saved** lines — empty on a new term. `6aab8a2be54d2a34fa4e28c2` and `6aab8a2cbd43f55762c7281a` were disabled (`save-rule --disabled`, every other setting unchanged, backup `payterms_rules_pre_disable`), and the term then saved with Percent total 100 and Line count 1 read back afterwards. Difference 1 |
| 6 | An early discount must be positive, and needs days | **Pass.** With Early Discount ticked, Discount % 0 shows "The Early Payment Discount must be strictly positive." and Discount Days 0 "The Early Payment Discount days must be strictly positive.", both **as typed**. HAP draws the message over the Early Discount checkbox, so the box cannot be unticked until the field is corrected |
| 7 | A percentage lies between 0 and 100, inside the subtable | **Pass.** Due 120 on the Percent row marks the cell, heads the table with "Please enter correct Due Terms" and shows Odoo's "Percentages on the Payment Terms lines must be between 0 and 100." on hover. The row was not saved — `record list` still reads 100 |
| 8 | The days added lie between 0 and 31, inside the subtable | **Pass.** With Delay Type *Days end of month on the*, 40 in Days on the next month is refused with "The days added must be between 0 and 31." |
| 9 | Days on the next month only for "Days end of month on the" | **Pass.** Blank and read-only on a *Days after invoice date* row; the moment Delay Type becomes *Days end of month on the* it shows its 10 and takes typing |
| 10 | Archive and Unarchive | **Pass.** Archive asks "Are you sure that you want to archive this record?" and moves *TEST UI default row* to the **Archived** view; Unarchive brings it back with no confirmation, one run in the history. On the full record page the button whose condition fails is **hidden**; in the pop-up record it is **greyed** instead |
| 11 | The Lines view | **Pass.** 18 lines, columns Payment Terms · Due · Value · After · Delay Type · Days on the next month, ordered by the term's title then creation. The column shows every line's Days on the next month, the rule being a form rule |
| 12 | Invoices: a posted document | **Pass.** INV/2026/00001 reads **Payment Terms 21 Days, read-only**, and no Due Date — the term is set, so Odoo's "Due Date *or* Payment Terms" shows the term |
| 13 | Invoices: the picker | **Pass.** It offers the 14 active terms and leaves out the archived *TEST UI default row*. They come newest first, not in Sequence order (difference 3) |
| 14 | Invoices: a new invoice in the browser | **Pass.** Customer / Vendor **Sunway Construction Group**, Journal Sales, Accounting Date 2026-09-01, no Invoice Date, Payment Terms left empty → after Submit the record reads **30 Days** (automation C, from the contact) and **Due Date 2026-10-01** (automation D, 2026-09-01 + 30). So the browser's own create starts C |
| 15 | Invoices: changing the term | **Pass.** The same draft set to *30% Now, Balance 60 Days* and saved: **Due Date 2026-10-31**, the later of the two lines (2026-09-01 + 60) |
| 16 | Invoices: a journal entry carries neither | **Pass.** Type → Journal Entry hides **Due Date and Payment Terms** (and Delivery Address, 06's own rule); back to Customer Invoice brings them back. Cancelled without saving |
| 17 | Invoices: Due Date or Payment Terms | **Pass.** Clearing Payment Terms on the draft shows **Due Date 2026-10-31**, the date D last wrote; setting a term hides it again |
| 18 | Contacts: the two terms | **Pass.** *TEST PT Person*'s **Sales & Purchase** tab reads *Sales* · Salesperson \| **Customer Payment Terms 45 Days** · **Vendor Payment Terms** · *Misc* · Reference. The tab shows for a contact under a company, where the Invoicing tab is hidden |
| 19 | Contacts: a company's terms reach a new contact | **Pass.** A contact created in the browser (*TEST UI PT contact*) under **TEST PT Vendor Co** came back with **Customer Payment Terms 45 Days and Vendor Payment Terms 15 Days**, the company's own |
| 20 | Invoices: Confirm dates the document | **Pass**, 18 Sep. The draft of test 15 (*30% Now, Balance 60 Days*, Accounting Date 2026-09-01, no Invoice Date) → **INV/2026/00009, Posted, Invoice Date 2026-09-18** (today) and **Due Date 2026-11-17**, 60 days on from the new Invoice Date. Every field read-only afterwards, Due Date hidden behind the term |
| 21 | Invoices: dated exactly once | **Pass**, 18 Sep, counted in the run history around each browser action. Changing a draft's Invoice Date to 2026-09-05: **D 25 → 26**, C unmoved, Due Date 2026-10-05. Confirm on another draft (Invoice Date already set): **Confirm 26 → 27, D unmoved at 26**, Due Date 2026-10-20 — the document is dated once, by whichever workflow acts |
| 22 | Products: Favorite restored | **Pass**, 18 Sep. Another administrator deleted Products' Favorite while this bundle was being built; it is rebuilt as `6aabf880e43d174ab374dcf0` (03 §2). The form's row 1 reads **Favorite \| Sales \| Purchase**; the List view's quick filters read Product Type · Sales · Purchase · **Favorite** · Category; ticking it on *TEST Favorite Restored* carried to its variant **[TEST-0007]** and moved the product to the **top of the list**, favourites first |

### Differences from Odoo

1. **Nothing checks that the percentages add up to 100, or that an early discount has a single line** (test 5). Odoo
   refuses both. A HAP roll-up over a subtable judges the saved rows only, so the rules refused every new term and are
   built but disabled; they can be switched on the day HAP's roll-ups follow unsaved rows.
2. **No Preview.** Odoo shows an example amount on an example date with its installments; a HAP formula cannot walk a
   subtable's rows. An invoice's own Due Date is the same arithmetic, and is built.
3. **Pickers list terms newest first**, where Odoo orders them by Sequence.
4. **The Lines table shows every line's Days on the next month**; a HAP rule hides a field on a form, not in a table
   column. Inside a term's own Due Terms table it is hidden as Odoo hides it.
5. **An invoice is dated as soon as it has a term.** Odoo waits until the invoice has lines.
6. **The term and the date arrive with the save.** Odoo's onchange fills them as the customer is picked; HAP's
   workflows run after the save, so the form shows them a moment later.
7. **A term an invoice uses can still be deleted.** Odoo refuses ("Uh-oh! Those payment terms are quite popular…").
   HAP has no hook before a delete; only the Accounting Administrator can delete, and Archive is the way to retire one.
8. **Sequence is typed, not dragged**, and a new line does not start at 100 − the other percentages, nor at the
   previous line's days + 30 (Odoo computes both while typing).

### Test records left in the worksheets

- **Payment Terms:** the four `TEST PT` terms from §2 (empty After · 15 Days after End of Month · 30 Days, on the 31st
  · fixed line), all active with Sequence 90, and **TEST UI default row**, active again after test 10.
- **Products:** **TEST Favorite Restored** is left **Favorite**, so the list shows favourites first (test 22).
- **Invoices:** the `TEST PT` documents of §2, and from tests 14–21 **INV/2026/00009** (`11ec708e…`, posted on
  18 Sep, *30% Now, Balance 60 Days*, due 2026-11-17), **INV/2026/00010** (`b24859c8…`, posted, 30 Days, due
  2026-10-20) and the draft `a2f3da54…` (30 Days, Invoice Date 2026-09-05, due 2026-10-05).
- **Contacts:** the `TEST PT` contacts of §2 and **TEST UI PT contact** under TEST PT Vendor Co (test 19).
- **Products:** TEST Favorite Restored and its variant [TEST-0007], from the Favorite fix.

All go after sign-off, with the owner's approval. The tenant's ten terms, their eleven lines and every seeded
reference stay.


## Descriptions rewritten for the app's users (22 Sep 2026)

The owner's rule of 22 Sep 2026: a description in the app says only what the field or button does, for the people using it — no Odoo, no field or model names, no divergences, no build notes. The texts below were rewritten or emptied on the live app and in the builder's constants. The old text is kept here, word for word, because it carried the Odoo references and build reasoning that are no longer in the app.

**Payment Terms**

| Control | Key | Before | After |
|---|---|---|---|
| Sequence | desc | Terms are listed by this number, lowest first — Odoo sets it by dragging the term in its list. | Terms are listed by this number, lowest first. |
| Active | desc | If the active field is set to False, it will allow you to hide the payment terms without removing it. | Untick to hide these payment terms without deleting them. |
| Due Terms | desc | When the invoice falls due: each line gives a date, and the Due Date of an invoice on this term is the latest of them. The worksheet Payment Term Lines, mounted here. | When the invoice falls due: each line gives a date, and the invoice's Due Date is the latest of them. |
| Percent total | desc | The sum of Due over the Due Terms lines whose Value is Percent — Odoo's check that the percentages add up to 100 reads it. | The sum of the percentage lines. It must come to 100. |
| Line count | desc | How many Due Terms lines the term has — the early discount rule reads it. | The number of lines in Due Terms. |

**Payment Term Lines**

| Control | Key | Before | After |
|---|---|---|---|
| Display name | desc | Due, Value, After and Delay Type — how a line reads wherever HAP shows its title. | How the line reads in lists: Due, Value, After and Delay Type together. |
| Payment Terms | desc | The term this line belongs to — the link the Due Terms table on the term is built on. | The payment terms this line belongs to. |
