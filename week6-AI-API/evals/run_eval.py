import sys
import json
import argparse
import pathlib
import urllib.request
import urllib.error

CASES_PATH = pathlib.Path(__file__).parent / "cases.json"


def call_endpoint(base_url: str, text: str) -> dict:
    req = urllib.request.Request(
        f"{base_url}/triage",
        data=json.dumps({"text": text}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return {"status": resp.status, "body": json.loads(resp.read())}
    except urllib.error.HTTPError as exc:
        return {"status": exc.code, "body": json.loads(exc.read())}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000")
    args = parser.parse_args()

    cases = json.loads(CASES_PATH.read_text())
    results = []
    matched = 0

    for case in cases:
        outcome = call_endpoint(args.url, case["text"])
        got_category = outcome["body"].get("category") if outcome["status"] == 200 else None
        is_match = got_category == case["expected_category"]
        matched += is_match
        results.append({
            "id": case["id"],
            "text": case["text"][:60],
            "expected": case["expected_category"],
            "got": got_category,
            "status": outcome["status"],
            "match": is_match,
        })

    print(f"\n{'ID':<4}{'expected':<10}{'got':<10}{'status':<8}match")
    for r in results:
        mark = "PASS" if r["match"] else "FAIL"
        print(f"{r['id']:<4}{r['expected']:<10}{str(r['got']):<10}{r['status']:<8}{mark}")

    total = len(cases)
    print(f"\nScore: {matched}/{total} on category ({round(100 * matched / total)}%)")

    failed = [r for r in results if not r["match"]]
    if failed:
        print("\nFailed cases:")
        for r in failed:
            print(f"  #{r['id']}: expected {r['expected']!r}, got {r['got']!r} (status {r['status']})")

    return 0 if matched == total else 1


if __name__ == "__main__":
    sys.exit(main())
