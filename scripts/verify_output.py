#!/usr/bin/env python3
"""
verify_output.py - Validates artifacts/sanity_output.json format
Used by judges to verify submission compliance.
"""

import json
import sys
import os

REQUIRED_FIELDS = ["timestamp", "sample_query", "agent_response", "citations", "status"]

def verify():
    # Look for the file in multiple locations
    paths = [
        "backend/artifacts/sanity_output.json",
        "artifacts/sanity_output.json",
        os.path.join(os.path.dirname(__file__), "..", "backend", "artifacts", "sanity_output.json"),
    ]

    filepath = None
    for p in paths:
        if os.path.exists(p):
            filepath = p
            break

    if not filepath:
        print("FAIL: sanity_output.json not found in any expected location")
        print(f"  Searched: {paths}")
        sys.exit(1)

    print(f"Found: {filepath}")

    try:
        with open(filepath) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"FAIL: Invalid JSON - {e}")
        sys.exit(1)

    print("  JSON is valid")

    # Check required fields
    missing = [field for field in REQUIRED_FIELDS if field not in data]
    if missing:
        print(f"FAIL: Missing required fields: {missing}")
        sys.exit(1)

    print(f"  All required fields present: {REQUIRED_FIELDS}")

    # Validate field types
    if not isinstance(data["timestamp"], str):
        print("FAIL: 'timestamp' must be a string (ISO format)")
        sys.exit(1)

    if not isinstance(data["sample_query"], str) or len(data["sample_query"]) == 0:
        print("FAIL: 'sample_query' must be a non-empty string")
        sys.exit(1)

    if not isinstance(data["agent_response"], str) or len(data["agent_response"]) == 0:
        print("FAIL: 'agent_response' must be a non-empty string")
        sys.exit(1)

    if not isinstance(data["citations"], list):
        print("FAIL: 'citations' must be a list")
        sys.exit(1)

    print("  Field types validated")

    # Print summary
    print("\n=== Output Summary ===")
    print(f"  Timestamp: {data['timestamp']}")
    print(f"  Query: {data['sample_query']}")
    print(f"  Response: {data['agent_response'][:100]}...")
    print(f"  Citations: {len(data['citations'])} items")
    print(f"  Status: {data.get('status', 'N/A')}")

    if "documents_indexed" in data:
        print(f"  Documents Indexed: {data['documents_indexed']}")

    print("\nPASS: sanity_output.json is valid!")
    return 0

if __name__ == "__main__":
    sys.exit(verify())
