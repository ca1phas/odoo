# Org, collaboration, FAQ and other pages: native HAP digest

| | |
|---|---|
| Slice | `--other --exclude integration,api,ai,getting-started`: 88 cached pages (org, faq, account, purchase, task, calendar, post, file, group-chat, entra, feishu, dingtalk, wecom, the home page and two zh-Hans pages) |
| Pages read | 88 of 88 from the cache, plus 39 uncached unlisted pages and the pricing page read live (§7) |
| Written | 23 Nov 2026, read-only. No app, workflow or other file was changed |

**Marks used**
- Plain statements are help.nocoly.com docs as cached on 3 Nov 2026. They are docs, not runtime proof.
- **[live 23 Nov]** means read on the live site on 23 Nov 2026. Still docs, not runtime proof.
- *Inference:* is my own reasoning; the docs do not say it.
- **Conflict:** means two sources disagree; both are kept.
- Menu paths are copied as each page prints them. Several pages spell the same menu differently (see §4, trap 40).

## 1. Summary

1. The org directory is HAP's native backbone for users, employees and teams: members (paid seats), a department tree with several managers per department, job titles, work locations, employee IDs, organisation roles in role groups with "responsible departments", and a separate org chart with one manager per member.
2. Approvals, notifications, view filters and app-role permissions read the directory natively: department manager, org-chart manager, org-role members, or the role member responsible for the submitter's department. A primary department settles members who sit in several departments.
3. Offboarding has a handover tool for pending approvals, workflow-node assignees and app roles. It does not move record owners or member fields.
4. SaaS limits that shape the data model: 200 fields per worksheet; 1,000 subform rows; rollups, stored foreign fields and Get Multiple Data through a relation stop at 1,000 related records; Update Record handles 100 rows per run; Excel import takes 20,000 rows; the API returns 1,000 rows per call and allows 20 writes per second per IP.
5. The Standard plan stops at 100 worksheets and has no Code Block, Loop node, global variables, condition groups, extended user information, Super Search, contacts visibility or data encryption. Those need Professional.
6. A unique index (composite allowed) gives native uniqueness, but an optional field can then be empty in only one record of the worksheet.
7. Mobile hardware: PDA laser scanning into fields, continuous scanning, hardware keys that press HAP buttons, Bluetooth label printing (CPCL/TSPL, App only) and NFC tags that open records.
8. Messaging: SMS to numbers outside Mainland China goes through the customer's own Twilio account; the docs cap email at 10 per hour per recipient mailbox; webhooks, API calls and code blocks leave from 5 fixed Hong Kong IPs.
9. Calendar, Task, Post, Groups and Files form a collaboration suite outside app data. It suits Discuss-style chat and announcements; Odoo Calendar, Project and Documents need worksheets.
10. Native online payment, refunds and e-invoicing exist only for China (WeChat Pay/Alipay, China tax account) and sit on unlisted pages. Malaysian payment gateways and MyInvois need integrations (*inference*).

## 2. Capability inventory

### 2.1 Organisation directory

#### Members
- **What it does:** a member is a personal HAP account that has joined the organisation. Admins keep the organisation information: department(s), job title ("position"), org role, employee ID, work location, work phone. Name, phone and email belong to the personal account, and only the member can change them.
- **Inviting:**
  - Contacts (`E`) > **Add Contact**: **Public invitation** (link, QR code or organisation ID; always needs admin approval), **Targeted invitation by mobile/email**, **Invite from Contacts**.
  - `Org Admin > User & Department > Add User`: name, email or mobile, department, position.
  - Bulk import from the provided template. HAP sends the invitation SMS or emails.
  - Import fields: Telephone / Email, Name, Department, Job title, Role, Employee ID, Work location, Work phone. Departments, job titles and roles that do not exist yet are created. Department levels are separated with `>`.
- **Lists:** **Not Activated** (resend or cancel invitations, also in batch); **Pending** (join requests; the **Rejected** list can be re-reviewed).
- **Several departments:** a member can hold positions in several departments ("All Positions" then appears on the profile) and must have one **Primary Department** (`Set as Primary Department`). The primary department is listed first, and member pickers show only the primary department. In approvals, a "department head" step can go to every department's head or only to the primary department's head.
  - **Conflict:** the member page says the profile card shows only the primary department; the security page says profile pages and cards show all departments and job titles.
- **Batch edit:** department, position and work location only. Batch offboarding. Export all members or one department (`Import/Export/Update > Export/Update`).
- **User ID:** unique per user. Copy it from the Contacts profile panel or export it in bulk. Used to match users in imports and in batch offboarding.
- **Limits:** non-paying organisations can import 100 members per day per IP and user; paid organisations have no import limit. Free plan: 10 users at most, no seat expansion.
- **Where the data shows:** member pickers inside the organisation show department and job title from the organisation information (primary department only). Pickers opened from All Contacts or Friends show the personal organisation name and job title. Profile cards in apps and organisation groups show organisation information; in Messages, Workflow To-Dos and personal groups they show personal information.
- **Source:** https://help.nocoly.com/org/member-management, https://help.nocoly.com/account/modify, https://help.nocoly.com/account/faq, https://help.nocoly.com/purchase/online-purchase

#### Joining rules
- **Where:** `Org Admin > Security > Contacts > Rules for user joining` (also `User & Department > Invite More > Rules for User Joining`).
- **Options:**
  - **Enrollment Approval** on/off: users invited by non-admin members need admin approval.
  - **Approval-free join:** users invited by admins by phone or email join without approval.
  - **Mandatory approval:** joins through a public invitation link or a Door ID search always need approval.
  - **Join via Organization Door ID** on/off.
  - **Identity Information Collection:** fields the applicant must fill in, such as department, job title, work location and employee ID.
- **IDs:** the Organization Door ID is 6 digits (`Profile Picture > My Org`). The Organization ID is in `Org Admin > Org Info` (not on mobile) or at the end of the Org Admin URL.
- **Source:** https://help.nocoly.com/org/security, https://help.nocoly.com/org/member-management, https://help.nocoly.com/org/id

#### Departments
- **What it does:** the department tree used across Contacts, apps, permissions and workflows; for example, a department manager as approver.
- **Where:** `Org Admin > User > User & Department`.
- **Options:** **Add** (name); per department: **Add Subdepartment**, **Edit** (name, parent department, department managers), **Copy department ID**, **Refresh department member information**, **Disable**, **Delete**. Drag to reorder or move under another department. Members can be pinned and reordered; that order is used in Contacts and member pickers.
- **Managers:** chosen from the department's own members. Several managers are allowed.
- **Disable:** the department disappears from Contacts and from member and department pickers (such as Department fields). Records that already reference it keep it, shown with a strikethrough. Admins still manage it and can re-enable it. Sync and import into a disabled department still work. Exports mark it **Disabled**.
- **Delete:** move all members out first. If records reference the department, the docs recommend disabling instead.
- **Import/export:** `More` next to Department > **Import Departments** / **Export Departments**. Template headers start on row 2. Each row gives the full **department path** from the top, levels separated by `/`. Parent departments must already exist. A path equal to the name means a top-level department.
- **Source:** https://help.nocoly.com/org/department-position

#### Job titles and work locations
- **Where:** `Org Admin > Organization > Org Info`, **Setting** under **Job Title**. Work locations are kept in Org Info too.
- **Options:** **Create Job Title**, rename, delete; per title: **Add User**, remove or export members; `More` > **Import Job Title** / **Export Job Title**.
- **Limits:** a job title with members cannot be deleted. Import rejects titles that already exist and marks the duplicate rows. Template headers start on row 2.
- **Source:** https://help.nocoly.com/org/department-position, https://help.nocoly.com/org/basic-info

#### Organisation roles
- **What it does:** groups members across departments by skill, function or project (examples in the docs: "Sales Consultant", "Finance Specialist", "Backend Developer"). Used for permissions, member selection and workflows.
- **Where:** `Org Admin > User > Role`.
- **Options:**
  - **+ Role** (name, role group, notes); bulk creation by import; edit, disable, delete.
  - **Role groups:** **+ Group**; a built-in **Default** group that cannot be edited.
  - **Members:** **Add User**; a member can hold several roles; remove or export members.
  - **Responsible departments:** each role member can be given one or more departments they are responsible for. With none, the member counts as responsible for **All Members** (shown as `-`).
  - **Disabled roles:** hidden from all role pickers, shown with a strikethrough in existing records, still manageable by admins, still reachable by import and sync, marked **Disabled** in exports. `More > Show Disabled Roles > Reactivate`.
- **Used in:** Organization Role fields in worksheets; adding all members of an org role to an app role at once; approval steps (members of a role as approvers); department-based approvers (the role member responsible for a department).
- **Limits:** up to 50 role groups. A role group that still holds roles cannot be deleted.
- **Source:** https://help.nocoly.com/org/roles

#### Org chart (reporting lines)
- **What it does:** manager and subordinate links between members. Each member has at most one manager and any number of subordinates. It is separate from the department tree and from department managers.
- **Used in:**
  - view filters: records of the current user's subordinates can be included;
  - app-role data permissions: access to records related to a member's subordinates;
  - workflows: the manager of a member in approval, notification, fill-in and other nodes.
  - Also the Task module's **Subordinates' Tasks** list and the fallback list of frequent collaborators.
- **Where:** `Org Admin > User > Org Chart`. **+ Add Subordinate** next to the organisation name adds a top-level member; several top-level members are allowed. `More` on a member: add subordinate, replace member, remove from the chart. Removing a member keeps their own subordinate links; they reappear if the member is added back.
- **Settings:** **Allow Employees to Manage Their Subordinates**; **Allow All Employees to View the Org Chart** (otherwise employees see only their manager and subordinates). Employees use `My Org > My Org Chart` and cannot set their own manager.
- **Source:** https://help.nocoly.com/org/reporting-structure, https://help.nocoly.com/task/faq, https://help.nocoly.com/faq/all-members

#### Organisation groups
- **What it does:** chat groups that also serve as visibility scopes (posts, shared projects, batch-adding folder collaborators).
- **Types:** **organisation groups** (managed by the creator and org admins; members who leave the organisation are removed) and **personal groups** (managed only by group admins, invisible to org admins, leavers stay). The type cannot be changed later.
- **Official group:** bound to a department, shows a **V** badge, and new members of the department are added automatically.
- **Admin page:** `Org Admin > User > Groups`: set or change group admins, manage members, associate groups with departments, enable or disable, disband, mark official, create groups. A closed group can be reopened here.
- **Source:** https://help.nocoly.com/org/group-management, https://help.nocoly.com/group-chat/create, https://help.nocoly.com/group-chat/operations, https://help.nocoly.com/group-chat/introduction

#### External users
- **Collaborators:** HAP users from outside the organisation can be invited to groups by mobile number or email. They are "not counted as billable users". They see only the groups, projects, tasks and shared folders they are added to; in apps, access follows their roles. Posts shared with "All Colleagues" stay hidden from them. Their profile cards carry a **Collaboration** label.
- **Former employees:** after offboarding, a person can be invited back to specific apps and groups as an external collaborator.
- **External user seats (portal):** a paid plan includes 100 external user seats. More come in packs (monthly or annual), bought under `Org Admin > User > External User > Expand`; not available on Free or Trial. Only active users use seats (not Pending Review, Pending Activation, Disabled or Deleted). "If a user registers and joins two applications, they count as 2 users." Auto-purchase can add 100 seats when fewer than 20 remain.
- *Inference:* the seat rules apply to external portal users, while group collaborators are a different, non-billable kind of external user. The portal itself is in the portal slice.
- **Source:** https://help.nocoly.com/group-chat/invite, https://help.nocoly.com/purchase/online-purchase, https://help.nocoly.com/org/home, https://help.nocoly.com/org/handover-terminate-restore

#### Work handover, offboarding and restore
- **Handover** (`User & Department`, the member's `More` > **Handover**). Several handovers to different successors are allowed. Items:
  - pending workflows: approval and fill-in tasks waiting for the person;
  - workflows that name the person in a node (approver in an approval node, owner in an Update Record node, and so on);
  - app memberships: remove the person from several apps, or transfer their app roles to someone else.
  - Not included: member fields and record owners in worksheet records.
- **Offboard** one member, a selection, or by User ID (one per line). Up to 50 per batch.
- **Effects of offboarding:**
  - removed from the organisation, every app, and every group, task and project;
  - apps they owned, and groups, tasks, projects and shared folders they owned, go to **Assistant**;
  - no more access to organisation data, even through old notifications.
- **After offboarding:** `User & Department > Offboarded`, `More` > **Handover** for app workflows (recommended before offboarding). **Handover Collaboration** moves one item, several, all, or **One-click Handover** (groups, projects, tasks, shared folders, approvals). Collaboration items can only be transferred after offboarding.
- **Manual follow-up:** app ownership under `App Management > App`; records by filtering on the owner (the user picker offers an **Offboarded** option) and bulk-updating owner and member fields.
- **Restore:** `Offboarded > More > Restore`. App and group memberships are not restored.
- **Source:** https://help.nocoly.com/org/handover-terminate-restore

### 2.2 Organisation administration

#### Org Admin sections
- **Home, User, Organization, App Management, Payments & Invoicing, Integration, Security, Log.** Opened from `Profile Picture > My Org > Org Admin` or the **Org Admin** link on the home page.
- Source: https://help.nocoly.com/org/management-module

#### Organisation settings
- **Org Info:** logo, name, short name, **Country/Region**, **Time Zone**, Door ID, Organization ID, identity verification, subdomain, job titles, work locations.
  - **Country/Region** sets the default country of region/city fields, the default currency of currency fields and the default calling code of telephone fields in apps.
  - **Time Zone** sets the default time zone for apps in the organisation.
- **Close an organisation:** Free or trial organisations only. Members lose access at once; after 90 days the apps go to the Recycle Bin, and 60 days later they are deleted. A closed organisation can be restored from `My Org`.
- **Billing:** credit and AI free credit balances, purchases, payment and usage records, invoices. **Switch to New Version** opens the new Billing Center: **Statistics** (credits used this month, total purchased, total used; by category, app and period) and **Details** (filter by product type, period and app; export).
- **Misc.:** **Announcement** to selected members (in-app notification, direct message, email and more) and **Usage Statistics** (user activity ranking, posts, documents, images). The pricing page lists "Usage analysis" as Professional only **[live 23 Nov]**.
- Source: https://help.nocoly.com/org/basic-info

#### Admin home: seats, credits, quotas
- **Edition and expiry** with **Renew**; **Member Seats** (active members against the limit) with **Expand** and **Invite Users**. Trial organisations get Professional features and limits, with no member limit during the trial.
- **Credits:** 1 credit = USD 1. They pay for workflow automation, SMS, email and AI. **Credits Alert** sets a low-balance threshold.
- **Auto-purchase add-ons** (`Manage`):
  - Workflow Execution Add-on when less than 2% of the monthly quota is left;
  - Synchronization Task Compute Capacity Add-on when less than 2% of the monthly quota is left;
  - File Upload Add-on when less than 2% of the annual quota is left;
  - External User Add-on: 100 more when fewer than 20 are left;
  - Mingo AI features: AI Free Credits first, then credits at 20 credits per million tokens (can be switched off).
- **AI Free Credits** refresh on the 1st of each month and do not roll over.
- **Organization Quota:** core resources (apps, worksheets, records, direct sync tasks, ETL tasks) are "typically not subject to quota limits in the current edition" but are counted. Quota-limited resources (aggregated tables, external portal users, vector knowledge bases, vector chunks) have fixed limits with **Expand**. **Usage Analysis** shows trends.
- Source: https://help.nocoly.com/org/home

#### Permission groups (organisation administrators)
- **Where:** `Org Admin > Organization > Permission Management`, **+ Permission Group**.
- **Super Admin** group: fixed, full rights, cannot be edited or deleted.
- **Custom groups** (examples: Organization Admin, App Admin, Integration Admin) with two tabs:
  - **Manage Permission:** which admin modules and operations (users, organisation, apps, integrations, ...).
  - **Feature Permission:** App Development (**Create apps**, **Delete apps**, **Create API connections**, **Create sync tasks**, **Create plugins**); Mingo AI (**App planning and building**, **Data queries**, other app assistance such as creating worksheets or sample data); **Global Search (Search Records)**.
  - **Allow Members to Manage Others:** group members can add or remove members of the group.
- **Default Feature for All Members:** features every member gets; when off, only permission-group members get them.
- **Permission requests:** with **Allow Permission Requests** on, members ask to join a group from Org Admin; Super Admins **Grant Access** or **Reject**.
- **Logs:** `Org Admin > Log` records group creation, configuration and membership changes.
- Source: https://help.nocoly.com/org/administrators

#### Security settings
- **Where:** `Org Admin > Security`.
- **Contacts visibility** (`Security > Contacts > Contacts Visibility`). Three rule types:
  - **Restrict Viewing Other Departments:** selected members see only their own department, plus **additional visible members** (departments or users).
  - **Restrict Viewing All Users:** selected members see no contacts, except listed visible users. The docs' example is agents who should not see colleagues.
  - **Hide from Everyone:** hides chosen users from Contacts, app-member pickers, group invitations and @mentions. User level only, not by department or job title.
  - A **whitelist** exempts users when a rule targets a department or org role.
  - **Priority:** an individual's rule beats their department's. A sub-department follows its own rule if it has one, otherwise its parent's. For members of several departments: if one department is unrestricted they are unrestricted; if all are restricted, they see the union.
  - **Effect:** hidden users and departments vanish from Contacts, @mention lists and member selection dialogs.
  - **Plan:** "Contacts visibility" is Professional only on the pricing page **[live 23 Nov]**; the cached plan page says "Hidden contacts: Professional".
- **Member information display:** which fields show on profile pages and cards. The Department field shows either the name only or the full path. Members of several departments show all of them. Phone or email set to "visible only to you" stays hidden from others (admins still see it).
- **Screen watermark** (`Security > Data & Access`): name, last 4 digits of the phone, email, organisation name, or a fixed text of up to 20 characters. Shown on the Org Admin pages, app home, record create and edit pages, views, custom pages (also when saved as image), user management (including portal management) and the workflow list. Not shown on form or workflow configuration pages.
- **API Access Policy:** whether members may call APIs through platform-level OAuth applications and/or Personal Access Tokens.
- **CLI Access Policy:** when disabled, the CLI can no longer reach organisation data with a user's identity.
- **API Proxy:** routes the **Send API Request** node and Integration Center API requests through a proxy. An HTTP-only proxy does not carry HTTPS requests, and the other way round. Professional only (plan page).
- **Field encryption rules** (`Security > Data & Access > Encryption Rule`): methods **AES128, AES192, AES256, SM4**. Each organisation gets a default AES rule with a random key; system-generated rules cannot be changed or deleted. Super admins can add rules, pick the default, enable or disable rules, and list the fields that use a rule. Fields are then encrypted in the worksheet settings (worksheet slice). "Data encryption" is Professional only.
- **Feature restrictions** (`Security > Feature > Member Feature Control`): limit **creating apps**, **deleting apps**, **creating API connections** and **developing plugins** to app administrators. All off by default. See trap 41 on how this overlaps with permission groups.
- **Passwordless Policy** (`Security > Feature > Passwordless Policy`, **Operation Without Verification**): after one successful password check, users can skip the check for 1 hour on custom buttons and approvals that ask for the login password. Off means a check every time.
- Source: https://help.nocoly.com/org/security, https://help.nocoly.com/purchase/version-comparison

#### Identity verification and SMS signatures
- This page is unlisted on the Nocoly site **[live 23 Nov]** and is written for mainland China (WeChat facial verification, China carriers). *Inference:* it may not apply to Nocoly as written.
- **Restricted features:** inviting users (Free users need personal verification); inviting into groups and inviting organisation members (Free/Trial); buying credits (Free/Trial); changing SMS signatures (enterprise verification, everyone); publishing to the Marketplace; **sharing externally** (Free/Trial organisations need enterprise verification for record, view, custom page and chart shares, public forms, public queries, the external portal, the Get Link node and ChatBot sharing).
- **Multiple business entities** can be verified; SMS signatures and e-invoicing tax IDs are set per entity.
- **SMS signatures:** reviewed by carriers in about 5 business days (10 for trademarks). The default signature is the Chinese name of Mingdao Cloud. Messages whose links use a HAP domain must use that signature.
- Source: https://help.nocoly.com/org/certification

#### Integrations page (Org Admin > Integration)
- **Org Integration:** WeCom, DingTalk, Feishu/Lark, WeLink, Microsoft Entra. Only one platform per organisation; disable the current one before switching.
- **System Services:** WeChat Service Account; **Twilio International SMS**.
- **LDAP login:** `Integration > Misc.`, **LDAP login** > **Setting** (server and sync). Matches HAP accounts by username and email; can create missing accounts. Deleting a user in LDAP does not deactivate the HAP account. "In paid plans"; the plan page lists LDAP/AD for Standard and Professional.
- **Disable Platform Account Login** for the custom subdomain login page once LDAP or an identity platform is on.
- **Organisation API key:** `Integration > Misc. > View Key` gives the key pair (Secret); **View Docs** opens the API documentation.
- **Plans:** Feishu/Lark, DingTalk, WeLink and WeCom integrations are Professional only. Entra is not on the plan page.
- Source: https://help.nocoly.com/org/integration, https://help.nocoly.com/purchase/version-comparison

#### OAuth applications
- Third-party tools act for a user through OAuth 2.0 access tokens, without the user's password.
- Admins (`Integration > OAuth Application`) restrict **API Permissions** (for example read or write) and **Application Scope** (which apps or worksheets). Disabling an application invalidates its access tokens at once, stops refresh tokens and blocks new authorisations. **Disable Integration** turns off all OAuth applications.
- Users authorise on HAP's page and revoke under `Authorization & Access > Authorized Apps`.
- The docs say HAP "will gradually support" ChatGPT, Codex and Claude Code through OAuth. The Integration Center has a **HAP API (Personal Authorization)** template.
- Source: https://help.nocoly.com/org/thirdapp

#### Cloud services (HAP Server only)
- Lets a HAP Server install use SaaS AI models through a key created in the SaaS organisation (`Org Admin > Integration > Cloud Service`), with an IP whitelist. Calls are billed to the SaaS organisation's credits. Not needed for a SaaS build.
- Source: https://help.nocoly.com/org/cloud-service, https://help.nocoly.com/zh-Hans/org/cloud-service

### 2.3 Plans, quotas and prices

**Plan limits** (cached plan page; the live pricing page of 23 Nov shows the same usage figures):

| Item | Free | Standard | Professional |
|---|---|---|---|
| Applications | 3 | unlimited | unlimited |
| Worksheets | 100 | 100 | unlimited |
| Rows per worksheet | 5,000 | 1,000,000 | 5,000,000 |
| Total rows | 50,000 | unlimited | unlimited |
| Workflow executions | 1,000/month | 100,000/month | 500,000/month |
| Attachment uploads | 1 GB/year | 60 GB/year | 120 GB/year |
| AI credits | none | 15/month | 28/month |
| Vector knowledge base chunks | none | 100,000 | 200,000 |
| External portal users | 100 | 100 | 100 |
| Data sync | not available | 100,000 rows/month | 500,000 rows/month |
| Seats **[live 23 Nov]** | max 10, $0 | min 5, $15 per user/month | min 10, contact sales |

**Extra usage** (Standard; Professional pays the Standard rate; none on Free): workflow execution $0.01 each; attachments $50 per 10 GB per year; vector chunks $30 per 10,000 per year; data sync $5 per 100,000 rows; SMS by country; email $0.002; PDF generation $0.03; external users $25 per 100, $50 per 1,000 or $250 per 10,000 per month (a year costs 10 months).

**Features by plan** (cached plan page; differences on the live page in §7):
- Standard and Professional: collaboration suite, recycle bin, custom icons, API integration, application logs, bulk attachment export, API Query fields, application localization, application backup and restore, generate print files, custom print templates, interface push, workflow plugins, call integrated APIs, LDAP/AD.
- Professional only: Super Search, hidden contacts, online document editing, condition groups, global variables, attachment and image watermarks, user activity logs, usage analytics, extended user information, data synchronization and transformation, data encryption, Code Block, API Proxy, Packaged Business Process (PBP), Loop, worksheet data mirroring, ETL, Feishu/Lark, DingTalk, WeLink, WeCom.
- Every plan: application import and export, external portal, API developer documentation, Chatbot, AI Agent; data sync tasks Free 5, Standard and Professional unlimited.

**Pay-as-you-go prices** (credits, $1 = 1 credit):
- SMS to Mainland China: 0.007 per message (70 characters; longer messages billed in 67-character parts). "Custom SMS can only be sent to mainland China numbers."
- SMS to other regions: 0.34, when no international SMS provider is configured (public-form and portal verification).
- Email: 0.002 per recipient, CCs included.
- OCR: 0.03 per file.
- Generate PDF ('Get Record Print File' node): 0.03 per time; failed conversions are free.
- LLM prices: https://www.nocoly.com/billingrules. WeCom integration API calls are billed by use.
- **Conflict:** the Twilio page says verification SMS outside Mainland China without Twilio cost 2.3 credits each.

**Buying and subscriptions:**
- `Org Admin > Home > Upgrade`, then the payment page with a seat count. Offline purchase goes through a partner or sales.
- Online and offline purchase records are not synchronised; organisations with offline payment records cannot buy online.
- Auto-renewal charges the default payment method; cancelling keeps the plan until the period ends.
- **Subscription Management** (`Org Admin > Home > Manage Subscription`): **Update Subscription** for four add-on packs (External User Pack, Attachment Uploads Pack, Workflow Executions Pack, Data Sync Pack), prorated mid-cycle; bills and PDF invoices; payment methods and a backup method.
- **Recharge** credits (not on the Free plan); **Expand** seats.
- Source: https://help.nocoly.com/purchase/version-comparison, https://help.nocoly.com/purchase/billing-items, https://help.nocoly.com/purchase/online-purchase, https://help.nocoly.com/org/home

### 2.4 Platform usage limits

| Area | Nocoly SaaS | HAP Server |
|---|---|---|
| Fields per worksheet | 200 (system fields not counted) | 2,000 (6 system fields not counted) |
| Subform rows | 1,000 | 1,000 |
| Related records shown in a relation field | Dropdown 50; Card 200; Table and Tab Table unlimited | not stated |
| Related records read | 1,000 for rollups, for Get Multiple Data through a relation, and for stored foreign fields | rollups 1,000 (a manual refresh aggregates all); stored foreign fields 1,000 |
| Recycle bin | 60 days | not stated |
| Excel import | 20,000 rows and 200 columns per import | not stated |
| Single/multiple select options | 1,000 options in total; at import a field may hold only 50, unless it uses a shared option set (up to 1,000) | 50 at import; option sets unlimited |
| Record volume alerts | at 95%, 99.5% and 100% of the per-worksheet limit, to app admins; Free: super admins, on 50,000 rows in total | not stated |
| Table view columns | 50 | not stated |
| Batch operations in a table view | 1,000 records per operation | 1,000 by default, adjustable |
| Custom pages | charts refresh every 15 minutes; up to 60 components | 15 minutes by default, adjustable |
| Update Record node | 100 records per run (batch update or delete) | Update, Delete and Add Record and Code Block: 200 by default, adjustable |
| Subprocess | 10,000 records | 20,000 by default |
| Send API Request node | 10 seconds | 10 seconds by default |
| Code Block | 10 seconds | 10 seconds by default |
| Worksheet-event trigger delay | not stated | 5 seconds by default |
| API records per call | 1,000 to read; 1,000 for batch create, update or delete | not stated |
| Base64 attachment by API | 7 MB | 14 MB |
| API rate limit per source IP | add/edit/delete row(s): 20 per second, 16 MB body; get rows and row count: 50 per second; other APIs no limit | no limit, 25 MB body |

- Rate-limit errors come back as **HTTP 200** with `{"error_code":90001,"success":false,"error_msg":"Rate limit exceeded"}`. A body over the limit returns **HTTP 413**.
- Rollups can be recalculated in full with the refresh icon or the **Calibrate Single Record** workflow option. A display-only foreign field always shows the latest data.
- Source: https://help.nocoly.com/faq/numbers

### 2.5 Worksheet indexes (from the zh-Hans page)
- **What it does:** speeds up queries and sorting on large worksheets. The docs suggest it once a sheet reaches tens of thousands of rows or filters become slow.
- **Where:** worksheet editor > **More settings** > **Retrieval acceleration** > **Create index** (translated from the Chinese page; the English label is on the worksheet slice's page).
- **Types:**
  - normal and composite indexes;
  - **Unique index:** the combination of the indexed fields cannot repeat (example: Name + Created date allows one record per person per day);
  - the old full-text index on all text fields can no longer be created.
- **Limits:**
  - up to 5 indexes per worksheet;
  - 1 text index per worksheet, and a text index cannot contain multi-value fields;
  - at most 1 multi-value field per index. Multi-value types include member, department, role, option, relation and array fields.
  - With a unique index, a field that allows empty values may be empty in **only one record** of the whole worksheet.
- **Editing:** add or remove fields, change the order and sort direction, rename, delete. The system index `index_rowid` cannot be renamed.
- **Creating a unique index fails** when duplicates exist, and the check includes the recycle bin. Records deleted more than 60 days ago, and some batch deletions, are not visible there; empty the recycle bin (Empty now) and retry.
- **Auto-indexing:** on the public cloud, HAP learns frequent queries from daily logs and creates indexes itself. Do not change or delete indexes you did not create. Server installs do not auto-index.
- **Query advice:**
  - follow the leftmost-prefix rule;
  - match the sort order of the view;
  - use "equals" on text and "any of" on multi-value fields;
  - indexes rarely help with "not equal", "does not contain", "does not start/end with", "contains", "is empty", "starts/ends with", OR conditions, options where one value covers more than 30% of rows, or text sorted by pinyin;
  - more indexes slow down writes.
- The English page (https://help.nocoly.com/worksheet/index-acceleration, 6,766 characters) is in the worksheet slice.
- Source: https://help.nocoly.com/zh-Hans/worksheet/index-acceleration

### 2.6 Search, shortcuts, participants and notifications

#### Super Search
- **Opening it:** the `F` key or the magnifier in the right-hand message bar. **Open in new page** (or Enter) opens the full page with filters by module.
- **Scope by module:**
  - App: app, group, worksheet and custom page names.
  - Record: the title field by default. Searchable field types: Text, Email, Telephone, Auto Number, ID Number, Concatenate, Relationship, Foreign Field (stored).
  - Post: content and comments. Task: title, description, discussion (only tasks you own or belong to). File: file name. Contacts: name, job title, department, mobile. Group: name and announcement (only groups you belong to).
- **Matching:** fuzzy (part of a word matches); English is **case-sensitive**; no word segmentation and no multi-keyword search; external collaboration apps are not searched; results respect permissions.
- **Options:** untick "title field only" to search other fields. Inside an app, the search is limited to that app until you click **All**. Apps or worksheets can be excluded from results (managed under **Excluded Locations**). Record results can be filtered by app. Results are sorted by last update, with 5 per module on the **All** tab.
- **Switching it off:** org admins can disable record search (`Org Admin > Security > Misc. > Feature Restrictions`). Permission groups also carry a **Global Search (Search Records)** feature permission.
- **Plan:** Professional only.
- Source: https://help.nocoly.com/faq/sse, https://help.nocoly.com/org/administrators, https://help.nocoly.com/purchase/version-comparison

#### Keyboard shortcuts (Windows; Mac uses ⌘)
- **Global:** `M` Mingo, `F` Super Search, `S` Messages, `E` Contacts, `Q` all contacts, `K` shortcut help.
- **Form editor:** `Ctrl + /` control panel.
- **Views:** `Ctrl + /` full screen; `Shift + click` row numbers to select a range; `⇧ + click` in the org view expands all levels.
- **Table view, spreadsheet mode:** `Enter` edit; `Tab` next cell; `Ctrl + C` / `Ctrl + V`; arrow keys; `Space` opens the record; while editing, `Esc` cancels, arrows move between options and `Enter` selects.
- **Records:** `Ctrl + Enter` new-record popup; `Ctrl + S` save or submit; `Ctrl + ⇧ + Enter` submit and continue; `Tab` next editable field; `Ctrl + ⇧ + ,` / `Ctrl + ⇧ + .` previous or next record; `Esc` closes.
- **Subforms:** `Ctrl + Enter` adds a row at the end; arrow keys move between cells; `Ctrl + arrow` jumps to an edge; `Tab` next cell.
- **Desktop client:** `Ctrl + Shift + I` opens the developer console.
- Source: https://help.nocoly.com/faq/shortcut-key

#### Record participants and @All
- **Frequent collaborators** (Contacts > **Manage Frequent Collaborators**): people you @mentioned or were @mentioned by in the last 30 days; otherwise your direct manager and subordinates. You can add, remove and reorder them.
- **Record participants:** the record owner, members in member fields, people who commented, and people mentioned in the discussion. **@All Participants of the Record** notifies them all. Members in a member field set to **Store Data Only** are not participants and get no notice.
- **Others:** post participants (people and groups mentioned in the post or replies, and repliers); task members (owner and members); calendar event participants.
- Source: https://help.nocoly.com/faq/all-members

#### Muting notifications
- A muted conversation shows only a red dot (no tab flashing, sound or mobile push). Direct replies and mentions of you still notify.
- By source:
  - system messages, Knowledge, HR and groups: all muted;
  - workflows: all muted, including approval, fill-in, CC and in-app notices;
  - applications: muted except direct replies, mentions of you and mentions of all record members;
  - posts: muted except direct replies and mentions of you;
  - calendar and tasks: muted except direct replies, mentions of you and mentions of all members.
- Source: https://help.nocoly.com/faq/mute-notification

### 2.7 Messaging delivery and network

- **Email delivery:** the same recipient mailbox can receive at most 10 emails in one hour; later ones are blocked by mail providers, so workflows should not send more. The page asks recipients to allow these sender domains: mingdao.com, sender.mingdao.net, workflow-sender.mingdao.net, register.mingdao.com, workflow.mail.mingdaoyun.cn, smtp-out.qcloudmail.com. An email check tool shows up to 50 sends from the last 3 days. *Inference:* the page is written for Mingdao in China (China carriers, <email>); Nocoly's sender domains may differ. Source: https://help.nocoly.com/faq/sms-emali-service-failure
- **Twilio international SMS:**
  - **Scope:** once connected, SMS to numbers outside Mainland China go through Twilio automatically: the **Send SMS** workflow node, phone verification in public forms, portal sign-up and sign-in codes, and portal invitation, notice and approval-result SMS.
  - **Setup:** `Org Admin > Integration > System Services > Twilio International SMS > Connect`, then enter **API Key SID**, **API Key Secret**, **Verify Service SID** (starts with VA; verification codes) and **Messaging Service SID** (starts with MG; notifications).
  - **Billing:** Twilio bills the SMS; HAP takes no part.
  - **Requirements:** numbers in E.164 format (for example +60...); senders registered where the country requires it; Sender IDs are not allowed in every country.
  - **Troubleshooting:** Twilio statuses and errors 30003 (rate limit), 30004 (invalid number), 30005 (destination restrictions).
  - Without Twilio, verification SMS outside Mainland China cost 2.3 credits each.
  - Source: https://help.nocoly.com/org/link-twilio-international-sms
- **Outbound IPs:** webhooks (workflow and worksheet events), **Send API Request** nodes and code blocks all leave from five Tencent Cloud Hong Kong addresses, picked at random per request: 43.154.235.158, 43.154.111.184, 43.154.63.239, 43.154.158.53, 43.154.202.180.
- **Inbound domains:** allow www.nocoly.com and nocoly.com, status.nocoly.com, and wps.nocoly.com (online Office preview and editing). Outside Mainland China, Hong Kong, Macao and Taiwan, www.nocoly.com resolves through a CDN, so allow it by domain, not by IP. Source: https://help.nocoly.com/faq/ip
- **WeChat Service Account** (China): a verified WeChat service account gives portal QR sign-in, WeChat details of form respondents, quick WeChat Pay access from worksheets and template messages from workflows. Several accounts can be connected. Error 10005 means a subscription account or expired verification. Source: https://help.nocoly.com/org/link-wechat-service-account

### 2.8 Mobile and hardware

- **PDA scanning (handheld terminals):**
  - **Modes:** browser (H5) or the HAP App (Android 5+). In H5, the PDA's scan service types into the focused field: nothing to install, but no continuous scanning and no key mapping. The App calls the scan engine natively, with continuous scanning and hardware-key mapping; turn on **Enable Dedicated Scanning Device** in the App's scan page settings.
  - **Scans** fill text or barcode fields. Supported codes include 1D (EAN-13, Code128) and 2D (QR, DM, PDF417).
  - **Hardware keys** can trigger HAP actions: run a PBP, create a record, start scanning. Copy the button ID in the app, then on the PDA either send a broadcast with action `com.mingdao.PDA_Btn_Click_Action` and extra `key` = button ID, or, on newer Android, launch the app with the parameter `key` = button ID. The app must be opened once to register for broadcasts; it may then run in the background.
  - Source: https://help.nocoly.com/faq/hardware-integration-guide
- **Bluetooth printing:**
  - App only (SPP through JSBridge); H5 pages cannot print by Bluetooth.
  - Command sets **CPCL** and **TSPL**.
  - Only HAP **barcode and QR code templates**: label size, text layout, barcode or QR code, placeholders such as product name, batch number and storage location.
  - Flow: select the template in the app > search for and pick the printer > **Print**.
  - Source: https://help.nocoly.com/faq/hardware-integration-guide
- **NFC:**
  - **Devices:** Android phones with NFC; iPhone XR and newer. Most rewritable tags work: NTAG215 holds a URL of about 400 bytes, NTAG216 about 888 bytes usable.
  - **Writing:** use NFC Tools for Android. Write an Application record (for Android) and a Custom URL/URI record. For Nocoly, the URL is `nocoly://nfc/` + the link (HAP Server uses `mingdaoR://nfc/`). Links with Chinese characters must be URL-encoded. The iOS App cannot write the Android app record.
  - **Links that open:** worksheet links, shared view links, record links and shared record links. The docs advise proving the flow with QR codes first.
  - Source: https://help.nocoly.com/faq/nfc
- **Push on Android:** choose the Huawei, Xiaomi or VIVO channel, or Google FCM abroad, and use **Test**. Allow auto-start, notifications and no battery optimisation. Source: https://help.nocoly.com/faq/notification-setting-android
- **Requirements:** Windows 10+ or macOS; Android 5.0+; iOS 9.3+; no Internet Explorer; other browsers supported up to 10 versions back (Chrome, Edge, Firefox, Safari recommended). Source: https://help.nocoly.com/faq/system-browser

### 2.9 Personal account settings

- **Profile menu:** Manage My Account, Add Status, My Organization, Language, Theme, Sidebar, Authorization & Access, More, Log Out.
- **Languages:** English, Simplified Chinese, Traditional Chinese, Japanese.
- **Personal time zone** (`More > Basics`): date fields and system fields in worksheets are shown and calculated in this time zone. The default follows the device.
- **Map service:** Google Maps only; location search by name is not supported.
- **Privacy:** **Add Me as a Friend** (Verification Required / Allow Anyone / Do Not Allow Anyone); phone and email "visible only to you" (admins still see them).
- **Identity verification:** **Verify Now** runs facial verification on a mobile device. Unverified users cannot add friends or invite users to groups.
- **Security:**
  - two-factor authentication by SMS, email or authenticator app (TOTP: Google Authenticator, Microsoft Authenticator, Authy); the docs advise at least two methods;
  - **Allow Only One Device Login**, per device type (web, mobile App); push goes only to the last mobile device signed in;
  - device list with remote **Log Out**;
  - changing the password signs out every device.
- **Account data:** phone and email can be bound, changed or unbound (unbinding needs both bound). Accounts cannot be merged. Only the owner can delete an account, after leaving every organisation; there is a 15-day window to cancel. Third-party links: WeChat and QQ by the user; WeCom, Feishu/Lark and DingTalk by org admins.
- **Personal Access Token (PAT):** acts with the user's identity, with chosen permissions and data scope; do not share it. Authorised third-party apps can be reviewed and revoked.
- **Personal status:** On Leave, Sick Leave, In Meeting, Work Trip or a custom one, with a duration and a note. It shows in one-to-one chats, @mention lists, the profile page and the profile card, and clears itself at the end.
- **Product Key:** HAP Server licences only; SaaS shows "No Product Key".
- Source: https://help.nocoly.com/account/faq, https://help.nocoly.com/account/bind-delete, https://help.nocoly.com/account/status, https://help.nocoly.com/account/modify

### 2.10 Collaboration suite (Standard and Professional plans)

#### Calendar
- **Events:** **New** creates an event with participants (colleagues, WeChat contacts and others), reminders (notification alerts and phone reminders) and a discussion.
- **Options:** **Private Event** (others see only **Busy**); **Time Zone** per event. The creator can delete but not leave an event; participants can leave but not delete. Events can be shared with WeChat contacts, who can join without registering.
- **Time zones:** event times follow each viewer's device time zone (8:00 PM in New York shows as 9:00 AM the next day in Beijing). Task start and end times are **not** converted.
- **Sync:** **Copy Internet calendar address** gives a public, **read-only** iCal URL for Outlook, Mac Calendar and Google Calendar.
- **Other views:** **View Colleagues' Schedule** overlays several colleagues (private events show as Busy); your own events can be hidden. Past events drop out of the list view; use Month, Week or Day.
- Source: https://help.nocoly.com/calendar/introduction, https://help.nocoly.com/calendar/operations, https://help.nocoly.com/calendar/time-zone, https://help.nocoly.com/calendar/sync-instructions, https://help.nocoly.com/calendar/view-others, https://help.nocoly.com/calendar/find

#### Task and Project
- **Tasks:** New Task (Enter creates the next one); star; subtasks; checklists (pasted lines become items; progress bar; an item can become a task); comments with @mentions and files; lock (members can no longer edit); link a parent task or a project.
- **Planned and actual dates:** planned start and end; actual start (**Start Now**, needs a planned start); actual end = completion time.
- **Status rules:**
  - Not Started, In Progress or Completed, with variants such as Not Started (Overdue Start), In Progress (Overdue Unfinished), On-Time, Early or Overdue Completion;
  - completion with no planned end date counts as On-Time Completion.
- **Projects:**
  - blank or template; Private or Public (Public with a sharing scope of groups); folders;
  - roles: **Project Owner** (everything), **Project Admin** (cannot delete or archive), **Project Member** (view, comment, create subtasks), shared groups.
  - **Kanban boards** (stages) can be added, reordered, renamed and deleted, each with a **Default Owner** (cleared if that person leaves).
  - **Gantt** (day, week, month; planned and actual bars; export as image).
  - Settings: rename, export tasks to Excel, save as template (templates are personal), archive, delete, duplicate, hide, pin.
- **Permissions:** only project owners and admins can edit task details or move tasks between boards, unless the person is also a task member. Task members see only the project name and their own board. Parent-task members see only subtask titles; subtask members see only the parent's title.
- **Bulk actions** (web only, Ctrl+click): owner, members, complete, delete, lock, tags and colours, star, mute.
- **Subordinates' Tasks** relies on the org chart.
- **Custom Task Content is deprecated:** it can no longer be edited, though existing content still works.
- Source: https://help.nocoly.com/task/introduction, https://help.nocoly.com/task/operations, https://help.nocoly.com/task/start-end, https://help.nocoly.com/task/role-permission, https://help.nocoly.com/task/faq, https://help.nocoly.com/task/gantt, https://help.nocoly.com/task/default-owner, https://help.nocoly.com/task/board, https://help.nocoly.com/task/board-operations, https://help.nocoly.com/task/checklist, https://help.nocoly.com/task/project-operations, https://help.nocoly.com/task/custom-field

#### Posts
- **Content:** text, images, documents, links (with a preview) and polls. The docs say "the system and applications can also push automated post updates to specific users".
- **Visibility:** one or more groups (the union), **All Colleagues**, or **Only Me**. @mentions widen it; "Only Me" plus @mentions works as a private message.
- **Types:** file, link, **poll** (up to 99 options, images allowed, anonymous or named) and **Q&A** (a post ending in "?").
- **Actions:** reply, like, star (**Starred**), edit (creator only), delete (creator or a super admin who can see it; cannot be recovered), change visibility.
- **Pin:** only super admins and organisation account admins, and only posts shared with All Colleagues. Pinning rights are granted under `[Organization] > [Administrator]`.
- **Filters:** All, My Posts, Starred Posts, Groups; by type, date range and keyword.
- Source: https://help.nocoly.com/post/introduction, https://help.nocoly.com/post/operations, https://help.nocoly.com/post/types, https://help.nocoly.com/post/filter, https://help.nocoly.com/post/sharing-scope, https://help.nocoly.com/post/scenario

#### Groups, chats and contacts
- **Contacts** (`E`): New Friends, App Notifications (Post, Task, Calendar, Knowledge, File Transfer Assistant, apps, workflows), All Contacts (colleagues and friends), My Groups, Friends, View by Organization. "Only contacts can be messaged, and only contacts will appear when assigning members in other modules."
- **Chats:** one person starts a private chat; two or more start a temporary group chat. Chats have no avatar, no admins and no Contacts entry; they can be converted into groups.
- **Group settings:** name, QR code, announcement; owner (the creator, fixed) and admins; show in the organisation's Contacts; only owner and admins invite; official group; **New members require admin approval**; **Close Group** (reopen in Org Admin); **Delete Group** (permanent).
- **Messages:** stored permanently except recalled ones. Your own messages can be recalled within 10 minutes; group admins can recall anyone's messages at any time. Admins can open a departed member's conversations from the org panel.
- **Suggested group types:** official, cross-department, management, product feedback, learning and interest, service, external collaboration.
- Source: https://help.nocoly.com/group-chat/contacts, https://help.nocoly.com/group-chat/create, https://help.nocoly.com/group-chat/operations, https://help.nocoly.com/group-chat/faq, https://help.nocoly.com/group-chat/introduction, https://help.nocoly.com/group-chat/type, https://help.nocoly.com/group-chat/invite

#### Files
- **Shared folders:** owned by the organisation or shared with friends; ownership is fixed. Collaborators get **Admin**, **Editor** or **Read-only**; they are added one by one, with departments or groups for batch adding.
- **Folder actions:** star, sharing settings (rename, collaborators, permissions, ownership transfer), recycle bin. Deleting a whole folder removes everything permanently.
- **Contents:** files, whole folders, **link files** (saved web pages) and subfolders.
- **File actions:** preview, share, download, star, rename, move, copy, delete; properties (creator, type, path, dates, view and download counts, share links, download, edit and visibility rights) and an activity log.
- **Sharing:** **Disable sharing**, **Allow public access**, **Restrict to organization members**, **Limit to selected contacts only**.
- **Preview** uses Microsoft's online preview service. More than 99% of files work; complex formulas or layouts may fail. Avoid **Online View Only** so that users can still download.
- **Storage:**
  - File-module uploads are personal: Free 300 MB a month and 5 GB in total; paid 10 GB a month with no total cap. Posts, tasks and the File module share this quota.
  - Uploads inside apps count against the organisation's quota.
  - Posts, tasks and discussions take under 1 GB per upload. Single files of 1–2 GB go to the File module first and are referenced from there. Nothing over 2 GB.
  - Knowledge base: up to 2 GB per file.
- The permissions page has no text; its matrix is one image **[live 23 Nov]**.
- Source: https://help.nocoly.com/file/introduction, https://help.nocoly.com/file/operations, https://help.nocoly.com/file/size-storage, https://help.nocoly.com/file/preview-failure, https://help.nocoly.com/file/role-permission

### 2.11 Identity platforms (directory sync and sign-in)

- **Microsoft Entra (SaaS):**
  - **Connect:** a Super Admin opens `Org Admin > Integration > Org Integration > Microsoft Entra`, clicks **Connect** and the Entra admin authorises.
  - **Sync scope:** the Object ID of an Entra security group goes in **GroupID**; left blank, the whole directory syncs.
  - **Accounts:** **Sync** matches each user's UPN to HAP account emails and creates new accounts for the rest. Linked accounts are managed under **Data Sync**; an unlinked Microsoft account can no longer sign in.
  - **Set Microsoft Entra as the sole login method** turns off passwords, codes and other SSO, but only for members who are synced and linked.
  - Server installs register their own Entra app (client ID, secret, Graph permissions).
  - Source: https://help.nocoly.com/entra/integration-guide
- **Lark (Feishu):**
  - **Setup:** a custom app in Lark Developer with a web app (HAP home URL), a bot for notifications, tenant-token scopes and a published version whose user scope decides who syncs. Then enter the App ID and App Secret in HAP and click **Sync** (Super Admin).
  - **Matching:** by mobile number, then by email, and only with accounts that are already members. Otherwise a new account is created with a random email.
  - **Leavers and joiners:** people who leave the scope are marked departed at the next sync; people who join get an account or a reactivated one.
  - **Exclusions:** a Lark custom member field **Sync** set to **Do Not Sync** leaves people out.
  - **Messages** open in a **New Window** or the Lark **Sidebar**.
  - **Lark sign-in:** works on the organisation sign-in page `{primary-domain}/network?projectid={organization-id}`.
  - **Plan:** Professional only.
  - Source: https://help.nocoly.com/feishu/integration-guide
- **DingTalk, WeCom:** the cached English pages are empty, and live they are unlisted with no English body. WeCom API calls are billed by use. Professional only. Source: https://help.nocoly.com/dingtalk/integration-guide, https://help.nocoly.com/wecom/integration-note, https://help.nocoly.com/wecom/disable-integration

### 2.12 Other pages

- **Platform overview:** apps are built from Worksheet, View, Role and Permission, Workflow, ChatBot, Chart, Custom Page and External Portal; SaaS or self-hosted. Source: https://help.nocoly.com/
- **Architecture:** React front end; Java, C# and Node.js services; REST and gRPC; Kubernetes; MySQL, MongoDB, Redis, Kafka, Elasticsearch and object storage. Source: https://help.nocoly.com/faq/technology-architecture
- **Desktop client and browser cache:** client settings, clearing `%USERPROFILE%\AppData\Roaming\HAPCloud`, a screenshot scaling fix; clear cached images and files when pages misbehave after an update. Source: https://help.nocoly.com/faq/desktop, https://help.nocoly.com/faq/browser-cache

## 3. Odoo rebuild notes

### 3.1 Users, employees and teams

| Odoo concept | Native HAP feature | Where it falls short / notes |
|---|---|---|
| `res.users` (internal user) | Organisation member (a paid seat) and Member fields in worksheets | Name, phone and email belong to the user; admins edit only organisation info. *Inference:* people who never sign in should not be members, because members use seats |
| `res.groups` (access rights) | App roles (role slice). Org roles can fill an app role in bulk. Org permission groups cover only the admin console | *Inference:* no implied-group chains as in Odoo; each app role is set by hand |
| User language and time zone | Personal language (EN, zh-Hans, zh-Hant, JA) and personal time zone | No Malay interface. The personal time zone drives date display and date calculations |
| `hr.employee` | Org member data (departments, job title, employee ID, work location, work phone, manager) plus an **Employees worksheet** for HR fields | The docs show no custom fields on members. Cross-slice: the Get Multiple Personnel node reads members, departments and org roles as "system tables" and its page shows a scheduled sync into an Employee Directory sheet (https://help.nocoly.com/workflow/node-get-multiple-data-from-user) |
| Employee without a user account | A record in the Employees worksheet only | *Inference:* this avoids seats for staff who never sign in |
| `parent_id` (manager) | Org chart manager, one per member | Matches Odoo's single manager; works in approvals, view filters and role scopes |
| `coach_id` | None | A Member field on the Employees sheet |
| `hr.department` (tree, manager) | Departments (tree, several managers, disable) | HAP managers must belong to the department; an Odoo manager need not (trap 9). Department fields in worksheets pick from the organisation tree |
| One department per employee | Members may sit in several departments, one marked primary | Use the primary department as Odoo's `department_id` (*inference*) |
| `hr.job` / job title | Job titles: a list with members; a member may hold several | No department link and no recruitment targets, so Recruitment needs its own sheet |
| `hr.work.location` | Work locations (Org Info) | A name list only, as far as the docs show |
| Badge or employee number | Employee ID | — |
| `crm.team` (members, leader) | An org role per team, grouped in a "Sales Teams" role group, with responsible departments; or departments; or a Teams worksheet with **Extended user information** (role slice, Professional) | Org roles drive approvals and bulk app-role membership. "Team members see the team's records" needs extended user information (https://help.nocoly.com/role/extended-info) or department-based role scopes (role slice) |
| Record rules (own / team / all documents) | App-role data scope, including records of subordinates in the org chart | Details in the role slice |
| Approval by manager, department head or a named group | Approval node approvers: manager (org chart), department manager, org-role members, the role member responsible for the submitter's department | For people in several departments, choose every department head or only the primary one |
| Archiving a user | Offboard, then handover | Record owners and member fields keep the departed user; reassign in bulk with the **Offboarded** filter |
| Portal user | External portal user (portal slice) or an external collaborator | 100 portal users on every plan, counted per app; group collaborators are not billed |
| User invitation (`auth_signup`) | Invitations, joining rules, bulk import | 100 imports a day on unpaid organisations |
| `res.company` (single company) | Organisation settings: name, logo, country/region (default currency, region and calling code), time zone | *Inference:* organisation settings do not model several companies. "Multiple business entities" exist only for China SMS signatures and tax IDs |
| `res.users.apikeys` | Personal Access Token (scoped), organisation API key, OAuth applications | The API and CLI access policies can switch these off for the whole organisation |
| `auth_totp` | Personal 2FA (SMS, email, TOTP) | No organisation-wide 2FA enforcement in this slice |
| `auth_ldap`, `auth_oauth` | LDAP (Standard and Professional), Entra SSO, Lark sign-in (Professional) | One identity platform per organisation |

### 3.2 Other Odoo concepts

| Odoo concept | Native HAP feature | Where it falls short / notes |
|---|---|---|
| Followers (`mail.followers`) | Record participants: owner, member-field members (not **Store Data Only**), commenters, @mentioned users | *Inference:* no explicit follow/unfollow per record; members are added through member fields |
| Chatter @mentions | @mention in the record discussion; frequent collaborators | In app records, the frequent-collaborator list for @mentions holds only members of the current organisation |
| Discuss channels and chats | Organisation and personal groups; official groups tied to departments; temporary chats | Messages are kept for ever; recall within 10 minutes |
| Company news | Posts to All Colleagues, pinned by admins; Org Admin **Announcement** (in-app, message, email) | Deleting a post cannot be undone |
| Out-of-office status (Time Off) | Personal status (On Leave, Sick Leave, In Meeting, Work Trip) | *Inference:* display only, not linked to app data |
| Calendar (`calendar.event`) | Collaboration Calendar: private events (Busy), time zone per event, reminders, colleagues' schedules, read-only iCal feed | *Inference:* events cannot be linked to app records and there is no two-way Google or Outlook sync. Meetings on CRM records need a worksheet with a calendar view (view slice) |
| Project and To-do (`project.task`) | Task module: projects, boards with default owners, subtasks, checklists, planned and actual dates, Gantt, roles | Custom task content is deprecated and tasks are not app data. *Inference:* build Project and Timesheets as worksheets; the Task module could cover personal to-dos |
| Documents (Enterprise) | File module: shared folders with Admin, Editor and Read-only collaborators, link files, sharing, logs | Not linked to records; personal monthly upload quota |
| Attachments on records | Attachment fields (worksheet slice) | Count against the organisation's yearly upload quota (Standard 60 GB a year) |
| SQL unique constraints (`_sql_constraints`) | Unique index, composite allowed | One empty value per worksheet; at most 5 indexes; no uniqueness across two sheets (barcode on products and variants still needs a check) |
| Global search and name search | Super Search (Professional) | Title field by default; case-sensitive. *Inference:* make Odoo's display name the title field |
| Keyboard shortcuts | HAP shortcuts | `Ctrl+Enter` new, `Ctrl+S` save, `Ctrl+⇧+Enter` save and new, `Ctrl+⇧+,` / `Ctrl+⇧+.` previous and next record |
| Import (`base_import`) | Excel import | 20,000 rows and 200 columns; select fields take 50 options at import unless they use an option set |
| SMS (`sms`, SMS marketing) | Send SMS node with Twilio | The platform sends custom SMS only to Mainland China numbers |
| Mass mailing and invoice emails | Email node (workflow slice) | $0.002 per recipient; 10 emails an hour per recipient mailbox (docs) |
| Payment providers (`payment`) | Native payment (unlisted): WeChat Pay and Alipay merchants only (§7) | *Inference:* Malaysian gateways need API integration |
| E-invoicing (`l10n_my_edi`, MyInvois) | E-Invoicing node (unlisted): China digital tax account (§7) | *Inference:* MyInvois needs API integration (EMS already has one) |
| Barcode (Enterprise) and scanning in Inventory | Mobile scanning; PDA laser scan into fields; continuous scanning; hardware keys pressing buttons | Continuous scanning and keys need the App, not H5 |
| Label printing (ZPL or PDF) | Bluetooth CPCL and TSPL with barcode and QR templates (App) | No ZPL in the docs. PDF labels go through print templates (another slice) |
| IoT and tags | NFC tags opening records | Writing works best from Android |
| Audit trail | Org Admin > Log; app logs (Standard+); user behaviour log (Professional) | — |
| Translations | Four interface languages; app multilingual content (Standard+) | Malay only through app content translation (another slice) |
| Scheduled actions and automation volume | Workflow executions per month by plan, with auto-purchase below 2% | Each run uses quota: 100,000 a month on Standard |

### 3.3 Where native falls short (summary)
- Members cannot carry custom fields, and seats are paid, so Odoo employees need an Employees worksheet kept in step with the directory (*inference*).
- Team-scoped record access ("my team's documents") needs extended user information (Professional) or departments; org roles alone do not scope records (*inference* from the role slice pointer).
- Handover leaves record owners and member fields untouched.
- Collaboration Calendar, Task and Files are not app data.
- There is no Malay interface.
- Payments and e-invoicing are China-only.
- Label printing is limited to CPCL and TSPL over Bluetooth in the App.
- A Standard plan blocks Code Block, Loop, global variables, condition groups and more.

## 4. Traps

**Data model and limits**
1. **200 fields per worksheet on SaaS.** Odoo models are larger: `res.partner` 225, `res.company` 247, `product.product` 222 business fields (counts in `00-foundation.md` §2, which include computed fields). If every module appends its own fields to the shared sheets, they will run out. *Inference:* give each shared sheet a field budget per module. (faq/numbers)
2. **Standard plan: 100 worksheets.** The September estimate was about 233 worksheets for the Community apps. Customer copies on Standard also lose Code Block, Loop, global variables, condition groups, extended user information and Super Search. (purchase/version-comparison; pricing **[live 23 Nov]**)
3. **1,000 related records** for rollups, Get Multiple Data through a relation, and stored foreign fields. A customer with more than 1,000 invoices gets a wrong rollup total until it is refreshed, and only 1,000 stored foreign values follow a change. Use "Get from Worksheet" with a filter instead. (faq/numbers)
4. **Relation display:** Dropdown mode shows 50 related records and Card mode 200; Table and Tab Table have no limit. A subform holds 1,000 rows. (faq/numbers)
5. **Update Record node: 100 records per run on SaaS** (Server: 200). Subprocess: 10,000. Code Block and Send API Request: 10 seconds. (faq/numbers)
6. **Imports:** 20,000 rows and 200 columns per file. A select field may hold only 50 options at import unless it uses a shared option set. (faq/numbers)
7. **Table views show 50 columns; batch operations take 1,000 records**; custom page charts refresh every 15 minutes. (faq/numbers)
8. **Unique index:** an optional field may be empty in only one record, so a unique index on an optional barcode or internal reference blocks the second empty value. Creation fails if duplicates exist, recycle bin included. At most 5 indexes and 1 text index per worksheet. On SaaS, do not edit or delete indexes HAP created itself. (zh-Hans/worksheet/index-acceleration)

**Organisation directory**
9. **Department managers must be members of that department.** In Odoo, any employee can manage a department. (org/department-position)
10. **Department manager and org-chart manager are different things.** Pick the right one in each approval step. Members of several departments may get one approval step per department head unless the step is limited to the primary department. (org/reporting-structure, org/member-management)
11. **Disable, do not delete,** departments and org roles that records use. Deleting breaks history; disabled ones show with a strikethrough. A job title with members cannot be deleted. (org/department-position, org/roles)
12. **Two separators:** member import writes department levels with `>`, department import with `/`. Template headers start on row 2. Member import creates missing departments, job titles and roles, so typos create new ones. (org/member-management, org/department-position)
13. **Batch edit covers only department, position and work location.** Name, phone and email can be changed only by the member, so an HR sheet cannot push them to the directory. (org/member-management)
14. **Handover does not move record owners or member fields.** Owned apps go to "Assistant". A restored account does not get its app and group memberships back. (org/handover-terminate-restore)
15. **Member fields set to Store Data Only** do not make people participants, and @All Participants skips them. Do not use that option where Odoo would add a follower. (faq/all-members)
16. **Contacts visibility rules also hide users in member pickers and @mention lists.** A restricted salesperson may be unable to pick colleagues in Member fields. Only contacts (colleagues and friends) appear in member pickers. (org/security, group-chat/contacts)
17. **External users are counted per app:** one person who joins two applications counts as 2 users. Portal seats are 100 on every plan. (purchase/online-purchase, version-comparison)
18. **The Free plan caps the organisation at 10 users; unpaid organisations import 100 members a day.** (purchase/online-purchase, org/member-management)

**Time zones and languages**
19. **Personal time zone:** date fields and system fields are shown and calculated in each viewer's time zone (default: the device). Together with UTC server time (`00-foundation.md`), "today" in rules can differ by user. (account/faq)
20. **The organisation time zone is only the default for apps,** and its country sets the default currency and calling code. Check the Odoo Replica organisation is set to Malaysia. (org/basic-info)
21. **Task times do not convert between time zones;** calendar event times do. (calendar/time-zone)
22. **No Malay interface:** English, Simplified Chinese, Traditional Chinese and Japanese only. (account/faq)

**Messaging, network and integrations**
23. **Email: 10 per hour per recipient mailbox** (docs written for Mingdao). Sending many invoices or reminders to one customer from a workflow can be blocked. (faq/sms-emali-service-failure)
24. **The platform sends custom SMS only to Mainland China numbers.** Malaysian numbers need Twilio (E.164 format, registered senders, billed by Twilio). (purchase/billing-items, org/link-twilio-international-sms)
25. **Outbound IPs:** webhooks, Send API Request and code blocks use 5 fixed Hong Kong IPs picked at random. Whitelist all 5 at any partner that filters by IP (tax portal, bank, 3PL). (faq/ip)
26. **API rate limit errors return HTTP 200** with error_code 90001, not 429; retry logic must read the body. Writes: 20 per second per IP. Base64 uploads: 7 MB. (faq/numbers)
27. **One identity platform per organisation** (Entra, Lark, WeCom, DingTalk or WeLink). Deleting a user in LDAP does not deactivate them in HAP. Entra "sole login" applies only to synced, linked members. (org/integration, entra/integration-guide)
28. **Lark sync creates accounts with random emails** for people with no match, and links existing accounts only if they are already members with the same mobile number. (feishu/integration-guide)
29. **The CLI Access Policy and API Access Policy can cut off the HAP CLI, MCP or PATs** for the whole organisation. Our build depends on them. (org/security)

**Mobile and hardware**
30. **Bluetooth printing is App-only, CPCL or TSPL, with barcode and QR templates only.** ZPL printers are not mentioned. (faq/hardware-integration-guide)
31. **PDA continuous scanning and key mapping need the App** (H5 types into the focused field only). On newer Android, broadcasts cannot start the app, so use the launch-app mapping, and the app must be opened once to register. The broadcast action name is `com.mingdao...`; check it on the Nocoly app. (faq/hardware-integration-guide)
32. **NFC:** the iOS App cannot write the Android app record; NTAG215 holds about 400 bytes; URL-encode Chinese characters; Nocoly uses `nocoly://nfc/`. (faq/nfc)
33. **Single-device login:** push notifications go only to the last mobile device signed in, and changing the password signs out every device. (account/faq)

**Collaboration modules**
34. **Collaboration Calendar, Task and Files are not app data:** no record links, and custom task content is deprecated. Do not build Odoo Calendar, Project or Documents on them (*inference*). (task/custom-field, calendar pages, file pages)
35. **A group's type (organisation or personal) is fixed.** Personal groups are invisible to admins and keep people who left. Deleting a group or a post is permanent. (group-chat/create, group-chat/operations, post/operations)
36. **Only super admins and organisation account admins can pin posts,** and only posts shared with All Colleagues. (post/operations)
37. **File preview relies on Microsoft.** Complex formulas or layouts may not preview; "Online View Only" then blocks users. (file/preview-failure)

**Billing and plan pages**
38. **Online and offline purchases are not synchronised:** an organisation with offline payment records cannot buy add-ons or recharge online. (purchase/online-purchase)
39. **Conflicting figures:** international SMS costs 0.34 on the billing page and 2.3 credits on the Twilio page. On Free, the cached plan page calls data sync "unavailable" yet gives Free 5 sync tasks; the live pricing page shows data sync on Free with 10,000 rows in its feature table but "-" in its usage table **[live 23 Nov]**. The admin home says core resources (worksheets, records) are "typically not subject to quota limits in the current edition", against 100 worksheets on Standard. (purchase/billing-items, org/link-twilio-international-sms, org/home)

**Docs consistency**
40. **Menu paths differ between pages,** for example "Org Admin > Use > User & Department", "Orga Admin", "[Organization] > [Administrator]" next to "Organization > Permission Management", and record search switched off under "Security > Misc. > Feature Restrictions" next to "Security > Feature > Member Feature Control". The interface has moved on; follow what the live interface shows.
41. **Two overlapping controls for creating and deleting apps:** "Feature restrictions" (limit to app administrators) on the security page, and "Feature Permission" plus "Default Feature for All Members" in permission groups. *Inference:* the permission-group model may have replaced the older restriction; check which one the live interface has. (org/security, org/administrators)
42. **Several pages here are unlisted Mingdao pages written for China** (org/certification, org/payment, the e-invoicing node). Their rules (WeChat facial verification, China SMS signatures, RMB fees) may not apply to Nocoly SaaS as written. (§7)

## 5. To verify live (Nocoly SaaS)

| # | Doc claim | Why it matters | Suggested check (read-only first) |
|---|---|---|---|
| 1 | Plan gates: Code Block, Loop, PBP API response, global variables, condition groups, extended user information, Super Search, data encryption are Professional only | Decides which native tools the build and customer copies can use | `Org Admin > Home`: edition of the organisation; open the workflow node list and the worksheet settings |
| 2 | 200 fields per worksheet on SaaS | Shared sheets (Contacts, Products, Companies) grow with every module | Count fields on EMS's largest sheet; on a test sheet, see whether field 201 is refused |
| 3 | Unique index: composite, a relation field allowed, one empty value, enforced for workflow and API writes | Could replace workflow duplicate checks (state code per country, barcode) | On a test sheet: create a unique index, then write duplicates through the form, a workflow and the API; note the error |
| 4 | The English label and place of the index tool (More settings > Retrieval acceleration) | Builders need the path | Open a worksheet's More settings |
| 5 | Rollups, Get Multiple Data through a relation and stored foreign fields stop at 1,000 related records | Customer totals and stock sums | Test sheet with 1,001 child rows |
| 6 | Update Record node: 100 records per run on SaaS | Batch postings and stock moves | Run a test flow on 150 rows and count the updates |
| 7 | Approver options: department manager, manager (org chart), org-role members, the role member responsible for the department; the primary-department option | Odoo approvals (purchase, expenses, time off) | Open an approval node's approver picker |
| 8 | App-role data scope includes "records of subordinates" (org chart) | Odoo team-leader visibility | Role settings plus Role Debug with a test subordinate |
| 9 | A Store Data Only member field skips @All Participants | Odoo follower behaviour | Test record with such a field and an @All mention |
| 10 | Handover moves pending approvals; offboarding gives owned apps to "Assistant" | Leaver process | Read the Offboarded screens only; do not offboard anyone |
| 11 | The personal time zone changes date display and date calculations | "Today" rules, Malaysian time | Compare one record with two users in different time zones |
| 12 | The organisation's Country/Region sets the default currency and calling code | MYR and +60 defaults | `Org Info` of the Odoo Replica organisation; add a test currency field |
| 13 | 10 emails per hour per recipient mailbox; the sender domains | Invoice and reminder emails | Ask Nocoly support, or send a small test to one test mailbox |
| 14 | Send SMS to +60 numbers without Twilio | Delivery notices, portal codes | Check `Integration > System Services`; ask before any send |
| 15 | Outbound IPs are still the five 43.154.x addresses | IP whitelisting at partners | Send a test webhook to a request-inspector URL |
| 16 | The API rate limit answers HTTP 200 with code 90001 | Integration retry logic | Read the V3 API docs; no load test without approval |
| 17 | External portal users are counted per app; group collaborators are not billed | Portal pricing for customers | `Org Admin > User > External User` |
| 18 | API and CLI Access Policies are on for our organisation | The build uses hap-cli and MCP | `Org Admin > Security > Data & Access` (view only) |
| 19 | Org Admin has "Payments & Invoicing" / "Merchant & Payment", and what it offers on Nocoly | Native payment and e-invoicing may be China-only | Open the menu without applying for a merchant |
| 20 | Bluetooth printing (CPCL/TSPL) and PDA key mapping in the Nocoly App, and the broadcast action name | Warehouse labels and scanning | Nocoly Android App on a PDA, if one is available |
| 21 | Contacts visibility (Professional) also hides users in member pickers | Agent or partner isolation | Test rule on a test user only |
| 22 | Field encryption rules and Professional gating; can encrypted fields be filtered or searched? | Bank account and ID numbers on contacts | `Security > Data & Access > Encryption Rule` (view only) |
| 23 | The 1-hour passwordless window for buttons and approvals | Usability of password-confirmed buttons | `Security > Feature` (view only) |
| 24 | Free/Trial external sharing needs enterprise verification (China process) | Trial customers using public forms or the portal | Check on a trial organisation, if one exists |
| 25 | Which control exists for creating and deleting apps (trap 41) | Admin set-up | `Security > Feature` and `Permission Management` |
| 26 | Data sync on Free and the PBP plan gate (conflicting sources) | Plan advice to customers | Ask Nocoly sales or the partner manager |

## 6. Coverage

Every page of the slice, in `read_pages.py` order (`#` = `--offset`). All 88 were read.

| # | URL | Title | Summary |
|---|---|---|---|
| 0 | https://help.nocoly.com/ | Introduction to HAP | Apps are built from 8 modules (worksheet, view, role, workflow, ChatBot, chart, custom page, external portal); SaaS or self-hosted |
| 1 | https://help.nocoly.com/account/bind-delete | Account Binding and Deletion | Bind or unbind phone and email (unbinding needs both); no account merge; only the owner deletes, after leaving all organisations; 15-day cancel window |
| 2 | https://help.nocoly.com/account/faq | Personal Account | Profile menu, 4 languages, privacy, 2FA (SMS, email, TOTP), single-device login, User ID, personal time zone, Google Maps only, PATs and authorised apps |
| 3 | https://help.nocoly.com/account/modify | How Department and Job Title Information Is Displayed | When cards, member pickers and @mention lists show personal or organisation information |
| 4 | https://help.nocoly.com/account/status | Personal Status | Timed status (On Leave, Sick Leave, In Meeting, Work Trip, custom) in chats, @lists and profiles |
| 5 | https://help.nocoly.com/calendar/find | Can't Find an Event? | Past events leave the list view; check sidebar categories or use Month, Week or Day |
| 6 | https://help.nocoly.com/calendar/introduction | Calendar Overview | Meetings with colleagues and WeChat contacts, reminders, discussion |
| 7 | https://help.nocoly.com/calendar/operations | Common Calendar Operations | Create, edit, delete or leave, share; private events show Busy; time zone per event |
| 8 | https://help.nocoly.com/calendar/sync-instructions | Sync Events | Read-only iCal URL for Outlook, Mac Calendar and Google Calendar |
| 9 | https://help.nocoly.com/calendar/time-zone | Time Zone Settings in Calendar | Events convert to each viewer's time zone; task times do not |
| 10 | https://help.nocoly.com/calendar/view-others | Viewing Colleagues' Schedule | Overlay colleagues' calendars; private events show Busy |
| 11 | https://help.nocoly.com/dingtalk/integration-guide | DingTalk Integration Guide | No text in the cache; live it is unlisted with no English body |
| 12 | https://help.nocoly.com/entra/integration-guide | Integrated with Microsoft Entra | Entra sync with optional security-group scope, UPN matching, SSO and "sole login method"; Server app registration |
| 13 | https://help.nocoly.com/faq/all-members | Who Are Considered "All Members/Participants" | Frequent collaborators; who @All reaches in records (no Store Data Only fields), posts, tasks and events |
| 14 | https://help.nocoly.com/faq/browser-cache | How to clear browsing data | Clear cached images and files when pages misbehave after an update |
| 15 | https://help.nocoly.com/faq/desktop | FAQs of Desktop Client | Client settings, clearing its cache folder, screenshot scaling fix |
| 16 | https://help.nocoly.com/faq/hardware-integration-guide | HAP Mobile Peripheral Integration User Guide | PDA scanning (H5 or App), continuous scanning, hardware keys pressing buttons, Bluetooth CPCL/TSPL printing |
| 17 | https://help.nocoly.com/faq/ip | IP and Domains | 5 fixed outbound IPs for webhooks, API calls and code blocks; inbound domains; CDN outside Greater China |
| 18 | https://help.nocoly.com/faq/mute-notification | Mute Notifications | What still notifies when a conversation is muted, by module |
| 19 | https://help.nocoly.com/faq/nfc | NFC Support in HAP Mobile App | Write record and view links to NFC tags (`nocoly://nfc/`); devices, tags, writing steps |
| 20 | https://help.nocoly.com/faq/notification-setting-android | What to do if you can't receive message notifications (Android)? | Push channel choice and phone permissions |
| 21 | https://help.nocoly.com/faq/numbers | Key Usage Limits You Should Know | SaaS and Server limits: fields, subforms, relations, rollups, import, views, workflow nodes, API sizes and rate limits |
| 22 | https://help.nocoly.com/faq/shortcut-key | Keyboard Shortcuts | Global, view, spreadsheet, record, field and subform shortcuts |
| 23 | https://help.nocoly.com/faq/sms-emali-service-failure | Can't receive SMS or email? | Delivery troubleshooting; 10 emails per hour per mailbox; sender domains to allow (Mingdao) |
| 24 | https://help.nocoly.com/faq/sse | Super Search Engine | Platform-wide search: scope by module, searchable field types, title-only default, exclusions, permissions |
| 25 | https://help.nocoly.com/faq/system-browser | Requirements for Systems and Browsers | Windows 10+ or macOS, Android 5+, iOS 9.3+, modern browsers, no IE |
| 26 | https://help.nocoly.com/faq/technology-architecture | HAP SaaS Technology Architecture | React; Java, C# and Node.js on Kubernetes; MySQL, MongoDB, Redis, Kafka, Elasticsearch |
| 27 | https://help.nocoly.com/feishu/integration-guide | Integrate HAP with Lark | Lark app set-up, scopes, user and department sync (mobile, then email), exclude field, Lark sign-in |
| 28 | https://help.nocoly.com/file/introduction | File Overview | File module for storing, sharing and versioning documents |
| 29 | https://help.nocoly.com/file/operations | File Operations | Shared folders, Admin/Editor/Read-only collaborators, uploads, link files, sharing options, properties and logs |
| 30 | https://help.nocoly.com/file/preview-failure | About File Preview Failures | Preview uses Microsoft's online service; complex files may fail |
| 31 | https://help.nocoly.com/file/role-permission | Permissions in File Module | No text; live, the permission matrix is one image |
| 32 | https://help.nocoly.com/file/size-storage | File Size and Storage Limits | Personal quotas (Free 300 MB a month and 5 GB; paid 10 GB a month); app uploads count at organisation level; 1 GB and 2 GB file limits |
| 33 | https://help.nocoly.com/group-chat/contacts | Contacts | Contacts panel; contacts are colleagues and friends; only contacts can be messaged or picked as members |
| 34 | https://help.nocoly.com/group-chat/create | Create Groups and Start Chats | Organisation and personal groups, official (department) groups, chats |
| 35 | https://help.nocoly.com/group-chat/faq | FAQs | Recall rules (10 minutes); departed members' history is kept |
| 36 | https://help.nocoly.com/group-chat/introduction | Introduction to Groups and Messages | Groups (also visibility scopes), temporary chats, the Messages panel |
| 37 | https://help.nocoly.com/group-chat/invite | How to Invite External Users to a Group | External users in groups are not billed; what they can see in posts, projects, tasks, files and apps |
| 38 | https://help.nocoly.com/group-chat/operations | Group and Chat Common Operations | Group settings (official, join approval, close, delete); chat limits |
| 39 | https://help.nocoly.com/group-chat/type | Common Types of Groups in an Organization | Seven suggested group types |
| 40 | https://help.nocoly.com/org/administrators | Organization Administrators | Permission groups (Super Admin and custom), admin and feature permissions, defaults for all members, requests, logs |
| 41 | https://help.nocoly.com/org/basic-info | Organization Settings | Org info (country sets currency, region and calling code; time zone), closing an organisation, Billing Center, announcements |
| 42 | https://help.nocoly.com/org/certification | Identity Verification and SMS Signatures | Verification gates on Free/Trial (external sharing and more); China SMS signatures; unlisted on the live site |
| 43 | https://help.nocoly.com/org/cloud-service | Cloud Services | Keys that let HAP Server use SaaS AI models, billed to SaaS credits; unlisted on the live site |
| 44 | https://help.nocoly.com/org/department-position | Departments and Job Titles | Department tree, managers, disable or delete, member order, import and export; job titles and their members |
| 45 | https://help.nocoly.com/org/group-management | Group Management | Admin control of organisation groups (admins, members, department link, official badge) |
| 46 | https://help.nocoly.com/org/handover-terminate-restore | Work Handover, Offboarding, and Account Restoration | Handover of approvals, node assignees and app roles; offboarding (50 per batch); what is not moved; restore |
| 47 | https://help.nocoly.com/org/home | Organization Admin Home | Edition, seats, credits (1 = USD 1), alerts, auto-purchased add-ons, AI free credits, quotas |
| 48 | https://help.nocoly.com/org/id | Find Your Organization Door ID and Organization ID | 6-digit Door ID for joining; Organization ID for support |
| 49 | https://help.nocoly.com/org/integration | Platform Integration | One identity platform per organisation; WeChat and Twilio services; LDAP; disabling platform login; organisation API key |
| 50 | https://help.nocoly.com/org/link-twilio-international-sms | Integrate Twilio for International SMS | Twilio set-up for SMS outside Mainland China; billing; troubleshooting |
| 51 | https://help.nocoly.com/org/link-wechat-service-account | Connect a WeChat Service Account | WeChat service account for portal QR sign-in, form data, WeChat Pay and template messages |
| 52 | https://help.nocoly.com/org/management-module | Organization Management | Org Admin sections and how to open them |
| 53 | https://help.nocoly.com/org/member-management | Member Management | Invitations, bulk import (fields, limits), activation and pending lists, joining rules, several positions, primary department, batch edit, export |
| 54 | https://help.nocoly.com/org/reporting-structure | Org Chart | Manager tree (one manager each) used in view filters, role scopes and approvers; employee rights |
| 55 | https://help.nocoly.com/org/roles | Organization Roles | Roles across departments in role groups (50 at most), members, responsible departments; used in fields, app roles and approvals |
| 56 | https://help.nocoly.com/org/security | Organization Security Settings | Joining rules, contacts visibility, profile fields, watermark, API and CLI policies, API proxy, encryption rules, feature limits, passwordless window |
| 57 | https://help.nocoly.com/org/thirdapp | OAuth Applications | OAuth 2.0 apps acting for users; admin scope limits; disabling and revoking |
| 58 | https://help.nocoly.com/post/filter | Filtering Posts | All, My Posts, Starred, Groups; type, date and keyword filters |
| 59 | https://help.nocoly.com/post/introduction | Introduction to Post | Posts with text, files, links and polls; system and app posts; visibility |
| 60 | https://help.nocoly.com/post/operations | Basic Operations with Posts | Publish, reply, like, star, permanent delete, edit, visibility, pinning by admins |
| 61 | https://help.nocoly.com/post/scenario | 7 Common Scenarios for Posts | Suggested uses: progress, announcements, ideas, feedback, help, knowledge, goals |
| 62 | https://help.nocoly.com/post/sharing-scope | Recommended Guidelines for Setting the Visibility of Posts | Groups or All Colleagues; "Myself" with @mentions as a private message |
| 63 | https://help.nocoly.com/post/types | Types of Posts | File, link, poll (99 options at most, anonymous or named) and Q&A posts |
| 64 | https://help.nocoly.com/purchase/billing-items | Pricing & Billing | Credit prices for SMS, email, OCR and PDF generation; LLM price link; WeCom API fees |
| 65 | https://help.nocoly.com/purchase/external-user-billing | Billing for External Users | Stub that links to the online purchase page (live as well) |
| 66 | https://help.nocoly.com/purchase/free-edition-faq | free-edition-faq | Stub ("--") |
| 67 | https://help.nocoly.com/purchase/online-purchase | How to Subscribe to a Paid Plan Online | Upgrade, offline purchase, auto-renewal, add-on packs, recharge, seats, external user packs and how they are counted |
| 68 | https://help.nocoly.com/purchase/recharge | Recharge Online | Stub that links to the online purchase page |
| 69 | https://help.nocoly.com/purchase/user-billing | Billing Rules in Paid Plans | Stub that links to www.nocoly.com/pricing |
| 70 | https://help.nocoly.com/purchase/user-package | Purchase User Pack Online | Stub that links to the online purchase page |
| 71 | https://help.nocoly.com/purchase/version-comparison | Compare Nocoly HAP Plans | Free, Standard and Professional limits, extra-usage prices and features by plan |
| 72 | https://help.nocoly.com/task/board | How to Adjust the Task's Board (Stage) | Move a task between boards on the web and in the app |
| 73 | https://help.nocoly.com/task/board-operations | Add a New Board in a Project | Add, reorder, rename and delete boards |
| 74 | https://help.nocoly.com/task/checklist | Checklist | Checklists with a progress bar; an item can become a task |
| 75 | https://help.nocoly.com/task/custom-field | Custom Task Content | Deprecated: custom task content can no longer be edited |
| 76 | https://help.nocoly.com/task/default-owner | Default Task Owner in Each Board | A default owner per board, applied to new tasks |
| 77 | https://help.nocoly.com/task/faq | FAQs | Notifications, bulk actions, parent tasks, subordinates' tasks, project links, locking, sharing templates |
| 78 | https://help.nocoly.com/task/gantt | Gantt View in Task | Project Gantt (day, week, month), planned and actual bars, export as image |
| 79 | https://help.nocoly.com/task/introduction | Task Overview | Tasks, subtasks, comments; projects, roles, public or private, Kanban, folders |
| 80 | https://help.nocoly.com/task/operations | How to Effectively Use the Task Module | Status rules (not started, in progress, completed, overdue variants), filters, sorting |
| 81 | https://help.nocoly.com/task/project-operations | Project Operations | Rename, export tasks to Excel, template, archive, duplicate, hide, folders |
| 82 | https://help.nocoly.com/task/role-permission | Task and Project Role Permissions | What project and task roles can see and edit; parent and subtask visibility |
| 83 | https://help.nocoly.com/task/start-end | Planned vs. Actual Start and End Times of Tasks | Planned and actual dates, Start Now, status rules |
| 84 | https://help.nocoly.com/wecom/disable-integration | Disable WeCom Integration | No text in the cache; live it is unlisted with no English body |
| 85 | https://help.nocoly.com/wecom/integration-note | WeCom Integration Notes | No text in the cache; live it is unlisted with no English body |
| 86 | https://help.nocoly.com/zh-Hans/org/cloud-service | Cloud Services (Chinese page) | Chinese version of Cloud Services, same content as #43 |
| 87 | https://help.nocoly.com/zh-Hans/worksheet/index-acceleration | Worksheet indexes (Chinese page) | Worksheet indexes: up to 5, unique and composite indexes, query advice, auto-indexing on SaaS (English page in the worksheet slice) |

## 7. New since 3 Nov (live check, 23 Nov 2026)

**Method.**
- Downloaded the raw `https://help.nocoly.com/sitemap.xml` (HTTP 200, 352 URLs), `robots.txt` and `https://help.nocoly.com/zh-Hans/sitemap.xml` (395 URLs) with curl. No browser tools were used.
- Read the route table in the site's Docusaurus 3.9.2 bundle (`/assets/js/main.79323f43.js`, 397 English routes).
- Compared all of these with `python -I read_pages.py --list` (359 cached pages) and with the `lastmod` stored in the 3 Nov corpus.

**Result: no page has been added or changed since 3 Nov.**
- **Sitemap:** the 351 documentation URLs are exactly the cached ones, and all 351 have the same `lastmod` as on 3 Nov. The newest `lastmod` is 20 Oct 2026, in both the English and the zh-Hans sitemaps. The only extra URL is `/search`, the search screen.
- **Cached pages missing from the sitemap:** 8 cached pages are not in the sitemap: dingtalk/integration-guide, org/certification, org/cloud-service, wecom/disable-integration, wecom/integration-note, workflow/sms-failure and the two zh-Hans pages. They were found through links on 3 Nov. Live they still return 200, and each carries Docusaurus's banner "This page is unlisted".
- **Unlisted routes never cached:** the route table holds 39 English routes (plus `/search`) that were never cached and are in no English sitemap. All 39 carry the "unlisted" banner. Their Chinese pages are dated 17 Jul 2025 to 20 Oct 2026 in the zh-Hans sitemap (market/intro and market/seller are in neither sitemap). So they most likely already existed on 3 Nov as unlisted pages; when their English routes appeared cannot be proved.
  - 35 have no English body: either the title only, or "The English version of this page is not yet available".
  - 4 have English text; they are summarised below.

| Route (help.nocoly.com/…) | Slice | English content, live 23 Nov |
|---|---|---|
| changelog | this slice | none ("not yet available"); zh-Hans dated 21 May 2026 |
| dingtalk/integration-faq, dingtalk/notification-integration | this slice | title only |
| faq/network-diagnostic | this slice | none |
| file/excel-preview | this slice | none |
| hdp, hdp/account-and-message, hdp/data-mirroring, hdp/etl, hdp/getting-started, hdp/home, hdp/source, hdp/synctask, hdp/troubleshooting-guide, hdp/workspace | this slice | none |
| market/intro, market/buyer, market/seller, market/faq | this slice | title only |
| org/invoice, org/wechat-message-template | this slice | title only |
| **org/payment** | this slice | **read, summarised below** |
| wecom/group-robot, wecom/install-single-app, wecom/integration-faq, wecom/integration-guide, wecom/private-deployment-integration, wecom/self-service-docking, wecom/sync-rule, wecom/ways-login-hap | this slice | title only |
| api/external-system-integration | api | none |
| integration/troubleshooting-guide | integration | none |
| plugin/api-doc, plugin/mdye-intranet-guide | plugin | none |
| **workflow/node-get-payment-link, workflow/node-refund-order, workflow/node-e-invoicing** | workflow | **read, summarised below** (not in the cache, so no other slice has them) |
| worksheet/kuaimai-printing | worksheet | title only |
| worksheet/scratch-excel | worksheet | none |

**Merchant Services and Online Payments** (https://help.nocoly.com/org/payment, unlisted) **[live 23 Nov]**
- **Overview:** online payment from forms through **WeChat Pay and Alipay**. A public form shows the payment page after submission; a worksheet record gets a **Pay** button on its detail page. Refunds are possible.
- **Merchant set-up:** a super admin opens `Org Admin > Merchant & Payment > Merchant`, clicks **Apply** or **Create Merchant** and chooses channels.
- **Fees:** service fee ¥999 a year or ¥199 a month per merchant; aggregate payment rate 0.25%; WeChat Pay and Alipay at their official rates.
- **Limits:** up to 20 merchants; aggregate payments up to ¥10,000 per transaction.
- **Withdrawals:** aggregate payments only, free, available 1 business day after the transaction. Verified merchants cannot be deleted.
- **Orders and refunds:** `Merchant & Payment > Order`.
- **Worksheet set-up:** app admins enable payment in the worksheet's **Extend** tab, for record payments and public-form payments.
  - **Select Merchant:** one collection merchant per worksheet.
  - **Payment Details:** a field shown on the payment page.
  - **Amount:** read from a number field.
  - **Set transaction validity period:** unpaid orders close automatically.
- **The Pay button** is a system button. It can be set separately for internal and external users, limited to some views, shown on conditions and controlled per role.
- **Field mapping** writes the payment details back to fields.
- **Pay Now:** goes straight to payment without a confirmation; the order is "Pending Payment" until paid or cancelled.
- **Submit the form after payment:** public forms only; needs the validity period.
- **Display order information in the record detail sidebar.**
- **Allow refunds:** within 7 days of completion and only by the payer; without the sidebar, admins handle refunds.

**Node – Get Payment Link** (https://help.nocoly.com/workflow/node-get-payment-link, unlisted) **[live 23 Nov]**
- Needs the worksheet's **Worksheet Record** payment option; otherwise the link is empty.
- **Link type:** "Record link with Payment button" (record page with Pay; password, validity period and visible fields can be set) or "Payment link" (straight to the payment page).
- **Link name:** used as the clickable text in emails.

**Node – Refund Order** (https://help.nocoly.com/workflow/node-refund-order, unlisted) **[live 23 Nov]**
- Full or partial refund of a paid order. A partial refund larger than the payment fails.
- **On failure:** "Continue the process" (later nodes get empty refund values) or "Terminate the process".
- An order that has already been invoiced cannot be refunded automatically.

**Node – E-Invoicing** (https://help.nocoly.com/workflow/node-e-invoicing, unlisted) **[live 23 Nov]**
- Issues an invoice from a workflow. Needs an invoicing tax ID ("Enable Invoice Tax ID", whose English page is empty).
- The workflow waits at the node until the result returns.
- **Returned data:** application and invoice dates; invoice type, title, title type, title tax ID, content, number, reference number; status (option); total amount and tax rate; e-invoice URL. Putting the URL in an attachment field downloads the file.
- If the node stays "In Progress", check that the digital tax account is signed in and facial verification is done.

*Inference:* all four pages describe mainland China services (RMB fees, WeChat Pay/Alipay, a China digital tax account). Malaysian payment gateways and LHDN MyInvois still need API integrations, and whether Nocoly SaaS shows a Merchant & Payment menu at all needs a live check (§5, item 19).

**Pricing page against the cached plan page** (https://www.nocoly.com/pricing) **[live 23 Nov]**
- **Same as cached:** usage limits, extra-usage prices and most plan gates. Worksheets: 100 on Free and Standard, unlimited on Professional. Code block, Loop node, API proxy, condition group, global variable, extended user information and data encryption: Professional only.
- **New on the live page:**
  - prices: Free $0 (10 seats at most); Standard $15 per user per month (5 seats at least); Professional by quote (10 seats at least);
  - "Storage is unlimited on all SaaS plans"; the yearly attachment limit resets on 1 January;
  - Professional-only rows: **Contacts visibility**, **App access policy**, **User behavior log**;
  - "PBP API Response" is Professional only, where the cached page said "Packaged Business Process (PBP): Professional";
  - the website language list includes Bahasa Melayu (the website only, not the product).
- **Conflict:** the live usage table shows no data sync on Free, while its feature table shows data sync on Free with 5 tasks and 10,000 rows. The cached plan page says unavailable but also lists 5 sync tasks for Free.
