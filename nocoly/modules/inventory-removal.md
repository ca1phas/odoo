# Inventory module removal plan

12 October 2026 · ERP Master · **Plan only; no application objects have been removed.**

**Delivery:** duplicate ERP Master, remove Inventory from the **client copy**, keep CRM / Sales / shared foundations.
Never apply the source IDs below as deletion targets on the original Master app.

## At a glance

| Remove from the client copy | Keep |
|---|---|
| 22 Inventory worksheets: 21 business tables + hidden Scan Requests | All 41 non-Inventory worksheets and their records |
| All fields, form sections, child controls, rules, actions and views owned by those tables | Existing shared fields, including Sales delivery fields |
| 80 known Inventory workflows: 79 registered + 1 unbound QA process | 130 registered non-Inventory workflows |
| Inventory Operations + Inventory Reporting dashboards; 35 registered Inventory reports | CRM / Sales dashboards and the shared Configuration Dashboard |
| Configuration → Inventory tab and its four components | Configuration → CRM / Sales / Settings content and the tab container |
| Products → `x_inventory_tracking` only, after detaching consumers | Products / Variants / Units / Categories and existing Inventory-labelled tabs |

Counts describe the reviewed evidence, **not a fresh live-app audit**. Worksheets/workflows/relations were captured
10–11 Oct; views/reports were registered 6 Oct. Refresh every target before execution.
Inventory behavior is still partly validated; this document does not claim full Odoo parity.

The [ID manifest](inventory-removal.manifest.json) is an **ownership/reference register, not a deletion script**.
It contains the full workflow, view, report, shared-field and cross-module Relation lists.

## 1. Worksheets to remove

For **each** table below, remove its owned fields (visible and hidden), sections, inline child fields,
business rules, record actions, worksheet settings, views and records only after backup and dependency checks.
Deleting a Relation must not delete its shared Product, Contact, Unit or Sales target records.

| Operations | Transfer | `6ac303825e337edf2bf1b7b4` |
| Operations | Batch Transfers | `6ac3239e6f62fbbb4fe6e662` |
| Operations | Scrap | `6ac3253c6f62fbbb4fe6e6cc` |
| Stock & Tracking | Lots & Serial Numbers | `6ac3227691143e1169ecc09f` |
| Stock & Tracking | Packages | `6ac323976f62fbbb4fe6e656` |
| Warehouse Setup | Warehouses | `6ac3227b896787ba363048f6` |
| Warehouse Setup | Locations | `6ac322810e590eb436fe2d65` |
| Warehouse Setup | Operation Types | `6ac3228791143e1169ecc0aa` |
| Warehouse Setup | Package Types | `6ac3239291143e1169ecc0f8` |
| Warehouse Setup | Storage Categories | `6ac324655e337edf2bf1be83` |
| Warehouse Setup | Scrap Reasons | `6ac325585e337edf2bf1bee6` |
| Routes & Rules | Routes | `6ac3222e5e337edf2bf1bdda` |
| Routes & Rules | Reordering Rules | `6ac325100e590eb436fe2eff` |
| Routes & Rules | Putaway Rules | `6ac324486f62fbbb4fe6e68f` |
| System Tables | Stock Moves | `6ac3228d6f62fbbb4fe6e613` |
| System Tables | Stock Move Lines | `6ac323960e590eb436fe2dd9` |
| System Tables | Stock Balances | `6ac323b20e590eb436fe2e1c` |
| System Tables | Stock Rules | `6ac324096f62fbbb4fe6e66e` |
| System Tables | Storage Capacity Lines | `6ac32486896787ba36304a3d` |
| System Tables | Package History | `6ac3239a896787ba36304950` |
| System Tables | Stock References | `6ac325820e590eb436fe2f39` |
| System Tables | Scan Requests | `6aca5bb06f62fbbb4fe7cb54` |

- Receipts / Deliveries / Internal Transfers are **views of Transfer**, not three separate worksheets.
- Physical Inventory / Stock / Replenishment / history screens are views, not additional tables.
- Remove all **70 registered views**, the Scan Requests default view, and any later verified Inventory-owned views.
- Removal Strategies was already deleted. **Do not recreate it or purge the recycle bin.**

## 2. Shared worksheets to keep

Inventory removal alone is **not** permission to prune any of these bundles.

| Area | Keep every listed worksheet |
|---|---|
| CRM | Leads, Stages, Lost Reasons, Sales Teams, CRM Tags, Campaigns, Mediums, Sources |
| Sales | Orders, Order Lines; quotation templates remain records in Orders |
| Contacts | Contacts, Contact Tags, Countries, States, Country Groups |
| Products | Products, Product Variants, Units & Packagings, Product Categories, Pricelists, Price Rules |
| Finance | Invoices, Invoice Lines, Journals, Chart of Accounts, Taxes, Fiscal Positions, Fiscal Position Accounts, Payment Terms, Payment Term Lines, Payment Methods, Payment Method Lines, Payments, Incoterms |
| Activities | Activities, Activity Types, Activity Plans, Activity Plan Steps, Activity Plan Launches, Recurring Plans |
| Project | Projects |

Keep their existing records, forms, rules, roles, workflows, reports and navigation unless an **explicitly reviewed
Inventory reference** needs a field/node/component-level replacement. Do not delete a mixed-use object wholesale.

## 3. Fields and CRM / Sales bridges

| Location / ownership | Decision | Why |
|---|---|---|
| Products.Tracking — `x_inventory_tracking`, field `6ac668b35e337edf2bf21647` | Remove after Inventory consumers are detached | The one explicitly added Inventory-only shared-table extension |
| Products / Product Variants → existing Inventory tab, Weight, Volume, Cost, Barcode, Unit and Packagings | Keep | Pre-existing product/Sales controls; the tab title does not establish Inventory ownership |
| Orders → Delivery Status, Delivery Date, Delivery Address, Incoterm and Incoterm Location | Keep | Existing Sales-owned fulfillment/trade fields |
| Order Lines → Quantity Delivered, Left to Deliver, delivery helper formulas, Quantity Invoiced and invoice links | Keep | Existing Sales / Finance behavior; preserve historical values |
| Transfer.Sales Order — `sale_id`, field `6ac313b75e337edf2bf1ba17` → Orders | Remove with Transfer; keep Orders | **Inventory–Sales bridge**, stored on the Inventory side |
| Stock Moves.Sales Order Line — `sale_line_id`, field `6ac327555e337edf2bf1bf70` → Order Lines | Remove with Stock Moves; keep Order Lines | **Inventory–Sales bridge**, stored on the Inventory side |
| Transfer.Project — `x_project_id`, field `6ac313b75e337edf2bf1ba1a` → Projects | Remove with Transfer; keep Projects | Inventory–Project traceability link |
| Inventory → Contacts / Products / Product Variants / Units / Product Categories | Remove source Relations with their Inventory tables; keep target records | Shared input/reference masters |
| Leads ↔ Orders; Leads ↔ Activities; Activities → plans / steps / launches | Keep unchanged | CRM–Sales and CRM–Activities bridges, not Inventory |
| Orders ↔ Invoices; Order Lines ↔ Invoice Lines | Keep unchanged | Sales–Invoicing bridge |

**Observed direction:** all 32 physical cross-module Relations in the reviewed snapshot originate in Inventory;
no retained worksheet directly relates back into Inventory. This is **not** proof that all workflow/page/formula
dependencies are absent. Expanded `relationControls` catalogues are not additional physical Relation fields.

Named packs for future ownership: **inventory-sales**, **inventory-project**, **product-inventory-tracking**.
If a new reverse Stock Moves / Transfers / warehouse Relation or lookup appears on Orders, Order Lines, Products,
Variants, Categories, Contacts or Activities, classify its consumers before removing it. Unknown dependencies block
deletion; they are not automatically approved by this plan.

**Sales without Inventory:** keep the existing Sales-owned **Deliver** flow and delivery quantities/status formulas.
Do not reset historical delivered values. Stock-aware automatic Sales writeback has not been certified; inspect the
latest workflow graph before choosing any manual fallback. Inventory-off must have no stock-posting side effects.

## 4. Workflows to disable, drain, then remove

The manifest lists **80 exact source IDs** (79 registered + one unbound QA), grouped by trigger worksheet. Similar names such as Validate / Confirm /
Cancel occur in other modules: match **ID + trigger + ownership**, never name alone.

| Owner | Remove workflow families |
|---|---|
| Transfer | Initialize Draft; Mark as To Do; reserve after confirmation; Check Availability; Unreserve; Validate; Cancel Transfer; Create / No Backorder; Create Return; Put In Pack |
| Stock Moves | Initialize Draft; prepare move lines/reservation details; remaining demand/moves; settle completion; return calculation/reverse moves; Package Posting History |
| Stock Move Lines | Quantity-in-unit; ledger preparation; stock allocation; posting availability; scrap ledger; remaining/reverse tracking details; packing preflight; per-line history |
| Batch Transfers | Initialize Draft; Confirm; Validate; Cancel / Detach |
| Scrap | Validate Scrap (Native); Continue Scrap |
| Stock Balances | Record Count; Clear / Apply / Apply All; selected-count/clear loops; package preflight/unpack ledger |
| Packages | Refresh Contents; Unpack |
| Reordering Rules | Snooze; Undo Manual Quantity; Refresh Replenishment; Order; Automate |
| Inventory navigation | Moves, Returns, Batch, Add a Product, Transfers, Detailed Operations, Stock Operation, Location, Routes, Putaway Rules, Products, Add a Capacity, Locations, Add a Rule, Stock Moves — only the Inventory-owned processes |
| Inventory QA | Packing Guard Setup; Incoming Package History QA; Serial Relation Query QA; Apply Putaway (QA PUT); Scan Queue Probe; Button Snapshot |
| Scan Requests | Queue QA `6aca5bd1a7d6780599e63ba8`; Independent Scan Requests QA `6aca5eb85fa8a0f296a647b7` — both disabled in final evidence |
| Unbound Inventory QA | Barcode Decision QA `6ac66b9fa7d6780599a86407` — unpublished, disabled, blank trigger; remove only if present in the copy and ownership is re-confirmed |

Remove parent callers before their reusable child processes. Confirm no retained workflow calls an Inventory child;
replace only the reviewed bridge nodes if a mixed Sales process does. **Disabled processes also require cleanup.**
Do not retry old posting or scan test fixtures to “drain” them; quarantine/export unfinished requests.

**Keep:** CRM stage/probability/activity/meeting workflows; Sales quotation, template, signature, discount, pricing,
delivery, email, invoice and Stripe flows; shared Contact/Product/Variant/Unit and Finance automations.
In particular preserve **Deliver**, **Deliver: one product line**, and the **Orders: Delivery Status…** workflows.

## 5. Dashboards, reports, navigation and other assets

| Object | Decision |
|---|---|
| Inventory Operations Dashboard — `6ac3cdf32c3553b4049313f5` | Remove entire page and its Inventory-only embeds/buttons |
| Inventory Reporting Dashboard — `6ac3ce082c3553b4049313f7` | Remove entire page and its Inventory-only embeds/buttons |
| 35 registered Inventory reports | Detach every consumer, then remove report objects if not automatically removed with their pages; no shared report deletion |
| Configuration Dashboard — `6aba250de320fa9d4cd87cbd` | **Keep page.** Remove only Inventory tab `a6c75dd0-6283-448a-9d34-33d0b559ec56` and its intro / Warehouse Setup / Routes & Rules / Storage & Tracking components |
| CRM Pipeline, Sales Operations, Sales Performance, Sales Manager dashboards | Keep unchanged; remove a future Inventory-only widget only after explicit dependency review |
| Dashboards group — `6aba24fae320fa9d4cd87cb6` | Keep |
| Inventory group — `6ac3036bbd1c7ff411530849` | Remove after its contents; remove Operations / Stock & Tracking / Warehouse Setup / Routes & Rules / System Tables children |
| Transfer print templates | Remove **Picking Operations** and **Delivery Slip** after resolving their copied IDs; keep Sales quotation/invoice templates |
| Inventory rule/action/grant references | Remove only Inventory-scoped entries, including Scan Requests saved-input rule `6aca611a5e337edf2bf29fbc` |
| Existing roles and memberships | Keep; remove only grants to removed Inventory objects, not entire roles |
| Shared integrations / API library | Keep Stripe, meeting/OAuth connections and other shared authorization; remove only a proven Inventory-exclusive binding |

An action's attached worksheet determines its ownership. Do not delete a global API connection merely because an
Inventory workflow used it. After page removal, check for standalone reports, scheduled jobs, public links, print
templates and role grants that the platform may not cascade.

## 6. Execution order — later, not in this task

1. **Confirm the client copy and enabled modules.** If retained Purchase / Manufacturing / POS / Repairs / valuation
   still consumes stock, stop until an approved replacement or removal plan exists.
2. **Back up and map IDs.** Export configuration, records and attachments; establish recovery. A local schema snapshot
   alone is not a full restore point. Source IDs are hints: resolve copied IDs by name, type, ownership and relations.
3. **Fresh dependency scan.** Read schemas, formulas, defaults, rules, actions, workflow graphs/callers, views, reports,
   pages, printing, roles and integrations. Record explicit keep/remove/replace decisions for unexpected consumers.
4. **Freeze Inventory.** Hide its entry points, stop new requests, disable Inventory flows and drain/quarantine runs.
5. **Detach consumers first.** Remove Inventory dashboard/configuration/report/action links and approved bridge nodes.
   Never replace an entire shared worksheet/page configuration from an old snapshot.
6. **Remove processes and the one extension.** Delete Inventory workflows after caller checks, then Products.Tracking.
   Preserve the pre-existing Product Inventory tabs and all other shared fields.
7. **Recycle owned worksheets.** Detach internal reciprocal/child-form references as required, then remove all 22
   tables and their owned assets. Preserve audit exports; no permanent recycle-bin purge.
8. **Finish and verify.** Remove empty Inventory navigation and only its role grants; read back retained objects and
   run the smoke tests below. Keep a final before/after/removal record.

All relation-related changes are **serial, one writer**. Do not use multiple agents to edit connected schemas.

## 7. Post-removal acceptance

| Check | Expected |
|---|---|
| Reference sweep | No retained field, formula, rule, action, workflow, report, page, template or grant points at a removed object |
| Shared schemas / data | All 41 retained tables and their mapped IDs/records remain; only the explicit Tracking extension is removed |
| CRM | Opportunity creation, stage changes, Activities, meeting link/calendar and Lead → quotation remain usable |
| Sales | Product/unit/tax/pricelist/template selection; quotation → confirm → Sales-owned Deliver → invoice still work |
| Sales communication/payment | Quotation email/PDF/template, signature and Stripe paths retain their previous behavior; use an authorized test recipient and Sandbox only |
| Dashboards | Five retained pages remain; Configuration keeps its other tabs; no dead Inventory navigation |
| Workflow / role scope | 130 baseline non-Inventory processes and existing roles/memberships remain; actual role checks pass |
| History / stock boundary | Historical Sales quantities/statuses unchanged; no new stock postings; backup/recovery reference recorded |

## Evidence and repository alignment

- Remote `19.0` was checked on 12 Oct: `be5fa501109060bb6b08432589b34ccb51fbdde8`; no pull/merge was needed
  because the local remote-tracking ref matched it. This documentation branch starts from that commit.
- [Master architecture](../README.md), [decisions](../DECISIONS.md), [original dependency plan](../plan/phases.json).
- [Earlier CRM/Sales register](https://github.com/ca1phas/odoo/blob/codex/crm-sales-relation-register/nocoly/CRM-SALES-RELATIONS.md)
  remains on its separate branch (`6fda5fcca55`); this plan does not merge it or mark it part of `19.0`.
- Reviewed Inventory evidence is from saved configuration/readback/acceptance files, **not a new live-app audit**.
  Exact local evidence paths and SHA-256 hashes are recorded in the manifest; raw payloads/customer data are not committed.
- A fresh target-side readback and dependency sweep are mandatory before using this plan to delete anything.
