# Removing CRM from a customer copy

The CRM part of `../SPLIT-GUIDE.md`. Written with the plan (24 Nov 2026), before the build. **After the build, replace the planned lists below with the real ones** from `register_build.py --prune crm` and the ledger `ids.json`.

## 1. What goes, and what may stay

| Odoo module | Remove when the customer has… | Keep when… |
|---|---|---|
| `crm` | no CRM | — |
| `sales_team` (Sales Teams, Team Members, CRM Tags, the sales roles) | neither CRM nor Sales nor Point of Sale | Sales or Point of Sale stays (they use teams) |
| `utm` (Campaigns, Mediums, Sources, UTM Stages, UTM Tags) | no CRM, Sales, marketing or website | any of those stays |
| `calendar` (Meetings) | no other module uses Meetings | another module schedules meetings |

**Modules that depend on `crm`**, and so go with it: `sale_crm` (the opportunity link on quotations), `website_crm`, `crm_sms`, `crm_livechat`, `event_crm`, `survey_crm`, `mass_mailing_crm`, `crm_sale_project`, `partnership`, `crm_iap_*`. The register adds them automatically (Odoo dependency closure).

## 2. Objects CRM owns (planned)

| Kind | Objects |
|---|---|
| Worksheets | Leads / Opportunities, Stages, Lost Reasons, Recurring Plans, Scoring Frequencies (System Tables) |
| Workflows | the "CRM - …" flows: defaults, customer sync, stage rules, Won / Lost / Restore, conversion, rotting, meetings, public form, UTM names; Phase B: scoring, assignment, merge |
| Buttons | on Leads: Won, Lost, Restore, Convert to Opportunity, Schedule Meeting, Launch Plan, Merge |
| Views, charts, pages | the Leads views (pipeline kanban, lists, calendar), the CRM page with its charts |
| Public form | the enquiry form on Leads (switch it off before deleting) |

## 3. Bridges: what CRM adds to sheets that stay

| Retained sheet (owner) | CRM object | Remove how |
|---|---|---|
| Contacts (`base`) | "Opportunities" tab (reverse of the lead's Customer) and the opportunity count | The tab goes with Leads (two-way pair); delete the count field |
| Activities (`mail`) | "Lead / Opportunity" relation; activities whose document is a lead | Delete the activities on leads first (approval), then the field |
| Activity Types, Activity Plans (`mail`) | the "Leads" option in Applies to | Archive or re-point the types and plans that use it, then delete the option |
| Meetings (`calendar`) | the "Opportunity" relation | Delete the field; meetings stay |
| Roles | Leads, Stages… rows in Salesperson / Sales User / Sales Manager | Go with the sheets; the roles themselves belong to `sales_team` |
| Wave 0 workflows | "Activities - Launch plan" and the activity buttons read the document generically (model text and id) | Check that they still publish and run for a contact |

## 4. Order

1. Switch off the public form.
2. Switch off and delete the "CRM - …" workflows, button flows first.
3. Delete the buttons on Leads.
4. Delete the CRM page and charts.
5. Delete the activities on leads (with approval).
6. Delete the Lead relation on Activities and on Meetings, and the count field on Contacts.
7. Delete the "Leads" option in Activity Types and Plans, after re-pointing the records that use it.
8. Delete the worksheets: Scoring Frequencies, Leads / Opportunities, Stages, Lost Reasons, Recurring Plans.
9. If `sales_team` and `utm` go too: Team Members, Sales Teams, option set CRM Tags, the sales roles; then Campaigns, UTM Stages, Mediums, Sources, option set UTM Tags.

## 5. Checks after removal

- **Register:** re-scan; nothing owned by `crm` is left, "Bridges to fix" is empty, 0 unresolved.
- **Contacts:** the form has no Opportunities tab. The Contacts sync flows still run: re-run wave 0 tests 1 and 2.
- **Activities:** Mark Done, Done & Schedule Next and Launch Plan still work on a contact. Re-run wave 0 tests 14–16 and 18.
- **Roles:** the remaining roles open without errors in Role Debug.
