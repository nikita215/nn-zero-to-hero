import argparse
import socket
import subprocess
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric import x25519

from toyssh.crypto_utils import (
    b64decode,
    b64encode,
    derive_session_key,
    ed25519_public_bytes,
    load_or_create_host_key,
    public_key_fingerprint,
    x25519_public_bytes,
)
from toyssh.protocol import (
    recv_encrypted_json,
    recv_plain_json,
    send_encrypted_json,
    send_plain_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a tiny educational SSH-like server.")
    parser.add_argument("--host", default="127.0.0.1", help="host/IP to bind")
    parser.add_argument("--port", type=int, default=2222, help="TCP port to bind")
    parser.add_argument("--username", default="demo", help="demo login username")
    parser.add_argument("--password", default="demo", help="demo login password")
    parser.add_argument(
        "--host-key",
        default="config/host_ed25519.key",
        help="path to the server Ed25519 host private key",
    )
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
    if request.get("type") != "auth":
        send_encrypted_json(conn, session_key, {"type": "auth_response", "ok": False})
        return False

    ok = request.get("username") == username and request.get("password") == password
    send_encrypted_json(conn, session_key, {"type": "auth_response", "ok": ok})
    return ok


def run_command(command: str, timeout: int) -> dict[str, object]:
    try:
        completed = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "type": "exec_result",
            "exit_code": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "type": "exec_result",
            "exit_code": 124,
            "stdout": exc.stdout or "",
            "stderr": f"command timed out after {timeout} seconds",
        }


def handle_client(conn: socket.socket, address: tuple[str, int], args: argparse.Namespace) -> None:
    with conn:
        print(f"[+] client connected: {address[0]}:{address[1]}")
        session_key = perform_handshake(conn, Path(args.host_key))

        if not authenticate(conn, session_key, args.username, args.password):
            print("[-] authentication failed")
            return

        request = recv_encrypted_json(conn, session_key)
        if request.get("type") != "exec":
            send_encrypted_json(conn, session_key, {"type": "error", "message": "expected exec request"})
            return

        command = str(request.get("command", ""))
        print(f"[>] executing command: {command}")
        result = run_command(command, args.command_timeout)
        send_encrypted_json(conn, session_key, result)


def main() -> None:
    args = parse_args()
    host_key = load_or_create_host_key(Path(args.host_key))
    host_public_bytes = ed25519_public_bytes(host_key.public_key())

    print(f"Toy SSH server listening on {args.host}:{args.port}")
    print(f"Host key fingerprint: {public_key_fingerprint(host_public_bytes)}")
    print("Demo credentials:", f"{args.username}/{args.password}")
    print("Warning: this demo executes shell commands from authenticated clients.")

    with socket.create_server((args.host, args.port), reuse_port=False) as server:
        while True:
            conn, address = server.accept()
            try:
                handle_client(conn, address, args)
            except Exception as exc:
                print(f"[-] client error: {exc}")
                conn.close()


if __name__ == "__main__":
    main()
