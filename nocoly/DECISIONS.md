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
| 15 Sep 2026 | **ohyes.odoo.com is Teh Li Wei's own site; casimir.odoo.com stays the reference** for every worksheet, Journals included | One reference for the whole app; `reference/odoo-19.4/account.journal.md` is the casimir extract | owner |
| 15 Sep 2026 | **Teh Li Wei builds Journals (05) and Invoices (06) first.** When he is done with each, we re-check it against casimir, close the gaps, run the UI test and send him a summary. Until then implementation agents leave both worksheets alone; 07 Invoice Lines follows Invoices | Two builders without collisions: the colleague edited Journals and created Invoices while a gap-closing agent was preparing changes, which it parked unapplied (branch `claude/journals-gaps`) | owner |
| 15 Sep 2026 | Merging Teh Li Wei's branch `codex/journals-phase1-handoff` into 19.0 waits until the gaps are closed and double-checked | Keeps 19.0 matching what has been reviewed | owner |

## Open — to settle before the worksheet that needs it

| Needed by | Question | Recommendation from the plan |
|---|---|---|
| 07 Invoice Lines | Do lines point at Product Variants or Products? | **Variants.** Every order line, stock move and invoice line in Odoo points at the variant; pointing at the template is the one choice that costs a rebuild rather than an append. 04 is built so lines can point at variants |
| 06 Invoices | One Invoices worksheet split by Move Type, or separate Bills? | **One worksheet with a Move Type dropdown** — Customer Invoice · Vendor Bill · Credit Note · Vendor Refund — as Odoo's single `account.move`; separate worksheets mean two numbering schemes and two posting workflows |

## Worksheet 01 · Contacts

| Date | Decision | Why | By |
|---|---|---|---|
| 15 Sep 2026 | **Tax ID stays on Contacts**; SST, TTx and the Malaysian TIN wait for the Taxes bundle and e-invoicing | Tax ID (`vat`) is a base field of every contact. SST and TTx come from `l10n_my_ubl_pint` and the TIN from `l10n_my_edi`, both built on Invoicing | planner, confirmed with owner |
| 15 Sep 2026 | Upstream sync (a contact's edit rewriting its company) is left out | Avoids automation loops; edit the company instead | planner |
| 15 Sep 2026 | **Show "Company, Person" as the display name, like Odoo** | Customer pickers on Invoices must identify the company | owner |
| 15 Sep 2026 | Delete the three rules the 19.0 build left disabled | They referred to a deleted field and did nothing | owner |
| 15 Sep 2026 | Display Name is a function formula over a stored lookup of the Company's name, and the title field; the views drop their Company column and sort by it | HAP's only text IF is in function formulas | implementation agent, accepted by planner |
| 15 Sep 2026 | Display Name is **read-only on a saved contact's form**, under Image, and not on the create form — rather than hidden | The retest found a hidden field dropped from every table, so Contacts and Archived lost their first column; an always-true rule hiding it on the form would be a workaround reviewers must learn | planner |

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

## Worksheet 04 · Product Variants

| Date | Decision | Why | By |
|---|---|---|---|
| 15 Sep 2026 | **One variant per product** until the Product Variants bundle, created with its product; **Products is the master** of Internal Reference, Cost, Weight, Volume and Favorite, copied to the variant by workflows and read-only there | Without attributes every Odoo product has exactly one variant, whose fields are the product's (single-variant inverses, `is_favorite` related) | planner |
| 15 Sep 2026 | Variants show as **"[Internal Reference] Name"** — the title field, read-only, not hidden; products keep showing their Name | Odoo `_compute_display_name`; invoice lines will pick variants; hidden fields drop out of tables. Settles the open question for variants; " (attribute values)" waits for the bundle | planner |
| 15 Sep 2026 | The product → variant copy reaches **active variants only**; unarchiving a product revives only its **oldest** variant and copies the fields onto it | The tenant's invoice lines point at archived original variants (FURN-0001, FURN-0002) that 07 may add as archived extras: they must keep their own reference and cost. Odoo `_create_variant_ids` revives one variant | planner, with the implementation agent |
| 15 Sep 2026 | The variant's Archive / Unarchive also archive / unarchive the product when it has no other active variant | Odoo `action_archive` / `action_unarchive` on `product.product` | implementation agent, accepted by planner |
| 15 Sep 2026 | No Create, Duplicate or Re-create on Product Variants; Product is read-only | Odoo's variant action has `create: False`, the views `duplicate="false"`, and the form shows the product read-only | implementation agent, accepted by planner |
| 15 Sep 2026 | Views sort Favorite, then Internal Reference, then Name; variants without a reference come first | Odoo's list `default_order`; HAP cannot put empty values last | planner |
| 15 Sep 2026 | Sales Price and the product's other fields are lookups, and Variant Image is the variant's own | HAP lookups are read-only; Odoo's editing through `_inherits` and its image fallback are left out | implementation agent, accepted by planner |
| 15 Sep 2026 | Extra Packagings leave out the product's Unit by comparing unit names; the Sales and Inventory tab rules are Products' | A lookup of a relation stores the title, so no record id is available to compare; the variant form inherits the product form's tabs | implementation agent, accepted by planner |

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
| 16 Sep 2026 | **We complete Journals** on top of Teh Li Wei's build, keeping his control ids, aliases and option keys; he keeps Invoices | The owner asked for it once his last Journals edit was 14 hours old; keeping the ids leaves his views and any later record valid | owner |
| 16 Sep 2026 | The gaps closed against casimir: prefix back to **5 characters and unique**, **Sequence** restored (default 10) with the views sorted Sequence → Type → Sequence Prefix, the two **dedicated sequence** checkboxes added, Payment Communications shown and required on Sales only, Archive / Unarchive buttons, a Type quick filter, Odoo's own help text, and the **7 tenant journals seeded** | Odoo `size=5`, `code_company_uniq`, `_order`, the form's `invisible` rules and the tenant's data | planner |
| 16 Sep 2026 | **Sequence is a visible, editable Number** | A HAP table has no drag handle, so the number is the only way to reorder journals | implementation agent, accepted by planner |
| 16 Sep 2026 | **Communication Type and Standard are required by a rule, not on the field** | A field a rule hides can never be filled: field-level required would make every non-Sales journal unsavable | implementation agent, accepted by planner |
| 16 Sep 2026 | **One flat form, no notebook tabs**; four interaction rules on Type decide what shows | Odoo's two pages would hold one and two fields until the deferred settings land; add the tabs when they have content | implementation agent, accepted by planner |
| 16 Sep 2026 | The 5-character prefix limit stays a **form-only check** | HAP does not enforce a text maximum on API writes and no filter operator measures length; No duplicates, which entry numbering depends on, is enforced everywhere | implementation agent, accepted by planner |
| 16 Sep 2026 | "You cannot archive a journal containing draft journal entries" waits for **06 Invoices**, then joins the Archive workflow | The check counts draft entries, which do not exist yet | implementation agent, accepted by planner |
| 16 Sep 2026 | **Journals gets Odoo's two notebook tabs — Journal Entries and Advanced Settings — and a remark block in each** naming what Odoo shows there and which bundle or table brings it | The owner asked for the tabs even while the deferred settings leave them thin; the remark blocks tell a reviewer what is coming rather than leaving a bare tab | owner |
| 16 Sep 2026 | Static notes are HAP's **remark block (control type 10010)**, not a divider's description | A divider renders its description nowhere at all, so the first attempt was invisible in the UI test; the remark block holds HTML and renders it | planner |
