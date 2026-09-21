# 18 · Sales Reporting — requirements

| | |
|---|---|
| Odoo model | `sale.report` — a **SQL view**, not a table |
| Odoo menus | Sales › Reporting › **Sales** (481) · **By Salespersons** (482) · **By Products** (483) · **By Customers** (484) |
| HAP shape | one **custom page** (`type=1`) holding chart components, as CRM Reporting `6ab0be302e0e812bfe7099bc` already does |
| Status | **Requirements only.** Nothing built |
| Date | 21 Sep 2026, read from casimir over read-only RPC |

---

## 1 · What Odoo's Sales Reporting actually is

Four menu entries, **one model**, and they differ only in a default group-by carried in the action's context:

| Menu | Action | Context |
|---|---|---|
| Sales | 481 | `search_default_Sales: 1`, `search_default_filter_order_date: 1` |
| By Salespersons | 482 | `search_default_User: 1`, `group_by: user_id` |
| By Products | 483 | `search_default_Product: 1`, `group_by: product_id` |
| By Customers | 484 | `search_default_Customer: 1`, `group_by: partner_id` |

Two things follow, and both shape the build:

- **Every one of them defaults to a date filter** on the order date, and 481 and 483 also default to
  `state = 'sale'`. Odoo's sales reporting means *confirmed orders in a period*, not everything in the table.
- **`sale.report` is a database view over `sale.order.line`** — one row per line, with the order's own columns
  (customer, salesperson, team, status, date) **denormalised onto each line**. That is what lets one query
  group by product *and* by customer.

### Its measures and dimensions

**Measures (17)** — the ones worth carrying: `price_subtotal` *Untaxed Total*, `price_total` *Total*,
`product_uom_qty` *Qty Ordered*, `qty_delivered`, `qty_invoiced`, `qty_to_invoice`, `discount_amount`,
`nbr` *# of Lines*, and `discount` / `price_unit`, which aggregate as **averages**, not sums.

**Dimensions (22)** — `date` *Order Date*, `partner_id` *Customer*, `user_id` *Salesperson*, `team_id`
*Sales Team*, `state` *Status*, `invoice_status`, `product_id`, `product_tmpl_id`, `categ_id` *Product
Category*, `product_uom_id`, `country_id` / `state_id` / `industry_id` (customer geography), and the three
UTM fields.

## 2 · The structural problem, and the pattern that solves it

HAP has **no view model**. A chart hangs off exactly one worksheet and groups by a field on that worksheet.
So the denormalisation `sale.report` does in SQL has to exist as **stored lookup controls**, and where a
report needs them decides which worksheet it can be built on:

| Worksheet | Holds today | Can report on |
|---|---|---|
| **Orders** | Customer · Salesperson · Sales Teams · Status · Invoicing Status · Quotation/Order Date · Tax Mode · Payment Terms · the three roll-ups | anything at **order** level — revenue by customer, by salesperson, by team, by status, over time |
| **Order Lines** | Product · Display Type · Unit · Taxes · Quantity · Discount · Subtotal · Tax Amount · Total | anything at **line** level — revenue by product, quantity by product — but **cannot cross it with a customer, a salesperson or a date**, because it holds none of them |

**The fix is the pattern 07 already uses.** Invoice Lines carries three stored lookups off its Invoice
relation — *Number*, *Accounting Date*, *Status* — precisely so the standalone list can show them. Order Lines
needs the same, off its Orders relation:

| Lookup to add | From Orders | Why |
|---|---|---|
| **Order Date** | Quotation/Order Date | every Odoo reporting action defaults to filtering on it |
| **Customer** | Customer | *By Customers* crossed with product |
| **Salesperson** | Salesperson | *By Salespersons* |
| **Sales Team** | Sales Teams | Odoo's `team_id` dimension |
| **Status** | Status | so reporting can exclude quotations and cancellations, as Odoo's default does |

Five lookups, one version-pinned save. After that, Order Lines **is** `sale.report`.

**Product Category is the one that is not cheap.** Odoo's `categ_id` reaches the category through the product.
Order Lines relates to Product Variants, and **Product Variants carries no Category lookup** — it has Name,
Product Type, Unit, Sales Price, Sales and Purchase, but not Category. So *By Product Category* needs either a
Category lookup added to Product Variants first and then a second hop from Order Lines, or it is deferred.
**Whether HAP will resolve a lookup of a lookup is unproven in this app** and needs a spike before it is
promised.

## 3 · What HAP gives us to build with

`hap custom-page component-types`: **analysis** (chart/statistic) · **view** (an embedded worksheet view) ·
**filter** · **tabs** · **card** · richText · button · image · embedUrl · carousel.

A chart is **a separate stored object** built against a worksheet (`hap worksheet chart`), and the custom page
holds only its id — CRM Reporting's three chart components each carry a bare `reportId` as their `value`. So a
build is two layers: create the charts, then place them.

Chart types by `reportType`: 1 column · 2 line · 3 pie · 8 **pivot** · 10 **number** · 16 ranking (there is
no 4). Odoo's reporting is graph + pivot, so **pivot (8)** and **column (1)** carry most of it, with
**number (10)** for the headline figures.

> **The trap, from the CLI's own guide:** a chart with no `filter` block **saves successfully and renders
> blank** — "无法形成图表". The CLI now injects an all-time default, but any chart that should be scoped to a
> period must carry `filter.filterRangeId` naming the date field and a `rangeType`. Every chart this page
> builds is date-scoped, so every one of them must set it.

## 4 · Proposed page

One custom page, **Sales Reporting**, in the Sales group beside Orders — mirroring Odoo's single Reporting
menu rather than four separate pages, with **tabs** standing in for the four menu entries.

| Tab | Component | Worksheet | Shape |
|---|---|---|---|
| **Overview** | four **number** charts | Orders | Untaxed Amount · Total · order count · average order value, all scoped to Status = Sales Order |
| | **column** by month | Orders | Σ Untaxed Amount grouped by Quotation/Order Date |
| | **pie** by status | Orders | order count by Status — the one chart that deliberately does *not* filter to confirmed |
| **By Customer** | **ranking** + **pivot** | Orders | Σ Untaxed Amount by Customer |
| **By Salesperson** | **column** + **pivot** | Orders | Σ Untaxed Amount by Salesperson, split by Sales Team |
| **By Product** | **ranking** + **pivot** | Order Lines | Σ Subtotal and Σ Quantity by Product |
| | **pivot** | Order Lines | Product × Order Date, once the lookups of §2 exist |

Plus a **filter** component bound to Order Date so the whole page moves together, which is what Odoo's
`search_default_filter_order_date` does for its four actions.

**Every chart excludes templates** (`Is Template` not ticked) and **excludes Section, Subsection and Note
lines** where it is built on Order Lines — the same Display Type filter the roll-ups already carry, for the
same reason.

## 5 · Dependencies

| Needs | State |
|---|---|
| **Order Lines' Subtotal computing** | **In flight.** Until the Currency→Formula conversion lands, all 30 seeded lines store Subtotal empty and every line-level chart would draw zero |
| The five lookups of §2 | not built |
| Product Category lookup chain | not built, and **unproven** |
| Seeded data worth charting | **Provisional.** The owner will reseed everything once Phases 1–3 are complete, so charts should be built and proved against structure, not against figures |

## 6 · Not built now

| What | Why |
|---|---|
| **Customer geography and industry dimensions** (`country_id`, `state_id`, `industry_id`) | Countries and States are built, but Contacts carries no Industry, and reaching a customer's country from an order line is a two-hop lookup — the same unproven chain as Product Category |
| **The three UTM dimensions** | Marketing attribution is built, but Orders carries no Campaign / Source / Medium control yet |
| `weight`, `volume` | Inventory is not built |
| `untaxed_amount_invoiced` / `_to_invoice` | need the order → invoice link |
| **Quotations Analysis** (action 486) | a separate action over the same model; the Overview tab's status pie covers the question it answers |
