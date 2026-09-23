# 23 · Sales Dashboard — requirements and results

| | |
|---|---|
| What | One HAP **custom page** (自定义页面) of charts, **Sales Dashboard**, in the Sales menu group right after Order Lines |
| Odoo counterpart | Sales ▸ Reporting (`sale.report`), loosely. The owner asked for a dashboard for the demo, **not** a copy of Odoo's report; 18-sales-reporting.md is the Odoo-shaped plan and stays unbuilt |
| Source of facts | none from Odoo: every figure is ERP Master's own data. The HAP chart and page shapes come from hap-cli 0.8 (`hap guide chart`, `core/chart.py`, `core/page.py`, `core/app_creator/charts.py`) and pd-openweb `main` (`src/pages/Statistics/…`, `src/pages/customPage/components/editWidget/filter/…`) |
| Builder | `nocoly/build/dashboard.py` — `page` · `charts` · `layout` · `all` · `check` · `data "<chart>"` |
| Depends on | 16 Orders, Order Lines, 06 Invoices; Invoices' payment controls (another agent, 23 Sep) for two headlines |
| Status | **Built 23 Sep 2026**, all eleven charts; every figure checked against the records (§4). **UI not verified** — the building agent has no browser |
| Date | 23 Sep 2026 |

---

## 1 · Requirements

A dashboard of the sales app for the demo, built as **one custom page** of chart components.

| Block | Chart | Source | Definition |
|---|---|---|---|
| Headline | number | Orders | **Confirmed sales**: Σ Untaxed Amount, Status = Sales Order |
| Headline | number | Orders | **Open quotations**: count and Σ Untaxed Amount; Status Quotation or Quotation Sent; not Is Template |
| Headline | number | Orders | **To invoice**: count of orders, Invoice Status = To Invoice |
| Headline | number | Invoices | **Overdue**: count and Σ **Amount Due**; Status Posted, Type Customer Invoice, Due Date before today, **Payment Status not Paid** (revised 23 Sep: invoices now take payments) |
| Headline | number | Invoices | **Received this month**: Σ Amount Paid on customer invoices whose Last Payment Date is in the current month (added 23 Sep) |
| Trend | column | Orders | Confirmed sales by month of Quotation/Order Date, last 12 months |
| Pipeline | pie | Orders | Count by Status, templates excluded |
| Customers | ranking | Orders | Top customers by confirmed Untaxed Amount |
| Salespeople | bar | Orders | Confirmed Untaxed Amount by Salesperson |
| Invoicing | pie | Orders | Sales Orders by Invoice Status |
| Products | ranking | Order Lines | Top products by Subtotal, product lines only |

- A page-level date filter on Quotation/Order Date, applied to the Orders charts.
- Every chart opens its records on a click.
- Titles and descriptions are for the app's users: plain words, no Odoo, no field names.

## 2 · What HAP offers, and how the build uses it

A chart is a stored object against **one** worksheet; the page holds only its id (18 §3). A chart's condition is a
**third** object — a stored filter the chart names by `filterId` — and a page filter is a **filter group** the page
names by id. So a build is four layers: conditions, charts, filter group, layout. `BUILDING.md` *Charts and custom
pages* has the platform detail.

| Decision | Why |
|---|---|
| Charts are **page charts** (`sourceType` 1) | what the page editor makes; they stay out of Orders', Invoices' and Order Lines' own Statistics lists. CRM Reporting's charts were made as worksheet charts and are listed on Leads |
| Amounts carry an **RM** prefix on the chart | every amount in the app is ringgit and the controls carry no unit; the CRM charts carry RM too |
| **Click-through** is `displaySetup.showRowList` on every chart | a click on a number, bar, slice or ranking row opens the records behind it, in a pop-up list (`style.viewDataType` 1, the default). Chart-to-chart linkage is off: the page's `autoLinkage` is not set, as on CRM Reporting |
| **Trend** uses a dynamic range, *past 11 months → today* | the server snaps it to whole months: `2025/10/01-2026/09/23` on 23 Sep 2026, i.e. this month and the eleven before it |
| **Top customers / Top products** show the top **10** (`showXAxisCount` 10), sorted by value descending | a ranking with no sort draws in record order |
| **Sales by salesperson** is a horizontal bar (`showChartType` 2) | names read better across than under a column |
| **Top products is already confirmed-only** | Order Lines **already carries** an *Order Status* lookup (`6ab2cb9d805aef7032e32a68`, type 30, hidden `011`, off the Orders relation), stored and correct on all 126 lines. A condition on it excludes templates (they are Quotations) and drafts in one go, which no condition on the Orders relation itself can do — a relation condition names fixed records. See §5 |
| The **page filter** is *Order date* with the preset-range picker (`filterType` 17, every preset), no default | the headlines read "all time" until someone picks a range. It binds the eight Orders charts; Invoices and Order Lines carry no order date |
| Overdue sums **Amount Due**, not Total | the owner's revision, once invoices take payments |

## 3 · The page — ids

Page **`6ab353b77e7f0f2333bec7d2`**, Sales group `6ab098785d273c4a416772f5`, sidebar order *Orders · Order Lines ·
Sales Dashboard*. Page filter group **`a907f87e-c949-4dee-88ea-9c291a6eee4e`**. All in ids.json under
`dashboard` → `"Sales Dashboard: …"`.

| Chart | Type | Worksheet | Chart id | Place (x, y, w, h on 48 columns) | On the date filter |
|---|---|---|---|---|---|
| *Order date* filter | — | — | group `a907f87e…` | 0, 0, 48, 3 | — |
| Confirmed sales | number | Orders | `6ab354263bd0d5cfc333898d` | 0, 3, 12, 6 | yes |
| Open quotations | number | Orders | `6ab354363bd0d5cfc333898e` | 12, 3, 12, 6 | yes |
| Value of open quotations | number | Orders | `6ab35fef59bcf31f9afcf7c9` | 24, 3, 12, 6 | yes |
| Orders to invoice | number | Orders | `6ab354373bd0d5cfc333898f` | 36, 3, 12, 6 | yes |
| Overdue invoices | number | Invoices | `6ab3589a3bd0d5cfc3338dcc` | 0, 9, 16, 6 | no |
| Amount overdue | number | Invoices | `6ab35ff8df55951844a382d3` | 16, 9, 16, 6 | no |
| Received this month | number | Invoices | `6ab3589c3bd0d5cfc3338dcd` | 32, 9, 16, 6 | no |
| Monthly sales | column | Orders | `6ab354383bd0d5cfc3338990` | 0, 15, 32, 11 | yes |
| Quotations and orders by status | pie | Orders | `6ab354393bd0d5cfc3338991` | 32, 15, 16, 11 | yes |
| Top customers | ranking | Orders | `6ab354393bd0d5cfc3338992` | 0, 26, 24, 11 | yes |
| Sales by salesperson | bar | Orders | `6ab3543a3bd0d5cfc3338993` | 24, 26, 24, 11 | yes |
| Sales orders by invoicing status | pie | Orders | `6ab3543b3bd0d5cfc3338994` | 0, 37, 16, 11 | yes |
| Top products | ranking | Order Lines | `6ab361723bd0d5cfc33390bd` (replaced `6ab3543c…`, §4) | 16, 37, 32, 11 | yes, through its lines' *Order Date* lookup (§5) |

### 3.1 · The headline row, and why every headline holds one value

The first build put two values in *Open quotations* and *Overdue invoices*. In the browser (coordinator, 23 Sep, a
page about 1250 px wide) both amounts were clipped. The platform's own numbers show why: 48 columns, 10 px grid
margins and 10 px container padding (pd-openweb `customPage/components/WidgetContent` `LAYOUT_CONFIG`), 15 px card
padding (`Statistics/Card/Card.less`), 8 px between the values of a number chart and 8 px padding inside each
(`Statistics/Charts/NumberChart.js`), with values in 28 px type. A card `w` columns wide is `15.83·w + 10·(w − 1)` px:
12 columns come to 300 px, so each half of a two-value card has about **111 px**. "RM 1,382,807.20" needs about
**190 px**: that is what a single value gets on a 10-column card, where it fit. A two-value card would need about
**19 columns**, so two of them and three single cards cannot share a 48-column row. The coordinator's first option,
2 · 3 · 2 · 3 · 2 on a 12-wide row (8 · 12 · 8 · 12 · 8 of 48), fails the same way.

**So each two-value card became two single-value cards, over two rows**: Orders on the first row at 12 columns
(about 240 px for the value) and Invoices on the second at 16 (about 345 px). Click-through is on every card. The
count cards keep the old chart ids; *Value of open quotations* and *Amount overdue* are new.

## 4 · Results

`dashboard.py check` asks each chart for what it draws (`report/getData`, the page's own call) and computes the same
figure from the records (GetRowDetail `rowData`), at the same moment. **Records move under this** — the owner and two
other agents were writing Orders and Invoices on 23 Sep — so the figures below are one run's, not a fixture.

**Latest run: 23 Sep 2026, ~13:45, after the headline split** (`dashboard.py check`, exit 0). **Every figure
agrees.** Headlines: Confirmed sales RM 1,213,917.46 · Open quotations 16 · Value of open quotations RM
1,383,107.20 · Orders to invoice 7 · Overdue invoices 4 · Amount overdue RM 340,748.55 · Received this month RM
6,985.80. The payment agent had marked invoices paid by then. The charts below the headlines are as in the first
run.

**Amounts show two decimals** on every chart (`dotFormat` "0"). The first build carried "1", which drops trailing
zeros, so the card read "RM 1,383,107.2" (coordinator, 23 Sep).

First run: ~13:00, before the split.

| Chart | Figure | Chart draws | Records give |
|---|---|---|---|
| Confirmed sales | untaxed | RM 1,213,917.46 | 1,213,917.46 |
| Open quotations | count · untaxed | 16 · RM 1,382,807.20 | 16 · 1,382,807.20 |
| Orders to invoice | count | 7 | 7 |
| Overdue invoices | count · amount due | 14 · RM 1,122,351.19 | 14 · 1,122,351.19 |
| Received this month | amount | RM 1,000.00 | 1,000.00 — the one paid invoice, the payment agent's *TEST Register Payment*, paid 23 Sep |
| Monthly sales | Oct 2025 … Sep 2026 | 71,804 · 13,772 · 47,691 · 113,520 · 187,462 · 164,208 · 76,524 · 198,672.96 · 127,077.50 · 106,195 · 94,496 · 12,495 | the same, month for month |
| Quotations and orders by status | count | Quotation 10 · Quotation Sent 6 · Sales Order 17 · Cancelled 3 | the same (the 2 templates left out) |
| Top customers | top 10 untaxed | Gadget Galeri 219,715 · Hospital Pakar Seri Cahaya 205,200 · JPN Johor 187,462 · SM Bukit Damai 151,674 · Kolej Teknologi Nusantara 127,077.50 · Studio Reka Warna 101,195 · Awan Digital 88,182.96 · MP Seberang Perai 76,524 · Pusat Komputer Kinabalu 30,620 · Klinik Mediviva Ampang 13,772 | the same |
| Sales by salesperson | untaxed | Casimir Chiong Ming Yuan 1,213,917.46 | the same — every order has one salesperson |
| Sales orders by invoicing status | count | To Invoice 7 · Fully Invoiced 8 · Upselling Opportunity 2 | the same |
| Top products | top 10 subtotal | myBook Air 13" 256GB 197,754 · myPad Pro 13" 132,475 · myBook Air 13" 512GB 96,727.50 · myPad Air 11" 95,166 · myMac 24" 87,984 · myDisplay Studio 87,627.48 · myPhone 16 Pro 82,485 · myPhone 16 128GB 79,980 · myCare+ 56,637 · myBook Pro 14" 512GB 44,154.48 | the same |

**The page filter, proved without a browser.** `check` sends two bound charts the condition the page sends when
someone picks *Last month* (August 2026) and compares: Confirmed sales RM 94,496.00 against 94,496.00; the status
pie Quotation 3 · Sent 2 · Sales Order 2 · Cancelled 1 against the same. *This month* and *This year* were tried by
hand too: 12,495.00 and 1,080,650.46 — the sum of January to September in Monthly sales.

**Overdue and Received this month will move.** When they were built the payment agent had added the controls but
marked no demo invoice paid: all 15 posted customer invoices read *Not Paid* and 14 are past due. Once it marks the
older ones Paid, Overdue should drop to about 6. Re-run `check` then. One run in between read **1,000 on the chart
against 400 in the records** — the TEST invoice was being written between the two reads; the next run agreed. With
nothing paid this month, the chart returns no series at all and HAP draws it as empty; `check` reads that as 0.

**A page chart dies when a layout save leaves it off the page.** One `layout` run hit a transient read failure
on Top products `6ab3543c3bd0d5cfc3338995`. The cause was the CLI's own access-check cache file, renamed underneath
it by another agent's `hap` run. The builder then counted the chart as missing and saved the page without it. The
next save put it back, but its config still read and it drew nothing: getData status 0, with no name. Re-saving it
did not revive it. `charts` now spots this (`alive`) and builds a replacement on the same stored condition
(`6ab361723bd0d5cfc33390bd`); the dead id is kept in ids.json as `retired Top products`. `layout` now stops rather
than save a page with a chart missing, and a chart read is retried.

**Idempotence.** `all` a second time: every chart "as specified; nothing saved", the layout "already placed;
nothing saved".

## 5 · Not built, and why

| What | Why |
|---|---|
| Top products on the date filter: **bound, but empty until the reseed** | `dashboard.py lookups` appended *Order Date* (`6ab36202e54d2a34faaaa888`, `date_order`), *Customer* (`…a889`, `order_partner_id`) and *Salesperson* (`…a88a`, `salesman_id`) to Order Lines. All three are hidden (`011`), stored (`strDefault` "00") and off the Orders relation. `append_checked` proved the 35 existing controls unchanged, and *Order Status* was reused. Lines that already existed were **not backfilled**. The coordinator measured that a new line fills them at creation and that re-saving a line's Orders link does not, and decided to leave the existing lines alone: the reset reseed re-creates every line before the demo. The page filter binds Top products to that lookup (23 Sep, coordinator's call). **Until the reseed, any date pick empties Top products**; with no pick it reads as before. `check` shows how many lines hold the date: 1 of 128 on 23 Sep, a Note on a quotation, so *This month* and *This year* rightly draw nothing. It also shows what *Last month* will read once they do: 7 products, RM 94,496.00, the same as Confirmed sales for August |
| Top products by customer or salesperson | the lookups exist, but no chart uses them yet; they fill with the reseed |
| Sales Team, Product Category dimensions | 18 §2 and §6: no Sales Team lookup yet; Category is a two-hop lookup, unproven |
| UI verification | no browser here. §6 lists what to look at |

**Two orphaned filter groups** (`61cf82f3-d258-46b0-89d9-31887cd9ee94` and one reused since) were minted by a first
`layout` run that stopped before the page saved; `61cf82f3…` is referenced by nothing. Nothing was deleted; the
builder now remembers a group's id the moment it is minted.

**The sidebar placement is the owner's once the page exists.** A re-run at ~12:50 found the page out of place in
Sales and moved it back after Order Lines before `page` knew better; who moved it could not be told from the app log
(every agent works as the same account). `page` now places only a page it has just created, and reports otherwise.

## 6 · Browser checklist

Open **ERP Master ▸ Sales ▸ Sales Dashboard**.

1. **Sidebar**: *Sales Dashboard* sits under Sales right after Order Lines, with a dashboard icon.
2. **The page renders**: the *Order date* filter across the top. Headline row 1: Confirmed sales · Open quotations ·
   Value of open quotations · Orders to invoice. Headline row 2: Overdue invoices · Amount overdue · Received this
   month. Then Monthly sales beside the status pie, Top customers beside Sales by salesperson, and the invoicing pie
   beside Top products. **No card shows "无法形成图表" / "cannot draw chart"**, and **no amount is clipped** at your
   usual width (§3.1).
3. **Figures** match §4 (or a later `check`).
4. **RM** in front of every amount, with thousands separators and **always two decimals** (RM 1,383,107.20); counts
   with no prefix.
5. **Click-through**: click the Confirmed sales number, a Monthly sales column, a pie slice, a Top customers row —
   each should open a list of exactly the records behind it (e.g. the 7 *To Invoice* sales orders).
6. **The date filter**: pick *Last month* — Confirmed sales should read RM 94,496.00 and Monthly sales only August;
   Value of open quotations should move with it, and **Top products goes empty until the reseed** (§5). Overdue,
   Amount overdue and Received this month should **not** move. Clear it and the figures come back.
7. **Top customers / Top products** read highest first, ten rows, with the crown style on the first three.
8. **Sales by salesperson** draws horizontal bars.
9. **Titles and hover descriptions** read as plain English for a user (the ⓘ on each card).
10. **Mobile** (optional): the page has no mobile layout set, so HAP stacks the cards; check it is usable.
11. Two roles, via *Select Role*: a sales role sees the page and its charts; a role without Orders sees what HAP does
    for a chart it cannot read.
