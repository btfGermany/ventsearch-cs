"""
Company model - Core entity for the knowledge graph.

Represents a company with multiple names, identifiers, addresses, and statuses.
"""

from datetime import datetime
from app.core.extensions import db
from app.models.mixins import ProvenanceMixin, TimestampMixin


class Company(db.Model, ProvenanceMixin, TimestampMixin):
    """Company entity representing a business organization."""
    
    __tablename__ = 'companies'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, index=True)
    
    # Status fields
    status = db.Column(
        db.String(50),
        default='active',
        index=True
    )  # active, inactive, liquidation, dissolved, merged
    
    # Primary data from highest trust source
    registration_number = db.Column(db.String(100), index=True)
    registration_court = db.Column(db.String(255))
    registration_date = db.Column(db.Date)
    
    # Legal form
    legal_form = db.Column(db.String(100), index=True)
    
    # Industry classification
    industry_code = db.Column(db.String(20), index=True)
    industry_description = db.Column(db.String(500))
    
    # Country of registration
    country = db.Column(db.String(2), default='DE', index=True)
    
    # Primary address (denormalized for performance)
    primary_city = db.Column(db.String(255), index=True)
    primary_postal_code = db.Column(db.String(20), index=True)
    primary_country = db.Column(db.String(2), default='DE')
    
    # LEI reference
    lei = db.Column(db.String(20), unique=True, index=True)
    
    # Entity resolution
    canonical_name = db.Column(db.String(500), index=True)
    name_norm = db.Column(db.String(500), index=True)  # normalized for matching
    
    # Confidence
    confidence_score = db.Column(db.Float, default=0.0)
    
    # Flags
    is_verified = db.Column(db.Boolean, default=False)
    is_merged = db.Column(db.Boolean, default=False)
    merged_into_id = db.Column(db.Integer, db.ForeignKey('companies.id'), index=True)
    
    # Relationships
    merged_into = db.relationship('Company', remote_side=[id], foreign_keys=[merged_into_id])
    
    names = db.relationship('CompanyName', back_populates='company', cascade='all, delete-orphan')
    identifiers = db.relationship('CompanyIdentifier', back_populates='company', cascade='all, delete-orphan')
    addresses = db.relationship('CompanyAddress', back_populates='company', cascade='all, delete-orphan')
    source_records = db.relationship('CompanySourceRecord', back_populates='company', cascade='all, delete-orphan')
    events = db.relationship('CompanyEvent', back_populates='company', cascade='all, delete-orphan')
    industries = db.relationship('CompanyIndustry', back_populates='company', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Company {self.uuid}: {self.canonical_name}>'
    
    @property
    def primary_name(self):
        """Get the primary/current company name."""
        for name in self.names:
            if name.is_primary and name.is_current:
                return name.name
        return self.canonical_name
    
    def to_dict(self, include_relations: bool = False):
        """Convert to dictionary."""
        result = {
            'id': self.id,
            'uuid': self.uuid,
            'status': self.status,
            'canonical_name': self.canonical_name,
            'legal_form': self.legal_form,
            'country': self.country,
            'registration_number': self.registration_number,
            'registration_court': self.registration_court,
            'registration_date': self.registration_date.isoformat() if self.registration_date else None,
            'lei': self.lei,
            'industry_code': self.industry_code,
            'confidence_score': self.confidence_score,
            'is_verified': self.is_verified,
            'primary_city': self.primary_city,
            'primary_postal_code': self.primary_postal_code,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_relations:
            result['names'] = [n.to_dict() for n in self.names]
            result['identifiers'] = [i.to_dict() for i in self.identifiers]
            result['addresses'] = [a.to_dict() for a in self.addresses]
            result['source_records'] = [s.to_dict() for s in self.source_records]
        
        return result