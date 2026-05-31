package com.example.tabletcoderemote.ssh

import java.net.ServerSocket

fun allocateLocalPort(): Int = ServerSocket(0).use { it.localPort }
