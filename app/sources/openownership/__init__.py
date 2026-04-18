"""
OpenOwnership Source Connector

Beneficial ownership data following BODS specification.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Generator, List, Optional
import xml.etree.ElementTree as ET

from app.sources.base import (
    BaseSourceConnector,
    SourceConfig,
    SourceRecord,
)


logger = logging.getLogger('company_intel.sources.openownership')


class OpenOwnershipConnector(BaseSourceConnector):
    """Connector for OpenOwnership data."""
    
    BASE_URL = 'https://www.openownership.org'
    
    def __init__(self, config: Optional[SourceConfig] = None):
        if config is None:
            config = SourceConfig(
                name='openownership',
                enabled=True,
                base_url=self.BASE_URL,
                rate_limit=5,
            )
        super().__init__(config)
    
    def fetch_all(self, limit: Optional[int] = None) -> Generator[SourceRecord, None, None]:
        """Fetch ownership statements."""
        logger.info(f"Starting fetch from OpenOwnership (limit={limit})")
        
        # OpenOwnership provides data dumps
        yield from []
    
    def fetch_one(self, source_id: str) -> Optional[SourceRecord]:
        """Fetch a single statement."""
        url = f"{self.config.base_url}/statements/{source_id}"
        
        try:
            response = self._make_request(url)
            data = response.json()
            return self._parse_statement(data)
        except Exception as e:
            logger.error(f"Failed to fetch statement {source_id}: {e}")
            return None
    
    def parse_bods(self, xml_content: str) -> List[Dict[str, Any]]:
        """Parse BODS XML content."""
        statements = []
        
        try:
            root = ET.fromstring(xml_content)
            for stmt in root.findall('.//statement'):
                statement = {
                    'statementID': stmt.get('statementID'),
                    'statementType': stmt.get('statementType'),
                    'publicationDate': stmt.get('publicationDate'),
                    'subject': self._parse_entity(stmt.find('subject')),
                    'interestedParty': self._parse_entity(stmt.find('interestedParty')),
                    'interests': self._parse_interests(stmt.find('interests')),
                }
                statements.append(statement)
        except ET.ParseError as e:
            logger.error(f"Failed to parse BODS: {e}")
        
        return statements
    
    def _parse_entity(self, element) -> Optional[Dict[str, Any]]:
        """Parse entity element."""
        if element is None:
            return None
        
        entity = {
            'type': element.get('type'),
            'name': element.findtext('name'),
            'country': element.findtext('country'),
        }
        
        # Identifiers
        id_elem = element.find('identifiers')
        if id_elem is not None:
            entity['identifiers'] = [
                {
                    'type': id.get('type'),
                    'value': id.text,
                }
                for id in id_elem.findall('identifier')
            ]
        
        return entity
    
    def _parse_interests(self, element) -> List[Dict[str, Any]]:
        """Parse interests element."""
        interests = []
        
        if element is None:
            return interests
        
        for interest in element.findall('interest'):
            interests.append({
                'type': interest.get('type'),
                'share': interest.findtext('share'),
                'direct': interest.get('direct') == 'true',
            })
        
        return interests
    
    def _parse_statement(self, data: Dict[str, Any]) -> SourceRecord:
        """Parse statement data."""
        return SourceRecord(
            source='openownership',
            source_id=data.get('statementID', ''),
            source_url=f"{self.config.base_url}/statement/{data.get('statementID', '')}",
            source_data=data,
            trust_score=0.80,
        )