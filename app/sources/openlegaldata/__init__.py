"""
OpenLegalData Source Connector

Legal context data - court decisions, laws, regulations.
"""

import logging
from typing import Any, Dict, Generator, Optional

from app.sources.base import (
    BaseSourceConnector,
    SourceConfig,
    SourceRecord,
)


logger = logging.getLogger('company_intel.sources.openlegaldata')


class OpenLegalDataConnector(BaseSourceConnector):
    """Connector for OpenLegalData."""
    
    BASE_URL = 'https://openlegaldata.io'
    
    def __init__(self, config: Optional[SourceConfig] = None):
        if config is None:
            config = SourceConfig(
                name='openlegaldata',
                enabled=True,
                base_url=self.BASE_URL,
                rate_limit=5,
            )
        super().__init__(config)
    
    def fetch_all(self, limit: Optional[int] = None) -> Generator[SourceRecord, None, None]:
        """Fetch legal documents."""
        logger.info(f"Starting fetch from OpenLegalData (limit={limit})")
        yield from []
    
    def fetch_one(self, source_id: str) -> Optional[SourceRecord]:
        """Fetch a single legal document."""
        url = f"{self.config.base_url}/docs/{source_id}"
        
        try:
            response = self._make_request(url)
            data = response.json()
            return self._parse_document(data)
        except Exception as e:
            logger.error(f"Failed to fetch document {source_id}: {e}")
            return None
    
    def search_cases(self, query: str, court: Optional[str] = None) -> Generator[SourceRecord, None, None]:
        """Search court decisions."""
        url = f"{self.config.base_url}/cases/search"
        params = {'q': query}
        if court:
            params['court'] = court
        
        try:
            response = self._make_request(url, params=params)
            data = response.json()
            for case in data.get('results', []):
                yield self._parse_document(case)
        except Exception as e:
            logger.error(f"Search failed: {e}")
            yield from []
    
    def _parse_document(self, data: Dict[str, Any]) -> SourceRecord:
        """Parse legal document."""
        return SourceRecord(
            source='openlegaldata',
            source_id=data.get('id', ''),
            source_url=data.get('url'),
            source_data=data,
            trust_score=0.60,
        )