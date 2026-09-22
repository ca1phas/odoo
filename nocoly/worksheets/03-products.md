# 03 · Products

| | |
|---|---|
| Nocoly app | ERP Master · menu group **Products** |
| Worksheet | Products |
| Odoo model | `product.template` |
| Reference | **casimir.odoo.com — Odoo saas~19.4+e**: fields by module, form, list, kanban, search, defaults, order and all 14 records, extracted read-only to `nocoly/reference/odoo-19.4/product.template.md`. Behaviour the tenant cannot show — onchange checks, domains, defaults in code — is read from the Odoo 19.0 source in this repo: `addons/product/models/product_template.py` |
| Phase | 1 — core worksheet 3 of 7 |
| Status | Built with the hap CLI and seeded on 15 Sep 2026 · UI-tested on 15 Sep 2026: 15 of 17 pass, 2 in part · ready for review |

The catalogue: every good and service a company sells or buys, with its price, cost and unit. Only the `product`
module's own fields are here, plus Sales Description; Sales, Purchase, Inventory, Invoicing and the optional bundles
append their fields when they land. Each product has exactly one variant until the Product Variants bundle.

## 1 · Requirements

### Fields

Labels are Odoo 19.4's. "Hidden" means not on the form but used by views, rules or buttons. Descriptions carry
Odoo's field help where it has one.

| # | Field | Odoo field | Nocoly type | Required | Default | Notes |
|---|---|---|---|---|---|---|
| 1 | Name | `name` | Text · **title field** | yes | — | Placeholder "e.g. Cheese Burger" |
| 2 | Favorite | `is_favorite` | Checkbox | no | unchecked | Odoo's star beside the name. Every view lists favourites first |
| 3 | Sales | `sale_ok` | Checkbox | no | checked | Under the name, as in Odoo. Unchecked hides the Sales tab |
| 4 | Purchase | `purchase_ok` | Checkbox | no | checked | Under the name. Odoo hides it for Combo products, which are not built |
| 5 | Image | `image_1920` | Attachment | no | — | The gallery card cover |
| 6 | Product Type | `type` | Single select, options side by side (Odoo's horizontal radio): Goods · Service | yes | Goods | Tab **General Information**. Service hides the Inventory tab. Combo waits for the Product Combos bundle |
| 7 | Sales Price | `list_price` | Currency MYR, shown as RM, 2 decimals | no | 1.00 | Tab General Information. Odoo precision "Product Price" = 2 |
| 8 | Unit | `uom_id` | Relation → Units & Packagings (single, **one-way**) | yes | Units | Tab General Information. The picker lists active units only (Odoo's `active_test`) and shows each one's Contains and Reference Unit, as Odoo's dropdown shows "Days --8 Hours--". No reverse field on Units & Packagings |
| 9 | Cost | `standard_price` | Currency MYR, shown as RM, 2 decimals | no | 0.00 | Tab General Information. Cannot be negative (rules) |
| 10 | Internal Reference | `default_code` | Text | no | — | Tab General Information. Odoo's form labels it "Reference"; list, search and field label say Internal Reference |
| 11 | Internal Notes | `description` | Rich text | no | — | Tab General Information. Placeholder "This note is only for internal purposes.". Odoo shows the field under the group title "Internal Notes"; the field itself is labelled Description |
| 12 | Packagings | `uom_ids` | Relation → Units & Packagings (multiple, **one-way**), shown as a dropdown | no | — | Tab **Sales**. The picker lists active units other than the product's Unit (Odoo domain `[('id', '!=', uom_id)]`); while Unit is empty it lists every active unit |
| 13 | Sales Description | `description_sale` | Text, multi-line | no | — | Tab Sales. Placeholder "This note is added to sales orders and invoices." |
| 14 | Weight | `weight` | Number, 2 decimals, suffix kg | no | 0 | Tab **Inventory**. Odoo precision "Stock Weight" = 2; its unit label (`weight_uom_name`) is kg |
| 15 | Volume | `volume` | Number, 2 decimals, suffix m³ | no | 0 | Tab Inventory. Odoo precision "Volume" = 2; unit label m³ |
| 16 | Active | `active` | Checkbox | — | checked | Hidden. Set by Archive / Unarchive |

**Added since by bundles:** **Category** (`categ_id`), a relation to Product Categories on General Information between Cost and Internal Reference — bundle 1, `08-product-categories.md`; **Income Account** and **Expense Account** (`property_account_income_id`, `property_account_expense_id`), relations to Chart of Accounts with the placeholder "From Category" and no default, on a new tab **Accounting** after Inventory — bundle 2, `09-chart-of-accounts.md`.

### Form layout

| Odoo 19.4 | Nocoly |
|---|---|
| Button box: Variants · Documents · Sold | **# Variants** beside Active — Odoo's Variants count (21 Sep 2026); Documents and Sold see *Not built now* |
| Header: ☆ Name; Sales ☑ Purchase ☑ under it; image on the right | Name, full width · Favorite \| Sales \| Purchase · Image |
| Tab General Information — left: Product Type (radio), and fields of Sales, Inventory and e-invoicing; right: Sales Price per Unit · Sales Taxes · Cost per Unit · Purchase Taxes · Category · Reference · Barcode · Tags · tariff code; then Internal Notes | Product Type \| Sales Price · Unit \| Cost · Internal Reference · Internal Notes |
| Tab Attributes & Variants | — |
| Tab Sales, hidden unless Sales — *Upsell & Cross-Sell*: Packagings, Optional Products; *Short Description*: Sales Description; *Expenses, Services & Materials*: Re-Invoice Costs | Packagings · Sales Description; the whole tab hidden when Sales is unchecked |
| Tab Prices | — |
| Tab Purchase (`invisible="1 or …"`: never shown on the tenant) | — |
| Tab Inventory, hidden for services — *Logistics*: Weight kg, Volume m³, Delivery Time | Weight \| Volume; the whole tab hidden when Product Type is Service |

A HAP form is a 12-column grid, so Odoo's two columns become paired rows, and the Unit that Odoo repeats after
"Sales Price … per" and "Cost … per" is one field beside Cost. HAP has no avatar slot or favourite star: Image is
a full-width field and Favorite a checkbox. Group titles inside the tabs are left out: the Sales and Inventory tabs
hold two fields each.

### Rules

| Rule | Type | When | Effect | Odoo source |
|---|---|---|---|---|
| Sales tab only for products that can be sold | interaction | Sales is unchecked | hide the **Sales** tab | `<page name="sales" invisible="not sale_ok">` |
| Inventory tab only for goods | interaction | Product Type = Service | hide the **Inventory** tab | `<page name="inventory" invisible="type in ['service', 'combo']">` |
| Cost cannot be negative | validation — **form only** | Cost < 0 | "The cost of a product can't be negative." on Cost, as you type | `@api.onchange('standard_price')` `_onchange_standard_price` (`product_template.py:417`). An onchange: Odoo checks it in the form and not on API writes, and so does this rule |

Name, Product Type and Unit are required on the fields themselves. The two picker restrictions are in Fields.

### Buttons (Odoo ⚙ Actions)

| Button | Shown when | Does | Confirmation |
|---|---|---|---|
| Archive | Active is checked | Active → unchecked | "Are you sure that you want to archive this record?" · Archive / Cancel |
| Unarchive | Active is unchecked | Active → checked | none |

As on Contacts and Units & Packagings, the button that does not apply is greyed out rather than hidden.

### Views

| View | Type | Shows | Odoo 19.4 |
|---|---|---|---|
| Products | gallery — opens first | Active products. Image cover; title Name; Internal Reference, Sales Price, Unit. Favourites first, then Name A→Z | Kanban, the first view of the Products action (`kanban,list,form`): image, name, favourite star, variant count, Sales Price, Cost, Internal Reference, properties, On Hand with its unit |
| List | table | Active products. Columns Name · Internal Reference · Sales Price · Cost · Unit; quick filters Product Type · Sales · Purchase · Favorite; same sort | List view: favourite star · Product Name · Internal Reference · Sales Price · Cost · On Hand · Free To Use · Forecasted · Unit. Search filters Goods · Services · Combo, Favorites, Sales · Purchase |
| Archived | table | Archived products, List's columns and sort | The *Archived* filter |

Odoo's model order is `is_favorite desc, name`. Search is on the title and text fields, HAP's search box.

### Automations

None.

### Not built now, and why

| Odoo 19.4 field / feature | Why not now |
|---|---|
| ~~Product Category (`categ_id`)~~ | **Built on 16 Sep 2026 by the Product Categories bundle** — a Category relation on General Information between Cost and Internal Reference, and a quick filter on the Products and List views. See `worksheets/08-product-categories.md` |
| Tags (`product_tag_ids`) | Product Tags bundle — excluded |
| Sales Taxes, Purchase Taxes (`taxes_id`, `supplier_taxes_id`, `tax_string`) | Taxes bundle; module `account` |
| ~~Income and Expense Accounts (`property_account_income_id`, `property_account_expense_id`)~~, Account Tags (`account_tag_ids`) | **The two accounts were built on 17 Sep 2026 by the Chart of Accounts bundle** — a tab Accounting after Inventory; see `worksheets/09-chart-of-accounts.md`. Account Tags are not among the six bundles |
| Product Type **Combo**, Combo Choices (`combo_ids`) and the checks "A combo product must contain at least 1 combo choice." and "A sellable combo product can only contain sellable products." | Product Combos bundle; module `product` |
| Attributes & Variants tab (`attribute_line_ids`) | Product Variants bundle; module `product` |
| ~~the Variants smart button~~ | **Built 21 Sep 2026**, not deferred after all. This row sent it to worksheet 04, which then declined to give Products a reverse field, and it fell between the two. Products now carries **Variants** (the reverse of `product_tmpl_id`, drawn as a tab at the foot) and **# Variants** (`product_variant_count`, a 汇总 count beside Active) — see `04-product-variants.md` › *The reverse on Products*. Both are **read-only and hidden on create** (`fieldPermission` "100"): they were "101" for a few hours and the screen pass caught both rendering on the Create Record form, where Odoo's smart button does not exist yet (`15-ui-conformance.md` §6.3). "011" would have taken their table columns with them. Written by `products.py perms`, a version-pinned save of those two controls alone — **`products.py layout` must not be run**, its places and views predate another administrator's changes of 17 Sep and would revert them (§2) |
| Barcode (`barcode`) | Stored on the variant: worksheet 04 Product Variants |
| Prices tab (`fixed_pricelist_rule_ids`, `pricelist_rule_ids`) | Pricelists bundle; module `product` |
| Vendors (`seller_ids`), Purchase Description (`description_purchase`), the Purchase tab | Purchase — not installed on the tenant, whose form never shows that tab |
| Invoicing Policy (`invoice_policy`), Create on Order (`service_tracking`), Service Invoicing Policy (`service_policy`), Track Service, Project and Task Templates, Re-Invoice Costs, Optional Products, Sales Order Line Warning, Delivery Time (`sale_delay`), the Sold smart button | Sales (`sale`, `sale_project`) and Project — appended as bridge fields when those apps land |
| Track Inventory (`is_storable`), On Hand, Forecasted, Incoming, Outgoing, Free To Use | Inventory (`stock`) is not installed; the tenant shows them inert |
| Documents (`product_document_ids`) smart button | HAP's record attachments and discussion |
| Properties (`product_properties`) | Odoo's ad-hoc fields, defined per category; in HAP an admin adds a field |
| Price per unit (`base_unit_count`, `base_unit_id`, `base_unit_price`) | eCommerce (`website_sale` in 19.0); not on the tenant's form |
| Malaysian Customs Tariff Code / Service Type Code, Malaysian classification code | Malaysian e-invoicing localisation (`l10n_my`, `l10n_my_edi`), with Invoicing — as SST and TTx on Contacts |
| Company (`company_id`) | One company per app copy; multi-company is not in Phase 1 |
| Sequence, Color Index, Currency, Cost Currency, Unit Name | Technical fields, not on the form: nothing orders by Sequence, the currency is fixed to MYR on the two Currency fields, and the Unit relation shows its name |
| Display name "[Internal Reference] Name" in pickers (`_compute_display_name`) | Pickers show the Name. Order and invoice lines will pick a Product Variant, whose display name is decided with worksheet 04 |
| "The Internal Reference '…' already exists." (`_onchange_default_code`) | A warning, not a refusal: HAP has no warning-only rule, and a field's No-duplicates setting would refuse the save |
| "What to expect ?" when the Unit changes, and the conversion of existing lines (`_onchange_uom_id`, `write` → `_update_uom`) | Only matters once the product is on order or invoice lines — worksheet 07 |
| Archiving a product archives its variants (`write`) | Product Variants (04) |
| A duplicated product is named "… (copy)" (`copy_data`) | HAP's duplicate keeps the name |
| "Labels cannot be printed for products of service type" | No label printing |
| ~~Roles~~ | **Set on 16 Sep 2026** for the whole app, at the end of Phase 1: five stock roles renamed to English and four business roles, one per Odoo accounting group, each with a rule for this worksheet. The table is in `REVIEWING.md` › *Phase 1 · Roles* |

### Records

The 14 products of the extract, all active and none favourite: Name, Internal Reference, Product Type, Sales,
Purchase, Sales Price, Cost, Unit (Units, Hours or Days, from Units & Packagings) and Sales Description; Weight and
Volume 0, as on the tenant. The Ergonomic Office Chair's internal note — a stray pasted code snippet — is not
copied. The monitor, chair and desk have 2, 3 and 2 active variants on the tenant, plus each one's archived original
variant (hence no Internal Reference and a Cost of 0 on the product); their variants wait for Product Variants.

## 2 · Build

Built by `nocoly/build/products.py` — steps `create → fields → relations → layout → rules → views → buttons → seed`,
each safe to re-run (`fields` refuses to run on a worksheet that already has its fields); helpers shared with other
worksheets are in `nocoly/build/common.py`; every id is in `nocoly/build/ids.json` under "Products: …" (the
worksheet under "Products"). `products.py verify` compares the live products with the 19.4 extract;
`products.py order` prints each view's records in the view's order; `products.py product <name>` prints a
product's stored values, hidden ones included.

| Element | Built | Id |
|---|---|---|
| App | ERP Master | `6cb4d051-a33c-4bf9-b56f-5f47f0e85dc9` |
| Menu group | Products — Products first, then Units & Packagings | `6aa8d12ddb26b712423d345d` |
| Worksheet | Products, alias `product_template` | `6aa8ea0c4a22ad87b728cf0b` |
| Controls | 19: the 16 fields above (aliases are Odoo field names) and 3 tabs | — |
| Relations | Unit · Packagings, one-way to Units & Packagings | `6aa8ea304720c515252be609` · `6aa8ea304720c515252be60b` |
| Rules | the 3 above | `6aa8ea9cf363582dd37a5ab0` · `6aa8ea9cf363582dd37a5ab2` · `6aa8ea9e4a73a3142152d722` |
| Views | Products · List · Archived | `6aa8eadd1204328eb1af105b` · `6aa8ea0c4a22ad87b728cf0f` · `6aa8eadf1204328eb1af105d` |
| Buttons | Archive · Unarchive | `6aa8eb444720c515252be61c` · `6aa8eb484720c515252be61e` |
| Button workflows | one step each, setting Active | `6aa8eb452fe3e8d6b31a6da2` · `6aa8eb482fe3e8d6b31a6dc6` |
| Records | the 14 products; `verify` matches all 14 | — |

**Favorite deleted by another administrator, and restored with a new id — 17 Sep 2026.** Teh Li Wei deleted Favorite
(`6aa8ea161204328eb1af1013`) in the form designer at 16:11 on 17 Sep. At the owner's request ("Add the favourite
back") it was re-created at 22:26 with a **new id, `6aabf880e43d174ab374dcf0`**: the same name, checkbox, alias
`is_favorite`, default unchecked, permission "111" and no description, back on row 1 as **Favorite (4) | Sales (4) |
Purchase (4)**. It went in with one full save pinned to the controls' version (`common.save_controls(…, version=…)`),
read immediately before it after the app log showed no other operator active since 16:57; every other control read
back identical key by key, Sales and Purchase changed only col and size, and the other eight worksheets were
identical. `products.py` was **not** run — its layout and views predate his changes and would revert them. His other
changes stay as he made them: Name No duplicates, Product Type's option **Combo**, Purchase no longer ticked by
default, Active moved to row 3 (the tabs and their fields one row down), a Number **Delivery Time** on Inventory
(16:46), the rule *Interaction Rule 3* (Purchase hidden for Combo), and his Units & Packagings changes. **Re-pointed
from the old id to the new one:** the Products, List and Archived views' sort (Favorite descending, then Name) and
List's quick filters (Product Type · Sales · Purchase · Favorite · Category); Product Variants' automations A, B (its
copy step and its trigger fields) and C — see 04 §2. `payterms.py deadrefs 6aa8ea161204328eb1af1013` then found no
reference in the views, rules, buttons and controls of 11 worksheets or in 30 workflows (354 nodes). All 18 products
were written unchecked, as every variant was (no variant said otherwise). `products.py verify`: 0 missing or
differing. `ids.json`: `Products: Favorite` holds the new id, the old one is kept under `Products: Favorite (deleted
by another admin 17 Sep 2026)`. **The deleted control is still in Products' field recycle bin — do not restore it**:
the form would carry two Favorite checkboxes with one alias (`BUILDING.md`). Backups:
`backups/favorite_products_*_20260917-22*.json`.

**History.** Built and seeded on 15 Sep 2026 in one pass; nothing was left behind and there is nothing to delete.
Self-checks through the CLI: Units & Packagings' controls, rules, buttons and views read back unchanged after every
save; Whiteboard Marker Set was marked Favorite (it moved to the top of Products and List) and back, and archived
and unarchived once with `workflow trigger` (it moved to Archived and back). The Unit default, the two pickers, the
tab rules, the negative-Cost check and the currency display are browser behaviour: HAP stores them as configured,
and only the UI test can show them working.

### Found while building — applies to every worksheet

- `hap worksheet view sort` sends no appId: SortWorksheetViews answers `false` and changes nothing. The same call
  with the appId works (`common.sort_views`).
- A **one-way Relation** is added with `add-fields`, without a controlId and with `advancedSetting.bidirectional`
  "0" (hap-cli's own builder does this): the target worksheet gets no reverse control; the relation's
  `sourceControlId` is only a reserved id. After the full layout save on Products, `worksheet fields` listed
  Units & Packagings' controls in another order (by id), every attribute unchanged: compare controls by id, not by
  position.
- A **static Relation default** is `defsource [{"cid": "", "rcid": "", "staticValue": "[\"<rowid>\"]"}]`; the
  server stores the record's whole row in place of the rowid. The API applies no defaults, so only a new record in
  the form shows it.
- An interaction rule can hide a **whole tab**: its item names the tab (SECTION) control.
- A Relation's picker filters are applied by the browser — GetFilterRows for a picker ignores them — so they can
  only be checked in the UI. A filter can compare the record id with a Relation on the form
  (`controlId: "rowid"`, `dynamicSource: [{cid: <relation>}]`); an empty dynamic value drops that condition.
- `worksheet record list --view-id` applies the view's filter and sort, and returns only that view's columns.
- A Currency field's symbol is `advancedSetting.currency` = `{"currencycode": "MYR", "symbol": "RM"}`.

## 3 · Test list

Run in the Nocoly UI in Chrome on 15 Sep 2026; stored values read back with
`~/.hap-venv/bin/python nocoly/build/products.py product "<Name>"` from the repo root. Test records are named `TEST …`.

| # | Check | Steps | Expected | Result |
|---|---|---|---|---|
| 1 | Menu | Open ERP Master | Menu group **Products** holds Products, then Units & Packagings. Products opens on the **Products** gallery; its views are Products · List · Archived | **Pass** — HAP reopens the view you last used; opened fresh, the worksheet starts on the gallery |
| 2 | Empty form and defaults | Products → + Record, look | Name (placeholder "e.g. Cheese Burger"); Favorite unchecked, Sales and Purchase checked; Image. Tab General Information: Product Type **Goods**, Sales Price **RM 1.00**, Unit **Units**, Cost **RM 0.00**, Internal Reference, Internal Notes (placeholder "This note is only for internal purposes."). Tabs Sales and Inventory shown; Weight 0.00 kg, Volume 0.00 m³. No Active field | **Partly** — every field, default and tab as expected, with Odoo's help under the fields, but Internal Notes shows no placeholder, even when clicked into (difference 2). Sales Description shows its placeholder |
| 3 | Required fields | Clear Unit, leave Name empty → Submit | Name and Unit marked required; not saved | **Pass** — "Please fill in Unit" as soon as Unit is cleared; Submit adds "Please fill in Name" and "Please fill in the record correctly" |
| 4 | Unit picker | Open Unit | Only active units — the 14 standard ones, e.g. Days showing 8 · Hours — plus any active TEST unit; no Dozens, cm or km | **Partly** — exactly 17: the 14 standard active units and the 3 TEST units; no Dozens, cm or km. Names only, without Contains and Reference Unit (difference 1); typing "Hours" also finds Minutes and Days |
| 5 | Packagings picker | Unit = Units; tab Sales → Packagings | Active units except Units; more than one can be picked. Change Unit to Hours: Units is offered, Hours is not | **Pass** — 16 units without Units; Pack of 6 and Days picked together; with Unit Hours, the 16 include Units and not Hours |
| 6 | Sales tab hides | Uncheck Sales; check it again | The Sales tab disappears, then comes back | **Pass** |
| 7 | Inventory tab hides | Product Type = Service; back to Goods | The Inventory tab disappears, then comes back | **Pass** |
| 8 | Negative cost | Cost −1 | "The cost of a product can't be negative." under Cost; Submit refused | **Pass** — shown as you type, beside Cost; Submit opens "Please correct form errors" with the same message |
| 9 | Save a product | Name "TEST Product", Internal Reference TEST-0001, Sales Price 1890, Cost 5.5, Packagings Pack of 6, Sales Description "TEST line", Weight 1.5 → Submit | Saved. Sales Price and Cost show the RM symbol and 2 decimals (5.50). CLI: code TEST-0001, type Goods, sale_ok and purchase_ok True, list_price 1890.00, standard_price 5.50, uom Units, active True, weight 1.50 | **Pass** — RM 1,890.00 and RM 5.50 in the form; CLI as expected, with packagings Pack of 6, description_sale "TEST line", volume 0.00 |
| 10 | One-way relations | Open a unit in Units & Packagings | No Products or Packagings field, and no new column in its views | **Pass** — Units shows Unit Name, Contains and Reference Unit only; both views keep their three columns; `units.py verify` still 0 differing |
| 11 | Views | Products, List, Archived | Products: cards with image, Name, Internal Reference, Sales Price, Unit. List: columns Name, Internal Reference, Sales Price, Cost, Unit. Both: the 14 products and TEST Product, sorted by Name (27" 4K Monitor first). Archived: empty | **Pass** — 15 cards and 15 rows; TEST Product between Steel Filing Cabinet 4-Drawer and Whiteboard Marker Set |
| 12 | Favourites first | Mark Whiteboard Marker Set Favorite; then unmark it | It moves to the top of Products and List, then back to its place by name, just before Wireless Keyboard & Mouse Set | **Pass** — after a refresh each time (difference 3); the change is stored with Save on the record's *Modifying form data* bar |
| 13 | Quick filters | List: Product Type = Service; then clear it and click Purchase twice (ticked, then unticked); then Favorite ticked | Service: Annual Support Retainer, Implementation Consulting, both Nocoly HAP Licences, Onsite Training (per day). Purchase unticked: the same five. Favorite ticked: none | **Pass** — Purchase ticked lists the 9 goods and TEST Product; Service with Purchase ticked lists none; Favorite ticked lists Whiteboard Marker Set while it is a favourite (difference 4) |
| 14 | Archive | Open TEST Product → Archive | Confirmation as above with Archive / Cancel; TEST Product leaves Products and List and appears in Archived; on the record, Archive is greyed out and Unarchive available | **Pass** — exact text; "Operation completed" and the record closes (difference 5) |
| 15 | Unarchive | Archived → TEST Product → Unarchive | No confirmation; back in Products and List | **Pass** — Archived empty again, List back to 15 |
| 16 | Seeded data | `~/.hap-venv/bin/python nocoly/build/products.py verify` | Every product OK; "14 in the extract; 0 missing or differing"; TEST Product listed as not in the extract | **Pass** — "14 in the extract; 0 missing or differing; 1 not in the extract ['TEST Product']" |
| 17 | Odoo side by side | casimir.odoo.com Products vs Nocoly | Same fields as §1 apart from the "Not built now" list; the same 14 products with their references, types, Sales and Purchase flags, prices, costs, units and sales descriptions | **Pass** — Sales › Products shows the same 14 in the same order, prices and references; the laptop's General Information, Sales and Inventory tabs hold §1's fields and the Not built now ones |

### Differences from Odoo seen in testing

1. **Unit and Packagings pickers list names only.** Odoo's unit dropdown hints each unit's ratio ("Days 8.0
   Hours"); HAP's dropdown shows the name. The search still reads Contains and Reference Unit: "Hours" finds Minutes
   and Days. The same as Units & Packagings, difference 1.
2. **Internal Notes has no placeholder.** HAP's rich-text editor never shows a field's hint; the text is stored on the
   field and shows nowhere. Odoo shows "This note is only for internal purposes." in the empty field.
3. **Favorite is a checkbox, not a star**, and an open record's changes are kept with Save on the *Modifying form
   data* bar. The open view re-sorts only after Refresh.
4. **Checkbox quick filters have two states once used.** Sales, Purchase and Favorite start unset; a click filters
   for ticked, the next for unticked — the box then looks empty but still filters. Reload the view to clear them.
   Odoo's Sales and Purchase filters are on or off.
5. **Archive and Unarchive.** The button that does not apply is greyed out rather than hidden, as on Contacts and
   Units & Packagings, and the record closes once it leaves the open view; Odoo keeps the form open with an
   *Archived* ribbon.

### Test records left in the worksheet

TEST Product — TEST-0001, Goods, Sales Price RM 1,890.00, Cost RM 5.50, Unit Units, Packagings Pack of 6, Sales
Description "TEST line", Weight 1.50 kg. Whiteboard Marker Set is back to not favourite. Remove TEST Product after
sign-off.

Added on 17 Sep 2026 by the Favorite restore's proof (§2, 04 §2): **TEST Favorite Restored** — TEST-0007, Goods, RM
7.00 / RM 3.00, Unit Units, not favourite, no Weight or Volume (created through the API, which applies no defaults),
rowid `3869dcc0-8b75-4e0a-b311-2d82f4e092a1`.


## Descriptions rewritten for the app's users (22 Sep 2026)

The owner's rule of 22 Sep 2026: a description in the app says only what the field or button does, for the people using it — no Odoo, no field or model names, no divergences, no build notes. The texts below were rewritten or emptied on the live app and in the builder's constants. The old text is kept here, word for word, because it carried the Odoo references and build reasoning that are no longer in the app.

| Control | Key | Before | After |
|---|---|---|---|
| Cost | desc | Value of the product (automatically computed in AVCO). Used to value the product when the purchase cost is not known (e.g. inventory adjustment). Used to compute margins on sale orders. | What this product costs the company. Used to value it and to work out margins. |
| Sales Description | desc | A description of the Product that you want to communicate to your customers. This description will be copied to every Sales Order, Delivery Order and Customer Invoice/Credit Note | A description of this product for your customers. |
| Active | desc | If unchecked, it will allow you to hide the product without removing it. | Untick to hide the product without deleting it. |
| Unit | desc | Default unit of measure used for all stock operations. | The unit this product is sold and counted in. |
| Variants | desc | The variants of this product. Odoo product_variant_ids — read-only here, as it is there: a variant says which product it belongs to. | The variants of this product. |
| Expense Account | desc | Keep this field empty to use the default value from the product category. If anglo-saxon accounting with automated valuation method is configured, the expense account on the product category will be used. | Keep this field empty to use the default value from the product category. |
| Sales Taxes | desc | Default taxes used when selling the product — Odoo taxes_id. The picker offers the taxes whose Tax Type is Sales, which is Odoo's own domain on the field. | Default taxes used when selling this product. |
| Purchase Taxes | desc | Default taxes used when buying the product — Odoo supplier_taxes_id. The picker offers the taxes whose Tax Type is Purchases. | Default taxes used when buying this product. |
| # Variants | desc | The number on Odoo's Variants smart button (product_variant_count). | The number of variants of this product. |
