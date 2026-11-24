# Modules of EMS (ERP Master) and who owns them

**Status: draft, 24 Nov 2026.** Counts come from a read-only scan of the app that day (`STATE-2026-11-24.md`).
The *Module Owner* column is for the App Owner to fill in; until it is filled, a builder treats every module but
their own as read-only (`PARALLEL-BUILD.md`).

**Reference column:** the proposal is the local Odoo 20 plus the owner's online instance (`REFERENCES.md`) for every
module; *to decide* marks the modules that never had a reference recorded.

The app is now named **EMS** (renamed again after "CRM odoo"). `build/hap.py` still accepts only
`('CRM odoo', 'ERP Master')`, so the builder scripts' safety checks refuse to run until "EMS" is added there.

## Modules

| Menu group | Worksheets | In `build/ids.json` | Workflows | Documented in 19.0 | Module Owner (role holder) | Reference |
|---|---:|---:|---:|---|---|---|
| Contacts | 7 | 4 | 10 | 01, 11, 12, 20. Not: Companies, Country Groups, MSIC Codes | *to fill* | saas~19.4 extracts + 19.0 source |
| Products | 6 | 4 | 17 | 02, 03, 04, 08. Not: Pricelists, Price Rules | *to fill* | saas~19.4 extracts + 19.0 source |
| Invoicing | 14 (+1 page) | 8 | 69 | 05, 06, 07, 09, 10, 13, 19, 21. Not: Fiscal Positions, Fiscal Position Accounts, Payment Methods, Payment Method Lines, Payments, MyInvois Documents, MyInvois Setup | *to fill* | saas~19.4 extracts + 19.0 source; MyInvois: LHDN's specification |
| Sales | 2 | 2 | 43 | 16, 17, 18, 21, 22, 23 (no rows in the `REVIEWING.md` status table yet) | *to fill* | saas~19.4 extracts + 19.0 source |
| CRM | 8 | 0 | 8, plus *Calculated Probability* | 14 (a conformance check, not a hand-off). Unmerged: `codex/crm-phase2-handoff`, `codex/crm-activity-workflows`, `codex/crm-sales-relation-register` | *to fill* | *to decide* |
| Activities | 6 | 0 | 13 | None in 19.0 | *to fill* | *to decide* |
| Inventory | 25 (+3 pages) | 0 | 98, plus 16 *Putaway ID reader* and 5 timed flows | None in 19.0. Unmerged: `codex/inventory-module-removal-plan` | *to fill* | *to decide* |
| Point of Sale | 14 (+1 sheet under Dashboards) | 0 | 13 | None | *to fill* | *to decide* |
| Dashboards | 7 pages | — | — | 23 (Sales dashboard) | *to fill* | — |
| App-wide | Roles (12), option sets, app settings | Phase 1 roles | 7 timed, 4 others | *Phase 1 · Roles* in `REVIEWING.md` | App Administrator | — |

**Totals:** 83 worksheets (18 in the ledger), 11 custom pages, 298 workflows (60 in the ledger, 28 switched off),
12 roles.

## How to keep this file true

- The Module Owner updates their row when the module changes: counts from the register scan, documents, reference.
- A new menu group gets a row before its first worksheet is built.
- A worksheet that moves between modules (for example Recurring Plans, which sits under Activities but is CRM's
  `crm.recurring.plan`) is moved here and in the ledger in the same commit.

## Shared objects

Some objects belong to one module but are used by several. Changing them needs the owner's agreement and a claim on
every module that uses them.

| Object | Owner | Used by |
|---|---|---|
| Contacts, Companies | Contacts | every module |
| Products, Product Variants, Units & Packagings | Products | Sales, Invoicing, Inventory, POS |
| Taxes, Fiscal Positions, Journals | Invoicing | Sales, POS |
| Activities and plans | Activities | CRM, Sales, Inventory |
| Roles | App-wide (App Administrator) | every module |
