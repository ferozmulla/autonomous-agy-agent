"""Main CLI entry point for Agent-Built Demos.

Usage:
    python src/launch_demo.py --company "SiriusXM"
    python src/launch_demo.py --company "Apple" --project my-project-id

This script orchestrates two Managed Agents in parallel:
  1. Page Builder — builds and deploys a React dashboard to Cloud Run.
  2. Data Generator — creates a synthetic BigQuery dataset.
"""

from __future__ import annotations

import os
import sys
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

# Suppress noisy ADC warning about end-user credentials lacking a quota project.
# This warning is informational and doesn't affect functionality.
warnings.filterwarnings("ignore", message="Your application has authenticated using end user credentials")

# Ensure the project root is on sys.path so `src` is importable
# regardless of how the script is invoked (direct, -m, or installed).
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Auto-load .env file from project root (no external dependency needed)
_env_file = Path(_PROJECT_ROOT) / ".env"
if _env_file.exists():
    with open(_env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                key, value = key.strip(), value.strip()
                # Only set if not already in environment (env vars take precedence)
                if key and key not in os.environ:
                    os.environ[key] = value

import click
from google import genai

from src.config import (
    DEFAULT_GCP_PROJECT,
    DEFAULT_GCP_REGION,
    slugify,
    get_dataset_name,
    get_frontend_service_name,
)
from src.output import (
    console,
    print_agent_error,
    print_agent_start,
    print_agent_success,
    print_banner,
    print_error,
    print_info,
    print_separator,
    print_success,
)
from src.result_parser import (
    extract_frontend_url,
    is_agent_success,
)


def _create_client() -> genai.Client:
    """Create and return a Gemini API client.

    Reads ``GOOGLE_API_KEY`` from the environment. Exits with an actionable
    error if the key is not set.

    Returns:
        An initialized ``genai.Client``.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print_error(
            "CLI",
            "GOOGLE_API_KEY environment variable is not set.\n"
            "         Copy .env.example to .env and add your API key:\n"
            "           cp .env.example .env\n"
            "           # Then edit .env and set GOOGLE_API_KEY=your-key",
        )
        sys.exit(1)

    return genai.Client(api_key=api_key)


def _run_data_generator(
    client: genai.Client,
    company: str,
    company_slug: str,
    project: str,
) -> dict[str, Any]:
    """Run the Data Generator agent and return results.

    Args:
        client: Gemini API client.
        company: Human-readable company name.
        company_slug: Slugified company name.
        project: GCP project ID.

    Returns:
        A dict with keys: agent, result, success.
    """
    from src.agents.data_generator import invoke_data_generator

    result = invoke_data_generator(client, company, company_slug, project)
    return {
        "agent": "Data Generator",
        "result": result,
        "success": result.status.upper() == "SUCCESS",
    }


def _run_page_builder(
    client: genai.Client,
    company: str,
    ticker: str | None,
    company_slug: str,
    project: str,
    region: str,
) -> dict[str, Any]:
    """Run the Page Builder agent and return results.

    Args:
        client: Gemini API client.
        company: Human-readable company name.
        ticker: Optional stock ticker symbol.
        company_slug: Slugified company name.
        project: GCP project ID.
        region: GCP region for Cloud Run.

    Returns:
        A dict with keys: agent, result, success.
    """
    from src.agents.page_builder import invoke_page_builder

    result = invoke_page_builder(
        client, company, ticker, company_slug, project, region
    )
    return {
        "agent": "Page Builder",
        "result": result,
        "success": result.status.upper() == "SUCCESS",
    }


@click.command()
@click.option(
    "--company",
    required=True,
    help="Company name to build the demo for (e.g., 'SiriusXM').",
)
@click.option(
    "--ticker",
    default=None,
    help="Stock ticker symbol (auto-detected if not provided).",
)
@click.option(
    "--project",
    default=DEFAULT_GCP_PROJECT,
    show_default=True,
    help="GCP project ID for BigQuery and Cloud Run.",
)
@click.option(
    "--region",
    default=DEFAULT_GCP_REGION,
    show_default=True,
    help="GCP region for Cloud Run deployments.",
)
def main(company: str, ticker: str | None, project: str, region: str) -> None:
    """Agent-Built Demos — Generate a company-specific AI demo.

    Spawns two Managed Agents in parallel to create a deployed dashboard
    and synthetic dataset for the given company.
    """
    # --- Setup ---
    company_slug = slugify(company)
    dataset_name = get_dataset_name(company_slug)

    print_banner(company)
    print_info(f"Company slug: {company_slug}")
    print_info(f"Dataset: {project}.{dataset_name}")
    print_info(f"Region: {region}")
    print_separator()

    # --- Create Gemini API client ---
    client = _create_client()

    # --- Dispatch agents in parallel ---
    print_agent_start("Page Builder")
    print_agent_start("Data Generator")
    print_separator()

    results: dict[str, dict[str, Any]] = {}

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(
                _run_data_generator, client, company, company_slug, project
            ): "Data Generator",
            executor.submit(
                _run_page_builder,
                client,
                company,
                ticker,
                company_slug,
                project,
                region,
            ): "Page Builder",
        }

        for future in as_completed(futures):
            agent_name = futures[future]
            try:
                agent_result = future.result()
                results[agent_name] = agent_result

                if agent_result["success"]:
                    result_obj = agent_result["result"]

                    if agent_name == "Data Generator":
                        ds = getattr(result_obj, "dataset_name", None) or dataset_name
                        print_agent_success(agent_name, f"Dataset created: {ds}")
                    else:
                        # Page Builder
                        url = getattr(result_obj, "frontend_url", None)
                        if url:
                            print_agent_success(agent_name, f"Frontend deployed: {url}")
                        else:
                            print_agent_success(agent_name, "Frontend deployed to Cloud Run")

                        ca_url = getattr(result_obj, "ca_backend_url", None)
                        if ca_url:
                            print_agent_success(agent_name, f"CA backend deployed: {ca_url}")
                else:
                    result_obj = agent_result.get("result")
                    error_msg = getattr(result_obj, "error", None)
                    # If no explicit error, try to extract from output_text
                    if not error_msg:
                        output = getattr(result_obj, "output_text", "")
                        if output:
                            import re
                            err_match = re.search(r"ERROR:\s*(.+)", output)
                            if err_match:
                                error_msg = err_match.group(1).strip()[:200]
                            else:
                                error_msg = f"Agent output (first 200 chars): {output[:200]}"
                        else:
                            error_msg = "No output produced"
                    print_agent_error(agent_name, f"Failed: {error_msg}")

            except Exception as exc:
                results[agent_name] = {
                    "agent": agent_name,
                    "result": None,
                    "success": False,
                }
                print_agent_error(agent_name, f"Failed: {exc!s:.200}")

    # --- Final output ---
    print_separator()

    all_succeeded = all(r.get("success", False) for r in results.values())

    if all_succeeded:
        # Try to extract the frontend URL from the Page Builder result
        pb_result = results.get("Page Builder", {}).get("result")
        frontend_url = None
        if pb_result:
            frontend_url = getattr(pb_result, "frontend_url", None)
            if not frontend_url and hasattr(pb_result, "output_text"):
                frontend_url = extract_frontend_url(pb_result.output_text)

        if frontend_url:
            print_success(frontend_url)
        else:
            print_info(
                "Both agents completed successfully, but no frontend URL was "
                "extracted. Check the Page Builder output for the Cloud Run URL."
            )

        # Generate demo prompts from the actual dataset schema
        from src.demo_prompts import generate_demo_prompts
        from src.output import print_demo_prompts

        demo_prompts = generate_demo_prompts(project, dataset_name, company)
        if demo_prompts:
            print_demo_prompts(demo_prompts)
    else:
        failed_agents = [
            name for name, r in results.items() if not r.get("success", False)
        ]
        print_error(
            "CLI",
            f"Demo generation failed. Failed agents: {', '.join(failed_agents)}. "
            "Check the error messages above for details.",
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
