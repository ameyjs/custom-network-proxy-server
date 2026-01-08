"""
Request handler module for the proxy server.
Orchestrates request processing, filtering, and forwarding.
"""

import socket
from parser import recv_http_request, parse_http_request
from filter import is_blocked
from forwarder import tunnel, forward_http
from logger import (log_request, increment_total, increment_allowed,
                   increment_blocked, add_bytes_sent, add_bytes_received)


def handle_client(client_sock, client_addr, config):
    """
    Handle incoming client connection.
    Orchestrates the complete request processing flow.

    Args:
        client_sock: Client socket
        client_addr: Client address tuple (ip, port)
        config: ProxyConfig instance

    Flow:
        1. Receive and parse HTTP request
        2. Increment total request metrics
        3. Check if destination is blocked
        4. If blocked: Send 403 Forbidden and log
        5. If allowed: Route to appropriate handler (CONNECT or HTTP)
        6. Log request with detailed metrics
        7. Close client socket
    """
    try:
        # Set socket timeout from config
        if config.timeout > 0:
            client_sock.settimeout(config.timeout)

        # Receive HTTP request
        request_data = recv_http_request(client_sock, config.buffer_size)
        if not request_data:
            return

        # Parse request
        parsed = parse_http_request(request_data)
        if not parsed:
            send_error_response(client_sock, 400, "Bad Request",
                              "Invalid HTTP request", config)
            return

        # Increment total requests
        increment_total()

        host = parsed["host"]
        port = parsed["port"]
        method = parsed["method"]

        # Check if destination is blocked
        if is_blocked(host):
            # Send 403 Forbidden response
            send_error_response(client_sock, 403, "Forbidden",
                              f"Access to {host} is blocked by proxy policy",
                              config)

            # Log and increment blocked counter
            log_request(client_addr, host, port, method, "BLOCKED",
                       response_status=403)
            increment_blocked()
            return

        # Request is allowed
        increment_allowed()

        # Route based on request method
        if method == "CONNECT":
            # HTTPS tunneling
            if config.enable_https:
                handle_connect(client_sock, client_addr, parsed, config)
            else:
                send_error_response(client_sock, 501, "Not Implemented",
                                  "HTTPS tunneling is disabled", config)
        else:
            # Regular HTTP forwarding
            handle_http(client_sock, client_addr, parsed, config)

    except socket.timeout:
        send_error_response(client_sock, 408, "Request Timeout",
                          "Client request timed out", config)
    except Exception as e:
        if config.detailed_errors:
            send_error_response(client_sock, 500, "Internal Server Error",
                              f"Proxy error: {str(e)}", config)
        else:
            send_error_response(client_sock, 500, "Internal Server Error",
                              "An error occurred", config)
    finally:
        # Always close client socket
        try:
            client_sock.close()
        except:
            pass


def handle_connect(client_sock, client_addr, parsed, config):
    """
    Handle HTTPS CONNECT request.
    Establishes tunnel between client and destination server.

    Args:
        client_sock: Client socket
        client_addr: Client address tuple
        parsed: Parsed request dictionary
        config: ProxyConfig instance
    """
    server_sock = None
    bytes_sent = 0
    bytes_received = 0

    try:
        host = parsed["host"]
        port = parsed["port"]

        # Connect to destination server
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.settimeout(config.connect_timeout)
        server_sock.connect((host, port))

        # Send 200 Connection Established to client
        connect_response = b"HTTP/1.1 200 Connection Established\r\n\r\n"
        client_sock.sendall(connect_response)

        # Create bidirectional tunnel and track bytes
        bytes_sent, bytes_received = tunnel(client_sock, server_sock,
                                           config.buffer_size)

        # Update global metrics
        add_bytes_sent(bytes_sent)
        add_bytes_received(bytes_received)

        # Log the connection with metrics
        log_request(client_addr, host, port, "CONNECT", "ALLOWED",
                   response_status=200, bytes_sent=bytes_sent,
                   bytes_received=bytes_received)

    except socket.timeout:
        log_request(client_addr, host, port, "CONNECT", "TIMEOUT")
    except ConnectionRefusedError:
        log_request(client_addr, host, port, "CONNECT", "REFUSED")
    except Exception:
        log_request(client_addr, host, port, "CONNECT", "ERROR")
    finally:
        if server_sock:
            try:
                server_sock.close()
            except:
                pass


def handle_http(client_sock, client_addr, parsed, config):
    """
    Handle regular HTTP request.
    Forwards request to destination and returns response.

    Args:
        client_sock: Client socket
        client_addr: Client address tuple
        parsed: Parsed request dictionary
        config: ProxyConfig instance
    """
    try:
        host = parsed["host"]
        port = parsed["port"]
        method = parsed["method"]

        # Forward request and response, tracking bytes
        response_status, bytes_sent, bytes_received = forward_http(
            parsed, client_sock, config
        )

        # Update global metrics
        add_bytes_sent(bytes_sent)
        add_bytes_received(bytes_received)

        # Log the request with full metrics
        log_request(client_addr, host, port, method, "ALLOWED",
                   response_status=response_status,
                   bytes_sent=bytes_sent,
                   bytes_received=bytes_received)

    except Exception:
        log_request(client_addr, host, port, method, "ERROR")


def send_error_response(client_sock, status_code, status_message, body_message, config):
    """
    Send an HTTP error response to the client.

    Args:
        client_sock: Client socket
        status_code: HTTP status code (e.g., 403, 500)
        status_message: HTTP status message (e.g., "Forbidden")
        body_message: Detailed error message for response body
        config: ProxyConfig instance
    """
    try:
        # Build detailed HTML response if enabled
        if config.detailed_errors:
            html_body = f"""<!DOCTYPE html>
<html>
<head>
    <title>{status_code} {status_message}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #d32f2f; }}
        .error-code {{ font-size: 72px; font-weight: bold; color: #e0e0e0; }}
        .message {{ margin-top: 20px; padding: 20px; background: #f5f5f5; border-left: 4px solid #d32f2f; }}
    </style>
</head>
<body>
    <div class="error-code">{status_code}</div>
    <h1>{status_message}</h1>
    <div class="message">{body_message}</div>
    <hr>
    <p><small>Custom Network Proxy Server</small></p>
</body>
</html>"""
        else:
            html_body = f"""<!DOCTYPE html>
<html>
<head><title>{status_code} {status_message}</title></head>
<body>
    <h1>{status_code} {status_message}</h1>
    <p>{body_message}</p>
</body>
</html>"""

        body_bytes = html_body.encode("utf-8")

        # Build HTTP response
        response = (
            f"HTTP/1.1 {status_code} {status_message}\r\n"
            f"Content-Type: text/html; charset=utf-8\r\n"
            f"Content-Length: {len(body_bytes)}\r\n"
            f"Connection: close\r\n"
            f"\r\n"
        ).encode("utf-8")

        # Send response
        client_sock.sendall(response + body_bytes)

    except Exception:
        # If error response fails, silently ignore
        pass
