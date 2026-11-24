# Claims: who is writing what in EMS right now

**Status: draft, 24 Nov 2026.** The rules are in `PARALLEL-BUILD.md`. In short:

- Add your line and push it **before** the first HAP write of a session; delete it when you finish.
- A claim covers a cluster: the worksheets you change, every worksheet joined to them (Relation, rollup, lookup,
  subform) and every workflow that writes to any of them. If any of those is already claimed, wait or ask.
- Write the worksheet and workflow **names**, not ids, so a claim can be read at a glance.
- A claim past its *Until* time may be taken over only after asking its holder.

## Active claims

| Since | Until | Holder (role, session) | Module | Worksheets | Workflows | Note |
|---|---|---|---|---|---|---|
| | | | | | | |

## Requests to other modules' owners

For a change you need in a module you do not own. The owner answers here, then does it or claims it for you.

| Date | From (role) | To module | What is needed and why | Answer |
|---|---|---|---|---|
| | | | | |

## Recently released

Keep the last ten released claims, newest first, so a builder can see what moved since their last session.

| Released | Holder | Module | What changed | Commit |
|---|---|---|---|---|
| | | | | |
