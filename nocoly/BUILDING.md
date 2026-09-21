# Building a worksheet

How ERP Master is built, for whoever builds or changes a worksheet — a person or an implementation agent. Why
things are this way is in `DECISIONS.md`; how a worksheet is reviewed is in `REVIEWING.md`.

## Setup

```bash
export HAP_TOKEN=pat_…            # Nocoly personal access token
./nocoly/tools/bootstrap.sh       # installs hap-cli into ~/.hap-venv and logs in with profile "nocoly"
hap auth whoami
```

- Build scripts import the CLI's own builders, so run them with the CLI's interpreter:
  `~/.hap-venv/bin/python nocoly/build/<worksheet>.py <step>`.
- Pass the app id explicitly. The `nocoly` profile's default app is an unrelated training app.
- hap-cli upgrades itself when it runs. Everything here was verified on **0.8.31**; if a flag vanishes, read
  `hap <command> --help` again rather than guessing.

## The loop, per worksheet

1. **Reference.** Extract the Odoo model from casimir.odoo.com into `reference/odoo-19.4/<model>.md` with
   `tools/odoo_extract.js` (read-only; see the comment at its top). Read the 19.0 source for behaviour the tenant
   cannot show.
2. **Requirements.** Write section 1 of `worksheets/NN-name.md`, in the format of `01-contacts.md`: fields, form layout,
   rules, buttons, views, automations, and *Not built now* with a reason for each omission.
3. **Build** with a step-based script `build/<worksheet>.py`. Every step reads the live state and is safe to re-run.
   Record every id in `build/ids.json`.
4. **Self-check** through the CLI: read back controls, rules, views, buttons, workflows and seeded records.
5. **UI test** in the Nocoly UI against the test list, reading stored values back with the CLI.
6. **Hand-off:** results into section 3, the review page into `artifacts/`, then commit and push to `19.0`.

## Review pages

Each worksheet's hand-off is also published as a page for the reviewer, kept in `artifacts/worksheet-NN-<name>.html`.

- **Start from `artifacts/worksheet-02-units.html`** — it uses the shared stylesheet `artifacts/review.css` (the
  Contacts page predates it and carries its styles inline). Keep its order: identity block and score chips, one
  callout for what the reviewer must know or decide, then Requirements · Build · Tests and differences.
- The page mirrors `worksheets/NN-name.md`; the markdown stays the source of truth. Edit both together.
- Publish it as an artifact with the stylesheet alongside — `files: {"review.css": "nocoly/artifacts/review.css"}` —
  and republish from the same file path to keep its URL.
- Record the URL in the status table in `REVIEWING.md`, and commit the page with the results it shows.

## Conventions

- **Aliases are Odoo field names** (`parent_id`, `relative_factor`); names and labels are Odoo's English labels.
- **One menu group per Odoo app.** Worksheet alias = the model name with underscores (`res_partner`).
- **`build/ids.json`**: the Contacts keys are plain names ("Archive"); every later key is namespaced
  "<Worksheet>: <name>" so buttons and workflows with the same name never collide. Never rename existing keys.
- **Shared helpers** live in `build/common.py`; `build/hap.py` wraps the CLI (`run`, `controls`, `listing`, `backup`).
  Backups of anything a step replaces go to `build/backups/` (not committed).
- **`build/roles.py` is the one builder that is not a worksheet's**: it owns the app's roles, which every
  worksheet's *Not built now* defers to the end of a phase, and records their ids in `ids.json` under `roles`.
  Its keys are the role names, not namespaced.
- **No deletions without the owner's approval.** A mistake is disabled or renamed "ZZ obsolete – " and reported.
- **Records written through the API must set Active explicitly**, or they show in neither the main view nor
  Archived. Test records are named `TEST …`.
- **Read back every write.** Several HAP writes return success and store nothing, or store a malformed value.

## HAP and hap-cli traps (verified 15–17 Sep 2026, hap-cli 0.8.31)

### Worksheets and fields

- `hap app create --sections` also creates an empty, unnamed section ("Unnamed Group").
- `hap worksheet create` builds the icon URL on a Mingdao host; on Nocoly pass
  `--icon-url https://www.nocoly.com/file/mdpub/customIcon/<icon>.svg`. **`hap icon list` and `hap icon search
  <keyword>` are the catalogue** — 426 names, searchable in Chinese or English. A name outside it is refused
  nowhere: the worksheet is created and its icon URL answers HTTP 400 for ever. `hap worksheet update <ws>
  -a <app> --icon <name>` re-icons an existing worksheet and builds the Nocoly URL correctly.
- **`add-fields` parks everything it adds at row 9999, col 0**, whatever `row` and `col` the payload carries
  (`size`, `sectionId` and the rest are kept). A new two-way Relation's reverse arrives there too, width 0 and
  with no alias — that is the general rule, not a quirk of reverses. **Only a full `update-fields` save places a
  control**: there is no per-field endpoint, and hap-cli's own editor ops `field update` and `field reorder` both
  go through `save_controls`. A control can also be **created and placed in that one full save**: sent with a
  client-side 32-hex `controlId` (what hap-cli's `build_control` mints), it gets a server id and keeps the row, col and
  size it was sent with (Products' Favorite re-created at row 1 col 0, 17 Sep).
- **A read-modify-write of a worksheet someone else edits must pin the version.** `SaveWorksheetControls` carries an
  optimistic-lock `version`, but hap-cli's `save_controls` refetches the counter on a conflict and saves anyway — a
  change another administrator made between the read and the save is silently overwritten. Read the controls and
  their `version` in one call (`common.controls_with_version`) and pass it on (`common.save_controls(ws, ctrls,
  version=…)`): hap-cli then returns a conflict as it comes — code 10, 数据过时, which `save_controls` raises — instead of
  retrying over it (its docstring; no conflict was provoked here). Before a surgical save, `hap --json app logs <app>
  --start …` names every operator's recent *Modified worksheet* (Products, version 15 → 16, Favorite, 17 Sep).
- **A deleted field waits in the form designer's field recycle bin** (字段回收站, pd-openweb `FieldRecycleBin.jsx`) for
  the site's `worksheetRowRecycleDays`: `GetWorksheetControls` with `getControlType` **9** lists it — id, alias, place,
  who deleted it and when — and `EditControlsStatus {worksheetId, controlIds, status}` restores it with its id (1)
  or purges it (999). Look there before re-creating a deleted field: a re-created field has a new id, and every view,
  rule and workflow naming the old one must be re-pointed. **Once it is re-created, the old one must never be restored**
  — the worksheet would carry two controls with one name and alias. (Products' Favorite, deleted by another
  administrator at 16:11 on 17 Sep, is still listed there; restoring through the API was not tried.)
- **`add-fields` given a control that already exists appends a second entry with the same `controlId`** instead of
  updating it (`{"code": 1}`, and the worksheet then lists it twice). A full save that sends that id once updates
  **both** copies; a full save that omits it deletes **both**. A duplicate can only be cleared by deleting the
  control and re-creating it.
- A **single Relation to its own worksheet always comes back two-way**, with a reverse control named "Child" that
  **the server creates itself**, in the same `update-fields` save. Writing that reverse by hand — same reserved id —
  makes the server mint its own as well and leaves two controls sharing a controlId. A re-save of the relation does
  not bring a deleted reverse back either: the relation has to be re-created.
- A **two-way Relation added to another worksheet with `add-fields` gets no reverse at all** — the server only
  reserves the id in `sourceControlId` (below). Save the reverse on the target yourself, carrying **that reserved
  controlId**, with `sourceControlId` = the forward control, `sourceControlType` **6** and `enumDefault` 2: the same
  handshake `mount-subtable` performs for a 子表's back-relation. It pairs properly — the forward write shows up in
  the reverse list and a 汇总 over it counts (Products' Category ↔ Product Categories' Products).
  **…and the same is true of a two-way Relation created in the *first full save* of an empty worksheet.**
  `update-fields` on a brand-new worksheet is not the exception it might look like: States' Country, saved that
  way, came back with the reverse id reserved in `sourceControlId` and **no control on Countries** (18 Sep). The
  rule is about the relation's *target* being another worksheet, not about which call created it — only a
  **self**-relation's reverse is made by the server.
- A **one-way Relation** to another worksheet: add it with `add-fields`, without a controlId, and
  `advancedSetting.bidirectional` "0". The target worksheet gets no reverse field.
- A **汇总 (roll-up, control type 37)** has a hap-cli builder:
  `hap_cli.core.app_creator.fields.rollup_control(name, via_control_id=…, source_control_id=…, aggregate=…)`.
  `aggregate` maps to `enumDefault` **1 avg · 2 max · 3 min · 5 sum · 6 count · 21 distinct count**, `dataSource` is
  `$<the bridge 子表 or multi-Relation>$`, and **a count still needs a column named** on the target worksheet in
  `sourceControlId` (the title serves). Added with `add-fields` and re-saved (as a formula must be) it computes at
  once and follows a record moving in or out of the relation (Product Categories' # Products).
- **A 汇总 can carry its own filter** — `rollup_control(…, filters=[…])` stores it in `advancedSetting.filters`, in the
  view-editor enum: a single select's "is" is **filterType 51** with the option key in `values`. It computes over a
  mounted 子表 too: Payment Terms' *Percent total* (`enumDefault` 5, sum of Due where Value is Percent) reads 100 on a
  TEST term holding a 100 Percent and a 50 Fixed line, and *Line count* (6) reads 2 (bundle 3).
- **…and the same filter takes over a multi-Relation, on a *Dropdown* (type 11) of the related worksheet.** Invoice
  Lines' *Tax rate* (`enumDefault` 5, sum of Taxes' Amount through the Taxes relation, `filterType` **51** with the
  Percentage option key) reads **3** on a line carrying a 3 % tax and a **Fixed 7** tax, and **0** on a line carrying
  the Fixed tax alone — so 51 is not limited to the single select of a 子表 (bundle 6, 18 Sep 2026).
- **…and over a *reverse* relation, on a checkbox, added to a 汇总 that was already live.** Products' *# Variants*
  (`enumDefault` 6, a count through the reverse of Product Variants' Product) was filtered to **Active is ticked**
  — a checkbox's "is" is **filterType 2** with `values` `["1"]`, the shape every Active picker filter here carries,
  not the single select's 51 — by a version-pinned save that changed that one control and nothing else. It
  **recomputed at once and on every record**: the TEST product with one active and one archived variant went 2 → 1
  in the same breath, the other eighteen stayed 1, and no record was touched and no nudge needed (21 Sep 2026,
  `variants.set_filters`). A filter written this way also **survives a later full `layout` save** of the holding
  worksheet, which sends each control's `advancedSetting` back as it read it.
- **A 汇总 over a multi-Relation follows the relation, and a *number formula* can read it.** `$<the 汇总>$` inside a
  type-31 expression computes — Invoice Lines' *Total* is `Subtotal × (1 + Tax rate ÷ 100)` — and recomputes on every
  change of the relation through the open API, with no workflow and no re-save (four probes, bundle 6). What it does
  while a **form** is open is a separate question, and the 子表 answer below says it holds only the saved rows.
- **A 汇总 does not follow the rows being edited in the open form** — answered in the browser, 17 Sep 2026: it holds
  the **saved** rows until the record is saved, so a validation rule standing on one judges the record as it was. On a
  new record every roll-up is empty, and Payment Terms' two rules refused every new term, its default 100 % row
  included; both are built and **disabled** (10 §3). Never gate a save on a roll-up of the subtable being edited.
- A **static Relation default** is `defsource: [{"staticValue": "[\"<rowid>\"]"}]`; the server stores the whole record
  in place of the id. The API applies no defaults — only the form does.
- **…and a save that sends that whole record back clears the default.** `GetWorksheetControls` returns the record's
  JSON inside `staticValue`, and a read-modify-write save that returns it unchanged — every `layout` step — stores
  `staticValue` `""` instead, with no error (Contacts' two account defaults, 17 Sep 2026: set, round-tripped, gone).
  `products.py layout` rewrites its Unit default from the record id on every run, which is why it never showed there.
  **`common.save_controls` reduces every static Relation default to its record ids before it saves**
  (`relation_defaults_by_id`); hap-cli's own normaliser only rewrites dynamic defaults whose value starts with "{".
  Compare such a default by record id, never as a string (`accounts.defsource_state`).
- A **Date field's default is a sentinel, not a value**: `defsource` `staticValue` **"2"** with `time` "current" is
  HAP's 当天, the current day (hap-cli's captured payload, `tests/test_core.py::test_date_now_default`). It reads
  like a "+2 days" offset and is not one. An **empty** `staticValue` with the same `time` is stored without
  complaint and applies nothing — and since the API applies no defaults at all, only the form or a byte comparison
  of the stored string can tell the two apart (Invoices' Accounting Date).
- A **hidden field never shows as a table column**, even as the title and listed in the view's columns. A hidden
  title still reaches record titles, cards and pickers. To keep a computed title off the create form but in
  tables, make it read-only and hidden on create: `fieldPermission` "100" (the three places are hidden · read-only ·
  hidden on create, and `0` switches each one on). The list calls behind views blank other hidden fields.
- A single select's `advancedSetting.direction`: 2 horizontal · 1 vertical · 0 matrix.
- A field's **Required holds in the form only**. `record create` through the API writes a record with the
  required field empty and returns success — Product Categories accepted a category with no Name, and its title
  formula then computed an empty string. It joins a text field's maximum length: a form check, not a constraint,
  so seed and import scripts have to check it themselves. (A field's **No duplicates** is the opposite — that one
  is enforced on API writes.)
- A **list-style Relation (`showtype` "2") renders as a tab at the foot of the record**, not as a field in the
  form grid, whatever row the layout gives it. And a list with no `showControls` shows its row count over the
  words ***No visible fields*** — the columns have to be named, by controlId, from the *target* worksheet
  (Product Categories' Child Categories and Products lists).
- **…and no stored setting narrows which records that tab shows.** The tab is drawn from
  `Worksheet/GetRowRelationRows` `{appId, worksheetId: the holding worksheet, rowId, controlId, pageIndex,
  pageSize}` — the same call read from the CLI's session — and on Products' *Variants* (the reverse of Product
  Variants' Product, `showtype` "2") over a product with one active and one archived variant it answered **both
  rows** whatever was stored: with `advancedSetting.filters` set to *Active is ticked*, and with `viewId` bound to
  the target worksheet's own Active-filtered view. A Relation's `filters` is the **picker's** filter and nothing
  else — the entry above says it runs in the browser, and a read-only list offers no picker at all. `viewId` is
  not inert: the rows came back in that view's **sort order**, repeatably, and in the tab's own order again once
  it was cleared — so a bound view gives such a list its order, not its rows. The server itself can filter:
  the same call with **`filterControls`** in the *request* answered one row. So the narrowing has to come from
  whoever calls, and nothing stored makes the call carry it. Consequence for a reverse one2many that Odoo
  active-filters: the **汇总 over it can be made active-only** (below) while the **list beside it cannot** —
  Products' *# Variants* reads 1 where its *Variants* tab lists 2 (21 Sep 2026; whether the browser narrows
  what it renders is for the UI pass).
- **The tab bar at the foot of a record has an order of its own** (pd-openweb `getControlsByTab`): the type-52 tabs
  and the relation lists with `showtype` **"6"** come first, in row order, and the lists with `showtype` **"2"** after
  all of them. Product Categories' Child Categories is a "6" and Products a "2", so an Accounting tab placed under the
  lists would sit between them; at row 2 the bar reads Accounting · Child Categories · Products (bundle 2 — for the
  browser to confirm).
- `worksheet add-fields` keeps a control's client-side 32-hex id, and a formula or text combination added that way
  computes nothing until an `update-fields` save re-mints the id. Inside one `update-fields` save, references to
  not-yet-minted ids (formula expressions, a lookup's source) are rewritten to the minted ids.
- `hap worksheet update-fields` replaces the whole control set. Use it only on a worksheet with no records, or send
  back the full list you just read; add fields to a live worksheet with `add-fields`.
- A new worksheet comes with three stock controls — Name (the title), Description and Attachment. A first
  `update-fields` save that leaves one out deletes it: reuse their ids for your own fields.
- A tab and a field can share a name (the Sales tab and the Sales checkbox): look fields up by name among non-tab
  controls (`common.fields`). **Any other by-name index over the whole control list has the same hazard**: a row map
  built as `{controlName: row}` over Products put the *Sales* **checkbox** on the *Sales* **tab**'s row and moved it
  out of the header into the middle of the form. Key by `controlId` (bundle 6, 18 Sep 2026).
- **Static text on a form takes two controls.** The 分段 block, control type 22 (`SPLIT_LINE`, "Divider"), renders
  its `controlName` as a heading and **renders its `desc` nowhere at all** — not even as a tooltip, so a note written
  there is invisible. The text itself is HAP's **remark block, control type 10010**: the content is HTML in
  `dataSource` (`<p><strong>…</strong> …</p>`), with `advancedSetting.hidetitle` "1" so the `controlName` stays an
  internal label, and `size` 12 for full width. `worksheet_templates` has no builder for type 10010 — send the control
  JSON through `add-fields` and read it back. Both take a `sectionId`, so both can sit inside a tab (Journals' two
  tabs). Note that `common.fields` returns them, since it only filters out type 52.
- A field's **No duplicates** (`unique`) is real on some control types and inert on others, and the control list
  cannot tell them apart — see *No duplicates: where it is real* below.
- A text field's **maximum length does not**. `advancedSetting` `checkrange` "1" with `min` / `max` is a form-side
  check: `record create` and `record update` store a longer value without complaint (a 6-character value on Journals'
  Sequence Prefix, limited to 5). No filter operator measures length either, so a validation rule cannot stand in —
  seed and import scripts have to check the length themselves.
- Worksheet switches 10 (show create button), 26 and 36 (duplicate) and 37 (re-create) remove UI paths only:
  `record create` through the API and workflows still create records.
- The Phone control validates numbers (libphonenumber): an unallocated number such as 03-1234 5678, or a placeholder
  like "NA", is refused.
- **`hap app sort-worksheets <app> <section> <every worksheet id, in order>`** reorders a menu group
  (`HomeApp/UpdateSectionChildSort`); `worksheet create --section-id` always appends. Read the order back from
  `app info` (Chart of Accounts, moved in front of Journals).
- **`common.ensure_section` re-sorts the app's menu groups**, and that is only safe while this build owns them
  all. It puts the group it is given straight after `after`, or **last** when `after` is None, and calls
  `app sort-sections` whenever the result differs from what is live — so calling it for the existing *Contacts*
  group with no `after` would have moved Contacts to the end of the sidebar, behind the CRM group another
  administrator had just added. A builder adding a worksheet to a group that already exists should look the group
  up **by id** and re-sort nothing (`countries.step_create`, 18 Sep).
- **A worksheet is hidden from the sidebar with `HomeApp/SetWorksheetStatus`** `{appId, worksheetId, status}` —
  status **1** shown · **2** hidden everywhere (全隐藏) · 3 hidden on PC · 4 hidden on mobile (pd-openweb
  `api/homeApp.js`). hap-cli has no command for it; call it through the session (`payterms.step_create`). The status
  reads back only from the main site's `HomeApp/GetApp` with `getSection` true (`sections[].workSheetInfo[].status`);
  `hap app info` (V3) lists a hidden worksheet exactly like a visible one. The worksheet keeps its views, rules,
  records and role entries, and still works as a mounted 子表 (Payment Term Lines, bundle 3). What an administrator
  and a role member each see in the sidebar is for the browser.
- **A Number hides its trailing zeros with `advancedSetting.dotformat` "1"** — the field editor's 省略末尾的 0 under
  小数位数 (pd-openweb `PointerConfig.jsx`). `dot` keeps the stored precision: Payment Term Lines' Due has `dot` 6 and
  should show 100 rather than 100.000000 (bundle 3; the rendering is for the browser).
- **A text control can carry a format check**: `advancedSetting.filterregex`, the field editor's 限定输入格式 — a
  JSON list of at most five `{name, value, err}`, `value` the regular expression and `err` the message
  (pd-openweb `TextVerify.jsx`). hap-cli has no builder for it; send it in a full save. **It is the form's check
  only**: the form tests `new RegExp(value, 'gm')` and lets an empty value through (`checkValueByFilterRegex`),
  and `record update` stored the Code `TEST-01` against `^[A-Za-z0-9.]+$` without complaint (Chart of
  Accounts). Import scripts have to check the format themselves, as they do a maximum length.
- **The server re-serialises some JSON-valued `advancedSetting` keys on save**: `filterregex` comes back compact
  with `"filters": null` added to each entry, and a Relation's picker `filters` in its own key order, while
  `defsource` is stored byte for byte. Compare those two parsed, never as strings (`accounts.setting_state`).
- `hap worksheet update --alias` answers `参数错误` unless `-a/--app-id` is passed. `common.ensure_worksheet` calls it
  without one and works there because the worksheet is being created in the same breath; re-aliasing an existing
  worksheet needs the app id (Invoices, `invoices` → `account_move`).
- **The title field moves in one full save**: set `attribute` on every control in the same `update-fields` (1 on the
  new title, 0 on the rest). Two controls carrying `attribute` 1 in one save is undefined, so a control added with
  `is_title` while another still holds it is a coin toss — add it plain and let the layout save move the title.
- A Relation's `sourceControlId` can name a **control that does not exist**: the server reserves the id for a reverse
  field, and if none is ever saved on the target the id just dangles. Re-sending such a control in a full save does
  not create the reverse field either (Invoices' Customer / Vendor, whose placeholder on Contacts was never used).
- **A worksheet mounted as a 子表 (type 34) keeps everything it had.** `hap worksheet mount-subtable <parent>
  <child> --name … --back-relate-name …` does both halves of HAP's 已有关联 handshake: the 子表 on the parent
  (with the child's controls as its `relationControls` snapshot), then the **back-relation on the child carrying
  the placeholder controlId the server reserved** for it — which is what makes rows show under the right parent.
  (`--back-relate-name` names that back-relation at once — Payment Term Lines' *Payment Terms* needed no rename —
  but leaves its alias empty and its `required` false.)
  The child keeps its sidebar entry, its views, its rules and its records; only the `child_fields` kind of 子表
  creates a hidden child table. The back-relation is created *by the mount*, at row 0 col 0 width 12, dropdown,
  with no alias — place and alias it in a later save, sending its `sourceControlId` back untouched. Column order
  is `showControls` (an ordered list) **plus** `advancedSetting.controlssorts` (the same list as a JSON string);
  `advancedSetting.hidetitle` "1" drops the heading above the table. `record get` on the parent returns a 子表
  as a **row count**, an integer, not as the rows (Invoice Lines under Invoices).
- **A 子表 can start a new record with rows**: its custom default (自定义默认值, pd-openweb
  `DynamicDefaultValue/inputTypes/SubSheet/CustomDefaultValue.jsx`) is `advancedSetting.defsource`
  `[{rcid: "", cid: "", staticValue: "<the rows as a JSON string>", isAsync: false}]` with `dynamicsrc` "" and
  `defaulttype` "0"; each row is keyed by the table's column ids plus `pid`, `rowid` (`temp-<uuid>`) and `childrenids`,
  a number as a string and a dropdown as its key list in a string. Payment Terms' Due Terms carries Odoo's default
  line, 100 Percent · 0 · Days after invoice date, stored and read back byte for byte (bundle 3). Like every default
  it is the form's: the API creates a term with no line, and only the browser shows whether the row appears.
- **`worksheet update-fields --controls` stops working once a worksheet carries a 子表.** The whole control list
  goes on the command line and the `relationControls` snapshot pushes it past the kernel's argument limit —
  `OSError: [Errno 7] Argument list too long`. Make the same call through the CLI's own session:
  `hap_cli.core.worksheet.save_controls(Session.load(None), ws, controls)`, which is what the command does anyway
  (`invlines.save_worksheet_controls`; `invoices.py` uses it too since Invoice Lines was mounted).
- **…and so does any worksheet holding a few Relations to a large one.** Every Relation carries the same
  `relationControls` snapshot of its target, and the limit is the kernel's **128 KiB for one argument**
  (`MAX_ARG_STRLEN`), not `ARG_MAX`: Contacts was 93 KB before its two account Relations, and each Relation to Chart of
  Accounts adds about 55 KB. Since bundle 2 the full saves of `contacts.py`, `products.py`, `prodcat.py`,
  `journals.py`, `invlines.py` and `common.add_fields` go through **`common.save_controls(ws, controls)`** — the
  session transport, which also checks the answer and keeps static Relation defaults (above). `invoices.py` already
  used the session; `units.py`, `variants.py` and part A of `accounts.py` still put the list on the command line, and
  their worksheets are well under the limit — switch them the day one gains Relations.
- `add-fields` stores a new control's `fieldPermission` as `""` where every saved control reads `"111"`; the first
  `layout` save writes `"111"`, and a before/after comparison shows it as a change. **Only a save that sends `"111"`
  does**: `contacts.py layout` places a control without touching its permission, and Contacts' two payment-term
  Relations still read `""` after it — `payterms.py` wrote the permission in a save of its own (bundle 3).
- **…but `""` is what an `add-fields` payload carrying *no* `fieldPermission` gets, not a value the endpoint
  refuses.** Sent one, `AddWorksheetControls` stores it: Orders' four button-written controls — Invoicing Closed,
  Signature, Signed By, Signed On — were appended with `fieldPermission` `"100"` in the payload and all four read
  back `"100"` from the append alone, so **no repair save was needed at all** (21 Sep 2026, `orders.py part1`;
  `common.control` only sets the key when `hidden` or `readonly` is passed, which is why Is Template and Template
  Name, appended with neither, still read `""`). A new control that must be read-only from its first moment can
  therefore be appended read-only, without a full `SaveWorksheetControls` ever being made.
- **A control-set digest is not a reliable "untouched" signal when a static Relation default is in play.** The
  default stores the whole related record, `utime` included, so saving *any* record that the default points at
  changes the holding worksheet's control payload without the worksheet being written to at all — no
  `Modified worksheet` entry in `hap app logs`, and the control-set `version` does not move. Products' digest
  shifted when Invoice Lines was seeded with eight lines pointing at the `Units` unit. Compare a worksheet
  control by control, by id, as the build scripts do.
- **…and adding a control to the worksheet a default points *at* does it too.** The embedded record is the related
  row's whole JSON, so a new column on that worksheet appears inside it — and the server re-serialises the snapshot
  on every read, moving its keys about. Giving Chart of Accounts its *Default Taxes* control changed the string
  stored inside **Contacts'** two account defaults, and a raw-string `check_untouched` stopped the run over a
  worksheet nothing had touched. Parse `advancedSetting` before comparing it (`accounts.control_state`, which
  `accounts.signature` and `invlines.signature_of` now go through — bundle 6, 18 Sep 2026).
- **A deleted control's alias is free again at once.** The formula State key was deleted and a **Text** control
  carrying the same name and the same alias `state_key` was added in the next call of the same run: accepted,
  and the alias reads back on the new control. The old one is still listed in the field recycle bin with that
  alias, so the bin reserves nothing — which is the other half of the warning above: **never restore it**, or the
  worksheet carries two controls with one name and one alias (12 §2, 18 Sep).
- **…and the recycle bin fills up with controls nobody deleted.** `add-fields` plus a re-save — the way every
  formula and lookup here is built — mints a server id for the control and drops its **client-side 32-hex id**
  into the bin under the same name and alias. States' bin lists six entries of which one is a real deletion:
  the other five are the two stock controls a first save left out and three client-side ghosts of Display Name,
  Country Code and State key. So the bin is not a list of mistakes, and **restoring from it is almost always
  wrong** — read the live control list first.

### *No duplicates*: where it is real, and where it is decoration

HAP offers **No duplicates** (`unique` on the control) on field types where it does nothing, and the control list
is no guide: `SaveWorksheetControls` accepts the switch wherever it is sent and it reads back `True` everywhere.
What decides is **whether the value being compared is in the write**.

- **Real on a value a write carries — a Text control.** The server compares it against every other record and
  refuses: `record create` and `record update` come back **`resultCode 11`** with the control id in `badData`,
  and nothing is stored. The **form** draws *Duplicates are not allowed* while the field is being edited, as it
  draws a validation rule's message (Countries' Country Code, bundle 4). Empty values are never compared. States'
  *State key* is the same control type and behaves the same way: 2 103 keys written through the API, and the
  one that would have been a second Malaysian `MY|ZZ-01` refused 11 (12 §2, 18 Sep).
- **Decoration on a value the server computes — a function formula (type 53).** Nothing is ever refused: two
  Malaysian states computing the same hidden key `MY|ZZ-01` were both **created** (`resultCode` 1), moving one
  state's code onto the other's by `record update` was accepted, and **the form saved the duplicate too** (12 §3
  test 7, in the browser). The reason is the order of events — the formula is computed *after* the write the
  check would have refused, so at the moment of comparison there is nothing to compare. Read the same argument
  across to a stored lookup and a 汇总: assume the switch there is decoration until something refuses a write.
- **Decoration again on a *workflow's* own write — even on that same Text control.** The switch is applied to
  the open API and **not** to a workflow update step: G's first cut wrote `MY|ZZ-01` onto a second state and HAP
  stored it, a minute after the identical value had been refused 11 through `record update`. Nothing marks it —
  the run came back `status` **2** with every node **2**. Same control, same value, two write paths, two
  answers (12 §2, 18 Sep).
- **So a composite key — Odoo's `unique(country_id, code)` — has to be a Text control something writes**, and in
  HAP that something is a worksheet-event workflow (12's *State key*, written by workflow G). Three consequences,
  all structural:
  - the duplicate **record is still created**. A workflow runs after the save, so no save can be refused for a
    value only the workflow computes;
  - the **workflow's shape is the whole of the enforcement**, since its own write is not checked: it must look
    for a record already holding the key (a search step, excluding the trigger record) and its duplicate path
    must **end in an abort** before the write, not merely rely on being refused;
  - and it must write something **visible** — 12 pairs the key with a read-only *Duplicate code* checkbox —
    **in a step of its own, before** the key, so that whatever happens to the key write the mark stands.
- **A hidden field's No duplicates can never reach the form.** The browser checks what it renders; a hidden or
  read-only computed control is never typed into and never recomputed in the form, so its switch cannot fire on
  a form save whatever the control type. (Reasoned from the two measurements above rather than observed — 12 §3
  is where the browser settles it.) The refusal a person actually sees comes from a field they fill in
  themselves.

### Formulas and lookups

- **Functions need a `c` prefix** in a *number* formula's stored expression — `cMIN`, `cINT`, `cROUNDUP`, `cABS`.
  Written as `MIN(…)` the formula saves and computes empty. Plain arithmetic needs no prefix; a number formula has no IF.
- **IF lives in function formulas** (control type 53). The expression is stored as JSON —
  `{"type": "mdfunction", "expression": …, "status": 1}` — with `enumDefault2` 2 for a text result. Function names
  take **no** `c` prefix there; a dropdown compares by its label (`type == "Delivery"`); the formula recomputes when
  a stored lookup it reads changes (Contacts' Display Name).
- A text combination can use the record id, `$rowid$`.
- **A function formula renders a Number without its decimals' trailing zeros, and an empty Number as nothing.**
  Payment Term Lines' Display name, `CONCAT(Due," ",Value," · ",After," · ",Delay Type)` over a Due with `dot` 6,
  reads "100 Percent · 30 · Days after invoice date" and — with After empty — "50 Percent ·  · Days after end of next
  month" (two spaces). No `TEXT()` or rounding was needed (bundle 3).
- Stored lookups chain: saving a record updates the lookups pointing at it and the formulas built on them, level
  after level — so a self-referencing chain (Absolute Quantity down a unit chain) works without workflows.
- **A stored lookup (`strDefault` "00") may read a function formula on its own worksheet**, which is how a
  recursive text field is built: Product Categories' Complete Name reads Parent Complete Name, a lookup of the
  *parent's* Complete Name. Proved three levels deep, recomputing in both directions on a record save, with no
  workflow and no `refresh` pass. **HAP has no recursion constraint**, so a record can be made its own parent: the
  lookup then reads the record's own last value once — "Goods / Consumables / X / X" — and stops. It is not a loop
  and not an error, and putting the parent back restores the value in one save.
- But the recompute HAP runs **after a formula or lookup definition changes** treats each record on its own and can
  leave rows stale. Re-saving a record's unchanged relation brings its lookups up to date (`units.py refresh`).
- A **lookup of a Relation stores the related record's title as text** (`sourceControlType` 2): it shows and sorts,
  but a picker filter cannot compare a record id with it. Compare the candidate's title field with the lookup
  instead (Product Variants' Extra Packagings).
- **…and a lookup of a *single select* stores the source dropdown's own option key** (`sourceControlType` 11),
  not its label: Invoice Lines' Status reads back `[{"key": "0979d4bb-…", "value": "Draft"}]`, the key minted on
  **Invoices'** Status control. So a rule or filter standing on such a lookup compares the **source** worksheet's
  keys, and its `dataType` is the source control's type (**11**), not the lookup's 30 — the editors read a type-30
  lookup as its source type (pd-openweb `redefineComplexControl`), as they do a function formula. Proved by
  Invoices' two journal checks, which are enforced on `record update` (`resultCode` 32) with exactly that shape
  (06 §2, 21 Sep 2026). A lookup added to a live worksheet **computes on every existing record at once** — all 36
  invoices carried their journal's Type the moment the control was saved, with no nudge.

### Views

- `view create/update --view-spec` ignores sort. Set `sortCid`, `sortType` (2 = ascending) and `moreSort` with
  `view update --view-json … --edit-attrs sortCid,sortType,moreSort`.
- `hap worksheet view sort` never works: it omits the app id, the server answers false and nothing moves. Use
  `common.sort_views`, which makes the same call with the app id.
- `sortType` 1 is descending, 2 ascending. `record list --view-id` applies the view's filter and sort but returns only
  that view's columns — a field the view sorts on but does not show comes back empty.
- A **record just created sits at the top of the table** until the view is reloaded, whatever the sort — HAP puts
  it where the user can see it. It takes its sorted place on the next load, which is worth knowing before
  reporting a sort as broken.
- **A user clicking a table's column header sorts client-side and does not touch the saved view**: `sortCid` and
  `sortType` read back unchanged afterwards.
- An ascending sort puts **empty values first**. `moreSort[].emptyRule` is stored (1, 2 and 3 tried) and changes
  nothing, so Odoo's NULLS LAST cannot be matched.
- A table **sorts on a function formula** (type 53) like any other column — `sortCid` the formula, `sortType` 2 —
  and the rows come back in the formula's own alphabetical order (Product Categories' Complete Name, which reads
  as an indented tree).
- A **quick filter can be added to a live view without rewriting it**:
  `view update --view-json '{"fastFilters": [ …the ones already there…, {"controlId": …, "advancedSetting":
  {"allowitem": "2", "direction": "2"}} ]}' --edit-attrs fastFilters`. `allowitem` is "1" single · "2" any of;
  `direction` "2" a dropdown · "1" tiles. Sending only `fastFilters` leaves the view's filter, sort and columns
  alone (Products' Category quick filter, added beside the four that were already there).
- **…and `--view-spec quickFilters` given a bare control id stores it with an empty `advancedSetting`** —
  Contacts' three and Countries' were all written that way — so a step that then rewrites the settings with
  `--edit-attrs fastFilters` rewrites them on **every** run, because the next `--view-spec` save wipes them
  again. Name the filter as the spec adapter's own object instead: `{fieldId, selectionType: "single" |
  "multiple", displayType: "dropdown" | "tile"}` lowers to `allowitem` and `direction` in the same save, and the
  step is idempotent (States' Country quick filter, 18 Sep).
- **Deleting a field leaves every view sorting on its id.** `sortCid` and `moreSort` keep the dead control id and
  nothing cleans them up (Journals' two views still pointed at a Sequence field removed on 15 Sep). Re-write the sort
  after a field goes. **A quick filter keeps it too** — Products' List still listed the deleted Favorite fourth among
  its `fastFilters` — and so do **a business rule** (Rules, below) and **a workflow step or trigger** (Workflows). To
  re-point a view, send only the attribute with the id replaced in place: `--view-json '{"sortCid": …, "sortType": …,
  "moreSort": […]}' --edit-attrs sortCid,sortType,moreSort`, and `--edit-attrs fastFilters` for the quick filters;
  every other attribute read back unchanged (17 Sep).
- **A view sorts on a Relation by the related record's title, as text**: Payment Term Lines' *Lines* view, sorted
  Payment Terms then created, lists "10 Days after End of Next Month", "15 Days", "2/7 Net 30", "21 Days", … **The
  system field `ctime` works as a sort key** in `moreSort` (`controlId` "ctime", `dataType` 16): Payment Terms' views
  sort Sequence then created, and ten terms sharing Sequence 10 come back in creation order (bundle 3). `record list
  --view-id` returns them in that order; the seed created each term in a second of its own so no two share a `ctime`.
- A **view's or a button's condition on a single select is filterType 51**, not 2: the CLI's filter translator maps
  `eq` to 51 (EQ_FOR_SINGLE) only when the condition carries `dataType` 9 or 11, and to 2 without it. 51 with several
  option keys means "is any of" (Invoices' Reset to Draft: Status is Posted or Cancelled). A **business rule's**
  filter is the other enum, where the same "is any of" is filterType 2.
- **The view and filter editors treat a function formula as its result type** (pd-openweb
  `redefineComplexControl`: a type 53 becomes its `enumDefault2`). A **text** formula's quick filter is therefore a
  *text* filter — `dataType` 2, `filterType` 1 ("contains", the editor's default), no option list — and a picker
  filter comparing a text formula is saved with `dataType` 2 too. Both are stored as sent; what the browser draws
  for the quick filter is for the UI pass to confirm (Chart of Accounts' Internal Group).
- `--view-spec` `tableFields` sets only `displayControls`, and the table then shows every field. A table's columns are
  `showControls` plus `advancedSetting.customShowControls`:
  `view update --view-json '{"showControls":[…],"advancedSetting":{"customdisplay":"1","customShowControls":"[…]"}}'
  --edit-attrs showControls,advancedSetting --edit-ad-keys customdisplay,customShowControls`.

### Rules

- Rule item types: 1 show · 2 hide · **4 read-only** · 5 required · 6 error message · 7 whole record read-only.
  Filter operators: 2 equals · 6 not equals · 7 empty · 8 not empty.
- **Read-only (type 4) works and takes several controls at once** (Invoices locks eight fields while Status is
  Posted or Cancelled). Like every interaction rule it is browser-side: `record create` / `record update` still
  write the fields it greys out — which is how a build script can put a posted record back to a draft.
- A validation rule with `--check-type 1` is enforced on API writes too — but the server checks it **only when one
  of its condition fields is in the write**. A rule that tests only a lookup or formula never fires on the API; add
  the field being edited as a condition. A refused write returns `resultCode 32` naming `<ruleId>:<rowid>`.
- **…and only on an update.** `record create` (`AddWorksheetRow`) is not checked: Chart of Accounts' *A receivable
  or payable account must be reconcilable* (check type 1) refused two `record update`s (`UpdateWorksheetRow`) —
  one sending Type, one sending the box, with the same `0` encoding — and **accepted a `record create` of a Payable
  account with the box unchecked**, both condition fields in the write. The form enforces it; seed and import
  scripts that create records have to check the rule themselves.
- **A validation rule is checked before the save, and a worksheet-event workflow runs after it**, so a workflow
  can never make a write pass a rule. Odoo recomputes a field before its constraint; HAP refuses the write and the
  workflow that would have fixed the value never starts (Chart of Accounts: re-typing a Current Assets account
  as Receivable without ticking Payment Reconciliation is refused, and automation A never runs).
- A rule condition can compare with the record id (`dynamicSource: [{cid: "rowid"}]`).
- A rule **applies its action while its condition holds and the opposite when it does not**, so show and hide are two
  ways of writing the same toggle — except on an empty field. "Show when Type is Sales" keeps the field hidden on a
  new record whose Type is still empty, while "hide when Type is not Sales" depends on how the server compares an
  empty option. Choose the form by what a **new record** should show: *show · equals* leaves the field hidden until
  the driver is set (Journals' four field rules), *hide · equals* leaves the target visible from the start
  (Journals' Advanced Settings tab, Odoo's `invisible="type in ['bank','cash']"`). Flipping one changes the empty case.
- A dropdown condition takes **several option keys in one `values` list**, meaning "is any of" (Journals' Type). It
  reads back in the options' own order, not the order it was written in, so compare unordered.
- A field a rule hides can never be filled, so **a field a rule hides must not be required on the field itself**:
  require it with a second rule carrying the same condition (Journals' two Payment Communications).
- A show/hide rule can target a **whole tab** (the tab's section control), and takes the tab's contents with it —
  remark blocks included.
- **Relation picker filters run in the browser only**: the picker query through the API ignores them, so prove a
  picker filter in the UI. A picker filter can compare a candidate with a Relation field on the form being edited.
- **…but its dynamic value cannot bridge two different dropdowns.** `dynamicSource` reads the *form's* value of a
  control on the holding worksheet, and a single select's value is an **option key minted on that control**. The
  candidate worksheet's own dropdown has its own keys, so a filter comparing the two matches nothing, ever, and
  nothing in HAP maps one option set onto another. Every picker filter in this app that uses `dynamicSource`
  compares a **record id or a text value** for exactly this reason (Products' Packagings, Product Variants' Extra
  Packagings, Chart of Accounts' Parent Account). It is why Odoo's `account.move.journal_id` domain — sale
  journals for a customer document, purchase for a vendor one — **could not be built**, and its constraint
  `_check_journal_move_type` was built as two validation rules instead (06 §2, 15 §1.3). The only conceivable
  bridge is a computed text on each worksheet, which adds a control to both for a filter the CLI cannot prove.
- **An empty dynamic value drops its condition** rather than matching nothing, so a picker on a record whose
  source field is still blank offers everything (03 §2).
- **Read-only (type 4) on a 子表 (type 34) hides the table's row controls.** A rule item accepts the subtable
  among its controls and the server stores it unchanged — `childControlIds: []`, `permission: []`, exactly as
  sent — and in the browser the table loses ***Add a row* and *Batch Operation*** and its required columns lose
  their asterisk, while a record the rule does not catch keeps both (Invoices' *A posted or cancelled document is
  closed for editing*, proved on the posted INV/2026/00001 against the Sunway draft). Like every interaction rule
  it is browser-side only: the API still writes the child records, so seed and roll-up scripts are unaffected.
  **None of that is readable from the CLI** — the stored rule looks the same whether the browser greys the table,
  hides the row controls or ignores it — so a rule acting on a control type this app has not used before has to
  be proved in the UI before it is written down as working.
- **Deleting a control does not take it out of the rules that name it.** Invoices' *A posted or cancelled document is
  closed for editing* still listed the deleted text stand-in `6aa920d74a73a3142152e68d` among its read-only controls
  after the full save that removed it (bundle 3). Give the rule its replacement **before** the deletion — the build
  added the new relation beside the stand-in, so the relation was never unlocked — and rewrite the rule's controls
  afterwards (`invoices.py rules`). Views, buttons and workflow nodes were scanned the same way (`payterms.py
  deadrefs`); a workflow node's `controls`, `addControls`, `filedControls`, `flowNodeList` and `flowNodeAppDtos` are the
  worksheet's control catalogue and name every control, dead or alive, so a scan must leave them out.
- The CLI cannot delete a rule. Disable it (`save-rule --rule-id … --disabled`) and delete it in the UI: worksheet
  ⋯ › Set Worksheet › Business Rules › hover the rule › trash icon.

### Buttons

- `hap worksheet create-custom-action --action-spec` **ignores `--btn-id`**: every run adds another button. Look the
  button up by name with `hap worksheet custom-actions <ws>` first.
- A button that runs a workflow gets a hidden workflow; while it has no steps, its trigger's `nextId` is `99`.
  Deleting the button deletes that workflow too.
- A button's condition **hides** it on a full-page record — a posted Invoices document shows Reset to Draft and
  neither Confirm nor Cancel — and **greys it out in the pop-up record** a table row opens: Payment Terms' Unarchive
  reads disabled beside Archive in the pop-up and is absent from the same record's own page (bundle 3). Write the test
  for the surface it is run on.
- **A validation message is drawn above its field**, and covers whatever sits there: Payment Terms' *Discount %*
  message lands on the Early Discount checkbox, which then cannot be clicked until the field is corrected (bundle 3).
- **A Relation picker lists the newest record first**, whatever the target worksheet's views are sorted by — Odoo
  orders its own by sequence or name, so a picker's order is a difference to record, not a defect (bundle 3).
- `hap workflow trigger <processId> -s <rowid>` runs a button's workflow on one record — a CLI check of a button.
  **It runs a *worksheet-event* workflow on one record too**, which is the only way to re-run one over a record
  without writing to it: a `record update` that changes nothing fires no worksheet-event workflow, so "nudging" a
  record means writing a value and writing it back. Invoice Lines' roll-up, started this way on one line of an
  invoice, rewrote that invoice's four amounts and the run came back `status` 2 (bundle 6, `taxes.py amounts`).
- In a button's workflow a **get related record** step cannot start from the trigger record: the server leaves the
  trigger out of that step's sources, drops the relation field, and publishing fails (warningType 103, 200). Search
  the related worksheet instead: Record ID equals the trigger's Relation field (conditionId 9).

### Workflows

- `workflow node batch-add` names worksheet triggers in Chinese ("工作表事件触发") and drops branch-path names:
  rename them with `workflow node rename`, then republish.
- A get-records node's filter must be written as the UI stores it —
  `filters: [{spliceType: 2, conditions: [[{nodeId: <that node>, filedId, filedTypeId, conditionId: "9",
  conditionValues: [{value: {key, value}}]}]]}]` — with `workflow node save --type 13`. `--nodes` sends
  `operateCondition` instead, which the UI does not use.
- `workflow node get` returns a branch path's conditions as `conditions`; `workflow node save --type 2` expects
  `operateCondition`.
- A get-records filter on a Relation uses conditionId **33**, with `conditionValues: [{nodeId, controlId}]` —
  `rowid` for that node's record, or a Relation field of it.
- To add steps to an existing workflow, `batch-add` with `--trigger-node-id <last node in the chain>` and
  `{"nodeId": …}` references (aliases exist only within one call; `--trigger-alias` then names that last node, not
  the trigger). **`batch-add` can only append**, so a step that has to go in the *middle* of a chain is
  `workflow node add --type <n> -n … --after <the node it follows>` — the same call the abort node needs. A formula
  step is `--type 9` with `-a` its sub-mode (100 number · 106 function · **107 worksheet total**), and a 107 needs
  `--app-id` at create time like any data node: a later `saveNode` cannot attach `appId`. Both roll-ups of bundle 6
  gained their 汇总 and their Tax formula that way, in the middle, and published unchanged otherwise. Change a trigger's fields or condition with
  `workflow node save --type 0 -c '{appId, appType: 1, triggerId, assignFieldIds, operateCondition, returns: []}'`.
- A data step's **worksheet is fixed when the step is added**: `node save` with another `appId` answers success, keeps
  the old one and drops the fields that do not fit. `hap workflow rollback <processId> -y` restores the last published
  version, so a mis-built draft needs no step deleted.
- A create or update step's **field list can be changed in place**: read it with `node get`, change or append the
  entry, send the whole list back with `node save --type 6` (`actionId`, `appId`, `appType`, `selectNodeId`,
  `fields`), then republish (`variants.py` `sync_step`). A text value taken from a node reads back as the template
  `$node-field$`, the other types as `nodeId` + `fieldValueId`. `hap workflow update <processId> -n … -d …` renames a
  workflow; `workflow get` returns its description as `explain`.
- **A step or trigger naming a deleted field keeps the dead id, stays published and raises nothing.** When Products'
  Favorite was deleted in the form designer, Product Variants' automations A, B and C kept it as the `fieldValueId`
  of a create or update entry, and B kept it among its trigger's `assignFieldIds`: `isException` stayed false,
  `publishStatus` 2, and the only sign in `node get` was the entry's **`fieldValueName` reading ""** (it reads the
  field's name once the id is live). A scan for the id finds them (`payterms.py deadrefs <id>`, which skips each
  node's control catalogue). Re-point in place: the entry with only its `fieldValueId` replaced, the whole `fields`
  list sent back with `node save --type 6`; the trigger's `assignFieldIds` with `node save --type 0` (appId, appType,
  triggerId, operateCondition and returns as read); republish, then compare every node with its backup — only the id,
  and the server's `fieldValueName` and `sourceType` on that entry, changed (17 Sep).
- A search step's result branch marks its paths `resultTypeId` 3 (found) and 4 (not found) in `workflow node list`;
  `node get` leaves it out, and `workflow structure` leaves out get-records (type 13) steps.
- **An update step's `selectNodeId` must name a node that produces a record** — the trigger, or a search step.
  Pointed at another **update** step the node comes back `isException: true` with `fields: []` and every field write
  is dropped silently; publishing then fails with `warningType 103`. This is what `batch-add --trigger-node-id <an
  update step>` produces, so re-save those steps' `selectNodeId` afterwards.
- **A workflow update step's field value by type**: a dropdown is the **bare option key** in `fieldValue` (a list
  makes `flowNode/saveNode` answer HTTP 500; a JSON array string is accepted and stored empty). A **text** taken
  from another node is the template `$<nodeId>-<fieldId>$` in `fieldValue`, not `nodeId` + `fieldValueId`. Every
  other type from a node is `nodeId` + `fieldValueId`; from the fixed 系统 node (`5d39140d381d42d20db0c4da`,
  `nowTime` = current time) add `nodeTypeId` 100 and **`nodeAppType`** 100 — send `appType` and the server rewrites
  it, so a step comparing what it sent with what came back re-saves for ever.
- **…and the server converts a text field to that template itself, whichever shape it was sent in.** Sent as
  `nodeId` + `fieldValueId` — what `batch-add` leaves behind, and what a Relation in the same `fields` list keeps —
  a **text** entry reads back with `nodeId` **emptied** and `fieldValue` holding `$<nodeId>-<fieldId>$`. It is the
  same binding written the other way and the step works, but a step that compares what it sent with what came back
  re-saves for ever unless it reads the node id out of the template (`contacts.node_fields.source_of`; Contacts'
  *Copy the company address* shows five templates and one Relation side by side, 18 Sep). `fieldValueName` reading
  `""` on an entry is still the sign of a **dead** field id, whichever shape the entry is in.
- **A search step (flowNodeType 7, actionId 406) returns one record and can be sorted**: `sorts`
  `[{controlId, controlType, isAsc}]` on the node, a filter whose comparison value may be an **earlier formula
  node's** result (`conditionValues: [{nodeId, controlId: "string_fx_id"}]`), and `$<searchNodeId>-<controlId>$`
  reachable from any later formula. Found nothing, that reference reads back as the empty string. So "the row with
  the greatest X" needs no extra field — sort descending and read the first (Invoices' highest-number step).
  `batch-add` writes neither the filter (it sends `operateCondition`) nor the sort; both go in with
  `node save --type 7`.
- **…and its filter can exclude the record that started the run**: `filedId` **"rowid"**, `filedValue` "Record
  ID", `filedTypeId` 2, conditionId **10** (不等于 — the opposite of the 9 every Record-ID *equals* uses), with
  `conditionValues: [{nodeId: <the trigger>, controlId: "rowid"}]`. A field-narrowed trigger fires whenever one
  of its fields is in the write, **changed or not**, so a workflow that searches its own worksheet for "another
  record like this one" needs it: without it an ordinary re-save finds the record itself and the run draws the
  wrong conclusion (States' workflow G, 18 Sep).
- **A workflow's update step is not checked against a field's *No duplicates*.** The switch that refuses a
  `record update` with `resultCode 11` is not applied to the same value written by a step: States' *State key*
  refused the open API and accepted the workflow, leaving two records holding `MY|ZZ-01`. The run says nothing
  about it either — `status` **2**, every node **2**. So a workflow cannot lean on a unique field to stop
  itself: if a step must not write a value, the **path has to end before it**, in an abort node (below).
  Whether a validation rule catches a step's write is a different question and is not answered.
- **A code block (flowNodeType 14) is built with `node add`, `saveNode` and `codeTest`**, and the organisation runs
  it (bundle 3, automations C and D and Confirm):
  1. `hap workflow node add <pid> --type 14 -n … --after <node> -a 102` inserts it after that node (102 JavaScript ·
     103 Python — pd-openweb `WorkflowSettings/enum.js`);
  2. `flow_node.save_node(session, pid, node, 14, {actionId, inputDatas, code, testMap, version, maxRetries})` —
     **`testMap` is required**: without it `flowNode/saveNode` answers **HTTP 500**, even for one line of code. `code` is
     the source **base64-encoded** as the editor does (`btoa(unescape(encodeURIComponent(code)))`); `inputDatas` is
     `[{name, value: "$<nodeId>-<controlId>$"}]`; `maxRetries` defaults to 1;
  3. **the outputs exist only once `flowNode/codeTest` has run it** (`hap workflow node test-code`, the code base64
     again, `inputDatas` carrying test values): the answer's `controls` — one per key of `output`, `type` 1 — are
     stored on the node, and only then can a later step bind them. An update step writes a **Date** field from an
     output with `nodeId` = the code node and `fieldValueId` = the output's key; `isException` stays false and the
     workflow publishes.
  A **get-multiple step's field reaches the code as a list**, one entry per record, in the same record order for every
  field, and **an empty value keeps its place**: a term whose first line has no After and whose second has 5 dated as
  if the lists were aligned. Whether the list arrives as a JSON array or comma-separated text is not visible from the
  CLI — `approval history-detail` lists a code node's run with no input or output — so the code accepts both. A system
  value is reachable as `$5d39140d381d42d20db0c4da-nowTime$`.
- **A get-multiple step (flowNodeType 13, actionId 400) has no `executeType`.** It carries **`execute`** instead:
  true fetches the records when the step runs (直接获取), false — the default — fetches them again every time a later
  step reads them (每次使用时动态获取; pd-openweb `FindMode`). Its filter is `filters`, as a search step's; a Relation
  equal to another node's Relation is conditionId 33 with `conditionValues: [{nodeId, controlId}]`.
- **An update step empties a field with `isClear: true`** on the field entry (the editor's 清空, pd-openweb
  `UpdateFields`). Sent as a plain empty `fieldValue`, the entry is dropped on save — `fields` reads back `[]`, no
  error, and the step writes nothing (automation C's *Empty the Payment Terms*).
- **A search step whose filter value is empty fails the whole run** — status 4, cause 100000 **"筛选条件值为空
  记录ID"** — even with `executeType` 2 (carry on when nothing is found). A Relation that is empty on the record the
  value comes from is enough: Invoice Lines' automation B died at *Get the product variant* on a line with no Product.
  The condition editor's **条件异常时忽略** (`ignoreEmpty` 1 on the condition, offered on a dynamic value) lets the run
  go on — **but the ignored condition leaves the step with no condition, and it hands back a record anyway**: the run
  detail showed the TEST Product variant found for a line with no product, and the category Goods for a product with
  none. So every later step or path that reads a record found that way must first check the Relation it was found
  through (automation B's guarded paths). 值为空时忽略 (`ignoreValueEmpty`) is a different switch, and the editor does
  not offer it on Record ID *equals*.
- **`approval history-detail` gives each step's `sourceId`** — the record a search found or an update wrote — which is
  how to see what a step actually read.
- A path of an exclusive gateway takes **several OR-ed condition groups**: `operateCondition` is a list of AND-groups,
  and `path_state`-style read-backs return the same shape (automation B's journal paths carry four).
- **`+` concatenates in a workflow formula whenever either side is text, and the result is then read as an octal
  literal**: `"5" + 1` is `51`, and `"00005" + 1` is **41** — "000051" parsed as octal. Anything sliced out of a
  text field with `RIGHT`/`LEFT`/`MID` is text, however numeric it looks. Force a numeric context with
  **`SUM(x, 1)`**, `x * 1` or `INT(x)`. There is **no `VALUE()` and no `LEN()`** — either one computes the whole
  expression empty, with no error.
- **A workflow function formula compares with `==`, never `=`.** `IF(1 = 1, …)` saves, publishes and computes
  **empty**, silently emptying the `CONCAT` around it; there is no error anywhere, only a wrong stored value.
  `&&` / `||` are the boolean operators; a ternary and `IIF()` also compute empty. `CONCAT`, `IF`, `YEAR`, `RIGHT`
  and arithmetic work. Inside a formula a dropdown renders its **label** and a checkbox renders `true`/`false`,
  but the checkbox compares equal to `1`.
- A formula node's own result is `string_fx_id` (text) or `number_fx_id` (number). **Counting records** is a formula
  node with actionId **107** (worksheet total), `reportControlId` empty and `reportType` 0, plus its own `filters` —
  and that filter can compare a field with an earlier formula node's result (`kind: "field"`, `fieldId:
  string_fx_id`). **Summing a column** is the same node with `reportControlId` = the column and `reportType` **3**
  (4 avg · 5 max · 6 min), and its filter can compare a Relation with another node's record: `op` "33",
  `conditionValues: [{nodeId, controlId: "rowid"}]`. `batch-add` writes a 107 node's filter correctly (it sends
  `filters`), unlike a search node's (type 7). `batch-add` refuses `nodeType: "code"` outright — but a code block **can** be built through the CLI (below).
- **A field write taking a formula node's result reads `nodeAppType` back as 11**, whatever it was sent as (1 is
  what pd-openweb sends). It is the same binding — the step works and publishes — but a step that compares what it
  sent with what came back re-saves for ever unless it leaves that key out of the comparison (bundle 6).
- **A formula node's result can only be bound as `nodeId` + `fieldValueId` when the node is a worksheet total
  (107) or a number formula (100).** A **function** formula (106) reports `appType` **11**, its `number_fx_id`
  comes back with an empty `type` and `name` in the consuming node's `formulaMap`, that node goes
  `isException: true` and `workflow publish` fails with **warningType 200** and nothing else to go on. A 100 or
  107 result binds with `nodeAppType` **1**, `nodeTypeId` 9 and `nodeActionId` "100"/"107" (Invoice Lines'
  roll-up). A 106 node's **text** result is still reachable as the template `$<nodeId>-string_fx_id$` in a text
  field's `fieldValue` (Invoices' Confirm) — the limit is on the numeric binding, not on function formulas.
- **A workflow number formula (100) rounds to whole numbers and computes empty on an empty input.** `number` on
  the node is its **decimal places**, default **0** — the first roll-up stored 104,603.20 as 104,603 and
  115,063.52 as 115,064 with no error anywhere. `nullZero` is "treat an empty input as 0", default **false** —
  `sum + Tax` on a document whose Tax was never filled produced 0.00. Send `number: 2, nullZero: true`.
- **A worksheet-event trigger takes one event.** 新增 '1' · 新增或更新 '2' · 删除 '3' · 仅更新 '4'; 2 and 3 cannot
  share a trigger, so a roll-up that must survive a deletion is two workflows with the same body.
  `node batch-add --trigger-worksheet … --trigger-event …` configures a `--type worksheet` workflow's trigger in
  the same call; without it the trigger stays unconfigured and the workflow cannot publish.
- **新增或更新 ('2') narrowed to fields (`assignFieldIds`) fires on a create only when the create writes one of those
  fields**, and on an update **whenever one of those fields is in the write — changed or not**. (This bullet first read
  "on every create, whatever the fields": Chart of Accounts' creates all wrote Type. Bundle 3 isolated it: automation C,
  narrowed to Customer / Vendor, ran for every API create carrying a Customer / Vendor and **for none without one** —
  *TEST PT C no customer* has a create entry in its record log and no run. Whether the browser's create sends an empty
  Customer / Vendor, and so starts C, is for the UI pass.) A `record update` sending Type
  unchanged together with a real change to Non Trade started Chart of Accounts' Type-narrowed automation, and
  the record log shows the entry as `Type: 'Current Assets'->'Current Assets'`; a write of Non Trade alone started
  nothing. So a script that re-sends every field re-runs every field-narrowed workflow — as Odoo does for a stored
  compute, since its `write` calls `modified(vals)` on every field written, changed or not (`odoo/orm/models.py`).
- **A `record update` that changes nothing fires no worksheet-event workflow** — so a check that writes back the
  value a record already holds and then re-reads is testing nothing.
- `hap workflow list` takes the **app id as an argument**, not as `-a`.
- `batch-add` in a **second** call drops a branch path's name as well as its condition. (Seen otherwise once: the two
  branches bundle 3 appended to *Contacts: copy company details to its contact* read back with their DSL `condition`
  on the Yes path — the names were set by `contacts.py`'s own rename pass. Read the conditions back rather than trust
  either behaviour.) `node save --type 2` with
  `operateCondition` sets the condition but not the name even with `-n`; the name needs `workflow node rename`.
- Even in a **first** call, `batch-add` returns the **two paths it reuses from a new gateway's default items with no
  name**, while the paths it adds beyond those two keep theirs. The order holds: the gateway's `flowIds` list the
  paths as given. Re-save every path's condition, rename every path, and read both back (Chart of Accounts'
  four-path automation).
- **Whether a workflow's writes start other workflows is the writing workflow's own setting, 触发其他工作流**, in its
  process config (the editor's ⋯ › 流程配置; `hap workflow config-get <pid>` / `config-set`; pd-openweb
  `WorkflowSettings/ProcessConfig`, key **`triggerType`**): **0 允许触发** — HAP's default — · **1 只能触发指定工作流**,
  the workflows listed in `processIds` · **2 不允许触发**. There is no such switch on an update step or on a trigger
  (pd-openweb's action and trigger editors have none). Under 0 the editor's help text adds that **a workflow of the
  writer's own worksheet is started only if it is narrowed to trigger fields**, which accounts for everything seen:
  a variant's Unarchive button writing its product started the product's archive workflow (another worksheet);
  Invoice Lines' automation B writing Account on its line started **none** of the runs of 07's roll-up, which has no
  trigger fields (新增或更新 on any change), while the roll-up ran for every API write of a line; and automation C
  writing Payment Terms, and Confirm filling the Invoice Date, each started automation D, which is narrowed to
  Payment Terms, Invoice Date and Accounting Date — a control run on 17 Sep, 22:40, dated one new invoice twice: C at
  :14, D at :19. **With `triggerType` 2 on C and Confirm, neither starts D any more**: seven actions on *TEST PT once
  …* invoices — creates with a customer's term, a typed term, the same term typed; a date change; a customer change;
  a create and Confirm — each dated the invoice exactly once (`payterms.py selfcheck once`, 17 Sep). A workflow set
  to 2 starts nothing anywhere, so a later workflow that must react to its writes needs 1 with that workflow named.
  Design cascades so a second run finds nothing to change, or switch the writer off when its own run already does
  the work.
- **`workflow config-set` takes the config object**: send back the whole `config-get` answer with only the key changed,
  as the editor's Save does (`revokeNodeIds` kept only while `allowRevoke`, `value` trimmed), then read it back — every
  other key came back unchanged — and **republish**: the editor marks the workflow as having unpublished changes after
  this save (`payterms.ensure_quiet`).
- **An update step copying a field from the trigger record to related records writes an empty value as empty.**
  *Contacts: push company address and Tax ID to its contacts* cleared TEST PT Person's Tax ID when TEST PT Company's
  was emptied (a text template `$trigger-field$`), and its Vendor Payment Terms when the company's was emptied (a
  Relation, `nodeId` + `fieldValueId`) — Odoo's `_commercial_sync_to_descendants` does the same (bundle 3).
- `hap workflow create` can answer **ReadTimeout** after 30 s having created nothing: the workflow list did not show it,
  and running the step again created it once. Look the workflow up by name before re-creating it.
- Give a worksheet-event trigger a condition when most records cannot need the run — every run counts against the
  organisation's workflow quota.
- **A workflow's run history is `hap approval history --process-id <pid>`** — `workflow history` is the *version*
  history, not the runs. An empty run list is the quickest way to tell "the trigger never fired" apart from
  "the steps are wrong", and it is what proved that Invoice Lines' delete roll-up had never once been reached.
  `hap approval history-detail <instanceId>` then lists **every node one run passed through**, in order, each with
  its own status — the only way to show that a step was *not* reached.
- **`approval history`'s `count` is the number of rows on the page it returned, not the total**: `-n 50` gives 50,
  then 37 on page 2, for 87 runs. Count by paging. And tell a new run apart **by its instance id**, never by
  position or by how long the list is: a run registers about **5 s after the write** that starts it, and the
  listing has been seen to lag by a row, which once pinned a run on the write before it (`accounts.wait_new_runs`).
- **A run's detail never lists a branch path node** — only the trigger, the gateway and the steps that ran. A path
  with no step leaves no trace, so which path such a run took can only be inferred. A run that matches **no** path
  of an exclusive gateway is different: it stops there with `status` **3** and `instanceLog.cause` **40002**,
  `causeMsg` **"未通过分支"** (Chart of Accounts' automation on an emptied Type).
- **A branch converges**, so an empty path is not a stop: both paths run into the gateway's `nextId` and carry on
  to whatever follows the branch. To stop a run before a later step, a path must end in an **abort node**.
- **…or the step moves *into* the path, which is usually the better answer.** A branch path can hold a data step:
  `hap workflow node add --type 6 --after <the branch-path node>` sets that path's `nextId` to the new node, which
  then takes its configuration through `node save --type 6` like any other, reads back `isException: false` and
  publishes. So "do the work only when the condition fails" needs no abort at all — hang the work off the path and
  leave the gateway converging on nothing. That matters because **an abort is visible to the user**: an aborted
  run draws HAP's own toast, a warning icon and the untranslated word **中止**, which no name or description
  changes. A run that simply ends comes back `status` **2** with an empty `causeMsg` and draws nothing (Journals'
  archive guard, restructured 21 Sep 2026; 15 §6.6). **There is no "move a node" call**: create the new step
  inside the path, copy the old node's `actionId`, `appId`, `selectNodeId` and `fields` onto it, read them back,
  and only then delete the old node — all on the draft, which `hap workflow rollback <pid> -y` undoes.
  Consequence for anything that reads such a workflow back: **both** paths now carry a `nextId`, so "the path with
  a step on it" no longer identifies the conditioned one — tell them apart by which node they run into.
- **A branch path with no condition is the default/else path** (hap-cli `_build_branch`), and that is how a
  comparison HAP has no operator for is written: put the condition it *does* have on a path with no steps and
  hang the work off the unconditioned one. A Relation compared with **another node's** Relation is `conditionId`
  **33**, the filter's *is*, and hap-cli's operator table has no opposite for it — so "the state's Country is
  **not** the contact's Country" is built as a path conditioned on *is*, carrying nothing, beside an else path
  carrying the write (Contacts' workflows E and F, 12 §2; proved at runtime in both directions).
- **Node type 30 is 中止流程, the abort**, and it is the only way to stop a workflow from inside. It must be last
  in its chain — inserting one in front of an existing node is refused outright with
  `中止节点后面不允许有节点` — and it carries a **name and a description and nothing else**: no message, nothing
  a user ever sees. hap-cli's DSL has no builder for it (`batch-add` cannot make one), so add it with
  `workflow node add --type 30 -n … --after <the last node of that path>`. A run that ended in one comes back from
  `approval history` with `status` **3**, `instanceLog.cause` **6666** and `causeMsg` **"中止"**, naming the node
  (Journals' archive guard; States' workflow G, whose duplicate path reads *tick · clear the key · stop*). That
  status is also the only **visible** mark a run can leave on a record it deliberately did not finish — nothing
  else distinguishes "the step was skipped" from "the step ran", since a step that writes nothing still reports 2.
- **The only thing a button workflow can put in front of a user is a 站内通知** (notice, flowNodeType 27), and it
  is an **in-app notification**, not a dialog: it lands in the workflow channel of the notification list, reading
  **`【<the node's name>】<sendContent>`**. So the node's name is user-facing — name it as a heading. The button's
  own `confirmMsg` is shown *before* the workflow runs and the click always reports "Operation completed", so a
  workflow cannot report a refusal any other way. The name is stored twice: on the node, and inside
  `flowNodeMap` "106" (the channel config that must be sent back or publish fails with warningType 200) —
  `workflow node rename` updates only the first.
- **"The person who triggered the flow" is the fixed 系统 node's `triggeraid`** (`5d39140d381d42d20db0c4da`,
  "Trigger", control type 26), sent wire-shaped:
  `{type: 6, entityId: <系统 node>, roleId: "triggeraid", controlType: 26, appType: 100}` —
  `translate_accounts` passes a recipient with no `kind` through untouched. hap-cli's `kind: "triggerUser"` is a
  different thing: it keys `uaid` off the trigger node, and on a **button** trigger the server reads that back as
  **Last modifier**, the record's last editor rather than whoever pressed the button.
- **`workflow node get` on any node returns `flowNodeList`** — the catalogue of nodes and fields that node may
  reference, each with its controls. It is how to discover what is reachable: the 系统 node's `triggeraid`,
  `triggertime`, `nowTime`, `timestamp`, `sourceId` and `instanceId` are only listed there.
- A **107 (worksheet total) node's filter conditions have their `nodeId` rewritten by the server** to the
  aggregate node's own id. Whatever `left.node` says in the DSL filter is discarded; what binds the count to a
  record is the **comparison value's** `nodeId` — `{kind: "field", node: …, fieldId: "rowid"}`. A later branch
  path then compares the aggregate's own result: `filedId` `number_fx_id`, `filedTypeId` 6, conditionId 14
  (大于等于).
- `hap workflow node delete` **prompts unless `-y` is passed**; without it the `--json` output is
  `{"error": "", "type": "Abort"}` and nothing is deleted.

### Records

- **`hap worksheet record batch-create` is one `AddWorksheetRow` per row *and* one `GetWorksheetControls` per
  row.** Its own help says 每行一次调用, and `hap_cli.core.record.batch_create_rows` calls
  `encode_controls_by_id` per row, which re-reads the worksheet's fields each time — 4 204 HTTP calls to seed
  2 102 states — while `--rows-json` for that many rows is far past the kernel's 128 KiB limit for one
  argument. There is no bulk endpoint behind it, so the saving to be had is the control read: fetch the
  controls once, encode each row with the CLI's own `record._legacy_cell_entry` (so a Relation still becomes
  `[{"sid": …}]` and nothing is sent raw) and call `record.create_record` through the session. **2 102 records
  in 291 seconds**, about seven a second, against 251 countries in five minutes one process at a time
  (`states.batch`, 18 Sep).
- **Two writes a few seconds apart on one record race the workflow runs they start, and the later run wins.** A
  worksheet-event workflow registers about five seconds after the write, so a script that writes, reads the
  value it expects and writes again is racing a run still in flight: the first `states.py selfcheck` set a
  State, then a Country one second later, and the State's workflow evaluated its condition **four seconds
  after** that and wrote the Country back over it — both workflows correct, the test wrong. Wait for the record
  to stop changing before the next write (`states.quiesce`: poll until the value has not moved for ten
  seconds), not just for the value you expect.
- `hap worksheet record delete` needs the rowId UUID; given `_id` it reports success and deletes nothing.
- **`hap worksheet record delete` suppresses workflows unless `--trigger-workflow` is passed**, and **prompts
  unless `-y` is passed** (so it hangs when a script runs it). It is a v3 open-API command; `triggerWorkflow`
  defaults to `true` in the API schema *and* in the command's own `--help`, but the v3 dispatcher renders a
  boolean as a Click flag, an absent flag is `False` rather than `None`, and only `None` / `()` / `""` are
  dropped from the request body — so the CLI sends `triggerWorkflow: false`. The record is deleted and nothing
  downstream runs, with no error and no clue. Always write it in full:
  `hap worksheet record delete <ws> --row-ids <rowid> -a <app> --trigger-workflow -y`. (Invoice Lines' delete
  roll-up looked broken for exactly this reason; the workflow was right all along.) The two record-delete tools
  are the only v3 schemas in the CLI carrying a boolean that defaults to `true`.
- **`hap worksheet record list` returns the default view's columns — and some of the rest, never all of it.**
  A field the view does not show comes back as an empty string, hidden or not (Product Categories' Name came back
  empty from every row because the Categories view shows Complete Name, Parent Category and # Products; Units
  looked like "hidden fields are blanked" for the same reason). But the cut is by **control type**, not by the
  view alone: with `--use-field-id-as-key`, a **Text or Number the view does not show has no key in the row at
  all** — absent, not empty, which is how a reader can tell "not returned" from "no value" — while relations,
  dropdowns, member fields, switches, lookups and formulas come back whether the view shows them or not. Countries'
  view shows Country Name and Country Code, and the rows also carried Zip Required and State Required (switches)
  while Country Calling Code (a Number) and Vat Label (a Text) were missing entirely; Contacts behaves the same
  way (18 Sep). `record get` always returns everything. A reader over many records can therefore page the list and
  fall back to a per-record read **only when a control it needs has no key in the first row**
  (`countries.read_countries`) — 251 rows come back in one call at 0.15 s, against 1.2 s of process start for each
  `record get`.
- **A *hidden* control comes back from the list as the empty string — but a filter on it still works.** Every
  State key read `""` from `GetFilterRows` while `filterControls` "State key **is empty**" returned exactly the
  records that had none. So a hidden field's values can be **found** in one call even though they can only be
  **read** one record at a time: ask the question as a filter (how many are empty, which are ticked) and keep
  `GetRowDetail` for the values themselves — 2 104 of them took 274 s through the session, about eight a second
  (`states.key_column`, `states.step_keys`, 18 Sep). It is part of the cost of hiding a computed key; a visible
  read-only control would have read back from the list.
- **The reverse half of a two-way Relation reads back from `record get` as a row count** — an integer, not the
  rows — exactly as a 子表 does; the forward half returns the usual `[{"sid": …, "name": …}]` (Goods' Child
  Categories is `4`).
- A **Relation cell carries the related record's title**, so a seeded value is compared with the target's *title
  field*, not its name: a product's Category reads back "Goods / IT Equipment" (the Complete Name), never
  "IT Equipment".
- **A single select reads back differently through the two record calls.** `GetRowDetail` (what `record get` is
  built on, and what a script reaches through the session) hands back a JSON list of the option **keys** —
  `["d4ecbc5c-…"]` — while the v3 `record get` command hands back `[{"key": …, "value": "Sales"}]` with the label.
  A reader written for one blanks on the other (bundle 6: every tax read back with an empty Tax Type until the
  option table was consulted). The same is true of the `--use-field-id-as-key` list.
- `record get` returns a record's creation time as `_createdAt`; `record list` returns `ctime` empty.
- `record get` keys a value by the control's **alias**, and by its **controlId** when it has none — the new Payment Terms
  relation on Invoices read back under `6aab8b6b7d58b0f449311740` beside the stand-in's `invoice_payment_term_id` until
  the stand-in was deleted and the relation took the alias (bundle 3). A script that reads by alias must know which.
- **`hap worksheet record logs <ws> <rowid>` is the record's change log**: every write with its time and each
  field's old → new value, including the formulas it recomputed, and a `requestType` — seen as **1** for a
  `record update`, **2** for a workflow's step (button and worksheet-event workflows alike) and **8**
  for the reverse half of a Relation being paired. Set beside `approval history`'s run times it ties each run to
  the write that started it, which is how the Type-narrowed trigger was caught firing on an unchanged Type.
- **A plain string written into a Relation is accepted and stores nothing** — and a seed step that compares
  before it writes then re-writes the same records for ever. Contacts' State and Country were Text when
  `invoices.py customers` was written and became **Relations** in bundles 11 and 12; from then on the step sent
  `{"id": <the Relation's controlId>, "value": "Selangor"}` with every other cell, `record update` answered
  success, the cell read back empty, the comparison found the same difference on the next run, and the step
  finally failed its own read-back (21 Sep 2026). Nothing in the answer says which cell was dropped. Two
  consequences for any seed or import: **check the control's type, not only its name**, before writing a value
  a worksheet has carried since an earlier bundle; and treat a read-back that never converges as a type
  mismatch rather than a stale read. `invoices.seedable_contact_fields` does the first — it drops any seed
  field whose live control is no longer a text field and says so.
- **A worksheet-event workflow can overwrite what a `record create` just sent.** It runs *after* the save, so a
  field a workflow owns is the workflow's, not the create's: Invoice Lines' automation B fills a product line's
  Taxes from the product a moment after the row is written. A seed that must put its own value in one of those
  fields has to **settle** rather than write once — wait for the workflow to land, compare, and only then write
  again (`invlines.settle_taxes`, bundle 7). Where the workflow lands on the same value, as it did on both of
  INV/2026/00002's product lines, nothing is re-written.
- Value formats differ by field type and a wrong one is accepted silently — see `hap guide record` before writing.

### Roles

- **`hap app role list` is not the app's own role list.** It is the V3 endpoint, and V3 renders HAP's **built-in
  label** — 管理员 · 运营者 · 开发者 — for the three typed roles (`roleType` 100 / 2 / 1) whatever name is stored,
  so a rename of one of them looks like it silently failed. It has not: the app's Roles page calls the main
  site's `AppManagement/GetRolesWithUsers`, which returns the stored name, and the browser confirmed it on
  16 Sep 2026 — the page lists Administrator · Operator · Developer under *System* while `hap app role list` was
  still printing the Chinese three. `hap app role permissions` is V3 too and substitutes the same way. Reach the
  main-site call from a build script the way `common.sort_views` reaches SortWorksheetViews —
  `role_mod.get_roles(Session.load(None), app)` (`roles.py`). The two also key a role differently: V3 by `id`,
  the main site by `roleId`.
- **`hap app role rename` answers `0` for a typed role and `1` for a custom one, and renames either way.** It is a
  read-modify-write of the whole `appRoleModel` with only `name` replaced, so `roleType`, `permissionWay`, the
  per-worksheet scopes and the members survive — but the return value is not a success flag. Read the name back.
- **Renaming a typed role writes an app-level log entry that reads like an app rename.** `hap app logs` shows
  `编辑了应用基础信息` and, for some of them, **`Modified App name "X" to "X" and updated App icon`** — boilerplate
  for a save of the app record, with the old name on both sides and no icon in the request (the call sends only
  `{appId, roleId, appRoleModel}`). The app's name, icon and colour were compared before and after and are
  unchanged. Renaming a **custom** role logs `Updated role "<name>" permissions` instead. Expect both when
  reading the log after a roles run, and do not chase them.
- **`hap app role create-fine`** writes a `permissionScope` 0 role: per worksheet, `recordDataScope`
  `{read, edit, delete}` with **0 none · 20 own · 30 own and subordinates' · 100 every record**, plus
  `recordActions.add` for the create right. Three things to know:
  - **Field and view permissions default to fully allowed and stay that way**, so a "read only" worksheet reads
    every field back as `edit: true`; the **record scope is the gate**, not the field list.
  - **`globalPermissions` comes back all `false`** on a fine-grained role and means nothing there — it belongs to
    the coarse `permissionWay` roles.
  - Everything the intent does not name is filled in from hap-cli's defaults: `worksheetActions` no share / no
    import / no export / no batch, discussion on; `recordActions` no share / no print / no log, attachment
    download and discussion on. Write down what you left at default — a reviewer cannot tell a default from a
    decision.
- **`create-fine` only creates, and V3 has no call that edits a role afterwards.** Change an existing role the way
  the Roles page does and `role rename` already does: read the whole `appRoleModel` with
  `role_mod.get_role_detail`, change only what must change, post it back through
  `AppManagement/EditAppRole` with `{appId, roleId, appRoleModel}` (`roles.reconcile`). Everything else goes back
  exactly as it was read, so the scopes, members, field and view permissions cannot move. The main-site model
  names the same switches differently: V3's per-worksheet `worksheetActions.export` is
  `sheets[].worksheetExport.enable` there, and V3's `recordDataScope` `{read, edit, delete}` is
  `readLevel` / `editLevel` / `removeLevel`. A write through either shows up in both.
- **A worksheet created after a role joins that role by itself**, and at HAP's own defaults, not hap-cli's and not
  the role's: `readLevel` / `editLevel` / `removeLevel` **20** (own records only), `canAdd` false, and **every action
  switch on** — share view, import, **export**, batch operation, record share, printing, logging, payment. So a
  fine-grained role silently gains the most permissive entry it has, and every new bundle has to bring its worksheet
  back to the owner's table (`roles.reconcile`, which now takes the role's matrix as well as its description).
  **Including a worksheet that is not this build's**: another administrator's new worksheet joins the business roles
  the same way, and nobody watching this repo will notice. So a roles builder must not insist that the app hold
  exactly the worksheets it owns — it stops only when one of **its own** is missing, leaves every other sheet in
  the role model exactly as it read it, and **prints** the ones it does not own so the gap is visible
  (`roles.unowned`; ERP Master's CRM worksheets Stages and Lost Reasons, 18 Sep, still at 20/20/20 with export on).
- **A role's sheet entry whose views are all unreadable is dropped on save, silently.** `AppManagement/EditAppRole`
  answers `1` and stores nothing — levels, `canAdd` and switches all read back unchanged — until
  `views[].canRead` / `canEdit` / `canRemove` are set true in the same post, which is what every sheet an existing
  role carries has. (The auto-added entry above arrives with all three false.) The record scope is still the gate;
  the view flags are what make the entry real.
- `hap app role list` takes `-a/--app-id`; the app id as a positional argument is refused (the V3 command shadows
  the one in `commands/role_cmd.py`, which takes it positionally).
- **A fine-grained role can hide a single field.** Each sheet of the role model lists every control of the worksheet in
  `fields[]` with **`notAdd` · `notRead` · `notEdit`** — the Roles page's 新增 · 查看 · 编辑 columns — and its tab in
  `sectionId`; V3's `fieldPermissions` reads the same switches as `add` · `read` · `edit`. A control added to a worksheet
  joins every role at once, visible. The page clears 编辑 when 查看 is unticked, and hides a **tab** once every field
  in it is hidden and shows it again as soon as one is visible (pd-openweb `Role/component/RoleSet/TooltipSetting`);
  `roles.py` HIDDEN_FIELDS writes the same through `EditAppRole` (bundle 2's account fields). None of it is readable
  as *behaviour* from the CLI: whether a member of the role sees the field gone needs a browser test with a member.

### In the UI

- An open record can keep a *Modifying form data — Cancel / Save* bar after a relation or member change that is
  already stored; Save clears it.
- A dropdown opens reliably by typing into it; clicking the arrow sometimes does nothing. **To choose an option from
  browser automation, open the dropdown, type the option's label and press Enter** — a click on an option in the
  list does not register, and a quick-filter dropdown behaves the same way (Chart of Accounts' Type filter). A
  **Relation picker or relation quick filter does not take Enter or the arrow keys**: open it, type to narrow the
  list, then click the item — a `.RelateRecordListItem` — at its own rectangle scaled to the screenshot frame
  (`getBoundingClientRect()` × frame width ÷ `innerWidth`; the page can be far wider than the screenshot). The item
  takes a ✓, and a quick filter applies when the list closes on a click outside it (Product Categories' Parent
  Category filter, 17 Sep).
- A validation rule's message shows **while the form is being edited**, the moment its condition holds — before any
  save (Chart of Accounts: Type set to Receivable with the box unticked). No duplicates shows the same way.
- **Escape inside a Create Record dialog closes it and asks "Save the filled content as a draft?"** — close that
  prompt with its ×, not Discard, to get back to the form.
- A Relation shown as a dropdown lists record titles only, never its `showControls`; its search still matches
  those fields ("Hours" finds Minutes and Days on a unit picker). It also **offers archived records** — the
  Invoices Journal picker lists the archived TEST Sales journal beside Sales — so a worksheet that must hide them
  needs a picker filter, which is browser-side only and has to be proved in the UI.
- **HAP marks a read-only field four different ways in the DOM**, which matters when testing a read-only rule: a
  text, number or date control gets the class `controlDisabled` on its `.customFormControlBox`; a Relation gets
  `readonly` on `.RelateRecordDropdown-selected`; a **formula** control gets `customFormReadonly` on its
  `.customFormControlBox` and a recompute icon beside the value, never `controlDisabled` (Invoice Lines'
  Subtotal); and a read-only field with **no value** renders as an empty `<div class="customFormNull">`,
  indistinguishable from an empty editable field.
- A **newly created record stays in a view whose filter excludes it until the page is reloaded** (a Vendor Bill
  created from the Invoices view, whose filter is Type). The filter itself is right; the open list is stale.
- A Rich text field never shows its hint, even when clicked into. Put guidance in the description instead.
- A checkbox quick filter has two states once used: a click filters for ticked, the next for unticked, and the box
  then looks empty while still filtering. Reloading the view clears it.
- A change typed into an open record is stored only with Save on the *Modifying form data* bar; an open view
  re-sorts only after Refresh; a record that leaves the open view (Archive) closes itself.
- An unsubmitted Create Record form is kept as a local draft and offered back ("Restored to the last interrupted
  content"); clear it before a clean test.

- A Number's **`thousandth` reads the opposite way round from its name**: `"0"` — the platform default every
  Number in this app carries — *draws* the thousands separator, and `"1"` hides it. Countries' Country Calling
  Code showed *1,264* for Anguilla until it was set to `"1"`, and *1264* after. Nothing in the control's other
  keys says so, and `worksheet fields` does not print `advancedSetting` at all, so read it back from the raw
  control.

### Reading Odoo in the browser (18 Sep 2026)

- **Odoo does not render in a background tab.** Its client waits for an animation frame and Chrome gives none to a
  tab whose `document.visibilityState` is *hidden*, so the page stops after the top bar and the control panel:
  `main.o_content` is empty and every screenshot is a dark rectangle. **A screenshot forces one frame**, so read
  an Odoo page as *navigate → wait → screenshot → screenshot*: the first screenshot is blank and pays for the
  paint, the second is the page. Nocoly's own app renders while hidden, which is why only the Odoo side ever
  looked broken — and why three worksheets carried a false "the tenant has no screen for this".
- The reference tenant's admin is an **Invoicing** administrator: it holds `account.group_account_invoice`,
  `account.group_account_manager` and `account.group_account_basic`, but **not** `account.group_account_readonly`
  or `account.group_account_user`. Every field Odoo puts behind those two groups — a journal's five accounts, a
  product's and a category's income and expense accounts, an invoice line's account and date, a contact's
  receivable and payable — is therefore **invisible on the tenant's own screens**, though `fields_get` and a
  record read return it. Read `ir.ui.view.arch_db` when you need the real form, not `get_views`, which is already
  filtered by the caller's groups.
- Reading the raw arch over RPC in the page: `ir.ui.view.search_read([('model','=',…),('type','in',['form','list'])], ['name','arch_db'])`
  and pull field names with a regex. Return **only what you need** — a whole arch trips the session's
  "cookie/query string data" guard and the call comes back blocked, and anything over ~1,900 characters is
  truncated. `res.groups.search_read([('all_user_ids','in',[uid])])` answers what the tenant's user can see.

### Role debugging — testing a role without a member (18 Sep 2026)

- **HAP can show the app as any role, with no member assigned.** The owner switched it on: **Select Role** sits at
  the foot of the app's sidebar, lists System (Administrator · Operator · Developer) and Custom roles, and the
  chosen one becomes a chip at the same place with an ✕ to leave. This is how every "role visibility" test that
  had been parked — 09's test 28, 11's test 23 — was finally run.
- **It applies to the account's API session too, not just the browser.** While a role is being debugged, the
  `hap` CLI on the same account is refused with **`Insufficient permissions`** for anything that role cannot do
  (`app role list` fails; worksheet reads still work). **Switch the role off before running a build script** —
  the script will fail halfway otherwise, and the cause does not look like a permission at all.
- What it proved, first time: a **tab whose every field is hidden from a role disappears with them** (a contact's
  *Invoicing* tab for Invoicing and Accounting Read-only; a product's and a category's *Accounting* tab for
  Invoicing); a hidden field **leaves the table column out as well as the form field** (Journals' Default
  Account, Invoice Lines' Account); a view-only worksheet **has no + Record button**; a relation **picker offers
  no + Record** when the role cannot create in the target worksheet — which is how Odoo's `no_create` is
  enforced here; and a read-only record renders as plain text with no input boxes.
- **Read the table in a wide window.** A narrow or zoomed window renders only the leftmost columns, and a missing
  column then looks exactly like a hidden field — it cost a wrong finding on Journals before the same list, in a
  wide window, showed the column it was supposed to.

### Four more, from the Taxes UI test (18 Sep 2026)

- **`advancedSetting.showtype` on a *Dropdown* (type 11) is the display style, and it is not the Relation's
  meaning.** "0" is the dropdown, "1" tiles, "2" the **progress bar** — which draws the option as a slider with a
  bar behind it in the table and reads as a defect beside every other column. On a **Relation** (type 29) the
  same key means list · tab · dropdown, which is where the confusion comes from: Taxes' five Dropdowns were built
  with "2" in the belief that it meant "a dropdown list, as Journals' and Invoices' single selects". It does not
  — all thirteen Dropdowns built before them carry **"0"**. A `SingleSelect` (type 9) with "1" is a deliberate
  tile row (Products' Product Type, Odoo's radio).
- **`record list` blanks a multi-value Relation and a 汇总 even when the view shows them.** Single relations come
  back populated, so this is not the "columns the view does not show" cut above: Invoice Lines' *Taxes* and *Tax
  rate* read as empty strings through `record list --view-id` on a view that carries both, while *Product*,
  *Account* and *Unit* on the same rows read fine. **`record get` shows them**, and it takes the **`rowId`
  (the uuid), not the `_id`** — passing `_id` answers *行记录不存在或没权限*, which reads like a permission
  problem and is not one.
- **A 子表 row's panel draws the *subtable's* columns, not the child worksheet's form.** A field that is on the
  child's form but missing from `showControls` is missing from the row panel as well, so a person opening the row
  from inside the parent cannot see or set it — Invoice Lines' *Taxes* was on the worksheet, held the right
  values and drove the arithmetic, and was invisible and unsettable from inside an invoice until it was added to
  the column list. **Add a field to `showControls` whenever a person must edit it from the parent**, not only
  when it should be a visible column.
- **A self-check that finds its probe record by name breaks the moment the duplicate check is exercised in the
  UI** — which is exactly what the house rule asks for, since `TEST …` records are left in place. A second record
  with the probe's name makes `{name: rowid}` keep whichever came last, and the run then drives the *marked*
  record and reports DIFF on probes the workflow actually passed. Resolve the probe by the record that **holds
  the key**, and say so when the name is shared.

### Five from the Orders build (21 Sep 2026)

- **A function default only fires in the browser.** A number control whose value comes from
  `advancedSetting.defaulttype "1"` + `defaultfunc` is computed **client-side, in the form**. The API applies no
  defaults, so every record written by a seed stores it **empty**. Order Lines' Subtotal was built this way and
  worked perfectly for the two lines typed in the browser, then stored blank on all thirty seeded ones — and
  because Tax Amount and Total were Formulas built on it, they went blank too and all twelve order roll-ups read
  `0.00`. **A control that anything other than a person will write must be a Formula (type 31), not a function
  default.**
- **A control that reads a 汇总 must be a Formula**, for the same reason from the other direction: a roll-up is
  computed server-side and has no value while the form is open, so a client-side function default reading one
  evaluates to nothing.
- **A type 31 formula does read a Currency (type 8) operand.** Order Lines' Unit Price is a t8 where Invoice
  Lines' is a plain t6, which was the one thing its Subtotal formula could not copy from 07. Every Subtotal
  computed, so it is settled.
- **A definition change can recompute cleanly, and can also leave rows stale.** Converting Subtotal recomputed
  all 30 lines and all 12 orders at once, three levels deep, with no nudge. An earlier conversion on the same
  worksheet left one order rounded to whole ringgit because the roll-up recomputed while it still carried
  `dot = 0`. So: **set `dot` before the child's figures change**, and read back rather than assume either way.
- **A record listing drops fields the control hides; `record get` returns them.** `common.records` read
  Prepayment Percentage (`fieldPermission` `011`) as `''` on all twelve orders that had just been written with
  100, and read every tax's Amount as `''` while the tax-rate roll-up was correctly summing 10 and 8. **Never
  conclude a hidden field is empty from a listing** — fetch the record.
