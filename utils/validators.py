"""
Input validation utilities.
Ensures user input is safe and correctly formatted.
"""
import re

class Validators:
    """Input validation methods."""
    
    @staticmethod
    def validate_eth_address(address: str) -> tuple[bool, str]:
        """
        Validate Ethereum address format.
        
        Returns:
            (is_valid, error_message)
        """
        if not address:
            return False, "Address cannot be empty"
        
        # Remove whitespace
        address = address.strip()
        
        # Check if starts with 0x
        if not address.startswith('0x'):
            return False, "Address must start with '0x'"
        
        # Check length (0x + 40 hex chars = 42 total)
        if len(address) != 42:
            return False, f"Address must be 42 characters (got {len(address)})"
        
        # Check if valid hex
        if not re.match(r'^0x[0-9a-fA-F]{40}$', address):
            return False, "Address contains invalid characters"
        
        return True, ""
    
    @staticmethod
    def format_eth_amount(amount: float, decimals: int = 4) -> str:
        """Format ETH amount for display."""
        return f"{amount:.{decimals}f}"
    
    @staticmethod
    def format_usd_amount(amount: float) -> str:
        """Format USD amount for display."""
        return f"${amount:,.2f}"
    
    @staticmethod
    def sanitize_input(text: str, max_length: int = 100) -> str:
        """
        Sanitize user input to prevent injection attacks.
        
        Args:
            text: User input text
            max_length: Maximum allowed length
            
        Returns:
            Sanitized text
        """
        # Remove control characters
        sanitized = ''.join(char for char in text if char.isprintable())
        
        # Trim whitespace
        sanitized = sanitized.strip()
        
        # Limit length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized
