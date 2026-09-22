# 19 · Incoterms — requirements

| | |
|---|---|
| Odoo model | `account.incoterms` — `addons/account/models/account_incoterms.py` |
| Odoo menu | Invoicing › Configuration › Invoicing › **Incoterms** (action `action_incoterms_tree`) — **developer mode only** (`groups="base.group_no_one"`) |
| Bundle | **Incoterms**, `binc`, 1 worksheet, 1.1 h — ground-up build page |
| Source | the 19.0 source only. casimir.odoo.com expired on 22 Sep 2026, and no extract of this model was taken |
| Status | **Requirements.** Nothing built |
| Date | 22 Sep 2026 |

---

## 1 · What it is

The eleven ICC trade terms — FOB, CIF, DDP and the rest — which say who pays for and carries the risk of each
leg of an international shipment. A tiny reference table: a code and a name. Other documents point at it;
nothing about it computes.

**Odoo ships all eleven as data** (`addons/account/data/account_incoterms_data.xml`), so this is the one bundle
whose seed does not need the tenant.

## 2 · Fields

| # | Field | Odoo | Type | Required | Default | Notes |
|---|---|---|---|---|---|---|
| 1 | **Display Name** | `display_name` | Concatenation, **title** | — | — | `[FOB] FREE ON BOARD` — Odoo's `_compute_display_name`: `[code] name`. What every picker shows. Read-only and off the create form (`100`), the pattern 04's Display Name and 08's Complete Name already use |
| 2 | Name | `name` | Text | **yes** | — | Odoo's help: "Incoterms are series of sales terms. They are used to divide transaction costs and responsibilities between buyer and seller and reflect state-of-the-art transportation practices." |
| 3 | Code | `code` | Text | **yes** | — | `size=3`: at most three characters. Help: "Incoterm Standard Code". **Not unique in Odoo** — no constraint, so none here |
| 4 | Active | `active` | Checkbox | — | ticked | hidden; Archive / Unarchive drive it. Help: "By unchecking the active field, you may hide an INCOTERM you will not use." |

**Code's three-character limit** is a real rule, not a display width. Build it as a validation rule on Code's
length, with a message in Odoo's spirit ("An Incoterm code has at most three characters."). Odoo raises it as a
database field-size error, which has no user-facing wording of its own.

## 3 · Form, views, buttons

**Form** — Name, Code. Odoo puts Name first. An *Archived* ribbon shows on an archived record.

**List** — Code, Name; Active hidden. Odoo's list is `editable="bottom"`, so rows are edited in place. No
`_order`, so records come back in creation order — which, seeded, is Odoo's own order, EXW to DDP.

**Views** — **All** (Active only) and **Archived**, the house pattern.

**Buttons** — **Archive** and **Unarchive**, as every other worksheet with an Active field carries. Odoo offers
archive here: the form includes `active`, and the search view has an *Archived* filter. Contrast Headers/Footers,
where Odoo surfaced no archive action and none was built.

**Rules** — the one above, on Code's length.

## 4 · Seed — Odoo's own eleven, verbatim

Names in Odoo's own capitals. Seeded in this order, so the list reads as Odoo's does.

| Code | Name |
|---|---|
| EXW | EX WORKS |
| FCA | FREE CARRIER |
| FAS | FREE ALONGSIDE SHIP |
| FOB | FREE ON BOARD |
| CFR | COST AND FREIGHT |
| CIF | COST, INSURANCE AND FREIGHT |
| CPT | CARRIAGE PAID TO |
| CIP | CARRIAGE AND INSURANCE PAID TO |
| DPU | DELIVERED AT PLACE UNLOADED |
| DAP | DELIVERED AT PLACE |
| DDP | DELIVERED DUTY PAID |

Active explicitly ticked on every one (BUILDING.md: an API-written record must set Active or it appears in
neither view).

## 5 · Where it is used — wiring, a separate later step

The worksheet stands alone. These links touch forms the owner edits by hand, so each is its own
version-pinned save, after the worksheet exists.

| Worksheet | Field | Odoo | State today |
|---|---|---|---|
| **Orders** | **Incoterm** — Relation → Incoterms, single | `sale.order.incoterm` (from `sale_stock`) | missing. **Incoterm Location** already stands alone in *Other Info › Shipping*; this gives it its pair, beside it |
| **Invoices** | **Incoterm** — Relation → Incoterms, single | `account.move.invoice_incoterm_id` | missing |
| **Invoices** | **Incoterm Location** — Text | `account.move.incoterm_location` | missing |

Help text for each relation, Odoo's: "International Commercial Terms are a series of predefined commercial terms
used in international transactions."

## 6 · Not built now

| What | Why |
|---|---|
| The company default Incoterm, `res.company.incoterm_id` | no company table; Invoices' incoterm defaults from it in Odoo. Revisit with a company-settings table |
| Carrying the order's Incoterm onto its invoice | needs the order → invoice link, not built |
| Developer-mode-only visibility | HAP has no developer mode. The worksheet is visible; restrict it by role later if it should be admin-only |
| Code uniqueness | Odoo does not enforce it either |
