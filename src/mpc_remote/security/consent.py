"""Consent management for Model Context Protocol"""

import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, Optional


class ConsentStatus(Enum):
    """Represents the status of user consent"""
    PENDING = auto()
    GRANTED = auto()
    DENIED = auto()
    REVOKED = auto()

@dataclass
class ConsentRecord:
    """
    Represents a detailed consent record
    
    Tracks consent for specific resources or tools
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    resource_name: str = ''
    is_tool: bool = False
    status: ConsentStatus = ConsentStatus.PENDING
    granted_at: Optional[float] = None
    revoked_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class ConsentManager:
    """
    Manages user consent for resources and tools
    
    Provides granular consent tracking and management
    """
    def __init__(self):
        """Initialize consent manager"""
        self._consent_records: Dict[str, ConsentRecord] = {}
        self._consent_hooks: Dict[str, Callable] = {}
    
    def request_consent(
        self, 
        resource_name: str, 
        is_tool: bool = False,
        user_context: Optional[Dict[str, Any]] = None
    ) -> ConsentRecord:
        """
        Request consent for a resource or tool
        
        :param resource_name: Name of resource or tool
        :param is_tool: Whether the request is for a tool
        :param user_context: Optional user context
        :return: Consent record
        """
        # Check for existing pending or granted consent
        for record in self._consent_records.values():
            if (record.resource_name == resource_name and 
                record.is_tool == is_tool and
                record.status in [ConsentStatus.PENDING, ConsentStatus.GRANTED]):
                return record
        
        # Create new consent record
        record = ConsentRecord(
            resource_name=resource_name,
            is_tool=is_tool
        )
        
        # Check custom consent hook if defined
        if resource_name in self._consent_hooks:
            try:
                consent_granted = self._consent_hooks[resource_name](
                    resource_name=resource_name,
                    is_tool=is_tool,
                    user_context=user_context
                )
                record.status = (
                    ConsentStatus.GRANTED if consent_granted 
                    else ConsentStatus.DENIED
                )
            except Exception as e:
                record.status = ConsentStatus.DENIED
                record.metadata['error'] = str(e)
        
        # Store and return record
        self._consent_records[record.id] = record
        return record
    
    def grant_consent(
        self, 
        record_id: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConsentRecord:
        """
        Explicitly grant consent for a record
        
        :param record_id: Consent record ID
        :param metadata: Additional consent metadata
        :return: Updated consent record
        """
        if record_id not in self._consent_records:
            raise ValueError(f"Consent record {record_id} not found")
        
        record = self._consent_records[record_id]
        record.status = ConsentStatus.GRANTED
        record.metadata.update(metadata or {})
        return record
    
    def revoke_consent(
        self, 
        record_id: str, 
        reason: Optional[str] = None
    ) -> ConsentRecord:
        """
        Revoke previously granted consent
        
        :param record_id: Consent record ID
        :param reason: Reason for revocation
        :return: Updated consent record
        """
        if record_id not in self._consent_records:
            raise ValueError(f"Consent record {record_id} not found")
        
        record = self._consent_records[record_id]
        record.status = ConsentStatus.REVOKED
        if reason:
            record.metadata['revocation_reason'] = reason
        return record
    
    def add_consent_hook(
        self, 
        resource_name: str, 
        hook: Callable[[str, bool, Optional[Dict[str, Any]]], bool]
    ):
        """
        Add a custom consent validation hook
        
        :param resource_name: Resource or tool name
        :param hook: Callable that returns consent status
        """
        self._consent_hooks[resource_name] = hook
    
    def get_consent_status(
        self, 
        resource_name: str, 
        is_tool: bool = False
    ) -> ConsentStatus:
        """
        Check consent status for a resource or tool
        
        :param resource_name: Name of resource or tool
        :param is_tool: Whether checking a tool
        :return: Current consent status
        """
        for record in self._consent_records.values():
            if (record.resource_name == resource_name and 
                record.is_tool == is_tool):
                return record.status
        
        return ConsentStatus.PENDING

# Example usage
def example_consent_management():
    """Demonstrate consent management functionality"""
    consent_manager = ConsentManager()
    
    # Add a custom consent hook
    def custom_consent_hook(resource_name, is_tool, user_context):
        # Example: Always grant consent for 'basic_tool'
        return resource_name == 'basic_tool'
    
    consent_manager.add_consent_hook('basic_tool', custom_consent_hook)
    
    # Request consent
    consent_record = consent_manager.request_consent('basic_tool', is_tool=True)
    print(f"Consent status: {consent_record.status}")
    
    # Manually grant consent
    consent_record = consent_manager.grant_consent(consent_record.id)
    print(f"Updated consent status: {consent_record.status}")

# Main execution
if __name__ == "__main__":
    example_consent_management()
