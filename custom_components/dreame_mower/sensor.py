"""Minimal sensor platform for Dreame Mower Implementation."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfArea, UnitOfTime

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import DreameMowerCoordinator
from .dreame.const import DeviceStatus
from .entity import DreameMowerEntity
from .config_flow import DEVICE_TYPE_SWBOT

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Dreame Mower sensors from config entry."""
    coordinator: DreameMowerCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    
    if coordinator.device_type == DEVICE_TYPE_SWBOT:
        sensors = [
            DreameMowerBatterySensor(coordinator),
            DreameMowerStatusSensor(coordinator),
            DreameMowerWiFiSignalSensor(coordinator),
        ]
    else:
        # Full mower sensor set
        sensors = [
            DreameMowerBatterySensor(coordinator),
            DreameMowerStatusSensor(coordinator),
            DreameMowerChargingStatusSensor(coordinator),
            DreameMowerBluetoothSensor(coordinator),
            DreameMowerDeviceCodeSensor(coordinator),
            DreameMowerTaskSensor(coordinator),
            DreameMowerProgressSensor(coordinator),
            DreameMowerCurrentAreaSensor(coordinator),
            DreameMowerTotalAreaSensor(coordinator),
            DreameMowerElapsedTimeSensor(coordinator),
            DreameMowerFirmwareUpdateSensor(coordinator),
            DreameMowerBladeUsageSensor(coordinator),
            DreameMowerWiFiSignalSensor(coordinator),
        ]
    
    async_add_entities(sensors)


class DreameMowerBatterySensor(DreameMowerEntity, SensorEntity):
    """Battery level sensor for Dreame Mower."""

    def __init__(self, coordinator: DreameMowerCoordinator) -> None:
        """Initialize the battery sensor."""
        super().__init__(coordinator, "battery")
        self._attr_device_class = SensorDeviceClass.BATTERY
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_icon = "mdi:battery"

    @property
    def native_value(self) -> int | None:
        """Return the battery level."""
        return self.coordinator.device_battery_percent


class DreameMowerStatusSensor(DreameMowerEntity, SensorEntity):
    """Status sensor for Dreame Mower."""

    def __init__(self, coordinator: DreameMowerCoordinator) -> None:
        """Initialize the status sensor."""
        super().__init__(coordinator, "status")
        self._attr_icon = "mdi:robot-mower"
        self._attr_translation_key = "status"

    @property
    def native_value(self) -> str | None:
        """Return the mower status."""
        if not self.available:
            return "offline"
        return self.coordinator.device_status


class DreameMowerChargingStatusSensor(DreameMowerEntity, SensorEntity):
    """Charging status sensor for Dreame Mower (3:2)."""

    def __init__(self, coordinator: DreameMowerCoordinator) -> None:
        """Initialize the charging status sensor."""
        super().__init__(coordinator, "charging_status")
        self._attr_icon = "mdi:lightning-bolt"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_translation_key = "charging_status"

    @property
    def native_value(self) -> str | None:
        """Return the charging status mapped text."""
        return self.coordinator.device_charging_status


class DreameMowerBluetoothSensor(DreameMowerEntity, SensorEntity):
    """Bluetooth connection sensor for Dreame Mower."""

    def __init__(self, coordinator: DreameMowerCoordinator) -> None:
        """Initialize the Bluetooth sensor."""
        super().__init__(coordinator, "bluetooth_connection")
        self._attr_icon = "mdi:bluetooth"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_translation_key = "bluetooth_connection"

    @property
    def native_value(self) -> bool | None:
        """Return the Bluetooth connection status."""
        return self.coordinator.device_bluetooth_connected

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        return {
            "bluetooth_connected": self.coordinator.device_bluetooth_connected,
        }


class DreameMowerDeviceCodeSensor(DreameMowerEntity, SensorEntity):
    """Device code sensor (2:2) - shows current device status/error codes."""

    def __init__(self, coordinator: DreameMowerCoordinator) -> None:
        """Initialize the device code sensor."""
        super().__init__(coordinator, "device_code")
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_translation_key = "device_code"

    @property
    def native_value(self) -> int | None:
        """Return the current device code."""
        return self.coordinator.device_code

    @property
    def icon(self) -> str:
        """Return icon based on device code type."""
        if self.coordinator.device_code_is_error:
            return "mdi:alert-circle"
        elif self.coordinator.device_code_is_warning:
            return "mdi:alert"
        else:
            return "mdi:information-outline"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attributes: dict[str, Any] = {}
        
        # Add device code details
        if self.coordinator.device_code is not None:
            attributes["code"] = self.coordinator.device_code
            attributes["name"] = self.coordinator.device_code_name
            attributes["description"] = self.coordinator.device_code_description
            
            # Determine type based on priority: error > warning > info
            if self.coordinator.device_code_is_error:
                attributes["type"] = "error"
            elif self.coordinator.device_code_is_warning:
                attributes["type"] = "warning"
            else:
                attributes["type"] = "info"
        
        return attributes


class DreameMowerTaskSensor(DreameMowerEntity, SensorEntity):
    """Current task sensor for Dreame Mower."""

    def __init__(self, coordinator: DreameMowerCoordinator) -> None:
        """Initialize the task sensor."""
        super().__init__(coordinator, "current_task")
        self._attr_icon = "mdi:clipboard-play"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_translation_key = "current_task"

    @property
    def native_value(self) -> str | None:
        """Return the current task status.

        State machine:
          - None:        No task data has ever been received
          - Inactive:    No task is active (task_active=False or task was reset)
          - Active:      Task is running AND mower is actively mowing
          - Recharging:  Task is running BUT mower is returning to/at the dock
          - Paused:      Task is accepted but execution is paused
          - Error:       Task is active but mower is paused due to errors
          - Mapping:     Task is active but mower is in mapping mode
        """
        task_data = self.coordinator.current_task_data
        if not task_data:
            return None

        execution_active = task_data.get("execution_active", False)
        task_active = task_data.get("task_active", False)

        if not task_active:
            return "Inactive"

        if not execution_active:
            return "Paused"

        # Task is active and execution is active — cross-reference with device status
        status = self.coordinator.device_status_code
        if status in (DeviceStatus.RETURNING_TO_CHARGE, DeviceStatus.CHARGING, DeviceStatus.CHARGING_COMPLETE):
            return "Recharging"
        if status == DeviceStatus.PAUSED_DUE_TO_ERRORS:
            return "Error"
        if status == DeviceStatus.MAPPING:
            return "Mapping"
        if status in (DeviceStatus.PAUSED, DeviceStatus.STANDBY):
            # Device says paused/standby but task still thinks execution is active.
            # This is a transient race — report as Paused until the task descriptor
            # catches up (the next 2:50 update will set execution_active=False).
            return "Paused"
        return "Active"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes with detailed task information."""
        attributes: dict[str, Any] = {}

        task_data = self.coordinator.current_task_data
        if task_data:
            attributes.update({
                "task_type": task_data.get("type"),
                "execution_active": task_data.get("execution_active"),
                "task_active": task_data.get("task_active"),
                "coverage_target": task_data.get("coverage_target"),
                "area_id": task_data.get("area_id"),
                "region_id": task_data.get("region_id"),
                "elapsed_time": task_data.get("elapsed_time"),
            })

        # Always expose the device status so users can correlate task state
        attributes["device_status"] = self.coordinator.device_status
        
        return attributes


class DreameMowerProgressSensor(DreameMowerEntity, SensorEntity):
    """Mowing progress sensor for Dreame Mower."""

    def __init__(self, coordinator: DreameMowerCoordinator) -> None:
        """Initialize the progress sensor."""
        super().__init__(coordinator, "mowing_progress")
        self._attr_device_class = SensorDeviceClass.POWER_FACTOR
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_icon = "mdi:percent"
        self._attr_translation_key = "mowing_progress"

    @property
    def native_value(self) -> float | None:
        """Return the mowing progress percentage."""
        progress = self.coordinator.mowing_progress_percent
        if progress is not None:
            return round(progress, 1)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        progress = self.coordinator.mowing_progress_percent
        attributes: dict[str, Any] = {
            "current_area_sqm": self.coordinator.current_area_sqm,
            "total_area_sqm": self.coordinator.total_area_sqm,
            "progress_percent": round(progress, 1) if progress is not None else None,
        }
        
        # Add mower coordinates data
        coordinates = self.coordinator.mower_coordinates
        if coordinates:
            attributes["coordinates"] = f"{coordinates[0]}, {coordinates[1]}"
            attributes["x"] = coordinates[0]
            attributes["y"] = coordinates[1]
        else:
            attributes["coordinates"] = None
            attributes["x"] = None
            attributes["y"] = None
            
        attributes["segment"] = self.coordinator.current_segment
        attributes["heading"] = self.coordinator.mower_heading

        # Add path history summary
        path_history = self.coordinator.mowing_path_history
        attributes["path_points"] = len(path_history)

        return attributes


class DreameMowerCurrentAreaSensor(DreameMowerEntity, SensorEntity):
    """Current mowed area sensor for Dreame Mower."""

    def __init__(self, coordinator: DreameMowerCoordinator) -> None:
        """Initialize the current area sensor."""
        super().__init__(coordinator, "current_area")
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfArea.SQUARE_METERS
        self._attr_icon = "mdi:grass"
        self._attr_translation_key = "current_area"

    @property
    def native_value(self) -> float | None:
        """Return the current mowed area in square meters."""
        area = self.coordinator.current_area_sqm
        if area is not None:
            return round(area, 1)
        return None


class DreameMowerTotalAreaSensor(DreameMowerEntity, SensorEntity):
    """Total planned mowing area sensor for Dreame Mower."""

    def __init__(self, coordinator: DreameMowerCoordinator) -> None:
        """Initialize the total area sensor."""
        super().__init__(coordinator, "total_area")
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfArea.SQUARE_METERS
        self._attr_icon = "mdi:texture-box"
        self._attr_translation_key = "total_area"

    @property
    def native_value(self) -> float | None:
        """Return the total planned mowing area in square meters."""
        area = self.coordinator.total_area_sqm
        if area is not None:
            return round(area, 1)
        return None


class DreameMowerElapsedTimeSensor(DreameMowerEntity, SensorEntity):
    """Elapsed mowing time sensor for current task."""

    def __init__(self, coordinator: DreameMowerCoordinator) -> None:
        """Initialize the elapsed time sensor."""
        super().__init__(coordinator, "elapsed_time")
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "min"
        self._attr_icon = "mdi:timer"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_translation_key = "elapsed_time"

    @property
    def native_value(self) -> float | None:
        """Return the elapsed mowing time in minutes."""
        task_data = self.coordinator.current_task_data
        if task_data and task_data.get("elapsed_time") is not None:
            # elapsed_time is in seconds, convert to minutes
            return round(task_data["elapsed_time"] / 60, 1)
        return None


class DreameMowerFirmwareUpdateSensor(DreameMowerEntity, SensorEntity):
    """Firmware/OTA update status sensor for Dreame Mower."""

    def __init__(self, coordinator: DreameMowerCoordinator) -> None:
        """Initialize the firmware update sensor."""
        super().__init__(coordinator, "firmware_update")
        self._attr_icon = "mdi:update"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_translation_key = "firmware_update"

    @property
    def native_value(self) -> str | None:
        """Return firmware update status text.

        Priority: firmware_install_state (MiOT property) > ota_state (MQTT props) > up_to_date.
        """
        from .dreame.const import FIRMWARE_INSTALL_STATE_MAPPING

        state = self.coordinator.device_firmware_install_state
        if state is not None and state in FIRMWARE_INSTALL_STATE_MAPPING:
            return FIRMWARE_INSTALL_STATE_MAPPING[state]

        ota = self.coordinator.device_ota_state
        if ota:
            return ota

        return "up_to_date"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes with firmware update details."""
        attributes: dict[str, Any] = {}

        attributes["firmware_install_state"] = self.coordinator.device_firmware_install_state

        # Combine both progress sources: MiOT download progress takes priority
        progress = self.coordinator.device_firmware_download_progress
        if progress is None:
            progress = self.coordinator.device_ota_progress
        attributes["download_progress"] = progress

        attributes["ota_state"] = self.coordinator.device_ota_state
        attributes["current_firmware"] = self.coordinator.device_firmware

        return attributes


# Recommended blade life for Dreame mowers (in hours)
# Based on manufacturer recommendation: ~200 hours for standard blades
RECOMMENDED_BLADE_LIFE_HOURS = 200


class DreameMowerBladeUsageSensor(DreameMowerEntity, SensorEntity):
    """Blade usage/life tracking sensor for Dreame Mower.

    Tracks cumulative mowing time since last blade reset by accumulating
    duration data from mission completion events (4:1).

    The primary value is total blade hours. Extra attributes provide
    detailed breakdowns including area mowed, mission count, and
    estimated remaining blade life percentage.

    Note: Counters reset on HA restart. Persistence via .storage will be
    added once the actual blade-life MQTT property (likely in Service 5)
    is identified and mapped.
    """

    def __init__(self, coordinator: DreameMowerCoordinator) -> None:
        """Initialize the blade usage sensor."""
        super().__init__(coordinator, "blade_usage")
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_native_unit_of_measurement = UnitOfTime.HOURS
        self._attr_icon = "mdi:fan"
        self._attr_translation_key = "blade_usage"

    @property
    def native_value(self) -> float:
        """Return total blade mowing hours."""
        return self.coordinator.blade_total_mowing_hours

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return detailed blade usage attributes."""
        total_hours = self.coordinator.blade_total_mowing_hours
        total_minutes = self.coordinator.blade_total_mowing_minutes
        total_area = self.coordinator.blade_total_mowed_area_sqm
        missions = self.coordinator.blade_completed_missions

        # Estimated remaining life based on recommended 200-hour blade life
        remaining_pct = max(
            0.0,
            round(100.0 - (total_hours / RECOMMENDED_BLADE_LIFE_HOURS * 100.0), 1),
        )

        return {
            "total_mowing_minutes": total_minutes,
            "total_mowing_hours": total_hours,
            "total_mowed_area_sqm": round(total_area, 1),
            "completed_missions": missions,
            "blade_reset_timestamp": self.coordinator.blade_reset_timestamp,
            "recommended_life_hours": RECOMMENDED_BLADE_LIFE_HOURS,
            "estimated_life_remaining_percent": remaining_pct,
        }


class DreameMowerWiFiSignalSensor(DreameMowerEntity, SensorEntity):
    """WiFi signal strength sensor for Dreame Mower."""

    def __init__(self, coordinator: DreameMowerCoordinator) -> None:
        """Initialize the WiFi signal sensor."""
        super().__init__(coordinator, "wifi_signal")
        self._attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "dBm"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_icon = "mdi:wifi"
        self._attr_translation_key = "wifi_signal"

    @property
    def native_value(self) -> int | None:
        """Return the WiFi signal strength in dBm."""
        return self.coordinator.device_wifi_rssi
