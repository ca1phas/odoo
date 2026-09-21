# 17 · Recurring Plans

| | |
|---|---|
| Nocoly app | ERP Master · menu group **CRM** |
| Worksheet | Recurring Plans |
| Odoo model | `crm.recurring.plan` |
| Reference used for this hand-off | `ohyes.odoo.com` plus the Odoo 19 source: the feature is not exposed in the live tenant because recurring revenues are disabled |
| Phase | 2 — CRM worksheet 3 of 4 |
| Status | Empty placeholder repaired into the real model; 0 records; default view repaired. Owner hid its navigation; CLI `displayType=2` and the sidebar's hidden marker confirm this on 21 Sep. Retaining the model remains a design decision. |

## 1 · Delivered scope

The preflight count was zero, so replacing the placeholder controls did not risk business data. The worksheet now contains:

- Plan Name — required title Text
- # Months — Number
- Active — Checkbox, default checked
- Sequence — Number, default 10

No plan was invented and no recurring revenue field was added to Leads while the feature is disabled.

## 2 · Build

| Element | Id |
|---|---|
| Worksheet | `6aacfa43e43d174ab374f862` |
| Plan Name | `6aacfa43e43d174ab374f863` |
| # Months | `6aad104ae54d2a34fa4e581a` |
| Active | `6aad104abd43f55762c75856` |
| Sequence | `6aad104a805aef703286ac3a` |
| Records | 0 |

## 3 · Validation and open decision

The controls and repaired view read back correctly. `field.add` initially ignored alias/default/layout metadata; raw field updates fixed it. The Personal MCP later returned success for moving/hiding the worksheet, but the rendered sidebar did not change. On 21 Sep, the owner hid it manually: CLI now reports `displayType=2`, and the browser's administrator sidebar shows a hidden marker. A non-administrator navigation check is still pending. The colleague's Odoo conformance review recommends deciding whether this disabled-feature worksheet should remain hidden or be removed; no deletion is authorized here.

No product ticket was submitted.
