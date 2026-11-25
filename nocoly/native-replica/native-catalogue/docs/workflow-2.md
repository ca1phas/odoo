# Nocoly Help digest: workflow, part 2 of 2

| | |
|---|---|
| Slice | `python -I read_pages.py --prefix workflow --part 2/2`: 38 pages, `node-invite-external-user` to `workflow-execution-limits` (alphabetical) |
| Pages read | 38 of 38, full text (131,210 characters) |
| Source | help.nocoly.com, cached 3 Nov 2026 (`knowledge-base/nocoly-mingdao/research/corpus.sqlite`) |
| Written | 23 Nov 2026. Read-only: no app, workflow, record or setting was touched |
| Companions | `workflow-1.md` (part 1: approval, fill in, branch, calculation, get single/multiple data, code block, delay, interface push, global settings and the rest). `../workflow-nodes.md` (wave-0 catalogue with CLI and EMS evidence) |

**How to read the evidence**
- Plain statements in §2 are **docs (cached 3 Nov 2026)**: vendor text, not runtime proof.
- Lines starting **Inference:** or **ERP use (inference):** are mine, not the docs'.
- **[Plan page]** = `https://help.nocoly.com/purchase/version-comparison` (same cache, outside this slice). It is quoted because the brief asks for plan limits, and because it contradicts prices given in this slice.
- No page in this slice makes a SaaS-only or Server-only statement. The URLs and IP addresses quoted are SaaS ones.
- Short source names below (for example `node-loop`) stand for `https://help.nocoly.com/workflow/<name>`. Full URLs are in §6.

## 1. Summary

1. **Triggers cover Odoo's automation layer.** Worksheet events (create, update, create-or-update, delete; trigger fields; conditions), date fields (± minutes, hours or days; yearly, monthly or weekly repeat) and schedules (custom times, weekdays, months) replace automation rules and scheduled actions. Webhooks and PBP APIs take inbound calls.
2. **PBP is the native shared method:** typed inputs and outputs, callable from any workflow in the organisation, a custom-page button or its own API. The docs' first example is a reusable "update inventory" PBP. [Plan page] PBP, Loop, Code Block and Global variables are **Professional only**.
3. **Volume needs fan-out.** A Subprocess runs once per record: up to 1,000,000 worksheet rows (default 50,000) or 10,000 array rows, in parallel or one by one. Batch delete takes 1,000 rows, a code block 100, a Loop 10,000 iterations, Jump To 20 jumps per run.
4. **Executions cost.** Every loop iteration and every subprocess record is one execution (500 records = 501). [Plan page] Standard includes 100,000 a month, Professional 500,000; extra executions cost $0.01 each.
5. **Update Record has To / Add / Minus** on number, amount, multi-select, member, department, multi-relation and file fields. This is the native way to post stock and balance changes, but the docs say nothing about concurrent runs.
6. **The Rollup node** sums, averages, counts, and finds max/min with no row limit. It also counts a Get Multiple Data result and totals the records picked for a bulk button. Its result can lag slightly behind recent writes.
7. **Documents:** Word or Excel print template → Get Record Print File (PDF optional, paid) → file field or e-mail attachment. Send Email offers rich text, MJML, field aliases, CC/BCC and Reply-To, but the sender address is fixed and one address can receive at most 10 e-mails an hour.
8. **Integration without code:** Send API Request (6 methods, 4 body types, 10 s timeout, continue or stop on failure), JSON Parsing (JSONPath), a condition loop for cursor paging, and webhooks (10,000 requests an hour, app authorisation, IP whitelist).
9. **Malaysia limits:** custom SMS outside Mainland China needs the organisation's own Twilio account. Portal invitations go by SMS only, never to overseas numbers. The WeChat node serves China only (inference).
10. **The docs conflict with each other.** The subprocess page says a subprocess run is not counted, then counts it. CNY prices in this slice differ from the plan page's USD prices. The webhook page sends you to "AI Capabilities" for response settings. All three need a live check.

## 2. Capability inventory

### 2.1 Triggers

The overview page lists nine trigger types. A tenth kind of flow, the loop process, is created by a Loop node (§2.3).

**Triggered by Worksheet**
- *What:* watches one worksheet and starts a run for each record that is created, updated or deleted.
- *Options:*
  - Trigger Worksheet.
  - Trigger Event: When a Record Is Created or Updated / When a Record Is Created / When a Record Is Updated / When a Record Is Deleted.
  - Trigger fields (several allowed, for the two update events): the run starts only when one of them is filled in or changed. With none chosen, any change starts it.
  - Trigger Conditions: only matching records enter the flow.
- *Limits:* the delete event fires after the record is deleted. The page gives no counts and no execution modes; those are in `workflow-1.md` (global settings).
- *ERP use (inference):* Odoo automation rules on create, write and unlink: order confirmed → reserve stock; status changed → notify; amount over 10,000 → approval (the page's own example).
- *Source:* https://help.nocoly.com/workflow/trigger-by-worksheet , https://help.nocoly.com/workflow/trigger-mode

**Triggered on Schedule**
- *What:* runs on a recurring timetable, with no record attached.
- *Options:*
  - Start Execution Time: the first run, and the anchor of the cycle.
  - End Execution Time: optional.
  - Recurrence (labelled "Loop" in the docs): hourly, daily, weekdays, weekly, monthly, yearly, custom.
  - Custom: times within a day (for example 9:00 and 21:00, or every few hours), chosen weekdays, chosen months. Generate previews the next 7 runs.
  - Execute Now (after publishing) runs it at once.
- *Limits:*
  - Weekly, monthly and yearly runs fall on the weekday, day of month or date of the start time.
  - "Weekdays" means Monday to Friday **excluding holidays**. The page does not say which holiday calendar.
  - No record is in context, so records must be queried first (Update Record page).
- *ERP use (inference):* Odoo scheduled actions: daily currency rates, reordering-rule checks, overdue-invoice reminders, nightly activity-state refresh, staging-table purges.
- *Source:* https://help.nocoly.com/workflow/trigger-by-scheduled

**Triggered by Date Field**
- *What:* for each record, runs when server time reaches the value of a date or date-time field, optionally offset.
- *Options:*
  - Worksheet: any in the app.
  - Field: a date or date-time field.
  - Start Time for a date field: on, before or after the date, at an execution time (default 8:00 AM).
  - Start Time for a date-time field: at the value, or a number of minutes, hours or days before or after it.
  - Recurrence: Every year / Every month / Every week / No repeat.
  - End Time: only with a recurrence.
  - Filter conditions.
- *Limits:* when a record's date changes, the trigger waits for the new value. The page does not say what happens when the time has already passed at save.
- *ERP use (inference):* payment-due reminders (due date − 3 days), contract and warranty expiry, lot expiry and removal alerts, visit and activity reminders (the page's example fires 1 hour before a visit), yearly anniversaries.
- *Source:* https://help.nocoly.com/workflow/trigger-by-date-field

**Triggered by Member Events**
- *What:* runs when a member joins or leaves the organisation.
- *Options:* the event (joins / leaves) and filter conditions (for example, Sales Department only).
- *When it fires:*
  - Join: an invited member completes their profile; an admin approves a member who came by link or by a non-admin's invitation; an admin restores a deactivated member.
  - Leave: an admin processes the departure, or the member leaves voluntarily.
- *ERP use (inference):* keep an Employees worksheet in step with the organisation (the page's example adds a record); reassign open leads and activities when someone leaves.
- *Source:* https://help.nocoly.com/workflow/trigger-by-personnel

**Triggered by External User**
- *What:* runs when a portal (external) user registers, logs in (automatic login included), deletes their account, or is disabled. UI example: "When a User Deletes Their Account".
- *ERP use (inference):* create or link a Contact when a customer registers on the portal; log portal sign-ins; flag the contact when the account closes.
- *Source:* https://help.nocoly.com/workflow/trigger-by-external-user

**Triggered by Webhook**
- *What:* each webhook workflow has a unique URL. An HTTPS request to it starts a run.
- *Options:*
  - Data sample, three ways:
    - Generate from Request Example: send a GET or POST within 3 minutes. Generate Full Body Parameter also keeps the whole body as one parameter.
    - Generate from JSON Example.
    - Generate from Key-Value Pairs.
  - Parameters can be marked required. A missing one returns `"msg": "Missing required parameter"`.
  - Custom response method and content. The page places them under [Workflow Configuration] > [AI Capabilities], probably meaning the API-capability setting.
  - Security: Use App Authorization (AppKey and Sign required) and App IP Whitelist.
  - Enabled webhook flows appear in the app's API documentation. The flow list can be searched by the ID in the URL.
- *Limits:* 10,000 requests per hour per webhook ("Execution limit exceeded."). Without the security options, anyone who has the URL can post.
- *ERP use (inference):* marketplace and web-shop orders, payment-gateway callbacks, courier status, e-invoice status callbacks.
- *Source:* https://help.nocoly.com/workflow/trigger-by-webhook , https://help.nocoly.com/workflow/workflow-execution-limits

**Packaged Business Process (PBP)**
- Started by a Call PBP node in any workflow of the organisation, by a shortcut button on a custom page, or through its own API. Details in §2.3.
- *Source:* https://help.nocoly.com/workflow/trigger-mode

**Subprocess**
- Cannot be created on its own. A Subprocess node creates it, and it runs only when another workflow passes it data.
- Existing worksheet-event, custom-button and date-field flows can be converted into one (single-workflow-management). Details in §2.3.
- *Source:* https://help.nocoly.com/workflow/trigger-mode

**Triggered by Custom Button**
- *What:* cannot be created directly. You create a custom action on a worksheet, the system creates the linked workflow, and it runs when a user clicks the button.
- *Bulk:* a custom action available for bulk actions starts **one** run for all the selected records. The trigger node holds them, and a Rollup node can total them (node-rollup).
- *ERP use (inference):* Odoo object buttons (Confirm, Validate, Create Invoice, Send by Email, Register Payment, Cancel) and multi-record actions, such as one bill from several selected receipts.
- *Source:* https://help.nocoly.com/workflow/trigger-mode , https://help.nocoly.com/workflow/node-rollup

**Run context available to every trigger**
- *Data Source ID:* triggering record ID + triggering user ID + trigger timestamp. A scheduled run has only the last two. Non-user sources appear as `user-api`, `user-workflow` and `user-publicform`. (trigger-info)
- *Execution Instance ID:* one per run, for example `<id>`. Append `/2/<InstanceID>` to the workflow configuration page URL to open that run's log. (trigger-info)
- *Time values* (times):
  - Trigger Time: when the run started.
  - Creation Time and Last Modified Time: of the record.
  - System Current Time: when the current node runs.
  - For an "approved at" stamp, use System Current Time.
- *Record ID (rowid)* (rowid, recordid):
  - 36 characters, unique within a worksheet, never reused, cannot change.
  - Shown only in a Table view (column display settings).
  - Filter related records with "<relationship field> is Record ID".
  - A record page URL is made of app ID / worksheet ID / view ID / `row` / record ID. Open a record in a new tab from the target view, copy the URL, and swap the record ID.
  - Recipients of the link must sign in and pass that view's permissions.
- *ERP use (inference):* idempotency keys (store the instance ID on the rows a run creates), "posted by" audit, record links in e-mails and notifications.
- *Source:* https://help.nocoly.com/workflow/trigger-info , https://help.nocoly.com/workflow/times , https://help.nocoly.com/workflow/rowid , https://help.nocoly.com/workflow/recordid

### 2.2 Record and data nodes

**Update Record**
- *What:* changes one or more fields of one record.
- *Options:*
  - Choose the object to be updated: a node that points at the record (trigger, Add Record, Approval, Fill in, Get Single Data). A scheduled flow has none, so first find the record (for example with Get Multiple Data) and update that node.
  - New value: A = fixed text, B = a value from another node; at least one is needed.
  - Set to empty.
  - Update the associated (relationship) fields.
  - To / Add / Minus (the page also says Reduce).
  - Combine existing content with new: select the same field again, then add text.
- *Values:* Add and Minus work on number, amount, multi-select, member, department, relationship (multiple rows) and file fields. Example: stock 50, Add 60 → 110; To 60 → 60.
- *Limits:* this page gives no row count for updating a set (see `workflow-1.md`, Get Multiple Data).
- *ERP use (inference):* status changes (draft → confirmed), on-hand quantity changes, linking an invoice to its order (Add on a multi-relation), attaching a generated PDF, appending to a log text.
- *Source:* https://help.nocoly.com/workflow/node-update-record

**Rollup**
- *What:* queries and aggregates data for later nodes.
- *Methods:*
  - Summary from Worksheet: filter conditions, then Number of Records, or a field with Sum, Average, Maximum or Minimum, or a count of filled or empty values. Option "When the summary result is empty, it is considered as 0".
  - Get Data Count: counts what a Get Multiple Data node returned (worksheet records, or arrays from Code Block or Send API Request). Option "Limit results based on the number of summary objects": on = count within that node's limit (example 100); off = all matches (135).
  - Batch data source: totals the records selected for a bulk custom action. Only in flows started by such an action.
- *When calculated:* Direct access (computed once, when the node runs) or Dynamically acquired data each time (recomputed whenever a later node uses it, so two later nodes can get different results).
- *Limits:*
  - No limit on the number of records.
  - Results can lag slightly when the source data changes often.
  - Related records read through a relationship cannot be fed in. Query the line worksheet with "relationship = current record ID" instead.
  - Subform rows count only if the subform is stored as an entity worksheet.
- *ERP use (inference):* order total from lines, amount still due from payments, credit-limit check (sum of a customer's open invoices), open tasks before closing a project, stock from a move ledger.
- *Source:* https://help.nocoly.com/workflow/node-rollup

**Update Record Followers**
- *What:* changes who follows a record. Followers are notified of every new discussion message on it, even when not mentioned.
- *Options:*
  - Select Update Object: the record.
  - Update Method: Add Followers / Remove Followers / Overwrite Followers (replaces the list).
  - Followers: fixed users; single or multi member fields; users from a Get Multiple Members node.
  - The current list shows under the 🔔 icon in the record's discussion.
- *ERP use (inference):* Odoo followers: the salesperson follows the order and is overwritten on reassignment; the support owner follows the ticket.
- *Source:* https://help.nocoly.com/workflow/node-updates-record-followers

**Subform data in workflows**
- *Read:* Get Multiple Data → Get the associated records, from the parent record.
- *Write in bulk:*
  - Only into a subform that has an entity sheet.
  - A blank subform (created from scratch) cannot receive rows from a workflow until it is converted to an entity sheet (one click).
  - The rows must come from an earlier batch node.
- *ERP use (inference):* order, invoice or bill-of-materials lines built from an API payload or copied from a template.
- *Source:* https://help.nocoly.com/workflow/process-subform-data

### 2.3 Flow control, reuse and variables

**Jump To**
- *What:* sends the run to a chosen node and resumes there.
- *Options:*
  - Go to Node: a node on the current branch or the main flow, not on another branch.
  - Jump Conditions: with none, it always jumps.
- *Rules and limits:*
  - The target node and the nodes after it run again.
  - A jump from a parallel branch stops that branch and every other branch still running or waiting.
  - Inside an approval flow, it can only jump to a node of the same approval flow.
  - **At most 20 jumps per run.** Later jumps are not executed.
- *ERP use (inference):* rework loops (back to a fill-in step when data is invalid), bounded retries of an API call, re-approval after a correction.
- *Source:* https://help.nocoly.com/workflow/node-jump-to

**Loop**
- *Modes:*
  - Loop a Specified Number of Times: system parameters start, end and step. You set their initial values but cannot rename or delete them. The loop ends when start > end.
  - Loop While Conditions Are Met: system parameter index (+1 per iteration), custom parameters changed by Update Parameters, and an exit condition.
- *Options:*
  - Custom parameters, added in the loop's first node.
  - Use the triggering user of this workflow for the loop. When off, the loop runs as "Workflow".
  - When an iteration is terminated: Skip and Continue to the Next Iteration / End the Loop and Continue the Workflow / Terminate the Workflow.
  - Use an Existing Loop Process: pick an app and a loop.
  - Final parameter values can be read after the loop.
- *Limits:*
  - Iterations run strictly one after another.
  - **Each iteration is one workflow execution.**
  - **At most 10,000 iterations.** The loop then ends and the flow carries on, even if the end condition was never met.
  - Update Parameters cannot change index, start, end or step.
  - [Plan page] Loop: Professional only.
- *Examples on the page:* start 1, end 3, step 1 → 3 iterations; step 2 → 2; end 0 → none. Cursor paging uses a text parameter hasMore and a cursor parameter.
- *ERP use (inference):* paging through marketplace or bank APIs; generating N rows (instalments, serial numbers, recurring entries); walking a unit or category chain upwards.
- *Source:* https://help.nocoly.com/workflow/node-loop

**Subprocess**
- *What:* runs a child flow of type Subprocess for one record, for each of several records, or for each row of an array.
- *Options:*
  - A Data to Pass: a node's record or set.
  - B: the subprocess is created when the node is saved.
  - C Workflow Parameters: values passed in.
  - D "After the subflow is completed, start the next node": wait for the child, or carry on.
  - F "Use the triggering user of this workflow for the subprocess". When off, the child runs as "Workflow".
  - Maximum records: "Get all records from the worksheet" (up to 1,000,000) or a custom limit (default 50,000).
  - Execution mode for several records: Parallel / Execution on a line-by-line basis, with no subsequent subflows triggered on abort / Execute one by one, continue to the next one when interrupted.
  - One subprocess can be reused by several parent flows.
- *Limits:*
  - Worksheet data ≤ 1,000,000 records (default 50,000). Arrays from Code Block, PBP or Send API Request ≤ 10,000 rows.
  - ≤ 100,000 subprocess executions per hour ("The hourly execution limit for subprocesses has been reached.").
  - One execution per record: 500 records plus the parent = 501 executions.
  - Only flows of type Subprocess can be chosen.
  - If the node waits and the mode is Parallel or line-by-line-stop, one terminated child terminates the parent. If it does not wait, the parent ignores the children's results.
  - The child cannot see the parent's records unless they are passed as parameters, because each run has its own execution context.
  - No nesting depth is documented. No cached help.nocoly.com/workflow page mentions nesting.
  - No output parameters are documented. The global-variables page names app-level variables as the way to pass subprocess results back.
- *ERP use (inference):* anything over 100 rows (stock moves per order line), upsert per imported row, purging more than 1,000 staging rows, one approval logic shared by an on-create flow and a Submit button (the page's own example).
- *Source:* https://help.nocoly.com/workflow/node-subflow , https://help.nocoly.com/workflow/workflow-execution-limits

**PBP (Packaged Business Process) and Call PBP**
- *What:* a flow with no data source. It starts with typed input parameters and returns output parameters. Every workflow in the organisation can call it, though it is managed in one app. It can also have its own API.
- *Create:* the app's workflow module › [PBP] › [Create New PBP]. It can be called only after it is published.
- *Input parameters:*
  - Types: Text, Number, Members, O-roles, Department, Date/Time, File, normal arrays (`["A","B"]`), object arrays (`[{"name":"A","age":20}]`).
  - Members and departments are passed as objects, not text.
  - Each parameter has a required flag and a description.
  - Pasting a JSON array generates parameters.
  - Arrays from a code block must go through JSON Parsing first.
- *Output parameters:* defined in the Output Parameters node (delete the blank one if none are needed). Files are not supported: return a record ID and let the caller fetch the record.
- *Call PBP options:*
  - Perform once / Perform multiple times.
  - Multiple, Based on field value: the number of runs comes from a field. No limit.
  - Multiple, Based on the amount of data in multiple data objects: one run per row. **≤ 100 rows** if any passed parameter uses a field of those rows, otherwise **≤ 10,000**.
  - Parallel runs are allowed (the page's inventory example uses them).
  - The "wait" option must be on to use outputs. The docs label it variously: "After the business process is executed, start the next node" or "Wait for the business process to finish before starting the next node".
  - Parameters take node fields or fixed values (for example 0 = in, 1 = out).
- *API capability:*
  - Switched on at [Configuration] > [API Capability].
  - Address generated automatically, for example `https://www.nocoly.com/api/workflow/hooks/…`. An added sub-path is only cosmetic.
  - Authentication: Use Application Authorization (appKey and sign) or No Authorization Required.
  - Give parameters aliases for the API: a name in Chinese without an alias may cause errors.
  - Five response methods (not listed in the page text).
  - The PBP cannot return parameters to the caller if it contains Call PBP, Approval, Fill in, Delay, Subflow or other nodes of uncertain duration.
  - Response parameters take English names and examples.
  - Listed in the app's API documentation with sample code.
- *Custom pages:* a button can call a PBP directly, or scan a code first (record link, other link or text) and pass the result.
- *Limits:* [Plan page] PBP: Professional only.
- *Doc examples:*
  1. Update inventory: product ID, in/out flag and quantity, called per receipt line in parallel.
  2. Phone-number region from an external API.
  3. Order query API for an external system, returning the order and its lines as an array.
  4. Payment process: create a Payment record, Fill in for finance, return the record ID.
  5. Scan a device code on a custom page and close its work orders.
- *ERP use (inference):* the shared logic in the foundation plan (Convert quantity, Convert amount, Price for product), plus post stock move, next sequence number and credit-limit check; outbound APIs for partners.
- *Source:* https://help.nocoly.com/workflow/pbp , https://help.nocoly.com/workflow/trigger-mode

**Workflow parameters and Update Parameters**
- *What:* variables that live for one run and are cleared at its end. Any node can read them.
- *Options:*
  - Defined in the workflow settings. No limit on how many.
  - Types: Text, Number (Currency), Date/Time, Array, Object Array, Member, Department, Organization Role.
  - Name: starts with a letter, then letters, numbers and underscores.
  - A description, shown where the parameter is used.
- *Values:* none at creation. Set them with an Update Parameters node (configured like Update Record fields), or receive them from a parent's Subprocess node. Define them in the subprocess, either from the node or from the subprocess's settings.
- *ERP use (inference):* running totals, flags and cursors, and the target record ID handed to a subprocess. In the page's example, each order run adds its amount to a Statistics record found by a passed ID.
- *Source:* https://help.nocoly.com/workflow/node-update-parameters

**Global variables and Update Global Variables**
- *What:* named values shared across workflows (app level) or across apps (organisation level). Any node that accepts dynamic values can read them. The Update Global Variables node changes them.
- *Organisation level:* [Org Admin] > [App Management] > [Global Variables] > Organization. Available to the entire organisation (default) or to chosen apps. A setting decides whether workflows may update the variable.
- *App level:* [App Management] > [Global Variables] in the app, by app admins or developers. Current app only. It supports passing values between workflows, for example subprocess results to the parent.
- *Types:* text and number only. Text can use Mask Display: masked in use, and app admins can reveal it on the management page.
- *After creation:* name and type are read-only; value and authorisation can change. Operation logs: organisation admins see all of them; app admins and developers see their app's.
- *Limits:* [Plan page] Global variables: Professional only.
- *ERP use (inference):* company defaults (base currency, default tax), API keys (masked), the last-sync cursor of a scheduled import, an on/off switch for an integration.
- *Source:* https://help.nocoly.com/workflow/node-update-global-variables

### 2.4 Integration nodes

**Send API Request**
- *Modes:* Send Custom Request (GET, POST, PUT, DELETE, HEAD, PATCH) and Send Specified Data Object (pushes a node's record to a URL).
- *Options:*
  - API URL: static and dynamic parts.
  - Proxy and SSL-verification switches. An organisation admin sets the proxy under Integration > Security > Data & Access.
  - Headers, for example `Authorization`.
  - POST body: form-data, x-www-form-urlencoded, raw or binary (binary = one file).
  - Success status codes (comma-separated) and error codes with messages; errors show in the run history.
  - Test API: asks for test values of dynamic parameters and remembers them.
  - Import JSON response sample: builds the response structure.
  - On timeout or failure: Continue Execution (later nodes skip only the fields that use this node's output) or Terminate Workflow.
- *Limits:*
  - **10-second timeout.**
  - Requests leave from 123.59.59.220 or 106.75.14.110, picked at random per request.
  - The page's closing note: data POSTed to the URL must get HTTP 200 within 10 s. Otherwise it is resent, up to 10 times, then dropped.
- *Results:* a single object maps straight into Add Record or Update Record. An array goes through Get Multiple Data (retrieve from object array) first.
- *ERP use (inference):* push an approved purchase order to a supplier system, submit e-invoices, book couriers, fetch exchange rates, sync stock to web shops.
- *Source:* https://help.nocoly.com/workflow/node-send-api-request

**JSON Parsing**
- *What:* turns JSON from a Code Block or Send API Request node into variables or arrays, using JSONPath.
- *Options:*
  - Source node.
  - View Parsing Result: the structure, sample values and the JSONPath of each item.
  - Output parameters: generated with one click or typed as JSONPath, with a preview.
  - Custom error messages: conditions on output values, fixed or dynamic text, then Continue execution or Terminate workflow.
- *JSONPath:*
  - `$` is the root.
  - Dot or bracket notation, for example `$.store.book[0].title`.
  - Filters such as `[?(@.price > 10)]`, combined with `&&` and `||`.
  - Strings in single or double quotes.
- *Limits:* array outputs need a Get Multiple Data node to become rows. Only Code Block and Send API Request are named as sources.
- *ERP use (inference):* pick the MYR rate, an e-invoice UUID or a tracking number from a response without a code block.
- *Source:* https://help.nocoly.com/workflow/node-json-parsing

### 2.5 Documents and messages

**Get Record Print File** (index name: Print Record)
- *What:* makes a Word or Excel file from one record with a print template, and optionally a PDF.
- *Options:*
  - Print Object: the node with the record.
  - Print Template: a Word or Excel template of that worksheet.
  - File Name: a field, fixed text, or both. Default: the record title. Not allowed: `/ \ : * ? " < > |`.
  - Generate File: Word or Excel according to the template type. Switch on PDF to add one.
- *Use:*
  - An Update Record node writes the file into a file field; a Send Email node attaches it.
  - One Update Record node adds one file type. For a second type, add another Update Record node with update method Add.
- *Limits:*
  - Paid plans only. [Plan page] Generate print files and Custom print templates: Standard and Professional.
  - Word and Excel files are free.
  - PDF is made by a WPS service at CNY 0.15 per successful file; failures are free, and one file is charged once even if several nodes use it. [Plan page] $0.03 per PDF generation.
  - File ≤ 100 MB; as an e-mail attachment ≤ 50 MB.
  - The flow waits until the file exists.
  - System print templates cannot be used.
- *ERP use (inference):* quotation, order confirmation, invoice, delivery slip, purchase order and statement PDFs, saved on the record and e-mailed.
- *Source:* https://help.nocoly.com/workflow/node-print-record

**Send Email**
- *Delivery method:*
  - Standard Delivery: To, CC and BCC. Recipients see To and CC, never BCC.
  - Individual Delivery (Bulk Send with Hidden Recipients): one e-mail per recipient; no CC or BCC.
- *Recipients:*
  - Fixed Email Address.
  - System User (the account needs an e-mail address).
  - Email Field.
  - Workflow Participants (requester, approver …).
  - Batch Data Nodes (an e-mail field of a Get Multiple Data result).
  - Sources are merged in configuration order; duplicates are removed and keep their first position.
- *Content:*
  - Subject and body take fixed text, field values and node outputs.
  - Body modes: Plain Text; Rich Text Editor (headings, bold, italic, underline, lists, links, images, tables; option Automatically Convert to Email-Compatible Format); MJML Editor (Advanced).
  - Fields are inserted from Node Object as `{NodeID.FieldID}`, or `{NodeAlias.FieldAlias}` once node and field aliases are set.
- *Sender:* Sender Name can be set. The sender address is the platform's and cannot be changed. A Reply-To Address can be set.
- *Attachments:* uploaded files, file fields and generated print files, **≤ 50 MB in total**.
- *Limits:*
  - **10 e-mails per hour to the same address.** More may be blocked.
  - Each recipient address costs one e-mail credit in either mode. [Plan page] $0.002 per e-mail; not on Free.
  - E-mail HTML: inline styles (no `<style>`), padding rather than margin, public absolute or Base64 images, web-safe fonts.
  - A table of records needs a code block (≤ 100 rows, no images). Its HTML goes into Rich Text mode or into a rich-text field.
- *ERP use (inference):* quotation or invoice with PDF, order and delivery confirmations, payment reminders, approval results, internal alerts.
- *Source:* https://help.nocoly.com/workflow/node-send-email

**Send SMS**
- *Before use:* Twilio (Global SMS) set up under Org Admin > Integration > System Services, and enough credits under Org Admin > Home.
- *Recipients:*
  - Typed numbers.
  - A Telephone field.
  - A Text field holding numbers.
  - Roles or departments (all their members).
  - Node objects (initiator, approver).
  - Numbers need a country code.
- *Content:*
  - A template = SMS signature + message type + body.
  - Signature: added for Mainland China; none for Hong Kong, Macau, Taiwan or other regions.
  - Message type: Mainland China only.
  - Body: fixed text and field values.
  - Create New Template. Templates can be edited or deleted; a deleted template stays in nodes that already use it.
- *Limits:*
  - If any selected user has no valid number, the node fails and **stops the workflow**.
  - Avoid full-width square brackets (U+3010, U+3011).
  - From the SMS troubleshooting page:
    - ≤ 500 characters including the signature.
    - Symbols such as the full-width yen sign (U+FFE5), ★, ✓ and ※ may come out garbled.
    - Outside Mainland China, **custom SMS requires the organisation's own Twilio account**, billed by Twilio.
    - Verification SMS without Twilio cost 2.3 credits each.
    - Mainland China: messages with links or phone numbers are likely to be blocked, and China Unicom and China Telecom may restrict delivery at night (about 23:00 to 07:00).
  - [Plan page] SMS: not on Free; priced by country.
- *ERP use (inference):* "shipped, tracking number …" (the page's example), delivery-slot and payment reminders.
- *Source:* https://help.nocoly.com/workflow/node-send-sms , https://help.nocoly.com/workflow/sms-failure

**Audio Notification**
- *What:* plays a sound or spoken text to the triggering user or to chosen users.
- *Options:*
  - Recipients: the triggering user by default; others can be added. They must be signed in.
  - Audio mode: a system sound, or an MP3/WAV file ≤ 10 MB.
  - Voice mode: language, tone, speech rate and Content; Tryout plays it.
- *Limits:*
  - Plays only when a user started the flow directly.
  - Allowed in worksheet-event flows, button flows and PBPs; not in date-field, scheduled, webhook or subprocess flows.
  - A PBP plays when called from a custom-page button, an API query field or a control event, but not when a button flow calls it.
  - Plays on PC web first, otherwise in the mobile app in the foreground. Not in mobile browsers, mini programs, WeCom, DingTalk or Feishu.
- *ERP use (inference):* scan feedback in the warehouse ("OK" / "wrong lot"), like Odoo Barcode's sounds.
- *Source:* https://help.nocoly.com/workflow/node-voice-broadcast

**Send WeChat Official Account Template Message**
- *Options:* Send to (for example the record creator, an external user); Select Template (from the WeChat Official Accounts Platform); Details Link (an H5 page, for example the portal record URL).
- *Limits:* recipients must follow the connected Official Service Account.
- *ERP use (inference):* none for Malaysia; China-facing portals only.
- *Source:* https://help.nocoly.com/workflow/node-send-wechat-official-account-template-message

**Create Task**
- *What:* creates a Task in the collaboration module.
- *Options:* project (any the operator can see) and board; name and description (fixed text, field values or both); owner, members, planned start and end (picked from lists).
- *Limits:* [Plan page] Collaboration suite: Standard and Professional.
- *ERP use (inference):* a task per service line of a confirmed order (Odoo `sale_project`). A collaboration task is not a worksheet record, so ERP reports and relations do not reach it (inference).
- *Source:* https://help.nocoly.com/workflow/node-new-task

### 2.6 External users (portal)

**Invite External User**
- *What:* sends an SMS invitation to register for the portal, and creates the portal user with status Inactive.
- *Options:* Invite One User / Invite Multiple Users Based on Multiple Records.
- *Limits:*
  - CNY 0.05 per SMS, taken from the organisation balance.
  - **No overseas numbers.**
  - **No e-mail invitations.**
  - [Plan page] 100 external portal users on every plan; extra packs cost $25 per 100 users a month, $50 per 1,000 or $250 per 10,000.
- *ERP use (inference):* Odoo's "Grant portal access", but not for +60 numbers if the docs hold.
- *Source:* https://help.nocoly.com/workflow/node-invite-external-user

**Get Single External User** (as described in this slice; the node's own page is in part 1)
- *Options:* take the user from an External User field of the record, or search the portal user list by a unique value such as the mobile number.
- *Matching:* with several matches, the most recently registered user wins. Random Selection picks any one instead.
- *Source:* https://help.nocoly.com/workflow/node-update-external-user-info

**Update External User Info**
- *What:* changes a portal account: name, role, account status and custom information-collection fields.
- *Limits:* status switches only between Active and Disabled. An Inactive user (invited, not registered) cannot be changed.
- *ERP use (inference):* block portal access for a blocked customer; move a customer to a distributor portal role.
- *Source:* https://help.nocoly.com/workflow/node-update-external-user-info

### 2.7 Approvals and to-do

**Initiate Approval Flow versus Approval**
- *Docs:* Initiate Approval Flow is an approval block that groups approval, fill-in, branch and CC nodes. Compared with a bare Approval node:
  - approvers act in the worksheet record itself;
  - app admins can end the process or replace operators;
  - the process can go on after a withdrawal;
  - it gives one approval result to later nodes;
  - it can be saved as a template and reused.
- The docs recommend Initiate Approval Flow.
- *ERP use (inference):* PO approval by amount, discount approval, credit-limit override, expense approval.
- *Source:* https://help.nocoly.com/workflow/nodes-comparison (node details are in `workflow-1.md`)

**Workflow To-Do**
- *Where:* web: the To-Do icon on the home page or inside an app; mobile: Home › My Workflow.
- *Tabs:*
  - Approve & Fill in: batch approval if enabled. **Required fields are ignored in batch approval.**
  - CC: messages from CC nodes; mark read, or Mark All as Read. Send Internal Notification messages do not appear here.
  - Submit: my pending submissions, with progress, recall and reminders.
  - Completed: the current and previous year; older items are in To-Dos History.
- *Badge:* the count of approvals and fill-ins, shown up to 99. A red dot when only CCs wait.
- *Filter and sort:*
  - Filters: initiator, organisation, application, workflow type.
  - Several keywords are combined with AND, and then only the summary field is searched.
  - Sort: overdue first (default), newest or oldest.
- *Admins:* follow flows they are not part of through the execution history or Records.
- *ERP use (inference):* "My approvals" for purchases, sales discounts and expenses.
- *Source:* https://help.nocoly.com/workflow/to-do

### 2.8 Managing, testing, limits and quotas

**Managing one workflow**
- *Edit:* name and description; global configuration (execution settings, automatic approval; see `workflow-1.md`); nodes.
- *Test, two ways:* test the edited version on a chosen record, or Execute a published flow now.
  - Quick test works for worksheet-event, scheduled, date-field and custom-button flows, subprocesses and PBPs.
  - The record must meet the trigger filter.
  - A delete-triggered test does not delete the record.
  - **Field updates really happen.**
  - The tester counts as the initiator, and the test time as the trigger time.
  - Testing the edited version: CC, internal notification, SMS and e-mail go to the tester; approval and fill-in pass automatically; subprocesses, PBPs and approval processes are skipped and must be tested separately.
  - Executing a published flow: you choose whether messages go to yourself or to the configured recipients.
- *Publish updates:* needed for changes to apply. Runs already started keep the configuration they started with.
- *Move to another app:* only flows not triggered by worksheet data: webhook, scheduled (not date-field), organisation member events (not external users), PBP.
- *Convert:* worksheet-event, custom-button and date-field flows → subprocess; a subprocess whose data source is an object array → PBP.
- *Delete and restore:*
  - Deleted flows go to a recycle bin, available in paid editions only ([Plan page]: Standard and Professional).
  - They are kept 60 days, then deleted for good.
  - A restored flow comes back disabled.
  - Only app admins and developers can delete or restore.
- *Source:* https://help.nocoly.com/workflow/single-workflow-management

**Workflow execution limits**
- Subprocess: 100,000 executions an hour.
- Webhook: 10,000 requests an hour.
- Slow queries:
  - Queries over 1 second are counted per worksheet per minute.
  - At 300, further requests are refused for a while.
  - Affected flows retry up to 10 times ("Request rate limited. The workflow will retry automatically later."), then fail.
- *Advice in the docs:*
  - Index the fields used in filters and sorting (not every field).
  - Keep Get Single Data and Get Multiple Data conditions minimal, and set record limits.
  - Avoid hitting one worksheet at high frequency.
  - Use fewer relationship, rollup, sort and aggregate operations in queries.
  - Split big jobs into smaller batches.
- *Source:* https://help.nocoly.com/workflow/workflow-execution-limits

**Execution add-ons and plan quotas**
- *Docs (this slice):*
  - Org Admin › App Management › Workflow › Purchase Upgrade Package.
  - Recurring Monthly Add-on: ¥600 a year per extra 10,000 executions a month (600 × N × remaining years).
  - One-Time Monthly Add-on: ¥10 per 1,000, current month only.
  - Credits or Alipay apply at once; bank transfer is processed by hand.
  - Auto-Purchase (recommended by the page): when less than 2% is left, it buys ¥100 for 10,000 from credits. Switch it off at Admin Console › Home › Credits › Manage.
- *[Plan page]:* executions per month: Free 1,000; Standard 100,000; Professional 500,000. Extra executions $0.01 each (not on Free). The CNY figures above do not match.
- *Source:* https://help.nocoly.com/workflow/package

### 2.9 Every node type on the index page

The index (`nodes`) lists 44 entries. "Part 1" means `workflow-1.md`.

| Node (index name) | Detailed in | What this slice adds |
|---|---|---|
| Add Record | part 1 | Member-join example adds a record; batch create from a Get Multiple Data set |
| Update Record | §2.2 | — |
| Get Single Data | part 1 | Loop example: random pick, returns no record when none is left |
| Get Multiple Data | part 1 (2 pages; one is `process-subform-data`, here) | "Get the associated records" reads subform rows. "Retrieve from object array" turns API or JSON arrays into rows. Query and Batch Delete takes ≤ 1,000 records |
| Delete Record | part 1 | — |
| Jump To | §2.3 | — |
| Calculation | part 1 | — |
| Branch | part 1 | Drives has-more paging in the Loop example |
| Rollup | §2.2 | — |
| Calibrate | part 1 | — |
| Initiate Approval Flow | part 1 + `nodes-comparison` here | §2.7 |
| Approval | part 1 | §2.7. Prevents a PBP from answering an API caller |
| Fill in | part 1 | Used for finance in PBP example 4. Prevents a PBP from answering an API caller |
| CC & Send Internal Notification | part 1 | Internal notifications do not show in To-Do › CC; edit-mode tests send them to the tester |
| Send SMS | §2.5 | — |
| Send Email | §2.5 | — |
| WeChat Official Account | §2.5 | — |
| Interface Push | part 1 | — |
| Audio Notification | §2.5 | — |
| Delay | part 1 | Prevents a PBP from answering an API caller |
| AI Agent | part 1 | — |
| Knowledge Retrieval | no cached workflow page | — |
| AI Generated Text | part 1 | — |
| AI Data Object Generator | part 1 | — |
| Get Link | part 1 | — |
| Loop | §2.3 | — |
| Subprocess | §2.3 | — |
| Call PBP | part 1 (node page) + `pbp` here | §2.3 |
| Call Integrated API | part 1 | — |
| Print Record | §2.5 (Get Record Print File) | — |
| Get Page Snapshot | part 1 | — |
| Update Parameters | §2.3 | — |
| Update Global Variables | §2.3 | — |
| Update Record Followers | §2.2 | — |
| Terminate Process | part 1 | Called "Abort Process" on the Loop page, where it stops one iteration |
| Get Single Data from User/Department/O-Roles | part 1 | — |
| Get Multiple Data from User/Department/O-Roles | part 1 | "Get Multiple Members" feeds dynamic followers |
| External User-Related (4 pages) | part 1 (Get Single/Multiple External User) + §2.6 | — |
| Create Task | §2.5 | — |
| Create Event | part 1 | — |
| Send API Request | §2.4 | — |
| Code Block | part 1 | ≤ 100 rows (e-mail table recipe). Arrays from it must be JSON-parsed before they can feed PBP inputs |
| JSON Parsing | §2.4 | — |
| Custom Node | `https://help.nocoly.com/plugin/node` (another slice) | — |

## 3. Odoo rebuild notes

The "Native in HAP" column is from the docs. The "Falls short" column is partly inference, marked where it is.

| Odoo concept | Native in HAP (this slice) | Falls short |
|---|---|---|
| Automation rules (`base_automation`): on create, on update with trigger fields and a domain, on deletion | Triggered by Worksheet: event + trigger fields + trigger conditions | Runs after the save, so it cannot refuse one (inference; refusals belong to field and business rules). The delete flow runs after the record is gone |
| Automation rule based on a date field, with a delay | Triggered by Date Field: ± minutes, hours or days; yearly, monthly or weekly repeat; end time; filter | One date field per flow (inference). Dates already past at save: undocumented |
| Scheduled actions (`ir.cron`) | Triggered on Schedule, custom recurrence, Execute Now | No record context. Over 100 rows needs a subprocess. The holiday calendar behind "weekdays" is unknown |
| Server-action types: Update Record, Create Record, Execute Code, Send Email, Send SMS, Add/Remove Followers, Create Activity, Send Webhook Notification, Multi Actions | Update Record, Add Record, Code Block, Send Email, Send SMS, Update Record Followers, Create Task or Fill in, Send API Request › Send Specified Data Object, a chain of nodes or a subprocess | Code Block is Professional only ([Plan page]) and takes ≤ 100 rows (Send Email page; details in part 1) |
| Shared model methods (`stock.quant._update_available_quantity`, `res.currency._convert`, pricelist price, `ir.sequence.next_by_code`) | PBP with typed inputs and outputs, called by Call PBP from any app | Professional only. Outputs cannot be files. No transaction around the steps (inference) |
| Loops over recordsets (`for line in order.order_line`) | Subprocess per record (parallel or one by one), or the Loop node | Each record or iteration is a billed execution. Caps: 10,000 iterations; 10,000 / 50,000 / 1,000,000 rows |
| Stored computed totals (`amount_total`, `amount_residual`) | Rollup node (Summary from Worksheet, relationship = record ID) + Update Record; or a rollup field (worksheet docs) | Rollup can lag slightly. Direct access and Dynamic give snapshots taken at different moments |
| Quantity bookkeeping (`stock.quant` increments, `qty_delivered`, `qty_invoiced`) | Update Record → Add / Minus | Safety under parallel runs is undocumented. Summing a move ledger with Rollup avoids the race but can lag (inference) |
| Smart-button counters ("3 Invoices") | Rollup → Get Data Count, written to a field | A snapshot that is stale until the next run (inference). For live counts, use relation views or rollup fields |
| Mail templates (`mail.template`) | Send Email: Rich Text or MJML, `{NodeAlias.FieldAlias}` placeholders | Fixed sender address. 10 e-mails an hour per address. Inline CSS only. Line tables need a code block (≤ 100 rows) |
| PDF reports (`ir.actions.report`: invoice, quotation, delivery slip) | Word or Excel print template + Get Record Print File (+ PDF) | Paid plans only. PDF billed per file. System templates cannot be used. Layout is built in Word, not QWeb |
| "Send & Print" on invoices, "Send by Email" on quotations | Button flow: Get Record Print File → Send Email with attachment → Update Record (sent flag, file) | As above. Customer replies go to the Reply-To address |
| Followers (`mail.followers`, `message_subscribe`) | Update Record Followers: Add / Remove / Overwrite | Followers are told of every new discussion; no subtypes (inference) |
| Activities (`mail.activity`), "My Activities" | Create Task (collaboration module), or Fill in + Workflow To-Do (part 1) | A collaboration task is not a worksheet record (inference). To-Do lists only approval, fill-in and CC items |
| Approvals (purchase double validation, discount limits) | Initiate Approval Flow (recommended by the docs) | Detailed rules are in part 1 |
| SMS (`sms` module) | Send SMS with templates and field placeholders | Outside Mainland China, custom SMS needs your own Twilio. One user without a number stops the flow |
| Portal access (`portal.wizard`, "Grant portal access") | Invite External User; Triggered by External User; Update External User Info | Invitations by SMS only: no overseas numbers, no e-mail. Inactive users cannot be changed. 100 portal users per plan ([Plan page]) |
| Employees kept in step with users (`hr.employee`) | Triggered by Member Events → Add Record or Update Record | Only join and leave events are documented (no department change) |
| External API (JSON-RPC), custom controllers | PBP with API capability (app authorisation, aliases, response parameters); webhook flows are listed in the app's API docs | No direct reply to the caller if the PBP holds approval, fill-in, delay, subprocess or Call PBP nodes |
| "On webhook" automation rules, payment-provider callbacks | Triggered by Webhook: sample parsing, required parameters, App Authorization, IP whitelist | 10,000 requests an hour. Open to anyone with the URL unless secured |
| Outbound integrations (e-invoicing, couriers, banks) | Send API Request + JSON Parsing (+ Call Integrated API, part 1) | 10 s timeout. The documented outbound IPs may not be Nocoly's. Resends can create duplicates |
| Automatic currency rates (`currency_rate_live`, not in the Community code) | Schedule → Send API Request → JSON Parsing → Add Record | 10 s timeout per call |
| System parameters (`ir.config_parameter`), company defaults | Global variables (organisation or app; text or number; Mask Display) | Professional only. Text and number only. Name and type cannot change |
| Context values passed between methods | Workflow parameters (one run) | No initial values. No boolean type: use text, as the Loop example does |
| Multi-record server actions ("Create Invoices" from several orders) | Custom action for bulk actions + Rollup batch data source + Add Record | The batch-source Rollup works only in bulk-button flows |
| One2many lines created by code | Batch add to a subform with an entity sheet; Add Record from a set | Subforms without an entity sheet cannot be written by workflows |
| Barcode app scan feedback | Custom-page scan button → PBP → Update Record + Audio Notification | Sound only for direct user triggers, and not in mobile browsers. A button flow that calls a PBP stays silent |
| Record links in e-mails (share URLs, portal tokens) | Record page URL built from IDs (`rowid` page); Get Link node (part 1) | The rowid link needs a sign-in and that view's permissions |
| `create_date`, `write_date`, `fields.Datetime.now()` | Creation Time, Last Modified Time, Trigger Time, System Current Time | — |
| Back-to-draft and resubmit cycles | Jump To (≤ 20 jumps a run) | Earlier side effects run again |

**Build patterns the docs point to (inference, not tested)**
- *More than 100 rows:* Get Multiple Data (query) → Subprocess (Parallel, or one by one when order matters) → per-record logic. Cost = rows + 1 executions.
- *Paged import:* Schedule → Loop While Conditions Are Met (hasMore, cursor) → Send API Request → JSON Parsing → Get Multiple Data (object array) → Subprocess upsert.
- *Document out:* Button → Get Record Print File (PDF) → Update Record (file field) → Send Email (attachment, Reply-To).
- *Shared rule:* PBP with typed inputs and outputs, called with Perform once and the wait option on. This is the closest match to the foundation plan's "Convert quantity", "Convert amount" and "Price for product", which are subprocesses today. A subprocess has no documented outputs.

## 4. Traps

**Cost and plan**
1. *Execution counting conflicts (docs):* the subprocess page says "A single subprocess execution does not count toward the organization's workflow execution usage", then counts the parent + child as 2 executions and 500 records as 501.
2. *Volume costs executions (docs):* every loop iteration and every subprocess record is one execution. Inference: a nightly run over 3,000 products costs about 90,000 executions a month, almost all of Standard's 100,000.
3. *Prices disagree (docs vs [Plan page]):* this slice quotes CNY (add-ons ¥600 or ¥10, PDF CNY 0.15, invitation SMS CNY 0.05, payment by Alipay). The Nocoly plan page quotes USD: $0.01 per execution, $0.03 per PDF. The CNY pages look like Mingdao text (inference).
4. *Auto-Purchase (docs):* the add-on page recommends Auto-Purchase. Once fewer than 2% of executions remain, it buys ¥100 of executions from credits without asking.
5. *Plan gating ([Plan page]):* PBP, Loop, Code Block, Global variables and condition groups are Professional only. Inference: a module sold to a Standard customer cannot depend on them.

**Silent truncation**
6. Loop stops at 10,000 iterations and the flow continues as if the loop had finished (docs).
7. Jumps after the 20th are not executed (docs). What the run does next is not stated.
8. A subprocess fed from a worksheet takes 50,000 records by default unless "Get all records" is on (max 1,000,000). Arrays stop at 10,000 rows. The docs do not say what happens to the rest.
9. Get Data Count gives 100 or 135 for the same data, depending on "Limit results based on the number of summary objects" (docs).
10. Call PBP per row: ≤ 100 rows as soon as any parameter uses a field of the rows, otherwise 10,000 (docs).

**Side effects and partial work**
11. Jump To re-runs the target and every later node, including notifications, record creation and API calls (docs).
12. Tests are real (docs): field updates happen. Testing the edited version sends messages to the tester only. Executing a published flow can send them to the real recipients, for example customers.
13. Continue Execution after an API or JSON failure skips only the fields that depend on the failed node. The rest of the record is still written, leaving it half updated (docs; the consequence is inference).
14. Send API Request resends up to 10 times when HTTP 200 does not come back within 10 s (docs). Inference: a slow receiver that still processes each request gets duplicates unless it is idempotent.
15. A jump from a parallel branch ends all other branches (docs).
16. When the Subprocess node waits and runs Parallel or line-by-line-stop, one terminated child terminates the parent (docs).

**Freshness and context**
17. Rollup Summary from Worksheet can lag behind recent writes. Direct access and Dynamic access give different snapshots (docs).
18. Rollup cannot aggregate related records read through a relationship. Query the worksheet with "relationship = record ID" (docs).
19. A scheduled flow has no record to update until it queries one (docs).
20. A subprocess cannot see the parent's records. Pass the IDs as workflow parameters (docs).
21. PBP outputs can be selected only when the wait option is on (docs).
22. Publishing an update does not change runs already in progress (docs).
23. The date-field trigger re-arms when the date changes, and End Time exists only for repeating flows (docs).
24. Schedules are anchored on the start time. "Weekdays" skip holidays of an unstated calendar (docs). Inference: if it is China's calendar, flows would skip Chinese holidays and run on Malaysian ones.

**Messaging and portal**
25. Send Email (docs): at most 10 e-mails an hour per address (a shared inbox such as accounts@ hits this quickly), a fixed platform sender, and inline CSS only.
26. Send SMS (docs): one selected user without a number stops the whole flow. Outside Mainland China, custom SMS needs Twilio. Full-width square brackets (U+3010, U+3011) are reserved. 500-character limit.
27. Invite External User (docs): SMS only, never to overseas numbers, no e-mail invitations.
28. Audio Notification is silent for indirect triggers: a flow started by another flow, a button flow calling a PBP, scheduled, date and webhook flows (docs).
29. WeChat recipients must follow the Official Service Account (docs).
30. Batch approval in the To-Do list ignores required fields (docs).
31. Update External User Info cannot change Inactive users. Get Single External User by mobile number silently takes the latest registration when numbers repeat (docs).
32. A member "joins" only after completing their profile or after admin approval, and restoring a member also counts as a join (docs).

**Data shape and security**
33. Workflow parameters start empty. Loop system parameters cannot be updated. Custom loop parameters must be added in the loop's first node (docs).
34. Global variables: name and type cannot change, and only text and number exist (docs). Inference: they are shared by every run, so using them to return subprocess results races between concurrent runs.
35. PBP inputs (docs): Chinese parameter names need API aliases; members and departments travel as objects; code-block arrays need JSON Parsing; files cannot be outputs.
36. A PBP API set to "No Authorization Required" is public. So is a webhook URL without App Authorization or an IP whitelist (docs).
37. A Region/City value needs "/" between levels, or it is not written (PBP example 2, docs).
38. Print (docs): system print templates are not supported. One Update Record node adds one file type. The flow waits for the file.
39. Subforms without an entity sheet cannot be written by workflows, and Rollup needs subform rows stored as an entity worksheet (docs).
40. Record links depend on the view, and Record IDs are visible only in table views (docs).
41. Runs not started by a person carry `user-api`, `user-workflow` or `user-publicform` as the user ID (docs). Logic that reads "triggered by" must expect them.
42. More than 300 slow queries per worksheet per minute are refused, retried 10 times, then failed (docs).
43. Only flows not triggered by worksheet data can move between apps. Restored flows come back disabled. The recycle bin keeps flows for 60 days (docs).
44. The webhook page places response settings under "[Workflow Configuration] > [AI Capabilities]". This is probably mislabelled (docs text; the reading is inference).
45. The outbound IPs on the Send API page (123.59.59.220, 106.75.14.110) may be Mingdao China's. Check them before asking partners or banks to whitelist them (inference).

## 5. To verify live

All on a test app in Odoo Replica (AI), never on EMS or customer apps. Each item gives the claim, why it matters, and a suggested check.

1. **Plan and feature gates.** Which plan the organisation is on, and whether PBP, Loop, Code Block, Global variables and condition groups are enabled. This decides whether modules can be sold to Standard customers. Check Org Admin › plan and try to add each node.
2. **Execution counting.** Is a subprocess run counted, and is a loop iteration? This drives the quota budget. Run 5 records through a subprocess and a 5-iteration loop, then read the usage counter before and after.
3. **Add / Minus under concurrency.** Twenty parallel subprocess runs each Add 1 to the same number field: does the field end at 20? Stock and balances depend on it. The docs' own statistics example relies on it.
4. **Rollup freshness.** Batch-add 3 lines, then immediately run Rollup (Direct access): are they included? This matters for order totals computed right after line creation.
5. **Send API Request behaviour.** The real outbound IP from Nocoly SaaS, the 10 s timeout, and how many resends a slow or failing endpoint receives. Use our own test endpoint only.
6. **Send Email on Nocoly.** The actual sender address and domain, Reply-To, the 10-an-hour cap, MJML availability and the credit cost per recipient.
7. **SMS to a Malaysian (+60) number**, with and without Twilio. Delivery notices and reminders depend on it.
8. **Portal invitation to +60 numbers.** Is it blocked as the docs say? This decides how Odoo's "Grant portal access" is rebuilt.
9. **PDF generation.** The price on our organisation (CNY 0.15 or $0.03), plan availability, how faithfully a Word template renders, and how long it takes.
10. **"Weekdays" schedules.** Which holidays are skipped, and whether a custom Monday-to-Friday schedule also skips them.
11. **Date-field trigger.** What happens with a date already past at save, and which time zone applies to the default 08:00. Due-date reminders depend on it.
12. **Webhook and PBP responses.** Where the webhook response settings really are; the five PBP API response methods; the time limit for a synchronous reply.
13. **Call PBP per row.** The 100 versus 10,000 limits, and which execution modes are offered besides parallel.
14. **Loop at 10,000.** Is any warning logged when the cap ends a loop early?
15. **Jump To past 20 jumps.** Does the run continue past the node or stop?
16. **Audio Notification** from a custom-page scan button → PBP, on PC web and in the mobile app (the warehouse feedback idea).
17. **Global variables.** Two concurrent runs updating one number variable; whether add and subtract exist; how Mask Display behaves in API headers.
18. **Subprocess caps.** More than 50,000 source rows without "Get all records": is the rest dropped silently?
19. **JSON Parsing sources.** Can it parse JSON held in a text field or a webhook body, or only Code Block and Send API Request output?
20. **Test-message routing.** Confirm that an edited-version test e-mails only the tester before testing customer-facing flows.
21. **Create Task.** Is the collaboration module available on our Nocoly SaaS plan?
22. **Batch approval.** Can it be switched off per flow, given that it skips required fields?
23. **Portal user updates.** Update External User Info on an Inactive user, and Get Single External User when two users share a mobile number.
24. **Subprocess nesting and outputs.** The maximum nesting depth (undocumented), and whether anything besides app-level global variables can return a child's result.

## 6. Coverage

All 38 pages of the slice, in slice order.

| # | URL | Title | Summary |
|---|---|---|---|
| 1 | https://help.nocoly.com/workflow/node-invite-external-user | Node - Invite External User | SMS invitation to the portal; creates an Inactive portal user; CNY 0.05 each; no overseas numbers, no e-mail |
| 2 | https://help.nocoly.com/workflow/node-json-parsing | Node — JSON Parsing | JSONPath extraction from Code Block or API output into variables or arrays; custom errors; JSONPath primer |
| 3 | https://help.nocoly.com/workflow/node-jump-to | Node - Jump To | Jump to a node on the same branch or the main flow, optional conditions; parallel and approval rules; 20 jumps per run |
| 4 | https://help.nocoly.com/workflow/node-loop | Node - Loop | Count and condition loops, parameters, termination options, reuse; 10,000 iterations; each iteration one execution |
| 5 | https://help.nocoly.com/workflow/node-new-task | Node – Create Task | Creates a collaboration Task: project, board, owner, members, dates, description |
| 6 | https://help.nocoly.com/workflow/node-print-record | Workflow Node - Get Record Print File | Word or Excel from a print template, optional paid PDF; save to a field or attach; 100 MB and 50 MB limits |
| 7 | https://help.nocoly.com/workflow/node-rollup | Node - Rollup | Summary from worksheet (no row limit), Get Data Count, bulk-button totals; direct versus dynamic results |
| 8 | https://help.nocoly.com/workflow/node-send-api-request | Node — Send API Request | Custom HTTP requests or record push; headers, bodies, tests, error handling; 10 s timeout; outbound IPs; resends |
| 9 | https://help.nocoly.com/workflow/node-send-email | Node - Send Email | Delivery modes, recipient sources, rich text and MJML, aliases, Reply-To, 50 MB attachments, 10 an hour; HTML table recipe |
| 10 | https://help.nocoly.com/workflow/node-send-sms | Node — Send SMS | Twilio and credits, recipient sources, templates (signature, type, body); fails if a user has no number |
| 11 | https://help.nocoly.com/workflow/node-send-wechat-official-account-template-message | Node - Send WeChat Official Account Template Message | Template message with a detail link to followers of a WeChat service account |
| 12 | https://help.nocoly.com/workflow/node-subflow | Node - Subprocess | Reuse logic and fan out records; data limits, wait, triggering user, execution modes, termination, execution counts |
| 13 | https://help.nocoly.com/workflow/node-update-external-user-info | Node - Update External User Info | Find a portal user by field or mobile; update name, role, status (Active/Disabled) and custom fields |
| 14 | https://help.nocoly.com/workflow/node-update-global-variables | Global Variables | Organisation- and app-level variables (text or number, masking), permissions, logs, Update Global Variables node |
| 15 | https://help.nocoly.com/workflow/node-update-parameters | Workflow Parameters | One-run parameters: types, naming, Update Parameters node, passing to subprocesses; statistics example |
| 16 | https://help.nocoly.com/workflow/node-update-record | Node - Update Record | Choose the record node; set, clear, relation fields, To / Add / Minus, append |
| 17 | https://help.nocoly.com/workflow/node-updates-record-followers | Node - Update Record Followers | Add, remove or overwrite followers; followers get discussion notifications |
| 18 | https://help.nocoly.com/workflow/node-voice-broadcast | Node - Audio Notification | Sound or text-to-speech for users; only for direct user triggers; platform limits |
| 19 | https://help.nocoly.com/workflow/nodes | Introduction to Nodes in Workflow | Index of the 44 node entries |
| 20 | https://help.nocoly.com/workflow/nodes-comparison | Differences Between [Initiate Approval Flow] and [Approval] | Why the approval block is preferred over bare approval nodes |
| 21 | https://help.nocoly.com/workflow/package | Purchasing Workflow Execution Add-ons | Recurring and one-time execution add-ons in CNY; auto-purchase |
| 22 | https://help.nocoly.com/workflow/pbp | PBP | Packaged business processes: inputs, outputs, Call PBP modes and limits, API capability, five worked examples |
| 23 | https://help.nocoly.com/workflow/process-subform-data | Batch Process Data in Subform | Read subform rows through associated records; bulk add only to subforms with an entity sheet |
| 24 | https://help.nocoly.com/workflow/recordid | Using Record IDs in Workflows | Filter related records with "relationship is Record ID" |
| 25 | https://help.nocoly.com/workflow/rowid | Introduction to Record ID (rowid) | 36-character unique ID; shown in table views; building record page URLs |
| 26 | https://help.nocoly.com/workflow/single-workflow-management | Managing Individual Workflows | Edit, test (two modes), publish, move between apps, convert, delete and restore |
| 27 | https://help.nocoly.com/workflow/sms-failure | Not Receiving SMS Messages? | China SMS compliance, formatting rules, Twilio for numbers outside Mainland China, billing table |
| 28 | https://help.nocoly.com/workflow/times | Time Types in Workflows | Trigger time versus creation time versus system current time |
| 29 | https://help.nocoly.com/workflow/to-do | Workflow To-Do | To-do tabs, badges, batch approval, filters and sorting |
| 30 | https://help.nocoly.com/workflow/trigger-by-date-field | Workflow Trigger - Triggered by Date Field | Date and date-time triggers with offsets, recurrence, end time and filters |
| 31 | https://help.nocoly.com/workflow/trigger-by-external-user | Workflow Trigger - Triggered by External User | Portal register, login, account deletion and disable events |
| 32 | https://help.nocoly.com/workflow/trigger-by-personnel | Workflow Trigger - Triggered by Member Events | Member join and leave events, and the cases that fire them |
| 33 | https://help.nocoly.com/workflow/trigger-by-scheduled | Triggered on Schedule | Start and end time, recurrence types, custom schedules, Execute Now |
| 34 | https://help.nocoly.com/workflow/trigger-by-webhook | Trigger Mode – Trigger by Webhook | Webhook URL, sample parsing, required parameters, response, security |
| 35 | https://help.nocoly.com/workflow/trigger-by-worksheet | Workflow Trigger - Triggered by Worksheet | Worksheet, events, trigger fields, conditions |
| 36 | https://help.nocoly.com/workflow/trigger-info | Data Source ID & Execution Instance ID | Parts of the data source ID; the instance ID and how to open a run's log |
| 37 | https://help.nocoly.com/workflow/trigger-mode | Workflow Triggers | The nine trigger types |
| 38 | https://help.nocoly.com/workflow/workflow-execution-limits | Workflow Execution Limits | Subprocess 100,000 an hour, webhook 10,000 an hour, slow-query throttling and tuning advice |
