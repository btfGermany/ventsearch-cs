"""
Legal Reference model - References to legal documents.
"""

from app.core.extensions import db
from app.models.mixins import ProvenanceMixin, TimestampMixin


class LegalReference(db.Model, ProvenanceMixin, TimestampMixin):
    """Legal reference linked to companies."""
    
    __tablename__ = 'legal_references'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Reference type
    reference_type = db.Column(db.String(50), nullable=False)
    # e.g., COURT_DECISION, LAW, REGULATION, CONTRACT, FILING
    
    # Reference ID
    reference_id = db.Column(db.String(255), index=True)
    
    # Title
    title = db.Column(db.String(1000), nullable=False)
    
    # Court / Authority
    court = db.Column(db.String(255))
    court_code = db.Column(db.String(50))
    
    # Date
    decision_date = db.Column(db.Date)
    publication_date = db.Column(db.Date)
    
    # Case number
    case_number = db.Column(db.String(255))
    
    # Court level
    court_level = db.Column(db.String(50))
    
    # Summary
    summary = db.Column(db.Text)
    summary_source = db.Column(db.String(255))
    
    # Link
    link = db.Column(db.String(2000))
    
    # Status
    is_in_force = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<LegalReference {self.reference_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'reference_type': self.reference_type,
            'reference_id': self.reference_id,
            'title': self.title,
            'court': self.court,
            'decision_date': self.decision_date.isoformat() if self.decision_date else None,
            'case_number': self.case_number,
        }