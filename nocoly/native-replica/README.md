# Native replica: Odoo's modules rebuilt with HAP's native features

Li Wei and Claude, November 2026. This folder is a second, separate track beside the ERP Master work in `nocoly/`:
- **Plan first.** Every Odoo module gets a plan before anything is built.
- **Native first.** It uses HAP's own field types, views, rules, buttons and workflow nodes; code (code blocks, custom fields, Compute) only with a written reason.
- **Registered.** Every object is tagged with the Odoo module that owns it, so modules can later be split off and sold on their own.

It is here so we can go through it together. Later, if we build modules with Claude, it can work from these files.

**Status (23 Nov 2026):**
- The wave 0 plan (`00-foundation.md`, v2) is waiting for review.
- A first build attempt was deleted, so the build restarts from an empty app ("Odoo Replica (AI)" on Nocoly SaaS).
- Nothing in this folder writes to HAP by itself.

## Start here

| Read | For |
|---|---|
| [`native-catalogue/README.md`](native-catalogue/README.md) | **What HAP can do natively:** the Odoo → native map, limits, workflow run rules, plan gates, live tests still open. Read it before planning any module |
| [`PROGRAMME.md`](PROGRAMME.md) | The programme: goal, principles, waves, how a module is planned and built |
| [`00-foundation.md`](00-foundation.md) | Wave 0 plan, v2: contacts, products, units, pricelists, currencies, activities, all with native fields and nodes |
| [`TEMPLATE.md`](TEMPLATE.md) | The 12-section template every module plan follows |
| [`sept-plan-comparison.md`](sept-plan-comparison.md) | Casimir's September plan and build compared with this one, and what this programme took from it |

## Folders

```
native-catalogue/  fields.md (every field type tried live), workflow-nodes.md (triggers, nodes, the 16 wave 0
                   behaviours designed natively), docs/ (digests of all 359 pages of help.nocoly.com)
catalogue/         the Odoo 20.0 module catalogue (apps, extensions, bridges) and every model and field with its
                   owner module, generated from the open-source code and a local Odoo 20
register/          tools that scan the HAP app read-only and tag each object with its owner module; they also
                   predict what a module's removal would take with it, and report fields not yet covered
odoo20-local/      Docker setup of a local Odoo 20 Community with every open-source app and demo data
```

## Using the tools

- **`register/register_scan.py`** reads the app with hap-cli. Set `ODOO_REPLICA_APP_ID` and `HAP_PROFILE` in your environment first: app ids and profiles are kept out of this repo.
- **`catalogue/odoo_export.py`** reads the local Odoo in `odoo20-local/` (Docker).
- **`native-catalogue/docs/read_pages.py`** reads a local cache of the help pages. Set `NOCOLY_CORPUS` to that SQLite file. The digests themselves need no cache.

## Rules the work follows

- A module is planned and approved before it is built.
- **Every finished step is opened and tested in the HAP UI**: tool output and API success have been wrong before.
- **Native first.** Each native option is tried live before the design is fixed.
- **One builder at a time.** No parallel agents writing to the app; parallel creation caused problems.
- Test sheets and records are deleted right after their test.
- Nothing is deleted without the owner's approval.

**Left out on purpose:** notes from customer projects, internal ids, build ledgers and backups.
