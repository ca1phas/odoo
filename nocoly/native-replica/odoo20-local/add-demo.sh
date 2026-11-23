#!/usr/bin/env bash
# Follow-up to setup.sh (23 Nov 2026): Odoo 20 does not load demo data by default.
# 1. add Timesheets and common optional modules, 2. load demo data for every installed module, 3. restart and count.
set -u
export MSYS_NO_PATHCONV=1
cd "$(dirname "$0")"
log() { echo "[$(date '+%H:%M:%S')] $*"; }
CONF="$(pwd -W 2>/dev/null || pwd)/odoo-cli.conf"

docker compose stop odoo
EXTRA="hr_timesheet,product_expiry,stock_landed_costs,stock_dropshipping,mrp_subcontracting,purchase_requisition,sale_margin,sale_loyalty"
log "installing extra modules: $EXTRA"
docker compose run --rm odoo odoo -d odoo20 -i "$EXTRA" --stop-after-init --log-level=warn 2>&1 | tail -n 20
log "extra modules finished with exit code ${PIPESTATUS[0]}"

log "loading demo data for every installed module (force-demo)"
docker compose run --rm --entrypoint odoo -v "$CONF:/etc/odoo/cli.conf:ro" odoo \
  module force-demo -c /etc/odoo/cli.conf -d odoo20 2>&1 | grep -v " INFO " | tail -n 30
log "force-demo finished with exit code ${PIPESTATUS[0]}"

docker compose up -d odoo
sleep 10
code=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8069/web/login)
log "Odoo web login page answers HTTP $code"
docker compose exec -T db psql -U odoo -d odoo20 -t -A -F' | ' \
  -c "select 'installed', count(*), 'with demo', count(*) filter (where demo) from ir_module_module where state='installed';" \
  -c "select 'partners', (select count(*) from res_partner), 'products', (select count(*) from product_template), 'sale orders', (select count(*) from sale_order), 'transfers', (select count(*) from stock_picking), 'POs', (select count(*) from purchase_order), 'MOs', (select count(*) from mrp_production), 'invoices', (select count(*) from account_move where move_type like 'out_%'), 'tasks', (select count(*) from project_task);"
