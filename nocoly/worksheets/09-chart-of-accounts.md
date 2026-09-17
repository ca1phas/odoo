# 09 · Chart of Accounts

| | |
|---|---|
| Nocoly app | ERP Master · menu group **Invoicing**, first — before Journals, as in Odoo's Configuration menu |
| Worksheet | Chart of Accounts |
| Odoo model | `account.account` |
| Reference | **casimir.odoo.com — Odoo saas~19.4+e**: fields by module, form, list, search, the window action, all 87 accounts, `ir.default`, the raw view arch that places every account field on Journals, Product Categories, Products and Contacts, and the accounts of the seeded journal items — extracted read-only to `nocoly/reference/odoo-19.4/account.account.md`, with the data in `nocoly/data/casimir-accounts.json`. Behaviour the tenant cannot show is read from the Odoo 19.0 source in this repo (`addons/account/models/account_account.py`, `account_journal.py`, `account_move_line.py`, `partner.py`, `product.py`), minding where 19.4 has moved on — parent accounts replace account groups |
| Phase | 1 — **bundle 2 of 6** (Product Categories · Chart of Accounts · Payment Terms · Countries · States · Taxes) |
| Status | §1 written 16 Sep 2026 · **part A — the worksheet — built and UI-tested 15/15 on 16 Sep 2026** (§2, §3) · part B — the account fields on the other worksheets — not built |

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

It is how Odoo's *"An Off-Balance account can not be reconcilable"* holds here: the box is hidden for that type
and the automation clears it. Seeding the 87 accounts with their tenant values agrees with it on every row. **It
does not stop the validation rule on a type change**, as this section first assumed: HAP checks a rule before the
save and runs a workflow after it, so an account re-typed as Receivable with the box unticked is refused until the
box is ticked by hand — found by the build, §2, and a §3 difference.

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

## 2 · Build

### Part A — the worksheet

Built on 16 Sep 2026 by `nocoly/build/accounts.py` — steps `create → fields → computed → layout → rules →
automation → buttons → views → roles → seed`, or `all` for every one of them followed by `check`. Each step reads
the live state first, refuses to run unless the profile reaches ERP Master › Invoicing › Chart of Accounts and
the worksheet holds only this script's own work, compares the other eight worksheets' controls id by id before
and after its writes, reads back what it wrote, and is safe to re-run: every step was run a second time and wrote
nothing (the second `all` stopped on a dropped connection in `seed`'s guard, before any write, so `seed` and
`check` were then run on their own). Helpers:
`check` reads the configuration back against §1, `verify` compares the accounts with
`data/casimir-accounts.json`, `runs` reads automation A's run history path by path and account by account,
`selfcheck` drives the platform behaviour §1 relies on through the CLI on `TEST Account`, `order` prints each
view's records in the view's own order, `account <code>` one account's stored values, `untouched` every other
worksheet's control count and digest, and `show` the control list. Nothing in `common.py` or `hap.py` changed.

**Part B is not built.** The account fields on Contacts, Products, Product Categories, Journals and Invoice Lines,
their seed, automation B and the per-field hiding in the roles are all still to do, and no other worksheet was
written to: every save was bracketed by the id-by-id comparison, and `untouched` reads the same digests after the
build as before it (below).

| Element | Built | Id |
|---|---|---|
| App | ERP Master | `6cb4d051-a33c-4bf9-b56f-5f47f0e85dc9` |
| Menu group | Invoicing — **Chart of Accounts** (first), Journals, Invoices, Invoice Lines | `6aa8f3ecbf00c316381dbbe8` |
| Worksheet | Chart of Accounts, alias **`account_account`**, icon `sys_books_office` | `6aaa92ae805aef70328667da` |
| Code | Text, single line, required, **No duplicates**, "e.g. 101000", format check `^[A-Za-z0-9.]+$` | `6aaa92d87d58b0f44930f221` |
| Account Name | Text, required, "e.g. Current Assets" — the stock *Name* control's id | `6aaa92ae805aef70328667db` |
| Display Name | Function formula, text, **the title**, `fieldPermission` "100" | `6aaa92f9805aef7032866879` |
| Type | Dropdown, required, Odoo's 19 options in Odoo's order, Odoo's help | `6aaa92d87d58b0f44930f222` |
| Internal Group | Function formula, text, "100" | `6aaa92f9805aef703286687a` |
| Payment Reconciliation | Checkbox, default unchecked, Odoo 19.4's help | `6aaa92d87d58b0f44930f223` |
| Non Trade | Checkbox, default unchecked, Odoo's help | `6aaa92d87d58b0f44930f224` |
| Parent Account | Relation → Chart of Accounts, single, dropdown, "Root account", picker filter | `6aaa92d87d58b0f44930f225` |
| Child Accounts | the reverse of Parent Account, made by the server; multiple, **hidden** ("011") | `6aaa92d87d58b0f44930f226` |
| Description | Text, multi-line, "Enter description here..." — the stock *Description* control's id | `6aaa92ae805aef70328667dc` |
| Active | Checkbox, default checked, **hidden** ("011") | `6aaa92d87d58b0f44930f227` |
| Rules | Payment Reconciliation is not offered for bank, card and off-balance accounts · Non Trade only for receivable and payable accounts · A receivable or payable account must be reconcilable | `6aaa93327d58b0f44930f30d` · `6aaa9332e43d174ab374a527` · `6aaa9351e54d2a34fa4e14f2` |
| Automation A | *Chart of Accounts: Payment Reconciliation follows Type*, published | `6aaa9397a1c923a16effd002` |
| Buttons | Archive · Unarchive | `6aaa94247d58b0f44930f31c` · `6aaa9427e54d2a34fa4e14ff` |
| Button workflows | Archive · Unarchive | `6aaa942487707da9d612e86a` · `6aaa94274f2a99acac091db5` |
| Views | Chart of Accounts (the stock *All* view, renamed; opens first) · Archived | `6aaa92ae805aef70328667de` · `6aaa9476805aef70328668dc` |
| Records | the tenant's 87 accounts · `TEST Account` (TEST01) · `TEST refused payable` (TEST02, archived) | below |

Every id is in `nocoly/build/ids.json`: `"Chart of Accounts"` under `worksheets`, and "Chart of Accounts: …" keys
for the eleven controls, the three rules, the two views, the two buttons, the three workflows and 89 records —
the 87 accounts **keyed by Code** ("Chart of Accounts: 410000"), which is how part B can look them up, TEST01 and
TEST02. No existing key was renamed. `nocoly/build/roles.py` changed (below).

#### The form

| Row | Left | Right |
|---|---|---|
| 0 | **Code** (4) | **Account Name** (8) |
| 1 | Display Name (12) — read-only, hidden on the create form | |
| 2 | **Type** (6) | Internal Group (6) — read-only, hidden on the create form |
| 3 | Payment Reconciliation (6) — hidden for Bank and Cash, Credit Card, Off-Balance Sheet | Non Trade (6) — shown for Receivable and Payable only |
| 4 | Parent Account (6) | |
| 5 | Description (12) | |
| 6 | Active (6) — hidden | |
| 7 | Child Accounts (12) — hidden | |

The first save of the empty worksheet reused the two stock controls whose type matched — *Name* became Account
Name and *Description* became Description — and did not send the stock *Attachment*, which §1 does not have, so
the save removed it. That is the only control this build removed; nothing had to be cleared, deleted or renamed
`ZZ obsolete`.

Help: Odoo's own, verbatim, on Type, Payment Reconciliation (19.4's wording) and Non Trade (its two sentences on
two lines, as in the source). Display Name, Internal Group and Child Accounts carry this build's one-line account
of what they are; Code, Account Name, Parent Account, Description and Active have no help in Odoo and none here.

**Display Name** is `TRIM(CONCAT($Code$," ",$Account Name$))` — Odoo's `f"{code} {name}"`, which falls back to
the name when there is no code; TRIM does both in one expression. **Internal Group** spells Odoo's
`account_type.split('_')[0]` out over the labels, because a function formula sees a dropdown as its label:

```
IF(OR(Type=="Receivable",Type=="Bank and Cash",Type=="Current Assets",Type=="Non-current Assets",
      Type=="Prepayments",Type=="Fixed Assets"),"Asset",
IF(OR(Type=="Payable",Type=="Credit Card",Type=="Current Liabilities",Type=="Non-current Liabilities"),"Liability",
IF(OR(Type=="Equity",Type=="Current Year Earnings"),"Equity",
IF(OR(Type=="Income",Type=="Other Income"),"Income",
IF(OR(Type=="Expenses",Type=="Other Expenses",Type=="Depreciation",Type=="Cost of Revenue"),"Expense",
IF(Type=="Off-Balance Sheet","Off Balance",""))))))
```

(line breaks added here; the stored expression is one line, with control ids). An empty Type gives an empty group,
as in Odoo. Both formulas read back right on all 87 accounts and on all 19 types (self-check). Because the
formula compares labels, **renaming a Type option silently breaks Internal Group** — the option keys are what
records and rules hold, the labels are what this formula holds.

**Parent Account** is §1's self-relation. The server made its reverse ("Child") in the same save, and `layout`
named it **Child Accounts** (`child_ids`) and hid it. Pairing proved: giving TEST Account the parent 410000 raised
410000's Child Accounts from 0 to 1, and clearing it brought it back. The picker filter is stored as §1 asks —
the candidate is active **and** its Display Name is not this record's Display Name (a text formula compared with
`dataType` 2, the way the filter editor saves one). A picker filter runs in the browser only, so whether the
dropdown really leaves the account itself out is for the UI pass; through the API an account **can** be made its
own parent. The account's descendants are not excluded (§1 *Not built now*).

#### Code's format check — §1's question, answered

**Yes, a HAP text control can carry one**, and Code does. It is `advancedSetting.filterregex`, the field editor's
*限定输入格式* ("restrict input format"): a list of `{name, value, err}`. Code's one entry is named *Letters, digits
and dots*, tests `^[A-Za-z0-9.]+$` and says *"The account code can only contain alphanumeric characters and
dots."* — Odoo's message without its "(account code: %s)", which a HAP message cannot fill in. hap-cli knows
nothing of the setting; it was found in pd-openweb's field editor (`TextVerify.jsx`) and form validation
(`checkValueByFilterRegex`, which tests `new RegExp(value, 'gm')` and lets an empty value through).

**It is a form check only.** `record update` stored the Code `TEST-01` without complaint (self-check, then put
back), exactly as Journals' maximum length is stored. **No duplicates**, by contrast, holds everywhere: a second
`410000` was refused on create and on update with `resultCode 11`. How the browser shows the message is for the UI
pass.

#### Rules

| Rule | Id | Built as |
|---|---|---|
| Payment Reconciliation is not offered for bank, card and off-balance accounts | `6aaa93327d58b0f44930f30d` | interaction · **hide** Payment Reconciliation while Type is any of Bank and Cash, Credit Card, Off-Balance Sheet. A new record with no Type shows the box, as Odoo's `invisible` does |
| Non Trade only for receivable and payable accounts | `6aaa9332e43d174ab374a527` | interaction · **show** Non Trade while Type is any of Receivable, Payable — hidden for every other type **and while Type is empty** (decision below) |
| A receivable or payable account must be reconcilable | `6aaa9351e54d2a34fa4e14f2` | validation · Type is any of Receivable, Payable **and** Payment Reconciliation is not checked → *"You cannot have a receivable/payable account that is not reconcilable."* on Payment Reconciliation · check type **1** (form and server) · hint type **0** (as the Type is picked, and on submit) |

Through the API the validation rule refused a Current Assets account being re-typed Receivable with its box
unchecked, and refused unticking the box of a Receivable account — both `resultCode 32`. It **did not** refuse a
new Payable account created with the box unchecked: see *What §1 expects and HAP does not do*.

#### Automation A — Payment Reconciliation follows Type

Workflow `6aaa9397a1c923a16effd002`, published. Trigger **When an account is created or its Type changes** —
worksheet event 新增或更新 ('2') on Chart of Accounts, narrowed to Type, no condition — into an **exclusive**
gateway (唯一分支) *What does the Type do to Payment Reconciliation?* with §1's table as four paths, in §1's
order:

| Path | Type is any of | Step |
|---|---|---|
| Income, Expense or Equity — unchecked | Income · Other Income · Expenses · Other Expenses · Depreciation · Cost of Revenue · Equity · Current Year Earnings | *Uncheck Payment Reconciliation (income, expense, equity)* |
| Receivable or Payable — checked | Receivable · Payable | *Check Payment Reconciliation* |
| Bank and Cash, Credit Card or Off-Balance Sheet — unchecked | Bank and Cash · Credit Card · Off-Balance Sheet | *Uncheck Payment Reconciliation (bank, card, off-balance)* |
| Any other asset or liability type — left as it is | Current Assets · Non-current Assets · Prepayments · Fixed Assets · Current Liabilities · Non-current Liabilities | **none** — the path writes nothing |

Each step writes only Payment Reconciliation, on the trigger record; nothing follows the gateway, and the three
workflows on this worksheet cannot start one another (the buttons write Active, the automation writes Payment
Reconciliation, and neither is Type). The fourth path lists its six types rather than being a condition-less
"else", so an account with **no** Type matches no path — that run stops at the gateway with "未通过分支" and
writes nothing, which is what Odoo's compute does with no type.

**Proved three ways:**

1. **The 87 creates of the seed** — 87 runs, all completed, exactly one per account; each account's run took the
   path its Type calls for (48 through *Income, Expense or Equity*, 7 through *Receivable or Payable*, 1 through
   *Bank and Cash…*, 31 through the path that writes nothing); and afterwards every box reads as the extract has
   it — on for 111220, 120003, 120004, 124000, 124100, 124300, 124600, 124700, 221100, 221600 and 221700, off for
   the other 76. **§1's claim that the seed agrees with the automation on every row holds**, and it holds because
   the automation ran and wrote the same values, not because it did not run.
2. **All 19 types, one after another on TEST Account** (self-check) — 19 runs, each through the right path, with
   the box and Internal Group read back after every one; the path that writes nothing proved with the box off
   (Current Assets, Current Liabilities) and on (Non-current Assets, Prepayments, Fixed Assets, Non-current
   Liabilities), and the *unchecked* paths always reached with the box on.
3. **Nothing else starts it** — Archive, Unarchive and a write of Non Trade alone start no run.

A run's detail never lists a branch path node, only the steps that ran. The three writing paths are identified by
their steps, and the fourth by elimination: the run passed the gateway, completed, and wrote nothing.

#### What §1 expects and HAP does not do

**1 · The automation cannot keep the validation rule from firing on a type change.** §1: *"It is what keeps the
validation rule from ever firing on a type change."* In Odoo it is: `reconcile` is recomputed the moment the type
changes, before `_check_reconcile` looks. HAP checks a validation rule **before** the save and runs a workflow
**after** it. So re-typing an account whose box is unchecked as Receivable or Payable is **refused by the rule**,
and automation A never runs to tick the box — the self-check's `record update` came back `resultCode 32`, the
Type stayed Current Assets, and no run started. In the form the user should see the message on Payment
Reconciliation as soon as they pick Receivable or Payable (hint type 0 — for the UI pass to confirm), tick the
box, and save: one click more than Odoo. A **new** receivable or payable account is the same, since the box
defaults to unchecked. Everything else in §1's table the automation does — it clears the box for the income,
expense, equity, bank, card and off-balance types, and it ticks it for a receivable or payable account whenever
the save gets through.

**2 · The server does not check the validation rule on a create.** A `record create` of a Payable account with
the box unchecked — both condition fields in the write — was **accepted** (TEST02, *TEST refused payable*,
created 21:36:39). Automation A then ticked its box five seconds later, as §1's table says, and the self-check
archived it. The same rule refused both `record update`s above, with the box sent the same way. The form enforces
the rule on create and on edit alike; only API creates get past it — which matters for import scripts, not for
the seed, whose seven receivable and payable accounts all arrive ticked.

**3 · The trigger narrowed to Type fires when Type is in the write, not only when it changes.** A `record update`
sending Type unchanged together with a real change to Non Trade started a run (the record log reads *Type:
'Current Assets' → 'Current Assets'*). Odoo does the same — its `write` calls `modified(vals)` on every field
written, changed or not (`odoo/orm/models.py`), so `reconcile` is recomputed — and the behaviour matches Odoo; it
matters for any script that re-sends every field, which would re-run the
automation and reset a hand-set box on an income, expense, equity, bank, card or off-balance account. Whether the
browser sends an unchanged Type when a user edits another field is for the UI pass to read in the record log.

These three are §3 differences to record, not workarounds to build; see *For a second opinion*.

#### Buttons and views

**Archive** (shown while Active is checked; confirmation *"Are you sure that you want to archive this record?"* ·
Archive / Cancel) and **Unarchive** (shown while Active is unchecked; no confirmation), each running a one-step
workflow that writes Active on the record — Journals' pattern exactly. Both proved through `workflow trigger` on
TEST Account, and neither starts automation A.

| View | Id | Built |
|---|---|---|
| Chart of Accounts | `6aaa92ae805aef70328667de` | the stock *All* view renamed; opens first · filter Active is checked · columns **Code · Account Name · Type · Payment Reconciliation** · sort **Code A→Z** (`sortCid` Code, `sortType` 2) · quick filters **Type** (any of, dropdown — `allowitem` "2", `direction` "2") and **Internal Group** |
| Archived | `6aaa9476805aef70328668dc` | filter Active is not checked · the same columns and sort · no quick filter (§1: "the same columns and sort") |

**How HAP renders a quick filter on a text formula — from the stored view and pd-openweb's source, not yet from
the browser.** The view editor treats a function formula as its result type (`redefineComplexControl`), so the
Internal Group quick filter is a **text** filter: stored as `dataType` 2 with `filterType` 1 — "contains", the
editor's default for text — and drawn as a **search box, not a list of the six groups**. Typing *Asset*,
*Liability*, *Equity*, *Income*, *Expense* or *Off Balance* matches exactly one group, since no group's name
contains another's, so Odoo's five group filters are still one word away. The UI pass has to confirm the box.

`order`: both views return their records in Code order — *Chart of Accounts (88): 110000, 111000, 111220, 113000,
…, 999998, 999999, TEST01* and *Archived (1): TEST02*, each `sorted A→Z as text: True` (TEST01 sorts last, as a
letter follows every digit).

#### Roles

`build/roles.py` now carries Chart of Accounts: in `ORDER` after Product Categories and before Journals, and in
the Accountant and Invoicing matrices as *view*; Accounting Administrator (*full*) and Accounting Read-only
(*view*) take it from `ORDER` — so Accounting Administrator full, the other three view, the same rule as Products
and Odoo's access list for `account.account`. `accounts.py roles` ran `roles.py create`: HAP had added the new
worksheet to all four roles by itself, at its own defaults (`BUILDING.md` › Roles), and `reconcile` wrote
exactly the Chart of Accounts entry of each role — its three levels, the create
right, the action switches and the two views' flags — and nothing else. `roles.py check`: OK. **The per-field
hiding in §1's second Roles table is part B's; nothing was written for it.**

#### Records

- **The tenant's 87 accounts**, matched by Code, each read back as it was written; `verify` compares every one
  with the extract — Code, Account Name, Type, Payment Reconciliation, Non Trade, Active, no parent, no
  description — and with the Display Name and Internal Group the two formulas must produce: **87 OK**.
- **TEST Account** (TEST01, `a2b4c8c0-1134-439f-ba5d-a046ae15bba9`) — the self-check's record, left active as a
  Current Assets account with the box unchecked and no parent.
- **TEST refused payable** (TEST02, `c7928ba1-3497-4967-82e4-517da832bb96`) — the create the validation rule did
  not refuse; left **archived**, Payable, box ticked by automation A. It is the evidence for difference 2 above.

The first `seed` run created all 86 remaining accounts (410000 had been seeded alone first, to see automation A
fire on a create before seeding the rest) and read each back. It then waited out its whole deadline for the runs —
the history's `count` is per page (Found while building) — and stopped on a dropped connection while counting
them, after every write had been read back. The second run wrote nothing, waited for nothing and verified all
87; `runs` then read the 87 runs one by one.

#### What §1 left to the build

1. **Code's format check** — answered above: `filterregex`, and a form check only.
2. **Where the hidden controls sit** — Active at row 6 and Child Accounts at row 7, under §1's rows.
3. **§1's "Payment Reconciliation | Non Trade · Parent Account"** — read as two rows: Payment Reconciliation |
   Non Trade, then Parent Account on the left half of the next row.
4. **The Type option keys** — minted once in `accounts.TYPES`, which records and rules point at; colours by
   internal group (a dropdown shows none).
5. **The icon** — `sys_books_office`, from `hap icon list`.
6. **The aliases** — every one an Odoo field name: `code`, `name`, `display_name`, `account_type`,
   `internal_group`, `reconcile`, `non_trade`, `parent_id`, `description`, `active`, `child_ids`.
7. **The validation rule's check type and hint type** — 1 (form and server) and 0 (as you type, and on submit).
8. **The workflow's shape** — one exclusive gateway with §1's four rows as paths, the empty one with an explicit
   condition; the names of the workflow, trigger, gateway, paths and steps.

#### Self-checks through the CLI

`accounts.py check` — menu place, worksheet alias / remark / icon, every control's type, place, alias, help,
hint, required, No duplicates, permission and title, the option keys, Code's format check, Parent Account's
picker filter, both formulas, the self-relation's pairing, the three rules, automation A's trigger, gateway,
paths, conditions, steps and published state, both buttons and their workflows, and both views:

```
section Invoicing: ['Chart of Accounts', 'Journals', 'Invoices', 'Invoice Lines']
check: OK — first in Invoicing; eleven controls with their places, permissions, help, hints and Code's format
check; Display Name the title; the two formulas; the self-relation and its hidden reverse; the three rules;
automation A published with its four paths; Archive / Unarchive; the two views
```

`accounts.py verify` (87 lines, one per account, then):

```
…
OK    120001 Bank                                  Bank and Cash            Asset     reconcile=0 non_trade=0 active=1
…
OK    124000 Account Receivable                    Receivable               Asset     reconcile=1 non_trade=0 active=1
…
OK    124700 SST Receivable                        Receivable               Asset     reconcile=1 non_trade=1 active=1
…
OK    410000 Trade Income                          Income                   Income    reconcile=0 non_trade=0 active=1
…
OK    999999 Profit or Loss Appropriation          Current Year Earnings    Equity    reconcile=0 non_trade=0 active=1
87 accounts in the extract; 0 missing or differing; 2 not in the extract ['TEST01 TEST Account', 'TEST02 TEST refused payable']
reconcile on: ['111220', '120003', '120004', '124000', '124100', '124300', '124600', '124700', '221100', '221600', '221700']
```

`accounts.py runs`, straight after the seed:

```
87 run(s) read; status counts {2: 87} (2 completed · 1 running · 3 stopped · 4 failed)
 48  Income, Expense or Equity — unchecked
 31  no update step (the path that writes nothing, or no path at all)
  7  Receivable or Payable — checked
  1  Bank and Cash, Credit Card or Off-Balance Sheet — unchecked
seeded accounts with a run: 87 of 87; with more than one: []; without: []
runs whose path is not the one the account's Type calls for: []
```

and over the whole history at the end of the build, the self-check's two walks through the 19 types included
(the two status-3 runs are the two emptied Types):

```
137 run(s) read; status counts {2: 135, 3: 2} (2 completed · 1 running · 3 stopped · 4 failed)
 52  no update step (the path that writes nothing, or no path at all)
 14  Receivable or Payable — checked
  7  Bank and Cash, Credit Card or Off-Balance Sheet — unchecked
 64  Income, Expense or Equity — unchecked
seeded accounts with a run: 87 of 87; with more than one: []; without: []
runs whose path is not the one the account's Type calls for: []
```

`accounts.py selfcheck` — `DIFF` would be the build not doing what §1 says; `LIMIT` is platform behaviour §1 did
not expect, recorded rather than counted as a failure (run lines shortened):

```
OK     Display Name and Internal Group: 'TEST01 TEST Account' / 'Asset'
OK     Type → Receivable: 1 run(s) [(…, 2, 'Receivable or Payable — checked')], reconcile=1 (want 1), group 'Asset'
OK     Type → Bank and Cash: 1 run(s) [(…, 2, 'Bank and Cash, Credit Card or Off-Balance Sheet — unchecked')], reconcile=0 (want 0), group 'Asset'
OK     Type → Current Assets: 1 run(s) [(…, 2, 'no update step …')], reconcile=0 (want 0), group 'Asset'
OK     Type → Non-current Assets: 1 run(s) [(…, 2, 'no update step …')], reconcile=1 (want 1), group 'Asset'
OK     Type → Prepayments: 1 run(s) [(…, 2, 'no update step …')], reconcile=1 (want 1), group 'Asset'
OK     Type → Fixed Assets: 1 run(s) [(…, 2, 'no update step …')], reconcile=1 (want 1), group 'Asset'
OK     Type → Payable: 1 run(s) [(…, 2, 'Receivable or Payable — checked')], reconcile=1 (want 1), group 'Liability'
OK     Type → Credit Card: 1 run(s) [(…, 2, 'Bank and Cash, Credit Card or Off-Balance Sheet — unchecked')], reconcile=0 (want 0), group 'Liability'
OK     Type → Current Liabilities: 1 run(s) [(…, 2, 'no update step …')], reconcile=0 (want 0), group 'Liability'
OK     Type → Non-current Liabilities: 1 run(s) [(…, 2, 'no update step …')], reconcile=1 (want 1), group 'Liability'
OK     Type → Equity: 1 run(s) [(…, 2, 'Income, Expense or Equity — unchecked')], reconcile=0 (want 0), group 'Equity'
OK     Type → Current Year Earnings: 1 run(s) [(…, 2, 'Income, Expense or Equity — unchecked')], reconcile=0 (want 0), group 'Equity'
OK     Type → Income: 1 run(s) [(…, 2, 'Income, Expense or Equity — unchecked')], reconcile=0 (want 0), group 'Income'
OK     Type → Other Income: 1 run(s) [(…, 2, 'Income, Expense or Equity — unchecked')], reconcile=0 (want 0), group 'Income'
OK     Type → Expenses: 1 run(s) [(…, 2, 'Income, Expense or Equity — unchecked')], reconcile=0 (want 0), group 'Expense'
OK     Type → Other Expenses: 1 run(s) [(…, 2, 'Income, Expense or Equity — unchecked')], reconcile=0 (want 0), group 'Expense'
OK     Type → Depreciation: 1 run(s) [(…, 2, 'Income, Expense or Equity — unchecked')], reconcile=0 (want 0), group 'Expense'
OK     Type → Cost of Revenue: 1 run(s) [(…, 2, 'Income, Expense or Equity — unchecked')], reconcile=0 (want 0), group 'Expense'
OK     Type → Off-Balance Sheet: 1 run(s) [(…, 2, 'Bank and Cash, Credit Card or Off-Balance Sheet — unchecked')], reconcile=0 (want 0), group 'Off Balance'
OK     Type emptied through the API: no path matches, nothing is written: type None, group '', reconcile=0, 1 run(s) [(…, 3, …)], cause [(40002, '未通过分支')]
LIMIT  an exclusive gateway that no path matches: ends the run with status 3, cause [(40002, '未通过分支')] — unlike the path that writes nothing, which completes (2)
OK     back to Current Assets: 1 run(s) [(…, 2, 'no update step …')], reconcile=0
LIMIT  a write that sends Type unchanged with a real change to Non Trade: starts automation A all the same: 1 run(s) — the trigger narrowed to Type fires when Type is in the write, not only when it changes
OK     a write of Non Trade alone starts no run: 0 run(s) []
OK     Current Assets (box unchecked) → Receivable, box not sent: refused, so automation A never runs: refused; type now 'Current Assets'; 0 run(s) []; … (resultCode 32) …
LIMIT  create a Payable account with the box unchecked (validation rule, check type 1): accepted in an earlier run — TEST02 'TEST refused payable' is Payable, reconcile=1, active=0
OK     Current Assets → Receivable with the box ticked in the same write: 1 run(s) [(…, 2, 'Receivable or Payable — checked')]
OK     untick the box on a Receivable account: refused; reconcile=1; … (resultCode 32) …
OK     create an account with Code 410000 (No duplicates): refused; 0 record(s) added; … (resultCode 11) …
OK     set TEST Account's Code to 410000: refused; code 'TEST01'; … (resultCode 11) …
LIMIT  Code 'TEST-01' (a hyphen) through the API: accepted — stored 'TEST-01': the format check is the form's
OK     Code restored, and Display Name follows: TEST01 TEST Account
OK     Parent Account → 410000: parent '410000 Trade Income'; 410000's Child Accounts 0 → 1
LIMIT  TEST Account as its own parent through the API: accepted — parent reads 'TEST01 TEST Account'; the picker filter is the browser's
OK     Parent Account cleared: parent None; 410000's Child Accounts 0
OK     Archive through its workflow: active=0; automation A: 0 run(s) []
OK     Unarchive through its workflow: active=1; automation A: 0 run(s) []
OK     back to rest: Current Assets, box unchecked: 1 run(s) [(…, 2, 'no update step …')]
untouched: Contacts (30), Units & Packagings (10), Products (20), Product Variants (20), Product Categories (7), Journals (15), Invoices (33), Invoice Lines (13)
selfcheck: OK
platform limits recorded: 5
```

The earlier run that created TEST02 printed, for the same check: `ACCEPTED — a record was created and archived;
{"resultCode": 1, "data": {… "rowid": "c7928ba1-3497-4967-82e4-517da832bb96" …`, and TEST02's record log reads
*created 21:36:39* then *Payment Reconciliation: '0' → '1'* by the workflow at 21:36:44.

`roles.py check` — `OK — five stock roles in English with their roleType and members, four business roles with
their per-worksheet scopes, export on Accounting Administrator alone, and no members`.

`accounts.py untouched` — the other eight worksheets, before the build and after it:

```
Contacts             30 controls  sha256:9f7e59498c3081a1
Units & Packagings   10 controls  sha256:e57dc8775cd5038b
Products             20 controls  sha256:0f1bee0b9bfc3c25
Product Variants     20 controls  sha256:6eba14458f20e2a6
Product Categories    7 controls  sha256:e7e1b79f49099ff2
Journals             15 controls  sha256:3d6313d3be876df3
Invoices             33 controls  sha256:93d1ebe3ec9b2766
Invoice Lines        13 controls  sha256:22b1e1b7f197b880
```

— identical, line for line, before the first write and after the last. (Products' digest differs from the one 08
recorded because Products' static Unit default holds the whole Units record, `utime` included — `BUILDING.md`;
nothing wrote to Products here.)

#### Decisions taken while building

- **Non Trade's rule is a show rule**, not §1's "hide when Type is not Receivable or Payable". §1 wants it hidden
  for every other type **and for an empty Type**; *show while Type is any of Receivable, Payable* does exactly
  that, and it is the form every "… only for …" rule in this app takes (Journals). A hide on "is not any of"
  would depend on how the server compares an empty option (`BUILDING.md`).
- **The validation rule's message appears as the Type is picked** (hint type 0), not only on submit. Odoo raises
  its constraint on save, but in Odoo the box has already ticked itself by then; in HAP the early message is the
  nearest thing to that — it tells the user to tick the box before they try to save.
- **The fourth path names its six types** instead of catching everything else, so that an empty Type matches no
  path (Odoo computes nothing without a type) and a run through it can be told apart in the history from a run
  that matched nothing.
- **The two stock controls were reused, the stock Attachment dropped** by the first save of the empty worksheet.
- **The 87 records are keyed by Code in `ids.json`**, not by name: codes are unique and stable, and they are what
  part B's seed refers to.
- **Odoo's 64-character limit on `code` is not built** — §1 does not ask for it, and like any maximum length it
  would be a form check only.
- **Both TEST records stay**: TEST Account is the self-check's walk through the 19 types, TEST02 the evidence
  that the API can create what the rule forbids. Removing them after sign-off is two `record delete`s.

#### For a second opinion

1. **The rule and the automation (difference 1).** Keep as built — the user ticks the box when HAP asks — or look
   at HAP's **custom field events** (pd-openweb `widgetConfig/…/CustomEvent`: *on value change* → *set field
   value*), which is the only pre-save mechanism HAP appears to offer and so the only way to tick the box the
   moment Receivable or Payable is picked. **Not built and not proved**: it has no hap-cli support, and whether
   Nocoly exposes it would have to be seen in the field editor. It would sit beside automation A, not replace it
   (the API ignores form events).
2. **The rule is not checked on API creates (difference 2).** Nothing in part A creates a receivable or payable
   account unticked, but any future import should check it — or the rule could be accepted as form-only.
3. **Internal Group's quick filter is a search box**, not a list of groups (pending the UI). If that reads badly,
   the Type quick filter alone covers all of Odoo's seven search filters, since Odoo's group filters are sets of
   types.
4. **The picker's self-exclusion compares Display Names** and runs in the browser only; until the UI pass proves
   it, an account may be offered as its own parent.

#### Found while building

- **A text control can carry a format check** — `advancedSetting.filterregex`, the field editor's 限定输入格式: a
  JSON list of at most five `{name, value, err}` — and **it is the form's check only**: `record update` stored
  `TEST-01` against `^[A-Za-z0-9.]+$`. hap-cli has no builder for it.
- **The server re-serialises `filterregex` and a Relation's picker `filters` on save** — compact, in its own key
  order, with `"filters": null` added to each format-check entry — where `defsource` is kept byte for byte. They
  have to be compared parsed.
- **`hap app sort-worksheets <app> <section> <all ids in order>`** moves a worksheet within its menu group;
  `worksheet create --section-id` only appends.
- **A validation rule is checked on API updates only**: `record create` (`AddWorksheetRow`) accepted a Payable
  account with the box unchecked that the same rule refused on `record update` (`UpdateWorksheetRow`).
- **A validation rule runs before the save and a workflow after it**, so no workflow can make a write pass a rule
  — the re-typed account was refused and automation A never started.
- **A worksheet-event trigger 新增或更新 ('2') narrowed to fields fires on every create, and on an update whenever
  one of its fields is in the write, changed or not.**
- **`approval history`'s `count` is the number of rows on the page, not the total**, and a run registers about
  5 s after the write that starts it; the listing was also seen to lag by a row. New runs have to be told apart by
  instance id. The first `seed` waited out its full deadline because of the first, and the first self-check
  pinned a run on the wrong write because of the last.
- **A run's detail never lists a branch path node**, only the trigger, the gateway and the steps; **a run that
  matches no path of an exclusive gateway stops with status 3, cause 40002, "未通过分支"**.
- **`batch-add`, even in a first call, returns the two paths it reuses from a new gateway's default items with no
  name**; the paths it adds keep theirs, and the order is kept.
- **`hap worksheet record logs <ws> <rowid>`** gives every write to a record with its time, each field's old and
  new value and a `requestType` (1 an API update, 2 a workflow step, 8 a reverse relation's pairing) — the way to
  tie a run to the write that started it.
- **The view and filter editors treat a function formula as its result type** (pd-openweb
  `redefineComplexControl`), so a text formula's quick filter is a text filter (`dataType` 2, `filterType` 1).

All of these are in `BUILDING.md`.

## 3 · Test list

### Part A — the worksheet, run in the browser on 16 Sep 2026

**Part B is not built yet**, so these are part A's checks only. Run in the Nocoly UI in Chrome, stored values read
back with `hap worksheet record get` and automation A's runs with `hap approval history`.
**15 of 15 pass**, one with a difference.

| # | Test | Result |
|---|---|---|
| 1 | The sidebar | **Pass.** Invoicing reads Chart of Accounts · Journals · Invoices · Invoice Lines |
| 2 | The Chart of Accounts view | **Pass.** 88 rows (the 87 accounts and TEST01), Code A→Z, columns Code · Account Name · Type · Payment Reconciliation |
| 3 | The two quick filters | **Pass.** Type *any of* Payable + Receivable → 7 rows (124000, 124300, 124600, 124700, 221100, 221600, 221700), all reconciled — Odoo's Receivable and Payable filters together. Internal Group renders as a **search box**, not a list: "Income" → 8 rows, the six Income accounts and 999001, 999997 |
| 4 | A seeded account, field by field | **Pass.** 124700 SST Receivable: Display Name "124700 SST Receivable" and Internal Group "Asset", both read-only; Payment Reconciliation and Non Trade ticked; only the Archive button |
| 5 | The create form | **Pass.** Code \* "e.g. 101000" · Account Name \* "e.g. Current Assets" · Type \* with Odoo's help · Payment Reconciliation with its help · Parent Account "Root account" · Description "Enter description here...". No Display Name, no Internal Group, and no Non Trade until a Type calls for it |
| 6 | A duplicate code | **Pass.** 410000 → "Duplicates are not allowed" on Code as soon as it is typed, and Submit refused |
| 7 | A malformed code | **Pass.** "TEST-03" → "The account code can only contain alphanumeric characters and dots." and the toast "Please fill in the record correctly". Form-side only: the API stores such a code (§2) |
| 8 | Automation A, through the form | **Pass.** TEST01 Current Assets → Receivable, box ticked, saved: stays ticked. → Bank and Cash, saved: automation A cleared it (read back 0) |
| 9 | Payment Reconciliation hidden for bank, card and off-balance | **Pass.** It disappears the moment Type is Bank and Cash |
| 10 | Non Trade only for receivable and payable | **Pass.** Shown for Receivable, hidden for Current Assets and Bank and Cash |
| 11 | A receivable account must be reconcilable | **Pass, with a difference.** The message "You cannot have a receivable/payable account that is not reconcilable." appears **as soon as Type becomes Receivable**, before any save, and clears when the box is ticked. Odoo ticks the box itself (`_compute_reconcile`); here the user ticks it — automation A runs only after a save, and the rule stops that save |
| 12 | The Parent Account picker | **Pass.** On TEST03, searching "TEST" offers only TEST01: the account itself and the archived TEST02 are left out. Titles are Display Names, with **+ Record** at the foot |
| 13 | Archive and Unarchive | **Pass.** Archive asks "Are you sure that you want to archive this record?" and moves TEST03 to the Archived view; Unarchive, with no confirmation, moves it back |
| 14 | Internal Group | **Pass.** Asset on Receivable and on Bank and Cash, Income on Income; all 19 types walked through the CLI by `accounts.py selfcheck` |
| 15 | An unrelated edit does not re-fire automation A | **Pass.** A Description-only save on TEST03 (stored 22:25:24) added no run: the form sends only the fields that changed |

TEST records left by part A: **TEST01** "TEST Account" (now Bank and Cash, active), **TEST02** "TEST refused payable"
(archived) and **TEST03** "TEST UI account" (Income, active, with a Description).
