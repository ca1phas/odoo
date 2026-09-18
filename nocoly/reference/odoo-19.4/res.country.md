# res.country — as on casimir.odoo.com (Odoo saas~19.4+e)

Read-only extract, 18 Sep 2026: `fields_get`, the raw `ir.ui.view` arch of every view of `res.country`, the window
actions and their menus, `res.groups` of the reading user, the access list, every country's `name`, `code`,
`phone_code`, `vat_label`, `state_required` and `zip_required`, the states of Malaysia, the country of every
`res.partner` and of the company, and the Countries list and the Malaysia form on screen. Behaviour the tenant
cannot show is read from the Odoo 19.0 source in this repo: `odoo/addons/base/models/res_country.py`,
`odoo/addons/base/views/res_country_views.xml`, `odoo/addons/base/models/res_partner.py`,
`odoo/addons/base/security/ir.model.access.csv`.

The 251 records are saved as `nocoly/data/casimir-countries.json`. **They were rebuilt from this repo's
`odoo/addons/base/data/res_country_data.xml` and then verified against the tenant**, not copied through the
browser: both sides were reduced to one line per country (`code|name|phone_code|vat_label|state_required|
zip_required`), sorted, and compared by count, FNV-1a hash, sum of the calling codes and the three counts. Every
figure matched except the VAT labels — see *19.0 and 19.4* below — and the three that differ were taken from the
tenant.

Menu: **Contacts ▸ Configuration ▸ Localization ▸ Countries** (window action `base.action_country`, id 58, no
explicit view mode, so `list,form`). Beside it sit **Fed. States** (action 60, `res.country.state`) and **Country
Group** (action 59, `res.country.group`).

## Fields

Every field is module `base` unless noted. S = stored.

| Field | Label | Type | Req. | Default | Notes |
|---|---|---|---|---|---|
| `name` | Country Name | char S | **yes** | — | translatable; **unique** |
| `code` | Country Code | char(2) S | **yes** | — | **unique**; help "The ISO country code in two chars. \nYou can use this field for quick search."; `create` and `write` force it upper-case |
| `phone_code` | Country Calling Code | integer S | | 0 | shown without thousands formatting (`enable_formatting: false`) |
| `vat_label` | Vat Label | char S | | — | translatable; help "Use this field if you want to change vat label." — it renames *Tax ID* on a contact of that country |
| `zip_required` | Zip Required | boolean S | | **true** | |
| `state_required` | State Required | boolean S | | false | |
| `currency_id` | Currency | many2one → `res.currency` S | | — | |
| `state_ids` | States | one2many → `res.country.state` S | | — | on the form as an editable list of State Name · State Code |
| `country_group_ids` | Country Groups | many2many → `res.country.group` S | | — | on no view of the country |
| `country_group_codes` | Country Group Codes | json, computed | | — | the groups' codes, or `['']` |
| `image_url` | Flag | char, computed | | — | `/base/static/img/country_flags/<code lower>.png`; ten territories borrow another flag (`FLAG_MAPPING`: GF→fr, BV→no, BQ→nl, GP→fr, HM→au, YT→fr, RE→fr, MF→fr, UM→us, XI→uk) and two have none (AQ, SJ) |
| `address_format` | Layout in Reports | text S | | `%(street)s\n%(street2)s\n%(city)s %(state_code)s %(zip)s\n%(country_name)s` | python-style pattern over the address fields plus `state_name`, `state_code`, `country_name`, `country_code` |
| `address_view_id` | Input View | many2one → `ir.ui.view` S | | — | domain `[('model','=','res.partner'),('type','=','form')]` — replaces the address input block |
| `name_position` | Customer Name Position | selection S | | `before` | **Before Address · After Address** |
| `is_stripe_supported_country` | Is Stripe Supported Country | boolean, computed | | | module `payment`; on no view |
| `is_mercado_pago_supported_country` | Is Mercado Pago Supported Country | boolean, computed | | | module `payment`; on no view |

`_order = 'name, id'`. `_rec_names_search = ['name', 'code']`, and `name_search` is overridden so that **a
two-character search matches the code first** and those countries come back before the name matches.

## Constraints

| | Message |
|---|---|
| `unique (name)` | *The name of the country must be unique!* |
| `unique (code)` | *The code of the country must be unique!* |
| `_check_address_format` (Python) | *The layout contains an invalid format key* — raised when `address_format` names a key that is not an address field |

Creating or writing a country **clears the `stable` ORM cache** (the calling-code lookup) and, when
`address_view_id` or `vat_label` changes, the `templates` cache, because both change how a partner form is built.

## Form (`base.view_country_form`)

`<form create="0" delete="0">` — **Odoo's own screen offers neither New nor Delete.**

| | |
|---|---|
| Top right | the flag, `image_url` with `widget="image_url"`, 128 × 128 |
| Group *country_details* | **Country Name · Currency · Country Code** |
| Group *phone_vat_settings* | **Country Calling Code · Vat Label · Zip Required · State Required** |
| Group *Advanced Address Formatting*, `groups="base.group_no_one"` | **Input View** (with the note "Choose a subview of partners that includes only address fields…") · **Layout in Reports** ("Change the way addresses are displayed in reports") · **Customer Name Position** |
| Then | label *States* and the `state_ids` list, editable at the bottom, columns **State Name · State Code** |

The reading user holds `base.group_no_one`, so the advanced block **is** on the tenant's screen; a normal user
does not see it. Confirmed on screen for Malaysia: Country Name *Malaysia*, Currency *MYR*, Country Code *MY*,
Country Calling Code *60*, Vat Label empty, Zip Required ticked, State Required clear, the Malaysian flag, the
layout `%(street)s / %(street2)s / %(city)s %(state_name)s %(zip)s / %(country_name)s`, Customer Name Position
*Before Address*, and sixteen states from Johor (MY-01) down.

## List, search, and what is missing

- **List** `base.view_country_tree`: `<list string="Country" create="0" delete="0">` with **Country Name · Country
  Code**. Seen on screen: 251 rows, name order, **no New button**.
- **Search** `base.view_country_search`: one field, Country Name, whose `filter_domain` matches **name or code**,
  plus Country Calling Code. **No filters and no group-by.**
- No kanban, no graph, no pivot. The action carries the empty-list help *"No Country Found! Manage the list of
  countries that can be set on your contacts."*

## Access (`odoo/addons/base/security/ir.model.access.csv`)

| Group | R | W | C | D |
|---|---|---|---|---|
| `base.group_public`, `base.group_portal`, `base.group_user`, `base.group_partner_manager` | yes | — | — | — |
| `base.group_system` | yes | yes | yes | yes |

**Everybody reads countries; only a settings administrator writes them.** `res.country.state` is different — there
`base.group_partner_manager` has all four rights (bundle 5 will want that). `res.country.group` is readable by
everyone and written by `group_system`.

## The records — 251 countries, 18 Sep 2026

| | |
|---|---|
| Count | **251** |
| With a VAT label | **54** (AE TRN · AR CUIT · AT USt · AU ABN · BE/BG/CY/CZ/DE/DK/EE/ES/FI/FR/GB/GR/HR/HU/IE/IT/LT/LU/LV/MT/NL/PF/PL/PT/RO/SE/SI/SK VAT · CA GST/HST number · CL RUT · CO NIT · DO RNC · EC RUC · GT NIT · HK BRN · HN RTN · ID NPWP/NIK · IN GSTIN · MX RFC · MZ NUIT · NZ GST · PA RUC · PE RUC · PK NTN · SG GST No. · UG TIN · US TIN · UY RUT · UZ TIN · ZM TPIN) |
| State required | **15** |
| ZIP required | **241** — ten do not require one |
| Calling codes | sum 124 769; Malaysia 60 |
| Malaysia (id 157) | name *Malaysia*, code *MY*, calling code *60*, no VAT label, ZIP required, state not required, currency MYR, its own address layout with `%(state_name)s` |
| States | **2 102** in all, **16** for Malaysia — the `res.country.state` model, bundle 5 |

Every contact on the tenant is in Malaysia, and so is the company (*casimir*).

## Where other models point here

| Model | Field | What it does |
|---|---|---|
| `res.partner` | `country_id` many2one | On the address block, placeholder "Country", `options='{"no_open": True, "no_create": True}'` — **the picker neither creates a country nor opens one**. In the list it is an optional column, shown by default and read-only |
| `res.partner` | `country_code` related `country_id.code` | Read by the phone formatting, the VAT check and the localisations |
| `res.partner` | `_onchange_country_id` | Setting a country **clears the State** when the state belongs to another country |
| `res.partner` | `_onchange_state` | Setting a state **sets the Country** to that state's country |
| `res.partner` | `_display_address` | Formats the address with the country's `address_format` and `name_position` |
| `res.country.state` | `country_id` many2one, required | Bundle 5 |
| `res.company` | `country_id` | The company's own country, which drives the fiscal country codes below |
| `account.tax` | `country_id` **required** | Bundle 6 — a tax belongs to a country |
| `account.payment.term`, `uom.uom` | `fiscal_country_codes` | Computed from the company's country; both are invisible on their forms |
| `payment` module | two computed booleans on the country | Whether Stripe and Mercado Pago serve it |

## 19.0 and 19.4

Three VAT labels differ between this repo's 19.0 base data and the tenant, and the tenant wins: **HK** gains
*BRN*, **US** gains *TIN*, and **ID** is *NPWP/NIK* where 19.0 has *NPWP*. Everything else — all 251 names, codes,
calling codes, and the state and ZIP switches — is identical. The tenant also carries the two `payment` module
booleans, which 19.0's base module does not define.
