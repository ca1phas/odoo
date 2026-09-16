# 09 · Chart of Accounts

| | |
|---|---|
| Nocoly app | ERP Master · menu group **Invoicing**, first — before Journals, as in Odoo's Configuration menu |
| Worksheet | Chart of Accounts |
| Odoo model | `account.account` |
| Reference | **casimir.odoo.com — Odoo saas~19.4+e**: fields by module, form, list, search, the window action, all 87 accounts, `ir.default`, the raw view arch that places every account field on Journals, Product Categories, Products and Contacts, and the accounts of the seeded journal items — extracted read-only to `nocoly/reference/odoo-19.4/account.account.md`, with the data in `nocoly/data/casimir-accounts.json`. Behaviour the tenant cannot show is read from the Odoo 19.0 source in this repo (`addons/account/models/account_account.py`, `account_journal.py`, `account_move_line.py`, `partner.py`, `product.py`), minding where 19.4 has moved on — parent accounts replace account groups |
| Phase | 1 — **bundle 2 of 6** (Product Categories · Chart of Accounts · Payment Terms · Countries · States · Taxes) |
| Status | §1 written 16 Sep 2026 — not built yet |

The ledger's list of accounts: every amount Odoo posts lands on one of them. The tenant carries Malaysia's chart,
87 accounts. This bundle builds the worksheet and then does what bundle 1 did for Products, five times over:
**every field in the app that points at `account.account` arrives with it** — on Contacts, Products, Product
Categories, Journals and Invoice Lines — seeded with the tenant's own values. **Nothing is replaced or deleted:**
none of those worksheets carried a stand-in for an account.

It stops short of double entry. Invoice Lines gains an Account, not a debit and a credit; the tax and payment-term
lines Odoo writes itself are still not built. So an account here has no balance, and the *Balance* button and the
*Account with Entries* filter wait with them.

## 1 · Requirements

### Fields

Labels are Odoo 19.4's; aliases are Odoo field names on `account.account`. Descriptions are Odoo's `help`, verbatim,
where it has one. "Hidden" means not on the form but used by views, rules or buttons.

| # | Field | Odoo field | Nocoly type | Required | Default | Notes |
|---|---|---|---|---|---|---|
| 1 | Code | `code` | Text, **No duplicates** | yes | — | Placeholder "e.g. 101000". Odoo: "The code must be set for every company…" and "Account codes must be unique…" — per company, so per app copy here. Odoo also allows **only letters, digits and dots** (`^[A-Za-z0-9.]+$`, "The account code can only contain alphanumeric characters and dots."): if a HAP text field can carry a format check, use it with that message; if not, say so in §2 — it is a difference, not a blocker |
| 2 | Account Name | `name` | Text | yes | — | Placeholder "e.g. Current Assets" |
| 3 | Display Name | `display_name` | Function formula, text · **title field** | — | — | **"410000 Trade Income"** — Code, a space, Account Name, trimmed. Odoo's `_compute_display_name` for an accounting user. Read-only and hidden on create (`fieldPermission` "100"), as 04's and 08's titles |
| 4 | Type | `account_type` | Single select, dropdown | yes | — | The **19 options in Odoo's order with Odoo's labels** (reference › Type): Receivable · Bank and Cash · Current Assets · Non-current Assets · Prepayments · Fixed Assets · Payable · Credit Card · Current Liabilities · Non-current Liabilities · Equity · Current Year Earnings · Income · Other Income · Expenses · Other Expenses · Depreciation · Cost of Revenue · Off-Balance Sheet. Odoo's help as the description |
| 5 | Internal Group | `internal_group` | Function formula, text | — | — | **Asset · Liability · Equity · Income · Expense · Off Balance**, from Type — Odoo's `account_type.split('_')[0]`: the six asset types → Asset, the four liability types → Liability, Equity and Current Year Earnings → Equity, Income and Other Income → Income, the four expense types → Expense, Off-Balance Sheet → Off Balance. Odoo keeps it invisible and filters on it; here it is read-only and hidden on create ("100") so a view can filter and show it |
| 6 | Payment Reconciliation | `reconcile` | Checkbox | — | unchecked | Odoo 19.4's label and help: "This account is used in bank reconciliation. Currency rate difference entries will be automatically created if needed." Set from Type by automation A; hidden by a rule for Bank and Cash, Credit Card and Off-Balance Sheet |
| 7 | Non Trade | `non_trade` | Checkbox | — | unchecked | Odoo's help (two sentences). Shown only for Receivable and Payable |
| 8 | Parent Account | `parent_id` | Relation → Chart of Accounts (single), dropdown | no | — | **New in 19.4** — accounts form a tree. Placeholder "Root account". The picker lists active accounts **other than this one** (compare the candidate's Display Name with this record's, the way 04's Extra Packagings excludes the product's unit); Odoo also excludes the account's descendants, which a HAP filter cannot express (§3). A single relation to its own worksheet comes back two-way: its reverse, **Child Accounts** (`child_ids`), stays **hidden** — Odoo shows children only by indenting its list |
| 9 | Description | `description` | Text, multi-line | no | — | Placeholder "Enter description here...". Odoo puts it under the heading *Description* with no label of its own |
| 10 | Active | `active` | Checkbox | — | checked | **Hidden.** Set by Archive / Unarchive; the two views filter on it |

**An account has an Active field**, so — unlike Product Categories — this worksheet has Archive, Unarchive and an
*Archived* view. Odoo 19.4 shows Active as a toggle on the form; the house pattern keeps it hidden behind the two
buttons, as on every other worksheet (§3).

### Form layout

| Odoo 19.4 | Nocoly |
|---|---|
| Stat buttons Taxes · Balance | — (Not built now) |
| h1: Code \| Account Name | Code (4) \| Account Name (8) |
| — | Display Name (read-only, not on the create form) |
| Tab *Accounting*, left: Type · Default Taxes · Fiscal Category · Tags · Deferred | Type \| Internal Group (read-only) |
| Tab *Accounting*, right: Non Trade · Payment Reconciliation (→ Reconcile) · Active · Parent Account | Payment Reconciliation \| Non Trade · Parent Account |
| Group *Description* | Description, full width |
| Tab *Fiscal Rates* | — (Not built now) |
| Chatter | HAP's record discussion |

No tabs: with Taxes, Tags, Fiscal Category and Deferred not built, Odoo's one *Accounting* tab would hold six fields
and nothing beside it, so they sit on the form itself, under the name.

### Rules

| Rule | Type | When | Effect | Odoo source |
|---|---|---|---|---|
| Payment Reconciliation is not offered for bank, card and off-balance accounts | interaction | Type is Bank and Cash, Credit Card or Off-Balance Sheet | hide **Payment Reconciliation** | `<label for="reconcile" invisible="account_type in ('asset_cash', 'liability_credit_card', 'off_balance')"/>` |
| Non Trade only for receivable and payable accounts | interaction | Type is **not** Receivable or Payable (an empty Type included) | hide **Non Trade** | `invisible="account_type not in ('liability_payable', 'asset_receivable')"` |
| A receivable or payable account must be reconcilable | validation | Type is Receivable or Payable **and** Payment Reconciliation is unchecked | "You cannot have a receivable/payable account that is not reconcilable." on Payment Reconciliation | `_check_reconcile`. Odoo appends "(account code: %s)"; a HAP message is static, so it is left off |

### Automations

**A · Payment Reconciliation follows Type** — on a Chart of Accounts record created, or its **Type** changed.
Odoo's `_compute_reconcile`, branch for branch:

| Type is… | Payment Reconciliation becomes |
|---|---|
| Income · Other Income · Expenses · Other Expenses · Depreciation · Cost of Revenue · Equity · Current Year Earnings | unchecked |
| Receivable · Payable | checked |
| Bank and Cash · Credit Card · Off-Balance Sheet | unchecked |
| any other asset or liability type | **left as it is** |

It is what keeps the validation rule from ever firing on a type change, and it is how Odoo's *"An Off-Balance
account can not be reconcilable"* holds here: the box is hidden for that type and the automation clears it. Seeding
the 87 accounts with their tenant values agrees with it on every row.

### Buttons

| Button | Shown when | Does | Confirmation |
|---|---|---|---|
| Archive | Active is checked | Active → unchecked | "Are you sure that you want to archive this record?" · Archive / Cancel |
| Unarchive | Active is unchecked | Active → checked | none |

As on every other worksheet since Journals, the button whose condition fails is hidden, not greyed.

### Views

| View | Type | Shows | Odoo 19.4 |
|---|---|---|---|
| Chart of Accounts | table — opens first | Active accounts. Columns **Code · Account Name · Type · Payment Reconciliation**; sorted **Code A→Z**. Quick filters **Type** (any of) and **Internal Group** | The list: Code · Account Name · Type · Payment Reconciliation, with Parent Account, Active, Non Trade, Default Taxes and Tags as columns switched off. `_order = "code, placeholder_code"`. Filters Receivable · Payable (types) and Equity · Assets · Liability · Income · Expenses (internal groups) — the two quick filters cover all seven |
| Archived | table | Inactive accounts, the same columns and sort | The *Inactive Accounts* filter |

### What this bundle brings to the worksheets already built

Every account field below is a **one-way** Relation → Chart of Accounts (single, dropdown) — no reverse field on
Chart of Accounts — whose picker lists **active accounts only**, showing the Display Name. Labels, placements and
help are the tenant's; "the income-and-expense filter" is Odoo's `ACCOUNT_DOMAIN`: Type **not** Receivable, Payable,
Bank and Cash, Credit Card or Off-Balance Sheet.

**None of them is required on the field.** Odoo marks Contacts' two accounts and several journal accounts required,
but Odoo also hides every one of these fields from some accounting groups (Roles, below), and a HAP field that is
required but hidden from a role blocks every save that role makes. Where the only people who can edit the worksheet
can also see the field — Journals — a rule makes it required. Everywhere else defaults, the seed and automation B
keep the value filled, and §3 checks that they do.

#### Contacts (01)

| Change | Detail |
|---|---|
| New tab **Invoicing** | Between *Sales & Purchase* and *Notes*, where Odoo has it. **Hidden when Company is set** — Odoo's `invisible="not is_company and parent_id"`: a contact under a company posts through the company's accounts |
| **Account Receivable** (`property_account_receivable_id`) | Picker: Type = Receivable. **Default 124000 Account Receivable** (a static relation default). Description: "Odoo reads the company's default, 124000 Account Receivable, until a contact is given its own." — Odoo has no help on the field |
| **Account Payable** (`property_account_payable_id`) | Picker: Type = Payable. **Default 221100 Account Payable**. Description in the same words, with 221100 Account Payable |
| Seed | **Every contact**, TEST records included, gets 124000 and 221100: no contact on the tenant holds its own value, and Odoo reads the company default for every one of them (`ir.default`) |
| Not now | *Bank accounts* (`bank_ids`, `res.partner.bank`) and *Auto-post bills* — neither is among the six bundles. 01's *Not built now* row for the Invoicing tab is narrowed to those two |

#### Products (03)

| Change | Detail |
|---|---|
| New tab **Accounting** | After *Inventory*, where Odoo has it (Odoo's group title *Cost and Revenue* is left out, as 03 leaves its other group titles out) |
| **Income Account** (`property_account_income_id`) | The income-and-expense filter. **Placeholder "From Category"**, no default. Help: "Keep this field empty to use the default value from the product category." |
| **Expense Account** (`property_account_expense_id`) | The same filter and placeholder. Help: "Keep this field empty to use the default value from the product category. If anglo-saxon accounting with automated valuation method is configured, the expense account on the product category will be used." |
| Seed | **Nothing** — all fourteen are empty on the tenant, and empty is what makes a product use its category's account |
| Not now | 03's *Not built now* row "Income and Expense Accounts … Account Tags" is narrowed to Account Tags |

#### Product Categories (08)

| Change | Detail |
|---|---|
| New tab **Accounting** | Odoo's page of that name. It joins the Child Categories and Products tabs HAP draws at the foot of the record — §2 says how they sit together |
| **Income Account** (`property_account_income_categ_id`) | The income-and-expense filter. **Default 410000 Trade Income.** Help: "This account will be used when validating a customer invoice." |
| **Expense Account** (`property_account_expense_categ_id`) | The same filter. **Default 510000 Costs.** Help: "The expense is accounted for when a vendor bill is validated, except in anglo-saxon accounting with perpetual inventory valuation in which case the expense (Cost of Goods Sold account) is recognized at the customer invoice validation." |
| Seed | **Every category**, TEST records included: 410000 and 510000, the company defaults every category on the tenant reads |
| Not now | 08's *Not built now* row that promised these two is removed |

#### Journals (05)

On the tab *Journal Entries*, **above** the two sequence checkboxes and the *Also on Odoo's Journal Entries tab*
block, in Odoo's order:

| Field | Shown for | Required (rule) | Picker | Description |
|---|---|---|---|---|
| **Default Account** (`default_account_id`) | every type | Sales, Purchase, Bank, Cash, Credit Card | every active account | "Odoo labels this Bank Account on a Bank journal, Cash Account on Cash, Journal Account on Credit Card, Default Income Account on Sales, Default Expense Account on Purchase, and Default Account on Miscellaneous, where it is used to automatically balance entries." HAP cannot change a label by condition, so one label and this description |
| **Suspense Account** (`suspense_account_id`) | Bank, Cash, Credit Card | the same three | Type = Current Assets | Odoo's help |
| **Profit Account** (`profit_account_id`) | Cash, Bank | — | Income, Other Income | Odoo's help |
| **Loss Account** (`loss_account_id`) | Cash, Bank | — | Expenses | Odoo's help |
| **Private Share Account** (`non_deductible_account_id`) | Purchase | — | every active account | Odoo's help |

Layout inside the tab: Default Account \| Suspense Account · Profit Account \| Loss Account · Private Share Account ·
then the two sequence checkboxes as they are. The **Journals** view gains a **Default Account** column after
Sequence Prefix (Odoo's list shows it); *Archived* follows. Visibility and requirement are rules of the existing
kind ("… only for …"). **Required is safe here**: only Accounting Administrator and Accountant can edit a journal, and
both see these fields.

Seed: **INV** Default 410000 Trade Income · **BILL** Default 510000 Costs · **BNK1** Default 120001 Bank, Suspense
120002 Bank Suspense Account, Profit 999001 Cash Difference Gain, Loss 999002 Cash Difference Loss. The other four
tenant journals and the TEST journals carry none. 05's *Not built now* row for the five accounts is removed.

#### Invoice Lines (07), and the lines table inside Invoices (06)

| Change | Detail |
|---|---|
| New field **Account** (`account_id`) | Picker: active accounts whose Type is **not** Receivable, Payable or Off-Balance Sheet (Odoo's domain on the invoice line). Not required — see above; automation B fills it |
| Where | **After Label** — on the line form, as a column of the standalone *Lines* view, and as a column of the subtable inside Invoices, which is where Odoo's invoice form puts it |
| Rule | Account **joins** 07's existing rule *A section or a note carries no figures* — hidden on Section, Subsection and Note lines, as Odoo's SQL check forbids an account there |
| Seed | The **eight tenant lines: 410000 Trade Income**, all of them. The TEST lines are left as they are |
| Not now | 07's *Not built now* row for Account is narrowed to debit, credit, balance and the lines Odoo writes itself |

**B · Invoice Lines: fill the account** — on a line **created with no Account**, or on a line whose **Product
changes**; only for a Product line (not a Section, Subsection or Note). Odoo's `_compute_account_id`:

| The line's invoice Type is… | Account becomes the first of |
|---|---|
| Customer Invoice · Customer Credit Note · Sales Receipt | the product's **Income Account** → its category's **Income Account** → the invoice journal's **Default Account** |
| Vendor Bill · Vendor Credit Note · Purchase Receipt | the product's **Expense Account** → its category's **Expense Account** → the journal's **Default Account** |
| Journal Entry | the journal's **Default Account** |

The line's Product is a **variant**, so "the product" is the variant's Product on Products. When the chain yields
nothing, Account is left as it is. Odoo walks up the category's parents when a category has no account of its own;
every category here carries one, so the automation reads the product's own category only (§3). Odoo also tries the
partner's most frequent account for a line with no product, and the last two lines' account; neither is built.

### Roles

**Chart of Accounts joins the four business roles** in `build/roles.py`: Accounting Administrator *full*;
Accountant, Invoicing and Accounting Read-only *view* — Odoo's access list gives write, create and delete on
`account.account` to `account.group_account_manager` alone.

**Odoo also hides the account fields from part of the accounting staff**, by `groups=` on the views:

| Fields | Accounting Administrator | Accountant | Invoicing | Accounting Read-only |
|---|---|---|---|---|
| Journals' five accounts · Products' and Product Categories' Income and Expense Account · Invoice Lines' Account (`groups="account.group_account_readonly"`) | sees | sees | **hidden** | sees |
| Contacts' Account Receivable and Account Payable (`groups="account.group_account_user"`) | sees | sees | **hidden** | **hidden** |

Build that as field permissions on each role's sheet. **If a HAP role cannot hide a single field**, build nothing in
its place, report it in §2 and it becomes a §3 difference — do not hide whole tabs or worksheets to approximate it.

### Not built now, and why

| Odoo 19.4 field / feature | Why not now |
|---|---|
| Default Taxes (`tax_ids`) and the *Taxes* stat button (`related_taxes_amount`) | **Taxes bundle — bundle 6.** It must come back here, as this bundle came back to Product Categories |
| Tags (`tag_ids`) | Account Tags are not among the six bundles; on the tenant they feed the cash-flow report only |
| *Balance* stat button (`current_balance`), *Account with Entries* (`used`), Opening Debit / Credit / Balance | Need journal items with a debit and a credit. Invoice Lines carries an account and a subtotal, not double entry |
| Account Currency (`currency_id`), Exclude Provision Currency | Multi-currency is not in Phase 1; the tenant sets none |
| Fiscal Category, the *Fiscal Rates* tab (`fiscal_category_id`, `rate_ids`) | `account_fiscal_categories`; none on the tenant |
| Deferred (`is_deferred`) | Deferred revenue and expense entries, `account_accountant` |
| Companies, Code Mapping, Display code, code and name paths, the Root side panel | One company per app copy; the side panel groups by the code's first characters, which the Code sort already lines up |
| Internal Notes (`note`) | On no view on the tenant |
| The *→ Reconcile* link | Reconciliation needs payments and journal items |
| The grouped type dropdown and the indented hierarchy list | HAP's dropdown and table are flat. Codes sort children after their parents when the codes nest, as Malaysia's do |
| "Suggested" accounts and the most-frequent-account order in pickers | Needs posting history |
| An account's type may not become Receivable or Payable while it is a Sales or Purchase journal's default, or a bank journal's account | A HAP rule cannot look at another worksheet (§3) |
| Accounts on a tax repartition line or a fiscal position mapping cannot be archived | Taxes bundle; fiscal positions are not among the six |
| Excluding an account's descendants from its Parent Account picker | A HAP filter cannot follow a tree (§3) |
| The code alone in pickers for non-accounting users (`display_name` drops it) | One Display Name for everyone |
| Journals: Odoo **creates** a bank, cash or card account when Default Account is left empty | HAP cannot create a record from a save without a workflow; a rule requires the field instead |
| Journals: the Default Account picker narrowed by the journal's type | A HAP picker cannot change its filter with the record's own dropdown (§3) |
| Contacts: *Bank accounts*, *Auto-post bills* | `res.partner.bank` is not among the six; auto-posting needs vendor bill automation |
| Invoice Lines: debit, credit, balance; the tax and payment-term lines and their accounts | Double entry, and the Taxes and Payment Terms bundles |
| "Missing required account on accountable line" | Not required here (above); automation B fills the account, and §3 checks a line it cannot fill |

### Records

1. **The 87 accounts** from `data/casimir-accounts.json`: Code, Account Name, Type, Payment Reconciliation, Non
   Trade, all active, no parent, no description. Read every one back.
2. **Then the references**, each read back: every contact → 124000 / 221100; every category → 410000 / 510000;
   INV, BILL and BNK1 as in the Journals table; the eight tenant invoice lines → 410000. Products get nothing.

No `TEST …` record is needed to seed; the test list adds its own.
