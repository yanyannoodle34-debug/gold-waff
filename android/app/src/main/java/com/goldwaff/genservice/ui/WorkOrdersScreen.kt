package com.goldwaff.genservice.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.goldwaff.genservice.net.WorkOrderDto

@Composable
fun WorkOrdersScreen(state: UiState<List<WorkOrderDto>>, onRetry: () -> Unit) {
    StateContent(state, onRetry) { orders ->
        if (orders.isEmpty()) {
            EmptyMessage("No work orders yet.")
            return@StateContent
        }
        LazyColumn(
            modifier = Modifier.fillMaxSize().padding(12.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            items(orders) { wo -> WorkOrderCard(wo) }
        }
    }
}

@Composable
private fun WorkOrderCard(wo: WorkOrderDto) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                Text(text = wo.id, fontWeight = FontWeight.Bold)
                Text(text = wo.priority, color = MaterialTheme.colorScheme.primary)
            }
            Text(
                text = "${wo.type} • ${wo.status}",
                style = MaterialTheme.typography.bodyMedium,
                modifier = Modifier.padding(top = 4.dp),
            )
            Text(
                text = "Generator ${wo.generatorId}" +
                    (wo.assignedTechnicianId?.let { " • Tech $it" } ?: " • unassigned"),
                style = MaterialTheme.typography.bodySmall,
                modifier = Modifier.padding(top = 2.dp),
            )
        }
    }
}
