"""Miscellaneous property handlers for known but not actively used properties.

This module provides simple logging handlers for properties that are known
but not currently useful for the integration. These handlers log the data
for observability without extracting specific values.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable
from ..const import PROPERTY_1_1, SETTINGS_CHANGE_PROPERTY

_LOGGER = logging.getLogger(__name__)


class Property11Handler:
    """Handler for property 1:1 - complex status/telemetry data.
    
    This property contains 20-byte array with various telemetry including:
    - Raw battery charging state (byte 10: 0-100 direct %, ≥128 means charging with value-128)
    
    Currently only logged for observability, not actively used in integration.
    """
    
    def __init__(self) -> None:
        """Initialize property handler."""
        self._last_value: list[int] | None = None
    
    def parse_value(self, value: list[int]) -> bool:
        """Parse and log property 1:1 value."""
        try:
            if not isinstance(value, list):
                _LOGGER.warning("Property 1:1 unexpected type: %s, value: %s", type(value), value)
                return False

            self._last_value = value.copy()

            # Known format: 20-byte array with sentinel 0xCE at positions 0 and 19
            if len(value) == 20 and value[0] == 206 and value[19] == 206:
                payload = value[1:19]  # p0..p17
                raw_battery = payload[10]  # Known: raw battery state with charging flag
                _LOGGER.debug(
                    "Property 1:1 received - raw_battery: %d, payload: %s",
                    raw_battery,
                    payload
                )
            elif len(value) == 24:
                # 24-byte variant seen on mova.mower.g2405c firmware 4.3.6_0062 (issue #18)
                _LOGGER.debug("Property 1:1 received (24-byte variant): %s", value)
            elif len(value) == 20:
                # 20-byte variant with non-CE sentinels seen on dreame.swbot.g2509 fw 4.3.6_0603
                _LOGGER.debug("Property 1:1 received (20-byte alt-sentinel variant): %s", value)
            else:
                _LOGGER.warning("Property 1:1 unrecognised format (len=%d): %s", len(value), value)
                return False

            return True

        except Exception as ex:
            _LOGGER.error("Failed to parse property 1:1: %s", ex)
            return False
    
    @property
    def last_value(self) -> list[int] | None:
        """Return last received property value."""
        return self._last_value.copy() if self._last_value else None


class SettingsChangeHandler:
    """Handler for generic settings change acknowledgment property (2:51).
    
    This property serves as a generic 'echo back' mechanism when any device setting
    is changed. It reports back information about the changed setting but is not
    tied to any specific feature.
    """
    
    def __init__(self) -> None:
        """Initialize settings change handler."""
        self._last_value: dict[str, Any] | None = None
    
    def parse_value(self, value: Any) -> bool:
        """Parse and log settings change acknowledgment."""
        try:
            if not isinstance(value, dict):
                _LOGGER.warning("Invalid settings change value type: %s, value: %s", type(value), value)
                return False
            
            self._last_value = value
            
            # Log the settings change as info with JSON content
            _LOGGER.info("Settings change acknowledged (2:51): %s", json.dumps(value))
            return True
                
        except Exception as ex:
            _LOGGER.error("Failed to parse settings change acknowledgment: %s, value: %s", ex, value)
            return False
    
    @property
    def last_value(self) -> dict[str, Any] | None:
        """Return last received settings change data."""
        return self._last_value.copy() if self._last_value else None


class MiscPropertyHandler:
    """Unified handler for all miscellaneous properties."""
    
    def __init__(self) -> None:
        """Initialize misc property handler."""
        self._property_1_1_handler = Property11Handler()
        self._settings_change_handler = SettingsChangeHandler()
    
    @staticmethod
    def matches(siid: int, piid: int) -> bool:
        """Check if a property is a miscellaneous property."""
        return PROPERTY_1_1.matches(siid, piid) or SETTINGS_CHANGE_PROPERTY.matches(siid, piid)
    
    def handle_property_update(self, siid: int, piid: int, value: Any, notify_callback: Callable[[str, Any], None]) -> bool:
        """Handle miscellaneous property updates."""
        try:
            if PROPERTY_1_1.matches(siid, piid):
                return self._property_1_1_handler.parse_value(value)
            elif SETTINGS_CHANGE_PROPERTY.matches(siid, piid):
                return self._settings_change_handler.parse_value(value)
            else:
                # Property not handled by this handler
                return False
                
        except Exception as ex:
            _LOGGER.error("Failed to handle misc property %d:%d:%s: %s", siid, piid, value, ex)
            return False
