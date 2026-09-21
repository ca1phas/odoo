# 14 · CRM — conformance against Odoo

| | |
|---|---|
| Nocoly app | ERP Master · menu group **CRM** |
| Worksheets | Stages · Lost Reasons · Recurring Plans · Leads · Sales Teams · Campaigns · Mediums · Sources · CRM Tags |
| Odoo models | `crm.stage` · `crm.lost.reason` · `crm.recurring.plan` · `crm.lead` · `crm.team` · `utm.campaign` · `utm.medium` · `utm.source` · `crm.tag` |
| Built by | **Teh Li Wei**, 18–21 Sep 2026, by hand — no `§1`, no builder script, no entry in `build/ids.json` |
| Reference | **casimir.odoo.com — Odoo saas~19.4+e**, extracted read-only on 21 Sep 2026 to `nocoly/reference/odoo-19.4/crm.*.md` and `utm.*.md` |
| Phase | 2 — CRM, plus three bundles pulled forward (Marketing attribution · Sales Teams · CRM Tags) |
| Status | **Conformance pass, 21 Sep 2026** — not a hand-off. 9 worksheets read against Odoo, then **re-checked against Odoo's own screens the same day**; **19 divergences**, of which **5 matter**. Two of the first six findings were withdrawn on the screen check — see §0 |

This is not the usual worksheet document. Teh built these nine by hand rather than through the loop, so there is
no §1 to test against and no builder to re-run. What follows instead is the check the loop would have produced:
every field, view and record read back and compared with Odoo, on the owner's ruling of 21 September that
**Odoo is the only reference** (`DECISIONS.md`).

**The shape is good.** The menu mirrors Odoo's own — CRM holding Stages, Lost Reasons, Recurring Plans and
Leads, with a *Configuration* sub-group for Sales Teams, Campaigns, Mediums, Sources and CRM Tags. Aliases are
Odoo's field names throughout. Leads has three views named after Odoo's own actions (*My Pipeline*,
*All Opportunities*, *Lost*), a **+ New Opportunity** button, Priority as stars and Salesperson as a
Collaborator — the house rule for `res.users`. Most of what follows is detail, not rework.

## 0 · What the screen check changed

The first pass compared the worksheets with the **model and the stored view arch**, read over RPC. That is not
the same as comparing them with **what Odoo draws**, and for two findings it gave the wrong answer. Both the
model and the arch describe `crm.lead` as a two-type table with recurring-revenue fields; the tenant's own
screens show neither, because two feature groups are off:

| Group | On this tenant | What it hides |
|---|---|---|
| `crm.group_use_lead` | **false** | The whole lead half. The menu bar reads *CRM · Sales · Reporting · Configuration* with **no Leads entry**; `type` is forced to `opportunity`; none of the `…lead` views renders |
| `crm.group_use_recurring_revenues` | **false** | `recurring_revenue`, `recurring_revenue_monthly` and `recurring_plan` on the opportunity, **and the entire Recurring Plans menu** |

The rendered **CRM ▸ Configuration** menu is: Settings · Sales Teams · Teams Members · *Activities* (Activity
Types, Activity Plans) · *Pipeline* (Stages, Tags, Lost Reasons) · *Lead Generation* (Lead Mining Requests).

**Withdrawn:** "Leads has no `type`" — with the group off, an opportunity-only worksheet is faithful to this
tenant. It is a note for the day the group is turned on, not a defect. **Withdrawn:** "Leads has no Recurring
Plan relation" — Odoo hides that field here too. What remains of that finding is sharper and sits below.

**Added, and it is the biggest one:** Odoo's CRM app opens on a **kanban board grouped by stage** — the
pipeline, a column per stage with a quick-create on each. That is the primary CRM screen, and the worksheet
has three tables and no board.

**Also corrected, from the tenant's `ir.model.constraint` rather than the 19.0 checkout:** four of the nine
models carry a unique constraint, not one.

## 1 · What matters

| # | Worksheet | Finding | Why it matters |
|---|---|---|---|
| 1 | **Leads** | **No pipeline board.** Odoo's CRM app *opens* on a kanban grouped by `stage_id` — New · Qualified · Proposition · Won, a quick-create on each column, folded stages behind a `»`. The worksheet has three tables (*My Pipeline*, *All Opportunities*, *Lost*) and no board | This is the screen a salesperson lives in. Everything else in CRM is secondary to it |
| 2 | **Leads** | **`Status` is invented.** A Single Select *Open · Won · Lost* with alias `pipeline_status` — **no such field exists on `crm.lead`**. Odoo derives `won_status` from the stage's `is_won` and from `lost_reason_id`; it is computed, not typed | Two sources of truth for the same fact. A record can be Stage *Won* and Status *Lost* at once, and nothing stops it |
| 3 | **Recurring Plans** | **The worksheet should not exist yet.** `crm.group_use_recurring_revenues` is off on the tenant, so Odoo shows neither the menu nor the three fields it feeds. Ours is built, empty, and **nothing points at it** — Leads has no Recurring Plan relation, which is itself faithful | A worksheet for a feature that is switched off, with no records and no referrer. Either turn the feature on in Odoo and build it properly — relation, four seeded plans — or drop it to a *Not built now* |
| 4 | **Campaigns · Mediums · Sources** | **These are not CRM screens in Odoo at all** — they live under **Link Tracker ▸ UTMs**, and the CRM ▸ Configuration menu does not carry them. On top of that Campaigns is missing two required fields: `stage_id` → `utm.stage` (a clickable status bar, and what its kanban groups by) and `tag_ids` → `utm.tag`, both targeting unbuilt models | A campaign in Odoo cannot be saved without a stage; ours can. And three worksheets sit in a menu group Odoo does not put them in |
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
| **All nine** | **Every title field carries *No duplicates*** | **Four of the nine are right and five are wrong**, read from the tenant's own `ir.model.constraint` (not the 19.0 checkout, which is where my first answer came from). **Correct:** `crm.tag` `unique (name)` *"Tag name already exists!"*, `utm.medium` and `utm.source` `UNIQUE(name)` *"The name must be unique"*. **Wrong:** `crm.stage`, `crm.lost.reason`, `crm.recurring.plan`, `crm.team` and `crm.lead` carry **no unique constraint at all** — Odoo allows two stages called *Qualified* |
| **Campaigns** | *No duplicates* is on **Campaign Name** (`title`) | **Backwards.** `utm_campaign_unique_name` is `UNIQUE(name)` — on the **Campaign Identifier**, which the worksheet leaves unconstrained *and* optional while Odoo requires it |
| **Recurring Plans** | no check on # Months | Odoo carries `crm_recurring_plan_check_number_of_months = CHECK(number_of_months >= 0)` |
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
| Leads | **the kanban board is the app's opening screen** — a column per stage with a quick-create, folded stages behind a `»`; the lists are secondary | **My Pipeline · All Opportunities · Lost** — three tables, quick filters Salesperson and Sales Team, a **+ New Opportunity** button. **No board** — finding 1 |
| Stages | list with sequence handle, *Stage Name read-only*, Is Won, Sales Teams, Days to rot (optional) | *All Stages* with all six columns. Stage Name is **not** read-only |
| Lost Reasons | list `editable="bottom"`, one column; search with Active / Archived filters | *All Lost Reasons*. **No Archived view** though the worksheet has Active |
| **Menu placement** | CRM ▸ Configuration ▸ **Pipeline** ▸ Stages · Tags · Lost Reasons; Sales Teams and Teams Members flat above it; **Campaigns, Mediums and Sources under Link Tracker ▸ UTMs** | CRM ▸ Configuration holds all five flat, UTM's three included. The *Pipeline* grouping is missing and the UTM three are in a menu Odoo does not put them in |
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

1. **Leads gains a board** — a kanban grouped by Stage, which is the screen Odoo opens on.
2. **`Status` goes**, and Won/Lost is read from the stage and the lost reason as Odoo reads it. Needs the
   owner's approval, since it means deleting a control.
3. **Leads gains the *Extra Info* fields** — the address block, Company Name, Contact Name, Job Position,
   Website. (`type` is **not** needed while `crm.group_use_lead` is off; note it and move on.)
4. **Recurring Plans is decided** — turn the Odoo feature on and build it properly, or drop the worksheet to a
   *Not built now*. As it stands it is a screen Odoo does not show, with no records and no referrer.
5. **Campaigns gets a Stage**, which means a `utm.stage` worksheet — or an explicit *Not built now*. And the
   three UTM worksheets move out of CRM, or the deviation is recorded.
6. **The seed data is re-taken from Odoo** — Sources' 14, Sales Teams' 7, Recurring Plans' 4, and Proposition
   unfolded.
7. **Roles**: the nine get a row in the owner's table like every other worksheet.
8. **Archive / Unarchive** on the six worksheets with an Active field, and an *Archived* view beside each.
9. **Stages' Sales Teams is moved off row 9999**; the *No duplicates* switches come off the **five** titles
   Odoo does not constrain, and Campaigns' moves from the name to the identifier.

**Open for the owner.** Items 2, 4 and 9 remove things, which needs approval. And the CRM Tags record `testtest`
should be renamed `TEST …` or removed under the same rule.

## 7 · Later Activity implementation

This document is the 21 September conformance snapshot of the original nine CRM worksheets. Later the same day,
Teh Li Wei added the CRM Activity slice: My Activities, Activity Types, Activity Plans and Activity Plan Steps,
plus creation, reassignment and due-date notification workflows. Its current implementation, tests and explicit
gaps are tracked separately in [`18-crm-activities.md`](18-crm-activities.md); do not use the earlier statement
that Activity Types and Activity Plans were absent as the current ERP Master state.
