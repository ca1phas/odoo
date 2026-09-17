# 10 · Payment Terms

| | |
|---|---|
| Nocoly app | ERP Master · menu group **Invoicing**, after Journals — Odoo's *Configuration ▸ Invoicing ▸ Payment Terms* |
| Worksheets | **Payment Terms**, and **Payment Term Lines** mounted inside it as the *Due Terms* table |
| Odoo models | `account.payment.term`, `account.payment.term.line` |
| Reference | **casimir.odoo.com — Odoo saas~19.4+e**: both models' fields by module, constraints, defaults, every view's raw arch, the window action and menu, the decimal precision, all 10 terms and 11 lines, every field in the database that points at either model, the invoice-form and contact-form arch that places them, and the payment terms of every invoice, contact and sales order — extracted read-only to `nocoly/reference/odoo-19.4/account.payment.term.md`, with the data in `nocoly/data/casimir-payment-terms.json`. Behaviour the tenant cannot show — the constraints, the line defaults, how a term dates an invoice, how a company's terms reach its contacts — is read from the Odoo 19.0 source in this repo: `addons/account/models/account_payment_term.py`, `account_move.py`, `partner.py`, `odoo/addons/base/models/res_partner.py` |
| Phase | 1 — **bundle 3 of 6** (Product Categories · Chart of Accounts · Payment Terms · Countries · States · Taxes) |
| Status | §1 written 17 Sep 2026 |

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
