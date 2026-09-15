#!/usr/bin/env bash
# Prepare a machine to build the Nocoly app against this Odoo checkout.
#   HAP_TOKEN     Nocoly personal access token (pat_…)
#   ODOO_LOGIN    Odoo login email        — only needed to read the reference tenant
#   ODOO_API_KEY  Odoo ▸ My Profile ▸ Account Security ▸ New API Key
set -euo pipefail

python3 -m venv ~/.hap-venv
~/.hap-venv/bin/pip install --quiet --upgrade pip
~/.hap-venv/bin/pip install --quiet "hap-cli==0.8.31"   # the version the build scripts were verified on
mkdir -p ~/.local/bin && ln -sf ~/.hap-venv/bin/hap ~/.local/bin/hap
export PATH="$HOME/.local/bin:$PATH"

if [ -z "${HAP_TOKEN:-}" ]; then
  echo "HAP_TOKEN not set — export it, then re-run." >&2
else
  # The server argument is required. Without 'nocoly' the CLI targets
  # www.mingdao.com and fails with a misleading "token has expired".
  hap auth login nocoly --token "$HAP_TOKEN" --profile nocoly
  hap auth whoami || true
fi

echo
echo "Plan:      nocoly/plan/phases.json"
echo "Artifacts: nocoly/artifacts/*.html  (open in a browser)"
echo "Tools:     python3 nocoly/tools/manifest_graph.py"
