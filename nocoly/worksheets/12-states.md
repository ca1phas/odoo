# 12 · States

| | |
|---|---|
| Nocoly app | ERP Master · menu group **Contacts** |
| Worksheet | States |
| Odoo model | `res.country.state` |
| Reference | **casimir.odoo.com — Odoo saas~19.4+e**: the *Fed. States* screen, the model, its three views, the access list, `name_search` under three contexts, all 2 102 states and the state of every contact, extracted read-only to `nocoly/reference/odoo-19.4/res.country.state.md`; the records are `nocoly/data/casimir-states.json`. Behaviour the tenant cannot show is read from the Odoo 19.0 source in this repo: `odoo/addons/base/models/res_country.py`, `res_country_views.xml`, `res_partner.py`, `ir.model.access.csv` |
| Phase | 1 — **bundle 5 of 6** (Product Categories · Chart of Accounts · Payment Terms · Countries · **States** · Taxes) |
| Status | §1 written 18 Sep 2026 · built and self-checked 18 Sep 2026 (`nocoly/build/states.py`) · **the duplicate check dropped and rebuilt the same day at the owner's word** (§1 › Rules, §2 › *The duplicate check, rebuilt*) · **UI-tested 18 Sep 2026: 20 pass, 1 not isolated** (§3) · ready for review |

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
| 5 | Duplicate code | — | Checkbox, read-only, hidden on create | — | — | **Not an Odoo field.** Ticked by workflow G when another state already holds this state's key — what a person sees in place of Odoo's refusal. Added 18 Sep 2026 with the rebuilt check below |
| — | State key | — | **Text**, hidden and read-only, **No duplicates** | — | — | `<country code>\|<state code>` — *MY\|MY-10*. Written by G, never typed. It replaced the function formula of the first build, which took the switch and enforced nothing |

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

**Odoo's one constraint, and how it is enforced here — revised 18 Sep 2026, after the first build.**
`unique(country_id, code)` — *"The code of the state must be unique by country!"* — is a pair, and HAP's *No
duplicates* is a single field. Putting it on State Code would refuse Portugal's 01 because Mongolia already has
one. The first build tried the obvious thing: *No duplicates* on a hidden **formula** of `country code + "|" +
state code`. **HAP accepts the switch on a formula and enforces it nowhere** — not through the API and not in the
form (§3 test 7). The owner's answer: *"Drop it. Enforce uniqueness via other methods."*

So the formula goes, and the pair is enforced the only way HAP can — on a **Text** control, where *No duplicates*
is real (bundle 4 proved it refuses both an API write and a form save), with a workflow keeping it true:

| | What | Detail |
|---|---|---|
| **State key** | Text, hidden, **No duplicates**, read-only | `<country code>|<state code>` — *MY\|MY-10*. Written by workflow **G**, never typed |
| **Duplicate code** | Checkbox, read-only, on the form | Ticked by **G** when another state already holds that key. What a person actually sees |
| **G** | *States: the key and the duplicate check* | On create, and when **Country** or **State Code** changes: work out the key, look for another state that already has it, **tick Duplicate code** if there is one, and write the key. Quiet (`triggerType` 2) |

**What this does and does not do — rewritten 18 Sep 2026 against what HAP was measured doing, not what the switch
promised.** Two of this section's first guesses were wrong, and §2 has the transcripts:

- **A workflow's write ignores *No duplicates*.** The same value HAP refuses through the open API with
  `resultCode` 11 is **accepted** from a workflow's update step, silently, run status 2. So the key write cannot
  be the check.
- **Bundle 4's proof does not transfer.** There the unique control is one a person types into; here it is hidden,
  read-only and written by a workflow, and neither half of that carries over.

So **G does the checking itself**, and the shape is: work out the key → search for another state holding it,
excluding this record → if one exists, **tick Duplicate code, clear the key and stop the flow**; otherwise untick
and write the key. A duplicate therefore ends with **no key and a tick**, and its workflow run ends at the stop
node — `status` 3, `cause` 6666 — which is the visible mark in the run history. The invariant to test against is
**a state holds the key its code implies, or holds none and is ticked**.

HAP still cannot *refuse* the save: a workflow runs after it, so the duplicate is created and then marked a few
seconds later. That is the ceiling, and it is the reason Duplicate code exists at all.

### Buttons

None — there is no Active field to archive.

### Views

| View | Type | Shows | Odoo 19.4 |
|---|---|---|---|
| States | table — opens first | Every state. Columns **State Name · State Code · Country**, sorted **State Code A→Z**, then Country Name. Quick filter **Country** | `base.view_country_state_tree`, the same three columns, `_order = 'code, id'` — so Odoo's list reads Aveiro (PT) 01, Архангай (MN) 01, Amazonas (PE) 01, Azuay (EC) 01, Beja (PT) 02 …, states of different countries interleaved. Its search view offers Name and Country and **one group-by, Country**, which is what the quick filter stands for |

| Duplicate codes | table | The states Duplicate code is ticked on — nothing, unless something went in twice. The same three columns, plus **Duplicate code** | **Ours, not Odoo's.** Odoo has no such view because its database refuses the second state; this is where the check the owner asked for can actually be read |

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

**So States does not follow Countries.** The owner's answer, given while the build was running, is to follow
Odoo's access list here as it was followed there — and here it points somewhere else. The roles that create a
contact in this app create the state that contact sits in:

| Role | States | and its Contacts cell, for comparison |
|---|---|---|
| Accounting Administrator | **full** | full |
| Accountant | **view · add · edit** | view · add · edit |
| Invoicing | **view · add · edit** | view · add · edit |
| Accounting Read-only | **view** | view |

Delete stays with **Accounting Administrator** alone, the standing rule of 16 Sep, even though Odoo's
`group_partner_manager` may delete a state too. **Countries does not change**: `res.country` sits behind
`base.group_system`, so it stays view for all four with the app Administrator writing. Two worksheets, two
answers, both of them Odoo's.

### Not built now, and why

| Odoo 19.4 field / feature | Why not now |
|---|---|
| The constraint `unique(country_id, code)` **as a refusal** | A pair, and HAP's *No duplicates* is one field — and on a formula it is decoration, on a workflow's write it is ignored. What is built instead is the catch-and-mark above: a duplicate saves, then loses its key and gains a tick. Odoo refuses it outright |
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

## 2 · Build

Built by `nocoly/build/states.py` — steps `create → fields → key → reverse → views → dupview → roles → unique
→ seed → contacts → carry → retire → automations → duplicates → backfill`, or `all` for every one of them
followed by `check`. Each step reads the live state first, refuses to run unless the profile reaches ERP Master
› Contacts › States and the worksheet holds only this script's own work, reads back what it wrote, and is safe
to re-run:
**a second run of every step created nothing, wrote no record, rewrote no workflow node, changed no role and
changed no control** (`0 states written`, `0 keys written, 0 duplicates marked`, no republish of G,
`check: OK`). Helpers: `check` reads the controls, **both views and their order**,
the roles' entry, the reverse on Countries, workflow G and everything this bundle put on Contacts against §1;
`verify` compares all 2 102 states with the 19.4 extract field by field and prints §1's digests; `keys` reads
every State key back one record at a time and lists what carries Duplicate code; `selfcheck` drives the
duplicate check and then E and F through the CLI; `unique` reports where §1's *Rules* question stands; `order`
prints each view's records in its own order; `state MY-10` one state's stored values; `deadrefs` scans
every view, rule, button, control and workflow node of the app for a deleted control's id; `untouched` every
other worksheet's control count and digest; `show` the control list. The profile comes from `$HAP_PROFILE` and
otherwise from hap-cli's active profile; **nothing in `common.py` changed**.

| Element | Built | Id |
|---|---|---|
| App | ERP Master | `6cb4d051-a33c-4bf9-b56f-5f47f0e85dc9` |
| Menu group | Contacts — Contacts, Countries, **States** (after it) | `6aa8a3a93e5e4ad5b852a6d3` |
| Worksheet | States, alias **`res_country_state`**, icon `sys_9_2_map` | `6aace374805aef7032869ec9` |
| Controls | **7** — four fields, the Duplicate code checkbox and two hidden helpers; no tab, no divider, no remark block | — |
| Fields | State Name (required, Odoo's help) · State Code (required, Odoo's help, **no** No duplicates) | `6aace374805aef7032869eca` · `6aace384bd43f55762c74890` |
| | Country (required, Relation → Countries, single, **two-way**, `showtype` "3" a dropdown) · **Display Name** (function formula, text, **title**, `fieldPermission` "100") | `6aace384bd43f55762c74891` · `6aace39fe43d174ab374eeac` |
| | **Duplicate code** (checkbox, read-only and hidden on create — `fieldPermission` "100"; written only by **G**) | `6aacf930805aef703286a8ce` |
| Hidden helpers | Country Code (stored lookup of Countries' Country Code through Country, `strDefault` "00", "011") · **State key** (**Text**, `fieldPermission` "001" — hidden *and* read-only — carrying **No duplicates**) | `6aace392bd43f55762c7489d` · `6aacf923e43d174ab374f7c9` |
| Deleted on **States** | the **State key function formula** — the bundle's second owner-approved deletion, 18 Sep (DECISIONS.md) | `6aace4a47d58b0f4493134f4` |
| Views | States (the stock *All* view, renamed) — opens first · **Duplicate codes**, §1's second view | `6aace374805aef7032869ecd` · `6aad02af805aef703286ab80` |
| Rules · Buttons | **none**, as §1 says | — |
| On **Countries** | the reverse **States** (`state_ids`), read-only, a list at the foot of the form | `6aace384bd43f55762c74892` |
| On **Contacts** | the new **State** relation (`state_id`), single one-way → States, dropdown, row 8 col 1 | `6aace6c3e54d2a34fa4e530c` |
| Deleted on **Contacts** | the State **text** control, the owner-approved deletion | `6aa8a452f363582dd37a50e5` |
| Workflow **E** | *Contacts: the Country follows the State* — published, **quiet** | `6aace7dfa1c923a16e17e49a` |
| Workflow **F** | *Contacts: a State that belongs elsewhere is cleared* — published, **quiet** | `6aace7ec16473257ad6b77cc` |
| Workflow **G** | *States: the key and the duplicate check* — published, **quiet**, 16 nodes | `6aacf9524f2a99acac2c1fff` |
| Records | the tenant's **2 102 states**, every one carrying its **State key**, plus the four `TEST` states (below) | — |

Every id is in `nocoly/build/ids.json`: the six controls and the view under `"States: …"`, Malaysia's sixteen
states under `"States: MY|<state code>"` — Odoo's own natural key, the pair its constraint is on — with
`"States: TEST State One"` and `"States: TEST State Two"`, `"Contacts: State"` and `"Countries: States"` for
the two controls added to other worksheets, `"Contacts: TEST State Contact"` for the self-check's contact, the
two workflows by name, and `"States"` under `worksheets`. **The other 2 086 states are not in `ids.json`** —
they are found by the natural key, which reads back off the worksheet, and 2 102 keys would swamp the file. No
existing key was renamed.

`res.country.state` has **no `active` field**, so — as §1 says — there is no Active checkbox, no *Archived*
view and no Archive / Unarchive buttons. There are no rules either.

The form reads **State Name | State Code · Country | Display Name**, then the read-only **Duplicate code**
checkbox, with the two hidden helpers under them — §1's layout with the checkbox §1's revised *Rules* added:

```
r0  c0 s6   2 State Name      6aace374805aef7032869eca  name            required
r0  c1 s6   2 State Code      6aace384bd43f55762c74890  code            required
r1  c0 s6  29 Country         6aace384bd43f55762c74891  country_id      required ds=Countries src=…4892
r1  c1 s6  53 Display Name    6aace39fe43d174ab374eeac  display_name    title perm=100
               ds={"expression": "CONCAT($State Name$,\" (\",$Country Code$,\")\")"}
r2  c0 s6  36 Duplicate code  6aacf930805aef703286a8ce  duplicate_code  perm=100
r3  c0 s6  30 Country Code    6aace392bd43f55762c7489d  country_code    perm=011 ds=$Country$ src=Countries/Country Code
r3  c1 s6   2 State key       6aacf923e43d174ab374f7c9  state_key       perm=001 unique
```

**The controls went in in four saves, not one.** A formula saved under a client-side id computes nothing until
an `update-fields` save re-mints it (`BUILDING.md`), and both formulas here are built on controls that did not
exist yet, so each was appended on its own and read back before the next: (1) one full save of the empty
worksheet for State Name — reusing the stock title's id `6aace374805aef7032869eca`, so Description and
Attachment went with the save that left them out — State Code and the Country relation; (2) `add-fields` plus a
re-save for the Country Code lookup; (3) the same for Display Name; (4) the same for State key. Then one
placing save for rows, sizes, permissions and the title. **Display Name was the only control carrying
`attribute` 1 in that save**, so the title was not the coin toss `BUILDING.md` warns of, and both formulas
computed on the first record written.

**Two more saves followed on 18 September**, when the State key formula was dropped: one full save of States
leaving it out, then the Text State key and the Duplicate code checkbox appended (`add-fields`, no controlId,
so the server mints them) and one placing save that gave them their rows, aliases, descriptions and
permissions and moved Country Code down a row. `fields` and `key` share that placing save
(`states.place_controls`), which is driven by `PLACE` and writes only what differs.

### The reverse on Countries

`states.py reverse` did HAP's 已有关联 handshake by hand, the way `prodcat.ensure_reverses` paired Products'
Category with Product Categories' Products: a **two-way Relation saved on another worksheet gets no reverse at
all** — the server only reserves the id in `sourceControlId` and leaves it dangling — so the reverse was saved
on Countries carrying that reserved id `6aace384bd43f55762c74892`, with `sourceControlId` pointing back at
`6aace384bd43f55762c74891`, `sourceControlType` 6 and `enumDefault` 2. It reads back paired, and the pair
closes in both directions.

| | |
|---|---|
| Name · alias | **States** · `state_ids` |
| Shape | `showtype` "2" — a **list at the foot of the country form**, not a field in the grid; row 4 size 12 |
| Columns | **State Name · State Code**, by controlId from the States worksheet — exactly Odoo's two. A list with no `showControls` shows its row count over the words *No visible fields* |
| Permission | **`100`** — read-only **and hidden on create**. It was `101` until 21 Sep 2026, when the screen pass found a "101" reverse rendering on the Create Record form, where Odoo has no states list on a country that does not exist yet (`15-ui-conformance.md` §1). A state is still given its country on the state. `011` would take the table column with it; hidden-on-create does not |
| Reads back | Malaysia **18** (the sixteen plus the two TEST states), United Kingdom **119**, Saudi Arabia **13**, Singapore and Andorra **0**. `record get` returns the reverse half as a **row count**, an integer, not the rows |

The remark block `6aacb5ba7d58b0f449312e41` had its last line rewritten in the same save, from "The **States**
Odoo lists at the foot of the form arrive with the States bundle" to "The **States** Odoo lists at the foot of
the form are here, at the foot of this one". `countries.py` was updated to match — its `HTML` carries the new
text, so a re-run does not put the old line back, and a new `BUNDLE_5` tuple keeps its `guard` and `check` from
calling the reverse control unknown. **`countries.py check` and `verify` both still pass unchanged.**

### The two views

**States**, the stock *All* renamed, which opens first. Columns **State Name · State Code · Country**, sorted
**State Code A→Z then Country**, quick filter **Country**.

```
States  6aace374805aef7032869ecd  type=0  sortCid=State Code/2
        moreSort=[(State Code, asc), (Country, asc)]
        columns=[State Name, State Code, Country]
        fastFilters=[(Country, {'allowitem': '2', 'direction': '2'})]
```

A view sorts on a Relation by the related record's **title**, and Countries' title is Country Name, so §1's
"then Country Name" needed no extra field. The first rows the view returns are

> 01 Azuay, 01 Архангай, 01 Amazonas, 01 Aveiro, 02 Bolivar, 02 Баян-Өлгий, 02 Áncash, 02 Beja, 03 Canar,
> 03 Баянхонгор, 03 Apurímac, 03 Braga …

— codes interleaved across countries, which is Odoo's `_order = 'code, id'`, and within one code **Ecuador,
Mongolia, Peru, Portugal**, which is our Country Name where Odoo's is the record id. Odoo's own first four are
Aveiro (PT), Архангай (MN), Amazonas (PE), Azuay (EC): the same four rows in a different order, the difference
§1 predicted.

**The quick filter needed the spec adapter's object form.** Named in `--view-spec quickFilters` as a bare
control id — the way `contacts.py` names its three — it is stored with an **empty `advancedSetting`**, and
`upsert_views` then rewrote it on every run. Named as `{fieldId, selectionType: "multiple", displayType:
"dropdown"}` it lowers to `allowitem` "2" and `direction` "2", the shape Products' Category filter carries, and
the step is idempotent.

**Duplicate codes**, §1's second view, built by `states.py dupview` on 18 September with the rebuilt check —
the only place the tick can be read without opening a record:

```
Duplicate codes  6aad02af805aef703286ab80  type=0  sortCid=State Code/2
                 moreSort=[(State Code, asc), (Country, asc)]
                 columns=[State Name, State Code, Country, Duplicate code]
                 filters=[(Duplicate code, filterType 2, ['1'])]
                 fastFilters=[]
```

The filter is the spec adapter's switch condition — `common.switch_filter(Duplicate code, 'eq')`, the shape
02's *Archived* view uses on Active — and it lowers to **filterType 2** (equals) with the switch's `"1"`.
The view carries no quick filter of its own.

**The *States* view is not touched by this step**, and that is checked rather than assumed: `dupview` names
only its own view to `upsert_views`, names the pair to `sort_views` (which leaves every view it is not given
where it is, so States keeps opening first), and then **compares States' `showControls`, `sortCid`,
`sortType`, `moreSort`, `filters`, `fastFilters` and `advancedSetting` before and after**, stopping if any of
the seven moved. A second run reports `States: unchanged` and writes nothing.

It lists **two** records: **`TEST State Duplicate`** — the browser's, the one the backfill marked — and
**`TEST State Duplicate Two`**, `selfcheck`'s own. Both are Malaysian `ZZ-01`; **no seeded state appears**,
which is the point of it.

### §1's *Rules*, first cut: HAP takes *No duplicates* on a formula and never applies it

§1 first asked §2 to try *No duplicates* on a hidden formula of `country code + "|" + state code` and say
whether HAP allows the switch. **It does — and the switch does nothing.**

1. **The switch is accepted.** Tried first on the **empty** worksheet, on the Display Name formula (itself
   unique across all 2 102 states) so that nothing had to be created and deleted: `SaveWorksheetControls`
   returned success and `unique` read back `True`. The probe was reverted in the same run.
2. **So the composite key was built**, as §1 then said it should be: **State key** `6aace4a47d58b0f4493134f4`,
   a hidden function formula `CONCAT($Country Code$,"|",$State Code$)` with `unique` true. It computed: every
   seeded state held its pair, Selangor read `MY|MY-10`.
3. **And it refused nothing.** Two Malaysian states with the same code were created — `TEST State One` and
   `TEST State Two`, both moved onto `ZZ-01` — and the second write was accepted, `resultCode` 1; both read
   `State key` `MY|ZZ-01`. **§3 test 7 then showed the form accepts one too.**

So *No duplicates* on a **function formula** is stored and never enforced anywhere. The owner's ruling, the
same day: *"Drop it. Enforce uniqueness via other methods, maybe code+country_code or something else."*

### The duplicate check, rebuilt — 18 September 2026

§1's *Rules* was rewritten and this is what was built against it. `states.py key`, `duplicates` and `backfill`
own it; `check` reads it all back.

| | What | Id |
|---|---|---|
| **Deleted** | the State key **function formula**, the owner-approved deletion (DECISIONS.md, 18 Sep) — a full save of States leaving it out; the worksheet went 6 → 5 controls | `6aace4a47d58b0f4493134f4` |
| **State key** | a **Text** control, hidden *and* read-only (`fieldPermission` "001"), carrying **No duplicates**, holding `<country code>\|<state code>`. Nothing computes it: **G** writes it | `6aacf923e43d174ab374f7c9` |
| **Duplicate code** | a checkbox, read-only and hidden on create ("100"), `duplicate_code`. Written only by **G**. What a person actually sees | `6aacf930805aef703286a8ce` |
| **G** | *States: the key and the duplicate check* — worksheet event 新增或更新 on States narrowed to **Country and State Code**, no trigger condition, **quiet** (`triggerType` 2), 16 nodes | `6aacf9524f2a99acac2c1fff` |

**The new control took the deleted one's alias in the same run.** `state_key` was free the moment the formula
was saved away, even though the old control is still listed in the field recycle bin holding it — so the bin
reserves nothing (`BUILDING.md`). The ids.json key `States: State key` now holds the **Text** control's id;
no key was renamed. The bin reads

```
6aace4a47d58b0f4493134f4  State key      type 53  alias 'state_key'   ← the deletion
c7b7d5f2ef1f4a6fa5f4a3811f76fbbd  State key      type 53  alias 'state_key'
8a627637ed2e4e4287e63a637086f8cd  Display Name   type 53  alias 'display_name'
bcabc96a36694735873827cc5b260ba5  Country Code   type 30  alias 'country_code'
6aace374805aef7032869ecb  Description    type 2   ·  6aace374805aef7032869ecc  Attachment  type 14
```

— and only the first of those was ever deleted on purpose. The three 32-hex entries are **client-side ids left
by `add-fields` plus a re-save**, the pattern every formula on this worksheet was built with: the re-save mints
a server id and the client-side one lands in the bin. Anyone reading the bin should expect them, and **restore
nothing** — the live Text control already carries that name and alias.

**G, node by node.**

```
trigger  When a state's Country or State Code is written   assignFieldIds=[State Code, Country], no condition
  1      Get the country              get-related-record from the trigger's Country, on Countries
  2      Work out the key             function formula, text: CONCAT($country-Country Code$,"|",$trigger-State Code$)
  3      Another state with this key? search of States: State key = $key$ AND Record ID ≠ the trigger,
                                      oldest first (ctime), executeType 2 — carry on when nothing is found
  4      Is there one?                exclusive gateway
  4a       Yes — another state already holds this key   (the found state's State key is not empty)
             Tick Duplicate code  →  Clear the State key  →  Stop — a duplicate gets no key   (中止流程)
  4b       No — this key is free    (no condition: the default path)
             Untick Duplicate code
  5      Write the State key          the trigger record's State key ← $key-string_fx_id$
```

Three things about that shape are the answers to §1's open questions, and two of them are not what §1 expected.

1. **A workflow's write is not checked against *No duplicates*.** The first cut of G had no clear and no stop:
   the gateway ticked and both paths ran on into *Write the State key*. Driven onto a Malaysian `ZZ-01` that
   `TEST State One` already held, G **wrote the duplicate key and HAP took it** — two records then read
   `MY|ZZ-01` — while the *identical* value written through the open API a minute earlier was refused
   `resultCode 11`. Same control, same value, two write paths, two answers.
2. **So the run does not fail — there is nothing to fail.** Every run of that first cut came back `status` **2**
   (完成) with **every node at status 2**, *Write the State key* included. §1's "the key write is refused by
   *No duplicates* (the run fails, visibly)" is wrong in both halves.
3. **The shape is what enforces the pair, not the switch.** So the duplicate path was given *Clear the State
   key* (`isClear`) and a **中止流程 abort** (node type 30, `workflow node add --type 30 --after …`; hap-cli's
   DSL cannot build one). A branch converges, so an empty path is not a stop — only the abort keeps the run
   away from the write. A duplicate's run now comes back **`status` 3, `cause` 6666, `causeMsg` 中止**, naming
   the stop node, which is the visible mark §1 wanted, one step further down than it expected it.

**What *No duplicates* on the Text control is still worth.** It refuses a duplicate written through the **open
API** — which is how the backfill and any later import write, and it is what refused `TEST State Duplicate`'s
key while the other 2 103 went in. It is a backstop on that one path, not the mechanism; the invariant is kept
by G's shape. Anyone reading the control list and seeing the switch should read this paragraph — it does
nothing to a workflow's write and (below) nothing to a form save either — and so should anyone reading the
control's own **description**, which now says the same thing in the field editor.

**What the form will do is not measured here, and it is a structural answer rather than a guess.** The key is
hidden and read-only, so the browser neither renders it, nor types into it, nor recomputes it — and the
duplicate value does not exist at save time anyway, because G computes it afterwards. So a duplicate state
saved in the form should be **accepted silently**, with *Duplicate code* appearing on the record a few seconds
later. The API stands in for the form exactly here: a `record create` carrying Country and State Code and **no
State key** — the same fields a form sends — was accepted, and G ticked the record. §3 has the browser.

**The measurements, in one table** (`states.py selfcheck`, 18 Sep; every one re-runnable):

| | What was done | What HAP did |
|---|---|---|
| 0a | a State key another state holds, written through the **open API** | **refused**, `resultCode 11`, the control id in `badData`, nothing stored |
| 0b | a second Malaysian `ZZ-01` **created** through the API with no State key in the write | **accepted** — nothing refuses the record itself; G ran on the create and ticked it |
| 0c | its code moved to a **free** code | G unticked Duplicate code and wrote `MY|ZZ-09`; run `status` 2 |
| 0d | its code moved **back onto** `ZZ-01` | G ticked Duplicate code, cleared the key and **stopped**: run `status` **3**, `causeMsg` 中止, State key empty |
| 0e | an **unchanged** State Code re-sent together with a new State Name | Duplicate code stayed **off** — the search excludes the record that started the run |

0e is not a nicety. A field-narrowed trigger fires whenever one of its fields is in the write, **changed or
not** (`BUILDING.md`), so without `Record ID ≠ the trigger` in the search — `filedId` "rowid", conditionId
**10** (不等于), `conditionValues` `[{nodeId: <trigger>, controlId: "rowid"}]` — every ordinary form save of a
state would have found the record's own key and marked it as its own duplicate.

**The backfill.** `states.py backfill` gave all 2 102 seeded states their key through the API, in creation
order, marking a collision rather than writing one:

```
  2105 states; 2104 without a key; 0 already ticked; 2104 to write
  … 2000/2104 (332s)
  DUPLICATE 'TEST State Duplicate' (2026-09-18 16:00:32) holds MY|ZZ-01, which TEST State One already has
            — Duplicate code ticked (ok)
            the key write on it: refused, resultCode 11
  backfill: 2103 keys written, 1 duplicates marked
  2105 states: 2104 carry a State key, 1 do not, 1 carry Duplicate code
  2104 keys read back one by one: 0 differing {}
```

**Not one of the 2 102 seeded states came out ticked**, and every one of their keys reads back exactly
`<country code>|<state code>` — checked one record at a time, because a hidden control is blanked in the list
call. The one ticked record is **`TEST State Duplicate`**, the state §3 test 7 created in the browser: it is
the *second* Malaysian `ZZ-01`, `TEST State One` being the first, so it is the one that loses. `TEST State
One` keeps `MY|ZZ-01` and is not ticked; `TEST State Two` holds `MY|ZZ-02`. (A fourth, `TEST State Duplicate
Two`, is `selfcheck`'s own and ends every run ticked with no key.)

The invariant the whole thing keeps, and what `keys` asserts: **a state holds the key its own State Code
implies, or holds none and carries Duplicate code.**

Nothing else on this worksheet is unique. **State Code deliberately is not**: 01 belongs to Portugal, Mongolia,
Peru and Ecuador at once, and the switch there would have refused three of them.

### The 2 102 states

`seed` writes them in one batch and reads every one back. `hap worksheet record batch-create` exists and was
**not** used as a command: its help says 每行一次调用 — one `AddWorksheetRow` per row — and
`batch_create_rows` *also* re-reads the worksheet's controls for every row it encodes, which is 4 204 HTTP
calls, on top of a `--rows-json` argument far past the kernel's 128 KiB limit for one argument. `states.batch`
makes the same call through the CLI's own session with the same encoder (`_legacy_cell_entry`, so the Country
cell becomes `[{"sid": …}]` and nothing is sent raw) and the control list read once: **2 102 records in 291
seconds**, about seven a second. A state already stored as the extract has it is skipped, so the second run
wrote nothing.

```
  2102 states in the extract; 0 missing []; 0 differing {}; 2 live records outside it ['MY|ZZ-01', 'MY|ZZ-02']
  OK    count      live 2102     §1 2102     extract 2102
  OK    countries  live 74       §1 74       extract 74
  OK    MY         live 16       §1 16       extract 16
  OK    GB         live 119      §1 119      extract 119
  OK    LV         live 119      §1 119      extract 119
  OK    IT         live 111      §1 111      extract 111
  OK    SA         live 13       §1 13       extract 13
  OK    Malaysia   MY-01 Johor · MY-02 Kedah · MY-03 Kelantan · MY-04 Melaka · MY-05 Negeri Sembilan ·
                   MY-06 Pahang · MY-07 Pulau Pinang · MY-08 Perak · MY-09 Perlis · MY-10 Selangor ·
                   MY-11 Terengganu · MY-12 Sabah · MY-13 Sarawak · MY-14 Kuala Lumpur · MY-15 Labuan ·
                   MY-16 Putrajaya
            Display Name reads 'Selangor (MY)' for 'Selangor'
```

Every digest is checked **three ways** — what is live, the number §1 records, and the number computed from the
extract — and all three agree on every one. Malaysia's sixteen are in Odoo's own order, MY-01 to MY-16. The two
records "outside the extract" are the uniqueness probe's `TEST State One` and `TEST State Two`, so the States
view showed **2 104 rows** and the 2 102 are the ones the digests count. (§3 test 7 and the rebuild's
self-check have since added two more `TEST` states, so the view reads **2 106**; the digests are unmoved
because they count the extract's keys.)

Every state's **Display Name** is compared too, against `"<name> (<country code>)"` computed from the extract:
0 differing. So the function formula over the stored lookup is right on all 2 102, with no `refresh` pass — the
chain `Country → Country Code → Display Name` computed at create time on every row.

Reading 2 102 records back goes through the CLI's session (`GetFilterRows`), as bundle 4's 251 did: a `record
get` process costs about 1.2 s, which would be forty minutes for one read, and `check`, `verify` and `seed`
each read them all.

### What this bundle did to Contacts

| Change | Detail |
|---|---|
| The text control renamed and parked | `State` → **`State (text stand-in)`** at row 26, out of the relation's cell, so the two could exist side by side while the values moved. One full save, compared control by control |
| The relation added | **State** `6aace6c3e54d2a34fa4e530c`, type 29, alias **`state_id`**, single (`enumDefault` 1), `showtype` "3" (dropdown), `bidirectional` "0", not required, no default, **no picker filter** — every state in the world, by Display Name, which is Odoo (§1). Added with `add-fields` (no controlId, so the server mints one) and **placed at row 8 col 1 size 6** — the cell the text had, beside City — by a second save. §1 was right that the alias was free: the stand-in held `state` |
| States gained no reverse | The relation carries a `sourceControlId` `6aace6c3e54d2a34fa4e530d` that the server reserved and nobody ever saved — the dangling id `BUILDING.md` describes. `check` asserts no control on States carries it |
| The values carried | The **eight** contacts §1 names — seven *Selangor* (Klinik Kesihatan Damansara, Sunway Construction Group, TEST QA Trading Sdn Bhd and its four people: TEST Person One, Two, Three and **TEST UI Country Person**, the contact bundle 4's UI test left) and one *Sarawak* (Sarawak Timber Logistics) — read back holding `Selangor (MY)` and `Sarawak (MY)`. The other eight had no State and were given none |
| Views | **§1 was right: no view of Contacts ever named State.** The Contacts and Archived tables show Display Name · Email · Phone · Country and the Kanban card Email · Phone · City · Country, so `retire` had nothing to re-point — it checks and prints it rather than assuming, and `check` asserts the relation appears in no view's columns, card fields, quick filters or sort |
| The two address workflows re-pointed | The **four** places §1 counted, and they are four: *copy company details to its contact* — the branch **Contact-type, and the company has an address?** (one AND-group per address field, `conditionId` 7 on the company node) and the step **Copy the company address**; *push company address and Tax ID to its contacts* — the step **Copy the address to them** and the **trigger's `assignFieldIds`**. All four now name `6aace6c3e54d2a34fa4e530c` and read `fieldValueName` "State", not `""`. Nothing in `contacts.py` had to change for it: `ADDRESS` is looked up by name, and once the stand-in was renamed "State" meant the relation |
| The text control deleted | `6aa8a452f363582dd37a50e5`, a full save of Contacts that leaves it out. Contacts went 35 → 36 → 35 controls |
| `contacts.py` kept in step | `ADDRESS_TEXT` is now the **four** address fields still built as Text (Street, Street 2, City, ZIP); `HINTS` lost its dead `State` entry as it lost `Country`; `PLACE['State']` is unchanged and now places a Relation. `contacts.py layout` was run after the deletion **as a test** and changed nothing |
| The deleted id, afterwards | `states.py deadrefs` scanned **13 worksheets' views, rules, buttons and controls and all 30 workflows (354 nodes)**: `no reference` |

**Every save of Contacts and of Countries pinned HAP's optimistic lock** (`common.controls_with_version` →
`save_controls(…, version=…)`), because another administrator is still building the CRM worksheets in this app.
Every other worksheet's control digest is byte-identical to the one taken before the first write:

```
  Units & Packagings   10 controls  sha256:fec521c3eb8378c5      Journals             20  090afe02cb145208
  Products             24 controls  sha256:da8a69eb08350b2a      Payment Terms        12  ff76da6783d45216
  Product Variants     20 controls  sha256:6eba14458f20e2a6      Payment Term Lines    7  9f34ea4b506239e5
  Product Categories   10 controls  sha256:ec20fc990f0c5d1e      Invoices             33  506aba611a7f55dc
  Chart of Accounts    11 controls  sha256:d47363354585a909      Invoice Lines        14  e99c008917014117
```

### Workflows E and F

Both are worksheet-event workflows on **Contacts**, 新增或更新 narrowed to one field, with the trigger condition
**State is not empty** (`conditionId` 7). Both are **quiet** — `triggerType` 2, 不允许触发 — so E's write of the
Country cannot start F and F's write of the State cannot start E. Both published with no warnings.

| | E `6aace7dfa1c923a16e17e49a` | F `6aace7ec16473257ad6b77cc` |
|---|---|---|
| Trigger | *When a contact's State is set or changed* — `assignFieldIds` **State** | *When a contact's Country changes and it has a State* — `assignFieldIds` **Country** |
| Condition | State is not empty | State is not empty |
| 1 | **Get the state** — a get-related-record step from the trigger's State, on the States worksheet | the same |
| 2 | **The state's Country is not the contact's Country?** — an exclusive gateway | the same |
| 2a | *No — they already agree*: the state's Country **is** the contact's Country. No steps | the same |
| 2b | *Yes — the state belongs to another country*: **no condition**, the default path | the same |
| 3 | **Write the Country from the state** — the trigger record's Country ← the state node's Country (`nodeId` + `fieldValueId`) | **Clear the State** — the trigger record's State, `isClear` true |

**The gateway is written the way round it is because HAP has no "a Relation is not" operator.** A Relation
compared with another node's Relation is `conditionId` **33**, the workflow filter's *is*; hap-cli's operator
table has no opposite for it, and guessing a conditionId would have been guessing. So the **conditioned** path
is the one that carries nothing — "they already agree", `33` with `conditionValues: [{nodeId: <trigger>,
controlId: <Contacts' Country>}]` — and the write hangs off the **default** path, which a branch path with no
condition is (hap-cli `_build_branch`: *"a path with no `condition` is the default/else branch"*). It behaves
exactly as §1 describes.

`selfcheck` drives all of it through the CLI on `TEST State Contact`
(`b64b011f-2294-490f-af46-16fa014b335a`), which is left in Contacts:

```
  OK      0a-0e. the duplicate check (above)
  OK      1. E writes the Country from a new State:            state 'Selangor (MY)'  country 'Malaysia'
  OK      2. E leaves a State of the same country alone:       state 'Johor (MY)'     country 'Malaysia'
  OK      3. F clears a State that belongs elsewhere:          state None             country 'Singapore'
  OK      4. E moves the contact to the state's country:       state 'Aceh (ID)'      country 'Indonesia'
  selfcheck: OK
```

The whole of it was re-run after the duplicate check was rebuilt — nine checks, all OK — so **E and F are
unchanged by it**: G is on States, they are on Contacts, and G's writes start nothing (it is quiet).

Test 2 is the one that proves the gateway rather than the step: Johor is Malaysian and the contact was already
Malaysian, so E ran, took the *they already agree* path and wrote nothing. Test 3 is F on its own — the
contact's Country moved to Singapore while it held a Malaysian state, and F emptied the State.

**The first run of this self-check failed, and the workflows were right.** It wrote State, saw the expected
value and wrote Country a second later — but a worksheet-event workflow registers about five seconds after the
write that starts it, so E's run for the *Johor* write was still in flight, evaluated its gateway four seconds
**after** the Country had been set to Singapore, found the two disagreeing and wrote Malaysia back over it. F
then ran, correctly found a Malaysian state on a Malaysian contact, and did nothing. Both workflows were
behaving exactly as specified; `selfcheck` now waits for the record to stop changing (`quiesce`) before each
write. It is worth knowing for §3: **two changes a few seconds apart on one contact race, and the later run
wins.**

### Roles

**The owner changed this while the build was running**, and §1's Roles section was rewritten to match. States
does **not** follow Countries: Odoo's `ir.model.access.csv` writes `res.country.state` from
`base.group_partner_manager` — a contact manager — where `res.country` sits behind `base.group_system`. So
every role has the same cell on States that it already has on **Contacts**:

| Role | States | Countries, for contrast |
|---|---|---|
| Accounting Administrator | **full** | view |
| Accountant | **view · add · edit** | view |
| Invoicing | **view · add · edit** | view |
| Accounting Read-only | **view** | view |

`roles.py` grew States in `ORDER` and in the three explicit matrices (the fourth is computed), and its
`VIEW_ONLY` set — the worksheets no business role may write — deliberately does **not** gain it; a comment
there says why. Delete stays with Accounting Administrator alone, the standing rule of 16 Sep, even though
Odoo's `group_partner_manager` may delete a state.

**HAP had already added States to all four roles by itself**, as `BUILDING.md` warns, at its own defaults — own
records only (20/20/20), no create, and **export on**. `roles.reconcile` brought all four back to the owner's
table and switched export off on the three non-exporters; the CRM worksheets *Stages* and *Lost Reasons* were
printed as not-owned and left exactly as they were. `roles.py check` passes.

### Where this build departs from §1

| §1 says | What was built, and why |
|---|---|
| Five controls (four fields and one hidden lookup) | **Seven**, after the rebuild: the four fields, the hidden Country Code lookup, the hidden Text **State key** and the **Duplicate code** checkbox §1's revised *Rules* asks for |
| "the key write is refused by *No duplicates* (the run fails, visibly)" | **Neither happens.** A workflow's update step is not checked against the switch at all, so there is nothing to refuse and no run to fail (above). The visible mark is there, but it comes from an **abort node** the build added: `status` 3, 中止 |
| **G** *"work out the key, look for another state that already has it, tick Duplicate code if there is one, and write the key"* | Also **unticks** it when the key is free, **clears** the key on the duplicate path, and **stops** there. The untick is what keeps the checkbox honest when a duplicate is fixed by re-coding; the clear and the stop are what keep the key unique now that the switch is known not to bite |
| The search "look for another state that already has it" | needs `Record ID ≠ the trigger` as well, or a save that re-sends an unchanged State Code marks the record as its own duplicate (above) |
| "the deletion, then re-point" | Re-pointed **first**, as bundle 4 did: a deleted control stays in every view, rule and workflow step that names it and nothing cleans it up, so this is the order in which nothing is ever broken |
| The eight contacts are "TEST QA Trading Sdn Bhd and its four people" | Exactly right, once the fourth person is read as **TEST UI Country Person**, the contact bundle 4's UI test created. Seven Selangor, one Sarawak |
| Nothing | The **quick filter** had to be written as the spec adapter's object rather than a bare control id, or every run rewrote it (above) |
| "which a view filter can list" | Nothing listed them at first — §1's *Views* table had one row. The owner added a second the same day and **Duplicate codes** is built (above), so the tick is now readable without opening a record. The *States* view is untouched, as asked |

### Found while building

- **HAP stores *No duplicates* on a function formula and never applies it** (above). New in `BUILDING.md`.
- **…and a *workflow's* update step is not checked against it either**, on a control type where the open API
  is: the same duplicate value was refused `resultCode 11` through `record update` and accepted from a step,
  leaving two states holding one key (above). `BUILDING.md` now carries the whole question — where *No
  duplicates* is real and where it is decoration — as a section of its own.
- **A deleted control's alias is free at once.** The Text State key took `state_key` from the formula deleted
  in the previous call of the same run; the recycle bin holds the old control and reserves nothing. New in
  `BUILDING.md`.
- **The field recycle bin fills with controls nobody deleted**: `add-fields` plus a re-save leaves the
  **client-side id** of every formula and lookup in it, under the same name and alias. Three of States' six
  entries are those ghosts and only one is a real deletion (above). New in `BUILDING.md`.
- **A hidden control is blanked in `GetFilterRows` — but a *filter* on it still works.** Every State key read
  back empty from the list call, while `filterControls` "State key is empty" returned exactly the records
  without one. So a hidden field's values can be **found** in one call even though they can only be **read**
  one record at a time (`states.key_column`; 2 104 `GetRowDetail` reads took 274 s, about eight a second).
  New in `BUILDING.md`.
- **A search step can exclude the record that started the run** — Record ID *不等于* the trigger, conditionId
  **10** — which a field-narrowed trigger makes necessary. New in `BUILDING.md`.
- **A step that writes nothing still reports `status` 2**, so a run's detail cannot tell a skipped write from a
  done one; an **abort** is the only thing that marks a run — `status` 3, `cause` **6666**, `causeMsg` 中止,
  naming the node. `BUILDING.md`'s abort bullet gained the cause code and that consequence.
- **A two-way Relation created in the first full save of an empty worksheet behaves like one added with
  `add-fields`**: the server reserves the reverse id in `sourceControlId` and creates nothing on the target.
  `BUILDING.md` had this for `add-fields`; it is the general rule for a relation to *another* worksheet.
- **`hap worksheet record batch-create` is one `AddWorksheetRow` per row *and* one `GetWorksheetControls` per
  row.** New in `BUILDING.md`, with what to do instead.
- **A branch path with no condition is the else path**, which is how a comparison with no "is not" operator is
  written (above). New in `BUILDING.md`.
- **Two writes a few seconds apart on one record race the workflow runs they start**, and the later run wins
  (above). New in `BUILDING.md`.
- A **stored lookup through a Relation into another worksheet, and a function formula on top of it**, computed
  on all 2 102 rows at create time with no refresh pass — the `Country → Country Code → Display Name` chain.

### For the UI test (§3)

The first seven ran on 18 September and are §3's tests 1 to 17. **The rebuilt duplicate check needs a pass of
its own** — five tests, numbered 18 to 22 so they append to §3's list:

18. **A duplicate in the form, end to end.** Create a Malaysian state with State Code `ZZ-01` — three states
    already hold it. The save is expected to be **accepted quietly**: the key is hidden and read-only, the
    browser neither renders nor computes it, and the duplicate value does not exist until G runs. Then wait a
    few seconds, reload the record and expect **Duplicate code ticked**, read-only, with no State key. If the
    form *does* refuse the save, that is news and §2's paragraph above is wrong.
19. **An ordinary save does not tick.** Open **Selangor**, change nothing but the State Name, save, wait, and
    check Duplicate code is still **off** — the form re-sends State Code unchanged, which fires G (0e proves
    the case through the API; the browser is what proves what a form actually sends).
20. **Fixing a duplicate unticks it.** On the state made in test 18, change the code to something free
    (`ZZ-07`) and expect Duplicate code to clear itself a few seconds later, with a State key appearing.
21. **What a person sees of the key.** On any state's form: **Duplicate code** is visible and cannot be
    clicked, and **State key** is not on the form at all — nor is it a column of the States table, a hidden
    control never being one.
22. **The Duplicate codes view.** Open it from the view bar, after *States*: four columns — State Name · State
    Code · Country · Duplicate code — and the two `TEST` duplicates, with **no seeded state**. Then tick
    nothing and change nothing: the test is that the view is a list you can hand someone. Test 18's new state
    should appear in it a few seconds after it is saved, and leave it again after test 20.

And the seven the first build left, for reference — 1 is superseded by 18 above:

1. ~~Does the form refuse a duplicate?~~ — **test 18**.
2. The **States list at the foot of a country's form**: open Malaysia and check the tab shows the Malaysian
   states with the two columns State Name · State Code, and that it is read-only (no *+ Record*).
3. The **State picker on a contact**: it should offer every state in the world by Display Name — type "Sel" and
   expect Basel-Landschaft (CH), Kalimantan Selatan (ID), Selangor (MY), Overijssel (NL) — **not** narrowed to
   the contact's country, and with no *+ Record* for a role that cannot create a state.
4. **E and F in the form**, which is where Odoo runs them as onchanges: pick a state of another country and
   watch the Country follow; change the Country and watch the State clear. A HAP workflow runs **after the
   save**, not while the form is open, so the field will change on the record rather than under the cursor —
   that difference from Odoo is worth writing down.
5. **What happens when one save changes both** — §1's open question. Set Country and State together, to a
   country and a state that disagree, and record what the record ends up holding. Both triggers match, both
   workflows are quiet, HAP does not order them, and the racing seen in `selfcheck` says the later run wins.
6. The **States table**: **2 106** rows now, three columns, sorted by code with countries interleaved, and the
   Country quick filter as a dropdown.
7. **Role visibility** with Select Role: Accountant and Invoicing should now see **+ Record** on States (they
   may create one) and not on Countries.

### Test records left in the worksheet

| Record | Where | Why |
|---|---|---|
| `TEST State One` — ZZ-01, Malaysia, key `MY\|ZZ-01` | States | the first uniqueness probe's first record, and the **first holder** of `MY\|ZZ-01`, so it keeps the key and is not ticked |
| `TEST State Two` — ZZ-02, Malaysia, key `MY\|ZZ-02` | States | its second; `selfcheck` renames it and re-sends its unchanged code (test 0e) and puts the name back |
| `TEST State Duplicate` — ZZ-01, Malaysia, **no key, Duplicate code ticked** | States | §3 test 7's record, made in the browser. The second Malaysian `ZZ-01`, so it is the one the backfill marked — the only ticked record among the 2 102 seeded states and the build's own |
| `TEST State Duplicate Two` — ZZ-01, Malaysia, **no key, Duplicate code ticked** | States | `selfcheck`'s own: created through the API with no key in the write (0b), driven onto a free code and back (0c, 0d), and left ticked |
| `TEST State Contact` — Aceh (ID), Indonesia | Contacts | the self-check's contact for E and F |

## 3 · Test list

Run on 18 September 2026 in Chrome against the live app, with the stored values read back through the CLI where
the browser's own panel went stale. **20 pass and 1 not isolated** — test 7 failed on the first build, the owner had the field dropped, and tests 18–22 cover what replaced it. Records made here are named `TEST …`.

| # | Test | Steps | Expected | Result |
|---|---|---|---|---|
| 1 | Menu and view | ERP Master → **Contacts** → States | States sits after Countries; one view; 2 102 seeded rows plus the build's `TEST` ones | **Pass** — 2 104 at the start of the test, 2 105 after test 7 |
| 2 | Columns and sort | The States view | **State Name · State Code · Country**, State Code A→Z then Country Name | **Pass** — 01 Ecuador, Mongolia, Peru, Portugal; 02 … Odoo's own list is the same codes in the tenant's creation order (difference 1) |
| 3 | The Country quick filter | Country → *Malaysia* | Malaysia's states alone | **Pass** — **18** (16 seeded + the build's two `TEST` states) |
| 4 | A state's form | Open **Selangor** | State Name *Selangor* \| State Code *MY-10* · Country *Malaysia* \| Display Name *Selangor (MY)*, read-only; the record's title is the Display Name | **Pass** |
| 5 | The create form | + Record | Three required fields with Odoo's help under each; **no Display Name, no State key** | **Pass** — "Administrative divisions of a country. E.g. Fed. State, Department, Canton" and "The state code." |
| 6 | Display Name on a new state | Save one | Display Name reads *Name (CC)* without a refresh pass | **Pass** — the build computed all 2 102 at create time, and test 7's record got its own |
| 7 | **Two states of one country with the same code** | + Record → *TEST State Duplicate*, code **ZZ-01**, Country Malaysia — the build's `TEST State One` already holds ZZ-01 in Malaysia | Odoo refuses: *"The code of the state must be unique by country!"* | **Failed on the first build** — *Submitted successfully*, and the hidden State key **formula** carrying *No duplicates* refused nothing, in the API or the form. The owner had it dropped and the check rebuilt; **tests 18–21 are the replacement, and they pass** |
| 8 | No archiving | The view list and a form | No Archive / Unarchive and no *Archived* view | **Pass** |
| 9 | Countries: the States list | Open **Malaysia** on Countries | A **States** tab at the foot, columns State Name · State Code, and the remark block's last line now says the States are here | **Pass** — *States (19)*, newest first (a HAP relation list's order) |
| 10 | Contacts: the field | Open **Klinik Kesihatan Damansara** | **State · Selangor (MY)** beside City, where the text control was | **Pass** — Country · Malaysia beside it |
| 11 | The picker is not narrowed | On a Malaysian contact, type *Aceh* in State | **Aceh (ID)** is offered — Odoo's picker is not narrowed either | **Pass** |
| 12 | **Workflow E**, in the form | Set that contact's State to **Aceh (ID)** → Save | The Country becomes **Indonesia** | **Pass** — read back: State *Aceh (ID)*, Country *Indonesia* |
| 13 | **Workflow F** | Write **only** the Country (Malaysia) on a contact holding Aceh | The State is **cleared** | **Pass** — Country *Malaysia*, State empty |
| 14 | **Both in one write** — §1's open question | Send Country *Singapore* **and** State *Selangor (MY)* together | Unknown; §1 asked for it to be watched | **Answered**: both fire on the pre-save values — E writes the Country from the state (**Malaysia**) and F clears the **State**. The contact ends in the state's country with no state. Difference 3 |
| 15 | F on its own, through the form | Change only the Country on a contact holding a foreign state | The state is cleared | **Not isolated.** The one run ended with E's write winning — Country back to *Indonesia*, Aceh kept — and the browser could not be driven cleanly enough to repeat it. What a form sends decides which workflows match; test 13 and 14 pin the two ends. **Worth a reviewer's minute** |
| 16 | The address push carries the State | Set **TEST QA Trading Sdn Bhd**'s State to *Johor (MY)*, wait, read its contacts; then set it back | Its **Contact-type** contacts follow; the Invoice and Delivery addresses do not | **Pass** — the company and its four people read *Johor (MY)*, the two addresses nothing; all five back to *Selangor (MY)* afterwards |
| 17 | Roles | **Role debugging** as *Invoicing* | States offers **+ Record** (view · add · edit) where **Countries does not** | **Pass** — the two worksheets differ on screen exactly as Odoo's access list has them |
| 18 | **A duplicate made in the form** | + Record → *TEST State Duplicate Three*, code **ZZ-01**, Country Malaysia — a third Malaysian ZZ-01 | The record saves (HAP cannot refuse), then G marks it | **Pass** — *Submitted successfully*, and within seconds `duplicate_code` **1** with **no key**, exactly the invariant |
| 19 | The seeded states are clean | The backfill's read-back and the view below | All 2 102 hold the key their code implies, none ticked | **Pass** — 2 103 keys written, 0 differing, no seeded state ticked |
| 20 | **Fixing a duplicate** | Change that record's code to **ZZ-03** | The tick clears and the key is written | **Pass** — `state_key` *MY\|ZZ-03*, `duplicate_code` **0**, and it leaves the view |
| 21 | The **Duplicate codes** view | Open it | Only the ticked states | **Pass** — three while test 18 stood, two after test 20: `TEST State Duplicate` and `TEST State Duplicate Two`, both Malaysian ZZ-01, with a Duplicate code column |
| 22 | A hidden control in the two read paths | Read a ticked record with `record list`, then with `record get` | — | **Worth knowing**: `record list` returns a hidden control **blank** — Duplicate code read empty on a record the view was listing — while `record get` shows `1`. The view filters the stored value, so the view is right and the list is misleading (`BUILDING.md`) |

### Differences from Odoo seen in testing

1. **The tie at equal code.** Odoo orders `code, id`, so its list runs in the tenant's creation order within a
   code; ours breaks the tie on Country Name. The same class of difference as 02's and 05's.
2. **A duplicate code is caught after the save, not refused at it.** Odoo's `unique(country_id, code)` is a
   database constraint and HAP has no equivalent: *No duplicates* covers one field, is **decoration on a
   formula**, and is **ignored on a workflow's write** — §2 measured both, on the same control, minutes apart.
   What is built instead catches every duplicate a second later: the record ends with **no key and Duplicate code
   ticked**, its workflow run stops at the abort node, and the **Duplicate codes** view lists it until someone
   mends the code — at which point the tick clears and the key is written (tests 18–21).
   **Answered the same day.** The owner dropped it, and §2 › *The duplicate check, rebuilt* replaced it with a
   Text key, a **Duplicate code** checkbox and workflow **G**. The difference from Odoo stands and is now
   narrower: the duplicate record is still **created** — a workflow runs after the save — but it is caught,
   ticked on the record and its run ends in an abort. Tests 18 to 21 of §2's list are the browser pass this
   still needs.
3. **A save that changes both fields does both things.** Odoo's onchanges fire one at a time in the form, so you
   never get both; here E writes the Country from the state and F clears the state in the same save, and the
   contact ends in the state's country with no state (test 14).
4. **A relation list is newest first** — Malaysia's States tab starts with the newest state, where Odoo's list at
   the foot of a country is in code order. The same difference Payment Terms and Countries recorded.
5. **No editable list and no New button on a country's own form.** Odoo lets you type a state straight into the
   list at the foot of the country; here a state is a record of its own.

### Test records left in the worksheet

On States: **TEST State One** (ZZ-01) and **TEST State Two** (ZZ-02) from the first build; **TEST State
Duplicate** (ZZ-01 again) from test 7 and **TEST State Duplicate Two** from the rebuilt check's self-check — the
two the *Duplicate codes* view lists; and **TEST State Duplicate Three**, which test 18 made a duplicate and
test 20 mended (ZZ-03). On Contacts: **TEST State Contact** from the build. All go after sign-off, with the owner's approval; the 2 102
states stay. *The rebuild of 18 Sep added a fourth, **TEST State Duplicate Two** (ZZ-01 as well), so Malaysia
now reads 20; §2's table says what each one is for.*
