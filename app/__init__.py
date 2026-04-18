"""
Company Intelligence Aggregator Platform
=======================================

A modular Flask-based platform for aggregating company data from multiple sources,
focused primarily on German companies with international extensibility.

Core Features:
- Source-specific ingestion modules
- Entity resolution and matching
- Knowledge graph relationships
- Advanced search with OpenSearch
- REST API with OpenAPI documentation
- German admin interface
- Background job processing with Celery
"""

from flask import Flask
from app.core.config import Config
from app.core.extensions import db, migrate, celery, opensearch_client


def create_app(config_class=Config):
    """Create and configure the Flask application using the app factory pattern."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Initialize extension
    # Note: Celery should be initialized independently when running workers
    
    # Initialize OpenSearch if available
    if app.config.get('OPENSEARCH_URL'):
        from app.services.search.opensearch_service import OpenSearchService
        app.opensearch = OpenSearchService(app)
    
    # Register core components
    from app.core.errors import register_error_handlers
    register_error_handlers(app)

    # Register blueprints
    from app.api.v1.health import health_bp
    from app.api.v1.companies import companies_bp
    from app.api.v1.search import search_bp
    from app.api.v1.sources import sources_bp
    from app.api.v1.screening import screening_bp
    from app.api.v1.discovery import discovery_bp
    from app.api.v1.admin import admin_bp
    from app.admin.routes import admin_ui_bp
    from app.ui.routes import ui_bp

    app.register_blueprint(ui_bp)
    app.register_blueprint(health_bp, url_prefix='/api/v1')
    app.register_blueprint(companies_bp, url_prefix='/api/v1/companies')
    app.register_blueprint(search_bp, url_prefix='/api/v1')
    app.register_blueprint(sources_bp, url_prefix='/api/v1/sources')
    app.register_blueprint(screening_bp, url_prefix='/api/v1/screening')
    app.register_blueprint(discovery_bp, url_prefix='/api/v1/discovery')
    app.register_blueprint(admin_bp, url_prefix='/api/v1/admin')
    app.register_blueprint(admin_ui_bp, url_prefix='/admin', name='admin_ui')

    # Create tables
    with app.app_context():
        db.create_all()

    return app