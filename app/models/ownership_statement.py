"""
Ownership Statement model - BODS-style ownership statements.
"""

from app.core.extensions import db
from app.models.mixins import ProvenanceMixin, TimestampMixin


class OwnershipStatement(db.Model, ProvenanceMixin, TimestampMixin):
    """Ownership statement following BODS specification."""
    
    __tablename__ = 'ownership_statements'
    
    id = db.Column(db.Integer, primary_key=True)
    statement_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    
    # Statement type
    statement_type = db.Column(db.String(50), nullable=False)
    # e.g., ownershipOrControl, personEntity, entity
    
    # Publication info
    publication_date = db.Column(db.Date)
    publication_platform = db.Column(db.String(255))
    publication_url = db.Column(db.String(2000))
    
    # Source type
    source_type = db.Column(db.String(50))  # register, annualReport, leaked, etc.
    
    # Interested party
    interested_party_name = db.Column(db.String(500))
    interested_party_country = db.Column(db.String(2))
    
    # Interested party type (person or entity)
    interested_party_type = db.Column(db.String(20))
    
    # interested party identifiers
    interested_party_identifier_type = db.Column(db.String(50))
    interested_party_identifier_value = db.Column(db.String(255))
    
    # Subject
    subject_name = db.Column(db.String(500))
    subject_lei = db.Column(db.String(20))
    subject_country = db.Column(db.String(2))
    
    # Interest details
    interest_type = db.Column(db.String(50))
    interest_level = db.Column(db.String(20))  # direct, indirect, ultimate
    
    # Percentage
    percentage_shares = db.Column(db.Float)  # ownership percentage
    percentage_voting = db.Column(db.Float)
    
    # Raw statement
    raw_statement = db.Column(db.JSON)
    
    # Status
    is_verified = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<OwnershipStatement {self.statement_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'statement_id': self.statement_id,
            'statement_type': self.statement_type,
            'interested_party_name': self.interested_party_name,
            'interested_party_type': self.interested_party_type,
            'subject_name': self.subject_name,
            'interest_type': self.interest_type,
            'interest_level': self.interest_level,
            'percentage_shares': self.percentage_shares,
        }