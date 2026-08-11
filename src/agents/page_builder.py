"""Page Builder agent invocation module.

Reads the system instruction and all frontend template files, assembles
the interaction configuration with inline environment sources, and calls
the Gemini API to create a Managed Agent interaction that builds and
deploys the React dashboard.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from google import genai

from src.config import (
    BASE_AGENT_ID,
    CA_BACKEND_TEMPLATES_DIR,
    FRONTEND_TEMPLATES_DIR,
    GEMINI_MODEL,
    PAGE_BUILDER_PROMPT_PATH,
    CA_AGENT_PROMPT_TEMPLATE_PATH,
    get_ca_backend_service_name,
    get_dataset_name,
    get_frontend_service_name,
    get_network_allowlist,
)


@dataclass
class PageBuilderResult:
    """Structured result from a Page Builder interaction.

    Attributes:
        output_text: The raw output text from the Managed Agent.
        frontend_url: The deployed frontend Cloud Run URL, if found.
        ca_backend_url: The deployed CA backend Cloud Run URL, if found.
        status: The reported status ("SUCCESS", "FAILED", or "UNKNOWN").
        error: Error message, if the interaction failed.
    """

    output_text: str = ""
    frontend_url: str | None = None
    ca_backend_url: str | None = None
    status: str = "UNKNOWN"
    error: str | None = None


def _load_prompt(
    company: str,
    ticker: str | None,
    company_slug: str,
    project: str,
    region: str,
) -> str:
    """Load and parameterize the Page Builder system instruction.

    Args:
        company: The human-readable company name.
        ticker: Optional stock ticker symbol.
        company_slug: The slugified company name.
        project: The GCP project ID.
        region: The GCP region for Cloud Run.

    Returns:
        The fully parameterized system instruction string.
    """
    raw_prompt = PAGE_BUILDER_PROMPT_PATH.read_text(encoding="utf-8")
    dataset_name = get_dataset_name(company_slug)

    prompt = raw_prompt.replace("{{PROJECT_ID}}", project)
    prompt = prompt.replace("{{REGION}}", region)
    prompt = prompt.replace("{{COMPANY_SLUG}}", company_slug)
    prompt = prompt.replace("{{DATASET_NAME}}", dataset_name)

    return prompt


def _build_user_message(
    company: str,
    ticker: str | None,
    company_slug: str,
    project: str,
    region: str,
) -> str:
    """Build the user message that kicks off page building.

    Args:
        company: The human-readable company name.
        ticker: Optional stock ticker symbol.
        company_slug: The slugified company name.
        project: The GCP project ID.
        region: The GCP region.

    Returns:
        The user message string.
    """
    ticker_info = f" (ticker: {ticker})" if ticker else ""
    dataset_name = get_dataset_name(company_slug)
    frontend_service = get_frontend_service_name(company_slug)

    return (
        f"Build and deploy a Pastel Terminal dashboard for **{company}**{ticker_info}.\n\n"
        f"- **Project ID:** `{project}`\n"
        f"- **Region:** `{region}`\n"
        f"- **Company slug:** `{company_slug}`\n"
        f"- **Dataset name:** `{dataset_name}`\n"
        f"- **Frontend service name:** `{frontend_service}`\n\n"
        f"1. Research the company using web search.\n"
        f"2. Replace all placeholders in App.jsx with real data.\n"
        f"3. Build the React app (npm install && npm run build).\n"
        f"4. Deploy the frontend to Cloud Run.\n"
        f"5. Report the deployed URL in the required output format."
    )


def _collect_template_files(base_dir: Path, workspace_prefix: str) -> list[dict[str, str]]:
    """Recursively collect all files in a directory as inline source entries.

    Args:
        base_dir: The local directory containing template files.
        workspace_prefix: The path prefix in the agent's sandbox.

    Returns:
        A list of dicts with ``target`` and ``content`` keys for inline sources.
    """
    sources: list[dict[str, str]] = []

    if not base_dir.exists():
        return sources

    for file_path in sorted(base_dir.rglob("*")):
        if file_path.is_file() and not file_path.name.startswith("."):
            try:
                content = file_path.read_text(encoding="utf-8")
                relative_path = file_path.relative_to(base_dir)
                target = f"{workspace_prefix}/{relative_path}"
                sources.append({
                    "type": "inline",
                    "target": target,
                    "content": content,
                })
            except (UnicodeDecodeError, PermissionError):
                # Skip binary files or files we can't read
                continue

    return sources


def _build_environment(all_sources: list[dict[str, str]]) -> dict:
    """Build the environment config with sources and network auth.

    Args:
        all_sources: List of inline source dicts (templates, prompts).

    Returns:
        The environment dict for the interactions.create() call.
    """
    env: dict = {
        "type": "remote",
        "sources": all_sources,
    }

    # Inject GCP credentials via network allowlist header transform
    network = get_network_allowlist()
    if network:
        env["network"] = network

    return env


def invoke_page_builder(
    client: genai.Client,
    company: str,
    ticker: str | None,
    company_slug: str,
    project: str,
    region: str,
) -> PageBuilderResult:
    """Invoke the Page Builder Managed Agent.

    Creates an interaction via the Gemini API that spawns a Managed Agent
    in a remote sandbox. The agent researches the company, builds a React
    app from templates, and deploys it to Cloud Run.

    Args:
        client: An initialized ``genai.Client`` instance.
        company: The human-readable company name.
        ticker: Optional stock ticker symbol.
        company_slug: The slugified company name.
        project: The GCP project ID.
        region: The GCP region for Cloud Run.

    Returns:
        A ``PageBuilderResult`` with the interaction output and parsed fields.
    """
    from src.result_parser import (
        extract_ca_backend_url,
        extract_frontend_url,
        extract_status,
    )

    system_instruction = _load_prompt(
        company, ticker, company_slug, project, region
    )
    user_message = _build_user_message(
        company, ticker, company_slug, project, region
    )

    # Collect all frontend template files as inline sources
    frontend_sources = _collect_template_files(
        FRONTEND_TEMPLATES_DIR, "/workspace/frontend"
    )

    # Collect CA backend templates if they exist (Phase 2)
    ca_backend_sources = _collect_template_files(
        CA_BACKEND_TEMPLATES_DIR, "/workspace/ca-backend"
    )

    # Also include the CA agent system prompt template if it exists
    ca_prompt_sources: list[dict[str, str]] = []
    if CA_AGENT_PROMPT_TEMPLATE_PATH.exists():
        ca_prompt_content = CA_AGENT_PROMPT_TEMPLATE_PATH.read_text(encoding="utf-8")
        ca_prompt_sources.append({
            "type": "inline",
            "target": "/workspace/prompts/ca_agent_system_template.md",
            "content": ca_prompt_content,
        })

    # Build environment sources (plain dicts for the API)
    all_sources = frontend_sources + ca_backend_sources + ca_prompt_sources

    try:
        interaction = client.interactions.create(
            agent=BASE_AGENT_ID,
            input=user_message,
            system_instruction=system_instruction,
            tools=[
                {"type": "google_search"},
                {"type": "code_execution"},
                {"type": "url_context"},
            ],
            agent_config={
                "type": "antigravity",
            },
            environment=_build_environment(all_sources),
        )

        # Log diagnostic info
        interaction_status = getattr(interaction, "status", "unknown")
        interaction_errors = getattr(interaction, "errors", None)
        steps = getattr(interaction, "steps", None)
        steps_count = len(steps) if steps else 0
        import sys
        print(
            f"[PB DEBUG] interaction.status={interaction_status}, "
            f"steps={steps_count}, "
            f"errors={interaction_errors}, "
            f"output_text length={len(interaction.output_text) if interaction.output_text else 0}",
            file=sys.stderr,
        )

        output_text = interaction.output_text or ""

        # Debug: show first/last 300 chars of output
        if output_text:
            print(f"[PB DEBUG] output_text START: {output_text[:300]}", file=sys.stderr)
            print(f"[PB DEBUG] output_text END: {output_text[-300:]}", file=sys.stderr)

        # If no output text but interaction didn't complete, provide diagnostics
        if not output_text and interaction_status != "completed":
            error_details = ""
            if interaction_errors:
                error_details = "; ".join(
                    str(getattr(e, "message", e)) for e in interaction_errors
                )
            return PageBuilderResult(
                error=f"Interaction {interaction_status}: {error_details or 'no output produced'}",
                status="FAILED",
            )

        # Extract status from output, fall back to interaction status
        parsed_status = extract_status(output_text)
        if not parsed_status and interaction_status == "completed" and output_text:
            parsed_status = "SUCCESS"

        return PageBuilderResult(
            output_text=output_text,
            frontend_url=extract_frontend_url(output_text),
            ca_backend_url=extract_ca_backend_url(output_text),
            status=parsed_status or "UNKNOWN",
        )

    except Exception as exc:
        return PageBuilderResult(
            error=_format_error(exc),
            status="FAILED",
        )


def _extract_output_text(interaction) -> str:
    """Extract concatenated text from an Interaction's outputs.

    The Interaction.outputs is a list of Content items (TextContent,
    CodeExecutionCallContent, etc.). We extract only TextContent items.

    Args:
        interaction: The Interaction response object.

    Returns:
        A concatenated string of all text outputs.
    """
    if not hasattr(interaction, "outputs") or not interaction.outputs:
        return ""

    text_parts: list[str] = []
    for content in interaction.outputs:
        if hasattr(content, "text") and content.text:
            text_parts.append(content.text)
    return "\n".join(text_parts)


def _format_error(exc: Exception) -> str:
    """Convert an exception to a user-friendly error message.

    Args:
        exc: The caught exception.

    Returns:
        A human-readable error string with actionable guidance.
    """
    error_str = str(exc).lower()

    if "api_key" in error_str or "unauthorized" in error_str or "401" in error_str:
        return (
            "Authentication failed. Check that GOOGLE_API_KEY is set correctly."
        )
    if "quota" in error_str or "429" in error_str:
        return (
            "API quota exceeded. Wait a few minutes and try again."
        )
    if "timeout" in error_str or "deadline" in error_str:
        return (
            "Agent timed out. The page build took too long. "
            "Try a well-known public company."
        )
    if "not found" in error_str or "404" in error_str:
        return (
            "Agent or model not found. Verify config in src/config.py."
        )

    return f"Unexpected error: {str(exc)[:300]}"

