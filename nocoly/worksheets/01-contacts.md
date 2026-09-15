# 01 · Contacts

| | |
|---|---|
| Nocoly app | ERP Master · menu group **Contacts** |
| Worksheet | Contacts |
| Odoo model | `res.partner` |
| Reference | **casimir.odoo.com — Odoo saas~19.4+e** (form, list, kanban and search views read from the live tenant). Behaviour the tenant cannot show — constraints, sync rules — is read from the Odoo 19.0 source in this repo: `odoo/addons/base/models/res_partner.py` |
| Phase | 1 — core worksheet 1 of 7 |
| Status | Built with the hap CLI and matched to 19.4 on 15 Sep 2026 · **UI-tested: 13 of 13 pass**, 4 differences from Odoo noted · ready for review |

One worksheet holds companies, the people who work at them, and their extra addresses (invoice, delivery,
other) — as Odoo keeps all three in `res.partner`, linked by **Company**.

## 1 · Requirements

### Fields

Labels are Odoo's. "Hidden" means not on the form but used by views, rules or buttons.

| # | Field | Odoo field | Nocoly type | Required | Default | Notes |
|---|---|---|---|---|---|---|
| 1 | Name | `name` | Text · **title field** | when Address Type = Contact | — | Placeholder "Name (company or person)". Odoo constraint `_check_name`: "Contacts require a name"; a nameless invoice or delivery address is allowed |
| 2 | Company | `parent_id` | Relation → Contacts (single) | no | — | Placeholder "Company Employer". The picker lists contacts that have no company themselves and are not archived — Odoo 19.4 domain `[('parent_id', '=', False)]` |
| 3 | Address Type | `type` | Dropdown: Contact · Invoice · Delivery · Other | yes | Contact | Odoo shows it only when adding a contact from a company's **Contacts** tab; here, only once Company is set |
| 4 | Email | `email` | Email | no | — | |
| 5 | Phone | `phone` | Phone | no | — | Country code defaults to Malaysia (+60) |
| 6 | Job Position | `function` | Text | no | — | Placeholder "e.g. Sales Director" |
| 7 | Website | `website` | Text | no | — | Placeholder "e.g. https://www.odoo.com" |
| 8 | Tax ID | `vat` | Text | no | — | A base field (`res_partner.py:237`) — it has nothing to do with the Taxes bundle |
| 9 | Company ID | additional identifier *Company ID* | Text | no | — | 19.4 adds it with the **+** beside Tax ID (`company_registry` in 19.0) |
| 10 | DUNS | additional identifier *DUNS* | Text | no | — | The other **+** option beside Tax ID |
| 11–16 | Street · Street 2 · City · State · ZIP · Country | `street` `street2` `city` `state_id` `zip` `country_id` | Text | no | — | State and Country are dropdowns in Odoo; Text until the Geography bundle |
| 17 | Image | `image_1920` | Attachment | no | — | The avatar; the Kanban card cover |
| 18 | Contacts | `child_ids` | Relation → Contacts (multiple), the reverse of Company | — | — | Tab **Contacts**. Columns: Name, Address Type, Email, Phone, Job Position |
| 19 | Salesperson | `user_id` | Member | no | — | Tab **Sales & Purchase** |
| 20 | Reference | `ref` | Text | no | — | Tab **Sales & Purchase** |
| 21 | Notes | `comment` | Rich text | no | — | Tab **Notes**. Placeholder "Internal notes..." |
| 22 | Active | `active` | Checkbox | — | checked | Hidden. Set by Archive / Unarchive |

### Form layout

| Odoo 19.4 | Nocoly |
|---|---|
| Header: Image · Name · Company · Email · Phone | Name · Company \| Address Type · Email \| Phone |
| Left column: Address · Tax ID (+ Company ID, DUNS) · SST · TTx | Job Position \| Website · Tax ID \| Company ID · DUNS |
| Right column: Job Position · Website · Tags | *Address* divider · Street \| Street 2 · City \| State · ZIP \| Country · Image |
| Tabs: Contacts · Sales & Purchase · Invoicing · Notes | Tabs: Contacts · Sales & Purchase · Notes |

A HAP form is a 12-column grid, so Odoo's two columns become paired rows. HAP has no avatar slot; Image sits
under the address.

### Rules

| Rule | Type | When | Effect | Odoo source |
|---|---|---|---|---|
| Address Type only under a company | interaction | Company is empty | hide Address Type | `type` appears only in the Contacts-tab form |
| Name is required for contacts | interaction | Address Type = Contact | Name required | `name required="type == 'contact'"` |
| Contacts require a name | validation — form **and** API writes | Address Type = Contact and Name is empty | "Contacts require a name" | SQL constraint `_check_name` |

### Buttons (Odoo ⚙ Actions)

| Button | Shown when | Does | Confirmation |
|---|---|---|---|
| Archive | Active is checked | Active → unchecked | "Are you sure that you want to archive this record?" (`addons/web/static/src/views/form/form_controller.js:569`) |
| Unarchive | Active is unchecked | Active → checked | none |

### Views

| View | Type | Shows | Odoo 19.4 |
|---|---|---|---|
| Contacts | table | Active records. Columns Name · Company · Email · Phone · Country, sorted by Name A→Z. Quick filters Salesperson · Company · Country | List view. Its default columns are Name, Email, Phone, Activities, Country, and a person's name reads "Company, Person" — here Company is its own column. Its group-bys are Salesperson, Company, Country |
| Kanban | gallery | Active records. Image cover; Name, Email, Phone, City, Country | Kanban view |
| Archived | table | Archived records, same columns | The *Archived* filter |

### Automations (Odoo `_fields_sync`)

| Automation | Runs when | Does | Odoo source |
|---|---|---|---|
| Contacts: copy company details to its contact | a record's Company or Address Type is set or changed, and it has a Company | Copies the company's address — only for Address Type = Contact, and only if the company has an address. Copies each of Tax ID, Company ID and DUNS that the company has. Copies the company's salesperson to a contact that has none | `onchange_parent_id`, `_fields_sync` 1a–1b, `_get_commercial_values`, `_compute_user_id` |
| Contacts: push company address and Tax ID to its contacts | a record **that has contacts** changes its address, Tax ID, Company ID or DUNS | Copies Tax ID, Company ID and DUNS to all its contacts, and the address to its Contact-type contacts | `_children_sync`, `_commercial_sync_to_descendants` |

### Not built now, and why

| Odoo 19.4 field / feature | Why not now |
|---|---|
| SST and TTx registration numbers; Malaysian e-invoicing identity (Identification Type and Number, Industrial Classification, Malaysian TIN) | Malaysian e-invoicing localisation — on the tenant, SST and TTx come from `l10n_my_ubl_pint` and the TIN from `l10n_my_edi`, both built on Invoicing. They arrive with the Taxes bundle and e-invoicing. **Tax ID itself stays here:** `vat` is a base field |
| Tags (`category_id`) | Contact Tags bundle — excluded for now |
| State and Country as dropdowns | Geography bundle — excluded; Text meanwhile |
| Pricelist, Payment Terms, Payment Method, Incoterm, Fiscal Position (tab Sales & Purchase) | Pricelists, Payment Terms, Payments, Incoterms and Fiscal Positions bundles |
| Industry (`industry_id`) | Its own table (`res.partner.industry`), not in Phase 1 |
| GLN (`global_location_number`, delivery addresses) | Module `account` on the tenant — arrives with Invoicing |
| Invoicing tab — bank accounts, e-invoice sending and format, credit limit | Invoicing |
| Smart buttons (Opportunities, Sales, Invoiced, Meetings, Tasks), Activities, Last Reminder | Owned by other apps; HAP has native activity and discussion |
| Language (`lang`) | Odoo hides it while one language is installed |
| Properties | Odoo's ad-hoc custom fields; in HAP an admin adds a field instead |
| Is a Company (`is_company`) | Computed and read-only in 19.4, and not on the form; nothing here depends on it |
| Upstream sync — a contact's address or Tax ID edit rewriting its company | Odoo does it; left out to avoid automation loops — edit the company instead |
| "Potential duplicates" warning on the same Tax ID | Odoo only warns; revisit with Invoicing |
| Email required for a contact with a user login | No logins on contacts in HAP |
| Roles | Set once for the app at the end of Phase 1 |

## 2 · Build

Built by `nocoly/build/contacts.py` — steps `fields → layout → rules → views → buttons → automations`, each safe
to re-run; every id is in `nocoly/build/ids.json`.

| Element | Built | Id |
|---|---|---|
| App | ERP Master | `6cb4d051-a33c-4bf9-b56f-5f47f0e85dc9` |
| Menu group | Contacts | `6aa8a3a93e5e4ad5b852a6d3` |
| Worksheet | Contacts, alias `res_partner` | `6aa8a3b34a22ad87b728c4fe` |
| Controls | 28: the 22 fields above (aliases are Odoo field names), 3 tabs, 3 dividers | — |
| Rules | the 3 above | — |
| Views | Contacts · Kanban · Archived | `6aa8a3b34a22ad87b728c502` · `6aa8a4d11204328eb1af06f9` · `6aa8a4d14a73a3142152ca08` |
| Buttons | Archive · Unarchive, each running a one-step workflow that sets Active | `6aa8a5654720c515252bda3d` · `6aa8a5674a73a3142152ca18` |
| Automation | Contacts: copy company details to its contact | `6aa8a7ff8475f61d4cc65bb9` |
| Automation | Contacts: push company address and Tax ID to its contacts | `6aa8a8048475f61d4cc65ebe` |

**History.** Built first from the Odoo 19.0 source, then moved to 19.4 the same day by `contacts.py to194`,
keeping every id: Company Type (Person / Company) removed, DUNS added, the rules and views that depended on
Company Type retired, Company shown on every contact. A last pass copied Company ID and DUNS on linking, kept
archived companies out of the Company picker, and stopped the push automation running for contacts that have
nobody under them.

### Cleanup, 15 Sep 2026

- The 3 rules the 19.0 build left disabled — *Company is hidden on companies*, *Job Position only for persons*,
  *Company ID only on stand-alone companies* — were deleted in the form designer with the owner's approval (the CLI
  cannot delete a rule).
- The workflows of the duplicate Archive / Unarchive pair, `6aa8a542d91d10186df35aa2` and
  `6aa8a543e589b8933dd4c83d`, were already gone: HAP deletes a button's workflow with the button.

### Found while building — applies to every worksheet

- `hap worksheet create-custom-action --action-spec` ignores `--btn-id`: every run adds another button.
- `--view-spec` sets a table's `displayControls` only, and the table then shows every field. Columns are
  `showControls` plus `advancedSetting.customShowControls`; sort needs `--view-json` too.
- `workflow node get` returns a branch's conditions as `conditions`; `workflow node save` wants `operateCondition`.
- The Phone control validates numbers: an unallocated one such as 03-1234 5678 is refused, and so will be
  placeholders like "NA" when seeding from Odoo.
- Records created through the API must set Active, or they appear in neither Contacts nor Archived.

## 3 · Test list

Run in the Nocoly UI in Chrome on 15 Sep 2026; stored values were read back with the hap CLI after each step.
Test records are named `TEST …`.

| # | Check | Steps | Expected | Result |
|---|---|---|---|---|
| 1 | Empty form | + Record → Submit | Name is marked required; "Contacts require a name" | **Pass** — "Please fill in Name" on the field and a "Contacts require a name" dialog |
| 2 | Company record | Fill Name, Email, Phone, Website, Tax ID, Company ID, DUNS, address → Submit | Saved; appears in Contacts and Kanban, not Archived | **Pass** — every value read back; Address Type defaulted to Contact, Active to checked. Phone 03-2287 6543 stored as +60322876543 |
| 3 | Address Type hidden | Open the new company | No Address Type field (it has no Company) | **Pass** |
| 4 | Company picker | New record → open Company | Lists contacts without a company; not archived ones | **Pass** — lists only TEST QA Trading Sdn Bhd, never the people under it; "No records available" while that company was archived |
| 5 | Contact under a company | From the company's Contacts tab, add "TEST Person One" with no address | Address Type shows, default Contact. Within seconds the person has the company's address, Tax ID, Company ID and DUNS | **Pass** — all eight values copied |
| 6 | Nameless address | Add a Delivery address with no name | Saves (Name not required) and gets no address copied | **Pass** — saved; got Tax ID, Company ID and DUNS, no address |
| 7 | Salesperson | Set the company's Salesperson, then add another contact without one | The contact gets the company's salesperson | **Pass** — TEST Person Two got the salesperson |
| 8 | Push address | Change the company's City | Contact-type contacts get the new City; the Delivery address does not | **Pass** — Cyberjaya → Putrajaya on both people; the Delivery address stayed blank |
| 9 | Push identifiers | Change the company's Tax ID | Every contact under it gets the new Tax ID | **Pass** — all three got C2584563299 (changed in the same save as test 8) |
| 10 | Views | Contacts, Kanban and Archived tabs | Columns Name, Company, Email, Phone, Country; sorted by Name; Kanban shows image, email, phone, city, country | **Pass** — see differences 1 and 4 |
| 11 | Archive | Archive a contact | Confirmation text as above; it leaves Contacts and appears in Archived | **Pass** — exact text; the company moved to Archived; its contacts kept showing it as their Company, as in Odoo |
| 12 | Unarchive | Unarchive it from Archived | Back in Contacts | **Pass** — no confirmation, "Operation completed", back in Contacts |
| 13 | Odoo side by side | casimir.odoo.com Contacts vs Nocoly | Same fields as in §1, apart from the "Not built now" list | **Pass** — see differences below |

### Differences from Odoo seen in testing

1. **Display name.** Odoo names a company's contact "Company, Person" and a nameless address "Company, Delivery" —
   in lists, cards and every partner picker. Nocoly shows the Name alone, so a nameless address is blank in the list
   and "Unnamed" on its card. This will matter when Invoices picks a customer. **Owner's decision, 15 Sep: match
   Odoo now** — a *Display Name* formula becomes the title field; the affected tests are rerun afterwards.
2. **Archive / Unarchive.** The button that does not apply is greyed out rather than hidden.
3. **"Modifying form data" bar.** After adding a contact from the Contacts tab, or picking a Salesperson, an open
   record keeps a *Modifying form data — Cancel / Save* bar although the change is already stored. Clicking Save
   clears it. HAP behaviour, not the build.
4. **Kanban card.** The image sits on top of the card; Odoo puts the avatar on the left.

### Test records left in the worksheet

TEST QA Trading Sdn Bhd · TEST Person One · TEST Person Two · a nameless Delivery address under the company. Left
for the reviewer to inspect; remove them after sign-off.
