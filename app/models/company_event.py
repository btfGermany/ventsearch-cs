"""
Company Event model - Tracks company lifecycle events.
"""

from app.core.extensions import db
from app.models.mixins import ProvenanceMixin, TimestampMixin


class CompanyEvent(db.Model, ProvenanceMixin, TimestampMixin):
    """Company event capturing corporate actions."""
    
    __tablename__ = 'company_events'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False, index=True)
    
    # Event type
    event_type = db.Column(db.String(50), nullable=False, index=True)
    # e.g., FOUNDED, DISSOLVED, LIQUIDATION, MERGED, SPLIT, CAPITAL_CHANGE, ADDRESS_CHANGE, LEGAL_FORM_CHANGE
    
    # Event date
    event_date = db.Column(db.Date, index=True)
    event_date_text = db.Column(db.String(255))  # Original text if exact date unknown
    
    # Description
    description = db.Column(db.Text)
    description_source = db.Column(db.String(255))
    
    # Authority
    registering_court = db.Column(db.String(255))
    gazette = db.Column(db.String(255))
    
    # Amounts (for capital changes)
    amount_old = db.Column(db.Numeric(15, 2))
    amount_new = db.Column(db.Numeric(15, 2))
    currency = db.Column(db.String(3))
    
    # Relationships
    company = db.relationship('Company', back_populates='events')
    
    def __repr__(self):
        return f'<CompanyEvent {self.event_type} {self.event_date}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'event_type': self.event_type,
            'event_date': self.event_date.isoformat() if self.event_date else None,
            'description': self.description,
            'source': self.source,
        }