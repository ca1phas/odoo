# Views, custom pages, charts and custom actions (Nocoly HAP): native digest for the Odoo rebuild

| | |
|---|---|
| Slice | `read_pages.py --prefix view,custom-page,chart,custom-action`: 47 help.nocoly.com pages, cached 3 Nov 2026. All 47 were read in full (§6) |
| Written | 23 Nov 2026. Read-only: no app, view, chart, page, button or workflow was created or changed |
| For | Builders of the Odoo 20 modules in Odoo Replica (AI) on Nocoly SaaS. Rule: native HAP first (`BRIEF.md`) |
| Related | `../workflow-nodes.md` (button workflows, Interface Push). Form layout, field types, business rules, roles, portal and print templates belong to other digests; this file notes only where they touch views and buttons |

**Evidence tags**

| Tag | Source | What it proves |
|---|---|---|
| none in §2; [Doc] elsewhere | A page of this slice, cached 3 Nov 2026 | What Nocoly documents. Not a runtime test |
| [Odoo] | Odoo 19 Community source (`external/ca1phas-odoo/addons`) and the Odoo 20.0 module list (`../../catalogue/odoo-20.0/modules.csv`), read 23 Nov 2026 | What Odoo has, and whether it is Community or Enterprise. Other Odoo remarks are general knowledge, to be checked on candy99 |
| [Mem] | Project memory from live work on Nocoly SaaS (an earlier demo app, 19–23 Nov 2026) | One runtime observation, not repeated for this digest |
| [KB] | Internal reviews of the Mingdao HAP manual (`knowledge-base/nocoly-mingdao/internal/`) | Historical Mingdao text, used only where it agrees with the Nocoly pages |
| [Inf] | My inference | Not stated in the docs. Test it before relying on it |

## 1. Summary

- **Views:** 10 types. Table, Kanban/Gallery, Calendar and Org (= Odoo's hierarchy) match Community views. **Gantt and Map are native in HAP**, although in Odoo they are Enterprise-only. The Resource view gives Enterprise-style planning by resource.
- **Gaps:** no pivot or graph *view* (both are admin-built charts), no activity view, no kanban column totals or progress bars, no Gantt dependencies.
- **Custom actions = Odoo buttons and simple wizards.** A dialog edits chosen fields of the record or of one related record, or creates a related record, and/or a workflow runs. Options: confirmation with comment templates, password check, conditional availability, single or batch (a batch runs the workflow **once** for the whole selection).
- **Wizards with lines, and buttons that open their result,** need button → workflow → Interface Push opening a draft record [Inf].
- **Charts (17 types)** replace Odoo graph/pivot reports and KPI tiles. Admins configure them; users can only filter, sort, drill to records and export.
- **Custom pages are the dashboard layer:** ≤30 charts, embedded views (≤100 rows), linked filters, quick buttons (create with defaults, open view/page/URL, scan a code, call a PBP), URL parameters, public sharing.
- **Search:** Odoo's search view becomes view filters + quick filters (defaults, required, query first) + filter list (= searchpanel; can be a tree; presets new records). Grouping is set by the admin (≤50 groups); users cannot group ad hoc.
- **Caps:** Kanban 1,000 records, Map 200 pins, Org 1,000 rows per expanded level, Resource 50 resources, chart points 500–10,000, pivot 10,000 cells.
- **Safety traps:** link parameters fail open; a view share shows what the *sharer* sees plus related records; "All records" charts and "All data" drill-down bypass row permissions; inline edits skip business rules unless switched on; drags write fields with no dialog; the Data Management view ignores rules.

## 2. Capability inventory

Every row comes from the cached pages (docs, 3 Nov 2026) unless tagged. Each link opens the page on help.nocoly.com.

### 2.1 Views: rules shared by every view type

| Feature | What it does | Options and values (UI names) | Limits and notes | Source |
|---|---|---|---|---|
| View types | How a worksheet's records are shown | Table, Kanban, Details, Org, Gallery, Map, Resource, Calendar, Gantt, Plugin (custom). Data Management is an extra system view (§2.2) | Every worksheet keeps at least one view. Views change display only: copying or deleting a view never touches data | [view/introduction](https://help.nocoly.com/view/introduction) |
| Who configures | Create and configure views; choose which members may use each view | — | App admins only | [view/introduction](https://help.nocoly.com/view/introduction) |
| Navigation visibility | Show or hide a view in the menu | Per platform (web, mobile); "Hide from bar" on PC, mobile or both; Hide Across All Platforms | Hidden on all platforms = unavailable to every user, app admins included | [view/introduction](https://help.nocoly.com/view/introduction), [view/operations](https://help.nocoly.com/view/operations) |
| Filter | Limits the view to matching records | Field → operator → value; condition groups; "Parameter Value" once link parameters exist | Records enter and leave the view as their values change | [view/grid](https://help.nocoly.com/view/grid) |
| Sort | Record order | Custom sort on several fields; fallback default sort by Created Time or Last Modified Time; "No default sorting added" | Without a strictly ordered custom sort, "No default sorting added" can skip or repeat records between pages. Users can sort temporarily by clicking a column header | [view/grid](https://help.nocoly.com/view/grid), [view/introduction](https://help.nocoly.com/view/introduction) |
| Record colour | Colours records by status | A Single Select whose options have colours; choose which options colour; Sidebar / Sidebar + Background / Background Only | Only from one Single Select's option colours | [view/grid](https://help.nocoly.com/view/grid) |
| Field style | Field name and value colours set in the form editor's Style | Show on PC / Show on Mobile | — | [view/grid](https://help.nocoly.com/view/grid) |
| Field visibility | Hides fields in the view | Toggle per field (counter such as "10/12") | Hidden fields also disappear from record details opened from this view | [view/grid](https://help.nocoly.com/view/grid) |
| Auto refresh | Reloads the view | Interval | 10 s to 5 min | [view/grid](https://help.nocoly.com/view/grid) |
| Record click | What a click on a row or card does | Open the record details page / Open a link (URL held in a text field) / None | — | [custom-action/introduction](https://help.nocoly.com/custom-action/introduction) |
| View operations | Maintain views | Configure View; Copy from Other Views; Apply to Other Views; Change Type; Copy; Delete; Share; Export; Hide from bar; drag to reorder; search views | Apply to Other Views overwrites the targets. Change Type works freely between table, kanban, org, gallery, calendar, Gantt and others | [view/operations](https://help.nocoly.com/view/operations) |
| Share | Public link to a view | Page title, expiry date, password; turn sharing off | The recipient sees every record the *sharer* can see in that view, read-only, and can open related records. Turning sharing off invalidates existing links | [view/operations](https://help.nocoly.com/view/operations) |
| Export | Excel export from a view | Choose fields and format | Only records the exporting user can see | [view/operations](https://help.nocoly.com/view/operations) |
| Link parameters | URL values used as filter values | Define names on the view; filter value "Parameter Value"; `?a=1&b=2`; several values comma-separated; no quotes. Types: text (Text, Email, Telephone, ID Number, Concat, Autonumber), number (Number, Currency, Level, Rollup or Formula number), date (Date, Rollup or Formula date; `yyyy-mm-dd`, `yyyy-mm-dd hh:mm:ss`), time (`hhmmss`), boolean (Check items: 0/1, true/false) | An empty, missing or invalid value makes the condition **ignored**. Used on the view's public share link or embed link. Option, member and relationship fields are not in the type list | [view/link-parameter](https://help.nocoly.com/view/link-parameter) |
| Design patterns | How to split views | By status; by owner (My = current user, Team = current user and subordinates, All); by information scope (which fields show) | Avoid one view per growing value (versions, regions, models); use filters, quick filters or grouping instead | [view/split](https://help.nocoly.com/view/split) |

### 2.2 View types

#### Table ([view/grid](https://help.nocoly.com/view/grid))

| Setting | Options and values | Limits and notes |
|---|---|---|
| Default view | A table view "All" is created with each worksheet | — |
| Row height, column width | Drag, or Batch Settings for column style | An admin's width plus Save applies to all users; a non-admin's change is temporary |
| Display settings | Show Row Numbers; Show Record Quick Actions (hover "More": share, copy, delete); Show Summary Row; Show Vertical Grid Lines; Show Alternate Row Colors; Enable Title Line Wrapping (top-aligned or vertically centred) | — |
| Interaction mode | Classic (default: click opens the record, hover shows Edit) / Grid (select a cell, arrow keys, Enter to edit, Space to open) | — |
| Inline editing | On/off in the view and in the worksheet's Function Switch | If the two settings conflict, inline editing is off. Business rules apply to inline edits only with **Enable Business Rule** (may slow the view); the details page always applies them |
| Display Column | "Consistent with the form fields" (plus up to 6 system fields: Owner, Record ID, Creator, Last Modified By, Created Time, Last Modified Time) / "Customize display columns" (pick and reorder; Show All, Hide All, Reset Order) | Only fields visible in the Field section can be columns. Consistent mode shows the first 50 fields. Custom mode hides newly added fields by default. Column order never changes the form's field order |
| Column style | Alignment Left / Center / Right; width (manual, drag, Auto Fit); field statistics in the bottom row; Single Select shown as Plain Text, Label, Progress Bar or Cell Background Color; images Square, Circle or Auto Fit; "Apply to other table views" | — |
| Personal columns | Each user picks and orders their own columns (Column Settings icon) | Affects only that user |
| Freeze | Freezes a column and every column to its left | Up to 10 columns |
| Mobile | Records shown as cards; choose a card template and its fields | — |
| Grouping, quick filter, filter list | §2.3 | — |

#### Kanban ([view/board](https://help.nocoly.com/view/board))

| Setting | Options and values | Limits and notes |
|---|---|---|
| Grouping field (columns) | Single-select, Multi-select, Level, Members, Department, Org-Roles, Relationship (single record), Foreign field (data storage) | The grouping table on view/grid lists Kanban without Multi-select and with single-selection Members/Department/Org-Roles only. Conflict (§5, V12) |
| Display Items | All / Show items with data / Show specified items / Show items that meet the filter criteria (relationship field) | — |
| Group order | Sorting rule, or a custom order | Custom order covers the first groups, up to 50. Priority: Custom Sort > Defined Sort Rule > Default Sort. Members: custom only (else member ID order). Level: ascending, no custom order. Selects: option order. Relationship: order in which related records were added, or the related view's sort if set |
| Special columns | "Unassigned" (empty grouping value; hidden when empty); Pin First Kanban (Unassigned can be pinned) | — |
| Card | Title (default: the title field); Summary (long text); Display Fields, with or without field names; "Allow Users to Adjust Number of Fields Displayed"; Cover Image (file field; position; click can open the record); Card Width | Summary max 5 lines. Empty fields are not shown. The cover shows the most recent image. Width 280 px by default |
| Behaviour | Drag a card to another column; create a record inside a column; grouped display | A drag writes the grouping field. A record created in a column gets that column's value |
| Records | — | Up to 1,000 records (grouping limits table on view/grid) |

#### Gallery ([view/gallery](https://help.nocoly.com/view/gallery))

Image-led cards in tiles. Card settings as Kanban; filter, sort, field visibility, quick filter, filter list and grouping as Table.

#### Details ([view/details](https://help.nocoly.com/view/details))

| Setting | Options and values |
|---|---|
| Number of Records | Standard (Multiple): record cards on the left, the selected record's details on the right / Details Only (Single): the first record by the view's sort and filters opens directly |
| Action bar and record title | Show or hide (the action bar holds Print, Favorite and so on) |
| Close Sidebar | The discussion and log sidebar starts collapsed (it can still be expanded) |
| Card settings | For multiple mode |
| URL parameter | Single mode plus a filter on a link parameter opens one record from the public sharing link or the internal member link (e.g., `?name=…`) |

#### Calendar ([view/calendar](https://help.nocoly.com/view/calendar))

| Setting | Options and values |
|---|---|
| Dates | Start Date (required); End Date (optional); several date groups, each with its own label (e.g., review, beta, go-live) |
| Display | Default Month / Week / Day (users can switch); first day of the week Monday or Sunday; title field; record card on hover (fields, cover) |
| Options | Show Lunar Calendar; Show Weekdays Only (choose the days); 24-Hour Format; Show All Schedules |
| Drag | Moves the Start Date; the End Date adjusts |
| Scheduling panel | "Schedule" button: All / Scheduled / Unscheduled (by Start Date) |

#### Gantt ([view/gantt](https://help.nocoly.com/view/gantt))

| Setting | Options and values |
|---|---|
| Bars | Start and End date fields; a red line marks today; the left list shows title, start, end and duration by default |
| Milestone | A Check item field marks a record as a milestone (no duration) |
| Left list | Title; Display Fields |
| Grouping | Single Select, Level, Members, Department, Org-Roles, Relationship (single record), Foreign field; show all groups / only groups with records / specific groups; group sorting |
| Timeline | Default Timeline Precision day / week / month / quarter / year; Show Weekday Only; labels beside the bars; record card on hover |
| User actions | Resize or collapse the record list; drag a bar's edges or the whole bar; export the view as PNG; switch precision; jump to today; search and locate records |
| Unscheduled | Records "without both start and end dates" are unscheduled and hidden by default; users can show them and click a date to assign it |
| [Mem] | A begin/end date displayed as month only (`showtype 4`) made the Gantt open on its setup panel. The time scale a user picks is kept per browser |

#### Resource ([view/resource](https://help.nocoly.com/view/resource))

| Setting | Options and values |
|---|---|
| Resource field | Members, Department, Org-Roles; Single-Select, Multi-Select, Level; Relationship (single or multiple records, card or dropdown); Foreign fields (data storage) |
| Time | Two date/time fields: start and end |
| Resource panel | Display Items (up to 50 resources); Display Fields; Cover Image (click can open the record) |
| Calendar panel | Default view Year / Month / Week / Day; first day of the week; Show Weekdays Only; Show Work Hours Only; 24-Hour Format |
| Colour | Blue by default, or a Single Select's option colour |
| Actions | Add a record next to a resource; resize the panel; drag a bar's edges or the whole bar to change the time or reassign the resource; previous/next period; export as PNG; switch Day / Week / Month / Year |

#### Map ([view/map](https://help.nocoly.com/view/map))

| Setting | Options and values | Limits and notes |
|---|---|---|
| Data | One Positioning field | Up to 200 records drawn; the sort decides which |
| Card | As Kanban | — |
| Label | The title field; colour Light / Dark / Dynamic (a Single Select's colour) | A Concat field as the title gives richer labels |
| Pin and card colour | From a Single Select | — |
| Default display | Show All Locations / Current Location / Fixed Location | — |

#### Org ([view/org](https://help.nocoly.com/view/org))

| Setting | Options and values | Limits and notes |
|---|---|---|
| Structure | Same worksheet (parent–child, e.g., employee and supervisor) or multiple worksheets (one per level, e.g., project → task → subtask) | The relations must already exist |
| Layout | Display Style horizontal / vertical / mixed; Connection Line straight / curve; Summary; Display Fields (field names optional); Cover | — |
| Add | [+] for one record; paste several lines to create one record per line | Quick create writes the title only; it ignores required fields and default values |
| Other | Edit the title on the card; download the tree as an image | — |
| Loading | Level by level | Up to 1,000 records per expanded level. Deleting a level removes it and the levels below it from the view, not worksheets, data or relations |

#### Plugin ([view/plugin](https://help.nocoly.com/view/plugin))

| Setting | Options and values |
|---|---|
| What | A view written in code by a developer, for layouts the preset views cannot give |
| Publishing | An Organization Admin publishes, installs or imports it; every enabled plugin is then available to all users of the organisation |
| Inside | Search, filter, statistics and quick filter; a public JavaScript interface calls system components (record details page, add-record window) |
| Configuration | Fields and settings as for preset views; permissions for view, edit, delete and system operations; can be shared |

#### Data Management, a system view ([view/data-management](https://help.nocoly.com/view/data-management))

| Setting | Options and values |
|---|---|
| Access | Not in the new-view panel: view list → "Data Management"; it then shows as the worksheet's first view |
| Who | App admins only; it cannot be selected in role permissions |
| Configuration | As a table view, without field hiding or filters |
| Effect | Overrides hide and read-only from field properties and business rules: every field visible and editable, every button and print template shown and working, every function switch on |

### 2.3 Finding records: quick filter, filter list, grouping ([view/grid](https://help.nocoly.com/view/grid))

| Feature | Options and values | Limits and notes |
|---|---|---|
| Quick filter | View Configuration > Quick Filter > Select Fields; filter method and default value per field (defaults can use link parameters); Query Button on (required fields allowed; Enter starts the search) or off (searches on each change); Display Data Only After Query | More than three fields turns the Query Button on automatically |
| Text search | Several keywords at once, one per line | A record matches if it has any of them (OR) |
| Option fields | Choose which options appear; add an "Empty" option and rename it (e.g., "Not Set") | — |
| Relationship fields | All related records / specified ones / those meeting conditions (dynamic values allowed, e.g., another quick filter's value) | In dropdown mode only text-type fields are searchable |
| Date presets | Predefined ranges | Limited by the field's precision (no "Past 1 Hour" on a day field) |
| Filter list | One option-type field listed on the left: Single Select, Multi Select, Level, Members, Department, Org-Roles, Cascading, Relationship (single record), Foreign Field (data storage), Region/City. "All" and "Empty" options (renamable); only options with records, or specified ones; conditions on related records; option sorting; use the selected option as the default for new records; width | Related records show as a tree when the related worksheet has an org view. "All" is always first. Relationship options can be sorted only with "Display specified items". Width 200 px by default, 100–500 px |
| Grouping | View Configuration > Group. Table/Gallery fields: Single-Select, Multi-Select, Level, Relationship (Dropdown/Card), Members/Department/Org-Roles (single and multiple), Foreign Field (data storage). Kanban fields: Single Select, Level, Relationship (single record), Members/Department/Org-Roles (single), Foreign Field (data storage). "Ungrouped" group shown or hidden. Default state: expand first group only / expand all / collapse all | Table/Gallery: no record limit, up to 50 groups. Kanban: up to 1,000 records, no group limit |

### 2.4 Custom actions (buttons)

Sources: [custom-action/introduction](https://help.nocoly.com/custom-action/introduction), [custom-action/operations](https://help.nocoly.com/custom-action/operations), [custom-action/display](https://help.nocoly.com/custom-action/display).

| Feature | What it does | Options and values | Limits and notes |
|---|---|---|---|
| Create | Adds a button | Worksheet: Form Settings > Custom Action > Add Button. View: Configure View > Data Operation > + Action | Worksheet buttons are in all views by default. View buttons are only in that view by default, and also appear in the worksheet's list |
| Look | Name, icon, colour, description | The description shows on hover | No limit on the name's length |
| Action | What a click does | Execute a workflow directly / Open a pop-up window for completing specific fields / both (fields first, then the workflow) | — |
| Dialog target | Which record the dialog writes | Current record or a related record; update existing fields or create a new related record. Four cases: fill the current record; create a related record for it; update a related record; create a related record for a related record | The related record must be a single related record |
| Dialog fields | Per field | Read-only / Editable / Required. Default: fixed / dynamic (Members and dates: current user, current date) / clear value (saved blank if left empty). In a related-record dialog, defaults can come from the current record | — |
| Confirmation | Asks before running | Confirmation prompt; optional comments; comment templates | Comments can be read in the workflow |
| Password | Asks for the login password | On/off. Organisation super admins can add "Passwordless Verification Within 1 Hour" | — |
| Workflow after the dialog | Runs a workflow after submit | Send the results to the user who clicked; "Continue Filling After Execution" reopens the dialog after each run | — |
| Workflow data source | Records passed to the workflow | Single Record / Multiple Records | Multiple: the workflow runs **once** and its trigger holds every selected record (read one with Get Single Data "From multiple data items") |
| Completion message | Toast after the workflow | "Notify When Workflow Completes", with custom text | The docs advise switching it off and reporting success or failure with an Interface Push node, because the flow can finish while the business step failed |
| Who clicked | — | System Fields in the workflow | — |
| Availability | When the button works | Always / When Conditions Are Met (filter conditions; otherwise greyed out). "Hide Unavailable Buttons" is set in the view | — |
| Placement | Where it shows | Record Details (record opened, or one record selected) / Batch Operations (several records selected in a table view) | Configured separately per view |
| Quick actions | Buttons on rows and cards | Custom actions, system action buttons, print templates. Table: action column (Data Operation > Inline Operation). Kanban, Gallery, Org: Card Operation. Styles Standard / Text / Icon Only | Up to 3 buttons shown, the rest under More; up to 3 primary (solid) buttons. Only Table, Kanban, Gallery and Org views |
| Groups and order | Organise buttons | Add Group (name, icon); drag buttons in and out; drag to reorder | Saved per view; Record Details and Bulk Actions are grouped separately; empty groups are hidden; deleting a group moves its buttons to the end. No reordering in the worksheet list (creation order) |
| Lifecycle | Manage buttons | Copy; rename; edit; Enabled / Disabled; delete | Copy also duplicates the workflow. Disabled: hidden from regular users, marked "Disabled" for admins. Deleted from the worksheet: goes to the Recycle Bin. Deleted from a view: "Remove from the current view only" or delete the action and its associated workflow (all views) |
| Scope | Where it is available | All Records (every view) / Specified View; then per view Record Details and/or Batch Operations | Set from the worksheet list ("Scope") |
| Why a button is missing | Troubleshooting page | Not added to the view; record opened from a related record whose relationship field uses a view without the button; conditions unmet with hiding on; button placed only in batch or only in details; batch disabled in the worksheet Function Switch; dialog on a related record (never available in batch) | With several records selected, conditions are not checked for display, but records that fail them are not processed |

### 2.5 Charts: general configuration ([chart/set](https://help.nocoly.com/chart/set), [chart/introduction](https://help.nocoly.com/chart/introduction))

| Feature | Options and values | Limits and notes |
|---|---|---|
| Create | Worksheet toolbar: Chart > Public or Personal Chart > + | Public: everyone who can open the worksheet. Personal: the creator only. Can be converted later |
| Data source | All records, or a view | A view is required for "Open in view" drill-down |
| Time range | Today, Yesterday, This Week, Last Week, This Month, This Year, custom; based on created time, updated time or a date field | — |
| Permissions | All records / Records with view permission (default) | — |
| Filters | Add Filter Field | — |
| Volume | No limit on records read; limit on items drawn | Pie and word cloud 500; column, bar and line 10,000; pivot 10,000 aggregated cells; other charts 5,000 (the scatter page says 1,000 points). Over the limit: "Unable to generate chart. The dataset is too large…" |
| Dimension, value, grouping | X dimension; Y value; grouping splits X into sub-series | Numbers: sum, max, min, average, count, distinct count. Other fields: count, distinct count. Empty result: Hide / Show as 0 / Show as "-" |
| Style | Total (toggle; second aggregation sum, average, max, min; label); Legend (position; click to hide a series); axes (labels, titles, auto-rotate, X scrollbar, Y line solid or dashed, Y min/max); data labels (values, separately for web and mobile; percentage; decimals; drop trailing zeros; hide overlaps); values (scale Auto, thousand, ten thousand, million; thousands separator; rounding standard, round up, truncate; prefix or suffix units); Top N; colour themes (classic, business) | 12 preset palettes; an option field's own colours are used by default ([chart/column-chart](https://help.nocoly.com/chart/column-chart)) |
| Analysis | View Raw Data: click an element → View in panel / Open in view; scope Based on permissions / All data. Reference lines: constant, min/max, average, median, percentile, trend; name, colour, solid/dotted/dashed; show the name or the value | "All data" shows records regardless of permissions |
| Admin actions | Setting; Personal ↔ Public; drag to reorder (for everyone); duplicate to this worksheet or to a custom page in any app where you are admin; enable sharing | — |
| User actions | Expand; filter; sort; share by link or QR code (no sign-in); Export to Excel (raw values or with display units); show the data as a table (vertical or horizontal); save as image (browser) | User filters cannot widen the scope. Sharing is off by default; app admins, developers and operators can switch it on; it needs Data Source "All records", otherwise "Unable to generate chart. No permission." Pivots export as laid out; other charts export the underlying X–Y rows |
| Chart menu | Share, Export to Excel, Remove from "Public" group, Copy to a custom page, Delete | From [chart/pie-chart](https://help.nocoly.com/chart/pie-chart) |

### 2.6 Chart types

| Chart | Specific options | Limits and notes | Source |
|---|---|---|---|
| Column / horizontal bar | Grouping; Stack; Percentage; legend colours (classic or Custom) | Several value fields act as the grouping, so no extra grouping field can be added | [chart/column-chart](https://help.nocoly.com/chart/column-chart) |
| Symmetric bar | Direction 1 and Direction 2 values; Vertical / Horizontal; maximum per direction; colour per direction; value labels; sort | One shared scale. Needs two fields: split a single Amount by type with a formula (`IF(Type = 'Refund', Amount, 0)`) or a rollup | [chart/symmetric-bar](https://help.nocoly.com/chart/symmetric-bar) |
| Line | X granularity (e.g., Month, Day); Line / Curve; Area; Stack / Cumulative / Cumulative Percentage | — | [chart/line-chart](https://help.nocoly.com/chart/line-chart) |
| Dual-axis ("combination chart") | Primary Y: several metrics, each column or line; secondary Y; maximum per axis; stacked columns; Cumulative; Month or Quarter granularity | The secondary Y axis is always a line | [chart/biaxial-chart](https://help.nocoly.com/chart/biaxial-chart) |
| Scatter | Point dimension; X; Y; point size (numeric, may equal X or Y); colour by an option field; quadrant lines with colours and labels | Max 1,000 points | [chart/scatter-diagram](https://help.nocoly.com/chart/scatter-diagram) |
| Radar | One dimension; one or more numeric metrics; axis min/max | — | [chart/radar-chart](https://help.nocoly.com/chart/radar-chart) |
| Pie | Circular (ring) or regular | — | [chart/pie-chart](https://help.nocoly.com/chart/pie-chart) |
| Funnel | Non-numeric dimension; numeric value; vertical or horizontal; conversion rate; comparison with the previous month or year | — | [chart/funnel-chart](https://help.nocoly.com/chart/funnel-chart) |
| Word cloud | Label field; size value; rectangular or elliptical | — | [chart/word-cloud](https://help.nocoly.com/chart/word-cloud) |
| Number | One or more values; optional dimension; MoM / YoY with display styles; empty value Hide / 0 / -- (one value) or 0 / -- (several); Total (with a dimension); icon and background colour (without); left or centre alignment; background colour or image; number size and colour; suffix; decimals | With a dimension, only the first value gets MoM/YoY | [chart/number-chart](https://help.nocoly.com/chart/number-chart) |
| Dashboard (gauge) | Indicator (Sum, Max, Min, Average); minimum and maximum from fields; Standard / Sector / Scale; ranges and colours; scale as numbers, percentage or hidden; pointer on or off | The indicator must be a number or formula field | [chart/dashboard](https://help.nocoly.com/chart/dashboard) |
| Progress bar | Value; target fixed or taken from a field; horizontal bar / ring / liquid fill; labels raw / percentage / value/target | Ratio = actual ÷ target × 100 %. Up to 4 charts per row | [chart/progress-bar](https://help.nocoly.com/chart/progress-bar) |
| Ranking list | Dimension; value; data bars (on by default); top-3 style | Field names show only when there are several values | [chart/ranking-list](https://help.nocoly.com/chart/ranking-list) |
| World map | Region (country, or province/city); value; point size; colour category; filters | **Professional Edition only.** Value and point size must be different fields (workaround: a calculated field = value + 0) | [chart/world-map](https://help.nocoly.com/chart/world-map) |
| Administrative division | Region field; scope National / Province / City (with a region picker); drill-down; filled map or bubble map | No drill-down below City | [chart/administrative-division](https://help.nocoly.com/chart/administrative-division) |
| Pivot table | Rows; columns; values; display fields of related records; header colours; column width Auto / Fixed (default) / Percentage, with "Equal Parts"; pagination; Single Line Display; cell colours; merge cells; freeze headers; Subtotal; row and column totals (name, hint, position, aggregation per field); top X rows or columns; display unit; font and background colour rules, data bars | Up to 100 rows per page (pagination on by default). Mobile: Fixed or Percentage widths only. Merging is on by default and kept in the Excel export. All headers frozen by default, at least 1 column | [chart/pivot-chart](https://help.nocoly.com/chart/pivot-chart) |

### 2.7 Custom pages

| Feature | Options and values | Limits and notes | Source |
|---|---|---|---|
| Create | [Create] > [Custom Page] > [Canvas]; "Edit Canvas" to change it | App Admins configure pages | [custom-page/introduction](https://help.nocoly.com/custom-page/introduction) |
| Components | Charts, Quick Buttons, Filters, Image Carousel, Views, Images, Text Blocks, Embedded URLs, Sections; containers Tabs and Cards | — | [introduction](https://help.nocoly.com/custom-page/introduction), [rich-text](https://help.nocoly.com/custom-page/rich-text) |
| Page settings | Style (theme colour; light or dark); Background (dark or light theme colour; white, grey or black; 6 geometric shapes); Global Color (overrides chart colours); Link Parameters (`?source=value`, used by charts and filters as Link Parameter → source); Page Layout Scroll / Adaptive; Auto Refresh; Linked Filtering | Auto refresh 30 s to 5 min | [introduction](https://help.nocoly.com/custom-page/introduction) |
| Component actions | Configure; add a title; duplicate; move to another page (also to another app where you are App Admin); delete; drag to reorder; resize from the bottom-right corner | — | [introduction](https://help.nocoly.com/custom-page/introduction) |
| Mobile | Hide components or change their order in the app | — | [introduction](https://help.nocoly.com/custom-page/introduction) |
| Sharing | Full screen, external share and save as image (each can be switched off); Embed Link (page components only, no navigation; the viewer must be signed in and allowed); Public Share (no sign-in; title, expiry date, password) | Public share is off by default and only App Admins can enable it. Switching sharing off invalidates old links | [introduction](https://help.nocoly.com/custom-page/introduction) |
| Chart actions on a page | Expand, favorite, filter, export to Excel, share | Share and export can be switched off: Page Setting → Chart Operations | [introduction](https://help.nocoly.com/custom-page/introduction) |
| Chart component | New chart, or copy one from a worksheet; resize; auto-refresh; linked interaction ("Auto-link components with the same data source") | Max 30 charts per page. Linking works only between charts on the same worksheet, and only on custom pages. This page says only charts auto-refresh; the introduction says charts or embedded views (conflict) | [custom-page/add-chart](https://help.nocoly.com/custom-page/add-chart) |
| Button component | Name, style, colour, icon, shape, width, buttons per row, defaults. Actions: Create a Record (defaults for Text, Number, Currency, Email, Date, Telephone, Single/Multiple Select, Members (Regular), Region/City, Check items, Level, Department, Relationship single/multiple card/dropdown, Subform; Members and Date can be dynamic); Open a View (same or new tab); Open a Custom Page (this app or another app in the organisation); Open a URL (current tab, new tab or popup; fixed or dynamic parameters); Scan QR Code / Barcode (phone camera, or a physical scanner on a PC); Call PBP. Button cards with a description; several buttons per card | URLs must start with https:// | [custom-page/add-button](https://help.nocoly.com/custom-page/add-button) |
| Filter component | Targets several charts and views; filter fields; default value from page link parameters; Enable Filter Button (Query and Reset; off = refresh on every change); Show Data Only After Filter Execution; field order; "As global config" (all fields share the same targets) | The first worksheet sets the field type and the others must match. Single- and multi-select filters need the **same option set** in every worksheet | [custom-page/add-filter](https://help.nocoly.com/custom-page/add-filter) |
| View component | Component name; worksheet and view; record limit; actions Add Record, Search, Filter, Drafts, Import; link to the filter component; Open View on (a click opens the record) or off (read-only list) | Up to 100 rows | [custom-page/add-view](https://help.nocoly.com/custom-page/add-view) |
| Carousel | Worksheet, view and file field (or barcode field); all images / first image per record / maximum number of images; fit mode, background, title, description; animation and interval; click: Open Record (popup, current page, new tab) / Open Link (popup, current page) / Preview Image | Title, description and link must be text fields | [custom-page/image-carousel](https://help.nocoly.com/custom-page/image-carousel) |
| Text, Image, Section | Text: headings, formatting, inline images. Image: Transparent or Card; Fill / Fit / Stretch; a click opens a link or a preview. Section: a heading in the app's theme colour | One image per Image component | [custom-page/rich-text](https://help.nocoly.com/custom-page/rich-text) |
| Containers | Tab: container name; each tab's name, order and display style; card or transparent mode; component borders. Card: component borders; show the card name | — | [custom-page/container](https://help.nocoly.com/custom-page/container) |
| Embed URL | URL; fixed or dynamic parameters; Show Action Bar (Refresh, Open in New Tab); size | https only. Dynamic values are user account information only; worksheet data cannot be used. A HAP view can be embedded by its address or share link | [custom-page/embed-url](https://help.nocoly.com/custom-page/embed-url) |
| External Link page | A navigation page of type "External Link"; URL parameters; language values en, ja, zh-hant, zh-hans; Open Mode: inside the app or in a new tab; Hide Title Bar | Embedded mode needs https and a site that allows iframes ("Connection Refused" otherwise). "Please enter a correct URL" means a missing http(s):// or a leading space | [custom-page/external-link](https://help.nocoly.com/custom-page/external-link) |
| Home-screen widgets | Phone widget → HAP → Chart or Custom Button → App → Custom Page → Component; resizable | iOS 14.0 and above, Android | [custom-page/mobile-display](https://help.nocoly.com/custom-page/mobile-display) |

## 3. Odoo rebuild notes

Odoo side: [Odoo] = checked in the Odoo 19 Community source and the 20.0 module list; the rest is general Odoo knowledge, to confirm on candy99. HAP side: [Doc] unless tagged [Inf].

### 3.1 Odoo view types → HAP

| Odoo view | HAP native | What carries over | Where native falls short | Fallback |
|---|---|---|---|---|
| **list** | Table view | Column set per view; the user's column picker ≈ `optional` columns; summary row with field statistics ≈ `sum`/`avg` footers; inline editing ≈ `editable`; record colour ≈ `decoration-*`; Single Select as Label or Progress Bar ≈ badge and progressbar widgets; row buttons (quick actions); batch buttons ≈ list header buttons and the Action menu; frozen columns and row numbers (Odoo has neither) | Odoo decorations take any expression; HAP colours come only from one Single Select, so keep a "display status" select updated by a workflow [Inf]. Users cannot group ad hoc; grouping is set per view (≤50 groups). Per-group subtotals, `handle` drag ordering and inline new lines are not documented. Inline edits skip business rules unless "Enable Business Rule" is on | Extra views; pivot chart |
| **form** | Record details page (its layout belongs to the worksheet and field digests) | From this slice: fields hidden in a view also hide on the details page opened from it, and buttons are scoped per view, so several views ≈ several form views per menu [Inf]. The Details view opens a record directly; custom-action dialogs are small forms | Header statusbar, notebook, smart buttons and ribbons are not in this slice | — |
| **kanban** | Kanban (grouped); Gallery (ungrouped cards) | `default_group_by="stage_id"` → group by a Relationship (single record) to a Stage sheet, columns in the related view's sort ≈ stage `sequence`; drag between columns; a new record in a column gets its value (≈ the quick-create default); card title, summary, fields, cover; Show specified items / Show items with data; pinned first column | Odoo's CRM kanban has a `progressbar` on `activity_state` with `sum_field="expected_revenue"` [Odoo]: no column totals or progress bars are documented. No folded stages (`fold`). 1,000-record cap (scope unclear, V1). A drag skips any dialog, such as a lost reason [Inf]. Odoo's quick-create mini-form is not documented | Funnel, number or ranking charts per stage on a page; plugin view |
| **calendar** | Calendar view | Start and end, Month / Week / Day, drag to reschedule, hover card; **several date fields in one calendar** (Odoo allows one `date_start` per view); unscheduled panel | No Year mode (the Resource view has one). Colour per attendee or per field, and the attendee filter sidebar, are not documented | Resource view; quick filters |
| **gantt** (Enterprise: no `web_gantt` in the 20.0 Community list [Odoo]) | Gantt view | Start/end bars, drag and resize, grouping (Members and relations included), milestones (Check item), labels, PNG export, unscheduled records with click-to-schedule, scale day to year | No dependencies (arrows, automatic rescheduling), no progress on bars, no totals row and no working-calendar shading beyond "Show Weekday Only" are documented | Resource view for planning by resource; plugin view or Compute for dependencies |
| **pivot** | Pivot table **chart** (worksheet chart area or a custom page) | Rows, columns, values; subtotals; totals with an aggregation per field; top X; colour rules and data bars; frozen headers; Excel export as laid out | Not a view: users cannot add or expand other groupings, flip axes or change measures, since the documented user actions are filter, sort, drill and export [Inf]. No period comparison documented. ≤10,000 cells, ≤100 rows per page | Several pivot charts; a grouped table with a summary row |
| **graph** | Bar, line, pie, dual-axis and symmetric-bar charts | Stack / Percentage / Cumulative ≈ Odoo's stacked and cumulative modes; Top N; reference and trend lines (Odoo has none); drill-down to records | The admin fixes chart type and measure; charts sit in the worksheet's chart area, not in a view switcher [Inf] | — |
| **map** (Enterprise: no `web_map` in the 20.0 Community list [Odoo]) | Map view | Pins, hover card, colour by Single Select, default centre | ≤200 pins. Needs coordinates in a Positioning field, whereas Odoo geocodes partner addresses (`base_geolocalize`, Community [Odoo]). No routing documented | World map and administrative-division charts for totals |
| **activity** (Community, `mail`; on leads, orders, pickings and invoices [Odoo]) | None | — | No grid of records × activity types with due-state colours and schedule-from-cell. Wave 0 already plans a Compute "My Activities" page with native fallback views and a calendar (`../../00-foundation.md` §5) | Activities sheet: Table grouped by type, Kanban by state, Calendar by due date; plugin view |
| **hierarchy** (Community, `web_hierarchy`; employee and department charts in `hr_org_chart`, `draggable="1"` [Odoo]) | Org view | Same-sheet parent/child (Manager) or fixed multi-sheet levels; card fields and cover; image export; quick add | Drag to re-parent is not documented. Quick add skips required fields and defaults. 1,000 rows per expanded level | — |
| **cohort, grid** (Enterprise) | None | — | — | Pivot by month; plugin view |
| **search view, searchpanel** | View filters, quick filters, filter list, grouping | §3.2 | — | — |
| **dashboards** (`spreadsheet_dashboard` plus 12 per-app dashboard modules, and `board`: Community [Odoo]) | Custom pages with charts | §3.4 | — | — |

### 3.2 Odoo search view → HAP

| Odoo | HAP | Notes |
|---|---|---|
| Predefined filters (`<filter domain=…>`, e.g., "My Pipeline") | Views split by status or owner for the main cases; quick filters with defaults for the rest | Avoid one view per growing value ([view/split](https://help.nocoly.com/view/split)) |
| Action context `search_default_*` | The view's filter, or a quick-filter default value (which can come from a link parameter) | — |
| `<searchpanel>` (used in account, hr, expenses and time off [Odoo]) | Filter list | Shows a tree when the related sheet has an org view; can preset the value on new records. Odoo's `enable_counters` (counts per option) is not documented |
| User "Group By" on any field, several levels | Grouping fixed by the admin per view | Nothing user-side is documented, so users cannot regroup [Inf] |
| OR within one filter | Several keywords in a text quick filter | — |
| Date filters (This Month, Q1 …) | Date presets in quick filters; chart time ranges | — |
| "Compare to previous period" in pivot or graph | Not documented for pivots; number charts have MoM/YoY; funnels compare with the previous month or year | — |
| Favorites (saved searches) | Not in this slice | — |

### 3.3 Odoo buttons, server actions and wizards → custom actions

| Odoo | HAP native | Notes |
|---|---|---|
| Form header button `type="object"` (e.g., `action_confirm`) | Custom action, "Execute a workflow directly", Single Record | The workflow does what the Python method did |
| Button `type="action"` opening a wizard (TransientModel in a dialog) | "Open a pop-up window for completing specific fields", optionally followed by a workflow | Cases below |
| `confirm="…"` | Confirmation, with optional comments | — |
| `invisible="state != 'draft'"` | Availability "When Conditions Are Met" + "Hide Unavailable Buttons" | Conditions are record filters, not Python expressions |
| `groups="…"` on a button | Role permissions on custom actions | Not in this slice (roles digest) |
| `btn-primary` / `oe_highlight` | Button colour; up to 3 primary buttons in quick actions | — |
| Row buttons in list or kanban | Quick actions (Inline Operation, Card Operation) | Table, Kanban, Gallery and Org only |
| List header buttons; server actions bound to the model (Action menu) | Batch Operations button with "Multiple Records" | One workflow run for the whole selection. Odoo methods loop over `self`, so the HAP flow must handle a set (loop or batch nodes, `../workflow-nodes.md`) [Inf] |
| Wizard that stores a choice on the record, e.g., `crm.lead.lost` (Lost Reason, Closing Note) [Odoo] | Dialog filling fields of the current record + confirmation comments with comment templates, then a workflow (set the stage, archive) | The wizard's fields become real fields on the record, which keeps them for reporting [Inf] |
| Wizard that creates a linked record, e.g., `account.payment.register` [Odoo] | Dialog "create a new related record" (a Payment linked to the Invoice) with defaults from the invoice, then a workflow | Related-record dialogs are not allowed in batch, so batch payment = batch button → workflow creates the payments [Inf] |
| Wizard with editable lines (return quantities, backorder confirmation) | No documented dialog with lines. Button → workflow creates a draft record with its lines → Interface Push opens it → a second button validates [Inf] | Interface Push limits: `../workflow-nodes.md` §3.4 |
| Method returning an action that opens the new record | An Interface Push node opens the record (custom-action Example 3) | — |
| `raise UserError(…)` | Switch off "Notify When Workflow Completes" and send the error text with Interface Push | The docs' own advice |
| `default_get` / context defaults | Dialog defaults: fixed, dynamic (current user, current date), clear, or values of the current record | — |
| "Save & New" | "Continue Filling After Execution" | — |
| Re-authentication for sensitive actions (`check_identity`) | Password verification (optional 1-hour passwordless window) | — |
| "Send by Email" (`mail.compose.message`) | Button → workflow that sends the message (nodes in `../workflow-nodes.md`); an editable message needs dialog fields on the record [Inf] | — |
| Duplicate / Delete / Share; Print menu | Record quick actions (share, copy, delete); print templates as row and card buttons | — |
| Menu item → window action with domain and context | A filtered view; custom page buttons (Open a View; Create a Record with defaults) | — |
| `ir.actions.act_url` | Button "Open a URL" (https), External Link page, record click "Open a link" | — |
| Barcode app (Enterprise) | Custom page button "Scan QR Code / Barcode" | What happens to the scanned value is not documented (V7) |
| Smart button (a count that opens a filtered list) | Not a custom action. Relation fields and rollups in the form (other digests); from this slice, a chart's raw-data drill or a page's "Open a View". The foundation plan uses a custom field (`../../00-foundation.md` §5) | — |

### 3.4 Odoo reporting and dashboards → charts and custom pages

- **Analysis reports** (sales, pipeline, invoices, stock moves) → public pivot and bar/line charts on the worksheet; personal charts for one user's own analyses.
- **Permissions.** Odoo reports obey record rules, as HAP's default "Records with view permission" does. "All records" shows totals over rows the user cannot open, which Odoo cannot do without `sudo` [Inf]. Keep the raw-data drill on "Based on permissions" in that case.
- **KPI tiles with a trend** (spreadsheet dashboards) → number charts with MoM/YoY.
- **Targets** (team invoicing target, revenue goal) → a progress bar with the target in a field, or a gauge.
- **Pipeline conversion** → funnel chart with conversion rates.
- **Overview kanbans** (Inventory Overview, Accounting Dashboard) → a custom page. Number charts per operation type or journal, whose "View Raw Data → Open in view" opens the list; "Open a View" and "Create a Record" buttons with defaults (e.g., a new Receipt) [Inf].
- **Dashboard global filters** → the filter component + linked charts. Select fields across sheets need one shared option set.
- **"Add to my dashboard"** (`board`) → no personal pages: App Admins build pages, and users keep personal charts on worksheets [Inf].
- **Sharing a dashboard outside the company** → public page share (password, expiry) or an embed link. Odoo Community dashboards have no public link [Inf].

### 3.5 Other Odoo screen concepts

- **Chatter** → the discussion and log sidebar on record details; a Details view can start with it collapsed ("Close Sidebar"). The discussion itself is in another digest.
- **Settings page** (`res.config.settings`) → a Settings sheet with one record, shown by a Details view in "Details Only (Single)" [Inf].
- **Archived records** (`active`) → views filtered on Active = yes, plus an "Archived" view [Inf].
- **A customer link to one document** → not a public view share (list-level, shows what the sharer sees) and never a view link parameter (fails open). Use record share links or the portal (other digests) [Inf].
- **`handle` sequence** (stages, pricelist rules) → a number field "Sequence" plus the view sort; drag ordering is not documented [Inf].
- **Folded stages** → Display Items "Show specified items" or "Show items with data" [Inf].
- **Kanban colour picker** → record colour from a Single Select [Inf].
- **Priority stars** → the Level field, which the field docs describe as a rating-style control for priority or satisfaction (worksheet/controls, outside this slice) [Inf].
- **Category and location trees** → an Org view on a self-relation, and a filter list that shows the tree in product or stock views [Inf].
- **BoM structure (multi-level)** → Org view levels are fixed per worksheet; recursion through the same sheets is not documented (V14) [Inf].
- **Mobile** → table card templates, per-platform view hiding, a mobile layout for pages, home-screen widgets.
- **Screens Odoo builds in JavaScript** → a plugin view (code published by an org admin; keeps HAP permissions, search and filters) is an alternative to Compute for list-like screens. It is still custom code [Inf].

### 3.6 Recipes for common Odoo screens [Inf]

| Odoo screen | Native HAP recipe |
|---|---|
| CRM pipeline | Kanban grouped by Stage (relation, single record; order from the Stage view's sort). Card: expected revenue, probability, salesperson. Record colour by priority. "Won" and "Lost" buttons; Lost = dialog with Lost Reason, Closing Note and comment templates, then a workflow. Leave Lost out of the columns (Show specified items) so nobody drags a lead into it. Totals per stage as a funnel or number chart on a CRM page |
| My Pipeline, My Activities | Views filtered on owner = current user; quick filters with defaults |
| Quotation → invoice | "Create Invoice" button: a dialog fills the invoice method and down-payment fields on the order, then a workflow creates the invoice and Interface Push opens it |
| Register payment | "Register Payment" button: a dialog creates a related Payment with defaults; a workflow updates the invoice's payment state |
| Inventory Overview | Custom page: number charts per operation type (drill opens the list), "Create a Record" buttons with the operation type preset, a Scan button |
| Transfer schedule | Calendar with two date groups (Scheduled Date, Deadline) |
| Stock on hand | Pivot chart product × location; table grouped by product with a summary row |
| Project tasks | Kanban by stage; Gantt with milestones (no dependencies); Org view project → task → subtask |
| Work-centre planning (Enterprise) | Resource view, resource = Work Centre relation |
| Employees | Gallery or Kanban with a photo; Org view on the Manager self-relation; filter list by Department |
| Contacts map (Enterprise) | Map view on a Positioning field (≤200 pins) |
| Company settings | Details view, single record |

### 3.7 Packaging: customer copies pruned by menu group (`../../README.md` §6, decision 3) [Inf]

- A custom page that mixes charts, filters or embedded views from several modules ties those modules together. Keep one dashboard page per module, and put cross-module dashboards in the bridge's menu group, so pruning a module removes them cleanly.
- Page filters across worksheets need a shared option set, which then becomes a shared foundation item.
- Charts and pages can be copied to other apps where you are admin; a copy is a separate object.
- Copying a custom action copies its workflow; the copies drift apart unless both are maintained.
- A chart whose data source is a view depends on that view. What happens when the view is deleted during pruning is not documented: check it in the prune test.

## 4. Traps

**Data exposure**

1. **Link parameters fail open.** An empty, missing or malformed value removes the condition, so the view shows everything the link can reach, and a single-record Details view opens the first record. Parameters are not access control. [Doc [view/link-parameter](https://help.nocoly.com/view/link-parameter), [view/details](https://help.nocoly.com/view/details); KB]
2. **A view share shows what the sharer sees,** read-only, and recipients can also open related records. [Doc [view/operations](https://help.nocoly.com/view/operations)]
3. **Chart sharing needs Data Source "All records",** and the raw-data scope "All data" ignores permissions. [Doc [chart/set](https://help.nocoly.com/chart/set)]
4. **Public page and view shares need no sign-in;** switching sharing off is the way to kill the links. [Doc]
5. **Embedded URLs can pass only user account details,** and URL parameters are not authentication. [Doc [custom-page/embed-url](https://help.nocoly.com/custom-page/embed-url); KB]

**Rules bypassed**

6. Table inline edits skip business rules unless **Enable Business Rule** is on (slower). [Doc [view/grid](https://help.nocoly.com/view/grid)]
7. Drags in Kanban, Calendar, Gantt and Resource views write the grouping field, the dates or the resource, and the docs mention no dialog. An input that Odoo asks for (lost reason, approval) can therefore be skipped. [Doc; Inf]
8. Org quick add and bulk paste write only the title and ignore required fields and default values. [Doc [view/org](https://help.nocoly.com/view/org)]
9. The Data Management view ignores hide and read-only from field properties and business rules, and shows every button and print template. [Doc [view/data-management](https://help.nocoly.com/view/data-management)]
10. Hiding a view, a button or a field is display, not permission; record colours are not validation. [KB; Inf]

**Custom actions**

11. Scope defaults differ: worksheet buttons appear in every view, view buttons only in their own view. [Doc]
12. A button can disappear when the record is opened from a parent's relationship field. That field must use a related view in which the button is enabled. [Doc [custom-action/display](https://help.nocoly.com/custom-action/display)]
13. With several records selected, availability conditions are not checked for display, and records that fail them are not processed (the docs mention no message to the user). Related-record dialogs never work in batch, and the worksheet Function Switch can turn batch buttons off. [Doc]
14. A "Multiple Records" button runs the workflow once for the whole selection, not once per record. [Doc]
15. "Notify When Workflow Completes" reports success even when the business step failed. [Doc]
16. Copying a button copies its workflow. Deleting from a view can delete the workflow for every view. Groups and order are per view and cannot be set in the worksheet list. [Doc]

**Views**

17. "Apply to Other Views" overwrites the target views. [Doc]
18. "Hide across all platforms" locks out app admins too. [Doc]
19. "No default sorting added" without a unique sort can skip or repeat records between pages; scripts that page through a view are affected too. [Doc; Inf]
20. A field hidden in a view's Field section also disappears from the details page opened from that view. "Customize display columns" hides new fields by default; "Consistent with the form fields" shows only 50. [Doc]
21. Caps: Kanban 1,000 records; Map 200; Org 1,000 per expanded level; Resource 50 resources; Table/Gallery 50 groups; Kanban custom order for 50 groups; page view component 100 rows; 30 charts per page; pivot 100 rows per page. [Doc]
22. Grouping and resources on a foreign field need its "data storage" mode. A stored lookup stays empty on old rows until an app admin recalibrates (once per sheet per 2 hours). [Doc; Mem]
23. Gantt: dates displayed as month only broke the view [Mem]. Records missing their dates are hidden as unscheduled by default [Doc].
24. Column widths set by non-admins are not saved. [Doc]

**Charts and pages**

25. Chart drawing caps: pie and word cloud 500; column, bar and line 10,000; pivot 10,000 cells; others 5,000; scatter 1,000. Over the cap the chart does not render. [Doc]
26. The world map is Professional Edition only, and its value and point size cannot be the same field. [Doc]
27. Chart quirks: with a dimension, only the first value of a number chart gets MoM/YoY; the dual-axis secondary axis is always a line; several values in a bar chart block grouping; a symmetric bar needs two fields. [Doc]
28. Page filters across worksheets need the same field type, and for selects the same option set. [Doc]
29. Auto-refresh conflict: one page says only charts refresh, the introduction says charts or embedded views. Views also have their own refresh (10 s to 5 min). [Doc]
30. Embedded pages and URL buttons need https, and the target site must allow iframes. [Doc]
31. A chart's Excel export holds the underlying rows (a pivot keeps its layout), not the picture. [Doc]
32. A plugin published by an org admin is available to every user in the organisation. [Doc]

## 5. To verify live

On Nocoly SaaS, in Odoo Replica (AI) or a test app, before the build depends on the claim.

| # | Question | Why it matters | Test | Priority |
|---|---|---|---|---|
| V1 | Does the 1,000-record limit apply to every Kanban, or only with grouped display? What does a user see above it? | CRM pipeline, transfers | Kanban on a sheet with 1,050 rows | High |
| V2 | Do business rules (validation, read-only), field permissions and role edit rights block a drag in Kanban, Calendar, Gantt and Resource views? Does an update-triggered workflow run? | Stage changes and rescheduling must keep Odoo's rules | Drag onto a read-only or rule-blocked value; check the workflow history | High |
| V3 | Which field types can a custom-action dialog show (subform, multi-record relation, attachment)? Are business rules applied inside it? Can "create a related record" pre-fill child rows? | Every wizard design | Button with a dialog on a test sheet | High |
| V4 | Batch buttons: maximum number of selected records; "select all" across pages; are records that fail the conditions left out of the trigger set? | Mass confirm, batch payments | Select 150 mixed records; read the run's input | High |
| V5 | Do link parameters fail open on a public view share and on a single-record Details view? Are parameter names case-sensitive (the page mixes `entry_date` and `EntryDate`)? | Any external link | Public link with an empty, a wrong and a missing parameter | High |
| V6 | Is "Enable Business Rule" off by default for inline editing, and are required and validation rules skipped when it is off? | Line and price edits in lists | Edit a ruled field inline | High |
| V7 | What does the page's "Scan QR Code / Barcode" button do with the code (open the matching record, fill a filter, pass it to a PBP)? Phone camera and PC scanner | Inventory, POS, Barcode-style screens | Scan a product barcode | High |
| V8 | With "Notify When Workflow Completes" off, does Interface Push from a button workflow open the new record, and show error text to the person who clicked? | Every "button returns an action" pattern | Button → create a record → push | High |
| V9 | Does a button disappear when the record is opened from a parent's relationship field, and does pointing that field at a view with the button fix it? | Order → invoice, transfer → move | Open a child from its parent | Medium |
| V10 | Chart with "All records" + raw data "Based on permissions": does a user without row access see the totals but no records? | Team dashboards | Two roles | Medium |
| V11 | Grouped table: are subtotals shown per group? What happens past 50 groups? | List views with sums | Group by a field with 60 values | Medium |
| V12 | Can a Kanban group by a Multi-select, or by a multi-value Members field? The two pages disagree | Tag boards | Try both | Medium |
| V13 | Do record colours show on Kanban, Gallery, Calendar and Gantt (documented for Table, Map and Resource)? Is there any column total or count on a Kanban? | Odoo kanban colours and progress bars | Configure and look | Medium |
| V14 | Org view: can the same worksheet appear at several levels (BoM recursion)? Can users drag to re-parent? | BoM structure, category and location trees | Three-level configuration | Medium |
| V15 | How does a Positioning field get coordinates from an address (manual only, or another feature)? Map tiles and search for Malaysia | Contacts, deliveries, field service | Enter a Malaysian address | Medium |
| V16 | Administrative-division chart with Malaysian states; is the world map visible on our organisation's plan (Professional only)? | Sales by state | Region field data | Medium |
| V17 | Which date granularities do chart axes offer (year, quarter, month, week, day)? | Weekly reports | Open the X-axis options | Medium |
| V18 | Which user attributes can an Embed URL pass (ID, name, email, phone)? | Embedding Compute pages | Inspect the generated URL | Medium |
| V19 | Do embedded views on a custom page auto-refresh (conflict), and at what minimum interval? | Warehouse wallboards | Page with a view and a 30 s refresh | Low |
| V20 | Gantt: is a record with only one of its two dates "unscheduled"? Does the default precision win over the per-browser scale [Mem]? | Project and MRP planning | Two test records | Low |
| V21 | Calendar: colour by Single Select? Does a drag keep the duration? | Meetings, deliveries | Drag a two-day record | Low |
| V22 | Are plugin views available to our organisation, and who can publish them? | Fallback for the activity view and Gantt dependencies | Look at the plugin list (read-only) | Low |
| V23 | Password verification and the 1-hour passwordless option on Nocoly SaaS | Sensitive buttons (post, cancel) | Configure on a test button | Low |
| V24 | Can a link parameter filter an option, member or relationship field (they are not in the type list)? | Deep links from other systems | Define one and try | Low |
| V25 | Does the Data Management view also skip required and validation rules, or only hide and read-only? | Admin data fixes | Save a record with a required field left empty | Low |

## 6. Coverage

All 47 pages of the slice, in `read_pages.py` order.

| # | URL | Title | Summary |
|---|---|---|---|
| 0 | https://help.nocoly.com/chart/administrative-division | Administrative Division | Map chart on a Region field with National / Province / City scope, drill-down, filled or bubble style |
| 1 | https://help.nocoly.com/chart/biaxial-chart | Dual-Axis Chart Creation Guide | Primary and secondary Y axes (secondary always a line), per-axis maximum, stacking, cumulative mode |
| 2 | https://help.nocoly.com/chart/column-chart | Bar Chart / Horizontal Bar Chart Creation Guide | Grouping with Stack or Percentage, 12 palettes and option colours; several values block extra grouping |
| 3 | https://help.nocoly.com/chart/dashboard | Dashboard | Gauge with a numeric or formula indicator, minimum and maximum fields, three styles, ranges, pointer |
| 4 | https://help.nocoly.com/chart/funnel-chart | Funnel Chart | Stage dimension and numeric value; vertical or horizontal; conversion rate; period comparison |
| 5 | https://help.nocoly.com/chart/introduction | Introduction to Statistical Charts | The chart types and when to use each: comparison, trend, proportion, business-specific, key metrics |
| 6 | https://help.nocoly.com/chart/line-chart | Line Chart Creation Guide | Month or day granularity; line, curve or area; stack, cumulative, cumulative percentage |
| 7 | https://help.nocoly.com/chart/number-chart | Number Chart | One or more KPI values; MoM/YoY (first value only with a dimension); icons and card style |
| 8 | https://help.nocoly.com/chart/pie-chart | Pie Chart | Ring or regular pie; chart menu: share, export, remove from Public, copy to a page, delete |
| 9 | https://help.nocoly.com/chart/pivot-chart | Pivot Table | Rows, columns, values; subtotals and totals; width modes; 100 rows per page; merge, freeze, top X, colour rules |
| 10 | https://help.nocoly.com/chart/progress-bar | Progress Bar | Value against a fixed or field target; bar, ring or liquid; label formats; up to 4 per row |
| 11 | https://help.nocoly.com/chart/radar-chart | Radar Chart | One dimension, several numeric metrics, axis min/max |
| 12 | https://help.nocoly.com/chart/ranking-list | Ranking List | Dimension ranked by value, data bars, top-3 styling |
| 13 | https://help.nocoly.com/chart/scatter-diagram | Scatter Chart | X, Y, size and colour by option; quadrant lines; max 1,000 points |
| 14 | https://help.nocoly.com/chart/set | General Configuration for Charts | Public and personal charts, data range and permission modes, drawing limits, style, raw data and reference lines, management, sharing, export |
| 15 | https://help.nocoly.com/chart/symmetric-bar | Symmetric Bar Chart Creation Guide | Two opposing metrics on one scale; needs two fields (formula or rollup to split one) |
| 16 | https://help.nocoly.com/chart/word-cloud | Word Cloud | Label and size fields; rectangular or elliptical |
| 17 | https://help.nocoly.com/chart/world-map | World Map | Country or province bubbles with size and colour; Professional Edition only; value must differ from point size |
| 18 | https://help.nocoly.com/custom-action/display | Why Isn't My Custom Action Displayed When Opening a Record? | Why a button is missing: view scope, opening from a related record, hidden conditions, single vs batch placement, Function Switch |
| 19 | https://help.nocoly.com/custom-action/introduction | Custom Actions | Buttons that open a field dialog and/or run a workflow; single vs multiple records; confirmation, password, availability, buttons on rows and cards |
| 20 | https://help.nocoly.com/custom-action/operations | Manage Custom Actions | Groups and order per view, copy with workflow, enable/disable, delete options, scope by view and placement |
| 21 | https://help.nocoly.com/custom-page/add-button | Adding Buttons to a Custom Page | Button actions: create a record with defaults, open a view, page or URL, scan a code, call a PBP; button cards |
| 22 | https://help.nocoly.com/custom-page/add-chart | Adding Charts to a Custom Page | Up to 30 charts; copy from a worksheet; auto-refresh for charts only; linked charts on one worksheet |
| 23 | https://help.nocoly.com/custom-page/add-filter | Adding Filters to a Custom Page | One filter for several charts and views; same field type and option set; defaults from page parameters; Query button |
| 24 | https://help.nocoly.com/custom-page/add-view | Adding Views to a Custom Page | Embedded view of up to 100 rows with optional add, search, filter, drafts, import; linked to page filters |
| 25 | https://help.nocoly.com/custom-page/container | Containers: Tab/Card | Tab and card containers: names, order, borders, card or transparent mode |
| 26 | https://help.nocoly.com/custom-page/embed-url | Embed a URL in a Custom Page | https only; fixed or user-information parameters (no worksheet data); action bar |
| 27 | https://help.nocoly.com/custom-page/external-link | Adding External Links to a Custom Page | External Link page: embedded (https, iframe allowed) or new tab; language parameters; common errors |
| 28 | https://help.nocoly.com/custom-page/image-carousel | Adding Carousel to a Custom Page | Images from a file field with limits, text captions, click to open a record or link, or preview |
| 29 | https://help.nocoly.com/custom-page/introduction | Introduction to Custom Page | Components, page settings (theme, global colour, link parameters, layout, 30 s–5 min refresh, linked filtering), mobile, sharing |
| 30 | https://help.nocoly.com/custom-page/mobile-display | Display Custom Pages on the Mobile Home Screen | iOS 14+ and Android home-screen widgets for page charts and buttons |
| 31 | https://help.nocoly.com/custom-page/rich-text | Text, Image, and Section Components | Formatted text, one image with fit modes and click actions, section headings |
| 32 | https://help.nocoly.com/view/board | Kanban View | Grouping fields, which groups show, group order, unassigned and pinned columns, card settings, drag to regroup |
| 33 | https://help.nocoly.com/view/calendar | Calendar View | Start and end dates, several date groups, month/week/day, drag to reschedule, scheduling panel |
| 34 | https://help.nocoly.com/view/data-management | View - Data Management | Admin-only system view with every field editable and every button shown, bypassing rules |
| 35 | https://help.nocoly.com/view/details | Details View | Several records (cards + details) or one; collapsed sidebar; open a record by URL parameter |
| 36 | https://help.nocoly.com/view/gallery | Gallery View | Image-led card tiles; settings shared with Kanban and Table |
| 37 | https://help.nocoly.com/view/gantt | Gantt View | Start/end bars, milestones, grouping, precision, labels, drag, PNG export, unscheduled records |
| 38 | https://help.nocoly.com/view/grid | Table View | Shared view settings (filter, sort, colour, fields, refresh) plus table display, inline editing, columns, freeze, grouping, quick filter, filter list |
| 39 | https://help.nocoly.com/view/introduction | Introduction to Views | 10 view types, view components, admin-only configuration, visibility per platform |
| 40 | https://help.nocoly.com/view/link-parameter | Link Parameters in Views | URL parameters as filter values; supported field types and formats; empty or invalid values ignored |
| 41 | https://help.nocoly.com/view/map | Map View | Pins from a Positioning field (≤200), labels, colours, default centre |
| 42 | https://help.nocoly.com/view/operations | Operations on Views | Copy or apply configuration, change type, share, export, hide, reorder and search views |
| 43 | https://help.nocoly.com/view/org | Org View | Same-sheet or multi-sheet hierarchy, layouts, quick and bulk add (title only), 1,000 rows per level |
| 44 | https://help.nocoly.com/view/plugin | Custom View - Plugin | Code-built views published by an org admin; search, filter, statistics; JavaScript access to system components; permissions |
| 45 | https://help.nocoly.com/view/resource | Resources View | Resources × time bars; resource field types; ≤50 resources; year to day; drag to move or reassign |
| 46 | https://help.nocoly.com/view/split | Common View Design Patterns | Views by status, owner and information scope; avoid one view per growing value |
