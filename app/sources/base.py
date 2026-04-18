"""
Base source connector class for data providers.

All source connectors inherit from this base class and implement
the required methods for their specific data format and API.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Generator, List, Optional

import requests
from app.core.extensions import db
from app.models import Company, CompanyName, CompanyIdentifier, CompanyAddress, CompanySourceRecord


logger = logging.getLogger('company_intel.sources.base')


@dataclass
class SourceConfig:
    """Configuration for a source connector."""
    name: str
    enabled: bool = True
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    rate_limit: int = 10  # requests per second
    max_retries: int = 3
    timeout: int = 30


@dataclass
class SourceRecord:
    """Normalized record from a source."""
    company_id: Optional[str] = None
    source: str = ''
    source_id: str = ''
    source_url: str = ''
    source_data: Dict[str, Any] = None
    
    # Company fields
    names: List[Dict[str, Any]] = None
    identifiers: List[Dict[str, Any]] = None
    addresses: List[Dict[str, Any]] = None
    legal_form: Optional[str] = None
    status: Optional[str] = None
    registration_number: Optional[str] = None
    registration_court: Optional[str] = None
    registration_date: Optional[datetime] = None
    industry_code: Optional[str] = None
    country: Optional[str] = 'DE'
    lei: Optional[str] = None
    
    trust_score: float = 0.5


class BaseSourceConnector(ABC):
    """Base class for all source connectors."""
    
    def __init__(self, config: SourceConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CompanyIntelAggregator/1.0',
            'Accept': 'application/json',
        })
        if config.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {config.api_key}',
            })
    
    @property
    def name(self) -> str:
        return self.config.name
    
    @property
    def is_enabled(self) -> bool:
        return self.config.enabled
    
    @abstractmethod
    def fetch_all(self, limit: Optional[int] = None) -> Generator[SourceRecord, None, None]:
        """Fetch all records from the source."""
        pass
    
    @abstractmethod
    def fetch_one(self, source_id: str) -> Optional[SourceRecord]:
        """Fetch a single record by source ID."""
        pass
    
    def transform_to_company(self, record: SourceRecord) -> Dict[str, Any]:
        """Transform source record to company data structure."""
        # Base implementation - subclasses should override
        return {
            'canonical_name': record.names[0]['name'] if record.names else None,
            'legal_form': record.legal_form,
            'status': record.status or 'active',
            'country': record.country,
            'registration_number': record.registration_number,
            'registration_court': record.registration_court,
            'registration_date': record.registration_date,
            'industry_code': record.industry_code,
        }
    
    def save_record(self, record: SourceRecord) -> Optional[Company]:
        """Save a source record to the database."""
        if not record:
            return None
        
        # Check if company already exists from this source
        existing = CompanySourceRecord.query.filter_by(
            source=self.name,
            source_record_id=record.source_id
        ).first()
        
        if existing:
            # Update existing record
            company = db.session.get(Company, existing.company_id)
        else:
            # Create new company
            company = Company(
                uuid=self._generate_uuid(),
                canonical_name=record.names[0]['name'] if record.names else 'Unknown',
                legal_form=record.legal_form,
                status=record.status or 'active',
                country=record.country or 'DE',
                registration_number=record.registration_number,
                registration_court=record.registration_court,
                registration_date=record.registration_date,
                industry_code=record.industry_code,
                trust_score=record.trust_score,
            )
            db.session.add(company)
            db.session.flush()
        
        # Add names
        if record.names:
            for name_data in record.names:
                name = CompanyName(
                    company_id=company.id,
                    name=name_data['name'],
                    name_type=name_data.get('name_type', 'name'),
                    is_primary=name_data.get('is_primary', False),
                    is_current=name_data.get('is_current', True),
                    source=self.name,
                    source_id=record.source_id,
                    trust_score=record.trust_score,
                )
                db.session.add(name)
        
        # Add identifiers
        if record.identifiers:
            for id_data in record.identifiers:
                identifier = CompanyIdentifier(
                    company_id=company.id,
                    identifier_type=id_data['type'],
                    identifier_value=id_data['value'],
                    issuing_authority=id_data.get('issuing_authority'),
                    source=self.name,
                    source_id=record.source_id,
                    trust_score=record.trust_score,
                )
                db.session.add(identifier)
        
        # Add addresses
        if record.addresses:
            for addr_data in record.addresses:
                address = CompanyAddress(
                    company_id=company.id,
                    address_type=addr_data.get('address_type', 'registered'),
                    street=addr_data.get('street'),
                    house_number=addr_data.get('house_number'),
                    postal_code=addr_data.get('postal_code'),
                    city=addr_data.get('city'),
                    region=addr_data.get('region'),
                    country=addr_data.get('country', 'DE'),
                    is_primary=addr_data.get('is_primary', False),
                    latitude=addr_data.get('latitude'),
                    longitude=addr_data.get('longitude'),
                    source=self.name,
                    source_id=record.source_id,
                    trust_score=record.trust_score,
                )
                db.session.add(address)
        
        # Add source record
        source_record = CompanySourceRecord(
            company_id=company.id,
            source=record.source,
            source_record_id=record.source_id,
            source_url=record.source_url,
            source_data=record.source_data,
            trust_score=record.trust_score,
        )
        db.session.add(source_record)
        
        db.session.commit()
        return company
    
    def _generate_uuid(self) -> str:
        """Generate a UUID for a new company."""
        import uuid
        return str(uuid.uuid4())
    
    def _make_request(self, url: str, method: str = 'GET', **kwargs) -> requests.Response:
        """Make an HTTP request with retry logic."""
        from time import sleep
        from random import uniform
        
        for attempt in range(self.config.max_retries):
            try:
                response = self.session.request(
                    method,
                    url,
                    timeout=self.config.timeout,
                    **kwargs
                )
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < self.config.max_retries - 1:
                    # Exponential backoff
                    sleep(uniform(1, 2 ** attempt))
                else:
                    raise
    
    def close(self):
        """Clean up resources."""
        self.session.close()