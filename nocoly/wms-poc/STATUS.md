# Status

Last updated: 27 Nov 2026.

## Now

- **Stage:** 1, preparing the POC app ([`PLAN.md`](PLAN.md#stage-1-the-poc-app)).
- **Working on it:** Builder (Travis), 27 Nov 2026.
- **Next step:** Stage 1, steps 4 to 7 of the checklist. CRM and Activities are removed (see **POC app** below). Still to do:
  - **Re-test in the UI:** run the core flow (receipt → sales order → delivery → return) after the trim. Also run a receipt with a new lot name and a scrap of a lot-tracked product, to check the two fixes.
  - **Point of Sale:** it waits for the Account Lead's answer on over-the-counter sales.
  - **Test transactions:** the POC Lead chooses how to clean them up ([`PLAN.md`](PLAN.md#stage-1-the-poc-app), step 5).
  - **UI-only checks:** someone checks in the HAP UI what the CLI cannot read: the print templates on Transfer, the portal settings and portal users, and the members named in workflow notifications.
  - **Demo data and language:** steps 6 and 7.
- **Waiting on the Account Lead:** the questions in [`REQUIREMENTS.md`](REQUIREMENTS.md#questions-for-the-account-lead).

## Environment

- **Platform:** Nocoly SaaS (HAP), in the organisation that holds EMS. Ask the POC Lead for access.
- **EMS master:** the app named EMS. Read-only for this POC.
- **Export for the POC app:** EMS's export history, entry of **27 Nov 2026, 19:41 (UTC+8)**.
  - It was made with `hap app export --include-data`, so it holds the structure plus up to 10,000 records per table.
  - On 27 Nov every one of the 83 worksheets was under that limit: 5,557 records in all, and the largest, States, has 2,130. So no table should be cut.
  - *Verified 27 Nov:* the export is listed with a download link. Whether the records are really inside is confirmed only at import.
- **Older exports in the same history:** 17 Nov, 6 Oct and 30 Sep 2026. Do not use them. The 17 Nov one lacks the 17 Nov additions and has two faults ([`EMS-BASELINE.md`](EMS-BASELINE.md#faults-in-the-17-nov-export)).
- **POC app:** imported from a `.mdy` file on 27 Nov 2026 at 20:23 (UTC+8), then renamed. Its name carries the client name, so it is not written here; ask the POC Lead. It came from the 17 Nov export. The decision of 27 Nov is to keep it and patch it ([`PLAN.md`](PLAN.md#decisions)).
  - **Faults of the 17 Nov export, fixed on 27 Nov** *(Verified 27 Nov, HAP CLI: read back and compared step by step with EMS; not yet run in the UI)*:
    - **`Inventory - Lot/Serial from name`:** the step "Lot from name - current lot" now gets the line's related Lot/Serial Number record and continues when there is none. The decide step reads the lot's name from that step, as in EMS. Published without warnings.
    - **`Validate Scrap (Native)` and `Continue Scrap`:** Scrap Math now takes Tracking from the Template step and posts with serial, lot or none to match. The `known_untracked` check is gone, and the step's code and inputs are the same as in EMS. Both flows published without warnings.
  - **Still missing from the 17 Nov additions:** the Forecast and Inventory at Date pages, the Stock Ledger worksheet, and 15 workflows. Among them are the daily replenishment run, the stock report sync, the lot expiry alerts and the release of reservations after a scrap. They are rebuilt only where the demo needs them.
  - **Stage 1 checks** *(Verified 27 Nov, HAP CLI)*:
    - **Workflows:** on and off as in EMS, except the scheduled flows (below) and `Put In Pack`.
    - **`Put In Pack`:** it is off and cannot be published, because three steps are flagged. A branch condition reads a Transfer field that no longer exists, and two "Pack Finished" update steps set no field. EMS's design has the same three steps (see the findings below). Until this is repaired, goods cannot be put in a pack in the copy.
    - **Custom pages:** the 9 pages have the same components as in EMS.
    - **Roles:** the same 12 roles as in EMS. Members were not checked, because the CLI's role list does not return them.
    - **Not checked yet (HAP UI only):** the print templates on Transfer, the portal settings and portal users, the members named in workflow notifications, and the MyInvois and API credentials.
  - **Trimmed on 27 Nov: CRM and Activities removed** *(Verified 27 Nov, HAP CLI: read back; not yet re-tested in the UI)*:
    - **Backup first:** an app backup with data was made before anything was removed (27 Nov, 21:07, 4,481 records).
    - **Removed:**
      - the 8 CRM worksheets and the 6 Activities worksheets, and their sections;
      - their 22 workflows, among them `Calculated Probability`;
      - the CRM Pipeline and Sales Manager dashboards (both showed only CRM data);
      - the CRM tab and the Activities buttons on the Configuration Dashboard;
      - the two Orders fields that pointed at CRM (Tags and Sales Teams), and Sales Teams in the Orders rule "A template shows only what it hands on".
    - **What points at the removed sheets now:** nothing. This was checked with the CLI's reference lists and by reading the Orders and app-level workflows, the dashboard charts, and the Orders and Contacts views and rules.
    - **Restoring:** the worksheets and pages are in the app's recycle bin, the two fields in the Orders field recycle bin, and the workflows in the workflow recycle bin.
    - **The app now holds:** 7 modules, 68 worksheets, 7 custom pages and 261 workflows (236 on).
  - **Scheduled flows:** after the import, three were on in the copy: `MyInvois: Document Synchronization`, `Stock availability: hourly` and `Inventory - daily reservation run`. They were turned off on 27 Nov and read back as off, so that the copy neither uses workflow quota nor calls MyInvois. The EMS master was not touched.

## Log

| Date | Who | What happened | Evidence |
|---|---|---|---|
| 17 Nov 2026 | Nocoly | EMS demo and discussion with the client team. The four POC areas came out of it | Client request |
| 17 Nov 2026 | Nocoly | Inventory additions after the demo: scheduled replenishment, Inventory at Date and Forecast, lot expiry alerts, count conflicts, scrap of reserved stock | Tested 17 Nov in EMS |
| 27 Nov 2026 | Account Lead | The client's project lead saw the PoC and was happy. Next is a presentation in Chinese for the client's management. Nocoly runs the POC and the project | Account Lead's emails |
| 27 Nov 2026 | Builder | Read-only check of EMS: 9 modules, 83 worksheets, 11 custom pages, record counts. The scheduled flows added on 17 Nov are enabled; the multi-step routes draft is disabled | HAP CLI, 27 Nov |
| 27 Nov 2026 | Builder | Fresh export of EMS with data, for the POC app | Export in EMS history, 19:41 |
| 27 Nov 2026 | Builder | This folder | — |
| 27 Nov 2026 | Builder | POC app imported from a `.mdy` file and renamed | App log, 20:23 |
| 27 Nov 2026 | Builder (Travis) | Compared the POC app with EMS: it is the 17 Nov export. Turned off its three scheduled flows; nothing else changed | HAP CLI, 27 Nov, read back |
| 27 Nov 2026 | Builder (Travis) | Decision: keep the current copy and patch it, instead of re-importing ([`PLAN.md`](PLAN.md#decisions)) | — |
| 27 Nov 2026 | Builder (Travis) | Fixed the two faults of the 17 Nov export in the POC app (details under Environment) | HAP CLI, read back against EMS; not yet run in the UI |
| 27 Nov 2026 | Builder (Travis) | Stage 1 checks of workflows, pages and roles. `Put In Pack` cannot be published | HAP CLI, 27 Nov |
| 27 Nov 2026 | Builder (Travis) | Names next to roles in this file ([`AGENTS.md`](AGENTS.md#before-you-start)) | — |
| 27 Nov 2026 | Builder (Travis) | Trimmed CRM and Activities from the POC app, after an app backup with data (details under Environment) | HAP CLI, read back; not yet re-tested in the UI |

## Findings for the EMS App Owner

- **`Put In Pack`** (the button flow on Transfer), found on 27 Nov 2026 *(HAP CLI)*:
  - Its design has a branch condition on a Transfer field that no longer exists, and two "Pack Finished" update steps that set no field.
  - EMS still shows it as published (on, last changed 7 Oct), but a copy of EMS cannot publish it.
  - Whether it still works in EMS was not checked.
