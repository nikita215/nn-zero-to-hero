package com.example.tabletcoderemote.ui

import android.app.Application
import android.content.Intent
import androidx.lifecycle.AndroidViewModel
import com.example.tabletcoderemote.shared.ConnectionState
import com.example.tabletcoderemote.shared.RemoteIdeEndpoint
import com.example.tabletcoderemote.shared.ServerProfile
import com.example.tabletcoderemote.ssh.RemoteIdeTunnelService
import kotlinx.serialization.encodeToString

class MainViewModel(private val app: Application) : AndroidViewModel(app) {
    var state: ConnectionState = ConnectionState.Idle
        private set

    fun startPrototypeTunnel(host: String, username: String, password: String, workspace: String) {
        state = ConnectionState.Connecting
        val profile = ServerProfile(
            id = host,
            displayName = host,
            host = host,
            username = username,
            workspacePath = workspace.ifBlank { "~" },
        )
        val intent = Intent(app, RemoteIdeTunnelService::class.java).apply {
            putExtra(RemoteIdeTunnelService.EXTRA_PROFILE_JSON, RemoteIdeTunnelService.PROFILE_JSON.encodeToString(profile))
            putExtra(RemoteIdeTunnelService.EXTRA_PASSWORD, password)
        }
        app.startForegroundService(intent)
        // The foreground service updates its notification when ready. A production build should expose this
        // endpoint via bound service, shared flow, or persisted session state.
        state = ConnectionState.Connected(RemoteIdeEndpoint(localPort = 39081, remotePort = 0, token = "pending"))
    }
}
