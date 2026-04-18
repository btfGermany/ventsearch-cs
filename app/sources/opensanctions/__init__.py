"""
OpenSanctions Source Connector

Sanctions and PEP screening data.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Generator, List, Optional

from app.sources.base import (
    BaseSourceConnector,
    SourceConfig,
    SourceRecord,
)


logger = logging.getLogger('company_intel.sources.opensanctions')


class OpenSanctionsConnector(BaseSourceConnector):
    """Connector for OpenSanctions data."""
    
    BASE_URL = 'https://www.opensanctions.org'
    
    def __init__(self, config: Optional[SourceConfig] = None):
        if config is None:
            config = SourceConfig(
                name='opensanctions',
                enabled=True,
                base_url=self.BASE_URL,
                rate_limit=10,
            )
        super().__init__(config)
    
    def fetch_all(self, limit: Optional[int] = None) -> Generator[SourceRecord, None, None]:
        """Fetch sanctions entities."""
        logger.info(f"Starting fetch from OpenSanctions (limit={limit})")
        
        # OpenSanctions provides dumps
        yield from []
    
    def fetch_one(self, source_id: str) -> Optional[SourceRecord]:
        """Fetch a single entity."""
        url = f"{self.config.base_url}/api/v1/{source_id}"
        
        try:
            response = self._make_request(url)
            data = response.json()
            return self._parse_entity(data)
        except Exception as e:
            logger.error(f"Failed to fetch entity {source_id}: {e}")
            return None
    
    def search(self, query: str) -> Generator[SourceRecord, None, None]:
        """Search sanctions data."""
        url = f"{self.config.base_url}/api/v1/search"
        params = {'q': query}
        
        try:
            response = self._make_request(url, params=params)
            data = response.json()
            for result in data.get('results', []):
                yield self._parse_entity(result)
        except Exception as e:
            logger.error(f"Search failed: {e}")
            yield from []
    
    def _parse_entity(self, data: Dict[str, Any]) -> SourceRecord:
        """Parse sanctions entity data."""
        return SourceRecord(
            source='opensanctions',
            source_id=data.get('id', ''),
            source_url=f"{self.config.base_url}/entity/{data.get('id', '')}",
            source_data=data,
            names=[{
                'name': data.get('caption', ''),
                'name_type': 'name',
                'is_primary': True,
                'is_current': True,
            }],
            aliases=data.get('aliases', []),
            trust_score=0.85,
        )