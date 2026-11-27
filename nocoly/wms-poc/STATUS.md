# Status

Last updated: 27 Nov 2026.

## Now

- **Stage:** 1, preparing the POC app ([`PLAN.md`](PLAN.md#stage-1-the-poc-app)).
- **Working on it:** nobody. Write your role and the date here when you start.
- **Next step:** import the export of 27 Nov 2026 (below) as a new app, in the HAP UI; the HAP CLI cannot import. Then work through the Stage 1 checklist.
- **Waiting on the Account Lead:** the questions in [`REQUIREMENTS.md`](REQUIREMENTS.md#questions-for-the-account-lead).

## Environment

- **Platform:** Nocoly SaaS (HAP), in the organisation that holds EMS. Ask the POC Lead for access.
- **EMS master:** the app named EMS. Read-only for this POC.
- **Export for the POC app:** EMS's export history, entry of **27 Nov 2026, 19:41 (UTC+8)**.
  - It was made with `hap app export --include-data`, so it holds the structure plus up to 10,000 records per table.
  - On 27 Nov every one of the 83 worksheets was under that limit: 5,557 records in all, and the largest, States, has 2,130. So no table should be cut.
  - *Verified 27 Nov:* the export is listed with a download link. Whether the records are really inside is confirmed only at import.
- **Older exports in the same history:** 17 Nov, 6 Oct and 30 Sep 2026. Do not use them. The 17 Nov one lacks the 17 Nov additions and has two faults ([`EMS-BASELINE.md`](EMS-BASELINE.md#faults-in-the-17-nov-export)).
- **POC app:** not created yet.

## Log

| Date | Who | What happened | Evidence |
|---|---|---|---|
| 17 Nov 2026 | Nocoly | EMS demo and discussion with the client team. The four POC areas came out of it | Client request |
| 17 Nov 2026 | Nocoly | Inventory additions after the demo: scheduled replenishment, Inventory at Date and Forecast, lot expiry alerts, count conflicts, scrap of reserved stock | Tested 17 Nov in EMS |
| 27 Nov 2026 | Account Lead | The client's project lead saw the PoC and was happy. Next is a presentation in Chinese for the client's management. Nocoly runs the POC and the project | Account Lead's emails |
| 27 Nov 2026 | Builder | Read-only check of EMS: 9 modules, 83 worksheets, 11 custom pages, record counts. The scheduled flows added on 17 Nov are enabled; the multi-step routes draft is disabled | HAP CLI, 27 Nov |
| 27 Nov 2026 | Builder | Fresh export of EMS with data, for the POC app | Export in EMS history, 19:41 |
| 27 Nov 2026 | Builder | This folder | — |

## Findings for the EMS App Owner

None yet.
