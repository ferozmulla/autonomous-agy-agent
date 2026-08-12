"""Data Generator agent invocation module.

Reads the system instruction and SKILL.md, assembles the interaction
configuration, and calls the Gemini API to create a Managed Agent
interaction that generates a BigQuery dataset.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from google import genai


from src.config import (
    BASE_AGENT_ID,
    DATA_GENERATOR_PROMPT_PATH,
    DATA_GENERATOR_SKILL_PATH,
    GEMINI_MODEL,
    get_dataset_name,
    get_network_allowlist,
)


@dataclass
class DataGeneratorResult:
    """Structured result from a Data Generator interaction.

    Attributes:
        output_text: The raw output text from the Managed Agent.
        dataset_name: The full dataset reference (project.dataset), if found.
        table_info: List of table names and row counts, if found.
        status: The reported status ("SUCCESS", "FAILED", or "UNKNOWN").
        error: Error message, if the interaction failed.
    """

    output_text: str = ""
    dataset_name: str | None = None
    table_info: list[dict[str, str]] = field(default_factory=list)
    status: str = "UNKNOWN"
    error: str | None = None


def _load_prompt(company: str, company_slug: str, project: str) -> str:
    """Load and parameterize the Data Generator system instruction.

    Args:
        company: The human-readable company name.
        company_slug: The slugified company name.
        project: The GCP project ID.

    Returns:
        The fully parameterized system instruction string.
    """
    raw_prompt = DATA_GENERATOR_PROMPT_PATH.read_text(encoding="utf-8")
    dataset_name = get_dataset_name(company_slug)

    prompt = raw_prompt.replace("{{PROJECT_ID}}", project)
    prompt = prompt.replace("{{DATASET_NAME}}", dataset_name)
    return prompt


def _load_skill() -> str:
    """Load the analytics-data-generator SKILL.md content.

    Returns:
        The full content of the SKILL.md file.
    """
    return DATA_GENERATOR_SKILL_PATH.read_text(encoding="utf-8")


def _build_user_message(company: str, company_slug: str, project: str) -> str:
    """Build the user message that kicks off data generation.

    Args:
        company: The human-readable company name.
        company_slug: The slugified company name.
        project: The GCP project ID.

    Returns:
        The user message string.
    """
    dataset_name = get_dataset_name(company_slug)
    return (
        f"Generate a synthetic analytics dataset for **{company}**.\n\n"
        f"- **Project ID:** `{project}`\n"
        f"- **Dataset name:** `{dataset_name}`\n"
        f"- **Dataset location:** `us-central1`\n\n"
        f"Follow the Generation Blueprint in your skill file. "
        f"Generate the complete, consolidated SQL script.\n\n"
        f"**IMPORTANT:** After generating the SQL, try executing it using "
        f"`bq query`. If execution fails due to authentication issues in "
        f"this sandbox environment, that is OK — output the SQL script "
        f"in a fenced code block (```sql ... ```) and set STATUS: SQL_READY "
        f"instead of FAILED. The CLI will execute it externally.\n\n"
        f"Report results in the required output format."
    )


def _build_environment(skill_content: str) -> dict:
    """Build the environment config with sources and network auth.

    Args:
        skill_content: The SKILL.md content to inject as an inline source.

    Returns:
        The environment dict for the interactions.create() call.
    """
    env: dict = {
        "type": "remote",
        "sources": [
            {
                "type": "inline",
                "target": ".agents/skills/analytics-data-generator/SKILL.md",
                "content": skill_content,
            },
        ],
    }

    # Inject GCP credentials via network allowlist header transform
    network = get_network_allowlist()
    if network:
        env["network"] = network

    return env


def invoke_data_generator(
    client: genai.Client,
    company: str,
    company_slug: str,
    project: str,
) -> DataGeneratorResult:
    """Invoke the Data Generator Managed Agent.

    Creates an interaction via the Gemini API that spawns a Managed Agent
    in a remote sandbox. The agent generates and executes BigQuery SQL
    following the analytics-data-generator skill methodology.

    Args:
        client: An initialized ``genai.Client`` instance.
        company: The human-readable company name.
        company_slug: The slugified company name.
        project: The GCP project ID.

    Returns:
        A ``DataGeneratorResult`` with the interaction output and parsed fields.
    """
    from src.result_parser import (
        extract_dataset_name,
        extract_status,
        extract_table_info,
    )

    system_instruction = _load_prompt(company, company_slug, project)
    skill_content = _load_skill()
    user_message = _build_user_message(company, company_slug, project)

    try:
        interaction = client.interactions.create(
            agent=BASE_AGENT_ID,
            input=user_message,
            system_instruction=system_instruction,
            tools=[
                {"type": "google_search"},
                {"type": "code_execution"},
            ],
            agent_config={
                "type": "antigravity",
            },
            environment=_build_environment(skill_content),
        )

        # Log diagnostic info
        interaction_status = getattr(interaction, "status", "unknown")
        interaction_errors = getattr(interaction, "errors", None)
        steps = getattr(interaction, "steps", None)
        steps_count = len(steps) if steps else 0
        import sys
        print(
            f"[DG DEBUG] interaction.status={interaction_status}, "
            f"steps={steps_count}, "
            f"errors={interaction_errors}, "
            f"output_text length={len(interaction.output_text) if interaction.output_text else 0}",
            file=sys.stderr,
        )

        output_text = interaction.output_text or ""

        # Debug: show first/last 300 chars of output
        if output_text:
            print(f"[DG DEBUG] output_text START: {output_text[:300]}", file=sys.stderr)
            print(f"[DG DEBUG] output_text END: {output_text[-300:]}", file=sys.stderr)

        # If no output text but interaction didn't complete, provide diagnostics
        if not output_text and interaction_status != "completed":
            error_details = ""
            if interaction_errors:
                error_details = "; ".join(
                    str(getattr(e, "message", e)) for e in interaction_errors
                )
            return DataGeneratorResult(
                error=f"Interaction {interaction_status}: {error_details or 'no output produced'}",
                status="FAILED",
            )

        # Extract status from output, fall back to interaction status
        parsed_status = extract_status(output_text)
        if not parsed_status and interaction_status == "completed" and output_text:
            parsed_status = "SUCCESS"

        # If agent couldn't execute SQL in sandbox, extract and run locally
        if parsed_status in ("SQL_READY", "FAILED") and "```sql" in output_text:
            sql = _extract_sql(output_text)
            if sql:
                print("[DG] Agent generated SQL but couldn't execute in sandbox. "
                      "Executing locally...", file=sys.stderr)
                local_result = _execute_sql_locally(sql, project)
                if local_result["success"]:
                    print("[DG] ✅ Local SQL execution succeeded!", file=sys.stderr)
                    parsed_status = "SUCCESS"
                else:
                    print(f"[DG] ❌ Local SQL execution failed: {local_result['error']}",
                          file=sys.stderr)
                    return DataGeneratorResult(
                        output_text=output_text,
                        error=f"Local SQL execution failed: {local_result['error']}",
                        status="FAILED",
                    )

        return DataGeneratorResult(
            output_text=output_text,
            dataset_name=extract_dataset_name(output_text),
            table_info=extract_table_info(output_text),
            status=parsed_status or "UNKNOWN",
        )

    except Exception as exc:
        return DataGeneratorResult(
            error=_format_error(exc),
            status="FAILED",
        )


def _extract_sql(output_text: str) -> str | None:
    """Extract the SQL script from fenced code blocks in agent output.

    Looks for ```sql ... ``` blocks and returns the largest one
    (the main generation script, not verification queries).

    Args:
        output_text: The agent's output text containing SQL blocks.

    Returns:
        The SQL script string, or None if no SQL block found.
    """
    import re

    sql_blocks = re.findall(r"```sql\s*\n(.*?)```", output_text, re.DOTALL)
    if not sql_blocks:
        return None

    # Return the largest SQL block (the main generation script)
    return max(sql_blocks, key=len).strip()


def _hoist_declares(sql: str) -> str:
    """Move all DECLARE statements to the top of a BigQuery SQL script.

    BigQuery requires all DECLARE statements at the start of a block or
    script. LLM-generated SQL sometimes places them mid-script (e.g.,
    inside loops or after CREATE statements). This function extracts them
    and moves them to the top while preserving order.

    Args:
        sql: The raw SQL script.

    Returns:
        The SQL script with all DECLARE statements hoisted to the top.
    """
    import re

    lines = sql.split("\n")
    declares: list[str] = []
    other: list[str] = []

    for line in lines:
        stripped = line.strip()
        # Match lines starting with DECLARE (case-insensitive), but not
        # inside comments
        if re.match(r"^DECLARE\s+", stripped, re.IGNORECASE) and not stripped.startswith("--"):
            declares.append(line)
        else:
            other.append(line)

    if not declares:
        return sql

    return "\n".join(declares) + "\n\n" + "\n".join(other)


def _execute_sql_locally(sql: str, project: str) -> dict:
    """Execute a BigQuery SQL script locally using the BigQuery client.

    Uses the local machine's Application Default Credentials which have
    the required BigQuery permissions (dataEditor + jobUser).

    Args:
        sql: The complete SQL script to execute.
        project: The GCP project ID.

    Returns:
        A dict with 'success' (bool) and optionally 'error' (str).
    """
    try:
        from google.cloud import bigquery

        client = bigquery.Client(project=project)

        # Preprocess: hoist any misplaced DECLARE statements to the top
        sql = _hoist_declares(sql)

        # Set job location to match dataset location (us-central1)
        job_config = bigquery.QueryJobConfig()

        import sys
        print(f"[DG] Executing SQL script ({len(sql)} chars) against project {project} "
              f"in us-central1...", file=sys.stderr)

        job = client.query(sql, job_config=job_config, location="us-central1")
        job.result()  # Wait for completion

        print(f"[DG] SQL execution complete. Job ID: {job.job_id}", file=sys.stderr)
        return {"success": True}

    except Exception as exc:
        return {"success": False, "error": str(exc)[:500]}


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
            "Authentication failed. Check that GOOGLE_API_KEY is set correctly "
            "in your .env file."
        )
    if "quota" in error_str or "429" in error_str:
        return (
            "API quota exceeded. Wait a few minutes and try again, or check "
            "your Gemini API quota at https://aistudio.google.com."
        )
    if "timeout" in error_str or "deadline" in error_str:
        return (
            "Agent timed out. The data generation took too long. "
            "Try a well-known public company with abundant online data."
        )
    if "not found" in error_str or "404" in error_str:
        return (
            "Agent or model not found. Verify that the base agent ID and "
            "model name are correct in src/config.py."
        )

    # Generic fallback — include first 300 chars of the original error
    return f"Unexpected error: {str(exc)[:300]}"
