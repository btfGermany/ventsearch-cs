"""
Error handling module for standardized API error responses.
"""

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException
from marshmallow import ValidationError


class APIError(Exception):
    """Base API error with standard error format."""
    
    def __init__(self, message: str, status_code: int = 400, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or 'API_ERROR'
        self.details = details or {}
    
    def to_dict(self):
        return {
            'error': True,
            'error_code': self.error_code,
            'message': self.message,
            'details': self.details,
        }


class NotFoundError(APIError):
    """Resource not found error."""
    
    def __init__(self, resource: str, identifier: str = None):
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        super().__init__(message, 404, 'NOT_FOUND')
        self.identifier = identifier


class ValidationError_(APIError):
    """Validation error."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, 400, 'VALIDATION_ERROR', details)


class AuthenticationError(APIError):
    """Authentication error."""
    
    def __init__(self, message: str = 'Authentication required'):
        super().__init__(message, 401, 'AUTHENTICATION_REQUIRED')


class AuthorizationError(APIError):
    """Authorization error."""
    
    def __init__(self, message: str = 'Insufficient permissions'):
        super().__init__(message, 403, 'AUTHORIZATION_DENIED')


class RateLimitError(APIError):
    """Rate limit error."""
    
    def __init__(self, message: str = 'Rate limit exceeded'):
        super().__init__(message, 429, 'RATE_LIMIT_EXCEEDED')


class InternalServerError(APIError):
    """Internal server error."""
    
    def __init__(self, message: str = 'Internal server error'):
        super().__init__(message, 500, 'INTERNAL_SERVER_ERROR')


def register_error_handlers(app: Flask) -> None:
    """Register error handlers for the Flask application."""
    
    @app.errorhandler(APIError)
    def handle_api_error(error: APIError):
        return jsonify(error.to_dict()), error.status_code
    
    @app.errorhandler(ValidationError)
    def handle_validation_error(error: ValidationError):
        return jsonify({
            'error': True,
            'error_code': 'VALIDATION_ERROR',
            'message': 'Validation failed',
            'details': error.messages,
        }), 400
    
    @app.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException):
        return jsonify({
            'error': True,
            'error_code': error.name.upper().replace(' ', '_'),
            'message': error.description,
        }), error.code
    
    @app.errorhandler(Exception)
    def handle_exception(error: Exception):
        app.logger.error(f"Unhandled exception: {str(error)}", exc_info=True)
        return jsonify({
            'error': True,
            'error_code': 'INTERNAL_SERVER_ERROR',
            'message': 'An unexpected error occurred',
        }), 500