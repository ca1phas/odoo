# 11 · Countries

| | |
|---|---|
| Nocoly app | ERP Master · menu group **Contacts** |
| Worksheet | Countries |
| Odoo model | `res.country` |
| Reference | **casimir.odoo.com — Odoo saas~19.4+e**: fields, the raw arch of every view, the actions and their menus, the access list, all 251 countries and the country of every contact, extracted read-only to `nocoly/reference/odoo-19.4/res.country.md`; the records themselves are `nocoly/data/casimir-countries.json`. Behaviour the tenant cannot show is read from the Odoo 19.0 source in this repo: `odoo/addons/base/models/res_country.py`, `res_country_views.xml`, `res_partner.py`, `ir.model.access.csv` |
| Phase | 1 — **bundle 4 of 6** (Product Categories · Chart of Accounts · Payment Terms · **Countries** · States · Taxes) |
| Status | §1 written 18 Sep 2026; not yet built |

The list a contact's address hangs on. Odoo ships 251 countries with their calling codes, their VAT labels and
two switches that say whether an address needs a state or a postcode, and every partner points at one. This bundle
adds the worksheet, seeds all 251, and **replaces Contacts' Country text with the relation** — the values are
carried across, read back, and the text control is then deleted, as the house rule asks. State stays Text until
bundle 5.

## 1 · Requirements

### Fields

Labels are Odoo 19.4's; aliases are Odoo field names on `res.country`.

| # | Field | Odoo field | Nocoly type | Required | Default | Notes |
|---|---|---|---|---|---|---|
| 1 | Country Name | `name` | Text · **title field** · **No duplicates** | yes | — | Odoo's `unique (name)`, message *"The name of the country must be unique!"* |
| 2 | Country Code | `code` | Text, **at most 2 characters** · **No duplicates** | yes | — | Odoo's `unique (code)`, *"The code of the country must be unique!"*. Odoo's help as the description: "The ISO country code in two chars. You can use this field for quick search." **Odoo upper-cases it on save; we do not** — see *Not built now*. The length limit is a form check, as 05's Sequence Prefix is |
| 3 | Country Calling Code | `phone_code` | Number, 0 decimals, **no thousands separator** | — | — | Odoo renders it with `enable_formatting: false`, so *1264*, not *1,264*. Malaysia is 60 |
| 4 | Vat Label | `vat_label` | Text | — | — | Odoo's help as the description: "Use this field if you want to change vat label." On the tenant 54 countries have one — VAT, GST No., TRN, CUIT … |
| 5 | Zip Required | `zip_required` | Checkbox | — | **checked** | Odoo's default is true; ten of the 251 have it clear |
| 6 | State Required | `state_required` | Checkbox | — | unchecked | 15 of the 251 have it set |

**No Active field, so no Archive and no Unarchive.** `res.country` has no `active` — the second worksheet after
Product Categories with none. The pair of buttons and the *Archived* view are deliberately absent.

**No reverse field on Contacts' side.** Odoo's country form does not list the partners in that country, so the
relation is **one-way**, as Products' Unit is. What the form does show is the country's **States**, which is
bundle 5's reverse relation, not this one's.

### Form layout

Odoo's form has no title block: the name is simply the first field of the left group. HAP puts the title field at
the top of the record, so Country Name appears twice there, as Complete Name does on a category.

| Odoo 19.4 | Nocoly |
|---|---|
| Flag, top right (`image_url`, 128 × 128) | — (*Not built now*) |
| Group *country_details*: Country Name · Currency · Country Code | Country Name \| Country Calling Code |
| Group *phone_vat_settings*: Country Calling Code · Vat Label · Zip Required · State Required | Country Code \| Vat Label |
| Group *Advanced Address Formatting* (`groups="base.group_no_one"`): Input View · Layout in Reports · Customer Name Position | — (*Not built now*) |
| Label *States* and the editable `state_ids` list: State Name · State Code | — (bundle 5) |

| Row | Left (6) | Right (6) |
|---|---|---|
| 1 | **Country Name** | Country Calling Code |
| 2 | **Country Code** | Vat Label |
| 3 | Zip Required | State Required |
| 4 | **Remark block** *Also on Odoo's country form* (full width, 12) | |

Odoo's two columns become paired rows in a 12-column grid, as they do on Products. The remark block (type 10010,
the pattern 05 set) names what Odoo shows and this worksheet does not: **Currency**, the **flag**, the three
**Advanced Address Formatting** fields — which Odoo shows only in developer mode — the **Country Groups**, and the
**States**, which arrive with bundle 5.

### Rules

None. Both required fields are required on the control, and both uniqueness constraints are the field's own *No
duplicates* switch.

### Buttons

None — there is no Active field to archive.

### Views

| View | Type | Shows | Odoo 19.4 |
|---|---|---|---|
| Countries | table — the only view | Every country. Columns **Country Name · Country Code**, sorted **Country Name A→Z**. No quick filter | `base.view_country_tree`, the same two columns, `_order = 'name, id'`. Its search view offers Country Name — whose filter matches **name or code** — and Country Calling Code, and has **no filters and no group-by**, so there is nothing to make a quick filter out of |

Odoo's list carries `create="0" delete="0"`: **its own screen offers neither New nor Delete.** HAP has no such
switch on a view, so the same thing is done with Roles below.

### Automations

None. Nothing here is computed.

### What this bundle changes on Contacts (01)

| Change | Detail |
|---|---|
| New field **Country** (`country_id`) | Relation → Countries (single, **one-way**), dropdown, not required, no default. It takes the Text control's place — row 9, right half, beside ZIP — and the **alias `country_id` is free from the start**: the stand-in holds `country`, Odoo's own field name is `country_id`, so there is no alias hand-over of the kind 10 needed |
| Picker | Lists all 251 countries by name and **may not create one** — Odoo's `options='{"no_open": True, "no_create": True}'` |
| Carry across | Every contact whose Country text reads *Malaysia* — all of them that have one — is given the relation, and every value is read back before anything is removed |
| Deleted | The **Country text control** `6aa8a452f363582dd37a50e7`, once the values are carried and read back (`DECISIONS.md`, 17 Sep) |
| Views | The **Country column** on the *Contacts* and *Archived* tables, the **Country quick filter** on *Contacts*, and the **country field on the Kanban card** are all re-pointed at the relation |
| *Not built now* | 01's row "State and Country as dropdowns — Geography bundle" becomes a line pointing here for Country; **State stays Text** until bundle 5 |
| Not built | Odoo's `country_code` (related `country_id.code`), and the onchange that **clears the State when the Country changes** — it needs States, so it belongs to bundle 5 |

### Roles

**Odoo reads countries to everyone and writes them from one place only.** `ir.model.access.csv` gives
`group_public`, `group_portal`, `group_user` and even `group_partner_manager` read alone, and only
`base.group_system` — the settings administrator — read, write, create and delete. None of our four business roles
stands for `group_system`.

So Countries joins `build/roles.py` with **view for all four** — Accounting Administrator, Accountant, Invoicing
and Accounting Read-only — and nobody but the app **Administrator** (Casimir and Teh Li Wei) creates, edits or
deletes a country. It is the first worksheet where Accounting Administrator is not *full*, and the reason is
Odoo's own access list; the owner can overturn it. `REVIEWING.md` › *Phase 1 · Roles* gains a column.

### Not built now, and why

| Odoo 19.4 field / feature | Why not now |
|---|---|
| Currency (`currency_id`) | `res.currency` is not among the six bundles, and multi-currency is not in Phase 1 |
| Flag (`image_url`) | A computed URL to a static image **on the Odoo server** — it would either point at a tenant that is about to disappear or mean 251 uploads. Named in the remark block |
| States (`state_ids`) | **Bundle 5**, which adds the reverse relation and Odoo's *State Required* behaviour with it |
| Country Groups (`country_group_ids`, `res.country.group`) | Not among the six; on the tenant they feed tax and pricelist scoping, neither of which is built |
| Input View (`address_view_id`), Layout in Reports (`address_format`), Customer Name Position (`name_position`) | Odoo hides all three behind `base.group_no_one`, developer mode. The address is six plain fields here and no report prints it yet. `_check_address_format` goes with them |
| The code forced **upper-case** on save | Odoo's `create` and `write` do it in Python. A HAP rule compares values, it cannot transform one; only a workflow could, and a workflow for a list that is seeded once and rarely touched is not worth its weight. The seed is upper-case throughout |
| A two-letter search matching the **code** first (`name_search`) | HAP's picker searches the title field; typing "MY" will not jump to Malaysia |
| The VAT label renaming a contact's **Tax ID** | `FormatVATLabelMixin` rewrites the field's own label per country. HAP cannot rename a field per record |
| `country_group_codes`, `is_stripe_supported_country`, `is_mercado_pago_supported_country` | Computed, on no view |
| Odoo's list forbidding **New** and **Delete** | Done with Roles instead — see above |
| Translated country names (`translate=True`) | One language |
| Clearing the ORM caches on write | Odoo internals |

### Records

1. **The 251 countries** from `nocoly/data/casimir-countries.json`: Country Name, Country Code, Country Calling
   Code, Vat Label, Zip Required, State Required. Read every one back, and check the six digests the reference
   records: 251 rows, 54 VAT labels, 15 state-required, 241 zip-required, calling codes summing to 124 769, and
   Malaysia reading *Malaysia · MY · 60 · no VAT label · ZIP required · state not required*.
2. **Then Contacts**: every contact whose Country text is *Malaysia* gets the relation, read back, before the text
   control is deleted.

No `TEST …` record is needed to seed; the test list adds its own.
