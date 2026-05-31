# Tablet Code Remote

Tablet Code Remote is a repository-ready Android MVP for a VS Code-compatible remote development client:

- Android tablet UI built with Jetpack Compose.
- SSH foreground service for long-lived remote sessions.
- Remote bootstrap script generation for `openvscode-server` or `code-server`.
- Localhost-only remote IDE binding plus SSH local port forwarding.
- WebView container for the VS Code-compatible web UI.
- A pure Kotlin `shared` module with tested bootstrap/script logic.

> This is an initial development scaffold. It intentionally starts with password authentication and a prototype host-key verifier in the foreground service so the feature path is visible. Before production, replace that verifier with persisted `known_hosts`, move secrets into Android Keystore, and expose tunnel readiness through a bound service or repository state.

## Architecture

```text
Android app
  ├─ Compose server form
  ├─ Foreground SSH tunnel service
  ├─ Remote bootstrap script executor
  ├─ Local port forwarder
  └─ WebView IDE shell

Cloud server
  ├─ ~/.tablet-code-remote/bin/openvscode-server or code-server
  ├─ ~/.tablet-code-remote/data
  ├─ ~/.tablet-code-remote/extensions
  └─ project workspace
```

The remote IDE must listen on `127.0.0.1` only. The Android app connects through SSH local forwarding, avoiding public exposure of the IDE HTTP port.

## Module layout

```text
settings.gradle.kts
build.gradle.kts
shared/  # Kotlin/JVM domain logic and tests
app/     # Android Compose/WebView/SSH prototype
```

## Development commands

```bash
# Pure JVM tests for the shared module
./gradlew :shared:test

# Android build once an Android SDK is available
./gradlew -PincludeAndroid=true :app:assembleDebug
```

This environment does not include an Android SDK, so only the shared Kotlin module can be verified here.

## First production hardening tasks

1. Replace `PromiscuousVerifier` with persistent host-key verification.
2. Store passwords/private keys with Android Keystore and `EncryptedSharedPreferences` or a custom keychain repository.
3. Report the actual ready endpoint from `RemoteIdeTunnelService` to Compose through a bound service, `StateFlow`, or persisted session store.
4. Add downloader/checksum verification for OpenVSCode Server/code-server releases.
5. Add key authentication, ProxyJump, SFTP upload, reconnect, and terminal diagnostics.
6. Restrict WebView navigation to `127.0.0.1` tunnel URLs and remove broad cleartext allowances.
