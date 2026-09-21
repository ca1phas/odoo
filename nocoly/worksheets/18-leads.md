# 18 · Leads

| | |
|---|---|
| Nocoly app | ERP Master · menu group **CRM** |
| Worksheet | Leads |
| Odoo model | `crm.lead` |
| Reference used for the initial build | Teh Li Wei's authenticated `ohyes.odoo.com` English Opportunity form, list and pipeline, 18 Sep 2026. The owner's 21 Sep decision makes Odoo the sole ERP Master reference; see the later [CRM conformance review](14-crm-conformance.md) |
| Phase | 2 — CRM worksheet 4 of 4 |
| Status | Built; 3 views, 1 rule, 2 custom actions and 2 published workflows. The owner reports manual UI corrections on 21 Sep; CLI read-back confirms navigation, but fresh-form validation was blocked by CAPTCHA. The conformance findings are not signed off |

## 1 · Requirements delivered

### Fields

| Field | Nocoly type | Notes |
|---|---|---|
| Opportunity | Text, required title | English example hint |
| Stage | single Relation → Stages, required | New intended as the form default |
| Expected Revenue | Currency | Malaysia `RM`, 2 decimals |
| Probability | Number | `%`, 0–100 intent |
| Contact | single Relation → Contacts | Existing Foundation worksheet reused |
| Email | Email | English hint |
| Phone | Phone Number | Malaysia `+60` selector and hint |
| Salesperson | single Member | dynamic current-user form default, remains selectable |
| Sales Team | single Relation → Sales Teams | Sales form default |
| Expected Closing | Date | English hint |
| Priority | Rating | Odoo-style priority control |
| Tags | multi Relation → CRM Tags | `testtest` is selectable |
| Notes | Rich Text | internal notes |
| Campaign | single Relation → Campaigns | marketing attribution |
| Medium | single Relation → Mediums | marketing attribution |
| Source | single Relation → Sources | marketing attribution |
| Referred By | Text | marketing attribution |
| Lost Reason | single Relation → Lost Reasons | conditionally shown for Lost |
| Status | Single Select | hidden technical Open/Won/Lost outcome |
| Closed On | DateTime | hidden, read-only technical field |
| Active | Checkbox | hidden technical field |

### Relation foundations

| Worksheet | Model | Id | Seed |
|---|---|---|---|
| Sales Teams | `crm.team` | `6aad0f727d58b0f4493141c4` | Sales, Test |
| Campaigns | `utm.campaign` | `6aad0f8f7d58b0f4493141ce` | none |
| Mediums | `utm.medium` | `6aad0f92e54d2a34fa4e5808` | Direct, Email, Phone, Social Media, Website |
| Sources | `utm.source` | `6aad0f95bd43f55762c75833` | Google, Mass Mailing, Newsletter, Monster, Glassdoor, Craigslist, Survey, Referral |
| CRM Tags | `crm.tag` | `6aad0f99e43d174ab374fb05` | testtest — Raspberry |

CRM Tags is intentionally separate from Contact Tags.

### Views

| View | Id | Delivered behavior |
|---|---|---|
| My Pipeline | `6aad1284bd43f55762c7588b` | CLI reports `viewType=1` and `viewControl=Stage`, with Open opportunities filtered to Teh Li Wei's static ID. The 21 Sep conformance review calls this "no pipeline board"; a fresh rendered comparison is needed to resolve the conflict |
| All Opportunities | `6aad1284e54d2a34fa4e5862` | Opportunity, Contact, Email, Salesperson, Expected Revenue, Stage |
| Lost | `6aad1284805aef703286ac64` | Lost outcome rows with Lost Reason and Closed On |

### Rule and actions

- Rule `6aad1303e54d2a34fa4e5864`: show Lost Reason only when Status is Lost.
- Won button `6aad1469e43d174ab374fba1` → workflow `6aad1469e606b26d26c89493`.
- Lost button `6aad1474bd43f55762c758ba` → workflow `6aad1474e606b26d26c894f7`.

Won sets the Won stage, Status Won, Probability 100 and Closed On. Lost preserves the selected reason, sets Status Lost, Probability 0, Active false and Closed On. Lost is not a stage.

## 2 · Build

| Element | Id |
|---|---|
| Worksheet | `6aad111de43d174ab374fb5f` |
| Alias | `crm_lead` |
| Fields | 20 user/technical controls plus system fields |
| Records after TEST cleanup | 0 |

HAP writes used the explicit `fbmy-nocoly` CLI profile or Nocoly Personal MCP. Web was read-only.

## 3 · Validation

Passed:

- All relation targets and field types read back correctly; no Text stand-ins.
- UI shows RM, +60, Teh Li Wei, Sales, New on the saved test record, English hints, `testtest`, and Won/Lost.
- All Opportunities matches the source list's principal columns.
- Status, Closed On and Active are absent from the normal form.
- Won and Lost were executed end to end and read back. The exact TEST records were then soft-deleted.

Open/manual:

1. Confirm a genuinely fresh New Opportunity displays Stage **New**. The raw Stage control still carries a `defsource` pointing at the New stage on 21 Sep; browser verification was blocked by CAPTCHA, so the raw value is not proof of the form result.
2. My Pipeline uses Teh Li Wei's static account id; no verified dynamic `currentUser` view-filter wire was available.
3. CRM Tags shows Raspberry in its lookup table, but a related tag on Leads renders as ordinary relation text rather than inheriting the colour.
4. Reconcile the colleague's [Odoo conformance findings](14-crm-conformance.md), especially the pipeline UI, invented `Status`, Extra Info fields, roles and Odoo-only seed data. No destructive field change was made in this hand-off.

CLI/MCP discrepancies are recorded in Chinese in the Nocoly workspace's 18 September limitation register. No product ticket was submitted.

## 4 · Not built now

Activities, Meetings, Quotations, Lead Mining, Sales/Invoice bridges, dashboards and new roles are outside this Phase 2 slice. In particular, the planned Activities bundle (`mail.activity.type`, `mail.activity.plan`, `mail.activity.plan.template`) is not present in the ERP Master CLI inventory on 21 Sep. This says nothing about the older, separate Odoo CRM Malaysia app.
