package com.example.tabletcoderemote.shared

/**
 * Builds the remote shell script that installs and starts a localhost-only VS Code compatible server.
 * The Android app executes this script over SSH, then opens the returned port through SSH forwarding.
 */
class BootstrapScriptBuilder {
    fun build(config: IdeServerConfig, workspacePath: String, token: String): String {
        val safeWorkspace = shellQuote(workspacePath)
        val safeRoot = shellQuote(config.installRoot)
        val safeToken = shellQuote(token)
        return when (config.kind) {
            IdeServerKind.OpenVSCodeServer -> openVSCodeScript(config, safeRoot, safeWorkspace, safeToken)
            IdeServerKind.CodeServer -> codeServerScript(config, safeRoot, safeWorkspace, safeToken)
        }.trimIndent()
    }

    private fun openVSCodeScript(
        config: IdeServerConfig,
        safeRoot: String,
        safeWorkspace: String,
        safeToken: String,
    ): String = """
        set -eu
        ROOT=$safeRoot
        KIND=openvscode-server
        VERSION=${shellQuote(config.version)}
        PORT=${config.remotePort}
        WORKSPACE=$safeWorkspace
        TOKEN=$safeToken
        mkdir -p "${'$'}ROOT/bin" "${'$'}ROOT/data" "${'$'}ROOT/extensions" "${'$'}ROOT/logs"
        if [ ! -x "${'$'}ROOT/bin/openvscode-server" ]; then
          echo "TABLET_CODE_ERROR missing_openvscode_server_binary"
          echo "Install openvscode-server into ${'$'}ROOT/bin/openvscode-server or enable the downloader in a future release."
          exit 42
        fi
        if [ "${'$'}PORT" = "0" ]; then
          PORT=$(python3 - <<'PY'
import socket
s=socket.socket(); s.bind(('127.0.0.1', 0)); print(s.getsockname()[1]); s.close()
PY
)
        fi
        nohup "${'$'}ROOT/bin/openvscode-server" \
          --host 127.0.0.1 \
          --port "${'$'}PORT" \
          --connection-token "${'$'}TOKEN" \
          --server-data-dir "${'$'}ROOT/data" \
          --extensions-dir "${'$'}ROOT/extensions" \
          "${'$'}WORKSPACE" > "${'$'}ROOT/logs/server.log" 2>&1 &
        echo "TABLET_CODE_REMOTE_PORT=${'$'}PORT"
    """

    private fun codeServerScript(
        config: IdeServerConfig,
        safeRoot: String,
        safeWorkspace: String,
        safeToken: String,
    ): String = """
        set -eu
        ROOT=$safeRoot
        PORT=${config.remotePort}
        WORKSPACE=$safeWorkspace
        TOKEN=$safeToken
        mkdir -p "${'$'}ROOT/bin" "${'$'}ROOT/data" "${'$'}ROOT/extensions" "${'$'}ROOT/logs"
        if [ ! -x "${'$'}ROOT/bin/code-server" ]; then
          echo "TABLET_CODE_ERROR missing_code_server_binary"
          echo "Install code-server into ${'$'}ROOT/bin/code-server or enable the downloader in a future release."
          exit 42
        fi
        if [ "${'$'}PORT" = "0" ]; then
          PORT=$(python3 - <<'PY'
import socket
s=socket.socket(); s.bind(('127.0.0.1', 0)); print(s.getsockname()[1]); s.close()
PY
)
        fi
        PASSWORD="${'$'}TOKEN" nohup "${'$'}ROOT/bin/code-server" \
          --bind-addr "127.0.0.1:${'$'}PORT" \
          --auth password \
          --user-data-dir "${'$'}ROOT/data" \
          --extensions-dir "${'$'}ROOT/extensions" \
          "${'$'}WORKSPACE" > "${'$'}ROOT/logs/server.log" 2>&1 &
        echo "TABLET_CODE_REMOTE_PORT=${'$'}PORT"
    """

    fun parseRemotePort(stdout: String): Int? =
        Regex("TABLET_CODE_REMOTE_PORT=(\\d+)")
            .find(stdout)
            ?.groupValues
            ?.get(1)
            ?.toIntOrNull()

    private fun shellQuote(value: String): String = "'" + value.replace("'", "'\\''") + "'"
}
