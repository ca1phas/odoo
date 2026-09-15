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
| 15 Sep 2026 | **Worksheet 05 Journals is built by the colleague, in parallel.** Implementation agents skip it — after Products they do 04 Product Variants, then 06 Invoices and 07 Invoice Lines once Journals stands — and never touch the Journals worksheet | Two builders working at once; Invoices relates to Journals | owner |
| 15 Sep 2026 | **Deleting anything needs the owner's approval.** Mistakes are renamed "ZZ obsolete – " and listed; test records are named `TEST …` and removed after sign-off | Several HAP deletions cannot be undone | owner |

## Open — to settle before the worksheet that needs it

| Needed by | Question | Recommendation from the plan |
|---|---|---|
| 04 Product Variants, 07 Invoice Lines | Do lines point at Product Variants or Products? | **Variants.** Every order line, stock move and invoice line in Odoo points at the variant; pointing at the template is the one choice that costs a rebuild rather than an append |
| 04 Product Variants | Show products and variants as "[Internal Reference] Name (attributes)" in pickers, as Odoo does? | Likely yes — the same reasoning as Contacts' display name; settle it in the 04 brief |
| 06 Invoices | One Invoices worksheet split by Move Type, or separate Bills? | **One worksheet with a Move Type dropdown** — Customer Invoice · Vendor Bill · Credit Note · Vendor Refund — as Odoo's single `account.move`; separate worksheets mean two numbering schemes and two posting workflows |

## Worksheet 01 · Contacts

| Date | Decision | Why | By |
|---|---|---|---|
| 15 Sep 2026 | **Tax ID stays on Contacts**; SST, TTx and the Malaysian TIN wait for the Taxes bundle and e-invoicing | Tax ID (`vat`) is a base field of every contact. SST and TTx come from `l10n_my_ubl_pint` and the TIN from `l10n_my_edi`, both built on Invoicing | planner, confirmed with owner |
| 15 Sep 2026 | Upstream sync (a contact's edit rewriting its company) is left out | Avoids automation loops; edit the company instead | planner |
| 15 Sep 2026 | **Show "Company, Person" as the display name, like Odoo** | Customer pickers on Invoices must identify the company | owner |
| 15 Sep 2026 | Delete the three rules the 19.0 build left disabled | They referred to a deleted field and did nothing | owner |
| 15 Sep 2026 | Display Name is a hidden function formula over a stored lookup of the Company's name, and the title field; the views drop their Company column and sort by it | HAP's only text IF is in function formulas; a hidden title still reaches titles, tables, cards and pickers | implementation agent, accepted by planner |

## Worksheet 02 · Units & Packagings

| Date | Decision | Why | By |
|---|---|---|---|
| 15 Sep 2026 | Menu group **Products** holds Units & Packagings, then Products and Product Variants | Units belong with the catalogue they measure | planner |
| 15 Sep 2026 | UN/ECE Code waits for e-invoicing; packaging Barcodes wait for Products | `unece_code` comes from `account_edi_ubl_cii`; barcodes live on products | planner |
| 15 Sep 2026 | Absolute Quantity is kept correct down the whole reference chain, though hidden as in Odoo | Every later unit conversion uses it | planner |
| 15 Sep 2026 | Seed Odoo's 30 standard units | Odoo ships them as data; Products needs them | planner |
| 15 Sep 2026 | Add a **recursion check** (hidden Parent Path + "Recursion Detected." rule) and Odoo's "Reference unit of measure is missing." rule | A reference loop (km → m → km) would make HAP recompute Absolute Quantity endlessly; both mirror checks Odoo enforces (`_parent_store`, `_check_factor`) | implementation agent, accepted by planner |
| 15 Sep 2026 | Sequence is a formula that follows Contains; lists sort by Sequence, then Unit Name | HAP rows cannot be dragged; Odoo sets Sequence once at creation and orders by `sequence, relative_uom_id, id` — close enough to review | implementation agent, accepted by planner |

## Worksheet 03 · Products

| Date | Decision | Why | By |
|---|---|---|---|
| 15 Sep 2026 | Products sits in menu group Products, **before** Units & Packagings | Odoo's catalogue order: products first, units under configuration | planner |
| 15 Sep 2026 | **Scope is the `product` module's own fields** plus Sales Description; Sales, Invoicing, Project, Purchase and Inventory fields on products are appended when those apps or bundles land | The bridge-pack rule: an app appends its fields to Products, it does not arrive pre-built | planner |
| 15 Sep 2026 | Product Type offers **Goods and Service**; Combo waits for the Product Combos bundle | A Combo product is meaningless without Combo Choices | planner |
| 15 Sep 2026 | Views open on a **gallery**, then List and Archived; favourites first, then by name | Odoo's Products action opens in Kanban; its order is `is_favorite desc, name` | planner |
| 15 Sep 2026 | Seed the 14 products; the monitor's, chair's and desk's variants wait for Product Variants (04) and its bundle | Without the Product Variants bundle each product has exactly one variant | planner |
| 15 Sep 2026 | Packagings leave out the product's own Unit; both unit pickers show Contains and Reference Unit; a negative Cost is refused in the form only; Weight and Volume default to 0 | Odoo's field domain, Odoo's unit dropdown, Odoo's onchange (not a constraint), and the tenant's data | implementation agent, accepted by planner |

## Worksheet 05 · Journals

| Date | Decision | Why | By |
|---|---|---|---|
| 15 Sep 2026 | Journals is assigned to **Teh Li Wei** as the reviewing colleague and is handed off for parallel work while Products is being built; implementation agents must not touch the Journals worksheet | Two builders can work in parallel without crossing the Products, Units & Packagings or Journals boundaries; later Invoices will relate to Journals | owner |
| 15 Sep 2026 | The Journals handoff records the Phase 1 core fields only; Chart of Accounts, Currency, Payments, e-invoicing and other Journal relations are deferred | Creating fake Text fields would produce the wrong model and make later bundles harder to attach correctly | owner / Teh Li Wei |
| 15 Sep 2026 | This commit is planning and collaboration handoff only; it does not build HAP objects and must not change `build/ids.json` | The correct CLI profile is not currently authenticated, and live Odoo UI extraction plus a later CLI preflight are required before creation | Teh Li Wei |
| 15 Sep 2026 | After the Products handoff, build the approved Journals core slice through the explicit `fbmy-nocoly` CLI profile and record its HAP IDs; keep the status at CLI-built until Web validation passes | The correct Nocoly organization/app were confirmed, Journals had zero records, and the work does not overlap Units & Packagings or Products | owner / Teh Li Wei |
| 15 Sep 2026 | Do not seed Journals or add deferred account/currency/payment relations; record the unavailable Sequence Prefix maximum-length setting instead of inventing a CLI parameter | The live Odoo source/form check and dependent Foundation bundles are still pending | Teh Li Wei |
| 15 Sep 2026 | Use the owner's authenticated `ohyes.odoo.com` tenant as the live UI source for Journals; do not require or join `casimir.odoo.com` for this worksheet | The owner explicitly supplied the correct tenant and its user-visible list/form are authoritative for this hand-off | Teh Li Wei |
| 15 Sep 2026 | Preserve the existing Communication Standard option IDs and default binding, but update their visible labels to include Odoo's example references | The `ohyes.odoo.com` Sales journal visibly shows `Full Reference (INV/2024/00001)`, `European (RF83INV202400001)` and `Numbers only (202400001)` | Teh Li Wei |
