# CRM: everything we know (Odoo 20 → HAP)

For whoever builds, tests or maintains the CRM module of Odoo Replica (AI), or splits it off later. The plan is `../01-crm.md`. This file keeps the facts behind it, with their sources, so nobody has to rediscover them.

Collected 24 Nov 2026. Odoo facts were read from the **Odoo 20 source and database in the local container** unless marked otherwise. HAP facts come from `../native-catalogue/` and the wave 0 build (`../00-foundation-build/BUILD-LOG.md`, `../PLATFORM-ISSUES.md`).

## 1. Sources, and how to re-check them

| Source | Where | What it gives |
|---|---|---|
| Odoo 20 source | container `odoo20-local-odoo-1`, `/usr/lib/python3/dist-packages/odoo/addons/{crm,sales_team,utm}` (start it with `external/odoo20-local/docker-compose.yml`) | Exact behaviour; method names are cited below |
| Odoo 20 database (demo data) | same container, read-only SQL through `../00-foundation-build/step3_export_demo.py` → `rows()` | Seed data and who owns each row (`ir_model_data`) |
| Field catalogue | `reference/odoo20-crm-fields.csv` (362 fields: model, type, relation, stored, computed, label, owner module) | Field-by-field coverage |
| Seed data | `reference/odoo20-crm-seed.json` | Stages, lost reasons, plans, tags, teams, UTM rows, with owner module |
| Access rules | `reference/odoo20-crm-access.csv` | Odoo 20 rights and record rules (Odoo 20 keeps both in `security/ir.access.csv`; there is no `ir_rule` table) |
| September build in ERP Master | `external/ca1phas-odoo-crm/nocoly/` (branch `codex/crm-phase2-handoff`): `CRM-HANDOFF-2026-09-21.md`, `worksheets/14-crm-conformance.md`, `15`–`18`, `reference/odoo-19.4/crm.*.md`, `utm.*.md` | 19 divergences found against Odoo, and the rendered Odoo 19.4 screens (form layout, menus, views) |

## 2. Odoo 20 CRM at a glance

- **Modules:** `crm` (app), `sales_team` (foundation: teams, team members, **tags**), `utm` (foundation: campaigns, mediums, sources, UTM stages and tags), plus `calendar` for meetings. Bridges that come later: `sale_crm` (with Sales), `website_crm`, `crm_sms`, `crm_livechat`, `event_crm`, `survey_crm`, `mass_mailing_crm`; paid IAP: `crm_iap_mine`, `crm_iap_enrich`.
- **Menus:**
  - Sales: My Pipeline, My Activities, Teams, Customers.
  - Leads (only with the Leads setting).
  - Reporting: Forecast, Pipeline, Leads, Activities.
  - Configuration: Settings, Sales Teams, Teams Members, Activity Types, Activity Plans, Pipeline (Stages, Tags, Lost Reasons), Recurring Plans (with that setting), Lead Generation.
  - Campaigns, Mediums and Sources sit under **Link Tracker › UTMs**, not under CRM.
- **Settings (feature switches):**
  - **Leads**: `crm.group_use_lead`, off by default. With it off, `type` is always "opportunity" and the lead menus and views are hidden.
  - **Recurring Revenues**: `crm.group_use_recurring_revenues`, off by default. It hides the recurring fields and the Recurring Plans menu.
  - **Predictive Lead Scoring**: always computing. Its variables live in the `crm.pls_fields` parameter (default `phone_state,email_state,state_id,country_id,source_id,lang_id,tag_ids`, plus stage and team always) and its start date in `crm.pls_start_date`.
  - **Rule-based assignment**: a scheduled job, or manual.
  - **Multi-team membership**: `sales_team.membership_multi`.
- **The opening screen** is the pipeline: a kanban of opportunities grouped by `stage_id`. Each column has a quick-create, unused stages fold behind "»", column totals of expected revenue appear, and an activity progress bar runs on each column.

## 3. Models and the fields that matter

Full list: `reference/odoo20-crm-fields.csv`. The form of an opportunity, as Odoo 19.4 / 20 draws it (`reference/odoo-19.4/crm.lead.md` in the September repo):

```
header   stage (status bar; hidden for a lead)
title    name ("Opportunity") · type badge
         expected_revenue [· recurring_revenue · recurring_plan] · probability
group    partner_id · email_from · phone · lost_reason_id (only when lost)
         user_id · date_deadline · priority (stars) · tag_ids · lead_properties
notebook Notes (description)
         Extra Info: Company Information (partner_name, street, street2, city, state_id, zip, country_id, lang_id)
                     Contact Information (contact_name, function, website)
                     Marketing (campaign_id, medium_id, source_id, utm_reference, referred)
                     Ownership (company_id, team_id)
```

| Model (owner) | Key fields | Notes |
|---|---|---|
| `crm.lead` (crm) | `name` (required), `type` (lead / opportunity, required), `partner_id`, `partner_name`, `contact_name`, `email_from`, `phone`, `function`, `website`, `lang_id`, address (`street`, `street2`, `zip`, `city`, `state_id`, `country_id`), `user_id`, `team_id`, `stage_id`, `tag_ids` → `crm.tag`, `priority` (0–3), `expected_revenue`, `probability`, `automated_probability`, `prorated_revenue`, `date_deadline` (Expected Closing), `date_open`, `date_closed`, `date_last_stage_update`, `date_conversion`, `day_open`, `day_close`, `won_status`, `lost_reason_id`, `description`, `active`, `campaign_id` / `medium_id` / `source_id`, `referred`, `recurring_revenue`, `recurring_plan`, recurring monthly / prorated, `is_rotting`, `rotting_days`, `duplicate_lead_ids`, `calendar_event_ids`, `company_id` | `_order = "priority desc, id desc"`. **No unique constraint.** Stage is not required on input |
| `crm.stage` (crm) | `name`, `sequence`, `is_won`, `fold`, `rotting_threshold_days` ("Days to rot", 0 = off), `requirements` (tooltip), `team_ids` (empty = every team) | No unique name |
| `crm.team` (sales_team) | `name`, `sequence`, `active`, `user_id` (Team Leader), `member_ids`, `crm_team_member_ids`, `use_leads`, `use_opportunities`, `assignment_optout`, `assignment_domain`, `assignment_max` (sum of members), mail alias fields, `company_id` | No unique name |
| `crm.team.member` (sales_team) | `crm_team_id`, `user_id`, `active`, `assignment_max` (leads per 30 days), `assignment_domain`, `assignment_domain_preferred`, `lead_day_count`, `lead_month_count` | Capacity for assignment |
| `crm.tag` (**sales_team**) | `name` (unique), `color` (1–11, random default) | Salespeople may create tags |
| `crm.lost.reason` (crm) | `name` (label "Description"), `active`, `leads_count` | No unique name |
| `crm.recurring.plan` (crm) | `name`, `number_of_months` (check ≥ 0), `active`, `sequence` | |
| `utm.campaign` (utm) | `title` (Campaign Name), `name` (Campaign Identifier: computed from the title, required, **unique**), `user_id`, `stage_id` → `utm.stage` (required, kanban groups by it), `tag_ids` → `utm.tag`, `active`, `crm_lead_count` | |
| `utm.medium` / `utm.source` (utm) | `name` **unique**; medium has `active`, source has **no** `active` | |
| `res.partner` (+crm) | `opportunity_ids` (opportunities of this contact), `opportunity_count` | |
| `calendar.event` (+crm) | `opportunity_id` | Meetings scheduled from an opportunity |
| `crm.lead.scoring.frequency` (crm) | `variable`, `value`, `team_id`, `won_count`, `lost_count` | The scoring table |

## 4. Behaviour, rule by rule

All in `crm/models/crm_lead.py` unless stated.

**Status**
- **Won / lost / pending** (`_compute_won_status`): *won* = probability 100 **and** stage `is_won`; *lost* = **not active and probability 0**; otherwise *pending*. Constraint `_check_won_validity`: a lead in a won stage must have probability 100.
- **Writing a stage** (`write`):
  - any stage change sets `date_last_stage_update` = now;
  - entering a won stage sets `active = True`, `probability = 100`, `automated_probability = 100`.
- **Writing a salesperson:** changing the salesperson sets `date_open` = now; removing it clears `date_open`.
- **Closed date:** set when probability ≥ 100 or the record is archived. Cleared when probability > 0, or when the stage changes to a non-won stage and the probability is not written.
- **Leaving a won stage:** `_compute_probabilities` re-runs. When the probability was automated (equal to the automated value), it follows the new automated value.

**Buttons**
- **Won** (`action_set_won`): unarchive, then move to the first won stage with a higher sequence than the current one (else the nearest lower one), probability 100.
- **Lost** (wizard `crm.lead.lost`): lost reason plus a "Closing Note" (HTML, posted in the chatter); then `action_set_lost` archives and sets probability 0 and automated probability 0.
- **Restore** (`action_restore`): unarchive, clear the lost reason, probability = automated probability. Plain **unarchive** also clears the lost reason and recomputes probabilities.

**Defaults on a new record**
- **Stage** (`_compute_stage_id`, `_stage_find`): when empty, or when it does not belong to the team, take the first **unfolded** stage by sequence among stages with no team or with this team.
- **Team** (`_compute_team_id`, `sales_team` `_get_default_team_id`): when a salesperson is set and is not in the current team, pick in this order:
  1. their team matching `use_opportunities` (or `use_leads` for a lead);
  2. any of their teams;
  3. the default from the context;
  4. a team of the company matching the domain;
  5. any team of the company.
- **Name** (`_compute_name`): "<customer name>'s opportunity" when empty and a customer is set.

**Customer sync**
- **Customer → lead** (`_compute_contact_name`, `_compute_partner_name`, `_compute_function`, `_compute_website`, `_compute_lang_id`, `_compute_partner_address_values`, `_compute_email_from`, `_compute_phone`): choosing a customer fills company name, contact name, job position, website, language, the whole address (all or none), e-mail and phone.
- **Lead → customer** (`_inverse_email_from`, `_inverse_phone`): editing the e-mail or phone on the lead writes it back to the customer when they differ (`partner_email_update` / `partner_phone_update` warn first in the form).

**Computed values**
- **Revenue:**
  - prorated = expected × probability / 100 (rounded to 2 decimals);
  - monthly recurring = recurring / plan months (1 when no plan);
  - monthly prorated = monthly × probability / 100;
  - prorated recurring = recurring × probability / 100.
- **Day counters:** `day_open` = days from creation to assignment; `day_close` = days from creation to closing.
- **Rotting:** only pending opportunities, when the stage's `rotting_threshold_days` > 0 and the time since the last stage update exceeds it.
- **Duplicates** (`_compute_potential_lead_duplicates`): the same e-mail domain criterion or normalised e-mail, the same customer, or the same sanitised phone.

**Conversion and merging**
- **Lead → opportunity** (`action_convert_to_opportunity`, `convert_opportunity`, `_convert_opportunity_data`):
  - Sets `type` opportunity and `date_conversion` = now; sets the stage of the team if empty; skips inactive or won leads.
  - Customer (`_handle_partner_assignment`): the contact with the same e-mail (`_find_matching_partner`), otherwise a new one (`_create_customer`). It is a person named after the contact name, under the existing customer company if any. Without a contact name, the existing company or a contact named after the lead.
  - The new contact gets e-mail, phone, function, address, website, language and the lead's notes.
- **Salesperson assignment** (`_handle_salesmen_assignment`): with several salespeople, leads are dealt round robin.
- **Merge** (`crm.merge.opportunity`, `_merge_opportunity`, at most 5 records):
  - Records are ranked by confidence (`_sort_by_confidence_level`): active before lost, opportunity before lead, then higher stage sequence, higher probability, newer id.
  - Fields take the first non-empty value; descriptions are concatenated; followers, attachments, meetings, activities and messages move to the kept record; the others are deleted.

**Meetings**
- `action_schedule_meeting` opens a calendar event linked by `opportunity_id`.
- `_compute_meeting_display` shows the next future meeting, else the last one ("Next Meeting" / "Last Meeting" / "No Meeting").

**Predictive lead scoring (PLS)**
- `_pls_get_naive_bayes_probabilities` uses naive Bayes over frequency rows (`crm.lead.scoring.frequency`), counted per team and globally.
- The variables are stage (counted for every stage passed), team, and the `crm.pls_fields` list.
- Counts are incremented and decremented by `_handle_won_lost` when a lead becomes won or lost, or leaves those states. A daily cron (`_cron_update_automated_probabilities`) refreshes the automated probability.
- A manual probability stays manual until "Restore" or a reset.

**Assignment** (`crm_team.py` `_action_assign_leads`, `_allocate_leads`, members)
- Unassigned live leads (no team, no salesperson; created in the last 7 days by default; matching the team's domain) go to teams by a random choice weighted by each team's capacity (`assignment_max`).
- Duplicates are merged on the way.
- Inside a team, members receive leads within their 30-day capacity and their domains.

**UTM**
- `utm.mixin._get_unique_names` appends " [2]", " [3]" to a duplicate medium, source or campaign name **instead of refusing it**.
- A campaign's identifier is computed from its title the same way.

## 5. Who may do what in Odoo 20 (`reference/odoo20-crm-access.csv`)

| Group | `crm.lead` | Stages, Lost Reasons, Teams | Tags | Campaigns |
|---|---|---|---|---|
| Sales / User: Own Documents Only | create, read, update where **salesperson is me or empty**; no delete | read | create, read, update | create, read, update (every internal user) |
| Sales / User: All Documents | create, read, update all; no delete | read | create, read, update | same |
| Sales / Administrator | everything | everything | everything | same |
| Multi-company rule | company in the user's companies or empty | | | |

## 6. Seed and demo data (local Odoo 20, `reference/odoo20-crm-seed.json`)

| Data | Rows (owner module) |
|---|---|
| Stages (`crm`) | New 1, Qualified 2, Proposition 3 (**5 days to rot**), Won 70 (won); none folded |
| Lost reasons (`crm`) | Too expensive; We don't have people/skills; Not enough stock |
| Recurring plans (`crm`) | Monthly 1, Yearly 12, Over 3 years 36, Over 5 years 60 |
| Tags (`sales_team`) | Product, Software, Services, Information, Design, Training, Consulting, Other (colours 1–8) |
| Sales Teams | `sales_team`: Sales, Pre-Sales, Website, Point of Sale. `pos_self_order_sale`: Kiosk Sale Team (later) |
| UTM (`utm`) | Mediums: Phone, Direct, Website, Social Media, Messaging, Email (SMS belongs to `mass_mailing_sms`). Sources: 14 (Google, Mass Mailing, Newsletter, Monster, Glassdoor, Craigslist, Survey, Referral, Livechat, Facebook, X, LinkedIn, Instagram, YouTube); Chatbot, Mass SMS and Sale Promotion 1 belong to later modules. Campaigns: Black Friday Sales, Christmas Special. UTM stages: New, Schedule, Design, Sent |
| Leads (`crm` demo) | 44: 26 leads, 18 opportunities; 3 won, 5 lost; 14 activities |

## 7. HAP: what native gives, and the traps

**Native fits:**
- **Pipeline:** a kanban grouped by the Stage relation; "+" per column creates in that stage; the card shows chosen fields; record colour comes from an option field.
- **Duplicates:** a **Query Records** field (type 51) lists matching records live.
- **Revenue:** formula fields; next activity date as a rollup.
- **Web leads:** a public form (no sign-in).
- **Meetings:** a worksheet with a calendar view.
- **Reports:** native charts (funnel, number, bar) on a custom page.
- **Tags:** an option set with colours that users may extend.

**Gaps and substitutes:**
- **Kanban:** no column totals or progress bars, so totals come from charts; no folded stages, so use "show specified items"; a drag opens no dialog, so Lost is never a column and flows do the stage rules.
- **No inbound e-mail:** a public form, or an external inbound-mail service posting to a webhook.
- **HAP Calendar cannot link to records:** Meetings is a worksheet.
- **A role scope cannot say "own or empty":** salespeople read all and edit their own.
- **No live "today" in formulas:** rotting is refreshed by a daily flow.

**Traps met in wave 0 that apply here** (details in `../PLATFORM-ISSUES.md`):

| Issue | Trap | Workaround |
|---|---|---|
| P38 | A button that creates a related record, made by the CLI, saves no target and does nothing | Set "In the current record → Create <relation>" and "Always" in the button editor, then press it in the UI |
| P36, P37 | Per-sheet role rights cannot be changed by the CLI; `create-fine` turns every app-wide switch off | Create roles with the V3 call plus `globalPermissions` (`../00-foundation-build/step7_roles.py`) |
| P33 | A query whose filter value is empty fails the whole run | Trigger conditions "is not empty", or a branch before the query |
| P22 | "Relation is not empty" cannot be written by the CLI | Write the stored condition (`conditionId` 31) |
| P23 | Branch paths lose their names | Rename them |
| P25 | Function steps round to integers | Set 6 decimals |
| P27 | "Clear a field" is dropped | Raw save with `isClear` |
| P29 | Formula errors give empty results | — |
| P30 | Steps after a branch cannot read inside it | — |
| — | Records made by a workflow get no field defaults | Set Active and similar explicitly |
| — | A deleted record still blocks unique values (P26) | — |
| — | Forms | `../00-foundation-build/step9_form_layouts.py` (rows on a 12-column grid; `fieldPermission` "100" / "110" for hidden on create). A single-select shown as a dropdown is field type 11 (the designer switches 9 → 11) |

## 8. Lessons from the September CRM build (ERP Master, 18–21 Sep)

The conformance review found 19 divergences, 5 that mattered. Its findings are built into this plan:

1. The pipeline board was missing: it is the primary screen.
2. An invented "Status" field gave two sources of truth: `won_status` is derived.
3. A Recurring Plans sheet existed while the feature was off, with nothing pointing at it.
4. UTM sheets sat in the CRM menu; Campaigns lacked its required stage and tags.
5. Fields added later stayed at row 9999.
6. No role decisions had been made: HAP's default applied.

Data and fields:
- **Unique flags** belong only to `crm.tag`, `utm.medium`, `utm.source` and the campaign **identifier**.
- **Missing on the lead:** the address and company block, job position, website and language.
- **Stage** must not be required.
- **Tags** are CRM Tags, not Contact Tags.
- **Seed data** must be taken from Odoo; a "testtest" tag broke the TEST naming rule.

Screens: Archive / Unarchive buttons and Archived views wherever there is an Active field.

## 9. Decisions (24 Nov 2026, approved with the plan's defaults)

| # | Decision | Why |
|---|---|---|
| 1 | Build leads **and** opportunities; show the Leads menu only when a customer wants the lead step | Same as Odoo's setting, no feature cut |
| 2 | Recurring revenue in Phase B | Off by default in Odoo |
| 3 | Meetings as a worksheet owned by `calendar` | HAP Calendar cannot link to records |
| 4 | Predictive lead scoring in Phase B, with Odoo's default variables | Workflow volume; Odoo's own default list |
| 5 | Salesperson: read all, edit own | HAP roles cannot express "own or empty" |
| 6 | Web leads by public form only | No inbound e-mail in HAP |
| 7 | Ownership **by role** (Module Owner, Builder, App Administrator, Programme Lead) | Easier handover (`../HANDOVER.md` §2) |

## 10. Words used

| Odoo | Here |
|---|---|
| Lead / Opportunity | one record type with Type; the pipeline shows opportunities |
| Pipeline | the kanban by stage |
| Won / Lost / Pending | `won_status`, derived, read-only |
| PLS | predictive lead scoring: the automated probability |
| UTM | campaign / medium / source attribution |
