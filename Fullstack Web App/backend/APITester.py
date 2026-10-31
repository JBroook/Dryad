
import json
import math
import os
import statistics
import time

import requests

BASE_URL = os.environ.get("DRYAD_API_URL", "").rstrip("/")
EMAIL = os.environ.get("DRYAD_TEST_EMAIL", "")
PASSWORD = os.environ.get("DRYAD_TEST_PASSWORD", "")

PROJECT_ID = os.environ.get("DRYAD_TEST_PROJECT_ID")
USER_ID = os.environ.get("DRYAD_TEST_USER_ID")
DEVICE_ID = os.environ.get("DRYAD_TEST_DEVICE_ID")

ITERATIONS = int(os.environ.get("DRYAD_TEST_ITERATIONS", "20"))
TIMEOUT = int(os.environ.get("DRYAD_TEST_TIMEOUT", "120"))

INCLUDE_WRITE_TESTS = (
    os.environ.get("DRYAD_INCLUDE_WRITE_TESTS", "0") == "1"
)

session = requests.Session()

def percentile(values, percent):
    ordered = sorted(values)
    index = max(0, math.ceil(percent / 100 * len(ordered)) - 1)
    return ordered[index]


def benchmark_get(name, path):
    url = f"{BASE_URL}{path}"

    print(f"\nTesting: {name}")
    print(f"Endpoint: GET {path}")

    timings_ms = []
    statuses = []
    failures = 0

    for iteration in range(ITERATIONS):
        start = time.perf_counter()

        try:
            response = session.get(url, timeout=TIMEOUT)
            elapsed_ms = (time.perf_counter() - start) * 1000

            timings_ms.append(elapsed_ms)
            statuses.append(response.status_code)

            if not response.ok:
                failures += 1

        except requests.RequestException as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            timings_ms.append(elapsed_ms)
            statuses.append("ERROR")
            failures += 1
            print(f"  Request {iteration + 1} failed: {exc}")

    if not timings_ms:
        print("  No timing results available.")
        return

    print(f"  Requests: {len(timings_ms)}")
    print(f"  HTTP statuses: {sorted(set(map(str, statuses)))}")
    print(f"  Successful requests: {len(timings_ms) - failures}")
    print(f"  Error rate: {failures / len(timings_ms) * 100:.1f}%")
    print(f"  Average: {statistics.mean(timings_ms):.1f} ms")
    print(f"  Median:  {statistics.median(timings_ms):.1f} ms")
    print(f"  P95:     {percentile(timings_ms, 95):.1f} ms")
    print(f"  Minimum: {min(timings_ms):.1f} ms")
    print(f"  Maximum: {max(timings_ms):.1f} ms")


def benchmark_single_post(name, path, payload):
    url = f"{BASE_URL}{path}"

    print(f"\nTesting: {name}")
    print(f"Endpoint: POST {path}")
    print("  Single request only; this may modify database records.")

    start = time.perf_counter()

    try:
        response = session.post(
            url,
            json=payload,
            timeout=TIMEOUT,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        print(f"  HTTP status: {response.status_code}")
        print(f"  Response time: {elapsed_ms:.1f} ms")

        if not response.ok:
            print(f"  Response: {response.text[:1000]}")

    except requests.RequestException as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        print(f"  Request failed after {elapsed_ms:.1f} ms: {exc}")


def authenticate():
    if not BASE_URL:
        raise ValueError(
            "Set DRYAD_API_URL to your backend API base URL."
        )

    if not EMAIL or not PASSWORD:
        raise ValueError(
            "Set DRYAD_TEST_EMAIL and DRYAD_TEST_PASSWORD."
        )

    login_url = f"{BASE_URL}/login/"

    print("Authenticating with Dryad...")

    start = time.perf_counter()
    response = session.post(
        login_url,
        json={"email": EMAIL, "password": PASSWORD},
        timeout=TIMEOUT,
    )
    elapsed = time.perf_counter() - start

    print(f"Login status: {response.status_code}")
    print(f"Login time: {elapsed:.3f} seconds")

    response.raise_for_status()
    data = response.json()

    access_token = data.get("access")

    if access_token:
        session.headers.update({
            "Authorization": f"Bearer {access_token}"
        })
    elif data.get("key"):
        session.headers.update({
            "Authorization": f"Token {data['key']}"
        })
    else:
        raise ValueError(
            "Could not find an access token in the login response. "
            "Check your LoginView response and authentication scheme."
        )

    print("Authentication successful.")

def main():
    authenticate()

    if ITERATIONS < 1:
        raise ValueError("DRYAD_TEST_ITERATIONS must be at least 1.")

    endpoints = [
        # Core project endpoints
        ("List projects", "/projects/"),
        ("Project overview", "/projects/overview"),
        ("List threat classes", "/threat_classes/"),
        ("List incidents", "/incidents/"),
    ]

    # Endpoints requiring an existing project
    if PROJECT_ID:
        project = f"/projects/{PROJECT_ID}"

        endpoints.extend([
            ("Project details", f"{project}/"),
            ("Grid cells", f"{project}/grid_cells/"),
            ("Project members", f"{project}/members/"),
            ("Project devices", f"{project}/devices/"),
            ("Project patrols", f"{project}/patrols/"),
            ("Routine patrols", f"{project}/routine_patrols/"),
            ("Incident activity", f"{project}/incident_activity"),
        ])

    # Endpoints requiring an existing user
    if USER_ID:
        user = f"/users/{USER_ID}"

        endpoints.extend([
            ("User details", f"{user}/"),
            ("User overview", f"{user}/overview"),
            ("User memberships", f"{user}/memberships"),
            ("User patrols", f"{user}/patrols/"),
            ("User routine patrols", f"{user}/routine_patrols/"),
        ])

    # Run the read-only benchmarks
    for name, path in endpoints:
        benchmark_get(name, path)

    # Optional state-changing tests
    if INCLUDE_WRITE_TESTS:
        print("\n" + "=" * 60)
        print("OPTIONAL WRITE TESTS")
        print("=" * 60)

        if PROJECT_ID:
            # The view may not require a JSON body; confirm its implementation.
            risk_payload = json.loads(
                os.environ.get("DRYAD_TEST_RISK_PAYLOAD", "{}")
            )
            benchmark_single_post(
                "Calculate project risk",
                f"/projects/{PROJECT_ID}/calculate_risk",
                risk_payload,
            )
        else:
            print("Skipping risk calculation: PROJECT_ID is not set.")

        # if DEVICE_ID:
        #     report_payload_text = os.environ.get(
        #         "DRYAD_TEST_REPORT_PAYLOAD"
        #     )

        #     if report_payload_text:
        #         report_payload = json.loads(report_payload_text)
        #         benchmark_single_post(
        #             "Submit device incident report",
        #             f"/devices/{DEVICE_ID}/report",
        #             report_payload,
        #         )
        #     else:
        #         print(
        #             "Skipping device report: set "
        #             "DRYAD_TEST_REPORT_PAYLOAD to valid JSON."
        #         )
        # else:
        #     print("Skipping device report: DEVICE_ID is not set.")



    print("\nPerformance tests completed.")


if __name__ == "__main__":
    main()
