"""Tests for miscellaneous property handlers (property_misc module)."""

import pytest
from unittest.mock import patch

from custom_components.dreame_mower.dreame.property.property_misc import Property11Handler


class TestProperty11Handler:
    """Test cases for Property11Handler."""

    def test_init(self):
        """Test handler initialization."""
        handler = Property11Handler()
        
        # Should initialize with None last_value
        assert handler.last_value is None

    def test_parse_value_valid_data(self):
        """Test parsing valid property 1:1 data."""
        handler = Property11Handler()
        
        # Create test data with sentinels (206) and sample payload (18 bytes between sentinels)
        test_data = [
            206,  # Start sentinel (index 0)
            0,    # payload[0]
            0,    # payload[1]
            0,    # payload[2]
            0,    # payload[3]
            0,    # payload[4]
            0,    # payload[5]
            4,    # payload[6]
            0,    # payload[7]
            0,    # payload[8]
            0,    # payload[9]
            85,   # payload[10]
            33,   # payload[11]
            35,   # payload[12]
            133,  # payload[13]
            54,   # payload[14]
            0,    # payload[15]
            235,  # payload[16]
            68,   # payload[17]
            206   # End sentinel (index 19)
        ]
        
        result = handler.parse_value(test_data)
        
        # Should return True for successful parsing
        assert result is True
        
        # Check that last_value is stored
        assert handler.last_value == test_data

    def test_parse_value_unknown_length(self):
        """Test parsing with non-standard data lengths."""
        handler = Property11Handler()
        
        # 24-byte variant (mova.mower.g2405c firmware 4.3.6_0062, issue #18) - silently acknowledged
        result = handler.parse_value([1] + [0] * 22 + [0])
        assert result is True
        
        # Unknown sizes return False to surface new firmware variants
        result = handler.parse_value([206, 1, 2, 3])  # 4 bytes
        assert result is False
        
        result = handler.parse_value([206] * 25)  # 25 bytes
        assert result is False

    def test_parse_value_invalid_type(self):
        """Test parsing with invalid data type."""
        handler = Property11Handler()
        
        # Test with non-list input
        result = handler.parse_value("invalid")
        assert result is False

    def test_parse_value_unknown_sentinels(self):
        """Test parsing 20-byte arrays with non-standard sentinel values are silently accepted."""
        handler = Property11Handler()

        # Non-CE sentinels on 20-byte array (e.g. dreame.swbot.g2509) - silently accepted
        test_data = [100] + [0] * 18 + [206]
        result = handler.parse_value(test_data)
        assert result is True

        test_data = [206] + [0] * 18 + [100]
        result = handler.parse_value(test_data)
        assert result is True

    @patch('custom_components.dreame_mower.dreame.property.property_misc._LOGGER')
    def test_logging_on_invalid_format(self, mock_logger):
        """Test that proper warnings are logged for invalid data format."""
        handler = Property11Handler()
        
        # Test with invalid type
        handler.parse_value("not a list")
        mock_logger.warning.assert_called()

    def test_multiple_parse_calls_update_values(self):
        """Test that multiple parse calls properly update values."""
        handler = Property11Handler()
        
        # First parse
        test_data_1 = [206] + [1] * 18 + [206]
        result = handler.parse_value(test_data_1)
        assert result is True
        assert handler.last_value == test_data_1
        
        # Second parse with different data
        test_data_2 = [206] + [2] * 18 + [206]
        result = handler.parse_value(test_data_2)
        assert result is True
        assert handler.last_value == test_data_2
