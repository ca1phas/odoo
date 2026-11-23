# Odoo apps that are not open source (checked 23 Nov 2026)

**Method:** take the app list on Odoo's editions page (https://www.odoo.com/page/editions, read 23 Nov 2026), then look for each app's module in the official open-source code, branch 20.0 (`odoo-20.0/modules.json`).
- No module found means the app is Enterprise-only. Its code is not public, so a plan can only rely on candy99's screens and Odoo's documentation.
- The editions page's own check marks did not come through as text, so this list is **inferred from what the code lacks**, not read off the page.

## In the open-source code (Community, LGPL-3)

Invoicing (`account`), Expenses, CRM, Sales, Point of Sale, Website, eCommerce, Blog, Forum, Live Chat, eLearning, Inventory (`stock`, which in 20.0 includes batch and wave transfers), Manufacturing, Purchase, Maintenance, Repairs, Employees, Recruitment, Time Off, Attendances, Fleet, Lunch, Email Marketing, SMS Marketing, Events, Surveys, Project, Timesheets (`hr_timesheet`), Discuss, To-Do, Calendar.

## Not in the open-source code (Enterprise-only)

| Area | Apps (expected module name, absent from 20.0) |
|---|---|
| Finance | Accounting full version (`account_accountant`), Budgets (`account_budget`), Consolidation (`account_consolidation`), Documents (`documents`), Sign (`sign`), ESG |
| Sales | Subscriptions (`sale_subscription`), Rental (`sale_renting`), Amazon Connector (`sale_amazon`) |
| Supply chain | Barcode app (`stock_barcode`), MRP Shop Floor / work orders (`mrp_workorder`), PLM (`mrp_plm`), Quality (`quality`, `quality_control`) |
| HR | Payroll (`hr_payroll`), Appraisals (`hr_appraisal`), Referrals (`hr_referral`) |
| Marketing | Social Marketing (`social`), Marketing Automation (`marketing_automation`) |
| Services | Helpdesk (`helpdesk`), Planning (`planning`), Field Service (`industry_fsm`), Appointments (`appointment`), Timesheet grid and timer (`timesheet_grid`) |
| Productivity | Knowledge (`knowledge`), Approvals (`approvals`), Phone / VoIP (`voip`), IoT app (`iot`; only the IoT box drivers `iot_drivers` are open), Studio (`web_studio`) |

**What this means for plans:**
- Community apps can be planned from the source code, function by function.
- Enterprise apps can only be planned from screens and documentation, so expect more unknowns.
- Some Enterprise "apps" are partly a better screen on top of a Community app. Examples: the Barcode app on Inventory, Shop Floor on Manufacturing, the Timesheet grid on Timesheets. These are natural candidates for Compute screens.
