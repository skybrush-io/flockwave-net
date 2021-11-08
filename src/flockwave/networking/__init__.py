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
    get_broadcast_address_of_network_interface,
    get_link_layer_address_mapping,
    resolve_network_interface_or_address,
)
from .scanner import NetworkScanner
from .sockets import (
    can_bind_to_tcp_address,
    can_bind_to_udp_address,
    create_socket,
    enable_tcp_keepalive,
    format_socket_address,
    get_socket_address,
)
from .version import __version__
from .wired import is_carrier_detected, is_maybe_wired_or_wireless
from .wireless import get_connected_access_point_name, is_likely_wireless

__all__ = (
    "can_bind_to_tcp_address",
    "can_bind_to_udp_address",
    "canonicalize_mac_address",
    "create_socket",
    "enable_tcp_keepalive",
    "find_interfaces_with_address",
    "find_interfaces_in_network",
    "format_socket_address",
    "get_address_of_network_interface",
    "get_all_ipv4_addresses",
    "get_broadcast_address_of_network_interface",
    "get_connected_access_point_name",
    "get_link_layer_address_mapping",
    "get_socket_address",
    "is_carrier_detected",
    "is_likely_wireless",
    "is_mac_address_unicast",
    "is_mac_address_universal",
    "is_maybe_wired_or_wireless",
    "resolve_network_interface_or_address",
    "NetworkScanner",
    "__version__",
)
