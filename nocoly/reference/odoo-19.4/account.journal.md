# account.journal — as on casimir.odoo.com (Odoo saas~19.4+e)

Read-only extract, 15 Sep 2026: `fields_get`, `ir.model.fields.modules`, `get_views` (form, list, kanban, search), the
window actions, `default_get`, `_order`, SQL constraints and every journal (7, archived included). The views are what
the tenant's admin user is served, so parts restricted to Accounting groups (`account.group_account_readonly`) are
absent from the form, notably the Default / Suspense / Profit / Loss account fields and Currency. Behaviour the
tenant cannot show comes from the Odoo 19.0 source, `addons/account/models/account_journal.py`.

An earlier Journals hand-off used the colleague's own tenant, ohyes.odoo.com; those notes are kept in
`reference/ohyes/account.journal.md`. **This file is the reference** (owner, 15 Sep 2026).

Menu: Invoicing › Configuration › Accounting › **Journals** — action *Journals*, `list,kanban,form`, no default filter.
The Invoicing dashboard is a second action on the model (*Dashboard*, `kanban,form`, default filter Favorites).

## Fields that matter for Phase 1 (module `account` unless noted)

| Field | Label | Type | Req | Default | Help / notes |
|---|---|---|---|---|---|
| `name` | Journal Name | char | yes | — | Form: `required="not type"`; on create an empty name takes `name_placeholder` — "Customer Invoices (1)", "Vendor Bills (1)", "Cash (1)", "Bank (1)", "Credit Card (1)", "Miscellaneous Operations (1)", the number being the code's trailing digits (`_compute_name_placeholder`, `create`) |
| `code` | Sequence Prefix | char, **size 5** | yes | computed from Type when empty (`_compute_code` → `_get_next_journal_default_code`) | "Shorter name used for display. The journal entries of this journal will also be named using this prefix by default." Placeholder "e.g. INV". SQL constraint `account_journal_code_company_uniq` unique (company_id, code): **"Journal codes must be unique per company."** |
| `type` | Type | selection | yes | — | `sale` Sales · `purchase` Purchase · `cash` Cash · `bank` Bank · `credit` Credit Card · `general` Miscellaneous. Help: "Select 'Sale' for customer invoices journals. Select 'Purchase' for vendor bills journals. Select 'Cash', 'Bank' or 'Credit Card' for journals that are used in customer or vendor payments. Select 'General' for miscellaneous operations journals." |
| `active` | Active | boolean | | true | "Set active to false to hide the Journal without removing it." Archive is refused while the journal has draft entries (`_check_auto_post_draft_entries`) |
| `sequence` | Sequence | integer | | 10 | "Used to order Journals in the dashboard view"; the list's drag handle |
| `invoice_reference_type` | Communication Type | selection | yes | `invoice` | `partner` Based on Customer · `invoice` Based on Invoice. "You can set here the default communication that will appear on customer invoices, once validated, to help the customer to refer to that particular invoice when making the payment." |
| `invoice_reference_model` | Communication Standard | selection | yes | `odoo` | `odoo` Full Reference (INV/2024/00001) · `euro` European (RF83INV202400001) · `number` Numbers only (202400001). "You can choose different models for each type of reference. The default one is the Odoo reference." |
| `refund_sequence` | Dedicated Credit Note Sequence | boolean | | — | "Check this box if you don't want to share the same sequence for invoices and credit notes made from this journal". Shown for Sales and Purchase only |
| `payment_sequence` | Dedicated Payment Sequence | boolean | | — | "Check this box if you don't want to share the same sequence on payments and bank transactions posted on this journal". Shown for Bank, Cash and Credit Card only |
| `show_on_dashboard` | Show journal on dashboard | boolean | | true | The dashboard's *Favorites* filter |
| `color` | Color Index | integer | | 0 | Dashboard card colour |
| `company_id` | Company | many2one res.company | yes | the company | Read-only, invisible |

Other fields on the model, all outside Phase 1: `default_account_id` Default Account, `suspense_account_id`,
`non_deductible_account_id` Private Share Account, `profit_account_id`, `loss_account_id` (Chart of Accounts);
`currency_id` (Currency); `inbound/outbound_payment_method_line_ids`, `available_payment_method_ids` (Payments);
`bank_account_id`, `bank_statements_source` Bank Feeds, `bank_name`, `bank_account_number`, `bank_bic` (bank accounts);
`journal_group_id` Ledger; `restrict_mode_hash_table` Secure Posted Entries with Hash; `is_self_billing` Self Billing;
`alias_*` Email Alias and `incoming_einvoice_notification_email` Send Copy To (emails, e-invoicing);
`invoice_template_pdf_report_id` Invoice report; `sequence_override_regex`; the `account_online_synchronization` fields;
dashboard computations (`kanban_dashboard`, `entries_count`, `has_entries`, `has_posted_entries`,
`has_sequence_holes`, …); mail and activity fields.

## Form

```
[ribbon "Archived" when not active]
Journal Name (h1, required when no Type)
group: Type · Sequence Prefix (placeholder "e.g. INV")      | Ledger (only when the company has ledgers)
notebook
  Journal Entries
    Dedicated Credit Note Sequence   — invisible unless Type in (Sales, Purchase)
    Dedicated Payment Sequence       — invisible unless Type in (Bank, Cash, Credit Card)
    Invoice report                   — only when several report templates exist
    [Bank only] Bank Account Number · BIC · Bank Feeds (radio, required for Bank)
    [Credit Card only] Bank Feeds (radio, required)
  Incoming Payments / Outgoing Payments — Bank, Cash, Credit Card only (payment method lines)
  Advanced Settings — invisible for Bank and Cash
    Automation: Self Billing (Sales, Purchase)
    Emails: Email Alias, Send Copy To (Miscellaneous, Sales, Purchase)
    Payment Communications — Sales only:
      Communication Type
      Communication Standard — invisible when Communication Type is 'none'
chatter
```

## List

Drag handle (`sequence`) · **Journal Name** · **Type** · Ledger (optional, hidden) · **Sequence Prefix** (optional,
shown) · **Default Account** (optional, shown) · Active (optional, hidden). Header button *New* opens a create wizard
(`account_accountant.action_journal_create_wizard`).

## Kanban and search

- Kanban (the Journals action's second view): name and type only.
- Search field: Journal (name; `_rec_names_search` is name and code). Filters: Favorites (show on dashboard) |
  Sales · Purchases · Liquidity (Cash, Bank, Credit Card) · Miscellaneous | Archived.

## Defaults, order, constraints

- `default_get`: active true · sequence 10 · Communication Type Based on Invoice · Communication Standard Full
  Reference · bank_statements_source undefined · show_on_dashboard true · color 0. Type has no default.
- `_order`: **`sequence, type, code`**.
- SQL: `account_journal_code_company_uniq` — unique (company_id, code) — "Journal codes must be unique per company."
- Python checks relevant later: archive refused with draft entries; bank account must belong to the company;
  "You cannot modify the field Secure Posted Entries with Hash of a journal that already has accounting entries."

## Records (7, all active, company casimir)

In list order (`sequence, type, code`).

| id | Journal Name | Type | Sequence Prefix | Sequence | Communication Type | Communication Standard | Dedicated Credit Note Seq. | Dedicated Payment Seq. | Show on dashboard | Color | Default Account | Suspense Account |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Sales | Sales | INV | 5 | Based on Invoice | Full Reference | yes | no | yes | 11 | Trade Income | — |
| 2 | Purchases | Purchase | BILL | 6 | Based on Invoice | Full Reference | yes | no | yes | 11 | Costs | — |
| 6 | Bank | Bank | BNK1 | 7 | Based on Invoice | Full Reference | no | yes | yes | 0 | Bank | Bank Suspense Account |
| 3 | Miscellaneous Operations | Miscellaneous | MISC | 9 | Based on Invoice | Full Reference | no | no | no | 0 | — | — |
| 5 | Cash Basis Taxes | Miscellaneous | CABA | 10 | Based on Invoice | Full Reference | no | no | no | 0 | — | — |
| 4 | Exchange Difference | Miscellaneous | EXCH | 10 | Based on Invoice | Full Reference | no | no | no | 0 | — | — |
| 7 | Tax Returns | Miscellaneous | TAX | 10 | Based on Invoice | Full Reference | no | no | no | 0 | — | — |

No Cash or Credit Card journal on the tenant. Communication Type and Standard hold their defaults on every journal,
though the form shows them only for Sales.
