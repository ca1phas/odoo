# 18 · CRM Activities — implementation hand-off

| | |
|---|---|
| Nocoly app | ERP Master · CRM |
| HAP worksheets | My Activities · Activity Types · Activity Plans · Activity Plan Steps |
| Odoo models | CRM-scoped equivalent of `mail.activity`, `mail.activity.type` and `mail.activity.plan` |
| Built by | **Teh Li Wei**, 21 Sep 2026, through `hap --profile fbmy-nocoly` |
| Reference | Odoo CRM rendered UI, with ERP Master's existing Leads worksheet preserved |
| Status | **Built and UI-tested.** The workflow-backed Lead `Schedule Activity` action creates a real Activity; creation notification has rendered evidence; reassignment and due-time delivery still need runtime testing |

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
| `TEST - Scheduled from Lead action` | Scheduled, due 23 Sep 2026 | Workflow-backed Lead action and Calendar rendering |
| `TEST - Schedule Activity repeat` | Scheduled, due 24 Sep 2026 | Repeated action creation |
| `TEST - Schedule Activity default reset` | Scheduled, due 25 Sep 2026 | First reset-node test |
| `TEST - Schedule Activity final reset` | Scheduled, due 26 Sep 2026 | Corrected Relation reset and final repeatability proof |

All six point to `TEST MY - New sales enquiry` and Activity Type To-Do. They remain intentionally for review.

## 4 · Schedule Activity on the Lead

The direct-related-record design remains invalid and its three failed attempts remain useful historical evidence:
when the mounted subtable is hidden, Nocoly rejects that action as a hidden/deleted associated field. Phase 3
therefore uses the approved alternative instead of reopening that relation path.

Leads now owns five hidden technical inputs—Activity Type, Summary, Due Date, Assigned To and Note. The
`Schedule Activity` Fill action writes those inputs, then its published workflow creates a real row in My
Activities with the current Lead relation, Scheduled status and Active flag. To-Do, current date and current user
are the configured defaults; Note is optional. The fields use raw `fieldPermission=011`, so they do not appear in
the normal Lead form.

The workflow finishes with `Reset Schedule Inputs`. It clears Summary and Note, restores Activity Type to To-Do,
sets Due Date from System Current time, and sets Assigned To from System Trigger user. This is necessary because a
Fill action on an existing record does not reapply field defaults after a previous workflow has cleared the stored
values. The final CLI trigger and read-only Web reopening proved the action is repeat-safe.

CLI end-to-end validation triggered the workflow on `TEST MY - New sales enquiry` and created
`TEST - Scheduled from Lead action` (`775f477f-fe05-4a45-a9db-645a53efc964`). Read-only Web validation then
confirmed the top button, dialog values and Calendar entry. The stored `sureName=Schedule` is rendered by HAP as
`Confirm`; this is a recorded presentation mismatch, not a functional blocker.

The final repeatability fixture is `TEST - Schedule Activity final reset`
(`44447036-2147-4f37-89d0-76bc1f201b34`). It was created with To-Do, the source Lead, 26 September, Teh Li Wei,
Scheduled, Active and its test note. After creation, the Lead read back with To-Do, 21 September, Teh Li Wei and
empty Summary/Note; the Web dialog showed the same clean defaults and was cancelled without saving.

## 5 · Review checklist

- Create a clearly named `TEST …` Activity in My Activities and confirm Assigned To receives the notification.
- Change Assigned To to another test user and confirm only the new assignee receives the reassignment message.
- Keep the scheduled 22 Sep test active through 09:00 and confirm the due message; complete/cancel it before the
  trigger to prove the guard suppresses the message.
- Confirm the Lead form does not show the Activities subtable.
- Open `Schedule Activity` repeatedly from the test Lead and confirm To-Do/current date/current user defaults,
  empty Summary/Note, then cancel without saving. This passed on 21 Sep 2026.
- Confirm My Activities' six views and English labels remain usable for a non-administrator.
- Decide whether Activity Plan Steps should be hidden manually from the sidebar; hiding its only view did not
  hide the worksheet entry.
- Do not report activity-plan execution, Meetings/Calendar bridge, Odoo chatter, top-bar counter or Opportunity
  × Activity Type matrix as delivered. The Lead top button is delivered through Fill + workflow, not direct relation.

## 6 · Tool and evidence boundary

All HAP writes and record creation were made through CLI. Web was read-only and is the authority for rendered
behaviour. The original direct-relation Schedule Activity action looked valid in CLI but failed in Web and was
deleted. Its replacement is the delivered Fill + Create workflow above. Captured CLI issues include workflow
batch-add partial writes, the full wire required for dynamic Member recipients, add-fields dropping a Member
default, save-action clearing that Member mapping, and one malformed raw button wire temporarily breaking both
button listing and deletion until an in-place minimal recovery. A raw update-node Relation also requires a bare
row ID rather than the JSON-array string used by worksheet record updates; the wrong shape saved and published but
rendered as a deleted relation until corrected and re-tested.

`MCP status: not evaluated`. No MCP write or verification was used for this Activity follow-up, and no product
ticket was submitted.
