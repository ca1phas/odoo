# Reviewing a worksheet

We are rebuilding Odoo's apps, one worksheet at a time, inside a Nocoly HAP app called **ERP Master**. Each finished
worksheet comes with a hand-off, and a reviewer checks it against Odoo before it counts as done. This page is
everything a reviewer needs.

## What you need

- **Access to ERP Master** in the Nocoly organisation — https://www.nocoly.com/app/6cb4d051-a33c-4bf9-b56f-5f47f0e85dc9
- **Access to the reference Odoo**, casimir.odoo.com (Odoo saas~19.4). Treat it as read-only: don't create or change
  records there while reviewing.
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
| 01 | Contacts | `res.partner` | Built, UI-tested 13/13 — display-name change in progress | [md](worksheets/01-contacts.md) · [page](https://claude.ai/artifact/JHfvYa7uKiucMfkPnyH2Xu) |
| 02 | Units & Packagings | `uom.uom` | Built and seeded (30 units) — UI test in progress | [md](worksheets/02-units-and-packagings.md) |
| 03 | Products | `product.template` | Being built | — |
| 04 | Product Variants | `product.product` | Not started | — |
| 05 | Journals | `account.journal` | Not started | — |
| 06 | Invoices | `account.move` | Not started | — |
| 07 | Invoice Lines | `account.move.line` | Not started | — |

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
