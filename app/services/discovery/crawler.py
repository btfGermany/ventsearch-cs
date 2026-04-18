"""
Discovery Crawler Service

Crawls CKAN endpoints to discover datasets.
"""

import logging
from typing import Dict, Generator, List, Optional

from app.core.extensions import db
from app.models import DatasetCatalogItem, DatasetResource
from app.sources.ckan import CKANConnector


logger = logging.getLogger('company_intel.discovery')


class DiscoveryCrawler:
    """CKAN dataset discovery crawler."""
    
    # Relevance keywords for classification
    COMPANY_RELEVANT_KEYWORDS = [
        'unternehmen', 'company', 'handelsregister', 'companies',
        'firmen', 'business', 'gmbh', 'ag', 'wirtschaft',
    ]
    
    INDIRECTLY_RELEVANT_KEYWORDS = [
        'adresse', 'address', 'geo', 'location', 'region',
        'behoerde', 'authority', 'public', 'government',
    ]
    
    def __init__(self, ckan_url: str = 'https://www.govdata.de'):
        self.connector = CKANConnector(ckan_url)
    
    def crawl(self, limit: int = 1000) -> int:
        """Crawl datasets and save to catalog."""
        count = 0
        
        for record in self.connector.search(''):
            dataset = self._parse_dataset(record.source_data)
            
            # Determine relevance
            dataset.relevance = self._classify_relevance(
                record.source_data.get('title', ''),
                record.source_data.get('tags', []),
            )
            
            db.session.add(dataset)
            count += 1
            
            if count >= limit:
                break
        
        db.session.commit()
        return count
    
    def _parse_dataset(self, data: Dict) -> DatasetCatalogItem:
        """Parse dataset metadata."""
        dataset = DatasetCatalogItem(
            dataset_id=data.get('id', ''),
            title=data.get('title', ''),
            description=data.get('notes', ''),
            
            publisher_name=data.get('author'),
            publisher_url=data.get('author_url'),
            
            tags=data.get('tags', []),
            
            license=data.get('license_id'),
            update_frequency=data.get('frequency'),
            
            language=data.get('language'),
            formats=[r.get('format') for r in data.get('resources', []) if r.get('format')],
            
            resources_count=len(data.get('resources', [])),
            
            source='ckan',
            trust_score=0.40,
        )
        
        # Add resources
        for resource in data.get('resources', []):
            res = DatasetResource(
                resource_id=resource.get('id'),
                name=resource.get('name', ''),
                description=resource.get('description', ''),
                url=resource.get('url'),
                format=resource.get('format'),
                mime_type=resource.get('mimetype'),
                size=resource.get('size'),
                source='ckan',
                trust_score=0.40,
            )
            dataset.resources.append(res)
        
        return dataset
    
    def _classify_relevance(self, title: str, tags: List[str]) -> str:
        """Classify dataset relevance."""
        search_text = f"{title} {' '.join(tags)}".lower()
        
        # Check directly relevant
        for keyword in self.COMPANY_RELEVANT_KEYWORDS:
            if keyword in search_text:
                return 'directly_relevant'
        
        # Check indirectly relevant
        for keyword in self.INDIRECTLY_RELEVANT_KEYWORDS:
            if keyword in search_text:
                return 'indirectly_relevant'
        
        return 'unknown'