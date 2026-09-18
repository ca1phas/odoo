# 16 · Leads

| | |
|---|---|
| Nocoly app | ERP Master · menu group **CRM** |
| Worksheet | Leads |
| Odoo model | `crm.lead` |
| Reference used for this hand-off | Teh Li Wei's authenticated `ohyes.odoo.com` English Opportunity form, list and pipeline, 18 Sep 2026. Re-check against `casimir.odoo.com` before final repository sign-off |
| Phase | 2 — CRM worksheet 4 of 4 |
| Status | Built; 3 views, 1 rule, 2 custom actions and 2 published workflows; CLI/MCP post-check and core rendered UI checks pass. **Three presentation/default checks remain** |

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
| My Pipeline | `6aad1284bd43f55762c7588b` | Kanban grouped by Stage; Open opportunities assigned to Teh Li Wei |
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

1. Clear the restored interrupted blank draft and confirm a genuinely fresh New Opportunity displays Stage **New**.
2. My Pipeline uses Teh Li Wei's static account id; no verified dynamic `currentUser` view-filter wire was available.
3. CRM Tags shows Raspberry in its lookup table, but a related tag on Leads renders as ordinary relation text rather than inheriting the colour.

CLI/MCP discrepancies are recorded in Chinese in the Nocoly workspace's 18 September limitation register. No product ticket was submitted.

## 4 · Not built now

Activities, Meetings, Quotations, Lead Mining, Sales/Invoice bridges, dashboards and new roles are outside this Phase 2 slice.
