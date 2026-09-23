# 22 · Demo data — MyTech Products & Services Sdn Bhd

| | |
|---|---|
| What it is | a coherent invented dataset for a customer demo, replacing every test record the build left behind |
| Data | `nocoly/data/demo.json` — the whole story, dates as **offsets from the seeding day** |
| Builder | `nocoly/build/demo.py` — `plan` · `backup` · `wipe` · `tags` `contacts` `products` `variants` `orders` `orderlines` `invoices` `invlines` · `seed` · `check` · `show` |
| Worksheets rebuilt | Contact Tags · Contacts · Products · Product Variants · Orders · Order Lines · Invoices · Invoice Lines |
| Worksheets kept | Countries · States · Taxes · Chart of Accounts · Journals · Payment Terms (and Lines) · Units & Packagings · Product Categories · Incoterms — only their `TEST …` rows go |
| Never touched | the CRM worksheets (Leads, CRM Reporting, Activities, their Configuration) and the Sales app `3e596740-d096-42cd-b948-0b62a0220927` |
| Status | **Half A done 23 Sep 2026** — files written, backup taken, dry run clean. Nothing deleted, nothing created. Awaiting the owner's go for Half B |
| Date | 23 Sep 2026 |

---

## 1 · The story

**MyTech Products & Services Sdn Bhd** resells consumer technology and the services around it to Malaysian
organisations: schools and a college, two clinics and a specialist hospital, two government bodies, a design
studio, a digital agency, two retail resellers, and two individuals who walk in. It buys from a hardware
distributor, a freight company and its landlord.

Every brand is invented — **myBook**, **myPhone**, **myPad**, **myMac**, **myDisplay**, **myKeyboard**,
**myMouse**, **myPencil**, **myPods**, **myCare+** — and none is a real trademark. Every company, person, phone
number and address is made up; **every email address ends in `example.com`**. Prices are in RM at retail-ish
levels. Addresses use the app's own **States** records (all sixteen Malaysian states are there) and its
**Countries** record for Malaysia.

## 2 · What is in it

| Worksheet | Records | What it is |
|---|---|---|
| Contact Tags | **10** | 2 categories — *Industry*, *Account Type* — and 8 tags under them: Education, Healthcare, Government, Design & Media, Retail · Key Account, Reseller, Supplier |
| Contacts | **20** | 15 organisations and individuals (10 customers, 3 suppliers, 2 individuals) + 3 named people and 2 delivery addresses under their companies. Tagged, with payment terms and addresses |
| Products | **19** | 4 computers, 5 phones and tablets (one of them archived), 6 accessories, 4 services |
| Product Variants | **25** | one per product, and **three variants each** on myBook Air 13", myBook Pro 14" and myPhone 16 |
| Orders | **36** | 16 Sales Orders, 9 Quotations, 6 Quotation Sent, 3 Cancelled, 2 templates |
| Order Lines | **119** | 2–6 a document, mixing the 10% and 8% taxes, with line discounts, a Section, a Note and the discount lines |
| Invoices | **28** | 14 posted customer invoices, 6 drafts, 2 cancelled, **1 credit note**, **5 vendor bills** |
| Invoice Lines | **75** | 2–4 a document; the credit note alone has one, because one line item was returned |

Two orders carry six lines rather than the brief's five: `AWAN-RFQ-2026-0401`, whose four product lines gain two
discount lines (one per tax group), and the `TPL-CLASSROOM` template, which is a Section, four products and a
Note.

Plus the two records the wipe keeps on purpose: the **Discount** product and its variant, which Orders'
*Apply Discount* writes its lines with.

### The products

| Group | Category used | Products |
|---|---|---|
| Computers | Goods / IT Equipment | myBook Air 13" · myBook Pro 14" · myMac 24" · myMac mini |
| Phones & tablets | Goods / IT Equipment | myPhone 16 · myPhone 16 Pro · myPad Air 11" · myPad Pro 13" · **myPhone 15 (archived)** |
| Accessories | Goods / Consumables | myDisplay Studio · myKeyboard · myMouse · myPencil Pro · myPods Pro · USB-C hub |
| Services | Services | myCare+ · Setup & Migration · Onsite Support Day (in *Days*) · Device Enrolment |

Goods carry the Sales **10% G** and Purchase **10% G** taxes; services carry **8% S**. Units are the app's own
*Units* and *Days*.

### Dates

**Every date in `demo.json` is an offset in days from the day the seed runs.** The oldest order is at day −348
and the newest at day −2; quotations run out to day +49. The dataset therefore reads as "the last twelve
months" whenever it is reseeded, and the overdue invoices stay overdue. Order values trend gently upward over
the twelve months, so a dashboard has a shape to draw.

## 3 · What each part demonstrates

| Feature | The records that exercise it |
|---|---|
| **Quotations** view | the 9 Quotations and the 6 Quotation Sent; the 2 templates are excluded by its own `Is Template` filter |
| **Orders** view | the 16 Sales Orders |
| **Templates** view | `Starter Classroom Pack`, `Clinic Front-Desk Bundle` |
| **To Invoice** quick filter | AWAN-PO-2026-0310 · SMBD-PO-2026-0502 · SRW-PO-2026-207 · HPSC-PO-2026-0788 · TANWM-2026-0051 |
| **To Upsell** quick filter (Upselling Opportunity) | KTN-PO-2026-0119 · GGR-PO-91104 |
| Fully Invoiced | 9 Sales Orders |
| **Confirm** | the 9 Quotations and 6 Quotation Sent orders it is offered on |
| **Cancel** | any Quotation, Quotation Sent or unlocked Sales Order |
| **Set to Quotation** | the 3 Cancelled orders and the 6 Quotation Sent ones |
| **Mark as Sent** | the 9 Quotations |
| **Deliver** | the 16 Sales Orders; 2 of them are part-delivered already (SMBD-PO-2026-0502, SRW-PO-2026-207) and 2 not delivered at all (HPSC-PO-2026-0788, TANWM-2026-0051). Delivery Status follows the lines by itself since 23 Sep 2026 (16 §15) |
| **Apply Discount** | HPSC-RFQ-2026-0812 (Global Discount 10%), AWAN-RFQ-2026-0401 (Global Discount 5%), GGR-RFQ-93012 (**Fixed Amount** RM 500) — each already carrying the lines the button writes, one per tax group |
| **Send Quotation** | every quotation; every customer has an Email |
| **Share for Signature** | the open quotations. It is **withheld** on the two expired ones — SMBD-RFQ-2026-0611 (expired 12 days ago) and KTN-RFQ-2026-0288 (4 days ago) |
| Expiration | 2 open quotations expire within the week (MPSP-RFQ-2026-0512 in 3 days, AWAN-RFQ-2026-0377 in 6) and 2 have expired; JPNJ-RFQ-2026-0091 expires in 2 |
| **Locked** | 4 Sales Orders — SMBD-PO-2025-0418, SRW-PO-2025-114, JPNJ-T-2026-007, SRW-PO-2026-207 |
| **Invoicing Closed** | MPSP-PO-2026-0455, GGR-PO-91104 |
| **Signed** | SRW-PO-2026-207 (Rajesh Kumar) and HPSC-PO-2026-0788 (Nor Azlina Hashim) — see §5 |
| Sections and Notes | JPNJ-T-2026-007 has both; TPL-CLASSROOM has both; INV-JPNJ-007A a Section, INV-JPNJ-007B a Note |
| Incoterms | GGR-PO-88231 (DAP), HPSC-PO-2026-0221 (CIF), MPSP-RFQ-2026-0512 (EXW), MPSP-RFQ-2026-0603 (DDP), each with an Incoterm Location |
| Line discounts | 4 orders carry per-line discounts of 5–10% — JPNJ-T-2026-007, AWAN-PO-2026-0310, KTN-PO-2026-0119, JPNJ-RFQ-2026-0091 — and three invoices mirror them |
| **Invoices** view | 23 customer documents (invoices and the credit note) |
| **Bills** view | the 5 vendor bills |
| Invoice **Confirm** | the 6 drafts |
| Invoice **Cancel** / **Reset to Draft** | the 6 drafts / the 14 posted, 2 cancelled and the credit note |
| Overdue on the demo day | **6** — INV-KTN-0119 (28 days, its Due Date computed by the app), INV-NURUL-0044 (19), INV-SMBD-0502 (17), BILL-LOGISTIK-7741 (15), INV-GGR-91104 (11), INV-HPSC-0640 (3) |
| Payment Status (23 Sep 2026, `paid` / `paid_offset` in demo.json) | **12 Paid** — every posted document not overdue, paid in full between its invoice and due dates; **1 Partially Paid** — INV-SMBD-0502, 50,000.00 of 113,592.00 (63,592.00 due); **15 Not Paid** — the other five overdue, the 7 drafts and the 3 cancelled. *Register Payment* is offered on the 6 posted documents not yet Paid (five overdue and the part-paid one); *Reset to Draft* is no longer offered on the 13 Paid or Partially Paid ones, which narrows the row two above |
| The numbering the Confirm workflow reproduces | INV/2025/00001–00004 then INV/2026/00001–00012, BILL/2025/00001 and BILL/2026/00001–00003, and **RINV/2026/00001** for the credit note (the Sales journal has a Dedicated Credit Note Sequence) |
| Draft numbering | 7 drafts whose Number reads `Draft` |
| *Due Date follows the Payment Terms* + *Payment Terms follow the Customer / Vendor* | INV-KTN-0119 states **neither** Payment Terms nor Due Date, so both come from the customer |
| A payment term with two lines | *30% Now, Balance 60 Days* on Kolej Teknologi Nusantara, on INV-KTN-0102 and INV-KTN-0119 |
| Payment term variety | Immediate Payment · 15 · 21 · 30 · 45 Days · 30% Now, Balance 60 Days |
| Archived records | myPhone 15 and its variant |
| Variants | myBook Air 13" (3), myBook Pro 14" (3), myPhone 16 (3) |

### Orders meant to be invoiced later

The owner will create invoices from some demo orders once the **order → invoice link** exists. Those orders are
flagged `"to_invoice_later": true` in `demo.json` and carry Invoice Status *To Invoice*:

`AWAN-PO-2026-0310` · `SMBD-PO-2026-0502` · `SRW-PO-2026-207` · `HPSC-PO-2026-0788` · `TANWM-2026-0051`

Nothing here invents a link. No invoice names an order in its Source Document, and Source Document is left empty
on every document; the only tie today is the Invoice Status label and the customer.

## 4 · Record numbering

**Orders' Number is an auto-number control (type 33)** — `[S][auto, 5 digits, never resets, start 1]`. The
platform mints it on create and the counter does not go back when records are deleted: the app is at S00023
while its live records are S00006–S00023, so the first five were deleted and the counter carried on. There is no
CLI or API call to restart it — `hap worksheet` has no such command, `GetWorksheetInfo` exposes no counter, and
the only reset is the worksheet's **"…" menu › Reset Auto-number** in the browser ("Specify the number of the
next record; subsequent numbers will increment based on this. Previous record numbers remain unchanged").

So the sequence is **`wipe` → reset Orders' auto-number to 1 in the browser → the seed steps**. Orders is the
**only** wiped worksheet that carries an auto-number.

`demo.json` never states a record number, and the seeder never writes one for an order. An order is keyed on its
**Customer Reference** (a realistic customer PO number, unique across the dataset) and a template on its
**Template Name**; the rowid goes into `ids.json` under `Demo: Orders <key>` and the minted Number under
`numbers` → `Demo: <key>`.

**Invoices' Number is a plain text control** that the Confirm workflow fills, reproducing Odoo's
`sequence.mixin`: `<journal Sequence Prefix>/<year of the Accounting Date>/<n padded to five>`, with an `R` in
front for a credit note on a journal with a Dedicated Credit Note Sequence, and the word `Draft` on an
unnumbered draft. The counter is **not** stored anywhere — the workflow reads the highest Number already issued
under that prefix and year — so wiping Invoices resets invoice numbering by itself. `demo.py` builds the same
numbers at seed time, in Accounting Date order within each prefix and year.

## 5 · Signed orders

The Signature control (type 42) holds an image. The image the two signed demo orders reuse is the one a browser
test left on **S00018** (`TEST signer (browser)`), and the wipe deletes that order — so `backup` copies it into
`ids.json` under `Orders: signature image` while it is still readable.

**What is kept is the path, not the URL a read hands back.** A HAP signature URL carries a time-limited token
(`?e=<epoch>&token=…`) and the server mints a **fresh one on every read**: the same image read twice, two hours
apart, came back with `e=1790101003` and then `e=1790103675`. The stored value is therefore the path and the
token is decoration, so keeping the path means the id never goes stale. Whether writing that path back into a
signature control stores is what `orders` proves; it reads back and says either way, and if it does not store,
the two orders carry **Signed By and Signed On only** and the step reports it.

**A signed quotation cannot stay a quotation in this app.** *Signed: confirm the order* fires when a Signature
appears on an order whose Status is Quotation or Quotation Sent, and confirms it. The two signed demo orders are
therefore **Sales Orders**, which is exactly what Odoo's own online signing produces, and the Signature is
written last and only onto an order that is already a Sales Order. The six Quotation Sent orders are unsigned;
three of them have **Online Signature** ticked, so *Share for Signature* has something to do.

*This departs from the brief's literal "6 Quotation Sent (two signed)".* Keeping two Quotation Sent rows that
look signed would mean filling Signed By and Signed On and leaving the Signature empty — possible, and a
one-line change to `demo.json` if the owner prefers it.

## 6 · What the app cannot express

1. **A product has no attributes.** There is no `product.attribute` / `product.attribute.value` model, so a
   variant is distinguished only by its **Internal Reference** and **Barcode**. The storage and colour of a
   myBook or a myPhone live in the reference — `MYB-AIR13-512-MID` — and the Display Name reads
   `[MYB-AIR13-512-MID] myBook Air 13"`. `demo.json` carries a human `label` ("512GB · Midnight") for each
   variant so it is ready the day attributes exist, and nothing today displays it.
2. **A child contact cannot have its own address.** *copy company details to its contact* fills a child's
   Street, Street 2, City, State, ZIP, Country, Tax ID, Company ID, DUNS, both payment terms and the
   salesperson from its company, and *push company address and Tax ID to its contacts* re-fills them whenever
   the company changes. So the two delivery addresses (*Stor ICT Blok C*, *Gudang Melaka Tengah*) carry a name,
   an email and a phone of their own and their company's address. `demo.json` states no address on a child, and
   `demo.py` writes none.
3. **A multi-variant product's Internal Reference and Cost can only be set once.** *copy a product's Internal
   Reference, Cost, Weight and Volume to its active variant* gets **all** of the product's active variants and
   writes the product's values onto every one, so changing either on a product with three variants would wipe
   the per-variant references. `demo.py` writes those two fields on such a product **only when it creates it**,
   and reports a later difference instead of writing it.
4. **There is no order → invoice link.** Out of scope for this job; §3 names the five orders meant to be
   invoiced once it exists.
5. **A discount line is arithmetic, not a link.** The three discount-bearing orders carry the lines *Apply
   Discount* would have written (the Discount product, quantity 1, a negative Unit Price, one line per tax
   group, labelled `Discount 10.00%` / `Discount`). Pressing the button on them rewrites the same lines.
6. **The four story groups do not match the Product Categories tree.** Computers and Phones & tablets both map
   to *Goods / IT Equipment* and Accessories to *Goods / Consumables*, because Product Categories is
   configuration the job keeps and no new category is created. `demo.json` keeps the story group on each product
   as `group`.

## 7 · The wipe

The owner approved deleting **after a backup** (relayed 23 Sep 2026). `backup` must run first and `wipe` refuses
without it.

`backup` writes `nocoly/build/backups/demo-preseed-<stamp>/`:

* `<worksheet>.json` for each of the 18 worksheets — `count`, `rows` (the full listing of every record) and
  `detail` (GetRowDetail's complete `rowData` for every row the wipe would delete). Each file's row count is
  verified against the live count as it is written.
* `_manifest.json` — the stamp, the app id, the two kept rowids, the signature-image path, and per worksheet the
  id, the count, **every live rowid** and the **exact delete list** as `[rowid, identity]`.

`wipe` then refuses unless: a `demo-preseed-*` folder with a manifest exists; it is of this app; it covers every
worksheet; every file's row count matches its manifest entry; and **every record that is live now is in it** —
so a row the owner added after the backup stops the wipe rather than being swept up. It deletes only the rowids
the manifest names, checks each one still reads as the identity the backup recorded, and re-reads the worksheet
to prove the delete stored. Deletion order is children before parents, and within a self-referencing worksheet
(Contact Tags' Category, Contacts' Company, Product Categories' Parent Category) children before their own
parents. Re-running is a no-op.

**Only records are deleted.** No control, view, rule, button, workflow or worksheet is touched, and the delete is
soft — `--permanent` is never passed, so every row goes to the worksheet's recycle bin. `--trigger-workflow` and
`-y` are written out in full, because the CLI sends `triggerWorkflow: false` without the first and hangs without
the second (BUILDING.md).

### What it takes out

| Worksheet | Live | Deleted | Left |
|---|---|---|---|
| Invoice Lines | 39 | 39 | 0 |
| Order Lines | 37 | 37 | 0 |
| Invoices | 36 | 36 | 0 |
| Orders | 18 | 18 | 0 |
| Product Variants | 22 | 21 | 1 (Discount) |
| Products | 21 | 20 | 1 (Discount) |
| Contacts | 8 | 8 | 0 |
| Contact Tags | 3 | 3 | 0 |
| Payment Term Lines | 18 | 7 | 11 |
| Payment Terms | 15 | 5 | 10 |
| States | 2107 | 5 | 2102 |
| Taxes | 40 | 5 | 35 |
| Chart of Accounts | 90 | 3 | 87 |
| Journals | 11 | 4 | 7 |
| Units & Packagings | 34 | 4 | 30 |
| Product Categories | 11 | 4 | 7 |
| Incoterms | 12 | 1 | 11 |
| Countries | 252 | 1 | 251 |
| | **2774** | **221** | **2553** |

A configuration row counts as a test leftover when its title or its name reads `TEST…` or contains ` TEST `; the
seven Payment Term Lines are recognised by their parent term instead, because a line has no name of its own.
`plan` prints the list by name so it can be read before anything is deleted.

## 7b · Payment terms and due dates: the dataset agrees with the automations rather than fighting them

*Payment Terms follow the Customer / Vendor* writes the contact's own Customer or Vendor Payment Terms onto a
document when it is created, and *Due Date follows the Payment Terms* then computes the Due Date. Whether the
first overwrites a term the create already sent has not been measured — so the dataset is built so that it
cannot matter:

* **every document's Payment Terms is exactly its contact's own term**, checked over all 28 documents;
* **every stated Due Date equals the invoice date plus that term's days**, checked over all 28.

A two-line term puts the Due Date on its **last** line: the live `INV/2026/00009` carries *30% Now, Balance 60
Days* with Invoice Date 2026-09-18 and Due Date 2026-11-17, exactly 60 days later. `INV-KTN-0102` states that
term and a Due Date 60 days out; `INV-KTN-0119` states neither and is the one document that shows the two
automations doing the work.

The term day-counts used: Immediate Payment 0 · 15 Days · 21 Days · 30 Days · 45 Days · 30% Now, Balance 60
Days → 60.

## 8 · What the automations own

`demo.py` writes none of these and compares none of them; it reports them.

| Owned by | Fields |
|---|---|
| *Roll the lines up into the invoice* | an invoice's Untaxed Amount, Tax, Total, Amount Due |
| the Order Lines 汇总 | an order's Untaxed Amount, Tax, Total |
| *Orders: Delivery Status follows …* (three workflows, `delivery.py`) | an order's Delivery Status — from its lines' Quantity and Quantity Delivered, which **are** written |
| *fill the account of a new line* | an invoice line's Account |
| *create a new product's variant* | a product's first variant |
| *copy a product's … to its active variant* | a multi-variant product's Internal Reference and Cost after creation |
| *copy company details to its contact* · *push company address and Tax ID to its contacts* | a child contact's address, identifiers, payment terms and salesperson |
| *Due Date follows the Payment Terms* · *Payment Terms follow the Customer / Vendor* | INV-KTN-0119's Payment Terms and Due Date — neither is written nor compared; every other document states values the automations agree with (§7b) |
| *the Country follows the State* | a contact's Country (written as well, and it agrees) |
| *Signed: confirm the order* | the Status of an order that gains a Signature — which is why the signature goes only on a Sales Order |

Quantity Delivered and Quantity Invoiced **are** written, so no status label stands on nothing: every product
line of a fully delivered order, the first two lines of a part-delivered one, and the quantities of a Fully
Invoiced or Upselling order.

## 9 · Reading records

`demo.py` reads through **GetRowDetail's `rowData`**, one call per record through the CLI's own session. It is
the only complete read — the record listing blanks a hidden control and leaves a Text or Number its view does
not show out of the row altogether, and `record get` drops a control added after the record existed
(BUILDING.md). `rowData` is keyed by controlId and returned all 53 of Orders' fields, hidden ones included, in
0.15 s; `record get` through the command line takes 1.2 s for the same record. A single select comes back as a
JSON list of option **keys**, so every label is resolved against the live option table.

The cheap listing is still used where a title, a relation or a dropdown is enough: recognising the test
leftovers and counting rows.

## 10 · Running it

```
~/.hap-venv/bin/python nocoly/build/demo.py plan        # dry run, writes nothing
~/.hap-venv/bin/python nocoly/build/demo.py backup      # export everything, pin the delete list
~/.hap-venv/bin/python nocoly/build/demo.py wipe        # delete only what the manifest names
#   -> then, in the browser: Orders "..." > Reset Auto-number > next record 1
~/.hap-venv/bin/python nocoly/build/demo.py seed        # tags contacts products variants orders
                                                        #   orderlines invoices invlines, then check
~/.hap-venv/bin/python nocoly/build/demo.py check       # counts, buckets, views, overdue, arithmetic
```

Every step reads the live state first and is safe to re-run; a second run writes nothing. `show` prints the
dataset without calling the app.

## 11 · Test results

| Step | Run | Result |
|---|---|---|
| `plan` | 23 Sep 2026 | every reference in `demo.json` resolves to exactly one live record; 221 rows named for deletion, 332 to create |
| `backup` | 23 Sep 2026 | `backups/demo-preseed-20260923-020223`, 2774 records of 18 worksheets, every file's row count matching the live count; S00018's signature path kept in `ids.json` |
| `wipe` | — | not run — awaiting the owner's go |
| the seed steps | — | not run |
| `check` | — | not run |
| UI | — | not tested; implementation agents have no browser |
