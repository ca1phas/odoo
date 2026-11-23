# <NN> <Module name>: module plan

> Copy this file to `NN-<module>.md`. Fill every section before building. A plan is only approved when the reviewer and date are filled in below.

| | |
|---|---|
| Status | Draft / In review / **Approved** (by …, date) / Building / Accepted |
| Odoo reference | 20.0 open source, commit … (`catalogue/odoo-20.0/`), and/or candy99 (20.0+e) screens. For Enterprise-only parts there is no source: say so. |
| Owner in Nocoly | who builds and owns it (a colleague's module is not changed without them) |
| Depends on | modules that must exist first |
| Size | S / M / L, with the main cost drivers |

## 1. Scope

- **Odoo modules covered:** the app module, the extensions to include, and the bridges to include. Take the list from `catalogue/odoo-20.0/modules.csv`, then pick.
- **Main business flows**, as Odoo's menus show them, e.g. "Receipts: receive, check, validate, backorder".
- **Out of scope**, each with a reason: Enterprise-only, needs hardware, needs another module, low demand.

## 2. Dependencies and bridges

- **Foundation used:** Contacts, Products/Variants/Units, Company/Currency/Taxes, Activities. For each, say whether it exists in EMS and who owns it.
- **Apps it needs:** must already exist in EMS, or be planned first.
- **Bridges:** for each other app, say what the pair needs, whether it is built now or later, and which side owns it. Example: Sales + Inventory = `sale_stock` (delivery from a confirmed order, delivered quantity on order lines).
- **Fields added to other modules' sheets** (Odoo `_inherit`): field, target sheet, the owner's approval. These are tagged to *this* module in the register, so a split keeps them.

## 3. Data model (HAP worksheets)

| Odoo model | HAP worksheet | New / reuse | Key fields and relations (target module) | Notes |
|---|---|---|---|---|

- Use Odoo field names as aliases and Odoo's English labels as names.
- Sheets that users never open go in a "System Tables" group.

## 4. Business logic (HAP workflows)

| Odoo behaviour (method, source file) | HAP implementation (trigger, workflow, sub-process) | Platform limit met | Mitigation |
|---|---|---|---|

Known limits to design around:
- Code blocks stop after 10 seconds.
- A query returns at most 100 rows per step.
- Workflow writes are not one transaction (use commit markers, rechecks and strict serial runs).
- A lookup on an empty value stops the run.
- Writes only start other flows when the flow allows it.

## 5. User interface

**Rule:** HAP stays the system of record. A Compute page reads and writes through HAP and starts the same workflows, so no business rule exists only in Compute.

| Screen / task | Odoo today (steps) | EMS today (steps), if built | Native HAP / custom field / Compute | Why | Target: steps and clicks vs Odoo |
|---|---|---|---|---|---|

- **Native HAP:** lists, forms, kanban, calendar, Gantt, charts and custom pages where they are good enough.
- **Custom field:** a widget inside a form (React/Tailwind, up to 5 per sheet) for presentation the form cannot do. Examples: status bar, tax breakdown, counters. It never holds a rule.
- **Compute:** screens where HAP's standard UI is weaker than Odoo, or where we can be clearly easier. Examples: a scanner screen, a planning board, a one-page "do the task" screen that replaces several forms.
- **For each Compute screen:**
  - what it reads and writes;
  - sign-in (public, or HAP sign-in) and whose permissions apply;
  - how it is opened (link, or embedded in a HAP page);
  - what happens when Compute is down.
- **No-feature-cut checklist:** every Odoo feature in scope maps to where it lives (HAP native / Compute / not built + reason). Nothing is dropped silently.

## 6. Roles and permissions

- Odoo groups → HAP roles: what each role sees and can do.
- Compute screens must apply the same rules (see the open question in `README.md` §6).

## 7. Documents, reports and notifications

Print templates, dashboards/pivots, emails, activities and scheduled jobs.

## 8. Data

Seed and demo data, migration from current EMS records, test records named `TEST …`.

## 9. Acceptance tests

| # | Scenario | Steps | Expected (as candy99 does it) | Proof (readback / screen) |
|---|---|---|---|---|

Cover the main flows, the exceptions (cancel, return, partial, wrong input), the bridges and the permissions.

## 10. Register entries

Components this module adds or changes, with kind **core / foundation / bridge A+B**, for `catalogue/` and the EMS register scan.

## 11. Work order, effort and risks

Build order inside the module (data → logic → native UI → Compute UI → tests), effort per part, and risks with how they are reduced.

## 12. Open questions and decisions needed

Each item: who decides and by when.
