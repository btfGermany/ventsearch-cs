"""
OpenCorporates Source Connector

Global company enrichment and cross-jurisdiction matching.
"""

import logging
from typing import Any, Dict, Generator, Optional

from app.sources.base import (
    BaseSourceConnector,
    SourceConfig,
    SourceRecord,
)


logger = logging.getLogger('company_intel.sources.opencorporates')


class OpenCorporatesConnector(BaseSourceConnector):
    """Connector for OpenCorporates API."""
    
    BASE_URL = 'https://api.opencorporates.com/v0.4'
    
    def __init__(self, config: Optional[SourceConfig] = None):
        if config is None:
            config = SourceConfig(
                name='opencorporates',
                enabled=True,
                base_url=self.BASE_URL,
                rate_limit=10,
                api_key=None,  # Set via environment
            )
        super().__init__(config)
    
    def fetch_all(self, limit: Optional[int] = None) -> Generator[SourceRecord, None, None]:
        """Fetch companies from OpenCorporates."""
        logger.info(f"Starting fetch from OpenCorporates (limit={limit})")
        
        # OpenCorporates requires API key for bulk access
        # This yields empty for demonstration
        yield from []
    
    def fetch_one(self, source_id: str) -> Optional[SourceRecord]:
        """Fetch a single company by jurisdiction and company ID."""
        # Format: jurisdiction/company_number
        url = f"{self.config.base_url}/companies/{source_id}"
        
        try:
            response = self._make_request(url)
            data = response.json()
            return self._parse_company(data)
        except Exception as e:
            logger.error(f"Failed to fetch company {source_id}: {e}")
            return None
    
    def search(self, query: str, jurisdiction: str = 'de') -> Generator[SourceRecord, None, None]:
        """Search companies."""
        url = f"{self.config.base_url}/companies"
        params = {'q': query, 'jurisdiction': jurisdiction}
        
        try:
            response = self._make_request(url, params=params)
            data = response.json()
            for company in data.get('results', []):
                yield self._parse_company(company)
        except Exception as e:
            logger.error(f"Search failed: {e}")
            yield from []
    
    def _parse_company(self, data: Dict[str, Any]) -> SourceRecord:
        """Parse company data from OpenCorporates."""
        company = data.get('company', {})
        
        # Extract basic info
        name = company.get('name', '')
        jurisdiction = company.get('jurisdiction_code', '')
        
        identifiers = [{
            'type': 'OPENCORPORATES',
            'value': company.get('company_number'),
            'issuing_authority': jurisdiction,
        }]
        
        # Additional IDs from OpenCorporates
        for id_type in ['ticker', 'isin']:
            if company.get(id_type):
                identifiers.append({
                    'type': id_type.upper(),
                    'value': company.get(id_type),
                })
        
        # Address
        address_data = company.get('registered_address', {})
        addresses = []
        if address_data:
            addresses.append({
                'address_type': 'registered',
                'street': address_data.get('address'),
                'postal_code': address_data.get('postal_code'),
                'city': address_data.get('locality'),
                'country': jurisdiction.upper(),
                'is_primary': True,
            })
        
        return SourceRecord(
            source='opencorporates',
            source_id=f"{jurisdiction}/{company.get('company_number', '')}",
            source_url=company.get('opencorporates_url'),
            source_data=company,
            
            names=[{
                'name': name,
                'name_type': 'name',
                'is_primary': True,
                'is_current': True,
            }],
            identifiers=identifiers,
            addresses=addresses,
            
            country=jurisdiction.upper(),
            trust_score=0.75,
        )