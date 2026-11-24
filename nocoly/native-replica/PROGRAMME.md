# Odoo modules on HAP + Compute: programme plan

**Status:** updated 24 Nov 2026. Wave 0 is built and accepted (`00-foundation-build/BUILD-LOG.md`); the CRM plan is approved and not built yet (`01-crm.md`). Owners are recorded by role (`HANDOVER.md` §2); anyone taking over starts with `HANDOVER.md`. Each module gets its own plan (`TEMPLATE.md`), and building a module starts only after that plan is approved.

## 1. Goal

- **The Programme Lead's idea:** rebuild Odoo's modules in Nocoly HAP, with AI and MCP doing the build work.
- **Use HAP Compute for the user interface** where HAP's standard screens are weaker. The aim is to be easier to use than Odoo without cutting features.
- **Plan every module before building it.** Keep the modules separable, so they can later be sold one by one.

### Where we build (decided 23 Nov 2026)

- **A new, empty master app: Odoo Replica (AI),** on Nocoly SaaS.
  - App `<uuid>`, the organisation, CLI profile `<profile>`.
  - **Purpose:** test how far an AI rebuild from scratch can go, and whether it beats our earlier build. Screens HAP cannot show natively use custom fields or Compute.
- **EMS stays as it is.** It is the baseline to beat, and the copy exported to a partner.
  - Lessons, scripts and findings from EMS are reused; its sheets and workflows are not copied.
- **The new app follows the same packaging decision:** one master app, customer copies pruned by menu group.
- **How "better than EMS" is judged,** per module:
  1. acceptance tests passed against Odoo's behaviour;
  2. steps and clicks for the main tasks, compared with Odoo and with EMS;
  3. robustness: no half-posted data, and every run is safe to repeat;
  4. build time and rework;
  5. a prune test on a copy, predicted by the register;
  6. coverage of the no-silent-cut checklist.

### Odoo references

| Reference | What it gives | Limits and rules |
|---|---|---|
| **candy99.odoo.com** (20.0+e) | Real Odoo screens, including Enterprise-only apps | Only **one app can be installed at a time**; a second one triggers payment. Switching means uninstalling the current app (its data there is deleted), then installing the next. The Module Owner allowed switching without asking (23 Nov). Before each switch, export the screens and data the plans need. **Never** subscribe, upgrade or install a second app |
| **Local Odoo 20 Community** (`external/odoo20-local/`, Docker, set up 23 Nov) | Every open-source app installed together with demo data, on this PC only | No Enterprise apps; for reading screens and flows, not for customers |
| **Odoo 20.0 source** (`catalogue/`, `github.com/odoo/odoo`) | Exact rules and computations of the open-source modules | No Enterprise code |

## 2. What was checked (23 Nov 2026)

**Odoo source**
- Odoo Community is open source (LGPL-3) at `github.com/odoo/odoo`. Branch **20.0** exists; this plan read commit `530bc2789e2f` (22 Nov 2026). That is the same major version as our reference tenant candy99 (20.0+e).
- Odoo Enterprise code is not public.
- The local fork `external/ca1phas-odoo` is 19.0 and holds earlier Nocoly analysis (see §8).

**Module catalogue,** generated from the 20.0 manifests (`catalogue/odoo-20.0/`), 668 modules:
- 34 apps. Discuss, Contacts and Calendar count as foundation apps.
- 118 extensions of one app.
- 141 bridges between apps. Examples:
  - `sale_stock` = Sales + Inventory;
  - `purchase_stock` = Purchase + Inventory;
  - `stock_account` = Inventory + Invoicing (stock valuation).
- 134 foundation modules, e.g. `product`, `uom`, `analytic`, `portal`.
- 238 country localisations.
- The most connected apps are Sales (50 bridges), Project (30), Inventory (26), Events (24) and Purchase (21). Sales and Inventory sit in the middle of everything, so their plans decide much of the rest.

**Enterprise-only apps**
- 27 apps on Odoo's own app list have no module in the open-source code: full Accounting, Payroll, Documents, Sign, Subscriptions, Rental, Barcode, Shop Floor, PLM, Quality, Helpdesk, Planning, Field Service, Appointments, Knowledge, Studio and others (`catalogue/enterprise-only.md`).
- Their plans can only use candy99's screens and Odoo's documentation.

**Odoo keeps changing**
- In 20.0, batch and wave transfers moved into the core Inventory module (`stock_picking_batch` no longer exists).
- Since 18, multi-step deliveries create each next step on validation instead of up front.
- So every plan names its target version and is re-checked when Odoo releases a new one.

**EMS today** (`catalogue/ems-app-info-2026-11-23.json`)
- Sales, CRM, Inventory (32 sheets and pages), Contacts, Products, Invoicing (including MyInvois), Activities, Point of Sale and 8 dashboards.
- Not there: Purchase, Manufacturing, Project/Timesheets, HR, Website/eCommerce, Marketing, Helpdesk and the rest.

**Compute**
- It can host sign-in-protected pages and APIs on HAP data. It is still pre-release: every Compute was wiped on 19 Nov and production waits for the official version. Details and the checks to run first: `compute-for-ui.md`.

## 3. Principles

1. **One module at a time, dependencies first, ordered by real demand.**
2. **Plan before building.** Use `TEMPLATE.md`; the plan is approved before any build step.
3. **Reuse, don't rebuild.** Check the register first. Foundation data and modules that already exist are reused; a new module adds only its own core and the bridges to modules that exist.
4. **Three kinds of component:** core of one module, shared foundation, and bridge between two modules (as Odoo does). This is what makes selling by module possible: module X = X's core + the foundation it needs + bridges only to modules the customer also buys.
5. **HAP is the system of record; custom fields and Compute add presentation.** Pick the lightest option that is good enough for each screen:
   - native HAP views and forms;
   - a **custom field** (a React/Tailwind widget inside a form, up to 5 per sheet);
   - a **Compute page**.

   No business rule lives only in a custom field or in Compute, and every critical task still works in native HAP (`compute-for-ui.md`).
6. **No silent cuts.** Every Odoo feature in a module's scope is mapped to HAP native, Compute, or "not built" with a reason.
7. **Evidence:** a module is done when its acceptance tests pass against candy99's behaviour, with readback. "AI built it" is not done.
8. **Ownership:** a colleague's module is not changed without them.

## 4. Steps for each module

1. **Draft** the plan from the catalogue, the Odoo source (or candy99 for Enterprise parts) and the current EMS register.
   - Capture reference extracts of the module's models from candy99 early, because a tenant can disappear, as casimir.odoo.com did on 22 Sep.
2. **Review** it with the Module Owner and the Programme Lead (roles, `HANDOVER.md` §2), and record the approval in the plan.
3. **Build:** data → workflows → native screens → Compute screens. Compute screens wait until the Compute checks have passed.
   - Inside the module, use the September worksheet loop (`sept-plan-comparison.md` §3): requirements with *Not built now* → re-runnable build script → CLI readback → UI test → review page.
   - Check the platform trap list before building.
4. **Acceptance tests**, with proof.
5. **Update** the register and the change list (what changed since the last export to a partner).

## 5. Proposed planning order

Change the order when a deal needs something earlier. For example, a partner's end client asked for WMS, an e-commerce API, FX rates, a portal and finance.

| Wave | Module plans | Why in this wave | In EMS now |
|---|---|---|---|
| 0 | **Register and foundation:** Contacts, Products (variants, units, categories, pricelists, combos), company, currencies and rates, countries, Activities. **Plan: `00-foundation.md`** (v2 native-first, built and accepted 24 Nov) | Every other module uses them; ownership must be tagged before splitting. Taxes moved to Invoicing (wave 1), because in Odoo the Invoicing module adds them to products | To build in a new master app (v2 decision 1); "Odoo Replica (AI)" becomes the sandbox; EMS has its own |
| 1 | **Since 23 Nov: native builds in Odoo Replica (AI)** of CRM, Invoicing, Sales, Inventory, Point of Sale, in that order (`01-wave1.md`; first plan `01-crm.md`). Earlier wording: gap plans for what exists | Compare with 20.0; pick the Compute screens; finish open items (Inventory: multi-step routes, waves, nested packages, labels) | Exists |
| 2 | **Purchase**, then **Manufacturing** | Inventory needs Purchase (buy route, receipts from orders, landed costs). Manufacturing needs both | Missing |
| 3 | **Accounting depth** (beyond Invoicing: valuation entries, reconciliation, reports) | Highest risk: postings must be exact, and HAP workflows have no transactions. Full Accounting is Enterprise-only | Invoicing exists |
| 4 | **Services and HR:** Project, Timesheets, Employees, Time Off, Attendances, Expenses | A separate business area with its own bridges to Sales | Missing |
| 5 | **Website, eCommerce and customer portal; marketing** (Email/SMS, Events, Surveys); Live Chat | Public screens suit Compute well, but the website builder is very large | Missing |
| Later | **Enterprise-only apps** (Helpdesk, Planning, Subscriptions, Rental, Quality, Barcode, …) | Only when a customer asks; no source to plan from | Missing |

## 6. Decisions needed from the Programme Lead

0. **Decided 23 Nov:** build in the new app Odoo Replica (AI) on Nocoly SaaS; keep EMS as the baseline; use the local Odoo 20 Community alongside candy99.
1. **Target version:** Odoo 20.0, the same as candy99, re-checked once a year.
2. **Scope:** open-source apps first, Enterprise-only apps on demand.
3. **Packaging: already decided in September; confirm it still stands.**
   - The decision (`external/ca1phas-odoo/nocoly/DECISIONS.md`, 15 Sep 2026): one master app holds every Odoo app; a customer gets a copy with the menu groups it does not need deleted; menu groups follow Odoo's apps, so dropping an app means deleting its group.
   - Li Wei's Inventory removal plan (`nocoly/modules/inventory-removal.md`, 12 Oct, never executed) is the worked example of that method.
   - **Test:** run it on a copy of EMS and check that it predicted everything that breaks.
4. **Compute:** run the checks in `compute-for-ui.md` with one pilot screen before any module's screens depend on Compute, and wait for the official version before production.
5. **Owners: by role, not by name** (decided 24 Nov 2026, for easier handover). Each module has a Module Owner, a Builder, an App Administrator and the Programme Lead (`HANDOVER.md` §2); who holds each role is kept outside the repo. In ERP Master, Products and Sales already have Module Owners in other teams.
6. **Priorities** from current deals.
7. **Effort:** give a figure per module only after its plan. For scale:
   - The September plan estimated about 233 worksheets and 1,500 hours (~38 weeks at 40 h/week) for the Community apps. It predates the Inventory build.
   - Inventory alone has run from late September to now and still has open items.
   - So re-base the estimate on real build data before quoting it.
   - Estimate by the amount of logic, not by the number of worksheets: sheets without much logic went fast in September, while logic-heavy Inventory has taken months.
8. **Sign-off:** who signs off plans and finished modules, and within how long. In September none of the 13 finished worksheets was signed off.

## 7. Files

| File | What it is |
|---|---|
| `HANDOVER.md` | **Read first when taking over:** roles, working rules, environment, file map, planning and building a module, publishing, open items |
| `ROLE-HOLDERS.md` | Who holds each role today (private: never published) |
| `SPLIT-GUIDE.md` | How to take modules out of a customer copy with the register; per-module notes in each `*-build/SPLIT-GUIDE.md` |
| `PLATFORM-ISSUES.md` | Platform issues P1–P38, ticket-ready in Simplified Chinese, and documentation errors D1–D12; nothing is filed without approval |
| `publish/` | `make_public.py` and the public README: builds the shareable copy for the public repo (private: never published) |
| `TEMPLATE.md` | The module plan template (12 sections) |
| `compute-for-ui.md` | Compute facts, the rules for using it, the checks to run first, candidate screens |
| `sept-plan-comparison.md` | Casimir's September replica: what was built, the problems met, his plan against this one |
| `native-catalogue/` | **Start here for every module (23 Nov 2026).** What HAP does natively: every field type tested live (`fields.md`), workflow triggers and nodes (`workflow-nodes.md`), digests of all 359 pages of help.nocoly.com (`docs/`), Odoo → native mapping, limits, run rules, plan gates, open live tests (`README.md`) |
| `00-foundation.md` | Wave 0 module plan **v2, native first**: built and accepted 24 Nov 2026 in Odoo Replica (AI), 21 of 21 acceptance tests |
| `00-foundation-v1.md` | Wave 0 plan v1, approved and then superseded the same day |
| `01-wave1.md` | Wave 1 order and scope (draft, 24 Nov): CRM → Invoicing → Sales → Inventory → Point of Sale, from the Odoo 20 dependencies |
| `01-crm.md` | Wave 1 module plan **CRM**, **approved** 24 Nov 2026 with the defaults of its §12, not built yet: `crm`, `sales_team`, `utm`, native only, Phase A and B |
| `01-crm-build/` | The CRM knowledge base (`KNOWLEDGE.md`: Odoo 20 behaviour rule by rule, access rules, seed data, native mapping and traps, September lessons), its split guide and Odoo 20 reference extracts |
| `00-foundation-build/` | Build log (`BUILD-LOG.md`), step and acceptance scripts, field decisions, the review page, the ledger (`ids.json`, private) and reference data exported from the local Odoo |
| `register/` | Register tools: Odoo export, HAP scan, join, diff, prune prediction, coverage |
| `catalogue/odoo-20.0/foundation-fields.csv`, `foundation-fields-by-owner.md` | Every field of the foundation models in the local Odoo 20, with the module that defines it (generated) |
| `catalogue/odoo-20.0/apps.md` | Apps, dependencies and bridges by app pair (generated) |
| `catalogue/odoo-20.0/modules.csv` / `.json` | Every Odoo 20.0 module with its kind, apps, dependencies and auto-install (generated) |
| `catalogue/odoo_catalogue.py` | The generator: `python -I odoo_catalogue.py <odoo repo> <output dir>` |
| `catalogue/enterprise-only.md` | Apps without public code, and how that was found |
| `catalogue/ems-app-info-2026-11-23.json` | Snapshot of EMS's groups and sheets |

## 8. Earlier work to build on

Reviewed 23 Nov 2026, read-only, in `external/ca1phas-odoo/nocoly/`. This is an Odoo 19 fork: 127 commits by Casimir ("cas") from 15 to 23 Sep, and 6 by Li Wei.

| What | Where | Status | How this plan uses it |
|---|---|---|---|
| **Ground-up rebuild plan:** one HAP app; a 7-worksheet core (Contacts, Units & Packagings, Products, Product Variants, Journals, Invoices, Invoice Lines); then Odoo's app groups (CRM, Sales, POS, Inventory & Manufacturing, Services, HR, Finance, Marketing, Website, Productivity) | `README.md`, `plan/phases.json`, `artifacts/ground-up-build.html` | 14 Sep, revised 21 Sep: about 233 worksheets, 1,500 hours. Worksheets 01–13 built; none signed off | Baseline for scope and effort, to be re-based (§6.7) |
| **Decisions:** one master app with customer copies pruned by menu group; menu groups follow Odoo's apps; Products holds only the `product` module's fields and each app appends its own ("bridge-pack rule"); Odoo is the only reference | `DECISIONS.md` (14–17 Sep) | Decided | Adopted as principles 3–4 and decision 3 |
| **Inventory removal plan:** how to take Inventory out of a customer copy. Its manifest lists what to remove and keep, the bridges, unresolved items, the order of steps and acceptance checks. Workflows are matched by ID + trigger + owning sheet, never by name | `modules/inventory-removal.md` and `.manifest.json` (Li Wei, 12 Oct; addenda of 13–20 Oct not committed) | Never executed; based on 6–11 Oct snapshots | Format for the register; re-scan before any use |
| **Analysis scripts** on Odoo 19 manifests: app map with Enterprise-only marks, dependency closures and bridges, models per app, most-referenced models | `analysis/*.py`, `data/connections.json`, `data/refs.json` | Odoo 19 | Replaced for 20.0 by `catalogue/`. `fundamentals.py` and `models_per_app.py` can be re-run on 20.0 when a plan needs model-level detail |
| **Reference extracts** from the old tenant casimir.odoo.com (saas~19.4, expired 22 Sep) | `reference/odoo-19.4/` (23 models) | Historical | Use only after a candy99 (20.0) cross-check |
| **CRM ↔ Sales relation register** | branch `codex/crm-sales-relation-register`, `CRM-SALES-RELATIONS.md` (28 Sep, not merged) | Not merged | Read when planning CRM and Sales |

**Full comparison:** `sept-plan-comparison.md` covers what he built from 15 to 23 Sep, the problems he hit (we met three of them again in Inventory), his plan beside ours, and what this programme takes from it.

**Gaps in the earlier work that this programme fills:**
- **Its numbers drifted:** `README.md` and `phases.json` still show the 14 Sep figures, and the 21 Sep revision exists only in the pages.
- **Bridges were found from manifests only.** No script measured which fields a bridge adds, and nothing maps Odoo modules to the HAP objects that implement them. The EMS register scan (§9) does that mapping.
- **Enterprise apps were never measured.** `catalogue/enterprise-only.md` starts that.
- **The only worked split is Inventory,** and it left formulas, pages and rules for a later scan.

## 9. Next steps

1. The Module Owner and the Programme Lead review this plan and answer §6.
2. **Build the EMS register scan,** read-only, in the format of the Inventory removal manifest:
   - cover sheets, fields, relations, workflows (with the sub-processes they call), views, pages, print templates and rules;
   - tag each with its Odoo module and its kind (core / foundation / bridge A+B);
   - plans can then cite what already exists, and a customer copy can be pruned with evidence.
3. Write the wave 0 and wave 1 plans first, one module at a time, each reviewed before the next.
