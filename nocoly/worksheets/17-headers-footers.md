# 17 · Quote Builder — one optional bundle, and one table not to build

| | |
|---|---|
| Odoo models | `sale.order.template` (+ `sale.order.template.line`) and `quotation.document` |
| Odoo menus | Sales › Configuration › **Quotation Templates** (action 530) and **Headers/Footers** (action 539) |
| Reference | `nocoly/reference/odoo-19.4/quotation.document.md` |
| Status | **One optional bundle, `bqb`, not core.** Moved out of Phase 3 on 21 Sep 2026. Quotation Templates left Phase 3 the same day and was **dropped from the plan entirely** — §1.1 |
| Date | 21 Sep 2026. Everything below was read off casimir, and the view definitions were read rather than inferred |

---

## 1 · Why these are optional, and why they are two bundles

The original draft of this page treated Headers/Footers as a core Phase 3 worksheet. It should not be, for a
reason that does not go away with more build effort: **HAP generates no quotation PDF.** A Header/Footer
record is a PDF that Odoo splices onto the front or back of a printed quotation, so the table is
configuration for an assembler that does not exist here and is not on any roadmap. That is the definition of
an optional bundle — a feature a client may want, priced and switchable on its own — not a gap in the core.

| Bundle | Models | Buy it when |
|---|---|---|
| **`bqb` Quote Builder** | `quotation.document` | branded cover and terms pages on a quotation. **Carries the caveat**: it records which PDFs a quotation should carry and does not assemble them |

**The caveat belongs on the bundle card**, not in a *Not built now* table at the bottom of a page. Someone
switching Quote Builder on needs to know before they start that no PDF comes out of the other end.

## 1.1 · Why Quotation Templates is not built at all — owner's decision, 21 Sep 2026

An earlier draft made `sale.order.template` a second bundle. It should not exist, because **HAP already has the
primitive Odoo needed a table for.**

A record's **Recreate** action opens a new record pre-filled from the source **including its child rows** —
proved on the app: recreating an order produced a second order line rather than moving the first, and the new
order's roll-ups computed to the cent. That is what applying a quotation template does. (A record's **Copy** is
*not* the same — it duplicates the header and leaves the lines behind. Tested, and the distinction is written
into `Is Template`'s own description so it is not rediscovered later.)

What the template table adds on top is a *name* and a *pickable set*, and those are two controls on Orders:

| Control | Alias | What it does |
|---|---|---|
| **Is Template** | `is_template` | marks an order as one kept to recreate from, never sent |
| **Template Name** | `template_name` | what it is called in the Templates view |

plus the rules **`A quotation needs a customer, a template does not`** (Customer's field-level `required` had to
come off — a rule cannot relax one) and **`Template Name is for templates`**, and a **Templates** view.

**What is genuinely lost**, recorded so nobody claims parity that does not exist:

| Odoo does | Here |
|---|---|
| Apply a template to an order that **already exists**, replacing its lines | **Not possible.** Recreate only makes new records |
| Templates live in **their own table** | A template **is** an order: it consumes a number from the sequence, and appears in Orders' lists and reporting unless each view filters it out |
| A template's `number_of_days` recomputes the new quotation's validity | **Untested.** If Recreate copies Expiration rather than recomputing it, a template made months ago yields a quotation born expired. One test settles it; the fix is a rule that clears Expiration, not a worksheet |

Neither gap justifies a worksheet and a child table. The cost model's 7.2 h comes out of the plan, and the
project total falls from 1502 h to **1495 h**.

## 2 · Where Headers/Footers is actually used

Traced on the tenant, because the answer was not obvious. Three consumers, all in Odoo:

1. **A quotation** — `sale.order.quotation_document_ids`, labelled *Headers/Footers*, on the order form's
   **Quote Builder** tab. Both that field and `customizable_pdf_form_fields` are `invisible="1"`; what a
   salesperson actually uses is a `customContentKanbanLikeWidget` card picker. The tab appears only once the
   quotation **has a customer** (`invisible="not (partner_id and is_pdf_quote_builder_available)"`).
2. **A quotation template** — `sale.order.template.quotation_document_ids`, labelled *Headers and footers*,
   on the template's own **Quote Builder** page. That page is `invisible="not (id)"` — it does not exist on
   an unsaved template, which is why a new template appears to have no such field. It holds exactly one
   field and no widget: a plain list, where the order gets the card picker.
3. **`add_by_default`** — puts a document on a new quotation without anyone choosing it.

Supporting fields: `available_quotation_document_ids` (read-only, the candidate list, narrowed by template)
and `customizable_pdf_form_fields` (JSON, the AcroForm values for that one order).

**In ERP Master today it is used by nothing.** Orders has no relation to Headers/Footers, and neither does
the Template worksheet. The only nearby link points the wrong way — see §4.

## 3 · Print Order — the one deliberate divergence

Odoo's field is `sequence`, and it is **global**: one integer per document, shared across every template and
quotation. Proved on the tenant — the three documents carry 10, 11, 12, and template 1 returns them as
`[2, 4, 3]`, i.e. sorted by those numbers rather than by the order they were attached. There is no
intermediate model (`ir.model` holds only `quotation.document`), so a plain many-to-many has nowhere to store
a per-template order, and **Odoo cannot express one either**.

It never appears on the form. In the list and kanban it is `<field name="sequence" widget="handle"/>` — the
drag handle. HAP has no drag handle, so it has to be a typed number.

**What is built instead: `Print Order`, numbered within each type.** Two changes from Odoo, both cosmetic:

- **The name.** *Sequence* is a developer's word and says nothing about what it does.
- **The numbering.** Odoo runs one number line across both types, so a footer at 12 looks like it comes after
  headers at 10 and 11 when it is simply the first footer. Numbering restarts per type, so *Footer · 1* reads
  as *first page after the quotation*.

The stored shape is still one integer per document, so it maps one-for-one onto `sequence` if this is ever
synced. **A per-template order was considered and rejected** — it would need a join subtable in place of the
relation, on both Orders and Template, inventing structure Odoo does not have to buy flexibility that in
practice nobody uses. Revisit only if two templates ever need the same documents in a different order.

## 4 · Headers/Footers (`quotation.document`) — fields

The worksheet exists, hand-built, at `6ab099387d58b0f449316373` with **5 controls and 3 records**.

| # | Field | Odoo | Type | Required | State |
|---|---|---|---|---|---|
| 1 | Name | `name` (via attachment) | Text · title | **yes** | built, **but not required** — Odoo's is `required=True`. Odoo also makes it read-only until a file is uploaded (`readonly="not raw"`), which is the one rule this model has |
| 2 | Document | `raw` / `ir_attachment_id` | Attachment | **yes** | built |
| 3 | Document Type | `document_type` | Single Select — Header · Footer | **yes** | built and correct; HAP's stray *Option 3* already carries `isDeleted` |
| 4 | **Print Order** | `sequence` | Number, integer | — | **missing** — see §3 |
| 5 | Quotation Templates | `quotation_template_ids` | Relation → Template, multiple | — | **built against the wrong worksheet** — it targets **Orders** `6ab09897e43d174ab3752d7b`. The id ordering explains it: this control was minted at `6ab09a…` and the Template worksheet not until `6ab0c3…`, so the intended target did not exist yet. Its `sourceControlId` also names a reverse control that is not on Orders — a parked reverse relation |
| 6 | Add By Default | `add_by_default` | Checkbox | — | built |

**Not built, each with a reason:**

| What | Why |
|---|---|
| **Active / Archive / Unarchive / an Archived view** | **Odoo surfaces no archive action on this model.** The form cog offers Duplicate and Delete; the kanban card menu offers Edit, Delete, Download; neither the form nor the list arch carries `active`. The field exists and is writable, and the scaffolding around it survives — a `web_ribbon` titled *Archived* on the kanban card and `Archived` / `All` filters in the search view — but nothing in the UI sets the flag. **This breaks the house pattern every other ERP Master worksheet follows**, and it is deliberate: the standing rule is to follow Odoo |
| **Description** | `description`, delegated from `ir.attachment` and `store=False`. Absent from the form, the list *and* the kanban — no Odoo user of this screen can see or set it. Building it would put a box on the form that Odoo does not have |
| `form_field_ids` / `sale.pdf.form.field` | Read-only, computed by parsing the PDF's AcroForm fields. HAP cannot parse a PDF |
| `company_id` | Single company, as everywhere else |
| **The PDF assembly** | The feature this table configures. HAP does not generate the quotation PDF — §1 |

## 5 · The Template worksheet — to be retired

Hand-built at `6ab0c38dbd43f55762c78496` with **3 controls** — Name (required, title), Description,
Attachment — and one record, *Testing*. It never grew a Lines child table, which is the half a template
exists for.

**The owner approved retiring it on 21 Sep 2026**, once §1.1 settled that templates are flagged orders. Per
BUILDING.md a retirement is a rename to `ZZ obsolete – `, not a delete, and it is reported rather than done
quietly.

Two things move with it:

1. **Orders' `Template` relation** (`6ab0c459805aef703286d782`) points at this worksheet. It should point at
   **Orders itself, filtered to Is Template** — which is `sale_order_template_id` exactly, in the flag model.
2. **Headers/Footers' `Quotation Templates` relation** was going to need this worksheet as its target. It
   already points at Orders — a mis-pick when it was made, and now the right target. It still needs the
   Is Template filter and its parked reverse relation cleared (§4 row 5).

## 6 · The build, if either bundle is taken

**`bqb` Quote Builder** — small, and mostly correction:

1. Re-point **Quotation Templates** at the Template worksheet, and clear the parked reverse relation.
2. Add **Print Order** (§3).
3. **Name** required, and the rule *Name is read-only until a document is uploaded*.
4. Aliases — every control carries `alias=''` today; the convention is the Odoo field name (`name`,
   `document_type`, `ir_attachment_id`, `sequence`, `quotation_template_ids`, `add_by_default`).
5. The two relations that make it mean anything: **Orders → Headers/Footers** and **Template →
   Headers/Footers**, both multiple. Neither exists.
6. Views: the list sorted by Document Type then Print Order. No Archived view — §4.

**Quotation Templates** — nothing. §1.1. The two controls and two rules that replace it belong to Orders,
not to this bundle, and are built there.

## 7 · Estimates

From the same cost model as every other bundle (`nocoly/analysis/timeline3.py`):

| Bundle | Worksheets | Hours |
|---|---|---|
| `bqb` Quote Builder | 1 | **1.1** |

Phase 3 Sales drops from 5 worksheets / 73.1 h to **2 worksheets / 64.8 h** — Orders and Order Lines alone.
The optional bundles go from 17 to **18**, and from 30 worksheets / 100 h to **31 / 101 h**. Quotation
Templates' 7.2 h leaves the plan rather than moving columns, so the **project total falls from 1502 h to
1495 h** and the schedule from 38 weeks to 37.
