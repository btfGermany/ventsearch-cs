"""
OpenStreetMap / Overpass API Connector

Geospatial enrichment via OSM data.
"""

import json
import logging
from typing import Any, Dict, Generator, List, Optional

from app.sources.base import (
    BaseSourceConnector,
    SourceConfig,
    SourceRecord,
)


logger = logging.getLogger('company_intel.sources.osm')


class OSMConnector(BaseSourceConnector):
    """Connector for OpenStreetMap via Overpass API."""
    
    OVERPASS_URL = 'https://overpass-api.de/api/interpreter'
    
    def __init__(self, config: Optional[SourceConfig] = None):
        if config is None:
            config = SourceConfig(
                name='osm',
                enabled=True,
                base_url=self.OVERPASS_URL,
                rate_limit=1,
            )
        super().__init__(config)
    
    def fetch_all(self, limit: Optional[int] = None) -> Generator[SourceRecord, None, None]:
        """Fetch OSM POIs."""
        # OSM doesn't have a simple bulk API
        # This implementation focuses on local queries
        logger.info(f"Starting OSM POI fetch (limit={limit})")
        yield from []
    
    def query_area(self, city: str, country: str = 'DE', 
                  tags: Optional[List[str]] = None) -> Generator[SourceRecord, None, None]:
        """Query POIs in a specific area."""
        if tags is None:
            tags = ['company', 'office', 'shop', 'factory']
        
        # Build Overpass query
        overpass_query = self._build_area_query(city, country, tags)
        
        try:
            response = self._make_request(
                self.OVERPASS_URL,
                data=overpass_query
            )
            data = response.json()
            
            for element in data.get('elements', []):
                if element.get('type') == 'node':
                    yield self._parse_poi(element)
        except Exception as e:
            logger.error(f"Failed to query OSM: {e}")
            yield from []
    
    def query_bounding_box(self, north: float, south: float, east: float, west: float,
                    tags: Optional[List[str]] = None) -> Generator[SourceRecord, None, None]:
        """Query POIs in a bounding box."""
        if tags is None:
            tags = ['company']
        
        overpass_query = self._build_bbox_query(north, south, east, west, tags)
        
        try:
            response = self._make_request(
                self.OVERPASS_URL,
                data=overpass_query
            )
            data = response.json()
            
            for element in data.get('elements', []):
                if element.get('type') == 'node':
                    yield self._parse_poi(element)
        except Exception as e:
            logger.error(f"Failed to query OSM: {e}")
            yield from []
    
    def _build_area_query(self, city: str, country: str, tags: List[str]) -> str:
        """Build Overpass query for an area."""
        tag_filter = '|'.join([f'~"{tag}"~"."' for tag in tags])
        
        return json.dumps({
            'data': f'''
            [out:json][timeout:25];
            area["name"="{city}"]["admin_level"~"4|6"]({country});
            (
              node["{tag_filter}"](area);
              way["{tag_filter}"](area);
            );
            out center;
            '''
        })
    
    def _build_bbox_query(self, north: float, south: float, east: float, west: float,
                      tags: List[str]) -> str:
        """Build Overpass query for a bounding box."""
        tag_filter = '|'.join([f'~"{tag}"~"."' for tag in tags])
        
        return json.dumps({
            'data': f'''
            [out:json][timeout:25];
            (
              node["{tag_filter}"]({south},{west},{north},{east});
              way["{tag_filter}"]({south},{west},{north},{east});
            );
            out center;
            '''
        })
    
    def _parse_poi(self, element: Dict[str, Any]) -> SourceRecord:
        """Parse OSM element to POI record."""
        tags = element.get('tags', {})
        
        return SourceRecord(
            source='osm',
            source_id=str(element.get('id')),
            source_url=f"https://www.openstreetmap.org/{'node' if element.get('type') == 'node' else 'way'}/{element.get('id')}",
            source_data=element,
            
            names=[{
                'name': tags.get('name', tags.get('brand', '')),
                'name_type': 'trading_name',
                'is_primary': True,
                'is_current': True,
            }],
            
            addresses=[{
                'address_type': 'branch',
                'street': tags.get('addr:street'),
                'house_number': tags.get('addr:housenumber'),
                'postal_code': tags.get('addr:postcode'),
                'city': tags.get('addr:city'),
                'country': tags.get('addr:country', 'DE'),
                'latitude': element.get('lat'),
                'longitude': element.get('lon'),
            }],
            
            country=tags.get('addr:country', 'DE'),
            trust_score=0.50,
        )