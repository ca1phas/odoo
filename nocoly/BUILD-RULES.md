# Rules for rebuilding an Odoo module in HAP

**Status: proposed for EMS, 25 Nov 2026.** These are the working rules of the Odoo Replica (AI) programme, which
rebuilt the foundation (wave 0) and the CRM (Phase A) natively in HAP and tested both. They apply to any module, in
EMS or elsewhere. `PARALLEL-BUILD.md` adds what is needed when several builders share one app, and `CLAUDE.md`
keeps the EMS-specific rules (saving controls, reading records).

The full material is on branch `claude/odoo-native-replica`, folder `nocoly/native-replica/`:

| File | What it gives |
|---|---|
| `HANDOVER.md` | Roles, the first ten of these rules, environment, how to plan and build a module |
| `TEMPLATE.md` | The module plan template |
| `native-catalogue/` | What HAP can do natively (fields, views, rules, buttons, workflow nodes), from tests and the help pages |
| `00-foundation.md`, `00-foundation-build/` | A worked example, start to finish: plan, step scripts, build log, acceptance |
| `01-crm.md`, `01-crm-build/` | The CRM plan, its knowledge file and split guide. Its build scripts, build log and acceptance results (24 Nov) are not in that copy yet |
| `PLATFORM-ISSUES.md` | Platform issues P1–P38, ticket-ready; the later ones are summarised in `TRAPS-HAP-CLI-0.9.md` |

## The rules

1. **Plan first.** No build before the module's plan (`TEMPLATE.md`) is approved by its Module Owner.
2. **Plans are written in stages, not time periods.** Each step says who does it and when it is done; a step may
   carry an effort guide, but the plan never fixes weeks or dates.
3. **Odoo is the reference.** Behaviour, field names and seed data come from the reference recorded for the module
   (`REFERENCES.md`), with the source cited. Aliases are Odoo's field names; HAP-only fields are
   `x_<module>__<name>`.
4. **Nothing of Odoo is cut silently.** Every field of the module's Odoo models is either built or has a written
   decision: skip with the reason, done natively another way, or later in a named phase or module.
5. **Native first.** Native field types (Region, Phone, Money, option sets…), views, rules, buttons and workflow
   nodes. Code blocks, custom fields, plugin views or Compute only with a written reason in the plan.
6. **Forms are laid out.** Short fields three or four per row, dividers for groups, long text full width, never one
   short field alone on a row. New-record forms show only what people fill in; fields kept by workflows are
   read-only. Button dialogs get the same care, and no visibility rule may empty them.
7. **Views native first.** Boards, lists, calendars and dashboards from HAP's own views and charts; a plugin view or
   Compute only where those cannot do it, with the reason in the plan.
8. **Test every step in the UI**, not only by API readback: press every button, open every dialog, check every
   role with Role Debug. Tool success messages have been wrong (a button saved with no target; a filter that was
   ignored).
9. **Read before write.** Other people change the app too: re-read a field, rule, view, button or workflow just
   before changing it, and read back every write.
10. **One writer at a time.** No parallel agents or scripts writing the same worksheets; across modules, claim first
    (`PARALLEL-BUILD.md`).
11. **TEST data.** Test records are named `TEST …` and deleted right after the test. Nothing else is deleted without
    the App Owner's approval.
12. **Owners by role.** Plans, build logs and guides name roles (Module Owner, Builder, App Owner…), not people; who
    holds each role is kept in one place (`MODULES.md`).
13. **Log platform differences.** Anything where the CLI or MCP disagrees with the UI, or that behaves like a bug,
    goes ticket-ready into the platform issues list. Nothing is filed without approval.
14. **Keep the register current.** Every object is recorded in the ledger as it is created; a register scan at the
    end of the module shows no object without an owner.

## A module is done when

1. Its acceptance tests pass, by script (on `TEST …` records, cleaned up) and in the UI, Role Debug included.
2. The register scan shows no object of the module without an owner, and field coverage has nothing open.
3. The build log records each step with its evidence; the module has a knowledge file (facts with sources) and a
   split guide (what removing it takes).
4. A review page is published and the Module Owner has signed off.

## How a module is built

1. **Plan:** read the native catalogue, the module's Odoo source and any earlier build; fill the template (data
   model with Odoo names, form layouts, workflows with their Odoo methods, views, roles, seed data, acceptance
   tests, decisions needed); get it approved.
2. **Build in steps:** sheets and layouts → seed data → workflows → views, pages, roles → acceptance tests. One
   script per step, safe to re-run, recording every id.
3. **After each step:** read it back, check it in the UI, write the build-log section, log any platform difference.
4. **After any workflow change:** run the acceptance scripts again, with Role Debug switched off.
5. **Close:** acceptance tests, register scan with coverage, review page, sign-off.
