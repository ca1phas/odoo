# Decisions

What was decided, why, and by whom. The owner is Casimir; "planner" means Claude, acting as orchestrator, within
the owner's direction. Newest last.

## Direction

| Date | Decision | Why | By |
|---|---|---|---|
| 14 Sep 2026 | Rebuild Odoo's apps **from the ground up** rather than extend the existing Nocoly Sales app | The Sales app (`3e596740…`) mirrors one Odoo app with its own Contacts and Products; a foundation shared by every app has to come first | owner |
| 15 Sep 2026 | **One master app, ERP Master**, holds every Odoo app. A client gets a copy with the menu groups it does not need deleted | Delivery is duplicate-and-prune, so everything must coexist in one app; it also removes the need for cross-app Relations | owner |
| 15 Sep 2026 | **Optional feature bundles are excluded for now.** Phase 1 is the seven core worksheets — Contacts, Units & Packagings, Products, Product Variants, Journals, Invoices, Invoice Lines — built one at a time | Bundles (Taxes, Chart of Accounts, Categories, Pricelists, Geography…) can be appended later without touching what exists; core worksheets cannot | owner |
| 15 Sep 2026 | **Menu groups follow Odoo's apps**: Contacts · Products · Invoicing for Phase 1 | Mirrors how Odoo splits its menus, and lets a client copy drop an app by deleting one group | owner (asked for "the best logic, or how Odoo does it") |
| 15 Sep 2026 | **The reference is the live tenant casimir.odoo.com (Odoo saas~19.4)**, not the 19.0 checkout in this repo. Fields, labels, layout, views and records follow the tenant; behaviour it cannot show (constraints, computes, sync logic) is read from the 19.0 source | The tenant is what the business actually uses; 19.4 differs from 19.0 (Contacts lost its Person/Company switch, for example) | owner |
| 15 Sep 2026 | Names and labels in **English, as in Odoo** | A reviewer can compare Odoo and Nocoly side by side | owner |
| 15 Sep 2026 | Every worksheet gets a **hand-off** — `worksheets/NN-name.md` plus a published review page — checked by a colleague | Review happens independently of the build | owner |
| 15 Sep 2026 | **One implementation agent at a time** builds a worksheet (requirements + hap CLI build); Claude plans, reviews its work, runs the UI test, writes the hand-off and commits | Throughput with one point of review | owner |
| 15 Sep 2026 | **Deleting anything needs the owner's approval.** Mistakes are renamed "ZZ obsolete – " and listed; test records are named `TEST …` and removed after sign-off | Several HAP deletions cannot be undone | owner |

## Open — to settle before the worksheet that needs it

| Needed by | Question | Recommendation from the plan |
|---|---|---|
| 04 Product Variants, 07 Invoice Lines | Do lines point at Product Variants or Products? | **Variants.** Every order line, stock move and invoice line in Odoo points at the variant; pointing at the template is the one choice that costs a rebuild rather than an append |
| 06 Invoices | One Invoices worksheet split by Move Type, or separate Bills? | **One worksheet with a Move Type dropdown** — Customer Invoice · Vendor Bill · Credit Note · Vendor Refund — as Odoo's single `account.move`; separate worksheets mean two numbering schemes and two posting workflows |

## Worksheet 01 · Contacts

| Date | Decision | Why | By |
|---|---|---|---|
| 15 Sep 2026 | **Tax ID stays on Contacts**; SST, TTx and the Malaysian TIN wait for the Taxes bundle and e-invoicing | Tax ID (`vat`) is a base field of every contact. SST and TTx come from `l10n_my_ubl_pint` and the TIN from `l10n_my_edi`, both built on Invoicing | planner, confirmed with owner |
| 15 Sep 2026 | Upstream sync (a contact's edit rewriting its company) is left out | Avoids automation loops; edit the company instead | planner |
| 15 Sep 2026 | **Show "Company, Person" as the display name, like Odoo** | Customer pickers on Invoices must identify the company | owner |
| 15 Sep 2026 | Delete the three rules the 19.0 build left disabled | They referred to a deleted field and did nothing | owner |

## Worksheet 02 · Units & Packagings

| Date | Decision | Why | By |
|---|---|---|---|
| 15 Sep 2026 | Menu group **Products** holds Units & Packagings, then Products and Product Variants | Units belong with the catalogue they measure | planner |
| 15 Sep 2026 | UN/ECE Code waits for e-invoicing; packaging Barcodes wait for Products | `unece_code` comes from `account_edi_ubl_cii`; barcodes live on products | planner |
| 15 Sep 2026 | Absolute Quantity is kept correct down the whole reference chain, though hidden as in Odoo | Every later unit conversion uses it | planner |
| 15 Sep 2026 | Seed Odoo's 30 standard units | Odoo ships them as data; Products needs them | planner |
