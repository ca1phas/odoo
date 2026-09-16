# 02 · Units & Packagings

| | |
|---|---|
| Nocoly app | ERP Master · menu group **Products** |
| Worksheet | Units & Packagings |
| Odoo model | `uom.uom` |
| Reference | **casimir.odoo.com — Odoo saas~19.4+e**: fields, form, list, search, constraints and all 30 records, extracted read-only to `nocoly/reference/odoo-19.4/uom.uom.md`. Behaviour the tenant cannot show — computes, Python constraints, the ORM's recursion check — is read from the Odoo 19.0 source in this repo: `addons/uom/models/uom_uom.py`, `odoo/orm/models.py` |
| Phase | 1 — core worksheet 2 of 7 |
| Status | Built with the hap CLI and seeded on 15 Sep 2026 · **UI-tested: 18 of 19 pass, 1 partly** (the Reference Unit picker shows names only) · ready for review |

Every unit of measure and packaging, in one worksheet. A unit is a multiple (**Contains**) of its **Reference
Unit**, and so on up to a unit that has none. **Absolute Quantity** multiplies that chain out — km = 1000 × m's
1000 = 1,000,000 — and is what every later unit conversion (Products, Invoice Lines) reads.

## 1 · Requirements

### Fields

Labels are Odoo's. "Hidden" means not on the form but used by views, rules or later worksheets.

| # | Field | Odoo field | Nocoly type | Required | Default | Notes |
|---|---|---|---|---|---|---|
| 1 | Unit Name | `name` | Text · **title field** | yes | — | |
| 2 | Contains | `relative_factor` | Number, 7 decimals, trailing zeros hidden | yes | 1 | Odoo help as the field description: "How much bigger or smaller this unit is compared to the reference UoM for this unit". Cannot be 0 (rules) |
| 3 | Reference Unit | `relative_uom_id` | Relation → Units & Packagings (single) | no | — | Placeholder "Reference Unit". The picker lists active units only (Odoo's `active_test`) and shows each one's Contains and Reference Unit, as Odoo's dropdown shows "Days  8.0 Hours" |
| 4 | Absolute Quantity | `factor` | Formula, 9 decimals | — | — | Hidden, read-only. Contains × the Reference Unit's Absolute Quantity; Contains alone when there is no Reference Unit (`_compute_factor`). A change anywhere up the chain reaches every unit below it |
| 5 | Sequence | `sequence` | Formula, integer | — | — | Hidden. min(int(Contains × 100), 1000) (`_compute_sequence`). Both views sort on it |
| 6 | Active | `active` | Checkbox | — | checked | Hidden. Set by Archive / Unarchive |
| 7 | Related UoMs | `related_uom_ids` | Relation → Units & Packagings (multiple), the reverse of Reference Unit | — | — | Hidden. HAP creates it with the Reference Unit relation |
| 8 | Parent Path | `parent_path` | Text combination | — | — | Hidden, technical. The record ids from the top of the chain down to this unit, each followed by "/" — Odoo's `parent_path` with HAP record ids. The recursion rule reads it |
| — | Reference Absolute Quantity | *(helper)* `relative_uom_id.factor` | Lookup through Reference Unit, stored | — | — | Hidden. Feeds the Absolute Quantity formula |
| — | Reference Parent Path | *(helper)* `relative_uom_id.parent_path` | Lookup through Reference Unit, stored | — | — | Hidden. Feeds Parent Path and the recursion rule |

**How Absolute Quantity stays right.** It is a number formula on a stored lookup of the Reference Unit's own
Absolute Quantity. When a unit is saved, HAP updates the lookup on every unit that points at it, which recomputes
their formula, and so on down. Tested live: changing cm's Contains reached m, km, in, ft, yd and mi (four levels)
within 5 seconds, and back. A number formula has no IF, so the formula reads
`Contains × (x + 1 − MIN(1, ROUNDUP(ABS(x), 0)))`, x being the lookup (empty counts as 0): x when there is a
Reference Unit, 1 when there is none. No workflow is involved.

### Form layout

| Odoo 19.4 | Nocoly |
|---|---|
| Button box: Packaging Barcodes | — (see Not built now) |
| Unit Name | Unit Name, full width |
| UN/ECE Code | — (see Not built now) |
| Quantity: [Contains] [Reference Unit] | Contains \| Reference Unit, side by side |

HAP labels each field, so Odoo's single "Quantity" label becomes the labels Contains and Reference Unit.

### Rules

All three are validation rules checked in the form **and** on API writes.

| Rule | When | Effect | Odoo source |
|---|---|---|---|
| Contains cannot be 0 | Contains = 0 | "The conversion ratio for a unit of measure cannot be 0!" on Contains, as you type | SQL constraint `_factor_gt_zero` (`uom_uom.py:46`; in the 19.4 extract) |
| A unit without a Reference Unit contains 1 | no Reference Unit and Contains ≠ 1 | "Reference unit of measure is missing." on Reference Unit, on submit | `@api.constrains` `_check_factor` (`uom_uom.py:97`) |
| Reference Unit cannot be the unit or one below it | the chosen Reference Unit's Parent Path contains this unit's id | "Recursion Detected." on Reference Unit, as you type | ORM `_parent_store_update` (`odoo/orm/models.py:5033`); `uom.uom` has `_parent_store = True` |

Without the third rule a loop (km → m → km) would make HAP recompute Absolute Quantity endlessly. Tested on the
API: a unit pointing at itself or at a unit below it is refused; re-pointing a unit to one above it is allowed.

### Buttons (Odoo ⚙ Actions)

| Button | Shown when | Does | Confirmation |
|---|---|---|---|
| Archive | Active is checked | Active → unchecked | "Are you sure that you want to archive this record?" · Archive / Cancel |
| Unarchive | Active is unchecked | Active → checked | none |

### Views

| View | Type | Shows | Odoo 19.4 |
|---|---|---|---|
| Units & Packagings | table | Active units. Columns Unit Name · Contains · Reference Unit, sorted by Sequence, then Unit Name | List view (the action is `list,form`; no Kanban). Odoo hides Contains when it is 1 and there is no Reference Unit, and orders by `sequence, relative_uom_id, id` with a drag handle |
| Archived | table | Archived units, same columns and sort | The *Archived* search filter |

Search is on Unit Name, HAP's search box.

### Automations

None. Absolute Quantity and Parent Path follow the chain through stored lookups (see Fields).

### Not built now, and why

| Odoo 19.4 field / feature | Why not now |
|---|---|
| UN/ECE Code (`unece_code`) and its uniqueness check | `account_edi_ubl_cii` — UBL/CII e-invoicing, which comes with Invoicing; the same treatment Contacts gave SST and TTx |
| Packaging Barcodes button, Barcodes (`product_uom_ids`), "Barcodes can be configured on each variant" | Module `product` (`product.uom`) — comes with Products and Product Variants |
| Related UoMs on the form | Odoo does not show it either; it exists here, hidden |
| Drag-and-drop ordering | Sequence is a formula, so rows cannot be dragged. Odoo also sets Sequence only when a unit is created; here it follows Contains |
| Contains left blank in the list for a unit with Contains 1 and no Reference Unit | A HAP table cannot hide a single cell |
| Standard units cannot be deleted ("The following units of measure are used by the system and cannot be deleted … You can archive them instead.") | `_unlink_except_master_data` — no HAP rule can block a delete; restrict deleting in Roles |
| Deleting a unit deletes the units that point at it | `relative_uom_id ondelete='cascade'` — HAP clears their Reference Unit instead; archive rather than delete (Roles) |
| Warning when Contains of a standard unit changes | `_onchange_critical_fields` — a warning only; HAP has no on-change warning |
| Unit Name, Contains, Reference Unit read-only when the form is opened from a product | Form context `product_id` — comes with Products |
| Ratio locked once products in this unit have stock moves or quants | `stock` module (`UomUom.write`) — Inventory is not in Phase 1 |
| Conversion methods (`_compute_quantity`, `_compute_price`, `_check_qty`, `_has_common_reference`) | Built where they are used (Products, Invoice Lines), reading Absolute Quantity |
| Translated unit names (`translate=True`) | One language |
| ~~Roles~~ | **Set on 16 Sep 2026** for the whole app, at the end of Phase 1: five stock roles renamed to English and four business roles, one per Odoo accounting group, each with a rule for this worksheet. The table is in `REVIEWING.md` › *Phase 1 · Roles* |

## 2 · Build

Built by `nocoly/build/units.py` — steps `create → fields → computed → layout → rules → views → buttons → seed`,
each safe to re-run (`fields` refuses to run on a worksheet that already has its fields); helpers shared with later
worksheets are in `nocoly/build/common.py`; every id is in `nocoly/build/ids.json` under "Units & Packagings: …".
`units.py verify` compares the live units with the 19.4 extract; `units.py unit <name>` prints a unit's hidden
values; `units.py refresh` re-saves units whose stored lookups fell behind.

| Element | Built | Id |
|---|---|---|
| App | ERP Master | `6cb4d051-a33c-4bf9-b56f-5f47f0e85dc9` |
| Menu group | Products, after Contacts | `6aa8d12ddb26b712423d345d` |
| Worksheet | Units & Packagings, alias `uom_uom` | `6aa8d14d4a73a3142152d3f6` |
| Controls | 10: the 8 fields above (aliases are Odoo field names) and 2 hidden lookups | — |
| Rules | the 3 above | `6aa8d6c21204328eb1af0db9` · `6aa8d6c34720c515252be287` · `6aa8d6c3f363582dd37a582b` |
| Views | Units & Packagings · Archived | `6aa8d14d4a73a3142152d3fa` · `6aa8d8554720c515252be2d3` |
| Buttons | Archive · Unarchive | `6aa8d8814720c515252be2f8` · `6aa8d8894a73a3142152d499` |
| Button workflows | one step each, setting Active | `6aa8d881e589b8933dd73bfb` · `6aa8d889d91d10186df6ec14` |
| Records | the 30 standard units, Active as in Odoo (14 active, 16 archived); `verify` matches Unit Name, Contains, Reference Unit, Active, Sequence and Absolute Quantity for all 30 | — |

**History.** Absolute Quantity was built as the planner's first choice, Lookup + Formula; HAP accepted the
self-referencing chain and it propagates, so the workflow fallback was not needed. Nothing was left behind:
there is nothing to delete for this worksheet.

### Found while building — applies to every worksheet

- A **single relation to the same worksheet** comes back two-way: HAP adds a reverse control named "Child" at
  row 9999, width 0, no alias.
- **Formula functions need a `c` prefix** in the stored expression — `cMIN`, `cINT`, `cROUNDUP`, `cABS`. Written as
  `MIN(…)` the formula saves and computes empty. Plain arithmetic needs no prefix. There is no IF.
- `worksheet add-fields` stores a control under its **client-side 32-hex id**; a formula or text combination saved
  that way computes nothing until an `update-fields` save re-mints the id. References to not-yet-minted ids inside
  one `update-fields` save (formula expressions, a lookup's source) are rewritten to the minted ids.
- A text combination can use the record id: `$rowid$`. A rule condition can compare with it
  (`dynamicSource: [{cid: "rowid"}]`) and test it (`controlId: "rowid"`).
- **Stored lookups chain**: a record save updates the lookups pointing at it and the formulas on them, level
  after level. But the recompute HAP runs **after a formula or lookup definition changes** handles each record
  on its own and can leave rows behind; re-saving a record's unchanged relation brings its lookups up to date
  and passes the change on (`units.py refresh`).
- The server checks a **validation rule only when one of its condition fields is in the write**. A rule that
  tests only a lookup or formula never fires on the API; add the field being edited as a condition. Lookups
  are then read from the new value.
- A refused write comes back as `resultCode 32` naming `<ruleId>:<rowid>`.
- `worksheet record list` returns **hidden fields as empty strings**; `record get` returns their values.
- `workflow trigger <processId> -s <rowid>` runs a button's workflow on a record — a CLI check of Archive/Unarchive.
- `worksheet create` builds the icon URL on `fp1.mingdaoyun.cn`; pass
  `--icon-url https://www.nocoly.com/file/mdpub/customIcon/<icon>.svg` on Nocoly.

## 3 · Test list

Run in the Nocoly UI in Chrome on 15 Sep 2026; stored values read back with
`~/.hap-venv/bin/python nocoly/build/units.py unit "<Unit Name>"` from the repo root. Test records are named `TEST …`.

| # | Check | Steps | Expected | Result |
|---|---|---|---|---|
| 1 | Menu | Open ERP Master | Menu group **Products** after Contacts, holding Units & Packagings; views Units & Packagings and Archived, no Kanban | **Pass** |
| 2 | Active view | Units & Packagings | 14 units in this order: Minutes, g, Hours, KWH, m², ml, mm, Units, Pack of 6, Days, kg, L, m, t. Columns Unit Name, Contains, Reference Unit (e.g. Minutes · 0.0166667 · Hours) | **Pass** — exact order and values; Contains shows thousands separators (1,000) |
| 3 | Archived view | Archived | 16 units: in³, fl oz (US), ft², in, yd, gal (US), cm, Dozens, ft, ft³, km, lb, m³, mi, oz, qt (US) | **Pass** |
| 4 | Empty form | + Record, look, then Submit | Unit Name, then Contains and Reference Unit side by side; nothing else. Contains is 1; Reference Unit shows "Reference Unit"; Contains' description shows Odoo's help. Submit: Unit Name required | **Pass** |
| 5 | Contains 0 | Unit Name "TEST Zero", Contains 0 | "The conversion ratio for a unit of measure cannot be 0!" under Contains; Submit refused | **Pass** — shown as you type; Submit refused, listing that message and "Reference unit of measure is missing." (no Reference Unit, Contains ≠ 1) |
| 6 | Missing reference | Unit Name "TEST Box of 10", Contains 10, no Reference Unit → Submit | "Reference unit of measure is missing."; not saved | **Pass** |
| 7 | Reference Unit picker | Open Reference Unit | Only the 14 active units (no cm, no Dozens); each shows its Contains and Reference Unit, e.g. Days: 8 · Hours | **Partly** — exactly the 14 active units, but the dropdown shows unit names only (difference 1). Typing in its search also matches the Reference Unit column: "Units" finds Pack of 6 |
| 8 | Save with a reference | Reference Unit = Units → Submit | Saved, no "Recursion Detected."; last row of Units & Packagings (Sequence 1000, after t). CLI: absolute quantity=10, sequence=1000, path=Units/TEST Box of 10 | **Pass** — all three values as expected |
| 9 | Chain | New "TEST Crate": Contains 5, Reference Unit TEST Box of 10 | CLI: absolute quantity=50, path=Units/TEST Box of 10/TEST Crate | **Pass** — also sequence=500 |
| 10 | Change up the chain | Edit TEST Box of 10: Contains 12 | Within ~10 s, CLI: TEST Box of 10 = 12 and TEST Crate = 60 | **Pass** |
| 11 | Change the reference | Edit TEST Box of 10: Reference Unit = Pack of 6 | CLI: TEST Box of 10 = 72, TEST Crate = 360; TEST Crate's path Units/Pack of 6/TEST Box of 10/TEST Crate | **Pass** |
| 12 | Recursion — itself | Edit TEST Box of 10: Reference Unit = TEST Box of 10 | "Recursion Detected." under Reference Unit; not saved | **Pass** — HAP leaves a record out of its own picker, so the UI cannot even offer it; the rule's refusal of the same write on the API was proven at build time |
| 13 | Recursion — below | Edit TEST Box of 10: Reference Unit = TEST Crate | "Recursion Detected."; not saved | **Pass** — shown as you pick; Save refused; the change was cancelled |
| 14 | Sequence | New "TEST Half": Contains 0.5, Reference Unit Units | Second row of Units & Packagings, after Minutes. CLI: sequence=50, absolute quantity=0.5 | **Pass** — after a refresh (difference 2); TEST Crate sorts between Units and Pack of 6 |
| 15 | Archive | Open TEST Crate → Archive | Confirmation as above with Archive / Cancel; TEST Crate leaves Units & Packagings, appears in Archived; the record offers Unarchive, not Archive | **Pass** — exact text; in Archived the record's Archive button is greyed and Unarchive active (difference 3) |
| 16 | Archived out of the picker | New record → Reference Unit | TEST Crate not listed | **Pass** — searching "TEST" offers TEST Half and TEST Box of 10 only |
| 17 | Unarchive | Archived → TEST Crate → Unarchive | No confirmation; back in Units & Packagings | **Pass** |
| 18 | Standard data | `~/.hap-venv/bin/python nocoly/build/units.py verify` | Every standard unit OK; "0 differing from the extract; 0 with stale lookups"; the TEST units listed as not in the extract | **Pass** — 30 OK, 0 differing, 0 stale; TEST Box of 10, TEST Crate, TEST Half listed |
| 19 | Odoo side by side | casimir.odoo.com Units & Packagings vs Nocoly | Same fields as §1 apart from the "Not built now" list; the same 30 units, Active flags, Contains and Reference Units | **Pass** — through the extract and test 18: the tenant does not show a Units & Packagings menu (its units setting is off), so there is no screen to compare |

### Differences from Odoo seen in testing

1. **Reference Unit picker.** Odoo's dropdown hints each unit's ratio ("Days  8.0 Hours"); HAP's dropdown lists names
   only. The ratio shows once a unit is picked, in the Contains and Reference Unit fields.
2. **New records sit at the top of the open view** until it is refreshed, whatever their Sequence — HAP behaviour.
3. **Archive / Unarchive.** The button that does not apply is greyed out rather than hidden, as on Contacts.

### Test records left in the worksheet

TEST Box of 10 (Contains 12, Reference Unit Pack of 6) · TEST Crate (Contains 5, Reference Unit TEST Box of 10) ·
TEST Half (Contains 0.5, Reference Unit Units). Left for the reviewer to inspect; remove them after sign-off.
