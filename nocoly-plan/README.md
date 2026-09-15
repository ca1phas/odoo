# Nocoly × Odoo — build plan and the analysis behind it

Everything here was derived from this repository (Odoo 19.0 Community, `7bbce824`) plus
read-only reads of the live Nocoly HAP tenant. No number in the plan is asserted; each one
has a script in `analysis/` that regenerates it.

## What's in here

| Path | What it is |
|---|---|
| `pages/` | The three published pages, self-contained HTML. Open in any browser. |
| `analysis/` | The scripts that produced every figure in those pages. |
| `data/` | Their output — the parsed manifest graph and the derived tables. |
| `sources/` | Page sources, so the pages can be rebuilt instead of hand-edited. |

## The pages

- **`pages/ground-up.html`** — the greenfield plan. 11 phases, 233 worksheets, ~38 weeks at
  40 h/week. Interactive: drag the phase slider, toggle the 17 feature bundles, hover any
  brick to see what it sits on and what sits on it.
- **`pages/ground-up-zh.html`** — the same page in Chinese. Odoo and Nocoly terms stay in English.
- **`pages/expansion-map.html`** — the brownfield plan, for extending the existing Sales app
  rather than starting over. Also holds the 74-edge connectivity ring and the 49-app catalogue.

Published copies (same content, shareable):
- Ground-Up Build — https://claude.ai/code/artifact/abf0f678-db8a-457e-bf24-a27b945980c8
- 从零搭建 — https://claude.ai/code/artifact/f9143f7a-deeb-4773-ba70-372ac474bb62
- Expansion Map — https://claude.ai/code/artifact/927b65c6-5401-46f1-80de-3b0f2566568c

## Reproducing the analysis

Run from the repository root. Python 3 only, no dependencies.

```bash
python3 nocoly-plan/analysis/extract.py          # parse 662 __manifest__.py → data/manifests.json
python3 nocoly-plan/analysis/bridges.py          # 190 bridge modules = 49% of business modules
python3 nocoly-plan/analysis/connections.py      # per-app requires / uses / connects-to
python3 nocoly-plan/analysis/verify_core.py      # which models carry required=True
python3 nocoly-plan/analysis/verify_bundles.py   # proves each optional bundle is really optional
python3 nocoly-plan/analysis/timeline3.py        # the effort model and the phase timeline
```

`extract.py` writes to an absolute scratchpad path — change `SP` at the top to
`nocoly-plan/data` before running, and the rest will read from there.

## The findings the plan rests on

1. **Odoo's apps do not reference each other.** `grep -rniE '\b(stock\.|mrp\.|purchase\.)' addons/sale/models/`
   returns zero. Every cross-app feature is a separate `auto_install` bridge module that
   `_inherit`s and *appends* — 190 of them, 49% of all business modules, and not one defines a
   new model.
2. **Only 7 worksheets are structurally core** — Contacts, Units & Packagings, Products,
   Product Variants, Journals, Invoices, Invoice Lines. The other 29 foundation worksheets are
   optional features, most of them behind an Odoo settings toggle. `verify_core.py` and
   `verify_bundles.py` print the evidence.
3. **HAP Relation controls are not app-scoped.** A relation stores a bare `dataSource`
   worksheetId with no appId, so a worksheet in a new app can point at one that already exists.
   *Still to be confirmed in the form designer — see below.*

## Rebuilding a page after editing it

```bash
cd nocoly-plan
cat sources/head3.html sources/gbody1.html sources/gbody2.html > pages/ground-up.html
printf '<script>\n' >> pages/ground-up.html
cat sources/walldata.js sources/wall.js >> pages/ground-up.html
printf '</script>\n' >> pages/ground-up.html
```

Same for the Chinese page with the `-zh` sources.

## Before Phase 1 — still open

- **Prove the cross-app Relation in the UI.** Throwaway app, throwaway worksheet, one Relation
  control pointed at Products, set via `ws.add_controls`, read back, then opened in the form
  designer. Everything downstream assumes the picker offers worksheets from another app. If it
  refuses but the API accepts, build relations through the API.
- **Check role traversal** across the app boundary.
- **Decide the Move Type append on Invoices** — one Dropdown now, or two worksheets forever.
