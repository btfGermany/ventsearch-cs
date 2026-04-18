"""
Company Identifier model - Tracks various identifiers from different sources.
"""

from app.core.extensions import db
from app.models.mixins import ProvenanceMixin


class CompanyIdentifier(db.Model, ProvenanceMixin):
    """Company identifier from various sources."""
    
    __tablename__ = 'company_identifiers'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False, index=True)
    
    # Identifier type
    identifier_type = db.Column(db.String(50), nullable=False, index=True)
    # e.g., LEI, REGISTRATION_NUMBER, VAT, DUNS, ISIN, OEIK, HRB, HRA
    
    identifier_value = db.Column(db.String(255), nullable=False, index=True)
    
    # Issuing authority
    issuing_authority = db.Column(db.String(255))
    
    # Issue/expiry dates
    issued_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date)
    
    # Is primary for this type
    is_primary = db.Column(db.Boolean, default=False)
    
    # Relationships
    company = db.relationship('Company', back_populates='identifiers')
    
    __table_args__ = (
        db.Index('ix_company_identifier_type_value', 'identifier_type', 'identifier_value'),
    )
    
    def __repr__(self):
        return f'<CompanyIdentifier {self.identifier_type}:{self.identifier_value}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'identifier_type': self.identifier_type,
            'identifier_value': self.identifier_value,
            'issuing_authority': self.issuing_authority,
            'issued_date': self.issued_date.isoformat() if self.issued_date else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'is_primary': self.is_primary,
            'source': self.source,
        }