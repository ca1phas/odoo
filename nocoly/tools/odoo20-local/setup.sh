#!/usr/bin/env bash
# One-time setup of the local Odoo 20 Community reference instance.
# 1. wait for Docker Desktop, 2. pull the official images, 3. create database "odoo20"
# with every open-source app (and their bridges, which install themselves), 4. start the server.
set -u
cd "$(dirname "$0")"
log() { echo "[$(date '+%H:%M:%S')] $*"; }

log "waiting for the Docker engine"
for i in $(seq 1 60); do
  if docker info >/dev/null 2>&1; then break; fi
  sleep 5
done
docker info >/dev/null 2>&1 || { log "Docker engine did not start within 5 minutes"; exit 1; }
log "Docker engine is up: $(docker info --format '{{.ServerVersion}}')"

IMAGE=""
for tag in odoo:20.0 odoo:20; do
  log "trying $tag"
  if docker pull "$tag"; then IMAGE="$tag"; break; fi
done
[ -n "$IMAGE" ] || { log "no official Odoo 20 image found on Docker Hub (tried odoo:20.0, odoo:20); stopping"; exit 2; }
export ODOO_IMAGE="$IMAGE"
docker pull postgres:16 || { log "postgres:16 pull failed"; exit 3; }
log "images: $IMAGE and postgres:16"
docker image inspect "$IMAGE" --format 'odoo image size {{.Size}} bytes, created {{.Created}}'
docker run --rm "$IMAGE" odoo --version 2>&1 | tail -n 1

APPS="contacts,calendar,mail,crm,sale_management,account,stock,purchase,mrp,repair,maintenance,point_of_sale,pos_restaurant,project,project_todo,hr,hr_attendance,hr_expense,hr_holidays,hr_recruitment,hr_skills,fleet,lunch,survey,mass_mailing,mass_mailing_sms,marketing_card,im_livechat,website,website_sale,website_event,website_slides,website_hr_recruitment,website_blog,website_forum,data_recycle"
DEMO_FLAG=""
if docker run --rm "$IMAGE" odoo --help 2>/dev/null | grep -q -- "--with-demo"; then DEMO_FLAG="--with-demo"; fi
log "demo data flag: ${DEMO_FLAG:-default}"

docker compose up -d db
sleep 8
log "creating database odoo20 with all open-source apps (this takes a while)"
docker compose run --rm odoo odoo -d odoo20 -i "$APPS" $DEMO_FLAG --load-language=en_US --stop-after-init --log-level=warn 2>&1 | tail -n 40
rc=${PIPESTATUS[0]}
log "database init finished with exit code $rc"
docker compose up -d odoo
sleep 10
code=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8069/web/login)
log "Odoo web login page answers HTTP $code at http://127.0.0.1:8069"
docker compose ps
