"""
Sanctions Match model - Represents matches between companies and sanctions entities.
"""

from app.core.extensions import db
from app.models.mixins import ProvenanceMixin, TimestampMixin


class SanctionsMatch(db.Model, ProvenanceMixin, TimestampMixin):
    """Match result between a company and a sanctions entity."""
    
    __tablename__ = 'sanctions_matches'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False, index=True)
    sanctions_entity_id = db.Column(db.Integer, db.ForeignKey('sanctions_entities.id'), nullable=False, index=True)
    
    # Match type
    match_type = db.Column(db.String(20), nullable=False)
    # e.g., NAME_MATCH, ALIAS_MATCH, ADDRESS_MATCH, DIRECTOR_MATCH
    
    # Confidence score (0.0 - 1.0)
    match_score = db.Column(db.Float, nullable=False)
    
    # Match details
    matched_field = db.Column(db.String(50))  # Which field matched
    matched_value = db.Column(db.String(1000))  # The value that matched
    
    # Review status
    review_status = db.Column(db.String(20), default='pending')
    # pending, confirmed, false_positive, cleared
    
    # Review info
    reviewed_by = db.Column(db.String(255))
    reviewed_at = db.Column(db.DateTime)
    review_notes = db.Column(db.Text)
    
    # Relationships
    company = db.relationship('Company')
    sanctions_entity = db.relationship('SanctionsEntity')
    
    def __repr__(self):
        return f'<SanctionsMatch {self.match_score}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'sanctions_entity_id': self.sanctions_entity_id,
            'match_type': self.match_type,
            'match_score': self.match_score,
            'review_status': self.review_status,
        }