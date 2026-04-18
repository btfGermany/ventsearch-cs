"""
GovData CKAN API Source Connector

Dataset discovery via CKAN API.
"""

import logging
from typing import Any, Dict, Generator, Optional

from app.sources.base import (
    BaseSourceConnector,
    SourceConfig,
    SourceRecord,
)


logger = logging.getLogger('company_intel.sources.ckan')


class CKANConnector(BaseSourceConnector):
    """Connector for CKAN API endpoints."""
    
    def __init__(self, base_url: str, config: Optional[SourceConfig] = None):
        if config is None:
            config = SourceConfig(
                name='ckan',
                enabled=True,
                base_url=base_url,
                rate_limit=10,
            )
        super().__init__(config)
    
    def fetch_all(self, limit: Optional[int] = None) -> Generator[SourceRecord, None, None]:
        """Fetch all packages from CKAN."""
        offset = 0
        page_size = 100
        
        while True:
            url = f"{self.config.base_url}/api/3/action/package_list"
            params = {'limit': page_size, 'offset': offset}
            
            try:
                response = self._make_request(url, params=params)
                data = response.json()
                
                if data.get('success'):
                    results = data.get('result', [])
                    if not results:
                        break
                    
                    for pkg in results:
                        yield SourceRecord(
                            source='ckan',
                            source_id=pkg.get('id', ''),
                            source_data=pkg,
                            trust_score=0.40,
                        )
                    
                    offset += page_size
                    if limit and offset >= limit:
                        break
                else:
                    break
            except Exception as e:
                logger.error(f"Failed to fetch packages: {e}")
                break
    
    def search(self, query: str) -> Generator[SourceRecord, None, None]:
        """Search CKAN packages."""
        url = f"{self.config.base_url}/api/3/action/package_search"
        params = {'q': query}
        
        try:
            response = self._make_request(url, params=params)
            data = response.json()
            
            if data.get('success'):
                results = data.get('result', {}).get('results', [])
                for pkg in results:
                    yield SourceRecord(
                        source='ckan',
                        source_id=pkg.get('id', ''),
                        source_data=pkg,
                        trust_score=0.40,
                    )
        except Exception as e:
            logger.error(f"Search failed: {e}")
            yield from []