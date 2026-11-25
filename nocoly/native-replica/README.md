# Native replica: Odoo's modules rebuilt with HAP's native features

A second, separate track beside the EMS work in `nocoly/` (the app those files call ERP Master), started in November 2026:
- **Plan first.** Every Odoo module gets a plan before anything is built.
- **Native first.** HAP's own field types, views, rules, buttons and workflow nodes; code (code blocks, custom fields, Compute) only with a written reason.
- **Registered.** Every object is tagged with the Odoo module that owns it, so modules can be split off and sold on their own.
- **Owned by role.** Plans name roles (Programme Lead, Module Owner, Builder, Reviewer, App Administrator, Platform Liaison, Data Steward), never people, so the work can be handed over.

**Status (25 Nov 2026):**
- **Wave 0** (contacts, companies, products and variants, units, categories, pricelists, currencies, countries, activities) is **built and accepted** in the app "Odoo Replica (AI)" on Nocoly SaaS: 21 of 21 acceptance tests, register with 0 unowned objects, 0 Odoo fields without a decision.
- **Wave 1** order is CRM → Invoicing → Sales → Inventory → Point of Sale. **CRM Phase A** (leads and opportunities, pipeline boards, stages, won / lost / restore, activities and plans, meetings, campaigns and sources, the reporting page, three sales roles, the public enquiry form) is **built and tested**: all 18 acceptance tests pass (37 API checks, UI tests with Role Debug), the register has 755 objects with 0 unowned, and no Odoo field is without a decision. It waits for the Module Owner's sign-off. Phase B (lead scoring, assignment, merge, recurring revenue) has not started.
- Nothing in this folder writes to HAP by itself.

## Start here

| Read | For |
|---|---|
| [`HANDOVER.md`](HANDOVER.md) | **Taking over:** roles, working rules, environment, where things are, how to plan and build a module, publishing, open items |
| [`native-catalogue/README.md`](native-catalogue/README.md) | What HAP can do natively: the Odoo → native map, limits, workflow rules. Read it before planning any module |
| [`PROGRAMME.md`](PROGRAMME.md) | The programme: goal, sources, waves, decisions |
| [`00-foundation.md`](00-foundation.md) and [`00-foundation-build/BUILD-LOG.md`](00-foundation-build/BUILD-LOG.md) | Wave 0 plan, and how it was built and tested step by step (with the build scripts beside it) |
| [`01-wave1.md`](01-wave1.md), [`01-crm.md`](01-crm.md) | Wave 1 order; the approved CRM plan |
| [`01-crm-build/BUILD-LOG.md`](01-crm-build/BUILD-LOG.md) | How CRM Phase A was built and tested: every step and deviation, the 18 acceptance tests and the fixes they forced (with the build scripts and acceptance tests beside it) |
| [`01-crm-build/KNOWLEDGE.md`](01-crm-build/KNOWLEDGE.md) | Everything known about CRM: Odoo 20 behaviour rule by rule, access rules, seed data, native mapping and traps, lessons from the September build |
| [`SPLIT-GUIDE.md`](SPLIT-GUIDE.md), [`01-crm-build/SPLIT-GUIDE.md`](01-crm-build/SPLIT-GUIDE.md) | How to take modules out of a customer copy with the register; the CRM part |
| [`PLATFORM-ISSUES.md`](PLATFORM-ISSUES.md) | 47 platform issues found while building (steps, expected and actual result, impact, workaround) and 12 documentation errors |
| [`TEMPLATE.md`](TEMPLATE.md) | The 12-section template every module plan follows |
| [`sept-plan-comparison.md`](sept-plan-comparison.md) | Casimir's September plan and build compared with this one |

## Folders

```
00-foundation-build/ wave 0 build log, field decisions and build scripts (ids replaced: reference, not runnable as is)
01-crm-build/        CRM Phase A build log, field decisions, build scripts and acceptance tests (ids replaced: reference,
                     not runnable as is), knowledge base, split guide, Odoo 20 reference extracts (fields, seed data,
                     access rules)
native-catalogue/    fields.md (every field type tried live), workflow-nodes.md, docs/ (digests of help.nocoly.com)
catalogue/           the Odoo 20.0 module catalogue and every model and field with its owner module
register/            tools that scan the HAP app read-only, tag each object with its owner module, predict a
                     module's removal (prune) and report fields not yet covered
odoo20-local/        Docker setup of a local Odoo 20 Community with every open-source app and demo data
```

## Using the tools

- Set `ODOO_REPLICA_APP_ID` and `HAP_PROFILE` in your environment first; the CRM scripts also read `HAP_ACCOUNT_ID` and `HAP_USER_NAME` (the build account). App ids and profiles are kept out of this repo.
- **`register/register_scan.py`** reads the app with hap-cli; **`register/register_build.py`** builds the register, coverage and prune predictions.
- **`catalogue/odoo_export.py`** reads the local Odoo in `odoo20-local/` (Docker).
- **`native-catalogue/docs/read_pages.py`** reads a local cache of the help pages. Set `NOCOLY_CORPUS` to that SQLite file; the digests themselves need no cache.

## Rules the work follows

- A module is planned and approved before it is built.
- **Every finished step is opened and tested in the HAP UI**: tool output and API success have been wrong before.
- **Native first**, and forms laid out (short fields three or four per row); native views unless native truly cannot.
- **One builder at a time.** No parallel agents writing to the app.
- Test records are named `TEST …` and deleted right after their test. Nothing else is deleted without the App Administrator's approval.

**Left out on purpose:** notes from customer projects, internal ids, build ledgers, backups, exported data, review pages and the list of who holds each role.

**English only.** The Module Owner's quoted instructions are translated from Chinese, and the platform issues are given in English; the ticket drafts for the product team, written in Simplified Chinese, stay outside this repo.
