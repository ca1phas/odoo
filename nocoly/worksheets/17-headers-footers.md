# 17 · Headers/Footers — requirements

| | |
|---|---|
| Odoo model | `quotation.document` (Enterprise, `sale_pdf_quote_builder`) |
| Odoo menu | Sales › Configuration › **Headers/Footers**, action 539 |
| Reference | `nocoly/reference/odoo-19.4/quotation.document.md` |
| Status | **§1 only — requirements.** The owner is building this worksheet by hand; nothing here has been built by a builder, and no `build/` script owns it |
| Date | 21 Sep 2026, read from casimir before the trial expires |

---

## 1 · What it is, and the decision to take first

A Header/Footer record is **a PDF file** that Odoo splices onto the front or the back of a quotation's PDF
when the quotation is printed or sent. Where the uploaded PDF carries AcroForm fields, Odoo reads them into
`form_field_ids` and fills them from the order at print time. The order's **Quote Builder** tab is where a
salesperson picks which documents go onto a given quotation.

**So this table is configuration for a PDF assembler, and HAP has no PDF assembler.** The records model
cleanly — a file, a type, a sequence, two flags and a relation. What cannot be built is the thing they
configure: nothing downstream will ever splice those pages onto anything.

That makes it an owner's call, and it should be taken before the layout work, not after:

- **Build it as a configuration table now.** Cheap, faithful, and it holds the files where Odoo holds them.
  The worksheet's *Not built now* then has to say plainly that the documents are stored and never used.
- **Defer the whole worksheet** until whatever generates a quotation PDF exists.

Two facts that bear on the call. The tenant holds **one record**, `exSlip_2026062401315.pdf`, a sample
header with no templates attached and *Add By Default* off. And `sale.order.template` — the only table this
worksheet relates to — holds **zero records**, because Quotation Templates has not been built either.
Built today, this worksheet would be one sample row pointing at an empty table.

## 2 · Fields, if it is built

Odoo's model delegates to `ir.attachment` (`_inherits`), so `name`, `description` and the file bytes are the
attachment's. HAP has no delegation; an Attachment control and a Text control cover it, and the delegation
is not a difference worth recording beyond a line in §3.

| # | Field | Odoo | Type | Required | Default | Notes |
|---|---|---|---|---|---|---|
| 1 | Name | `name` (via attachment) | Text · title field | **yes** | — | Odoo makes it **read-only until a file is uploaded** (`readonly="not raw"`) — the upload names it. Worth reproducing with a rule |
| 2 | Document | `raw` / `ir_attachment_id` | **Attachment**, single file | **yes** | — | the PDF. Odoo's `ir_attachment_id` is required; in the form it is edited as `raw` |
| 3 | Document Type | `document_type` | Single Select, dropdown | **yes** | — | **Header · Footer** |
| 4 | Sequence | `sequence` | Number, integer | — | 10 | the order pages are spliced in; the list sorts on it |
| 5 | Quotation Templates | `quotation_template_ids` | Relation → Quotation Templates, **multiple** | — | — | **blocked** — that worksheet does not exist. Either build Quotation Templates first or leave this control out and record it |
| 6 | Add By Default | `add_by_default` | Checkbox | — | unticked | put the document on a new quotation without being asked |
| 7 | Description | `description` (via attachment) | Text, multi-line | — | — | not on Odoo's form, but it is on the model |
| 8 | Active | `active` | Checkbox | — | ticked | hidden, as on every other worksheet; driven by Archive / Unarchive |

**Not a field to build:** `form_field_ids` (*Form Fields Included*) is read-only and computed by parsing the
PDF's AcroForm fields. HAP cannot parse a PDF. Leave it out and say so.

## 3 · Rules, buttons and views

**Rules.** One, and it is Odoo's: *Name is read-only until a document is uploaded*
(`readonly="not raw"`). There are **no SQL or unique constraints** on this model — `ir.model.constraint`
reports none, so a duplicate name is allowed.

**Buttons.** Archive / Unarchive, the same pair every other worksheet carries, with Odoo's confirmation
*"Are you sure that you want to archive this record?"*. Nothing else — the model has no workflow.

**Views.** Odoo's `view_mode` is **kanban, list, form** and kanban opens first. The list is
`sequence · name · document_type · quotation_template_ids · add_by_default · company_id`, sorted by
sequence. An **Archived** view, as elsewhere.

## 4 · Not built now

| What | Why |
|---|---|
| **The PDF assembly itself** — splicing headers and footers onto a quotation's PDF | HAP does not generate the quotation PDF. This is the feature the table configures, and it does not exist |
| `form_field_ids` and the whole `sale.pdf.form.field` model | The list is computed by reading AcroForm fields out of the uploaded PDF |
| `quotation_template_ids` | Quotation Templates (`sale.order.template`) is not built and holds zero records on the tenant |
| `company_id` | Single company, as everywhere else in ERP Master |

## 5 · Dependencies

| Needs | State |
|---|---|
| **Quotation Templates** (`sale.order.template`) | **not built**, and empty on the tenant |
| Orders (`sale.order`) — the Quote Builder tab is the consumer | worksheet 16, requirements only |

Neither blocks a configuration-table build; both block the feature being useful.
