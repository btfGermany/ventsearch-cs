"""
Geo Point of Interest model - OSM POIs linked to companies.
"""

from app.core.extensions import db
from app.models.mixins import ProvenanceMixin, TimestampMixin


class GeoPointOfInterest(db.Model, ProvenanceMixin, TimestampMixin):
    """Geo POI from OSM linked to companies."""
    
    __tablename__ = 'geo_points_of_interest'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # OSM ID
    osm_id = db.Column(db.BigInteger, unique=True, index=True)
    osm_type = db.Column(db.String(10))  # node, way, relation
    
    # POI type
    poi_type = db.Column(db.String(50), index=True)
    # e.g., office, shop, amenity, company
    
    # Name
    name = db.Column(db.String(500))
    
    # Alternative names
    alt_names = db.Column(db.JSON)
    
    # Category
    category = db.Column(db.String(50))
    subcategory = db.Column(db.String(50))
    
    # Address
    street = db.Column(db.String(500))
    house_number = db.Column(db.String(20))
    postal_code = db.Column(db.String(20), index=True)
    city = db.Column(db.String(255), index=True)
    country = db.Column(db.String(2), default='DE')
    
    # Location
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    
    # Additional tags
    tags = db.Column(db.JSON)
    
    # Linked companies
    linked_companies = db.relationship('GeoMatch', back_populates='poi', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<GeoPointOfInterest {self.osm_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'osm_id': self.osm_id,
            'poi_type': self.poi_type,
            'name': self.name,
            'city': self.city,
            'postal_code': self.postal_code,
            'latitude': self.latitude,
            'longitude': self.longitude,
        }


class GeoMatch(db.Model, ProvenanceMixin):
    """Match between company and geo POI."""
    
    __tablename__ = 'geo_matches'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False, index=True)
    poi_id = db.Column(db.Integer, db.ForeignKey('geo_points_of_interest.id'), nullable=False, index=True)
    
    # Match score
    match_score = db.Column(db.Float, nullable=False)
    
    # Match type
    match_type = db.Column(db.String(20))
    # e.g., ADDRESS_MATCH, NAME_PROXIMITY, EXACT
    
    # Review status
    review_status = db.Column(db.String(20), default='pending')
    # pending, confirmed, rejected
    
    # Relationships
    company = db.relationship('Company')
    poi = db.relationship('GeoPointOfInterest', back_populates='linked_companies')
    
    def __repr__(self):
        return f'<GeoMatch {self.match_score}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'poi_id': self.poi_id,
            'match_score': self.match_score,
            'match_type': self.match_type,
            'review_status': self.review_status,
        }