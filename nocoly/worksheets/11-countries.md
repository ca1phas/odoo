# 11 · Countries

| | |
|---|---|
| Nocoly app | ERP Master · menu group **Contacts** |
| Worksheet | Countries |
| Odoo model | `res.country` |
| Reference | **casimir.odoo.com — Odoo saas~19.4+e**: fields, the raw arch of every view, the actions and their menus, the access list, all 251 countries and the country of every contact, extracted read-only to `nocoly/reference/odoo-19.4/res.country.md`; the records themselves are `nocoly/data/casimir-countries.json`. Behaviour the tenant cannot show is read from the Odoo 19.0 source in this repo: `odoo/addons/base/models/res_country.py`, `res_country_views.xml`, `res_partner.py`, `ir.model.access.csv` |
| Phase | 1 — **bundle 4 of 6** (Product Categories · Chart of Accounts · Payment Terms · **Countries** · States · Taxes) |
| Status | §1 written 18 Sep 2026 · built and self-checked 18 Sep 2026 (`nocoly/build/countries.py`) · **UI-tested 18 Sep 2026: 22 pass, 1 fixed during the test** (§3) · ready for review |

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
bundle 5's reverse relation, not this one's — built on 18 Sep 2026 (`worksheets/12-states.md`).

### Form layout

Odoo's form has no title block: the name is simply the first field of the left group. HAP puts the title field at
the top of the record, so Country Name appears twice there, as Complete Name does on a category.

| Odoo 19.4 | Nocoly |
|---|---|
| Flag, top right (`image_url`, 128 × 128) | — (*Not built now*) |
| Group *country_details*: Country Name · Currency · Country Code | Country Name \| Country Calling Code |
| Group *phone_vat_settings*: Country Calling Code · Vat Label · Zip Required · State Required | Country Code \| Vat Label |
| Group *Advanced Address Formatting* (`groups="base.group_no_one"`): Input View · Layout in Reports · Customer Name Position | — (*Not built now*) |
| Label *States* and the editable `state_ids` list: State Name · State Code | **States**, a read-only list at the foot of the form, same two columns (bundle 5) |

| Row | Left (6) | Right (6) |
|---|---|---|
| 1 | **Country Name** | Country Calling Code |
| 2 | **Country Code** | Vat Label |
| 3 | Zip Required | State Required |
| 4 | **Remark block** *Also on Odoo's country form* (full width, 12) | |
| — | **States**, the reverse list — a `showtype` "2" Relation renders as a tab at the foot of the record, not in the grid (bundle 5) | |

Odoo's two columns become paired rows in a 12-column grid, as they do on Products. The remark block (type 10010,
the pattern 05 set) names what Odoo shows and this worksheet does not: **Currency**, the **flag**, the three
**Advanced Address Formatting** fields — which Odoo shows only in developer mode — and the **Country Groups**. Its
last line was rewritten by bundle 5 once the States arrived: it now reads "The **States** Odoo lists at the foot of
the form are here, at the foot of this one; the currency, the flag and the address layout are not in Phase 1."
`countries.py` carries the new text, so a re-run does not put the old line back.

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
| Not built here | Odoo's `country_code` (related `country_id.code`), and the onchange that **clears the State when the Country changes** — both needed States and both arrived with bundle 5: the onchange as workflow **F** on Contacts, and `country_code` as the hidden stored lookup **Country Code** on States (`worksheets/12-states.md`) |

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
| ~~States (`state_ids`)~~ | **Built on 18 Sep 2026 by the States bundle** (`worksheets/12-states.md`): the reverse half of the two-way Country relation on States, `6aace384bd43f55762c74892`, read-only, shown as a list at the foot of the country form with Odoo's own two columns State Name · State Code — Malaysia reads 18, Great Britain 119, Singapore 0. Odoo's *State Required* behaviour is **still not built**: the checkbox is stored on every country and nothing reads it |
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

## 2 · Build

Built by `nocoly/build/countries.py` — steps `create → fields → views → roles → seed → contacts → carry →
retire`, or `all` for every one of them followed by `check`. Each step reads the live state first, refuses to
run unless the profile reaches ERP Master › Contacts › Countries and the worksheet holds only this script's own
work, reads back what it wrote, and is safe to re-run: **a second `all` created nothing, wrote no record,
rewrote no workflow node, changed no role and changed no control** (`0 countries written`, `check: OK`).
Helpers: `check` reads the controls, the view, the roles' entry and everything this bundle put on Contacts back
against §1, `verify` compares all 251 countries with the 19.4 extract field by field and prints §1's six
digests, `selfcheck` drives No duplicates, the 2-character limit and the Zip Required default through the CLI,
`order` prints the view's records in the view's own order, `country MY` one country's stored values, `deadrefs`
scans every view, rule, button, control and workflow node of the app for the deleted control's id, `untouched`
every other worksheet's control count and digest, and `show` the control list. The profile comes from
`$HAP_PROFILE` and otherwise from hap-cli's active profile; **nothing in `common.py` changed**.

| Element | Built | Id |
|---|---|---|
| App | ERP Master | `6cb4d051-a33c-4bf9-b56f-5f47f0e85dc9` |
| Menu group | Contacts — Contacts, **Countries** (after it) | `6aa8a3a93e5e4ad5b852a6d3` |
| Worksheet | Countries, alias **`res_country`**, icon `sys_16_5_globe_earth` | `6aacb572805aef7032869637` |
| Controls | 7 — six fields and one remark block; no tab, no divider | — |
| Fields | Country Name (**title**, required, **No duplicates**) · Country Calling Code (Number, `dot` 0) | `6aacb572805aef7032869638` · `6aacb5ba7d58b0f449312e3c` |
| | Country Code (required, **No duplicates**, `checkrange` "1" min 1 **max 2**, Odoo's help) · Vat Label (Odoo's help) | `6aacb5ba7d58b0f449312e3d` · `6aacb5ba7d58b0f449312e3e` |
| | Zip Required (Checkbox, default **ticked**) · State Required (Checkbox, default unticked) | `6aacb5ba7d58b0f449312e3f` · `6aacb5ba7d58b0f449312e40` |
| Remark block | *Country form note* — type **10010**, `hidetitle` "1", full width under the fields | `6aacb5ba7d58b0f449312e41` |
| View | Countries (the stock *All* view, renamed) — the only view | `6aacb572805aef703286963b` |
| Rules · Buttons · Workflows | **none**, as §1 says | — |
| On **Contacts** | the new **Country** relation (`country_id`), single one-way → Countries, dropdown, row 9 col 1 | `6aacb7e2e54d2a34fa4e42a4` |
| Deleted on **Contacts** | the Country **text** control, the owner-approved deletion | `6aa8a452f363582dd37a50e7` |
| Records | the tenant's **251 countries**, plus one `TEST Country` (§3) | — |

Every id is in `nocoly/build/ids.json`: the seven controls and the view under `"Countries: …"`, the 251
countries under `"Countries: <ISO code>"` (Odoo's own natural key, as Chart of Accounts uses the account code)
with `"Countries: TEST Country"`, `"Contacts: Country"` for the control added to Contacts, and `"Countries"`
under `worksheets`. No existing key was renamed.

`res.country` has **no `active` field**, so — as §1 says — there is no Active checkbox, no *Archived* view and
no Archive / Unarchive buttons. There are no rules and no workflows either: both uniqueness constraints are the
field's own *No duplicates* switch, and nothing here is computed.

The form reads **Country Name | Country Calling Code · Country Code | Vat Label · Zip Required | State
Required**, with the remark block full width under them — §1's layout exactly:

```
r0  c0 s6      2  Country Name           6aacb572805aef7032869638  name            title required
r0  c1 s6      6  Country Calling Code   6aacb5ba7d58b0f449312e3c  phone_code      dot=0
r1  c0 s6      2  Country Code           6aacb5ba7d58b0f449312e3d  code            required
r1  c1 s6      2  Vat Label              6aacb5ba7d58b0f449312e3e  vat_label
r2  c0 s6     36  Zip Required           6aacb5ba7d58b0f449312e3f  zip_required
r2  c1 s6     36  State Required         6aacb5ba7d58b0f449312e40  state_required
r3  c0 s12 10010  Country form note      6aacb5ba7d58b0f449312e41
```

**All seven controls were created and placed in the worksheet's one full save.** A new worksheet's three stock
controls (Name, Description, Attachment) were sent back as one control — Country Name reused the stock title's
id, `6aacb572805aef7032869638` — and Description and Attachment went with the save that left them out. Country
Name was the only control carrying `attribute` 1, so the title was not the coin toss `BUILDING.md` warns of.
Only one thing needed a second save: `add-fields`-style creation stores `fieldPermission` as `""`, and the six
fields were brought to `"111"`.

### The 251 countries

`seed` creates one country per CLI call — 251 of them, about five minutes — and skips any whose six stored
values already equal the extract's, so the second run wrote nothing. Every one is then **read back field by
field** and compared with `nocoly/data/casimir-countries.json` (`xmlid`, `currency` and `address_format`
ignored, as §1 says). The result, from `countries.py verify`:

```
  251 countries in the extract; 0 missing []; 0 differing {}; 1 live records outside it ['ZZZ']
  OK    count            live 251      §1 251      extract 251
  OK    vat_label        live 54       §1 54       extract 54
  OK    state_required   live 15       §1 15       extract 15
  OK    zip_required     live 241      §1 241      extract 241
  OK    phone_code       live 124769   §1 124769   extract 124769
  OK    Malaysia         Malaysia · MY · 60 · no VAT label · ZIP required · state not required
```

Each digest is checked **three ways** — what is live, the number §1 records, and the number computed from the
extract — and all three agree on every one. `ZZZ` is `TEST Country`, the self-check's own record (below), so
the Countries view shows **252 rows** and the 251 are the ones the digests count.

The view returns them in its own order: *Afghanistan, Åland Islands, Albania, Algeria, American Samoa, Andorra,
Angola, Anguilla … Western Sahara, Yemen, Zambia, Zimbabwe* — the same place for *Åland Islands* that Odoo's
own list gives it.

Seeding went through `hap worksheet record create`, one process per record, because that is the call whose
value encoding the house trusts; **reading 251 records back does not**, and `countries.py` reads them through
the CLI's own session instead (the same `GetFilterRows` and `GetRowDetail` the read commands make). A CLI
invocation costs about 1.2 s of interpreter start, so one read-back of this worksheet through `record get`
would be five minutes, and `check` and `verify` read it every time.

### What this bundle did to Contacts

| Change | Detail |
|---|---|
| The text control renamed and parked | `Country` → **`Country (text stand-in)`** at row 26, out of the relation's cell, so that the two could exist side by side while the values moved. One full save, compared control by control |
| The relation added | **Country** `6aacb7e2e54d2a34fa4e42a4`, type 29, alias **`country_id`**, single (`enumDefault` 1), `showtype` "3" (dropdown), `bidirectional` "0", not required, no default, no picker filter. Added with `add-fields` (no controlId, so the server mints one) and **placed at row 9 col 1 size 6** — the cell the text had, beside ZIP — by a second full save. §1 was right that the alias was free from the start: the stand-in held `country`, Odoo's field is `country_id`, so there was no hand-over of the kind bundle 3 needed |
| Countries gained no reverse | The relation carries a `sourceControlId` `6aacb7e2e54d2a34fa4e42a5` that the server reserved and nobody ever saved — the dangling id `BUILDING.md` describes. `check` asserts no control on Countries carries it |
| The values carried | **Eight** of the fifteen contacts had a Country text, every one of them *Malaysia*; all eight now point at the Malaysia record `3a554a3a-b46a-4e7a-8a36-91c029161bb8`, read back one by one. The other seven — bundle 3's TEST companies and the two nameless addresses — had no country and were given none |
| The three views re-pointed | The **Country column** on *Contacts* and *Archived* (`showControls`, `displayControls`, `controlsSorts` and `advancedSetting.customShowControls`), the **Country quick filter** on *Contacts*, and the **country field on the Kanban card** (`displayControls`) all name `6aacb7e2e54d2a34fa4e42a4`. Nothing in `contacts.py` had to change for this: `step_views` looks every column up **by name**, and once the stand-in was renamed, "Country" meant the relation |
| The two address workflows re-pointed | **§1 missed these** — see below |
| The text control deleted | `6aa8a452f363582dd37a50e7`, a full save of Contacts that leaves it out. Contacts went 35 → 36 → 35 controls; every other worksheet's control digest is byte-identical to the one taken before the first write |
| `contacts.py` kept in step | `ADDRESS` still names all six address fields (the automations copy all six, by name); the new `ADDRESS_TEXT` is the five that `fields` still builds as Text; `HINTS` lost its dead `Country` entry; `PLACE['Country']` is unchanged and now places a Relation. `contacts.py layout` was run after the deletion **as a test** and changed nothing — the proof that the script and the worksheet agree |
| The deleted id, afterwards | `countries.py deadrefs` scanned **12 worksheets' views, rules, buttons and controls and all 30 workflows (354 nodes)**: `no reference` |

**Every save of Contacts pinned HAP's optimistic lock** (`common.controls_with_version` → `save_controls(…,
version=…)`). Another administrator was building CRM worksheets in this same app while this bundle ran, and
without the version hap-cli refetches the counter on a conflict and saves over whatever they wrote in between.

### The one thing §1 got wrong: the two address automations

§1's *What this bundle changes on Contacts* lists the views and the Kanban card. It does not mention
**Contacts' two address-sync automations**, and both of them named the text control — four nodes in all:

| Workflow | Node | What named the dead field |
|---|---|---|
| *Contacts: copy company details to its contact* | `Copy the company address` `6aa8a8018475f61d4cc65c63` | the update step's `fields` |
| | the branch `Contact-type, and the company has an address?` → its *Yes* path `6aa8a8008475f61d4cc65c0f` | one of its six OR-ed condition groups |
| *Contacts: push company address and Tax ID to its contacts* | `Copy the address to them` `6aa8a805e589b8933dd4e4be` | the update step's `fields` |
| | the trigger `When a company's address or identifiers change` `6aa8a8048475f61d4cc65ebf` | `assignFieldIds` |

Left alone they would have kept the dead id for ever — published, `isException` false, nothing raised
(`BUILDING.md`). Odoo pushes `country_id` between a company and its contacts exactly as it pushes `street` and
`zip` (`res.partner._address_fields`), so the right repair is to point them at the relation, not to drop
Country from them. `contacts.py` gained **`address_nodes`**, the address sibling of the `term_nodes` bundle 3
added: it rewrites the update step's whole `fields` list (`node save --type 6`) and the branch path's six
condition groups (`--type 2`) when they no longer match what the six names resolve to, and writes nothing when
they do. The trigger was already handled by `step_automations`' own rewrite. Both workflows republished
`isPublish: True, processWarnings: [], errorNodeIds: []`.

### Where this build departs from §1

| §1 | What was built, and why |
|---|---|
| "…only then delete the Text control; then re-point the Country column…" | **The re-pointing was done first.** A deleted control stays in every view, quick filter, rule and workflow step that names it and nothing cleans it up (`BUILDING.md`), so `retire` re-points the three views and the four workflow nodes, *then* deletes. The values were still carried and read back before anything was deleted, which is what §1's "only then" protects. Nothing was broken at any moment, and `deadrefs` found no reference afterwards |
| The picker "**may not create one**" — Odoo's `no_create` | **HAP has no such switch that the CLI can reach.** A Relation's `advancedSetting` carries `allowlink`, `searchrange`, `showtype`, `showquick` and the rest; nothing there says "the picker may not create a record", and nothing in hap-cli's builders writes one. What actually stops it is **Roles**: all four business roles have *view* on Countries, so no member of one can create a country from the picker or anywhere else. Only the app Administrator can. Whether the picker still draws a **+ New** for an administrator is for the UI pass |
| Country Calling Code "**no thousands separator**" | `advancedSetting.thousandth` is **"0"**, written explicitly — but that is also HAP's own default for a Number, and every Number already in this app reads back "0". So the setting is right; whether the browser draws *1264* or *1,264* is for the UI pass, and if it draws the comma there is no other key to try |
| "251 rows" | **252 live.** `TEST Country` (`ZZZ`) is the self-check's record and stays, as `TEST Category` does on Product Categories. Deleting a record needs the owner's approval, so it was not deleted; say the word and it goes |

### Self-checks through the CLI

`countries.py selfcheck` proves the three things §1 leans on, on `TEST Country`
(`5eff075a-a151-40fa-a4a5-f51e22a4fa20`), which is left in the worksheet:

1. **No duplicates is enforced on API writes, on both fields.** Setting `TEST Country`'s Country Name to
   *Malaysia* is refused with `resultCode 11`, and so is setting its Country Code to *MY*. The record reads back
   unchanged after both. §1 replaces Odoo's two SQL constraints with the field's own switch, and the switch is
   real — unlike a *Required*, which only the form enforces.
2. **The 2-character limit is the form's only.** `TEST Country` was created with the code **`ZZZ`** and stored
   it without complaint, exactly as 05's five-character Sequence Prefix does. That is why `seed` checks the
   length of all 251 codes itself before it writes anything.
3. **Zip Required's default does not apply through the API.** The create left the field out and it reads back
   **unticked**, though the field's default is ticked. HAP applies a default in the form only — the browser is
   the only place the tick can be confirmed.

### Roles

`build/roles.py` now carries Countries: it is in `ORDER` (right after Contacts, as in the menu group) and in
all four matrices as **view** — the first worksheet where *Accounting Administrator* is not *full*. §1's
reason holds: `ir.model.access.csv` gives `res.country` read to `group_public`, `group_portal`, `group_user`
and `group_partner_manager`, and read/write/create/delete to `base.group_system` alone, and none of the four
business roles stands for the settings administrator. `roles.py` gained a `VIEW_ONLY` set so that Accounting
Administrator's "everything is full" matrix can carry the exception, and the description of that role says so.
`roles.py check` passes.

Countries had already joined all four fine-grained roles **by itself**, at HAP's own defaults — own records
only (20/20/20), no create, and **export on** — which `reconcile` brought back to the owner's table, as it did
for Product Categories.

**Two worksheets in this app are not this build's, and `roles.py` had to learn to leave them alone.** Between
the first read of the app and the creation of Countries, another administrator added a **CRM** menu group with
**Stages** (`crm_stage`, `6aacb0f0805aef7032869597`) and **Lost Reasons** (`crm_lost_reason`,
`6aacb149e43d174ab374e721`). `roles.guard` used to stop unless the app held *exactly* the worksheets in
`ORDER`; it now stops only when one of `ORDER`'s own is missing, and prints the others. `reconcile` walks the
role's matrix, so those two sheets are read from each role model and posted back untouched — and `check` prints
a `note:` line for each instead of a difference. **They are still sitting in all four business roles at HAP's
defaults, export included**; whoever owns the CRM bundle has the same reconciling to do.

### `check`

```
  check: OK — the six controls and the remark block with their places, help, defaults and the two
  No-duplicates switches, Country Name the title, the Countries view sorted A→Z with no quick filter,
  view for all four business roles, and Contacts carrying the one-way relation in place of the deleted
  text control
```

and the other worksheets, before the first write and after the last (`countries.py untouched`) — only
Contacts moved, and only where this bundle moved it:

```
  Contacts             35 controls  sha256:5a995d4cbfec6617  ->  35 controls  sha256:e5d396eb7435dc56
  Units & Packagings   10 controls  sha256:fec521c3eb8378c5  (unchanged)
  Products             24 controls  sha256:da8a69eb08350b2a  (unchanged)
  Product Variants     20 controls  sha256:6eba14458f20e2a6  (unchanged)
  Product Categories   10 controls  sha256:ec20fc990f0c5d1e  (unchanged)
  Chart of Accounts    11 controls  sha256:d47363354585a909  (unchanged)
  Journals             20 controls  sha256:090afe02cb145208  (unchanged)
  Payment Terms        12 controls  sha256:ff76da6783d45216  (unchanged)
  Payment Term Lines    7 controls  sha256:9f34ea4b506239e5  (unchanged)
  Invoices             33 controls  sha256:506aba611a7f55dc  (unchanged)
  Invoice Lines        14 controls  sha256:e99c008917014117  (unchanged)
```

### Found while building

Both went into `BUILDING.md`.

- **`record list` returns more than the default view's columns — and less than everything.** The existing note
  said "only the default view's columns". It is not that: on Countries, whose view shows Country Name and
  Country Code, the row also came back with **Zip Required** and **State Required**, while **Country Calling
  Code** (a Number) and **Vat Label** (a Text) were **absent from the row altogether** — the key missing, not
  empty, which is how a reader can tell "not returned" from "no value". Contacts behaves the same way: its
  relations, its dropdown, its member field, its switch, its lookup and its formula all come back, and the text
  fields the view does not show do not. `countries.read_countries` checks the six ids against the first row and
  falls back to a per-record read when any is missing, which is what it does here.
- **A workflow update step's text field is stored as the template, whatever shape it is sent in.** Sent as
  `nodeId` + `fieldValueId` — the shape `batch-add` leaves behind and the shape a Relation keeps — a **text**
  field comes back with `nodeId` emptied and `fieldValue` holding `$<nodeId>-<fieldId>$`. It is the same
  binding written the other way and the step works, but a step that compares what it sent with what came back
  re-saves for ever unless it reads the node id out of the template
  (`contacts.node_fields.source_of`). The six fields of *Copy the company address* show both shapes side by
  side: five templates and one Relation.
- Also worth knowing, though it is a helper and not the platform: **`common.ensure_section` re-sorts the app's
  menu groups** when the group it is handed is not where it computes it should be. Called for the existing
  *Contacts* group with no `after`, it would have moved Contacts to the end of the sidebar, behind the CRM group
  another administrator had just added. `countries.step_create` looks the group up **by id** and re-sorts
  nothing.

### For the UI test (§3)

Worth pointing a browser at, in rough order of risk:

1. **Country Calling Code with no thousands separator** — Anguilla must read *1264*, not *1,264*.
2. **Zip Required ticked on a new country** and State Required clear — the defaults only the form applies.
3. **The 2-character limit and the two No-duplicates switches** as the form shows them (the messages appear
   while typing, before any save).
4. **The remark block** renders its HTML under the fields, with no heading of its own.
5. **Contacts' Country picker**: 252 records by name, one-way, no *Open*; whether it offers **+ New** to an
   administrator (§1 asks for `no_create`, and HAP has no switch for it).
6. **The Country column, quick filter and Kanban field** on Contacts, and the *Contacts* view's eight
   Malaysias.
7. **The two address automations** end to end: set a company's Country and watch its Contact-type contacts take
   it; link a new contact to a company with a country and watch it arrive.

## 3 · Test list

Run in Chrome on 18 September 2026, against the live app, with casimir.odoo.com open beside it. **22 pass and 1 was
fixed during the test** — test 23 was run later the same day, once role debugging was switched on. Records made here are named `TEST …`.

| # | Test | Steps | Expected | Result |
|---|---|---|---|---|
| 1 | Menu and view | ERP Master → **Contacts** group → Countries | Countries sits under Contacts; one view, *Countries*; 252 rows (251 + the build's `TEST Country`) | **Pass** |
| 2 | Columns and sort | The Countries view | **Country Name · Country Code** only, sorted Country Name A→Z, no quick filter | **Pass** — Afghanistan, Åland Islands, Albania, Algeria … (see difference 1) |
| 3 | A country's form | Open **Malaysia** | Country Name \| Country Calling Code · Country Code \| Vat Label · Zip Required \| State Required, then the remark block. *Malaysia · 60 · MY · no VAT label · ZIP required · state not required* | **Pass** — identical to Odoo's form for the six built fields |
| 4 | VAT label and State Required | Open **United States** | Calling code 1, code US, **Vat Label TIN**, Zip Required ticked, **State Required ticked** | **Pass** — TIN is the tenant's value, which the 19.0 base data does not carry |
| 5 | A country with no postcode | Open **Angola** | Code AO, calling code 244, **Zip Required clear** | **Pass** — one of the ten |
| 6 | The calling code's formatting | Open **Anguilla** | **1264**, not 1,264 (Odoo's `enable_formatting: false`) | **Fixed during the test** — it read *1,264*. HAP's `thousandth` is inverted: "0", the platform default, *draws* the separator and "1" hides it. Set to "1" in `countries.py`; Anguilla now reads **1264** (`BUILDING.md`) |
| 7 | Duplicate name refused | + Record → Country Name *Malaysia*, Code *MYX* → Submit | Refused on the name | **Pass** — *Duplicates are not allowed* under Country Name, and the toast *Please fill in the record correctly* |
| 8 | Duplicate code refused | Change the name to *TEST Duplicate Code*, code *MY* → Submit | Refused on the code | **Pass** — *Duplicates are not allowed*, this time under Country Code |
| 9 | The two-character limit | Country Code *MYX* → Submit | Refused | **Pass** — *Please enter 1 to 2 characters*. Form-side only: the API stores a longer code (§2) |
| 10 | Both fields required | Clear both → Submit | Refused on both | **Pass** — *Please fill in Country Name* and *Please fill in Country Code* |
| 11 | Zip Required's default | + Record | **Zip Required ticked**, State Required clear, both help texts under their fields | **Pass** — the default that the API does not apply (§2) is applied by the form |
| 12 | No archiving | Any country's form and the view list | No Archive / Unarchive buttons and no *Archived* view — `res.country` has no `active` | **Pass** |
| 13 | Search by name and by code | Search *Malaysia*; then *MY* | Name → Malaysia alone. Code → Malaysia, and whatever else holds those letters | **Pass** — *MY* returns **Malaysia (MY)**, Myanmar and Saint Barthélemy, Malaysia first. Odoo's `name_search` puts an exact code match first instead (difference 3) |
| 14 | Contacts: the field | Open **Klinik Kesihatan Damansara** → Address | **Country** is a dropdown reading *Malaysia*, beside ZIP, where the text control was | **Pass** — State is still Text (*Selangor*), as §1 says |
| 15 | Contacts: the column | The *Contacts* table | The Country column shows the relation for the 8 carried contacts | **Pass** |
| 16 | Contacts: the quick filter | Country → *Malaysia* | 8 rows: the three tenant customers and five `TEST` ones | **Pass** |
| 17 | Contacts: the Kanban card | The *Kanban* view | Each card shows Email · Phone · City · **Country** | **Pass** |
| 18 | Contacts: the Archived view | The *Archived* table | The same four columns, Country among them | **Pass** — no archived contact to show |
| 19 | The copy automation | Open *TEST QA Trading Sdn Bhd* → Contacts tab → + Record → name **TEST UI Country Person** → Submit | Within seconds the new contact holds the company's street, city, state, ZIP, Tax ID, Company ID, DUNS **and the Country relation** | **Pass** — read back: street *Level 8, Menara QA*, city *Putrajaya*, state *Selangor*, ZIP *63000*, **country_id → Malaysia** |
| 20 | The push automation | Set the company's Country to **Singapore**, wait, read its contacts; then set it back to Malaysia | Its **Contact-type** contacts follow; the Invoice and Delivery addresses do not | **Pass** — the four people took Singapore and returned to Malaysia; the two addresses never moved, as `_children_sync` has it |
| 21 | The picker | Klinik → click the Country field | The 252 countries, searchable | **Pass**, with two differences: it offers **+ Record** (difference 2) and lists the **newest first** (difference 4) |
| 22 | Opening a country from a contact | Click the *Malaysia* chip on a contact | Odoo's `no_open` keeps the country closed | **Difference 5** — ours opens the country's record |
| 23 | Role visibility | **Role debugging** — *Select Role* at the foot of the sidebar — as each business role in turn | The four see Countries and cannot add, edit or delete | **Pass — run 18 Sep 2026.** As **Invoicing** and as **Accounting Administrator** the Countries view has **no + Record**, a country's form is read-only, and — the point of difference 2 — **the Country picker on a contact offers no + Record**. Roles is what enforces Odoo's `no_create`, exactly as §3 claims |

### Differences from Odoo seen in testing

1. **Åland Islands sorts second here and last in Odoo.** Ours sorts Country Name A→Z with Å beside A; the tenant's
   database collation puts Å after Z, so Odoo's own list ends *Zambia · Zimbabwe · Åland Islands*. It is the only
   row of 251 where the two orders disagree.
2. **The picker offers + Record — to an administrator only.** Odoo's country field is `no_create`: a partner's
   Country cannot invent a country. HAP has no switch for it that the CLI can reach, so what stops it is Roles —
   and test 23 proved it: seen as **Invoicing**, the picker has no *+ Record* at all.
3. **A two-letter search does not jump to the code.** Odoo's `name_search` matches a 2-character search against
   the code first and returns those countries ahead of the name matches. HAP searches name and code together, so
   *MY* returns Malaysia, Myanmar and Saint Barthélemy, in name order.
4. **The picker lists the newest record first**, as it does on Payment Terms — with 252 countries that means the
   tail of the alphabet at the top. Odoo's picker is in name order.
5. **Clicking a country chip on a contact opens the country.** Odoo's field carries `no_open: True`.
6. **No flag, no currency, no address layout, no states** — all in *Not built now*, and all named in the remark
   block at the foot of the form.

### Test records left in the worksheet

**TEST Country** (code ZZZ) on Countries, the build's own self-check record — and note that its three-character
code is what proved difference *the API does not enforce the length*. On Contacts, **TEST UI Country Person**
under TEST QA Trading Sdn Bhd, from test 19. Both go after sign-off, with the owner's approval.
