# Status

Last updated: 27 Nov 2026.

## Now

- **Stage:** 1 is nearly done, and Stage 2 has started early on the Builder's instruction ([`PLAN.md`](PLAN.md#stage-2-the-four-demo-areas)). Built so far: daily exchange rates, the management dashboard and e-commerce order intake (see **Stage 2 builds** below).
- **Working on it:** Builder (Travis), 27 Nov 2026.
- **Next step:**
  - **Caution before any invoice is confirmed in the copy:**
    - `Invoices: Send To MyInvois on Confirm` is on *(Verified 29 Nov, HAP CLI)*, so a confirmed invoice is sent to MyInvois with the settings copied from EMS.
    - Switch it off, or clear the copied MyInvois settings, first. That is a Builder change, with the POC Lead's OK.
    - The buttons Send To MyInvois, Submit To MyInvois, Update MyInvois Status and Generate a Payment Link act only when clicked.
  - **Stage 2, in the HAP UI:** the supplier and customer portal (recipe under **Stage 2 builds**). The CLI cannot create portal roles.
  - **Stage 2, needs a sandbox store:** stock and fulfilment updates back to the store. The platform is a question for the Account Lead.
  - **Stage 2, run once:** each build, which has not been run yet.
  - **Stage 1 leftovers:**
    - **Document numbering:** the start values were raised on 27 Nov (see **POC app** below). Confirm in the UI that the next new record takes the new number.
    - **UI walk-through:** a Reviewer runs the same flow in the HAP UI, which no one has done yet.
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
- **POC app:** imported from a `.mdy` file on 27 Nov 2026 at 20:23 (UTC+8), then renamed. Its name carries the client name, so it is not written here; ask the POC Lead. It came from the 17 Nov export. The decision of 27 Nov, confirmed by the POC Lead on 29 Nov, is to keep it and patch it ([`PLAN.md`](PLAN.md#decisions)).
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
  - **Re-test on 27 Nov: passed** *(Verified 27 Nov, HAP CLI: TEST records created and the same buttons pressed that the UI uses, then every result read back; not run in the UI)*:
    - **Core flow in Kuching (KCH):**
      - The receipt reached Done and the stock went from 4 to 9.
      - The sales order was confirmed, and its delivery was created and reserved.
      - The delivery reached Done. The order showed 2 delivered and Fully Delivered, and the stock went from 9 to 7.
      - The return of 1 unit reached Done. The order showed 1 delivered and Partially Delivered, and the stock went from 7 to 8.
    - **Lot fix:** a new lot name typed on a receipt line created the lot and linked it, and the receipt posted 3 units to that lot.
    - **Scrap fix:** a scrap of 1 unit of a lot-tracked product reached Done and took 1 from that lot.
    - **A trap for CLI tests:** an order line written through the CLI needs its Unit. The UI fills it in from the product. Without it, reservation fails at the "Move Unit" step.
    - **Records the test left:**
      - receipts KCH/IN/00001 and KCH/IN/00005;
      - orders S00001 and S00002 (S00002 cancelled);
      - deliveries KCH/OUT/00002 and KCH/OUT/00004 (KCH/OUT/00004 cancelled);
      - return KCH/IN/00003;
      - scrap SCRAP/00001;
      - lot TEST-LOT-2711.

      All carry "TEST CLI re-test 27 Nov" as source document or customer reference. They go with the cleanup of test transactions (step 5).
  - **Document numbering restarted at 1 after the import** *(Verified 27 Nov)*:
    - **What happens:** the 18 auto-number fields (Transfer, Orders, Order Lines, Stock Move Lines, Stock Balances, Scrap, Packages, Batch Transfers, Reordering Rules, Putaway Rules and the POS and pricing tables) began again at 1. New records repeat numbers that imported records already carry: S00001, SML/00001 and SML/00002 now each exist twice.
    - **Impact:** the re-test found no flow that looks records up by these numbers, but the repeats confuse people and the demo.
    - **Fixed on 27 Nov** *(Verified 27 Nov, HAP CLI: read back; the next number itself not yet seen)*. The start value of 16 auto-numbers was raised above the highest number in use, through `hap app-editor` `field.update`, which reads the whole field set and writes it back with only that change:
      - Transfer and Stock Move Lines start at 300;
      - Orders and Stock Balances at 200;
      - POS Order Lines at 100;
      - Batch Transfers, Scrap, Packages, Reordering Rules, Putaway Rules, Storage Capacity Lines, Sessions, POS Orders and POS Payments at 50;
      - Pricelists and Fiscal Positions at 10.

      Order Lines and Price Rules hold no numbers and were left as they are.
- **Stage 2 builds** *(Verified 27 Nov, HAP CLI: read back and published; not run, on the Builder's instruction)*:
  - **Daily exchange rates:**
    - **Sheets:** two new sheets in Invoicing.
      - Currencies: Code, Currency Name, Symbol, Active and Base Currency. Seeded with MYR (base), USD, SGD, CNY, EUR, GBP and JPY.
      - Currency Rates: Currency Code, Rate Date, Rate (MYR per unit, 6 decimals) and Source.
    - **`Currency - daily rates (BNM)`:** runs daily at 12:30. For each active foreign currency, its sub-process `Currency Sub - store one rate` fetches Bank Negara Malaysia's 12:00 middle rate (RM per unit, divided by BNM's unit), and stores it unless a rate for that date is already stored. On days without a new rate, nothing is added and the last stored rate stays in use.
    - **Why a Code Block:** the fetch is a Code Block, because a native API step cannot pick one currency out of BNM's reply. The block calls the public BNM API and needs no key.
    - **Orders:** five new fields:
      - Order Currency, a link to Currencies;
      - Order Currency Code;
      - Exchange Rate (MYR per unit);
      - Rate Date;
      - Total in Order Currency, a formula: Total ÷ rate, because order prices stay in MYR.
    - **`Currency - order exchange rate`:** runs when an order is created or its currency or date changes.
      - MYR gets rate 1.
      - A foreign currency gets the latest stored rate on or before the order date.
      - If no rate is stored yet, the order keeps the rate it had. A step that clears it could not be built through the CLI.
    - **Open:** the new Orders fields sit at the end of the form; a person should place them in the layout.
  - **Management dashboard:** a new page in Dashboards with 13 charts copied from the existing dashboards.
    - Sales and finance KPIs: sales revenue (YTD), confirmed sales, receivables overdue, and cash received this month.
    - Inventory KPIs: late transfers, waiting transfers, open backorders, and products to replenish.
    - Larger charts: monthly sales, stock lines by location, top products, top customers, and transfers by status.
    - Margin is not shown, because it needs a costing decision first ([`PLAN.md`](PLAN.md#finance-functions-and-a-management-dashboard)).
  - **E-commerce order intake:**
    - **Sheets:** two new sheets in Sales.
      - Online Orders: Store Order ID, Platform, Customer Name, Customer Email, Customer Phone, Status, Message and a link to the Sales Order. Status is one of Received, Ready, Processed, Duplicate or Failed.
      - Online Order Lines: SKU, Quantity, Unit Price, Result, a link to the Online Order, and the Store Order ID looked up from it.
    - **How an order arrives:** the store, or a middleware such as n8n or Zapier, writes through HAP API V3. It creates the Online Order with Status Received, then its lines linked to it, then sets Status to Ready. Ready starts the flow, so the lines are always in place first.
    - **`E-commerce - online order in`:** runs when an Online Order is set to Ready.
      - If a sales order already carries the Store Order ID (in Customer Reference), the Online Order is marked Duplicate and linked to it, so a repeated call creates nothing.
      - Otherwise it finds the customer by email, or creates one. It then creates the sales order: Customer Reference = Store Order ID, Tax Excluded, salesperson = whoever created the Online Order. The warehouse is left empty, so the order ships from Shah Alam (WH).
      - Its sub-process `E-commerce Sub - add one line` matches each line's SKU to a variant's Internal Reference and adds the order line with Unit = Units. It marks the line "Added to the sales order" or "SKU not found".
      - It then confirms the order. The Status change starts the existing delivery creation and reservation.
      - Finally it marks the Online Order Processed and links the sales order.
    - **Not built yet:**
      - pushing stock per SKU back to the store;
      - sending the delivery status and tracking number back.

      Both need a sandbox store and its API. The Online Orders sheet can serve as the integration log for incoming orders; outgoing calls will need a log of their own.
  - **Supplier and customer portal (HAP UI only):** the CLI cannot create external portal roles. Recipe:
    1. Turn on the external portal of the POC app.
    2. Add to the portal user sheet a field that links each portal user to their company in Contacts.
    3. Create two portal roles:
       - **Supplier:** sees Transfer receipts whose Contact is the user's company, and may upload a delivery note and confirm quantities.
       - **Customer:** sees Orders and deliveries whose Customer or Contact is the user's company, and the Delivery Slip.
    4. Create one test portal user per role, without sending invitations to anyone outside Nocoly.
  - **Cancelling a sales order leaves its delivery open** *(Verified 27 Nov, HAP CLI)*: when a confirmed order was cancelled, its delivery stayed Ready with the stock still reserved. Cancel Transfer on the delivery released it. EMS uses the same flows, so it most likely behaves the same; that was not checked.
  - **`Auto Update/Create Route` turned off on 27 Nov:**
    - **The problem:** this flow runs whenever a warehouse is created or changed. Its code step holds a literal API key and sign, and the worksheet IDs of the EMS master, so in any copy of EMS it writes to the master's Routes and Warehouses.
    - **What was done:** it is off in the copy (read back as off). It had not run in the copy since the import.
    - **Before anyone turns it on again:** rebuild it on the copy's own sheets (see the findings below).
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
| 27 Nov 2026 | Builder (Travis) | Re-test of the core flow and both fixes with TEST records: passed. Found that document numbering restarted at 1, that cancelling an order leaves its delivery reserved, and that `Auto Update/Create Route` writes to the EMS master (turned off) | HAP CLI, 27 Nov; the Chrome extension was not connected, so no UI run |
| 27 Nov 2026 | Builder (Travis) | Raised the start values of 16 auto-numbers. Stage 2 started early: daily exchange rates (2 sheets, 2 flows and 5 Orders fields) and the management dashboard (13 charts) | HAP CLI, read back and published; not run |
| 27 Nov 2026 | Builder (Travis) | E-commerce order intake: Online Orders and Online Order Lines sheets, and a flow with a sub-process that creates and confirms the sales order. Portal recipe written for the UI | HAP CLI, read back and published; not run |
| 29 Nov 2026 | POC Lead | Confirmed the decision to keep the copy and patch it ([`PLAN.md`](PLAN.md#decisions)) | — |
| 29 Nov 2026 | POC Lead (AI session) | Read-only check of the copy: `Invoices: Send To MyInvois on Confirm` and the MyInvois and Stripe buttons are on; nothing in the copy changed after 27 Nov | HAP CLI, 29 Nov |

## Findings for the EMS App Owner

- **`Put In Pack`** (the button flow on Transfer), found on 27 Nov 2026 *(HAP CLI)*:
  - Its design has a branch condition on a Transfer field that no longer exists, and two "Pack Finished" update steps that set no field.
  - EMS still shows it as published (on, last changed 7 Oct), but a copy of EMS cannot publish it.
  - Whether it still works in EMS was not checked.
- **`Auto Update/Create Route`** (on Warehouses), found on 27 Nov 2026 *(HAP CLI)*:
  - **What it holds:** its code step contains a literal API key and sign, and the worksheet IDs of EMS's Warehouses and Routes.
  - **Why it matters:** every copy of EMS inherits this flow switched on, and in a copy it writes back into the EMS master whenever a warehouse is created or changed. The key itself is a secret stored inside a workflow.
  - **Suggested fix:** move the key out of the flow, or use native workflow steps, so that a copy works on its own sheets.
  - **Status:** turned off in the POC copy; not changed in EMS.
- **Document numbering after an import** (27 Nov 2026): a copy imported with data restarts every auto-number at 1. Anyone who imports EMS should set the start values afterwards.
- **Cancelling a sales order** (27 Nov 2026, seen in the POC copy): the order's delivery stays reserved. EMS most likely does the same; not checked.
