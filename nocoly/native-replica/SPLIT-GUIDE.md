# Splitting a module off a customer copy

How to take one or more modules out of a **copy** of Odoo Replica (AI) for a customer, using the register. It is the procedure behind the packaging decision in `README.md` §6.3: one master app holds every module, and a customer gets a copy with the modules it does not buy removed. Each module keeps its own part in `<NN>-<name>-build/SPLIT-GUIDE.md` (CRM: `01-crm-build/SPLIT-GUIDE.md`).

The worked example of the method is the October Inventory removal plan for ERP Master. It lives in the colleague repo at `nocoly/modules/inventory-removal.md` with its manifest; it was never executed. It matches workflows by id + trigger + owning sheet, never by name.

## Roles (`HANDOVER.md` §2)

| Role | Does |
|---|---|
| App Administrator | Makes the copy, deletes objects, owns the split log |
| Module Owner of each removed module | Confirms the remove list and the bridges |
| Module Owner of each retained module | Confirms that the bridge fixes keep their module whole |
| Builder | Fixes the bridges (edits retained workflows, rules, option lists) |
| Reviewer | Runs the checks in step 5 and signs the split off |

Nothing is deleted without the App Administrator's approval: that standing rule applies to every step below.

## Steps

**0. Preconditions** (all must hold)
- The master's register is current: a scan after the last build step, 0 unresolved objects.
- Every object is in a ledger (`<NN>-<name>-build/ids.json`).
- Coverage has 0 OPEN fields.
- **Never prune the master app.**

**1. Copy the master.** Copy the app in HAP and note the copy's app id privately, never in the repo.

**2. Predict.** Scan the copy, then build the prediction for each module to remove:
```bash
ODOO_REPLICA_APP_ID=<copy id> python -I register/register_scan.py
python -I register/register_build.py --prune crm        # writes prune-crm.md in the scan folder
```
`prune-<module>.md` has three parts:
- **Remove**: everything owned by the module and by the modules that depend on it (the Odoo dependency closure).
- **Retain**: what stays.
- **Bridges to fix**: retained objects that point at removed ones.

**3. Decide each bridge**, with the Module Owners:

| Kind of bridge | Usual fix |
|---|---|
| A field the removed module added to a retained sheet (e.g. a reverse tab, a count) | Remove it with the module (it is tagged to the removed module) |
| A retained workflow that reads a removed sheet or field | Edit it: drop the branch or step. If the whole flow only served the removed module, it is owned by that module and goes with it |
| An option the removed module added to a retained option list (e.g. "Leads" in Applies to) | Re-point or archive the records that use it, then delete the option |
| A retained role with rows for removed sheets | The rows go with the sheets; check the role afterwards with Role Debug |
| Records of retained sheets that point at removed records (e.g. activities on leads) | Delete or archive them first, with approval |

**4. Delete, in this order** (references go before what they reference):
1. Workflows of the removed modules: button flows, inner flows, PBPs, scheduled flows. Switch each one off first, then delete it.
2. Buttons on retained sheets that belong to the removed modules.
3. Custom pages and charts of the removed modules.
4. Business rules on retained sheets that use removed fields.
5. Fields the removed modules added to retained sheets. A two-way relation is deleted from its own side, which removes the pair.
6. The removed modules' worksheets: line sheets and sub-tables before their parents.
7. Option sets owned by the removed modules, once no field uses them.
8. Roles owned by the removed modules; menu groups left empty.

**5. Verify** (Reviewer)
- Re-scan the copy. The removed objects are gone; "Bridges to fix" is empty; 0 unresolved.
- Open every retained workflow listed as a bridge. It publishes, and a test run succeeds. A deleted field can leave a flow that looks published and fails at run time, so check the run history.
- Run the smoke tests of every retained module (their plans' §9) on TEST records, then delete them.
- Check the retained roles with Role Debug.

**6. Record.** Write a split log for the customer: modules removed, objects deleted (type, name, id), bridges fixed, checks run, date, and the role that did each step. Keep it with the customer's files, not in this repo.

## Traps

- **Recycle bin:** deleted worksheets and records go to the recycle bin, and deleted rows still block unique values (P26).
- **Two-way relations:** deleting one side removes both.
- **Delete order:** delete workflows first. A flow can still look published after a field it uses is gone; it fails only when it runs.
- **Owners:** every object must have an owner in the register before a split. "Derived" menu groups go only when all their items go.
