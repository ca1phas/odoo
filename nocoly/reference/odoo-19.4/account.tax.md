# account.tax — as on casimir.odoo.com (Odoo saas~19.4+e)

Read-only extract, 18 Sep 2026: `fields_get`, the raw `ir.ui.view.arch_db` of every view of `account.tax` and
`account.tax.group` **including the three modules that extend the form on this tenant**, the window actions and
their menus, all 35 taxes with every field a person can edit, all 10 tax groups, all 36 repartition lines of the
nine taxes that have them, the company's tax settings, the taxes of all 14 products, the `tax_ids` of every
account, and the `tax_ids`, `tax_line_id` and `tax_base_amount` of all 31 invoice lines. Behaviour the tenant
cannot show is read from the Odoo 19.0 source in this repo: `addons/account/models/account_tax.py`,
`account_tax_views.xml`, `account_account.py`, `account_move_line.py`, `product.py`,
`addons/account/security/ir.model.access.csv` and `account_security.xml`.

The 35 records are saved as `nocoly/data/casimir-taxes.json`. Unlike the countries and the states they were
**read straight out of the tenant** — 35 records is small enough to carry through the browser without the digest
reconciliation those two needed.

Menu: **Invoicing ▸ Configuration ▸ Accounting ▸ Taxes** (window action `account.action_tax_form`, id
`action_tax_form`, path `taxes`, view mode `list,kanban,form`). Beside it, **Tax Groups**
(`account.action_tax_group`) — behind `base.group_no_one`, so it is a developer-mode screen.

The action's context is `{'search_default_sale': True, 'search_default_purchase': True, 'active_test': False}`:
the list opens on one **Sale or Purchase** facet and, because `active_test` is off, **shows the inactive taxes
too** — 35 rows, not 10.

## Fields

Every field is module `account` unless noted. S = stored.

| Field | Label | Type | Req. | Default | Notes |
|---|---|---|---|---|---|
| `name` | Tax Name | char S | **yes** | — | translatable; tracked; part of the compound uniqueness below |
| `type_tax_use` | Tax Type | selection S | **yes** | `sale` | `sale` Sales · `purchase` Purchases · `none` None. Help: "Determines where the tax is selectable. Note: 'None' means a tax can't be used by itself, however it can still be used in a group." Tracked |
| `tax_scope` | Tax Scope | selection S | | — | `service` Services · `consu` Goods. Empty means both |
| `amount_type` | Tax Computation | selection S | **yes** | `percent` | `group` Group of Taxes · `fixed` Fixed · `percent` Percentage · `division` Percentage Tax Included · **`code` Custom Formula** — the last from `account_tax_python`, which is installed here. Tracked |
| `amount` | Amount | float(16, 4) S | **yes** | 0.0 | renders with **four decimals** — 10% G shows `10.0000` — and a `%` suffix unless Tax Computation is Fixed. Tracked |
| `formula` | Formula | char S | | `price_unit * 0.10` | module `account_tax_python`. Only read when Tax Computation is Custom Formula; **every** tax carries the default string anyway |
| `description` | Description | html S | | — | translatable. On this tenant always one `<div>` of plain text — *SST 10%*, *Not Applicable* |
| `invoice_label` | Label on Invoices | char S | | — | translatable; what prints on the document. `tax_label` = `invoice_label or name` |
| `active` | Active | boolean S | | **true** | help "Set active to false to hide the tax without removing it." |
| `sequence` | Sequence | integer S | **yes** | 1 | the list's handle column; `_order = 'sequence,id'` |
| `tax_group_id` | Tax Group | many2one → `account.tax.group` S | **yes** (when Tax Computation ≠ Group of Taxes) | computed | domain `[('country_id', 'in', (country_id, False))]` |
| `country_id` | Country | many2one → `res.country` S | **yes** | computed from the company's fiscal country | help "The country for which this tax is applicable." All 35 are Malaysia |
| `price_include_override` | Included in Price | selection S | | — (placeholder *Default*) | `tax_included` · `tax_excluded`. Overrides the company's `account_price_include`. Tracked |
| `include_base_amount` | Affect Base of Subsequent Taxes | boolean S | | false | Tracked |
| `is_base_affected` | Base Affected by Previous Taxes | boolean S | | **true** | on the form behind `base.group_no_one`. Tracked |
| `analytic` | Include in Analytic Cost | boolean S | | false | on the form behind `analytic.group_analytic_accounting` |
| `tax_exigibility` | Tax Exigibility | selection S | | `on_invoice` | `on_invoice` Based on Invoice · `on_payment` Based on Payment. Invisible unless the company has cash-basis on — **this company has not** |
| `cash_basis_transition_account_id` | Cash Basis Transition Account | many2one → `account.account` S | when Based on Payment | — | invisible while Based on Invoice |
| `invoice_legal_notes` | Legal Notes | html S | | — | its own group at the foot of Advanced Options |
| `children_tax_ids` | Children Taxes | many2many → `account.tax` S | | — | only when Tax Computation is Group of Taxes. **No tax on this tenant has any** |
| `invoice_repartition_line_ids` | Distribution for Invoices | one2many → `account.tax.repartition.line` S | | computed | |
| `refund_repartition_line_ids` | Distribution for Refunds | one2many → `account.tax.repartition.line` S | | computed | |
| `fiscal_position_ids` | Fiscal Position | many2many → `account.fiscal.position` S | | — | placeholder *all* |
| `original_tax_ids` | Replaces | many2many → `account.tax` S | | — | hidden unless `display_alternative_taxes_field` |
| `l10n_my_tax_type` | Malaysian Tax Type | selection S | | — | module `l10n_my_myinvois`: `01` Sales Tax · `02` Service Tax · `03` Tourism Tax · `04` High-Value Goods Tax · `05` Sales Tax on Low Value Goods · `06` Not Applicable · `E` Tax exemption |
| `ubl_cii_tax_category_code` | Tax Category Code | selection S | | — | module `account_edi_ubl_cii` |
| `is_used` | Tax used | boolean, computed | | — | true for **2** of the 35 — 8% S and 10% G |
| `company_id` | Company | many2one → `res.company` S | **yes** | the current company | read-only; hidden on a single-company database |

## Constraint — a **compound** uniqueness, not a single field

| | |
|---|---|
| `_constrains_name` | unique **(company, name, type_tax_use, tax_scope, country_id)**, skipped when `type_tax_use = 'none'` |
| Message | *"Tax names must be unique!"* followed by `- <name> in <company>` per clash |

That is why the tenant's names repeat: **0% NA** is both a Sales tax and a Purchase tax, **5% G**, **8% S** and
**10% G** each exist twice for the same reason, and **Exempt C 1,2** exists once for Sales (Goods) and once for
Purchases (Goods). Fourteen of the 35 names are shared by two records.

Two more constraints: the tax group's country must equal the tax's (`validate_tax_group_id`), and a
Based-on-Payment tax needs a reconcilable transition account.

## Views

- **List** `account.view_tax_tree` — the tenant's arch is **identical to the 19.0 source**:
  `<list decoration-muted="not active">` · sequence (handle) · **Tax Name · Description · Tax Type · Tax Scope ·
  Label on Invoices · Active** (boolean toggle), with *Replaces*, *Country* and *Company* as columns switched
  off. Seen on the tenant: 35 rows, a **New** button, the facet *Sale or Purchase*, `1-35 / 35`.
- **Form** `account.view_tax_form` — **19.4 has moved three fields since 19.0**, so the source alone would have
  been wrong here:

  | | 19.0 source | casimir (19.4) |
  |---|---|---|
  | header left | Tax Name · Tax Computation · **Active** | Tax Name · Tax Computation · Amount % · **Description** |
  | header right | Tax Type · **Tax Scope** · Amount % · Fiscal Position · Replaces | Tax Type · Fiscal Position · Replaces |
  | Advanced Options left | Label on Invoices · **Description** · Tax Group · Analytic · Company · Country · Legal Notes | Label on Invoices · **Tax Scope** · Tax Group · Analytic · Company · Country |
  | Advanced Options right | Included in Price · Affect Base · Base Affected · Exigibility · Cash Basis Account | the same **plus Active** |
  | foot | — | its own group **LEGAL NOTES** |

  Tab **Definition**: *Distribution for Invoices* and *Distribution for Refunds* side by side (hidden when Tax
  Computation is Group of Taxes), else the *Children Taxes* list. A `<chatter/>` closes the form —
  `account.tax` inherits `mail.thread`.
- **Three modules extend the form on this tenant**, and none of them is in the 19.0 source read alone:
  `account_edi_ubl_cii` adds Tax Category Code and two exemption-reason fields after Country;
  `account_tax_python` adds **Formula** after Tax Computation, required when the computation is Custom Formula;
  `l10n_my_myinvois` adds **Malaysian Tax Type** and its exemption reason before Description.
- **What the tenant's own user actually sees** on the form: Analytic is absent (no
  `analytic.group_analytic_accounting`), Company is absent (one company), Tax Exigibility is absent (the company
  has cash basis off), and **Base Affected by Previous Taxes is present** because the user holds
  `base.group_no_one`.
- **Search** `account.view_account_tax_search`: fields Name, Description, Amount, Fiscal Position; filters Sale ·
  Purchase — Services · Goods — Domestic — Active · Inactive; group-by Tax Type, Tax Scope, Fiscal Position.
- **Kanban** `account.view_tax_kanban` (mobile): name, Tax Type and Tax Scope as pills, description muted.

## Access (`addons/account/security/ir.model.access.csv`)

| Group | R | W | C | D |
|---|---|---|---|---|
| `base.group_user` | yes | — | — | — |
| `account.group_account_readonly` | yes | — | — | — |
| `account.group_account_invoice` | yes | — | — | — |
| `account.group_account_manager` | yes | yes | yes | yes |

**Exactly the shape of `account.account`** (rows 68–72 of the same file): the accounting administrator writes,
everybody else reads. `account.tax.group` and `account.tax.repartition.line` carry the same four rows.

The *menu* is stricter than the model: `menu_finance_configuration` is `groups="account.group_account_manager"`,
so only an administrator reaches the Taxes screen — but every internal user can read a tax, which is what lets an
invoice line show one.

## Where other models point here

| Model | Field | What it does |
|---|---|---|
| `account.move.line` | `tax_ids` many2many (*Taxes*) | The taxes on a line. Computed from the product and the fiscal position, then editable. Context `{'active_test': False, 'hide_original_tax_ids': True}` |
| `account.move.line` | `tax_line_id` many2one (*Originator Tax*) | Set on the **tax lines Odoo writes itself** — `display_type = 'tax'` — with `tax_base_amount` carrying the base |
| `account.move.line` | `price_total` | `price_subtotal` plus the line's tax |
| `product.template` | `taxes_id` many2many (*Sales Taxes*), domain `type_tax_use = sale` | Default taxes when selling; defaults to the company's `account_sale_tax_id` |
| `product.template` | `supplier_taxes_id` many2many (*Purchase Taxes*), domain `type_tax_use = purchase` | Default taxes when buying |
| `account.account` | `tax_ids` many2many (*Default Taxes*) | On the account form's Accounting tab. **Not one of this tenant's accounts has any** |
| `account.fiscal.position`, the localisations | `tax_ids`, `state_ids`, … | Not in Phase 1 |

## The company's tax settings, 18 Sep 2026

| | |
|---|---|
| Fiscal country | **Malaysia** · currency MYR |
| Default sale tax | **10% G** (id 7) · default purchase tax **0% NA** (id 2) |
| `account_price_include` | **tax_excluded** — so no tax on this tenant is price-included |
| `tax_exigibility` | **off** — the cash-basis option is hidden on every tax form |
| `tax_calculation_rounding_method` | **round_per_line** |

## The records — 35 taxes, 18 Sep 2026

Every one of the 35 is **Malaysia**, **sequence 1**, **Based on Invoice**, *Included in Price* empty, *Affect
Base of Subsequent Taxes* off, *Base Affected by Previous Taxes* on, *Include in Analytic Cost* off, with **no
children and no legal notes**. Ten are active and **25 are archived**; the list shows all 35 because the action
turns `active_test` off. Only two have ever been used on a document: **8% S** and **10% G**.

Type `s` = Sales, `p` = Purchases. Computation `p` = Percentage, `c` = Custom Formula. `A` = active.

| id | Tax Name | Type | Scope | Comp. | Amount | | Description | Label | Tax Group | Fiscal position |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0% NA | s | — | p | 0 | A | Not Applicable | 0% | Not Applicable | MY Domestic |
| 2 | 0% NA | p | — | p | 0 | A | Not Applicable | 0% | Not Applicable | MY Domestic |
| 3 | 5% G | s | Goods | p | 5 | A | SST 5% | 5% | SST 5% | MY Domestic |
| 4 | 6% S | s | Services | p | 6 | | SST 6% | 6% | SST 6% | MY Domestic |
| 5 | **8% S** | s | Services | p | 8 | A | SST 8% Other than Group H | 8% | SST 8% | MY Domestic |
| 6 | 8% S H | s | Services | p | 8 | A | SST 8% Group H | 8% | SST 8% | MY Domestic |
| 7 | **10% G** | s | Goods | p | 10 | A | SST 10% | 10% | SST 10% | MY Domestic |
| 8 | 25 Per Card | s | — | c | 0 | | Credit card or Charge card service | RM25 | SST 25 Per Card | MY Domestic |
| 9 | X Per Litre G | s | Goods | c | 0 | | Goods under schedule 2 (Per Litre) | — | SST X Per Litre | MY Domestic |
| 10 | X Per Kilogram G | s | Goods | c | 0 | | Goods under schedule 2 (Per Kilogram) | — | SST X Per Kilogram | MY Domestic |
| 11 | X% | s | Goods | p | 0 | | Goods under schedule 2 (Ad-volerem) | — | SST X % | MY Domestic |
| 12 | EX | s | Goods | p | 0 | A | Sales exempted from tax, export | Export | Exempt | Foreign Trade |
| 13 | Exempt A | s | Goods | p | 0 | | Sales exempted from tax, schedule A | Exempt | Exempt | Exempted person under Schedule A |
| 14 | Exempt B | s | Goods | p | 0 | | Sales exempted from tax, schedule B | Exempt | Exempt | Exempted person under Schedule B |
| 15 | Exempt C 1,2 | s | Goods | p | 0 | | Sales exempted from tax, schedule C, Item 1 and 2 | Exempt | Exempt | Exempted person under Schedule C |
| 16 | Exempt C 3,4 | s | Goods | p | 0 | | Sales exempted from tax, schedule C, Item 3 and 4 | Exempt | Exempt | Exempted person under Schedule C |
| 17 | Exempt C 5 | s | Goods | p | 0 | | Sales exempted from tax, schedule C, Item 5 | Exempt | Exempt | Exempted person under Schedule C |
| 18 | Exempt | s | Goods | p | 0 | | Services exempted from tax, schedule C, Item 5 | Exempt | Exempt | Exempted person under Schedule C |
| 19 | 5% G | p | Goods | p | 5 | A | SST 5% | 5% | SST 5% | MY Domestic |
| 20 | 6% S | p | Services | p | 6 | | SST 6% | 6% | SST 6% | MY Domestic |
| 21 | 8% S | p | Services | p | 8 | A | SST 8% | 8% | SST 8% | MY Domestic |
| 22 | 10% G | p | Goods | p | 10 | A | SST 10% | 10% | SST 10% | MY Domestic |
| 23 | Exempt C 1,2 | p | Goods | p | 0 | | Purchase under the schedule C, item 1 and 2 | Exempt | Exempt | — |
| 24 | Exempt C 3,4 | p | Goods | p | 0 | | Purchase under the schedule C, item 3 and 4 | Exempt | Exempt | — |
| 25 | Exempt C 5 | p | Goods | p | 0 | | Purchase under the schedule C, item 5 | Exempt | Exempt | — |
| 26 | IM S | p | Services | p | 6 | | Imported services | Import | SST 6% | Foreign Trade |
| 27 | IM Others S | p | Services | p | 8 | | Other imported services | Import | SST 8% | Foreign Trade |
| 28 | 5% G OU | s | Goods | p | 5 | | Value of Goods For Own Used / Disposed. Value of Free Services | — | SST 5% | — |
| 29 | 10% G OU | s | Goods | p | 10 | | Value of Goods For Own Used / Disposed. Value of Free Services | — | SST 6% | — |
| 30 | 6% S OU | s | Services | p | 6 | | Value of Goods For Own Used / Disposed. Value of Free Services | — | SST 8% | — |
| 31 | 8% S OU | s | Services | p | 8 | | Value of Goods For Own Used / Disposed. Value of Free Services | — | SST 10% | — |
| 32 | 5% G D | p | Goods | p | 5 | | SST 5% (Deduction) | 5% | SST 5% | — |
| 33 | 10% G D | p | Goods | p | 10 | | SST 10% (Deduction) | 10% | SST 10% | — |
| 34 | 5% G SC | s | Goods | p | 5 | | SST 5% (Sub-contracting) | 5% | SST 5% | — |
| 35 | 10% G SC | s | Goods | p | 10 | | SST 10% (Sub-contracting) | 10% | SST 10% | — |

Note ids **29–31**: their tax groups are one row out of step with their amounts — a 10% tax in *SST 6%*, a 6% in
*SST 8%*, an 8% in *SST 10%*. That is how `l10n_my` ships them and how the tenant holds them; it is copied, not
corrected.

The three **Custom Formula** taxes are the only ones whose `formula` is not the default: `quantity * 25`,
`quantity * 0.30`, `quantity * 0.01`. All three are archived.

**Malaysian Tax Type** across the 35: `01` Sales Tax ×10 · `02` Service Tax ×9 · `06` Not Applicable ×3 ·
`E` Tax exemption ×13.

## Tax groups — 10, all alike

| id | Name |
|---|---|
| 1–10 | SST 5% · SST 6% · SST 8% · SST 10% · SST 25 Per Card · SST X Per Litre · SST X Per Kilogram · SST X % · Not Applicable · Exempt |

Every one of the ten: country **Malaysia**, sequence **10**, Tax Payable Account **SST Payable**, Tax Receivable
Account **SST Receivable**, no advance account, no preceding subtotal. They differ **only in the name**.

## Distribution (repartition lines) — 36 lines, all the default

The nine taxes that have them (1, 2, 3, 5, 7, 12, 19, 21, 22) each carry four lines: invoice **base 100%** and
**tax 100%**, refund **base 100%** and **tax 100%**. Every *sale* tax's tax line posts to **SST Control
Account** with *Use in Tax Closing* on; every *purchase* tax's has **no account**. Nothing varies. On the form
the lines also carry **Tax Grids** (`tag_ids` → `account.account.tag`) — 10% G shows `SST02_11B_C`, `SST02_8`,
`SST02_11B_D` on its invoice lines and `SST02_13A_D` on its refund.

## Taxes in use on this tenant

**Products** — all 14 carry exactly one sales tax and one purchase tax:

| | Sales tax | Purchase tax |
|---|---|---|
| the 8 goods | **10% G** (id 7) | 0% NA (id 2) |
| the 6 services | **8% S** (id 5) | 0% NA (id 2) |

**Accounts** — **none**. Not one of the accounts has a Default Tax.

**Invoice lines** — the three documents the Invoices and Invoice Lines worksheets were built from:

| Document | Product lines | Untaxed | Tax | Total |
|---|---|---|---|---|
| SCG-PO-88213 (draft) | 3 × **10% G** | 104,603.20 | **10,460.32** | 115,063.52 |
| INV/2026/00001 (KKD-2026-009) | 3 × **10% G** | 11,432.00 | **1,143.20** | 12,575.20 |
| STL-2026-0042 (draft) | 2 × **8% S** | 180,000.00 | **14,400.00** | 194,400.00 |

Three further documents exist that neither worksheet seeded — INV/2026/00002 (*TEST demo run - delete me*),
INV/2026/00003 and a draft, all from the sale-order flow, each mixing 10% G and 8% S lines.

Each document carries **one `display_type = 'tax'` line per distinct tax**, written by Odoo, with
`tax_base_amount` the base it was computed on — `-11432` on INV/2026/00001's single 10% G line. Those lines are
Odoo's, not a person's, and are outside the Invoice Lines worksheet by its own §1.

**Every active tax on this tenant is a Percentage**, and the company rounds per line, so every figure above is
`subtotal × rate ÷ 100` rounded to two decimals. No Fixed, Custom Formula, Percentage-Tax-Included,
price-included or base-affecting tax is in use anywhere.
