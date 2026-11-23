# Integration, API and AI in Nocoly HAP: native catalogue digest

| | |
|---|---|
| Slice | `read_pages.py --prefix integration,api,ai,getting-started`: 22 help.nocoly.com pages, cached 3 Nov 2026. All 22 were read in full |
| Purpose | What HAP offers natively for external connectors, APIs, data sync and AI, and what can replace Odoo 20's automatic currency rates, e-invoicing and other connectors, vendor-bill OCR and email-to-record |
| Rule | Native first (Li Wei, 23 Nov 2026). Code blocks, custom fields and Compute only where native cannot do the job |
| Status | Desk survey, written 23 Nov 2026. Read-only: no app, connection, workflow, record or setting was created or changed, and no browser was used |
| Target app | Odoo Replica (AI) `<uuid>`, Nocoly SaaS, CLI profile `<profile>` |
| Companions | `../workflow-nodes.md` (workflow triggers and nodes) and `../../00-foundation.md` (behaviour #13 and decision 7: automatic currency rates) |

**Evidence tags.** Every [Doc] statement is vendor documentation cached on 3 Nov 2026. None of it is a runtime test on Nocoly SaaS.

| Tag | Source | What it proves |
|---|---|---|
| [Doc] | A page of this slice | What the vendor documents |
| [Doc-x] | A help.nocoly.com page outside this slice (same cache), read only to answer the replacement questions. Another digest owns it | Same as [Doc] |
| [KB] | Workspace `knowledge-base/nocoly-mingdao/chapters/` 03, 04, 05 and 16 | Curated earlier reviews, including checks of Nocoly's published API schemas. Not runtime |
| [EMS] | `../../../handover/EMS-Handover-Digital-Omnis.md`, `../../../handover/module-map.md`, `../workflow-nodes.md` | The object exists in EMS on Nocoly SaaS. Not inspected or run in this survey |
| [Obs] | Project memory notes from earlier live work (18–20 Nov 2026) | One earlier data point |
| [Odoo] | `../../catalogue/odoo-20.0/modules.csv` (Odoo 20.0 Community manifests) | The module is in Community. "Absent" suggests Enterprise-only |
| [Inference] | My reasoning or a proposed design | Untested |

## 1. Summary

- **Integration Center connections are the native connector layer** [Doc]. One connection holds the authentication (none or API key, Basic, OAuth 2.0 client credentials with token refresh, or OAuth 2.0 authorization code per user) and several published APIs with typed inputs and outputs, plus optional JavaScript/Python code before or after each call. API Query and OCR fields, control events and the Call Integrated API node all reuse it. There are 200+ ready templates. Plans: Standard and Professional [Doc-x].
- **Inbound** = a webhook-triggered workflow or API V3 (AppKey + Sign, PAT, OAuth 2.0). **Outbound** = Send API Request or Call Integrated API. **Polling** = a scheduled workflow [Doc] [Doc-x].
- **Automatic currency rates can be fully native** [Inference]: scheduled workflow → rate API (the docs' own teaching example is an exchange-rate GET) → parse → Add Record. This needs no Compute, and no code if the JSON path can be fixed.
- **MyInvois has no native feature** [Doc] [KB]. Build it as a connection with OAuth 2.0 client credentials plus button and scheduled workflows, as EMS already did [EMS]. Building, hashing and signing the document is the part likely to need code or a middleware [Inference].
- **Vendor-bill OCR is native in two ways**: the OCR field (preset invoice template or your own OCR API; lines only into a subform; PDFs read on page 1 only), or AI nodes with an image-capable model. Mingo's AI Auto Fill covers one-off entry. Accuracy on Malaysian bills is unproven [Doc] [Doc-x].
- **The docs show no inbound email.** Email-to-record needs an external inbound-mail service posting to a webhook, or a public form in place of the mail alias. Send Email cannot set the sender address [Doc-x] [Inference].
- **Data Integration (Professional)** gives real-time database↔worksheet sync, ETL (filter, join, group, merge) and mirroring to MySQL or PostgreSQL. Multi-row relations, OCR, API Query and several other field types do not sync [Doc].
- **AI building blocks:** AI Action on the record page, ChatBot (a chat-triggered workflow), the AI Agent / Generate Text / Generate Data Object nodes (always billed in credits), Mingo (app builder, data query, auto-fill) and MCP/CLI/Skills for scripted building [Doc].
- **Main traps:** Mingdao versus Nocoly API host, two conflicting outbound-IP lists, webhook URLs open by default, Professional-only Code Block/PBP/Loop/Data Integration, and names with spaces or special characters breaking Data Integration [Doc] [Doc-x] [KB].

## 2. Capability inventory

### 2.1 Integration Center: API connections (`integration/api`)

| Item | What it does | Options and values (UI names) | Limits and notes |
|---|---|---|---|
| Entry and modules | Stores third-party authentication and request settings once, for apps that are allowed to use them | Home > [Integrate] > [API Integration]. Tabs **My Connections** and **API Library**. The library has a **Public Library** (HAP's prebuilt templates; connection settings are read-only and you only fill in parameters) and an **Organization Library** (admins publish internal connections; other users request access) | "Over 200" templates; the worked example is Tianyancha, a Chinese company registry [Doc]. Plan: "API integration" on Standard and Professional [Doc-x version-comparison]. Org admins can limit who may "Create API connections" [Doc-x org/administrators] |
| Where a connection is used | Same credentials and API reused across the app | **API Query** and **OCR** fields; **Call Integrated API** action in control events; **Call Integrated API** node; **API Authentication & Connection** node | Only published APIs, only for authorised apps [Doc] |
| Install a template | Quick start | Search > **Install** > paste the provider's token > enable the APIs you need > authorise applications > add an API Query field | You register with the provider and hold the key [Doc] |
| Custom connection: authentication | How each request authenticates | [+ Custom Connection] > [Create Custom Connection], then one of: **[API Key or No Authentication]**; **Basic Auth** (username and password, fixed or from connection parameters); **OAuth 2.0 (Client Credentials Grant)** (default parameters `app_id` and `app_secret`, which can be renamed; **[Get Access Token]** to test; token expiry for automatic refresh); **OAuth 2.0 (Authorization Code Grant)** (Redirect URI generated by HAP, Authorization URL, Token URL; the identity is per user, and the **Account** section renames, deletes, reauthorises or manually refreshes each account) | [Doc] |
| Connection parameters | Provider-issued values (for example WeCom `corpid` and `corpsecret`), usable for auth and inside request payloads | Each value **hidden** or **visible** | Hidden values are encrypted. They can be replaced but **never revealed** again [Doc] |
| Connection basics | — | Name, logo, description | [Doc] |
| API definition | One reusable request with typed input and output | **API Management** > **Create API**: name, description, icon, colour. **Input parameters**: types Text, Number, DateTime, Members, Department, Attachment, Array, Object Array; required flag; default value; alias. **Custom code blocks** (JavaScript or Python) to reshape inputs before the call or the response after it. **Request**: URL, Query Params, Headers, Body, filled from connection parameters, inputs and auth. **Test API**. **Output parameters** (JSON parsing). **Publish** | Attachments arrive as `["URL1","URL2",…]`. Aliases allow only letters, digits, `_` and `-`. Four documented rules decide when object-array items are validated. All APIs of one connection share its credentials. Only published APIs can be used [Doc] |
| Authorize to Application | Ownership, alerts and access | **Connection owner** (can view and edit; receives alerts); **error notification** on or off, with a minimum interval between alerts; **authorise applications** | Only applications **in the same organisation** can be authorised [Doc] |
| Management | Moving and auditing connections | More > **export**, **import** or **upgrade** a connection; enable or disable single APIs; **usage references** (the worksheets and workflows that use an API, with links); **request logs** (parameters and results) | Upgrading keeps each parameter's hidden/visible setting. Log access follows user permissions [Doc] |
| Publish to the API Library | Share a connection | ⋮ > **Apply for API Library**; later **Apply to publish new version** | Review takes 1–3 business days. Logo, descriptions, product introduction, official website and integration overview are required; contact details are recommended. To give users an updated API you must duplicate it and disable the old one. SaaS users then click **Add API**; Server users reinstall the connection [Doc] |

### 2.2 Calling APIs from forms and workflows (cross-reference)

These belong to the worksheet and workflow digests. They are listed here because every replacement in §3.1 depends on them.

- **API Query field** [Doc-x worksheet/control-api-query]
  - Source: a pre-integrated API or a PBP.
  - Display: **Button**, **Dropdown List** or **Searchable Dropdown List**. Searchable options: **Button-Triggered Search** or **Real-Time Search** (more API calls), minimum character length, and **Make a request before searching** (sends an empty keyword).
  - Multi-row results go to a subform (Button mode) or become dropdown options.
  - Plan: Standard and Professional [Doc-x].
  - From this slice's `integration/parameters` [Doc]: an API Query field cannot run at record creation when its input comes from an attachment. A simple array is passed as comma-separated text. An object array can only come from a subform or a multi-record relationship. If the data lives only in the current record, use a button workflow instead.
- **OCR field** [Doc-x worksheet/control-ocr]
  - API type **System Preset** (0.15 credits per call on that page, but 0.03 credits per file on the billing page [Doc-x purchase/billing-items]) or **Integration Center** (no platform fee; you pay the provider).
  - Templates include ID card and invoice. ID and general text recognition accept images only. Invoice recognition accepts PDF and images, but **only the first page of a PDF** is read.
  - Results go to the current record (no batch upload) or to a subform (batch upload allowed). The source image can be saved to an attachment field. On mobile, **Disable Album** forces the camera.
  - **Invoice lines must go to a subform, not a relationship field.** If a tax rate shows 0, set the field to 2 decimals.
- **Control events** [Doc-x worksheet/event]: the actions **Call Integrated API** and **Call Packaged Business Process** map returned values into the record. They run on the record create and detail pages only, not when editing in a view or in bulk.
- **Workflow nodes** [Doc-x]
  - **Send API Request:**
    - **Send Custom Request** (GET, POST, PUT, DELETE, HEAD, PATCH) or **Send Specified Data Object**.
    - Body as form-data, x-www-form-urlencoded, raw or binary (one file).
    - Proxy and SSL options, success status codes and error messages.
    - A request over **10 s** times out; you then choose **Continue Execution** or **Terminate Workflow**.
    - An array response needs a Get Multiple Data node.
    - Pushed data needs an HTTP 200 within 10 s, otherwise it is retried up to 10 times.
  - **Call Integrated API:** stop or continue on failure. Multi-row results go through Get Multiple Data → Add Record.
  - **API Connection and Authentication:**
    - Basic Auth gives base64(username:password) without the `Basic` prefix.
    - OAuth 2.0 client credentials. Token lifetime defaults to 7,200 s (range 0–604,800; 0 = never cached).
    - Any JSON response counts as success, even without a token.
  - Plans: Call integrated APIs on Standard and Professional; Code Block, PBP, Loop and API Proxy on Professional only [Doc-x version-comparison].
- **Attachments by URL** [Doc-x worksheet/workflow-api-upload-file]
  - A workflow file field takes `["url1","url2"]`. API V2 takes `"url1,url2"` or Base64 (`valueType` 2 with `controlFiles`); `editType` is 0 to overwrite or 1 to append.
  - URLs must be reachable by the platform, directly downloadable and end in a file extension.
  - A batch add with attachments can time out. Save the URLs to a text field first and upload them in a workflow.

### 2.3 Inbound data: webhooks and pulls

- **Webhook-triggered workflow** (`api/external-data-webhook` [Doc]; details in `workflow/trigger-by-webhook` [Doc-x])
  - Each workflow gets a unique URL. The external system POSTs to it [Doc].
  - Parameters come from **Generate from Sample Request**: you must send a test request within **3 minutes** [Doc]. Other options are **Generate from JSON Example**, **Generate from Key-Value Pairs** and **Generate Full Body Parameter**. A missing required parameter returns "Missing required parameter" [Doc-x].
  - An Add Record node maps the data; then you publish. In the doc's test the record appears "within about 10 seconds" with **Creator = "Workflow"** [Doc].
  - Security: by default **anyone who has the URL can send requests**. Options: **Use App Authorization** (the request must carry AppKey and Sign) and **App IP Whitelist**. The response method and content can be customised (the doc gives the path [Workflow Configuration] > [AI Capabilities]). Enabled webhook flows appear in the app's API docs [Doc-x].
  - Limit: 10,000 requests per hour per webhook [Doc-x workflow/workflow-execution-limits].
- **Pulling external data** (`api/get-external-data` [Doc]): a worksheet-event trigger on the phone field → Send API Request (GET, with the provider key inside the URL) → a Code Block that first strips "+86" → Update Record.

### 2.4 Open APIs (`api/introduction`, `api/v3`, `api/write-data-to-worksheet`, `api/basics`)

| Item | Facts (UI names) | Limits and notes |
|---|---|---|
| Organization API | Users, departments, reporting lines, logs, workflow to-dos. Org Admin > Integration > Misc. > **Open API** shows the AppKey and SecretKey. Docs: `www.nocoly.com/apidoc/organization` [Doc] | Org-level keys; not the same as app keys [KB 04] |
| Application API | Generated for every app. Menu next to the app name > **API Developer Docs**. **Authorization Management** > **Create Authorization Key**. An app can have several keys, each with an AppKey, a Sign and an API permission scope (for example one per external system) [Doc] | Key creation is for app admins only; the page is "not available to developers or operators" [Doc] |
| API V2 | Action-style endpoints per worksheet, e.g. `POST https://www.nocoly.com/api/v2/open/worksheet/addRow` with `appKey`, `sign`, `worksheetId`, `controls[{controlId, value}]` and `triggerWorkflow`. Returns the new row id. Worksheet and field **aliases** can replace IDs. The docs show a **Field Information Table** (field ID, name, type, type code, description), a view table and a **Filter Generator**. Shared V2 docs hide credentials and can carry an expiry date and password [Doc] | Records written by API show **Creator "API"** [Doc] |
| API V3 | REST paths that are the same for every app. Docs: `www.nocoly.com/apidoc/application_v3`. Auth: **AppKey + Sign** (headers `HAP-Appkey`, `HAP-Sign`; acts as **application administrator**; long-lived; for server integrations), **PAT** (`Authorization: Bearer`, plus `HAP-Appid` for some APIs; the user's own permissions; configurable expiry and scope) or **OAuth 2.0** (short-lived tokens with refresh; for third-party apps). Methods: GET, POST (create and complex queries), **PUT (replaces the whole resource and clears omitted fields)**, PATCH (partial update), DELETE. Envelope: `success`, `error_code`, `error_msg`, `data` [Doc] | System fields are renamed: `ownerid`→`_owner`, `caid`→`_createdBy`, `ctime`→`_createdAt`, `utime`→`_updatedAt`, `uaid`→`_updatedBy`, and `wf*`→`_processName` … `_processStatus` [Doc] |
| V3 endpoint groups | Users and organisations; apps (list, create, info, sections, items, update, delete); worksheets (list, create, schema, update structure, delete); records (filtered list via `POST …/rows/list`, get, create, PATCH, logical or permanent delete, batch create/update/delete, relations, **pivot**, **share link** with password and expiry, logs, discussions, read only); views (batch create); charts (create); custom pages (update); workflows (triggerable list and details, **trigger** `POST /v3/app/workflow/hooks/{process_id}`, create, batch nodes, delete node, delete, schema, validate, publish); workflow to-dos (list, details, batch approve, revoke, return, terminate, urge); ChatBots (create); roles (CRUD, members); vector knowledge bases (list, search); lookups (departments, regions, users); option sets (CRUD) [Doc] | The overview page's 36-row table is only a subset [Doc] |
| Hosts | The V3 page gives HAP SaaS = `https://api.mingdao.com` and Server = `{host}/api` [Doc] | Nocoly's own V3 and organization schemas give `https://www.nocoly.com/api` [KB 04]. See trap 1 |
| Rate limits | Per **source IP** only; no app or user limits. `addRow`, `addRows`, `editRow`, `editRows`, `deleteRow`, `getFilterRowsTotalNum`, `getFilterRows`: 50 QPS each; write bodies up to 16 MB; other APIs unlimited. Server: unlimited QPS, 25 MB. Over the limit → HTTP 503 with `error_code` 90001; too large → HTTP 413. Advice: retry, pause between calls (about 200 ms), split batches [Doc] | The table names V2 endpoints; whether it covers V3 is not stated [KB 04] |
| Error codes | General codes such as 10005 (no permission), 10006 (exists), 10007 (missing or deleted), 10102 (bad signature), 100005 (duplicate value), 430019 (required field empty), 430021 (business rule failed), 90000 (request limit). OAuth codes 600000–600320 (for example token expired, scope changed, redirect mismatch, client IP not whitelisted) [Doc] | — |
| API Basics | A primer on endpoint, method, parameters, auth (API key, token, appKey + sign), headers and body. Three examples, all set up in **Send API Request**: an exchange-rate GET (`https://api.frankfurter.dev/v2/rates?base=USD&quotes=CNY` returning `{"base":"USD","date":…,"rates":{"CNY":7.18}}`), a Bearer-token GET, and a V2 addRow POST with a Raw (JSON) body [Doc] | Teaching examples, not endorsements |

### 2.5 Data Integration, ETL, mirroring and scheduled sync

| Database | Source | Destination | Versions and notes [Doc] |
|---|---|---|---|
| Worksheet | yes | yes | — |
| MySQL | yes | yes | 5.6, 5.7, 8.0.x; Alibaba Cloud and Tencent Cloud |
| SAP HANA | yes | no | Scheduled sync only (the only source with it) |
| SQL Server | yes | yes | 2012, 2014, 2016, 2017, 2019; Alibaba and Tencent Cloud |
| Oracle | yes | no | 9i, 10g, 11g, 12c+ |
| PostgreSQL | yes | yes | 9.6, 10, 11, 12+ |
| MongoDB | yes | yes | ≥ 3.6; Alibaba and Tencent Cloud |
| MariaDB | yes | yes | ≥ 10.3; Alibaba and Tencent Cloud |
| IBM DB2 | yes | no | 11.5x |
| Kafka | yes | no | 2.3.x |

- **Access:** [Integrate] > Data Integration. Only **Org Super Admins and App Admins** see it, and the source list shows only apps where you are app admin [Doc].
- **Set-up:**
  1. A **connector** (source + destination, **Test Connection**, set-up guide on the right).
  2. **Sync tasks**, one per table ("Create X Sync Tasks"), in mode **Sync data only** or **Require data processing while syncing** (ETL).
  3. Field mapping.
  4. Destination:
     - **Existing Worksheet:** a matching field decides duplicates, which are **overwritten** or **skipped**; option "Clear existing data in the target worksheet before syncing".
     - **Create New Worksheet:** name, fields, field names and types, title field.
  5. Per task, whether synced adds, updates and deletes **trigger workflows** [Doc].
- **Timing:** real-time by default. Scheduled sync exists only for SAP HANA (`integration/timed-synchronization`): every hour or at a set daily time. **Full Data Sync (Overwrite)** needs a primary key. **Incremental Sync** needs a **Matching Field** that is a primary key, a datetime/timestamp or a number, and starts from its minimum value [Doc].
- **Deletes:** destination rows in the recycle bin are not re-synced until restored. Permanently deleted rows never return; you need a new task [Doc].
- **Field types that do not sync:** Uppercase (25), Remarks (10010), Free Link (21), Embed (45), Section (22), Tab (52), Relationship with multiple rows (29), Foreign Field (30, "sync only"), Signature (42), Barcode (47), API Query (49), OCR (43), Query Records (51) [Doc].
- **System fields that do sync:** rowid, ownerid, caid, ctime, utime, uaid, wfname, wfcuaids, wfcaid, wfctime, wfrtime, wfftime, wfstatus [Doc].
- **Names:** an app, worksheet or field name with special characters (the listed set includes `( ) - , . /` and Chinese punctuation) **or spaces** may block selection or break the sync [Doc].
- **Operations:** data is written in queued batches, so speed varies with load. The Data Sources page reuses saved connections, with passwords stored encrypted. The **Statistics** tab shows records read and written this month, up to 6 months of history and per-task logs [Doc].
- **ETL nodes** (`integration/etl`) [Doc]:
  - **Data Source:** several per task.
  - **Data Destination:** exactly one per task.
  - **Filter:** conditions and condition groups.
  - **Join Tables:** Inner, Left or Right, across HAP and external databases. A source cannot be joined twice, field names must be unique, and a DB primary key or worksheet row ID is required.
  - **Group Summary:** Text gets Max/Min; Number and Date get Sum/Avg/Max/Min; Count counts rows. Only the group and summary fields pass on.
  - **Merge Tables:** UNION, UNION ALL, INTERSECT, INTERSECT ALL, EXCEPT, EXCEPT ALL. Only same-name, same-type fields merge.
- **Mirroring** (`integration/datamirror`): Integration > Data Integration > **Worksheet Data Mirror** > **Create Mirror** (app, worksheet, data source, database). Destinations: **MySQL and PostgreSQL only**. You can preview or delete a mirror [Doc].
- **Plans** [Doc-x version-comparison]:
  - Data integration, sync, ETL and mirroring are listed under **Professional**.
  - The same page gives Standard a sync capacity of 100,000 rows/month (Professional 500,000), with extra rows at $5 per 100,000.
  - It says both "Data synchronization tasks: Free 5" and "Data synchronization: Free unavailable".
  - These entries conflict.
  - Org admins can limit who may "Create sync tasks" [Doc-x org/administrators].

### 2.6 BI (`api/bi-integration`)

- **SaaS:** BI tools read worksheets through the open API. Named tools: SmartBI, NetEase YouData BI, Alibaba Cloud DataV [Doc].
- **Server:** BI tools read the database directly. Named tools: Power BI, Tableau, SmartBI, Hengshi BI, FanRuan BI [Doc].
- On SaaS, Power BI or Tableau would need the API or a MySQL/PostgreSQL mirror (§2.5) [Inference].

### 2.7 AI features

**Billing** (`ai`) [Doc]:
- **Always charged against credits:** the AI Agent, AI Generate Text and AI Generate Data Object nodes.
- **AI free credits first, then organisation credits:** Mingo building apps, worksheets and records, sample data, name and icon optimisation, AI translation. Org admins can stop Mingo from using organisation credits (Org Admin > Home > Credits > Manage).
- **Currently free:** AI Generate Code Block, AI Custom Field. Mingo's product help is free [Doc ai/mingo].
- AI credits per plan: Free none, Standard 15/month, Professional 28/month. Per-model prices are at `www.nocoly.com/billingrules` [Doc-x].

**Mingo** (`ai/mingo`) [Doc], opened anywhere with the **M** key:
- **AI Application Builder:**
  - Two phases, **Planning** and **Application Generation**.
  - Mingo asks design questions and produces an editable plan. You can upload a requirements document.
  - The estimated credits appear next to **Create Application**.
- **AI Worksheet Generation:**
  - Opened from **Build** > **Create Worksheet**, or **Create with AI**.
  - Creates the icon, fields, layout and option values, optionally related worksheets, and can start from an image of a table.
  - **Relationship fields need their target chosen by hand.**
- **AI Sample Data:** **Populate Sample Data** or **AI Generate Sample Data**, then **Generate Now**, **Add to Worksheet** or **Clear**. Only app admins, operators and developers can use it. The data is fictional and fills every non-read-only field.
- **AI Record Creation:**
  - Opened with **AI Auto Fill** on the create page, or M > Create a Record.
  - **Smart Fill** on: AI infers missing values and may search the web; such values are marked ✨. Smart Fill off: only what the user gave is written.
  - Works from images too (the doc's example is a business card). The user reviews, then clicks **Submit**.
- **Optimize Name and Icon** for apps.
- **Data Query and Analytics:**
  - Answers within the user's permissions. Covers app information, structures, records, "my / my department / my manager / direct reports", approvals, the contents of attachments (Word, Excel, PowerPoint, PDF, text, images), the vector knowledge base, and statistics.
  - Charts: pie, column, bar, line, area, funnel, rose, radar, word cloud, heatmap, KPI card, gauge, dual-axis.
  - Diagrams: flowchart, ERD, state, Gantt, timeline, mind map, quadrant.
- **Product Help** with links to the docs.
- **Limits:**
  - 5 files per message; images ≤ 5 MB; documents ≤ 10 MB; at most 50,000 words across documents (the rest is ignored).
  - Formats: Word, WPS, PDF, PPT, TXT, Markdown, JSON, XML, YAML, LOG, PNG, JPG.
  - **No role-based access control for Mingo.** Org feature permissions can switch Mingo features on or off per member [Doc-x org/administrators].

**AI Action** (`ai/ai-action`) [Doc]:
- **What it is:** a button in the record page's top action bar. It opens a multi-turn chat about that record, with its fields, discussions and logs injected as context.
- **Setup:**
  - Go to [Form Settings] > [More Settings] > [AI Action] > **+ Add**, describe the goal (or pick a suggestion) and click **Create**.
  - Edit the name, description and **enable conditions** (a filter; records outside it cannot use the action).
  - **Configure** the agent: model, prompt, memory turns, preset reply style, tools. Prompt context options are **All Fields** and **Comments Info**.
- **Safety:**
  - **Access Based on User Permissions** keeps the agent within the current user's rights.
  - **User Confirmation Required Before Execution** makes the user approve Add Record or Update Record first.
- **Running it:**
  - **Test** with a chosen record.
  - **Action History** shows past chats.
  - Per role: Role & Permission > Access Selected App Items.
  - A workflow is generated automatically for each action, and **no further nodes can be added** to it.

**ChatBot** (`ai/chatbot`) [Doc]:
- **What it is:** an app item. With **Access to All App Items** everyone can use it; with **Access to Selected App Items** a role needs **View**. External users follow the same rules.
- **Creating it:** **＋ Create** > **ChatBot**, then describe its purpose; the configuration is generated for you.
- **Settings:**
  - Name, Avatar (PNG or JPG), Welcome Message, **Suggested Questions (up to 5)**, Share Chat, Setup Process.
  - **File Uploads:** PNG, JPG, JPEG, PDF, Word and Excel; up to 5 per message; images ≤ 5 MB; documents ≤ 10 MB.
- **Conversation workflow:**
  - The trigger outputs the user's message, attachments and user info.
  - Each AI Agent node's output becomes a reply.
  - A round ends when all nodes finish, or at an **Approval, Fill in, Delay, Subprocess, PBP or Initiate Approval Flow** node.
- **Agent options in chat:**
  - **Memory Rounds** 0–10 (default 5; per session only).
  - **Use System-Preset Reply Style** (on by default).
  - **By user permissions** (on by default; off = **bypasses permission checks and reads all data**).
  - **Require Confirmation Before Execution.**
- **Tools for operators:**
  - **Test**; logs per round (test chats do not appear in the history list); **View Details**; **Feedback to Platform** (sends the prompt, AI reply and tool parameters only).
  - The bot can be distributed, upgraded and published with the app. It can also be created through `POST /v3/app/chatbots` [Doc api/v3].
- **For users:**
  - Text, files, voice-to-text and a stop button.
  - A 30-day personal history, deletable. **New Chat** starts a fresh context.
  - **Share** creates a public link with copy, QR code, password and expiry. Visitors see a snapshot; signed-in users can continue with their own permissions.
- The ChatBot itself has no direct data access: its tools follow workflow and worksheet permissions.
- Plan: ChatBot and AI Agent are on Free, Standard and Professional [Doc-x].

**Agent practice** (`ai/best-practices-for-agent`) [Doc]:
- **Tools:** Query Records, Add Record, Update Record, Rollup, PBP, integrated APIs, notifications and email. **Structured output** returns JSON for later nodes.
- **Models with image input:** GPT-5, GPT-5-mini, GPT-5-nano, GPT-4.1, GPT-4.1 mini, GPT-4o, GPT-4o-mini, o3, o4-mini.
- **Text-only models:** DeepSeek-V3, Qwen Turbo, Qwen Plus, Qwen Max.
- **By complexity:** simple tasks GPT-5-nano or Qwen Turbo; moderate GPT-5-mini (the default advice); complex GPT-5 or o3.
- **By User Permissions** applies to ChatBot workflows only (on by default).
- **Require User Confirmation** works only in conversation workflows. It covers Add Record, Update Record, Send Internal Notification, Send Email, Call PBP and Call Integrated API.
- Pick the worksheets by hand and narrow queries with filters.
- **Cost:** split tasks across cheap models, keep toolsets small, limit memory rounds, ask for JSON.

**AI workflow nodes** (cross-reference) [Doc-x]:
- **AI Generate Data Object:**
  - Models GPT-4o-mini, GPT-4o, QWen-Turbo/Plus/Max, DeepSeek and others.
  - Takes a prompt (fixed text and node values) and object parameters, each with Name, Type and Description. **More Settings** has System Message and Temperature.
  - Outputs the parameters, the history JSON and the tokens used.
- **AI Agent:**
  - **File Link** passes file fields as context. Images need an image-capable model; documents go to a document-analysis service, which may cost more.
  - Tools come in four groups: data, notification, PBP and integrated APIs. Worksheet scope is **All Worksheets** or **Specific Worksheets**, and query filters narrow it further.
  - Outputs: AI Generated Result, AI Model, Token Usage, structured output, and fields from tool calls (**first row only** when several are returned).
  - Get Record Discussions returns at most 50 entries. Query Records is not a vector search.

**Other AI items** (`ai`) [Doc]:
- **AI Custom Fields:** React + Tailwind widgets written through chat.
- **AI Code Block Generation:** JavaScript or Python, inside the Code Block node.
- **AI Translation** of app content.
- **Vector Knowledge Base** and the **Knowledge Retrieval** node (semantic, keyword or hybrid search; returns snippets, sources and scores).
- **HAP for VS Code** (view plugins) and **Dify** (an assistant on live app data).

### 2.8 Connect AI, MCP, CLI and Skills (`ai/connect-ai`, `ai/mcp`, `ai/cli`)

- **Connect AI portal** (top right of the HAP home page) [Doc]:
  - Methods **MCP**, **CLI** and **Skills**, each with **Interactive Installation** or **Manual Installation**.
  - You pick the AI tool, or **Misc.** if it is not listed. The **Install Related Skills** option installs the skills at the same time.
- **MCP access modes** [Doc]:
  - **Personal:** a Personal Access Token, with the user's permissions.
  - **Application:** an app plus its authorization key, with the app's scope.
- **HAP MCP endpoint:** app **API Documentation** > **MCP** tab > copy the URL. Config examples are given for Cursor; for Dify ("MCP SSE / StreamableHTTP" plugin for agent apps, "Agent Strategies (Support MCP Tools)" for workflows; `transport: streamable_http`); and for VS Code + Cline (`type: streamableHttp`) [Doc].
- **APIfox MCP** (`apifox.nocoly.com`) only lets a model read the API docs; it cannot act [Doc].
- **Personal Access Token** [Doc]:
  - Org Management > **API Access Policy** > **Personal Access Token** must be enabled first.
  - Create it under avatar > Manage My Account > Personal Access Token > **Add**, with Name, Expiration period, Organization, Application scope and API scope.
- **Application authorization key:** app **API Documentation** > **Authorization Management** > **Create Authorization Key** [Doc].
- **Skills** [Doc]:
  - **MCP Skill:** app building; needs MCP set up.
  - **CLI Skill:** create and manage apps, query data; needs the CLI installed and signed in.
  - **API Skill:** V3 integrations, view plugins, front-end development; needs API auth.
- **CLI** (`pip install hap-cli`) [Doc]:
  - **Org Admin Console > Security > Data & Access > CLI Access Policy** must allow it; `hap auth list-my-orgs` shows CLI:on/off.
  - Login: `hap auth login` (default), `mingdao`, `nocoly` or a Server URL; `--token` for scripts.
  - Named profiles: `--profile` beats `HAP_PROFILE`, which beats the active profile. Default org and app can be set.
  - `--json` on every command; a REPL.
  - Command groups:
    - `auth`
    - `app` (including backup/export, usage/logs, roles, option sets with cross-app migration, knowledge search)
    - `worksheet` (rules, switches, form settings, custom actions, charts, views)
    - `worksheet record` (CRUD, batch including subforms and related records, relations, share links, discussions, logs, pivot, bottom stats)
    - `workflow` (structure, history, stats, create/update/copy/move/delete, publish/rollback, trigger and trigger-pbp, config, approval containers, nodes including code/webhook/AI tests)
    - `approval` (to-dos, actions, revoke/terminate/restart/retry, batch, delegation)
    - `custom-page`, `contact`, `department`, `post`, `calendar`, `chat`, `region`, `icon`, `upload`, `config` (languages en, zh-Hans, zh-Hant, ja), `update`

### 2.9 Get Started page: platform pieces the rebuild uses (`getting-started`)

- **Core modules:** Worksheet, View, Roles and Permissions, Workflow, ChatBot, Chart, Custom Page, External Portal [Doc].
- **Public form:** Edit Form > Extend > **Enable Public Form**, with logo, background, description and visible fields. It is shared by link or QR code, and people submit without signing in [Doc].
- **Records:** entered by hand or imported from Excel. The record page can edit, share, comment, print and delete; bulk actions exist. Also named: business rules, custom actions and Word print templates [Doc].
- **Relations:** a relationship field (single or multiple records, two-way).
  - A **foreign field** is either **Display only** (live display) or **Data storage** (a stored copy that can be filtered, sorted and calculated).
  - A **concat** field can serve as the title field [Doc].
- **Views:** Table, Kanban, Org, Gallery, Calendar, Gantt, Map, Resources, Details, Custom [Doc].
- **Roles:** App Admin (cannot be changed) and the default roles Member and Read-only. Access can be granted by view, by record and by field [Doc].
- **Workflow triggers:** Worksheet event, Scheduled, Date field (for example 15 minutes before a time), Webhook, Button. The example nodes are CC, Branch, Get Single Data (from a relationship field) and Update Record [Doc].
- **Custom page components:** Button, Chart, Filter, View, Carousel, Text, Image, Embedded URL. Containers: Tabs and Card [Doc].
- **Integrations:**
  - API integration (Integration Center, and the Send API Request node).
  - Data Integration (external databases, sync, ETL, middleware between databases).
  - DingTalk, WeCom and Feishu (SSO, contacts, message sync) [Doc].
  - The org-level page adds WeLink, Microsoft Entra, LDAP, Twilio SMS and a WeChat service account. Only one third-party platform can be integrated per organisation [Doc-x org/integration].

### 2.10 Plan and billing gates that touch this slice (cross-reference)

| Capability | Free | Standard | Professional |
|---|---|---|---|
| API developer documentation | yes | yes | yes |
| API integration (Integration Center), API Query fields, Call integrated APIs node, Interface push | no | yes | yes |
| Code Block, API Proxy, PBP, Loop | no | no | yes |
| Data integration, sync and ETL; worksheet data mirroring | no | listed as no, but given 100,000 rows/month | yes, 500,000 rows/month |
| ChatBot, AI Agent | yes | yes | yes |
| AI credits | none | 15/month | 28/month |
| Workflow executions | 1,000/month | 100,000/month | 500,000/month |
| LDAP/AD | no | yes | yes |
| WeCom, DingTalk, Feishu/Lark, WeLink | no | no | yes |

Source: [Doc-x purchase/version-comparison].

Pay-as-you-go prices, at $1 = 1 credit [Doc-x purchase/billing-items]:
- Email: 0.002 credits per recipient (To + CC).
- OCR Service: 0.03 per file.
- Generate PDF: 0.03 per generation; failed conversions are free.
- SMS: 0.007 per message in mainland China; 0.34 international.

## 3. Odoo rebuild notes

### 3.1 Replacing Odoo's external features

| Odoo feature | Native HAP replacement | Where native falls short |
|---|---|---|
| **Automatic currency rates**: `currency_rate_live`, absent from the 20.0 Community catalogue, so Enterprise [Odoo]. Provider choice, interval, "Update now" | Scheduled workflow + Send API Request (or a connection + Call Integrated API) → parse → Add Record in Currency Rates. A button runs the same sub-process for "Update now". The schedule offers hourly, daily, weekdays, weekly, monthly, yearly and custom [Doc] [Doc-x] | No provider list: you choose and maintain the API. The legal rate source is a business decision (BNM or ECB, EMS handover §4.2). Avoiding a duplicate rate per date is your job. A response keyed by currency code needs one fixed path per call, or code |
| **MyInvois e-invoicing**: `l10n_my_edi`, `l10n_my_edi_pos`, `l10n_my_ubl_pint` are Community; `l10n_my_edi` depends on Odoo's EDI proxy client (`account_edi_proxy_client`) [Odoo] | A connection with **OAuth 2.0 (Client Credentials Grant)** and one API per MyInvois call; a button workflow submits, a scheduled workflow polls status; a documents sheet; a print template with QR [Inference]. EMS already runs this pattern [EMS] | Building the UBL document, the SHA-256 hash, Base64 and any digital signature need code (connection code block or Code Block, which is Professional) or a middleware [Inference]. Credentials are per organisation |
| **Other connectors**: payments (`payment_stripe` and others, Community); carriers (`delivery_dhl`, `delivery_fedex`, `delivery_ups` absent, so Enterprise); `partner_autocomplete` and `crm_iap_enrich` (IAP); `sms` (IAP); `google_calendar`, `microsoft_calendar` [Odoo] | Connection + API Query field, control event, Call Integrated API, Send API Request, webhook trigger. API V3 for systems that call in [Doc] | Webhook signatures are not checked natively [KB 04]. The library's examples are Chinese services (Tianyancha, Juhe) [Doc]; Malaysian providers must be checked. No calendar sync is documented |
| **Vendor-bill OCR**: `account_invoice_extract` absent, so Enterprise; Odoo IAP [Odoo] | OCR field (preset invoice or your own OCR API) writing header fields and a lines **subform**; or a workflow with an AI Agent (image model, File Link) and structured output; Mingo AI Auto Fill for one-off entry [Doc] [Doc-x] | Accuracy on Malaysian bills unproven; preset reads PDF page 1 only; lines only into a subform; vendor matching and tax mapping by rules; nothing learns from corrections; credits per bill |
| **Email-to-record**: mail aliases and incoming mail servers in `mail` (Community); `mail_plugin`, `crm_mail_plugin` [Odoo] | A public form or external portal in place of the alias (native); or an external inbound-mail service → webhook workflow → Add Record with attachment URLs → OCR/AI [Inference] | No native mailbox, threading or reply capture in the docs. Send Email's sender address is set by the platform; replies go to the Reply-To address [Doc-x] |

#### A. Automatic currency rates

**Docs say:**
- The scheduled trigger has a start time, an optional end time and a recurrence: hourly, daily, weekdays (Monday to Friday, **excluding holidays**), weekly, monthly, yearly, or custom times, days and months. **Execute Now** runs it after publishing [Doc-x workflow/trigger-by-scheduled].
- The API Basics page teaches with an exchange-rate API: `GET https://api.frankfurter.dev/v2/rates?base=USD&quotes=CNY` returns `base`, `date` and a `rates` object [Doc api/basics].
- Send API Request: GET with dynamic URL parts, **Test API**, import of a JSON response sample, 10 s timeout, continue or terminate [Doc-x].

**Design [Inference]:**
1. Sheets per `00-foundation.md`: Currencies, and Currency Rates (date, currency, rate, inverse rate, source).
2. A connection "FX rates": [API Key or No Authentication] for a keyless API, or a key header for a paid provider. If the Bank Negara Malaysia API is chosen, check its required headers and terms. One API, "Rate for currency", with inputs `base` and `quote`; output `rate` = `rates.<quote>`.
3. A PBP or sub-process "Fetch rate (currency, date)":
   - Get Single Data for an existing rate on that date. If there is none:
   - call with **base = the foreign currency and quote = MYR**, so the JSON path is always `rates.MYR`;
   - Add Record: rate = 1 ÷ value and inverse = value. Odoo stores units of currency per one unit of the company currency.
   - The "current rate" upkeep in `../workflow-nodes.md` §5.4 then runs on the new row.
4. A daily scheduled workflow on weekdays, timed after the provider publishes (ECB publishes in the afternoon CET; check), does Get Multiple Data on active non-base currencies, then runs the sub-process for each.
5. An **Update rates now** custom action on Currencies runs the same sub-process. This is Odoo's manual refresh.
6. On weekends and holidays the last rate stays in force, through the Convert amount fallback in `../workflow-nodes.md` §5.4.

**Falls short:**
- Turning a multi-currency `rates` object into rows in one call needs a Code Block (Professional). Hence one call per currency.
- The provider's terms, accuracy and choice of buying, selling or middle rate are business decisions (EMS handover §4.2).
- Nothing makes a scheduled run transactional. The per-date check is what keeps runs repeatable.

#### B. MyInvois e-invoicing

**Docs and evidence:**
- There is no Malaysian e-invoice node or service in this slice [Doc].
- Mingdao's China e-invoicing (Baiwang) is not evidence for Nocoly or Malaysia [KB 03, KB 16].
- Connections support OAuth 2.0 client credentials with token refresh, hidden credentials, JavaScript/Python code around each API, error alerts to an owner, request logs and usage references [Doc integration/api].
- EMS already has:
  - a MyInvois Documents sheet and a MyInvois Setup page;
  - a Companies "Test Connection" button;
  - the app-level flow "MyInvois: Document Synchronization";
  - Call Integrated API nodes for MyInvois and Stripe [EMS].
- This survey did not open those flows.

**Design [Inference]:**
- Read EMS's connection and flows first, for their lessons. The connection itself could be moved with export/import [Doc], if the programme allows it: EMS's sheets and workflows are not copied (`../../README.md` §1).
- Keep one API per MyInvois operation: token, submit documents, get submission, get document, cancel, validate TIN, search. Confirm the names against LHDN's SDK.
- **Submit to MyInvois** button on the invoice → workflow: build the document (code) → Call Integrated API → store the submission UID and each document's UUID.
- A scheduled workflow every N minutes polls pending submissions and stores status, long ID and validation URL. The validation URL feeds a Barcode (QR) field for the print template (cross-reference: worksheet digest).

**Falls short [Inference]:**
- Building the UBL JSON/XML, hashing, Base64 and, where the document version requires it, signing need code: the connection's code block or a Code Block. Certificates add more handling.
- Each call has a 10 s timeout. MyInvois submission is asynchronous, which suits polling.
- Credentials live per organisation, because connections can only be authorised to apps in the same org [Doc]. Every customer copy needs its own connection and keys.

#### C. Other connectors

| Odoo | Native HAP | Note |
|---|---|---|
| Payment providers (`payment_stripe` …) [Odoo] | Connection + Call Integrated API; provider events into a webhook-triggered workflow [Doc]. EMS has "Book a Stripe payment" [EMS] | Provider signatures are not verified natively [KB 04]. Re-read the event from the provider's API by its ID before trusting it [Inference] |
| Shipping carriers (`delivery_*`, Enterprise) | API Query field: tracking number → shipment status in a subform (the doc's own logistics example) [Doc-x]. Call Integrated API to create shipments; labels saved as attachments by URL [Doc-x] | Carrier templates must be checked in the library |
| Partner autocomplete, lead enrichment (`partner_autocomplete`, `crm_iap_enrich`) | API Query field in **Searchable Dropdown List** mode on a registry API (the doc example is China's Tianyancha) [Doc] [Doc-x]. Or Mingo AI Auto Fill with Smart Fill (web search, ✨ marks) [Doc] | A Malaysian registry source is needed. Smart Fill output needs human review |
| TIN or VAT validation on input | Control event **Call Integrated API** on field change, or an API Query button [Doc-x] | Record page only |
| SMS (`sms`, IAP) | SMS node; Twilio for international SMS [Doc-x] | Paid per message |
| E-commerce platforms | Webhook in, Send API Request out, scheduled polling; store the platform order ID to avoid duplicates (EMS handover §4.1) [Doc] [EMS] | 10,000 webhook requests per hour [Doc-x] |
| External API (XML-RPC/JSON-RPC with API keys) | API V3 with AppKey + Sign, PAT or OAuth 2.0; batch, pivot and workflow-trigger endpoints [Doc] | No transaction across calls. 50 QPS per IP on V2 write and list endpoints |
| Automation webhooks (`base_automation` [Odoo]) | Send API Request **Send Specified Data Object** to push a record; webhook trigger to receive [Doc-x] | Pushes can be retried up to 10 times, so the receiver must ignore duplicates |
| Calendar sync (`google_calendar`, `microsoft_calendar`) | Nothing native documented. An **OAuth 2.0 (Authorization Code Grant)** connection (per-user accounts) plus workflows could push events [Inference] | Two-way sync would be custom work |

#### D. Vendor-bill OCR

**Docs say:**
- The OCR field supports invoices, PDF page 1 only, writing to a subform with batch upload, your own OCR API through the Integration Center, and a camera-only mode on mobile [Doc-x worksheet/control-ocr].
- To pass a file to an API, the record is saved first and its attachment URL is handed over [Doc integration/parameters].
- The AI Agent node takes file fields through **File Link** (images need a vision model) and returns structured output [Doc-x].
- Mingo AI Auto Fill fills a new record from an uploaded image [Doc ai/mingo].

**Design [Inference]:**
1. Vendor Bills has an attachment field for the bill and an OCR field, either the preset invoice template or a connection to an OCR provider.
2. The OCR field maps supplier, TIN, invoice number, dates, currency, totals and tax to header fields, and the lines to a **Bill Lines subform**.
3. On create (or from a button), a workflow:
   - matches the supplier by TIN (Get Single Data on Contacts) and sets the relation;
   - checks that the line totals add up to the header;
   - sets the status "To review".
4. A person confirms with a button before anything is posted.
5. AI route instead of the OCR field: an AI Agent with File Link and structured output fills the header, then Add Record creates the lines.
6. AI Generate Data Object suits text input, such as an email body. Its page describes no file input.

**Falls short:**
- Accuracy on Malaysian supplier bills, multi-page PDFs and handwriting is unproven.
- Duplicate bills are not detected by default. HAP's "No duplicates" works only on values a user types (`00-foundation.md` row 6), so a check node is needed.
- HAP does not learn from corrections, as Odoo's extraction does.
- The cost conflict (0.15 against 0.03 credits) is open.
- Where OCR and AI processing run, and how long data is kept, is not documented [KB 05].

#### E. Email-to-record

**Docs say:**
- The cached docs show no inbound-email trigger or mailbox. The Get Started page lists Worksheet event, Scheduled, Date field, Webhook and Button triggers [Doc]. A search of all cached help.nocoly.com pages for IMAP, POP3, mailbox, inbound or incoming email and email alias found no inbound-mail feature.
- In Send Email, the sender address is managed by the platform and cannot be customised; a Reply-To address can be set [Doc-x workflow/node-send-email].

**Design [Inference]:**
1. **Native first:** replace the mail alias with a **public form** or **external portal** page, where suppliers upload bills and prospects submit enquiries [Doc getting-started].
2. **If email must stay:** an external inbound-mail service (an "inbound parse" or routing feature of a mail provider, or a Microsoft 365 flow) POSTs sender, subject, body and attachment URLs to a webhook-triggered workflow. The webhook uses **Use App Authorization** and an **App IP Whitelist**. The workflow then:
   - creates the lead or bill;
   - uploads the attachments from the URLs;
   - runs OCR or AI (§D);
   - notifies the owner.
3. Replies: set Reply-To to the same inbound address and put a reference such as `[BILL-123]` in the subject, so replies can be matched and stored as rows in an "Email messages" child sheet.
4. For single emails, a user can paste the text into Mingo AI Auto Fill to create the record [Doc ai/mingo].

**Falls short:**
- No native mailbox, threading, spam filtering or bounce handling.
- Attachment URLs must be publicly downloadable and end in a file extension [Doc-x].
- Code-block polling of IMAP is possible in principle but fragile (10 s limit, credentials in code). Not recommended.

### 3.2 Other Odoo concepts this slice can replace

| Odoo concept | Native HAP feature | Gap |
|---|---|---|
| Studio (`web_studio` absent, so Enterprise [Odoo]) | Mingo AI Application Builder and AI Worksheet Generation, AI Field Suggestions [Doc-x]; CLI and MCP for scripted builds [Doc] | Relationship targets are set by hand. Generated designs need review. Build traps in §4 |
| Demo data | AI Sample Data Generation [Doc] | Fictional; admins, operators and developers only |
| Data import and migration from an older Odoo | Excel import [Doc]; Data Integration from the old Odoo's PostgreSQL (a supported source), with ETL joins and filters [Doc] [Inference] | Multi-row relations do not sync, so relations are rebuilt afterwards. Professional plan. The database must be reachable from Nocoly SaaS |
| Spreadsheet dashboards and reporting (`spreadsheet_dashboard`) | Charts and custom pages [Doc]; Mingo data query with charts [Doc]; pivot API [Doc]; a mirror to MySQL or PostgreSQL feeding BI [Doc] | Mirroring is Professional. Direct-database BI is documented for Server only |
| Shared master data across apps or companies | Worksheet→worksheet sync (Data Integration scenario 1: maintain once, use in many apps) [Doc] | Relations and other types do not sync (§2.5); the naming trap applies |
| Onchange that calls an outside service | Control event **Call Integrated API** [Doc-x] | Record page only |
| `ir.cron` jobs that pull external data | Scheduled workflow + Call Integrated API or Send API Request [Doc-x] | 10 s per call |
| Live Chat chatbot scripts (`im_livechat`) | ChatBot app item for internal and external users, with share links [Doc] | No website chat widget is documented |
| AI drafting and summaries (Odoo's AI features; no `ai` module in Community [Odoo]) | AI Action on the record (fields, comments and logs as context), AI Generate Text node [Doc] | Billed in credits. The AI Action's own flow cannot take extra nodes |
| Knowledge (Enterprise) | Vector Knowledge Base and the Knowledge Retrieval node [Doc] | Detailed in another slice |
| Portal share link | V3 **Generate Record Share Link** (password, expiry) [Doc] | — |
| User API keys (`res.users.apikeys`) | PAT with expiry and org, app and API scopes [Doc] | The org must enable the PAT policy |
| OAuth or LDAP sign-in (`auth_oauth`, `auth_ldap`) | Org integrations: LDAP/AD (Standard+); WeCom, DingTalk, Feishu/Lark and WeLink (Professional); Microsoft Entra [Doc-x] | One third-party platform per organisation |
| Activity reminder before a deadline | Date field trigger + CC node [Doc getting-started] | — |
| Many2one with `related=` fields | Relationship + Foreign field, **Display only** or **Data storage** [Doc] | Stored copies can go stale (trap 22) |
| Website form, lead capture | Public form [Doc] | — |

## 4. Traps

1. **Wrong API host.**
   - The V3 page says HAP SaaS = `https://api.mingdao.com` [Doc]. That is Mingdao's China SaaS.
   - Nocoly's own published V3 and organization schemas use `https://www.nocoly.com/api` [KB 04], and the V2 example uses `https://www.nocoly.com/api/v2/open/…` [Doc].
   - Other Mingdao links in this slice: `apifox.mingdao.com` (endpoint list) and `apidoc2.mingdao.com` (PAT docs) [Doc].
2. **Two outbound-IP lists.**
   - The Send API Request page lists `123.59.59.220` and `106.75.14.110`.
   - The network FAQ lists five Tencent Cloud Hong Kong addresses (`43.154.235.158`, `43.154.111.184`, `43.154.63.239`, `43.154.158.53`, `43.154.202.180`), shared by webhook pushes, Send API Request and code blocks [Doc-x] [KB 04].
   - Use the FAQ list for provider allowlists, and check it live.
3. **Webhook URLs are open by default.**
   - Turn on **Use App Authorization** and **App IP Whitelist**.
   - Provider signatures (for example HMAC) and replays are not checked natively [Doc-x] [KB 04].
   - When capturing a sample request, it must arrive within 3 minutes [Doc]. The limit is 10,000 requests per hour [Doc-x].
4. **Duplicates from retries.** A push that does not get HTTP 200 within 10 s is retried up to 10 times [Doc-x]. Receivers, and our own webhook flows, need an idempotency key (external ID) [Inference]. **Continue Execution** after a timeout skips only the fields that depend on the failed node [Doc-x], so a record can be half filled.
5. **Plan gates.**
   - Code Block, PBP, Loop, API Proxy, Data Integration/ETL and mirroring are Professional. Integration Center, API Query and Call Integrated API are Standard+ [Doc-x].
   - Several documented workarounds need a Code Block: attachment URL, arrays, Base64, stripping "+86" [Doc]. A Standard-plan customer copy cannot use them.
   - The plan page contradicts itself on data sync (§2.5).
6. **API Query field timing.**
   - It cannot run at record creation when its input is an attachment URL or an array [Doc].
   - Only a Code Block can output a simple array [Doc].
   - Object arrays need a subform or a multi-record relationship. Inside a workflow, Get Multiple Data filtered on Record ID = current record turns one record into an object array [Doc].
7. **OCR shape and cost.**
   - Invoice lines must sit in a **subform**, not a relationship field, so design Bill Lines as a subform if OCR is used.
   - The preset template reads page 1 of a PDF only.
   - Price: 0.15 credits per call (field page) against 0.03 credits per file (billing page) [Doc-x] [KB 05].
8. **Data Integration and names.** Spaces and special characters in app, worksheet or field names may block selection or break a sync [Doc]. The target app **"Odoo Replica (AI)" contains spaces and parentheses**, and most field names contain spaces. Test before designing around Data Integration.
9. **Data Integration field gaps** [Doc]: multi-row relations, foreign fields ("sync only"), OCR, API Query, Query Records, signature, barcode, embed, uppercase, remark, free link, section and tab do not sync. Odoo-style relational data loses its many-side links.
10. **Deletes and sync** [Doc]: a destination row in the recycle bin is not re-synced until restored; a permanently deleted row is never re-synced.
11. **No scheduled database pulls** except from SAP HANA [Doc]. A "nightly import" from MySQL is a real-time task, or a workflow that calls an API.
12. **AppKey + Sign acts as app administrator** and ignores role permissions [Doc]. Use PAT or OAuth when the caller should be limited. **PUT clears omitted fields**; use PATCH for updates [Doc].
13. **Rate limits are per source IP** [Doc]. Integrations behind one NAT address share the 50 QPS. Expect HTTP 503 with `error_code` 90001 and build retries.
14. **Creator becomes "API" or "Workflow"** for integrated writes [Doc]. Keep explicit source and external-ID fields; Odoo's `create_uid` meaning is lost [Inference].
15. **`triggerWorkflow`.** API writes start workflows only when the flag says so. The V2 example sets `true`; the default is not documented [Doc]. In the other direction, a Data Integration task can also start workflows if that option is on [Doc], which can cause double side effects.
16. **Integration Center credentials.**
    - Hidden parameters can never be read back, so keep the master copy of secrets elsewhere.
    - A connection serves apps in its own organisation only.
    - Updating a published library API means duplicating it and disabling the old one.
    - Server customers must reinstall updated connections [Doc].
    - App export includes "Integration Center API bindings" [Doc-x application/import-export]; whether credentials travel with them is not stated.
17. **Keys in URLs.** The pull example puts the provider key in the URL [Doc]. Keep keys in hidden connection parameters instead [Inference].
18. **AI costs and control.**
    - AI Agent, Generate Text and Generate Data Object always consume credits, and plan allowances are small (15 or 28 a month) [Doc] [Doc-x].
    - Mingo has no role-based control [Doc]; only org feature permissions [Doc-x].
    - Smart Fill can search the web and guess (✨). Keep it off for accounting data [Doc].
19. **Agents outside chat.** "By user permissions" and "Require confirmation" exist only in conversation workflows [Doc]. A record-triggered AI Agent therefore acts with workflow rights and without confirmation: limit its worksheets and tools [Doc]. Tool output returns **only the first row** [Doc-x].
20. **ChatBot exposure.**
    - Turning "By user permissions" off lets the bot read all data [Doc].
    - External users can use ChatBots under the same distribution rules [Doc].
    - Shared chats are public snapshots [Doc].
    - A chat round ends at Approval, Fill in, Delay, Subprocess, PBP or Initiate Approval Flow [Doc], so long processes do not belong in chat flows.
21. **The AI Action workflow is generated and locked**: no extra nodes can be added [Doc]. Post-processing needs a separate workflow.
22. **Foreign fields:**
    - Display only cannot be filtered, sorted or used in calculations.
    - Data storage is a copy [Doc getting-started].
    - Earlier work found stored copies empty on old rows until recalibrated [Obs].
23. **Build tooling traps** [Doc] [Obs]:
    - The CLI is blocked unless the org's CLI Access Policy allows it. PAT needs the API Access Policy [Doc].
    - `hap-cli` `field.add` often reports a 30 s timeout although the field was created: re-read before retrying [Obs].
    - MCP workflow nodes save `kind: record` relation values as broken text, so test-run and read back [Obs].
    - `role set-permissions -P` reset a role's rules [Obs].
24. **Send Email** cannot change the sender address. Replies go to the Reply-To mailbox, not back to the record [Doc-x].

## 5. To verify live

Each test should be read-only or run in a scratch app, with readback in the UI.

1. **Plan of the organisation.** Code Block, PBP, Loop, Data Integration, mirroring and API Proxy depend on Professional. EMS uses code blocks and a PBP, which suggests the org has them, but the plan is unconfirmed.
2. **Public API Library on Nocoly.** Search the library for exchange rate, currency, OCR, invoice, MyInvois, email, SMS and logistics. Note what exists for Malaysia.
3. **FX rate call.** Use **Test API** in a Send API Request node with Frankfurter `base=USD&quotes=MYR`, and with the Bank Negara Malaysia API if that source is chosen. Check the response shape, the date, MYR availability and the JSON Parsing path.
4. **Outbound IPs.** Call an IP-echo service from Send API Request and from a Code Block. Compare the result with both documented lists.
5. **V3 host.** Make a read-only GET (`/v3/app`) with an app key on `https://www.nocoly.com/api` against `https://api.mingdao.com`.
6. **`triggerWorkflow`.** Find its default on V3 create and update. Check whether records created by a webhook flow start worksheet-event workflows.
7. **Webhook security.** Confirm that **Use App Authorization** rejects unsigned calls and that the IP whitelist works. Check that a custom response is returned. Show that a repeated POST creates a duplicate unless the flow checks first.
8. **OCR field on real Malaysian bills** (PDF and photo):
   - which preset templates appear;
   - which fields are extracted;
   - whether lines land in the subform;
   - how a multi-page PDF behaves;
   - what is actually charged (0.15 or 0.03).
9. **AI extraction.** Check whether AI Agent structured output can return an object array of bill lines that Get Multiple Data → Add Record turns into rows. Also measure the vision-model accuracy on scans, the credits per bill and File Link on PDFs.
10. **Data Integration on the target app.**
    - Does a name with spaces or parentheses block selection?
    - Does worksheet→worksheet sync across apps work, and how fast?
    - Which field types survive?
    - Does the workflow-trigger option work?
    - Is the feature available on this plan?
11. **Email.** Confirm that the trigger list in the workflow editor has no email trigger. Then test one inbound-mail-to-webhook service end to end, including an attachment URL uploaded to a file field.
12. **Send Email.** Check the sender address shown and that replies reach the Reply-To mailbox.
13. **MyInvois through a connection** (read EMS's existing connection first):
    - the token request (POST, form-encoded body, scope);
    - the token lifetime setting against the provider's expiry;
    - what the connection's code block can do (SHA-256, Base64, signing; language versions);
    - the 10 s timeout against sandbox latency.
14. **AI Action and ChatBot.** Do their runs count as workflow executions? What do they cost per run? Does per-role availability work? Does "By user permissions" limit a restricted role? Can a portal user reach a ChatBot?
15. **API Query field.** Test the real-time search cost and its behaviour on a new, unsaved record.
16. **Connection export and import into another organisation.** Check what carries over, especially hidden parameters and app authorisations.
17. **Mingo AI Auto Fill** on a vendor-bill image with Smart Fill off: check accuracy and which fields get ✨.

## 6. Coverage

All 22 pages of the slice were read in full.

| # | URL | Title | One-line summary |
|---|---|---|---|
| 1 | https://help.nocoly.com/ai | AI Capabilities in HAP | Catalogue of AI features (Mingo, ChatBot, knowledge base, AI fields, actions and nodes, translation, MCP, VS Code, Dify) and the AI billing rules |
| 2 | https://help.nocoly.com/ai/ai-action | AI Action | Record-page AI assistant: setup path, enable conditions, agent settings, context, safety switches, locked auto-generated workflow, history, role access |
| 3 | https://help.nocoly.com/ai/best-practices-for-agent | Agent Best Practices | A ChatBot CRM lead assistant and a complaint-triage workflow; model choice by image need and complexity; prompt, tool and permission advice; cost tips |
| 4 | https://help.nocoly.com/ai/chatbot | ChatBot | ChatBot app item: permissions, creation, settings and upload limits, chat-triggered workflow, round-ending nodes, agent options, logs, sharing, FAQ |
| 5 | https://help.nocoly.com/ai/cli | CLI Usage Guide | hap-cli install, org CLI policy, login, profiles and environments, JSON and REPL modes, full command reference |
| 6 | https://help.nocoly.com/ai/connect-ai | Connect AI | Portal that installs MCP, CLI and Skills; Personal versus Application access; Personal Access Tokens and app authorization keys |
| 7 | https://help.nocoly.com/ai/mcp | MCP Server | MCP concepts, APIfox MCP (read docs) versus HAP MCP (act on data), where to get the endpoint, configs for Cursor, Dify and Cline |
| 8 | https://help.nocoly.com/ai/mingo | Mingo, Your AI Assistant | Built-in assistant: app builder, worksheet generation, sample data, AI Auto Fill, name and icon optimisation, data query with charts, help; billing and upload limits |
| 9 | https://help.nocoly.com/api/basics | API Basics | Primer on API requests through Send API Request, using an exchange-rate GET, a Bearer-token GET and a V2 addRow POST |
| 10 | https://help.nocoly.com/api/bi-integration | Integrating with BI Systems | SaaS BI through the open API (SmartBI, YouData, DataV); Server BI straight from the database (Power BI, Tableau and others) |
| 11 | https://help.nocoly.com/api/external-data-webhook | How to Write External Data into a Worksheet via Webhook | Webhook-triggered workflow with sample-request parameters and Add Record; created records show creator "Workflow" |
| 12 | https://help.nocoly.com/api/get-external-data | How to Retrieve External Data into a Worksheet | Worksheet-event workflow calls a third-party GET API (a code block strips +86) and writes the result back |
| 13 | https://help.nocoly.com/api/introduction | API Overview | Organization versus application APIs, authorization keys, V2 versus V3, field and view tables, sharing, Filter Generator, rate limits, error codes, 36-endpoint V3 list |
| 14 | https://help.nocoly.com/api/v3 | API V3 Specification | REST conventions, hosts, three auth methods, naming rules, system fields V2→V3, full endpoint reference, general and OAuth error codes |
| 15 | https://help.nocoly.com/api/write-data-to-worksheet | How to Read/Write Worksheet Data via API | V2 addRow example with aliases, the field table, `triggerWorkflow`, testing with an API client, finding row and view IDs |
| 16 | https://help.nocoly.com/getting-started | Get Started with HAP | Builds a recruitment app: worksheets, public form, relations and foreign fields, views, roles, date and event workflows, charts, custom pages, integration overview |
| 17 | https://help.nocoly.com/integration/api | API Integration | Integration Center connections and API Library: auth methods, API definition (inputs, code, request, outputs), app authorisation, alerts, export/import, logs, publishing |
| 18 | https://help.nocoly.com/integration/data-integration | Data Integration | Database↔worksheet connectors and sync tasks: supported databases, modes, ETL, workflow triggering, delete rules, unsupported fields, system fields, examples, statistics |
| 19 | https://help.nocoly.com/integration/datamirror | Worksheet Data Mirroring | Continuous copy of a worksheet into MySQL or PostgreSQL for analysis |
| 20 | https://help.nocoly.com/integration/etl | Introduction to ETL Functionality | ETL nodes: source, destination, filter, join (inner, left, right), group summary, merge (six set operations), with limits and examples |
| 21 | https://help.nocoly.com/integration/parameters | 4 Parameter Passing Examples | Passing file URLs, simple arrays, object arrays and Base64 images to integrated APIs through API Query fields or workflows |
| 22 | https://help.nocoly.com/integration/timed-synchronization | Scheduled Sync | SAP HANA-only scheduled sync: hourly or daily, full overwrite or incremental by key, time or number |

**Read for cross-reference only, not counted above** [Doc-x]:
- **Read in full:**
  - `worksheet/control-ocr`, `worksheet/control-api-query`, `worksheet/ai-suggestion`, `worksheet/workflow-api-upload-file`
  - `workflow/node-send-api-request`, `workflow/trigger-by-webhook`, `workflow/trigger-by-scheduled`, `workflow/node-call-integrated-api`, `workflow/node-api-connectivity-authentication`, `workflow/node-ai-generates-data-objects`, `workflow/node-ai-agent`, `workflow/workflow-execution-limits`
  - `org/integration`, `purchase/billing-items`, `purchase/version-comparison`, `faq/ip`
- **Excerpts only:** `workflow/node-send-email`, `worksheet/event`, `application/import-export`, `org/security`, `org/administrators`, `workflow/node-interface-push`.
