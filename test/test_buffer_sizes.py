import trio.socket

from flockwave.networking import (
    create_socket,
    maximize_socket_receive_buffer_size,
    maximize_socket_send_buffer_size,
)


async def test_maximize_socket_receive_buffer_size():
    sock = create_socket(trio.socket.SOCK_STREAM)
    original_size = sock.getsockopt(trio.socket.SOL_SOCKET, trio.socket.SO_RCVBUF)
    new_size = maximize_socket_receive_buffer_size(sock)
    assert new_size > original_size, (
        "The new receive buffer size should be larger than the original size."
    )

    even_newer_size = maximize_socket_receive_buffer_size(sock)
    assert new_size == even_newer_size, (
        "maximize_socket_receive_buffer_size should not change the size again "
        "if it is already maximized."
    )


async def test_maximize_socket_send_buffer_size():
    sock = create_socket(trio.socket.SOCK_STREAM)
    original_size = sock.getsockopt(trio.socket.SOL_SOCKET, trio.socket.SO_SNDBUF)

    new_size = maximize_socket_send_buffer_size(sock)
    assert new_size > original_size, (
        "The new send buffer size should be larger than the original size."
    )

    even_newer_size = maximize_socket_send_buffer_size(sock)
    assert new_size == even_newer_size, (
        "maximize_socket_send_buffer_size should not change the size again "
        "if it is already maximized."
    )
