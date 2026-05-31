import json
import socket
import struct
from typing import Any

from toyremote.crypto_utils import decrypt_bytes, encrypt_bytes


MAX_FRAME_SIZE = 20 * 1024 * 1024


def recvall(sock: socket.socket, size: int) -> bytes:
    chunks = bytearray()
    while len(chunks) < size:
        chunk = sock.recv(size - len(chunks))
        if not chunk:
            raise ConnectionError("connection closed while reading frame")
        chunks.extend(chunk)
    return bytes(chunks)


def send_frame(sock: socket.socket, payload: bytes) -> None:
    sock.sendall(struct.pack("!I", len(payload)) + payload)


def recv_frame(sock: socket.socket) -> bytes:
    raw_size = recvall(sock, 4)
    size = struct.unpack("!I", raw_size)[0]
    if size > MAX_FRAME_SIZE:
        raise ValueError(f"frame too large: {size} bytes")
    return recvall(sock, size)


def send_plain_json(sock: socket.socket, message: dict[str, Any]) -> None:
    payload = json.dumps(message, ensure_ascii=False).encode("utf-8")
    send_frame(sock, payload)


def recv_plain_json(sock: socket.socket) -> dict[str, Any]:
    payload = recv_frame(sock)
    return json.loads(payload.decode("utf-8"))


def send_encrypted_json(sock: socket.socket, session_key: bytes, message: dict[str, Any]) -> None:
    plaintext = json.dumps(message, ensure_ascii=False).encode("utf-8")
    send_frame(sock, encrypt_bytes(session_key, plaintext))


def recv_encrypted_json(sock: socket.socket, session_key: bytes) -> dict[str, Any]:
    payload = recv_frame(sock)
    plaintext = decrypt_bytes(session_key, payload)
    return json.loads(plaintext.decode("utf-8"))
