"""Generic networking-related utility functions."""

__all__ = (
    "canonicalize_mac_address",
    "is_mac_address_unicast",
    "is_mac_address_universal",
)


def canonicalize_mac_address(address: str) -> str:
    """Returns a canonical representation of a MAC address, with all whitespace
    stripped, hexadecimal characters converted to lowercase and dashes replaced
    with colons.
    """
    return address.strip().lower().replace("-", ":")


def _get_first_byte_of_mac_address(address: str) -> int:
    """Returns the first byte of a MAC address (specified as colon- or
    dash-separated hex digits).
    """
    for index, ch in enumerate(address):
        if ch in ("-:"):
            try:
                return int(address[:index], 16)
            except ValueError:
                raise ValueError("input is not a valid MAC address") from None

    raise ValueError("input is not a valid MAC address")


def is_mac_address_unicast(address: str) -> bool:
    """Returns whether a given MAC address (specified as colon- or dash-separated
    hex digits) is a unicast MAC address.
    """
    return not bool(_get_first_byte_of_mac_address(address) & 0x01)


def is_mac_address_universal(address: str) -> bool:
    """Returns whether a given MAC address (specified as colon-separated
    hex digits) is a universal, vendor-assigned MAC address.
    """
    return not bool(_get_first_byte_of_mac_address(address) & 0x03)
