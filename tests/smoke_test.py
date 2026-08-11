"""End-to-end smoke test for Agent-Built Demos.

Runs launch_demo.py against a test company and verifies:
  1. CLI exits with code 0
  2. Output contains a Cloud Run URL
  3. The URL returns HTTP 200
  4. BigQuery dataset exists with >0 rows in all tables

This test requires:
  - GOOGLE_API_KEY set in the environment
  - gcloud authenticated with BigQuery and Cloud Run access
  - Network access to the Gemini API and GCP services

Usage:
    pytest tests/smoke_test.py -v --timeout=900
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

# Skip the entire module if GOOGLE_API_KEY is not set
pytestmark = pytest.mark.skipif(
    not os.environ.get("GOOGLE_API_KEY"),
    reason="GOOGLE_API_KEY not set — skipping smoke tests",
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
LAUNCH_SCRIPT = PROJECT_ROOT / "src" / "launch_demo.py"
TEST_COMPANY = "Apple"
TEST_PROJECT = os.environ.get("GCP_PROJECT", "firstargolisproject-338816")


class TestSmokeEndToEnd:
    """End-to-end smoke test suite."""

    @pytest.fixture(scope="class")
    def cli_result(self):
        """Run launch_demo.py and capture output.

        This is a class-scoped fixture so the CLI only runs once for all
        tests in this class.
        """
        result = subprocess.run(
            [
                sys.executable,
                str(LAUNCH_SCRIPT),
                "--company", TEST_COMPANY,
                "--project", TEST_PROJECT,
            ],
            capture_output=True,
            text=True,
            timeout=600,
            cwd=str(PROJECT_ROOT),
        )
        return result

    def test_cli_exits_successfully(self, cli_result) -> None:
        """The CLI should exit with code 0."""
        assert cli_result.returncode == 0, (
            f"CLI exited with code {cli_result.returncode}.\n"
            f"stdout: {cli_result.stdout[:500]}\n"
            f"stderr: {cli_result.stderr[:500]}"
        )

    def test_output_contains_cloud_run_url(self, cli_result) -> None:
        """The output should contain a Cloud Run URL."""
        import re
        url_pattern = r"https://[a-zA-Z0-9._-]+\.run\.app"
        match = re.search(url_pattern, cli_result.stdout)
        assert match is not None, (
            f"No Cloud Run URL found in output:\n{cli_result.stdout[:500]}"
        )

    def test_deployed_url_returns_200(self, cli_result) -> None:
        """The deployed URL should return HTTP 200."""
        import re
        import requests

        url_pattern = r"https://[a-zA-Z0-9._-]+\.run\.app"
        match = re.search(url_pattern, cli_result.stdout)
        if match is None:
            pytest.skip("No Cloud Run URL found in output")

        url = match.group(0)
        response = requests.get(url, timeout=30)
        assert response.status_code == 200, (
            f"URL {url} returned status {response.status_code}"
        )

    def test_bigquery_dataset_exists(self, cli_result) -> None:
        """The BigQuery dataset should exist with tables containing rows."""
        from google.cloud import bigquery

        slug = "apple"
        dataset_name = f"{slug}_demo"
        bq_client = bigquery.Client(project=TEST_PROJECT)

        dataset_ref = f"{TEST_PROJECT}.{dataset_name}"
        tables = list(bq_client.list_tables(dataset_ref))
        assert len(tables) > 0, f"No tables found in dataset {dataset_ref}"

        for table in tables:
            full_table = bq_client.get_table(table.reference)
            assert full_table.num_rows > 0, (
                f"Table {table.table_id} has 0 rows"
            )
