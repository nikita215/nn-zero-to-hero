package com.example.tabletcoderemote

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import com.example.tabletcoderemote.shared.ConnectionState
import com.example.tabletcoderemote.ui.MainViewModel
import com.example.tabletcoderemote.web.WebIdeView

class MainActivity : ComponentActivity() {
    private val viewModel: MainViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                Surface(Modifier.fillMaxSize()) {
                    MainScreen(viewModel)
                }
            }
        }
    }
}

@Composable
private fun MainScreen(viewModel: MainViewModel) {
    var host by remember { mutableStateOf("") }
    var username by remember { mutableStateOf("ubuntu") }
    var password by remember { mutableStateOf("") }
    var workspace by remember { mutableStateOf("~") }
    val state = viewModel.state

    Column(Modifier.fillMaxSize().padding(24.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text("Tablet Code Remote", style = MaterialTheme.typography.headlineMedium)
        Text("Connect an Android tablet to a cloud Linux server over SSH, then open a localhost-only VS Code compatible server through an SSH tunnel.")
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            OutlinedTextField(host, { host = it }, label = { Text("Host") }, modifier = Modifier.weight(1f))
            OutlinedTextField(username, { username = it }, label = { Text("User") }, modifier = Modifier.weight(1f))
        }
        OutlinedTextField(workspace, { workspace = it }, label = { Text("Remote workspace") }, modifier = Modifier.fillMaxWidth())
        OutlinedTextField(
            password,
            { password = it },
            label = { Text("Password prototype auth") },
            visualTransformation = PasswordVisualTransformation(),
            modifier = Modifier.fillMaxWidth(),
        )
        Button(onClick = { viewModel.startPrototypeTunnel(host, username, password, workspace) }, enabled = host.isNotBlank() && username.isNotBlank()) {
            Text("Connect and start remote IDE")
        }
        when (state) {
            ConnectionState.Idle -> Text("Idle")
            ConnectionState.Connecting -> Text("Connecting…")
            is ConnectionState.Failed -> Text("Failed: ${state.message}")
            is ConnectionState.Connected -> {
                Text("Tunnel requested. Open the ready URL from the foreground notification, or bind service state in the next milestone.")
                WebIdeView(url = state.endpoint.localUrl, modifier = Modifier.fillMaxSize())
            }
        }
    }
}
