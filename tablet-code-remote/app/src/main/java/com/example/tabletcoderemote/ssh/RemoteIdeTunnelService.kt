package com.example.tabletcoderemote.ssh

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.os.IBinder
import com.example.tabletcoderemote.shared.BootstrapScriptBuilder
import com.example.tabletcoderemote.shared.IdeServerConfig
import com.example.tabletcoderemote.shared.RemoteIdeEndpoint
import com.example.tabletcoderemote.shared.ServerProfile
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import net.schmizz.sshj.SSHClient
import net.schmizz.sshj.connection.channel.direct.Parameters
import net.schmizz.sshj.transport.verification.PromiscuousVerifier
import java.security.SecureRandom
import java.net.ServerSocket
import java.util.Base64

/**
 * Foreground service that keeps an SSH session and local port-forward alive while the IDE is open.
 * Host-key persistence and encrypted credential retrieval are intentionally isolated as TODOs so the
 * MVP never silently trusts production hosts beyond the explicit prototype verifier used here.
 */
class RemoteIdeTunnelService : Service() {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private var ssh: SSHClient? = null

    override fun onCreate() {
        super.onCreate()
        ensureChannel()
        startForeground(ONGOING_ID, notification("Preparing remote IDE tunnel"))
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        scope.launch {
            val profile = intent?.getStringExtra(EXTRA_PROFILE_JSON)?.let { PROFILE_JSON.decodeFromString<ServerProfile>(it) }
                ?: return@launch stopSelf()
            val password = intent.getStringExtra(EXTRA_PASSWORD)
            runCatching { connect(profile, password) }
                .onFailure { stopSelf() }
        }
        return START_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        ssh?.disconnect()
        scope.cancel()
        super.onDestroy()
    }

    private fun connect(profile: ServerProfile, password: String?) {
        val client = SSHClient()
        // TODO: replace with persistent known_hosts verification before production release.
        client.addHostKeyVerifier(PromiscuousVerifier())
        client.connect(profile.host, profile.port)
        if (password != null) client.authPassword(profile.username, password) else error("Password auth required for MVP service")
        ssh = client

        val token = randomToken()
        val script = BootstrapScriptBuilder().build(IdeServerConfig(), profile.workspacePath, token)
        val stdout = client.startSession().use { session ->
            val cmd = session.exec("bash -lc ${shellQuote(script)}")
            val text = cmd.inputStream.bufferedReader().readText()
            cmd.join()
            text
        }
        val remotePort = BootstrapScriptBuilder().parseRemotePort(stdout) ?: error("Remote server did not report a port")
        val localPort = allocateLocalPort()
        val endpoint = RemoteIdeEndpoint(localPort = localPort, remotePort = remotePort, token = token)
        startForeground(ONGOING_ID, notification("IDE ready at ${endpoint.localUrl}"))
        client.newLocalPortForwarder(
            Parameters("127.0.0.1", localPort, "127.0.0.1", remotePort),
            ServerSocket(localPort),
        ).listen()
    }

    private fun ensureChannel() {
        val manager = getSystemService(NotificationManager::class.java)
        manager.createNotificationChannel(NotificationChannel(CHANNEL_ID, "Remote IDE tunnel", NotificationManager.IMPORTANCE_LOW))
    }

    private fun notification(text: String): Notification = Notification.Builder(this, CHANNEL_ID)
        .setContentTitle("Tablet Code Remote")
        .setContentText(text)
        .setSmallIcon(android.R.drawable.stat_sys_upload_done)
        .build()

    private fun randomToken(): String {
        val bytes = ByteArray(32)
        SecureRandom().nextBytes(bytes)
        return Base64.getUrlEncoder().withoutPadding().encodeToString(bytes)
    }

    private fun shellQuote(value: String): String = "'" + value.replace("'", "'\\''") + "'"

    companion object {
        const val EXTRA_PROFILE_JSON = "profile_json"
        const val EXTRA_PASSWORD = "password"
        private const val CHANNEL_ID = "remote_ide_tunnel"
        private const val ONGOING_ID = 1001
        val PROFILE_JSON = kotlinx.serialization.json.Json { ignoreUnknownKeys = true }
    }
}
