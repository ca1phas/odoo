# Nocoly — building Odoo's apps from the ground up

This directory sits inside a checkout of **Odoo 19 Community** on purpose. The plan is to
rebuild Odoo's apps as worksheets in a Nocoly HAP tenant, and the only reliable answer to
"how does Odoo actually model this?" is the source you are standing in.

Everything here was derived from this checkout at `7bbce824` (branch `19.0`) and from the
live Nocoly tenant, read-only, on 14 Sep 2026.

```
artifacts/   the three published plans, as standalone HTML
plan/        phases.json — the same plan, machine-readable
tools/       reproducible analysis + a HAP v3 client
```

## Start here

```bash
export HAP_TOKEN=pat_…        # Nocoly personal access token
export HAP_APP=3e596740-d096-42cd-b948-0b62a0220927
export ODOO_LOGIN=…           # only needed to read the reference tenant
export ODOO_API_KEY=…
./nocoly/tools/bootstrap.sh
```

Then open `nocoly/artifacts/ground-up-build.html` in a browser. Drag the phase slider and
toggle the feature bundles — that page is the plan, and it is interactive for a reason.

## The plan in one paragraph

Eleven phases. Phase 1 builds the seven worksheets nothing else can exist without; the other
ten are Odoo's own app groups, added whole. **233 worksheets, ~38 weeks at 40 h/week.**
Within a phase, worksheets and their Relation controls go in one at a time, in dependency
order. `plan/phases.json` carries every worksheet, its Odoo model, its dependencies and the
hours model behind the estimate.

| | |
|---|---|
| Ground-up plan (interactive) | `artifacts/ground-up-build.html` · https://claude.ai/code/artifact/abf0f678-db8a-457e-bf24-a27b945980c8 |
| 中文 | `artifacts/ground-up-build.zh.html` · https://claude.ai/code/artifact/f9143f7a-deeb-4773-ba70-372ac474bb62 |
| Brownfield alternative | `artifacts/expansion-map.html` · https://claude.ai/code/artifact/927b65c6-5401-46f1-80de-3b0f2566568c |

## Why one app at a time works

Odoo's apps do not reference each other. Verify it yourself:

```bash
grep -rniE '\b(stock\.|mrp\.|purchase\.)' addons/sale/models/ | wc -l   # 0
python3 nocoly/tools/manifest_graph.py                                  # 190 bridges, 49%
```

Of 391 business modules, **190 are bridges** — `auto_install` modules that depend on two apps
and exist only to join them. A bridge adds fields through `_inherit` and defines no models of
its own: `sale_stock` appends 13 controls to Orders and 14 to Order Lines without touching a
line of `sale`. The Nocoly equivalent is an **append-only bridge pack**, applied with
`ws.add_controls` and never a controls round-trip.

## What makes cross-app Relations possible

A HAP Relation control stores a bare `dataSource` worksheetId with **no appId**:

```bash
python3 nocoly/tools/hap_v3.py relations 6a9e38ccf363582dd3794504
```

So a worksheet in a new app can point straight at Products in another app and share one row
set. **Still unverified end to end**: whether the form designer's relation picker offers
worksheets from another app, and whether roles traverse the boundary. Test that on a throwaway
app before Phase 1 — every phase after the first assumes it.

## Core is seven worksheets, not sixty

A worksheet is core only if Odoo enforces it with `required=True` from a model that is itself
core, or the concept is unrepresentable without it:

```bash
python3 nocoly/tools/verify_core.py
```

**Core**: Contacts · Units & Packagings · Products · Product Variants · Journals · Invoices ·
Invoice Lines. Everything else in the foundation — Taxes, Chart of Accounts, Product
Categories, Payment Terms, Payments, Activity Types — is an optional bundle. Two findings the
check produced that are easy to get wrong:

- **`account.tax.country_id` is `required=True`** → Taxes cannot stand without Countries.
- **`account.move.currency_id` is `required=True`** → Multi-currency is the one bundle Odoo
  genuinely requires. It stays optional only because a Nocoly Currency control carries its own
  code, so a single-currency build needs no Currencies worksheet.

Nocoly already *is* several things Odoo has to model as tables — `res.users` → Collaborator,
`res.groups` → roles, `mail.message` → record discussion, `ir.attachment` → the Attachment
control. Don't build those.

## Decisions to make before building

- **Invoices Move Type.** Odoo models customer invoices and vendor bills as one `account.move`
  split by `move_type`. Add the Dropdown on day one; a separate Bills worksheet later means two
  numbering schemes and two posting workflows forever.
- **Order lines point at Product Variants, not Products.** Every order line, stock move and
  invoice line in Odoo points at the variant. Pointing them at the template to keep things
  simple is the one decision in this plan that costs a rebuild rather than an append.

## Rules that hold in every phase

1. A worksheet is finished when its Relations are wired — HAP will happily let you point a
   Relation at a worksheet that does not exist yet.
2. Relations point down into Phase 1, never sideways into another app except through a named
   bridge pack built after both apps stand.
3. A bridge pack is its own deliverable. Nocoly has no `auto_install`, so the trigger is a
   checklist: one file per pair naming the controls it appends and the invariants it must not
   break.
4. Every phase ends seeded and read back. Several HAP writes return success and store nothing.

## Related

The brownfield tooling — `lib/` helpers, the existing Sales app's captured IDs, the parity
trackers — lives in `ca1phas/nocoly-odoo-sales`. That repo assumes the current Sales app; this
directory assumes nothing.
