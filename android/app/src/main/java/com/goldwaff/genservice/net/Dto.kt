package com.goldwaff.genservice.net

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/**
 * Data-transfer objects mirroring a subset of the backend JSON. Unknown fields
 * are ignored by the Json configured in [ApiClient], so only the fields the UI
 * uses are declared here. All fields carry defaults so partial payloads decode.
 */

@Serializable
data class DashboardDto(
    @SerialName("active_generators") val activeGenerators: Int = 0,
    @SerialName("generators_under_contract") val generatorsUnderContract: Int = 0,
    @SerialName("upcoming_preventive_maintenance") val upcomingPm: Int = 0,
    @SerialName("emergency_jobs") val emergencyJobs: Int = 0,
    @SerialName("open_work_orders") val openWorkOrders: Int = 0,
    @SerialName("mttr_hours") val mttrHours: Double? = null,
    @SerialName("first_time_fix_rate") val firstTimeFixRate: Double? = null,
    @SerialName("technician_utilization") val technicianUtilization: Double? = null,
    @SerialName("total_invoiced") val totalInvoiced: Double = 0.0,
    @SerialName("open_purchase_requests") val openPurchaseRequests: Int = 0,
)

@Serializable
data class WorkOrderDto(
    val id: String = "",
    @SerialName("generator_id") val generatorId: String = "",
    val type: String = "",
    val status: String = "",
    val priority: String = "",
    @SerialName("assigned_technician_id") val assignedTechnicianId: String? = null,
)

@Serializable
data class GeoLocationDto(
    val lat: Double = 0.0,
    val lng: Double = 0.0,
    val label: String = "",
)

@Serializable
data class GeneratorDto(
    val id: String = "",
    @SerialName("serial_number") val serialNumber: String = "",
    val model: String = "",
    @SerialName("running_hours") val runningHours: Double = 0.0,
    val location: GeoLocationDto = GeoLocationDto(),
)
