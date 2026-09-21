# 15 · Stages

| | |
|---|---|
| Nocoly app | ERP Master · menu group **CRM** |
| Worksheet | Stages |
| Odoo model | `crm.stage` |
| Reference used for this hand-off | Teh Li Wei's authenticated `ohyes.odoo.com` English UI, 18 Sep 2026. Re-check against `casimir.odoo.com` before final repository sign-off because that remains this repository's shared tenant reference |
| Phase | 2 — CRM worksheet 1 of 4 |
| Status | Existing worksheet repaired in place; 4 records preserved. Owner moved it under CRM › Configuration; CLI and sidebar confirmed on 21 Sep. |

## 1 · Delivered scope

The worksheet keeps the four live stages in sequence: **New · Qualified · Proposition · Won**. Lost is deliberately not a stage.

Fields: Stage Name (required title), Sales Teams (multi Relation to CRM Sales Teams), Sequence, Folded in Pipeline, Is Won Stage?, Days to rot and Requirements. The Won record is the only won stage.

The default table view no longer points at the deleted stock Name/Description/Attachment controls. Leads uses this worksheet for its required Stage Relation and for the My Pipeline Kanban grouping.

## 2 · Build

| Element | Id |
|---|---|
| Worksheet | `6aacb0f0805aef7032869597` |
| Sales Teams Relation | `6aad104ae54d2a34fa4e581c` |
| Records | 4 |

No record was deleted or recreated.

## 3 · Validation

- CLI/MCP count: 4.
- Existing test opportunity rendered Stage **New**; Won workflow selected the real **Won** row.
- All Relations opened without a deleted-worksheet error.
- The Personal MCP previously returned success when asked to move this worksheet into Configuration, but the sidebar did not change. On 21 Sep, the owner completed the move manually; `hap app info` shows Stages under Configuration and the browser sidebar agrees. This confirms the current UI state, not that the earlier MCP call worked.

No product ticket was submitted.
