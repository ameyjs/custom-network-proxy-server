"""
Domain and IP filtering module.
Implements blocklist-based filtering with configurable matching rules.
"""

import os

BLOCKED_SET = set()
CONFIG = None


def init_filter(config):
    """
    Initialize filter with configuration.
    Loads blocklist from file specified in config.

    Args:
        config: ProxyConfig instance
    """
    global CONFIG
    CONFIG = config

    if config.enable_filtering:
        load_blocklist(config.blocked_list, config.case_sensitive)


def load_blocklist(blocklist_file, case_sensitive=False):
    """
    Load blocked domains and IPs from configuration file.

    Format:
        - One domain/IP per line
        - Lines starting with # are comments
        - Blank lines are ignored
        - Entries are case-insensitive by default

    Args:
        blocklist_file: Path to blocklist file
        case_sensitive: If True, perform case-sensitive matching
    """
    global BLOCKED_SET

    if not os.path.exists(blocklist_file):
        print(f"[!] Warning: Blocklist file {blocklist_file} not found")
        return

    count = 0
    with open(blocklist_file, "r") as f:
        for line in f:
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Add to blocklist (lowercase if case-insensitive)
            entry = line if case_sensitive else line.lower()
            BLOCKED_SET.add(entry)
            count += 1

    print(f"[+] Loaded {count} entries from blocklist")


def is_blocked(host):
    """
    Check if a host (domain or IP) is blocked.

    Args:
        host: Hostname or IP address to check

    Returns:
        bool: True if blocked, False otherwise

    Blocking logic:
        - Exact match against blocklist
        - Subdomain matching (blocking example.com also blocks www.example.com)
        - Case-insensitive by default (configurable)
    """
    if not CONFIG or not CONFIG.enable_filtering:
        return False

    if not host:
        return False

    # Convert to lowercase if case-insensitive matching
    check_host = host if CONFIG.case_sensitive else host.lower()

    # Check exact match
    if check_host in BLOCKED_SET:
        return True

    # Check subdomain matching
    # If example.com is blocked, www.example.com should also be blocked
    parts = check_host.split(".")
    for i in range(len(parts)):
        parent_domain = ".".join(parts[i:])
        if parent_domain in BLOCKED_SET:
            return True

    return False


def add_to_blocklist(host):
    """
    Add a host to the blocklist at runtime.

    Args:
        host: Hostname or IP to block
    """
    global BLOCKED_SET

    entry = host if (CONFIG and CONFIG.case_sensitive) else host.lower()
    BLOCKED_SET.add(entry)


def remove_from_blocklist(host):
    """
    Remove a host from the blocklist at runtime.

    Args:
        host: Hostname or IP to unblock
    """
    global BLOCKED_SET

    entry = host if (CONFIG and CONFIG.case_sensitive) else host.lower()
    BLOCKED_SET.discard(entry)


def get_blocklist():
    """
    Get current blocklist.

    Returns:
        set: Copy of blocked entries
    """
    return BLOCKED_SET.copy()


def get_blocklist_size():
    """
    Get number of entries in blocklist.

    Returns:
        int: Number of blocked entries
    """
    return len(BLOCKED_SET)
