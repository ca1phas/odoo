# ERP Master CRM hand-off update — 21 Sep 2026

This updates Teh Li Wei's Phase 2 hand-off after the owner's manual navigation corrections. It does not close the Odoo conformance review or authorize further HAP changes. The owner-directed reference for ERP Master is Odoo itself (see `DECISIONS.md`, 21 Sep), not either builder's previous form.

## Confirmed today

- Target: Nocoly organisation `f887b7cc-6832-416c-8e7e-c730aec70a21`, ERP Master `6cb4d051-a33c-4bf9-b56f-5f47f0e85dc9`; read with CLI profile `fbmy-nocoly` and the app ID explicitly.
- Stages and Lost Reasons are under CRM › Configuration in CLI `app info` and the rendered administrator sidebar. Recurring Plans has CLI `displayType=2` and a hidden marker in that sidebar. The owner made these UI changes; the earlier MCP move/hide success response did **not** accomplish them.
- Leads has zero records. Its Stage control still has a raw `defsource` referencing the New stage, but a genuinely fresh form was **not** verified today: navigating to Leads triggered a CAPTCHA. The static Teh Li Wei filter in My Pipeline is unchanged.
- CLI `worksheet view info` reports My Pipeline as `viewType=1`, `viewControl=Stage`. This contradicts the newly merged conformance document's assertion that there is no pipeline board. A rendered comparison is required before either claim is closed; do not rebuild or remove the view based on one reading.
- ERP Master's worksheet inventory contains no Activity Types, Activity Plans or Plan Steps. The Activities bundle in `plan/phases.json` remains planned, not built. The existing global To-do control is not that bundle.

## Reconciliation needed before the next HAP write

1. Review `worksheets/14-crm-conformance.md` against the actual ERP Master and Odoo screens, separating verified discrepancies from API/source-only inferences. Its description of the CRM build as "by hand" is inaccurate: the initial build used HAP CLI and Personal MCP; only the three navigation corrections above were manual.
2. After the CAPTCHA is cleared by the user, check the fresh New Opportunity Stage default and visually compare the My Pipeline board to Odoo's grouped kanban. Record the exact UI result, including any difference between a grouped gallery and Odoo's board.
3. Triage the conformance items with the owner before destructive changes: invented Status, Recurring Plans retention, title uniqueness switches, seed-data replacement and role policy. The CLI-only finding is not consent to delete fields or records.
4. Only then design the Activities bundle from Odoo's rendered Activity Types and Activity Plans screens. Confirm whether actual scheduled activity records and lead-level Schedule Activity / Mark Done flows are in scope; the three planned configuration worksheets alone do not implement those interactions.

No HAP object or record was changed during this update. MCP status: not evaluated in this 21 Sep check; the prior 18 Sep MCP issues remain documented, not retested.
