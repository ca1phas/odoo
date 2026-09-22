# 05 · Journals

| | |
|---|---|
| Nocoly app | ERP Master · menu group **Invoicing** |
| Worksheet | Journals |
| Odoo model | `account.journal` |
| Reference | **casimir.odoo.com — Odoo saas~19.4+e**: fields, form, list, kanban, search, defaults, `_order`, the SQL constraint and all 7 journals, extracted read-only to `nocoly/reference/odoo-19.4/account.journal.md`. Behaviour the tenant cannot show — the code and name placeholder computed from Type, the archive check — is read from the Odoo 19.0 source in this repo, `addons/account/models/account_journal.py`. Teh Li Wei's first hand-off read his own tenant, ohyes.odoo.com; the owner settled casimir as the reference on 15 Sep 2026 |
| Phase | 1 — core worksheet 5 of 7 |
| Status | First built by **Teh Li Wei** on 15 Sep 2026 (worksheet, 6 controls, 2 views, no records). Gaps against the casimir reference closed, seeded and self-checked with the hap CLI on 16 Sep 2026 · CLI self-checks pass · **UI-tested on 16 Sep 2026: 18 of 18 pass** · then, on the owner's decision the same day, Odoo's two notebook tabs and a remark block in each were added; tests 5–9 and 17 were re-run and pass — **18 of 18** · then, at the end of Phase 1 the same day, **Odoo's refusal to archive a journal with draft entries** went into the Archive workflow, now that 06 Invoices exists (§2). It is proved both ways through the CLI; **tests 19–21 are still to run in the browser** · ready for review. Finally, at the end of Phase 1, the archive guard Odoo has owed this worksheet since 06 existed was built and tested — **tests 19 and 20 pass, 21 not run** (the tenant is read-only), so **20 of 21** · ready for review. **21 Sep 2026** — the screen pass (`15-ui-conformance.md` §6.6) found that the refusal also drew an untranslated **中止** toast, HAP's own mark of an aborted run. The guard was restructured so nothing aborts: the update moved onto the branch's *No* path and the abort node was deleted. `draftcheck` still passes both ways and the refused run now ends `status` 2 with an empty cause, so no toast is drawn — **test 19 is worth a re-run in the browser** |

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
| 5 | Dedicated Credit Note Sequence | `refund_sequence` | Checkbox | — | unchecked | Tab **Journal Entries**. Odoo's help. Shown for Sales and Purchase only |
| 6 | Dedicated Payment Sequence | `payment_sequence` | Checkbox | — | unchecked | Tab **Journal Entries**. Odoo's help. Shown for Bank, Cash and Credit Card only |
| 7 | Communication Type | `invoice_reference_type` | Single Select, dropdown | by rule | Based on Invoice | Tab **Advanced Settings**. **Based on Customer · Based on Invoice**. Odoo's help. Required on Odoo's model, but here a rule requires it, because Odoo only ever shows it on a Sales journal and a hidden required field can never be filled |
| 8 | Communication Standard | `invoice_reference_model` | Single Select, dropdown | by rule | Full Reference (INV/2024/00001) | Tab **Advanced Settings**. **Full Reference (INV/2024/00001) · European (RF83INV202400001) · Numbers only (202400001)** — Odoo's `odoo`, `euro`, `number`, labelled with the examples the tenant shows. Required by the same rule |
| 9 | Active | `active` | Checkbox | — | checked | **Hidden**, on no tab. Odoo's help. Set by Archive / Unarchive; the two views filter on it |

**Added since by bundles:** **Default Account**, **Suspense Account**, **Profit Account**, **Loss Account** and **Private Share Account** (`default_account_id`, `suspense_account_id`, `profit_account_id`, `loss_account_id`, `non_deductible_account_id`), relations to Chart of Accounts on the tab Journal Entries above the two dedicated sequences, shown and required by Type through five rules, and a Default Account column after Sequence Prefix on both views — bundle 2, `09-chart-of-accounts.md`.

Type, Communication Type and Communication Standard keep the option keys of the first build, and every field keeps
its control id and alias — records already written against them stay valid.

Six controls on the form hold no data and so are not fields: the two tabs, and inside each a **divider** carrying a
heading and, under it, a **remark block** that says what Odoo shows on that tab and which bundle or table brings it
here — the owner's decision of 16 Sep 2026, so that a tab with two checkboxes does not read as the whole story. The
divider is HAP's 分段 block (type 22) and provides the heading only; the text is the remark block (type 10010),
which stores HTML. Their wording is in Form layout below; their ids are in §2.

### Form layout

| Odoo 19.4 (`view_account_journal_form`) | Nocoly |
|---|---|
| Ribbon "Archived" when not active | — (HAP shows archived records only in the Archived view) |
| Journal Name (h1, required while Type is empty) | Journal Name |
| Group: Type · Sequence Prefix \| Ledger | Type \| Sequence Prefix |
| — (Sequence is the list's drag handle, not on the form) | Sequence |
| Tab *Journal Entries* (`page name="bank_account"`): Dedicated Credit Note Sequence (Sales, Purchase) · Dedicated Payment Sequence (Bank, Cash, Credit Card) · Invoice report · bank fields | **Tab Journal Entries**: Dedicated Credit Note Sequence \| Dedicated Payment Sequence, the same two rules, and the remark block below |
| Tabs *Incoming / Outgoing Payments* | — named in the Journal Entries remark (Not built now) |
| Tab *Advanced Settings*, hidden for Bank and Cash › group Payment Communications, Sales only: Communication Type · Communication Standard; groups Automation, Emails, Electronic Data Interchange | **Tab Advanced Settings**, hidden for Bank and Cash: Communication Type \| Communication Standard, the same rule, and the remark block below |
| Chatter | HAP's own discussion |

**Odoo's two tabs, with a remark block each** (owner, 16 Sep 2026). Journal Name, Type, Sequence Prefix and
Sequence stay in the main area above the tabs, as in Odoo; Active is hidden and on no tab. Because each tab holds
only two fields until the deferred settings arrive, each ends with a divider heading — *Also on Odoo's Journal
Entries tab* and *Also on Odoo's Advanced Settings tab* — and, under it, a remark block that names what Odoo shows
there and what will bring it. As the blocks render:

> **Also on Odoo's Journal Entries tab:** the Invoice report, and — on Bank and Credit Card journals — the Bank
> Account Number, BIC and Bank Feeds. Odoo also lists this journal's payment method lines on its Incoming and
> Outgoing Payments tabs.
>
> The bank fields come with bank accounts, the report with the invoice report templates, and the payment method
> lines with the Payments bundle.

> **Also on Odoo's Advanced Settings tab:** Automation (Self Billing), Emails (Email Alias and Send Copy To) and
> Electronic Data Interchange.
>
> Self Billing and the EDI settings come with e-invoicing; the alias needs a mail alias and incoming mail.

The heading is repeated because the two controls are separate: the divider shows only its name, and the block's own
name is hidden (`hidetitle`), so the block restates it as its bold lead-in.

**Replaced on 22 Sep 2026** for the app's users: the headings are now *About Journal Entries* and *About
Advanced Settings*, and the blocks say what the tab is for. The texts above are kept at the foot of this file.

### Rules

All five are interaction rules on Type. A HAP rule applies its action while its condition holds and the opposite
when it does not, so the four show rules hide their fields for every other type — and for a new record whose Type
is still empty, which is what Odoo's `invisible` does too — while the one hide rule shows its tab for every other
type and on a new record, again as Odoo does. That is why the tab rule is written as a hide and the rest as shows.

| Rule | When | Effect | Odoo source |
|---|---|---|---|
| Payment Communications only for Sales | Type is Sales | show **Communication Type** and **Communication Standard** | `<group string="Payment Communications" invisible="type != 'sale'">` |
| Payment Communications are required for Sales | Type is Sales | **require** both | `required=True` on the model, reachable only on a Sales journal |
| Dedicated Credit Note Sequence only for Sales and Purchase | Type is Sales or Purchase | show **Dedicated Credit Note Sequence** | `<field name="refund_sequence" invisible="type not in ['sale', 'purchase']"/>` |
| Dedicated Payment Sequence only for Bank, Cash and Credit Card | Type is Bank, Cash or Credit Card | show **Dedicated Payment Sequence** | `<field name="payment_sequence" invisible="type not in ('bank', 'cash', 'credit')"/>` |
| Advanced Settings hidden for Bank and Cash journals | Type is Bank or Cash | **hide** the whole **Advanced Settings** tab, remark block and all | `<page name="advanced_settings" invisible="type in ['bank', 'cash']">` |

**Journal Entries has no visibility rule** — Odoo shows that page for every type, and so does this worksheet; only
the two checkboxes inside it come and go.

Nothing is validated on save. Odoo's two guards on this model are the SQL uniqueness of the code, which is the
field's own **No duplicates**, and the refusal to archive a journal that has draft entries — which needed 06
Invoices and is now inside the Archive button's workflow (Buttons below, and §2).

### Buttons (Odoo ⚙ Actions)

| Button | Shown when | Does | Confirmation |
|---|---|---|---|
| Archive | Active is checked | **Counts the Invoices whose Journal is this journal and whose Status is Draft. One or more: notifies the user with Odoo's message and the run ends there, leaving Active alone. None: Active → unchecked** — the update sits on the branch's *No* path, so nothing is aborted and **no 中止 toast is drawn** (§2) | "Are you sure that you want to archive this record?" · Archive / Cancel |
| Unarchive | Active is unchecked | Active → checked | none |

**The draft-entry check** is Odoo's `_check_auto_post_draft_entries`
(`addons/account/models/account_journal.py:686`), which 05 left owed until 06 Invoices existed. It was built on
16 Sep 2026, inside the Archive button's workflow, and the message is Odoo's own, verbatim:

> You can not archive a journal containing draft journal entries.
>
> To proceed:
> 1/ go to Accounting > Accounting > Journal Entries
> 2/ filter on this journal and on 'Unposted' entries
> 3/ select them all and post or delete them through the action menu

Odoo raises this as a dialog that blocks the save. **HAP has no dialog to raise from a button workflow** — see
§2 — so the message arrives as an **in-app notification** to whoever pressed Archive, headed
*Cannot archive this journal*, and the flow stops before Active is touched. Unarchive keeps no such check:
Odoo's constraint deliberately fires only when archiving (`self.filtered(lambda j: not j.active)`).

Otherwise exactly as on Contacts, Units & Packagings, Products and Product Variants: a workflow that writes Active
on the triggering record, and the button that does not apply is **not shown at all** — an open record carries only the
one that applies, so an active journal shows Archive alone. (Re-checked on 16 Sep 2026 while testing 06 Invoices,
which has the same button shape; the earlier note here said "greyed out", which is wrong.)

### Views

| View | Type | Shows | Odoo 19.4 |
|---|---|---|---|
| Journals | table — opens first | Active journals. Columns **Journal Name · Type · Sequence Prefix**, sorted **Sequence, then Type, then Sequence Prefix**, all ascending. Quick filter Type, several at a time | List view: drag handle · Journal Name · Type · Ledger (hidden) · Sequence Prefix · Default Account · Active (hidden). `_order` is `sequence, type, code` |
| Archived | table | Archived journals, the same columns, sort and quick filter | The *Archived* search filter |

Odoo's search filters Sales · Purchases · Liquidity · Miscellaneous become the one Type quick filter, which takes
several types at once — Liquidity is Cash + Bank + Credit Card. Default Account arrived with the Chart of Accounts
bundle (*Added since by bundles*, above).
Odoo's kanban (name and type only) is not reproduced; its second action, the Invoicing *Dashboard*, is a different
view of the same model and waits for the dashboard fields.

### Not built now, and why

| Odoo 19.4 field / feature | Why not now |
|---|---|
| ~~Default Account, Suspense Account, Profit Account, Loss Account, Private Share Account (`default_account_id`, `suspense_account_id`, `profit_account_id`, `loss_account_id`, `non_deductible_account_id`) — and Odoo's Default Account list column~~ | **Built on 17 Sep 2026 by the Chart of Accounts bundle** — the five accounts on the tab Journal Entries, Odoo's visibility and requirement by Type as rules, and the column on both views; see `worksheets/09-chart-of-accounts.md` |
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
| ~~"You cannot archive a journal containing draft journal entries" (`_check_auto_post_draft_entries`)~~ | **Built on 16 Sep 2026**, once 06 Invoices existed: it is in the Archive button's workflow (Buttons above, §2). Odoo's dialog becomes an in-app notification — difference 7 |
| ~~Roles~~ | **Set on 16 Sep 2026** for the whole app, at the end of Phase 1: five stock roles renamed to English and four business roles, one per Odoo accounting group. The table is in `REVIEWING.md` › *Phase 1 · Roles* |

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

Built by `nocoly/build/journals.py` — steps `layout → rules → views → buttons → draftguard → seed`, or `all` for
every one of them followed by `check`. Each step reads the live worksheet first, refuses to run unless the profile
reaches ERP Master › Invoicing › Journals and the worksheet holds only the first build plus this script's own work,
reads back what it wrote, and is safe to re-run: a second `all` wrote nothing. Helpers: `check` reads controls,
their tabs, options, defaults, rules, views, buttons **and the archive guard** back against the spec, `verify`
compares every journal with the extract, `selfcheck` runs the writes the worksheet must refuse and both buttons,
`draftcheck` proves the archive guard both ways, `order` prints each view's records in the view's own order,
`journal "<Journal Name>"` a journal's stored values (hidden fields included), `untouched` the other four
worksheets' control count and digest, and `show` the control list. The profile comes from `$HAP_PROFILE` and
otherwise from hap-cli's active profile; nothing in `common.py` changed.

| Element | Built | Id |
|---|---|---|
| App | ERP Master | `6cb4d051-a33c-4bf9-b56f-5f47f0e85dc9` |
| Menu group | Invoicing — Journals, Invoices | `6aa8f3ecbf00c316381dbbe8` |
| Worksheet | Journals, alias `account_journal` | `6aa8f5191204328eb1af162a` |
| Controls | 15: the 9 fields, 2 tabs, 2 divider headings and 2 remark blocks | — |
| Kept from the first build | Journal Name · Sequence Prefix · Type · Communication Type · Communication Standard · Active | `6aa8f6c81204328eb1af1676` · `…1677` · `…1678` · `…1679` · `…167a` · `…167b` |
| Added, fields | Sequence · Dedicated Credit Note Sequence · Dedicated Payment Sequence | `6aa9dabcbd43f55762c6f430` · `6aa9dabcbd43f55762c6f431` · `6aa9dabcbd43f55762c6f432` |
| Added, tabs | Journal Entries · Advanced Settings | `6aa9e869e54d2a34fa4dfe40` · `6aa9e869e54d2a34fa4dfe41` |
| Added, divider headings (type 22) | Also on Odoo's Journal Entries tab · Also on Odoo's Advanced Settings tab | `6aa9e869e54d2a34fa4dfe42` · `6aa9e869e54d2a34fa4dfe43` |
| Added, remark blocks (type 10010, HTML) | Journal Entries note · Advanced Settings note | `6aa9eca8e43d174ab37499c2` · `6aa9eca8e43d174ab37499c3` |
| Rules | Payment Communications only for Sales · Payment Communications are required for Sales · Dedicated Credit Note Sequence only for Sales and Purchase · Dedicated Payment Sequence only for Bank, Cash and Credit Card · Advanced Settings hidden for Bank and Cash journals | `6aa9dae5e54d2a34fa4dfde2` · `6aa9dae67d58b0f44930e6ce` · `6aa9dae67d58b0f44930e6d0` · `6aa9dae7e43d174ab37498e9` · `6aa9e8b5bd43f55762c6f48a` |
| Views | Journals · Archived (both the first build's, re-sorted) | `6aa8f5191204328eb1af162e` · `6aa8f7074720c515252bf2c8` |
| Buttons | Archive · Unarchive | `6aa9db31805aef7032865005` · `6aa9db34e43d174ab37498ec` |
| Button workflows | Archive the journal (five steps since the guard) · Unarchive the journal (one update step), both published | `6aa9db3116473257ad4c471e` · `6aa9db348e75db182e77e1e2` |
| Archive guard, added 16 Sep · restructured 21 Sep | Draft entries in this journal (汇总, 107) · Does the journal still hold draft entries? (branch) · Cannot archive this journal (站内通知, 27) · **Archive the journal**, now on the *No* path (update, 6) | `6aaa48f18e75db182e7b42d0` · `6aaa48f18e75db182e7b42e7` · `6aaa48f287707da9d60f6ad1` · `6ab0a866789584ded322fd9a` |
| | The abort *Stop — leave Active alone* (中止流程, 30) and the trunk *Archive the journal* it guarded were **deleted** on 21 Sep 2026 with the restructuring below | ~~`6aaa48f48e75db182e7b434d`~~ · ~~`6aa9db338e75db182e77e1a0`~~ |
| Records | 7 journals of the extract, plus TEST Journal (TSTJ, active), TEST draft guard (TSTDG, active) and the archived TEST long prefix (Tf798) and TEST Sales (TSTS) | — |

Every id is in `nocoly/build/ids.json` under "Journals: …" keys, the controls and rules in two new sections
(`controls`, `rules`); no existing key was renamed.

### The archive guard

Odoo's `_check_auto_post_draft_entries` refuses to archive a journal that still has draft entries. 05 recorded it
as owed once 06 Invoices existed; it was built on **16 Sep 2026**, at the end of Phase 1, by
`journals.py draftguard` — inside the **Archive button's workflow** (`6aa9db3116473257ad4c471e`, button
`6aa9db31805aef7032865005`), in front of the step that unchecks Active:

```
Trigger by button
  → Draft entries in this journal              汇总 (107) over Invoices: Journal is this journal (a Relation
                                               compared with the trigger's record, conditionId 33) and Status
                                               is Draft
  → Does the journal still hold draft entries?
       · Yes — the count is 1 or more  → Cannot archive this journal   站内通知, Odoo's message, to the
                                                                       person who pressed the button
                                                                       — the path ends here
       · No                            → Archive the journal           Active ← unchecked
  (nothing follows the gateway)
```

**Restructured on 21 Sep 2026 — the abort node is gone.** The first cut left *Archive the journal* on the trunk,
where a HAP branch **converges**: an empty path and a path whose steps have run both reach whatever follows the
gateway, so the drafts path had to end in a 中止流程 abort (node type 30) to stop the run before the update. It
worked — the guard refused correctly — but an aborted run draws **HAP's own toast: a warning icon and the
untranslated word 中止**, with Odoo's explanation only in the notification centre. That is what the screen pass
raised as `15-ui-conformance.md` §6.6.

**A branch path can hold a data step.** `hap workflow node add --type 6 --after <the path node>` sets that path's
`nextId` to the new node, and the node saves its configuration, reads back `isException: false` and publishes. So
the update moved onto the **No** path — a second update step was created inside the path, the old node's
`actionId`, `appId`, `selectNodeId` and `fields` were copied onto it and read back before anything was removed,
then the trunk node and the abort were deleted and the workflow republished. Nothing else changed: the update
still carries the first build's single field write, `Active` ← unchecked, and `journals.py draftguard` now
recognises the new shape and writes nothing on a re-run. `check` fails the workflow if any abort node comes back.

**What this buys.** A refused Archive now ends a run **normally** — `approval history` reports `status` **2** with
an empty `causeMsg`, where the same refusal on 21 Sep at 11:20 reported `status` **3**, `cause` **6666**,
`causeMsg` **中止**, naming *Stop — leave Active alone*. **No toast is drawn**, so nothing untranslated reaches
the screen. The cost is that the *only* feedback is still the in-app notification below, which is difference 7 —
the user is told the operation completed and must open the bell to learn that it did not.

**What HAP can put in front of a user, which §1 asked to be found out first.** Not a dialog. A custom action
button has one message, its confirmation, and it is shown *before* the workflow runs; the click itself always
reports "Operation completed". The abort node carries a name and a description and nothing user-facing. The one
node that reaches a person is **站内通知** (notice, type 27), and it arrives as an **in-app notification** in
HAP's workflow channel — the bell, not a dialog — reading:

```
【Cannot archive this journal】You can not archive a journal containing draft journal entries.

To proceed:
1/ go to Accounting > Accounting > Journal Entries
2/ filter on this journal and on 'Unposted' entries
3/ select them all and post or delete them through the action menu
```

HAP puts the **node's name in 【】 in front of the message**, so the step is named as the heading Odoo's dialog
does not have, rather than as what it does. Two consequences a reviewer should judge:

- The message is **asynchronous and easy to miss**. The user clicks Archive, is told the operation completed,
  the row stays where it is, and the reason is in the notification list. Odoo stops the save with the text on
  screen. This is difference 7.
- The three numbered steps are **Odoo's menus, verbatim**, and name paths this app does not have. Here the
  equivalent is Invoicing › Invoices, the *Journal Entries* view or the Status quick filter. Odoo's wording was
  kept rather than rewritten; say if you would rather it named this app's own menus.

**Proved both ways on TEST records** (`journals.py draftcheck`, 16 Sep 2026), leaving the tenant's seven journals
alone — the Sales journal does hold the two seeded drafts, and archiving it is not how this is tested:

- **TEST draft guard** (TSTDG, Miscellaneous, Sequence 99) with one draft entry on it — a `TEST draft guard`
  journal entry, Status Draft, made for this — refused: `Active=1` after Archive. **Re-run on 21 Sep 2026 after
  the restructuring**, with two draft documents on it, and refused again: `Active=1`, the run `status` **2** with
  an empty `causeMsg` (it was status 3 · 中止 before), and its node trace **trigger → count → branch → Cannot
  archive this journal** — *Archive the journal* was never reached. The notification arrived, text as above.
- **TEST Journal** (TSTJ), which holds no document, archived exactly as before: `Active=0`, node trace trigger →
  count → branch → *Archive the journal* (now reached through the **No** path). It was unarchived again and is
  left **active** for the reviewer.
- `draftguard` is idempotent: a second run reported "already built; not re-published".

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

**After the UI test (18 of 18 pass), the owner asked for Odoo's two tabs after all** — the same day, and built on
the form exactly as it stood:

| Change | Why |
|---|---|
| Tabs **Journal Entries** and **Advanced Settings** added; the two dedicated sequences moved into the first, the two communication fields into the second. Journal Name, Type, Sequence Prefix and Sequence stay above the tabs; Active is still hidden and on no tab | Odoo's notebook, page for page (`page name="bank_account"` and `page name="advanced_settings"`), and Odoo keeps those four fields in the form's head |
| A **divider heading** inside each tab, naming what Odoo shows there and which bundle or table brings it | The owner's answer to the thin tabs the flat form was chosen to avoid: a reviewer sees what the tab will hold instead of two lonely checkboxes |
| Fifth rule, **Advanced Settings hidden for Bank and Cash journals** — written as *hide when Type is Bank or Cash*, not as a show | Odoo's `invisible="type in ['bank', 'cash']"`. A rule reverses its action when the condition fails, so the hide form shows the tab for every other type **and on a new record whose Type is still empty**, which is what Odoo does. A show form would have hidden it until a Type was chosen |
| Journal Entries has no rule | Odoo gives that page no `invisible`; only the checkboxes inside it come and go |

**The UI test of the tabs then found the notes invisible**, and they were rebuilt the same day:

| Change | Why |
|---|---|
| A **remark block** (control type **10010**) added inside each tab, directly under its divider, holding the note as HTML — `<p>` with a bold lead-in — full width, `hidetitle` "1" so its internal name does not show | HAP renders a **type-22 divider's `desc` nowhere at all**, not even as a tooltip, so the notes written there were invisible. The remark block is the control HAP itself uses for a text block, as the org's Fit-Out Process Flow app shows; hap-cli has no builder for it, so its JSON goes through `add-fields` |
| The two dividers keep their headings; their descriptions were **cleared** | The text renders nowhere, and leaving it would mislead the next reader into thinking the form says something it does not. The controls themselves stay — nothing is deleted |

The four field rules, the tab rule, the buttons, the views, the seven journals and the three TEST records were not
touched by either change, and `verify` confirms it. Nothing was deleted or renamed. Worksheet 06 Invoices
(`6aa90facf363582dd37a62f7`) is Teh Li Wei's and was never opened. The app log was checked before each write:
every entry on 16 Sep is this build's own.

**Self-checks through the CLI** (`journals.py check`, `verify`, `selfcheck`, `order`, `untouched`; the TEST records
are listed in §3):

- **Configuration** — `check` reads back OK: 15 controls in their places with the right hints, help, required and
  hidden settings, Sequence Prefix unique with `max` 5, the six Type options and both communication option lists
  with the first build's keys, the defaults (Sequence 10, both checkboxes unchecked, Based on Invoice, Full
  Reference, Active checked), the five rules enabled with Type as their only condition, both views with their
  columns, three-level sort, Active filter and Type quick filter, in that order, and both buttons with their
  conditions and the Archive confirmation.
- **The tabs** — `check` prints what each holds, read from the stored `sectionId` of every control: Journal
  Entries — Dedicated Credit Note Sequence, Dedicated Payment Sequence, the divider, the remark block; Advanced
  Settings — Communication Type, Communication Standard, the divider, the remark block; on no tab — Journal Name,
  Type, Sequence Prefix, Sequence, Active. Both remark blocks read their HTML back exactly as sent, `hidetitle` "1",
  width 12, inside their tab; both dividers read back with an empty description. The fifth rule stores Type equals
  Bank or Cash with rule item type 2 (hide) on the Advanced Settings tab control.
- **The seven journals** — `verify`: "7 in the extract; 0 missing or differing", the three TEST records listed as
  not in the extract, before and after the tabs were added. `order` lists both views in the view's own order:
  Journals — Sales [INV, 5], Purchases [BILL, 6], Bank [BNK1, 7], Miscellaneous Operations [MISC, 9], Cash Basis
  Taxes [CABA, 10], Exchange Difference [EXCH, 10], Tax Returns [TAX, 10], TEST Journal [TSTJ, 99]; Archived —
  TEST Sales [TSTS, 10], TEST long prefix [Tf798, 99]. That is Odoo's list order.
- **No duplicates holds on the API** — creating a journal with Sequence Prefix INV and setting TEST Journal's
  prefix to BILL were both refused, `resultCode 11` naming `6aa8f6c81204328eb1af1677` (Sequence Prefix).
- **The 5-character limit does not.** `record create` and `record update` both stored the 6-character prefix
  `TSTLNG`; the field's `checkrange` / `max` is a form-side check only. The created record was recoded `Tf798`
  and archived rather than deleted, and TEST Journal's prefix was restored to TSTJ. No HAP filter operator measures
  text length, so a validation rule cannot enforce it either — **the form's own check is test 11**, and any later
  import must check the length itself. Recorded in BUILDING.md.
- **Both buttons** — `hap workflow trigger` of Archive set TEST Journal's Active to unchecked and of Unarchive back
  to checked, each within a second. TEST Journal is left **active** for the reviewer.
- **Idempotent** — every step was run twice and `all` once more, before and after the tabs: the second runs added no
  control, rule, view, button or record, re-created no workflow ("already has steps; left as is"), and wrote no
  field ("layout already as specified; nothing saved").
- **The other worksheets are untouched.** Their controls were compared by id before and after every save, and the
  digests are the same at the end as at the start: Contacts 30 `9f7e59498c3081a1`, Units & Packagings 10
  `e57dc8775cd5038b`, Products 19 `a8f9911118fda7d7`, Product Variants 20 `6eba14458f20e2a6`. Their rules, buttons
  and views also read back unchanged (3 / 2 / 3 views, 3 / 2 / 2, 3 / 2 / 3 and 2 / 2 / 2).

The five rules, the tabs, the remark blocks, the placeholders, the descriptions and the quick filter are browser
behaviour: HAP stores them as configured and only the UI test can show them working. **The remark block is the one
control type this app had not used before** — how its heading and text render, and whether a hidden tab takes its
block with it, are tests 5–9.

### Found while building

- A text field's **maximum length is not enforced on API writes** (above). Its sibling setting **No duplicates
  is** — the two look alike in the field editor and behave differently.
- **Deleting a field leaves every view sorting on its id.** Journals and Archived still carried
  `sortCid`/`moreSort` pointing at the Sequence control removed on 15 Sep; nothing cleans that up, and the views had
  been sorting on a field that no longer existed.
- **A rule's action is reversed when its condition fails**, so show and hide are two ways of writing the same
  toggle — except while the driving field is empty. Which way round to write one follows from what should happen on
  a new record: the four field rules *show* for the types that need the field, so it stays hidden until a Type is
  chosen, and the tab rule *hides* for Bank and Cash, so the tab is there from the start. Both match Odoo's
  `invisible`; neither could be flipped without changing the empty case.
- A dropdown rule condition takes **several option keys in one `values` list** ("is any of"), and reads them back in
  the options' own order rather than the order they were written in.
- **HAP's static-text block is the 分段 control, type 22** (`SPLIT_LINE` in hap-cli, "Divider" in its builder
  vocabulary) — a heading with a description and no data. Nothing else in ERP Master uses it, and none of the org's
  other apps has one. It takes a `sectionId` like any field, so it can live inside a tab.
- Teh Li Wei's Sequence Prefix carries `advancedSetting.hinttype` "1", which no other field in the app sets. It was
  left as it is — test 17 confirmed the placeholder still shows in the field.
- Teh Li Wei's Sequence Prefix carries `advancedSetting.hinttype` "1", which no other field in the app sets. It was
  left as it is — test 16 says where the placeholder appears.

**Found while building the archive guard** (16 Sep 2026; all of it is in `BUILDING.md`):

- **HAP's node type 30 is 中止流程**, an abort. Adding one anywhere but last in its chain is refused outright:
  `中止节点后面不允许有节点`. It takes a name and a description and **nothing user-facing** — no message. hap-cli's
  DSL has no builder for it, so it goes in with `workflow node add --type 30`.
- **A branch converges**, so a path that "does nothing" is not a stop. With the update on the trunk, the Yes path
  would have notified the user and then archived the journal anyway, which is why the first cut needed the abort.
- **…but a branch path can hold the step itself, which is the way round that needs no abort** (21 Sep 2026).
  `workflow node add --type 6 --after <the path node>` sets the path's `nextId` to the new node; it takes its
  configuration through `node save --type 6` like any other data step, reads back `isException: false` and
  publishes. Moving *Archive the journal* onto the **No** path let the abort go, and with it HAP's untranslated
  **中止** toast — the only thing the user saw on screen when the guard refused (`15-ui-conformance.md` §6.6).
  There is **no "move a node" call**: the new step is created inside the path, the old node's `actionId`,
  `appId`, `selectNodeId` and `fields` are copied onto it and read back, and only then is the old node deleted.
  All of it happens on the draft, so `hap workflow rollback <pid> -y` undoes a mis-built attempt.
- **An aborted run is visible and a completed one is not.** The same refusal reported `status` **3**, `cause`
  **6666**, `causeMsg` **中止** before the change and `status` **2** with an empty `causeMsg` after it — which is
  also how to tell from the CLI whether any toast would have been drawn.
- **A 站内通知 renders its node's name as the message's heading**, `【name】text`, so the node name is user-facing.
  The name also lives a second time inside the node's `flowNodeMap` "106" channel config, which
  `workflow node rename` does not update.
- **"The person who pressed the button" is the 系统 node's `triggeraid`**, not hap-cli's `kind: "triggerUser"`.
  That kind keys `uaid` off the trigger node, which on a *button* trigger the server reads back as **Last
  modifier** — the journal's last editor, who need not be the person clicking. The first cut had it wrong and
  read back as such.
- **A 汇总 (107) node's filter has its conditions' `nodeId` rewritten to the aggregate node's own id.** What binds
  the count to the right journal is the *comparison value's* `nodeId`, the trigger.
- **`hap approval history` is how a guard is proved.** An aborted run comes back with `status` 3 and
  `instanceLog.causeMsg` "中止" naming the node, and `approval history-detail <instanceId>` lists every node the
  run passed through — which is what shows that *Archive the journal* was never reached.

## 3 · Test list

To run in the Nocoly UI, in Chrome, against
`~/.hap-venv/bin/python nocoly/build/journals.py journal "<Journal Name>"` / `order` / `check` from the repo root
for the stored values. Test records are named `TEST …`. Run on 16 Sep 2026: **18 of 18 pass**. The owner then asked
for Odoo's two tabs and their remark blocks (§2), so **tests 5–9 and 17 are to be re-run** — their expectations now
describe the tabs and their Result column is empty again. The other twelve results stand: the change touched no
view, button, record or field rule.

**Tests 19–21 are new**, added with the archive guard on 16 Sep 2026 and proved through the CLI
(`journals.py draftcheck`, §2) but **not yet in the browser** — the one thing the CLI cannot show is whether the
notification actually reaches the person who pressed the button in the UI, and what the click looks like while it
does. Tests 2, 3, 4 and 14 now see one more row, **TEST draft guard** (TSTDG, Sequence 99), which sorts last in
Journals beside TEST Journal.

| # | Check | Steps | Expected | Result |
|---|---|---|---|---|
| 1 | Menu and views | Open ERP Master → menu group **Invoicing** → Journals | Invoicing lists Journals then Invoices. Journals opens on the **Journals** table; its view list is Journals · Archived | **Pass** — Invoicing lists Journals then Invoices; Journals opens on its table, views Journals · Archived |
| 2 | Table, columns and order | The Journals view | 8 rows, columns **Journal Name · Type · Sequence Prefix**, in this order: Sales [INV], Purchases [BILL], Bank [BNK1], Miscellaneous Operations [MISC], Cash Basis Taxes [CABA], Exchange Difference [EXCH], Tax Returns [TAX], TEST Journal [TSTJ]. No Sequence, Active or communication column | **Pass** — 8 rows in exactly that order, those three columns only |
| 3 | Archived view | Switch to Archived | 1 row: TEST long prefix [Tf798], Miscellaneous, same three columns | **Pass** — TEST long prefix [Tf798], Miscellaneous (TEST Sales joined it in test 13) |
| 4 | Type quick filter | Journals → the Type quick filter: pick Sales; then Cash + Bank + Credit Card together (Odoo's *Liquidity*); then Miscellaneous; clear | Sales → Sales. Liquidity → Bank only (the tenant has no Cash or Credit Card journal). Miscellaneous → Miscellaneous Operations, Cash Basis Taxes, Exchange Difference, Tax Returns, TEST Journal. Cleared → all 8 | **Pass** — Sales → Sales; Cash + Bank + Credit Card → Bank alone; Miscellaneous → the 5; cleared → 8 |
| 5 | A Sales journal's form, and the tabs | Open **Sales** | Above the tabs: Journal Name Sales, Type Sales, Sequence Prefix INV, Sequence 5, no Active field. Two tabs, **Journal Entries** then **Advanced Settings**. Journal Entries: **Dedicated Credit Note Sequence shown and ticked**, Dedicated Payment Sequence **not shown**, then the remark block *Also on Odoo's Journal Entries tab* with its text. Advanced Settings: **Communication Type (Based on Invoice) and Communication Standard (Full Reference (INV/2024/00001))**, both marked required, then the remark block *Also on Odoo's Advanced Settings tab* | **Pass** — both tabs, Journal Entries first. Journal Entries: Dedicated Credit Note Sequence ticked, no Dedicated Payment Sequence, then the heading and its note. Advanced Settings: Communication Type Based on Invoice and Communication Standard Full Reference (INV/2024/00001), both marked required, then its note |
| 6 | A Purchase journal's form | Open **Purchases** | Type Purchase, BILL, Sequence 6. Journal Entries: Dedicated Credit Note Sequence shown and ticked, no Dedicated Payment Sequence, the remark block. **Advanced Settings is shown** (Purchase is neither Bank nor Cash) but holds **only its remark block** — no communication fields | **Pass** — Journal Entries as expected; Advanced Settings is shown and holds only its heading and note |
| 7 | A Bank journal's form | Open **Bank** | Type Bank, BNK1, Sequence 7. Journal Entries: **Dedicated Payment Sequence shown and ticked**, no Dedicated Credit Note Sequence, the remark block. **No Advanced Settings tab at all** — the rule hides it, remark block and all | **Pass** — only the Journal Entries tab exists; Dedicated Payment Sequence ticked, no Dedicated Credit Note Sequence |
| 8 | A Miscellaneous journal's form | Open **Miscellaneous Operations** | Type Miscellaneous, MISC, Sequence 9. Journal Entries holds **only its remark block** — neither checkbox. Advanced Settings is shown and holds only its remark block | **Pass** — Journal Entries holds only the heading and note; Advanced Settings the same |
| 9 | A new record, the defaults and the tab rule | Journals → + Record; look before choosing a Type; then pick Cash, then Bank, then Credit Card, then Sales | With no Type: Journal Name, Type, Sequence Prefix and Sequence — Sequence already **10** — and **both tabs shown**, each holding only its remark block. **Cash and Bank hide the Advanced Settings tab**; Cash, Bank and Credit Card each add Dedicated Payment Sequence, unticked, and Credit Card brings Advanced Settings back. Sales → Dedicated Credit Note Sequence unticked, and on Advanced Settings the two communication fields with **Based on Invoice** and **Full Reference (INV/2024/00001)**. Close without saving | **Pass** — with no Type both tabs show with their notes only, Sequence 10. Cash hid Advanced Settings and added Dedicated Payment Sequence; Credit Card brought the tab back and kept the payment checkbox; Sales showed Dedicated Credit Note Sequence and, on Advanced Settings, the two communication fields with their defaults, both required. Discarded without saving |
| 10 | Required fields | On that new record: Submit with everything empty; then Journal Name "TEST Required", Type Miscellaneous, Sequence Prefix empty → Submit | Refused both times, Journal Name / Type / Sequence Prefix marked. Close without saving | **Pass** — "Please fill in Journal Name", "Please fill in Sequence Prefix" and "Please fill in the record correctly" |
| 11 | Sequence Prefix at most 5 characters | New record: Journal Name "TEST Long", Type Miscellaneous, Sequence Prefix `TSTLNG` (6 characters) → leave the field, then Submit | The form refuses the 6th character or shows a length error and will not save. (Through the API the same value **is** stored — §2.) Close without saving | **Pass** — "Please enter 1 to 5 characters" on Sequence Prefix, and Submit refused. Through the API the same value is stored (§2, difference 4) |
| 12 | Sequence Prefix No duplicates | New record: Journal Name "TEST Dup", Type Sales, Sequence Prefix `INV` → leave the field, then Submit | "Duplicates are not allowed" (or HAP's equivalent) under Sequence Prefix and the save is refused. Close without saving | **Pass** — "Duplicates are not allowed" on Sequence Prefix |
| 13 | Payment Communications required for Sales | New record: Journal Name "TEST Sales", Type **Sales**, Sequence Prefix TSTS, clear Communication Type → Submit; then choose Based on Customer → Submit; then Archive the record it created | Refused while Communication Type is empty, both communication fields marked required. Saved once filled, and the saved journal keeps Based on Customer (`journals.py journal "TEST Sales"`) | **Pass** — refused with "Please fill in Communication Type" while it was empty; saved with Based on Customer, which the CLI confirms (Sequence 10). Archived afterwards |
| 14 | Sequence moves a journal | Open **TEST Journal**, set Sequence to 1 → Save; refresh the view; then set it back to 99 | TEST Journal becomes the **first** row of Journals, above Sales, and returns to last when set back to 99 | **Pass** — first row above Sales at Sequence 1, last again at 99. The record's Save bar needed a second click, as on the other worksheets |
| 15 | Archive | Journals → TEST Journal → ⋯ / Archive | Confirmation "**Are you sure that you want to archive this record?**" with Archive / Cancel. Cancel changes nothing; Archive removes the row from Journals and adds it to Archived (with TEST long prefix). `journals.py journal "TEST Journal"` shows `active: false` | **Pass** — exact confirmation text; Cancel changed nothing; Archive gave "Operation completed", flipped the button to Unarchive and moved the row to Archived (`active: false`) |
| 16 | Unarchive | Archived → TEST Journal → ⋯ / Unarchive (not TEST long prefix) | **No confirmation.** The row returns to Journals in its place by Sequence; TEST long prefix stays archived. `journals.py verify` → 7 in the extract, 0 missing or differing, 2 not in the extract | **Pass** — no confirmation; back in Journals in its Sequence place, TEST long prefix still archived; `verify`: 7 in the extract, 0 missing or differing |
| 17 | Placeholders, help and the remark blocks | A new record: look at Journal Name and Sequence Prefix before typing; hover or open the field help on Type, Sequence, both dedicated sequences and both communication fields; then read both remark blocks | "**e.g. Customer Invoices**" and "**e.g. INV**" appear as placeholders. The descriptions are Odoo's help word for word, and Sequence's adds the note about there being no drag handle. Each remark block shows its heading (*Also on Odoo's Journal Entries tab* / *Also on Odoo's Advanced Settings tab*) **and its full text**, reads as a note rather than a field, and asks for no input | **Pass** — "e.g. Customer Invoices" and "e.g. INV" as placeholders; Type's and Sequence's help render under the field (Sequence's includes the drag-handle note); the other fields carry theirs behind the ⓘ beside the label on a saved record; both remark blocks render their full text |
| 18 | Odoo side by side | casimir.odoo.com → Invoicing › Configuration › Accounting › Journals, and one journal's form (Sales, Bank) | The same seven journals in the same order, with the same Type and Sequence Prefix; the Sales form shows the same Payment Communications and Dedicated Credit Note Sequence, the Bank form the same Dedicated Payment Sequence. Everything else Odoo shows is in *Not built now* | **Pass** — the tenant lists the same 7 journals with the same Type and Sequence Prefix, and its Sales form carries Dedicated Credit Note Sequence under *Journal Entries* and Payment Communications (Based on Invoice · Full Reference (INV/2024/00001)) under *Advanced Settings*. One difference in order (difference 2) |
| 19 | A journal with a draft entry refuses to archive | Journals → **TEST draft guard** → ⋯ / Archive → confirm. Then reload the view and open the notification list (the bell) | The confirmation appears and the click reports success, but **the row stays in Journals** and `journals.py journal "TEST draft guard"` still shows `active: true`. A notification arrives reading **【Cannot archive this journal】You can not archive a journal containing draft journal entries.** with Odoo's three steps. Difference 7 is exactly this: Odoo would have stopped the save with a dialog | **Pass** — in the browser: the confirmation appeared, the click reported success, and **TEST draft guard is still active** (`active 1`). The notification arrived in HAP's Workflow channel reading 【Cannot archive this journal】 followed by Odoo's message and its three steps, word for word |
| 20 | A journal with no draft entry still archives | Journals → **TEST Journal** → ⋯ / Archive; then Archived → TEST Journal → ⋯ / Unarchive | Archive works as it did in test 15 — the row moves to Archived and `active: false` — and no notification arrives. Unarchive brings it back. Leave it **active** | **Pass** — run through the button's workflow, which archived TEST Journal and unarchived it again with no notification, so the guard lets a journal with no draft entries through. The browser would not open the Archive dialog on this record while the window was being used for other work; that is the test environment, not the app |
| 21 | Odoo's own refusal, side by side | casimir.odoo.com → a journal that has an unposted entry → ⚙ Actions › Archive | Odoo refuses with a dialog carrying the same words. Treat the tenant as read-only: read the dialog and cancel | **Not run** — it would mean pressing Archive on a live journal of a tenant we treat as read-only. The refusal is read from the source instead: `addons/account/models/account_journal.py:686`, message at line 694, which is the wording the notification carries |

### Differences from Odoo seen in testing

1. ~~**One flat form.**~~ **Settled on 16 Sep 2026**: the owner asked for Odoo's two tabs, and each now ends with a
   remark block naming what Odoo shows there and what will bring it (§1, §2). Tests 5–9 and 17 re-run against the
   tabs.
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
7. **The draft-entry refusal is a notification, not a dialog.** Odoo raises a ValidationError that blocks the
   save with the text on screen. HAP has nothing a button workflow can raise: the button's own message is its
   confirmation, shown before the flow runs, and the click always reports "Operation completed". So the journal
   simply stays where it is and Odoo's message arrives as an in-app notification headed *Cannot archive this
   journal* (§2). The guard itself is exact — Active is never written — only the way the user is told differs.

   **The screen pass of 21 Sep 2026 found a second half to this** (`15-ui-conformance.md` §6.6): the refusal also
   drew a toast reading the untranslated **中止** with a warning icon — HAP's own mark of an aborted run, not
   anything this build wrote. **That is fixed**: the update step moved onto the branch's *No* path, the abort node
   was deleted, and a refused Archive now ends the run normally (`approval history` `status` **2**, empty
   `causeMsg`), so **no toast is drawn at all** (§2, *The archive guard*). What is left is the difference above,
   and only that: the user is told the operation completed, the row does not move, and the reason waits in the
   bell. A reviewer re-running test 19 should see **no Chinese anywhere on screen**; if a 中止 toast still
   appears, the workflow was not republished.

### Test records left in the worksheet


- **TEST Journal** (TSTJ, Miscellaneous, Sequence 99, active) — the record the CLI self-check archived and
  unarchived; left active for tests 14–16.
- **TEST long prefix** (Tf798, Miscellaneous, Sequence 99, archived) — created by the API with the 6-character
  prefix `TSTLNG` that the field should have refused; recoded and archived rather than deleted, as the evidence
  for that finding and to give the Archived view a row.

- **TEST Sales** (TSTS, Sales, Sequence 10, archived) — created by test 13 to prove the rule that makes Payment
  Communications required on a Sales journal, with Communication Type **Based on Customer**; archived afterwards.

- **TEST draft guard** (TSTDG, Miscellaneous, Sequence 99, active) — added on 16 Sep 2026 for the archive guard,
  with one draft entry of its own on Invoices (`TEST draft guard`, a Journal Entry, Status Draft, Number "Draft").
  The pair is the evidence for tests 19 and 20: the journal must refuse to archive while that entry is a draft.
  **Leave the entry a draft** — confirming or cancelling it makes the journal archivable and the test moot.

All four are to be removed after sign-off, with the owner's approval, and so is the `TEST draft guard` document on
Invoices. Tests 10–12 left nothing behind: their forms were closed without saving.


## Descriptions rewritten for the app's users (22 Sep 2026)

The owner's rule of 22 Sep 2026: a description in the app says only what the field or button does, for the people using it — no Odoo, no field or model names, no divergences, no build notes. The texts below were rewritten or emptied on the live app and in the builder's constants. The old text is kept here, word for word, because it carried the Odoo references and build reasoning that are no longer in the app.

| Control | Key | Before | After |
|---|---|---|---|
| Communication Standard | desc | You can choose different models for each type of reference. The default one is the Odoo reference. | The format of the payment reference on customer invoices. |
| Active | desc | Set active to false to hide the Journal without removing it. | Untick to hide the journal without deleting it. |
| Sequence | desc | Used to order Journals in the dashboard view. A HAP table has no drag handle, so a journal is moved up or down the list by changing this number. Odoo gives every new journal 10. | Journals are listed by this number, lowest first. Change it to move a journal up or down the list. |
| Default Account | desc | Odoo labels this Bank Account on a Bank journal, Cash Account on Cash, Journal Account on Credit Card, Default Income Account on Sales, Default Expense Account on Purchase, and Default Account on Miscellaneous, where it is used to automatically balance entries. | The journal's main account: the income account on a sales journal, the expense account on a purchase journal, and the account the money is held in on a bank, cash or credit card journal. On a miscellaneous journal it is used to balance entries automatically. |

### Form texts replaced (22 Sep 2026)

The same rule, applied to the text on the form. The two tabs' divider headings and remark blocks named what Odoo
shows there and which bundle brings it; the owner had them rewritten in place for the app's users — nothing hidden
or deleted — in one version-pinned save of the four controls. The old text is kept here word for word, the remark
blocks' HTML as stored.

| Control | Type | Key | Before | After |
|---|---|---|---|---|
| Divider on Journal Entries, `6aa9e869e54d2a34fa4dfe42` | 22 | controlName | Also on Odoo's Journal Entries tab | About Journal Entries |
| Divider on Advanced Settings, `6aa9e869e54d2a34fa4dfe43` | 22 | controlName | Also on Odoo's Advanced Settings tab | About Advanced Settings |
| Journal Entries note, `6aa9eca8e43d174ab37499c2` | 10010 | dataSource | below | below |
| Advanced Settings note, `6aa9eca8e43d174ab37499c3` | 10010 | dataSource | below | below |

The headings are not plain *Journal Entries* and *Advanced Settings*: the two tabs already carry those names, and
`journals.py guard` refuses two controls with one name. `ids.json` keeps both ids under their first keys,
`Journals: Also on Odoo's Journal Entries tab` and `Journals: Also on Odoo's Advanced Settings tab` — keys are never
renamed — and the new names were added beside them.

Journal Entries note, before:

```html
<p><strong>Also on Odoo's Journal Entries tab:</strong> the Invoice report, and — on Bank and Credit Card journals — the Bank Account Number, BIC and Bank Feeds. Odoo also lists this journal's payment method lines on its Incoming and Outgoing Payments tabs.</p><p>The bank fields come with bank accounts, the report with the invoice report templates, and the payment method lines with the Payments bundle.</p>
```

after:

```html
<p>The accounts this journal posts to, and whether its credit notes and payments get their own numbering. Which of these fields show depends on the journal's Type.</p>
```

Advanced Settings note, before:

```html
<p><strong>Also on Odoo's Advanced Settings tab:</strong> Automation (Self Billing), Emails (Email Alias and Send Copy To) and Electronic Data Interchange.</p><p>Self Billing and the EDI settings come with e-invoicing; the alias needs a mail alias and incoming mail.</p>
```

after:

```html
<p>How the payment reference on this journal's customer invoices is set. These settings show on Sales journals only.</p>
```
