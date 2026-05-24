package com.example.tabletcoderemote.shared

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotNull
import kotlin.test.assertTrue

class BootstrapScriptBuilderTest {
    private val builder = BootstrapScriptBuilder()

    @Test
    fun `builds localhost only openvscode server command`() {
        val script = builder.build(
            config = IdeServerConfig(kind = IdeServerKind.OpenVSCodeServer, remotePort = 3000),
            workspacePath = "/home/dev/project with spaces",
            token = "secret-token",
        )

        assertTrue(script.contains("--host 127.0.0.1"))
        assertTrue(script.contains("--port \"${'$'}PORT\""))
        assertTrue(script.contains("'/home/dev/project with spaces'"))
        assertTrue(script.contains("TABLET_CODE_REMOTE_PORT=${'$'}PORT"))
    }

    @Test
    fun `quotes single quotes safely`() {
        val script = builder.build(
            config = IdeServerConfig(),
            workspacePath = "/home/dev/it's-fine",
            token = "tok'en",
        )

        assertTrue(script.contains("'/home/dev/it'\\''s-fine'"))
        assertTrue(script.contains("'tok'\\''en'"))
    }

    @Test
    fun `parses remote port from stdout`() {
        val port = builder.parseRemotePort("log\nTABLET_CODE_REMOTE_PORT=39123\n")
        assertNotNull(port)
        assertEquals(39123, port)
    }
}
