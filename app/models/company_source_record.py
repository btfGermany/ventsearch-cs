"""
Company Source Record - Raw data from each source for provenance and audit.
"""

from app.core.extensions import db
from app.models.mixins import ProvenanceMixin


class CompanySourceRecord(db.Model, ProvenanceMixin):
    """Raw source record for a company from a specific source."""
    
    __tablename__ = 'company_source_records'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False, index=True)
    
    # Source and source-specific ID
    source = db.Column(db.String(50), nullable=False, index=True)
    source_record_id = db.Column(db.String(255), index=True)
    
    # Source-specific data (JSON)
    source_data = db.Column(db.JSON)
    
    # Last sync info
    last_synced = db.Column(db.DateTime)
    
    # Relationships
    company = db.relationship('Company', back_populates='source_records')
    
    __table_args__ = (
        db.Index('ix_company_source', 'company_id', 'source'),
    )
    
    def __repr__(self):
        return f'<CompanySourceRecord {self.source}:{self.source_record_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'source': self.source,
            'source_record_id': self.source_record_id,
            'last_synced': self.last_synced.isoformat() if self.last_synced else None,
        }