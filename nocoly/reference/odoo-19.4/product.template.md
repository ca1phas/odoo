# product.template — as on casimir.odoo.com (Odoo saas~19.4+e)

Read-only extract, 15 Sep 2026: `fields_get` (117 fields, 65 stored), `ir.model.fields.modules`, `get_views`
(form, list, kanban, search), the window actions, and every record (14, none archived).

Installed applications on the tenant: `account` (Invoicing), `calendar`, `contacts`, `crm`, `mail`, `project`,
`project_todo`, `sale_management`, `web_studio` — **no Inventory, Purchase, Point of Sale or Manufacturing**. Fields
and view parts those apps would drive are present but inert (for example stock quantities).

Menu: **Products** — several window actions, `kanban,list,form` (Sales and Invoicing menus default to the *Sales*
filter; the Purchase-side action defaults to *Purchase*).

## Fields

`S` = stored. Module is the first module listed for the field. Mail, activity and rating plumbing
(`activity_*`, `message_*`, `rating_ids`, `has_message`) exists on the model and is HAP-native; it is omitted below.

### Product core (`product`)

| Field | Label | Type | Req | RO | S | Notes |
|---|---|---|---|---|---|---|
| `name` | Name | char | yes | | S | placeholder "e.g. Cheese Burger" |
| `type` | Product Type | selection | yes | | S | `consu` Goods · `service` Service · `combo` Combo. help: "Goods are tangible materials and merchandise you provide. A service is a non-material product you provide." |
| `sale_ok` | Sales | boolean | | | S | checkbox under the name |
| `purchase_ok` | Purchase | boolean | | | S | checkbox under the name; hidden when type = combo |
| `is_favorite` | Favorite | boolean | | | S | star beside the name |
| `image_1920` | Image | binary | | | S | (+ 1024/512/256/128 resized copies, read-only) |
| `list_price` | Sales Price | float | | | S | help: "Price at which the product is sold to customers." |
| `standard_price` | Cost | float | | | – | company-dependent; help: "Value of the product (automatically computed in AVCO)…" |
| `uom_id` | Unit | many2one → uom.uom | yes | | S | help: "Default unit of measure used for all stock operations." |
| `uom_ids` | Packagings | many2many → uom.uom | | | S | help: "Additional packagings for this product which can be used for sales" |
| `uom_name` | Unit Name | char | | yes | – | |
| `default_code` | Internal Reference | char | | | S | form label "Reference" |
| `barcode` | Barcode | char | | | – | stored on the variant |
| `categ_id` | Product Category | many2one → product.category | | | S | form label "Category" |
| `product_tag_ids` | Tags | many2many → product.tag | | | S | |
| `description` | Description | html | | | S | "Internal Notes"; placeholder "This note is only for internal purposes." |
| `description_sale` | Sales Description | text | | | S | help: "…copied to every Sales Order, Delivery Order and Customer Invoice/Credit Note"; placeholder "This note is added to sales orders and invoices." |
| `description_purchase` | Purchase Description | text | | | S | |
| `sequence` | Sequence | integer | | | S | help: "Gives the sequence order when displaying a product list" |
| `active` | Active | boolean | | | S | help: "If unchecked, it will allow you to hide the product without removing it." |
| `color` | Color Index | integer | | | S | |
| `company_id` | Company | many2one → res.company | | | S | |
| `combo_ids` | Combo Choices | many2many → product.combo | | | S | shown when type = combo |
| `attribute_line_ids` | Product Attributes | one2many → product.template.attribute.line | | | S | tab Attributes & Variants |
| `product_variant_ids` | Products | one2many → product.product | yes | | S | |
| `product_variant_id` | Product | many2one → product.product | | yes | – | |
| `product_variant_count` | # Product Variants | integer | | yes | – | |
| `has_configurable_attributes` | Is a configurable product | boolean | | yes | S | |
| `is_dynamically_created` | Is Dynamically Created | boolean | | yes | – | |
| `seller_ids` / `variant_seller_ids` | Vendors / Variant Seller | one2many → product.supplierinfo | | | S | Purchase |
| `pricelist_rule_ids` / `fixed_pricelist_rule_ids` | Pricelist Rules / Fixed Pricelist Rule | one2many → product.pricelist.item | | | S | tab Prices |
| `product_document_ids` | Documents | one2many → product.document | | | S | smart button |
| `product_properties` | Properties | properties | | | S | |
| `weight` / `volume` | Weight / Volume | float | | | S | tab Inventory › Logistics (+ read-only unit labels) |
| `is_storable` | Track Inventory | boolean | | | S | |
| `qty_available`, `virtual_available`, `incoming_qty`, `outgoing_qty`, `free_qty` | On Hand, Forecasted, Incoming, Outgoing, Free To Use | float | | | – | computed; inert without Inventory |
| `base_unit_count` | Reference Unit | float | yes | | S | help: "Display base unit price. Set to 0 to hide it for this product." |
| `base_unit_id` | Custom Unit of Measure | many2one → product.base.unit | | | S | |
| `base_unit_price` / `base_unit_name` | Price Per Unit / Base Unit Name | monetary / char | | yes | – | |
| `currency_id` / `cost_currency_id` | Currency / Cost Currency | many2one → res.currency | | yes | – | |
| `product_tooltip` | Product Tooltip | char | | yes | – | |

### Invoicing (`account`)

| Field | Label | Type | S | Notes |
|---|---|---|---|---|
| `taxes_id` | Sales Taxes | many2many → account.tax | S | "Default taxes used when selling the product" |
| `supplier_taxes_id` | Purchase Taxes | many2many → account.tax | S | "Default taxes used when buying the product" |
| `tax_string` | Tax String | char | – | read-only, shown beside Sales Taxes |
| `property_account_income_id` | Income Account | many2one → account.account | S | "Keep this field empty to use the default value from the product category." |
| `property_account_expense_id` | Expense Account | many2one → account.account | S | same, for expenses |
| `account_tag_ids` | Account Tags | many2many → account.account.tag | S | |

### Sales (`sale`, `sale_project`)

| Field | Label | Type | Req | S | Notes |
|---|---|---|---|---|---|
| `invoice_policy` | Invoicing Policy | selection | yes | S | `order` Ordered quantities · `delivery` Delivered quantities |
| `service_tracking` | Create on Order | selection | yes | S | `no` Nothing · `task_global_project` Task · `task_in_project` Project & Task · `project_only` Project (`sale_project`) |
| `service_type` | Track Service | selection | | S | `manual` Manually set quantities on order · `milestones` Project Milestones |
| `service_policy` | Service Invoicing Policy | selection | | – | `ordered_prepaid` Prepaid/Fixed Price · `delivered_manual` Based on Delivery (Manual); form label "Invoicing Policy" for services |
| `project_id` | Project | many2one → project.project | | S | |
| `project_template_id` | Project Template | many2one → project.project | | S | |
| `task_template_id` | Task Template | many2one → project.task | | S | |
| `sale_line_warn_msg` | Sales Order Line Warning | text | | S | |
| `reinvoice_policy` | Re-Invoice Costs | selection | | S | `no` No · `cost` At cost · `sales_price` At Sales price |
| `optional_product_ids` | Optional Products | many2many → product.template | | S | placeholder "Recommend when 'Adding to Cart' or quotation" |
| `sale_delay` | Delivery Time | integer | | S | days |
| `sales_count` | Sold | float | | – | smart button |

### Malaysian localisation

| Field | Label | Type | Module | Notes |
|---|---|---|---|---|
| `l10n_my_tax_classification_code` | Malaysian Customs Tariff Code (goods) / Malaysian Service Type Code (services) | char | `l10n_my` | shown for fiscal country MY |
| `l10n_my_edi_classification_code` | Malaysian classification code | selection (45 MyInvois codes, 001 Breastfeeding equipment … 045 Self-billed – Non-monetary payment to agents) | `l10n_my_edi` | shown for fiscal country MY |

## Form

`=` and `&` restored; attributes kept: invisible, required, readonly, placeholder, widget, string.

```xml
<form string="Product">
  <sheet>
    <div name="button_box"> Variants (product_variant_count) · Documents · Sold (sales_count) </div>
    <widget name="web_ribbon" invisible="active"/>
    <h1>
      <field name="is_favorite" widget="boolean_favorite"/>
      <field name="name" placeholder="e.g. Cheese Burger"/>
    </h1>
    <div name="options">
      <span name="sale_option"><field name="sale_ok"/> Sales</span>
      <span name="purchase_option" invisible="type == 'combo'"><field name="purchase_ok"/> Purchase</span>
    </div>
    <field name="image_1920"/>
    <notebook>
      <page name="general_information" string="General Information">
        <group>
          <group name="group_general">
            <field name="type" widget="radio"/>
            <field name="invoice_policy" invisible="(not sale_ok or type == 'combo') or (type == 'service')"/>
            <field name="combo_ids" invisible="type != 'combo'" placeholder="e.g. Starter - Meal - Desert"/>
            <field name="service_tracking" invisible="(type != 'service') or (not sale_ok)"/>
            <field name="project_id" invisible="service_tracking != 'task_global_project'" placeholder="Defined on quotation"/>
            <field name="project_template_id" invisible="service_tracking not in ['task_in_project', 'project_only']" placeholder="Empty project"/>
            <field name="task_template_id" invisible="not project_id or service_tracking != 'task_global_project'"/>
            <field name="service_policy" string="Invoicing Policy" invisible="type != 'service' or sale_ok == False" required="type == 'service' and sale_ok == True"/>
            <field name="product_tooltip" invisible="not product_tooltip"/>
            <field name="is_storable" invisible="type != 'consu' or is_storable"/>
            <!-- when goods and tracked: Track Inventory + Quantity On Hand + Free To Use, with the unit -->
            <field name="l10n_my_edi_classification_code" invisible="'MY' not in fiscal_country_codes"/>
          </group>
          <group name="group_standard_price">
            <label>Sales Price</label> <field name="list_price" widget="monetary"/> per <field name="uom_id"/>
            <label invisible="type == 'combo'">Sales Taxes</label>
            <field name="taxes_id" widget="many2many_tax_tags"/> <field name="tax_string"/>
            <label invisible="type == 'combo' or (not is_product_variant and (product_variant_count > 1 or (product_variant_count == 0 and is_dynamically_created)))">Cost</label>
            <field name="standard_price" widget="monetary"/> per <field name="uom_id"/>
            <field name="supplier_taxes_id" invisible="not purchase_ok or type == 'combo'"/>
            <field name="categ_id" string="Category"/>
            <field name="default_code" string="Reference" invisible="product_variant_count > 1"/>
            <field name="barcode" invisible="product_variant_count > 1 or (product_variant_count == 0 and valid_product_template_attribute_line_ids) or type in ['service', 'combo']"/>
            <field name="product_tag_ids" widget="many2many_tags"/>
            <field name="l10n_my_tax_classification_code" invisible="'MY' not in fiscal_country_codes or type == 'service'"/>
            <field name="l10n_my_tax_classification_code" string="Malaysian Service Type Code" invisible="'MY' not in fiscal_country_codes or type != 'service'"/>
          </group>
          <field name="product_properties"/>
        </group>
        <group name="internal_notes" string="Internal Notes">
          <field name="description" placeholder="This note is only for internal purposes."/>
        </group>
      </page>
      <page name="variants" string="Attributes &amp; Variants" invisible="type == 'combo'">
        <field name="attribute_line_ids">
          <list>
            <field name="sequence" widget="handle"/>
            <field name="attribute_id" placeholder="Attribute name (e.g. Color, Size, ... )"/>
            <field name="value_ids" placeholder="List of possible values (e.g. Blue, Green, White, ... )"/>
            <button name="action_open_attribute_values" string="Configure"/>
          </list>
        </field>
      </page>
      <page name="sales" string="Sales" invisible="not sale_ok">
        <group name="upsell" string="Upsell &amp; Cross-Sell">
          <field name="uom_ids" widget="many2many_uom_tags"/>
          <button name="action_open_packaging_barcodes" string="Barcodes" invisible="type != 'consu' or not product_variant_count"/>
          <field name="optional_product_ids" placeholder="Recommend when 'Adding to Cart' or quotation"/>
        </group>
        <group name="description" string="Short Description">
          <field name="description_sale" placeholder="This note is added to sales orders and invoices."/>
        </group>
        <group name="expense_info" string="Expenses, Services &amp; Materials" invisible="not visible_reinvoice_policy">
          <field name="reinvoice_policy" widget="radio"/>
        </group>
      </page>
      <page name="sales_price" string="Prices" invisible="not show_sales_price_page">
        <field name="fixed_pricelist_rule_ids">
          <list>  <!-- "Add a price" -->
            Variant (optional hide) · Pricelist · Min. Quantity · Unit · Validity (optional hide) · Unit Price
          </list>
        </field>
      </page>
      <page name="purchase" string="Purchase" invisible="1 or not purchase_ok or type == 'combo'"/>
      <page name="inventory" string="Inventory" invisible="type in ['service', 'combo']">
        <group name="group_lots_and_weight" string="Logistics" invisible="type != 'consu'">
          Weight (+ unit label) · Volume (+ unit label) · Delivery Time (days, invisible="not sale_ok")
        </group>
      </page>
    </notebook>
  </sheet>
  <chatter/>
</form>
```

## List

Visible by default: Favorite (star) · **Product Name** · Internal Reference · Sales Price · Cost · On Hand · Free To Use
(storable only) · Forecasted · Unit · activity exception. Optional, hidden by default: Tags · Barcode · Product
Category · Product Type.

## Kanban

Card: image, name, favorite star, variant count, Sales Price, Cost, Internal Reference, properties, On Hand + Unit.

## Search

- Search fields: Product (name), Product Category, Tags, Attributes.
- Filters: Goods · Services · Combo | Favorites | Sales · Purchase | Warnings | Archived.
- Group by: Product Type · Product Category · Product Properties.

## Records (14)

All active; none favourite; no barcodes; weight, volume and delivery time 0; every product has 1 sales tax.

| Name | Internal Ref | Type | Sales | Purchase | Sales Price | Cost | Unit | Invoicing Policy | Service Invoicing | Variants | Category |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 27" 4K Monitor | | Goods | ✓ | ✓ | 1890 | 0 | Units | Ordered | Prepaid/Fixed | 3 | Goods / IT Equipment |
| A4 Copy Paper (Box of 5 reams) | CONS-0001 | Goods | ✓ | ✓ | 68 | 41 | Units | Ordered | Prepaid/Fixed | 1 | Goods / Consumables |
| Annual Support Retainer | SRV-0003 | Service | ✓ | | 18000 | 7200 | Units | Ordered | Prepaid/Fixed | 1 | Services |
| Business Laptop 14" i7 | IT-0001 | Goods | ✓ | ✓ | 5400 | 4150 | Units | Ordered | Prepaid/Fixed | 1 | Goods / IT Equipment |
| Docking Station USB-C | IT-0004 | Goods | ✓ | ✓ | 760 | 520 | Units | Ordered | Prepaid/Fixed | 1 | Goods / IT Equipment |
| Ergonomic Office Chair | | Goods | ✓ | ✓ | 899 | 0 | Units | Ordered | Prepaid/Fixed | 4 | Goods / Office Furniture |
| Height-Adjustable Desk 140cm | | Goods | ✓ | ✓ | 1650 | 0 | Units | Ordered | Prepaid/Fixed | 3 | Goods / Office Furniture |
| Implementation Consulting | SRV-0001 | Service | ✓ | | 850 | 400 | Hours | Delivered | Based on Delivery (Manual) | 1 | Services |
| Nocoly HAP Licence — Pro | SW-0002 | Service | ✓ | | 7200 | 0 | Units | Ordered | Prepaid/Fixed | 1 | Goods / Software |
| Nocoly HAP Licence — Standard | SW-0001 | Service | ✓ | | 2940 | 0 | Units | Ordered | Prepaid/Fixed | 1 | Goods / Software |
| Onsite Training (per day) | SRV-0002 | Service | ✓ | | 3200 | 1500 | Days | Delivered | Based on Delivery (Manual) | 1 | Services |
| Steel Filing Cabinet 4-Drawer | FURN-0003 | Goods | ✓ | ✓ | 720 | 430 | Units | Ordered | Prepaid/Fixed | 1 | Goods / Office Furniture |
| Whiteboard Marker Set | CONS-0002 | Goods | ✓ | ✓ | 24.5 | 11 | Units | Ordered | Prepaid/Fixed | 1 | Goods / Consumables |
| Wireless Keyboard & Mouse Set | IT-0003 | Goods | ✓ | ✓ | 289 | 168 | Units | Ordered | Prepaid/Fixed | 1 | Goods / IT Equipment |

"Create on Order" is Nothing on every product. The three products with no Internal Reference and a Cost of 0 are the
ones with variants (monitor, chair, desk): Odoo hides both fields on the template once it has more than one variant.
