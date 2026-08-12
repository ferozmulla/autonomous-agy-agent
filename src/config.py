"""Central configuration constants and utility functions for Agent-Built Demos.

This module contains all default values, naming patterns, path constants,
and the slugify function used throughout the CLI orchestrator.
"""

from __future__ import annotations

import os
import re
from pathlib import Path


# ---------------------------------------------------------------------------
# GCP Defaults (overridable via CLI flags and environment variables)
# ---------------------------------------------------------------------------

DEFAULT_GCP_PROJECT: str = os.environ.get(
    "GCP_PROJECT", "firstargolisproject-338816"
)
DEFAULT_GCP_REGION: str = os.environ.get("GCP_REGION", "us-central1")

# ---------------------------------------------------------------------------
# Managed Agent Configuration
# ---------------------------------------------------------------------------

#: Base agent identifier for Antigravity Managed Agents.
BASE_AGENT_ID: str = "antigravity-preview-05-2026"

#: Model to use for all Gemini API / ADK interactions.
GEMINI_MODEL: str = "gemini-3.6-flash"

#: Inference region for Gemini API calls (global — not tied to resource region).
GEMINI_INFERENCE_REGION: str = "global"

# ---------------------------------------------------------------------------
# Cloud Run Service Naming
# ---------------------------------------------------------------------------

FRONTEND_SERVICE_PATTERN: str = "{slug}-frontend"
CA_BACKEND_SERVICE_PATTERN: str = "{slug}-ca-backend"

# ---------------------------------------------------------------------------
# BigQuery Naming
# ---------------------------------------------------------------------------

DATASET_PATTERN: str = "{slug}_demo"

# ---------------------------------------------------------------------------
# Path Constants (relative to project root)
# ---------------------------------------------------------------------------

#: Resolve the project root directory (two levels up from this file).
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

PROMPTS_DIR: Path = PROJECT_ROOT / "prompts"
TEMPLATES_DIR: Path = PROJECT_ROOT / "templates" / "page-builder"
FRONTEND_TEMPLATES_DIR: Path = TEMPLATES_DIR / "frontend"
CA_BACKEND_TEMPLATES_DIR: Path = TEMPLATES_DIR / "ca-backend"
SKILLS_DIR: Path = PROJECT_ROOT / "skills"
DATA_GENERATOR_SKILL_PATH: Path = (
    SKILLS_DIR / "analytics-data-generator" / "SKILL.md"
)

# Prompt file paths
PAGE_BUILDER_PROMPT_PATH: Path = PROMPTS_DIR / "page_builder_system.md"
DATA_GENERATOR_PROMPT_PATH: Path = PROMPTS_DIR / "data_generator_system.md"
CA_AGENT_PROMPT_TEMPLATE_PATH: Path = PROMPTS_DIR / "ca_agent_system_template.md"


def slugify(company_name: str) -> str:
    """Convert a company name to a snake_case slug safe for BigQuery and Cloud Run.

    Lowercases the input, replaces any non-alphanumeric character with an
    underscore, collapses consecutive underscores, and strips leading/trailing
    underscores.

    Args:
        company_name: The human-readable company name (e.g., "JPMorgan Chase").

    Returns:
        A snake_case slug (e.g., "jpmorgan_chase").

    Examples:
        >>> slugify("SiriusXM")
        'siriusxm'
        >>> slugify("JPMorgan Chase")
        'jpmorgan_chase'
        >>> slugify("AT&T")
        'at_t'
        >>> slugify("  Procter & Gamble  ")
        'procter_gamble'
    """
    slug = company_name.lower().strip()
    # Replace any non-alphanumeric character (including hyphens) with underscore
    slug = re.sub(r"[^a-z0-9]", "_", slug)
    # Collapse consecutive underscores
    slug = re.sub(r"_+", "_", slug)
    # Strip leading/trailing underscores
    slug = slug.strip("_")
    return slug


def get_dataset_name(company_slug: str) -> str:
    """Return the BigQuery dataset name for a given company slug.

    Args:
        company_slug: The slugified company name.

    Returns:
        Dataset name in the format ``{slug}_demo``.
    """
    return DATASET_PATTERN.format(slug=company_slug)


def get_frontend_service_name(company_slug: str) -> str:
    """Return the Cloud Run frontend service name for a given company slug.

    Args:
        company_slug: The slugified company name.

    Returns:
        Service name in the format ``{slug}-frontend``.
    """
    return FRONTEND_SERVICE_PATTERN.format(slug=company_slug)


def get_ca_backend_service_name(company_slug: str) -> str:
    """Return the Cloud Run CA backend service name for a given company slug.

    Args:
        company_slug: The slugified company name.

    Returns:
        Service name in the format ``{slug}-ca-backend``.
    """
    return CA_BACKEND_SERVICE_PATTERN.format(slug=company_slug)


# Service account for Agent-Built Demos (has BigQuery + Cloud Run permissions)
DEMO_SERVICE_ACCOUNT: str = os.environ.get(
    "DEMO_SERVICE_ACCOUNT",
    "agent-demo-builder@firstargolisproject-338816.iam.gserviceaccount.com",
)


def get_gcp_access_token() -> str | None:
    """Get a fresh GCP access token by impersonating the demo service account.

    Uses the caller's Application Default Credentials to impersonate
    the dedicated service account that has BigQuery and Cloud Run permissions.
    This avoids needing to manage key files while ensuring the sandbox
    gets a token with the right IAM roles.

    Returns:
        A bearer access token string, or None if credentials are unavailable.
    """
    try:
        import google.auth
        import google.auth.transport.requests
        from google.auth import impersonated_credentials

        # Get the caller's base credentials (user ADC)
        source_credentials, _ = google.auth.default()
        source_credentials.refresh(google.auth.transport.requests.Request())

        # Impersonate the demo service account
        target_credentials = impersonated_credentials.Credentials(
            source_credentials=source_credentials,
            target_principal=DEMO_SERVICE_ACCOUNT,
            target_scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        target_credentials.refresh(google.auth.transport.requests.Request())
        return target_credentials.token
    except Exception:
        # SA impersonation not available — silently fall back to direct ADC token
        try:
            import google.auth
            import google.auth.transport.requests

            credentials, _ = google.auth.default(
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            credentials.refresh(google.auth.transport.requests.Request())
            return credentials.token
        except Exception:
            return None


def get_network_allowlist() -> dict | None:
    """Build the environment network allowlist with GCP auth header injection.

    Configures the remote sandbox to allow outbound traffic to GCP APIs
    and injects the service account's access token via the Authorization header.

    Returns:
        A network config dict for the environment, or None if no token available.
    """
    token = get_gcp_access_token()
    if not token:
        return None

    return {
        "allowlist": [
            {
                "domain": "*",
                "transform": {"Authorization": f"Bearer {token}"},
            },
        ],
    }
