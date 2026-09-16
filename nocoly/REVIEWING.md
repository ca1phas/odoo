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
| 05 | Journals | `account.journal` | First build by Teh Li Wei; gaps closed against casimir, seeded (7 journals), UI-tested 18/18 — ready for review | [md](worksheets/05-journals.md) · [page](https://claude.ai/artifact/BckMvdNdP9bQhj66UyCdcr) |
| 06 | Invoices | `account.move` | Skeleton by Teh Li Wei; completed against casimir, seeded (3 tenant invoices and their 3 customers), UI-tested 24/24 — ready for review | [md](worksheets/06-invoices.md) · [page](https://claude.ai/artifact/DjdgDLdRmYC44dWoQTvG7T) |
| 07 | Invoice Lines | `account.move.line` | Built, mounted inside Invoices, seeded (the 8 lines of the 3 seeded documents), UI-tested 18/20 + 1 partly + 1 not run — ready for review | [md](worksheets/07-invoice-lines.md) · [page](https://claude.ai/artifact/7HsZ8L7Ecsp6mDbqGyocCh) |

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
