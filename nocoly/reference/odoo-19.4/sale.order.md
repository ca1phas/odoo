# `sale.order` — Orders (Odoo saas~19.4+e)

Read from **casimir.odoo.com** on 21 Sep 2026 over read-only RPC. The 19.0 Community checkout is behind the
tenant — read this, not the repo.

## Menus and actions

| Menu | Action | Context |
|---|---|---|
| Sales › Orders › **Quotations** | `act_window` **497** | `{'search_default_my_quotation': 1}` |
| Sales › Orders › **Orders** | `act_window` **496** | `{'search_default_sales': 1}` |

Both point at `sale.order`; they are two filtered views of one table, exactly as Invoices/Bills/Journal
Entries are for `account.move`. `view_mode` is `list, kanban, form, calendar, pivot, graph, activity, map`.

## The status bar

`state`, `statusbar_visible="draft,sent,sale"`:

| Value | Label |
|---|---|
| `draft` | **Quotation** |
| `sent` | **Quotation Sent** |
| `sale` | **Sales Order** |
| `cancel` | Cancelled (not on the bar) |

A separate boolean **`locked`** gates Lock / Unlock and freezes a confirmed order.

## Header buttons

| Method | Label | Hidden when |
|---|---|---|
| `action_confirm` | **Confirm** | `state != 'draft'` (primary) / `state != 'sent'` |
| `action_quotation_send` | **Send** | `state != 'draft'` / `state not in ('sent','sale')` |
| `sale.action_report_saleorder` | **Download** | `state == 'sale'` |
| `action_preview_sale_order` | **Preview** | — |
| `action_cancel` | **Cancel** | `state not in ['draft','sent','sale'] or not id or locked` |
| `action_draft` | **Set to Quotation** | `state != 'cancel'` |
| `action_lock` | **Lock** | `locked or state != 'sale'` |
| `action_unlock` | **Unlock** | `not locked` |
| action **495** | **Create Invoice** | `invoice_status != 'to invoice' …` / `invoice_status != 'no' or state != 'sale'` |
| `action_reopen_order` | Reopen Invoicing | (truncated in the extract) |
| `payment_action_capture` · `payment_action_void` | Capture / Void Transaction | `not has_authorized_transaction_ids` |

## Form — header fields

`name · partner_id · partner_invoice_id · partner_shipping_id · validity_date · date_order ·
pricelist_id · currency_id · payment_term_id · commitment_date · delivery_status · expected_date ·
document_tax_mode`

Plus warning/alert fields (`sale_warning_text`, `partner_credit_warning`, `duplicated_order_ids`) and the
smart-button counts (`invoice_count`, `project_count`, `tasks_count`, `transaction_count`).

### Read-only and visibility conditions, as read from the arch

| Field | readonly | invisible |
|---|---|---|
| `partner_id` | `state in ['cancel','sale']` | — |
| `partner_invoice_id` | `state == 'cancel' or locked` | — |
| `partner_shipping_id` | `state == 'cancel' or locked` | — |
| `validity_date` | `state in ['cancel','sale']` | `state == 'sale'` |
| `date_order` | `state in ['cancel','sale']` | two instances — one hidden for `['sale','cancel']`, one for `['draft','sent']`, so the label changes from *Quotation Date* to *Order Date* |
| `pricelist_id` | `state in ['cancel','sale']` | — |
| `payment_term_id` | — | — |
| `commitment_date` | `state == 'cancel' or locked` | — |
| `document_tax_mode` | `state != 'draft'` | — |
| `require_signature` · `require_payment` | `state in ['cancel','sale']` | — |
| `prepayment_percent` | `state in ['cancel','sale']` | `not require_payment` |
| `sale_order_template_id` | `state in ['cancel','sale']` | — |
| `user_id` · `team_id` | — | — |

`document_tax_mode` is **the same field ERP Master already models on Invoices** (Tax Excluded / Tax Included).

## Tabs

**Order Lines · Quote Builder · Other Info**

### Order Lines — `order_line` (`sale.order.line`)

Fields declared on the embedded list: `sequence`, `display_type`, `product_id`, `name`, `product_uom_qty`,
`qty_delivered`, `qty_invoiced`, `product_uom_id`, `price_unit`, `tax_ids`, `discount`, `customer_lead`,
`price_subtotal`, `price_total`, `is_optional`, `invoice_lines`, plus the combo/variant machinery
(`combo_item_id`, `linked_line_id`, `product_custom_attribute_value_ids`,
`product_no_variant_attribute_value_ids`, `selected_combo_items`) and the down-payment flag
`is_downpayment`.

`display_type` selection: **`line_section` Section · `line_subsection` Subsection · `line_note` Note**.
A product line has `display_type` **NULL** — there is no explicit "Product" option, unlike the modelling
choice ERP Master made on Invoice Lines.

Other labels: `product_uom_qty` = *Quantity*, `discount` = *Discount (%)*, `customer_lead` = *Lead Time*
("Number of days between the order confirmation and the shipping of the products"), `is_optional` =
*Optional Line*.

### Quote Builder

`quotation_document_ids` and `customizable_pdf_form_fields` — **this is where Headers/Footers attach.**

### Other Info — groups

| Group | Fields |
|---|---|
| Confirmation | `require_signature`, `require_payment`, `prepayment_percent` |
| Sales | `user_id`, `team_id`, `sale_order_template_id`, `reference`, `client_order_ref`, `tag_ids` |
| Invoicing | `fiscal_position_id`, `preferred_payment_method_line_id`, `project_id`, `journal_id`, `invoice_status` |
| Shipping | `incoterm`, `incoterm_location` |
| Tracking | `origin`, `opportunity_id`, `campaign_id`, `medium_id`, `source_id`, `utm_reference` |

## List columns

`name · date_order(shown) · delivery_date(hidden) · commitment_date(hidden) · partner_id · user_id(shown) ·
activity_ids(shown) · team_id(hidden) · amount_untaxed(hidden) · amount_tax(hidden) · amount_total(shown) ·
tag_ids(hidden) · state(hidden) · delivery_status(hidden) · invoice_status(shown) ·
client_order_ref(hidden) · validity_date(hidden) · expected_date · invoicing_closed`

## Computed status fields

`invoice_status`: **`upselling` Upselling Opportunity · `invoiced` Fully Invoiced · `to invoice` To Invoice ·
`no` Nothing to Invoice`**

`delivery_status`: **`pending` Not Delivered · `started` Started · `partial` Partially Delivered ·
`full` Fully Delivered`**

## SQL constraints

| Name | Definition |
|---|---|
| `sale_order_date_order_conditional_required` | `CHECK((state = 'sale' AND date_order IS NOT NULL) OR state != 'sale')` |
| `sale_order_line_accountable_required_fields` | `CHECK(display_type IS NOT NULL OR is_downpayment OR product_uom_id IS NOT NULL)` |
| `sale_order_line_non_accountable_null_fields` | `CHECK(display_type IS NULL OR (product_id IS NULL AND price_unit = 0 AND product_uom_qty = 0 AND product_uom_id IS NULL AND customer_lead = 0))` |

The last two are the same pair `account.move.line` carries, so ERP Master's *A section or a note carries no
figures* rule on Invoice Lines transfers directly.

## Defaults on a new record

`state` = `draft`, `date_order` = **now** (a datetime, not a date), `company_id` = 1. `validity_date`,
`require_signature`, `require_payment` and `document_tax_mode` are **not** in `default_get` — they are
computed from the company's settings or left empty.

## The 12 records on the tenant

29 order lines across them.

| Number | Customer | State | Untaxed | Total | Validity | Invoice status |
|---|---|---|---|---|---|---|
| S00010 | Petronas Digital Sdn Bhd | Sales Order | 247,225.00 | 271,743.50 | 2026-07-12 | To Invoice |
| S00011 | Sunway Construction Group | Sales Order | 104,603.20 | 115,063.52 | 2026-08-02 | Fully Invoiced |
| S00012 | Universiti Teknologi Malaysia | Quotation Sent | 178,040.00 | 192,283.20 | 2026-09-20 | Nothing to Invoice |
| S00013 | TechBridge Distributors | Quotation Sent | 75,094.80 | 82,604.28 | 2026-10-01 | Nothing to Invoice |
| S00014 | Klinik Kesihatan Damansara | Sales Order | 11,432.00 | 12,575.20 | 2026-10-04 | Fully Invoiced |
| S00015 | Bumi Retail Ventures | Cancelled | 7,856.50 | 8,642.15 | 2026-06-18 | Nothing to Invoice |
| S00016 | Sarawak Timber Logistics | Sales Order | 180,000.00 | 194,400.00 | 2026-05-08 | Fully Invoiced |
| S00017 | Nasi Kandar Pelita Holdings | Quotation | 77,460.00 | 84,088.80 | 2026-09-27 | Nothing to Invoice |
| S00019 | Casimir | Quotation | 1,019.00 | 1,120.90 | 2026-10-14 | Nothing to Invoice |
| S00020 | Casimir | Cancelled | — | 3,027.80 | — | Nothing to Invoice |
| S00021 | Casimir | Quotation Sent | — | 3,027.80 | — | Nothing to Invoice |
| S00022 | Klinik Kesihatan Damansara | Quotation | — | 0.00 | — | Nothing to Invoice |

There is no S00018. **Five of these customers are not in ERP Master's Contacts** — Petronas Digital Sdn Bhd,
Universiti Teknologi Malaysia, TechBridge Distributors, Bumi Retail Ventures and Nasi Kandar Pelita
Holdings — so seeding Orders faithfully means seeding those five contacts first.

S00011, S00014, S00016 and S00021 are the Source Documents already sitting on ERP Master's seeded invoices.
