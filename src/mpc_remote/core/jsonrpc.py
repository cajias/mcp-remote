from __future__ import annotations

import json
import uuid
from typing import Any, TypeVar

from pydantic import BaseModel, Field, model_validator

T = TypeVar("T", bound="JSONRPCMessage")


class JSONRPCError(BaseModel):
    """Structured JSON-RPC error representation"""

    code: int
    message: str
    data: Any | None = None

    def __str__(self) -> str:
        return f"JSON-RPC Error {self.code}: {self.message}"


class JSONRPCMessage(BaseModel):
    """Base JSON-RPC message model"""

    jsonrpc: str = Field(default="2.0", alias="jsonrpc")

    @model_validator(mode="before")
    @classmethod
    def validate_jsonrpc_version(cls, values: Any) -> Any:
        """Ensure JSON-RPC version is 2.0"""
        if not isinstance(values, dict):
            return values

        version = values.get("jsonrpc", "2.0")
        if version != "2.0":
            raise ValueError(f"Unsupported JSON-RPC version: {version}")

        return values

    def model_dump_json(self, **kwargs: Any) -> str:
        """Enhanced JSON dumping with aliases and exclusion of None"""
        return super().model_dump_json(by_alias=True, exclude_none=True, **kwargs)


class JSONRPCRequest(JSONRPCMessage):
    """JSON-RPC request message"""

    method: str
    params: dict[str, Any] | list | None = None
    id: str | int = Field(default_factory=lambda: str(uuid.uuid4()))


class JSONRPCResponse(JSONRPCMessage):
    """JSON-RPC response message"""

    result: Any | None = None
    error: JSONRPCError | None = None
    id: str | int | None = None

    @model_validator(mode="after")
    def validate_result_or_error(self) -> JSONRPCResponse:
        """Ensure either result or error is present"""
        if self.result is None and self.error is None:
            raise ValueError("Response must have either result or error")
        return self


class JSONRPCProtocol:
    """Advanced JSON-RPC 2.0 protocol handler"""

    # Standard JSON-RPC error codes
    ERROR_PARSE = -32700
    ERROR_INVALID_REQUEST = -32600
    ERROR_METHOD_NOT_FOUND = -32601
    ERROR_INVALID_PARAMS = -32602
    ERROR_INTERNAL = -32603

    @classmethod
    def create_request(
        cls, method: str, params: dict[str, Any] | list | None = None, id: str | int | None = None
    ) -> JSONRPCRequest:
        """Create a type-safe JSON-RPC request"""
        return JSONRPCRequest(method=method, params=params, id=id or str(uuid.uuid4()))

    @classmethod
    def create_response(
        cls, result: Any | None = None, error: JSONRPCError | dict[str, Any] | None = None, id: str | int | None = None
    ) -> JSONRPCResponse:
        """Create a type-safe JSON-RPC response"""
        # Convert dict to JSONRPCError if needed
        if isinstance(error, dict):
            error = JSONRPCError(**error)

        return JSONRPCResponse(result=result, error=error, id=id)

    @classmethod
    def parse_message(cls, message: str | dict[str, Any], expected_type: type[T] | None = None) -> T:
        """
        Parse and validate a JSON-RPC message

        :param message: Raw message to parse
        :param expected_type: Optional expected message type
        :return: Validated message
        :raises ValidationError: If message is invalid
        """
        # Parse string to dict if needed
        if isinstance(message, str):
            try:
                message = json.loads(message)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON: {e!s}") from e

        # Determine message type if not specified
        if expected_type is None:
            if "method" in message:
                expected_type = JSONRPCRequest  # type: ignore
            elif "result" in message or "error" in message:
                expected_type = JSONRPCResponse  # type: ignore
            else:
                raise ValueError("Unable to determine message type")

        # Validate and return
        return expected_type.model_validate(message)

    @classmethod
    def is_request(cls, message: dict[str, Any]) -> bool:
        """Check if message is a JSON-RPC request"""
        return "method" in message and "id" in message

    @classmethod
    def is_response(cls, message: dict[str, Any]) -> bool:
        """Check if message is a JSON-RPC response"""
        return ("result" in message or "error" in message) and "id" in message
