"""
Screening Service - Sanctions and risk screening.

Provides matching between companies and sanctions lists.
"""

import logging
from typing import Any, Dict, List, Optional

from app.core.extensions import db
from app.models import Company, SanctionsEntity, SanctionsMatch
from app.services.matching.normalizers import normalize_name


logger = logging.getLogger('company_intel.services.screening')


class ScreeningService:
    """Sanctions and PEP screening service."""
    
    def __init__(self, app=None):
        self.app = app
    
    def screen_company(self, company: Company) -> List[Dict[str, Any]]:
        """Screen a company against sanctions lists."""
        results = []
        
        # Screen by name
        name_results = self._screen_by_name(company)
        results.extend(name_results)
        
        # Screen by aliases
        for name in company.names:
            if name.name and not (name.is_primary and name.is_current):
                alias_results = self._screen_by_name_str(name.name)
                for result in alias_results:
                    if result['sanctions_entity_id'] not in [r['sanctions_entity_id'] for r in results]:
                        results.extend(alias_results)
        
        # Screen by address
        address_results = self._screen_by_address(company)
        results.extend(address_results)
        
        return results
    
    def _screen_by_name(self, company: Company) -> List[Dict[str, Any]]:
        """Screen company by name."""
        if not company.canonical_name:
            return []
        
        return self._screen_by_name_str(company.canonical_name)
    
    def _screen_by_name_str(self, name: str) -> List[Dict[str, Any]]:
        """Screen a name string against sanctions."""
        results = []
        
        name_norm = normalize_name(name)
        if not name_norm:
            return results
        
        # Search for similar names in sanctions
        candidates = SanctionsEntity.query.filter(
            SanctionsEntity.is_designated == True,
            SanctionsEntity.name_norm.ilike(f'%{name_norm[:10]}%')
        ).all()
        
        for entity in candidates:
            score, match_type = self._calculate_name_match(name_norm, entity)
            
            if score > 0.5:
                results.append({
                    'sanctions_entity_id': entity.id,
                    'match_type': match_type,
                    'match_score': score,
                    'matched_field': 'name',
                    'matched_value': name,
                })
        
        return results
    
    def _screen_by_address(self, company: Company) -> List[Dict[str, Any]]:
        """Screen by address similarity."""
        results = []
        
        # Get primary address
        primary_address = next((a for a in company.addresses if a.is_primary), None)
        if not primary_address:
            return results
        
        # Screen city
        city = primary_address.city
        if city:
            candidates = SanctionsEntity.query.filter(
                SanctionsEntity.is_designated == True,
            ).all()
            
            for entity in candidates:
                # Only check if there's a text field that might match
                # This is a simplified implementation
                pass
        
        return results
    
    def _calculate_name_match(self, name: str, entity: SanctionsEntity) -> tuple:
        """Calculate name match score."""
        from difflib import SequenceMatcher
        
        if not name or not entity.name_norm:
            return 0.0, None
        
        # Exact match
        if normalize_name(name) == entity.name_norm:
            return 1.0, 'EXACT'
        
        # Alias match
        aliases = entity.aliases or []
        if isinstance(aliases, list):
            for alias in aliases:
                if normalize_name(name) == normalize_name(alias):
                    return 0.95, 'ALIAS'
        
        # Similarity match
        score = SequenceMatcher(None, name, entity.name_norm[:len(name)+10] if len(entity.name_norm or '') > len(name) else (name or '')[:len(entity.name_norm or '')+10] if entity.name_norm else '').ratio()
        
        if score > 0.8:
            return score, 'SIMILAR'
        
        return 0.0, None
    
    def create_match_record(self, company: Company, entity: SanctionsEntity,
                         match_type: str, match_score: float,
                         matched_field: str, matched_value: str) -> SanctionsMatch:
        """Create a sanctions match record."""
        match = SanctionsMatch(
            company_id=company.id,
            sanctions_entity_id=entity.id,
            match_type=match_type,
            match_score=match_score,
            matched_field=matched_field,
            matched_value=matched_value,
            review_status='pending' if match_score < 0.9 else 'auto_confirmed',
            source='automated_screening',
            trust_score=0.85,
        )
        
        db.session.add(match)
        db.session.commit()
        
        return match