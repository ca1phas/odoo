# Building EMS with several builders at once

**Status: draft for the owner's review, 24 Nov 2026.** Nothing here is a decision until the owner agrees and
`DECISIONS.md` records it. **EMS** is the app this repo calls ERP Master (renamed "CRM odoo" on 23 Sep, then
"EMS"); the app id has not changed. Companion files: `NEXT-STEPS.md` (the plan from here), `BUILD-RULES.md` (how a module is built), `MODULES.md` (who owns what), `CLAIMS.md` (who is writing
what now), `REFERENCES.md` (where Odoo's facts come from),
`STATE-2026-11-24.md` (what the app and this repo hold today), `TRAPS-HAP-CLI-0.9.md` (traps found since 0.8.31).

## Why this is needed

- **Several people and their AI sessions now change EMS on the same days.** The app has grown past the
  Phase 1 loop: CRM, Sales, Inventory, Invoicing with MyInvois, Activities and Point of Sale. The loop in
  `BUILDING.md` assumes one builder: "one implementation agent at a time builds a worksheet" (`DECISIONS.md`,
  15 Sep).
- **HAP does not protect concurrent edits.**
  - `hap-cli`'s `save_controls` refetches the optimistic-lock version on a conflict and saves anyway
    (`BUILDING.md`, *Worksheets and fields*), so the second save silently overwrites the first.
  - On 7 Oct a multi-agent sprint on Inventory was stopped because sessions that edited related worksheets and
    workflows at the same time broke each other's work.
  - It also happens between people: an administrator deleted Products' Favorite while it was in use
    (`DECISIONS.md`, 17 Sep), and a gap-closing agent had to park its changes while Journals was being edited
    (`DECISIONS.md`, 15 Sep).
- **What exists covers one case.** `CLAUDE.md` (*Saving controls*) protects a worksheet's controls while the owner
  edits them in the browser during a build: append instead of re-saving, and pin the version. Views, rules,
  buttons, workflows, roles and records have no such protection, and nothing covers two builders.
- **The app does not say who owns an object.** 65 of the 83 worksheets and 238 of the 298 workflows are not in
  `build/ids.json`, and 223 workflow names carry no module prefix (read-only scan, 24 Nov 2026, see
  `STATE-2026-11-24.md`). A session cannot tell which objects it may change.

## Roles

Owners and approvers are named by role here. Who holds each role is in `MODULES.md`.

| Role | Does |
|---|---|
| **App Owner** | Sets direction, settles `DECISIONS.md`, approves deletions and anything that crosses modules |
| **Module Owner** | One per menu group. Approves changes to the module's objects and signs off its tests |
| **Builder** | A person or an AI session building in one module, under that module's owner |
| **Reviewer** | Checks a hand-off independently of the builder (`REVIEWING.md`) |
| **App Administrator** | Roles, members, app settings; the only one who edits roles. By default the App Owner holds it |
| **Repo owner** | Reviews and merges into 19.0; repo settings and collaborators |

## The rules

1. **Own before you write.** Write only to objects of the module you build for (`MODULES.md`). For anything
   else, add a request under *Requests* in `CLAIMS.md` for that module's owner, and wait.
2. **Claim before you write.** Add a line to `CLAIMS.md` and push it before the first HAP write of a session;
   remove it when the session ends. A claim covers a **cluster**: the worksheets you change, every worksheet
   joined to them by a Relation, rollup, lookup or subform, and every workflow that writes to any of them. One
   writer per cluster at a time. A claim older than its *Until* time may be taken over after asking its holder.
3. **Append, never round-trip, on a worksheet you do not own.** Add controls with `C.append_controls` (the server
   mints the ids and nothing else is re-sent; `CLAUDE.md`, *Saving controls*). Never save its whole control list,
   its layout, its views, its rules or its roles. On your own worksheets, change an attribute only with a
   version-pinned save and a signature diff (`build/products.py` `step_perms`), as `CLAUDE.md` already requires.
4. **Read before you write, read back after.** Re-read a rule, view, button or workflow just before changing it:
   someone may have changed it since your last read. Read back every write; a success reply is not proof that
   anything was stored.
5. **Record every object you create** in `build/ids.json` under the module's namespace (`"<Module>: <name>"`), in
   the same commit as the change. Never rename existing keys.
6. **Scan at the start and at the end** of every session (*Register scan* below). The diff shows what changed under
   you and what you left without an owner.
7. **No deletions without the App Owner's approval** (`DECISIONS.md`, 15 Sep). Do not rename another module's
   objects to `ZZ obsolete –` either; report them to their owner.
8. **Test data:** `TEST …` names, deleted right after the test, never written onto another module's records. A test
   that changes shared settings (team membership, roles, sequences, default values) needs a claim like any write.
9. **Roles:** only the App Administrator edits roles. Roles created through the V3 API must not be saved in the role
   editor (P43 in `TRAPS-HAP-CLI-0.9.md`). Switch Role Debug off before running scripts: it changes your API rights
   too.

## Session protocol

**Start**
1. Pull the branch you work on; read `MODULES.md`, `CLAIMS.md`, and your module's worksheet documents.
2. Run the register scan and compare it with the last one recorded for your module.
3. Add your claim; commit and push it.

**During**
- One HAP writer per session, one write at a time. Back up anything you replace to `build/backups/` (not
  committed).
- Record ids as you create objects.
- Check each finished step in the UI, not only through the API.

**End**
1. Run the test list of what you changed; read the values back; check them in the UI.
2. Run the register scan again: no object of your module without an owner.
3. Update the worksheet document, the status table in `REVIEWING.md` and `MODULES.md`; remove your claim; commit
   and push.

## Naming, so that ownership shows in the app

| Object | Name | Example |
|---|---|---|
| Workflow | `<Module> - <what it does>` | `CRM - Stage rules`, `Inventory - allocate stock` (Inventory already does this) |
| Sub-process | `<Module> Sub - <what>` | `Inventory Sub - ledger rows for one posted line` |
| Button workflow | The button's name; recorded in the ledger as `<Worksheet>: <button>` | `Leads: Won` |
| HAP-only field | Alias `x_<module>__<name>` | `x_crm__lost_feedback` |
| Odoo field | Odoo's field name as alias, as today | `partner_id` |

No two workflows of one module share a name. Today the app has eleven called *Archive*, eleven *Unarchive*, four
*Confirm* and four *Cancel*.

## Register scan

A read-only scan that lists every object of the app with its owner module (from the ledgers, the alias and the name
prefix), flags objects with no owner, and checks field coverage against Odoo. The scripts already exist, built for
the Odoo Replica (AI) app: `nocoly/native-replica/register/` on branch `claude/odoo-native-replica`.

To use them on EMS:
1. Run `register_scan.py --app <EMS app id>` (read-only).
2. Add EMS's ledgers (`build/ids.json`, and one per module that keeps its own) and the workflow name prefixes
   above to `conventions.json`.
3. Run `register_build.py` with `--coverage` for the modules being checked.

## Questions for the App Owner

1. Adopt these rules for every builder, people and AI sessions alike?
2. Confirm the role holders and the app-wide classification in `MODULES.md` (filled in on 25 Nov).
3. Claims as a file in this repo (simple, needs a push before writing) or as GitHub issues (one per claim)?
4. Rename the existing unprefixed workflows now, or only when their module is next touched?
5. Which branch is the integration branch, and when are the unmerged branches merged or closed
   (`STATE-2026-11-24.md`, *Branches*)?
