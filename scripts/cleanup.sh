#!/usr/bin/env bash
# =============================================================================
# cleanup.sh — Remove a demo deployment (Cloud Run services + BigQuery dataset)
# =============================================================================
# Usage:
#   bash scripts/cleanup.sh --company-slug siriusxm
#   bash scripts/cleanup.sh --company-slug apple --project my-project-id
#
# Deletes the Cloud Run frontend and CA backend services, and drops the
# BigQuery dataset for the specified company. Safe to run multiple times.
# =============================================================================

set -euo pipefail

# --- Defaults ---
PROJECT="${GCP_PROJECT:-firstargolisproject-338816}"
REGION="${GCP_REGION:-us-central1}"
COMPANY_SLUG=""

# --- Parse arguments ---
while [[ $# -gt 0 ]]; do
    case "$1" in
        --company-slug)
            COMPANY_SLUG="$2"
            shift 2
            ;;
        --project)
            PROJECT="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        *)
            echo "Unknown argument: $1"
            echo "Usage: bash scripts/cleanup.sh --company-slug SLUG [--project PROJECT_ID] [--region REGION]"
            exit 1
            ;;
    esac
done

if [[ -z "${COMPANY_SLUG}" ]]; then
    echo "❌ --company-slug is required."
    echo "Usage: bash scripts/cleanup.sh --company-slug siriusxm"
    exit 1
fi

FRONTEND_SERVICE="${COMPANY_SLUG}-frontend"
CA_BACKEND_SERVICE="${COMPANY_SLUG}-ca-backend"
DATASET="${COMPANY_SLUG}_demo"

echo "🧹 Cleaning up demo: ${COMPANY_SLUG}"
echo "   Project: ${PROJECT}"
echo "   Region:  ${REGION}"
echo "─────────────────────────────────────────────"

# --- Delete Cloud Run frontend ---
echo -n "  Deleting Cloud Run service: ${FRONTEND_SERVICE}... "
if gcloud run services delete "${FRONTEND_SERVICE}" \
    --project="${PROJECT}" \
    --region="${REGION}" \
    --quiet 2>/dev/null; then
    echo "✓ deleted"
else
    echo "⚠ not found (may already be deleted)"
fi

# --- Delete Cloud Run CA backend ---
echo -n "  Deleting Cloud Run service: ${CA_BACKEND_SERVICE}... "
if gcloud run services delete "${CA_BACKEND_SERVICE}" \
    --project="${PROJECT}" \
    --region="${REGION}" \
    --quiet 2>/dev/null; then
    echo "✓ deleted"
else
    echo "⚠ not found (may already be deleted)"
fi

# --- Drop BigQuery dataset ---
echo -n "  Dropping BigQuery dataset: ${PROJECT}:${DATASET}... "
if bq rm -r -f -d "${PROJECT}:${DATASET}" 2>/dev/null; then
    echo "✓ deleted"
else
    echo "⚠ not found (may already be deleted)"
fi

# --- Summary ---
echo ""
echo "─────────────────────────────────────────────"
echo "✅ Cleanup complete for: ${COMPANY_SLUG}"
echo ""
echo "Deleted resources:"
echo "  - Cloud Run: ${FRONTEND_SERVICE}"
echo "  - Cloud Run: ${CA_BACKEND_SERVICE}"
echo "  - BigQuery:  ${PROJECT}.${DATASET}"
echo ""
