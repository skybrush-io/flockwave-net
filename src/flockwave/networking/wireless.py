from platform import system
from subprocess import run
from typing import Optional


def _get_connected_access_point_name_dummy(name: str) -> Optional[str]:
    """Returns the name of the wireless access point name that the given
    network interface is connected to, or `None` if it cannot be determined
    or if the network interface is not wireless.

    Dummy version, always returns `None`.
    """
    return None


def _get_connected_access_point_name_darwin(name: str) -> Optional[str]:
    """Returns the name of the wireless access point name that the given
    network interface is connected to, or `None` if it cannot be determined
    or if the network interface is not wireless.

    macOS version, uses `networksetup` to figure out the name of the AP.
    """
    PREFIX = b"Current Wi-Fi Network: "
    result = run(["networksetup", "-getairportnetwork", name], capture_output=True)
    if not result.returncode and result.stdout.startswith(PREFIX):
        return result.stdout[len(PREFIX) :].decode("utf-8", "replace").strip()
    else:
        return None


def _get_connected_access_point_name_linux(name: str) -> Optional[str]:
    """Returns the name of the wireless access point name that the given
    network interface is connected to, or `None` if it cannot be determined
    or if the network interface is not wireless.

    Linux version, uses `iwgetid -r` to figure out the name of the AP.
    """
    result = run(["iwgetid", "-r"], capture_output=True)
    if not result.returncode:
        return result.stdout.decode("utf-8", "replace").strip()
    else:
        return None


def _is_likely_wireless_dummy(name: str) -> bool:
    """Returns whether the network interface with the given name is likely to
    be a wireless interface (dummy variant that always returns False).
    """
    return False


def _is_likely_wireless_darwin(name: str) -> bool:
    """Returns whether the network interface with the given name is likely to
    be a wireless interface (macOS variant).
    """
    if name.startswith("awdl") or name.startswith("llw"):
        # Apple Wireless Direct Link or Low-Latency Wireless
        return True

    if name.startswith("lo"):
        # Loopback interface
        return False

    from ._darwin import get_network_interface_to_device_map

    ports = get_network_interface_to_device_map()
    return ports.get(name, "").startswith("Wi-Fi")


def _is_likely_wireless_linux(name: str) -> bool:
    """Returns whether the network interface with the given name is likely to
    be a wireless interface (Linux variant).
    """
    return len(name) > 2 and name[:2] in ("wl", "ww")


if system() == "Darwin":
    get_connected_access_point_name = _get_connected_access_point_name_darwin
    is_likely_wireless = _is_likely_wireless_darwin
elif system() == "Linux":
    get_connected_access_point_name = _get_connected_access_point_name_linux
    is_likely_wireless = _is_likely_wireless_linux
else:
    get_connected_access_point_name = _get_connected_access_point_name_dummy
    is_likely_wireless = _is_likely_wireless_dummy
