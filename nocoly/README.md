# Nocoly — building Odoo's apps from the ground up

We are rebuilding Odoo's apps, worksheet by worksheet, inside one Nocoly HAP app, **ERP Master**
(https://www.nocoly.com/app/6cb4d051-a33c-4bf9-b56f-5f47f0e85dc9). The reference is the company's live Odoo,
casimir.odoo.com (Odoo saas~19.4). This directory sits inside a checkout of Odoo 19 Community on purpose: the source
is where Odoo's behaviour is read from.

## Start here

| You are | Read |
|---|---|
| **Reviewing a worksheet** | [`REVIEWING.md`](REVIEWING.md) — access, how to review, the status of every worksheet |
| **Building or changing one** | [`BUILDING.md`](BUILDING.md) — setup, the per-worksheet loop, conventions, HAP traps |
| **Asking why** | [`DECISIONS.md`](DECISIONS.md) — every decision, with its reason and who made it |

```
worksheets/  one hand-off per worksheet: requirements, build, test results
reference/   read-only extracts of each Odoo model from casimir.odoo.com (saas~19.4)
build/       the scripts that build each worksheet with the hap CLI, and ids.json
artifacts/   published pages: worksheet review pages, and the original plans
tools/       bootstrap, the Odoo extract snippet, and the checks behind the plan
plan/        phases.json — the original plan, machine-readable
analysis/    the one-off scripts behind the figures in the plan pages
data/        their output
sources/     page sources the two ground-up plan pages are built from
```

## Where the build stands

Phase 1 — the seven core worksheets — is in progress, one worksheet at a time; optional feature bundles are excluded
for now. The per-worksheet state, with links to each hand-off, is kept in one place: the **Status** table in
[`REVIEWING.md`](REVIEWING.md).

## Background: the original plan

Published 14 Sep 2026 and derived from this checkout at `7bbce824`. Where it differs from `DECISIONS.md` — notably,
it planned one HAP app per Odoo app — the decisions win.

| | |
|---|---|
| Ground-up plan (interactive) | `artifacts/ground-up-build.html` · https://claude.ai/code/artifact/abf0f678-db8a-457e-bf24-a27b945980c8 |
| 中文 | `artifacts/ground-up-build.zh.html` · https://claude.ai/code/artifact/f9143f7a-deeb-4773-ba70-372ac474bb62 |
| Brownfield alternative | `artifacts/expansion-map.html` · https://claude.ai/code/artifact/927b65c6-5401-46f1-80de-3b0f2566568c |

Eleven phases. Phase 1 builds the seven worksheets nothing else can exist without; the other ten are Odoo's own app
groups, added whole — **233 worksheets, ~38 weeks at 40 h/week**. `plan/phases.json` carries every worksheet, its Odoo
model, its dependencies and the hours model behind the estimate.

### Why one app at a time works

Odoo's apps do not reference each other. Verify it yourself:

```bash
grep -rniE '\b(stock\.|mrp\.|purchase\.)' addons/sale/models/ | wc -l   # 0
python3 nocoly/tools/manifest_graph.py                                  # 190 bridges, 49%
```

Of 391 business modules, **190 are bridges** — `auto_install` modules that depend on two apps and exist only to join
them. A bridge adds fields through `_inherit` and defines no models of its own: `sale_stock` appends 13 fields to
Orders and 14 to Order Lines without touching a line of `sale`. The Nocoly equivalent is an **append-only bridge
pack**: fields added to existing worksheets with `hap worksheet add-fields`, never a full control round-trip.

### Core is seven worksheets, not sixty

A worksheet is core only if Odoo enforces it with `required=True` from a model that is itself core, or the concept is
unrepresentable without it:

```bash
python3 nocoly/tools/verify_core.py
```

**Core**: Contacts · Units & Packagings · Products · Product Variants · Journals · Invoices · Invoice Lines. Everything
else in the foundation — Taxes, Chart of Accounts, Product Categories, Payment Terms, Payments, Activity Types — is an
optional bundle. Two findings the check produced that are easy to get wrong:

- **`account.tax.country_id` is `required=True`** → Taxes cannot stand without Countries.
- **`account.move.currency_id` is `required=True`** → Multi-currency is the one bundle Odoo genuinely requires. It
  stays optional only because a Nocoly Currency control carries its own code.

Nocoly already *is* several things Odoo has to model as tables — `res.users` → Member fields, `res.groups` → roles,
`mail.message` → record discussion, `ir.attachment` → the Attachment field. Don't build those.

### Rules that hold in every phase

1. A worksheet is finished when its Relations are wired — HAP will happily let you point a Relation at a worksheet
   that does not exist yet.
2. An app's worksheets relate down into Phase 1, never sideways into another app except through a named bridge pack
   built after both apps stand.
3. A bridge pack is its own deliverable: one file per pair naming the fields it appends and the invariants it must not
   break.
4. Every phase ends seeded and read back. Several HAP writes return success and store nothing.

## Reproducing the analysis

Run from the repository root. Python 3, no dependencies.

```bash
python3 nocoly/analysis/extract.py          # parse all 662 __manifest__.py → data/manifests.json
python3 nocoly/analysis/connections.py      # per-app requires / connects-to → data/connections.json
python3 nocoly/analysis/fundamentals.py     # which modules reference each model → data/refs.json
python3 nocoly/analysis/verify_bundles.py   # evidence that each optional bundle really is optional
python3 nocoly/analysis/timeline3.py        # the hours model → data/hours.json
python3 nocoly/analysis/gen_svg.py          # expansion map's connectivity ring → data/net.svg
python3 nocoly/analysis/gen_bricks.py       # expansion map's build diagram → data/bricks.svg
```

The other scripts in `analysis/` print a table and write nothing. Re-run on 15 Sep 2026, `connections.json`,
`hours.json` and `refs.json` came back with the same content, and both SVGs match the ones embedded in
`expansion-map.html` byte for byte. Three data files have no generator left — `edges.json`, `matrix.json` and
`apps_slim.json` came from scratch scripts that were not kept.

## Rebuilding a plan page

The two ground-up pages are concatenated from `sources/`; the result is byte-identical to `artifacts/`:

```bash
cd nocoly
cat sources/head3.html sources/gbody1.html sources/gbody2.html > artifacts/ground-up-build.html
printf '<script>\n' >> artifacts/ground-up-build.html
cat sources/walldata.js sources/wall.js >> artifacts/ground-up-build.html
printf '</script>\n' >> artifacts/ground-up-build.html
```

Same for `ground-up-build.zh.html` with the `-zh` sources. `expansion-map.html` has no sources; edit it in place.

## Related

The brownfield tooling — `lib/` helpers, the existing Sales app's captured ids, the parity trackers — lives in
`ca1phas/nocoly-odoo-sales`. That repo assumes the current Sales app (`3e596740-d096-42cd-b948-0b62a0220927`);
this directory assumes nothing about it.
