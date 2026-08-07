package com.goldwaff.genservice.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.goldwaff.genservice.net.ApiClient
import com.goldwaff.genservice.net.DashboardDto
import com.goldwaff.genservice.net.GenServiceApi
import com.goldwaff.genservice.net.GeneratorDto
import com.goldwaff.genservice.net.WorkOrderDto
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/** Generic screen state: loading, error, or loaded data. */
sealed interface UiState<out T> {
    data object Loading : UiState<Nothing>
    data class Error(val message: String) : UiState<Nothing>
    data class Data<T>(val value: T) : UiState<T>
}

/** A generator row annotated with whether it is currently due for maintenance. */
data class GeneratorRow(val generator: GeneratorDto, val isDue: Boolean)

class AppViewModel : ViewModel() {

    private val _baseUrl = MutableStateFlow(ApiClient.DEFAULT_BASE_URL)
    val baseUrl: StateFlow<String> = _baseUrl.asStateFlow()

    private val _dashboard = MutableStateFlow<UiState<DashboardDto>>(UiState.Loading)
    val dashboard: StateFlow<UiState<DashboardDto>> = _dashboard.asStateFlow()

    private val _workOrders = MutableStateFlow<UiState<List<WorkOrderDto>>>(UiState.Loading)
    val workOrders: StateFlow<UiState<List<WorkOrderDto>>> = _workOrders.asStateFlow()

    private val _generators = MutableStateFlow<UiState<List<GeneratorRow>>>(UiState.Loading)
    val generators: StateFlow<UiState<List<GeneratorRow>>> = _generators.asStateFlow()

    private var api: GenServiceApi = ApiClient.create(_baseUrl.value)

    init {
        refreshAll()
    }

    /** Point the app at a different backend and reload everything. */
    fun setBaseUrl(url: String) {
        val trimmed = url.trim()
        if (trimmed.isEmpty() || trimmed == _baseUrl.value) return
        _baseUrl.value = trimmed
        api = ApiClient.create(trimmed)
        refreshAll()
    }

    fun refreshAll() {
        loadDashboard()
        loadWorkOrders()
        loadGenerators()
    }

    fun loadDashboard() {
        _dashboard.value = UiState.Loading
        viewModelScope.launch {
            _dashboard.value = try {
                UiState.Data(api.dashboard())
            } catch (e: Exception) {
                UiState.Error(e.friendly())
            }
        }
    }

    fun loadWorkOrders() {
        _workOrders.value = UiState.Loading
        viewModelScope.launch {
            _workOrders.value = try {
                UiState.Data(api.workOrders())
            } catch (e: Exception) {
                UiState.Error(e.friendly())
            }
        }
    }

    fun loadGenerators() {
        _generators.value = UiState.Loading
        viewModelScope.launch {
            _generators.value = try {
                val all = api.generators()
                val dueIds = api.generatorsDue().map { it.id }.toSet()
                UiState.Data(all.map { GeneratorRow(it, it.id in dueIds) })
            } catch (e: Exception) {
                UiState.Error(e.friendly())
            }
        }
    }

    private fun Exception.friendly(): String =
        message?.takeIf { it.isNotBlank() } ?: this::class.simpleName ?: "Request failed"
}
