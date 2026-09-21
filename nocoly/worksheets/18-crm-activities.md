# 18 · CRM Activities — implementation hand-off

| | |
|---|---|
| Nocoly app | ERP Master · CRM |
| HAP worksheets | My Activities · Activity Types · Activity Plans · Activity Plan Steps |
| Odoo models | CRM-scoped equivalent of `mail.activity`, `mail.activity.type` and `mail.activity.plan` |
| Built by | **Teh Li Wei**, 21 Sep 2026, through `hap --profile fbmy-nocoly` |
| Reference | Odoo CRM rendered UI, with ERP Master's existing Leads worksheet preserved |
| Status | **Built and partly UI-tested.** Creation notification has rendered evidence; reassignment and due-time delivery still need runtime testing; the Odoo-style Lead top button is not delivered |

This is a bounded CRM activity implementation, not a claim to reproduce Odoo's global polymorphic
`mail.activity` engine. It adds useful assignment and reminder behaviour without extending the same model to
Contacts, Orders, Invoices or every future ERP worksheet.

## 1 · What is built

- `My Activities` is the user-facing worksheet. Its views are My Activities, Overdue, Today, Upcoming, Done
  and Calendar.
- `Activity Types` is seeded with To-Do, Email, Call, Meeting and Document.
- `Activity Plans` and `Activity Plan Steps` model repeatable plan headers and their ordered lines. Automatic
  application of a plan is not built.
- An Activity relates to one Lead and one Activity Type, has Summary, Due Date, Assigned To, Status, Notes,
  completion/cancellation metadata and Active.
- Reschedule, Mark Done and Cancel actions exist on Activities. The Mark Done workflow has passed an end-to-end
  CLI/Web test on `TEST - CRM Activity follow-up`.
- The mounted Activities subtable on Leads is retained as the technical relation bridge but hidden from the
  normal Lead form. Its raw relation metadata was preserved.

## 2 · Operational workflows

| Workflow | Trigger | Result | Verification |
|---|---|---|---|
| Notify Activity Assignee | Activity created | In-app notification to Assigned To | Published; a CLI-created test Activity produced Nocoly's new-message indicator |
| Notify Activity Reassignment | Assigned To changes | In-app notification to the new assignee | Published and structurally read back; second-user runtime test pending |
| Activity Due Reminder | 09:00 on Due Date | If Status is Scheduled and Active is checked, notify Assigned To | Published and structurally read back; the test record is on the Calendar, but 09:00 delivery has not elapsed |

The due reminder is a per-record date trigger, not a daily full-table scan. That keeps the workflow narrow and
avoids waking for records that are not due.

## 3 · Test records left for review

| Record | State | Purpose |
|---|---|---|
| `TEST - CRM Activity follow-up` | Done, due/completed 21 Sep 2026 | Mark Done workflow and Done/Calendar rendering |
| `TEST - Activity notification flow` | Scheduled, due 22 Sep 2026 | Creation notification and due reminder |

Both point to `TEST MY - New sales enquiry` and Activity Type To-Do. They remain intentionally for review.

## 4 · Known gap: Schedule Activity on the Lead

Three direct-related-record action configurations were tested and removed. The final raw action retained the
child-side Lead relation correctly in CLI read-back, but Nocoly Web returned:

> Unable to execute button "Schedule Activity" Associated field is hidden or has been deleted

The final Leads action inventory is Won, Lost and Quotation; no broken Schedule Activity button remains. A
simple direct relation action therefore cannot satisfy both requirements at once: the relation bridge must be
visible for the action, while the approved Odoo-like Lead form hides the mounted subtable.

If the top button is approved as the next slice, implement it with hidden technical scheduling fields on Leads,
a Fill workflow and a Create Activity workflow, then validate the complete no-save/create path in Web. Do not
reuse the failed direct-relation configuration.

## 5 · Review checklist

- Create a clearly named `TEST …` Activity in My Activities and confirm Assigned To receives the notification.
- Change Assigned To to another test user and confirm only the new assignee receives the reassignment message.
- Keep the scheduled 22 Sep test active through 09:00 and confirm the due message; complete/cancel it before the
  trigger to prove the guard suppresses the message.
- Confirm the Lead form does not show the Activities subtable.
- Confirm My Activities' six views and English labels remain usable for a non-administrator.
- Decide whether Activity Plan Steps should be hidden manually from the sidebar; hiding its only view did not
  hide the worksheet entry.
- Do not report the Lead top button, activity-plan execution, Meetings/Calendar bridge, Odoo chatter, top-bar
  counter or Opportunity × Activity Type matrix as delivered.

## 6 · Tool and evidence boundary

All HAP writes and record creation were made through CLI. Web was read-only and is the authority for rendered
behaviour. The highest-impact mismatch is the Schedule Activity action: CLI read-back looked valid, but Web
execution failed, so the action was deleted. Other captured CLI issues include workflow batch-add partial writes,
the full wire required for dynamic Member recipients and high-level field output not reflecting raw layout-hidden
permission.

`MCP status: not evaluated`. No MCP write or verification was used for this Activity follow-up, and no product
ticket was submitted.
