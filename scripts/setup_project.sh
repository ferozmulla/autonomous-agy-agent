#!/usr/bin/env bash
# =============================================================================
# setup_project.sh — One-time GCP project setup for Agent-Built Demos
# =============================================================================
# Usage:
#   bash scripts/setup_project.sh [--project PROJECT_ID] [--region REGION]
#
# This script enables required GCP APIs, configures gcloud defaults,
# and verifies authentication. Run once per GCP project.
# =============================================================================

set -euo pipefail

# --- Defaults ---
PROJECT="${GCP_PROJECT:-firstargolisproject-338816}"
REGION="${GCP_REGION:-us-central1}"

# --- Parse arguments ---
while [[ $# -gt 0 ]]; do
    case "$1" in
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
            echo "Usage: bash scripts/setup_project.sh [--project PROJECT_ID] [--region REGION]"
            exit 1
            ;;
    esac
done

echo "🔧 Setting up GCP project for Agent-Built Demos"
echo "   Project: ${PROJECT}"
echo "   Region:  ${REGION}"
echo "─────────────────────────────────────────────"

# --- Check gcloud is installed ---
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed."
    echo "   Install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi
echo "✓ gcloud CLI found: $(gcloud version 2>/dev/null | head -1)"

# --- Check authentication ---
ACCOUNT=$(gcloud auth list --filter="status=ACTIVE" --format="value(account)" 2>/dev/null || true)
if [[ -z "${ACCOUNT}" ]]; then
    echo "❌ No active gcloud authentication."
    echo "   Run: gcloud auth login"
    exit 1
fi
echo "✓ Authenticated as: ${ACCOUNT}"

# --- Set project and region defaults ---
gcloud config set project "${PROJECT}" --quiet
gcloud config set run/region "${REGION}" --quiet
echo "✓ Project set to: ${PROJECT}"
echo "✓ Region set to:  ${REGION}"

# --- Enable required APIs ---
echo ""
echo "Enabling required GCP APIs..."

APIS=(
    "run.googleapis.com"
    "bigquery.googleapis.com"
    "cloudbuild.googleapis.com"
    "artifactregistry.googleapis.com"
)

for api in "${APIS[@]}"; do
    echo -n "  Enabling ${api}... "
    if gcloud services enable "${api}" --project="${PROJECT}" --quiet 2>/dev/null; then
        echo "✓"
    else
        echo "⚠ (may already be enabled or insufficient permissions)"
    fi
done

# --- Verify BigQuery access ---
echo ""
echo -n "Verifying BigQuery access... "
if bq ls --project_id="${PROJECT}" &>/dev/null; then
    echo "✓"
else
    echo "⚠ Could not list BigQuery datasets. Check IAM permissions."
fi

# --- Verify Cloud Run access ---
echo -n "Verifying Cloud Run access... "
if gcloud run services list --project="${PROJECT}" --region="${REGION}" --limit=1 &>/dev/null; then
    echo "✓"
else
    echo "⚠ Could not list Cloud Run services. Check IAM permissions."
fi

# --- Application Default Credentials ---
echo ""
echo -n "Checking Application Default Credentials... "
if gcloud auth application-default print-access-token &>/dev/null; then
    echo "✓"
else
    echo "⚠ ADC not configured. Run: gcloud auth application-default login"
fi

# --- Summary ---
echo ""
echo "─────────────────────────────────────────────"
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Copy .env.example to .env and set your GOOGLE_API_KEY"
echo "  2. Run: python src/launch_demo.py --company \"Apple\""
echo ""
