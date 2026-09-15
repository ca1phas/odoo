# product.product — as on casimir.odoo.com (Odoo saas~19.4+e)

Read-only extract, 15 Sep 2026: `fields_get`, `ir.model.fields.modules`, `get_views` (form, list, kanban, search), the
window actions, and every variant (21, archived included).

A **variant** is one sellable version of a product template. Every template has at least one; the variants bundle
(attributes and their values) is what creates more. Order lines, invoice lines and stock moves point at the variant.
Installed apps on the tenant are listed in `product.template.md` (no Inventory, Purchase or POS).

Menu: no menu of its own on this tenant — **Product Variants** opens from a product's *Variants* smart button
(`list,form`, context `create: False`, default filter on that product). The *Product Variants* setting also adds a
Sales › Products › Product Variants menu when enabled.

## Fields stored on the variant (`product`, unless noted)

Every other product field is the template's, reached through `product_tmpl_id` (related, not stored on the variant):
name, type, sale_ok, purchase_ok, uom_id, categ_id, taxes, descriptions, invoice policy and the rest listed in
`product.template.md`.

| Field | Label | Type | Req | RO | Notes |
|---|---|---|---|---|---|
| `product_tmpl_id` | Product Template | many2one → product.template | yes | | |
| `default_code` | Internal Reference | char | | | |
| `barcode` | Barcode | char | | | help: "International Article Number used for product identification." Unique per company (Python check) |
| `lst_price` | Sales Price | float | | | help: "The sale price can be set manually or computed from the product template…" = template Sales Price + the variant's attribute price extras |
| `standard_price` | Cost | float | | | company-dependent on the variant |
| `active` | Active | boolean | | | "If unchecked, it will allow you to hide the product without removing it." |
| `product_template_attribute_value_ids` | Attribute Values | many2many → product.template.attribute.value | | | variants bundle |
| `product_template_variant_value_ids` | Attributes | many2many → product.template.attribute.value | | | variants bundle; shown as colour-dot tags under the name |
| `combination_indices` | Combination Indices | char | | yes | variants bundle |
| `extra_uom_ids` | Extra Packagings | many2many → uom.uom | | | "Variant-specific additional packagings for this product which can be used for sales" |
| `product_uom_ids` | Unit Barcode | one2many → product.uom | | | packaging barcodes |
| `additional_product_tag_ids` | Variant Tags | many2many → product.tag | | | |
| `image_variant_1920` | Variant Image | binary | | | (+ 1024/512/256/128 resized copies) |
| `is_favorite` | Favorite | boolean | | | |
| `weight` / `volume` | Weight / Volume | float | | | stored on the variant |
| `qty_available` | Quantity On Hand | float | | | stored; inert without Inventory |
| `product_document_ids` | Documents | one2many → product.document | | | |
| `base_unit_count` / `base_unit_id` | Reference Unit / Custom Unit of Measure | float (req) / many2one → product.base.unit | | | eCommerce price per unit |
| `is_image_fetch_pending` | Is Image Fetch Pending | boolean | | | `product_barcodelookup` |

## Form

The variant form is the template form (see `product.template.md`) with these differences:
- Under the name, the variant's **Attributes** as colour-dot tags (read-only, hidden when it has none).
- **Sales Price** is `lst_price`; **Cost** is the variant's own `standard_price`.
- Smart buttons: Documents, Sold. No Variants button, no Attributes & Variants tab.

## List

Visible by default: image · **Name** · Attributes (tags) · Sales Price · Cost · Barcode · On Hand and Free To Use (storable
only) · Unit. Optional, hidden by default: Internal Reference · Forecasted · Extra Packagings · Volume · Weight.

## Kanban

Card: image, name, favourite star, attribute values, Sales Price, Cost, Internal Reference, On Hand + Unit.

## Search

- Search fields: Product (name), Product Category, Tags, Attribute Values, Product (template).
- Filters: Goods · Services · Combo | Favorites | Sales · Purchase | Warnings | Archived.
- Group by: Product Type · Product Category · Product (template) · Product Properties.

## Order and constraints

- `_order`: `default_code, name, id`.
- No SQL constraints on the model. Barcode uniqueness is a Python check (see the 19.0 source,
  `addons/product/models/product_product.py`).

## Records (21)

Name as Odoo displays it (`[Internal Reference] Name (attribute values)`).

| Display name | Template | Internal Ref | Sales Price | Cost | Attribute values (price extra) | Active |
|---|---|---|---|---|---|---|
| [IT-0002] 27" 4K Monitor | 27" 4K Monitor | IT-0002 | 1890 | 1420 | — | **archived** |
| 27" 4K Monitor (Silver) | 27" 4K Monitor | | 1950 | 0 | Color: Silver (+60) | yes |
| 27" 4K Monitor (Black) | 27" 4K Monitor | | 1890 | 0 | Color: Black | yes |
| [CONS-0001] A4 Copy Paper (Box of 5 reams) | A4 Copy Paper (Box of 5 reams) | CONS-0001 | 68 | 41 | — | yes |
| [SRV-0003] Annual Support Retainer | Annual Support Retainer | SRV-0003 | 18000 | 7200 | — | yes |
| [IT-0001] Business Laptop 14" i7 | Business Laptop 14" i7 | IT-0001 | 5400 | 4150 | — | yes |
| [IT-0004] Docking Station USB-C | Docking Station USB-C | IT-0004 | 760 | 520 | — | yes |
| [FURN-0001] Ergonomic Office Chair | Ergonomic Office Chair | FURN-0001 | 899 | 540 | — | **archived** |
| Ergonomic Office Chair (Red) | Ergonomic Office Chair | | 1019 | 0 | Color: Red (+120) | yes |
| Ergonomic Office Chair (Blue) | Ergonomic Office Chair | | 959 | 0 | Color: Blue (+60) | yes |
| Ergonomic Office Chair (Black) | Ergonomic Office Chair | | 899 | 0 | Color: Black | yes |
| [FURN-0002] Height-Adjustable Desk 140cm | Height-Adjustable Desk 140cm | FURN-0002 | 1650 | 980 | — | **archived** |
| Height-Adjustable Desk 140cm (Oak) | Height-Adjustable Desk 140cm | | 1650 | 0 | Material: Oak | yes |
| Height-Adjustable Desk 140cm (Aluminium) | Height-Adjustable Desk 140cm | | 1710 | 0 | Material: Aluminium (+60) | yes |
| [SRV-0001] Implementation Consulting | Implementation Consulting | SRV-0001 | 850 | 400 | — | yes |
| [SW-0002] Nocoly HAP Licence — Pro | Nocoly HAP Licence — Pro | SW-0002 | 7200 | 0 | — | yes |
| [SW-0001] Nocoly HAP Licence — Standard | Nocoly HAP Licence — Standard | SW-0001 | 2940 | 0 | — | yes |
| [SRV-0002] Onsite Training (per day) | Onsite Training (per day) | SRV-0002 | 3200 | 1500 | — | yes |
| [FURN-0003] Steel Filing Cabinet 4-Drawer | Steel Filing Cabinet 4-Drawer | FURN-0003 | 720 | 430 | — | yes |
| [CONS-0002] Whiteboard Marker Set | Whiteboard Marker Set | CONS-0002 | 24.5 | 11 | — | yes |
| [IT-0003] Wireless Keyboard & Mouse Set | Wireless Keyboard & Mouse Set | IT-0003 | 289 | 168 | — | yes |

No barcodes on any variant. The three products with attributes keep their original single variant, **archived**, with
the Internal Reference and Cost they had before attributes were added — Odoo archives rather than deletes a variant
that has been used (orders or invoices point at it).
