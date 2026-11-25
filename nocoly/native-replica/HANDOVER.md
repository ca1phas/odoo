# Handover: the native Odoo replica programme

For whoever takes this programme over, or picks up one of its modules. Read this first, then `README.md` (the programme) and the plan of the module you work on. Updated 24 Nov 2026.

## 1. What it is, and where it stands

Odoo 20's modules are rebuilt in Nocoly HAP with native fields, views, rules, buttons and workflow nodes, in one master app, **Odoo Replica (AI)**. Every object is tagged with the Odoo module that owns it, so that a customer copy can drop the modules it does not need (`SPLIT-GUIDE.md`).

| Wave | Module | State |
|---|---|---|
| 0 | Foundation: contacts, companies, products and variants, units, categories, pricelists, currencies, countries, activities | **Built and accepted** (24 Nov 2026): `00-foundation.md`, `00-foundation-build/BUILD-LOG.md`. Open items in §9 |
| 1 | CRM (`crm`, `sales_team`, `utm`) | **Plan approved** (24 Nov 2026), not built: `01-crm.md`, `01-crm-build/` |
| 1 | Invoicing, Sales, Inventory, Point of Sale | Order agreed in `01-wave1.md`; no plans yet |

## 2. Roles

Ownership and decisions are recorded **by role, never by name**, so the work can change hands. Who holds each role is kept outside the repo.

| Role | Responsible for |
|---|---|
| **Programme Lead** | Priorities and wave order; module owners; approving plans at programme level; customer and partner commitments |
| **Module Owner** (one per module) | The module's plan, its open decisions, acceptance and sign-off; confirms deletions and splits that touch the module |
| **Builder** | Builds and tests from an approved plan, keeps the build log, the ledger and the register current. Can be a person or an AI assistant working under the Module Owner |
| **Reviewer** | Checks plans and acceptance evidence before sign-off; runs the checks after a split |
| **App Administrator** | The HAP app's admin rights: roles, members, Role Debug, app settings; approves every deletion of app objects |
| **Platform Liaison** | Turns `PLATFORM-ISSUES.md` items into product tickets once approved, and follows the replies |
| **Data Steward** | Seed and demo data, TEST data hygiene, migrations from other apps |

## 3. Working rules (all modules)

1. **Plan first.** No build before the module's plan (`TEMPLATE.md`) is approved.
2. **Native first.** Native field types, views, rules, buttons and workflow nodes. Code blocks, custom fields, plugin views or Compute only with a written reason in the plan.
3. **Forms laid out.** Short fields three or four per row, dividers for groups, long text full width. New-record forms show only what people fill in. Button dialogs follow the form layout.
4. **Odoo is the reference.** Use the Odoo 20 source and the local Odoo for behaviour, field names and seed data. Aliases are Odoo's field names; new fields are `x_<module>__<name>`.
5. **Test every step in the UI**, not only by API readback. Tool success messages have been wrong (P38 was found only by pressing the button).
6. **TEST data:** test records are named `TEST …` and deleted right after the test. Nothing else is deleted without the App Administrator's approval.
7. **One builder at a time** in the app: no parallel agents or scripts writing the same sheets.
8. **Read before write.** Other people edit the app too: re-read a field, rule, button or flow just before changing it.
9. **Log platform differences** (CLI / MCP vs UI, or anything that behaves like a bug) in `PLATFORM-ISSUES.md`, ticket-ready. Nothing is filed without approval.
10. **Keep the register current.** Ledger entries for every object; a register scan and coverage (0 OPEN) at the end of a module.
11. **Plans in stages.** A plan's steps are stages with a "done when", never fixed weeks or dates; an effort guide per step is fine.
12. **Owners by role.** Plans, logs and guides name roles; who holds each role is kept in one place (`ROLE-HOLDERS.md`, private).
13. **Dialogs and roles are tested too.** No visibility rule may empty a button's dialog (rules apply inside it). Every role is checked with Role Debug, pages included, and Role Debug is switched off before scripts run (it changes the account's API rights).

The same rules, adapted for EMS where several builders share one app, are in the shared repo: `nocoly/BUILD-RULES.md` on branch `claude/ems-parallel-build`.

## 4. Environment

| Tool | Notes |
|---|---|
| HAP app | Odoo Replica (AI), Nocoly SaaS. App and object ids are in the private ledgers (`*-build/ids.json`), never in the repo |
| hap-cli | Python package `hap-cli` (0.9.14 during wave 0). Signed in with a build profile that has admin rights in the app. Scripts read the app id from `lib.py` locally; public copies read `ODOO_REPLICA_APP_ID` and `HAP_PROFILE` from the environment |
| Local Odoo 20 | `external/odoo20-local/` (Docker, Community with every open-source app and demo data): the source for behaviour, demo data and field catalogues |
| Browser | A signed-in browser for UI checks (Role Debug is switched on in the app). CAPTCHAs, one-time codes and passwords are always entered by a person |
| Python | 3.13; run scripts with `PYTHONIOENCODING=utf-8 PYTHONUTF8=1` on Windows |

## 5. Where things are

```
README.md            the programme: goal, sources, waves, decisions
HANDOVER.md          this file
SPLIT-GUIDE.md       how to take modules out of a customer copy
TEMPLATE.md          the 12-section module plan
PLATFORM-ISSUES.md   P1–P47 ticket-ready platform issues, D1–D12 documentation errors (English version for the repo: publish/PLATFORM-ISSUES.en.md)
00-foundation.md     wave 0 plan; 00-foundation-build/ its build (BUILD-LOG.md, scripts, field-decisions.csv)
01-wave1.md          wave 1 order; 01-crm.md the CRM plan; 01-crm-build/ its build (BUILD-LOG.md, scripts, acceptance tests), knowledge base and split guide
native-catalogue/    what HAP can do natively (fields, workflow nodes, the help-site digests)
catalogue/           Odoo 20 modules, models and fields with their owner module
register/            the register scan, coverage and prune prediction
```

## 6. Planning a module

1. Read `native-catalogue/README.md`, the Odoo 20 source of the module, and any earlier build of it (ERP Master, the colleague repo).
2. Fill `TEMPLATE.md`. Include the data model with Odoo names, the form layout of each sheet, the workflows with their Odoo methods, the native UI and its gaps, the roles (Odoo groups → HAP roles), seed data with owner modules, acceptance tests, the register entries and the decisions needed.
3. Keep facts in `<NN>-<name>-build/KNOWLEDGE.md` and the split notes in `<NN>-<name>-build/SPLIT-GUIDE.md`.
4. Get the Module Owner's approval and record it in the plan's status line.

## 7. Building a module

Follow wave 0's pattern (`00-foundation-build/`):
- **Helpers:** `lib.py` (hap calls, ledger), `sheetlib.py` (sheets and fields), `wflib.py` (workflows, conditions, decimals, clearing fields).
- **One script per step:** `step4*` sheets, `step5*` data, `step6*` workflows, `step7*` screens and roles, `step9_form_layouts.py` layouts. Each script is idempotent and writes the ledger.
- **After each step:** read it back, check it in the UI, write a BUILD-LOG section with the evidence, and log any platform difference.
- **End of the module:** acceptance scripts (`acceptance_*.py` style), register scan with coverage, a review page for sign-off, and the Module Owner's sign-off recorded in the plan.

Known traps are in `PLATFORM-ISSUES.md` and in the KNOWLEDGE file of each module. The ones that cost the most time:
- P33: an empty filter value fails a query.
- P36 / P37: roles cannot be changed by the CLI.
- P38: related-record buttons.
- P25: decimals.
- P27: clearing a field.
- P22: "relation not empty" conditions.

## 8. Publishing to the repo

The repo `github.com/ca1phas/odoo` is **public**. The shareable copy goes to `nocoly/native-replica/` on branch `claude/odoo-native-replica`.
- **Script:** `publish/make_public.py` (in the private workspace, never published itself). It copies the listed files and replaces customer and partner names, organisation and app ids, record ids, profiles, e-mail addresses and local paths. It prints every replaced name line for review.
- **English only** (Module Owner, 25 Nov 2026: no mixed languages in the repo). `PLATFORM-ISSUES.md` is published from its English version, `publish/PLATFORM-ISSUES.en.md`: add each new issue there too. Other Chinese text is translated through the script's `ENGLISH` list. The script stops if an issue has no English version or if any published line still contains Chinese.
- **Never published:** ledgers (`ids.json`), backups, scan outputs, exported data, the role-holder list, customer files.
- **Before every push:** check the diff for names and ids; push only with the Module Owner's or Programme Lead's go-ahead.

## 9. Open items

**Wave 0**
- Chained pricelists (Sales needs them).
- Filtered relation pickers (Related Company to companies; line values to the line's attribute).
- Hide Rebuild Variants from employees (role editor, UI).
- Contacts first in the sidebar; map view; rate-history chart; System Tables hidden from members.
- To-do pilot deadline and reminders.
- Two "later:step 5" contact fields.
- Whether to delete the unused role "Member (HAP default)".
- Whether Role Debug stays on.
- Which platform issues to file.

**CRM:** build Phase A (`01-crm.md` §11), then its acceptance tests and review page.

**Next plan:** Invoicing (2a, then 2b), per `01-wave1.md`.
