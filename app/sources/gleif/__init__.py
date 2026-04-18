"""
GLEIF LEI API Source Connector

Legal Entity Identifier data and relationships.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Generator, List, Optional

from app.sources.base import (
    BaseSourceConnector,
    SourceConfig,
    SourceRecord,
)


logger = logging.getLogger('company_intel.sources.gleif')


class GLEIFConnector(BaseSourceConnector):
    """Connector for GLEIF LEI API."""
    
    BASE_URL = 'https://leilookup.gleif.org/api/v1'
    
    def __init__(self, config: Optional[SourceConfig] = None):
        if config is None:
            config = SourceConfig(
                name='gleif',
                enabled=True,
                base_url=self.BASE_URL,
                rate_limit=10,
            )
        super().__init__(config)
    
    def fetch_all(self, limit: Optional[int] = None) -> Generator[SourceRecord, None, None]:
        """Fetch LEI records."""
        logger.info(f"Starting fetch from GLEIF (limit={limit})")
        yield from []
    
    def fetch_one(self, source_id: str) -> Optional[SourceRecord]:
        """Fetch a single LEI record."""
        url = f"{self.config.base_url}/lei/{source_id}.json"
        
        try:
            response = self._make_request(url)
            data = response.json()
            return self._parse_company(data)
        except Exception as e:
            logger.error(f"Failed to fetch LEI {source_id}: {e}")
            return None
    
    def search_by_name(self, name: str, limit: int = 10) -> List[str]:
        """Search for LEI by entity name."""
        url = f"{self.config.base_url}/search"
        params = {'q': name, 'limit': limit}
        
        try:
            response = self._make_request(url, params=params)
            data = response.json()
            return [match.get('LEI') for match in data.get('matches', [])]
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_relationships(self, lei: str) -> List[Dict[str, Any]]:
        """Get relationships for a LEI."""
        url = f"{self.config.base_url}/relationships/{lei}"
        
        try:
            response = self._make_request(url)
            data = response.json()
            return data.get('relationships', [])
        except Exception as e:
            logger.error(f"Failed to fetch relationships for {lei}: {e}")
            return []
    
    def _parse_company(self, data: Dict[str, Any]) -> SourceRecord:
        """Parse LEI data."""
        entity = data.get('entity', {})
        
        names = [{
            'name': entity.get('legalName', {}).get('name', ''),
            'name_type': 'legal_name',
            'is_primary': True,
            'is_current': True,
        }]
        
        identifiers = [{
            'type': 'LEI',
            'value': entity.get('LEI'),
            'issuing_authority': 'GLEIF',
        }]
        
        # Registered address
        reg_addr = entity.get('registeredAddress', {})
        if reg_addr:
            addresses = [{
                'address_type': 'registered',
                'street': reg_addr.get('addressLines', [{}])[0].get('addressLine', {}).get('value'),
                'city': reg_addr.get('city'),
                'postal_code': reg_addr.get('postalCode'),
                'country': reg_addr.get('country'),
                'is_primary': True,
            }]
        else:
            addresses = []
        
        # Legal form
        legal_form = entity.get('legalForm', {}).get('label')
        
        # Status
        status = 'active'
        if entity.get('entityStatus') == 'INACTIVE':
            status = 'inactive'
        
        return SourceRecord(
            source='gleif',
            source_id=entity.get('LEI', ''),
            source_url=f"https://search.gleif.org/entity/{entity.get('LEI', '')}",
            source_data=entity,
            
            names=names,
            identifiers=identifiers,
            addresses=addresses,
            
            legal_form=legal_form,
            status=status,
            lei=entity.get('LEI'),  # Note: This field name is unusual but kept for matching
            country=entity.get('jurisdiction'),
            trust_score=0.90,
        )