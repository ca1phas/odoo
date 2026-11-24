# Worksheet features, part 2 of 2 (help.nocoly.com/worksheet): native catalogue for the Odoo rebuild

| | |
|---|---|
| Purpose | What Nocoly HAP's worksheet layer offers natively for field validation, default values and functions, record handling, import and export, printing and external access, so that Odoo modules can be rebuilt without code where possible |
| Slice | `read_pages.py --prefix worksheet --part 2/2`: 40 pages, 171,294 characters. Every page was read in full |
| Source | Nocoly Help (help.nocoly.com), cached on 3 Nov 2026 in `knowledge-base/nocoly-mingdao/research/corpus.sqlite`. Vendor documentation: **not a runtime test** |
| Edition and version notes | No page carries a version or a date. Edition notes appear on four pages: batch attachment export and Word/Excel templates are for paid versions; print limits need Professional; create-from-Excel caps the Free edition at 50,000 rows. SaaS/Server notes appear on two: automatic indexes (SaaS only) and the server time zone (stated for SaaS) |
| Status | Written 23 Nov 2026. Read-only: no app, worksheet, record or setting was touched |
| Target app | Odoo Replica (AI) `<uuid>`, Nocoly SaaS |
| Companions | `worksheet-1.md` (first half of the worksheet pages: field types, business rules, default-value methods, custom functions, batch operations), `../workflow-nodes.md` |

**Tags.** An untagged statement is what the docs say (cached 3 Nov 2026), not runtime proof. ***[Inference]*** marks my own reading, a design suggestion or an Odoo comparison. ***[Internal]*** marks an earlier note in this workspace, quoted but not re-checked here. Slugs in brackets, such as [field-property], are the pages listed in §6.

## 1. Summary

- **Uniqueness:** "Prevent duplicate input" checks manual input only. The docs send strict uniqueness to a **Unique Index** (composite; at most 5 indexes per sheet), which allows **one** row with empty values.
- **Required** applies on the form only. **Mandatory Validation on Write** extends it: a workflow that leaves the field empty stops with an error, an API write fails and import rows are skipped.
- **Dynamic default values** (another field, a worksheet query or a function) are set on create and edit and re-run when their inputs change. They never run on import, API, workflow or bulk edit. *[Inference]* This is Odoo's onchange behaviour.
- **76 documented functions**, including DATEADD, WORKDAY / WORKDAY_INTL / NETWORKDAY with holiday lists, CEILING/FLOOR to multiples and SPLIT/JOIN/FIND. DATEIF returns text, and SUM/MIN/MAX/PRODUCT count empty values as 0.
- **Word/Excel print templates** (paid; 500 templates per sheet) support line tables with row numbers, merged cells, repeated blocks, hide-if-empty sections, QR codes and barcodes, file-name rules, and limiting a template to certain views and records. Print-count limits need Professional. *[Inference]* Enough for Odoo's QWeb documents.
- **Excel import** updates or inserts by Record ID or by up to 5 key fields (Skip / Overwrite / Update only). It links parents from the "many" side and can skip workflows. It cannot import subforms, formulas, rollups or lookups, and it applies no defaults (10 MB, 20,000 rows, 200 columns per file).
- **Export** follows the view and the user's permissions. It can add Record IDs, data IDs and related records in a separate sheet (at most 1,000). Above 1,000 rows, records come out in creation order.
- **Feature controls** by role and view can hide Create, Import, Export, bulk actions, quick edit, copy/print/delete, discussion/log and file download. A **record lock** (by an admin or a business rule; only admins unlock) blocks edits, deletion and approvals.
- **Drafts** are private, capped at 10 per user per sheet, skip validation, and are invisible to workflows and the API. *[Inference]* So Odoo's draft state must be a status value, not a HAP draft.
- **External access:** public forms (URL source tracking, embedding, CAPTCHA/SMS), public query (exact match, at most 50 rows) and read-only share links. Masking does not apply to exports, Word/Excel printing or the API. SaaS stores times in UTC+8, which is Malaysian time.

## 2. Capability inventory

### 2.1 Field properties and input validation

**Field basic properties.** Source: https://help.nocoly.com/worksheet/field-property

| Property | What it does | Options and values | Limits and notes |
|---|---|---|---|
| Name | Field label | The name can be hidden so that only the value shows | |
| Required | The record page will not save while the field is empty | On / off | **Not enforced** when editing in table view, on workflow or API writes, or on Excel import |
| Mandatory Validation on Write | Extends Required to the other write paths | Extra switch on a Required field | When the field is empty: the workflow stops with an error; Excel import skips the invalid rows and imports the valid ones; the API write fails with an error; data integration skips the invalid data (not counted) and keeps syncing |
| Prevent duplicate input | Warns and blocks saving a duplicate value | On / off | **Manual input only.** Excel imports and API writes are not checked; the docs point to a Unique Index (§2.4) for strict uniqueness. On Member and Relationship fields, a member or record already chosen in another record cannot be chosen again |
| Default value | Fills the field on a new record | Static or dynamic | See §2.2 |
| Read-only | Cannot be edited when creating or editing | | Workflows can still update it, and business rules can make it editable |
| Hidden | Not shown when creating or editing | | The docs suggest it for intermediate calculation fields |
| Hide on create | Hidden on the create form, shown when viewing or editing | | |
| Width | Width in the form | 1/4 width up to full width | At most 4 fields per row |
| Color and style | Colour, font size and style of the label and the value | | Shown in views only after Configure View > Color > Display on PC. Inside relationship, subform and query-records fields, every style except label font size applies |
| Placeholder text, Field description | Input help | Description display: **Auto** (shown below the field on create, behind an icon when viewing), **Icon** (on hover), **Below** (always) | |
| Field alias | Readable, editable key for the API and Word/Excel printing | Generated when the field is created; editable here, in form settings and in the API documentation | The system **field ID** has 24 characters and "may change after duplicating an application". Aliases must be unique; reserved names are listed below |
| Developer notes (field notes) | Comments for maintainers, "like code comments" | | Not shown when creating or viewing records |
| Bulk operations on fields | Select several fields, then delete, duplicate, move to tabs, reorder, or set Required / Read-only / Hidden / Hide on create | Save, Cancel | Field types that are read-only by nature lack some of these options in bulk |

- How aliases are generated: for names of 3 characters or fewer, Chinese becomes full Pinyin; for longer names, Chinese becomes initials. Letters and digits stay. A purely numeric name becomes the field type in English. Duplicates get a suffix.
- Reserved aliases (spelt as on the page): `ownerid`, `autoid`, `caid`, `ctime`, `utime`, `uaid`, `daid`, `rowid`, `wfstatus`, `wfname`, `wfcuaids`, `wfrtime`, `wfftime`, `wfcaid`, `wfctime`, `wsid`, `status`, `sharerange`, `discussunreads`, `relations`, `unreads`, `keywords`, `users`, `owners`, `portal_status`, `portal_mobile`, `portal_email`, `portal_name`, `portal_avatar`, `portal_role`, `partal_regtime`, `portal_openid`, `partal_id`.

**Regular expressions.** Source: https://help.nocoly.com/worksheet/regular-expression

| Item | Detail |
|---|---|
| Applies to | Text fields, and file fields (where it checks file names). Switch: **Restrict Input Format** |
| Each expression | Title, Regular Expression, Error Message and Test. Pick from a preset list (for example Alphanumeric) or type your own; custom expressions cannot be saved into the preset list |
| Conditions | Each expression can carry filter conditions and applies only when they are met. Without conditions it always applies |
| Limits | Up to **5 expressions per field**, in an order you can change. They are checked in that order; validation **stops at the first failure** and shows that expression's message. Avoid leading spaces when pasting |

**Field masking.** Source: https://help.nocoly.com/worksheet/field-mask

| Item | Detail |
|---|---|
| Field types | Single-line Text, Number, Currency, Mobile/Landline, Email, ID Number. Switch: **Mask Display** |
| Rules | **Fully Masked**, **Preset Masking Rule**, **Custom Masking Rule**. A custom rule has Start Characters to Display, End Characters to Display, Middle Characters to Display and Always-Masked Keywords; priority Always-Masked > Start > End > Middle. **Virtual mask length** always shows a fixed number of `*`, which hides the real length. Preview with a test string and **Mask** |
| Always-masked keywords | Comma-separated, exact and case-sensitive matches only; they override every display rule |
| Who can decode | App admins always. Other users follow the field-level permission; a "masking settings" section appears in field permissions. Anyone who can edit the field sees the original in edit mode. Users decode by clicking the value, also in fill-in custom actions and in approval and fill-in nodes; in table view through the column menu |
| Original always shown | Data exports, Word/Excel template printing, API calls, data synchronisation |
| Cannot be decoded | Without decode permission; in public forms, view sharing, record sharing, public query and the workflow "Get Link" node; masked values in system printing; statistics charts; related-record dropdowns; masked title fields in calendar and Gantt views |

**Title field.** Source: https://help.nocoly.com/worksheet/title-field

| Item | Detail |
|---|---|
| What | The field that names a record. A form cannot be saved without one. Set it with the **"T"** icon on a field or under Form Style |
| Allowed types | Text, Telephone, Email, Concat, Autonumber, Foreign field, ID number, Rich text; Number, Currency, Uppercase, Formula, Level; Member, Department, Single select, Multi select, Date, Region/City, Positioning |
| Not allowed | File, Rollup, Relationship, Cascading, Check item, Signature, Free link, Section, Remark, Subform |
| Shown in | The top of the record detail page; notifications about the record; the value that relationship fields display for this sheet |
| Searchable in related worksheets | Lets other sheets search their records by this sheet's title (orders by customer name). Untick it to turn it off (*[Inference]* so it is on by default). It keeps a **redundant copy** of the title; turn it off if titles change often. Text-type titles only: **not for Concat, Rollup or Foreign-field titles** |

### 2.2 Default values and functions

**Field default values.** Source: https://help.nocoly.com/worksheet/field-default-value

| Item | Detail |
|---|---|
| Where | Form editor > field > **Default Value**. Click the blank area for a static value, or the button for a dynamic one |
| Static | A fixed value. Applies **only when a record is created** |
| Dynamic: current context | Date field → Current date; Member → Current user; Department → Current user's department |
| Dynamic: other field values | A field of the current record or of a related record (details in worksheet-1: default-other-field-value) |
| Dynamic: query worksheet | Finds a record in another worksheet by conditions and uses one of its field values (worksheet-1: default-query-worksheet) |
| Dynamic: function calculation | Maths, text handling and logic on other fields (worksheet-1: default-function; functions below) |
| Field types | Text, Number, Currency, Phone, Email, Date, Member, Department, Single select, Multi select, Level, Region/City, Positioning, Check item, Relationship (not with the multi-record list display), Subform |
| When dynamic values apply | When a record is created or edited. They also **update when the values they depend on change** |
| When they do **not** apply | Bulk edits, Excel import, API create/update, workflow create/update. A field left unassigned there stays empty |
| Compared with a foreign field | A foreign field always shows the source's latest value. A dynamic default copies the value at create or edit time and does not stay in sync. The docs' example: a product price on an order should be a Currency field with a dynamic default, not a foreign field |

**Setting values with functions, by field type.** Source: https://help.nocoly.com/worksheet/function-examples

| Field type | Setting a value | Reading a value |
|---|---|---|
| Check item | The formula returns `true` (ticked) or `false`, e.g. `IF(Score >= 60, true, false)` or `ISBLANK(Score)` | Compare with `1`/`0` or `true`/`false` |
| Single select | Return the option **label**; if no option matches, nothing is set. Put fixed values in quotes and pick fields without quotes: `IF(Score<60,'Fail',IF(Score<75,'Pass',IF(Score<85,'Good','Excellent')))` | Stored as a one-element array: append `[0]` |
| Multi select | `'Option 1,Option 3'` or `['Option 2','Option 3']` | |

**System functions.** Source: https://help.nocoly.com/worksheet/system-functions. They work in formula fields, default values and workflow calculations. The page title says "50+"; the page lists 76:

| Category | Functions | Points that matter |
|---|---|---|
| Math (32) | SUM, AVERAGE, MIN, MAX, PRODUCT, COUNTA, ABS, INT, MOD, ROUND, ROUNDUP, ROUNDDOWN, CEILING, FLOOR, POWER, LOG, COUNTBLANK, COUNTCHAR, RANDBETWEEN, NUMBER, PI, RADIANS, DEGREES, SIN, COS, TAN, ASIN, ACOS, ATAN, NORM_S_DIST, PERMUT, COMBIN | SUM, MIN, MAX and PRODUCT count an empty value as **0**; AVERAGE skips empties but counts zeros. MOD: an empty dividend counts as 0, and an empty or zero divisor skips the calculation. ROUNDUP rounds away from zero, ROUNDDOWN toward zero; leaving out the digits gives an integer; "ensure the number of decimal places matches the field configuration". CEILING and FLOOR round to a multiple (`CEILING(9,2)` → 10). INT rounds down (`INT(-3.991)` → -4). NUMBER turns text into a number |
| Date (13) | NETWORKDAY, HOUR, MINUTE, WEEKDAY, DAY, MONTH, YEAR, DATENOW, DATEADD, DATEIF, WEEKNUM, WORKDAY, WORKDAY_INTL | Details below |
| Text (17) | CONCAT, REPLACE, MID, RIGHT, LEFT, TRIM, CLEAN, REPT, LOWER, UPPER, STRING, FIND, FINDA, SPLIT, JOIN, SUBSTITUTE, STRREVERSE | REPLACE and MID count from 1. CLEAN removes **all** spaces; TRIM only the leading and trailing ones. FIND(text, start, end) returns the text between two delimiters; FINDA returns every match as an array. SPLIT returns an array; JOIN(array, delimiter) joins one. SUBSTITUTE is case-sensitive and takes an optional occurrence number |
| Logical (8) | IF, AND, OR, NOT, ISBLANK, INCLUDE, TRUE, FALSE | The OR example tests equality with `==`. INCLUDE(text, search) tests for a substring |
| Advanced (6) | ENCODEURI, DECODEURI, ENCODEURICOMPONENT, DECODEURICOMPONENT, DISTANCE, GETPOSITION | DISTANCE(location1, location2 or "longitude,latitude") returns km. GETPOSITION(location, 'title' / 'address' / 'x' / 'y' / 'x,y') |

Date functions:
- `DATEADD(date, 'offset', format)`. The offset is text: `(+/-)(number)(unit)`, with units `Y` year, `M` month, `d` day, `h` hour, `m` minute. Format `1` returns a date, `2` a date and time. Build a changing offset with CONCAT, e.g. the start of this week: `DATEADD(DATENOW(), CONCAT('-', WEEKDAY(DATENOW())-1, 'd'), 1)`.
- `DATEIF(start, end, format, 'unit')` returns **text with a unit**, such as "6 days". Format 1 counts both dates from 00:00; format 2 counts the end date to 24:00. The format matters only when the fields hold no time. Units are Y, M, d (default), h and m; results round down. Wrap the result in `NUMBER(FIND(...))` before calculating with it.
- `NETWORKDAY(start, end, [holidays])` counts working days, including both ends, without Saturdays and Sundays.
- `WORKDAY(start, days, [holidays])` returns the date N working days before or after the start.
- `WORKDAY_INTL(start, days, [weekend], [holidays])` takes a weekend code: 1 Sat–Sun (default), 2 Sun–Mon, 3 Mon–Tue, 4 Tue–Wed, 5 Wed–Thu, 6 Thu–Fri, 7 Fri–Sat, and 11–17 for a single day, Sunday through Saturday.
- A holiday list can sit in a text field (`2026-06-07,2026-06-08`) and be passed as `SPLIT(Holiday List, ",")`.
- `WEEKDAY` gives Monday = 1 … Sunday = 7. `WEEKNUM(date, [type])`: type 1 (default) starts weeks on Sunday, type 2 on Monday. `DATENOW()` returns the current date and time (for date-time and text fields). HOUR returns 0–23 and MINUTE 0–59.

*[Inference]* These are missing from the list: SWITCH/IFS, IFERROR, regex functions, number and date formatting (thousands separators, "MMM YYYY"), EOMONTH, lookups across sheets, and amount in words. `worksheet-1.md` reports that Custom Functions run JavaScript for default values only, within 1 second, and that the Uppercase amount field is built around China. So a default value can fill these gaps with JavaScript, but formula fields and workflow calculations cannot, and an English amount in words has no native function.

### 2.3 Shared definitions and impact analysis

**Option sets.** Source: https://help.nocoly.com/worksheet/option-set

| Item | Detail |
|---|---|
| What | A list of options defined for the whole app and reused by single- and multi-select fields |
| Create | App Management > Option Set (app admins), or convert an existing field's options into a set |
| Actions | Edit, disable, enable, duplicate, delete, **move to another application**, and view usage. **View Reference** lists the worksheets and apps that use the set and links to their form editors |
| Editing | Editing the options inside any field that uses the set **changes the set itself**, and so every field that uses it |
| Disable | The set can no longer be chosen for new fields; existing fields keep working. A disabled set can still be edited, duplicated, moved or deleted |
| Delete | Only from the management page, and only when no field uses it; otherwise disable it |
| Option settings | Colour, sorting, adding, hiding/showing, option values and "Other" are on the select-field page (worksheet-1: control-select) |

**Field templates.** Source: https://help.nocoly.com/worksheet/field-template

| Item | Detail |
|---|---|
| What | Saves the full configuration of one or more fields for reuse, such as an address block |
| Create | Worksheet Edit page > select the fields > **Create Field Template**. Enter a Template Name (required, unique within its scope), a Scope and a Description |
| Scope | **Personal**: only the creator sees and manages it, in any app where they are app admin, and also in other organisations. **Organization**: created and managed by organisation super admins or by admins with the Application > Application Services and Resources permission, and offered to every app admin in the organisation. Users who are not organisation admins don't see the Scope option |
| Referenced fields | Included automatically one level down; their own references are not. The page also says fields "can be included up to three levels deep" |
| Limits | **30 fields** per template, counting the fields added automatically; **100 personal** and **100 organization** templates |
| Use | Edit page > **Template** tab: click a template to add its fields at the end, or drag it to a position |
| Copy model | Fields created from a template are independent. Later edits to the template, or deleting it, do not touch them |
| Relationship-based fields | Creating the template needs management permission on the target worksheet. Applying it creates new relationships. Organization templates are meant to point at **centrally maintained reference worksheets**: an admin who applies one can see the related sheet's structure and use its data through the relationship, without management rights on it |
| Rules by field type | Relationship, Query Records and Cascading need management permission on the target sheet. Rollup and Foreign field need their relationship field in the template. Formula, Uppercase, Concat and Barcode pull in their referenced fields. Auto Number needs its referenced fields to be in the template already. **Embed is not supported.** A subform without an entity worksheet cannot be saved |
| Manage | Edit (name, description, scope), Delete |

**Worksheet and field references.** Source: https://help.nocoly.com/worksheet/reference-details

| Item | Detail |
|---|---|
| Worksheet references | Worksheet menu > **View Reference**, or App Management > **ER Diagram**. Covers relationships, queries and data exchange between sheets, and workflow steps that query, assign values, approve, fill in or CC |
| Field references | **View References** at the top right of the field settings panel, also offered when a field is deleted. Covers other fields (default values, Formula, Concat, Auto Number, OCR, API Query, Barcode, subform duplicate rules, relationship selection scope, Cascading, Query Records conditions, Foreign field, Rollup); workflows (node filter conditions, Code Block, Branch and Formula nodes); business-rule **conditions**; and view filter conditions. References from this app and from other apps are shown |
| Blind spot | Fields used in business-rule **actions** are not listed |

### 2.4 Worksheet-level settings

**Basic worksheet operations.** Source: https://help.nocoly.com/worksheet/operations

| Operation | Detail and limits |
|---|---|
| Edit Form | More > Edit Form opens the designer |
| Name, icon, description | The description shows as an Icon, or as Text that is always under the name |
| Record name | Edit Form > Data Name. Replaces "Record" (for example "Lead"). The Create button label follows it ("+Lead") and can be changed separately ("+New Lead") |
| Worksheet alias, field alias, developer notes | Edit Form > Data Name; aliases can also be managed in the API documentation. Developer notes: app admins and developers only; the Get App Info API returns them as `notes` |
| Duplicate | You choose which relationship fields to copy. Records, discussions and activity logs are not copied |
| Delete / restore | App admins only. A deleted sheet can be restored for **60 days**; after that it is gone for good. A restored sheet keeps its structure and relationships |
| Move | To another group, or to another application (you need admin or developer rights in the target app). **Not to another organisation** |
| Hide from navigation | On desktop, on mobile or everywhere. Regular users stop seeing it; admins and developers still do, unless "View Hidden Items" is turned off. **Access does not change**: a direct link still opens it |
| Groups, navigation | Worksheet groups in the top navigation; the left navigation can be collapsed or hidden |

**Feature controls (function switches).** Source: https://help.nocoly.com/worksheet/function-switch

Each control can be **Disabled** for everyone, **Available to specific roles** (all users, or specific system roles only) or **Available in specific views** (chosen views or all views).

| Level | Control | Effect |
|---|---|---|
| Worksheet | Show "Create Record" button | Off hides it for everyone; records can still be created by custom actions or from relationship fields |
| Worksheet | Worksheet Discussion | (no detail on the page) |
| Worksheet | Import Data from Excel | The import button is hidden when this is off or the user lacks permission |
| Worksheet | Recycle Bin | Off for all, or limited to app admins / developers / operators / all users |
| Worksheet | Statistics | Personal and shared charts |
| View | Embedded Link | A link that shows only the data area, without navigation, still permission-checked. Off removes it from the share menu |
| View | Export | Exports every visible record of the view |
| View | Bulk Actions (table view only) | Edit, Duplicate, Delete, Export, Print QR codes, Execute custom actions. To stop exports completely, turn off **both** Export and bulk export |
| View | Quick Edit | Inline editing in table view, and quick editing on kanban, org and gallery cards |
| Record | Internal Access Link | A link for app members only, checked against roles |
| Record | Copy, Recreate, Print, Delete | Removed from the record menu. Print disappears only when printing is off **and** no Word/Excel template exists |
| Record | Record Discussion and Activity Log | Hides both panels and the recent-update information |
| Record | File Download | Files cannot be downloaded, shared, added to knowledge or printed from preview; they can only be deleted. Files the user uploaded are not affected |
| Approval | Approval System Fields | Workflow name, status, completion time, node owner, node start time, remaining time, initiator, initiation time |
| Approval | Approval Flow Details | Shows the approval process and its steps in the record panel |

**Submit-form settings.** Source: https://help.nocoly.com/worksheet/submit-form (Edit Form > More Settings > Submit Form, app admins)

| Setting | Detail |
|---|---|
| Form title | Title of the create page. Priority: Form Title > Record Name > "Record" |
| AI Autofill | A button on the create page (a purple camera on mobile). Users upload text, images or documents and AI fills in the fields. **Not available in public forms** |
| Save as Draft | On by default for new sheets. Drafts are seen only by their author; **workflows, worksheet queries and the API cannot reach them**; they send no notifications, **trigger no workflows** and get **no validation** (required fields, duplicates, formats, business rules). **10 drafts per user per worksheet.** They don't count toward the sheet's record total, but their attachments use storage |
| Submit button (Button 1) | Always shown; the label can be changed. After submitting it can close the page, continue creating, or open the new record in a chosen view, where users can comment or run custom actions |
| Continue to Create (Button 2) | Optional; can be hidden or renamed |
| Retain values (Button 3) | All fields or chosen fields; either a checkbox the user ticks, or automatic. Works only with Continue to Create (and with the mobile setting "create next record after submission") |
| Confirmation before submission | A confirmation dialog with your own message and button text |
| Trigger workflow immediately | Workflows normally start **5 seconds** after a record is created. This option runs create and create-or-update workflows at once (within up to 10 seconds) and refreshes an open record page. It applies only to records made with the Create button; Excel imports, workflows and the API still wait 5 seconds |

**Worksheet indexes (Search Acceleration).** Source: https://help.nocoly.com/worksheet/index-acceleration (Edit Form > More Settings > Search Acceleration > Create Index)

| Item | Detail |
|---|---|
| Purpose | Faster filtering, searching and sorting on large sheets (tens or hundreds of thousands of records) |
| Index types | The page describes the **Unique Index** (the combination of the indexed fields must be unique, e.g. Name + Created Date) and mentions a text index; no other type names are given |
| Limits | **5 indexes per worksheet**; **1 text index** per worksheet; a text index cannot include multi-select fields; **at most one multi-select field** per index |
| Unique index rules | No duplicate values. If the indexed fields can be empty, **only one record with empty values** may exist. Creation fails unless the existing data, **including the Recycle Bin**, is already unique. Records deleted more than 60 days ago, or by some batch operations, may not show in the bin yet still conflict; the docs' fix is **Empty Now**, which deletes them permanently |
| Edit | Add or remove fields, change their order and sort direction, rename, delete. The system index `index_rowid` cannot be renamed |
| Automatic indexes | **SaaS** creates indexes on its own from daily access logs; don't change or delete indexes you did not create. **HAP Server does not do this** |
| Guidance | On sheets with 100,000 records or more, index the fields used by frequent batch queries before running them. Prefer fields with few duplicate values. One composite index (Last Name + First Name) works better than two single ones. Composite indexes follow the **leftmost-prefix** rule and should match the view's sort order and direction. Every index slows writes a little |
| Queries that may not use an index | Not Equals, Does Not Contain, Does Not Start With, Does Not End With; Contains, Is Empty, Starts With, Ends With; OR conditions; options held by more than about 30% of records; text sorted with Sort by Pinyin. The fastest patterns are Equals on text and Is One Of on array fields (Member, Department, Org Role, Multi-select, Relationship) |

*[Internal]* The Chinese-manual review `knowledge-base/nocoly-mingdao/internal/hap-manual-cn-v124-worksheet-index-constraints-review.md` says the same and keeps three open questions, CN03-013 to CN03-015: composite keys with empty values, recycle-bin conflicts, and automatic indexes on Nocoly.

**Time zones.** Source: https://help.nocoly.com/worksheet/time-zone

| Item | Detail |
|---|---|
| Server time zone | **HAP SaaS: Beijing Time (UTC+08:00).** Date-time values, system time fields and workflow trigger times are stored in it. Date-based chart statistics and scheduled workflows run on it |
| Personal time zone | Avatar > More > Basics. The list includes "(UTC+08:00) Kuala Lumpur, Singapore". It applies to date-time fields, worksheet and record log timestamps, Gantt, Calendar and Resource views, and chat and notification timestamps |
| Conversion | Date-time values are typed and shown in the personal zone and stored in the server zone. **Date-only fields are never converted.** These system fields are converted too: Created Time, Last Modified Time, Node Start Time, Initiated Time |

**Introduction.** Source: https://help.nocoly.com/worksheet/introduction. Worksheets are described as "online Excel": records with discussion and sharing, relationships between sheets, and data entry, search, sorting and filtering ready from the start. Data comes in by Excel, by API, or through forms that need no login.

### 2.5 Records, search and filters

**Operations on a single record.** Source: https://help.nocoly.com/worksheet/record-operations

| Operation | Detail and limits |
|---|---|
| Create | The "+" button (needs create permission). A QR code or link for internal members opens the create page after login; a public-share QR code or link lets anyone create without login (see public forms) |
| Edit | Click a field on the record page |
| Copy | Creates a new record from the current one |
| Recreate | Opens a create page filled with the previous record's values; nothing is saved until it is submitted |
| What Copy and Recreate take | Every field value; up to **200** subform rows; up to **5** related records shown as cards or dropdowns, inside subforms too. Related records shown as a **list** are not copied |
| Favorite | The record appears under "Favorite Records" on the home page |
| Lock | App admins lock and unlock from the toolbar. Anyone can lock through a **business rule**; only admins unlock. Admins can lock or unlock **up to 1,000** records at once. **Locked records cannot be deleted or changed in any way, and no approval actions can be taken on them. Records cannot be filtered by lock status** |
| Delete / restore | Deleted records go to the worksheet's recycle bin. Users who are not admins can restore what they deleted; only admins delete permanently, which cannot be undone |
| Print | System print, Word/Excel templates, or saved system templates. Without templates only system print is offered |
| Share | A public link or QR code, with expiry and password options. Viewers cannot edit |
| Discussion | Comments, @someone or @all record members; replies notify too. **Follow** (the bell icon) sends every new comment, and can push it to third-party platforms. Only users who can see the record in the worksheet can follow, not users who were only mentioned. **Internal organisation members only.** The follower list is visible. The workflow node **Update Record Followers** adds or updates followers |
| Log | Every operation: who, what, the value before and after. **The log can be exported** |
| Moving around | Previous/next buttons; each record has its own URL; the **Tab** key moves through editable fields from top to bottom and left to right, and Enter opens the options of dropdown-type fields; hover shortcuts for favourite, copy, recreate, delete, print, lock and share |

**Search, filters, sorting and column statistics.** Source: https://help.nocoly.com/worksheet/sort-filter-records

| Feature | Detail and limits |
|---|---|
| Search | Text, Telephone, Email, ID Number, Concat, Autonumber, API Query, Cascading Select, Relationship (single record), Foreign Field (data storage). For the last three, the linked field must be Text, Telephone, Email, ID Number, Concat or Autonumber. Text over **5,000 characters** cannot be searched. **Aa** turns case sensitivity on or off. Keywords separated by spaces must all match (AND); **5 keywords at most** |
| Filters | Work on the records the user can see in the current view. Conditions and condition groups: AND or OR inside a group; use several groups to mix them. Modes: **Effective immediately** or **Effective after clicking Query** |
| Saved filters | **Personal** (any member; seen only by its creator) or **Public** (made by app admins, seen by all members; can be turned back into personal). Only admins can make their own personal filter public. Filters can be deleted, renamed, changed, duplicated and reordered |
| Sort | A temporary sort by clicking a column, **table view only**; it resets when the page reloads |
| Statistics | Column statistics on the visible records, **table view only**, kept after a reload. Number and Currency: sum, average, maximum and so on; other types: how many records have a value and how many are empty |

**Filter operators by field type.** Source: https://help.nocoly.com/worksheet/field-filter. They are used in custom filters, view filters and workflow trigger and branch conditions.

| Field family | Members | Operators |
|---|---|---|
| All | | Is Empty / Is Not Empty. "No file" and an unticked check item count as empty; **0 does not** |
| Text | Text, Telephone, Email, ID Number, Concat, Auto-number | Equals / Not Equals; Include / Not Include; **All Include** (every keyword); Starts With / Not Start With; Ends With / Not End With |
| Numeric | Number, Currency, Formula, Rollup | The page describes only Within Range (bounds included) and Outside Range (bounds excluded) |
| Date | Time, Date, Date/Time | Equals / Not Equals (only the date part counts, e.g. "Equals Today"; broader matches such as "This Month" work too); Before / After (the date excluded); On or Before / On or After (included); In Range (both ends included); Out Of Range (both excluded). The precision follows the display format: a field shown as a date can only be filtered by day |
| Single-select family | Single-select, Region/City, Level, Members (single), Department (single), Org-roles (single), Relationship (single) | Equals / Not Equals (one value); Is One Of / Is Not Any Of (several values) |
| Two-state fields | File, Check item, Positioning, Signature, Subform | Filtered like a single select with two values (Yes/No, Checked/Unchecked, Empty/Not Empty) |
| Multi-select family | Multi-select, Members (multi), Department (multi), Org-roles (multi), Relationship (multi) | Equals / Not Equals (exactly the same set); Is Any Of; Is None Of; **Also Includes** (all of the chosen values, others allowed) |
| Department, Region/City | | **Belongs To / Not Belong To** (sub-levels included); **'s Subordinate Contain / 's Subordinate Not Contain** (matches records holding the superiors of the chosen units) |
| Relationship | | **Equals Record ID** |

**Filter related records (the relationship picker).** Source: https://help.nocoly.com/worksheet/filter-associated-records

| Item | Detail |
|---|---|
| What | Limits which records the relationship picker offers; by default it offers every record the user can access |
| Conditions | Field, operator and value. The value is fixed or **dynamic**: a field of the current record or of a related record. Several conditions can be combined |
| Examples | Only products with Status = Active. Customer → Contact: only the contacts of the customer already chosen |

**Subform or relationship.** Source: https://help.nocoly.com/worksheet/relationship-subform-comparison

| | Subform | Relationship |
|---|---|---|
| Link | Containment: the subform is a field of the parent, and deleting the parent deletes its rows | An association between two worksheets; it can be removed and both sides live on |
| Entry | Rows are added on the parent's page | Like a subform, or through card views and dropdowns |
| Use when | The rows mean nothing outside the parent (expense lines) | The data is a business object of its own (companies and contacts) |
| Conversion | A subform can become an independent worksheet, or be linked to an existing worksheet through a relationship field, "without affecting existing data" | |

**Subform rows in workflows.** Source: https://help.nocoly.com/worksheet/process-subform-data
- Reading: get the parent record first, then use **Get Multiple Data** > **Get Associated Records** to fetch its subform rows.
- Writing: a workflow can add rows only to a subform **that has an entity worksheet**. A blank subform (no entity worksheet) cannot be the target, but it can be converted into one. A batch add needs an earlier node that fetched the batch of data.

### 2.6 Import and export

**Import Excel data.** Source: https://help.nocoly.com/worksheet/import-excel-data

| Item | Detail and limits |
|---|---|
| Entry | Toolbar **Import** > **Import Excel** |
| File | .xls, .xlsx or .csv; **under 10 MB, 20,000 rows and 200 columns**. Split bigger files |
| Header | Any row can be the header; the rows below it are imported. An empty header row, or any empty column header, makes the import fail |
| Mapping | Columns map automatically when names match; "Please Select" skips a column |
| Identify Duplicate Records | Matching fields can be Text, Phone, Email, ID, Auto Number, **Record ID** or Member (single). Up to **5**, all of which must match (AND). Actions: **Skip** (import only rows with no match), **Overwrite** (update matches, create the rest), **Update Only (No New Records)** |
| Skip Error Data | 8 kinds of validation error can be chosen (wrong formats, empty required fields and so on). On: rows with a chosen error are skipped. Off: the row is imported with the invalid fields left empty |
| Trigger Workflow | Off skips create and update workflows for the import, **and also date-field workflows due on the import day**. Example: a flow set for 1 hour after creation does not run for rows imported before 23:00, but does run after midnight for rows imported after 23:00 |
| Save Import Configuration | Saves the mapping and duplicate rules as the default. "Restrict non-admin users from modifying the default configuration" hides the options from regular users |
| Allow New Options | Select options that are in the file but not in the field are added |
| Associate with Other Worksheets | Relationship fields are matched to existing records (see import-associate below) |
| Results | A summary of added and updated counts; a downloadable error report; details in the worksheet logs |
| Not importable | Subform, Formula, Uppercase, Positioning, Foreign field, Rollup, Cascading, Signature, Barcode, Embed, Section, Remarks. (The same page then explains how Cascading values import; see §4) |
| Admin-only targets | Fields set to Hide, Hide when Create or Read-only, and fields a role cannot see when creating: only app admins can import into them |
| Defaults | **Field default values are not applied during import.** Put the values in the file |
| Fields with several values | Multi-select, Members, Departments, Org-roles: separate values with commas |
| Departments | Matched by the lowest-level name only, not by path; use department IDs for exact matches |
| Members | Matched by name, telephone, email, employee ID or user ID. With duplicate names, a multi-member field gets **everyone** with that name and a single-member field gets **no one** |
| Region/City | A full `Province/City/District` path with `/`. It must fit the field's levels and the real hierarchy; partial paths are ignored; for municipalities use `City/District` |
| Cascading | A record ID gives an exact match. Text with a path matches on the last segment; text without one matches on the whole text. Multi-select cascading fields match item by item |

**Update existing records on import.** Source: https://help.nocoly.com/worksheet/import-update. Tick **Identify duplicate records**, choose **Overwrite** and a unique matching field (record ID, employee ID, phone; not names). This page describes Overwrite as "fully replaces the existing record in the worksheet with the values from the Excel file". **Update only, do not add new records** ignores rows without a match.

**Link records on import.** Source: https://help.nocoly.com/worksheet/import-associate. While mapping, choose the Excel column, the relationship field, and the field in the related sheet to match on (for example the full company name). This works **only when importing into the "many" side** (contacts linking to a company), not the other way round, so import the parent sheet first.

**Create apps and worksheets from Excel.** Source: https://help.nocoly.com/worksheet/import-excel-create

| Item | Detail and limits |
|---|---|
| App from Excel | Choose the sheets (each becomes a worksheet), the header row and columns, the title field, and field names and types; then the app's name, theme colour and icon. An in-app notification says when it is done |
| Worksheet from Excel | App menu **+ App Item** > **Create from Excel**, with the same steps. Columns can be made relationship fields to **existing** worksheets and are linked automatically |
| Type detection | Only Number, Date and Boolean (as a Check item) are recognised; everything else becomes Text |
| Title field | The leftmost field by default, or the first column of an allowed type from the left |
| Limits | .xls, .xlsx or .csv up to **20 MB**; up to **20 sheets**; **20,000 rows and 200 columns** per sheet; the **Free edition imports 50,000 rows** in total across sheets, paid editions have no row limit; sheets with **merged cells** cannot be imported; relationships cannot be made while the app is created (create the base sheets first, then import related sheets) |

**Export records to Excel.** Source: https://help.nocoly.com/worksheet/export-excel

| Item | Detail and limits |
|---|---|
| Scope | The records the exporting user can see in the current view. All visible records: view menu > Export. Selected records: action bar > Export > Export Info (**table view only**). The whole sheet: an app admin selects everything in the **Data Management** view |
| Order | Under 1,000 records: the view's order. **Over 1,000: creation time** |
| Fields | Chosen fields or all; a table view's custom display columns are preselected in their order. Admins can export every field in the view, other users only the fields they may see. **Column Statistics** can go in row 2 (not when exporting selected records) |
| Record IDs | Of the exported records and of their related records, so that a later import can match them |
| Related records | A single related record: a column. Several, or a subform: a column when shown as cards or a dropdown; a separate sheet when shown as a list. **At most 1,000 related records** |
| Accelerated Export | Relationship fields (dropdown or card), Cascading fields and foreign fields (data storage) keep cached copies: the related record's title, or the source value. A sync queue updates them, sometimes late. On: the cached values are exported (fast, possibly out of date). Off: live values are read (slower) |
| Format | Excel or CSV. **Preserve Excel number formats on export** keeps Number, Currency, numeric Formula and Rollup, and Level values as numbers; otherwise they export as text |
| Extra columns | The assigned values of select options; data IDs for single relationship, cascading, member and department fields; the Work ID for members; **Generate preview link for attachment field** (opening it needs a login and follows permissions) |
| Default export configuration | Admins save the fields, options and format for everyone. **Users are not allowed to modify default settings** makes it mandatory |

**Attachments: export and import.** Source: https://help.nocoly.com/worksheet/export-import-file

| Item | Detail and limits |
|---|---|
| Batch attachment export | **Paid versions only.** Selected records, or the view menu > Export > Export Attachments. Choose the file fields; build file names from the record title, the file field name and the original name, with your own separators; one folder per record or a single folder. **At most 1,000 attachments and 1 GB per export.** Attachments shown through foreign fields cannot be exported |
| Links in an Excel export | File name + URL, separated by commas. Opening them needs a login. The file can be imported back as it is |
| Import by link | Import Excel with public URLs, separated by commas. The file name is the URL's last segment, or use `filename.ext (URL)` |
| Import Attachments (local files in bulk) | Toolbar Import > **Import Attachments**. Needs import, create and edit permission; uploads count toward the organisation's attachment upload quota. File names are matched against a field: text, email, telephone, ID number, auto number, or a foreign field of one of those types (no system fields). An optional delimiter (`_ - .`) matches only the part before the first one. Pick the target file field. Write mode **Append** or **Overwrite** (cannot be undone). **Create records when no match is found** writes the name or prefix into the matching field and groups files with the same prefix into one record; it may fail when other required fields have no default or imported value. **At most 100 files and 2 GB per upload.** Results come as a pop-up and an app message, with an error report; the app log records them under Data Operation > Import > Worksheet Record, and record logs show attachment changes |

The characters `\ / : * ? " < > |` in file names are replaced with `_` on upload.

**Upload attachments by workflow or API.** Source: https://help.nocoly.com/worksheet/workflow-api-upload-file

| Path | Format | Notes |
|---|---|---|
| Workflow (Add Record or Update Record node, for example after a webhook trigger) | URLs only, as a JSON string: `url1`, `["url1"]` or `["url1","url2"]` | The docs' pattern: save the URLs in a text field first, then let a workflow download them into the file field |
| API | `value` holding comma-separated URLs (`valueType 1`, the default), or `controlFiles` `[{baseFile, fileName}]` in base64 (`valueType 2`). `editType` 0 overwrites (default) and 1 appends; it is required when updating | The example uses `appKey` + `sign` + `worksheetId` + `controls`, the older API style |
| URL requirements | The platform's server must be able to reach the URL, the file must download directly, and the URL must end in a valid file extension | Batch-add API calls that carry attachments can time out because they wait for every upload. The docs advise writing the URLs to a text field and uploading later by workflow |

### 2.7 Printing

**Template types.** Source: https://help.nocoly.com/worksheet/print-template

| Type | What it is | Limits |
|---|---|---|
| Word / Excel | Your own .docx or .xlsx layout with field codes, filled in at print time and exported | **Paid versions only** |
| System | A fixed layout in which you choose the fields | |
| QR code | Fields or record links as QR codes, for scanning on mobile | |
| Barcode | Fields as barcodes (equipment, product labels) | |
| Cloud print | Sends jobs to remote printers. The template is designed on the provider's platform (for example Kuaimai) and connected through **System Services** | |
| All types | | **500 print templates per worksheet** |

*[Internal]* The Nocoly price list reviewed in `knowledge-base/nocoly-mingdao/internal/nocoly-pricing-msrp-2026-11-06.md` names three SaaS editions, Free, Standard and Professional. It ticks "print files and templates" and "batch attachment export" for Standard and Professional, and "online document editing" for Professional only.

**System print template.** Source: https://help.nocoly.com/worksheet/system-print-template (Edit Form > More Settings > Print Template > Create Template > **Record Printing**)

| Setting | Detail |
|---|---|
| Layout | Paper size and orientation, font size, the fields to print, and a live preview |
| Print options in tile layout | Prints every option of a tiled option field, selected or not |
| Print fields with null values | Shows or hides empty fields, with an optional placeholder such as `---` |
| Subforms and related worksheets | Printed as **General**, **Transpose** or **Tile** |
| Date/time format | Your own format for system time fields (created, last modified) |
| Allow downloading & printing | Off: users who are not admins cannot download the file; admins always can |
| Record QR code | A Public Link or an Internal Member Access Link |
| Export | A system template can also be exported to a Word file |

**Word and Excel templates.** Sources: https://help.nocoly.com/worksheet/word-print-template and https://help.nocoly.com/worksheet/excel-print-template (Edit Form > More Settings > Print Template > Create Template)

| Step or setting | Detail |
|---|---|
| Field code reference table | Field Name; Field Code (made from the name); Field ID or Field Alias (exact and unique, for when two codes are the same) |
| Authoring | Microsoft Word or Excel is recommended; templates made in **WPS** may print badly. Download a sample template with codes, or start from your own file |
| Related records and subforms | A table whose first row holds column names and whose second row holds the codes `{relationship field name.field name}`. In Word the table must stand on its own, not inside a cell of the main table. A `.` in the relationship or subform name breaks the code; use the alias or field code instead |
| Row numbers | `#{DetailName.sequencenumber}` or `#{DetailID.sequencenumber}` |
| File format | Word **.docx only**; Excel **.xlsx only**. Upload the file or create it online |
| Export file name | By default template name + title field + export time, or a combination of fields of your choice |
| Allow Downloading & Printing | Lets regular users download the generated file |
| Allow Editing Before Printing | Adds an **Online Editing** button to the preview, for editing the generated Word or Excel file before printing |
| Empty fields | A placeholder for empty fields (described on the Word page) |

**Advanced field codes for Word and Excel.** Source: https://help.nocoly.com/worksheet/print-template-rules

| Need | Code |
|---|---|
| Every option of a select, chosen or not | `#{Status_Alloptions}`; vertical: `#{Status_Alloptions[V]}` |
| Image size | `#{File$[90*auto]$}` fixed width; `[auto*80]` fixed height; `[70*90]` both; `[45*90_auto]` fit inside the box. `[auto*auto]` is invalid |
| Image quality | Add `_L` (75 dpi, the default), `_M` (150 dpi) or `_H` (300 dpi), e.g. `#{File$[auto*90_M]$}`. The original is used if it is smaller |
| Image file name | `#{File$[90*auto_L]$_name}` for image and name; `#{File_name}` for the name only. Excel cannot show the image and the name together; documents print only their name |
| QR code or barcode of a field | `#{[qrcode]FieldName$[20*20]$}` and `#{[barcode]FieldName$[40*10]$}`. QR holds up to 150 characters (Chinese allowed); the barcode is Code128 with up to 30 letters, digits and symbols |
| System links and IDs | `sharelink` (public share link), `privatelink` (internal access link), `recordid` |
| Row numbers | `#{DetailName.sequencenumber}` |
| Merge equal cells down a column | `#{SubformName.FieldName[M]}` |
| One block per related record, with headers repeated | `#Relation.Repeat[start]#` … `#Relation.Repeat[end]#`, each tag on its own row |
| One field across all records, comma-joined | Add `[S]` to the field code |
| Only the first N rows | Add an index to the subform name (the page's example prints the first two) |
| Hide a section when its list is empty | `#NoDataNotPrint[start]#` … `#NoDataNotPrint[end]#`. Wrap each list on its own: if one list in a shared block has data, the whole block prints. Give each list its own table |
| Member details | `#{[member]Owner$[_ID]$}`; several: `#{[member]Owner$[(_ID;_Email)]$}` gives "Ross (102;md1@md.com)"; `_Phone` also works |
| Date format | `#{ctime$[yyyy/M/d]$}`; the default is `yyyy-MM-dd HH:mm:ss` |
| Print metadata | Print time, printed by, QR codes, barcodes, creation time and last-modified time, by inserting their codes or aliases |

**Template management.** Source: https://help.nocoly.com/worksheet/print-template-management. In Edit Form > More Settings > Print Template you can:
- redesign a template;
- rename, copy or delete it through `...`;
- set its **Scope**, the views where it appears;
- add **filter conditions**, so that it is offered only for matching records;
- set a **Print Limit**;
- drag templates into order; the record's print menu uses the same order.

**Print limits and print counts.** Source: https://help.nocoly.com/worksheet/print-times-limit

| Item | Detail |
|---|---|
| Edition | **Professional edition and above.** Covers system, Word/Excel, QR code/barcode and cloud printing |
| Track Print Count | A switch on the Print Template page. The record page then shows how often the record has been printed. Counts are recorded even while the switch is off |
| Print Limit | Set per template: `...` > Print Limit > **Limits Enable**, plus the maximum prints per record. The limit shows in the template list and in the record's print menu. Turning it off keeps the count, which applies again if it is turned back on |
| At the limit | One record: that template's print button is disabled. Several records: those at the limit are skipped and listed, and the rest print. Other templates still work for the record |
| Reset | App admins only: record > Print > **Manage Print Counts**, per template and record. A reset does not lower the record's total count or change audit logs |

**QR code and barcode printing.** Source: https://help.nocoly.com/worksheet/print-barcode

| Item | Detail and limits |
|---|---|
| Browsers | Not IE, Safari or the desktop apps; use Chrome, Edge, Firefox or 360 |
| Start | Table view: select records > Print QR Code or Print Barcode. If the button is missing, batch printing is off in the function switches, printing is not allowed in the view, or a user who is not an admin lacks **System Print** or **Batch Operations** |
| Data source | The record link (Internal Member Access or Public Link) or a field value |
| Encoding | QR: up to **150** characters, Chinese allowed. Barcode: **Code128**, up to **30** characters |
| Printer | **Label printer** (barcodes print only here): preset or custom size, layout and position, code size S/M/L/XL, QR fault tolerance. **A4**: rows and columns per page |
| Extra fields | Printed around the code; how many fit depends on label size, code size and layout. The title field's font size is fixed, the others can be changed. Field names can be shown, hidden or renamed for the label only. Single-line display shrinks the text to fit and prints the title bold and centred, without its name. Fixed text is allowed. Fields hidden in the table view do not print in quick print |
| Templates | Save the setup as a template and manage it in the worksheet |
| Volume | **200 records per print** |
| Output | The browser's print dialog, or a **PDF download** |

### 2.8 External access

**Public forms.** Source: https://help.nocoly.com/worksheet/public-form (Extend > Public Form)

| Area | Settings and limits |
|---|---|
| Look | Title, description and cover (theme colour, background image, QR code on the form). The fields and their layout are independent of the worksheet form: fields per row and width ratios. **Reset** restores the layout and clears visibility and order settings |
| Not allowed | **Member, Department, Organization Role** and similar system fields cannot be put on a public form. **64 MB per uploaded file** |
| Link | A public link and QR code. **Disable** stops submissions; **Regenerate Link** kills the old link and keeps the data |
| Who can submit | All users (no login), Platform users (a HAP login), or Internal users (members of the organisation) |
| When | Start and end time, shown as a countdown or a deadline; a schedule by months, dates, weekdays and time ranges. Both can be combined |
| How many | A cap on total responses (counting public-form submissions only), and a per-respondent cap per day, week, month or year. Anonymous forms without WeChat identity enforce the per-respondent cap **by device cache**; logged-in and WeChat users are counted by identity |
| Protection | A password (4 random digits by default, editable); a description shown before filling in; **SMS verification** (needs a mobile number field, otherwise it is skipped; the SMS signature can be changed); a puzzle **CAPTCHA**. With both on, SMS comes first, then CAPTCHA |
| Cached data | Restores unsubmitted input, and can prefill from the last submission (all fields or chosen ones). It lives in browser storage. **Cached data beats default values** |
| WeChat | OpenID only (silent), or OpenID, nickname and avatar (with the user's consent), through HAP's service account or your own (your own allows silent only). WeChat-only submission; custom share cards |
| Identifying respondents | With WeChat details, or with Platform/Internal users: forms can prefill from earlier answers and let people view and update what they sent |
| Receipt | A message, instructions or a redirect link after submitting, with dynamic field values |
| Source tracking | URL parameters saved into a hidden field, e.g. `?source=linkedin`. **Generate Link** makes one link and QR code per channel; parameters can also be added by hand or by a workflow (for example a record ID). Custom functions can read them before submit |
| Device information | IP, browser, device type and OS saved into hidden Text fields (**+ New Text Field** creates one) |
| Embed | Extend > Public Form > Form Settings > Publishing Settings > **Embed** gives HTML code. You can hide the title, logo, border and description, and align Submit left, centre or right |

**Public query.** Source: https://help.nocoly.com/worksheet/public-inquiry (Edit Form > Extend > Public Query)

| Item | Detail and limits |
|---|---|
| Query view | The view that is searched. To expose every record, it must have no filter conditions and no hidden fields |
| Query conditions | All are required; matching is **exact**, not fuzzy; several conditions must all match |
| Options | Page title; **Allow Data Export** (a Download button) |
| Results | **At most 50 records**; use view sharing for more. A table view shows its own columns (3 on mobile); other views show fields in the record-detail order |
| Ways to share the link | Send it by SMS or email after a public-form submission, or put it in the form's description or receipt |

**Public sharing of views and records.** Source: https://help.nocoly.com/worksheet/share (Edit Form > More Settings > Public Sharing)

| Item | Detail |
|---|---|
| View sharing | On: choose which views can be shared and who may share them. Off: all view sharing stops and **existing links stop working** |
| Record sharing | On: choose who may share and from which views; sharing can also be turned off for a single record. Off: the same effect as for views |
| What the viewer sees | **Each user gets their own link, and it shows data with the sharing user's permissions.** Shared records are read-only |
| WeChat card | Views: title (by default "Worksheet - View"), a fixed description and an icon. Records: title from the record title or a field, description from a field, and an icon |
| @mentions | A mentioned user who can see the worksheet can open the record **read-only** from the notification. They cannot if they have no access to the view where the mention happened, or if the record is not in that view ("Record not accessible"). The same rules cover follower notifications and notifications from member fields |

## 3. Odoo rebuild notes

The mapping below is *[Inference]*. The limits it quotes come from §2.

### 3.1 Concept map

| Odoo concept | Native HAP replacement | Fit, and where native falls short |
|---|---|---|
| `_sql_constraints` UNIQUE and uniqueness constraints (country code; state code per country; lot/serial name per product; product barcode) | **Unique Index**, composite where needed | Good where every row has a value: it holds for import and API writes, and probably for workflow writes too. It falls short for optional values such as Odoo's barcode, because only one empty row is allowed. It cannot span two sheets (barcodes on Products and on Variants). At most 5 indexes per sheet |
| `required=True` | **Required** + **Mandatory Validation on Write** | Plain Required checks the form only. With the extra switch, a workflow that writes an empty value stops with an error, so test it before turning it on for sheets that workflows fill in stages |
| `readonly=True`, read-only by state | **Read-only** property, plus business rules for the dynamic cases (worksheet-1) | Workflows can still write read-only fields, which suits Odoo's computed fields |
| `default=` with a constant; `default=lambda` with today or `env.user` | Static default; Current date, Current user, Current user's department | No "current company" (single company, decision 1) |
| `@api.onchange`, or stored computes that copy from a related record (line price from the product, payment terms from the customer) | **Dynamic default value** (another field, a query worksheet or a function) | Same snapshot behaviour as Odoo, re-run when the inputs change. **Not applied** on import, API, workflow or bulk edit, so any workflow that creates lines (reordering, quotation templates) must set prices itself |
| Related fields (`related='partner_id.email'`) | Foreign field (worksheet-1) | A foreign field always follows its source. Use a dynamic default when the value must stay frozen |
| Stored computes (`amount_total`, `date_deadline`, `qty_to_invoice`) | Formula fields with the 76 functions; rollups (worksheet-1) | Date maths, rounding and text are covered. There is no SWITCH, IFERROR or amount-in-words, and DATEIF returns text |
| `resource.calendar` working days and public holidays; lead times in working days | **WORKDAY**, **WORKDAY_INTL** (weekend codes; 7 = Friday–Saturday, as in Kelantan and Terengganu), **NETWORKDAY**, with holidays kept in a text field and passed through `SPLIT` | Whole days only. There are no working hours per day, so Odoo's hour-based planning cannot be rebuilt natively |
| Payment terms (N days, end of month, N days after end of month) | DATEADD with `'+Nd'` and `'+1M'`, plus DAY() arithmetic for month ends | No EOMONTH; build it from DATEADD and DAY |
| Pricelist rounding, surcharge, minimum and maximum margin; cash rounding to 0.05 | ROUND, ROUNDUP, ROUNDDOWN, CEILING, FLOOR, MIN, MAX | No MROUND. The nearest multiple is `ROUND(x/m)*m`; test it for floating-point noise |
| UoM rounding up (`float_round(..., rounding_method='UP')`) | ROUNDUP / CEILING | |
| `selection` fields shared by several models (states, priorities, types) | **Option set** + single select | A label edit changes every field that uses the set |
| Coloured many2many tags (`crm.tag`, `product.tag`) | Multi-select with colours, ideally on an option set; or a Tags worksheet with a multi-record relationship | Option sets have no parent, no active flag and no extra fields, so `res.partner.category` (parent, active) stays a worksheet, as the foundation plan has it |
| `_rec_name`, `display_name` | **Title field** | A Concat title such as "Company, Person" cannot be "searchable in related worksheets". If later modules need to search orders by the customer's display name, have the workflow write it into a Text title (foundation #1) |
| A many2one `domain` (contacts of the chosen customer; only saleable or active products) | **Filter related records** with dynamic values | Good fit |
| `child_of` domains (a category with its sub-categories, a location tree) | Only Department and Region/City have Belongs To and Subordinate operators | Relationship trees cannot be filtered by subtree. Keep a stored full path ("All / Saleable / Office") and filter with Starts With, or keep a relation to all ancestors |
| Search panel, favourites, shared filters (`ir.filters`) | Saved filters (Personal / Public), condition groups | |
| Totals in list views (`sum`, `avg`) | Column statistics | Table view only |
| `active` with Archive / Unarchive | Not covered by these pages. Use an Active check item with view filters and picker filters (the docs' "only active products" example) | The recycle bin is deletion, not archiving |
| Locked documents (locked sales orders, posted entries, done transfers) | **Record lock** (a business rule when Status = Posted), or read-only rules driven by status | Only admins unlock, while Odoo lets accountants reset to draft. Locked records cannot be approved, and lock status cannot be filtered. The docs don't say whether workflows can still update a locked record |
| Chatter (`mail.thread`): log notes, @mentions, followers, field tracking | Record **discussion**, the follow bell, the **Update Record Followers** node, and the operation **log** (before/after, exportable) | Internal members only. No "send message" from the record to the customer by email |
| `copy()` with `copy=False` fields | **Copy** / **Recreate** | Copies every field value; there is no per-field "don't copy". Reset numbers, states and dates with a create workflow. List-mode relations are not copied; subforms copy up to 200 rows |
| Save & New | **Continue to Create** + **retain values** | Better than Odoo for entering many records |
| Draft records (draft quotation, draft invoice) | A **Status** value, ideally from an option set | HAP drafts are private, unvalidated and invisible to workflows and the API, so never use them as Odoo drafts. Consider turning drafts off on transactional sheets |
| The user's `tz`; `Datetime` versus `Date` | Personal time zone; date-only fields never shift | SaaS server time is UTC+8, Malaysian time, so native "today" matches what Odoo shows Malaysian users |
| QWeb reports (quotation/order, pro-forma, invoice, delivery slip, picking operations, RFQ/PO) | **Word/Excel templates** with line tables, `sequencenumber`, `[M]`, Repeat blocks, NoDataNotPrint, `[qrcode]`/`[barcode]`, member details and date formats; template **Scope** and **filter** per status | Strong fit. Paid editions only, and the layout is made in MS Office. For several languages, make one template per language and filter on a language field |
| `print_report_name` | Export file name rule (template name + title + time, or chosen fields) | |
| Report shown only in some states | Template filter conditions and view scope | |
| `is_move_sent`; cheques printed once, then reprinted | **Track Print Count** + a per-template **Print Limit** + admin reset | Professional edition only |
| Product, lot and location labels (`product.label.layout`) | **QR/barcode printing**: label-printer sizes or A4 grids, extra fields, up to 200 per batch | Code128 only (no EAN-13 symbology is documented), 30 characters, and not in Safari |
| e-invoice QR code (MyInvois validation link) | `#{[qrcode]Field$[w*h]$}` in the invoice template | QR codes hold up to 150 characters; check a real validation link |
| CRM duplicate detection (similar leads by email, phone, partner) | Prevent duplicate input (manual, exact) or a unique index (exact, all write paths, one empty row) | No similarity matching. A workflow query or a Query Records field (worksheet-1) can list possible matches |
| `base_import`: External ID, updating existing records, many2one by name | Excel import: Record ID or key fields (Skip / Overwrite / Update only), relationship auto-link, Allow New Options, Skip Error Data, saved configuration | Lines cannot come in the parent's file (Odoo's one2many import). They go into their own worksheet afterwards, linked by the parent's key. Auto-link works only from the many side. Match keys must be Text, Phone, Email, ID, Auto Number, Record ID or Member, not Concat or a relationship |
| Import-compatible export (External IDs), saved export lists | Export with **Record IDs**, data IDs and Work IDs; a **default export configuration** that can be locked | Above 1,000 rows, records come out in creation order |
| Product images and documents named after the product (`default_code` in the file name) | **Import Attachments** with a matching field and a delimiter; link import `name.ext (URL)` | 100 files and 2 GB per upload; uploads count toward the attachment quota |
| Creating `ir.attachment` through RPC (base64 `datas`) | API `valueType 2` (base64) or URLs; workflow URL arrays | The docs show the older appKey/sign API; check the v3 equivalent |
| Website forms (`website_crm` Contact Us → lead), helpdesk ticket forms, surveys; UTM source, medium and campaign | **Public form** with URL-parameter source fields, device information, embed code, CAPTCHA/SMS, limits and a receipt | No Member or Department fields on the form; no AI autofill; anonymous limits are per device only |
| Customer portal: viewing a quotation or invoice; the "Share" link (`portal.share`) | A **record share** link (read-only, with the sharer's permissions); a `sharelink` QR code in the PDF; a **public query** for "check status by reference + email" | A share link cannot accept, sign or pay. Public query returns at most 50 rows and exact matches only. Real portals are a separate topic (portal pages) |
| Field-level privacy (`groups=` on fields, e.g. bank account numbers) | **Field masking** + field permissions (roles pages) | Masking is display-only: exports, Word/Excel printing and the API return the original |
| VAT, TIN and phone validation (`base_vat`, `phone_validation`) | **Regular expressions** with conditions (e.g. Country = Malaysia → TIN pattern) | At most 5 expressions per field, so only a handful of countries per field |
| Geolocation (`base_geolocalize`), delivery distance | Positioning field + **DISTANCE** (km) and **GETPOSITION** | |
| Technical field names, XML IDs | **Field aliases**, worksheet alias, developer notes (Get App Info returns them as `notes`) | Use aliases, not IDs, in templates and integrations; avoid the reserved aliases (`status`, `users`, `owners`, `keywords`, `relations` and others) |
| Mixins and shared field groups (an address block on contacts, companies and warehouses) | **Field templates** (up to 30 fields, organisation scope) | A copy, not inheritance: later template changes don't reach existing fields |
| "Where is this field used" | **View References**, ER Diagram | Use in business-rule actions is not listed |
| `index=True` | Indexes (5 per sheet) + automatic SaaS indexes | No automatic indexes on Server |
| Group-based access to buttons and actions (`create="false"`, export rights) | **Feature controls** by role and view | The page says "Specific system roles only"; whether custom roles can be chosen needs a check |
| Document lines (`sale.order.line`, `account.move.line`, `stock.move`) | A subform with an **entity worksheet**, or a relationship to a line worksheet | Deliveries, invoices and reports reuse the lines, so they need an entity worksheet. Blank subforms cannot be written by workflows or by import |

### 3.2 Effect on the wave 0 plan (`../../00-foundation.md`)

- **#6, unique country code and unique state code per country.** A **Unique Index** on Countries.Code and a composite one on States (Country + Code) could replace the planned workflow duplicate check. They would also cover the 251 + 2,130 seeded rows and every API or import write. Whether a relationship field can be part of an index needs a test: the page treats relationships as array fields, at most one per index. Fallback: a Text "Country code" key next to the state code.
- **#9, unique barcode.** A unique index alone does not fit: most products have no barcode, only one empty value is allowed, and Products and Variants are two sheets. Keep the planned save-flow check. A per-sheet unique index on a helper key (the barcode, or the record ID when there is none) can be added as a second guard.
- **#1, display name.** If the title field is a Concat field that builds the display name, related sheets cannot search by it. A Text title written by the workflow that is already planned keeps the search.
- **#12, pricelist price.** The rounding, surcharge and margin step fits native functions (`ROUND(x/r)*r`, MIN, MAX). Choosing the rule stays in the sub-process.
- **#14, activity state.** These docs put SaaS server time at UTC+8, as `../workflow-nodes.md` also found; that digest reports that only the code-block clock is UTC, so the plan's "server time is UTC" in §4 #14 applies to code blocks. The due date is date-only, so it never shifts.
- **§8, data load.**
  - Import in dependency order: Countries before States; Currencies before Rates; Units with their relative unit, and categories with their parents, each in two passes; companies before their people.
  - Give each loaded sheet an "Odoo ID" text field and use it as the matching key, so that a second run updates rows instead of duplicating them. Don't put a unique index on it if records created in HAP leave it empty.
  - Decide per load whether **Trigger Workflow** stays on. If it is off, computed values such as category full names (#10) need a one-off batch flow afterwards.
- **Sub-tables** (Currency Rates, Pricelist Rules, Attribute Lines, Attribute Values, Plan Steps). Make them entity worksheets so that Excel import and workflows can write to them.
- **§6, roles.** If custom roles can be selected, feature controls can hide Import, Export and bulk actions from the Employee role.

## 4. Traps

**Validation and uniqueness**
- Required is not checked on table-view edits, workflow or API writes, or Excel imports unless **Mandatory Validation on Write** is on. With it on, a workflow that leaves the field empty **stops with an error** [field-property].
- Prevent duplicate input checks manual input only; imports and API writes get through [field-property].
- A unique index allows **one** record with empty values. It cannot be created while duplicates exist anywhere, including recycle-bin rows that are not visible. The documented fix, **Empty Now**, deletes permanently. *[Inference]* In a shared app, get the owner's approval first [index-acceleration].
- Regex checks stop at the first failing expression; there are at most 5 per field, on text and file fields only [regular-expression].
- Exports, Word/Excel printing, the API and data sync always show the original of a masked field. *[Inference]* So masking is not access control [field-mask].
- Masking keywords match exactly and case-sensitively [field-mask].

**Defaults, functions and time**
- Static defaults apply on create only. Dynamic defaults also apply on edit and re-run when their inputs change. *[Inference]* A value the user edited by hand can therefore be replaced when an input changes [field-default-value].
- No default value of any kind applies on import, API, workflow or bulk edit [field-default-value; import-excel-data].
- Cached public-form data overrides default values [public-form].
- SUM, MIN, MAX and PRODUCT count empty as 0: the MIN of an empty price is 0, and a PRODUCT with an empty quantity is 0. AVERAGE skips empties [system-functions].
- DATEIF returns text with a unit; wrap it in FIND and NUMBER before arithmetic [system-functions].
- DATEADD offsets are text, and the unit letter is case-sensitive: `M` is month, `m` is minute [system-functions].
- WEEKDAY starts at Monday = 1; WEEKNUM defaults to weeks starting on Sunday [system-functions].
- A single select reads as an array (`[0]`). A function that returns a label not in the option list sets nothing [function-examples].
- A date "Equals" filter compares only the date part, and a date-time field displayed as a date can only be filtered by day [field-filter].
- 0 is not empty; an unticked check item and a missing file are [field-filter].
- Only date-time values are converted between personal and server time zones; date-only fields never are [time-zone].

**Records and permissions**
- Hiding a worksheet from navigation changes no permissions: users with access can still open it by direct link [operations].
- Hiding the Create button still allows records to be created through custom actions and relationship fields [function-switch].
- To block exports, turn off both the view's Export and bulk Export [function-switch].
- Turning off File Download does not affect files the user uploaded themselves [function-switch].
- Locked records cannot be edited, deleted or approved; only admins unlock them; lock status cannot be filtered [record-operations].
- Copy and Recreate copy every field. List-mode relations are not copied; subforms copy up to 200 rows and card or dropdown relations up to 5 [record-operations].
- Users who are not admins can restore only what they deleted themselves; only admins delete permanently [record-operations].
- Only internal members can follow a discussion [record-operations].
- A mentioned user opens the record read-only, and cannot open it at all if it is outside the view where they were mentioned [share].
- Field IDs can change when an app is duplicated, so templates and integrations should use aliases [field-property].
- Editing an option set's options inside one field changes every field that uses the set [option-set].
- Field templates are copies: fixing a template does not fix fields already made from it [field-template].
- Field references do not show use in business-rule actions [reference-details].
- A duplicated worksheet carries no data, discussions or logs; a deleted worksheet is gone after 60 days [operations].

**Drafts and submitting**
- Drafts skip all validation and all workflows, are invisible to queries and the API, and are capped at 10 per user per sheet. Their attachments still use storage [submit-form].
- Workflows start 5 seconds after creation. "Trigger workflow immediately" works only for records made with the Create button [submit-form].
- Retained values work only with Continue to Create [submit-form].

**Import and export**
- Import files are limited to 10 MB, 20,000 rows and 200 columns. Create-from-Excel allows 20 MB, but rejects merged cells and recognises only Number, Date and Boolean [import-excel-data; import-excel-create].
- Subform, Formula, Uppercase, Positioning, Foreign field, Rollup, Cascading, Signature, Barcode, Embed, Section and Remarks fields are listed as not importable, yet the same page explains how cascading values import. Treat cascading import as unproven [import-excel-data].
- Fields set to Hidden, Hide on create or Read-only, and fields a role cannot see when creating, can be imported by app admins only [import-excel-data].
- Turning off Trigger Workflow also skips date-field workflows due on the import day [import-excel-data].
- One page says Overwrite updates the record "with data from the Excel file", the other that it "fully replaces the existing record". Test whether fields that are not mapped survive [import-excel-data; import-update].
- Relationship auto-link works only from the many side; import the parents first [import-associate].
- Importing a single-member field when two users share a name imports nobody; a multi-member field gets everyone with that name [import-excel-data].
- Departments match by their lowest-level name only; Region/City needs full slash paths [import-excel-data].
- An export of more than 1,000 rows comes out in creation order, not the view's order. Related records stop at 1,000. Exporting selected records works in table view only [export-excel].
- Accelerated Export may export out-of-date cached titles and foreign values [export-excel].
- Exported attachment links need a login to open [export-import-file].
- The attachment import's Overwrite mode cannot be undone. Creating records for unmatched files may fail when other required fields have no default [export-import-file].
- Workflow file values need a JSON array string (`["url1","url2"]`); the API needs a comma-separated string. The URLs must be public, download directly and end in a file extension [workflow-api-upload-file].
- Batch-add API calls that carry attachments can time out [workflow-api-upload-file].

**Printing**
- Word/Excel templates need a paid version; print limits need Professional [print-template; print-times-limit].
- Templates made in WPS may print badly; only .docx and .xlsx files are accepted [word-print-template; excel-print-template].
- Related tables must be stand-alone tables, and a `.` in a relationship or subform name breaks its codes [word-print-template].
- One NoDataNotPrint block that holds several lists prints all of them if any one has data [print-template-rules].
- Excel templates cannot print an image and its file name together; documents print only their file name; `[auto*auto]` is invalid [print-template-rules].
- QR codes hold up to 150 characters; barcodes are Code128 with up to 30 [print-template-rules; print-barcode].
- Batch QR/barcode printing does not work in IE, Safari or the desktop apps and stops at 200 records. Fields hidden in the table view are left out of quick prints [print-barcode].
- Resetting a print count does not lower the record's total count [print-times-limit].
- System printing shows masked values masked, with no way to decode them [field-mask].

**External access**
- Public forms cannot show Member, Department or Org-role fields, and AI autofill is not available on them [public-form; submit-form].
- On anonymous forms, the per-respondent limit relies on the device cache [public-form].
- SMS verification is silently skipped when the form has no mobile number field [public-form].
- Public query needs an exact match on every required condition and returns at most 50 rows. To expose every record, the view must have no filters and no hidden fields [public-inquiry].
- Share links show data with the sharer's permissions, and turning sharing off kills every existing link [share].

**Search and performance**
- Text over 5,000 characters cannot be searched. At most 5 keywords count, and all must match [sort-filter-records].
- Searching through a relationship or foreign field needs a text-type target field. Concat, Rollup and Foreign-field titles cannot be searchable in related sheets [sort-filter-records; title-field].
- Not-equals, contains, starts-with, ends-with, is-empty and OR filters may not use indexes, and Pinyin sorting stops sort indexes being used [index-acceleration].
- Don't change or delete the indexes SaaS created itself. Server has no automatic indexes [index-acceleration].

## 5. To verify live

Run these on a scratch sheet in a test app, not on EMS or customer apps.

| # | Doc claim (cached 3 Nov 2026) | Why it matters | Suggested test | Source |
|---|---|---|---|---|
| V1 | A unique index blocks duplicates, allows one empty row, and takes at most one array field | Foundation #6 and #9; lot numbers later | Index Countries.Code, and States on Country relation + Code. Try duplicates through the form, import, API and a workflow; add two rows with an empty code; note the error text. See KB questions CN03-013 to CN03-015 | index-acceleration |
| V2 | With Mandatory Validation on Write, a workflow stops with an error when the field is empty | It could break workflows that fill records in stages | Turn it on for one field. Run a workflow that leaves the field empty, and one that updates a different field on a record where it is empty | field-property |
| V3 | Prevent duplicate input does not check import or API writes | The docs say nothing about workflow writes | Let a workflow write a duplicate value | field-property |
| V4 | Dynamic defaults re-run on edit, and never run on import, API, workflow or bulk edit | Order-line prices in Sales and Purchase | Give a line price a query-worksheet default. Change the product after editing the price by hand. Create a line by workflow, by import, by Copy/Recreate and as a subform row | field-default-value |
| V5 | SaaS server time is UTC+8; date-only fields are never converted; how DATENOW() behaves in formulas | Activity state #14; "due today" logic | Evaluate a formula with DATENOW() just after midnight Malaysian time. Check whether a stored formula refreshes without a save | time-zone; system-functions |
| V6 | What Overwrite does on import | Reloading data must not blank fields | Run an Overwrite import that maps only two columns | import-excel-data; import-update |
| V7 | Relationship auto-link: which match-field types work, and whether links inside one sheet work | Contact parents, the unit chain, categories | Import people that link to companies in the same sheet; match once by Record ID and once by name | import-associate; export-excel |
| V8 | Cascading fields are "not importable", yet import rules for them are given | Region or state pickers, if cascading is used | Import a cascading value by record ID and by path | import-excel-data |
| V9 | Which time zone imported date-time values are read in | Odoo exports | Import `2026-11-23 09:00` as a user in UTC+8, then as a user in another zone | time-zone; import-excel-data |
| V10 | A Concat title cannot be "searchable in related worksheets" | Foundation #1 and searching orders later | Set a Concat title, look for the option, and search from a related sheet | title-field |
| V11 | Field IDs may change when an app is duplicated; aliases stay | One master app with pruned customer copies | Duplicate a small app; compare field IDs and aliases; print a Word template that uses aliases in the copy | field-property |
| V12 | Feature controls offer "specific system roles only" | Restricting Import and Export to the Master Data Manager | Open the role picker of a function switch | function-switch |
| V13 | Locked records "cannot be deleted or modified in any way" | Posted invoices still need payment-status updates | Update a locked record by workflow and by API; lock one through a business rule as a user who is not an admin | record-operations |
| V14 | Word/Excel templates (paid) and print limits (Professional) on our edition; Online Editing before printing | Sales and Invoicing documents | Find the edition of the organisation that hosts Odoo Replica (AI), and check whether these template types, Print Limit and Online Editing are offered | print-template; print-times-limit; word-print-template |
| V15 | QR up to 150 characters; barcodes Code128 up to 30; no EAN-13 mentioned | MyInvois QR; product labels | Encode a real MyInvois validation link; print a 13-digit EAN as a barcode and scan it | print-template-rules; print-barcode |
| V16 | Public-form SMS verification and CAPTCHA | Lead capture in Malaysia | Turn on SMS verification on a test form with a +60 number. a person (never the AI assistant) does the OTP and CAPTCHA, per the workspace rules | public-form |
| V17 | Workflow uploads need URLs that end in a file extension | e-invoice PDFs; signed URLs | Upload from a URL that carries a query string | workflow-api-upload-file |
| V18 | Copying a record copies every field | Odoo's `copy=False` | Copy a record that has an Auto Number and a status; check whether the number is regenerated and whether create workflows run | record-operations |
| V19 | Option-set edits spread to every field; sets can move between apps | Shared states across modules | Edit an option label inside one field; check the other sheets and the language pack | option-set |
| V20 | Drafts are on by default and invisible to workflows | Users might save drafts instead of submitting | Check the default on a new sheet; decide whether to turn drafts off on transactional sheets | submit-form |
| V21 | The "trigger workflow immediately" option exists | A faster screen after creating a record | Look for the option on Nocoly SaaS | submit-form |
| V22 | The API attachment upload format | Integrations | Make the same upload through the v3 API | workflow-api-upload-file |

## 6. Coverage

All 40 pages of the slice, in the order `read_pages.py` lists them.

| # | URL | Title | Summary |
|---|---|---|---|
| 1 | https://help.nocoly.com/worksheet/excel-print-template | Create an Excel Print Template | Excel (.xlsx) templates built from field codes: reference table, detail tables with `sequencenumber`, export file name, download and edit-before-print options |
| 2 | https://help.nocoly.com/worksheet/export-excel | Export Records to Excel | What can be exported (view, selection, all through Data Management), order rule, fields, record IDs, related records, accelerated export, Excel/CSV, number formats, ID columns, default configuration |
| 3 | https://help.nocoly.com/worksheet/export-import-file | Attachment Export and Import (Images/Documents) | Batch attachment export (paid; 1,000 files / 1 GB), attachment links in Excel, import by URL, bulk import of local files matched by file name (100 files / 2 GB) |
| 4 | https://help.nocoly.com/worksheet/field-default-value | Field Default Values | Static and dynamic defaults (current date/user/department, other fields, query worksheet, function), supported types, when they apply, compared with foreign fields |
| 5 | https://help.nocoly.com/worksheet/field-filter | Data Filtering | Filter operators by field family, AND/OR and condition groups, what counts as empty, date precision, department and region hierarchy operators |
| 6 | https://help.nocoly.com/worksheet/field-mask | Field Masking Display | Masking rules (full, preset, custom with start/middle/end characters and keywords), virtual length, decode permissions, where originals or masks always show |
| 7 | https://help.nocoly.com/worksheet/field-property | Field Basic Properties | Required and mandatory validation on write, duplicate prevention, read-only, hidden, width, style, descriptions, aliases and reserved names, developer notes, bulk field edits |
| 8 | https://help.nocoly.com/worksheet/field-template | Field Templates | Reusable field groups (personal or organisation), 30-field and 100-template limits, copy model, relationship handling, unsupported types |
| 9 | https://help.nocoly.com/worksheet/filter-associated-records | Filter Related Records | Picker filters with fixed or dynamic values; customer → contact cascading example |
| 10 | https://help.nocoly.com/worksheet/function-examples | Examples of Setting Default Values with Functions for Different Field Types | How functions set and read check items, single selects (`[0]`) and multi selects |
| 11 | https://help.nocoly.com/worksheet/function-switch | Feature Controls in Worksheets | Switches by role and view for create, import, recycle bin, statistics, embedding, export, bulk actions, quick edit, record actions, discussion and log, file download, approval fields |
| 12 | https://help.nocoly.com/worksheet/import-associate | How to Automatically Link Records When Importing from Excel | Relationship auto-link through a matching field; many side only; import the parents first |
| 13 | https://help.nocoly.com/worksheet/import-excel-create | Create Applications and Worksheets from Excel | Building an app or sheet from Excel: steps, type detection, title choice, size and row limits, no merged cells, relationships only to existing sheets |
| 14 | https://help.nocoly.com/worksheet/import-excel-data | Import Excel Data into a Worksheet | Import steps and limits, duplicate handling (Skip / Overwrite / Update only), error skipping, workflow trigger, saved configuration, new options, fields that cannot be imported, member/department/region/cascading rules |
| 15 | https://help.nocoly.com/worksheet/import-update | How to Update Existing Records When Importing from Excel | Using Identify duplicate records with a unique matching field to update records instead of creating them |
| 16 | https://help.nocoly.com/worksheet/index-acceleration | Worksheet Indexes | Indexes and unique indexes; limits (5 per sheet, 1 text index, 1 multi-select per index); recycle-bin conflicts; automatic SaaS indexes; query patterns that use indexes |
| 17 | https://help.nocoly.com/worksheet/introduction | Introduction to Worksheet | Worksheets as online Excel with records, discussions, relationships, import and no-login data collection; links to the basic topics |
| 18 | https://help.nocoly.com/worksheet/operations | Basic Operations on Worksheets | Name, description, record name, aliases and notes, duplicate, delete/restore (60 days), move, hiding from navigation, groups |
| 19 | https://help.nocoly.com/worksheet/option-set | Option Set | App-level option lists: create, convert, edits that sync, disable, delete when unused, move, view usage |
| 20 | https://help.nocoly.com/worksheet/print-barcode | Print QR Codes/Barcodes for Records | Batch QR and Code128 printing from table view: sources, label and A4 printers, extra fields, templates, 200 records per print |
| 21 | https://help.nocoly.com/worksheet/print-template | Print Templates | Five template types (Word/Excel paid, system, QR, barcode, cloud), 500 per sheet |
| 22 | https://help.nocoly.com/worksheet/print-template-management | Manage Print Templates | Redesign, rename, copy, delete, view scope, record filter, print limit, order |
| 23 | https://help.nocoly.com/worksheet/print-template-rules | Advanced Design Guidelines for Word/Excel Print Templates | Field-code syntax for options, images, QR codes and barcodes, line tables (row numbers, merge, repeat, join, first N rows, hide when empty), member details, date formats, print metadata |
| 24 | https://help.nocoly.com/worksheet/print-times-limit | Print Limits and Print Count Tracking | Professional and above: print counts, per-template limits per record, skipping in batches, admin reset |
| 25 | https://help.nocoly.com/worksheet/process-subform-data | Batch Processing Subform Data | Reading subform rows in workflows; adding rows only to subforms that have an entity worksheet |
| 26 | https://help.nocoly.com/worksheet/public-form | Public Forms | No-login forms: layout, access and time limits, response caps, password, SMS/CAPTCHA, caching, WeChat identity, receipts, URL source tracking, device information, embedding |
| 27 | https://help.nocoly.com/worksheet/public-inquiry | Public Query | Public exact-match search on a view, at most 50 results, optional download, ways to share the link |
| 28 | https://help.nocoly.com/worksheet/record-operations | Operations on a Single Record | Create, copy and recreate, favourite, lock, delete and restore, print, share, discussion and following, logs, navigation and Tab order |
| 29 | https://help.nocoly.com/worksheet/reference-details | Worksheet and Field References | Where-used lists for worksheets (also the ER diagram) and for fields, across fields, workflows, rule conditions and view filters |
| 30 | https://help.nocoly.com/worksheet/regular-expression | Regular Expressions | Input-format checks on text and file fields: presets or custom, conditions, up to 5 expressions checked in order |
| 31 | https://help.nocoly.com/worksheet/relationship-subform-comparison | Differences Between Subform and Relationship Fields | Containment versus association, how data is entered, when to choose which, converting between them |
| 32 | https://help.nocoly.com/worksheet/share | Public Sharing of Views and Records | Turning on view and record sharing, per-user links with the sharer's permissions, WeChat cards, access rules for @mentions |
| 33 | https://help.nocoly.com/worksheet/sort-filter-records | Record Search/Filter/Sort/Statistics | Searchable types and limits, saved personal and public filters, filter modes, temporary sort and column statistics in table view |
| 34 | https://help.nocoly.com/worksheet/submit-form | Submit Form and Save as Draft | Form title, AI autofill, drafts and their limits, submit and continue buttons, retained values, confirmation, immediate workflow trigger |
| 35 | https://help.nocoly.com/worksheet/system-functions | Overview of 50+ System Functions | 76 maths, date, text, logical and advanced functions with syntax, empty-value rules and examples (WORKDAY_INTL, DATEADD, DATEIF and more) |
| 36 | https://help.nocoly.com/worksheet/system-print-template | Create a System Print Template | Designer settings: tiled options, empty-field placeholders, subform layouts, date formats, download permission, record QR type, Word export |
| 37 | https://help.nocoly.com/worksheet/time-zone | Display Dates and Times in Your Personal Time Zone | SaaS server time UTC+8, personal time zones, which values are converted, the full time-zone list |
| 38 | https://help.nocoly.com/worksheet/title-field | Title Field | What the title field is for, allowed types, the searchable-in-related-worksheets option, where the title appears |
| 39 | https://help.nocoly.com/worksheet/word-print-template | Create a Word Print Template | Word (.docx) templates built from field codes: related tables, row numbers, troubleshooting, file name, download, edit before print, placeholders |
| 40 | https://help.nocoly.com/worksheet/workflow-api-upload-file | How to Upload Attachments via Workflow or API | URL uploads by workflow (JSON array) and URL or base64 uploads by API, timeouts, URL requirements |
