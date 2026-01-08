"""
Logging and metrics module for the proxy server.
Provides thread-safe logging with automatic rotation and detailed metrics tracking.
"""

import os
import threading
from datetime import datetime

log_lock = threading.Lock()
metrics_lock = threading.Lock()

metrics = {
    "total": 0,
    "allowed": 0,
    "blocked": 0,
    "bytes_sent": 0,
    "bytes_received": 0
}

# Will be initialized from config
LOG_DIR = "logs"
LOG_FILE = None
MAX_LOG_SIZE = 10240  # 10 KB
LOG_ROTATION_COUNT = 5


def init_logger(config):
    """
    Initialize logger with configuration.

    Args:
        config: ProxyConfig instance
    """
    global LOG_DIR, LOG_FILE, MAX_LOG_SIZE, LOG_ROTATION_COUNT

    LOG_DIR = config.log_dir
    LOG_FILE = os.path.join(LOG_DIR, config.log_file)
    MAX_LOG_SIZE = config.max_log_size * 1024  # Convert KB to bytes
    LOG_ROTATION_COUNT = config.log_rotation_count

    # Create log directory if it doesn't exist
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)


def log_request(client_addr, host, port, method, status, response_status=None,
                bytes_sent=0, bytes_received=0):
    """
    Log a request with comprehensive details.
    Thread-safe logging with automatic log rotation.

    Args:
        client_addr: Tuple of (ip, port) for client
        host: Destination hostname/IP
        port: Destination port
        method: HTTP method (GET, POST, CONNECT, etc.)
        status: Request status (ALLOWED, BLOCKED, ERROR)
        response_status: HTTP response status code (e.g., 200, 403)
        bytes_sent: Number of bytes sent to server
        bytes_received: Number of bytes received from server
    """
    if LOG_FILE is None:
        return  # Logger not initialized

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Build log entry with available information
    log_parts = [
        f"[{timestamp}]",
        f"{client_addr}",
        f"→ {host}:{port}",
        f"| {method}",
        f"| {status}"
    ]

    if response_status:
        log_parts.append(f"| {response_status}")

    if bytes_sent > 0 or bytes_received > 0:
        log_parts.append(f"| ↑{bytes_sent}B ↓{bytes_received}B")

    log_entry = " ".join(log_parts) + "\n"

    with log_lock:
        # Check if rotation is needed
        if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > MAX_LOG_SIZE:
            rotate_log()

        # Append to log file
        with open(LOG_FILE, "a") as f:
            f.write(log_entry)


def rotate_log():
    """
    Rotate log files when max size is exceeded.
    Keeps LOG_ROTATION_COUNT backup files.
    Must be called with log_lock held.
    """
    if LOG_FILE is None:
        return

    # Shift existing rotated logs
    for i in range(LOG_ROTATION_COUNT - 1, 0, -1):
        old_file = f"{LOG_FILE}.{i}"
        new_file = f"{LOG_FILE}.{i + 1}"

        if os.path.exists(old_file):
            if i == LOG_ROTATION_COUNT - 1:
                os.remove(old_file)  # Delete oldest
            else:
                os.rename(old_file, new_file)

    # Rename current log to .1
    if os.path.exists(LOG_FILE):
        os.rename(LOG_FILE, f"{LOG_FILE}.1")


def increment_total():
    """Thread-safe increment of total requests counter."""
    with metrics_lock:
        metrics["total"] += 1


def increment_allowed():
    """Thread-safe increment of allowed requests counter."""
    with metrics_lock:
        metrics["allowed"] += 1


def increment_blocked():
    """Thread-safe increment of blocked requests counter."""
    with metrics_lock:
        metrics["blocked"] += 1


def add_bytes_sent(count):
    """
    Thread-safe addition to bytes sent counter.

    Args:
        count: Number of bytes to add
    """
    with metrics_lock:
        metrics["bytes_sent"] += count


def add_bytes_received(count):
    """
    Thread-safe addition to bytes received counter.

    Args:
        count: Number of bytes to add
    """
    with metrics_lock:
        metrics["bytes_received"] += count


def get_metrics():
    """
    Get current metrics in a thread-safe manner.

    Returns:
        dict: Copy of current metrics
    """
    with metrics_lock:
        return metrics.copy()


def print_metrics_summary():
    """Print a formatted summary of current metrics."""
    m = get_metrics()
    print("\n" + "=" * 60)
    print("Proxy Server Metrics Summary")
    print("=" * 60)
    print(f"Total Requests:    {m['total']}")
    print(f"Allowed:           {m['allowed']}")
    print(f"Blocked:           {m['blocked']}")
    print(f"Bytes Sent:        {m['bytes_sent']:,} ({format_bytes(m['bytes_sent'])})")
    print(f"Bytes Received:    {m['bytes_received']:,} ({format_bytes(m['bytes_received'])})")
    print("=" * 60 + "\n")


def format_bytes(bytes_count):
    """
    Format byte count in human-readable form.

    Args:
        bytes_count: Number of bytes

    Returns:
        str: Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_count < 1024.0:
            return f"{bytes_count:.2f} {unit}"
        bytes_count /= 1024.0
    return f"{bytes_count:.2f} PB"
