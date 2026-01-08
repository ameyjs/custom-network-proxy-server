#!/usr/bin/env bash
#
# Basic functional tests for the proxy server
# Run this script after starting the proxy server on localhost:8888
#

PROXY="localhost:8888"
PASSED=0
FAILED=0

echo "============================================================"
echo "Custom Network Proxy Server - Basic Tests"
echo "============================================================"
echo "Proxy: $PROXY"
echo ""

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Simple HTTP GET request
echo -n "[TEST 1] HTTP GET request (httpbin.org)... "
RESPONSE=$(curl -s -x http://$PROXY http://httpbin.org/get -w "%{http_code}" -o /dev/null --max-time 10)
if [ "$RESPONSE" == "200" ]; then
    echo -e "${GREEN}PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}FAIL${NC} (Got HTTP $RESPONSE)"
    ((FAILED++))
fi

# Test 2: HTTP HEAD request
echo -n "[TEST 2] HTTP HEAD request (httpbin.org)... "
RESPONSE=$(curl -s -I -x http://$PROXY http://httpbin.org/headers -w "%{http_code}" -o /dev/null --max-time 10)
if [ "$RESPONSE" == "200" ]; then
    echo -e "${GREEN}PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}FAIL${NC} (Got HTTP $RESPONSE)"
    ((FAILED++))
fi

# Test 3: HTTPS CONNECT request
echo -n "[TEST 3] HTTPS CONNECT request (google.com)... "
RESPONSE=$(curl -s -x http://$PROXY https://www.google.com -w "%{http_code}" -o /dev/null --max-time 10)
if [ "$RESPONSE" == "200" ]; then
    echo -e "${GREEN}PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}FAIL${NC} (Got HTTP $RESPONSE)"
    ((FAILED++))
fi

# Test 4: Blocked domain (example.com)
echo -n "[TEST 4] Blocked domain (example.com)... "
RESPONSE=$(curl -s -x http://$PROXY http://example.com -w "%{http_code}" -o /dev/null --max-time 10)
if [ "$RESPONSE" == "403" ]; then
    echo -e "${GREEN}PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}FAIL${NC} (Expected HTTP 403, got $RESPONSE)"
    ((FAILED++))
fi

# Test 5: Blocked subdomain (www.example.com)
echo -n "[TEST 5] Blocked subdomain (www.example.com)... "
RESPONSE=$(curl -s -x http://$PROXY http://www.example.com -w "%{http_code}" -o /dev/null --max-time 10)
if [ "$RESPONSE" == "403" ]; then
    echo -e "${GREEN}PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}FAIL${NC} (Expected HTTP 403, got $RESPONSE)"
    ((FAILED++))
fi

# Test 6: POST request with body
echo -n "[TEST 6] HTTP POST with body (httpbin.org)... "
RESPONSE=$(curl -s -x http://$PROXY -X POST -d "test=data" http://httpbin.org/post -w "%{http_code}" -o /dev/null --max-time 10)
if [ "$RESPONSE" == "200" ]; then
    echo -e "${GREEN}PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}FAIL${NC} (Got HTTP $RESPONSE)"
    ((FAILED++))
fi

# Test 7: User-Agent header forwarding
echo -n "[TEST 7] Custom User-Agent forwarding... "
RESPONSE=$(curl -s -x http://$PROXY -A "ProxyTest/1.0" http://httpbin.org/user-agent -w "%{http_code}" -o /tmp/proxy_test_ua.txt --max-time 10)
if [ "$RESPONSE" == "200" ] && grep -q "ProxyTest" /tmp/proxy_test_ua.txt; then
    echo -e "${GREEN}PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}FAIL${NC}"
    ((FAILED++))
fi
rm -f /tmp/proxy_test_ua.txt

# Test 8: Large response handling
echo -n "[TEST 8] Large response handling (1KB)... "
RESPONSE=$(curl -s -x http://$PROXY http://httpbin.org/bytes/1024 -w "%{http_code}" -o /dev/null --max-time 10)
if [ "$RESPONSE" == "200" ]; then
    echo -e "${GREEN}PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}FAIL${NC} (Got HTTP $RESPONSE)"
    ((FAILED++))
fi

echo ""
echo "============================================================"
echo "Test Results"
echo "============================================================"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo "Total:  $((PASSED + FAILED))"
echo "============================================================"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed.${NC}"
    exit 1
fi
