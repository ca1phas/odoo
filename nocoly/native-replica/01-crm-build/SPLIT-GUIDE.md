# Removing CRM from a customer copy

The CRM part of `../SPLIT-GUIDE.md`. Written with the plan (24 Nov 2026); §2–§4 updated after the build from the register scan of 24 Nov 2026, 17:32 (`register_build.py --prune crm sales_team utm`) and the ledger `ids.json`.

## 1. What goes, and what may stay

| Odoo module | Remove when the customer has… | Keep when… |
|---|---|---|
| `crm` | no CRM | — |
| `sales_team` (Sales Teams, Team Members, CRM Tags, the sales roles) | neither CRM nor Sales nor Point of Sale | Sales or Point of Sale stays (they use teams) |
| `utm` (Campaigns, Mediums, Sources, UTM Stages, UTM Tags) | no CRM, Sales, marketing or website | any of those stays |
| `calendar` (Meetings) | no other module uses Meetings | another module schedules meetings |

**Modules that depend on `crm`**, and so go with it: `sale_crm` (the opportunity link on quotations), `website_crm`, `crm_sms`, `crm_livechat`, `event_crm`, `survey_crm`, `mass_mailing_crm`, `crm_sale_project`, `partnership`, `crm_iap_*`. The register adds them automatically (Odoo dependency closure).

## 2. Objects each module owns (built, register scan 24 Nov 2026 17:32)

From `../register/scans/2026-11-24-1732/register.json` (755 objects in the app, 0 without an owner). The prune files next to it (`prune-crm.md`, `prune-sales_team.md`, `prune-utm.md`) give the totals: removing `crm` removes 126 objects; `sales_team` (which takes `crm` with it) 143; `utm` (also takes `crm`) 160.

| Module | Worksheets | Other objects |
|---|---|---|
| `crm` | Leads / Opportunities, Stages, Lost Reasons (75 fields) | **Views:** My Pipeline, Pipeline, All, Leads, Forecast, Won, Lost, Rotting, Archived; All on Stages and Lost Reasons. **Rules:** Lost reason when archived; Name or customer. **Buttons:** Won, Lost, Restore, Convert to Opportunity, Schedule Meeting, Launch Plan. **Workflows (20):** the 16 "CRM - …" flows (one is the inner flow "CRM - one plan step on a lead") and the 4 button flows. **Page:** Reporting. **Groups:** CRM, Configuration. **Public form** on Leads (not in the scan: switch it off by hand) |
| `sales_team` | Sales Teams | Roles Salesperson, Sales User, Sales Manager; option set CRM Tags |
| `utm` | Campaigns, Mediums, Sources, UTM Stages | Campaigns board; 4 "UTM - …" flows; option set UTM Tags; group Link Tracker |
| `calendar` | Meetings | Calendar view; "Meetings - Duration"; option set Meeting Tags |

Each sheet also has HAP's two default statistics charts ("Add new"), which go with it. Phase B objects (Recurring Plans, Scoring Frequencies, Team Members, the Merge button) are not built yet.

**Fields `crm` adds to sheets of other modules** (they go with `crm`): Contacts: Opportunities (reverse of the lead's Customer) and Opportunities Count; Activities and Plan Launches: Lead / Opportunity; Meetings: Opportunity; Campaigns: Leads (reverse) and Leads Count; Sales Teams: Opportunities (reverse); Lost Reasons: Leads Count.

## 3. Bridges: what stays but points at CRM

`prune-crm.md` lists 13 retained objects that point at removed ones:

- **12 relation fields** on Contacts, Activities, Plan Launches and Meetings (Related Company, Contacts & Addresses, Commercial Entity, Account Holder, Contact, Attendees, Activities, Plan Launches, Plan Launch). They hold a copy of the related sheet's columns, which now includes the CRM columns (Opportunities, Opportunities Count, Lead / Opportunity). They are expected to drop those columns when the CRM fields are deleted; the re-scan after removal confirms it (not yet tried).
- **The Campaigns board** (`utm`) shows Leads Count on its cards: remove it from the card fields when `crm` goes and `utm` stays.

Not in the scan, check by hand:

| Retained object (owner) | What CRM added | Remove how |
|---|---|---|
| Activity Types, Activity Plans (`mail`) | the "Leads" option in Applies to | Re-point or archive the types and plans that use it, then delete the option |
| Activities (`mail`) | activities whose document is a lead | Delete them first (with approval), then the Lead / Opportunity field |
| Wave 0 flow "Activities - Launch plan" | it now runs only when the launch has a contact (A3 guard) | Leave it: contacts keep working. Removing the guard is optional |
| Sales roles (`sales_team`) | Leads, Stages… rows | Go with the sheets; the roles go only with `sales_team` |

## 4. Order

1. Switch off the public form on Leads.
2. Switch off and delete the 20 `crm` workflows, the 4 button flows first.
3. Delete the 6 buttons on Leads.
4. Delete the Reporting page.
5. Delete the activities on leads (with approval).
6. Delete the CRM fields on other sheets: Lead / Opportunity on Activities and Plan Launches, Opportunity on Meetings, Opportunities Count on Contacts, Leads Count on Campaigns and Lost Reasons. Take Leads Count off the Campaigns board first.
7. Delete the "Leads" option in Activity Types and Plans, after re-pointing the records that use it.
8. Delete the worksheets Leads / Opportunities (this removes the reverse fields Opportunities on Contacts, Campaigns and Sales Teams), Stages, Lost Reasons; then the groups CRM and Configuration.
9. If `sales_team` goes too: Sales Teams, option set CRM Tags, the three sales roles. If `utm` goes too: its 4 flows, Campaigns, UTM Stages, Mediums, Sources, option set UTM Tags, group Link Tracker. `calendar` (Meetings) goes only if no other module schedules meetings.

## 5. Checks after removal

- **Register:** re-scan; nothing owned by `crm` is left, "Bridges to fix" is empty, 0 unresolved.
- **Contacts:** the form has no Opportunities tab. The Contacts sync flows still run: re-run wave 0 tests 1 and 2.
- **Activities:** Mark Done, Done & Schedule Next and Launch Plan still work on a contact. Re-run wave 0 tests 14–16 and 18.
- **Roles:** the remaining roles open without errors in Role Debug.
