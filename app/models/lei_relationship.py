"""
LEI Relationship model - Parent-child relationships from GLEIF.
"""

from app.core.extensions import db
from app.models.mixins import ProvenanceMixin


class LEIRelationship(db.Model, ProvenanceMixin):
    """LEI relationship (ownership, subsidiary, etc.)."""
    
    __tablename__ = 'lei_relationships'
    
    id = db.Column(db.Integer, primary_key=True)
    lei_record_id = db.Column(db.Integer, db.ForeignKey('lei_records.id'), nullable=False, index=True)
    
    # Relationship type
    relationship_type = db.Column(db.String(50), nullable=False)
    # e.g., IS_DIRECT_SUBSIDIARY_OF, IS_ULTIMATE_PARENT_OF, IS_GENERAL_PARTNER_OF
    
    # Related LEI
    related_lei = db.Column(db.String(20), nullable=False, index=True)
    related_entity_name = db.Column(db.String(500))
    
    # Relationship status
    relationship_status = db.Column(db.String(20))
    
    # Hierarchy
    start_node = db.Column(db.Boolean)  # True if this record is start node
    level = db.Column(db.Integer)  # 1 = direct, 2 = indirect, etc.
    
    # Period
    period_start = db.Column(db.Date)
    period_end = db.Column(db.Date)
    
    # Ownership percentage (if applicable)
    ownership_percentage = db.Column(db.Float)
    
    # Governance
    is_controller = db.Column(db.Boolean)
    
    # Relationships
    lei_record = db.relationship('LEIRecord', back_populates='relationships')
    
    def __repr__(self):
        return f'<LEIRelationship {self.relationship_type} {self.related_lei}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'lei_record_id': self.lei_record_id,
            'relationship_type': self.relationship_type,
            'related_lei': self.related_lei,
            'related_entity_name': self.related_entity_name,
            'ownership_percentage': self.ownership_percentage,
            'level': self.level,
        }