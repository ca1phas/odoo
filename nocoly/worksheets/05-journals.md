# 05 · Journals

| | |
|---|---|
| Nocoly app | ERP Master · menu group **Invoicing** |
| Worksheet | Journals |
| Odoo model | `account.journal` |
| Reference | **casimir.odoo.com — Odoo saas~19.4+e**: fields, form, list, kanban, search, defaults, `_order`, the SQL constraint and all 7 journals, extracted read-only to `nocoly/reference/odoo-19.4/account.journal.md`. Behaviour the tenant cannot show — the code and name placeholder computed from Type, the archive check — is read from the Odoo 19.0 source in this repo, `addons/account/models/account_journal.py`. Teh Li Wei's first hand-off read his own tenant, ohyes.odoo.com; the owner settled casimir as the reference on 15 Sep 2026 |
| Phase | 1 — core worksheet 5 of 7 |
| Status | First built by **Teh Li Wei** on 15 Sep 2026 (worksheet, 6 controls, 2 views, no records). Gaps against the casimir reference closed, seeded and self-checked with the hap CLI on 16 Sep 2026 · CLI self-checks pass · **UI-tested on 16 Sep 2026: 18 of 18 pass**, 6 differences noted · ready for review |

A journal is the book an accounting entry is written in: customer invoices go in a Sales journal, vendor bills in a
Purchase one, payments in Bank, Cash or Credit Card, and everything else in Miscellaneous. Type drives the whole
form — what is shown, what is required — and Sequence Prefix becomes the prefix of every entry's number, which is
why Odoo keeps it short and unique. 06 Invoices will point at this worksheet.

## 1 · Requirements

### Fields

Labels are Odoo 19.4's; aliases are Odoo's field names on `account.journal`. Descriptions are Odoo's own `help`,
verbatim. "Hidden" means not on the form but used by the views and the buttons.

| # | Field | Odoo field | Nocoly type | Required | Default | Notes |
|---|---|---|---|---|---|---|
| 1 | Journal Name | `name` | Text · **title field** | yes | — | Placeholder "e.g. Customer Invoices". Odoo has no help on it; the first build's invented hint ("Enter journal name") and description are gone |
| 2 | Type | `type` | Single Select, dropdown | yes | — | **Sales · Purchase · Cash · Bank · Credit Card · Miscellaneous** — Odoo's `sale`, `purchase`, `cash`, `bank`, `credit`, `general`, in that order. Odoo's help kept as the description; no placeholder. Quick filter on both views |
| 3 | Sequence Prefix | `code` | Text, **at most 5 characters**, **No duplicates** | yes | — | Placeholder "e.g. INV"; Odoo's help. Odoo's `Char(size=5)` and the SQL constraint `account_journal_code_company_uniq` ("Journal codes must be unique per company"), which is per company and so per app copy here. The length limit is a form check only — see §2 |
| 4 | Sequence | `sequence` | Number, 0 decimals | — | 10 | Odoo's help plus the note that a HAP table has no drag handle, so a journal is moved up or down the list by changing this number. Visible and editable, where Odoo hides it behind the list's drag handle. Both views sort on it first |
| 5 | Dedicated Credit Note Sequence | `refund_sequence` | Checkbox | — | unchecked | Odoo's help. Shown for Sales and Purchase only |
| 6 | Dedicated Payment Sequence | `payment_sequence` | Checkbox | — | unchecked | Odoo's help. Shown for Bank, Cash and Credit Card only |
| 7 | Communication Type | `invoice_reference_type` | Single Select, dropdown | by rule | Based on Invoice | **Based on Customer · Based on Invoice**. Odoo's help. Required on Odoo's model, but here a rule requires it, because Odoo only ever shows it on a Sales journal and a hidden required field can never be filled |
| 8 | Communication Standard | `invoice_reference_model` | Single Select, dropdown | by rule | Full Reference (INV/2024/00001) | **Full Reference (INV/2024/00001) · European (RF83INV202400001) · Numbers only (202400001)** — Odoo's `odoo`, `euro`, `number`, labelled with the examples the tenant shows. Required by the same rule |
| 9 | Active | `active` | Checkbox | — | checked | **Hidden.** Odoo's help. Set by Archive / Unarchive; the two views filter on it |

Type, Communication Type and Communication Standard keep the option keys of the first build, and every field keeps
its control id and alias — records already written against them stay valid.

### Form layout

| Odoo 19.4 (`view_account_journal_form`) | Nocoly |
|---|---|
| Ribbon "Archived" when not active | — (HAP shows archived records only in the Archived view) |
| Journal Name (h1, required while Type is empty) | Journal Name |
| Group: Type · Sequence Prefix \| Ledger | Type \| Sequence Prefix |
| — (Sequence is the list's drag handle, not on the form) | Sequence |
| Tab *Journal Entries*: Dedicated Credit Note Sequence (Sales, Purchase) · Dedicated Payment Sequence (Bank, Cash, Credit Card) · Invoice report · bank fields | Dedicated Credit Note Sequence \| Dedicated Payment Sequence, the same two rules |
| Tabs *Incoming / Outgoing Payments* | — (Not built now) |
| Tab *Advanced Settings* › group Payment Communications, Sales only: Communication Type · Communication Standard | Communication Type \| Communication Standard, the same rule |
| Chatter | HAP's own discussion |

**One flat form, no tabs.** Odoo's two notebook pages would hold one and two fields here until the deferred
settings arrive — self-billing, the email alias, the bank fields and the payment method lines are all Not built
now — so the nine fields sit on HAP's 12-column grid in Odoo's order, and Type governs what is visible through the
rules below rather than through tab visibility. Add the tabs when the pages have something to hold.

### Rules

All four are interaction rules on Type. A HAP rule applies its action while its condition holds and the opposite
when it does not, so each of these shows its fields for the listed types and hides them for every other type — and
for a new record whose Type is still empty, which is what Odoo's `invisible` does too.

| Rule | When | Effect | Odoo source |
|---|---|---|---|
| Payment Communications only for Sales | Type is Sales | show **Communication Type** and **Communication Standard** | `<group string="Payment Communications" invisible="type != 'sale'">` |
| Payment Communications are required for Sales | Type is Sales | **require** both | `required=True` on the model, reachable only on a Sales journal |
| Dedicated Credit Note Sequence only for Sales and Purchase | Type is Sales or Purchase | show **Dedicated Credit Note Sequence** | `<field name="refund_sequence" invisible="type not in ['sale', 'purchase']"/>` |
| Dedicated Payment Sequence only for Bank, Cash and Credit Card | Type is Bank, Cash or Credit Card | show **Dedicated Payment Sequence** | `<field name="payment_sequence" invisible="type not in ('bank', 'cash', 'credit')"/>` |

Nothing is validated. Odoo's two guards on this model are the SQL uniqueness of the code, which is the field's own
**No duplicates**, and the refusal to archive a journal that has draft entries, which needs 06 Invoices.

### Buttons (Odoo ⚙ Actions)

| Button | Shown when | Does | Confirmation |
|---|---|---|---|
| Archive | Active is checked | Active → unchecked | "Are you sure that you want to archive this record?" · Archive / Cancel |
| Unarchive | Active is unchecked | Active → checked | none |

Exactly as on Contacts, Units & Packagings, Products and Product Variants: a one-step workflow that writes Active
on the triggering record, and the button that does not apply is greyed out rather than hidden.

### Views

| View | Type | Shows | Odoo 19.4 |
|---|---|---|---|
| Journals | table — opens first | Active journals. Columns **Journal Name · Type · Sequence Prefix**, sorted **Sequence, then Type, then Sequence Prefix**, all ascending. Quick filter Type, several at a time | List view: drag handle · Journal Name · Type · Ledger (hidden) · Sequence Prefix · Default Account · Active (hidden). `_order` is `sequence, type, code` |
| Archived | table | Archived journals, the same columns, sort and quick filter | The *Archived* search filter |

Odoo's search filters Sales · Purchases · Liquidity · Miscellaneous become the one Type quick filter, which takes
several types at once — Liquidity is Cash + Bank + Credit Card. Default Account waits for Chart of Accounts.
Odoo's kanban (name and type only) is not reproduced; its second action, the Invoicing *Dashboard*, is a different
view of the same model and waits for the dashboard fields.

### Not built now, and why

| Odoo 19.4 field / feature | Why not now |
|---|---|
| Default Account, Suspense Account, Profit Account, Loss Account, Private Share Account (`default_account_id`, `suspense_account_id`, `profit_account_id`, `loss_account_id`, `non_deductible_account_id`) — and Odoo's Default Account list column | They point at `account.account`: the **Chart of Accounts** worksheet, not in Phase 1. A Text substitute would be the wrong model. The tenant's admin cannot even see them (Accounting groups) |
| Currency (`currency_id`) | Currencies bundle; one currency (MYR) per app copy for now |
| Payment method lines and available methods (`inbound_payment_method_line_ids`, `outbound_payment_method_line_ids`, `available_payment_method_ids`), tabs Incoming / Outgoing Payments | **Payments** bundle — each line is its own record pointing at a payment method and an account |
| Bank Account (`bank_account_id`), Account Number, BIC, Bank Name, Bank Feeds (`bank_statements_source`) and the `account_online_synchronization` fields | Bank accounts are `res.partner.bank` records; feeds are a paid online service |
| Ledger (`journal_group_id`) | `account.journal.group`, its own table; the tenant has none, so Odoo hides the field |
| Secure Posted Entries with Hash (`restrict_mode_hash_table`) | Hashing only means something once entries exist, and Odoo refuses to change it on a journal that has them — **needs 06 Invoices** |
| Self Billing (`is_self_billing`) | Self-billing is an e-invoicing flow on vendor bills |
| Email Alias (`alias_*`) and Send Copy To (`incoming_einvoice_notification_email`) | Mail aliases are `mail.alias` records and need incoming mail; the notification address belongs with e-invoicing |
| Invoice report (`invoice_template_pdf_report_id`) | Report templates are `ir.actions.report` records; Odoo shows the field only when several exist |
| Show journal on dashboard (`show_on_dashboard`), Color Index (`color`), and everything the dashboard computes (`kanban_dashboard`, `entries_count`, `has_entries`, `has_sequence_holes`, …) | There is no Invoicing dashboard here; both fields exist only to arrange its cards |
| Company (`company_id`) | One company per app copy (Direction, 15 Sep) |
| Sequence override regex (`sequence_override_regex`) | It reshapes entry numbering, which 06 Invoices has to define first |
| Odoo computing an empty Sequence Prefix from Type (`_compute_code` → `_get_next_journal_default_code`, e.g. the second Sales journal becomes INV2) and an empty Journal Name from the placeholder ("Customer Invoices (1)") | Both are onchange-style computes with no HAP equivalent; here Sequence Prefix is required and the placeholder "e.g. Customer Invoices" tells the user what to type. A workflow could fill them later |
| "You cannot archive a journal containing draft journal entries" (`_check_auto_post_draft_entries`) | The check counts draft entries — **needs 06 Invoices**; add it to the Archive workflow then |
| Roles | Set once for the app at the end of Phase 1 |

### Records

The tenant's seven journals, seeded exactly as the extract lists them, all active, all with Communication Type
*Based on Invoice* and Communication Standard *Full Reference* (Odoo stores those defaults on every journal even
though the form shows them only for Sales):

| Journal Name | Type | Sequence Prefix | Sequence | Credit note seq. | Payment seq. |
|---|---|---|---|---|---|
| Sales | Sales | INV | 5 | ✓ | |
| Purchases | Purchase | BILL | 6 | ✓ | |
| Bank | Bank | BNK1 | 7 | | ✓ |
| Miscellaneous Operations | Miscellaneous | MISC | 9 | | |
| Cash Basis Taxes | Miscellaneous | CABA | 10 | | |
| Exchange Difference | Miscellaneous | EXCH | 10 | | |
| Tax Returns | Miscellaneous | TAX | 10 | | |

In that order, which is what both views show: Sequence, then Type, then Sequence Prefix. The tenant has no Cash and
no Credit Card journal, so those two types are exercised only by the rules. Two `TEST …` records are left for the
reviewer (§3).

## 2 · Build

Built by `nocoly/build/journals.py` — steps `layout → rules → views → buttons → seed`, or `all` for every one of
them followed by `check`. Each step reads the live worksheet first, refuses to run unless the profile reaches ERP
Master › Invoicing › Journals and the worksheet holds only the first build plus this script's own work, reads back
what it wrote, and is safe to re-run: a second `all` wrote nothing. Helpers: `check` reads controls, options,
defaults, rules, views and buttons back against the spec, `verify` compares every journal with the extract,
`selfcheck` runs the writes the worksheet must refuse and both buttons, `order` prints each view's records in the
view's own order, `journal "<Journal Name>"` a journal's stored values (hidden fields included), `untouched` the
other four worksheets' control count and digest, and `show` the control list. The profile comes from `$HAP_PROFILE`
and otherwise from hap-cli's active profile; nothing in `common.py` changed.

| Element | Built | Id |
|---|---|---|
| App | ERP Master | `6cb4d051-a33c-4bf9-b56f-5f47f0e85dc9` |
| Menu group | Invoicing — Journals, Invoices | `6aa8f3ecbf00c316381dbbe8` |
| Worksheet | Journals, alias `account_journal` | `6aa8f5191204328eb1af162a` |
| Controls | 9, no tabs | — |
| Kept from the first build | Journal Name · Sequence Prefix · Type · Communication Type · Communication Standard · Active | `6aa8f6c81204328eb1af1676` · `…1677` · `…1678` · `…1679` · `…167a` · `…167b` |
| Added | Sequence · Dedicated Credit Note Sequence · Dedicated Payment Sequence | `6aa9dabcbd43f55762c6f430` · `6aa9dabcbd43f55762c6f431` · `6aa9dabcbd43f55762c6f432` |
| Rules | Payment Communications only for Sales · Payment Communications are required for Sales · Dedicated Credit Note Sequence only for Sales and Purchase · Dedicated Payment Sequence only for Bank, Cash and Credit Card | `6aa9dae5e54d2a34fa4dfde2` · `6aa9dae67d58b0f44930e6ce` · `6aa9dae67d58b0f44930e6d0` · `6aa9dae7e43d174ab37498e9` |
| Views | Journals · Archived (both the first build's, re-sorted) | `6aa8f5191204328eb1af162e` · `6aa8f7074720c515252bf2c8` |
| Buttons | Archive · Unarchive | `6aa9db31805aef7032865005` · `6aa9db34e43d174ab37498ec` |
| Button workflows | Archive the journal · Unarchive the journal, one update step each, published | `6aa9db3116473257ad4c471e` · `6aa9db348e75db182e77e1e2` |
| Records | 7 journals of the extract, plus TEST Journal (TSTJ, active) and the archived TEST long prefix (Tf798) | — |

Every id is in `nocoly/build/ids.json` under "Journals: …" keys, the controls and rules in two new sections
(`controls`, `rules`); no existing key was renamed.

**History.** **Teh Li Wei built the worksheet on 15 Sep 2026** — the Invoicing menu group, the worksheet and its
alias, six of the nine controls with their ids and all eleven option keys, and the Journals and Archived views with
their Active filters and their Journal Name · Type · Sequence Prefix columns. He labelled the three Communication
Standard options with Odoo's examples after reading a live tenant, and at 17:27 he removed his Sequence field and
raised the Sequence Prefix limit to 7. That build is the base of everything here; the owner then asked us to finish
the worksheet against casimir. What changed on 16 Sep 2026, and why:

| Change | Why |
|---|---|
| **Sequence added back** (a new control id; the old one was deleted), visible and editable, default 10 | Odoo's `_order` is `sequence, type, code`: without the field neither view can reproduce the tenant's list order, and both views were left sorting on the deleted control's id |
| Sequence Prefix: maximum **5** characters, not 7; **No duplicates** switched on | Odoo declares `code = fields.Char(size=5)` and the SQL constraint `account_journal_code_company_uniq` |
| Dedicated Credit Note Sequence and Dedicated Payment Sequence added | Odoo shows both on the Journal Entries page; they decide whether credit notes and payments get their own numbering, which 06 Invoices needs |
| Communication Type and Communication Standard are **no longer required on the field**; a rule requires them for Sales | They are hidden for every other type, and a hidden required field can never be filled — the form could not be saved |
| Placeholders: "e.g. Customer Invoices" and "e.g. INV"; the invented ones ("Enter journal name", "Select a journal type", "Select a communication type", "Select a communication standard", "Enter up to 7 characters") cleared | Odoo's own placeholders are the two kept; the rest were invented in the first build |
| Descriptions are Odoo's `help`, verbatim, on Type, Sequence Prefix, Sequence, both dedicated sequences, both communication fields and Active | A reviewer can compare them with Odoo's tooltips. The first build's two invented descriptions are replaced |
| Four interaction rules, the two Archive / Unarchive buttons with their workflows, and the seven journals | The first build had none — 0 rules, 0 buttons, 0 records |
| Both views: sort Sequence → Type → Sequence Prefix, Type quick filter | Odoo's `_order` and its search filters. The views' ids, names, filters and columns are Teh Li Wei's, unchanged |

Nothing was deleted or renamed. Worksheet 06 Invoices (`6aa90facf363582dd37a62f7`) is Teh Li Wei's and was never
opened. The app log was checked before each write: every entry on 16 Sep is this build's own.

**Self-checks through the CLI** (`journals.py check`, `verify`, `selfcheck`, `order`, `untouched`; the TEST records
are listed in §3):

- **Configuration** — `check` reads back OK: 9 controls in their places with the right hints, help, required and
  hidden settings, Sequence Prefix unique with `max` 5, the six Type options and both communication option lists
  with the first build's keys, the defaults (Sequence 10, both checkboxes unchecked, Based on Invoice, Full
  Reference, Active checked), the four rules enabled with Type as their only condition, both views with their
  columns, three-level sort, Active filter and Type quick filter, in that order, and both buttons with their
  conditions and the Archive confirmation.
- **The seven journals** — `verify`: "7 in the extract; 0 missing or differing". `order` lists both views in the
  view's own order: Journals — Sales [INV, 5], Purchases [BILL, 6], Bank [BNK1, 7], Miscellaneous Operations
  [MISC, 9], Cash Basis Taxes [CABA, 10], Exchange Difference [EXCH, 10], Tax Returns [TAX, 10], TEST Journal
  [TSTJ, 99]; Archived — TEST long prefix [Tf798, 99]. That is Odoo's list order.
- **No duplicates holds on the API** — creating a journal with Sequence Prefix INV and setting TEST Journal's
  prefix to BILL were both refused, `resultCode 11` naming `6aa8f6c81204328eb1af1677` (Sequence Prefix).
- **The 5-character limit does not.** `record create` and `record update` both stored the 6-character prefix
  `TSTLNG`; the field's `checkrange` / `max` is a form-side check only. The created record was recoded `Tf798`
  and archived rather than deleted, and TEST Journal's prefix was restored to TSTJ. No HAP filter operator measures
  text length, so a validation rule cannot enforce it either — **the form's own check is test 11**, and any later
  import must check the length itself. Recorded in BUILDING.md.
- **Both buttons** — `hap workflow trigger` of Archive set TEST Journal's Active to unchecked and of Unarchive back
  to checked, each within a second. TEST Journal is left **active** for the reviewer.
- **Idempotent** — every step was run twice and `all` once more: the second runs added no control, rule, view,
  button or record, re-created no workflow ("already has steps; left as is"), and wrote no field ("layout already as
  specified; nothing saved").
- **The other worksheets are untouched.** Their controls were compared by id before and after every save, and the
  digests are the same at the end as at the start: Contacts 30 `9f7e59498c3081a1`, Units & Packagings 10
  `e57dc8775cd5038b`, Products 19 `a8f9911118fda7d7`, Product Variants 20 `6eba14458f20e2a6`. Their rules, buttons
  and views also read back unchanged (3 / 2 / 3 views, 3 / 2 / 2, 3 / 2 / 3 and 2 / 2 / 2).

The four rules, the placeholders, the descriptions and the quick filter are browser behaviour: HAP stores them as
configured and only the UI test can show them working.

### Found while building

- A text field's **maximum length is not enforced on API writes** (above). Its sibling setting **No duplicates
  is** — the two look alike in the field editor and behave differently.
- **Deleting a field leaves every view sorting on its id.** Journals and Archived still carried
  `sortCid`/`moreSort` pointing at the Sequence control removed on 15 Sep; nothing cleans that up, and the views had
  been sorting on a field that no longer existed.
- **A rule's action is reversed when its condition fails**, so show and hide are two ways of writing the same
  toggle — except while the driving field is empty. "Show when Type is Sales" keeps the field hidden on a new
  record whose Type has not been chosen; "hide when Type is not Sales" would depend on how the server compares an
  empty option. All four rules here are written in the positive form.
- A dropdown rule condition takes **several option keys in one `values` list** ("is any of"), and reads them back in
  the options' own order rather than the order they were written in.
- Teh Li Wei's Sequence Prefix carries `advancedSetting.hinttype` "1", which no other field in the app sets. It was
  left as it is — test 16 says where the placeholder appears.

## 3 · Test list

To run in the Nocoly UI, in Chrome, against
`~/.hap-venv/bin/python nocoly/build/journals.py journal "<Journal Name>"` / `order` / `check` from the repo root
for the stored values. Test records are named `TEST …`. Run on 16 Sep 2026: **18 of 18 pass**.

| # | Check | Steps | Expected | Result |
|---|---|---|---|---|
| 1 | Menu and views | Open ERP Master → menu group **Invoicing** → Journals | Invoicing lists Journals then Invoices. Journals opens on the **Journals** table; its view list is Journals · Archived | **Pass** — Invoicing lists Journals then Invoices; Journals opens on its table, views Journals · Archived |
| 2 | Table, columns and order | The Journals view | 8 rows, columns **Journal Name · Type · Sequence Prefix**, in this order: Sales [INV], Purchases [BILL], Bank [BNK1], Miscellaneous Operations [MISC], Cash Basis Taxes [CABA], Exchange Difference [EXCH], Tax Returns [TAX], TEST Journal [TSTJ]. No Sequence, Active or communication column | **Pass** — 8 rows in exactly that order, those three columns only |
| 3 | Archived view | Switch to Archived | 1 row: TEST long prefix [Tf798], Miscellaneous, same three columns | **Pass** — TEST long prefix [Tf798], Miscellaneous (TEST Sales joined it in test 13) |
| 4 | Type quick filter | Journals → the Type quick filter: pick Sales; then Cash + Bank + Credit Card together (Odoo's *Liquidity*); then Miscellaneous; clear | Sales → Sales. Liquidity → Bank only (the tenant has no Cash or Credit Card journal). Miscellaneous → Miscellaneous Operations, Cash Basis Taxes, Exchange Difference, Tax Returns, TEST Journal. Cleared → all 8 | **Pass** — Sales → Sales; Cash + Bank + Credit Card → Bank alone; Miscellaneous → the 5; cleared → 8 |
| 5 | A Sales journal's form | Open **Sales** | Journal Name Sales, Type Sales, Sequence Prefix INV, Sequence 5. **Dedicated Credit Note Sequence shown and ticked**; Dedicated Payment Sequence **not shown**. **Communication Type (Based on Invoice) and Communication Standard (Full Reference (INV/2024/00001)) shown**, both marked required. No Active field | **Pass** — every value as expected; Dedicated Credit Note Sequence ticked, no payment sequence, both communication fields shown and marked required, no Active |
| 6 | A Purchase journal's form | Open **Purchases** | Type Purchase, BILL, Sequence 6, Dedicated Credit Note Sequence shown and ticked; **no** Dedicated Payment Sequence and **no** communication fields | **Pass** |
| 7 | A Bank journal's form | Open **Bank** | Type Bank, BNK1, Sequence 7, **Dedicated Payment Sequence shown and ticked**; no Dedicated Credit Note Sequence, no communication fields | **Pass** |
| 8 | A Miscellaneous journal's form | Open **Miscellaneous Operations** | Type Miscellaneous, MISC, Sequence 9; **neither** checkbox and **neither** communication field is shown | **Pass** — only Journal Name, Type, Sequence Prefix and Sequence |
| 9 | A new record, and the defaults | Journals → + Record; look before choosing a Type; then pick Cash, then Credit Card, then Sales | With no Type: Journal Name, Type, Sequence Prefix and Sequence only — Sequence already **10**, both checkboxes and both communication fields hidden. Cash and Credit Card → Dedicated Payment Sequence appears, unticked. Sales → the two communication fields appear with **Based on Invoice** and **Full Reference (INV/2024/00001)**, and Dedicated Credit Note Sequence appears unticked. Close without saving | **Pass** — Sequence 10 before anything is chosen; Cash and Credit Card add the payment sequence unticked; Sales adds the credit note sequence and both communication fields with Based on Invoice and Full Reference (INV/2024/00001) |
| 10 | Required fields | On that new record: Submit with everything empty; then Journal Name "TEST Required", Type Miscellaneous, Sequence Prefix empty → Submit | Refused both times, Journal Name / Type / Sequence Prefix marked. Close without saving | **Pass** — "Please fill in Journal Name", "Please fill in Sequence Prefix" and "Please fill in the record correctly" |
| 11 | Sequence Prefix at most 5 characters | New record: Journal Name "TEST Long", Type Miscellaneous, Sequence Prefix `TSTLNG` (6 characters) → leave the field, then Submit | The form refuses the 6th character or shows a length error and will not save. (Through the API the same value **is** stored — §2.) Close without saving | **Pass** — "Please enter 1 to 5 characters" on Sequence Prefix, and Submit refused. Through the API the same value is stored (§2, difference 4) |
| 12 | Sequence Prefix No duplicates | New record: Journal Name "TEST Dup", Type Sales, Sequence Prefix `INV` → leave the field, then Submit | "Duplicates are not allowed" (or HAP's equivalent) under Sequence Prefix and the save is refused. Close without saving | **Pass** — "Duplicates are not allowed" on Sequence Prefix |
| 13 | Payment Communications required for Sales | New record: Journal Name "TEST Sales", Type **Sales**, Sequence Prefix TSTS, clear Communication Type → Submit; then choose Based on Customer → Submit; then Archive the record it created | Refused while Communication Type is empty, both communication fields marked required. Saved once filled, and the saved journal keeps Based on Customer (`journals.py journal "TEST Sales"`) | **Pass** — refused with "Please fill in Communication Type" while it was empty; saved with Based on Customer, which the CLI confirms (Sequence 10). Archived afterwards |
| 14 | Sequence moves a journal | Open **TEST Journal**, set Sequence to 1 → Save; refresh the view; then set it back to 99 | TEST Journal becomes the **first** row of Journals, above Sales, and returns to last when set back to 99 | **Pass** — first row above Sales at Sequence 1, last again at 99. The record's Save bar needed a second click, as on the other worksheets |
| 15 | Archive | Journals → TEST Journal → ⋯ / Archive | Confirmation "**Are you sure that you want to archive this record?**" with Archive / Cancel. Cancel changes nothing; Archive removes the row from Journals and adds it to Archived (with TEST long prefix). `journals.py journal "TEST Journal"` shows `active: false` | **Pass** — exact confirmation text; Cancel changed nothing; Archive gave "Operation completed", flipped the button to Unarchive and moved the row to Archived (`active: false`) |
| 16 | Unarchive | Archived → TEST Journal → ⋯ / Unarchive (not TEST long prefix) | **No confirmation.** The row returns to Journals in its place by Sequence; TEST long prefix stays archived. `journals.py verify` → 7 in the extract, 0 missing or differing, 2 not in the extract | **Pass** — no confirmation; back in Journals in its Sequence place, TEST long prefix still archived; `verify`: 7 in the extract, 0 missing or differing |
| 17 | Placeholders and help | A new record: look at Journal Name and Sequence Prefix before typing; hover or open the field help on Type, Sequence, both dedicated sequences and both communication fields | "**e.g. Customer Invoices**" and "**e.g. INV**" appear as placeholders (Sequence Prefix carries `hinttype` "1" from the first build — note where its hint is shown). The descriptions are Odoo's help word for word, and Sequence's adds the note about there being no drag handle | **Pass** — both placeholders appear (the `hinttype` setting does not stop the Sequence Prefix hint rendering as the field's placeholder), and Odoo's help sits under Type, Sequence — with the drag-handle note — both dedicated sequences and both communication fields |
| 18 | Odoo side by side | casimir.odoo.com → Invoicing › Configuration › Accounting › Journals, and one journal's form (Sales, Bank) | The same seven journals in the same order, with the same Type and Sequence Prefix; the Sales form shows the same Payment Communications and Dedicated Credit Note Sequence, the Bank form the same Dedicated Payment Sequence. Everything else Odoo shows is in *Not built now* | **Pass** — the tenant lists the same 7 journals with the same Type and Sequence Prefix, and its Sales form carries Dedicated Credit Note Sequence under *Journal Entries* and Payment Communications (Based on Invoice · Full Reference (INV/2024/00001)) under *Advanced Settings*. One difference in order (difference 2) |

### Differences from Odoo seen in testing

1. **One flat form.** Odoo splits the journal over *Journal Entries* and *Advanced Settings* tabs; here every field
   is on one form and Type decides what shows. Each tab would hold one or two fields until the deferred settings
   arrive.
2. **Order at equal Sequence.** Odoo's list falls back to the order the journals were created in — Exchange
   Difference before Cash Basis Taxes — while ours follows the model's declared order, Type then Sequence Prefix
   (Cash Basis Taxes, Exchange Difference, Tax Returns). Both start Sales, Purchases, Bank, Miscellaneous Operations.
3. **Sequence is visible and editable.** Odoo hides it behind the list's drag handle; a HAP table has no handle, so
   the number is the only way to reorder.
4. **The 5-character prefix limit is a form check only.** The API stores a longer value (the evidence is TEST long
   prefix). No duplicates, the constraint that matters for entry numbering, is enforced everywhere.
5. **Odoo fills an empty Sequence Prefix and Journal Name from the Type** ("INV", "Customer Invoices (1)"); here both
   are required instead.
6. **Archive / Unarchive and the Save bar** behave as on the other worksheets: the button that does not apply is
   hidden on a full-page record, and an edit is kept with Save on the *Modifying form data* bar.

### Test records left in the worksheet


- **TEST Journal** (TSTJ, Miscellaneous, Sequence 99, active) — the record the CLI self-check archived and
  unarchived; left active for tests 14–16.
- **TEST long prefix** (Tf798, Miscellaneous, Sequence 99, archived) — created by the API with the 6-character
  prefix `TSTLNG` that the field should have refused; recoded and archived rather than deleted, as the evidence
  for that finding and to give the Archived view a row.

- **TEST Sales** (TSTS, Sales, Sequence 10, archived) — created by test 13 to prove the rule that makes Payment
  Communications required on a Sales journal, with Communication Type **Based on Customer**; archived afterwards.

All three are to be removed after sign-off, with the owner's approval. Tests 10–12 left nothing behind: their forms
were closed without saving.
