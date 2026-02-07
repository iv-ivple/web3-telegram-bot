"""
Unit tests for bot functionality.
"""
import sys
import os
# Add parent directory to path so we can import utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from utils.validators import Validators
from utils.web3_helper import Web3Helper

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

# Run with: pytest tests/
