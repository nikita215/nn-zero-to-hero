import base64
import hashlib
import os
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, x25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


def b64encode(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def b64decode(data: str) -> bytes:
    return base64.b64decode(data.encode("ascii"))


def public_key_fingerprint(public_key_bytes: bytes) -> str:
    digest = hashlib.sha256(public_key_bytes).digest()
    return "SHA256:" + base64.b64encode(digest).decode("ascii").rstrip("=")


def load_or_create_host_key(path: Path) -> ed25519.Ed25519PrivateKey:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        private_bytes = path.read_bytes()
        return serialization.load_pem_private_key(private_bytes, password=None)

    private_key = ed25519.Ed25519PrivateKey.generate()
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    path.write_bytes(private_bytes)
    return private_key


def ed25519_public_bytes(public_key: ed25519.Ed25519PublicKey) -> bytes:
    return public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )


def x25519_public_bytes(public_key: x25519.X25519PublicKey) -> bytes:
    return public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )


def verify_host_signature(host_public_bytes: bytes, message: bytes, signature: bytes) -> None:
    public_key = ed25519.Ed25519PublicKey.from_public_bytes(host_public_bytes)
    try:
        public_key.verify(signature, message)
    except InvalidSignature as exc:
        raise ValueError("server host key signature is invalid") from exc


def derive_session_key(shared_secret: bytes, server_kex_public: bytes, client_kex_public: bytes) -> bytes:
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=server_kex_public + client_kex_public,
        info=b"toyssh-session-key-v1",
    ).derive(shared_secret)


def encrypt_json_bytes(session_key: bytes, plaintext: bytes) -> bytes:
    nonce = os.urandom(12)
    ciphertext = AESGCM(session_key).encrypt(nonce, plaintext, None)
    return nonce + ciphertext


def decrypt_json_bytes(session_key: bytes, payload: bytes) -> bytes:
    if len(payload) < 13:
        raise ValueError("encrypted payload is too short")

    nonce = payload[:12]
    ciphertext = payload[12:]
    return AESGCM(session_key).decrypt(nonce, ciphertext, None)
