# Local Odoo 20 Community (reference only)

Set up on 23 Nov 2026 for the Odoo module programme (``).

- **Why:** candy99.odoo.com allows one installed app at a time. This instance has every open-source app installed together, with demo data, so plans can look at screens and flows freely.
- **What it is not:** it has no Enterprise apps (see `module-plans/catalogue/enterprise-only.md`), and it is not for customers or real data.

| | |
|---|---|
| Address | **Back office (the apps): http://127.0.0.1:8069/odoo**, which leads to the sign-in page. The plain address http://127.0.0.1:8069 opens the public website and shop, because Website and eCommerce are installed. This PC only; the port is not exposed to the network |
| Database | `odoo20` |
| Sign-in | `admin` / `admin`: the local test account Odoo creates with a new database. Not a real credential |
| Images | official Docker Hub `odoo:20.0` (or `odoo:20`) and `postgres:16` |
| Apps installed | every open-source app (`APPS` in `setup.sh`), plus Timesheets and common optional modules (`EXTRA` in `add-demo.sh`). Bridges such as `sale_stock` install themselves. 267 modules in all |
| Demo data | Loaded for all 267 modules with `odoo module force-demo` (Odoo 20 does not load it by default). Counts on 23 Nov: 118 contacts, 177 products, 59 sales orders, 104 transfers, 20 purchase orders, 11 manufacturing orders, 20 customer invoices, 131 project tasks |
| Not included | Enterprise-only apps (shown in the Apps menu as uninstallable) and the Malaysian localisation `l10n_my`; the company is generic |
| Setup logs | `setup.log`, `add-demo.log` |

## Use

Docker Desktop must be running.

```bash
docker compose up -d          # start (from this folder)
docker compose stop           # stop, keeps the data
docker compose logs -f odoo   # watch the server log
```

To start again from zero, run `docker compose down -v` (this deletes the local database), then `bash setup.sh`.
