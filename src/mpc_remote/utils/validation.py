"""Validation utilities for Model Context Protocol"""

from typing import Any, Dict, Optional, Union, Callable
import re
import json
import jsonschema
from enum import Enum, auto

class ValidationError(Exception):
    """Custom exception for validation failures"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize validation error
        
        :param message: Error message
        :param details: Additional error details
        """
        super().__init__(message)
        self.details = details or {}

class ValidationType(Enum):
    """Supported validation types"""
    JSON_SCHEMA = auto()
    REGEX = auto()
    CUSTOM = auto()
    TYPE = auto()

class Validator:
    """
    Comprehensive validation utility for complex data structures
    """
    @staticmethod
    def validate(
        data: Any, 
        validation_type: ValidationType, 
        validation_spec: Union[Dict[str, Any], str, Callable],
        allow_none: bool = False
    ) -> bool:
        """
        Validate data against specified validation type
        
        :param data: Data to validate
        :param validation_type: Type of validation
        :param validation_spec: Validation specification
        :param allow_none: Whether None is considered valid
        :return: Validation result
        :raises ValidationError: If validation fails
        """
        # Handle None case
        if data is None:
            if allow_none:
                return True
            raise ValidationError("Data cannot be None")
        
        try:
            if validation_type == ValidationType.JSON_SCHEMA:
                return Validator._validate_json_schema(data, validation_spec)
            
            elif validation_type == ValidationType.REGEX:
                return Validator._validate_regex(data, validation_spec)
            
            elif validation_type == ValidationType.CUSTOM:
                return Validator._validate_custom(data, validation_spec)
            
            elif validation_type == ValidationType.TYPE:
                return Validator._validate_type(data, validation_spec)
            
            else:
                raise ValueError(f"Unsupported validation type: {validation_type}")
        
        except Exception as e:
            raise ValidationError(
                f"Validation failed: {str(e)}",
                details={
                    'data': data,
                    'validation_type': validation_type.name
                }
            )
    
    @staticmethod
    def _validate_json_schema(
        data: Any, 
        schema: Dict[str, Any]
    ) -> bool:
        """
        Validate data against JSON Schema
        
        :param data: Data to validate
        :param schema: JSON Schema
        :return: Validation result
        """
        jsonschema.validate(instance=data, schema=schema)
        return True
    
    @staticmethod
    def _validate_regex(
        data: Any, 
        pattern: str
    ) -> bool:
        """
        Validate data against regex pattern
        
        :param data: Data to validate
        :param pattern: Regex pattern
        :return: Validation result
        """
        if not isinstance(data, str):
            raise ValueError("Regex validation requires string input")
        
        if not re.match(pattern, data):
            raise ValueError(f"Data does not match pattern: {pattern}")
        
        return True
    
    @staticmethod
    def _validate_custom(
        data: Any, 
        validator: Callable[[Any], bool]
    ) -> bool:
        """
        Validate data using custom validation function
        
        :param data: Data to validate
        :param validator: Custom validation function
        :return: Validation result
        """
        if not validator(data):
            raise ValueError("Custom validation failed")
        
        return True
    
    @staticmethod
    def _validate_type(
        data: Any, 
        expected_type: Union[type, tuple]
    ) -> bool:
        """
        Validate data type
        
        :param data: Data to validate
        :param expected_type: Expected type or types
        :return: Validation result
        """
        if not isinstance(data, expected_type):
            raise ValueError(f"Expected type {expected_type}, got {type(data)}")
        
        return True

class DataNormalizer:
    """
    Utility for normalizing and transforming data
    """
    @staticmethod
    def normalize_json(
        data: Any, 
        indent: Optional[int] = None
    ) -> str:
        """
        Normalize JSON data to consistent format
        
        :param data: Data to normalize
        :param indent: Indentation for pretty printing
        :return: Normalized JSON string
        """
        return json.dumps(
            data, 
            sort_keys=True, 
            indent=indent
        )
    
    @staticmethod
    def sanitize_input(
        input_data: str, 
        max_length: Optional[int] = None,
        allowed_chars: Optional[str] = None
    ) -> str:
        """
        Sanitize input string
        
        :param input_data: Input to sanitize
        :param max_length: Maximum allowed length
        :param allowed_chars: Regex pattern of allowed characters
        :return: Sanitized input
        """
        # Trim to max length if specified
        if max_length is not None:
            input_data = input_data[:max_length]
        
        # Filter allowed characters
        if allowed_chars:
            input_data = re.sub(
                f'[^{re.escape(allowed_chars)}]', 
                '', 
                input_data
            )
        
        return input_data.strip()

# Example usage
def example_validation():
    """Demonstrate validation functionality"""
    # JSON Schema validation
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "number", "minimum": 0}
        },
        "required": ["name"]
    }
    
    # Validate valid data
    valid_data = {"name": "John", "age": 30}
    print("Valid data:", 
        Validator.validate(
            valid_data, 
            ValidationType.JSON_SCHEMA, 
            schema
        )
    )
    
    # Regex validation
    print("Regex validation:", 
        Validator.validate(
            "john@example.com", 
            ValidationType.REGEX, 
            r'^[\w\.-]+@[\w\.-]+\.\w+$'
        )
    )

# Main execution
if __name__ == "__main__":
    example_validation()
