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
| 07 | Invoice Lines | `account.move.line` | Built, mounted inside Invoices, seeded (the 8 lines of the 3 seeded documents), UI-tested 18/20 + 1 partly + 1 not run; its one open question is now resolved — ready for review | [md](worksheets/07-invoice-lines.md) · [page](https://claude.ai/artifact/7HsZ8L7Ecsp6mDbqGyocCh) |

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

| Role | Odoo group (and Odoo's own name for it) | Contacts | Units & Packagings | Products | Product Variants | Journals | Invoices | Invoice Lines |
|---|---|---|---|---|---|---|---|---|
| Accounting Administrator | `account.group_account_manager` — *Administrator*, plus `base.group_allow_export` | full | full | full | full | full | full | full |
| Accountant | `account.group_account_user` — *Show Full Accounting Features* | view · add · edit | view | view | view | view · add · edit | view · add · edit | view · add · edit |
| Invoicing | `account.group_account_invoice` — *Invoicing* | view · add · edit | view | view | view | **view** | view · add · edit | view · add · edit |
| Accounting Read-only | `account.group_account_readonly` — *Show Accounting Features - Readonly* | view | view | view | view | view | view | view |

Read the three words as HAP stores them, per worksheet:

| | Read | Edit | Delete | + Record | Export |
|---|---|---|---|---|---|
| **full** | every record | every record | every record | yes | Accounting Administrator only |
| **view · add · edit** | every record | every record | — | yes | — |
| **view** | every record | — | — | no | — |

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
