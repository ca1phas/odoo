# `account.journal` — live `ohyes.odoo.com` reference

| | |
|---|---|
| Source | `https://ohyes.odoo.com/odoo/action-372` |
| Inspected | 15 September 2026 |
| Access mode | Authenticated, read-only UI inspection |
| Owner instruction | Use `ohyes.odoo.com` for Journals; do not join or require `casimir.odoo.com` |

No Odoo record was created or saved during this inspection. An unsaved New form was used only to inspect defaults
and client-side input behaviour, then discarded.

## List view

Visible columns: **Journal Name**, **Type**, **Sequence Prefix**, **Default Account**.

| Journal Name | Type | Sequence Prefix | Default Account |
|---|---|---|---|
| Sales | Sales | `INV` | Trade Income |
| Purchases | Purchase | `账单` | Costs |
| Bank | Bank | `BNK1` | Bank |
| Miscellaneous Operations | Miscellaneous | `杂项` | — |
| Exchange Difference | Miscellaneous | `交换` | — |
| Cash Basis Taxes | Miscellaneous | `CABA` | — |
| Tax Returns | Miscellaneous | `TAX` | — |

The tenant therefore contains 7 Journals records. The non-English Sequence Prefix values are tenant data, not UI
labels; the Nocoly worksheet remains English-first and currently has no seeded Journal records by decision.

## New form

The new form starts with blank **Journal Name**, **Type** and **Sequence Prefix**. Its header includes the **Journal
Items** action and the notebook tabs **Journal Entries** and **Advanced Settings**. Type-specific settings are not
fully presented until a Type is selected.

The unsaved New form accepted `ABCDEF` in Sequence Prefix without truncation or an inline validation message.
Server-side save validation was not tested because the reference tenant must remain read-only.

## Sales journal form

Observed on the existing Sales record:

- Journal Name: `Sales`
- Type: `Sales`
- Sequence Prefix: `INV`
- Journal Entries: **Dedicated Credit Note Sequence** checked
- Advanced Settings / Automation: **Self Billing** unchecked
- Advanced Settings / Emails: Email Alias `sales@ohyes.odoo.com`; Send Copy To blank
- Advanced Settings / Payment Communications:
  - Communication Type: `Based on Invoice`
  - Communication Standard: `Full Reference (INV/2024/00001)`

## Visible options

### Type

- Sales
- Purchase
- Cash
- Bank
- Credit Card
- Miscellaneous

### Communication Type

- Based on Customer
- Based on Invoice

### Communication Standard

- Full Reference (INV/2024/00001)
- European (RF83INV202400001)
- Numbers only (202400001)

## Phase 1 Nocoly boundary

The approved Phase 1 worksheet reproduces the seven core fields documented in
[`worksheets/05-journals.md`](../../worksheets/05-journals.md). Default Account and the other account, currency,
payment, e-invoicing, email/action and type-specific settings remain deferred until their owning bundles exist.
They must not be replaced with Text placeholders.

The Nocoly form currently shows Communication Type and Communication Standard in the main body rather than an
Advanced Settings tab. This is a documented Phase 1 layout difference, not a claim of exact full-form parity.

`MCP status: not evaluated` — the Odoo inspection used Web UI and the Nocoly modification used hap-cli only.
