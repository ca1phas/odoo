# 05 · Journals

| | |
|---|---|
| Nocoly app | ERP Master · menu group **Invoicing** |
| Worksheet | Journals |
| Odoo model | `account.journal` |
| Phase | 1 — core worksheet 5 of 7 |
| Status | **CLI-built and HAP UI-validated — live Odoo source login pending** |
| Owner | **Teh Li Wei** (reviewing colleague) |
| Reference | User-approved `account.journal` core plan; live `casimir.odoo.com` source and HAP form validation are pending |

This document is the Journals handoff and current build record for the ERP Master app. The approved core slice
was built through hap-cli on 15 September 2026. After the user manually completed Nocoly's Tencent CAPTCHA, the
HAP field editor, list, Archived view and unsaved New form were validated. The live Odoo tenant comparison still
requires a manual `casimir.odoo.com` login.

## 1 · Scope and ownership

Journals is being handled by the reviewing colleague in parallel with the colleague's Products work.
Implementation agents must skip this worksheet. The next implementation order remains Product Variants after
Products, followed by Invoices and Invoice Lines once Journals stands. This handoff must not change the existing
Units & Packagings or Products work.

The target location is:

```text
ERP Master
└── Invoicing
    └── Journals
```

This branch now contains the guarded `build/journals.py` builder and the final Journals menu, worksheet and view
IDs. It does not contain seed records. The builder pins the `fbmy-nocoly` profile, refuses to replace a non-empty
worksheet, and does not touch Contacts, Units & Packagings or Products.

## 2 · Dependencies and boundaries

| Area | Phase 1 treatment |
|---|---|
| Contacts | Existing worksheet; do not modify it from this handoff |
| Units & Packagings | Existing worksheet; do not modify it from this handoff |
| Products | Being built by the colleague; do not modify it from this handoff |
| Product Variants | Later worksheet; no dependency for the Journals core slice |
| Invoices and Invoice Lines | Later worksheets; they may relate to Journals after both sides are reviewed |
| Chart of Accounts, Currency and Payments | Optional/deferred bundles; do not create placeholder fields now |

The initial Journals worksheet has no relation fields. In particular, do not create Text substitutes for relations
that cannot be built until a later bundle exists.

## 3 · Requirements

Labels and options below are the English UI target. The live Odoo form and list must be read before implementation;
the final build must follow what the user can actually see in that tenant.

### Fields

| # | Field | Odoo field / concept | Nocoly type | Required | Default | Notes |
|---|---|---|---|---|---|---|
| 1 | Journal Name | `name` | Text · **title field** | yes | — | User-visible journal name |
| 2 | Sequence Prefix | `code` | Text | yes | — | Maximum 5 characters |
| 3 | Type | `type` | Single Select | yes | — | `Sales`, `Purchase`, `Cash`, `Bank`, `Credit Card`, `Miscellaneous` |
| 4 | Active | `active` | Checkbox | — | checked | Technical/archive state; hidden from the normal form |
| 5 | Sequence | `sequence` | Number | — | 10 | Technical ordering field; hidden from the normal form |
| 6 | Communication Type | `invoice_reference_type` | Single Select | — | `Based on Invoice` | `Based on Customer`, `Based on Invoice` |
| 7 | Communication Standard | `invoice_reference_model` | Single Select | — | `Full Reference` | `Full Reference`, `European`, `Numbers only` |

Before build, confirm the exact Odoo labels and option wording in the live tenant. The communication fields may
need the tenant's displayed labels even when the underlying 19.0 source names differ.

### Deferred fields and actions

Do not create the following as Text fields or unrelated placeholders:

- Default Account
- Suspense Account
- Private Share Account
- Profit Account
- Loss Account
- Currency
- Payment Methods
- Bank Account Number
- Journal Items action
- E-invoicing and Email Alias settings

These require future Chart of Accounts, Currency, Invoices, Payment or e-invoicing bundles. Their absence from
the Phase 1 core worksheet is intentional and must not be reported as an accidentally omitted Text field.

## 4 · Views and menu plan

The target menu group is **Invoicing** in the existing ERP Master app. The exact columns and ordering are
subject to the live Odoo UI read, but the initial plan is:

| View | Planned content |
|---|---|
| Journals list | Journal Name, Type, Sequence Prefix; active records; Odoo-aligned ordering |
| Archived list/filter | Archived journals using Active; no separate user-facing Active field on the normal form |
| Form | Journal Name, Sequence Prefix, Type and the communication settings shown by Odoo |

Do not add extra visible Notes, Requested On, Owner or other fields. If a technical value is required later, keep
it read-only or hidden according to the UI-aligned build decision.

## 5 · Build gate and validation checklist

The build was executed after the Products handoff and correct Nocoly profile became available. Current gate state:

1. [x] Products' current CLI write is handed off, while the Journals ownership boundary remains explicit.
2. [x] The correct Nocoly CLI profile, Organization and ERP Master app are confirmed.
3. [x] A CLI preflight confirmed that Journals did not already exist and reported worksheet/field/view/rule/workflow
   counts and record counts.
4. [ ] The live Odoo Journals form, list, search and actions still require browser validation; the browser-control
   approval service was unavailable during the source check.
5. [x] Only the new Journals worksheet and its Invoicing menu placement were created through CLI; Web was not
   used to save HAP changes.
6. [x] CLI post-check confirmed field types, defaults, required/hidden settings, view columns and
   record count.
7. [x] Web validation confirmed Field Editor, New form, defaults, hidden technical fields, Journals/Archived views,
   English labels, all six Type options and `Total 0 row(s)`; no record was saved.
8. [x] Every CLI/MCP/UI difference and workaround found so far was added to the limitation register before the worksheet is called
   complete.

### Authentication blocker resolved

The previous `fbmy-mingdao` preflight returned `401 AuthenticationError`. A later account inventory found and
validated `fbmy-nocoly`; the Nocoly organization and ERP Master app were confirmed before the build. The old 401
is therefore resolved as a wrong-profile/authentication-context issue, not an open Journals blocker.

`MCP status: not evaluated` — MCP was not used or claimed to be tested for this build.

### CLI build result — 15 September 2026

- Menu group: `Invoicing` (`6aa8f3ecbf00c316381dbbe8`).
- Worksheet: `Journals` (`6aa8f5191204328eb1af162a`), alias `account_journal`.
- Fields: 7; records: 0; business rules: 0; custom actions: 0.
- Views: `Journals` (`6aa8f5191204328eb1af162e`) and `Archived` (`6aa8f7074720c515252bf2c8`).
- List columns: Journal Name, Type, Sequence Prefix; sort: Sequence then Journal Name, ascending.
- Deferred relation-dependent fields were not created and there are no Phase 1 Relation controls.
- `Sequence Prefix` carries the English hint `Enter up to 5 characters`, but the installed CLI schema exposes no
  confirmed text maximum-length parameter. The HAP UI accepted `ABCDEF`, so hard enforcement is a confirmed gap.
- HAP Web validation: passed for the built scope. Live Odoo source validation remains pending manual login.

### Evidence to retain after the build

- CLI preflight and post-check output, including the final record count.
- The live Odoo 19.4 reference for `account.journal` and the UI test notes.
- Any field, option, relation or view that CLI/MCP exposes but the UI does not show, and any UI option that the
  tools cannot create or read.
- The final HAP IDs only after an actual build; this planning commit must not modify `nocoly/build/ids.json`.

## 6 · Non-interference checklist

- [x] Did not checkout, merge or modify the colleague's active Products branch.
- [x] Did not modify Contacts, Units & Packagings, Products or their IDs.
- [x] Modified only the approved Journals and Invoicing HAP objects.
- [x] Did not add a fake Text field for any deferred relation.
- [x] Did not add sample Journals records.
- [x] Kept all user-visible labels and options in English.
