from subprocess import run
from time import monotonic
from typing import Optional

__all__ = ("get_network_interface_to_device_map",)

_network_interface_to_device_map_last_checked_at: Optional[float] = None
_network_interface_to_device_map_cached: Optional[dict[str, str]] = None


def get_network_interface_to_device_map() -> dict[str, str]:
    """Returns a (cached) mapping from network interface identifiers to the
    names of the corresponding network devices on macOS.
    """
    global _network_interface_to_device_map_cached
    global _network_interface_to_device_map_last_checked_at

    if _network_interface_to_device_map_last_checked_at is not None and (
        _network_interface_to_device_map_last_checked_at >= monotonic() - 5
    ):
        assert _network_interface_to_device_map_cached is not None
        return dict(_network_interface_to_device_map_cached)

    result = {}
    device, port = None, None

    process = run(["networksetup", "-listallhardwareports"], capture_output=True)
    if not process.returncode:
        for line in process.stdout.splitlines():
            line = line.strip()
            if line.startswith(b"Hardware Port: "):
                port = line[15:].decode("utf-8", "replace").strip()
            elif line.startswith(b"Device: "):
                device = line[7:].decode("utf-8", "replace").strip()
                if port:
                    result[device] = port
                    device, port = None, None
            elif not line:
                device, port = None, None

    _network_interface_to_device_map_cached = result
    _network_interface_to_device_map_last_checked_at = monotonic()

    return dict(result)
