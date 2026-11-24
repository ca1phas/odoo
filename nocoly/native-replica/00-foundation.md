# 00 Foundation and register: module plan, v2 (native first)

| | |
|---|---|
| Status | **Draft v2**, 23 Nov 2026, for Li Wei's review. Replaces v1 (`00-foundation-v1.md`, approved earlier the same day), after Li Wei asked to rebuild the master app with native fields and to read the full Nocoly docs first |
| What changed | Every field and behaviour was re-chosen from the native catalogue (`native-catalogue/`): live tests of all field types, the 16 behaviours mapped to native nodes, and all 359 pages of help.nocoly.com. Code is a last resort with a written reason |
| Target | A **new** master app (name: decision 1), Nocoly SaaS organisation Nocoly (Professional edition), profile `<profile>`. The current "Odoo Replica (AI)" becomes the sandbox for live tests (decision 2) |
| Odoo reference | Odoo 20.0 source (`catalogue/odoo-20.0`) and the local Odoo 20 Community with demo data (`external/odoo20-local`); field lists come from it |
| Owner | **By role** (`HANDOVER.md` §2): the Module Owner reviews and signs off; the Builder builds (here an AI assistant under the Module Owner) |
| Size | **M**: about 21 business sheets plus 4 helper sheets, 3 shared PBPs, about 25 workflows |

## 1. Scope

**Odoo modules covered (foundation):**
- `base`: contacts, companies, currencies and rates, countries, country groups, industries, bank accounts;
- `contacts`: the app and its menus;
- `uom`: units;
- `product`: products, variants, attributes, pricelists, combos, categories, tags;
- `mail`: activities, activity types and plans.

**Programme items in this wave:**
- conventions;
- the register (built: `register/`), pointed at the new app;
- the live tests the wave depends on (§9, step 0).

**Main flows, as Odoo shows them:**
1. Companies with people and addresses.
2. Tags, salesperson, archive.
3. Reference lists.
4. Units in chains.
5. Products with attributes and variants.
6. Pricelists with rules.
7. Activities: schedule, done with feedback, next, plans.

**Out of scope**, the same as v1:
- users and groups (HAP members and roles);
- multi-company;
- other modules' fields;
- IAP and geolocation services;
- properties;
- vendor prices (Purchase);
- working times;
- barcode nomenclatures;
- product taxes (Invoicing).

**New in v2:**
- `res.country.state` is **not built**. The native Region field has every country's states with ISO codes (§3).
- `res.partner.category` and `product.tag` are **not sheets**. They become native coloured multi-select options.

## 2. Dependencies, field budget and edition

- **Dependencies:** none. Other modules add fields to these sheets later (bridge-pack rule). The measured counts per model are in v1 §2 and `catalogue/odoo-20.0/foundation-fields-by-owner.md`.
- **Field budget:** HAP allows **200 fields per worksheet**. Odoo's `res.partner` has 225 business fields across all modules and `product.product` has 222. So each shared sheet gets a budget per module, and the register reports the count:

  | Sheet | Wave 0 | Kept free for later modules |
  |---|---:|---:|
  | Contacts | about 35 | 165 |
  | Products | about 35 | 165 |
  | Variants | about 20 | 180 |

  Display-only data (counters, lookups) goes to Query Records fields or pages, not stored fields.
- **Edition:** built on Professional. Wave 0 uses Professional-only features:
  - PBP, for the three shared functions;
  - Loop, for #8, #14 and #16;
  - condition groups, in queries.

  A customer on Standard would need the fallbacks in §4. Every later plan has the same edition line.

## 3. Data model: sheets and native fields

**Conventions** (from v1, refined):
- Sheet alias = Odoo model with `_`. Field alias = Odoo field.
- HAP-only objects use `x_<module>__<name>`.
- Native replacements of Odoo fields are listed in `00-foundation-build/field-decisions.csv`, so the register's coverage shows them as "native" instead of "missing".
- All Currency fields: **MYR** (this organisation defaults to HKD).
- All Phone fields: Mobile type with **MY** as the default country.
- All Region fields: **Global** range.
- Dates in imports: `YYYY-MM-DD`.
- Numbers that may exceed 16 digits (barcodes, bank accounts, IC numbers) go in Text fields.

**Menu groups:**
- **Contacts** (› Configuration);
- **Products** (› Configuration);
- **Activities** (› Configuration);
- **Settings**;
- **System Tables**, hidden from members.

| Sheet (alias) | Group | Fields and their native types | Notes |
|---|---|---|---|
| **Contacts** (`res_partner`) | Contacts | **Display Name** `complete_name` (Text, **title**, read-only, written by #1). Name `name` (Text). **Company Type** `company_type` (Single select, radio: Person / Company; replaces `is_company`). Address Type `type` (Single select: Contact / Invoice / Delivery / Other). **Parent** `parent_id` (self-relationship; the pair creates **Contacts & Addresses** `child_ids`, tab table). Job Position `function` (Text). Email `email` (**Email**). Phone `phone` (**Phone**). Website `website` (Text, link). **Address** `x_base__region` (**Region**, Global, state level; replaces `country_id` + `state_id` for input). Country `country_id` (relationship to Countries, read-only, set from the region by #3). Street, Street 2, Zip, City (Text). Location `x_base__location` (**Positioning**, optional, for the map view). Tax ID `vat` (Text). Other identifiers `additional_identifiers` (multi-line Text; Malaysian BRN/TIN/SST come with l10n_my later). Reference `ref` (Text). Language `lang` (Single select). Salesperson `user_id` (**Members**). **Tags** `category_id` (**Multi-select**, option set "Contact Tags", colours, users may add). Industry `industry_id` (relationship). Notes `comment` (**Rich Text**). Image `image_1920` (**Attachment**, image). Barcode `barcode` (Text). Employee `employee` (Check). Active `active` (Check, default on). Commercial Entity `commercial_partner_id` (self-relationship, by #2). Company Name `commercial_company_name` (Text, by #2). Company `company_id` (hidden; decision 1 of v1). **Bank Accounts** `bank_ids` (reverse of Bank Accounts) | About 35 fields. Not built, with reasons: `tz` (HAP members have time zones), `color` (kanban colour comes from options), `user_ids` / `partner_share` (HAP members and portal), `properties` (no equivalent), the image sizes |
| **Bank Accounts** (`res_partner_bank`) | Contacts › Configuration | Account Number `account_number` (Text, title). Sanitized `sanitized_account_number` (Function formula, SUBSTITUTE of spaces). Holder `holder_name` (Text). Partner `partner_id` (two-way relationship → Contacts "Bank Accounts"). Bank `bank_name`, BIC `bank_bic` (Text). Bank address: Region + Text. Send Money `allow_out_payment` (Check). Note `note` (Text). Active, Sequence. **Unique index** on (Sanitized, Partner), Odoo's constraint | Clearing fields are country-specific: not built |
| **Companies** (`res_company`) | Settings | Name (Text, title). Contact `partner_id` (relationship; the address lives on the contact, as in Odoo). Currency `currency_id` (relationship, MYR). Logo `logo_web` (Attachment). Address, Email, Phone, Website, Tax ID: display-only **Foreign Fields** from the contact (as built; see BUILD-LOG). Report Header, Report Footer, Company Details (Rich Text). Colours `primary_color` / `secondary_color` (Text hex). Active, Sequence | One record (single company). Branches (`parent_id` / `child_ids`) come with multi-company |
| **Currencies** (`res_currency`) | Settings | As built in the sandbox: name, full name, symbol, active, current and inverse rate, rate date, decimals, rounding, symbol position, unit and subunit labels, numeric code. **Unique index** on `name` | Kept: native Currency fields have no per-record currency and no rates. Needed for multi-currency documents and conversion (decision 4) |
| **Currency Rates** (`res_currency_rate`) | Settings | Date `name` (Date), Currency `currency_id` (two-way → "Rates" tab), Technical Rate `rate` (Number, 6 decimals). **Unique index** on (currency, date) | Daily automatic rates can come later through a scheduled workflow and a rate API (native) |
| **Countries** (`res_country`) | Contacts › Configuration | As built in the sandbox, plus **Region** `x_base__region` (Global, country level) linking each to the native list. **Unique index** on `code` | Holds Odoo's country data: currency, VAT label, address format, zip and state rules, groups |
| **Country Groups** (`res_country_group`) | Contacts › Configuration | Name, Code, Countries `country_ids` (two-way multiple ↔ Countries "Country Groups"), Pricelists `pricelist_ids` (reverse of Pricelists) | |
| **Industries** (`res_partner_industry`) | Contacts › Configuration | Name, Full Name, Active | |
| **Units** (`uom_uom`) | Products › Configuration | Unit Name `name` (Text, title). Contains `relative_factor` (Number, 6 decimals). Reference Unit `relative_uom_id` (self-relationship; the pair creates **Related UoMs** `related_uom_ids`). Absolute Quantity `factor` (Number, 6 decimals, read-only, by #7). Path `parent_path` (Text, by #7). Active, Sequence | Org (hierarchy) view of the chains |
| **Product Categories** (`product_category`) | Products › Configuration | Name (Text). Parent `parent_id` (self-relationship → Child Categories `child_id`). Complete Name `complete_name` (Text, **title**, by #10). Path `parent_path` (Text). Product Count `product_count` (**Rollup**, count) | Org view, plus a Cascading picker on Products if the live test passes |
| **Attributes** (`product_attribute`) | Products › Configuration | Name. Display Type `display_type` (Single select: Radio / Pills / Select / Color / Multi-checkbox). Variant Creation `create_variant` (Single select: Instantly / Dynamically / Never). Values `value_ids` (**subform on the existing sheet** Attribute Values). Sequence | |
| **Attribute Values** (`product_attribute_value`) | System Tables | Value `name`. Attribute `attribute_id`. Colour `html_color` (Text hex; decision 6). Free Text `is_custom` (Check). Default Extra Price `default_extra_price` (**Currency**). Sequence | |
| **Products** (`product_template`) | Products | Name (Text, title). **Product Type** `type` (Single select, radio: Goods / Service / Combo). Track Inventory `is_storable` (Check, shown for Goods). Category `categ_id` (relationship, or Cascading if it passes). **Tags** `product_tag_ids` (Multi-select, option set "Product Tags", colours). **Sales Price** `list_price` (**Currency**). **Cost** `standard_price` (**Currency**; the variants hold it, the template shows it for one variant). Internal Reference `default_code` (Text). **Barcode** `barcode` (Text with scan input, plus a **Barcode** display field). Sales / Purchase `sale_ok` / `purchase_ok` (Check). Unit `uom_id` (relationship), Packagings `uom_ids` (multiple). Description `description` (Rich Text), Sales / Purchase Description (multi-line Text). Weight / Volume (Number with kg / m³ suffix). Image (Attachment). **Favourite** `is_favorite` (**Level**, 1 star). Sequence, Active. **Attributes & Variants** `attribute_line_ids` (subform on the existing sheet Attribute Lines). **Variants** `product_variant_ids` (reverse). Combo Choices `combo_ids` (multiple, shown for Combo). Documents `product_document_ids` (Attachment). Company (hidden) | About 35 fields. `service_tracking` and `base_unit_*` belong to Sales / eCommerce: later |
| **Attribute Lines** (`product_template_attribute_line`) | System Tables | Product `product_tmpl_id`. Attribute `attribute_id`. Values `value_ids` (multiple, filtered to the attribute) | The subform's own sheet |
| **Product Attribute Values** (`product_template_attribute_value`) | System Tables | Product, Attribute Value, Attribute Line, Extra Price `price_extra` (**Currency**), Active, Key (Text) | One per product and value |
| **Variants** (`product_product`) | Products | Product `product_tmpl_id` (two-way → "Variants"). Values `product_template_attribute_value_ids` (multiple). Combination Key `combination_indices` (Text, for find-or-create). Internal Reference, Barcode (Text + Barcode display). Cost `standard_price` (**Currency**). **Sales Price** `lst_price` (**Currency**, written by #11). Weight, Volume. Variant Image (Attachment). Favourite (Level). Extra Tags `additional_product_tag_ids` (Multi-select, same option set). Active | |
| **Pricelists** (`product_pricelist`) | Products | Name. Currency `currency_id` (relationship, default MYR). Sequence, Active. **Rules** `item_ids` (subform on the existing sheet Pricelist Rules). Country Groups `country_group_ids` (two-way ↔ Country Groups). Company (hidden) | |
| **Pricelist Rules** (`product_pricelist_item`) | System Tables | Pricelist. **Apply On** `applied_on` (Single select: All Products / Category / Product / Variant). Category, Product, Variant (relationships, shown by Apply On). Min. Quantity (Number). Start / End `date_start` / `date_end` (Date-time). **Price Type** `compute_price` (Single select: Fixed / Discount / Formula). Fixed Price (**Currency**). Discount `price_discount` (Number, %). Based On `base` (Single select: Sales Price / Cost / Other Pricelist). Other Pricelist `base_pricelist_id`. Rounding, Surcharge, Min. / Max. Margin (**Currency**). Unit `uom_id`. **Rule Summary** (Function formula, for example "10% discount on Office") | Multi-currency pricelists use Number fields: decision 4 |
| **Combo Choices** (`product_combo`) | Products › Configuration | Name. Items `combo_item_ids` (subform on the existing sheet **Combo Items** `product_combo_item`: Product (variant), Extra Price (**Currency**)). Sequence, Company (hidden) | |
| **Activities** (`mail_activity`) | Activities | Activity Type `activity_type_id`. **Summary** `summary` (Text, title). Note `note` (Rich Text). **Due Date** `date_deadline` (Date, required). **Assigned to** `user_id` (**Members**, default current user). **State** `x_mail__state` (Single select with colours: Overdue red / Today orange / Planned green / Done grey; set by #14). Done On `date_done` (Date). Feedback `feedback` (multi-line Text). Active (Check; done = archived). Automated (Check). Document Model `res_model`, Document Name `res_name`, Document ID `res_id` (Text). **Contact** `x_contacts__partner_id` (relationship; each later module adds its own typed link). Attachments `attachment_ids` (Attachment) | `role_id`, `user_tz` and `phone` are not built (HAP roles and members) |
| **Activity Types** (`mail_activity_type`) | Activities › Configuration | Name (title). Default Summary. Icon (Text). Action `category` (Single select). Decoration `decoration_type` (Single select). Schedule `delay_count` (Number) + `delay_unit` (Single select: days / weeks / months) + Delay Type `delay_from` (Single select). Suggest Next `suggested_next_type_id` (self-relationship). Default User `default_user_id` (Members). Model `res_model` (Single select of sheets). Default Note (Rich Text). Active, Sequence | 6 seed types from `mail` |
| **Activity Plans** (`mail_activity_plan`) | Activities › Configuration | Name. Model `res_model` (Single select). Active. **Steps** `template_ids` (subform on the existing sheet **Plan Steps** `mail_activity_plan_template`: Activity Type, Summary, Assignment `responsible_type` (Single select), Assigned to (Members), Interval + Unit + Trigger (before / after the plan date), Note, Sequence) | |

**Helper sheets** in System Tables:
- Plan Launches `x_mail__plan_launch` (#16);
- Variant Queue `x_product__variant_queue` and Combinations `x_product__combination` (#8);
- Price Checks `x_product__price_check` (the price checker, §5);
- Resync Requests `x_base__resync` (#2/#3, see §4).

**Option sets:** Contact Tags, Product Tags.

**Unique indexes**, which are native and strict: currency name, (rate currency, date), country code, (bank sanitized number, holder).
- Barcode uniqueness across products and variants spans two sheets and allows empty values, so it stays a workflow check (#9).

## 4. Business logic: native designs

Details, risks and the live questions are in `native-catalogue/workflow-nodes.md` §5.

**Run rules that shape them** (catalogue README):
- update-triggered workflows always run in parallel;
- a second edit during a run is dropped;
- a flow's own writes never re-trigger it;
- there are no transactions.

So sync flows can safely run again, and the sheets that need them get a **Resync** button.

| # | Odoo behaviour | Native design | Code? |
|---|---|---|---|
| 1 | Display name "Company, Person" | Flow on create, and on name or parent change: read the parent, then write the Display Name (Text title, searchable in pickers). A company rename rewrites its people (batch update by query) | No |
| 2 | VAT, identifiers and industry kept on the company and copied to its people | Company change: one batch update of its people. New person, or a new parent: copy from the company. "Resync" button. Fields locked on people by a business rule | No |
| 3 | A Contact-type person uses the company's address; Country set from the region | Same pattern as #2, for Contact-type people only. The Country relation is found from the region's country code | No |
| 4 | No circular parents | The parent picker shows companies only. A stored path plus an INCLUDE() check, then revert with a message | No |
| 5 | A person takes the company's language | Create flow copies `lang` | No |
| 6 | Unique codes | **Unique index** (native, strict) | No |
| 7 | Unit chains and conversion | Stored factor and path. Factor = Contains × the parent's factor. Descendants are rewritten by path prefix. **PBP "Convert quantity"** | No |
| 8 | Variants from attribute lines (always / dynamic / never) | The queue sheet's create-only flow runs serially per product: find-or-create the values, build combinations through nested sub-processes on helper rows, find-or-create each variant by key, archive the rest. Never-lines are left out; dynamic creates none | No, if live tests Q4/Q5/Q17 pass |
| 9 | Barcode unique across products and variants | Two duplicate queries, then a branch with a message | No |
| 10 | Category full name and no cycles | The EMS location-path pattern, with CONCAT and SUBSTITUTE instead of code | No |
| 11 | Variant price = product price + extras | Rollup of the extras, then calibrate, compute and write `lst_price` | No |
| 12 | Pricelist rule choice and price | **PBP "Price for product"**: one sorted query in Odoo's rule order, branch by price type, compute and round. Chained pricelists go through a loop with a trace | No; fallback in the catalogue |
| 13 | Rate on a date and conversion | **PBP "Convert amount"** (rate on or before the date, else the earliest, else 1). The current-rate flow runs on rate changes and daily | No |
| 14 | Activity state from the due date | Computed on save, plus a daily 00:05 batch (Malaysian time per the docs; live test Q1) | No |
| 15 | Done with feedback, next activity | Buttons with dialogs: **Mark Done** (feedback; archive) and **Done & Schedule Next** (feedback, compute the next date from the type's delay, create the activity, open it with Interface Push) | No |
| 16 | Launch an activity plan | A **Launch Plan** button creates a Plan Launches row. The flow loops over the steps, computes each date, picks the assignee and creates each activity | No |

**Pilot: native to-do for activities.** A fill-in node with a time limit gives a real to-do: a deadline, an overdue mark, reminders and a feedback form. It closes only through Submit from the to-do, so it is piloted on one activity type ("To-Do") next to the sheet design, not instead of it.

## 5. User interface (native)

| Screen | Native choice |
|---|---|
| Contacts | Kanban with image cover and tags. Table. Map, when Location is filled. Form with a "Contacts & Addresses" tab. Rules show company fields only for companies |
| Hierarchies | Org view on Contacts (company › people), Units and Product Categories |
| Products / Variants | Kanban with image. Table. Form with an "Attributes & Variants" subform and a "Variants" tab. **Scan barcode** to find a product |
| Pricelists | Form with a rule subform and Rule Summary |
| **Price checker** (better than Odoo) | A **Check Price** button on Pricelists opens a dialog (product, quantity, date). It creates a Price Checks row; the flow calls the PBP; Interface Push shows the price and the rule used |
| Activities | **My Activities** (table, current user, grouped by State with colours). **Calendar** by Due Date. **Overdue** view. Buttons Mark Done, Done & Schedule Next, Launch Plan (on Contacts) |
| Currencies | Table, plus a rate-history chart |

**Not used in wave 0, with reasons:**
- Compute pages: the native views cover My Activities. The Compute checks from v1 move to the first module whose screen native can't do.
- Custom fields: only the colour picker (decision 6).

## 6. Roles

| Role | Rights |
|---|---|
| Administrator | HAP built-in |
| **Master Data Manager** | Create and edit everything in this wave |
| **Employee** | Read master data. Create and edit their own activities (record scope Owned on Activities) |
| Read Only | Default role, kept |

- Later modules add one role per app and level. HAP merges roles by union, so they combine cleanly.
- Live test: Employee sees only their own activities, checked with Role Debug.

## 7. Documents and notifications

- **Activity due:** the daily flow notifies the assignee, or the to-do pilot reminds them.
- No print templates in this wave.

## 8. Data

| Data | Rows | Source |
|---|---:|---|
| Countries | 251 | Local Odoo; Region set for 249 |
| Country groups | 11 | Local Odoo |
| Currencies | 170 | Local Odoo |
| Rates | 163 | Local Odoo; Odoo demo rates against USD, kept as test data |
| Industries | 21 | Local Odoo |
| Units | 30 | Local Odoo |
| Product categories | 7 | Rows owned by `product` |
| Activity types | 6 | Rows owned by `mail` |

- States are not loaded: the native region data replaces them.
- Demo subset (decision 5 of v1): about 7 companies with people, about 30 products with variants, 4 pricelists, 2 activity plans and 8 combos. Odoo's prices are loaded as MYR amounts.

## 9. Work order and acceptance

| Step | What | Effort (days) |
|---|---|---|
| 0 | **Live tests in the sandbox app** that this wave depends on: time zone (Q1); unique index; Mandatory Validation on Write; PBP inputs and outputs; loops and nested sub-processes (Q3–Q5); subform on an existing sheet with defaults; Rollup lag and calibrate; custom-action dialogs and Interface Push; Cascading picker; Region state level by CLI | 1.5 |
| 1 | Create the new app; groups, option sets, roles; point the register at it | 0.5 |
| 2 | Sheets in dependency order: Settings → Contacts → Units → Products → Activities. CLI builds with the raw keys from `fields.md`, each sheet checked in the UI | 3 |
| 3 | Load data (§8) and check it in the UI | 0.5 |
| 4 | The 3 PBPs and the workflows #1–#16 | 3–4 |
| 5 | Views, rules, custom actions, charts | 1.5 |
| 6 | To-do pilot | 0.5 |
| 7 | Acceptance tests and the review page | 1.5 |
| | **Total** | **about 12–13** |

**Acceptance tests:** v1's 19 tests, with these changes:
- Test 4 becomes: a duplicate country code is refused by the unique index.
- New test: an address picked in Region shows Malaysia / Selangor, and Country is set to MY.
- New test: a new tag typed on a contact appears in the option set with a colour.
- Test 12 is checked through the price checker.
- Test 18 covers the to-do pilot instead of the Compute checks.

The register scan after the build must show every object with an owner, and the coverage file must have no OPEN foundation field.

## 10. Register

Unchanged from v1 §10. The tools are built in `register/`.

Two additions:
- `field-decisions.csv` marks the native replacements, for example `res.partner,state_id,native:x_base__region`.
- The register reports **fields per sheet against the 200 limit**.

App copy and upgrade only work between apps from the same source, and an upgrade brings back anything the target lacks. So the register's "prune prediction" becomes part of the release process: each sellable edition gets its own pruned package for each release.

## 11. Risks

| Risk | Mitigation |
|---|---|
| Docs differ from runtime | Step 0 runs the tests first; the live test wins |
| Parallel update flows | Flows safe to repeat, plus Resync buttons, queue sheets for #8 |
| 200-field limit on shared sheets | Field budget per module; displays in Query Records or pages |
| Professional-only features | Edition line in every plan; fallbacks noted |
| Calculation node rounds to 2 decimals | Set the precision on unit and price calculations |
| Import formats | `YYYY-MM-DD` dates; long numbers as Text |

## 12. Decisions needed

| # | Question | Proposal |
|---|---|---|
| 1 | Name of the new master app | **OdooReplica**. Data Integration may break on names with spaces or brackets, and "Odoo Replica (AI)" has both |
| 2 | The current "Odoo Replica (AI)" | Rename it **"Odoo Replica Sandbox"** and keep it for live tests. Tests write real data, so they stay out of the master. It already holds the probe sheet and the reference sheets. Delete it at the end of the programme, with your OK |
| 3 | Company currency for all Currency fields | **MYR**. Odoo's demo prices are loaded as MYR numbers |
| 4 | Multi-currency | Keep the Currencies and Rates sheets. Wave 0 amounts are MYR only; documents in other currencies (Number + currency relation) are designed in Sales / Invoicing |
| 5 | Activities | The native sheet, views and buttons, plus the fill-in to-do pilot on one type. No Compute page in wave 0 |
| 6 | Attribute value colour | Text hex now. A colour-picker custom field (code) only if you approve it: native has no colour field |
| 7 | Contacts title | A Text "Display Name" written by the workflow (searchable in pickers), rather than a Concat (not searchable) |
| 8 | Sharing with Casimir | `github.com/ca1phas/odoo` is **public**. Push the programme files there without customer names or internal IDs, or ask him for a private repo |
| 9 | Sign-off | Module Owner, after the review page |
