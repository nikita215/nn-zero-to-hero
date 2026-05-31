import argparse
import json
import socket
from getpass import getpass
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric import x25519

from toyssh.crypto_utils import (
    b64decode,
    b64encode,
    derive_session_key,
    public_key_fingerprint,
    verify_host_signature,
    x25519_public_bytes,
)
from toyssh.protocol import (
    recv_encrypted_json,
    recv_plain_json,
    send_encrypted_json,
    send_plain_json,
)


DEFAULT_KNOWN_HOSTS = ".toyssh_known_hosts.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Connect to a tiny educational SSH-like server.")
    parser.add_argument("host", help="server hostname or IP")
    parser.add_argument("--port", type=int, default=2222, help="server TCP port")
    parser.add_argument("--username", default="demo", help="login username")
    parser.add_argument("--password", help="login password; prompted when omitted")
    parser.add_argument("--command", required=True, help="command to execute on the server")
    parser.add_argument(
        "--known-hosts",
        default=DEFAULT_KNOWN_HOSTS,
        help="known hosts JSON file",
    )
    parser.add_argument(
        "--trust-on-first-use",
        action="store_true",
        help="store unknown host fingerprints on first connection",
    )
    return parser.parse_args()


def load_known_hosts(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_known_hosts(path: Path, known_hosts: dict[str, str]) -> None:
    path.write_text(json.dumps(known_hosts, indent=2, sort_keys=True), encoding="utf-8")


def verify_known_host(
    host_id: str,
    fingerprint: str,
    known_hosts_path: Path,
    trust_on_first_use: bool,
) -> None:
    known_hosts = load_known_hosts(known_hosts_path)
    expected = known_hosts.get(host_id)

    if expected is None:
        if not trust_on_first_use:
            raise ValueError(
                f"unknown host {host_id} with fingerprint {fingerprint}; "
                "re-run with --trust-on-first-use to trust it"
            )
        known_hosts[host_id] = fingerprint
        save_known_hosts(known_hosts_path, known_hosts)
        print(f"[+] trusted new host {host_id}: {fingerprint}")
        return

    if expected != fingerprint:
        raise ValueError(
            f"host key mismatch for {host_id}; expected {expected}, got {fingerprint}"
        )


def perform_handshake(sock: socket.socket, args: argparse.Namespace) -> bytes:
    server_hello = recv_plain_json(sock)
    if server_hello.get("type") != "server_hello":
        raise ValueError("expected server_hello")

    host_public_bytes = b64decode(server_hello["host_key"])
    server_kex_public = b64decode(server_hello["kex_key"])
    signature = b64decode(server_hello["signature"])
    fingerprint = public_key_fingerprint(host_public_bytes)

    verify_host_signature(host_public_bytes, server_kex_public, signature)
    verify_known_host(
        f"{args.host}:{args.port}",
        fingerprint,
        Path(args.known_hosts),
        args.trust_on_first_use,
    )

    client_kex_private = x25519.X25519PrivateKey.generate()
    client_kex_public = x25519_public_bytes(client_kex_private.public_key())

    send_plain_json(
        sock,
        {
            "type": "client_hello",
            "kex_key": b64encode(client_kex_public),
        },
    )

    server_public_key = x25519.X25519PublicKey.from_public_bytes(server_kex_public)
    shared_secret = client_kex_private.exchange(server_public_key)
    return derive_session_key(shared_secret, server_kex_public, client_kex_public)


def authenticate(sock: socket.socket, session_key: bytes, username: str, password: str) -> None:
    send_encrypted_json(
        sock,
        session_key,
        {
            "type": "auth",
            "username": username,
            "password": password,
        },
    )

    response = recv_encrypted_json(sock, session_key)
    if not response.get("ok"):
        raise PermissionError("authentication failed")


def main() -> None:
    args = parse_args()
    password = args.password if args.password is not None else getpass("Password: ")

    with socket.create_connection((args.host, args.port), timeout=10) as sock:
        session_key = perform_handshake(sock, args)
        authenticate(sock, session_key, args.username, password)

        send_encrypted_json(
            sock,
            session_key,
            {
                "type": "exec",
                "command": args.command,
            },
        )

        result = recv_encrypted_json(sock, session_key)
        if result.get("type") != "exec_result":
            raise RuntimeError(f"unexpected server response: {result}")

    stdout = result.get("stdout", "")
    stderr = result.get("stderr", "")
    exit_code = result.get("exit_code", 1)

    if stdout:
        print(stdout, end="")
    if stderr:
        print(stderr, end="")
    print(f"\n[exit code: {exit_code}]")


if __name__ == "__main__":
    main()
