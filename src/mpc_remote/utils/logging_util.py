"""Logging utilities for Model Context Protocol"""
import json
import logging
import sys
from enum import Enum
from typing import Any, Dict, List, Optional, TextIO, Union


class LogLevel(Enum):
    """Standard logging levels"""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

class MCPLogger:
    """
    Comprehensive logging management for Model Context Protocol

    Provides flexible logging configuration and management
    """
    def __init__(
        self,
        name: str = 'mcp',
        level: LogLevel = LogLevel.INFO,
        log_file: Optional[str] = None,
        stream: Optional[Union[TextIO, str]] = None
    )->None:
        """
        Initialize MCP logger

        :param name: Logger name
        :param level: Logging level
        :param log_file: Path to log file
        :param stream: Output stream or stream name
        """
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level.value)

        # Clear existing handlers
        self.logger.handlers.clear()

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # File handler
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

        # Stream handler
        if stream is not None:
            if isinstance(stream, str):
                stream = sys.stdout if stream.lower() == 'stdout' else sys.stderr

            stream_handler = logging.StreamHandler(stream)
            stream_handler.setFormatter(formatter)
            self.logger.addHandler(stream_handler)

        # Default to console output if no handlers
        if not self.logger.handlers:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def debug(self, message: str, *args: List[str], **kwargs:Dict[str, Any])->None:
        """Log debug message"""
        self.logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args: List[str], **kwargs:Dict[str, Any])->None:
        """Log info message"""
        self.logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args: List[str], **kwargs:Dict[str, Any])->None:
        """Log warning message"""
        self.logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args: List[str], **kwargs:Dict[str, Any])->None:
       """Log error message"""
       self.logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args: List[str], **kwargs:Dict[str, Any])->None:
        """Log critical message"""
        self.logger.critical(message, *args, **kwargs)

    def log(
        self,
        level: LogLevel,
        message: str,
        *args:List[str],
        **kwargs:Dict[str, Any]
    )->None:
        """
        Log message at specified level

        :param level: Logging level
        :param message: Log message
        """
        self.logger.log(level.value, message, *args, **kwargs)

    def exception(self, message: str, *args: List[str], **kwargs:Dict[str, Any])->None:
        """
        Log exception with traceback

        :param message: Exception message
        """
        self.logger.exception(message, *args, **kwargs)

class AuditLogger(MCPLogger):
    """
    Specialized logger for audit trail and compliance tracking

    Provides enhanced logging for security-critical events
    """
    def __init__(
        self,
        name: str = 'mcp_audit',
        log_file: Optional[str] = None
    )->None:
        """
        Initialize audit logger

        :param name: Logger name
        :param log_file: Path to audit log file
        """
        super().__init__(
            name=name,
            level=LogLevel.INFO,
            log_file=log_file or 'mcp_audit.log'
        )

        # Customize formatter for audit logs
        audit_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s | %(extra)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Update handlers with audit formatter
        for handler in self.logger.handlers:
            handler.setFormatter(audit_formatter)

    def audit_event(
        self,
        event_type: str,
        description: str,
        user: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None
    )->None:
        """
        Log a structured audit event

        :param event_type: Type of event
        :param description: Event description
        :param user: User associated with event
        :param extra_data: Additional event metadata
        """
        extra_info = {
            'user': user,
            'extra': json.dumps(extra_data or {})
        }

        # Log as info with extra context
        self.logger.info(
            f"{event_type}: {description}",
            extra=extra_info
        )

# Logging configuration utility
def configure_logging(
    default_level: LogLevel = LogLevel.INFO,
    log_file: Optional[str] = None
) -> MCPLogger:
    """
    Quick configuration of default MCP logging

    :param default_level: Default logging level
    :param log_file: Optional log file path
    :return: Configured logger
    """
    return MCPLogger(
        name='mcp',
        level=default_level,
        log_file=log_file,
        stream='stdout'
    )

# Example usage
def example_logging()->None:
    """Demonstrate logging functionality"""
    # Standard logger
    logger = MCPLogger(level=LogLevel.DEBUG)
    logger.debug("Debug message")
    logger.info("Information message")
    logger.warning("Warning message")

    # Audit logger
    audit_logger = AuditLogger()
    audit_logger.audit_event(
        event_type='USER_LOGIN',
        description='Successful login',
        user='example_user',
        extra_data={'ip': '192.168.1.1'}
    )

# Main execution
if __name__ == "__main__":
    example_logging()
