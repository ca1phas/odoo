# Rules for work on the WMS POC

For everyone who works on this POC: people, and AI sessions such as Claude Code or Codex. Read this page and [`STATUS.md`](STATUS.md) before you change anything.

The rules in the repository's root `CLAUDE.md` (Never, Always, Saving controls) apply to the POC app too, except those about ERP Master's build scripts and `nocoly/build/ids.json`.

## Before you start

1. Take the next step from `STATUS.md`. Write your role and the date under **Working on it**, and clear it when you stop.
2. One Builder works in the POC app at a time, and never with several AI agents in parallel. HAP does not protect concurrent edits: a later save silently overwrites an earlier one.
3. Read every element (field, business rule, button, workflow, view, page) again before you change or delete it, even one you made. Someone may have changed it in the UI since.

## Where you may change things

- **The POC app:** yes, within the current stage of [`PLAN.md`](PLAN.md).
- **The EMS master:** never, not even to fix a fault you find. Record the fault in `STATUS.md` for the EMS App Owner.
- **Anything else** (other apps, organisation settings, external services, messages to the client): only after the POC Lead approves that action.
- **Deleting in the POC app:** only what the current stage lists. Anything else is disabled or renamed `ZZ obsolete – …`, and reported.

## How to build

- **Native first.** Use native field types, views, business rules, buttons and workflow nodes. Use a Code Block step, plugin view or Compute only when native cannot do it, and write the reason in `STATUS.md`.
- **Keep the demos simple:** few roles and worksheets. Show what the platform can do, not production depth.
- **Plans go by stage, each with a "done when"**, never by week or date.
- **Stock changes only by posting** (receipt, delivery, scrap, count apply). Never edit Stock Balances or the Stock Ledger directly. See the Inventory build rules in [`EMS-BASELINE.md`](EMS-BASELINE.md#inventory-build-rules).
- **HAP CLI on Windows:** set `PYTHONIOENCODING=utf-8` and `PYTHONUTF8=1`.
- **References:**
  - known CLI traps: `nocoly/TRAPS-HAP-CLI-0.9.md` on branch `claude/ems-parallel-build`;
  - what native HAP can do: `nocoly/native-replica/native-catalogue/` on branch `claude/odoo-native-replica`.

## How to check

- **A success message is not proof.** Read the result back, and check every finished step in the HAP UI with the role that will use it. Never claim a UI check you did not do.
- **A timeout often means the change was made.** Read back before you retry.
- **Keep facts apart:**
  - *Verified*, with the date and how it was checked;
  - *Client request*;
  - *Documented*, from the help pages and not tested here;
  - *Assumption*.

## What goes into this repository

- English only.
- No client name while the repository is public. Use the code name "WMS POC".
- No passwords, API keys, tokens, AppKey/Sign pairs or personal contact details. Write where a secret is kept, never the secret.
- No export packages (`.mdy`) or other binaries. They carry the app's configuration and records.
- Roles, not names (see [`README.md`](README.md#roles)).
- Commit to branch `claude/wms-poc`, or another branch the POC Lead agrees. The repository owner merges.

## When you stop

Update `STATUS.md`:
- what you did;
- what you verified, and how;
- what is still open;
- the next step.
