from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from functools import partial
from ipaddress import ip_address
from netifaces import AF_INET, AF_LINK, ifaddresses
from typing import (
    Callable,
    Iterable,
    Iterator,
    Optional,
    Sequence,
)

from .interfaces import list_network_interfaces
from .utils import aclosing
from .wired import is_carrier_detected, is_maybe_wired_or_wireless
from .wireless import get_connected_access_point_name, is_likely_wireless

__all__ = ("NetworkScanner", "NetworkScanResult", "NetworkScanResultItem")


class NetworkInterfaceType(Enum):
    WIRED = "wired"
    WIRELESS = "wireless"


@dataclass
class NetworkScanResultItem:
    """A single item in the result of a network scan."""

    #: Name of the network interface
    interface: str

    #: The type of the interface: wired or wireless
    type: NetworkInterfaceType

    #: Whether the network interface is connected
    connected: bool = False

    #: List of IPv4 addresses, netmasks and broadcast addresses of the interface
    addresses: Sequence[dict[str, str]] = field(default_factory=list)

    #: Name of the AP that the wireless interface is connected to, if known
    access_point_name: Optional[str] = None

    @property
    def first_address_and_netmask(self) -> Optional[str]:
        """Returns the first IPv4 address and netmask of the interface in slashed
        notation, if known, `None` otherwise.
        """
        addresses = self.get_networks_and_netmasks()
        return addresses[0] if addresses else None

    def get_networks_and_netmasks(self) -> list[str]:
        """Returns the list of IPv4 addresses and netmasks of the interface in
        slashed notation.
        """
        result: list[str] = []
        for address in self.addresses:
            addr = address.get("addr") or "-"
            netmask = address.get("netmask")
            if netmask:
                result.append(f"{addr} / {netmask}")
            else:
                result.append(str(addr))
        return result

    @property
    def wireless(self) -> bool:
        """Whether the network interface is wireless."""
        return self.type is NetworkInterfaceType.WIRELESS


#: Type specification for the result of a network scan
NetworkScanResult = list[NetworkScanResultItem]


def _is_loopback(item: dict[str, str]) -> bool:
    addr = item.get("addr")
    return ip_address(addr).is_loopback if addr is not None else False


class NetworkScanner:
    """Network scanner object that runs an asynchronous task that publishes
    network scans, i.e. summaries of which wired and wireless networks the
    machine is currently connected to.
    """

    _handlers: list[Callable[[NetworkScanResult], None]]
    _last_result: Optional[NetworkScanResult]

    def __init__(self) -> None:
        """Constructor."""
        self._handlers = []
        self._last_result = None

    def add_result_handler(
        self, func: Callable[[NetworkScanResult], None]
    ) -> Callable[[], None]:
        """Registers the given function to be called whenever the network
        scanner detects a possible change in the network configuration and
        produces a new network scan result.

        Parameters:
            func: the function to register. It must accept a single argument,
                which is the new network scan result

        Returns:
            a function that can be called with no arguments to unregister the
            handler function
        """
        self._handlers.append(func)
        return partial(self._remove_result_handler, func)

    @property
    def last_result(self) -> NetworkScanResult:
        """Returns the result of the last network scan."""
        return list(self._last_result or ())

    async def run(self) -> None:
        try:
            from aio_net_events import NetworkEventDetector
            from trio import to_thread
        except ImportError:
            raise RuntimeError(
                "you need to install the 'async' extra to use this class"
            ) from None

        detector = NetworkEventDetector()
        async with aclosing(detector.events()) as network_events:
            async for _ in network_events:
                # TODO(ntamas): debounce the events!
                try:
                    result = await to_thread.run_sync(self._scan_interfaces)
                except Exception:
                    raise

                self._last_result = result

                for handler in self._handlers:
                    handler(result)

    @contextmanager
    def use_result_handler(
        self, func: Callable[[NetworkScanResult], None]
    ) -> Iterator[None]:
        """Context manager that registers the given result handler function when
        the context is entered and unregisters the given result handler function
        when the context is exited.
        """
        disposer = self.add_result_handler(func)
        try:
            yield
        finally:
            disposer()

    def _find_relevant_interfaces(
        self,
    ) -> Iterable[tuple[str, Sequence[dict[str, str]]]]:
        """Finds the list of network interfaces that might be relevant to us
        in the sense that they probably represent a wired or wireless IPv4
        interface.

        Yields:
            pairs consisting of the name of a relevant network interface and
            its IPv4 addresses (or an empty list if the interface has no IPv4
            address)
        """
        for interface in list_network_interfaces():
            addresses = ifaddresses(interface)
            ipv4_addresses = addresses.get(AF_INET)
            if not ipv4_addresses:
                # No IPv4 address. It might be a disconnected network
                # interface so we continue if we have an Ethernet address
                # but nothing else.
                if (
                    len(addresses) == 1
                    and AF_LINK in addresses
                    and is_maybe_wired_or_wireless(interface)
                ):
                    yield interface, ipv4_addresses or []
            else:
                # If any of the addresses is the loopback address, then this
                # is the loopback interface so it is not relevant
                if not any(_is_loopback(addr) for addr in ipv4_addresses):
                    yield interface, ipv4_addresses

    def _remove_result_handler(self, func: Callable[[NetworkScanResult], None]) -> None:
        try:
            self._handlers.remove(func)
        except ValueError:
            pass

    def _scan_interfaces(self) -> list[NetworkScanResultItem]:
        """Scans the network interfaces of the current device and tries to
        figure our the wired and wireless IP addresses of the device as well
        as the name of the wireless AP that the device is connected to.
        """
        result = []

        for interface, addresses in self._find_relevant_interfaces():
            if is_likely_wireless(interface):
                access_point_name = get_connected_access_point_name(interface)
                item = NetworkScanResultItem(
                    interface=interface,
                    type=NetworkInterfaceType.WIRELESS,
                    connected=access_point_name is not None,
                    access_point_name=access_point_name,
                    addresses=addresses,
                )
            else:
                item = NetworkScanResultItem(
                    interface=interface,
                    type=NetworkInterfaceType.WIRED,
                    connected=is_carrier_detected(interface),
                    addresses=addresses,
                )
            result.append(item)

        return result


def test():
    import trio

    def handler(result: NetworkScanResult):
        print("Finished network scan.")
        if result:
            print("")
            for item in result:
                print(repr(item))
                print("---")
        print("")

    async def scan():
        scanner = NetworkScanner()
        with scanner.use_result_handler(handler):
            await scanner.run()

    trio.run(scan)


if __name__ == "__main__":
    test()
