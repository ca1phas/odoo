# Nocoly Help digest: workflow, part 1 of 2

| | |
|---|---|
| Slice | `read_pages.py --prefix workflow --part 1/2`: 39 pages, `administrator-intervene` to `node-interface-push` (alphabetical). **All 39 read.** |
| Source | help.nocoly.com, cached 3 Nov 2026 in `knowledge-base/nocoly-mingdao/research/corpus.sqlite`. Text only: screenshots were not cached, so a few examples stop at "as shown below" |
| Written | 23 Nov 2026, for the Odoo rebuild in Odoo Replica (AI) on Nocoly SaaS |
| Status | Docs only. Nothing was run, built, triggered or changed |
| Companions | `workflow-2.md` (part 2: the trigger pages, Loop, Subprocess, Rollup, Update Record, Send API Request / Email / SMS, PBP, parameters, global variables, execution limits). `../workflow-nodes.md` (wave-0 catalogue with CLI and EMS evidence). Where the two overlap they agree; this file adds the approval, fill-in, link, personnel, AI and operations detail |

**Tags**
- **[Doc]:** what a cached page says (3 Nov 2026). Not runtime proof.
- **[Inference]:** my reading or design idea. Not in the docs.
- **[Project]:** an earlier observation in this project, cited with its file.

In §2 every statement is [Doc] unless tagged otherwise, and every "ERP use" line is [Inference]. Names in backticks such as (`node-approve`) are page slugs of `https://help.nocoly.com/workflow/<slug>`. §6 lists every full URL.

## 1. Summary

1. **Approvals are the richest native area.** An Initiate Approval Flow block runs Approval, Fill in, CC and branch nodes as one sub-flow with one result (pass, reject, withdraw, terminate). It shows status fields and a flow chart on the record and writes every approver's action to a subform or related sheet. This covers Odoo's purchase double validation, discount and expense approvals without code.
2. **The Approval node is deep:** Or-Sign and three Co-Sign rules (all, any one, percentage), approval level by level up the department tree, return and resubmit rules, deadlines with auto-approve / reject / terminate, field updates at five stages, comment templates, signatures, password checks, batch and e-mail approval, to-do delegation and admin intervention.
3. **Only create-only, delete and button flows can be serialised** (Sequential, Strictly Sequential, Strict Serial Execution by Partition, e.g. per Product). Update-triggered flows always run in parallel, and a record runs only one instance of a workflow at a time.
4. **Row caps shape every batch design:** a Get Multiple Data set feeding Add / Update / Delete / Code is capped at 100 rows, and more terminates the run. Query-and-batch-update or -delete and related-record reads stop at 1,000. A subprocess takes up to 10,000.
5. **Get Single Data is the native search and upsert:** AND/OR filters, sort, first or random record, "Create a Record and Continue", Has Data / No Data branches, and query-and-update that hands back the pre-update values (stock deduction with rollback).
6. **The Calculation node works across records** (numbers, date add/subtract, date differences, functions), while formula fields see only their own record. **Calibrate** refreshes rollups and stored lookups for one record at once, or for a whole sheet in the background (≤100,000 rows, once per 120 minutes).
7. **Fill in is a structured human task** with field permissions, deadlines, up to 10 reminders and auto-submit or terminate when overdue. It completes only by Submit from the to-do or the notification.
8. **Button flows can answer the user.** Interface Push shows a toast or card, or opens the new record, a draft creation form, a view, a page or a link, provided no waiting node comes before it.
9. **Integration is mostly native:** Call Integrated API, OAuth 2.0 client-credentials tokens with caching, Get Link (public read-only or editable links with password and expiry), Create Event (calendar entry and ICS) and Get Page Snapshot (paid plans). Code Block (Node 10.16.3 / Python 3.7.5, ≤100 input rows) stays the last resort.
10. **Operations:** run history with retry from the failed node, version restore (then Update Release), org-wide monitoring with pause and queue alerts, 90-day node input/output logs. **There are no transactions:** withdraw, terminate and failures never undo writes already made.

## 2. Capability inventory

### 2.0 Limits at a glance

| Limit | Value | Applies to | Page |
|---|---|---|---|
| Rows from a Get Multiple Data set into Add Record, Update Record, Delete Record or Code Block | ≤ 100. More **terminates the workflow** | Batch writes | `node-get-multiple-data` |
| Size of a Get Multiple Data result when no limit is set | 100 (the page says 10,000 when the set goes to a subprocess, and still recommends setting 10,000 explicitly) | Query worksheet | `node-get-multiple-data` |
| Query and batch update / Query and batch delete | ≤ 1,000, the first 1,000 by sort. The updated set reused by later nodes: ≤ 100 | One node, no separate write node | `node-get-multiple-data` |
| Get associated records | ≤ 1,000 related records. Beyond that, use Query worksheet | Relation reads | `node-get-multiple-data` |
| Rows passed to a subprocess | ≤ 10,000 | Large batches | `node-get-multiple-data` |
| Code Block input from Get Multiple Data | ≤ 100 rows | Code | `node-code-block` |
| Calibrate Worksheet | ≤ 100,000 records per run; ≥ 120 minutes between runs, otherwise the node is skipped; runs in the background | Recalculation | `node-calibrate` |
| Delay for a duration | days ≤ 999, hours ≤ 23, minutes ≤ 59, seconds ≤ 59; may resume slightly late | Waits | `node-delay` |
| Repeated reminders (Approval, Fill in) | ≤ 10 | Deadlines | `node-approve`, `node-fill-in` |
| Recent comments offered to an approver | 5 | Approval | `node-approve` |
| Password-free approval after one password check | 1 hour (enabled by the super admin) | Approval | `node-approve` |
| Node input/output kept in history | 90 days, when enabled | Debugging | `configuration` |
| Recycle bin for deleted records | 60 days, unless deleted permanently | Delete | `node-delete-record` |
| Page snapshots | 100 per hour per organisation; paid plans only | Get Page Snapshot | `node-get-snapshot` |
| OAuth 2.0 token lifetime | default 7,200 s; range 0–604,800 s; 0 = no caching | Authentication | `node-api-connectivity-authentication` |
| AI Agent: record discussions read | 50 most recent | AI Agent tool | `node-ai-agent` |
| AI Agent: records exposed from a tool call | the first row only | AI Agent output | `node-ai-agent` |
| Get Link password | letters and numbers, ≥ 4 characters | Public links | `node-get-link` |
| Fill-in e-mail copy | 0.002 credits per message | Fill in | `node-fill-in` |
| Interface Push nodes that run | only the first one in a run | Button flows | `node-interface-push` |
| Running instances | one per record per workflow | Record triggers | `in-queue`, `history-versions` |
| Workflow owner | exactly one per workflow | Error notices, empty assignees | `configuration` |
| Calculation rounding | 2 decimals by default | Calculation | `node-calculation` |
| Code runtimes | Node.js v10.16.3; Python 3.7.5 | Code Block | `node-code-block` |
| Call PBP "Execute Once" | not counted as a workflow execution | PBP | `node-call-pbp` |
| Node catalogue size | "40 Workflow Nodes" | — | `create` |

**Not stated in this slice.** These are on part 2's pages (`workflow-execution-limits`, `node-loop`, `node-subflow`, `node-send-api-request`, `package`), see `workflow-2.md`:
- subprocess nesting depth;
- loop iteration cap;
- code-block and API timeouts in seconds;
- monthly execution quotas per plan;
- webhook rate limits.

### 2.1 Building and running a workflow (`create`, `introduction`)

- **Structure:** one trigger plus one or more action nodes. Add a node with "+" under the node before it.
- **Who and where:** app administrators, from the app's workflow icon › Workflow Management › Create Workflow.
- **Steps:** select and configure a trigger → add action nodes → set execution options and parameters → save and **Test** (pick a record) → **Publish**.
  - After later changes, click **Update Release**.
  - A workflow must be **enabled** to run automatically.
  - The Workflow Mini Map (canvas overview icon) helps to move around a large flow.
- **Scenarios named by the docs:**
  - automated data processing, including scheduled updates;
  - approvals (sales orders, project changes, leave, hiring, item requests);
  - notifying internal users (system messages) and external users (e-mail, SMS);
  - integration: pushing data out and pulling data in.

### 2.2 Triggers met in this slice

The trigger pages themselves are in part 2. This slice says:

| Trigger | What this slice says | Execution mode (`configuration`) | Interface Push (`node-interface-push`) | ERP use [Inference] |
|---|---|---|---|---|
| **Triggered by Worksheet** | A record is created, updated or deleted. Trigger condition (e.g. "when a record is updated"), filter (e.g. status changed to Completed) and trigger fields (`create`, `auto-data-modification`, `configuration`) | Choosable only for "when a record is created only" and "when a record is deleted". Every other worksheet trigger is Parallel | Not excluded | Confirm, post or cascade on a state change; create-only "queue" sheets for serialised stock work |
| **Triggered on Schedule** | A recurring schedule, e.g. 6:00 PM every weekday (`create`). No record is available after triggering, so query first (`node-get-single-data`) | Parallel | Not available | Nightly jobs: activity state, overdue reminders, reorder checks, rate import, KPI e-mails |
| **Triggered by Date Field** | Runs when the date or time in a field is reached, e.g. Birthday (`create`) | Parallel | Not available | Payment-due and contract-expiry reminders, quotation expiry, receipt reminders |
| **Triggered by Member Events** | A member joins or leaves the organisation (`create`) | Parallel | — | Keep an Employees sheet in sync; reassign a leaver's leads and to-dos |
| **Triggered by External User** | A portal user registers, logs in, closes the account or is disabled (`create`) | Parallel | — | Link a new portal user to its Contact; welcome e-mail |
| **Triggered by Webhook** | An external system pushes data; HAP then runs the actions (`create`). Custom responses exist (`node-abort-the-process`) | Parallel | Not available | Inbound e-commerce orders, payment notices, courier status |
| **Custom action (button)** | Runs on one record, or on several selected records in bulk (`configuration`) | Choosable: all four modes | Available, if no waiting node comes first | Odoo's action buttons: Confirm, Validate, Create Invoice, Register Payment |
| **Subprocess / packaged business process (PBP)** | The mode is set on the calling Subprocess or Call PBP node; parameters are passed in (`configuration`, `node-call-pbp`) | Set by the calling node | Not in subprocesses. A button flow converted into a subprocess does not push | Per-line processing; shared functions (price, unit, currency) |
| **Initiate Approval Flow block** | Behaves as a sub-flow with its own owner and initiator (`node-initiate-approval-flow`) | — | — | Approval of one document |
| **ChatBot workflow** | Named only: AI Agent "Memory Turns" work here (`node-ai-agent`) | — | — | An assistant over ERP data |

### 2.3 Workflow-level settings (`configuration`)

**Basic settings**
- **Workflow Error Notifications:** the owner is always notified; "Notify Additional Members" adds others. Repeated notices for the same error can be suppressed for a set period.
- **Workflow Owner:** the creator by default; can be changed; one owner per workflow. *Conflict:* `all-workflows-management` says "Workflow creators cannot transfer ownership".
- **Operation Mode:** Parallel / Sequential / Strictly Sequential / Strict Serial Execution by Partition.
  - **Where it can be set:** only for flows triggered "when a record is created only", "when a record is deleted" and by a custom action (button). All other triggers run Parallel and cannot be changed. For subprocesses and PBPs the calling node decides.
  - **Parallel:** instances run at the same time, in no fixed order; highest throughput.
  - **Sequential:** instances *start* one by one, in a defined order:
    - records picked one by one before a bulk action: in the order they were picked;
    - all records selected: top to bottom in the current sort order;
    - new records: in creation order.

    The next instance may start before the current one ends: when it finishes, fails, or reaches a Delay, Approval, Fill in, Subprocess or PBP node.
  - **Subprocess wording (unclear):** with "Wait until the subprocess finishes before continuing" ticked, the page says queued instances do **not** wait for the subprocess, so the next one starts once the current one enters it. Unticked, the next one starts when the current main flow finishes.
  - **Strictly Sequential:** the next instance starts only when the current run ends, including all its subprocesses and PBPs, or when it fails. One global queue; lowest throughput.
  - **Strict Serial Execution by Partition:** one strict queue per value of a partition field; different partitions run at the same time.
    - Choose a stable field that names the contested object: product, material, account, customer or order.
    - Never a value that changes during processing. The page's bad example is partitioning by Inventory Quantity.
- **Data Formatting**
  - **Decimal Places for Numeric Fields:** a branch condition compares either the original value or the value rounded to the field's display decimals. Branch nodes only; every other node uses the original value.
  - **Date and Time Precision for System Fields:** minutes (default) or seconds.
    - It covers Created Time, Approval Initiated Time, Node Start Time, Remaining Time, Workflow Trigger Time, date/time workflow parameters, and the Calculation node's Date + Time output.
    - The current system time is always to the second.
    - It mainly affects Code Block, Calculation and other date nodes.
    - **In Get Data query conditions, Equals and Does Not Equal compare by day; other operators compare to the second.**
- **Text Formatting:** Original Value (3141592.6) or Field Format (3,141,592.6) for date, time, number and currency values in approval/CC summaries and in SMS or e-mail text.
- **Save Node Input and Output parameters:** keeps each node's input and output in the run history for 90 days. Dynamic fields show the value at run time.
- **Initiator View:** whether the flow appears under To-do › Submit for the user who triggered it.
  - Off by default.
  - Switched on automatically when an Approval, Fill in or CC node is added. Nodes added inside an Initiate Approval Flow block do not switch it on.
- **Trigger Other Workflows:** whether this flow's record writes can start other flows.
  - **Trigger Allowed.** If this flow and another automatic flow trigger on the same worksheet, the other flow must have a trigger field to start. This requirement does not apply when this flow was started by a button.
  - **Trigger Only Specified Workflows.** The chosen flows can be in this app or other apps.
  - **Trigger Not Allowed.** This blocks only the workflow's own writes. Manual changes, such as a button that creates a record directly, still trigger other flows.

**Manual node settings.** These apply only to Approval nodes placed directly in a workflow, not inside an Initiate Approval Flow block.
- **Withdraw and Nudge:** the triggering user can withdraw or nudge from To-do › Submit.
  - You can name the approval node after which withdrawal is no longer allowed.
  - Withdrawing terminates the flow at once and does **not** undo nodes that already ran.
  - Admins see withdrawals in the run history.
- **Auto-Approval Settings**
  1. Auto-approve when the triggering user is the approver.
  2. Auto-approve if the approver has already approved the same record earlier.
  3. Auto-approve when there is no valid approver.
  4. Validate Required Fields, for cases 1 and 2: required fields on the node block auto-approval. Case 3 always auto-approves.
- **Notification Nodes:** whether the triggering user receives CC and internal notifications. If that user is the only recipient, the node is skipped.

**Workflow parameters**
- Temporary variables for one run; cleared when the run ends.
- Types: text, numeric (including currency), date/time, member, department.
- Names start with a letter and may contain numbers and underscores.
- Set by an Update Parameters node, or by a Subprocess node that fills the subprocess's own parameters (as their initial values).

**ERP use [Inference]:**
- Strict Serial Execution by Partition on create-only stock-move or reservation flows, keyed by Product (or a Product + Location key), is the native stand-in for Odoo's row locks on stock quants.
- "Trigger Only Specified Workflows" stops cascades between sheets.
- Seconds precision helps audit timestamps.

### 2.4 Record nodes

**Add Record** (`node-add-record`)
- **Does:** creates one record in a chosen worksheet, or many when fed by a Get Multiple Data node.
- **Options:**
  - worksheet;
  - how records are added: single, or batch from a Get Multiple Data node;
  - each field's value: fixed, from an earlier node, or both;
  - link the new record to the triggering record.
- **Field rules:**
  - Relation fields take only records from related worksheets that earlier nodes provide.
  - Text fields take free text, node values or both.
  - Number and currency fields take a fixed value or a node value.
  - Member, date/time and level fields cannot be typed: pick a value or a field of the same type.
  - Formatted types must match the source type: a phone field only from a phone field.
- **Limits:** a batch takes ≤ 100 rows (`node-get-multiple-data`).
- **ERP use [Inference]:** an invoice from a sale order; one stock move per order line; a follow-up activity; a lead from a new contact (the page's example).

**Update Record** (node page in part 2; used in `auto-data-modification` and `node-get-single-data`)
- **Does:** changes fields of the triggering record, a retrieved record, or a set of records.
- **Examples:**
  - Task Status becomes Completed → Completion Time = System Current Time (trigger: on update, filtered on the status change).
  - Project Status becomes Completed → every related Task's Status = Completed.
- **Limits:** a set takes ≤ 100 rows (`node-get-multiple-data`).
- **ERP use [Inference]:** stamp confirmation dates, set states, cascade a status to lines.

**Delete Record** (`node-delete-record`)
- **Options:** the record or records to delete; "Permanently delete record (skip recycle bin)".
- **Limits:** without the permanent option, deleted records can be restored from the recycle bin for 60 days. Permanent deletion cannot be restored. The worksheet log records every deletion.
- **ERP use [Inference]:** remove draft lines. The page's example deletes a rejected purchase request. For Odoo parity prefer a Cancelled state, because Odoo refuses to delete confirmed documents.

**Get Single Data** (`node-get-single-data`)
- **Does:** finds one record to update, delete or read in later nodes.
- **Methods:**
  - *Query and Update Record:* filters and sort find one record, which is updated in the same node. Can hand the pre-update values to later nodes. No random pick.
  - *Query and Delete Record:* no random pick; permanent deletion available.
  - *Query Worksheet:* read only; random pick allowed.
  - *From Multiple Records:* one row of a Get Multiple Data result.
  - *Retrieve Related Record:* through a relation field or a subform.
  - *From Record Link:* parses a record link held in a text field. Supported: internal record-sharing QR links, and external QR links from system print or Word print.
- **Options:**
  - worksheet;
  - filter conditions with fixed or dynamic values, in AND/OR groups;
  - **Ignore Condition Errors:** on, a broken condition (e.g. a deleted field) skips the query and the flow goes on; off, the node fails, stops the flow and notifies the configured people;
  - **Ignore Empty Values:** a condition whose value is empty is dropped. If it was the only condition, there is no filter at all;
  - sorting: the first record wins;
  - Random Retrieval.
- **When no record is found:**
  - *Continue:* later nodes that need the record may be skipped or get empty values.
  - *Create a Record and Continue:* creates the record and passes it on. If a unique index rejects it, the flow stops, or, with "Continue on failure" ticked, goes on with empty data.
  - *Stop or Branch Based on Result:* takes the No Data branch if a branch follows; otherwise stops.
- **Query and Update output for later nodes:**
  - *Use pre-update data:* later nodes see the values before the update;
  - *Use latest data:* later nodes read live values, which may include other workflows' changes.
- **Missing-record rules:** a later node that acts on the record (update, delete) is skipped. A later node that only reads its fields gets empty values and still runs.
- **Tips:**
  - Retrieve Related Record returns one record even when several are linked; use Get Multiple Data for all of them.
  - Query Worksheet is "generally faster" than reading through the relation.
  - Scheduled flows have no record until one is queried.
- **ERP use [Inference]:**
  - find-or-create a customer on lead conversion (the page's example);
  - the current price rule or currency rate (sort by date, newest first);
  - stock deduction with rollback when stock is short (the page's example);
  - scan the QR code on a printed picking or order to fetch the record.

**Get Multiple Data** (`node-get-multiple-data`)
- **Does:** retrieves many rows, worksheet records or array rows, for batch writes, batch inserts or subprocesses.
- **Seven methods:**
  1. *Query and batch update:* ≤ 1,000 records, the first 1,000 by sort; later nodes can reuse ≤ 100 of them.
  2. *Query and batch delete:* ≤ 1,000; permanent deletion available.
  3. *Query worksheet:* into Add / Update / Delete Record or Code Block ≤ 100, otherwise the workflow terminates; into a subprocess ≤ 10,000.
  4. *Get associated records:* ≤ 1,000. Set the source record, the relation field (multiple), a filter, a sort and a limit.
  5. *Get new data in bulk:* the rows that a batch Add Record just created.
  6. *Get operation details:* operator, time, comments and signature from an Approval or Fill in node.
  7. *Get object array:* converts an object array from Code Block, Send API Request or PBP output, or a PBP's object-array input, into rows.
- **Options:**
  - sort order, or random;
  - limit to the first N, fixed or from a numeric field;
  - Access mode: **Direct access** (one result kept for all later nodes) or **Dynamic retrieval during each use** (each later node runs the query again).
- **ERP use [Inference]:** read order lines; batch-update states (≤ 1,000); feed per-line subprocesses; turn an API's JSON array (rates, tracking events) into rows; approval audit rows.

**Calibrate** (`node-calibrate`)
- **Does:** the same as the worksheet's Batch Refresh Data. It recalculates "delayed" fields: formula, rollup, foreign field (stored data), concatenation and option fields.
- **Options:**
  - *Calibrate Single Record:* immediate; later nodes can use the new values.
  - *Calibrate Worksheet:* every record matching the filters (calculations, option sorting and values, stored foreign fields, rollups).
- **Limits of worksheet mode:**
  - runs in the background, so later nodes cannot use the refreshed values;
  - ≤ 100,000 records per run (split by filters for more);
  - ≥ 120 minutes between runs, otherwise the node is skipped.
- **[Project]** Manual calibration (校准) in the UI is also limited to app admins and to once per worksheet per 2 hours (memory note `hap-foreign-field-storage-modes`, 23 Nov 2026). Whether the node and the manual action share that window is unknown.
- **ERP use [Inference]:** refresh an order's rollup total before an amount-based approval branch; refresh stored lookups overnight after master-data changes.

### 2.5 Logic and time

**Branch** (`node-branch`)
- **Types:**
  - **Parallel Branch:** every branch whose conditions match runs, left to right. The next branch starts when the one before it finishes, unless that branch reaches a waiting node (delay, approval, fill in, subprocess).
  - **Exclusive Branch:** only the first matching branch from the left runs. A last branch with no condition is the "else".
  - Parallel and Exclusive can be switched: a circle icon for Parallel, an X icon for Exclusive.
  - **Branch Based on Approval Result:** Agree / Reject, after an Approval node.
  - **Branch Based on Data Retrieval Result:** Has Data / No Data, after Get Single Data.
- **Flow:** after the branches finish, the workflow rejoins the main path.
- **Operations (Parallel and Exclusive only):**
  - add a branch, or copy one (its conditions only, or its conditions and nodes);
  - expand or collapse;
  - reorder: one place left or right, or to the first or last place;
  - delete. With only two branches left, deleting one keeps the other's nodes as a plain path and drops its conditions.
- **Notes:**
  - Get Multiple Data has no Has Data branch: count its rows with a Rollup node and test for > 0.
  - Without an approval-result branch, a rejection ends the workflow.
- **ERP use [Inference]:** amount thresholds, route choice, find-or-create, state machines.

**Calculation** (`node-calculation`)
- **Does:** computes a value for later nodes and changes no field.
  - Unlike a formula field, it can mix fields of different records and worksheets.
  - It runs in the workflow, after the record is saved.
- **Types:**
  - number and currency: a custom formula (+, −, *, / and brackets) or system formulas;
  - duration between two dates;
  - add or subtract time from a date;
  - functions, e.g. YEAR(), REPLACE(), DISTANCE(); the full list is in the Function Reference. Choose the output type.
- **Options:**
  - **Static calculation** (computed once, at the node) or **Dynamic calculation** (computed again each time a later node uses it);
  - "Treat empty calculation field values as 0".
- **Adding or subtracting time:**
  - A – Date;
  - B – Date Format: Date (the time is dropped and 00:00 used) or Date + Time;
  - C – Formula: starts with + or −; units Y, M, d, h, m, case-sensitive; e.g. `+7d+3h-2m`. A numeric field must be followed directly by a unit;
  - D – Output Format.
- **Duration between two dates:**
  - Format 1: start at 00:00, end at 24:00, so 13 to 14 Dec = 2 days;
  - Format 2: both at 00:00, so 13 to 14 Dec = 1 day;
  - values that include a time use their real time; choose the output unit (e.g. days, hours).
- **Behaviour and limits:**
  - results are rounded to 2 decimals by default;
  - an empty operand makes the result empty, unless "treat empty as 0" is on;
  - an empty denominator always gives an empty result;
  - a deleted field gives an empty result;
  - with custom operators (e.g. + to join text), an empty value empties the result, while built-in functions treat empties as 0 by default;
  - a result that cannot be converted to the output type is empty (1 + 1 with output type Date).
- **ERP use [Inference]:** line subtotal, tax, discount; currency conversion with a rate from another sheet; due date = invoice date + payment-term days; aging days; lead-time dates; duplicate-check keys.

**Delay** (`node-delay`)
- **Options:**
  - **Resume on a specified date:**
    - the date is typed in or taken from an earlier node;
    - On the Date / Before / After N days;
    - a time of day, default 8:00 AM. A date-time field keeps its own time, and before/after can still be set.
  - **Resume after a specified duration:** M days, N hours, X minutes and Y seconds, fixed or from fields.
- **Limits:** M ≤ 999, N ≤ 23, X ≤ 59, Y ≤ 59. Second precision; may resume slightly later than set.
- **ERP use [Inference]:** a follow-up N days after a quotation is sent; a receipt reminder N days before the expected date; lead rotting.

**Terminate Process** (`node-abort-the-process`)
- **Does:** ends the run; no later node runs.
  - Inside a branch, the other branches and the nodes after the branch do not run either.
  - Running subprocesses, approval processes and PBPs are terminated too.
- **Inside a subprocess or loop:** the calling node's setting decides: "skip and continue" or "terminate main process".
- **Inside a PBP:** output parameters that use values from after the Terminate node return null. The same applies to PBPs with API access and to webhook flows with custom responses.
- **ERP use [Inference]:** guard clauses (stock short, price missing) after a toast; stopping before a half-posted state.

**Named in this slice, documented in part 2**
- **Subprocess:**
  - execution mode and parameters are set on the node;
  - takes ≤ 10,000 rows;
  - termination behaviour as above;
  - no Interface Push inside.
- **Loop:** blocks Interface Push; termination behaviour as above.
- **Rollup:** counts a Get Multiple Data set; also an AI Agent tool.
- **Others:** Update Parameters, Send API Request, Send Email, Send SMS, Update External User Info.

### 2.6 People, approvals and tasks

**Approval** (`node-approve`)
- **Does:** a decision task on one record. After Approve or Reject, branches can update data and send notifications.
- **Setup:** add the node → choose the record (a node that represents it) → approvers and method → the approver's permissions → result branches. Rename nodes so progress reads clearly.
- **Approvers, custom per stage**
  - *Single:* a user from Contacts, the applicant's direct supervisor, or a member field.
  - *Fixed:* users, or by role, position or department.
  - *Dynamic:* from the applicant or a member field, e.g. the direct supervisor or the department head.
  - *Multiple:* by role, department or position, or several users picked by hand.
  - *Positions in main department:* e.g. the person in the main department whose position is "PM".
  - *Org-role manager:* the member of an organisation role who is in charge of the initiator's department.
    - If no member is in charge of that department, members with no departments assigned share it.
    - If every member has departments and none covers it, there is no approver, and the empty-approver rule applies.
  - The next approver can be the direct superior of the previous approver: pick the earlier approval node.
- **Approve level by level** (up the department structure)
  - **Approval starting point:** a member field, usually the initiator; that member's department head is the first level.
    - The page adds that an option is unavailable outside an Initiate Approval Flow block. It seems to mean picking "initiator", but the wording is unclear.
  - **Approver hierarchy cap:** "X level upward" or a named directory level. "2 levels upward" means three approvals: the current level plus two above.
  - **"Only the head of the main department needs to approve":** without it, the heads of all the member's departments approve.
- **Methods when several approvers are involved**
  - **Or-Sign:** the first approver to act decides.
  - **Co-Sign (all must approve):** any rejection rejects.
  - **Co-Sign (approved when one approves, rejected when all reject).**
  - **Co-Sign (approved by proportionate voting):**
    - approvals needed = approvers × ratio, rounded up (4 approvers at 60 % → 3);
    - rejections needed = approvers − approvals needed + 1.
- **Approver actions**
  - **Stash:** save field edits without deciding. Writes the record and is logged.
  - **Reject:** can be left out, so only approve or return remain.
  - **Forward:** with an optional list of candidates.
  - **Add an approver:** before or after oneself; optional candidates.
  - **Return** to an earlier node.
- **Return rules**
  - Targets: Approval nodes, Fill in nodes and the initiating node.
  - A standalone Approval node offers only "all nodes above" and "the initiating node". "A specified node" and "only the previous node" exist only inside an Initiate Approval Flow block.
  - Only Delay, Calculation, Approval, Fill in and CC nodes may sit between the target and the current node, and the target must be on the main path.
  - With "Directly return to approval node", only the initiating node or a Fill in node can be targets.
  - Not possible with "approved when one approves, rejected when all reject".
- **Resubmitting after a return**
  - Custom approvers: **Repeat the flow** / **Return to approval node directly**.
  - Level by level: **Repeat the flow** / **Return to the first level of this node** / **Return to the level where it is returned**.
- **When the approver is empty**
  - **Automatically enter the next node:** no one can later return to this node.
  - **Delegate by the workflow owner.**
  - **Delegate by the specified personnel.**
  - **Terminate the process.**
  - **Use the default settings of the process:** the block's setting or the workflow's. At workflow level, "Automatically approve when approver is empty" approves; otherwise the process is terminated.
- **Notify the initiator of the node result,** with custom text.
- **Approval comments / Signature / Verify login password,** each set separately for approve and reject.
  - Comment templates: several each, with a default; "Free Input" on or off.
  - The approver's last 5 comments are offered.
  - The super admin can allow password-free approval for 1 hour.
- **"No need to fill out form fields when reject/return":** required fields are not enforced, and entries are not saved.
- **Allow batch approval:** from To-do › Approve; required fields and comment requirements are ignored.
- **Allow check-list approval:** approve and reject buttons on the record page, in e-mail notifications and in Feishu; required fields are ignored.
- **E-mail notification**
  - "Quick approval in email" puts approve, reject and return buttons in the e-mail. Required fields, signatures and comments are then ignored.
  - Summary fields add detail to the e-mail; attachments are supported.
  - Sender name is customisable; default is the platform name.
  - E-mail style: session mode or standard mode.
- **Time-limited processing**
  - Deadline: *Custom* (X days, hours or minutes after the node is reached) or *a date field* (with a fixed time when the field has no time).
  - Reminders before or after the deadline, to approvers and others such as their supervisor.
  - "Repeat reminder" continues after the deadline, up to 10 times. Several reminder sets are possible.
  - After timeout: **Automatic approval** / **Automatic rejection** / **Workflow terminated** / **Do nothing**.
  - Approvers see the remaining or overdue time.
- **Field settings**
  - per field: hidden, view, edit, required;
  - summary fields in the to-do list;
  - "New fields are viewable by default";
  - the node's permissions apply regardless of the approver's app role;
  - record edits are logged.
- **Data update:** "Update when approval starts" (runs again when the flow is returned to this node), "after approval", "after rejection", "after return", "during the approval process" (after each co-signer or each level).
  - **Only fields of the current worksheet; not subforms or related worksheets.**
- **Other settings**
  - Approver in action: the first operator, a forwardee, or added approvers.
  - Approval instructions.
  - Custom labels and descriptions for the Approve, Reject and Return buttons.
  - Alert tone: a fixed audio file or text-to-speech. When the user is online on both PC and app, it plays on the PC only.
- **Auto-pass** is set for the whole workflow. Inside a block, the block's setting applies.
- **ERP use [Inference]:** purchase order approval above an amount, discount approval, vendor bill approval, credit-limit override, inventory adjustment approval, expense approval (wave 4).

**Initiate Approval Flow** (`node-initiate-approval-flow`; admin side in `administrator-intervene`)
- **Does:** a block that behaves as a sub-flow.
  - Inside: Approval, Fill in and CC nodes, conditional branches, and data nodes.
  - It ends with one result: pass, reject, withdraw or terminate.
  - Branches on that result go **outside** the block: Approve, Reject, Withdraw, Terminate.
- **Create**
  - **Create new workflow**, or **Copy from approval workflow**: copies the structure only; reselect the approval object and approvers.
  - Copying from other apps is allowed, and the copy is a new flow.
- **Node settings**
  - **Name:** shown in approval lists, notifications and prints.
  - **Data object:** the record to approve.
  - **To-do title:** fixed text plus fields; defaults to the record title.
  - **Initiator:** one person from the record. Not necessarily the user who triggered the main flow.
  - **Initiator operations:**
    - "Allow the initiator to withdraw the process", optionally not after a given node. Re-initiating then either repeats the flow, or goes "back to the time of the withdrawal of the node";
    - "Allow initiator to nudge";
    - "Allow the initiator to view the approval comments", chosen per node.
  - **When the initiator is empty:** Automatically enter the next node / Delegate by the workflow owner / Delegate by the specified personnel / Terminate the process.
  - **Default for an empty approver or filler:** used when the Approval or Fill in node has no rule of its own.
  - **"When there is no superior in charge, handle by the current personnel":** when the approver is a superior or the superior department's head and none exists, the current person handles it (falling back to the department head where needed). Unticked, the empty-approver rule applies.
  - **"Verify node owner's record view permission":** ticked, an approver without view permission on the worksheet cannot view or approve, but can "forward to the process owner". Batch operations are not affected. Unticked, the node's field settings govern.
  - **Owner of the approval flow:** receives tasks when the initiator, approver or filler is empty.
  - **Automatic approval:** when the approver is the initiator; when the approver already approved earlier.
    - Not when a required field is empty.
    - Not on a node set as mandatory.
  - **Field settings for the initiator:** view, edit and required when they resubmit after a withdrawal or a return. Without them, the initiator's worksheet permissions apply.
  - **Summary fields:** shown in the approval to-do and in e-mails; the default for new Approval nodes.
  - **Print template:** Word, Excel and system templates, ordered by drag. **Not** templates with QR codes or barcodes.
- **Showing approvals on the record**
  - Worksheet "Function Switch" page: enable the approval system fields and the approval details. "Show Flow Chart" controls the flow-chart entry.
  - **System fields:** Workflow Name, Status, Approval Completion Time, Node Owner, Node Start Time, Node Remaining Time, Initiator, Initiation Time.
  - They can be shown in table views once enabled in the view settings.
  - **Status:** active, pass, reject, terminate. While active, views show the current node's name, e.g. "Approve by Supervisor".
  - These fields cannot be changed by workflows or by hand.
- **Automatic status update when returned to the initiator,** e.g. Status = Returned. Returns to an approver are set in the Approval node.
- **Approval operation details** can be mapped into a subform or related worksheet.
  - Fields: Node name, Operation object ID, Operator, Entry time, Operation time, Operation, Note, Signature.
  - Or-Sign: only the person who acted (plus any added approvers).
  - Co-Sign: every approver, including those who did not need to act under percentage voting.
  - Level by level: one row per level.
- **Parallel approval inside the block:** a new branch is Exclusive by default. A Parallel branch runs all matching branches at once, and any rejection rejects the whole flow. Their approval cards appear together.
- **Management:** block flows also appear in the app's Approval Flow tab with details and history.
- **ERP use [Inference]:** the default for any document approval (purchase order, sales discount, vendor bill, expense), because it gives status fields in views, a flow chart, history rows and print templates.

**Fill in** (`node-fill-in`)
- **Does:** asks a person to complete fields on one record; the flow waits until they submit.
- **Options**
  - Node name, shown in the notification.
  - **Fill-in Target:** the record.
  - **Assignee:** fixed users from Contacts, or by Department, Position or Application role. Everyone matching is notified, and **the first to submit completes the task**.
  - **Field permissions:** hidden, read-only (the default), optional or required, in form order. "New fields are visible by default".
  - Summary fields in the to-do list.
  - **Customize Button Name** (default "Submit"); **Fill-in Instructions**; notification sound (fixed audio or text-to-speech; PC only when both PC and app are online).
  - **Stash:** save without submitting.
  - **Forward:** to any user, or only to listed candidates.
  - **Login Password Verification.**
- **Enable Time Limit**
  - Deadline: *Custom Time* (X days, hours or minutes after the notification) or *Based on a Date Field* plus a time.
  - Reminders before or after the deadline, to the assignee and others such as the supervisor. "Repeat Reminder" sends up to 10.
  - When overdue: **Automatically submit** / **Terminate the workflow** / **Do nothing and continue waiting**.
- **Other settings**
  - Empty assignee: handled as in Approval.
  - **Enable Email Notification:** 0.002 credits per message.
  - **Data Update:** "Update When Node Starts" and "Update After Submission".
  - Later nodes can refer to the **assigned fill-in user** or the **actual executor**: different after a forward, or when a position has several people.
- **Limits**
  - Only Submit from the workflow notification or the to-do list completes the task. Editing the record in the worksheet does not.
  - The assignee can view and edit the record whatever their role.
- **ERP use [Inference]:** assign a technician (the page's example); a quality-check form; a delivery confirmation; an Odoo activity with a deadline and feedback.

**CC** (`node-cc-send-internal-notification`)
- **Does:** a message with a record link. It appears under To-Do › CC, and the counter drops only when the recipient opens the record ("Read" and "All Clear" clear it in the to-do list).
- **Options**
  - **Data object.**
  - **View:** recipients who can open that view see the record as the view shows it, can edit fields and can click custom buttons. Others get read-only fields from the view's display list and no buttons.
  - **Recipients:** fixed members or by role. A department field sends to all its members.
  - **Content:** fixed or with node fields. "Show To-Do/Record Title" (otherwise a "View Details" link). The message starts with the node name.
  - Summary fields; alert tone.
  - **Email Notification** with attachments: fixed files, or all files of file fields.
- **ERP use [Inference]:** tell a salesperson about a new lead, with an assign button (the page's example); tell the warehouse about a confirmed order.

**Send Internal Notification** (same page)
- A plain-text system message from "Workflow Message". Not in the to-do list; the counter drops when it is read.
- Fixed or dynamic content; several recipients; alert tone; links in the text are clickable.
- **ERP use [Inference]:** low-stock alerts; "job finished" messages.

**Get Single Personnel (Department / Organization Role)** (`node-get-single-data-from-user`)
- **Does:** reads one member, department or organisation-role object, from a record field or from the directory. Its properties are usable later.
- **Properties**
  - *Member:* name, mobile, e-mail, department, primary department, job title, employee ID, work location, organisation roles, user ID, direct manager, direct reports, all reports, created time.
  - *Department:* name, manager, parent, all parents, direct children, all children, members, members including sub-departments, ID, created time.
  - *Role:* name, description, members, ID, current role, created time.
- **Options**
  - "Get from Member Field";
  - "Search across Organization Departments", with conditions;
  - "Search from All Organization Members, Departments, and Organization Roles": Organization Super Admins and Account Admins only;
  - "Retrieve Reporting Relationships": off by default, for speed;
  - a found / not found branch.
- **Limits**
  - It returns a single object, which cannot feed a subprocess.
  - External collaborators come back with empty organisation properties.
  - It reads members even when their profile is "Visible Only to Me" or hidden from Contacts.
  - All Parent / All Child Departments are arrays: they can be written to a multi-select Department field, or as names in text.
- **ERP use [Inference]:** find an approver (the salesperson's manager); fill Department Members (the page's example); get a user ID for API calls (`endInstance`).

**Get Multiple Personnel (Departments / Organization Roles)** (`node-get-multiple-data-from-user`)
- **Does:** reads many members, departments or roles, from record fields or from the directory, as rows for subprocesses or batch nodes. With no filter it returns every member.
- **Options:** source; filters; "Retrieve Reporting Relationships" (off by default).
- **Output:** can fill multi-select Member, Department or Organization Role fields through Add or Update Record.
- **ERP use [Inference]:** sync an Employees sheet nightly (the page's example: weekdays at 2:00 AM, with a subprocess that updates or creates each employee); sales-team membership.

**Get Single / Multiple External User** (`node-get-external-user`)
- **Does:** reads portal users from an external member field or from the app's portal user list. The results can be used later, or changed with Update External User Info (name, role, status, custom sign-up fields).
- **Multiple:** from an external member field (multi-select), or "Get from Portals" (e.g. only users with normal status).
- **Single:** "Get from field - external user", or "Get from portals" by a unique value such as a phone number.
  - Several matches → the most recently signed-up user.
  - "Get one at random on the basis of filtering" → a random match.
- **Tip:** for a daily sync, do not batch Add Record. Pass the users to a subprocess that looks each one up and updates or adds it.
- **ERP use [Inference]:** link portal customers to Contacts; disable portal access when a customer is blocked.

### 2.7 Links, screens and calendar

**Get Link** (`node-get-link`)
- **Does:** generates a link to a record, for e-mail, SMS, notifications or a URL field.
- **Access Mode**
  - **Share Link:** read-only, no login. "Does not expire unless the record is deleted".
  - **Internal Link:** login and permission needed; the same link as opening the record from a view.
  - **Editable Link:** chosen fields can be edited, and some required, without logging in.
- **Options**
  - **Link Name:** hyperlink text, but in e-mails only; SMS and internal messages show the raw URL. Written to a field, it is stored as a URL.
  - **Password Protection:** letters and numbers, ≥ 4 characters, with a validity of a fixed duration or until a date. Blank = no password.
  - **Set Link Expiry:** a fixed duration, a date and time, or a date field.
  - **Allow Viewing/Modification After Submission** (Editable Link only): read-only afterwards, or editable again at once or after a delay.
  - **Field permissions:** Visible / Editable / Required. A Share Link has view permissions only.
  - "New Fields Default to Viewable"; **Customize Submit Button Label** (default "Submit").
- **ERP use [Inference]:** send a quotation or invoice as a read-only link; let a customer rate a ticket (the page's example) or accept a quotation; let a supplier enter RFQ prices and lead times without logging in; payslips (the page's example).

**Interface Push** (`node-interface-push`)
- **Does:** after a button click, shows a message to the user or opens a page.
- **Notifications**
  - *Toast:* one line at the top of the page; disappears by itself; message and theme colour only; to the initiator only.
  - *Card:* at the bottom of the page; title, description and buttons; can stay until closed; to the initiator or to other users who are logged in. A type such as Success (green).
- **Open a page**
  - the record creation page, optionally with "Create Draft Record", so the record is saved only on Submit;
  - a record detail page: a record from an earlier node, in a modal window or a new browser tab;
  - a worksheet view; a custom page; a link.
- **Limits**
  - Not available in date-field, scheduled, webhook or subprocess flows.
  - No Approval, Fill in, Delay, Subprocess/PBP or Loop node may come between the trigger and the push.
  - A button flow converted into a subprocess does not push, and an invalid link fails.
  - **Only the first Interface Push node in a run is executed.**
- **ERP use [Inference]:** "Create Invoice" then open it; an error toast before Terminate Process; a "New Quotation" button that opens a draft.

**Create Event** (`node-create-event`)
- **Does:** creates a schedule entry in the collaboration calendar, and/or an ICS file.
- **Options**
  - *Create System Schedule:* All-day Schedule (starts at 00:00); Private Schedule (others see only "Busy"); Reminder Before Start in minutes; Generate ICS File.
  - *ICS file only:* Use UTC standard time.
  - The ICS can be written to an attachment field or attached to an e-mail, where a click adds it to the recipient's calendar.
- **ERP use [Inference]:** meetings from CRM visit plans (the page's example uses a button on a Visit Plan sheet); delivery or installation appointments sent to customers.

**Get Page Snapshot** (`node-get-snapshot`)
- **Does:** captures a custom page, a chart or a URL as an image, for an e-mail attachment or a file field.
- **Options**
  - Content: Custom Page; Chart (not charts that have access permissions); URL.
  - Page Width and Height (no height needed for custom pages).
  - Wait Time.
  - Enable SSL Certificate Verification (turn off only on trusted internal networks).
- **Limits:** paid plans only; 100 snapshots per hour per organisation. Pages that need a login cannot be captured; use public share links instead.
- **ERP use [Inference]:** a monthly KPI e-mail like Odoo's digest (the page's example: the Quarterly Orders chart on the 1st of each month).

### 2.8 Integration and code

**Call Integrated API** (`node-call-integrated-api`)
- **Does:** calls an API set up in the Integration Center; later nodes can use the response.
- **Options:** the API; on timeout or failure, stop the workflow or **Continue**. With Continue, dependent values are skipped.
- **Multi-row responses** (e.g. logistics tracking): receive them with Get Multiple Data, then batch-insert with Add Record.
- **ERP use [Inference]:** MyInvois, payment gateways, courier tracking, phone-number lookups (the page's example).

**API Connection and Authentication** (`node-api-connectivity-authentication`)
- **Basic Auth:** outputs "Basic Auth Parameter" = base64encode(username + ":" + password). No scheme prefix is added: check whether the receiving API expects Basic, Bearer or another prefix.
- **OAuth 2.0 – Client Credentials**
  - Access Token URL: GET by default; also POST, PUT, DELETE, HEAD, PATCH.
  - Request parameters can be shown or hidden. URL parameters `app_id` and `app_secret` are present by default.
  - "Get Access Token" sends the request and lists the response.
- **Behaviour and limits**
  - Any JSON response counts as success, even without a token. Every returned parameter is an output.
  - Token lifetime: default 7,200 s, range 0–604,800 s. 0 requests a new token every time; otherwise the cached token is reused and refreshed ahead of expiry.
  - The node is complete only after a response has been obtained.
- **ERP use [Inference]:** tokens for MyInvois or bank APIs without code.

**Call PBP** (`node-call-pbp`)
- **Does:** calls a packaged business process of this app, or of another app in the organisation ("PBP under Other Applications").
- **Options**
  - **Execute Once:** not counted as a workflow execution.
  - **Execute Multiple Times:** as many times as there are source records, or a set number (fixed or from a numeric field).
  - Mode: **Parallel**, or **Execute one by one** (the remaining runs stop after one is terminated).
  - "Wait for the PBP to finish": needed to use the PBP's outputs.
  - Input parameters: fixed or from nodes; those marked * are required.
  - "Use the triggering user of this workflow for the PBP": otherwise the PBP's trigger user is "Workflow".
- **ERP use [Inference]:** shared functions (price for a product, unit conversion, currency conversion); a stock update per line (the page's example: "Stock In" on an inbound order calls "Update Inventory" per line); copy a record N times (the page's example).

**Code Block** (`node-code-block`)
- **Does:** runs JavaScript or Python on workflow data; later nodes use its outputs.
- **Inputs:** number, text, date/time, single select, member and more. Arrays arrive as strings. ≤ 100 rows from Get Multiple Data.
- **Outputs:** text or array.
- **Runtimes**
  - Node.js v10.16.3 with moment, lodash, node-fetch, form-data, xml2js, node-rsa, uuid, pinyin, sm-crypto.
  - Python 3.7.5 with requests, xmltodict, pycryptodome, dingtalk-sdk, beautifulsoup4, rsa, uuid, xpinyin, gmssl, cryptography, lxml, pandas, numpy, matplotlib.
  - API calls from code: SOAP supported; XML, JSON or Form-Data; GET, POST, PUT, DELETE.
- **Usage:** define inputs as key/value pairs ("+ Key/Value Pair") and read them as `input.name`; return `output = {...}`. Outputs exist only after a successful **Test** and a save.
- **Not stated on this page:** timeout and memory.
- **ERP use [Inference]:** the last resort, e.g. the org-API signature in `endInstance`, e-invoice document signing, complex parsing.

**Send API Request (custom)** (named in `endInstance`; node page in part 2)
- A request URL with query parameters, method GET, and a "Test API" button with test values.

### 2.9 AI nodes (charged to organisation credits)

**AI Agent** (`node-ai-agent`)
- **Does:** LLM reasoning with tools inside a workflow.
- **Options**
  - **Model:** e.g. DeepSeek-V3, Qwen-Max, GPT-5, GPT-4o. Blue dots show performance; parameters are optional.
  - **Prompt:** variables, single fields or whole records. Attachment fields named in the prompt are parsed and passed to the model.
  - **File Link:** file fields from earlier nodes. Images need a vision model; documents go through the document analysis service; may cost more.
  - **Memory Turns:** ChatBot flows only.
- **Tools** (Add Tool)
  - Data Processing: Query Records, Add Records, Update Records, Get Record Discussion, Rollup.
  - Notification: internal notifications and e-mail.
  - Call PBP.
  - Call Integrated APIs.
- **Access control**
  - **Set Worksheet Scope:** All Worksheets (the agent picks) or Specific Worksheets (faster, fewer tokens; recommended for sensitive data).
  - **Query Filters:** fixed filters for Query Records and Rollup.
- **Outputs**
  - System fields: AI Generated Result, AI Model, Token Usage.
  - "Fields called by the tool", when a worksheet scope is set.
  - **Structured Output:** named parameters with descriptions.
- **Limits**
  - Query Records uses the HAP API: no vector search (RAG).
  - Get Record Discussions returns the 50 most recent entries and needs the Record ID in the prompt.
  - A tool that returns several records exposes only the first row.
  - Structured-output accuracy depends on the model.
  - Tokens are charged to the organisation's credit balance.
- **Logs:** for every run (test or history), the steps Memory, Agent, File Parsing, Model Selection ("Auto-select Model"), Model and Tool, with token cost. "Feedback to Platform" sends only the prompt, response and tool parameters.
- **ERP use [Inference]:** follow-up reminders (the page's example: high-value customers not contacted for 7 days); document digitisation with structured output; summaries.

**AI Generate Data Object** (`node-ai-generates-data-objects`)
- **Does:** extracts structured values from text into parameters you define (Name, Type, Description).
- **Options:** model, e.g. GPT-4o-mini, GPT-4o, QWen-Turbo, QWen-Plus, QWen-Max, DeepSeek; the price shows once a model is picked. Prompt with fixed text and node values. Test. More Settings: System Message, Temperature.
- **Outputs:** the object parameters, Historical Message (JSON), Tokens Consumed.
- **ERP use [Inference]:** order details from an e-mail text (the page's example); vendor bill fields from text.

**AI Generate Text** (`node-ai-text-generation`)
- **Does:** generates or rewrites text.
- **Options:** model as above (e.g. DeepSeek-V3); prompt, with a panel of prompt templates; Test shows the output and an estimated cost; More Settings: System Message, Temperature.
- **Outputs:** AI-Generated Result, Historical Message (JSON), Tokens Consumed.
- **ERP use [Inference]:** translate product descriptions into Malay (the page's example); draft follow-up e-mails.

### 2.10 Operating and governing workflows

**Run history and versions** (`history-versions`)
- **Instances:** a list with each run's status; a detail page shows every node.
- **Terminate:** app admins, for one run or many. Running subprocesses, approval processes and PBPs end too.
- **Retry:** one run or many. It **resumes from the failed or terminated node**, not from the start.
- **Why a workflow did not start**
  - the trigger conditions failed;
  - the record's previous instance of this workflow is still running;
  - the monthly execution quota is used up.

  To see node data, enable the Node Log and run again.
- **Versions** (Version button): view, rename (default name: publish date plus a number) and restore. **Restoring changes only the design; click Update Release to run it.**

**Queued runs** (`in-queue`)
- **Why runs queue:** in Sequential mode one runs at a time; in Parallel mode the server limits load. The execution service is **shared by all organisations** on the platform.
- **While an admin pauses a workflow,** triggers keep queuing. Queued count = runs queued before the pause + new triggers after it.
- **Per record:** one running instance at a time. Several triggers from the same record during a pause produce **one** run after resuming.

**Organisation management and monitoring** (`all-workflows-management`)
- **Access:** super admins, via profile › Org Admin › App Management › Workflow.
- **Workflow list**
  - every workflow, with this month's execution count;
  - buy an expansion package when executions run short;
  - filter and search; enable or disable; view history;
  - "Workflow creators cannot transfer ownership".
- **Monitor**
  - *Real time:* runs queued now, triggered in the last 5 minutes, and consumed (executed) in the last 5 minutes.
  - *Workflow Queue Alert:* a threshold and the users to notify.
  - *Historical Execution:* by time range.
  - *Execution Details:* queue duration per workflow.
  - *Pause Workflow Execution:* for a set time or until resumed by hand; also in bulk. The workflow's System Error Notifier is told.
  - *Reset Queue Count:* also in bulk.

**Admin intervention** (`administrator-intervene`)
- **Who and where:** app admins, from the record's approval or fill-in panel.
- **Actions**
  - **Nudge.**
  - **Skip Current Node:** approves at once, with the remark "Approved by Admin".
  - **Change Node Owner.**
  - **Return:** to the initiator or an earlier node.
  - **Abort:** ends the Initiate Approval Flow node. Later nodes of the main flow still run.
- **Only** for Approval and Fill in nodes inside an Initiate Approval Flow, and the worksheet must show approval flow details.

**To-do delegation** (`delegation`)
- **Users:** To-do › Delegation › My Delegation › Create Delegation.
  - Set the organisation, delegate, period and application scope; the delegate is notified.
  - Each delegated to-do shows who delegated it.
  - "Recall Delegation" on a to-do takes it back. Delegations can be edited or ended.
- **Org admins:** Org Admin › User › To-do Delegation, to view, edit or end anyone's.
- **Rules**
  - Approval and Fill in only; **not CC**.
  - Only to-dos created during the period; existing ones stay.
  - Several delegations by app are possible.
  - Ending a delegation does not return the to-dos already delegated.

**Ending an instance from a record** (`endInstance`)
- **Pattern:** a "Terminate" button flow calls the organisation API `GET https://www.nocoly.com/api/workflow/v1/instance/endInstance` with `appKey`, `sign`, `timestamp`, `accountId` and `instanceId`, through a Send API Request (custom) node.
- **sign** = Base64 of the hex SHA-256 of `AppKey=…&SecretKey=…&Timestamp=…`, made in a Code Block (sample code on the page).
  - AppKey and SecretKey: Organization Admin Console › Integration › Misc.
  - accountId: fixed ("Copy User ID" from the profile), or the clicking user's ID via Get Single Member Info.
  - instanceId: written to a field by an Update Record node right after the Initiate Approval Flow node.
- **Result:** status = 1 on success. Errors: 400 bad signature, 401 accountId unknown, 500 bad instanceId. It can end **any** workflow instance, not only approvals.
- **HAP Server:** Organization Admin Console › Integration › Misc. › Open API › View Docs shows the server's own host.
- **Tip:** keep Approval Instance ID, Last Termination Time and Termination Operator fields for audit, and branch on the approval status afterwards.

**Approval details for standalone Approval nodes** (`get-approval-details`)
- **How:** Get Multiple Data › Get Operation Details after an Approval node. It also works after Fill in and Send Internal Notification nodes.
- **Fields returned:** Record ID, Operator, Arrival time, Operation time, Operation (Approved / Rejected / Submitted), Comment, Signature.
- **Using the rows:** they are multi-row data even when there is one row. Write them with Add Record to an Approval Details sheet (two-way relation to the request), or take one row with Get Single Data first.
- **Rules**
  - Set it up on both the Approved and the Rejected branch of every Approval node.
  - With several approvers, the details arrive only after all have acted.
  - The values typed in a Fill in node are not returned.
- **For Initiate Approval Flow,** use the block's own mapping instead.

## 3. Odoo rebuild notes

Every row is [Inference], built on the doc facts in §2.

| Odoo concept | Native HAP feature (this slice) | Fit, and where native falls short |
|---|---|---|
| Purchase "Order Approval" (second validation above an amount; state To Approve) | Initiate Approval Flow + Exclusive Branch on the amount + Approval nodes. "Update when approval starts / after approval / after rejection" set our own Status field; approval system fields show progress in views | Good fit. The approval node writes only header fields: purchase-line changes need nodes after the result branch. If Amount Total is a rollup, Calibrate the record before the branch |
| Enterprise Approvals app (approval types, minimum approvers, approver order) | Co-Sign all / any / percentage; several Approval nodes; level by level | Percentage voting ≈ "minimum approval". Required documents need form rules (other slices) |
| Manager-chain approvals (`hr.employee.parent_id`; expense and leave managers) | Direct supervisor; superior of the previous approver; level by level by department head; org-role managers | HAP follows the organisation directory, not an Employees sheet. Keep the directory in sync (Member Events trigger, Get Multiple Personnel) |
| Refuse-reason wizards, approval notes | Comments required on reject, comment templates, "Free Input" off | Batch approval and e-mail quick approval skip required comments. Turn them off where a reason is mandatory |
| Scheduled actions (`ir.cron`) | Scheduled trigger + Get Multiple Data (query and batch update ≤ 1,000) or a subprocess (≤ 10,000) | Fine for nightly jobs. Large tables need loops or subprocesses (part 2), and each run and iteration counts as an execution |
| Automated actions on create / write / delete (`base.automation`) | Worksheet trigger with trigger fields and filters; "Trigger Other Workflows" control | Write-triggered flows always run in parallel; one instance per record, so edits made while an instance runs are lost |
| Automated actions on a time condition; quotation expiry | Date Field trigger; Delay node (on / before / after a date, at a time) | Good fit |
| Bulk import or mass actions | Operation mode for create-only and button flows; order = selection, sort or creation order | Importing 100 rows starts 100 runs. Pick Sequential or by Partition where runs compete for stock or numbers |
| Stored computed fields (`@api.depends`, `store=True`) | Formula and rollup fields + Calibrate; Calculation node for values across records | Rollups are "delayed fields": Calibrate one record before reading them in a flow |
| `onchange` | Not a workflow feature: Calculation runs after save | Use field defaults and business rules (other slices) |
| Constraints and `UserError` on buttons | Button flow: Get Single Data / Calculation checks → Interface Push toast or card → Terminate Process | The check runs after the click, not before the form is saved. Only the first push shows, and no waiting node may come before it |
| Stock-quant concurrency (row locks) | Strict Serial Execution by Partition on create-only or button flows; Query and Update with "Use pre-update data" for deduct-and-check | No transactions, and update triggers cannot be serialised. Route stock changes through rows that are *created* (a moves sheet or a queue sheet) |
| Find-or-create (customer on lead conversion, product by code) | Get Single Data: Create a Record and Continue, or a Has Data / No Data branch; a unique index with "Continue on failure" | The page's own example is lead → customer. Two simultaneous creates can both miss: partition by the key |
| Odoo actions that open a window (open the created invoice; smart-button lists) | Interface Push: record detail (modal or new tab), creation page (draft), view, custom page, link | Button flows only |
| Portal sharing with access tokens (`portal.mixin`); customer accept / sign; ratings | Get Link: Share Link, Editable Link with chosen fields, password, expiry | No payment step. Whether signature or file fields can be edited through a public link is untested (§5) |
| Portal users (portal access wizard) | Get Single / Multiple External User; Update External User Info (part 2); External User trigger | Good for status and role sync |
| Mail activities (assignee, deadline, reminders, done + feedback) | Fill in with a time limit and reminders; CC for information only | Fill in closes only by Submit from the to-do; no native "mark done" from a button. See `../workflow-nodes.md` §5.7 |
| Chatter messages and followers | CC, Send Internal Notification. Record discussions are readable only through the AI Agent tool | No node in this slice posts to the record discussion. The followers node is in part 2 |
| Calendar events and ICS invitations | Create Event: system schedule + ICS, private, reminders | The event is not linked back to the record's state |
| KPI digests (`digest.digest`), scheduled report e-mails | Scheduled flow + Get Page Snapshot + Send Email | Paid plans only, 100 per hour; charts with access permissions cannot be captured |
| Server actions "Execute Python code" | Code Block (JavaScript or Python) | Last resort; old runtimes (Node 10, Python 3.7) |
| Approval audit trail (`mail.tracking` on state) | Initiate Approval Flow operation details → subform or related sheet; Get Operation Details for standalone approvals | Good fit |
| Printed reports with approvals | Print templates in the Initiate Approval Flow (Word, Excel, system) | No QR or barcode templates there |
| Per-line logic (e.g. launching stock rules per order line) | Call PBP "Execute Multiple Times", one by one; subprocess (part 2) | The page's example is exactly this: Stock In → Update Inventory per line |
| Exchange-rate import, e-invoicing (MyInvois), payment providers | Call Integrated API; API Connection and Authentication (OAuth 2.0 client credentials); Get Multiple Data object array | Token handling is native. Signing e-invoice documents still likely needs code |
| Document digitisation (Enterprise extraction) | AI Agent with File Link + Structured Output; AI Generate Data Object for text | Costs credits and is not deterministic: keep a human review step |
| Cancelling a document while its approval runs | Initiator withdraw; admin Abort / Skip / Return from the record; org API `endInstance` | A Cancel button for ordinary users needs the org API, and so a code block holding the organisation secret |
| Record rules during approval | Approval and Fill in grant access to the record whatever the role; "Verify node owner's record view permission" in the block | Watch for data exposure across companies or teams |

**Where native falls short** [Inference]
- **No transactions.** Withdraw, terminate and failures leave earlier writes in place, and Retry resumes from the failed node. Make steps idempotent and add compensation, e.g. the pre-update rollback pattern from `node-get-single-data`.
- **Write-triggered flows cannot be serialised,** and one instance per record drops edits made while an instance runs or waits.
- **Batch caps** (100 / 1,000 / 10,000) and per-run execution counting force subprocess and loop designs for large data.
- **Approval nodes cannot update** subform or related-sheet fields.
- **Fill in cannot be closed** by editing the record or by a button.
- **Interface Push** works only in button-style flows without waits, and there is no pre-save validation dialog.
- **Calibrate Worksheet** runs in the background and only once per 120 minutes.
- **Code Block runtimes are old:** Node 10, Python 3.7.

## 4. Traps

### Execution and concurrency

1. Update, scheduled, date-field, member, external-user and webhook flows always run in parallel. Only create-only, delete and button flows can be serialised (`configuration`).
2. **Sequential is not strict.** The next run may start when the current one fails, or reaches a Delay, Approval, Fill in, Subprocess or PBP node. Only Strictly Sequential, or by Partition, waits for the whole run (`configuration`).
3. The subprocess wording is counter-intuitive: with "Wait until the subprocess finishes" ticked, the next queued run may start as soon as the current one enters the subprocess (`configuration`). Test it before relying on it.
4. Partition on a stable identifier such as the product. Never on a value that changes, such as the stock quantity (`configuration`).
5. **One running instance per record per workflow.** A change made while the instance runs, including while it waits at a Delay, Approval or Fill in node, does not start the flow again. During a pause, repeated triggers from one record become one run (`history-versions`, `in-queue`).
6. **Same-sheet chains:** when two automatic flows trigger on the same worksheet, the writes of one start the other only if the other has trigger fields. This does not apply when a button started the writing flow (`configuration`).
7. "Trigger Not Allowed" blocks only the workflow's own writes. Manual creates still start other flows (`configuration`).
8. When the monthly execution quota is used up, flows simply do not start (`history-versions`). The execution queue is shared with other organisations, so timing varies (`in-queue`).
9. Restoring a version changes nothing at runtime until Update Release (`history-versions`).
10. Retry continues from the failed node with the data as it is now (`history-versions`; "as it is now" is inference).

### Data and rows

11. **More than 100 rows** from Get Multiple Data into Add / Update / Delete / Code **terminates the whole run**. With no limit set, Get Multiple Data returns 100 (`node-get-multiple-data`). Set explicit limits and count first.
12. Query and batch update / delete touch only the first 1,000 by sort; the docs mention no error (`node-get-multiple-data`).
13. "Dynamic retrieval during each use" and dynamic calculations can give different values at different nodes (`node-get-multiple-data`, `node-calculation`).
14. **Get Single Data with "Ignore Empty Values":** if the only condition's value is empty, no filter applies, and the first or a random record comes back, ready to be updated or deleted (`node-get-single-data`). Avoid it on update and delete methods, or guard with a branch.
15. "Ignore Condition Errors" hides a broken filter, such as a deleted field, by skipping the query (`node-get-single-data`).
16. When Get Single Data finds nothing and you chose Continue: nodes that act on the record are skipped, but nodes that copy its fields get empty values and still run. An Update Record can therefore blank fields (`node-get-single-data`; the blanking is inference).
17. Create a Record and Continue with a unique index: the duplicate insert fails, and with "Continue on failure" the node returns empty data (`node-get-single-data`).
18. Retrieve Related Record returns one record even when several are linked (`node-get-single-data`).
19. Date filters: Equals / Does Not Equal compare by day. System date-times default to minute precision (`configuration`).
20. The branch decimal-places setting affects only branches; every other node uses the raw value (`configuration`).
21. **Calculation rounds to 2 decimals by default.** Empty operands empty the result unless "treat empty as 0", but built-in functions silently treat empties as 0. An empty denominator always gives empty, and so does a wrong output type (`node-calculation`).
22. Date formulas must start with + or −. M is month and m is minute. "Date" mode drops the time (`node-calculation`).
23. Duration Format 1 counts the end date through 24:00, so 13 to 14 Dec = 2 days (`node-calculation`).
24. Calibrate Worksheet runs in the background, so later nodes still see old values. It stops at 100,000 rows, and a second run within 120 minutes is skipped (`node-calibrate`).
25. Code Block: arrays arrive as strings; outputs exist only after a successful Test and a save; ≤ 100 rows (`node-code-block`).
26. Permanent delete bypasses the 60-day recycle bin, in Delete Record, Get Single Data and Get Multiple Data alike (`node-delete-record`, `node-get-single-data`, `node-get-multiple-data`).

### Approvals and tasks

27. A rejection ends the workflow unless a "Branch Based on Approval Result" follows the Approval node (`node-branch`, `node-approve`).
28. The workflow-level auto-approval, withdraw and nudge settings do not apply inside an Initiate Approval Flow block, which has its own (`configuration`, `node-approve`).
29. **Batch approval, check-list approval and e-mail quick approval ignore required fields.** Batch and e-mail approval also skip required comments and signatures (`node-approve`).
30. Approval data updates cannot touch subforms or related sheets (`node-approve`).
31. **Return limits:**
    - only Delay, Calculation, Approval, Fill in and CC nodes may sit between the two nodes;
    - the target must be on the main path;
    - not possible with "approved when one approves, rejected when all reject";
    - a standalone node returns only to "all nodes above" or the initiator (`node-approve`).
32. "Automatically enter the next node" for an empty approver means no one can later return to that node (`node-approve`).
33. Approval and Fill in assignees can see and edit the record whatever their role (`node-approve`, `node-fill-in`). Inside a block, "Verify node owner's record view permission" changes this (`node-initiate-approval-flow`).
34. Approval status system fields cannot be written by workflows or by hand (`node-initiate-approval-flow`). Keep your own Status field for business logic.
35. Print templates in the approval block cannot contain QR codes or barcodes (`node-initiate-approval-flow`).
36. Co-sign operation details include approvers who never acted, under percentage voting (`node-initiate-approval-flow`).
37. Get Operation Details must be set up on both result branches of every Approval node, arrives only after all approvers act, and does not include fill-in values (`get-approval-details`).
38. **Fill in completes only through Submit** in the to-do or the notification. The first submitter wins. E-mail copies cost 0.002 credits each (`node-fill-in`).
39. Withdraw and Terminate do not undo earlier writes (`configuration`, `node-abort-the-process`). Terminating also ends subprocesses, approval flows and PBPs (`history-versions`).
40. Admin Abort ends only the approval block; the main flow carries on. Handle the Terminate result in the result branch (`administrator-intervene`, `node-initiate-approval-flow`).
41. Admin intervention works only inside blocks, and only when the sheet shows approval details (`administrator-intervene`).
42. Delegation excludes CC, does not move existing to-dos, and ending it does not take delegated to-dos back (`delegation`).
43. A CC or internal-notification node whose only recipient is the triggering user is skipped when "Notification Nodes" excludes that user (`configuration`).
44. Initiator View is off by default, so flows do not show under Submit, unless an Approval, Fill in or CC node was added outside a block (`configuration`).

### Screens, links and integration

45. **Only the first Interface Push node runs.** None runs after a waiting node or a Loop, and none in scheduled, date, webhook or subprocess flows (`node-interface-push`).
46. Toasts reach only the initiator. Cards reach other users only while they are logged in (`node-interface-push`).
47. **A Share Link does not expire** unless the record is deleted (or, presumably, an expiry is set) (`node-get-link`). For commercial documents, set an expiry and a password [Inference].
48. Link Name shows only in e-mails (`node-get-link`).
49. Get Page Snapshot works on paid plans only, at 100 per hour, and cannot capture pages behind a login or charts with access permissions (`node-get-snapshot`).
50. The Basic Auth output has no "Basic " prefix, and any JSON reply counts as a successful token request (`node-api-connectivity-authentication`).
51. Call Integrated API with "Continue" on timeout: later nodes silently skip the missing values (`node-call-integrated-api`).
52. Call PBP outputs exist only when the node waits. "Execute one by one" stops the rest after a termination. Without the option, the PBP's trigger user is "Workflow" (`node-call-pbp`).
53. A Terminate inside a PBP returns null outputs, and webhook custom responses after a Terminate are null (`node-abort-the-process`).
54. Get Single Personnel cannot feed a subprocess. It also reads profiles hidden from Contacts, and returns empty organisation properties for external collaborators (`node-get-single-data-from-user`).
55. An external-user lookup by phone returns the most recently signed-up match (`node-get-external-user`).
56. AI Agent tools expose only the first record; discussions need the Record ID in the prompt; every run spends credits (`node-ai-agent`).
57. The `endInstance` example puts the organisation SecretKey in plain text in a Code Block, readable by anyone who can open the workflow [Inference] (`endInstance`).

### Conflicts and unclear wording in the docs

58. **Workflow ownership:** "can be changed" (`configuration`) versus "Workflow creators cannot transfer ownership" (`all-workflows-management`).
59. The queue alert fires when the queue "reaches or falls below" the threshold (`all-workflows-management`). It probably means "reaches or exceeds".
60. The level-by-level "approval starting point": the page says some option is unavailable outside a block, without saying clearly which (`node-approve`).

## 5. To verify live

None of these has been tested. Run them in a sandbox app, not in EMS or a customer app. The model lists, credit prices and plan gates (AI nodes, 0.002 credits, paid-plan snapshots) are time-sensitive and should be re-read from the live docs when they matter.

1. **Partitioned serial runs** (`configuration`). Build a create-only flow on a Stock Moves sheet, partitioned by Product, and import 20 moves for 2 products at once. Expect no over-allocation, with the two products processed at the same time.
2. **Sequential runs with a subprocess** (`configuration`). Check whether the next run starts when the current one enters a waiting subprocess, with and without "Wait until the subprocess finishes".
3. **Same-sheet trigger rule** (`configuration`). Flow A triggers automatically on sheet 1 and writes to sheet 1. Flow B also triggers on sheet 1, with and without trigger fields. Repeat with A started by a button, and with A triggered from another sheet.
4. **One instance per record** (`history-versions`, `in-queue`). Update a record twice while its first run waits at a Delay. Confirm the second change is dropped, not queued.
5. **100-row cap** (`node-get-multiple-data`). Feed 101 rows into Update Record. Confirm the run terminates, and whether any row was written first.
6. **1,000-row cap** (`node-get-multiple-data`). Run query and batch update on 1,200 matching rows. Confirm that exactly the first 1,000 by sort are updated, and whether any error or notice appears.
7. **Ignore Empty Values** (`node-get-single-data`). Run Query and Update with a single condition whose value is empty. Confirm whether it updates an arbitrary record.
8. **Query and Update with "Use pre-update data" in parallel** (`node-get-single-data`). Start two deductions on the same product at once and record what each run read.
9. **Calculation precision** (`node-calculation`). Confirm the default 2-decimal rounding, and whether the output can keep more decimals: Odoo prices and unit factors need more.
10. **Dates and times** (`configuration`, `node-delay`):
    - the seconds-precision setting;
    - Equals on a date-time filter compares by day;
    - which time zone the Delay node's default 8:00 AM uses: the app's or the server's UTC+8 (part 2 has the time pages).
11. **Calibrate** (`node-calibrate`; [Project] memory note).
    - After Calibrate Single Record, does a rollup read straight away return the new value?
    - Does Calibrate Worksheet share the 120-minute window with manual calibration (校准)?
12. **Approval data updates** (`node-approve`). Confirm that subform and related-sheet fields cannot be set, and that "Update when approval starts" runs again after a return.
13. **Required fields in bulk and e-mail approval** (`node-approve`). Confirm that batch, check-list and e-mail quick approval skip required fields and comments on Nocoly SaaS, then decide the setting per flow.
14. **Approval status in views** (`node-initiate-approval-flow`; not stated). Can a view filter and sort on Status or Node Owner, for a "To Approve" list?
15. **Fill-in completion** (`node-fill-in`; `../workflow-nodes.md`). Submit from the to-do works and a record edit does not. Does the CLI `approval submit` or the MCP also complete it?
16. **Interface Push** (`node-interface-push`).
    - Can the draft from "Open Record Creation Page" + "Create Draft Record" be prefilled, e.g. with the customer from the opportunity?
    - Does only the first push run?
    - Do cards reach other users?
17. **Editable Link** (`node-get-link`). Which field types can be edited without logging in: signature, attachment, subform? Does Set Link Expiry apply to Share Links? How do the password and its validity behave?
18. **Snapshot plan gate** (`node-get-snapshot`). Is Get Page Snapshot enabled on our Nocoly plan?
19. **Code Block** (`node-code-block`). Confirm the Node 10.16.3 and Python 3.7.5 runtimes, and find the timeout, which this page does not state.
20. **OAuth against MyInvois** (`node-api-connectivity-authentication`). Can the node send a form-encoded POST body (client_id, client_secret, grant_type, scope), and does it cache the token for its lifetime?
21. **PBP execution counts** (`node-call-pbp`). Confirm in Org Admin › Workflow that "Execute Once" is not counted, and see how "Execute Multiple Times" is counted.
22. **endInstance on SaaS** (`endInstance`). Does the org API end an Initiate Approval Flow instance on Nocoly SaaS and return status = 1? Prefer a design that keeps the secret out of the code block.
23. **Ownership conflict** (`configuration` vs `all-workflows-management`). Can the owner be changed on the workflow's Configuration page?
24. **Retry** (`history-versions`). Does a retry use the current record data and skip the nodes that already succeeded?

## 6. Coverage

All 39 pages of the slice, cached 3 Nov 2026.

| # | URL | Title | Summary |
|---|---|---|---|
| 1 | https://help.nocoly.com/workflow/administrator-intervene | How Admins Can Intervene in Workflow Processes | Five admin actions (Nudge, Skip Current Node, Change Node Owner, Return, Abort) on approval and fill-in nodes inside an Initiate Approval Flow, taken from the record |
| 2 | https://help.nocoly.com/workflow/all-workflows-management | Management and Monitoring of All Workflows | Org Admin › App Management › Workflow: list with monthly execution counts, expansion packages, real-time monitor, queue alerts, pause and resume, reset queue count |
| 3 | https://help.nocoly.com/workflow/auto-data-modification | How to Automatically Update Related Data When Worksheet Records Change | Update Record examples: stamp a completion time on the same record; cascade a project's status to its tasks (second example only in screenshots) |
| 4 | https://help.nocoly.com/workflow/configuration | Global Workflow Settings | Error notices, owner, the four execution modes and which triggers allow them, data and text formatting, 90-day node logs, Initiator View, Trigger Other Workflows, withdraw and nudge, auto-approval, notification nodes, workflow parameters |
| 5 | https://help.nocoly.com/workflow/create | How to Create an Automated Workflow | The six trigger types, adding nodes ("40 Workflow Nodes"), test, publish, Update Release, mini map, enabling |
| 6 | https://help.nocoly.com/workflow/delegation | Workflow To-do Delegation | Delegating new approval and fill-in to-dos for a period and app scope; recall; org-admin management; CC excluded |
| 7 | https://help.nocoly.com/workflow/endInstance | End a Workflow from a Record | A Terminate button that calls the org API endInstance with a code-block signature and a stored instanceId; error codes |
| 8 | https://help.nocoly.com/workflow/faq | FAQ | Links to articles on auto numbers and record IDs, time terms, filters, buying executions and updating other data |
| 9 | https://help.nocoly.com/workflow/get-approval-details | Get Approval Details | Get Multiple Data › Get Operation Details after standalone Approval nodes: the fields returned, writing them to an Approval Details sheet, taking a single row |
| 10 | https://help.nocoly.com/workflow/history-versions | Workflow History and Execution Details | Run list and details, terminate (also in bulk), retry from the failed node, troubleshooting, version view / rename / restore and Update Release |
| 11 | https://help.nocoly.com/workflow/in-queue | What Does "Queued" Workflow Mean? | Why runs queue (sequential mode, a platform-wide shared service), the effect of pauses, one running instance per record |
| 12 | https://help.nocoly.com/workflow/introduction | Workflow Overview | Workflow as BPM: trigger plus action nodes; automation, approval, notification and integration scenarios |
| 13 | https://help.nocoly.com/workflow/node-abort-the-process | Node - Terminate Process | Ends the run and its children; behaviour in branches, subprocesses, loops, PBPs and webhook responses |
| 14 | https://help.nocoly.com/workflow/node-add-record | Workflow Node -- Add Record | Creating one or many records; value sources; linking to the trigger record; field-type matching rules |
| 15 | https://help.nocoly.com/workflow/node-ai-agent | Node - AI Agent | LLM agent: model, prompt, files, memory, tools (data, notification, PBP, API), worksheet scope, filters, outputs, logs, credits |
| 16 | https://help.nocoly.com/workflow/node-ai-generates-data-objects | Node - AI Generate Data Object | Extracting structured parameters from text with a chosen model; test; outputs and credits |
| 17 | https://help.nocoly.com/workflow/node-ai-text-generation | Node - AI Generate Text | Generating or translating text with a model and prompt templates; outputs and credits |
| 18 | https://help.nocoly.com/workflow/node-api-connectivity-authentication | API Connection and Authentication | Basic Auth and OAuth 2.0 client credentials; token request, caching and lifetime (0–604,800 s) |
| 19 | https://help.nocoly.com/workflow/node-approve | Node - Approval | Approvers, multi-approver methods, actions (stash, forward, add, return), empty approver, comments / signature / password, batch and e-mail approval, deadlines, field permissions, data updates |
| 20 | https://help.nocoly.com/workflow/node-branch | Node - Branch | Parallel, Exclusive, approval-result and data-retrieval-result branches; else logic; branch operations |
| 21 | https://help.nocoly.com/workflow/node-calculation | Node - Calculation | Number, date add/subtract, date duration and function calculations; static versus dynamic; empty-value rules |
| 22 | https://help.nocoly.com/workflow/node-calibrate | Node - Calibrate | Refreshing formula, rollup, stored foreign, concatenation and option fields for one record (at once) or a worksheet (background, 100,000 rows, 120-minute interval) |
| 23 | https://help.nocoly.com/workflow/node-call-integrated-api | Node – Call Integrated API | Calling an Integration Center API; timeout handling; multi-row responses through Get Multiple Data |
| 24 | https://help.nocoly.com/workflow/node-call-pbp | Node - Call PBP | Calling a PBP once or many times (parallel or one by one), waiting for outputs, passing inputs and the triggering user |
| 25 | https://help.nocoly.com/workflow/node-cc-send-internal-notification | Node - CC and Send Internal Notification | CC with a record link, display through a view and a to-do entry, versus plain internal notifications; recipients, sound, e-mail |
| 26 | https://help.nocoly.com/workflow/node-code-block | Node — Code Block | JavaScript (Node 10.16.3) or Python (3.7.5) with preinstalled modules; ≤ 100 input rows; input and output format; test before use |
| 27 | https://help.nocoly.com/workflow/node-create-event | Node – Create Event | Creating calendar schedules and/or ICS files (all-day, private, reminders, UTC) |
| 28 | https://help.nocoly.com/workflow/node-delay | Node - Delay | Waiting until a date (on / before / after, at a time) or for a duration (≤ 999 d 23 h 59 m 59 s) |
| 29 | https://help.nocoly.com/workflow/node-delete-record | Node - Delete Record | Deleting one or many records, to the recycle bin (60 days) or permanently |
| 30 | https://help.nocoly.com/workflow/node-fill-in | Node - Fill in | Form task: assignees, field permissions, stash and forward, password, deadlines and reminders, overdue handling, e-mail cost, data updates |
| 31 | https://help.nocoly.com/workflow/node-get-external-user | Node – Get Single/Multiple External User | Reading portal users from a field or the portal list (lookup by phone), then using or updating them; daily sync pattern |
| 32 | https://help.nocoly.com/workflow/node-get-link | Node - Get Link | Share, internal or editable record links with password, expiry, field permissions and access after submission |
| 33 | https://help.nocoly.com/workflow/node-get-multiple-data | Node - Get Multiple Data | Seven retrieval methods, row caps (100 / 1,000 / 10,000), random or first N, direct versus dynamic retrieval |
| 34 | https://help.nocoly.com/workflow/node-get-multiple-data-from-user | Node - Get Multiple Personnel (Departments / Organization Roles) | Many members, departments or org roles from fields or the directory; subprocess sync pattern; reporting relationships |
| 35 | https://help.nocoly.com/workflow/node-get-single-data | Node — Get Single Data | Six retrieval methods, filters, empty-value and error handling, no-result actions, pre-update values, record-link parsing |
| 36 | https://help.nocoly.com/workflow/node-get-single-data-from-user | Node - Get Single Personnel (Department/Organization Role) | One member, department or org role with its properties; org-wide search for admins only; cannot feed a subprocess |
| 37 | https://help.nocoly.com/workflow/node-get-snapshot | Node - Get Page Snapshot | Capturing a custom page, chart or URL as an image; paid plans; 100 per hour; no pages behind a login |
| 38 | https://help.nocoly.com/workflow/node-initiate-approval-flow | Node - Initiate Approval Flow | Approval block as a sub-flow: initiator options, empty handling, auto-approval, field settings, print templates, status fields, operation-detail mapping, parallel approval, copying |
| 39 | https://help.nocoly.com/workflow/node-interface-push | Node - Interface Push | Toast and card notifications, and opening pages, after a button click; availability rules; only the first push runs |
