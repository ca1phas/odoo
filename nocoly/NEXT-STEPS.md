# Next steps for EMS

**Status: proposed 24 Nov 2026, for the App Owner.** This updates the September plan (`plan/phases.json`,
`README.md`) for how EMS is built now: several people and their AI sessions, one shared app, and no live reference
tenant. Why: `REVIEW-2026-11-24.md`. Rules: `PARALLEL-BUILD.md`.

## Week 1: get ready (no writes to EMS)

| # | Step | Who | Done when |
|---|---|---|---|
| 1 | Read this branch with your AI (prompt below) | Every builder | Each builder has read it and raised questions |
| 2 | Agree `PARALLEL-BUILD.md`; confirm the owners and the app-wide classification in `MODULES.md` (filled in by role on 25 Nov) | App Owner, Module Owners | The decision is in `DECISIONS.md` |
| 3 | Merge this branch and the two up-to-date branches into 19.0; delete the two already merged (`STATE-2026-11-24.md`, *Branches*) | Repo owner | 19.0 holds them; an agent reading 19.0 sees everything |
| 4 | Set up the local Odoo 20 (`tools/odoo20-local/`) | Every builder | The sign-in page answers; the demo counts match its README |
| 5 | Set up the online instance for your module (`REFERENCES.md`) | Each Module Owner | The module is installed; captures start in `reference/` |
| 6 | Decide the reference for each module | App Owner | The *Reference* column in `MODULES.md` is filled |
| 7 | Make this repo private and add the builders as collaborators (agreed 25 Nov) | Repo owner | Only collaborators can open it |
| 8 | List which build steps may run again on today's worksheets, then add "EMS" to `APP_NAMES` | Repo owner | The list is in `BUILDING.md`; the scripts run again |

## Weeks 2–3: read-only re-review, one module at a time

Order (dependencies first): Contacts → Products → Invoicing → Sales → CRM → Activities → Inventory → Point of Sale.
Each builder reviews one module at a time; two builders may review different modules at once.

For each module:
1. **Register scan** of EMS (`PARALLEL-BUILD.md`, *Register scan*): every object attributed; the rest listed for the
   owner.
2. **Conformance** against the module's reference: fields, views, rules, buttons, workflows, then Odoo's behaviour
   rule by rule. `worksheets/14-crm-conformance.md` is the model.
3. **Tests:** run the module's existing test list on `TEST …` records, in the UI and by readback. This writes test
   records, so it needs a claim and the owner's go-ahead.
4. **Verdict** with an estimate: keep, a fix list, or rebuild.

Output per module: `worksheets/NN-<module>-review.md`, a review page, an updated row in `MODULES.md`.

## After the review: changes, one module at a time

1. The Module Owner approves the fix list or the rebuild plan.
2. The builder claims the cluster (`CLAIMS.md`), builds with a re-runnable script, records every id, reads every
   write back and tests in the UI.
3. The module closes with its test list, a register scan with no unowned objects, an updated hand-off and the
   claim released.
4. `plan/phases.json` is re-based on the result: what is built, which planned worksheet it is, what is left.

## Material you can reuse

The Odoo Replica (AI) programme rebuilds Odoo's modules natively in a separate app with the same organisation.
Its public copy is on branch `claude/odoo-native-replica`, folder `nocoly/native-replica/`:

- per-module plans and knowledge files;
- the register scripts (`register/`), which also work on EMS;
- `PLATFORM-ISSUES.md`, with every platform issue found and steps to reproduce it.

Its CRM (Phase A, accepted in tests on 24 Nov 2026) is a reference for what a rebuilt CRM gives.

## For your AI session (paste this)

```text
Read the EMS hand-over from the repo github.com/ca1phas/odoo, branch claude/ems-parallel-build
(or 19.0 once it is merged). Check out only CLAUDE.md and nocoly/ (sparse checkout; the rest is Odoo itself).

Read, in this order: CLAUDE.md, nocoly/NEXT-STEPS.md, nocoly/REVIEW-2026-11-24.md,
nocoly/PARALLEL-BUILD.md, nocoly/MODULES.md, nocoly/CLAIMS.md, nocoly/STATE-2026-11-24.md,
nocoly/REFERENCES.md, nocoly/TRAPS-HAP-CLI-0.9.md, nocoly/tools/odoo20-local/README.md.
Then skim nocoly/BUILDING.md by section, and nocoly/DECISIONS.md.

Then tell me, in a short list:
1. which module I own, according to MODULES.md (or that it is not filled in yet);
2. the rules you must follow before any write to EMS;
3. what I have to set up (local Odoo 20, online instance) and the commands;
4. my next step from NEXT-STEPS.md.

Until the owners are filled in and I have a claim in CLAIMS.md, do not write anything to the EMS app:
read only. Never write to the separate Sales app named in CLAUDE.md. Never subscribe to anything in Odoo.
```
