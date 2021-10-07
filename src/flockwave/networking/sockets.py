import platform
import socket

from ipaddress import ip_address, ip_network
from netifaces import AF_INET, gateways, ifaddresses, interfaces
from typing import Any, Optional, Tuple

__all__ = ("create_socket", "enable_tcp_keepalive", "get_socket_address")


def create_socket(socket_type) -> Any:
    """Creates an asynchronous socket with the given type.

    Asynchronous sockets have asynchronous sender and receiver methods so
    you need to use the `await` keyword with them.

    Parameters:
        socket_type: the type of the socket (``socket.SOCK_STREAM`` for
            TCP sockets, ``socket.SOCK_DGRAM`` for UDP sockets)

    Returns:
        the newly created socket
    """
    import trio.socket

    sock = trio.socket.socket(trio.socket.AF_INET, socket_type)
    if hasattr(trio.socket, "SO_REUSEADDR"):
        # SO_REUSEADDR does not exist on Windows, but we don't really need
        # it on Windows either
        sock.setsockopt(trio.socket.SOL_SOCKET, trio.socket.SO_REUSEADDR, 1)
    if hasattr(trio.socket, "SO_REUSEPORT"):
        # Needed on Mac OS X to work around an issue with an earlier
        # instance of the flockctrl process somehow leaving a socket
        # bound to the UDP broadcast address even when the process
        # terminates
        sock.setsockopt(trio.socket.SOL_SOCKET, trio.socket.SO_REUSEPORT, 1)
    return sock


def enable_tcp_keepalive(
    sock, after_idle_sec: int = 1, interval_sec: int = 3, max_fails: int = 5
) -> None:
    """Enables TCP keepalive settings on the given socket.

    Parameters:
        after_idle_sec: number of seconds after which the socket should start
            sending TCP keepalive packets
        interval_sec: number of seconds between consecutive TCP keepalive
            packets
        max_fails: maximum number of failures allowed before terminating the
            TCP connection
    """
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

    if hasattr(socket, "TCP_KEEPIDLE"):
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, after_idle_sec)
    elif platform.system() == "Darwin":
        # This is for macOS
        try:
            TCP_KEEPALIVE = 0x10  # scraped from the Darwin headers
            sock.setsockopt(socket.IPPROTO_TCP, TCP_KEEPALIVE, after_idle_sec)
        except Exception:
            pass

    if hasattr(socket, "TCP_KEEPINTVL"):
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, interval_sec)

    if hasattr(socket, "TCP_KEEPCNT"):
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, max_fails)


def format_socket_address(
    sock, format: str = "{host}:{port}", in_subnet_of: Optional[Tuple[str, int]] = None
) -> str:
    """Formats the address that the given socket is bound to in the
    standard hostname-port format.

    Parameters:
        sock: the socket to format
        format: format string in brace-style that is used by
            ``str.format()``. The tokens ``{host}`` and ``{port}`` will be
            replaced by the hostname and port.
        in_subnet_of: the IP address and port that should preferably be in the
            same subnet as the response. This is used only if the socket is
            bound to all interfaces, in which case we will try to pick an
            interface that is in the same subnet as the remote address.

    Returns:
        str: a formatted representation of the address and port of the
            socket
    """
    host, port = get_socket_address(sock, in_subnet_of)
    return format.format(host=host, port=port)


def get_socket_address(
    sock, in_subnet_of: Optional[Tuple[str, int]] = None
) -> Tuple[str, int]:
    """Gets the hostname and port that the given socket is bound to.

    Parameters:
        sock: the socket for which we need its address
        in_subnet_of: the IP address and port that should preferably be in the
            same subnet as the response. This is used only if the socket is
            bound to all interfaces, in which case we will try to pick an
            interface that is in the same subnet as the remote address.

    Returns:
        the host and port where the socket is bound to
    """
    if hasattr(sock, "getsockname"):
        address = sock.getsockname()
    else:
        address = sock

    if len(address) == 4:
        # IPv6 addresses?
        host, port, _, _ = address
    else:
        # IPv4 addresses
        host, port = address

    # Canonicalize the value of 'host'
    if host == "0.0.0.0" or host == "::":
        host = ""

    # If host is empty and an address is given, try to find one from
    # our IP addresses that is in the same subnet as the given address
    if not host and in_subnet_of:
        remote_host, _ = in_subnet_of
        try:
            remote_host = ip_address(remote_host)
        except Exception:
            remote_host = None

        if remote_host:
            for interface in interfaces():
                # We are currently interested only in IPv4 addresses
                specs = ifaddresses(interface).get(AF_INET)
                if not specs:
                    continue
                for spec in specs:
                    if "addr" in spec and "netmask" in spec:
                        net = ip_network(
                            spec["addr"] + "/" + spec["netmask"], strict=False
                        )
                        if remote_host in net:
                            host = spec["addr"]
                            break

        if not host:
            # Try to find the default gateway and then use the IP address of
            # the network interface corresponding to the gateway. This may
            # or may not work; most likely it won't, but that's the best we
            # can do.
            gateway = gateways()["default"][AF_INET]
            if gateway:
                _, interface = gateway
                specs = ifaddresses(interface).get(AF_INET)
                for spec in specs:
                    if "addr" in spec:
                        host = spec["addr"]
                        break

    return host, port
