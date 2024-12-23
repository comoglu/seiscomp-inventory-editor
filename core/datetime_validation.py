# core/datetime_validation.py
import re
from datetime import datetime
from typing import Tuple, Optional

class DateTimeValidator:
    """Validator for SeisComP datetime formats"""
    
    # SeisComP datetime format: YYYY-MM-DDThh:mm:ss.ssssZ
    SEISCOMP_PATTERN = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{4}Z$'
    
    # Alternative formats that should be converted to SeisComP format
    ALTERNATIVE_PATTERNS = [
        r'^\d{4}-\d{2}-\d{2}$',                          # YYYY-MM-DD
        r'^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}$',      # YYYY-MM-DD HH:MM:SS
        r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$',       # YYYY-MM-DDThh:mm:ss
        r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$',      # YYYY-MM-DDThh:mm:ssZ
        r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+$',  # YYYY-MM-DDThh:mm:ss.sss
    ]

    @classmethod
    def validate(cls, text: str) -> bool:
        """
        Validate datetime string format
        
        Args:
            text: Datetime string to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not text:  # Empty is valid
            return True
            
        # Check if already in SeisComP format
        if re.match(cls.SEISCOMP_PATTERN, text):
            return cls._validate_components(text)
            
        # Check alternative formats
        for pattern in cls.ALTERNATIVE_PATTERNS:
            if re.match(pattern, text):
                return cls._validate_components(text)
                
        return False

    @classmethod
    def convert_to_seiscomp_format(cls, text: str) -> Optional[str]:
        """
        Convert datetime string to SeisComP format
        
        Args:
            text: Datetime string to convert
            
        Returns:
            str: Converted datetime string or None if invalid
        """
        if not text:
            return None
            
        # Already in SeisComP format
        if re.match(cls.SEISCOMP_PATTERN, text):
            return text if cls._validate_components(text) else None
            
        try:
            # Parse basic date components
            if 'T' in text:
                date_str, time_str = text.split('T')
            elif ' ' in text:
                date_str, time_str = text.split(' ')
            else:
                date_str, time_str = text, "00:00:00"
                
            # Remove timezone indicator if present
            time_str = time_str.rstrip('Z')
            
            # Parse date
            year, month, day = map(int, date_str.split('-'))
            
            # Parse time
            if ':' in time_str:
                time_parts = time_str.split(':')
                hour = int(time_parts[0])
                minute = int(time_parts[1])
                second = float(time_parts[2]) if len(time_parts) > 2 else 0
            else:
                hour, minute, second = 0, 0, 0
                
            # Validate components
            if not cls._validate_date(year, month, day):
                return None
            if not cls._validate_time(hour, minute, second):
                return None
                
            # Format with 4 decimal places for seconds
            second_int = int(second)
            second_frac = int((second - second_int) * 10000)
            
            return f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second_int:02d}.{second_frac:04d}Z"
            
        except (ValueError, IndexError):
            return None

    @staticmethod
    def _validate_date(year: int, month: int, day: int) -> bool:
        """Validate date components"""
        if not (1900 <= year <= 2100):
            return False
            
        if not (1 <= month <= 12):
            return False
            
        # Use datetime to validate day (handles leap years)
        try:
            datetime(year, month, day)
            return True
        except ValueError:
            return False

    @staticmethod
    def _validate_time(hour: int, minute: int, second: float) -> bool:
        """Validate time components"""
        return (0 <= hour <= 23 and 
                0 <= minute <= 59 and 
                0 <= second < 60)

    @classmethod
    def _validate_components(cls, text: str) -> bool:
        """Validate all datetime components"""
        try:
            # Remove timezone indicator
            text = text.rstrip('Z')
            
            # Split into date and time
            if 'T' in text:
                date_str, time_str = text.split('T')
            else:
                date_str, time_str = text.split(' ')
            
            # Validate date
            year, month, day = map(int, date_str.split('-'))
            if not cls._validate_date(year, month, day):
                return False
                
            # Validate time if present
            if time_str:
                time_parts = time_str.split(':')
                hour = int(time_parts[0])
                minute = int(time_parts[1])
                second = float(time_parts[2])
                if not cls._validate_time(hour, minute, second):
                    return False
                    
            return True
            
        except (ValueError, IndexError):
            return False