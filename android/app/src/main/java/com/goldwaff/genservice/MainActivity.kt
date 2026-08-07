package com.goldwaff.genservice

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Build
import androidx.compose.material.icons.filled.DateRange
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.goldwaff.genservice.ui.AppViewModel
import com.goldwaff.genservice.ui.DashboardScreen
import com.goldwaff.genservice.ui.GeneratorsScreen
import com.goldwaff.genservice.ui.LoginScreen
import com.goldwaff.genservice.ui.ServerUrlDialog
import com.goldwaff.genservice.ui.WorkOrdersScreen
import com.goldwaff.genservice.ui.theme.GoldWaffGenServiceTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            GoldWaffGenServiceTheme {
                AppRoot()
            }
        }
    }
}

private enum class Tab(val label: String) {
    DASHBOARD("Dashboard"),
    WORK_ORDERS("Work Orders"),
    GENERATORS("Generators"),
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun AppRoot(vm: AppViewModel = viewModel()) {
    var authenticated by remember { mutableStateOf(false) }
    if (!authenticated) {
        LoginScreen(onAuthenticated = { authenticated = true })
        return
    }

    var tab by remember { mutableStateOf(Tab.DASHBOARD) }
    var showSettings by remember { mutableStateOf(false) }

    val baseUrl by vm.baseUrl.collectAsStateWithLifecycle()
    val dashboard by vm.dashboard.collectAsStateWithLifecycle()
    val workOrders by vm.workOrders.collectAsStateWithLifecycle()
    val generators by vm.generators.collectAsStateWithLifecycle()

    if (showSettings) {
        ServerUrlDialog(
            current = baseUrl,
            onDismiss = { showSettings = false },
            onConfirm = {
                vm.setBaseUrl(it)
                showSettings = false
            },
        )
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Generator Service") },
                actions = {
                    IconButton(onClick = { vm.refreshAll() }) {
                        Icon(Icons.Filled.Refresh, contentDescription = "Refresh")
                    }
                    IconButton(onClick = { showSettings = true }) {
                        Icon(Icons.Filled.Settings, contentDescription = "Server URL")
                    }
                },
            )
        },
        bottomBar = {
            NavigationBar {
                NavigationBarItem(
                    selected = tab == Tab.DASHBOARD,
                    onClick = { tab = Tab.DASHBOARD },
                    icon = { Icon(Icons.Filled.DateRange, contentDescription = null) },
                    label = { Text(Tab.DASHBOARD.label) },
                )
                NavigationBarItem(
                    selected = tab == Tab.WORK_ORDERS,
                    onClick = { tab = Tab.WORK_ORDERS },
                    icon = { Icon(Icons.Filled.Build, contentDescription = null) },
                    label = { Text(Tab.WORK_ORDERS.label) },
                )
                NavigationBarItem(
                    selected = tab == Tab.GENERATORS,
                    onClick = { tab = Tab.GENERATORS },
                    icon = { Icon(Icons.Filled.Settings, contentDescription = null) },
                    label = { Text(Tab.GENERATORS.label) },
                )
            }
        },
    ) { innerPadding ->
        androidx.compose.foundation.layout.Box(
            modifier = Modifier.fillMaxSize().padding(innerPadding),
        ) {
            when (tab) {
                Tab.DASHBOARD -> DashboardScreen(dashboard, vm::loadDashboard)
                Tab.WORK_ORDERS -> WorkOrdersScreen(workOrders, vm::loadWorkOrders)
                Tab.GENERATORS -> GeneratorsScreen(generators, vm::loadGenerators)
            }
        }
    }
}
