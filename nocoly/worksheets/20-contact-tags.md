# 20 · Contact Tags — requirements

| | |
|---|---|
| Odoo model | `res.partner.category` — `odoo/addons/base/models/res_partner.py` |
| Odoo menu | Contacts › Configuration › **Contact Tags** (`base.action_partner_category_form`) — administrators (`base.group_system`) |
| Bundle | **Contact Tags**, `btag`, 1 worksheet, 1.1 h — ground-up build page |
| Source | the 19.0 source only. casimir.odoo.com expired on 22 Sep 2026, and no extract of this model was taken |
| Status | **Requirements.** Nothing built |
| Date | 22 Sep 2026 |

---

## 1 · What it is

Free labels for contacts — "VIP", "Supplier / Local" — that can nest under a parent tag. **Not the same as CRM
Tags** (`crm.tag`), which Teh Li Wei built for Leads; the app's own remark on that worksheet reads "Do not
substitute Contact Tags". Two models, two worksheets.

**It starts empty.** Odoo ships no standard tags, and the tenant's own are no longer readable.

## 2 · Fields

| # | Field | Odoo | Type | Required | Default | Notes |
|---|---|---|---|---|---|---|
| 1 | **Complete Name** | `display_name` | Formula text, **title** | — | — | `Parent / Child`, the **whole** ancestor chain (Odoo walks `parent_id` to the top). What pickers show. Read-only, off the create form (`100`). **08 Product Categories' Complete Name is the exact pattern** |
| 2 | Name | `name` | Text | **yes** | — | placeholder `e.g. "Consulting Services"` |
| 3 | **Category** | `parent_id` | Relation → Contact Tags, single, **self** | — | — | Odoo's own label for the parent is *Category*, on the field and in the list. Picker excludes the record itself (`domain="[('id', '!=', id)]"`) |
| 4 | Child Tags | `child_ids` | the reverse of 3 | — | — | comes free: a single self-relation is two-way in HAP, as on 08 |
| 5 | Color | `color` | Dropdown, 12 colours | — | — | Odoo stores an integer 0–11 and picks **1–11 at random** on create. HAP has no random default, so it defaults to **no colour** — a recorded difference. Options coloured to match Odoo's palette |
| 6 | Active | `active` | Checkbox, **visible and editable** | — | ticked | see §3 |

**Recursion.** Odoo refuses a loop with *"You can not create recursive tags."* The picker's filter stops the
direct case (a tag as its own parent). A longer loop (A under B under A) is not caught — **08 records the same
limit for Product Categories**; follow whatever it settled on.

## 3 · Form, views, buttons

**Form** — Name, Color, Category, Active, in Odoo's two-column group.

**Active is on the form as a toggle** in Odoo (`widget="boolean_toggle"`), unlike most models where it is hidden
behind Archive / Unarchive. So build **no Archive/Unarchive buttons**: the toggle *is* the archive action here,
which is the same call as Locked and Invoicing Closed on Orders — a visible switch beats a button pair that only
flips it. Keep an **Archived** view.

**List** — Name, Category, Color; editable in place, multi-edit. Sorted by **Name** (`_order = 'name, id'`).

**Views** — **All** (Active only, sorted by Name) and **Archived**. Odoo's search also groups by Category and by
Color; group-by is a view setting, so offer a **By Category** grouping if cheap.

## 4 · Where it is used — wiring, a separate later step

| Worksheet | Field | Odoo | Notes |
|---|---|---|---|
| **Contacts** | **Tags** — Relation → Contact Tags, **multiple, one-way** | `res.partner.category_id` | on the form as tags; in Odoo's list it is an optional column, hidden by default. **One-way**: Odoo's reverse, `partner_ids`, is on no view, so it needs no control here |

A pinned save on Contacts, a Phase 1 core worksheet with a lot of hand-set layout. Its own step.

## 5 · Not built now

| What | Why |
|---|---|
| Searching contacts by a tag **and its children** | Odoo searches Tags with `child_of`; a HAP filter matches the tag itself only |
| Tag colours on contact chips | Odoo colours the chips from `color`. HAP does not colour a relation chip from a field of the target, so Color only shows on this worksheet |
| A random default colour | no random default in HAP |
| Seed data | none shipped; tenant unreadable |
