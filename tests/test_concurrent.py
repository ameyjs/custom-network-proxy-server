#!/usr/bin/env python3
"""
Concurrent connection test for the proxy server.
Tests the proxy's ability to handle multiple simultaneous requests.
"""

import requests
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

PROXY_URL = "http://localhost:8888"
NUM_CONCURRENT = 20
NUM_REQUESTS_PER_THREAD = 5

proxies = {
    'http': PROXY_URL,
    'https': PROXY_URL,
}

results = {
    'success': 0,
    'failed': 0,
    'total_time': 0
}

results_lock = threading.Lock()


def make_request(thread_id, request_id):
    """
    Make a single HTTP request through the proxy.

    Args:
        thread_id: Thread identifier
        request_id: Request identifier within thread

    Returns:
        tuple: (success, elapsed_time)
    """
    start_time = time.time()
    try:
        response = requests.get(
            'http://httpbin.org/delay/1',
            proxies=proxies,
            timeout=10
        )
        elapsed = time.time() - start_time

        if response.status_code == 200:
            return True, elapsed
        else:
            print(f"[Thread {thread_id}, Request {request_id}] "
                  f"HTTP {response.status_code}")
            return False, elapsed

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[Thread {thread_id}, Request {request_id}] Error: {e}")
        return False, elapsed


def worker(thread_id):
    """
    Worker function that makes multiple requests.

    Args:
        thread_id: Thread identifier

    Returns:
        tuple: (successes, failures, total_time)
    """
    successes = 0
    failures = 0
    total_time = 0

    for i in range(NUM_REQUESTS_PER_THREAD):
        success, elapsed = make_request(thread_id, i + 1)
        if success:
            successes += 1
        else:
            failures += 1
        total_time += elapsed

    return successes, failures, total_time


def main():
    """Run concurrent proxy tests."""
    print("=" * 60)
    print("Custom Network Proxy Server - Concurrent Connection Test")
    print("=" * 60)
    print(f"Proxy: {PROXY_URL}")
    print(f"Concurrent threads: {NUM_CONCURRENT}")
    print(f"Requests per thread: {NUM_REQUESTS_PER_THREAD}")
    print(f"Total requests: {NUM_CONCURRENT * NUM_REQUESTS_PER_THREAD}")
    print("=" * 60)
    print("")

    print("Starting concurrent requests...")
    start_time = time.time()

    # Use ThreadPoolExecutor for concurrent requests
    with ThreadPoolExecutor(max_workers=NUM_CONCURRENT) as executor:
        futures = [executor.submit(worker, i) for i in range(NUM_CONCURRENT)]

        for future in as_completed(futures):
            successes, failures, thread_time = future.result()
            with results_lock:
                results['success'] += successes
                results['failed'] += failures
                results['total_time'] += thread_time

    total_elapsed = time.time() - start_time

    # Print results
    print("")
    print("=" * 60)
    print("Results")
    print("=" * 60)
    print(f"Successful requests: {results['success']}")
    print(f"Failed requests:     {results['failed']}")
    print(f"Total requests:      {results['success'] + results['failed']}")
    print(f"Wall clock time:     {total_elapsed:.2f} seconds")
    print(f"Avg request time:    {results['total_time'] / (results['success'] + results['failed']):.2f} seconds")
    print(f"Requests per second: {(results['success'] + results['failed']) / total_elapsed:.2f}")
    print("=" * 60)

    if results['failed'] == 0:
        print("✓ All concurrent requests succeeded!")
        return 0
    else:
        print(f"✗ {results['failed']} requests failed")
        return 1


if __name__ == "__main__":
    try:
        exit(main())
    except KeyboardInterrupt:
        print("\n[!] Test interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n[!] Test error: {e}")
        exit(1)
