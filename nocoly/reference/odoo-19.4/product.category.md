# product.category — as on casimir.odoo.com (Odoo saas~19.4+e)

Read-only extract, 16 Sep 2026: `fields_get`, `ir.model.fields` (for the module each field comes from),
`get_views` (form, list, search), the window action, every record, and the category of every product.
Behaviour the tenant cannot show is read from the Odoo 19.0 source in this repo,
`addons/product/models/product_category.py` and `addons/product/views/product_category_views.xml`.

Menu: **Categories** (window action id 287, `list,form`, path `product-categories`, context `{}`, no domain).
Odoo reaches it from Inventory/Sales ▸ Configuration ▸ Product Categories; there is no top-level menu on the tenant.

## Fields

Module column: `product` unless noted. The chatter, rating and activity fields (`message_*`, `rating_ids`,
`has_message`) come from `mail.thread` and are left out.

| Field | Label | Type | Required | Read-only | Module | Notes |
|---|---|---|---|---|---|---|
| `name` | Name | char | yes | | product | `index='trigram'`. Form placeholder "e.g. Lamps", form label **Category** |
| `complete_name` | Complete Name | char | | yes | product | computed, recursive: `parent.complete_name + ' / ' + name`. **Not stored on the tenant** — `order='complete_name'` answers *"Cannot convert product.category.complete_name to SQL because it is not stored"*. The 19.0 source declares it `store=True` |
| `parent_id` | Parent Category | many2one → product.category | | | product | `index=True`, **`ondelete='cascade'`** — deleting a parent deletes its children. Form label **Parent**, placeholder "None", quick-create and inline edit allowed |
| `child_id` | Child Categories | one2many → product.category | | | product | reverse of `parent_id`; not on any view |
| `parent_path` | Parent Path | char | | | product | technical, `index=True`, `_parent_store` |
| `product_count` | # Products | integer | | yes | product | computed, **not stored**. help: "The number of products under this category (Does not consider the children categories)" — **the help is wrong**: `_compute_product_count` reads `('categ_id', 'child_of', self.ids)` over the whole subtree. The tenant proves it: Goods holds no product of its own and reports 11, the total of its four children |
| `product_properties_definition` | Product Properties | properties_definition | | | product | defines the ad-hoc fields `product.template.product_properties` carries |
| `company_id` | Company | many2one → res.company | | | product | multi-company |
| `property_account_income_categ_id` | Income Account | many2one → account.account | | | **account** | company-dependent. help: "This account will be used when validating a customer invoice." |
| `property_account_expense_categ_id` | Expense Account | many2one → account.account | | | **account** | company-dependent. help: "The expense is accounted for when a vendor bill is validated, except in anglo-saxon accounting with perpetual inventory valuation in which case the expense (Cost of Goods Sold account) is recognized at the customer invoice validation." |

**There is no `active` field.** A category cannot be archived — Odoo's only way out is deletion.

## Form

```xml
<form>
  <sheet>
    <div class="oe_button_box" name="button_box">
      <button class="oe_stat_button" name="281" icon="fa-th-list" type="action"
              context="{'search_default_categ_id': id, 'default_categ_id': id, 'group_expand': True}">
        <div class="o_field_widget o_stat_info">
          <span class="o_stat_value"><field name="product_count"/></span>
          <span class="o_stat_text"> Products</span>
        </div>
      </button>
    </div>
    <div class="oe_title">
      <label for="name" string="Category"/>
      <h1><field name="name" placeholder="e.g. Lamps"/></h1>
    </div>
    <group name="first" col="2">
      <field name="parent_id" class="oe_inline" string="Parent" placeholder="None"
             can_create="True" can_write="True"/>
    </group>
    <notebook/>
  </sheet>
  <chatter/>
</form>
```

The stat button opens the Products action filtered to this category (`search_default_categ_id`), and the action's
`group_expand` keeps the category's column visible when it holds nothing.

## List

```xml
<list string="Product Categories">
  <field name="display_name" string="Product Category"/>
</list>
```

One column, and it is the **display name** — which is `complete_name`, so the list reads as an indented tree:
"Goods", then "Goods / Consumables".

## Search

```xml
<search string="Product Categories">
  <field name="name" string="Product Categories"/>
  <field name="parent_id"/>
</search>
```

No filters and no group-by.

## Order and naming, from the 19.0 source

- `_parent_name = "parent_id"`, `_parent_store = True`, `_rec_name = 'complete_name'`, `_order = 'complete_name'`.
- `_compute_display_name` depends on the context key `hierarchical_naming`: the default is the complete name,
  and `hierarchical_naming=False` gives the bare `name` (used where the parent is already obvious).
- `name_create` makes a category from a typed name — that is Odoo's quick-create in the product form's picker.
- `copy_data` names a duplicate "**%s (copy)**".
- `@api.constrains('parent_id')` `_check_category_recursion` raises **"You cannot create recursive categories."**
- The tenant, whose `complete_name` is not stored, returns categories parent-first and then by name — roots
  Expenses · Goods · Services, then Goods' children Consumables · IT Equipment · Office Furniture · Software.

## Records — all 7, 16 Sep 2026

| id | Name | Parent | Complete Name | # Products |
|---|---|---|---|---|
| 2 | Expenses | — | Expenses | 0 |
| 1 | Goods | — | Goods | 11 |
| 3 | Services | — | Services | 3 |
| 7 | Consumables | Goods | Goods / Consumables | 2 |
| 5 | IT Equipment | Goods | Goods / IT Equipment | 4 |
| 4 | Office Furniture | Goods | Goods / Office Furniture | 3 |
| 6 | Software | Goods | Goods / Software | 2 |

Two levels, one branch: only Goods has children. Expenses is Odoo's stock category for expense products and holds
nothing on this tenant.

## `product.template.categ_id` — the field this bundle fills

| Attribute | Value |
|---|---|
| Label | Product Category (form label **Category**) |
| Type | many2one → product.category |
| Required | **no** on the tenant (19.0 source declares it without `required`, and there is no default) |
| Tracking | yes (`tracking=True`) |
| Help | none |
| Group expand | `_read_group_categ_id` — a kanban grouped by category keeps empty columns |
| Form | General Information, right column, between Cost/Purchase Taxes and Reference |
| List | `optional="hide"` — a column the user can switch on, off by default |
| Search | `filter_domain="[('categ_id', 'child_of', raw_value)]"` — searching Goods finds the children's products too; group-by **Product Category** |

`default_get` on `product.template` returns nothing for `categ_id` on this tenant: new products start with no category.

### Every product's category, 16 Sep 2026 (14 active products)

| Product | Category |
|---|---|
| 27" 4K Monitor | Goods / IT Equipment |
| A4 Copy Paper (Box of 5 reams) | Goods / Consumables |
| Annual Support Retainer | Services |
| Business Laptop 14" i7 | Goods / IT Equipment |
| Docking Station USB-C | Goods / IT Equipment |
| Ergonomic Office Chair | Goods / Office Furniture |
| Height-Adjustable Desk 140cm | Goods / Office Furniture |
| Implementation Consulting | Services |
| Nocoly HAP Licence — Pro | Goods / Software |
| Nocoly HAP Licence — Standard | Goods / Software |
| Onsite Training (per day) | Services |
| Steel Filing Cabinet 4-Drawer | Goods / Office Furniture |
| Whiteboard Marker Set | Goods / Consumables |
| Wireless Keyboard & Mouse Set | Goods / IT Equipment |

## Other models that point here

| Model | Field | Note |
|---|---|---|
| `product.template` | `categ_id` | this bundle |
| `product.category` | `parent_id`, `child_id` | itself |
| `product.product` | `categ_id` | inherited from the template through `_inherits` |
| `account.account` (Chart of Accounts bundle) | — | the two company-dependent accounts above point *at* accounts |
