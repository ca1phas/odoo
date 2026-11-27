# WMS POC

This folder is the working file for a client's proof of concept (POC): a warehouse management system (WMS) on Nocoly (HAP), plus four areas the client asked to see. It is written so that the next person, or their AI session, can pick the work up without the earlier chats.

**Client name:** not written in this repository while it is public. "WMS POC" is the code name; ask the POC Lead which client it is.

**Status on 27 Nov 2026:** Stage 1 has started. A fresh export of the EMS app was made for the POC; it has not been imported yet. Details are in [`STATUS.md`](STATUS.md).

## Start here

| You want to | Read |
|---|---|
| Know the rules before you change anything | [`AGENTS.md`](AGENTS.md) |
| See where the work stands and take the next step | [`STATUS.md`](STATUS.md) |
| See the stages, what each one shows and when it is done | [`PLAN.md`](PLAN.md) |
| Know what the client asked for and what is still unknown | [`REQUIREMENTS.md`](REQUIREMENTS.md) |
| Know what the starting app can and cannot do | [`EMS-BASELINE.md`](EMS-BASELINE.md) |

## The project in brief

- The client's core need is a WMS with IoT integration. *(Client request, passed on by the Account Lead, 27 Nov 2026)*
- For the POC the client asked to see four more areas: e-commerce integration by API, daily exchange rates by API, a portal for suppliers or customers, and finance functions with a management dashboard. *(Client request, 17 Nov 2026)*
- The client's project lead has seen a demo of the current app and was happy with it. The next step is a full presentation in Chinese for the client's management. *(Account Lead, 27 Nov 2026)*
- Nocoly runs the POC, and the project after it, itself. No implementation partner is involved. *(27 Nov 2026)*

## How the work is set up

- **Starting point:** EMS, a Nocoly (HAP) app modelled on Odoo's standard modules. Its Inventory module is the WMS core. The rest of `nocoly/` documents how EMS was built; older files there call it ERP Master or CRM odoo, its earlier names.
- **The POC runs in its own copy of EMS.** The EMS master is shared by several module owners and is never changed for the POC.
- **The full system is not planned as a continuation of EMS.** Working assumption, not final: after the POC it is designed from the client's processes and volumes, with EMS as a reference ([`PLAN.md`](PLAN.md), Stage 4).

## Roles

Files here name roles, not people. The POC Lead keeps the list of who holds each role.

| Role | Does |
|---|---|
| **Account Lead** | Talks to the client, in Chinese; agrees dates and scope; presents |
| **POC Lead** | Owns the plan; approves each stage and any change outside the POC app |
| **Builder** | Builds and tests in the POC app, usually with an AI session; one Builder at a time |
| **Reviewer** | Checks each finished step in the HAP UI before it counts as done |
| **EMS App Owner** | Owns the EMS master; is asked before any export from it or change to it |

## Files

```
README.md         this page
AGENTS.md         rules for people and AI sessions working on the POC
CLAUDE.md         loads AGENTS.md for Claude Code
STATUS.md         current state, environment, log, findings
PLAN.md           stages with "done when", demo scope, decisions, risks
REQUIREMENTS.md   what the client asked for, what is unknown, questions to ask
EMS-BASELINE.md   what EMS does, its limits, module dependencies, build rules
```

Everything in this repository is in English.
