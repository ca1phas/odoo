# uom.uom — as on casimir.odoo.com (Odoo saas~19.4+e)

Read-only extract, 15 Sep 2026: `fields_get`, `get_views` (form, list, kanban, search), `ir.model.fields.modules`,
`ir.model.constraint`, the window action, and every record (archived included).

Menu: **Units & Packagings** (window action, `list,form`, context `{}`).

## Fields

| Field | Label | Type | Required | Read-only | Module | Notes |
|---|---|---|---|---|---|---|
| `name` | Unit Name | char | yes | | uom | |
| `relative_factor` | Contains | float | yes | | uom | help: "How much bigger or smaller this unit is compared to the reference UoM for this unit". SQL check `relative_factor != 0`: "The conversion ratio for a unit of measure cannot be 0!" |
| `relative_uom_id` | Reference Unit | many2one → uom.uom | | | uom | |
| `related_uom_ids` | Related UoMs | one2many → uom.uom | | | uom | reverse of `relative_uom_id` |
| `factor` | Absolute Quantity | float | | yes (computed, stored) | uom | depends `relative_factor`, `relative_uom_id`, `relative_uom_id.factor` |
| `sequence` | Sequence | integer | | | uom | computed from `relative_factor`, stored, editable (list drag handle) |
| `active` | Active | boolean | | | uom | help: "Uncheck the active field to disable a unit of measure without deleting it." |
| `parent_path` | Parent Path | char | | | uom | technical |
| `product_uom_ids` | Barcodes | one2many → product.uom | | | product | packaging barcodes per product |
| `unece_code` | UN/ECE Code | char | | | account_edi_ubl_cii | unique: "The UN/ECE code already exists!"; shown only when `is_unece_code_supported` (true on this tenant, fiscal country MY) |

## Form

```xml
<form string="Units of Measure">
  <sheet>
    <div name="button_box">
      <button name="action_open_packaging_barcodes"> "Packaging Barcodes" </button>
    </div>
    <group>
      <group name="uom_details">
        <field name="name" readonly="(context.get('product_id') or context.get('product_ids')) and id"/>
        <field name="unece_code" invisible="not is_unece_code_supported"/>
        <label string="Quantity"/>
        <div name="relative_factor">
          <field name="relative_factor" readonly="(context.get('product_id') or context.get('product_ids')) and id"/>
          <field name="relative_uom_id" placeholder="Reference Unit" readonly="(same)"/>
        </div>
      </group>
    </group>
    <div invisible="not context.get('has_variants')">Barcodes can be configured on
      <button name="action_open_packaging_barcodes" string="each variant"/>.</div>
  </sheet>
</form>
```

The `readonly` expressions only bite when the form is opened from a product.

## List

```xml
<list string="Units & Packagings">
  <field name="sequence" widget="handle"/>
  <field name="name"/>
  <field name="relative_factor" invisible="relative_factor == 1 and not relative_uom_id"/>
  <field name="relative_uom_id"/>
</list>
```

## Kanban and search

- Kanban: `name` only.
- Search: `name`; filter **Archived** `[('active', '=', False)]`.

## Records (30)

| Unit Name | Contains | Reference Unit | Absolute Quantity | Active | Sequence | UN/ECE |
|---|---|---|---|---|---|---|
| Minutes | 0.0166667 | Hours | 0.0166667 | yes | 1 | MIN |
| in³ | 0.0163871 | L | 16.3871 | no | 1 | INQ |
| fl oz (US) | 0.0295735 | L | 29.5735 | no | 2 | OZA |
| ft² | 0.092903 | m² | 0.092903 | no | 9 | FTK |
| Units | 1 | | 1 | yes | 100 | C62 |
| Hours | 1 | | 1 | yes | 100 | HUR |
| mm | 1 | | 1 | yes | 100 | MMT |
| m² | 1 | | 1 | yes | 100 | MTK |
| ml | 1 | | 1 | yes | 100 | MLT |
| g | 1 | | 1 | yes | 100 | GRM |
| KWH | 1 | | 1 | yes | 100 | KWH |
| in | 2.54 | cm | 25.4 | no | 254 | INH |
| yd | 3 | ft | 914.4 | no | 300 | YRD |
| gal (US) | 4 | qt (US) | 3785.408 | no | 400 | GLL |
| Pack of 6 | 6 | Units | 6 | yes | 600 | P6 |
| Days | 8 | Hours | 8 | yes | 800 | DAY |
| Dozens | 12 | Units | 12 | no | 1000 | DZN |
| cm | 10 | mm | 10 | no | 1000 | CMT |
| m | 100 | cm | 1000 | yes | 1000 | MTR |
| km | 1000 | m | 1000000 | no | 1000 | KMT |
| L | 1000 | ml | 1000 | yes | 1000 | LTR |
| m³ | 1000 | L | 1000000 | no | 1000 | MTQ |
| kg | 1000 | g | 1000 | yes | 1000 | KGM |
| t | 1000 | kg | 1000000 | yes | 1000 | TNE |
| oz | 28.3495 | g | 28.3495 | no | 1000 | ONZ |
| lb | 16 | oz | 453.592 | no | 1000 | LBR |
| ft | 12 | in | 304.8 | no | 1000 | FOT |
| mi | 1760 | yd | 1609344 | no | 1000 | SMI |
| qt (US) | 32 | fl oz (US) | 946.352 | no | 1000 | QTL |
| ft³ | 1728 | in³ | 28316.9088 | no | 1000 | FTQ |

The m³ row's sequence and code were cut off in the extract and follow the pattern of its neighbours.
