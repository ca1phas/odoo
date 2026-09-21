# crm.recurring.plan — as on casimir.odoo.com (Odoo saas~19.4+e)

Read-only extract, 21 Sep 2026. Menu: **CRM ▸ Configuration ▸ Recurring Plans**, and the whole feature sits
behind the group **`crm.group_use_recurring_revenues`** — with it off, neither this menu nor the three recurring
fields on an opportunity are visible.

## Fields

| Field | Label | Type | Req. | Notes |
|---|---|---|---|---|
| `name` | Plan Name | char | **yes** | |
| `number_of_months` | # Months | integer | **yes** | |
| `active` | Active | boolean | | |
| `sequence` | Sequence | integer | | |

## Views

- **List** `crm.recurring.plan.view.list`, **`editable="bottom"`**: sequence (handle) · Plan Name · # Months.
  **There is no form view** — the list is the whole screen.
- **Search**: Plan Name, and an *Archived* filter.

## The records — 4

| Plan Name | # Months | Sequence |
|---|---|---|
| Monthly | 1 | 10 |
| Yearly | 12 | 10 |
| Over 3 years | 36 | 10 |
| Over 5 years | 60 | 10 |

## What points here

`crm.lead.recurring_plan`, beside `recurring_revenue` and `recurring_revenue_monthly` — all three behind
`crm.group_use_recurring_revenues`. **Nothing else in the database references this model**, so a Recurring Plans
worksheet with no Recurring Plan field on Leads has nothing pointing at it.
