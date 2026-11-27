# EMS baseline: what the POC app starts from

The POC app starts as a copy of the EMS master (export of 27 Nov 2026). This page is what Nocoly checked in the EMS master between 3 and 27 Nov 2026. Modules outside Inventory may have been changed by their owners since 17 Nov; that was not re-checked.

## Modules

EMS has nine menu modules, 83 worksheets and 11 custom pages *(Verified 27 Nov 2026)*.

| Module | What it does | For the POC |
|---|---|---|
| **Inventory** | Warehouses, locations, receipts, deliveries, internal transfers, returns, scrap, counts, stock ledger, lots and serials, packages, putaway, reordering, printing, barcode scanning, stock reports | **Keep**: the WMS core |
| **Products** | Products and variants (SKU, barcode, price, cost), categories, units and packagings, price lists | **Keep**: Inventory depends on it |
| **Contacts** | Customers, vendors, addresses, companies, countries and states | **Keep**: Inventory depends on it, and a portal would key on Contact |
| **Sales** | Quotations and sales orders. A confirmed order creates and reserves the delivery; delivered quantities flow back to the order | **Keep**: the e-commerce order flow would use it |
| **Invoicing** | Chart of accounts, taxes, journals, invoices and bills, payments, MyInvois e-invoicing | **Keep**: the base for finance |
| **Dashboards** | CRM Pipeline, Sales Operations, Sales Performance, Sales Manager, Configuration, Inventory Operations and Inventory Reporting | **Keep** the two Inventory dashboards; add the management dashboard |
| **Point of Sale** | Cashier terminals, sessions, register screen, POS orders, payments and refunds | **Remove** unless the client sells over the counter |
| **CRM** | Leads and opportunities pipeline | **Remove**: no link to Inventory |
| **Activities** | To-dos, calls, meetings and activity plans, linked to CRM leads only | **Remove** together with CRM |

The largest tables on 27 Nov were reference data: States (2,130 records), MSIC Codes (1,174) and Countries (251). All 83 worksheets held 5,557 records in all.

## Inventory: what works *(Verified 3–17 Nov 2026)*

| Area | What works |
|---|---|
| Warehouses and locations | Several warehouses. A new warehouse gets its view and stock locations, its Receipts, Delivery Orders and Internal Transfers operation types with their own numbering (for example KCH/IN/… and KCH/OUT/…) and paired return types. Sub-locations such as shelves and bins get a full path automatically, for example WH/Stock/Shelf 1. |
| Receipts | Draft → Mark as To Do → Validate. Putaway rules (by product or category) send stock to the right shelf. Backorders follow the policy (Ask, Always or Never). |
| Deliveries | Reservation at confirmation, by hand, or before the scheduled date (daily run at 06:00), including stock in sub-locations. Check Availability, Unreserve, Validate and backorders. |
| Internal transfers | The same lifecycle between internal locations. |
| Returns | Create Return builds the return on the operation type's return type, with quantities filled in. Packed goods come back in their package. Returns reduce the sales order's delivered quantity. |
| Sales link | Confirming a sales order creates and reserves the delivery on the order's warehouse. Validating the delivery writes the delivered quantity back to the order lines. |
| Lots and serials | Tracking per product (none, lots or unique serials), with required and uniqueness checks at posting. Generate Serials creates serial lines on a receipt move. Lots typed on receipts are created and linked automatically. |
| Packages | Put In Pack, Unpack, package history and package types. A "Require All Products to Be Packed" rule per operation type. |
| Scrap and counts | Scrap with an insufficient-stock warning. Physical counts are recorded on stock balances, then applied or cleared. |
| Batch transfers | Group transfers and validate them together. |
| Barcode | A Barcode Scanner page (camera or USB scanner) for draft receipts with one line per product, and an external portal for assigned scanner users. |
| Printing | Picking Operations and Delivery Slip templates. Print on Validation can attach the Delivery Slip, Reception Report or Return Slip to the transfer as a Word file; all these switches are off in the master app. |
| Dashboards | Inventory Operations (Waiting, Ready, Late, Draft) and Inventory Reporting (Stock, Moves, Returns). |

## Added on 17 Nov 2026

Built and tested on 17 Nov 2026. A check on 27 Nov 2026 found their scheduled workflows enabled *(Verified)*.
- **Scheduled replenishment:** a daily run at 05:30 orders every active reordering rule set to Auto.
- **Inventory at Date and Forecast reports,** in a new Inventory › Reporting group, fed by an hourly stock report sync.
- **Lot expiry alerts** (daily at 06:15) and **lot import** on receipt moves (Generate Serials / Lots).
- **Count conflicts:** when stock moved after a count, Apply asks whether to Keep Counted Quantity or Keep Difference.
- **Scrap of reserved stock:** the scrap is posted and the reservations it used are released.

## What already exists for each POC area

| Area | Already in EMS | Status |
|---|---|---|
| E-commerce by API | Products and variants with SKU and barcode; On Hand and Free To Use per location; sales orders that create and reserve the delivery; delivered quantities and returns linked to the order *(Verified 3–17 Nov)* | **Not built** |
| Exchange rates | Amounts are in MYR only; there is no currency or exchange-rate table *(Verified 27 Nov)* | **Not built** |
| External portal | An external portal for barcode-scanner users, who see only the receipts assigned to them *(Verified 3 Nov)* | **Not built** for suppliers or customers |
| Finance and dashboard | Invoicing (chart of accounts, taxes, journals, invoices and bills, payments, MyInvois), Create Invoice from sales orders, operational dashboards | **Partly there** |

Finance gaps *(Verified 17–27 Nov)*:
- no stock valuation or cost of goods sold: Inventory has no costing method;
- no purchasing or vendor-bill matching;
- general-ledger and financial-statement coverage has not been confirmed;
- no management dashboard; the current dashboards are operational.

Invoicing also has a Stripe payment-link flow; it was not re-tested.

EMS has no Purchase module, so supplier deliveries are entered as receipts *(Verified 27 Nov)*.

## Not built in Inventory *(Verified 17–27 Nov)*

- **Multi-step routes**, for example two- or three-step receipts and deliveries such as Pick → Pack → Out.
  - Route and location records exist, but chained transfers are not generated.
  - An unfinished draft workflow, `Inventory - warehouse steps`, is in the app and disabled. Leave it disabled in the POC app, or delete it there.
- Wave transfers.
- Nested or repacked packages (single-level packages only).
- Stock valuation.
- Automatic lot dates from product durations (lot dates are entered by hand).
- Label printing, and most barcode-scanner options (Require Product Scan, Allow Extra Products, location and lot scan options, Put in Pack timing). Only "Require All Products to Be Packed" is enforced.
- Purchasing and manufacturing: reordering cannot raise an RFQ or a manufacturing order.

## Known limits *(Verified 17 Nov, measured in the EMS master)*

- A receipt into a location with an active putaway rule takes about 50–80 s per line. Receipts without rules validate in about 3 s, and deliveries in 2–7 s.
- About 100 lines per document and per batch step (a platform input limit).
- Several users validating the same stock at the same moment is not coordinated; avoid it.
- One detailed line reserves from one location, so stock spread over several shelves gives a partial reservation.
- The scanner supports draft receipts with one move and one line per product.
- The EMS master ran about 1,700 workflow executions a day from 20 to 26 Nov 2026, the same every day *(usage statistics, 27 Nov)*.

## Module dependencies and removal

**How the modules depend on each other** *(Verified 17 Nov 2026, from the app's field and workflow references)*
- Inventory's own fields point only to Products (21 fields), Contacts (10) and Sales (2: Transfer.Sales Order and Stock Moves.Sales Order Line). No Inventory field points to POS, Invoicing, CRM or Activities.
- Inventory workflows read Products and Contacts. They write to Sales (Quantity Delivered on order lines) and to POS (`WF_POS_Transfer_MarkOrderDelivered` and `WF_POS_Transfer_MarkOrderFailed` on Transfer update POS Orders).
- Sales creates Inventory deliveries (`Inventory - Sales Order creates Delivery`, `Inventory Sub - Sales line to Stock Move`). POS creates Inventory transfers, moves and serial lines (`POS: Deliver Stock`, `POS: Return Stock` and their sub-processes).
- Second level: Products has 6 fields pointing to Invoicing (income and expense accounts, sales and purchase taxes). Contacts has 7 (receivable and payable accounts, payment terms, payment methods, fiscal position) and 1 pointing to Sales (Quotation Templates).

**If you remove a module** *(derived from the references, not tested)*
- **Point of Sale:** remove the two `WF_POS_Transfer_…` flows on Transfer and the POS System sheet under Dashboards. POS's own links into Inventory go with it.
- **Sales:**
  - Transfer.Sales Order and Stock Moves.Sales Order Line lose their target.
  - Remove `Inventory - Delivered quantity to Sales` and `Inventory Sub - Recompute sales line delivered`.
  - Deliveries must then be created another way: by API, from e-commerce or by hand.
  - Contacts.Quotation Templates and the app-level flow `Stock availability: hourly` also point at Sales.
- **Invoicing:**
  - Nothing in Inventory refers to it, but the 13 Products and Contacts fields above lose their target; remove or re-point them.
  - The app-level flows `Book a Stripe payment`, `MyInvois: Document Synchronization` and one Invoices/Journals loop go with it.
- **CRM and Activities:**
  - Neither links to Inventory.
  - Sales has 2 fields pointing to CRM, and the Configuration Dashboard has CRM and Sales tabs.
  - The app-level flow `Calculated Probability` goes with CRM.
- **Always** re-test after removing anything.
- The "View reference" list does not include business-rule actions, so an empty list does not prove that a field is safe to delete *(Documented)*.

## Test material outside Inventory

Listed on 17 Nov 2026; not removed from the EMS master.
- Sales › Orders: the button "ZZ obsolete – Deliver", shown in no view; its workflow is disabled.
- Two enabled workflows, "TEST batch probe" and "TEST MyInvois filters". Their trigger sheet could not be read (probably deleted). They read Contacts, Orders and Invoices.
- 7 POS buttons and 5 CRM stage buttons shown in no view, and a POS "Register Payment" button set to run a workflow that does not exist.
- Test records in every module, Inventory included: for example test leads, QA lots, packages, transfers and archived test warehouses.

## Inventory build rules

Keep these rules when you extend Inventory.
- **Document chain:** Transfer → Stock Moves (one per product) → Stock Move Lines (lot, package, from and to location) → Stock Balances. A Stock Balance is one row per product + location + lot + package + owner. Its Stock Dimension Key holds these five IDs in JSON.
- **Stock changes only by posting.** On-hand and reserved quantities change only through the posting workflows (Validate, reservation, scrap, count apply), and each posting leaves a ledger trail. Never edit Stock Balances by hand or by a direct record update; use a transfer, a scrap or a count.
- **Errors show on the transfer,** in Stock Validation Message, with a prefix such as [Putaway], [Barcode], [Serials] or a ledger error. A refused action changes nothing.
- **Naming:**
  - Workflows are named `Inventory - …`. Shared sub-processes are reused by several flows; for example, the reservation step serves Mark as To Do, Sales → Delivery and the daily run.
  - Fields added by Nocoly use the `x_inventory_…`, `x_pkg_…` and `x_…` aliases.
  - Fields named "(Service)" mirror Odoo fields and may be unused.
- **Platform lessons:**
  - Checkbox and number values reach code steps as text such as "1.0", so parse them as numbers.
  - A relation field used directly as a code-step input can fail; pass a text field instead.
  - Batch nodes and code steps take at most 100 rows.
  - A workflow's own writes do not re-trigger it, and lookup values read inside a running flow can be stale.
- **Other behaviour to know:**
  - If a receipt was refused once and its lines still carry an error, putaway rules are not re-applied on the retry, so the stock stays at the receipt's destination.
  - New lots are created when the name is entered, not at validation, so a cancelled receipt leaves its new lot records behind.

## Faults in the 17 Nov export

An earlier export of EMS, made on 17 Nov 2026, has two faults that were fixed in the EMS master later that day. The 27 Nov export should carry the fixed flows; check both in Stage 1.
1. **Lots typed on receipts were not created or linked.** In `Inventory - Lot/Serial from name`, the step "Lot from name - current lot" looked the lot up by the line's empty Lot field. The fix reads the related record from the trigger record's Lot/Serial Number field instead, continuing when it is empty.
2. **Scrap worked for one product only.** The Scrap Math step of `Validate Scrap (Native)` and `Continue Scrap` refused every product except one hard-coded variant, and always posted with tracking "none". The fix takes the product's Tracking as an input and posts with serial, lot or none to match.

Do not use the 17 Nov export for the POC.
