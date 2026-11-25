# Platform issues found while building (for product tickets)

Started 23 Nov 2026 at the Module Owner's request: every difference between the CLI/MCP and the UI, and anything that behaves like a bug, is recorded so it can be raised with the product team. Platform: Nocoly SaaS (www.nocoly.com), organisation on Professional, hap-cli 0.9.14, test app "Odoo Replica (AI)".

**How to use:**
- Each "P" item gives the context, the steps, the expected and actual result, the impact and, where one was found, the workaround used. The tickets themselves are written in Simplified Chinese, the product team's format, and are kept outside this repository; the facts are the same.
- "D" items are documentation errors, with sources.
- Status: **Open** = not filed. The Module Owner decides what to file and the Platform Liaison files it (roles: `HANDOVER.md` §2); nothing is submitted without approval.

| # | Area | Kind | Severity | Status |
|---|---|---|---|---|
| P1 | Unique index error message | Wrong ids in the message | Low | Open |
| P2 | Region field, CLI create | Hidden default differs from the UI | Low | Open |
| P3 | Region value through the API | Language does not follow the user | Medium | Open |
| P4 | Region field type numbers | CLI type table and server disagree | Low | Open |
| P5 | Multi-relation display fields | Created with no visible columns | Medium | Open |
| P6 | Multi-relation cells in record list / get | Truncated to 5 rows without notice; shapes differ | Medium | Open |
| P7 | Option set with no options | Refused with an empty error | Low | Open |
| P8 | Role create with per-sheet scope on an empty app | Refused with an empty error | Low | Open |
| P9 | CLI options | Inconsistent between commands | Low | Open |
| P10 | `field.add` timeout | Reports failure, but the field is created | Medium | Open (known since 20 Nov) |
| P11 | Amount in words (Uppercase) | Preview differs from the stored value | Low | Open |
| P12 | Field type numbers vs CLI names | Several mismatches | Low | Open |
| P13 | Subform reverse field | Not listed by `worksheet fields` | Low | Open |
| P14 | Landline field | Stores Hong Kong keys the panel never shows | Low | Open |
| P15 | Option colours | Saved while the colour switch is off | Low | Open |
| P16 | Single-select → Progress bar | Silently turns off "allow adding options" | Medium | Open |
| P17 | Self-relation through add-fields | Two-way flag set, but no reverse field created | Medium | Open |
| P18 | Foreign field of a Region field, record get | Returned as a JSON string, the source as an object | Low | Open |
| P19 | Foreign field of a Phone field, record form | Shows the raw stored number, not the formatted one | Low | Open |
| P20 | Hidden fields in `record list` | Returned empty; `record get` returns the values | Medium | Open |
| P21 | CLI workflow DSL, date calculation result | Referenced as string_fx_id; the server uses date_fx_id, so conditions break | Medium | Open |
| P22 | CLI workflow DSL, relation conditions | "Is not empty" cannot be written; raw ids refused | Medium | Open |
| P23 | CLI batch-add, branch paths | A path with a condition loses its name | Low | Open |
| P24 | Region value in workflow functions | Returned as a Chinese path, not the code or the user's language | Medium | Open |
| P25 | CLI workflow DSL, function calculation | Created with 0 decimals: numeric results are rounded to integers | High | Open |
| P26 | Unique index and the recycle bin | A deleted record still blocks its unique values | Medium | Open |
| P27 | CLI workflow DSL, clearing a field | "op: clear" is dropped or refused; the stored form needs isClear | Medium | Open |
| P28 | CLI workflow DSL, rollup of a fetched set | aggregate "sum" is not kept; the node only counts | Medium | Open |
| P29 | Workflow function calculation | A formula error gives an empty result; the run shows success | High | Open |
| P30 | Workflow publish | A step that reads a node inside a branch is refused with an unspecific message | Low | Open |
| P31 | CLI role set-permissions | Changing the level turns every app-wide switch off | High | Open |
| P32 | CLI workflow DSL, fill-in node | A wrongly shaped form-field list gives HTTP 500 instead of a message | Low | Open |
| P33 | Workflow query node | An empty dynamic filter value fails the whole run; build and publish give no warning | Medium | Open |
| P34 | CLI record create | Refused by a "hide" rule because a hidden field has a default value; the same record saves in the UI | Low | Open |
| P35 | CLI record update, option fields | An option text that is not in the list is stored as a dangling key; the form shows an empty tag | Medium | Open |
| P36 | CLI role set-permissions -P | Per-sheet rules are not saved, the command reports success | High | Open |
| P37 | CLI role create-fine | The role is created with every app-wide switch off; a sheet with read scope 0 falls back to "own, everything allowed" | High | Open |
| P38 | CLI create-custom-action, createRelatedRecord | The button shows but does nothing: target saved as "related record" with no relation, and no "Active Button" choice | High | Open |
| P39 | CLI app-editor field.update, option fields | An option added without a key is saved with an empty key; picking it stores nothing | Medium | Open |
| P40 | CLI record create / update, relation range check | The pre-check ignores an "is empty" group of a relation's selection limit and refuses values the form offers | Medium | Open |
| P41 | Workflow query step (get single record), OR filter groups | Written by the CLI in the old condition slot: the editor shows the OR groups, but the run ignores the whole filter and returns the first record by the sort | High | Open |
| P42 | CLI workflow DSL, date difference | `out_unit` numbers differ from the product: "hour" is stored as Month, so the result is 0 | Medium | Open |
| P43 | Role editor, roles created through V3 | The editor shows the per-sheet rights as view / edit / delete **All** where the stored role (API readback, Role Debug) is read-only; saving there would likely write what it shows | High | Open |
| P44 | CLI worksheet create --fields, form layout | The fields' row / column / size are ignored: one field per row | Medium | Open |
| P45 | New sheet with its default fields replaced | The "All" view still lists the deleted default fields and looks empty | Low | Open |
| P46 | CLI view update --view-spec, table view | `tableFields` has no effect; the command reports success | Medium | Open |
| P47 | CLI app create --sections | An extra empty group with no name ("Unnamed Group") | Low | Open |
| D1–D12 | Help docs | Conflicts and outdated content | — | Open |

---

### P1 The id in the unique-index error message is not the conflicting record

- **Context:** the Builder of the Odoo replica, 23 Nov 2026, on the test app in Nocoly SaaS, writing a duplicate value through hap-cli to test a unique index.
- **Steps:**
  1. Create a unique index on the Country Code field of Countries (form settings › Retrieval acceleration › New index › Unique index).
  2. Add a record with Country Code = MY (MY exists already) with `hap worksheet record create`.
- **Expected:** refused, naming the conflicting field and the existing record.
- **Actual:** correctly refused (resultCode 11), but the message says "another record already has them: <id>". That id is the Country Code **field's** id, not the existing record's. A composite index lists two field ids.
- **Impact:** misleading when tracing duplicates: it looks like a record id.
- **Evidence:** `00-foundation-build/BUILD-LOG.md` (23 Nov, unique index test).

### P2 A Region field created by the CLI with the "International" scope gets chooserange = "CN" from the server

- **Context:** 23 Nov 2026, a Region field (type 24, enumDefault 1 = International, enumDefault2 1 = Country) created with `worksheet create --fields`.
- **Steps:**
  1. Create the field with the CLI.
  2. Read it back with `hap worksheet fields --raw`.
- **Expected:** the same as an "International" field saved in the UI: `chooserange: ""`.
- **Actual:** it reads back as `chooserange: "CN"`. A field saved as "International" in the UI has `""`.
- **Impact:** the same setting is stored differently depending on how it was made. The UI shows it correctly for now, but whether it behaves the same is unknown; it has to be cleared by hand.
- **Evidence:** BUILD-LOG (Region field of Countries).

### P3 Region paths read through the API do not follow the user's language

- **Context:** 23 Nov 2026, reading the Region field of Countries records.
- **Steps:**
  1. The account's UI language is English.
  2. Open a record: the region shows "Malaysia".
  3. Read the same field with `hap worksheet record list`.
- **Expected:** the path in the user's language (Malaysia).
- **Actual:** the API returns `{"code":"MY","path":"<Malaysia in Simplified Chinese>"}`. In the field survey the same day, the CLI also returned state and district paths in Simplified Chinese while the UI showed English.
- **Impact:** reports, printed text and interfaces made through the API or MCP show place names in the wrong language, which is very visible for customers outside China (Malaysia).

### P4 Region field type numbers do not match the CLI type table

- **Context:** 23 Nov 2026, a Region field created with `worksheet add-fields` as type 19 (province).
- **Steps:**
  1. Add a Region field of type 19 with add-fields.
  2. Read it back.
- **Expected:** type 19, or the CLI saying that only 24 with a level is used.
- **Actual:** stored as type 24 with enumDefault2 = 1. `hap worksheet field-types` still lists 19/23/24.
- **Impact:** scripts written from the docs or the CLI table fail their readback comparison.

### P5 Multi-record relations created by the CLI have no display fields; the tab table shows "No visible fields"

- **Context:** 23 Nov 2026, a two-way multi-record relation (Country Groups › Countries, displayMode tabTable, no showFields) created with `worksheet create --fields`.
- **Steps:**
  1. Create the field with the CLI.
  2. Open a Country Group record.
- **Expected:** as with a relation made in the UI, the first few fields of the target sheet are shown by default.
- **Actual:** showControls = []; the tab shows 27 rows, each reading "No visible fields". The reverse field the system generates gets two display fields by default.
- **Impact:** users see rows but cannot tell which records they are. showControls has to be set afterwards with field.update.

### P6 `record list` returns only the first 5 linked records of a multi-record relation, in a different shape from `record get`

- **Context:** 23 Nov 2026, reading back Country Groups (the European Union has 27 countries).
- **Steps:**
  1. Read the multi-record relation with `hap worksheet record list`.
  2. Read the same record with `hap worksheet record get`.
- **Expected:** the full list, or a total and a truncation flag; the same shape from both commands.
- **Actual:** list returns 5 linked records with no notice; get returns an integer (27), not a list.
- **Impact:** checks mistake it for missing imports. We briefly believed each group had stored only 5 countries.

### P7 Creating an empty option set is refused with an empty error

- **Context:** 23 Nov 2026, `hap app optionset create --options-json '[]'`.
- **Expected:** an empty option set is allowed, or the message says that at least one option is needed.
- **Actual:** "The server refused the request (error None)".
- **Impact:** the cause is found only by trial and error.

### P8 Creating a role with per-sheet rights on an app with no sheets is refused with an empty error

- **Context:** 23 Nov 2026, `hap app role create --type 0 --permission-scope 0` on an app with no worksheets yet.
- **Expected:** a role with no rights is created, or the reason is given.
- **Actual:** "The server refused the request (error None)". It worked with permission-scope 20.
- **Impact:** setting up the roles of a new app gets stuck.

### P9 CLI options differ between commands

- **Context:** 23 Nov 2026, hap-cli 0.9.14.
- **Problem:**
  - `worksheet create --fields` does not take `@file` ("not valid JSON"), while `worksheet update-fields --fields @file` does.
  - `worksheet add-fields` has no `-a/--app-id`; every other worksheet command has it.
- **Impact:** scripts need a different option form for each command, and long field lists hit the command-line length limit.
- Added 23 Nov 2026: `record create` takes `--no-workflow` but `record update` refuses it ("Workflows cannot be suppressed for this write"); an ordinary update of a hidden field is refused and needs `--ignore-rules`.

### P10 field.add reports a timeout, but the field is created

- **Context:** first recorded on 20 Nov 2026 (another demo app); again on 23 Nov 2026 in the field survey, where it produced a duplicate Phone field.
- **Actual:** "Read timed out (read timeout=30)"; the CLI stops, but the field exists.
- **Impact:** retrying as the message suggests creates duplicate fields.

### P11 Amount in words: the form preview differs from the stored value

- **Context:** 23 Nov 2026, field survey (Uppercase field, English).
- **Actual:** the preview shows "TWO HUNDRED THIRTY FOUR"; once saved it is "TWO HUNDRED AND THIRTY-FOUR".
- **Impact:** printed amounts in words differ from the screen.

### P12 Field type numbers do not match the CLI names

- **Stored number → CLI name:**
  - API query (button mode) is stored as 49, the CLI calls it Button;
  - tab is stored as 52, the CLI calls it Section;
  - divider is stored as 22, the CLI calls it Divider;
  - free link 21 is called DynamicLink;
  - custom fields are stored as type 2 + customtype, while the CLI lists 54;
  - a single select is stored as 11 whatever its display, while the CLI also lists 9.
- **Impact:** fields generated or compared from the CLI table come out wrong.

### P13 A subtable's reverse field is not listed by `worksheet fields`

- **Impact:** a read-modify-write script can miss it, or overwrite it.

### P14 The landline field stores Hong Kong settings the UI never shows

- **Actual:** the raw type 4 field holds `commcountries` / `defaultarea` (Hong Kong), but the settings panel shows no such options.

### P15 Option colours are still saved after "option colours" is switched off

- **Impact:** switching it back on brings the old colours back, which looks accidental.

### P16 Switching a single select to the "progress bar" display silently turns off "allow users to add options"

- **Actual:** `allowadd` goes from 1 to 0 with no notice.
- **Impact:** users suddenly cannot add options.

### P17 A two-way relation to the same sheet made with add-fields gets no reverse field

- **Context:** 23 Nov 2026, a relation field added to Contacts with `hap worksheet add-fields`: dataSource = the same sheet, advancedSetting.bidirectional = "1".
- **Steps:**
  1. Add a "Related Company" field that way.
  2. Read the field list back.
- **Expected:** as with a same-sheet relation made in the UI, the multi-record field on the other side is generated.
- **Actual:** the field is flagged bidirectional 1 and a sourceControlId is reserved, but the sheet has no reverse field. It appears only after `hap worksheet pair-relation`.
- **Impact:** the script believes the relation is two-way while it is one-way. The list of a company's contacts is missing, and the UI gives no clue why.

### P18 A foreign field showing a Region field returns a JSON string in record get; the source field returns an object

- **Context:** the Builder of the Odoo replica, 23 Nov 2026, added a foreign field (type 30, display only, strDefault "10") on Companies showing the contact's Region field, then read records back with hap-cli.
- **Steps:**
  1. The linked record's Region value is `MY|MY-10`.
  2. Read the record that shows it with `hap worksheet record get`.
  3. Read a record with a Region field of its own, for comparison.
- **Expected:** both in the same shape, a `{"code": ..., "path": ...}` object.
- **Actual:** the foreign field returns the string `"{\n  \"code\": \"MY|MY-10\",\n  \"path\": \"<Malaysia/Selangor in Simplified Chinese>\"\n}"` (with line breaks); the Region field itself returns the object `{"code": "MY|MY-14", "path": "<Malaysia/Kuala Lumpur in Simplified Chinese>"}`.
- **Impact:** integrations and scripts need two parsers for the same kind of value.
- **Evidence:** BUILD-LOG (23 Nov, test records of Companies and Bank Accounts).

### P19 A foreign field showing a Phone field shows the unformatted number on the form

- **Context:** 23 Nov 2026, a display-only foreign field on Companies showing the contact's phone (mobile type, Malaysia by default).
- **Steps:**
  1. The contact's phone is 012-345 6789; the contact form shows "+60 012 345 6789".
  2. Open the Companies record that refers to the contact.
- **Expected:** the foreign field is formatted like the source field.
- **Actual:** it shows the stored value "+60123456789", with no separate country code and no number format.
- **Impact:** the same number looks different on two sheets, and users think the data disagree.
- **Evidence:** a check of the screen in Chrome (23 Nov, TEST Company).

### P20 Hidden fields read as empty in record list; only record get has the values

- **Context:** the Builder of the Odoo replica, 23 Nov 2026, hidden helper fields (fieldPermission "011") on Product Categories, written and read back with hap-cli.
- **Steps:**
  1. Write the hidden text field (Ancestor Key 1) with `hap worksheet record update ... --ignore-rules`.
  2. Read it with `hap worksheet record list --fields x_product__ancestor_1`.
  3. Read the same record with `hap worksheet record get`.
- **Expected:** both reads return the same value (the reader is an app administrator).
- **Actual:** list returns an empty string "" for all 7 records; get returns the correct record id. Nothing says that the field was left out because it is hidden.
- **Impact:** integrations and scripts that check or export through the list call believe the data is missing, or overwrite real data with empty values.
- **Evidence:** BUILD-LOG (23 Nov, Units and Product Categories).

### P21 CLI workflow DSL: a date calculation's result is referenced as string_fx_id; the UI and the server use date_fx_id

- **Context:** the Builder of the Odoo replica, 23 Nov 2026, built the "activity state" workflow with `hap workflow node batch-add`: a date calculation step (now + 0d, date output), and branch conditions comparing "due date before / equal to the result".
- **Steps:**
  1. In the batch-add branch condition, reference the calculation's result as `{"kind":"field","node":"today","fieldId":"string_fx_id"}` (hap-cli 0.9.14's self-check and docs say that text and date results use string_fx_id, and there is no date_fx_id).
  2. Publish.
- **Expected:** the condition references the result, and the flow publishes.
- **Actual:** publishing is refused ("step(s) have no valid operation, or its content is wrong"), and the UI shows the condition value as "Today-Field Deleted". Picked again in the UI, the reference reads back as `controlId: "date_fx_id"`; with date_fx_id the flow publishes and runs correctly.
- **Impact:** every date comparison built through the CLI or MCP fails to publish, with an error that does not show why.
- **Evidence:** BUILD-LOG (23 Nov, workflow #14); flow "Activities - State on save".

### P22 The CLI workflow DSL cannot write "relation field is not empty"

- **Context:** 23 Nov 2026, the contact sync flow built with batch-add, with the branch condition "Parent company is not empty".
- **Steps:**
  1. Write the condition as `{"node":"trigger","field":"<relation field>","op":"not_empty"}`.
  2. Write the raw condition number instead, `"op":"31"`.
- **Expected:** "is empty / is not empty" can be chosen, as in the UI.
- **Actual:** step 1 is refused ("A relation column has no 'not_empty' comparison. It takes: all_contains, eq, ne"), and so is step 2 ("'31' is not a comparison this filter understands"). The CLI maps not_empty to condition 7, while "is not empty" on a relation is 31 ("is empty" is 32). The only way is to build with a placeholder condition and then write the stored form (conditionId 31) with `node save`; the UI then shows "Related Company is not empty".
- **Impact:** whether a relation is empty is one of the most common checks, and it cannot be built through the CLI or MCP.

### P23 batch-add branches: paths with a condition lose their names

- **Actual:** only the default path, without a condition, keeps its `name`; paths with a condition have an empty name and the UI shows "Branch". `node rename` puts the names back.
- **Impact:** the flow chart is hard to read, and the paths cannot be told apart when maintaining it.

### P24 A Region field read in a workflow function gives a Simplified Chinese path

- **Context:** 23 Nov 2026, a calculation step reading the contact's Region (value MY|MY-10) with `CONCAT("[", Region, "]")` and `LEFT(Region, 2)` into a text field.
- **Expected:** the region code (MY|MY-10), or at least the path in the user's UI language (English).
- **Actual:** the result is the Chinese path in brackets, and its first two Chinese characters.
- **Impact:** a workflow cannot get the country code from a region, nor write address text for users who do not read Chinese. The only way is a query condition "Countries.Region contains Contact.Region" (tested, works). Same cause as P3.

### P25 Function calculation steps made by the CLI default to 0 decimals, so numeric results are rounded

- **Context:** the Builder of the Odoo replica, 23 Nov 2026, calculation steps built with batch-add (function mode, number output), for example the inverse rate `1 / Rate`.
- **Steps:**
  1. Build a function calculation step with `output_type: number`.
  2. Run it, writing the result to a number field with 6 decimals.
- **Expected:** 1 / 0.204553 = 4.888709.
- **Actual:** 5.000000 is written. The step's settings read back `"number": 0` (decimal places). The DSL has no option for decimals, and the UI's default is unclear; after `node save` with `"number": 6` the result is right.
- **Impact:** unit conversions (1/12, 0.016667), exchange rates and price calculations are all rounded silently, so amounts are wrong with no warning. High risk.
- **Evidence:** BUILD-LOG (23 Nov, workflow #13); flow "Settings - Current rate on change".

### P26 Unique index: a deleted record (in the recycle bin) still holds its unique values

- **Context:** 23 Nov 2026, the rates sheet has a unique index (date + currency). A TEST rate for SGD on 2026-11-23 was created and deleted (into the recycle bin), then a rate with the same date and currency was created.
- **Expected:** after the deletion it can be created again.
- **Actual:** refused (resultCode 11, "values must be unique and another record already has them"), while `record list` no longer shows the record.
- **Impact:** a user who deletes a wrong record cannot recreate it without deleting it for good from the recycle bin, and the message does not say that the conflict is in the recycle bin.

### P27 CLI workflow DSL: "clear the field" writes are dropped or refused

- **Context:** 23 Nov 2026, an "update record" step built with batch-add, with the field write `{"fieldId": ..., "op": "clear"}` (or `{"kind": "empty"}`, as the guide writes it).
- **Actual:**
  1. When it is the step's only write, the CLI reports "The step was saved but none of its 1 field write(s) were kept", and the whole batch is rolled back.
  2. Together with other writes, the clear is silently dropped and the other fields are saved. This is how the contact flow's "clear the company name" was lost.
  3. `save-action` with the expanded form `{"fieldValue": "", "isClear": true}` gives the same error.
- **For comparison:** a "clear" set in the UI reads back as `{"type": 2, "fieldValue": "", "isClear": true, "addType": 0}`. Written as is with `node save`, it publishes and runs. The fields of the "calibrate single record" step use the same form (isClear true).
- **Impact:** flows built through the CLI or MCP cannot clear a field, and with mixed writes there is no error.

### P28 CLI workflow DSL: a sum over a "get multiple records" result is saved as a count

- **Context:** 23 Nov 2026, a rollup step built with batch-add: `data_source` a get-multiple step, `aggregate: "sum"`, `field: <extra price field>`.
- **Actual:** the step reads back with no field and no aggregation, and the UI shows "Total count of the multiple data objects obtained". The run gives the number of records (2), not the sum of the extra prices.
- **Impact:** prices go wrong silently (every variant's sales price was 2 too high). In the UI this step can only count, but the CLI accepts the sum option without an error.

### P29 Workflow function calculation: a formula error gives an empty result, and the run shows success

- **Context:** 24 Nov 2026, the price calculation step in the PBP.
- **Steps:**
  1. Write `IF(<option field>="Cost", 1, 2)` (a single equals sign), use `STRING()` on an empty option field, or subtract an empty number.
  2. Run the flow.
- **Expected:** the step fails with the reason when the formula is wrong, or the editor warns when it is saved.
- **Actual:** the step shows success and the result is an empty string; the next steps get an empty value and the final price is empty. The cause was found only by writing each part of the formula into the record one by one (equality is `==`; options must be turned into text).
- **Impact:** amount calculations go wrong silently, and tracing them is expensive.

### P30 Publishing refuses a step that reads a step inside a branch, with an unspecific message

- **Actual:** a calculation step after a branch read a step inside one of its paths (the result of a PBP call); publishing gave "step(s) have no valid operation, or its content is wrong", without saying that it is a reference across branches.
- **Impact:** with a "calculate inside the branch, combine after it" design, it is hard to find out why the flow does not publish.

### P31 hap-cli `app role set-permissions --permission-way` turns off every app-wide switch of the role

- **Context:** 24 Nov 2026, the role "Master Data Manager" changed from "view all" (20) to "manage all records" (80).
- **Steps:** `hap app role set-permissions <appId> <roleId> --permission-way 80`, then read back with `app role permissions`.
- **Expected:** only the record scope changes; everything else stays.
- **Actual:** the scope becomes 80, but every globalPermissions switch becomes false: add records, import, export, discussion, print, attachment download, logs. The CLI has no option to set these switches on their own, so the only way is to delete the role and recreate it with `create --global-permissions-json`.
- **Impact:** the role's members suddenly cannot add records or export, while the command reports success. High risk (a role with members cannot simply be recreated).

### P32 CLI workflow DSL: a wrongly shaped field-permission list in a fill-in step gives HTTP 500

- **Actual:** with `formProperties` written as an object `{<field>: "readonly"}`, the server answers "Internal Server Error" and the CLI rolls the batch back; the correct shape is a list, `[{"id": <field>, "permission": "readonly"}]`.
- **Impact:** the error does not show the cause; the shape was found only in the CLI's source.

### P33 Workflow "query worksheet" step: an empty dynamic filter value fails the whole run

- **Context:** 24 Nov 2026 00:48, during acceptance tests, two contacts (companies) were created with no Region.
- **Steps:**
  1. In a worksheet-event flow (contact added or updated), add a "get single record / query worksheet" step on Countries, filtered by "Countries.Region contains the trigger record's Region" (a dynamic value).
  2. After it, add an "update record" step (display name and so on).
  3. Create a contact with an empty Region.
- **Expected:** a configurable way to handle an empty dynamic value (for example treated as "no data found", following the step's "continue when no data is found" setting), or at least a warning when building or publishing.
- **Actual:** the run fails with the reason "the filter value is empty: Region" (shown in Chinese), and none of the later steps run. Building and publishing both report success with no warning; setting the step to "continue when no data is found" makes no difference.
- **Impact:** a single record without an optional field stops the whole flow halfway, and the record's other automatic fields (here the display name and the commercial entity) are never written. The only way round is a separate flow with the trigger condition "Region is not empty".
- **Workaround (used):** the country query moved to its own flow, "Contacts - Country from Region", triggered only when Region is not empty.

### P34 hap-cli `record create` is refused by a "hide" business rule because a hidden field has a default value

- **Context:** 24 Nov 2026 00:47, a contact of type company created with the CLI, writing only the name, the type and Active.
- **Steps:**
  1. The Contacts sheet has the business rule "Company: hide person fields": when the type is company, Address Type is hidden (that field has the default value Contact).
  2. `hap worksheet record create <Contacts sheet> --fields-json '[{"id":"name",...},{"id":"company_type","value":"<Company>"}]'`.
- **Expected:** as in the UI, the record is saved (a company created in the UI stores the hidden field's default as usual).
- **Actual:** RuleBlocked: "Company: hide person fields" makes Address Type hidden on this record, so it cannot be written. The request did not write Address Type; the default value was counted as a write.
- **Impact:** scripts must add `--ignore-rules`, which also skips every other rule check.

### P35 hap-cli `record update`: writing an option text that does not exist stores a dangling key

- **Context:** 24 Nov 2026 01:15, the "new tag" acceptance test: a new tag written with the CLI to a TEST contact's Tags (multi-select, option set Contact Tags, users may add options).
- **Steps:** `hap worksheet record update <Contacts sheet> <record> --fields-json '[{"id":"category_id","value":["TEST Tag"]}]'`, then read back with `record get` and open the record in the UI.
- **Expected:** as in the UI: when the field allows new options, the new option is added to the option set (with a colour) and written to the record; otherwise an error.
- **Actual:** the command succeeds and the record stores `{"key": "TEST Tag", "value": null}`; the option set gets no new option; the UI shows an empty blue tag. Typing the same new tag in the UI adds it properly (colour #1677ff).
- **Impact:** new tags written by imports or integrations become invisible junk data, and filters and counts do not add up.

### P36 hap-cli `app role set-permissions --permission-way 0 -P`: per-sheet rights are not saved, and the command reports success

- **Context:** 24 Nov 2026 01:20, the Employee role changed from "view all + manage own" to per-sheet rights (master data read-only; activities: own only).
- **Steps:**
  1. `hap app role set-permissions <appId> <roleId> --permission-way 0 -P '<per-sheet rules JSON>'`. Both the V3 shape that `app role permissions` reads (id / recordDataScope) and the older `sheets` shape that the CLI source actually sends (sheetId / readLevel / editLevel / removeLevel / canAdd) were tried.
  2. Read back with `app role permissions` and GetRoleDetail.
- **Expected:** each sheet's scope is saved as given.
- **Actual:** both shapes return success (EditAppRole returns 1), but every sheet keeps its old scope (20/20/20); only the overall "custom" switch takes effect, so the role ends up seeing only its own records on every sheet. Also, `-P` does not take `@file`, and the full rules exceed the Windows command-line length.
- **Impact:** adjusting an existing role's per-sheet rights through the CLI breaks the role, invisibly. High risk (a role with members affects them at once).
- **Workaround (used):** set it back to 50 first; create new roles through V3 (see P37) and keep the old role, renamed.

### P37 hap-cli `app role create-fine`: the new role has every app-wide switch off; a sheet with read scope 0 falls back to "own, everything allowed"

- **Context:** 24 Nov 2026 01:25, a per-sheet Employee role created with `create-fine`.
- **Steps:** `hap app role create-fine <appId> -n Employee --worksheet-permissions '[{"worksheetId":...,"recordDataScope":{"read":100,"edit":0,"delete":0},...}, {"worksheetId":<system sheet>,"recordDataScope":{"read":0,"edit":0,"delete":0}}]'`, then read back with `app role permissions`.
- **Expected:** as the help says, "items not given are allowed by default": the app-wide switches (add records, export, discussion, logs, print, attachment download) are on, and a sheet with read scope 0 has no rights.
- **Actual:** every globalPermissions switch is false (members cannot add any record); the two sheets with read scope 0 become 20/20/20, with add and import allowed. The V3 request that the CLI sends has no globalPermissions.
- **Impact:** the new role's members cannot add records, and the sheets meant to be hidden can be added to and imported into.
- **Workaround (used):** create the role through the same V3 endpoint with the 8 globalPermissions switches in the request; system sheets read-only.

### P38 hap-cli `create-custom-action` (createRelatedRecord): the button shows but does nothing when clicked

- **Context:** 24 Nov 2026 10:10, a UI test of the "Launch Plan" button on Contacts. The CLI created it at 00:22 with `hap worksheet create-custom-action <Contacts sheet> --action-spec '{"type":"createRelatedRecord","relationField":"<Plan Launches relation field>"}'`.
- **Steps:**
  1. Create a "create related record" button with that command.
  2. Open any contact and click the button.
  3. Open form settings › Custom actions and edit the button.
- **Expected:** a new Plan Launch form opens (a related record created from the current record).
- **Actual:** nothing happens, and there is no error. The button editor shows "At linked record 'Associated records have been deleted' Create Plan Launches", and neither "Always" nor "When conditions are met" is selected for when the button is available. The stored settings: writeObject 2 (related record), relationControl empty, showType 0. Changed in the editor to "current record" with "Always" (writeObject 1, showType 1), the dialog opens, and the flow runs after submitting.
- **Impact:** testing the flow with `workflow trigger` shows nothing wrong, but users cannot use the button; only a test in the UI finds it.
- **Workaround (used):** corrected in the button editor and saved. Another button, "Rebuild Variants" (runs at once, with a confirmation), also has showType 0 but works.

### P39 hap-cli `app-editor` field.update: an option added without a key is saved with an empty key

- **Context:** the Builder of the Odoo replica, 24 Nov 2026 13:50, used field.update through `app-editor apply` to add the option "Leads" to the single select "Applies to" of Activity Types and Activity Plans (the existing options kept their keys; the new one had none).
- **Steps:**
  1. Read the single-select field and append `{"value":"Leads","index":5,"isDeleted":false}` (no key) to its options.
  2. Write the whole options list back with field.update.
  3. Read the field back.
- **Expected:** the server gives the new option a key (as when an option is added in the UI), or refuses the save and says that the key is missing.
- **Actual:** saved; the new option reads back with an empty key ""; a record that picks it cannot store a valid value.
- **Impact:** options added through the CLI or MCP look fine but cannot be used; this shows only on readback, or when the option is picked in the UI.
- **Workaround (used):** generate a UUID as the key when adding an option (the script does now).

### P40 hap-cli record writes: the pre-check of a relation's selection limit ignores an "is empty" group and refuses valid values

- **Context:** the Builder of the Odoo replica, 24 Nov 2026 17:00, set a selection limit on the Stage relation of Leads / Opportunities: "the stage's Sales Teams include the record's Sales Team" or "the stage's Sales Teams are empty" (two groups, OR). Then a record's Stage was changed to Won (Won has no Sales Teams) with `hap worksheet record update`.
- **Steps:**
  1. Give the relation field the selection limit above (two OR groups).
  2. Write `hap worksheet record update <sheet> <record> --fields-json '[{"id":"stage_id","value":["<Won stage row id>"]}]'`.
- **Expected:** the write succeeds (Won is offered in the form's dropdown).
- **Actual:** the CLI refuses: "\"Stage\": <id> is outside what this field offers (and a condition on <Sales Teams> this version cannot compute was left out of the check …)". The pre-check evaluated only the first group and left the "is empty" group out, so a valid value was refused. With `--ignore-rules` it is written.
- **Impact:** once a selection limit has an "is empty" condition, ordinary CLI and script writes fail, and the check has to be bypassed.
- **Workaround (used):** the test scripts write with `--ignore-rules` (as a workflow writes); the form's dropdown was tested in the UI separately.

### P41 Workflow "get single record": with OR groups in the old condition slot, the whole filter is ignored at run time

- **Context:** the Builder of the Odoo replica, 24 Nov 2026 16:50–17:20, built 13 "get single record from worksheet" steps in 5 flows (the Won button on Leads, the new-lead defaults and others) with hap-cli 0.9.14's workflow DSL (`batch-add`, get_single, a filter of two OR groups).
- **Steps:**
  1. Build a "get single record" step on Stages, filtered by (Is Won Stage checked and Sequence > the previous step's Sequence and Sales Teams equals the trigger record's Sales Team) or (Is Won Stage checked and Sequence > the previous step's Sequence and Sales Teams is empty), sorted by Sequence ascending.
  2. The CLI stores the conditions in the old `conditions` slot (two groups), with `filters` empty. The editor shows both groups and the "or" correctly, with a notice that filters now support and/or combinations.
  3. Publish and run (button trigger, record in the Proposition stage).
- **Expected:** the Won stage (the only stage with Is Won Stage checked).
- **Actual:** the New stage (Is Won Stage not checked, Sequence condition not met), which is the first record by the sort: the whole filter was ignored. The run shows success, with no error. The same fault made "default stage of a new lead" return another team's stage. Steps of the same kind with one group run correctly.
- **Impact:** the flow silently takes the wrong record and writes business data from it; building, publishing and running give no warning.
- **Workaround (used):** in the editor, switch to the supported and/or combined filters and save (the conditions move to `filters`, each group with `spliceType` 2): the run is then correct. The script `crmwf.group_filters()` does the same conversion for every multi-group "get single record" step (13 steps converted and published).
- **Suggestion:** make the run match the editor (support the old multi-group conditions, or refuse or warn at publish); have the CLI write new steps straight into `filters`, as it already does for "get multiple records".

### P42 hap-cli workflow DSL: the date difference's `out_unit` numbers differ from the product; "hour" is stored as "month"

- **Context:** the Builder of the Odoo replica, 24 Nov 2026 17:20, built a "date/time difference" step with the DSL (`mode: date_diff`, `out_unit: "hour"`) for the hours from a meeting's start to its end.
- **Steps:**
  1. Build a date difference step with `out_unit: "hour"`, start = Start, end = End.
  2. Create a meeting from 10:00 to 11:30 (and another that spans 2 days).
  3. Open the step in the editor.
- **Expected:** output unit "hour"; results 1.5 (or 1) and 48.
- **Actual:** both results are 0. The editor shows the output unit as "month". The step stores `outUnit: 2`; the editor's dropdown order is year, month, day, hour, minute, second (1–6), while the CLI maps minute 1, hour 2, day 3, month 4, year 5, second 6, week 7. Only "day" (3) agrees.
- **Also seen (not judged a bug):** with "hour" output the result is in whole hours (48.5 hours gives 48).
- **Impact:** every date difference built through the CLI has the wrong unit except "day", and the result is silently 0 or wrong.
- **Workaround (used):** read all of the step's settings and write `outUnit` back with the product's numbers (`crmwf.save_compute`, `DATE_DIFF_UNITS`); the meeting duration is now counted in minutes and divided by 60, giving 1.50 / 48.00 (tested).

### P43 Role editor: for roles created through V3, the per-sheet rights show as view / edit / delete "All", unlike what is stored

- **Context:** the Builder of the Odoo replica, 24 Nov 2026 22:40, opened the Salesperson role under the app's Users › Roles (the role was created the same day with V3 `POST /v3/app/roles`, with per-sheet rights).
- **Steps:**
  1. Create the role through V3, with Countries, Contacts and other sheets set to: view all, edit 0 (Contacts 20, own), delete 0.
  2. Read back with `hap app role permissions` / V3 `GET /v3/app/roles/{id}`: as set. Enter the app as that role with Role Debug: Stages has no Add button and its records are read-only, and opportunities cannot be deleted; the behaviour matches what is stored.
  3. Open the role's edit page under Users › Roles.
- **Expected:** the edit page shows the stored rights (Countries read-only, Contacts edit own, no delete).
- **Actual:** on the edit page, the rows of Countries, Country Groups, Industries, Bank Accounts, Contacts, Units, Product Categories and others have view / edit / delete ticked and set to "All". Not saved (to avoid widening the rights); saving would presumably write what is shown.
- **Impact:** an administrator who changes anything in the editor (opening a page, for example) and saves may unknowingly turn a read-only role into one that can edit and delete all data.
- **Workaround (used):** these roles are never saved in the editor. Page rights went through V3 instead: `PUT /v3/app/roles/{id}` returns 405; `PATCH` with only `pagePermissions` returns "parameter invalid"; `PATCH` with the whole role (the GET result without its id) works, and a key-by-key comparison shows that no other right changed (`01-crm-build/step4_roles.py`, `grant_pages`).

The next four items come from a separate small demo app built on Nocoly SaaS on 24–25 Nov 2026 (hap-cli 0.9.14). It is not part of the Odoo programme.

### P44 hap-cli `worksheet create --fields`: the fields' `layout` (row / col / size) is ignored

- **Context:** the demo app's Builder, 24 Nov 2026 23:55, created a sheet with `hap worksheet create <APP> Devices --fields '[...]'`, each field with `"layout": {"row": r, "col": c, "size": s}` (for example, two fields of size 6 on one row).
- **Steps:**
  1. Create the sheet that way, with layouts on the fields.
  2. Read back with `hap worksheet fields <WS> --raw`, or open the form designer.
- **Expected:** the fields are placed in the rows, columns and widths given.
- **Actual:** the command succeeds, but every layout is ignored: text fields each take a whole row (size 12), some fields pair up by themselves, and the rows run on in order. `update-fields --help` says that `layout` "places the field on the form".
- **Impact:** every sheet created through the CLI has one field per row, and needs a second, full layout write.
- **Workaround (used):** read all controls, change only row / col / size, and write them back with `update-fields --controls @file` (after `--check`); the readback and the UI are both correct.

### P45 A new sheet whose default fields were replaced with `--fields`: the "All" view still lists the deleted defaults

- **Context:** as above; the sheet was created on 24 Nov 2026 at 23:56 and checked in the UI on 25 Nov 2026 at 00:10.
- **Steps:**
  1. `hap worksheet create <APP> <name> --fields '[...]'` (the default Name / Description / Attachment fields are replaced).
  2. Open the generated "All" table view, and check `displayControls` with `hap worksheet view info <WS> <VIEW>`.
- **Expected:** the "All" view shows the new fields (or at least does not reference fields that no longer exist).
- **Actual:** `displayControls` still holds the ids of two deleted default fields, and the list shows only the title column.
- **Impact:** every new sheet created through the CLI has a default list view that looks empty, and it must be fixed by hand before a demo.
- **Workaround (used):** `hap worksheet view update <WS> <VIEW> --view-json '{"displayControls":[...],"customDisplay":true}' --edit-attrs displayControls,customDisplay`; it reads back correctly.

### P46 hap-cli `worksheet view update --view-spec`: `tableFields` has no effect on a table view, and the command reports success

- **Context:** as above, 25 Nov 2026 00:11, fixing P45 first with `--view-spec '{"tableFields":[...]}'` to set a table view's columns.
- **Steps:**
  1. Run `view update --view-spec '{"tableFields":["<id>", ...]}'` on a table view (viewType 0).
  2. Read `displayControls` back with `view info`.
- **Expected:** the columns become the fields given (`hap guide worksheet` 4.2 lists `tableFields` as a view-spec key).
- **Actual:** the command reports success, and `displayControls` is unchanged. The same `tableFields` does set the card fields when a board view is created (`view create --view-spec`).
- **Impact:** a silent failure: it looks fixed, but the UI has not changed.
- **Workaround (used):** as in P45, `--view-json` with `--edit-attrs`.

### P47 hap-cli `app create --sections`: an extra empty group with no name; the navigation shows "Unnamed Group"

- **Context:** as above, 24 Nov 2026 23:50, `hap app create ... --sections '["Maintenance"]'`.
- **Steps:**
  1. Create an app with `--sections`, giving one group name.
  2. Create the sheets in that group, and open the app in the UI.
- **Expected:** the navigation has one group, "Maintenance".
- **Actual:** there is also a group with no name and no content (name "" in `app info`), and the top bar shows "Unnamed Group".
- **Impact:** the demo app looks unfinished; the group has to be deleted by hand.
- **Workaround (used):** `hap app delete-section <APP> <empty group id> -y`.

---

### Documentation issues (help.nocoly.com, cached 3 Nov 2026)

Details and URLs are in `native-catalogue/docs/*.md`, in each digest's Traps section.

- **D1. Region field:** the docs say regions outside China have two levels and no state codes. Live, Malaysia has country › state › district with ISO codes. (worksheet-1)
- **D2. Export/import:** "paid editions" on its own page, but included in Free on the plan page. (app-roles-portal-plugins)
- **D3. App recycle bin:** 7 days on one page, 60 on another. (app-roles-portal-plugins)
- **D4. Portal domain:** "cannot be changed" on one page, while the role table mentions editing a custom domain. (app-roles-portal-plugins)
- **D5. Plugin Center:** says field plugins are coming later, but a Custom Fields page exists. (app-roles-portal-plugins)
- **D6. International SMS:** 0.34 credits on one page, 2.3 on another. (org-collab-faq-other)
- **D7. Outbound IPs:** the API-request node page lists 2 IPs, the network FAQ lists 5 Hong Kong IPs. (integration-api-ai)
- **D8. API host:** the help page shows `api.mingdao.com`; Nocoly's own schemas use `www.nocoly.com/api`. (integration-api-ai)
- **D9. PDF output price:** CNY 0.15 per file on one page, US$0.03 on the plan page. (workflow-2)
- **D10. OCR price:** 0.15 credits per call on one page, 0.03 per file on another. (integration-api-ai)
- **D11. Mingdao-era content on Nocoly pages:** RMB prices, "Ultimate Edition", and an e-mail sender at `register.mingdao.com`. (app-roles-portal-plugins)
- **D12. Sub-process executions:** the sub-process page says its runs are not counted, then counts them. (workflow-2)
