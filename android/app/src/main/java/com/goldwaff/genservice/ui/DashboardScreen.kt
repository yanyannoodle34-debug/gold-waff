package com.goldwaff.genservice.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.goldwaff.genservice.net.DashboardDto

private data class Kpi(val label: String, val value: String)

@Composable
fun DashboardScreen(state: UiState<DashboardDto>, onRetry: () -> Unit) {
    StateContent(state, onRetry) { d ->
        val kpis = listOf(
            Kpi("Active generators", d.activeGenerators.toString()),
            Kpi("Under contract", d.generatorsUnderContract.toString()),
            Kpi("Upcoming PM", d.upcomingPm.toString()),
            Kpi("Emergency jobs", d.emergencyJobs.toString()),
            Kpi("Open work orders", d.openWorkOrders.toString()),
            Kpi("Purchase requests", d.openPurchaseRequests.toString()),
            Kpi("MTTR (hrs)", d.mttrHours?.let { "%.1f".format(it) } ?: "—"),
            Kpi("First-time fix", d.firstTimeFixRate?.let { "%.0f%%".format(it * 100) } ?: "—"),
            Kpi("Tech utilization", d.technicianUtilization?.let { "%.0f%%".format(it * 100) } ?: "—"),
            Kpi("Total invoiced", "%.0f".format(d.totalInvoiced)),
        )
        LazyVerticalGrid(
            columns = GridCells.Fixed(2),
            modifier = Modifier.fillMaxWidth().padding(12.dp),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            items(kpis) { kpi -> KpiTile(kpi) }
        }
    }
}

@Composable
private fun KpiTile(kpi: Kpi) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                text = kpi.value,
                style = MaterialTheme.typography.headlineMedium,
                color = MaterialTheme.colorScheme.primary,
            )
            Box(modifier = Modifier.padding(top = 4.dp)) {
                Text(text = kpi.label, style = MaterialTheme.typography.bodyMedium)
            }
        }
    }
}
