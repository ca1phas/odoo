# 20 · Contact Tags — requirements

| | |
|---|---|
| Odoo model | `res.partner.category` — `odoo/addons/base/models/res_partner.py` |
| Odoo menu | Contacts › Configuration › **Contact Tags** (`base.action_partner_category_form`) — administrators (`base.group_system`) |
| Bundle | **Contact Tags**, `btag`, 1 worksheet, 1.1 h — ground-up build page |
| Source | the 19.0 source only. casimir.odoo.com expired on 22 Sep 2026, and no extract of this model was taken |
| Status | **Built and self-checked 22 Sep 2026** (`build/contacttags.py`), not yet UI-tested. Wiring (§4) not started |
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

---

## 6 · Built — 22 Sep 2026

`nocoly/build/contacttags.py`, steps `create → fields → views → roles`, then `check` and `selfcheck`. Every step reads
live state first; a second `all` run saved nothing. Every full control save was pinned to the version it read.
Worksheet `6ab29232e54d2a34faaa98bb`, alias `res_partner_category`, icon `sys_8_2_bookmark_ribbon`. **No seed**: the
worksheet holds only selfcheck's three TEST tags, archived.

**Sidebar.** Menu group **Contacts**: Contacts · **Contact Tags** · Countries · States — Odoo's Contacts ›
Configuration opens with Contact Tags (sequence 1), before Localization's Countries and States (5). Flat in the
group, as Countries and States are.

### Controls

| Control | Type | Alias | Permission | Notes |
|---|---|---|---|---|
| Name | Text, required | `name` | `111` | (0, 0, 6). Placeholder `e.g. "Consulting Services"` (Odoo's) |
| Color | Dropdown, 12 options, **coloured** | `color` | `111` | (0, 1, 6). Default **No color** (form only). Options in Odoo's order and colours (below); `enumDefault2` 1 switches the colours on, as on the owner's Orders Status |
| Category | Relation → Contact Tags, single, **two-way** (self), dropdown | `parent_id` | `111` | (1, 0, 6). Picker filter: **Active is ticked** and **Complete Name is not this record's** (09's Parent Account pattern) — browser-only, like every picker filter |
| Active | Checkbox as a **switch** (`showtype` "1", the owner's style for Locked) | `active` | `111` visible | (1, 1, 6). Default on (form only). No Archive / Unarchive buttons (§3) |
| Complete Name | Function formula (53), text, **title** | `display_name` | `100` | (2, 0, 6). `IF(ISBLANK(Parent Complete Name),TRIM(Name),CONCAT(Parent Complete Name," / ",TRIM(Name)))` — 08's expression |
| Child Tags | the reverse of Category, multiple | `child_ids` | `100` | (3, 0, 12), a list at the foot of the record, columns Name · Color. Made by the server in the first save as "Child" and renamed |
| Parent Complete Name | Lookup through Category of Complete Name, **stored** (`strDefault` "00") | `parent_complete_name` | `011` hidden | (4, 0, 6). Not an Odoo field — what Complete Name is built on, as on 08 |

Colours — Odoo's `ColorList` names and `$o-colors` swatches, index 0–11: No color `#a2a2a2` · Red `#ee2d2d` · Orange
`#dc8534` · Yellow `#e8bb1d` · Cyan `#5794dd` · Purple `#9f628f` · Almond `#db8865` · Teal `#41a9a2` · Blue
`#304be0` · Raspberry `#ee2f8a` · Green `#61c36e` · Violet `#9872e6`. The keys are fixed in `contacttags.py`.

### Views

All three: columns **Name · Category · Color**, sorted **Name ↑ then Created ↑** (Odoo `_order = 'name, id'`).

| View | Filter | Grouping |
|---|---|---|
| **All** (opens first) `6ab29232e54d2a34faaa98bf` | Active is on | — |
| **By Category** `6ab2929c805aef7032e3286b` | Active is on | **grouped by Category** — `advancedSetting.groupsetting` `[{"controlId": <Category>, "filterType": 11}]`, `groupshow` "0", the shape the table-view editor stores (captured from the UI on the Sales app, 13 Sep 2026). Not seen in a browser here |
| **Archived** `6ab2929dbd43f55762240055` | Active is off | — |

Odoo's search also groups by Color; not built — a view per group-by would crowd the tabs, and Color is a column.

### Rules and buttons

None, as §3 says: Name is required on the field itself, and the Active switch is the archive action.

### Roles

`roles.py` `plan` listed only this worksheet and Incoterms, so `create` was run. Contact Tags joined like
**Countries** — **view for all four business roles**; only the app Administrator adds, edits or deletes a tag — as the
brief asked ("an administrator configuration table"). `roles.py check` passes.

**For the owner:** Odoo's *menu* is behind `base.group_system`, but its *access list* is wider —
`ir.model.access.csv` writes `res.partner.category` from **`base.group_partner_manager`** (a contact manager), exactly
as it writes `res.country.state`. States followed that and gave every role its Contacts cell (18 Sep 2026); Contact
Tags, as built, follows Countries instead. It matters once Tags is wired onto Contacts: in Odoo a person who can edit
contacts can create a tag from the Tags field; here only the Administrator can. Switching is one line in `roles.py`
(`VIEW_ONLY`) and a `create` run.

### Self-check — three TEST tags, left archived

| # | What | Result |
|---|---|---|
| 1 | TEST Grandchild Tag under TEST Child Tag under TEST Parent Tag | Complete Name "TEST Parent Tag / TEST Child Tag / TEST Grandchild Tag" through `record get` **and** the listing; its lookup "TEST Parent Tag / TEST Child Tag". Color empty — an API create applies no default |
| 2 | Rename the parent, then back | The grandchild followed both ways |
| 3 | The parent's Child Tags | 1 (the child) |
| 4 | A tag as its own parent, through the API | **Accepted**; it read "TEST Parent Tag / TEST Parent Tag", as 08's does. Cleared again in one write |
| 5 | Switch Active off on the grandchild | Out of All, into Archived |
| 6 | All three switched off | Left in Archived: TEST Parent Tag `e38e6c41-be3f-4eaf-86f9-19c2b0e05d26`, TEST Child Tag `6f49f1b3-2c04-4cca-8519-6c2f6ef6f9c5`, TEST Grandchild Tag `a2c8dcfa-c5f5-4384-9cb2-02cbfabc7199` |

### Differences from Odoo

| Odoo | Here | Why |
|---|---|---|
| "You can not create recursive tags." | Not built. The picker hides the tag itself (browser only); a longer loop (A under B under A) is not caught, and an API write can make a tag its own parent | 08 settled the same: no HAP rule can ask whether a record is its own ancestor |
| A random colour 1–11 on create | No color | HAP has no random default (§2) |
| Contact chips coloured from the tag | Colour shows on this worksheet only | HAP does not colour a relation chip from the target's field (§5) |
| Group by Color | not built | above |
| Name is translatable | one language | as everywhere in this app |

## 7 · Wiring — what the later step needs

Not built; no control was added to Contacts. Its own **version-pinned** step on a Phase 1 worksheet with hand-set
layout, added with `C.append_controls` (row 9999) — **placement is the owner's**.

| Worksheet | Control | Type | Alias | Intended place | Notes |
|---|---|---|---|---|---|
| **Contacts** | Tags | Relation → Contact Tags `6ab29232e54d2a34faaa98bb`, **multiple**, **one-way** (`bidirectional` "0"), shown as tags | `category_id` | the right half of row 5, beside DUNS — after Website and Tax ID, where Odoo's right-hand group ends (function, vat, website, lang, **category_id**) | Placeholder `e.g. "B2B", "VIP", "Consulting", ...` (Odoo's). Picker filter Active is on. **Not a column** in Contacts' views: Odoo's list carries it `optional="hide"`. A quick filter on Tags is worth adding; note it matches the tag itself, not its children (§5) |

Once Tags is on Contacts, decide the roles question above: with Contact Tags view-only, a business role can pick
existing tags on a contact but not create one from the picker.

## 8 · For the browser

Nothing here was seen in a browser.

1. **Sidebar**: Contacts shows Contact Tags between Contacts and Countries, with the bookmark icon.
2. **+ Record**: Name (placeholder), Color defaulting to **No color**, Category, Active **switched on**; Complete
   Name and Child Tags absent. Save "VIP" — the title reads VIP.
3. **Color**: the dropdown shows the twelve names **in their colours**, and the table draws the Color column as
   coloured chips.
4. **Category picker**: on an existing tag it offers the other active tags but **not the tag itself**, and no
   archived tag. Put a tag under another: Complete Name reads "Parent / Child" in the title and the table; the
   parent's form lists it under **Child Tags** (Name · Color columns) at the foot.
5. **Active switch**: switching it off and saving moves the tag from All to Archived; switching it on moves it back.
   There are no Archive / Unarchive buttons.
6. **By Category**: the table is grouped under each parent's name (and a group for tags with no Category). If it is
   not grouped, the grouping key is wrong — set it once in the view editor and read `advancedSetting` back.
7. **As Invoicing** (Select Role): view only — no + Record, the form read-only, the switch cannot be changed. **As
   Administrator**: full.
8. Clean-up: the three TEST tags sit in Archived.

