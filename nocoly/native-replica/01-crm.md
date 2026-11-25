# 01 CRM: module plan

| | |
|---|---|
| Status | **Approved** 24 Nov 2026 by the Module Owner, with the defaults in §12 (first wave 1 plan; CRM chosen first on 24 Nov). **Phase A built and tested 24 Nov 2026** (`01-crm-build/BUILD-LOG.md`, Acceptance); waiting for the Module Owner's sign-off. Phase B not started |
| Odoo reference | 20.0 open source: `crm`, `sales_team`, `utm` source in the local Odoo 20 container (`odoo20-local`), field lists in `catalogue/odoo-20.0/`, demo data from the local database. Lessons: the September CRM build in ERP Master and its conformance review against Odoo saas~19.4 (`external/ca1phas-odoo-crm/nocoly/worksheets/14-crm-conformance.md`, `reference/odoo-19.4/crm.*.md`) |
| Owner in Nocoly | **By role** (`HANDOVER.md` §2): Module Owner (accountable: plan, decisions, acceptance), Builder (builds and tests), App Administrator (roles, members, deletions), Programme Lead (priorities). Who holds each role is kept outside the repo |
| Depends on | Wave 0 in Odoo Replica (AI): Contacts, Countries, Companies, Currencies, Activities with plans |
| Size | **M**. Phase A (pipeline core) about 3 days with tests; Phase B (scoring, assignment, merge, recurring revenue) about 3 days. Cost drivers: the partner sync, won / lost / restore states, lead conversion, predictive lead scoring |

## 1. Scope

- **Odoo modules covered:** `crm` (app), `sales_team` (foundation: Sales Teams, also needed by Sales), `utm` (foundation: Campaigns, Mediums, Sources). From `calendar`, only the meeting record that CRM links to (§3).
- **Bridges:** none needed now. `sale_crm` (quotations from an opportunity, "won" on confirmation) comes with the Sales plan. `website_crm` is replaced by a native public form now (§4 L12); the full website comes in wave 5.
- **Main flows, as Odoo's menus show them:**
  - **Sales:** My Pipeline (kanban by stage), My Activities, Teams, Customers.
  - **Leads** (when the lead step is on): Leads, convert to an opportunity.
  - **Reporting:** Forecast, Pipeline, Leads, Activities.
  - **Configuration:** Sales Teams, Team Members, Activity Types, Activity Plans, Stages, Tags, Lost Reasons, Recurring Plans.
  - **Link Tracker › UTMs:** Campaigns, Mediums, Sources.
- **Out of scope, with reasons:**
  - Lead mining and enrichment (`crm_iap_mine`, `crm_iap_enrich`): Odoo's paid IAP service.
  - Mail plugins (`crm_mail_plugin`): Outlook / Gmail add-ins.
  - Live chat, SMS marketing, events and surveys bridges: their apps come later (waves 4–5).
  - Lead properties (`lead_properties`): HAP has no per-team dynamic fields, as decided for Contacts in wave 0.
  - The "rainbow man" won animation; mass-mailing blacklist fields.
  - **E-mail to lead** through a mail alias: HAP has no inbound mail (native catalogue, integration §E). The native substitute is a **public form**; an external inbound-mail service is a Phase B option (§12).

**Lessons carried from the September build** (conformance review, 21 Sep): the pipeline board is the primary screen; no invented Status field (won / lost come from the stage and the lost reason); CRM Tags are their own list, not Contact Tags; UTM screens belong to Link Tracker, not CRM; only Odoo's own unique rules (tags, mediums, sources, campaign identifiers); stage not required on input; the address and company block on the lead; seed data from Odoo; Archive / Restore buttons and Archived views wherever there is an Active field; every sheet gets a role row.

## 2. Dependencies and bridges

| Foundation | Use | In Odoo Replica (AI) |
|---|---|---|
| Contacts | Lead customer (`partner_id`), customer created on conversion, address and company copied from the contact | Built, wave 0 |
| Countries / Region | Lead address: native Region field, Country set from it (same as Contacts) | Built |
| Activities, Activity Types, Activity Plans | Activities on leads, Launch Plan on leads, My Activities | Built; extended here |
| Companies, Currencies | Company (hidden), expected revenue in MYR | Built |
| HAP members | Salesperson, Team Leader, team members (`res.users`) | Native |

**Fields this module adds to other modules' sheets** (tagged `crm` in the register, so a split keeps them):

| Sheet (owner) | Field | Why |
|---|---|---|
| Contacts (`base`) | **Opportunities** tab = reverse of the lead's Customer; Opportunity count | `crm/models/res_partner.py` |
| Activities (`mail`) | **Lead / Opportunity** relation `x_crm__lead_id`; Lead option in the document model | Activities on leads |
| Activity Types, Activity Plans (`mail`) | "Leads" option in Applies to (`res_model`) | Plans and suggested types for leads |

## 3. Data model (HAP worksheets)

New menu groups: **CRM** (Pipeline, Leads, Meetings, Reporting page; *Configuration* sub-group: Sales Teams, Team Members, Stages, Lost Reasons, Recurring Plans) and **Link Tracker** (Campaigns, Mediums, Sources, UTM Stages). Helper sheets go to System Tables.

| Odoo model | HAP worksheet | New / reuse | Key fields and relations | Notes |
|---|---|---|---|---|
| `crm.lead` | **Leads / Opportunities** `crm_lead` | new | `name` (title, required), `type` (Lead / Opportunity), `partner_id` → Contacts, `partner_name`, `contact_name`, `email_from` (Email), `phone` (Phone), `function`, `website`, `lang`, address (`street`, `street2`, `zip`, `city`, **Region** `x_base__region`, `country_id` from the Region), `user_id` (Member), `team_id` → Sales Teams, `stage_id` → Stages, `tag_ids` (option set **CRM Tags**), `priority` (Rating, 3 stars), `expected_revenue` (Money MYR), `probability` (%), `automated_probability` (read-only), `prorated_revenue` (formula), `date_deadline`, `won_status` (Won / Lost / Pending, kept by workflows), `lost_reason_id`, `x_crm__lost_feedback` (closing note), `description` (rich text), `active`, `campaign_id` / `medium_id` / `source_id`, `referred`, dates (`date_open`, `date_closed`, `date_last_stage_update`, `date_conversion`), `day_open` / `day_close` (formulas), rotting (`is_rotting`, `rotting_days`), recurring revenue (`recurring_revenue`, `recurring_plan`, monthly and prorated formulas), company (hidden) | Odoo's `type` is kept. Whether the Leads menu is shown is decision 1. Duplicates: native **Query Records** field "Similar Leads" (same e-mail, same customer or same phone, not itself) |
| `crm.stage` | **Stages** | new | `name`, `sequence`, `is_won`, `fold`, `rotting_threshold_days`, `requirements`, `team_ids` → Sales Teams (multi) | Name not unique (Odoo has no constraint) |
| `crm.team` | **Sales Teams** | new | `name`, `sequence`, `active`, `user_id` (Team Leader), `member_ids` (Members, multi), `use_leads`, `use_opportunities`, `assignment_optout`, company (hidden) | `alias_*` (mail alias) not built: no inbound mail. `invoiced_target` comes with Sales |
| `crm.team.member` | **Team Members** | new (Phase B) | `crm_team_id`, `user_id`, `active`, `assignment_max` (leads per 30 days), `lead_month_count` (rollup) | For rule-based assignment |
| `crm.tag` | option set **CRM Tags** | new option set, owned by `sales_team` (Odoo 20 defines `crm.tag` there) | colour per tag, users may add (Odoo lets salespeople create tags) | Odoo's `unique(name)`: option values are unique by nature |
| `crm.lost.reason` | **Lost Reasons** | new | `name` (label "Description"), `active`, `leads_count` (rollup) | |
| `crm.recurring.plan` | **Recurring Plans** | new (decision 2) | `name`, `number_of_months` (≥ 0), `active`, `sequence` | |
| `utm.campaign` | **Campaigns** | new | `title` (Campaign Name, title field), `name` (Campaign Identifier, kept unique by a workflow), `user_id`, `stage_id` → UTM Stages, `tag_ids` (option set UTM Tags), `active`, `crm_lead_count` (rollup) | Kanban by stage is the default view, as in Odoo |
| `utm.stage` | **UTM Stages** | new | `name`, `sequence` | |
| `utm.medium` | **Mediums** | new | `name`, `active` | Duplicate names get " [2]" as in Odoo (workflow), not a refusal |
| `utm.source` | **Sources** | new | `name` | No Active field, as in Odoo |
| `calendar.event` (the part CRM uses) | **Meetings** `calendar_event` | new, owned by `calendar` | `name`, `start`, `stop`, `allday`, `duration`, `user_id` (Organizer), attendees (Contacts multi + Members multi), `location`, `videocall_location`, `description`, tags (option set), `privacy`, `show_as`, `x_crm__lead_id` (`opportunity_id`, tagged `crm`), document model / id / name | HAP's own Calendar cannot link to records (decision 3). Recurrence and reminders: Phase B |
| `crm.lead.scoring.frequency` | **Scoring Frequencies** (System Tables) | new (Phase B) | `variable`, `value`, `team_id`, `won_count`, `lost_count` | For predictive lead scoring |

### Form layouts (rule of 24 Nov: short fields 3–4 per row, dividers, nothing one per row)

**Leads / Opportunities** (Odoo's form: status bar, title, revenue and probability, customer group, Notes and Extra Info pages):
```
row  name 6 | type 3 | priority 3
row  partner_id 6 | expected_revenue 3 | probability 3
row  email_from 4 | phone 4 | date_deadline 4
row  user_id 3 | team_id 3 | tag_ids 6
row  stage_id 4 | won_status 4 | lost_reason_id 4          (Lost Reason shown only when lost)
§ Notes             description 12
§ Company and contact
row  partner_name 6 | contact_name 3 | function 3
row  x_base__region 6 | zip 3 | city 3
row  street 6 | street2 6
row  country_id 3 | website 6 | lang 3
§ Marketing         campaign_id 3 | medium_id 3 | source_id 3 | referred 3
§ Recurring revenue recurring_revenue 4 | recurring_plan 4 | recurring_revenue_monthly 4   (decision 2)
§ Kept up to date automatically
row  prorated_revenue 3 | automated_probability 3 | date_open 3 | date_closed 3
row  date_last_stage_update 3 | date_conversion 3 | rotting_days 3 | next activity date 3
tabs Activities · Meetings · Similar Leads
```
New-record form: only what people fill in (automatic fields hidden on create, as in wave 0).

**Sales Teams:** `name 6 | user_id 3 | sequence 3` · `member_ids 12` · `use_leads 3 | use_opportunities 3 | assignment_optout 3 | active 3` · tabs Team Members, Opportunities.
**Stages:** `name 6 | sequence 3 | is_won 3` · `team_ids 9 | fold 3` · `rotting_threshold_days 3 | requirements 9`.
**Campaigns:** `title 6 | name 6` · `user_id 4 | stage_id 4 | active 4` · `tag_ids 12` · tab Leads.
**Meetings:** `name 6 | start 3 | stop 3` · `allday 3 | duration 3 | user_id 3 | x_crm__lead_id 3` · attendees `12` · `location 6 | videocall_location 6` · `description 12`.
Small lists (Lost Reasons, Recurring Plans, Mediums, Sources, UTM Stages): one row each.

## 4. Business logic (HAP workflows)

| # | Odoo behaviour (method, `crm/models/crm_lead.py` unless noted) | HAP implementation | Platform limit | Mitigation |
|---|---|---|---|---|
| L1 | New record: stage = first unfolded stage for the team (`_compute_stage_id`, `_stage_find`); team from the salesperson (`_compute_team_id`, `sales_team._get_default_team_id`); assignment date when a salesperson is set (`_compute_date_open`); name "<Customer>'s opportunity" when empty (`_compute_name`) | Create / update flow on Salesperson, Team, Customer; queries on Stages and Sales Teams | A query on an empty value stops the run (P33) | Branch before each query; trigger conditions "is not empty" |
| L2 | Customer → lead: company name, contact name, e-mail, phone, function, website, language, address (`_compute_partner_*`, `_prepare_values_from_partner`) | Update flow on Customer | Loops with the Contacts flows | Trigger fields kept narrow; only when the customer changes |
| L3 | Lead e-mail / phone written back to the customer (`_inverse_email_from`, `_inverse_phone`) | Update flow on E-mail, Phone when a customer is set and differs | Two-way sync | Only from the lead to the contact; the contact → lead direction only on a customer change (L2) |
| L4 | Stage change: last stage update date; a won stage forces probability 100 (`_check_won_validity`), won status, closed date; leaving a won stage reverts them (`_compute_won_status`, `_handle_won_lost`) | Update flow on Stage (kanban drag included) | A drag opens no dialog | The flow does it all, so a drag is safe |
| L5 | **Won** button (`action_set_won`): next won stage by sequence, probability 100, active | Button + flow | — | — |
| L6 | **Lost** button (`crm.lead.lost` wizard): lost reason, closing note, archive, probability 0 (`action_set_lost`) | Button with a dialog (Lost Reason, Closing Note) + flow | — | Lost is not a stage, so it is never a kanban column |
| L7 | **Restore** (`action_restore`): active, lost reason cleared, probability = automated probability | Button on lost records + flow | — | — |
| L8 | **Convert to Opportunity** (`action_convert_to_opportunity`, `convert_opportunity`, `_find_matching_partner`, `_create_customer`): type, conversion date, stage; link the contact with the same e-mail or create one (person under the company name) | Button with a dialog (create / link / none, existing customer, salesperson, team) + flow | — | Decision 1: only if the lead step is on |
| L9 | Prorated revenue, monthly recurring revenue, days to assign / close (`_compute_prorated_revenue` …) | **Formula fields** (native), no workflow | — | — |
| L10 | Rotting (`rotting_threshold_days`, `is_rotting`, `rotting_days`) | Daily flow + reset on stage change; view filter "Rotting" | No live "today" in formulas | Daily refresh like the activity states |
| L11 | Activities on leads, plans, next activity on the card | Wave 0 flows with the new Lead link; rollup "next activity date" | — | Launch Plan / Mark Done buttons reused |
| L12 | Web leads (`website_crm`, mail alias `message_new`) | **Public form** on Leads (name, company, contact, e-mail, phone, message) → flow sets type Lead, source / medium "Website", team | No inbound mail | External inbound-mail service in Phase B if needed |
| L13 | Campaign identifier from the title, unique with " [2]" (`utm.mixin._get_unique_names`); same for Mediums and Sources | Create flow that appends " [n]" | A query on an empty value | Trigger condition |
| L14 | Meetings: Schedule Meeting on a lead (`action_schedule_meeting`), next / last meeting on the lead (`_compute_meeting_display`) | Button "Schedule Meeting" (new related Meeting, the pattern fixed in Launch Plan, P38) + flow on meeting save | — | — |
| L15 | **Predictive lead scoring** (`_pls_get_naive_bayes_probabilities`, `_handle_won_lost`, daily `_cron_update_automated_probabilities`) | Phase B: Scoring Frequencies sheet incremented on won / lost; automated probability from the naive Bayes formula on lead change; daily refresh for changed teams | Workflow run volume | Limit the variables (stage, team, country, source, tags), as Odoo's settings do |
| L16 | Rule-based assignment (`crm.team` `_action_assign_leads`, member capacity) and round robin (`_handle_salesmen_assignment`) | Phase B: scheduled flow and an "Assign" button | 100 rows per query | Runs in batches |
| L17 | Merge opportunities (`crm.merge.opportunity`, `_merge_opportunity`, up to 5) | Phase B: batch button on selected records; keep the first by confidence, fill empty fields, move activities and meetings, archive the rest | No transactions | Commit markers; strict serial run |

## 5. User interface

All native. No Compute is planned, because the board, lists, calendar, charts and forms cover CRM; the gaps are listed with their native substitutes.

| Screen / task | Odoo | Native HAP | Gap and substitute |
|---|---|---|---|
| **My Pipeline** (opening screen) | Kanban by stage, quick create per column, folded stages, column totals and activity bar | **Kanban grouped by Stage** (relation), "+" per column creates in that stage, filter salesperson = me, active opportunities; card: name, customer, expected revenue, probability, stars, tags, salesperson, next activity, rotting days | No column totals, no folding: **funnel and number charts per stage** on the CRM page; "show specified items" hides unused stages |
| Pipeline (team), All opportunities, Leads, Lost, Won, Rotting | Lists with filters | Table views with filters | — |
| Forecast | Kanban by expected closing month | **Calendar view** by Expected Closing + bar chart "prorated revenue by closing month" | No grouping by month in kanban |
| Pipeline / Leads / Activities analysis | Pivot and graph views | **CRM page** with native charts: funnel by stage, won / lost by month, by salesperson, by source and campaign, conversion rate, activities by type and state | — |
| Lost dialog, Convert dialog, Schedule Meeting, Launch Plan | Wizards | Button dialogs (fill-in / new related record) | — |
| Meetings | Calendar | Calendar view on Meetings, filter "my meetings" | No sync with Outlook / Google (HAP calendar feed is read-only and not linked) |
| Web enquiry | Website contact form | Public form | — |
| Campaigns | Kanban by stage | Kanban by UTM Stage | — |
| Sales Teams | Dashboard kanban | Gallery / table with counts | No dashboard graphs per team card: charts on the CRM page |

**No-feature-cut checklist:** the register coverage for `crm`, `sales_team` and `utm` must reach 0 OPEN, each field built, native, HAP, later or skipped with a reason (same method as wave 0).

## 6. Roles and permissions

Odoo 20 rights, from `crm/security/ir.access.csv`, `sales_team/…` and `utm/…`:

| Odoo group | Odoo rights | HAP role | HAP rights |
|---|---|---|---|
| Sales / User: Own Documents Only | Leads: create, read, update (no delete) where Salesperson is me **or empty**; Stages, Teams, Lost Reasons: read; Tags: create and update; Campaigns: create, read, update | **Salesperson** | Leads: add, read all, edit own (the Salesperson field gives ownership), no delete; Meetings: own; configuration read-only; may add tags and campaigns |
| Sales / User: All Documents | Leads: create, read, update on all (no delete) | **Sales User** | Leads and Meetings: add, read and edit all, no delete |
| Sales / Administrator | Everything, delete included | **Sales Manager** | All CRM and Link Tracker sheets, configuration |
| Internal user without a sales group | Read stages, teams, lost reasons; campaigns create / read / update; no CRM menu | Employee (wave 0) | No CRM sheets |

A HAP role scope cannot say "own **or empty**", so a salesperson reads all leads and edits their own (decision 5). Roles are created with the V3 call plus app-wide switches (P36, P37) and checked with Role Debug.

## 7. Documents, reports and notifications

- Notification to a salesperson when a lead is assigned to them (Odoo's assignment e-mail).
- Activity reminders: wave 0 (daily state refresh, to-do pilot).
- Scheduled flows: daily rotting refresh; Phase B: scoring refresh and assignment.
- No print templates (CRM has none in Odoo).

## 8. Data

From the local Odoo 20 demo database (`odoo20-local`), loaded by a script like wave 0's:
Only rows owned by the modules this plan covers (`ir_model_data`), as in wave 0:
- `crm`: 4 stages (New 1, Qualified 2, Proposition 3 with 5 days to rot, Won 70), 3 lost reasons, 4 recurring plans, 44 demo leads and opportunities (26 leads, 18 opportunities; 3 won, 5 lost) with their 14 activities;
- `sales_team`: 4 Sales Teams (Sales, Pre-Sales, Website, Point of Sale) and 8 tags with colours. The Kiosk team belongs to `pos_self_order_sale` and waits for POS;
- `utm`: 6 mediums, 14 sources, 2 campaigns (Black Friday Sales, Christmas Special), 4 UTM stages. SMS, Chatbot, "Sale Promotion 1", "Job Campaign" and "Newsletter" belong to later modules.

Test records are named `TEST …` and deleted after each test.

## 9. Acceptance tests

| # | Scenario | Expected (as Odoo 20 does it) | Proof |
|---|---|---|---|
| 1 | "+" in the Qualified column of My Pipeline | New opportunity in Qualified; team from the salesperson; assignment date set | UI + readback |
| 2 | Choose a customer on a new opportunity | Company name, contact name, e-mail, phone, address, language copied; name "<Customer>'s opportunity" if empty | Readback |
| 3 | Change the e-mail on an opportunity with a customer | The contact's e-mail follows | Readback |
| 4 | Drag to Won, then back | Probability 100, Won, closed date; back: Pending, probability back to the automated one | UI + readback |
| 5 | Won button in Proposition | Moves to Won (sequence 70), probability 100 | Readback |
| 6 | Lost button with a reason and a note; then Restore | Archived, probability 0, Lost, reason and note kept, shown in Lost; Restore: active, reason cleared, Pending | UI + readback |
| 7 | Expected revenue 10,000, probability 50 | Prorated revenue 5,000 | UI |
| 8 | Convert a lead: new customer / existing by e-mail / no customer | Type Opportunity, conversion date, stage set, customer created or linked as chosen | Readback |
| 9 | A second lead with the same e-mail | Listed under Similar Leads on both | UI |
| 10 | Proposition (5 days to rot), last stage change 6 days ago | Rotting, days shown; after a stage change, not rotting | Readback |
| 11 | Activity and plan on an opportunity | In its Activities tab and My Activities; next activity date on the card | UI |
| 12 | Schedule Meeting from an opportunity | Meeting in the calendar; next meeting on the opportunity | UI |
| 13 | Public form enquiry | New lead with source and medium Website | Readback |
| 14 | Two campaigns titled "Promo" | Identifiers "Promo" and "Promo [2]"; same rule for mediums and sources | Readback |
| 15 | Salesperson in Pre-Sales creates an opportunity; stage limited to a team | Team Pre-Sales; a team-only stage is offered only to that team | Readback |
| 16 | Roles with Role Debug | Salesperson reads all, edits own, cannot edit configuration; Manager can | UI |
| 17 | CRM page charts | Funnel and totals per stage match the records | UI |
| 18 | Register scan and coverage | Every object owned; `crm`, `sales_team`, `utm` fields 0 OPEN | Register report |
| 19 | Phase B: scoring | Automated probability equals Odoo's for the same history (checked against the local Odoo) | Readback vs Odoo |
| 20 | Phase B: assignment | Unassigned leads shared round robin within capacity | Readback |
| 21 | Phase B: merge 3 opportunities | One remains with the filled fields, activities and meetings moved, the others archived | Readback |

## 10. Register entries

- `crm`: Leads / Opportunities, Stages, Lost Reasons, Recurring Plans, Scoring Frequencies, the CRM page, the fields on Contacts / Activities / Activity Types / Activity Plans / Meetings listed in §2–§3, the CRM workflows and roles.
- `sales_team`: Sales Teams, Team Members, option set CRM Tags.
- `utm`: Campaigns, UTM Stages, Mediums, Sources, option set UTM Tags.
- `calendar`: Meetings (foundation, reused by later apps).

## 11. Work order, effort and risks

**Phase A (about 3 days):**
1. Sheets, option sets and form layouts, checked in the UI (0.5 day).
2. Seed data from the local Odoo (0.25 day).
3. Workflows L1–L14 (1.5 days).
4. Views, CRM page, roles, public form (0.5 day).
5. Acceptance tests 1–18 and the review page (0.5 day).

**Phase B (about 3 days):** scoring L15, assignment L16, merge L17, recurring revenue if chosen, e-mail-in if chosen.

**Risks:**
- Two-way contact sync loops: L2 and L3 keep to narrow triggers, and the test covers both directions.
- Kanban limits: 1,000 records per board, no totals. Boards stay filtered to active opportunities; totals come from charts.
- Workflow volume for scoring: limit the variables and refresh only changed teams.
- CLI traps from wave 0: button targets (P38), roles (P36, P37), empty query values (P33). Each step is checked in the UI.

## 12. Open questions and decisions needed

| # | Question | Decided 24 Nov 2026 (the defaults) | Decides |
|---|---|---|---|
| 1 | **Lead step:** use leads and conversion (Odoo setting "Leads"), or opportunities only (Odoo's default)? | Build both; the Leads menu is shown only when a customer wants the lead step | Module Owner |
| 2 | **Recurring revenues:** now or later? (off by default in Odoo) | Later (Phase B) | Module Owner |
| 3 | **Meetings** as a worksheet with a calendar view (HAP's own calendar cannot link records)? | Yes, owned by `calendar` | Module Owner |
| 4 | **Predictive lead scoring:** Odoo's naive Bayes in Phase B, or a manual probability only? | Phase B, limited variables | Module Owner |
| 5 | **Salesperson visibility:** "read all, edit own" instead of Odoo's "own and unassigned" | Read all, edit own | Module Owner |
| 6 | **E-mail to lead:** public form only, or also an external inbound-mail service? | Public form only | Module Owner with the Programme Lead |
| 7 | **Owner** of CRM in Nocoly | **By role**, not by name: Module Owner, Builder, App Administrator, Programme Lead (`HANDOVER.md` §2), so the module can be handed over | Programme Lead |
