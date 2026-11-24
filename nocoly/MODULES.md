# Modules of EMS (ERP Master) and who owns them

**Status: 25 Nov 2026.** Owners as given by the team on 24–25 Nov 2026. Counts come from a read-only scan of the app
on 24 Nov (`STATE-2026-11-24.md`). A builder treats every module but their own as read-only (`PARALLEL-BUILD.md`).

**Ownership is recorded by role.** Each module and each app-wide object has an owner role. Who holds a role is in
one table, so a handover, or splitting a module off into a customer copy, changes one line here and nothing else.

The app is now named **EMS** (renamed again after "CRM odoo"). `build/hap.py` still accepts only
`('CRM odoo', 'ERP Master')`, so the builder scripts' safety checks refuse to run until "EMS" is added there.

**Reference column:** the proposal is the local Odoo 20 plus the owner's online instance (`REFERENCES.md`) for every
module; *to decide* marks the modules that never had a reference recorded.

## Who holds each role now

| Role | Holder | Covers |
|---|---|---|
| **App Owner** | cas | Direction and `DECISIONS.md`; deletions; anything that crosses modules. App-wide objects follow this role, not a person |
| **App Administrator** | The App Owner, unless they delegate it | Roles and their members, app settings |
| **Repo owner** | cas | Reviews and merges into 19.0; repo settings and collaborators |
| Module Owner, **Contacts** | cas | stage 0 |
| Module Owner, **Products** | cas | stage 0 |
| Module Owner, **Invoicing** (MyInvois included) | cas | |
| Module Owner, **Sales** | cas | |
| Module Owner, **CRM** | Li Wei | Recurring Plans included |
| Module Owner, **Activities** | Li Wei | |
| Module Owner, **Inventory** | Li Wei | |
| Module Owner, **Point of Sale** | hong | |

## Modules

| Menu group | Worksheets | In `build/ids.json` | Workflows | Documented in 19.0 | Owner role | Reference |
|---|---:|---:|---:|---|---|---|
| Contacts | 7 | 4 | 10 | 01, 11, 12, 20. Not yet: Companies, Country Groups, MSIC Codes | Module Owner, Contacts | saas~19.4 extracts + 19.0 source |
| Products | 6 | 4 | 17 | 02, 03, 04, 08. Not yet: Pricelists, Price Rules | Module Owner, Products | saas~19.4 extracts + 19.0 source |
| Invoicing | 14 (+ MyInvois Setup page) | 8 | 69 | 05, 06, 07, 09, 10, 13, 19, 21. Not yet: Fiscal Positions, Fiscal Position Accounts, Payment Methods, Payment Method Lines, Payments, MyInvois Documents, MyInvois Setup | Module Owner, Invoicing | saas~19.4 extracts + 19.0 source; MyInvois: LHDN's specification |
| Sales | 2 | 2 | 43 | 16, 17, 18, 21, 22, 23 (no rows in the `REVIEWING.md` status table yet) | Module Owner, Sales | saas~19.4 extracts + 19.0 source |
| CRM | 8, plus Recurring Plans (in the Activities menu for now) | 0 | 8, plus *Calculated Probability* | 14 (a conformance check, not a hand-off). Unmerged: `codex/crm-phase2-handoff`, `codex/crm-activity-workflows`, `codex/crm-sales-relation-register` | Module Owner, CRM | *to decide* |
| Activities | 5, plus Recurring Plans (CRM's) | 0 | 13 | None in 19.0 | Module Owner, Activities | *to decide* |
| Inventory | 25 (+3 pages) | 0 | 98, plus 16 *Putaway ID reader* and 5 timed flows | None in 19.0. Unmerged: `codex/inventory-module-removal-plan` | Module Owner, Inventory | *to decide* |
| Point of Sale | 14 (+1 sheet under Dashboards) | 0 | 13 | None | Module Owner, Point of Sale | *to decide* |
| Dashboards | 7 pages | — | — | 23 (Sales dashboard) | Each page's module (below) | — |
| App-wide | Roles (12), option sets, app settings | Phase 1 roles | 7 timed, 4 others | *Phase 1 · Roles* in `REVIEWING.md` | App Owner (see *App-wide objects*) | — |

**Totals:** 83 worksheets (18 in the ledger), 11 custom pages, 298 workflows (60 in the ledger, 28 switched off),
12 roles.

**Dashboards and pages:**

| Page | Owner role |
|---|---|
| CRM Pipeline Dashboard | Module Owner, CRM |
| Sales Operations Dashboard, Sales Performance Dashboard, Sales Manager Dashboard | Module Owner, Sales |
| Inventory Operations Dashboard, Inventory Reporting Dashboard, Barcode Scanner, Inventory at Date, Forecast | Module Owner, Inventory |
| POS System (a worksheet under Dashboards) | Module Owner, Point of Sale |
| MyInvois Setup | Module Owner, Invoicing |
| Configuration Dashboard | App Owner (for now) |

## App-wide objects: by role, department or module

Proposed 25 Nov 2026; the App Owner confirms. The rule behind it: an object belongs to the module whose work it
serves; what serves the whole app belongs to the App Owner role; and **who** gets rights or tasks is decided by
role, department or job position, never by a named person, so that a handover changes the organisation, not the
app.

| Object | Owner role | Note |
|---|---|---|
| App settings, menu groups and their order | App Owner | |
| The built-in roles (Administrator, Operator, Developer) and Member | App Owner; edited by the App Administrator | Every module depends on them |
| Accounting Administrator, Accountant, Invoicing, Accounting Read-only | Module Owner, Invoicing decides their rights; the App Administrator edits them | |
| Salesperson - Personal Pipeline | Module Owner, CRM | |
| Sales Manager | Module Owner, Sales, with the CRM owner's agreement (*to confirm*) | Its rights span CRM and Sales |
| POS Cashier, POS Manager | Module Owner, Point of Sale | |
| Who is a member of each role | App Administrator | Assign by department or job position where HAP allows it, not by named people |
| Approvers and notification or CC recipients in workflows | The workflow's module | Point them at a role, department or job position, not a person |
| Views, rules or filters that name a person (the September notes mention a My Pipeline filter fixed on one salesperson) | The module | Replace with "current user", a role or a department |
| Timed workflows | Their module: MyInvois synchronisation → Invoicing; the stock and Inventory runs → Inventory | The switched-off *Unnamed Workflow* → App Owner, to sort out |
| Workflows outside any worksheet | *Calculated Probability* → CRM; the 16 *Putaway ID reader* → Inventory; *Book a Stripe payment* → *to confirm* (Invoicing or Point of Sale); the two *Loop* → App Owner, to sort out | |
| Option sets used by several modules | App Owner | |

## Shared objects

Some objects belong to one module but are used by several. Changing them needs the owner's agreement and a claim on
every module that uses them.

| Object | Owner role | Used by |
|---|---|---|
| Contacts, Companies | Module Owner, Contacts | every module |
| Products, Product Variants, Units & Packagings | Module Owner, Products | Sales, Invoicing, Inventory, POS |
| Taxes, Fiscal Positions, Journals | Module Owner, Invoicing | Sales, POS |
| Activities and plans | Module Owner, Activities | CRM, Sales, Inventory |
| Recurring Plans (in the Activities menu; Odoo's `crm.recurring.plan`) | Module Owner, CRM | CRM; may move to the CRM menu later |
| Roles | App Owner; edited by the App Administrator | every module |

## How to keep this file true

- **When a role changes hands, change one line** in *Who holds each role now*.
- The Module Owner updates their row when the module changes: counts from the register scan, documents, reference.
- A new menu group gets a row, and its Module Owner role a holder, before its first worksheet is built.
- A worksheet that moves between modules (for example Recurring Plans into the CRM menu) is moved here and in the
  ledger in the same commit.
