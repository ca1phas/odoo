# The September replica (Casimir) compared with this programme

Read 23 Nov 2026, read-only.

**Source:** `github.com/ca1phas/odoo`, checked against the local copy `external/ca1phas-odoo`.
- `git ls-remote` showed every GitHub branch head equal to the local remote-tracking ref; nothing was pulled.
- His latest work is branch `19.0` at `be5fa501109`, 23 Sep 2026, 19:21.
- His "ERP Master" app (`<uuid>`, renamed "CRM odoo" on 23 Sep) is **the same app as EMS**. His foundation sheets and our Inventory sit in one app.

## 1. What he built, 15–23 Sep 2026

| Dates | Work | Evidence |
|---|---|---|
| 15–16 Sep | **Phase 1 core**: Contacts, Units & Packagings, Products, Product Variants, Journals and Invoices (first builds by Li Wei), Invoice Lines; then roles | `git log origin/19.0 -- nocoly`, `REVIEWING.md` status table |
| 16–18 Sep | **Six bundles**: Product Categories, Chart of Accounts (87 accounts and every account field), Payment Terms, Countries (251), States (2,102), Taxes (35 Malaysian SST) | same |
| 18 Sep | **Cross-check** of every worksheet against Odoo's live screens: "nothing built is wrong", three cosmetic differences | `CROSSCHECK.md` |
| 21 Sep | **Check of Li Wei's nine CRM worksheets** against Odoo; **UI conformance** pass of the core seven; Orders rebuilt | `worksheets/14-crm-conformance.md`, `15-ui-conformance.md` |
| 22–23 Sep | **Sales:** the 20 Orders buttons (Deliver, Apply Discount, Download, Send, Sign & Accept), Incoterms, Contact Tags, order-to-invoice, invoice numbering, Register Payment, Sales Dashboard (13 charts), demo seed, demo-readiness tracker | commits 22–23 Sep |

**Where it stopped (23 Sep):**
- Worksheets 01–13 are "ready for review"; none was signed off.
- Demo readiness: 34 tasks, 13 done, 1 in progress, 20 to do.
- The CRM check ended with 9 follow-ups, among them: no pipeline board, an invented `Status` field, UTM screens in the wrong menu, and no role settings on the nine sheets.

## 2. Problems he ran into

About 150 platform traps are written up in `nocoly/BUILDING.md`: verified on hap-cli 0.8.31 on 15–17 Sep, with dated additions up to 23 Sep. Grouped:

| # | Problem | Where written | Did we meet it again in Inventory (Nov)? |
|---|---|---|---|
| 1 | **Concurrent edits clobber the layout.** Saving controls replaces the whole field set while the owner edits the same sheets in the browser ("three times in one day"). He moved to version-pinned saves | fork `CLAUDE.md` "Saving controls" | Avoided by only adding fields; still a risk for any shared sheet |
| 2 | **Writes that report success and store nothing,** or store a malformed value (e.g. plain text into a Relation; `add-fields` with an existing control adds a duplicate) | `BUILDING.md` Conventions, Records | Yes: the find-or-create setting that read back off (18 Nov) |
| 3 | **The two read paths disagree** (`record get` vs listing); this produced wrong conclusions twice | fork `CLAUDE.md` "Reading records" | Yes: checkbox values from the list API were unreliable |
| 4 | **Computation timing differs from Odoo:** function defaults only run in the browser; roll-ups need a refresh; formulas go blank when an operand is blank; automations run **on save**, where Odoo fills fields as you type | `BUILDING.md` Formulas; `15-ui-conformance.md` §2 #8–9 | Partly (formula-only fields) |
| 5 | **Rules behave differently on the API:** some validations are not enforced, and picker filters work in the browser only | `BUILDING.md` Rules | Not tested |
| 6 | **Workflow traps:** a search step with an empty filter value fails the whole run; two writes seconds apart race; whether a flow's writes start other flows is the writing flow's own setting; a button flow can only show the user an in-app notice | `BUILDING.md` Workflows | Yes, all three of the first: the ledger sync abort, the strict serial runs, the trigger settings |
| 7 | **Roles:** the V3 role API is limited; roles are tested with HAP's role debugging | `BUILDING.md` Roles | Not touched |
| 8 | **External limits:** sending e-mail was blocked on Nocoly credits | commit "tracker - Send built, blocked on Nocoly credits" (22 Sep) | n/a |
| 9 | **The reference disappeared:** the casimir.odoo.com trial expired on 22 Sep. He had to extract models "before the trial ends" | fork `CLAUDE.md`, `reference/odoo-19.4/` | Could happen to candy99 too |
| 10 | **Review bottleneck:** nothing got signed off; hand-built sheets drifted from Odoo (the CRM findings) | `REVIEWING.md`, `14-crm-conformance.md` | Our Inventory runs also have no formal sign-off |

The traps repeat: we hit 2, 3 and 6 again two months later. His `BUILDING.md` and our Inventory notes are still separate.

## 3. His plan and ours side by side

| Aspect | September (Casimir) | This programme (Nov) |
|---|---|---|
| Odoo reference | casimir.odoo.com (saas~19.4+e, expired 22 Sep) + 19.0 source | candy99 (20.0+e) + official 20.0 source (`catalogue/`) |
| Unit of work | **Worksheet**: a loop of extract → requirements with *Not built now* → re-runnable build script → CLI readback → UI test → review page | **Module**: an approved plan first (12 sections), then the worksheet loop inside it |
| Packaging | One master app; customer copies drop menu groups; menu group = Odoo app | Same (adopted) |
| Cross-module links | "Bridge-pack rule" (an app appends its own fields), found from manifests | Same rule, plus a register that maps Odoo modules to the actual HAP objects |
| User interface | Native HAP only; differences from Odoo recorded as "presentation differences" or "inherent to HAP" | Native HAP plus Compute screens where HAP is weaker, under the rules in `compute-for-ui.md` |
| Order | Core → CRM → Sales → POS → Inventory & Manufacturing → Services → HR → Finance → Marketing → Website → Productivity | Wave 0 foundation and register → 1 gap plans for what exists → 2 Purchase, Manufacturing → 3 Accounting → 4 Services and HR → 5 Website and marketing → Enterprise on demand |
| Enterprise apps | Not measured | Listed (27), planned only on demand |
| Accounting | Journals and Invoices in the core; **double entry left out of Phase 1 by decision** | Accounting depth gets its own wave; stock valuation needs it |
| Effort | 233 worksheets ≈ 1,500 h ≈ 38 weeks (14 Sep; 21 Sep revision 232 / 1,495 h) | Re-based on real build data |
| Done means | Owner sign-off per worksheet | Plan approval, then acceptance tests against candy99 with readback |

**On effort:**
- Form-and-data sheets went fast with AI: 13 sheets in about 4 days, Orders with 20 buttons in 3 days.
- "Built" was not "ready": 20 demo tasks were still open.
- Logic-heavy modules cost far more. Inventory (posting, reservations, routes) has taken two months and is not finished.
- So estimate per module by the amount of logic, not by the number of worksheets.

## 4. What this programme takes from his work

1. **Keep his worksheet loop** as the build phase inside each approved module plan (`README.md` §4).
2. **One shared trap list:**
   - merge our Inventory findings into his `BUILDING.md` approach: the 10-second code block limit, the find-or-create setting, 100-row queries;
   - or index both from the knowledge base;
   - check it before every build.
3. **Capture reference extracts from candy99 early** for each module's models, as he did with `reference/odoo-19.4/`, in case the tenant disappears like casimir did.
4. **Name a reviewer and a time limit for sign-off.** In September nothing was signed off (`README.md` §6).
5. **His UI differences become the first Compute backlog:**
   - Odoo fills fields as you type;
   - list footers show totals;
   - status badges and smart buttons;
   - per-rate tax breakdown;
   - section and note lines.

   Some are fixable in native HAP, e.g. a kanban pipeline board for CRM. Check that before reaching for Compute.
6. **Wave 1 gap plans start from his open lists:** the 20 demo-readiness tasks (Sales), the 9 CRM follow-ups, the unsigned worksheets 01–13, and the four Invoices defects already fixed but needing a UI re-test.
7. **Accounting depth is a known hole.** There is no double entry yet, so stock valuation (the Inventory + Invoicing bridge) cannot be planned until wave 3 settles it.
