"""
Flask extensions initialization.

Provides database, migration, Celery, and OpenSearch client instances.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
# Database
db = SQLAlchemy()

# Migration
migrate = Migrate()

# Celery - initialized lazily in app
celery = None

# OpenSearch client (lazy-loaded)
opensearch_client = None