# Status

Last updated: 27 Nov 2026.

## Now

- **Stage:** 1, preparing the POC app ([`PLAN.md`](PLAN.md#stage-1-the-poc-app)).
- **Working on it:** Builder (AI session), 27 Nov 2026.
- **Next step:** the POC continues in the current copy, which came from the 17 Nov export ([`PLAN.md`](PLAN.md#decisions), 27 Nov). Fix its two faults by hand ([`EMS-BASELINE.md`](EMS-BASELINE.md#faults-in-the-17-nov-export)), then work through the Stage 1 checklist. The 17 Nov additions are rebuilt only where the demo needs them.
- **Waiting on the Account Lead:** the questions in [`REQUIREMENTS.md`](REQUIREMENTS.md#questions-for-the-account-lead).

## Environment

- **Platform:** Nocoly SaaS (HAP), in the organisation that holds EMS. Ask the POC Lead for access.
- **EMS master:** the app named EMS. Read-only for this POC.
- **Export for the POC app:** EMS's export history, entry of **27 Nov 2026, 19:41 (UTC+8)**.
  - It was made with `hap app export --include-data`, so it holds the structure plus up to 10,000 records per table.
  - On 27 Nov every one of the 83 worksheets was under that limit: 5,557 records in all, and the largest, States, has 2,130. So no table should be cut.
  - *Verified 27 Nov:* the export is listed with a download link. Whether the records are really inside is confirmed only at import.
- **Older exports in the same history:** 17 Nov, 6 Oct and 30 Sep 2026. Do not use them. The 17 Nov one lacks the 17 Nov additions and has two faults ([`EMS-BASELINE.md`](EMS-BASELINE.md#faults-in-the-17-nov-export)).
- **POC app:** imported from a `.mdy` file on 27 Nov 2026 at 20:23 (UTC+8), then renamed. Its name carries the client name, so it is not written here; ask the POC Lead.
  - **It is the 17 Nov export, not the 27 Nov one** *(Verified 27 Nov, HAP CLI, compared with EMS)*:
    - It lacks what EMS gained after that export: the Forecast and Inventory at Date pages, the Stock Ledger worksheet, and the 15 workflows created in EMS after it. Among them are the daily replenishment run, the stock report sync and the lot expiry alerts.
    - Both faults of that export are in it. The step "Lot from name - current lot" in `Inventory - Lot/Serial from name` is still a single-record lookup. The Scrap Math step of `Validate Scrap (Native)` and `Continue Scrap` still holds the `known_untracked` check.
    - It has 82 worksheets, 9 custom pages and 283 workflows; EMS has 83, 11 and 298.
    - `Put In Pack` is off in the copy and on in EMS.
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
| 27 Nov 2026 | Builder (AI session) | Compared the POC app with EMS: it is the 17 Nov export (details under Environment). Turned off its three scheduled flows; nothing else changed | HAP CLI, 27 Nov, read back |
| 27 Nov 2026 | Builder | Decision: keep the current copy and patch it, instead of re-importing ([`PLAN.md`](PLAN.md#decisions)) | Builder's instruction to the AI session |

## Findings for the EMS App Owner

None yet.
