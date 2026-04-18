"""
Model mixins for common fields.
"""

from datetime import datetime
from app.core.extensions import db


class ProvenanceMixin:
    """Mixin for tracking data provenance."""
    
    source = db.Column(db.String(50), index=True, nullable=False)
    source_id = db.Column(db.String(255), index=True)
    source_url = db.Column(db.String(2000))
    source_raw_id = db.Column(db.String(255), index=True)
    trust_score = db.Column(db.Float, default=0.5)
    ingested_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Data quality
    data_quality = db.Column(db.String(20), default='standard')  # standard, high, low
    is_deleted = db.Column(db.Boolean, default=False)


class TimestampMixin:
    """Mixin for created/updated timestamps."""
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)