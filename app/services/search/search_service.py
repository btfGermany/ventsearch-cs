"""
Search Service - Company search with OpenSearch.

Provides full-text search and filtering for companies.
"""

import logging
from typing import Any, Dict, List, Optional

from opensearchpy import OpenSearch
from flask import current_app


logger = logging.getLogger('company_intel.services.search')


class SearchService:
    """Company search service with OpenSearch."""
    
    def __init__(self, client: Optional[OpenSearch] = None, index: str = 'companies'):
        self.client = client
        self.index = index
    
    @property
    def is_available(self) -> bool:
        """Check if OpenSearch is available."""
        return self.client is not None
    
    def search(self, query: str = None, filters: Optional[Dict[str, Any]] = None,
               page: int = 1, page_size: int = 25,
               sort: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """Search companies with filters."""
        if not self.is_available:
            return {
                'total': 0,
                'companies': [],
                'page': page,
                'page_size': page_size,
            }
        
        # Build query
        search_query = self._build_query(query, filters)
        
        # Execute search
        try:
            response = self.client.search(
                body=search_query,
                index=self.index,
                from_=(page - 1) * page_size,
                size=page_size,
            )
            
            return self._parse_results(response, page, page_size)
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {
                'total': 0,
                'companies': [],
                'error': str(e),
            }
    
    def _build_query(self, query: Optional[str], 
                   filters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Build OpenSearch query."""
        must_clauses = []
        filter_clauses = []
        
        # Full-text search
        if query:
            must_clauses.append({
                'multi_match': {
                    'query': query,
                    'fields': ['canonical_name^3', 'names.name', 'identifiers.value'],
                    'type': 'best_fields',
                    'fuzziness': 'AUTO',
                }
            })
        
        # Filters
        if filters:
            # Country filter
            if 'country' in filters:
                filter_clauses.append({'term': {'country': filters['country']}})
            
            # Status filter
            if 'status' in filters:
                filter_clauses.append({'term': {'status': filters['status']}})
            
            # Legal form filter
            if 'legal_form' in filters:
                filter_clauses.append({'term': {'legal_form': filters['legal_form']}})
            
            # City filter
            if 'city' in filters:
                filter_clauses.append({'term': {'primary_city': filters['city']}})
            
            # Postal code filter
            if 'postal_code' in filters:
                filter_clauses.append({'term': {'primary_postal_code': filters['postal_code']}})
            
            # Has LEI filter
            if filters.get('has_lei'):
                filter_clauses.append({'exists': {'field': 'lei'}})
            
            # Industry code filter
            if 'industry_code' in filters:
                filter_clauses.append({'term': {'industry_code': filters['industry_code']}})
            
            # Source filter
            if 'source' in filters:
                filter_clauses.append({'term': {'source_records.source': filters['source']}})
            
            # Region filter
            if 'region' in filters:
                filter_clauses.append({'term': {'addresses.region': filters['region']}})
            
            # Min confidence score
            if 'min_confidence' in filters:
                filter_clauses.append({
                    'range': {
                        'confidence_score': {'gte': filters['min_confidence']}
                    }
                })
        
        # Build final query
        query_body = {
            'query': {
                'bool': {
                    'must': must_clauses if must_clauses else [{'match_all': {}}],
                    'filter': filter_clauses,
                }
            },
            'aggs': {
                'countries': {'terms': {'field': 'country'}},
                'statuses': {'terms': {'field': 'status'}},
                'legal_forms': {'terms': {'field': 'legal_form'}},
                'cities': {'terms': {'field': 'primary_city', 'size': 50}},
                'industries': {'terms': {'field': 'industry_code', 'size': 20}},
            },
        }
        
        return query_body
    
    def _parse_results(self, response: Dict[str, Any], 
                     page: int, page_size: int) -> Dict[str, Any]:
        """Parse OpenSearch results."""
        hits = response.get('hits', {})
        total = hits.get('total', {}).get('value', 0)
        
        companies = []
        for hit in hits.get('hits', []):
            company = hit.get('_source', {})
            company['_score'] = hit.get('_score')
            companies.append(company)
        
        # Extract aggregations
        aggs = response.get('aggregations', {})
        
        return {
            'total': total,
            'companies': companies,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size,
            'facets': {
                'countries': aggs.get('countries', {}).get('buckets', []),
                'statuses': aggs.get('statuses', {}).get('buckets', []),
                'legal_forms': aggs.get('legal_forms', {}).get('buckets', []),
                'cities': aggs.get('cities', {}).get('buckets', []),
                'industries': aggs.get('industries', {}).get('buckets', []),
            },
        }
    
    def index_company(self, company: Dict[str, Any]) -> bool:
        """Index a company document."""
        if not self.is_available:
            return False
        
        try:
            self.client.index(
                index=self.index,
                id=company.get('id'),
                body=company,
                refresh=True,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to index company: {e}")
            return False
    
    def delete_company(self, company_id: int) -> bool:
        """Delete a company from the index."""
        if not self.is_available:
            return False
        
        try:
            self.client.delete(
                index=self.index,
                id=str(company_id),
                ignore=[404],
                refresh=True,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete company: {e}")
            return False
    
    def reindex(self, company_query, batch_size: int = 100) -> int:
        """Reindex all companies."""
        if not self.is_available:
            return 0
        
        indexed = 0
        offset = 0
        
        while True:
            companies = company_query.limit(batch_size).offset(offset).all()
            
            if not companies:
                break
            
            for company in companies:
                doc = company.to_dict()
                if self.index_company(doc):
                    indexed += 1
            
            offset += batch_size
        
        return indexed
    
    def create_index(self, delete_existing: bool = False) -> bool:
        """Create the companies index with proper mappings."""
        if not self.is_available:
            return False
        
        index_name = self.index
        
        # Check if index exists
        if self.client.indices.exists(index_name):
            if delete_existing:
                self.client.indices.delete(index_name)
            else:
                return True
        
        # Create index with mappings
        mappings = {
            'properties': {
                'uuid': {'type': 'keyword'},
                'status': {'type': 'keyword'},
                'canonical_name': {
                    'type': 'text',
                    'fields': {
                        'keyword': {'type': 'keyword'}
                    }
                },
                'name_norm': {'type': 'keyword'},
                'legal_form': {'type': 'keyword'},
                'country': {'type': 'keyword'},
                'registration_number': {'type': 'keyword'},
                'registration_court': {'type': 'keyword'},
                'lei': {'type': 'keyword'},
                'industry_code': {'type': 'keyword'},
                'primary_city': {'type': 'keyword'},
                'primary_postal_code': {'type': 'keyword'},
                'confidence_score': {'type': 'float'},
                'is_verified': {'type': 'boolean'},
                'names': {
                    'type': 'nested',
                    'properties': {
                        'name': {'type': 'text'},
                        'name_type': {'type': 'keyword'},
                    }
                },
                'identifiers': {
                    'type': 'nested',
                    'properties': {
                        'identifier_type': {'type': 'keyword'},
                        'identifier_value': {'type': 'keyword'},
                    }
                },
                'addresses': {
                    'type': 'nested',
                    'properties': {
                        'address_type': {'type': 'keyword'},
                        'city': {'type': 'keyword'},
                        'postal_code': {'type': 'keyword'},
                        'region': {'type': 'keyword'},
                        'country': {'type': 'keyword'},
                    }
                },
                'source_records': {
                    'type': 'nested',
                    'properties': {
                        'source': {'type': 'keyword'},
                    }
                },
            }
        }
        
        try:
            self.client.indices.create(
                index=index_name,
                body={'mappings': mappings}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create index: {e}")
            return False