# utm.campaign — as on casimir.odoo.com (Odoo saas~19.4+e)

Read-only extract, 21 Sep 2026. Menu: **Link Tracker ▸ UTMs ▸ Campaigns** — **not a CRM screen.** Checked on
the tenant on 21 Sep 2026: the CRM ▸ Configuration menu does not carry Campaigns, Mediums or Sources at all.
Defined in `utm`, extended by `sale`, `crm` and the marketing apps.

**Unique constraint on the tenant: `utm_campaign_unique_name = UNIQUE(name)`, *"The name must be unique"* — on
`name`, the Campaign Identifier, not on `title`, the Campaign Name.**

## Fields

| Field | Label | Type | Req. | Notes |
|---|---|---|---|---|
| `title` | **Campaign Name** | char | **yes** | what a person types — placeholder *e.g. Black Friday* |
| `name` | **Campaign Identifier** | char | **yes** | the UTM slug. **Invisible on the form and a hidden column in the list** — Odoo generates it from the title |
| `user_id` | Responsible | many2one → `res.users` | **yes** | `widget="many2one_avatar_user"`, domain `share = False` |
| `stage_id` | Stage | many2one → **`utm.stage`** | **yes** | a **status bar in the form header**, clickable; the kanban groups by it |
| `tag_ids` | Tags | many2many → **`utm.tag`** | | `widget="many2many_tags"` with a colour field |
| `active` | Active | boolean | | invisible; **Archived** ribbon |
| `color` | Color Index | integer | | |
| `is_auto_campaign` | Automatically Generated Campaign | boolean | | a search filter |
| `company_id` | Company | many2one → `res.company` | | |
| `crm_lead_count`, `quotation_count`, `invoiced_amount`, `use_leads` | — | computed | | the three stat buttons, each `groups="sales_team.group_sale_salesman"` |

**Two required relations that are themselves unbuilt models**: `utm.stage` and `utm.tag`. A faithful Campaigns
worksheet needs both, or has to say why it does without them.

## Views

- **Form**: header status bar `stage_id`; a stat-button box (Revenues · Quotations · Leads/Opportunities);
  then Campaign Name · Responsible · Tags. `name` is present but `invisible="1"`.
- **Kanban** (the default view), grouped by `stage_id`, `on_create="quick_create"` with its own quick-create form.
- **List** `multi_edit="1"`: Name (`title`, read-only) · Responsible · Stage · Tags (optional, hidden).
- **Search**: Campaigns (`title`), Tags, Responsible, auto-generated; filter *My Campaigns*; group by Stage,
  Responsible, Tags.

## The records — 0

The tenant has no campaign.
