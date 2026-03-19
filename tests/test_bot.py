"""
Unit tests for bot functionality.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import MagicMock, patch
from utils.validators import Validators


class TestValidators:
    """Test input validation."""

    def test_valid_address(self):
        """Test valid Ethereum address."""
        address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
        is_valid, _ = Validators.validate_eth_address(address)
        assert is_valid

    def test_invalid_address_no_prefix(self):
        """Test address without 0x prefix."""
        address = "d8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
        is_valid, error = Validators.validate_eth_address(address)
        assert not is_valid
        assert "0x" in error

    def test_invalid_address_wrong_length(self):
        """Test address with wrong length."""
        address = "0x123"
        is_valid, error = Validators.validate_eth_address(address)
        assert not is_valid
        assert "42 characters" in error

    def test_format_eth_amount(self):
        """Test ETH amount formatting."""
        result = Validators.format_eth_amount(1.23456789)
        assert result == "1.2346"


class TestWeb3Helper:
    """Test Web3Helper with mocked Ethereum connection."""

    @patch('utils.web3_helper.Web3')
    def test_get_eth_balance(self, mock_web3_class):
        """Test ETH balance retrieval with mocked node."""
        # Set up mock
        mock_w3 = MagicMock()
        mock_w3.is_connected.return_value = True
        mock_w3.to_checksum_address.return_value = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
        mock_w3.eth.get_balance.return_value = 1_000_000_000_000_000_000  # 1 ETH in Wei
        mock_w3.from_wei.return_value = 1.0
        mock_web3_class.return_value = mock_w3

        from utils.web3_helper import Web3Helper
        helper = Web3Helper()
        balance = helper.get_eth_balance("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045")
        assert balance == 1.0

    @patch('utils.web3_helper.Web3')
    def test_is_valid_address(self, mock_web3_class):
        """Test address validation via Web3Helper."""
        mock_w3 = MagicMock()
        mock_w3.is_connected.return_value = True
        mock_w3.is_address.return_value = True
        mock_web3_class.return_value = mock_w3

        from utils.web3_helper import Web3Helper
        helper = Web3Helper()
        assert helper.is_valid_address("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045") is True

    @patch('utils.web3_helper.Web3')
    def test_connection_failure(self, mock_web3_class):
        """Test that ConnectionError is raised when node is unreachable."""
        mock_w3 = MagicMock()
        mock_w3.is_connected.return_value = False
        mock_web3_class.return_value = mock_w3

        from utils.web3_helper import Web3Helper
        with pytest.raises(ConnectionError):
            Web3Helper()
