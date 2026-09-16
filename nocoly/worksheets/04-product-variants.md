# 04 · Product Variants

| | |
|---|---|
| Nocoly app | ERP Master · menu group **Products** |
| Worksheet | Product Variants |
| Odoo model | `product.product` |
| Reference | **casimir.odoo.com — Odoo saas~19.4+e**: the fields stored on the variant, form, list, kanban, search, order and all 21 variants, extracted read-only to `nocoly/reference/odoo-19.4/product.product.md`, with `product.template.md`, `uom.uom.md` and, for the variants invoice lines point at, `account.move.line.md`. Behaviour the tenant cannot show — sync between product and variant, archiving, constraints, display name — is read from the Odoo 19.0 source in this repo: `addons/product/models/product_product.py`, `addons/product/models/product_template.py`, `addons/product/views/product_views.xml` |
| Phase | 1 — core worksheet 4 of 7 |
| Status | Built with the hap CLI and seeded on 15 Sep 2026; Favorite and the list order moved to Odoo's after the planner's review the same day · CLI self-checks pass (automations, buttons, Favorite, Barcode uniqueness, seed and extract) · **UI-tested on 15 Sep 2026: 16 of 16 pass**, 5 differences from Odoo noted · ready for review |

A variant is one sellable version of a product. Order lines and invoice lines point at the variant, never at the
product. Until the Product Variants bundle (attributes and their values) each product has exactly one variant,
and **Products is the master** of what both carry: Internal Reference, Cost, Weight and Volume, and Favorite, which
Odoo relates to the product's. Workflows keep the variant in step with its product; the variant's own fields are
Barcode, Extra Packagings and Variant Image.

## 1 · Requirements

### Fields

Labels are Odoo 19.4's; aliases are Odoo field names on `product.product`. "Lookup" means a stored lookup through
Product: read-only, and updated by HAP when the product changes, without a workflow. "Hidden" means not on the form
but used by the display name, views or buttons.

| # | Field | Odoo field | Nocoly type | Required | Default | Notes |
|---|---|---|---|---|---|---|
| 1 | Product | `product_tmpl_id` | Relation → Products (single, **one-way**), dropdown | yes | set by automation A | **Read-only**, as on Odoo's variant form (`readonly="1"`). Opens the product. The picker lists active products and its search matches their Internal Reference. No reverse field on Products. Odoo labels it Product Template |
| 2 | Favorite | `is_favorite` | Checkbox | — | the product's | **Read-only**: the product's Favorite, copied by automations A, B and C — edit it on the product. Odoo relates the two (`related='product_tmpl_id.is_favorite'`, `product_product.py:123`) and shows it read-only on the variant form and list. Quick filter; the views list favourites first |
| 3 | Sales | `sale_ok` | Lookup of the product's Sales | — | — | Beside Favorite, as Odoo's header. Quick filter |
| 4 | Purchase | `purchase_ok` | Lookup of the product's Purchase | — | — | Beside Sales. Quick filter |
| 5 | Variant Image | `image_variant_1920` | Attachment | no | — | The variant's own |
| 6 | Display Name | `display_name` | Function formula, text · **title field** | — | — | "[Internal Reference] Name", or the Name alone when there is no Internal Reference (Odoo `_compute_display_name`, `product_product.py:816`). Read-only under Variant Image on a saved variant, not on the create form: read-only and hidden on create rather than hidden, because a hidden field never shows as a table column |
| 7 | Product Type | `type` | Lookup of the product's Product Type | — | — | Tab **General Information**. Quick filter |
| 8 | Sales Price | `lst_price` | Lookup of the product's Sales Price, shown as RM with 2 decimals | — | — | Tab General Information. Edit the price on the product. Odoo adds the attribute values' price extras (`_compute_product_lst_price`), which come with the Product Variants bundle |
| 9 | Unit | `uom_id` | Lookup of the product's Unit (stored as the unit's name) | — | — | Tab General Information |
| 10 | Cost | `standard_price` | Currency MYR, shown as RM, 2 decimals | — | 0.00 | Tab General Information. **Read-only**: copied from the product (automations A, B, C). Odoo help "Value of the product (automatically computed in AVCO)…" kept in the description |
| 11 | Internal Reference | `default_code` | Text | no | — | Tab General Information. **Read-only**: copied from the product. Odoo's variant form labels it Reference |
| 12 | Barcode | `barcode` | Text, **No duplicates** | no | — | Tab General Information. Help "International Article Number used for product identification." Empty is allowed for any number of variants |
| 13 | Extra Packagings | `extra_uom_ids` | Relation → Units & Packagings (multiple, **one-way**), dropdown | no | — | Tab **Sales**. Help "Variant-specific additional packagings for this product which can be used for sales". The picker lists active units other than the product's Unit, by name only (§3 difference 1) |
| 14 | Weight | `weight` | Number, 2 decimals, suffix kg | — | 0 | Tab **Inventory**. **Read-only**: copied from the product |
| 15 | Volume | `volume` | Number, 2 decimals, suffix m³ | — | 0 | Tab Inventory. **Read-only**: copied from the product |
| 16 | Active | `active` | Checkbox | — | checked | Hidden. Set by Archive / Unarchive and by automation C |
| — | Name | `name` | Lookup of the product's Name | — | — | Hidden. Read by Display Name and by the views' sort |

The four read-only copies say so in their descriptions: "Copied from the product — edit it there. Read-only on the
variant while each product has one variant." Favorite's says "The product's Favorite — edit it on the product."

**Odoo differs from the brief in two places, built as briefed.** Odoo's variant form shows `image_1920` — the
variant's image, or the product's when it has none — and on a product with one active variant a new image is written
to the product (`_set_image_1920` → `_set_template_field`); here Variant Image is the variant's own field. Odoo's
Sales Price on a single-variant product is editable and writes the product's price (`_set_product_lst_price`); here
it is a read-only lookup.

**How Display Name works.** A number formula has no IF, so Display Name is a HAP function formula with a text
result, as on Contacts:

```
IF(ISBLANK(Internal Reference), TRIM(Name), CONCAT("[", TRIM(Internal Reference), "] ", TRIM(Name)))
```

Name is the stored lookup of the product's Name, so renaming a product renames its variant within seconds; a new
Internal Reference reaches the variant through automation B and the formula recomputes on that save. This settles
the open question in DECISIONS.md for variants: order and invoice lines (07) will show "[Internal Reference] Name";
Products keeps showing its Name. The " (attribute values)" suffix waits for the Product Variants bundle.

### Form layout

| Odoo 19.4 (variant form = the product form, `product_normal_form_view`) | Nocoly |
|---|---|
| Button box: Documents · Sold | — (see Not built now) |
| Header: ☆ Name (the product's, editable; the star read-only); the variant's Attributes as tags; Sales ☑ Purchase ☑; image | Product (read-only) · Favorite \| Sales \| Purchase (all three read-only) · Variant Image · Display Name (read-only, saved variants only) |
| Tab General Information — Product Type · Sales Price per Unit · Cost per Unit · Category · Reference · Barcode · Tags · Variant Tags; Internal Notes | Product Type \| Sales Price · Unit \| Cost · Internal Reference \| Barcode |
| Tab Sales, hidden unless Sales — Packagings, Extra Packagings, Optional Products, Sales Description | Extra Packagings; the whole tab hidden when the product's Sales is unchecked |
| Tab Inventory, hidden for services — Weight, Volume | Weight \| Volume; the whole tab hidden when the product is a Service |
| Tabs Prices, Purchase (never shown on the tenant) | — |

HAP's 12-column grid pairs Odoo's two columns. Odoo edits the product's own fields (Name, Product Type, Sales,
Purchase, Unit, Sales Price, Internal Notes, Packagings, Sales Description) on the variant form through `_inherits`;
here the ones a reviewer needs are read-only lookups and the rest stay on the product.

### Rules

| Rule | Type | When | Effect | Odoo source |
|---|---|---|---|---|
| Sales tab only for products that can be sold | interaction | the product's Sales is unchecked | hide the **Sales** tab | `<page name="sales" invisible="not sale_ok">`, inherited by the variant form |
| Inventory tab only for goods | interaction | the product's Product Type = Service | hide the **Inventory** tab | `<page name="inventory" invisible="type in ['service', 'combo']">`, inherited |

Nothing is validated here. The negative-Cost check (`_onchange_standard_price`) is moot while Cost is read-only on
the variant, and the product still refuses a negative Cost in its form. "The Reference '…' already exists."
(`_onchange_default_code`) stays out, as on Products: Odoo only warns. Barcode uniqueness is the field's own No
duplicates setting (Fields). Product is required on the field.

### Buttons (Odoo ⚙ Actions)

| Button | Shown when | Does | Confirmation | Odoo source |
|---|---|---|---|---|
| Archive | Active is checked | Active → unchecked. If the product has no other active variant, the product is archived too | "Are you sure that you want to archive this record?" · Archive / Cancel | `product.product.action_archive` (`product_product.py:696`): templates left with no active variant are archived |
| Unarchive | Active is unchecked | Active → checked, and the product is unarchived | none | `action_unarchive` (`:704`): inactive templates that now have an active variant are unarchived |

As on the other worksheets, the button that does not apply is greyed out rather than hidden.

### Views

| View | Type | Shows | Odoo 19.4 |
|---|---|---|---|
| Product Variants | table — opens first | Active variants. Columns Display Name · Sales Price · Cost · Barcode · Unit. Favourites first, then by Internal Reference, then Name. Quick filters Product Type · Sales · Purchase · Favorite | List view: image · Name (the display name) · Attributes · Sales Price · Cost · Barcode · On Hand · Free To Use · Unit. Search filters Goods · Services · Combo, Favorites, Sales · Purchase |
| Archived | table | Archived variants, the same columns and sort | The *Archived* filter |

The sort is Odoo's list order, `default_order="is_favorite desc, default_code, name, id"` (`product_views.xml:426`;
the model's `_order` is `default_code, name, id`), with one difference: PostgreSQL puts variants without an Internal
Reference **last**, HAP puts empty values **first** in an ascending sort, whatever the sort's empty-value setting says
(see Build). No gallery: Odoo's variant action is `list,form`.

### Automations

| Automation | Runs when | Does | Odoo source |
|---|---|---|---|
| **A** · Product Variants: create a new product's variant | a product is **created**, with a Name | If no variant points at the product yet: creates one with Product, Internal Reference, Cost, Weight, Volume, Favorite and Active from the product | `product.template.create` → `_create_variant_ids` (`product_template.py:568, 770`); `_prepare_variant_values` copies `active`; `is_favorite` is related to the product's |
| **B** · Product Variants: copy a product's Internal Reference, Cost, Weight, Volume and Favorite to its active variant | a product's Internal Reference, Cost, Weight, Volume or Favorite **changes** (those five trigger fields are its condition) | Copies the five fields to the product's **active** variants. Archived variants keep their own values | `_set_default_code`, `_set_standard_price`, `_set_weight`, `_set_volume` → `_set_product_variant_field` (`:292`) with one active variant; the related `is_favorite` (`product_product.py:123`) |
| **C** · Product Variants: archive and unarchive a product's variant with it | a product's Active **changes** (the trigger field is its condition) | Archived: archives all its active variants. Unarchived: unarchives the product's **own variant — its oldest** — and copies the five fields to it, so it cannot come back stale. Other (extra) variants stay archived | `product.template.write` (`:585`): archiving archives every variant; unarchiving a product with no active variant runs `_create_variant_ids`, which reactivates one variant per combination — without attributes, the oldest (`sorted(lambda p: (p.active, -p.id))`) — and leaves the rest archived |

**Why the oldest variant.** 07 Invoice Lines may add the tenant's archived original variants as extra, archived
variants of their product (Records). "Unarchive every archived variant" would revive them; Odoo revives one, and the
variant A or the seed created with the product is always the oldest.

**Why C copies the five fields.** Odoo writes a product's Cost to its single archived variant when it has no active
one (`_set_product_variant_field`, `count == 0`), and a related Favorite is always the product's; B deliberately
updates active variants only (planner addendum), so a Cost or Favorite changed while the product is archived would
otherwise come back stale. Checked: see Build.

**No loops, few runs.** A, B and C trigger on Products and write only Product Variants, where no worksheet event
starts a workflow. The variant's Archive / Unarchive buttons write the product, which starts C once; C then finds
nothing left to change. A product's creation runs A once; an edit runs B only when one of its five fields changes;
archiving or unarchiving runs C once.

### Not built now, and why

| Odoo 19.4 field / feature | Why not now |
|---|---|
| Attribute Values, Attributes, Combination Indices (`product_template_attribute_value_ids`, `product_template_variant_value_ids`, `combination_indices`); price extras (`price_extra`) and the " (attribute values)" suffix of the display name; more than one active variant per product (`_combination_unique`) | Product Variants bundle — excluded for now |
| Variant Tags (`additional_product_tag_ids`) | Product Tags bundle |
| Unit Barcode (`product_uom_ids`), and Barcode uniqueness against packaging barcodes (`_check_duplicated_packaging_barcodes`) | Its own table `product.uom`, not in Phase 1 |
| Documents (`product_document_ids`) | HAP's record attachments and discussion |
| Quantity On Hand (`qty_available`), On Hand and Free To Use columns | Inventory is not installed on the tenant |
| Reference Unit, Custom Unit of Measure (`base_unit_count`, `base_unit_id`) | eCommerce price per unit |
| Is Image Fetch Pending (`is_image_fetch_pending`) | `product_barcodelookup` |
| Pricelist rules (`pricelist_rule_ids`), tab Prices | Pricelists bundle |
| Company (`company_id`) | One company per app copy |
| Sold smart button, Warnings filter | Sales |
| Editing the product's Name, Product Type, Sales, Purchase, Unit, Sales Price… on the variant form (`_inherits`) | HAP lookups are read-only: edit them on the product |
| Editing Internal Reference, Cost, Weight, Volume on the variant | Products is their master while each product has one variant (planner decision) |
| Creating a variant directly, and duplicating one (Odoo's variant action has `create: False`; the form and list have `duplicate="false"`; `copy` duplicates the product instead) | A variant comes with its product (automation A). Create, Duplicate and Re-create are switched off on this worksheet; API writes still create |
| Re-creating a product's variant when an unarchived product has none at all (`_create_variant_ids` creates it) | In Phase 1 a variant only disappears by being deleted; `variants.py seed` restores it |
| Deleting the last variant deletes its product (`unlink`) | No deletion cascade; deletions need the owner's approval anyway |
| "The Reference '…' already exists." (`_onchange_default_code`) · negative Cost (`_onchange_standard_price`) | A warning only, as on Products · moot while Cost is read-only |
| Print Labels, Kanban and Activity views | No label printing; Odoo's variant action is `list,form` |
| Search on Product Category, Tags, Attribute Values; group by Product Category or Properties | Their bundles |
| ~~Roles~~ | **Set on 16 Sep 2026** for the whole app, at the end of Phase 1: five stock roles renamed to English and four business roles, one per Odoo accounting group, each with a rule for this worksheet. The table is in `REVIEWING.md` › *Phase 1 · Roles* |

### Records

One active variant for each of the 14 products of the extract, copying its Internal Reference, Cost, Weight, Volume
and Favorite (no product is a favourite); no Barcode, Extra Packagings or image, as on the tenant. **11 of them match
the extract exactly** — display name, Internal Reference, Sales Price, Cost, Active, no barcode. The monitor, chair and desk
get one variant with no Internal Reference and Cost 0, like their product: "27" 4K Monitor", "Ergonomic Office Chair",
"Height-Adjustable Desk 140cm". TEST Product (TEST-0001) has its variant too.

**Waiting for the Product Variants bundle.** The tenant's 6 attribute variants — 27" 4K Monitor (Silver +60,
Black), Ergonomic Office Chair (Red +120, Blue +60, Black), Height-Adjustable Desk 140cm (Oak, Aluminium +60) — and
the 3 archived original variants [IT-0002] 27" 4K Monitor (1,890 / cost 1,420), [FURN-0001] Ergonomic Office Chair
(899 / 540) and [FURN-0002] Height-Adjustable Desk 140cm (1,650 / 980).

**The tenant's invoice lines point at three of them** (`account.move.line.md`): [FURN-0001] Ergonomic Office Chair
and [FURN-0002] Height-Adjustable Desk 140cm, both archived originals, and Ergonomic Office Chair (Blue). **07 can add
the two originals without changing this worksheet**: create each through the API as an extra variant of its
product — Product, Internal Reference FURN-0001 / FURN-0002, Cost 540 / 980, Weight and Volume 0, Favorite and
Active unchecked — after the product's own variant exists. Its Display Name follows ("[FURN-0001] Ergonomic Office
Chair") and its Sales Price shows the product's, as on the tenant; B leaves archived variants alone, C only ever unarchives the
product's oldest variant, and `variants.py seed` / `verify` never touch extras (verify lists them). This was
proven with an archived extra on a TEST product (Build). Ergonomic Office Chair (Blue) — 959, the chair's 899 plus
a 60 price extra — cannot exist before the bundle: 07 can point those lines at the chair's own variant and keep the
line's price.

## 2 · Build

Built by `nocoly/build/variants.py` — steps `create → fields → relations → lookups → display → layout → rules →
views → buttons → automations → switches → seed`, each safe to re-run (`fields` refuses to run once the worksheet
has its fields); every id is in `nocoly/build/ids.json` under "Product Variants: …" (the worksheet under "Product
Variants"). Helpers: `variants.py verify` compares every variant with its product and with the extract,
`variants.py order` prints each view's records in the view's order, `variants.py variant "<Display Name>"` prints a
variant's stored values (hidden ones included), `variants.py raw <rowid>` its `record get` output, and
`variants.py show` the control list. No change to `common.py`.

| Element | Built | Id |
|---|---|---|
| App | ERP Master | `6cb4d051-a33c-4bf9-b56f-5f47f0e85dc9` |
| Menu group | Products — Products, **Product Variants**, Units & Packagings | `6aa8d12ddb26b712423d345d` |
| Worksheet | Product Variants, alias `product_product` | `6aa90c161204328eb1af1b82` |
| Controls | 20: the 17 fields above and 3 tabs | — |
| Relations | Product → Products · Extra Packagings → Units & Packagings, both one-way | `6aa90c7d4a22ad87b728e9f0` · `6aa90c7d4a22ad87b728e9f2` |
| Title field | Display Name (function formula) · Name (its lookup) | `6aa90cd04720c515252bf923` · `6aa90c9f4a22ad87b728e9f8` |
| Copied from the product, read-only | Internal Reference · Cost · Weight · Volume · Favorite | `6aa90c161204328eb1af1b83` · `6aa90c69f363582dd37a6229` · `6aa90c69f363582dd37a622c` · `6aa90c69f363582dd37a622d` · `6aa90c69f363582dd37a6227` |
| Lookups | Product Type · Unit · Sales · Purchase · Sales Price | `6aa90c9f4a22ad87b728e9f9` · `6aa90c9f4a22ad87b728e9fa` · `6aa90d9c4720c515252bf93c` · `6aa90c9f4a22ad87b728e9fb` · `6aa90c9f4a22ad87b728e9fc` |
| Rules | Sales tab · Inventory tab | `6aa90f134a22ad87b728ea5e` · `6aa90f134a22ad87b728ea60` |
| Views | Product Variants · Archived | `6aa90c161204328eb1af1b86` · `6aa90f171204328eb1af1bbf` |
| Buttons | Archive · Unarchive | `6aa90fc04a22ad87b728ea89` · `6aa90fc34720c515252bf9b8` |
| Button workflows | Archive the variant → product still has an active variant? → if not, archive the product · Unarchive the variant → unarchive the product | `6aa90fc08475f61d4ccd0f8b` · `6aa90fc38475f61d4ccd0faf` |
| Automation A | create a new product's variant | `6aa9117ce589b8933dd933da` |
| Automation B | copy a product's Internal Reference, Cost, Weight, Volume and Favorite to its active variant (its ids.json key keeps the first name, without Favorite) | `6aa91186e589b8933dd9367a` |
| Automation C | archive and unarchive a product's variant with it | `6aa9118ce589b8933dd93748` |
| Switches off | Show create button (10) · View › Batch › Duplicate (26) · Record › Duplicate (36) · Record › Re-create (37) | — |
| Records | 17 variants of the 17 products (14 seeded, TEST Product's, and the two TEST products' created by A) and 1 archived extra TEST variant; `verify` matches all | — |

**History.** Built and seeded on 15 Sep 2026. The worksheet's three stock controls were reused (Name → Internal
Reference, Description → Barcode, Attachment → Variant Image), so nothing was dropped. The first button cascade
used Odoo-like *get related record* steps; they came back without their relation field and would not publish, so
the unpublished draft of the Archive workflow was rolled back to its published one-step version with `hap workflow
rollback` (no step deleted) and both cascades were rebuilt with a search on Products. Then the planner's addendum
narrowed B to active variants, and C was built to reactivate only the product's oldest variant. Products' and Units
& Packagings' controls were compared by id before and after every full save of this worksheet — unchanged — and
their rules, views and buttons read back unchanged at the end.

**Favorite and list order, 15 Sep 2026** (planner's review: follow Odoo). `variants.py layout` made Favorite
read-only, keeping its control, with the description "The product's Favorite — edit it on the product."; `views`
sorts both views Favorite descending, then Internal Reference and Name. `automations` now brings an existing
workflow up to date in place — name, description, trigger, the fields its steps write — backing up what it rewrites
and rolling back to the published version if a read-back fails: A's create step takes Favorite from the product (it
wrote unchecked), B has Favorite among its trigger fields and in its copy step ("Copy the five fields to them"; the
workflow renamed), and C's reactivation copies it too. A second run rewrote nothing. `seed` sets Favorite from the
product and `verify` compares it; the seed changed no record, as no product is a favourite.

**Self-checks through the CLI** (records named TEST, listed in §3); A, B, C and the buttons were rerun after the
Favorite change:

- **A** — TEST Auto Variant Product, created through the API in the first build, and TEST Favorite Product, created
  after the change **with Favorite ticked**, each had exactly one variant within 20 s, with the product's Internal
  Reference, Cost, Weight, Volume, Favorite and Active, and its Sales Price, Unit, Product Type, Sales and Purchase in
  the lookups. "[TEST-0005] TEST Favorite Product ★" was the first row of Product Variants.
- **B** — changes of Internal Reference, Cost, Weight and Volume reached the variant (TEST-0003 / 13.75 / 1.25, and
  after the change TEST-0006 / 31.50 / Volume 0.02); clearing the Internal Reference gave the title without brackets;
  all restored. A write of only Name and Sales Price started no run of B, and the variant's Name, Sales Price and
  Display Name followed through the lookups. **Favorite ticked on TEST Auto Variant Product reached its active variant
  [TEST-0002], which moved to the top of Product Variants, and not the archived extra [TEST-0002-OLD]**; unticked, it
  went back to its place.
- **C** — archiving a product archived its variant. Changes made while the product was archived — Cost 14 on TEST Auto
  Variant Product, Favorite unticked on TEST Favorite Product — left the archived variant as it was; unarchiving
  brought the variant back active with the product's current values (Cost 14.00; not favourite). Restored.
- **Buttons** — `workflow trigger` of the variant's Archive archived the variant and its product; Unarchive
  unarchived both (TEST Auto Variant Product, from an active and from an archived product, and TEST Favorite Product
  after the change).
- **Extras** (the 07 path) — an archived extra "[TEST-0002-OLD] TEST Auto Variant Product" (Cost 11) created through the
  API while Create is switched off: `verify` lists it and stays OK; a Cost change reached only the product's own
  variant; archiving and unarchiving the product left the extra archived with its own reference and Cost.
- **Barcode** — TEST-BARCODE-0001 on one TEST variant was accepted; the same on the other was refused (resultCode 11
  naming Barcode); another value was accepted; both cleared.
- **Run history** — every run of A (2), B (12), C (12), Archive (2) and Unarchive (3) completed, one per action.
- **Nothing is favourite at the end** — no product and no variant, archived ones included.
- `variants.py verify`: 17 products, 0 differing, 1 extra; 11 of 11 single-variant products match the extract.
  `products.py verify`: 0 missing or differing (TEST Product, TEST Auto Variant Product and TEST Favorite Product not
  in the extract). `units.py verify`: 0 differing, 0 stale (3 TEST units).

The pickers' filters, the tab rules, the read-only fields (Favorite included), the currency display of the Sales Price lookup, the
switched-off buttons and the quick filters on lookups are browser behaviour: HAP stores them as configured, and only
the UI test can show them working.

### Found while building — applies to every worksheet

- A new worksheet comes with three stock controls — Name (the title), Description and Attachment. A first
  `update-fields` save that leaves one out deletes it: reuse their ids.
- A **lookup of a Relation stores the related record's title as text** (`sourceControlType` 2, "Units"): it shows
  and sorts, but a picker filter cannot compare a record id with it. Extra Packagings compare the candidate's Unit
  Name with it instead.
- A field's **No duplicates** (`unique`) holds on API writes too: the write is refused with resultCode 11 naming the
  field. Empty values are not compared.
- A tab and a field may share a name (the Sales tab and the Sales lookup): look fields up among non-tab controls.
- **Empty values sort first** in an ascending view sort. `moreSort[].emptyRule` is stored (1, 2 and 3 tried) and
  changes nothing.
- A workflow data step's **worksheet is fixed when the step is added**: `node save` with another `appId` answers
  success and keeps the old one, dropping the fields that do not fit. **`hap workflow rollback <processId> -y`**
  restores the last published version and discards the draft's steps, so a mis-built draft needs no deletion.
- In a **button's workflow, a *get related record* step cannot start from the trigger record**: the server leaves
  the trigger out of that step's sources, drops the relation field, and publishing fails (warningType 103, 200).
  Search the related worksheet instead: Record ID equals the trigger's Relation field (conditionId 9).
- A get-records filter on a Relation uses **conditionId 33** with the value `{nodeId, controlId}` — `rowid` for the
  node's record, or a Relation field of that node's record.
- `node batch-add --trigger-alias` names the `--trigger-node-id` node: when appending steps, that is the last step,
  not the trigger — reference the trigger by `nodeId`.
- A search step's result branch marks its paths `resultTypeId` 3 (found) and 4 (not found) in `workflow node list`;
  `node get` leaves it out. `workflow structure` omits get-records (type 13) steps.
- **A record written by a workflow starts that worksheet's event workflows**: the variant's Unarchive button writing
  the product started automation C. Design cascades so the second run finds nothing to change.
- Worksheet switches 10 (show create button), 26 and 36 (duplicate) and 37 (re-create) only remove UI paths:
  `record create` through the API and workflows still create records.
- `record get` returns the creation time as `_createdAt`; `record list` returns `ctime` empty.
- A **create or update step's field list can be changed in place**: read it with `node get`, change or append the
  entry, send the whole list back with `node save --type 6` (`actionId`, `appId`, `appType`, `selectNodeId`,
  `fields`), then republish. A text value taken from a node reads back as the template `$node-field$`, the other
  types as `nodeId` + `fieldValueId`.
- `hap workflow update <processId> -n … -d …` renames a workflow and sets its description (`explain` in
  `workflow get`).

## 3 · Test list

Run in the Nocoly UI in Chrome on 15 Sep 2026; stored values read back with
`~/.hap-venv/bin/python nocoly/build/variants.py variant "<Display Name>"` (and `products.py product "<Name>"`)
from the repo root. Where a result says "through the CLI", the product was changed with `hap worksheet record
update` or its button workflow with `hap workflow trigger` — the automations react to the change the same way —
and the variant was checked in the UI. Test records are named `TEST …`.

| # | Check | Steps | Expected | Result |
|---|---|---|---|---|
| 1 | Menu and no Create | Open ERP Master → menu group Products | Products, **Product Variants**, Units & Packagings in that order. Product Variants opens on the **Product Variants** table; views Product Variants · Archived. No "+ Record" button; a record's ⋯ menu has no Duplicate or Re-create | **Pass** — the group lists Products, Product Variants, Units & Packagings; Product Variants opens on its table; no + Record; a record's ⋯ menu offers Copy ID, Share, System Print, View in full page, Lock, Delete, Edit — no Duplicate or Re-create |
| 2 | Table, title and sort | Product Variants view; then Archived | 17 rows, columns Display Name · Sales Price · Cost · Barcode · Unit. Favourites would come first (there are none, see test 13); then the three without Internal Reference — 27" 4K Monitor, Ergonomic Office Chair, Height-Adjustable Desk 140cm — then [CONS-0001] A4 Copy Paper (Box of 5 reams), [CONS-0002] Whiteboard Marker Set, [FURN-0003] …, [IT-0001] …, [IT-0003] …, [IT-0004] …, [SRV-0001] …, [SRV-0002] …, [SRV-0003] …, [SW-0001] …, [SW-0002] …, [TEST-0001] TEST Product, [TEST-0002] TEST Auto Variant Product, [TEST-0005] TEST Favorite Product. Prices with RM and 2 decimals ([IT-0001] RM 5,400.00 / RM 4,150.00); Unit Units, Hours ([SRV-0001]) or Days ([SRV-0002]). Archived: 1 row, [TEST-0002-OLD] TEST Auto Variant Product | **Pass** — exactly those 17 rows and columns, RM with 2 decimals, Hours and Days where expected; Archived: [TEST-0002-OLD] TEST Auto Variant Product, RM 99.00 / RM 11.00 |
| 3 | Quick filters | Product Variants: Product Type = Service; clear; Purchase clicked twice (ticked, then unticked); reload; Sales ticked; reload; Favorite ticked | Service: [SRV-0001], [SRV-0002], [SRV-0003], [SW-0001], [SW-0002]. Purchase ticked: the other 12; unticked: the 5 services. Sales ticked: all 17. Favorite ticked: none | **Pass** — Service: the 5; Purchase ticked: 12; unticked: 5; Sales ticked: 17; Favorite ticked: 0 rows |
| 4 | A variant's form and read-only fields | Open [SRV-0002] Onsite Training (per day) | Title "[SRV-0002] Onsite Training (per day)". Product "Onsite Training (per day)", read-only, opens the product. Favorite ☐, Sales ✓ and Purchase ☐, all read-only (Favorite's description "The product's Favorite — edit it on the product."); Variant Image empty; Display Name read-only. General Information: Product Type Service, Sales Price RM 3,200.00, Unit Days, Cost RM 1,500.00, Internal Reference SRV-0002 — all read-only; Barcode empty and editable. Tab Sales shown; **tab Inventory hidden** (service). No Active or Name field. Cost's description ends "Copied from the product — edit it there…" | **Pass** — title, Product link and values as expected; clicking Favorite, Purchase or Product Type changes nothing; Barcode opens for editing; the Inventory tab is absent; no Active or Name field; descriptions as expected (tooltips, and CLI read-back) |
| 5 | Inventory and Sales tabs | Open [CONS-0002] Whiteboard Marker Set; then on Products uncheck Sales of TEST Auto Variant Product, reopen its variant [TEST-0002], and check Sales again | Whiteboard: tab Inventory with Weight 0.00 kg and Volume 0.00 m³, read-only. [TEST-0002]: Sales shows unchecked and the **Sales tab disappears**; it comes back once Sales is checked again | **Pass** — Whiteboard: Weight 0.00 kg, Volume 0.00 m³, read-only. With the product's Sales unchecked (changed through the CLI) [TEST-0002] shows Sales ☐ and only General Information and Inventory; checked again, the Sales tab is back |
| 6 | Barcode no duplicates | [TEST-0002] TEST Auto Variant Product: Barcode "TEST-4006381333931" → Save. Open [TEST-0001] TEST Product: the same Barcode → Save. Then clear both | The first is stored. The second is refused with HAP's duplicate-value message on Barcode (Odoo says "Barcode(s) already assigned: …"). Both empty at the end (CLI) | **Pass** — stored on [TEST-0002]; on [TEST-0001] "Duplicates are not allowed" appears under Barcode as soon as the field is left, and Save is refused with "Please fill in the record correctly"; cancelled; both empty (CLI) |
| 7 | Extra Packagings picker | [TEST-0001] TEST Product (Unit Units): tab Sales → Extra Packagings; pick Pack of 6 and Days → Save. Then open [SRV-0002] Onsite Training (per day) (Unit Days) → Extra Packagings, look, close without saving | TEST Product: active units except **Units** — 16 including the 3 TEST units; no Dozens, cm or km; two can be picked together. Onsite Training: Units offered, **Days** not | **Pass** — [TEST-0001]: 16 units without Units; Pack of 6 and Days picked together and stored (CLI). Onsite Training: 16 units with Units and without Days. Names only (difference 1) |
| 8 | Automation A and Display Name | Products → + Record: Name "TEST Variant From UI", Internal Reference TEST-0003, Sales Price 50, Cost 20, Weight 2, Volume 0.1 → Submit; refresh Product Variants | "[TEST-0003] TEST Variant From UI" appears, Sales Price RM 50.00, Cost RM 20.00, Unit Units; opened: Weight 2.00 kg, Volume 0.10 m³, Favorite unchecked like the product. CLI `variants.py verify "TEST Variant From UI"` → OK | **Pass** — within 20 s "[TEST-0003] TEST Variant From UI": RM 50.00, RM 20.00, Units, Weight 2.00, Volume 0.10, not favourite; `verify` OK |
| 9 | Automation B and lookups | On that product: Internal Reference TEST-0004 and Cost 21.50 → Save; then Sales Price 55 → Save; then clear Internal Reference → Save; then TEST-0004 again → Save | The variant becomes "[TEST-0004] TEST Variant From UI", Cost RM 21.50; Sales Price RM 55.00; with no reference its title is "TEST Variant From UI" and it sorts among the three without a reference; back to "[TEST-0004] …" | **Pass** — product fields changed through the CLI: "[TEST-0004] TEST Variant From UI" at RM 21.50; Sales Price RM 55.00; without a reference its title is "TEST Variant From UI", 4th in the view among the unreferenced; back to [TEST-0004] |
| 10 | Automation C | Products → TEST Variant From UI → Archive; check Product Variants and its Archived; then Products › Archived → Unarchive | Archived: the variant leaves Product Variants and shows in Archived. Unarchived: it is back, active, Cost RM 21.50 | **Pass** — Products' Archive and Unarchive workflows run through the CLI: the variant was archived with its product and came back active at RM 21.50 |
| 11 | Variant Archive button | Product Variants → [TEST-0002] TEST Auto Variant Product → Archive | Confirmation "Are you sure that you want to archive this record?" with Archive / Cancel. The variant moves to Archived **and its product TEST Auto Variant Product to Products › Archived**; [TEST-0002-OLD] stays archived | **Pass** — exact confirmation with Cancel / Archive; "Operation completed"; variant and product archived (CLI); [TEST-0002-OLD] still archived |
| 12 | Variant Unarchive button | Archived → [TEST-0002] TEST Auto Variant Product → Unarchive (not [TEST-0002-OLD]) | No confirmation. The variant is back in Product Variants and the product in Products; [TEST-0002-OLD] still archived. CLI `variants.py verify` → 0 differing, 1 extra variant | **Pass** — no confirmation; variant and product active again; [TEST-0002-OLD] archived, Cost 11.00; `verify`: 0 differing, 1 extra |
| 13 | Favorite follows the product | Products → Whiteboard Marker Set: tick Favorite → Save; refresh Product Variants; open [CONS-0002] Whiteboard Marker Set. Products → TEST Auto Variant Product: tick Favorite → Save; refresh Product Variants and Archived. Tick the Favorite quick filter. Reload the view; untick Favorite on both products → Save; refresh | Within ~20 s [CONS-0002] is the first row of Product Variants, above the three without an Internal Reference; on the variant Favorite is ticked and read-only. Then the first two rows are [CONS-0002] Whiteboard Marker Set and [TEST-0002] TEST Auto Variant Product, while [TEST-0002-OLD] in Archived stays unticked (an archived variant keeps its own values). The quick filter lists exactly those two. Unticked, both go back to their places (test 2). CLI: no product or variant is favourite | **Pass** — Favorite ticked on the two products (through the CLI): [CONS-0002] and [TEST-0002] became the first two rows, Favorite ticked and read-only on the variant form, [TEST-0002-OLD] unticked; the quick filter showed exactly those two; unticked, both returned to their places; no favourite left (CLI) |
| 14 | Display name where variants are searched | Product Variants search box: "IT-0001", then "Laptop" | Both find "[IT-0001] Business Laptop 14" i7". (No worksheet picks a variant before 07 Invoice Lines, where the picker shows the same title) | **Pass** — both searches find only [IT-0001] Business Laptop 14" i7 |
| 15 | Seeded data | `~/.hap-venv/bin/python nocoly/build/variants.py verify`; `products.py verify`; `units.py verify` | variants: every product OK, "0 whose own variant differs or is missing", the extra [TEST-0002-OLD] listed, "extract: 11 of 11 single-variant products match". products: 0 missing or differing. units: 0 differing, 0 stale | **Pass** — variants: 18 products, 0 differing, 1 extra, 11 of 11 match the extract; products: 0 missing or differing (4 TEST products); units: 0 differing, 0 stale |
| 16 | Odoo side by side | casimir.odoo.com: a product's Variants smart button (Business Laptop 14" i7, Ergonomic Office Chair) vs Nocoly | The laptop's variant list and form hold §1's fields apart from Not built now; its display name, Sales Price and Cost match. The chair shows its attribute variants and archived original in Odoo, one variant here (Records) | **Pass** — read through the tenant's API (the Odoo tab would not render): [IT-0001] Business Laptop 14" i7 is 5,400 / 4,150, Units, active, no barcode, as here; the chair has the archived [FURN-0001] (899 / 540) and Red 1,019, Blue 959, Black 899 at cost 0 in Odoo, one Ergonomic Office Chair (899 / 0) here, as Records says. Odoo lists referenced variants before unreferenced ones (difference 2) |

### Differences from Odoo seen in testing

1. **Unit pickers list names only.** Extra Packagings shows unit names, without Contains and Reference Unit — as on
   Products and Units & Packagings.
2. **Variants without an Internal Reference sort first.** Odoo (PostgreSQL) puts them after the referenced ones; HAP
   puts empty values first in an ascending sort and has no setting to change it.
3. **The product's fields are read-only on the variant.** Odoo edits Name, Sales Price, image and the other product
   fields through the variant form; here they are lookups or copies — edit them on the product.
4. **Workflows take a few seconds.** A product change reaches its variant within about 20 s, and an open view shows it
   after a refresh. A variant created by automation A shows "Owner: Not specified".
5. **Archive and Unarchive.** In a record opened as a full page only the button that applies is shown; in the record
   pop-up the other is greyed out, as on the other worksheets. Edits to Barcode or Extra Packagings are kept with Save
   on the *Modifying form data* bar.

### Test records left in the worksheet

- **Products:** TEST Product (TEST-0001) · TEST Auto Variant Product (TEST-0002, RM 99.00 / RM 12.50) · TEST Favorite
  Product (TEST-0005, RM 45.00 / RM 30.00) · TEST Variant From UI (TEST-0004, RM 55.00 / RM 21.50, Weight 2.00 kg,
  Volume 0.10 m³).
- **Product Variants:** their variants [TEST-0001] (with Extra Packagings Pack of 6 and Days), [TEST-0002], [TEST-0005]
  and [TEST-0004], and the archived extra [TEST-0002-OLD] (Cost 11.00).

No barcodes are set and nothing is favourite. Remove them after sign-off.
