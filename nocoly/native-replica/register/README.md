# Module register

Answers "which Odoo module owns each object of Odoo Replica (AI)?", so that a module can later be split off and sold on its own. Built in wave 0, step 1 (`00-foundation.md` §10). It follows the format of the 12 Oct Inventory removal manifest: remove / retain / bridges / unresolved.

## How to run

```bash
# 1. Odoo side, once per Odoo version (needs Docker and the local Odoo running)
python -I ../catalogue/odoo_export.py            # writes catalogue/odoo-20.0/odoo-models.csv and odoo-fields.csv

# 2. HAP side, after every build step (read-only hap-cli calls)
python -I register_scan.py                       # writes scans/<YYYY-MM-DD-HHMM>/hap-scan.json

# 3. Join
python -I register_build.py --coverage base,contacts,uom,product,mail --prune product
```

`register_build.py` writes these files into the scan's folder:

| File | What it holds |
|---|---|
| `register.json` | Every object: type, id, name, alias, Odoo model or field, owner module, family, kind, how the owner was found, and the objects it refers to |
| `register.md` | Counts by module and by type, the sheets with their owners, and the unresolved objects |
| `diff.md` | Changes since the previous scan |
| `prune-<module>.md` | What would go if that module and the modules that depend on it were removed. "Bridges to fix" lists the objects that stay but point at removed ones |
| `coverage.md` | The no-feature-cut checklist. Every Odoo field of the given modules, on the models that have a sheet, is marked built, decided (from `*-build/field-decisions.csv`) or OPEN |

## How an owner is found

| Object | Rule (first match wins) |
|---|---|
| Worksheet | ledger → alias `x_<module>__<name>` → alias = Odoo model with `_` for `.` (`res_partner`) → the module that defines the model |
| Field | ledger → HAP system field → alias `x_<module>__<name>` → alias = a field of the sheet's model → the module that declares it |
| View, rule, button, chart | ledger → the sheet's owner (marked "inherit") |
| Workflow | ledger → name prefix `<App> - ` (`conventions.json`) → the trigger sheet's owner |
| Page, option set | ledger |
| Role | built-in role (administrator, developer, operator) → system; otherwise ledger |
| Group | ledger; otherwise "derived": a group goes when all its items go |

**Ledger:** each wave's build keeps `../<NN>-<name>-build/ids.json`, written by the build scripts as they create objects:

```json
{"objects": {"<object id>": {"type": "view", "name": "...", "module": "contacts", "note": "step 6"}}}
```

A later module that adds a view, rule, button or workflow to a shared sheet must record it in its own ledger. Otherwise the register gives it the sheet's owner, and pruning that module would leave it behind.

## Naming conventions this relies on

- Sheet alias = Odoo model with underscores (`product_template`). Field alias = Odoo field name (`list_price`).
- HAP-only sheets and fields: `x_<module>__<name>`, with two underscores after the module. Odoo module names contain underscores themselves (`sale_stock`), so the double underscore keeps the owner unambiguous. Example: `x_mail__plan_launch`.
- Workflow names start with the app: `Contacts - …`, `Products - …`.
- Pseudo-module `system`: HAP built-ins and the programme's own tooling.

## Limits

- HAP has no alias on views, rules, buttons, charts, pages and roles. Their owner comes from the ledger, or for sheet objects is inherited from the sheet.
- References are found by scanning each object's raw JSON for the IDs of other objects in the app. A reference written as plain text, such as a sheet name inside a code step, is not seen.
- The scan does not cover print templates, custom-field code or Compute sites, because hap-cli has no read command for them. They go in the ledger by hand.
- `computed` in the Odoo export is true only for custom (manual) fields. Use `store` = f to find computed fields.
