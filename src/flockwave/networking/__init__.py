"""Generic networking-related utility functions."""

from .addressing import (
    canonicalize_mac_address,
    is_mac_address_unicast,
    is_mac_address_universal,
)
from .interfaces import (
    find_interfaces_in_network,
    find_interfaces_with_address,
    get_address_of_network_interface,
    get_all_ipv4_addresses,
    get_link_layer_address_mapping,
    resolve_network_interface_or_address,
)
from .sockets import (
    create_socket,
    enable_tcp_keepalive,
    format_socket_address,
    get_socket_address,
)
from .version import __version__

__all__ = (
    "canonicalize_mac_address",
    "create_socket",
    "enable_tcp_keepalive",
    "find_interfaces_with_address",
    "find_interfaces_in_network",
    "format_socket_address",
    "get_address_of_network_interface",
    "get_all_ipv4_addresses",
    "get_link_layer_address_mapping",
    "get_socket_address",
    "is_mac_address_unicast",
    "is_mac_address_universal",
    "resolve_network_interface_or_address",
    "__version__",
)
