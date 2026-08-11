"""Tests for prompt file existence and content validation.

Validates that all prompt files exist, contain expected sections,
and have the required placeholders for runtime parameterization.
"""

import pytest
from pathlib import Path

from src.config import (
    DATA_GENERATOR_PROMPT_PATH,
    PAGE_BUILDER_PROMPT_PATH,
    CA_AGENT_PROMPT_TEMPLATE_PATH,
    PROJECT_ROOT,
)


class TestDataGeneratorPrompt:
    """Validates the Data Generator system instruction."""

    def test_file_exists(self) -> None:
        assert DATA_GENERATOR_PROMPT_PATH.exists(), (
            f"Data Generator prompt not found at {DATA_GENERATOR_PROMPT_PATH}"
        )

    def test_contains_role_definition(self) -> None:
        content = DATA_GENERATOR_PROMPT_PATH.read_text(encoding="utf-8")
        assert "Data Engineer" in content or "data engineer" in content.lower()

    def test_contains_skill_reference(self) -> None:
        content = DATA_GENERATOR_PROMPT_PATH.read_text(encoding="utf-8")
        assert "SKILL.md" in content or "skill" in content.lower()

    def test_contains_generation_blueprint(self) -> None:
        content = DATA_GENERATOR_PROMPT_PATH.read_text(encoding="utf-8")
        assert "Generation Blueprint" in content or "generation blueprint" in content.lower()

    def test_contains_output_format(self) -> None:
        content = DATA_GENERATOR_PROMPT_PATH.read_text(encoding="utf-8")
        assert "DATA GENERATOR RESULTS" in content

    def test_contains_project_id_placeholder(self) -> None:
        content = DATA_GENERATOR_PROMPT_PATH.read_text(encoding="utf-8")
        assert "{{PROJECT_ID}}" in content

    def test_contains_dataset_placeholder(self) -> None:
        content = DATA_GENERATOR_PROMPT_PATH.read_text(encoding="utf-8")
        assert "{{DATASET_NAME}}" in content

    def test_contains_verification_section(self) -> None:
        content = DATA_GENERATOR_PROMPT_PATH.read_text(encoding="utf-8")
        assert "Verify" in content or "verify" in content.lower()


class TestPageBuilderPrompt:
    """Validates the Page Builder system instruction."""

    def test_file_exists(self) -> None:
        assert PAGE_BUILDER_PROMPT_PATH.exists(), (
            f"Page Builder prompt not found at {PAGE_BUILDER_PROMPT_PATH}"
        )

    def test_contains_deployment_instructions(self) -> None:
        content = PAGE_BUILDER_PROMPT_PATH.read_text(encoding="utf-8")
        assert "gcloud run deploy" in content

    def test_contains_research_instructions(self) -> None:
        content = PAGE_BUILDER_PROMPT_PATH.read_text(encoding="utf-8")
        assert "web search" in content.lower() or "google_search" in content.lower()

    def test_contains_template_references(self) -> None:
        content = PAGE_BUILDER_PROMPT_PATH.read_text(encoding="utf-8")
        assert "App.jsx" in content

    def test_contains_output_format(self) -> None:
        content = PAGE_BUILDER_PROMPT_PATH.read_text(encoding="utf-8")
        assert "PAGE BUILDER RESULTS" in content

    def test_contains_placeholder_list(self) -> None:
        content = PAGE_BUILDER_PROMPT_PATH.read_text(encoding="utf-8")
        placeholders = [
            "{{TICKER}}",
            "{{COMPANY_NAME}}",
            "{{PRICE}}",
            "{{TREND_PERCENT}}",
        ]
        for placeholder in placeholders:
            assert placeholder in content, f"Missing placeholder: {placeholder}"


class TestCaAgentPromptTemplate:
    """Validates the CA agent system prompt template (Phase 2)."""

    def test_file_will_exist_in_phase_2(self) -> None:
        """The CA agent template may not exist in Phase 1 — that's expected."""
        # This test passes regardless since the file is a Phase 2 deliverable.
        # When the file exists, it must contain the required placeholders.
        if CA_AGENT_PROMPT_TEMPLATE_PATH.exists():
            content = CA_AGENT_PROMPT_TEMPLATE_PATH.read_text(encoding="utf-8")
            assert "{{COMPANY_NAME}}" in content
            assert "{{DATASET_NAME}}" in content
            assert "{{PROJECT_ID}}" in content


class TestSkillFile:
    """Validates the analytics-data-generator SKILL.md."""

    def test_skill_exists(self) -> None:
        skill_path = PROJECT_ROOT / "skills" / "analytics-data-generator" / "SKILL.md"
        assert skill_path.exists(), f"SKILL.md not found at {skill_path}"

    def test_skill_contains_blueprint(self) -> None:
        skill_path = PROJECT_ROOT / "skills" / "analytics-data-generator" / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")
        assert "Generation Blueprint" in content

    def test_skill_contains_use_case_table(self) -> None:
        skill_path = PROJECT_ROOT / "skills" / "analytics-data-generator" / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")
        assert "Use-Case Lookup" in content or "Media / Entertainment" in content

    def test_skill_contains_checklist(self) -> None:
        skill_path = PROJECT_ROOT / "skills" / "analytics-data-generator" / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")
        assert "Agent-Readiness Checklist" in content
