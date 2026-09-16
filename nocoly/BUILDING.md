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

## HAP and hap-cli traps (verified 15–16 Sep 2026, hap-cli 0.8.31)

### Worksheets and fields

- `hap app create --sections` also creates an empty, unnamed section ("Unnamed Group").
- `hap worksheet create` builds the icon URL on a Mingdao host; on Nocoly pass
  `--icon-url https://www.nocoly.com/file/mdpub/customIcon/<icon>.svg`.
- A new two-way Relation's reverse control comes back at row 9999, width 0, with no alias. Place it in a second save.
  A **single Relation to its own worksheet always comes back two-way**, with a reverse control named "Child".
- A **one-way Relation** to another worksheet: add it with `add-fields`, without a controlId, and
  `advancedSetting.bidirectional` "0". The target worksheet gets no reverse field.
- A **static Relation default** is `defsource: [{"staticValue": "[\"<rowid>\"]"}]`; the server stores the whole record
  in place of the id. The API applies no defaults — only the form does.
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
- `worksheet add-fields` keeps a control's client-side 32-hex id, and a formula or text combination added that way
  computes nothing until an `update-fields` save re-mints the id. Inside one `update-fields` save, references to
  not-yet-minted ids (formula expressions, a lookup's source) are rewritten to the minted ids.
- `hap worksheet update-fields` replaces the whole control set. Use it only on a worksheet with no records, or send
  back the full list you just read; add fields to a live worksheet with `add-fields`.
- A new worksheet comes with three stock controls — Name (the title), Description and Attachment. A first
  `update-fields` save that leaves one out deletes it: reuse their ids for your own fields.
- A tab and a field can share a name (the Sales tab and the Sales checkbox): look fields up by name among non-tab
  controls (`common.fields`).
- **Static text on a form takes two controls.** The 分段 block, control type 22 (`SPLIT_LINE`, "Divider"), renders
  its `controlName` as a heading and **renders its `desc` nowhere at all** — not even as a tooltip, so a note written
  there is invisible. The text itself is HAP's **remark block, control type 10010**: the content is HTML in
  `dataSource` (`<p><strong>…</strong> …</p>`), with `advancedSetting.hidetitle` "1" so the `controlName` stays an
  internal label, and `size` 12 for full width. `worksheet_templates` has no builder for type 10010 — send the control
  JSON through `add-fields` and read it back. Both take a `sectionId`, so both can sit inside a tab (Journals' two
  tabs). Note that `common.fields` returns them, since it only filters out type 52.
- A field's **No duplicates** (`unique`) holds on API writes too: the write is refused with `resultCode 11` naming the
  field. Empty values are never compared.
- A text field's **maximum length does not**. `advancedSetting` `checkrange` "1" with `min` / `max` is a form-side
  check: `record create` and `record update` store a longer value without complaint (a 6-character value on Journals'
  Sequence Prefix, limited to 5). No filter operator measures length either, so a validation rule cannot stand in —
  seed and import scripts have to check the length themselves.
- Worksheet switches 10 (show create button), 26 and 36 (duplicate) and 37 (re-create) remove UI paths only:
  `record create` through the API and workflows still create records.
- The Phone control validates numbers (libphonenumber): an unallocated number such as 03-1234 5678, or a placeholder
  like "NA", is refused.
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
  The child keeps its sidebar entry, its views, its rules and its records; only the `child_fields` kind of 子表
  creates a hidden child table. The back-relation is created *by the mount*, at row 0 col 0 width 12, dropdown,
  with no alias — place and alias it in a later save, sending its `sourceControlId` back untouched. Column order
  is `showControls` (an ordered list) **plus** `advancedSetting.controlssorts` (the same list as a JSON string);
  `advancedSetting.hidetitle` "1" drops the heading above the table. `record get` on the parent returns a 子表
  as a **row count**, an integer, not as the rows (Invoice Lines under Invoices).
- **`worksheet update-fields --controls` stops working once a worksheet carries a 子表.** The whole control list
  goes on the command line and the `relationControls` snapshot pushes it past the kernel's argument limit —
  `OSError: [Errno 7] Argument list too long`. Make the same call through the CLI's own session:
  `hap_cli.core.worksheet.save_controls(Session.load(None), ws, controls)`, which is what the command does anyway
  (`invlines.save_worksheet_controls`; `invoices.py` uses it too since Invoice Lines was mounted).
- **A control-set digest is not a reliable "untouched" signal when a static Relation default is in play.** The
  default stores the whole related record, `utime` included, so saving *any* record that the default points at
  changes the holding worksheet's control payload without the worksheet being written to at all — no
  `Modified worksheet` entry in `hap app logs`, and the control-set `version` does not move. Products' digest
  shifted when Invoice Lines was seeded with eight lines pointing at the `Units` unit. Compare a worksheet
  control by control, by id, as the build scripts do.

### Formulas and lookups

- **Functions need a `c` prefix** in a *number* formula's stored expression — `cMIN`, `cINT`, `cROUNDUP`, `cABS`.
  Written as `MIN(…)` the formula saves and computes empty. Plain arithmetic needs no prefix; a number formula has no IF.
- **IF lives in function formulas** (control type 53). The expression is stored as JSON —
  `{"type": "mdfunction", "expression": …, "status": 1}` — with `enumDefault2` 2 for a text result. Function names
  take **no** `c` prefix there; a dropdown compares by its label (`type == "Delivery"`); the formula recomputes when
  a stored lookup it reads changes (Contacts' Display Name).
- A text combination can use the record id, `$rowid$`.
- Stored lookups chain: saving a record updates the lookups pointing at it and the formulas built on them, level
  after level — so a self-referencing chain (Absolute Quantity down a unit chain) works without workflows.
- But the recompute HAP runs **after a formula or lookup definition changes** treats each record on its own and can
  leave rows stale. Re-saving a record's unchanged relation brings its lookups up to date (`units.py refresh`).
- A **lookup of a Relation stores the related record's title as text** (`sourceControlType` 2): it shows and sorts,
  but a picker filter cannot compare a record id with it. Compare the candidate's title field with the lookup
  instead (Product Variants' Extra Packagings).

### Views

- `view create/update --view-spec` ignores sort. Set `sortCid`, `sortType` (2 = ascending) and `moreSort` with
  `view update --view-json … --edit-attrs sortCid,sortType,moreSort`.
- `hap worksheet view sort` never works: it omits the app id, the server answers false and nothing moves. Use
  `common.sort_views`, which makes the same call with the app id.
- `sortType` 1 is descending, 2 ascending. `record list --view-id` applies the view's filter and sort but returns only
  that view's columns — a field the view sorts on but does not show comes back empty.
- An ascending sort puts **empty values first**. `moreSort[].emptyRule` is stored (1, 2 and 3 tried) and changes
  nothing, so Odoo's NULLS LAST cannot be matched.
- **Deleting a field leaves every view sorting on its id.** `sortCid` and `moreSort` keep the dead control id and
  nothing cleans them up (Journals' two views still pointed at a Sequence field removed on 15 Sep). Re-write the sort
  after a field goes.
- A **view's or a button's condition on a single select is filterType 51**, not 2: the CLI's filter translator maps
  `eq` to 51 (EQ_FOR_SINGLE) only when the condition carries `dataType` 9 or 11, and to 2 without it. 51 with several
  option keys means "is any of" (Invoices' Reset to Draft: Status is Posted or Cancelled). A **business rule's**
  filter is the other enum, where the same "is any of" is filterType 2.
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
- **Read-only (type 4) on a 子表 (type 34) hides the table's row controls.** A rule item accepts the subtable
  among its controls and the server stores it unchanged — `childControlIds: []`, `permission: []`, exactly as
  sent — and in the browser the table loses ***Add a row* and *Batch Operation*** and its required columns lose
  their asterisk, while a record the rule does not catch keeps both (Invoices' *A posted or cancelled document is
  closed for editing*, proved on the posted INV/2026/00001 against the Sunway draft). Like every interaction rule
  it is browser-side only: the API still writes the child records, so seed and roll-up scripts are unaffected.
  **None of that is readable from the CLI** — the stored rule looks the same whether the browser greys the table,
  hides the row controls or ignores it — so a rule acting on a control type this app has not used before has to
  be proved in the UI before it is written down as working.
- The CLI cannot delete a rule. Disable it (`save-rule --rule-id … --disabled`) and delete it in the UI: worksheet
  ⋯ › Set Worksheet › Business Rules › hover the rule › trash icon.

### Buttons

- `hap worksheet create-custom-action --action-spec` **ignores `--btn-id`**: every run adds another button. Look the
  button up by name with `hap worksheet custom-actions <ws>` first.
- A button that runs a workflow gets a hidden workflow; while it has no steps, its trigger's `nextId` is `99`.
  Deleting the button deletes that workflow too.
- A button's condition **hides** it when unmet on an open record — a posted Invoices document shows Reset to Draft
  and neither Confirm nor Cancel — though a greyed-out button has also been seen elsewhere in the UI. Do not write
  a test expecting one or the other without checking the worksheet you are on; Journals' own hand-off records the
  same hiding on a full-page record.
- `hap workflow trigger <processId> -s <rowid>` runs a button's workflow on one record — a CLI check of a button.
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
  the trigger). Change a trigger's fields or condition with
  `workflow node save --type 0 -c '{appId, appType: 1, triggerId, assignFieldIds, operateCondition, returns: []}'`.
- A data step's **worksheet is fixed when the step is added**: `node save` with another `appId` answers success, keeps
  the old one and drops the fields that do not fit. `hap workflow rollback <processId> -y` restores the last published
  version, so a mis-built draft needs no step deleted.
- A create or update step's **field list can be changed in place**: read it with `node get`, change or append the
  entry, send the whole list back with `node save --type 6` (`actionId`, `appId`, `appType`, `selectNodeId`,
  `fields`), then republish (`variants.py` `sync_step`). A text value taken from a node reads back as the template
  `$node-field$`, the other types as `nodeId` + `fieldValueId`. `hap workflow update <processId> -n … -d …` renames a
  workflow; `workflow get` returns its description as `explain`.
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
- **A search step (flowNodeType 7, actionId 406) returns one record and can be sorted**: `sorts`
  `[{controlId, controlType, isAsc}]` on the node, a filter whose comparison value may be an **earlier formula
  node's** result (`conditionValues: [{nodeId, controlId: "string_fx_id"}]`), and `$<searchNodeId>-<controlId>$`
  reachable from any later formula. Found nothing, that reference reads back as the empty string. So "the row with
  the greatest X" needs no extra field — sort descending and read the first (Invoices' highest-number step).
  `batch-add` writes neither the filter (it sends `operateCondition`) nor the sort; both go in with
  `node save --type 7`.
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
  `filters`), unlike a search node's (type 7). There is **no code node** through the CLI: `batch-add` refuses
  `nodeType: "code"` outright.
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
- **A `record update` that changes nothing fires no worksheet-event workflow** — so a check that writes back the
  value a record already holds and then re-reads is testing nothing.
- `hap workflow list` takes the **app id as an argument**, not as `-a`.
- `batch-add` in a **second** call drops a branch path's name as well as its condition. `node save --type 2` with
  `operateCondition` sets the condition but not the name even with `-n`; the name needs `workflow node rename`.
- **A record written by a workflow starts that worksheet's event workflows** (a variant's Unarchive button writing its
  product started the product's archive workflow). Design cascades so the second run finds nothing to change.
- Give a worksheet-event trigger a condition when most records cannot need the run — every run counts against the
  organisation's workflow quota.
- **A workflow's run history is `hap approval history --process-id <pid>`** — `workflow history` is the *version*
  history, not the runs. An empty run list is the quickest way to tell "the trigger never fired" apart from
  "the steps are wrong", and it is what proved that Invoice Lines' delete roll-up had never once been reached.
  `hap approval history-detail <instanceId>` then lists **every node one run passed through**, in order, each with
  its own status — the only way to show that a step was *not* reached.
- **A branch converges**, so an empty path is not a stop: both paths run into the gateway's `nextId` and carry on
  to whatever follows the branch. To stop a run before a later step, a path must end in an **abort node**.
- **Node type 30 is 中止流程, the abort**, and it is the only way to stop a workflow from inside. It must be last
  in its chain — inserting one in front of an existing node is refused outright with
  `中止节点后面不允许有节点` — and it carries a **name and a description and nothing else**: no message, nothing
  a user ever sees. hap-cli's DSL has no builder for it (`batch-add` cannot make one), so add it with
  `workflow node add --type 30 -n … --after <the last node of that path>`. A run that ended in one comes back from
  `approval history` with `status` **3** and `instanceLog.causeMsg` **"中止"**, naming the node (Journals' archive
  guard).
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
- `hap worksheet record list` can return hidden fields as empty strings (seen on Units, not always on Contacts or
  Products); `record get` always returns their values.
- `record get` returns a record's creation time as `_createdAt`; `record list` returns `ctime` empty.
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
- `hap app role list` takes `-a/--app-id`; the app id as a positional argument is refused (the V3 command shadows
  the one in `commands/role_cmd.py`, which takes it positionally).

### In the UI

- An open record can keep a *Modifying form data — Cancel / Save* bar after a relation or member change that is
  already stored; Save clears it.
- A dropdown opens reliably by typing into it; clicking the arrow sometimes does nothing.
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
