# Plan

Four stages, each with a "done when". There are no dates: the Account Lead agrees them with the client.

## Stage 1: the POC app

1. **Import** the export of 27 Nov 2026 as a new app, in the HAP UI. Give it a name that marks it as the POC.
2. **Check after import:**
   - **Workflows:** which are on and which are off, compared with EMS. The scheduled ones are:
     - the daily reservation run (06:00);
     - replenishment (05:30);
     - lot expiry alerts (06:15);
     - the hourly stock report sync.
   - **Print templates and pages:**
     - the templates on Transfer: Delivery Slip, Reception Report, Return Slip, Picking Operations;
     - the custom pages: dashboards, Barcode Scanner, Inventory at Date, Forecast, MyInvois Setup.
   - **Organisation-specific settings,** which may not carry over:
     - roles, portal settings and portal users;
     - members or departments named inside workflows (notifications, approvals);
     - credentials for MyInvois and any API connection.
   - **The two flows fixed in the EMS master on 17 Nov** (see `EMS-BASELINE.md`):
     - a receipt line with a new lot name creates and links the lot;
     - a scrap works for more than one product.
3. **Decide the scheduled workflows.** The EMS master runs about 1,700 workflow executions a day (usage statistics, 20–26 Nov 2026). The count is the same every day, which points to its scheduled flows. A copy with the same schedules adds as many to the organisation's quota, so keep only what the demo needs.
4. **Trim the modules** the client does not need: CRM and Activities, and Point of Sale unless the client sells over the counter. Follow the dependency notes in `EMS-BASELINE.md`, and re-test after each removal.
5. **Clean up.** Remove the test material listed in `EMS-BASELINE.md`. For the test transactions, the POC Lead chooses one of two ways:
   - keep them, out of the demo views;
   - reset the copy's transaction tables together, then post fresh demo stock through receipts.

   Never edit single stock rows.
6. **Demo data** that fits the client's business: products, warehouses, customers and suppliers.
7. **Language:** Chinese labels in the app, or English labels with Chinese narration. This is a question for the Account Lead.

*Done when* the core flow (receipt → sales order → delivery → return) runs in the POC app on demo data, checked in the UI.

## Stage 2: the four demo areas

At demo depth: one example of each, end to end, on demo data.

### E-commerce integration by API

- **Shows:**
  - an order from a sandbox store (or a simulated order) arrives, becomes a sales order with lines matched by SKU, and its delivery is reserved;
  - stock per SKU goes back to the store;
  - when the delivery is done, the status and tracking number go back too.
- **How:**
  - a webhook-triggered workflow brings orders in, and Send API Request steps make the calls out;
  - the store's order ID is kept on the sales order, so a repeated webhook cannot create a duplicate;
  - failures go to an integration log sheet.
- **Done when:** one order runs end to end, a repeated webhook creates no duplicate, and a failed call shows in the log.

### Daily exchange rates by API

- **Shows:** the day's rates arrive on their own, and a foreign-currency order shows the amount in both currencies.
- **How:**
  - a Currencies sheet (code, name, symbol, rounding, active);
  - a Currency Rates sheet (date, currency, rate against the base currency, source);
  - a scheduled workflow that calls the agreed rate API every day; on days without a new rate, the last one is used;
  - documents store the document-currency amount, the base-currency amount and the rate used.
- **Done when:** the scheduled run stores the day's rates, and a foreign-currency sales order shows both amounts with the rate used.

### Portal for suppliers or customers

- **Shows:** a supplier and a customer each sign in to their own portal and see only their own records.
  - Supplier: expected receipts and dates, upload of a delivery note, confirmation of quantities.
  - Customer: orders, delivery status, the delivery slip, a return request.
- **How:** the HAP external portal, with one portal role per user group; rows are filtered by the user's own company (Contact).
- **Done when:** both users sign in and see only their own records, checked with each portal role.

### Finance functions and a management dashboard

- **Shows:**
  - the finance basics the Account Lead agrees, for example receivables and payables from invoices and bills, and payments;
  - one management dashboard.
- **How:**
  - Invoicing's existing sheets cover the finance basics;
  - the dashboard is a custom page with charts across sales (revenue, margin), inventory (stock on hand, late deliveries, fill rate) and finance (receivables ageing, cash).
- **Note:** EMS has no stock valuation, no cost of goods sold and no purchasing. A stock value or margin figure needs a costing decision first.
- **Done when:** the dashboard shows real figures from the demo data for the agreed KPIs, checked with a management role.

### IoT

- IoT is part of the client's broader requirement. Whether it is in this presentation, and with which IoT platform, is a question for the Account Lead.
- HAP is not an MQTT broker. Devices connect through an IoT platform, which calls HAP by webhook, and HAP calls the platform's API back.
- Nocoly has a separate demo of that pattern; ask the POC Lead.

### Platform notes *(Documented; check the current help pages before quoting a number)*

- Inbound webhooks: up to 10,000 requests per hour.
- Send API Request: 10-second timeout. A timeout does not prove that the other system did nothing.
- Code Block steps and loops are listed under the Professional plan, and Inventory relies on them.
- Portal users belong to one app and have one portal role each.

*Done when* each area has run end to end in the UI, with the role that will use it.

## Stage 3: the presentation

- Slides in Chinese: the client's needs, what the POC shows, how it is built, and the road to the full system.
- A demo script: which screens, in which order, with which records.
- A dry run with the Account Lead, then fixes for what it finds.
- Never run a live receipt into a location with an active putaway rule: it takes 50–80 s per line (`EMS-BASELINE.md`).
- Present the app as a POC, not as the system that will go live.

*Done when* the dry run is done and its findings are fixed.

## Stage 4: the full system, after the POC

- Discovery with the client: processes, warehouses, volumes, e-commerce platforms, currencies, portal users, finance scope, KPIs and IoT devices ([`REQUIREMENTS.md`](REQUIREMENTS.md#questions-for-the-client)).
- A solution design for a new app, native first. It reuses EMS's proven designs (document chain, stock ledger, reservation logic, reports) rather than its objects.
- An estimate of effort, with owners.

*Done when* the client and Nocoly agree the scope and the estimate.

## Decisions

| Date | Decision | Why | By |
|---|---|---|---|
| 27 Nov 2026 | Nocoly runs the POC and the project; no implementation partner | The client asked to work directly with Nocoly | Account Lead |
| 27 Nov 2026 | The POC runs in a copy of EMS; the EMS master is not changed | The master is shared by several module owners | POC Lead |
| 27 Nov 2026 | The copy comes from a fresh export with data, not the 17 Nov export | The 17 Nov export lacks later work and has two faults. Inventory needs EMS's configuration records (warehouses, locations, operation types) | POC Lead |
| 27 Nov 2026 | Working assumption: the full system is designed anew, with EMS as a reference | EMS's measured limits and gaps (`EMS-BASELINE.md`) | POC Lead, not final |
| 27 Nov 2026 | The POC continues in the copy imported on 27 Nov, although it came from the 17 Nov export. Its two faults are fixed by hand, and the 17 Nov additions are rebuilt only where the demo needs them. This replaces the decision to use a fresh export | The copy already exists, and both faults are known and fixable (`EMS-BASELINE.md`) | Builder (Travis); confirmed by the POC Lead on 29 Nov 2026 |
| 27 Nov 2026 | `STATUS.md` shows each person's name next to their role. Each person sets their own name once (`git config --global wmspoc.name`), and AI sessions fill it in | Easier tracking of who is working and who did what | Builder (Travis); the POC Lead to confirm |

## Risks

- **Volumes.**
  - Receipts with putaway rules take 50–80 s per line.
  - A document holds about 100 lines at most.
  - Concurrent postings are not coordinated.

  Measure with the client's real volumes in Stage 4.
- **Compute.**
  - The Account Lead said the PoC uses some Compute capabilities, but none was found in EMS on 27 Nov: its 11 custom pages are standard, and Point of Sale runs as a plugin view.
  - Compute is pre-release, and every Compute was wiped once, on 19 Nov 2026.

  Confirm what is meant before the presentation.
- **After import,** workflows, roles, portal users and credentials need re-mapping. Until then, flows can fail without warning.
