# crm.lead — as on casimir.odoo.com (Odoo saas~19.4+e)

Read-only extract, 21 Sep 2026: `fields_get`, the raw `ir.ui.view.arch_db` of every primary form, list and search
view, and the window actions. **No lead or opportunity exists on the tenant**, so there are no records to copy —
the value here is the model and the form, not data.

Menu: **CRM ▸ Sales ▸ My Pipeline** (`crm.crm_lead_opportunities`), with Leads a separate menu when
`crm.group_use_lead` is on. `_order = 'priority desc, id desc'`.

## The one thing to get right first

`crm.lead` is **two things in one table**. `type` is a required selection — `lead` · `opportunity` — rendered as
a **badge in the form header**, and almost every view is doubled: `crm.lead.list.lead` and
`crm.lead.list.opportunity`, `crm.lead.search.lead` and `crm.lead.search.opportunity`.

**But on this tenant the lead half is switched off.** `crm.group_use_lead` is **false** (checked 21 Sep 2026),
so Odoo's own menu bar reads *CRM · Sales · Reporting · Configuration* with **no Leads entry**, `type` is forced
to `opportunity`, and none of the `…lead` views ever renders. A worksheet that models the opportunity alone is
therefore **faithful to this tenant as configured** — it only becomes a gap if the group is ever turned on.
`crm.group_use_recurring_revenues` is **false** too, which hides `recurring_revenue`,
`recurring_revenue_monthly` and `recurring_plan` on the form and the whole Recurring Plans menu.

## What the screen actually is

The CRM app opens on a **kanban board grouped by `stage_id`** — the pipeline — with a column per stage
(New · Qualified · Proposition · Won), a `+` on each to quick-create, and the folded stages behind a `»`. The
lists are secondary. **A build with no board has not built the primary CRM screen.**

## Fields the form and lists actually name

| Field | Label | Type | Req. | Notes |
|---|---|---|---|---|
| `name` | Opportunity | char | **yes** | the title, `widget="text"` |
| `type` | Type | selection | **yes** | `lead` · `opportunity`, a **badge in the header** |
| `partner_id` | Contact | many2one → `res.partner` | | `widget="res_partner_many2one"`; shown differently for a lead and an opportunity |
| `partner_name` | Company Name | char | | *Extra Info ▸ Company Information* |
| `contact_name` | Contact Name | char | | *Extra Info ▸ Contact Information* |
| `email_from` | Email | char | | `widget="email"` |
| `phone` | Phone | char | | `widget="phone"` |
| `function` | Job Position | char | | |
| `website` | Website | char | | `widget="url"` |
| `street`, `street2`, `city`, `state_id`, `zip`, `country_id` | the address block | char / many2one | | *Extra Info ▸ Company Information* — `state_id` → `res.country.state`, `country_id` → `res.country` |
| `expected_revenue` | Expected Revenue | monetary | | |
| `prorated_revenue` | Prorated Revenue | monetary | | forecast list only |
| `recurring_revenue` | Recurring Revenues | monetary | | **behind `crm.group_use_recurring_revenues`** |
| `recurring_revenue_monthly` | Expected MRR | monetary | | same group |
| `recurring_plan` | Recurring Plan | many2one → `crm.recurring.plan` | | same group |
| `probability` | Probability | float | | beside `automated_probability` and `is_automated_probability` |
| `stage_id` | Stage | many2one → `crm.stage` | | the header status bar, `widget="rotting_statusbar_duration"`, hidden when `type == 'lead'` |
| `date_deadline` | Expected Closing | date | | |
| `date_closed` | Closed Date | datetime | | search only |
| `date_open` | Assignment Date | datetime | | search only |
| `date_conversion` | Conversion Date | datetime | | invisible |
| `priority` | Priority | selection | | `widget="priority"` — the stars |
| `user_id` | Salesperson | many2one → `res.users` | | `widget="many2one_avatar_leader_user"` |
| `team_id` | Sales Team | many2one → `crm.team` | | *Extra Info ▸ Ownership* |
| `tag_ids` | Tags | many2many → **`crm.tag`** | | `widget="many2many_tags"` — **not `res.partner.category`** |
| `lost_reason_id` | Lost Reason | many2one → `crm.lost.reason` | | visible only when `won_status == 'lost'` and the record is an opportunity |
| `won_status` | Won/Lost | selection | | computed; drives the Lost Reason's visibility |
| `campaign_id` · `medium_id` · `source_id` | Campaign · Medium · Source | many2one → `utm.campaign` / `utm.medium` / `utm.source` | | *Extra Info ▸ Marketing* |
| `referred` | Referred By | char | | same group |
| `utm_reference` | UTM Reference | reference | | hidden when empty |
| `description` | Notes | html | | its own **Notes** page |
| `active` | Active | boolean | | invisible on the form |
| `lang_id` | Language | many2one → `res.lang` | | hidden unless more than one language is active |
| `lead_properties` | Properties | properties | | Odoo's dynamic properties, defined per Sales Team |
| `is_rotting`, `rotting_days` | Rotting · Days Rotting | boolean / integer | | computed from the stage's `rotting_threshold_days` |
| `duplicate_lead_count` | Potential Duplicate Lead Count | integer | | the duplicates warning |

## The form, as 19.4 draws it

```
header   stage_id (status bar, hidden for a lead)
title    name (Opportunity)  ·  type badge
         expected_revenue [· recurring_revenue · recurring_plan]  ·  probability
group lead_partner
         partner_id · email_from · phone · lost_reason_id
         user_id · date_deadline · priority · tag_ids · lead_properties
notebook
  Notes        description
  Extra Info
     Company Information   partner_name · street · street2 · city · state_id · zip · country_id · lang_id
     Contact Information   contact_name · function · website
     Marketing             campaign_id · medium_id · source_id · utm_reference · referred
     Ownership             company_id · team_id
chatter
```

## Views

**Ten primary views**, the important ones being `crm.lead.form`, the two lists (`…list.lead`,
`…list.opportunity`), the two searches, `crm.lead.form.quick_create` (the kanban's inline create), and
`crm.lead.view.list.simplified`. The pipeline itself is a **kanban grouped by `stage_id`**.

## What points here

`utm.campaign` counts its leads (`crm_lead_count`); `crm.team` counts assigned opportunities; Sales' quotations
link back to the opportunity. None of that is Phase 2 work.
