import socket
import threading
import signal
import sys
from config import config
from handler import handle_client
from logger import init_logger, print_metrics_summary
from filter import init_filter

server_socket = None
shutdown_event = threading.Event()
active_connections = threading.Semaphore(100) 


def signal_handler(sig, frame):
  
    print("\n[!] Shutting down proxy server...")
    print("[*] Waiting for active connections to complete...")

    shutdown_event.set()

    if server_socket:
        try:
            server_socket.close()
        except:
            pass

    print_metrics_summary()

    print("[+] Shutdown complete")
    sys.exit(0)


def handle_client_wrapper(client_sock, client_addr, cfg):
    """
    Wrapper for handle_client that manages connection semaphore.

    Args:
        client_sock: Client socket
        client_addr: Client address
        cfg: ProxyConfig instance
    """
    try:
        handle_client(client_sock, client_addr, cfg)
    finally:
        active_connections.release()


def start_server():
    """
    Initialize and start the proxy server.

    Configuration:
        - Reads settings from config/proxy_config.ini
        - Listens on configured host:port
        - SO_REUSEADDR enabled for quick restarts
        - Spawns daemon thread for each client
        - Implements graceful shutdown on SIGINT/SIGTERM
        - Enforces max connection limit if configured

    Threading Model:
        - Main thread runs accept loop
        - Each client connection handled in separate daemon thread
        - Daemon threads automatically terminate when main exits
        - Semaphore controls max concurrent connections
    """
    global server_socket, active_connections

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    config.display()

    init_logger(config)
    print(f"[+] Logger initialized: {config.log_dir}/{config.log_file}")

    init_filter(config)

    if config.max_connections > 0:
        active_connections = threading.Semaphore(config.max_connections)
        print(f"[+] Max concurrent connections: {config.max_connections}")
    else:
        active_connections = threading.Semaphore(10000)
        print(f"[+] Max concurrent connections: Unlimited")

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_socket.bind((config.host, config.port))
    except OSError as e:
        print(f"[!] Error: Could not bind to {config.host}:{config.port}")
        print(f"[!] {e}")
        print(f"[!] Ensure port {config.port} is not already in use")
        sys.exit(1)

    server_socket.listen(config.backlog)

    print(f"[+] Proxy listening on {config.host}:{config.port}")
    print(f"[+] Press Ctrl+C to stop server and view metrics\n")

    connection_count = 0

    try:
        while not shutdown_event.is_set():
            try:
                server_socket.settimeout(1.0)

                try:
                    client_sock, client_addr = server_socket.accept()
                    connection_count += 1

                    if active_connections.acquire(blocking=False):
                        client_thread = threading.Thread(
                            target=handle_client_wrapper,
                            args=(client_sock, client_addr, config),
                            name=f"Client-{connection_count}"
                        )
                        client_thread.daemon = True
                        client_thread.start()
                    else:
                        try:
                            error_msg = (
                                b"HTTP/1.1 503 Service Unavailable\r\n"
                                b"Content-Type: text/plain\r\n"
                                b"Connection: close\r\n"
                                b"\r\n"
                                b"Proxy server at maximum capacity. Please try again later.\r\n"
                            )
                            client_sock.sendall(error_msg)
                        except:
                            pass
                        finally:
                            client_sock.close()

                except socket.timeout:
                    continue

            except OSError:
                break

    except KeyboardInterrupt:
        pass
    finally:
        if server_socket:
            server_socket.close()
        print_metrics_summary()


if __name__ == "__main__":
    start_server()
