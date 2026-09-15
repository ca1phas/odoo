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
- A new two-way Relation's reverse control comes back at row 9999, width 0, with no alias. Place it in a second save.
- `hap worksheet update-fields` replaces the whole control set. Use it only on a worksheet with no records, or send
  back the full list you just read; add fields to a live worksheet with `add-fields`.
- The Phone control validates numbers (libphonenumber): an unallocated number such as 03-1234 5678, or a placeholder
  like "NA", is refused.

### Views

- `view create/update --view-spec` ignores sort. Set `sortCid`, `sortType` (2 = ascending) and `moreSort` with
  `view update --view-json … --edit-attrs sortCid,sortType,moreSort`.
- `--view-spec` `tableFields` sets only `displayControls`, and the table then shows every field. A table's columns are
  `showControls` plus `advancedSetting.customShowControls`:
  `view update --view-json '{"showControls":[…],"advancedSetting":{"customdisplay":"1","customShowControls":"[…]"}}'
  --edit-attrs showControls,advancedSetting --edit-ad-keys customdisplay,customShowControls`.

### Rules

- Rule item types: 1 show · 2 hide · 4 read-only · 5 required · 6 error message · 7 whole record read-only.
  Filter operators: 2 equals · 6 not equals · 7 empty · 8 not empty.
- A validation rule with `--check-type 1` is enforced on API writes too.
- The CLI cannot delete a rule. Disable it (`save-rule --rule-id … --disabled`) and delete it in the UI: worksheet
  ⋯ › Set Worksheet › Business Rules › hover the rule › trash icon.

### Buttons

- `hap worksheet create-custom-action --action-spec` **ignores `--btn-id`**: every run adds another button. Look the
  button up by name with `hap worksheet custom-actions <ws>` first.
- A button that runs a workflow gets a hidden workflow; while it has no steps, its trigger's `nextId` is `99`.
  Deleting the button deletes that workflow too.
- A button's condition greys it out when unmet; it does not hide it.

### Workflows

- `workflow node batch-add` names worksheet triggers in Chinese ("工作表事件触发") and drops branch-path names:
  rename them with `workflow node rename`, then republish.
- A get-records node's filter must be written as the UI stores it —
  `filters: [{spliceType: 2, conditions: [[{nodeId: <that node>, filedId, filedTypeId, conditionId: "9",
  conditionValues: [{value: {key, value}}]}]]}]` — with `workflow node save --type 13`. `--nodes` sends
  `operateCondition` instead, which the UI does not use.
- `workflow node get` returns a branch path's conditions as `conditions`; `workflow node save --type 2` expects
  `operateCondition`.
- To add steps to an existing workflow, `batch-add` with `--trigger-node-id <last node in the chain>` and
  `{"nodeId": …}` references (aliases exist only within one call). Change a trigger's fields or condition with
  `workflow node save --type 0 -c '{appId, appType: 1, triggerId, assignFieldIds, operateCondition, returns: []}'`.
- Give a worksheet-event trigger a condition when most records cannot need the run — every run counts against the
  organisation's workflow quota.

### Records

- `hap worksheet record delete` needs the rowId UUID; given `_id` it reports success and deletes nothing.
- Value formats differ by field type and a wrong one is accepted silently — see `hap guide record` before writing.

### In the UI

- An open record can keep a *Modifying form data — Cancel / Save* bar after a relation or member change that is
  already stored; Save clears it.
- A dropdown opens reliably by typing into it; clicking the arrow sometimes does nothing.
- An unsubmitted Create Record form is kept as a local draft and offered back ("Restored to the last interrupted
  content"); clear it before a clean test.
