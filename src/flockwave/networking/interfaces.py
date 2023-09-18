"""Generic networking-related utility functions."""

from ipaddress import ip_address, ip_network, IPv6Address, IPv6Network
from netifaces import AF_INET, AF_INET6, AF_LINK, ifaddresses, interfaces
from typing import Sequence

from .addressing import canonicalize_mac_address

__all__ = (
    "find_interfaces_with_address",
    "find_interfaces_in_network",
    "get_address_of_network_interface",
    "get_all_ipv4_addresses",
    "get_broadcast_address_of_network_interface",
    "get_link_layer_address_mapping",
    "resolve_network_interface_or_address",
)


def find_interfaces_with_address(address: str) -> Sequence[tuple[str, str]]:
    """Finds the network interfaces of the current machine that contain the given
    address in their network.

    Parameters:
        address: the address that we are looking for

    Returns:
        for all the network interfaces that have at least one address that
        belongs to the given network, the name of the network interface itself and
        the network of the interface, in a tuple
    """
    address = ip_address(address)
    if isinstance(address, IPv6Address):
        family = AF_INET6
    else:
        family = AF_INET

    candidates = []
    for interface in interfaces():
        specs = ifaddresses(interface).get(family) or []
        ip_addresses_in_network = (
            (spec.get("addr"), spec.get("netmask")) for spec in specs
        )
        for if_address, netmask in ip_addresses_in_network:
            network = ip_network(f"{if_address}/{netmask}", strict=False)
            if address in network:
                candidates.append((interface, network))

    return candidates


def find_interfaces_in_network(network: str) -> Sequence[tuple[str, str, str]]:
    """Finds the network interfaces of the current machine that have at
    least one address that belongs to the given network.

    Parameters:
        network: the network that we are looking for

    Returns:
        for all the network interfaces that have at least one address that
        belongs to the given network, the name of the network interface
        itself, the matched address and the network of the interface, in
        a tuple
    """
    network = ip_network(network)
    if isinstance(network, IPv6Network):
        family = AF_INET6
    else:
        family = AF_INET

    candidates = []
    for interface in interfaces():
        specs = ifaddresses(interface).get(family) or []
        ip_addresses_in_network = (
            (spec.get("addr"), spec.get("netmask"))
            for spec in specs
            if ip_address(str(spec.get("addr"))) in network
        )
        for address, netmask in ip_addresses_in_network:
            candidates.append(
                (
                    interface,
                    address,
                    str(ip_network(f"{address}/{netmask}", strict=False))
                    if netmask
                    else None,
                )
            )

    return candidates


def get_address_of_network_interface(value: str, family: int = AF_INET) -> str:
    """Returns the address of the given network interface in the given
    address family.

    If the interface has multiple addresses, this function returns the first
    one only.

    Parameters:
        value: the name of the network interface
        family: the address family of the interface; one of the `AF_` constants
            from the `netifaces` module. Use `AF_INET` for the standard IPv4
            address and `AF_LINK` for the MAC address.

    Returns:
        the address of the given network interface

    Raises:
        ValueError: if the given network interface has no address in the given
            address family
    """
    addresses = ifaddresses(value).get(family)
    if addresses:
        return addresses[0]["addr"]
    else:
        raise ValueError(f"interface {value} has no address")


def get_all_ipv4_addresses() -> Sequence[str]:
    """Returns all IPv4 addresses of the current machine."""
    result = []
    for iface in interfaces():
        addresses = ifaddresses(iface)
        if AF_INET in addresses:
            result.append(addresses[AF_INET][0]["addr"])
    return result


def get_broadcast_address_of_network_interface(
    value: str, family: int = AF_INET
) -> str:
    """Returns the broadcast address of the given network interface in the given
    address family.

    Parameters:
        value: the name of the network interface
        family: the address family of the interface; one of the `AF_` constants
            from the `netifaces` module

    Returns:
        the broadcast address of the given network interface

    Raises:
        ValueError: if the given network interface has no broadcast address in
            the given address family
    """
    addresses = ifaddresses(value).get(family)
    if addresses:
        return addresses[0]["broadcast"]
    else:
        raise ValueError(f"interface {value} has no broadcast address")


def get_link_layer_address_mapping() -> dict[str, str]:
    """Returns a dictionary mapping interface names to their corresponding
    link-layer (MAC) addresses.

    We assume that one interface may have only one link-layer address.
    """
    result = {}
    for iface in interfaces():
        addresses = ifaddresses(iface)
        if AF_LINK in addresses:
            result[iface] = canonicalize_mac_address(addresses[AF_LINK][0]["addr"])
    return result


def resolve_network_interface_or_address(value: str) -> str:
    """Takes the name of a network interface or an IP address as input,
    and returns the resolved and validated IP address.

    This process might call `netifaces.ifaddresses()` et al in the
    background, which could potentially be blocking. It is advised to run
    this function in a separate worker thread.

    Parameters:
        value: the IP address to validate, or the interface whose IP address
            we are about to retrieve.

    Returns:
        the IPv4 address of the interface.
    """
    try:
        return str(ip_address(value))
    except ValueError:
        return str(get_address_of_network_interface(value))
