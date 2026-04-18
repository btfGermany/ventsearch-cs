"""
Company Address model - Tracks all addresses of a company.
"""

from app.core.extensions import db
from app.models.mixins import ProvenanceMixin


class CompanyAddress(db.Model, ProvenanceMixin):
    """Company address for headquarters, branches, registered office, etc."""
    
    __tablename__ = 'company_addresses'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False, index=True)
    
    # Address type
    address_type = db.Column(db.String(20), default='registered')  # registered, postal, branch, headquarters
    
    # Street address
    street = db.Column(db.String(500))
    house_number = db.Column(db.String(20))
    address_line_1 = db.Column(db.String(500))
    address_line_2 = db.Column(db.String(500))
    
    # Postal
    postal_code = db.Column(db.String(20), index=True)
    city = db.Column(db.String(255), index=True)
    district = db.Column(db.String(255))
    region = db.Column(db.String(255))  # Bundesland for Germany
    
    # Country
    country = db.Column(db.String(2), default='DE', index=True)
    country_text = db.Column(db.String(255))
    
    # PO Box
    po_box = db.Column(db.String(20))
    po_box_postal_code = db.Column(db.String(20))
    
    # Care-of
    care_of = db.Column(db.String(255))
    
    # Validity
    is_primary = db.Column(db.Boolean, default=False)
    is_current = db.Column(db.Boolean, default=True)
    
    valid_from = db.Column(db.Date)
    valid_to = db.Column(db.Date)
    
    # Geo coordinates
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    
    # Relationships
    company = db.relationship('Company', back_populates='addresses')
    
    def __repr__(self):
        return f'<CompanyAddress {self.postal_code} {self.city}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'address_type': self.address_type,
            'street': self.street,
            'house_number': self.house_number,
            'postal_code': self.postal_code,
            'city': self.city,
            'region': self.region,
            'country': self.country,
            'is_primary': self.is_primary,
            'is_current': self.is_current,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'source': self.source,
        }