# HAP and hap-cli traps found since 0.8.31

**Status: draft, 24 Nov 2026.** `BUILDING.md` lists the traps verified in September on hap-cli 0.8.31. These were
found in November on 0.9.x while building the Odoo Replica (AI) app, on the same Nocoly SaaS organisation. Each "P"
number has steps, expected and actual results in that programme's `PLATFORM-ISSUES.md` (public copy on branch
`claude/odoo-native-replica`, folder `nocoly/native-replica/`; P1–P47, in English since 25 Nov). Most of them are
silent: the build, the publish and the run all report success.

## Workflows

| Trap | What to do |
|---|---|
| **P41.** A *get single record* step whose filter has OR groups ignores the whole filter when the groups sit in the old `conditions` slot, which is where the CLI writes them. It returns the first record by its sort | Store each OR group as `filters = [{"spliceType": 2, "conditions": [group]}]` with `conditions = []`, as the editor's "use and/or filters" switch does. One-group filters work in either slot |
| **"Equals" on a multi-record relation** compares the whole set: a record linked to two teams does not "equal" either | Use **is any of** (`33`) for "includes this record"; `9` / `10` are whole-set equals / not equals |
| **P42.** Date-difference units: the product numbers Year 1, Month 2, Day 3, Hour 4, Minute 5, Second 6; the CLI's `out_unit` names map differently, so "hour" is saved as Month and gives 0 | Set `outUnit` raw. A difference in hours is whole hours: for a duration use minutes / 60 |
| **P33.** A query whose dynamic filter value is empty fails the whole run (the run log says the filter value is empty) | Put the query behind a branch or a trigger condition that checks the value first |
| **P25.** A function calculation made by the CLI has 0 decimals, so numeric results are rounded | Set the decimals on the step, or read the result as text (`string_fx_id`) |
| **P29.** A formula error gives an empty result and the run still shows success | Test each formula on a record and read the result in `approval history-detail` |
| **P21.** A date calculation's result is referenced as `string_fx_id`; the server uses `date_fx_id`, so later conditions break | Reference `date_fx_id` |
| **P22.** "Is (not) empty" on a relation cannot be written by the CLI | Patch the condition raw: `conditionId` 31 (not empty) / 32 (empty), `filedTypeId` 29 |
| **P27.** Clearing a field (`op: clear`) is dropped or refused | Write the stored form with `isClear` |
| **P23.** `batch-add` drops the names of branch paths that have a condition | Rename the paths after the batch |
| A whole-step `node save` clears every setting it does not name | Send all of the step's own keys back (for a query: actionId, appId, conditions, filters, sorts, executeType, …) |
| A function step's result is read as `string_fx_id`, even into a number field; `number_fx_id` is refused at publish | Use `string_fx_id` |
| **Business rules apply inside a button's fill-in dialog.** A "show only when archived" rule emptied a Lost dialog on active records | Keep dialog fields free of visibility rules |
| `approval history-detail <run id>` shows each step's result in `sourceId` | Use it to test flows without a UI |

## Fields and records

| Trap | What to do |
|---|---|
| **P10.** `field.add` can time out after the field was created | Re-read the worksheet before retrying |
| **P39.** An option added by `field.update` without a key is saved with an empty key | Give every new option a key (a UUID) |
| **P35.** An option text that is not in the list is stored by `record update` as a dangling key | Add options in the form or by `field.update` first |
| **P40.** The CLI's range check on a relation ignores an "is empty" group of the selection limit and refuses values the form offers | Write with `--ignore-rules`, as a workflow does |
| **P34.** `record create` is refused by a hide rule over a hidden field that has a default value | `--ignore-rules` for test data |
| `record create --no-workflow` is refused when the worksheet has a create-triggered workflow | Expect the workflow to run, or use a test record |
| List reads can lag single-record reads, and can miss hidden fields (P20) | Read one record with `record get` before deciding a write failed (`CLAUDE.md`, *Reading records*) |

## Roles, buttons and views

| Trap | What to do |
|---|---|
| **P31.** `role set-permissions --permission-way` turns every app-wide switch off | Read `globalPermissions` back after any level change |
| **P36.** `role set-permissions -P` reports success and saves no per-sheet rule | Create roles with the V3 call `POST /v3/app/roles` including `globalPermissions` |
| **P37.** `role create-fine` creates the role with every app-wide switch off | As above |
| **P43.** The role editor shows roles created through V3 as view / edit / delete **All**, though their stored rights are narrower; saving there would likely widen them | Do not save such roles in the editor. Change them with V3 `PATCH /v3/app/roles/{id}` and the role's complete body from `GET` (PUT gives 405; a partial PATCH is refused), then compare every key |
| A role created without its custom pages in `pagePermissions` cannot see them | List the pages when creating the role |
| Role Debug changes the account's API rights, not only the screen | Switch it off before running scripts |
| **P38.** A *create related record* button made by the CLI is saved with no target and does nothing | Finish it in the button editor ("In the current record", "Always"), then press it |
| A list view's order is `moreSort` (`[{controlId, isAsc}]`); `sortCid` / `sortType` alone do not change it | Write `moreSort`; `sortType` 1 = descending, 2 = ascending |
| A board's column order is the view's `advancedSetting.navsorts` | Set it to the related worksheet's sequence field |
