"""
OffeneRegister Source Connector

Primary German company register data source.
Provides company master data including registration info, legal form, addresses, etc.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Generator, List, Optional
from urllib.parse import urlencode

from app.sources.base import (
    BaseSourceConnector,
    SourceConfig,
    SourceRecord,
)


logger = logging.getLogger('company_intel.sources.offeneregister')


class OffeneRegisterConnector(BaseSourceConnector):
    """Connector for OffeneRegister.de API."""
    
    BASE_URL = 'https://api.offeneregister.de'
    
    def __init__(self, config: Optional[SourceConfig] = None):
        if config is None:
            config = SourceConfig(
                name='offeneregister',
                enabled=True,
                base_url=self.BASE_URL,
                rate_limit=5,
            )
        super().__init__(config)
    
    def fetch_all(self, limit: Optional[int] = None) -> Generator[SourceRecord, None, None]:
        """Fetch companies from OffeneRegister.
        
        Note: OffeneRegister API provides bulk dumps. This implementation
        simulates fetching from the API for demonstration.
        """
        # In production, this would:
        # 1. Download latest bulk dump or use streaming API
        # 2. Process in chunks for memory efficiency
        # 3. Handle pagination
        
        # For demonstration, yield empty generator
        # Real implementation would parse actual API data
        logger.info(f"Starting full fetch from OffeneRegister (limit={limit})")
        
        # Example of how records would be structured:
        # {
        #     "id": "HRB123456",
        #     "name": "Example GmbH",
        #     "legalForm": "Gesellschaft mit beschränkter Haftung",
        #     "registeredOffice": "Berlin",
        #     "address": "...",
        #     ...
        # }
        
        yield from []
    
    def fetch_one(self, source_id: str) -> Optional[SourceRecord]:
        """Fetch a single company by ID."""
        url = f"{self.config.base_url}/companies/{source_id}"
        
        try:
            response = self._make_request(url)
            data = response.json()
            return self._parse_company(data)
        except Exception as e:
            logger.error(f"Failed to fetch company {source_id}: {e}")
            return None
    
    def _parse_company(self, data: Dict[str, Any]) -> SourceRecord:
        """Parse company data from OffeneRegister."""
        # Extract names
        names = []
        primary_name = data.get('name', '')
        if primary_name:
            names.append({
                'name': primary_name,
                'name_type': 'legal_name',
                'is_primary': True,
                'is_current': True,
            })
        
        # Add trading name if different
        trading_name = data.get('commercialName')
        if trading_name and trading_name != primary_name:
            names.append({
                'name': trading_name,
                'name_type': 'trading_name',
                'is_primary': False,
                'is_current': True,
            })
        
        # Extract identifiers
        identifiers = []
        reg_number = data.get('id')
        if reg_number:
            identifiers.append({
                'type': 'HRB',
                'value': reg_number,
                'issuing_authority': data.get('registerCourt'),
            })
        
        # VR identifier
        vr_id = data.get('vrID')
        if vr_id:
            identifiers.append({
                'type': 'OEIK',
                'value': vr_id,
                'issuing_authority': 'OffeneRegister',
            })
        
        # Extract address
        addresses = []
        address = data.get('address', {})
        if address:
            addresses.append({
                'address_type': 'registered',
                'street': address.get('street'),
                'house_number': address.get('houseNumber'),
                'postal_code': address.get('postalCode'),
                'city': address.get('city'),
                'country': 'DE',
                'is_primary': True,
            })
        
        # Extract legal form
        legal_form_code = data.get('legalForm')
        legal_form = self._map_legal_form(legal_form_code)
        
        # Registration date
        reg_date = None
        if data.get('registrationDate'):
            try:
                reg_date = datetime.fromisoformat(data['registrationDate'].replace('Z', '+00:00'))
            except:
                pass
        
        # Status
        status = 'active'
        if data.get('liquidation'):
            status = 'liquidation'
        elif data.get('dissolved'):
            status = 'dissolved'
        
        return SourceRecord(
            source='offeneregister',
            source_id=data.get('id', ''),
            source_url=f"https://www.offeneregister.de/{data.get('id', '')}",
            source_data=data,
            
            names=names,
            identifiers=identifiers,
            addresses=addresses,
            
            legal_form=legal_form,
            status=status,
            registration_number=reg_number,
            registration_court=data.get('registerCourt'),
            registration_date=reg_date,
            
            country='DE',
            trust_score=0.95,
        )
    
    def _map_legal_form(self, code: Optional[str]) -> Optional[str]:
        """Map legal form code to full name."""
        if not code:
            return None
        
        mapping = {
            'GMBH': 'Gesellschaft mit beschränkter Haftung',
            'AG': 'Aktiengesellschaft',
            'KG': 'Kommanditgesellschaft',
            'OHG': 'Offene Handelsgesellschaft',
            'GmbHCoKG': 'GmbH & Co. KG',
            'UG': 'Unternehmergesellschaft',
            'SE': 'Europäische Gesellschaft',
            'SCE': 'Europäische Genossenschaft',
            'EV': 'eingetragener Verein',
            'PARTG': 'Partnerschaftsgesellschaft',
        }
        return mapping.get(code.upper(), code)