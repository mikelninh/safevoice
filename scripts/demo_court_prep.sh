#!/usr/bin/env bash
# Demo the Court-Prep Agent end-to-end against a running backend.
#
# Usage:
#   ./scripts/demo_court_prep.sh                  # against http://localhost:8000
#   BASE=https://safevoice-vert.vercel.app ./scripts/demo_court_prep.sh
#   CASE_ID=case-001 ./scripts/demo_court_prep.sh
#
# Prints the tool trace + a base64 PDF size, and writes the PDF to /tmp.

set -euo pipefail

BASE="${BASE:-http://localhost:8000}"
CASE_ID="${CASE_ID:-case-001}"
VICTIM_NAME="${VICTIM_NAME:-Demo Person}"
BUNDESLAND="${BUNDESLAND:-BE}"

echo "→ POST ${BASE}/agent/court-prep/${CASE_ID}"
RESPONSE="$(curl -fsS -X POST "${BASE}/agent/court-prep/${CASE_ID}" \
  -H 'Content-Type: application/json' \
  -d "$(printf '{"victim_name": "%s", "bundesland_code": "%s"}' "${VICTIM_NAME}" "${BUNDESLAND}")")"

# Pretty-print without the big base64 blobs.
echo "${RESPONSE}" | python3 -c "
import json, sys, base64
data = json.load(sys.stdin)
artefacts = data.get('artefacts') or {}
pdf_b64 = artefacts.get('strafanzeige_pdf_base64')
emls = artefacts.get('netzdg_emls') or []

# Save the PDF if present
if pdf_b64:
    pdf_bytes = base64.b64decode(pdf_b64)
    out = f'/tmp/strafanzeige-{data[\"agent_run_id\"][:8]}.pdf'
    with open(out, 'wb') as f:
        f.write(pdf_bytes)
    artefacts['strafanzeige_pdf_base64'] = f'<{len(pdf_bytes)} bytes saved to {out}>'

for eml in emls:
    if eml.get('eml_base64'):
        eb = base64.b64decode(eml['eml_base64'])
        out = f'/tmp/{eml[\"filename\"]}'
        with open(out, 'wb') as f:
            f.write(eb)
        eml['eml_base64'] = f'<{len(eb)} bytes saved to {out}>'

print(json.dumps(data, indent=2, ensure_ascii=False))
"

echo ""
echo "→ Artefacts written to /tmp/. To download via Mail: open one of the .eml files."
