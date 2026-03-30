"""Tests for Dreame Mower integration setup."""

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.const import CONF_NAME, CONF_PASSWORD, CONF_USERNAME
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.dreame_mower import async_setup_entry
from custom_components.dreame_mower.config_flow import (
    CONF_ACCOUNT_TYPE,
    CONF_COUNTRY,
    CONF_DID,
    CONF_MAC,
    CONF_MODEL,
    CONF_SERIAL,
)
from custom_components.dreame_mower.const import DATA_COORDINATOR, DOMAIN


def _make_entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        title="Test Mower",
        data={
            CONF_NAME: "Test Mower",
            CONF_MAC: "11:22:33:44:55:66",
            CONF_MODEL: "dreame.mower.test789",
            CONF_SERIAL: "MIN123456",
            CONF_DID: "test_device_456",
            CONF_USERNAME: "test_user",
            CONF_PASSWORD: "test_password",
            CONF_ACCOUNT_TYPE: "dreame",
            CONF_COUNTRY: "eu",
        },
        entry_id="test_init_entry",
    )


async def test_async_setup_entry_fetches_vector_map_for_mowers(hass):
    """Mower setup should preload vector map data before entity setup."""
    entry = _make_entry()
    entry.add_to_hass(hass)

    coordinator = MagicMock()
    coordinator.device_type = "mower"
    coordinator.device = MagicMock()
    coordinator.device.fetch_vector_map = MagicMock(return_value=True)
    coordinator.async_connect_device = AsyncMock(return_value=True)
    coordinator.async_config_entry_first_refresh = AsyncMock(return_value=None)
    coordinator.async_request_refresh = AsyncMock(return_value=None)

    with patch("custom_components.dreame_mower.DreameMowerCoordinator", return_value=coordinator), patch.object(
        hass.config_entries,
        "async_forward_entry_setups",
        AsyncMock(return_value=None),
    ) as forward_entry_setups:
        assert await async_setup_entry(hass, entry) is True

    coordinator.async_connect_device.assert_awaited_once()
    coordinator.device.fetch_vector_map.assert_called_once_with()
    coordinator.async_config_entry_first_refresh.assert_awaited_once()
    coordinator.async_request_refresh.assert_awaited_once()
    forward_entry_setups.assert_awaited_once()
    assert hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR] is coordinator