"""
HTTP request parser module.
Handles receiving and parsing HTTP requests from client sockets.
"""

from urllib.parse import urlparse

BUFFER_SIZE = 4096
HEADER_TERMINATOR = b"\r\n\r\n"


def recv_http_request(sock, buffer_size=BUFFER_SIZE):
    """
    Receive HTTP request headers from socket.
    Reads data in chunks until complete headers are received.

    This implements proper header accumulation as recommended in the project specs.

    Args:
        sock: Client socket
        buffer_size: Size of receive buffer

    Returns:
        bytes: Complete HTTP request headers including terminator
    """
    data = b""
    while HEADER_TERMINATOR not in data:
        try:
            chunk = sock.recv(buffer_size)
            if not chunk:
                break
            data += chunk
        except Exception:
            break
    return data


def parse_http_request(data):
    """
    Parse HTTP request to extract method, host, port, headers, and raw data.

    Args:
        data: Raw HTTP request as bytes

    Returns:
        dict: Parsed request with keys:
              - method: HTTP method (GET, POST, CONNECT, etc.)
              - host: Destination hostname/IP
              - port: Destination port
              - raw: Original request bytes
              - request_line: First line of HTTP request
              - content_length: Content-Length header value (0 if not present)
              - headers: Dictionary of HTTP headers
              Returns None if parsing fails
    """
    try:
        # Decode bytes to string, ignoring errors
        request_str = data.decode("utf-8", errors="ignore")
        lines = request_str.split("\r\n")

        if not lines:
            return None

        # Parse request line (e.g., "GET http://example.com/ HTTP/1.1")
        request_line = lines[0].split()
        if len(request_line) < 2:
            return None

        method = request_line[0]
        target = request_line[1]

        host = None
        port = None
        content_length = 0
        headers = {}

        # Parse headers into dictionary
        for line in lines[1:]:
            if not line or ":" not in line:
                continue

            key, value = line.split(":", 1)
            key = key.strip().lower()
            value = value.strip()
            headers[key] = value

            # Extract Content-Length if present
            if key == "content-length":
                try:
                    content_length = int(value)
                except ValueError:
                    content_length = 0

        # Handle CONNECT requests (HTTPS tunneling)
        if method == "CONNECT":
            # Format: "CONNECT example.com:443 HTTP/1.1"
            if ":" in target:
                host, port_str = target.split(":", 1)
                port = int(port_str)
            else:
                host = target
                port = 443  # Default HTTPS port

        # Handle regular HTTP requests
        else:
            # First, try to get Host header
            if "host" in headers:
                host = headers["host"]
                # Remove port from host if present
                if ":" in host:
                    host, port_str = host.split(":", 1)
                    port = int(port_str)
                else:
                    port = 80  # Default HTTP port

            # If no Host header, try parsing absolute URL from target
            if not host:
                if target.startswith("http://") or target.startswith("https://"):
                    parsed = urlparse(target)
                    host = parsed.hostname
                    port = parsed.port if parsed.port else 80
                else:
                    # Relative URL without Host header - cannot determine host
                    return None

        if not host:
            return None

        return {
            "method": method,
            "host": host,
            "port": port,
            "raw": data,
            "request_line": lines[0],
            "content_length": content_length,
            "headers": headers
        }

    except Exception:
        return None


def recv_request_body(sock, content_length, buffer_size=BUFFER_SIZE):
    """
    Receive HTTP request body based on Content-Length header.

    Args:
        sock: Client socket
        content_length: Number of bytes to receive
        buffer_size: Size of receive buffer

    Returns:
        bytes: Request body data
    """
    body = b""
    remaining = content_length

    while remaining > 0:
        try:
            chunk_size = min(buffer_size, remaining)
            chunk = sock.recv(chunk_size)
            if not chunk:
                break
            body += chunk
            remaining -= len(chunk)
        except Exception:
            break

    return body


def extract_response_status(response_data):
    """
    Extract HTTP status code from response.

    Args:
        response_data: HTTP response bytes

    Returns:
        int: Status code (e.g., 200, 404) or None if not found
    """
    try:
        response_str = response_data.decode("utf-8", errors="ignore")
        lines = response_str.split("\r\n")

        if not lines:
            return None

        # Status line format: "HTTP/1.1 200 OK"
        status_line = lines[0].split()
        if len(status_line) >= 2:
            return int(status_line[1])

    except Exception:
        pass

    return None
