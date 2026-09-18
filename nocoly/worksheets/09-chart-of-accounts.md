# 09 · Chart of Accounts

| | |
|---|---|
| Nocoly app | ERP Master · menu group **Invoicing**, first — before Journals, as in Odoo's Configuration menu |
| Worksheet | Chart of Accounts |
| Odoo model | `account.account` |
| Reference | **casimir.odoo.com — Odoo saas~19.4+e**: fields by module, form, list, search, the window action, all 87 accounts, `ir.default`, the raw view arch that places every account field on Journals, Product Categories, Products and Contacts, and the accounts of the seeded journal items — extracted read-only to `nocoly/reference/odoo-19.4/account.account.md`, with the data in `nocoly/data/casimir-accounts.json`. Behaviour the tenant cannot show is read from the Odoo 19.0 source in this repo (`addons/account/models/account_account.py`, `account_journal.py`, `account_move_line.py`, `partner.py`, `product.py`), minding where 19.4 has moved on — parent accounts replace account groups |
| Phase | 1 — **bundle 2 of 6** (Product Categories · Chart of Accounts · Payment Terms · Countries · States · Taxes) |
| Status | §1 written 16 Sep 2026 · **part A — the worksheet — built and UI-tested 15/15 on 16 Sep 2026** · **part B — the account fields on the other worksheets — built, self-checked and UI-tested 12/13 on 17 Sep 2026**, automation B's journal fallback aligned with Odoo the same day · **27 of 28 pass, 1 not run** (§3) · ready for review |

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

**Part B was not built then** (it is now — *Part B*, below). The account fields on Contacts, Products, Product
Categories, Journals and Invoice Lines, their seed, automation B and the per-field hiding in the roles were all still
to do, and no other worksheet was written to: every save was bracketed by the id-by-id comparison, and `untouched`
reads the same digests after the build as before it (below).

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
3. **Internal Group's quick filter is a search box**, not a list of groups — **seen on screen 18 Sep 2026** in
   the cross-check pass (`CROSSCHECK.md`): Type renders as a dropdown reading *Please select*, Internal Group as a
   text box reading *Search*. If that reads badly, the Type quick filter alone covers all of Odoo's seven search
   filters, since Odoo's group filters are sets of types.
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

### Part B — the account fields on the worksheets already built

Built on 17 Sep 2026 by `nocoly/build/accounts.py` — steps `contacts → products → categories → journals → lines →
automation-b → visibility → references`, or `all-b` for all of them followed by `check-b`. Helpers: `check-b` reads
the configuration back against §1, `verify-b` the references, `selfcheck-b` proves automation B on TEST records,
`runs-b` reads its run history, `rerun-b` runs again every owning step this bundle extended and proves each writes
nothing, and `records-b` compares every record of the nine worksheets with a snapshot taken before the first write
(`backups/partb_snapshot_baseline_20260917-090220.json`, not committed). Every step reads the live state first and is
safe to re-run: after the build, `all-b` ran every step again and wrote nothing (below).

**Changed after the browser pass, at the coordinator's call (17 Sep 2026, 11:40–11:43):** the journal's Default
Account fills only an **empty** Account, as Odoo's does — both workflows of automation B, and the Invoice Lines
Account description to match (*Automation B*, below). Nothing else changed.

**Who owns what.** This script adds each control with `add-fields` — which parks it at row 9999 — and owns what no
other step rewrites: the Relation itself, its alias, its picker filter, its static default, automation B, the
references and the checks. **Each worksheet's own script places it**: its `layout` step is the read-modify-write save
that moves a control, so its `PLACE` carries the new controls and every row they pushed down, and its descriptions
and placeholders carry theirs wherever that step rewrites them. The rule and column changes went into the owning
scripts' own fixed lists, and the account steps here run exactly those steps. **roles.py** owns the per-field hiding.
Every write — add, layout, rules, views, roles, references — was bracketed by a control-by-control comparison of all
nine worksheets (`b_snapshot` / `b_expect`) that allows only the changes it names, and the rules and views steps by a
comparison of the worksheet's rules and views as well; Chart of Accounts, Units & Packagings and Product Variants
read back identical after every one.

**Scripts changed**, beyond `accounts.py` (a part B section, its steps and helpers):

| Script | Change |
|---|---|
| `common.py` | New `save_controls(ws, controls)`: the full save through the CLI's session instead of the command line, answer checked, static Relation defaults sent as record ids (`relation_defaults_by_id`). `add_fields` re-saves through it |
| `contacts.py` | `PLACE` / `TABS`: the tab Invoicing (row 18) with Account Receivable \| Account Payable (row 19); Notes and everything under it two rows down. `DESC`: the two accounts' descriptions. `rules`: the tab rule. Every full save through `common.save_controls` |
| `products.py` | `TAB_ROWS` / `PLACE`: the tab Accounting (row 13) with Income Account \| Expense Account (row 14); Active to row 15. `HINTS` ("From Category") and `DESC` (Odoo's help). Both full saves through `common.save_controls` |
| `prodcat.py` | `PLACE`: the tab Accounting at row 2, Income Account \| Expense Account at row 3, the rows under them two down; `TAB_OF`, `BUNDLE_2`, `NEW` and `DESC` for the three controls. `desired` places a control in its tab and owns only a tab's place; `layout` places bundle 2's controls when they exist. Every full save through `common.save_controls` |
| `journals.py` | `PLACE`: the five accounts on Journal Entries (rows 4–6), everything under them three rows down. `DESC`: their help. `RULES`: five rules. `COLUMNS`: Default Account after Sequence Prefix. `rules` and `views` leave the account rules and column out on a build that has not reached bundle 2. Its full save through `common.save_controls` |
| `invlines.py` | `PLACE`: Account at row 4, everything under it one row down; `ALIAS`, `DESC` (and Display Type's description now lists Account), `RELATIONS`, `BUNDLE_2`. `FIGURES`, `VIEW_COLUMNS` and `SUBTABLE_COLUMNS` carry Account after Label. `layout`, `rules` and `views` take Account in when it exists. `save_worksheet_controls` now calls `common.save_controls` |
| `roles.py` | `HIDDEN_FIELDS`: the account fields hidden per role; `reconcile` writes them and reads them back (a field not built yet is skipped), `check` reads them in the Roles page's model and through V3 and reports a missing one |

**Owning steps re-run** (`rerun-b`, after the build, each compared before and after): `contacts.py layout`, `contacts.py
rules`, `products.py layout`, `prodcat.py layout`, `journals.py layout`, `journals.py rules`, `journals.py views`,
`invlines.py layout`, `invlines.py rules`, `invlines.py views`, `roles.py create` — none of them changed anything
(output below). During the build itself `contacts.py layout` and `rules`, `products.py layout`, `prodcat.py layout`,
`journals.py layout`, `rules` and `views`, `invlines.py layout` (with its `place_subtable`), `rules` and `views`, and
`roles.py create` are the steps that made the changes.

#### What was built, worksheet by worksheet

Every account field is a **one-way** Relation → Chart of Accounts (`6aaa92ae805aef70328667da`), single, shown as a
dropdown, required nowhere on the field, with a picker filter that starts with *Active is checked* (a picker filter runs
in the browser only — the UI pass proves it). "The income-and-expense filter" is *Type is none of Receivable, Payable,
Bank and Cash, Credit Card, Off-Balance Sheet* (Odoo's `ACCOUNT_DOMAIN`). Chart of Accounts gained no control: each
Relation's `sourceControlId` names an id the server reserved and no control carries.

**Contacts (01)** — 30 controls → 33.

| Element | Built | Id |
|---|---|---|
| Tab **Invoicing** | row 18, between Sales & Purchase (13) and Notes (now 20) | `6aab3ed9bd43f55762c71d3e` |
| **Account Receivable** | `property_account_receivable_id`; row 19 col 0, size 6, in Invoicing; picker Type is Receivable; **default 124000 Account Receivable**; description "Odoo reads the company's default, 124000 Account Receivable, until a contact is given its own." | `6aab3f17e43d174ab374a802` |
| **Account Payable** | `property_account_payable_id`; row 19 col 1; picker Type is Payable; **default 221100 Account Payable**; the same description with 221100 Account Payable | `6aab3f17e43d174ab374a804` |
| Rule *Invoicing hidden for a contact under a company* | interaction · **hide** the tab Invoicing while Company is not empty — a new contact, with no Company yet, shows it | `6aab4032e54d2a34fa4e1f69` |

Moved by `contacts.py layout`: the tab Notes 18 → 20, Notes 19 → 21, Active 20 → 22, Display Name 21 → 23, Parent
name 22 → 24.

**Products (03)** — 20 controls → 23.

| Element | Built | Id |
|---|---|---|
| Tab **Accounting** | row 13, after Inventory (11) | `6aab40a1bd43f55762c71dc1` |
| **Income Account** | `property_account_income_id`; row 14 col 0 in Accounting; the income-and-expense filter; **placeholder "From Category"**; no default; Odoo's help | `6aab40a3e43d174ab374a818` |
| **Expense Account** | `property_account_expense_id`; row 14 col 1; the same filter and placeholder; Odoo's help (two sentences) | `6aab40a3e43d174ab374a81a` |

Moved by `products.py layout`: Active 13 → 15. No column and no quick filter (§1 asks for none).

**Product Categories (08)** — 7 controls → 10.

| Element | Built | Id |
|---|---|---|
| Tab **Accounting** | row 2 | `6aab4109e43d174ab374a821` |
| **Income Account** | `property_account_income_categ_id`; row 3 col 0 in Accounting; the income-and-expense filter; **default 410000 Trade Income**; Odoo's help | `6aab410b7d58b0f44930f5e5` |
| **Expense Account** | `property_account_expense_categ_id`; row 3 col 1; the same filter; **default 510000 Costs**; Odoo's help | `6aab410b7d58b0f44930f5e7` |

Moved by `prodcat.py layout`: Child Categories and # Products 2 → 4, Products 3 → 5, Parent Complete Name 4 → 6.

**How the tab sits beside the two relation lists.** HAP's tab bar at the foot of a record does not simply follow the
rows. pd-openweb's `getControlsByTab` takes the type-52 tabs **and** the relation lists whose `showtype` is "6" in row
order, then appends the lists whose `showtype` is "2". Here **Child Categories is a "6" and Products a "2"** — so a tab
placed under the lists (the first save put it at row 5) would have landed *between* them: Child Categories ·
Accounting · Products. At row 2 the bar reads **Accounting · Child Categories · Products** — Odoo's own page first,
HAP's two lists together. That is read from the source and the stored rows, not seen in a browser: the UI pass
confirms it.

**Journals (05)** — 15 controls → 20; 5 rules → 10.

| Element | Built | Id |
|---|---|---|
| **Default Account** | `default_account_id`; row 4 col 0 on Journal Entries; every active account; description: the six labels Odoo gives it by Type | `6aab4249e54d2a34fa4e1f82` |
| **Suspense Account** | `suspense_account_id`; row 4 col 1; Type is Current Assets; Odoo's help | `6aab4249e54d2a34fa4e1f84` |
| **Profit Account** | `profit_account_id`; row 5 col 0; Type is Income or Other Income; Odoo's help | `6aab4249e54d2a34fa4e1f86` |
| **Loss Account** | `loss_account_id`; row 5 col 1; Type is Expenses; Odoo's help | `6aab4249e54d2a34fa4e1f88` |
| **Private Share Account** | `non_deductible_account_id`; row 6 col 0; every active account; Odoo's help | `6aab4249e54d2a34fa4e1f8a` |
| Rule *Default Account is required for Sales, Purchase, Bank, Cash and Credit Card* | interaction · require | `6aab4279bd43f55762c71de8` |
| Rule *Suspense Account only for Bank, Cash and Credit Card* | interaction · show | `6aab427a7d58b0f44930f60a` |
| Rule *Suspense Account is required for Bank, Cash and Credit Card* | interaction · require | `6aab427a7d58b0f44930f610` |
| Rule *Profit and Loss Accounts only for Bank and Cash* | interaction · show, both fields | `6aab427b7d58b0f44930f612` |
| Rule *Private Share Account only for Purchase* | interaction · show | `6aab427c805aef7032866c1d` |
| Views **Journals** and **Archived** | columns Journal Name · Type · Sequence Prefix · **Default Account**; filter, sort and quick filter unchanged | `6aa8f5191204328eb1af162e` · `6aa8f7074720c515252bf2c8` |

Moved by `journals.py layout`: the two dedicated sequences 4 → 7, the Journal Entries divider 5 → 8 and note 6 → 9, the
tab Advanced Settings 7 → 10, the two communication fields 8 → 11, its divider 9 → 12 and note 10 → 13, Active 11 →
14. The rules are of the existing kind: every *show* hides its field while Type is empty, and a field a rule hides is
required by a second rule rather than on the field.

**Invoice Lines (07), and the lines table inside Invoices (06)** — 13 controls → 14; Invoices keeps 33.

| Element | Built | Id |
|---|---|---|
| **Account** | `account_id`; row 4, size 12, after Label; Type is none of Receivable, Payable, Off-Balance Sheet; not required; a description of what fills it (Odoo has no help): "The account the line posts to. A product line saved without one is given it, and a change of Product gives it again: the product's Income Account, else its category's — the Expense Accounts on a vendor document. The journal's Default Account fills it only when it is still empty, and is the only source on a journal entry. A section, a subsection and a note carry none." | `6aab42fdbd43f55762c71ed6` |
| Rule *A section or a note carries no figures* | the same rule, now hiding **Product, Account**, Quantity, Unit, Unit Price, Discount (%) and Subtotal | `6aaa2d3c7d58b0f44930eb72` |
| View **Lines** | Number · Label · **Account** · Product · Quantity · Unit · Unit Price · Discount (%) · Subtotal | `6aaa2b50e54d2a34fa4e0225` |
| Invoices subtable **Lines** | Sequence · Display Type · Product · Label · **Account** · Quantity · Unit · Unit Price · Discount (%) · Subtotal (`showControls` and `controlssorts`), saved by `invlines.py place_subtable` through the session — `update-fields --controls` cannot carry Invoices | `6aaa2baae43d174ab3749de9` |

Moved by `invlines.py layout`: Quantity and Unit 4 → 5, Unit Price and Discount (%) 5 → 6, Subtotal 6 → 7, Number and
Accounting Date 7 → 8, Status 8 → 9; Display Type's description now names Account among what a section hides. On
Invoices only the subtable's columns changed.

#### Automation B — Invoice Lines: fill the account

Two workflows with one body, because a HAP worksheet trigger takes one event:

| Workflow | Trigger | Id |
|---|---|---|
| *Invoice Lines: fill the account of a new line* | 新增 ('1') on Invoice Lines · condition: Display Type is Product **and** Account is empty — a line created with an Account keeps it | `6aab44254f2a99acac0f026f` |
| *Invoice Lines: fill the account when the Product changes* | 仅更新 ('4') narrowed to **Product** · condition: Display Type is Product | `6aab447416473257ad590b41` |

Both published, with the same body:

1. **Get the invoice** — Invoices where Record ID = the line's Invoice;
2. **Get the product variant** — Product Variants where Record ID = the line's Product;
3. **Get the product** — Products where Record ID = the variant's Product;
4. **Get the product's category** — Product Categories where Record ID = the product's Category;
5. **Get the invoice's journal** — Journals where Record ID = the invoice's Journal;

each a search step (406) that carries on when nothing is found and whose condition is **ignored when abnormal**
(`ignoreEmpty` 1 — difference 1 below); then the exclusive gateway **Which account does the line take?** with
seven paths, each running into one update step that writes Account on the trigger line from the record named:

| Path | Its condition groups (any one) | Step · value |
|---|---|---|
| Customer document — the product's Income Account | line names its Invoice · Type is Customer Invoice, Customer Credit Note or Sales Receipt · line names a Product · the variant names its Product · the product's Income Account is set | *Take the product's Income Account* |
| Customer document — the category's Income Account | … the same, but the product's Income Account is empty · the product names its Category · the category's Income Account is set | *Take the category's Income Account* |
| Customer document — the journal's Default Account | invoice, customer Type, the invoice names its Journal, the journal's Default Account is set, **the line's Account is empty** — **and** one of: the line names no Product · the variant names no Product · the product has no Income Account and no Category · the product has no Income Account and its category none | *Take the journal's Default Account (customer document)* |
| Vendor document — the product's Expense Account | as the first path, for Vendor Bill, Vendor Credit Note, Purchase Receipt and the Expense Account | *Take the product's Expense Account* |
| Vendor document — the category's Expense Account | as the second | *Take the category's Expense Account* |
| Vendor document — the journal's Default Account | as the third, four groups | *Take the journal's Default Account (vendor document)* |
| Journal entry — the journal's Default Account | invoice · Type is Journal Entry · the invoice names its Journal · the journal's Default Account is set · **the line's Account is empty** | *Take the journal's Default Account (journal entry)* |

**The journal's Default Account fills only an empty Account.** As first built, the journal paths followed §1's "the
first of" product → category → journal, so a Product change that found nothing on the product or its category
replaced the account a line already carried with the journal's default. Odoo's `_compute_account_id` keeps it —
`accounts['income'] or line.account_id` — and the journal's default reaches only a line with no account. At the
coordinator's call after the browser pass, every group of the three journal paths gained *the line's Account is
empty* (`b_paths`), in both workflows, republished at 11:42 on 17 Sep 2026 (version 3 of each: the first build, the
guards, this) and read back node by node. The product's and the category's accounts still replace whatever the line
carries when its Product changes. For the new-line workflow the condition changes nothing — it only runs on a line
with no Account — but it keeps the two bodies one.

The paths are written out in full, guards and all, so none depends on the order the gateway reads them in. A run that
matches none stops at the gateway with 40002 *未通过分支* and writes nothing — §1's "left as it is" (a journal entry on a
journal with no Default Account; a Product change that finds nothing on the product or its category for a line that
already has an Account, which keeps it; also a line with no Invoice, or a document with no Journal and nothing from
the product). Neither workflow starts the other: both write Account alone, and the second is narrowed to Product. **Nor
does automation B's write start 07's roll-up**, though the roll-up triggers on any change to a line: its history holds
one run for every API write of a line — the eight Account writes of the references included — and none for the writes
automation B made (each in the line's record log as `requestType` 2, a few seconds after the write that started it).

**Proved through the CLI on TEST records** (`selfcheck-b`, output below), on the build as changed: the new-line
workflow on nine *TEST B2* lines created after the change, and then the Product-change workflow walking every path of
the gateway on the same lines — the journal's Default Account for a line whose Account is empty, the stop when none
matches for a line that has one, and the product's and category's accounts replacing either.

#### Roles — the account fields hidden by role

**A HAP role can hide a single field**, so §1's second table is built as field permissions. Each sheet of a
fine-grained role lists every control in `fields[]` with three switches — the Roles page's 新增 · 查看 · 编辑 (add ·
view · edit), stored as `notAdd` · `notRead` · `notEdit`; V3's `fieldPermissions` reads them as `add` · `read` ·
`edit`. `roles.py` `HIDDEN_FIELDS`:

| Fields | Accounting Administrator | Accountant | Invoicing | Accounting Read-only |
|---|---|---|---|---|
| Journals' five accounts; Products' and Product Categories' Income and Expense Account; Invoice Lines' Account | visible | visible | **hidden** | visible |
| Contacts' Account Receivable and Account Payable | visible | visible | **hidden** | **hidden** |

A hidden field has all three switches set: not on the create form, not visible, not editable. The tabs **Invoicing**
(Contacts) and **Accounting** (Products, Product Categories) hold nothing but those accounts, and the Roles page
hides a tab by itself once every field in it is hidden (pd-openweb `RoleSet/TooltipSetting`); `roles.py` does the same
for those three tabs and touches no other tab — Journal Entries keeps its sequences. Read back in the Roles page's
own model and through V3; every role's model otherwise identical to the snapshot taken before the build, the five
stock roles included.

#### Records

The references of Records step 2, from `data/casimir-accounts.json`, each written only where it differed and read
back at once (`references`), then read again by `verify-b`: **all 10 contacts** (3 tenant, 7 TEST) → 124000 / 221100;
**all 11 categories** (7 tenant, 4 TEST) → 410000 / 510000; **INV** Default 410000, **BILL** Default 510000, **BNK1**
Default 120001, Suspense 120002, Profit 999001, Loss 999002, and the other eight journals (four tenant, four TEST) none;
**the eight tenant invoice lines** → 410000; **all 18 products** none. Nothing was written onto TEST01, TEST02 or
TEST03. The eight line writes each started 07's roll-up, and `invlines.py verify` read every invoice's amounts back
equal to its own lines afterwards.

#### Decisions taken while building

- **The account Relations' text lives with the step that rewrites it.** Descriptions and placeholders sit in the owning
  script's `DESC` / `HINTS` wherever its `layout` rewrites them (Products, Product Categories, Journals, Invoice Lines);
  Contacts' descriptions too, for one place to look, though its `layout` never touches a description. The alias,
  picker filter and default live in `accounts.py`'s `B_FIELDS`.
- **Contacts' Invoicing tab holds the two accounts side by side** (row 19, 6 \| 6), and no divider: §1 names no group
  title, and Odoo's group *General* would head two fields.
- **Products' Income and Expense Account side by side** (row 14), as Weight \| Volume above them.
- **Product Categories' Accounting tab at row 2**, the rows under it moved: the tab bar then reads Accounting · Child
  Categories · Products instead of splitting HAP's two lists (above). Kept at the coordinator's call.
- **Journals' layout is §1's:** Default \| Suspense, Profit \| Loss, Private Share, then the sequences.
- **Invoice Lines' Account at full width** under Label, as Product and Label above it.
- **Invoice Lines' Account got a description** of what fills it; Odoo has none, and §1 gives none. Kept, and reworded
  after the change below as the coordinator suggested (second opinion 3).
- **Five Journals rules, not fewer:** requirement and visibility are separate rules, as the existing Payment
  Communications pair is, and Profit and Loss share one rule because they share a condition.
- **Automation B is two workflows** — a line created with no Account, and a line whose Product changes — because one
  trigger cannot tell a create from an update, and a line created with an Account must keep it.
- **The gateway's paths carry guards**, written out in full (above, and difference 1).
- **The journal's Default Account fills only an empty Account** — Odoo's rule rather than §1's flattened "first of",
  at the coordinator's call after the browser pass (above, and difference 2).
- **Hidden means all three role switches**, add included, where §1 says only "hidden"; and the three tabs follow their
  fields as the Roles page would make them. Kept at the coordinator's call: when single-field hiding works, a tab
  left empty for a role hides with its fields; §1's "do not hide whole tabs" was about approximating that hiding.
- **The TEST documents on tenant journals leave no draft behind that an Archive guard would count**: Sales already holds
  drafts, and the TEST vendor bill on Purchases was cancelled through the Cancel button's own workflow at the end.

#### What §1 expects and HAP does not do, and what the build found

**1 · A search on an empty value fails the run — so the searches ignore it, and the paths guard it.** The first build of
automation B had plain searches, set to carry on when nothing is found. On a line with **no Product** the run **failed**
at *Get the product variant* — status 4, cause 100000 *筛选条件值为空 记录ID*, "the filter value is empty: Record ID" — and
nothing was written: §1's journal fallback never ran. The same would have happened to any product with no category.
The condition editor offers *条件异常时忽略* (`ignoreEmpty`, "ignore the condition when it is abnormal") on a dynamic
value, and with it the run carries on — **but the step then has no condition at all and still returns a record**: the
run detail's `sourceId` shows the variant of TEST Product found for a line with no product, and the category Goods for
a product with none. So each path checks the Relation every record it reads was found through. With the guards the same
two lines take the journal's Default Account, and without them test 7b would have written TEST Product's own 420000.
The first failed run is kept as evidence (*TEST B no product*).

**2 · The journal's Default Account, as Odoo applies it — changed after the browser pass.** §1: "the first of"
product → category → journal. Odoo's `_compute_account_id` applies the product's or category's account whenever there
is one, but the **journal's default only when the line has no account at all**. The first build followed §1, so a
Product change that left nothing from product and category replaced an account the line already carried with the
journal's default, where Odoo keeps it. At the coordinator's call the journal paths now require an empty Account
(above): a line with an Account keeps it, a line without one takes the journal's default — `selfcheck-b` 3p proves
both on the same line and the same change, and 3v, 3n and 3e the same on a vendor bill, a line with no Product and a
journal entry.

**3 · A save that sets Product and Account together — a known difference, for §3** (below). The change workflow runs
after the save and writes the product's or the category's account over the one the user picked in the same save; Odoo
keeps a value written in the same `write`. A user who changes the Product and wants another account sets Account in
a second save. The journal's Default Account no longer does this since the change: a line whose Account is set keeps
it.

**4 · The API applies no defaults, and a role may hide a defaulted field from the person creating the record.**
Contacts' and Product Categories' defaults apply in the form only, so an import has to set the accounts itself.
Whether HAP's form applies a static default to a field the role cannot see — an Invoicing user creating a contact —
is for the UI pass with a member in the role; §1 relies on the defaults and the seed to keep Contacts' accounts
filled.

**5 · Picker filters and the tab bar are browser-side**, and so is whether a hidden field is really gone for a role
member: all stored and read back, none seen in a browser.

#### Known differences, for §3

| Difference | Odoo 19.4 | Here | Why |
|---|---|---|---|
| **A save that sets Product and Account together** | Keeps the Account written in the same `write`; `_compute_account_id` fills only what that write left alone | The Product-change workflow runs after the save and writes the product's or the category's account over the one picked in that save | The workflow starts after the save and is not told that the same save also wrote Account. A user who wants another account sets it in a second save. (The journal's Default Account never overwrites: its paths require an empty Account.) |

#### For a second opinion — answered by the coordinator, 17 Sep 2026

1. **Difference 2** — **changed:** the journal paths of both workflows require an empty Account, as Odoo does (above).
2. **The role tabs** — **kept:** the three tabs hide with their fields; §1's "do not hide whole tabs" was about
   approximating single-field hiding, which HAP does not need here.
3. **Invoice Lines' Account description** — **kept**, and reworded for the change as the coordinator suggested, with
   one departure: "fills it only when it is still empty, and **is the only source** on a journal entry", where the
   suggestion read "…and on a journal entry" — on a journal entry, too, the default fills only an empty Account.
4. **Product Categories' rows** — **kept:** Accounting stays first in the tab bar, the four controls two rows down.

#### Found while building

- **A save that sends a static Relation default back as the whole record clears it** — `staticValue` reads back `""`,
  no error. `common.save_controls` sends record ids.
- **`update-fields --controls` breaks on any worksheet with a few Relations to a large one**, not only on a 子表: the
  limit is 128 KiB for one argument, and each Relation to Chart of Accounts brings a 55 KB snapshot.
- **`add-fields` stores `fieldPermission` ""**; the first layout save writes "111".
- **A search step whose filter value is empty fails the run**, whatever it is told to do when nothing is found;
  **条件异常时忽略 lets it through and it then returns an arbitrary record**.
- **`approval history-detail` gives each step's `sourceId`**, the record it found or wrote.
- **A worksheet-event workflow's write of its trigger line started none of that worksheet's event workflows**: 07's
  roll-up ran for every API write of a line and for none of automation B's writes.
- **A path of an exclusive gateway takes several OR-ed condition groups.**
- **The tab bar orders type-52 tabs and showtype-6 lists by row, then showtype-2 lists.**
- **A fine-grained role can hide a single field** (`fields[]`: `notAdd` · `notRead` · `notEdit`), a new control joins
  every role visible, and the Roles page hides a tab whose fields are all hidden.

All of these are in `BUILDING.md`.

#### Self-checks through the CLI

`check-b` — each worksheet's accounts and new tab against §1 and the owner's tables, every control where its
owner puts it and the owners' own layout checks, the seven rules, the columns and the subtable, automation B's two
workflows node by node, the roles' field hiding (it runs `roles.py check`), and Chart of Accounts unchanged. Run after
the change, 17 Sep 2026 11:46–11:47 — so every journal group read back with its *Account is empty*, and Account's
description as reworded:

```
Product Categories' tab bar, as pd-openweb orders it: Accounting · Child Categories · Products
check: OK — five stock roles in English with their roleType and members, four business roles with their per-worksheet
scopes, export on Accounting Administrator alone, the account fields hidden from Invoicing and Accounting Read-only as
09 §1 says, and no members
check-b: OK — the accounts on Contacts, Products, Product Categories, Journals and Invoice Lines with their tabs,
places, pickers and defaults; the rules, columns and subtable; automation B published with its guarded paths, the
journal's Default Account only on an empty Account; the roles' per-field hiding; Chart of Accounts unchanged
```

The change itself (`accounts.py lines`, then `accounts.py automation-b`, 11:40–11:42), each write bracketed by the
control-by-control comparison of the nine worksheets:

```
lines         Invoice Lines: invlines.py layout — moves {}; differences {"Account": {"desc": [...]}}
              invlines.py layout (Invoice Lines, and the subtable on Invoices): compared control by control
                Invoice Lines: 'Account' desc
                identical: Contacts (33), Products (23), Product Categories (10), Journals (20), Invoices (33),
                Units & Packagings (10), Product Variants (20), Chart of Accounts (11)
              Invoice Lines: read back as specified — Account
automation-b  Invoice Lines: fill the account of a new line — published {'isPublish': True, 'processWarnings': [],
              'errorNodeIds': []}; nodes (25)
              Invoice Lines: fill the account when the Product changes — published {'isPublish': True, ...}; nodes (25)
              automation B (no control may change): identical: all nine worksheets
```

`automation-b` reads each workflow back against `b_paths` before it returns and stops on any difference; read again
directly, each workflow's three journal paths carry *the line's Account is empty* in all 4 + 4 + 1 groups, the four
product and category paths in none, both enabled and published (`publishStatus` 2, version 3).

`selfcheck-b` — on the build as changed, 17 Sep 2026 11:47–12:06. `DIFF` would be the build not doing what §1 and
the coordinator's call say, `LIMIT` is platform behaviour recorded (times of day; lines shortened):

```
OK     TEST Product given its own Income and Expense Accounts: 420000 / 510100
LIMIT  a product line with no Product, in the first build (a search on an empty Relation):
       [(10:02:08, 4, None, 100000, '筛选条件值为空 记录ID')] — the run failed at "Get the product variant"; Account —
OK     1. customer invoice, the product has no account of its own: [(11:48:25, 2, "Take the category's Income Account")]; Account 410000
OK     2. customer invoice, the product has its own Income Account: [(11:48:53, 2, "Take the product's Income Account")]; Account 420000
OK     4. vendor bill: [(11:49:20, 2, "Take the category's Expense Account")]; Account 510000
OK     5. created with an explicit Account: no run of either workflow (0 / 0); Account 421000
OK     6. journal entry on a journal with no Default Account: [(11:50:16, 3, None, 40002, '未通过分支')]; Account —
OK     7. a product line with no Product: [(11:50:42, 2, "Take the journal's Default Account (customer document)")]; Account 410000
OK     8. journal entry on a journal with a Default Account: [(11:51:10, 2, "Take the journal's Default Account (journal entry)")]; Account 410000
OK     9. a Section line: no run of either workflow (0 / 0); Account —
OK     10. a product with no category and no account of its own: [(11:52:09, 2, "Take the journal's Default Account (customer document)")]; Account 410000
OK     3. customer invoice (line 1): Product → [TEST-0001] TEST Product: [(11:52:42, 2, "Take the product's Income Account")]; Account 420000
OK     3. customer invoice (line 1): Product → [CONS-0002] Whiteboard Marker Set: [(11:53:38, 2, "Take the category's Income Account")]; Account 410000
OK     3p. a product with no category (line 2): Product → [TEST-0004] TEST Variant From UI: [(11:54:04, 3, None, 40002, '未通过分支')]; Account 420000
OK     3p. a product with no category (line 2): Product → [TEST-0001] TEST Product: [(11:54:30, 2, "Take the product's Income Account")]; Account 420000
OK     3p. a product with no category (line 2): Account → none, written alone: 0 / 0 run(s); Account —
OK     3p. a product with no category (line 2): Product → [TEST-0004] TEST Variant From UI: [(11:55:23, 2, "Take the journal's Default Account (customer document)")]; Account 410000
OK     3p. a product with no category (line 2): Product → [TEST-0001] TEST Product: [(11:55:51, 2, "Take the product's Income Account")]; Account 420000
OK     3v. vendor bill (line 4): Product → [TEST-0001] TEST Product: [(11:56:50, 2, "Take the product's Expense Account")]; Account 510100
OK     3v. vendor bill (line 4): Product → none: [(11:57:15, 3, None, 40002, '未通过分支')]; Account 510100
OK     3v. vendor bill (line 4): Product → [CONS-0002] Whiteboard Marker Set: [(11:57:40, 2, "Take the category's Expense Account")]; Account 510000
OK     3v. vendor bill (line 4): Account → none, written alone: 0 / 0 run(s); Account —
OK     3v. vendor bill (line 4): Product → none: [(11:58:36, 2, "Take the journal's Default Account (vendor document)")]; Account 510000
OK     3v. vendor bill (line 4): Product → [CONS-0002] Whiteboard Marker Set: [(11:59:03, 2, "Take the category's Expense Account")]; Account 510000
OK     3n. customer invoice, no Product (line 7): Product → [CONS-0002] Whiteboard Marker Set: [(11:59:32, 2, "Take the category's Income Account")]; Account 410000
OK     3n. customer invoice, no Product (line 7): Account → 421000, written alone: 0 / 0 run(s); Account 421000
OK     3n. customer invoice, no Product (line 7): Product → none: [(12:00:27, 3, None, 40002, '未通过分支')]; Account 421000
OK     3n. customer invoice, no Product (line 7): Product → [CONS-0002] Whiteboard Marker Set: [(12:00:52, 2, "Take the category's Income Account")]; Account 410000
OK     3n. customer invoice, no Product (line 7): Account → none, written alone: 0 / 0 run(s); Account —
OK     3n. customer invoice, no Product (line 7): Product → none: [(12:01:47, 2, "Take the journal's Default Account (customer document)")]; Account 410000
OK     3e. journal entry on Sales (line 8): Account → 421000, written alone: 0 / 0 run(s); Account 421000
OK     3e. journal entry on Sales (line 8): Product → [TEST-0001] TEST Product: [(12:03:07, 3, None, 40002, '未通过分支')]; Account 421000
OK     3e. journal entry on Sales (line 8): Account → none, written alone: 0 / 0 run(s); Account —
OK     3e. journal entry on Sales (line 8): Product → [CONS-0002] Whiteboard Marker Set: [(12:04:24, 2, "Take the journal's Default Account (journal entry)")]; Account 410000
OK     3e. journal entry with no Default Account (line 6): Product → [TEST-0001] TEST Product: [(12:04:52, 3, None, 40002, '未通过分支')]; Account —
OK     3e. journal entry with no Default Account (line 6): Product → [CONS-0002] Whiteboard Marker Set: [(12:05:17, 3, None, 40002, '未通过分支')]; Account —
OK     3b. a write that leaves Product out (Quantity 2) starts neither workflow: 0 / 0 run(s); Account 410000
OK     TEST Product put back: no account of its own: — / —
OK     'TEST B vendor bill' cancelled through the Cancel workflow, so Purchases holds no new draft: Cancelled
selfcheck-b (no control may change): compared control by control — identical: all nine worksheets
selfcheck-b: OK
platform limits recorded: 1
```

38 `OK`, no `DIFF`. Every change run above also shows `0 new-line run(s)`; every new-line run `0` change runs. **The
two cases the change is about** are 3p, on one line and one Product change — to a product with no category and no
account of its own: with an Account (420000) the run stops at the gateway and the line keeps it; with the Account
emptied (written alone, which starts neither workflow) the same change takes the journal's Default Account, 410000.
3v, 3n and 3e show the same on a vendor bill, on a line whose Product is cleared, and on a journal entry — each with
an Account of its own or 421000 written in first — and the product's and category's accounts still replace whatever
the line carries (3, 3v, 3n). Every walk ends where its line's create left it, so a re-run finds each *TEST B2*
line as the new-line check expects and re-reads the run its create started.

The *TEST B* lines of the two builds before — created 09:58–10:03 on the first build and 10:20–10:21 on the guarded
one, and walked 10:22–10:27 — proved the same cases on those builds; that output is superseded by the run above, and
`selfcheck-b` no longer writes to those lines. The first build's failed run is still re-read as the LIMIT.

`runs-b`, after the change's `selfcheck-b` (12:08) — both builds' runs together, *TEST B* before the change and *TEST
B2* after it:

```
Invoice Lines: fill the account of a new line: 15 run(s), status counts {2: 12, 3: 2, 4: 1}
   2  [2] Take the category's Expense Account  ['TEST B vendor bill line', 'TEST B2 vendor bill line']
   2  [2] Take the category's Income Account  ['TEST B category account', 'TEST B2 category account']
   4  [2] Take the journal's Default Account (customer document)  ['TEST B no product, guarded',
          'TEST B product without a category', 'TEST B2 no product', 'TEST B2 product without a category']
   2  [2] Take the journal's Default Account (journal entry)  ['TEST B entry on Sales line', 'TEST B2 entry on Sales line']
   2  [2] Take the product's Income Account  ['TEST B product account', 'TEST B2 product account']
   2  [3] 未通过分支  ['TEST B entry without default', 'TEST B2 entry without default']
   1  [4] 筛选条件值为空 记录ID  ['TEST B no product']
Invoice Lines: fill the account when the Product changes: 32 run(s), status counts {3: 8, 2: 24}
   3  [2] Take the category's Expense Account  ['TEST B vendor bill line', 'TEST B2 vendor bill line']
   6  [2] Take the category's Income Account  ['TEST B category account', 'TEST B no product, guarded',
          'TEST B2 category account', 'TEST B2 no product']
   3  [2] Take the journal's Default Account (customer document)  ['TEST B no product, guarded', 'TEST B2 no product',
          'TEST B2 product account']
   3  [2] Take the journal's Default Account (journal entry)  ['TEST B entry on Sales line', 'TEST B2 entry on Sales line']
   2  [2] Take the journal's Default Account (vendor document)  ['TEST B vendor bill line', 'TEST B2 vendor bill line']
   2  [2] Take the product's Expense Account  ['TEST B vendor bill line', 'TEST B2 vendor bill line']
   5  [2] Take the product's Income Account  ['TEST B category account', 'TEST B2 category account',
          'TEST B2 product account']
   8  [3] 未通过分支  ['TEST B entry without default', 'TEST B2 entry on Sales line', 'TEST B2 entry without default',
          'TEST B2 no product', 'TEST B2 product account', 'TEST B2 vendor bill line']
```

No run of either workflow on a tenant line: the references write Account alone, which starts neither. Of the change
workflow's eight stops, two are *TEST B entry without default* before the change; the six after it are the two on the
journal with no Default Account and the four stops the change introduced — a line with an Account kept it (3p, 3v, 3n,
3e).

`rerun-b` — the eleven owning steps run again after the build, every control, rule and view compared before and
after each (one line per step shown):

```
contacts.py layout, run again: identical: all nine worksheets; 4 rules identical; 3 views changed {}
contacts.py rules, run again: identical: all nine worksheets; 4 rules identical; 3 views changed {}
products.py layout, run again: identical: all nine worksheets; 3 rules identical; 3 views changed {}
prodcat.py layout, run again: updated: nothing (already as specified); identical: all nine worksheets; 1 view changed {}
journals.py layout, run again: layout already as specified; nothing saved; identical: all nine worksheets
journals.py rules, run again: identical: all nine worksheets; 10 rules identical; 2 views changed {}
journals.py views, run again: identical: all nine worksheets; 10 rules identical; 2 views changed {}
invlines.py layout, run again: layout already as specified; nothing saved; the subtable is already in its place; nothing saved
invlines.py rules, run again: identical: all nine worksheets; 1 rule identical; 1 view changed {}
invlines.py views, run again: identical: all nine worksheets; 1 rule identical; 1 view changed {}
roles.py create, run again: every role "exists; not re-created", nothing reconciled; identical: all nine worksheets
check-b: OK
```

Seven of these re-save what they own whatever they find — `contacts.py layout` and `rules`, `products.py layout`,
and the `rules` and `views` steps of `journals.py` and `invlines.py`, which is how those scripts were written — and
everything they re-saved read back identical; the other four compare first and saved nothing.

`verify-b` — Records step 2 read back, record by record (58 lines, `OK` or `DIFF`; a few shown):

```
OK    Contacts           Sarawak Timber Logistics                   Account Receivable 124000, Account Payable 221100
OK    Contacts           TEST QA Trading Sdn Bhd, TEST Person One   Account Receivable 124000, Account Payable 221100
OK    Product Categories Goods / Consumables                        Income Account 410000, Expense Account 510000
OK    Product Categories TEST created with no Name                  Income Account 410000, Expense Account 510000
OK    Products           Whiteboard Marker Set                      Income Account —, Expense Account —
OK    Journals           INV Sales                                  Default Account 410000, Suspense Account —, Profit Account —, Loss Account —, Private Share Account —
OK    Journals           BILL Purchases                             Default Account 510000, Suspense Account —, Profit Account —, Loss Account —, Private Share Account —
OK    Journals           BNK1 Bank                                  Default Account 120001, Suspense Account 120002, Profit Account 999001, Loss Account 999002, Private Share Account —
OK    Journals           MISC Miscellaneous Operations              Default Account —, Suspense Account —, Profit Account —, Loss Account —, Private Share Account —
OK    Invoice Lines      SCG-PO-88213 line 0                        Account 410000
OK    Invoice Lines      STL-2026-0042 line 1                       Account 410000
·     Invoice Lines      MISC/2026/00001 TEST roll-up line          Account —   (not in the seed)
references: 0 differing
```

— 10 contacts, 11 categories, 18 products, 11 journals and the 8 tenant lines, all `OK`; the twelve TEST lines are
listed as they are (the two of 07 untouched, empty; the ten below). Run again after the change (12:06–12:08): the
same 58 `OK` and `references: 0 differing`, with twenty-one TEST lines listed — the two of 07, the ten *TEST B* and
the nine *TEST B2* lines below.

The worksheets' own checks, run after the build (`nocoly/build/<script>.py <step>`, last line of each):

```
invoices.py verify   3 in the seed file; 0 missing or differing; 16 not in it [the TEST documents, 4 of them part B's]
invoices.py check    check: OK — controls, tabs, options, defaults, rules, views, buttons and the numbering workflow as specified
invlines.py verify   8 in the seed; 0 missing or differing — and every invoice's amounts equal to its lines, the 3 tenant
                     documents (115,063.52 · 12,575.20 · 194,400.00), MISC/2026/00001 and the 4 TEST B documents
                     (run again after the change, 12:09–12:10: the same, 21 TEST lines not in the seed, the TEST B
                     documents at 110.00 · 20.00 · 20.00 · 20.00 with the TEST B2 lines)
invlines.py check    check: OK — controls, options, defaults, the rule, the view, the mount and the two roll-up workflows as specified
products.py verify   14 in the extract; 0 missing or differing; 4 not in the extract [the TEST products]
variants.py verify   18 products; 0 whose own variant differs or is missing; … 11 of 11 single-variant products match
prodcat.py verify    7 categories in the extract; 0 missing or differing; … 14 products; 0 with the wrong category
prodcat.py check     check: OK — the controls with their places and permissions …, Products' Category with a quick filter on both its views
accounts.py verify   87 accounts in the extract; 0 missing or differing; 3 not in the extract [TEST01, TEST02, TEST03]
accounts.py check    check: OK — first in Invoicing; eleven controls …; automation A published with its four paths; Archive / Unarchive; the two views
journals.py verify   7 in the extract; 0 missing or differing; 4 not in the extract [the TEST journals]
journals.py check    check: OK — controls, tabs, options, defaults, rules, views, buttons and the archive guard as specified
roles.py check       check: OK — … the account fields hidden from Invoicing and Accounting Read-only as 09 §1 says, and no members
```

`products.py` and `variants.py` have no `check` step. `accounts.py untouched` after the build — Units & Packagings
and Product Variants read the digests part A recorded, and the six worksheets part B wrote to read new ones:

```
Contacts             33 controls  sha256:e690201db95a4eb5
Units & Packagings   10 controls  sha256:e57dc8775cd5038b      (unchanged)
Products             23 controls  sha256:7d0b6fd0163fefe6
Product Variants     20 controls  sha256:6eba14458f20e2a6      (unchanged)
Product Categories   10 controls  sha256:ae36bfce97c03588
Journals             20 controls  sha256:090afe02cb145208
Invoices             33 controls  sha256:74fdc37a579b150c
Invoice Lines        14 controls  sha256:a30b97b69de2854c
```

The roles, compared with the snapshot taken before the build: every role's model identical but for the controls part
B added — visible in every role except Invoicing (all twelve account fields hidden, and the three tabs with them)
and Accounting Read-only (Contacts' two accounts and the tab Invoicing hidden).

**The last run before the change, 17 Sep 2026 10:51–11:10**, after the last edits to `journals.py`, `invlines.py` and `roles.py` (the
ones that let their steps run on a build that has not reached bundle 2): `rerun-b`, then `all-b`, then `records-b`, each
exiting 0.

`rerun-b` again — the same eleven lines as above, every step's controls, rules and views identical before and after,
the four business roles "exists; not re-created" with nothing reconciled, and `check-b: OK`.

`all-b` — every part-B step on the finished build (one line per step shown):

```
contacts      Account Receivable, Account Payable already there; nothing added · every control already where contacts.py
              puts it; its layout step not run · alias, help, placeholder, picker and default already as specified;
              nothing saved · rule already as specified; contacts.py rules not run
products      already there; nothing added · layout step not run · nothing saved
categories    already there; nothing added · layout step not run · tab bar Accounting · Child Categories · Products ·
              nothing saved
journals      already there; nothing added · layout step not run · nothing saved · the five account rules already as
              specified; journals.py rules not run · both views already show Default Account after Sequence Prefix;
              journals.py views not run
lines         already there; nothing added · every control in place and the subtable already shows Account; layout not
              run · nothing saved · the rule already hides Account; invlines.py rules not run · the Lines view already
              shows Account after Label; invlines.py views not run
automation-b  both workflows: already built and published; nothing written · controls identical: all nine worksheets
visibility    the four business roles exist; nothing reconciled · controls identical · roles.py check: OK
references    0 record(s) written and read back; 58 already as the extract has them · controls identical ·
              invlines.py verify 8 in the seed, 0 missing or differing, every document's amounts equal to its lines ·
              references: 0 differing
check-b       check-b: OK
```

`records-b` — every record of the nine worksheets against the snapshot taken before the first write, field by field
through `record get`, the account references left to `verify-b`:

```
OK    Contacts             10 before, 10 now; 0 changed beyond the account references; gone []; new []
OK    Units & Packagings   33 before, 33 now; 0 changed beyond the account references; gone []; new []
OK    Products             18 before, 18 now; 0 changed beyond the account references; gone []; new []
OK    Journals             11 before, 11 now; 0 changed beyond the account references; gone []; new []
OK    Product Variants     19 before, 19 now; 0 changed beyond the account references; gone []; new []
OK    Invoices             15 before, 19 now; 0 changed beyond the account references; gone []; new ['TEST B vendor bill',
      'TEST B journal entry', 'TEST B customer invoice', 'TEST B entry on Sales']
OK    Invoice Lines        10 before, 20 now; 0 changed beyond the account references; gone []; new [the ten TEST B lines]
OK    Product Categories   11 before, 11 now; 0 changed beyond the account references; gone []; new []
OK    Chart of Accounts    90 before, 90 now; 0 changed beyond the account references; gone []; new []
records-b against partb_snapshot_baseline_20260917-090220.json: 0 difference(s)
```

A control part B added reads back on every existing record as a key of its own — a tab as `""` — so a key absent
from the snapshot that holds nothing now is not counted as a change; the first `records-b` counted those tab keys
and a new Invoices document by its title ("Draft") rather than its Customer Reference, and was corrected to this.

**After the change** (12:10–12:14): `records-b` again 0 differences — Invoice Lines 10 before, 29 now, the new ones the
ten *TEST B* and nine *TEST B2* lines, every other worksheet as above — and the two steps the change ran, run once
more, wrote nothing:

```
lines         Account already there; nothing added · every control in place and the subtable already shows Account;
              layout not run · alias, help, placeholder, picker and default already as specified; nothing saved ·
              rule not run · view not run
automation-b  Invoice Lines: fill the account of a new line: already built and published; nothing written
              Invoice Lines: fill the account when the Product changes: already built and published; nothing written
              automation B (no control may change): identical: all nine worksheets
```

#### TEST records left by part B

Four documents in Invoices, each created as a draft by `selfcheck-b` and named by its Customer Reference, and nineteen
lines on them in Invoice Lines, each named by its Label: ten *TEST B* lines from the builds before the change, no longer
written to, and nine *TEST B2* lines from the proof after it. Their ids are in `ids.json` ("Invoices: TEST B …",
"Invoice Lines: TEST B …", "Invoice Lines: TEST B2 …").

| Record | What it is | Left as |
|---|---|---|
| *TEST B customer invoice* `b042dd75-cd81-40ea-9c4d-8b7aa0bce9bf` | Customer Invoice on Sales (INV) | Draft, thirteen lines (seven TEST B, six TEST B2) |
| *TEST B vendor bill* `67ef77cf-ce74-4a76-a89d-8c52862df5b5` | Vendor Bill on Purchases (BILL) | **Cancelled** through the Cancel workflow, so Purchases holds no new draft; two lines |
| *TEST B journal entry* `959cfd34-3e3a-47a8-ae53-3c70be84eba8` | Journal Entry on *TEST draft guard* (TSTDG, no Default Account) | Draft, two lines — TSTDG now holds two draft entries, which its archive guard refuses as before |
| *TEST B entry on Sales* `d69605df-a56e-40a4-8215-a17eb59b9208` | Journal Entry on Sales (INV) | Draft, two lines |
| *TEST B category account* `a226cfbf-da97-4108-b9ac-de01162a35f9` | customer invoice line, [CONS-0002] Whiteboard Marker Set | Account 410000 |
| *TEST B product account* `9f8c584a-65df-48e4-988f-3b1ffef4651e` | customer invoice line, [TEST-0001] TEST Product | Account 420000 |
| *TEST B explicit account* `170e3290-3b6e-41a6-8cce-bd2936774844` | customer invoice line created with an Account | Account 421000 |
| *TEST B no product* `ecd5d5a2-a541-41b0-a1a8-357feae52107` | customer invoice line with no Product — the first build's failed run | Account empty |
| *TEST B no product, guarded* `fd6f3a1e-c1eb-433b-b538-1be322a1cd13` | customer invoice line with no Product | Account 410000 |
| *TEST B section* `5d0f5bbc-2491-430e-ab4d-77b8b4ec89e3` | customer invoice Section line | no Account |
| *TEST B product without a category* `abff405d-1926-4224-927d-2108f84ae6e5` | customer invoice line, [TEST-0004] TEST Variant From UI | Account 410000 |
| *TEST B vendor bill line* `a1e2df25-5ee1-4c1a-9421-a70f47b57aeb` | vendor bill line, Whiteboard Marker Set | Account 510000 |
| *TEST B entry without default* `916b3ab2-ce65-4b2c-a984-2bb2dc1ded59` | journal entry line, Whiteboard Marker Set | Account empty |
| *TEST B entry on Sales line* `29a5f12c-4369-43b9-b5db-c9a859640d15` | journal entry line, Whiteboard Marker Set | Account 410000 |
| *TEST B2 category account* `23e05ad1-1db1-4e6f-ad22-2cc7de71e14f` | customer invoice line, [CONS-0002] Whiteboard Marker Set (walk 3) | Account 410000 |
| *TEST B2 product account* `519567be-2d84-4668-a449-484c56f41c4d` | customer invoice line, [TEST-0001] TEST Product (walk 3p) | Account 420000 |
| *TEST B2 explicit account* `88a94904-95cc-4c92-9a91-3955337062e4` | customer invoice line created with an Account | Account 421000 |
| *TEST B2 no product* `0ca9c3ec-f95b-4010-a633-0eb15135d140` | customer invoice line with no Product (walk 3n) | Account 410000 |
| *TEST B2 section* `9e25cd43-97fb-4be4-940c-73adc7a64c4d` | customer invoice Section line | no Account |
| *TEST B2 product without a category* `f87b7b96-29d5-4b5b-a7dc-417997a00003` | customer invoice line, [TEST-0004] TEST Variant From UI | Account 410000 |
| *TEST B2 vendor bill line* `c0e2d83f-caf4-4b1e-a6d7-495ce27b5a5d` | vendor bill line, Whiteboard Marker Set (walk 3v) | Account 510000 |
| *TEST B2 entry without default* `b3e05f94-4add-4810-9936-2bedff4b3169` | journal entry line on TSTDG, Whiteboard Marker Set (walk 3e) | Account empty |
| *TEST B2 entry on Sales line* `21c8b311-36df-4bea-9d70-623631437d87` | journal entry line on Sales, Whiteboard Marker Set (walk 3e) | Account 410000 |

**TEST Product** (TEST-0001) was given its own Income Account 420000 and Expense Account 510100 for the check and put
back, both times: both read back empty, and `records-b` finds the record otherwise unchanged. The roll-up gave the four
documents their amounts from these lines (110.00, 20.00, 20.00 and 20.00 untaxed since the TEST B2 lines), and
`invlines.py verify` reads them equal to their lines. Nothing was written onto the tenant's documents, TEST01, TEST02 or
TEST03.

## 3 · Test list

**27 of 28 pass, 1 not run** — part A 15 of 15 (one with a difference), part B 12 of 13 — plus one check the
browser pass could not drive, also not run.

### Part A — the worksheet, run in the browser on 16 Sep 2026

**Part B was not built yet**, so these are part A's checks only. Run in the Nocoly UI in Chrome, stored values read
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

### Part B — the account fields on the other worksheets, run in the browser on 17 Sep 2026

Run in the Nocoly UI in Chrome, with stored values read back through the CLI. Automation B's cases were driven through
the CLI on TEST records (`accounts.py selfcheck-b`, §2) and their results then read in the UI. The Chrome window went to
the background partway through, so a line created from an invoice's own table was not driven. **12 of 13 pass, 1 not
run.**

| # | Test | Result |
|---|---|---|
| 16 | Contacts: the Invoicing tab | **Pass.** Sunway Construction Group's tabs read Contacts · Sales & Purchase · **Invoicing** · Notes, with Account Receivable 124000 Account Receivable \| Account Payable 221100 Account Payable. On *TEST QA Trading Sdn Bhd, TEST Person One*, a contact under a company, the tab is not there |
| 17 | Contacts: a new contact's defaults | **Pass.** The create form's Invoicing tab opens on 124000 and 221100, each described "Odoo reads the company's default, … until a contact is given its own." Closed without saving |
| 18 | Contacts: the two pickers | **Pass.** Account Receivable offers exactly the four Receivable accounts (124000, 124300, 124600, 124700); Account Payable exactly the three Payable ones (221100, 221600, 221700). The archived TEST02, a Payable account, is not offered |
| 19 | Products: the Accounting tab | **Pass.** Business Laptop 14" i7's tabs read General Information · Sales · Inventory · **Accounting**; Income Account \| Expense Account, both empty, placeholder "From Category" |
| 20 | Products: the income-and-expense filter | **Pass.** Searching the Income Account picker for "12" offers 111220, 120000, 120002–120004, 124100, 124200, 124500, 125000–127000, 221200 and 511200 — and **not** 120001 Bank, the four Receivable accounts or 221100 Account Payable |
| 21 | Product Categories: the Accounting tab | **Pass.** Goods' tab bar reads **Accounting** · Child Categories (4) · Products, Accounting open, with Income Account 410000 Trade Income \| Expense Account 510000 Costs |
| 22 | Journals: the accounts by type | **Pass.** *Bank*: Default Account \* 120001 Bank · Suspense Account \* 120002 Bank Suspense Account · Profit Account 999001 · Loss Account 999002. *Sales*: Default Account \* 410000 Trade Income, and nothing else. *Purchases*: Default Account \* 510000 Costs · Private Share Account, empty |
| 23 | Journals: Default Account is required | **Pass.** A new Sales journal with no Default Account is refused — "Please fill in Default Account" and "Please fill in the record correctly". Discarded; `record list` confirms no journal was saved |
| 24 | Journals: the Default Account column | **Pass.** The Journals view reads Journal Name · Type · Sequence Prefix · **Default Account**: Sales 410000 Trade Income, Purchases 510000 Costs, Bank 120001 Bank, the rest empty |
| 25 | Invoice Lines: the Account column | **Pass.** The Lines view reads Number · Label · **Account** · Product · …; INV/2026/00001's own table reads Sequence · Display Type · Product · Label · **Account** · Quantity · Unit, each of its three lines on 410000 Trade Income, and its amounts still 11,432.00 · 1,143.20 · 12,575.20 |
| 26 | Invoice Lines: no account on a section | **Pass.** *TEST B section*'s form shows Sequence, Label, Number, Accounting Date and Status — no Account, as no Product and no figures |
| 27 | Automation B | **Pass, through the CLI.** Every case of §1's table and of the fix below, re-proved on the *TEST B2* lines after the change (§2 › Self-checks); in the UI, *TEST B customer invoice*'s table reads category account 410000, product account 420000, explicit account 421000 kept, no product 410000, product without a category 410000, and no account on the section. **Changed after the first build**: a Product change whose product and category yield nothing used to give the line the journal's Default Account over an Account it already had. Odoo keeps the existing account (`accounts['income'] or line.account_id`) and uses the journal's default only when the account is empty, and so does automation B now |
| 28 | Field visibility by role | **Not run.** The four business roles have no members, so no browser session can see the app as Invoicing or Accounting Read-only. `roles.py check` reads the per-field hiding back as built |
| — | A line created from an invoice's own table | **Not run** in the browser: *Add a row* opened a row, and the window went to the background before a product could be chosen; the page was reloaded without saving and `record list` confirms the invoice kept its lines. The same create path is proved through the CLI |

### Differences from Odoo

1. **A receivable or payable account's box is ticked by hand** (test 11). HAP checks a rule before the save and runs a
   workflow after it, so automation A cannot tick Payment Reconciliation before the rule that requires it refuses the
   save. Odoo's compute ticks it as the Type changes.
2. **None of the account fields on the other worksheets is required on the field.** Odoo requires a contact's
   receivable and payable accounts and a product line's account, but hides those fields from part of the accounting
   staff; a HAP field that is required yet hidden from a role blocks that role's saves. Defaults, the seed and
   automation B keep them filled instead. Journals, edited only by the two roles that see its accounts, requires them
   by rule.
3. **Checks that hold in the form only.** The code's format, the receivable rule, and every default apply in the form;
   `record create` and `record update` write around them. No duplicates holds everywhere.
4. **A save that sets Product and Account together.** Automation B runs after the save and gives the line the
   product's or the category's account over the one chosen; Odoo keeps an account written with the product. Set a
   different account in a second save.
5. **One level of category.** Odoo walks up a category's parents for an account; every category here carries one, so
   automation B reads the product's own category.
6. **No double entry.** No debit or credit, no Balance button, no *Account with Entries* filter, no tax or payment-term
   lines — beyond this bundle.
7. **Pickers that cannot follow the record.** A journal's Default Account picker offers every active account, where
   Odoo narrows it by the journal's type; a Parent Account picker leaves out the account itself but not its
   descendants.
8. **Odoo creates a bank, cash or card journal's account when Default Account is left empty.** Here a rule requires one.

### Test records left in the worksheet

- **Chart of Accounts:** TEST01 "TEST Account" (Bank and Cash), TEST02 "TEST refused payable" (archived), TEST03
  "TEST UI account" (Income, with a Description).
- **Invoices and Invoice Lines:** four *TEST B* documents and their 19 lines — ten *TEST B*, nine *TEST B2* after the
  fix — listed with their ids in §2 › *TEST records left by part B*. *TEST draft guard* (TSTDG) now holds two draft
  entries.
- **Products:** TEST Product's own accounts were set for the checks and cleared again.

All go after sign-off, with the owner's approval. The 87 accounts and every seeded reference are the tenant's and stay.
