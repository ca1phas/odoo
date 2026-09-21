# `quotation.document` — Headers/Footers (Odoo saas~19.4+e)

Read from **casimir.odoo.com** on 21 Sep 2026 over read-only RPC. Menu **Sales › Configuration ›
Headers/Footers** → `ir.actions.act_window` **539**, `res_model` `quotation.document`,
`view_mode` **kanban, list, form**.

The model comes from the Enterprise module **`sale_pdf_quote_builder`**. It is not in the 19.0 Community
checkout at `/home/cas/odoo/addons/`, so there is nothing to read there — this extract is the only source.

## What the feature actually is

A Header/Footer record is **a PDF file** that Odoo splices onto the front or the back of the quotation PDF
when a quotation is printed or sent. If the uploaded PDF carries AcroForm fields, Odoo lists them in
`form_field_ids` (`sale.pdf.form.field`) and fills them from the order at print time. The order form's
**Quote Builder** tab (`quotation_document_ids` + `customizable_pdf_form_fields`) is where a salesperson
picks which of these go onto a given quotation.

So the table is **configuration for a PDF assembler**. The records are cheap to model; the assembler is not.

## Structure

`quotation.document` **delegates to `ir.attachment`** (`_inherits`): `ir_attachment_id` is required and
stored, and `name`, `description`, `res_model`, `res_field`, `res_id` and the file bytes all come through it
with `store=False`. In HAP there is no delegation — an Attachment control plus a Text control covers it.

### Own fields

| Field | Label | Type | Required | Notes |
|---|---|---|---|---|
| `ir_attachment_id` | Related attachment | many2one → `ir.attachment` | **yes** | the PDF itself; in the form it is edited as `raw` |
| `document_type` | Document Type | selection **`header` Header · `footer` Footer** | **yes** | the whole point of the record |
| `active` | Active | boolean | — | Archive / Unarchive |
| `sequence` | Sequence | integer | — | order in which pages are spliced; list is sorted by it |
| `quotation_template_ids` | Quotation Templates | many2many → `sale.order.template` | — | which templates offer this document |
| `form_field_ids` | Form Fields Included | many2many → `sale.pdf.form.field` | — | **read-only**, computed from the PDF's AcroForm fields |
| `add_by_default` | Add By Default | boolean | — | put it on a new quotation without being asked |

### Delegated from `ir.attachment`

`name` (**required**, char), `description` (text), `raw` / `datas` (the file), `mimetype`, `res_model`,
`res_field`, `res_id`, `company_id`.

## Form view

```
name                 readonly="not raw"      ← you cannot name it until a file is uploaded
document_type
raw                                          ← the PDF upload
quotation_template_ids   widget=many2many_tags
add_by_default
create_uid           readonly="1"
create_date          readonly="1"
form_field_ids       invisible="True" readonly="True"
company_id           invisible="True" readonly="True"
```

## List view

`sequence · name · document_type · quotation_template_ids · add_by_default · company_id`

Default view is **kanban**, then list, then form.

## Records on the tenant

**One**, and it is a sample:

| Name | Type | Sequence | Add by default | Templates |
|---|---|---|---|---|
| `exSlip_2026062401315.pdf` | Header | 10 | no | — |

`sale.order.template` (Quotation Templates) holds **zero records**, so `quotation_template_ids` points at an
empty table.

## Constraints

None — `ir.model.constraint` reports no unique or check constraint on this model.
