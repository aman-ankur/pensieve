"""
Logging utility for Pensieve.
Provides structured logging with file and console output.
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.logging import RichHandler

from .config import get_config


class PensieveFormatter(logging.Formatter):
    """Custom formatter for Pensieve logs."""
    
    def __init__(self):
        super().__init__()
        self.default_fmt = '[%(asctime)s] %(levelname)8s | %(name)s | %(message)s'
        self.detailed_fmt = '[%(asctime)s] %(levelname)8s | %(name)s:%(lineno)d | %(funcName)s() | %(message)s'
    
    def format(self, record):
        # Use detailed format for DEBUG level
        if record.levelno == logging.DEBUG:
            self._style._fmt = self.detailed_fmt
        else:
            self._style._fmt = self.default_fmt
        
        return super().format(record)


class PensieveLogger:
    """Custom logger setup for Pensieve application."""
    
    def __init__(self, name: str = "pensieve"):
        """
        Initialize the logger.
        
        Args:
            name: Logger name (defaults to 'pensieve').
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.console = Console()
        self._setup_done = False
    
    def setup(self, force_reload: bool = False) -> logging.Logger:
        """
        Set up the logger with file and console handlers.
        
        Args:
            force_reload: Force recreation of handlers even if already set up.
            
        Returns:
            Configured logger instance.
        """
        if self._setup_done and not force_reload:
            return self.logger
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Get configuration
        config = get_config()
        log_config = config.logging
        
        # Set level
        level = getattr(logging, log_config.level.upper(), logging.INFO)
        self.logger.setLevel(level)
        
        # Create log directory if it doesn't exist
        log_file_path = Path(log_config.log_file)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # File handler with rotation
        file_handler = self._create_file_handler(log_config)
        self.logger.addHandler(file_handler)
        
        # Console handler if enabled
        if log_config.console_output:
            console_handler = self._create_console_handler()
            self.logger.addHandler(console_handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
        
        self._setup_done = True
        return self.logger
    
    def _create_file_handler(self, log_config) -> logging.Handler:
        """Create rotating file handler."""
        # Parse max file size
        max_bytes = self._parse_size(log_config.max_file_size)
        
        handler = logging.handlers.RotatingFileHandler(
            filename=log_config.log_file,
            maxBytes=max_bytes,
            backupCount=log_config.backup_count,
            encoding='utf-8'
        )
        
        handler.setFormatter(PensieveFormatter())
        return handler
    
    def _create_console_handler(self) -> logging.Handler:
        """Create rich console handler for beautiful terminal output."""
        handler = RichHandler(
            console=self.console,
            show_time=True,
            show_path=False,
            rich_tracebacks=True,
            tracebacks_show_locals=True
        )
        
        # Simpler format for console
        formatter = logging.Formatter(
            fmt='%(message)s',
            datefmt='%H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        return handler
    
    def _parse_size(self, size_str: str) -> int:
        """
        Parse size string like '10MB' to bytes.
        
        Args:
            size_str: Size string (e.g., '10MB', '1GB').
            
        Returns:
            Size in bytes.
        """
        size_str = size_str.upper().strip()
        
        # Default multipliers
        multipliers = {
            'B': 1,
            'KB': 1024,
            'MB': 1024 ** 2,
            'GB': 1024 ** 3
        }
        
        # Extract number and unit
        for unit, multiplier in multipliers.items():
            if size_str.endswith(unit):
                number_str = size_str[:-len(unit)].strip()
                try:
                    number = float(number_str)
                    return int(number * multiplier)
                except ValueError:
                    pass
        
        # Default to 10MB if parsing fails
        return 10 * 1024 * 1024
    
    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        """
        Get a child logger.
        
        Args:
            name: Child logger name. If None, returns main logger.
            
        Returns:
            Logger instance.
        """
        if name is None:
            return self.logger
        
        child_name = f"{self.name}.{name}"
        return logging.getLogger(child_name)


# Global logger instance
_pensieve_logger = PensieveLogger()


def setup_logging(force_reload: bool = False) -> logging.Logger:
    """
    Set up application-wide logging.
    
    Args:
        force_reload: Force recreation of handlers.
        
    Returns:
        Main logger instance.
    """
    return _pensieve_logger.setup(force_reload=force_reload)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name. If None, returns main logger.
        
    Returns:
        Logger instance.
    """
    if not _pensieve_logger._setup_done:
        setup_logging()
    
    return _pensieve_logger.get_logger(name)


def log_system_info():
    """Log basic system information."""
    logger = get_logger("system")
    
    logger.info("🧠 Pensieve starting up...")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Platform: {sys.platform}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    # Log configuration info
    try:
        config = get_config()
        logger.info(f"Zoom folder: {config.monitoring.zoom_folder}")
        logger.info(f"Summaries folder: {config.output.summaries_folder}")
        logger.info(f"AI model: {config.processing.model_name}")
        logger.info(f"Features enabled: {[k for k, v in config.features.items() if v]}")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")


def log_performance_metrics(operation: str, duration: float, success: bool = True, **kwargs):
    """
    Log performance metrics for operations.
    
    Args:
        operation: Name of the operation.
        duration: Duration in seconds.
        success: Whether operation was successful.
        **kwargs: Additional metadata to log.
    """
    logger = get_logger("performance")
    
    status = "✅ SUCCESS" if success else "❌ FAILED"
    extra_info = " | ".join(f"{k}={v}" for k, v in kwargs.items())
    
    message = f"{status} | {operation} | {duration:.2f}s"
    if extra_info:
        message += f" | {extra_info}"
    
    if success:
        logger.info(message)
    else:
        logger.error(message) 