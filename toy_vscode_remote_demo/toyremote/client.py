import argparse
import json
import shlex
import socket
from getpass import getpass
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.asymmetric import x25519

from toyremote.crypto_utils import (
    b64decode,
    b64encode,
    derive_session_key,
    public_key_fingerprint,
    verify_host_signature,
    x25519_public_bytes,
)
from toyremote.protocol import (
    recv_encrypted_json,
    recv_plain_json,
    send_encrypted_json,
    send_plain_json,
)


DEFAULT_KNOWN_HOSTS = ".toyremote_known_hosts.json"


class RemoteClient:
    def __init__(self, sock: socket.socket, session_key: bytes) -> None:
        self.sock = sock
        self.session_key = session_key

    def request(self, message: dict[str, Any]) -> dict[str, Any]:
        send_encrypted_json(self.sock, self.session_key, message)
        response = recv_encrypted_json(self.sock, self.session_key)
        if not response.get("ok"):
            raise RuntimeError(str(response.get("error", "unknown remote error")))
        return response.get("result", {})

    def close(self) -> None:
        try:
            self.request({"type": "close"})
        finally:
            self.sock.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Connect to a toy VS Code Remote-like server.")
    parser.add_argument("host", help="server hostname or IP")
    parser.add_argument("--port", type=int, default=2299, help="server TCP port")
    parser.add_argument("--username", default="demo", help="login username")
    parser.add_argument("--password", help="login password; prompted when omitted")
    parser.add_argument("--known-hosts", default=DEFAULT_KNOWN_HOSTS, help="known hosts JSON file")
    parser.add_argument("--trust-on-first-use", action="store_true", help="trust unknown host fingerprint")

    subparsers = parser.add_subparsers(dest="command_name", required=True)
    subparsers.add_parser("info", help="show remote workspace information")

    ls_parser = subparsers.add_parser("ls", help="list remote directory")
    ls_parser.add_argument("path", nargs="?", default=".")

    read_parser = subparsers.add_parser("read", help="read remote text file")
    read_parser.add_argument("path")

    write_parser = subparsers.add_parser("write", help="write remote text file")
    write_parser.add_argument("path")
    write_source = write_parser.add_mutually_exclusive_group(required=True)
    write_source.add_argument("--text", help="text to write")
    write_source.add_argument("--from-file", help="local file to read content from")

    search_parser = subparsers.add_parser("search", help="search text in remote workspace")
    search_parser.add_argument("query")
    search_parser.add_argument("path", nargs="?", default=".")
    search_parser.add_argument("--max-results", type=int, default=100)

    exec_parser = subparsers.add_parser("exec", help="execute command in remote workspace")
    exec_parser.add_argument("remote_command")

    subparsers.add_parser("repl", help="open interactive remote prompt")
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
        raise ValueError(f"host key mismatch for {host_id}; expected {expected}, got {fingerprint}")


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
    send_plain_json(sock, {"type": "client_hello", "kex_key": b64encode(client_kex_public)})

    server_public_key = x25519.X25519PublicKey.from_public_bytes(server_kex_public)
    shared_secret = client_kex_private.exchange(server_public_key)
    return derive_session_key(shared_secret, server_kex_public, client_kex_public)


def authenticate(sock: socket.socket, session_key: bytes, username: str, password: str) -> None:
    send_encrypted_json(sock, session_key, {"type": "auth", "username": username, "password": password})
    response = recv_encrypted_json(sock, session_key)
    if not response.get("ok"):
        raise PermissionError("authentication failed")


def connect(args: argparse.Namespace) -> RemoteClient:
    password = args.password if args.password is not None else getpass("Password: ")
    sock = socket.create_connection((args.host, args.port), timeout=10)
    try:
        session_key = perform_handshake(sock, args)
        authenticate(sock, session_key, args.username, password)
        return RemoteClient(sock, session_key)
    except Exception:
        sock.close()
        raise


def print_entries(result: dict[str, Any]) -> None:
    for entry in result["entries"]:
        marker = "d" if entry["type"] == "directory" else "f"
        print(f"{marker} {entry['size']:>10} {entry['path']}")


def print_search_results(result: dict[str, Any]) -> None:
    for item in result["results"]:
        print(f"{item['path']}:{item['line']}: {item['text']}")
    if result.get("truncated"):
        print("[results truncated]")


def print_exec_result(result: dict[str, Any]) -> None:
    if result.get("stdout"):
        print(result["stdout"], end="")
    if result.get("stderr"):
        print(result["stderr"], end="")
    print(f"\n[exit code: {result.get('exit_code')}]")


def run_single_command(client: RemoteClient, args: argparse.Namespace) -> None:
    if args.command_name == "info":
        print(json.dumps(client.request({"type": "workspace_info"}), indent=2, ensure_ascii=False))
    elif args.command_name == "ls":
        print_entries(client.request({"type": "list_dir", "path": args.path}))
    elif args.command_name == "read":
        print(client.request({"type": "read_file", "path": args.path})["content"], end="")
    elif args.command_name == "write":
        content = args.text
        if args.from_file:
            content = Path(args.from_file).read_text(encoding="utf-8")
        result = client.request({"type": "write_file", "path": args.path, "content": content})
        print(f"wrote {result['bytes']} bytes to {result['path']}")
    elif args.command_name == "search":
        result = client.request(
            {
                "type": "search_text",
                "query": args.query,
                "path": args.path,
                "max_results": args.max_results,
            }
        )
        print_search_results(result)
    elif args.command_name == "exec":
        print_exec_result(client.request({"type": "exec", "command": args.remote_command}))
    elif args.command_name == "repl":
        repl(client)


def repl(client: RemoteClient) -> None:
    print("Toy VS Code Remote REPL. Type 'help' for commands.")
    while True:
        try:
            line = input("remote> ").strip()
        except EOFError:
            print()
            return

        if not line:
            continue
        if line in {"exit", "quit"}:
            return
        if line == "help":
            print("info | ls [path] | read <path> | write <path> <text> | search <query> [path] | exec <command> | exit")
            continue

        try:
            parts = shlex.split(line)
            command = parts[0]
            if command == "info":
                print(json.dumps(client.request({"type": "workspace_info"}), indent=2, ensure_ascii=False))
            elif command == "ls":
                print_entries(client.request({"type": "list_dir", "path": parts[1] if len(parts) > 1 else "."}))
            elif command == "read" and len(parts) == 2:
                print(client.request({"type": "read_file", "path": parts[1]})["content"], end="")
            elif command == "write" and len(parts) >= 3:
                print(client.request({"type": "write_file", "path": parts[1], "content": " ".join(parts[2:])}))
            elif command == "search" and len(parts) >= 2:
                result = client.request(
                    {
                        "type": "search_text",
                        "query": parts[1],
                        "path": parts[2] if len(parts) > 2 else ".",
                    }
                )
                print_search_results(result)
            elif command == "exec" and len(parts) >= 2:
                print_exec_result(client.request({"type": "exec", "command": line[len("exec ") :]}))
            else:
                print("unknown or invalid command; type 'help'")
        except Exception as exc:
            print(f"error: {exc}")


def main() -> None:
    args = parse_args()
    client = connect(args)
    try:
        run_single_command(client, args)
    finally:
        client.close()


if __name__ == "__main__":
    main()
