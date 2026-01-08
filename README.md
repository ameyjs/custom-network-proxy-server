# Custom Network Proxy Server

A production-quality HTTP/HTTPS forward proxy server implemented from scratch using Python and low-level socket programming. This proxy demonstrates fundamental systems and networking concepts including TCP socket communication, multi-threaded concurrency, HTTP protocol parsing, request forwarding, HTTPS tunneling, configurable filtering, and comprehensive logging.

## Project Overview

This implementation fulfills all requirements of a network proxy server project:

✅ Reliable TCP-based client-server communication using sockets
✅ Concurrent network service handling multiple clients
✅ Correct HTTP request/response parsing and forwarding
✅ Configurable traffic control with logging and filtering
✅ Modular, documented, and testable codebase
✅ HTTPS tunneling via CONNECT method
✅ Content-Length body forwarding
✅ Graceful shutdown handling (SIGINT/SIGTERM)

---

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Build Instructions](#build-instructions)
- [Configuration](#configuration)
- [Testing](#testing)
- [Usage Examples](#usage-examples)
- [Design Documentation](#design-documentation)
- [Implementation Details](#implementation-details)
- [Limitations](#limitations)
- [License](#license)

---

## Features

### Core Functionality
- **HTTP/HTTPS Support**: Full HTTP request/response forwarding and HTTPS CONNECT tunneling
- **Multi-threaded Architecture**: Thread-per-connection model with configurable max connections
- **Content-Length Handling**: Proper request body forwarding based on Content-Length header as specified in HTTP/1.1
- **Domain Filtering**: Configurable blocklist with subdomain matching and case-insensitive comparison
- **Comprehensive Logging**: Detailed request logs with timestamp, client info, destination, status, and byte transfer metrics
- **Automatic Log Rotation**: Configurable size-based rotation with multiple backup files
- **Graceful Shutdown**: SIGINT/SIGTERM handlers that close server socket and display final metrics
- **Connection Limits**: Enforces maximum concurrent connections to prevent resource exhaustion
- **Error Handling**: Proper HTTP error responses (400, 403, 408, 500, 501, 503) with optional detailed messages

### Technical Highlights
- **Pure Python**: Uses only Python standard library (no external dependencies)
- **Socket Programming**: Low-level TCP socket operations (bind, listen, accept, connect, recv, send)
- **Thread Safety**: All shared resources (logs, metrics) protected by locks
- **Configuration-Driven**: INI-based configuration for all server parameters
- **Streaming Forwarding**: Responses not buffered in memory (supports large transfers)
- **Metrics Tracking**: Total requests, allowed, blocked, bytes sent/received

---

## Quick Start

### Prerequisites
- Python 3.7 or higher
- No external packages required

### Installation

```bash
# Clone or download the repository
cd custom-network-proxy-server

# Verify Python installation
python --version

# Check syntax of all modules
make check
```

### Running the Server

```bash
# Start the proxy server
python src/server.py

# Or use make
make run
```

Expected output:
```
============================================================
Proxy Server Configuration
============================================================
Server Address: 0.0.0.0:8888
Listen Backlog: 50
Socket Timeout: 30s
Max Connections: 100
...
============================================================

[+] Logger initialized: logs/proxy.log
[+] Loaded 3 entries from blocklist
[+] Max concurrent connections: 100
[+] Proxy listening on 0.0.0.0:8888
[+] Press Ctrl+C to stop server and view metrics
```

### Testing

```bash
# Run all tests (in another terminal while server is running)
make test

# Or run individual test suites
make test-basic        # Basic functional tests
make test-concurrent   # Concurrent connection tests

# Manual test with curl
curl -x http://localhost:8888 http://httpbin.org/get
```

---

## Project Structure

```
custom-network-proxy-server/
│
├── src/                        # Source code
│   ├── server.py              # Main entry point (187 lines)
│   ├── config.py              # Configuration loader (140 lines)
│   ├── handler.py             # Request orchestration (253 lines)
│   ├── parser.py              # HTTP protocol parser (198 lines)
│   ├── filter.py              # Domain/IP filtering (147 lines)
│   ├── forwarder.py           # Traffic forwarding (184 lines)
│   └── logger.py              # Logging & metrics (200 lines)
│
├── config/                     # Configuration files
│   ├── proxy_config.ini       # Server configuration
│   └── blocked_domains.txt    # Domain/IP blocklist
│
├── tests/                      # Test suite
│   ├── test_basic.sh          # Basic functional tests (bash)
│   └── test_concurrent.py     # Concurrent connection tests (python)
│
├── docs/                       # Documentation
│   └── DESIGN.md              # Design document (800+ lines)
│
├── logs/                       # Runtime logs (generated)
│   ├── proxy.log              # Current log file
│   └── proxy.log.*            # Rotated log files
│
├── Makefile                    # Build and test automation
├── README.md                   # This file
└── .gitignore                 # Git ignore rules
```

---

## Build Instructions

### Using Makefile

```bash
# Check Python syntax
make check

# Run the proxy server
make run

# Run all tests
make test

# Clean generated files
make clean

# Show help
make help
```

### Manual Build/Run

```bash
# No compilation needed (Python is interpreted)

# Verify syntax
python -m py_compile src/*.py

# Run server
python src/server.py

# Run tests (server must be running)
bash tests/test_basic.sh
python tests/test_concurrent.py
```

---

## Configuration

### Configuration File: `config/proxy_config.ini`

```ini
[server]
host = 0.0.0.0           # Bind address (0.0.0.0 = all interfaces)
port = 8888              # Listen port
backlog = 50             # Pending connection queue size
timeout = 30             # Socket timeout (seconds)

[concurrency]
max_connections = 100    # Max concurrent connections (0 = unlimited)

[logging]
log_dir = logs
log_file = proxy.log
max_log_size = 10        # KB
log_rotation_count = 5   # Number of backup files

[filtering]
blocked_list = config/blocked_domains.txt
enable_filtering = true
case_sensitive = false

[forwarding]
buffer_size = 4096       # Bytes
connect_timeout = 10     # Seconds
forward_body = true      # Handle Content-Length bodies

[features]
enable_https = true      # Support CONNECT method
track_sizes = true       # Track byte transfers
detailed_errors = true   # Detailed error messages
```

### Blocklist File: `config/blocked_domains.txt`

```
# Blocked Domains and IPs
# One entry per line
# Lines starting with # are comments
# Blocking a domain also blocks all subdomains

example.com              # Blocks example.com, www.example.com, etc.
badsite.org
192.0.2.5               # Block specific IP
```

---

## Testing

### Test Suite Overview

The project includes comprehensive tests demonstrating:
- ✅ Successful HTTP request forwarding
- ✅ HTTPS CONNECT tunneling
- ✅ Domain blocking (exact and subdomain)
- ✅ POST requests with body forwarding
- ✅ Custom header forwarding
- ✅ Large response handling
- ✅ Concurrent client handling
- ✅ Malformed request handling

### Running Tests

#### Basic Functional Tests (Bash)

```bash
bash tests/test_basic.sh
```

Tests:
1. HTTP GET request
2. HTTP HEAD request
3. HTTPS CONNECT request
4. Blocked domain (exact match)
5. Blocked subdomain
6. HTTP POST with body
7. Custom User-Agent forwarding
8. Large response handling

#### Concurrent Connection Tests (Python)

```bash
python tests/test_concurrent.py
```

Tests:
- 20 concurrent threads
- 5 requests per thread
- 100 total requests
- Measures throughput and success rate

#### Manual Testing with curl

```bash
# HTTP GET
curl -v -x http://localhost:8888 http://httpbin.org/get

# HTTP POST with body
curl -v -x http://localhost:8888 -d "key=value" http://httpbin.org/post

# HTTPS (CONNECT method)
curl -v -x http://localhost:8888 https://www.google.com

# Test blocking
curl -v -x http://localhost:8888 http://example.com
# Expected: HTTP 403 Forbidden

# Test subdomain blocking
curl -v -x http://localhost:8888 http://www.example.com
# Expected: HTTP 403 Forbidden
```

### Viewing Logs

```bash
# Tail logs in real-time
tail -f logs/proxy.log

# View entire log
cat logs/proxy.log

# Search for blocked requests
grep BLOCKED logs/proxy.log

# Count requests by type
grep ALLOWED logs/proxy.log | wc -l
grep BLOCKED logs/proxy.log | wc -l
```

---

## Usage Examples

### Configure Browser

#### Firefox
1. Settings → Network Settings → Manual proxy configuration
2. HTTP Proxy: `localhost`, Port: `8888`
3. Check "Also use this proxy for HTTPS"
4. Click OK

#### Chrome/Edge (Command Line)
```bash
chrome.exe --proxy-server="localhost:8888"
```

### Python Requests Library

```python
import requests

proxies = {
    'http': 'http://localhost:8888',
    'https': 'http://localhost:8888',
}

# HTTP request
response = requests.get('http://httpbin.org/ip', proxies=proxies)
print(response.json())

# HTTPS request
response = requests.get('https://httpbin.org/headers', proxies=proxies)
print(response.json())
```

### curl Examples

```bash
# Basic GET
curl -x http://localhost:8888 http://httpbin.org/get

# With custom headers
curl -x http://localhost:8888 -H "X-Custom: value" http://httpbin.org/headers

# POST with JSON
curl -x http://localhost:8888 -X POST -H "Content-Type: application/json" \
  -d '{"key":"value"}' http://httpbin.org/post

# Download file
curl -x http://localhost:8888 -O http://example.com/file.zip

# Follow redirects
curl -x http://localhost:8888 -L http://example.com
```

---

## Design Documentation

### Architecture Overview

The proxy server follows a modular architecture with clear separation of concerns:

```
┌──────────────┐
│ Client       │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────┐
│ server.py                        │
│  • Socket initialization         │
│  • Accept loop                   │
│  • Thread spawning               │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│ handler.py                       │
│  • Request parsing               │
│  • Filtering                     │
│  • Routing (HTTP/CONNECT)        │
└──┬────────┬──────────┬───────────┘
   │        │          │
   ▼        ▼          ▼
┌────────┐ ┌─────┐  ┌────────┐
│parser  │ │filter│ │logger  │
└────────┘ └─────┘  └────────┘
   │
   ▼
┌──────────────────────────────────┐
│ forwarder.py                     │
│  • HTTP forwarding               │
│  • HTTPS tunneling               │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────┐
│ Destination  │
│ Server       │
└──────────────┘
```

### Concurrency Model

**Thread-per-Connection**
- Main thread runs accept loop
- Each client connection spawns a worker thread
- Daemon threads (auto-cleanup)
- Semaphore controls max connections
- Thread-safe logging and metrics

See [docs/DESIGN.md](docs/DESIGN.md) for complete architecture documentation.

---

## Implementation Details

### HTTP Request Parsing

Implements proper header accumulation as recommended in project specifications:

```python
def recv_http_request(sock):
    """Accumulate data until \\r\\n\\r\\n terminator found."""
    data = b""
    while HEADER_TERMINATOR not in data:
        chunk = sock.recv(BUFFER_SIZE)
        if not chunk:
            break
        data += chunk
    return data
```

### Content-Length Body Forwarding

Handles request bodies as specified in HTTP/1.1:

```python
if content_length > 0:
    body = recv_request_body(client_sock, content_length)
    server_sock.sendall(body)
```

### HTTPS CONNECT Tunneling

Bidirectional forwarding without TLS inspection:

```python
1. Receive CONNECT request
2. Connect to destination:port
3. Send "HTTP/1.1 200 Connection Established"
4. Create two threads:
   - Thread A: client → server (encrypted data)
   - Thread B: server → client (encrypted data)
5. Forward bytes without inspection
```

### Error Response Generation

Proper HTTP error responses with configurable detail:

```python
send_error_response(
    client_sock,
    status_code=403,
    status_message="Forbidden",
    body_message="Access to example.com blocked by proxy policy"
)
```

### Logging Format

```
[2026-01-07 14:30:15] ('127.0.0.1', 54321) → google.com:443 | CONNECT | ALLOWED | 200 | ↑1024B ↓2048B
```

Fields:
- Timestamp
- Client (IP, port)
- Destination host:port
- HTTP method
- Status (ALLOWED, BLOCKED, ERROR, TIMEOUT, REFUSED)
- HTTP response code
- Bytes sent/received

---

## Limitations

### Known Limitations

1. **Scalability**: Thread-per-connection model doesn't scale to thousands of concurrent clients
2. **HTTP/1.1 Only**: No HTTP/2 or HTTP/3 support
3. **No Caching**: Every request forwarded to origin server
4. **IPv4 Only**: No IPv6 support (AF_INET only)
5. **Chunked Transfer**: Not explicitly handled (transparent forwarding)

### Security Limitations

⚠️ **Not for Production Use**

- ❌ No authentication (anyone can use the proxy)
- ❌ No encryption between client and proxy
- ❌ No rate limiting (vulnerable to DoS)
- ❌ Simple text-based blocklist
- ❌ No TLS inspection capability

**Deployment Recommendations:**
- Use in trusted, controlled environments only
- Deploy behind firewall
- Do NOT expose to public internet
- Do NOT use for sensitive production traffic

### Future Enhancements

- Async I/O (asyncio) for better scalability
- HTTP/2 and WebSocket support
- Response caching with LRU eviction
- Authentication (Basic Auth, tokens)
- Rate limiting per client
- IPv6 dual-stack support
- Metrics dashboard

---

## Design Document

For complete architecture details, see **[docs/DESIGN.md](docs/DESIGN.md)**

Contents:
- High-level architecture diagrams
- Component descriptions
- Concurrency model and rationale
- Data flow for HTTP and HTTPS
- Error handling strategies
- Security considerations
- Limitations and future work

---

## Project Deliverables

This project includes all required deliverables:

### ✅ Source Code
- Complete, documented implementation in `src/`
- 6 modular Python files
- ~1,300 lines of code
- Pure Python standard library

### ✅ Build Instructions
- **Makefile** with targets: check, run, test, clean, help
- Manual build instructions in this README
- No dependencies to install

### ✅ Configuration Files
- **config/proxy_config.ini** - Server configuration
- **config/blocked_domains.txt** - Filtering rules

### ✅ Design Document
- **docs/DESIGN.md** - Complete architecture documentation
- High-level diagrams
- Concurrency model rationale
- Data flow descriptions
- Error handling and security analysis

### ✅ Test Artifacts
- **tests/test_basic.sh** - Functional test script
- **tests/test_concurrent.py** - Concurrent connection tests
- Test results in terminal output
- Sample logs in `logs/` directory

### ✅ Demonstration Materials
- Usage examples in this README
- curl command examples
- Browser configuration instructions
- Log samples

---

## Development

### Adding to Blocklist

Edit `config/blocked_domains.txt`:
```
malicious-site.com
ads.example.net
```

Restart server for changes to take effect.

### Modifying Configuration

Edit `config/proxy_config.ini`:
```ini
[server]
port = 9000              # Change port

[concurrency]
max_connections = 200    # Increase limit
```

Restart server for changes to take effect.

### Viewing Metrics

Press `Ctrl+C` to gracefully shutdown and view metrics:

```
============================================================
Proxy Server Metrics Summary
============================================================
Total Requests:    150
Allowed:           145
Blocked:           5
Bytes Sent:        512,340 (500.33 KB)
Bytes Received:    2,048,576 (2.00 MB)
============================================================
```

---

## License

This is an educational project developed for academic purposes.

---

## References

### Project Specifications
- Socket programming: `socket(2)`, `bind(2)`, `listen(2)`, `accept(2)`, `connect(2)`, `recv(2)`, `send(2)`
- Threading: `pthread` (C), `threading` (Python)
- HTTP/1.1: RFC 2616, RFC 7230-7235
- CONNECT method: RFC 7231 Section 4.3.6

### Testing Tools
- `curl` - Command-line HTTP client with proxy support
- `requests` - Python HTTP library
- Browser developer tools

### Documentation
- Python socket module: https://docs.python.org/3/library/socket.html
- Python threading module: https://docs.python.org/3/library/threading.html
- Python configparser: https://docs.python.org/3/library/configparser.html

---

## Contact & Support

For questions or issues:
1. Check [docs/DESIGN.md](docs/DESIGN.md) for architecture details
2. Review test scripts in `tests/` for usage examples
3. Examine log files in `logs/` for debugging

---

**Version**: 2.0
**Last Updated**: 2026-01-07
**Python Version**: 3.7+
**Status**: Complete and Tested
