"""
Configuration module for the Company Intelligence Aggregator Platform.

Supports configuration via environment variables with sane dev defaults.
"""

import os
from datetime import timedelta


class Config:
    """Base configuration with development defaults."""

    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = False
    TESTING = False

    # Database - SQLite as default for development
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///company_intel.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {}

    # Celery / Redis
    CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TIMEZONE = 'UTC'
    CELERY_ENABLE_UTC = True
    CELERY_TASK_TRACK_STARTED = True
    CELERY_TASK_TIME_LIMIT = 3600
    CELERY_TASK_SOFT_TIME_LIMIT = 3300

    # OpenSearch
    OPENSEARCH_URL = os.environ.get('OPENSEARCH_URL', 'http://localhost:9200')
    OPENSEARCH_USER = os.environ.get('OPENSEARCH_USER', '')
    OPENSEARCH_PASSWORD = os.environ.get('OPENSEARCH_PASSWORD', '')
    OPENSEARCH_INDEX = 'companies'

    # API
    API_VERSION = 'v1'
    API_TITLE = 'Company Intelligence Aggregator API'
    API_DESCRIPTION = 'REST API for the Company Knowledge Graph'

    # Pagination
    DEFAULT_PAGE_SIZE = 25
    MAX_PAGE_SIZE = 100

    # CORS
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')

    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # Source Configurations
    SOURCE_OFFENEREGISTER_ENABLED = os.environ.get('SOURCE_OFFENEREGISTER_ENABLED', 'true').lower() == 'true'
    SOURCE_OPENCORPORATES_ENABLED = os.environ.get('SOURCE_OPENCORPORATES_ENABLED', 'true').lower() == 'true'
    SOURCE_OPENCORPORATES_API_KEY = os.environ.get('SOURCE_OPENCORPORATES_API_KEY', '')
    SOURCE_GLEIF_ENABLED = os.environ.get('SOURCE_GLEIF_ENABLED', 'true').lower() == 'true'
    SOURCE_OPENOWNERSHIP_ENABLED = os.environ.get('SOURCE_OPENOWNERSHIP_ENABLED', 'true').lower() == 'true'
    SOURCE_OPENSANCTIONS_ENABLED = os.environ.get('SOURCE_OPENSANCTIONS_ENABLED', 'true').lower() == 'true'
    SOURCE_OPENLEGALDATA_ENABLED = os.environ.get('SOURCE_OPENLEGALDATA_ENABLED', 'true').lower() == 'true'
    SOURCE_GOVDATA_ENABLED = os.environ.get('SOURCE_GOVDATA_ENABLED', 'true').lower() == 'true'
    SOURCE_OSM_ENABLED = os.environ.get('SOURCE_OSM_ENABLED', 'true').lower() == 'true'

    # Matching Configuration
    MATCHING_AUTO_MERGE_THRESHOLD = float(os.environ.get('MATCHING_AUTO_MERGE_THRESHOLD', '0.95'))
    MATCHING_PROBABLE_MATCH_THRESHOLD = float(os.environ.get('MATCHING_PROBABLE_MATCH_THRESHOLD', '0.85'))
    MATCHING_MANUAL_REVIEW_THRESHOLD = float(os.environ.get('MATCHING_MANUAL_REVIEW_THRESHOLD', '0.70'))

    # Source Trust Scores (0.0 - 1.0)
    TRUST_OFFENEREGISTER = 0.95
    TRUST_GLEIF = 0.90
    TRUST_OPENCORPORATES = 0.75
    TRUST_OPENOWNERSHIP = 0.80
    TRUST_OPENSANCTIONS = 0.85
    TRUST_OPENLEGALDATA = 0.60
    TRUST_GOVDATA = 0.40
    TRUST_OSM = 0.50


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    LOG_LEVEL = 'WARNING'


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///test_company_intel.db'
    )
    LOG_LEVEL = 'DEBUG'


# Configuration mapping
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
}


def get_config():
    """Get config based on FLASK_ENV or default to development."""
    env = os.environ.get('FLASK_ENV', 'development')
    return config_by_name.get(env, DevelopmentConfig)