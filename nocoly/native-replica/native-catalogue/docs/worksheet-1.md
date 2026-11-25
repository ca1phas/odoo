# Nocoly Help digest: Worksheet, part 1 of 2

- **Slice:** `read_pages.py --prefix worksheet --part 1/2`, 41 pages, `ai-suggestion` to `event` in alphabetical order. Part 2 (`excel-print-template` to `workflow-api-upload-file`) is `worksheet-2.md`.
- **Source:** help.nocoly.com, cached on 3 Nov 2026 in `knowledge-base/nocoly-mingdao/research/corpus.sqlite`. All 41 pages were read in full on 23 Nov 2026.
- **Missing from the cache:** screenshots. Anything a page shows only as an image (for example the table of reversible field-type conversions, or the API Query field-mapping rules) is not in this digest.
- **Labels:**
  - Everything in §2, and every line marked **[Docs]**, is what the cached help says. It is not runtime proof on Nocoly SaaS.
  - **[Inference]** is my own reading or design suggestion.
  - **[Memory]** is an earlier runtime observation on Nocoly SaaS recorded in the workspace memory (Nov 2026).
  - **[Plan]** is a statement from the programme files (`../../README.md`, `../../00-foundation.md`, `../../compute-for-ui.md`).
  - Neither [Memory] nor [Plan] is docs.
- **Editions and versions:** the help is translated from Mingdao and says "HAP". Few pages in this slice name an edition, SaaS versus Server, or a version. Where one does, the digest quotes it.

## 1. Summary

1. **Relations:** single and multiple relationship fields (two-way or one-way, cross-app, self-referencing Parent/Child) with filtered, searchable pickers, tree tables and mobile scan-to-link. They are the base for many2one, one2many, many2many and hierarchies.
2. **Document lines:** a subform backed by a real line worksheet gives editable lines: grid editing, Excel or paste import, "Select Product" bulk add, duplicate checks, at most 1,000 rows, and rights taken from the line sheet. Its rows are deleted with the parent.
3. **Onchange-style defaults:** a default can come from other fields, from the chosen related record (copied once, not kept in sync), from a worksheet query (which can also fill a subform, ≤500 rows), from a function, or from JavaScript that must finish within 1 second.
4. **Computed fields:** formula (number, date or function), rollup (≤1,000 rows, can lag), concat (titles), and foreign field (live display, or a stored copy synced to at most 1,000 rows).
5. **Form logic:** business rules (show/hide, read-only, required, set value, styling, block-or-warn validation with a server re-check, lock record; at most 100 per worksheet) and control events (on change or focus: set values, refresh fields, call a packaged business process or an API). Both run only in the record form.
6. **Numbering:** the autonumber field combines prefixes, dates, field values and a sequence that can reset daily, weekly, monthly or yearly. Numbers are given when a record is created, and after a reset they can repeat.
7. **Choice fields:** single and multi select support colours, numeric values for formulas, shared option sets, "Other" and a progress-bar display. Member, department and org-role fields can give people owner or member rights on the record.
8. **List actions:** in table view you can bulk edit, copy (20 at most), export, print, delete, lock and run custom actions on up to 1,000 rows. An admin's "Calibrate Data" recalculates up to 100,000 rows, once per 120 minutes per worksheet.
9. **Mobile and warehouse:** barcode and QR fields, bulk label printing, scan-first forms, scan-to-link relations, camera-only photos with GPS watermarks, OCR, and API lookups inside fields.
10. **Biggest gaps for Odoo [Inference]:** form logic doesn't guard imports, the API or workflows. There are no posting-time, gapless numbers, and a currency field's currency is set on the field, not per record. Nothing links to "any model", and the region, ID, OCR and uppercase features are built around China.

## 2. Capability inventory

All statements in this section are **[Docs]** (help.nocoly.com, cached 3 Nov 2026). Option names are written as the UI shows them, in quotes where the help quotes them.

### 2.1 Worksheet and form design

#### Create/Edit Worksheet
- **Does:** builds the form of a new or existing worksheet. You add fields by clicking or dragging a control, copy, move, delete and restore fields, set field properties and the form style, then save.
- **Options:**
  - **Title field:** hover a field and choose "Set as title". It identifies the record when relating records and in notifications.
  - **Field tools:** "Copy control", the delete icon, and restoring a deleted field.
  - **Record cover:** an image from a File field shown at the top of the record page, with animation and autoplay speed. Several images loop, multiple images or videos can show as thumbnails, and it works in the App and H5.
  - **Field layout:**
    - "Number of fields per line", 1 to 4, with Apply and Restore.
    - Field title shown vertical, horizontal or aligned right, set separately for PC and mobile.
  - **Section/Tab style:** one style for all sections and tabs.
  - **Further configuration:** Business Rule; Public Form, where external users submit without signing in.
- **Limits:**
  - **Fields:** at most 200 per worksheet; [Segment] and [Remarks] do not count.
  - **Record cover height:** 100 to 1000 px, default 600.
  - **Deleted fields:** one still used in a view filter or a workflow shows "The data field is deleted".
  - **Fields per line:** this setting only re-lays the form once. Admins can still drag fields and change widths, so rows can end up with a different count.
- **Source:** https://help.nocoly.com/worksheet/create-edit

#### AI Field Suggestions
- **Does:** in the form editor, "AI Field Suggestions" proposes fields from a description of the business object. You tick the ones you want and click "Add to Form", or refine the description and try again. Suggestions can be rated.
- **Limits:** none stated. A specific description, such as "fire safety equipment management", gives better suggestions.
- **Source:** https://help.nocoly.com/worksheet/ai-suggestion

#### Change Field Type
- **Does:** "Switch" (top right of a selected field in the form editor) converts the field to a similar type and keeps its data.
- **Options:**
  - **Reversible conversions:** listed only in a screenshot, which is not cached.
  - **One-way conversions:** for example, Concat → Text works, but Text cannot go back to Concat.
  - **Structured types:** Email, Telephone and ID number cannot be converted directly into each other. Convert to Text first.
- **Limits:** existing values that don't fit the new type stay on screen, but must be corrected before the record can be saved again.
- **Source:** https://help.nocoly.com/worksheet/change-field-type

#### Section and Tabs
- **Does:** these are layout containers. Sections stack groups of fields vertically and can collapse; tabs group fields horizontally.
- **Options:**
  - **Section:** text colour, icon and icon colour, and a default state of Expand, Collapse or Non-collapsible. "Form Style" sets one style for all sections, and only the first style allows an icon.
  - **Tab content:** a tab name and icon. You add fields by selecting them or dragging them in. A read-only tab makes all of its fields read-only.
  - **Tab position:** top, bottom or left of the page.
  - **Default tab:** with tabs at the top, fields not in any tab go into a default tab whose name and icon you can set, for example "Details".
  - **Tab display:** "Hide Tab Icon" and "Hide When Only One Tab". The editor can show tabs expanded or collapsed, but records always show them collapsed in a row.
- **Limits:** no numeric limits are stated.
- **Source:** https://help.nocoly.com/worksheet/control-section-tabs

#### Introduction to controls (the field-type catalogue)
- **Does:** lists the "40 types of controls", each with its own validation and settings. §2.2 is taken from this page. Controls that have their own page get their own entry below.
- **Source:** https://help.nocoly.com/worksheet/controls

### 2.2 Basic field types (from the controls page)

Source for this whole subsection: https://help.nocoly.com/worksheet/controls

- **Text:**
  - **Entry:** single-line, or multi-line with a minimum and maximum height. Markdown is supported.
  - **Checks:** a regular-expression format check, unique values, and a minimum and maximum character count.
  - **Other:**
    - a default value, and a width of 1/4, 1/3, 1/2 or the full row;
    - you can scan a barcode or QR code into the field, and links in the text can be clicked;
    - "Sort by Pinyin" adds a hidden pinyin field.
- **Number and Currency:**
  - **Both:** a unit as prefix or suffix, decimal places, a default, value limits and thousand separators.
  - **Number only:** percentage display, a progress-bar display and stepper input.
  - **Currency only:** a currency type and currency unit. The Uppercase control can be linked only to Currency fields.
  - **Limit:** 16 digits including decimals, with at most 14 before the decimal point. Longer integers are stored in scientific notation and may change. So long codes such as bank cards or business IDs belong in Text, and mobile numbers in Telephone.
- **Email:** only addresses of the form xxx@xx.xx can be saved.
- **Date:**
  - **Type and precision:** Date or Date & Time, shown as Year, Year-Month, Year-Month-Day, …Hour, …Hour:Minute or …Hour:Minute:Second.
  - **Time zone:** values are shown in the user time zone or in the application time zone.
  - **Restrictions:** allowed weekdays, a time range (for example 9:00–18:00), a time interval from 1 minute to 1 hour, and a start and end date.
  - **Other:** default values, and ISO, US, EU, Chinese or custom display formats.
  - **Write formats** for workflows, APIs, functions and imports:
    - accepted: `YYYY<year>MM<month>DD<day> HH:mm:ss` (with the Chinese characters for year, month and day), `YYYY-MM-DD HH:mm:ss`, `YYYY/MM/DD HH:mm:ss` and `MM/DD/YYYY HH:mm:ss`;
    - `DD/MM/YYYY` is not supported, and is read as `MM/DD/YYYY`;
    - `YYYYMMDD` saves an empty value or clears the existing one;
    - function defaults accept Year-Month-Day only;
    - leading zeros are optional, and an out-of-range part saves empty or clears the value.
- **Time:**
  - **Settings:** Hour:Minute or Hour:Minute:Second, a minute interval, and a start and end time.
  - **Import:** minutes or seconds above 59 become 59, hours above 23 become empty, and `24:00:00` is not supported.
- **Telephone:**
  - **Validation:** mobile or landline. To collect both kinds, add two fields.
  - **Country code:** a default code, or a list of allowed codes. New fields take the code set in Organization Settings.
  - **Workflows:** the value always includes the country code.
- **Check Item:**
  - **Display:** Checkbox, Switch or Yes/No, with a default value.
  - **Setting values:**
    - by function, for example `IF('Score'>60,TRUE(),FALSE())`;
    - by workflow or Excel import, with `true`/`1` or `false`/`0` taken from Text or Number values;
    - by API, with `1` or `0`.
- **Level:** stars, hearts or other icons, with a range of 1 to 10, a colour per level and a description per level shown on hover.
- **Rich Text:** formatted text and images, at most 5 per worksheet. It can be converted to Text, and then becomes multi-line text.
- **ID Number:**
  - **Validates:** the Chinese National ID card (18 digits only, residence permits for Hong Kong, Macao and Taiwan residents included), passports, and the Mainland Travel Permits for Hong Kong/Macao and for Taiwan residents.
  - **Other:** can be unique and required.
- **Signature:**
  - **Signing:** with a mouse on a PC, or by hand in the mobile app.
  - **Reuse:** a user's latest signature can be reused, and is shared across Signature fields and workflow approval signatures.
  - **Other:** it prints as an image and can be written by a workflow.
- **Positioning:**
  - **Capture:** location in the mobile app and on the web, with GPS on. It shows a map plus longitude and latitude, and the mobile app returns WGS84 coordinates.
  - **Maps:** the map provider can be chosen. AMap can show overseas maps, but HAP Server users must buy the overseas map service separately.
  - **Writing by workflow or API:** `{"x": "<longitude>", "y": "<latitude>", "title": "...", "address": "..."}`. title and address are optional.
- **Remark:** read-only rich-text instructions inside the form.
- **Free Link:** links a record to tasks, projects or calendar events. The link is one-way: the item cannot open the record.
- **Uppercase:** shows an amount "in uppercase", from a currency field, a rollup based on one, or a formula field.
- **Embed:** shows a Chart, a Link (a URL that can take other fields' values as parameters) or a View inside the form. It can also be a Gallery view's cover.

#### Date display formats
- **Does:** lists the tokens for custom date and time output.
- **Options:**
  - **In Autonumber fields:**
    - day and weekday: `d dd ddd dddd`;
    - hours: `h hh H HH`; minutes: `m mm`; seconds: `s ss`; AM/PM: `tt`;
    - months: `M MM MMM MMMM`;
    - years: `y yy yyy yyyy yyyyy`.
  - **In Date fields:**
    - years: `YY YYYY`; months: `M MM MMM MMMM`;
    - days: `D DD`; day of year: `DDD DDDD`;
    - weekday: `d dd ddd dddd`, and `E` as 1–7;
    - week of year: `w ww`; quarter: `Q`; AM/PM: `A`.
  - **Language:** `MMM`, `MMMM`, `ddd` and `dddd` follow the user's language. Add `#EN#` to force English: `YY-MMM-DD#EN#` gives 24-Jun-20.
- **Source:** https://help.nocoly.com/worksheet/date-format

### 2.3 Choice and organisation fields

#### Single Select / Multi Select
- **Does:** the user picks from predefined options. Options can carry colours and numeric values.
- **Options:**
  - **Display:**
    - "Dropdown", "Tiled Layout" (horizontal, vertical or matrix), or "Progress Bar" (single select only);
    - these combine with the field width.
  - **Where options come from:** the field itself, or an option set.
  - **Adding options:**
    - "+ Add Option", and X to delete one;
    - bulk add takes one option per line, ignores duplicates, and restores an option that is in the recycle bin.
  - **"Other" ("Show Other Option" in More Actions):**
    - can be renamed and always comes last;
    - gives a free-text input with hint text, and you filter such records by choosing "Other";
    - "Require additional input when "Other" is selected";
    - "Disallow selecting regular options when "Other" is selected" (multi select only).
  - **Managing options:**
    - "Copy All Options";
    - drag to reorder, or sort by pinyin;
    - "Allow Users to Add Options" (Dropdown mode only: type and press Enter);
    - deleted options can be viewed and restored, and colours turned on or off.
  - **"Assign Values to Options":**
    - the numbers can be used in formula fields, default values and workflow calculation nodes;
    - in calculation nodes this works for single select only, and never in function calculations;
    - sorting does not follow the values.
  - **Default:** fixed, or dynamic (other field values, query worksheet or function).
  - "Show all options in read-only mode" (tiled layout).
  - **Option sets:**
    - choose a set when adding the field;
    - converting custom options into a set makes later edits sync to every field that uses it;
    - converting a set back into custom options converts the history, and the field can't rejoin the original set;
    - you can hide some of a set's options in one field.
- **Limits:**
  - **Sorting:** views sort by a stored option index. After options are reordered or inserted, an app admin must run the bulk refresh, which is not possible for multi select.
  - **Values:** a changed option value doesn't reach existing records until they are refreshed.
  - **Switching type:** changing multi select to single select keeps existing multiple values, but editing then allows only one (controls page).
- **Source:** https://help.nocoly.com/worksheet/control-select

#### Members
- **Does:** picks users from Contacts. It can notify them and give them rights on the record.
- **Options:**
  - **Selection mode:** single or multi select, which can be switched after saving. Multi → single keeps the members already shown, but only one can stay when the record is edited. Drag to reorder.
  - **Member type:**
    - "General", or "External Portal" (this app's external users);
    - External Portal appears only when the app has an external portal;
    - the type is fixed once saved.
  - **Selection scope** (not for External Portal):
    - "User Contacts" or "Organization Contacts";
    - or "Custom Scope": departments (sub-departments included), organisation roles, or the record's other member, department and org-role fields, combined as a union.
  - **Permissions:** "As Member", "As Record Owner" or "None (Data only)".
  - **Default:** fixed users, the record creator (current user), or the members in other member fields.
  - **Other:**
    - notify selected members when they are added;
    - quick actions on an avatar: Remove, Replace, and Add to another member field.
- **Limits:**
  - **Access:** being a member or owner doesn't grant access by itself; roles decide.
  - **Type check:** the member-type check is not applied to imports, workflow writes or API writes.
  - **Older fields:** fields created before 1 Dec 2024 don't tell types apart until the option is turned on.
- **Source:** https://help.nocoly.com/worksheet/control-members

#### Department
- **Does:** picks organisation departments, and can fill in the current user's department.
- **Options:**
  - **Selection mode:** single or multi select, which can be switched; drag to order.
  - **Scope:**
    - "All";
    - "Specified Departments Only": a fixed department, a department field, or a member field, meaning those members' departments;
    - "Specified Departments and All Sub-departments";
    - "Sub-departments Only".
  - **Permissions:** "Member", "Owner" or "None (Data only)". The rights can go to:
    - the members of the selected department, optionally with all its sub-departments;
    - that department's managers, optionally with the managers of all its parent departments.
  - **Default:** a fixed department, another department field in this worksheet, or a department field in another worksheet. The controls page adds the record creator's department.
  - **Display:** "Show department path" and "Show deleted".
- **Limits:** as with Members, rights still depend on roles.
- **Source:** https://help.nocoly.com/worksheet/control-department

#### Org-roles
- **Does:** picks organisation roles, which are labels that cut across departments. It can fill in the current user's roles.
- **Options:**
  - **Selection mode:** single or multi select, which can be switched; drag to order.
  - **Scope:** "All", or "Specified Roles": fixed roles, the current user's roles, or other org-role fields.
  - **Permissions:** "As Member", "As Record Owner" or "Data only".
  - **Default:** a fixed role, a field in this worksheet, or a field in another worksheet.
- **Limits:**
  - **Defaults:** a single-select field that gets several roles as its default keeps only the first.
  - **Access:** rights still depend on roles.
- **Source:** https://help.nocoly.com/worksheet/control-o-roles

#### Region/City
- **Does:** a multi-level location picker, for filtering and charts.
- **Options:**
  - **Scope:** "Specified Region" or "Global".
  - **Levels in China:** Province, Province-City, or Province-City-District/County.
  - **Levels elsewhere:** two, State/Province and City/County.
  - **Required depth:** users must pick down to the configured last level.
- **Writes (Excel import, API, workflow):**
  - **Path:** the full path, with "/" between levels, matching the configured depth and the real hierarchy. Anything else is skipped.
  - **Country name:** Chinese values leave it out; Global values must start with it.
  - **Municipalities:** China's four municipalities use City/District.
- **Limits:**
  - **Charts:** "Administrative Division" charts work for China only.
  - **Separate parts:** province, city and district values that arrive separately (for example from a webhook) must first be joined in a workflow.
- **Source:** https://help.nocoly.com/worksheet/control-region-city

#### Cascading
- **Does:** lets the user choose step by step from a hierarchical worksheet.
- **Options:**
  - **Data source:** a worksheet with an org view that is related to the current worksheet. You can:
    - create a new one, named `DataSource-DateTime` and hidden from regular members' navigation;
    - or pick an existing sheet whose org view is linked to the current sheet.
  - **Selection and display:**
    - single or multi select, which can be switched;
    - "Cascading Menu" (levels side by side) or "Tree Selection" (levels stacked).
  - **Default:** other field values (another cascading field on the same source), or a query worksheet.
  - **Filter data source:** "All data", "Viewable data only" or "Filtered data".
  - **Selection range:**
    - start item: "All top-level", "Conditional items" or "Specified item";
    - end item: "Final level" or "Specified levels backward".
  - **Depth rule:** "Mandatory full-level selection", or "Arbitrary choice" with "Number of selected levels backwards".
  - **Path:**
    - "Display Hierarchical Path" shows A / B / C; without it only the last level shows;
    - "Store Hierarchical Path" can be used for hierarchical grouping in charts, but doesn't follow later renames until recalibrated.
  - **Search settings:** choose which fields can be searched.
- **Limits:** multi select allows at most 20 selections.
- **Source:** https://help.nocoly.com/worksheet/control-cascading

### 2.4 Relations and lines

#### Worksheet relationships (concepts)
- **Does:** explains the three relationship types, all modelled with relationship fields:
  - 1:1, usually better kept in one sheet;
  - 1:N, for example Customer → Orders;
  - N:N, for example Employees ↔ Tasks.
- **Source:** https://help.nocoly.com/worksheet/associations

#### Self-relationship (within one worksheet)
- **Does:** builds a hierarchy inside one worksheet, such as parent and sub-tasks or managers and their staff.
- **Options:**
  - **Setup:** relationship field → "New association" → "This application" → "This table".
  - **Fields created:** two, automatically: "Parent" (one record) and "Child" (multiple records).
  - **Field settings:** name, display type and display fields.
  - **Display:** an org view shows the hierarchy.
- **Source:** https://help.nocoly.com/worksheet/associate-current-form

#### Relationship
- **Does:** links records of another worksheet (in this app or another app) or of the same worksheet. It is a reference, not a copy.
- **Options:**
  - **Target:**
    - this app or another app, where you must be an admin or developer of the other app;
    - if the other sheet already has this relationship, you pick it from the existing ones;
    - two-way ("bidirectional": both sides stay in sync) or one-way.
  - **Relationship quantity:** "Single row" or "Multiple rows". The page insists on single row wherever the business allows, because it loads faster and keeps data consistent.
  - **Display, multiple rows:**
    - "Card", showing at most 200 linked records;
    - "Dropdown List", at most 50;
    - "Table" and "Tab table", no limit.
  - **Display, single row:** dropdown list, or a pop-up whose result shows as a card. In views, hovering a single-row card or dropdown relation shows a preview card.
  - **Shown fields:** a title field per relationship, and display fields (drag to order). "Show additional info and cover in the dropdown list" adds them to the dropdown.
  - **"Related Record Settings"** (only when "Select existing records" is on):
    - a filter on the records that can be chosen: AND/OR conditions with dynamic values;
    - when a dynamic value is empty: "No results for this condition", "Ignore this condition (return all records if all are ignored)", "Ignore this condition (return no results if all are ignored)" or "Query empty values";
    - the pop-up as a table with chosen fields, or as a list showing only titles (1,000 records loaded at a time); "Enable popup" opens it from the dropdown;
    - query settings: search fields (by default all text fields, exact or fuzzy), "Show selectable records only after search", and filter fields;
    - statistics on the chosen records (displayed fields only);
    - selection sort: the related worksheet's order, or a custom order on up to 5 fields.
  - **Sort related records:** "Sort by added time" (the default), "Sort by set order" or "Sort by the related view". Dragging is possible in card and dropdown mode, not in a table or tab table.
  - **Default value:** fixed records, another field's value (not in table mode), or a query worksheet (at most 500 records).
  - **Interaction:**
    - "Select existing records", limited to "All records" or "Only records with query permission", plus filters;
    - "Add new records" and "Unrelate records";
    - "Allow opening records", with a chosen view. The record opens only if the user can see it in that view. With no view set, it opens with the fields the user can see;
    - "Allow export" (the displayed fields, to Excel);
    - "Allow batch operations" (unrelate, edit, export, delete and so on, chosen in its settings);
    - "Show the record shortcut".
  - **Style:**
    - table "General" or "Transpose";
    - interaction "Classic", or "Grid" with Excel-like keyboard editing;
    - row height, and column widths: the widths an admin saves apply to everyone;
    - "Tree table", built on a parent field of the related sheet;
    - "Allow inline editing" and "Show alternate row colors".
  - **Advanced:**
    - query settings: one search field ("Only one field can be specified"), exact or fuzzy, and several filter fields;
    - "Related view": drives sorting, which records can be chosen, and the view used to open them. Settings under "Allow opening records" win. A link survives if the record later leaves the view;
    - "Filter the displayed results": by criteria, or with "Show by user permissions", which shows "X records are hidden";
    - "Show count": better turned off when display filters are on, because the count can differ from what is shown.
  - **Mobile:**
    - "Scan content" finds the record from a record-link QR code or from a chosen field value, such as the name;
    - "Disable manual input" means scanning only, on PC and mobile;
    - "Disable album";
    - "Scan before displaying the form" and "Submit the form after scanning", which also work in custom-button fill-ins.
  - **Operations:** create a new linked record, or relate an existing one. Unrelating does not delete the record. To show related records as columns, use a tab table.
- **Limits:**
  - **Card and dropdown ordering:**
    - by added time it holds up to 50 records; beyond that the order stays but dragging stops;
    - set order and related-view order are guaranteed for the first 5 records only.
  - **Display caps:** see the display options above.
  - **Summary row:** described on a separate page, outside this slice.
- **Source:** https://help.nocoly.com/worksheet/control-relationship

#### Subform
- **Does:** repeating rows inside a record, such as order lines or work experience.
- **Options:**
  - **Kinds:**
    - "Add from blank": a hidden worksheet that is not in the navigation and can only be reached through the parent;
    - "Use an existing sheet": a real worksheet. You only choose which fields show and in what order; fields can't be renamed or deleted from here.
  - **Adding rows:**
    - "Add a Row";
    - copying rows, if "Copy" is on. "Return Hidden Fields" (Advanced Settings; existing-sheet subforms and custom fields only) makes copies keep hidden values;
    - bulk add through a relationship field in the subform, with a "Select <relationship name>" button such as "Select Product".
  - **Importing rows:**
    - an Excel file (*.xls, *.xlsx or *.csv, at most 20 MB): you pick the sheet and the header row, then map each column or choose "Do not import this column";
    - pasted plain text (Ctrl/Cmd+V), split by colon, vertical line, comma or space; invalid values are dropped;
    - imported values win over field defaults.
  - **Duplicate checks:**
    - "Duplicate inputs are not allowed in this record": for chosen fields, within this record's subform;
    - "Duplicate inputs are not allowed globally": for existing-sheet subforms, by setting the line sheet's field to "No duplicate values". It is then checked against all records;
    - a relationship field with duplicate checking hides records already chosen from the picker.
  - **Row limits:** a minimum and a maximum number of rows. Setting both to the same number fixes the count.
  - **Switches:**
    - "Allow adding data" and "Edit existing data";
    - "Delete existing data" (new, unsaved rows can always be removed);
    - "Allow popup to open", "Allow batch operations" (edit, delete, copy) and "Allow Export";
    - read-only for the whole subform; per-field settings are in the subform's field configuration.
  - **"Access by user permissions"** (existing-sheet subforms):
    - record-level view, edit and delete rights, and field-level view and edit rights, come from the user's role on the line sheet;
    - without the right to add, every way of adding is hidden: single rows, import, and the relationship picker.
  - **Sorting:** sort rules apply when viewing saved records. New rows stay at the bottom until the record is saved.
  - **Style:**
    - "General" or "Transpose", and "Classic" or "Grid";
    - row height Compact, Middle, High or Extra; column width (drag, then save the record);
    - frozen columns, at most 10: a user's own, or an admin's for everyone;
    - a tree table (for an existing-sheet subform related to its own sheet);
    - paginated or scrolling display, and a maximum height;
    - up to 5 empty rows, "Show the sequence number", "Show count" and a summary row;
    - on mobile web, "List" or "Tile" (collapsible cards with chosen fields).
  - **Defaults:** static per field (for example pre-filled education stages), or dynamic from a query worksheet (at most 500 rows, with field mapping).
  - **Conversion:**
    - an "Add from blank" subform can be turned into a worksheet, which then appears in the navigation;
    - a converted subform can be switched to a relationship field and back.
- **Limits:**
  - **Rows:** at most 1,000 per subform. For the maximum height the page says "up to 200 rows maximum".
  - **Deletion:** deleting the parent deletes its subform rows.
  - **Standalone use:** rows can't be printed, shared or turned into tasks on their own.
  - **Filtering:** not possible in tree-table mode or while editing. While editing, new rows show at the top of a filtered list.
  - **Conversion:**
    - converting to a worksheet can't be undone, and leaves no relationship between the two sheets;
    - deleting the subform field afterwards keeps the new sheet and its data.
- **Source:** https://help.nocoly.com/worksheet/control-subform

#### Foreign Field
- **Does:** shows a field of the record linked through a single-row relationship field.
- **Options:**
  - **Setup:** a name, the relationship field (which must be "single record") and the target field.
  - **Type:**
    - "Display Only": read when a view or record loads and not stored. It can't be searched, filtered, sorted, aggregated, or used in formulas or concat;
    - "Store Data": a stored copy kept in sync. It supports all of those, and has a Pinyin sorting option.
- **Limits:**
  - **Sync:** not real time.
  - **Scale:** one change at the source updates at most 1,000 linked records. With 1,500 linked orders, 500 stay stale.
  - **Frozen values:** the page itself says that a value which must not change (a price at order time) should be a Currency field with a dynamic default, not a foreign field.
- **Source:** https://help.nocoly.com/worksheet/control-foreign

#### Query Records
- **Does:** shows matching records of another worksheet or an aggregated table, without a stored relationship. An example is showing a customer's orders when Orders → Customer is one-way.
- **Options:**
  - **Conditions:**
    - "Create query": for example the relationship Customer "is any of" the current record AND Status = Approved;
    - "Existing association": adds "Customer = Current record";
    - you choose what happens when a dynamic value is empty.
  - **Sorting**, and "Show single record" (the first by sort, as a card) or "Show multiple records" with a "Record limit".
  - **Display:** "Text" (the default, at most 50 records), "Card", "Table" (anywhere, or inside tabs) or "Tab table" (at the bottom, with the tabs).
  - **Actions:**
    - "Allow adding records" (a Create button);
    - "Allow opening records", with a view;
    - "Allow export", at most 10,000 records;
    - "Filter by user permissions", and a summary row.
  - **Table:** "General" or "Row-to-column transposition"; "Classic" or "Grid"; column visibility.
- **Limits:**
  - **Display only:** it stores nothing.
  - **Use elsewhere:** it can't be used for filtering or sorting in other places, nor as a condition or dynamic value.
  - **Control:** business rules and workflows can show it, hide it or make it read-only.
- **Source:** https://help.nocoly.com/worksheet/control-query-records

### 2.5 Calculated and generated fields

#### Formula
- **Does:** a calculated value that is recalculated whenever an input changes.
- **Options:**
  - **Number:**
    - an expression of fields, operators and built-in functions, which can be nested;
    - inputs: Number, Currency, Rollup, Formula (except "duration from now") and stored Foreign fields;
    - "Treat empty values as 0". Without it, one empty input makes the result empty.
  - **Date:**
    - **Duration between two dates:** Format 1 counts from start 00:00 to end 24:00, Format 2 from start 00:00 to end 00:00. Both apply only to dates without a time.
    - **Units and display:** the unit is year, month, day, hour, minute or second, with a "Display Unit" label. "Auto Conversion" turns 49 days into 1 month 19 days (not for years).
    - **Working days:** "Calculate Working Days Only" leaves out weekends.
    - **Add or subtract a duration:** `+1M`, `-1d`, `+1Y-1M+2d-3m` (Y, M, d, h, m), from a field or a fixed number. The output is a date or a date-time.
    - **"Duration from a date to now":** target − today, or today − target.
  - **Function:** the output can be text, number, date-time, date or time.
  - **Display:**
    - up to 14 decimal places, with Round up, Round down or Round half up;
    - "Trim trailing zeros": when on, the value also exports as a number; when off, as text;
    - thousand separators;
    - percentage (×100, which hides units);
    - units.
- **Limits:**
  - **Large worksheets:** above 100,000 records, changing the formula doesn't recalculate existing records. Use Bulk Refresh.
  - **"Duration from a date to now":** not stored, so it can't be used in other formulas, workflows or chart totals.
  - **Function formulas:** can't be inputs of other formulas.
- **Source:** https://help.nocoly.com/worksheet/control-formula

#### Rollup
- **Does:** totals the rows of a multiple-row relationship or of a subform.
- **Options:**
  - **What to total:** a multiple-row relationship, or a subform.
  - **Aggregation:**
    - Currency/Number: Sum, Max, Min or Average;
    - Date/Time: Earliest or Latest;
    - other types: a count of filled or empty values.
  - **Scope:** "Set up the filter", with conditions that are either all AND or all OR.
  - **Display:**
    - the raw value, or a percentage of the unfiltered total (for counts and number/currency sums);
    - decimals, separators, percentage and units.
- **Limits:**
  - **Rows:** at most 1,000 related records or subform rows. Only two things count them all: the field's refresh button in the record, and the workflow Calibrate node's "Calibrate Single Data".
  - **Filters:** no dynamic values, so "Date = Today" is not possible; use a chart instead.
  - **When it updates:**
    - at once when lines are edited inside the parent record, or by the refresh button, batch calibration, the Calibrate node, or a workflow that adds or removes links;
    - later, in the background, when lines are edited in their own worksheet or updated by a workflow.
  - **Workflows:** a workflow that needs the latest total should run the Calibrate node or use the Rollup node.
  - **Fit:** suited to about 100 rows that change rarely, not to large volumes that keep growing.
- **Source:** https://help.nocoly.com/worksheet/control-rollup

#### Concat
- **Does:** joins static text, fields and separators. It is often used as the title field.
- **Options:** "Parse Links" (on by default) and Pinyin sorting.
- **Limits:**
  - **Updating:** it updates itself only. It can't be edited by hand, imported, or written by a workflow.
  - **Titles with related data:** add the relationship field to the concat.
  - **Unique titles in workflow history:** add the creation time.
- **Source:** https://help.nocoly.com/worksheet/control-concat

#### Autonumber
- **Does:** generates a formatted record number, such as `HT0001` or `HT-2020-09-10-001`.
- **Options:**
  - **Parts:**
    - one sequence number (required);
    - any number of fixed characters and of referenced fields (Text, Option, Date or Region/City);
    - the creation time, in a preset or custom format.
    - Parts can be reordered.
  - **Sequence:**
    - "Natural number" or "Fixed-length number", and the digit length;
    - "Continue incrementing beyond digit length": 999 → 1000; otherwise back to 001;
    - the starting value, and "Use updated start value for the next record";
    - a reset cycle of Daily, Weekly, Monthly or Yearly.
  - **Other:** "Sort by Pinyin" and "Displayed in app time zone".
  - **Resetting:** "Reset Auto Number" in the worksheet's More menu. You can set "The number of the next record".
- **Limits:**
  - **Rule changes:** they apply to new records only, and empty numbers are not filled in.
  - **How a number is counted:** starting value − 1 + all records ever created, deleted ones included.
  - **Resets:**
    - can't be undone;
    - when a cycle is set, they affect only the current cycle;
    - can produce repeated numbers: "it may not always be unique".
  - **Renumbering existing records:**
    - by Excel import, with "Identify duplicate records" on Record ID and "Overwrite";
    - or by a button workflow whose Update Record node writes the Autonumber field.
- **Source:** https://help.nocoly.com/worksheet/control-autonumber

#### Barcode
- **Does:** shows a barcode or QR code in the record.
- **Options:**
  - **Type:** Barcode or QR Code.
  - **Source:** a field value (Record ID is offered first), or the record's internal access link.
  - **Size and error correction:** a maximum width. QR error correction is 7%, 15%, 25% or 30%.
  - **Existing records:** codes are generated for them once you save.
- **Limits:**
  - **Barcode content:** numbers, letters and symbols only; Chinese characters are ignored.
  - **QR content:** at most 150 characters from a field; the rest is cut. The record link is exempt.
  - **Source fields:** Text, Email, Telephone, Concat, Autonumber, or a Foreign field showing one of those.
  - **Cards:** it can't be a display field on Kanban, Gallery or related-record cards, only their cover.
  - **Tables:** it can't show in multi-row related tables.
- **Source:** https://help.nocoly.com/worksheet/control-barcode

### 2.6 Default values and functions

#### Function Calculation
- **Does:** Excel-like functions in five groups: Math, Text, Date, Logical and Advanced. They work in formula fields, in field default values and in workflow calculation nodes.
- **Options:** select a field, then "Dynamic Default Value" → "Function Calculation". Pick functions and fields from the left panel, or type them. "Test" checks the formula with typed values or an existing record.
- **Rules:**
  - **Fields that take a function default:** only Text, Number, Currency, Date, Email and Phone.
  - **Allowed parameters:**
    - Text, Number, Currency, Email, Phone and Date;
    - Single/Multi select, Member, Department, Check item, Region/City and ID number;
    - Subform, Relationship, and stored Foreign fields.
  - **Not allowed as parameters:** Concat, Autonumber, Rich text, Cascading, File, Uppercase and Signature.
  - **Syntax:**
    - Typed function names are in uppercase, and fields are picked from the panel.
    - The result type must match the field: DATENOW() in a Number field is ignored.
    - Operators: `+ - * / > == < >= <= !=` (compare with `==`), typed as English symbols.
  - **Parameters:**
    - Static text and dates go in quotes; fields and nested functions do not.
    - Build dynamic text with CONCAT. For example, the Monday of a date's week is `DATEADD(Date, CONCAT('-', WEEKDAY(Date)-1, 'd'), 1)`.
- **Source:** https://help.nocoly.com/worksheet/default-function

#### Default value from other fields
- **Does:** "Dynamic Default Value" → "Other field values" builds a default from fields of the current form, or from a field of the chosen related record. The default follows those fields while the record is being created or edited, and stays editable.
- **Options:**
  - **From the current form:** Text can combine several fields with fixed text; Date, Phone and similar types take one field.
  - **From the related record:** for example Account Executive = the chosen Customer's Account Owner, or an order line's Unit Price = the chosen Product's price (Order → Order Details is 1:N, Order Details → Product is N:1).
- **Limits:**
  - **Physical worksheets only:** related-record defaults work only for physical worksheets. "Default values in empty subforms do not support selecting fields from related records".
  - **No sync:** unlike a foreign field, the saved value doesn't follow later changes at the source. The page recommends this to freeze prices and owners.
- **Source:** https://help.nocoly.com/worksheet/default-other-field-value

#### Default value from a worksheet query
- **Does:** fills a standard, relationship or subform field from records that match conditions.
- **Options:**
  - **Query:** the worksheet to query, plus conditions. Relationship fields need only the conditions.
  - **When several records match:** take the "first matched record", set the field empty, or keep the original value.
  - **When none match:** set it empty, or keep the original value.
  - **Empty dynamic values:** how to handle them is configurable.
  - **Subforms and table relationships:** at most 500 records (50 in card mode), with field mapping.
- **Limits:** subforms can't use the "Other field values" method.
- **Examples in the docs:**
  - the bank account from the employee's last expense claim;
  - linking the contact whose phone number matches;
  - loading inspection items from a template sheet into a subform.
- **Source:** https://help.nocoly.com/worksheet/default-query-worksheet

#### Custom Functions
- **Does:** JavaScript for default values ("Function Calculation" → "Custom Function").
- **Options:** variables receive field values (pick the field after `=`), and `return` gives the result. `SYSTEM_URL_PARAMS.<name>` reads a URL query parameter, for example on a public form, or from a view's URL when a record is created there.
- **Limits:**
  - **Result:** one value only.
  - **Running:** it runs in the background in a separate thread and is stopped after 1 second.
  - **Where:** field default values only. Workflow calculation nodes can't use it; use a code block node there.
  - **URL parameters:** work in browsers, not in the mobile app.
- **Source:** https://help.nocoly.com/worksheet/custom-functions

### 2.7 Form behaviour

#### Business Rule
- **Does:** condition → action rules that apply when records are created, edited or viewed.
- **Options:**
  - **Where:** [Edit Form] > [Form Settings] > [Business Rule], for app admins. Rules can be viewed, edited, deleted, copied, sorted, enabled and disabled.
  - **Conditions:** field + operator + value, against a "Fixed value" or another "Field value". Conditions can be combined.
  - **Field interaction:**
    - Show / Hide, Read-only / Editable, Required, Set field value;
    - Set all fields to read-only. It takes effect after the record is saved, and custom actions and workflows can still write.
  - **Field styling:**
    - the title's colour, bold, italic, underline, strikethrough and size;
    - the value's colour, style and size;
    - also available per field in its "Style" panel.
  - **Field validation:**
    - an alert message, which can show on chosen fields;
    - "Real-time prompts when entering fields";
    - "Re-validate when saving data to server": checks again against database values, for example stock that others changed meanwhile;
    - block the save (red message) or allow saving with a warning (yellow message).
  - **Lock record:** applies after a save (create or edit) when the conditions match. The record shows the lock description, which also appears on records an admin locked by hand.
- **Logic:**
  - **Show and Hide:** strict opposites. When the condition fails the opposite is forced, so no reverse rule is needed.
  - **Editable, Required, Read-only:** apply only while the condition holds and the field is visible. Otherwise the field falls back to its own setting. "Read-only all fields" does nothing when its condition fails.
  - **Several rules on one field:** merged in the order Hide > Show > Read-only > Required > Editable. The same order merges field settings, business rules, views, role permissions, and workflows or custom buttons.
  - **Two Show rules on one field:** for example Lead Source = Ad and Lead Source = Email, written as separate rules. The field stays hidden, because the failing rule forces Hide. Use one rule with OR.
  - **"Hide when Create":** always wins when a record is created.
  - **"Read-only All Fields":** applies only when working in the worksheet. Custom buttons can still edit, and so can records opened from workflow Fill-in, Approval or Send Internal Notification nodes.
  - **Views:**
    - in table view, Hide becomes Read-only and Required is not enforced;
    - in table view and org view (tree table), only Read-only and Editable run;
    - in other views, rules don't run;
    - on the detail page, rules run as long as their condition fields exist.
  - **Error prompts and hidden fields:**
    - a condition on a single hidden field raises no error;
    - A > B still runs if one of A and B is visible, and is ignored if both are hidden;
    - in an OR, only the part whose fields are hidden is dropped.
- **Limits:**
  - **Number of rules:** at most 100 enabled at once.
  - **Lock conditions:** only on single select, multi select and check item fields.
  - **Changing a lock rule:** existing records are not re-checked; it applies at their next save.
- **Source:** https://help.nocoly.com/worksheet/business-rule

#### Control Events
- **Does:** field-level event handlers on the record detail page, whether the record is new ("Create Record") or opened.
- **Options:**
  - **Where:** form editor → field → "Event" → "+ Event". "Add Condition" adds more condition-and-action groups.
  - **Events:** "When Field is Shown / Hidden", "When Field Gains / Loses Focus", "When Value Changes" and "When Value Changes and Loses Focus".
  - **Which events each kind of control supports:**
    - **Input** (Text, typed Number, Currency, Email, Phone, Rich text, ID number): show, hide, focus, blur, and change plus blur, but not change alone.
    - **Action** (Number as progress or stepper, Date, Time, File, Check item, Level, Positioning, Signature): show, hide and change.
    - **Read-only** (Formula, Auto-number, OCR, button API Query, Barcode, Uppercase, Embed, Query records, Foreign field, Rollup, Free link, Section, Tab, Remark): show and hide only.
    - **Selection** (Region/City, Single and Multi select, Member, Department, Organization role, dropdown API Query): show, hide and change.
    - **Relationship** (Relationship, Subform, Cascading): show, hide and change.
  - **Actions:**
    - Show / Hide and Set Read-only / Editable: temporary, unlike business rules;
    - Set Field Value (or clear it), and Refresh Field Value (formula, rollup, concat and so on);
    - Call Packaged Business Process and Call Integrated API, mapping the results into fields;
    - Show Message, Play Sound and Activate Tab.
  - **Conditions:** "Based on Field Values", "Based on Query Worksheet" or "Based on Custom Function" (JavaScript that returns true). Groups are tried in order until one matches.
- **Logic:**
  - **Order:** actions run top to bottom.
  - **On load:** each visible field fires On Show, in layout order.
  - **Business-rule effects:** visibility changes made by business rules fire On Show or On Hide.
  - **Field settings:** events can override a field's own hidden or read-only setting.
  - **With business rules on the same field:** events run first, then the rules apply (Hidden > Visible; Read-only > Required > Editable).
- **Limits:**
  - **Where they don't run:** in views (bulk edit included), on import, and on records created by workflows.
  - **Empty read-only fields:** they don't fire On Show.
- **Source:** https://help.nocoly.com/worksheet/event

#### Edit Lock
- **Does:** while one user edits a record on its detail page ("Modifying form data..."), others can only read it until that user saves or the lock times out.
- **Options:**
  - **Where:** [Edit Form] > [More Settings] > [Edit Lock].
  - **Protection period:** 5 to 30 minutes, with an optional "Show countdown before timeout".
  - **After timeout:**
    - "Keep editing when records unchanged": only if nobody else is editing and the record hasn't changed;
    - or "Disable further editing".
- **Limits:**
  - **Not covered:** workflow and API writes, inline editing, public forms, and custom actions (Fill in).
  - **What it blocks:** other users' edits through detail pages, custom actions (Fill in) and interface pushes (Fill in).
  - **Devices:** the lock holder can edit on several devices.
- **Source:** https://help.nocoly.com/worksheet/edit-lock

### 2.8 Files, integrations and code-based fields

#### File
- **Does:** attaches files (documents, images and so on) to a record.
- **Options:**
  - **Display:** "Thumbnail", "Card", "List" or "Poster" (images only). "Display the file name in the cell" adds the name in table view.
  - **File types:** .exe, .vbs, .bat, .com, .cmd and .url are always blocked. You can also set a custom list of allowed types; extensions ignore case.
  - **Sorting:** "Newest first", "Oldest first" or "Custom order" (drag). Switching back from custom order keeps the existing order.
  - **File names:** can be checked with a regular expression. A Text field whose default is a File field gets the uploaded file names.
  - **"Scan to Upload":** scan a QR code to upload from a phone. Also available for signature fields and record discussions.
  - **Rights while editing:**
    - "Allow Upload", plus "Take Photo on PC";
    - "Allow Delete" (new, unsaved files can always be removed);
    - "Allow Download": the field setting wins over the function switch, which wins over user permissions. "Download All" is limited to 200 MB in total.
  - **Image watermark:**
    - fixed text, field values (text, email or telephone), the current user, and the date as yyyyMMdd; at most 100 characters;
    - added on preview and on download or export;
    - for jpeg, png, tiff, bmp and heic.
  - **Online editing (WPS):**
    - "Edit" in the preview; "Actions > Save Version", Ctrl/Cmd+S or closing the editor saves;
    - saving updates the field, logs the change and can trigger workflows; no WPS account is needed;
    - formats: doc and docx family (rtf and txt preview only), xls and xlsx family (csv preview only), ppt and pptx family, pdf and ofd;
    - needs "Online Document Editing" on; "Only edit self-uploaded attachments" is optional;
    - the field must be editable.
  - **Mobile:**
    - "Auto Compression", "Disable Input from Desktop" and "Disable Album";
    - "Add Watermark to Photos": field values, user name, location, capture time and GPS;
    - "Act before Input": the camera opens first;
    - "Submit After Capture".
- **Limits:**
  - **Uploads:** at most 100 files at a time. Each field takes 1 to 100 files, and the per-file size limit can be set from 0.01 MB to 4 GB.
  - **Watermarks:** images of at most 20 MB, and not documents.
  - **Online editing:**
    - files of at most 100 MB, and at most 10 people at the same time;
    - only inside the app, external portals included: not from discussions, posts, the knowledge base or public shares;
    - best in Chrome 80 or later.
- **Source:** https://help.nocoly.com/worksheet/control-file

#### OCR
- **Does:** reads text, invoices or ID cards from files into fields.
- **Options:**
  - **API type:**
    - "System Preset": 0.15 credits per call, taken from the organisation's balance;
    - "Integration Center": your own or a third party's API, which must be authorised for the app. No platform fee is charged.
  - **Where results go:** the current record (no batch upload), or a subform (batch upload). You map fields, and can keep the original image in an attachment field.
  - **Mobile:** "Disable album".
- **Limits:**
  - **File types:** ID cards and general text are read from images only. Invoices are read from images or PDFs, and only a PDF's first page is read.
  - **Invoice lines:** must go to a subform, not a relationship field.
  - **Tax rates:** if one shows 0, set the field to 2 decimal places.
- **Source:** https://help.nocoly.com/worksheet/control-ocr

#### API Query
- **Does:** while a record is created or edited, it calls an integrated API or a packaged business process. The results fill fields or subforms; it can also push data out.
- **Options:**
  - **Source:** a pre-integrated API or a packaged business process. Only APIs authorised for the app are listed.
  - **Display mode:**
    - **"Button":** a single-row result fills fields. A multi-row result goes to a subform, and the search keyword is typed in another field.
    - **"Dropdown List" and "Searchable Dropdown List":** for multi-row responses only. The chosen row fills normal fields, not a subform.
  - **Searchable dropdown settings:**
    - search method "Button-Triggered" or "Real-Time" (real time makes more API calls and costs more);
    - a minimum character length;
    - "Make a request before searching": sends an empty search when opened. Use it only if the API accepts that;
    - the typed text is passed as the parameter.
  - **Mapping:** results are mapped to fields. The rules are only in a screenshot.
- **Limits:** the docs' examples (Tianyancha company data, phone-number location) are Chinese services.
- **Source:** https://help.nocoly.com/worksheet/control-api-query

#### Custom Fields
- **Does:** a field drawn by React and Tailwind CSS code, written by AI or by hand.
- **Options:**
  - **Kind:** "Store Field Value", or "Reference Other Field Values Only".
  - **Editor:**
    - Chat Panel;
    - Online Code Editor, with Run and Console;
    - Live Preview;
    - Referenced Fields, read in code as `formData[env.<fieldVariableName>]`;
    - Mock Data: load a record, and simulate mobile and read-only.
  - **Read-only state:** `env.isDisabled`.
  - **Finishing:** "Exit AI-assisted Development", then save the form.
- **Limits:**
  - **Libraries:** third-party libraries are not supported.
  - **Fields per sheet:** this page states no limit. [Plan] `compute-for-ui.md` gives 5 per worksheet, from Mingdao V12.1.
  - **Examples:** a random-number widget (Number), a colour picker (Text, `#XXXXXX`), a capsule date picker (Date) and a digital clock (Time).
- **Source:** https://help.nocoly.com/worksheet/control-custom-fields

### 2.9 Record operations and printing

#### Batch Operations on Records
- **Does:** bulk actions in table view, which an app admin must first enable ("Batch Operation", with the users and views it applies to).
- **Options:**
  - **Selecting:** single records, a Shift range, the current page, all records in the view, or invert the selection.
  - **Actions:**
    - Bulk Edit (Update Fields), Bulk Copy, Bulk Export and Bulk Print;
    - Bulk Delete and Bulk Lock/Unlock;
    - Bulk Execute Custom Actions;
    - also Bulk Export Attachments, and Bulk Refresh Data (admins).
- **Limits:**
  - **Selection:**
    - with more than 1,000 records selected, only the first 1,000 are processed;
    - unticking one record after "select all" leaves only the current page selected.
  - **Bulk Edit:**
    - several fields at once, set or cleared; required fields and the owner can't be cleared;
    - read-only fields can't be edited, and multi select can't get new options;
    - no undo.
  - **Delete:**
    - other users: up to 1,000 records, to the Recycle Bin;
    - app admins: can permanently delete every selected record. Those records can't be restored and no workflows run.
    - Links in other sheets show "Deleted".
  - **Copy:** at most 20 records.
  - **Print:**
    - Word or Excel templates, or QR codes and barcodes;
    - one line says record data can be bulk-printed with Word templates only.
  - **Custom actions:**
    - with one record selected, the button shows only if its condition is met;
    - with several selected, it always shows, and records that fail the condition are skipped.
  - **Admins only:** refresh, lock and unlock.
- **Source:** https://help.nocoly.com/worksheet/batch-operations

#### Batch Printing
- **Does:** prints several records with a template, from table view.
- **Options:**
  - **System template:** each record on a new page, in one Word file.
  - **Excel template:** each record on its own sheet.
  - **Word template:** turn on "Page Break Before" so each record starts a new page.
- **Limits:**
  - **Current page only:** template printing across pages is not supported, so the page size sets the maximum.
  - **Conditions:** records that don't meet the template's conditions are not printed.
- **Source:** https://help.nocoly.com/worksheet/batch-print

#### Bluetooth Print
- **Does:** prints one record's QR code on a thermal Bluetooth printer from the Android app.
- **Options:** set up a QR code print template first. Then long-press the record (or use the menu at the top right of the record), choose [Print/Export], pick the template, set the printing options and connect the printer.
- **Limits:** Android only, QR codes only, one record at a time.
- **Source:** https://help.nocoly.com/worksheet/bluetooth-print

#### Bulk Refresh Data ("Calibrate Data")
- **Does:** brings existing records up to date after configuration changes. In table view, select records ("Select All" works), then More > Calibrate Data. App admins only.
- **Options:**
  - **Refresh Calculations:** formula, rollup, concat and foreign fields. These recalculate automatically below 100,000 records, and need a manual run above that.
  - **Update Option Set Result:** realigns stored option indexes after reordering (not for multi select), and applies changed option values; formulas then recalculate.
  - **Update Encrypted Field Values.**
  - **Update Foreign Fields and Rollup Results.**
  - **Update Relationships:** removes links that are no longer valid, for example to deleted records. Field values are not changed.
- **Limits:**
  - **Interval:** after a refresh, wait 120 minutes before refreshing the same worksheet again.
  - **Size:** at most 100,000 records per run. If more are selected, the 100,000 earliest by creation time are processed.
- **Source:** https://help.nocoly.com/worksheet/batch-refresh

#### Basic Operations for Records (index)
- **Does:** an index page with no content of its own. It links to Single Record, Filter and Sort (1 page), Bulk Record Actions (1), Import/Export Data (5) and Print Records (3).
- **Source:** https://help.nocoly.com/worksheet/data-operations

### 2.10 Security and platform limits

#### Field Encryption
- **Does:** stores sensitive field values as ciphertext and decrypts them for display according to the rule.
- **Options:**
  - **Rules:** an organisation super admin defines encryption rules in the Organization Admin Console.
  - **Fields:** then "Data Encryption" is turned on with a rule, on Text (single line), Phone/Landline, Email or ID number fields.
  - **Plain values:** exports, the API and data sync return plain values.
- **Limits:**
  - **Existing values:**
    - only new values are encrypted. Existing ones need "Update Encrypted Field Values";
    - until then they can be viewed but not filtered.
  - **Searching:** no search in worksheet or super search, and no fuzzy search in relationship search.
  - **Filters:** quick filters do exact match only. The only filter operators are Equals, Not equals, Is empty and Is not empty.
- **Source:** https://help.nocoly.com/worksheet/data-encryption

#### Platform storage and attachment upload traffic
- **Does:** describes how attachment upload traffic is metered.
- **Options:**
  - **Storage:** not charged.
  - **Uploads that don't count:** Chat, Feed, Tasks, Calendar and Files.
  - **Uploads that count:** application attachment uploads (attachment fields, worksheet discussions, record discussions). The organisation shares one yearly quota.
- **Limits:**
  - **Yearly quota:** Free 1 GB, Standard 60 GB, Enterprise 120 GB.
  - **Extra traffic:** paid editions can buy more at USD 50 per 10 GB per year; Free can't.
  - **Year:** a calendar year, reset on 1 January.
  - **Re-uploads:** every upload counts, so deleting a file and uploading it again counts twice.
- **Source:** https://help.nocoly.com/worksheet/data-storage

## 3. Odoo rebuild notes

The "Fit" column says how well the native feature covers the Odoo concept:
- **Good:** native covers it.
- **Partial:** native covers the main case; the rest needs a workflow, a custom field or Compute.
- **Gap:** no native equivalent in this slice.
- **Unknown:** must be tested live.

Tags as in the header. Odoo names refer to Odoo 20.0 Community.

### 3.1 Fields and widgets

| Odoo | Native HAP (this slice) | Fit | Falls short / notes |
|---|---|---|---|
| `Char` (name, reference, VAT) | Text: regex check, unique values, min/max length, scan input | Good | VAT checksum or VIES checks are not native [Inference]. HAP uniqueness may only check values a user types [Plan, from September `BUILDING.md`] |
| `Text`, `Html` | Multi-line Text (Markdown); Rich Text | Good | At most 5 Rich Text fields per worksheet [Docs] |
| `Integer`, `Float` (quantities, weights) | Number: decimals, units, stepper, progress bar, percentage | Good | 16 digits, 14 before the point [Docs]. Leading zeros are lost, so codes go in Text [Inference] |
| `Monetary` + `currency_id` | Currency field (currency type and unit) | Partial | The currency is chosen in the field settings. A per-record currency (Odoo's order or pricelist currency) is not described → a Currency relation plus Number/formula, or one field per currency [Inference] |
| `Boolean` | Check Item: Checkbox, Switch or Yes/No | Good | Written as 1/0 by API, as true/1 or false/0 by import or workflow [Docs] |
| `Selection` | Single Select with colours and numeric values; option sets | Good | No technical keys, so workflows and imports match on labels [Inference]. Reordering or changing values needs Calibrate Data [Docs] |
| `statusbar` widget (state, stage) | Single Select "Progress Bar" display | Partial | Whether clicking a step changes the value is not stated [Inference → §5]. Per-team stages or folding need a Stages sheet [Inference] |
| `priority` stars | Level (1–10 icons, colours, hover text) | Good | |
| `many2many_tags` with colours | Multi Select with colours; an option set to share across sheets; "Allow Users to Add Options" to create on the fly | Good | Tags with a parent or extra fields (Odoo `res.partner.category`) → a relationship to a Tags sheet; a dropdown shows at most 50 linked records [Docs + Inference] |
| `radio`, `many2many_checkboxes` widgets | Select "Tiled Layout" (horizontal, vertical, matrix) | Good | |
| `Date`, `Datetime` (user time zone) | Date: Date or Date & Time; user or app time zone; weekday, time-range and date limits | Good | Written values: DD/MM/YYYY is read as MM/DD/YYYY, and YYYYMMDD clears the field [Docs] |
| `float_time` (durations) | Number with a unit; formula date durations | Partial | The Time control stores a clock time, not a duration [Inference] |
| `Binary`, `Image`, attachments | File (at most 100 files per field and 4 GB each; type and name rules; watermarks; WPS editing); record cover | Good | Yearly upload traffic per organisation (Free 1 GB, Standard 60 GB, Enterprise 120 GB) [Docs] |
| `phone`, `email`, `url` widgets | Telephone (country codes), Email, Text with link parsing | Good | In workflows the phone value always includes the country code (+60…) [Docs] |
| Online signature on quotations | Signature field | Good | The latest signature is reused across fields and approvals [Docs] |
| `partner_latitude`, `partner_longitude` | Positioning (WGS84 in the mobile app; choice of map provider) | Good | |
| Address with `state_id` and `country_id` | Region/City (Global: two levels outside China) | Partial | No ISO or state codes, no postcode, and division charts for China only → keep the foundation's Countries and States sheets; use Region/City at most as an extra analytics field [Inference] |
| `amount_to_text` (amount in words) | Uppercase | Unknown | The wording suggests Chinese capital-amount numerals; English output is not stated [Inference → §5] |
| `barcode` and product labels | Text (scan input) + Barcode/QR field + bulk QR/barcode printing | Good | Barcodes can hold letters, numbers and symbols only; QR codes at most 150 characters [Docs] |
| `display_name`, `_rec_name` | Title field; a Concat field as title | Good | A concat can't be written by workflow or import [Docs] |
| `fields.Properties` | none | Gap | Custom field or Compute [Plan] |

### 3.2 Form and list layout

| Odoo | Native HAP | Fit | Notes |
|---|---|---|---|
| `<notebook>` pages | Tabs (top, bottom or left; default tab; icons) | Good | A read-only tab makes all its fields read-only [Docs] |
| `<group>`, `<separator>` | Section (collapsible; colour and icon) | Good | |
| Help texts and banners | Remark control | Good | |
| List row decorations (`decoration-danger`) | Business-rule field styling (colour and style of a field's title or value) | Partial | Styling is per field, not per row; whether list rows can be coloured is not covered here [Inference] |
| Form header image | Record cover from a File field | Good | |
| Status badges | Option colours | Good | |

### 3.3 Relations and structure

| Odoo | Native HAP | Fit | Notes |
|---|---|---|---|
| `Many2one` with `domain` | Relationship "Single row" + a filter on selectable records with dynamic values and an empty-value strategy | Good | |
| `name_search` (find a product by code or barcode) | Related Record Settings → search fields (exact or fuzzy), filter fields, "Show selectable records only after search" | Good | The Advanced settings section says only one search field [Docs conflict C3] |
| `One2many` | Relationship "Multiple rows" as Table or Tab table; Subform; Query Records | Good | Card shows at most 200 linked records, dropdown 50 [Docs] |
| `Many2many` | Two-way multiple relationship (N:N) | Good | |
| `parent_id` / `child_ids` (categories, company ↔ contacts, locations, tasks) | Self-relationship (Parent and Child created automatically) + org view + tree-table display; Cascading to pick a node and show its path | Good | Preventing circular parents is not native → selection filter plus validation [Inference]. A stored hierarchical path doesn't follow renames [Docs] |
| `related=` fields | Foreign Field: "Display Only" (live) or "Store Data" | Good / Partial | Stored copies sync to at most 1,000 records, with delay; display-only can't be filtered, sorted or totalled [Docs]. Could show a company's VAT on its people without a copy workflow, if no search is needed [Inference] |
| Smart buttons (count + filtered list) | Query Records (tab table, summary row, Create button, export); a rollup count; an embedded view | Good | Query Records stores nothing and can't be filtered on [Docs] |
| `Reference`, `res_model` + `res_id` (activities, attachments, messages) | none: Free Link only reaches tasks, projects and calendar events | Gap | One typed relationship per target sheet [Plan, decision 3] |
| `ondelete='cascade'` (order → lines) | Subform rows are deleted with the parent | Good for subforms | In a relationship table, the linked records stay and show "Deleted" [Docs]; clean them up in a workflow [Inference] |
| `ondelete='restrict'` | not in this slice | Gap? | Check in a workflow or business rule [Inference] |
| References across modules (Sales ↔ Inventory) | Relationship to a worksheet in another app (requires admin or developer rights there) | Partial | Cross-app links make it harder to prune customer copies [Inference]; the programme already keeps one master app [Plan] |

### 3.4 Computation and onchange

| Odoo | Native HAP | Fit | Notes |
|---|---|---|---|
| Stored `@api.depends` computes (line subtotal, margin) | Formula (number, date, function); Concat | Good | Above 100,000 records, changing the config needs Bulk Refresh; function formulas can't feed other formulas [Docs] |
| Order totals (`amount_untaxed`, `amount_tax`, `amount_total`) | Rollup of line subtotals + Formula | Partial | At most 1,000 lines. Totals lag when lines change outside the order form, so workflows must calibrate first [Docs] |
| Tax totals per rate | A rollup with a fixed filter per rate [Inference] | Partial | Filters can't use dynamic values [Docs]; a tax-table lookup needs a workflow [Inference] |
| `@api.onchange`: product → price, unit, description; customer → salesperson, pricelist, terms | "Other field values" default from the related record (copied once); control events "When Value Changes" → Set Field Value, Refresh Field Value, Call Packaged Business Process or Call Integrated API; business rule "Set field value" | Good in the form | Events don't run on import, on workflow-created records, or in list edits [Docs]. Related-record defaults need physical sheets [Docs] |
| Pricelist price (`_compute_price_rule`) | A "Query Worksheet" default against a Pricelist Rules sheet, for simple fixed prices; or a control event calling a packaged business process ("Price for product") [Inference] | Partial | Which record counts as the "first matched record" is not documented [§5]. Complex rules stay in the workflow sub-process [Plan] |
| `default_get`, context defaults | Fixed, other-field, query-worksheet, function and JavaScript defaults; `SYSTEM_URL_PARAMS` when creating from a link (browser only) | Good | Custom functions stop after 1 second [Docs] |
| Due dates (payment terms, validity, deadlines) | Formula add/subtract (`+30d`, `+1M`); DATEADD | Good | End-of-month rules: see the system-functions page in `worksheet-2.md` |
| "Late by N days", activity state | Formula "Duration from a date to now" | Partial | Not stored, so not usable in workflows or charts [Docs]. A stored state needs a scheduled workflow [Plan, foundation row 14] |
| Working-day durations (`resource.calendar`) | Formula "Calculate Working Days Only" | Partial | Leaves out weekends only; holidays are not mentioned [Docs] |
| Unit-of-measure chains, recursive computes | none (no recursive formulas) | Gap | Workflow [Plan] |
| Hierarchical full name ("All / Saleable") | Cascading "Display Hierarchical Path" on fields that pick a category | Partial | Shown only on the picking field, not on the category record [Inference]. The category's own full name stays a workflow [Plan] |

### 3.5 Constraints, states and locking

| Odoo | Native HAP | Fit | Notes |
|---|---|---|---|
| `@api.constrains`, SQL unique constraints | Business-rule validation (block in red or warn in yellow; server re-check); Text unique values; subform duplicate checks | Partial | Works in the form only; imports, the API and workflows are probably not checked [Inference → §5]. Validation is skipped when its fields are hidden [Docs] |
| View modifiers (`invisible`, `readonly`, `required` expressions) | Business rules: Show/Hide, Read-only/Editable, Required | Good | Weakened in table view, and not run in kanban or other views; merge order applies [Docs] |
| Read-only after confirming or posting; the "Lock" button on sales orders | "Lock record" rule on a status select or check item; "Set all fields to read-only"; admin Bulk Lock/Unlock | Partial | Workflows and custom actions can still write [Docs]. Bulk unlock is for admins only [Docs] |
| Concurrent-edit protection | Edit Lock (5–30 minutes) | Partial | Doesn't cover workflows, the API, inline edits, public forms or Fill-in actions [Docs] |
| Stock availability check before delivery | Rule "Outbound quantity > Inventory" with "Re-validate when saving data to server" (the docs' own example) | Partial | Not atomic when two people save at once [Inference]; ledger writes stay in workflows [Plan] |
| Required depending on the stage | Business rule Required, with the stage as condition | Partial | Not enforced in table view [Docs] |

### 3.6 Sequences (`ir.sequence`)

| Odoo | Native HAP | Fit | Notes |
|---|---|---|---|
| Numbers given on creation (S00001, P00001, WH/OUT/00001) | Autonumber: fixed characters + creation-time tokens (`yyyy`) + fixed-length sequence + yearly reset; referenced fields (Text, Option, Date, Region/City) | Good | One counter per field. Separate counters per warehouse, operation type or company would need one sheet per type, or a workflow counter [Inference] |
| Invoice and bill numbers given at posting, without gaps (`sequence.mixin`) | none | Gap | Autonumber numbers records on creation, counts deleted ones, and can repeat after a reset [Docs]. → A workflow gives a Text number at posting from a counter sheet [Inference] |
| Lot and serial numbers | Autonumber on the Lots sheet, or typed in with "No duplicate values" | Good | |

### 3.7 Document lines (`sale.order.line`, `purchase.order.line`, `account.move.line`, `stock.move`)

| Odoo | Native HAP | Fit | Notes |
|---|---|---|---|
| Editable list of lines | A subform on an existing Order Lines sheet ("Use an existing sheet"): Grid mode, "Select Product" bulk add, Excel/paste import, duplicate checks, minimum and maximum rows, summary row, "Access by user permissions" | Good | At most 1,000 rows; rows can't be printed on their own [Docs] |
| Why a physical sheet, not "Add from blank" | Product-price defaults need a physical sheet [Docs]; lines can then be reported on and charted, and get role permissions [Inference] | — | |
| Line ordering (`sequence` with a drag handle) | Subform sort rules on a Sequence field | Partial | Drag ordering is only documented for relationship cards and dropdowns, at most 50 [Docs] |
| Section and note lines (`display_type`) | none | Gap | A Line Type select plus business rules that hide the numeric fields [Inference] |
| Lines from a template (quotation templates, BoM components, checklists) | Subform default by Query Worksheet (at most 500 rows, with field mapping) | Good | Possibly only when a record is created [Inference → §5] |

### 3.8 Lists, import, export and printing

| Odoo | Native HAP | Fit | Notes |
|---|---|---|---|
| Editing many records in a list | Bulk Edit | Good | At most 1,000 records, no undo; limits on read-only, required and owner fields [Docs] |
| Duplicate (`copy`) | Bulk Copy | Partial | At most 20 records [Docs]. Whether subform rows are copied is not stated [Inference → §5] |
| Server actions on a selection | Bulk Execute Custom Actions | Good | Records that fail the button's condition are skipped [Docs] |
| Archive (`active`) | no archive action among the bulk actions | Gap | An "Active" check item plus view filters, set with Bulk Edit [Inference] |
| Delete | Bulk Delete (to the Recycle Bin) | Good | An admin's permanent delete runs no workflows and leaves "Deleted" links [Docs] |
| Import that updates by external ID | Excel import with "Identify duplicate records" on Record ID, and "Overwrite" | Good | The import pages are in `worksheet-2.md` |
| QWeb PDF reports | Word, Excel or system print templates | Partial | Batch printing covers the current page only; Word needs "Page Break Before"; Excel puts each record on its own sheet [Docs] |
| Product, lot and location labels | Bulk QR/barcode printing; Bluetooth thermal QR printing on Android | Partial | Bluetooth printing is QR only, one record at a time [Docs] |
| Recomputing stored fields | Calibrate Data | Good | Admins only; at most 100,000 records; 120 minutes between runs per sheet [Docs] |

### 3.9 Users, teams and security

| Odoo | Native HAP | Fit | Notes |
|---|---|---|---|
| `user_id` (salesperson, responsible) | Member field (General) with "As Record Owner"; default the record creator; notify | Good | Access is still decided by roles [Docs] |
| Portal users | Member type "External Portal" | Good | The type check is skipped for imports, workflows and the API [Docs] |
| Sales teams (`crm.team`) and team leaders | A Department field (whose managers can get rights), or a Teams worksheet [Inference] | Partial | Departments come from the HAP organisation chart, while Odoo teams are business data → a Teams sheet, unless teams are the departments [Inference] |
| Followers (`message_follower_ids`) | Member field "As Member" + "Notify selected members" | Partial | Notifies only when someone is added [Docs]; no subscription types [Inference] |
| Sensitive fields | Field Encryption (Text, Phone, Email, ID number) | Partial | Encrypted fields can't be searched, and filters are limited [Docs]. Field visibility by role is in the role docs |

### 3.10 Mobile, warehouse and documents

| Odoo | Native HAP | Fit | Notes |
|---|---|---|---|
| Barcode app (Enterprise) | Relationship "Scan content" on a barcode field; "Disable manual input"; "Scan before displaying the form"; "Submit the form after scanning"; scan input on Text fields | Good | Scanning works in the mobile app [Docs]. One scan makes one link, so quantities need a workflow or repeated scans [Inference] |
| Photos as proof of delivery | File: "Act before Input", "Submit After Capture", "Disable Album", photo watermark (user, location, time, GPS) | Good | |
| Bill digitisation (Enterprise, IAP) | OCR invoice recognition (system preset at 0.15 credits per call), or OCR through the Integration Center | Unknown | The preset is probably made for Chinese invoices; invoice lines must go to a subform [Docs + Inference] |
| Partner autocomplete (IAP) | API Query searchable dropdown on an Integration Center API | Partial | Needs a Malaysian company-data API; the docs use Tianyancha, a Chinese service [Inference] |
| Live exchange rates | API Query (button), or a control event "Call Integrated API" | Partial | Started by a user in the form; a scheduled refresh is a workflow, outside this slice [Inference] |
| Editing attachments online | File online editing (WPS) | Unknown | Availability on Nocoly SaaS is not stated [Inference → §5] |

### 3.11 Not in this slice

These are covered by other digests: chatter (record discussion and field logs), activities, roles and record rules, views (kanban, Gantt, org view), workflows (Calibrate and Rollup nodes, code block), custom buttons, print-template design, Excel import, public forms, summary rows, the title field, time zones and the function list.

## 4. Traps

### Form logic
1. **[Docs]** Two separate Show rules on one field keep it hidden, because the failing rule forces Hide. Put the conditions in one rule with OR. **[Memory]** This happened on Nocoly SaaS on 20 Nov 2026 (an earlier POC app). The rules read back correctly; only the rendered form showed the problem.
2. **[Docs]** A validation is skipped silently when its condition fields are hidden, whether by rules, roles or field settings. If a role hides "Inventory", the stock check is off for that role. **[Inference]** Make such fields read-only instead of hidden.
3. **[Docs]** Table view turns Hide into Read-only, and Required is not enforced there. Kanban, gallery and the other views run no rules at all, so editing inline in a list escapes required checks.
4. **[Docs]** "Set all fields to read-only", "Lock record" and Edit Lock don't stop workflows, custom actions (Fill in), or approval and fill-in nodes. **[Inference]** That suits system postings. For true immutability, the workflows must also refuse to write.
5. **[Docs]** The business-rule page says "To fully lock a record, use Edit Lock". But Edit Lock is only a 5–30-minute lock against concurrent editing, and it ignores workflows, the API, inline edits, public forms and Fill-in actions. For locks by status, use "Lock record".
6. **[Docs]** "Lock record" conditions accept only single select, multi select and check item fields. The lock applies after saving, and changing the rule doesn't re-check existing records. **[Inference]** Model Odoo states as a single select.
7. **[Docs]** Control events run only on the record detail page: not in list views (bulk edit included), not on import, and not on records created by workflows. **[Inference]** Any onchange logic that API, import or point-of-sale paths need must also exist in a workflow.
8. **[Docs]** "Hide when Create" beats every Show rule while a record is being created.
9. **[Docs]** Control events run before business rules. Events can override a field's own settings, but the rules still decide in the order Hidden > Visible and Read-only > Required > Editable.
10. **[Docs]** At most 100 business rules can be enabled per worksheet.

### Computed fields
11. **[Docs]** A rollup counts at most 1,000 rows. It lags when lines are changed in their own sheet or by a workflow. A workflow that reads an order total right after changing lines can get the old total → run the Calibrate node or the Rollup node first.
12. **[Docs]** A rollup's filter can't use dynamic values: no "Date = Today", and no comparison with a field of the current record.
13. **[Docs]** A stored foreign field syncs to at most 1,000 linked records, and not in real time. **[Memory]** On Nocoly (23 Nov 2026), list reads showed a stored foreign field as empty for minutes after a calibration, while a single-record read already had the value. Check one record, not a list.
14. **[Docs]** A display-only foreign field can't be searched, filtered, sorted, totalled, or used in formulas or concat.
15. **[Docs]** Above 100,000 records, changing a formula, rollup, concat or foreign field doesn't recalculate existing records.
    - Calibrate Data handles at most 100,000 records per run, once per 120 minutes per worksheet. **[Memory]** Confirmed as a 2-hour limit on Nocoly on 23 Nov 2026.
    - Tick every affected field in one run.
16. **[Docs]** "Duration from a date to now" is not stored. Function-type formulas can't feed other formulas. "Treat empty values as 0" is off by default, so one empty input blanks the result.
17. **[Docs]** A concat can't be edited, imported or written by a workflow, and can't be a function parameter.
18. **[Docs]** Changing an option's value or order doesn't update existing records until an admin runs Calibrate Data. The order refresh is not possible for multi select.
19. **[Docs]** Option values work in formulas and defaults. In workflow calculation nodes they work for single select only, and never in function calculations.

### Numbering
20. **[Docs]** Autonumber:
    - a rule change applies only to new records;
    - deleted records still use up numbers;
    - "Reset Auto Number" can't be undone and can produce duplicates;
    - numbers are given when the record is created.

    **[Inference]** So it can't serve as Odoo's posting-time invoice numbering.
21. **[Docs]** Changing the starting value doesn't restart the count: the number is start − 1 + every record ever created. To restart, use Reset with "The number of the next record".
22. **[Docs]** Autonumber date tokens are in .NET style (`yyyy`, `dd`, `MM`); Date field tokens are in moment style (`YYYY`, `DD`). **[Inference]** A format copied from one to the other gives wrong output.

### Data formats, imports and writes
23. **[Docs]** For dates written by import, the API, a workflow or a function:
    - `DD/MM/YYYY` is read as `MM/DD/YYYY`, so 13/01/2026 fails and 03/01/2026 becomes 1 March;
    - `YYYYMMDD` empties or clears the field.

    **[Inference]** Convert Malaysian data to `YYYY-MM-DD` before writing it.
24. **[Docs]** When times are imported, hours above 23 become empty, minutes above 59 become 59, and `24:00:00` is invalid.
25. **[Docs]** Numbers with more than 16 digits are stored in scientific notation. **[Inference]** EAN/UPC barcodes, IC numbers, bank accounts and any code with leading zeros must be Text fields.
26. **[Docs]** A Region/City value is skipped unless it is a full path matching the configured depth. For Global fields the path must start with the country name.
27. **[Docs]** The member-type check is not applied to imports, workflow writes or API writes. **[Inference]** Expect the same of other form-only checks.
28. **[Docs]** In workflows, phone values always include the country code. **[Inference]** Normalise numbers before matching or deduplicating on them.
29. **[Plan]** HAP's "No duplicate values" only checks values a user types (from September's `BUILDING.md`). These docs don't say so.

### Lines and relations
30. **[Docs]** Defaults from a related record (a price from the product) need physical worksheets; "Add from blank" subforms can't use them.
31. **[Docs]** A subform holds at most 1,000 rows, and a dynamic default loads at most 500. Deleting the parent deletes the rows, and subform rows can't be printed on their own.
32. **[Docs]** Converting an "Add from blank" subform into a worksheet is one-way, and leaves no relationship between the two sheets.
33. **[Docs]** Relationship display caps: a dropdown shows at most 50 linked records and a card 200. In card and dropdown mode, "set order" and "related view" sorting are guaranteed for the first 5 records only.
34. **[Docs]** After a deletion, links in other sheets show "Deleted"; for example after an admin's permanent bulk delete. "Update Relationships" in Calibrate Data removes such invalid links.
35. **[Docs]** A foreign field needs a single-row relationship. A relationship to a worksheet in another app needs admin or developer rights on that app.
36. **[Docs]** Query Records stores nothing: it can't be filtered or sorted on, nor used as a condition or dynamic value.
37. **[Docs]** A relationship's "Show count" can differ from the records shown when display filters or permission filters are on.

### Bulk and admin operations
38. **[Docs]** Bulk actions process only the first 1,000 selected records. Unticking one record after "select all" leaves only the current page selected. Bulk edits can't be undone.
39. **[Docs]** An app admin's bulk delete is permanent (no Recycle Bin) and runs no workflows. **[Inference]** Never use it on documents whose deletion must reverse stock or accounting entries.
40. **[Docs]** Bulk Copy handles at most 20 records. Batch printing covers the current page only, and records that fail the template's conditions are skipped without notice.
41. **[Docs]** With several records selected, a custom action's button always shows, and records that fail its condition are skipped. The docs mention no error message.

### Files and platform
42. **[Docs]** Attachment upload traffic has a yearly cap per organisation, by calendar year: Free 1 GB, Standard 60 GB, Enterprise 120 GB; extra traffic costs USD 50 per 10 GB per year. Re-uploads count again. **[Inference]** Mobile flows with many photos (proof of delivery) need "Auto Compression" and an estimate of the volume.
43. **[Docs]** File limits:
    - "Download All": at most 200 MB;
    - watermarks: images of at most 20 MB only;
    - WPS editing: files of at most 100 MB, at most 10 people at once, and only inside the app.
44. **[Docs]** Encrypted fields can't be searched, and their filters are limited to Equals, Not equals, Is empty and Is not empty. Existing values must be refreshed, and export and API return plain text.
45. **[Docs]** Custom functions stop after 1 second and only run for default values. `SYSTEM_URL_PARAMS` doesn't work in the mobile app.
46. **[Docs]** At most 5 Rich Text fields and 200 fields per worksheet.
47. **[Memory]** A Date field shown with Year-Month precision (`showtype` 4) displays only the month, and Gantt views built on such fields break (Nocoly, 19 Nov 2026).
48. **[Docs]** Change Field Type can't convert Email, Telephone and ID number into each other directly, and Concat → Text is one-way.

### Conflicts between doc pages (settle them live, §5)
- **C1:** `default-function` limits function defaults to Text, Number, Currency, Date, Email and Phone. But `controls` (Check Item) and `control-select` show function defaults for check items and selects.
- **C2:** bulk record printing is "Word/Excel templates" (batch-operations notes, batch-print), but "Word templates only" in batch-operations §7.
- **C3:** relationship search fields: several can be set (Related Record Settings), yet "Only one field can be specified" (Advanced settings).
- **C4:** Autonumber is a "unique sequential number" (controls) but "may not always be unique" (autonumber).
- **C5:** Edit Lock is recommended as a full lock (business-rule), but its own page limits it to concurrent editing on the detail page (edit-lock).
- **C6:** Uppercase "can only be associated with Currency fields" (controls, Number/Currency section), yet the Uppercase section also lists rollup and formula sources.
- **C7:** Rollup works on a relationship or a subform (intro), yet "Only relationship fields (multiple related records) … can be selected" (step B).

## 5. To verify live (Nocoly SaaS)

| # | Doc claim | Why it matters for the build | Suggested test | Priority |
|---|---|---|---|---|
| 1 | A related-record default (Unit Price from Product) works in a subform on a physical sheet, but not in an "Add from blank" subform | Design of order lines | Build Orders with a subform on an existing Order Lines sheet. Pick a product, change the product's price, and check that the old line keeps its price. Repeat with an "Add from blank" subform | High |
| 2 | "Other field values" defaults follow their source fields while a record is edited | Could overwrite prices typed by hand on existing orders | On an existing order line, type a price by hand, then change the product, then the quantity. Watch whether the price resets | High |
| 3 | Control events can call a packaged business process and map its results | Live pricelist price and unit conversion in the form | Event on Product change → packaged process "Price for product" → set Unit Price, inside a subform row. Measure the delay | High |
| 4 | Events don't run on import, list edits or workflow-created records. What about business-rule validation for API and workflow writes? | Decides where constraints must live | Break a blocking rule through API v3, through a workflow and through an import. Edit inline in table view with a Required rule | High |
| 5 | Rollup: at most 1,000 rows; delayed when lines change in their own sheet or by workflow | Order totals used in workflows | Change a line in its own sheet and through a workflow. Read the order total at once and after N seconds. Test the Calibrate node | High |
| 6 | `DD/MM/YYYY` is read as `MM/DD/YYYY`, and `YYYYMMDD` clears the field | Importing Malaysian data | Write 03/01/2026, 13/01/2026 and 20260103 into Date fields by Excel import and by API | High |
| 7 | Autonumber parts and yearly reset; deleted records use up numbers; a workflow can write the field | Numbers for sales orders, purchase orders and transfers | Create `S-{yyyy}-{00000}` with a yearly reset. Delete a record and check for the gap. Write the field from a workflow Update Record node | High |
| 8 | "Lock record" still lets workflows and custom actions write; unlocking is for admins | Keeping posted documents unchanged | Lock on Status = Posted. Try to edit as a user, through a custom action and through a workflow. Try to unlock | High |
| 9 | A Currency field's currency is set per field | Documents in several currencies | Look at the currency setting; check whether it can follow another field, and whether MYR and SGD are available | Med |
| 10 | Output language of Uppercase | Malaysian invoices ("Ringgit Malaysia … only") | Add Uppercase on an RM amount, with the UI in English | Med |
| 11 | Region/City Global gives two levels for Malaysia, and writes start with the country name | Address model | Pick Malaysia; check its states and cities. Write "Malaysia/Selangor/Petaling Jaya" by API | Med |
| 12 | Telephone default code (+60) and validation | Contacts | Enter 012-3456789 and 03-12345678 | Med |
| 13 | Relationship "Scan content" finds a product by its barcode field on mobile | Warehouse receipts and picking | In the Nocoly mobile app, scan an EAN-13 into a Product relationship; try "Disable manual input" | Med |
| 14 | Whether business-rule conditions (styling, validation) can compare a date with "today" | Activity status colours without a custom field | Rule: Due Date earlier than Today → red. Check whether "Today" is offered | Med |
| 15 | Which record a Query Worksheet default takes as "first matched record" | Choosing pricelist rules | Make two matching rules and see which one wins; look for a sort option | Med |
| 16 | Custom fields: available on Nocoly? This page states no per-sheet limit, the plan says 5 | Foundation pilots (colour picker, status badge) | Add custom fields to a test sheet until one is refused | Med |
| 17 | Bulk Copy: are subform rows copied? (not stated) | Duplicating a quotation | Copy an order that has lines | Med |
| 18 | Can a "Progress Bar" select be clicked to change its value? | Status-bar experience | Click a step in record view | Med |
| 19 | Function defaults on Check Item and Select (conflict C1) | Defaults for flags such as "is a company" | Set a function default on a check item and on a select | Low |
| 20 | Batch printing with an Excel template (conflict C2) | Printing invoices in bulk | Batch-print with an Excel template | Low |
| 21 | Subform: at most 1,000 rows and 20 MB Excel files; dynamic defaults at most 500 rows | Large orders and bills of materials | Import 1,001 rows | Low |
| 22 | Stored foreign field: at most 1,000 records synced, with delay | Related fields on large master data | Change a contact linked to more than 1,000 orders; count the updated ones | Low |
| 23 | OCR invoice recognition on Malaysian (MyInvois) invoices, at 0.15 credits per call | Vendor bills | Upload a sample invoice | Low |
| 24 | WPS online editing is available on Nocoly SaaS | Editing documents | Open a .docx in a File field | Low |
| 25 | "Calculate Working Days Only" ignores public holidays | Lead times and service levels | Calculate a period that includes a holiday | Low |
| 26 | Our organisation's edition and its attachment traffic quota | Flows with many photos | Check usage in Organization Management | Low |

## 6. Coverage

All 41 pages of the slice were read. Every one is listed here.

| # | URL | Title | One-line summary |
|---|---|---|---|
| 0 | https://help.nocoly.com/worksheet/ai-suggestion | AI Field Suggestions | AI proposes fields from a description in the form editor; tick them and "Add to Form". |
| 1 | https://help.nocoly.com/worksheet/associate-current-form | Link Records Within the Same Worksheet | A self-relationship creates Parent (single) and Child (multiple) fields; an org view shows the tree. |
| 2 | https://help.nocoly.com/worksheet/associations | Worksheet Relationships | 1:1, 1:N and N:N relationships with examples, and when to use each. |
| 3 | https://help.nocoly.com/worksheet/batch-operations | Batch Operations on Records | Bulk edit, copy, export, print, delete, lock and custom actions in table view; 1,000-record cap, copy 20, admin permanent delete. |
| 4 | https://help.nocoly.com/worksheet/batch-print | Batch Printing | Template printing of the current page's records; page breaks per template type. |
| 5 | https://help.nocoly.com/worksheet/batch-refresh | Bulk Refresh Data | Admin "Calibrate Data" for calculations, options, encryption, foreign fields, rollups and relationships; at most 100,000 rows, then a 120-minute wait. |
| 6 | https://help.nocoly.com/worksheet/bluetooth-print | Bluetooth Print | Prints one record's QR code on a thermal Bluetooth printer from Android. |
| 7 | https://help.nocoly.com/worksheet/business-rule | Business Rule | Conditions → show/hide, read-only, required, set value, styling, validation and lock; how rules combine, view limits, at most 100 rules. |
| 8 | https://help.nocoly.com/worksheet/change-field-type | Change Field Type | "Switch" converts a field's type and keeps its data; some conversions are one-way; Email, Phone and ID convert via Text. |
| 9 | https://help.nocoly.com/worksheet/control-api-query | Control - API Query | A field that calls an integrated API or packaged process, as a button or (searchable) dropdown, and maps results to fields or a subform. |
| 10 | https://help.nocoly.com/worksheet/control-autonumber | Autonumber Field | Number parts, sequence options, reset cycles, manual reset, and renumbering existing records. |
| 11 | https://help.nocoly.com/worksheet/control-barcode | Control - Barcode | A barcode or QR code from a field or the record link; content limits; can't show on cards. |
| 12 | https://help.nocoly.com/worksheet/control-cascading | Control - Cascading | Step-by-step picker on an org-view worksheet: ranges, depth, showing and storing the path; multi select at most 20. |
| 13 | https://help.nocoly.com/worksheet/control-concat | Control - Concat | Joins text and fields, often as the title; can't be imported or written by workflow. |
| 14 | https://help.nocoly.com/worksheet/control-custom-fields | Custom Fields | A React/Tailwind field built with AI, stored or reference-only; the editor's parts; no third-party libraries. |
| 15 | https://help.nocoly.com/worksheet/control-department | Control - Department | Department picker: scopes, rights incl. for department managers, defaults, path display. |
| 16 | https://help.nocoly.com/worksheet/control-file | Control - File | Attachments: display, type, size and name rules, rights, watermarks, WPS editing, mobile capture. |
| 17 | https://help.nocoly.com/worksheet/control-foreign | Control - Foreign Field | Display-only or stored values from a single-row relationship; syncs to at most 1,000 records; use defaults to freeze values. |
| 18 | https://help.nocoly.com/worksheet/control-formula | Control - Formula | Number, date and function formulas; rounding and display; the 100,000-record and "now" limits. |
| 19 | https://help.nocoly.com/worksheet/control-members | Control - Members | User picker: General or External Portal, scope, owner and member rights, defaults, notifications. |
| 20 | https://help.nocoly.com/worksheet/control-o-roles | Control - Org-roles | Organisation-role picker: scope, rights, defaults. |
| 21 | https://help.nocoly.com/worksheet/control-ocr | Control - OCR | Reads IDs, text and invoices through the preset service (0.15 credits) or an Integration Center API, into fields or a subform. |
| 22 | https://help.nocoly.com/worksheet/control-query-records | Control - Query Records | Display-only list of another sheet's records by condition; display types, create, open, export; can't be filtered on. |
| 23 | https://help.nocoly.com/worksheet/control-region-city | Control - Region/City | Region picker (3 levels in China, 2 elsewhere); write formats; division charts for China only. |
| 24 | https://help.nocoly.com/worksheet/control-relationship | Control - Relationship | All relationship settings: quantity, display modes and caps, selection filters and search, sorting, defaults, interaction, styles, mobile scanning. |
| 25 | https://help.nocoly.com/worksheet/control-rollup | Control - Rollup | Totals over relationships or subforms; at most 1,000 rows; immediate versus delayed updates; fixed filters only. |
| 26 | https://help.nocoly.com/worksheet/control-section-tabs | Control - Section and Tabs | Section and tab containers: default states, tab positions, styles. |
| 27 | https://help.nocoly.com/worksheet/control-select | Control - Single Select/Multi Select | Options, "Other", colours, values, option sets, display modes, options added by users, sort refresh. |
| 28 | https://help.nocoly.com/worksheet/control-subform | Control - Subform | Blank or existing-sheet subforms: adding and importing rows, duplicate checks, limits, rights, styles, defaults, conversion. |
| 29 | https://help.nocoly.com/worksheet/controls | Introduction to controls | Catalogue of the 40 controls, with settings and write formats (dates, times, check items, positions). |
| 30 | https://help.nocoly.com/worksheet/create-edit | Create/Edit Worksheet | Adding and editing fields, title field, record cover, layout; at most 200 fields. |
| 31 | https://help.nocoly.com/worksheet/custom-functions | Custom Functions | JavaScript default-value functions, the 1-second limit, URL parameters. |
| 32 | https://help.nocoly.com/worksheet/data-encryption | Field Encryption | Rule-based encryption of fields, and its limits on search and filters. |
| 33 | https://help.nocoly.com/worksheet/data-operations | Basic Operations for Records | Index page linking to the record, filter, bulk, import/export and print topics. |
| 34 | https://help.nocoly.com/worksheet/data-storage | Platform Storage and Attachment Upload Traffic | Yearly upload-traffic quotas per organisation by edition; storage itself is free. |
| 35 | https://help.nocoly.com/worksheet/date-format | Custom Date and Time Display Formats | Format tokens for autonumber and date fields; the `#EN#` suffix. |
| 36 | https://help.nocoly.com/worksheet/default-function | Function Calculation | Function defaults: which fields and parameters, syntax rules, testing. |
| 37 | https://help.nocoly.com/worksheet/default-other-field-value | Default Value Method 1 — Other Field Values | Defaults from current fields or the chosen related record, copied once; physical sheets only. |
| 38 | https://help.nocoly.com/worksheet/default-query-worksheet | Default Value Method 2 — Query Worksheet | Defaults from a worksheet query for fields, relationships and subforms (at most 500 rows). |
| 39 | https://help.nocoly.com/worksheet/edit-lock | Edit Lock | A temporary one-editor lock on the detail page (5–30 minutes), and what it doesn't cover. |
| 40 | https://help.nocoly.com/worksheet/event | Control Events | Field events and their actions (set value, refresh, call a packaged process or API, message, sound, tab); detail page only; order with business rules. |
