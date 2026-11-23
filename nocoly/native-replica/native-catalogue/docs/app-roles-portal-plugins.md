# Native HAP features: applications, roles, external portal and plugins

| | |
|---|---|
| Slice | `--prefix application,role,portal,plugin,extensions`: 44 pages of help.nocoly.com, cached 3 Nov 2026 in `knowledge-base/nocoly-mingdao/research/corpus.sqlite` |
| Written | 23 Nov 2026, for the Odoo 20 rebuild in Odoo Replica (AI) on Nocoly SaaS (`../BRIEF.md`) |
| Status | Docs digest only. Read-only: no app, role, portal, plugin or setting was opened or changed |
| Evidence | Untagged statements in §1, §2 and §4 are **docs (cached 3 Nov 2026), not runtime proof**. **[Inference]** = my own reasoning. **[X-ref]** = a cached help page outside this slice, read only to settle a conflict or a plan limit. **[Ours]** = findings from our own Nocoly builds in Nov 2026 (memory notes), not docs |
| Doc quality | Several pages still carry Mingdao-era content: RMB prices, WeChat Pay/Alipay, "Ultimate Edition", a `mingdao.com` sender address. Nocoly's plans are Free / Standard / Professional ([X-ref] `purchase/version-comparison`). Treat prices and plan names on these pages as unconfirmed for Nocoly |

## 1. Summary

1. **Packaging is per app:** Duplicate copies configuration only; Export writes a `.mdy` (≤20 apps, records optional and capped, optional import password and configuration lock); Import creates an app or upgrades a *source-related* one (**Merge and Update** / **Overwrite and Update**, never selective).
2. **Keep each sellable edition inside one app:** relations to other apps turn into text on export unless those apps are in the same package, and Duplicate drops them. This backs the one-master-app decision.
3. **[Inference] Upgrading a pruned customer copy from the full master adds the pruned items back** (an upgrade adds every item the target lacks), so each edition needs its own pruned package per release.
4. **Localization (paid editions):** UI, config labels, option sets and workflow names, by hand or AI Smart Translation; full system UI in English, Malay and Simplified Chinese. **Record data is never translated.**
5. **Roles:** Administrator/App Owner, Developer, Operator, custom roles. Advanced mode: visible items → View/Edit/Delete per view (Add per sheet) → record scope All / Joined / Owned (+ subordinates) → field visibility/editability and action switches. Multiple roles merge by union per view.
6. **Record-rule equivalents:** system Owner; Member/Department/Org Role fields granting Owner or Member rights; Joined; Org Chart subordinates; extended-information permission tags (team or company scoping).
7. **External portal** fits Odoo's customer and vendor portals (registration, invitation, approval with an auto-approve list, external roles, per-link default roles, permission tags, internal/external discussion split). Limits: one role per external user, no to-dos (no approvals or fill-ins), web only, 100 external users included.
8. **Plugins:** view plugins (custom views, JS SDK `mdye`) and workflow node plugins (packaged reusable steps): organisation-level, versioned, exportable as `.mdye`. Field and page plugins are "future". **Custom fields and Compute are not documented in this slice.**
9. **Aggregated tables** replace Odoo SQL report views for charts, the Get Multiple Data node and the API; read-only, never a worksheet source.
10. **Safety nets:** scheduled backups, 60-day recycle bins, maintenance mode (workflows and APIs keep running), app lock, logs, role debugging mode.

## 2. Capability inventory

### 2.1 App lifecycle and packaging

#### 2.1.1 Create an application
- **Does:** four routes: **Create from Scratch**, import Excel, import an application file (`.mdy`), **Add External Link**. Suggested build order: name, theme colour and icon → worksheets → views (every worksheet needs at least one) → roles → workflows → charts.
- **Planning model:** business function → app; business process → group; business data object → worksheet; data by status → view. Views double as the unit of role access.
- **Limits:** the build page cites about 50 automation actions and 16 chart types; the older introduction page still says 36 controls and 20 automated processes (out of date).
- **Source:** https://help.nocoly.com/application/building, https://help.nocoly.com/application/plan-design, https://help.nocoly.com/application/introduction

#### 2.1.2 Duplicate (copy) an application
- **Does:** copies configuration only, **not worksheet data**. Relations to worksheets in other applications are not copied.
- **Who:** Operators and Developers cannot copy, export or delete an app (role matrix), so copying needs an Administrator. A locked app cannot be copied.
- **Upgrade link:** a duplicate shares the hidden source ID of its original, so the two can upgrade each other later (§2.1.5).
- **Source:** https://help.nocoly.com/application/operations, https://help.nocoly.com/role/type-configuration, https://help.nocoly.com/application/lock, https://help.nocoly.com/application/upgrade

#### 2.1.3 Export an application (`.mdy`)
- **Does:** packages configuration and optional records for import into another organisation, to duplicate, migrate or upgrade an app.
- **Paths:** one app: App Management > **Export** > **Export App** (app administrator). Several: Org Admin > App Management > App > More > **Export App**, up to **20 applications** per export; relations between apps in the same package are kept.
- **Record options:** "Export up to 10,000 records per worksheet" (the quota is split evenly: 100,000 ÷ total worksheets in the package), or a custom number per worksheet (capped at 10,000). Hard caps: **10,000 records per worksheet, 50,000 per application.**
- **Security options:**
  - **Import Password** (generated or typed) protects the file.
  - **Lock Application Configuration** = "No configuration changes allowed after import", with an unlock password. The imported app is locked; nobody can view or change its configuration without that password.
  - Forgotten passwords: export history, or Org Admin > App Management > App > More > **File Password** (upload the `.mdy`; works only for files exported from the same organisation).
- **Included:**
  - application structure: name, icon, theme colour, group layout, settings, sorting, group visibility;
  - worksheet structure: fields, field settings, views, filters, buttons, business rules, worksheet aliases, row-level indexes;
  - permission settings of all roles;
  - workflows (all or selected), with their workflow plug-in configuration;
  - charts, reports and custom pages;
  - external portal: settings, user customisation, passwordless-authentication settings;
  - aggregated tables (excluded from Market and App Library packages);
  - Integration Center API bindings; referenced global variables;
  - application languages; external links; print templates; custom icons; Excel export presets;
  - user, department and position ID mappings.
- **Not included or needs rework after import:** records unless chosen; attachment and print-template **binaries** (only references or URLs; SaaS → Server or Server → Server needs re-upload); user mapping, external system authorisation, API credentials and attachment access (the import page prompts for them).
- **Cannot be exported:** apps from the Application Distribution Platform, apps installed from the Market (incl. locked purchased apps), locked apps (unlock first). The Export button is then hidden.
- **Limits:** paid SaaS editions and every Server edition, per this page ([X-ref] the Nocoly plan comparison lists import and export for Free too: conflict). An export usually takes about 10 seconds. Links between exported records may not all survive; for a complete data move the page recommends Data Synchronization or a consultant.
- **Source:** https://help.nocoly.com/application/import-export, https://help.nocoly.com/application/management

#### 2.1.4 Import an application
- **Does:** creates a new app from a `.mdy`. From the Home page: one package at a time. From Org Admin > App Management > App > More > **Import App**: several packages at once, as new apps or as upgrades.
- **User matching:** by User ID; else, when both mobile and email exist in the package, both must match; else mobile only; else email only. Departments, positions and organisation roles: by ID, else by name (departments by full path).
- **Relations:** relation fields to apps not in the package become text fields; the relation is removed.
- **Source:** https://help.nocoly.com/application/import-export

#### 2.1.5 Import & Upgrade
- **Does:** applies a `.mdy` exported from a **source-related** app to a target app. A, its export-import copy A1 and its duplicate A2 are source-related (same hidden source ID); any of them can upgrade the others. Other files fail with "The imported file is not eligible for upgrade."
- **Paths:** App Management > **Import & Upgrade** (one app). Org Admin > App Management > Apps > More > **Import App** for several: extract a batch package first, then choose **Select Existing Applications** (upgrade) or **Create New Applications**.
- **Modes:**
  - **Merge and Update:** adds missing items, updates existing ones, keeps extra content. Nothing is removed.
  - **Overwrite and Update:** adds, updates, and deletes what the source no longer has (moved to the target's recycle bin). The target ends up matching the source.
- **Change review:** each item is shown as **Add** (only in source), **Update** (in both; not proof that it changed) or **Delete** (only in target, Overwrite only), with **Details**. **You cannot pick which items to upgrade.** Listed upgradable items: worksheets, views, custom view plugins, fields, workflows, workflow plugins.
- **Settings that can be held back (Merge only; Overwrite updates everything):**
  - All Names and Descriptions (app items, views, workflows, roles);
  - All Visibility Settings (app items, views, roles);
  - Appearance and Navigation (theme and navigation colours, navigation, item order);
  - Application Language and Time Zone;
  - Match Users, Departments, and Positions During Import. On: created in the target if missing, permission settings updated. Off: configuration for items missing in the target is cleared, member-related settings of shared items are not updated.
  - Plus **Back Up the Current Version Before Upgrading**.
- **Special cases:** an item that sits in the target's recycle bin is restored, then updated. An item moved to another app is created anew instead of updated.
- **Server only:** **Migration Mode** keeps the original application IDs (unique per platform).
- **Source:** https://help.nocoly.com/application/upgrade

#### 2.1.6 App lock
- **Does:** blocks configuration changes (worksheets, workflows, export, copy, delete) to protect IP and centralise maintenance. Path: App Management > **Lock** → enable → lock password → Confirm.
- **Who:** only the **App Owner** locks, changes the lock password or disables locking. App admins and developers unlock with the password; **unlocking applies only to the current user**.
- **While locked:** App Management = rename, description, logs, usage analysis, unlock. Worksheets = name, description, number reset, Excel import, logs, recycle bin. Views = share and export only. **Workflow entry hidden.** Hidden worksheets and custom pages stay hidden (even with View Hidden Items).
- **Limits:** imported apps, distributed apps and Market apps cannot be locked from App Management. An app locked **at export** arrives locked: users can only unlock it, and **nobody can disable locking**.
- **Source:** https://help.nocoly.com/application/lock, https://help.nocoly.com/application/navigation

#### 2.1.7 Backup and restore
- **Does:** App Management > **Backup & Restore**: **+ Backup** (structure and configuration, data optional; data cannot be backed up alone), **Scheduled Backup** (daily, weekly, monthly), rename, delete, download, **Restore App**, **Restore as New App**, **Restore from File**, backup logs.
- **Contents:** optional data; name, icon, description, mobile navigation, option sets, groups; worksheet structure; custom pages; workflows of this app only (not workflows in other apps that write to it); **role permission settings only (no role members, departments or positions)**; external portal roles and permissions only (no external user accounts).
- **Restore options:** **Restore App Configuration** (later configuration changes are lost); **Restore Data** (incremental overwrite, irreversible); **Back up current app version during restore**. Identity verification is required.
- **Restore semantics (Q&A):** deleted worksheets come back with their data; records added after the backup stay; field values revert to the backup's values (including back to empty); deleted fields come back with their data. **Reference-type fields cannot be restored if modified or deleted:** Relationship, Subform, Cascading, File, Free Link, Department, Org-roles.
- **Limits:** app admins who are members of the organisation; ≥5 minutes between backups; backups count toward the annual attachment upload quota; data backups download only below 1 GB; Restore as New App restores no data, and the new app is visible only to the operator (sole admin). Developers can back up and restore, but cannot download backup files or restore them as new apps. [X-ref] plan comparison: Standard and Professional only.
- **Source:** https://help.nocoly.com/application/backup-restore, https://help.nocoly.com/role/type-configuration

#### 2.1.8 Organisation-level app management
- **Does:** Org Admin > App Management > App lists every app (including ones the admin has not joined): worksheet count, platforms, status, created, owner. Enable, disable, delete; change owner; join any app as app admin; import/export several apps; app recycle bin; decrypt `.mdy` passwords.
- **Owner leaving:** ownership passes to the **Business Assistant** and the app can no longer be deleted by anyone; org admins transfer ownership from the list.
- **Limits:** this page gives the app recycle bin a **7-day** window; the recycle-bin page says **60 days** (conflict).
- **Source:** https://help.nocoly.com/application/management

#### 2.1.9 Recycle bins
- **Apps:** personal (Application > Recycle Bin) and org admin (App Management > App > More > App Recycle Bin); 60 days; paid editions. Owners restore or purge their own apps; org super admins all apps.
- **Worksheets and custom pages:** App Management > Recycle Bin; 60 days; structure and relations restored.
- **Views:** View List > **Recently Deleted**; 60 days.
- **Fields:** form editor > Recycle Bin; 60 days; data restored with the field.
- **Records:** worksheet menu > Recycle Bin (can be hidden by the role's function switch); 60 days; ≤1,000 records per restore; members restore only records they deleted; only app admins purge; related records in other sheets are restored too.
- **Custom actions:** custom action page > Recycle Bin.
- **Workflows:** 60 days; paid editions; restored workflows are **disabled** until enabled by hand; only app admins and developers.
- **Source:** https://help.nocoly.com/application/recycle

#### 2.1.10 Maintenance mode
- **Does:** App Management > **Publish** > **Application Maintenance**, with an announcement (reason, expected recovery). Only app admins can turn it on.
- **Effect:** regular members and external portal users cannot enter. App admins work normally. **Workflows keep running, worksheet APIs stay available, and published public forms, public queries, shared records and shared views stay reachable.**
- **Source:** https://help.nocoly.com/application/maintenance, https://help.nocoly.com/application/publish

#### 2.1.11 Publishing and platforms
- **Does:** App Management > **Publish**: platforms **PC**, **Mobile App**, **Mobile Web** (mobile browsers, WeChat Mini Programs, WeCom, DingTalk, Feishu); publish to third-party workspaces; share links with hidden UI areas; maintenance.
- **Source:** https://help.nocoly.com/application/publish

#### 2.1.12 App Library
- **Does:** about 200 template apps: preview, install, download as `.mdy`. Anyone can upload an app under **My Publications** as **Creator** or **Partner**; approval usually takes 1–3 working days; updates must be re-uploaded. All worksheets must be uploaded; workflows are optional. Paid downloads are planned, not live. Installs become sales leads for the uploader.
- **Limits:** aggregated tables are excluded from App Library packages (export page).
- **Source:** https://help.nocoly.com/application/library, https://help.nocoly.com/application/import-export

### 2.2 Language and time

#### 2.2.1 Application localization
- **Does:** translates an app into several languages. App Management > **Language**.
  - **System Text:** menus, buttons, descriptions, notifications.
  - **Custom Content:** worksheet, field, view and button names, option sets, workflows and workflow node names.
  - **Not translated:** user-entered data, i.e. values of Text, Rich Text, Formula, Concat, Auto Number and Uppercase fields, record comments.
- **Languages:**
  - **Full support (system + custom):** Simplified Chinese, Traditional Chinese, English, Japanese, **Malay**, Thai.
  - **Partial (custom content only):** about 50 more, incl. Indonesian, Vietnamese, Filipino, Hindi, Bengali, Korean, German, French, Spanish. **Tamil is not in the table** (nor Arabic).
- **Options:**
  - **Base Language** (language admins build in; default = the admin's account language; a non-system language can be chosen, but the system UI then follows the user's account language).
  - **Source Text** = what was typed while building; the fallback for every language.
  - **Add Language**; pick content in the app tree; **reference language** column (read-only) next to the target column; manual entry.
  - **Smart Translation** (AI): **Translate Empty Items Only** or **Translate All Items (Overwrite Existing Translations)**.
  - **Sync Referenced Languages:** pulls translations of option sets and related worksheets/records owned by other apps (the source app is not changed).
- **Display:** a language selector appears in the app's navigation bar. Priority: **Application Language > Personal Account Language > Source Language**. Choosing a system-supported app language **also switches the user's personal account language** (not the other way round).
- **Limits:** paid editions only ([X-ref] Standard and Professional). A translation can only be made where the reference language has content. Rich Text content (app description, remark fields, worksheet and page descriptions) is not smart-translated. After a successful Smart Translation, wait 5 minutes before the next run. **Languages survive application copy, export and import.**
- **Source:** https://help.nocoly.com/application/language
- **[Ours] traps met on Nocoly (19–23 Nov 2026):** the worksheet summary line is never translated (write it bilingual); the "+ Add" button only gets a translation slot after a custom add-button name is set; renaming a field leaves its old translation in place.

#### 2.2.2 Application time zone
- **Does:** App Management > **Time Zone** sets the common basis for date/time **filtering** in worksheets, views, business-rule filters and charts ("Today", "Yesterday", "Tomorrow" and unspecified times use it). Display still follows each user's **personal time zone**; a label shows when the two differ.
- **Source:** https://help.nocoly.com/application/app-time-zone

### 2.3 Structure, navigation, appearance and embedding

#### 2.3.1 Navigation
- **Does:** App > Navigation. PC styles: **Classic** (default; groups on top, sheets on the left), **Group List**, **Tree List**, **Card**. Up to **3 levels**; groups only at levels 1–2; worksheets and pages at any level.
- **Options:** icon display per level; **Remember Last Accessed Item**; Tree List expand mode **General** or **Accordion**; **Hide First Group Title** (Tree List; first group's item as a home page); **View Hidden Items** (admins see hidden sheets; never while locked). Groups: create, rename, icon, delete (must be empty first), reorder, move sheets by drag and drop. Mobile: navigation style plus group display **List**, **Matrix** or **Tab Bar** (default: first four sheets/pages; fixed once configured).
- **Source:** https://help.nocoly.com/application/navigation

#### 2.3.2 Common operations, icons and colours
- **Does:** admins change name, theme colour, navigation colour, icon (built-in fill/outline or custom), description; duplicate; delete (owner only) or leave; personal app order; app groups; publish; maintenance; backup; **option sets** (app-level shared option lists for single/multi-select fields).
- **Org general settings:** Org Admin > App Management > General Settings: **Custom Icon** (SVG only; option "Upload icons with color retained") and **Custom Color** (theme colours: up to 18 enabled, up to 18 custom; chart colours: up to 10 custom).
- **Source:** https://help.nocoly.com/application/operations, https://help.nocoly.com/application/settings

#### 2.3.3 Home page and app groups
- **Home page:** org admins set logo (height), slogan, **banner** (several items, image + optional link, 1600×400 px recommended, jpg/jpeg/png/gif, ≤2 MB, rotates every 3 s) and theme colour (inside an app the app's colour wins). Users set the to-do display (**count**, up to 99, or **list**; red dot for CC-only), recent items (≤30), favourite apps/sheets/pages, **favourite records (≤200)**, **favourite charts (≤10)**, section order.
- **App groups:** system groups **All**, **Owned**, **External Collaboration**; custom **personal** groups (any user, private) and **organization** groups (org super admins or app admins; visible to the app's members). Star groups (Tile or Tab display), reorder, search.
- **Source:** https://help.nocoly.com/application/homepage, https://help.nocoly.com/application/group

#### 2.3.4 Hide UI areas (embedding)
- **Does:** URL parameters hide parts of a HAP page for iframe embedding: `s` (back to home), `tb` (group bar), `tr` (top-right buttons), `td` (to-do), `ac` (avatar), `ln` (left navigation), `rp` (right message panel), `ch` (chat), each `=no`. Example `?s=no&tb=no&tr=no&ln=no&rp=no`.
- **Limits:** lowercase names and values; any order; only `no` hides; reliable only inside an iframe (navigation elsewhere may drop the parameters).
- **Source:** https://help.nocoly.com/application/hide-area

#### 2.3.5 External application links
- **Does:** **Create App** > **Add External Link**: a home-page entry that opens an `http(s)` URL with parameters: user ID, phone, email, language (`en`, `ja`, `zh-hant`, `zh-hans`), organisation Door ID, app ID, UserAgent (≤150 chars), timestamp. Visibility per platform (PC, mobile web, App; admins always see it on PC). Roles: owner, admin, member.
- **Source:** https://help.nocoly.com/application/external-link

#### 2.3.6 ER diagram
- **Does:** App Management > **ER Diagram**: worksheet cards with relation and subform lines; one arrow = one-way, two arrows = two-way; `1` / `N` cardinality; **Focus** on one sheet's direct relations; edit fields from a card; drag cards; create or search sheets; zoom; export the diagram.
- **Source:** https://help.nocoly.com/application/er

### 2.4 Roles and permissions

#### 2.4.1 Model and access path
- **Does:** role-based access control. A user reaches a record only through **application > section (group) > worksheet > view**. Admins configure roles, then add users, departments, organisation roles or job titles.
- **Scenarios covered:** which items and views are visible, which records are visible, which records can be edited or deleted, which fields are hidden or read-only, which fields can be filled on create, and switches for sharing, printing, import, export and bulk operations.
- **Source:** https://help.nocoly.com/role/introduction, https://help.nocoly.com/application/add-member

#### 2.4.2 System roles
- **Administrator:** all configuration and data. Fixed permissions; cannot be changed or deleted.
- **App Owner:** one per app, by default the creator, transferable. Only the owner deletes or locks the app; otherwise equals an administrator.
- **Operator:** data and user management without configuration: manages Role Owners and members of all custom roles; views, edits and deletes **all records**. Cannot copy, delete or export the app, nor manage users of system roles.
- **Developer:** configuration: navigation and groups, workflows, worksheets, custom pages, roles (including portal roles), external portal settings including domain configuration. Data rights: **views joined records, edits and deletes only owned records**. Cannot copy, delete or export the app. For a cross-app relation, the user must be Developer or Administrator in the referenced app.
- **Operator + Developer** = Administrator minus copy, export and delete.
- **Matrix highlights** (Operator / Developer):
  - copy, export, delete app: No / No;
  - backup, restore, navigation, option sets, app recycle bin, publish settings, API development documents: No / Yes;
  - usage analysis: Yes / No;
  - edit form, worksheet settings, field names, view configure/copy/delete, public filters, save print templates, custom-page editing: No / Yes;
  - Excel import, autonumber reset, worksheet logs, recycle bin, view share/export, record calibration: Yes / Yes;
  - roles, permissions and extended info: No / Yes; Add User: Yes / Yes;
  - portal roles, portal settings, custom domain: No / Yes; portal approval-free configuration: Yes / No.
  - A third column ("permissions if app locked") equals the Operator column in every row.
- **Source:** https://help.nocoly.com/role/type-configuration

#### 2.4.3 Custom roles and Role Owner
- **Does:** admins and developers create roles with a name and description (shown to users). New apps come with two custom roles, **Member** and **Read-Only**. A **Role Owner** is a member type that can add and remove the role's members and appoint other Role Owners.
- **Source:** https://help.nocoly.com/role/type-configuration

#### 2.4.4 Mode 1: Access to all application items (simple)
- **Does:** every page, worksheet and view is visible; one uniform rule for all sheets. Presets:
  1. View, Edit, and Delete All Records;
  2. View All Records, But Only Edit/Delete Owned Records;
  3. View Joined Records, Only Edit/Delete Owned Records;
  4. Read-Only for All Records.
- **Options:** for presets 2 and 3, **Records Owned/Joined by Subordinates** (subordinates from the Org Chart). Other actions: create, import, export, print, share and similar.
- **Limits:** **no field-level permissions**; meant for apps with few users and roles.
- **Source:** https://help.nocoly.com/role/type-configuration

#### 2.4.5 Mode 2: Access to selected application items (advanced)
- **Level 1, visible pages:** choose worksheets, custom pages and views. A worksheet's data needs at least one visible view. Custom pages only have "view".
- **Level 2, record permissions in views:** **View**, **Edit**, **Delete**, **Add**. Viewing is a prerequisite for edit and delete. **Add is set per worksheet, not per view.**
- **Level 3, operable record scope** (button **Settings**):
  - Viewable: **All** / **Joined** / **Subordinate Joined**;
  - Editable: **All** / **Owned** / **Subordinate Owned**;
  - Deletable: **All** / **Owned** / **Subordinate Owned**.
  - **The scope applies to all views of the worksheet.** For different scopes per view, put the user in several roles.
- **Level 4, field-level permissions:** show/hide in view and edit mode, editable or not, hidden when creating. An editable field must be visible.
- **Action tab:**
  - Worksheet: Public Sharing, Import, Export, Discussions, Bulk Operations;
  - Record: Public Sharing, Discussions, System Print, Attachment Download, Logs (which log types; log export);
  - Payment: **Make Payments**.
  - The worksheet's **Function Switch** sets the same actions per view. **The more restrictive of the two wins.**
- **Bulk Permission Configuration:** record scope, editable fields and system actions across several sheets at once. It skips sheets where the base right (e.g. Delete) is off, and **excludes custom actions and payment settings**.
- **Hide from Navigation:** per role (hover > Hide) or for all non-admins. Hiding only removes the menu entry; the sheet stays reachable through related sheets, links and views embedded in custom pages.
- **Hide Applications:** removes the app from members' home page only; notifications and shared links still open it.
- **Source:** https://help.nocoly.com/role/type-configuration

#### 2.4.6 Record identities
- **Creator:** fixed; shows "Public Form", "Workflow" or "API" for records made that way. Never a permission by itself.
- **Owner:** built-in system field; defaults to the creator; reassignable; can be set to **Unassigned**.
- **Owner-level permission through fields:** a Member, Department or Organization Role field whose field permission is **Owner** gives the selected users (or the department's or org role's users) the owner's rights. **They are not written into the system Owner field**, so filtering by Owner, "update owner" in workflows and references to Owner only see the system field.
- **Member:** users in a Member, Department or Organization Role field whose field permission is **Member**. Being a member grants nothing by itself.
- **Joined:** Owner + Members; used as a record scope.
- Final rights always come from the role (operation, record scope, field permissions). Example: a role without edit rights means even the owner cannot edit.
- **Source:** https://help.nocoly.com/role/creator-owner-joiner

#### 2.4.7 Several roles on one user
- **Rule:** merge only where two roles configure the **same worksheet**; then per **view**, per level, take the union (highest).
  - **L1** operations in the view (view, edit, delete) gate everything below.
  - **L2** record scope.
  - **L3** fields on create/view/edit, system features (discussions, sharing, import, printing) and **custom actions**.
- Broader L2/L3 rights do nothing where L1 is off in that view. Roles that configure different worksheets do not interact.
- A downloadable "Permission Merging Rules Table" is referenced (not in the cache).
- **Source:** https://help.nocoly.com/role/multi-role-permission

#### 2.4.8 User extended information (permission tags)
- **Does:** Users > Expand > **Create User's Expanded Information Table**. A mapping worksheet holds a Member field (**user mapping**) and relation fields (**permission labels**). A role's record scope can then use "records under my labels", e.g. orders of the teams I belong to.
- **Limits:** up to **3** label fields; up to **1,000 labels** per user per label field (more are ignored); no limit on records per label. External member fields cannot be the user mapping (externals join as external collaborators). [X-ref] the plan comparison lists extended user information under Professional only.
- **Portal equivalent:** a relation field in the portal user list as a permission tag (§2.5.6).
- **Source:** https://help.nocoly.com/role/extended-info, https://help.nocoly.com/portal/introduction

#### 2.4.9 Adding members and managing users
- **Add Users** to a role: persons (Contacts; external collaborators via Friends), **departments** (current and future members inherit the role; sub-departments included unless "Current Department Only"), organisation roles, job titles. Users can also apply to join through the app link.
- **Role operations:** **Create Role**; edit; **Copy** (permissions and description, **not users**); **Delete** (move members to another role or remove them; other roles unaffected); reorder (Administrator always on top).
- **User tab:** **All** (users, positions, departments and org roles with role labels; export lists departments etc. by name, not expanded), **Apply to Join**, **Collaborators** (external collaborators), per-role lists. Transfer app ownership. **Allow viewing** (non-admins see the user list or not). Notifications on add, role change and removal can be switched off.
- **Source:** https://help.nocoly.com/role/operations, https://help.nocoly.com/role/type-configuration

#### 2.4.10 Role debugging mode
- **Does:** enable on the app's User Management page; a role menu then lets admins test any role and operators test regular roles (the overview also names developers). One role at a time, or **Multi-Select Mode** for combinations. Also applies on mobile. Clear with the X; disable on the user page.
- **Source:** https://help.nocoly.com/role/debugging

#### 2.4.11 Worked patterns from the docs
- **Self-service profile:** "My Profile" view filtered to the current user, edit scope All, Employee ID and Department read-only through field permissions; "Contacts" view read-only with private fields hidden.
- **Lock records by status, method 1:** one view per status; grant Edit only in the Draft and Rejected views.
- **Lock records by status, method 2:** role edits only owned records; a workflow sets Owner to **Unassigned** when the request goes under review and back to the creator when rejected.
- **HR-like full access:** administrator only if they must change structure; otherwise a separate data role.
- **Source:** https://help.nocoly.com/role/permission-configuration-example

### 2.5 External portal

#### 2.5.1 Enable, URL and entry points
- **Does:** app **User** module > **Enable External Portal**; disable with Portal Settings > Basic > **Close Portal**. Registration and login share one entry; the first login creates the account. Links and QR codes are in Portal Settings.
- **URL:** default `Domain/Application ID`. A custom suffix replaces the app ID: letters, digits and hyphens, not starting or ending with a hyphen, ≥4 characters, unique. The default URL keeps working. This page says the domain itself is fixed, while the role matrix lists "Edit Custom Domain Name" for developers (unclear).
- **Login page:** Portal Settings > **Customize Login Interface**: page name, logo, layout (left-right only on PC browsers), background image or colour. A **portal display name** separate from the app name.
- **Source:** https://help.nocoly.com/portal/introduction, https://help.nocoly.com/role/type-configuration

#### 2.5.2 Registration, login and security
- **Accounts:** mobile number or email. **Login:** verification code (needs **SMS Signature Settings**; first code login auto-registers), password (set later in Personal Center), WeChat QR code (bind a WeChat service account in Org Admin; option to require following it first; marked "Coming soon" in one place).
- **Options:** user agreement and privacy policy; **two-factor authentication** for password and WeChat logins; **Restrict Registration Time**; **Enable 7-Day Passwordless Login** (on by default); **Require Mobile Number and Email Binding**.
- **Personalised login links:** several links, each with its own registration methods, login methods and **default role** (methods must be enabled in Portal Settings > Basic). Example: email + password for overseas users, mobile + WeChat for China.
- **Source:** https://help.nocoly.com/portal/introduction

#### 2.5.3 Access permission type
- **Anyone:** anyone with the link registers and enters without approval.
- **Approved users:** an admin reviews new registrations (SMS on the result). See the approval-exempt list in §2.5.8.
- **Invited users only:** registration only by invitation, single or batch.
- **Source:** https://help.nocoly.com/portal/introduction

#### 2.5.4 Discussions and notifications
- **Record discussions:** **Disable discussions**; **Allow discussions - View all discussions** (one shared area); **Allow discussions - Invisible internal discussions** (separate internal and external areas; externals see only their own). The worksheet's Function Switch settings also apply. Switching from "show all" to "hide internal" for the first time moves old discussions into the internal area.
- **Discussion notifications:** externals get no app notifications. Basic Settings > Notification Settings > **Notify external users when there are discussions (mentions and replies)** auto-creates a workflow with a fixed trigger; add SMS, email, WeChat or API nodes, then **Publish**.
- **Registration notifications:** admins get an in-system message on new registrations or activations; users get an SMS with the approval result.
- **Source:** https://help.nocoly.com/portal/introduction

#### 2.5.5 Messages (SMS and email)
- **SMS:** signature ≤20 characters. **Custom Signature** needs an org admin to add it and complete real-name verification; otherwise the **Platform Signature**. The login-code SMS text is fixed. Invitation and approval-result SMS are editable. With **Include Link**, carriers force the platform signature; a short custom URL suffix reduces billable characters.
- **Email:** login codes, password-setup codes, invitations, approval results. **Sender fixed as `sender@register.mingdao.com`**; subject and body editable under **Email Settings**.
- **Charges:** SMS to mainland China numbers is deducted from credits. **SMS to Hong Kong, Macao, Taiwan or other international numbers requires integrating Twilio first.**
- **Source:** https://help.nocoly.com/portal/introduction

#### 2.5.6 Collect info and extended permission tags
- **Collect Info:** fields users must complete after their first login before the account is active (Name is not collected by default; add, sort, remove field types). Per app. If approval is on, users finish the fields before entering approval.
- **Permission tags:** a relationship field in the external user list used as a permission tag (pointer to "Extended Permission Tags").
- **Source:** https://help.nocoly.com/portal/introduction

#### 2.5.7 Other portal settings
- **Allow Viewing Approval Flowchart Details:** externals see approval progress, only for approvals started by the **Initiate Approval Flow** node.
- **Screen Watermark:** name, mobile, email or custom text.
- **Allow External Users to Modify Account Information** (bound mobile/email) and **Allow External Users to Modify Personal Extended Information**.
- **Configure Business Card:** what internal users and external users may see of an external user (hide other externals' mobiles and emails).
- **Source:** https://help.nocoly.com/portal/introduction

#### 2.5.8 External roles and user management
- **External roles:** managed separately from internal roles but with the **same permission structure**, so configurations can be copied between them. **Each external user belongs to exactly one role.** Users are managed by assigning roles, not added to roles directly. **Set Default Role** for new registrations.
- **Invite:** **Invite User** (tick **Send Notification** or nothing is sent), or batch import from a template.
- **User list:** filters by role, status (Active, Disabled, Deactivated) and fields; column settings; quick edit (role, status); side panel (collected fields, status, role); WeChat OpenID column; export by role or selection; batch activate, disable, deactivate (delete), cancel invitations, remove, re-invite. Users can deactivate themselves.
- **Approval:** **Pending** list, approve or reject one by one or in batch. **No Approval Settings** → Enabled: auto-approve registrants who match a list from an **Excel file** (first row = field names) or an **application worksheet** (this app or another). Map mobile or email, plus collected fields if any; registered values must match exactly. Worksheet lists update live; Excel lists need re-upload.
- **Statistics:** External Portal > **Statistics**: daily registrations, page views, security login logs, user management logs.
- **[X-ref] workflow nodes:** **Get Single/Multiple External User** and **Update External User Info** read and change an external user's name, role, status (Active/Disabled only) and collected fields; an **External User** member field can hold portal users in records.
- **Source:** https://help.nocoly.com/portal/introduction

#### 2.5.9 What external users get
- **Can:** personal settings (name if collected, avatar, bound mobile/email, password, **system language**, extended info, deactivate, log out); views and create/read/update/delete within their external role.
- **Cannot:**
  - use any app other than this portal's (no switching; another app needs its own link and login);
  - use collaboration tools, Contacts, posts, IM;
  - use **to-dos, including approvals, fill-in, CC and internal notifications**;
  - have departments, positions, org roles or reporting lines;
  - hold more than one app role;
  - use the mobile App, mini programs or third-party login (web only: PC browser, mobile browser, WeChat browser).
- **Identity types (FAQ):** organisation members; external collaborators (registered HAP users invited into an app or collaboration item; several roles possible; to-dos supported); external users (portal accounts).
- **Quota and price:** all plans include **100 external users**. Disabled and deactivated users do not count. **The same person registering on two apps' portals = two accounts and two quota uses.** The page prices external users from RMB 0.5 per user per year (Mingdao-era); [X-ref] Nocoly plan page: packages at $25 per 100 users/month, $50 per 1,000, $250 per 10,000.
- **Maintenance mode** also blocks external users (§2.1.10).
- **Source:** https://help.nocoly.com/portal/introduction, https://help.nocoly.com/portal/faq

#### 2.5.10 Organisation-level external users and collaborators
- **External users:** Org Admin > **External User**: view, search, delete across apps; add or renew capacity; **Auto-Purchase** (below 20 remaining, 500 credits buy 100 more). Deleting a person from one app's portal leaves their other portal accounts.
- **External collaborators:** people outside the organisation invited from Contacts (All) or through shared links to apps, groups, tasks. In an app they appear under that app's **Collaborators**, not in the org-level list; Org Admin > External User > **Collaboration** shows their participation and removes them everywhere at once. An org member who leaves stays in Owner/Member fields, labelled **External Collaboration**.
- **Source:** https://help.nocoly.com/portal/management

### 2.6 Plugins, custom fields and Compute

#### 2.6.1 Plugin Center
- **Does:** develop and manage plugins for the organisation. Today: **views** and **workflow nodes**. **Worksheet field plugins** and **custom page plugins** are announced for a later release.
- **Source:** https://help.nocoly.com/plugin/introduction; https://help.nocoly.com/plugin/extensions-api is empty in the cache.

#### 2.6.2 View plugins ("Customized view")
- **Does:** a fully custom view of a worksheet's records when Table/Grid, Kanban, Org, Calendar, Gallery, Detail, Resource and Gantt are not enough. Users treat it like any view: permissions, sharing, search, filters, statistics, **Quick Filtering** and **Filter List** (opt-in; the plugin receives events and must filter itself).
- **Create:** add a view of type **Customized view**, or Plugins > **Developed by me** > **Create Plugin** (choose a debug worksheet).
- **Settings parameters** (shown to whoever configures the view; read in code via `env`): Field Selector (single or multiple, `array[string]`, optional count limit), String, Number (double), Enum (Radio Group or Dropdown Menu, options `key=value`), Boolean (Switch or Checkbox), Group. **Parameter Mapping** ties them to variable IDs.
- **Environment parameters:** admin-level JSON injected into `mdye.env`, e.g. each customer's own licence key for a paid component.
- **Development:** Node.js ≥16.20; `npm install -g mdye-cli` (doc shows `beta-0.0.37`); commands `auth`, `init view --id <id> --template <name>`, `start`, `build`, `push -m`, `whoami`, `logout`, `sync-params`. Templates: React, JavaScript, React + Tailwind CSS, Vue 3, Vue 2. Debug: paste the local server JS address on the plugin's **Debug** page > **Load** (hot reload). Rendered in an **iframe**; **mobile adaptation is the developer's job**.
- **SDK `mdye`:**
  - `env`: view settings.
  - `config`: appId, worksheetId, projectId, viewId, filters, URL query, controls, worksheetInfo, currentAccount (accountId, fullname, avatar, lang).
  - `api`: `getFilterRows` (worksheetId, viewId, pageSize, pageIndex, sortId, isAsc, notGetTotal), `getFilterRowsTotalNum`, `getRowDetail`, `getRowRelationRows` (relation or subtable rows), `addWorksheetRow` (receiveControls), `updateWorksheetRow` (newOldControl), `deleteWorksheetRow` (rowIds).
  - `utils`: `openRecordInfo`, `openNewRecord`, `selectUsers`, `selectDepartments`, `selectOrgRole`, `selectRecord`, `selectLocation`.
  - `md_emitter` events: `filters-update`, `new-record`.
  - Field value formats are documented by type, e.g. 2 text, 6 number, 8 amount, 15 date, 46 time, 11/10 single/multi select (option keys), 26 member, 27 department, 48 org role, 36 checkbox, 28 rating, 41 rich text, 40 location, 29 relation, 35 cascading.
- **Release:** `mdye push` stores a build (visible to everyone using that view once the debug file is cleared). **Publish** a chosen submission with a version number higher than the current one. Before publishing, the plugin works only in its debug app; after an admin enables it, everyone in the organisation can add it as a view.
- **Management:** **Developed by me** (debug apps, submission and release history, publish) and **Organization** (release history, environment parameters, usage, upgrade or roll back by admins). Regular users only view the list.
- **Export/import:** a published plugin exports as `.mdye` from **Publishing History**. An authorisation key can set an **import password**, an **expiry date** (after which the plugin stops working for the whole importing organisation), **authorised organisations** and **authorised private-deployment servers**; all set conditions must hold. Import via **+Import** on the Organization page; an existing same-source plugin can be upgraded or a new copy created. **Imported plugins cannot be exported again.** Publishing to a plugin library is not available yet.
- **Samples:** Map, Detail Table, Timeline at `github.com/nocoly/plugin_view_samples`.
- **Source:** https://help.nocoly.com/extensions/developer/view (the cached page holds the guide twice, with only wording differences)

#### 2.6.3 Workflow node plugins ("custom node")
- **Does:** packages a data-processing step into a reusable node for everyone in the organisation, like a small packaged business process for one step. Components: **Branch**, **AIGC**, **API request**, **code block**, **JSON parsing**.
- **Create:** Plugin Center > **Workflow Node** tab > **Create Plugin**: name, icon, description (shown to users); input parameters (extra input methods for option and checkbox inputs, group titles); data processing steps; output parameters from those steps.
- **Release:** **Publish** (the node appears under the **Plugin** tab when adding nodes), test, then publish to the organisation. New versions via **Edit**; any version can be set as **Current Version** (the latest is not necessarily the live one).
- **Example:** an encryption node (MD5, SHA-1, SHA-256, HMAC) for API signatures.
- **Limits:** [X-ref] the plan comparison puts workflow plugins in Standard and Professional, and the Code Block node in Professional only.
- **Source:** https://help.nocoly.com/plugin/node

#### 2.6.4 Custom fields and Compute: not covered by this slice
- **Nothing in these 44 pages documents custom fields or HAP Compute.** The Plugin Center page still lists field plugins as future.
- **[X-ref]** https://help.nocoly.com/worksheet/control-custom-fields (worksheet slice) documents **Custom Fields**: a form control coded by AI chat or by hand in React + Tailwind CSS; modes **Store Field Value** or **Reference Other Field Values Only** (`formData[env.<variable>]`); mock data, mobile and read-only (`env.isDisabled`) previews; no third-party libraries. The cached Nocoly page states no per-sheet count (the "5 per sheet" in `../../compute-for-ui.md` comes from Mingdao V12.1 help).
- **"Dedicated Instance" (§2.7.6) is not HAP Compute.** The help.nocoly.com cache has no Compute page at all. For Compute facts and the checks to run first, see `../../compute-for-ui.md`.

### 2.7 Data, AI and operations add-ons

#### 2.7.1 Aggregated tables
- **Does:** App Management > **Aggregated Table** > **Create Aggregated Table**: a virtual table that groups and sums data from one or more worksheets (also from other apps).
  - Sources: **+ Worksheet** (each once), a filter per source.
  - Grouping fields: each source must have a field for the same business object; rename, reorder; **Show null**; array fields (e.g. multi-select) counted **split** or **combined**.
  - Aggregation fields (**+ Field**): **Sum, Maximum, Minimum, Average, Count, Distinct count**, with a data format.
  - Calculation fields over aggregation fields only.
  - **View Data** preview, rename, publish.
- **Used by:** charts on custom pages (incl. pivot tables), the workflow **Get Multiple Data** node, and the API (in the app's API documentation). **Query only**: no update or delete. **Not usable as a worksheet data source.**
- **Management:** create, delete, edit, duplicate, enable/disable, rename, **Resynchronize** (pulls fresh data; other aggregated tables on the same source resync too). Org admins can enable or disable all of them centrally.
- **Limits:** ≤**20 aggregation fields**; fields whose names contain `@@` or a backtick cannot be selected; capacity is a quota, bought in multiples of 5 (Org Admin > App Management > Aggregated Table > **Expand**). Carried by export, migration and upgrade; not by Market or App Library packages.
- **Source:** https://help.nocoly.com/application/aggregation, https://help.nocoly.com/application/import-export

#### 2.7.2 Vector knowledge base
- **Does:** App Management > **Vector Knowledge Base** > **+ Vector Knowledge Base**: vectorises chosen worksheets of the current app (records, attachments, optionally record discussions) for semantic search by the **Knowledge Retrieval** workflow node and the **AI Agent** node.
- **Options:**
  - Fields: Text, Concat, Title, Rich Text, Cascading (single), Relationship (single), stored foreign fields (Text, Concat, Rich Text, File), File (doc, docx, xls, xlsx, ppt, pptx, rtf, pdf, txt, csv, md).
  - Record filter (option, level and check-item fields); **enhanced attachment parsing** (vision model).
  - Chunks: records ≤3,500 characters; attachments split by paragraph (>1,000 tokens split again); one chunk per discussion message.
  - **Start Vectorization** by hand (model Qwen3-Embedding-0.6B).
  - Retrieval: semantic, keyword or hybrid; Top K ≤20; minimum relevance 0–1.
  - Records added, changed or deleted later sync automatically.
- **Limits:**
  - **While vectorising, the source worksheets' records cannot be added, deleted or modified.**
  - Paid only: Standard 100,000 chunks, Professional 200,000; extra $30 per 10,000 chunks per year. Over quota: no new data is vectorised.
  - After the subscription expires, data is kept 30 days.
  - **Export, import, duplication, upgrade and backup/restore do not carry knowledge-base configurations.**
- **Source:** https://help.nocoly.com/application/vector-knowledge-base

#### 2.7.3 Offline data submission (mobile app)
- **Does:** App Management > **APP Offline**: choose worksheets; in the mobile app, Me > **Offline Mode**. Records are saved locally and **submitted by hand** when the network is back (no automatic sync, no batch submission).
- **Fields offline:** Text, Number, Currency, Email, Date, Time, Telephone, File, Check Item, Rich Text, ID Number, Positioning, Single/Multi-select (**custom options only**), Signature. No relation fields.
- **Rules:** business rules, validations and permissions do not run offline; they are checked at submission.
- **Source:** https://help.nocoly.com/application/appofflinesubmit

#### 2.7.4 Logs
- **Application logs:** org-wide (Org Admin > Log > App) or per app (App Management > Log). Categories:
  - **Application Management:** create, update, delete and export of apps, items, print templates, workflows, users, option sets and aggregated tables; role changes for internal and portal users.
  - **Data Operations:** create (not drafts), update, delete, restore, export, batch create/delete/update, custom actions, attachment downloads.
  - **User Behavior:** browse and print; the page ties it to the "Ultimate Edition" ([X-ref] Nocoly lists user activity logs under Professional); no backfill.
  - Export for the last six months; also through the API (`nocoly.com/apidoc/organization`).
- **Login logs:** user, time, method, type, IP and location, browser, OS, device type, model and ID; filter, columns, export.
- **Org admin logs:** permission-group changes such as adding or removing administrators.
- **Source:** https://help.nocoly.com/application/log

#### 2.7.5 Usage analysis
- **Does:** organisation totals (apps, worksheets, records, workflows, attachment storage; real time) and trends (visits, visitors, records created, workflow runs, uploads; daily, up to yesterday). Views by application and by member; filters by department, app and period; export to Excel. Navigation inside an app does not count as a visit. [X-ref] usage analytics is a Professional feature on the Nocoly plan page.
- **Source:** https://help.nocoly.com/application/usage-analysis

#### 2.7.6 Dedicated instance (workflow concurrency)
- **Does:** reserved workflow capacity, so that chosen workflows are not delayed by queue congestion. **Not faster per run.** Typical runs: a worksheet-event workflow finishes within 5 s, a button workflow within 1 s (excluding approval, fill-in and delay nodes). Subprocesses and packaged business processes called by an assigned workflow run on the same instance.
- **Options:** concurrency 20, 50 or 100; **Monthly Upgrade Package** (to licence end) or **Single-Month Package**. Status: Creating, Active, Terminating, Terminated. Add, remove or move workflows, one by one or in bulk.
- **Limits:** org super admins and org app admins; not on Free; ≤5 per organisation; one free single-month trial of 20. Prices on the page are in RMB (200/500/1,000 per month).
- **Source:** https://help.nocoly.com/application/exclusive-computing-power

## 3. Odoo rebuild notes

Everything in this section is **[Inference]** built on the docs above, unless a doc fact is restated.

### 3.1 Concept map

| Odoo concept | HAP native replacement | Where native falls short |
|---|---|---|
| Installable apps (modules) and the app menu | One first-level navigation group per Odoo app; its menus as second-level groups; worksheets and pages at level 3 (§2.3.1) | No module manager: no dependency check, no uninstall. Odoo menus deeper than 3 levels must be flattened |
| Install a module for a customer / uninstall it | Duplicate or export the master, prune groups, import into the customer's organisation (§2.1.2–2.1.4) | Pruning is manual; relations, workflows, rules and pages that cross a pruned module must be found by the register scan |
| Module update (`-u`) for an installed customer | **Import & Upgrade** from a source-related package (§2.1.5) | Not selective. The full master re-adds pruned modules (trap T2). Customer-side extras are deleted by Overwrite |
| Database duplicate, backup, restore | Duplicate; Backup & Restore with scheduled backups (§2.1.7) | Per app, not per database. No role members, departments, portal users or other apps' workflows. Reference-type fields restore only partly |
| apps.odoo.com and module licences (OPL) | App Library (free now, paid later); `.mdy` import password and configuration lock; `.mdye` plugin keys with expiry and organisation binding | Locks on imported apps are permanent; apps have no licence expiry, only plugins do |
| Data export/import (`base_import`) | Excel import per worksheet (outside this slice); app export with records (≤10,000 per sheet, ≤50,000 per app) | App export is not a migration tool: links between exported records may break |
| `res.lang`, user language, UI translations | Application Localization: Malay, English and Simplified Chinese with full system text; Smart Translation; language selector; App > Account > Source priority (§2.2.1) | Paid editions only. Tamil is not supported at all |
| Translatable record fields (`translate=True`: product name, sales description, payment terms, UoM names) | None native | Record values are never translated: use one field per language or a translation worksheet, and pick the field by the user's or partner's language in views and print templates |
| Partner language for documents and emails | None native (each user has a personal language; external users choose a system language) | Print templates and workflow messages per language need a language field on the contact and branching or one template per language |
| User time zone; "today" in domains | Personal time zone for display, app time zone for date filters (§2.2.2) | Set the app time zone to UTC+8 once; filters do not follow each user's zone |
| `res.groups` hierarchy, e.g. Sales: User own documents → All documents → Administrator | Custom roles with record scopes Owned/Joined/All, plus subordinate scopes; system Administrator/Developer/Operator (§2.4.2–2.4.5) | No implied groups: each level is a separate role. Multi-role union gives the same result when a user holds several roles |
| `ir.model.access` (create/read/write/unlink per model) | Advanced mode: Add per worksheet; View/Edit/Delete per view | Add cannot differ by view |
| `ir.rule` domain record rules | A view filter as the "domain", plus record scope, plus Org Chart subordinates, plus extended-information tags (§2.4.8) | No free domain on the role. The record scope is one per worksheet and role, so "different rule per menu" needs more roles. Hidden sheets stay reachable through relations |
| Multi-company rules (`company_ids`, allowed companies) | Extended-information tags on a Company relation | Professional plan only ([X-ref]); ≤3 tag fields and ≤1,000 tags per user. Foundation decision 1 is single company anyway |
| Field `groups=` (hide or make read-only by group) | Field-level permissions: visible, editable, hidden on create (§2.4.5) | Advanced mode only. Editable needs visible. Whether field rights can differ by view is unclear (V13) |
| Button `groups=` | Custom actions sit in L3 role permissions (§2.4.7) | Bulk permission editing skips custom actions |
| Followers (`message_follower_ids`) | Member, Department or Org Role field with field permission **Member** → Joined scope (§2.4.6) | Members get no notifications by being members (needs workflows) |
| Salesperson or responsible (`user_id`) as the "own documents" key | System Owner, or a Member field with field permission **Owner** | Owner rights through a field do not show in Owner filters or workflow owner steps. Keep the system Owner equal to the salesperson when filters or workflows rely on it |
| "Locked" confirmed orders and posted invoices | Views per state with edit rights only in draft views, or Owner set to Unassigned by workflow (§2.4.11) | Read-only by state is a design pattern, not a single switch (business rules are outside this slice) |
| Portal users (`base.group_portal`) and `/my` pages | External portal: external roles with views per role (§2.5) | One role per external user; web only; no mobile app; no to-dos |
| "Grant portal access" on a contact | **Invite User** (single or batch); or **Approved users** with an approval-exempt list fed by a worksheet such as Contacts (§2.5.8) | Inviting a new external user from a workflow is not documented here; [X-ref] nodes can read and update existing external users |
| Portal record rules (documents of the user's commercial partner) | Portal permission tags: a relation from the external user to their company in Contacts; documents carry a relation to that company | Documents must link to the tag sheet. Odoo links an order to a child contact; HAP needs a separate "customer company" relation for scoping |
| Portal chatter versus internal notes | **Allow discussions - Invisible internal discussions** (§2.5.4) | Mentions and replies reach externals only through the auto-created notification workflow (SMS/email) |
| Portal sign-up, 2FA, password reset (`auth_signup`, `auth_totp_portal`) | Registration by mobile or email, code or password login, 2FA, 7-day passwordless, registration window, agreement and privacy policy (§2.5.2) | Email sender is fixed at a `mingdao.com` address; SMS outside mainland China needs Twilio |
| Vendor portal (purchase RFQs and POs) | A second external role, and a personalised login link whose default role is Vendor | A contact who is both customer and vendor can hold only one external role: build a combined role |
| Quote acceptance, signature and payment in the portal | Custom actions allowed for the external role; Signature field; role action **Make Payments** (payment setup outside this slice) | Externals cannot act on approval or fill-in to-dos; portal printing and payment need live tests (V11) |
| Studio and OWL field widgets | Custom Fields (X-ref, worksheet slice) | Not in this slice; see `../../compute-for-ui.md` |
| Extra view types (map, cohort, grid, hierarchy, Gantt variants, "detail table") | **View plugins** with the `mdye` SDK (§2.6.2); samples include Map, Detail Table and Timeline | Front-end development; mobile handled by the plugin; organisation-level installation |
| Reusable server actions and Python helpers (amount in words, hashing or signing for e-invoicing, rate fetch) | **Workflow node plugins** (§2.6.3); packaged business processes (outside this slice) | Standard/Professional; a code-block plugin may need Professional (V15) |
| SQL report models (`sale.report`, `purchase.report`, `account.invoice.report`, stock reports) | **Aggregated tables**: group and sum across sheets for charts, Get Multiple Data and the API (§2.7.1) | Read-only, not a worksheet source, ≤20 aggregation fields, capacity-limited; refresh timing unclear (V16) |
| Computed stock quantities shown on the product form | None in this slice (an aggregated table cannot show in a form) | Use rollups or workflow-maintained fields (field and workflow digests) |
| Tracking and audit (`tracking=True`, audit log) | Application logs (data operations), login logs, record logs (§2.7.4) | Six-month export; user-behaviour logs need the top plan |
| Knowledge and AI (Enterprise) | Vector knowledge base, Knowledge Retrieval node, AI Agent (§2.7.2) | Paid quota; not carried by export, upgrade or backup; locks records during first vectorisation |
| Offline mobile work (Field Service, Barcode, POS) | Offline Data Submission (§2.7.3) | Simple fields only, no relations, so no product picking offline |
| Dashboards and favourites | Home page favourites (records ≤200, charts ≤10), to-dos, banner (§2.3.3) | — |
| Company branding | Org home page logo, banner and theme; app theme colour; custom SVG icons and colours (§2.3.2) | — |
| Cron and queue workers | Dedicated instance for critical workflows (§2.7.6) | Isolation only, not speed |
| Internal user / portal user / public user | Org members (and external collaborators) / external users / public forms and shared views (outside this slice) | — |

### 3.2 Selling modules separately: copy, export and import

1. **One master app is the right unit.** Duplicate drops cross-app relations, and export turns them into text unless the related apps travel together (≤20 per export). A foundation (Contacts, Products) in a separate app would make every customer copy depend on a multi-app export, and Duplicate could not be used at all.
2. **Release flow per edition (to prove with V1):**
   - **First delivery:** Duplicate the master → prune the groups the customer does not buy → test → Export (import password; lock only if the customer must not see the configuration) → the customer imports it as a new app.
   - **Each later release:** repeat the duplicate-and-prune on the new master and export again. The customer runs Import & Upgrade:
     - **Merge and Update** keeps their own additions but never removes what we dropped;
     - **Overwrite and Update** mirrors the package and moves their additions to the recycle bin.
   - Never upgrade a pruned copy with the full master package.
3. **Every copy stays source-related** (duplicates and imports share the source ID), so any pruned package can upgrade any customer copy. Keep a register of which master release and which edition each customer copy came from: the source ID is invisible.
4. **Design for portability:**
   - **References:** use worksheet and field **aliases** (they are exported) in code blocks, custom fields, Compute and API calls, not raw IDs. ID preservation across imports is not documented for SaaS; only Server's Migration Mode keeps app IDs.
   - **People:** do not name specific users in workflows or defaults. Unmatched users, departments and positions are cleared on import or upgrade. Use roles, departments, or Member fields filled at runtime.
   - **Credentials:** integration credentials and API bindings (MyInvois, e-commerce, FX rates) are re-entered per customer.
   - **Files:** attachment and print-template binaries do not travel to HAP Server.
5. **Lock with care.** A copy locked at export can never have its lock removed, and its workflows are hidden even from its admins. That suits sealed customer editions. It does not suit partner copies that must build add-ons on top.
6. **Not in any package:** role members, portal user accounts, vector knowledge bases, and data beyond the record caps. Plan an onboarding step per customer: users to roles, portal invitations, opening data through Excel import or Data Synchronization.

### 3.3 Multi-language

- **Malaysia is well covered for the UI.** English, Malay and Simplified Chinese have full system and custom-content support. Translations travel with copy, export and import. Upgrades can push language settings ("Application Language and Time Zone"), which a customer can hold back only in Merge mode.
- **Build in English as source text** and add Malay and Chinese as languages, as foundation decision 6 already says. Run Smart Translation with **Translate Empty Items Only** after each module, then review.
- **Record data needs its own design.** Odoo translates product names, descriptions, payment terms and UoM names per language; HAP never translates field values. Options:
  - extra per-language text fields on the few customer-facing masters, chosen in print templates by the partner's language (a language field on Contacts, as in foundation behaviour #5);
  - or a translation worksheet.
- **Selecting an app language changes the user's account language,** so users who work in several apps see the change everywhere.
- **Known UI gaps [Ours]:** summary line, add-button label, renamed fields. Add a language check to each module's acceptance tests.

### 3.4 Roles and field permissions

- **Use advanced mode always.** Simple mode has no field permissions.
- **One role per Odoo app and level** (e.g. "Sales / User: Own Documents", "Sales / Administrator", "Inventory / User"). Give each only its own module's worksheets, plus read access to shared foundation sheets.
  - Because merging happens only where two roles touch the same worksheet, module roles combine cleanly by union.
  - Pruning a module then means deleting its roles too.
  - Foundation sheets (Products, Contacts) are touched by many roles, so the user gets the highest rights any of their roles grant there. Decide the foundation rights centrally.
- **Mapping Odoo's levels:**
  - "Own documents" → Edit/Delete scope **Owned** (with View **All** or **Joined**).
  - "All documents" → **All**.
  - Team leads → **Subordinate** scopes from the Org Chart, or extended-information tags for sales teams. Tags need the Professional plan.
- **The record scope is per worksheet per role.** Where Odoo has different rules per menu, use separate views and, if needed, separate roles.
- **Status locks:** per-state views with edit rights only in draft views, or the documented Owner→Unassigned workflow pattern.
- **Hiding is not security.** Hidden sheets, hidden apps and Function-Switch-hidden actions can still be reached by relation, link or embedding. The record scope and field permissions are the real controls.
- **Builders:**
  - Developers can build everything except copy, export and delete; those need an Administrator.
  - A Developer sees only joined records and edits only owned ones, so test data through **Role Debugging Mode** (Multi-Select for combined roles).
  - **[Ours]:** `hap app role set-permissions -P` reset every sheet of a role on Nocoly. Change roles with a read-modify-write of the raw role model and diff afterwards.

### 3.5 Portal for customers and vendors

- **One app, two or more external roles:** e.g. "Portal Customer" and "Portal Vendor".
  - A personalised login link per audience sets the default role.
  - Permission tags (relation to the user's company in Contacts) scope what each user sees.
  - Documents need a "customer company" or "vendor company" relation for that scoping.
- **One role per external user.** A partner who both buys and sells needs a combined "Customer + Vendor" role. Per-module portal roles cannot be stacked as internal roles can, so each edition needs its own portal roles.
- **Use Approved users with an approval-exempt list** fed by Contacts (email or mobile) to imitate Odoo's "Grant portal access". Use **Invited users only** for vendor portals.
- **No to-dos for externals.** Quote acceptance or vendor confirmation must be a custom action button or a field the external role may edit, not an approval or fill-in node. Externals can follow approvals only through **Allow Viewing Approval Flowchart Details** (approvals started by Initiate Approval Flow).
- **Quota:** the organisation includes 100 external users, and the same person on two apps' portals counts twice. Another reason to keep each customer's edition in one app.
- **Malaysian deployment checks:**
  - SMS codes to +60 numbers need Twilio;
  - the email sender is documented as `sender@register.mingdao.com` (customer-facing branding risk);
  - WeChat features are irrelevant;
  - the custom URL suffix is free, but a custom domain is unclear.
- **Native portal before Compute.** It enforces HAP roles with no code. Keep Compute for the public shop or website (wave 5), where the portal's limits bite.

### 3.6 Plugins, custom fields and Compute

- **View plugins** fill Odoo view types that HAP lacks: an order-with-lines detail table, a map, a timeline, a cohort or timesheet grid.
  - They are organisation-level code: each customer organisation needs the `.mdye` imported and enabled.
  - Plugins we import from others cannot be re-exported.
  - An expiry key on our exported plugin can switch it off in a customer's organisation, which is usable as a licence control.
  - Whether an app export carries the view plugin into another organisation is not documented: the upgrade list includes "Custom view plugins", the export list does not (V8).
- **Workflow node plugins** fit shared technical steps reused across modules: signing or hashing for MyInvois, an FX-rate API call, amount in words. For whole business logic, packaged business processes (outside this slice) stay the documented tool. The export page says workflow plug-in configuration is packaged; whether the plugin itself arrives in a customer organisation is V8.
- **Custom fields and Compute are not in this slice.** The Plugin Center page calls field plugins "future", while the worksheet slice documents Custom Fields as an AI/React form control. Treat these as two different features until checked live (V14). Follow `../../compute-for-ui.md` for Compute, and note that "Dedicated Instance" here is workflow capacity, not Compute.
- **Embedding helps both ways.** HAP screens can be iframed into a Compute page or website with the hide-UI parameters (§2.3.4). A Compute site can sit on the HAP home page as an External Link app; the URL parameters it receives (user ID, email) are not authentication.

## 4. Traps

**Packaging and lifecycle**

- **T1.** Relations to other apps: converted to **text** on export unless those apps are in the same package; **not copied** at all by Duplicate (doc).
- **T2.** [Inference] Upgrade adds every item the target lacks, and restores items sitting in the target's recycle bin. A pruned customer copy upgraded from the full master gets the pruned modules back. Selective upgrade is not supported (doc).
- **T3.** **Overwrite and Update** deletes customer-made sheets, views, fields and workflows that the package lacks (recycle bin). **Merge and Update** never removes what we dropped (doc).
- **T4.** Upgrade only works between source-related apps. An app rebuilt by hand, or imported from an unrelated export, cannot be upgraded from the master (doc).
- **T5.** Record caps on export: 10,000 per worksheet, 50,000 per app; links between exported records may not all survive (doc).
- **T6.** Attachment and print-template binaries are not packaged; moving to HAP Server needs re-upload (doc).
- **T7.** Import user matching: unmatched users, departments and positions clear the related configuration (upgrade with matching off), and role members never travel (doc). [Inference] Workflows that notify a named user break in customer copies.
- **T8.** **Locked at export = locked forever.** Nobody can turn the lock off; the workflow entry is hidden; a locked app cannot be exported or copied; App Management shrinks to rename, description, logs, usage and unlock (doc).
- **T9.** Not carried by export, import, duplication, upgrade or backup: **vector knowledge-base configurations** (doc). Backups also skip role members, departments, positions, portal accounts and other apps' workflows that write to this app (doc).
- **T10.** Restore: **Restore Data** is an incremental overwrite that cannot be undone. Reference-type fields (Relationship, Subform, Cascading, File, Free Link, Department, Org-roles) cannot be restored once modified or deleted. **Restore as New App** has no data (doc).
- **T11.** Restored workflows come back **disabled** (doc).
- **T12.** App recycle bin retention: 60 days (recycle page) versus 7 days (management page) (doc conflict).
- **T13.** If the app owner leaves, the app passes to the Business Assistant and can no longer be deleted (doc).
- **T14.** Maintenance mode does **not** stop workflows, worksheet APIs, public forms, public queries or shared records/views (doc). Integrations keep writing during a module upgrade.
- **T15.** Plan statements conflict: export/import "paid editions" (import-export page) versus Free included ([X-ref] plan comparison). Several pages quote RMB, WeChat Pay and "Ultimate Edition" (Mingdao text).

**Language and time**

- **T16.** Record values are never translated, nor Formula, Concat, Auto Number or Uppercase outputs, nor comments (doc).
- **T17.** A translation needs content in the reference language. Rich Text is not smart-translated. 5-minute cooldown after Smart Translation (doc).
- **T18.** Choosing an app language overwrites the user's personal account language (doc).
- **T19.** Tamil is not in the supported list. External-link apps pass only `en`, `ja`, `zh-hant` and `zh-hans` as the language parameter, no Malay value (doc).
- **T20.** [Ours] Worksheet summary line never translated; add-button label needs a custom name first; a field rename leaves the old translation.
- **T21.** Date filters use the **app** time zone while display uses the **personal** one (doc). Set the app zone before building date-filtered views.

**Roles**

- **T22.** Simple mode has **no field-level permissions** (doc).
- **T23.** The record scope applies to **all views of the worksheet**; different scopes per view need multiple roles (doc).
- **T24.** **Add** is per worksheet, not per view (doc).
- **T25.** Multi-role merge is a union of the highest rights per view. An extra role can widen access unexpectedly, but rights never apply where L1 is off in that view (doc).
- **T26.** Function Switch versus role actions: the **more restrictive** wins (doc). A missing print or export button may come from either.
- **T27.** Hiding a worksheet from navigation, or hiding an app, is **not** access control: relations, links, notifications and embedded views still open them (doc).
- **T28.** Owner-level rights given through Member, Department or Org Role fields do **not** fill the system Owner field, so Owner filters and workflow owner steps ignore them (doc).
- **T29.** A worksheet's data needs at least one visible view for the role (doc). [Inference] Give line sheets reached through relations (order lines) a view, then hide them from navigation, as the doc's order-details example suggests.
- **T30.** An editable field must also be visible (doc).
- **T31.** Developers see only joined records and edit only owned ones. Operators manage all data but cannot change configuration. Neither can copy, export or delete the app (doc).
- **T32.** Extended-information tags: ≤3 tag fields, ≤1,000 tags per user per field (more are silently ignored), Professional plan ([X-ref]) (doc).
- **T33.** Copying a role copies its permissions, not its users. Deleting a role asks where its members go (doc).
- **T34.** [Ours] `hap app role set-permissions -P` returned success but reset every sheet of the role to "own records" on Nocoly. A rule that reads back correctly can still fail on screen: check with Role Debug.

**Portal**

- **T35.** **One external role per external user** (doc).
- **T36.** External users have **no to-dos**: no approvals, fill-ins, CC or internal notifications (doc).
- **T37.** Web only (PC browser, mobile browser, WeChat browser); no App, no mini program, no third-party login (doc).
- **T38.** Each app's portal registration is a separate account and a separate quota use; 100 external users are included per organisation (doc).
- **T39.** Email sender fixed as `sender@register.mingdao.com`. SMS outside mainland China needs Twilio. The login-code SMS text cannot be changed. Including a link forces the platform signature (doc).
- **T40.** The first switch from "View all discussions" to "Invisible internal discussions" moves **all existing discussions** into the internal area, out of external users' sight (doc).
- **T41.** External users get no app notifications for mentions or replies until the auto-created workflow is configured and published (doc).
- **T42.** The approval flowchart is visible to externals only for approvals started by the **Initiate Approval Flow** node (doc).
- **T43.** Registration links spread easily. **Anyone** lets anyone in; use **Approved users** or **Invited users only** for business portals (doc).
- **T44.** The approval-exempt match is exact on the mapped fields: mobile or email, plus collected fields if mapped (doc). Formatting differences (+60 prefixes, case) will fail the match [Inference].
- **T45.** Maintenance mode locks out portal users too (doc).
- **T46.** Custom URL: only the suffix can change, per the portal page, while the role matrix mentions editing a custom domain name (doc conflict).

**Plugins and add-ons**

- **T47.** View plugins run in an iframe and must handle mobile layouts themselves (doc).
- **T48.** Imported plugins cannot be exported again. An expiry key disables the plugin for the whole importing organisation (doc).
- **T49.** Only organisation app admins manage org plugins. A plugin is usable only in its debug app until published and enabled. New version numbers must be higher. The plugin library is unavailable (doc).
- **T50.** A workflow node plugin's newest version is not automatically the live one: set **Current Version** (doc).
- **T51.** Aggregated tables are read-only, cannot be a worksheet source, allow ≤20 aggregation fields, and calculation fields work only on aggregation fields. Field names with `@@` or a backtick cannot be used. Capacity is a paid quota. They are excluded from Market and App Library packages (doc).
- **T52.** Vector KB: the source worksheets are frozen (no add, edit or delete) while vectorisation runs (doc). Never start it on live ERP sheets during working hours [Inference].
- **T53.** Offline submission: no relation fields; option fields only with custom options (not option sets); rules and permissions run only at manual submission; no batch submit (doc).
- **T54.** A dedicated instance gives isolation, not speed (doc).
- **T55.** Hide-UI URL parameters are reliable only in an iframe (doc). External-link URL parameters (user ID, email) are not authentication [Inference].

## 5. To verify live

Tests for later; none were run for this digest. Use a throwaway copy, not the master, for anything that writes.

| # | Doc claim to test | Why it matters for the build | How to test on Nocoly SaaS |
|---|---|---|---|
| V1 | Upgrade adds items the target lacks; Merge keeps extras; Overwrite deletes them; not selective | The prune-per-edition release flow (§3.2) | Copy A of a small test app; copy B pruned (one group deleted). Upgrade B from A's export (Merge, then Overwrite on another copy); list what comes back. Then upgrade B from a pruned package |
| V2 | Which objects an upgrade really updates: the list names sheets, views, view plugins, fields, workflows, workflow plugins only | Custom pages, charts, print templates, roles, portal settings, option sets, business rules, custom actions and language packs may not follow | Change one of each in the source, upgrade a copy, read back each object |
| V3 | Worksheet, field, view and workflow IDs across Duplicate and export/import (only Server's Migration Mode keeps app IDs) | Code, custom fields, Compute and the register match by ID | Compare `hap app info` and worksheet structures of the original and the copy; check that aliases survive |
| V4 | Cross-app relations become text on export and vanish on Duplicate | Foundation placement | Two test apps with one relation; Duplicate one; export one alone and both together |
| V5 | A locked export: what the importing admin can do; can it be upgraded without unlocking | Sealed customer editions | Export a test app with the lock; import into a test organisation or as a new app; try Import & Upgrade before and after unlock |
| V6 | Plan entitlements of our organisation | Localization, backup, recycle bin, extended info, workflow plugins, code block, PBP and global variables depend on Standard vs Professional | Org Admin > Home > Organization Quota and the plan page (read-only) |
| V7 | Localization on our plan: Malay system text, Smart Translation quality, which objects appear in the language tree (print templates, custom-action names, workflow messages, portal texts) | Malay/Chinese editions | Add Malay to a test copy, run Translate Empty Items Only, switch language as a test user |
| V8 | Do view plugins and workflow node plugins travel with an app export into another organisation? (the upgrade list says view plugins; export says workflow plug-in configuration) | Modules sold with plugins | Export an app that uses one plugin of each kind into a second organisation; check the view and the node |
| V9 | External-user permission tags and role scope: an external user linked to a company in Contacts sees only that company's orders and invoices | Customer and vendor portals | Test portal with two companies and two external test users (test values only); read the views as each |
| V10 | Can an External User member field give portal users Owner or Joined record scope? | Simpler portal scoping than tags | Test record with an external user in a member field set to Owner or Member; check access |
| V11 | What portal users can do on a record: custom action buttons, System Print/PDF, attachment download, Make Payments, signature field | Odoo "sign and pay" and invoice download | Enable each action for the external role in a test app; try as an external test user |
| V12 | Portal messages on Nocoly: email sender address, SMS to +60 without Twilio, custom domain option | Customer-facing branding and Malaysian logins | Portal Settings > Message Settings and Basic, read-only; send only with approval, to our own test number |
| V13 | Field permissions: per worksheet or per view; do they apply to subtable (order line) fields | Line-level price and discount locks | Role with a field locked on the order and on the line sheet; check in Role Debugging Mode |
| V14 | Custom fields exist on our tenant (worksheet control) although the Plugin Center calls field plugins "future"; what they store; per-sheet limit | Native-first UI choices | Add one stored and one reference-only custom field in a test sheet (`../../compute-for-ui.md` check 9) |
| V15 | A workflow node plugin containing a code block on our plan | Shared technical steps | Create a trivial plugin in a test organisation or app; publish to test only |
| V16 | Aggregated-table freshness (the page promises live updates, yet offers a manual **Resynchronize**) and our quota | Odoo report replacements | Small aggregated table over two test sheets; add a record; time until the preview changes |
| V17 | App recycle-bin retention: 7 or 60 days | Recovery promises to customers | Read the retention shown in Org Admin > App Recycle Bin (read-only) |
| V18 | Role debugging for the Developer role; Multi-Select merges as documented | Build and acceptance testing | Developer test account in a test copy |
| V19 | Approval-exempt list from a worksheet: exact-match behaviour with Malaysian phone formats | "Grant portal access" emulation | Exempt list on a test Contacts sheet; register with +60 and 0-prefixed numbers |
| V20 | Translations, roles and portal settings after Duplicate (docs say languages survive; portal settings are in export) | Customer copies must arrive complete | Duplicate a test app with Malay added, one portal role and one custom role; compare |

## 6. Coverage

All 44 pages of the slice were read in full: offsets 0–43 of `read_pages.py --prefix application,role,portal,plugin,extensions`. Page 29 was split into parts because of its length; it holds the same guide twice.

| # | URL | Title | Summary |
|---|---|---|---|
| 0 | https://help.nocoly.com/application/add-member | Add Members to an Application | Access path app > section > worksheet > view; create a role, assign views, record scope and field rights, add users or departments |
| 1 | https://help.nocoly.com/application/aggregation | Aggregated Table | Virtual multi-sheet summary (group, Sum/Max/Min/Average/Count/Distinct count, ≤20 aggregation fields, calculation fields) for charts, Get Multiple Data and API; read-only |
| 2 | https://help.nocoly.com/application/app-time-zone | Application Time Zone | App time zone is the common basis for date filters in sheets, rules and charts; display follows the personal time zone |
| 3 | https://help.nocoly.com/application/appofflinesubmit | Offline Data Submission | Mobile offline entry for chosen sheets; simple field types only; rules and permissions checked at manual submission |
| 4 | https://help.nocoly.com/application/backup-restore | App Backup and Restore | Manual and scheduled backups with optional data; restore in place or as a new app; contents and restore semantics |
| 5 | https://help.nocoly.com/application/building | How to Create an Application | Four ways to create an app and the build order: sheets, views, roles, workflows, charts |
| 6 | https://help.nocoly.com/application/er | ER Diagram | Diagram of an app's sheets and relations (one/two-way, 1/N), focus mode, field editing, export |
| 7 | https://help.nocoly.com/application/exclusive-computing-power | Dedicated Instance | Purchased workflow concurrency (20/50/100) that isolates critical workflows; not faster; ≤5 per organisation |
| 8 | https://help.nocoly.com/application/external-link | Add External Application Links | Home-page entries that open external URLs with user and system parameters; platform visibility; owner/admin/member |
| 9 | https://help.nocoly.com/application/group | Application Grouping | Home-page app groups: system (All, Owned, External Collaboration) and personal or organisation groups; starring, display, order |
| 10 | https://help.nocoly.com/application/hide-area | Hide UI Areas in Applications | URL parameters (`s`, `tb`, `tr`, `td`, `ac`, `ln`, `rp`, `ch` = `no`) to hide UI parts when embedding in an iframe |
| 11 | https://help.nocoly.com/application/homepage | Home Page | Org logo, slogan, banner and theme; user to-dos, recent items and favourites (records ≤200, charts ≤10) |
| 12 | https://help.nocoly.com/application/import-export | Export and Import Applications | `.mdy` export (≤20 apps, record caps, import password, configuration lock), contents list, relation handling, import and user matching |
| 13 | https://help.nocoly.com/application/introduction | What is an application? | Seven building blocks: worksheet, view, role, chart, workflow, custom page, external portal (older counts) |
| 14 | https://help.nocoly.com/application/language | Application Localization | System and custom content translation, language list (full: zh-Hans, zh-Hant, en, ja, ms, th), base language, Smart Translation, display priority |
| 15 | https://help.nocoly.com/application/library | Introduction to App Library | Install or download template apps; upload own apps for approval; paid downloads planned |
| 16 | https://help.nocoly.com/application/lock | App Lock | Owner locks an app with a password; restrictions while locked; per-user unlock; export lock is permanent |
| 17 | https://help.nocoly.com/application/log | Application Logs and Login Logs | App logs (management, data operations, user behaviour), login logs, org admin logs; six-month export; API |
| 18 | https://help.nocoly.com/application/maintenance | Application Maintenance | Maintenance mode with an announcement: members and portal users blocked; admins, workflows, APIs and public shares keep working |
| 19 | https://help.nocoly.com/application/management | Application Management | Org admin app list: enable, disable, delete, owner change, join any app, batch import/export, recycle bin, decrypt `.mdy` passwords |
| 20 | https://help.nocoly.com/application/navigation | Worksheet Navigation Settings | Navigation styles, 3 levels with groups at levels 1–2, icons, last item, hidden items, mobile List/Matrix/Tab Bar |
| 21 | https://help.nocoly.com/application/operations | Common Application Operations | Name, colour, icon, description; duplicate (configuration only); delete or leave; groups; publish; maintenance; backup; option sets |
| 22 | https://help.nocoly.com/application/plan-design | How to Plan and Design an Application | Function → app, process → group, object → worksheet, status → view; views drive access control |
| 23 | https://help.nocoly.com/application/publish | Application Publishing | Platforms (PC, Mobile App, Mobile Web), third-party workspaces, links with hidden UI, maintenance |
| 24 | https://help.nocoly.com/application/recycle | Recycle Bin for Applications, Worksheets, Views, Fields, Records, and Workflows | 60-day recycle bins per object type, who may restore or purge, restore rules |
| 25 | https://help.nocoly.com/application/settings | General Application Settings | Org custom SVG icons and custom theme and chart colours |
| 26 | https://help.nocoly.com/application/upgrade | Import and Upgrade Applications | Upgrade between source-related apps: Merge vs Overwrite, change review, held-back settings, user matching, bulk upgrade, Server Migration Mode |
| 27 | https://help.nocoly.com/application/usage-analysis | Usage Analysis | Organisation totals and daily trends, by app and by member; Excel export |
| 28 | https://help.nocoly.com/application/vector-knowledge-base | Vector Knowledge Base | Vectorised records, files and discussions for semantic retrieval in workflows and AI Agent; chunking, retrieval modes, quotas, pricing |
| 29 | https://help.nocoly.com/extensions/developer/view | View Plugin Development Documentation | Building custom views: `mdye` CLI and SDK, settings parameters, debug, push, publish, versions, `.mdye` export keys, samples |
| 30 | https://help.nocoly.com/plugin/extensions-api | extensions-api | Empty in the cache (no text) |
| 31 | https://help.nocoly.com/plugin/introduction | Plugin Center | View and workflow-node plugins now; field and custom-page plugins announced for later |
| 32 | https://help.nocoly.com/plugin/node | Workflow Plugin - Custom Node | Package branch, AIGC, API, code and JSON steps into a reusable node with inputs and outputs; publish and versions |
| 33 | https://help.nocoly.com/portal/faq | Frequently Asked Questions About External Portals | WeChat login, per-app accounts and quota, identity types and their feature limits |
| 34 | https://help.nocoly.com/portal/introduction | External Portal | Portal setup: URL, login page, methods, access types, discussions, notifications, info collection, SMS/email, external roles, invitations, approval list, statistics, restrictions |
| 35 | https://help.nocoly.com/portal/management | External Users and External Collaborators | Org-level management of external users (capacity, auto-purchase) and external collaborators |
| 36 | https://help.nocoly.com/role/creator-owner-joiner | Record Creator, Owner, Member, and Joined User | Record identities and how Owner or Member rights come from member, department and org-role fields; roles still decide |
| 37 | https://help.nocoly.com/role/debugging | Role Debugging Mode | Switch to one or several roles to test permissions, also on mobile |
| 38 | https://help.nocoly.com/role/extended-info | Extended Information about Users | Mapping sheet turns relation fields into permission tags (≤3 tag fields, ≤1,000 tags per user) |
| 39 | https://help.nocoly.com/role/introduction | Introduction to Roles and Permissions | RBAC overview and the common permission scenarios |
| 40 | https://help.nocoly.com/role/multi-role-permission | Permission Rules for Users with Multiple Roles | Union per worksheet, view and level; L1 operations gate L2 record scope and L3 fields, features and custom actions |
| 41 | https://help.nocoly.com/role/operations | Role and User Management | Create, edit, copy, delete, reorder roles; User tab; ownership transfer; visibility and notification switches |
| 42 | https://help.nocoly.com/role/permission-configuration-example | User and Role Permission Configuration Examples | Self-service profile with field locks; status-based edit locks by views or by clearing the Owner in a workflow |
| 43 | https://help.nocoly.com/role/type-configuration | Application Roles and Permission Configuration | Role types, simple vs advanced mode, four permission levels, actions, bulk configuration, hiding, adding members, operator/developer matrix |
