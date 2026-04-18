"""
Matching Service - Entity resolution engine.

Provides deterministic and probabilistic matching for companies.
"""

import logging
import re
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple

from app.core.extensions import db
from app.models import Company, CompanyName
from app.services.matching.normalizers import normalize_name, normalize_address


logger = logging.getLogger('company_intel.services.matching')


class MatchingService:
    """Entity resolution and matching service."""
    
    # Confidence thresholds
    AUTO_MERGE_THRESHOLD = 0.95
    PROBABLE_MATCH_THRESHOLD = 0.85
    MANUAL_REVIEW_THRESHOLD = 0.70
    
    # Hard identifiers for deterministic matching
    DETERMINISTIC_TYPES = ['LEI', 'HRB', 'HRA', 'REGISTRATION_NUMBER', 'VAT', 'DUNS', 'ISIN', 'OEIK']
    
    def __init__(self, app=None):
        self.app = app
    
    def find_matches(self, company: Company, limit: int = 10) -> List[Dict[str, Any]]:
        """Find potential matches for a company."""
        matches = []
        
        # 1. Deterministic matching
        deterministic = self._deterministic_match(company)
        if deterministic:
            matches.extend(deterministic)
        
        # 2. Probabilistic matching
        probabilistic = self._probabilistic_match(company, limit=limit)
        for match in probabilistic:
            if not any(m['company_id'] == match['company_id'] for m in matches):
                matches.append(match)
        
        # Sort by score
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        return matches[:limit]
    
    def _deterministic_match(self, company: Company) -> List[Dict[str, Any]]:
        """Find deterministic matches via hard identifiers."""
        matches = []
        
        # Get all identifiers
        identifiers = company.identifiers
        for id_obj in identifiers:
            if id_obj.identifier_type in self.DETERMINISTIC_TYPES:
                # Look for same identifier in other companies
                same_id = CompanyIdentifier.query.filter(
                    CompanyIdentifier.identifier_type == id_obj.identifier_type,
                    CompanyIdentifier.identifier_value == id_obj.identifier_value,
                    CompanyIdentifier.company_id != company.id,
                ).first()
                
                if same_id:
                    matches.append({
                        'company_id': same_id.company_id,
                        'match_type': 'DETERMINISTIC',
                        'match_score': 1.0,
                        'matched_fields': {
                            'identifier': {
                                'type': id_obj.identifier_type,
                                'value': id_obj.identifier_value,
                            }
                        },
                        'should_merge': True,
                    })
        
        return matches
    
    def _probabilistic_match(self, company: Company, limit: int = 10) -> List[Dict[str, Any]]:
        """Find probabilistic matches via similarity."""
        matches = []
        
        # Get normalized name
        name_norm = normalize_name(company.canonical_name or '')
        if not name_norm:
            return matches
        
        # Search for similar names
        candidates = Company.query.filter(
            Company.id != company.id,
            Company.name_norm.ilike(f'%{name_norm[:10]}%')
        ).limit(limit * 10).all()
        
        for candidate in candidates:
            score, fields = self._calculate_similarity(company, candidate)
            
            if score >= self.MANUAL_REVIEW_THRESHOLD:
                matches.append({
                    'company_id': candidate.id,
                    'match_type': 'PROBABILISTIC',
                    'match_score': score,
                    'matched_fields': fields,
                    'should_merge': score >= self.AUTO_MERGE_THRESHOLD,
                    'review_status': 'auto' if score >= self.AUTO_MERGE_THRESHOLD else 'manual',
                })
        
        return matches
    
    def _calculate_similarity(self, company_a: Company, company_b: Company) -> Tuple[float, Dict[str, Any]]:
        """Calculate similarity between two companies."""
        scores = {}
        weights = {}
        
        # Name similarity
        if company_a.canonical_name and company_b.canonical_name:
            name_score = self._string_similarity(
                normalize_name(company_a.canonical_name),
                normalize_name(company_b.canonical_name)
            )
            scores['name'] = name_score
            weights['name'] = 0.4
        
        # City similarity
        if company_a.primary_city and company_b.primary_city:
            city_score = self._string_similarity(
                company_a.primary_city.lower(),
                company_b.primary_city.lower()
            )
            scores['city'] = city_score
            weights['city'] = 0.2
        
        # Postal code match
        if company_a.primary_postal_code and company_b.primary_postal_code:
            postal_match = company_a.primary_postal_code == company_b.primary_postal_code
            scores['postal_code'] = 1.0 if postal_match else 0.0
            weights['postal_code'] = 0.2
        
        # Legal form match
        if company_a.legal_form and company_b.legal_form:
            legal_match = company_a.legal_form == company_b.legal_form
            scores['legal_form'] = 1.0 if legal_match else 0.0
            weights['legal_form'] = 0.1
        
        # Country match
        if company_a.country and company_b.country:
            country_match = company_a.country == company_b.country
            scores['country'] = 1.0 if country_match else 0.0
            weights['country'] = 0.1
        
        # Calculate weighted score
        total_score = 0.0
        total_weight = 0.0
        
        for field, score in scores.items():
            weight = weights.get(field, 0.1)
            total_score += score * weight
            total_weight += weight
        
        final_score = total_score / total_weight if total_weight > 0 else 0.0
        
        return final_score, scores
    
    def _string_similarity(self, s1: str, s2: str) -> float:
        """Calculate string similarity."""
        if not s1 or not s2:
            return 0.0
        
        # Exact match
        if s1 == s2:
            return 1.0
        
        # Sequence matching
        return SequenceMatcher(None, s1, s2).ratio()
    
    def merge_companies(self, company_a: Company, company_b: Company) -> Company:
        """Merge two companies into one."""
        # Determine which company is the survivor
        if company_a.trust_score >= company_b.trust_score:
            survivor, deleted = company_a, company_b
        else:
            survivor, deleted = company_b, company_a
        
        # Mark deleted company
        deleted.is_merged = True
        deleted.merged_into_id = survivor.id
        
        # Transfer data (if needed for more complex merges)
        
        db.session.commit()
        
        return survivor