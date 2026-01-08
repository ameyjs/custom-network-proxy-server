"""
Traffic forwarding module for the proxy server.
Handles HTTP request/response forwarding and HTTPS tunneling.
"""

import socket
import threading
from parser import recv_request_body, extract_response_status


class DataTracker:
    """Tracks bytes sent and received during forwarding."""

    def __init__(self):
        self.bytes_sent = 0
        self.bytes_received = 0
        self.lock = threading.Lock()

    def add_sent(self, count):
        """Add to bytes sent counter."""
        with self.lock:
            self.bytes_sent += count

    def add_received(self, count):
        """Add to bytes received counter."""
        with self.lock:
            self.bytes_received += count

    def get_stats(self):
        """Get current statistics."""
        with self.lock:
            return self.bytes_sent, self.bytes_received


def forward_data(source_sock, destination_sock, tracker, is_sending, buffer_size=4096):
    """
    Forward data from source socket to destination socket with byte tracking.
    Used as a thread target for bidirectional tunneling.
    """
    try:
        while True:
            data = source_sock.recv(buffer_size)
            if not data:
                break
            destination_sock.sendall(data)

            # Track bytes
            if is_sending:
                tracker.add_sent(len(data))
            else:
                tracker.add_received(len(data))
    except Exception:
        pass


def tunnel(client_sock, server_sock, buffer_size=4096):
    """
    Create bidirectional tunnel between client and server.
    Used for HTTPS CONNECT tunneling.
    """
    tracker = DataTracker()

    # Create thread for client → server forwarding
    client_to_server = threading.Thread(
        target=forward_data,
        args=(client_sock, server_sock, tracker, True, buffer_size)
    )
    client_to_server.daemon = True

    # Create thread for server → client forwarding
    server_to_client = threading.Thread(
        target=forward_data,
        args=(server_sock, client_sock, tracker, False, buffer_size)
    )
    server_to_client.daemon = True

    # Start both threads
    client_to_server.start()
    server_to_client.start()

    # Wait for both threads to complete
    client_to_server.join()
    server_to_client.join()

    return tracker.get_stats()


def forward_http(parsed, client_sock, config):
    """
    Forward HTTP request to destination server and return response to client.
    """
    server_sock = None
    bytes_sent = 0
    bytes_received = 0
    response_status = None

    try:
        # Create connection to destination server
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.settimeout(config.connect_timeout)
        server_sock.connect((parsed["host"], parsed["port"]))

        # Send request headers to server
        server_sock.sendall(parsed["raw"])
        bytes_sent += len(parsed["raw"])

        # Handle request body if Content-Length is present
        if config.forward_body and parsed["content_length"] > 0:
            body = recv_request_body(client_sock, parsed["content_length"],
                                    config.buffer_size)
            if body:
                server_sock.sendall(body)
                bytes_sent += len(body)

        # Receive and forward response from server to client
        # Use streaming to avoid buffering entire response in memory
        first_chunk = True
        while True:
            response = server_sock.recv(config.buffer_size)
            if not response:
                break

            # Extract status code from first chunk
            if first_chunk and config.track_sizes:
                response_status = extract_response_status(response)
                first_chunk = False

            client_sock.sendall(response)
            bytes_received += len(response)

    except socket.timeout:
        # --- FIX: SMART TIMEOUT HANDLING ---
        if bytes_received > 0:
            # We received data, so this is likely just the connection staying open.
            # Treat this as a success (200 OK), not an error.
            if not response_status:
                response_status = "200"
        else:
            # We received NOTHING. This is a real timeout error.
            response_status = "TIMEOUT"
            
    except ConnectionRefusedError:
        response_status = "REFUSED"
    except Exception as e:
        print(f"!!! DEBUG ERROR: {e} !!!")  # <--- This will tell us the secret
        response_status = "ERROR"
    finally:
        # Close server connection
        if server_sock:
            server_sock.close()

    return response_status, bytes_sent, bytes_received