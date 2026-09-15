# 01 · Contacts

| | |
|---|---|
| Nocoly app | ERP Master |
| Section | Contacts |
| Worksheet | Contacts |
| Odoo model | `res.partner` (Odoo 19 Community) |
| Odoo source | `odoo/addons/base/models/res_partner.py`, `odoo/addons/base/views/res_partner_views.xml`, `addons/contacts/views/contact_views.xml` |
| Phase | 1 — core worksheet 1 of 7 |
| Status | Built with the hap CLI on 15 Sep 2026 · UI cross-check against Odoo pending |

One worksheet holds companies, the people who work at them, and their extra addresses (invoice, delivery,
other) — exactly as Odoo keeps all three in `res.partner`, linked by **Company**.

## 1 · Requirements

### Fields

Labels are Odoo's English labels. "Hidden" means not shown on the form but used by views, rules or buttons.

| # | Field | Odoo field | Nocoly type | Required | Default | Notes |
|---|---|---|---|---|---|---|
| 1 | Company Type | `company_type` | Single select: Person · Company | yes | Company | Odoo's Contacts app opens **New** on Company (`default_is_company: True`) |
| 2 | Name | `name` | Text · **title field** | when Address Type = Contact | — | Odoo constraint `_check_name`: "Contacts require a name". Addresses may be nameless |
| 3 | Email | `email` | Email | no | — | |
| 4 | Phone | `phone` | Phone | no | — | Default country Malaysia (+60) |
| 5 | Image | `image_1920` | Attachment (images) | no | — | Avatar; used as the card cover |
| 6 | Company | `parent_id` | Relation → Contacts (single) | no | — | Only companies can be picked (`domain is_company = True`) |
| 7 | Address Type | `type` | Dropdown: Contact · Invoice · Delivery · Other | yes | Contact | Shown only under a company |
| 8 | Street | `street` | Text | no | — | |
| 9 | Street 2 | `street2` | Text | no | — | |
| 10 | City | `city` | Text | no | — | |
| 11 | State | `state_id` | Text | no | — | Many2one in Odoo; Text until the Geography bundle |
| 12 | ZIP | `zip` | Text | no | — | |
| 13 | Country | `country_id` | Text | no | — | Many2one in Odoo; Text until the Geography bundle |
| 14 | Job Position | `function` | Text | no | — | Persons only |
| 15 | Tax ID | `vat` | Text | no | — | |
| 16 | Website | `website` | Text | no | — | |
| 17 | Contacts | `child_ids` | Relation → Contacts (multiple), reverse of Company | no | — | Tab **Contacts** |
| 18 | Salesperson | `user_id` | Member | no | — | Tab **Sales & Purchase** › Sales |
| 19 | Company ID | `company_registry` | Text | no | — | Tab **Sales & Purchase** › Misc; companies without a parent only |
| 20 | Reference | `ref` | Text | no | — | Tab **Sales & Purchase** › Misc |
| 21 | Notes | `comment` | Rich text | no | — | Tab **Notes** |
| 22 | Active | `active` | Checkbox | no | checked | Hidden. Archive / Unarchive set it |

### Form layout (Odoo `view_partner_form`)

- **Header:** Company Type · Name · Email · Phone · Image
- **Left column:** Company · Address Type · Street · Street 2 · City · State · ZIP · Country
- **Right column:** Job Position · Tax ID · Website
- **Tabs:** Contacts · Sales & Purchase · Notes

### Interaction rules (Odoo `invisible=` / `required=` attributes)

| Rule | When | Effect | Odoo source |
|---|---|---|---|
| Company hidden on companies | Company Type = Company and Company is empty | hide Company | `parent_id invisible="(is_company and not parent_id) …"` |
| Job Position only for persons | Company Type = Company | hide Job Position | `function invisible="is_company"` |
| Address Type only under a company | Company is empty | hide Address Type | address form `type invisible="not parent_id"` |
| Company ID only on stand-alone companies | Company Type = Person, or Company is set | hide Company ID | `company_registry invisible="parent_id or not is_company"` |
| Name required for contacts | Address Type = Contact | Name required | `name required="type == 'contact'"` |

### Validation rules

| Rule | When | Message | Odoo source |
|---|---|---|---|
| Contacts require a name | Address Type = Contact and Name is empty | Contacts require a name | SQL constraint `_check_name` |

### Buttons (Odoo ⚙ Actions menu)

| Button | Shown when | Does | Confirmation |
|---|---|---|---|
| Archive | Active is checked | Active → unchecked | "Are you sure that you want to archive this record?" |
| Unarchive | Active is unchecked | Active → checked | none |

### Views (Odoo Contacts menu: list first, then kanban)

| View | Type | Shows | Odoo source |
|---|---|---|---|
| Contacts | Table | Active records. Columns: Name, Email, Phone, Country, Company, Salesperson | `view_partner_tree` |
| Kanban | Gallery | Active records. Card: Image, Name, Email, Phone, City, Country | `res_partner_kanban_view` |
| Archived | Table | Archived records | search filter `inactive` |

Quick filters: Company Type (Odoo filters *Persons* / *Companies*), Salesperson, Company, Country.

### Automations (Odoo `_fields_sync`)

| Automation | Trigger | Does | Odoo source |
|---|---|---|---|
| Copy company address | Company set or changed, Address Type = Contact | Copy Street…Country from the company (only if the company has an address) | `onchange_parent_id`, `_fields_sync` 1b |
| Copy commercial fields | Company set or changed | Copy Tax ID from the company, and Salesperson if empty on a person | `_commercial_sync_from_company`, `_compute_user_id` |
| Push address to contacts | A company's address changes | Update every Contact-type contact under it | `_children_sync` 2b |
| Push Tax ID to contacts | A company's Tax ID or Company ID changes | Update every contact under it | `_commercial_sync_to_descendants` |

### Not built now, and why

| Odoo field / feature | Why not now |
|---|---|
| Tags (`category_id`) | Contact Tags bundle — excluded for now |
| Country, State as dropdowns | Geography bundle — excluded; Text meanwhile |
| Industry (`industry_id`) | Its own table (`res.partner.industry`), not in Phase 1 |
| Language (`lang`), Timezone (`tz`) | Odoo hides Language while one language is installed; neither drives anything yet |
| Company Name + **Create** company (`company_name`, `create_company`) | Only filled by CRM leads and website sign-up — arrives with CRM |
| Bank accounts, receivable/payable accounts, payment terms, fiscal position, pricelist | Added by Invoicing / Sales bundles, appended when those land |
| Smart buttons (Meetings, Sales, Invoiced …) | Belong to the apps that own them |
| Multi-company (`company_id`) | Single company |
| Upstream sync (a contact's address or Tax ID edit rewriting its company) | Odoo does this; left out to avoid automation loops — edit the company instead |
| Duplicate warning on same Tax ID / Company ID | Odoo only warns; revisit with Invoicing |
| Roles | Set once per app at the end of Phase 1 |

## 2 · Build

Built by `nocoly/build/contacts.py` (steps `fields → layout → rules → views → buttons → automations`);
every id is in `nocoly/build/ids.json`.

| Element | Built | Id |
|---|---|---|
| App | ERP Master | `6cb4d051-a33c-4bf9-b56f-5f47f0e85dc9` |
| Menu group | Contacts | `6aa8a3a93e5e4ad5b852a6d3` |
| Worksheet | Contacts, alias `res_partner` | `6aa8a3b34a22ad87b728c4fe` |
| Controls | 28: the 22 fields above (aliases = Odoo field names), 3 tabs, 3 dividers | — |
| Interaction rules | 5, as in the table above | — |
| Validation rule | Contacts require a name — checked in the form **and** on API writes | — |
| Views | Contacts (table) · Kanban (gallery) · Archived (table), all sorted by Name A→Z | `6aa8a3b34a22ad87b728c502` · `6aa8a4d11204328eb1af06f9` · `6aa8a4d14a73a3142152ca08` |
| Buttons | Archive · Unarchive, each running a one-step workflow that sets Active | `6aa8a5654720c515252bda3d` · `6aa8a5674a73a3142152ca18` |
| Automation | Contacts: copy company details to its contact | `6aa8a7ff8475f61d4cc65bb9` |
| Automation | Contacts: push company address and Tax ID to its contacts | `6aa8a8048475f61d4cc65ebe` |

Menu groups follow Odoo's app boundaries: **Contacts** now, then **Products** (Units & Packagings,
Products, Product Variants — shared by Invoicing, Sales, Inventory and Purchase) and **Invoicing**
(Journals, Invoices, Invoice Lines). A client copy drops an app by deleting its group.

### Found while building

- `hap worksheet create-custom-action --action-spec` ignores `--btn-id` and always adds a new button. A
  re-run created a second Archive/Unarchive pair; the broken pair was deleted with the owner's approval.
  HAP disabled — but kept — their two empty workflows (`6aa8a542d91d10186df35aa2`,
  `6aa8a543e589b8933dd4c83d`); they can be deleted from the workflow list.
- `hap app create --sections` also made an empty "Unnamed Group"; deleted with the owner's approval.
- To do in the UI check: the owner's screenshot showed the Contacts view listing every field instead of its six
  columns, and the Company Type quick filter without its Person / Company choices.
