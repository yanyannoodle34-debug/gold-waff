package com.goldwaff.genservice.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.AssistChip
import androidx.compose.material3.AssistChipDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp

@Composable
fun GeneratorsScreen(state: UiState<List<GeneratorRow>>, onRetry: () -> Unit) {
    StateContent(state, onRetry) { rows ->
        if (rows.isEmpty()) {
            EmptyMessage("No generators registered.")
            return@StateContent
        }
        LazyColumn(
            modifier = Modifier.fillMaxSize().padding(12.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            items(rows) { row -> GeneratorCard(row) }
        }
    }
}

@Composable
private fun GeneratorCard(row: GeneratorRow) {
    val g = row.generator
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                Text(text = g.serialNumber, fontWeight = FontWeight.Bold)
                if (row.isDue) {
                    AssistChip(
                        onClick = {},
                        enabled = false,
                        label = { Text("PM due") },
                        colors = AssistChipDefaults.assistChipColors(
                            disabledLabelColor = MaterialTheme.colorScheme.error,
                        ),
                    )
                }
            }
            Text(
                text = g.model,
                style = MaterialTheme.typography.bodyMedium,
                modifier = Modifier.padding(top = 4.dp),
            )
            Text(
                text = "${g.runningHours.toInt()} run hrs • ${g.location.label}",
                style = MaterialTheme.typography.bodySmall,
                modifier = Modifier.padding(top = 2.dp),
            )
        }
    }
}
