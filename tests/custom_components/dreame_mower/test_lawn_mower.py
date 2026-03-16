"""Tests for DreameMowerLawnMower entity."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.components.lawn_mower import LawnMowerActivity
from homeassistant.helpers.service import _validate_entity_service_schema

from custom_components.dreame_mower.lawn_mower import (
    DreameMowerLawnMower,
    SERVICE_START_MOWING_ZONES,
    SERVICE_START_MOWING_ZONES_SCHEMA,
)
from custom_components.dreame_mower.dreame.const import STATUS_PROPERTY, DeviceStatus


def _make_coordinator(connected=True, status_code=0):
    coordinator = MagicMock()
    coordinator.device_mac = "AA:BB:CC:DD:EE:FF"
    coordinator.device_name = "Test Mower"
    coordinator.device_model = "dreame.mower.test"
    coordinator.device_serial = "SN123"
    coordinator.device_manufacturer = "Dreametech™"
    coordinator.device_firmware = "1.0.0"
    coordinator.device_connected = connected
    coordinator.device_status_code = status_code
    coordinator.device = MagicMock()
    coordinator.device.register_property_callback = MagicMock()
    coordinator.device.start_mowing = AsyncMock(return_value=True)
    coordinator.device.pause = AsyncMock(return_value=True)
    coordinator.device.return_to_dock = AsyncMock(return_value=True)
    coordinator.selected_zone_id = None
    coordinator.async_start_mowing_zones = AsyncMock(return_value=True)
    return coordinator


def _make_entity(coordinator=None):
    """Bypass DreameMowerLawnMower.__init__ to avoid device registration side-effects."""
    if coordinator is None:
        coordinator = _make_coordinator()
    entity = DreameMowerLawnMower.__new__(DreameMowerLawnMower)
    entity.coordinator = coordinator
    entity._entity_description_key = "lawn_mower"
    entity._attr_has_entity_name = True
    entity._attr_activity = LawnMowerActivity.DOCKED
    entity.hass = MagicMock()
    return entity


def test_activity_returns_none_when_unavailable():
    entity = _make_entity(_make_coordinator(connected=False))
    assert entity.activity is None


def test_activity_returns_current_when_available():
    entity = _make_entity(_make_coordinator(connected=True))
    entity._attr_activity = LawnMowerActivity.MOWING
    assert entity.activity == LawnMowerActivity.MOWING


def test_on_property_change_ignores_non_status_property():
    entity = _make_entity()
    entity.schedule_update_ha_state = MagicMock()
    entity._attr_activity = LawnMowerActivity.DOCKED

    entity._on_property_change("some_other_property", 1)

    assert entity._attr_activity == LawnMowerActivity.DOCKED
    entity.schedule_update_ha_state.assert_not_called()


def test_on_property_change_updates_activity_to_mowing():
    entity = _make_entity()
    entity.schedule_update_ha_state = MagicMock()

    entity._on_property_change(STATUS_PROPERTY.name, DeviceStatus.MOWING)

    assert entity._attr_activity == LawnMowerActivity.MOWING
    entity.schedule_update_ha_state.assert_called_once_with()


def test_on_property_change_does_not_schedule_update_when_activity_unchanged():
    entity = _make_entity()
    entity._attr_activity = LawnMowerActivity.DOCKED
    entity.schedule_update_ha_state = MagicMock()

    # CHARGING also maps to DOCKED, so activity won't change
    entity._on_property_change(STATUS_PROPERTY.name, DeviceStatus.CHARGING)

    entity.schedule_update_ha_state.assert_not_called()


@pytest.mark.asyncio
async def test_async_start_mowing_calls_device():
    entity = _make_entity()
    await entity.async_start_mowing()
    entity.coordinator.device.start_mowing.assert_called_once()


@pytest.mark.asyncio
async def test_async_pause_calls_device():
    entity = _make_entity()
    await entity.async_pause()
    entity.coordinator.device.pause.assert_called_once()


@pytest.mark.asyncio
async def test_async_dock_calls_device():
    entity = _make_entity()
    await entity.async_dock()
    entity.coordinator.device.return_to_dock.assert_called_once()


def test_start_mowing_zones_schema_is_valid_entity_service_schema():
    """Ensure SERVICE_START_MOWING_ZONES_SCHEMA passes HA's entity-service schema validation.

    HA rejects plain vol.Schema objects for entity services; the schema must be
    created via cv.make_entity_service_schema so it includes entity-targeting keys.
    """
    # Must not raise HomeAssistantError
    _validate_entity_service_schema(
        SERVICE_START_MOWING_ZONES_SCHEMA, f"dreame_mower.{SERVICE_START_MOWING_ZONES}"
    )
