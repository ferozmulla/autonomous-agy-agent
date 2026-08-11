"""Unit tests for src/result_parser.py — output parsing functions."""

import pytest

from src.result_parser import (
    extract_all_cloud_run_urls,
    extract_ca_backend_url,
    extract_cloud_run_url,
    extract_dataset_name,
    extract_frontend_url,
    extract_milestones,
    extract_status,
    extract_table_info,
    is_agent_success,
)


# --- Sample output texts for testing ---

SAMPLE_DATA_GENERATOR_OUTPUT = """
=== DATA GENERATOR RESULTS ===
DATASET: firstargolisproject-338816.siriusxm_demo
TABLES:
  - dim_subscribers: 3000 rows
  - dim_channels: 50 rows
  - fact_listening_events: 89420 rows
INDUSTRY: Media / Entertainment
USE_CASE: Impact of channel removal on subscriber retention
WORST_ACTORS: 5 entities identified
DATE_RANGE: 2026-05-13 to 2026-08-11
STATUS: SUCCESS
=== END DATA GENERATOR RESULTS ===
"""

SAMPLE_PAGE_BUILDER_OUTPUT = """
=== PAGE BUILDER RESULTS ===
FRONTEND_URL: https://siriusxm-frontend-abc123.us-central1.run.app
CA_BACKEND_URL: https://siriusxm-ca-backend-xyz789.us-central1.run.app
COMPANY: SiriusXM
TICKER: SIRI
INDUSTRY: Media / Entertainment
STATUS: SUCCESS
=== END PAGE BUILDER RESULTS ===
"""

SAMPLE_FAILED_OUTPUT = """
=== DATA GENERATOR RESULTS ===
STATUS: FAILED
ERROR: BigQuery query execution failed — permission denied
=== END DATA GENERATOR RESULTS ===
"""

SAMPLE_OUTPUT_WITH_MILESTONES = """
✓ Dataset created: firstargolisproject-338816.siriusxm_demo
✓ Frontend deployed to Cloud Run
✗ CA backend deployment failed
✅ Demo ready
"""


class TestExtractCloudRunUrl:
    """Tests for Cloud Run URL extraction."""

    def test_extracts_single_url(self) -> None:
        text = "Service URL: https://my-service-abc.us-central1.run.app"
        assert extract_cloud_run_url(text) == "https://my-service-abc.us-central1.run.app"

    def test_returns_none_when_no_url(self) -> None:
        assert extract_cloud_run_url("No URL here") is None

    def test_extracts_first_url(self) -> None:
        text = "URL1: https://first.run.app URL2: https://second.run.app"
        assert extract_cloud_run_url(text) == "https://first.run.app"


class TestExtractAllCloudRunUrls:
    """Tests for extracting all Cloud Run URLs."""

    def test_extracts_multiple_urls(self) -> None:
        urls = extract_all_cloud_run_urls(SAMPLE_PAGE_BUILDER_OUTPUT)
        assert len(urls) == 2
        assert "https://siriusxm-frontend-abc123.us-central1.run.app" in urls
        assert "https://siriusxm-ca-backend-xyz789.us-central1.run.app" in urls

    def test_returns_empty_list_when_no_urls(self) -> None:
        assert extract_all_cloud_run_urls("No URLs") == []


class TestExtractDatasetName:
    """Tests for dataset name extraction."""

    def test_extracts_dataset(self) -> None:
        result = extract_dataset_name(SAMPLE_DATA_GENERATOR_OUTPUT)
        assert result == "firstargolisproject-338816.siriusxm_demo"

    def test_returns_none_when_missing(self) -> None:
        assert extract_dataset_name("No dataset") is None


class TestExtractStatus:
    """Tests for status extraction."""

    def test_extracts_success(self) -> None:
        assert extract_status(SAMPLE_DATA_GENERATOR_OUTPUT) == "SUCCESS"

    def test_extracts_failed(self) -> None:
        assert extract_status(SAMPLE_FAILED_OUTPUT) == "FAILED"

    def test_returns_none_when_missing(self) -> None:
        assert extract_status("No status here") is None


class TestExtractMilestones:
    """Tests for milestone extraction."""

    def test_extracts_milestone_lines(self) -> None:
        milestones = extract_milestones(SAMPLE_OUTPUT_WITH_MILESTONES)
        assert len(milestones) == 4
        assert any("Dataset created" in m for m in milestones)
        assert any("Frontend deployed" in m for m in milestones)
        assert any("failed" in m for m in milestones)


class TestExtractTableInfo:
    """Tests for table info extraction."""

    def test_extracts_tables(self) -> None:
        tables = extract_table_info(SAMPLE_DATA_GENERATOR_OUTPUT)
        assert len(tables) == 3
        assert tables[0]["name"] == "dim_subscribers"
        assert tables[0]["row_count"] == "3000"
        assert tables[2]["name"] == "fact_listening_events"
        assert tables[2]["row_count"] == "89420"


class TestExtractFrontendUrl:
    """Tests for frontend URL extraction."""

    def test_extracts_frontend_url(self) -> None:
        url = extract_frontend_url(SAMPLE_PAGE_BUILDER_OUTPUT)
        assert url == "https://siriusxm-frontend-abc123.us-central1.run.app"

    def test_returns_none_when_no_urls(self) -> None:
        assert extract_frontend_url("No URL") is None


class TestExtractCaBackendUrl:
    """Tests for CA backend URL extraction."""

    def test_extracts_ca_url(self) -> None:
        url = extract_ca_backend_url(SAMPLE_PAGE_BUILDER_OUTPUT)
        assert url == "https://siriusxm-ca-backend-xyz789.us-central1.run.app"

    def test_returns_none_when_no_ca_url(self) -> None:
        text = "FRONTEND_URL: https://siriusxm-frontend.run.app"
        assert extract_ca_backend_url(text) is None


class TestIsAgentSuccess:
    """Tests for the agent success determination."""

    def test_success_status(self) -> None:
        assert is_agent_success(SAMPLE_DATA_GENERATOR_OUTPUT) is True

    def test_failed_status(self) -> None:
        assert is_agent_success(SAMPLE_FAILED_OUTPUT) is False

    def test_fallback_url_heuristic(self) -> None:
        text = "https://my-service.run.app"
        assert is_agent_success(text) is True

    def test_fallback_no_indicators(self) -> None:
        assert is_agent_success("Nothing useful here") is False
