"""
OpenSearch Service - Wrapper for OpenSearch integration.
"""

import logging
from typing import Optional

from opensearchpy import OpenSearch
from flask import current_app


logger = logging.getLogger('company_intel.search')


class OpenSearchService:
    """OpenSearch service wrapper."""
    
    def __init__(self, app=None):
        self.app = app
        self.client = None
        
        if app and app.config.get('OPENSEARCH_URL'):
            self._init_client(app)
    
    def _init_client(self, app):
        """Initialize OpenSearch client."""
        url = app.config.get('OPENSEARCH_URL')
        user = app.config.get('OPENSEARCH_USER')
        password = app.config.get('OPENSEARCH_PASSWORD')
        
        try:
            if user and password:
                self.client = OpenSearch(
                    [url],
                    http_auth=(user, password),
                    use_ssl=True,
                )
            else:
                self.client = OpenSearch([url])
            
            logger.info(f"OpenSearch client initialized for {url}")
        except Exception as e:
            logger.error(f"Failed to initialize OpenSearch: {e}")
            self.client = None
    
    @property
    def is_available(self) -> bool:
        """Check if OpenSearch is available."""
        return self.client is not None
    
    def get_service(self):
        """Get search service with this client."""
        from app.services.search import SearchService
        return SearchService(client=self.client)