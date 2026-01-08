# Design Document: Custom Network Proxy Server

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [High-Level Architecture](#high-level-architecture)
3. [Component Descriptions](#component-descriptions)
4. [Concurrency Model](#concurrency-model)
5. [Data Flow](#data-flow)
6. [Error Handling](#error-handling)
7. [Security Considerations](#security-considerations)
8. [Limitations and Future Work](#limitations-and-future-work)

---

## Executive Summary

This document describes the design and implementation of a custom HTTP/HTTPS forward proxy server built from scratch using Python. The proxy server implements reliable TCP-based client-server communication, multi-threaded request handling, HTTP protocol parsing and forwarding, configurable traffic filtering, and comprehensive logging.

### Key Features
- **HTTP/HTTPS Support**: Full HTTP request/response forwarding and HTTPS CONNECT tunneling
- **Multi-threaded Architecture**: Thread-per-connection model with configurable connection limits
- **Content-Length Handling**: Proper request body forwarding based on Content-Length header
- **Domain Filtering**: Configurable blocklist with subdomain matching
- **Comprehensive Logging**: Detailed request logs with byte transfer metrics
- **Graceful Shutdown**: SIGINT/SIGTERM handlers for clean server shutdown
- **Configuration-Driven**: INI-based configuration for all server parameters

### Technical Stack
- **Language**: Python 3.7+
- **Dependencies**: Python standard library only (socket, threading, configparser, etc.)
- **Concurrency**: Thread-per-connection model
- **Protocol**: HTTP/1.1 with CONNECT method for HTTPS

---

## High-Level Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                       CLIENT APPLICATION                        │
│                  (Browser, curl, wget, etc.)                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTP/HTTPS Requests
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PROXY SERVER (Port 8888)                     │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              server.py - Main Entry Point                 │ │
│  │  • Socket initialization & binding                        │ │
│  │  • Accept loop with graceful shutdown                     │ │
│  │  • Thread spawning & connection management                │ │
│  └────────────────────────┬──────────────────────────────────┘ │
│                           │                                     │
│                           ▼                                     │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │               config.py - Configuration                   │ │
│  │  • Load settings from proxy_config.ini                    │ │
│  │  • Initialize logger and filter                           │ │
│  └───────────────────────────────────────────────────────────┘ │
│                           │                                     │
│                           ▼                                     │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │           handler.py - Request Orchestrator               │ │
│  │  • Receive & parse HTTP requests                          │ │
│  │  • Apply filtering rules                                  │ │
│  │  • Route to appropriate handler                           │ │
│  │  • Error response generation                              │ │
│  └───┬───────────────┬───────────────────┬───────────────────┘ │
│      │               │                   │                     │
│      ▼               ▼                   ▼                     │
│  ┌────────┐     ┌──────────┐      ┌──────────┐               │
│  │parser  │     │filter    │      │logger    │               │
│  │        │     │          │      │          │               │
│  │• Recv  │     │• Check   │      │• Log     │               │
│  │• Parse │     │• Block   │      │• Metrics │               │
│  │• Extract│    │• Subdomain│     │• Rotate  │               │
│  └────────┘     └──────────┘      └──────────┘               │
│      │                                                         │
│      ▼                                                         │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │            forwarder.py - Traffic Forwarding              │ │
│  │  • HTTP: Request/response forwarding                      │ │
│  │  • HTTPS: Bidirectional tunnel creation                   │ │
│  │  • Byte tracking for metrics                              │ │
│  └────────────────────────┬──────────────────────────────────┘ │
└─────────────────────────────┼────────────────────────────────────┘
                              │
                              │ Forwarded Requests
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DESTINATION SERVERS                          │
│                        (Internet)                               │
└─────────────────────────────────────────────────────────────────┘
```

### Module Dependency Graph

```
server.py
   ├── config.py
   ├── handler.py
   │   ├── parser.py
   │   ├── filter.py
   │   ├── forwarder.py
   │   └── logger.py
   ├── filter.py
   └── logger.py
```

---

## Component Descriptions

### 1. server.py - Main Server Module

**Responsibilities:**
- Initialize TCP server socket
- Bind to configured host:port
- Accept incoming client connections
- Spawn worker threads for each connection
- Implement graceful shutdown on SIGINT/SIGTERM
- Enforce maximum connection limits

**Key Functions:**
- `start_server()`: Main server initialization and accept loop
- `signal_handler()`: Graceful shutdown handler
- `handle_client_wrapper()`: Thread wrapper for connection management

**Socket Configuration:**
- `SO_REUSEADDR`: Enabled for quick server restarts
- Timeout: 1 second (allows periodic shutdown check)
- Backlog: 50 pending connections (configurable)

### 2. config.py - Configuration Management

**Responsibilities:**
- Load configuration from `config/proxy_config.ini`
- Provide default values for missing settings
- Validate configuration parameters
- Expose configuration to other modules

**Configuration Categories:**
- **Server**: host, port, backlog, timeout
- **Concurrency**: max_connections
- **Logging**: log directory, file size, rotation count
- **Filtering**: blocklist file, case sensitivity
- **Forwarding**: buffer size, connect timeout
- **Features**: HTTPS support, size tracking, detailed errors

### 3. handler.py - Request Handler

**Responsibilities:**
- Receive HTTP request headers from client
- Parse request to extract method, host, port
- Check if destination is blocked
- Route to HTTP or CONNECT handler
- Generate error responses
- Log all requests with metrics

**Request Processing Flow:**
1. Receive request headers (`recv_http_request`)
2. Parse request (`parse_http_request`)
3. Increment total requests metric
4. Check blocklist (`is_blocked`)
5. If blocked: Send 403, log, return
6. If CONNECT: Call `handle_connect`
7. If HTTP: Call `handle_http`
8. Close client socket

**Error Responses:**
- 400 Bad Request: Invalid HTTP syntax
- 403 Forbidden: Blocked by policy
- 408 Request Timeout: Client timeout
- 500 Internal Server Error: Server error
- 501 Not Implemented: HTTPS disabled
- 503 Service Unavailable: Max connections

### 4. parser.py - HTTP Protocol Parser

**Responsibilities:**
- Receive HTTP request headers in chunks
- Detect complete headers (\\r\\n\\r\\n terminator)
- Parse request line (method, target, version)
- Extract headers into dictionary
- Parse Content-Length header
- Support absolute and relative URLs
- Extract response status codes

**Key Functions:**
- `recv_http_request()`: Accumulate headers until complete
- `parse_http_request()`: Parse headers and extract metadata
- `recv_request_body()`: Receive body based on Content-Length
- `extract_response_status()`: Extract HTTP status from response

**Parsing Logic:**
- CONNECT: Extract host:port from target
- HTTP with Host header: Use Host header
- HTTP with absolute URL: Parse URL
- Default ports: 80 (HTTP), 443 (HTTPS)

### 5. filter.py - Domain Filtering

**Responsibilities:**
- Load blocklist from configuration file
- Check if host is blocked
- Support subdomain matching
- Runtime blocklist modification (add/remove)
- Case-insensitive matching (configurable)

**Blocklist Format:**
```
# Comment lines start with #
example.com      # Blocks example.com and *.example.com
192.0.2.5        # Blocks specific IP
```

**Matching Algorithm:**
1. Convert host to lowercase (if case-insensitive)
2. Check exact match in blocklist
3. Check each parent domain (subdomain matching)
4. Return True if any match found

**Example:**
- Blocklist contains: `example.com`
- Blocks: `example.com`, `www.example.com`, `api.example.com`
- Allows: `notexample.com`, `example.org`

### 6. forwarder.py - Traffic Forwarding

**Responsibilities:**
- Forward HTTP requests to destination
- Receive and forward HTTP responses
- Create bidirectional tunnels for HTTPS
- Track bytes sent and received
- Handle Content-Length body forwarding
- Extract response status codes

**HTTP Forwarding (`forward_http`):**
1. Connect to destination server
2. Send request headers
3. If Content-Length > 0, receive and forward body
4. Receive response (streaming, not buffered)
5. Extract status code from first chunk
6. Forward response to client
7. Track all bytes transferred

**HTTPS Tunneling (`tunnel`):**
1. Create two threads for bidirectional forwarding
2. Thread 1: Client → Server
3. Thread 2: Server → Client
4. Both threads track bytes
5. Wait for both threads to complete
6. Return byte counts

### 7. logger.py - Logging and Metrics

**Responsibilities:**
- Thread-safe log file writing
- Automatic log rotation by size
- Request metrics tracking
- Byte transfer tracking
- Formatted log entries

**Log Entry Format:**
```
[YYYY-MM-DD HH:MM:SS] (ip, port) → host:port | METHOD | STATUS | HTTP_CODE | ↑XB ↓YB
```

**Example:**
```
[2026-01-07 14:30:15] ('127.0.0.1', 54321) → google.com:443 | CONNECT | ALLOWED | 200 | ↑1024B ↓2048B
[2026-01-07 14:30:16] ('127.0.0.1', 54322) → example.com:80 | GET | BLOCKED | 403
```

**Log Rotation:**
- Triggers when log exceeds configured size (default: 10KB)
- Keeps N backup files (default: 5)
- Shifts existing backups: .1 → .2, .2 → .3, etc.
- Deletes oldest backup

**Metrics Tracked:**
- Total requests
- Allowed requests
- Blocked requests
- Bytes sent to servers
- Bytes received from servers

---

## Concurrency Model

### Thread-Per-Connection Model

**Architecture:**
```
Main Thread
   │
   ├── Accept Loop
   │   └── For each connection:
   │       └── Spawn Worker Thread
   │           ├── handle_client_wrapper()
   │           │   ├── Acquire semaphore slot
   │           │   ├── handle_client()
   │           │   │   ├── Recv & parse request
   │           │   │   ├── Apply filtering
   │           │   │   ├── Forward/tunnel
   │           │   │   └── Log metrics
   │           │   └── Release semaphore slot
   │           └── Exit
   │
   └── Signal Handler (SIGINT/SIGTERM)
       └── Graceful shutdown
```

**Thread Types:**

1. **Main Thread**
   - Runs accept loop
   - Checks shutdown event every 1 second
   - Spawns worker threads
   - Handles signals

2. **Worker Threads** (one per client)
   - Daemon threads (auto-terminate)
   - Handle single client request
   - Close client socket on exit
   - Release semaphore slot

3. **Tunnel Threads** (two per HTTPS connection)
   - Created by `tunnel()` function
   - One for client→server
   - One for server→client
   - Daemon threads
   - Run until connection closes

**Synchronization:**

1. **Semaphore** (`active_connections`)
   - Controls max concurrent connections
   - Acquired before handling client
   - Released after client completes
   - Non-blocking acquire (reject if full)

2. **Locks**
   - `log_lock`: Protects log file writes
   - `metrics_lock`: Protects metrics updates
   - `DataTracker.lock`: Per-tunnel byte tracking

**Rationale:**

✅ **Advantages:**
- Simple to implement and understand
- No shared state between requests
- Natural request isolation
- Works well for moderate load

❌ **Limitations:**
- Thread overhead for many connections
- Not scalable to thousands of concurrent clients
- Memory per thread (stack space)

**Alternative Considered:**
- **Event-driven (asyncio)**: More scalable but complex
- **Thread pool**: Better resource control but queuing latency
- **Decision**: Thread-per-connection chosen for simplicity and project scope

---

## Data Flow

### HTTP Request Flow

```
1. Client sends HTTP request
      │
      ▼
2. Server accepts connection
      │
      ▼
3. Spawn worker thread
      │
      ▼
4. recv_http_request() - Accumulate headers
      │
      ├─ Read chunks until \\r\\n\\r\\n
      │
      ▼
5. parse_http_request() - Extract metadata
      │
      ├─ Method: GET, POST, etc.
      ├─ Host: example.com
      ├─ Port: 80
      ├─ Content-Length: N
      │
      ▼
6. is_blocked() - Check filter
      │
      ├─ If blocked ──→ Send 403, log, exit
      │
      ▼
7. forward_http()
      │
      ├─ Connect to destination
      ├─ Send request headers
      ├─ If Content-Length > 0:
      │   ├─ recv_request_body()
      │   └─ Forward body
      ├─ Receive response (streaming)
      ├─ Extract status code
      ├─ Forward response to client
      └─ Track bytes
      │
      ▼
8. log_request() - Write to log
      │
      ▼
9. Close sockets, exit thread
```

### HTTPS CONNECT Flow

```
1. Client sends CONNECT request
      │
      ▼
2. Server accepts connection
      │
      ▼
3. Spawn worker thread
      │
      ▼
4. recv_http_request()
      │
      ▼
5. parse_http_request()
      │
      ├─ Method: CONNECT
      ├─ Host: google.com
      ├─ Port: 443
      │
      ▼
6. is_blocked() - Check filter
      │
      ├─ If blocked ──→ Send 403, log, exit
      │
      ▼
7. handle_connect()
      │
      ├─ Connect to destination:443
      ├─ Send "HTTP/1.1 200 Connection Established"
      │
      ▼
8. tunnel() - Bidirectional forwarding
      │
      ├─ Thread A: client → server
      │   └─ Loop: recv, sendall, track bytes
      │
      ├─ Thread B: server → client
      │   └─ Loop: recv, sendall, track bytes
      │
      └─ Wait for both threads
      │
      ▼
9. log_request() - Write with byte counts
      │
      ▼
10. Close sockets, exit threads
```

### Blocked Request Flow

```
1. Client sends request to blocked domain
      │
      ▼
2. parse_http_request()
      │
      ▼
3. is_blocked() returns True
      │
      ▼
4. send_error_response(403, "Forbidden")
      │
      ├─ Build HTML error page
      ├─ Set Content-Length
      ├─ Send response
      │
      ▼
5. log_request(status="BLOCKED", code=403)
      │
      ▼
6. increment_blocked()
      │
      ▼
7. Close socket, exit thread
```

---

## Error Handling

### Error Categories

#### 1. Client Errors (4xx)

**400 Bad Request**
- Trigger: Invalid HTTP syntax, missing required headers
- Action: Send error response, log, close connection
- Example: Malformed request line

**403 Forbidden**
- Trigger: Destination in blocklist
- Action: Send detailed error page, log BLOCKED status
- Example: Request to example.com (blocked)

**408 Request Timeout**
- Trigger: Socket timeout while receiving request
- Action: Send timeout response, log, close connection
- Example: Client sends headers too slowly

#### 2. Server Errors (5xx)

**500 Internal Server Error**
- Trigger: Unexpected exception in request handling
- Action: Send error response (detailed if configured), log
- Example: Connection to destination fails unexpectedly

**501 Not Implemented**
- Trigger: HTTPS disabled in config but CONNECT received
- Action: Send error response explaining feature disabled
- Example: enable_https = false

**503 Service Unavailable**
- Trigger: Maximum connections reached
- Action: Reject connection immediately, send 503
- Example: 100 concurrent connections (if max=100)

#### 3. Network Errors

**Connection Refused**
- Trigger: Destination server not reachable
- Action: Log "REFUSED" status, return to client
- Example: Server at dest:port not running

**Connection Timeout**
- Trigger: Destination server doesn't respond in time
- Action: Log "TIMEOUT" status, return to client
- Example: Firewall blocking destination

**Socket Errors**
- Trigger: Various socket-level failures
- Action: Log "ERROR" status, close connections
- Example: Client disconnects mid-request

### Error Handling Strategy

**Principle**: Fail safely, log everything, don't crash server

```python
try:
    # Main request handling
    handle_client()
except socket.timeout:
    send_error_response(408, "Request Timeout", ...)
except SpecificException:
    # Handle specific errors
except Exception as e:
    # Catch-all for unexpected errors
    if config.detailed_errors:
        send_error_response(500, ..., f"Error: {e}")
    else:
        send_error_response(500, ..., "An error occurred")
finally:
    # Always cleanup
    close_socket()
    release_resources()
```

**Logging:**
- All errors logged with status (ERROR, TIMEOUT, REFUSED)
- Metrics track failed requests
- Detailed errors optional (security vs. debugging)

---

## Security Considerations

### Implemented Security Measures

✅ **Domain Filtering**
- Blocklist prevents access to specific domains/IPs
- Subdomain matching prevents bypass
- Runtime modification capability

✅ **Request Logging**
- Complete audit trail of all requests
- Client IP, destination, status, bytes tracked
- Log rotation prevents disk exhaustion

✅ **Privacy-Preserving HTTPS**
- CONNECT method tunnels encrypted traffic
- Proxy does not inspect TLS payloads
- End-to-end encryption maintained

✅ **Resource Limits**
- Maximum concurrent connections enforced
- Connection timeout prevents hanging
- Log file size limits

✅ **Input Validation**
- HTTP request parsing validates syntax
- Malformed requests rejected with 400
- Buffer overflow prevention (fixed-size buffers)

✅ **Graceful Degradation**
- Errors don't crash server
- Failed requests logged and tracked
- Client receives proper error response

### Security Limitations

❌ **No Authentication**
- **Risk**: Anyone can use the proxy
- **Mitigation**: Deploy in trusted network only
- **Future**: Add HTTP Basic Auth or token-based auth

❌ **No Encryption to Proxy**
- **Risk**: Traffic between client and proxy is plaintext
- **Mitigation**: Run proxy on localhost or VPN
- **Future**: Add TLS support for client-proxy connection

❌ **No Rate Limiting**
- **Risk**: Denial of service through request flooding
- **Mitigation**: Firewall rules, max connections limit
- **Future**: Implement per-client rate limiting

❌ **No Request Size Limits**
- **Risk**: Large requests could consume memory
- **Mitigation**: Timeout prevents indefinite hangs
- **Future**: Add max request size config

❌ **Simple Blocklist**
- **Risk**: No regex, wildcards, or complex patterns
- **Mitigation**: Subdomain matching helps
- **Future**: Add pattern matching, IP ranges

❌ **No DNS Filtering**
- **Risk**: Client resolves DNS before proxy
- **Mitigation**: Block by hostname in HTTP request
- **Future**: Implement DNS resolution in proxy

❌ **No TLS Inspection**
- **Risk**: Cannot filter HTTPS content
- **Mitigation**: Block by hostname only
- **Note**: This is also a privacy feature

### Deployment Recommendations

**DO:**
- Deploy in trusted, controlled environments
- Use firewall to restrict access to proxy port
- Run with least-privilege user account
- Monitor logs for suspicious activity
- Rotate logs regularly
- Keep blocklist updated

**DON'T:**
- Expose to public internet without authentication
- Use for sensitive traffic over untrusted networks
- Trust client-provided headers for security decisions
- Disable detailed errors in production
- Run as root/administrator

---

## Limitations and Future Work

### Current Limitations

1. **Scalability**
   - Thread-per-connection doesn't scale to 1000s of clients
   - Memory overhead per thread
   - Solution: Migrate to async I/O (asyncio)

2. **HTTP/1.1 Only**
   - No HTTP/2 or HTTP/3 support
   - No WebSocket support
   - Solution: Add protocol version detection

3. **Chunked Transfer Encoding**
   - Not explicitly handled (transparent forwarding)
   - May fail with some edge cases
   - Solution: Implement chunk parsing

4. **Caching**
   - No caching implemented
   - Every request goes to origin
   - Solution: Add LRU cache with cache headers

5. **Keep-Alive**
   - Connections closed after each request
   - No persistent connection pooling
   - Solution: Implement connection reuse

6. **IPv6**
   - Only IPv4 supported (AF_INET)
   - No dual-stack support
   - Solution: Add AF_INET6 support

### Future Enhancements

**Caching (Optional Extension)**
- In-memory LRU cache
- Respect Cache-Control headers
- Configurable cache size
- Cache invalidation

**Authentication (Optional Extension)**
- HTTP Basic Authentication
- Token-based authentication
- Per-user access control
- Usage quotas

**Advanced Filtering**
- Regex pattern matching
- IP range blocking (CIDR)
- Time-based rules
- Category-based filtering

**Monitoring**
- Real-time metrics dashboard
- Prometheus metrics export
- Request analytics
- Alert on anomalies

**Performance**
- Connection pooling
- Async I/O migration
- Response compression
- DNS caching

**Protocol Support**
- HTTP/2 and HTTP/3
- WebSocket proxying
- FTP proxy support
- SOCKS proxy mode

---

## Appendices

### A. Configuration Reference

See `config/proxy_config.ini` for full configuration options.

### B. Log Format Specification

```
[TIMESTAMP] (CLIENT_IP, CLIENT_PORT) → HOST:PORT | METHOD | STATUS | HTTP_CODE | ↑SENT ↓RECEIVED
```

### C. Error Response Format

```html
<!DOCTYPE html>
<html>
<head><title>{CODE} {MESSAGE}</title></head>
<body>
    <div class="error-code">{CODE}</div>
    <h1>{MESSAGE}</h1>
    <div class="message">{DETAILS}</div>
    <hr>
    <p><small>Custom Network Proxy Server</small></p>
</body>
</html>
```

### D. Testing Commands

```bash
# HTTP GET
curl -v -x http://localhost:8888 http://httpbin.org/get

# HTTP POST
curl -v -x http://localhost:8888 -d "key=value" http://httpbin.org/post

# HTTPS
curl -v -x http://localhost:8888 https://www.google.com

# Blocked domain
curl -v -x http://localhost:8888 http://example.com

# Check logs
tail -f logs/proxy.log
```

---

**Document Version**: 1.0
**Last Updated**: 2026-01-07
**Author**: Custom Network Proxy Server Project
