# crm.lost.reason — as on casimir.odoo.com (Odoo saas~19.4+e)

Read-only extract, 21 Sep 2026. Menu: **CRM ▸ Configuration ▸ Lost Reasons**.

## Fields

| Field | Label | Type | Req. | Notes |
|---|---|---|---|---|
| `name` | **Description** | char | **yes** | Odoo labels it *Description*, not *Name*; placeholder *e.g. Too expensive* |
| `active` | Active | boolean | | invisible on the form; the *Archived* ribbon shows instead |
| `leads_count` | Leads Count | integer, computed | | the form's one stat button, *Leads* |

## Views

- **Form**: a stat button *Leads* (`action_lost_leads`), the **Archived** ribbon, then the title — Description alone.
- **List** `crm.lost.reason.list`, **`editable="bottom"`**: Description only, one column.
- **Search**: Description, plus filters **Active** and **Archived**.

## The records — 3

Too expensive · We don't have people/skills · Not enough stock. All active.
