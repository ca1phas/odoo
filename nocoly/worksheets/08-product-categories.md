# 08 · Product Categories

| | |
|---|---|
| Nocoly app | ERP Master · menu group **Products** |
| Worksheet | Product Categories |
| Odoo model | `product.category` |
| Reference | **casimir.odoo.com — Odoo saas~19.4+e**: fields by module, form, list, search, the window action, all 7 categories and the category of every product, extracted read-only to `nocoly/reference/odoo-19.4/product.category.md`. Behaviour the tenant cannot show — the recursive Complete Name, the product count, the recursion constraint, quick-create, duplicate naming — is read from the Odoo 19.0 source in this repo: `addons/product/models/product_category.py`, `addons/product/views/product_category_views.xml`, `addons/product/models/product_template.py` |
| Phase | 1 — **bundle 1 of 6** (Product Categories · Chart of Accounts · Payment Terms · Countries · States · Taxes) |
| Status | §1 written 16 Sep 2026 — not built yet |

The tree a catalogue hangs on: every product belongs to one category, and a category may sit under another.
Odoo uses it for reporting and — once the Chart of Accounts bundle lands — for the income and expense accounts a
product's invoice lines post to. This bundle adds the worksheet, gives **Products** the Category field it has never
had, and seeds the tenant's seven categories and all fourteen products' categories. **Nothing is replaced or
deleted:** Products carried no stand-in for a category, so there is no text field to carry across and remove.

## 1 · Requirements

### Fields

Labels are Odoo 19.4's; aliases are Odoo field names on `product.category`. "Hidden" means not on the form but
read by a formula, a view or a picker.

| # | Field | Odoo field | Nocoly type | Required | Default | Notes |
|---|---|---|---|---|---|---|
| 1 | Name | `name` | Text | yes | — | Placeholder "e.g. Lamps", Odoo's. Odoo's form heads it **Category**; the field is Name everywhere else |
| 2 | Complete Name | `complete_name` | Function formula, text · **title field** | — | — | "Goods / Consumables" — the parent's complete name, " / ", this name. **Read-only and hidden on create** (`fieldPermission` "100"), as 04's Display Name, so it stays a table column. Odoo's `_rec_name`, and what its list and every picker show |
| 3 | Parent Category | `parent_id` | Relation → Product Categories (single, **two-way**), dropdown | no | — | Odoo labels it **Parent**, placeholder "None". The picker lists every category by Complete Name and **allows adding one from the picker** (Odoo `can_create="True"` and `name_create`). A single relation to its own worksheet comes back two-way in HAP, which is what field 4 is |
| 4 | Child Categories | `child_id` | Relation → Product Categories (multiple) — the reverse of 3 | — | — | **Read-only**: it is maintained by the children. Odoo has the field and puts it on no view; here it is worth showing, because it is the tree |
| 5 | Products | — (reverse of `product.template.categ_id`) | Relation → Products (multiple) — the reverse of the new Category on Products | — | — | **Read-only**: set the category on the product. This is Odoo's *Products* stat button, as a list rather than a count-and-jump |
| 6 | # Products | `product_count` | 汇总 roll-up over field 5, count | — | — | **Read-only.** The number on Odoo's stat button. It counts the products **in this category**, not in its children — see the note below |
| — | Parent Complete Name | — | Lookup through Parent Category of the parent's **Complete Name** | — | — | Hidden; field 2 is built on it. Not an Odoo field: Odoo computes `complete_name` recursively in Python, and HAP does the same thing with a stored lookup that chains, as Units & Packagings' Absolute Quantity already does up a unit chain |

**# Products counts this category's own products.** Odoo's help says exactly that — *"Does not consider the
children categories"* — but `_compute_product_count` reads `('categ_id', 'child_of', self.ids)`, so Odoo's number
is the whole subtree: on the tenant, Goods holds no product of its own and shows **11**, the total of its four
children. A HAP roll-up aggregates one relation, not a subtree, so ours shows **0** for Goods. We build what
Odoo's help promises; §3 records the difference, and the Child Categories list is right beside it.

**There is no Active field, so there are no Archive and Unarchive buttons.** `product.category` is the first model
in this app with no `active` — Odoo's only way to remove a category is to delete it. Every other worksheet's pair
of buttons and its *Archived* view are deliberately absent here, not forgotten.

### Form layout

| Odoo 19.4 | Nocoly |
|---|---|
| Button box: **# Products** → the products in this category | # Products, read-only, beside the parent · and the Products list itself |
| Title: label "Category", `name` as the h1 | Name, full width |
| Group *first*: Parent (inline, placeholder "None") | Parent Category \| Complete Name |
| — | Child Categories \| # Products |
| — | Products |
| Chatter | HAP's record discussion |

| Row | Left (6) | Right (6) |
|---|---|---|
| 1 | **Name** (full width, 12) | |
| 2 | Parent Category | Complete Name — read-only, hidden on create |
| 3 | Child Categories — read-only | # Products — read-only |
| 4 | **Products** (full width, 12) — read-only | |

### Rules

None. Name is required on the field itself.

**Odoo's one constraint is not built:** `_check_category_recursion` raises *"You cannot create recursive
categories."* A HAP rule compares a control with a value or another control — it cannot ask whether a record is
its own ancestor, and the Parent Category picker will offer the record itself. §3 tests what HAP actually does
when a category is made its own parent (test 12) and when two categories point at each other (test 13); if the
result is ugly the owner decides whether it is worth a workflow.

### Buttons

None — see the note under Fields.

### Views

| View | Type | Shows | Odoo 19.4 |
|---|---|---|---|
| Categories | table — the only view | Every category. Columns **Complete Name · Parent Category · # Products**; sorted Complete Name A→Z, which reads as an indented tree (Goods, then Goods / Consumables). Quick filter Parent Category | The Categories action's single list view, one column — `display_name`, which *is* the complete name. Its search view offers Name and Parent Category and has no filters and no group-by |

Odoo's model order is `_order = 'complete_name'`; on the tenant `complete_name` is no longer stored, so it cannot
be sorted on there at all (`order='complete_name'` answers *"Cannot convert product.category.complete_name to SQL
because it is not stored"*) and the tenant returns roots first, then each parent's children by name. HAP stores its
formula, so **our sort is the one Odoo's source asks for**. If HAP refuses to sort a table on a function formula,
sort on Name A→Z instead and say so.

### Automations

None. Complete Name, Parent Complete Name and # Products are a formula, a lookup and a roll-up — the platform
keeps all three current.

### What this bundle changes on Products (03)

| Change | Detail |
|---|---|
| New field **Category** (`categ_id`) | Relation → Product Categories (single, **two-way** — its reverse is field 5 above), not required, no default. Tab **General Information**, between Cost and Internal Reference, which is where Odoo's form puts it (right column: Sales Price · Sales Taxes · Cost · Purchase Taxes · **Category** · Reference). The picker lists every category by Complete Name and allows adding one |
| Views | A **Category quick filter** on the *Products* and *List* views. **No new column:** Odoo's list carries `categ_id` as `optional="hide"`, off until the user switches it on, and HAP has no optional column — so adding one would show more than Odoo does |
| *Not built now* | The row "Product Category (`categ_id`) — Product Categories bundle, excluded for now" is replaced by a line pointing at this worksheet |
| Deleted | **Nothing.** Products never had a stand-in for the category |

Odoo's `categ_id` is **not required** and has no default on this tenant — `default_get` returns nothing for it, so
a new product starts with no category. Ours does the same.

### Roles

Product Categories joins the four business roles in `build/roles.py` with **the same rule Products has**:
Accounting Administrator *full*; Accountant, Invoicing and Accounting Read-only *view*. The table in
`REVIEWING.md` › *Phase 1 · Roles* gains a column.

### Not built now, and why

| Odoo 19.4 field / feature | Why not now |
|---|---|
| Income Account, Expense Account (`property_account_income_categ_id`, `property_account_expense_categ_id`) | **Chart of Accounts bundle — bundle 2, immediately after this one.** They are `account.account` relations, company-dependent in Odoo; this worksheet gains two relations when it lands. Whoever builds bundle 2 must come back here |
| Product Properties (`product_properties_definition`) and the products' `product_properties` | Odoo's ad-hoc fields, defined per category; in HAP an admin adds a field to the worksheet. Same reason 03 gives |
| Company (`company_id`) | One company per app copy; multi-company is not in Phase 1 |
| Parent Path (`parent_path`) | Technical — Odoo's `_parent_store` index. HAP's lookup chain does the same work |
| Category on **Product Variants** (04) | Odoo's variant form carries `categ_id` invisible (`product_product_view_form_normalized`) and its list hides it; the category belongs to the product. A one-field lookup if the reviewer wants it |
| The recursion constraint | Above, under Rules |
| Deleting a parent deletes its children (`ondelete='cascade'`) | HAP does not cascade a relation, and **no deletion happens without the owner's approval** in this app anyway |
| A duplicate named "… (copy)" (`copy_data`) | HAP's duplicate keeps the name, as on 03 |
| `hierarchical_naming=False` — the bare name in some pickers | Every picker here shows the Complete Name, which is Odoo's default |
| Chatter, followers, activities (`mail.thread`) | HAP's record discussion and attachments |
| The stat button's jump to a filtered product list | The Products relation on the form *is* the list, and the Category quick filter on Products is the same search |
| `group_expand` on Odoo's kanban — empty category columns stay visible | HAP's grouping has no equivalent switch; a category with no products simply has none |

### Records

Seed the tenant's seven categories, parents before children, then set every product's Category from the extract.

| Name | Parent | Complete Name should read | Products |
|---|---|---|---|
| Expenses | — | Expenses | — |
| Goods | — | Goods | — |
| Services | — | Services | Annual Support Retainer · Implementation Consulting · Onsite Training (per day) |
| Consumables | Goods | Goods / Consumables | A4 Copy Paper (Box of 5 reams) · Whiteboard Marker Set |
| IT Equipment | Goods | Goods / IT Equipment | 27" 4K Monitor · Business Laptop 14" i7 · Docking Station USB-C · Wireless Keyboard & Mouse Set |
| Office Furniture | Goods | Goods / Office Furniture | Ergonomic Office Chair · Height-Adjustable Desk 140cm · Steel Filing Cabinet 4-Drawer |
| Software | Goods | Goods / Software | Nocoly HAP Licence — Pro · Nocoly HAP Licence — Standard |

Fourteen products, all of them categorised — the tenant leaves none blank. After seeding, **# Products** should
read 3 on Services, 2 · 4 · 3 · 2 on Goods' four children, and **0** on Goods and Expenses (Odoo shows 11 on
Goods; see the note under Fields). No `TEST …` record is needed to seed; the test list adds its own.
