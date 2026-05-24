package com.example.tabletcoderemote.shared

import kotlinx.serialization.Serializable

@Serializable
data class ServerProfile(
    val id: String,
    val displayName: String,
    val host: String,
    val port: Int = 22,
    val username: String,
    val workspacePath: String = "~",
    val privateKeyAlias: String? = null,
    val passwordAlias: String? = null,
    val proxyJump: String? = null,
)

enum class IdeServerKind {
    OpenVSCodeServer,
    CodeServer,
}

@Serializable
data class IdeServerConfig(
    val kind: IdeServerKind = IdeServerKind.OpenVSCodeServer,
    val version: String = "latest",
    val installRoot: String = "~/.tablet-code-remote",
    val remotePort: Int = 0,
)

data class RemoteIdeEndpoint(
    val localPort: Int,
    val remotePort: Int,
    val token: String,
) {
    val localUrl: String = "http://127.0.0.1:$localPort/?tkn=$token"
}

sealed interface ConnectionState {
    data object Idle : ConnectionState
    data object Connecting : ConnectionState
    data class Connected(val endpoint: RemoteIdeEndpoint) : ConnectionState
    data class Failed(val message: String) : ConnectionState
}
