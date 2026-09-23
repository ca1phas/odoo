# CLAUDE.md

This is an Odoo 19.0 fork. **Everything Claude works on lives in `nocoly/`** — building the Nocoly HAP app
**ERP Master** as a replica of Odoo. Nothing here asks you to change Odoo itself; `addons/` is read as the
reference for Odoo's own behaviour.

**The reference tenant casimir.odoo.com is gone** — its trial expired on 22 Sep 2026 and it answers only with a
"database blocked" page. Odoo's facts now come from `nocoly/reference/odoo-19.4/` (extracted from it while it
lived) and from the 19.0 source under `addons/`, which is behind the saas~19.4 tenant in places. Say which one a
fact came from. Never click Subscribe.

This file exists so an agent does not have to read 400 KB of reference material to start. Read the sections
below, then read **only** the specific functions the index points at.

## Never

- **Never write to the Sales app `3e596740-d096-42cd-b948-0b62a0220927`.** It is a separate brownfield app.
  Reading it to identify a control is fine; writing to it is not.
- **Never run `nocoly/build/products.py layout`.** Its places and permissions predate another administrator's
  hand changes and running it reverts them. `products.py perms` is the narrow step that is safe.
- **Never delete without the owner's approval.** A mistake is disabled, or renamed `ZZ obsolete – `, and
  reported.
- **Never make an unpinned full control save.** See *Saving controls* below.
- **Never claim UI verification you did not do.** Implementation agents have no browser.

## Always

- Run build scripts with the CLI's own interpreter: `~/.hap-venv/bin/python nocoly/build/<script>.py <step>`.
  Never plain `python`. `hap` lives at `~/.hap-venv/bin/hap`.
- **Every step reads live state first and is safe to re-run.** Re-running must save nothing.
- **Read back every write** and `sys.exit` loudly if it did not store. Several HAP writes return success and
  store nothing, or store a malformed value.
- `hap.backup(...)` anything you replace. Backups go to `nocoly/build/backups/` and are not committed.
- Record every id in `nocoly/build/ids.json`. Keys are namespaced `"<Worksheet>: <name>"`. Never rename one.
- Aliases are **Odoo field names**; control names are Odoo's English labels.
- **Descriptions are for the app's users, not for us** (owner's rule, 22 Sep 2026). A control's or button's
  `desc`/`hint` says only what it does, in plain words. No Odoo, no field or model names, no divergences, no
  build notes. Divergences and reasoning go in `nocoly/worksheets/NN-name.md` and `nocoly/DECISIONS.md`.
- Test records are named `TEST …`.

## Saving controls

The one thing that breaks this app. `SaveWorksheetControls` replaces the **whole** control set, and the owner
hand-edits these worksheets in the browser while builds run — three times in one day.

- To **add** controls: `C.append_controls` — the server mints real ids and nothing else is re-sent. Never
  `C.add_fields` for this; its unpinned full re-save is the clobber risk.
- To **change** an attribute: read with `C.controls_with_version`, change only what you own, save with
  `C.save_controls(ws, ctrls, version=version)`, then prove by signature diff that only the intended controls
  moved. **The pattern is `nocoly/build/products.py:297` `step_perms`** — copy it.
- `add-fields` parks a new control at **row 9999**; only a full save places one, so **placement is the
  owner's**. Record the intent in a `*_PLACE` constant and say so in the report.

## The index — read these, not whole files

| Need | Where |
|---|---|
| Helpers: `control` `save_controls` `controls_with_version` `add_fields` `append_controls` | `nocoly/build/common.py:85-205` |
| Rules: `cond` `any_of` `item` `upsert_rules` | `common.py:233-275` |
| Views: `sort_spec` `switch_filter` `upsert_views` `view_info` | `common.py:275-360` |
| Buttons: `publish` `button_workflow` `upsert_buttons` `structure` | `common.py:371-425` |
| Records: `records` `row_id` | `common.py:425-450` |
| **Status buttons, the reference build** | `nocoly/build/invoices.py:728-765` (`status_when`, `step_buttons`) |
| **Workflow internals**: `branch_paths` `save_path` `nodes_by_name` `save_search` `patch` `set_fields` | `invoices.py:906-1077` |
| **A multi-node workflow with branches and formulas** | `invoices.py:959` `step_numbering` |
| **A rollup workflow over a subtable** | `nocoly/build/invlines.py:715` `rollup_nodes`, `:849` `step_rollup` |
| **Mounting a subtable; computed controls** | `invlines.py:432` `step_mount`, `:525` `step_computed` |
| **Seeding records from the tenant** | `invlines.py:1089` `step_seed` |
| Narrow version-pinned control save | `nocoly/build/products.py:297` `step_perms` |
| Platform gotchas, one section per topic | `nocoly/BUILDING.md` — 1083 lines, read the section not the file |
| Why a decision was taken | `nocoly/DECISIONS.md` |
| Per-worksheet requirements and test results | `nocoly/worksheets/NN-name.md` |
| Odoo model extracts from the tenant | `nocoly/reference/odoo-19.4/<model>.md` |

## Control types (HAP)

`2` text · `6` number · `8` currency · `11` dropdown · `14` attachment · `15` date · `16` date-time ·
`22` divider · `26` member · `29` relation · `30` lookup · `31` formula · `33` auto-number · `34` subtable ·
`36` checkbox · `37` rollup (汇总) · `41` rich text · `42` signature · `49` search button · `52` section.
Full map: `hap_cli/core/worksheet.py` `_TYPES`.

**`fieldPermission` is three inverted flags** — hidden / read-only / hidden-on-create, where `0` turns the
restriction **on**. `111` unrestricted · `101` read-only · `011` hidden · `100` read-only and off the create
form. A hidden field is never a column; hidden-on-create is not the same thing.

**An API write works whatever the permission** — `011` hidden and `100` read-only both store through
`record update`, and a workflow update node writes them too. Permission governs the *form*, not the API. **Since hap-cli 0.9 (23 Sep 2026) that needs `--ignore-rules`**: without it `record create/update` checks the form's read-only and required fields and business rules and refuses. `nocoly/build/hap.py run()` adds it to every record write; a raw `hap worksheet record update` you type yourself must pass it.

**But no single read path is complete, and they differ.** Measured on Orders, 21 Sep 2026:

| Control | Permission | `record get` | `common.records` listing |
|---|---|---|---|
| Prepayment Percentage | `011` hidden | `100.00` | **empty** |
| Invoicing Closed | `100` read-only | **None** | `1` |
| Signed By | `100` read-only | **None** | the value |
| Status | `100` read-only | the value | the value |

Status is `100` and both paths return it, so this is not permission alone — the three that vanish were added
to the worksheet **after** those records existed. **Never conclude a field is empty from one read.** Cross-check
with the other path before reporting a gap; this has produced two wrong conclusions and one wrong entry in
these notes.

## Computation

- A **function default** (`advancedSetting.defaulttype "1"` + `defaultfunc`) is evaluated **client-side, in
  the form only**. A seeded or API-written record stores it **empty**. Anything not typed by a person must be
  a **Formula (type 31)**.
- A control that reads a **汇总** must likewise be a Formula — a roll-up is computed server-side and has no
  value while the form is open.
- A 汇总 needs `dataSource='$<relation control id>$'` and `sourceControlId='<child control id>'`;
  `enumDefault` 5 = sum, 6 = count. Its own `advancedSetting.filters` writes a single select's "is" as
  `filterType` **51**, where a business rule writes **2**.

## Rules and filters

`SHOW HIDE READONLY REQUIRE ERROR = 1 2 4 5 6` (rule item types) · `CONTAINS EQ NE EMPTY NOT_EMPTY = 1 2 6 7 8`
(filter operators) · `INTERACTION VALIDATION = 0 1`. A rule applies its action while its condition holds and
**the opposite when it fails** — so write `<action> · equals`, never `<opposite> · not equals`.
`controlIds: []` is normal app-wide; targets live in `ruleItems[].controls`. A filter entry with an empty
`controlId` is a **group wrapper** whose real condition sits in `groupFilters`.

## Reading records

Neither path is complete — see the table above. `common.records` drops hidden fields; `record get` dropped
controls added after the record existed. **Read both before concluding a field is empty.**

## Working with the owner

They build in the browser at the same time, so **app state moves under you**. Read it; do not trust a brief's
control count. Report what you found instead of adjusting to it silently.
