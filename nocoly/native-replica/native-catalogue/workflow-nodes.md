# Native workflow triggers and nodes (Nocoly HAP): catalogue for wave 0

| | |
|---|---|
| Purpose | What Nocoly HAP's native workflow triggers and nodes can do today, so that the 16 Odoo behaviours in `../00-foundation.md` §4 can be built natively |
| Rule | Native first (Li Wei, 23 Nov 2026). A code block is allowed only when no native combination works, and then with a written reason |
| Status | Survey only, written 23 Nov 2026. Read-only: no workflow, node, record or setting was created, changed, published or triggered in any app |
| Target app | Odoo Replica (AI) `<uuid>`, Nocoly SaaS, CLI profile `<profile>` |
| Companion | `fields.md` (native field types), written separately |

**Evidence tags used below**

| Tag | Source | What it proves |
|---|---|---|
| [CLI] | hap-cli 0.9.14: `hap guide workflow --full`, `hap guide approval`, `hap guide record filter`, `hap workflow --help`, `workflow create --help`, `workflow node --help` and every `workflow node <sub> --help`, `node list-types`, `node types`; plus the `hap-cli-app-editor` skill references (`workflows.md`, `nodes.md`, `scenarios/`) | What the CLI can build and what it calls things. Not runtime behaviour |
| [Doc] | Nocoly Help pages cached in `knowledge-base/nocoly-mingdao/research/corpus.sqlite` (retrieved 3 Nov 2026; page dates up to Sep 2026) and chapter `03-workflows.md` | Vendor documentation. **Not a runtime test**; numbers can differ by plan or version, and some pages contradict each other |
| [MD] | Mingdao manual reviews in `knowledge-base/nocoly-mingdao/internal/` | Historical Mingdao text; not verified on Nocoly |
| [EMS] | EMS app `<uuid>`, read on 23 Nov 2026: all 298 workflow structures, 6 workflow configurations and about 25 node configurations | The setting exists and is saved on Nocoly SaaS. Says nothing about runtime unless [EMS-test] |
| [EMS-test] | EMS build notes (`../../handover/EMS-Handover-Digital-Omnis.md`, `../../modify-runs/*/RESULTS.md`) | Behaviour seen in earlier live tests |
| [Obs] | A read-only check made for this survey | One data point |
| [Design] | A proposal in this file | Not tested |

## 1. Summary

- **All 16 behaviours have a native design.** None needs a code block if the live tests in §7 pass. Code stays a fallback for two of them (#8 variants, #12 rule matching), and for one optional to-do variant of #15 that this file does not recommend (§5.7).
- **Five platform rules shape every design.**
  1. A record cannot start the same workflow again while that workflow's instance for the record is still running. The new event is **dropped, not queued** [Doc].
  2. A workflow's own writes do not trigger it again [EMS-test].
  3. Sequential, strictly sequential and partitioned runs exist **only** for create-only, delete and button workflows. Update, create-or-update, scheduled and date-field workflows always run in parallel [Doc] [EMS]. So the plan's "strict serial runs" for #2 cannot be set on an update trigger (§4).
  4. Volume limits: a set of records fed to Add / Update / Delete / Code nodes holds at most 100 rows; query-and-batch-update or -delete and relation reads take 1,000; a sub-process takes 10,000 array rows or up to 1,000,000 worksheet rows (default 50,000) [Doc] [EMS]. A loop runs at most 10,000 iterations [Doc].
  5. Time zone: Nocoly documents the SaaS server time zone as **UTC+8**, which is Malaysian time. Native timestamps read today match Malaysian time. Only the **code-block clock is UTC**: EMS code adds 8 hours [Doc] [Obs] [EMS]. The plan's "server time is UTC" applies to code blocks, not native nodes. To confirm with test Q1.
- **EMS leaned on code.** 205 code nodes sit in 108 of its 298 workflows, against 0 fill-in, 0 approval, 0 JSON-parse and 0 jump nodes [EMS]. Many of those code steps did date maths, path strings, simple arithmetic or user messages. Native nodes cover these: the Calculation node's functions (DATEADD, CONCAT, SUBSTITUTE, INCLUDE, IF, ROUND, MAX/MIN), loops and get-single queries with sorting (§6).
- **Shared logic should be PBPs, not sub-processes.** The plan names three shared sub-processes (Convert quantity, Convert amount, Price for product). A sub-process receives a record and returns no outputs to its caller. A PBP takes typed inputs, returns outputs, can be called from any app in the organisation, and one "execute once" call does not count as a workflow execution [Doc]. EMS has one PBP (`Calculated Probability`), and EMS and Odoo Replica (AI) are in the same organisation, so the feature is available here [EMS] [Obs].
- **Native to-do for activities (#15).** A fill-in node with a time limit gives a real to-do: deadline, overdue marking, reminders and a feedback form [Doc]. But the task can only be closed by submitting it from the to-do or the notification. A button or a direct record edit does not close it. Ending it from elsewhere needs the organisation API, which needs a code block for the signature [Doc]. Recommendation: keep the Activities sheet as the record of truth, use buttons, CC and notifications, and pilot the fill-in to-do in the Activities batch (§5.7).

## 2. Triggers

| Trigger | How it starts | Key options | Limits and traps | CLI |
|---|---|---|---|---|
| **Worksheet event** (START appType 1) | A record is created, updated, created-or-updated, or deleted; one instance per record | **Trigger fields:** an update starts the flow only when one of them is filled in or changed. **Filter:** only matching records start it [Doc]. EMS trigger ids: 1 create, 2 create or update, 4 update, 3 delete (EMS has 17 / 34 / 34 / 9 of them) [EMS] | Parallel only, unless create-only or delete (§4). A second change to the record while its instance runs does not start the flow again [Doc]. Workflow writes start another flow on the **same** trigger sheet only when that flow has trigger fields [Doc]. Per flow, "trigger other workflows" is allowed / only the listed flows / none (config `triggerType`, `processIds`) [Doc] [EMS] | `workflow create --type worksheet`; `node batch-add --trigger-worksheet <ws> --trigger-event create\|update\|create_or_update\|delete --trigger-fields f1,f2 --trigger-filter '{…}'` (filter `node` is always `trigger`; options by key) [CLI] |
| **Scheduled** (appType 5) | At a start time, then hourly / daily / weekdays (Mon–Fri, holidays excluded) / weekly / monthly / yearly / custom (several times a day, chosen weekdays and months; preview of the next 7 runs) [Doc] | Start time, optional end time; "Execute now" after publishing [Doc]. EMS stores `executeTime "2026-11-18 06:15"`, `repeatType 1` daily, `7` custom [EMS] | No record: query first. Always parallel. Runs on server time (UTC+8 on SaaS, [Doc]). Which holiday calendar "weekdays" uses is not stated | `--type scheduled`; `--trigger-schedule '{repeat,interval,week_days,start_time,end_time,config}'` [CLI] |
| **Date field** (appType 6) | Per record, when server time reaches a date or date-time field, plus or minus an offset | Date-only field: on / N days before / after, at a time of day (default 08:00). Date-time field: exactly, or ± minutes / hours / days. Repeat yearly / monthly / weekly / none; end time; filter conditions [Doc]. EMS `Activity Due Reminder`: Due Date (date-time), 15 minutes before, filter Status = Scheduled and Active [EMS] | Re-arms when the field changes [Doc]. A time already past when the record is saved is not documented (Q12). Interface Push not available | `--type date`; `--trigger-date '{worksheet,date_field_id,offset_type,offset_number,offset_unit,time,repeat}'` [CLI] |
| **Button** (custom action; appType 8) | A user clicks a button on one record, or on several selected records; the second starts **one** run whose trigger is the whole set (EMS: 39 of its 110 button start nodes carry action 411, batch; inferred) | Dialog before the run (fill chosen fields, or create a related record), confirmation and comment, password, availability conditions, "notify when the workflow completes" [Doc] | Execution mode can be set (sequential, strict, partitioned) [Doc]; config flags `sequence` / `partitionSequence` are true here [EMS]. Interface Push works when no waiting node comes before it [Doc] | `worksheet create-custom-action <ws> --action-spec '{"name":…,"type":"triggerWorkflow"}'` returns the processId, then `node batch-add` [CLI] |
| **Webhook** (appType 7) | An external HTTP request | Parameters derived from a sample body; custom response; authentication and IP limits [Doc] | 10,000 requests per hour [Doc] | `--type webhook`; `--trigger-webhook '{"sample":{…}}'` [CLI] |
| **PBP** (appType 17) | A Call PBP node in any workflow of the organisation, a custom-page button, or its own API | Typed inputs (text, number, date, member, department, org role, attachment, object, array, object array) and output parameters [CLI] [Doc] | An API mode that answers the caller cannot contain approval, fill-in, delay, sub-process or Call PBP nodes. Outputs cannot be files [Doc] | `--type pbp`; `--trigger-pbp '{"inputs":[…]}'`; `workflow pbp-parameters`; `workflow trigger-pbp` [CLI] |
| **Sub-process** (child flow) | Only from a Sub-process node, with one record, a set of records, or array rows [Doc] | Parameters and execution mode come from the calling node [Doc] | Cannot be started alone. Editing it puts the parent back into draft; publishing the parent publishes inner flows first [CLI] | Created by a `sub_process` node spec [CLI] |
| **Loop process** (appType 45) | Created by a Loop node; another Loop node can reuse it [Doc] | Count or condition mode (§3.3) | EMS has 18 [EMS] | Created by a `loop` node |
| Member and external-user events | Member joins or leaves; portal user registers, signs in, is removed or disabled [Doc] | — | Not needed in wave 0 | `--type staff`, `--type portal_user` [CLI] |

## 3. Nodes

**How the CLI configures nodes** [CLI]:
- `node batch-add --nodes '[{"nodeAlias","nodeType","config"}]'` builds a whole chain in one all-or-nothing call. It has a **high-level form** for data, query, branch, approval, fill-in, notification, sub-process, calculation (`compute`) and code nodes.
- The other kinds (`loop`, `delay`, `rollup`, `packaged_process`, `goto`, `parse_json`, …) can be created by name, but their settings are the raw keys. Read a working node with `node get --type <n>` (EMS examples below) and copy its shape.
- `node save` writes the **whole** step: keys left out are cleared. `save-action`, `save-search` and `save-get-more` change only the options named.
- Reserved aliases: `trigger`, `sub_trigger` (the record a sub-process is on), `approval_trigger`, `approval_start`.
- Value kinds in field writes: `literal`, `template` (`$alias-fieldId$`), `field` (another step's column), `record` (a whole record into a relation), `systemField` (`triggeraid`, `triggertime`, `nowTime`, …). Operations: `set`, `append`, `subtract`, `clear`.
- `workflow publish` is the only full validation. A fill-in node with no editable field, or an unbound trigger, is reported only there.

### 3.1 Records

| Node | What it does | Key options | Limits | CLI `nodeType` / wire type-action |
|---|---|---|---|---|
| Add Record | One record, or one per record of a set (batch) | Literal, template text, another step's column, a whole record into a relation, system values; field types must match [Doc] [CLI] | At most 100 records from a set [Doc] | `create_record` / 6-1 (6-5 create and link). EMS batch-add example: `Expand Activity Plan Launch` [EMS] |
| Update Record | One record (trigger, query result, created record) or every record of a set | Set, clear, add or subtract (numbers, money, multi-select, members, departments, multi-relations, files), keep text and append [Doc] | A set: at most 100 records, and only "set" [Doc] [CLI] | `update_record` / 6-2 |
| Delete Record | One record or a set | Recycle bin (60 days) or permanent [Doc] | As above | `delete_record` / 6-3 |
| Get related record | The record a relation field points to | — | One record | `get_relation` / 6-20 (EMS: 241 nodes) |
| Get Single Data | Queries a worksheet for one record | AND/OR condition groups, sorting (first record wins), random pick, ignore empty condition values. When none is found: continue, **create a record and continue**, or stop / take the "no data" branch. Variants: query-and-update (can return the values **before** the update), query-and-delete, one record from a set, one from a relation, one from a record link [Doc] | Date-time **equals** compares by day; other operators to the second [Doc] | `get_single` 7-406, `query_update` 7-421, 7-422, 7-407, 7-420 (EMS: 516 queries) |
| Get Multiple Data | A set of records | Query a worksheet (filters, several sort keys, first N by a fixed number or a field, or random N; "direct" or "dynamic" retrieval); related records of one record (with a filter); records just batch-added; approval or fill-in operation details; object arrays from code, API, PBP or JSON parse; query-and-batch-update; query-and-batch-delete [Doc] | Default 100. Over 100 into Add / Update / Delete / Code **ends the run**. Relation read ≤ 1,000. Batch update or delete ≤ 1,000 (the first 1,000 by sort). To a sub-process: 10,000 [Doc], or up to 1,000,000 with "all records", default 50,000 [Doc] (EMS `executeAllCount 50000`) [EMS] | `get_multiple` 13-400, `get_relation_records` 13-401, 13-402…405, 13-412, 13-413. EMS sort and limit: `sorts [{controlId, isAsc:false}]`, `numberFieldValue.fieldValue "100"` [EMS] |
| Calibrate | Recomputes formula, rollup and stored lookup values | One record (synchronous; later nodes see new values) or a worksheet (asynchronous, ≤ 100,000 rows, once per 120 minutes) [Doc] | Worksheet mode: later nodes do not see the new values | Wire 6-6 and 13-415 (inferred from the action list) |
| Update Record Followers | Adds, removes or replaces followers of a record [Doc] | — | — | 6-8 |

### 3.2 Calculation

| Node | What it does | Key options | Limits | CLI |
|---|---|---|---|---|
| Calculation | Computes a value for later nodes. It does not write anything | **Number:** operators or system formulas, 2 decimals by default, "treat empty as 0". **Date:** add or subtract Y, M, d, h, m, including a numeric field followed by a unit (`+7d`, `-74h`, `+8h+1m`); date-only or date-time input. **Date difference:** two boundary formats, output unit. **Functions:** the formula-field function set, including IF, AND, OR, ISBLANK, DATEADD (offset may be built with CONCAT), DATENOW, WORKDAY, CONCAT, MID, LEFT, RIGHT, SUBSTITUTE, REPLACE, FIND, INCLUDE, SPLIT, JOIN, ROUND, ROUNDUP, ROUNDDOWN, CEILING, FLOOR, MAX, MIN. **Static** (computed once) or **dynamic** (recomputed at each use) [Doc] | A result that cannot be converted to the output type is empty. A formula with an empty or deleted operand is empty unless "empty as 0" [Doc] | `compute` with `mode` number / date / date_diff / function and `output_type` [CLI] / 9-100, 9-101, 9-104, 9-106. EMS: 81 number, 12 function (`CONCAT(…,"\|",…)`), 1 date (`-74h` from `nowTime`) [EMS] |
| Rollup | Aggregates | **Summary from worksheet:** count, sum, average, max, min, count filled or empty, with filters; no row limit; may lag slightly behind recent writes. **Count of a Get Multiple set:** with or without that node's limit. **Sum over the records selected for a batch button.** Static or dynamic [Doc] | Related records read through a relation cannot be fed to "summary from worksheet"; query the worksheet with "relation = record id" instead [Doc]. EMS filters a relation by the trigger's Record ID [EMS] | `rollup` / 9-107 (EMS 117), 9-105 (EMS 7), 9-108 |

### 3.3 Flow control

| Node | What it does | Key options | Limits | CLI |
|---|---|---|---|---|
| Branch | Splits the run | **Exclusive:** first matching path from the left; a path with no condition is the else, put it last. **Parallel:** every matching path, left to right; the next path starts when the previous one finishes, unless that one waits. **Result branches:** after an approval (pass / reject) and after Get Single Data (has / no data) [Doc] [CLI] | Conditions compare a column with a literal, another step's column, a system value (`nowTime`) or a date window (today, this week, …; not the fixed-length ones). No `between` [CLI]. Relation conditions seen in EMS: empty, not empty, equals another step's relation or a record id [EMS] | `branch` with `mode` and `paths` / 1 + 2 |
| Loop | Repeats an inner loop process | **Count mode:** start, end, step (ends when start > end). **Condition mode:** system `index` plus custom parameters changed by Update Parameters; exit condition. Strictly sequential. Pass the triggering user. On a terminated iteration: skip it, end the loop, or end the workflow. Final parameter values readable after the loop. Reuse an existing loop process [Doc] | **At most 10,000 iterations**, then the run continues after the loop as if done. **Each iteration is one workflow execution** [Doc]. EMS sets a lower cap (`maxLoopCount 101`) and nests loops inside a sub-process [EMS] | `loop` / 29-211 count, 29-210 condition. EMS keys: `subProcessVariables` (start/end/step or index plus custom), `fields` (initial values, can read earlier steps and `instanceId`), `conditions` (exit), `maxLoopCount`, `fromTrigger` [EMS] |
| Sub-process | Runs a child flow for one record or for each record or row of a set | **Parallel**, **one by one, stop on abort**, or **one by one, continue**. Wait or not. Pass the triggering user. Parameters [Doc] | 100,000 sub-process runs per hour; one record = one execution; a terminated child ends the parent when the node waits and runs parallel or "stop on abort" [Doc]. The Help page also says one sub-process run is not counted, then counts it in its own example [Doc]. EMS nests sub-processes three levels deep and shares one child between several flows [EMS] | `sub_process` (`data_source`, `execute_type` 1/2/3, `wait_complete`, `parameters`, inner `nodes`) [CLI] / 16. EMS keys: `executeType`, `nextExecute` (wait), `executeAllCount`, `fromTrigger` [EMS] |
| Call PBP | Runs a PBP once or several times | Once; per record of a set; or N times from a number. Parallel, or one by one (stops at the first abort). Wait, to read its outputs. Pass the triggering user. PBPs of other apps in the organisation [Doc] | Per record: ≤ 100 runs if a parameter reads the set's fields, else ≤ 10,000; per number: no limit. "Execute once" is not counted as an execution [Doc] | `packaged_process` / 20 |
| Jump To | Goes back to an earlier node on the same branch or the main path, with an optional condition [Doc] | — | **At most 20 jumps per run**. Jumping from a parallel branch ends the other branches. Re-runs side effects [Doc] | `goto` / 35 |
| Terminate Process | Ends the run and its running children; inside a loop or sub-process the caller's option decides [Doc] | — | Does not undo earlier writes | Wire 30 (`RETURN`); EMS names it "Stop — …" [EMS] |
| Update Parameters | Sets the run's own parameters | Text, number, date, array, object array, member, department, org role [Doc] | Exist for one run only [Doc] | Wire 6-2 aimed at the flow's parameter node (appType 102) [EMS] |
| Update Global Variables | Sets organisation- or app-level text or number variables shared by flows [Doc] | Per variable: may workflows update it | Not a lock [MD] | — |
| Delay | Waits | **Until a date:** a field or fixed date; on, N days before or after; at a time (default 08:00; a date-time field keeps its own time). **For a duration:** days ≤ 999, hours ≤ 23, minutes ≤ 59, seconds ≤ 59, fixed or from fields [Doc] | Can resume late [Doc] | `delay` / 12-300, 12-301 (EMS `Lead Rotting Alert` reads the days from a field) [EMS] |

### 3.4 People and notifications

| Node | What it does | Key options | Limits | CLI |
|---|---|---|---|---|
| Fill in | A form task in the to-do centre for one record | Assignees: fixed members, department, position, role, or a member field; the **first** to submit completes it. Per field hidden / read-only / optional / required; summary fields; button name; instructions; stash; forward (to anyone or to candidates); password. **Time limit:** a deadline after X days / hours / minutes, or from a date field plus a time; reminders before or after it to the assignee and others, repeating up to 10 times; when overdue: submit automatically, end the workflow, or keep waiting. Empty-assignee policy; e-mail copy (credits); field updates on entry and on submit [Doc] | **Only Submit from the to-do or the notification completes it**; editing the record in the sheet does not [Doc]. Grants view and edit rights beyond the user's role for that record [Doc]. Publish fails with no editable field [CLI] | `fill_in` (`accounts`, `formProperties`) [CLI] / 3. Wire keys read from an earlier POC app backup: `schedule` (`{"enable": false}` when off), `submitBtnName`, `explain`, `allowTransfer`, `encrypt`, `userTaskNullMap` [Obs]. The shape of an enabled `schedule` is not known yet (Q8). Submit by CLI: `approval submit` [CLI] |
| Approval | A decision task | Assignee and form options as above; or-sign, all, any, percentage; time limit showing remaining or overdue time; reminders; on timeout pass, reject, end or wait [Doc] | Rejection ends the run unless a result branch follows [Doc] | `approve` / 4 |
| Initiate Approval Flow (approval block) | Runs approval, fill-in, CC and branch nodes as one approval with a single result | Approvers act **in the record itself**; app admins can end it or replace operators from the record [Doc] | Settings differ from plain approval nodes [Doc] | `approval_block` (set `source`, or it approves the triggering record) [CLI] / 26 |
| CC | A message with a record link, shown under **To-Do › CC** until opened; summary fields; shown through a chosen view; e-mail copy with attachments; sound [Doc] | — | Can skip the triggering user (global setting) [Doc] | `cc` / 5 (EMS 4: activity assignee, reassignment, due reminder, lot owner) [EMS] |
| Send Internal Notification | A text message from "Workflow Message"; not in the to-do list [Doc] | — | — | `notice` / 27 (EMS 74). Keep `flowNodeMap["106"]` when saving [CLI] |
| Email, SMS | E-mail (attachments ≤ 50 MB, standard or one by one); SMS through the organisation's Twilio [Doc] | — | — | `send_email` 11-201/202, `send_sms` 10 |
| Interface Push | Toast to the user who clicked, or a card to others; or opens a record, a new-record form (draft), a view, a page or a link [Doc] | — | Not in scheduled, date-field, webhook or sub-process flows; no approval, fill-in, delay, sub-process, PBP or loop before it; only the first push of a run [Doc] | `push` / 17 |
| Create Event, Create Task | Calendar event (reminder minutes, private, ICS file) or collaboration task [Doc] | — | Not linked back to the record's state | EMS creates calendar events as data node 6-1 with appType 43 [EMS] |
| Get member / department / org role | One or several organisation objects, e.g. a member's manager [Doc] | — | One object cannot feed a sub-process [Doc] | — |

### 3.5 Integration and code

| Node | What it does | Limits | CLI |
|---|---|---|---|
| Send API Request | Custom HTTP call (GET, POST, PUT, PATCH, DELETE, HEAD), headers, body, success codes, continue or end on error [Doc] | 10 s timeout; fixed outbound IPs [Doc] | `webhook` / 8 |
| Call Integrated API, Authentication | Reuses a connection from the integration centre [Doc] | — | `call_api` / 25 (EMS 10: Stripe, MyInvois), `authenticate` / 22 |
| JSON Parsing | JSONPath into variables or arrays; custom errors with continue or end [Doc] | Arrays need a Get Multiple node to become rows [Doc] | `parse_json` / 21 |
| Code Block | JavaScript (Node 10.16.3) or Python (3.7.5) [Doc] | **10 s**; **≤ 100 input rows**; outputs exist only after a test run; one automatic retry (`maxRetries 1`) [Doc] [EMS]. Number and checkbox inputs arrive as text such as `"1.0"`; a relation field as input can fail; **the clock is UTC** (EMS adds 8 h) [EMS-test] [EMS]. Documented as a Professional-plan feature, like PBP [EMS-test] | `code` / 14-102 JavaScript, 14-103 Python |
| AI text, AI object, AI agent, knowledge lookup, plugin | Not needed in wave 0 | — | `generate_text`, `agent`, `vector_search`, `plugin` |

## 4. Run rules that shape every design

1. **One instance per record per workflow.** "If Record A has already triggered Workflow B and the current instance of Workflow B has not yet completed, modifying Record A again will not re-trigger Workflow B" [Doc]. Quick double edits can therefore be lost, and a waiting node (fill-in, delay) blocks every later event for that record in that flow.
2. **No self-trigger.** A workflow's own writes do not start it again [EMS-test]. A writes-to-same-sheet chain needs a second flow, a PBP, or a queue sheet (Q10).
3. **Execution modes.** Parallel, sequential, strictly sequential, and strictly sequential by partition (a field such as Product) exist only for create-only, delete and button flows [Doc]. Readback agrees: `sequence` / `partitionSequence` are true on EMS create, delete and button flows, false on update, create-or-update, scheduled and date flows [EMS]. EMS `Inventory - Scan Barcode` (create) has `executeType 3`; defaults are `1` [EMS]; 2 and 4 are inferred. Sequential mode lets the next instance start when the current one reaches a delay, approval, fill-in, sub-process or PBP [Doc].
   - **Pattern for update-driven work that must not race** [Design]: the update flow only adds a row to a small queue sheet; a create-only flow on that sheet does the work, strictly sequential by partition.
   - **Or** make the work idempotent: read the source again with Get Single Data at run time, never trust the trigger snapshot, and offer a "Resync" button (buttons can be serial).
4. **Stale lookups.** Lookup values read inside a running flow can be stale [EMS-test]. EMS's first location-path cascade failed for that reason [EMS-test]. Read through Get Single Data on the worksheet instead.
5. **Waiting and order.** Parallel branches run left to right [Doc]. Platform queues are shared across organisations, so start times can slip [Doc].
6. **Slow queries.** More than 300 queries slower than 1 s per worksheet per minute are rate-limited, with up to 10 automatic retries [Doc].
7. **Time.**
   - Server time zone on SaaS: UTC+8 for stored date-times, system time fields, workflow trigger times and scheduled workflows [Doc].
   - [Obs] Industries rows created by the build script at about 13:49 Malaysian time read back through the API as `_createdAt 2026-11-23 13:49:46`.
   - The app time zone (App Management › Time Zone) sets the "today" boundaries of view, rule and chart filters [Doc]; set it to Kuala Lumpur.
   - System date-time fields work to the minute unless the flow is set to seconds [Doc].
   - Code blocks run on UTC [EMS].
8. **Executions.** Every run, loop iteration and sub-process record counts against the monthly workflow quota; once the quota is used up, flows stop triggering [Doc]. Designs below note their execution cost.
9. **Testing.** An editor test really writes, passes approval and fill-in nodes automatically and skips sub-processes and PBPs [Doc]. `workflow trigger --debug` sends to-dos, SMS and e-mail to the tester [CLI]. A failed run can be retried from the failed node [Doc]. Node input/output logging keeps 90 days [Doc].

## 5. The 16 behaviours

Names in `code font` are CLI node types. "Trigger fields" narrow an update trigger. Each design reads live values with `get_single`, not lookups, because of rule 4.

| # | Odoo behaviour | Native design: trigger → nodes | Risks | Needs code? |
|---|---|---|---|---|
| 1 | Display name "Company, Person" | **Field first:** a function formula `IF(ISBLANK(Parent Name), Name, CONCAT(Parent Name, ", ", Name))` if `fields.md` confirms the type. **Workflow fallback:** Contacts create-or-update (trigger fields Name, Parent, Type) → `get_relation` parent → `branch` (person with a parent / else) → `update_record` Display Name from a template. Company renamed: Contacts update (Name; filter Is Company) → `get_relation_records` its people (≤ 1,000) → `sub_process` → `update_record` | Lookups stale in-run (rule 4); quick double edits dropped (rule 1). Odoo's type labels for nameless Invoice / Delivery addresses need one more branch | No |
| 2 | Commercial fields (VAT, other ids, industry) copied from company to people | Company update (trigger fields VAT, ids, Industry; filter Is Company) → `get_single` the company again → `get_multiple` query-and-batch-update people with Parent = company (≤ 1,000; set the fields). Person create, or Parent change (create-or-update; field Parent) → `get_single` parent → `update_record`. Button **Resync people** (button flows can be strictly sequential) | The plan's "strict serial runs" **cannot** be set on update triggers (rule 3). Use idempotent re-reads plus the button, or the queue pattern. Writes reach other Contacts flows only if those have trigger fields | No |
| 3 | Contact-type people use the company address | Company update (address fields; filter Is Company) → query-and-batch-update people with Parent = company **and** Type = Contact (Street, Street 2, Zip, City, Region). Person create, or Type / Parent change → `branch` Type = Contact → `get_single` parent → `update_record` the address | Same as #2. Set "trigger other workflows" to only the listed flows, so address writes do not start unrelated flows | No |
| 4 | No circular parents | Relation filter: only companies can be picked (UI). Contacts create-or-update (field Parent) → `get_single` the new parent → `compute` function `INCLUDE(parent.Parent Path, Record ID)` (Odoo-style `parent_path`, e.g. `/a/b/`) → `branch`: loop found → `update_record` Parent back to a hidden "Last Valid Parent" + `notice` to the user; else → write Parent Path and Last Valid Parent, and cascade the path to descendants as in #10. Or, safer: a **Set Parent** button whose dialog is checked before anything is saved; it can answer with Interface Push because no loop node is used | Checked after saving, so the bad value exists for a moment, unless the button route is used. Last Valid Parent needed because an update trigger does not expose the old value | No |
| 5 | A person takes the company's language | Contacts create (filter Parent not empty and Language empty) → `get_relation` parent → `update_record` Language | Field default from the parent may be enough (`fields.md`) | No |
| 6 | Unique country code | Countries create-or-update (field Code) → `compute` `UPPER(TRIM(Code))` → `get_single` Countries where Code Key = key **and** Record ID ≠ this → `branch` has data → tick Duplicate, clear the key, terminate; no data → write the key. This is EMS's `States: the key and the duplicate check` (function calc, query, branch, terminate) [EMS]. States: no flow, the native Region field replaces the sheet | Two simultaneous **creates** can both pass. Fix: split it into a create-only flow, strictly sequential by partition on the code (allowed on create-only, rule 3), and an update flow, which stays parallel | No |
| 7 | Unit factor chains and conversion | §5.1: stored Factor and Parent Path; factor = Contains × parent's stored Factor (one step up, no recursion); descendants rewritten by path prefix in a `sub_process` sorted by level; **PBP** "Convert quantity" | Floating-point drift in long chains; cascade must run parents first; self-trigger rule 2 | No |
| 8 | Variants from attribute lines; always / dynamic / never | §5.2: queue sheet + create-only flow, strictly sequential per product; PTAV sync by find-or-create; cartesian product by **nested sub-processes** over a helper sheet; find-or-create each variant by combination key; archive the rest by run stamp; "dynamic" creates nothing, "never" lines are left out | Relation copy-plus-append per row (Q5); execution cost about 1 per combination; single-value lines differ from Odoo unless handled | No, if Q4, Q5 and Q17 pass. Fallback with reason: one code step that returns the combination list as an array (its output is not capped at 100 rows; a sub-process takes up to 10,000) |
| 9 | Barcode unique across products and variants | Products and Variants create-or-update (field Barcode; filter not empty) → `get_single` Products where Barcode = x and Record ID ≠ this → `get_single` Variants where Barcode = x and Product ≠ this product → `branch` any found → tick Barcode Conflict, clear or restore the barcode, `notice` | Same-moment race between two creates: partition the create flow by barcode | No |
| 10 | Category full name ("All / Saleable"); no circular parents | EMS's `Inventory - Location full path` pattern without its code [EMS]: Categories create-or-update (Name, Parent) → `get_single` parent → `compute` cycle check `INCLUDE(parent.Path, Record ID)` → `query_update` self (Full Name = `CONCAT(parent.Full Name, " / ", Name)`, Path) returning the **old** values → `get_multiple` descendants whose Path starts with the old Path → `sub_process` (parameters old and new prefixes) → `compute` `SUBSTITUTE(Full Name, old, new, 1)` → `update_record` | Cascade by prefix needs no recursion [EMS-test]. Child writes must not re-fire the parent flow: narrow trigger fields to Name and Parent | No |
| 11 | Variant sales price = product price + extra prices | Rollup **field** on Variants (sum of its PTAVs' Extra Price) plus a stored price. Triggers: PTAV Extra Price update, Variant PTAVs change, Product list price update → `get_multiple` affected variants → `sub_process` → Calibrate (single record) → `compute` product price + rollup → `update_record` Sales Price | Rollup fields refresh late; Calibrate before reading. "Summary from worksheet" over a multi-relation needs Q7 | No |
| 12 | Pricelist rule choice and price | §5.3: **PBP** "Price for product". One `get_single` on Pricelist Rules does Odoo's search and order: filters for pricelist, active, dates, minimum quantity and target, sorted by applied-on rank, minimum quantity desc, category key desc, rule number desc. Then `branch` on fixed / discount / formula and `compute` with ROUND, MAX, MIN. Chained "other pricelist" bases are walked by a condition loop and a trace sheet | The OR-groups for the target (Q6); category depth fixed at N levels; executions per priced line; Odoo's half-up rounding vs HAP ROUND (Q13) | No. Removes the plan's 100-rule cap. If Q6 fails: one sorted query per target kind (variant, product, each category ancestor, all) and a branch that applies Odoo's order, still native. Code (EMS's way, ≤ 100 rules) only as the last resort |
| 13 | Currency rate on a date and conversion | §5.4: **PBP** "Convert amount". `get_single` Rates for currency C with date ≤ D, sorted by date desc; no data → the earliest rate; none → 1.0. Then `compute` amount × rate_to / rate_from and round to the target currency. Current rate kept by a flow on Rates and a daily run | All rates must share one base (Odoo: the company currency, rate 1). The rates loaded on 23 Nov are Odoo's demo rates against USD (`../00-foundation-build/BUILD-LOG.md`), so the base must be settled before testing | No. Daily automatic rates (decision 7): scheduled `webhook` + `parse_json` + batch `create_record`, still native |
| 14 | Activity state (overdue / today / planned) in Malaysian time | §5.5: on save, compute the state at once; daily scheduled flow at 00:05 with three query-and-batch-update nodes, looped while more than 1,000 rows remain | Time zone (Q1, Q2); 1,000 rows per batch node; executions | No |
| 15 | Mark done with feedback; archive; next activity with delay | §5.6: buttons **Mark Done** and **Done & Schedule Next** with dialogs (Feedback; next type, date and summary) → `update_record` (Active off, State Done, Done Date, Feedback) → `get_single` type → `branch` chaining = trigger → `compute` `DATEADD` with the type's delay → `create_record` the next activity → `push` to open it. Optional to-do layer: §5.7 | Double clicks: make the button flow strictly sequential by partition on the activity. Odoo posts to the document's chatter; HAP has no "post a comment" node, so the archived activity under the document's typed relation is the history | No. The fill-in-only variant would need code to end tasks (§5.7), which is why it is not recommended |
| 16 | Activity plan launch | §5.6: **Launch Plan** button (dialog creates an Activity Plan Launches row: plan, plan date, on-demand assignee) → create-only flow → `get_multiple` steps sorted by sequence → `sub_process` per step → `compute` `DATEADD(plan date, ±N d/M)` → `branch` assignee (fixed / on demand / record owner) → `create_record` activity linked to the launch and the document. Same shape as EMS `Expand Activity Plan Launch`, which used code only for the date [EMS] | On-demand step without an assignee must stop the launch first (`rollup` count + `branch`); one execution per step | No |

### 5.1 Units (#7)

Sheet fields (wave 0): Contains (`relative_factor`), Reference Unit (`relative_uom_id`, self relation), Factor (number, stored), Parent Path (text, Odoo's `parent_path`, e.g. `/m/cm/`), Level (number), Last Valid Reference Unit (hidden).

**Flow "Units - factor and path"** [Design]. Trigger: Units create-or-update, trigger fields Contains and Reference Unit (not Factor, not Path, so its own cascade does not fire it).
1. `get_single` the reference unit by record id (fresh value; rule 4).
2. `branch`:
   - **No reference unit:** Contains must be 1 (Odoo `_check_factor`). If not, write an error message and restore Contains to 1.
   - **Has one:** `compute` the cycle check `INCLUDE(parent.Parent Path, Record ID)`. On a cycle, restore Last Valid Reference Unit and notify.
3. `compute`: Factor = Contains × parent.Factor (number mode; no "empty as 0"). Path = `CONCAT(parent.Parent Path, Record ID, "/")`; Level = parent.Level + 1.
4. `query_update` this unit with Factor, Path, Level and Last Valid Reference Unit. It returns the **old** Path and Factor.
5. If the Factor or Path changed: `get_multiple` units whose Parent Path starts with the old Path, sorted by Level ascending → `sub_process`, **one by one** → each child: `get_single` its parent again → `compute` → `update_record` Factor, Path and Level.

Chains of any depth are covered without recursion; Odoo itself stores `parent_path`.

**PBP "Convert quantity"** (inputs: quantity, from unit id, to unit id, round yes/no; output: quantity):
1. Two `get_single` reads of the units.
2. `compute`: quantity × from.Factor ÷ to.Factor.
3. Optional rounding: Odoo rounds **up** to the "Product Unit" precision, so use `ROUNDUP(x, digits)`.

Later modules call it with Call PBP, "execute once" (not counted as an execution) [Doc].

### 5.2 Variants (#8)

Sheets:
- **Product Attribute Lines** (subtable of Products): Attribute; Values, limited to that attribute; Variant Creation, a lookup.
- **Product Attribute Values (PTAV):** Product, Value, Attribute, Extra Price, Active, Key `product|value`, Run.
- **Variants:** Product, PTAVs (multi-relation), Combination Key, Active, Run.
- Helpers in System Tables: **Variant Requests** (Product, Done) and **Variant Build Rows** (Run, Product, Key, PTAVs, Done).

**Flow A "request variants"** [Design]:
- Triggers: attribute line create, update or delete (Attribute, Values); product create; a **Rebuild variants** button.
- Node: `create_record` a Variant Request.
- Dedupe in flow B: if a newer open request exists for the product, stop.
- Why a queue: line edits are update triggers (parallel only, and dropped while a run is busy, rules 1 and 3).
- Flow A's "trigger other workflows" setting must stay "allowed", or flow B never starts.

**Flow B "build variants"** [Design]:
- Trigger: Variant Requests **create-only**, strictly sequential **by partition = Product**.
- Run id: the system `instanceId`, which EMS reads as `$system-instanceId$` [EMS].

Steps:
1. **PTAV sync.**
   - `get_multiple` the product's lines → `sub_process`, one by one → `get_relation_records` the line's Values → `sub_process`.
   - Each value: `get_single` the PTAV by Key with **"create a record and continue"**. That is native find-or-create; new PTAVs take the value's default extra price. Then `update_record` Active = on, Run = run.
   - Afterwards, query-and-batch-update this product's PTAVs whose Run ≠ run: Active off (≤ 1,000).
2. **Mode check.** `rollup` counts the lines in "dynamic" mode.
   - If any: create nothing. Odoo also skips creation when any attribute is dynamic.
   - Then `get_multiple` this product's active variants → `sub_process` → `get_relation_records` the variant's PTAVs filtered to Active = off → `rollup` count → archive the variant if the count is above 0.
3. **Cartesian product** ("always" lines; "never" lines are excluded).
   - Seed one Build Row with an empty Key.
   - `get_multiple` the lines in a **stable order** (attribute sequence, then attribute id; not the line order) → `sub_process`, one by one, one call per line.
   - In each call: `get_multiple` this run's Build Rows not yet Done, with **direct access** (a snapshot, so rows created during this pass are not picked up) → `sub_process`, one per row.
   - In each row: `get_multiple` the line's active PTAVs (≤ 100) → `sub_process`, one per PTAV → `create_record` a Build Row with Key = row Key + "|" + PTAV Key and PTAVs = the row's PTAVs plus this PTAV. Then the row is marked Done.
   - Three nesting levels; EMS already runs three [EMS].
4. **Variants.**
   - `get_multiple` this run's open Build Rows (≤ 10,000; Odoo's own limit is 1,000) → `sub_process` → `get_single` the Variant by Product and Key with "create a record and continue" (PTAVs copied from the row) → `update_record` Active = on, Run = run.
   - Query-and-batch-update the product's active variants whose Run ≠ run: Active off. If more than 1,000, loop.
   - Query-and-batch-delete this run's Build Rows (permanent).
5. **No lines at all:** the seed row alone gives one variant with an empty key, as in Odoo.

**Cost and gaps:**
- About one execution per Build Row and per variant: 3 × 3 is about 25 executions; 10 × 10 × 10 is about 1,150.
- Odoo writes a newly added **single-value** line onto existing variants instead of recreating them. Here every key changes, so the variants would be archived and created again. To match Odoo, add a branch before step 3 that appends that PTAV to the existing active variants and their keys.
- Attribute exclusions are out of scope.

### 5.3 Pricelists (#12)

Pricelist Rules get these stored helper fields, written when a rule is saved (Odoo default min quantity 0; empty dates become 1900-01-01 / 2999-12-31):
- **Rank:** 0 variant, 1 product, 2 category, 3 all.
- **Target Key:** variant id, product id, category id, or `ALL`.
- **Category Sort Key:** the category's number, for Odoo's `categ_id desc`.
- **Effective Start / End.**
- **Min Qty.**

Each Product Category keeps Ancestor Key 1…N (its own id and its parents' ids, N = 5), maintained by the #10 flow.

**PBP "Price for product"** [Design].
- Inputs: pricelist, product, variant, quantity, unit, date.
- Outputs: price, rule id, rule label, trace.

Steps:
1. `get_single` the variant and product. Read list price (product price plus extras, from #11), cost, product unit and the category ancestor keys.
2. Call PBP "Convert quantity" into the product unit (Odoo checks the minimum quantity in the product unit).
3. **Rule search:** one `get_single` on Pricelist Rules.
   - Each condition group = pricelist = P, Active, Effective Start ≤ date, Effective End ≥ date, Min Qty ≤ quantity, plus one target alternative: `ALL`, the variant id, the product id, or one of the N category ancestor keys.
   - That is N + 3 OR-groups, the stored shape (outer OR, inner AND). Leave unused ancestor slots as a non-matching placeholder, not empty, so that "ignore empty values" cannot widen the search.
   - Sort: Rank asc, Min Qty desc, Category Sort Key desc, rule number desc. This is Odoo's `_order` and the "first applicable rule wins" loop.
   - No data: continue with no rule (price = base price).
4. `branch` on the rule's price type:
   - **Fixed:** fixed price converted to the unit (× target unit factor ÷ product unit factor).
   - **Discount:** base × (1 − percent ÷ 100).
   - **Formula:** base − base × discount ÷ 100, then `ROUND(price / rounding, 0) * rounding`, + surcharge, then `MAX(price, base + min margin)` and `MIN(price, base + max margin)` when set.
   - All in `compute` function mode.
5. **Base price** = list price, cost, or another pricelist.
   - For "another pricelist", a condition `loop` walks the chain: same rule search on the base pricelist, one trace row per level in a "Price Trace" sheet, exit when the base is not a pricelist or the depth passes 10.
   - A count `loop` then applies the levels from the deepest back to the top. Call PBP "Convert amount" when the base pricelist's currency differs.
   - This avoids recursion (Q3) and gives the price checker its "which rule applied" trace.
   - Simple pricelists (no chain) skip both loops.
6. Loop prevention when rules are saved: keep EMS's idea of a chain text per pricelist (`#a#b#`) that filters the "other pricelist" picker [EMS]. Detect loops with a condition loop plus `get_single`, not EMS's code.

### 5.4 Currencies (#13)

**PBP "Convert amount"** (inputs: amount, from currency, to currency, date):
- `branch` from = to → return the amount.
- For each currency: `get_single` Rates where Currency = c and Date ≤ date, sorted by date desc. No data → `get_single` sorted by date asc (Odoo's fallback). Still none → 1.0.
- `compute` amount × rate(to) ÷ rate(from), then `ROUND(x / rounding, 0) * rounding` with the target currency's rounding. Odoo's `_convert` works this way.

**Current rate:**
- Rates create, update or delete → `get_single` the latest rate dated today or earlier → `update_record` the currency's Current Rate and Inverse Rate.
- A daily run at 00:05 (`sub_process` over active currencies) catches rates dated in the future that become current.

### 5.5 Activity state (#14)

Odoo compares the deadline with the assignee's "today" (`_compute_state_from_date`).

**On save:** Activities create-or-update (Due Date, Active) → `compute` today = date-only of `nowTime` (`DATEADD(DATENOW(), "+0d", 1)`) → `branch`: Due Date = today (date window `today`) → Today; Due Date < today → Overdue; else Planned → `update_record` State.

**Daily:** scheduled 00:05.
- Three query-and-batch-update nodes:
  - Active, State ≠ Overdue, Due < today → Overdue.
  - Active, State ≠ Today, Due = today → Today.
  - Active, State ≠ Planned, Due > today → Planned.
- Each takes at most 1,000 rows, so wrap them in a condition loop that repeats while a `rollup` count of rows still to change is above 0.
- Usually only the rows that cross midnight change.

**Alternative:** two date-field flows per activity (on the due date at 00:00 → Today; the next day at 00:00 → Overdue). Exact timing and no 1,000-row limit, but 2 executions per activity.

**Time zone:**
- Native "now", date windows and scheduled times run on server time. That is UTC+8 per [Doc], which is Malaysian time; Malaysia has no daylight saving.
- If Q1 shows UTC, use `DATEADD(DATENOW(), "+8h", 2)` before taking the date, and schedule at 16:05.
- Do **not** compute today in a code block, whose clock is UTC [EMS].

**Due notice:** a date-field flow on Due Date (08:00 on the day) → `cc` to the assignee. EMS's `Activity Due Reminder` fires 15 minutes before a date-time [EMS].

### 5.6 Activities: done, next, plans (#15, #16)

**Mark Done** (button on one active record; dialog: Feedback) [Design]:
- `update_record`: Active off (Odoo `_action_done` archives done activities), State Done, Done Date (`nowTime`), Done By (`triggeraid`), Feedback.
- `get_single` the activity type → `branch` chaining = trigger and a next type exists.
- `compute` the next due date: base = this due date (delay from the previous deadline) or today (delay from completion), with `DATEADD(base, CONCAT("+", n, "d" or "M"), 1)`; weeks become days × 7.
- `create_record` the next activity: type, default summary, assignee (type default or same), due date, and the document link fields and typed relation copied.
- `cc` or `notice` to the assignee; `push` toast or open the new record.
- Button flows can be strictly sequential by partition on the activity, which stops double clicks.

**Done & Schedule Next:** same, with the next type, due date and summary taken from the dialog.

**Launch Plan** (#16; button with "create a related record": an Activity Plan Launches row with plan, plan date (default today) and on-demand assignee; document fields prefilled) [Design]:
- Launches **create-only** flow.
- `rollup` count of on-demand steps; `branch` with no assignee → `notice` and stop. Odoo refuses the launch in this case.
- `get_multiple` the plan's steps sorted by sequence → `sub_process`, parallel and waiting, with parameters: launch id, plan date, on-demand assignee, document fields.
- Each step: `compute` `DATEADD(plan date, CONCAT(before ? "-" : "+", n, unit), 1)` → `branch` on the assignment rule (fixed member, on demand, record owner via `get_single` on the document) → `create_record` the activity with a relation to the launch (the launch then lists its activities through the reverse relation).
- `update_record` the launch as done.
- EMS built the same chain and used a code block only for the date [EMS]. The DATEADD step replaces it.

### 5.7 Can a fill-in node be the activity to-do?

**What it gives** [Doc]:
- A task in the user's To-Do centre and a message, with summary fields: type, summary, document, due date.
- A deadline from the Due Date field plus a time. The task is marked **overdue** after it, and the remaining or overdue time is shown (documented for approvals; fill-in "treated as overdue").
- Reminders before or after the deadline, repeating up to 10 times, also to a supervisor.
- On overdue: submit automatically, end the workflow, or keep waiting.
- A form with Feedback editable, the button renamed "Mark Done", stash, forward (reassign), e-mail copy.
- After submit, the same flow archives the activity and schedules the next one, with no button needed.

**What the To-Do centre shows** [Doc]:
- Where: on the web, the To-Do icon on the home page or inside an app; on mobile, Home › My Workflow.
- **Approve & Fill in:** waiting approvals and fill-ins as cards with summary fields; batch approval for approvals only.
- **CC:** CC-node items, cleared when read; internal notifications do **not** appear.
- **Submit:** flows I started that still wait; recall and nudge.
- **Completed:** this and last year; older items under history.
- Badge: approvals plus fill-ins, capped at 99; a red dot when only CC is waiting.
- Filters: initiator, organisation, app, workflow type. Search: words combined with AND, summary field only.
- Default sort: **overdue and unprocessed first**.
- Users can delegate approvals and fill-ins for a period (not CC).
- CLI: `hap approval todo --type 3`, `todo-count`, `approval submit`.

**What it cannot do:**
1. It closes only by **Submit** from the to-do or the message. A button, a direct edit, or the daily state flow leaves the task open [Doc].
2. Cancelling or rescheduling from the record has no native "end that other run" node. Nocoly's own recipe calls the organisation API from a Send API Request node, after a **code block** builds the SHA-256 signature [Doc]. An app admin can end it from History [Doc]. Inside an approval block, the documentation gives ending it from the record to app admins [Doc]; whether a regular user can is Q9.
3. While the task waits, the same flow cannot start again for that activity (rule 1).
4. Overdue is a to-do attribute, not a field. Views, filters and the "My Activities" page still need the stored State (#14).
5. Whether a deadline from a date field moves when the date is changed later is not documented (Q8).
6. Each activity keeps one open run. Executions and waiting runs grow with the number of activities.
7. EMS never used fill-in or approval nodes, so there is no Nocoly evidence yet [EMS].

**Verdict** [Design]:
- Keep the Activities sheet as the record of truth: State, buttons, the daily refresh, and CC or notifications for "due today".
- Pilot the fill-in to-do in the Activities batch on one activity type, as the build log already plans. Mark Done would then come only from the to-do, and Cancel or Reschedule would go through the form itself: an Outcome field (Done / Cancel / Reschedule) and a branch. A reschedule waits again with Jump To (at most 20 jumps per run).
- Go further only if Q8 and Q9 pass.

## 6. EMS code blocks: what they did and the native replacement

EMS has 205 code nodes in 108 flows. 64 of those flows are Inventory flows [EMS].

| Purpose in EMS | Examples | Native replacement | Native? |
|---|---|---|---|
| Date arithmetic | `Calculate Activity Due Date` (3 plan flows), `Calculate Manual Snooze date`, `Compute the Due Date from the lines` (payment terms), return date "now (MYT)" | Calculation date mode or `DATEADD` with a CONCAT offset; Branch for the unit. The code also added 8 h to a UTC clock, which native time does not need | Yes |
| Path and key strings | `Compute full path`, `Compute descendant path` (prefix swap), keys | `CONCAT`, `SUBSTITUTE(text, old, new, 1)`; EMS States already used a `CONCAT` function node | Yes |
| Graph walks | `Pricelists: chain and loop check › Follow the chain` | Condition loop + `get_single`, or a stored path with `INCLUDE` | Yes |
| Rule matching and pricing | `Order Lines: price from the pricelist › Work out the price` (all rules into code, ≤ 100) | One sorted `get_single` + Branch + Calculation (§5.3), with no row cap | Yes |
| Unit maths | `Inventory - Detailed Quantity in Move Unit › Convert` | Calculation number mode | Yes |
| Messages to the user | "What to tell the presser" (about 10 flows) | Template text + Branch + Interface Push or notification | Yes |
| Clearing a relation | `Empty Relation Value` | `update_record` with `op: clear` | Yes |
| Tax grouping, e-invoice JSON, LHDN answers, consolidation | MyInvois and invoice flows | JSON building and hashing; Integrated API covers the calls | Partly; keep code (outside wave 0) |
| Inventory planning | allocation, putaway (21 code nodes in one flow), counts, scrap, backorders, 16 "ID reader" loops with 2 code nodes each | Large set maths under the 100-row and 10 s limits | Out of scope here |

## 7. Open questions that only a live test can settle

Run each in a scratch flow on a `TEST …` record in Odoo Replica (AI), after Li Wei approves it. Read back, check in the UI, then delete.

| # | Question | Matters for | Smallest test |
|---|---|---|---|
| Q1 | Do native "now", date windows and scheduled triggers use UTC+8 on this tenant, as [Doc] says? | #13, #14, #16 | Scheduled flow at a chosen minute writes `nowTime` and `DATEADD(DATENOW(),"+0d",1)` to a text field; compare with the clock |
| Q2 | Which zone does the workflow date window `today` use: app time zone or server? | #14 | Set the app time zone to Kuala Lumpur; branch on Due Date = today around midnight, or with a record dated yesterday and today |
| Q3 | Can a sub-process or a PBP call itself (recursion)? How deep can calls nest? | #7, #12 (designs avoid it) | A PBP that calls itself with depth − 1 |
| Q4 | Can a sub-process hold a sub-process that holds a sub-process (three levels) when built by `batch-add`? EMS has three levels built earlier | #8 | Three-level dummy flow |
| Q5 | One `create_record` writing a multi-relation from another record's relation **plus** one more record (`kind: field` and `kind: record` with `op: append`) | #8 | Create one Build Row and read its PTAVs back |
| Q6 | How many OR-groups can a `get_single` condition hold? Can "is one of" take several dynamic values? Does "ignore empty values" drop a whole group? | #12 | Query with 8 groups × 6 conditions on a test sheet |
| Q7 | Workflow condition "multi-relation contains this record" (for a relation that holds many) | #11, #12 | `get_multiple` on PTAVs by a Variants relation = record id |
| Q8 | Fill-in time limit from a date field: the `schedule` keys, the to-do display, reminders, and whether the deadline moves when the date changes | #15 | One fill-in to self (`trigger --debug`), deadline in 10 minutes, then move the date |
| Q9 | Can a regular user (not admin) close or cancel a waiting fill-in from the record, e.g. inside an approval block? | #15 | Approval block with one fill-in |
| Q10 | Does a record created by a PBP or sub-process count as the calling flow's own write (rule 2), or does it start the calling flow? | #8, #15 | Flow A calls a PBP that creates a record on A's trigger sheet |
| Q11 | Confirm `executeType` 2 and 4 and the partition field on a create-only trigger; confirm update triggers offer no serial mode | #2, #6, #8 | Read `config-get` after setting each mode in the UI |
| Q12 | Date-field trigger for a date already past when saved: does it fire, skip or fire late? | #14, #15 | Create a record due 5 minutes ago |
| Q13 | Does `ROUND` round half up (Odoo `float_round`)? Precision of factors such as 1/12 over long chains | #7, #12, #13 | Calculation of `ROUND(2.5,0)`, `ROUND(-2.5,0)`, `1/12*12` |
| Q14 | A set-targeted `update_record` with a template that names the set's own columns: is it evaluated per record? | #1, #2 | Batch-update 3 people with a template that uses each person's name |
| Q15 | Real row caps here: a set into a sub-process (10,000 / 50,000 / 1,000,000), batch add 100, batch update 1,000 | #8, #14 | Rollup counts before and after |
| Q16 | Execution usage: loop iterations, sub-process rows, PBP "execute once"; monthly quota of this plan | #8, #12, #14 | Read the billing or usage page before and after a test |
| Q17 | Is an attribute-line subtable row edit a worksheet event on the line sheet? Does deleting a row fire the delete trigger? | #8 | Edit a line in the product form |
| Q18 | Interface Push from a worksheet-event flow: who sees it? | #4 | Save a record that triggers a push |
