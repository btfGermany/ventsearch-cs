"""
LEI Record model - Legal Entity Identifier from GLEIF.
"""

from app.core.extensions import db
from app.models.mixins import ProvenanceMixin, TimestampMixin


class LEIRecord(db.Model, ProvenanceMixin, TimestampMixin):
    """LEI record from GLEIF."""
    
    __tablename__ = 'lei_records'
    
    id = db.Column(db.Integer, primary_key=True)
    lei = db.Column(db.String(20), unique=True, nullable=False, index=True)
    
    # Entity info
    entity_name = db.Column(db.String(500), nullable=False)
    entity_name_norm = db.Column(db.String(500), index=True)
    
    # Entity status
    entity_status = db.Column(db.String(50))
    
    # Jurisdiction
    jurisdiction = db.Column(db.String(2))
    
    # Legal form
    legal_form = db.Column(db.String(100))
    legal_form_code = db.Column(db.String(10))
    
    # Registered address
    registered_street = db.Column(db.String(500))
    registered_city = db.Column(db.String(255))
    registered_postal_code = db.Column(db.String(20))
    registered_country = db.Column(db.String(2))
    
    # Headquarters address
    headquarters_street = db.Column(db.String(500))
    headquarters_city = db.Column(db.String(255))
    headquarters_postal_code = db.Column(db.String(20))
    headquarters_country = db.Column(db.String(2))
    
    # Registration
    initial_registration_date = db.Column(db.Date)
    last_update_date = db.Column(db.Date)
    next_renewal_date = db.Column(db.Date)
    
    # Managing LOU
    managing_lou = db.Column(db.String(20))
    
    # Relationships
    relationships = db.relationship('LEIRelationship', back_populates='lei_record', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<LEIRecord {self.lei}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'lei': self.lei,
            'entity_name': self.entity_name,
            'entity_status': self.entity_status,
            'jurisdiction': self.jurisdiction,
            'legal_form': self.legal_form,
        }