"""
Sanctions Entity model - Entities from sanctions lists.
"""

from app.core.extensions import db
from app.models.mixins import ProvenanceMixin, TimestampMixin


class SanctionsEntity(db.Model, ProvenanceMixin, TimestampMixin):
    """Sanctions/PEP entity from various lists."""
    
    __tablename__ = 'sanctions_entities'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Source sanctions list
    list_name = db.Column(db.String(100), nullable=False, index=True)
    # e.g., EU_SANCTIONS, OFAC, UN_SANCTIONS, PEP_GERMANY
    
    # Entity ID in source
    entity_id = db.Column(db.String(255), index=True)
    
    # Entity type
    entity_type = db.Column(db.String(20), nullable=False)
    # e.g., individual, entity, vessel, aircraft
    
    # Name
    name = db.Column(db.String(500), nullable=False, index=True)
    name_norm = db.Column(db.String(500), index=True)
    
    # Aliases
    aliases = db.Column(db.JSON)  # List of alternative names
    
    # Program
    program = db.Column(db.String(255), index=True)
    
    # Designation date
    designation_date = db.Column(db.Date)
    
    # Country
    nationality = db.Column(db.String(2), index=True)
    
    # Status
    is_designated = db.Column(db.Boolean, default=True)
    
    # Additional info
    program_description = db.Column(db.Text)
    listing_remarks = db.Column(db.Text)
    
    # Links
    link = db.Column(db.String(2000))
    
    # Score/weight for matching
    risk_score = db.Column(db.Float, default=0.5)
    
    def __repr__(self):
        return f'<SanctionsEntity {self.list_name}:{self.entity_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'list_name': self.list_name,
            'entity_id': self.entity_id,
            'entity_type': self.entity_type,
            'name': self.name,
            'program': self.program,
            'nationality': self.nationality,
            'is_designated': self.is_designated,
            'risk_score': self.risk_score,
        }