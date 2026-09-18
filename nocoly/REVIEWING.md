# Reviewing a worksheet

We are rebuilding Odoo's apps, one worksheet at a time, inside a Nocoly HAP app called **ERP Master**. Each finished
worksheet comes with a hand-off, and a reviewer checks it against Odoo before it counts as done. This page is
everything a reviewer needs.

## What you need

- **Access to ERP Master** in the Nocoly organisation — https://www.nocoly.com/app/6cb4d051-a33c-4bf9-b56f-5f47f0e85dc9
- **Access to the reference Odoo**, casimir.odoo.com (Odoo saas~19.4) — the reference for every worksheet, Journals
  included. Treat it as read-only: don't create or change records there while reviewing.
- **This folder** of the repository (`nocoly/`, branch `19.0`). Ask Casimir for either account.

## Where things are

| You want | Look in |
|---|---|
| What a worksheet must do, what was built, and the test results | `worksheets/NN-name.md`, or the same content as a web page (link in the table below) |
| What Odoo itself looks like for that model | `reference/odoo-19.4/<model>.md` — fields, form, list, search and records, extracted from the tenant |
| Why something was done a certain way | `DECISIONS.md` |
| How each worksheet compares to Odoo's own screen, side by side | `CROSSCHECK.md`, or the same as a web page: [Beside Odoo's Screens](https://claude.ai/artifact/PWWjfHTutqNycCMcBXZBzn) — the pass of 18 Sep 2026 |
| How the worksheet was built, to rebuild or change it | `BUILDING.md` and `build/<worksheet>.py` |

## How to review

1. **Read section 1, Requirements.** It lists every field with its Odoo field name, the form layout, rules, buttons,
   views and automations, and — just as important — **Not built now**, the things left out on purpose and why. Don't
   report those as missing.
2. **Open the worksheet in Nocoly** and the same model in Odoo, side by side. Check the fields, labels, what is
   required, what shows and hides, and the views.
3. **Run the test list in section 3.** Each test has steps and the expected result; the Result column is what we
   saw. Re-running every test is ideal; at least spot-check the automations — they are the easiest to get subtly
   wrong. Name any records you create `TEST …`.
4. **Read "Differences from Odoo seen in testing".** These are known; say if you disagree with how one is handled.
   `CROSSCHECK.md` adds the screen-by-screen comparison of every worksheet against the tenant, made on 18 Sep 2026.
   Two things it tells you before you start: **Odoo does not render in a background browser tab** — click into its
   window before reading a page — and the tenant's own user, being an Invoicing administrator rather than an
   accounting one, **cannot see any account field on its screens**, so several fields we built are invisible there.
5. **Report back** to Casimir: the worksheet number, the test number or field, what you saw, and what Odoo does.
   A reply of "reviewed, no findings" matters too — it is what marks the worksheet done.

Records named `TEST …` were left in the worksheet for you to inspect; they are removed after sign-off. Every other
record was seeded from the Odoo tenant.

## Status

| # | Worksheet | Odoo model | State | Hand-off |
|---|---|---|---|---|
| 01 | Contacts | `res.partner` | Built, UI-tested 13/13; "Company, Person" display name built and its 6 tests rerun — ready for review | [md](worksheets/01-contacts.md) · [page](https://claude.ai/artifact/JHfvYa7uKiucMfkPnyH2Xu) |
| 02 | Units & Packagings | `uom.uom` | Built, seeded (30 units), UI-tested 18/19 + 1 partly — ready for review | [md](worksheets/02-units-and-packagings.md) · [page](https://claude.ai/artifact/LDoy447FXWYd5gkdDUNDJo) |
| 03 | Products | `product.template` | Built, seeded (14 products), UI-tested 15/17 + 2 partly — ready for review | [md](worksheets/03-products.md) · [page](https://claude.ai/artifact/4fKn4CsuYPTT6zSAMVZFSv) |
| 04 | Product Variants | `product.product` | Built, seeded (one variant per product), UI-tested 16/16 — ready for review | [md](worksheets/04-product-variants.md) · [page](https://claude.ai/artifact/1xo4yDavxjPNwHsUMHFYGV) |
| 05 | Journals | `account.journal` | First build by Teh Li Wei; gaps closed against casimir, seeded (7 journals), UI-tested 18/18, plus the archive guard at the end of Phase 1 — 20/21 — ready for review | [md](worksheets/05-journals.md) · [page](https://claude.ai/artifact/BckMvdNdP9bQhj66UyCdcr) |
| 06 | Invoices | `account.move` | Skeleton by Teh Li Wei; completed against casimir, seeded (3 tenant invoices and their 3 customers), UI-tested 25/25 — ready for review | [md](worksheets/06-invoices.md) · [page](https://claude.ai/artifact/DjdgDLdRmYC44dWoQTvG7T) |
| 07 | Invoice Lines | `account.move.line` | Built, mounted inside Invoices, seeded (the 8 lines of the 3 seeded documents), UI-tested 19/20 + 1 not run (test 3 re-run on 17 Sep); its one open question is now resolved — ready for review | [md](worksheets/07-invoice-lines.md) · [page](https://claude.ai/artifact/7HsZ8L7Ecsp6mDbqGyocCh) |
| 08 | Product Categories | `product.category` | **Bundle 1 of 6.** Built, seeded (7 categories, all 14 products categorised), UI-tested 17/18 + 1 caveat (test 8 re-run on 17 Sep); Products gained the Category it never had, between Cost and Internal Reference — ready for review | [md](worksheets/08-product-categories.md) · [page](https://claude.ai/artifact/5RbMmEJKXzV2Vf3QEdmz99) |
| 09 | Chart of Accounts | `account.account` | **Bundle 2 of 6.** The worksheet with the tenant's 87 accounts, and every account field on Contacts, Products, Product Categories, Journals and Invoice Lines, seeded with the tenant's values and hidden by role as Odoo hides them. UI-tested 28/28 — the role check was run on 18 Sep with role debugging — ready for review | [md](worksheets/09-chart-of-accounts.md) · [page](https://claude.ai/artifact/5boffeaSTZzPnY7xsvjWtN) |
| 10 | Payment Terms | `account.payment.term` (+ `account.payment.term.line`) | **Bundle 3 of 6.** The tenant's ten terms with their lines, as a worksheet and a *Due Terms* table; Invoices' **text stand-in replaced by the relation** (values carried, then the text field deleted), the Due Date computed from the term, the term taken from the customer or vendor; Contacts gained Customer and Vendor Payment Terms. UI-tested 21/22, 1 fails (the two roll-up rules, built and disabled) — ready for review | [md](worksheets/10-payment-terms.md) · [page](https://claude.ai/artifact/Vi6EAAxNgZ9nDiGya4qjh4) |
| 11 | Countries | `res.country` | **Bundle 4 of 6.** Odoo's 251 countries with their ISO code, calling code, VAT label and the two address switches; Contacts' **Country text replaced by the relation** (8 contacts carried, then the text field deleted) and its column, quick filter, Kanban field and both address automations re-pointed. UI-tested 22 pass, 1 fixed during the test | [md](worksheets/11-countries.md) · [page](https://claude.ai/artifact/Cjkq8eoykwMX7L6mshQnUT) |
| 12 | States | `res.country.state` | **Bundle 5 of 6.** Odoo's 2 102 states in 74 countries; **Countries** gained the States list Odoo shows at the foot of its form, and Contacts' **State text was replaced by the relation** (eight contacts carried, then the text field deleted), with Odoo's two onchanges as workflows — a state sets its country, a country clears a state that belongs elsewhere. UI-tested 20 pass, 1 not isolated — the one failure, Odoo's unique code per country, was dropped and rebuilt the same day: a duplicate now saves, then loses its key, gains a **Duplicate code** tick and lands in a *Duplicate codes* view | [md](worksheets/12-states.md) · [page](https://claude.ai/artifact/4pAVaBa4GsmRWuumAAtHmL) |

## Phase 1 · Roles

Set on 16 Sep 2026, at the end of Phase 1 — every worksheet's *Not built now* deferred roles to here. Built by
`build/roles.py`; the ids are in `build/ids.json` under `roles`.

**HAP's five stock roles are renamed to English**, as the house rule asks (`DECISIONS.md`, 15 Sep). Only the label
changed: each keeps its `roleType`, its permission level and its members, and **管理员 → Administrator still holds
Casimir and Teh Li Wei**, unchanged.

| Role | Was | What HAP gives it |
|---|---|---|
| Administrator | 管理员 | Manages every record; **Casimir and Teh Li Wei** |
| Operator | 运营者 | Manages every record |
| Developer | 开发者 | Manages its own records |
| Member | 成员 | Sees every record, manages its own |
| Read-only | 只读 | Sees every record |

**Four business roles were added, one per Odoo accounting group.** Each carries a rule per worksheet; the Odoo
group it stands for is written in its description, checked against
`addons/account/security/account_security.xml` in this checkout. **None of them has a member** — who belongs in
which role is the owner's call, and the two people above stay app administrators as they were.

| Role | Odoo group (and Odoo's own name for it) | Contacts | Countries | States | Units & Packagings | Products | Product Variants | Product Categories | Chart of Accounts | Payment Terms | Payment Term Lines | Journals | Invoices | Invoice Lines |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Accounting Administrator | `account.group_account_manager` — *Administrator*, plus `base.group_allow_export` | full | view | full | full | full | full | full | full | full | full | full | full | full |
| Accountant | `account.group_account_user` — *Show Full Accounting Features* | view · add · edit | view | view · add · edit | view | view | view | view | view | view | view | view · add · edit | view · add · edit | view · add · edit |
| Invoicing | `account.group_account_invoice` — *Invoicing* | view · add · edit | view | view · add · edit | view | view | view | view | view | view | view | **view** | view · add · edit | view · add · edit |
| Accounting Read-only | `account.group_account_readonly` — *Show Accounting Features - Readonly* | view | view | view | view | view | view | view | view | view | view | view | view | view |

Read the three words as HAP stores them, per worksheet:

| | Read | Edit | Delete | + Record | Export |
|---|---|---|---|---|---|
| **full** | every record | every record | every record | yes | Accounting Administrator only |
| **view · add · edit** | every record | every record | — | yes | — |
| **view** | every record | — | — | no | — |

**The matrix was checked in the app on 18 Sep 2026.** HAP can show the app as any role without giving that role
a member — **Select Role**, at the foot of the sidebar — and every cell that matters was read that way. What it
showed: a worksheet a role only *views* has **no + Record**; a **relation picker offers no + Record** either, which
is what keeps an Invoicing user from inventing a country; a field hidden from a role **leaves out its table column
as well as its form field**; and **a tab whose every field is hidden disappears with them** — a contact's
*Invoicing* tab for Invoicing and Accounting Read-only, a product's and a category's *Accounting* tab for
Invoicing. Accounting Read-only does see a journal's accounts, where Invoicing does not, which is the line Odoo
draws with `account.group_account_readonly`. One caution for whoever repeats this: **while a role is being
debugged the same account's API is restricted too**, so leave the role before running any build script.

**States goes the other way (18 Sep 2026), and for the same reason.** Odoo puts `res.country.state` behind **`base.group_partner_manager`** — a contact manager — with all four rights, where `res.country` needs a settings administrator; its own Fed. States list even carries a *New* button where the Countries list does not. So States gets each role's **Contacts** cell: Accountant and Invoicing may add and edit a state, Accounting Read-only may not, and delete stays with Accounting Administrator. Seen on screen with role debugging: as *Invoicing*, States offers **+ Record** and Countries does not.

**Countries is the one worksheet Accounting Administrator does not own (18 Sep 2026).** Odoo's own access list reads `res.country` to everyone and writes it from `base.group_system` alone — the settings administrator, which none of the four accounting groups stands for — and Odoo's Countries list ships with New and Delete switched off. So all four business roles have **view**, and only the app **Administrator** creates, edits or deletes a country (`DECISIONS.md`, 18 Sep). `res.country.state` is not the same: there `group_partner_manager` has all four rights, so the States bundle will not inherit this.

**Chart of Accounts added the first per-field hiding (17 Sep 2026).** Odoo shows account fields only to some
accounting groups, and a HAP role can hide a single field, so the roles now do the same: **Invoicing** does not see
Journals' five accounts, Products' and Product Categories' Income and Expense Account, or Invoice Lines' Account
(Odoo's `groups="account.group_account_readonly"`), and neither **Invoicing** nor **Accounting Read-only** sees a
contact's Account Receivable and Account Payable (`groups="account.group_account_user"`). The tabs those fields leave
empty for a role are hidden with them. Chart of Accounts itself is written by Accounting Administrator alone, as
Odoo's access list has it.

**Only Accounting Administrator may delete**, as the owner asked. Journals is the one cell where Invoicing and
Accountant differ: Odoo's `group_account_invoice` "cannot see accounting related stuff", so an Invoicing user
reads journals and does not change them.

**Exporting is Accounting Administrator's alone.** Odoo keeps exporting behind a group of its own,
`base.group_allow_export`, granted deliberately and *not* implied by an accounting level — so the other three
roles having no export is faithful to Odoo, not an oversight. It is written into Accounting Administrator's own
description beside the accounting group, so nobody has to come back here to find out why.

Three things a reviewer should know:

- **Everything else is at hap-cli's defaults**, the same for all four roles: no view sharing, no import, no batch
  operations, no record sharing, no printing, no record log; record discussion and attachment download on. The
  table above speaks to read, add, edit and delete; export was set deliberately, and nothing else was guessed at.
- **The record scope is what restricts, not the field list.** A fine-grained role reads every field and every
  view back as allowed; "view" is enforced by the record's edit scope being none. So a read-only user sees the
  whole form, greyed.
- **`hap app role list` still prints 管理员 · 运营者 · 开发者.** That command is HAP's V3 endpoint, which
  substitutes its own built-in label for the three typed roles whatever the stored name is. The app's own Roles
  page reads the stored name — checked in the browser on 16 Sep 2026, and it lists **Administrator · Operator ·
  Developer** under *System* and **Member · Read-only** with the four business roles under *Custom*, with
  Casimir and Teh Li Wei on Administrator. `~/.hap-venv/bin/python nocoly/build/roles.py show` prints both
  spellings.

One more thing to know if you read the app log: renaming one of the three typed roles is recorded there as
`编辑了应用基础信息` and `Modified App name "ERP Master" to "ERP Master" and updated App icon`. That is HAP's
boilerplate for saving the app record — the name is the same on both sides, no icon was sent, and the app's name,
icon and colour were read back unchanged. Nothing about the app itself was touched.

## Odoo words and HAP words

| Odoo | HAP / Nocoly |
|---|---|
| model, e.g. `res.partner` | worksheet |
| field | field (a "control"); its alias is the Odoo field name |
| many2one / one2many | Relation field, single / multiple; a two-way Relation shows the reverse side too |
| form view, notebook page | form, tab |
| list, kanban, search filters | table view, gallery view, quick filters and view filters |
| `invisible` / `required` attributes, onchange | interaction rules |
| constraints | validation rules |
| action buttons (⚙ Actions, header buttons) | custom action buttons |
| computed fields, `_fields_sync`, automated actions | formulas, lookups and workflows |
| archive | an Active checkbox with Archive / Unarchive buttons |
