"""
Company Industry model - Industry classifications.
"""

from app.core.extensions import db
from app.models.mixins import ProvenanceMixin


class CompanyIndustry(db.Model, ProvenanceMixin):
    """Company industry classification."""
    
    __tablename__ = 'company_industries'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False, index=True)
    
    # Classification system
    classification_system = db.Column(db.String(20), nullable=False)
    # e.g., NACE, WZ2008, ISIC, NAICS
    
    # Industry code
    industry_code = db.Column(db.String(20), nullable=False, index=True)
    
    # Description
    description = db.Column(db.String(500))
    
    # Is primary
    is_primary = db.Column(db.Boolean, default=False)
    
    # Relationships
    company = db.relationship('Company', back_populates='industries')
    
    def __repr__(self):
        return f'<CompanyIndustry {self.classification_system}:{self.industry_code}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'classification_system': self.classification_system,
            'industry_code': self.industry_code,
            'description': self.description,
            'is_primary': self.is_primary,
        }