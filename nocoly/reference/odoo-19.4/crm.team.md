# crm.team — as on casimir.odoo.com (Odoo saas~19.4+e)

Read-only extract, 21 Sep 2026. Menu: **CRM ▸ Configuration ▸ Sales Teams** (and a second action inside the
Sales app). Defined in **`sales_team`**. `_order = 'sequence ASC, create_date DESC, id DESC'`.

## Fields the form and list name

| Field | Label | Type | Req. | Notes |
|---|---|---|---|---|
| `name` | Sales Team | char | **yes** | the title, placeholder *e.g. North America* |
| `sequence` | Sequence | integer | | invisible on the form |
| `active` | Active | boolean | | invisible; the **Archived** ribbon shows instead |
| `user_id` | Team Leader | many2one → `res.users` | | `widget="many2one_avatar_user"`, domain `share = False` |
| `member_ids` | **Salespersons** | many2many → `res.users` | | the **Members** page, drawn as a kanban of avatars with name and email |
| `company_id` | Company | many2one → `res.company` | | `groups="base.group_multi_company"`, placeholder *Visible to all* |
| `color` | Color Index | integer | | |
| `is_favorite` | Show on dashboard | boolean | | |
| `use_leads` / `use_opportunities` | Leads / Pipeline | boolean | | the two feature switches |
| `invoiced_target` | Invoicing Target | float | | help "Revenue Target for the current month (untaxed total of paid invoices)" — added by `sale` |
| `alias_id` | Alias | many2one → `mail.alias` | **yes** | the mail gateway; `alias_name`, `alias_domain_id`, `alias_contact` and friends are related fields on it |
| `alias_contact` | Alias Contact Security | selection | **yes** | `everyone` · `partners` (Authenticated Partners) · `followers` (Followers only) |
| `is_membership_multi` | Multiple Memberships Allowed | boolean | | a system parameter, not per team; decides whether `member_ids` or `crm_team_member_ids` is shown |
| `crm_team_member_ids` | Sales Team Members | one2many → `crm.team.member` | | the **multi-membership** path, shown only when `is_membership_multi` |
| `assignment_*`, `lead_*`, `opportunity_count`, `invoiced`, `sale_order_count` | — | computed | | lead-assignment machinery and dashboard counters |
| `lead_properties_definition` | Lead Properties | properties_definition | | where an opportunity's Properties are defined |

## Views

- **Form** `crm.team.form` (`js_class="crm_team_form"`): a multi-team alert banner, the **Archived** ribbon, the
  title *Sales Team*, a *Team Details* group — Team Leader, Company — and a **Members** page holding `member_ids`
  as a kanban. A `<chatter/>` closes it.
- **List** `crm.team.list`, `multi_edit="1"`, `sample="1"`: sequence (handle) · **Sales Team (read-only)** ·
  Team Leader · Company.
- The default CRM action opens **kanban, form** — the dashboard — not a list.

## The records — 7, two archived

| id | Sales Team | Sequence | Active | Team Leader | Members | Alias | Colour |
|---|---|---|---|---|---|---|---|
| 1 | **Sales** | 0 | yes | Casimir | 1 | `info` | 7 |
| 4 | Enterprise | 10 | yes | — | — | — | 5 |
| 5 | SMB | 10 | yes | — | — | — | 3 |
| 6 | Channel Partners | 10 | yes | — | — | — | 1 |
| 7 | Online | 10 | yes | — | — | — | 1 |
| 2 | Website | 10 | **archived** | — | — | — | 8 |
| 3 | Point of Sale | 10 | **archived** | — | — | — | 1 |

`alias_contact` is **everyone** on all seven; `invoiced_target` is 0 on all seven.
