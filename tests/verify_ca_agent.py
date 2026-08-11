"""Standalone Conversational Analytics verification script.

Validates that the CA backend is deployed and functioning correctly:
  - /health returns healthy status
  - /chat responds to a test question with a valid answer
  - /schema returns the dataset schema

Usage:
    python tests/verify_ca_agent.py --url https://company-ca-backend.run.app
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
import urllib.error


def verify_health(base_url: str) -> bool:
    """Check the /health endpoint.

    Args:
        base_url: The CA backend base URL.

    Returns:
        True if healthy, False otherwise.
    """
    print("\n1. Health check... ", end="")
    try:
        url = f"{base_url}/health"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            status = data.get("status")
            if status == "healthy":
                tables = data.get("tables", [])
                print(f"✓ PASS (tables: {', '.join(tables)})")
                return True
            else:
                print(f"✗ FAIL: status={status}")
                return False
    except Exception as exc:
        print(f"✗ FAIL: {exc}")
        return False


def verify_chat(base_url: str) -> bool:
    """Check the /chat endpoint with a test question.

    Args:
        base_url: The CA backend base URL.

    Returns:
        True if a valid response is received, False otherwise.
    """
    print("\n2. Chat endpoint... ", end="")
    try:
        url = f"{base_url}/chat"
        payload = json.dumps({"message": "How many records are in the dataset?"}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            response_text = data.get("response", "")
            sql_used = data.get("sql")

            if response_text and len(response_text) > 10:
                print(f"✓ PASS")
                print(f"   Response: {response_text[:200]}")
                if sql_used:
                    print(f"   SQL: {sql_used[:100]}")
                return True
            else:
                print(f"✗ FAIL: empty or too short response")
                return False
    except Exception as exc:
        print(f"✗ FAIL: {exc}")
        return False


def verify_schema(base_url: str) -> bool:
    """Check the /schema endpoint.

    Args:
        base_url: The CA backend base URL.

    Returns:
        True if schema data is returned, False otherwise.
    """
    print("\n3. Schema endpoint... ", end="")
    try:
        url = f"{base_url}/schema"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            schema = data.get("schema", "")
            if schema and "Table:" in schema:
                table_count = schema.count("Table:")
                print(f"✓ PASS ({table_count} tables)")
                return True
            else:
                print(f"✗ FAIL: no table information found")
                return False
    except Exception as exc:
        print(f"✗ FAIL: {exc}")
        return False


def main() -> None:
    """CLI entry point for CA agent verification."""
    parser = argparse.ArgumentParser(
        description="Verify a Conversational Analytics backend deployment"
    )
    parser.add_argument(
        "--url",
        required=True,
        help="CA backend base URL (e.g., https://company-ca-backend-abc.run.app)",
    )
    parser.add_argument(
        "--wait",
        type=int,
        default=0,
        help="Wait N seconds before starting (for cold-start warmup)",
    )
    args = parser.parse_args()

    base_url = args.url.rstrip("/")

    print(f"🔍 Verifying CA backend: {base_url}")
    print("─" * 50)

    if args.wait > 0:
        print(f"Waiting {args.wait}s for cold-start warmup...")
        time.sleep(args.wait)

    results = [
        verify_health(base_url),
        verify_chat(base_url),
        verify_schema(base_url),
    ]

    print("\n" + "─" * 50)
    passed = sum(results)
    total = len(results)

    if all(results):
        print(f"✅ All {total} checks passed!")
        sys.exit(0)
    else:
        print(f"❌ {total - passed}/{total} checks failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
