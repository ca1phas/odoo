# utm.medium — as on casimir.odoo.com (Odoo saas~19.4+e)

Read-only extract, 21 Sep 2026. Menu: **Link Tracker ▸ UTMs ▸ Mediums** — not a CRM screen.

**Unique constraint on the tenant: `utm_medium_unique_name = UNIQUE(name)`, *"The name must be unique"*.**

## Fields

| Field | Label | Type | Req. |
|---|---|---|---|
| `name` | Medium Name | char | **yes** |
| `active` | Active | boolean | |

## Views

- **Form**: one group — Medium Name, and Active as a **boolean toggle**.
- **List**, `editable="bottom"`, `sample="1"`: Medium Name (placeholder *e.g. "Email"*); Active is a
  **`column_invisible`** column.
- **Search**: Medium Name, and an *Archived* filter.

## The records — 5

Direct · Email · Phone · Social Media · Website. All active.
