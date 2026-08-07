package com.goldwaff.genservice.net

import com.jakewharton.retrofit2.converter.kotlinx.serialization.asConverterFactory
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import retrofit2.Retrofit
import java.util.concurrent.TimeUnit

/**
 * Builds a [GenServiceApi] for a given base URL. The base URL is user-editable
 * (see AppViewModel); a new client is created whenever it changes.
 */
object ApiClient {

    const val DEFAULT_BASE_URL = "http://10.0.2.2:8000/"

    private val json = Json {
        ignoreUnknownKeys = true
        explicitNulls = false
        coerceInputValues = true
    }

    fun create(baseUrl: String): GenServiceApi {
        val normalized = if (baseUrl.endsWith("/")) baseUrl else "$baseUrl/"
        val client = OkHttpClient.Builder()
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(15, TimeUnit.SECONDS)
            .build()
        val contentType = "application/json".toMediaType()
        return Retrofit.Builder()
            .baseUrl(normalized)
            .client(client)
            .addConverterFactory(json.asConverterFactory(contentType))
            .build()
            .create(GenServiceApi::class.java)
    }
}
