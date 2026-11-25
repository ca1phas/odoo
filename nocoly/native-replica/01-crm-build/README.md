# CRM module folder

| | |
|---|---|
| Plan | `../01-crm.md`: **approved** 24 Nov 2026 with its defaults. **Phase A built and tested 24 Nov 2026** (`BUILD-LOG.md`); waiting for the Module Owner's sign-off on the review page <private review page> (`crm-review.html`) |
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

Added during the build:

| File | What |
|---|---|
| `BUILD-LOG.md` | Status per plan step, what was built and why, every deviation, the acceptance results and the fixes they led to |
| `crmlib.py`, `crmwf.py` | Shared helpers (the wave 0 helpers with this ledger) and the workflow helpers, including the raw patches the CLI cannot write (`group_filters`, `multi_relation_any`, `save_compute`) |
| `step1_sheets.py` … `step4_views.py`, `step5_field_decisions.py` | The build, step by step; each step reads the live state first and is safe to re-run |
| `acceptance_crm_core.py`, `acceptance_crm.py` | Re-runnable API acceptance tests with cleanup (`python acceptance_crm.py cleanup`) |
| `field-decisions.csv` | Decision for every Odoo field that is not built (for the register's coverage check) |
| `crm-review.html` | The review page for sign-off (private, not in this copy) |
| `ids.json`, `backups/`, `data/` | Ledger, backups and seed extracts (private, not published) |

## Before changing the build or starting Phase B

1. Read `../01-crm.md`, `KNOWLEDGE.md` §4 and §7, and `../HANDOVER.md` §3 and §7.
2. Make sure the local Odoo 20 is running (seed data), and that a register scan of the app is current.
3. Phase A was built in the plan's order (§11): sheets and layouts → seed data → workflows L1–L14 → views, CRM page, roles, public form → acceptance tests 1–18 and the review page. Re-run `acceptance_crm_core.py` and `acceptance_crm.py` after any change to a flow, and switch Role Debug off first.
