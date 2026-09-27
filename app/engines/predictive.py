"""Predictive maintenance engine.

Turns IoT sensor telemetry into maintenance recommendations using threshold
rules on oil pressure, coolant temperature, battery voltage, fuel level, and the
running-hours service interval.
"""

from __future__ import annotations

from typing import List

from ..models import (
    Generator,
    MaintenanceRecommendation,
    Priority,
    SensorReading,
    WorkOrderType,
)

# Threshold constants (typical diesel genset operating envelopes).
MIN_OIL_PRESSURE_BAR = 1.5
MAX_COOLANT_TEMP_C = 98.0
MIN_BATTERY_VOLTAGE = 12.2
LOW_FUEL_PCT = 15.0


class PredictiveMaintenance:
    def analyze(
        self, generator: Generator, reading: SensorReading
    ) -> List[MaintenanceRecommendation]:
        """Return recommendations triggered by a single sensor reading."""
        recs: List[MaintenanceRecommendation] = []

        if (
            reading.oil_pressure is not None
            and reading.oil_pressure < MIN_OIL_PRESSURE_BAR
        ):
            recs.append(
                MaintenanceRecommendation(
                    generator_id=generator.id,
                    severity=Priority.HIGH,
                    reason=(
                        f"Oil pressure {reading.oil_pressure} bar is below the "
                        f"{MIN_OIL_PRESSURE_BAR} bar minimum"
                    ),
                    recommended_action=WorkOrderType.OIL_CHANGE,
                )
            )

        if (
            reading.coolant_temp is not None
            and reading.coolant_temp > MAX_COOLANT_TEMP_C
        ):
            recs.append(
                MaintenanceRecommendation(
                    generator_id=generator.id,
                    severity=Priority.EMERGENCY,
                    reason=(
                        f"Coolant temperature {reading.coolant_temp} C exceeds the "
                        f"{MAX_COOLANT_TEMP_C} C limit"
                    ),
                    recommended_action=WorkOrderType.INSPECTION,
                )
            )

        if (
            reading.battery_voltage is not None
            and reading.battery_voltage < MIN_BATTERY_VOLTAGE
        ):
            recs.append(
                MaintenanceRecommendation(
                    generator_id=generator.id,
                    severity=Priority.NORMAL,
                    reason=(
                        f"Battery voltage {reading.battery_voltage} V is below the "
                        f"{MIN_BATTERY_VOLTAGE} V threshold"
                    ),
                    recommended_action=WorkOrderType.INSPECTION,
                )
            )

        if reading.fuel_level is not None and reading.fuel_level < LOW_FUEL_PCT:
            recs.append(
                MaintenanceRecommendation(
                    generator_id=generator.id,
                    severity=Priority.NORMAL,
                    reason=f"Fuel level {reading.fuel_level}% is low",
                    recommended_action=WorkOrderType.INSPECTION,
                )
            )

        # Running-hours interval crossed since the last preventive maintenance.
        hours = reading.running_hours if reading.running_hours is not None else (
            generator.running_hours
        )
        if hours - generator.last_pm_hours >= generator.pm_interval_hours:
            recs.append(
                MaintenanceRecommendation(
                    generator_id=generator.id,
                    severity=Priority.NORMAL,
                    reason=(
                        f"{hours - generator.last_pm_hours:.0f} running hours since "
                        f"last PM (interval {generator.pm_interval_hours:.0f}h)"
                    ),
                    recommended_action=WorkOrderType.PREVENTIVE,
                )
            )

        return recs
