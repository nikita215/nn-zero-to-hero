import argparse
import socket
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.asymmetric import x25519

from toyremote.crypto_utils import (
    b64decode,
    b64encode,
    derive_session_key,
    ed25519_public_bytes,
    load_or_create_host_key,
    public_key_fingerprint,
    x25519_public_bytes,
)
from toyremote.protocol import (
    recv_encrypted_json,
    recv_plain_json,
    send_encrypted_json,
    send_plain_json,
)
from toyremote.workspace import RemoteWorkspace


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a toy VS Code Remote-like server.")
    parser.add_argument("--host", default="127.0.0.1", help="host/IP to bind")
    parser.add_argument("--port", type=int, default=2299, help="TCP port to bind")
    parser.add_argument("--workspace", default=".", help="remote workspace root")
    parser.add_argument("--username", default="demo", help="demo login username")
    parser.add_argument("--password", default="demo", help="demo login password")
    parser.add_argument("--host-key", default="config/host_ed25519.key", help="server host key path")
    parser.add_argument("--command-timeout", type=int, default=10, help="command timeout seconds")
    return parser.parse_args()


def perform_handshake(conn: socket.socket, host_key_path: Path) -> bytes:
    host_private_key = load_or_create_host_key(host_key_path)
    host_public_bytes = ed25519_public_bytes(host_private_key.public_key())

    server_kex_private = x25519.X25519PrivateKey.generate()
    server_kex_public = x25519_public_bytes(server_kex_private.public_key())
    signature = host_private_key.sign(server_kex_public)

    send_plain_json(
        conn,
        {
            "type": "server_hello",
            "host_key": b64encode(host_public_bytes),
            "host_key_fingerprint": public_key_fingerprint(host_public_bytes),
            "kex_key": b64encode(server_kex_public),
            "signature": b64encode(signature),
        },
    )

    client_hello = recv_plain_json(conn)
    if client_hello.get("type") != "client_hello":
        raise ValueError("expected client_hello")

    client_kex_public = b64decode(client_hello["kex_key"])
    client_public_key = x25519.X25519PublicKey.from_public_bytes(client_kex_public)
    shared_secret = server_kex_private.exchange(client_public_key)
    return derive_session_key(shared_secret, server_kex_public, client_kex_public)


def authenticate(conn: socket.socket, session_key: bytes, username: str, password: str) -> bool:
    request = recv_encrypted_json(conn, session_key)
    ok = (
        request.get("type") == "auth"
        and request.get("username") == username
        and request.get("password") == password
    )
    send_encrypted_json(conn, session_key, {"type": "auth_response", "ok": ok})
    return ok


def ok(result: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"ok": True, "result": result or {}}


def error(message: str) -> dict[str, Any]:
    return {"ok": False, "error": message}


def dispatch(workspace: RemoteWorkspace, request: dict[str, Any]) -> dict[str, Any]:
    request_type = request.get("type")

    if request_type == "workspace_info":
        return ok(workspace.info())
    if request_type == "list_dir":
        return ok(workspace.list_dir(request.get("path", ".")))
    if request_type == "read_file":
        return ok(workspace.read_file(str(request.get("path", ""))))
    if request_type == "write_file":
        return ok(workspace.write_file(str(request.get("path", "")), str(request.get("content", ""))))
    if request_type == "search_text":
        return ok(
            workspace.search_text(
                str(request.get("query", "")),
                request.get("path", "."),
                int(request.get("max_results", 100)),
            )
        )
    if request_type == "exec":
        return ok(workspace.exec_command(str(request.get("command", ""))))
    if request_type == "close":
        return ok({"closed": True})

    return error(f"unknown request type: {request_type}")


def handle_client(
    conn: socket.socket,
    address: tuple[str, int],
    args: argparse.Namespace,
    workspace: RemoteWorkspace,
) -> None:
    with conn:
        print(f"[+] client connected: {address[0]}:{address[1]}")
        session_key = perform_handshake(conn, Path(args.host_key))

        if not authenticate(conn, session_key, args.username, args.password):
            print("[-] authentication failed")
            return

        while True:
            try:
                request = recv_encrypted_json(conn, session_key)
            except ConnectionError:
                break

            try:
                response = dispatch(workspace, request)
            except Exception as exc:
                response = error(str(exc))

            send_encrypted_json(conn, session_key, response)

            if request.get("type") == "close":
                break

        print(f"[-] client disconnected: {address[0]}:{address[1]}")


def main() -> None:
    args = parse_args()
    workspace = RemoteWorkspace(Path(args.workspace), command_timeout=args.command_timeout)
    host_key = load_or_create_host_key(Path(args.host_key))
    host_public_bytes = ed25519_public_bytes(host_key.public_key())

    print(f"Toy VS Code Remote server listening on {args.host}:{args.port}")
    print(f"Workspace: {workspace.root}")
    print(f"Host key fingerprint: {public_key_fingerprint(host_public_bytes)}")
    print("Demo credentials:", f"{args.username}/{args.password}")
    print("Warning: this demo can execute shell commands inside the workspace.")

    with socket.create_server((args.host, args.port), reuse_port=False) as server:
        while True:
            conn, address = server.accept()
            try:
                handle_client(conn, address, args, workspace)
            except Exception as exc:
                print(f"[-] client error: {exc}")
                conn.close()


if __name__ == "__main__":
    main()
