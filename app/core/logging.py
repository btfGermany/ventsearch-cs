"""
Logging configuration for the Company Intelligence Aggregator Platform.

Provides structured logging with OpenTelemetry-ready hooks.
"""

import logging
import sys
from typing import Any


class StructuredFormatter(logging.Formatter):
    """Structured log formatter that outputs JSON-like format."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        if hasattr(record, 'company_id'):
            log_data['company_id'] = record.company_id
        
        if hasattr(record, 'source'):
            log_data['source'] = record.source
        
        if hasattr(record, 'job_id'):
            log_data['job_id'] = record.job_id
        
        return str(log_data)


def setup_logging(app: Any) -> None:
    """Configure logging for the Flask application."""
    log_level = app.config.get('LOG_LEVEL', 'INFO')
    log_format = app.config.get('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific log levels for noisy libraries
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('celery').setLevel(logging.INFO)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    # Configure structured logging for company intel
    logger = logging.getLogger('company_intel')
    logger.setLevel(getattr(logging, log_level))


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(f'company_intel.{name}')