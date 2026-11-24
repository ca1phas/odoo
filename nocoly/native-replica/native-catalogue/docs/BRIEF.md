# Brief for the Nocoly docs digests (23 Nov 2026)

**Why:** we are rebuilding Odoo 20's open-source modules (contacts, products, sales, CRM, inventory, purchase, invoicing and more) inside Nocoly HAP SaaS (www.nocoly.com). The Module Owner set the rule: **use native HAP features wherever possible**. That means field types, views, forms, business rules, buttons, workflow nodes, approvals, pages, charts, roles, portal, print templates and integrations. Custom code (code blocks, custom fields, Compute pages) is used only when native truly can't do the job. These digests tell the builders, human or AI, what native features exist, how each is set up and where it stops.

Context, optional: `../../README.md` (programme plan) and `../../00-foundation.md` (wave 0: contacts, products, units, pricelists, currencies, activities).

## How to read your slice

The pages are cached locally (help.nocoly.com, cached on 3 Nov 2026, 359 pages in all). From this folder:

```bash
export PYTHONIOENCODING=utf-8
python -I read_pages.py --list <slice args>                       # the pages of your slice
python -I read_pages.py <slice args> --offset 0 --limit 5         # full text, a few pages at a time
```

Read **every** page in your list, short ones included, using `--offset` / `--limit` to work through them.

## What to write

Write `<your file>.md` in this folder, in English, with these six sections:

1. **Summary**, 10 lines at most: the native capabilities in your slice that matter most for an ERP rebuild.
2. **Capability inventory.** For each feature or setting, give:
   - what it does;
   - its options and values, named as the UI shows them;
   - its limits: counts, sizes, plans or editions, SaaS versus Server, version notes;
   - the source URL.
3. **Odoo rebuild notes.** Which Odoo concepts each feature can replace, for example:
   - many2many tags → multi-select with colours;
   - computed fields → formula or rollup;
   - scheduled actions → a scheduled workflow;
   - chatter → discussion and log;
   - a smart button → a relation or a page.
   Say where native falls short.
4. **Traps** that the docs state or imply.
5. **To verify live:** the doc claims that matter for the build and need a runtime test on Nocoly SaaS.
6. **Coverage:** a table of every page in your slice (URL, title, one-line summary). Every page must appear.

Mark doc statements as docs (cached 3 Nov 2026), not runtime proof. Keep facts and your own inferences apart.

## Rules

- **Read-only.** No hap-cli write commands, no changes to any app.
- Do not use the browser tools; other agents are using them.
- Edit no file other than your own digest.

**Report back:** the file path, the number of pages read (it must equal your slice's count), and the 10 findings most useful for building Odoo natively.
