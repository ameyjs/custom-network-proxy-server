#!/usr/bin/env python3
"""
Simple test script to verify proxy server functionality.
Run this after starting the proxy server.
"""

import socket


def test_http_request():
    """Test basic HTTP request through proxy."""
    print("\n[TEST 1] Testing HTTP request to httpbin.org...")
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("localhost", 8888))

        request = (
            b"GET http://httpbin.org/get HTTP/1.1\r\n"
            b"Host: httpbin.org\r\n"
            b"Connection: close\r\n"
            b"\r\n"
        )

        client.sendall(request)
        response = client.recv(4096).decode("utf-8", errors="ignore")

        if "200 OK" in response or "HTTP" in response:
            print("✓ HTTP request successful!")
            print(f"Response preview: {response[:200]}...")
        else:
            print("✗ Unexpected response")

        client.close()
    except Exception as e:
        print(f"✗ Error: {e}")


def test_blocked_domain():
    """Test blocked domain filtering."""
    print("\n[TEST 2] Testing blocked domain (example.com)...")
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("localhost", 8888))

        request = (
            b"GET http://example.com/ HTTP/1.1\r\n"
            b"Host: example.com\r\n"
            b"Connection: close\r\n"
            b"\r\n"
        )

        client.sendall(request)
        response = client.recv(4096).decode("utf-8", errors="ignore")

        if "403 Forbidden" in response:
            print("✓ Domain blocking works correctly!")
            print(f"Response: {response[:150]}...")
        else:
            print("✗ Domain blocking failed")
            print(f"Response: {response[:200]}")

        client.close()
    except Exception as e:
        print(f"✗ Error: {e}")


def test_https_connect():
    """Test HTTPS CONNECT tunneling."""
    print("\n[TEST 3] Testing HTTPS CONNECT to google.com...")
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("localhost", 8888))

        request = b"CONNECT google.com:443 HTTP/1.1\r\n\r\n"

        client.sendall(request)
        response = client.recv(4096).decode("utf-8", errors="ignore")

        if "200 Connection Established" in response:
            print("✓ HTTPS CONNECT successful!")
            print(f"Response: {response}")
        else:
            print("✗ CONNECT failed")
            print(f"Response: {response}")

        client.close()
    except Exception as e:
        print(f"✗ Error: {e}")


def test_metrics():
    """Display current proxy metrics."""
    print("\n[TEST 4] Checking metrics...")
    try:
        import sys
        sys.path.insert(0, 'src')
        from logger import get_metrics

        metrics = get_metrics()
        print(f"✓ Metrics retrieved:")
        print(f"  Total requests: {metrics['total']}")
        print(f"  Allowed: {metrics['allowed']}")
        print(f"  Blocked: {metrics['blocked']}")
    except Exception as e:
        print(f"✗ Error: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("Custom Network Proxy Server - Test Suite")
    print("=" * 60)
    print("\nMake sure the proxy server is running on localhost:8888")
    print("Start it with: python src/server.py")
    input("\nPress Enter to start tests...")

    test_http_request()
    test_blocked_domain()
    test_https_connect()
    test_metrics()

    print("\n" + "=" * 60)
    print("Tests completed! Check logs/proxy.log for details.")
    print("=" * 60)
