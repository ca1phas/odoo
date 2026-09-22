# 21 · The order → invoice link — requirements

| | |
|---|---|
| Odoo models | `sale.order` · `sale.order.line` · `account.move` · `account.move.line` · `sale.advance.payment.inv` |
| Odoo source | `addons/sale/models/sale_order.py`, `sale_order_line.py`, `sale/models/account_move.py`, `sale/models/account_move_line.py`, `sale/wizard/sale_make_invoice_advance.py`, `sale_stock/models/sale_order.py`, `sale_stock/models/account_move.py`, `account/models/account_move.py`, `sale/views/sale_order_views.xml` |
| Source of facts | **the 19.0 source under `addons/` only.** casimir.odoo.com expired on 22 Sep 2026 and no extract of `sale_order_line.invoice_lines` or of the down-payment wizard was taken. Nothing below comes from the tenant |
| Bundle | **Order → Invoice**, `bo2i`, 0 new worksheets, 4 worksheets touched — a wiring bundle, not a ground-up build |
| Depends on | 16 Orders, 07 Invoice Lines, 06 Invoices, 13 Taxes, 09 Chart of Accounts — all built |
| Status | **Requirements only, 23 Sep 2026. Nothing built. No app write was made while writing this.** |
| Date | 23 Sep 2026 |

---

## 1 · What it is, and why it is the biggest gap

Odoo's sales-to-invoicing chain hangs off **one** stored many-to-many:
`sale_order_line_invoice_rel`, between `sale.order.line` and `account.move.line`
(`sale/models/sale_order_line.py:257-261` and `sale/models/account_move_line.py:12-16`). Every figure a user
reads is derived from it — the order's Invoice Status, the line's Invoiced Quantity, the invoiced and
un-invoiced amounts, the *Invoices* smart button, the *To Invoice* and *To Upsell* lists, and the whole down
payment machinery. `sale.order.invoice_ids` is **not** a stored field: it is a compute that walks the line-level
relation (`sale_order.py:571-579`).

ERP Master holds both ends of that relation as real, mounted worksheets, and **nothing joins them.** Which is
why, in the app today:

| Blocked | Because |
|---|---|
| **Create Invoice** (Orders button 6 of 20, `16-orders.md` §3) | nothing writes an invoice from an order |
| **Invoice Status** on Orders (`6ab0c5eae54d2a34fa4e8131`) | the control and its four options exist; nothing can compute them |
| **Quantity Invoiced** on Order Lines (`6ab0c864e43d174ab37535fc`) | a plain Number a person types (`16-orders.md` §7.2 item 8) |
| Quantity To Invoice, Untaxed Invoiced / To Invoice, Already invoiced, Un-invoiced Balance | not built at all |
| Down payments | not built at all (`16-orders.md` §4) |
| Carrying the **Incoterm** onto the invoice | both fields exist on both worksheets; nothing copies one |
| Smart buttons *Invoices* (on the order) and *Sales Orders* (on the invoice) | no relation to count |

## 2 · Odoo's shape, from the 19.0 source

### 2.1 The relations, and which are stored

| Field | Model | Kind | Source |
|---|---|---|---|
| `invoice_lines` | `sale.order.line` | **many2many, stored** — table `sale_order_line_invoice_rel`, columns `order_line_id` / `invoice_line_id` | `sale_order_line.py:257-261` |
| `sale_line_ids` | `account.move.line` | **the same table, read the other way** — `readonly=True, copy=False` | `account_move_line.py:12-16` (in `sale`) |
| `invoice_ids` | `sale.order` | many2many, **computed, not stored**, `compute='_get_invoiced'`, with a custom `search=` | `sale_order.py:240-245`, `571-579`, `581-616` |
| `invoice_count` | `sale.order` | integer, computed with it | `sale_order.py:239` |
| `sale_order_count` | `account.move` | integer, `compute='_compute_origin_so_count'` over `line_ids.sale_line_ids` | `sale/models/account_move.py:46-49` |

`_get_invoiced` is `order.order_line.invoice_lines.move_id.filtered(lambda r: r.move_type in ('out_invoice',
'out_refund'))` — so the order's invoice list is **derived, two hops from the line-level link**, and it
deliberately picks up credit notes made directly from an invoice, which are not otherwise attached to the order
(the comment at `sale_order.py:572-575`).

`_copy_data_extend_business_fields` copies `sale_line_ids` when an invoice line is duplicated
(`account_move_line.py:37-39`), which is how a reversal stays attached to the order.

### 2.2 What the invoice is made of — `_prepare_invoice`

`sale_order.py:1413-1451`. Everything in the values dict, with what ERP Master can supply:

| Odoo key | From | Here |
|---|---|---|
| `move_type` | literal `'out_invoice'` | Type → **Customer Invoice** |
| `ref` | `self.client_order_ref or self.name` | Customer Reference, else Number |
| `invoice_origin` | `self.name` | Source Document ← Number |
| `narration` | `self.note` | Terms and Conditions ← Terms and conditions |
| `partner_id` | `self.partner_invoice_id` | Customer / Vendor ← **Invoice Address** |
| `partner_shipping_id` | `self.partner_shipping_id` | Delivery Address |
| `invoice_payment_term_id` | `self.payment_term_id` | Payment Terms |
| `invoice_user_id`, `user_id` | `self.user_id` | Salesperson |
| `journal_id` | `self.journal_id`, **only when set** (`:1449-1450`) | Journal |
| `currency_id`, `company_id` | order's | one currency, one company per app copy |
| `fiscal_position_id` | order's, else derived from the partner | not modelled |
| `campaign_id`, `medium_id`, `source_id`, `team_id` | UTM / Sales Team | not modelled (Sales app, out of Phase 1) |
| `payment_reference` | `self.reference` | not modelled |
| `preferred_payment_method_line_id`, `transaction_ids` | payment machinery | not modelled |
| `invoice_line_ids` | `[]`, then filled | the subtable |

**`invoice_date` and `date` are not in the dict.** A created invoice is a draft with no invoice date; posting
fills it. That matches 06's Confirm, which "fills Invoice Date with today when it is empty".

**Two things `sale` itself does not carry, and `sale_stock` does** (`sale_stock/models/sale_order.py:298-302`):

```python
invoice_vals['invoice_incoterm_id'] = self.incoterm.id
invoice_vals['delivery_date'] = self.effective_date and ...
```

and `incoterm_location` is not copied at all — it is a **compute on the invoice**, taking the first non-empty
`incoterm_location` of the orders behind its lines (`sale_stock/models/account_move.py:129-137`, extending
`account/models/account_move.py:2250` which is a `pass`). `account.move.invoice_incoterm_id` otherwise defaults
from the company (`account/models/account_move.py:2234`).

### 2.3 Which lines are invoiced, and how sections and notes are carried

`_get_invoiceable_lines` (`sale_order.py:1501-1550`), walking `order_line` **in order**:

1. a `line_section` **resets** the buffer to itself; a `line_subsection` starts a subsection buffer;
2. a line that is not a `line_note` and whose `qty_to_invoice` rounds to zero is **skipped**;
3. a line is taken when `qty_to_invoice > 0`, or `qty_to_invoice < 0` **and `final`** (the deduct-down-payments
   pass), or it is a `line_note`;
4. a down-payment line is set aside and appended **last**;
5. when a real line is taken, the buffered section (and subsection) are emitted **in front of it** and the
   buffer cleared. A note met while a section is buffered joins the buffer instead of being emitted.

So: **a section with no invoiceable line under it never reaches the invoice**, and a note behind such a section
does not either. A note with no pending section is emitted on its own.

Then in `_create_invoices` (`sale_order.py:1552-1692`):

- `if all(line.display_type for line in invoiceable_lines): continue` (`:1580`) — an order that yields only
  sections and notes produces **no invoice at all**;
- a *Down Payments* section line is inserted before the first down-payment line (`:1586-1594`, and
  `_prepare_down_payment_section_line` at `:2013`);
- a down-payment line goes on at **quantity −1** with its tax data reversed (`:1600-1605`);
- nothing invoiceable anywhere → `UserError` with the long *Cannot create an invoice* text
  (`:1616-1617`, `_nothing_to_invoice_error_message` at `:1486`);
- **grouping**: with `grouped=False` — the wizard's default, since `consolidated_billing` defaults True
  (`sale_make_invoice_advance.py:55-59`, `:138-141`) — orders sharing
  `company_id, partner_id, partner_shipping_id, currency_id, fiscal_position_id`
  (`_get_invoice_grouping_keys`, `sale_order.py:1483`) are merged into **one** invoice, with `ref`,
  `invoice_origin` and `payment_reference` concatenated (`:1638-1656`);
- lines are resequenced from 1 only when a grouping happened (`:1658-1677`);
- `final` and a negative total flips the move to a credit note (`:1681-1686`);
- every created move gets an origin-link chatter message (`:1688-1693`).

One invoice line per order line, from `_prepare_invoice_line` (`sale_order_line.py:1513-1558`):
`display_type` (`'product'` when the line has none), `sequence`, `name` (the journal-item full name),
`product_id`, `product_uom_id`, `quantity = qty_to_invoice`, `discount`, `price_unit`,
`tax_ids = Command.set(self.tax_ids.ids)`, `sale_line_ids = [Command.link(self.id)]`, `is_downpayment`,
`extra_tax_data`, and `account_id = False` on a display-type line (`:1556-1557`).

**Note the two that matter here**: the invoice line's taxes are the **order line's** taxes, not the product's;
and the link is written at creation, in the same `create`.

### 2.4 The figures

| Odoo field | Where | Rule |
|---|---|---|
| `qty_invoiced` | line, **stored compute** | sum over `invoice_lines` of the quantity, **`+` for `out_invoice`, `−` for `out_refund`**, skipping only lines whose move is `cancel` — so a **draft** invoice already counts (`sale_order_line.py:984-1017`) |
| `qty_invoiced_posted` | line, non-stored | the same restricted to `state == 'posted'` (`:1020-1034`) |
| `qty_to_invoice` | line, **stored compute** | `product_uom_qty − qty_invoiced` when the product's `invoice_policy == 'order'`, else `qty_delivered − qty_invoiced`; **0** when `state != 'sale'` or the line has a `display_type` (`:1048-1075`) |
| `untaxed_amount_invoiced` | line, stored | sum of `price_subtotal` of **posted** invoice lines, minus refunds (`:1123-1141`) |
| `amount_invoiced` | line, non-stored | the same on `price_total`, signed by `direction_sign` (`:1143-1153`) |
| `untaxed_amount_to_invoice` | line, stored | the line's subtotal on the policy quantity **minus `untaxed_amount_invoiced`**; **drafts are ignored on purpose** (`:1155-1201`) |
| `amount_invoiced` / `amount_to_invoice` | order, non-stored | the sums of the lines' (`sale_order.py:777-784`) |
| `invoice_status` | line, **stored compute** | below |
| `invoice_status` | order, **stored compute** | below |

**The line's status** (`sale_order_line.py:1078-1104`), in this order:

1. `state != 'sale'` → **no**;
2. a down payment line whose `untaxed_amount_to_invoice == 0` → **invoiced**;
3. `qty_to_invoice` not zero → **to invoice**;
4. `state == 'sale'` **and** the product's policy is `order` **and** `product_uom_qty >= 0` **and**
   `qty_delivered > product_uom_qty` → **upselling** — *delivered more than was ordered on an ordered-quantity
   product*;
5. `qty_invoiced >= product_uom_qty` → **invoiced**;
6. otherwise → **no**.

**The order's status** (`sale_order.py:620-665`), over its lines **excluding down payments and display types**
(`lines_domain` at `:633`):

1. `state != 'sale'` → **no** (every non-confirmed order, `:628-629`);
2. any line **to invoice** →
   - if some other line is **no**, and *every* invoiceable line fails `_can_be_invoiced_alone()` (i.e. they are
     all the company's discount product — `sale_order_line.py:1108-1114`) → **no**;
   - otherwise → **to invoice**;
3. else, lines exist and all are **invoiced** → **invoiced**;
4. else, lines exist and all are **invoiced or upselling** → **upselling**;
5. otherwise → **no**.

Two side effects worth knowing: reaching **upselling** schedules a to-do activity on the salesperson
(`_compute_field_value` at `sale_order.py:1966-1979`, `_create_upsell_activity` at `:1981`); and the order list
decorates *to invoice* in blue, *invoiced* in green, *upselling* in orange (`sale_order_views.xml:167-170`).

### 2.5 What posting, resetting, cancelling and deleting do

| Action | Effect on the order's figures | Source |
|---|---|---|
| create a **draft** invoice | `qty_invoiced` rises at once; `untaxed_amount_invoiced` does **not** | `sale_order_line.py:1007-1017` vs `:1123-1141` |
| **post** | `untaxed_amount_invoiced` rises, `untaxed_amount_to_invoice` falls; down-payment line descriptions and prices are recomputed | `sale/models/account_move.py:83-97` |
| **reset to draft** | down-payment descriptions recomputed; the figures stay | `sale/models/account_move.py:99-105` |
| **cancel** | `qty_invoiced` falls back — a cancelled move is excluded | `sale_order_line.py:1010` |
| **delete** | the m2m rows go with the lines; down-payment **order** lines whose only invoice lines were on that move are deleted too | `sale/models/account_move.py:26-31` |
| a **credit note** made from the invoice | its lines carry `sale_line_ids` through the copy, and `qty_invoiced` **subtracts** them | `account_move_line.py:37-39`, `sale_order_line.py:1012-1016` |

### 2.6 Down payments

The wizard `sale.advance.payment.inv` (`sale/wizard/sale_make_invoice_advance.py`) is what the *Create Invoice*
button actually opens. Three choices on `advance_payment_method` (`:13-23`):

| Choice | Does |
|---|---|
| **`delivered` — Regular invoice** (default) | `sale_orders._create_invoices(final=self.deduct_down_payments, grouped=not self.consolidated_billing)` (`:140-141`) |
| **`percentage` — Down payment (percentage)** | one order only |
| **`fixed` — Down payment (fixed amount)** | one order only |

For a down payment (`:142-196`):

1. the order's real lines are turned into tax base lines and `account.tax._prepare_down_payment_lines` splits
   the requested percentage or amount **across the tax groups** (`:147-169`);
2. `_create_down_payment_section_line_if_needed` adds a **Down Payments section** order line
   (`sale_order.py:2055-2071`, values at `:2074-2084`);
3. `_create_down_payment_lines_from_base_lines` adds one **`is_downpayment` order line per tax group** with
   `product_uom_qty = 0.0`, **no product**, the split `price_unit`, that group's `tax_ids` and the
   `extra_tax_data` (`sale_order.py:2036-2053`, `:2086-2104`);
4. an invoice is created from `_prepare_invoice()` plus one line per down-payment order line, quantity **1**,
   named *Down payment of X%* or *Down Payment*, on the company's `downpayment_account_id`, or the product's
   or category's down-payment / income account (`:199-253`);
5. the **final** invoice then re-emits those order lines at **quantity −1** with the tax data reversed
   (`sale_order.py:1600-1605`), which is how the deposit is deducted.

**There is no deposit *product* in 19.0** — a down-payment line carries no `product_id`
(`sale_order.py:2086-2104`); the account comes from the company or from the products being deposited against.
Older Odoo's *Down payment* service product is gone. Its description is recomputed as the invoice moves
between draft, cancelled and posted: *Down Payment: <date> (Draft)* / *Down Payment (Cancelled)* /
*Down Payment (ref: <payment reference> on <date>)* (`sale_order_line.py:484-512`).

`has_down_payments`, `deduct_down_payments` (default **True**), `amount_invoiced` and
`display_draft_invoice_warning` — *a draft invoice already exists* — are the wizard's own UI
(`:28-56`, `:91-99`).

### 2.7 The buttons and the two lists

`sale/views/sale_order_views.xml`:

| | |
|---|---|
| `:271-279` | **Create Invoice**, `btn-primary`, `invisible="invoice_status != 'to invoice'"` |
| `:280-287` | **Create Invoice** again, `invisible="invoice_status != 'no' or state != 'sale'"`, with `default_advance_payment_method: 'percentage'` — the *nothing to invoice yet, take a deposit* path |
| `:121-124` | **Create Invoices**, the same action from the list, over a selection |
| `:412` | the **Invoices** smart button → `action_view_invoice` (`sale_order.py:1455-1481`) |
| `:994` | `<filter string="To Invoice" name="to_invoice" domain="[('invoice_status','=','to invoice')]"/>` |
| `:995` | `<filter string="To Upsell" name="upselling" domain="[('invoice_status','=','upselling')]"/>` |
| `:1172`, `:1188` | two **dedicated actions** with those same domains — the Sales dashboard's *Orders to Invoice* and *Orders to Upsell* |

---

## 3 · What ERP Master holds today — read live, 23 Sep 2026

App `6cb4d051-a33c-4bf9-b56f-5f47f0e85dc9`. Record counts by paging: Orders **18**, Order Lines **37**,
Invoices **36**, Invoice Lines **39**. *Read this again before building — the owner edits these worksheets in
the browser.*

### 3.1 Orders — `6ab09897e43d174ab3752d7b`, 45 controls

| Control | Id | Type | Perm | Note |
|---|---|---|---|---|
| Status | `6ab0a847e54d2a34fa4e7b96` | 11 | `100` | Quotation `e43e8565-506a-47c9-9883-29aabeded2c0` · Quotation Sent `9dee5df2-d1d3-4382-aa22-37fedeabcba0` · **Sales Order `df9b6145-8288-489c-b823-e572fd22a5cb`** · Cancelled `a3d06913-ae24-4a9e-8082-6994f2e18025` |
| Number | `6ab0a141805aef703286cf7f` | 33 | `111` | auto-number, always present |
| Customer | `6ab0a141805aef703286cf80` | 29 | — | → Contacts |
| Invoice Address | `6ab0a141805aef703286cf83` | 29 | — | → Contacts. **`partner_invoice_id`** |
| Delivery Address | `6ab0a141805aef703286cf85` | 29 | — | → Contacts |
| **Invoice Status** | `6ab0c5eae54d2a34fa4e8131` | **11** | **`100`** | **no alias.** Upselling Opportunity `95b10f68-72da-466f-80e5-1e43d694249e` · To Invoice `a9150ecb-c7fa-4601-b84a-da01a31f1003` · Fully Invoiced `0ac57562-a137-4765-8165-44fc7d72776c` · Nothing to Invoice `1d0faacc-2a0f-490d-b339-d077c034bc62` |
| Payment Terms | `6ab0a425805aef703286cfdc` | 29 | — | → Payment Terms |
| Invoicing Closed | `6ab10089e54d2a34fa4e88c4` | 36 | `110` | `invoicing_closed` |
| Order Lines (subtable) | `6ab0c740e43d174ab37535b0` | 34 | — | → Order Lines, reverse `…35b1` |
| Untaxed Amount / Tax / Total | `…35b8` / `…35b9` / `…35ba` | 37 | — | 汇总 sum over the subtable |
| Terms and conditions | `6ab2587bbd43f5576223fb06` | 41 | `111` | `note` |
| Salesperson | `6ab0bff27d58b0f449316ae1` | 26 | `101` | |
| Customer Reference | `6ab0c1cdbd43f55762c783dd` | 2 | — | `client_order_ref` (no alias live) |
| Journal | `6ab0c459805aef703286d785` | 29 | — | under the **Invoicing** divider `6ab0c459805aef703286d784`, row 21 |
| Incoterm | `6ab29e24e43d174ab3cd7675` | 29 | `111` | `incoterm`, parked at row 9999 |
| Incoterm Location | `6ab0c528e54d2a34fa4e8124` | 2 | — | `incoterm_location` |
| Delivery Date | `6ab0a9dabd43f55762c78047` | 16 | — | |
| Tax Mode | `6ab0bfaf7d58b0f449316ad8` | 11 | — | Tax Excluded / Tax Included |
| Source Document | `6ab0c23fe54d2a34fa4e8053` | 2 | — | |

Views: **All**, **Quotations**, **Orders** (`6ab0df017d58b0f449316f4e`; filter Status is Sales Order and Is
Template ≠ ticked; columns Number · Quotation/Order Date · Customer · Salesperson · Total · **Invoice Status**;
**one quick filter, on Invoice Status**), **Templates**.
Buttons: Send Quotation · Confirm · Cancel · Set to Quotation · Mark as Sent · Deliver · Apply Discount ·
Share for Signature. **No Create Invoice, no Close Invoicing, no Reopen Invoicing.**
8 rules; none names Invoice Status.

### 3.2 Order Lines — `6ab0c740e43d174ab37535b2`, 19 controls

| Control | Id | Type | Perm | Alias |
|---|---|---|---|---|
| Orders | `6ab0c740e43d174ab37535b1` | 29 | — | `order_id` |
| Sequence | `6ab0c740e43d174ab37535b7` | 6 | — | `sequence` |
| Display Type | `6ab0c864e43d174ab37535f7` | 11 | — | `display_type` — **Product `1d0faacc-2a0f-490d-b339-d077c034bc62`** (default) · Section `95b10f68-72da-466f-80e5-1e43d694249e` · Subsection `83f20d55-b006-4ce3-865f-5d054ad9261d` · Note `a9150ecb-c7fa-4601-b84a-da01a31f1003` |
| Product | `6ab0c864e43d174ab37535f8` | 29 | — | `product_id` → Product Variants |
| Description | `6ab0c864e43d174ab37535fa` | 2 | — | `name` |
| Quantity | `6ab0c864e43d174ab37535fb` | 6 | — | `product_uom_qty` |
| **Quantity Invoiced** | `6ab0c864e43d174ab37535fc` | **6** | `101` | `qty_invoiced` — a plain Number |
| Quantity Delivered | `6ab0c864e43d174ab37535fd` | 6 | `101` | `qty_delivered` |
| Unit | `6ab0c984e43d174ab3753634` | 29 | — | `product_uom_id` |
| Unit Price | `6ab0ca1be43d174ab3753657` | 8 | — | `price_unit` |
| Discount | `6ab0ca1be43d174ab3753658` | 6 | — | `discount` |
| Taxes | `6ab0c984e43d174ab3753636` | 29 | — | `tax_ids`, multiple |
| Tax Amount | `6ab0cad0805aef703286d83d` | **31** | `101` | `price_tax` |
| Subtotal | `6ab0ca80805aef703286d82a` | **31** | `101` | `price_subtotal` |
| Total | `6ab0cad0805aef703286d83e` | **31** | `101` | `price_total` |
| Tax rate | `6ab0d4bbe43d174ab3753780` | 37 | `001` | `tax_rate` |
| Lead Time / Optional Line | `…3781` / `…3782` | 6 / 36 | — | |

One view (All). One rule, *A section or a note carries no figures* `6ab0d4e0e43d174ab375378c`, which **hides
Quantity Invoiced** among twelve others. No buttons. No workflows of its own.
Subtable columns on Orders: Sequence · Display Type · Product · Description · Quantity · Quantity Delivered ·
Quantity Invoiced · Unit · Unit Price · Taxes · Discount · Tax Amount · Subtotal · Total.

### 3.3 Invoices — `6aa90facf363582dd37a62f7`, 36 controls

Type `6aa9f847e54d2a34fa4dfeee` (**Customer Invoice `af9b889e-8e84-41ba-ac42-39a1b7a26039`**, Customer Credit
Note `eab71e3d-2d43-4cd3-af65-28c3f35ebd8c`) · Status `6aa9f847e54d2a34fa4dfeef` (Draft
`0979d4bb-c722-4fa4-9591-1bfb0fb04d05`, Posted `4524c691-8ce2-46bf-8a27-c2a857379a81`, **Cancelled
`4aebbafe-909e-468e-b5ff-9cbdee232765`**) · Number `6aa9f847e54d2a34fa4dfeed` (written by **Confirm**, not on
create) · Customer / Vendor `6aa920d74a73a3142152e689` · Invoice Date `6aa920d74a73a3142152e68b` · Delivery
Address `6aa9f848805aef703286517a` · Accounting Date `6aa9f847e54d2a34fa4dfef0` · Due Date
`6aa920d74a73a3142152e68c` · Payment Terms `6aab8b6b7d58b0f449311740` · Journal `6aa9f848805aef703286517c` ·
Tax mode `6aa9f847e54d2a34fa4dfef1` · **Lines** (subtable) `6aaa2baae43d174ab3749de9` · Terms and Conditions
`6aa9f847e54d2a34fa4dfef2` · Untaxed Amount `…fef3` / Tax `…fef4` / Total `…fef5` / Amount Due `…fef6`, all
**plain Numbers (type 6)** written by 07's roll-up workflows · Customer Reference `6aa920d74a73a3142152e692` ·
Salesperson `6aa920d74a73a3142152e693` · Delivery Date `6aa920d74a73a3142152e696` · **Source Document
`6aa9f847e54d2a34fa4dfef7`** (`invoice_origin`, text, `101`) · Incoterm `6ab29feae54d2a34faaa991a` · Incoterm
Location `6ab29feae54d2a34faaa991c`.

Buttons Confirm · Cancel · Reset to Draft. 11 rules. **No Orders relation, no Sales Orders smart button.**

### 3.4 Invoice Lines — `6aaa2b50e54d2a34fa4e0221`, 17 controls

Invoice `6aaa2baae43d174ab3749dea` (`move_id`, required) · Sequence `6aaa2b81e54d2a34fa4e022b` · Display Type
`6aaa2b81e54d2a34fa4e022c` (**Product `7f1d6a5c-3c4e-4b8a-9d21-6b0f2a5e7c31`** · Section
`2a90c7e4-1f63-4de5-8a07-4c3b91d0e6f2` · Subsection `b4e3f0a1-59d8-42c6-9f15-7e2d8c4a3b60` · Note
`d8c25b37-6e14-4a09-bf83-1d59e7c204af`) · Product `6aaa2b81e54d2a34fa4e022d` · Label
`6aaa2b50e54d2a34fa4e0222` · Account `6aab42fdbd43f55762c71ed6` · Quantity `6aaa2b81e54d2a34fa4e022f` · Unit
`6aaa2b81e54d2a34fa4e0230` · Unit Price `6aaa2b81e54d2a34fa4e0232` · Discount (%) `6aaa2b81e54d2a34fa4e0233` ·
Taxes `6aad1419bd43f55762c758ab` · Subtotal `6aaa2c18e43d174ab3749df1` (31) · Total `6aad1437bd43f55762c758b0`
(31) · Number `6aaa2c18e43d174ab3749df2` (30) · Accounting Date `6aaa2c18e43d174ab3749df3` (30) · **Status
`6aaa2c18e43d174ab3749df4`** (30, lookup of the invoice's Status) · Tax rate `6aad1428e43d174ab374fb98` (37).

**There is no lookup of the invoice's Type** — needed in §6.

Two workflows fill a new line: *Invoice Lines: fill the account of a new line* `6aab44254f2a99acac0f026f`
(trigger **create**, *"When a product line is created with no Account"*) and *…when the Product changes*
`6aab447416473257ad590b41`. Both write **Account and Taxes** — the step *Take the product's Income Account*
(`6aab44334f2a99acac0f0456`) carries a second field entry for `6aad1419bd43f55762c758ab` from the product's
Customer Taxes. **This is a trap for Create Invoice** (§5.6).

### 3.5 What the app has that Odoo's mechanism needs and Odoo's own data does not supply

- **No Invoicing Policy on Products.** `6aa8ea0c4a22ad87b728cf0b` has no `invoice_policy` control. So every
  line must be treated as Odoo's default *Ordered quantities*, and `qty_to_invoice` is
  `Quantity − Quantity Invoiced` always.
- **No `is_downpayment` anywhere**, on either lines worksheet.
- **No `state` on Order Lines** — Odoo's line status leans on it; here it needs a lookup of Orders → Status.
- **An Activities worksheet exists** (`6ab0cfb1805aef703286d929`, CRM group), so Odoo's upsell to-do is
  reachable later if the owner wants it.

---

## 4 · Spec 1 · The relations

### 4.1 The line-level many-to-many — the one that must exist

| Worksheet | Control | Alias | HAP type | Cardinality | Direction |
|---|---|---|---|---|---|
| **Order Lines** | **Invoice Lines** | `invoice_lines` | **29** (Relation) → Invoice Lines `6aaa2b50e54d2a34fa4e0221` | **multiple** (`enumDefault` 2) | **two-way** |
| **Invoice Lines** | **Sales Order Lines** | `sale_line_ids` | **29** → Order Lines `6ab0c740e43d174ab37535b2` | **multiple** (`enumDefault` 2) | the reverse of the above |

This is the faithful shape: Odoo's relation is a many-to-many, and HAP's 关联记录 lets each side be 单条 or
多条 independently, so **多 ↔ 多** is expressible. Both targets are ordinary worksheets — the fact that each is
*also* mounted as a 子表 changes nothing about a Relation between them.

**What HAP cannot express, and the consequences.**

1. **A 汇总 cannot cross two hops.** Odoo's `sale.order.invoice_ids` is `order_line.invoice_lines.move_id`;
   HAP has no aggregate over a relation of a relation. So the order's own invoice list must be a
   **denormalisation** (§4.2), and `invoice_count` must count that, not the lines.
2. **Odoo's link is written inside `create`; HAP's is written by a workflow *after* the row exists.** There is
   a window — seconds — in which an invoice line exists with no order line attached. Nothing in Odoo has that
   window. It matters only for a reader who looks during a run, and for a retry that dies between the two
   writes (§11).
3. **Cardinality caveat, unproven.** Nothing in this app yet pairs two **multiple** Relations. The handshake is
   known (BUILDING.md: `add-fields` on the target reserves the reverse id in `sourceControlId`, and the
   reverse must be saved on the other worksheet by hand carrying that id, `sourceControlType` 6 and
   `enumDefault` 2). What is unproven is a 多↔多 pair specifically. **If HAP refuses**, the fallback is:
   **Invoice Lines → Sales Order Lines as a *single* Relation (`enumDefault` 1), Order Lines → Invoice Lines
   as *multiple*.** That is a one-to-many, and it loses exactly one Odoo case: an invoice line that bills two
   order lines at once. Nothing in this app produces one — Create Invoice writes one invoice line per order
   line (`_prepare_invoice_lines_vals_list` returns a single dict, `sale_order_line.py:1510-1511`) — so the
   fallback is safe, and it is what should be built **first** if the 多↔多 pair does not take on the first
   try. Record which one was built; every 汇총 below works either way.

### 4.2 The header-level relation — a convenience, and say so

| Worksheet | Control | Alias | HAP type | Cardinality | Direction |
|---|---|---|---|---|---|
| **Orders** | **Invoices** | `invoice_ids` | 29 → Invoices `6aa90facf363582dd37a62f7` | multiple | **two-way** |
| **Invoices** | **Sales Orders** | *(none — see below)* | 29 → Orders | multiple | the reverse |
| **Orders** | **Invoice Count** | `invoice_count` | **37** (汇총), count over `$<Invoices relation>$` | — | — |
| **Invoices** | **Sales Order Count** | `sale_order_count` | **37**, count over the reverse | — | — |

The reverse on Invoices gets **no alias**: `account.move` has no stored field for it — `sale_order_count` is a
compute over `line_ids.sale_line_ids.order_id` (`sale/models/account_move.py:46-49`) and
`action_view_source_sale_orders` walks the same path (`:158-172`). Aliasing the 汇총 `sale_order_count` is
correct; aliasing the relation would invent an Odoo field. Note it in the divergences.

**It is written by the Create Invoice workflow, not derived.** So it can drift from the line-level truth when
someone deletes lines by hand. A **repair step** (§10, step 9) that rebuilds it from the lines is part of the
bundle, not an afterthought.

Placement: every new control lands at **row 9999** (`add-fields`), and **placement is the owner's**. Record the
intent in `*_PLACE` constants:

| Control | Intended place |
|---|---|
| Orders' Invoices, Invoice Count | *Other Info › Invoicing*, after Journal (divider `6ab0c459805aef703286d784`) |
| Orders' Invoice Status | already placed, row 4 — leave it |
| Order Lines' Invoice Lines | **not a subtable column** — hidden (`011`); it is a link, not a figure a person reads in the grid |
| Order Lines' Quantity To Invoice | the subtable grid, right after Quantity Invoiced |
| Invoice Lines' Sales Order Lines, Document Type | hidden (`011`); neither belongs in the invoice's line grid |
| Invoices' Sales Orders, Sales Order Count | *Other Info › Invoice* |

---

## 5 · Spec 2 · Create Invoice

### 5.1 The button

| | |
|---|---|
| Worksheet | Orders |
| Name | **Create Invoice** |
| `clickType` | 1 (a workflow button), **batch on** — Odoo offers it over a list selection (`sale_order_views.xml:121-124`) |
| Condition | Status **is** Sales Order `df9b6145-…` (`filterType` 51) **and** Invoice Status **is** To Invoice `a9150ecb-…` (51) **and** Invoicing Closed **is not** ticked |
| `confirmMsg` | none — Odoo's own button opens a wizard, and HAP's confirmation is the nearest thing to it. But see §5.7 |
| `desc`/`hint` | user-facing only, e.g. *"Makes a draft invoice for everything on this order that has not been invoiced yet."* No Odoo, no field names |
| ids.json | `buttons["Orders: Create Invoice"]`, `workflows["Orders: Create Invoice"]` |

Odoo's *second* Create Invoice button — `invoice_status == 'no' and state == 'sale'`, defaulting to a
percentage down payment (`sale_order_views.xml:280-287`) — is **not built in this bundle**; it belongs with down
payments (§7).

### 5.2 The workflow, node by node

The shape to copy is **Orders' Apply Discount** (`orders.py:3406` `apply_nodes`) — it already does the two hard
things: a `get_multiple` over the order's lines, and a `sub_process` in `sequential_each` mode that creates a
record per row.

```
trigger  (button, the order)
 1  Get the order as it now stands        get_single  → Orders, rowid = trigger        [re-read; the button's
                                                                                        condition is stale]
 2  How many lines are there to invoice?  rollup 107  count of Order Lines where
                                            Orders = the order
                                            AND Display Type is Product
                                            AND Quantity To Invoice > 0
 3  Is there anything to invoice?         branch
    ├─ No   (count < 1)  →  notice "Nothing to invoice"           (see §5.7)
    └─ Yes  (count ≥ 1)
        4  Make the invoice               create_record → Invoices, the header fields of §5.3
        5  Find the invoice just made     get_single  → Invoices, Source Document = the order's Number
                                            AND Status is Draft, sorted by ctime descending
        6  The lines to invoice           get_multiple → Order Lines, the §5.4 filter, sorted Sequence asc
        7  One invoice line per order line   sub_process, sequential_each, over node 6
             parameter  invoice = $node5-rowid$        (a text parameter)
             inner:
               7a  Get the invoice       get_single → Invoices, rowid = the invoice parameter
               7b  Make the line         create_record → Invoice Lines, the §5.5 fields
               7c  Attach it to the order line
                                          update_record → Order Lines (sub_trigger),
                                          Invoice Lines += the record 7b made      (addType append)
        8  Attach the invoice to the order   update_record → Orders (node 1),
                                              Invoices += node 5                   (addType append)
```

**Why node 5 exists at all.** An inner flow can reach the outer flow **only through parameters**, and a
sub-process parameter is **text** (`workflow_node_dsl._save_sub_process`: every `processVariables` entry is
`"type": 2`). So the invoice's row id travels down as text, and the inner flow turns it back into a record with
a `get_single` on `rowid` — exactly the trick Apply Discount uses for the discount product
(`orders.py` `variant()`, a `get_single` filtered `rowid eq <a literal id>`). Whether a `create_record`
node's own output can be bound by a later node directly is **not proven** in this repo; if it can, node 5
disappears and node 7a with it. Try it, and keep node 5 as the fallback.

**Why node 1 exists.** A button's condition is evaluated on the row the browser last rendered. Re-reading the
order inside the run is what makes a double press safe (§5.7).

**Node 2's filter** uses the view/rollup operator enum, not the rule enum: *Display Type is Product* is
`filterType` **51** with the Product key; *Quantity To Invoice > 0* is **13** (`FILTER_OP_TO_TYPE` in
`hap_cli.core.app_creator.fields`). A 107 node's filter conditions have their `nodeId` rewritten by the server;
what binds the count to this order is the **comparison value's** `nodeId` (BUILDING.md).

### 5.3 The header — what node 4 writes

| Invoice control | Value | Odoo |
|---|---|---|
| Type `6aa9f847e54d2a34fa4dfeee` | literal **Customer Invoice** `af9b889e-…` | `'move_type': 'out_invoice'` |
| Status `6aa9f847e54d2a34fa4dfeef` | literal **Draft** `0979d4bb-…` | a new move is draft |
| Customer / Vendor `6aa920d74a73a3142152e689` | the order's **Invoice Address**, and the order's **Customer** when it is empty | `partner_invoice_id`, which is itself a compute falling back to `partner_id` |
| Delivery Address `6aa9f848805aef703286517a` | the order's Delivery Address | `partner_shipping_id` |
| Source Document `6aa9f847e54d2a34fa4dfef7` | the order's **Number** | `invoice_origin` |
| Customer Reference `6aa920d74a73a3142152e692` | the order's Customer Reference, else its Number | `'ref': client_order_ref or name` |
| Payment Terms `6aab8b6b7d58b0f449311740` | the order's Payment Terms | `invoice_payment_term_id` — **but see §5.6** |
| Journal `6aa9f848805aef703286517c` | the order's Journal, **only when it is set** | `sale_order.py:1449-1450` |
| Salesperson `6aa920d74a73a3142152e693` | the order's Salesperson | `invoice_user_id` |
| Terms and Conditions `6aa9f847e54d2a34fa4dfef2` | the order's Terms and conditions | `'narration': self.note` |
| Tax mode `6aa9f847e54d2a34fa4dfef1` | the order's Tax Mode | **not in `_prepare_invoice`** — a divergence taken on purpose so the two documents' amounts agree (§12) |
| Incoterm `6ab29feae54d2a34faaa991a` | the order's Incoterm | `sale_stock/models/sale_order.py:300` |
| Incoterm Location `6ab29feae54d2a34faaa991c` | the order's Incoterm Location | `sale_stock/models/account_move.py:129-137`, a compute over the orders behind the lines; one order here, so a copy is the same answer |
| Delivery Date `6aa920d74a73a3142152e696` | the order's Delivery Date | `sale_stock` uses `effective_date` (when it *actually* shipped), which needs Inventory — divergence (§12) |
| Invoice Date, Accounting Date, Due Date, Number | **left empty** | Odoo leaves them; 06's Confirm fills Invoice Date and the Number, and the Due Date automation fills the due date |

### 5.4 Which order lines node 6 takes

`get_multiple` on Order Lines, sorted **Sequence ascending**, filtered:

- **Orders** equals the order (conditionId **33**, `conditionValues: [{nodeId: <node 1>, controlId: "rowid"}]`);
- **and** one of:
  - Display Type **is** Product `1d0faacc-…` **and** Quantity To Invoice **> 0**, or
  - Display Type **is any of** Section, Subsection, Note.

Written as two OR-ed AND-groups (BUILDING.md: `operateCondition` is a list of AND-groups; a get-multiple's
filter goes in with `node save --type 13`, since `--nodes` sends `operateCondition` where the UI wants
`filters`).

**Zero-quantity lines** are excluded by `> 0`, which is Odoo's `float_is_zero(qty_to_invoice)` skip
(`sale_order.py:1512`). **Negative** Quantity To Invoice — Odoo takes it only when `final`
(`sale_order.py:1513`), which is the deduct-down-payments pass — is therefore excluded, correctly, until down
payments exist.

**Sections and notes: a deliberate, recorded divergence.** Odoo buffers a section and emits it only when a real
invoiceable line follows (`sale_order.py:1504-1543`); a per-row loop cannot look ahead. **Build the cheap
version: carry every Section, Subsection and Note of an order that produces an invoice at all.** The visible
difference is an empty section heading on a partial invoice. The faithful version is a second pass that deletes
invoice-line sections with no product line between them and the next section — expensive, and worth doing only
if the owner asks. Note that node 3's guard already reproduces Odoo's *"all display types → no invoice"* rule
(`sale_order.py:1580`), because node 2 counts **product** lines only.

### 5.5 What node 7b writes on the invoice line

| Invoice Lines control | From the order line | Odoo (`sale_order_line.py:1513-1558`) |
|---|---|---|
| Invoice `6aaa2baae43d174ab3749dea` | node 7a's record | `move_id` |
| Sequence `6aaa2b81e54d2a34fa4e022b` | Sequence | `'sequence': self.sequence` |
| Display Type `6aaa2b81e54d2a34fa4e022c` | mapped key-for-key, Product → Product etc. — **the two controls' option keys differ**, so the map is explicit | `display_type or 'product'` |
| Product `6aaa2b81e54d2a34fa4e022d` | Product | `product_id` |
| Label `6aaa2b50e54d2a34fa4e0222` | Description | `_get_journal_items_full_name(self.name, product.display_name)` — see §12 |
| Quantity `6aaa2b81e54d2a34fa4e022f` | **Quantity To Invoice** | `'quantity': self.qty_to_invoice` |
| Unit `6aaa2b81e54d2a34fa4e0230` | Unit | `product_uom_id` |
| Unit Price `6aaa2b81e54d2a34fa4e0232` | Unit Price | `price_unit` |
| Discount (%) `6aaa2b81e54d2a34fa4e0233` | Discount | `discount` |
| Taxes `6aad1419bd43f55762c758ab` | **Taxes** | `Command.set(self.tax_ids.ids)` — **§5.6** |
| Account `6aab42fdbd43f55762c71ed6` | **not written** — 07's automation supplies it | Odoo derives it too |
| Sales Order Lines | the order line (`sub_trigger`) | `Command.link(self.id)` |

On a Section, Subsection or Note row: write Display Type, Sequence and Label only. Odoo forces
`account_id = False` there (`sale_order_line.py:1556-1557`) and 07's rule already hides the figures.

### 5.6 The two automations that will fight this, and what to do

**a. Invoice Lines' account automation overwrites the Taxes.** *Invoice Lines: fill the account of a new line*
(`6aab44254f2a99acac0f026f`) triggers on **create** and its step *Take the product's Income Account*
(`6aab44334f2a99acac0f0456`) writes **Account and Taxes** from the **product**. Odoo copies the taxes from the
**order line** (`sale_order_line.py:1543`). So a line created by Create Invoice would have its taxes silently
re-derived — a real divergence the moment a salesperson has hand-changed a tax on the order.

Three ways out, in order of preference:

1. **Split the automation's write**: Account under *Account is empty*, Taxes under *Taxes is empty*. Two
   narrow conditions, both faithful to Odoo (which derives both only when the user picks a product). This is
   an edit to a built, reviewed workflow — get the owner's nod, back it up, and change nothing else.
2. Give the Create Invoice workflow `triggerType` **1** (只能触发指定工作流) naming **only** 07's two roll-ups
   (`6aaa2d6aa1c923a16efc81a7`, `6aaa2ebba1c923a16efc8ecf`) — the account automation then never runs for these
   lines, and the line keeps the order's taxes and gets **no Account**. Worse: the invoice's lines then carry
   no account.
3. Accept the overwrite and record it. Only if 1 and 2 are both refused.

**b. Invoices' Payment Terms automation overwrites the Payment Terms.** *Invoices: Payment Terms follow the
Customer / Vendor* (`6aab8f1016473257ad5c91e0`) triggers on **create or Customer change** and its
*Take the customer's Customer Payment Terms* step is not gated on the field being empty (the structure shows no
such branch). Odoo copies the **order's** `payment_term_id`, which may differ from the customer's default. Same
three options; option 1 — gate that step on *Payment Terms is empty* — is the right one, and it is also what
Odoo's own `_compute_invoice_payment_term_id` does.

**c. `triggerType` must not be 2.** 06's amounts are written by 07's roll-up workflows, which are worksheet-event
workflows on Invoice Lines. A Create Invoice run set to 不允许触发 would leave every new invoice reading 0.00.
Whatever is decided above, **07's two roll-ups must stay reachable**, and the Invoice Status workflow of §6.4
must be reachable from Order Lines' writes.

### 5.7 Pressed twice, and pressed over a selection

**Twice.** Odoo hides the button once `invoice_status != 'to invoice'`, and the wizard warns when a draft
invoice already exists (`sale_make_invoice_advance.py:91-94`). Here, Invoice Status is written by a workflow
seconds after the first run, so the button stays pressable in that window. **The guard is node 2**: it counts,
inside the run, lines with Quantity To Invoice > 0 — and Quantity To Invoice falls the moment the first run's
invoice lines exist and carry the relation. A second press inside the window therefore counts 0 and takes the
*No* path.

That path must be a **notice (flowNodeType 27), not an abort.** An abort draws HAP's own toast, a warning icon
and the untranslated 中止 (BUILDING.md); a run that simply ends draws nothing. The notice's **name is what the
user reads**, as a heading, so name it *Nothing to invoice* with Odoo's own reason in the body — a plain-words
version of `_nothing_to_invoice_error_message` (`sale_order.py:1486-1499`), and nothing about Odoo or field
names. Hang the notice off the *No* path and let the gateway converge on nothing (BUILDING.md: a step inside a
path is better than an abort).

There is still a **narrower** race: two presses within the seconds before the first run's `update_record` node
7c lands. Both runs would count the same lines and make two invoices. Nothing HAP offers closes it — there is
no locking, and a workflow's own write is not checked against *No duplicates* (BUILDING.md). **Record it as a
known limitation** rather than building around it, exactly as 06's numbering race was recorded.

**Over a selection.** A HAP batch button runs the workflow **once per selected record**, so several orders give
**one invoice per order**. Odoo's default merges orders sharing customer, delivery address, currency and fiscal
position into one invoice (`consolidated_billing` default True → `grouped=False` →
`_get_invoice_grouping_keys`). **This is a divergence that cannot be closed** without a second, order-less
workflow that groups first — out of scope, and arguably better behaviour for a first version, since a merged
invoice is the thing users most often undo. Record it, and say so in the button's own description in plain
words: *"Makes one invoice for each order you selected."*

---

## 6 · Spec 3 · The computed fields

**Which mechanism, and why.** Three rules decide it, all from CLAUDE.md and BUILDING.md:

- a figure derived from related records is a **汇총 (37)** — computed server-side, follows the relation, takes
  its own filter;
- anything **reading** a 汇총 must be a **Formula** — type **31** for arithmetic, type **53** when it needs
  `IF`. A function default cannot: it is evaluated in the browser and a 汇총 has no value while the form is
  open (`16-orders.md` §7.3, the rule that cost a day);
- a **Dropdown cannot be computed at all**, so Invoice Status must be a **workflow write** — the same answer
  06's four amounts took.

### 6.1 On Order Lines

| # | Control | Alias | Type | Definition |
|---|---|---|---|---|
| 1 | **Qty on invoices** *(hidden)* | — | **37** | sum of Invoice Lines' **Quantity** over `$<Invoice Lines relation>$`, filtered **Status is not Cancelled** (`filterType` **52**, value `4aebbafe-909e-468e-b5ff-9cbdee232765`) **and Document Type is Customer Invoice** (51, `af9b889e-…`) |
| 2 | **Qty on credit notes** *(hidden)* | — | **37** | the same, Document Type **is Customer Credit Note** (51, `eab71e3d-…`) |
| 3 | **Quantity Invoiced** `6ab0c864e43d174ab37535fc` | `qty_invoiced` | **6 → 31** | `$1$ − $2$`, `nullzero "1"`, `dot` 2 |
| 4 | **Order Status** *(hidden)* | `state` | **30** (lookup) | of Orders → Status. A type-30 lookup of a single select stores the **source** control's option key, and the editors read it as type **11** (BUILDING.md) |
| 5 | **Quantity To Invoice** | `qty_to_invoice` | **53** | `IF($4$ == "Sales Order" && $DisplayType$ == "Product", $Quantity$ − $3$, 0)`, `enumDefault2` **6** (number), `dot` 2 |
| 6 | **Line Invoice Status** *(hidden)* | `invoice_status` | **53** | a **number** 0–3: `3` upselling, `1` to invoice, `2` invoiced, `0` nothing — the order of Odoo's own tests, §6.3 |
| 7 | **Untaxed Invoiced** *(hidden)* | `untaxed_amount_invoiced` | **37** | sum of Invoice Lines' **Subtotal**, filtered **Status is Posted** (51, `4524c691-…`) and Document Type is Customer Invoice; minus a twin filtered to credit notes, through a type-31 Formula. **Posted only** — Odoo ignores drafts here on purpose (`sale_order_line.py:1128`) |
| 8 | **Untaxed To Invoice** *(hidden)* | `untaxed_amount_to_invoice` | **31** | `$Subtotal$ − $7$`, `nullzero "1"` |

Item 3 is a **type change in place, 6 → 31, keeping the control id**. That is a move this worksheet has already
made: Tax Amount `6ab0cad0805aef703286d83d` and Total `6ab0cad0805aef703286d83e` were converted from
value controls to Formulas on 21 Sep 2026 and kept their ids (`16-orders.md` §7.3, and both read type 31 live
today). It still needs the owner's approval — it discards whatever is typed in Quantity Invoiced on the 37
existing lines — and a version-pinned save on the `products.py:297` `step_perms` pattern.

**`Document Type` must be added to Invoice Lines first**: a **type 30 lookup** of Invoice → Type, alias
`move_type`, hidden (`011`), not a subtable column. Every one of the 39 existing lines computes it the moment
it is saved (BUILDING.md: a lookup added to a live worksheet computes on every record at once).

### 6.2 On Orders

| # | Control | Alias | Type | Definition |
|---|---|---|---|---|
| 9 | **Invoice Count** | `invoice_count` | 37 | count over the Invoices relation |
| 10 | **Lines to invoice** *(hidden)* | — | 37 | **count** over the Order Lines subtable, filtered Display Type is Product **and Line Invoice Status = 1** |
| 11 | **Lines not to invoice** *(hidden)* | — | 37 | the same, **Line Invoice Status = 0** |
| 12 | **Lines invoiced** *(hidden)* | — | 37 | the same, **= 2** |
| 13 | **Lines upselling** *(hidden)* | — | 37 | the same, **= 3** |
| 14 | **Product lines** *(hidden)* | — | 37 | the same, no status filter |
| 15 | **Already invoiced** | `amount_invoiced` | 37 | sum of the lines' Untaxed Invoiced (item 7). Odoo's `amount_invoiced` is tax-**inclusive** (`price_total`); this is the untaxed figure and must be labelled as such, or built from a tax-inclusive twin of item 7 |
| 16 | **Un-invoiced Balance** | `amount_to_invoice` | 37 | sum of the lines' Untaxed To Invoice (item 8) |
| 17 | **Invoice Status** `6ab0c5eae54d2a34fa4e8131` | *(give it `invoice_status`)* | 11 | **written by a workflow**, §6.4 |

Items 10–14 are **filtered counts over a 子表 of a function formula's numeric result**. Each piece is proven
separately — a 汇총 over a mounted 子表 with its own filter (Payment Terms' *Percent total*), and the
filter editors reading a type 53 as its result type (BUILDING.md) — but **the combination is not**. Prove it on
one order before building four more. If it fails, the fallback is a **type 31 Formula on the line** per state
(`Is to invoice` = 1/0, and so on) with the 汇총 summing it — four extra hidden line controls, no conditionals,
and nothing unproven. Budget for the fallback.

### 6.3 The line's status, exactly

Odoo's tests in order (`sale_order_line.py:1078-1104`), with what each becomes here. `P` is the product-line
test (Display Type is Product), `S` the order test (Order Status is Sales Order):

| Odoo | Here | Note |
|---|---|---|
| `state != 'sale'` → **no** | `!S` → **0** | |
| `is_downpayment and untaxed_amount_to_invoice == 0` → **invoiced** | *skipped* | no down payments in this bundle |
| `qty_to_invoice != 0` → **to invoice** | `Quantity To Invoice != 0` → **1** | |
| policy `order` **and** `product_uom_qty >= 0` **and** `qty_delivered > product_uom_qty` → **upselling** | `Quantity >= 0 && Quantity Delivered > Quantity` → **3** | the policy test is always true here: no Invoicing Policy on Products, so every line is *Ordered quantities* (§3.5) |
| `qty_invoiced >= product_uom_qty` → **invoiced** | `Quantity Invoiced >= Quantity` → **2** | |
| otherwise → **no** | **0** | |

Also skip a display-type line entirely — Odoo's `lines_domain` excludes them from the order's decision
(`sale_order.py:633`), and items 10–14 filter on Display Type is Product anyway.

### 6.4 The order's Invoice Status — a workflow, and which events start it

Odoo's compute depends on `state` and `order_line.invoice_status` (`sale_order.py:619`). Here that is three
events, and HAP's worksheet-event trigger takes **one** event each (BUILDING.md), so:

| Workflow | Trigger | Why |
|---|---|---|
| **Orders: Invoice Status** | Orders, 新增或更新 `'2'`, narrowed to **Status** and **Invoicing Closed** | confirming or cancelling an order changes it |
| **Orders: Invoice Status follows its lines** | Order Lines, 新增或更新 `'2'` | a line added, a quantity changed, an invoice line attached |
| **Orders: Invoice Status when a line is deleted** | Order Lines, 删除 `'3'` | 2 and 3 cannot share a trigger — the same body twice, exactly as 07's two roll-ups |

Body, after a `get_single` for the order (the trigger itself on the first; the line's Orders relation on the
other two — and note that a search step whose filter **value** is empty fails the whole run, so a line with no
Orders must be guarded, as 07's automation B had to be):

```
branch  Which status?
 ├─ Order Status is not Sales Order        → Nothing to Invoice   1d0faacc-2a0f-490d-b339-d077c034bc62
 ├─ Lines to invoice ≥ 1                   → To Invoice           a9150ecb-c7fa-4601-b84a-da01a31f1003
 ├─ Product lines ≥ 1 and Lines invoiced = Product lines
 │                                         → Fully Invoiced       0ac57562-a137-4765-8165-44fc7d72776c
 ├─ Product lines ≥ 1 and Lines invoiced + Lines upselling = Product lines
 │                                         → Upselling Opportunity 95b10f68-72da-466f-80e5-1e43d694249e
 └─ else                                   → Nothing to Invoice
```

The paths are exclusive and **ordered**, which is Odoo's own order. A dropdown is written as the **bare option
key** in `fieldValue` — a list makes `saveNode` answer HTTP 500 (BUILDING.md). *Lines invoiced + Lines
upselling* needs a number formula node (actionId 100, `number: 0`, `nullZero: true`) before the gateway,
because a branch path compares one value.

**Odoo's discount-only refinement is not built.** `_can_be_invoiced_alone` (`sale_order_line.py:1108-1114`)
keeps an order out of *to invoice* when the only invoiceable lines are the company's discount product. Orders'
Apply Discount does create a discount line (`orders.py` §14), so the case is reachable — but the test needs
"every invoiceable line is the discount product", which is a second filtered count against a specific product
variant. **Defer it, record it**, and revisit if a reviewer notices a discount-only order offering Create
Invoice.

**Invoicing Closed.** Odoo's `invoicing_closed` is not in `_compute_invoice_status` at all; it is read by the
*Close Invoicing* / *Reopen Invoicing* buttons (`16-orders.md` §3, buttons 12 and 20, both unbuilt). Keep it out
of the status and put it in the **button's condition** only (§5.1) — which is where Odoo's own `invisible`
would put it if it used it.

---

## 7 · Spec 4 · Down payments

### 7.1 What a faithful version needs

| Piece | Where |
|---|---|
| **Down Payment / Down Payment Amount** inputs on Orders — two controls, like the Discount pair `6ab23575e54d2a34fa4f7b8b` / `…7b8c` | Odoo's wizard fields `amount` / `fixed_amount` (`sale_make_invoice_advance.py:34-39`) |
| **`is_downpayment`** on Order Lines and Invoice Lines | `sale_order_line.py:74`, `account_move_line.py:11` |
| **A Down Payments section** order line, added once | `sale_order.py:2055-2084` |
| **Splitting the amount across tax groups** — one down-payment order line per distinct tax combination, with `product_uom_qty = 0` and no product | `account.tax._prepare_down_payment_lines`, called at `sale_make_invoice_advance.py:159-165` |
| **A down-payment account** — a company setting, falling back to the product's or category's down-payment or income account | `_get_down_payment_account`, `:243-253`, and `res.company.downpayment_account_id` |
| **A Down Payments section** on the invoice, before the deposit lines | `sale_order.py:1586-1594`, `:2013-2034` |
| **The deduction**: the final invoice re-emits each deposit line at quantity **−1** with the tax data reversed | `sale_order.py:1600-1605` |
| **The description**, recomputed on post, cancel and reset to draft | `sale_order_line.py:484-512`, `sale/models/account_move.py:83-118` |
| **Deleting the invoice deletes its deposit order lines** | `sale/models/account_move.py:26-31` |
| **The status rule**: a deposit line with nothing left to invoice reads *Fully Invoiced*, and deposit lines are excluded from the order's status | `sale_order_line.py:1095-1096`, `sale_order.py:633` |

Nine of those eleven are new machinery. The tax-group split alone needs the taxes engine; `extra_tax_data` is
a JSON technical field with no HAP equivalent.

### 7.2 The cheaper version

A **Down Payment** button on Orders, percentage only, one order at a time:

1. two controls, *Down Payment %* and a read-only *Down Payments Invoiced* figure;
2. **`is_downpayment`** checkboxes on both lines worksheets, hidden;
3. one deposit **order** line per order — **no tax-group split**, the order's own Tax Mode and the taxes of the
   largest tax group, quantity 0, price = the percentage of the order's Untaxed Amount;
4. one draft invoice, one line, quantity 1, the account left to 07's automation;
5. and — **not optional** — Create Invoice's line filter widened to take deposit lines at quantity **−1**, so
   the final invoice deducts them.

### 7.3 The recommendation

**Do neither in this bundle. Build §4 to §6 and §9 first, prove them in the browser, and make down payments
bundle two.**

The reason is not effort, it is correctness. A down payment that is created and **not** deducted bills the
customer twice, and step 5 above — the deduction — is the one piece that cannot be simplified: it needs
`is_downpayment` on both worksheets, a negative-quantity line, and Create Invoice's filter to accept a negative
Quantity To Invoice. If the owner wants a deposit facility sooner than a full bundle, build **§7.2 in full,
including step 5** — and never ship steps 1–4 on their own.

Odoo's second *Create Invoice* button (`sale_order_views.xml:280-287`), which offers a percentage deposit when
there is nothing to invoice yet, belongs with that bundle too.

---

## 8 · Spec 5 · What the To Invoice and To Upsell filters become

**What is there today**, read live: the **Orders** view `6ab0df017d58b0f449316f4e` carries **one quick filter,
on Invoice Status** (`fastFilters: [{controlId: 6ab0c5eae54d2a34fa4e8131}]`), and Invoice Status is its last
column. There is no *To Invoice* view and no *To Upsell* view. Odoo has both a pair of **search filters**
(`sale_order_views.xml:994-995`) and a pair of **dedicated actions** with the same domains (`:1172`, `:1188`),
which is how its Sales overview reaches them.

| Odoo | Becomes | Why |
|---|---|---|
| the quick filter behaviour | **the existing Invoice Status quick filter, unchanged** — it starts working the day §6.4 writes the field, and it already offers all four values, which is more than Odoo's two named filters | nothing to build; say so rather than build a third thing |
| `sale.action_orders_upselling` (`:1188`) | a new view **To Upsell** — Status is Sales Order, Is Template not ticked, **Invoice Status is Upselling Opportunity**; the Orders view's columns and sort | Odoo surfaces it as a place you go, not only a filter |
| `sale.action_orders_to_invoice` (`:1172`) | a new view **To Invoice** — the same with **Invoice Status is To Invoice** | |

Both filters are `filterType` **51** on a single select (BUILDING.md: 51, not 2, and 51 with several keys means
*is any of*). Both views take the Orders view's `showControls` plus
`advancedSetting.customShowControls`, and the same `sort_by` — and **add Invoice Count** to their columns, since
the point of the lists is to see what has been billed. Put them **after** Orders in `sort_views` so the default
view does not change.

**Do not add Invoice Status to the Quotations view.** It means nothing on an unconfirmed order — Odoo's compute
returns `no` for every order that is not `state == 'sale'` (`sale_order.py:628-629`).

**Also worth its own line**: Order Lines has **one view, All**. Odoo has a standalone *Sales Order Lines* list
with `qty_invoiced` and `qty_to_invoice` as columns and an `[('qty_to_invoice','!=',0)]` domain
(`sale_order_line_views.xml:15-16`, `:95`). A **Lines to Invoice** view on Order Lines is a cheap, genuine
addition once §6.1 exists, and it is the fastest way for a reviewer to check the figures. Offer it; do not
assume it.

---

## 9 · Spec 6 · Carrying the Incoterm and the other header fields

Already specified field by field in §5.3. What is worth saying separately:

- **The Incoterm is `sale_stock`'s, not `sale`'s.** Base `sale._prepare_invoice` does not carry it;
  `sale_stock/models/sale_order.py:300` adds `invoice_vals['invoice_incoterm_id'] = self.incoterm.id`. Since
  ERP Master has Incoterm on both worksheets and no Inventory, copying it is the right call and the citation
  belongs in the build's docstring.
- **Incoterm Location is a compute on the invoice**, not a copy: the first non-empty `incoterm_location` among
  the orders behind the invoice's lines (`sale_stock/models/account_move.py:129-137`). With one order per
  invoice (§5.7) a copy gives the same answer. **If order grouping is ever built, this becomes wrong** — note
  it beside the grouping divergence.
- **Delivery Date is the divergence in this group.** Odoo's is the order's `effective_date` — when the goods
  actually left — which needs stock moves. Copying the order's promised Delivery Date is the nearest available
  value and is not the same field. State it in §12; do not describe it in the control's `desc`.
- **Tax mode is carried although Odoo does not carry it.** Odoo derives the invoice's tax mode from the fiscal
  position and the company; neither is modelled. Carrying the order's Tax Mode is what keeps the invoice's
  Untaxed Amount and Total equal to the order's, which is the first thing a reviewer compares.
- **Payment Reference, Fiscal Position, Sales Team and the UTM fields are not carried** because the app has no
  controls for them. Nothing to build; list them.
- **Source Document** `6aa9f847e54d2a34fa4dfef7` is `101` (read-only) and was kept read-only on purpose so the
  seeded `S00011` stayed visible (`06-invoices.md` §1). **A workflow update step writes a read-only field
  without trouble** — permission governs the form, not the API (CLAUDE.md) — so it needs no change. It is also
  the key node 5 finds the new invoice by, which makes it load-bearing: say so in the build.

---

## 10 · Spec 7 · Order of work

Each step is a `bo2i` step of its own, reads live state first, saves nothing when re-run, and reads back every
write. Nothing after step 1 can start before its predecessor is checked in the browser.

| # | Step | Builds | Check in the browser |
|---|---|---|---|
| **1** | `lookups` | Invoice Lines' **Document Type** (30, `move_type`, hidden) and Order Lines' **Order Status** (30, `state`, hidden) | Open an invoice line from the standalone Lines view: Document Type reads *Customer Invoice* on all 39. Open an order line: Order Status reads the order's status. Neither appears in either subtable grid |
| **2** | `relations` | the **Order Lines ↔ Invoice Lines** pair (§4.1), then the **Orders ↔ Invoices** pair (§4.2) and both count 汇총 | On an order line's row panel, link one existing invoice line by hand: the invoice line's *Sales Order Lines* shows it back. Invoice Count on an order reads 0, then 1 when an invoice is linked by hand. **If the 多↔多 pair does not take, stop and report before falling back to §4.1's one-to-many** |
| **3** | `qty` | Order Lines items 1, 2 and the 6 → **31** conversion of **Quantity Invoiced** (§6.1) | The hand-linked line from step 2 shows Quantity Invoiced equal to that invoice line's Quantity. Cancel the invoice → it falls to 0. Uncancel → it returns. Quantity Invoiced is still a subtable column and still read-only, and the section rule still hides it |
| **4** | `toinvoice` | **Quantity To Invoice** (53) and **Line Invoice Status** (53), and the five counts on Orders (§6.2 items 10–14) | On a confirmed order: a line with Quantity 10 and nothing invoiced reads 10 to invoice; a section reads 0. Set Quantity Delivered above Quantity → Line Invoice Status 3. **Read the five counts on the order form — this is the unproven combination of §6.2.** On an unconfirmed order every line reads 0 |
| **5** | `status` | the **three Invoice Status workflows** (§6.4), and Invoice Status' alias | Confirm a TEST order with two lines → *To Invoice*. Set it back to Quotation → *Nothing to Invoice*. Delete a line, add one. Check `hap approval history --process-id` for a run per event and no run for an unrelated write |
| **6** | `views` | **To Invoice** and **To Upsell** views, Invoice Count added to both, and — if the owner wants it — **Lines to Invoice** on Order Lines | The Orders view still opens first. The two new views hold the right orders and nothing else. The Invoice Status quick filter now returns rows for each value |
| **7** | `guards` | the two automation fixes of §5.6 — the account automation's Taxes gated on *Taxes is empty*, the Payment Terms automation's step gated on *Payment Terms is empty* | Create an invoice line by hand with a product and **no** taxes → Account and Taxes both fill. Create one **with** taxes → Account fills, the taxes stay. Create an invoice with a payment term typed → it survives |
| **8** | `create` | the **Create Invoice** button and its workflow (§5) | Press it on a TEST order with a section, two product lines and a note. One draft invoice appears, with every header field of §5.3, the section and the note, both product lines at the ordered quantity, the order's taxes, and an account on each. The order reads *Fully Invoiced*, Invoice Count 1, each line's Quantity Invoiced equal to its Quantity and Quantity To Invoice 0. **Press it again: no second invoice, and the notice appears in the notification list.** Change one line's Quantity up by 2 → *To Invoice*, press again → a second invoice with that one line at quantity 2 |
| **9** | `repair` | a step that rebuilds Orders' **Invoices** relation from its lines' Invoice Lines, and reports every order where the two disagreed | Run it twice: the second run reports nothing and saves nothing |
| **10** | `selfcheck` | the CLI drive of steps 5 and 8, on the `orders.py step_selfcheck` / `step_selfdiscount` pattern | not a browser step — but it is what lets the browser test be short |

Steps 1–4 touch controls on four worksheets the owner edits. **Every one is a version-pinned save on the
`products.py:297` `step_perms` pattern, proved by signature diff.** Step 3's type change needs the owner's
approval in writing before it runs.

A sensible split if the bundle is too big for one hand-off: **1–4 as *the figures*, 5–7 as *the status*, 8–10 as
*Create Invoice***. The figures alone already close `16-orders.md` §7.2 item 8, which is worth having on its own.

---

## 11 · Spec 8 · Risks

### 11.1 Clobbering the owner's hand edits

| Risk | Guard |
|---|---|
| Steps 1–4 all add or change controls on **Orders, Order Lines, Invoices and Invoice Lines** — the four worksheets the owner hand-edits, three times in one day on 22 Sep | Add with **`C.append_controls`**; change with `C.controls_with_version` → change only what you own → `C.save_controls(ws, ctrls, version=version)` → **prove by signature diff that only the intended controls moved**. Never an unpinned full save. `hap --json app logs <app> --start …` before each surgical save, to see who touched it |
| **Step 3 replaces a live control's type.** 6 → 31 on Quantity Invoiced discards whatever is typed in it on 37 order lines, and a Formula cannot be typed into afterwards | **The owner's explicit approval first.** Back the worksheet up with `hap.backup`. Read the 37 lines' current Quantity Invoiced into the backup file too, so the values can be quoted if anyone asks |
| **Step 7 edits two built, reviewed workflows** (07's account automation, 06's payment-terms automation) | `hap.backup` every node of both before the change; change one condition each; `hap workflow rollback <pid> -y` restores the last published version if the draft goes wrong. Compare every node with its backup afterwards, as the 17 Sep re-pointing pass did |
| **`add-fields` parks every new control at row 9999.** Nine new controls arriving there at once makes the four forms look broken until the owner places them | Do steps 1–4 in the order above, not all at once, and say in each report which controls are at 9999 and where they are meant to go (`*_PLACE` constants). Placement is the owner's |
| **Adding a control to a worksheet does not add it to the 子表 grid.** A row panel draws the *subtable's* `showControls`, so Quantity To Invoice is invisible from inside an order until the Orders subtable `6ab0c740e43d174ab37535b0` lists it | Step 4 must extend `showControls` **and** `advancedSetting.controlssorts` on that control, in the same pinned save |
| The **Sales app** `3e596740-d096-42cd-b948-0b62a0220927` | **Never written.** Nothing in this bundle has any reason to touch it |

### 11.2 Credits and quota

The organisation has **no credits** (`DECISIONS.md`, 22 Sep). Nothing in this bundle needs any: there is no
PDF, no email, no AI node. `SEND_PDF = False` in `orders.py` and the §11 fill-in-link decision are the
precedents, and Create Invoice is entirely record writes.

**Workflow runs are a separate quota**, and this bundle is the heaviest thing yet built on it:

- **Three Invoice Status workflows, two of them on Order Lines' every create, update and delete.** The
  worksheet holds 37 rows today and will grow with every invoice. `16-orders.md`'s own note applies: *give a
  worksheet-event trigger a condition when most records cannot need the run.* Narrow the two line-driven
  workflows to the fields that can change the answer — Orders, Display Type, Quantity, Quantity Delivered,
  Invoice Lines — remembering that a field-narrowed 新增或更新 fires **whenever one of those fields is in the
  write, changed or not** (BUILDING.md), so a script that re-sends every field re-runs them all.
- **A Create Invoice press starts one run plus one sub-process run per line, and each created invoice line
  starts 07's roll-up and the account automation.** A ten-line order is well over twenty runs. Say so in the
  hand-off; it is the owner's budget.
- **Step 3's type change recomputes every record at once** (BUILDING.md: changing a formula recomputes all
  records seconds later, no record write). Free, but it will look alarming in the app log.

### 11.3 What cannot be undone

| | |
|---|---|
| **The 6 → 31 conversion of Quantity Invoiced** | The typed values are gone. The control id survives, so nothing else breaks — but the numbers do not come back from HAP. The backup file is the only copy |
| **Invoices created by a test press** | 06 has **no Active field, no Archive** (`07-invoice-lines.md` §1). A test invoice cannot be archived, and deleting needs the owner's approval. So **every test press must be on a `TEST …` order**, and the invoices it makes must be named — Source Document carries the order's Number, so a `TEST …` order yields findable invoices. Expect to leave them in place and list them, as 06 and 07 already leave their TEST records |
| **A control deleted rather than retyped** | Never delete. The field recycle bin holds a deleted control for the site's retention window, and a re-created control has a **new id** that every view, rule, 汇총, workflow and subtable column naming the old one must be re-pointed to |
| **A half-finished Create Invoice run** | There is no transaction. A run that dies between node 4 and node 7c leaves an invoice with no lines, or lines with no relation, and Quantity Invoiced then under-reads. The **repair step (step 9)** must cover this case as well as the header relation — or the bundle must say plainly that it does not |
| **The double-press race inside the first seconds** | Cannot be closed (§5.7). Two invoices, both real, both deletable only with the owner's approval |

---

## 12 · Divergences from Odoo, all of them

| # | Odoo 19.0 | Here | Why |
|---|---|---|---|
| 1 | `sale.order.invoice_ids` is a **compute** over `order_line.invoice_lines.move_id` | a **stored, two-way Relation** written by Create Invoice, with a repair step | HAP has no aggregate across two relation hops (§4.1) |
| 2 | the m2m is written **inside** `create` | written by a workflow a moment after the row exists | HAP has no pre-create hook |
| 3 | `invoice_ids` picks up a credit note made **directly from the invoice** (`sale_order.py:572-575`) | a credit note reaches the figures only if something links its lines back to the order lines | 06 has no Credit Note button yet (`06-invoices.md` §1) — revisit with it |
| 4 | a section reaches the invoice **only when an invoiceable line follows it** | every Section, Subsection and Note is carried | a per-row loop cannot look ahead (§5.4) |
| 5 | several orders for one customer merge into **one** invoice by default | **one invoice per order** | a HAP batch button runs once per record (§5.7) |
| 6 | the invoice line's taxes are the **order line's** | the order line's — **only after step 7's fix**; before it, the product's | 07's account automation also writes Taxes (§5.6) |
| 7 | the invoice's payment term is the **order's** | the order's — **only after step 7's fix**; before it, the customer's | 06's payment-terms automation (§5.6) |
| 8 | `invoice_policy` per product decides ordered vs delivered quantities | every line is **Ordered quantities** | Products has no Invoicing Policy control (§3.5); `order` is Odoo's default |
| 9 | `Label` is `_get_journal_items_full_name(name, product.display_name)` | the order line's Description, copied | the helper builds a two-line string from the product and the line description; the order line's Description already holds Odoo's own line text |
| 10 | the invoice's `delivery_date` is the order's **`effective_date`** | the order's **Delivery Date** (promised) | no Inventory (§9) |
| 11 | the invoice's tax mode comes from the fiscal position and the company | the **order's Tax Mode**, copied | neither is modelled; copying is what keeps the two documents' totals equal (§9) |
| 12 | `incoterm_location` on the invoice is computed from every order behind its lines | copied from the one order | one order per invoice; **wrong the day grouping is built** (§9) |
| 13 | reaching *upselling* schedules a to-do on the salesperson (`sale_order.py:1981`) | nothing is scheduled | the Activities worksheet exists (`6ab0cfb1805aef703286d929`); a later step could |
| 14 | an order whose only invoiceable lines are the discount product is **not** *to invoice* (`_can_be_invoiced_alone`) | it is *to invoice* | a second filtered count against a product variant; deferred (§6.4) |
| 15 | `amount_invoiced` on the order is **tax-inclusive** (`price_total`) | *Already invoiced* is the **untaxed** figure | the tax-inclusive twin is a second pair of 汇총; add it if the owner wants Odoo's number |
| 16 | pressing Create Invoice twice is prevented by the field the button hides on | prevented by a **guard inside the run**, with a seconds-wide race | no locking in HAP (§5.7) |
| 17 | *Cannot create an invoice* is a modal `UserError` | an **in-app notification** in the workflow channel | the only thing a button workflow can put in front of a user (BUILDING.md) |
| 18 | the invoice's reverse relation is `account.move.sale_order_count`, a compute | a Relation with **no alias** plus a 汇총 aliased `sale_order_count` | `account.move` has no stored field for the set (§4.2) |
| 19 | down payments | **not built** | §7 |
| 20 | `qty_invoiced_posted`, `qty_invoiced_at_date`, `amount_to_invoice_at_date`, `extra_tax_data` | not built | accrual and tax-engine machinery with no HAP equivalent |

## 13 · What is unproven, and what to do about it

Ranked by how much of the bundle falls over if it is wrong.

| Unknown | Confidence | If it fails |
|---|---|---|
| A **多 ↔ 多** two-way Relation pair. The handshake is documented and proven for 1↔多; nothing in this app pairs two multiples | **medium** | §4.1's one-to-many fallback — Invoice Lines → Sales Order Lines single. Loses nothing this app produces. **Build the fallback rather than fight it** |
| A **filtered 汇총 over a 子表 whose filter compares a type-53 function formula's numeric result**. Each half is proven; the combination is not | **medium** | four extra type-31 Formula flags on Order Lines, one per state, with the 汇총 summing them (§6.2) |
| A **sub-process parameter carrying a row id as text**, turned back into a record by a `get_single` on `rowid`. The parameter mechanism is proven (Apply Discount passes a label and a divisor); the rowid round-trip is not | **medium-high** | if the create node's own record can be bound by a later node, nodes 5 and 7a both disappear and the problem is gone. Test that first |
| The **6 → 31 type change** keeping the control id. Tax Amount and Total on this very worksheet did it on 21 Sep | **high** | a new control, and re-point the section rule `6ab0d4e0e43d174ab375378c`, the subtable's `showControls`, and anything else naming `6ab0c864e43d174ab37535fc` |
| A **汇총 filter on a type-30 lookup of a single select** (Invoice Lines' Status, Document Type). Proven for rules and picker filters, which compare the **source** worksheet's option keys; not measured on a 汇총's `advancedSetting.filters` | **medium-high** | a hidden type-53 text formula on the line mirroring the lookup, and filter on that |
| **Whether an `update_record` with `addType` append on a multi-Relation adds without replacing.** Apply Discount uses `addType 2` on a **number**; a Relation append is the same key on a different type | **medium** | read the relation, then write the whole list — which is not safe under concurrency, so prefer proving the append |
| A `get_multiple` whose filter is **two OR-ed AND-groups** (§5.4). Branch paths take several OR-ed groups; a get-multiple's `filters` shape is documented but not with an OR | **medium** | two get-multiple nodes and two sub-processes, one for product lines and one for display-type lines — which also makes the section behaviour easier to change later |
| Whether 07's account automation, given a line that already carries Taxes, leaves them alone once its write is split | **high** — it is an ordinary branch condition | |

**The three things to prove before writing a line of the build**, each on one TEST record, each reversible:
the 多↔多 pair, the filtered 汇총 over a type-53 result, and the create-node binding. They decide the shape of
§4, §6 and §5 respectively, and all three are cheap to test.

---

## 14 · Build results — 23 Sep 2026

Built by `nocoly/build/o2i.py`, steps 1–10 of §10. Every step reads live state first, re-running saves
nothing (proved: a second run of all ten prints only *nothing saved / already built*), every control save is
version-pinned and proved by signature diff, and `o2i.py check` is the read-only verification.

### 14.1 The three unproven things of §13

| Unknown | Outcome |
|---|---|
| A **多 ↔ 多** two-way Relation pair | **It holds, first try.** Order Lines' *Invoice Lines* (`enumDefault` 2) pairs with Invoice Lines' *Sales Order Lines* through the documented handshake (the reserved `sourceControlId`, `sourceControlType` 6, `enumDefault` 2) — the reverse half of that handshake is always multiple, so the only new thing was the forward side. Writing either half makes the other read it back, and **the reverse half is writable**, which is what lets Create Invoice write the link inside the create as Odoo does. §4.1's one-to-many fallback was not needed |
| A **filtered 汇총 over a type-53 function formula's numeric result** | **It works**, once the formula has actually computed (below). All five counts on Orders read correctly, `dataType` **6** — a function formula is read by the filter editors as its *result* type |
| Whether a **`create_record` node's own record can be bound by a later node** | **It can.** The sub-process node's own `flowNodeList` lists *Make the invoice* (type 6) among the nodes it may reference, and a parameter bound to `$<create node>-rowid$` stores and reads back. **Node 5 was kept anyway**: it re-reads the invoice from the worksheet, so the loop cannot attach lines to a header that failed to store, and its `executeType` 0 stops the run if it is not there. Switching is a one-line change in `create_nodes` |

### 14.2 Three platform findings this build paid for

1. **A lookup is only *stored* when `strDefault` is `"00"`.** hap-cli's SHEET_FIELD default is `"10"`, a *display*
   lookup: the value renders in the form and `record get` answers with it, but nothing is written into the
   record's own column, so **a 汇총's filter over it matches nothing and computes 0.00 with no error anywhere.**
   Measured: *Document Type* as `"10"`, *is Customer Invoice* on an invoice line that plainly was one summed
   0.00; *is not Customer Invoice* on the same line summed 3.00. Invoice Lines' own three lookups carry `"00"`
   (`invlines.py:546` already names it) and filter correctly.
2. **A function formula (type 53) added with `add-fields` computes nothing until a full save changes it.** Both
   §6.1 formulas were appended carrying their final expression, read back exactly as sent, and stored empty on
   all 41 lines; the first pinned save that *changed* the expression filled every one within seconds. A **汇총**
   appended the same way computes at once (*Product lines* did). `o2i.py` therefore appends a function formula
   carrying the placeholder `0` and always writes the real expression in the pinned save, and `nudge_formula`
   proves it computed before the step returns.
3. **A workflow search step's filter cannot express an OR.** `batch-add --nodes` refuses an OR-of-AND outright
   (`flowNode/batchAdd` answers `筛选条件配置不正确`, because it sends the filter as `operateCondition`, a single
   AND list). `node save --type 13` *accepts* two groups and then does not mean it: the `filters` wrapper's
   **`spliceType` joins every condition it holds**, so 2 OR-ed the conditions themselves. Sent that way,
   Create Invoice's get-multiple returned **every order line in the app** instead of this order's (see §14.5).
   The working examples on this app all carry `spliceType` **1**. Consequence for anything else reading a
   search step back: a two-condition filter saved with `spliceType` 2 is an OR — *Find the invoice just made*
   was briefly "this order's Source Document **or** any draft".

### 14.3 What was built

| Worksheet | Control | Id | Type |
|---|---|---|---|
| Invoice Lines | Document Type (`move_type`, hidden) | `6ab2cb9ae54d2a34faaa9b98` | 30 |
| Order Lines | Order Status (`state`, hidden) | `6ab2cb9d805aef7032e32a68` | 30 |
| Order Lines | Invoice Lines (`invoice_lines`, hidden, **multiple**) | `6ab2cbdfbd43f55762240234` | 29 |
| Invoice Lines | Sales Order Lines (`sale_line_ids`, hidden, multiple) | `6ab2cbdfbd43f55762240235` | 29 |
| Orders | Invoices (`invoice_ids`, read-only, multiple) | `6ab2cbf2e43d174ab3cd77aa` | 29 |
| Invoices | Sales Orders (no alias, read-only, multiple) | `6ab2cbf2e43d174ab3cd77ab` | 29 |
| Orders | Invoice Count (`invoice_count`) | `6ab2cc19e54d2a34faaa9b9f` | 37 |
| Invoices | Sales Order Count (`sale_order_count`) | `6ab2cc4a805aef7032e32a7c` | 37 |
| Order Lines | Qty on invoices (hidden) | `6ab2ce11e54d2a34faaa9ba7` | 37 |
| Order Lines | Qty on credit notes (hidden) | `6ab2ce11e54d2a34faaa9ba8` | 37 |
| Order Lines | **Quantity Invoiced** (`qty_invoiced`) — **converted in place, 6 → 31** | `6ab0c864e43d174ab37535fc` | 31 |
| Order Lines | Quantity To Invoice (`qty_to_invoice`) | `6ab2d06fe43d174ab3cd77d2` | 53 |
| Order Lines | Line Invoice Status (`invoice_status`, hidden) | `6ab2d0727d58b0f4498fcf93` | 53 |
| Order Lines | **Invoiceable line** (hidden, no alias) — *not in §6, see §14.4* | `6ab2dbc2805aef7032e32ae3` | 53 |
| Orders | Lines to invoice / not to invoice / invoiced / upselling / Product lines (all hidden) | `…9bbb` `…9bbc` `…9bbd` `…9bbe` `…9bbf` | 37 |

Orders' **Invoice Status** already carried the alias `invoice_status` (the brief's *what changed*), so step 5
wrote none. **Quantity To Invoice was added to the Orders subtable grid**, right after Quantity Invoiced, in the
same pinned save that extended `advancedSetting.controlssorts`.

| Workflow / button / view | Id |
|---|---|
| Orders: Invoice Status follows the order's own Status (Orders, 新增或更新, narrowed to Status) | `6ab2d2c0a2c872a5c14057fc` |
| Orders: Invoice Status follows its lines (Order Lines, 新增或更新, narrowed to Orders · Display Type · Quantity · Quantity Delivered · Invoice Lines) | `6ab2d2df94093ab76bdda713` |
| Orders: Invoice Status when a line is deleted (Order Lines, 删除) | `6ab2d2fe94093ab76bddae2f` |
| Orders: Create Invoice (button, batch on) | button `6ab2d6a07d58b0f4498fcfa3`, workflow `6ab2d6a0a2c872a5c1408ae6` |
| Orders: Create Invoice: one order line (the child flow) | `6ab2d7f5789584ded345986f` |
| Orders view **To Invoice** / **To Upsell** (after Orders, so the default view is unchanged) | `6ab2d48dbd43f5576224026a` / `6ab2d48ee54d2a34faaa9bd1` |

**Invoicing Closed is not a trigger field** of the status workflows, against §6.4's wording: Odoo's
`invoicing_closed` is not in `_compute_invoice_status` at all, so it cannot change the answer, and an extra
trigger field only costs runs. It is in the button's condition, where §6.4 puts it.

### 14.4 Two divergences this build added to §12

| # | Odoo 19.0 | Here | Why |
|---|---|---|---|
| 21 | `_get_invoiceable_lines` decides per line, in Python | an extra hidden type-53 formula **Invoiceable line** on Order Lines decides it, and the loop's filter is a flat AND on it | a workflow search step's filter cannot express an OR (§14.2 item 3). It also makes §12.4's section behaviour one editable expression |
| 22 | the invoice line's taxes are the **order line's** | still the **product's** | §14.6: gating the account automation needs more than a filter, so it was not touched |

`Accounting Date` and `Auto-post` are written on the new invoice although `_prepare_invoice` does not carry
them: both are `account.move`'s own **field defaults** (`date = fields.Date.context_today`,
`auto_post` default `'no'`), which Odoo's create applies anyway, and both are **required** here — an invoice
without them is one a person could not save from the form.

### 14.5 The wrong run, and what is left of it

The first press of Create Invoice ran with the OR-shaped filter of §14.2 item 3 and made **one invoice with 41
lines — one per order line in the whole app**, each linked back to its order line. Repaired the same minute:
the invoice was **cancelled** (which takes it out of both quantity 汇총) and **renamed**
*TEST o2i - WRONG RUN 23 Sep, cancelled and unlinked, safe to delete*, and all 41 lines had their *Sales Order
Lines* emptied. Verified afterwards: **every order line in the app reads Quantity Invoiced 0.00 and no invoice
link** except the TEST chair line, which legitimately keeps the fixture's one; every order's Invoice Status
agrees with its own five counts. **Nothing was deleted.**

What is left for the owner to decide:

* invoice `8749c45a-d4a9-4616-900c-6121c99c36fe` and its **41 orphan invoice lines** — cancelled, unlinked,
  named; 06 has no Archive, so only a deletion clears them;
* the app's own orders' **Invoice Status is now computed**, not seeded. Every value agrees with its counts, but
  the tenant's seeded values have been overwritten where they differed.

### 14.6 Step 7, and what was deliberately not done

*Invoices: Payment Terms follow the Customer / Vendor* (`6aab8f1016473257ad5c91e0`) **was gated**, with no node
added, removed or re-pointed and no field write touched:

* the two paths *Customer document — the contact's Customer Payment Terms* and *Vendor document — …* each gained
  one condition, **Payment Terms is empty** (conditionId 8) on the trigger record;
* the else path *Otherwise — the Payment Terms are left as they are* gained two OR-groups — customer types with
  Payment Terms **not** empty, and vendor types likewise — because a run that matches no path of an exclusive
  gateway stops there (`causeMsg` 未通过分支) and would have taken the Due Date chain down with it.

Proved at runtime on two TEST invoices for the same customer (whose default is *30 Days*): one created carrying
*Immediate Payment* kept it and got Due Date 2026-09-23; one created with no term got *30 Days* and Due Date
2026-10-23. **Side effect to record**: a later change of Customer / Vendor no longer re-derives a term the
invoice already has. Odoo's compute is `partner.property_payment_term_id or move.invoice_payment_term_id`
(`account/models/account_move.py:1081-1089`) with `precompute=True`, so it does overwrite on a partner change —
that half is lost.

*Invoice Lines: fill the account of a new line* (`6aab44254f2a99acac0f026f`) **was not touched.** §3.4 says one
step carries the Taxes entry; read live, **four** do — every step that takes an account from a product or a
category also writes that product's Sales or Purchase Taxes:

| Step | Id |
|---|---|
| Take the product's Income Account | `6aab44334f2a99acac0f0456` |
| Take the category's Income Account | `6aab44334f2a99acac0f047b` |
| Take the product's Expense Account | `6aab44344f2a99acac0f04ef` |
| Take the category's Expense Account | `6aab44358e75db182e835375` |

Gating those on *Taxes is empty* is not a filter: each of the four paths would have to split into "the line
already carries taxes" and "it does not" — four gateways, eight paths and four duplicate update steps inside a
built, reviewed workflow. Two smaller options for the owner to choose between:

* **a) additive**: append three nodes after the existing gateway — get the line's Sales Order Lines, a branch on
  whether it came from an order, and one update that re-writes the Taxes from the order line. Faithful to
  `sale_order_line.py:1543`, and it touches no existing node;
* **b) split**: remove the four Taxes entries and give Invoice Lines a second small workflow, *fill the taxes of
  a new line*, whose **trigger condition** is Taxes is empty — a filter, but it does edit the four steps.

Until then the invoice line's taxes are the product's, which is §12 divergence 6's pre-fix state.

### 14.7 What the CLI proved, and what still needs a browser

`o2i.py selfcheck` is green, and these were driven end to end:

* the **多↔多** pair both ways, and both reverse halves written by hand;
* Quantity Invoiced following a **draft** invoice (3.00), falling to 0.00 when it is **cancelled**, returning
  when it is **posted** — Odoo's rule exactly (`sale_order_line.py:1007-1017`);
* Quantity To Invoice 7.00 on a confirmed order's product line, 0.00 on a section and on an unconfirmed order;
* Line Invoice Status **1** with something to invoice even when Quantity Delivered exceeds Quantity, which is
  Odoo's own test order (`qty_to_invoice != 0` is tested **before** upselling);
* the five counts on 19 orders, every one agreeing with the statuses;
* Status → Quotation → *Nothing to Invoice*, → Sales Order → *Fully Invoiced*; a line-driven quantity change →
  *To Invoice* and back;
* **Create Invoice pressed**: one draft invoice, four lines in Sequence order (section · chair 7 · desk 4 ·
  note), the order's taxes, an account on each product line, amounts 1,700.00 / 170.00 / 1,870.00, Accounting
  Date today, Auto-post No, the order's Payment Terms surviving the gate, the Salesperson copied, Sales Orders
  1, Source Document S00024, and `sale_line_ids` on every line — the link written **inside** the create;
* **pressed a second time**: no invoice, and the run's own detail shows it passing *Trigger · Get the order ·
  How many lines · Is there anything to invoice? · Nothing to invoice* and ending `status` 2 — a notice, not an
  abort;
* the chair's Quantity raised by 2 → *To Invoice* → pressed → a second invoice with **that one line at
  quantity 2** (plus the section and the note, §12.4);
* `repair` on a deliberately emptied Invoices list: rebuilt from the lines, and the second run reported nothing.

Still needs the browser, because a CLI cannot see it:

* the **notice** as the user meets it — *【Nothing to invoice】* in the notification list, and the button
  reporting "Operation completed" all the same;
* the two new views and the Invoice Status quick filter as lists;
* Quantity To Invoice as a **column** of the order-line grid, and that none of the hidden controls appears in
  either grid;
* the **placement** of the 18 controls still at row 9999 — that is the owner's, and `o2i.py check` prints each
  one's intended place;
* deleting a line from a TEST order, which would exercise *Invoice Status when a line is deleted* — its body is
  identical to the create-or-update one, which is proved, but the brief forbade deleting any record, so the
  delete trigger itself has never fired.

### 14.8 Not built

§6.1 items 7 and 8 (*Untaxed Invoiced*, *Untaxed To Invoice*) and §6.2 items 15 and 16 (*Already invoiced*,
*Un-invoiced Balance*) are the untaxed amount figures. §10's ten steps do not place them in any step, and they
are not in this bundle. Down payments (§7) are not built, as §7.3 recommends.
