"""Parse structured output from Managed Agent interaction results.

Each agent prints a well-defined output block at the end of its run.
This module extracts key fields (URLs, dataset names, milestones, status)
from the raw ``output_text`` so the CLI can present clean results.
"""

from __future__ import annotations

import re


def extract_cloud_run_url(output_text: str) -> str | None:
    """Extract the first Cloud Run URL from agent output text.

    Looks for URLs matching the pattern ``https://*.run.app``.

    Args:
        output_text: The raw output text from the Managed Agent interaction.

    Returns:
        The first Cloud Run URL found, or ``None`` if no URL is present.
    """
    match = re.search(r"https://[a-zA-Z0-9._-]+\.run\.app", output_text)
    return match.group(0) if match else None


def extract_all_cloud_run_urls(output_text: str) -> list[str]:
    """Extract all Cloud Run URLs from agent output text.

    Args:
        output_text: The raw output text from the Managed Agent interaction.

    Returns:
        A list of all Cloud Run URLs found (may be empty).
    """
    return re.findall(r"https://[a-zA-Z0-9._-]+\.run\.app", output_text)


def extract_dataset_name(output_text: str) -> str | None:
    """Extract the BigQuery dataset identifier from Data Generator output.

    Looks for the ``DATASET:`` marker in the structured output block.
    Expected format: ``DATASET: project_id.dataset_name``

    Args:
        output_text: The raw output text from the Data Generator interaction.

    Returns:
        The full dataset reference (e.g., ``project.dataset_name``), or ``None``.
    """
    match = re.search(r"DATASET:\s*(\S+)", output_text)
    return match.group(1) if match else None


def extract_status(output_text: str) -> str | None:
    """Extract the STATUS field from the structured output block.

    Args:
        output_text: The raw output text from a Managed Agent interaction.

    Returns:
        The status string (e.g., "SUCCESS", "FAILED"), or ``None``.
    """
    match = re.search(r"STATUS:\s*(\w+)", output_text)
    return match.group(1) if match else None


def extract_milestones(output_text: str) -> list[str]:
    """Extract milestone lines from agent output.

    Milestones are lines containing checkmarks (✓, ✅) or cross marks (✗, ❌).

    Args:
        output_text: The raw output text from a Managed Agent interaction.

    Returns:
        A list of milestone strings found in the output.
    """
    milestones: list[str] = []
    for line in output_text.splitlines():
        stripped = line.strip()
        if any(marker in stripped for marker in ("✓", "✗", "✅", "❌", "SUCCESS", "FAILED")):
            milestones.append(stripped)
    return milestones


def extract_table_info(output_text: str) -> list[dict[str, str]]:
    """Extract table names and row counts from Data Generator output.

    Parses lines matching: ``  - table_name: NNN rows``

    Args:
        output_text: The raw output text from the Data Generator interaction.

    Returns:
        A list of dicts with ``name`` and ``row_count`` keys.
    """
    tables: list[dict[str, str]] = []
    for match in re.finditer(r"-\s+([\w.]+):\s*(\d+)\s*rows", output_text):
        tables.append({"name": match.group(1), "row_count": match.group(2)})
    return tables


def extract_frontend_url(output_text: str) -> str | None:
    """Extract the frontend Cloud Run URL from Page Builder output.

    Looks for a URL containing 'frontend' in the hostname.

    Args:
        output_text: The raw output text from the Page Builder interaction.

    Returns:
        The frontend URL, or falls back to the first Cloud Run URL found.
    """
    urls = extract_all_cloud_run_urls(output_text)
    for url in urls:
        if "frontend" in url:
            return url
    # Fallback: return the first URL if no "frontend" URL found
    return urls[0] if urls else None


def extract_ca_backend_url(output_text: str) -> str | None:
    """Extract the CA backend Cloud Run URL from Page Builder output.

    Looks for a URL containing 'ca-backend' in the hostname.

    Args:
        output_text: The raw output text from the Page Builder interaction.

    Returns:
        The CA backend URL, or ``None``.
    """
    urls = extract_all_cloud_run_urls(output_text)
    for url in urls:
        if "ca-backend" in url:
            return url
    return None


def is_agent_success(output_text: str) -> bool:
    """Determine if an agent's output indicates success.

    Checks for the ``STATUS: SUCCESS`` marker in the structured output.
    Falls back to checking for the presence of key success indicators.

    Args:
        output_text: The raw output text from a Managed Agent interaction.

    Returns:
        ``True`` if the output indicates success, ``False`` otherwise.
    """
    status = extract_status(output_text)
    if status:
        return status.upper() == "SUCCESS"
    # Fallback heuristics
    has_url = extract_cloud_run_url(output_text) is not None
    has_dataset = extract_dataset_name(output_text) is not None
    return has_url or has_dataset
