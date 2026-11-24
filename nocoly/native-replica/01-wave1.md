# Wave 1: order and scope

| | |
|---|---|
| Status | **Draft** for the Programme Lead and the Module Owners, 24 Nov 2026. **CRM first** was chosen on 24 Nov; its plan `01-crm.md` is approved (24 Nov) and not built yet. Each module gets its own plan from `TEMPLATE.md`, approved before it is built |
| Odoo reference | 20.0 open source (`catalogue/odoo-20.0/`: dependencies from `modules.csv`, field counts from `odoo-fields.csv`); candy99 (20.0+e) for screens |
| Builds on | Wave 0 in Odoo Replica (AI), accepted 24 Nov 2026 (`00-foundation-build/BUILD-LOG.md`) |

## 1. What wave 1 means now

`README.md` §5 described wave 1 as gap plans for the modules EMS already has. Since the decision of 23 Nov the programme rebuilds natively in **Odoo Replica (AI)**, so wave 1 now means building **CRM, Invoicing, Sales, Inventory and Point of Sale** in the new app on top of wave 0. EMS stays the reference for lessons learnt, above all Inventory.

Rules that carry over from wave 0:
- Plan first; one module at a time, each plan approved before it is built (`README.md` §9).
- Native fields, workflow nodes and **views** first. Plugin views, custom fields or Compute only where native truly cannot, with the reason written in the plan.
- **Forms laid out:** short fields three or four per row, dividers for groups, long text full width; nothing one field per row.
- Every step checked in the UI; TEST records deleted after each test; platform differences logged in `PLATFORM-ISSUES.md`; no multi-agent builds.
- No feature cut: every Odoo field of the covered modules gets a decision in the register coverage.

## 2. Proposed order

The order follows the Odoo 20 dependencies, then size and risk.

| # | Module plan | Odoo modules | Needs (Odoo 20 manifests) | Size: fields declared in Odoo 20 CE | Why at this place |
|---|---|---|---|---|---|
| 1 | **CRM** | `crm`, `sales_team`, `utm` | contacts, mail, calendar, resource (no accounting) | crm 288, sales_team 74, utm 51 | Smallest and independent; reuses Contacts and Activities; Sales needs Sales Teams and UTM anyway; a visible result quickly (the pipeline) |
| 2 | **Invoicing** (two plans: 2a taxes, terms, fiscal positions, journals, invoices and bills; 2b payments and basic reconciliation) | `account`, `l10n_my`, `account_payment`, parts of `payment` | product, analytic, portal | account 2,002 (1,010 stored); payment 180 | Sales, Purchase and POS all depend on it (`sale` needs `account_payment`). Taxes and posted invoices are the riskiest logic, because HAP workflows have no transactions |
| 3 | **Sales** | `sale`, `sale_management`, bridge `sale_crm` | sales_team, account_payment, utm | sale 393, sale_management 59, sale_crm 14 | Needs CRM (teams, campaigns, opportunity → quotation) and Invoicing (taxes, invoices from orders) |
| 4 | **Inventory** (likely three plans: core transfers and stock; routes and replenishment; lots, packages and counts) | `stock`, bridge `sale_stock`; `stock_account` waits for Accounting depth (wave 3) | product | stock 1,127; sale_stock 43 | Independent of accounting apart from valuation. EMS Inventory lessons apply. The delivery bridge needs Sales |
| 5 | **Point of Sale** | `point_of_sale`, bridge `pos_sale` | account, product, resource | point_of_sale 715 | Needs Invoicing and Inventory. The till screen is the clearest Compute case: a native form is not a POS terminal |

Not recommended: Sales straight after CRM with taxes stubbed. Taxes belong to Invoicing in Odoo; building them inside Sales would be rebuilt later and would blur the register.

## 3. Outline per module (each plan details this)

**1. CRM**
- Sheets: Leads/Opportunities (`crm.lead`, one sheet with a Type), Stages, Sales Teams with members, Tags, Lost Reasons, UTM Campaigns / Mediums / Sources, Recurring Plans.
- Logic:
  - lead → opportunity conversion (create or link the customer, duplicate check);
  - stage changes, probability, won / lost with a reason;
  - expected and prorated revenue, recurring revenue;
  - assignment to teams and salespeople (capacity, round robin);
  - activities on leads, by extending the wave 0 Activities with a Lead link.
- Native views: kanban by stage with totals, list, calendar, map, charts (pipeline by stage and salesperson, won / lost). No Compute expected.
- To decide: meetings in HAP's own calendar or in a Meetings sheet; whether predictive lead scoring is in scope; creating leads from incoming e-mail (check what HAP offers natively). Lead mining and enrichment use Odoo's paid IAP: out of scope.

**2. Invoicing**
- Sheets: Chart of Accounts, Journals, Taxes with groups and repartition, Fiscal Positions, Payment Terms with lines, Invoices / Bills / Credit Notes (`account.move` with a line sub-table), Journal Items, Payments, Incoterms, Cash Rounding. Bank statements and analytic accounting: probably later.
- Logic: taxes per line (price included or excluded, groups; Malaysian SST from `l10n_my`), totals and rounding, posting with sequence numbers and balanced journal entries, due dates from payment terms, payments with partial / paid states, credit notes, fiscal position mapping, foreign currency through the wave 0 "Convert amount", lock dates.
- Risks: no transactions, so posting needs commit markers and re-checks; the 100-row query limit on large documents; rounding. This is why it is split into two plans.
- To decide: MyInvois e-invoicing in wave 1 or later (check whether Odoo 20's Malaysian e-invoicing module is open source); which taxes and accounts to seed.

**3. Sales**
- Sheets: Quotations / Sales Orders with lines; Quotation Templates with lines and optional products.
- Logic: prices from the wave 0 price function (chained pricelists still to do), taxes from Invoicing, discounts, quotation → order, lock and cancel, invoices from orders (ordered or delivered quantities, down payments), invoice status, opportunity link and "won" on confirmation (`sale_crm`), validity date.
- Documents: quotation and order PDF as a native print template.
- Native views; no Compute expected at first.

**4. Inventory**
- Warehouses, Locations, Operation Types, Transfers with moves and move lines, stock on hand, Lots / Serials, Routes and Rules, Reordering Rules, Scrap, counts, Packages.
- Lessons from the EMS build: multi-step routes, waves, lots and expiry, counts, scrap and reservations.
- Compute candidate: a scanner screen for receipts, picking and counts.

**5. Point of Sale**
- Sessions, orders, payments, closing, invoices from POS orders; the till as a Compute screen that writes through HAP.

## 4. What wave 0 already provides, and what it leaves open

- Provided: Contacts (companies, people, addresses, Region → Country, commercial fields), Companies, Products / Variants / Units / Categories, Pricelists with the price function and checker, Currencies with "Convert amount", Countries, Activities with plans and the to-do pilot, roles, form layouts.
- Open items that wave 1 touches:
  - **Chained pricelists:** Sales needs them; fix in wave 0 before or during the Sales plan.
  - **Customer pricelist on the contact:** recorded as `later:sale`.
  - **Relation pickers filtered**, e.g. Related Company to companies only.
  - **Rebuild Variants hidden from employees**, set in the role editor.

## 5. Size

Figures in days come with each module plan (`README.md` §6.7). For scale, wave 0 was 28 sheets, 334 fields and 41 workflows. It took about a day and a half to build and test, plus the acceptance pass. In wave 1 the logic weighs more than the number of sheets: Invoicing and Inventory are each larger than wave 0.

## 6. Decisions needed (Module Owner and Programme Lead)

1. **Order:** CRM first (recommended), or another module first because of a current deal?
2. **Invoicing scope:** SST only in wave 1, or MyInvois e-invoicing as well?
3. **Meetings:** HAP's own calendar, or a Meetings sheet like Odoo's `calendar.event`?
4. **Inventory:** rebuild natively in this app with the EMS lessons, or leave Inventory to EMS for now?
5. **Owners:** who in Nocoly owns each wave 1 module (`README.md` §6.5: Products and Sales belong to colleagues).
