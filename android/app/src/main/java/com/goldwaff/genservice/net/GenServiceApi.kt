package com.goldwaff.genservice.net

import retrofit2.http.GET

/** Retrofit interface for the generator-service orchestration backend. */
interface GenServiceApi {

    @GET("reporting/dashboard")
    suspend fun dashboard(): DashboardDto

    @GET("work-orders")
    suspend fun workOrders(): List<WorkOrderDto>

    @GET("generators")
    suspend fun generators(): List<GeneratorDto>

    @GET("maintenance/due")
    suspend fun generatorsDue(): List<GeneratorDto>
}
