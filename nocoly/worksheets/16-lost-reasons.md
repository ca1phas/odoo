# 16 · Lost Reasons

| | |
|---|---|
| Nocoly app | ERP Master · menu group **CRM** |
| Worksheet | Lost Reasons |
| Odoo model | `crm.lost.reason` |
| Reference used for this hand-off | Teh Li Wei's authenticated `ohyes.odoo.com` English UI, 18 Sep 2026. Re-check against `casimir.odoo.com` before final repository sign-off |
| Phase | 2 — CRM worksheet 2 of 4 |
| Status | Existing worksheet repaired in place; 3 records preserved; view and Leads loss flow tested. Owner moved it under CRM › Configuration; CLI and sidebar confirmed on 21 Sep. |

## 1 · Delivered scope

Fields: Lost Reason (required title) and Active. Records match the live selector:

- Too expensive
- We don't have people/skills
- Not enough stock

The default table view was repaired. Leads uses a single Relation to this worksheet. A business rule hides Lost Reason while an opportunity is open and shows it when the technical Status is Lost.

## 2 · Build

| Element | Id |
|---|---|
| Worksheet | `6aacb149e43d174ab374e721` |
| Leads Relation | `6aad117ce43d174ab374fb64` |
| Records | 3 |

## 3 · Validation

- CLI/MCP count: 3.
- The Lost action was exercised with **Too expensive**. Read-back showed Status Lost, Probability 0, Active false, Closed On populated and the reason retained.
- The temporary TEST record was soft-deleted after verification.
- The MCP move call previously did not change the rendered sidebar. On 21 Sep, the owner moved Lost Reasons manually; `hap app info` shows it under Configuration and the browser sidebar agrees. The earlier MCP call is still a recorded limitation.

No product ticket was submitted.
