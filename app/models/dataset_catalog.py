"""
Dataset Catalog model - Discovery catalog for datasets from CKAN.
"""

from app.core.extensions import db
from app.models.mixins import ProvenanceMixin, TimestampMixin


class DatasetCatalogItem(db.Model, ProvenanceMixin, TimestampMixin):
    """Dataset catalog item from Data.gov or CKAN."""
    
    __tablename__ = 'dataset_catalog_items'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Dataset ID from source
    dataset_id = db.Column(db.String(255), nullable=False, index=True)
    
    # Title
    title = db.Column(db.String(1000), nullable=False)
    
    # Description
    description = db.Column(db.Text)
    
    # Publisher
    publisher_name = db.Column(db.String(500))
    publisher_url = db.Column(db.String(2000))
    
    # Category relevance
    relevance = db.Column(db.String(20), default='unknown')
    # not_relevant, indirectly_relevant, directly_relevant
    
    # Categories/tags
    tags = db.Column(db.JSON)
    
    # License
    license = db.Column(db.String(255))
    
    # Update frequency
    update_frequency = db.Column(db.String(50))
    
    # Temporal coverage
    temporal_start = db.Column(db.Date)
    temporal_end = db.Column(db.Date)
    
    # Spatial
    spatial_coverage = db.Column(db.String(255))
    
    # Language
    language = db.Column(db.String(3))
    
    # Format
    formats = db.Column(db.JSON)
    
    # Resources count
    resources_count = db.Column(db.Integer, default=0)
    
    # Relationships
    resources = db.relationship('DatasetResource', back_populates='dataset', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<DatasetCatalogItem {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'dataset_id': self.dataset_id,
            'title': self.title,
            'publisher_name': self.publisher_name,
            'relevance': self.relevance,
            'tags': self.tags,
            'formats': self.formats,
        }


class DatasetResource(db.Model, ProvenanceMixin):
    """Individual resource within a dataset."""
    
    __tablename__ = 'dataset_resources'
    
    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset_catalog_items.id'), nullable=False, index=True)
    
    # Resource ID from source
    resource_id = db.Column(db.String(255))
    
    # Name
    name = db.Column(db.String(500), nullable=False)
    
    # Description
    description = db.Column(db.Text)
    
    # URL
    url = db.Column(db.String(2000), nullable=False)
    
    # Format
    format = db.Column(db.String(20))
    mime_type = db.Column(db.String(50))
    
    # Size
    size = db.Column(db.BigInteger)
    
    # Hash
    hash = db.Column(db.String(255))
    hash_algorithm = db.Column(db.String(20))
    
    # Relationships
    dataset = db.relationship('DatasetCatalogItem', back_populates='resources')
    
    def __repr__(self):
        return f'<DatasetResource {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'dataset_id': self.dataset_id,
            'name': self.name,
            'url': self.url,
            'format': self.format,
            'size': self.size,
        }