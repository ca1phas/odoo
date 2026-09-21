# crm.tag — as on casimir.odoo.com (Odoo saas~19.4+e)

Read-only extract, 21 Sep 2026. Menu: **CRM ▸ Configuration ▸ Pipeline ▸ Tags**. Defined in **`sales_team`**,
not in `crm`. The unique constraint below is **confirmed on the tenant** (`crm_tag_name_uniq`), not just in the
19.0 source.

## Fields

| Field | Label | Type | Req. | Notes |
|---|---|---|---|---|
| `name` | Tag Name | char | **yes** | translatable; placeholder *e.g. Services* |
| `color` | Color | integer | | default is a **random** 1–11 (`_get_default_color`); `widget="color_picker"`, and **required on the form** |

## Constraint

| | Message |
|---|---|
| `unique (name)` | *Tag name already exists!* |

## Views

- **Form**: title *Tag Name*, then one group with Color as a colour picker.
- **List**, `editable="bottom"`, `sample="1"`: Tag Name · Color (colour picker).

## The records — 0

The tenant has no CRM tag.

## Why this is not Contact Tags

`crm.lead.tag_ids` is `Many2many('crm.tag', 'crm_tag_rel', …)` — [crm_lead.py:136]. `res.partner.category`,
the Contact Tags model, **appears nowhere in `crm_lead.py`**. The two are different tables with different
menus, and a lead's tags are these.
