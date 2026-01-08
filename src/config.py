"""
Configuration loader for the proxy server.
Reads settings from config/proxy_config.ini
"""

import configparser
import os

CONFIG_FILE = "config/proxy_config.ini"

# Default configuration values
DEFAULTS = {
    "host": "0.0.0.0",
    "port": 8888,
    "backlog": 50,
    "timeout": 30,
    "max_connections": 100,
    "log_dir": "logs",
    "log_file": "proxy.log",
    "max_log_size": 10,
    "log_rotation_count": 5,
    "log_level": "INFO",
    "blocked_list": "config/blocked_domains.txt",
    "enable_filtering": True,
    "case_sensitive": False,
    "buffer_size": 4096,
    "connect_timeout": 10,
    "forward_body": True,
    "enable_https": True,
    "track_sizes": True,
    "detailed_errors": True,
}

class ProxyConfig:
    """Proxy server configuration container."""

    def __init__(self, config_file=CONFIG_FILE):
        """
        Load configuration from file or use defaults.

        Args:
            config_file: Path to configuration file
        """
        self.config = configparser.ConfigParser()

        # Load from file if it exists
        if os.path.exists(config_file):
            self.config.read(config_file)
        else:
            print(f"[!] Warning: Config file {config_file} not found, using defaults")

        # Server settings
        self.host = self._get("server", "host", DEFAULTS["host"])
        self.port = self._get_int("server", "port", DEFAULTS["port"])
        self.backlog = self._get_int("server", "backlog", DEFAULTS["backlog"])
        self.timeout = self._get_int("server", "timeout", DEFAULTS["timeout"])

        # Concurrency settings
        self.max_connections = self._get_int("concurrency", "max_connections",
                                             DEFAULTS["max_connections"])

        # Logging settings
        self.log_dir = self._get("logging", "log_dir", DEFAULTS["log_dir"])
        self.log_file = self._get("logging", "log_file", DEFAULTS["log_file"])
        self.max_log_size = self._get_int("logging", "max_log_size",
                                          DEFAULTS["max_log_size"])
        self.log_rotation_count = self._get_int("logging", "log_rotation_count",
                                                DEFAULTS["log_rotation_count"])
        self.log_level = self._get("logging", "log_level", DEFAULTS["log_level"])

        # Filtering settings
        self.blocked_list = self._get("filtering", "blocked_list",
                                      DEFAULTS["blocked_list"])
        self.enable_filtering = self._get_bool("filtering", "enable_filtering",
                                               DEFAULTS["enable_filtering"])
        self.case_sensitive = self._get_bool("filtering", "case_sensitive",
                                             DEFAULTS["case_sensitive"])

        # Forwarding settings
        self.buffer_size = self._get_int("forwarding", "buffer_size",
                                         DEFAULTS["buffer_size"])
        self.connect_timeout = self._get_int("forwarding", "connect_timeout",
                                             DEFAULTS["connect_timeout"])
        self.forward_body = self._get_bool("forwarding", "forward_body",
                                           DEFAULTS["forward_body"])

        # Feature flags
        self.enable_https = self._get_bool("features", "enable_https",
                                           DEFAULTS["enable_https"])
        self.track_sizes = self._get_bool("features", "track_sizes",
                                          DEFAULTS["track_sizes"])
        self.detailed_errors = self._get_bool("features", "detailed_errors",
                                              DEFAULTS["detailed_errors"])

    def _get(self, section, option, default):
        """Get string value from config or return default."""
        try:
            return self.config.get(section, option)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default

    def _get_int(self, section, option, default):
        """Get integer value from config or return default."""
        try:
            return self.config.getint(section, option)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return default

    def _get_bool(self, section, option, default):
        """Get boolean value from config or return default."""
        try:
            return self.config.getboolean(section, option)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return default

    def display(self):
        """Print current configuration."""
        print("\n" + "=" * 60)
        print("Proxy Server Configuration")
        print("=" * 60)
        print(f"Server Address: {self.host}:{self.port}")
        print(f"Listen Backlog: {self.backlog}")
        print(f"Socket Timeout: {self.timeout}s")
        print(f"Max Connections: {self.max_connections if self.max_connections > 0 else 'Unlimited'}")
        print(f"Buffer Size: {self.buffer_size} bytes")
        print(f"Connect Timeout: {self.connect_timeout}s")
        print(f"Log Directory: {self.log_dir}")
        print(f"Max Log Size: {self.max_log_size} KB")
        print(f"Filtering Enabled: {self.enable_filtering}")
        print(f"HTTPS Support: {self.enable_https}")
        print(f"Body Forwarding: {self.forward_body}")
        print(f"Size Tracking: {self.track_sizes}")
        print("=" * 60 + "\n")


# Global configuration instance
config = ProxyConfig()
