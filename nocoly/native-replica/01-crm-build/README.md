# CRM module folder

| | |
|---|---|
| Plan | `../01-crm.md`: **approved** 24 Nov 2026 with its defaults; not built yet |
| Owners | by role (`../HANDOVER.md` §2): Module Owner, Builder, App Administrator, Programme Lead |
| Odoo modules | `crm`, `sales_team`, `utm` (and Meetings from `calendar`) |

## Files

| File | What |
|---|---|
| `KNOWLEDGE.md` | Everything known about CRM for this build: Odoo 20 behaviour rule by rule with its source methods, access rules, seed data, the native HAP mapping and traps, lessons from the September build, the decisions |
| `SPLIT-GUIDE.md` | How to remove CRM (and `sales_team`, `utm`) from a customer copy |
| `reference/odoo20-crm-fields.csv` | 362 Odoo 20 fields of the CRM, sales team and UTM models, with type, storage, label and owner module |
| `reference/odoo20-crm-seed.json` | Seed and demo data from the local Odoo 20, with the owner module of each row |
| `reference/odoo20-crm-access.csv` | Odoo 20 access rights and record rules of the three modules |

Added during the build (same pattern as `../00-foundation-build/`): `BUILD-LOG.md`, `ids.json` (ledger, private), `field-decisions.csv`, the step scripts, acceptance scripts and the review page.

## Before starting Phase A

1. Read `../01-crm.md`, `KNOWLEDGE.md` §4 and §7, and `../HANDOVER.md` §3 and §7.
2. Make sure the local Odoo 20 is running (seed data), and that a register scan of the app is current.
3. Build in the plan's order (§11): sheets and layouts → seed data → workflows L1–L14 → views, CRM page, roles, public form → acceptance tests 1–18 and the review page.
