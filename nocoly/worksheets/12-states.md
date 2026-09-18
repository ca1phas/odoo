# 12 · States

| | |
|---|---|
| Nocoly app | ERP Master · menu group **Contacts** |
| Worksheet | States |
| Odoo model | `res.country.state` |
| Reference | **casimir.odoo.com — Odoo saas~19.4+e**: the *Fed. States* screen, the model, its three views, the access list, `name_search` under three contexts, all 2 102 states and the state of every contact, extracted read-only to `nocoly/reference/odoo-19.4/res.country.state.md`; the records are `nocoly/data/casimir-states.json`. Behaviour the tenant cannot show is read from the Odoo 19.0 source in this repo: `odoo/addons/base/models/res_country.py`, `res_country_views.xml`, `res_partner.py`, `ir.model.access.csv` |
| Phase | 1 — **bundle 5 of 6** (Product Categories · Chart of Accounts · Payment Terms · Countries · **States** · Taxes) |
| Status | §1 written 18 Sep 2026; not yet built |

The second half of an address. Odoo ships 2 102 states in 74 of its 251 countries — Malaysia's sixteen among them
— and a contact points at one. This bundle adds the worksheet, seeds all 2 102, gives **Countries** the list Odoo
shows at the foot of its form, and **replaces Contacts' State text with the relation**, carrying the values across
before the text control goes. It also brings the pair of rules Odoo runs when the two fields disagree: **a state
sets its country, and a country clears a state that belongs elsewhere.**

## 1 · Requirements

### Fields

Labels are Odoo 19.4's; aliases are Odoo field names on `res.country.state`.

| # | Field | Odoo field | Nocoly type | Required | Default | Notes |
|---|---|---|---|---|---|---|
| 1 | State Name | `name` | Text | yes | — | Odoo's help as the description: "Administrative divisions of a country. E.g. Fed. State, Department, Canton" |
| 2 | State Code | `code` | Text | yes | — | Odoo's help: "The state code." **Not *No duplicates*** — Odoo's constraint is the pair (country, code), and the same code sits in many countries: 01 is Portugal's, Mongolia's, Peru's and Ecuador's at once. See *Not built now* |
| 3 | Country | `country_id` | Relation → Countries (single, **two-way**), dropdown | yes | — | The reverse is field 5 on **Countries**. The picker lists all 251 countries by name |
| 4 | Display Name | `display_name` | Function formula, text · **title field** | — | — | **"Selangor (MY)"** — State Name, a space, the country's code in brackets, which is exactly Odoo's `_compute_display_name` and what every picker shows. **Read-only and hidden on create** (`fieldPermission` "100"), as 04's and 09's Display Name are |
| — | Country Code | *(helper)* `country_id.code` | Lookup through Country, stored | — | — | Hidden. Feeds field 4, the way 08's Parent Complete Name feeds its Complete Name |

**No Active field, so no Archive and no Unarchive** — `res.country.state` has none, as `res.country` has none.

### On Countries (11)

| Change | Detail |
|---|---|
| New field **States** (`state_ids`) | Relation → States (multiple) — **the reverse of field 3**, which HAP creates with it. **Read-only**: a state is given its country on the state, as Odoo's editable list does it the other way round. Shown as a list at the foot of the country form, columns **State Name · State Code**, which is exactly Odoo's list there |
| Remark block | Its last line — "The States Odoo lists at the foot of the form arrive with the States bundle" — is rewritten: the States are here; the currency, the flag and the address layout are still not |

### Form layout

Odoo's state form is one group of three fields.

| Odoo 19.4 | Nocoly |
|---|---|
| State Name · State Code · Country (`no_open`, `no_create`) | State Name \| State Code · Country \| Display Name |

| Row | Left (6) | Right (6) |
|---|---|---|
| 1 | **State Name** | **State Code** |
| 2 | **Country** | Display Name — read-only, hidden on create |

### Rules

None. All three fields are required on the control itself.

**Odoo's one constraint is not built.** `unique(country_id, code)` — *"The code of the state must be unique by
country!"* — is a pair, and HAP's *No duplicates* is a single field. Putting it on State Code would refuse
Portugal's 01 because Mongolia already has one. §2 should **try *No duplicates* on a hidden formula of
`country code + "|" + state code`** and say whether HAP allows the switch on a formula control; if it does not,
this is a difference, and nothing stops two states of one country sharing a code.

### Buttons

None — there is no Active field to archive.

### Views

| View | Type | Shows | Odoo 19.4 |
|---|---|---|---|
| States | table — the only view | Every state. Columns **State Name · State Code · Country**, sorted **State Code A→Z**, then Country Name. Quick filter **Country** | `base.view_country_state_tree`, the same three columns, `_order = 'code, id'` — so Odoo's list reads Aveiro (PT) 01, Архангай (MN) 01, Amazonas (PE) 01, Azuay (EC) 01, Beja (PT) 02 …, states of different countries interleaved. Its search view offers Name and Country and **one group-by, Country**, which is what the quick filter stands for |

Odoo's list is **editable in place** and carries a **New** button; ours is a table like every other worksheet's.
The tie at equal code is Odoo's record id and ours is the Country name — the same class of difference as 02's and
05's.

### Automations

Odoo keeps a contact's Country and State in step with two onchanges. Both become workflows on **Contacts**, and
both are **quiet** — their write starts no other workflow (`triggerType` 2, the pattern bundle 3 set for C and
Confirm) — so they cannot set each other off.

| | Workflow | Fires | Does | Odoo |
|---|---|---|---|---|
| **E** | *Contacts: the Country follows the State* | **State** changes, and it is not empty | When the state's Country is not the contact's Country, **write the contact's Country** from the state | `_onchange_state` |
| **F** | *Contacts: a State that belongs elsewhere is cleared* | **Country** changes, and State is not empty | When the State's Country is not the contact's Country, **clear the State** | `_onchange_country_id` |

**What happens when one save changes both** is the open question for §3: both triggers match, each workflow is
quiet, and HAP does not order them. Watch it and write down what the record ends up holding — Odoo's own answer
depends on the order the form fires its onchanges in, so whatever HAP does is a difference to record, not a
defect to fix.

### What this bundle changes on Contacts (01)

| Change | Detail |
|---|---|
| New field **State** (`state_id`) | Relation → States (single, **one-way**), dropdown, not required, no default. It takes the Text control's place — row 8, right half, beside City — and the alias `state_id` is free: the stand-in holds `state`, as Country's held `country` |
| Picker | **Every state in the world**, by Display Name, *not* narrowed to the contact's country. That is Odoo: its partner form passes `default_country_id`, which `name_search` does not narrow on — proved on the tenant (`reference/…/res.country.state.md`). Picking a state of another country then moves the contact, through workflow E |
| Carry across | The **eight** contacts that have a State text — **Selangor** on seven (Klinik Kesihatan Damansara, Sunway Construction Group, TEST QA Trading Sdn Bhd and its four people) and **Sarawak** on one (Sarawak Timber Logistics) — take the matching Malaysian state; every value is read back before anything is removed. They are the same eight that carry Malaysia |
| Deleted | The **State text control** `6aa8a452f363582dd37a50e5`, once the values are carried and read back (`DECISIONS.md`, 17 Sep) |
| Views | **No view points at State** — the Contacts and Archived tables show Display Name · Email · Phone · Country, and the Kanban card Email · Phone · City · Country. Nothing to re-point; check it and say so |
| Automations | The two address syncs (*copy the company's address*, *push it to the contacts*) **name the State control in four places**, exactly as they named Country. Re-point them **before** the delete, as bundle 4 did |
| *Not built now* | 01's Country line already points at bundle 4; its State line now points here |

### Roles

**Odoo writes a state from a different place than a country.** `ir.model.access.csv` gives `group_public`,
`group_portal` and `group_user` read, and **`base.group_partner_manager`** — a contact manager, not a settings
administrator — read, write, create and delete. Odoo's own Fed. States list carries a **New** button where the
Countries list does not.

None of our four business roles stands for `group_partner_manager`, so States joins `build/roles.py` the way
Countries did: **view for all four**, with the app **Administrator** creating and editing. The difference from
Countries is the reason, not the outcome, and it is worth a line in the role's description: a contact manager may
create a state in Odoo, and here that person is an administrator. The owner can overturn it — giving Accountant
and Invoicing *view · add · edit* would match Odoo more closely, since both already create contacts.

### Not built now, and why

| Odoo 19.4 field / feature | Why not now |
|---|---|
| The constraint `unique(country_id, code)` | A pair; HAP's *No duplicates* is one field. §2 tries it on a composite formula — see *Rules* |
| The **editable list** and its **New** button on Odoo's own screen | A HAP table edits in a record, not in the row |
| `formatted_display_name` — *"Selangor \t --MY--"* | One Display Name for everyone, as 09's accounts have |
| The state picker narrowed by the contact's country | Odoo does not narrow it either on the partner form (above). A HAP relation *can* be filtered by another control, so this is a deliberate no, not a limit — it would diverge from Odoo |
| `%(state_name)s` and `%(state_code)s` in a country's address layout | The address layout is not built (bundle 4's *Not built now*) |
| Translated state names | One language |
| States on taxes, fiscal positions and the localisations | Bundle 6 at the earliest; fiscal positions are not among the six |

### Records

1. **The 2 102 states** from `nocoly/data/casimir-states.json`: State Name, State Code, Country. Read every one
   back, and check the digests the reference records: **2 102 rows in 74 countries**, Malaysia **16** (MY-01 Johor
   … MY-16 Putrajaya), Great Britain and Latvia 119 each, Italy 111, Saudi Arabia **13**.
2. **Then Contacts**: the eight contacts with a State text take the matching state, read back, before the text
   control is deleted.

It is a lot of records for a Malaysian company's app, and the owner may prefer **Malaysia's sixteen alone**. The
case for all of them is the case bundle 4 made for all 251 countries: Odoo ships them, the picker is the point,
and seeding once costs nothing afterwards. Build all 2 102 unless the owner says otherwise.

No `TEST …` record is needed to seed; the test list adds its own.
