# 19 · Incoterms — requirements

| | |
|---|---|
| Odoo model | `account.incoterms` — `addons/account/models/account_incoterms.py` |
| Odoo menu | Invoicing › Configuration › Invoicing › **Incoterms** (action `action_incoterms_tree`) — **developer mode only** (`groups="base.group_no_one"`) |
| Bundle | **Incoterms**, `binc`, 1 worksheet, 1.1 h — ground-up build page |
| Source | the 19.0 source only. casimir.odoo.com expired on 22 Sep 2026, and no extract of this model was taken |
| Status | **Built and self-checked 22 Sep 2026** (`build/incoterms.py`), not yet UI-tested. **Wiring (§5) built the same day** (§8): Incoterm on Orders and Invoices, Incoterm Location on Invoices, the alias on Orders' own Incoterm Location — the new controls parked at row 9999 for the owner to place |
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

---

## 7 · Built — 22 Sep 2026

`nocoly/build/incoterms.py`, steps `create → fields → rules → views → buttons → roles → seed`, then `check` and
`selfcheck`. Every step reads live state first; a second `all` run saved nothing (proved: every step printed
"already as specified" / "not re-created" / "nothing written"). Every full control save was pinned to the version it
read. Worksheet `6ab28ec1e43d174ab3cd760a`, alias `account_incoterms`, icon `sys_7_1_truck`.

**Sidebar.** Menu group **Invoicing**, after Payment Terms and its hidden lines: Chart of Accounts · Taxes ·
Journals · Payment Terms · (Payment Term Lines, hidden) · **Incoterms** · Invoices · Invoice Lines — Odoo's
Configuration › Invoicing lists Payment Terms (sequence 10) then Incoterms (20). Countries, Payment Terms and Taxes
all sit flat in their app's group, not in a Configuration sub-group, so this does the same. Odoo shows the menu in
developer mode only; HAP has none, so it is visible (§6).

### Controls

| Control | Type | Alias | Permission | Notes |
|---|---|---|---|---|
| Name | Text | `name` | `111`, required | (0, 0, 6). Description: Odoo's help |
| Code | Text | `code` | `111`, required | (0, 1, 6). Description: "The standard code of the term, at most three characters, e.g. FOB." |
| Display Name | Function formula (53), text, **title** | `display_name` | `100` | (1, 0, 6). `IF(ISBLANK(Code),TRIM(Name),CONCAT("[",TRIM(Code),"] ",TRIM(Name)))` — 04's expression |
| Active | Checkbox | `active` | `011` hidden | (2, 0, 6). Default ticked (form only). Archive / Unarchive drive it |
| Code length | Function formula (53), **number** | `code_length` | `011` hidden | (2, 1, 6). Not an Odoo field — what the rule reads. No description (a helper) |

**Code length has no LEN().** HAP's function formula has no `LEN()`: a text or a number formula over it computed
empty on all eleven records, while `MID()` is there and counts from 1 (probed on the seeded records, 22 Sep). So the
helper asks each position of the trimmed code in turn whether it holds a character, and counts up to four — 4 means
"four or more", which is all the rule needs.

### Rule

**Code has at most three characters** (`6ab28f04bd43f55762240042`) — validation, check type 1 (form and server),
hint type 0 (while typing and on submit): *Code is not empty* **and** *Code length > 3* → error on Code, "An Incoterm
code has at most three characters." Stored exactly as sent (read back).

**It holds in the form only.** `selfcheck` updated TEST Incoterm's Code to `TSTX` through `record update` and the
server **accepted** it (Code length then read 4), although Code is a condition field and the rule is check type 1.
The server evaluates the rule before it recomputes the formula, it seems; either way an API or import write is not
stopped. The seed checks the length itself.

### Views

| View | Filter | Columns | Sort |
|---|---|---|---|
| **All** (opens first) `6ab28ec1e43d174ab3cd760e` | Active is ticked | Code · Name | Created ↑ — no `_order`, so creation order, which is Odoo's EXW → DDP |
| **Archived** `6ab28f2c805aef7032e32833` | Active is not ticked | Code · Name | Created ↑ |

### Buttons and workflows

| Button | Condition | Batch | Confirmation | Workflow (one update step, published) |
|---|---|---|---|---|
| Archive `6ab28f70805aef7032e32838` | Active is ticked | yes | "Are you sure that you want to archive this record?" (Archive / Cancel) | `6ab28f71a2c872a5c13e59cb` — *Archive the Incoterm*: Active ← 0 on the pressed record |
| Unarchive `6ab28f73e43d174ab3cd7627` | Active is not ticked | yes | none | `6ab28f73789584ded3432c2d` — *Unarchive the Incoterm*: Active ← 1 |

Both workflows read back enabled and published (`publishStatus` 2), trigger → the one step, the step writing
Active on the trigger record. `selfcheck` ran both on TEST Incoterm with `workflow trigger`: Archive moved it from
All to Archived, Unarchive back.

### Roles

`roles.py` gained a read-only `plan` step (what `create` would write, role by role). Before Incoterms and Contact
Tags joined its table, `plan` read **nothing to write** for all four roles; after, it listed only these two
worksheets, so `create` was run. Incoterms: **Accounting Administrator full; Accountant, Invoicing and Accounting
Read-only view** — Odoo's `ir.model.access.csv` writes `account.incoterms` from `account.group_account_manager`
alone and reads it to `base.group_user`, the shape of Payment Terms. `roles.py check` passes. The five stock roles
keep HAP's defaults, as for every worksheet.

### Seed — Odoo's eleven

Created in Odoo's order, one per second, each with Name, Code and **Active ticked explicitly**, matched by Code on a
re-run. Read back through **both** paths — `record get` and the `common.records` listing — Name, Code, Display Name,
Active and Code length agree on all eleven (the listing *did* return the two hidden controls here; these records were
created after the controls existed).

| Code | Name | Display Name | rowid |
|---|---|---|---|
| EXW | EX WORKS | [EXW] EX WORKS | `97bf7e4f-1e0b-4b72-b71a-28e83241f4b8` |
| FCA | FREE CARRIER | [FCA] FREE CARRIER | `ec6693f1-190f-4570-a12c-68c3864bce65` |
| FAS | FREE ALONGSIDE SHIP | [FAS] FREE ALONGSIDE SHIP | `45ad138c-c82a-4a4f-b308-19def3847eb6` |
| FOB | FREE ON BOARD | [FOB] FREE ON BOARD | `9a309eda-4d2a-4c5e-b965-7c96b5967ede` |
| CFR | COST AND FREIGHT | [CFR] COST AND FREIGHT | `28f0ff53-aa97-4880-b2a4-3095af488825` |
| CIF | COST, INSURANCE AND FREIGHT | [CIF] COST, INSURANCE AND FREIGHT | `55b945e7-e273-4a60-ab02-7df724492414` |
| CPT | CARRIAGE PAID TO | [CPT] CARRIAGE PAID TO | `da843f69-045d-4ce0-bd33-5d2fb1be7c09` |
| CIP | CARRIAGE AND INSURANCE PAID TO | [CIP] CARRIAGE AND INSURANCE PAID TO | `eea04d73-f7d4-4308-a915-19677329a160` |
| DPU | DELIVERED AT PLACE UNLOADED | [DPU] DELIVERED AT PLACE UNLOADED | `41a518b0-a12c-44db-ae09-bd3761ffc926` |
| DAP | DELIVERED AT PLACE | [DAP] DELIVERED AT PLACE | `477a9041-4d9e-4fd0-9242-6c268ebf5cee` |
| DDP | DELIVERED DUTY PAID | [DDP] DELIVERED DUTY PAID | `745605c7-7ee6-4d1a-b392-0b092051e579` |

**TEST Incoterm** (`9028ae01-b6dc-4cd5-8cd7-329789e53707`, code TST) is `selfcheck`'s record, left **archived** —
it shows only in Archived. Nothing was deleted.

### Differences from Odoo

| Odoo | Here | Why |
|---|---|---|
| The *Archived* ribbon on an archived record | none — the Archived view and the Unarchive button say it | HAP has no ribbon widget |
| `size=3` enforced by the database on every write | a validation rule, form only; the seed checks the length | no filter measures length, and the server did not refuse an API write (above) |
| The list edits rows in place (`editable="bottom"`) | HAP's own table editing | nothing to set |
| Developer-mode-only menu | visible to everyone the roles let in | HAP has no developer mode (§6) |
| Name is translatable | one language | as everywhere in this app |

## 8 · Wiring — built 22 Sep 2026

`orders.py incoterm` and `invoices.py incoterm`, each with a `selfincoterm` and an extended `check` (16-orders.md §12,
06-invoices.md *Incoterm*). Every new control was **appended** (`C.append_controls`, the server minting the id), and
the append proved every existing control unchanged and **Incoterms untouched** — the Relations are one-way. A second
run of each step saved nothing.

| Worksheet | Control | Type | Alias | Permission | Picker filter | Intended place |
|---|---|---|---|---|---|---|
| **Orders** | **Incoterm** `6ab29e24e43d174ab3cd7675` | Relation → Incoterms, single, one-way, dropdown | `incoterm` | `111` | Active is ticked | *Other Info* tab (stored), **row 9999** — intent: its own full-width row directly under the *Shipping* divider (row 22), above Incoterm Location, which moves down one |
| **Orders** | **Incoterm Location** `6ab0c528e54d2a34fa4e8124` — the owner's | Text | `incoterm_location` — **given in one version-pinned save** | `""` as the owner left it | — | unchanged (row 23) |
| **Invoices** | **Incoterm** `6ab29feae54d2a34faaa991a` | Relation → Incoterms, single, one-way, dropdown | `invoice_incoterm_id` | `111` | Active is ticked | *Other Info* tab (stored), **row 9999** — intent (19, 0, 6): the first row under the *Accounting* divider |
| **Invoices** | **Incoterm Location** `6ab29feae54d2a34faaa991c` | Text | `incoterm_location` | `111` | — | *Other Info*, row 9999 — intent (19, 1, 6), beside Incoterm |

- The picker shows the Incoterm's **Display Name**, "[FOB] FREE ON BOARD" — the Incoterms title; `check` confirms it.
- Both Incoterms carry Odoo's help as their description: "International Commercial Terms are a series of predefined
  commercial terms used in international transactions." Incoterm Location has none (Odoo gives it none).
- Orders' Incoterm Location was **not** duplicated: the step stops if the worksheet carries anything but the owner's
  one Text control under that name and id. The pinned save's signature diff named that control alone, of 45.
- **Receipts** — `invoices.py` rule **Incoterm is not offered on a receipt** (`6ab29fefbd43f557622400f7`): hide
  Incoterm and Incoterm Location while Type is Sales Receipt or Purchase Receipt — Odoo's
  `invisible="move_type in ('out_receipt', 'in_receipt')"` on both.
- **No read-only rule.** Odoo locks neither field (19.0 source): the sale order form gives `incoterm` and
  `incoterm_location` no `readonly` (sale_stock/views/sale_order_views.xml:27-28) and `sale.order.write` refuses only
  a pricelist change on a confirmed order; the invoice form gives neither a `readonly` (account_move_views.xml:1541-1542)
  and `account.move.write`'s posted-move list (`unmodifiable_fields`) does not name them. So Orders' *A confirmed or
  cancelled order…* and *A locked or cancelled order…* and Invoices' *A posted or cancelled document is closed for
  editing* were **not** extended. The tenant extracts carry no read-only condition for them either.
- Odoo's `no_create` on the order's picker is the Roles' job: every business role only views Incoterms.

**Self-checks** — `orders.py selfincoterm` on *TEST Sign & Accept, CLI run* (`8aa92a30-…`) set FOB and "TEST Port
Klang"; `invoices.py selfincoterm` on TEST-SEQ-1 (`65469834-…`) set CIF and "TEST Port of Singapore". Both read back
the Incoterm (rowid and title) and the location **through `record get` and the listing alike**, and both records were
put back empty and read back empty both ways. No workflow on either worksheet fires on these fields (every
worksheet-event trigger there is narrowed to other fields).

Still not built (§6): the company default Incoterm, Odoo's placeholder naming it ("Define a default in the
settings"), and carrying the order's Incoterm and location onto its invoice.

## 9 · For the browser

Nothing here was seen in a browser; implementation agents have none.

1. **Sidebar**: Invoicing shows Incoterms after Payment Terms (Payment Term Lines stays hidden), with the truck icon.
2. **All** lists the eleven, EXW first and DDP last, columns Code · Name; **Archived** shows TEST Incoterm only.
3. **The form**: Name | Code on one row, Display Name read-only under them; Active and Code length invisible; the
   title reads "[FOB] FREE ON BOARD". On **+ Record**, Display Name is absent and Active defaults ticked (save one and
   check it lands in All).
4. **The rule**: type a fourth character into Code — "An Incoterm code has at most three characters." shows under
   Code while typing, and the save is refused; back to three characters, it clears. **This is the one thing nothing
   else proves**: the rule reads a hidden formula, and only the browser shows whether the form recomputes it live.
   If it does not fire, fall back to Countries' pattern — `checkrange` 1..3 on Code — and say so.
5. **Archive** on an active record asks for confirmation and moves it to Archived; **Unarchive** there brings it
   back; each button is hidden (or greyed in the pop-up) when it does not apply. Batch: select two in All → Archive.
6. **As Invoicing** (Select Role): Incoterms is view-only — no + Record, the form read-only. **Look at whether Archive
   is still offered**: a button's workflow writes whatever the presser's role, so if a view-only role can press it,
   it archives — record what the page does (no earlier worksheet has settled this). **As Accounting
   Administrator**: full.
7. **Orders** (a quotation) › Other Info: **Incoterm** sits at the foot of the tab until the owner places it (intent:
   its own row under *Shipping*, above Incoterm Location). Its picker lists the eleven as "[EXW] EX WORKS" … and
   **not** the archived TEST Incoterm. Pick one, save, reopen. It stays editable on a confirmed, locked and cancelled
   order, as in Odoo. **As Invoicing**, the picker should offer no way to create an Incoterm (the role only views
   them) — record what the page does. Incoterm is also a column of the owner's **All** view, which shows every field.
8. **Invoices** › Other Info: Incoterm and Incoterm Location at the foot of the tab until placed (intent: the first
   row under *Accounting*, side by side). Both **disappear when Type is Sales Receipt or Purchase Receipt** and come
   back on any other type. Both stay editable on a posted invoice.
