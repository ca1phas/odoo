# account.account — as on casimir.odoo.com (Odoo saas~19.4+e)

Read-only extract, 16 Sep 2026: `fields_get`, `ir.model.fields` (module per field), `get_views` (form, list,
search), the window actions, `ir.model.constraint`, every account, the account fields of `account.journal`,
`product.category`, `product.template` and `res.partner` with their values, `ir.default`, the raw `ir.ui.view`
arch of the views that place those fields (unfiltered by group), and the accounts of the seeded documents' journal
items. The accounts and every account reference are saved as `nocoly/data/casimir-accounts.json`. Behaviour the
tenant cannot show is read from the Odoo 19.0 source in this repo, `addons/account/models/account_account.py`,
`account_journal.py`, `account_move_line.py`, `partner.py`, `product.py` — **with care: 19.4 has moved on** (below).

Menu: **Chart of Accounts** (window action `account.action_account_form`, `list,kanban,form`, context
`{'include_inactive_account_parents': True}`, no domain), under Accounting/Invoicing ▸ Configuration.

## 19.4 is not 19.0 here

| | 19.0 source in this repo | 19.4 tenant |
|---|---|---|
| Hierarchy | `account.group` (code-prefix ranges), read-only on the account | **`parent_id` Parent Account** on the account itself, with `parent_path`, `code_path`, `name_path`; `account.group` answers **404** — gone |
| Retiring an account | `active` | `active` (form toggle, list decoration, *Inactive Accounts* filter) |
| Code | company-dependent `code_store`, `code` computed | the same, plus `placeholder_code` "Display code" |

## Fields

Chatter, activity and rating fields are left out; so are the `account_reports` audit fields (`audit_*`,
`account_status`, `last_message`, `budget_item_ids`, `exclude_provision_currency_ids`). S = stored.

| Field | Label | Type | Req. | Module | Notes |
|---|---|---|---|---|---|
| `code` | Code | char (computed ↔ `code_store`) | | account | company-dependent through `code_store`. Form placeholder "e.g. 101000". Constraints below |
| `name` | Account Name | char S | **yes** | account | translatable; placeholder "e.g. Current Assets" |
| `account_type` | Type | selection S | **yes** | account | help: "Account Type is used for information purpose, to generate country-specific legal reports, and set the rules to close a fiscal year and generate opening entries." Options below |
| `internal_group` | Internal Group | selection, computed | | account | `account_type.split('_')[0]`: Equity · Asset · Liability · Income · Expense · Off Balance. Invisible on form and list; the search filters use it |
| `reconcile` | **Payment Reconciliation** | boolean S | | account | help: "This account is used in bank reconciliation. Currency rate difference entries will be automatically created if needed." (19.0 labels it *Allow Reconciliation*). Computed from the type, editable — below |
| `non_trade` | Non Trade | boolean S | | account | help: "If set, this account will belong to Non Trade Receivable/Payable in reports and filters. If not, this account will belong to Trade Receivable/Payable in reports and filters." |
| `active` | Active | boolean S | | account | default true |
| `parent_id` | Parent Account | many2one → account.account S | | account | placeholder "Root account"; domain excludes the account itself and its descendants (`['!', ('id', 'child_of', id)]`) |
| `description` | Description | text S | | account | translatable; placeholder "Enter description here..." |
| `note` | Internal Notes | text S | | account | on no view |
| `tax_ids` | Default Taxes | many2many → account.tax S | | account | invisible for Off-Balance Sheet |
| `tag_ids` | Tags | many2many → account.account.tag S | | account | help: "Optional tags you may want to assign for custom reporting". Domain `applicability = accounts` |
| `currency_id` | Account Currency | many2one → res.currency S | | account | help: "Forces all journal items in this account to have a specific currency (i.e. bank journals). If no currency is set, entries can use any currency." Not on the tenant's form |
| `company_ids` | Companies | many2many → res.company S | **yes** | account | invisible |
| `fiscal_category_id`, `rate_ids`, `current_rate` | Fiscal Category, Rate | | | account_fiscal_categories | the *Fiscal Rates* tab |
| `is_deferred` | Deferred | boolean S | | account_accountant | help: "Check to automatically use this account for deferred expenses or deferred revenue when recording the invoice"; income and expense types only |
| `current_balance` | Current Balance | float | | account | the *Balance* stat button, opening the account's journal items |
| `related_taxes_amount` | Related Taxes Amount | integer | | account | the *Taxes* stat button, hidden at 0 |
| `used` | Used | boolean | | account | the *Account with Entries* filter |
| `opening_debit`, `opening_credit`, `opening_balance` | Opening … | monetary | | account | onboarding |
| `placeholder_code`, `code_path`, `name_path`, `root_id`, `parent_ids`, `parent_path`, `code_store`, `code_mapping_ids`, `display_mapping_tab`, `company_currency_id`, `company_fiscal_country_code`, `include_initial_balance` | | | | account | technical or multi-company |

### Type — 19 options, in Odoo's order

| Key | Label | Internal group | | Key | Label | Internal group |
|---|---|---|---|---|---|---|
| `asset_receivable` | Receivable | Asset | | `equity` | Equity | Equity |
| `asset_cash` | Bank and Cash | Asset | | `equity_unaffected` | Current Year Earnings | Equity |
| `asset_current` | Current Assets | Asset | | `income` | Income | Income |
| `asset_non_current` | Non-current Assets | Asset | | `income_other` | Other Income | Income |
| `asset_prepayments` | Prepayments | Asset | | `expense` | Expenses | Expense |
| `asset_fixed` | Fixed Assets | Asset | | `expense_other` | Other Expenses | Expense |
| `liability_payable` | Payable | Liability | | `expense_depreciation` | Depreciation | Expense |
| `liability_credit_card` | Credit Card | Liability | | `expense_direct_cost` | Cost of Revenue | Expense |
| `liability_current` | Current Liabilities | Liability | | `off_balance` | Off-Balance Sheet | Off Balance |
| `liability_non_current` | Non-current Liabilities | Liability | | | | |

The form's `account_type_selection` widget shows them under group headings; a plain dropdown does not.

## Form

```xml
<form string="Account">
  <sheet>
    <div class="oe_button_box">  Taxes (related_taxes_amount, hidden at 0) · Balance (current_balance)  </div>
    <h1> Code (placeholder "e.g. 101000") | Account Name (placeholder "e.g. Current Assets") </h1>
    <notebook>
      <page name="accounting" string="Accounting">
        <group>
          <group>
            <field name="account_type" widget="account_type_selection"/>
            <field name="tax_ids" invisible="account_type == 'off_balance'"/>
            <field name="fiscal_category_id" invisible="internal_group not in ('asset', 'expense', 'income')"/>
            <field name="tag_ids" domain="[('applicability', '=', 'accounts')]"/>
            <field name="is_deferred" invisible="account_type not in ('expense', 'expense_other', 'income', 'income_other')"/>
          </group>
          <group name="technical_settings">
            <field name="non_trade" invisible="account_type not in ('liability_payable', 'asset_receivable')"/>
            <label for="reconcile" invisible="account_type in ('asset_cash', 'liability_credit_card', 'off_balance')"/>
            <div> <field name="reconcile"/> <button " -> Reconcile" invisible="not reconcile"/> </div>
            <field name="active" widget="boolean_toggle"/>
            <field name="parent_id" placeholder="Root account"/>
          </group>
          <group string="Description">
            <field name="description" nolabel="1" placeholder="Enter description here..."/>
          </group>
        </group>
      </page>
      <page name="fiscal_rates" string="Fiscal Rates" invisible="not fiscal_category_id"> rate_ids </page>
    </notebook>
  </sheet>
  <chatter/>
</form>
```

## List — "Chart of accounts", `js_class="account_hierarchy_list"`, `decoration-muted="not active"`, multi-edit

Code · Account Name · Type · *Parent Account (optional, hidden)* · Payment Reconciliation (toggle; invisible for Bank
and Cash, Credit Card, Off-Balance Sheet) · *Active, Non Trade, Default Taxes, Tags, Current Rate, Fiscal Category
(all optional, hidden)*.

## Search

- **Account** searches Account Name, Code (prefix) and Description; also Fiscal Category, Type.
- Filters: **Receivable** · **Payable** (by type) · **Equity** · **Assets** · **Liability** · **Income** · **Expenses**
  (by internal group) — **Account with Entries** (`used`) · **Inactive Accounts** (`active = False`).
- Group by **Account Type**. Side panel: `root_id`, the code's leading characters.

## Order and naming, from the source

- `_order = "code, placeholder_code"`.
- `_compute_display_name`: **"Code Account Name"** for a user in `account.group_account_readonly`; the bare name
  otherwise. With `formatted_display_name` it adds a *Suggested* tag and the description on a second line.

## Behaviour, from the 19.0 source

| What | Source | Message |
|---|---|---|
| Payment Reconciliation follows the type: **off** for the Income, Expense and Equity groups, **on** for Receivable and Payable, **off** for Bank and Cash, Credit Card, Off-Balance Sheet; other asset and liability types keep what they had | `_compute_reconcile` | — |
| A receivable or payable account must be reconcilable | `_check_reconcile` | "You cannot have a receivable/payable account that is not reconcilable. (account code: %s)" |
| An off-balance account cannot be reconcilable or carry taxes | `_constrains_reconcile` | "An Off-Balance account can not be reconcilable" · "An Off-Balance account can not have taxes" |
| The code may hold only letters, digits and dots | `_check_account_code`, `ACCOUNT_CODE_REGEX = ^[A-Za-z0-9.]+$` | "The account code can only contain alphanumeric characters and dots. (account code: %s)" |
| Every account has a code, and codes are unique | `_ensure_code_is_unique` | "The code must be set for every company to which this account belongs." · "Account codes must be unique. You can't create accounts with these duplicate codes: %s" |
| An account used as a sale or purchase journal's default cannot become receivable/payable | `_check_account_type_sales_purchase_journal` | "The account is already in use in a 'sale' or 'purchase' journal. This means that the account's type couldn't be 'receivable' or 'payable'." |
| An account used as a journal's bank account cannot become receivable/payable | `_check_account_is_bank_journal_bank_account` | "You cannot change the type of an account set as Bank Account on a journal to Receivable or Payable." |
| Accounts on a tax repartition line or a fiscal position mapping cannot be archived | `write` | "You cannot remove/deactivate the accounts "%s" which are set on a tax repartition line." |

## Access (`addons/account/security/ir.model.access.csv`)

`account.group_account_manager` read · write · create · delete; `group_account_readonly`, `group_account_invoice`,
`base.group_user`, `base.group_partner_manager` **read only**.

## The accounts — 87, all active, 16 Sep 2026

Malaysia's chart (`l10n_my`). **No account has a parent**, a currency, default taxes or a description. Four have
entries: 120003 Outstanding Receipts (3,027.80), 124000 Account Receivable (13,483.54), 221300 SST Control Account
(−1,480.94), 410000 Trade Income (−15,030.40). Tags: *Operating Activities* on 46 income and expense accounts,
*Investing & Extraordinary Activities* on 999001 and 999002; *Financing Activities* on none. The full list is in
`data/casimir-accounts.json`.

| Type | Count | Codes |
|---|---|---|
| Fixed Assets | 1 | 110000 |
| Non-current Assets | 4 | 111000 113000 114000 116000 |
| Current Assets | 11 | 111220 120000 120002 120003 120004 124100 124200 124500 125000 126000 127000 |
| Bank and Cash | 1 | 120001 Bank |
| Receivable | 4 | 124000 124300 124600 124700 |
| Non-current Liabilities | 1 | 210000 |
| Current Liabilities | 14 | 220000 221000–221040 221200–221500 310000 320000 330000 340000 |
| Payable | 3 | 221100 221600 221700 |
| Income | 6 | 410000–424000 |
| Other Income | 2 | 999001 999997 |
| Expenses | 39 | 510000–524000, 999002, 999998 |
| Current Year Earnings | 1 | 999999 |

Payment Reconciliation is on for all four Receivable and all three Payable accounts, and for four Current Assets
(111220 Funds in Transit, 120003, 120004, 124100). Non Trade is on for 124700 SST Receivable and 221700 SST Payable.
The chart's own quirk, kept as found: 310000 Paid Capital, 320000 Accumulated Profit & Loss and 330000 Profit & Loss
Account are typed **Current Liabilities**, not Equity.

## Where other models point here

### `account.journal` — tab *Journal Entries*, every field `groups="account.group_account_readonly"`

| Field | Label on the form | Shown for | Required | Domain | help |
|---|---|---|---|---|---|
| `default_account_id` | **Bank Account** (bank) · **Journal Account** (credit) · **Cash Account** (cash) · **Default Income Account** (sale) · **Default Expense Account** (purchase) · **Default Account** (general) | every type | sale, purchase; bank, cash, credit once saved | bank: Bank and Cash or Credit Card · credit: Credit Card · cash: Bank and Cash · sale: Income, Other Income · purchase: Expenses, Depreciation, Cost of Revenue · general: any | general only: "If set, this account is used to automatically balance entries." Placeholder "Create new account" on bank, cash, credit — Odoo creates one when left empty |
| `suspense_account_id` | Suspense Account | bank, cash, credit | same | Current Assets | "Bank statements transactions will be posted on the suspense account until the final reconciliation allowing finding the right account." Computed from the company's |
| `non_deductible_account_id` | Private Share Account | purchase | | — | "Account used to register the private part of mixed expenses." |
| `profit_account_id` | Profit Account | cash, bank | | Income, Other Income | "Used to register a profit when the ending balance of a cash register differs from what the system computes" |
| `loss_account_id` | Loss Account | cash, bank | | Expenses | "Used to register a loss when the ending balance of a cash register differs from what the system computes" |

The journal list carries `default_account_id` as a column (`optional="show"`).

| Journal | Default | Suspense | Profit | Loss | Private Share |
|---|---|---|---|---|---|
| INV Sales | 410000 Trade Income | | | | |
| BILL Purchases | 510000 Costs | | | | — |
| BNK1 Bank | 120001 Bank | 120002 Bank Suspense Account | 999001 Cash Difference Gain | 999002 Cash Difference Loss | |
| MISC, CABA, EXCH, TAX | — | | | | |

### `product.category` — page **Accounting**, `groups="account.group_account_readonly"`

Income Account (`property_account_income_categ_id`, help "This account will be used when validating a customer
invoice.") · Expense Account (`property_account_expense_categ_id`, help "The expense is accounted for when a vendor
bill is validated, except in anglo-saxon accounting with perpetual inventory valuation in which case the expense
(Cost of Goods Sold account) is recognized at the customer invoice validation."). Both company-dependent, domain
`ACCOUNT_DOMAIN` = type **not** Receivable, Payable, Bank and Cash, Credit Card, Off-Balance Sheet. **No category
holds its own value: all seven read the company default** (`ir.default`) — Income **410000 Trade Income**, Expense
**510000 Costs**.

### `product.template` — page **Accounting** after Inventory, group **Cost and Revenue**, `groups="account.group_account_readonly"`

Income Account (`property_account_income_id`) · Expense Account (`property_account_expense_id`), placeholder
**"From Category"**, muted when inactive, same `ACCOUNT_DOMAIN`. help: "Keep this field empty to use the default
value from the product category." (Expense adds: "If anglo-saxon accounting with automated valuation method is
configured, the expense account on the product category will be used."). **Empty on all 14 products.**

### `res.partner` — page **Invoicing**, `invisible="not is_company and parent_id"`, group *General*

Bank accounts (`bank_ids`) · **Account Receivable** (`property_account_receivable_id`, domain type Receivable) ·
**Account Payable** (`property_account_payable_id`, domain type Payable) — both `required="True"` and
`groups="account.group_account_user"` · Auto-post bills. Company-dependent; **no contact holds its own value: every
one reads the company default**, **124000 Account Receivable** and **221100 Account Payable**.

### `account.move.line` — the invoice form's line list

`account_id` after the Label, `groups="account.group_account_readonly"`, domain type **not** Receivable, Payable,
Off-Balance Sheet, required unless the line is a section, subsection or note. `_compute_account_id` on a product
line of an invoice: a **customer document** takes the product's Income Account, else the first Income Account up
its category's parents, else the company's; a **vendor document** the Expense equivalents; a line with no product
takes the partner's most frequent account; anything still empty takes the last two lines' account if they agree,
else **the journal's Default Account**. Payment-term lines take the partner's receivable or payable.

All eight product lines of the three seeded documents post to **410000 Trade Income**. Their tax lines post to
221300 SST Control Account and their payment-term lines to 124000 Account Receivable.

## Groups that see the account fields

`group_account_user` implies `group_account_readonly`; `group_account_invoice` implies neither.

| Placed with | Accounting Administrator | Accountant | Invoicing | Accounting Read-only |
|---|---|---|---|---|
| `groups="account.group_account_readonly"` — journal, category, product and line accounts | sees | sees | **does not** | sees |
| `groups="account.group_account_user"` — contact receivable and payable | sees | sees | **does not** | **does not** |

The tenant's own admin is in none of these, which is why `get_views` returned the category form without its
Accounting page: the raw `ir.ui.view` arch is what shows it.
