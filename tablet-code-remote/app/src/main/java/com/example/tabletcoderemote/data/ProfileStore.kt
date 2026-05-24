package com.example.tabletcoderemote.data

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.example.tabletcoderemote.shared.ServerProfile
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import kotlinx.serialization.decodeFromString
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json

private val Context.profileDataStore by preferencesDataStore("profiles")

class ProfileStore(private val context: Context) {
    private val json = Json { ignoreUnknownKeys = true; prettyPrint = true }
    private val profilesKey = stringPreferencesKey("server_profiles")

    val profiles: Flow<List<ServerProfile>> = context.profileDataStore.data.map { prefs ->
        prefs[profilesKey]?.let { json.decodeFromString<List<ServerProfile>>(it) } ?: emptyList()
    }

    suspend fun saveProfiles(profiles: List<ServerProfile>) {
        context.profileDataStore.edit { prefs -> prefs[profilesKey] = json.encodeToString(profiles) }
    }
}
