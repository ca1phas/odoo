# Native catalogue: what Nocoly HAP can do natively

Built on 23 Nov 2026 for the Odoo module programme. Rule from Li Wei: **native first**. Use HAP's native field types, views, rules, buttons and workflow nodes. Code (code blocks, custom fields, Compute pages) is a last resort, with a written reason. Before every module plan, look the needed features up here, then **try them live** in the sandbox app before fixing the design.

## Files

| File | What it is | Evidence |
|---|---|---|
| `fields.md` | Every field type, tried live on a probe sheet: settings, raw keys for CLI builds, rendering, limits, Odoo uses. Starts with an "Odoo field kind → native choice" table | **Live** on Nocoly SaaS, 23 Nov 2026 (probe sheet in the sandbox app) |
| `workflow-nodes.md` | Triggers and nodes, run rules, a native design for the 16 wave 0 behaviours, what EMS used code for, 18 live tests | CLI help, docs, EMS configuration (read-only) |
| `docs/worksheet-1.md`, `worksheet-2.md` | Worksheets, fields, forms, rules, records, import/export, print templates (81 pages) | Docs |
| `docs/workflow-1.md`, `workflow-2.md` | Workflows: triggers, nodes, approvals, PBP, limits, quotas (77 pages) | Docs |
| `docs/app-roles-portal-plugins.md` | Apps (copy, export, upgrade, languages), roles, portal, plugins (44 pages) | Docs |
| `docs/views-pages-charts-actions.md` | Views, custom pages, charts, custom actions (47 pages) | Docs |
| `docs/integration-api-ai.md` | Integration center, API, webhooks, AI (22 pages) | Docs |
| `docs/org-collab-faq-other.md` | Organisation, members and departments, FAQ, plans, collaboration modules (88 pages), plus a check for new pages | Docs, plus the live sitemap and pricing page |
| `docs/BRIEF.md`, `docs/read_pages.py` | How the digests were made; a reader for the cached pages (needs the workspace knowledge base) | |

**Coverage:** all 359 pages of help.nocoly.com (cache of 3 Nov 2026). Every digest has a page-by-page coverage table. On 23 Nov the live sitemap matched the cache; nothing is newer than 20 Oct 2026. Four unlisted pages were read live.

**Evidence rule:** docs are not runtime proof. Where a doc and a live test disagree, **the live test wins**. Example: the docs say regions outside China have two levels. Live, Malaysia has country › state › district, with ISO codes.

## Verified facts about our environment

- **Organisation:** Nocoly, **Professional** edition (licence to 27 Apr 2027, read with hap-cli on 23 Nov). PBP, loops, code blocks, condition groups and global variables are available. They are *not* available to customers on Standard (see Plan gates).
- **Time:** per the docs, native nodes and dates run in UTC+8 (Malaysian time). Records read back through the API in Malaysian time. Only the code-block clock is UTC; EMS adds 8 hours in code. Still to confirm with a live test.
- **Currency field:** the currency is fixed per field, chosen from 156 ISO currencies. This organisation defaults to **HKD**, so always set MYR. Nothing takes the currency from the record, and there are no exchange rates. Raw key: `advancedSetting.currency = {"currencycode":"MYR","symbol":"RM"}`.
- **Region field:** global range covers 249 countries, with states and districts. Ids are ISO-based: `MY`, `MY|MY-10`, `MY|MY-10-28`. Malaysia's numbers MY-01…MY-16 are the MyInvois state codes. Raw keys:
  - `enumDefault` 1 = Global;
  - `enumDefault2` 1 = country, 2 = state, 4 = all levels;
  - Targeted mode: `advancedSetting.chooserange` = country code, and the levels count from below the country.
  - Two Odoo countries are missing: XI and XK.
- **Phone field (Mobile type):** stores E.164 (`+60123456789`). The default country is set per field; the organisation default is Hong Kong, so set MY.

## Odoo → native, in short

The full table, with raw keys, is in `fields.md`.

| Odoo | Native HAP |
|---|---|
| char / text / html | Text / multi-line Text / Rich Text |
| integer, float (+ unit) | Number. A unit is display text only. A percentage stores a fraction (15 % = 0.15) |
| monetary in company currency | Currency field fixed to MYR |
| monetary in another currency (multi-currency documents) | Number plus a relation to Currencies, with a formula for display and the MYR amount. This is a native gap: no per-record currency |
| selection, statusbar | Single select. Colours, scores and a progress-bar (statusbar) style are all native |
| many2many tags | Multi-select with colours, an option set, and `allowadd` so users can type new tags. No parent tag: put it in the name |
| boolean | Check item |
| many2one / many2many | Relationship (single / multiple), optionally two-way |
| one2many lines | Subform on a real line sheet ("Use an existing sheet"). Lines can then take defaults from the product, use grid editing and import |
| parent_id trees | Self-relationship (creates the Parent/Child pair), plus the org (hierarchy) view or a Cascading picker |
| country, state, address | Region (Global, state level) plus Text for street, zip and city |
| phone / email / url | Phone (Mobile type) / Email / Text with link |
| res.users fields | Members, which also carry record permission |
| image, binary | Attachment |
| priority stars / favourite | Level |
| barcode | Text (16+ digit numbers break in Number) plus a Barcode display; scanning into relations is native |
| ir.sequence at creation | Autonumber. A gapless number given at posting needs a workflow counter |
| computed fields | Formula (number, function, date), Concat, Rollup, Foreign Field. Display-only or stored |
| onchange | Dynamic defaults and control events. **Form only**: not on import, API or workflow writes |
| SQL / Python constraints | Unique index (up to 5 per sheet, composite; only one row may be empty), business rules, "Mandatory Validation on Write", or a workflow check |
| record rules | Role record scope (All / Joined / Owned / subordinates), Members permissions, extended user info (Professional) |
| smart buttons | Query Records field (tab table, summary row, create button) |
| object buttons and wizards | Custom actions (dialogs that fill the record or a related record, then run a workflow). Button → workflow → Interface Push for "returns an action" |
| automated actions | Worksheet-event workflows. **No serial runs on update triggers** |
| scheduled actions | Scheduled or date-field workflows |
| shared server actions | PBP: inputs, outputs, callable from any workflow, a page button or the API (Professional) |
| approvals | Initiate Approval Flow and approval nodes: or-sign, co-sign, ratio, by department level, deadlines |
| chatter / followers | Record discussion and log / record participants |
| activities | No native activity view. An Activities sheet with views and buttons; a fill-in node with a deadline gives a native to-do (closes only by Submit) |
| list, kanban, calendar, hierarchy views | Table, Kanban/Gallery, Calendar, Org view. Gantt and Map are native (Enterprise-only in Odoo) |
| pivot / graph | Charts set up by an admin, on custom pages. Users cannot regroup on their own |
| QWeb reports | Word/Excel print templates: line tables, QR, barcodes, per-status templates |
| portal | External portal: separate roles, auto-approve lists. Limits: one role per user, no to-dos, web only, 100 users per plan |
| mail alias (email to record) | No native inbound email. Use a public form, or a webhook from a mail service |
| live currency rates | A scheduled workflow calls a rate API and writes Currency Rates; no code |
| vendor bill OCR | OCR field. Lines must go into a subform; only page 1 of a PDF is read |
| translations | App language pack (screens only). Translated record data needs one field per language |
| users, employees, teams | Organisation directory (departments, org roles, managers), plus an Employees sheet for custom data |

## Limits that shape designs

| Limit | Value |
|---|---|
| Fields per worksheet | 200. Odoo's res.partner has 225, so shared sheets need a field budget per module |
| Worksheets | 100 on Standard |
| Subform rows | 1,000 |
| Related records for a rollup, a stored foreign field, or "get through relation" | 1,000 |
| Relation picker | 50 records (dropdown) / 200 (card) |
| Get Multiple Data → add, update or delete | More than 100 rows terminates the run (default limit 100) |
| Batch update or delete by query | First 1,000 rows by sort, with no error |
| Sub-process | Up to 10,000 array rows or 1,000,000 worksheet rows |
| Loop | 10,000 iterations, then it carries on as if finished. Jump To: 20 per run |
| Code block | 100 input rows; Node 10 or Python 3.7 |
| Executions | Every loop pass and sub-process record counts. Professional 500,000 a month, Standard 100,000; extra US$0.01 each |
| Calculation node | 2 decimals by default (set it for prices and unit factors). Built-in functions treat empty values as 0 |
| Excel import | 20,000 rows, 10 MB, 200 columns. No defaults, no subforms. Dates must be YYYY-MM-DD |
| API | 1,000 rows per call; 20 writes per second per IP. A rate-limit error comes back as HTTP 200 with code 90001 |
| Kanban | 1,000 records |
| Map | 200 pins |
| Webhook | 10,000 requests per hour |
| Send API Request | 10 s timeout and up to 10 retries, so receivers need idempotency |
| Email | Fixed sender; about 10 per hour per recipient mailbox |
| Portal | 100 external users per plan |

## Run rules that shape every workflow

- Sequential, strict or partitioned runs exist only for create, delete and button workflows. **Update-triggered workflows always run in parallel.**
- A record runs one instance of a workflow at a time. Edits made while that instance runs or waits are **dropped**.
- A workflow's own writes never re-trigger it.
- **No transactions.** Failures, withdraws and terminations never undo earlier writes, so design every step to be safe to repeat.
- Required fields, dynamic defaults, control events and most business rules act **in the form only**. "Mandatory Validation on Write" extends required checks to other writes. Workflows and buttons can still write to read-only and locked records.
- HAP drafts are private and invisible to workflows. Model Odoo's draft state as a status value.
- A batch button runs its workflow **once** for the whole selection.
- Tests write real data, and running a published flow from the test screen can message real people. So live tests run in the **sandbox app**.

## Plan gates

- **Professional only:** PBP (the live pricing page may gate only "PBP API Response"), Loop, Code Block, global variables, condition groups, extended user info, data integration/ETL, print-count limits, world map, contacts visibility.
- **Standard and above:** Integration Center, API Query, Call Integrated API.

Every module plan states which of these it needs, so the edition a customer must buy is known.

## Live tests still open

Collected from all files, highest priority first. Run them in the sandbox app before the first build that depends on them.

1. Time zone of native date nodes and the "today" filter.
2. Unique index: composite keys and the empty-value rule.
3. "Mandatory Validation on Write" with workflows and the API.
4. Update Record add/minus when parallel runs hit the same record.
5. PBP inputs and outputs, and a PBP called from a control event and a page button.
6. Loops and nested sub-processes for the variant cartesian product.
7. Record lock against workflow writes.
8. Rollup lag and the Calibrate node.
9. A subform on an existing sheet with defaults from the product.
10. Custom action dialog field types, and batch behaviour.
11. Interface Push to the clicking user.
12. Whether "workdays" uses Malaysian holidays.
13. Outbound IPs.
14. The Region city level.
15. Multi-currency display with Number + relation.
