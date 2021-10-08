from platform import system

__all__ = ("is_carrier_detected", "is_maybe_wired_or_wireless")


def _is_carrier_detected_dummy(name: str) -> bool:
    """Returns whether a cable is physically connected to the network interface
    with the given name.

    Dummy version, always returns False.
    """
    return False


def _is_carrier_detected_darwin(name: str) -> bool:
    """Returns whether a cable is physically connected to the network interface
    with the given name.

    macOS version, currently unimplemented, always returns False.
    """
    return False


def _is_carrier_detected_linux(name: str) -> bool:
    """Returns whether a cable is physically connected to the network interface
    with the given name.

    Linux version, uses `/sys/class/net/{name}/carrier` to check.
    """
    if "/" in name or ".." in name:
        return False

    fname = f"/sys/class/net/{name}/carrier"
    try:
        with open(fname, "r") as fp:
            data = fp.read()
            return int(data.strip()) > 0
    except Exception:
        return False


def _is_maybe_wired_or_wireless_dummy(name: str) -> bool:
    """Returns whether the network interface with the given name might be a
    relevant wired or wireless interface (dummy variant that always returns True).
    """
    return True


def _is_maybe_wired_or_wireless_darwin(name: str) -> bool:
    """Returns whether the network interface with the given name might be a
    relevant wired or wireless interface (macOS variant).
    """
    if name.startswith("bridge") or name.startswith("p2p") or name.startswith("lo"):
        return False

    if name.startswith("llw") or name.startswith("awdl"):
        return True

    from ._darwin import get_network_interface_to_device_map

    ports = get_network_interface_to_device_map()
    if ports.get(name, "").startswith("Thunderbolt"):
        return False

    return True


def _is_maybe_wired_or_wireless_linux(name: str) -> bool:
    """Returns whether the network interface with the given name is likely to
    be a wireless interface (Linux variant).
    """
    return len(name) > 2 and (name[:2] in ("en", "wl", "ww") or name[:3] == "eth")


if system() == "Darwin":
    is_carrier_detected = _is_carrier_detected_darwin
    is_maybe_wired_or_wireless = _is_maybe_wired_or_wireless_darwin
elif system() == "Linux":
    is_carrier_detected = _is_carrier_detected_linux
    is_maybe_wired_or_wireless = _is_maybe_wired_or_wireless_linux
else:
    is_carrier_detected = _is_carrier_detected_dummy
    is_maybe_wired_or_wireless = _is_maybe_wired_or_wireless_dummy
