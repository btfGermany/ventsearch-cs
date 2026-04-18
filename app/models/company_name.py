"""
Company Name model - Tracks all names of a company including historical names.
"""

from app.core.extensions import db
from app.models.mixins import ProvenanceMixin


class CompanyName(db.Model, ProvenanceMixin):
    """Company name entity including aliases and historical names."""
    
    __tablename__ = 'company_names'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False, index=True)
    
    name = db.Column(db.String(500), nullable=False)
    name_norm = db.Column(db.String(500), index=True)  # normalized for matching
    
    # Name type
    name_type = db.Column(db.String(20), default='name')  # name, legal_name, trading_name, alias, former_name
    
    # Status
    is_primary = db.Column(db.Boolean, default=True)
    is_current = db.Column(db.Boolean, default=True)
    
    # Validity period
    valid_from = db.Column(db.Date)
    valid_to = db.Column(db.Date)
    
    # Language
    language = db.Column(db.String(3), default='de')
    
    # Relationships
    company = db.relationship('Company', back_populates='names')
    
    def __repr__(self):
        return f'<CompanyName {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'name': self.name,
            'name_type': self.name_type,
            'is_primary': self.is_primary,
            'is_current': self.is_current,
            'language': self.language,
            'valid_from': self.valid_from.isoformat() if self.valid_from else None,
            'valid_to': self.valid_to.isoformat() if self.valid_to else None,
            'source': self.source,
        }