# Local Odoo 20 Community (reference only)

A local Odoo 20 with **every open-source app installed together**, plus demo data. Use it to read Odoo's behaviour
from its source, look at screens and flows, and query exact values, without the one-app limit of a free online
instance. How it fits with the online reference: `../../REFERENCES.md`.

**Not for real data.** It runs on your computer only (the port is bound to 127.0.0.1); the passwords in these files
are local test values.

## Set it up (once, about 30–60 minutes)

1. Install and start **Docker Desktop**.
2. Open a bash shell in this folder (on Windows: Git Bash).
3. Run `bash setup.sh`. It pulls the official images `odoo:20.0` and `postgres:16`, creates the database `odoo20`
   with every open-source app (their bridges install themselves) and starts the server.
4. Run `bash add-demo.sh`. It adds Timesheets and some common optional modules, then loads demo data for every
   installed module (Odoo 20 does not load it by default).

Check: http://127.0.0.1:8069/odoo shows the sign-in page. Sign in with `admin` / `admin`, the local account
Odoo creates with a new database.

## What you get

| | |
|---|---|
| Back office | http://127.0.0.1:8069/odoo (the plain address opens the public website, because Website is installed) |
| Database | `odoo20` |
| Modules | 267 installed: every open-source app (`APPS` in `setup.sh`), the extras in `add-demo.sh`, and the bridges |
| Demo data (counts on the first install, 23 Nov 2026) | 118 contacts, 177 products, 59 sales orders, 104 transfers, 20 purchase orders, 11 manufacturing orders, 20 customer invoices, 131 project tasks |
| Not included | Enterprise-only apps and the Malaysian localisation `l10n_my`; the company is generic |

## Use

```bash
docker compose up -d          # start
docker compose stop           # stop, keeps the data
docker compose logs -f odoo   # server log
```

- **Odoo's source** is inside the container: `/usr/lib/python3/dist-packages/odoo/addons/<module>`. Read it with
  `docker compose exec odoo cat /usr/lib/python3/dist-packages/odoo/addons/crm/models/crm_lead.py`.
- **Read-only queries:** `docker compose exec db psql -U odoo -d odoo20`. Useful tables: `ir_model_fields`
  (fields, types, owner module), `ir_model_data` (which module created each demo row), `ir_module_module`
  (installed modules). Odoo 20 keeps access rights and record rules in each module's `security/ir.access.csv`.
- **Start again from zero:** `docker compose down -v` (deletes the local database), then `bash setup.sh` and
  `bash add-demo.sh`.
