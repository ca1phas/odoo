# 05 · Journals

| | |
|---|---|
| Nocoly app | ERP Master · menu group **Invoicing** |
| Worksheet | Journals |
| Odoo model | `account.journal` |
| Phase | 1 — core worksheet 5 of 7 |
| Status | **Planned handoff — not built in this branch** |
| Owner | **Teh Li Wei** (reviewing colleague) |
| Reference | Live `casimir.odoo.com` Odoo saas~19.4 tenant; extract and UI validation are required before the HAP build |

This document is the Journals handoff for the ERP Master app. It records the Phase 1 scope,
ownership boundary and build gate; it does not create or modify a HAP object.

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

This branch contains planning and collaboration documentation only. It deliberately does not add a Journals
builder, seed records, HAP IDs or a menu group.

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

The actual HAP build may start only after all of these are true:

1. Products' current CLI write is handed off, while the Journals ownership boundary remains explicit.
2. The correct Nocoly CLI profile, Organization and ERP Master app are confirmed.
3. A CLI preflight confirms that Journals does not already exist and reports worksheet/field/view/rule/workflow
   counts and record counts.
4. The live Odoo Journals form, list, search and actions are read and recorded before translating the plan.
5. Only the new Journals worksheet and its Invoicing menu placement are created through CLI or MCP; Web is not
   used to save HAP changes.
6. CLI/MCP post-check confirms field types, defaults, required/read-only/hidden settings, view columns and
   record count.
7. Web validation checks New, Edit, List, Archived, search, English labels, defaults and the absence of
   `worksheet has been deleted` or permission errors.
8. Every CLI/MCP/UI difference and workaround is added to the limitation register before the worksheet is called
   complete.

### Preflight blocker already observed

The previous read-only HAP preflight using the `fbmy-mingdao` profile returned `401 AuthenticationError`. A
`fbmy-nocoly` profile was not available in that CLI context. This branch records the blocker only: do not run a
Journals create or update until the user re-authenticates the correct Nocoly profile and the Organization/app are
confirmed.

`MCP status: not evaluated` — MCP is not used or claimed to be tested for this handoff.

### Evidence to retain after the build

- CLI preflight and post-check output, including the final record count.
- The live Odoo 19.4 reference for `account.journal` and the UI test notes.
- Any field, option, relation or view that CLI/MCP exposes but the UI does not show, and any UI option that the
  tools cannot create or read.
- The final HAP IDs only after an actual build; this planning commit must not modify `nocoly/build/ids.json`.

## 6 · Non-interference checklist

- [ ] Do not checkout, merge or modify the colleague's active Products branch.
- [ ] Do not modify Contacts, Units & Packagings, Products or their IDs.
- [ ] Do not create or modify HAP objects in this planning commit.
- [ ] Do not add a fake Text field for any deferred relation.
- [ ] Do not add sample Journals records before the live Odoo extract and build approval.
- [ ] Keep all user-visible labels and options in English.
