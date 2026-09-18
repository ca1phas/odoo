# res.country.state — as on casimir.odoo.com (Odoo saas~19.4+e)

Read-only extract, 18 Sep 2026: the model and its views from the Odoo 19.0 source in this repo
(`odoo/addons/base/models/res_country.py`, `res_country_views.xml`, `res_partner.py`,
`odoo/addons/base/security/ir.model.access.csv`), and from the tenant: the *Fed. States* screen, the counts and
contents of all 2 102 states, the states of Malaysia on the country form, `name_search` under three contexts, and
the state of every contact.

The 2 102 records are saved as `nocoly/data/casimir-states.json`. As with the countries, they were **rebuilt from
this repo's `odoo/addons/base/data/res.country.state.csv` and then reconciled with the tenant by digest** rather
than copied through the browser: each country's states were reduced to sorted `code|name` lines and hashed, and
only the countries whose digest differed were read out of the tenant in full. **Ten did** — six the checkout does
not have at all (Bahrain 4, Cuba 16, Kuwait 6, Lebanon 8, Oman 11, Qatar 8) and four whose contents differ (Egypt
27 where the checkout has 29, Pakistan 7 with different codes, **Saudi Arabia 13 where the checkout has 93**,
Türkiye 81 with different codes). After the swap the two sides agree exactly: **2 102 states, 74 countries, every
country's digest identical**.

Menu: **Contacts ▸ Configuration ▸ Localization ▸ Fed. States** (window action `base.action_country_state`, id 60).

## Fields

| Field | Label | Type | Req. | Notes |
|---|---|---|---|---|
| `country_id` | Country | many2one → `res.country` S | **yes** | indexed |
| `name` | State Name | char S | **yes** | help: "Administrative divisions of a country. E.g. Fed. State, Department, Canton" |
| `code` | State Code | char S | **yes** | help: "The state code." |

`_order = 'code, id'` — **the list is ordered by code across every country**, so it reads Aveiro (PT) 01,
Архангай (MN) 01, Amazonas (PE) 01, Azuay (EC) 01, Beja (PT) 02 … `_rec_names_search = ['name', 'code']`.

**`display_name` is `"<name> (<country code>)"`** — *Selangor (MY)* — computed from `country_id`. With
`formatted_display_name` in the context it becomes `"<name> \t --<code>--"`.

## Constraint

| | Message |
|---|---|
| `unique(country_id, code)` | *The code of the state must be unique by country!* |

The same code may exist in many countries — 01 belongs to Portugal, Mongolia, Peru and Ecuador at once.

## name_search — three behaviours, checked on the tenant

| Call | Result |
|---|---|
| `name_search('Sel')` | Every country's matches, each as *Name (CC)*: Basel-Landschaft (CH), Basel-Stadt (CH), Kalimantan Selatan (ID), **Selangor (MY)**, Overijssel (NL), … |
| with `country_id` in the context | **Selangor (MY)** alone |
| with `default_country_id` in the context | **not narrowed** — the whole list |

The code is searched first, with `=like`, and those come back ahead of the name matches. `_search_display_name`
also parses *"Name (Country)"* and narrows on the context's `country_id`.

**The partner form passes `default_country_id`, not `country_id`** — so on a contact **the State picker offers
every state in the world**, labelled with its country code, and picking one sets the Country (below).

## Views

- **List** `base.view_country_state_tree`: `<list editable="bottom">` — **State Name · State Code · Country**
  (`options="{'no_create': True, 'no_open': True}"` on the country). Seen on the tenant: 2 102 rows, a **New**
  button, 80 to a page.
- **Form** `base.view_country_state_form`: one group — State Name · State Code · Country (`no_open`, `no_create`).
- **Search** `base.view_country_state_search`: fields Name and Country, and one **group-by Country**.
- The action's empty-list help: *"Create a State — Federal States belong to countries and are part of your
  contacts' addresses."*

## Access (`odoo/addons/base/security/ir.model.access.csv`)

| Group | R | W | C | D |
|---|---|---|---|---|
| `base.group_public`, `base.group_portal`, `base.group_user` | yes | — | — | — |
| `base.group_partner_manager` | yes | yes | yes | yes |

**Unlike `res.country`, a state does not need a settings administrator** — any contact manager may create one, and
Odoo's own list carries a *New* button where the countries' list does not.

## Where other models point here

| Model | Field | What it does |
|---|---|---|
| `res.partner` | `state_id` many2one | On the address block, placeholder "State", `options="{'no_open': True, 'no_quick_create': True}"`, `context="{'default_country_id': country_id}"` — so a state created from there starts in the contact's country |
| `res.partner` | `_onchange_state` | **Setting a state sets the Country** to that state's country |
| `res.partner` | `_onchange_country_id` | **Changing the country clears a State** that belongs to another country |
| `res.partner` | `_display_address` | `%(state_name)s` and `%(state_code)s` in a country's address layout — Malaysia's uses `state_name` |
| `res.country` | `state_ids` one2many | The editable list at the foot of the country form: State Name · State Code |
| `account.tax`, `account.fiscal.position`, the localisations | `state_ids` etc. | Not in Phase 1 |

## The records — 2 102 states in 74 countries, 18 Sep 2026

| | |
|---|---|
| Total | **2 102** |
| Countries with states | **74** of 251 |
| Largest | Great Britain 119 · Latvia 119 · Italy 111 · Philippines 83 · Russia 81 · Türkiye 81 · Azerbaijan 77 · Thailand 77 |
| **Malaysia** | **16**, codes MY-01 … MY-16 in this order: Johor · Kedah · Kelantan · Melaka · Negeri Sembilan · Pahang · Pulau Pinang · Perak · Perlis · Selangor · Terengganu · Sabah · Sarawak · Kuala Lumpur · Labuan · Putrajaya |
| On the tenant's contacts | Selangor (×4), Johor (×2), Kuala Lumpur, Pulau Pinang, Sarawak — every contact is Malaysian |
