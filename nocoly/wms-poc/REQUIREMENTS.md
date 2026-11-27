# Requirements

## What the client asked for

**Core need:** a warehouse management system with IoT integration. *(Client request, passed on by the Account Lead, 27 Nov 2026)*

**For the POC** *(Client request, 17 Nov 2026, as written)*:
1. Showcase how the platform can connect to an e-commerce platform via API.
2. Add a currency exchange feature with daily rate updates via API.
3. Provide an external portal for suppliers or clients.
4. Add finance department & functions and a management dashboard.

**Where it stands:** the client's project lead has seen the PoC demo and was happy with it. The next step is a full presentation in Chinese for the client's management. *(Account Lead, 27 Nov 2026)*

## What is not known yet

No answers from the client have been recorded. Still unknown:
- platforms, volumes and currencies;
- user groups, finance scope and KPIs;
- IoT devices;
- the presentation date, and how deep each demo must go.

## Questions for the Account Lead

Needed before Stage 1 ends.
- The presentation date and audience.
- For each demo area: a showcase only, or hands-on use?
- Is IoT in this presentation? Which IoT platform or partner?
- Chinese labels in the app, or English labels with Chinese narration?
- Does the client sell over the counter? (This decides whether Point of Sale stays.)
- Which e-commerce platform, if known.
- Which Compute capabilities the PoC demo used. None was found in EMS.

## Questions for the client

Mostly for Stage 4; ask some earlier if a demo needs them.

**E-commerce**
- Platform(s) and version (Shopify, WooCommerce, Lazada, Shopee, TikTok Shop, Magento or custom), API documentation, sandbox access and the owner of the integration account.
- Which system owns the product master.
- Which data flows which way, and how often: products, stock, orders, cancellations, returns and refunds, shipping and tracking.
- SKU rules (one SKU per variant? bundles or kits?) and which warehouse fulfils which order.
- Orders per day and at peak; number of SKUs.
- Payment status and cash-on-delivery handling; the order currency.
- What should happen on errors, out-of-stock items and partial shipments.

**Currency exchange**
- The base currency (MYR?) and the foreign currencies used.
- The accepted rate source (for example Bank Negara Malaysia or a commercial FX API) and which rate (buying, selling or middle).
- The update time and time zone.
- Where conversion is needed (sales, purchasing, invoices, payments, e-commerce, reports).
- The rounding rules, and whether exchange gains and losses are posted.

**External portal**
- Who the external users are (suppliers, B2B clients or both) and roughly how many (for licensing).
- What each group may see and do: read status, upload documents, create orders or returns, confirm deliveries.
- Login method, branding and domain, languages, and data-privacy rules.
- Whether purchase orders are needed.

**Finance and management dashboard**
- The finance functions in scope and their owners.
- The current accounting software, and whether to integrate with it or replace it.
- Chart of accounts, tax (SST) setup and the inventory costing method (FIFO, average or standard).
- Approval matrix, MyInvois e-invoicing status, and multi-company or multi-currency needs.
- Dashboard KPIs with their definitions, refresh frequency, and who may see which figures.

**Warehouse**
- Number of warehouses; one-, two- or three-step receipts and deliveries.
- Volumes: receipts and deliveries per day, lines per document.
- Barcode and label needs; lots, serials and expiry dates.
- Whether the client sells over the counter (Point of Sale).

**IoT**
- Which devices and sensors (for example temperature, door, weight, RFID or location tags), how many, and where.
- Which events matter, and what the system should do for each: an alert, a work order, a stock movement.
- Which IoT platform or gateway the client uses or prefers, and whether anything must be sent back to the devices.
- How often devices report, and what should happen when a device goes offline.
