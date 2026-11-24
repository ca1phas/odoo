# Where Odoo's facts come from

**Status: draft, 24 Nov 2026.** Replaces the September reference, the live tenant casimir.odoo.com, whose trial
expired on 22 Sep (`CLAUDE.md`). Every builder sets up both references below before reviewing or building a module.

## Two references, two jobs

| Reference | Use it for | Limits |
|---|---|---|
| **Local Odoo 20 Community** (`tools/odoo20-local/`) | Behaviour read from the source; demo data; every open-source app installed together, so flows across apps (Sales → Inventory → Invoicing) can be followed; exact values by read-only SQL | No Enterprise-only apps; a generic company; screens can differ slightly from Odoo Online |
| **An Odoo Online instance** (20.x Enterprise) | The current screens; Enterprise-only features; how the SaaS behaves | On the free plan only **one app** can be installed per database; installing a second asks for a subscription. Switching apps means uninstalling the current one, **which deletes its data**, then installing the next. A trial database has every app, but only for its trial period |

## Rules for the online instance

- **Never subscribe, upgrade or enter payment details.**
- **One app at a time.** Before switching to another app, capture what the plans need (screens, field lists,
  settings) into `reference/`, then uninstall and install the next. Nothing on the instance is permanent.
- **Each Module Owner keeps the instance for their module**, so the app they need stays installed. Write which
  person holds which instance in a private note, not in this public repo.
- **Flows that need several apps together** (for example a sale that reserves stock and is invoiced): use the local
  Odoo 20, or a trial database for screens only Enterprise has, and capture them before the trial ends.
- **No real company or customer data.** `TEST …` records only.

## Citing a fact

Every fact in a worksheet document or a decision says where it came from:

| Source | Cite as |
|---|---|
| Local Odoo 20 source or database | `odoo20-local`, with the file and method, or the table |
| An Odoo Online instance | `online 20.x`, with the date |
| The September captures | `odoo-19.4 extract` (`reference/odoo-19.4/`) |

Where two sources disagree, keep both in the document and say which one the build follows.

## Versions

The September build followed saas~19.4; the references above are Odoo 20. Odoo 20 differs in places (for example,
in CRM, Convert to Opportunity no longer opens a wizard). Do not chase every difference in finished worksheets:
record it in the module's review, and fix what changes how the business works.
