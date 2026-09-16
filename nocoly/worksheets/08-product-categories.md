# 08 · Product Categories

| | |
|---|---|
| Nocoly app | ERP Master · menu group **Products** |
| Worksheet | Product Categories |
| Odoo model | `product.category` |
| Reference | **casimir.odoo.com — Odoo saas~19.4+e**: fields by module, form, list, search, the window action, all 7 categories and the category of every product, extracted read-only to `nocoly/reference/odoo-19.4/product.category.md`. Behaviour the tenant cannot show — the recursive Complete Name, the product count, the recursion constraint, quick-create, duplicate naming — is read from the Odoo 19.0 source in this repo: `addons/product/models/product_category.py`, `addons/product/views/product_category_views.xml`, `addons/product/models/product_template.py` |
| Phase | 1 — **bundle 1 of 6** (Product Categories · Chart of Accounts · Payment Terms · Countries · States · Taxes) |
| Status | §1 written 16 Sep 2026; **built and self-checked 16 Sep 2026** (`build/prodcat.py`), not yet UI-tested |

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

## 2 · Build

Built by `nocoly/build/prodcat.py` — steps `create → fields → products → computed → layout → views → roles →
seed`, or `all` for every one of them followed by `check`. Each step reads the live state first, refuses to run
unless the profile reaches ERP Master › Products › Product Categories and the worksheet holds only this
script's own work, reads back what it wrote, and is safe to re-run: a second `all` created nothing, added
nothing, renamed nothing, wrote no record and changed no role. Helpers: `check` reads the controls,
permissions, formula, lookup, roll-up, view and Products' Category back against this spec, `verify` compares
the seven categories and all fourteen products' categories with the 19.4 extract (**# Products** included),
`selfcheck` drives the recursion chain and the roll-up end to end through the CLI, `order` prints the view's
records in the view's own order, `category "<Name>"` one category's stored values with the hidden fields,
`untouched` every other worksheet's control count and digest, and `show` the control list. The profile comes
from `$HAP_PROFILE` and otherwise from hap-cli's active profile; **nothing in `common.py` changed**.

| Element | Built | Id |
|---|---|---|
| App | ERP Master | `6cb4d051-a33c-4bf9-b56f-5f47f0e85dc9` |
| Menu group | Products — Products, Product Variants, Units & Packagings, **Product Categories** (last) | `6aa8d12ddb26b712423d345d` |
| Worksheet | Product Categories, alias **`product_category`**, icon `sys_8_4_folder` | `6aaa60e17d58b0f44930f052` |
| Controls | 7, all fields; no tab, no divider, no remark block | — |
| Fields, own | Name (required, "e.g. Lamps") · Parent Category (single, two-way) | `6aaa60e17d58b0f44930f053` · `6aaa62f67d58b0f44930f094` |
| | Complete Name — function formula (type 53), text, **the title**, `fieldPermission` "100" | `6aaa6336805aef7032866545` |
| | Parent Complete Name — stored lookup (type 30) through Parent Category, hidden ("011") | `6aaa633b805aef703286654d` |
| | # Products — 汇总 (type **37**), count over Products, read-only ("101") | `6aaa6340805aef7032866556` |
| Fields, the two reverses | Child Categories (the reverse of Parent Category) · Products (the reverse of Category on Products) — both multiple, read-only ("101") | `6aaa62f67d58b0f44930f095` · `6aaa612ee43d174ab374a1e6` |
| On **Products** | the new **Category** control (`categ_id`), single two-way Relation, tab General Information | `6aaa612ee43d174ab374a1e5` |
| View | Categories (the stock *All* view, renamed) — the only view | `6aaa60e17d58b0f44930f056` |
| Rules · Buttons · Workflows | **none**, as §1 says | — |
| Records | the tenant's 7 categories, all 14 products categorised, and one `TEST Category` (§3) | — |

Every id is in `nocoly/build/ids.json` under "Product Categories: …" keys — the seven controls, the view, the
seven category records and `TEST Category` — plus `"Products: Category"` for the control added to Products and
`"Product Categories"` under `worksheets`; no existing key was renamed.

`product.category` has **no `active` field**, so — as §1 says — there is no Active checkbox, no *Archived*
view and no Archive / Unarchive buttons. There are no rules and no workflows either: Complete Name, Parent
Complete Name and # Products are a formula, a lookup and a roll-up, and the platform keeps all three current.

### The recursion, and the roll-up

**Complete Name is Odoo's recursive `complete_name`, and it recurses.** The chain is
`Complete Name` (a text function formula) ← `Parent Complete Name` (a **stored** lookup, `strDefault` "00")
← the parent record's own `Complete Name`. §1 warned that HAP might refuse a lookup of a function formula on
the same worksheet and offered a one-level fallback: **it does not refuse**, the fallback was not needed, and
the expression is §1's, character for character:

```
IF(ISBLANK($Parent Complete Name$),TRIM($Name$),CONCAT($Parent Complete Name$," / ",TRIM($Name$)))
```

It was proved three levels deep, one deeper than the tenant goes — `TEST Category` under Consumables reads
**Goods / Consumables / TEST Category** — and a rename at the top carries all the way down (below).

**# Products is HAP's own 汇总, control type 37** — the first one in this app. hap-cli *does* have a builder for
it (`hap_cli.core.app_creator.fields.rollup_control`), so no raw control JSON was needed: `dataSource` is
`$<the Products relation>$`, `enumDefault` **6** is count, and `dot` 0 keeps it an integer. A count still has to
name a column on the other worksheet — Products' own **Name** is the one used. It counts **the products in this
category**, not the subtree, exactly as Odoo's help promises and §1 asks; the tenant's own numbers come out as
§1 predicted: Services 3, IT Equipment 4, Office Furniture 3, Consumables 2, Software 2, and **0 on Goods**
(Odoo shows 11) and Expenses.

### What changed on Products, and the one thing §1 did not get

| Change | Detail |
|---|---|
| One control added: **Category** `6aaa612ee43d174ab374a1e5` — type 29, alias `categ_id`, single, two-way, not required, no default, `showtype` "3" (dropdown), inside the tab *General Information* | §1. Added with `add-fields`; the other nineteen controls were compared id by id before and after every call — name, type, alias, row, col, size, tab, required, title, unique, `fieldPermission`, `dataSource`, `sourceControlId`, `showControls`, `advancedSetting`, description and hint — and none of them moved, nor did anything on Contacts, Units & Packagings, Product Variants, Journals, Invoices or Invoice Lines |
| A **Category quick filter** on the *Products* and *List* views | `advancedSetting` `allowitem` "2" (any of) and `direction` "2" (a dropdown). Only `fastFilters` was sent (`--edit-attrs fastFilters`), so each view's own filter, sort and columns were not rewritten — the List view's four existing quick filters are still there, in order, with Category appended |
| **No column** on either view | §1: Odoo's list carries `categ_id` as `optional="hide"` |
| Fourteen product records given their Category | §1's table, read back one by one. Each of those writes fires 04's product → variant workflows (a Products record update is their trigger); they copied the same Internal Reference, Cost, Weight and Volume the variants already had, and `variants.py verify` still reads **0 whose own variant differs or is missing**, `products.py verify` **0 missing or differing** |
| `nocoly/build/products.py`: `PLACE` gained `'Category': (6, 0, 6, GENERAL)` and moved `'Internal Reference'` to `(6, 1)` | 03 owns the Products layout and its `layout` step reads `PLACE[name]` for every control, so without the entry a re-run would stop with `KeyError: 'Category'`. Re-running that step is what put Category where §1 asks — below |

**Where Category sits on the form, and the two calls that decide it.** §1 asks for it between Cost and
Internal Reference. `add-fields` cannot put it there, and the reason is worth keeping:

- HAP has exactly two ways to write controls. `add-fields` (`AddWorksheetControls`) **appends** and **parks
  whatever it adds at row 9999, col 0**, ignoring the row and col in the payload (it does keep `size` and
  `sectionId`); `update-fields` (`SaveWorksheetControls`) replaces the whole control set. There is no
  "update one field" call — hap-cli's own editor `field update` and `field reorder` both go through the full
  save.
- So the control was added by `prodcat fields` and **placed by `products.py layout`**, which is 03's own
  read-modify-write step: it reads the live control list, moves the rows it owns, and sends back the same
  list. That is the sanctioned way to touch a live worksheet (`BUILDING.md`: *use it only on a worksheet with
  no records, or send back the full list you just read*), and it is how every other Products field got its
  place. The step reported all twenty controls and `check_units_untouched` passed.

The form now reads **Unit | Cost · Category | Internal Reference · Internal Notes**, which is Odoo's own right
column (Sales Price · Sales Taxes · Cost · Purchase Taxes · **Category** · Reference), and `prodcat check`
expects `(6, 0, 6)`. A control's row and col are form layout only: the picker, the values, the quick filters
and the roll-up behind it were already as §1 asked before the move.

**Each of the two relation lists needed its columns naming.** A list-style Relation (`showtype` "2") renders as
a **tab at the foot of the record**, not as a field in the form grid — so Child Categories and Products are
tabs under # Products rather than rows 2 and 3 of §1's layout table. Worse, a list with no `showControls`
shows its row count over the words ***No visible fields***: Goods' Child Categories tab said "Total 4 row(s)"
and showed nothing. `prodcat.LIST_COLUMNS` now names them — Child Categories shows **Complete Name · #
Products**, the Products list **Name · Internal Reference** — and `layout` owns them like any other attribute,
so `check` reads them back.

### Roles

`build/roles.py` now carries Product Categories: it is in `ORDER` (after Product Variants) and in all four
matrices with **the same rule Products has** — Accounting Administrator *full*, Accountant · Invoicing ·
Accounting Read-only *view*. `roles.py check` reads back OK, and the stock roles, the members and every other
worksheet's scope are untouched.

Two things had to be learned to get there, both now in `BUILDING.md`:

- **HAP adds a new worksheet to every fine-grained role by itself**, at its own defaults — `readLevel` /
  `editLevel` / `removeLevel` **20** (own records only), no create, and **every switch on, export included**.
  That is neither the owner's table nor hap-cli's defaults, and it would have given all four roles import,
  export, sharing, batch operations and printing on this one worksheet.
- **A sheet entry whose views are all unreadable is dropped on save.** `EditAppRole` answered `1` and stored
  nothing at all for Product Categories until `views[].canRead` / `canEdit` / `canRemove` were set true in the
  same post — which is what every other sheet in these roles carries (the record scope is the gate, not the
  view list).

`roles.reconcile` now takes the role's matrix and brings each sheet's levels, create right, action switches and
view permissions up to it, as well as the description and the export right. It wrote **only** Product
Categories' entries — the seven existing sheets already matched, which is also a check that the shape it
enforces is the one the earlier build produced.

### The three things §1 left to the build

**1 · A table sorts on a function formula.** §1 said to fall back to Name A→Z if HAP refused to sort the
Categories view on Complete Name. It does not refuse: `sortCid` is Complete Name, `sortType` 2, and
`record list --view-id` returns Expenses · Goods · Goods / Consumables · Goods / Consumables / TEST Category ·
Goods / IT Equipment · Goods / Office Furniture · Goods / Software · Services — Odoo's own `_order`, reading as
the indented tree the tenant cannot itself produce (its `complete_name` is not stored).

**2 · The aliases §1 could not take from Odoo.** `product.category` has no field for the products in a category
and none for the parent's complete name, so two aliases are this build's: **`product_ids`** for the Products
relation (Odoo has only the computed `product_count`) and **`parent_complete_name`** for the hidden lookup.
Everything else is Odoo's: `name`, `complete_name`, `parent_id`, `child_id`, `product_count`, `categ_id`.

**3 · Where the hidden lookup lives.** §1's layout table has four rows and does not place Parent Complete Name.
It is at row 4, hidden (`fieldPermission` "011"), under the four rows §1 draws.

### Self-checks through the CLI

`prodcat.py check` — controls, places, permissions, aliases, the title field, the formula expression, the
lookup's source, the roll-up's bridge and aggregate, the view's columns / sort / quick filter, the absence of
rules and buttons, and Products' Category with its two quick filters and no column:

```
check: OK — seven controls with their places and permissions, Complete Name the title and built on the lookup,
the roll-up over Products, the Categories view, and Products' Category with a quick filter on both its views
```

`prodcat.py verify` — every category against the extract (parent, Complete Name, # Products, the children and
products the two reverse relations hold), then every product's Category:

```
OK    Goods             parent=None      complete=Goods                      #products=0 children=4 products=0
OK    Expenses          parent=None      complete=Expenses                   #products=0 children=0 products=0
OK    Services          parent=None      complete=Services                   #products=3 children=0 products=3
OK    Office Furniture  parent=Goods     complete=Goods / Office Furniture   #products=3 children=0 products=3
OK    IT Equipment      parent=Goods     complete=Goods / IT Equipment       #products=4 children=0 products=4
OK    Software          parent=Goods     complete=Goods / Software           #products=2 children=0 products=2
OK    Consumables       parent=Goods     complete=Goods / Consumables        #products=2 children=1 products=2
7 categories in the extract; 0 missing or differing; 1 not in the extract ['TEST Category']
14 products in the extract; 0 with the wrong category {}; 4 of 18 products with no category
['TEST Auto Variant Product', 'TEST Favorite Product', 'TEST Product', 'TEST Variant From UI']
```

(The four products with no category are the `TEST …` products earlier bundles left behind. Odoo's `categ_id`
has no default, so a product that is never given one has none — which is also what the four of them prove.)

`prodcat.py selfcheck` — what §1 asks the platform to do, driven through the CLI on `TEST Category`:

```
1. three levels: TEST Category under Consumables reads 'Goods / Consumables / TEST Category'
   (lookup 'Goods / Consumables')
2. renaming Goods to 'TEST Goods' makes it 'TEST Goods / Consumables / TEST Category'
3. moving 'A4 Copy Paper (Box of 5 reams)' into TEST Category: # Products 1 there, 1 on Consumables
3. and back: # Products 0 on TEST Category, 2 on Consumables
4. TEST Category as its own parent: accepted; it now reads
   'Goods / Consumables / TEST Category / TEST Category'
   (parent 'Goods / Consumables / TEST Category / TEST Category')
4. put back under Consumables: 'Goods / Consumables / TEST Category'
selfcheck: OK — three levels, a rename down the chain, the roll-up both ways, and the recursion case recorded
```

Check 4 is **§1's test 12, answered**: HAP has no recursion constraint and the Parent Category picker will
offer the record itself, so a category *can* be made its own parent. What happens is not a loop and not an
error — the lookup reads the record's own last Complete Name once, so the name appears twice
("Goods / Consumables / TEST Category / TEST Category") and stops there. Putting the parent back restores it in
one save. Whether that is worth a workflow is the owner's call, as §1 says.

`prodcat.py untouched` — every other worksheet's control count and digest, compared id by id before and after
every save this build made:

```
Contacts             30 controls  sha256:9f7e59498c3081a1
Units & Packagings   10 controls  sha256:e57dc8775cd5038b
Product Variants     20 controls  sha256:6eba14458f20e2a6
Journals             15 controls  sha256:3d6313d3be876df3
Invoices             33 controls  sha256:93d1ebe3ec9b2766
Invoice Lines        13 controls  sha256:22b1e1b7f197b880
Products             20 controls  sha256:7a4d9c15f0da3ce1   (19 + Category)
```

`roles.py check` — `OK — five stock roles in English with their roleType and members, four business roles with
their per-worksheet scopes, export on Accounting Administrator alone, and no members`.

**Not checkable from the CLI, for the UI pass:** that the Parent Category picker offers *Add a category* (Odoo's
`can_create="True"`). The control carries HAP's default relation settings (`strDefault` "000", `allowlink` /
`allowedit` / `showquick` "1"), the same as every other relation in this app, but nothing in the stored control
names that switch, so only the browser can show it.

### Decisions taken while building

- **`sys_8_4_folder` for the sidebar icon** — a folder for a tree of categories. `hap icon search 文件夹` is how
  it was found; guessing icon names wastes time and leaves a broken image (below).
- **Both reverse relations are shown as a list** (`showtype` "2"), not as cards or a tab table: Child
  Categories at half width beside # Products, Products full width under them, both read-only.
- **The worksheet is last in the Products menu group** (after Units & Packagings). `worksheet create
  --section-id` appends, and §1 does not ask for a position; moving it is a sidebar drag if the owner wants it
  beside Products.
- **`TEST Category` is left in the worksheet**, a child of Consumables, with no products and no children. It is
  the evidence for the three-level chain and the roll-up above, and it is the third level nothing else has.
  Removing it after sign-off is one `record delete`.
- **Nothing was deleted.** One thing was created by mistake and removed the same minute: probing whether
  `add-fields` could place a control left a **duplicate entry of the Child reverse** on this worksheet (same
  controlId, twice). It was cleared with a full save that omits the id — which deletes both copies — and Parent
  Category was then re-created so the server could mint its reverse again. That is why Parent Category's id is
  `6aaa62f67d58b0f44930f094` and not the id its first save gave it. The worksheet had no records at the time
  and nothing else was touched; the finding is below and in `BUILDING.md`.

### Found while building

- **`worksheet add-fields` parks everything it adds at row 9999, col 0**, whatever `row` and `col` the payload
  carries; `size`, `sectionId` and every other attribute are kept. The note in `BUILDING.md` that "a new
  two-way Relation's reverse comes back at row 9999" is the general rule, not a quirk of reverses: that is
  where *anything* added this way lands. Only a full `update-fields` save can place a control — hap-cli's own
  editor ops `field update` and `field reorder` both go through `save_controls`, and there is no per-field
  endpoint.
- **`add-fields` given a control that already exists appends a second entry with the same `controlId`.** It
  does not update in place: `AddWorksheetControls` answered `{"code": 1}` and the worksheet then listed the
  control twice, with the same id and different sizes. A full save that sends that id once **updates both
  copies**; a full save that omits it **deletes both**. So a duplicate can only be cleared by deleting the
  control and re-creating it.
- **A two-way Relation added to another worksheet with `add-fields` gets no reverse control.** The server only
  **reserves** the id in the new control's `sourceControlId` and leaves it dangling — which is the "a
  `sourceControlId` can name a control that does not exist" note in `BUILDING.md`, seen from the other side.
  The reverse is then saved on the target worksheet by hand, carrying **that reserved controlId**, with
  `sourceControlId` = the forward control, `sourceControlType` **6** and `enumDefault` 2 — the same handshake
  `hap worksheet mount-subtable` performs for a 子表's back-relation. It pairs properly: setting Category on a
  product puts the product in that category's Products list, and the 汇总 over it counts.
- **A self-relation is the opposite, and mixing the two duplicates the control.** The server creates a
  self-relation's reverse itself, in the same `update-fields` save that creates the relation. Saving a reverse
  by hand for one — same reserved id — makes the server mint *its* reverse as well, and the worksheet ends up
  with two controls sharing a controlId (above). A re-save of the relation on its own does **not** bring a
  deleted reverse back; the relation has to be re-created.
- **`record list` returns only the default view's columns.** Every other field comes back as an empty string —
  not just hidden fields, as `BUILDING.md` had it: here `Name` came back empty from every row because the
  Categories view shows Complete Name, Parent Category and # Products. `record get` returns everything.
- **The reverse half of a two-way Relation reads back from `record get` as a row count** — an integer, not the
  rows — exactly as a 子表 does. The forward half returns the usual `[{"sid": …, "name": …}]`. So Goods'
  `child_id` is `4` and Consumables' `product_ids` is `2`.
- **A Relation cell carries the related record's *title*.** Here that is the Complete Name, so a seeded
  product's Category reads back as "Goods / IT Equipment", never "IT Equipment" — a verification that compares
  it with the category's Name fails on every child category and passes on every root.
- **HAP's 汇总 (type 37) has a hap-cli builder after all**:
  `hap_cli.core.app_creator.fields.rollup_control(name, via_control_id=…, source_control_id=…, aggregate=…)`,
  with `aggregate` mapping to `enumDefault` **1 avg · 2 max · 3 min · 5 sum · 6 count · 21 distinct count** and
  `dataSource` written as `$<the bridge relation>$`. A **count still needs a column on the target worksheet**
  named in `sourceControlId` (the title serves). Added with `add-fields` and then re-saved (as a formula must
  be), it computes immediately and follows a record moving in or out of the relation.
- **A stored lookup of a function formula on the same worksheet is allowed, and it chains.** Complete Name
  reads Parent Complete Name, which is a lookup of the parent's Complete Name; three levels deep it recomputes
  on a record save, in both directions, with no workflow and no `refresh` pass of the kind Units &
  Packagings needs.
- **A table view sorts on a function formula.** `sortCid` = a type 53 control, `sortType` 2, and the rows come
  back in the formula's own alphabetical order.
- **A quick filter can be added to a live view without rewriting it**:
  `view update --view-json '{"fastFilters": [ …the ones already there…, {"controlId": …, "advancedSetting":
  {"allowitem": "2", "direction": "2"}} ]}' --edit-attrs fastFilters`. `allowitem` is "1" single / "2" any of
  and `direction` "2" dropdown / "1" tiles.
- **`hap icon list` and `hap icon search <keyword>` are the icon catalogue** — 426 names, searchable in Chinese
  or English. A name outside it is not refused anywhere: the worksheet is created, and its icon URL simply
  answers HTTP 400 for ever. `hap worksheet update <ws> -a <app> --icon <name>` re-icons an existing worksheet
  and builds the Nocoly URL correctly, unlike `worksheet create`, which still needs `--icon-url`.
- **HAP adds a newly created worksheet to every fine-grained role on its own**, with its own defaults —
  `readLevel`/`editLevel`/`removeLevel` **20** (own records only), `canAdd` false, and **every action switch
  on**, `worksheetExport` included. A role built by `create-fine` before the worksheet existed therefore gains
  an entry nobody wrote, and it is the most permissive one in the role.
- **A role's sheet entry whose views are all unreadable is dropped on save, silently.** `EditAppRole` answers
  `1` and stores nothing — the levels, `canAdd` and the switches all read back unchanged — until
  `views[].canRead`, `canEdit` and `canRemove` are set true in the same post. That is what every existing sheet
  in these roles carries, and the record scope is what actually restricts them.

## 3 · Test list

Run on 16 September 2026 against the built worksheet, in the Nocoly UI where the UI is the point and through the
CLI where the question is whether HAP recomputes — every value read back with `hap worksheet record get`.
**16 of 18 pass, 1 in part, 1 with a caveat.**

| # | Test | How | Result |
|---|---|---|---|
| 1 | Create a category with no parent | UI, *New record* | **Pass.** `TEST UI root` saved; Complete Name reads back as the bare name |
| 2 | Give it the parent *Goods / IT Equipment* — three levels | CLI | **Pass.** Complete Name = "Goods / IT Equipment / TEST UI root". §1's fallback to the parent's Name was never needed |
| 3 | A child under that — four levels | CLI | **Pass.** "Goods / IT Equipment / TEST UI root / TEST UI child", two levels deeper than the tenant goes |
| 4 | Rename the middle category | CLI | **Pass.** Its own name and the child's both followed, in one save, with no workflow |
| 5 | Clear a parent | CLI | **Pass.** The category fell back to its bare name and the child to "TEST UI renamed / TEST UI child" |
| 6 | Complete Name on the create form | UI | **Pass.** Not on the create form at all; on a saved record it is read-only (`customFormReadonly`), as `fieldPermission` "100" asks |
| 7 | The Categories view order | UI | **Pass.** Expenses · Goods · Goods / Consumables · … · Services — the indented tree. A record just created sits at the **top** of the table until the view is reloaded, whatever the sort |
| 8 | The Parent Category quick filter | UI | **In part.** It is there and its dropdown lists every category by Complete Name; **applying** it could not be driven from automation (the click frame and the screenshot frame disagree on this page) — one click for the reviewer |
| 9 | The Parent Category picker | UI | **Pass.** Every category by Complete Name, and **+ Record** at the foot — Odoo's `can_create` / `name_create` quick-create, matched |
| 10 | Child Categories on Goods | UI | **Pass.** A read-only tab listing its four children with Complete Name and # Products — 2 · 2 · 4 · 3, which add to Odoo's 11 |
| 11 | The Products list and # Products | UI + CLI | **Pass.** IT Equipment lists its four products by Name and Internal Reference; the counts are §1's — Services 3, IT Equipment 4, Office Furniture 3, Consumables 2, Software 2, **0 on Goods and Expenses** |
| 12 | Make a category its own parent | CLI | **Accepted, as §1 predicted.** Complete Name doubles the name ("TEST UI renamed / TEST UI renamed"). No loop, nothing else breaks, and clearing the parent puts it right in one save. See difference 2 |
| 13 | A two-record cycle — each the other's parent | CLI | **Accepted.** The path repeats and **grows by one level every time a record in the cycle is saved** ("… / TEST UI renamed / TEST UI child / TEST UI renamed"). One edit undoes it. See difference 2 |
| 14 | Category's place on the Products form | UI | **Pass.** The General Information tab reads Unit \| **Cost · Category** \| Internal Reference — Odoo's own order — and it shows "Goods / IT Equipment", the Complete Name |
| 15 | Set a product's Category | CLI + UI | **Pass.** The category's Products list and its # Products both moved 0 → 1, within seconds and with no workflow |
| 16 | The Products and List views | UI | **Pass.** A **Category** quick filter on both, and no Category column on either — Odoo hides that column by default |
| 17 | Name is required | UI + CLI | **Passes in the form, with a caveat.** The create form marks it required and will not save without it; **`record create` through the API accepts a category with no Name** — the record was found and named `TEST created with no Name`. See difference 3 |
| 18 | No Archive, no Unarchive, no Archived view | UI + CLI | **Pass.** The worksheet has 0 buttons and one view; a category's form carries no button at all, where a product's carries Archive |
| — | Delete a parent that has children | — | **Not run.** No deletion happens in this app without the owner's approval. Odoo cascades (`ondelete='cascade'`); HAP does not, so the children would be left pointing at nothing |

### Differences from Odoo

1. **# Products counts this category's own products; Odoo's counts the subtree.** Goods reads **0** here and
   **11** on the tenant. This is deliberate and is what Odoo's own help promises — *"Does not consider the
   children categories"* — while `_compute_product_count` reads `('categ_id', 'child_of', self.ids)`. The
   Child Categories tab on Goods shows 2 · 2 · 4 · 3 right beside it, so the 11 is one glance away.
2. **A cycle is accepted.** Odoo's `_check_category_recursion` raises *"You cannot create recursive
   categories."*; §1 said no HAP rule can ask whether a record is its own ancestor, and tests 12 and 13
   confirm what happens instead: the Complete Name repeats the path, and a two-record cycle lengthens it by a
   level on each save of a record in the cycle. It is cosmetic — no loop, no hang, no other field affected —
   and one edit undoes it. **Worth the owner's decision**: a workflow could refuse a parent whose own Complete
   Name already contains this category's, which would catch every cycle the lookup chain can see.
3. **Name is required in the form only.** Odoo's `required=True` is a NOT NULL column; HAP's is a form check,
   and the API writes a nameless category without complaint. It joins the same list as a text field's maximum
   length (`BUILDING.md`): seed and import scripts have to check it themselves.
4. **The two relation lists are tabs at the foot of the record**, not fields in the form grid — HAP renders a
   list-style Relation that way, so §1's rows 2 and 3 became Child Categories and Products tabs under
   # Products. Odoo puts neither on a view at all.
5. **Odoo's *Products* stat button is a list, not a jump.** The Products tab shows the products themselves;
   the count above it is the same number the button would carry.
6. **The tenant cannot sort its own category list.** 19.4 stopped storing `complete_name`, so
   `order='complete_name'` answers *"Cannot convert product.category.complete_name to SQL because it is not
   stored"* and the tenant returns roots first, then each parent's children by name. HAP stores its formula,
   so the Categories view is sorted the way Odoo's `_order = 'complete_name'` asks and reads as a tree.
7. **A record just created sits at the top of the table** until the view is reloaded, whatever the sort — HAP
   puts it where you can see it. It takes its sorted place on the next load.
8. **Deleting a parent.** Odoo's `parent_id` is `ondelete='cascade'`: deleting a category deletes its
   children. HAP does not cascade, so the children would survive with a dangling parent. Not tested — nothing
   is deleted here without the owner's approval.

### Test records left in the worksheet

| Record | Why it is there |
|---|---|
| `TEST Category` — under Goods / Consumables | The build's own three-level proof (`prodcat selfcheck`) |
| `TEST UI renamed` — a root, # Products 1 | Created through the UI as `TEST UI root` (test 1), renamed by test 4, its parent cleared by test 5, and it carries `TEST Product` from test 15 |
| `TEST UI child` — under it | Test 3's fourth level |
| `TEST created with no Name` | The record the API accepted with no Name (test 17); it was given that name afterwards so the view does not show a blank row |

`TEST Product`, a test record of worksheet 03, now carries the Category `TEST UI renamed` — that is test 15's
evidence. **The tenant's seven categories and all fourteen real products are untouched by the tests**:
`prodcat verify` reads 0 categories differing and 0 products with the wrong category.
