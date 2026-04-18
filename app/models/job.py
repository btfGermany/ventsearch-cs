"""
Ingestion Job model - Tracks background ingestion tasks.
"""

from datetime import datetime
from app.core.extensions import db
from app.models.mixins import TimestampMixin


class IngestionJob(db.Model, TimestampMixin):
    """Ingestion job for tracking background tasks."""
    
    __tablename__ = 'ingestion_jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String(36), unique=True, nullable=False, index=True)
    
    # Job type
    job_type = db.Column(db.String(50), nullable=False, index=True)
    # e.g., FULL_INGEST, INCREMENTAL_SYNC, NORMALIZE, MATCH, INDEX, SCREENING
    
    # Source
    source = db.Column(db.String(50), index=True)
    
    # Status
    status = db.Column(db.String(20), nullable=False, default='pending', index=True)
    # pending, running, completed, failed, cancelled
    
    # Progress
    total_items = db.Column(db.Integer, default=0)
    processed_items = db.Column(db.Integer, default=0)
    failed_items = db.Column(db.Integer, default=0)
    
    # Results
    results = db.Column(db.JSON)
    
    # Error info
    error_message = db.Column(db.Text)
    error_traceback = db.Column(db.Text)
    
    # Timing
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # Retry
    retries = db.Column(db.Integer, default=0)
    max_retries = db.Column(db.Integer, default=3)
    
    # Trigger
    triggered_by = db.Column(db.String(255))
    trigger_url = db.Column(db.String(2000))
    
    def __repr__(self):
        return f'<IngestionJob {self.job_id}:{self.status}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'job_id': self.job_id,
            'job_type': self.job_type,
            'source': self.source,
            'status': self.status,
            'total_items': self.total_items,
            'processed_items': self.processed_items,
            'failed_items': self.failed_items,
            'error_message': self.error_message,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }


class SourceSyncState(db.Model):
    """Tracks sync state per source for incremental updates."""
    
    __tablename__ = 'source_sync_states'
    
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(50), unique=True, nullable=False, index=True)
    
    # Last sync info
    last_sync_at = db.Column(db.DateTime)
    last_sync_token = db.Column(db.String(1000))
    last_record_id = db.Column(db.String(255))
    
    # Sync stats
    total_synced = db.Column(db.Integer, default=0)
    total_failed = db.Column(db.Integer, default=0)
    
    # Status
    sync_status = db.Column(db.String(20), default='idle')
    # idle, syncing, error
    
    # Last error
    last_error = db.Column(db.Text)
    
    def __repr__(self):
        return f'<SourceSyncState {self.source}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'source': self.source,
            'last_sync_at': self.last_sync_at.isoformat() if self.last_sync_at else None,
            'total_synced': self.total_synced,
            'sync_status': self.sync_status,
        }


class EntityMatchReview(db.Model, TimestampMixin):
    """Review queue for uncertain entity matches."""
    
    __tablename__ = 'entity_match_reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Match type
    match_type = db.Column(db.String(50), nullable=False)
    # e.g., COMPANY_MATCH, NAME_MATCH
    
    # Company IDs involved
    company_a_id = db.Column(db.Integer, nullable=False)
    company_b_id = db.Column(db.Integer, nullable=False)
    
    # Match score
    match_score = db.Column(db.Float, nullable=False)
    
    # Match fields
    matched_fields = db.Column(db.JSON)
    
    # Review decision
    decision = db.Column(db.String(20))
    # merge, keep_separate, needs_investigation
    
    # Review metadata
    reviewed_by = db.Column(db.String(255))
    reviewed_at = db.Column(db.DateTime)
    review_notes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<EntityMatchReview {self.match_score}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'match_type': self.match_type,
            'company_a_id': self.company_a_id,
            'company_b_id': self.company_b_id,
            'match_score': self.match_score,
            'decision': self.decision,
            'reviewed_by': self.reviewed_by,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
        }