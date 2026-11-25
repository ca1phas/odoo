# CRM Phase A: build log

Plan: `../01-crm.md` (approved 24 Nov 2026 with the §12 defaults). App: Odoo Replica (AI). Ledger: `ids.json` (private).
Roles as in `../HANDOVER.md` §2: the Builder built and tested; the Module Owner signs off.

## Status

| Step (plan §11) | Status | Evidence |
|---|---|---|
| 1 Sheets, option sets, form layouts | Done, **checked in the UI** (new-record form) | "Sheets and layouts" below |
| 2 Seed data | Done, read back | "Seed data" below |
| 3 Workflows L1–L14 | Built and published; all pass their API checks after the 24 Nov evening fixes (P41, P42, "is any of") | "Workflows" and "Acceptance" below |
| 4 Views, CRM page, roles, public form | Done, checked in the UI | "Screens, rules, roles, public form" below |
| 5 Acceptance tests 1–18, review page | Done 24 Nov 2026 (see "Acceptance"): API checks pass after 5 fixes; UI tests 1, 4, 6, 9, 11–13, 16, 17 pass; register 0 unresolved, coverage OPEN 0. Review page <private review page> (source `crm-review.html`) | "Acceptance" below |

## Sheets and layouts (24 Nov 2026, from about 13:40)

Scripts: `crmlib.py` (the wave 0 helpers with this ledger), `step1_sheets.py`, `step1b_layouts.py`.

| Group | Sheets (alias, owner) |
|---|---|
| CRM | Leads / Opportunities (`crm_lead`, crm, 49 fields), Meetings (`calendar_event`, calendar, 17) |
| CRM › Configuration | Sales Teams (`crm_team`, sales_team), Stages (`crm_stage`, crm), Lost Reasons (`crm_lost_reason`, crm) |
| Link Tracker | Campaigns (`utm_campaign`), Mediums (`utm_medium`), Sources (`utm_source`), UTM Stages (`utm_stage`), all utm |

- **Option sets:** CRM Tags (8, Odoo's colours, owned by sales_team), UTM Tags (Marketing), Meeting Tags (5, calendar).
- **Two-way relations:** lead Customer ↔ Contacts "Opportunities" (`opportunity_ids`); lead Sales Team ↔ Sales Teams "Opportunities"; lead Lost Reason ↔ Lost Reasons "Leads" (with the Leads Count rollup); lead Campaign ↔ Campaigns "Leads" (Leads Count).
- **Bridge fields on wave 0 sheets (owned by crm):** Activities and Plan Launches "Lead / Opportunity" (`x_crm__lead_id`, two-way: the lead's Activities tab and its Plan Launches tab, which the Launch Plan button fills); Meetings "Opportunity" (`opportunity_id`, Odoo's name; the lead's Meetings tab); option "Leads" in Applies to of Activity Types and Activity Plans.
- **Formula:** Prorated Revenue = expected revenue × probability / 100 (native number formula).
- **Deviations from the plan's first draft, on purpose:**
  - the lead's Region is `x_crm__region` (owner crm), not `x_base__region`;
  - the lead name is optional (Odoo names an unnamed lead "<customer>'s opportunity"); a validation rule keeps name-or-customer (step 4);
  - Days to Assign / Close and Duration are numbers written by flows (date differences), not formula fields;
  - the Leads view question (decision 1) is a view, not a menu: leads and opportunities share one sheet, as in Odoo.
- **Layouts:** short fields 3–4 per row, dividers (Notes, Company and contact, Marketing, Kept up to date automatically), the automatic fields read-only and off the new-record form. Field descriptions show as an ⓘ tooltip (`advancedSetting.hinttype` "1", found by setting it once in the designer), so rows stay aligned. Checked in the UI on the new-record form.
- **Platform issue found:** an option added with `field.update` without a key is stored with an empty key (P39). Fixed by giving the "Leads" options a key; the script now does.

## Seed data (24 Nov 2026, about 14:10)

`step2_seed.py export` (read-only SQL on the local Odoo 20) → `data/crm-demo.json`; `load` → the sheets. Only rows owned by crm, sales_team and utm (`ir_model_data`), exactly as plan §8:

| Data | Rows |
|---|---|
| UTM stages, mediums, sources, campaigns | 4, 6, 14, 2 |
| Sales Teams | 4 (Sales, Pre-Sales, Website, Point of Sale) |
| Stages, lost reasons | 4 (New 1, Qualified 2, Proposition 3 with 5 days to rot, Won 70), 3 |
| Leads and opportunities | 44: 22 pending leads, 4 lost leads, 14 pending opportunities, 3 won, 1 lost (5 archived) — read back, same as Odoo |
| Activities on leads | 14 (states from the wave 0 flow: 5 overdue, 5 planned, 4 today) |

- Odoo's demo users do not exist in HAP: salespeople, the Sales leader and activity owners are the build account; Pre-Sales is loaded without members (its demo member is Marc Demo).
- One lead customer, OpenWood (a base demo person), is not in Contacts; that lead keeps its company name with no customer.
- The fields the flows maintain (won status, dates, day counters) keep Odoo's values. The CLI refuses to write fields hidden on the new-record form, so leads and activities were written with `--ignore-rules` (as a workflow writes).

## Workflows (24 Nov 2026, 14:30–15:45)

Scripts: `crmwf.py` (helpers and raw patches), `step3_wf_core.py`, `step3b_buttons.py`, `step3c_activities.py`, `step3d_meetings_rotting.py`, `step3e_utm.py`. Every flow is published; names start with "CRM - ", "UTM - " or "Meetings - " (register prefixes).

| # | Flow | Odoo | Notes |
|---|---|---|---|
| F1 | CRM - New lead defaults | `_compute_team_id`, `_compute_stage_id`, `_compute_date_open` | team from the salesperson (`_get_default_team_id` order: their teams matching the type first, then any active team), then the team's first unfolded stage |
| F2 | CRM - Customer details | `_compute_partner_*`, `_compute_name` | company, contact, job, website, e-mail, phone, language, whole address (all or none), "<customer>'s opportunity" |
| F3 | CRM - E-mail and phone to the customer | `_inverse_email_from`, `_inverse_phone` | only lead → customer |
| F4 | CRM - Stage rules | `write()`, `_compute_won_status` | won stage: 100 / 100 / active / Won / closed date (kept when already won); other stage: Pending, closed date cleared |
| F5 | CRM - Salesperson changes | `write()`, `_compute_team_id` | assignment date; team when the salesperson is not its leader or member |
| F6 | CRM - Team changes | `_compute_stage_id` | stage kept when it belongs to every team or this one |
| F7 | CRM - Country from Region | as Contacts | |
| F8 | CRM - Day counters | `_compute_day_open`, `_compute_day_close` | whole days, as Odoo |
| B | Won, Lost (dialog), Restore, Convert to Opportunity | `action_set_won`, `crm.lead.lost`, `action_restore`, `action_convert_to_opportunity` | buttons with their flows; Schedule Meeting and Launch Plan are related-record buttons (finished in the button editor, P38) |
| A1 | CRM - Activity on a lead | — | keeps the Lead link and the document fields in step |
| A2 | CRM - Launch plan on a lead | plan launch | the wave 0 launch logic, for a lead; the wave 0 flow now starts only when the launch has a contact (A3) |
| R1, M1–M3, D1 | Refresh a lead, Meetings - Duration, Meeting changed / deleted, Daily refresh | `_compute_meeting_display`, `_compute_rotting` | a hidden helper, Refreshed At, carries "now": the daily flow stamps it in one batch, R1 recomputes |
| U1–U4 | UTM unique names, campaign identifier | `_get_unique_names`, `_compute_name` | smallest free " [n]" up to [5] |

- **Odoo 20 differs from the plan here:** Convert to Opportunity has **no dialog** in Odoo 20 (the single-lead wizard is gone): it links the contact with the same e-mail or creates one from the lead, then sets type, conversion date and a stage. Built that way.
- **Phase A limit:** the automated probability is not recomputed (lead scoring is phase B). Leaving a won stage therefore keeps probability 100 until then; Restore sets the probability to the automated one (0 after a loss).
- **CLI findings:**
  - a function step's result must be read as `string_fx_id`, also into a number field; `number_fx_id` from a function step is refused at publish;
  - a condition on a related-record step needs its field type stated;
  - query filters are OR-of-AND only;
  - a whole-step save clears every setting it does not name;
  - a path's stored condition is in the flow map, not in `node get`.
- **API checks** (`acceptance_crm_core.py`, TEST records deleted afterwards): T1 defaults, T2 customer details, T3 e-mail to the customer, T4 won and back, T5 team change keeps the stage, T6 salesperson removed and set again — **8 of 8 pass**.
- **W1 CRM - Web enquiry** (`step3f_webform.py`): public-form records carry Creator `user-publicform` (shown as Public Form); the flow starts on that and sets type Lead, medium Website, team Website. Tested with two TEST enquiries through the live form (deleted).

## Screens, rules, roles, public form (24 Nov 2026, 15:40–17:00)

- **Fields made in the designer** (the CLI cannot make them reliably), then read back and recorded:
  - **Next Activity** `activity_date_deadline`: rollup of the Activities tab, Due Date, **Earliest**, only active activities (raw: `enumDefault` 3, `enumDefault2` 15, `advancedSetting.filters` on Active).
  - **Similar Leads** `duplicate_lead_ids`: Query Records on the same sheet, three OR-groups (same e-mail / customer / phone) each with Record ID ≠ this record; empty values give no results for that group (`emptyRule` 3); shown as a tab. Checked in the UI on "5 VP Chairs": lists "Customizable Desk" (same customer and e-mail), not itself.
  - **Stage picker** limited to stages of every team or of the record's team (Odoo's `stage_id` domain).
- **Contacts:** Opportunities tab and **Opportunities Count** (rollup, all leads and opportunities, archived included; Odoo also counts the contact's people).
- **Rules** (`step4_rules.py`): Lost Reason and Closing Note show only on archived records; the form refuses a record with neither name nor customer (form only).
- **Buttons:** Schedule Meeting and Launch Plan finished in the button editor (P38): "In the current record → Create Meetings / Plan Launches", Always active.
- **Views** (`step4_views.py`): My Pipeline (board by stage, my open opportunities: the opening view), Pipeline, All, Leads, Forecast (calendar by expected closing), Won, Lost, Rotting, Archived; Meetings Calendar; Campaigns board by UTM stage. Board columns follow the stage sequence (`advancedSetting.navsorts`, set once in the view settings and read back); cards show customer, revenue, probability, stars, tags, salesperson, next activity. Checked in the UI.
- **Reporting page** (`step4_page.py`, CRM › Reporting): open opportunities and expected revenue (numbers), Won / Lost / Pending, pipeline funnel and revenue by stage (stage order: chart `sorts` = [{stage field: row ids}], set once in the chart editor), forecast by closing month, revenue by salesperson, leads by source and campaign, activities on leads by type. Checked in the UI: 14 open opportunities, 296,400 expected, funnel New 3 / Qualified 5 / Proposition 6, Won 3 / Pending 14 / Lost 1 — all match the records.
- **Roles** (`step4_roles.py`, owned by sales_team, V3 create with the app switches as wave 0): Salesperson (leads: read all, edit own, no delete; configuration read-only; campaigns, mediums, sources add and edit), Sales User (edit all, no delete), Sales Manager (everything on CRM and Link Tracker). The lead's Salesperson and the meeting's Organizer are now "Owner (edit and delete)" members (`userPermission` 2), so "own" follows them.
- **Public form** on Leads (Extend › Public Form): Opportunity, Email, Phone, Notes, Company Name, Contact Name; the field descriptions do not show there. Live link not shared.
- **Platform issue found:** the CLI's range pre-check on a relation ignores an "is empty" group of the selection limit and refuses stages the form offers (P40); tests write stage changes with `--ignore-rules`.

## Acceptance (24 Nov 2026, 16:30–23:00)

Scripts: `acceptance_crm_core.py` (T1–T6, 8 checks) and `acceptance_crm.py` (plan tests 2–15, 29 checks), both with TEST records deleted at the end. **Final run (24 Nov, 22:15–22:55): 8 of 8 and 29 of 29 pass** (`python acceptance_crm.py cleanup`); the UI tests used TEST records deleted right after. Logs: `backups/acceptance-run*.log` (private).

| # | Test (plan §9) | Result | Proof |
|---|---|---|---|
| 1 | "+" in the Qualified column | Pass: Qualified, team from the salesperson, assignment date | UI + readback (afternoon) |
| 2, 3 | Customer details copied; e-mail back to the contact | Pass | Readback |
| 4 | Drag to Won, then back | Pass in the UI and by API: Won, probability 100, closed date; back to Qualified: Pending, closed date cleared. Probability stays 100 (phase A has no lead scoring, so no automated probability to return to) | UI + readback |
| 5 | Won button in Proposition | Pass after fix 1 (Won stage, sequence 70) | Readback |
| 6 | Lost with reason and note; Restore | Pass after fix 4: the dialog asks Lost Reason and Closing Note; archived, probability 0, Lost, shown in the Lost view; Restore: active, reason cleared, Pending | UI + readback |
| 7 | Prorated revenue | Pass (10,000 × 50 % = 5,000) | Readback |
| 8 | Convert a lead: contact with the same e-mail / new contact / named after the lead | Pass (Odoo 20 has no dialog) | Readback |
| 9 | Same e-mail on two leads | Pass: each lists the other under Similar Leads, not itself; a lead with no e-mail, customer or phone lists none | UI |
| 10 | Rotting after 6 days in Proposition; not after a stage change | Pass | Readback |
| 11 | Activity and plan on an opportunity | Pass: in its Activities tab and in My Activities; next activity date on the card | UI + readback |
| 12 | Schedule Meeting | Pass: the button opens a meeting with the opportunity filled in; 10:00–11:30 gives duration 1.50 (fix 3); in the Meetings calendar; Next Meeting on the opportunity | UI + readback |
| 13 | Public form enquiry | Pass: Lead, medium Website, team Website (source stays empty, as in Odoo without UTM cookies) | Live form + readback (afternoon) |
| 14 | Two campaigns "TEST Promo"; mediums and sources | Pass: "TEST Promo", "TEST Promo [2]"; same for mediums and sources when added one after the other | Readback |
| 15 | Salesperson's team; team-only stage; stage shared by two teams | Pass after fixes 1 and 2 | Readback |
| 16 | Roles with Role Debug | See "Roles" below | UI |
| 17 | CRM page charts | Pass (afternoon): totals and funnel match the records | UI |
| 18 | Register and coverage | Pass: scan 2026-11-24-1732, 755 objects, 0 without owner (after recording 3 wave 0 dividers, below); coverage of base, contacts, uom, product, mail, crm, sales_team, utm: built 336, skip 163, later 78, HAP 55, native 45, **OPEN 0** | Register report |

**Fixed because of the tests**
1. **OR filters ignored (P41).** Query steps whose filter has OR groups ran as if they had no filter and took the first record by the sort: the Won button picked New, and a new lead got another team's stage. Cause: the CLI writes a get-single filter in the old condition slot. All 13 such steps (5 flows) moved to the grouped slot, as the editor's own switch does; `crmwf.group_filters()` now runs before every publish.
2. **"Equals" on Sales Teams compares the whole set.** A stage of two teams did not match either team. Odoo's `team_ids = team` means "includes it", the designer's **is any of** (33). Changed in every query and branch (`crmwf.multi_relation_any()`, also run before every publish); test 15d added.
3. **Meeting duration 0 (P42).** hap-cli's unit numbers differ from the product's: "hour" was stored as Month. The step now counts minutes (set raw, `crmwf.save_compute`) and the duration is minutes / 60, because a difference in hours is whole hours only.
4. **Empty Lost dialog.** The rule "Lost reason when archived" also applies inside the button dialog, which opens on an active record, so it hid both fields. The rule is turned off (kept, not deleted); Lost Reason and Closing Note now always show on the form. Deviation from Odoo's form, which hides Lost Reason on active records.
5. **Test tooling.** The core tests write with `--ignore-rules` (P40), and test 14 adds the second medium or source after the first is processed (two creates in the same second race, each flow seeing the other).

Also found by the register: three section dividers made by the wave 0 layout step ("Current rate" on Currencies, "Applies to" and "Price computation" on Pricelist Rules) were never recorded because their `add-fields` call had timed out (P10). Recorded now in the wave 0 ledger.

**Roles (test 16, Role Debug, 24 Nov 22:30–23:00)**
- **Salesperson:** sees every opportunity on the boards; can add leads; edits its own (Salesperson = the user; HAP also counts the creator, so in this build, where the loader created every seed record, all seed records count as "own" for the build account); no Delete in the record menu; Stages, Sales Teams and Lost Reasons read-only with no Add button.
- **Sales Manager:** Stages has the Add button and edits.
- **Found and fixed:** the CRM Reporting page was hidden from all three sales roles (roles were created with no page rights). Odoo opens CRM › Reporting to salespeople, so the page is now on for all three, through V3 `PATCH` with the full role body and a key-by-key comparison before and after (`step4_roles.py`, `grant_pages`). Checked again with Role Debug: the Salesperson sees the page with the same totals.
- **Found, not fixed (platform):** the role editor shows these roles' per-sheet rights as view / edit / delete All although the stored rights and Role Debug are read-only (P43). Do not save these roles in the role editor.
- **Also fixed:** the Stages list now sorts by Sequence (`moreSort`; `step4_views.py`).
- Role Debug acts on the API too: while it was on, `hap app role list` was refused. Switch it off before running scripts.
