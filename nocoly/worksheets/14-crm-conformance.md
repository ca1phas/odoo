# 14 · CRM — conformance against Odoo

| | |
|---|---|
| Nocoly app | ERP Master · menu group **CRM** |
| Worksheets | Stages · Lost Reasons · Recurring Plans · Leads · Sales Teams · Campaigns · Mediums · Sources · CRM Tags |
| Odoo models | `crm.stage` · `crm.lost.reason` · `crm.recurring.plan` · `crm.lead` · `crm.team` · `utm.campaign` · `utm.medium` · `utm.source` · `crm.tag` |
| Built by | **Teh Li Wei**, 18–21 Sep 2026, by hand — no `§1`, no builder script, no entry in `build/ids.json` |
| Reference | **casimir.odoo.com — Odoo saas~19.4+e**, extracted read-only on 21 Sep 2026 to `nocoly/reference/odoo-19.4/crm.*.md` and `utm.*.md` |
| Phase | 2 — CRM, plus three bundles pulled forward (Marketing attribution · Sales Teams · CRM Tags) |
| Status | **Conformance pass, 21 Sep 2026** — not a hand-off. 9 worksheets read against Odoo; **21 divergences**, of which **6 matter** |

This is not the usual worksheet document. Teh built these nine by hand rather than through the loop, so there is
no §1 to test against and no builder to re-run. What follows instead is the check the loop would have produced:
every field, view and record read back and compared with Odoo, on the owner's ruling of 21 September that
**Odoo is the only reference** (`DECISIONS.md`).

**The shape is good.** The menu mirrors Odoo's own — CRM holding Stages, Lost Reasons, Recurring Plans and
Leads, with a *Configuration* sub-group for Sales Teams, Campaigns, Mediums, Sources and CRM Tags. Aliases are
Odoo's field names throughout. Leads has three views named after Odoo's own actions (*My Pipeline*,
*All Opportunities*, *Lost*), a **+ New Opportunity** button, Priority as stars and Salesperson as a
Collaborator — the house rule for `res.users`. Most of what follows is detail, not rework.

## 1 · What matters

| # | Worksheet | Finding | Why it matters |
|---|---|---|---|
| 1 | **Leads** | **No `type`.** Odoo's `crm.lead` is *two things in one table* — `type` is a **required** selection, `lead` or `opportunity`, drawn as a badge in the form header, and almost every view is doubled (`crm.lead.list.lead` / `…list.opportunity`, two searches). The worksheet models the opportunity only | A lead that has not been qualified yet has nowhere to live. This is the one structural gap, and it is cheaper to close now than after records exist |
| 2 | **Leads** | **`Status` is invented.** A Single Select *Open · Won · Lost* with alias `pipeline_status` — **no such field exists on `crm.lead`**. Odoo derives `won_status` from the stage's `is_won` and from `lost_reason_id`; it is computed, not typed | Two sources of truth for the same fact. A record can be Stage *Won* and Status *Lost* at once, and nothing stops it |
| 3 | **Leads** | **No Recurring Plan relation**, so **Recurring Plans is an orphan** — nothing in the app points at it. Odoo has `recurring_plan`, `recurring_revenue` and `recurring_revenue_monthly` on the lead, all three behind `crm.group_use_recurring_revenues` | A worksheet nothing references. Either wire it up or say in a *Not built now* that the recurring-revenue feature is off |
| 4 | **Campaigns** | **Two required Odoo fields are missing**: `stage_id` → `utm.stage` (**required**, a clickable status bar in the header, and what the kanban groups by) and `tag_ids` → `utm.tag`. Both target models are unbuilt | A campaign in Odoo cannot be saved without a stage. Ours can — so the worksheet cannot round-trip |
| 5 | **Stages** | **Sales Teams is parked at row 9999.** The control is correct — a multiple Relation to Sales Teams, alias `team_ids`, matching Odoo's many2many — but `add-fields` leaves a new control at row 9999 and only a full layout save moves it (`BUILDING.md`) | It renders at the very foot of the form, below everything, rather than in Odoo's first group |
| 6 | **All nine** | **No roles position.** `roles.py check` reports each of the nine as *"not in the owner's table — HAP put it there at `{'delete': 20, 'edit': 20, 'read': 20}` add=True"* — HAP's own default, scoped to **own records only**, with create and delete on, decided by nobody | Our fourteen each have a row mapped onto an Odoo group. These nine have a default that nobody chose, and it is *more* permissive on delete than any of our four business roles except the administrator |

## 2 · Data that diverges from the tenant

Teh seeded from the **ohyes** app, not from Odoo — Sales Teams still carries `info@ohyes.odoo.com`. Now that
Odoo is the reference, these are the gaps.

| Worksheet | Odoo has | ERP Master has | |
|---|---|---|---|
| Stages | 4: New 1 · Qualified 2 · Proposition 3 · Won 70 | the same four, same sequences | **match** |
| Stages | `fold` **false on all four** | **Proposition is folded** | differs |
| Lost Reasons | 3: Too expensive · We don't have people/skills · Not enough stock | 3 | **match** (names to confirm) |
| Recurring Plans | 4: Monthly 1 · Yearly 12 · Over 3 years 36 · Over 5 years 60 | **0** | **empty** |
| Sales Teams | 7, two archived: Sales · Enterprise · SMB · Channel Partners · Online · *Website* · *Point of Sale* | **2** — `Test`, `Sales` | 5 missing, 1 invented |
| Campaigns | 0 | 0 | **match** |
| Mediums | 5: Direct · Email · Phone · Social Media · Website | the same 5 | **match** |
| Sources | **14**: Google · Mass Mailing · Newsletter · Monster · Glassdoor · Craigslist · Survey · Referral · Livechat · Facebook · X · LinkedIn · Instagram · YouTube | **8** | 6 missing |
| CRM Tags | 0 | 1 — `testtest` | a test record, and **not named `TEST …`** |

## 3 · Field-level divergences

| Worksheet | Divergence | Odoo |
|---|---|---|
| **All nine** | **Every title field carries *No duplicates*** | **Only `crm.tag` has a unique constraint** (`unique (name)`, *"Tag name already exists!"*). `crm.stage`, `crm.lost.reason`, `crm.recurring.plan`, `crm.team`, `utm.campaign`, `utm.medium` and `utm.source` have **none** — Odoo allows two stages called *Qualified* |
| **Leads** | Missing `partner_name` (Company Name), `contact_name`, the address block (`street`, `street2`, `city`, `state_id`, `zip`, `country_id`), `function` (Job Position), `website`, `lang_id` | All on Odoo's *Extra Info* page, in two groups — *Company Information* and *Contact Information* |
| **Leads** | `Stage` is **required** | Odoo's `stage_id` is **not** required; it is computed on create and hidden entirely when `type == 'lead'` |
| **Leads** | Tags → **CRM Tags** | **Correct, and a correction to our own plan** — `crm.lead.tag_ids` is a many2many to `crm.tag`, not to `res.partner.category`. The ground-up plan wired Leads to Contact Tags and was wrong |
| **Sales Teams** | `Email Alias` is an **Email** control with alias `alias_id` | `alias_id` is a **many2one to `mail.alias`**, required; `alias_name` is the char. Storing the address in a field aliased to the relation will not round-trip |
| **Sales Teams** | `Members` is a **Collaborator** field | Correct for `member_ids` (many2users) — but Odoo also has `crm_team_member_ids` → `crm.team.member` for the multi-membership path, which is *Not built* and should be said so |
| **Sales Teams** | `Invoicing Target` present | Correct, but it comes from `sale`, not `sales_team` — worth a note, since the Sales app is Phase 3 |
| **Campaigns** | `Campaign Identifier` (`name`) is **visible and optional** | In Odoo it is **required** and `invisible="1"` on the form, generated from the title; the list hides the column too |
| **CRM Tags** | `Color` is a Single Select of named colours | Odoo's `color` is an **integer** with `widget="color_picker"`, defaulting to a **random** 1–11, and **required on the form**. The Single Select is a fair HAP rendering; the random default and the required flag are missing |
| **Sources** | Has no Active | **Correct** — `utm.source` genuinely has no `active` field, so no Archived view and no Archive button. Well spotted |
| **Lost Reasons** | Title field labelled *Description* | **Correct** — Odoo labels `crm.lost.reason.name` *Description* |

## 4 · Views and buttons

| Worksheet | Odoo | ERP Master |
|---|---|---|
| Leads | kanban grouped by stage (the pipeline), two lists, two searches, a quick-create | **My Pipeline · All Opportunities · Lost** — three tables, quick filters Salesperson and Sales Team, a **+ New Opportunity** button. No kanban, so **no pipeline board** |
| Stages | list with sequence handle, *Stage Name read-only*, Is Won, Sales Teams, Days to rot (optional) | *All Stages* with all six columns. Stage Name is **not** read-only |
| Lost Reasons | list `editable="bottom"`, one column; search with Active / Archived filters | *All Lost Reasons*. **No Archived view** though the worksheet has Active |
| Recurring Plans | list `editable="bottom"`, **no form view at all** | *All Recurring Plans* |
| Sales Teams | the default action opens **kanban** (the dashboard), not a list | *All Sales Teams* |
| Campaigns | **kanban grouped by stage** is the default view | *All Campaigns* |
| Mediums · Sources · CRM Tags | lists `editable="bottom"`, `sample="1"` | one *All …* view each |
| **All nine** | — | **No Archive / Unarchive buttons anywhere**, though six of the nine carry an Active field. Every worksheet of ours with `active` has the pair |

## 5 · What is right

Worth saying plainly, because most of this build is sound:

- **The menu is Odoo's**, including the *Configuration* sub-group and its five members.
- **Every alias is Odoo's field name** — `name`, `is_won`, `rotting_threshold_days`, `team_ids`, `date_deadline`,
  `expected_revenue`, `partner_id`, `tag_ids`, `campaign_id`, `medium_id`, `source_id`, `lost_reason_id`.
- **`crm.tag`, not `res.partner.category`** — and his remark says so: *"Dedicated CRM tags. Do not substitute
  Contact Tags."* He is right and the ground-up plan was wrong.
- **`team_ids` is a *multiple* Relation**, matching Odoo's many2many; there is no singular `team_id` on a stage.
- **Stages' four records and their sequences are Odoo's exactly**, 70 included.
- **Mediums' five records are Odoo's exactly.**
- **Sources has no Active**, which is right and easy to get wrong.
- Priority renders as **stars**, Salesperson as a **Collaborator**, Phone with a dial-code widget.

## 6 · What this needs next

Nothing here is a rebuild. In the order I would take them:

1. **Leads gains `type`** (Lead · Opportunity) and the *Extra Info* fields — the address block, Company Name,
   Contact Name, Job Position, Website.
2. **`Status` goes**, and Won/Lost is read from the stage and the lost reason as Odoo reads it. Needs the
   owner's approval, since it means deleting a control.
3. **Campaigns gets a Stage**, which means a `utm.stage` worksheet — or an explicit *Not built now* saying the
   campaign pipeline is out of scope.
4. **Recurring Plans is wired to Leads** and seeded with Odoo's four, or declared off.
5. **The seed data is re-taken from Odoo** — Sources' 14, Sales Teams' 7, Recurring Plans' 4, and Proposition
   unfolded.
6. **Roles**: the nine get a row in the owner's table like every other worksheet.
7. **Archive / Unarchive** on the six worksheets with an Active field, and an *Archived* view beside each.
8. **Stages' Sales Teams is moved off row 9999**, and the *No duplicates* switches come off the eight titles
   Odoo does not constrain.

**Open for the owner.** Items 2 and 8 remove things, which needs approval. And the CRM Tags record `testtest`
should be renamed `TEST …` or removed under the same rule.
