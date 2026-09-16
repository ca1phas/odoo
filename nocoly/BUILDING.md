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
- **No deletions without the owner's approval.** A mistake is disabled or renamed "ZZ obsolete – " and reported.
- **Records written through the API must set Active explicitly**, or they show in neither the main view nor
  Archived. Test records are named `TEST …`.
- **Read back every write.** Several HAP writes return success and store nothing, or store a malformed value.

## HAP and hap-cli traps (verified 15 Sep 2026, hap-cli 0.8.31)

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
  that view's columns.
- An ascending sort puts **empty values first**. `moreSort[].emptyRule` is stored (1, 2 and 3 tried) and changes
  nothing, so Odoo's NULLS LAST cannot be matched.
- **Deleting a field leaves every view sorting on its id.** `sortCid` and `moreSort` keep the dead control id and
  nothing cleans them up (Journals' two views still pointed at a Sequence field removed on 15 Sep). Re-write the sort
  after a field goes.
- `--view-spec` `tableFields` sets only `displayControls`, and the table then shows every field. A table's columns are
  `showControls` plus `advancedSetting.customShowControls`:
  `view update --view-json '{"showControls":[…],"advancedSetting":{"customdisplay":"1","customShowControls":"[…]"}}'
  --edit-attrs showControls,advancedSetting --edit-ad-keys customdisplay,customShowControls`.

### Rules

- Rule item types: 1 show · 2 hide · 4 read-only · 5 required · 6 error message · 7 whole record read-only.
  Filter operators: 2 equals · 6 not equals · 7 empty · 8 not empty.
- A validation rule with `--check-type 1` is enforced on API writes too — but the server checks it **only when one
  of its condition fields is in the write**. A rule that tests only a lookup or formula never fires on the API; add
  the field being edited as a condition. A refused write returns `resultCode 32` naming `<ruleId>:<rowid>`.
- A rule condition can compare with the record id (`dynamicSource: [{cid: "rowid"}]`).
- A rule **applies its action while its condition holds and the opposite when it does not**, so show and hide are two
  ways of writing the same toggle — except on an empty field. "Show when Type is Sales" keeps the field hidden on a
  new record whose Type is still empty, while "hide when Type is not Sales" depends on how the server compares an
  empty option. Write the positive form (show · equals) whenever the field must stay hidden until the driver is set.
- A dropdown condition takes **several option keys in one `values` list**, meaning "is any of" (Journals' Type). It
  reads back in the options' own order, not the order it was written in, so compare unordered.
- A field a rule hides can never be filled, so **a field a rule hides must not be required on the field itself**:
  require it with a second rule carrying the same condition (Journals' two Payment Communications).
- A show/hide rule can target a **whole tab** (the tab's section control).
- **Relation picker filters run in the browser only**: the picker query through the API ignores them, so prove a
  picker filter in the UI. A picker filter can compare a candidate with a Relation field on the form being edited.
- The CLI cannot delete a rule. Disable it (`save-rule --rule-id … --disabled`) and delete it in the UI: worksheet
  ⋯ › Set Worksheet › Business Rules › hover the rule › trash icon.

### Buttons

- `hap worksheet create-custom-action --action-spec` **ignores `--btn-id`**: every run adds another button. Look the
  button up by name with `hap worksheet custom-actions <ws>` first.
- A button that runs a workflow gets a hidden workflow; while it has no steps, its trigger's `nextId` is `99`.
  Deleting the button deletes that workflow too.
- A button's condition greys it out when unmet; it does not hide it.
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
- **A record written by a workflow starts that worksheet's event workflows** (a variant's Unarchive button writing its
  product started the product's archive workflow). Design cascades so the second run finds nothing to change.
- Give a worksheet-event trigger a condition when most records cannot need the run — every run counts against the
  organisation's workflow quota.

### Records

- `hap worksheet record delete` needs the rowId UUID; given `_id` it reports success and deletes nothing.
- `hap worksheet record list` can return hidden fields as empty strings (seen on Units, not always on Contacts or
  Products); `record get` always returns their values.
- `record get` returns a record's creation time as `_createdAt`; `record list` returns `ctime` empty.
- Value formats differ by field type and a wrong one is accepted silently — see `hap guide record` before writing.

### In the UI

- An open record can keep a *Modifying form data — Cancel / Save* bar after a relation or member change that is
  already stored; Save clears it.
- A dropdown opens reliably by typing into it; clicking the arrow sometimes does nothing.
- A Relation shown as a dropdown lists record titles only, never its `showControls`; its search still matches
  those fields ("Hours" finds Minutes and Days on a unit picker).
- A Rich text field never shows its hint, even when clicked into. Put guidance in the description instead.
- A checkbox quick filter has two states once used: a click filters for ticked, the next for unticked, and the box
  then looks empty while still filtering. Reloading the view clears it.
- A change typed into an open record is stored only with Save on the *Modifying form data* bar; an open view
  re-sorts only after Refresh; a record that leaves the open view (Archive) closes itself.
- An unsubmitted Create Record form is kept as a local draft and offered back ("Restored to the last interrupted
  content"); clear it before a clean test.
